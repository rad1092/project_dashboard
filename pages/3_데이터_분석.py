from __future__ import annotations

import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app import (
    APP_ICON,
    APP_TITLE,
    configure_page,
    render_page_title,
    render_section_header,
    style_plotly_figure,
)
from dashboard_data import (
    ANALYSIS_COLUMNS,
    build_kpis,
    load_analysis_dataset,
    load_shelters_dataframe,
    load_shelters_dataframe_uncached,
)

PAGE_LABEL = "데이터 분석"
COLOR_SEQUENCE = ["#14b8a6", "#38bdf8", "#f59e0b", "#fb7185", "#c084fc"]


def _build_empty_figure(message: str) -> go.Figure:
    figure = go.Figure()
    figure.add_annotation(text=message, showarrow=False, font=dict(size=16, color="#e5eef9"))
    figure.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(t=40, b=20, l=20, r=20),
    )
    return style_plotly_figure(figure)


def build_alert_trend_chart(dataframe: pd.DataFrame) -> go.Figure:
    if dataframe.empty:
        return _build_empty_figure("선택한 조건에 맞는 특보 데이터가 없습니다.")

    summary = (
        dataframe.assign(발표일=dataframe["발표시간"].dt.strftime("%Y-%m-%d"))
        .groupby(["발표일", "재난그룹"], as_index=False)
        .size()
        .rename(columns={"size": "건수"})
    )
    figure = px.line(
        summary,
        x="발표일",
        y="건수",
        color="재난그룹",
        markers=True,
        color_discrete_sequence=COLOR_SEQUENCE,
    )
    figure.update_layout(
        title="일자별 재난 그룹 추이",
        margin=dict(t=60, b=20, l=20, r=20),
        legend_title_text="재난 그룹",
    )
    figure.update_xaxes(title="")
    figure.update_yaxes(title="특보 건수")
    return style_plotly_figure(figure)


def build_region_alert_chart(dataframe: pd.DataFrame) -> go.Figure:
    if dataframe.empty:
        return _build_empty_figure("선택한 조건에 맞는 지역 데이터가 없습니다.")

    summary = (
        dataframe.groupby("지역", as_index=False)
        .size()
        .rename(columns={"size": "건수"})
        .sort_values("건수", ascending=False)
    )
    figure = px.bar(
        summary,
        x="지역",
        y="건수",
        color="지역",
        text_auto=True,
        color_discrete_sequence=COLOR_SEQUENCE,
    )
    figure.update_layout(
        title="지역별 특보 건수",
        showlegend=False,
        margin=dict(t=60, b=20, l=20, r=20),
    )
    figure.update_xaxes(title="")
    figure.update_yaxes(title="특보 건수")
    return style_plotly_figure(figure)


def build_hazard_share_chart(dataframe: pd.DataFrame) -> go.Figure:
    if dataframe.empty:
        return _build_empty_figure("선택한 조건에 맞는 재난 종류 데이터가 없습니다.")

    summary = (
        dataframe.groupby("재난종류", as_index=False)
        .size()
        .rename(columns={"size": "건수"})
        .sort_values("건수", ascending=False)
    )
    figure = px.pie(
        summary,
        names="재난종류",
        values="건수",
        hole=0.55,
        color="재난종류",
        color_discrete_sequence=COLOR_SEQUENCE,
    )
    figure.update_layout(
        title="재난 종류 비중",
        margin=dict(t=60, b=20, l=20, r=20),
        legend_title_text="재난 종류",
    )
    return style_plotly_figure(figure)


def build_shelter_type_chart(dataframe: pd.DataFrame) -> go.Figure:
    if dataframe.empty:
        return _build_empty_figure("선택한 조건에 맞는 대피소 데이터가 없습니다.")

    summary = (
        dataframe.assign(대피소유형=dataframe["대피소유형"].fillna("미분류"))
        .groupby("대피소유형", as_index=False)
        .size()
        .rename(columns={"size": "건수"})
        .sort_values("건수", ascending=False)
    )
    figure = px.bar(
        summary,
        x="대피소유형",
        y="건수",
        color="대피소유형",
        text_auto=True,
        color_discrete_sequence=COLOR_SEQUENCE,
    )
    figure.update_layout(
        title="대피소 유형 분포",
        showlegend=False,
        margin=dict(t=60, b=20, l=20, r=20),
    )
    figure.update_xaxes(title="")
    figure.update_yaxes(title="대피소 수")
    return style_plotly_figure(figure)


def render_page() -> None:
    configure_page(
        page_title=f"{APP_TITLE} | {PAGE_LABEL}",
        page_icon=APP_ICON,
        set_page_config=False,
    )

    render_page_title(PAGE_LABEL)

    try:
        shelters_frame = load_shelters_dataframe()
        dataframe = load_analysis_dataset()
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.stop()

    st.sidebar.header("분석 필터")

    sidos = sorted(dataframe["지역"].dropna().unique().tolist())
    groups = sorted(dataframe["재난그룹"].dropna().unique().tolist())
    grades = sorted(dataframe["특보등급"].dropna().unique().tolist())

    selected_sidos = st.sidebar.multiselect("지역", options=sidos, default=sidos)
    selected_groups = st.sidebar.multiselect("재난그룹", options=groups, default=groups)
    selected_grades = st.sidebar.multiselect("특보등급", options=grades, default=grades)

    filtered = dataframe[
        dataframe["지역"].isin(selected_sidos)
        & dataframe["재난그룹"].isin(selected_groups)
        & dataframe["특보등급"].isin(selected_grades)
    ].copy()

    if filtered.empty:
        st.warning("선택한 조건에 맞는 분석 데이터가 없습니다. 필터를 조정해 주세요.")
        return

    kpis = build_kpis(filtered)
    regional_shelters = shelters_frame[shelters_frame["시도"].isin(selected_sidos)]
    latest_period = (
        "-"
        if kpis["latest_period"] is None or pd.isna(kpis["latest_period"])
        else pd.Timestamp(kpis["latest_period"]).strftime("%Y-%m-%d %H:%M")
    )

    tabs = st.tabs(["특보 추이", "지역/대피소", "분석 결과"])

    with tabs[0]:
        with st.container(border=True):
            render_section_header("일자별 특보 추이", "날짜별 특보 흐름을 확인합니다.")
            st.plotly_chart(build_alert_trend_chart(filtered), use_container_width=True)

    with tabs[1]:
        chart_left, chart_right = st.columns(2, gap="large")
        with chart_left:
            with st.container(border=True):
                render_section_header("지역별 특보", "특보가 몰린 지역을 비교합니다.")
                st.plotly_chart(build_region_alert_chart(filtered), use_container_width=True)
        with chart_right:
            with st.container(border=True):
                render_section_header("대피소 유형", "선택한 지역의 대피소 구성을 확인합니다.")
                st.plotly_chart(build_shelter_type_chart(regional_shelters), use_container_width=True)

    with tabs[2]:
        with st.container(border=True):
            render_section_header("현재 필터", "지금 보고 있는 분석 범위입니다.")
            st.markdown(f"- 지역 {len(selected_sidos)}개")
            st.markdown(f"- 재난그룹 {len(selected_groups)}개")
            st.markdown(f"- 특보등급 {len(selected_grades)}개")
            st.markdown(f"- 최신 시각 {latest_period}")

        metric_columns = st.columns(4, gap="medium")
        metric_columns[0].metric("특보 기록", f"{float(kpis['alert_count']):,.0f}")
        metric_columns[1].metric("재난그룹", f"{float(kpis['disaster_count']):,.0f}")
        metric_columns[2].metric("경보 건수", f"{float(kpis['warning_count']):,.0f}")
        metric_columns[3].metric("지역", f"{float(kpis['region_count']):,.0f}")

        with st.container(border=True):
            render_section_header("재난 종류 비중", "현재 필터 기준 비중을 확인합니다.")
            st.plotly_chart(build_hazard_share_chart(filtered), use_container_width=True)

    with st.expander("원본 데이터", expanded=False):
        display_frame = filtered.copy()
        display_frame["발표시간"] = display_frame["발표시간"].dt.strftime("%Y-%m-%d %H:%M")
        st.dataframe(display_frame[ANALYSIS_COLUMNS], use_container_width=True, hide_index=True)


if os.environ.get("PROJECT_DASHBOARD_IMPORT_ONLY") != "1":
    render_page()
