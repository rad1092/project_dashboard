from types import SimpleNamespace

import pandas as pd


def test_build_chrome_driver_kwargs_uses_linux_system_paths(
    crawling_module,
    monkeypatch,
    tmp_path,
) -> None:
    fake_binary = tmp_path / "chromium"
    fake_driver = tmp_path / "chromedriver"
    fake_binary.write_text("", encoding="utf-8")
    fake_driver.write_text("", encoding="utf-8")

    monkeypatch.setattr(crawling_module, "_running_on_linux", lambda: True)
    monkeypatch.setattr(crawling_module, "SYSTEM_CHROME_BINARY_PATH", fake_binary)
    monkeypatch.setattr(crawling_module, "SYSTEM_CHROMEDRIVER_PATH", fake_driver)

    driver_kwargs = crawling_module._build_chrome_driver_kwargs(headless=True)
    options = driver_kwargs["options"]
    service = driver_kwargs["service"]

    assert options.binary_location == str(fake_binary)
    assert "--headless=new" in options.arguments
    assert "--no-sandbox" in options.arguments
    assert "--disable-dev-shm-usage" in options.arguments
    assert "--window-size=1600,1200" in options.arguments
    assert service.path == str(fake_driver)


def test_build_chrome_driver_kwargs_falls_back_without_system_paths(
    crawling_module,
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(crawling_module, "_running_on_linux", lambda: True)
    monkeypatch.setattr(crawling_module, "SYSTEM_CHROME_BINARY_PATH", tmp_path / "missing-chromium")
    monkeypatch.setattr(crawling_module, "SYSTEM_CHROMEDRIVER_PATH", tmp_path / "missing-chromedriver")

    driver_kwargs = crawling_module._build_chrome_driver_kwargs(headless=False)
    options = driver_kwargs["options"]

    assert options.binary_location == ""
    assert "--headless=new" not in options.arguments
    assert "--no-sandbox" in options.arguments
    assert "--disable-dev-shm-usage" in options.arguments
    assert "--window-size=1600,1200" in options.arguments
    assert "service" not in driver_kwargs


def test_load_live_crawled_alerts_dataframe_uncached_uses_crawler_helper(
    live_guidance_page_module,
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_crawl_disaster_notifications(*, headless: bool, wait_seconds: int) -> pd.DataFrame:
        captured["headless"] = headless
        captured["wait_seconds"] = wait_seconds
        return pd.DataFrame(
            [
                {
                    "발표시간": "2026-03-06 13:00",
                    "지역": "경북",
                    "시군구": "포항시",
                    "재난종류": "호우",
                    "특보등급": "경보",
                    "내용": "포항시 호우 경보",
                    "발송기관": "포항시",
                    "번호": "101",
                }
            ]
        )

    monkeypatch.setattr(
        live_guidance_page_module,
        "load_crawling_module",
        lambda: SimpleNamespace(crawl_disaster_notifications=fake_crawl_disaster_notifications),
    )

    result = live_guidance_page_module.load_live_crawled_alerts_dataframe_uncached(headless=False)

    assert captured == {
        "headless": False,
        "wait_seconds": live_guidance_page_module.DEFAULT_CRAWLING_WAIT_SECONDS,
    }
    assert list(result.columns) == [
        *live_guidance_page_module.CRAWLED_ALERT_COLUMNS,
        live_guidance_page_module.SIGUNGU_NORMALIZED_COLUMN,
        live_guidance_page_module.DISASTER_GROUP_COLUMN,
        live_guidance_page_module.ALERT_KEY_COLUMN,
    ]
    assert result.iloc[0][live_guidance_page_module.PUBLISHED_AT_COLUMN] == pd.Timestamp("2026-03-06 13:00")
    assert result.iloc[0][live_guidance_page_module.SIGUNGU_NORMALIZED_COLUMN] == "포항"
    assert result.iloc[0][live_guidance_page_module.DISASTER_GROUP_COLUMN] == "호우/태풍"
