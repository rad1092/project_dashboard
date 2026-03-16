import sqlite3


def test_load_analysis_dataset_has_expected_columns(
    analysis_page_module,
    sample_preprocessing_dir,
) -> None:
    dataframe = analysis_page_module.load_analysis_dataset(sample_preprocessing_dir)

    assert list(dataframe.columns) == analysis_page_module.ANALYSIS_COLUMNS
    assert len(dataframe) == 3
    assert set(dataframe["재난종류"]) == {"강풍", "호우", "태풍"}


def test_build_kpis_returns_summary_values(
    analysis_page_module,
    sample_preprocessing_dir,
) -> None:
    dataframe = analysis_page_module.load_analysis_dataset(sample_preprocessing_dir)
    kpis = analysis_page_module.build_kpis(dataframe)

    assert kpis["alert_count"] == 3
    assert kpis["disaster_count"] == 3
    assert kpis["region_count"] == 2
    assert kpis["warning_count"] == 1
    assert str(kpis["latest_period"])[:16] == "2026-03-06 13:00"


def test_filter_analysis_dataset_uses_region_disaster_and_grade(
    analysis_page_module,
    sample_preprocessing_dir,
) -> None:
    dataframe = analysis_page_module.load_analysis_dataset(sample_preprocessing_dir)
    filtered = analysis_page_module.filter_analysis_dataset(
        dataframe,
        selected_regions=["경북"],
        selected_disasters=["호우"],
        selected_grades=["경보"],
    )

    assert len(filtered) == 1
    assert filtered.iloc[0]["지역"] == "경북"
    assert filtered.iloc[0]["재난종류"] == "호우"
    assert filtered.iloc[0]["특보등급"] == "경보"


def test_chart_builders_return_figures(analysis_page_module, sample_preprocessing_dir) -> None:
    dataframe = analysis_page_module.load_analysis_dataset(sample_preprocessing_dir)
    shelters_frame = analysis_page_module.load_shelters_dataframe_uncached(sample_preprocessing_dir)

    figures = [
        analysis_page_module.build_grade_distribution_chart(dataframe),
        analysis_page_module.build_monthly_distribution_chart(dataframe),
        analysis_page_module.build_region_disaster_counts_chart(dataframe),
        analysis_page_module.build_region_disaster_profile_radar_chart(dataframe),
        analysis_page_module.build_monthly_disaster_pattern_heatmap_chart(dataframe),
        analysis_page_module.build_disaster_region_scatter_chart(dataframe),
        analysis_page_module.build_shelter_type_distribution_chart(shelters_frame),
    ]

    for figure in figures:
        assert figure.data


def test_analysis_page_loaders_use_disaster_db_when_available(
    analysis_page_module,
    tmp_path,
) -> None:
    base = tmp_path / "preprocessing_data"
    db_dir = base / "preprocessing_code" / "data"
    db_dir.mkdir(parents=True)
    db_path = db_dir / "재난대피소.db"

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE regions (
                지역_id INTEGER PRIMARY KEY,
                시도 TEXT NOT NULL,
                시군구 TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE disaster_types (
                재난유형_id INTEGER PRIMARY KEY,
                재난이름 TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE danger_alerts (
                위험정보_id INTEGER PRIMARY KEY,
                발표시간 TEXT,
                지역_id INTEGER NOT NULL,
                재난유형_id INTEGER NOT NULL,
                특보등급 TEXT,
                해당지역 TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE shelters (
                대피소_id INTEGER PRIMARY KEY,
                지역_id INTEGER NOT NULL,
                대피소명 TEXT NOT NULL,
                주소 TEXT NOT NULL,
                대피소유형 TEXT,
                위도 REAL,
                경도 REAL,
                지역설명 TEXT,
                수용인원 INTEGER
            )
            """
        )
        connection.execute("INSERT INTO regions VALUES (1, '경북', '포항시')")
        connection.execute("INSERT INTO disaster_types VALUES (1, '호우')")
        connection.execute(
            """
            INSERT INTO danger_alerts
            VALUES (1, '2026-03-06 13:00:00', 1, 1, '경보', '포항시 북구')
            """
        )
        connection.execute(
            """
            INSERT INTO shelters
            VALUES (1, 1, '포항 체육센터', '경북 포항시 북구 1', '무더위쉼터', 36.019, 129.343, '경북 포항시', 50)
            """
        )
        connection.commit()

    alerts = analysis_page_module.load_analysis_dataset(base)
    shelters = analysis_page_module.load_shelters_dataframe_uncached(base)

    assert list(alerts.columns) == analysis_page_module.ANALYSIS_COLUMNS
    assert len(alerts) == 1
    assert alerts.iloc[0]["지역"] == "경북"
    assert alerts.iloc[0]["재난종류"] == "호우"

    assert list(shelters.columns) == analysis_page_module.SHELTER_COLUMNS
    assert len(shelters) == 1
    assert shelters.iloc[0]["시도"] == "경북"
    assert shelters.iloc[0]["대피소유형"] == "무더위쉼터"
