"""학습 로그와 확장 로드맵 페이지.

이 페이지는 기능 자체보다,
현재 구조를 통해 무엇을 배우고 어떤 순서로 확장할지를 기록하는 프로젝트 메모 역할을 한다.
코드, 문서, 다음 작업 기준을 함께 유지하기 위한 보조 화면이다.

초보자 메모:
- 이 페이지는 "앱이 지금 무엇을 하느냐"보다 "이 구조를 통해 무엇을 배우고 다음에 무엇을 할까"를 정리한다.
- 탭을 나눈 이유도 학습 메모, 로드맵, 운영 규칙을 서로 섞지 않기 위해서다.
"""

from __future__ import annotations

import streamlit as st

from dashboard.components.layout import render_page_intro
from dashboard.config import apply_page_config
from dashboard.content import LEARNING_TOPICS, ROADMAP_STEPS


apply_page_config("learning")

render_page_intro(
    "7 Learning Log",
    "현재 저장소를 통해 무엇을 배우고, 어떤 순서로 재난 앱을 확장할지 정리한 페이지입니다.",
    "코드와 문서를 같이 유지하기 위한 학습 포인트와 로드맵을 함께 기록합니다.",
)

# 서로 다른 성격의 정보가 한 화면에서 섞이지 않도록 학습/로드맵/운영 규칙 탭으로 나눈다.
topic_tab, roadmap_tab, rules_tab = st.tabs(["학습 주제", "로드맵", "운영 규칙"])
# st.tabs() 는 한 페이지 안에서 내용을 주제별로 전환해 볼 수 있게 만드는 Streamlit 레이아웃 위젯이다.

with topic_tab:
    # with topic_tab: 아래에 적는 위젯들은 첫 번째 탭이 선택됐을 때 보이는 영역 안에 들어간다.
    # 학습 주제 탭은 "무엇을 배웠는가"를 남기는 영역이라,
    # 구현 상세보다 주제별 의미와 다음 연습으로 읽히게 구성한다.
    for topic in LEARNING_TOPICS:
        with st.container(border=True):
            # phase 를 제목 앞에 붙이는 이유는 학습 항목도 로드맵처럼 순서를 가진 흐름으로 읽히게 하기 위해서다.
            st.subheader(f"{topic['phase']}. {topic['title']}")
            st.write(topic["summary"])
            st.markdown(f"**왜 중요한가**: {topic['why_it_matters']}")
            st.markdown(f"**다음 연습**: {topic['next_practice']}")

with roadmap_tab:
    # 두 번째 탭에서는 roadmap 단계만 렌더링해 학습 메모와 실제 작업 순서를 화면에서 분리한다.
    # 로드맵 탭은 학습 메모와 다르게 실제 작업 순서를 보여 주는 곳이라
    # 목표와 완료 기준을 함께 적어 다음 액션 판단에 바로 쓰게 만든다.
    for step in ROADMAP_STEPS:
        with st.container(border=True):
            st.subheader(f"{step['stage']} - {step['goal']}")
            st.write(step["plan"])
            st.markdown(f"**완료 기준**: {step['done_definition']}")

with rules_tab:
    with st.container(border=True):
        st.subheader("반드시 지킬 점")
        # 운영 규칙은 기능 설명보다 짧고 강하게 보여 주는 편이 좋아
        # 별도 탭에서 프로젝트의 금지사항과 유지 원칙만 모아 둔다.
        st.markdown("- 외부 전처리 CSV는 앱에서 수정하지 않고 읽기 전용으로만 사용한다.")
        st.markdown("- 유료 API와 유료 지도 API는 현재 단계 코드에 넣지 않는다.")
        st.markdown("- 페이지 파일이 추천 규칙과 CSV 로딩을 직접 떠안지 않도록 서비스 계층으로 분리한다.")
        st.markdown("- 새 기능을 넣을 때는 docs와 테스트를 함께 갱신한다.")
