import pandas as pd


def test_load_crawled_alerts_dataframe_adds_derived_columns(
    message_guidance_page_module,
    sample_preprocessing_dir,
) -> None:
    alerts = message_guidance_page_module.load_crawled_alerts_dataframe_uncached(sample_preprocessing_dir)

    assert pd.api.types.is_datetime64_any_dtype(alerts["발표시각"])
    assert {"시군구정규화", "재난그룹", "alert_key"}.issubset(alerts.columns)
    assert alerts.iloc[0]["alert_key"]
    assert alerts.loc[alerts["재난종류"] == "해일", "재난그룹"].iloc[0] == "해일/쓰나미"
    assert alerts.loc[alerts["재난종류"] == "풍랑", "재난그룹"].iloc[0] == "강풍/풍랑"


def test_map_crawled_disaster_group_maps_expected_values(message_guidance_page_module) -> None:
    assert message_guidance_page_module.map_crawled_disaster_group("호우") == "호우/태풍"
    assert message_guidance_page_module.map_crawled_disaster_group("태풍") == "호우/태풍"
    assert message_guidance_page_module.map_crawled_disaster_group("해일") == "해일/쓰나미"
    assert message_guidance_page_module.map_crawled_disaster_group("지진해일") == "해일/쓰나미"
    assert message_guidance_page_module.map_crawled_disaster_group("황사") == "기타"


def test_get_recent_crawled_alerts_prefers_sigungu_and_falls_back_to_region(
    message_guidance_page_module,
    sample_preprocessing_dir,
) -> None:
    alerts = message_guidance_page_module.load_crawled_alerts_dataframe_uncached(sample_preprocessing_dir)

    local_recent = message_guidance_page_module.get_recent_crawled_alerts(
        alerts,
        sido="경북",
        sigungu="포항시",
        limit=5,
    )
    regional_recent = message_guidance_page_module.get_recent_crawled_alerts(
        alerts,
        sido="경북",
        sigungu="안동시",
        limit=5,
    )

    assert len(local_recent) == 2
    assert local_recent.iloc[0]["재난종류"] == "호우"
    assert len(regional_recent) == 2
    assert set(regional_recent["지역"]) == {"경북"}


def test_select_default_crawled_alert_returns_latest_matching_row(
    message_guidance_page_module,
    sample_preprocessing_dir,
) -> None:
    alerts = message_guidance_page_module.load_crawled_alerts_dataframe_uncached(sample_preprocessing_dir)
    selected = message_guidance_page_module.select_default_crawled_alert(alerts, "경북", "포항시")

    assert selected is not None
    assert selected["재난종류"] == "호우"
    assert selected["재난그룹"] == "호우/태풍"
