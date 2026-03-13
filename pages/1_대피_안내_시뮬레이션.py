from __future__ import annotations

from html import escape
import math
import os
from collections.abc import Mapping, MutableMapping, Sequence
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

ALERT_COLUMNS = ["발표시간", "지역", "시군구", "재난종류", "특보등급", "해당지역"]
SHELTER_COLUMNS = ["대피소명", "주소", "대피소유형", "위도", "경도", "시도", "시군구", "지역", "수용인원"]
EARTHQUAKE_COLUMNS = ["대피소명", "주소", "위도", "경도", "수용인원", "시도", "시군구"]
TSUNAMI_COLUMNS = ["대피소명", "주소", "위도", "경도", "수용인원", "지역", "시도", "시군구"]

DATASET_FILE_MAP = {
    "alerts": Path("preprocessing") / "danger_clean.csv",
    "shelters": Path("preprocessing") / "final_shelter_dataset.csv",
    "earthquake_shelters": Path("preprocessing") / "earthquake_shelter_clean_2.csv",
    "tsunami_shelters": Path("preprocessing") / "tsunami_shelter_clean_2.csv",
}

SPECIAL_SHELTER_TYPE_LABELS = {
    "earthquake_shelter_clean_2.csv": "지진대피장소",
    "tsunami_shelter_clean_2.csv": "해일대피장소",
}

RAW_TO_GROUP = {
    "지진": "지진",
    "지진해일": "해일/쓰나미",
    "쓰나미": "해일/쓰나미",
    "지진해일/쓰나미": "해일/쓰나미",
    "호우": "호우/태풍",
    "태풍": "호우/태풍",
    "강풍": "강풍/풍랑",
    "풍랑": "강풍/풍랑",
    "폭염": "폭염",
    "한파": "한파",
    "대설": "대설",
    "건조": "건조",
}

DEFAULT_DISASTER_OPTIONS = [
    "호우/태풍",
    "강풍/풍랑",
    "폭염",
    "한파",
    "대설",
    "건조",
    "지진",
    "해일/쓰나미",
]

PAGE_LABEL = "대피 안내 시뮬레이션"
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
SHOWCASE_PANEL_HEIGHT_PX = 710
SHOWCASE_MAP_HEIGHT_PX = 610

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
ALERT_DISPLAY_COLUMNS = ALERT_COLUMNS[:5]


def _escape_card_text(value: str) -> str:
    return escape(value).replace("\n", "<br>")


def _scaled_rem(value: float) -> str:
    return f"{value * SHOWCASE_CARD_SCALE:.2f}rem"


def build_shelter_summary_card_html(
    title: str,
    rows: Sequence[tuple[str, str]],
    note: str | None = None,
) -> str:
    row_blocks: list[str] = []

    for index, (label, value) in enumerate(rows):
        border_style = "none" if index == 0 else f"1px solid {CARD_DIVIDER}"
        row_blocks.append(
            dedent(
                f"""\
<div class="pd-shelter-summary-card__row" style="
    display: grid;
    grid-template-columns: minmax({_scaled_rem(5.75)}, {_scaled_rem(6.75)}) minmax(0, 1fr);
    gap: {_scaled_rem(0.75)};
    align-items: start;
    padding: {_scaled_rem(0.58)} {_scaled_rem(0.15)};
    border-top: {border_style};
    line-height: 1.28;
">
    <div class="pd-shelter-summary-card__label" style="
        color: {CARD_TEXT_MUTED};
        font-size: {_scaled_rem(0.94)};
        font-weight: 600;
        letter-spacing: -0.01em;
        white-space: nowrap;
    ">{_escape_card_text(label)}</div>
    <div class="pd-shelter-summary-card__value" style="
        color: {CARD_TEXT_PRIMARY};
        font-size: {_scaled_rem(1.0)};
        font-weight: 500;
        line-height: 1.28;
        padding: {_scaled_rem(0.02)} {_scaled_rem(0.65)} {_scaled_rem(0.02)} {_scaled_rem(0.02)};
        border-radius: {_scaled_rem(0.6)};
        background: {CARD_ROW_BACKGROUND};
        overflow-wrap: anywhere;
        word-break: keep-all;
    ">{_escape_card_text(value)}</div>
</div>"""
            ).strip()
        )

    note_block = ""
    if note:
        note_block = dedent(
            f"""\
<div class="pd-shelter-summary-card__note" style="
    margin-top: {_scaled_rem(0.45)};
    padding-top: {_scaled_rem(0.7)};
    border-top: 1px solid {CARD_DIVIDER};
    color: {CARD_TEXT_MUTED};
    font-size: {_scaled_rem(0.84)};
    line-height: 1.25;
">{_escape_card_text(note)}</div>"""
        ).strip()

    parts = [
        f'<div class="pd-shelter-summary-card" style="color: {CARD_TEXT_PRIMARY};">',
        dedent(
            f"""\
<div class="pd-shelter-summary-card__title" style="
    margin: 0 0 {_scaled_rem(0.75)} 0;
    color: {CARD_TEXT_PRIMARY};
    font-size: {_scaled_rem(1.9)};
    font-weight: 700;
    line-height: 1.1;
    letter-spacing: -0.02em;
">{_escape_card_text(title)}</div>"""
        ).strip(),
        '<div class="pd-shelter-summary-card__rows" style="display: flex; flex-direction: column;">',
        "\n".join(row_blocks),
        "</div>",
    ]
    if note_block:
        parts.append(note_block)
    parts.append("</div>")
    return "\n".join(parts)


def render_shelter_summary_card(
    title: str,
    rows: Sequence[tuple[str, str]],
    note: str | None = None,
) -> None:
    st.markdown(build_shelter_summary_card_html(title=title, rows=rows, note=note), unsafe_allow_html=True)


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


def _prepare_alerts(dataframe: pd.DataFrame) -> pd.DataFrame:
    _validate_columns(dataframe, ALERT_COLUMNS, "danger_clean.csv")

    alerts = dataframe.copy()
    alerts["발표시간"] = pd.to_datetime(alerts["발표시간"], errors="coerce")
    alerts["지역"] = alerts["지역"].astype(str).str.strip()
    alerts["시군구"] = alerts["시군구"].astype(str).str.strip()
    alerts["시군구정규화"] = alerts["시군구"].map(normalize_sigungu_name)
    alerts["재난종류"] = alerts["재난종류"].astype(str).str.strip()
    alerts["특보등급"] = alerts["특보등급"].fillna("미분류").astype(str).str.strip()
    return alerts.dropna(subset=["발표시간"]).sort_values("발표시간").reset_index(drop=True)


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


def classify_disaster_type(disaster_name: str | None) -> str:
    if disaster_name is None:
        return "기타"

    text = str(disaster_name).strip()
    return RAW_TO_GROUP.get(text, text if text in DEFAULT_DISASTER_OPTIONS else "기타")


def _build_region_centers(shelters_frame: pd.DataFrame) -> pd.DataFrame:
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


def get_recent_alerts(
    alerts_frame: pd.DataFrame,
    sido: str,
    sigungu: str | None = None,
    limit: int = 5,
) -> pd.DataFrame:
    filtered = alerts_frame[alerts_frame["지역"] == sido]
    if sigungu:
        filtered = filtered[filtered["시군구정규화"] == normalize_sigungu_name(sigungu)]
        if filtered.empty:
            filtered = alerts_frame[alerts_frame["지역"] == sido]
    return filtered.sort_values("발표시간", ascending=False).head(limit).reset_index(drop=True)


def build_alert_summary(
    alerts_frame: pd.DataFrame,
    sido: str,
    sigungu: str | None = None,
) -> dict[str, object]:
    recent_alerts = get_recent_alerts(alerts_frame, sido=sido, sigungu=sigungu, limit=5)
    if recent_alerts.empty:
        return {
            "latest_time": None,
            "latest_disaster": None,
            "alert_count": 0,
            "hazards": [],
        }

    return {
        "latest_time": pd.Timestamp(recent_alerts.iloc[0]["발표시간"]),
        "latest_disaster": str(recent_alerts.iloc[0]["재난종류"]),
        "alert_count": int(len(recent_alerts)),
        "hazards": recent_alerts["재난종류"].dropna().astype(str).unique().tolist(),
    }


def get_disaster_options(alerts_frame: pd.DataFrame, sido: str, sigungu: str) -> list[str]:
    recent_alerts = get_recent_alerts(alerts_frame, sido=sido, sigungu=sigungu, limit=10)
    options = [classify_disaster_type(value) for value in recent_alerts["재난종류"].tolist()]
    options.extend(DEFAULT_DISASTER_OPTIONS)

    deduplicated: list[str] = []
    for item in options:
        if item not in deduplicated:
            deduplicated.append(item)
    return deduplicated


def should_compute_recommendations(selected_disaster: str | None) -> bool:
    return selected_disaster is not None and str(selected_disaster).strip() != ""


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


def _state_key(prefix: str, name: str) -> str:
    return f"{prefix}_{name}"


def get_browser_or_manual_coordinates(
    session_state: MutableMapping[str, object],
    *,
    prefix: str = "realtime",
) -> tuple[float, float] | None:
    latitude = session_state.get(_state_key(prefix, "lat"))
    longitude = session_state.get(_state_key(prefix, "lon"))
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


def current_timestamp_label() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def format_location_source_label(source: object) -> str:
    source_value = str(source or "")
    if source_value == "browser":
        return "브라우저"
    if source_value == "manual":
        return "수동"
    return "기본값"


def apply_browser_location(
    location_payload: object,
    *,
    prefix: str = "realtime",
    session_state: MutableMapping[str, object] | None = None,
) -> None:
    state = session_state if session_state is not None else st.session_state
    if state.get(_state_key(prefix, "location_mode")) != "auto":
        return

    if not isinstance(location_payload, dict):
        return

    latitude = location_payload.get("latitude")
    longitude = location_payload.get("longitude")
    if latitude in (None, "") or longitude in (None, ""):
        return

    try:
        state[_state_key(prefix, "lat")] = float(latitude)
        state[_state_key(prefix, "lon")] = float(longitude)
    except (TypeError, ValueError):
        return

    state[_state_key(prefix, "location_source")] = "browser"
    state[_state_key(prefix, "location_updated_at")] = current_timestamp_label()


def mark_manual_location(
    *,
    prefix: str = "realtime",
    session_state: MutableMapping[str, object] | None = None,
) -> None:
    state = session_state if session_state is not None else st.session_state
    state[_state_key(prefix, "location_mode")] = "manual"
    state[_state_key(prefix, "location_source")] = "manual"
    state[_state_key(prefix, "location_updated_at")] = current_timestamp_label()


def sync_default_coordinates(
    shelters_frame: pd.DataFrame,
    *,
    prefix: str = "realtime",
    session_state: MutableMapping[str, object] | None = None,
    default_sido: str = "울산",
    default_sigungu: str = "북구",
    fallback_coordinates: tuple[float, float] = (35.633, 129.365),
) -> None:
    state = session_state if session_state is not None else st.session_state
    state.setdefault(_state_key(prefix, "location_mode"), "auto")
    state.setdefault(_state_key(prefix, "location_source"), "fallback")
    state.setdefault(_state_key(prefix, "location_updated_at"), "-")

    if _state_key(prefix, "lat") in state and _state_key(prefix, "lon") in state:
        return

    default_latitude, default_longitude = get_region_center(
        shelters_frame,
        default_sido,
        default_sigungu,
    )
    if default_latitude is None or default_longitude is None:
        default_latitude, default_longitude = fallback_coordinates

    state[_state_key(prefix, "lat")] = float(default_latitude)
    state[_state_key(prefix, "lon")] = float(default_longitude)
    state[_state_key(prefix, "location_source")] = "fallback"


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
    page2_module=None,
    *,
    reason: str = "",
) -> dict[str, object]:
    normalized_origin = _normalize_point(origin)
    normalized_destination = _normalize_point(destination)
    if page2_module is None:
        page_module = globals()
        haversine_function = page_module["haversine_km"]
    elif isinstance(page2_module, dict):
        haversine_function = page2_module["haversine_km"]
    else:
        haversine_function = page2_module.haversine_km
    distance_km = haversine_function(
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
        color = RANK_COLORS[index % len(RANK_COLORS)]
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
            tooltip=f"Top {index + 1}. {row['대피소명']}",
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
    return ordered.drop(columns=["route_priority"])


def _build_route_bundle(
    recommendations: pd.DataFrame,
    user_latitude: float,
    user_longitude: float,
    osrm_base_url: str | None,
    osrm_profile: str = DEFAULT_OSRM_PROFILE,
    page2_module=None,
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
                    page2_module,
                    reason="osrm route lookup failed",
                )
        else:
            detail = _build_straight_line_route_detail(
                origin,
                destination,
                page2_module,
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


def _apply_browser_location(location_payload: object) -> None:
    apply_browser_location(location_payload, prefix="realtime")


def _mark_manual_location() -> None:
    mark_manual_location(prefix="realtime")


def _sync_default_coordinates(shelters_frame: pd.DataFrame) -> None:
    sync_default_coordinates(shelters_frame, prefix="realtime")


def _render_showcase_top3_cards(
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
    for _, row in recommendations.iterrows():
        detail = detail_by_key.get(str(row.get("route_key", "")), {})
        eta_label = "참고용" if is_tsunami else format_duration_s(detail.get("route_duration_s"))
        rows = [
            ("구분", str(row[RECOMMENDATION_KIND_COLUMN])),
            ("실경로 거리", format_distance_m(detail.get("route_distance_m"))),
            ("예상 시간", eta_label),
            ("직선 거리", f"{float(row[STRAIGHT_DISTANCE_COLUMN]):.2f} km"),
            ("주소", str(row[SHELTER_ADDRESS_COLUMN])),
        ]
        note = (
            "OSRM 경로 확인이 안 돼 직선 fallback 결과를 표시 중입니다."
            if detail.get("source") == "straight_line"
            else None
        )
        with st.container(border=True):
            render_shelter_summary_card(str(row[SHELTER_NAME_COLUMN]), rows, note=note)


def _render_showcase_detail_expander(
    recent_alerts: pd.DataFrame,
    recommendations: pd.DataFrame,
    route_details: list[dict[str, object]],
    *,
    tsunami_policy: dict[str, object],
    tsunami_policy_message: str,
) -> None:
    with st.expander("상세 데이터", expanded=False):
        detail_left, detail_right = st.columns([0.95, 1.05], gap="large")

        with detail_left:
            with st.container(border=True):
                render_section_header("최근 알림", "현재 감지 지역 기준 최근 5건입니다.")
                if recent_alerts.empty:
                    st.info("현재 감지 지역의 최근 알림 이력이 없습니다.")
                else:
                    alert_display = recent_alerts.copy()
                    alert_display[ALERT_COLUMNS[0]] = alert_display[ALERT_COLUMNS[0]].dt.strftime(
                        "%Y-%m-%d %H:%M"
                    )
                    st.dataframe(
                        alert_display[ALERT_DISPLAY_COLUMNS],
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
        alerts_frame = load_alerts_dataframe()
        shelters_frame = load_shelters_dataframe()
        earthquake_shelters_frame = load_earthquake_shelters_dataframe()
        tsunami_shelters_frame = load_tsunami_shelters_dataframe()
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.stop()

    st.session_state.setdefault("realtime_selected_disaster", None)
    st.session_state.setdefault("realtime_last_request_id", "")
    _sync_default_coordinates(shelters_frame)

    st.sidebar.header("안내 설정")
    browser_location_payload: object | None = None
    st.sidebar.markdown("위치 입력 방식")
    st.sidebar.radio(
        "위치 입력 방식",
        options=["auto", "manual"],
        format_func=lambda mode: "자동" if mode == "auto" else "수동",
        key="realtime_location_mode",
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
                st.caption("현재 위치와 대피소 경로를 확인합니다.")
                map_body_placeholder = st.empty()

        with top3_column:
            with st.container(border=True, height=SHOWCASE_PANEL_HEIGHT_PX):
                top3_body_placeholder = st.empty()

    if st.session_state["realtime_location_mode"] == "auto":
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
        key="realtime_lat",
        on_change=_mark_manual_location,
    )
    st.sidebar.number_input(
        "경도",
        min_value=120.0,
        max_value=140.0,
        step=0.0001,
        format="%.6f",
        key="realtime_lon",
        on_change=_mark_manual_location,
    )

    coordinates = get_browser_or_manual_coordinates(st.session_state, prefix="realtime")
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

    disaster_options = get_disaster_options(alerts_frame, active_sido, active_sigungu)
    st.sidebar.selectbox(
        "재난 유형",
        options=disaster_options,
        index=None,
        placeholder="재난 유형 선택",
        key="realtime_selected_disaster",
    )

    selected_disaster = st.session_state.get("realtime_selected_disaster")
    recent_alerts = get_recent_alerts(alerts_frame, active_sido, active_sigungu, limit=5)

    if not should_compute_recommendations(selected_disaster):
        recommendations = pd.DataFrame(columns=RECOMMENDATION_RESULT_COLUMNS)
    else:
        recommendations = recommend_shelters(
            shelters_frame=shelters_frame,
            earthquake_shelters_frame=earthquake_shelters_frame,
            tsunami_shelters_frame=tsunami_shelters_frame,
            disaster_group=str(selected_disaster),
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

    if not recommendations.empty:
        request_id = build_request_id(
            str(selected_disaster),
            coordinates,
            recommendations,
            osrm_base_url,
            osrm_profile,
        )
        if st.session_state.get("realtime_last_request_id") == request_id:
            recommendations = st.session_state.get("realtime_cached_recommendations", recommendations)
            route_details = st.session_state.get("realtime_cached_route_details", [])
            map_html = str(st.session_state.get("realtime_cached_map_html", ""))
            route_warnings = st.session_state.get("realtime_cached_route_warnings", [])
        else:
            recommendations, route_details, route_warnings = _build_route_bundle(
                recommendations,
                user_latitude=float(selected_latitude),
                user_longitude=float(selected_longitude),
                osrm_base_url=osrm_base_url,
                osrm_profile=osrm_profile,
                page2_module=globals(),
            )
            map_html = build_realtime_recommendation_map(
                user_lat=float(selected_latitude),
                user_lon=float(selected_longitude),
                recommendations=recommendations,
                route_details=route_details,
            )._repr_html_()
            st.session_state["realtime_last_request_id"] = request_id
            st.session_state["realtime_cached_recommendations"] = recommendations
            st.session_state["realtime_cached_route_details"] = route_details
            st.session_state["realtime_cached_map_html"] = map_html
            st.session_state["realtime_cached_route_warnings"] = route_warnings

    tsunami_policy = evaluate_tsunami_actionability(
        str(selected_disaster) if selected_disaster else None,
        recommendations,
        route_details,
    )
    show_recommendations = not recommendations.empty and bool(tsunami_policy["is_actionable"])
    tsunami_policy_message = str(tsunami_policy.get("message") or "")

    with metric_placeholder.container():
        metric_columns = st.columns(5, gap="medium")
        metric_columns[0].metric(
            "위치 소스",
            format_location_source_label(st.session_state.get("realtime_location_source")),
        )
        metric_columns[1].metric("감지 지역", f"{active_sido} {active_sigungu}")
        metric_columns[2].metric("최근 알림", f"{len(recent_alerts):.0f}")
        metric_columns[3].metric("선택 재난", "-" if not selected_disaster else str(selected_disaster))
        metric_columns[4].metric(
            "대피소",
            f"{len(recommendations):.0f}" if show_recommendations else "-",
        )

    with map_body_placeholder.container():
        if not selected_disaster:
            st.info("재난 유형을 선택해 주세요.")
        elif recommendations.empty:
            st.info("추천 결과가 없습니다.")
        elif tsunami_policy["is_tsunami"] and not tsunami_policy["is_actionable"]:
            st.warning(tsunami_policy_message)
            st.info(OFFICIAL_GUIDANCE_MESSAGE)
        else:
            components.html(map_html, height=SHOWCASE_MAP_HEIGHT_PX)

    with top3_body_placeholder.container():
        if not selected_disaster:
            st.info("재난 유형을 선택해주세요")
        elif recommendations.empty:
            st.info("현재 조건으로 추천할 대피소가 없습니다.")
        elif tsunami_policy["is_tsunami"] and not tsunami_policy["is_actionable"]:
            st.warning(tsunami_policy_message)
            st.info(OFFICIAL_GUIDANCE_MESSAGE)
        else:
            _render_showcase_top3_cards(
                recommendations,
                route_details,
                is_tsunami=bool(tsunami_policy["is_tsunami"]),
            )
            if tsunami_policy["is_tsunami"]:
                st.info(TSUNAMI_ETA_WARNING_MESSAGE)

    if route_warnings:
        for warning in dict.fromkeys(route_warnings):
            st.warning(warning)

    _render_showcase_detail_expander(
        recent_alerts,
        recommendations,
        route_details,
        tsunami_policy=tsunami_policy,
        tsunami_policy_message=tsunami_policy_message,
    )


if os.environ.get("PROJECT_DASHBOARD_IMPORT_ONLY") != "1":
    render_page()
