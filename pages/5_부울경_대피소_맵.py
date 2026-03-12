from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from app import APP_ICON, APP_TITLE

PAGE_LABEL = "부울경 대피소 맵"
MAP_FILE = Path(__file__).resolve().parents[1] / "preprocessing_code" / "shelter_type_layer_map1.html"
DEFAULT_MAP_HEIGHT = 760


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
    st.set_page_config(
        page_title=f"{APP_TITLE} | {PAGE_LABEL}",
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("5. 부산·울산·경남 대피소 맵")
    st.write("`preprocessing_code/shelter_type_layer_map1.html` 지도를 그대로 붙인 페이지입니다.")
    st.caption("지도를 확대하거나 마커를 눌러 대피소 유형과 위치를 확인할 수 있습니다.")

    if not MAP_FILE.exists():
        st.error(f"지도 HTML 파일을 찾지 못했습니다: {MAP_FILE}")
        st.stop()

    map_height = st.sidebar.slider(
        "지도 높이",
        min_value=500,
        max_value=1200,
        value=DEFAULT_MAP_HEIGHT,
        step=50,
    )
    st.sidebar.caption("마커가 많아서 화면을 크게 두는 편이 보기 쉽습니다.")

    components.html(load_map_html(str(MAP_FILE)), height=map_height, scrolling=True)

    with st.expander("원본 파일 정보", expanded=False):
        st.code(str(MAP_FILE))


if os.environ.get("PROJECT_DASHBOARD_IMPORT_ONLY") != "1":
    render_page()
