"""저장소 소개 페이지.

이 페이지는 ``dashboard.content.PROFILE_DATA`` 에 모아 둔 소개 문구를 읽어
저장소 운영 기준, 기술 스택, 다음 단계 계획을 화면으로 보여준다.
페이지 자체는 화면 조합만 담당하고, 실제 텍스트 원본은 content.py 에 둔다.
"""

from __future__ import annotations

import streamlit as st

from dashboard.components.layout import (
    render_bordered_points,
    render_chip_list,
    render_page_intro,
)
from dashboard.config import apply_page_config
from dashboard.content import PROFILE_DATA


# 페이지 키는 config.py 의 PAGE_META 와 연결된다.
apply_page_config("about")

# 상단 소개 블록은 공통 레이아웃 헬퍼를 사용해 다른 페이지와 톤을 맞춘다.
render_page_intro(
    "About",
    "이 페이지는 이 저장소를 어떤 기준으로 운영하고, 포트폴리오에 어떻게 연결할지를 설명합니다.",
)

# 왼쪽은 자기소개와 운영 원칙, 오른쪽은 기술 스택과 다음 단계로 나눈다.
left, right = st.columns([1.1, 0.9], gap="large")

with left:
    with st.container(border=True):
        # PROFILE_DATA 의 name/headline/intro 는 About 페이지의 핵심 소개 영역이다.
        st.subheader(PROFILE_DATA["name"])
        st.write(PROFILE_DATA["headline"])
        st.write(PROFILE_DATA["intro"])

    render_bordered_points("집중하고 있는 방향", PROFILE_DATA["focus_areas"])
    render_bordered_points("작업 원칙", PROFILE_DATA["principles"])

with right:
    with st.container(border=True):
        st.subheader("기술 스택")
        render_chip_list(PROFILE_DATA["tech_stack"])

    render_bordered_points("다음 단계", PROFILE_DATA["next_steps"])

    with st.container(border=True):
        st.subheader("저장소 사용 방식")
        st.markdown("- Home: 저장소 목적과 문서 읽는 순서를 먼저 이해한다.")
        st.markdown("- Projects: 어떤 작업을 어떻게 기록할지 정리한다.")
        st.markdown("- Data Analysis: 데이터 흐름과 화면 구조 예시를 확인한다.")
        st.markdown("- Learning Log: 현재 저장소를 통해 배우는 주제를 정리한다.")