"""분석 페이지에서 사용하는 Plotly 차트 생성기 모음.

이 파일은 ``pages/3_Data_Analysis.py`` 가 직접 집계 코드와 Plotly 설정을
모두 들고 있지 않도록 차트 생성을 별도 모듈로 분리한 곳이다.
차트를 추가하거나 스타일을 바꿀 때는 먼저 이 파일을 확인하면 된다.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 색상 시퀀스를 한 곳에 두면 막대/선/원형 차트가 같은 시각 언어를 공유한다.
COLOR_SEQUENCE = ["#0f766e", "#1d4ed8", "#f59e0b", "#dc2626", "#7c3aed"]


def build_category_impact_chart(dataframe: pd.DataFrame) -> go.Figure:
    """카테고리별 평균 임팩트 점수를 막대 차트로 만든다.

    Args:
        dataframe: 필터가 적용된 분석 데이터.

    Returns:
        Plotly Figure 객체.

    이 함수는 pages/3_Data_Analysis.py 에서 직접 호출된다.
    """
    # 차트를 그리기 전에 카테고리 단위 평균 임팩트를 계산해
    # 시각화 코드와 집계 의도를 함께 읽을 수 있게 한다.
    summary = (
        dataframe.groupby("category", as_index=False)["impact_score"]
        .mean()
        .sort_values("impact_score", ascending=False)
    )
    figure = px.bar(
        summary,
        x="category",
        y="impact_score",
        color="category",
        text_auto=".1f",
        color_discrete_sequence=COLOR_SEQUENCE,
    )
    figure.update_layout(
        title="카테고리별 평균 임팩트 점수",
        showlegend=False,
        margin=dict(t=60, b=20, l=20, r=20),
    )
    figure.update_yaxes(title="Impact Score")
    figure.update_xaxes(title="")
    return figure


def build_status_share_chart(dataframe: pd.DataFrame) -> go.Figure:
    """상태별 데이터 비중을 도넛 차트로 만든다.

    상태 분포는 counts 기반이므로 평균 계산이 아니라 ``size()`` 집계를 사용한다.
    """
    # 상태별 건수를 먼저 계산해 두면 비중 산식이 명확하게 보인다.
    summary = dataframe.groupby("status", as_index=False).size()
    figure = px.pie(
        summary,
        names="status",
        values="size",
        hole=0.6,
        color="status",
        color_discrete_sequence=COLOR_SEQUENCE,
    )
    figure.update_layout(
        title="상태 분포",
        margin=dict(t=60, b=20, l=20, r=20),
        legend_title_text="상태",
    )
    return figure


def build_trend_chart(dataframe: pd.DataFrame) -> go.Figure:
    """기간별 프로젝트 임팩트 추이를 선 차트로 만든다.

    한 기간에 여러 행이 생길 수 있는 미래 데이터 소스도 고려해
    ``period`` 와 ``project`` 기준 평균 집계를 먼저 수행한다.
    """
    # 추이 차트는 기간축 정렬이 중요하므로 집계 뒤 period 순으로 정렬한다.
    summary = (
        dataframe.groupby(["period", "project"], as_index=False)["impact_score"]
        .mean()
        .sort_values("period")
    )
    figure = px.line(
        summary,
        x="period",
        y="impact_score",
        color="project",
        markers=True,
        color_discrete_sequence=COLOR_SEQUENCE,
    )
    figure.update_layout(
        title="기간별 프로젝트 임팩트 추이",
        margin=dict(t=60, b=20, l=20, r=20),
        legend_title_text="프로젝트",
    )
    figure.update_yaxes(title="Impact Score")
    figure.update_xaxes(title="")
    return figure