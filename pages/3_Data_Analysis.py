"""샘플 데이터 분석 페이지.

이 페이지는 이 저장소의 핵심 학습 예시다.
``load_demo_dataset()`` 으로 데이터를 준비하고,
사이드바 필터를 적용한 뒤,
``build_kpis()`` 와 ``dashboard.components.charts`` 의 차트 함수를 이용해
KPI 카드, 차트, 상세 표를 한 화면에 조합한다.

중요한 구조 원칙:
- 페이지는 화면 조합만 담당한다.
- 데이터 생성과 KPI 계산은 services 모듈에 둔다.
- 차트 생성은 components/charts.py 에 둔다.
- 표시 형식은 utils/formatters.py 에 둔다.
"""

from __future__ import annotations

import streamlit as st

from dashboard.components.charts import (
    build_category_impact_chart,
    build_status_share_chart,
    build_trend_chart,
)
from dashboard.components.layout import render_page_intro
from dashboard.config import apply_page_config
from dashboard.services.analysis_data import build_kpis, load_demo_dataset
from dashboard.utils.formatters import (
    format_decimal,
    format_number,
    format_percent,
    format_period,
    label_status,
)


apply_page_config("analysis")

render_page_intro(
    "Data Analysis",
    "샘플 데이터를 기반으로 필터, KPI, 차트를 동시에 구성한 분석 페이지입니다.",
    "이 페이지는 나중에 실제 CSV, API, DB 데이터로 교체할 때도 같은 구조를 유지하도록 설계했습니다.",
)

# 1) 원본 데이터 준비
# 현재는 데모 데이터를 불러오지만, 나중에 같은 위치를 CSV/API/DB 기반 함수로 교체할 수 있다.
# 중요한 점은 페이지가 데이터 소스의 세부 구현을 몰라도 되게 만드는 것이다.
dataframe = load_demo_dataset()

# 2) 사이드바 필터에 필요한 선택지 준비
# 원본 데이터에서 가능한 프로젝트/카테고리/상태 목록을 먼저 뽑아 위젯 옵션으로 사용한다.
st.sidebar.header("필터")

projects = sorted(dataframe["project"].unique().tolist())
categories = sorted(dataframe["category"].unique().tolist())
statuses = sorted(dataframe["status"].unique().tolist())

# 사용자가 어떤 범위를 보고 싶은지 고를 수 있도록 멀티셀렉트 위젯을 둔다.
selected_projects = st.sidebar.multiselect("프로젝트", options=projects, default=projects)
selected_categories = st.sidebar.multiselect("카테고리", options=categories, default=categories)
selected_statuses = st.sidebar.multiselect("상태", options=statuses, default=statuses)

# 기간 필터는 날짜 범위 슬라이더로 받아 추이 차트와 표를 함께 좁힌다.
min_period = dataframe["period"].min().date()
max_period = dataframe["period"].max().date()
selected_period = st.sidebar.slider(
    "기간",
    min_value=min_period,
    max_value=max_period,
    value=(min_period, max_period),
)

# 3) 선택된 필터를 원본 데이터프레임에 적용
# 이 단계에서 만들어진 filtered 가 이후 KPI, 차트, 표의 공통 입력값이 된다.
filtered = dataframe[
    dataframe["project"].isin(selected_projects)
    & dataframe["category"].isin(selected_categories)
    & dataframe["status"].isin(selected_statuses)
    & dataframe["period"].dt.date.between(selected_period[0], selected_period[1])
].copy()

if filtered.empty:
    # 필터 결과가 비어도 앱이 에러를 내지 않고 사용자가 조건을 조정하도록 안내한다.
    st.warning("현재 필터 조건에 맞는 데이터가 없습니다. 필터를 조금 넓혀보세요.")
else:
    # 4) 필터 결과를 기준으로 KPI 계산
    # 평균과 개수 계산은 services 모듈의 build_kpis 에 맡겨 계산 규칙을 한곳에 둔다.
    kpis = build_kpis(filtered)

    # KPI 카드는 사람이 빠르게 읽을 수 있도록 formatters.py 로 표시 형식을 통일한다.
    metric_columns = st.columns(4)
    metric_columns[0].metric("기록 수", format_number(kpis["record_count"]))
    metric_columns[1].metric("프로젝트 수", format_number(kpis["project_count"]))
    metric_columns[2].metric("평균 전환율", format_percent(kpis["avg_conversion_rate"]))
    metric_columns[3].metric("평균 임팩트", format_decimal(kpis["avg_impact_score"]))

    # 5) 차트 렌더링
    # 집계와 Plotly 설정은 charts.py 함수에 맡겨 페이지 코드가 너무 비대해지지 않게 한다.
    chart_left, chart_right = st.columns(2, gap="large")
    with chart_left:
        st.plotly_chart(build_trend_chart(filtered), use_container_width=True)
        st.plotly_chart(build_category_impact_chart(filtered), use_container_width=True)
    with chart_right:
        st.plotly_chart(build_status_share_chart(filtered), use_container_width=True)
        with st.container(border=True):
            st.subheader("필터 요약")
            st.markdown(f"- 기간: {format_period(kpis['latest_period'])} 기준까지 반영")
            st.markdown(
                "- 상태: "
                + ", ".join(label_status(status) for status in selected_statuses)
            )
            st.markdown("- 샘플 데이터는 매 실행마다 같은 결과가 나오도록 고정 시드로 생성")

    # 6) 상세 표 표시용 데이터 정리
    # 원본 filtered 는 계산용으로 두고, 화면용 데이터프레임은 별도 복사본에서 포맷을 바꾼다.
    st.subheader("상세 데이터")
    display_frame = filtered.copy()

    # 날짜, 상태, 비율, 점수는 사용자가 읽기 쉬운 문자열로 변환해 표에 넣는다.
    display_frame["period"] = display_frame["period"].dt.strftime("%Y-%m-%d")
    display_frame["status"] = display_frame["status"].map(label_status)
    display_frame["conversion_rate"] = display_frame["conversion_rate"].map(format_percent)
    display_frame["impact_score"] = display_frame["impact_score"].map(
        lambda value: format_decimal(value)
    )
    display_frame["satisfaction_score"] = display_frame["satisfaction_score"].map(
        lambda value: format_decimal(value)
    )

    st.dataframe(display_frame, use_container_width=True, hide_index=True)