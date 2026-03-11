from pathlib import Path

import pytest


def test_resolve_data_dir_uses_override(dashboard_data_module, sample_preprocessing_dir) -> None:
    assert dashboard_data_module.resolve_data_dir(sample_preprocessing_dir) == sample_preprocessing_dir.resolve()


def test_resolve_data_dir_prefers_env_over_secret_and_repo_local(
    dashboard_data_module,
    tmp_path: Path,
    monkeypatch,
) -> None:
    # 데이터 경로 우선순위가 바뀌면 홈/추천/분석이 전부 다른 폴더를 읽을 수 있어서 중요하다.
    env_dir = tmp_path / "env_data"
    secret_dir = tmp_path / "secret_data"
    repo_dir = tmp_path / "repo_data"
    desktop_dir = tmp_path / "desktop_data"
    for path in [env_dir, secret_dir, repo_dir, desktop_dir]:
        path.mkdir()

    monkeypatch.setenv("PREPROCESSING_DATA_DIR", str(env_dir))
    monkeypatch.setattr(dashboard_data_module, "_maybe_get_secret_data_dir", lambda: str(secret_dir))
    monkeypatch.setattr(dashboard_data_module, "_get_repo_default_data_dir", lambda: repo_dir)
    monkeypatch.setattr(dashboard_data_module, "_get_desktop_default_data_dir", lambda: desktop_dir)

    assert dashboard_data_module.resolve_data_dir() == env_dir.resolve()


def test_resolve_data_dir_prefers_secret_over_repo_local(
    dashboard_data_module,
    tmp_path: Path,
    monkeypatch,
) -> None:
    secret_dir = tmp_path / "secret_data"
    repo_dir = tmp_path / "repo_data"
    desktop_dir = tmp_path / "desktop_data"
    for path in [secret_dir, repo_dir, desktop_dir]:
        path.mkdir()

    monkeypatch.delenv("PREPROCESSING_DATA_DIR", raising=False)
    monkeypatch.setattr(dashboard_data_module, "_maybe_get_secret_data_dir", lambda: str(secret_dir))
    monkeypatch.setattr(dashboard_data_module, "_get_repo_default_data_dir", lambda: repo_dir)
    monkeypatch.setattr(dashboard_data_module, "_get_desktop_default_data_dir", lambda: desktop_dir)

    assert dashboard_data_module.resolve_data_dir() == secret_dir.resolve()


def test_resolve_data_dir_uses_repo_local_default_when_no_override(
    dashboard_data_module,
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo_dir = tmp_path / "repo_data"
    desktop_dir = tmp_path / "desktop_data"
    repo_dir.mkdir()
    desktop_dir.mkdir()

    monkeypatch.delenv("PREPROCESSING_DATA_DIR", raising=False)
    monkeypatch.setattr(dashboard_data_module, "_maybe_get_secret_data_dir", lambda: None)
    monkeypatch.setattr(dashboard_data_module, "_get_repo_default_data_dir", lambda: repo_dir)
    monkeypatch.setattr(dashboard_data_module, "_get_desktop_default_data_dir", lambda: desktop_dir)

    assert dashboard_data_module.resolve_data_dir() == repo_dir.resolve()


def test_resolve_data_dir_falls_back_to_desktop_after_repo_local(
    dashboard_data_module,
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo_dir = tmp_path / "missing_repo_data"
    desktop_dir = tmp_path / "Desktop" / "preprocessing_data"
    desktop_dir.mkdir(parents=True)

    monkeypatch.delenv("PREPROCESSING_DATA_DIR", raising=False)
    monkeypatch.setattr(dashboard_data_module, "_maybe_get_secret_data_dir", lambda: None)
    monkeypatch.setattr(dashboard_data_module, "_get_repo_default_data_dir", lambda: repo_dir)
    monkeypatch.setattr(dashboard_data_module, "_get_desktop_default_data_dir", lambda: desktop_dir)

    assert dashboard_data_module.resolve_data_dir() == desktop_dir.resolve()


def test_load_alerts_dataframe_reports_missing_runtime_csv(
    dashboard_data_module,
    tmp_path: Path,
) -> None:
    missing_base = tmp_path / "preprocessing_data"
    (missing_base / "preprocessing").mkdir(parents=True)

    try:
        dashboard_data_module.load_alerts_dataframe_uncached(missing_base)
    except FileNotFoundError as exc:
        message = str(exc)
    else:
        raise AssertionError("missing runtime csv should raise FileNotFoundError")

    assert "전처리 데이터 파일이 없다" in message
    assert "PREPROCESSING_DATA_DIR" in message


def test_load_dataframes_read_expected_rows(
    dashboard_data_module,
    sample_preprocessing_dir,
) -> None:
    alerts_frame = dashboard_data_module.load_alerts_dataframe_uncached(sample_preprocessing_dir)
    shelters_frame = dashboard_data_module.load_shelters_dataframe_uncached(sample_preprocessing_dir)
    earthquake_shelters_frame = dashboard_data_module.load_earthquake_shelters_dataframe_uncached(
        sample_preprocessing_dir
    )
    tsunami_shelters_frame = dashboard_data_module.load_tsunami_shelters_dataframe_uncached(
        sample_preprocessing_dir
    )

    assert len(alerts_frame) == 3
    assert len(shelters_frame) == 4
    assert len(earthquake_shelters_frame) == 1
    assert len(tsunami_shelters_frame) == 1


def test_recent_alerts_and_summary_follow_region(
    recommendation_page_module,
    sample_preprocessing_dir,
) -> None:
    # 추천 페이지 상단 카드가 최근 특보 표와 어긋나지 않도록 둘을 같이 검증한다.
    alerts_frame = recommendation_page_module.load_alerts_dataframe_uncached(sample_preprocessing_dir)
    recent = recommendation_page_module.get_recent_alerts(
        alerts_frame,
        sido="경북",
        sigungu="포항시",
        limit=2,
    )
    summary = recommendation_page_module.build_alert_summary(
        alerts_frame,
        sido="경북",
        sigungu="포항시",
    )

    assert len(recent) == 2
    assert recent.iloc[0]["재난종류"] == "호우"
    assert summary["latest_disaster"] == "호우"
    assert "풍랑" in summary["hazards"]


def test_infer_region_from_coordinates_uses_nearest_region_center(
    recommendation_page_module,
    sample_preprocessing_dir,
) -> None:
    shelters_frame = recommendation_page_module.load_shelters_dataframe_uncached(sample_preprocessing_dir)

    pohang_region = recommendation_page_module.infer_region_from_coordinates(
        shelters_frame,
        latitude=36.0205,
        longitude=129.3440,
    )
    andong_region = recommendation_page_module.infer_region_from_coordinates(
        shelters_frame,
        latitude=36.5683,
        longitude=128.7291,
    )

    assert pohang_region["sido"] == "경북"
    assert pohang_region["sigungu"] == "포항시"
    assert pohang_region["source"] == "auto_detected"
    assert andong_region["sido"] == "경북"
    assert andong_region["sigungu"] == "안동시"


def test_update_recommendation_coordinates_from_region_center_sets_state(
    recommendation_page_module,
    sample_preprocessing_dir,
) -> None:
    shelters_frame = recommendation_page_module.load_shelters_dataframe_uncached(sample_preprocessing_dir)
    state: dict[str, float] = {}

    updated = recommendation_page_module.update_recommendation_coordinates_from_region_center(
        shelters_frame=shelters_frame,
        sido="경북",
        sigungu="포항시",
        state=state,
    )

    assert updated is True
    assert state["recommendation_lat"] == pytest.approx(36.02)
    assert state["recommendation_lon"] == pytest.approx(129.344)


def test_classify_disaster_type_maps_known_labels(recommendation_page_module) -> None:
    assert recommendation_page_module.classify_disaster_type("풍랑") == "강풍/풍랑"
    assert recommendation_page_module.classify_disaster_type("호우") == "호우/태풍"
    assert recommendation_page_module.classify_disaster_type("폭염") == "폭염"
    assert recommendation_page_module.classify_disaster_type("지진해일") == "해일/쓰나미"
    assert recommendation_page_module.classify_disaster_type("쓰나미") == "해일/쓰나미"


def test_get_disaster_options_includes_tsunami_without_matching_recent_alerts(
    recommendation_page_module,
    sample_preprocessing_dir,
) -> None:
    alerts_frame = recommendation_page_module.load_alerts_dataframe_uncached(sample_preprocessing_dir)

    options = recommendation_page_module.get_disaster_options(
        alerts_frame,
        sido="경북",
        sigungu="포항시",
    )

    assert "해일/쓰나미" in options


def test_should_compute_recommendations_waits_for_manual_selection(recommendation_page_module) -> None:
    assert not recommendation_page_module.should_compute_recommendations(None)
    assert recommendation_page_module.should_compute_recommendations("호우/태풍")


def test_haversine_km_returns_positive_distance(recommendation_page_module) -> None:
    distance = recommendation_page_module.haversine_km(35.1796, 129.0756, 35.538, 129.312)
    assert distance > 0


def test_recommend_shelters_prefers_dedicated_candidates(
    recommendation_page_module,
    sample_preprocessing_dir,
) -> None:
    # 지진과 해일/쓰나미처럼 전용 대피소가 있는 재난은,
    # 통합 대피소보다 전용 대피소가 먼저 올라와야 한다.
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
        disaster_group="지진",
        latitude=36.02,
        longitude=129.34,
        sido="경북",
        sigungu="포항시",
    )

    assert not recommendations.empty
    assert list(recommendations.columns) == recommendation_page_module.RECOMMENDATION_RESULT_COLUMNS
    assert recommendations.iloc[0]["추천구분"] == "전용 대피소"
    assert recommendations.iloc[0]["대피소유형"] == "지진대피장소"


def test_recommend_shelters_uses_tsunami_dedicated_label(
    recommendation_page_module,
    sample_preprocessing_dir,
) -> None:
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
        disaster_group="해일/쓰나미",
        latitude=36.02,
        longitude=129.34,
        sido="경북",
        sigungu="포항시",
    )

    assert not recommendations.empty
    assert list(recommendations.columns) == recommendation_page_module.RECOMMENDATION_RESULT_COLUMNS
    assert recommendations.iloc[0]["추천구분"] == "전용 대피소"
    assert recommendations.iloc[0]["대피소유형"] == "해일대피장소"


def test_recommend_shelters_uses_fallback_when_needed(
    recommendation_page_module,
    sample_preprocessing_dir,
) -> None:
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
        disaster_group="호우/태풍",
        latitude=36.02,
        longitude=129.34,
        sido="경북",
        sigungu="포항시",
    )

    assert not recommendations.empty
    assert list(recommendations.columns) == recommendation_page_module.RECOMMENDATION_RESULT_COLUMNS
    assert recommendations.iloc[0]["추천구분"] in {"기본 대피소", "대체 대피소"}


def test_should_display_recommendations_returns_true_within_threshold(
    recommendation_page_module,
    sample_preprocessing_dir,
) -> None:
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
        disaster_group="호우/태풍",
        latitude=36.02,
        longitude=129.34,
        sido="경북",
        sigungu="포항시",
    )

    assert recommendation_page_module.get_nearest_recommendation_distance_km(recommendations) is not None
    assert recommendation_page_module.should_display_recommendations(recommendations)


def test_should_display_recommendations_returns_false_over_threshold(
    recommendation_page_module,
    sample_preprocessing_dir,
) -> None:
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
        disaster_group="한파",
        latitude=35.1796,
        longitude=129.0756,
        sido="부산",
        sigungu="연제구",
    )

    nearest_distance = recommendation_page_module.get_nearest_recommendation_distance_km(recommendations)

    assert nearest_distance is not None
    assert nearest_distance > recommendation_page_module.MAX_ACTIONABLE_DISTANCE_KM
    assert not recommendation_page_module.should_display_recommendations(recommendations)
