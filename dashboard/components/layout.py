"""반복되는 Streamlit 레이아웃 패턴을 모아 둔 UI 헬퍼 모듈.

페이지 파일에서 제목 블록, 칩 목록, 테두리 카드 목록을 반복 작성하면
코드가 길어지고 페이지마다 표현이 조금씩 달라지기 쉽다.
이 파일은 그런 반복 UI를 함수로 묶어 각 페이지가 내용 조합에 집중하게 한다.

주요 호출 위치:
- ``pages/1_About.py``
- ``pages/2_Projects.py``
- ``pages/4_Learning_Log.py``
"""

from __future__ import annotations

import streamlit as st


def render_page_intro(title: str, subtitle: str, caption: str | None = None) -> None:
    """페이지 상단의 공통 제목 블록을 그린다.

    Args:
        title: 페이지 제목.
        subtitle: 제목 바로 아래에 들어갈 설명 문장.
        caption: 필요할 때만 추가하는 보조 설명.
    """
    st.title(title)
    st.write(subtitle)
    if caption:
        st.caption(caption)


def render_chip_list(items: list[str]) -> None:
    """기술 스택 같은 짧은 항목 목록을 칩 형태의 마크다운으로 출력한다.

    About 페이지에서 기술 스택을 가볍게 보여줄 때 사용한다.
    """
    chips = " ".join(f"`{item}`" for item in items)
    st.markdown(chips)


def render_bordered_points(title: str, items: list[str]) -> None:
    """제목과 글머리표 목록이 들어간 테두리 컨테이너를 렌더링한다.

    같은 카드 구조를 여러 페이지에서 재사용할 수 있게 묶어 둔 함수다.
    """
    with st.container(border=True):
        st.subheader(title)
        for item in items:
            st.markdown(f"- {item}")