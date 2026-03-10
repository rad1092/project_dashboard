"""현재 재난 앱 구현 작업을 기록하는 프로젝트 페이지."""

import os

import streamlit as st

APP_TITLE = "재난 대피소 추천 워크스페이스"
APP_ICON = "🛟"
PAGE_LABEL = "5 Projects"

PROJECT_ITEMS = [
    {
        "title": "전처리 데이터 기반 대피소 추천 페이지",
        "status": "active",
        "summary": "좌표와 재난 유형을 입력하면 활성 지역을 자동 감지하고 직선 거리 기준 대피소 Top 3를 보여주는 핵심 사용자 페이지",
        "role": "데이터 연결, 추천 규칙 정의, 지도 시각화, 사용자 입력 흐름 설계",
        "highlights": [
            "유료 API 없이 OSM 기반 지도와 거리 계산만으로 추천 흐름 구성",
            "통합 대피소 평균 좌표로 가장 가까운 지역을 감지하고 필요하면 수동 보정",
            "전용 대피소가 있으면 우선 추천하고, 부족하면 통합 대피소로 fallback",
            "현재 위치 자동 감지 확장을 고려한 좌표 우선 입력 구조 준비",
        ],
        "next_action": "실시간 특보 API와 자동 위치 권한 연동을 붙일 인터페이스를 더 구체화한다.",
    },
    {
        "title": "추천 작동 설명 페이지",
        "status": "building",
        "summary": "추천 결과가 어떤 데이터와 어떤 순서의 계산을 거쳐 나오는지 사용자와 개발자 모두가 이해할 수 있게 설명하는 페이지",
        "role": "플로우 설계, 데이터 계약 설명, 구현 범위와 확장 범위 분리",
        "highlights": [
            "청사진 PNG를 그대로 쓰지 않고 Streamlit 흐름 카드로 재구성",
            "현재 구현된 무료 구간과 미래 실시간 구간을 분리해 설명",
            "과한 구현 설명은 docs 로 옮기고 페이지는 요약판으로 유지",
        ],
        "next_action": "실시간 연결 시 어떤 함수와 페이지를 바꿔야 하는지 체크리스트까지 연결한다.",
    },
    {
        "title": "실시간 확장 준비 구조",
        "status": "planned",
        "summary": "현재는 비활성화해 두지만, 나중에 자동 위치·실시간 특보·경로 API를 어디에 붙일지 코드와 문서로 먼저 설계하는 작업",
        "role": "확장 포인트 설계, docs 기준 정리, 미래 인터페이스 고정",
        "highlights": [
            "현재 기능과 미래 기능을 한 파일에 섞지 않고 준비 페이지로 분리",
            "비활성화된 버튼과 docs 경로로 확장 위치를 명확히 표시",
            "실시간 전환 시에도 기존 추천 페이지 구조를 최대한 유지하도록 설계",
        ],
        "next_action": "실시간 API를 붙이기 전에 권한, 호출량, 실패 처리 기준을 먼저 문서화한다.",
    },
]

STATUS_LABELS = {
    "building": "구축 중",
    "planned": "계획 단계",
    "active": "운영 중",
}


def render_page() -> None:
    """프로젝트 페이지를 렌더링한다."""

    st.set_page_config(
        page_title=f"{APP_TITLE} | {PAGE_LABEL}",
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("5 Projects")
    st.write(
        "현재 저장소 안에서 진행 중인 재난 대피소 추천 기능과 설명 구조 작업을 카드 형태로 정리한 페이지입니다."
    )
    st.caption("실제 구현 작업이 늘어날수록 이 목록을 계속 갱신해 프로젝트 맥락을 남깁니다.")

    for item in PROJECT_ITEMS:
        status_label = STATUS_LABELS.get(str(item["status"]), str(item["status"]))
        with st.container(border=True):
            top_left, top_right = st.columns([0.75, 0.25])
            with top_left:
                st.subheader(item["title"])
                st.write(item["summary"])
            with top_right:
                st.metric("상태", status_label)

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

    with st.container(border=True):
        st.subheader("프로젝트 기록 기준")
        st.markdown("- 화면만 예쁜 항목이 아니라 데이터, 규칙, 다음 액션이 보이는 작업만 남긴다.")
        st.markdown("- 현재 동작과 미래 확장 구간을 같은 카드 안에서 섞지 않는다.")
        st.markdown("- 문서와 테스트까지 같이 갱신된 작업을 중심으로 기록한다.")


if os.environ.get("PROJECT_DASHBOARD_IMPORT_ONLY") != "1":
    render_page()
