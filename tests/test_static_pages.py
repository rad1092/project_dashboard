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
    assert "`app.py`" in structure_document
    assert "`pages/1_대피_시뮬레이션.py`" in flow_document
    assert "`pages/2_실시간_대피_안내.py`" in flow_document
    assert "`pages/3_데이터_분석.py`" in flow_document
    assert "`PROJECT_DASHBOARD_IMPORT_ONLY=1`" in test_document


def test_simulation_page_runtime_shape(simulation_page_module) -> None:
    assert simulation_page_module.PAGE_LABEL == "대피 시뮬레이션"
    assert hasattr(simulation_page_module, "render_page")
    assert hasattr(simulation_page_module, "_build_route_bundle")


def test_live_guidance_page_runtime_shape(live_guidance_page_module) -> None:
    assert live_guidance_page_module.PAGE_LABEL == "실시간 대피 안내"
    assert hasattr(live_guidance_page_module, "render_page")


def test_analysis_page_runtime_shape(analysis_page_module) -> None:
    assert analysis_page_module.PAGE_LABEL == "데이터 분석"
    assert hasattr(analysis_page_module, "render_page")


def test_app_and_pages_compile_without_writing_bytecode() -> None:
    for path in [
        Path("app.py"),
        Path("preprocessing_code/mock_disaster_message.py"),
        *Path("pages").glob("*.py"),
    ]:
        source = path.read_text(encoding="utf-8")
        compile(source, str(path), "exec")
