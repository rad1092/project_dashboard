def test_live_guidance_page_module_imports(live_guidance_page_module) -> None:
    assert live_guidance_page_module.PAGE_LABEL == "실시간 대피 안내"
    assert hasattr(live_guidance_page_module, "render_page")
    assert hasattr(live_guidance_page_module, "resolve_region_alert_state")


def test_live_guidance_card_html_matches_simulation_scale(
    live_guidance_page_module,
    simulation_page_module,
) -> None:
    rows = [
        ("대피소 계열", "지진대피장소"),
        ("실경로 거리", "1.91 km"),
        ("주소", "울산광역시 북구 화동로 47(화봉동)"),
        ("예상 시간", "3분"),
    ]

    live_html = live_guidance_page_module.build_shelter_summary_card_html(
        "화봉고등학교 운동장",
        rows,
        accent_color="#0f766e",
        note="OSRM 경로 확인이 안 돼 직선 fallback 결과를 표시 중입니다.",
    )
    simulation_html = simulation_page_module.build_shelter_summary_card_html(
        "화봉고등학교 운동장",
        rows,
        accent_color="#0f766e",
        note="OSRM 경로 확인이 안 돼 직선 fallback 결과를 표시 중입니다.",
    )

    assert live_html == simulation_html


def test_live_guidance_shelter_info_panel_uses_borderless_container(
    live_guidance_page_module,
) -> None:
    assert live_guidance_page_module._get_shelter_info_panel_kwargs() == {
        "border": False,
        "height": live_guidance_page_module.SHOWCASE_PANEL_HEIGHT_PX,
    }


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
        "경북",
        "포항시",
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


def test_build_current_alert_summary_contains_expected_fields(
    live_guidance_page_module,
    sample_preprocessing_dir,
) -> None:
    crawled_alerts = live_guidance_page_module.load_crawled_alerts_dataframe_uncached(
        sample_preprocessing_dir
    )
    selected = live_guidance_page_module.select_default_crawled_alert(
        crawled_alerts,
        "경북",
        "포항시",
    )

    summary = live_guidance_page_module.build_current_alert_summary(
        selected,
        source=live_guidance_page_module.CRAWLED_ALERT_SOURCE_MOCK,
    )

    assert summary is not None
    assert summary["published_at"] == "2026-03-06 14:00"
    assert summary["disaster_type"] == "호우"
    assert summary["alert_level"] == "경보"
    assert summary["location"] == "경북 포항"
    assert summary["sender"] == "포항시"
    assert "포항 호우 경보 발령" in summary["content"]
    assert summary["source_label"] == "모의"


def test_build_current_alert_summary_card_html_renders_compact_strip(
    live_guidance_page_module,
    sample_preprocessing_dir,
) -> None:
    crawled_alerts = live_guidance_page_module.load_crawled_alerts_dataframe_uncached(
        sample_preprocessing_dir
    )
    selected = live_guidance_page_module.select_default_crawled_alert(
        crawled_alerts,
        "경북",
        "포항시",
    )
    summary = live_guidance_page_module.build_current_alert_summary(
        selected,
        source=live_guidance_page_module.CRAWLED_ALERT_SOURCE_MOCK,
    )

    assert summary is not None

    html = live_guidance_page_module.build_current_alert_summary_card_html(summary)

    assert "pd-current-alert-strip" in html
    assert "모의" in html
    assert "호우 / 경보" in html
    assert "경북 포항" in html
    assert "2026-03-06 14:00" in html
    assert "포항시" in html
    assert "내용" in html
    assert "현재 재난문자" not in html
    assert "grid-template-columns: repeat(2, minmax(0, 1fr));" not in html


def test_build_recent_alert_display_frame_formats_expected_columns(
    live_guidance_page_module,
    sample_preprocessing_dir,
) -> None:
    crawled_alerts = live_guidance_page_module.load_crawled_alerts_dataframe_uncached(
        sample_preprocessing_dir
    )
    recent_alerts = live_guidance_page_module.get_recent_crawled_alerts(
        crawled_alerts,
        sido="경북",
        sigungu="포항시",
        limit=5,
    )

    display_frame = live_guidance_page_module.build_recent_alert_display_frame(recent_alerts)

    assert list(display_frame.columns) == [
        live_guidance_page_module.PUBLISHED_AT_COLUMN,
        live_guidance_page_module.DISASTER_TYPE_COLUMN,
        live_guidance_page_module.ALERT_LEVEL_COLUMN,
        live_guidance_page_module.SIGUNGU_COLUMN,
    ]
    assert display_frame.iloc[0][live_guidance_page_module.PUBLISHED_AT_COLUMN] == "2026-03-06 14:00"
    assert display_frame.iloc[0][live_guidance_page_module.DISASTER_TYPE_COLUMN] == "호우"
