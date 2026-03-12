from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from app import APP_ICON, APP_TITLE, configure_page, render_page_title

PAGE_LABEL = "권역 대피소 지도"
MAP_FILE = Path(__file__).resolve().parents[1] / "preprocessing_code" / "shelter_type_layer_map1.html"
DEFAULT_MAP_HEIGHT = 680


@st.cache_data(show_spinner=False)
def load_map_html(path_value: str) -> str:
    path = Path(path_value)
    for encoding in ("utf-8-sig", "utf-8", "cp949"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue

    raise UnicodeDecodeError("unknown", b"", 0, 1, f"Unable to decode {path}")


def render_page() -> None:
    configure_page(
        page_title=f"{APP_TITLE} | {PAGE_LABEL}",
        page_icon=APP_ICON,
        initial_sidebar_state="expanded",
        set_page_config=False,
    )

    if not MAP_FILE.exists():
        st.error(f"지도 HTML 파일을 찾지 못했습니다: {MAP_FILE}")
        st.stop()

    render_page_title(PAGE_LABEL)

    with st.container(border=True):
        components.html(load_map_html(str(MAP_FILE)), height=DEFAULT_MAP_HEIGHT, scrolling=False)


if os.environ.get("PROJECT_DASHBOARD_IMPORT_ONLY") != "1":
    render_page()
