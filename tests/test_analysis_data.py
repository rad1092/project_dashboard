"""analysis_data 모듈의 분석용 데이터 계약을 검증하는 테스트.

이 테스트 파일은 분석 페이지와 홈 화면이 같은 KPI/컬럼 계약을 공유하는지 확인한다.
즉, 분석 데이터 준비 모듈이 바뀌어도 차트와 카드가 기대하는 구조가 유지되는지를 보호한다.

초보자 메모:
- 테스트는 "값이 맞는가"만 보는 것이 아니라 "다른 파일이 믿고 쓰는 약속이 유지되는가"를 확인한다.
- 이 파일은 특히 분석 페이지와 홈 화면이 같은 KPI 계약을 계속 공유하는지 지켜본다.
"""

from __future__ import annotations

import pandas as pd

from dashboard.services.analysis_data import ANALYSIS_COLUMNS, build_kpis, load_analysis_dataset


def test_load_analysis_dataset_has_expected_columns(sample_preprocessing_dir) -> None:
    """분석용 특보 DataFrame 이 기대 컬럼 구조를 유지하는지 확인한다."""

    # 분석 차트는 이 열 순서를 그대로 기대하므로 컬럼 계약을 먼저 검증한다.
    dataframe = load_analysis_dataset(sample_preprocessing_dir)
    # list(dataframe.columns) 처럼 리스트로 바꿔 비교하면 열 순서까지 함께 검증할 수 있다.
    assert list(dataframe.columns) == ANALYSIS_COLUMNS
    assert len(dataframe) == 3
    # isin(...).all() 은 모든 행이 허용된 재난 그룹 집합 안에 들어 있는지 한 번에 확인하는 패턴이다.
    assert dataframe["재난그룹"].isin({"강풍/풍랑", "호우/태풍", "폭염"}).all()


def test_build_kpis_returns_summary_values(sample_preprocessing_dir) -> None:
    """기본 KPI 계산이 건수, 경보 수, 최신 시각을 올바르게 반환하는지 확인한다."""

    dataframe = load_analysis_dataset(sample_preprocessing_dir)
    summary = build_kpis(dataframe)

    # 이 값들은 홈 KPI 와 분석 화면 카드가 기대하는 실제 숫자 계약이다.
    # summary 는 dict 이므로 "키 이름 -> 값" 형태로 필요한 항목을 직접 읽는다.
    assert summary["alert_count"] == 3
    assert summary["disaster_count"] == 3
    assert summary["region_count"] == 2
    assert summary["warning_count"] == 1
    # isinstance(...) 는 값이 날짜 비슷한 문자열이 아니라 실제 Timestamp 객체인지까지 확인한다.
    assert isinstance(summary["latest_period"], pd.Timestamp)


def test_build_kpis_handles_empty_dataframe() -> None:
    """빈 데이터프레임에도 같은 KPI 키 구조를 반환하는지 확인한다."""

    # 빈 결과에서도 같은 키 구조를 유지해야 카드 UI 가 예외 없이 렌더링된다.
    empty = pd.DataFrame(columns=ANALYSIS_COLUMNS)
    # 빈 DataFrame 도 실제 DataFrame 객체이기 때문에, 함수는 예외 대신 0 값 요약을 반환해야 한다.
    summary = build_kpis(empty)

    assert summary == {
        "alert_count": 0,
        "disaster_count": 0,
        "region_count": 0,
        "warning_count": 0,
        "latest_period": None,
    }
