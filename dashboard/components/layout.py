"""반복되는 Streamlit 레이아웃 패턴을 모아 둔 UI 헬퍼 모듈.

왜 필요한가:
- 페이지마다 제목, 칩, 테두리 박스 코드를 반복하면 화면 톤은 비슷한데 수정 지점이 흩어진다.
- 이 모듈은 자주 쓰는 레이아웃 패턴을 작게 감싸 페이지 코드가 내용 흐름에 집중하게 만든다.

누가 사용하는가:
- ``pages/*.py`` 전반이 공통 소개 블록과 테두리 섹션을 이 모듈로 렌더링한다.

초보자 메모:
- 이 파일은 "새로운 데이터"를 만들지 않는다.
- 대신 여러 페이지가 비슷한 모양의 UI 를 반복해서 적지 않도록 화면 그리는 함수를 작게 나눠 둔다.
"""

from __future__ import annotations

import streamlit as st


def render_page_intro(title: str, subtitle: str, caption: str | None = None) -> None:
    """페이지 상단의 공통 제목 블록을 그린다.

    제목/부제/캡션 순서를 고정해 두면 페이지를 넘겨도 사용자가 같은 읽기 흐름을 느낄 수 있다.
    """

    # 모든 페이지의 첫 인상을 같은 구조로 맞춰 두면,
    # 사용자는 페이지마다 읽는 방법을 다시 학습하지 않아도 된다.
    # title, subtitle, caption 을 함수 인자로 받는 이유는 모양은 같게 두고 내용만 페이지마다 바꾸기 위해서다.
    st.title(title)
    st.write(subtitle)
    if caption:
        # caption 은 선택값(None 가능)이라 값이 있을 때만 추가로 그린다.
        st.caption(caption)


def render_chip_list(items: list[str]) -> None:
    """기술 스택 같은 짧은 항목 목록을 칩 형태로 출력한다.

    긴 설명보다 간단한 키워드 나열이 적합한 영역을 위해 별도 함수로 분리한다.
    """

    # 이 함수는 별도 박스를 만들지 않고 한 줄에 묶어,
    # 스택/태그 같은 짧은 정보가 화면 설명을 밀어내지 않게 한다.
    # join() 은 리스트의 여러 항목을 하나의 문자열로 합칠 때 자주 쓰는 Python 패턴이다.
    chips = " ".join(f"`{item}`" for item in items)
    st.markdown(chips)


def render_bordered_points(title: str, items: list[str]) -> None:
    """제목과 글머리표 목록이 들어간 테두리 컨테이너를 렌더링한다.

    여러 페이지가 같은 정보 밀도를 유지하도록 "제목 + 불릿 목록" 패턴을 재사용한다.
    """

    with st.container(border=True):
        st.subheader(title)
        # 동일한 시각 구조를 유지하면 About, 설명, 학습 로그 페이지가 달라도
        # "요약 정보 블록"이라는 역할을 공통적으로 인식할 수 있다.
        # 여기서는 리스트 항목을 하나씩 꺼내며 같은 마크다운 패턴으로 반복 출력한다.
        for item in items:
            st.markdown(f"- {item}")
