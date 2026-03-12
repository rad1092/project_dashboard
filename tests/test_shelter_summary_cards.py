import pytest


@pytest.mark.parametrize(
    "fixture_name",
    ["simulation_page_module", "live_guidance_page_module"],
)
def test_build_shelter_summary_card_html_contains_all_rows(request, fixture_name) -> None:
    page_module = request.getfixturevalue(fixture_name)
    long_address = "울산광역시 북구 화동로 47(화봉동) 별관 2층 대피 유도 공간"
    rows = [
        ("구분", "전용 대피소"),
        ("실경로 거리", "1.91 km"),
        ("예상 시간", "3분"),
        ("직선 거리", "1.35 km"),
        ("주소", long_address),
    ]

    html = page_module.build_shelter_summary_card_html("화봉고등학교 운동장", rows)

    assert "화봉고등학교 운동장" in html
    for label, value in rows:
        assert label in html
        assert value in html
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
        [("구분", "전용 대피소")],
        note=note,
    )

    assert note in html
    assert "pd-shelter-summary-card__note" in html
