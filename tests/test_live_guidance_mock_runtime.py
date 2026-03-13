from pathlib import Path

import pandas as pd


def test_load_mock_crawled_alerts_dataframe_uncached_generates_derived_columns(
    live_guidance_page_module,
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "preprocessing_code" / "data" / "disaster_message_realtime.csv"

    alerts = live_guidance_page_module.load_mock_crawled_alerts_dataframe_uncached(
        sido="부산",
        sigungu="해운대구",
        output_path=output_path,
    )

    assert len(alerts) == 1
    assert {"시군구정규화", "재난그룹", "alert_key"}.issubset(alerts.columns)
    assert alerts.iloc[0][live_guidance_page_module.REGION_COLUMN] == "부산"
    assert alerts.iloc[0][live_guidance_page_module.SIGUNGU_COLUMN] == "해운대구"
    assert alerts.iloc[0][live_guidance_page_module.DISASTER_GROUP_COLUMN]
    assert alerts.iloc[0][live_guidance_page_module.ALERT_KEY_COLUMN]


def test_get_runtime_crawled_alerts_uses_mock_loader_and_updates_state(
    live_guidance_page_module,
    sample_preprocessing_dir,
) -> None:
    expected_alerts = live_guidance_page_module.load_crawled_alerts_dataframe_uncached(
        sample_preprocessing_dir
    ).head(1)
    session_state: dict[str, object] = {}
    observed_args: dict[str, str] = {}

    def fake_live_loader() -> pd.DataFrame:
        raise AssertionError("live loader should not be used for mock requests")

    def fake_mock_loader(*, sido: str, sigungu: str) -> pd.DataFrame:
        observed_args["sido"] = sido
        observed_args["sigungu"] = sigungu
        return expected_alerts

    alerts, message = live_guidance_page_module._get_runtime_crawled_alerts(
        refresh_requested=False,
        mock_requested=True,
        active_sido="경북",
        active_sigungu="포항시",
        session_state=session_state,
        live_loader=fake_live_loader,
        mock_loader=fake_mock_loader,
    )

    assert message is None
    assert observed_args == {"sido": "경북", "sigungu": "포항시"}
    pd.testing.assert_frame_equal(alerts, expected_alerts)
    pd.testing.assert_frame_equal(
        session_state["message_guidance_live_crawled_alerts"],
        expected_alerts,
    )
    assert session_state["message_guidance_live_crawled_alerts_source"] == "mock"
    assert session_state["message_guidance_live_crawled_alerts_updated_at"] != "-"


def test_get_runtime_crawled_alerts_refreshes_live_and_overrides_mock_source(
    live_guidance_page_module,
    sample_preprocessing_dir,
) -> None:
    live_alerts = live_guidance_page_module.load_crawled_alerts_dataframe_uncached(
        sample_preprocessing_dir
    )
    cached_alerts = live_alerts.head(1)
    session_state: dict[str, object] = {
        "message_guidance_live_crawled_alerts": cached_alerts,
        "message_guidance_live_crawled_alerts_updated_at": "2026-03-13 10:00:00",
        "message_guidance_live_crawled_alerts_source": "mock",
    }

    def fake_live_loader() -> pd.DataFrame:
        return live_alerts

    def fake_mock_loader(*, sido: str, sigungu: str) -> pd.DataFrame:
        raise AssertionError("mock loader should not be used for live refresh")

    alerts, message = live_guidance_page_module._get_runtime_crawled_alerts(
        refresh_requested=True,
        mock_requested=False,
        active_sido="경북",
        active_sigungu="포항시",
        session_state=session_state,
        live_loader=fake_live_loader,
        mock_loader=fake_mock_loader,
    )

    assert message is None
    pd.testing.assert_frame_equal(alerts, live_alerts)
    assert session_state["message_guidance_live_crawled_alerts_source"] == "live"


def test_get_runtime_crawled_alerts_reuses_cached_alerts_for_unsupported_mock_region(
    live_guidance_page_module,
    sample_preprocessing_dir,
) -> None:
    cached_alerts = live_guidance_page_module.load_crawled_alerts_dataframe_uncached(
        sample_preprocessing_dir
    )
    session_state: dict[str, object] = {
        "message_guidance_live_crawled_alerts": cached_alerts,
        "message_guidance_live_crawled_alerts_updated_at": "2026-03-13 10:00:00",
        "message_guidance_live_crawled_alerts_source": "live",
    }

    def fake_live_loader() -> pd.DataFrame:
        raise AssertionError("live loader should not be used for unsupported mock requests")

    def fake_mock_loader(*, sido: str, sigungu: str) -> pd.DataFrame:
        raise AssertionError("mock loader should not be used for unsupported regions")

    alerts, message = live_guidance_page_module._get_runtime_crawled_alerts(
        refresh_requested=False,
        mock_requested=True,
        active_sido="인천",
        active_sigungu="중구",
        session_state=session_state,
        live_loader=fake_live_loader,
        mock_loader=fake_mock_loader,
    )

    assert "지원 권역" in str(message)
    pd.testing.assert_frame_equal(alerts, cached_alerts)
    assert session_state["message_guidance_live_crawled_alerts_source"] == "live"
    assert session_state["message_guidance_live_crawled_alerts_updated_at"] == "2026-03-13 10:00:00"
