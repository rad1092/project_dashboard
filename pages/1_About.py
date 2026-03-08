"""재난 대피소 추천 프로젝트 소개 페이지.

이 페이지는 프로젝트의 목적, 현재 구현 범위, 데이터 한계를 먼저 설명하는 허브다.
사용자가 추천 화면으로 바로 넘어가기 전에
"이 앱이 어떤 데이터를 기반으로 무엇을 하려는지"를 이해하게 만드는 역할을 맡는다.
"""

from __future__ import annotations

import streamlit as st

from dashboard.components.layout import (
    render_bordered_points,
    render_chip_list,
    render_page_intro,
)
from dashboard.config import apply_page_config
from dashboard.content import ABOUT_DATA, LIMITATIONS
from dashboard.services.disaster_data import build_dataset_catalog, load_dataset_bundle
from dashboard.utils.formatters import format_number


# 페이지 번호와 탭 제목이 다른 페이지와 어긋나지 않도록 공통 설정 함수를 먼저 호출한다.
# About 도 예외 없이 같은 메타데이터 체계를 따라야 홈/사이드바/문서가 같은 순서를 유지한다.
apply_page_config("about")

render_page_intro(
    "1 About",
    "이 프로젝트는 전처리된 재난 특보 이력과 대피소 데이터를 이용해 추천 결과와 분석 구조를 함께 보여주는 앱입니다.",
    "현재 단계에서는 과거 데이터 기반 추천과 설명 구조를 먼저 안정화하고 있습니다.",
)

# 왼쪽은 프로젝트 의미 설명, 오른쪽은 기술 스택과 한계처럼 보조 정보를 배치한다.
left, right = st.columns([1.1, 0.9], gap="large")

with left:
    with st.container(border=True):
        st.subheader(ABOUT_DATA["name"])
        st.write(ABOUT_DATA["headline"])
        # intro 는 headline 보다 길고 설명형 문장이라 별도 write 로 내려 읽게 한다.
        st.write(ABOUT_DATA["intro"])

    render_bordered_points("집중하고 있는 방향", ABOUT_DATA["focus_areas"])
    render_bordered_points("운영 원칙", ABOUT_DATA["principles"])

with right:
    with st.container(border=True):
        st.subheader("기술 스택")
        # 기술 스택은 긴 설명보다 태그형 표현이 더 읽기 쉬워 공통 chip 렌더러를 재사용한다.
        render_chip_list(ABOUT_DATA["tech_stack"])

    render_bordered_points("다음 단계", ABOUT_DATA["next_steps"])

    with st.container(border=True):
        st.subheader("현재 한계")
        for item in LIMITATIONS:
            st.markdown(f"- {item}")

st.divider()

try:
    # 소개 페이지에서도 실제 데이터 연결 상태를 보여 주면
    # 이 프로젝트가 현재 데이터 기반으로 움직인다는 점을 바로 전달할 수 있다.
    bundle = load_dataset_bundle()
    catalog = build_dataset_catalog(bundle)
except FileNotFoundError as exc:
    st.warning(str(exc))
else:
    with st.container(border=True):
        st.subheader("현재 연결된 전처리 데이터")
        # 소개 페이지에서도 실제 데이터 행 수를 보여 주면
        # 이 프로젝트가 더미 화면이 아니라 실데이터 기반이라는 점을 초반에 전달할 수 있다.
        for item in catalog:
            st.markdown(
                f"- **{item['name']}**: {format_number(item['rows'])}건, {item['description']}"
            )

st.divider()

with st.container(border=True):
    st.subheader("이후 페이지 읽는 순서")
    # About 페이지가 단순 소개에서 끝나지 않도록 다음 탐색 경로를 함께 안내한다.
    st.markdown("- `2 대피소 추천`: 현재 데이터 기준 실제 추천 결과를 본다.")
    st.markdown("- `3 작동 설명`: 추천이 어떤 계산 단계로 만들어지는지 확인한다.")
    st.markdown("- `4 실시간 준비`: 미래 확장 구조와 비활성화된 스텁을 본다.")
    st.markdown("- `6 Data Analysis`: 과거 특보와 대피소 분포를 분석 관점으로 본다.")
