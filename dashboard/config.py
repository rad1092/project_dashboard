"""Streamlit 앱 공통 설정 모듈.

모든 페이지와 홈 엔트리포인트가 이 모듈을 import 해서
앱 제목, 아이콘, 페이지별 라벨과 요약을 한 곳에서 공유한다.

이 파일을 수정하는 대표 상황:
- 브라우저 탭 제목이나 앱 아이콘을 바꾸고 싶을 때
- 새 페이지를 추가해 ``PAGE_META`` 에 등록할 때
- 홈 화면과 문서에서 사용하는 페이지 설명 문구를 맞추고 싶을 때
"""

from __future__ import annotations

import streamlit as st

# APP_TITLE과 APP_ICON은 모든 페이지의 브라우저 탭 정보와
# 홈 화면 안내 문구에서 공통으로 참조하는 기본 앱 메타데이터다.
APP_TITLE = "Streamlit Project Workspace"
APP_ICON = "📊"

# PAGE_META는 페이지 키와 화면용 라벨/요약을 연결한다.
# app.py는 이 값을 홈 화면 목록에 사용하고,
# 각 pages/*.py 파일은 자신의 page_key로 현재 페이지 메타데이터를 읽는다.
PAGE_META = {
    "home": {
        "label": "프로젝트와 분석을 정리하는 저장소",
        "summary": "저장소 목적, 현재 상태, 문서 읽는 순서를 보여주는 홈 화면",
    },
    "about": {
        "label": "About",
        "summary": "저장소 운영 기준, 작업 원칙, 소개를 정리한 페이지",
    },
    "projects": {
        "label": "Projects",
        "summary": "프로젝트 기록과 작업 맥락을 정리하는 페이지",
    },
    "analysis": {
        "label": "Data Analysis",
        "summary": "샘플 데이터 기반 분석 화면과 구조 예시를 보여주는 페이지",
    },
    "learning": {
        "label": "Learning Log",
        "summary": "학습 주제, 로드맵, 운영 원칙을 정리한 페이지",
    },
}


def apply_page_config(page_key: str) -> None:
    """주어진 페이지 키에 맞는 Streamlit 기본 설정을 적용한다.

    Args:
        page_key: ``PAGE_META`` 에 등록된 페이지 식별자.
            예를 들어 홈은 ``home``, About 페이지는 ``about`` 을 사용한다.

    이 함수가 필요한 이유:
    - 각 페이지 파일에서 ``st.set_page_config`` 코드를 반복하지 않기 위해
    - 제목, 아이콘, 레이아웃 기준을 한 곳에서 관리하기 위해
    """
    page = PAGE_META[page_key]
    st.set_page_config(
        page_title=f"{APP_TITLE} | {page['label']}",
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )