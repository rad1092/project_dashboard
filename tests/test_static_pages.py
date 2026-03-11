from pathlib import Path

STRUCTURE_DOC_PATH = Path("docs/01_프로젝트_구조.md")
FLOW_DOC_PATH = Path("docs/02_데이터_흐름.md")
TEST_DOC_PATH = Path("docs/03_테스트_가이드.md")


def test_docs_exist_with_current_sections() -> None:
    structure_document = STRUCTURE_DOC_PATH.read_text(encoding="utf-8")
    flow_document = FLOW_DOC_PATH.read_text(encoding="utf-8")
    test_document = TEST_DOC_PATH.read_text(encoding="utf-8")

    assert STRUCTURE_DOC_PATH.exists()
    assert FLOW_DOC_PATH.exists()
    assert TEST_DOC_PATH.exists()
    assert "왜 `dashboard_data.py`가 따로 있는가" in structure_document
    assert "`pages/2_실시간_테스트.py`" in flow_document
    assert "`PROJECT_DASHBOARD_IMPORT_ONLY=1`" in test_document


def test_realtime_page_runtime_shape(realtime_page_module) -> None:
    assert realtime_page_module.PAGE_LABEL == "실시간 테스트"
    assert hasattr(realtime_page_module, "render_page")
    assert hasattr(realtime_page_module, "_build_route_bundle")


def test_app_and_pages_compile_without_writing_bytecode() -> None:
    for path in [Path("app.py"), Path("dashboard_data.py"), *Path("pages").glob("*.py")]:
        source = path.read_text(encoding="utf-8")
        compile(source, str(path), "exec")
