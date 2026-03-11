import math
import os
from collections.abc import MutableMapping

import folium
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from app import APP_ICON, APP_TITLE
from dashboard_data import (
    DEFAULT_DISASTER_OPTIONS,
    _get_desktop_default_data_dir,
    _get_repo_default_data_dir,
    _maybe_get_secret_data_dir,
    classify_disaster_type,
    load_alerts_dataframe,
    load_alerts_dataframe_uncached,
    load_earthquake_shelters_dataframe,
    load_earthquake_shelters_dataframe_uncached,
    load_shelters_dataframe,
    load_shelters_dataframe_uncached,
    load_tsunami_shelters_dataframe,
    load_tsunami_shelters_dataframe_uncached,
    normalize_sigungu_name,
    resolve_data_dir,
)

PAGE_LABEL = "대피소 추천"

MAX_ACTIONABLE_DISTANCE_KM = 3.0
OFFICIAL_GUIDANCE_MESSAGE = (
    "재난문자, 기상청, 지자체 안내 같은 공식 재난 안내를 확인해주세요."
)

# 추천 표, 카드, 실시간 페이지 재사용까지 모두 같은 컬럼 순서를 기대하므로
# 결과 컬럼 집합은 여기에서 고정한다.
RECOMMENDATION_RESULT_COLUMNS = [
    "대피소명",
    "주소",
    "대피소유형",
    "위도",
    "경도",
    "시도",
    "시군구",
    "수용인원",
    "수용인원_정렬값",
    "거리_km",
    "추천구분",
    "추천사유",
]


def get_available_regions(shelters_frame: pd.DataFrame) -> pd.DataFrame:
    return (
        shelters_frame[["시도", "시군구"]]
        .drop_duplicates()
        .sort_values(["시도", "시군구"])
        .reset_index(drop=True)
    )


def _build_region_centers(shelters_frame: pd.DataFrame) -> pd.DataFrame:
    # 행정경계 API 없이도 좌표로 지역을 추정하려고,
    # 대피소 좌표 평균값을 지역 중심처럼 사용한다.
    return (
        shelters_frame.groupby(["시도", "시군구", "시군구정규화"], as_index=False)
        .agg(
            중심위도=("위도", "mean"),
            중심경도=("경도", "mean"),
            대피소수=("대피소명", "size"),
        )
        .sort_values(["시도", "시군구"])
        .reset_index(drop=True)
    )


def infer_region_from_coordinates(
    shelters_frame: pd.DataFrame,
    latitude: float,
    longitude: float,
) -> dict[str, object]:
    # 사용자가 직접 시도/시군구를 고르지 않아도 첫 화면이 동작해야 해서
    # 입력 좌표와 가장 가까운 지역 중심을 먼저 찾아 기본 지역으로 삼는다.
    region_centers = _build_region_centers(shelters_frame)
    if region_centers.empty:
        return {
            "sido": None,
            "sigungu": None,
            "distance_km": None,
            "source": "auto_detected",
        }

    scored = region_centers.copy()
    scored["distance_km"] = scored.apply(
        lambda row: haversine_km(
            latitude,
            longitude,
            float(row["중심위도"]),
            float(row["중심경도"]),
        ),
        axis=1,
    )
    scored = scored.sort_values(["distance_km", "대피소수"], ascending=[True, False]).reset_index(
        drop=True
    )
    nearest = scored.iloc[0]
    return {
        "sido": str(nearest["시도"]),
        "sigungu": str(nearest["시군구"]),
        "distance_km": float(nearest["distance_km"]),
        "source": "auto_detected",
    }


def get_sigungu_options(shelters_frame: pd.DataFrame, sido: str) -> list[str]:
    filtered = shelters_frame[shelters_frame["시도"] == sido]
    return sorted(filtered["시군구"].dropna().unique().tolist())


def get_region_center(
    shelters_frame: pd.DataFrame,
    sido: str,
    sigungu: str,
) -> tuple[float | None, float | None]:
    region_centers = _build_region_centers(shelters_frame)
    filtered = region_centers[
        (region_centers["시도"] == sido)
        & (region_centers["시군구정규화"] == normalize_sigungu_name(sigungu))
    ]
    if filtered.empty:
        filtered = region_centers[region_centers["시도"] == sido]
    if filtered.empty:
        return None, None

    return float(filtered["중심위도"].mean()), float(filtered["중심경도"].mean())


def update_recommendation_coordinates_from_region_center(
    shelters_frame: pd.DataFrame,
    sido: str,
    sigungu: str,
    state: MutableMapping[str, object],
) -> bool:
    # "지역 직접 수정"을 눌렀을 때 화면에 보이는 좌표 입력값도 같이 바꿔야 해서,
    # session_state를 직접 받도록 만든 함수다.
    latitude, longitude = get_region_center(shelters_frame, sido=sido, sigungu=sigungu)
    if latitude is None or longitude is None:
        return False

    state["recommendation_lat"] = float(latitude)
    state["recommendation_lon"] = float(longitude)
    return True


def sync_manual_region_center_to_recommendation_inputs(shelters_frame: pd.DataFrame) -> None:
    update_recommendation_coordinates_from_region_center(
        shelters_frame=shelters_frame,
        sido=str(st.session_state.get("manual_sido", "")),
        sigungu=str(st.session_state.get("manual_sigungu", "")),
        state=st.session_state,
    )


def get_recent_alerts(
    alerts_frame: pd.DataFrame,
    sido: str,
    sigungu: str | None = None,
    limit: int = 5,
) -> pd.DataFrame:
    # 상단 요약 카드와 하단 특보 표가 같은 기준을 보도록 최근 특보 조회를 따로 분리한다.
    filtered = alerts_frame[alerts_frame["지역"] == sido]
    if sigungu:
        filtered = filtered[filtered["시군구정규화"] == normalize_sigungu_name(sigungu)]
        if filtered.empty:
            filtered = alerts_frame[alerts_frame["지역"] == sido]

    return filtered.sort_values("발표시간", ascending=False).head(limit).reset_index(drop=True)


def build_alert_summary(
    alerts_frame: pd.DataFrame,
    sido: str,
    sigungu: str | None = None,
) -> dict[str, object]:
    recent_alerts = get_recent_alerts(alerts_frame, sido=sido, sigungu=sigungu, limit=5)
    if recent_alerts.empty:
        return {
            "latest_time": None,
            "latest_disaster": None,
            "alert_count": 0,
            "hazards": [],
        }

    return {
        "latest_time": pd.Timestamp(recent_alerts.iloc[0]["발표시간"]),
        "latest_disaster": str(recent_alerts.iloc[0]["재난종류"]),
        "alert_count": int(len(recent_alerts)),
        "hazards": recent_alerts["재난종류"].dropna().astype(str).unique().tolist(),
    }

def get_disaster_options(alerts_frame: pd.DataFrame, sido: str, sigungu: str) -> list[str]:
    # 최근 특보가 한동안 없더라도 사용자가 재난 유형을 직접 골라 볼 수 있어야 하므로
    # 최근 이력 + 기본 옵션 목록을 합쳐 중복 없이 보여 준다.
    recent_alerts = get_recent_alerts(alerts_frame, sido=sido, sigungu=sigungu, limit=10)
    options = [classify_disaster_type(value) for value in recent_alerts["재난종류"].tolist()]
    options.extend(DEFAULT_DISASTER_OPTIONS)

    deduplicated: list[str] = []
    for item in options:
        if item not in deduplicated:
            deduplicated.append(item)
    return deduplicated


def should_compute_recommendations(selected_disaster: str | None) -> bool:
    return selected_disaster is not None and str(selected_disaster).strip() != ""


def haversine_km(
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> float:
    # 현재 추천 페이지는 실제 도로 경로가 아니라
    # "지금 위치에서 어느 후보가 상대적으로 더 가까운가"를 직선 거리로만 비교한다.
    earth_radius_km = 6371.0
    lat_a = math.radians(latitude_a)
    lon_a = math.radians(longitude_a)
    lat_b = math.radians(latitude_b)
    lon_b = math.radians(longitude_b)

    delta_lat = lat_b - lat_a
    delta_lon = lon_b - lon_a
    haversine_value = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat_a) * math.cos(lat_b) * math.sin(delta_lon / 2) ** 2
    )
    return earth_radius_km * 2 * math.asin(math.sqrt(haversine_value))


def _filter_by_region(dataframe: pd.DataFrame, sido: str, sigungu: str) -> pd.DataFrame:
    # 세부 시군구 데이터가 비어 있는 CSV도 있어서,
    # 먼저 시군구를 보고 없으면 시도 단위로 범위를 넓힌다.
    normalized_sigungu = normalize_sigungu_name(sigungu)
    local = dataframe[
        (dataframe["시도"] == sido) & (dataframe["시군구정규화"] == normalized_sigungu)
    ]
    if not local.empty:
        return local.copy()

    regional = dataframe[dataframe["시도"] == sido]
    if not regional.empty:
        return regional.copy()

    return dataframe.copy()


def _build_primary_candidates(
    shelters_frame: pd.DataFrame,
    earthquake_shelters_frame: pd.DataFrame,
    tsunami_shelters_frame: pd.DataFrame,
    disaster_group: str,
    sido: str,
    sigungu: str,
) -> tuple[pd.DataFrame, str]:
    # 재난 그룹마다 우선해야 하는 대피소가 다르다.
    # 지진/해일은 전용 CSV를 보고, 폭염/한파는 통합 대피소 안 특정 유형만 먼저 고른다.
    if disaster_group == "지진":
        return _filter_by_region(earthquake_shelters_frame, sido, sigungu), "전용 대피소"
    if disaster_group == "해일/쓰나미":
        return _filter_by_region(tsunami_shelters_frame, sido, sigungu), "전용 대피소"
    if disaster_group == "폭염":
        filtered = shelters_frame[shelters_frame["대피소유형"].str.contains("무더위쉼터", na=False)]
        return _filter_by_region(filtered, sido, sigungu), "전용 대피소"
    if disaster_group == "한파":
        filtered = shelters_frame[shelters_frame["대피소유형"].str.contains("한파쉼터", na=False)]
        return _filter_by_region(filtered, sido, sigungu), "전용 대피소"

    return pd.DataFrame(), "기본 대피소"


def _build_fallback_candidates(
    shelters_frame: pd.DataFrame,
    sido: str,
    sigungu: str,
) -> pd.DataFrame:
    return _filter_by_region(shelters_frame, sido, sigungu)


def _score_candidates(
    dataframe: pd.DataFrame,
    latitude: float,
    longitude: float,
    recommendation_type: str,
    disaster_group: str,
    reason_prefix: str,
) -> pd.DataFrame:
    # 추천 정렬은 결국 거리와 수용인원 같은 숫자 컬럼이 있어야 돌아가므로
    # 각 후보 DataFrame을 공통 점수 테이블 형태로 바꿔 준다.
    if dataframe.empty:
        return dataframe.copy()

    scored = dataframe.copy()
    scored["거리_km"] = scored.apply(
        lambda row: haversine_km(latitude, longitude, float(row["위도"]), float(row["경도"])),
        axis=1,
    )
    scored["추천구분"] = recommendation_type
    scored["추천사유"] = (
        reason_prefix + disaster_group + " 상황에서 현재 좌표 기준으로 가까운 후보를 우선 정렬했다."
    )
    scored["수용인원_정렬값"] = pd.to_numeric(scored["수용인원_정렬값"], errors="coerce").fillna(0)
    return scored


def _ensure_result_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    # 추천이 비거나 일부 CSV에 컬럼이 빠져 있어도
    # 화면 표와 테스트는 항상 같은 컬럼 순서를 기대한다.
    ensured = dataframe.copy()
    default_values = {
        "대피소명": "",
        "주소": "",
        "대피소유형": "미분류",
        "위도": pd.NA,
        "경도": pd.NA,
        "시도": "",
        "시군구": "",
        "수용인원": pd.NA,
        "수용인원_정렬값": 0,
        "거리_km": pd.NA,
        "추천구분": "",
        "추천사유": "",
    }

    for column, default_value in default_values.items():
        if column not in ensured.columns:
            ensured[column] = default_value

    return ensured[RECOMMENDATION_RESULT_COLUMNS]


def recommend_shelters(
    shelters_frame: pd.DataFrame,
    earthquake_shelters_frame: pd.DataFrame,
    tsunami_shelters_frame: pd.DataFrame,
    disaster_group: str,
    latitude: float,
    longitude: float,
    sido: str,
    sigungu: str,
    top_n: int = 3,
) -> pd.DataFrame:
    # 추천 규칙의 핵심:
    # 1) 재난별 전용 후보를 먼저 찾고
    # 2) 부족하면 통합 대피소를 붙이고
    # 3) 추천구분 -> 거리 -> 수용인원 순서로 정렬한다.
    primary_candidates, primary_label = _build_primary_candidates(
        shelters_frame=shelters_frame,
        earthquake_shelters_frame=earthquake_shelters_frame,
        tsunami_shelters_frame=tsunami_shelters_frame,
        disaster_group=disaster_group,
        sido=sido,
        sigungu=sigungu,
    )
    scored_frames: list[pd.DataFrame] = []

    if not primary_candidates.empty:
        scored_frames.append(
            _score_candidates(
                dataframe=primary_candidates,
                latitude=latitude,
                longitude=longitude,
                recommendation_type=primary_label,
                disaster_group=disaster_group,
                reason_prefix="재난 그룹에 맞는 전용 후보를 먼저 조회했고, ",
            )
        )

    needs_fallback = disaster_group in {"호우/태풍", "강풍/풍랑", "대설", "건조", "기타"}
    if needs_fallback or len(primary_candidates) < top_n:
        fallback_candidates = _build_fallback_candidates(
            shelters_frame,
            sido=sido,
            sigungu=sigungu,
        )
        fallback_type = "기본 대피소" if needs_fallback and primary_candidates.empty else "대체 대피소"
        scored_frames.append(
            _score_candidates(
                dataframe=fallback_candidates,
                latitude=latitude,
                longitude=longitude,
                recommendation_type=fallback_type,
                disaster_group=disaster_group,
                reason_prefix="전용 후보만으로는 부족하거나 전용 정의가 없어 통합 대피장소를 함께 조회했고, ",
            )
        )

    if not scored_frames:
        return pd.DataFrame(columns=RECOMMENDATION_RESULT_COLUMNS)

    combined = pd.concat(scored_frames, ignore_index=True)
    combined = combined.drop_duplicates(subset=["대피소명", "주소"])

    priority_order = {"전용 대피소": 0, "기본 대피소": 1, "대체 대피소": 2}
    combined["추천우선순위"] = combined["추천구분"].map(priority_order).fillna(9)
    combined = combined.sort_values(
        ["추천우선순위", "거리_km", "수용인원_정렬값"],
        ascending=[True, True, False],
    )
    standardized = _ensure_result_columns(combined)
    return standardized.head(top_n).reset_index(drop=True)


def get_nearest_recommendation_distance_km(recommendations: pd.DataFrame) -> float | None:
    if recommendations.empty or "거리_km" not in recommendations.columns:
        return None

    distances = pd.to_numeric(recommendations["거리_km"], errors="coerce").dropna()
    if distances.empty:
        return None

    return float(distances.min())


def should_display_recommendations(
    recommendations: pd.DataFrame,
    max_distance_km: float = MAX_ACTIONABLE_DISTANCE_KM,
) -> bool:
    # 후보가 있다고 바로 "지금 대피하세요"처럼 보이면 과하게 해석될 수 있어서,
    # 가장 가까운 후보가 일정 거리 안에 있을 때만 행동형 추천으로 보여 준다.
    nearest_distance_km = get_nearest_recommendation_distance_km(recommendations)
    if nearest_distance_km is None:
        return False

    return nearest_distance_km <= max_distance_km


def build_recommendation_map(
    user_latitude: float,
    user_longitude: float,
    recommendations: pd.DataFrame,
) -> folium.Map:
    # 지도는 무료 OSM 타일만 쓰고, 추천 페이지에서는 실제 경로 API를 붙이지 않는다.
    # 그래서 사용자 위치와 대피소를 직선으로만 이어 준다.
    map_object = folium.Map(
        location=[user_latitude, user_longitude],
        zoom_start=11,
        tiles="OpenStreetMap",
        control_scale=True,
    )

    folium.CircleMarker(
        location=[user_latitude, user_longitude],
        radius=7,
        color="#dc2626",
        fill=True,
        fill_color="#dc2626",
        fill_opacity=0.95,
        tooltip="사용자 위치",
    ).add_to(map_object)

    bounds = [[user_latitude, user_longitude]]
    for row in recommendations.to_dict(orient="records"):
        shelter_latitude = float(row["위도"])
        shelter_longitude = float(row["경도"])
        recommendation_type = str(row["추천구분"])
        if recommendation_type == "전용 대피소":
            color = "#0f766e"
        elif recommendation_type == "대체 대피소":
            color = "#f59e0b"
        else:
            color = "#1d4ed8"

        folium.CircleMarker(
            location=[shelter_latitude, shelter_longitude],
            radius=5,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.9,
            tooltip=f"{row['대피소명']} ({row['추천구분']})",
        ).add_to(map_object)

        folium.PolyLine(
            locations=[[user_latitude, user_longitude], [shelter_latitude, shelter_longitude]],
            color=color,
            weight=2,
            opacity=0.75,
            dash_array="5 6",
        ).add_to(map_object)

        bounds.append([shelter_latitude, shelter_longitude])

    if len(bounds) > 1:
        map_object.fit_bounds(bounds, padding=(30, 30))

    return map_object


def render_page() -> None:
    st.set_page_config(
        page_title=f"{APP_TITLE} | {PAGE_LABEL}",
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("1. 대피소 추천")
    st.write("입력 좌표를 기준으로 지역을 자동 감지하고, 현재 데이터 안에서 가까운 대피소 Top 3 를 추천합니다.")
    st.caption("실제 경로 안내가 아니라 직선 거리 기준 추천이며, 지역 감지는 가장 가까운 지역 중심 좌표를 기준으로 동작합니다.")

    try:
        alerts_frame = load_alerts_dataframe()
        shelters_frame = load_shelters_dataframe()
        earthquake_shelters_frame = load_earthquake_shelters_dataframe()
        tsunami_shelters_frame = load_tsunami_shelters_dataframe()
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.stop()

    regions = get_available_regions(shelters_frame)
    sidos = sorted(regions["시도"].dropna().unique().tolist())

    st.sidebar.header("추천 조건")
    # recommendation_ 접두사를 둔 이유는
    # 실시간 페이지의 `realtime_*` 상태와 서로 덮어쓰지 않게 하려는 것이다.
    if "recommendation_lat" not in st.session_state:
        st.session_state["recommendation_lat"] = 35.1796
    if "recommendation_lon" not in st.session_state:
        st.session_state["recommendation_lon"] = 129.0756
    if "use_manual_region" not in st.session_state:
        st.session_state["use_manual_region"] = False

    st.sidebar.button("현재 위치 자동 입력 (준비중)", disabled=True)

    selected_latitude = st.sidebar.number_input(
        "위도",
        min_value=30.0,
        max_value=45.0,
        step=0.0001,
        format="%.6f",
        key="recommendation_lat",
    )
    selected_longitude = st.sidebar.number_input(
        "경도",
        min_value=120.0,
        max_value=140.0,
        step=0.0001,
        format="%.6f",
        key="recommendation_lon",
    )

    detected_region = infer_region_from_coordinates(
        shelters_frame,
        latitude=float(selected_latitude),
        longitude=float(selected_longitude),
    )
    detected_sido = str(detected_region["sido"] or sidos[0])
    detected_sigungu_options = get_sigungu_options(shelters_frame, detected_sido)
    detected_sigungu = (
        str(detected_region["sigungu"])
        if detected_region["sigungu"] in detected_sigungu_options
        else detected_sigungu_options[0]
    )

    if "manual_sido" not in st.session_state or not st.session_state["use_manual_region"]:
        st.session_state["manual_sido"] = detected_sido
    if "manual_sigungu" not in st.session_state or not st.session_state["use_manual_region"]:
        st.session_state["manual_sigungu"] = detected_sigungu
    if st.session_state["manual_sido"] not in sidos:
        st.session_state["manual_sido"] = detected_sido

    with st.sidebar.expander("지역 직접 수정", expanded=st.session_state["use_manual_region"]):
        st.checkbox("감지 지역 대신 직접 수정", key="use_manual_region")
        st.selectbox("시도", options=sidos, key="manual_sido")

        manual_sigungu_options = get_sigungu_options(shelters_frame, st.session_state["manual_sido"])
        if st.session_state.get("manual_sigungu") not in manual_sigungu_options:
            st.session_state["manual_sigungu"] = manual_sigungu_options[0]

        st.selectbox("시군구", options=manual_sigungu_options, key="manual_sigungu")

        st.button(
            "보정 지역 중심 좌표 불러오기",
            on_click=sync_manual_region_center_to_recommendation_inputs,
            args=(shelters_frame,),
        )

    if st.session_state["use_manual_region"]:
        active_sido = str(st.session_state["manual_sido"])
        active_sigungu = str(st.session_state["manual_sigungu"])
        region_source = "manual_override"
    else:
        active_sido = detected_sido
        active_sigungu = detected_sigungu
        region_source = str(detected_region["source"])

    disaster_options = get_disaster_options(alerts_frame, active_sido, active_sigungu)
    selected_disaster = st.sidebar.selectbox(
        "재난 유형",
        options=disaster_options,
        index=None,
        placeholder="재난 유형 선택",
    )

    alert_summary = build_alert_summary(alerts_frame, active_sido, active_sigungu)
    recent_alerts = get_recent_alerts(alerts_frame, active_sido, active_sigungu, limit=5)
    selection_pending = not should_compute_recommendations(selected_disaster)
    if selection_pending:
        recommendations = pd.DataFrame(columns=RECOMMENDATION_RESULT_COLUMNS)
    else:
        recommendations = recommend_shelters(
            shelters_frame=shelters_frame,
            earthquake_shelters_frame=earthquake_shelters_frame,
            tsunami_shelters_frame=tsunami_shelters_frame,
            disaster_group=str(selected_disaster),
            latitude=float(selected_latitude),
            longitude=float(selected_longitude),
            sido=active_sido,
            sigungu=active_sigungu,
        )
    nearest_recommendation_distance_km = get_nearest_recommendation_distance_km(recommendations)
    display_recommendations = should_display_recommendations(recommendations)
    # 후보는 찾았지만 너무 멀면 "참고용 조회 결과"만 보여 주고,
    # 바로 행동형 추천처럼 보이지 않게 한 번 더 걸러 준다.
    hold_recommendations = not selection_pending and not recommendations.empty and not display_recommendations
    hold_message = ""
    if hold_recommendations:
        if nearest_recommendation_distance_km is None:
            hold_message = (
                "추천 후보는 찾았지만 거리 기준을 확인하지 못해 현재 좌표에 대한 행동형 대피 추천은 보류합니다. "
                + OFFICIAL_GUIDANCE_MESSAGE
            )
        else:
            hold_message = (
                f"가장 근접한 후보가 직선 거리 {nearest_recommendation_distance_km:.2f} km로 멀어 "
                "현재 좌표에 대한 행동형 대피 추천은 보류합니다. "
                + OFFICIAL_GUIDANCE_MESSAGE
            )

    metric_columns = st.columns(4)
    metric_columns[0].metric("선택 재난", "-" if selection_pending else str(selected_disaster))
    metric_columns[1].metric(
        "최근 특보 시각",
        "-"
        if alert_summary["latest_time"] is None or pd.isna(alert_summary["latest_time"])
        else pd.Timestamp(alert_summary["latest_time"]).strftime("%Y-%m-%d %H:%M"),
    )
    metric_columns[2].metric("최근 확인 특보 수", f"{float(alert_summary['alert_count']):,.0f}")
    if selection_pending:
        metric_columns[3].metric("추천 후보 수", "-")
    elif recommendations.empty:
        metric_columns[3].metric("추천 후보 수", "0")
    elif hold_recommendations:
        metric_columns[3].metric("추천 상태", "보류")
    else:
        metric_columns[3].metric("추천 후보 수", f"{float(len(recommendations)):,.0f}")
    detected_distance_label = (
        "-"
        if detected_region["distance_km"] is None or pd.isna(detected_region["distance_km"])
        else f"{float(detected_region['distance_km']):.2f} km"
    )

    top_left, top_right = st.columns([1.1, 0.9], gap="large")

    with top_left:
        with st.container(border=True):
            st.subheader("현재 좌표 기준 특보 요약")
            st.markdown(
                f"- 감지 지역: **{detected_sido} {detected_sigungu}** "
                f"({detected_distance_label} 떨어진 지역 중심 기준)"
            )
            if region_source == "manual_override":
                st.markdown(f"- 보정 지역: **{active_sido} {active_sigungu}**")
            else:
                st.markdown(f"- 활성 지역: **{active_sido} {active_sigungu}**")

            if alert_summary["hazards"]:
                st.markdown("- 최근 특보 유형: " + ", ".join(alert_summary["hazards"]))
            else:
                st.markdown("- 최근 특보 데이터가 없어 재난을 선택하면 수동 기준으로 대피소 후보를 계산합니다.")
            st.markdown(f"- 입력 좌표: **{selected_latitude:.4f}, {selected_longitude:.4f}**")
            st.caption(
                "현재 지역 감지는 행정경계 기반이 아니라 가장 가까운 지역 중심 좌표 기준입니다. "
                "감지 결과는 사이드바의 `지역 직접 수정` 에서 보정할 수 있다."
            )
            if detected_region["distance_km"] is not None and float(detected_region["distance_km"]) > 40:
                st.warning("현재 좌표와 감지된 지역 중심 거리가 멀다. 필요하면 지역 직접 수정으로 보정해 주세요.")
        if selection_pending:
            st.info("재난 유형을 선택하면 가까운 대피소 후보를 계산합니다.")
        elif recommendations.empty:
            st.info("현재 조건으로 보여줄 추천 대피소가 없습니다.")
        elif hold_recommendations:
            st.warning(hold_message)
            st.info("현재 후보는 참고용 조회 결과일 뿐 행동형 추천으로는 표시하지 않습니다.")
        else:
            card_columns = st.columns(min(len(recommendations), 3))
            for index, (_, row) in enumerate(recommendations.iterrows()):
                distance_label = "-" if pd.isna(row["거리_km"]) else f"{float(row['거리_km']):.2f} km"
                with card_columns[index]:
                    with st.container(border=True):
                        st.subheader(f"Top {index + 1}. {row['대피소명']}")
                        st.markdown(f"**구분**: {row['추천구분']}")
                        st.markdown(f"**직선 거리**: {distance_label}")
                        st.markdown(f"**대피소 유형**: {row['대피소유형']}")
                        st.markdown(f"**수용인원**: {float(row['수용인원_정렬값']):,.0f}명")
                        st.markdown(f"**주소**: {row['주소']}")
                        st.caption(row["추천사유"])

    if not selection_pending:
        with top_right:
            with st.container(border=True):
                st.subheader("추천 지도")
                if recommendations.empty:
                    st.info("표시할 추천 지도가 없다.")
                elif hold_recommendations:
                    st.warning("추천 보류 상태 입니다. 공식 재난 안내를 확인해 주세요.")
                else:
                    components.html(
                        build_recommendation_map(
                            user_latitude=float(selected_latitude),
                            user_longitude=float(selected_longitude),
                            recommendations=recommendations,
                        )._repr_html_(),
                        height=470,
                    )
                    st.caption("지도 직선 거리 기준이며, 실제 도로 경로를 의미하지 않습니다.")

    st.divider()

    if selection_pending:
        with st.container(border=True):
            st.subheader("최근 특보 이력")
            if recent_alerts.empty:
                st.info("선택한 지역의 최근 특보 이력이 없습니다.")
            else:
                alert_display = recent_alerts.copy()
                alert_display["발표시간"] = alert_display["발표시간"].dt.strftime("%Y-%m-%d %H:%M")
                st.dataframe(
                    alert_display[["발표시간", "지역", "시군구", "재난종류", "특보등급"]],
                    use_container_width=True,
                    hide_index=True,
                )
    else:
        table_left, table_right = st.columns([0.95, 1.05], gap="large")

        with table_left:
            with st.container(border=True):
                st.subheader("최근 특보 이력")
                if recent_alerts.empty:
                    st.info("선택한 지역의 최근 특보 이력이 없습니다.")
                else:
                    alert_display = recent_alerts.copy()
                    alert_display["발표시간"] = alert_display["발표시간"].dt.strftime("%Y-%m-%d %H:%M")
                    st.dataframe(
                        alert_display[["발표시간", "지역", "시군구", "재난종류", "특보등급"]],
                        use_container_width=True,
                        hide_index=True,
                    )

        with table_right:
            with st.container(border=True):
                st.subheader("추천 결과 표")
                if recommendations.empty:
                    st.warning("현재 조건에서는 추천할 대피소가 없습니다. 지역이나 좌표를 조정해 주세요.")
                elif hold_recommendations:
                    st.warning(hold_message)
                else:
                    display_frame = recommendations.copy()
                    display_frame["거리"] = display_frame["거리_km"].map(
                        lambda value: "-" if pd.isna(value) else f"{float(value):.2f} km"
                    )
                    display_frame["수용인원"] = display_frame["수용인원_정렬값"].map(
                        lambda value: f"{float(value):,.0f}명"
                    )
                    st.dataframe(
                        display_frame[
                            ["대피소명", "추천구분", "대피소유형", "거리", "수용인원", "주소", "추천사유"]
                        ],
                        use_container_width=True,
                        hide_index=True,
                    )


if os.environ.get("PROJECT_DASHBOARD_IMPORT_ONLY") != "1":
    render_page()
