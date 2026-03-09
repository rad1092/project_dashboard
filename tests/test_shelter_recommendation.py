"""shelter_recommendation 모듈의 데이터 계약과 추천 규칙을 검증하는 테스트.

이 테스트 파일은 단순히 값 몇 개를 보는 것이 아니라,
추천 서비스가 어떤 재난 유형에서도 같은 반환 컬럼 계약을 지키는지를 보호한다.
특히 지진/해일 전용 대피장소는 원본 CSV 컬럼이 다르기 때문에,
표시용 `대피소유형` 합성과 표준 컬럼 보장이 깨지지 않는지 확인하는 것이 중요하다.

초보자 메모:
- 추천 결과는 카드, 표, 지도에서 동시에 쓰이기 때문에 "값"뿐 아니라 "컬럼 구조"도 중요한 계약이다.
- 이 파일은 전용 대피소 우선 규칙과 fallback 규칙이 계속 유지되는지 확인한다.
"""

from __future__ import annotations

from dashboard.services.disaster_data import load_dataset_bundle_uncached
from dashboard.services.shelter_recommendation import (
    RECOMMENDATION_RESULT_COLUMNS,
    classify_disaster_type,
    haversine_km,
    recommend_shelters,
)


def test_classify_disaster_type_maps_known_labels() -> None:
    """원본 재난 명칭이 내부 그룹으로 정규화되는지 확인한다."""

    # 이 매핑이 흔들리면 selectbox 옵션, 분석 범례, 추천 규칙이 한꺼번에 어긋난다.
    assert classify_disaster_type("풍랑") == "강풍/풍랑"
    assert classify_disaster_type("호우") == "호우/태풍"
    assert classify_disaster_type("폭염") == "폭염"


def test_haversine_km_returns_positive_distance() -> None:
    """서로 다른 좌표 사이 거리가 0보다 큰 값으로 계산되는지 확인한다."""

    distance = haversine_km(35.1796, 129.0756, 35.538, 129.312)
    # 정확한 실측 거리까지 보지 않더라도, 기본 거리 계산이 음수/0으로 깨지지 않는 계약을 먼저 확인한다.
    # 이런 테스트는 계산식 전체를 외우지 않아도 "말이 안 되는 결과"를 빠르게 잡아 주는 역할을 한다.
    assert distance > 0


def test_recommend_shelters_prefers_dedicated_candidates(sample_preprocessing_dir) -> None:
    """지진은 지진대피장소 전용 후보를 먼저 추천하고 표시용 유형도 채우는지 확인한다."""

    # sample_preprocessing_dir 는 pytest fixture 가 만든 임시 CSV 폴더 경로로, 테스트마다 같은 샘플 데이터를 안전하게 재사용하게 해 준다.
    bundle = load_dataset_bundle_uncached(sample_preprocessing_dir)
    recommendations = recommend_shelters(
        bundle=bundle,
        disaster_group="지진",
        latitude=36.02,
        longitude=129.34,
        sido="경북",
        sigungu="포항시",
    )

    # 이 검증은 전용 CSV 의 누락 컬럼을 서비스가 보완해 주는지까지 함께 확인한다.
    # recommendations 는 DataFrame 이라 첫 번째 행은 iloc[0] 으로 읽는다.
    assert not recommendations.empty
    # list(recommendations.columns) 로 바꾸면 컬럼 이름뿐 아니라 순서까지 함께 비교할 수 있다.
    assert list(recommendations.columns) == RECOMMENDATION_RESULT_COLUMNS
    assert recommendations.iloc[0]["추천구분"] == "전용 대피소"
    assert recommendations.iloc[0]["대피소유형"] == "지진대피장소"


def test_recommend_shelters_uses_tsunami_dedicated_label(sample_preprocessing_dir) -> None:
    """지진해일/쓰나미는 해일대피장소 전용 후보를 먼저 추천하는지 확인한다."""

    bundle = load_dataset_bundle_uncached(sample_preprocessing_dir)
    recommendations = recommend_shelters(
        bundle=bundle,
        disaster_group="지진해일/쓰나미",
        latitude=36.02,
        longitude=129.34,
        sido="경북",
        sigungu="포항시",
    )

    # 지진해일 전용 CSV 도 통합 CSV 와 다른 스키마를 가지므로, 전용 라벨과 표준 컬럼 계약을 함께 본다.
    assert not recommendations.empty
    # list(recommendations.columns) 로 바꾸면 컬럼 이름뿐 아니라 순서까지 함께 비교할 수 있다.
    assert list(recommendations.columns) == RECOMMENDATION_RESULT_COLUMNS
    assert recommendations.iloc[0]["추천구분"] == "전용 대피소"
    assert recommendations.iloc[0]["대피소유형"] == "해일대피장소"


def test_recommend_shelters_uses_fallback_when_needed(sample_preprocessing_dir) -> None:
    """전용 후보가 없거나 정의가 없는 재난은 통합/일반 대피장소로 fallback 하는지 확인한다."""

    bundle = load_dataset_bundle_uncached(sample_preprocessing_dir)
    recommendations = recommend_shelters(
        bundle=bundle,
        disaster_group="호우/태풍",
        latitude=36.02,
        longitude=129.34,
        sido="경북",
        sigungu="포항시",
    )

    # fallback 테스트는 단순히 값이 있는지만 보는 것이 아니라
    # 전용 후보가 없는 재난도 같은 반환 컬럼 계약을 유지하는지 확인하는 의미가 있다.
    # {"기본 대피소", "대체 대피소"} 같은 집합은 허용 후보 묶음을 표현하기 좋아, in 검사와 자주 함께 쓴다.
    # in {...} 검사는 추천구분이 허용된 여러 값 중 하나인지 볼 때 가장 간단한 패턴이다.
    assert not recommendations.empty
    # list(recommendations.columns) 로 바꾸면 컬럼 이름뿐 아니라 순서까지 함께 비교할 수 있다.
    assert list(recommendations.columns) == RECOMMENDATION_RESULT_COLUMNS
    assert recommendations.iloc[0]["추천구분"] in {"기본 대피소", "대체 대피소"}
