"""향후 실시간 버전 확장 포인트를 설명하는 준비 페이지."""

import os

import streamlit as st

APP_TITLE = "재난 대피소 추천 워크스페이스"
APP_ICON = "🛟"
PAGE_LABEL = "4 실시간 준비"
DETAIL_DOC_PATH = "docs/04_INTERNAL_FUNCTION_CLEANUP.md"

REALTIME_EXPANSION_ITEMS = [
    {
        "title": "현재 위치 자동 감지",
        "summary": "브라우저 위치 권한을 받아 위도와 경도를 자동 채우는 기능",
        "why_blocked": "현재는 권한 요청과 브라우저 연동을 넣지 않아 수동 입력만 사용한다.",
    },
    {
        "title": "실시간 재난 특보 갱신",
        "summary": "실시간 공공 API에서 최신 특보를 받아 추천 재난 유형을 자동 선택하는 기능",
        "why_blocked": "현재 저장소에는 API 키와 수신 구조가 없어 과거 전처리 데이터만 사용한다.",
    },
    {
        "title": "실제 경로 안내",
        "summary": "직선 거리 대신 실제 도로 경로와 이동 시간을 보여주는 기능",
        "why_blocked": "유료 길찾기 API를 쓰지 않기로 했기 때문에 현재는 거리선과 정렬만 제공한다.",
    },
]

PREPARATION_RULES = [
    "실시간 기능은 현재 추천 페이지 안에 미리 섞지 않는다.",
    "API 인증 방식, 호출 제한, 실패 처리 기준을 먼저 docs 로 고정한다.",
    "직선 거리와 실제 경로는 문구와 버튼에서 분명히 구분한다.",
]


def render_page() -> None:
    """실시간 준비 페이지를 렌더링한다."""

    st.set_page_config(
        page_title=f"{APP_TITLE} | {PAGE_LABEL}",
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("4 실시간 준비")
    st.write(
        "지금은 실행하지 않지만, 나중에 자동 위치·실시간 특보·경로 안내를 어디에 붙일지 준비 상태만 짧게 정리한다."
    )
    st.caption("긴 스텁 코드는 페이지가 아니라 docs 에 둔다.")

    button_columns = st.columns(3)
    button_columns[0].button("현재 위치 자동 감지 (준비중)", disabled=True)
    button_columns[1].button("실시간 특보 새로고침 (준비중)", disabled=True)
    button_columns[2].button("실제 경로 안내 (준비중)", disabled=True)

    st.info(
        "현재 앱은 과거 전처리 데이터와 수동 좌표 입력을 기준으로 동작한다. "
        "이 페이지는 미래 확장 포인트를 짧게 표시하는 요약판이다."
    )

    for item in REALTIME_EXPANSION_ITEMS:
        with st.container(border=True):
            st.subheader(item["title"])
            st.write(item["summary"])
            st.markdown(f"**지금 막아 둔 이유**: {item['why_blocked']}")

    left_column, right_column = st.columns(2, gap="large")

    with left_column:
        with st.container(border=True):
            st.subheader("실시간 전환 전 기준")
            for item in PREPARATION_RULES:
                st.markdown(f"- {item}")

    with right_column:
        with st.container(border=True):
            st.subheader("상세 스텁 위치")
            st.write("자동 위치, 실시간 특보, 경로 API 예시 스텁은 아래 docs 파일에 모아 둔다.")
            st.code(DETAIL_DOC_PATH, language="text")


if os.environ.get("PROJECT_DASHBOARD_IMPORT_ONLY") != "1":
    render_page()
