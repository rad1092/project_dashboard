from __future__ import annotations

from contextlib import nullcontext
from html import escape
import importlib.util
import math
import os
import sys
from collections.abc import Callable, Mapping, MutableMapping, Sequence
from datetime import datetime
from pathlib import Path
from textwrap import dedent
from typing import Any

import folium
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

from app import APP_ICON, APP_TITLE, configure_page, render_page_title, render_section_header

try:
    from streamlit_geolocation import streamlit_geolocation
except Exception:  # pragma: no cover - optional dependency fallback
    streamlit_geolocation = None

SHELTER_COLUMNS = ["대피소명", "주소", "대피소유형", "위도", "경도", "시도", "시군구", "지역", "수용인원"]
EARTHQUAKE_COLUMNS = ["대피소명", "주소", "위도", "경도", "수용인원", "시도", "시군구"]
TSUNAMI_COLUMNS = ["대피소명", "주소", "위도", "경도", "수용인원", "지역", "시도", "시군구"]

DATASET_FILE_MAP = {
    "shelters": Path("preprocessing") / "final_shelter_dataset.csv",
    "earthquake_shelters": Path("preprocessing") / "earthquake_shelter_clean_2.csv",
    "tsunami_shelters": Path("preprocessing") / "tsunami_shelter_clean_2.csv",
}

SPECIAL_SHELTER_TYPE_LABELS = {
    "earthquake_shelter_clean_2.csv": "지진대피장소",
    "tsunami_shelter_clean_2.csv": "해일대피장소",
}

CRAWLED_ALERT_COLUMNS = [
    "발표시각",
    "지역",
    "시군구",
    "재난종류",
    "특보등급",
    "내용",
    "발송기관",
    "번호",
]
(
    PUBLISHED_AT_COLUMN,
    REGION_COLUMN,
    SIGUNGU_COLUMN,
    DISASTER_TYPE_COLUMN,
    ALERT_LEVEL_COLUMN,
    CONTENT_COLUMN,
    SENDER_COLUMN,
    NUMBER_COLUMN,
) = CRAWLED_ALERT_COLUMNS
SIGUNGU_NORMALIZED_COLUMN = "시군구정규화"
DISASTER_GROUP_COLUMN = "재난그룹"
ALERT_KEY_COLUMN = "alert_key"
SUPPORTED_CRAWLED_REGIONS = ["대구", "울산", "부산", "경북", "경남"]
COLUMN_ALIASES = {"발표시간": PUBLISHED_AT_COLUMN}

PAGE_LABEL = "실시간 대피 안내"
STATE_PREFIX = "message_guidance"
OSRM_BASE_URL_KEY = "OSRM_BASE_URL"
DEFAULT_OSRM_BASE_URL = "http://router.project-osrm.org"
DEFAULT_OSRM_PROFILE = "foot"
OSRM_ROUTE_TIMEOUT_S = 10.0
MAX_ACTIONABLE_DISTANCE_KM = 3.0
OFFICIAL_GUIDANCE_MESSAGE = (
    "재난문자, 기상청, 지자체 안내 같은 공식 재난 안내를 확인해주세요."
)
TSUNAMI_ETA_WARNING_MESSAGE = "예상 시간은 보행 기준 추정치이며 실제 대피 상황과 다를 수 있습니다."
RANK_COLORS = ["#0f766e", "#1d4ed8", "#f59e0b"]
CARD_TEXT_PRIMARY = "#e5eef9"
CARD_TEXT_MUTED = "#94a3b8"
CARD_DIVIDER = "rgba(148, 163, 184, 0.16)"
CARD_ROW_BACKGROUND = "rgba(148, 163, 184, 0.04)"
SHOWCASE_CARD_SCALE = 0.8
SHOWCASE_CARD_STACK_GAP_REM = 3.70
SHOWCASE_PANEL_HEIGHT_PX = 710
SHOWCASE_MAP_HEIGHT_PX = 610
CRAWLING_MODULE_NAME = "project_dashboard_live_crawling_runtime"
CRAWLING_MODULE_PATH = Path(__file__).resolve().parents[1] / "preprocessing_code" / "crawling.py"
MOCK_DISASTER_MODULE_NAME = "project_dashboard_mock_disaster_message_runtime"
MOCK_DISASTER_MODULE_PATH = (
    Path(__file__).resolve().parents[1] / "preprocessing_code" / "mock_disaster_message.py"
)
DEFAULT_CRAWLING_WAIT_SECONDS = 15
CRAWLED_ALERT_SOURCE_LIVE = "live"
CRAWLED_ALERT_SOURCE_MOCK = "mock"

RECOMMENDATION_RESULT_COLUMNS = [
    "대피소명",
    "주소",
    "대피소유형",
    "위도",
    "경도",
    "시도",
    "시군구",
    "수용인원",
    "수용인원_정렬값",
    "거리_km",
    "추천구분",
    "추천사유",
]

SHELTER_NAME_COLUMN = RECOMMENDATION_RESULT_COLUMNS[0]
SHELTER_ADDRESS_COLUMN = RECOMMENDATION_RESULT_COLUMNS[1]
SHELTER_TYPE_COLUMN = RECOMMENDATION_RESULT_COLUMNS[2]
STRAIGHT_DISTANCE_COLUMN = RECOMMENDATION_RESULT_COLUMNS[9]
RECOMMENDATION_KIND_COLUMN = RECOMMENDATION_RESULT_COLUMNS[10]
RECENT_ALERT_DISPLAY_COLUMNS = [
    PUBLISHED_AT_COLUMN,
    DISASTER_TYPE_COLUMN,
    ALERT_LEVEL_COLUMN,
    SIGUNGU_COLUMN,
]
DISPLAY_RANK_COLUMN = "_display_rank"
ACCENT_COLOR_COLUMN = "_accent_color"


def _escape_card_text(value: str) -> str:
    return escape(value).replace("\n", "<br>")


def _scaled_rem(value: float) -> str:
    return f"{value * SHOWCASE_CARD_SCALE:.2f}rem"


def build_shelter_summary_card_html(
    title: str,
    rows: Sequence[tuple[str, str]],
    *,
    accent_color: str,
    note: str | None = None,
) -> str:
    surface_top = "#fbf7ef"
    surface_bottom = "#efe5d4"
    surface_border = "rgba(120, 105, 84, 0.18)"
    meta_background = "#e7dcc9"
    meta_border = "rgba(120, 105, 84, 0.14)"
    text_primary = "#1f2937"
    text_muted = "#6b6458"
    divider_color = "rgba(120, 105, 84, 0.14)"
    family_value = ""
    meta_rows: list[tuple[str, str]] = []

    for label, value in rows:
        if label == "대피소 계열" and not family_value:
            family_value = str(value).strip()
            continue
        meta_rows.append((label, value))

    meta_blocks: list[str] = []

    for index, (label, value) in enumerate(meta_rows):
        item_style = (
            "display: flex;"
            " align-items: center;"
            f" gap: {_scaled_rem(0.22)};"
            " min-width: 0;"
            f" padding: {_scaled_rem(0.26)} {_scaled_rem(0.5)};"
        )
        if index > 0:
            item_style += f" border-left: 1px solid {meta_border};"
        if label == "주소":
            item_style += " flex: 1 1 auto;"
        else:
            item_style += " flex: 0 0 auto;"

        value_style = (
            f"color: {text_primary};"
            f" font-size: {_scaled_rem(0.82)};"
            " font-weight: 700;"
            " min-width: 0;"
            " overflow: hidden;"
            " text-overflow: ellipsis;"
            " white-space: nowrap;"
        )

        meta_blocks.append(
            dedent(
                f"""\
<div class="pd-shelter-summary-card__meta-item" style="{item_style}">
    <span class="pd-shelter-summary-card__label" style="
        color: {text_muted};
        font-size: {_scaled_rem(0.68)};
        font-weight: 700;
        letter-spacing: -0.01em;
        white-space: nowrap;
        flex-shrink: 0;
    ">{_escape_card_text(label)}</span>
    <span class="pd-shelter-summary-card__value" style="{value_style}">{_escape_card_text(value)}</span>
</div>"""
            ).strip()
        )

    family_block = ""
    if family_value:
        family_block = dedent(
            f"""\
<div class="pd-shelter-summary-card__family" style="
    margin-top: {_scaled_rem(0.26)};
    display: inline-flex;
    align-items: center;
    gap: {_scaled_rem(0.24)};
    min-width: 0;
    max-width: 100%;
    padding: {_scaled_rem(0.18)} {_scaled_rem(0.5)};
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.55);
    border: 1px solid rgba(120, 105, 84, 0.1);
">
    <span style="
        color: {text_muted};
        font-size: {_scaled_rem(0.64)};
        font-weight: 700;
        white-space: nowrap;
        flex-shrink: 0;
    ">대피소 계열</span>
    <span style="
        color: {text_primary};
        font-size: {_scaled_rem(0.72)};
        font-weight: 700;
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    ">{_escape_card_text(family_value)}</span>
</div>"""
        ).strip()

    note_block = ""
    if note:
        note_block = dedent(
            f"""\
<div class="pd-shelter-summary-card__note" style="
    margin-top: {_scaled_rem(0.44)};
    padding-top: {_scaled_rem(0.48)};
    border-top: 1px solid {divider_color};
    color: {text_muted};
    font-size: {_scaled_rem(0.72)};
    line-height: 1.3;
">{_escape_card_text(note)}</div>"""
        ).strip()

    parts = [
        dedent(
            f"""\
<div class="pd-shelter-summary-card" style="
    color: {text_primary};
    margin-bottom: {_scaled_rem(SHOWCASE_CARD_STACK_GAP_REM)};
    padding: {_scaled_rem(0.74)} {_scaled_rem(0.9)};
    border-radius: {_scaled_rem(1.1)};
    border: 1px solid {surface_border};
    background:
        radial-gradient(circle at top right, rgba(255, 255, 255, 0.65), transparent 32%),
        linear-gradient(180deg, {surface_top}, {surface_bottom});
    box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
    overflow: hidden;
">"""
        ).strip(),
        dedent(
            f"""\
<div class="pd-shelter-summary-card__hero" style="
    display: flex;
    gap: {_scaled_rem(0.62)};
    align-items: center;
">
    <div class="pd-shelter-summary-card__accent" style="
        width: {_scaled_rem(2.18)};
        height: {_scaled_rem(2.18)};
        flex-shrink: 0;
        border-radius: 999px;
        background: {accent_color};
        border: 1px solid rgba(255, 255, 255, 0.12);
        box-shadow: 0 0 0 {_scaled_rem(0.2)} rgba(255, 255, 255, 0.03);
    "></div>
    <div style="min-width: 0; flex: 1;">
        <div class="pd-shelter-summary-card__title" style="
            margin: 0;
            color: {accent_color};
            font-size: {_scaled_rem(2.62)};
            font-weight: 800;
            line-height: 1.0;
            letter-spacing: -0.035em;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        ">{_escape_card_text(title)}</div>
        {family_block}
    </div>
</div>"""
        ).strip(),
        dedent(
            f"""\
<div class="pd-shelter-summary-card__meta-bar" style="
    display: flex;
    align-items: center;
    gap: 0;
    min-width: 0;
    margin-top: {_scaled_rem(0.7)};
    padding: {_scaled_rem(0.12)};
    border-radius: {_scaled_rem(0.74)};
    border: 1px solid {meta_border};
    background: {meta_background};
">"""
        ).strip(),
        "\n".join(meta_blocks),
        "</div>",
    ]
    if note_block:
        parts.append(note_block)
    parts.append("</div>")
    return "\n".join(parts)


def render_shelter_summary_card(
    title: str,
    rows: Sequence[tuple[str, str]],
    *,
    accent_color: str,
    note: str | None = None,
) -> None:
    st.markdown(
        build_shelter_summary_card_html(
            title=title,
            rows=rows,
            accent_color=accent_color,
            note=note,
        ),
        unsafe_allow_html=True,
    )


def _get_shelter_info_panel_kwargs() -> dict[str, object]:
    return {"border": False, "height": SHOWCASE_PANEL_HEIGHT_PX}


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
    return Path(__file__).resolve().parents[1] / "preprocessing_data"


def _get_desktop_default_data_dir() -> Path:
    return Path.home() / "Desktop" / "preprocessing_data"


def normalize_sigungu_name(value: str | None) -> str:
    if value is None or pd.isna(value):
        return ""

    text = str(value).strip().replace(" ", "")
    if text.endswith(("시", "군")) and len(text) > 1:
        return text[:-1]
    return text


def _ensure_shelter_derived_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    shelters = dataframe.copy()
    if "시군구정규화" not in shelters.columns and "시군구" in shelters.columns:
        shelters["시군구정규화"] = shelters["시군구"].map(normalize_sigungu_name)
    if "수용인원_정렬값" not in shelters.columns:
        if "수용인원" in shelters.columns:
            shelters["수용인원_정렬값"] = pd.to_numeric(
                shelters["수용인원"],
                errors="coerce",
            ).fillna(0)
        else:
            shelters["수용인원_정렬값"] = 0
    return shelters


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
        "전처리 데이터 폴더를 찾지 못했다.\n"
        "기본 실행은 저장소 내부 `preprocessing_data` 폴더를 사용한다.\n"
        "다음 경로를 차례대로 확인했다:\n"
        f"{searched}\n"
        "다른 위치를 쓰려면 환경변수 `PREPROCESSING_DATA_DIR` 또는 "
        "`.streamlit/secrets.toml` 의 `preprocessing_data_dir` 를 지정해 달라."
    )


def _read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"전처리 데이터 파일이 없다: {path}\n"
            "저장소 기본 데이터(`preprocessing_data/preprocessing/*.csv`)가 모두 있는지 확인하거나 "
            "다른 위치를 쓰려면 `PREPROCESSING_DATA_DIR` 또는 `.streamlit/secrets.toml` 의 "
            "`preprocessing_data_dir` 를 지정해 달라."
        ) from exc


def _validate_columns(dataframe: pd.DataFrame, expected_columns: list[str], label: str) -> None:
    missing_columns = [column for column in expected_columns if column not in dataframe.columns]
    if missing_columns:
        raise ValueError(f"{label} CSV 에 필요한 컬럼이 없다: {missing_columns}")


def _prepare_shelters(dataframe: pd.DataFrame) -> pd.DataFrame:
    _validate_columns(dataframe, SHELTER_COLUMNS, "final_shelter_dataset.csv")

    shelters = dataframe.copy()
    shelters["위도"] = pd.to_numeric(shelters["위도"], errors="coerce")
    shelters["경도"] = pd.to_numeric(shelters["경도"], errors="coerce")
    shelters["수용인원"] = pd.to_numeric(shelters["수용인원"], errors="coerce")
    shelters["시도"] = shelters["시도"].astype(str).str.strip()
    shelters["시군구"] = shelters["시군구"].astype(str).str.strip()
    shelters["시군구정규화"] = shelters["시군구"].map(normalize_sigungu_name)
    shelters["대피소유형"] = shelters["대피소유형"].fillna("미분류").astype(str).str.strip()
    shelters["수용인원_정렬값"] = shelters["수용인원"].fillna(0)
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
    shelters["시도"] = shelters["시도"].astype(str).str.strip()
    shelters["시군구"] = shelters["시군구"].astype(str).str.strip()
    shelters["시군구정규화"] = shelters["시군구"].map(normalize_sigungu_name)

    if "지역" not in shelters.columns:
        shelters["지역"] = shelters["시도"] + " " + shelters["시군구"]
    shelters["지역"] = shelters["지역"].fillna(shelters["시도"] + " " + shelters["시군구"])
    shelters["대피소유형"] = SPECIAL_SHELTER_TYPE_LABELS[label]
    shelters["수용인원_정렬값"] = shelters["수용인원"].fillna(0)
    return shelters.dropna(subset=["위도", "경도"]).reset_index(drop=True)


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


def _build_region_centers(shelters_frame: pd.DataFrame) -> pd.DataFrame:
    shelters_frame = _ensure_shelter_derived_columns(shelters_frame)
    return (
        shelters_frame.groupby(["시도", "시군구", "시군구정규화"], as_index=False)
        .agg(
            중심위도=("위도", "mean"),
            중심경도=("경도", "mean"),
            대피소수=("대피소명", "size"),
        )
        .sort_values(["시도", "시군구"])
        .reset_index(drop=True)
    )


def infer_region_from_coordinates(
    shelters_frame: pd.DataFrame,
    latitude: float,
    longitude: float,
) -> dict[str, object]:
    region_centers = _build_region_centers(shelters_frame)
    if region_centers.empty:
        return {
            "sido": None,
            "sigungu": None,
            "distance_km": None,
            "source": "auto_detected",
        }

    scored = region_centers.copy()
    scored["distance_km"] = scored.apply(
        lambda row: haversine_km(
            latitude,
            longitude,
            float(row["중심위도"]),
            float(row["중심경도"]),
        ),
        axis=1,
    )
    scored = scored.sort_values(["distance_km", "대피소수"], ascending=[True, False]).reset_index(
        drop=True
    )
    nearest = scored.iloc[0]
    return {
        "sido": str(nearest["시도"]),
        "sigungu": str(nearest["시군구"]),
        "distance_km": float(nearest["distance_km"]),
        "source": "auto_detected",
    }


def get_region_center(
    shelters_frame: pd.DataFrame,
    sido: str,
    sigungu: str,
) -> tuple[float | None, float | None]:
    region_centers = _build_region_centers(shelters_frame)
    filtered = region_centers[
        (region_centers["시도"] == sido)
        & (region_centers["시군구정규화"] == normalize_sigungu_name(sigungu))
    ]
    if filtered.empty:
        filtered = region_centers[region_centers["시도"] == sido]
    if filtered.empty:
        return None, None

    return float(filtered["중심위도"].mean()), float(filtered["중심경도"].mean())


def haversine_km(
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> float:
    earth_radius_km = 6371.0
    lat_a = math.radians(latitude_a)
    lon_a = math.radians(longitude_a)
    lat_b = math.radians(latitude_b)
    lon_b = math.radians(longitude_b)

    delta_lat = lat_b - lat_a
    delta_lon = lon_b - lon_a
    haversine_value = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat_a) * math.cos(lat_b) * math.sin(delta_lon / 2) ** 2
    )
    return earth_radius_km * 2 * math.asin(math.sqrt(haversine_value))


def _filter_by_region(dataframe: pd.DataFrame, sido: str, sigungu: str) -> pd.DataFrame:
    normalized_sigungu = normalize_sigungu_name(sigungu)
    local = dataframe[
        (dataframe["시도"] == sido) & (dataframe["시군구정규화"] == normalized_sigungu)
    ]
    if not local.empty:
        return local.copy()

    regional = dataframe[dataframe["시도"] == sido]
    if not regional.empty:
        return regional.copy()

    return dataframe.copy()


def _build_primary_candidates(
    shelters_frame: pd.DataFrame,
    earthquake_shelters_frame: pd.DataFrame,
    tsunami_shelters_frame: pd.DataFrame,
    disaster_group: str,
    sido: str,
    sigungu: str,
) -> tuple[pd.DataFrame, str]:
    if disaster_group == "지진":
        return _filter_by_region(earthquake_shelters_frame, sido, sigungu), "전용 대피소"
    if disaster_group == "해일/쓰나미":
        return _filter_by_region(tsunami_shelters_frame, sido, sigungu), "전용 대피소"
    if disaster_group == "폭염":
        filtered = shelters_frame[shelters_frame["대피소유형"].str.contains("무더위쉼터", na=False)]
        return _filter_by_region(filtered, sido, sigungu), "전용 대피소"
    if disaster_group == "한파":
        filtered = shelters_frame[shelters_frame["대피소유형"].str.contains("한파쉼터", na=False)]
        return _filter_by_region(filtered, sido, sigungu), "전용 대피소"

    return pd.DataFrame(), "기본 대피소"


def _build_fallback_candidates(
    shelters_frame: pd.DataFrame,
    sido: str,
    sigungu: str,
) -> pd.DataFrame:
    return _filter_by_region(shelters_frame, sido, sigungu)


def _score_candidates(
    dataframe: pd.DataFrame,
    latitude: float,
    longitude: float,
    recommendation_type: str,
    disaster_group: str,
    reason_prefix: str,
) -> pd.DataFrame:
    if dataframe.empty:
        return dataframe.copy()

    scored = dataframe.copy()
    scored["거리_km"] = scored.apply(
        lambda row: haversine_km(latitude, longitude, float(row["위도"]), float(row["경도"])),
        axis=1,
    )
    scored["추천구분"] = recommendation_type
    scored["추천사유"] = (
        reason_prefix + disaster_group + " 상황에서 현재 좌표 기준으로 가까운 후보를 우선 정렬했다."
    )
    scored["수용인원_정렬값"] = pd.to_numeric(scored["수용인원_정렬값"], errors="coerce").fillna(0)
    return scored


def _ensure_result_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    ensured = dataframe.copy()
    default_values = {
        "대피소명": "",
        "주소": "",
        "대피소유형": "미분류",
        "위도": pd.NA,
        "경도": pd.NA,
        "시도": "",
        "시군구": "",
        "수용인원": pd.NA,
        "수용인원_정렬값": 0,
        "거리_km": pd.NA,
        "추천구분": "",
        "추천사유": "",
    }

    for column, default_value in default_values.items():
        if column not in ensured.columns:
            ensured[column] = default_value

    return ensured[RECOMMENDATION_RESULT_COLUMNS]


def recommend_shelters(
    shelters_frame: pd.DataFrame,
    earthquake_shelters_frame: pd.DataFrame,
    tsunami_shelters_frame: pd.DataFrame,
    disaster_group: str,
    latitude: float,
    longitude: float,
    sido: str,
    sigungu: str,
    top_n: int = 3,
) -> pd.DataFrame:
    shelters_frame = _ensure_shelter_derived_columns(shelters_frame)
    earthquake_shelters_frame = _ensure_shelter_derived_columns(earthquake_shelters_frame)
    tsunami_shelters_frame = _ensure_shelter_derived_columns(tsunami_shelters_frame)
    primary_candidates, primary_label = _build_primary_candidates(
        shelters_frame=shelters_frame,
        earthquake_shelters_frame=earthquake_shelters_frame,
        tsunami_shelters_frame=tsunami_shelters_frame,
        disaster_group=disaster_group,
        sido=sido,
        sigungu=sigungu,
    )
    scored_frames: list[pd.DataFrame] = []

    if not primary_candidates.empty:
        scored_frames.append(
            _score_candidates(
                dataframe=primary_candidates,
                latitude=latitude,
                longitude=longitude,
                recommendation_type=primary_label,
                disaster_group=disaster_group,
                reason_prefix="재난 그룹에 맞는 전용 후보를 먼저 조회했고, ",
            )
        )

    needs_fallback = disaster_group in {"호우/태풍", "강풍/풍랑", "대설", "건조", "기타"}
    if needs_fallback or len(primary_candidates) < top_n:
        fallback_candidates = _build_fallback_candidates(
            shelters_frame,
            sido=sido,
            sigungu=sigungu,
        )
        fallback_type = "기본 대피소" if needs_fallback and primary_candidates.empty else "대체 대피소"
        scored_frames.append(
            _score_candidates(
                dataframe=fallback_candidates,
                latitude=latitude,
                longitude=longitude,
                recommendation_type=fallback_type,
                disaster_group=disaster_group,
                reason_prefix="전용 후보만으로는 부족하거나 전용 정의가 없어 통합 대피장소를 함께 조회했고, ",
            )
        )

    if not scored_frames:
        return pd.DataFrame(columns=RECOMMENDATION_RESULT_COLUMNS)

    combined = pd.concat(scored_frames, ignore_index=True)
    combined = combined.drop_duplicates(subset=["대피소명", "주소"])

    priority_order = {"전용 대피소": 0, "기본 대피소": 1, "대체 대피소": 2}
    combined["추천우선순위"] = combined["추천구분"].map(priority_order).fillna(9)
    combined = combined.sort_values(
        ["추천우선순위", "거리_km", "수용인원_정렬값"],
        ascending=[True, True, False],
    )
    standardized = _ensure_result_columns(combined)
    return standardized.head(top_n).reset_index(drop=True)


def resolve_crawled_alerts_path(path_override: str | Path | None = None) -> Path:
    if path_override is None:
        return Path(__file__).resolve().parents[1] / "preprocessing_code" / "data" / "disaster_message_realtime.csv"

    candidate = Path(path_override).expanduser().resolve()
    if candidate.is_dir():
        nested_path = candidate / "preprocessing_code" / "data" / "disaster_message_realtime.csv"
        if nested_path.exists():
            return nested_path

        flat_path = candidate / "disaster_message_realtime.csv"
        if flat_path.exists():
            return flat_path

        return nested_path

    return candidate


def map_crawled_disaster_group(disaster_type: str | None) -> str:
    if disaster_type is None:
        return "기타"

    text = str(disaster_type).strip()
    mapping = {
        "호우": "호우/태풍",
        "태풍": "호우/태풍",
        "호우/태풍": "호우/태풍",
        "강풍": "강풍/풍랑",
        "풍랑": "강풍/풍랑",
        "강풍/풍랑": "강풍/풍랑",
        "폭염": "폭염",
        "한파": "한파",
        "대설": "대설",
        "건조": "건조",
        "지진": "지진",
        "해일": "해일/쓰나미",
        "지진해일": "해일/쓰나미",
        "쓰나미": "해일/쓰나미",
        "해일/쓰나미": "해일/쓰나미",
    }
    return mapping.get(text, "기타")


def build_empty_crawled_alerts_dataframe() -> pd.DataFrame:
    alerts = pd.DataFrame({column: pd.Series(dtype="object") for column in CRAWLED_ALERT_COLUMNS})
    alerts[PUBLISHED_AT_COLUMN] = pd.Series(dtype="datetime64[ns]")
    alerts[SIGUNGU_NORMALIZED_COLUMN] = pd.Series(dtype="object")
    alerts[DISASTER_GROUP_COLUMN] = pd.Series(dtype="object")
    alerts[ALERT_KEY_COLUMN] = pd.Series(dtype="object")
    return alerts


def _load_runtime_module(module_name: str, module_path: Path, *, label: str):
    if module_name in sys.modules:
        return sys.modules[module_name]

    if not module_path.exists():
        raise FileNotFoundError(f"{label} 모듈이 없다: {module_path}")

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {module_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return module


def load_crawling_module():
    return _load_runtime_module(
        CRAWLING_MODULE_NAME,
        CRAWLING_MODULE_PATH,
        label="크롤링",
    )


def load_mock_disaster_message_module():
    return _load_runtime_module(
        MOCK_DISASTER_MODULE_NAME,
        MOCK_DISASTER_MODULE_PATH,
        label="모의 재난문자",
    )


def _validate_crawled_columns(dataframe: pd.DataFrame, *, source_name: str) -> None:
    missing_columns = [column for column in CRAWLED_ALERT_COLUMNS if column not in dataframe.columns]
    if missing_columns:
        raise ValueError(f"{source_name} 에 필요한 컬럼이 없다: {missing_columns}")


def _coerce_crawled_alert_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    normalized = dataframe.copy()
    rename_map = {
        source_name: target_name
        for source_name, target_name in COLUMN_ALIASES.items()
        if source_name in normalized.columns and target_name not in normalized.columns
    }
    if rename_map:
        normalized = normalized.rename(columns=rename_map)
    return normalized


def _build_alert_key(row: pd.Series) -> str:
    return "|".join(
        [
            str(row.get(NUMBER_COLUMN, "")).strip(),
            str(row.get(PUBLISHED_AT_COLUMN, "")).strip(),
            str(row.get(REGION_COLUMN, "")).strip(),
            str(row.get(SIGUNGU_COLUMN, "")).strip(),
            str(row.get(CONTENT_COLUMN, "")).strip(),
        ]
    )


def _prepare_crawled_alerts_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    alerts = dataframe[CRAWLED_ALERT_COLUMNS].copy()
    alerts[PUBLISHED_AT_COLUMN] = pd.to_datetime(alerts[PUBLISHED_AT_COLUMN], errors="coerce")
    for column in [
        REGION_COLUMN,
        SIGUNGU_COLUMN,
        DISASTER_TYPE_COLUMN,
        ALERT_LEVEL_COLUMN,
        CONTENT_COLUMN,
        SENDER_COLUMN,
        NUMBER_COLUMN,
    ]:
        alerts[column] = alerts[column].fillna("").astype(str).str.strip()

    alerts[SIGUNGU_NORMALIZED_COLUMN] = alerts[SIGUNGU_COLUMN].map(normalize_sigungu_name)
    alerts[DISASTER_GROUP_COLUMN] = alerts[DISASTER_TYPE_COLUMN].map(map_crawled_disaster_group)
    alerts[ALERT_KEY_COLUMN] = alerts.apply(_build_alert_key, axis=1)
    alerts = alerts.dropna(subset=[PUBLISHED_AT_COLUMN]).sort_values(PUBLISHED_AT_COLUMN).reset_index(drop=True)
    return alerts


def load_crawled_alerts_dataframe_uncached(path_override: str | Path | None = None) -> pd.DataFrame:
    path = resolve_crawled_alerts_path(path_override)
    try:
        dataframe = pd.read_csv(path, encoding="utf-8-sig")
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"크롤링 재난문자 CSV가 없다: {path}") from exc

    normalized = _coerce_crawled_alert_columns(dataframe)
    _validate_crawled_columns(normalized, source_name="disaster_message_realtime.csv")
    return _prepare_crawled_alerts_dataframe(normalized)


def load_live_crawled_alerts_dataframe_uncached(*, headless: bool = True) -> pd.DataFrame:
    crawling_module = load_crawling_module()
    options = crawling_module.Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1600,1200")

    driver = None
    try:
        driver = crawling_module.webdriver.Chrome(options=options)
        wait = crawling_module.WebDriverWait(driver, DEFAULT_CRAWLING_WAIT_SECONDS)
        driver.get(crawling_module.BASE_URL)
        dataframe = crawling_module.crawl_one_page(driver, wait)
    except Exception as exc:
        raise RuntimeError(f"실시간 재난문자 크롤링 실행 실패: {exc}") from exc
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass

    if not isinstance(dataframe, pd.DataFrame):
        raise RuntimeError("실시간 재난문자 크롤링 결과가 DataFrame이 아니다.")

    normalized = _coerce_crawled_alert_columns(dataframe)
    _validate_crawled_columns(normalized, source_name="preprocessing_code/crawling.py 결과")
    return _prepare_crawled_alerts_dataframe(normalized)


def load_mock_crawled_alerts_dataframe_uncached(
    *,
    sido: str,
    sigungu: str,
    output_path: str | Path | None = None,
) -> pd.DataFrame:
    mock_module = load_mock_disaster_message_module()
    resolved_output_path = output_path if output_path is not None else mock_module.DEFAULT_OUTPUT_PATH
    mock_module.write_mock_disaster_message_csv(
        sido=sido,
        sigungu=sigungu,
        output_path=resolved_output_path,
    )
    return load_crawled_alerts_dataframe_uncached(resolved_output_path)


def get_recent_crawled_alerts(
    dataframe: pd.DataFrame,
    sido: str,
    sigungu: str | None = None,
    limit: int = 5,
) -> pd.DataFrame:
    filtered = dataframe[dataframe[REGION_COLUMN] == sido]
    if sigungu:
        filtered = filtered[filtered[SIGUNGU_NORMALIZED_COLUMN] == normalize_sigungu_name(sigungu)]
        if filtered.empty:
            filtered = dataframe[dataframe[REGION_COLUMN] == sido]

    return filtered.sort_values(PUBLISHED_AT_COLUMN, ascending=False).head(limit).reset_index(drop=True)


def select_default_crawled_alert(
    dataframe: pd.DataFrame,
    sido: str,
    sigungu: str | None = None,
) -> dict[str, object] | None:
    recent_alerts = get_recent_crawled_alerts(dataframe, sido=sido, sigungu=sigungu, limit=1)
    if recent_alerts.empty:
        return None

    return recent_alerts.iloc[0].to_dict()


def _state_key(name: str) -> str:
    return f"{STATE_PREFIX}_{name}"


def _session_key(prefix: str, name: str) -> str:
    return f"{prefix}_{name}"


def format_crawled_alert_source_label(source: object) -> str:
    if str(source or "") == CRAWLED_ALERT_SOURCE_MOCK:
        return "모의"
    return "실시간"


def format_published_at_label(value: object) -> str:
    if value is None or pd.isna(value):
        return "-"
    timestamp = pd.Timestamp(value)
    if pd.isna(timestamp):
        return "-"
    return timestamp.strftime("%Y-%m-%d %H:%M")


def build_current_alert_summary(
    selected_alert: Mapping[str, object] | None,
    *,
    source: str,
) -> dict[str, str] | None:
    if selected_alert is None:
        return None

    region = str(selected_alert.get(REGION_COLUMN) or "").strip()
    sigungu = str(selected_alert.get(SIGUNGU_COLUMN) or "").strip()
    location_label = " ".join(part for part in [region, sigungu] if part).strip() or "-"
    source_label = format_crawled_alert_source_label(source)
    source_note = (
        "현재 화면은 모의 재난문자 기준으로 실행 중입니다."
        if source == CRAWLED_ALERT_SOURCE_MOCK
        else "현재 화면은 실시간 재난문자 기준으로 실행 중입니다."
    )
    return {
        "published_at": format_published_at_label(selected_alert.get(PUBLISHED_AT_COLUMN)),
        "disaster_type": str(selected_alert.get(DISASTER_TYPE_COLUMN) or "-"),
        "alert_level": str(selected_alert.get(ALERT_LEVEL_COLUMN) or "-"),
        "location": location_label,
        "sender": str(selected_alert.get(SENDER_COLUMN) or "-"),
        "content": str(selected_alert.get(CONTENT_COLUMN) or "-"),
        "source_label": source_label,
        "source_note": source_note,
    }


def build_current_alert_summary_card_html(summary: Mapping[str, str]) -> str:
    strip_items = [
        ("재난", f"{summary['disaster_type']} / {summary['alert_level']}"),
        ("적용 지역", summary["location"]),
        ("발표시각", summary["published_at"]),
        ("발송기관", summary["sender"]),
    ]
    item_blocks = "\n".join(
        dedent(
            f"""\
<div class="pd-current-alert-strip__item" style="
    display: inline-flex;
    align-items: center;
    gap: 0.38rem;
    min-width: 0;
    padding: 0.42rem 0.74rem;
    border-radius: 999px;
    border: 1px solid rgba(59, 130, 246, 0.14);
    background: rgba(15, 23, 42, 0.62);
">
    <span style="
        color: {CARD_TEXT_MUTED};
        font-size: 0.76rem;
        font-weight: 700;
        letter-spacing: -0.01em;
        white-space: nowrap;
    ">{_escape_card_text(label)}</span>
    <span style="
        color: {CARD_TEXT_PRIMARY};
        font-size: 0.9rem;
        font-weight: 700;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    ">{_escape_card_text(value)}</span>
</div>"""
        ).strip()
        for label, value in strip_items
    )
    return dedent(
        f"""\
<style>
@media (max-width: 900px) {{
    .pd-current-alert-strip {{
        flex-wrap: wrap !important;
        align-items: stretch !important;
    }}
    .pd-current-alert-strip__content {{
        flex-basis: 100% !important;
        max-width: 100% !important;
    }}
}}
</style>
<div class="pd-current-alert-strip" style="
    display: flex;
    flex-wrap: nowrap;
    align-items: center;
    gap: 0.65rem;
    min-width: 0;
    overflow: hidden;
    margin-top: 0.9rem;
    padding: 0.9rem 1rem;
    border-radius: 1rem;
    border: 1px solid rgba(56, 189, 248, 0.18);
    background:
        radial-gradient(circle at top right, rgba(20, 184, 166, 0.14), transparent 28%),
        linear-gradient(180deg, rgba(2, 6, 23, 0.96), rgba(15, 23, 42, 0.94));
    box-shadow: 0 14px 34px rgba(2, 6, 23, 0.2);
">
    <div class="pd-current-alert-strip__badge" style="
        flex-shrink: 0;
        padding: 0.42rem 0.78rem;
        border-radius: 999px;
        background: rgba(14, 165, 233, 0.16);
        border: 1px solid rgba(56, 189, 248, 0.24);
        color: #bae6fd;
        font-size: 0.84rem;
        font-weight: 800;
        letter-spacing: -0.01em;
        white-space: nowrap;
    ">{_escape_card_text(summary["source_label"])}</div>
    {item_blocks}
    <div class="pd-current-alert-strip__item pd-current-alert-strip__content" style="
        display: inline-flex;
        align-items: center;
        gap: 0.42rem;
        min-width: 0;
        flex: 1 1 16rem;
        padding: 0.42rem 0.78rem;
        border-radius: 0.92rem;
        border: 1px solid rgba(59, 130, 246, 0.14);
        background: rgba(15, 23, 42, 0.62);
    ">
        <span style="
            color: {CARD_TEXT_MUTED};
            font-size: 0.76rem;
            font-weight: 700;
            letter-spacing: -0.01em;
            white-space: nowrap;
        ">내용</span>
        <span style="
            min-width: 0;
            color: {CARD_TEXT_PRIMARY};
            font-size: 0.9rem;
            font-weight: 600;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        ">{_escape_card_text(summary["content"])}</span>
    </div>
</div>"""
    ).strip()


def build_recent_alert_display_frame(recent_alerts: pd.DataFrame) -> pd.DataFrame:
    if recent_alerts.empty:
        return pd.DataFrame(columns=RECENT_ALERT_DISPLAY_COLUMNS)

    alert_display = recent_alerts.copy()
    alert_display[PUBLISHED_AT_COLUMN] = alert_display[PUBLISHED_AT_COLUMN].map(format_published_at_label)
    return alert_display[RECENT_ALERT_DISPLAY_COLUMNS]


def get_crawled_alert_source(
    *,
    session_state: Mapping[str, object] | None = None,
    prefix: str = STATE_PREFIX,
) -> str:
    state = session_state if session_state is not None else st.session_state
    source = str(state.get(_session_key(prefix, "live_crawled_alerts_source")) or "")
    if source == CRAWLED_ALERT_SOURCE_MOCK:
        return CRAWLED_ALERT_SOURCE_MOCK
    return CRAWLED_ALERT_SOURCE_LIVE


def _get_cached_crawled_alerts(
    *,
    session_state: Mapping[str, object] | None = None,
    prefix: str = STATE_PREFIX,
) -> pd.DataFrame:
    state = session_state if session_state is not None else st.session_state
    cached_alerts = state.get(_session_key(prefix, "live_crawled_alerts"))
    if isinstance(cached_alerts, pd.DataFrame):
        return cached_alerts
    return build_empty_crawled_alerts_dataframe()


def _set_crawled_alerts_state(
    alerts: pd.DataFrame,
    *,
    source: str,
    session_state: MutableMapping[str, object] | None = None,
    prefix: str = STATE_PREFIX,
) -> None:
    state = session_state if session_state is not None else st.session_state
    state[_session_key(prefix, "live_crawled_alerts")] = alerts
    state[_session_key(prefix, "live_crawled_alerts_updated_at")] = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    state[_session_key(prefix, "live_crawled_alerts_source")] = source


def load_prefixed_session_value(
    session_state: MutableMapping[str, object],
    *,
    prefix: str,
    name: str,
    loader: Callable[[], Any],
    force_refresh: bool = False,
) -> Any:
    value_key = f"{prefix}_{name}"
    updated_key = f"{prefix}_{name}_updated_at"
    if force_refresh or value_key not in session_state:
        session_state[value_key] = loader()
        session_state[updated_key] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session_state.setdefault(updated_key, "-")
    return session_state[value_key]


def get_browser_or_manual_coordinates(
    session_state: MutableMapping[str, object],
    *,
    prefix: str,
) -> tuple[float, float] | None:
    latitude = session_state.get(f"{prefix}_lat")
    longitude = session_state.get(f"{prefix}_lon")
    if latitude in (None, "") or longitude in (None, ""):
        return None

    try:
        return float(latitude), float(longitude)
    except (TypeError, ValueError):
        return None


def format_distance_m(distance_m: object) -> str:
    try:
        value = float(distance_m)
    except (TypeError, ValueError):
        return "-"

    if value >= 1000:
        return f"{value / 1000:.2f} km"
    return f"{value:.0f} m"


def format_duration_s(duration_s: object) -> str:
    try:
        value = int(float(duration_s))
    except (TypeError, ValueError):
        return "-"

    minutes, seconds = divmod(value, 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{hours}시간 {minutes}분"
    if minutes > 0:
        return f"{minutes}분"
    return f"{seconds}초"


def evaluate_tsunami_actionability(
    disaster_group: str | None,
    recommendations: pd.DataFrame,
    route_details: list[dict[str, object]],
) -> dict[str, object]:
    result = {
        "is_tsunami": str(disaster_group or "").strip() == "해일/쓰나미",
        "is_actionable": True,
        "decision_distance_km": None,
        "distance_source": None,
        "message": "",
    }
    if not result["is_tsunami"] or recommendations.empty:
        return result

    top_row = recommendations.iloc[0]
    detail_by_key = {
        str(detail.get("destination_key", "")): detail
        for detail in route_details
        if detail.get("destination_key")
    }
    top_detail = detail_by_key.get(str(top_row.get("route_key", "")), {})

    decision_distance_km: float | None = None
    distance_source: str | None = None
    try:
        route_distance_m = top_detail.get("route_distance_m")
        if route_distance_m is not None:
            decision_distance_km = float(route_distance_m) / 1000
            distance_source = "실경로"
    except (TypeError, ValueError):
        decision_distance_km = None

    if decision_distance_km is None:
        try:
            decision_distance_km = float(top_row["거리_km"])
            distance_source = "직선거리"
        except (TypeError, ValueError, KeyError):
            return result

    result["decision_distance_km"] = decision_distance_km
    result["distance_source"] = distance_source
    if decision_distance_km > MAX_ACTIONABLE_DISTANCE_KM:
        result["is_actionable"] = False
        result["message"] = (
            f"현재 위치는 해일/쓰나미 대피 권고 거리 밖일 수 있습니다. "
            f"최단 {distance_source} 기준 {decision_distance_km:.2f} km입니다."
        )
    return result


def format_location_source_label(source: object) -> str:
    source_value = str(source or "")
    if source_value == "browser":
        return "브라우저"
    if source_value == "manual":
        return "수동"
    return "기본값"


def current_timestamp_label() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def apply_browser_location(
    location_payload: object,
    *,
    prefix: str,
    session_state: MutableMapping[str, object] | None = None,
) -> None:
    state = session_state if session_state is not None else st.session_state
    if state.get(f"{prefix}_location_mode") != "auto":
        return

    if not isinstance(location_payload, dict):
        return

    latitude = location_payload.get("latitude")
    longitude = location_payload.get("longitude")
    if latitude in (None, "") or longitude in (None, ""):
        return

    try:
        state[f"{prefix}_lat"] = float(latitude)
        state[f"{prefix}_lon"] = float(longitude)
    except (TypeError, ValueError):
        return

    state[f"{prefix}_location_source"] = "browser"
    state[f"{prefix}_location_updated_at"] = current_timestamp_label()


def mark_manual_location(
    *,
    prefix: str,
    session_state: MutableMapping[str, object] | None = None,
) -> None:
    state = session_state if session_state is not None else st.session_state
    state[f"{prefix}_location_mode"] = "manual"
    state[f"{prefix}_location_source"] = "manual"
    state[f"{prefix}_location_updated_at"] = current_timestamp_label()


def sync_default_coordinates(
    shelters_frame: pd.DataFrame,
    *,
    prefix: str,
    session_state: MutableMapping[str, object] | None = None,
    default_sido: str = "울산",
    default_sigungu: str = "북구",
    fallback_coordinates: tuple[float, float] = (35.633, 129.365),
) -> None:
    state = session_state if session_state is not None else st.session_state
    state.setdefault(f"{prefix}_location_mode", "auto")
    state.setdefault(f"{prefix}_location_source", "fallback")
    state.setdefault(f"{prefix}_location_updated_at", "-")

    if f"{prefix}_lat" in state and f"{prefix}_lon" in state:
        return

    default_latitude, default_longitude = get_region_center(
        shelters_frame,
        default_sido,
        default_sigungu,
    )
    if default_latitude is None or default_longitude is None:
        default_latitude, default_longitude = fallback_coordinates

    state[f"{prefix}_lat"] = float(default_latitude)
    state[f"{prefix}_lon"] = float(default_longitude)
    state[f"{prefix}_location_source"] = "fallback"


def get_osrm_config() -> tuple[str, str]:
    base_url = os.environ.get(OSRM_BASE_URL_KEY, "").strip() or DEFAULT_OSRM_BASE_URL
    return base_url.rstrip("/"), DEFAULT_OSRM_PROFILE


def _normalize_point(value: Mapping[str, object]) -> dict[str, Any]:
    return {
        "x": float(value["x"]),
        "y": float(value["y"]),
        "key": str(value.get("key", "")),
        "name": str(value.get("name", "")),
    }


def _extract_osrm_route_vertices(route: Mapping[str, object]) -> list[tuple[float, float]]:
    geometry = route.get("geometry", {}) if isinstance(route, dict) else {}
    coordinates = geometry.get("coordinates", []) if isinstance(geometry, dict) else []
    if not isinstance(coordinates, list):
        return []

    vertices: list[tuple[float, float]] = []
    for coordinate in coordinates:
        if not isinstance(coordinate, (list, tuple)) or len(coordinate) < 2:
            continue
        try:
            longitude = float(coordinate[0])
            latitude = float(coordinate[1])
        except (TypeError, ValueError):
            continue

        point = (latitude, longitude)
        if not vertices or vertices[-1] != point:
            vertices.append(point)
    return vertices


def _get_osrm_route_detail(
    origin: Mapping[str, object],
    destination: Mapping[str, object],
    base_url: str,
    profile: str,
    timeout: float = OSRM_ROUTE_TIMEOUT_S,
) -> dict[str, object]:
    normalized_origin = _normalize_point(origin)
    normalized_destination = _normalize_point(destination)
    route_path = (
        f"{base_url}/route/v1/{profile}/"
        f"{normalized_origin['x']},{normalized_origin['y']};"
        f"{normalized_destination['x']},{normalized_destination['y']}"
    )
    response = requests.get(
        route_path,
        params={
            "overview": "full",
            "geometries": "geojson",
            "steps": "false",
        },
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()

    if payload.get("code") != "Ok":
        raise ValueError(f"OSRM route response returned code={payload.get('code')!r}.")

    routes = payload.get("routes", [])
    if not isinstance(routes, list) or not routes:
        raise ValueError("OSRM route response does not contain routes.")

    route = routes[0]
    route_vertices = _extract_osrm_route_vertices(route)
    if not route_vertices:
        route_vertices = [
            (float(normalized_origin["y"]), float(normalized_origin["x"])),
            (float(normalized_destination["y"]), float(normalized_destination["x"])),
        ]

    return {
        "destination_key": normalized_destination["key"],
        "route_distance_m": route.get("distance"),
        "route_duration_s": route.get("duration"),
        "route_vertices": route_vertices,
        "source": "osrm",
    }


def _build_straight_line_route_detail(
    origin: Mapping[str, object],
    destination: Mapping[str, object],
    *,
    reason: str = "",
) -> dict[str, object]:
    normalized_origin = _normalize_point(origin)
    normalized_destination = _normalize_point(destination)
    distance_km = haversine_km(
        float(normalized_origin["y"]),
        float(normalized_origin["x"]),
        float(normalized_destination["y"]),
        float(normalized_destination["x"]),
    )
    return {
        "destination_key": normalized_destination["key"],
        "route_distance_m": round(distance_km * 1000, 1),
        "route_duration_s": None,
        "route_vertices": [
            (float(normalized_origin["y"]), float(normalized_origin["x"])),
            (float(normalized_destination["y"]), float(normalized_destination["x"])),
        ],
        "source": "straight_line",
        "warning": reason,
    }


def build_realtime_recommendation_map(
    user_lat: float,
    user_lon: float,
    recommendations: pd.DataFrame,
    route_details: list[dict[str, object]],
) -> folium.Map:
    detail_by_key = {
        str(detail.get("destination_key", "")): detail for detail in route_details if detail.get("destination_key")
    }
    map_object = folium.Map(
        location=[user_lat, user_lon],
        zoom_start=12,
        tiles="OpenStreetMap",
        control_scale=True,
    )
    bounds: list[list[float]] = [[user_lat, user_lon]]

    folium.CircleMarker(
        location=[user_lat, user_lon],
        radius=8,
        color="#dc2626",
        fill=True,
        fill_color="#dc2626",
        fill_opacity=1.0,
        tooltip="현재 위치",
    ).add_to(map_object)

    for index, (_, row) in enumerate(recommendations.iterrows()):
        route_key = str(row.get("route_key", index))
        detail = detail_by_key.get(route_key)
        display_rank = int(row.get(DISPLAY_RANK_COLUMN, index + 1))
        color = str(
            row.get(ACCENT_COLOR_COLUMN) or RANK_COLORS[(display_rank - 1) % len(RANK_COLORS)]
        )
        shelter_latitude = float(row["위도"])
        shelter_longitude = float(row["경도"])
        popup_lines = [
            f"<strong>{row['대피소명']}</strong>",
            f"구분: {row['추천구분']}",
            f"실경로 거리: {format_distance_m(detail.get('route_distance_m') if detail else None)}",
            f"예상 시간: {format_duration_s(detail.get('route_duration_s') if detail else None)}",
        ]
        if detail and detail.get("source") == "straight_line":
            popup_lines.append("OSRM 도보 경로 조회 실패로 직선 fallback 을 표시함")

        folium.CircleMarker(
            location=[shelter_latitude, shelter_longitude],
            radius=6,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.95,
            tooltip=f"Top {display_rank}. {row['대피소명']}",
            popup=folium.Popup("<br>".join(popup_lines), max_width=320),
        ).add_to(map_object)

        vertices = detail.get("route_vertices") if detail else None
        if not isinstance(vertices, list) or not vertices:
            vertices = [(user_lat, user_lon), (shelter_latitude, shelter_longitude)]

        folium.PolyLine(
            locations=vertices,
            color=color,
            weight=4,
            opacity=0.85,
            dash_array="7 7" if detail and detail.get("source") == "straight_line" else None,
            tooltip=f"{row['대피소명']} 경로",
        ).add_to(map_object)

        for vertex_lat, vertex_lon in vertices:
            bounds.append([float(vertex_lat), float(vertex_lon)])
        bounds.append([shelter_latitude, shelter_longitude])

    if len(bounds) > 1:
        map_object.fit_bounds(bounds, padding=(24, 24))

    return map_object


def _prepare_destinations(recommendations: pd.DataFrame) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    prepared = recommendations.head(3).copy().reset_index(drop=True)
    destinations: list[dict[str, object]] = []
    for index, row in prepared.iterrows():
        route_key = f"dest-{index}"
        prepared.at[index, "route_key"] = route_key
        destinations.append(
            {
                "key": route_key,
                "name": str(row["대피소명"]),
                "x": float(row["경도"]),
                "y": float(row["위도"]),
            }
        )
    return prepared, destinations


def _attach_route_sort(
    recommendations: pd.DataFrame,
    route_details: list[dict[str, object]],
) -> pd.DataFrame:
    ordered = recommendations.copy()
    detail_by_key = {
        str(detail.get("destination_key", "")): detail
        for detail in route_details
        if detail.get("destination_key")
    }
    ordered["route_distance_m"] = ordered["route_key"].map(
        lambda key: detail_by_key.get(str(key), {}).get("route_distance_m")
    )
    ordered["route_duration_s"] = ordered["route_key"].map(
        lambda key: detail_by_key.get(str(key), {}).get("route_duration_s")
    )
    ordered["route_priority"] = ordered["route_key"].map(
        lambda key: 0 if detail_by_key.get(str(key), {}).get("source") == "osrm" else 1
    )
    ordered = ordered.sort_values(
        ["route_priority", "route_duration_s", "route_distance_m", "거리_km"],
        ascending=[True, True, True, True],
        na_position="last",
    ).reset_index(drop=True)
    ordered[DISPLAY_RANK_COLUMN] = ordered.index + 1
    ordered[ACCENT_COLOR_COLUMN] = [
        RANK_COLORS[index % len(RANK_COLORS)] for index in range(len(ordered))
    ]
    return ordered.drop(columns=["route_priority"])


def _build_route_bundle(
    recommendations: pd.DataFrame,
    user_latitude: float,
    user_longitude: float,
    osrm_base_url: str | None,
    osrm_profile: str = DEFAULT_OSRM_PROFILE,
) -> tuple[pd.DataFrame, list[dict[str, object]], list[str]]:
    prepared, destinations = _prepare_destinations(recommendations)
    origin = {"x": user_longitude, "y": user_latitude, "key": "origin", "name": "현재 위치"}
    warnings: list[str] = []
    route_details: list[dict[str, object]] = []

    destination_by_key = {destination["key"]: destination for destination in destinations}
    if not osrm_base_url:
        warnings.append("OSRM_BASE_URL 설정이 없어 직선 fallback 경로를 표시합니다.")

    for _, row in prepared.iterrows():
        route_key = str(row["route_key"])
        destination = destination_by_key[route_key]
        if osrm_base_url:
            try:
                detail = _get_osrm_route_detail(origin, destination, osrm_base_url, osrm_profile)
            except Exception as exc:
                warnings.append(f"{row['대피소명']} 도보 경로 조회 실패: {exc}")
                detail = _build_straight_line_route_detail(
                    origin,
                    destination,
                    reason="osrm route lookup failed",
                )
        else:
            detail = _build_straight_line_route_detail(
                origin,
                destination,
                reason="missing osrm base url",
            )

        route_details.append(detail)

    prepared = _attach_route_sort(prepared, route_details)
    return prepared, route_details, warnings


def build_request_id(
    selected_token: str,
    coordinates: tuple[float, float],
    recommendations: pd.DataFrame,
    osrm_base_url: str | None,
    osrm_profile: str,
) -> str:
    latitude, longitude = coordinates
    shelter_tokens = "|".join(
        f"{row['대피소명']}:{row['위도']}:{row['경도']}" for _, row in recommendations.iterrows()
    )
    routing_signature = f"{osrm_profile}:{osrm_base_url or 'straight-line'}"
    return f"{selected_token}|{latitude:.6f}|{longitude:.6f}|{routing_signature}|{shelter_tokens}"


def _mark_manual_location() -> None:
    mark_manual_location(prefix=STATE_PREFIX)


def _sync_default_coordinates(shelters_frame: pd.DataFrame) -> None:
    sync_default_coordinates(shelters_frame, prefix=STATE_PREFIX)


def _apply_browser_location(location_payload: object) -> None:
    apply_browser_location(location_payload, prefix=STATE_PREFIX)


def _get_runtime_crawled_alerts(
    *,
    refresh_requested: bool,
    mock_requested: bool,
    active_sido: str,
    active_sigungu: str,
    session_state: MutableMapping[str, object] | None = None,
    prefix: str = STATE_PREFIX,
    live_loader: Callable[[], pd.DataFrame] = load_live_crawled_alerts_dataframe_uncached,
    mock_loader: Callable[..., pd.DataFrame] = load_mock_crawled_alerts_dataframe_uncached,
) -> tuple[pd.DataFrame, str | None]:
    state = session_state if session_state is not None else st.session_state
    cache_key = _session_key(prefix, "live_crawled_alerts")
    updated_key = _session_key(prefix, "live_crawled_alerts_updated_at")
    source_key = _session_key(prefix, "live_crawled_alerts_source")
    has_cached_alerts = isinstance(state.get(cache_key), pd.DataFrame)

    try:
        if mock_requested:
            if active_sido not in SUPPORTED_CRAWLED_REGIONS:
                state.setdefault(updated_key, "-")
                state.setdefault(source_key, CRAWLED_ALERT_SOURCE_LIVE)
                return (
                    _get_cached_crawled_alerts(session_state=state, prefix=prefix),
                    "모의 재난문자는 지원 권역에서만 생성할 수 있습니다.",
                )

            alerts = mock_loader(sido=active_sido, sigungu=active_sigungu)
            _set_crawled_alerts_state(
                alerts,
                source=CRAWLED_ALERT_SOURCE_MOCK,
                session_state=state,
                prefix=prefix,
            )
            return alerts, None

        if refresh_requested or not has_cached_alerts:
            alerts = live_loader()
            _set_crawled_alerts_state(
                alerts,
                source=CRAWLED_ALERT_SOURCE_LIVE,
                session_state=state,
                prefix=prefix,
            )
            return alerts, None

        state.setdefault(updated_key, "-")
        state.setdefault(source_key, CRAWLED_ALERT_SOURCE_LIVE)
        cached_alerts = state.get(cache_key)
        if isinstance(cached_alerts, pd.DataFrame):
            return cached_alerts, None
        return build_empty_crawled_alerts_dataframe(), None
    except Exception as exc:
        cached_alerts = state.get(cache_key)
        if isinstance(cached_alerts, pd.DataFrame):
            if mock_requested:
                return cached_alerts, f"모의 재난문자 생성은 실패했지만 직전 결과를 유지합니다: {exc}"
            return cached_alerts, f"실시간 크롤링 재시도에 실패해 직전 결과를 유지한다: {exc}"
        if mock_requested:
            return build_empty_crawled_alerts_dataframe(), f"모의 재난문자를 생성하지 못했다: {exc}"
        return build_empty_crawled_alerts_dataframe(), f"실시간 재난문자 크롤링을 실행하지 못했다: {exc}"


def resolve_region_alert_state(
    crawled_alerts: pd.DataFrame,
    active_sido: str,
    active_sigungu: str,
) -> tuple[bool, pd.DataFrame, dict[str, object] | None]:
    if active_sido not in SUPPORTED_CRAWLED_REGIONS:
        return False, pd.DataFrame(columns=crawled_alerts.columns), None

    recent_alerts = get_recent_crawled_alerts(crawled_alerts, active_sido, active_sigungu, limit=5)
    default_alert = select_default_crawled_alert(crawled_alerts, active_sido, active_sigungu)
    return True, recent_alerts, default_alert


def _render_live_top3_cards(
    recommendations: pd.DataFrame,
    route_details: list[dict[str, object]],
    *,
    is_tsunami: bool,
) -> None:
    detail_by_key = {
        str(detail.get("destination_key", "")): detail
        for detail in route_details
        if detail.get("destination_key")
    }
    for index, (_, row) in enumerate(recommendations.iterrows()):
        detail = detail_by_key.get(str(row.get("route_key", "")), {})
        eta_label = "참고용" if is_tsunami else format_duration_s(detail.get("route_duration_s"))
        family_label = str(row.get(SHELTER_TYPE_COLUMN) or "").strip() or str(
            row.get(RECOMMENDATION_KIND_COLUMN) or ""
        ).strip()
        accent_color = str(
            row.get(ACCENT_COLOR_COLUMN) or RANK_COLORS[index % len(RANK_COLORS)]
        )
        rows = [
            ("대피소 계열", family_label),
            ("실경로 거리", format_distance_m(detail.get("route_distance_m"))),
            ("주소", str(row[SHELTER_ADDRESS_COLUMN])),
            ("예상 시간", eta_label),
        ]
        note = (
            "OSRM 경로 확인이 안 돼 직선 fallback 결과를 표시 중입니다."
            if detail.get("source") == "straight_line"
            else None
        )
        render_shelter_summary_card(
            str(row[SHELTER_NAME_COLUMN]),
            rows,
            accent_color=accent_color,
            note=note,
        )


def _render_current_alert_summary(
    selected_alert: Mapping[str, object] | None,
    *,
    source: str,
) -> None:
    summary = build_current_alert_summary(selected_alert, source=source)
    if summary is None:
        return
    st.markdown(build_current_alert_summary_card_html(summary), unsafe_allow_html=True)


def _render_live_detail_expander(
    *,
    recent_alerts: pd.DataFrame,
    recommendations: pd.DataFrame,
    route_details: list[dict[str, object]],
    tsunami_policy: dict[str, object],
    tsunami_policy_message: str,
) -> None:
    with st.expander("상세 데이터", expanded=False):
        detail_left, detail_right = st.columns([0.95, 1.05], gap="large")

        with detail_left:
            with st.container(border=True):
                render_section_header("최근 재난문자", "현재 감지 지역 기준 최근 5건입니다.")
                if recent_alerts.empty:
                    st.info("현재 감지 지역의 최근 재난문자 이력이 없습니다.")
                else:
                    st.dataframe(
                        build_recent_alert_display_frame(recent_alerts),
                        use_container_width=True,
                        hide_index=True,
                    )

        with detail_right:
            with st.container(border=True):
                render_section_header("추천 결과 표")
                if recommendations.empty:
                    st.info("추천 결과가 없습니다.")
                elif tsunami_policy["is_tsunami"] and not tsunami_policy["is_actionable"]:
                    st.warning(tsunami_policy_message)
                    st.info(OFFICIAL_GUIDANCE_MESSAGE)
                else:
                    detail_by_key = {
                        str(detail.get("destination_key", "")): detail
                        for detail in route_details
                        if detail.get("destination_key")
                    }
                    display_frame = recommendations.copy()
                    display_frame["실경로 거리"] = display_frame["route_key"].map(
                        lambda key: format_distance_m(
                            detail_by_key.get(str(key), {}).get("route_distance_m")
                        )
                    )
                    display_frame["직선 거리"] = display_frame[STRAIGHT_DISTANCE_COLUMN].map(
                        lambda value: f"{float(value):.2f} km"
                    )
                    columns = [
                        SHELTER_NAME_COLUMN,
                        RECOMMENDATION_KIND_COLUMN,
                        SHELTER_TYPE_COLUMN,
                        "실경로 거리",
                        "직선 거리",
                        SHELTER_ADDRESS_COLUMN,
                    ]
                    if not tsunami_policy["is_tsunami"]:
                        display_frame["예상 시간"] = display_frame["route_key"].map(
                            lambda key: format_duration_s(
                                detail_by_key.get(str(key), {}).get("route_duration_s")
                            )
                        )
                        columns = [
                            SHELTER_NAME_COLUMN,
                            RECOMMENDATION_KIND_COLUMN,
                            SHELTER_TYPE_COLUMN,
                            "실경로 거리",
                            "예상 시간",
                            "직선 거리",
                            SHELTER_ADDRESS_COLUMN,
                        ]
                    st.dataframe(display_frame[columns], use_container_width=True, hide_index=True)
                    if tsunami_policy["is_tsunami"]:
                        st.info(TSUNAMI_ETA_WARNING_MESSAGE)


def render_page() -> None:
    configure_page(
        page_title=f"{APP_TITLE} | {PAGE_LABEL}",
        page_icon=APP_ICON,
        set_page_config=False,
    )

    render_page_title(PAGE_LABEL)

    try:
        shelters_frame = load_shelters_dataframe()
        earthquake_shelters_frame = load_earthquake_shelters_dataframe()
        tsunami_shelters_frame = load_tsunami_shelters_dataframe()
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.stop()

    shelters_frame = _ensure_shelter_derived_columns(shelters_frame)
    earthquake_shelters_frame = _ensure_shelter_derived_columns(earthquake_shelters_frame)
    tsunami_shelters_frame = _ensure_shelter_derived_columns(tsunami_shelters_frame)

    st.session_state.setdefault(_state_key("last_request_id"), "")
    _sync_default_coordinates(shelters_frame)

    st.sidebar.header("안내 설정")
    browser_location_payload: object | None = None
    refresh_requested = st.sidebar.button("재난문자 새로고침", use_container_width=True)
    mock_requested = st.sidebar.button("모의 재난문자 실행", use_container_width=True)
    crawl_status_placeholder = st.sidebar.empty()

    st.sidebar.markdown("위치 입력 방식")
    st.sidebar.radio(
        "위치 입력 방식",
        options=["auto", "manual"],
        format_func=lambda mode: "자동" if mode == "auto" else "수동",
        key=_state_key("location_mode"),
        horizontal=True,
        label_visibility="collapsed",
    )

    metric_placeholder = st.empty()
    map_body_placeholder = None
    top3_body_placeholder = None
    with st.container():
        map_column, top3_column = st.columns([1.45, 1.05], gap="medium")
        with map_column:
            with st.container(border=True, height=SHOWCASE_PANEL_HEIGHT_PX):
                map_header_column, map_action_column = st.columns(
                    [0.93, 0.07],
                    gap="small",
                    vertical_alignment="center",
                )
                with map_header_column:
                    st.subheader("지도")
                with map_action_column:
                    if streamlit_geolocation is not None:
                        browser_location_payload = streamlit_geolocation()
                st.caption("감지 지역 기준 최신 재난문자 경로를 확인합니다.")
                map_body_placeholder = st.empty()

        with top3_column:
            with st.container(**_get_shelter_info_panel_kwargs()):
                st.subheader("대피소 정보")
                st.caption("추천 대피소 위치와 정보를 확인합니다.")
                top3_body_placeholder = st.empty()
    alert_summary_placeholder = st.empty()

    if st.session_state[_state_key("location_mode")] == "auto":
        if streamlit_geolocation is None:
            st.sidebar.warning(
                "`streamlit-geolocation` 를 불러오지 못해 자동 위치를 받을 수 없습니다. 필요하면 좌표를 직접 입력해 주세요."
            )
        else:
            st.sidebar.caption("브라우저 위치 권한을 허용하면 현재 좌표가 자동으로 반영됩니다.")
            _apply_browser_location(browser_location_payload)
    else:
        st.sidebar.caption("수동 모드에서는 아래 입력한 좌표를 우선합니다.")

    st.sidebar.number_input(
        "위도",
        min_value=30.0,
        max_value=45.0,
        step=0.0001,
        format="%.6f",
        key=_state_key("lat"),
        on_change=_mark_manual_location,
    )
    st.sidebar.number_input(
        "경도",
        min_value=120.0,
        max_value=140.0,
        step=0.0001,
        format="%.6f",
        key=_state_key("lon"),
        on_change=_mark_manual_location,
    )

    coordinates = get_browser_or_manual_coordinates(st.session_state, prefix=STATE_PREFIX)
    if coordinates is None:
        st.warning("현재 좌표를 읽지 못했습니다. 수동 좌표를 입력해 주세요.")
        st.stop()

    selected_latitude, selected_longitude = coordinates
    detected_region = infer_region_from_coordinates(
        shelters_frame,
        latitude=float(selected_latitude),
        longitude=float(selected_longitude),
    )
    active_sido = str(detected_region.get("sido") or "울산")
    active_sigungu = str(detected_region.get("sigungu") or "북구")
    needs_live_reload = refresh_requested or _state_key("live_crawled_alerts") not in st.session_state
    if mock_requested and active_sido in SUPPORTED_CRAWLED_REGIONS:
        alert_load_context = st.spinner("모의 재난문자를 생성하는 중...")
    elif needs_live_reload:
        alert_load_context = st.spinner("실시간 재난문자를 확인하는 중...")
    else:
        alert_load_context = nullcontext()

    with alert_load_context:
        crawled_alerts, crawl_error = _get_runtime_crawled_alerts(
            refresh_requested=refresh_requested,
            mock_requested=mock_requested,
            active_sido=active_sido,
            active_sigungu=active_sigungu,
        )

    crawl_updated_at = str(st.session_state.get(_state_key("live_crawled_alerts_updated_at"), "-"))
    crawl_source = get_crawled_alert_source()
    crawl_status_placeholder.caption(
        f"최근 갱신: {crawl_updated_at} · {format_crawled_alert_source_label(crawl_source)}"
    )
    region_supported, recent_alerts, default_alert = resolve_region_alert_state(
        crawled_alerts,
        active_sido,
        active_sigungu,
    )
    pending_warnings: list[str] = []
    if crawl_error:
        pending_warnings.append(crawl_error)

    selected_alert: dict[str, object] | None = default_alert if region_supported else None

    recommendations = pd.DataFrame(columns=RECOMMENDATION_RESULT_COLUMNS)
    if selected_alert is not None:
        recommendations = recommend_shelters(
            shelters_frame=shelters_frame,
            earthquake_shelters_frame=earthquake_shelters_frame,
            tsunami_shelters_frame=tsunami_shelters_frame,
            disaster_group=str(selected_alert[DISASTER_GROUP_COLUMN]),
            latitude=float(selected_latitude),
            longitude=float(selected_longitude),
            sido=active_sido,
            sigungu=active_sigungu,
            top_n=3,
        )

    osrm_base_url, osrm_profile = get_osrm_config()
    route_details: list[dict[str, object]] = []
    route_warnings: list[str] = []
    map_html = ""
    if selected_alert is not None and not recommendations.empty:
        request_id = build_request_id(
            str(selected_alert[ALERT_KEY_COLUMN]),
            coordinates,
            recommendations,
            osrm_base_url,
            osrm_profile,
        )
        if st.session_state.get(_state_key("last_request_id")) == request_id:
            recommendations = st.session_state.get(_state_key("cached_recommendations"), recommendations)
            route_details = st.session_state.get(_state_key("cached_route_details"), [])
            map_html = str(st.session_state.get(_state_key("cached_map_html"), ""))
            route_warnings = st.session_state.get(_state_key("cached_route_warnings"), [])
        else:
            recommendations, route_details, route_warnings = _build_route_bundle(
                recommendations,
                user_latitude=float(selected_latitude),
                user_longitude=float(selected_longitude),
                osrm_base_url=osrm_base_url,
                osrm_profile=osrm_profile,
            )
            map_html = build_realtime_recommendation_map(
                user_lat=float(selected_latitude),
                user_lon=float(selected_longitude),
                recommendations=recommendations,
                route_details=route_details,
            )._repr_html_()
            st.session_state[_state_key("last_request_id")] = request_id
            st.session_state[_state_key("cached_recommendations")] = recommendations
            st.session_state[_state_key("cached_route_details")] = route_details
            st.session_state[_state_key("cached_map_html")] = map_html
            st.session_state[_state_key("cached_route_warnings")] = route_warnings

    tsunami_policy = evaluate_tsunami_actionability(
        str(selected_alert[DISASTER_GROUP_COLUMN]) if selected_alert is not None else None,
        recommendations,
        route_details,
    )
    tsunami_policy_message = str(tsunami_policy.get("message") or "")

    with metric_placeholder.container():
        current_disaster_label = "-"
        if selected_alert is not None:
            current_disaster_label = (
                f"{selected_alert.get(DISASTER_TYPE_COLUMN, '-')} / "
                f"{selected_alert.get(ALERT_LEVEL_COLUMN, '-')}"
            )
        metric_columns = st.columns(4, gap="medium")
        metric_columns[0].metric(
            "위치 소스",
            format_location_source_label(st.session_state.get(_state_key("location_source"))),
        )
        metric_columns[1].metric("감지 지역", f"{active_sido} {active_sigungu}")
        metric_columns[2].metric("현재 재난", current_disaster_label)
        metric_columns[3].metric("대피소", f"{len(recommendations):.0f}" if selected_alert else "-")

    with map_body_placeholder.container():
        if not region_supported:
            st.info("현재 위치는 재난문자 지원 권역 밖입니다.")
        elif selected_alert is None:
            st.info("현재 감지 지역에 적용할 최신 재난문자가 없습니다.")
        elif recommendations.empty:
            st.info("추천 결과가 없습니다.")
        elif tsunami_policy["is_tsunami"] and not tsunami_policy["is_actionable"]:
            st.warning(tsunami_policy_message)
            st.info(OFFICIAL_GUIDANCE_MESSAGE)
        else:
            components.html(map_html, height=SHOWCASE_MAP_HEIGHT_PX)

    with top3_body_placeholder.container():
        if not region_supported:
            st.info("현재 위치는 재난문자 지원 권역 밖입니다.")
        elif selected_alert is None:
            st.info("현재 감지 지역에 적용할 최신 재난문자가 없습니다.")
        elif recommendations.empty:
            st.info("현재 조건으로 추천할 대피소가 없습니다.")
        elif tsunami_policy["is_tsunami"] and not tsunami_policy["is_actionable"]:
            st.warning(tsunami_policy_message)
            st.info(OFFICIAL_GUIDANCE_MESSAGE)
        else:
            _render_live_top3_cards(
                recommendations,
                route_details,
                is_tsunami=bool(tsunami_policy["is_tsunami"]),
            )
            if tsunami_policy["is_tsunami"]:
                st.info(TSUNAMI_ETA_WARNING_MESSAGE)

    with alert_summary_placeholder.container():
        if region_supported and selected_alert is not None:
            _render_current_alert_summary(selected_alert, source=crawl_source)

    pending_warnings.extend(route_warnings)
    if pending_warnings:
        for warning in dict.fromkeys(pending_warnings):
            st.warning(warning)

    _render_live_detail_expander(
        recent_alerts=recent_alerts,
        recommendations=recommendations,
        route_details=route_details,
        tsunami_policy=tsunami_policy,
        tsunami_policy_message=tsunami_policy_message,
    )


if os.environ.get("PROJECT_DASHBOARD_IMPORT_ONLY") != "1":
    render_page()
