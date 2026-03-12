def test_message_guidance_page_module_imports(message_guidance_page_module) -> None:
    assert message_guidance_page_module.PAGE_LABEL == "재난문자 대피 안내"
    assert hasattr(message_guidance_page_module, "render_page")
    assert hasattr(message_guidance_page_module, "resolve_region_alert_state")


def test_message_guidance_region_state_handles_supported_and_unsupported_regions(
    crawler_alerts_data_module,
    message_guidance_page_module,
    sample_preprocessing_dir,
) -> None:
    crawled_alerts = crawler_alerts_data_module.load_crawled_alerts_dataframe_uncached(sample_preprocessing_dir)

    supported, recent_alerts, default_alert = message_guidance_page_module.resolve_region_alert_state(
        crawled_alerts,
        "경북",
        "포항시",
    )
    unsupported, unsupported_alerts, unsupported_default = message_guidance_page_module.resolve_region_alert_state(
        crawled_alerts,
        "인천",
        "남동구",
    )
    empty_supported, empty_recent, empty_default = message_guidance_page_module.resolve_region_alert_state(
        crawled_alerts,
        "대구",
        "중구",
    )

    assert supported is True
    assert len(recent_alerts) == 2
    assert default_alert is not None
    assert default_alert["재난종류"] == "호우"
    assert unsupported is False
    assert unsupported_alerts.empty
    assert unsupported_default is None
    assert empty_supported is True
    assert empty_recent.empty
    assert empty_default is None


def test_message_guidance_selected_alert_can_drive_recommendations(
    crawler_alerts_data_module,
    recommendation_page_module,
    sample_preprocessing_dir,
) -> None:
    crawled_alerts = crawler_alerts_data_module.load_crawled_alerts_dataframe_uncached(sample_preprocessing_dir)
    selected = crawler_alerts_data_module.select_default_crawled_alert(crawled_alerts, "경북", "포항시")
    shelters_frame = recommendation_page_module.load_shelters_dataframe_uncached(sample_preprocessing_dir)
    earthquake_shelters_frame = recommendation_page_module.load_earthquake_shelters_dataframe_uncached(
        sample_preprocessing_dir
    )
    tsunami_shelters_frame = recommendation_page_module.load_tsunami_shelters_dataframe_uncached(
        sample_preprocessing_dir
    )

    recommendations = recommendation_page_module.recommend_shelters(
        shelters_frame=shelters_frame,
        earthquake_shelters_frame=earthquake_shelters_frame,
        tsunami_shelters_frame=tsunami_shelters_frame,
        disaster_group=str(selected["재난그룹"]),
        latitude=36.02,
        longitude=129.34,
        sido="경북",
        sigungu="포항시",
    )

    assert list(recommendations.columns) == recommendation_page_module.RECOMMENDATION_RESULT_COLUMNS
    assert not recommendations.empty
