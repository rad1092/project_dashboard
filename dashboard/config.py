"""Streamlit 앱 공통 설정 모듈.

왜 필요한가:
- 여러 페이지가 제목, 아이콘, 라벨을 제각각 들고 있으면 번호 체계와 소개 문구가 쉽게 어긋난다.
- 이 모듈은 페이지 메타데이터를 한곳에 모아 홈, 사이드바, 문서 설명이 같은 기준을 보게 만든다.

누가 사용하는가:
- ``app.py`` 와 ``pages/*.py`` 파일이 모두 이 모듈을 읽는다.

무엇을 다루는가:
- 앱 공통 제목/아이콘
- 페이지별 라벨, 요약, 번호 체계
- ``st.set_page_config`` 적용 함수

나중에 어디를 바꾸면 되는가:
- 페이지 순서나 이름이 바뀌면 ``PAGE_META`` 를 먼저 수정한다.
- 브라우저 탭 제목/아이콘을 바꾸고 싶으면 ``APP_TITLE`` 과 ``APP_ICON`` 을 수정한다.
"""

from __future__ import annotations

import streamlit as st

APP_TITLE = "재난 대피소 추천 워크스페이스"
APP_ICON = "🛟"

# 페이지 메타데이터는 홈 안내 문구와 각 페이지의 제목 규칙을 동시에 맞추는 기준표다.
# label 은 사용자에게 보이는 제목이고, summary 는 홈/문서에서 페이지 역할을 짧게 설명할 때 재사용된다.
PAGE_META = {
    "home": {
        "label": "재난 대피소 추천 프로젝트 홈",
        "summary": "프로젝트 목적, 현재 데이터 범위, 페이지 읽는 순서를 안내하는 시작 화면",
    },
    "about": {
        "label": "1 About",
        "summary": "현재 프로젝트가 무엇을 풀고 있는지와 데이터 한계를 소개하는 페이지",
    },
    "recommendation": {
        "label": "2 대피소 추천",
        "summary": "전처리된 특보와 대피소 데이터를 이용해 Top 3 대피소를 추천하는 핵심 페이지",
    },
    "flow": {
        "label": "3 작동 설명",
        "summary": "대피소 추천이 어떤 순서로 계산되는지 흐름과 데이터 계약을 설명하는 페이지",
    },
    "realtime": {
        "label": "4 실시간 준비",
        "summary": "향후 자동 위치, 실시간 특보, 경로 API를 어디에 붙일지 정리한 준비 페이지",
    },
    "projects": {
        "label": "5 Projects",
        "summary": "현재 저장소 안에서 진행 중인 구현 작업과 역할을 기록하는 페이지",
    },
    "analysis": {
        "label": "6 Data Analysis",
        "summary": "과거 재난 특보와 대피소 분포를 분석 관점으로 보는 보조 페이지",
    },
    "learning": {
        "label": "7 Learning Log",
        "summary": "현재 구조에서 무엇을 배우고 어떤 순서로 확장할지 정리한 페이지",
    },
}


def apply_page_config(page_key: str) -> None:
    """주어진 페이지 키에 맞는 Streamlit 기본 설정을 적용한다.

    페이지 파일 안에서 ``st.set_page_config`` 를 직접 반복하지 않고
    여기서 한 번에 관리하면 제목 형식과 레이아웃 기준이 항상 같게 유지된다.
    """

    # page_key 로 직접 텍스트를 조합하지 않고 PAGE_META 를 거치는 이유는
    # 한 번 정한 번호 체계와 페이지 요약을 앱 전체에서 같은 기준으로 쓰기 위해서다.
    page = PAGE_META[page_key]
    st.set_page_config(
        page_title=f"{APP_TITLE} | {page['label']}",
        page_icon=APP_ICON,
        # wide 레이아웃을 고정하는 이유는 추천 카드, 지도, 분석 차트가 한 줄에 함께 보이도록 하기 위해서다.
        layout="wide",
        initial_sidebar_state="expanded",
    )
