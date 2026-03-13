import random
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest


def test_write_mock_disaster_message_csv_creates_expected_schema(
    mock_disaster_message_module,
    live_guidance_page_module,
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "disaster_message_realtime.csv"

    written_path = mock_disaster_message_module.write_mock_disaster_message_csv(
        sido="경북",
        sigungu="포항시",
        output_path=output_path,
        now=datetime(2026, 3, 13, 10, 30, 45),
        rng=random.Random(7),
    )

    dataframe = pd.read_csv(written_path, encoding="utf-8-sig")

    assert written_path == output_path.resolve()
    assert list(dataframe.columns) == live_guidance_page_module.CRAWLED_ALERT_COLUMNS
    assert len(dataframe) == 1
    assert dataframe.iloc[0]["지역"] == "경북"
    assert dataframe.iloc[0]["시군구"] == "포항시"
    assert dataframe.iloc[0]["재난종류"] in mock_disaster_message_module.DISASTER_TYPES
    assert dataframe.iloc[0]["특보등급"] in mock_disaster_message_module.ALERT_LEVELS
    assert dataframe.iloc[0]["발송기관"] == "경상북도 포항시"
    assert "포항시" in dataframe.iloc[0]["내용"]


def test_generated_mock_csv_can_be_loaded_by_live_guidance_page(
    mock_disaster_message_module,
    live_guidance_page_module,
    tmp_path: Path,
) -> None:
    mock_disaster_message_module.write_mock_disaster_message_csv(
        sido="부산",
        sigungu="해운대구",
        output_path=tmp_path / "disaster_message_realtime.csv",
        now=datetime(2026, 3, 13, 11, 0, 0),
        rng=random.Random(3),
    )

    alerts = live_guidance_page_module.load_crawled_alerts_dataframe_uncached(tmp_path)

    assert len(alerts) == 1
    assert "시군구정규화" in alerts.columns
    assert "재난그룹" in alerts.columns
    assert "alert_key" in alerts.columns
    assert alerts.iloc[0][live_guidance_page_module.REGION_COLUMN] == "부산"
    assert alerts.iloc[0][live_guidance_page_module.SIGUNGU_COLUMN] == "해운대구"
    assert alerts.iloc[0][live_guidance_page_module.DISASTER_GROUP_COLUMN]


def test_main_writes_nested_output_and_returns_zero(
    mock_disaster_message_module,
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "preprocessing_code" / "data" / "disaster_message_realtime.csv"

    exit_code = mock_disaster_message_module.main(
        [
            "--sido",
            "대구",
            "--sigungu",
            "중구",
            "--output",
            str(output_path),
        ]
    )

    dataframe = pd.read_csv(output_path, encoding="utf-8-sig")

    assert exit_code == 0
    assert output_path.exists()
    assert len(dataframe) == 1
    assert dataframe.iloc[0]["지역"] == "대구"
    assert dataframe.iloc[0]["시군구"] == "중구"


def test_write_mock_disaster_message_csv_rejects_unsupported_sido(
    mock_disaster_message_module,
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError):
        mock_disaster_message_module.write_mock_disaster_message_csv(
            sido="서울",
            sigungu="중구",
            output_path=tmp_path / "disaster_message_realtime.csv",
        )
