"""disaster_data 서비스 모듈의 경로 해석과 데이터 로딩을 검증하는 테스트.

이 테스트 파일은 외부 전처리 폴더를 읽는 서비스가
경로 탐색, CSV 로딩, 지역 요약 계약을 계속 지키는지 확인한다.

초보자 메모:
- 추천 페이지가 잘 보이려면 그 전에 데이터 폴더 탐색과 CSV 표준화가 먼저 안정적이어야 한다.
- 그래서 이 파일은 화면보다 아래쪽 계층인 데이터 서비스의 약속을 세밀하게 확인한다.
"""

from __future__ import annotations

from pathlib import Path

from dashboard.services import disaster_data
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


def test_resolve_data_dir_prefers_env_over_secret_and_repo_local(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """환경변수가 secrets 와 저장소 기본 경로보다 우선하는지 확인한다."""

    env_dir = tmp_path / "env_data"
    secret_dir = tmp_path / "secret_data"
    repo_dir = tmp_path / "repo_data"
    desktop_dir = tmp_path / "desktop_data"
    for path in [env_dir, secret_dir, repo_dir, desktop_dir]:
        path.mkdir()

    monkeypatch.setenv("PREPROCESSING_DATA_DIR", str(env_dir))
    monkeypatch.setattr(disaster_data, "_maybe_get_secret_data_dir", lambda: str(secret_dir))
    monkeypatch.setattr(disaster_data, "_get_repo_default_data_dir", lambda: repo_dir)
    monkeypatch.setattr(disaster_data, "_get_desktop_default_data_dir", lambda: desktop_dir)
    # monkeypatch 는 테스트 중에만 함수와 환경변수를 임시로 바꿔 실제 시스템 상태에 의존하지 않게 만든다.

    assert resolve_data_dir() == env_dir.resolve()


def test_resolve_data_dir_prefers_secret_over_repo_local(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """환경변수가 없을 때 secrets 가 저장소 기본 경로보다 우선하는지 확인한다."""

    secret_dir = tmp_path / "secret_data"
    repo_dir = tmp_path / "repo_data"
    desktop_dir = tmp_path / "desktop_data"
    for path in [secret_dir, repo_dir, desktop_dir]:
        path.mkdir()

    monkeypatch.delenv("PREPROCESSING_DATA_DIR", raising=False)
    monkeypatch.setattr(disaster_data, "_maybe_get_secret_data_dir", lambda: str(secret_dir))
    monkeypatch.setattr(disaster_data, "_get_repo_default_data_dir", lambda: repo_dir)
    monkeypatch.setattr(disaster_data, "_get_desktop_default_data_dir", lambda: desktop_dir)

    assert resolve_data_dir() == secret_dir.resolve()


def test_resolve_data_dir_uses_repo_local_default_when_no_override(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """아무 설정이 없으면 저장소 내부 기본 경로를 사용한다."""

    repo_dir = tmp_path / "repo_data"
    desktop_dir = tmp_path / "desktop_data"
    repo_dir.mkdir()
    desktop_dir.mkdir()

    monkeypatch.delenv("PREPROCESSING_DATA_DIR", raising=False)
    monkeypatch.setattr(disaster_data, "_maybe_get_secret_data_dir", lambda: None)
    monkeypatch.setattr(disaster_data, "_get_repo_default_data_dir", lambda: repo_dir)
    monkeypatch.setattr(disaster_data, "_get_desktop_default_data_dir", lambda: desktop_dir)

    assert resolve_data_dir() == repo_dir.resolve()


def test_resolve_data_dir_falls_back_to_desktop_after_repo_local(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """저장소 기본 경로가 없을 때만 Desktop fallback 으로 내려간다."""

    repo_dir = tmp_path / "missing_repo_data"
    desktop_dir = tmp_path / "Desktop" / "preprocessing_data"
    desktop_dir.mkdir(parents=True)

    monkeypatch.delenv("PREPROCESSING_DATA_DIR", raising=False)
    monkeypatch.setattr(disaster_data, "_maybe_get_secret_data_dir", lambda: None)
    monkeypatch.setattr(disaster_data, "_get_repo_default_data_dir", lambda: repo_dir)
    monkeypatch.setattr(disaster_data, "_get_desktop_default_data_dir", lambda: desktop_dir)

    assert resolve_data_dir() == desktop_dir.resolve()


def test_load_dataset_bundle_reports_missing_runtime_csv(tmp_path: Path) -> None:
    """런타임 CSV 가 비었을 때 누락 파일과 override 방법을 함께 알려 준다."""

    missing_base = tmp_path / "preprocessing_data"
    (missing_base / "preprocessing").mkdir(parents=True)

    try:
        load_dataset_bundle_uncached(missing_base)
    except FileNotFoundError as exc:
        message = str(exc)
    else:
        raise AssertionError("missing runtime csv should raise FileNotFoundError")

    # 오류 메시지 안에 override 방법까지 들어 있는지 보는 이유는
    # 단순 실패보다 "사용자가 다음에 무엇을 해야 하는지"까지 안내해야 하기 때문이다.
    assert "전처리 데이터 파일이 없다" in message
    assert "PREPROCESSING_DATA_DIR" in message


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

    # 여기서 보고 싶은 핵심은 정확한 미터 단위 오차가 아니라 "가장 가까운 감지 지역이 올바른가"다.
    assert pohang_region["sido"] == "경북"
    assert pohang_region["sigungu"] == "포항시"
    assert pohang_region["source"] == "auto_detected"
    assert andong_region["sido"] == "경북"
    assert andong_region["sigungu"] == "안동시"
