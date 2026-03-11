import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app import APP_ICON, APP_TITLE
from dashboard_data import (
    ANALYSIS_COLUMNS,
    _get_desktop_default_data_dir,
    _get_repo_default_data_dir,
    _maybe_get_secret_data_dir,
    build_kpis,
    classify_disaster_type,
    load_alerts_dataframe,
    load_alerts_dataframe_uncached,
    load_analysis_dataset,
    load_shelters_dataframe,
    load_shelters_dataframe_uncached,
    resolve_data_dir,
)

PAGE_LABEL = "Data Analysis"
COLOR_SEQUENCE = ["#0f766e", "#1d4ed8", "#f59e0b", "#dc2626", "#0f172a"]


def _build_empty_figure(message: str) -> go.Figure:
    # 필터 결과가 비어 있어도 차트 영역 자체는 유지해야 화면이 덜 흔들린다.
    figure = go.Figure()
    figure.add_annotation(text=message, showarrow=False, font=dict(size=16))
    figure.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(t=40, b=20, l=20, r=20),
    )
    return figure


def build_alert_trend_chart(dataframe: pd.DataFrame) -> go.Figure:
    # 추천 페이지가 "한 번의 추천 결과"를 보여준다면,
    # 이 차트는 날짜별로 어떤 재난 그룹이 많이 나왔는지 흐름을 읽게 해 준다.
    if dataframe.empty:
        return _build_empty_figure("선택한 조건에 맞는 특보 데이터가 없다.")

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
    return figure


def build_region_alert_chart(dataframe: pd.DataFrame) -> go.Figure:
    # 어느 지역에 특보가 상대적으로 많이 쌓였는지를 빠르게 비교하는 차트다.
    if dataframe.empty:
        return _build_empty_figure("선택한 조건에 맞는 권역 데이터가 없다.")

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
        title="권역별 특보 건수",
        showlegend=False,
        margin=dict(t=60, b=20, l=20, r=20),
    )
    figure.update_xaxes(title="")
    figure.update_yaxes(title="특보 건수")
    return figure


def build_hazard_share_chart(dataframe: pd.DataFrame) -> go.Figure:
    # 재난그룹보다 더 세부적인 "재난종류" 비중을 보려고 따로 둔 차트다.
    if dataframe.empty:
        return _build_empty_figure("선택한 조건에 맞는 재난 종류 데이터가 없다.")

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
    return figure


def build_shelter_type_chart(dataframe: pd.DataFrame) -> go.Figure:
    # 특보 데이터와 별개로, 현재 연결된 대피소 데이터가 어떤 유형에 치우쳐 있는지 보여준다.
    if dataframe.empty:
        return _build_empty_figure("선택한 조건에 맞는 대피소 데이터가 없다.")

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
    return figure


def render_page() -> None:
    st.set_page_config(
        page_title=f"{APP_TITLE} | {PAGE_LABEL}",
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("3. Data Analysis")
    st.write("현재 앱이 참고하는 과거 재난 특보와 대피소 분포를 분석 관점에서 정리한 페이지입니다.")
    st.caption(
        "추천 페이지가 한 지역의 결과를 보여준다면, 이 페이지는 전체 데이터 흐름과 분포를 읽는 데 초점을 둡니다."
    )

    try:
        shelters_frame = load_shelters_dataframe()
        dataframe = load_analysis_dataset()
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.stop()

    st.sidebar.header("분석 필터")
    # 추천 페이지는 한 지역을 자동으로 골라 주지만,
    # 분석 페이지는 사용자가 여러 지역과 재난 그룹을 직접 좁혀 보는 흐름이다.
    sidos = sorted(dataframe["지역"].dropna().unique().tolist())
    groups = sorted(dataframe["재난그룹"].dropna().unique().tolist())
    grades = sorted(dataframe["특보등급"].dropna().unique().tolist())

    selected_sidos = st.sidebar.multiselect("시도", options=sidos, default=sidos)
    selected_groups = st.sidebar.multiselect("재난 그룹", options=groups, default=groups)
    selected_grades = st.sidebar.multiselect("특보 등급", options=grades, default=grades)

    filtered = dataframe[
        dataframe["지역"].isin(selected_sidos)
        & dataframe["재난그룹"].isin(selected_groups)
        & dataframe["특보등급"].isin(selected_grades)
    ].copy()

    if filtered.empty:
        st.warning("선택한 조건에 맞는 분석 데이터가 없다. 필터를 조금 넓혀 달라.")
        return

    kpis = build_kpis(filtered)
    metric_columns = st.columns(4)
    metric_columns[0].metric("특보 기록 수", f"{float(kpis['alert_count']):,.0f}")
    metric_columns[1].metric("재난 그룹 수", f"{float(kpis['disaster_count']):,.0f}")
    metric_columns[2].metric("경보 건수", f"{float(kpis['warning_count']):,.0f}")
    metric_columns[3].metric(
        "최근 특보 시각",
        "-"
        if kpis["latest_period"] is None or pd.isna(kpis["latest_period"])
        else pd.Timestamp(kpis["latest_period"]).strftime("%Y-%m-%d %H:%M"),
    )

    regional_shelters = shelters_frame[shelters_frame["시도"].isin(selected_sidos)]

    chart_left, chart_right = st.columns(2, gap="large")
    with chart_left:
        st.plotly_chart(build_alert_trend_chart(filtered), use_container_width=True)
        st.plotly_chart(build_region_alert_chart(filtered), use_container_width=True)
    with chart_right:
        st.plotly_chart(build_hazard_share_chart(filtered), use_container_width=True)
        st.plotly_chart(build_shelter_type_chart(regional_shelters), use_container_width=True)

    st.subheader("기상상세 특보 데이터")
    display_frame = filtered.copy()
    display_frame["발표시간"] = display_frame["발표시간"].dt.strftime("%Y-%m-%d %H:%M")
    st.dataframe(display_frame, use_container_width=True, hide_index=True)


if os.environ.get("PROJECT_DASHBOARD_IMPORT_ONLY") != "1":
    render_page()
