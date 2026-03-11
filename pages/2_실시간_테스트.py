from __future__ import annotations

import importlib.util
import os
import sys
from collections.abc import Mapping, MutableMapping
from datetime import datetime
from pathlib import Path
from typing import Any

import folium
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components
from app import APP_ICON, APP_TITLE
from dashboard_data import (
    load_alerts_dataframe,
    load_earthquake_shelters_dataframe,
    load_shelters_dataframe,
    load_tsunami_shelters_dataframe,
)

try:
    from streamlit_geolocation import streamlit_geolocation
except Exception:  # pragma: no cover - optional dependency fallback
    streamlit_geolocation = None

PAGE2_PATH = Path(__file__).resolve().with_name("1_대피소_추천.py")
PAGE2_MODULE_NAME = "project_dashboard_recommendation_runtime"
OSRM_BASE_URL_KEY = "OSRM_BASE_URL"
DEFAULT_OSRM_BASE_URL = "http://router.project-osrm.org"
DEFAULT_OSRM_PROFILE = "foot"
OSRM_ROUTE_TIMEOUT_S = 10.0
RANK_COLORS = ["#0f766e", "#1d4ed8", "#f59e0b"]

PAGE_LABEL = "실시간 테스트"


def load_recommendation_page_module():
    # 추천 규칙은 1번 페이지를 기준으로 유지하고 싶어서,
    # 여기서는 필요한 helper만 import-only로 불러와 재사용한다.
    if PAGE2_MODULE_NAME in sys.modules:
        return sys.modules[PAGE2_MODULE_NAME]

    previous_value = os.environ.get("PROJECT_DASHBOARD_IMPORT_ONLY")
    os.environ["PROJECT_DASHBOARD_IMPORT_ONLY"] = "1"
    try:
        spec = importlib.util.spec_from_file_location(PAGE2_MODULE_NAME, PAGE2_PATH)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load module from {PAGE2_PATH}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[PAGE2_MODULE_NAME] = module
        spec.loader.exec_module(module)
        return module
    finally:
        if previous_value is None:
            os.environ.pop("PROJECT_DASHBOARD_IMPORT_ONLY", None)
        else:
            os.environ["PROJECT_DASHBOARD_IMPORT_ONLY"] = previous_value


def _get_osrm_config() -> tuple[str, str]:
    # 공개 OSRM 기본 URL을 쓰되, 필요하면 환경변수로만 덮어쓸 수 있게 단순화했다.
    base_url = os.environ.get(OSRM_BASE_URL_KEY, "").strip() or DEFAULT_OSRM_BASE_URL
    return base_url.rstrip("/"), DEFAULT_OSRM_PROFILE


def get_browser_or_manual_coordinates(
    session_state: MutableMapping[str, object],
) -> tuple[float, float] | None:
    latitude = session_state.get("realtime_lat")
    longitude = session_state.get("realtime_lon")
    if latitude in (None, "") or longitude in (None, ""):
        return None

    try:
        return float(latitude), float(longitude)
    except (TypeError, ValueError):
        return None


def format_distance_m(distance_m: object) -> str:
    try:
        value = float(distance_m)
    except (TypeError, ValueError):
        return "-"

    if value >= 1000:
        return f"{value / 1000:.2f} km"
    return f"{value:.0f} m"


def format_duration_s(duration_s: object) -> str:
    try:
        value = int(float(duration_s))
    except (TypeError, ValueError):
        return "-"

    minutes, seconds = divmod(value, 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{hours}시간 {minutes}분"
    if minutes > 0:
        return f"{minutes}분"
    return f"{seconds}초"


def _current_timestamp_label() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _format_location_source_label(source: object) -> str:
    source_value = str(source or "")
    if source_value == "browser":
        return "브라우저"
    if source_value == "manual":
        return "수동"
    return "기본값"


def _normalize_point(value: Mapping[str, object]) -> dict[str, Any]:
    return {
        "x": float(value["x"]),
        "y": float(value["y"]),
        "key": str(value.get("key", "")),
        "name": str(value.get("name", "")),
    }


def _extract_osrm_route_vertices(route: Mapping[str, object]) -> list[tuple[float, float]]:
    # OSRM은 [경도, 위도] 순서를 쓰는데 folium은 [위도, 경도]를 기대하므로
    # 좌표 순서를 여기서 바꿔 둔다.
    geometry = route.get("geometry", {}) if isinstance(route, dict) else {}
    coordinates = geometry.get("coordinates", []) if isinstance(geometry, dict) else []
    if not isinstance(coordinates, list):
        return []

    vertices: list[tuple[float, float]] = []
    for coordinate in coordinates:
        if not isinstance(coordinate, (list, tuple)) or len(coordinate) < 2:
            continue
        try:
            longitude = float(coordinate[0])
            latitude = float(coordinate[1])
        except (TypeError, ValueError):
            continue

        point = (latitude, longitude)
        if not vertices or vertices[-1] != point:
            vertices.append(point)
    return vertices


def _get_osrm_route_detail(
    origin: Mapping[str, object],
    destination: Mapping[str, object],
    base_url: str,
    profile: str,
    timeout: float = OSRM_ROUTE_TIMEOUT_S,
) -> dict[str, object]:
    # OSRM 원본 응답은 화면에서 바로 쓰기 어렵기 때문에
    # 거리, 시간, PolyLine 좌표만 남긴 공통 형태로 바꿔 준다.
    normalized_origin = _normalize_point(origin)
    normalized_destination = _normalize_point(destination)
    route_path = (
        f"{base_url}/route/v1/{profile}/"
        f"{normalized_origin['x']},{normalized_origin['y']};"
        f"{normalized_destination['x']},{normalized_destination['y']}"
    )
    response = requests.get(
        route_path,
        params={
            "overview": "full",
            "geometries": "geojson",
            "steps": "false",
        },
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()

    if payload.get("code") != "Ok":
        raise ValueError(f"OSRM route response returned code={payload.get('code')!r}.")

    routes = payload.get("routes", [])
    if not isinstance(routes, list) or not routes:
        raise ValueError("OSRM route response does not contain routes.")

    route = routes[0]
    route_vertices = _extract_osrm_route_vertices(route)
    if not route_vertices:
        route_vertices = [
            (float(normalized_origin["y"]), float(normalized_origin["x"])),
            (float(normalized_destination["y"]), float(normalized_destination["x"])),
        ]

    return {
        "destination_key": normalized_destination["key"],
        "route_distance_m": route.get("distance"),
        "route_duration_s": route.get("duration"),
        "route_vertices": route_vertices,
        "source": "osrm",
    }


def _build_straight_line_route_detail(
    origin: Mapping[str, object],
    destination: Mapping[str, object],
    page2_module,
    *,
    reason: str = "",
) -> dict[str, object]:
    # OSRM 호출이 실패해도 화면을 비워 두지 않으려고
    # 추천 페이지의 직선 거리 계산을 재사용해 fallback 경로를 만든다.
    normalized_origin = _normalize_point(origin)
    normalized_destination = _normalize_point(destination)
    distance_km = page2_module.haversine_km(
        float(normalized_origin["y"]),
        float(normalized_origin["x"]),
        float(normalized_destination["y"]),
        float(normalized_destination["x"]),
    )
    return {
        "destination_key": normalized_destination["key"],
        "route_distance_m": round(distance_km * 1000, 1),
        "route_duration_s": None,
        "route_vertices": [
            (float(normalized_origin["y"]), float(normalized_origin["x"])),
            (float(normalized_destination["y"]), float(normalized_destination["x"])),
        ],
        "source": "straight_line",
        "warning": reason,
    }


def build_realtime_recommendation_map(
    user_lat: float,
    user_lon: float,
    recommendations: pd.DataFrame,
    route_details: list[dict[str, object]],
) -> folium.Map:
    # 실시간 페이지는 추천 결과를 다시 지도에 그릴 때
    # 사용자 1명 + 상위 대피소 3곳 + 각 경로 3개만 표시하도록 제한한다.
    detail_by_key = {
        str(detail.get("destination_key", "")): detail for detail in route_details if detail.get("destination_key")
    }
    map_object = folium.Map(
        location=[user_lat, user_lon],
        zoom_start=12,
        tiles="OpenStreetMap",
        control_scale=True,
    )
    bounds: list[list[float]] = [[user_lat, user_lon]]

    folium.CircleMarker(
        location=[user_lat, user_lon],
        radius=8,
        color="#dc2626",
        fill=True,
        fill_color="#dc2626",
        fill_opacity=1.0,
        tooltip="현재 위치",
    ).add_to(map_object)

    for index, (_, row) in enumerate(recommendations.iterrows()):
        route_key = str(row.get("route_key", index))
        detail = detail_by_key.get(route_key)
        color = RANK_COLORS[index % len(RANK_COLORS)]
        shelter_latitude = float(row["위도"])
        shelter_longitude = float(row["경도"])
        popup_lines = [
            f"<strong>{row['대피소명']}</strong>",
            f"구분: {row['추천구분']}",
            f"실경로 거리: {format_distance_m(detail.get('route_distance_m') if detail else None)}",
            f"예상 시간: {format_duration_s(detail.get('route_duration_s') if detail else None)}",
        ]
        if detail and detail.get("source") == "straight_line":
            popup_lines.append("OSRM 도보 경로 조회 실패로 직선 fallback 을 표시함")

        folium.CircleMarker(
            location=[shelter_latitude, shelter_longitude],
            radius=6,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.95,
            tooltip=f"Top {index + 1}. {row['대피소명']}",
            popup=folium.Popup("<br>".join(popup_lines), max_width=320),
        ).add_to(map_object)

        vertices = detail.get("route_vertices") if detail else None
        if not isinstance(vertices, list) or not vertices:
            vertices = [(user_lat, user_lon), (shelter_latitude, shelter_longitude)]

        folium.PolyLine(
            locations=vertices,
            color=color,
            weight=4,
            opacity=0.85,
            dash_array="7 7" if detail and detail.get("source") == "straight_line" else None,
            tooltip=f"{row['대피소명']} 경로",
        ).add_to(map_object)

        for vertex_lat, vertex_lon in vertices:
            bounds.append([float(vertex_lat), float(vertex_lon)])
        bounds.append([shelter_latitude, shelter_longitude])

    if len(bounds) > 1:
        map_object.fit_bounds(bounds, padding=(24, 24))

    return map_object


def _apply_browser_location(location_payload: object) -> None:
    # 자동 모드일 때만 브라우저 좌표를 반영한다.
    # 수동 모드에서는 사용자가 직접 입력한 값을 절대 덮어쓰면 안 된다.
    if st.session_state.get("realtime_location_mode") != "auto":
        return

    if not isinstance(location_payload, dict):
        return

    latitude = location_payload.get("latitude")
    longitude = location_payload.get("longitude")
    if latitude in (None, "") or longitude in (None, ""):
        return

    try:
        st.session_state["realtime_lat"] = float(latitude)
        st.session_state["realtime_lon"] = float(longitude)
    except (TypeError, ValueError):
        return

    st.session_state["realtime_location_source"] = "browser"
    st.session_state["realtime_location_updated_at"] = _current_timestamp_label()


def _mark_manual_location() -> None:
    # 좌표 입력칸을 사용자가 건드린 순간부터는 자동 위치보다 수동 입력을 우선한다.
    st.session_state["realtime_location_mode"] = "manual"
    st.session_state["realtime_location_source"] = "manual"
    st.session_state["realtime_location_updated_at"] = _current_timestamp_label()


def _sync_default_coordinates(page2_module, shelters_frame: pd.DataFrame) -> None:
    # 첫 진입에서는 브라우저 권한이 아직 없을 수 있으므로,
    # 울산 북구 중심 좌표를 임시 기본값으로 채워 두고 이후 자동/수동 입력이 덮어쓰게 한다.
    st.session_state.setdefault("realtime_location_mode", "auto")
    st.session_state.setdefault("realtime_location_source", "fallback")
    st.session_state.setdefault("realtime_location_updated_at", "-")
    st.session_state.setdefault("realtime_selected_disaster", None)
    st.session_state.setdefault("realtime_last_request_id", "")

    if "realtime_lat" in st.session_state and "realtime_lon" in st.session_state:
        return

    default_latitude, default_longitude = page2_module.get_region_center(shelters_frame, "울산", "북구")
    if default_latitude is None or default_longitude is None:
        default_latitude, default_longitude = 35.633, 129.365

    st.session_state["realtime_lat"] = float(default_latitude)
    st.session_state["realtime_lon"] = float(default_longitude)
    st.session_state["realtime_location_source"] = "fallback"


def _prepare_destinations(recommendations: pd.DataFrame) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    # 지도 경로 상세와 추천 표를 다시 연결하려면
    # 정렬이 바뀌어도 흔들리지 않는 route_key가 필요하다.
    prepared = recommendations.head(3).copy().reset_index(drop=True)
    destinations: list[dict[str, object]] = []
    for index, row in prepared.iterrows():
        route_key = f"dest-{index}"
        prepared.at[index, "route_key"] = route_key
        destinations.append(
            {
                "key": route_key,
                "name": str(row["대피소명"]),
                "x": float(row["경도"]),
                "y": float(row["위도"]),
            }
        )
    return prepared, destinations


def _attach_route_sort(
    recommendations: pd.DataFrame,
    route_details: list[dict[str, object]],
) -> pd.DataFrame:
    # 추천 페이지는 직선 거리 기준이지만,
    # 실시간 페이지에서는 OSRM 도보 시간/거리 정보를 얻었으면 그 순서를 다시 반영한다.
    ordered = recommendations.copy()
    detail_by_key = {
        str(detail.get("destination_key", "")): detail
        for detail in route_details
        if detail.get("destination_key")
    }
    ordered["route_distance_m"] = ordered["route_key"].map(
        lambda key: detail_by_key.get(str(key), {}).get("route_distance_m")
    )
    ordered["route_duration_s"] = ordered["route_key"].map(
        lambda key: detail_by_key.get(str(key), {}).get("route_duration_s")
    )
    ordered["route_priority"] = ordered["route_key"].map(
        lambda key: 0 if detail_by_key.get(str(key), {}).get("source") == "osrm" else 1
    )
    ordered = ordered.sort_values(
        ["route_priority", "route_duration_s", "route_distance_m", "거리_km"],
        ascending=[True, True, True, True],
        na_position="last",
    ).reset_index(drop=True)
    return ordered.drop(columns=["route_priority"])


def _build_route_bundle(
    recommendations: pd.DataFrame,
    user_latitude: float,
    user_longitude: float,
    osrm_base_url: str | None,
    osrm_profile: str = DEFAULT_OSRM_PROFILE,
    page2_module=None,
) -> tuple[pd.DataFrame, list[dict[str, object]], list[str]]:
    # 목적지별로 OSRM을 호출하고, 실패한 목적지만 개별 fallback 처리한다.
    # 그래야 일부 경로만 실패해도 나머지 결과는 그대로 살릴 수 있다.
    recommendation_page_module = page2_module or load_recommendation_page_module()
    prepared, destinations = _prepare_destinations(recommendations)
    origin = {"x": user_longitude, "y": user_latitude, "key": "origin", "name": "현재 위치"}
    warnings: list[str] = []
    route_details: list[dict[str, object]] = []

    destination_by_key = {destination["key"]: destination for destination in destinations}
    if not osrm_base_url:
        warnings.append("OSRM_BASE_URL 설정이 없어 직선 fallback 경로를 표시합니다.")

    for _, row in prepared.iterrows():
        route_key = str(row["route_key"])
        destination = destination_by_key[route_key]
        if osrm_base_url:
            try:
                detail = _get_osrm_route_detail(origin, destination, osrm_base_url, osrm_profile)
            except Exception as exc:
                warnings.append(f"{row['대피소명']} 도보 경로 조회 실패: {exc}")
                detail = _build_straight_line_route_detail(
                    origin,
                    destination,
                    recommendation_page_module,
                    reason="osrm route lookup failed",
                )
        else:
            detail = _build_straight_line_route_detail(
                origin,
                destination,
                recommendation_page_module,
                reason="missing osrm base url",
            )

        route_details.append(detail)

    prepared = _attach_route_sort(prepared, route_details)
    return prepared, route_details, warnings


def _build_request_id(
    selected_disaster: str,
    coordinates: tuple[float, float],
    recommendations: pd.DataFrame,
    osrm_base_url: str | None,
    osrm_profile: str,
) -> str:
    # 같은 재난, 같은 좌표, 같은 추천 결과라면
    # rerun 때 OSRM과 folium 생성을 매번 다시 하지 않도록 캐시 키를 만든다.
    latitude, longitude = coordinates
    shelter_tokens = "|".join(
        f"{row['대피소명']}:{row['위도']}:{row['경도']}" for _, row in recommendations.iterrows()
    )
    routing_signature = f"{osrm_profile}:{osrm_base_url or 'straight-line'}"
    return f"{selected_disaster}|{latitude:.6f}|{longitude:.6f}|{routing_signature}|{shelter_tokens}"


def render_page() -> None:
    st.set_page_config(
        page_title=f"{APP_TITLE} | {PAGE_LABEL}",
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    page2_module = load_recommendation_page_module()

    st.title("2. 실시간 테스트")
    st.write("브라우저 위치를 받아 재난 유형별 대피소 3곳과 OSRM 도보 경로를 한 화면에서 테스트한다.")
    st.caption("재난 자동 분류는 아직 넣지 않고, 현재는 위치 자동 입력 + 수동 재난 선택 + 도보 경로 호출까지만 확인한다.")

    try:
        alerts_frame = load_alerts_dataframe()
        shelters_frame = load_shelters_dataframe()
        earthquake_shelters_frame = load_earthquake_shelters_dataframe()
        tsunami_shelters_frame = load_tsunami_shelters_dataframe()
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.stop()

    _sync_default_coordinates(page2_module, shelters_frame)

    st.sidebar.header("실시간 테스트 조건")
    # auto/manual 모드는 session_state에서 계속 유지된다.
    # 이 값이 바뀌면 브라우저 위치 반영 규칙도 함께 바뀐다.
    st.sidebar.radio(
        "위치 입력 방식",
        options=["auto", "manual"],
        format_func=lambda mode: "자동" if mode == "auto" else "수동",
        key="realtime_location_mode",
        horizontal=True,
    )

    if st.session_state["realtime_location_mode"] == "auto":
        if streamlit_geolocation is None:
            st.sidebar.warning("`streamlit-geolocation` 을 불러오지 못해 자동 위치를 쓸 수 없다. 필요하면 좌표를 직접 입력해 주세요.")
        else:
            st.sidebar.caption("브라우저 위치 권한을 허용하면 현재 좌표가 아래 입력칸으로 자동 채워진다.")
            _apply_browser_location(streamlit_geolocation())
    else:
        st.sidebar.caption("수동 모드에서는 아래 위경도 입력값을 유지한다.")

    st.sidebar.number_input(
        "위도",
        min_value=30.0,
        max_value=45.0,
        step=0.0001,
        format="%.6f",
        key="realtime_lat",
        on_change=_mark_manual_location,
    )
    st.sidebar.number_input(
        "경도",
        min_value=120.0,
        max_value=140.0,
        step=0.0001,
        format="%.6f",
        key="realtime_lon",
        on_change=_mark_manual_location,
    )

    coordinates = get_browser_or_manual_coordinates(st.session_state)
    if coordinates is None:
        st.warning("현재 좌표를 읽지 못했다. 수동 좌표를 입력해 주세요.")
        st.stop()

    selected_latitude, selected_longitude = coordinates
    detected_region = page2_module.infer_region_from_coordinates(
        shelters_frame,
        latitude=float(selected_latitude),
        longitude=float(selected_longitude),
    )
    active_sido = str(detected_region.get("sido") or "울산")
    active_sigungu = str(detected_region.get("sigungu") or "북구")

    disaster_options = page2_module.get_disaster_options(alerts_frame, active_sido, active_sigungu)
    st.sidebar.selectbox(
        "재난 유형",
        options=disaster_options,
        index=None,
        placeholder="재난 유형 선택",
        key="realtime_selected_disaster",
    )

    selected_disaster = st.session_state.get("realtime_selected_disaster")
    recent_alerts = page2_module.get_recent_alerts(alerts_frame, active_sido, active_sigungu, limit=5)
    alert_summary = page2_module.build_alert_summary(alerts_frame, active_sido, active_sigungu)

    if not page2_module.should_compute_recommendations(selected_disaster):
        recommendations = pd.DataFrame(columns=page2_module.RECOMMENDATION_RESULT_COLUMNS)
    else:
        recommendations = page2_module.recommend_shelters(
            shelters_frame=shelters_frame,
            earthquake_shelters_frame=earthquake_shelters_frame,
            tsunami_shelters_frame=tsunami_shelters_frame,
            disaster_group=str(selected_disaster),
            latitude=float(selected_latitude),
            longitude=float(selected_longitude),
            sido=active_sido,
            sigungu=active_sigungu,
            top_n=3,
        )

    osrm_base_url, osrm_profile = _get_osrm_config()
    route_details: list[dict[str, object]] = []
    route_warnings: list[str] = []
    map_html = ""

    if not recommendations.empty:
        request_id = _build_request_id(
            str(selected_disaster),
            coordinates,
            recommendations,
            osrm_base_url,
            osrm_profile,
        )
        if st.session_state.get("realtime_last_request_id") == request_id:
            # 같은 요청이라면 이전 계산 결과를 재사용해서 rerun 비용을 줄인다.
            recommendations = st.session_state.get("realtime_cached_recommendations", recommendations)
            route_details = st.session_state.get("realtime_cached_route_details", [])
            map_html = str(st.session_state.get("realtime_cached_map_html", ""))
            route_warnings = st.session_state.get("realtime_cached_route_warnings", [])
        else:
            recommendations, route_details, route_warnings = _build_route_bundle(
                recommendations,
                user_latitude=float(selected_latitude),
                user_longitude=float(selected_longitude),
                osrm_base_url=osrm_base_url,
                osrm_profile=osrm_profile,
                page2_module=page2_module,
            )
            map_html = build_realtime_recommendation_map(
                user_lat=float(selected_latitude),
                user_lon=float(selected_longitude),
                recommendations=recommendations,
                route_details=route_details,
            )._repr_html_()
            st.session_state["realtime_last_request_id"] = request_id
            st.session_state["realtime_cached_recommendations"] = recommendations
            st.session_state["realtime_cached_route_details"] = route_details
            st.session_state["realtime_cached_map_html"] = map_html
            st.session_state["realtime_cached_route_warnings"] = route_warnings

    metric_columns = st.columns(4)
    metric_columns[0].metric("위치 소스", _format_location_source_label(st.session_state.get("realtime_location_source")))
    metric_columns[1].metric("감지 지역", f"{active_sido} {active_sigungu}")
    metric_columns[2].metric("선택 재난", "-" if not selected_disaster else str(selected_disaster))
    metric_columns[3].metric("추천 대피소 수", f"{len(recommendations):.0f}" if not recommendations.empty else "-")

    left_column, right_column = st.columns([1.0, 1.15], gap="large")

    with left_column:
        with st.container(border=True):
            st.subheader("현재 테스트 상태")
            st.markdown(f"- 현재 좌표: **{selected_latitude:.6f}, {selected_longitude:.6f}**")
            st.markdown(f"- 감지 지역: **{active_sido} {active_sigungu}**")
            st.markdown(
                f"- 최근 알림 시각: **{'-' if alert_summary['latest_time'] is None else pd.Timestamp(alert_summary['latest_time']).strftime('%Y-%m-%d %H:%M')}**"
            )
            st.markdown(
                f"- 위치 갱신 시각: **{st.session_state.get('realtime_location_updated_at', '-')}**"
            )
            if recent_alerts.empty:
                st.caption("현재 감지 지역과 매칭된 알림이 없어도 재난 선택 옵션은 기본 목록을 기준으로 보여준다.")

        if selected_disaster and recommendations.empty:
            st.info("현재 조건으로 추천할 대피소가 없다.")
        elif not selected_disaster:
            st.info("재난 유형을 선택하면 대피소 3곳과 도보 경로를 계산한다.")
        else:
            detail_by_key = {
                str(detail.get("destination_key", "")): detail
                for detail in route_details
                if detail.get("destination_key")
            }
            card_columns = st.columns(min(len(recommendations), 3))
            for index, (_, row) in enumerate(recommendations.iterrows()):
                detail = detail_by_key.get(str(row.get("route_key", "")), {})
                with card_columns[index]:
                    with st.container(border=True):
                        st.subheader(f"Top {index + 1}. {row['대피소명']}")
                        st.markdown(f"**구분**: {row['추천구분']}")
                        st.markdown(f"**실경로 거리**: {format_distance_m(detail.get('route_distance_m'))}")
                        st.markdown(f"**예상 시간**: {format_duration_s(detail.get('route_duration_s'))}")
                        st.markdown(f"**직선 거리**: {float(row['거리_km']):.2f} km")
                        st.markdown(f"**주소**: {row['주소']}")
                        if detail.get("source") == "straight_line":
                            st.caption("OSRM 도보 경로 대신 직선 fallback 을 표시 중")

        if route_warnings:
            for warning in dict.fromkeys(route_warnings):
                st.warning(warning)

    with right_column:
        with st.container(border=True):
            st.subheader("실시간 경로 지도")
            if not selected_disaster:
                st.info("재난 유형을 선택하면 사용자 위치와 대피소 3곳 경로를 지도에 표시한다.")
            elif recommendations.empty:
                st.info("표시할 추천 결과가 없다.")
            else:
                components.html(map_html, height=560)
                st.caption("내 위치 1개, 대피소 3개, 각 경로 3개만 표시한다.")

    st.divider()

    bottom_left, bottom_right = st.columns([0.95, 1.05], gap="large")
    with bottom_left:
        with st.container(border=True):
            st.subheader("최근 알림 이력")
            if recent_alerts.empty:
                st.info("현재 감지 지역의 최근 알림 이력이 없다.")
            else:
                alert_display = recent_alerts.copy()
                alert_display["발표시간"] = alert_display["발표시간"].dt.strftime("%Y-%m-%d %H:%M")
                st.dataframe(
                    alert_display[["발표시간", "지역", "시군구", "재난종류", "특보등급"]],
                    use_container_width=True,
                    hide_index=True,
                )

    with bottom_right:
        with st.container(border=True):
            st.subheader("추천 결과 표")
            if recommendations.empty:
                st.info("추천 결과가 아직 없다.")
            else:
                detail_by_key = {
                    str(detail.get("destination_key", "")): detail
                    for detail in route_details
                    if detail.get("destination_key")
                }
                display_frame = recommendations.copy()
                display_frame["실경로 거리"] = display_frame["route_key"].map(
                    lambda key: format_distance_m(detail_by_key.get(str(key), {}).get("route_distance_m"))
                )
                display_frame["예상 시간"] = display_frame["route_key"].map(
                    lambda key: format_duration_s(detail_by_key.get(str(key), {}).get("route_duration_s"))
                )
                display_frame["직선 거리"] = display_frame["거리_km"].map(lambda value: f"{float(value):.2f} km")
                st.dataframe(
                    display_frame[
                        ["대피소명", "추천구분", "대피소유형", "실경로 거리", "예상 시간", "직선 거리", "주소"]
                    ],
                    use_container_width=True,
                    hide_index=True,
                )


if os.environ.get("PROJECT_DASHBOARD_IMPORT_ONLY") != "1":
    render_page()
