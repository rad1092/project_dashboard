"""학습 로그와 운영 규칙 페이지.

이 페이지는 ``dashboard.content`` 에 모아 둔 학습 주제와 로드맵을 탭으로 나누어 보여준다.
한 탭에는 무엇을 배우는지, 다른 탭에는 어떤 순서로 확장할지,
마지막 탭에는 작업 시 지켜야 할 기본 규칙을 정리한다.
"""

from __future__ import annotations

import streamlit as st

from dashboard.components.layout import render_page_intro
from dashboard.config import apply_page_config
from dashboard.content import LEARNING_TOPICS, ROADMAP_STEPS


apply_page_config("learning")

render_page_intro(
    "Learning Log",
    "현재 저장소를 통해 무엇을 배우고, 앞으로 어떤 순서로 확장할지 정리한 페이지입니다.",
    "이 페이지의 내용은 현재 코드와 docs 구조를 기준으로 계속 갱신합니다.",
)

# 학습 내용, 확장 로드맵, 운영 규칙을 서로 다른 탭으로 나눠 읽기 흐름을 정리한다.
topic_tab, roadmap_tab, rules_tab = st.tabs(["학습 주제", "로드맵", "운영 규칙"])

with topic_tab:
    # LEARNING_TOPICS 는 content.py 에서 관리하고,
    # 이 페이지는 그 내용을 카드처럼 보여주는 역할만 맡는다.
    for topic in LEARNING_TOPICS:
        with st.container(border=True):
            st.subheader(f"{topic['phase']}. {topic['title']}")
            st.write(topic["summary"])
            st.markdown(f"**왜 중요한가**: {topic['why_it_matters']}")
            st.markdown(f"**다음 연습**: {topic['next_practice']}")

with roadmap_tab:
    # ROADMAP_STEPS 는 앞으로 이 저장소를 어떤 순서로 실제화할지 보여주는 계획표다.
    for step in ROADMAP_STEPS:
        with st.container(border=True):
            st.subheader(f"{step['stage']} - {step['goal']}")
            st.write(step["plan"])
            st.markdown(f"**완료 기준**: {step['done_definition']}")

with rules_tab:
    with st.container(border=True):
        st.subheader("반드시 지킬 점")
        # 이 규칙들은 코드 작성, 데이터 연결, 문서 갱신 시 자주 놓치는 부분을 요약한다.
        st.markdown("- 절대경로와 로컬 전용 파일명에 의존하지 않는다.")
        st.markdown("- 비밀정보는 `.streamlit/secrets.toml`에만 두고 Git에는 올리지 않는다.")
        st.markdown("- 페이지 파일이 데이터 가공 로직까지 전부 떠안지 않게 분리한다.")
        st.markdown("- 문서와 코드가 서로 다른 설명을 하지 않게 함께 수정한다.")