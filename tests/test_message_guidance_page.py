def test_live_guidance_page_module_imports(live_guidance_page_module) -> None:
    assert live_guidance_page_module.PAGE_LABEL == "실시간 대피 안내"
    assert hasattr(live_guidance_page_module, "render_page")
    assert hasattr(live_guidance_page_module, "resolve_region_alert_state")


def test_message_guidance_region_state_handles_supported_and_unsupported_regions(
    live_guidance_page_module,
    sample_preprocessing_dir,
) -> None:
    crawled_alerts = live_guidance_page_module.load_crawled_alerts_dataframe_uncached(
        sample_preprocessing_dir
    )
    sample_row = crawled_alerts.iloc[0]

    supported, recent_alerts, default_alert = live_guidance_page_module.resolve_region_alert_state(
        crawled_alerts,
        str(sample_row[live_guidance_page_module.REGION_COLUMN]),
        str(sample_row[live_guidance_page_module.SIGUNGU_COLUMN]),
    )
    unsupported, unsupported_alerts, unsupported_default = (
        live_guidance_page_module.resolve_region_alert_state(
            crawled_alerts,
            "인천",
            "중구",
        )
    )

    assert supported is True
    assert not recent_alerts.empty
    assert default_alert is not None
    assert unsupported is False
    assert unsupported_alerts.empty
    assert unsupported_default is None


def test_message_guidance_selected_alert_can_drive_recommendations(
    live_guidance_page_module,
    sample_preprocessing_dir,
) -> None:
    crawled_alerts = live_guidance_page_module.load_crawled_alerts_dataframe_uncached(
        sample_preprocessing_dir
    )
    selected = live_guidance_page_module.select_default_crawled_alert(
        crawled_alerts,
        str(crawled_alerts.iloc[0][live_guidance_page_module.REGION_COLUMN]),
        str(crawled_alerts.iloc[0][live_guidance_page_module.SIGUNGU_COLUMN]),
    )
    shelters_frame = live_guidance_page_module.load_shelters_dataframe_uncached(
        sample_preprocessing_dir
    )
    earthquake_shelters_frame = live_guidance_page_module.load_earthquake_shelters_dataframe_uncached(
        sample_preprocessing_dir
    )
    tsunami_shelters_frame = live_guidance_page_module.load_tsunami_shelters_dataframe_uncached(
        sample_preprocessing_dir
    )

    recommendations = live_guidance_page_module.recommend_shelters(
        shelters_frame=shelters_frame,
        earthquake_shelters_frame=earthquake_shelters_frame,
        tsunami_shelters_frame=tsunami_shelters_frame,
        disaster_group=str(selected[live_guidance_page_module.DISASTER_GROUP_COLUMN]),
        latitude=36.02,
        longitude=129.34,
        sido=str(crawled_alerts.iloc[0][live_guidance_page_module.REGION_COLUMN]),
        sigungu=str(crawled_alerts.iloc[0][live_guidance_page_module.SIGUNGU_COLUMN]),
    )

    assert list(recommendations.columns) == live_guidance_page_module.RECOMMENDATION_RESULT_COLUMNS
    assert not recommendations.empty
