"""홈 페이지 엔트리포인트.

이 파일은 ``streamlit run app.py`` 로 앱을 열었을 때 가장 먼저 보이는 화면이다.
현재 프로젝트가 무엇을 목표로 하는지, 어떤 데이터가 연결되어 있는지,
그리고 사용자가 어느 페이지부터 보면 되는지를 한 번에 안내하는 역할을 맡는다.

초보자 관점에서 이 파일을 읽는 방법:
- 위쪽 상수는 홈 화면이 어떤 문구와 페이지 체계를 쓰는지 보여 준다.
- 중간의 데이터 로딩 함수들은 "홈이 어떤 CSV 를 읽는가"를 보여 준다.
- 마지막 ``render_page()`` 는 실제 화면 순서를 담당한다.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st

APP_TITLE = "재난 대피소 추천 워크스페이스"
APP_ICON = "🛟"

PAGE_META = {
    "home": {
        "label": "재난 대피소 추천 프로젝트 홈",
        "summary": "프로젝트 목적, 현재 데이터 범위, 페이지 읽는 순서를 안내하는 시작 화면",
    },
    "about": {
        "label": "1 About",
        "summary": "현재 프로젝트가 무엇을 풀고 있는지와 데이터 한계를 소개하는 페이지",
    },
    "recommendation": {
        "label": "2 대피소 추천",
        "summary": "전처리된 특보와 대피소 데이터를 이용해 Top 3 대피소를 추천하는 핵심 페이지",
    },
    "flow": {
        "label": "3 작동 설명",
        "summary": "대피소 추천이 어떤 순서로 계산되는지 흐름과 데이터 계약을 설명하는 페이지",
    },
    "realtime": {
        "label": "4 실시간 준비",
        "summary": "향후 자동 위치, 실시간 특보, 경로 API를 어디에 붙일지 정리한 준비 페이지",
    },
    "projects": {
        "label": "5 Projects",
        "summary": "현재 저장소 안에서 진행 중인 구현 작업과 역할을 기록하는 페이지",
    },
    "analysis": {
        "label": "6 Data Analysis",
        "summary": "과거 재난 특보와 대피소 분포를 분석 관점으로 보는 보조 페이지",
    },
    "learning": {
        "label": "7 Learning Log",
        "summary": "현재 구조에서 무엇을 배우고 어떤 순서로 확장할지 정리한 페이지",
    },
}

HOME_OVERVIEW_POINTS = [
    "과거 특보 이력을 바탕으로 좌표에서 감지한 활성 지역에서 어떤 재난 유형을 먼저 봐야 하는지 요약한다.",
    "통합 대피소, 지진 대피소, 지진해일 대피소 데이터를 분리해 상황별 추천 규칙을 적용한다.",
    "대피소 추천과 분석 화면을 함께 제공해 앱의 결과와 근거를 동시에 읽을 수 있게 한다.",
]

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

RAW_TO_GROUP = {
    "지진": "지진",
    "지진해일": "지진해일/쓰나미",
    "쓰나미": "지진해일/쓰나미",
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
    "지진해일/쓰나미",
]

ANALYSIS_COLUMNS = ["발표시간", "지역", "시군구", "재난종류", "재난그룹", "특보등급"]
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

    return Path(__file__).resolve().parent / "preprocessing_data"


def _get_desktop_default_data_dir() -> Path:
    """기존 로컬 실행 호환용 Desktop 기본 경로를 반환한다."""

    return Path.home() / "Desktop" / "preprocessing_data"


def normalize_sigungu_name(value: str | None) -> str:
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
    """재난 특보 DataFrame 을 앱 공통 형식으로 정리한다."""

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
    """통합/일반 대피장소 DataFrame 을 앱 공통 형식으로 정리한다."""

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
    """지진/해일 전용 대피장소 DataFrame 을 통합 대피소와 비슷한 형식으로 맞춘다."""

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


def classify_disaster_type(disaster_name: str | None) -> str:
    """원본 재난 명칭을 내부 그룹으로 정규화한다."""

    if disaster_name is None:
        return "기타"

    text = str(disaster_name).strip()
    return RAW_TO_GROUP.get(text, text if text in DEFAULT_DISASTER_OPTIONS else "기타")


def load_analysis_dataset(data_dir: str | Path | None = None) -> pd.DataFrame:
    """홈과 분석 화면이 공통으로 사용할 특보 이력 DataFrame 을 반환한다."""

    if data_dir is None:
        alerts_frame = load_alerts_dataframe()
    else:
        alerts_frame = load_alerts_dataframe_uncached(data_dir)

    analysis_frame = alerts_frame.copy()
    analysis_frame["재난그룹"] = analysis_frame["재난종류"].map(classify_disaster_type)
    return analysis_frame[ANALYSIS_COLUMNS].sort_values("발표시간").reset_index(drop=True)


def build_kpis(dataframe: pd.DataFrame) -> dict[str, object]:
    """홈 화면과 분석 화면에 필요한 기본 KPI 를 계산한다."""

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
        "disaster_count": int(dataframe["재난그룹"].nunique()),
        "region_count": int(dataframe["지역"].nunique()),
        "warning_count": int((dataframe["특보등급"] == "경보").sum()),
        "latest_period": pd.Timestamp(dataframe["발표시간"].max()),
    }


def build_dataset_catalog(
    alerts_frame: pd.DataFrame,
    shelters_frame: pd.DataFrame,
    earthquake_shelters_frame: pd.DataFrame,
    tsunami_shelters_frame: pd.DataFrame,
    path_override: str | Path | None = None,
) -> list[dict[str, object]]:
    """홈과 설명 페이지에 보여줄 데이터셋 요약 정보를 만든다."""

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
    """홈 페이지를 렌더링한다."""

    st.set_page_config(
        page_title=f"{APP_TITLE} | {PAGE_META['home']['label']}",
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title(PAGE_META["home"]["label"])
    st.write(
        "이 앱은 전처리된 재난 특보 이력과 대피소 좌표 데이터를 이용해 "
        "대피소 추천 흐름과 분석 화면을 함께 보여주는 Streamlit 프로젝트입니다."
    )
    st.caption(
        "실시간 API나 유료 지도 API는 아직 연결하지 않았으며, 현재는 과거 전처리 데이터 기준으로 동작합니다."
    )

    try:
        data_dir = resolve_data_dir()
        alerts_frame = load_alerts_dataframe()
        shelters_frame = load_shelters_dataframe()
        earthquake_shelters_frame = load_earthquake_shelters_dataframe()
        tsunami_shelters_frame = load_tsunami_shelters_dataframe()
        analysis_frame = load_analysis_dataset()
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.info(
            "기본 실행은 저장소 내부 `preprocessing_data` 폴더를 사용한다. "
            "다른 위치의 데이터를 쓰려면 `.streamlit/secrets.toml` 또는 "
            "`PREPROCESSING_DATA_DIR` 환경변수로 경로를 덮어쓰면 된다."
        )
        st.stop()

    kpis = build_kpis(analysis_frame)
    catalog = build_dataset_catalog(
        alerts_frame=alerts_frame,
        shelters_frame=shelters_frame,
        earthquake_shelters_frame=earthquake_shelters_frame,
        tsunami_shelters_frame=tsunami_shelters_frame,
    )

    metric_columns = st.columns(4)
    metric_columns[0].metric("특보 기록 수", f"{float(kpis['alert_count']):,.0f}")
    metric_columns[1].metric("통합 대피소 수", f"{float(len(shelters_frame)):,.0f}")
    metric_columns[2].metric("권역 수", f"{float(kpis['region_count']):,.0f}")
    metric_columns[3].metric(
        "최근 특보 시각",
        "-"
        if kpis["latest_period"] is None or pd.isna(kpis["latest_period"])
        else pd.Timestamp(kpis["latest_period"]).strftime("%Y-%m-%d %H:%M"),
    )

    st.divider()

    left, right = st.columns([1.05, 0.95], gap="large")

    with left:
        with st.container(border=True):
            st.subheader("이 앱에서 바로 볼 수 있는 것")
            for point in HOME_OVERVIEW_POINTS:
                st.markdown(f"- {point}")

        with st.container(border=True):
            st.subheader("추천 흐름 페이지")
            for page_key in ["about", "recommendation", "flow", "realtime"]:
                page = PAGE_META[page_key]
                st.markdown(f"- **{page['label']}**: {page['summary']}")

        with st.container(border=True):
            st.subheader("보조 페이지")
            for page_key in ["projects", "analysis", "learning"]:
                page = PAGE_META[page_key]
                st.markdown(f"- **{page['label']}**: {page['summary']}")

    with right:
        with st.container(border=True):
            st.subheader("현재 연결된 데이터셋")
            for item in catalog:
                st.markdown(
                    f"- **{item['name']}**: {float(item['rows']):,.0f}건, "
                    f"{item['description']}"
                )

        with st.container(border=True):
            st.subheader("현재 단계의 한계")
            for item in LIMITATIONS:
                st.markdown(f"- {item}")

        with st.container(border=True):
            st.subheader("데이터 폴더")
            st.code(str(data_dir), language="text")
            st.write(
                "이 경로의 CSV는 앱이 읽기 전용으로 사용한다. "
                "전처리 원본은 수정하지 않고, 페이지와 문서만 구조화하는 것이 이번 단계의 기준이다."
            )

    st.divider()

    with st.container(border=True):
        st.subheader("실행 방법")
        st.code("streamlit run app.py", language="powershell")
        st.write(
            "왼쪽 사이드바에서 `1 About` 부터 `7 Learning Log` 까지 순서대로 이동하면 "
            "소개 -> 추천 -> 작동 설명 -> 실시간 확장 준비 -> 보조 문서를 한 흐름으로 볼 수 있다."
        )


if os.environ.get("PROJECT_DASHBOARD_IMPORT_ONLY") != "1":
    render_page()
