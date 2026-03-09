"""현재 재난 앱 구현 작업을 기록하는 프로젝트 페이지.

이 페이지는 저장소 안에서 진행 중인 기능을
상태, 역할, 핵심 포인트, 다음 액션 기준으로 기록하는 작업 보드 역할을 한다.

초보자 메모:
- 이 페이지는 기능 실행 화면이 아니라 "현재 저장소가 어디까지 왔는지"를 설명하는 메모 보드에 가깝다.
- 그래서 content.py 의 PROJECT_ITEMS 데이터를 순회해 카드처럼 뿌리는 구조로 되어 있다.
"""

from __future__ import annotations

import streamlit as st

from dashboard.components.layout import render_page_intro
from dashboard.config import apply_page_config
from dashboard.content import PROJECT_ITEMS
from dashboard.utils.formatters import label_status


apply_page_config("projects")

render_page_intro(
    "5 Projects",
    "현재 저장소 안에서 진행 중인 재난 대피소 추천 기능과 설명 구조 작업을 카드 형태로 정리한 페이지입니다.",
    "실제 구현 작업이 늘어날수록 이 목록을 계속 갱신해 프로젝트 맥락을 남깁니다.",
)

# PROJECT_ITEMS 는 content.py 의 고정 키 계약을 따르므로,
# 이 페이지는 데이터를 가공하기보다 어떤 순서와 강조로 보여 줄지에 집중한다.
for item in PROJECT_ITEMS:
    # PROJECT_ITEMS 는 dict 목록이라 for 문을 돌 때마다 카드 하나에 들어갈 데이터 묶음이 item 으로 들어온다.
    with st.container(border=True):
        # 카드 하나가 "무엇을 하는 기능인지"와 "다음에 무엇을 할지"를 같이 보여 준다.
        # 오른쪽 상태 칸은 짧은 상태 라벨만 담으므로 폭을 0.25 로 더 좁게 둔다.
        top_left, top_right = st.columns([0.75, 0.25])
        with top_left:
            st.subheader(item["title"])
            st.write(item["summary"])
        with top_right:
            # 상태 코드 그대로보다 사람이 읽는 라벨이 중요하므로 formatters 를 거쳐 표시한다.
            # 예를 들어 active 같은 내부 코드값을 "운영 중" 같은 사용자 친화 라벨로 바꿔 보여 준다.
            st.metric("상태", label_status(item["status"]))

        detail_left, detail_right = st.columns([0.55, 0.45], gap="large")
        with detail_left:
            st.markdown(f"**역할**: {item['role']}")
            st.markdown("**핵심 포인트**")
            # 하이라이트 목록은 구현 세부가 아니라 이 작업이 왜 중요한지를 짧게 설명하는 용도다.
            for highlight in item["highlights"]:
                st.markdown(f"- {highlight}")
        with detail_right:
            st.markdown("**다음 액션**")
            st.write(item["next_action"])

st.divider()

with st.container(border=True):
    st.subheader("프로젝트 기록 기준")
    # 아래 기준은 카드 내용이 단순 작업 목록으로 흐려지지 않게 붙여 둔 운영 규칙이다.
    st.markdown("- 화면만 예쁜 항목이 아니라 데이터, 규칙, 다음 액션이 보이는 작업만 남긴다.")
    st.markdown("- 현재 동작과 미래 확장 구간을 같은 카드 안에서 섞지 않는다.")
    st.markdown("- 문서와 테스트까지 같이 갱신된 작업을 중심으로 기록한다.")
