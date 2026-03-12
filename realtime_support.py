from __future__ import annotations

import importlib.util
import os
import sys
from collections.abc import Callable, Mapping, MutableMapping
from datetime import datetime
from pathlib import Path
from typing import Any

import folium
import pandas as pd
import requests
import streamlit as st

PAGE2_PATH = Path(__file__).resolve().parent / "pages" / "1_대피소_추천.py"
PAGE2_MODULE_NAME = "project_dashboard_recommendation_runtime"
OSRM_BASE_URL_KEY = "OSRM_BASE_URL"
DEFAULT_OSRM_BASE_URL = "http://router.project-osrm.org"
DEFAULT_OSRM_PROFILE = "foot"
OSRM_ROUTE_TIMEOUT_S = 10.0
RANK_COLORS = ["#0f766e", "#1d4ed8", "#f59e0b"]


def load_recommendation_page_module():
    if PAGE2_MODULE_NAME in sys.modules:
        return sys.modules[PAGE2_MODULE_NAME]

    previous_value = os.environ.get("PROJECT_DASHBOARD_IMPORT_ONLY")
    os.environ["PROJECT_DASHBOARD_IMPORT_ONLY"] = "1"
    try:
        spec = importlib.util.spec_from_file_location(PAGE2_MODULE_NAME, PAGE2_PATH)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load module from {PAGE2_PATH}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[PAGE2_MODULE_NAME] = module
        spec.loader.exec_module(module)
        return module
    finally:
        if previous_value is None:
            os.environ.pop("PROJECT_DASHBOARD_IMPORT_ONLY", None)
        else:
            os.environ["PROJECT_DASHBOARD_IMPORT_ONLY"] = previous_value


def _state_key(prefix: str, name: str) -> str:
    return f"{prefix}_{name}"


def load_prefixed_session_value(
    session_state: MutableMapping[str, object],
    *,
    prefix: str,
    name: str,
    loader: Callable[[], Any],
    force_refresh: bool = False,
) -> Any:
    value_key = _state_key(prefix, name)
    updated_key = _state_key(prefix, f"{name}_updated_at")
    if force_refresh or value_key not in session_state:
        session_state[value_key] = loader()
        session_state[updated_key] = current_timestamp_label()
    session_state.setdefault(updated_key, "-")
    return session_state[value_key]


def get_osrm_config() -> tuple[str, str]:
    base_url = os.environ.get(OSRM_BASE_URL_KEY, "").strip() or DEFAULT_OSRM_BASE_URL
    return base_url.rstrip("/"), DEFAULT_OSRM_PROFILE


def get_browser_or_manual_coordinates(
    session_state: MutableMapping[str, object],
    *,
    prefix: str = "realtime",
) -> tuple[float, float] | None:
    latitude = session_state.get(_state_key(prefix, "lat"))
    longitude = session_state.get(_state_key(prefix, "lon"))
    if latitude in (None, "") or longitude in (None, ""):
        return None

    try:
        return float(latitude), float(longitude)
    except (TypeError, ValueError):
        return None


def format_distance_m(distance_m: object) -> str:
    try:
        value = float(distance_m)
    except (TypeError, ValueError):
        return "-"

    if value >= 1000:
        return f"{value / 1000:.2f} km"
    return f"{value:.0f} m"


def format_duration_s(duration_s: object) -> str:
    try:
        value = int(float(duration_s))
    except (TypeError, ValueError):
        return "-"

    minutes, seconds = divmod(value, 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{hours}시간 {minutes}분"
    if minutes > 0:
        return f"{minutes}분"
    return f"{seconds}초"


def current_timestamp_label() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def format_location_source_label(source: object) -> str:
    source_value = str(source or "")
    if source_value == "browser":
        return "브라우저"
    if source_value == "manual":
        return "수동"
    return "기본값"


def apply_browser_location(
    location_payload: object,
    *,
    prefix: str = "realtime",
    session_state: MutableMapping[str, object] | None = None,
) -> None:
    state = session_state if session_state is not None else st.session_state
    if state.get(_state_key(prefix, "location_mode")) != "auto":
        return

    if not isinstance(location_payload, dict):
        return

    latitude = location_payload.get("latitude")
    longitude = location_payload.get("longitude")
    if latitude in (None, "") or longitude in (None, ""):
        return

    try:
        state[_state_key(prefix, "lat")] = float(latitude)
        state[_state_key(prefix, "lon")] = float(longitude)
    except (TypeError, ValueError):
        return

    state[_state_key(prefix, "location_source")] = "browser"
    state[_state_key(prefix, "location_updated_at")] = current_timestamp_label()


def mark_manual_location(
    *,
    prefix: str = "realtime",
    session_state: MutableMapping[str, object] | None = None,
) -> None:
    state = session_state if session_state is not None else st.session_state
    state[_state_key(prefix, "location_mode")] = "manual"
    state[_state_key(prefix, "location_source")] = "manual"
    state[_state_key(prefix, "location_updated_at")] = current_timestamp_label()


def sync_default_coordinates(
    page2_module,
    shelters_frame: pd.DataFrame,
    *,
    prefix: str = "realtime",
    session_state: MutableMapping[str, object] | None = None,
    default_sido: str = "울산",
    default_sigungu: str = "북구",
    fallback_coordinates: tuple[float, float] = (35.633, 129.365),
) -> None:
    state = session_state if session_state is not None else st.session_state
    state.setdefault(_state_key(prefix, "location_mode"), "auto")
    state.setdefault(_state_key(prefix, "location_source"), "fallback")
    state.setdefault(_state_key(prefix, "location_updated_at"), "-")

    if _state_key(prefix, "lat") in state and _state_key(prefix, "lon") in state:
        return

    default_latitude, default_longitude = page2_module.get_region_center(
        shelters_frame,
        default_sido,
        default_sigungu,
    )
    if default_latitude is None or default_longitude is None:
        default_latitude, default_longitude = fallback_coordinates

    state[_state_key(prefix, "lat")] = float(default_latitude)
    state[_state_key(prefix, "lon")] = float(default_longitude)
    state[_state_key(prefix, "location_source")] = "fallback"


def _normalize_point(value: Mapping[str, object]) -> dict[str, Any]:
    return {
        "x": float(value["x"]),
        "y": float(value["y"]),
        "key": str(value.get("key", "")),
        "name": str(value.get("name", "")),
    }


def _extract_osrm_route_vertices(route: Mapping[str, object]) -> list[tuple[float, float]]:
    geometry = route.get("geometry", {}) if isinstance(route, dict) else {}
    coordinates = geometry.get("coordinates", []) if isinstance(geometry, dict) else []
    if not isinstance(coordinates, list):
        return []

    vertices: list[tuple[float, float]] = []
    for coordinate in coordinates:
        if not isinstance(coordinate, (list, tuple)) or len(coordinate) < 2:
            continue
        try:
            longitude = float(coordinate[0])
            latitude = float(coordinate[1])
        except (TypeError, ValueError):
            continue

        point = (latitude, longitude)
        if not vertices or vertices[-1] != point:
            vertices.append(point)
    return vertices


def _get_osrm_route_detail(
    origin: Mapping[str, object],
    destination: Mapping[str, object],
    base_url: str,
    profile: str,
    timeout: float = OSRM_ROUTE_TIMEOUT_S,
) -> dict[str, object]:
    normalized_origin = _normalize_point(origin)
    normalized_destination = _normalize_point(destination)
    route_path = (
        f"{base_url}/route/v1/{profile}/"
        f"{normalized_origin['x']},{normalized_origin['y']};"
        f"{normalized_destination['x']},{normalized_destination['y']}"
    )
    response = requests.get(
        route_path,
        params={
            "overview": "full",
            "geometries": "geojson",
            "steps": "false",
        },
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()

    if payload.get("code") != "Ok":
        raise ValueError(f"OSRM route response returned code={payload.get('code')!r}.")

    routes = payload.get("routes", [])
    if not isinstance(routes, list) or not routes:
        raise ValueError("OSRM route response does not contain routes.")

    route = routes[0]
    route_vertices = _extract_osrm_route_vertices(route)
    if not route_vertices:
        route_vertices = [
            (float(normalized_origin["y"]), float(normalized_origin["x"])),
            (float(normalized_destination["y"]), float(normalized_destination["x"])),
        ]

    return {
        "destination_key": normalized_destination["key"],
        "route_distance_m": route.get("distance"),
        "route_duration_s": route.get("duration"),
        "route_vertices": route_vertices,
        "source": "osrm",
    }


def _build_straight_line_route_detail(
    origin: Mapping[str, object],
    destination: Mapping[str, object],
    page2_module,
    *,
    reason: str = "",
) -> dict[str, object]:
    normalized_origin = _normalize_point(origin)
    normalized_destination = _normalize_point(destination)
    distance_km = page2_module.haversine_km(
        float(normalized_origin["y"]),
        float(normalized_origin["x"]),
        float(normalized_destination["y"]),
        float(normalized_destination["x"]),
    )
    return {
        "destination_key": normalized_destination["key"],
        "route_distance_m": round(distance_km * 1000, 1),
        "route_duration_s": None,
        "route_vertices": [
            (float(normalized_origin["y"]), float(normalized_origin["x"])),
            (float(normalized_destination["y"]), float(normalized_destination["x"])),
        ],
        "source": "straight_line",
        "warning": reason,
    }


def build_realtime_recommendation_map(
    user_lat: float,
    user_lon: float,
    recommendations: pd.DataFrame,
    route_details: list[dict[str, object]],
) -> folium.Map:
    detail_by_key = {
        str(detail.get("destination_key", "")): detail for detail in route_details if detail.get("destination_key")
    }
    map_object = folium.Map(
        location=[user_lat, user_lon],
        zoom_start=12,
        tiles="OpenStreetMap",
        control_scale=True,
    )
    bounds: list[list[float]] = [[user_lat, user_lon]]

    folium.CircleMarker(
        location=[user_lat, user_lon],
        radius=8,
        color="#dc2626",
        fill=True,
        fill_color="#dc2626",
        fill_opacity=1.0,
        tooltip="현재 위치",
    ).add_to(map_object)

    for index, (_, row) in enumerate(recommendations.iterrows()):
        route_key = str(row.get("route_key", index))
        detail = detail_by_key.get(route_key)
        color = RANK_COLORS[index % len(RANK_COLORS)]
        shelter_latitude = float(row["위도"])
        shelter_longitude = float(row["경도"])
        popup_lines = [
            f"<strong>{row['대피소명']}</strong>",
            f"구분: {row['추천구분']}",
            f"실경로 거리: {format_distance_m(detail.get('route_distance_m') if detail else None)}",
            f"예상 시간: {format_duration_s(detail.get('route_duration_s') if detail else None)}",
        ]
        if detail and detail.get("source") == "straight_line":
            popup_lines.append("OSRM 도보 경로 조회 실패로 직선 fallback 을 표시함")

        folium.CircleMarker(
            location=[shelter_latitude, shelter_longitude],
            radius=6,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.95,
            tooltip=f"Top {index + 1}. {row['대피소명']}",
            popup=folium.Popup("<br>".join(popup_lines), max_width=320),
        ).add_to(map_object)

        vertices = detail.get("route_vertices") if detail else None
        if not isinstance(vertices, list) or not vertices:
            vertices = [(user_lat, user_lon), (shelter_latitude, shelter_longitude)]

        folium.PolyLine(
            locations=vertices,
            color=color,
            weight=4,
            opacity=0.85,
            dash_array="7 7" if detail and detail.get("source") == "straight_line" else None,
            tooltip=f"{row['대피소명']} 경로",
        ).add_to(map_object)

        for vertex_lat, vertex_lon in vertices:
            bounds.append([float(vertex_lat), float(vertex_lon)])
        bounds.append([shelter_latitude, shelter_longitude])

    if len(bounds) > 1:
        map_object.fit_bounds(bounds, padding=(24, 24))

    return map_object


def _prepare_destinations(recommendations: pd.DataFrame) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    prepared = recommendations.head(3).copy().reset_index(drop=True)
    destinations: list[dict[str, object]] = []
    for index, row in prepared.iterrows():
        route_key = f"dest-{index}"
        prepared.at[index, "route_key"] = route_key
        destinations.append(
            {
                "key": route_key,
                "name": str(row["대피소명"]),
                "x": float(row["경도"]),
                "y": float(row["위도"]),
            }
        )
    return prepared, destinations


def _attach_route_sort(
    recommendations: pd.DataFrame,
    route_details: list[dict[str, object]],
) -> pd.DataFrame:
    ordered = recommendations.copy()
    detail_by_key = {
        str(detail.get("destination_key", "")): detail
        for detail in route_details
        if detail.get("destination_key")
    }
    ordered["route_distance_m"] = ordered["route_key"].map(
        lambda key: detail_by_key.get(str(key), {}).get("route_distance_m")
    )
    ordered["route_duration_s"] = ordered["route_key"].map(
        lambda key: detail_by_key.get(str(key), {}).get("route_duration_s")
    )
    ordered["route_priority"] = ordered["route_key"].map(
        lambda key: 0 if detail_by_key.get(str(key), {}).get("source") == "osrm" else 1
    )
    ordered = ordered.sort_values(
        ["route_priority", "route_duration_s", "route_distance_m", "거리_km"],
        ascending=[True, True, True, True],
        na_position="last",
    ).reset_index(drop=True)
    return ordered.drop(columns=["route_priority"])


def _build_route_bundle(
    recommendations: pd.DataFrame,
    user_latitude: float,
    user_longitude: float,
    osrm_base_url: str | None,
    osrm_profile: str = DEFAULT_OSRM_PROFILE,
    page2_module=None,
) -> tuple[pd.DataFrame, list[dict[str, object]], list[str]]:
    recommendation_page_module = page2_module or load_recommendation_page_module()
    prepared, destinations = _prepare_destinations(recommendations)
    origin = {"x": user_longitude, "y": user_latitude, "key": "origin", "name": "현재 위치"}
    warnings: list[str] = []
    route_details: list[dict[str, object]] = []

    destination_by_key = {destination["key"]: destination for destination in destinations}
    if not osrm_base_url:
        warnings.append("OSRM_BASE_URL 설정이 없어 직선 fallback 경로를 표시합니다.")

    for _, row in prepared.iterrows():
        route_key = str(row["route_key"])
        destination = destination_by_key[route_key]
        if osrm_base_url:
            try:
                detail = _get_osrm_route_detail(origin, destination, osrm_base_url, osrm_profile)
            except Exception as exc:
                warnings.append(f"{row['대피소명']} 도보 경로 조회 실패: {exc}")
                detail = _build_straight_line_route_detail(
                    origin,
                    destination,
                    recommendation_page_module,
                    reason="osrm route lookup failed",
                )
        else:
            detail = _build_straight_line_route_detail(
                origin,
                destination,
                recommendation_page_module,
                reason="missing osrm base url",
            )

        route_details.append(detail)

    prepared = _attach_route_sort(prepared, route_details)
    return prepared, route_details, warnings


def build_request_id(
    selected_token: str,
    coordinates: tuple[float, float],
    recommendations: pd.DataFrame,
    osrm_base_url: str | None,
    osrm_profile: str,
) -> str:
    latitude, longitude = coordinates
    shelter_tokens = "|".join(
        f"{row['대피소명']}:{row['위도']}:{row['경도']}" for _, row in recommendations.iterrows()
    )
    routing_signature = f"{osrm_profile}:{osrm_base_url or 'straight-line'}"
    return f"{selected_token}|{latitude:.6f}|{longitude:.6f}|{routing_signature}|{shelter_tokens}"
