def test_home_page_meta_and_copy_are_present(home_module) -> None:
    expected_keys = {"home", "simulation", "message_guidance", "analysis", "map"}

    assert expected_keys == set(home_module.PAGE_META.keys())
    assert home_module.PAGE_META["home"]["label"] == "HOME"
    assert home_module.PAGE_META["analysis"]["label"] == "데이터 분석"
    assert home_module.HOME_OVERVIEW_POINTS


def test_home_navigation_contains_five_pages(home_module) -> None:
    pages = home_module.build_navigation()

    assert len(pages) == 5


def test_home_page_kpis_can_be_built_from_analysis_dataset(home_module, sample_preprocessing_dir) -> None:
    analysis_frame = home_module.load_analysis_dataset(sample_preprocessing_dir)
    shelters_frame = home_module.load_shelters_dataframe(sample_preprocessing_dir)
    earthquake_frame = home_module.load_earthquake_shelters_dataframe(sample_preprocessing_dir)
    tsunami_frame = home_module.load_tsunami_shelters_dataframe(sample_preprocessing_dir)
    kpis = home_module.build_kpis(analysis_frame)

    assert len(shelters_frame) == 4
    assert len(earthquake_frame) == 1
    assert len(tsunami_frame) == 1
    assert kpis["alert_count"] == 3
    assert kpis["region_count"] == 2
