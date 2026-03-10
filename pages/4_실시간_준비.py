"""향후 실시간 버전 확장 포인트를 설명하는 준비 페이지."""

from __future__ import annotations

import os

import streamlit as st

APP_TITLE = "재난 대피소 추천 워크스페이스"
APP_ICON = "🛟"
PAGE_LABEL = "4 실시간 준비"

REALTIME_EXPANSION_ITEMS = [
    {
        "title": "현재 위치 자동 감지",
        "summary": "브라우저 위치 권한을 받아 위도와 경도를 자동 채우는 기능",
        "why_blocked": "현재는 권한 요청과 브라우저 연동 로직을 넣지 않았기 때문에 수동 입력만 사용한다.",
    },
    {
        "title": "실시간 재난 특보 갱신",
        "summary": "실시간 공공 API에서 최신 특보를 받아 추천 재난 유형을 자동 선택하는 기능",
        "why_blocked": "현재 저장소에는 실시간 API 키와 수신 구조가 없으므로 전처리된 과거 데이터만 사용한다.",
    },
    {
        "title": "실제 경로 안내",
        "summary": "직선 거리 대신 실제 도로 경로와 이동 시간을 보여주는 기능",
        "why_blocked": "유료 길찾기 API를 쓰지 않기로 했기 때문에 현재는 거리선과 정렬만 제공한다.",
    },
]

FUTURE_CODE_SNIPPETS = {
    "geolocation": """def get_browser_location() -> tuple[float, float] | None:\n    # TODO: 브라우저 위치 권한을 받은 뒤 사용자의 현재 좌표를 반환한다.\n    # 현재 단계에서는 수동 위경도 입력을 기본값으로 유지하므로 실제 호출은 막아 둔다.\n    return None\n""",
    "alerts": """def fetch_realtime_alerts() -> list[dict[str, str]]:\n    # TODO: 실시간 공공 API가 준비되면 최신 특보를 읽어 현재 재난 유형을 자동 선택한다.\n    # 지금은 전처리된 CSV만 사용하므로 이 함수는 설명용 스텁으로만 남겨 둔다.\n    return []\n""",
    "routing": """def build_live_route(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> dict[str, object] | None:\n    # TODO: 실제 경로 API를 붙이면 직선 거리 대신 도로 기준 경로와 시간을 반환한다.\n    # 유료 API를 쓰지 않는 현재 구조에서는 None 을 반환하고 직선 거리 시각화만 유지한다.\n    return None\n""",
}


def apply_page_config() -> None:
    """실시간 준비 페이지의 Streamlit 기본 설정을 적용한다."""

    st.set_page_config(
        page_title=f"{APP_TITLE} | {PAGE_LABEL}",
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )


def render_page_intro(title: str, subtitle: str, caption: str | None = None) -> None:
    """페이지 상단의 공통 제목 블록을 그린다."""

    st.title(title)
    st.write(subtitle)
    if caption:
        st.caption(caption)


def render_bordered_points(title: str, items: list[str]) -> None:
    """제목과 글머리표 목록이 들어간 테두리 컨테이너를 렌더링한다."""

    with st.container(border=True):
        st.subheader(title)
        for item in items:
            st.markdown(f"- {item}")


def render_page() -> None:
    """실시간 준비 페이지를 렌더링한다."""

    apply_page_config()

    render_page_intro(
        "4 실시간 준비",
        "현재는 실행하지 않지만, 나중에 자동 위치·실시간 특보·경로 안내를 어디에 붙일지 설명과 주석으로 먼저 정리한 페이지입니다.",
        "이 페이지의 버튼은 설명용 자리표시자이며 실제 API 호출을 하지 않습니다.",
    )

    button_columns = st.columns(3)
    button_columns[0].button("현재 위치 자동 감지 (준비중)", disabled=True)
    button_columns[1].button("실시간 특보 새로고침 (준비중)", disabled=True)
    button_columns[2].button("실제 경로 안내 (준비중)", disabled=True)

    st.info(
        "현재 앱은 과거 전처리 데이터와 수동 좌표 입력을 기준으로 동작한다. "
        "아래 내용은 미래에 어떤 코드를 어디에 붙일지 설명하기 위한 준비 문서 역할을 한다."
    )

    for item in REALTIME_EXPANSION_ITEMS:
        with st.container(border=True):
            st.subheader(item["title"])
            st.write(item["summary"])
            st.markdown(f"**지금 막아 둔 이유**: {item['why_blocked']}")

    left, right = st.columns(2, gap="large")

    with left:
        with st.container(border=True):
            st.subheader("자동 위치 스텁")
            st.code(FUTURE_CODE_SNIPPETS["geolocation"], language="python")

        with st.container(border=True):
            st.subheader("실시간 특보 스텁")
            st.code(FUTURE_CODE_SNIPPETS["alerts"], language="python")

    with right:
        with st.container(border=True):
            st.subheader("경로 안내 스텁")
            st.code(FUTURE_CODE_SNIPPETS["routing"], language="python")

        render_bordered_points(
            "실시간 전환 전에 먼저 정리할 것",
            [
                "위치 권한을 받을 브라우저/컴포넌트 방식을 정한다.",
                "실시간 공공 API의 인증 방식과 호출 제한을 문서화한다.",
                "직선 거리와 실제 경로를 어떤 버튼과 어떤 문구로 구분할지 정한다.",
            ],
        )


if os.environ.get("PROJECT_DASHBOARD_IMPORT_ONLY") != "1":
    render_page()
