from __future__ import annotations

import os

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from app import APP_ICON, APP_TITLE
from crawler_alerts_data import (
    SUPPORTED_CRAWLED_REGIONS,
    build_empty_crawled_alerts_dataframe,
    get_recent_crawled_alerts,
    load_live_crawled_alerts_dataframe_uncached,
    select_default_crawled_alert,
)
from dashboard_data import (
    load_earthquake_shelters_dataframe,
    load_shelters_dataframe,
    load_tsunami_shelters_dataframe,
)
from realtime_support import (
    _build_route_bundle,
    apply_browser_location,
    build_realtime_recommendation_map,
    build_request_id,
    format_distance_m,
    format_duration_s,
    format_location_source_label,
    get_browser_or_manual_coordinates,
    get_osrm_config,
    load_prefixed_session_value,
    load_recommendation_page_module,
    mark_manual_location,
    sync_default_coordinates,
)

try:
    from streamlit_geolocation import streamlit_geolocation
except Exception:  # pragma: no cover - optional dependency fallback
    streamlit_geolocation = None

PAGE_LABEL = "재난문자 대피 안내"
STATE_PREFIX = "message_guidance"
EMPTY_OPTION_KEY = "__empty__"


def _state_key(name: str) -> str:
    return f"{STATE_PREFIX}_{name}"


def _apply_browser_location(location_payload: object) -> None:
    apply_browser_location(location_payload, prefix=STATE_PREFIX)


def _mark_manual_location() -> None:
    mark_manual_location(prefix=STATE_PREFIX)


def _sync_default_coordinates(page2_module, shelters_frame: pd.DataFrame) -> None:
    sync_default_coordinates(page2_module, shelters_frame, prefix=STATE_PREFIX)


def _get_live_crawled_alerts(refresh_requested: bool) -> tuple[pd.DataFrame, str | None]:
    cache_key = _state_key("live_crawled_alerts")
    should_reload = refresh_requested or cache_key not in st.session_state

    try:
        if should_reload:
            with st.spinner("실시간 재난문자를 확인하는 중..."):
                alerts = load_prefixed_session_value(
                    st.session_state,
                    prefix=STATE_PREFIX,
                    name="live_crawled_alerts",
                    loader=load_live_crawled_alerts_dataframe_uncached,
                    force_refresh=True,
                )
        else:
            alerts = load_prefixed_session_value(
                st.session_state,
                prefix=STATE_PREFIX,
                name="live_crawled_alerts",
                loader=load_live_crawled_alerts_dataframe_uncached,
            )
        return alerts, None
    except Exception as exc:
        cached_alerts = st.session_state.get(cache_key)
        if isinstance(cached_alerts, pd.DataFrame):
            return cached_alerts, f"실시간 크롤링 재시도에 실패해 직전 결과를 유지한다: {exc}"
        return build_empty_crawled_alerts_dataframe(), f"실시간 재난문자 크롤링을 실행하지 못했다: {exc}"


def _format_alert_option(alert: pd.Series) -> str:
    timestamp = pd.Timestamp(alert["발표시각"]).strftime("%Y-%m-%d %H:%M")
    return (
        f"{timestamp} | {alert['지역']} {alert['시군구']} | "
        f"{alert['재난종류']} | {alert['특보등급']}"
    )


def _format_selected_disaster_metric(alert_row: pd.Series | None) -> str:
    if alert_row is None:
        return "-"

    raw_disaster = str(alert_row["재난종류"])
    disaster_group = str(alert_row["재난그룹"])
    if raw_disaster == disaster_group:
        return raw_disaster
    return f"{raw_disaster} ({disaster_group})"


def resolve_region_alert_state(
    crawled_alerts: pd.DataFrame,
    active_sido: str,
    active_sigungu: str,
) -> tuple[bool, pd.DataFrame, dict[str, object] | None]:
    if active_sido not in SUPPORTED_CRAWLED_REGIONS:
        return False, pd.DataFrame(columns=crawled_alerts.columns), None

    recent_alerts = get_recent_crawled_alerts(crawled_alerts, active_sido, active_sigungu, limit=5)
    default_alert = select_default_crawled_alert(crawled_alerts, active_sido, active_sigungu)
    return True, recent_alerts, default_alert


def _select_sidebar_alert(recent_alerts: pd.DataFrame, default_alert: dict[str, object] | None) -> pd.Series | None:
    selected_key_name = _state_key("selected_alert_key")
    if recent_alerts.empty:
        st.session_state[selected_key_name] = None
        st.sidebar.selectbox(
            "최근 재난문자",
            options=[EMPTY_OPTION_KEY],
            index=0,
            format_func=lambda _: "선택 가능한 재난문자 없음",
            disabled=True,
            key=_state_key("empty_alert_select"),
        )
        return None

    alert_by_key = {str(row["alert_key"]): row for _, row in recent_alerts.iterrows()}
    option_keys = list(alert_by_key.keys())
    default_key = str(default_alert["alert_key"]) if default_alert is not None else option_keys[0]
    if st.session_state.get(selected_key_name) not in option_keys:
        st.session_state[selected_key_name] = default_key

    st.sidebar.selectbox(
        "최근 재난문자",
        options=option_keys,
        format_func=lambda key: _format_alert_option(alert_by_key[str(key)]),
        key=selected_key_name,
    )

    selected_key = st.session_state.get(selected_key_name)
    if selected_key not in alert_by_key:
        return None
    return alert_by_key[str(selected_key)]


def render_page() -> None:
    st.set_page_config(
        page_title=f"{APP_TITLE} | {PAGE_LABEL}",
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    page2_module = load_recommendation_page_module()

    st.title("4. 재난문자 대피 안내")
    st.write("크롤링된 최근 재난문자를 기준으로 현재 위치와 맞물린 대피소 3곳과 OSRM 경로를 안내한다.")
    st.caption("이 페이지는 `preprocessing_code/crawling.py`의 크롤링 로직을 즉시 한 번 실행해 메모리에서만 판단하고, CSV 저장 여부는 보지 않는다.")

    try:
        shelters_frame = load_shelters_dataframe()
        earthquake_shelters_frame = load_earthquake_shelters_dataframe()
        tsunami_shelters_frame = load_tsunami_shelters_dataframe()
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.stop()

    st.session_state.setdefault(_state_key("selected_alert_key"), None)
    st.session_state.setdefault(_state_key("last_request_id"), "")
    _sync_default_coordinates(page2_module, shelters_frame)

    st.sidebar.header("재난문자 안내 조건")
    refresh_requested = st.sidebar.button("실시간 재난문자 확인", use_container_width=True)
    crawled_alerts, crawl_error = _get_live_crawled_alerts(refresh_requested)
    crawl_updated_at = str(st.session_state.get(_state_key("live_crawled_alerts_updated_at"), "-"))
    st.sidebar.caption(f"최근 크롤링 확인: {crawl_updated_at}")

    st.sidebar.radio(
        "위치 입력 방식",
        options=["auto", "manual"],
        format_func=lambda mode: "자동" if mode == "auto" else "수동",
        key=_state_key("location_mode"),
        horizontal=True,
    )

    if crawl_error:
        st.warning(crawl_error)

    if st.session_state[_state_key("location_mode")] == "auto":
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
        key=_state_key("lat"),
        on_change=_mark_manual_location,
    )
    st.sidebar.number_input(
        "경도",
        min_value=120.0,
        max_value=140.0,
        step=0.0001,
        format="%.6f",
        key=_state_key("lon"),
        on_change=_mark_manual_location,
    )

    coordinates = get_browser_or_manual_coordinates(st.session_state, prefix=STATE_PREFIX)
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
    region_supported, recent_alerts, default_alert = resolve_region_alert_state(
        crawled_alerts,
        active_sido,
        active_sigungu,
    )
    selected_alert: pd.Series | None = None
    if region_supported:
        selected_alert = _select_sidebar_alert(recent_alerts, default_alert)
    else:
        st.session_state[_state_key("selected_alert_key")] = None
        st.sidebar.selectbox(
            "최근 재난문자",
            options=[EMPTY_OPTION_KEY],
            index=0,
            format_func=lambda _: "지원 지역 밖",
            disabled=True,
            key=_state_key("unsupported_alert_select"),
        )
        st.sidebar.caption("이 페이지는 대구·울산·부산·경북·경남 크롤링 데이터 기준으로 동작한다.")

    selected_alert_group = None
    recommendations = pd.DataFrame(columns=page2_module.RECOMMENDATION_RESULT_COLUMNS)
    if selected_alert is not None:
        selected_alert_group = str(selected_alert["재난그룹"])
        recommendations = page2_module.recommend_shelters(
            shelters_frame=shelters_frame,
            earthquake_shelters_frame=earthquake_shelters_frame,
            tsunami_shelters_frame=tsunami_shelters_frame,
            disaster_group=selected_alert_group,
            latitude=float(selected_latitude),
            longitude=float(selected_longitude),
            sido=active_sido,
            sigungu=active_sigungu,
            top_n=3,
        )

    osrm_base_url, osrm_profile = get_osrm_config()
    route_details: list[dict[str, object]] = []
    route_warnings: list[str] = []
    map_html = ""
    if selected_alert is not None and not recommendations.empty:
        request_id = build_request_id(
            str(selected_alert["alert_key"]),
            coordinates,
            recommendations,
            osrm_base_url,
            osrm_profile,
        )
        if st.session_state.get(_state_key("last_request_id")) == request_id:
            recommendations = st.session_state.get(_state_key("cached_recommendations"), recommendations)
            route_details = st.session_state.get(_state_key("cached_route_details"), [])
            map_html = str(st.session_state.get(_state_key("cached_map_html"), ""))
            route_warnings = st.session_state.get(_state_key("cached_route_warnings"), [])
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
            st.session_state[_state_key("last_request_id")] = request_id
            st.session_state[_state_key("cached_recommendations")] = recommendations
            st.session_state[_state_key("cached_route_details")] = route_details
            st.session_state[_state_key("cached_map_html")] = map_html
            st.session_state[_state_key("cached_route_warnings")] = route_warnings

    metric_columns = st.columns(5)
    metric_columns[0].metric("위치 소스", format_location_source_label(st.session_state.get(_state_key("location_source"))))
    metric_columns[1].metric("감지 지역", f"{active_sido} {active_sigungu}")
    metric_columns[2].metric("크롤링 문자 수", f"{len(crawled_alerts):.0f}")
    metric_columns[3].metric("선택 재난", _format_selected_disaster_metric(selected_alert))
    metric_columns[4].metric("추천 대피소 수", f"{len(recommendations):.0f}" if not recommendations.empty else "-")

    left_column, right_column = st.columns([1.0, 1.15], gap="large")
    with left_column:
        with st.container(border=True):
            st.subheader("현재 안내 상태")
            st.markdown(f"- 현재 좌표: **{selected_latitude:.6f}, {selected_longitude:.6f}**")
            st.markdown(f"- 감지 지역: **{active_sido} {active_sigungu}**")
            st.markdown(f"- 최근 크롤링 확인: **{crawl_updated_at}**")
            st.markdown(
                f"- 위치 갱신 시각: **{st.session_state.get(_state_key('location_updated_at'), '-')}**"
            )
            if not region_supported:
                st.info("이 페이지는 대구·울산·부산·경북·경남 5개 권역 크롤링 데이터 기준으로만 안내한다.")
            elif crawl_error and crawled_alerts.empty:
                st.info("실시간 크롤링 결과를 아직 확보하지 못했다.")
            elif recent_alerts.empty:
                st.info("현재 감지 지역에 매칭된 최근 크롤링 재난문자가 없다.")

        with st.container(border=True):
            st.subheader("선택 재난문자 상세")
            if selected_alert is None:
                st.info("선택된 재난문자가 없다.")
            else:
                st.markdown(f"- 발표시각: **{pd.Timestamp(selected_alert['발표시각']).strftime('%Y-%m-%d %H:%M')}**")
                st.markdown(f"- 특보등급: **{selected_alert['특보등급'] or '-'}**")
                st.markdown(f"- 발송기관: **{selected_alert['발송기관'] or '-'}**")
                st.markdown(f"- 시군구: **{selected_alert['시군구'] or '-'}**")
                st.markdown(f"- 재난그룹: **{selected_alert['재난그룹']}**")
                st.markdown(f"- 내용: {selected_alert['내용'] or '-'}")

        if selected_alert is not None and recommendations.empty:
            st.info("현재 조건으로 추천할 대피소가 없다.")
        elif selected_alert is None and region_supported and not recent_alerts.empty:
            st.info("최근 재난문자를 선택하면 대피소 3곳과 경로를 계산한다.")
        else:
            detail_by_key = {
                str(detail.get("destination_key", "")): detail
                for detail in route_details
                if detail.get("destination_key")
            }
            if not recommendations.empty:
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
            st.subheader("재난문자 기반 경로 지도")
            if not region_supported:
                st.info("지원 권역 안으로 위치가 들어오면 최근 재난문자와 대피 경로를 안내한다.")
            elif selected_alert is None:
                st.info("최근 재난문자를 선택하면 사용자 위치와 대피소 3곳 경로를 지도에 표시한다.")
            elif recommendations.empty:
                st.info("표시할 추천 결과가 없다.")
            else:
                components.html(map_html, height=560)
                st.caption("내 위치 1개, 대피소 3개, 각 경로 3개만 표시한다.")

    st.divider()

    bottom_left, bottom_right = st.columns([0.95, 1.05], gap="large")
    with bottom_left:
        with st.container(border=True):
            st.subheader("최근 재난문자")
            if not region_supported:
                st.info("이 위치는 크롤링 지원 권역 밖이다.")
            elif crawl_error and crawled_alerts.empty:
                st.info("실시간 크롤링 결과가 없어 최근 재난문자를 표시할 수 없다.")
            elif recent_alerts.empty:
                st.info("현재 감지 지역의 최근 크롤링 재난문자가 없다.")
            else:
                alert_display = recent_alerts.copy()
                alert_display["발표시각"] = alert_display["발표시각"].dt.strftime("%Y-%m-%d %H:%M")
                st.dataframe(
                    alert_display[["발표시각", "지역", "시군구", "재난종류", "특보등급", "발송기관"]],
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
