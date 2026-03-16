from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_TITLE = "실시간 대피 안내 대시보드"
APP_ICON = "🚨"

BODY_FONT_FAMILY = '"Noto Sans KR", "Pretendard Variable", "Apple SD Gothic Neo", sans-serif'
HEADING_FONT_FAMILY = '"Noto Serif KR", "Cormorant Garamond", "AppleMyungjo", serif'
BACKGROUND_PRIMARY = "#f5efe4"
BACKGROUND_SECONDARY = "#efe5d7"
SURFACE_PRIMARY = "#fffaf2"
SURFACE_SECONDARY = "#f4ecdf"
SURFACE_TERTIARY = "#ece1d1"
TEXT_PRIMARY = "#2d3129"
TEXT_MUTED = "#6f7468"
TEXT_SOFT = "#8b8f84"
ACCENT_PRIMARY = "#2f8f83"
ACCENT_DEEP = "#1f6f68"
ACCENT_SOFT = "rgba(47, 143, 131, 0.14)"
BORDER_SOFT = "rgba(111, 116, 104, 0.16)"
BORDER_ACCENT = "rgba(47, 143, 131, 0.22)"
SHADOW_SOFT = "rgba(93, 78, 55, 0.12)"
PLOT_PANEL_BG = "rgba(239, 230, 217, 0.72)"
PLOT_LEGEND_BG = "rgba(255, 250, 242, 0.96)"

PAGE_META = {
    "home": {"label": "HOME", "url_path": ""},
    "simulation": {"label": "대피 시뮬레이션", "url_path": "simulation"},
    "message_guidance": {"label": "실시간 대피 안내", "url_path": "live-guidance"},
    "analysis": {"label": "데이터 분석", "url_path": "analysis"},
}

HOME_HEADLINE = "실시간 대피 안내 대시보드"
HOME_SUBTITLE = ""

ALERT_COLUMNS = ["발표시간", "지역", "시군구", "재난종류", "특보등급", "해당지역"]
SHELTER_COLUMNS = ["대피소명", "주소", "대피소유형", "위도", "경도", "시도", "시군구", "지역", "수용인원"]
EARTHQUAKE_COLUMNS = ["대피소명", "주소", "위도", "경도", "수용인원", "시도", "시군구"]
TSUNAMI_COLUMNS = ["대피소명", "주소", "위도", "경도", "수용인원", "지역", "시도", "시군구"]
ANALYSIS_COLUMNS = ALERT_COLUMNS.copy()

DATASET_FILE_MAP = {
    "alerts": Path("preprocessing") / "danger_clean.csv",
    "shelters": Path("preprocessing") / "final_shelter_dataset.csv",
    "earthquake_shelters": Path("preprocessing") / "earthquake_shelter_clean_2.csv",
    "tsunami_shelters": Path("preprocessing") / "tsunami_shelter_clean_2.csv",
}

SPECIAL_SHELTER_TYPE_LABELS = {
    "earthquake_shelter_clean_2.csv": "지진대피소",
    "tsunami_shelter_clean_2.csv": "지진해일대피소",
}


def _maybe_get_secret_data_dir() -> str | None:
    try:
        if "preprocessing_data_dir" in st.secrets:
            return str(st.secrets["preprocessing_data_dir"])
        if "app" in st.secrets and "preprocessing_data_dir" in st.secrets["app"]:
            return str(st.secrets["app"]["preprocessing_data_dir"])
    except Exception:
        return None
    return None


def _get_repo_default_data_dir() -> Path:
    return Path(__file__).resolve().parent / "preprocessing_data"


def _get_desktop_default_data_dir() -> Path:
    return Path.home() / "Desktop" / "preprocessing_data"


def resolve_data_dir(path_override: str | Path | None = None) -> Path:
    candidates: list[Path] = []
    if path_override is not None:
        candidates.append(Path(path_override))

    env_path = os.environ.get("PREPROCESSING_DATA_DIR")
    if env_path:
        candidates.append(Path(env_path))

    secret_path = _maybe_get_secret_data_dir()
    if secret_path:
        candidates.append(Path(secret_path))

    candidates.append(_get_repo_default_data_dir())
    candidates.append(_get_desktop_default_data_dir())

    checked_paths: list[Path] = []
    for candidate in candidates:
        resolved = candidate.expanduser().resolve()
        checked_paths.append(resolved)
        if resolved.exists():
            return resolved

    searched = "\n".join(f"- {path}" for path in checked_paths)
    raise FileNotFoundError(
        "전처리 데이터 폴더를 찾지 못했습니다.\n"
        "기본 실행은 프로젝트 루트의 `preprocessing_data` 폴더를 사용합니다.\n"
        "다음 경로를 차례로 확인했습니다:\n"
        f"{searched}\n"
        "다른 위치를 쓰려면 `PREPROCESSING_DATA_DIR` 환경변수 또는 "
        "`.streamlit/secrets.toml`의 `preprocessing_data_dir` 값을 지정하세요."
    )


def _read_csv(path: Path) -> pd.DataFrame:
    decode_error: UnicodeDecodeError | None = None
    for encoding in ("utf-8-sig", "utf-8", "cp949"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                f"전처리 데이터 파일을 찾지 못했습니다: {path}\n"
                "기본 경로는 `preprocessing_data/preprocessing/*.csv` 입니다."
            ) from exc
        except UnicodeDecodeError as exc:
            decode_error = exc

    if decode_error is not None:
        raise decode_error
    raise RuntimeError(f"CSV를 읽을 수 없습니다: {path}")


def _get_repo_default_db_dir() -> Path:
    return Path(__file__).resolve().parent / "preprocessing_code" / "data"


def _find_db_in_directory(directory: Path) -> Path | None:
    if not directory.exists() or not directory.is_dir():
        return None

    preferred_path = directory / "재난대피소.db"
    if preferred_path.exists():
        return preferred_path

    matches = sorted(directory.glob("*.db"))
    if matches:
        return matches[0]
    return None


def resolve_disaster_db_path(path_override: str | Path | None = None) -> Path | None:
    candidate_roots: list[Path] = []
    if path_override is not None:
        candidate_roots.append(Path(path_override))
    else:
        candidate_roots.append(_get_repo_default_db_dir())

    for candidate in candidate_roots:
        resolved = candidate.expanduser().resolve()
        if resolved.is_file() and resolved.suffix.lower() == ".db":
            return resolved

        for directory in (
            resolved / "preprocessing_code" / "data",
            resolved / "data",
            resolved,
        ):
            database_path = _find_db_in_directory(directory)
            if database_path is not None:
                return database_path.resolve()

    return None


def _load_alerts_dataframe_from_db(path_override: str | Path | None = None) -> pd.DataFrame | None:
    database_path = resolve_disaster_db_path(path_override)
    if database_path is None:
        return None

    query = """
        SELECT
            da.발표시간,
            r.시도 AS 지역,
            r.시군구,
            dt.재난이름 AS 재난종류,
            da.특보등급,
            da.해당지역
        FROM danger_alerts AS da
        LEFT JOIN regions AS r ON da.지역_id = r.지역_id
        LEFT JOIN disaster_types AS dt ON da.재난유형_id = dt.재난유형_id
    """
    with sqlite3.connect(database_path) as connection:
        alerts = pd.read_sql_query(query, connection)

    return _prepare_alerts(alerts.loc[:, ALERT_COLUMNS])


def _load_shelters_dataframe_from_db(path_override: str | Path | None = None) -> pd.DataFrame | None:
    database_path = resolve_disaster_db_path(path_override)
    if database_path is None:
        return None

    query = """
        SELECT
            s.대피소명,
            s.주소,
            s.대피소유형,
            s.위도,
            s.경도,
            r.시도,
            r.시군구,
            COALESCE(s.지역설명, r.시도) AS 지역,
            s.수용인원
        FROM shelters AS s
        LEFT JOIN regions AS r ON s.지역_id = r.지역_id
    """
    with sqlite3.connect(database_path) as connection:
        shelters = pd.read_sql_query(query, connection)

    return _prepare_shelters(shelters.loc[:, SHELTER_COLUMNS])


def _load_special_shelters_dataframe_from_db(
    table_name: str,
    expected_columns: list[str],
    label: str,
    path_override: str | Path | None = None,
) -> pd.DataFrame | None:
    database_path = resolve_disaster_db_path(path_override)
    if database_path is None:
        return None

    query = f"""
        SELECT
            s.대피소명,
            s.주소,
            s.위도,
            s.경도,
            COALESCE(sp.수용인원, s.수용인원) AS 수용인원,
            COALESCE(s.지역설명, r.시도) AS 지역,
            r.시도,
            r.시군구
        FROM {table_name} AS sp
        INNER JOIN shelters AS s ON sp.대피소_id = s.대피소_id
        LEFT JOIN regions AS r ON s.지역_id = r.지역_id
    """
    with sqlite3.connect(database_path) as connection:
        shelters = pd.read_sql_query(query, connection)

    return _prepare_special_shelters(shelters.loc[:, expected_columns], expected_columns, label)


def _validate_columns(dataframe: pd.DataFrame, expected_columns: list[str], label: str) -> None:
    missing_columns = [column for column in expected_columns if column not in dataframe.columns]
    if missing_columns:
        raise ValueError(f"{label} 파일에 필요한 컬럼이 없습니다: {missing_columns}")


def _prepare_alerts(dataframe: pd.DataFrame) -> pd.DataFrame:
    _validate_columns(dataframe, ALERT_COLUMNS, "danger_clean.csv")

    alerts = dataframe.copy()
    alerts["발표시간"] = pd.to_datetime(alerts["발표시간"], errors="coerce")
    for column in ["지역", "시군구", "재난종류", "특보등급", "해당지역"]:
        alerts[column] = alerts[column].fillna("").astype(str).str.strip()

    return alerts.dropna(subset=["발표시간"]).sort_values("발표시간").reset_index(drop=True)


def _prepare_shelters(dataframe: pd.DataFrame) -> pd.DataFrame:
    _validate_columns(dataframe, SHELTER_COLUMNS, "final_shelter_dataset.csv")

    shelters = dataframe.copy()
    shelters["위도"] = pd.to_numeric(shelters["위도"], errors="coerce")
    shelters["경도"] = pd.to_numeric(shelters["경도"], errors="coerce")
    shelters["수용인원"] = pd.to_numeric(shelters["수용인원"], errors="coerce")
    for column in ["대피소명", "주소", "대피소유형", "시도", "시군구", "지역"]:
        shelters[column] = shelters[column].fillna("").astype(str).str.strip()

    return shelters.dropna(subset=["위도", "경도"]).reset_index(drop=True)


def _prepare_special_shelters(
    dataframe: pd.DataFrame,
    expected_columns: list[str],
    label: str,
) -> pd.DataFrame:
    _validate_columns(dataframe, expected_columns, label)

    shelters = dataframe.copy()
    shelters["위도"] = pd.to_numeric(shelters["위도"], errors="coerce")
    shelters["경도"] = pd.to_numeric(shelters["경도"], errors="coerce")
    shelters["수용인원"] = pd.to_numeric(shelters["수용인원"], errors="coerce")
    for column in ["대피소명", "주소", "시도", "시군구"]:
        shelters[column] = shelters[column].fillna("").astype(str).str.strip()

    if "지역" not in shelters.columns:
        shelters["지역"] = shelters["시도"]
    shelters["지역"] = shelters["지역"].fillna(shelters["시도"]).astype(str).str.strip()
    shelters["대피소유형"] = SPECIAL_SHELTER_TYPE_LABELS[label]
    return shelters.dropna(subset=["위도", "경도"]).reset_index(drop=True)


def load_alerts_dataframe_uncached(path_override: str | Path | None = None) -> pd.DataFrame:
    db_frame = _load_alerts_dataframe_from_db(path_override)
    if db_frame is not None:
        return db_frame

    data_dir = resolve_data_dir(path_override)
    return _prepare_alerts(_read_csv(data_dir / DATASET_FILE_MAP["alerts"]))


@st.cache_data(show_spinner=False)
def load_alerts_dataframe(path_override: str | None = None) -> pd.DataFrame:
    return load_alerts_dataframe_uncached(path_override)


def load_shelters_dataframe_uncached(path_override: str | Path | None = None) -> pd.DataFrame:
    db_frame = _load_shelters_dataframe_from_db(path_override)
    if db_frame is not None:
        return db_frame

    data_dir = resolve_data_dir(path_override)
    return _prepare_shelters(_read_csv(data_dir / DATASET_FILE_MAP["shelters"]))


@st.cache_data(show_spinner=False)
def load_shelters_dataframe(path_override: str | None = None) -> pd.DataFrame:
    return load_shelters_dataframe_uncached(path_override)


def load_earthquake_shelters_dataframe_uncached(
    path_override: str | Path | None = None,
) -> pd.DataFrame:
    db_frame = _load_special_shelters_dataframe_from_db(
        "earthquake_shelters",
        EARTHQUAKE_COLUMNS,
        "earthquake_shelter_clean_2.csv",
        path_override,
    )
    if db_frame is not None:
        return db_frame

    data_dir = resolve_data_dir(path_override)
    return _prepare_special_shelters(
        _read_csv(data_dir / DATASET_FILE_MAP["earthquake_shelters"]),
        EARTHQUAKE_COLUMNS,
        "earthquake_shelter_clean_2.csv",
    )


@st.cache_data(show_spinner=False)
def load_earthquake_shelters_dataframe(path_override: str | None = None) -> pd.DataFrame:
    return load_earthquake_shelters_dataframe_uncached(path_override)


def load_tsunami_shelters_dataframe_uncached(
    path_override: str | Path | None = None,
) -> pd.DataFrame:
    db_frame = _load_special_shelters_dataframe_from_db(
        "tsunami_shelters",
        TSUNAMI_COLUMNS,
        "tsunami_shelter_clean_2.csv",
        path_override,
    )
    if db_frame is not None:
        return db_frame

    data_dir = resolve_data_dir(path_override)
    return _prepare_special_shelters(
        _read_csv(data_dir / DATASET_FILE_MAP["tsunami_shelters"]),
        TSUNAMI_COLUMNS,
        "tsunami_shelter_clean_2.csv",
    )


@st.cache_data(show_spinner=False)
def load_tsunami_shelters_dataframe(path_override: str | None = None) -> pd.DataFrame:
    return load_tsunami_shelters_dataframe_uncached(path_override)


def load_analysis_dataset(data_dir: str | Path | None = None) -> pd.DataFrame:
    if data_dir is None:
        alerts = load_alerts_dataframe()
    else:
        alerts = load_alerts_dataframe_uncached(data_dir)

    return alerts.loc[:, ANALYSIS_COLUMNS].copy().reset_index(drop=True)


def build_kpis(dataframe: pd.DataFrame) -> dict[str, object]:
    if dataframe.empty:
        return {
            "alert_count": 0,
            "disaster_count": 0,
            "region_count": 0,
            "warning_count": 0,
            "latest_period": None,
        }

    return {
        "alert_count": int(len(dataframe)),
        "disaster_count": int(dataframe["재난종류"].nunique()),
        "region_count": int(dataframe["지역"].nunique()),
        "warning_count": int((dataframe["특보등급"] == "경보").sum()),
        "latest_period": pd.Timestamp(dataframe["발표시간"].max()),
    }


def configure_page(
    page_title: str,
    page_icon: str | None,
    *,
    initial_sidebar_state: str = "expanded",
    set_page_config: bool = True,
) -> None:
    if set_page_config:
        st.set_page_config(
            page_title=page_title,
            page_icon=page_icon,
            layout="wide",
            initial_sidebar_state=initial_sidebar_state,
        )
    inject_global_theme_styles()
    inject_shared_card_styles()


def render_page_title(title: str, caption: str = "") -> None:
    st.title(title)
    if caption:
        st.caption(caption)


def render_section_header(title: str, caption: str = "") -> None:
    st.subheader(title)
    if caption:
        st.caption(caption)


def inject_global_theme_styles() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Noto+Sans+KR:wght@400;500;600;700;800&family=Noto+Serif+KR:wght@500;600;700&display=swap');

        :root {{
            --pd-font-body: {BODY_FONT_FAMILY};
            --pd-font-heading: {HEADING_FONT_FAMILY};
            --pd-bg: {BACKGROUND_PRIMARY};
            --pd-bg-alt: {BACKGROUND_SECONDARY};
            --pd-surface: {SURFACE_PRIMARY};
            --pd-surface-soft: {SURFACE_SECONDARY};
            --pd-surface-muted: {SURFACE_TERTIARY};
            --pd-text: {TEXT_PRIMARY};
            --pd-text-muted: {TEXT_MUTED};
            --pd-text-soft: {TEXT_SOFT};
            --pd-accent: {ACCENT_PRIMARY};
            --pd-accent-deep: {ACCENT_DEEP};
            --pd-accent-soft: {ACCENT_SOFT};
            --pd-border: {BORDER_SOFT};
            --pd-border-accent: {BORDER_ACCENT};
            --pd-shadow: {SHADOW_SOFT};
        }}

        html, body, .stApp {{
            font-family: var(--pd-font-body);
        }}

        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] > .main {{
            background:
                radial-gradient(circle at top left, rgba(47, 143, 131, 0.08), transparent 28%),
                radial-gradient(circle at top right, rgba(212, 183, 137, 0.10), transparent 24%),
                linear-gradient(180deg, var(--pd-bg) 0%, #f2eadc 100%);
            color: var(--pd-text);
        }}

        [data-testid="stHeader"] {{
            background: rgba(245, 239, 228, 0.78);
            border-bottom: 1px solid var(--pd-border);
            backdrop-filter: blur(14px);
        }}

        [data-testid="stMainBlockContainer"] {{
            padding-top: 2.1rem;
        }}

        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #e9dfcf 0%, #efe5d7 100%);
            border-right: 1px solid rgba(111, 116, 104, 0.18);
        }}

        section[data-testid="stSidebar"] > div {{
            background: transparent;
        }}

        section[data-testid="stSidebar"] * {{
            color: var(--pd-text);
        }}

        [data-testid="stIconMaterial"],
        [data-testid="stIconMaterial"] span,
        .material-symbols-rounded,
        .material-symbols-outlined {{
            font-family: "Material Symbols Rounded", "Material Symbols Outlined" !important;
            font-weight: normal !important;
            font-style: normal !important;
        }}

        [data-testid="stSidebarNav"] {{
            background: transparent;
        }}

        [data-testid="stSidebarNav"] a {{
            border-radius: 18px;
            color: var(--pd-text);
            transition: background-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
        }}

        [data-testid="stSidebarNav"] a:hover {{
            background: rgba(255, 250, 242, 0.72);
            box-shadow: inset 0 0 0 1px rgba(47, 143, 131, 0.12);
            transform: translateX(1px);
        }}

        [data-testid="stSidebarNav"] a[aria-current="page"] {{
            background:
                radial-gradient(circle at top left, rgba(47, 143, 131, 0.12), transparent 55%),
                linear-gradient(135deg, rgba(255, 250, 242, 0.95), rgba(244, 236, 223, 0.96));
            box-shadow:
                inset 0 0 0 1px rgba(47, 143, 131, 0.20),
                0 12px 28px rgba(93, 78, 55, 0.08);
        }}

        h1, h2, h3, h4, h5, h6 {{
            color: var(--pd-text);
            font-family: var(--pd-font-heading);
            letter-spacing: -0.02em;
        }}

        h1 {{
            font-weight: 700;
        }}

        h2, h3 {{
            font-weight: 600;
        }}

        p, li, label, span, div[data-testid="stMarkdownContainer"], .stCaption {{
            color: var(--pd-text);
        }}

        div[data-testid="stCaptionContainer"] p,
        .stCaption,
        section[data-testid="stSidebar"] div[data-testid="stCaptionContainer"] p {{
            color: var(--pd-text-muted);
        }}

        div[data-testid="stAlert"] {{
            background: linear-gradient(135deg, rgba(255, 250, 242, 0.95), rgba(244, 236, 223, 0.92));
            border: 1px solid rgba(47, 143, 131, 0.18);
            border-radius: 20px;
            box-shadow: 0 14px 32px rgba(93, 78, 55, 0.08);
        }}

        div[data-testid="stAlert"] * {{
            color: var(--pd-text);
        }}

        .stButton > button,
        section[data-testid="stSidebar"] .stButton > button {{
            border-radius: 16px;
            border: 1px solid var(--pd-border-accent);
            background: linear-gradient(135deg, rgba(240, 252, 249, 0.98), rgba(225, 243, 238, 0.94));
            color: var(--pd-accent-deep);
            font-family: var(--pd-font-body);
            font-weight: 700;
            box-shadow: 0 10px 24px rgba(93, 78, 55, 0.08);
        }}

        .stButton > button:hover,
        section[data-testid="stSidebar"] .stButton > button:hover {{
            border-color: rgba(47, 143, 131, 0.28);
            background: linear-gradient(135deg, rgba(236, 249, 246, 0.98), rgba(218, 239, 234, 0.96));
            color: var(--pd-accent-deep);
        }}

        .stButton > button:focus,
        .stButton > button:focus-visible {{
            box-shadow:
                0 0 0 3px rgba(47, 143, 131, 0.12),
                0 10px 24px rgba(93, 78, 55, 0.08);
        }}

        .stTextInput input,
        .stNumberInput input,
        .stTextArea textarea {{
            color: var(--pd-text);
            font-family: var(--pd-font-body);
        }}

        .stTextInput div[data-baseweb="base-input"] > div,
        .stNumberInput div[data-baseweb="base-input"] > div,
        .stTextArea div[data-baseweb="textarea"] {{
            background: rgba(255, 250, 242, 0.9);
            border: 1px solid var(--pd-border);
            border-radius: 16px;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.65);
        }}

        .stSelectbox div[data-baseweb="select"] > div,
        .stMultiSelect div[data-baseweb="select"] > div {{
            background: rgba(255, 250, 242, 0.9);
            border: 1px solid var(--pd-border);
            border-radius: 16px;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.65);
        }}

        .stSelectbox div[data-baseweb="select"] input,
        .stMultiSelect div[data-baseweb="select"] input {{
            color: var(--pd-text);
        }}

        div[data-baseweb="tag"] {{
            background: rgba(47, 143, 131, 0.12);
            border-radius: 999px;
            border: 1px solid rgba(47, 143, 131, 0.16);
            color: var(--pd-accent-deep);
        }}

        .stRadio [role="radiogroup"] label {{
            background: rgba(255, 250, 242, 0.84);
            border: 1px solid var(--pd-border);
            border-radius: 16px;
            padding: 0.4rem 0.65rem;
        }}

        .stRadio [role="radiogroup"] label:has(input:checked) {{
            background: rgba(47, 143, 131, 0.12);
            border-color: rgba(47, 143, 131, 0.22);
        }}

        button[data-baseweb="tab"] {{
            border-radius: 999px;
            border: 1px solid var(--pd-border);
            background: rgba(255, 250, 242, 0.72);
            color: var(--pd-text-muted);
            font-family: var(--pd-font-body);
            font-weight: 700;
            padding: 0.5rem 1rem;
        }}

        button[data-baseweb="tab"][aria-selected="true"] {{
            background:
                radial-gradient(circle at top left, rgba(47, 143, 131, 0.14), transparent 58%),
                linear-gradient(135deg, rgba(255, 250, 242, 0.96), rgba(241, 248, 245, 0.92));
            border-color: var(--pd-border-accent);
            color: var(--pd-accent-deep);
            box-shadow: 0 10px 24px rgba(93, 78, 55, 0.08);
        }}

        div[data-testid="stExpander"] details {{
            border-radius: 22px;
            border: 1px solid var(--pd-border);
            background: linear-gradient(135deg, rgba(255, 250, 242, 0.95), rgba(244, 236, 223, 0.92));
            box-shadow: 0 16px 36px rgba(93, 78, 55, 0.08);
        }}

        div[data-testid="stExpander"] summary {{
            color: var(--pd-text);
            font-family: var(--pd-font-body);
            font-weight: 700;
        }}

        [data-testid="stDataFrame"],
        [data-testid="stTable"] {{
            border-radius: 20px;
            overflow: hidden;
            border: 1px solid var(--pd-border);
            box-shadow: 0 16px 36px rgba(93, 78, 55, 0.08);
        }}

        [data-testid="stMarkdownContainer"] a {{
            color: var(--pd-accent-deep);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def inject_shared_card_styles() -> None:
    st.markdown(
        f"""
        <style>
        div[data-testid="stMetric"] {{
            padding: 1.15rem 1.2rem;
            border-radius: 24px;
            border: 1px solid {BORDER_ACCENT};
            background:
                radial-gradient(circle at top left, rgba(47, 143, 131, 0.16), transparent 34%),
                radial-gradient(circle at bottom right, rgba(212, 183, 137, 0.16), transparent 30%),
                linear-gradient(135deg, rgba(255, 250, 242, 0.98), rgba(244, 236, 223, 0.94));
            box-shadow: 0 18px 48px {SHADOW_SOFT};
        }}
        div[data-testid="stMetricLabel"] p {{
            color: {TEXT_MUTED};
            font-weight: 600;
            letter-spacing: 0.02em;
        }}
        div[data-testid="stMetricValue"] {{
            color: {TEXT_PRIMARY};
            font-family: {HEADING_FONT_FAMILY};
        }}
        div[data-testid="stMetricValue"] > div {{
            font-size: clamp(1.9rem, 2.15vw, 2.35rem);
            line-height: 1.08;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: 28px;
            border: 1px solid {BORDER_SOFT};
            background:
                radial-gradient(circle at top left, rgba(47, 143, 131, 0.12), transparent 38%),
                radial-gradient(circle at bottom right, rgba(212, 183, 137, 0.12), transparent 34%),
                linear-gradient(135deg, rgba(255, 250, 242, 0.96), rgba(244, 236, 223, 0.92));
            box-shadow: 0 24px 64px rgba(93, 78, 55, 0.12);
            overflow: hidden;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] > div {{
            background: transparent;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] iframe {{
            border-radius: 22px;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stPlotlyChart"] > div,
        div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stDataFrame"] {{
            border-radius: 22px;
            overflow: hidden;
        }}
        div[data-testid="stTabs"] [data-baseweb="tab-panel"] {{
            padding-top: 0.8rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def style_plotly_figure(figure: go.Figure) -> go.Figure:
    figure.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=PLOT_PANEL_BG,
        font=dict(color=TEXT_PRIMARY),
        legend=dict(
            bgcolor=PLOT_LEGEND_BG,
            bordercolor=BORDER_SOFT,
            borderwidth=1,
            font=dict(color=TEXT_PRIMARY),
        ),
        hoverlabel=dict(
            bgcolor=PLOT_LEGEND_BG,
            bordercolor=BORDER_ACCENT,
            font=dict(color=TEXT_PRIMARY),
        ),
        margin=dict(t=70, b=30, l=30, r=30),
    )
    figure.update_xaxes(
        gridcolor="rgba(111, 116, 104, 0.14)",
        linecolor="rgba(111, 116, 104, 0.22)",
        zerolinecolor="rgba(111, 116, 104, 0.14)",
        tickfont=dict(color=TEXT_MUTED),
        title_font=dict(color=TEXT_MUTED),
        automargin=True,
    )
    figure.update_yaxes(
        gridcolor="rgba(111, 116, 104, 0.14)",
        linecolor="rgba(111, 116, 104, 0.22)",
        zerolinecolor="rgba(111, 116, 104, 0.14)",
        tickfont=dict(color=TEXT_MUTED),
        title_font=dict(color=TEXT_MUTED),
        automargin=True,
    )
    return figure


def _format_latest_period(value: object) -> str:
    if value is None or pd.isna(value):
        return "-"
    return pd.Timestamp(value).strftime("%Y-%m-%d %H:%M")


def _render_home_hero() -> None:
    st.markdown(
        f"""
        <style>
        [data-testid="stMainBlockContainer"]:has(.home-page-marker) {{
            max-width: 1280px;
            min-height: calc(100vh - 5rem);
            padding-top: 1rem;
            padding-bottom: 1rem;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}
        [data-testid="stMainBlockContainer"]:has(.home-page-marker) > div {{
            width: 100%;
        }}
        [data-testid="stMainBlockContainer"]:has(.home-page-marker) div[data-testid="stMetric"] {{
            min-height: 8.9rem;
            padding: 1.05rem 1.1rem;
        }}
        [data-testid="stMainBlockContainer"]:has(.home-page-marker) div[data-testid="stMetricLabel"] p {{
            font-size: 0.95rem;
        }}
        [data-testid="stMainBlockContainer"]:has(.home-page-marker) div[data-testid="stMetricValue"] > div {{
            font-size: clamp(1.75rem, 1.95vw, 2.15rem);
        }}
        .home-hero {{
            padding: clamp(2.4rem, 4vw, 3.1rem) clamp(1.7rem, 3vw, 2.8rem);
            border-radius: 32px;
            border: 1px solid {BORDER_ACCENT};
            background:
                radial-gradient(circle at top left, rgba(47, 143, 131, 0.18), transparent 36%),
                radial-gradient(circle at bottom right, rgba(212, 183, 137, 0.16), transparent 30%),
                linear-gradient(135deg, rgba(255, 250, 242, 0.99), rgba(244, 236, 223, 0.94));
            box-shadow: 0 24px 80px rgba(93, 78, 55, 0.12);
            text-align: center;
        }}
        .home-kicker {{
            margin: 0 0 0.7rem 0;
            color: {ACCENT_DEEP};
            font-size: 0.88rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            font-weight: 700;
        }}
        .home-title {{
            margin: 0;
            color: {TEXT_PRIMARY};
            font-size: clamp(2.1rem, 2.8vw, 3.4rem);
            font-weight: 700;
            line-height: 1.08;
            font-family: {HEADING_FONT_FAMILY};
        }}
        .home-copy {{
            margin: 0.85rem auto 0;
            max-width: 760px;
            color: {TEXT_MUTED};
            font-size: 1.05rem;
            line-height: 1.65;
        }}
        @media (max-width: 900px) {{
            [data-testid="stMainBlockContainer"]:has(.home-page-marker) {{
                min-height: auto;
                padding-top: 0.8rem;
                padding-bottom: 0.6rem;
                justify-content: flex-start;
            }}
            [data-testid="stMainBlockContainer"]:has(.home-page-marker) div[data-testid="stMetric"] {{
                min-height: auto;
            }}
            .home-hero {{
                padding: 2rem 1.35rem;
                border-radius: 26px;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="home-page-marker"></div>
        <div class="home-hero">
            <p class="home-kicker">Disaster Dashboard</p>
            <h1 class="home-title">{HOME_HEADLINE}</h1>
            <p class="home-copy">{HOME_SUBTITLE}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_home_page() -> None:
    configure_page(
        page_title=APP_TITLE,
        page_icon=APP_ICON,
        set_page_config=False,
    )

    try:
        shelters_frame = load_shelters_dataframe()
        earthquake_shelters_frame = load_earthquake_shelters_dataframe()
        tsunami_shelters_frame = load_tsunami_shelters_dataframe()
        analysis_frame = load_analysis_dataset()
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.stop()

    kpis = build_kpis(analysis_frame)
    total_shelters = (
        len(shelters_frame) + len(earthquake_shelters_frame) + len(tsunami_shelters_frame)
    )
    latest_period = _format_latest_period(kpis["latest_period"])

    _, center, _ = st.columns([0.45, 6.1, 0.45], gap="small")
    with center:
        _render_home_hero()
        metric_columns = st.columns(3, gap="medium")
        metric_columns[0].metric("전체 대피소", f"{float(total_shelters):,.0f}")
        metric_columns[1].metric("특보 집계 지역 수", f"{float(kpis['region_count']):,.0f}")
        metric_columns[2].metric("최신 특보 시각", latest_period)


def build_navigation() -> list[st.Page]:
    base_dir = Path(__file__).resolve().parent
    return [
        st.Page(
            render_home_page,
            title=PAGE_META["home"]["label"],
            default=True,
            url_path=PAGE_META["home"]["url_path"],
        ),
        st.Page(
            base_dir / "pages" / "1_대피_안내_시뮬레이션.py",
            title=PAGE_META["simulation"]["label"],
            url_path=PAGE_META["simulation"]["url_path"],
        ),
        st.Page(
            base_dir / "pages" / "2_실시간_대피_안내.py",
            title=PAGE_META["message_guidance"]["label"],
            url_path=PAGE_META["message_guidance"]["url_path"],
        ),
        st.Page(
            base_dir / "pages" / "3_데이터_분석.py",
            title=PAGE_META["analysis"]["label"],
            url_path=PAGE_META["analysis"]["url_path"],
        ),
    ]


def main() -> None:
    configure_page(page_title=APP_TITLE, page_icon=APP_ICON)
    current_page = st.navigation(build_navigation(), position="sidebar", expanded=True)
    current_page.run()


if __name__ == "__main__" and os.environ.get("PROJECT_DASHBOARD_IMPORT_ONLY") != "1":
    main()
