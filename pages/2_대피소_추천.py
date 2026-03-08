"""전처리 데이터 기반 대피소 추천 페이지.

이 페이지는 현재 앱의 핵심 기능을 담당한다.
사용자가 위도, 경도, 재난 유형을 정하면,
로컬 데이터 기준으로 지역을 자동 추정한 뒤 가까운 대피소 Top 3 를 추천한다.

중요한 설계 기준:
- 현재는 실시간 API를 쓰지 않는다.
- 지도는 무료 OSM 타일만 사용한다.
- 거리 계산은 직선 거리만 제공한다.
- 전용 대피소가 부족하면 통합 대피소를 대체 후보로 보여준다.
"""

from __future__ import annotations

import streamlit as st

from dashboard.components.disaster_map import render_recommendation_map
from dashboard.components.disaster_sections import render_recommendation_cards
from dashboard.components.layout import render_page_intro
from dashboard.config import apply_page_config
from dashboard.services.disaster_data import (
    build_alert_summary,
    get_available_regions,
    infer_region_from_coordinates,
    get_recent_alerts,
    get_region_center,
    get_sigungu_options,
    load_dataset_bundle,
)
from dashboard.services.shelter_recommendation import (
    get_disaster_options,
    recommend_shelters,
    select_priority_disaster,
)
from dashboard.utils.formatters import format_datetime, format_distance_km, format_number


apply_page_config("recommendation")

render_page_intro(
    "2 대피소 추천",
    "입력 좌표를 기준으로 지역을 자동 감지하고, 현재 데이터 안에서 가까운 대피소 Top 3 를 추천합니다.",
    "실제 경로 안내가 아니라 직선 거리 기준 추천이며, 지역 감지는 가장 가까운 지역 중심 좌표를 기준으로 동작합니다.",
)

try:
    # 추천 페이지는 시작 시점부터 실제 데이터셋에 의존하므로,
    # 데이터 묶음을 읽지 못하면 나머지 입력 UI 도 의미가 없어 바로 중단한다.
    bundle = load_dataset_bundle()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

# 수동 보정 UI 를 열었을 때는 실제 대피소 데이터가 있는 지역만 보여 주는 편이 혼란이 적다.
regions = get_available_regions(bundle)
sidos = sorted(regions["시도"].dropna().unique().tolist())

st.sidebar.header("추천 조건")
# 좌표 입력이 지금 페이지의 출발점이므로, 지역보다 먼저 기본 좌표 상태를 잡아 둔다.
if "recommendation_lat" not in st.session_state:
    st.session_state["recommendation_lat"] = 35.1796
if "recommendation_lon" not in st.session_state:
    st.session_state["recommendation_lon"] = 129.0756
if "use_manual_region" not in st.session_state:
    st.session_state["use_manual_region"] = False

# 아래 버튼은 미래 확장을 위한 자리표시자다.
# 실제 브라우저 geolocation 연동은 4번 페이지와 서비스 스텁에서만 설명하고, 지금은 실행하지 않는다.
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
# number_input 을 쓰는 이유는 자유 텍스트 입력보다 좌표 범위를 강하게 제한해
# 거리 계산과 지역 감지 함수에 잘못된 문자열이 들어가는 일을 줄이기 위해서다.

# 좌표를 먼저 받은 뒤, 가장 가까운 지역 중심을 찾아 현재 화면의 기본 지역으로 사용한다.
detected_region = infer_region_from_coordinates(
    bundle,
    latitude=float(selected_latitude),
    longitude=float(selected_longitude),
)
detected_sido = str(detected_region["sido"] or sidos[0])
detected_sigungu_options = get_sigungu_options(bundle, detected_sido)
detected_sigungu = (
    str(detected_region["sigungu"])
    if detected_region["sigungu"] in detected_sigungu_options
    else detected_sigungu_options[0]
)
# 자동 감지된 시군구가 옵션 목록에 없을 때 첫 옵션으로 되돌리는 이유는
# 데이터 갱신 뒤 옛 세션 상태나 표기 차이로 selectbox 가 깨지는 상황을 막기 위해서다.

# 수동 보정 UI 는 항상 열 수 있지만, 기본값은 현재 감지된 지역을 따라가게 맞춘다.
if "manual_sido" not in st.session_state or not st.session_state["use_manual_region"]:
    st.session_state["manual_sido"] = detected_sido
if "manual_sigungu" not in st.session_state or not st.session_state["use_manual_region"]:
    st.session_state["manual_sigungu"] = detected_sigungu
if st.session_state["manual_sido"] not in sidos:
    st.session_state["manual_sido"] = detected_sido

with st.sidebar.expander("지역 직접 수정", expanded=st.session_state["use_manual_region"]):
    # 자동 감지 기반으로 충분하지 않을 때만 사용자가 시도/시군구를 직접 보정하게 만든다.
    st.checkbox("감지 지역 대신 직접 수정", key="use_manual_region")
    st.selectbox("시도", options=sidos, key="manual_sido")

    manual_sigungu_options = get_sigungu_options(bundle, st.session_state["manual_sido"])
    if st.session_state.get("manual_sigungu") not in manual_sigungu_options:
        # 상위 시도 변경 뒤에도 이전 시군구가 남아 있으면 잘못된 조합이 되므로 현재 시도 기준 첫 옵션으로 맞춘다.
        st.session_state["manual_sigungu"] = manual_sigungu_options[0]

    st.selectbox("시군구", options=manual_sigungu_options, key="manual_sigungu")

    # 예전의 지역 중심 좌표 버튼은 유지하되, 이제는 수동 보정 지역을 좌표칸으로 반영하는 용도로 쓴다.
    manual_center_latitude, manual_center_longitude = get_region_center(
        bundle,
        st.session_state["manual_sido"],
        st.session_state["manual_sigungu"],
    )
    if st.button("보정 지역 중심 좌표 불러오기"):
        if manual_center_latitude is not None and manual_center_longitude is not None:
            # 세션 상태를 직접 갱신해야 number_input, 특보 요약, 추천 계산이 모두 같은 좌표를 즉시 공유한다.
            st.session_state["recommendation_lat"] = manual_center_latitude
            st.session_state["recommendation_lon"] = manual_center_longitude
            st.rerun()

# 특보 요약과 추천 후보 필터가 서로 다른 지역을 보지 않도록,
# 페이지는 항상 하나의 활성 지역(active region)만 골라 아래 서비스들에 공통으로 넘긴다.
if st.session_state["use_manual_region"]:
    active_sido = str(st.session_state["manual_sido"])
    active_sigungu = str(st.session_state["manual_sigungu"])
    region_source = "manual_override"
else:
    active_sido = detected_sido
    active_sigungu = detected_sigungu
    region_source = str(detected_region["source"])

disaster_options = get_disaster_options(bundle, active_sido, active_sigungu)
default_disaster = select_priority_disaster(bundle, active_sido, active_sigungu)
# 기본 재난 선택값도 active region 기준으로 계산해야
# 자동 감지 지역을 바꿨을 때 특보 요약과 selectbox 초기값이 같은 문맥으로 움직인다.
selected_disaster = st.sidebar.selectbox(
    "재난 유형",
    options=disaster_options,
    index=disaster_options.index(default_disaster) if default_disaster in disaster_options else 0,
)

# 페이지는 계산 로직을 직접 들고 있지 않고, 서비스가 만든 요약/추천 결과를 표시하는 역할에 집중한다.
alert_summary = build_alert_summary(bundle, active_sido, active_sigungu)
recent_alerts = get_recent_alerts(bundle, active_sido, active_sigungu, limit=5)
recommendations = recommend_shelters(
    bundle=bundle,
    disaster_group=selected_disaster,
    latitude=float(selected_latitude),
    longitude=float(selected_longitude),
    sido=active_sido,
    sigungu=active_sigungu,
)

# 상단 KPI 는 현재 선택 기준과 데이터 요약을 한 줄에서 읽게 만드는 상황판이다.
metric_columns = st.columns(4)
# st.columns 를 고정 4칸으로 두는 이유는 재난/시각/특보 수/추천 후보 수를 항상 같은 위치에서 비교하게 하기 위해서다.
metric_columns[0].metric("선택 재난", selected_disaster)
metric_columns[1].metric("최근 특보 시각", format_datetime(alert_summary["latest_time"]))
metric_columns[2].metric("최근 확인 특보 수", format_number(alert_summary["alert_count"]))
metric_columns[3].metric("추천 후보 수", format_number(len(recommendations)))

top_left, top_right = st.columns([1.1, 0.9], gap="large")

with top_left:
    with st.container(border=True):
        # 이 요약 영역은 좌표 입력이 어떤 지역으로 해석됐는지와,
        # 그 지역을 기준으로 어떤 특보/재난 흐름이 잡혔는지를 먼저 설명하는 곳이다.
        st.subheader("현재 좌표 기준 특보 요약")
        st.markdown(
            f"- 감지 지역: **{detected_sido} {detected_sigungu}** "
            f"({format_distance_km(detected_region['distance_km'])} 떨어진 지역 중심 기준)"
        )
        if region_source == "manual_override":
            st.markdown(f"- 보정 지역: **{active_sido} {active_sigungu}**")
        else:
            st.markdown(f"- 활성 지역: **{active_sido} {active_sigungu}**")

        if alert_summary["hazards"]:
            st.markdown("- 최근 특보 유형: " + ", ".join(alert_summary["hazards"]))
        else:
            st.markdown("- 최근 특보 데이터가 없어 수동 선택 재난 기준으로만 추천한다.")
        st.markdown(
            f"- 입력 좌표: **{selected_latitude:.4f}, {selected_longitude:.4f}**"
        )
        st.caption(
            "현재 지역 감지는 행정경계 기반이 아니라 가장 가까운 지역 중심 좌표 기준이다. "
            "감지 결과가 애매하면 사이드바의 `지역 직접 수정` 에서 보정할 수 있다."
        )
        if detected_region["distance_km"] is not None and float(detected_region["distance_km"]) > 40:
            st.warning("현재 좌표와 감지된 지역 중심 거리가 멀다. 필요하면 지역 직접 수정으로 보정해 달라.")

    # 카드 영역은 상위 후보를 빠르게 훑는 요약용 UI 다.
    render_recommendation_cards(recommendations)

with top_right:
    with st.container(border=True):
        st.subheader("추천 지도")
        render_recommendation_map(
            user_latitude=float(selected_latitude),
            user_longitude=float(selected_longitude),
            recommendations=recommendations,
            height=470,
        )
        st.caption("지도 위 선은 직선 거리 기준 연결선이며 실제 도로 경로를 의미하지 않는다.")

st.divider()

table_left, table_right = st.columns([0.95, 1.05], gap="large")

with table_left:
    with st.container(border=True):
        st.subheader("최근 특보 이력")
        if recent_alerts.empty:
            st.info("선택한 지역에서 바로 보여줄 최근 특보 이력이 없다.")
        else:
            alert_display = recent_alerts.copy()
            # 원본 Timestamp 는 표에서 너무 길게 보일 수 있어, 근거 표에서는 사람이 읽기 좋은 문자열로만 바꾼다.
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
            st.warning("현재 조건에서는 추천할 대피소가 없다. 지역이나 좌표를 조정해 달라.")
        else:
            display_frame = recommendations.copy()
            # 서비스가 표준 컬럼을 보장하므로, 페이지는 여기서 화면용 문자열만 덧입혀 렌더링한다.
            display_frame["거리"] = display_frame["거리_km"].map(format_distance_km)
            # 수용인원 원문 대신 정렬용 숫자 컬럼을 쓰는 이유는
            # 전용/통합 CSV 차이와 상관없이 이미 숫자로 정리된 값을 공통으로 사용하기 위해서다.
            display_frame["수용인원"] = display_frame["수용인원_정렬값"].map(
                lambda value: f"{format_number(value)}명"
            )
            st.dataframe(
                display_frame[
                    ["대피소명", "추천구분", "대피소유형", "거리", "수용인원", "주소", "추천사유"]
                ],
                use_container_width=True,
                hide_index=True,
            )
