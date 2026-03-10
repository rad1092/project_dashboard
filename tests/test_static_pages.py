"""정적 페이지의 inline 콘텐츠 구조와 문법을 검증하는 테스트."""

from __future__ import annotations

from pathlib import Path


def test_about_page_inline_content_shape(about_page_module) -> None:
    required_keys = {
        "name",
        "headline",
        "intro",
        "focus_areas",
        "tech_stack",
        "principles",
        "next_steps",
    }
    assert required_keys.issubset(about_page_module.ABOUT_DATA.keys())
    assert about_page_module.LIMITATIONS


def test_flow_page_inline_content_shape(flow_page_module) -> None:
    assert flow_page_module.FLOW_STEPS
    assert {"geolocation", "alerts", "routing"}.issubset(flow_page_module.FUTURE_CODE_SNIPPETS.keys())
    assert flow_page_module.LIMITATIONS


def test_realtime_page_inline_content_shape(realtime_page_module) -> None:
    assert realtime_page_module.REALTIME_EXPANSION_ITEMS
    assert {"geolocation", "alerts", "routing"}.issubset(realtime_page_module.FUTURE_CODE_SNIPPETS.keys())


def test_projects_page_inline_content_shape(projects_page_module) -> None:
    assert projects_page_module.PROJECT_ITEMS
    for item in projects_page_module.PROJECT_ITEMS:
        assert {"title", "status", "summary", "role", "highlights", "next_action"}.issubset(item.keys())


def test_learning_page_inline_content_shape(learning_page_module) -> None:
    assert learning_page_module.LEARNING_TOPICS
    assert learning_page_module.ROADMAP_STEPS


def test_app_and_pages_compile_without_writing_bytecode() -> None:
    for path in [Path("app.py"), *Path("pages").glob("*.py")]:
        source = path.read_text(encoding="utf-8")
        compile(source, str(path), "exec")
