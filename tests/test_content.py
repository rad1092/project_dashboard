"""content 모듈의 기본 데이터 구조를 검증하는 테스트.

페이지 설명 문구와 카드 데이터는 코드보다 먼저 깨질 수 있는 영역이라,
이 테스트는 content.py 의 최소 구조를 보호하는 안전망 역할을 한다.

초보자 메모:
- content.py 는 텍스트 데이터 파일이라 실수로 key 를 하나 지워도 import 는 되지만 페이지는 실행 중 깨질 수 있다.
- 그래서 이 테스트는 화면 렌더링보다 앞단에서 데이터 구조 자체를 확인한다.
"""

from __future__ import annotations

import py_compile
from pathlib import Path

from dashboard.content import ABOUT_DATA, FLOW_STEPS, LEARNING_TOPICS, PROJECT_ITEMS, ROADMAP_STEPS


def test_about_data_has_required_sections() -> None:
    """About 페이지가 기대하는 핵심 키가 모두 있는지 확인한다."""

    # About 페이지는 dict key 를 직접 참조해 렌더링하므로 누락 키가 있으면 실행 중 바로 깨진다.
    required_keys = {
        "name",
        "headline",
        "intro",
        "focus_areas",
        "tech_stack",
        "principles",
        "next_steps",
    }
    # issubset() 은 "왼쪽 집합이 오른쪽 안에 모두 들어 있는가"를 검사하는 Python 집합 메서드다.
    assert required_keys.issubset(ABOUT_DATA.keys())


def test_project_items_have_minimum_shape() -> None:
    """프로젝트 카드가 기대하는 필드 구성을 유지하는지 확인한다."""

    # Python 에서 빈 리스트는 False 처럼 취급되므로, assert PROJECT_ITEMS 는 "비어 있지 않은가"를 간단히 검사하는 방식이다.
    assert PROJECT_ITEMS
    for item in PROJECT_ITEMS:
        # Projects 페이지는 모든 카드가 같은 key 집합을 가진다는 전제 위에서 반복 렌더링한다.
        # highlights 처럼 중첩 리스트가 들어 있는 키도 빠지면 카드 구조가 흔들리므로 같이 본다.
        assert {"title", "status", "summary", "role", "highlights", "next_action"}.issubset(
            item.keys()
        )


def test_learning_topics_flow_steps_and_roadmap_exist() -> None:
    """학습 주제, 작동 설명 단계, 로드맵이 비어 있지 않은지 확인한다."""

    # 비어 있지 않다는 검사는 단순해 보여도, 콘텐츠 파일이 실수로 초기화됐을 때 페이지 공백을 빠르게 잡아 준다.
    assert LEARNING_TOPICS
    assert FLOW_STEPS
    assert ROADMAP_STEPS


def test_page_files_compile() -> None:
    """페이지 번호 변경 이후에도 모든 페이지 파일이 문법적으로 유효한지 확인한다."""

    # 페이지가 import 단계에서라도 깨지면 Streamlit 사이드바 탐색이 바로 중단되므로 문법 검사를 둔다.
    # Path("pages").glob("*.py") 는 pages 폴더 안의 모든 파이썬 파일 경로를 하나씩 돌려주는 패턴이다.
    for page_file in Path("pages").glob("*.py"):
        # py_compile.compile(..., doraise=True) 는 문법 오류가 있으면 예외를 일으켜 테스트 실패로 연결한다.
        py_compile.compile(str(page_file), doraise=True)
