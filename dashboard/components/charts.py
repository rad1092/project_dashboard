"""분석 페이지에서 사용하는 Plotly 차트 생성기 모음.

이 모듈은 분석 페이지가 데이터 집계와 시각화 코드를 한 파일에 섞지 않도록
차트 생성 책임만 따로 분리해 둔 곳이다.
차트 함수는 모두 DataFrame 을 받아 Figure 를 반환하므로,
페이지는 어떤 그래프를 어디에 놓을지만 결정하면 된다.

초보자 메모:
- 각 함수는 "데이터프레임을 받아 Figure 를 돌려준다"는 같은 패턴을 따른다.
- 그래서 분석 페이지는 집계 방식보다 레이아웃 배치에 더 집중할 수 있다.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

COLOR_SEQUENCE = ["#0f766e", "#1d4ed8", "#f59e0b", "#dc2626", "#0f172a"]
# 분석 차트 전반이 같은 색 팔레트를 공유해야 한 화면에서 재난/지역 비교가 덜 흔들린다.


def _build_empty_figure(message: str) -> go.Figure:
    """비어 있는 데이터셋에도 깨지지 않는 안내용 Figure 를 만든다.

    필터 결과가 0건일 때도 페이지 레이아웃을 유지하면서 이유를 직접 설명해 주기 위한 보조 함수다.
    """

    # 빈 Figure 를 별도 함수로 빼 두면 차트별로 "빈 데이터 안내" 스타일을 반복해서 맞출 수 있다.
    figure = go.Figure()
    # annotation 은 그래프 안에 띄우는 설명 문구라, 빈 데이터일 때 "왜 비었는지"를 직접 보여 주기 좋다.
    figure.add_annotation(text=message, showarrow=False, font=dict(size=16))
    figure.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(t=40, b=20, l=20, r=20),
    )
    return figure


def build_alert_trend_chart(dataframe: pd.DataFrame) -> go.Figure:
    """일자별 재난 그룹 건수를 선 차트로 만든다."""

    if dataframe.empty:
        return _build_empty_figure("선택한 조건에 맞는 특보 데이터가 없다.")

    # 선 차트는 시계열 흐름을 읽는 용도라서 날짜별 집계를 먼저 만들고 그 결과만 시각화한다.
    summary = (
        dataframe.assign(발표일=dataframe["발표시간"].dt.strftime("%Y-%m-%d"))
        .groupby(["발표일", "재난그룹"], as_index=False)
        .size()
        .rename(columns={"size": "건수"})
    )
    # assign() 은 원본 dataframe 을 직접 바꾸지 않고, 차트 계산용 임시 열을 붙이는 pandas 패턴이다.
    # 발표시간 전체 대신 발표일 문자열로 묶는 이유는
    # 홈/분석 단계에서는 세부 시각보다 날짜 단위 흐름이 더 읽기 쉽기 때문이다.

    # markers=True 를 주는 이유는 꺾은선만 있을 때보다 날짜별 변화 지점을 더 또렷하게 보이게 하기 위해서다.
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
    """권역별 특보 건수를 막대 차트로 만든다."""

    if dataframe.empty:
        return _build_empty_figure("선택한 조건에 맞는 권역 데이터가 없다.")

    # 권역 막대 차트는 어느 지역에 특보가 많이 쌓였는지 비교하는 용도다.
    summary = (
        dataframe.groupby("지역", as_index=False)
        .size()
        .rename(columns={"size": "건수"})
        .sort_values("건수", ascending=False)
    )
    # sort_values() 를 먼저 해 두면 Plotly 가 막대를 그릴 때도 많은 지역부터 차례로 읽기 쉬워진다.
    # 건수 내림차순 정렬을 먼저 하는 이유는 막대 차트가 많은 지역부터 읽히는 편이 비교가 빠르기 때문이다.

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
    """재난 종류별 비중을 도넛 차트로 만든다."""

    if dataframe.empty:
        return _build_empty_figure("선택한 조건에 맞는 재난 종류 데이터가 없다.")

    # 도넛 차트는 재난 종류의 비중을 빠르게 읽는 데 적합해 전체 분포 설명용으로 사용한다.
    summary = (
        dataframe.groupby("재난종류", as_index=False)
        .size()
        .rename(columns={"size": "건수"})
        .sort_values("건수", ascending=False)
    )
    # groupby().size() 는 같은 값끼리 묶은 뒤 "몇 건인지" 세는 가장 기본적인 집계 패턴이다.
    # 재난그룹이 아니라 재난종류를 그대로 쓰는 이유는
    # 도넛 차트가 원본 특보 비중을 보여 주는 보조 설명 역할이기 때문이다.

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
    """대피소 유형 분포를 막대 차트로 만든다."""

    if dataframe.empty:
        return _build_empty_figure("선택한 조건에 맞는 대피소 데이터가 없다.")

    # 대피소 유형 분포는 추천 근거 데이터의 구성을 보여 주는 보조 정보라서
    # 결측 유형도 "미분류"로 통일해 누락 없이 집계한다.
    summary = (
        dataframe.assign(대피소유형=dataframe["대피소유형"].fillna("미분류"))
        .groupby("대피소유형", as_index=False)
        .size()
        .rename(columns={"size": "건수"})
        .sort_values("건수", ascending=False)
    )
    # fillna("미분류") 는 비어 있는 값을 사람이 읽을 수 있는 라벨로 바꾼 뒤 집계하겠다는 뜻이다.
    # fillna("미분류") 를 미리 하는 이유는 집계 전에 결측을 정리해 두어
    # Plotly 범례와 막대 축에서 빈 문자열/NaN 이 따로 보이는 일을 막기 위해서다.

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
