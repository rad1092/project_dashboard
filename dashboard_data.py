from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st

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

ANALYSIS_COLUMNS = ["발표시간", "지역", "시군구", "재난종류", "재난그룹", "특보등급"]


def _maybe_get_secret_data_dir() -> str | None:
    # 로컬 기본 폴더가 아닌 다른 데이터를 붙여야 할 때를 위해 secrets도 경로 후보에 넣어 둔다.
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
    # 예전 개발 환경 호환용 경로다. 저장소 내부 기본 폴더를 먼저 보고, 마지막에만 여기로 떨어진다.
    return Path.home() / "Desktop" / "preprocessing_data"


def normalize_sigungu_name(value: str | None) -> str:
    # CSV마다 "포항시"처럼 접미사가 붙기도 하고 빠지기도 해서,
    # 지역 비교 전에 최소한의 문자열 정규화를 맞춰 둔다.
    if value is None or pd.isna(value):
        return ""

    text = str(value).strip().replace(" ", "")
    if text.endswith(("시", "군")) and len(text) > 1:
        return text[:-1]
    return text


def resolve_data_dir(path_override: str | Path | None = None) -> Path:
    # 테스트, 배포, 로컬 실행이 서로 다른 폴더를 볼 수 있으므로
    # 경로 우선순위를 한 함수에 고정해 두고 모든 화면이 같이 쓴다.
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
    # 운영 중 가장 자주 헷갈리는 부분이 "파일이 없는데 어디를 봐야 하는가"라서
    # FileNotFoundError 메시지에 다음 확인 지점을 같이 넣는다.
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
    # 추천, 실시간, 분석이 모두 특보 데이터를 같이 보므로
    # 날짜형 변환과 문자열 정리를 여기서 끝내야 화면별 분기가 줄어든다.
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
    # 통합 대피소 CSV는 추천 정렬과 지역 비교에 바로 쓰이므로,
    # 숫자형과 지역 정규화 컬럼을 미리 만들어 둔다.
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
    # 지진/해일 전용 CSV도 추천 함수에서는 일반 대피소와 거의 같은 방식으로 다루고 싶기 때문에
    # 여기서 공통 컬럼 구조로 맞춘다.
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
    # 테스트는 항상 uncached 버전을 써서 입력 경로마다 즉시 다른 결과를 확인한다.
    data_dir = resolve_data_dir(path_override)
    return _prepare_alerts(_read_csv(data_dir / DATASET_FILE_MAP["alerts"]))


@st.cache_data(show_spinner=False)
def load_alerts_dataframe(path_override: str | None = None) -> pd.DataFrame:
    # 화면 실행에서는 같은 CSV를 반복해서 읽지 않도록 cache 버전을 기본으로 쓴다.
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
    # 원본 특보 이름은 그대로 쓰면 필터와 추천 옵션이 너무 잘게 쪼개지므로
    # 앱에서 공통으로 쓰는 재난 그룹으로 한 번 묶는다.
    if disaster_name is None:
        return "기타"

    text = str(disaster_name).strip()
    return RAW_TO_GROUP.get(text, text if text in DEFAULT_DISASTER_OPTIONS else "기타")


def load_analysis_dataset(data_dir: str | Path | None = None) -> pd.DataFrame:
    # 분석 페이지뿐 아니라 홈 KPI도 같은 분석용 DataFrame을 쓰도록 해서
    # "홈 숫자"와 "분석 숫자"가 다르게 보이는 문제를 막는다.
    if data_dir is None:
        alerts_frame = load_alerts_dataframe()
    else:
        alerts_frame = load_alerts_dataframe_uncached(data_dir)

    analysis_frame = alerts_frame.copy()
    analysis_frame["재난그룹"] = analysis_frame["재난종류"].map(classify_disaster_type)
    return analysis_frame[ANALYSIS_COLUMNS].sort_values("발표시간").reset_index(drop=True)


def build_kpis(dataframe: pd.DataFrame) -> dict[str, object]:
    # 홈과 분석 페이지가 같은 계산 결과를 쓰도록 KPI도 공용 함수로 분리했다.
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
    # 홈에서는 "지금 어떤 CSV를 몇 건 읽고 있는가"를 보여 주고 싶어서,
    # DataFrame과 원본 경로를 같이 묶은 카탈로그 형태로 만든다.
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
