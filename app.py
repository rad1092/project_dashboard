from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from dashboard_data import (
    ANALYSIS_COLUMNS,
    build_dataset_catalog,
    build_kpis,
    load_alerts_dataframe,
    load_alerts_dataframe_uncached,
    load_analysis_dataset,
    load_earthquake_shelters_dataframe,
    load_earthquake_shelters_dataframe_uncached,
    load_shelters_dataframe,
    load_shelters_dataframe_uncached,
    load_tsunami_shelters_dataframe,
    load_tsunami_shelters_dataframe_uncached,
)

APP_TITLE = "재난 대피소 추천 워크스페이스"
APP_ICON = "🛟"

# 홈 카드와 실제 페이지 제목이 어긋나지 않도록, 페이지 메타데이터는 여기 한 곳에서만 관리한다.
PAGE_META = {
    "home": {
        "label": "재난 대피소 추천 프로젝트 홈",
        "summary": "현재 데이터 상태와 주요 페이지 이동 흐름을 정리한 시작 화면",
    },
    "recommendation": {
        "label": "1. 대피소 추천",
        "summary": "좌표와 재난 유형을 기준으로 현재 조건에서 가까운 대피소 Top 3를 추천한다.",
    },
    "realtime": {
        "label": "2. 실시간 테스트",
        "summary": "브라우저 위치와 OSRM 도보 경로를 현재 추천 흐름에 붙여 테스트한다.",
    },
    "message_guidance": {
        "label": "4. 재난문자 대피 안내",
        "summary": "크롤링된 최근 재난문자를 현재 위치와 연결해 대피소와 경로를 안내한다.",
    },
    "analysis": {
        "label": "3. Data Analysis",
        "summary": "과거 특보 이력과 대피소 분포를 분석 관점에서 요약한다.",
    },
}

HOME_OVERVIEW_POINTS = [
    "과거 특보 이력과 대피소 좌표를 함께 읽어 현재 위치 기준의 대피소 추천 흐름을 제공한다.",
    "지진/해일 전용 대피소와 통합 대피소를 구분해 상황별 우선순위를 적용한다.",
    "추천 화면, 실험 화면, 재난문자 안내, 분석 화면을 분리해 결과와 근거를 함께 확인할 수 있게 한다.",
]

LIMITATIONS = [
    "현재 특보 데이터는 과거 전처리 CSV 기준이며 실시간 재난 상황을 보장하지 않는다.",
    "지도와 경로 표시는 무료 OSM/OSRM 기반이므로 실제 이동 환경과 차이가 날 수 있다.",
    "전용 대피소가 부족한 재난 유형은 통합 대피소를 fallback 후보로 함께 보여준다.",
]


def render_page() -> None:
    # 홈은 데이터를 직접 계산하는 곳이 아니라,
    # 공용 모듈이 정리한 결과를 "요약 화면"으로 보여주는 진입점이다.
    st.set_page_config(
        page_title=f"{APP_TITLE} | {PAGE_META['home']['label']}",
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title(PAGE_META["home"]["label"])
    st.write("이 앱은 전처리된 재난 특보 이력, 대피소 데이터, 크롤링된 재난문자를 바탕으로 추천, 실시간 테스트, 재난문자 안내, 분석 화면을 함께 제공한다.")
    st.caption("현재는 과거 데이터 기준으로 동작하며, 각 페이지는 같은 데이터 계약 위에서 역할만 나눠 보여준다.")

    try:
        # 홈 KPI와 데이터 상태 카드는 모두 같은 공용 로더를 쓰도록 맞춰 둔다.
        alerts_frame = load_alerts_dataframe()
        shelters_frame = load_shelters_dataframe()
        earthquake_shelters_frame = load_earthquake_shelters_dataframe()
        tsunami_shelters_frame = load_tsunami_shelters_dataframe()
        analysis_frame = load_analysis_dataset()
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.info(
            "기본 실행은 저장소 내부 `preprocessing_data` 폴더를 사용한다. "
            "다른 위치 데이터를 쓰려면 `.streamlit/secrets.toml` 또는 "
            "`PREPROCESSING_DATA_DIR` 환경변수로 경로를 지정하면 된다."
        )
        st.stop()

    kpis = build_kpis(analysis_frame)
    catalog = build_dataset_catalog(
        alerts_frame=alerts_frame,
        shelters_frame=shelters_frame,
        earthquake_shelters_frame=earthquake_shelters_frame,
        tsunami_shelters_frame=tsunami_shelters_frame,
    )

    metric_columns = st.columns(4)
    metric_columns[0].metric("특보 기록 수", f"{float(kpis['alert_count']):,.0f}")
    metric_columns[1].metric("통합 대피소 수", f"{float(len(shelters_frame)):,.0f}")
    metric_columns[2].metric("권역 수", f"{float(kpis['region_count']):,.0f}")
    metric_columns[3].metric(
        "최근 특보 시각",
        "-"
        if kpis["latest_period"] is None or pd.isna(kpis["latest_period"])
        else pd.Timestamp(kpis["latest_period"]).strftime("%Y-%m-%d %H:%M"),
    )

    st.divider()

    with st.container(border=True):
        st.subheader("앱 개요")
        for point in HOME_OVERVIEW_POINTS:
            st.markdown(f"- {point}")

    with st.container(border=True):
        st.subheader("페이지 이동")
        page_columns = st.columns(4, gap="large")
        for index, page_key in enumerate(["recommendation", "realtime", "message_guidance", "analysis"]):
            page = PAGE_META[page_key]
            with page_columns[index]:
                with st.container(border=True):
                    st.markdown(f"**{page['label']}**")
                    st.write(page["summary"])

    bottom_left, bottom_right = st.columns([1.0, 1.0], gap="large")

    with bottom_left:
        with st.container(border=True):
            st.subheader("현재 데이터 상태")
            for item in catalog:
                st.markdown(
                    f"- **{item['name']}**: {float(item['rows']):,.0f}건, {item['description']}"
                )

    with bottom_right:
        with st.container(border=True):
            st.subheader("핵심 한계")
            for item in LIMITATIONS:
                st.markdown(f"- {item}")


if __name__ == "__main__" and os.environ.get("PROJECT_DASHBOARD_IMPORT_ONLY") != "1":
    # 테스트나 다른 페이지 import 때는 홈이 자동 실행되면 안 되므로 환경변수로 진입을 막는다.
    render_page()
