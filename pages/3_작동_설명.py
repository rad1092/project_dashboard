"""대피소 추천이 어떤 흐름으로 작동하는지 설명하는 페이지.

청사진 이미지를 그대로 붙이지 않고, 실제 코드 흐름을 카드와 코드 조각으로 다시 풀어낸다.
현재 구현 구간과 미래 교체 구간을 나눠 보여 주는 것이 이 페이지의 핵심이다.
"""

from __future__ import annotations

import streamlit as st

from dashboard.components.disaster_sections import render_dataset_cards, render_flow_steps
from dashboard.components.layout import render_bordered_points, render_page_intro
from dashboard.config import apply_page_config
from dashboard.content import FLOW_STEPS, FUTURE_CODE_SNIPPETS, LIMITATIONS
from dashboard.services.disaster_data import build_dataset_catalog, load_dataset_bundle


apply_page_config("flow")

render_page_intro(
    "3 작동 설명",
    "청사진 이미지를 그대로 붙이지 않고, 현재 앱이 실제로 어떤 순서로 작동하는지 Streamlit 흐름 카드로 다시 구성했습니다.",
    "현재 구현된 구간과 나중에 바꿀 구간을 분리해서 읽을 수 있게 정리합니다.",
)

try:
    # 설명 페이지도 실제 연결된 데이터셋을 함께 보여 줘야
    # 사용자가 어떤 CSV 를 기준으로 흐름을 읽는지 이해하기 쉽다.
    bundle = load_dataset_bundle()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

# catalog 는 CSV 원본 역할을 설명 카드로 바꾸기 위한 중간 데이터다.
# 이 페이지는 DataFrame 자체보다 "이 파일이 무슨 책임을 가지는가"를 보여 주는 데 목적이 있다.
catalog = build_dataset_catalog(bundle)

with st.container(border=True):
    st.subheader("추천 플로우")
    # 단계 데이터는 content.py 에서 읽어 와 화면 설명과 문서 설명이 같은 표현을 쓰게 한다.
    # 청사진 이미지를 그대로 쓰지 않는 대신, 현재 구현과 미래 확장을 카드 형태로 분리해 읽게 한다.
    render_flow_steps(FLOW_STEPS)

st.divider()

left, right = st.columns([0.95, 1.05], gap="large")

with left:
    with st.container(border=True):
        st.subheader("현재 구현된 구간")
        # 이 목록은 실제 페이지/서비스 코드가 이미 수행하는 단계만 적어
        # 설명 페이지가 미래 스텁과 현재 동작을 혼동시키지 않게 만든다.
        st.markdown("- 지역 선택과 좌표 입력")
        st.markdown("- 최근 특보 요약")
        st.markdown("- 재난 유형 정규화")
        st.markdown("- 전용/대체 대피소 추천")
        st.markdown("- 무료 지도와 직선 거리 시각화")

    render_bordered_points("현재 단계의 제한", LIMITATIONS)

with right:
    with st.container(border=True):
        st.subheader("향후 교체 위치 예시")
        # 아래 코드 블록은 실행 코드가 아니라,
        # 미래 실시간 확장 시 어느 계층을 바꿔야 하는지 보여 주는 설명용 스텁이다.
        st.code(FUTURE_CODE_SNIPPETS["geolocation"], language="python")
        st.code(FUTURE_CODE_SNIPPETS["alerts"], language="python")
        st.code(FUTURE_CODE_SNIPPETS["routing"], language="python")

st.divider()

with st.container(border=True):
    st.subheader("현재 연결된 데이터셋")
    # 동일한 데이터셋 카드 컴포넌트를 재사용하면 홈과 설명 페이지의 데이터 설명 톤이 어긋나지 않는다.
    render_dataset_cards(catalog)
