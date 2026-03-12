from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard_data import (
    build_kpis,
    load_analysis_dataset,
    load_earthquake_shelters_dataframe,
    load_shelters_dataframe,
    load_tsunami_shelters_dataframe,
)

APP_TITLE = "재난 대피 대시보드"
APP_ICON = "🚨"

TEXT_PRIMARY = "#e5eef9"
TEXT_MUTED = "#94a3b8"

PAGE_META = {
    "home": {"label": "HOME", "url_path": ""},
    "simulation": {"label": "대피 안내 시뮬레이션", "url_path": "simulation"},
    "message_guidance": {"label": "실시간 대피 안내", "url_path": "live-guidance"},
    "analysis": {"label": "데이터 분석", "url_path": "analysis"},
    "map": {"label": "권역 대피소 지도", "url_path": "map"},
}

HOME_OVERVIEW_POINTS = [
    "대피 안내 시뮬레이션에서 현재 위치와 재난 유형 기준 대피 경로를 시연합니다.",
    "실시간 대피 안내에서 감지 지역 기준 최신 재난문자를 자동 반영한 안내를 확인합니다.",
    "데이터 분석에서 특보 흐름과 지역별 대피소 분포를 비교합니다.",
    "권역 대피소 지도에서 전체 대피소 위치를 한 화면으로 확인합니다.",
]


def configure_page(
    page_title: str,
    page_icon: str,
    *,
    initial_sidebar_state: str = "expanded",
    set_page_config: bool = True,
) -> None:
    if set_page_config:
        st.set_page_config(
            page_title=page_title,
            page_icon=page_icon,
            layout="wide",
            initial_sidebar_state=initial_sidebar_state,
        )


def render_page_title(title: str, caption: str = "") -> None:
    st.title(title)
    if caption:
        st.caption(caption)


def render_section_header(title: str, caption: str = "") -> None:
    st.subheader(title)
    if caption:
        st.caption(caption)


def render_bullet_list(items: Iterable[str]) -> None:
    for item in items:
        st.markdown(f"- {item}")


def style_plotly_figure(figure: go.Figure) -> go.Figure:
    figure.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(11, 18, 32, 0.24)",
        font=dict(color=TEXT_PRIMARY),
        legend=dict(
            bgcolor="rgba(8, 17, 28, 0.82)",
            bordercolor="rgba(36, 50, 68, 0.95)",
            borderwidth=1,
            font=dict(color=TEXT_PRIMARY),
        ),
        hoverlabel=dict(
            bgcolor="rgba(8, 17, 28, 0.94)",
            bordercolor="rgba(45, 212, 191, 0.28)",
            font=dict(color=TEXT_PRIMARY),
        ),
    )
    figure.update_xaxes(
        gridcolor="rgba(148, 163, 184, 0.16)",
        linecolor="rgba(148, 163, 184, 0.22)",
        zerolinecolor="rgba(148, 163, 184, 0.16)",
        tickfont=dict(color=TEXT_MUTED),
        title_font=dict(color=TEXT_MUTED),
    )
    figure.update_yaxes(
        gridcolor="rgba(148, 163, 184, 0.16)",
        linecolor="rgba(148, 163, 184, 0.22)",
        zerolinecolor="rgba(148, 163, 184, 0.16)",
        tickfont=dict(color=TEXT_MUTED),
        title_font=dict(color=TEXT_MUTED),
    )
    return figure


def render_home_page() -> None:
    configure_page(
        page_title=PAGE_META["home"]["label"],
        page_icon=APP_ICON,
        set_page_config=False,
    )

    try:
        shelters_frame = load_shelters_dataframe()
        earthquake_shelters_frame = load_earthquake_shelters_dataframe()
        tsunami_shelters_frame = load_tsunami_shelters_dataframe()
        analysis_frame = load_analysis_dataset()
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.info(
            "기본 실행은 저장소 내부 `preprocessing_data` 폴더를 사용합니다. "
            "다른 위치를 쓰려면 `.streamlit/secrets.toml` 또는 "
            "`PREPROCESSING_DATA_DIR` 환경변수로 경로를 지정하세요."
        )
        st.stop()

    kpis = build_kpis(analysis_frame)
    total_shelters = (
        len(shelters_frame) + len(earthquake_shelters_frame) + len(tsunami_shelters_frame)
    )
    latest_period = (
        "-"
        if kpis["latest_period"] is None or pd.isna(kpis["latest_period"])
        else pd.Timestamp(kpis["latest_period"]).strftime("%Y-%m-%d %H:%M")
    )

    render_page_title(PAGE_META["home"]["label"])

    metric_columns = st.columns(3, gap="large")
    metric_columns[0].metric("전체 대피소", f"{float(total_shelters):,.0f}")
    metric_columns[1].metric("지역", f"{float(kpis['region_count']):,.0f}")
    metric_columns[2].metric("기준 시각", latest_period)

    with st.container(border=True):
        render_section_header("개요", "현재 앱에서 바로 확인할 수 있는 화면입니다.")
        render_bullet_list(HOME_OVERVIEW_POINTS)


def build_navigation() -> list[st.Page]:
    base_dir = Path(__file__).resolve().parent
    return [
        st.Page(
            render_home_page,
            title=PAGE_META["home"]["label"],
            default=True,
            url_path=PAGE_META["home"]["url_path"],
        ),
        st.Page(
            base_dir / "pages" / "1_대피_안내_시뮬레이션.py",
            title=PAGE_META["simulation"]["label"],
            url_path=PAGE_META["simulation"]["url_path"],
        ),
        st.Page(
            base_dir / "pages" / "2_실시간_대피_안내.py",
            title=PAGE_META["message_guidance"]["label"],
            url_path=PAGE_META["message_guidance"]["url_path"],
        ),
        st.Page(
            base_dir / "pages" / "3_데이터_분석.py",
            title=PAGE_META["analysis"]["label"],
            url_path=PAGE_META["analysis"]["url_path"],
        ),
        st.Page(
            base_dir / "pages" / "4_권역_대피소_지도.py",
            title=PAGE_META["map"]["label"],
            url_path=PAGE_META["map"]["url_path"],
        ),
    ]


def main() -> None:
    configure_page(page_title=APP_TITLE, page_icon=APP_ICON)
    current_page = st.navigation(build_navigation(), position="sidebar")
    current_page.run()


if __name__ == "__main__" and os.environ.get("PROJECT_DASHBOARD_IMPORT_ONLY") != "1":
    main()
