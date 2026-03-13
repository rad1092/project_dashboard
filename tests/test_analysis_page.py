def test_load_analysis_dataset_has_expected_columns(
    analysis_page_module,
    sample_preprocessing_dir,
) -> None:
    dataframe = analysis_page_module.load_analysis_dataset(sample_preprocessing_dir)

    assert list(dataframe.columns) == analysis_page_module.ANALYSIS_COLUMNS
    assert len(dataframe) == 3
    assert set(dataframe["재난종류"]) == {"강풍", "호우", "태풍"}


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


def test_filter_analysis_dataset_uses_region_disaster_and_grade(
    analysis_page_module,
    sample_preprocessing_dir,
) -> None:
    dataframe = analysis_page_module.load_analysis_dataset(sample_preprocessing_dir)
    filtered = analysis_page_module.filter_analysis_dataset(
        dataframe,
        selected_regions=["경북"],
        selected_disasters=["호우"],
        selected_grades=["경보"],
    )

    assert len(filtered) == 1
    assert filtered.iloc[0]["지역"] == "경북"
    assert filtered.iloc[0]["재난종류"] == "호우"
    assert filtered.iloc[0]["특보등급"] == "경보"


def test_chart_builders_return_figures(analysis_page_module, sample_preprocessing_dir) -> None:
    dataframe = analysis_page_module.load_analysis_dataset(sample_preprocessing_dir)
    shelters_frame = analysis_page_module.load_shelters_dataframe_uncached(sample_preprocessing_dir)

    figures = [
        analysis_page_module.build_top_regions_by_disaster_chart(dataframe),
        analysis_page_module.build_grade_distribution_chart(dataframe),
        analysis_page_module.build_daily_disaster_trend_chart(dataframe),
        analysis_page_module.build_monthly_distribution_chart(dataframe),
        analysis_page_module.build_region_disaster_counts_chart(dataframe),
        analysis_page_module.build_region_disaster_ratio_heatmap(dataframe),
        analysis_page_module.build_shelter_type_distribution_chart(shelters_frame),
        analysis_page_module.build_region_disaster_vs_shelter_chart(dataframe, shelters_frame),
    ]

    for figure in figures:
        assert figure.data
