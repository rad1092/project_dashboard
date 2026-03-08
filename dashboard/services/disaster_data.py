"""외부 전처리 데이터 폴더를 읽어 앱용 DataFrame 으로 정리하는 서비스 모듈.

왜 필요한가:
- 실제 CSV 는 프로젝트 바깥 ``preprocessing_data`` 폴더에 있고 계속 갱신될 수 있다.
- 페이지 파일이 직접 CSV 경로, 인코딩, 원본 컬럼 차이를 알게 두면 구조가 금방 복잡해진다.

누가 사용하는가:
- 홈, About, 추천, 분석, 작동 설명 페이지가 모두 이 모듈을 통해 데이터를 읽는다.

무엇을 보장하는가:
- 외부 데이터 경로 탐색
- CSV 컬럼 검증
- 특보/대피소 DataFrame 표준화
- 전용 대피소 표시용 컬럼 합성
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import streamlit as st

ALERT_COLUMNS = ["발표시간", "지역", "시군구", "재난종류", "특보등급", "해당지역"]
SHELTER_COLUMNS = ["대피소명", "주소", "대피소유형", "위도", "경도", "시도", "시군구", "지역", "수용인원"]
EARTHQUAKE_COLUMNS = ["대피소명", "주소", "위도", "경도", "수용인원", "시도", "시군구"]
TSUNAMI_COLUMNS = ["대피소명", "주소", "위도", "경도", "수용인원", "지역", "시도", "시군구"]
# 이 상수들은 각 CSV 가 최소한 가져야 하는 컬럼 계약이다.
# 페이지까지 내려가기 전에 서비스 계층에서 먼저 검증해야 스키마 오류를 빨리 잡을 수 있다.

DATASET_FILE_MAP = {
    "alerts": Path("preprocessing") / "danger_clean.csv",
    "shelters": Path("preprocessing") / "final_shelter_dataset.csv",
    "earthquake_shelters": Path("preprocessing") / "earthquake_shelter_clean_2.csv",
    "tsunami_shelters": Path("preprocessing") / "tsunami_shelter_clean_2.csv",
}
# 파일명을 상수로 둔 이유는 같은 문자열을 여러 함수에서 반복하지 않고 수정 지점을 한곳으로 모으기 위해서다.

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
# 전용 대피소 CSV 는 원본에 대피소유형 컬럼이 없으므로, 로딩 시 붙일 표시용 라벨을 여기서 관리한다.


@dataclass(frozen=True)
class DisasterDatasetBundle:
    """페이지와 서비스가 함께 쓰는 전처리 데이터 묶음.

    Attributes:
        alerts: 재난 특보 이력 DataFrame.
        shelters: 통합/일반 대피장소 DataFrame.
        earthquake_shelters: 지진대피장소 전용 DataFrame.
        tsunami_shelters: 해일대피장소 전용 DataFrame.
    """

    alerts: pd.DataFrame
    shelters: pd.DataFrame
    earthquake_shelters: pd.DataFrame
    tsunami_shelters: pd.DataFrame


def _maybe_get_secret_data_dir() -> str | None:
    """Streamlit secrets 에 설정된 외부 데이터 경로가 있는지 읽는다.

    로컬 실행과 배포 환경이 다를 수 있어 secrets 조회를 별도 함수로 분리한다.
    """

    try:
        # secrets 구조를 두 형태로 모두 보는 이유는 로컬 예시 파일과 향후 배포 구성이 다를 수 있기 때문이다.
        if "preprocessing_data_dir" in st.secrets:
            return str(st.secrets["preprocessing_data_dir"])
        if "app" in st.secrets and "preprocessing_data_dir" in st.secrets["app"]:
            return str(st.secrets["app"]["preprocessing_data_dir"])
    except Exception:
        return None
    return None


def normalize_sigungu_name(value: str | None) -> str:
    """시군구 명칭을 비교용 문자열로 정규화한다.

    포항과 포항시, 울진과 울진군처럼 표기만 다른 지역명을
    같은 문자열로 비교할 수 있게 만들어 후보 필터가 덜 흔들리게 한다.
    """

    if value is None or pd.isna(value):
        return ""

    text = str(value).strip().replace(" ", "")
    if text.endswith(("시", "군")) and len(text) > 1:
        return text[:-1]
    return text


def _haversine_km(
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> float:
    """두 위경도 사이의 직선 거리를 km 단위로 계산한다.

    추천 서비스에도 같은 계산이 있지만, 지역 자동 감지는 데이터 서비스 계층에서 끝내야 하므로
    이 모듈 안에도 독립적인 거리 계산 헬퍼를 둔다.
    """

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


def resolve_data_dir(path_override: str | Path | None = None) -> Path:
    """외부 전처리 데이터 폴더 경로를 결정한다.

    우선순위:
    1. 함수 인자로 넘긴 경로
    2. 환경변수 ``PREPROCESSING_DATA_DIR``
    3. ``.streamlit/secrets.toml`` 의 ``preprocessing_data_dir``
    4. ``~/Desktop/preprocessing_data``
    """

    candidates: list[Path] = []
    if path_override is not None:
        candidates.append(Path(path_override))

    env_path = os.environ.get("PREPROCESSING_DATA_DIR")
    if env_path:
        candidates.append(Path(env_path))

    secret_path = _maybe_get_secret_data_dir()
    if secret_path:
        candidates.append(Path(secret_path))

    candidates.append(Path.home() / "Desktop" / "preprocessing_data")

    # 앞에서부터 우선순위가 높은 경로이므로, exists() 가 되는 첫 후보를 바로 채택한다.
    for candidate in candidates:
        resolved = candidate.expanduser().resolve()
        if resolved.exists():
            return resolved

    searched = "\n".join(f"- {path}" for path in candidates)
    raise FileNotFoundError(
        "전처리 데이터 폴더를 찾지 못했다.\n"
        "다음 경로를 차례대로 확인했다:\n"
        f"{searched}\n"
        "환경변수 `PREPROCESSING_DATA_DIR` 또는 `.streamlit/secrets.toml` 에 경로를 지정해 달라."
    )


def _read_csv(path: Path) -> pd.DataFrame:
    """UTF-8 기반 전처리 CSV 를 읽는다."""

    # utf-8-sig 를 쓰는 이유는 Windows 환경에서 BOM 이 포함된 CSV 도 안정적으로 읽기 위해서다.
    return pd.read_csv(path, encoding="utf-8-sig")


def _validate_columns(dataframe: pd.DataFrame, expected_columns: list[str], label: str) -> None:
    """CSV 에 기대한 컬럼이 모두 있는지 확인한다.

    전처리 데이터가 갱신되며 스키마가 바뀌면 여기서 바로 실패시켜
    어떤 CSV 가 깨졌는지 빠르게 알 수 있게 한다.
    """

    missing_columns = [column for column in expected_columns if column not in dataframe.columns]
    if missing_columns:
        raise ValueError(f"{label} CSV 에 필요한 컬럼이 없다: {missing_columns}")


def _prepare_alerts(dataframe: pd.DataFrame) -> pd.DataFrame:
    """재난 특보 DataFrame 을 앱 공통 형식으로 정리한다.

    특보 이력은 최근순 정렬, 지역 필터, 재난 요약에 모두 쓰이므로
    날짜형 변환과 지역명 정규화를 이 단계에서 끝내 둔다.
    """

    _validate_columns(dataframe, ALERT_COLUMNS, "danger_clean.csv")

    alerts = dataframe.copy()
    # 문자열 날짜를 Timestamp 로 맞춰야 최근 특보 계산과 정렬이 안정적으로 동작한다.
    alerts["발표시간"] = pd.to_datetime(alerts["발표시간"], errors="coerce")
    alerts["지역"] = alerts["지역"].astype(str).str.strip()
    alerts["시군구"] = alerts["시군구"].astype(str).str.strip()
    alerts["시군구정규화"] = alerts["시군구"].map(normalize_sigungu_name)
    alerts["재난종류"] = alerts["재난종류"].astype(str).str.strip()
    alerts["특보등급"] = alerts["특보등급"].fillna("미분류").astype(str).str.strip()
    # 날짜 변환 실패 행만 마지막에 제거해야, 그 전까지는 최대한 원문 문자열 정리를 모두 적용할 수 있다.
    return alerts.dropna(subset=["발표시간"]).sort_values("발표시간").reset_index(drop=True)


def _prepare_shelters(dataframe: pd.DataFrame) -> pd.DataFrame:
    """통합/일반 대피장소 DataFrame 을 추천과 분석에서 쓰기 좋게 정리한다.

    통합 대피소는 fallback 추천과 분석 차트가 함께 쓰는 기본 데이터라서,
    좌표/수용인원/지역명 컬럼을 한 번에 표준화해 둔다.
    """

    _validate_columns(dataframe, SHELTER_COLUMNS, "final_shelter_dataset.csv")

    shelters = dataframe.copy()
    # 좌표와 수용인원은 이후 거리 계산/정렬에 바로 쓰이므로 숫자형으로 강제 변환한다.
    shelters["위도"] = pd.to_numeric(shelters["위도"], errors="coerce")
    shelters["경도"] = pd.to_numeric(shelters["경도"], errors="coerce")
    shelters["수용인원"] = pd.to_numeric(shelters["수용인원"], errors="coerce")
    shelters["시도"] = shelters["시도"].astype(str).str.strip()
    shelters["시군구"] = shelters["시군구"].astype(str).str.strip()
    shelters["시군구정규화"] = shelters["시군구"].map(normalize_sigungu_name)
    shelters["대피소유형"] = shelters["대피소유형"].fillna("미분류").astype(str).str.strip()
    # 수용인원_정렬값은 표시용 원문과 분리한 정렬 전용 숫자 값이다.
    # 전용/통합 CSV 차이를 줄이고 추천 정렬 코드를 단순하게 만들기 위해 따로 둔다.
    shelters["수용인원_정렬값"] = shelters["수용인원"].fillna(0)
    return shelters.dropna(subset=["위도", "경도"]).reset_index(drop=True)


def _prepare_special_shelters(
    dataframe: pd.DataFrame,
    expected_columns: list[str],
    label: str,
) -> pd.DataFrame:
    """지진/해일 전용 대피장소 DataFrame 을 통합 대피소와 비슷한 형식으로 맞춘다.

    전용 CSV 두 개는 원본에 ``대피소유형`` 컬럼이 없지만,
    앱 화면과 추천 결과 표는 항상 같은 컬럼 계약을 기대한다.
    그래서 로딩 단계에서만 표시용 유형 라벨을 합성해
    전용/통합 데이터를 한 추천 파이프라인에서 안전하게 다루게 만든다.
    """

    _validate_columns(dataframe, expected_columns, label)

    shelters = dataframe.copy()
    shelters["위도"] = pd.to_numeric(shelters["위도"], errors="coerce")
    shelters["경도"] = pd.to_numeric(shelters["경도"], errors="coerce")
    shelters["수용인원"] = pd.to_numeric(shelters["수용인원"], errors="coerce")
    shelters["시도"] = shelters["시도"].astype(str).str.strip()
    shelters["시군구"] = shelters["시군구"].astype(str).str.strip()
    shelters["시군구정규화"] = shelters["시군구"].map(normalize_sigungu_name)

    if "지역" not in shelters.columns:
        # 전용 CSV 는 지역 문자열이 빠질 수 있어 설명용 최소 지역명을 직접 합성한다.
        shelters["지역"] = shelters["시도"] + " " + shelters["시군구"]
    shelters["지역"] = shelters["지역"].fillna(shelters["시도"] + " " + shelters["시군구"])

    # 원본 전용 CSV 는 유형 컬럼이 없으므로,
    # 앱 표시와 추천 결과 표준 컬럼을 맞추기 위해 여기서만 합성한다.
    shelters["대피소유형"] = SPECIAL_SHELTER_TYPE_LABELS[label]
    shelters["수용인원_정렬값"] = shelters["수용인원"].fillna(0)
    return shelters.dropna(subset=["위도", "경도"]).reset_index(drop=True)


def load_dataset_bundle_uncached(path_override: str | Path | None = None) -> DisasterDatasetBundle:
    """외부 전처리 폴더를 읽어 데이터셋 묶음을 반환한다.

    앱의 모든 화면이 같은 원본 데이터와 같은 전처리 기준을 공유하도록
    네 종류 CSV 를 하나의 묶음 객체로 반환한다.
    """

    data_dir = resolve_data_dir(path_override)
    # 모든 CSV 는 이 함수에서만 읽고 정리해 두고,
    # 이후 화면 계층은 정리된 DataFrame 만 사용한다.
    alerts = _prepare_alerts(_read_csv(data_dir / DATASET_FILE_MAP["alerts"]))
    shelters = _prepare_shelters(_read_csv(data_dir / DATASET_FILE_MAP["shelters"]))
    earthquake_shelters = _prepare_special_shelters(
        _read_csv(data_dir / DATASET_FILE_MAP["earthquake_shelters"]),
        EARTHQUAKE_COLUMNS,
        "earthquake_shelter_clean_2.csv",
    )
    tsunami_shelters = _prepare_special_shelters(
        _read_csv(data_dir / DATASET_FILE_MAP["tsunami_shelters"]),
        TSUNAMI_COLUMNS,
        "tsunami_shelter_clean_2.csv",
    )

    return DisasterDatasetBundle(
        alerts=alerts,
        shelters=shelters,
        earthquake_shelters=earthquake_shelters,
        tsunami_shelters=tsunami_shelters,
    )


@st.cache_data(show_spinner=False)
def load_dataset_bundle(path_override: str | None = None) -> DisasterDatasetBundle:
    """Streamlit rerun 시 CSV 재로딩을 줄이기 위한 캐시 래퍼.

    Streamlit 은 입력이 바뀔 때마다 스크립트를 다시 실행하므로, 무거운 CSV 로딩을 캐시한다.
    """

    return load_dataset_bundle_uncached(path_override)


def get_available_regions(bundle: DisasterDatasetBundle) -> pd.DataFrame:
    """통합 대피장소 기준으로 사용 가능한 시도/시군구 목록을 반환한다.

    드롭다운에는 실제 추천 가능한 지역만 보여 주는 편이 사용자 혼란이 적다.
    """

    # drop_duplicates() 는 selectbox 옵션에 같은 지역이 반복되는 것을 막기 위한 처리다.
    return (
        bundle.shelters[["시도", "시군구"]]
        .drop_duplicates()
        .sort_values(["시도", "시군구"])
        .reset_index(drop=True)
    )


def _build_region_centers(bundle: DisasterDatasetBundle) -> pd.DataFrame:
    """통합 대피소 기준 지역 중심 좌표 표를 만든다.

    현재는 외부 reverse geocoding 이 없기 때문에, 좌표 입력만으로 지역을 추정하려면
    각 지역의 평균 좌표를 먼저 만들어 두고 가장 가까운 지역을 찾는 방식이 필요하다.
    """

    grouped = (
        bundle.shelters.groupby(["시도", "시군구", "시군구정규화"], as_index=False)
        .agg(
            중심위도=("위도", "mean"),
            중심경도=("경도", "mean"),
            대피소수=("대피소명", "size"),
        )
        .sort_values(["시도", "시군구"])
        .reset_index(drop=True)
    )
    # 평균 좌표를 쓰는 이유는 행정경계 데이터 없이도 각 지역의 대표 중심점을 설명 가능하게 만들 수 있기 때문이다.
    return grouped


def infer_region_from_coordinates(
    bundle: DisasterDatasetBundle,
    latitude: float,
    longitude: float,
) -> dict[str, object]:
    """입력 좌표와 가장 가까운 지역 중심을 찾아 시도/시군구를 추정한다.

    이 함수는 행정경계 기반 역지오코딩을 하는 것이 아니다.
    현재 로컬 데이터만으로 동작해야 하므로, 통합 대피소의 지역 중심 좌표를 기준으로
    가장 가까운 시도/시군구를 감지해 추천 페이지의 기본 지역으로 사용한다.
    """

    region_centers = _build_region_centers(bundle)
    if region_centers.empty:
        return {
            "sido": None,
            "sigungu": None,
            "distance_km": None,
            "source": "auto_detected",
        }

    # 중심 좌표까지의 거리를 모두 계산한 뒤 가장 가까운 지역을 선택한다.
    # 거리가 같다면 대피소 수가 더 많은 지역을 우선해 중심 추정이 덜 흔들리게 만든다.
    scored = region_centers.copy()
    scored["distance_km"] = scored.apply(
        lambda row: _haversine_km(
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


def get_sigungu_options(bundle: DisasterDatasetBundle, sido: str) -> list[str]:
    """선택한 시도 안에서 사용 가능한 시군구 목록을 반환한다.

    시도 선택 뒤 바로 세부 지역을 좁혀야 중심 좌표와 추천 후보 계산이 자연스럽게 이어진다.
    """

    # 시도별로 시군구를 다시 계산해야 수동 보정 UI 가 항상 유효한 조합만 보여 줄 수 있다.
    filtered = bundle.shelters[bundle.shelters["시도"] == sido]
    return sorted(filtered["시군구"].dropna().unique().tolist())


def get_region_center(bundle: DisasterDatasetBundle, sido: str, sigungu: str) -> tuple[float | None, float | None]:
    """선택한 지역의 평균 좌표를 반환한다.

    자동 위치 감지가 아직 없기 때문에, 사용자가 기준 좌표를 빠르게 채우도록 지역 평균 좌표를 제공한다.
    """

    region_centers = _build_region_centers(bundle)
    filtered = region_centers[
        (region_centers["시도"] == sido)
        & (region_centers["시군구정규화"] == normalize_sigungu_name(sigungu))
    ]
    # 시군구 단위 후보가 없을 때는 같은 시도 평균으로 넓혀 수동 보정용 좌표 보조 기능이 비지 않게 한다.
    if filtered.empty:
        filtered = region_centers[region_centers["시도"] == sido]
    if filtered.empty:
        return None, None

    return float(filtered["중심위도"].mean()), float(filtered["중심경도"].mean())


def get_recent_alerts(
    bundle: DisasterDatasetBundle,
    sido: str,
    sigungu: str | None = None,
    limit: int = 5,
) -> pd.DataFrame:
    """선택 지역 기준의 최근 특보 이력 일부를 반환한다.

    추천 페이지는 긴 히스토리 전체보다 최근 몇 건이 중요하므로,
    지역 필터와 최신순 정렬을 같이 처리해 바로 UI 에 연결한다.
    """

    filtered = bundle.alerts[bundle.alerts["지역"] == sido]
    if sigungu:
        # 세부 지역 특보가 비어 있으면 같은 시도 전체 기록으로 넓혀
        # 추천 페이지가 완전히 빈 상태로 보이는 상황을 줄인다.
        filtered = filtered[filtered["시군구정규화"] == normalize_sigungu_name(sigungu)]
        if filtered.empty:
            filtered = bundle.alerts[bundle.alerts["지역"] == sido]

    return filtered.sort_values("발표시간", ascending=False).head(limit).reset_index(drop=True)


def build_alert_summary(
    bundle: DisasterDatasetBundle,
    sido: str,
    sigungu: str | None = None,
) -> dict[str, object]:
    """추천 페이지 상단에 보여줄 최근 특보 요약 정보를 만든다.

    카드 UI 에 필요한 작은 조각 정보만 뽑아 dict 로 반환해 페이지가 읽기 쉽게 만든다.
    """

    recent_alerts = get_recent_alerts(bundle, sido=sido, sigungu=sigungu, limit=5)
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


def build_dataset_catalog(
    bundle: DisasterDatasetBundle,
    path_override: str | Path | None = None,
) -> list[dict[str, object]]:
    """설명 페이지와 홈 화면에 보여줄 데이터셋 요약 정보를 만든다.

    파일 이름만 보여 주는 대신 역할, 행 수, 컬럼, 실제 경로를 함께 묶어
    사용자가 어떤 CSV 를 보고 있는지 이해하기 쉽게 만든다.
    """

    data_dir = resolve_data_dir(path_override)
    dataset_frames = {
        "alerts": bundle.alerts,
        "shelters": bundle.shelters,
        "earthquake_shelters": bundle.earthquake_shelters,
        "tsunami_shelters": bundle.tsunami_shelters,
    }

    # dict 리스트 형태를 쓰는 이유는 홈과 설명 페이지가 같은 데이터를 바로 순회해 불릿/카드를 만들기 쉽기 때문이다.
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
