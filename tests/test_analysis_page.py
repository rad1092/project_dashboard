"""분석 페이지 내부 데이터 준비와 KPI 계산을 검증하는 테스트."""

from __future__ import annotations


def test_load_analysis_dataset_has_expected_columns(
    analysis_page_module,
    sample_preprocessing_dir,
) -> None:
    dataframe = analysis_page_module.load_analysis_dataset(sample_preprocessing_dir)

    assert list(dataframe.columns) == analysis_page_module.ANALYSIS_COLUMNS
    assert len(dataframe) == 3
    assert set(dataframe["재난그룹"]) == {"강풍/풍랑", "호우/태풍", "폭염"}


def test_build_kpis_returns_summary_values(
    analysis_page_module,
    sample_preprocessing_dir,
) -> None:
    dataframe = analysis_page_module.load_analysis_dataset(sample_preprocessing_dir)
    kpis = analysis_page_module.build_kpis(dataframe)

    assert kpis["alert_count"] == 3
    assert kpis["disaster_count"] == 3
    assert kpis["region_count"] == 2
    assert kpis["warning_count"] == 1
    assert str(kpis["latest_period"])[:16] == "2026-03-06 13:00"


def test_chart_builders_return_figures(analysis_page_module, sample_preprocessing_dir) -> None:
    dataframe = analysis_page_module.load_analysis_dataset(sample_preprocessing_dir)
    shelters_frame = analysis_page_module.load_shelters_dataframe_uncached(sample_preprocessing_dir)

    trend = analysis_page_module.build_alert_trend_chart(dataframe)
    region = analysis_page_module.build_region_alert_chart(dataframe)
    hazard = analysis_page_module.build_hazard_share_chart(dataframe)
    shelter = analysis_page_module.build_shelter_type_chart(shelters_frame)

    assert trend.data
    assert region.data
    assert hazard.data
    assert shelter.data
