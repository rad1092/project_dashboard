from types import SimpleNamespace

import pandas as pd


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self._payload


def test_get_browser_or_manual_coordinates_reads_session_values(realtime_support_module) -> None:
    state = {"realtime_lat": "35.6432", "realtime_lon": "129.3621"}

    assert realtime_support_module.get_browser_or_manual_coordinates(state) == (35.6432, 129.3621)


def test_get_browser_or_manual_coordinates_returns_none_for_invalid_values(realtime_support_module) -> None:
    state = {"realtime_lat": "north", "realtime_lon": 129.3621}

    assert realtime_support_module.get_browser_or_manual_coordinates(state) is None


def test_get_osrm_route_detail_normalizes_payload(realtime_support_module, monkeypatch) -> None:
    payload = {
        "code": "Ok",
        "routes": [
            {
                "distance": 2500,
                "duration": 700,
                "geometry": {
                    "coordinates": [[129.36, 35.65], [129.355, 35.645], [129.35, 35.64]],
                },
            }
        ],
    }
    captured: dict[str, object] = {}

    def fake_get(url, *, params, timeout):
        captured["url"] = url
        captured["params"] = params
        captured["timeout"] = timeout
        return DummyResponse(payload)

    monkeypatch.setattr(realtime_support_module.requests, "get", fake_get)

    result = realtime_support_module._get_osrm_route_detail(
        origin={"x": 129.36, "y": 35.65},
        destination={"x": 129.35, "y": 35.64, "key": "dest-0"},
        base_url="http://localhost:5000/",
        profile="foot",
    )

    assert captured["url"] == "http://localhost:5000/route/v1/foot/129.36,35.65;129.35,35.64"
    assert captured["params"] == {
        "overview": "full",
        "geometries": "geojson",
        "steps": "false",
    }
    assert captured["timeout"] == realtime_support_module.OSRM_ROUTE_TIMEOUT_S
    assert result == {
        "destination_key": "dest-0",
        "route_distance_m": 2500,
        "route_duration_s": 700,
        "route_vertices": [(35.65, 129.36), (35.645, 129.355), (35.64, 129.35)],
        "source": "osrm",
    }


def test_build_route_bundle_sorts_osrm_routes_and_falls_back(realtime_support_module, monkeypatch) -> None:
    recommendations = pd.DataFrame(
        [
            {
                "대피소명": "A 대피소",
                "주소": "울산 북구 1",
                "대피소유형": "실내",
                "위도": 35.631476,
                "경도": 129.353966,
                "시도": "울산",
                "시군구": "북구",
                "수용인원": 0,
                "수용인원_정렬값": 0,
                "거리_km": 1.1,
                "추천구분": "전용 대피소",
                "추천사유": "test",
            },
            {
                "대피소명": "B 대피소",
                "주소": "울산 북구 2",
                "대피소유형": "실내",
                "위도": 35.637000,
                "경도": 129.359000,
                "시도": "울산",
                "시군구": "북구",
                "수용인원": 0,
                "수용인원_정렬값": 0,
                "거리_km": 1.4,
                "추천구분": "전용 대피소",
                "추천사유": "test",
            },
            {
                "대피소명": "C 대피소",
                "주소": "울산 북구 3",
                "대피소유형": "실내",
                "위도": 35.629000,
                "경도": 129.349500,
                "시도": "울산",
                "시군구": "북구",
                "수용인원": 0,
                "수용인원_정렬값": 0,
                "거리_km": 0.8,
                "추천구분": "전용 대피소",
                "추천사유": "test",
            },
        ]
    )
    dummy_page2 = SimpleNamespace(haversine_km=lambda *args: 2.4)

    def fake_get_osrm_route_detail(origin, destination, base_url, profile, timeout=10.0):
        destination_key = destination["key"]
        if destination_key == "dest-1":
            raise RuntimeError("no route")
        if destination_key == "dest-0":
            return {
                "destination_key": destination_key,
                "route_distance_m": 1500,
                "route_duration_s": 600,
                "route_vertices": [(35.64, 129.36), (35.635, 129.357), (35.631476, 129.353966)],
                "source": "osrm",
            }
        return {
            "destination_key": destination_key,
            "route_distance_m": 900,
            "route_duration_s": 300,
            "route_vertices": [(35.64, 129.36), (35.634, 129.355), (35.629, 129.3495)],
            "source": "osrm",
        }

    monkeypatch.setattr(realtime_support_module, "_get_osrm_route_detail", fake_get_osrm_route_detail)

    ordered, route_details, warnings = realtime_support_module._build_route_bundle(
        recommendations,
        user_latitude=35.64,
        user_longitude=129.36,
        osrm_base_url="http://localhost:5000",
        osrm_profile="foot",
        page2_module=dummy_page2,
    )

    assert ordered["대피소명"].tolist() == ["C 대피소", "A 대피소", "B 대피소"]
    detail_by_key = {detail["destination_key"]: detail for detail in route_details}
    assert detail_by_key["dest-1"]["source"] == "straight_line"
    assert detail_by_key["dest-1"]["route_duration_s"] is None
    assert warnings == ["B 대피소 도보 경로 조회 실패: no route"]


def test_build_route_bundle_uses_straight_line_when_osrm_is_missing(realtime_support_module) -> None:
    recommendations = pd.DataFrame(
        [
            {
                "대피소명": "북구종합사회복지관",
                "주소": "울산 북구 어딘가",
                "대피소유형": "실내",
                "위도": 35.631476,
                "경도": 129.353966,
                "시도": "울산",
                "시군구": "북구",
                "수용인원": 0,
                "수용인원_정렬값": 0,
                "거리_km": 1.1,
                "추천구분": "전용 대피소",
                "추천사유": "test",
            }
        ]
    )
    dummy_page2 = SimpleNamespace(haversine_km=lambda *args: 1.5)

    ordered, route_details, warnings = realtime_support_module._build_route_bundle(
        recommendations,
        user_latitude=35.64,
        user_longitude=129.36,
        osrm_base_url=None,
        osrm_profile="foot",
        page2_module=dummy_page2,
    )

    assert ordered.iloc[0]["대피소명"] == "북구종합사회복지관"
    assert route_details[0]["source"] == "straight_line"
    assert warnings == ["OSRM_BASE_URL 설정이 없어 직선 fallback 경로를 표시합니다."]


def test_build_realtime_recommendation_map_returns_folium_map(realtime_support_module) -> None:
    recommendations = pd.DataFrame(
        [
            {
                "대피소명": "북구종합사회복지관",
                "주소": "울산 북구 어딘가",
                "대피소유형": "실내",
                "위도": 35.631476,
                "경도": 129.353966,
                "시도": "울산",
                "시군구": "북구",
                "수용인원": 0,
                "수용인원_정렬값": 0,
                "거리_km": 1.1,
                "추천구분": "전용 대피소",
                "추천사유": "test",
                "route_key": "dest-0",
            },
            {
                "대피소명": "태화체육관",
                "주소": "울산 북구 다른 곳",
                "대피소유형": "실내",
                "위도": 35.639,
                "경도": 129.364,
                "시도": "울산",
                "시군구": "북구",
                "수용인원": 0,
                "수용인원_정렬값": 0,
                "거리_km": 0.7,
                "추천구분": "기본 대피소",
                "추천사유": "test",
                "route_key": "dest-1",
            },
        ]
    )
    route_details = [
        {
            "destination_key": "dest-0",
            "route_distance_m": 1500,
            "route_duration_s": 420,
            "route_vertices": [(35.64, 129.36), (35.635, 129.357), (35.631476, 129.353966)],
            "source": "osrm",
        },
        {
            "destination_key": "dest-1",
            "route_distance_m": 800,
            "route_duration_s": None,
            "route_vertices": [(35.64, 129.36), (35.639, 129.364)],
            "source": "straight_line",
        },
    ]

    result = realtime_support_module.build_realtime_recommendation_map(
        35.64,
        129.36,
        recommendations,
        route_details,
    )

    assert result is not None
    assert hasattr(result, "_children")
    assert any(child.__class__.__name__ == "PolyLine" for child in result._children.values())


def test_realtime_page_module_imports(realtime_page_module, realtime_support_module) -> None:
    assert realtime_page_module.PAGE_LABEL == "실시간 테스트"
    assert hasattr(realtime_page_module, "render_page")
    assert realtime_page_module._build_route_bundle is realtime_support_module._build_route_bundle
