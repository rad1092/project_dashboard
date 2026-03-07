"""content 모듈의 기본 데이터 구조를 검증하는 테스트.

이 파일은 About, Projects, Learning Log 페이지가 기대하는 키와 리스트가
실수로 빠지지 않았는지 확인한다.
문구 내용을 세세하게 고정하기보다, 화면이 필요한 최소 구조를 보장하는 것이 목적이다.
"""

from __future__ import annotations

from dashboard.content import LEARNING_TOPICS, PROFILE_DATA, PROJECT_ITEMS, ROADMAP_STEPS


def test_profile_data_has_required_sections() -> None:
    """About 페이지가 필요로 하는 PROFILE_DATA 핵심 키가 모두 있는지 확인한다."""
    required_keys = {
        "name",
        "headline",
        "intro",
        "focus_areas",
        "tech_stack",
        "principles",
        "next_steps",
    }

    assert required_keys.issubset(PROFILE_DATA.keys())


def test_project_items_have_minimum_shape() -> None:
    """Projects 페이지 카드가 기대하는 필드 구성을 모든 항목이 가지는지 확인한다."""
    assert PROJECT_ITEMS
    for item in PROJECT_ITEMS:
        assert {"title", "status", "summary", "role", "highlights", "next_action"}.issubset(
            item.keys()
        )


def test_learning_topics_and_roadmap_exist() -> None:
    """Learning Log 페이지가 렌더링할 주제와 로드맵 데이터가 비어 있지 않은지 확인한다."""
    assert LEARNING_TOPICS
    assert ROADMAP_STEPS