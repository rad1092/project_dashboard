def test_home_page_meta_and_copy_are_present(home_module) -> None:
    expected_keys = {
        "home",
        "recommendation",
        "realtime",
        "analysis",
    }

    assert expected_keys.issubset(home_module.PAGE_META.keys())
    assert home_module.HOME_OVERVIEW_POINTS
    assert home_module.LIMITATIONS


def test_home_page_builds_catalog_and_kpis(home_module, sample_preprocessing_dir) -> None:
    # 홈 화면이 쓰는 요약 값은 전부 공용 데이터 모듈을 거쳐 나오므로,
    # 여기서 카탈로그와 KPI가 같이 맞는지 확인해 두면 홈 회귀를 빨리 잡을 수 있다.
    alerts_frame = home_module.load_alerts_dataframe_uncached(sample_preprocessing_dir)
    shelters_frame = home_module.load_shelters_dataframe_uncached(sample_preprocessing_dir)
    earthquake_shelters_frame = home_module.load_earthquake_shelters_dataframe_uncached(
        sample_preprocessing_dir
    )
    tsunami_shelters_frame = home_module.load_tsunami_shelters_dataframe_uncached(sample_preprocessing_dir)
    analysis_frame = home_module.load_analysis_dataset(sample_preprocessing_dir)
    catalog = home_module.build_dataset_catalog(
        alerts_frame=alerts_frame,
        shelters_frame=shelters_frame,
        earthquake_shelters_frame=earthquake_shelters_frame,
        tsunami_shelters_frame=tsunami_shelters_frame,
        path_override=sample_preprocessing_dir,
    )
    kpis = home_module.build_kpis(analysis_frame)

    assert len(catalog) == 4
    assert catalog[0]["name"] == "alerts"
    assert kpis["alert_count"] == 3
    assert kpis["region_count"] == 2


def test_home_page_analysis_dataset_matches_expected_columns(home_module, sample_preprocessing_dir) -> None:
    dataframe = home_module.load_analysis_dataset(sample_preprocessing_dir)
    assert list(dataframe.columns) == home_module.ANALYSIS_COLUMNS
