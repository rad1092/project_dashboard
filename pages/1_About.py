"""재난 대피소 추천 프로젝트 소개 페이지."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st

APP_TITLE = "재난 대피소 추천 워크스페이스"
APP_ICON = "🛟"
PAGE_LABEL = "1 About"

ABOUT_DATA = {
    "name": "재난 대피소 추천 + 분석 프로젝트",
    "headline": "전처리된 재난 특보 이력과 대피소 좌표 데이터를 이용해 추천 흐름과 분석 구조를 함께 정리하는 Streamlit 앱",
    "intro": (
        "이 프로젝트는 지금 당장 유료 API나 실시간 공공 API 없이도, "
        "사용자가 지역과 위치를 선택하면 어떤 재난 상황에서 어떤 대피소를 먼저 볼 수 있는지 "
        "설명 가능한 형태로 보여주는 것을 목표로 한다. "
        "현재 단계에서는 과거 전처리 데이터를 사용하고, 이후 실시간 특보와 자동 위치 인식을 붙일 수 있는 구조를 먼저 정리한다."
    ),
    "focus_areas": [
        "입력 좌표에서 감지한 활성 지역의 특보 이력을 빠르게 요약하기",
        "대피소 좌표와 직선 거리 계산으로 가까운 추천 후보 Top 3를 제시하기",
        "추천이 어떤 데이터와 규칙으로 만들어졌는지 별도 설명 페이지로 풀어내기",
    ],
    "tech_stack": ["Python", "Streamlit", "pandas", "plotly", "folium"],
    "principles": [
        "유료 API와 유료 지도 API는 넣지 않는다.",
        "외부 전처리 CSV는 읽기 전용으로 사용하고 앱 코드에서 수정하지 않는다.",
        "페이지, 테스트, 문서를 함께 갱신해 설명과 동작이 어긋나지 않게 한다.",
    ],
    "next_steps": [
        "브라우저 위치 권한 연동으로 현재 좌표를 자동 채우는 흐름 추가",
        "실시간 특보 API를 붙여 자동 재난 선택 로직으로 확장",
        "경로 API 또는 내비게이션 대체 수단을 붙일 수 있는 인터페이스 설계",
    ],
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
    """소개 페이지의 Streamlit 기본 설정을 적용한다."""

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


def render_chip_list(items: list[str]) -> None:
    """짧은 항목 목록을 칩 형태로 출력한다."""

    chips = " ".join(f"`{item}`" for item in items)
    st.markdown(chips)


def render_bordered_points(title: str, items: list[str]) -> None:
    """제목과 글머리표 목록이 들어간 테두리 컨테이너를 렌더링한다."""

    with st.container(border=True):
        st.subheader(title)
        for item in items:
            st.markdown(f"- {item}")


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
    """소개 페이지를 렌더링한다."""

    apply_page_config()

    render_page_intro(
        "1 About",
        "이 프로젝트는 전처리된 재난 특보 이력과 대피소 데이터를 이용해 추천 결과와 분석 구조를 함께 보여주는 앱입니다.",
        "현재 단계에서는 과거 데이터 기반 추천과 설명 구조를 먼저 안정화하고 있습니다.",
    )

    left, right = st.columns([1.1, 0.9], gap="large")

    with left:
        with st.container(border=True):
            st.subheader(ABOUT_DATA["name"])
            st.write(ABOUT_DATA["headline"])
            st.write(ABOUT_DATA["intro"])

        render_bordered_points("집중하고 있는 방향", ABOUT_DATA["focus_areas"])
        render_bordered_points("운영 원칙", ABOUT_DATA["principles"])

    with right:
        with st.container(border=True):
            st.subheader("기술 스택")
            render_chip_list(ABOUT_DATA["tech_stack"])

        render_bordered_points("다음 단계", ABOUT_DATA["next_steps"])

        with st.container(border=True):
            st.subheader("현재 한계")
            for item in LIMITATIONS:
                st.markdown(f"- {item}")

    st.divider()

    try:
        alerts_frame = load_alerts_dataframe()
        shelters_frame = load_shelters_dataframe()
        earthquake_shelters_frame = load_earthquake_shelters_dataframe()
        tsunami_shelters_frame = load_tsunami_shelters_dataframe()
        catalog = build_dataset_catalog(
            alerts_frame=alerts_frame,
            shelters_frame=shelters_frame,
            earthquake_shelters_frame=earthquake_shelters_frame,
            tsunami_shelters_frame=tsunami_shelters_frame,
        )
    except FileNotFoundError as exc:
        st.warning(str(exc))
    else:
        with st.container(border=True):
            st.subheader("현재 연결된 전처리 데이터")
            for item in catalog:
                st.markdown(
                    f"- **{item['name']}**: {format_number(item['rows'])}건, {item['description']}"
                )

    st.divider()

    with st.container(border=True):
        st.subheader("이후 페이지 읽는 순서")
        st.markdown("- `2 대피소 추천`: 현재 데이터 기준 실제 추천 결과를 본다.")
        st.markdown("- `3 작동 설명`: 추천이 어떤 계산 단계로 만들어지는지 확인한다.")
        st.markdown("- `4 실시간 준비`: 미래 확장 구조와 비활성화된 스텁을 본다.")
        st.markdown("- `6 Data Analysis`: 과거 특보와 대피소 분포를 분석 관점으로 본다.")


if os.environ.get("PROJECT_DASHBOARD_IMPORT_ONLY") != "1":
    render_page()
