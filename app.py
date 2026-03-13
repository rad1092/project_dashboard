from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_TITLE = "실시간 대피 안내 대시보드"
APP_ICON = "🚨"

TEXT_PRIMARY = "#e5eef9"
TEXT_MUTED = "#94a3b8"

PAGE_META = {
    "home": {"label": "HOME", "url_path": ""},
    "simulation": {"label": "대피 안내 시뮬레이션", "url_path": "simulation"},
    "message_guidance": {"label": "실시간 대피 안내", "url_path": "live-guidance"},
    "analysis": {"label": "데이터 분석", "url_path": "analysis"},
    "map": {"label": "권역 대피소 지도", "url_path": "map"},
}

HOME_HEADLINE = "실시간 대피 안내 대시보드"

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
    data_dir = resolve_data_dir(path_override)
    return _prepare_alerts(_read_csv(data_dir / DATASET_FILE_MAP["alerts"]))


@st.cache_data(show_spinner=False)
def load_alerts_dataframe(path_override: str | None = None) -> pd.DataFrame:
    return load_alerts_dataframe_uncached(path_override)


def load_shelters_dataframe_uncached(path_override: str | Path | None = None) -> pd.DataFrame:
    data_dir = resolve_data_dir(path_override)
    return _prepare_shelters(_read_csv(data_dir / DATASET_FILE_MAP["shelters"]))


@st.cache_data(show_spinner=False)
def load_shelters_dataframe(path_override: str | None = None) -> pd.DataFrame:
    return load_shelters_dataframe_uncached(path_override)


def load_earthquake_shelters_dataframe_uncached(
    path_override: str | Path | None = None,
) -> pd.DataFrame:
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
    page_icon: str,
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


def render_page_title(title: str, caption: str = "") -> None:
    st.title(title)
    if caption:
        st.caption(caption)


def render_section_header(title: str, caption: str = "") -> None:
    st.subheader(title)
    if caption:
        st.caption(caption)


def style_plotly_figure(figure: go.Figure) -> go.Figure:
    figure.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(11, 18, 32, 0.24)",
        font=dict(color=TEXT_PRIMARY),
        legend=dict(
            bgcolor="rgba(8, 17, 28, 0.82)",
            bordercolor="rgba(36, 50, 68, 0.95)",
            borderwidth=1,
            font=dict(color=TEXT_PRIMARY),
        ),
        hoverlabel=dict(
            bgcolor="rgba(8, 17, 28, 0.94)",
            bordercolor="rgba(45, 212, 191, 0.28)",
            font=dict(color=TEXT_PRIMARY),
        ),
        margin=dict(t=70, b=30, l=30, r=30),
    )
    figure.update_xaxes(
        gridcolor="rgba(148, 163, 184, 0.16)",
        linecolor="rgba(148, 163, 184, 0.22)",
        zerolinecolor="rgba(148, 163, 184, 0.16)",
        tickfont=dict(color=TEXT_MUTED),
        title_font=dict(color=TEXT_MUTED),
        automargin=True,
    )
    figure.update_yaxes(
        gridcolor="rgba(148, 163, 184, 0.16)",
        linecolor="rgba(148, 163, 184, 0.22)",
        zerolinecolor="rgba(148, 163, 184, 0.16)",
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
        """
        <style>
        .home-hero {
            padding: 2.3rem 2.4rem;
            border-radius: 28px;
            border: 1px solid rgba(56, 189, 248, 0.20);
            background:
                radial-gradient(circle at top left, rgba(20, 184, 166, 0.22), transparent 36%),
                radial-gradient(circle at bottom right, rgba(56, 189, 248, 0.18), transparent 30%),
                linear-gradient(135deg, rgba(15, 23, 42, 0.96), rgba(17, 24, 39, 0.92));
            box-shadow: 0 24px 80px rgba(15, 23, 42, 0.28);
            text-align: center;
        }
        .home-kicker {
            margin: 0 0 0.85rem 0;
            color: #5eead4;
            font-size: 0.88rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            font-weight: 700;
        }
        .home-title {
            margin: 0;
            color: #f8fafc;
            font-size: clamp(2.1rem, 2.8vw, 3.4rem);
            font-weight: 800;
            line-height: 1.08;
        }
        .home-copy {
            margin: 1rem auto 0;
            max-width: 700px;
            color: #cbd5e1;
            font-size: 1.05rem;
            line-height: 1.65;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="home-hero">
            <p class="home-kicker">Disaster Dashboard</p>
            <h1 class="home-title">{HOME_HEADLINE}</h1>
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

    _, center, _ = st.columns([0.8, 4.8, 0.8], gap="large")
    with center:
        _render_home_hero()

    _, metrics_center, _ = st.columns([0.8, 4.8, 0.8], gap="large")
    with metrics_center:
        with st.container(border=True):
            metric_columns = st.columns(3, gap="medium")
            metric_columns[0].metric("전체 대피소", f"{float(total_shelters):,.0f}")
            metric_columns[1].metric("특보 지역", f"{float(kpis['region_count']):,.0f}")
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
        st.Page(
            base_dir / "pages" / "4_권역_대피소_지도.py",
            title=PAGE_META["map"]["label"],
            url_path=PAGE_META["map"]["url_path"],
        ),
    ]


def main() -> None:
    configure_page(page_title=APP_TITLE, page_icon=APP_ICON)
    current_page = st.navigation(build_navigation(), position="sidebar")
    current_page.run()


if __name__ == "__main__" and os.environ.get("PROJECT_DASHBOARD_IMPORT_ONLY") != "1":
    main()
