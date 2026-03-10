"""학습 로그와 확장 로드맵 페이지."""

import os

import streamlit as st

APP_TITLE = "재난 대피소 추천 워크스페이스"
APP_ICON = "🛟"
PAGE_LABEL = "7 Learning Log"
DETAIL_DOC_PATH = "docs/04_INTERNAL_FUNCTION_CLEANUP.md"

LEARNING_TOPICS = [
    {
        "phase": "01",
        "title": "데이터 경로와 외부 자원 읽기",
        "summary": "앱이 프로젝트 밖의 전처리 폴더를 안정적으로 읽고, 없는 경우에는 명확한 오류를 보여주는 방법을 정리한다.",
        "why_it_matters": "실제 데이터는 프로젝트 밖에서 계속 갱신될 수 있으므로 경로 탐색과 안내 메시지가 구조의 시작점이 되기 때문이다.",
        "next_practice": "환경변수, secrets, 기본 경로 fallback 순서를 유지한 채 경로 검증 테스트를 추가한다.",
    },
    {
        "phase": "02",
        "title": "재난 유형 정규화와 추천 규칙",
        "summary": "서로 다른 재난 명칭을 내부 그룹으로 정규화하고 어떤 대피소를 우선 추천할지 규칙으로 관리한다.",
        "why_it_matters": "추천 로직이 페이지 안에 흩어지면 나중에 실시간 API를 붙일 때 기준을 잃기 쉽기 때문이다.",
        "next_practice": "재난 그룹 추가가 필요할 때 페이지 코드와 설명 문서를 동시에 갱신한다.",
    },
    {
        "phase": "03",
        "title": "무료 지도와 거리 시각화",
        "summary": "유료 지도 없이도 사용자 위치, 추천 대피소, 직선 거리선을 한 화면에 읽기 쉽게 배치하는 방법을 다룬다.",
        "why_it_matters": "현재 단계에서는 네비게이션이 아니라 추천 후보 확인이 목적이므로, 단순하지만 분명한 지도 표현이 중요하다.",
        "next_practice": "후보 개수가 늘어날 때도 지도와 표가 같은 결과를 유지하는지 검증한다.",
    },
    {
        "phase": "04",
        "title": "추천 결과와 분석 화면 분리",
        "summary": "실사용 성격의 추천 페이지와 과거 이력 분석 페이지를 역할별로 분리해 서로 다른 읽기 흐름을 만든다.",
        "why_it_matters": "사용자에게는 추천 결과가 먼저 중요하고, 개발자나 리뷰어에게는 근거 데이터 분석이 따로 필요하기 때문이다.",
        "next_practice": "분석 페이지에서 나온 인사이트를 추천 페이지 문구와 어떻게 연결할지 정리한다.",
    },
]

ROADMAP_STEPS = [
    {
        "stage": "Step 1",
        "goal": "현재 추천 흐름 안정화",
        "plan": "전처리 데이터만으로도 지역 선택, 재난 선택, 좌표 입력, Top 3 추천이 안정적으로 작동하게 다듬는다.",
        "done_definition": "빈 결과와 좌표 누락 같은 예외에서도 안내 메시지가 분명하게 보인다.",
    },
    {
        "stage": "Step 2",
        "goal": "실시간 입력 구조 연결",
        "plan": "브라우저 위치 권한과 실시간 특보 API가 들어와도 현재 추천 페이지의 화면 구조를 크게 바꾸지 않도록 페이지 인터페이스를 유지한다.",
        "done_definition": "수동 입력 대신 자동 입력으로 바꿔도 추천 화면 출력 코드는 대부분 유지된다.",
    },
    {
        "stage": "Step 3",
        "goal": "경로 안내 확장 설계",
        "plan": "유료 API나 외부 경로 서비스를 붙일 필요가 생길 때 어느 함수와 어느 버튼에서 교체할지 문서와 코드 주석을 맞춘다.",
        "done_definition": "직선 거리 표시를 실제 경로 안내로 대체할 지점이 코드와 docs 양쪽에서 명확하다.",
    },
    {
        "stage": "Step 4",
        "goal": "설명 문서와 검증 체계 고도화",
        "plan": "README, docs, 테스트가 현재 구조와 같은 이야기를 하도록 계속 보강한다.",
        "done_definition": "처음 보는 사람도 홈과 docs만 읽고 데이터 범위와 확장 한계를 이해할 수 있다.",
    },
]


def render_page() -> None:
    """학습 로그 페이지를 렌더링한다."""

    st.set_page_config(
        page_title=f"{APP_TITLE} | {PAGE_LABEL}",
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("7 Learning Log")
    st.write("현재 저장소를 통해 무엇을 배우고, 어떤 순서로 재난 앱을 확장할지 정리한 페이지입니다.")
    st.caption("코드와 문서를 같이 유지하기 위한 학습 포인트와 로드맵을 함께 기록합니다.")

    topic_tab, roadmap_tab, rules_tab = st.tabs(["학습 주제", "로드맵", "운영 규칙"])

    with topic_tab:
        for topic in LEARNING_TOPICS:
            with st.container(border=True):
                st.subheader(f"{topic['phase']}. {topic['title']}")
                st.write(topic["summary"])
                st.markdown(f"**왜 중요한가**: {topic['why_it_matters']}")
                st.markdown(f"**다음 연습**: {topic['next_practice']}")

    with roadmap_tab:
        for step in ROADMAP_STEPS:
            with st.container(border=True):
                st.subheader(f"{step['stage']} - {step['goal']}")
                st.write(step["plan"])
                st.markdown(f"**완료 기준**: {step['done_definition']}")

    with rules_tab:
        with st.container(border=True):
            st.subheader("반드시 지킬 점")
            st.markdown("- 외부 전처리 CSV는 앱에서 수정하지 않고 읽기 전용으로만 사용한다.")
            st.markdown("- 유료 API와 유료 지도 API는 현재 단계 코드에 넣지 않는다.")
            st.markdown("- 각 페이지 파일이 자기 화면 흐름과 데이터 규칙을 직접 설명할 수 있게 유지한다.")
            st.markdown("- 새 기능을 넣을 때는 docs와 테스트를 함께 갱신한다.")
            st.markdown(f"- 상세 정리 기준은 `{DETAIL_DOC_PATH}` 에서 함께 관리한다.")


if os.environ.get("PROJECT_DASHBOARD_IMPORT_ONLY") != "1":
    render_page()
