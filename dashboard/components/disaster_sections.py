"""재난 추천 앱 전용 섹션 UI를 모아 둔 모듈.

이 파일은 추천 카드, 데이터셋 카드, 플로우 단계 카드처럼
재난 앱에서 반복적으로 쓰는 설명형 UI 블록을 한곳에 모아 둔다.
페이지 파일은 여기서 만든 작은 렌더러를 호출해
"무엇을 보여줄지"와 "어떻게 그릴지"를 분리한다.

초보자 메모:
- 페이지는 이 함수들을 불러 "데이터를 넘기기만" 하고,
  카드 배치나 텍스트 꾸밈 같은 표현 방식은 여기서 맡는다.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.utils.formatters import format_distance_km, format_number


def render_recommendation_cards(recommendations: pd.DataFrame) -> None:
    """추천 결과를 카드 3장 형태로 보여준다.

    표보다 먼저 카드 요약을 보여 주는 이유는,
    사용자가 상위 후보의 이름/거리/유형을 한눈에 비교하게 만들기 위해서다.
    """

    if recommendations.empty:
        st.info("현재 조건으로 보여줄 추천 대피소가 없다.")
        return

    # 추천 함수가 Top 3 계약을 보장하므로, 여기서는 들어온 행 수만큼만 카드 칸을 만든다.
    # len(recommendations) 가 2면 2칸, 3이면 3칸만 만들기 때문에 빈 카드가 남지 않는다.
    columns = st.columns(min(len(recommendations), 3))
    for index, (_, row) in enumerate(recommendations.iterrows()):
        # enumerate(...) 는 반복 순번과 실제 값을 함께 돌려줘 index 는 0, 1, 2 처럼 카드 위치 번호로 쓰인다.
        # iterrows() 는 DataFrame 의 각 행을 하나씩 꺼내는 pandas 반복 방식이다.
        # 앞의 `_` 는 첫 번째 반환값인 원래 행 인덱스를 이번 코드에서는 쓰지 않겠다는 표시다.
        with columns[index]:
            # with columns[index]: 아래에 적는 위젯들은 현재 번호의 열 칸 안에 배치된다.
            with st.container(border=True):
                # 카드 한 장은 사용자가 표를 펼치기 전에도 핵심 판단 요소를 한눈에 보게 만드는 요약 단위다.
                st.subheader(f"Top {index + 1}. {row['대피소명']}")
                st.markdown(f"**구분**: {row['추천구분']}")
                st.markdown(f"**직선 거리**: {format_distance_km(row['거리_km'])}")
                st.markdown(f"**대피소 유형**: {row['대피소유형']}")
                st.markdown(f"**수용인원**: {format_number(row['수용인원_정렬값'])}명")
                st.markdown(f"**주소**: {row['주소']}")
                st.caption(row["추천사유"])


def render_dataset_cards(catalog: list[dict[str, object]]) -> None:
    """설명 페이지에서 데이터셋 역할을 카드형으로 보여준다.

    데이터셋 이름만 보여 주면 사용자가 각 CSV 의 책임을 이해하기 어려워서,
    설명/행 수/컬럼/원본 경로를 같이 묶어 표시한다.
    """

    for item in catalog:
        with st.container(border=True):
            # 데이터셋 카드는 "이 CSV 가 무슨 역할을 하는지"를 설명하는 용도라
            # 컬럼명과 원본 경로까지 함께 보여 준다.
            # item 은 build_dataset_catalog() 가 만든 dict 이므로 name/description/rows 같은 키를 그대로 읽는다.
            st.subheader(str(item["name"]))
            st.write(str(item["description"]))
            st.markdown(f"**행 수**: {format_number(int(item['rows']))}건")
            st.markdown(f"**컬럼**: {item['columns']}")
            st.caption(f"원본 경로: {item['source_path']}")


def render_flow_steps(steps: list[dict[str, str]]) -> None:
    """추천 플로우 설명용 단계를 순서대로 렌더링한다.

    청사진 이미지를 그대로 붙이는 대신,
    단계 데이터를 카드로 풀어 사용자가 현재 구현과 미래 확장을 함께 읽게 만든다.
    """

    for item in steps:
        with st.container(border=True):
            # 단계 카드는 현재 구현과 미래 변경 지점을 같은 형식으로 비교하게 만들기 위한 반복 UI 다.
            # columns([0.8, 0.2]) 는 왼쪽 제목 칸을 더 넓게, 오른쪽 상태 칸을 더 좁게 주는 비율 설정이다.
            head_left, head_right = st.columns([0.8, 0.2])
            with head_left:
                st.subheader(f"{item['step']}. {item['title']}")
            with head_right:
                st.markdown(f"**{item['status']}**")
            st.write(item["summary"])
            st.markdown(f"**현재 구현**: {item['now_note']}")
            st.markdown(f"**나중에 바꿀 지점**: {item['future_note']}")
