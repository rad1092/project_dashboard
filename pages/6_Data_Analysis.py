"""과거 재난 특보와 대피소 분포를 보는 분석 페이지.

추천 페이지가 특정 좌표 기준 Top 3 를 보여 준다면,
이 페이지는 전체 특보 이력과 대피소 분포를 더 넓게 읽는 분석용 화면이다.
서비스 계층에서 만든 분석 DataFrame 과 차트 빌더를 조합해 사용한다.

초보자 메모:
- 추천 페이지가 한 좌표의 결과를 보는 곳이라면, 이 페이지는 전체 데이터의 패턴을 보는 곳이다.
- 코드도 `데이터 로드 -> 필터 선택 -> 필터 적용 -> KPI/차트/표 렌더링` 순서로 읽으면 이해가 쉽다.
"""

from __future__ import annotations

import streamlit as st

from dashboard.components.charts import (
    build_alert_trend_chart,
    build_hazard_share_chart,
    build_region_alert_chart,
    build_shelter_type_chart,
)
from dashboard.components.layout import render_page_intro
from dashboard.config import apply_page_config
from dashboard.services.analysis_data import build_kpis, load_analysis_dataset
from dashboard.services.disaster_data import load_dataset_bundle
from dashboard.utils.formatters import format_datetime, format_number


apply_page_config("analysis")

render_page_intro(
    "6 Data Analysis",
    "현재 앱이 참고하는 과거 재난 특보와 대피소 분포를 분석 관점에서 정리한 페이지입니다.",
    "추천 페이지가 한 지역의 결과를 보여준다면, 이 페이지는 전체 데이터 흐름과 분포를 읽는 데 초점을 둡니다.",
)

try:
    # 분석 화면은 특보 이력과 통합 대피소 분포를 함께 보므로 둘 다 시작 시점에 불러온다.
    bundle = load_dataset_bundle()
    dataframe = load_analysis_dataset()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

# 추천 페이지와 달리 분석은 여러 조건을 넓게 조합해 보는 흐름이라 다중 선택 필터를 사용한다.
# 기본값을 전체 선택으로 두는 이유는 첫 진입 시 빈 차트보다 전체 데이터 윤곽을 먼저 보여 주기 위해서다.
st.sidebar.header("분석 필터")
sidos = sorted(dataframe["지역"].dropna().unique().tolist())
groups = sorted(dataframe["재난그룹"].dropna().unique().tolist())
grades = sorted(dataframe["특보등급"].dropna().unique().tolist())
# unique().tolist() 는 DataFrame 열에서 중복 없는 선택지 목록을 만드는 전형적인 pandas 패턴이다.

selected_sidos = st.sidebar.multiselect("시도", options=sidos, default=sidos)
selected_groups = st.sidebar.multiselect("재난 그룹", options=groups, default=groups)
selected_grades = st.sidebar.multiselect("특보 등급", options=grades, default=grades)

# 차트와 표는 모두 같은 filtered DataFrame 을 공유해야 화면별 숫자가 어긋나지 않는다.
filtered = dataframe[
    dataframe["지역"].isin(selected_sidos)
    & dataframe["재난그룹"].isin(selected_groups)
    & dataframe["특보등급"].isin(selected_grades)
].copy()
# copy() 를 붙이는 이유는 이후 발표시간 문자열 변환 같은 화면용 조작을 해도 원본 분석 프레임을 건드리지 않기 위해서다.
# isin(...) 은 "선택된 목록 안에 들어 있는가"를 검사하는 pandas 필터 문법이다.

if filtered.empty:
    st.warning("선택한 조건에 맞는 분석 데이터가 없다. 필터를 조금 넓혀 달라.")
else:
    kpis = build_kpis(filtered)
    metric_columns = st.columns(4)
    metric_columns[0].metric("특보 기록 수", format_number(kpis["alert_count"]))
    metric_columns[1].metric("재난 그룹 수", format_number(kpis["disaster_count"]))
    metric_columns[2].metric("경보 건수", format_number(kpis["warning_count"]))
    metric_columns[3].metric("최근 특보 시각", format_datetime(kpis["latest_period"]))

    # 대피소 유형 분포는 현재 선택한 시도 집합에 맞춰 보여 줘야 특보 분석과 나란히 읽기 쉽다.
    regional_shelters = bundle.shelters[bundle.shelters["시도"].isin(selected_sidos)]
    # 특보 필터에서 고른 시도 범위와 대피소 분포 차트가 같은 지역 집합을 바라보게 맞춰 준다.

    chart_left, chart_right = st.columns(2, gap="large")
    with chart_left:
        # 왼쪽은 시간/지역처럼 "흐름과 규모"를 읽는 차트를 배치한다.
        st.plotly_chart(build_alert_trend_chart(filtered), use_container_width=True)
        st.plotly_chart(build_region_alert_chart(filtered), use_container_width=True)
    with chart_right:
        # 오른쪽은 비중과 구성 같은 비교형 차트를 묶어 한 번에 읽게 만든다.
        st.plotly_chart(build_hazard_share_chart(filtered), use_container_width=True)
        st.plotly_chart(build_shelter_type_chart(regional_shelters), use_container_width=True)

    st.subheader("상세 특보 데이터")
    display_frame = filtered.copy()
    # 차트는 요약을 보여 주고, 이 표는 근거가 되는 행 단위 원본을 다시 확인하는 용도다.
    # dt.strftime(...) 는 datetime 열을 사람이 읽는 문자열로 바꾸는 pandas 날짜 처리 문법이다.
    display_frame["발표시간"] = display_frame["발표시간"].dt.strftime("%Y-%m-%d %H:%M")
    st.dataframe(display_frame, use_container_width=True, hide_index=True)
