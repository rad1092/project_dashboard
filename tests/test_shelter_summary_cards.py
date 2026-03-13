import pytest


@pytest.mark.parametrize(
    "fixture_name",
    ["simulation_page_module", "live_guidance_page_module"],
)
def test_build_shelter_summary_card_html_contains_all_rows(request, fixture_name) -> None:
    page_module = request.getfixturevalue(fixture_name)
    long_address = "울산광역시 북구 화동로 47(화봉동) 별관 2층 대피 유도 공간"
    rows = [
        ("대피소 계열", "무더위쉼터"),
        ("실경로 거리", "1.91 km"),
        ("주소", long_address),
        ("예상 시간", "3분"),
    ]

    html = page_module.build_shelter_summary_card_html(
        "화봉고등학교 운동장",
        rows,
        accent_color="#0f766e",
    )

    assert "화봉고등학교 운동장" in html
    for label, value in rows:
        assert label in html
        assert value in html
    assert "pd-shelter-summary-card__accent" in html
    assert "#0f766e" in html
    assert "pd-shelter-summary-card__meta-bar" in html
    assert "pd-shelter-summary-card__family" in html
    assert "pd-shelter-summary-card__meta-grid" not in html
    assert "-webkit-line-clamp" not in html
    assert "#fbf7ef" in html
    assert "margin-bottom: 2.96rem;" in html
    assert "pd-shelter-summary-card__note" not in html


@pytest.mark.parametrize(
    "fixture_name",
    ["simulation_page_module", "live_guidance_page_module"],
)
def test_build_shelter_summary_card_html_renders_optional_note(request, fixture_name) -> None:
    page_module = request.getfixturevalue(fixture_name)
    note = "OSRM 경로 확인이 안 돼 직선 fallback 결과를 표시 중입니다."

    html = page_module.build_shelter_summary_card_html(
        "울산에너지고등학교 운동장",
        [("실경로 거리", "1.20 km")],
        accent_color="#1d4ed8",
        note=note,
    )

    assert note in html
    assert "pd-shelter-summary-card__note" in html
    assert "#1d4ed8" in html
