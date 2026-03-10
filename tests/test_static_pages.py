"""정적 페이지의 요약 콘텐츠와 docs 연계를 검증하는 테스트."""

from __future__ import annotations

from pathlib import Path

DETAIL_DOC_PATH = Path("docs/04_INTERNAL_FUNCTION_CLEANUP.md")


def test_internal_cleanup_doc_exists_with_expected_sections() -> None:
    assert DETAIL_DOC_PATH.exists()
    document = DETAIL_DOC_PATH.read_text(encoding="utf-8")
    assert "내부 함수 정리 기준" in document
    assert "render_page()" in document
    assert "설명성 페이지 운영 원칙" in document
    assert "`with` 와 지역변수 기준" in document


def test_about_page_trimmed_content_shape(about_page_module) -> None:
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
    assert about_page_module.DETAIL_DOC_PATH == str(DETAIL_DOC_PATH).replace("\\", "/")
    assert not hasattr(about_page_module, "load_alerts_dataframe_uncached")
    assert not hasattr(about_page_module, "build_dataset_catalog")


def test_flow_page_trimmed_content_shape(flow_page_module) -> None:
    assert flow_page_module.FLOW_STEPS
    assert flow_page_module.LIMITATIONS
    assert flow_page_module.DETAIL_DOC_PATH == str(DETAIL_DOC_PATH).replace("\\", "/")
    assert not hasattr(flow_page_module, "load_alerts_dataframe_uncached")
    assert not hasattr(flow_page_module, "build_dataset_catalog")


def test_realtime_page_trimmed_content_shape(realtime_page_module) -> None:
    assert realtime_page_module.REALTIME_EXPANSION_ITEMS
    assert realtime_page_module.DETAIL_DOC_PATH == str(DETAIL_DOC_PATH).replace("\\", "/")
    assert not hasattr(realtime_page_module, "FUTURE_CODE_SNIPPETS")


def test_projects_page_inline_content_shape(projects_page_module) -> None:
    assert projects_page_module.PROJECT_ITEMS
    for item in projects_page_module.PROJECT_ITEMS:
        assert {"title", "status", "summary", "role", "highlights", "next_action"}.issubset(item.keys())


def test_learning_page_inline_content_shape(learning_page_module) -> None:
    assert learning_page_module.LEARNING_TOPICS
    assert learning_page_module.ROADMAP_STEPS
    assert learning_page_module.DETAIL_DOC_PATH == str(DETAIL_DOC_PATH).replace("\\", "/")


def test_app_and_pages_compile_without_writing_bytecode() -> None:
    for path in [Path("app.py"), *Path("pages").glob("*.py")]:
        source = path.read_text(encoding="utf-8")
        compile(source, str(path), "exec")
