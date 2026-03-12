from __future__ import annotations

import os

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from app import APP_ICON, APP_TITLE
from dashboard_data import (
    load_alerts_dataframe,
    load_earthquake_shelters_dataframe,
    load_shelters_dataframe,
    load_tsunami_shelters_dataframe,
)
from realtime_support import (
    _build_route_bundle,
    apply_browser_location,
    build_realtime_recommendation_map,
    build_request_id as _build_request_id,
    format_distance_m,
    format_duration_s,
    format_location_source_label as _format_location_source_label,
    get_browser_or_manual_coordinates,
    get_osrm_config as _get_osrm_config,
    load_recommendation_page_module,
    mark_manual_location,
    sync_default_coordinates,
)

try:
    from streamlit_geolocation import streamlit_geolocation
except Exception:  # pragma: no cover - optional dependency fallback
    streamlit_geolocation = None

PAGE_LABEL = "실시간 테스트"


def _apply_browser_location(location_payload: object) -> None:
    apply_browser_location(location_payload, prefix="realtime")


def _mark_manual_location() -> None:
    mark_manual_location(prefix="realtime")


def _sync_default_coordinates(page2_module, shelters_frame: pd.DataFrame) -> None:
    sync_default_coordinates(page2_module, shelters_frame, prefix="realtime")


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

    st.session_state.setdefault("realtime_selected_disaster", None)
    st.session_state.setdefault("realtime_last_request_id", "")
    _sync_default_coordinates(page2_module, shelters_frame)

    st.sidebar.header("실시간 테스트 조건")
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

    coordinates = get_browser_or_manual_coordinates(st.session_state, prefix="realtime")
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
                alert_display["발표시각"] = alert_display["발표시각"].dt.strftime("%Y-%m-%d %H:%M")
                st.dataframe(
                    alert_display[["발표시각", "지역", "시군구", "재난종류", "특보등급"]],
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
