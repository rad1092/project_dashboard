"""disaster_data 서비스 모듈의 경로 해석과 데이터 로딩을 검증하는 테스트.

이 테스트 파일은 외부 전처리 폴더를 읽는 서비스가
경로 탐색, CSV 로딩, 지역 요약 계약을 계속 지키는지 확인한다.
"""

from __future__ import annotations

from dashboard.services.disaster_data import (
    build_alert_summary,
    build_dataset_catalog,
    infer_region_from_coordinates,
    get_recent_alerts,
    get_region_center,
    load_dataset_bundle_uncached,
    resolve_data_dir,
)


def test_resolve_data_dir_uses_override(sample_preprocessing_dir) -> None:
    """함수 인자로 넘긴 경로를 가장 우선해서 사용하는지 확인한다."""

    # override 우선순위가 깨지면 테스트와 로컬 실행이 모두 Desktop 기본 경로에 종속될 수 있다.
    assert resolve_data_dir(sample_preprocessing_dir) == sample_preprocessing_dir.resolve()


def test_load_dataset_bundle_reads_expected_frames(sample_preprocessing_dir) -> None:
    """전처리 폴더에서 네 종류 CSV 를 모두 읽는지 확인한다."""

    # 번들 객체가 비면 이후 페이지 대부분이 함께 깨지므로 묶음 로딩 자체를 먼저 검증한다.
    bundle = load_dataset_bundle_uncached(sample_preprocessing_dir)
    assert len(bundle.alerts) == 3
    assert len(bundle.shelters) == 4
    assert len(bundle.earthquake_shelters) == 1
    assert len(bundle.tsunami_shelters) == 1


def test_recent_alerts_and_summary_follow_region(sample_preprocessing_dir) -> None:
    """선택 지역 기준 최근 특보와 요약 정보가 올바르게 정렬되는지 확인한다."""

    bundle = load_dataset_bundle_uncached(sample_preprocessing_dir)
    recent = get_recent_alerts(bundle, sido="경북", sigungu="포항시", limit=2)
    summary = build_alert_summary(bundle, sido="경북", sigungu="포항시")

    assert len(recent) == 2
    assert recent.iloc[0]["재난종류"] == "호우"
    assert summary["latest_disaster"] == "호우"
    assert "풍랑" in summary["hazards"]


def test_dataset_catalog_and_region_center(sample_preprocessing_dir) -> None:
    """데이터셋 설명 정보와 지역 중심 좌표가 만들어지는지 확인한다."""

    bundle = load_dataset_bundle_uncached(sample_preprocessing_dir)
    catalog = build_dataset_catalog(bundle, sample_preprocessing_dir)
    latitude, longitude = get_region_center(bundle, "경북", "포항시")

    # catalog 길이와 중심 좌표 존재 여부를 같이 보는 이유는 설명 페이지 계약과 추천 페이지 보조 기능을 한 번에 보호하기 위해서다.
    assert len(catalog) == 4
    assert latitude is not None
    assert longitude is not None


def test_infer_region_from_coordinates_uses_nearest_region_center(sample_preprocessing_dir) -> None:
    """좌표 입력 기준으로 가장 가까운 지역 중심을 자동 감지하는지 확인한다."""

    bundle = load_dataset_bundle_uncached(sample_preprocessing_dir)

    # 포항 근처 좌표는 포항시, 안동 근처 좌표는 안동시로 감지돼야
    # 추천 페이지가 지역 드롭다운 없이도 같은 active region 을 만들 수 있다.
    pohang_region = infer_region_from_coordinates(bundle, latitude=36.0205, longitude=129.3440)
    andong_region = infer_region_from_coordinates(bundle, latitude=36.5683, longitude=128.7291)

    assert pohang_region["sido"] == "경북"
    assert pohang_region["sigungu"] == "포항시"
    assert pohang_region["source"] == "auto_detected"
    assert andong_region["sido"] == "경북"
    assert andong_region["sigungu"] == "안동시"
