"""대피소 추천이 어떤 흐름으로 작동하는지 설명하는 페이지."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st

APP_TITLE = "재난 대피소 추천 워크스페이스"
APP_ICON = "🛟"
PAGE_LABEL = "3 작동 설명"

FLOW_STEPS = [
    {
        "step": "01",
        "title": "좌표 입력과 지역 감지",
        "summary": "사용자가 위도와 경도를 입력하면 통합 대피소 지역 중심 좌표를 기준으로 가장 가까운 지역을 감지하고 추천 기준 위치를 정한다.",
        "status": "현재 구현",
        "now_note": "현재는 좌표 우선 입력 뒤 자동 감지된 지역을 기본으로 쓰고, 필요하면 사이드바에서 수동 보정한다.",
        "future_note": "브라우저 권한을 받아 현재 위치를 자동 채우는 버튼과 reverse geocoding 기반 지역 판별로 확장할 수 있다.",
    },
    {
        "step": "02",
        "title": "최근 특보 요약",
        "summary": "감지되거나 보정된 활성 지역의 최근 특보 이력에서 재난 유형과 최신 시각을 요약해 현재 화면의 기본 문맥을 만든다.",
        "status": "현재 구현",
        "now_note": "과거 전처리 데이터 안에서만 최근 이력을 찾는다.",
        "future_note": "실시간 공공 API가 연결되면 최신 특보로 자동 갱신할 수 있다.",
    },
    {
        "step": "03",
        "title": "재난 유형 정규화",
        "summary": "원본 특보 명칭을 내부 재난 그룹으로 묶어 어떤 대피소 집합을 먼저 볼지 결정한다.",
        "status": "현재 구현",
        "now_note": "강풍/풍랑, 호우/태풍처럼 비슷한 상황을 하나의 그룹으로 정리한다.",
        "future_note": "실시간 API 응답 구조가 달라져도 이 정규화 함수만 유지하면 된다.",
    },
    {
        "step": "04",
        "title": "대피소 후보 구성",
        "summary": "지진, 지진해일, 폭염, 한파처럼 전용 후보가 있는 경우 우선 사용하고, 부족하면 통합 대피소로 fallback 한다.",
        "status": "현재 구현",
        "now_note": "전용 대피소와 대체 대피소를 다른 라벨로 구분해 보여준다.",
        "future_note": "향후 재난별 상세 정책이 생기면 후보 필터만 바꾸면 된다.",
    },
    {
        "step": "05",
        "title": "거리 계산과 지도 시각화",
        "summary": "사용자 좌표와 대피소 좌표 사이의 직선 거리를 계산해 Top 3를 정렬하고, 무료 OSM 지도에 점과 선으로 표시한다.",
        "status": "현재 구현",
        "now_note": "직선 거리만 계산하며 실제 도로 경로는 제공하지 않는다.",
        "future_note": "경로 API를 붙일 경우 거리 함수와 지도 렌더링 일부만 교체하면 된다.",
    },
    {
        "step": "06",
        "title": "실시간 확장 포인트 분리",
        "summary": "자동 위치, 실시간 특보, 경로 API는 지금은 비활성화된 채 별도 페이지와 주석에서만 설명한다.",
        "status": "준비 완료",
        "now_note": "실행 코드와 미래 코드를 섞지 않아 현재 앱 동작을 단순하게 유지한다.",
        "future_note": "실시간 기능을 붙일 때는 준비 페이지와 서비스 스텁을 실제 함수로 교체하면 된다.",
    },
]

FUTURE_CODE_SNIPPETS = {
    "geolocation": """def get_browser_location() -> tuple[float, float] | None:\n    # TODO: 브라우저 위치 권한을 받은 뒤 사용자의 현재 좌표를 반환한다.\n    # 현재 단계에서는 수동 위경도 입력을 기본값으로 유지하므로 실제 호출은 막아 둔다.\n    return None\n""",
    "alerts": """def fetch_realtime_alerts() -> list[dict[str, str]]:\n    # TODO: 실시간 공공 API가 준비되면 최신 특보를 읽어 현재 재난 유형을 자동 선택한다.\n    # 지금은 전처리된 CSV만 사용하므로 이 함수는 설명용 스텁으로만 남겨 둔다.\n    return []\n""",
    "routing": """def build_live_route(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> dict[str, object] | None:\n    # TODO: 실제 경로 API를 붙이면 직선 거리 대신 도로 기준 경로와 시간을 반환한다.\n    # 유료 API를 쓰지 않는 현재 구조에서는 None 을 반환하고 직선 거리 시각화만 유지한다.\n    return None\n""",
}

LIMITATIONS = [
    "현재 화면의 특보는 과거 전처리 데이터 기준이며 실시간 재난 상황을 보장하지 않는다.",
    "지도는 무료 OSM 타일과 직선 거리만 사용하므로 실제 주행/도보 경로와 다를 수 있다.",
    "재난별 전용 대피소가 부족한 경우에는 통합 대피소를 대체 후보로 함께 보여준다.",
]

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

DATASET_DESCRIPTIONS = {
    "alerts": "재난 특보 이력을 담은 전처리 CSV",
    "shelters": "통합 또는 일반 대피장소 기준 CSV",
    "earthquake_shelters": "지진대피장소 전용 CSV",
    "tsunami_shelters": "해일대피장소 전용 CSV",
}

SPECIAL_SHELTER_TYPE_LABELS = {
    "earthquake_shelter_clean_2.csv": "지진대피장소",
    "tsunami_shelter_clean_2.csv": "해일대피장소",
}


def apply_page_config() -> None:
    """설명 페이지의 Streamlit 기본 설정을 적용한다."""

    st.set_page_config(
        page_title=f"{APP_TITLE} | {PAGE_LABEL}",
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )


def render_page_intro(title: str, subtitle: str, caption: str | None = None) -> None:
    """페이지 상단의 공통 제목 블록을 그린다."""

    st.title(title)
    st.write(subtitle)
    if caption:
        st.caption(caption)


def render_bordered_points(title: str, items: list[str]) -> None:
    """제목과 글머리표 목록이 들어간 테두리 컨테이너를 렌더링한다."""

    with st.container(border=True):
        st.subheader(title)
        for item in items:
            st.markdown(f"- {item}")


def render_dataset_cards(catalog: list[dict[str, object]]) -> None:
    """데이터셋 역할을 카드형으로 보여준다."""

    for item in catalog:
        with st.container(border=True):
            st.subheader(str(item["name"]))
            st.write(str(item["description"]))
            st.markdown(f"**행 수**: {format_number(int(item['rows']))}건")
            st.markdown(f"**컬럼**: {item['columns']}")
            st.caption(f"원본 경로: {item['source_path']}")


def render_flow_steps(steps: list[dict[str, str]]) -> None:
    """추천 플로우 설명용 단계를 순서대로 렌더링한다."""

    for item in steps:
        with st.container(border=True):
            head_left, head_right = st.columns([0.8, 0.2])
            with head_left:
                st.subheader(f"{item['step']}. {item['title']}")
            with head_right:
                st.markdown(f"**{item['status']}**")
            st.write(item["summary"])
            st.markdown(f"**현재 구현**: {item['now_note']}")
            st.markdown(f"**나중에 바꿀 지점**: {item['future_note']}")


def format_number(value: int | float) -> str:
    """천 단위 구분 기호가 있는 문자열로 바꾼다."""

    return f"{float(value):,.0f}"


def _maybe_get_secret_data_dir() -> str | None:
    """Streamlit secrets 에 설정된 외부 데이터 경로가 있는지 읽는다."""

    try:
        if "preprocessing_data_dir" in st.secrets:
            return str(st.secrets["preprocessing_data_dir"])
        if "app" in st.secrets and "preprocessing_data_dir" in st.secrets["app"]:
            return str(st.secrets["app"]["preprocessing_data_dir"])
    except Exception:
        return None
    return None


def _get_repo_default_data_dir() -> Path:
    """저장소에 포함된 기본 전처리 데이터 폴더 경로를 반환한다."""

    return Path(__file__).resolve().parents[1] / "preprocessing_data"


def _get_desktop_default_data_dir() -> Path:
    """기존 로컬 실행 호환용 Desktop 기본 경로를 반환한다."""

    return Path.home() / "Desktop" / "preprocessing_data"


def _normalize_sigungu_name(value: str | None) -> str:
    """시군구 명칭을 비교용 문자열로 정규화한다."""

    if value is None or pd.isna(value):
        return ""
    text = str(value).strip().replace(" ", "")
    if text.endswith(("시", "군")) and len(text) > 1:
        return text[:-1]
    return text


def resolve_data_dir(path_override: str | Path | None = None) -> Path:
    """전처리 데이터 폴더 경로를 결정한다."""

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
    """UTF-8 기반 전처리 CSV 를 읽는다."""

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
    """CSV 에 기대한 컬럼이 모두 있는지 확인한다."""

    missing_columns = [column for column in expected_columns if column not in dataframe.columns]
    if missing_columns:
        raise ValueError(f"{label} CSV 에 필요한 컬럼이 없다: {missing_columns}")


def _prepare_alerts(dataframe: pd.DataFrame) -> pd.DataFrame:
    """재난 특보 DataFrame 을 공통 형식으로 정리한다."""

    _validate_columns(dataframe, ALERT_COLUMNS, "danger_clean.csv")
    alerts = dataframe.copy()
    alerts["발표시간"] = pd.to_datetime(alerts["발표시간"], errors="coerce")
    alerts["시군구정규화"] = alerts["시군구"].map(_normalize_sigungu_name)
    return alerts.dropna(subset=["발표시간"]).sort_values("발표시간").reset_index(drop=True)


def _prepare_shelters(dataframe: pd.DataFrame) -> pd.DataFrame:
    """통합/일반 대피장소 DataFrame 을 공통 형식으로 정리한다."""

    _validate_columns(dataframe, SHELTER_COLUMNS, "final_shelter_dataset.csv")
    shelters = dataframe.copy()
    shelters["위도"] = pd.to_numeric(shelters["위도"], errors="coerce")
    shelters["경도"] = pd.to_numeric(shelters["경도"], errors="coerce")
    shelters["수용인원"] = pd.to_numeric(shelters["수용인원"], errors="coerce")
    shelters["시군구정규화"] = shelters["시군구"].map(_normalize_sigungu_name)
    shelters["수용인원_정렬값"] = shelters["수용인원"].fillna(0)
    return shelters.dropna(subset=["위도", "경도"]).reset_index(drop=True)


def _prepare_special_shelters(
    dataframe: pd.DataFrame,
    expected_columns: list[str],
    label: str,
) -> pd.DataFrame:
    """지진/해일 전용 대피장소 DataFrame 을 통합 대피소와 비슷한 형식으로 맞춘다."""

    _validate_columns(dataframe, expected_columns, label)
    shelters = dataframe.copy()
    shelters["위도"] = pd.to_numeric(shelters["위도"], errors="coerce")
    shelters["경도"] = pd.to_numeric(shelters["경도"], errors="coerce")
    shelters["수용인원"] = pd.to_numeric(shelters["수용인원"], errors="coerce")
    if "지역" not in shelters.columns:
        shelters["지역"] = shelters["시도"].astype(str).str.strip() + " " + shelters["시군구"].astype(str).str.strip()
    shelters["대피소유형"] = SPECIAL_SHELTER_TYPE_LABELS[label]
    shelters["수용인원_정렬값"] = shelters["수용인원"].fillna(0)
    return shelters.dropna(subset=["위도", "경도"]).reset_index(drop=True)


def load_alerts_dataframe_uncached(path_override: str | Path | None = None) -> pd.DataFrame:
    """전처리 폴더에서 재난 특보 DataFrame 을 읽는다."""

    data_dir = resolve_data_dir(path_override)
    return _prepare_alerts(_read_csv(data_dir / DATASET_FILE_MAP["alerts"]))


@st.cache_data(show_spinner=False)
def load_alerts_dataframe(path_override: str | None = None) -> pd.DataFrame:
    """Streamlit rerun 시 재난 특보 CSV 재로딩을 줄이기 위한 캐시 래퍼."""

    return load_alerts_dataframe_uncached(path_override)


def load_shelters_dataframe_uncached(path_override: str | Path | None = None) -> pd.DataFrame:
    """전처리 폴더에서 통합 대피소 DataFrame 을 읽는다."""

    data_dir = resolve_data_dir(path_override)
    return _prepare_shelters(_read_csv(data_dir / DATASET_FILE_MAP["shelters"]))


@st.cache_data(show_spinner=False)
def load_shelters_dataframe(path_override: str | None = None) -> pd.DataFrame:
    """Streamlit rerun 시 통합 대피소 CSV 재로딩을 줄이기 위한 캐시 래퍼."""

    return load_shelters_dataframe_uncached(path_override)


def load_earthquake_shelters_dataframe_uncached(
    path_override: str | Path | None = None,
) -> pd.DataFrame:
    """전처리 폴더에서 지진 전용 대피소 DataFrame 을 읽는다."""

    data_dir = resolve_data_dir(path_override)
    return _prepare_special_shelters(
        _read_csv(data_dir / DATASET_FILE_MAP["earthquake_shelters"]),
        EARTHQUAKE_COLUMNS,
        "earthquake_shelter_clean_2.csv",
    )


@st.cache_data(show_spinner=False)
def load_earthquake_shelters_dataframe(path_override: str | None = None) -> pd.DataFrame:
    """Streamlit rerun 시 지진 전용 대피소 CSV 재로딩을 줄이기 위한 캐시 래퍼."""

    return load_earthquake_shelters_dataframe_uncached(path_override)


def load_tsunami_shelters_dataframe_uncached(
    path_override: str | Path | None = None,
) -> pd.DataFrame:
    """전처리 폴더에서 해일 전용 대피소 DataFrame 을 읽는다."""

    data_dir = resolve_data_dir(path_override)
    return _prepare_special_shelters(
        _read_csv(data_dir / DATASET_FILE_MAP["tsunami_shelters"]),
        TSUNAMI_COLUMNS,
        "tsunami_shelter_clean_2.csv",
    )


@st.cache_data(show_spinner=False)
def load_tsunami_shelters_dataframe(path_override: str | None = None) -> pd.DataFrame:
    """Streamlit rerun 시 해일 전용 대피소 CSV 재로딩을 줄이기 위한 캐시 래퍼."""

    return load_tsunami_shelters_dataframe_uncached(path_override)


def build_dataset_catalog(
    alerts_frame: pd.DataFrame,
    shelters_frame: pd.DataFrame,
    earthquake_shelters_frame: pd.DataFrame,
    tsunami_shelters_frame: pd.DataFrame,
    path_override: str | Path | None = None,
) -> list[dict[str, object]]:
    """설명 페이지와 홈 화면에 보여줄 데이터셋 요약 정보를 만든다."""

    data_dir = resolve_data_dir(path_override)
    dataset_frames = {
        "alerts": alerts_frame,
        "shelters": shelters_frame,
        "earthquake_shelters": earthquake_shelters_frame,
        "tsunami_shelters": tsunami_shelters_frame,
    }

    catalog: list[dict[str, object]] = []
    for key, dataframe in dataset_frames.items():
        catalog.append(
            {
                "name": key,
                "description": DATASET_DESCRIPTIONS[key],
                "rows": int(len(dataframe)),
                "columns": ", ".join(dataframe.columns.tolist()),
                "source_path": str(data_dir / DATASET_FILE_MAP[key]),
            }
        )
    return catalog


def render_page() -> None:
    """작동 설명 페이지를 렌더링한다."""

    apply_page_config()

    render_page_intro(
        "3 작동 설명",
        "청사진 이미지를 그대로 붙이지 않고, 현재 앱이 실제로 어떤 순서로 작동하는지 Streamlit 흐름 카드로 다시 구성했습니다.",
        "현재 구현된 구간과 나중에 바꿀 구간을 분리해서 읽을 수 있게 정리합니다.",
    )

    try:
        alerts_frame = load_alerts_dataframe()
        shelters_frame = load_shelters_dataframe()
        earthquake_shelters_frame = load_earthquake_shelters_dataframe()
        tsunami_shelters_frame = load_tsunami_shelters_dataframe()
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.stop()

    catalog = build_dataset_catalog(
        alerts_frame=alerts_frame,
        shelters_frame=shelters_frame,
        earthquake_shelters_frame=earthquake_shelters_frame,
        tsunami_shelters_frame=tsunami_shelters_frame,
    )

    with st.container(border=True):
        st.subheader("추천 플로우")
        render_flow_steps(FLOW_STEPS)

    st.divider()

    left, right = st.columns([0.95, 1.05], gap="large")

    with left:
        with st.container(border=True):
            st.subheader("현재 구현된 구간")
            st.markdown("- 지역 선택과 좌표 입력")
            st.markdown("- 최근 특보 요약")
            st.markdown("- 재난 유형 정규화")
            st.markdown("- 전용/대체 대피소 추천")
            st.markdown("- 무료 지도와 직선 거리 시각화")

        render_bordered_points("현재 단계의 제한", LIMITATIONS)

    with right:
        with st.container(border=True):
            st.subheader("향후 교체 위치 예시")
            st.code(FUTURE_CODE_SNIPPETS["geolocation"], language="python")
            st.code(FUTURE_CODE_SNIPPETS["alerts"], language="python")
            st.code(FUTURE_CODE_SNIPPETS["routing"], language="python")

    st.divider()

    with st.container(border=True):
        st.subheader("현재 연결된 데이터셋")
        render_dataset_cards(catalog)


if os.environ.get("PROJECT_DASHBOARD_IMPORT_ONLY") != "1":
    render_page()
