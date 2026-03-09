"""재난 유형 정규화와 대피소 추천 규칙을 담당하는 서비스 모듈.

왜 필요한가:
- 추천 기준이 페이지 안에 흩어지면 재난 유형을 추가하거나 실시간으로 바꿀 때 유지하기 어렵다.
- 이 모듈은 재난 그룹화, 후보 선택, 거리 계산, 표준 반환 계약을 한곳에 모은다.

누가 사용하는가:
- ``pages/2_대피소_추천.py`` 가 핵심 추천 결과를 만들 때 사용한다.
- ``analysis_data.py`` 는 같은 재난 분류 함수를 재사용한다.

초보자 메모:
- 이 파일이 하는 핵심 일은 "활성 지역과 재난 그룹을 받아 어떤 대피소를 어떤 순서로 보여 줄지" 결정하는 것이다.
- 실제 화면은 pages 에 있지만, 추천 판단 기준은 이 파일 안에 모여 있다.
"""

from __future__ import annotations

import math

import pandas as pd

from dashboard.services.disaster_data import DisasterDatasetBundle, normalize_sigungu_name

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
# 원본 특보 명칭과 내부 그룹 이름을 분리해 두면 CSV 표기가 달라도 추천 규칙은 같은 그룹을 기준으로 움직인다.

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
# 최근 특보가 없는 지역에서도 selectbox 가 비지 않게 하기 위한 기본 목록이다.
# 즉, 실시간/과거 특보가 없더라도 사용자는 최소한 수동 선택을 계속 할 수 있다.

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
# 카드, 표, 지도는 모두 이 표준 컬럼 계약을 기대하므로 서비스가 마지막에 책임지고 맞춘다.


def classify_disaster_type(disaster_name: str | None) -> str:
    """원본 재난 명칭을 내부 그룹으로 정규화한다.

    서로 다른 원본 표기를 몇 개의 내부 그룹으로 묶어 UI 선택지와 추천 규칙을 단순화한다.
    """

    if disaster_name is None:
        return "기타"

    # strip() 을 먼저 하는 이유는 CSV 원문에 남는 공백 때문에 매핑이 실패하는 일을 막기 위해서다.
    text = str(disaster_name).strip()
    # dict.get(key, default) 패턴은 매핑이 없을 때 기본값을 함께 정하는 Python 기본 문법이다.
    return RAW_TO_GROUP.get(text, text if text in DEFAULT_DISASTER_OPTIONS else "기타")


def get_disaster_options(bundle: DisasterDatasetBundle, sido: str, sigungu: str) -> list[str]:
    """활성 지역의 최근 특보와 기본 목록을 합쳐 재난 선택 옵션을 만든다.

    추천 페이지는 좌표 기반 자동 감지나 수동 보정 중 하나를 골라 활성 지역을 만든다.
    이 함수는 그 활성 지역의 최근 특보를 읽어 우선순위를 앞쪽에 두되,
    사용자가 수동으로 고를 기본 목록도 항상 유지한다.
    """

    from dashboard.services.disaster_data import get_recent_alerts

    recent_alerts = get_recent_alerts(bundle, sido=sido, sigungu=sigungu, limit=10)
    # 리스트 컴프리헨션은 최근 특보의 원본 재난명 각각을 내부 그룹명으로 바꾸는 단계다.
    options = [classify_disaster_type(value) for value in recent_alerts["재난종류"].tolist()]
    options.extend(DEFAULT_DISASTER_OPTIONS)

    # 최근 특보 목록과 기본 목록이 겹칠 수 있어, 순서를 유지한 채 중복만 제거한다.
    deduplicated: list[str] = []
    for item in options:
        # set 대신 리스트 중복 제거 방식을 쓰는 이유는 최근 특보 기반 우선순위 순서를 유지해야 하기 때문이다.
        if item not in deduplicated:
            deduplicated.append(item)
    return deduplicated


def select_priority_disaster(bundle: DisasterDatasetBundle, sido: str, sigungu: str) -> str:
    """최근 특보를 기준으로 기본 선택 재난 그룹을 정한다.

    추천 페이지가 열릴 때 기본 재난 선택값을 자동으로 채워 주는 보조 로직이다.
    즉, 좌표로 지역을 감지한 직후 사용자가 바로 첫 결과를 읽을 수 있게 만드는 단계다.
    """

    from dashboard.services.disaster_data import build_alert_summary

    summary = build_alert_summary(bundle, sido=sido, sigungu=sigungu)
    latest_disaster = summary["latest_disaster"]
    if latest_disaster:
        # 최신 특보가 있으면 그 값을 기본 선택값으로 삼고,
        # 없으면 아래 기본 목록 첫 항목으로 내려가는 흐름이다.
        return classify_disaster_type(str(latest_disaster))
    return DEFAULT_DISASTER_OPTIONS[0]


def haversine_km(
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> float:
    """두 위경도 사이의 직선 거리를 km 단위로 계산한다.

    현재 프로젝트 범위에서는 실제 경로가 아니라 비교용 직선 거리를 공통 기준으로 사용한다.
    """

    # 반지름을 km 단위로 두면 결과도 바로 km 로 계산되어 포맷터와 자연스럽게 이어진다.
    earth_radius_km = 6371.0
    # 거리 공식을 위해 위도/경도 차이를 삼각함수에 넣을 수 있는 라디안 값으로 바꾼다.
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
    """시군구 우선, 없으면 시도 기준으로 후보 범위를 조정한다.

    세부 지역 기준 추천을 우선하되, 데이터가 부족하면 같은 시도 후보로 넓혀 빈 결과를 줄인다.
    """

    normalized_sigungu = normalize_sigungu_name(sigungu)
    # 추천 후보가 너무 먼 타 지역으로 튀지 않게, 먼저 시군구 단위 후보를 찾는다.
    local = dataframe[
        (dataframe["시도"] == sido) & (dataframe["시군구정규화"] == normalized_sigungu)
    ]
    if not local.empty:
        # copy() 를 돌려주는 이유는 이후 점수 계산 과정에서 열을 추가해도 원본 후보 DataFrame 을 건드리지 않기 위해서다.
        return local.copy()

    # 시군구 데이터가 부족한 전용 대피소 CSV 도 있어 같은 시도 범위로 한 번 넓혀 본다.
    regional = dataframe[dataframe["시도"] == sido]
    if not regional.empty:
        return regional.copy()

    return dataframe.copy()


def _build_primary_candidates(
    bundle: DisasterDatasetBundle,
    disaster_group: str,
    sido: str,
    sigungu: str,
) -> tuple[pd.DataFrame, str]:
    """재난 그룹에 맞는 전용 후보 집합을 고른다.

    지진과 해일은 전용 대피장소 CSV 가 따로 있으므로 먼저 그 집합을 본다.
    통합/일반 대피장소는 전용 후보가 부족할 때만 보완용으로 붙인다.
    """

    if disaster_group == "지진":
        return _filter_by_region(bundle.earthquake_shelters, sido, sigungu), "전용 대피소"
    if disaster_group == "지진해일/쓰나미":
        return _filter_by_region(bundle.tsunami_shelters, sido, sigungu), "전용 대피소"
    if disaster_group == "폭염":
        # str.contains(..., na=False) 는 결측값이 있어도 에러 없이 문자열 포함 여부를 검사하는 pandas 패턴이다.
        filtered = bundle.shelters[bundle.shelters["대피소유형"].str.contains("무더위쉼터", na=False)]
        return _filter_by_region(filtered, sido, sigungu), "전용 대피소"
    if disaster_group == "한파":
        filtered = bundle.shelters[bundle.shelters["대피소유형"].str.contains("한파쉼터", na=False)]
        return _filter_by_region(filtered, sido, sigungu), "전용 대피소"

    # 빈 DataFrame 을 반환하면 전용 후보가 없는 재난도 같은 추천 함수 안에서 fallback 단계로 자연스럽게 이어진다.
    return pd.DataFrame(), "기본 대피소"


def _build_fallback_candidates(bundle: DisasterDatasetBundle, sido: str, sigungu: str) -> pd.DataFrame:
    """전용 후보가 없거나 부족할 때 사용할 통합/일반 대피장소 후보를 만든다.

    fallback 후보를 별도 단계로 분리해 두면 전용 추천과 대체 추천의 의미가 화면에서 분명해진다.
    """

    return _filter_by_region(bundle.shelters, sido, sigungu)


def _score_candidates(
    dataframe: pd.DataFrame,
    latitude: float,
    longitude: float,
    recommendation_type: str,
    disaster_group: str,
    reason_prefix: str,
) -> pd.DataFrame:
    """후보 대피장소에 거리와 설명 컬럼을 붙여 정렬 가능한 형태로 만든다.

    페이지는 거리뿐 아니라 추천 사유도 같이 보여 줘야 하므로, 표시용 컬럼을 여기서 만든다.
    """

    if dataframe.empty:
        return dataframe.copy()

    scored = dataframe.copy()
    # 각 행마다 사용자 좌표와의 거리를 계산해 같은 정렬 기준으로 묶는다.
    scored["거리_km"] = scored.apply(
        lambda row: haversine_km(latitude, longitude, float(row["위도"]), float(row["경도"])),
        axis=1,
    )
    # apply(..., axis=1) 은 각 행마다 함수 한 번씩 실행해 새 열을 만드는 방식이다.
    # recommendation_type 은 화면에서 "왜 이 후보가 떴는지"를 설명하는 핵심 메타정보라 별도 컬럼으로 남긴다.
    scored["추천구분"] = recommendation_type
    scored["추천사유"] = (
        reason_prefix + disaster_group + " 상황에서 현재 좌표 기준으로 가까운 후보를 우선 정렬했다."
    )
    # to_numeric(...).fillna(0) 는 문자열 숫자나 빈값이 섞여 있어도 정렬용 숫자 열을 안전하게 맞추는 단계다.
    scored["수용인원_정렬값"] = pd.to_numeric(scored["수용인원_정렬값"], errors="coerce").fillna(0)
    return scored


def _ensure_result_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    """추천 결과가 항상 같은 표준 컬럼 집합을 가지도록 맞춘다.

    전용 대피장소와 통합 대피장소는 원본 컬럼 구조가 다르다.
    로딩 단계에서 대부분 맞추더라도, 반환 직전에 한 번 더 필수 컬럼을 보장해 두면
    페이지가 특정 컬럼을 고정적으로 읽어도 바로 깨지지 않는다.
    """

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
        # 이미 값이 있는 컬럼은 유지하고, 누락된 컬럼만 채워 표준 계약을 맞춘다.
        if column not in ensured.columns:
            ensured[column] = default_value

    # 마지막에 원하는 컬럼 순서만 다시 뽑아 주면 표와 카드가 항상 같은 열 순서를 기대할 수 있다.
    return ensured[RECOMMENDATION_RESULT_COLUMNS]


def recommend_shelters(
    bundle: DisasterDatasetBundle,
    disaster_group: str,
    latitude: float,
    longitude: float,
    sido: str,
    sigungu: str,
    top_n: int = 3,
) -> pd.DataFrame:
    """사용자 좌표 기준 추천 대피장소 Top N 을 반환한다.

    우선순위:
    1. 지진/해일 전용 대피장소 또는 재난별 전용 쉼터
    2. 전용 후보가 부족할 때만 통합/일반 대피장소 fallback
    3. 거리 오름차순, 수용인원 내림차순
    """

    # 1차 후보는 재난 그룹에 맞는 전용 대피장소를 우선 조회하는 단계다.
    primary_candidates, primary_label = _build_primary_candidates(
        bundle=bundle,
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
    # len(primary_candidates) < top_n 조건은 "전용 후보가 아예 없지 않아도 수가 부족하면 보완 후보를 붙인다"는 뜻이다.
    # 지진/해일도 전용 후보 수가 부족하면 통합/일반 대피장소를 보완용으로만 붙인다.
    if needs_fallback or len(primary_candidates) < top_n:
        # 전용 후보가 부족한 경우에만 fallback 을 붙여 추천구분 의미를 보존한다.
        fallback_candidates = _build_fallback_candidates(bundle, sido=sido, sigungu=sigungu)
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

    # concat() 은 전용 후보와 fallback 후보를 하나의 긴 표로 합치는 pandas 기본 함수다.
    combined = pd.concat(scored_frames, ignore_index=True)
    # 같은 대피소가 전용/통합 양쪽 데이터에서 동시에 보일 수 있어 이름+주소 기준으로 한 번 더 정리한다.
    combined = combined.drop_duplicates(subset=["대피소명", "주소"])

    # 추천구분 우선순위를 숫자로 바꿔 두면 카드와 표가 같은 정렬 결과를 공유할 수 있다.
    priority_order = {"전용 대피소": 0, "기본 대피소": 1, "대체 대피소": 2}
    combined["추천우선순위"] = combined["추천구분"].map(priority_order).fillna(9)
    combined = combined.sort_values(
        ["추천우선순위", "거리_km", "수용인원_정렬값"],
        ascending=[True, True, False],
    )
    # ascending=[True, True, False] 는 앞의 두 기준은 오름차순, 마지막 수용인원은 내림차순으로 정렬하겠다는 뜻이다.

    # 마지막 반환 지점에서 표준 컬럼을 강제해 두면,
    # 페이지는 어떤 재난 유형이 와도 같은 계약으로 카드와 표를 렌더링할 수 있다.
    standardized = _ensure_result_columns(combined)
    # head(top_n) 를 마지막에 적용해야 전용/대체 후보를 모두 같은 우선순위 규칙으로 정렬한 뒤 상위 N개를 자를 수 있다.
    return standardized.head(top_n).reset_index(drop=True)
