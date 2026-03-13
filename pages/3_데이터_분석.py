from __future__ import annotations

import os
from html import escape
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from app import (
    ANALYSIS_COLUMNS,
    APP_ICON,
    APP_TITLE,
    build_kpis,
    configure_page,
    load_analysis_dataset,
    load_shelters_dataframe,
    load_shelters_dataframe_uncached,
    render_page_title,
    render_section_header,
    style_plotly_figure,
)

PAGE_LABEL = "데이터 분석"
MAP_FILE = Path(__file__).resolve().parents[1] / "preprocessing_code" / "shelter_type_layer_map1.html"
DEFAULT_MAP_HEIGHT = 680
COLOR_SEQUENCE = [
    "#22d3ee",
    "#60a5fa",
    "#f97316",
    "#fb7185",
    "#a78bfa",
    "#facc15",
    "#34d399",
    "#f472b6",
]
DISASTER_COLOR_MAP = {
    "호우": "#60a5fa",
    "폭염": "#f97316",
    "한파": "#67e8f9",
    "강풍": "#fb7185",
    "태풍": "#a78bfa",
    "대설": "#facc15",
    "건조": "#f59e0b",
    "폭풍해일": "#22d3ee",
}


def _build_empty_figure(message: str) -> go.Figure:
    figure = go.Figure()
    figure.add_annotation(text=message, showarrow=False, font=dict(size=16, color="#e5eef9"))
    figure.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(t=40, b=20, l=20, r=20),
    )
    return style_plotly_figure(figure)


def _format_latest_period(value: object) -> str:
    if value is None or pd.isna(value):
        return "-"
    return pd.Timestamp(value).strftime("%Y-%m-%d %H:%M")


@st.cache_data(show_spinner=False)
def load_map_html(path_value: str) -> str:
    path = Path(path_value)
    for encoding in ("utf-8-sig", "utf-8", "cp949"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue

    raise UnicodeDecodeError("unknown", b"", 0, 1, f"Unable to decode {path}")


def _get_color_map(values: list[str]) -> dict[str, str]:
    color_map: dict[str, str] = {}
    for index, value in enumerate(values):
        color_map[value] = DISASTER_COLOR_MAP.get(value, COLOR_SEQUENCE[index % len(COLOR_SEQUENCE)])
    return color_map


def build_disaster_legend_html(dataframe: pd.DataFrame) -> str:
    if dataframe.empty:
        return ""

    labels = dataframe["재난종류"].dropna().astype(str).drop_duplicates().tolist()
    color_map = _get_color_map(labels)
    items = "".join(
        f"<span style='display:flex;align-items:center;gap:0.5rem;'>"
        f"<span style='width:0.8rem;height:0.8rem;border-radius:999px;background:{color_map[label]};'></span>"
        f"<span style='color:#e5eef9;font-size:0.95rem;'>{escape(label)}</span>"
        f"</span>"
        for label in labels
    )
    return (
        "<div style='padding:0.4rem 0 0 0;'>"
        "<div style='color:#94a3b8;font-size:0.9rem;font-weight:600;margin-bottom:0.8rem;'>범례</div>"
        f"<div style='display:flex;flex-direction:column;gap:0.7rem;'>{items}</div>"
        "</div>"
    )


def filter_analysis_dataset(
    dataframe: pd.DataFrame,
    selected_regions: list[str],
    selected_disasters: list[str],
    selected_grades: list[str],
) -> pd.DataFrame:
    return dataframe[
        dataframe["지역"].isin(selected_regions)
        & dataframe["재난종류"].isin(selected_disasters)
        & dataframe["특보등급"].isin(selected_grades)
    ].copy()


def build_top_regions_by_disaster_chart(dataframe: pd.DataFrame) -> go.Figure:
    if dataframe.empty:
        return _build_empty_figure("선택한 조건에 맞는 재난 분포가 없습니다.")

    summary = (
        dataframe.groupby(["재난종류", "시군구"], as_index=False)
        .size()
        .rename(columns={"size": "발생건수"})
        .sort_values(["재난종류", "발생건수"], ascending=[True, False])
    )
    top_regions = summary.groupby("재난종류", group_keys=False).head(3)
    if top_regions.empty:
        return _build_empty_figure("재난종류별 상위 지역을 계산할 수 없습니다.")

    disaster_order = top_regions["재난종류"].drop_duplicates().tolist()
    rows = max(1, (len(disaster_order) + 3) // 4)
    figure = px.bar(
        top_regions,
        x="시군구",
        y="발생건수",
        color="재난종류",
        facet_col="재난종류",
        facet_col_wrap=4,
        text_auto=True,
        title="재난종류별 특보 발생 상위 지역",
        color_discrete_map=_get_color_map(disaster_order),
    )
    figure.for_each_annotation(lambda annotation: annotation.update(text=annotation.text.split("=")[-1]))
    figure.update_layout(showlegend=False, height=420 + ((rows - 1) * 180))
    figure.update_xaxes(title="")
    figure.update_yaxes(title="발생건수")
    return style_plotly_figure(figure)


def build_grade_distribution_chart(dataframe: pd.DataFrame) -> go.Figure:
    if dataframe.empty:
        return _build_empty_figure("선택한 조건에 맞는 특보등급 분포가 없습니다.")

    summary = (
        dataframe.groupby(["특보등급", "재난종류"], as_index=False)
        .size()
        .rename(columns={"size": "발생건수"})
    )
    color_map = _get_color_map(summary["재난종류"].drop_duplicates().tolist())
    present_grades = summary["특보등급"].drop_duplicates().tolist()
    show_single_grade_legend = len(present_grades) > 1

    def percent_labels(values: pd.Series) -> list[str]:
        total = float(values.sum())
        if total <= 0:
            return ["" for _ in values]
        return [f"{(value / total) * 100:.1f}%" if (value / total) * 100 >= 3 else "" for value in values]

    warning = summary[summary["특보등급"] == "경보"]
    advisory = summary[summary["특보등급"] == "주의보"]
    figure = go.Figure()

    if not advisory.empty:
        figure.add_trace(
            go.Pie(
                labels=advisory["재난종류"],
                values=advisory["발생건수"],
                hole=0.28,
                sort=False,
                direction="clockwise",
                name="주의보",
                marker=dict(colors=[color_map[value] for value in advisory["재난종류"]]),
                text=percent_labels(advisory["발생건수"]),
                textinfo="text",
                textposition="inside",
                domain=dict(x=[0.08, 0.92], y=[0.08, 0.92]),
                hovertemplate="주의보<br>%{label}: %{value}건 (%{percent})<extra></extra>",
                showlegend=show_single_grade_legend,
            )
        )

    if not warning.empty:
        figure.add_trace(
            go.Pie(
                labels=warning["재난종류"],
                values=warning["발생건수"],
                hole=0.28,
                sort=False,
                direction="clockwise",
                name="경보",
                marker=dict(colors=[color_map[value] for value in warning["재난종류"]]),
                text=percent_labels(warning["발생건수"]),
                textinfo="text",
                textposition="inside",
                domain=dict(x=[0.08, 0.92], y=[0.08, 0.92]) if advisory.empty else dict(x=[0.28, 0.72], y=[0.28, 0.72]),
                hovertemplate="경보<br>%{label}: %{value}건 (%{percent})<extra></extra>",
                showlegend=False,
            )
        )

    if figure.data:
        layout_kwargs: dict[str, object] = {
            "title": f"{present_grades[0]} 재난 분포" if len(present_grades) == 1 else "특보등급별 재난 분포"
        }
        if len(present_grades) > 1:
            layout_kwargs["annotations"] = [
                dict(
                    text="안쪽: 경보<br>바깥: 주의보",
                    x=1.07,
                    y=0.78,
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    font=dict(size=12, color="#cbd5e1"),
                    align="left",
                )
            ]
        figure.update_layout(**layout_kwargs)
    return style_plotly_figure(figure)


def build_daily_disaster_trend_chart(dataframe: pd.DataFrame) -> go.Figure:
    if dataframe.empty:
        return _build_empty_figure("선택한 조건에 맞는 날짜별 특보 추이가 없습니다.")

    summary = (
        dataframe.assign(날짜=dataframe["발표시간"].dt.strftime("%Y-%m-%d"))
        .groupby(["날짜", "재난종류"], as_index=False)
        .size()
        .rename(columns={"size": "발생건수"})
    )
    figure = px.line(
        summary,
        x="날짜",
        y="발생건수",
        color="재난종류",
        markers=True,
        title="재난종류별 특보 발생 날짜 추이",
        color_discrete_map=_get_color_map(summary["재난종류"].drop_duplicates().tolist()),
    )
    figure.update_xaxes(title="")
    figure.update_yaxes(title="발생건수")
    return style_plotly_figure(figure)


def build_monthly_distribution_chart(dataframe: pd.DataFrame) -> go.Figure:
    if dataframe.empty:
        return _build_empty_figure("선택한 조건에 맞는 월별 재난 분포가 없습니다.")

    summary = (
        dataframe.assign(년월=dataframe["발표시간"].dt.to_period("M").astype(str))
        .groupby(["년월", "재난종류"], as_index=False)
        .size()
        .rename(columns={"size": "발생건수"})
    )
    figure = px.bar(
        summary,
        x="년월",
        y="발생건수",
        color="재난종류",
        barmode="stack",
        title="월별 재난 발생 분포",
        color_discrete_map=_get_color_map(summary["재난종류"].drop_duplicates().tolist()),
    )
    figure.update_xaxes(title="", tickangle=0)
    figure.update_yaxes(title="발생건수")
    figure.update_layout(height=460, margin=dict(t=70, b=60, l=30, r=30))
    return style_plotly_figure(figure)


def build_region_disaster_counts_chart(dataframe: pd.DataFrame) -> go.Figure:
    if dataframe.empty:
        return _build_empty_figure("선택한 조건에 맞는 지역별 재난 비교가 없습니다.")

    summary = (
        dataframe.groupby(["지역", "특보등급", "재난종류"], as_index=False)
        .size()
        .rename(columns={"size": "발생건수"})
    )
    grades = summary["특보등급"].drop_duplicates().tolist()
    region_order = dataframe.groupby("지역").size().sort_values(ascending=False).index.tolist()
    chart_kwargs = dict(
        data_frame=summary,
        x="지역",
        y="발생건수",
        color="재난종류",
        barmode="stack",
        category_orders={"지역": region_order},
        color_discrete_map=_get_color_map(summary["재난종류"].drop_duplicates().tolist()),
    )
    if len(grades) == 1:
        figure = px.bar(
            title=f"지역별 {grades[0]} 현황",
            **chart_kwargs,
        )
    else:
        figure = px.bar(
            facet_col="특보등급",
            title="시도 기준 재난 종류별 특보 발생 건수",
            **chart_kwargs,
        )
        figure.for_each_annotation(lambda annotation: annotation.update(text=annotation.text.split("=")[-1]))
    figure.update_xaxes(title="")
    figure.update_yaxes(title="발생건수")
    return style_plotly_figure(figure)


def build_region_disaster_ratio_heatmap(dataframe: pd.DataFrame) -> go.Figure:
    if dataframe.empty:
        return _build_empty_figure("선택한 조건에 맞는 지역별 재난 비율이 없습니다.")

    counts = pd.pivot_table(
        dataframe,
        index="지역",
        columns="재난종류",
        values="발표시간",
        aggfunc="count",
        fill_value=0,
    )
    if counts.empty:
        return _build_empty_figure("히트맵을 그릴 수 있는 데이터가 없습니다.")

    ratios = counts.div(counts.sum(axis=1), axis=0).mul(100).round(1)
    figure = px.imshow(
        ratios,
        text_auto=".1f",
        aspect="auto",
        color_continuous_scale="YlOrRd",
        title="시도별 재난종류 비율",
    )
    figure.update_layout(coloraxis_colorbar=dict(title="비율(%)"))
    figure.update_xaxes(title="재난종류", side="top")
    figure.update_yaxes(title="지역")
    return style_plotly_figure(figure)


def summarize_shelters_by_region(dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataframe.empty:
        return pd.DataFrame(columns=["지역", "무더위쉼터_합계", "지진대피소_합계", "한파쉼터", "대피소_합계"])

    shelters = dataframe.copy()
    shelter_type = shelters["대피소유형"].fillna("")
    shelters["무더위쉼터_합계"] = shelter_type.str.contains("무더위쉼터", na=False).astype(int)
    shelters["지진대피소_합계"] = shelter_type.str.contains("지진옥외대피장소|지진해일대피장소", regex=True).astype(int)
    shelters["한파쉼터"] = shelter_type.str.contains("한파쉼터", na=False).astype(int)

    summary = (
        shelters.groupby("시도", as_index=False)[["무더위쉼터_합계", "지진대피소_합계", "한파쉼터"]]
        .sum()
        .rename(columns={"시도": "지역"})
    )
    summary["대피소_합계"] = summary[["무더위쉼터_합계", "지진대피소_합계", "한파쉼터"]].sum(axis=1)
    return summary.sort_values("대피소_합계", ascending=False).reset_index(drop=True)


def build_shelter_type_distribution_chart(dataframe: pd.DataFrame) -> go.Figure:
    summary = summarize_shelters_by_region(dataframe)
    if summary.empty:
        return _build_empty_figure("선택한 조건에 맞는 대피소 유형 분포가 없습니다.")

    figure = go.Figure()
    figure.add_bar(
        x=summary["지역"],
        y=summary["무더위쉼터_합계"],
        name="무더위쉼터",
        marker_color="#f97316",
        customdata=summary["대피소_합계"],
        hovertemplate="지역: %{x}<br>무더위쉼터: %{y}<br>총 대피소 수: %{customdata}<extra></extra>",
    )
    figure.add_bar(
        x=summary["지역"],
        y=summary["지진대피소_합계"],
        name="지진대피소",
        marker_color="#38bdf8",
        customdata=summary["대피소_합계"],
        hovertemplate="지역: %{x}<br>지진대피소: %{y}<br>총 대피소 수: %{customdata}<extra></extra>",
    )
    figure.add_bar(
        x=summary["지역"],
        y=summary["한파쉼터"],
        name="한파쉼터",
        marker_color="#22c55e",
        customdata=summary["대피소_합계"],
        hovertemplate="지역: %{x}<br>한파쉼터: %{y}<br>총 대피소 수: %{customdata}<extra></extra>",
    )
    figure.add_trace(
        go.Scatter(
            x=summary["지역"],
            y=summary["대피소_합계"],
            mode="text",
            text=summary["대피소_합계"],
            textposition="top center",
            showlegend=False,
            hoverinfo="skip",
        )
    )
    figure.update_layout(
        barmode="stack",
        title="지역별 대피소 분포",
        xaxis_title="지역",
        yaxis_title="대피소 수",
        hovermode="x unified",
    )
    return style_plotly_figure(figure)


def build_region_disaster_vs_shelter_chart(
    alerts_frame: pd.DataFrame,
    shelters_frame: pd.DataFrame,
) -> go.Figure:
    if alerts_frame.empty:
        return _build_empty_figure("선택한 조건에 맞는 재난 발생과 대피소 비교가 없습니다.")

    alert_summary = (
        alerts_frame.groupby("지역", as_index=False)
        .size()
        .rename(columns={"size": "재난발생횟수"})
    )
    shelter_summary = summarize_shelters_by_region(shelters_frame)[["지역", "대피소_합계"]]
    summary = (
        alert_summary.merge(shelter_summary, on="지역", how="left")
        .fillna({"대피소_합계": 0})
        .sort_values("재난발생횟수", ascending=False)
    )
    figure = px.scatter(
        summary,
        x="재난발생횟수",
        y="대피소_합계",
        text="지역",
        size="재난발생횟수",
        color="지역",
        title="지역별 재난 발생 횟수와 대피소 수 비교",
        color_discrete_sequence=COLOR_SEQUENCE,
    )
    figure.update_traces(
        textposition="top center",
        marker=dict(line=dict(width=1, color="rgba(15, 23, 42, 0.9)")),
    )
    figure.update_xaxes(title="재난 발생 횟수")
    figure.update_yaxes(title="대피소 수")
    return style_plotly_figure(figure)


def render_page() -> None:
    configure_page(
        page_title=f"{APP_TITLE} | {PAGE_LABEL}",
        page_icon=APP_ICON,
        set_page_config=False,
    )

    render_page_title(PAGE_LABEL, "원본 전처리 CSV를 다시 집계해 재난 흐름, 지역 비교, 권역 대피소 지도를 함께 보여줍니다.")

    try:
        alerts_frame = load_analysis_dataset()
        shelters_frame = load_shelters_dataframe()
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.stop()

    st.sidebar.header("분석 필터")
    regions = sorted(alerts_frame["지역"].dropna().unique().tolist())
    disasters = sorted(alerts_frame["재난종류"].dropna().unique().tolist())
    grades = sorted(alerts_frame["특보등급"].dropna().unique().tolist())

    selected_regions = st.sidebar.multiselect("지역", options=regions, default=regions)
    selected_disasters = st.sidebar.multiselect("재난종류", options=disasters, default=disasters)
    selected_grades = st.sidebar.multiselect("특보등급", options=grades, default=grades)

    filtered_alerts = filter_analysis_dataset(
        alerts_frame,
        selected_regions=selected_regions,
        selected_disasters=selected_disasters,
        selected_grades=selected_grades,
    )
    filtered_shelters = shelters_frame[shelters_frame["시도"].isin(selected_regions)].copy()

    if filtered_alerts.empty:
        st.warning("선택한 조건에 맞는 분석 데이터가 없습니다. 필터를 조정해 주세요.")

    kpis = build_kpis(filtered_alerts)
    latest_period = _format_latest_period(kpis["latest_period"])

    metric_columns = st.columns(4, gap="medium")
    metric_columns[0].metric("특보 기록", f"{float(kpis['alert_count']):,.0f}")
    metric_columns[1].metric("재난종류", f"{float(kpis['disaster_count']):,.0f}")
    metric_columns[2].metric("지역", f"{float(kpis['region_count']):,.0f}")
    metric_columns[3].metric("최신 특보", latest_period)

    tabs = st.tabs(["재난 분포", "시계열 추이", "지역 비교", "권역 대피소 지도"])

    with tabs[0]:
        with st.container(border=True):
            render_section_header("특보등급별 재난 분포", "경보와 주의보 안에서 어떤 재난이 비중을 차지하는지 비교합니다.")
            charts_col, legend_col = st.columns([5, 1], gap="large")
            with charts_col:
                warning_col, advisory_col = st.columns(2, gap="large")
                with warning_col:
                    st.plotly_chart(
                        build_grade_distribution_chart(filtered_alerts[filtered_alerts["특보등급"] == "경보"]),
                        use_container_width=True,
                    )
                with advisory_col:
                    st.plotly_chart(
                        build_grade_distribution_chart(filtered_alerts[filtered_alerts["특보등급"] == "주의보"]),
                        use_container_width=True,
                    )
            with legend_col:
                st.markdown(build_disaster_legend_html(filtered_alerts), unsafe_allow_html=True)

    with tabs[1]:
        with st.container(border=True):
            render_section_header("월별 재난 분포", "월 단위 누적 분포로 재난 발생 패턴을 봅니다.")
            st.plotly_chart(build_monthly_distribution_chart(filtered_alerts), use_container_width=True)

    with tabs[2]:
        advisory_col, warning_col, shelter_col = st.columns(3, gap="large")
        with advisory_col:
            with st.container(border=True):
                render_section_header("지역별 주의보 현황", "시도별 주의보 기준 재난 발생 분포를 확인합니다.")
                st.plotly_chart(
                    build_region_disaster_counts_chart(filtered_alerts[filtered_alerts["특보등급"] == "주의보"]),
                    use_container_width=True,
                )
        with warning_col:
            with st.container(border=True):
                render_section_header("지역별 경보 현황", "시도별 경보 기준 재난 발생 분포를 확인합니다.")
                st.plotly_chart(
                    build_region_disaster_counts_chart(filtered_alerts[filtered_alerts["특보등급"] == "경보"]),
                    use_container_width=True,
                )
        with shelter_col:
            with st.container(border=True):
                render_section_header("지역별 대피소 분포", "선택한 지역의 대피소 구성을 유형별로 합산해 보여줍니다.")
                st.plotly_chart(build_shelter_type_distribution_chart(filtered_shelters), use_container_width=True)

    with tabs[3]:
        if not MAP_FILE.exists():
            st.error(f"지도 HTML 파일을 찾지 못했습니다: {MAP_FILE}")
        else:
            with st.container(border=True):
                render_section_header("권역 대피소 지도", "권역 전체 대피소 지도를 한 화면에서 확인합니다.")
                components.html(load_map_html(str(MAP_FILE)), height=DEFAULT_MAP_HEIGHT, scrolling=False)

    with st.expander("원본 데이터", expanded=False):
        display_frame = filtered_alerts.copy()
        display_frame["발표시간"] = display_frame["발표시간"].dt.strftime("%Y-%m-%d %H:%M")
        st.dataframe(display_frame[ANALYSIS_COLUMNS], use_container_width=True, hide_index=True)


if os.environ.get("PROJECT_DASHBOARD_IMPORT_ONLY") != "1":
    render_page()
