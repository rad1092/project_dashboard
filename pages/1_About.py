"""재난 대피소 추천 프로젝트 소개 페이지."""

from __future__ import annotations

import os

import streamlit as st

APP_TITLE = "재난 대피소 추천 워크스페이스"
APP_ICON = "🛟"
PAGE_LABEL = "1 About"
DETAIL_DOC_PATH = "docs/04_INTERNAL_FUNCTION_CLEANUP.md"

ABOUT_DATA = {
    "name": "재난 대피소 추천 + 분석 프로젝트",
    "headline": "전처리된 재난 특보 이력과 대피소 좌표 데이터를 바탕으로 추천 흐름과 분석 화면을 함께 보여주는 Streamlit 앱",
    "intro": (
        "이 프로젝트는 유료 API 없이도 사용자가 입력한 좌표와 지역 기준으로 "
        "어떤 재난 상황에서 어떤 대피소를 먼저 봐야 하는지 설명 가능한 형태로 보여주는 데 초점을 둔다. "
        "상세 구현 설명은 docs 로 옮기고, 이 페이지는 현재 목표와 읽는 순서를 짧게 안내한다."
    ),
    "focus_areas": [
        "좌표 기준 활성 지역 감지와 최근 특보 요약",
        "재난 그룹별 전용 대피소 우선 추천과 통합 대피소 fallback",
        "추천 페이지와 분석 페이지가 같은 데이터 범위를 공유하도록 유지",
    ],
    "tech_stack": ["Python", "Streamlit", "pandas", "plotly", "folium"],
    "principles": [
        "유료 API와 유료 지도 API는 넣지 않는다.",
        "외부 전처리 CSV는 앱에서 수정하지 않고 읽기 전용으로만 사용한다.",
        "페이지, 테스트, docs 를 함께 갱신해 설명과 동작이 어긋나지 않게 한다.",
    ],
    "next_steps": [
        "자동 위치 권한과 실시간 특보 API를 붙일 인터페이스를 문서 기준으로 정리",
        "추천 결과와 분석 결과가 같은 데이터 계약을 유지하도록 테스트 보강",
        "설명 페이지는 얇게 유지하고 상세 맥락은 docs 쪽으로 모으기",
    ],
}

LIMITATIONS = [
    "현재 화면의 특보는 과거 전처리 데이터 기준이며 실시간 재난 상황을 보장하지 않는다.",
    "지도는 무료 OSM 타일과 직선 거리만 사용하므로 실제 주행/도보 경로와 다를 수 있다.",
    "재난별 전용 대피소가 부족한 경우에는 통합 대피소를 대체 후보로 함께 보여준다.",
]

DATASET_SCOPE = [
    "`danger_clean.csv`: 재난 특보 이력",
    "`final_shelter_dataset.csv`: 통합 또는 일반 대피소",
    "`earthquake_shelter_clean_2.csv`: 지진대피장소",
    "`tsunami_shelter_clean_2.csv`: 해일대피장소",
]

NEXT_READING_ORDER = [
    "`2 대피소 추천`: 현재 데이터 기준 실제 추천 결과",
    "`3 작동 설명`: 추천이 어떤 단계로 계산되는지 요약",
    "`4 실시간 준비`: 미래 확장 포인트와 준비 상태",
    "`6 Data Analysis`: 과거 특보와 대피소 분포를 분석 관점으로 확인",
]


def render_page() -> None:
    """소개 페이지를 렌더링한다."""

    st.set_page_config(
        page_title=f"{APP_TITLE} | {PAGE_LABEL}",
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("1 About")
    st.write(
        "이 프로젝트는 전처리된 재난 특보 이력과 대피소 데이터를 이용해 추천 결과와 분석 구조를 함께 보여주는 앱이다."
    )
    st.caption("상세 구현 설명은 페이지 안에 길게 두지 않고 docs 로 분리해 유지한다.")

    overview_column, guide_column = st.columns([1.05, 0.95], gap="large")

    with overview_column:
        with st.container(border=True):
            st.subheader(ABOUT_DATA["name"])
            st.write(ABOUT_DATA["headline"])
            st.write(ABOUT_DATA["intro"])

        with st.container(border=True):
            st.subheader("집중하고 있는 방향")
            for item in ABOUT_DATA["focus_areas"]:
                st.markdown(f"- {item}")

        with st.container(border=True):
            st.subheader("운영 원칙")
            for item in ABOUT_DATA["principles"]:
                st.markdown(f"- {item}")

    with guide_column:
        with st.container(border=True):
            st.subheader("기술 스택")
            st.markdown(" ".join(f"`{item}`" for item in ABOUT_DATA["tech_stack"]))

        with st.container(border=True):
            st.subheader("현재 데이터 범위")
            for item in DATASET_SCOPE:
                st.markdown(f"- {item}")

        with st.container(border=True):
            st.subheader("현재 한계")
            for item in LIMITATIONS:
                st.markdown(f"- {item}")

    st.divider()

    next_column, docs_column = st.columns(2, gap="large")

    with next_column:
        with st.container(border=True):
            st.subheader("다음 단계")
            for item in ABOUT_DATA["next_steps"]:
                st.markdown(f"- {item}")

        with st.container(border=True):
            st.subheader("이후 페이지 읽는 순서")
            for item in NEXT_READING_ORDER:
                st.markdown(f"- {item}")

    with docs_column:
        with st.container(border=True):
            st.subheader("상세 설명 위치")
            st.write(
                "페이지 내부 함수 정리 기준, 설명 페이지에서 뺀 세부 맥락, 실시간 스텁 예시는 아래 docs 파일로 옮겨 관리한다."
            )
            st.code(DETAIL_DOC_PATH, language="text")


if os.environ.get("PROJECT_DASHBOARD_IMPORT_ONLY") != "1":
    render_page()
