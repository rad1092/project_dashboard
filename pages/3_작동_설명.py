"""대피소 추천이 어떤 흐름으로 작동하는지 설명하는 페이지."""

import os

import streamlit as st

APP_TITLE = "재난 대피소 추천 워크스페이스"
APP_ICON = "🛟"
PAGE_LABEL = "3 작동 설명"
DETAIL_DOC_PATH = "docs/04_INTERNAL_FUNCTION_CLEANUP.md"

FLOW_STEPS = [
    {
        "step": "01",
        "title": "좌표 입력과 지역 감지",
        "summary": "입력 좌표에서 가장 가까운 지역 중심을 찾아 활성 지역을 정한다.",
        "status": "현재 구현",
        "now_note": "감지 결과가 애매하면 사이드바에서 수동 보정한다.",
        "future_note": "브라우저 위치 권한과 reverse geocoding 은 docs 기준으로 나중에 붙인다.",
    },
    {
        "step": "02",
        "title": "최근 특보 요약",
        "summary": "활성 지역의 최근 특보 이력에서 재난 유형과 최신 시각을 요약한다.",
        "status": "현재 구현",
        "now_note": "현재는 과거 전처리 데이터 안에서만 최근 이력을 찾고, 이 정보는 참고용으로만 보여준다.",
        "future_note": "실시간 특보 API 는 준비 페이지와 docs 에서만 미리 정리한다.",
    },
    {
        "step": "03",
        "title": "재난 그룹 정규화",
        "summary": "원본 특보 명칭을 내부 재난 그룹으로 묶고, 사용자가 선택한 재난 기준으로 후보 계산을 시작한다.",
        "status": "현재 구현",
        "now_note": "강풍/풍랑, 호우/태풍처럼 비슷한 상황을 같은 그룹으로 관리하고, 재난을 선택하기 전에는 추천을 계산하지 않는다.",
        "future_note": "실시간 응답 구조가 달라져도 분류 기준은 함수 하나로 유지한다.",
    },
    {
        "step": "04",
        "title": "후보 대피소 구성",
        "summary": "전용 대피소를 먼저 찾고 부족하면 통합 대피소를 fallback 으로 더한다.",
        "status": "현재 구현",
        "now_note": "전용, 기본, 대체 대피소를 다른 라벨로 구분하고, 어떤 후보를 계산할지는 사용자가 고른 재난 기준으로 정한다.",
        "future_note": "재난별 세부 정책은 후보 필터 기준만 교체하면 된다.",
    },
    {
        "step": "05",
        "title": "거리 정렬과 지도 표시",
        "summary": "직선 거리 기준으로 후보를 정렬하되 가장 가까운 후보도 3km를 넘으면 Top 3 대신 추천 보류로 안내한다.",
        "status": "현재 구현",
        "now_note": "실제 도로 경로나 이동 시간은 제공하지 않고, 멀리 있는 후보는 행동형 추천으로 보여주지 않는다.",
        "future_note": "경로 API 는 문서에 적은 교체 지점에서 붙인다.",
    },
]

LIMITATIONS = [
    "현재 화면의 특보는 과거 전처리 데이터 기준이며 실시간 재난 상황을 보장하지 않는다.",
    "지도는 무료 OSM 타일과 직선 거리만 사용하므로 실제 주행/도보 경로와 다를 수 있다.",
    "재난별 전용 대피소가 부족하면 통합 대피소를 대체 후보로 더하되, 가장 가까운 후보도 직선 거리 3km를 넘으면 추천을 보류한다.",
]

IMPLEMENTED_SCOPE = [
    "좌표 입력과 활성 지역 감지",
    "최근 특보 요약, 재난 그룹 정규화, 재난 수동 선택",
    "전용 대피소 우선 추천과 fallback",
    "직선 거리 기준 지도, 결과 표, 추천 보류 가드",
]

DETAILS_MOVED_TO_DOCS = [
    "내부 함수 정리 기준",
    "설명 페이지에서 제거한 긴 코드 스텁",
    "실시간 준비 단계에서 바뀔 함수 위치",
    "페이지 안에 다시 넣지 않기로 한 과한 구현 설명",
]


def render_page() -> None:
    """작동 설명 페이지를 렌더링한다."""

    st.set_page_config(
        page_title=f"{APP_TITLE} | {PAGE_LABEL}",
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("3 작동 설명")
    st.write(
        "현재 앱이 실제로 어떤 순서로 작동하는지만 요약해서 보여준다. 세부 구현 설명과 긴 스텁 코드는 docs 로 옮겨 유지한다."
    )
    st.caption("이 페이지는 추천 플로우를 빠르게 읽는 요약판이고, 상세 맥락은 docs 에 둔다.")

    with st.container(border=True):
        st.subheader("추천 플로우")
        for item in FLOW_STEPS:
            with st.container(border=True):
                st.markdown(f"**{item['step']}. {item['title']}**  `{item['status']}`")
                st.write(item["summary"])
                st.markdown(f"**현재 구현**: {item['now_note']}")
                st.markdown(f"**나중에 바꿀 지점**: {item['future_note']}")

    st.divider()

    left_column, right_column = st.columns(2, gap="large")

    with left_column:
        with st.container(border=True):
            st.subheader("현재 구현된 구간")
            for item in IMPLEMENTED_SCOPE:
                st.markdown(f"- {item}")

        with st.container(border=True):
            st.subheader("현재 단계의 제한")
            for item in LIMITATIONS:
                st.markdown(f"- {item}")

    with right_column:
        with st.container(border=True):
            st.subheader("상세 내용을 docs 로 옮긴 항목")
            for item in DETAILS_MOVED_TO_DOCS:
                st.markdown(f"- {item}")

        with st.container(border=True):
            st.subheader("상세 설명 위치")
            st.write("실시간 스텁과 내부 함수 정리 기준은 아래 docs 파일에서 함께 관리한다.")
            st.code(DETAIL_DOC_PATH, language="text")


if os.environ.get("PROJECT_DASHBOARD_IMPORT_ONLY") != "1":
    render_page()
