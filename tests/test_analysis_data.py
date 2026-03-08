"""analysis_data 모듈의 분석용 데이터 계약을 검증하는 테스트.

이 테스트 파일은 분석 페이지와 홈 화면이 같은 KPI/컬럼 계약을 공유하는지 확인한다.
즉, 분석 데이터 준비 모듈이 바뀌어도 차트와 카드가 기대하는 구조가 유지되는지를 보호한다.
"""

from __future__ import annotations

import pandas as pd

from dashboard.services.analysis_data import ANALYSIS_COLUMNS, build_kpis, load_analysis_dataset


def test_load_analysis_dataset_has_expected_columns(sample_preprocessing_dir) -> None:
    """분석용 특보 DataFrame 이 기대 컬럼 구조를 유지하는지 확인한다."""

    # 분석 차트는 이 열 순서를 그대로 기대하므로 컬럼 계약을 먼저 검증한다.
    dataframe = load_analysis_dataset(sample_preprocessing_dir)
    assert list(dataframe.columns) == ANALYSIS_COLUMNS
    assert len(dataframe) == 3
    assert dataframe["재난그룹"].isin({"강풍/풍랑", "호우/태풍", "폭염"}).all()


def test_build_kpis_returns_summary_values(sample_preprocessing_dir) -> None:
    """기본 KPI 계산이 건수, 경보 수, 최신 시각을 올바르게 반환하는지 확인한다."""

    dataframe = load_analysis_dataset(sample_preprocessing_dir)
    summary = build_kpis(dataframe)

    # 이 값들은 홈 KPI 와 분석 화면 카드가 기대하는 실제 숫자 계약이다.
    assert summary["alert_count"] == 3
    assert summary["disaster_count"] == 3
    assert summary["region_count"] == 2
    assert summary["warning_count"] == 1
    assert isinstance(summary["latest_period"], pd.Timestamp)


def test_build_kpis_handles_empty_dataframe() -> None:
    """빈 데이터프레임에도 같은 KPI 키 구조를 반환하는지 확인한다."""

    # 빈 결과에서도 같은 키 구조를 유지해야 카드 UI 가 예외 없이 렌더링된다.
    empty = pd.DataFrame(columns=ANALYSIS_COLUMNS)
    summary = build_kpis(empty)

    assert summary == {
        "alert_count": 0,
        "disaster_count": 0,
        "region_count": 0,
        "warning_count": 0,
        "latest_period": None,
    }
