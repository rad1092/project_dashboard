"""analysis_data 서비스 모듈의 기본 동작을 검증하는 테스트.

이 파일은 샘플 데이터 스키마와 KPI 계산 규칙이 바뀌지 않았는지 확인한다.
분석 페이지가 기대하는 데이터 구조가 깨지면 가장 먼저 여기서 감지할 수 있다.
"""

from __future__ import annotations

import pandas as pd

from dashboard.services.analysis_data import REQUIRED_COLUMNS, build_kpis, load_demo_dataset


def test_load_demo_dataset_has_expected_columns() -> None:
    """데모 데이터가 기대하는 컬럼 구조와 기본 크기를 유지하는지 확인한다."""
    dataframe = load_demo_dataset()

    # 컬럼 순서까지 고정해야 화면 코드와 테스트가 같은 스키마를 공유한다.
    assert list(dataframe.columns) == REQUIRED_COLUMNS
    assert len(dataframe) == 64
    assert dataframe["project"].nunique() == 4


def test_build_kpis_returns_summary_values() -> None:
    """KPI 계산 함수가 유효한 요약 값을 반환하는지 확인한다."""
    dataframe = load_demo_dataset(seed=7)
    summary = build_kpis(dataframe)

    # 평균값과 최신 기간 타입이 올바르게 계산되는지 확인한다.
    assert summary["record_count"] == 64
    assert summary["project_count"] == 4
    assert 0 < summary["avg_conversion_rate"] < 1
    assert summary["avg_impact_score"] > 0
    assert isinstance(summary["latest_period"], pd.Timestamp)


def test_build_kpis_handles_empty_dataframe() -> None:
    """빈 데이터프레임에도 KPI 함수가 같은 키 구조를 반환하는지 확인한다."""
    empty = pd.DataFrame(columns=REQUIRED_COLUMNS)
    summary = build_kpis(empty)

    # 필터 결과가 비어도 페이지가 깨지지 않게 기본 응답 구조를 유지해야 한다.
    assert summary == {
        "record_count": 0,
        "project_count": 0,
        "avg_conversion_rate": 0.0,
        "avg_impact_score": 0.0,
        "latest_period": None,
    }