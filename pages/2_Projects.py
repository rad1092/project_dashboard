"""프로젝트 기록 페이지.

이 페이지는 ``dashboard.content.PROJECT_ITEMS`` 에 모아 둔 프로젝트 메모를
카드 형태로 반복 출력한다. 프로젝트 텍스트 자체는 content.py 에 두고,
상태 라벨 변환은 formatters.py 에 맡겨서 페이지는 화면 조합만 담당한다.
"""

from __future__ import annotations

import streamlit as st

from dashboard.components.layout import render_page_intro
from dashboard.config import apply_page_config
from dashboard.content import PROJECT_ITEMS
from dashboard.utils.formatters import label_status


apply_page_config("projects")

render_page_intro(
    "Projects",
    "이 페이지는 현재 저장소 안에서 정리하고 있는 작업을 카드 형태로 기록하는 공간입니다.",
    "대표 프로젝트가 늘어나면 이 목록을 실제 사례 중심으로 계속 갱신하면 됩니다.",
)

# PROJECT_ITEMS 의 각 딕셔너리를 한 장의 카드처럼 보여준다.
for item in PROJECT_ITEMS:
    with st.container(border=True):
        top_left, top_right = st.columns([0.75, 0.25])
        with top_left:
            st.subheader(item["title"])
            st.write(item["summary"])
        with top_right:
            # 상태 코드는 내부 값 그대로 두고, 화면에서만 한국어 라벨로 변환한다.
            st.metric("상태", label_status(item["status"]))

        detail_left, detail_right = st.columns([0.55, 0.45], gap="large")
        with detail_left:
            st.markdown(f"**역할**: {item['role']}")
            st.markdown("**핵심 포인트**")
            for highlight in item["highlights"]:
                st.markdown(f"- {highlight}")
        with detail_right:
            st.markdown("**다음 액션**")
            st.write(item["next_action"])

st.divider()

# 하단 기준 블록은 어떤 항목을 공개용 프로젝트 기록으로 남길지 설명한다.
with st.container(border=True):
    st.subheader("프로젝트를 추가할 때의 기준")
    st.markdown("- 화면만 있는 아이디어가 아니라, 문제 정의와 작업 맥락이 있는 항목만 남긴다.")
    st.markdown("- 데이터 출처, 분석 목적, 역할, 배운 점이 설명되지 않으면 공개용 기록으로 올리지 않는다.")
    st.markdown("- 실험 단계의 코드는 바로 넣지 말고, 문서 기준에 맞게 다시 정리한다.")