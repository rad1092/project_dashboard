"""무료 OSM 기반 지도 렌더링을 담당하는 모듈.

왜 필요한가:
- 추천 페이지는 사용자 위치와 대피소 후보를 즉시 확인할 수 있어야 한다.
- 이번 단계에서는 유료 지도 API 를 쓰지 않기 때문에, 무료 OSM 타일 기반 지도를 사용한다.

누가 사용하는가:
- ``pages/2_대피소_추천.py`` 가 이 모듈을 호출해 지도와 거리선을 출력한다.

무엇을 보장하는가:
- 사용자 위치 1개
- 추천 대피소의 작은 점 마커
- 사용자 위치와 후보를 잇는 직선 연결선

초보자 메모:
- 이 모듈은 추천 "계산"을 하지 않는다.
- 이미 계산된 추천 결과를 받아 지도 위에 어떻게 그릴지만 담당한다.
"""

from __future__ import annotations

import folium
import pandas as pd
import streamlit.components.v1 as components


def _get_marker_color(recommendation_type: str) -> str:
    """추천 구분에 따라 지도 마커 색을 고른다.

    같은 좌표라도 추천 이유가 다를 수 있으므로 색상으로 전용/대체/기본 후보를 구분한다.
    """

    if recommendation_type == "전용 대피소":
        return "#0f766e"
    if recommendation_type == "대체 대피소":
        return "#f59e0b"
    return "#1d4ed8"


def build_recommendation_map(
    user_latitude: float,
    user_longitude: float,
    recommendations: pd.DataFrame,
) -> folium.Map:
    """사용자 위치와 추천 대피소를 함께 표시하는 folium 지도를 만든다.

    실제 도로 길찾기 대신 직선 연결만 그리는 이유는,
    현재 프로젝트 범위가 "가까운 후보를 설명 가능하게 보여 주는 것"에 있기 때문이다.
    """

    map_object = folium.Map(
        # folium 은 좌표를 [위도, 경도] 순서의 리스트로 받기 때문에 이 순서를 바꾸면 지도가 엉뚱한 곳으로 간다.
        location=[user_latitude, user_longitude],
        zoom_start=11,
        tiles="OpenStreetMap",
        control_scale=True,
    )
    # Folium Map 객체는 "빈 지도 판"에 가깝고,
    # 아래에서 marker 와 polyline 을 add_to() 하면서 요소를 하나씩 올린다.

    # 사용자 기준점은 항상 하나만 찍어 추천의 출발 좌표가 어디인지 분명하게 보여 준다.
    folium.CircleMarker(
        location=[user_latitude, user_longitude],
        radius=7,
        color="#dc2626",
        fill=True,
        fill_color="#dc2626",
        fill_opacity=0.95,
        tooltip="사용자 위치",
    ).add_to(map_object)

    # 추천 후보가 있을 때는 사용자 위치와 후보가 모두 화면 안에 들어오도록 bounds 를 같이 계산한다.
    bounds = [[user_latitude, user_longitude]]
    for row in recommendations.to_dict(orient="records"):
        # to_dict(orient="records") 는 DataFrame 을 "행 단위 dict 목록"으로 바꾼다.
        # 그래서 pandas 문법을 몰라도 row["대피소명"] 처럼 일반 dict 처럼 읽을 수 있다.
        shelter_latitude = float(row["위도"])
        shelter_longitude = float(row["경도"])
        color = _get_marker_color(str(row["추천구분"]))

        # 추천 후보 점은 작고 빠르게 보이도록 circle marker 로 통일해 청사진의 "작은 점" 느낌을 유지한다.
        folium.CircleMarker(
            location=[shelter_latitude, shelter_longitude],
            radius=5,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.9,
            # tooltip 은 마우스를 올렸을 때 잠깐 뜨는 설명 상자다.
        tooltip=f"{row['대피소명']} ({row['추천구분']})",
        ).add_to(map_object)

        # 선은 실제 경로가 아니라 추천 기준이 되는 직선 거리 관계를 보여 주는 설명선이다.
        folium.PolyLine(
            locations=[[user_latitude, user_longitude], [shelter_latitude, shelter_longitude]],
            color=color,
            weight=2,
            opacity=0.75,
            dash_array="5 6",
        ).add_to(map_object)

        bounds.append([shelter_latitude, shelter_longitude])

    if len(bounds) > 1:
        # 추천 후보가 하나라도 있으면 사용자와 대피소가 모두 보이도록 자동 줌 범위를 다시 계산한다.
        # padding=(30, 30) 은 가장자리 여백을 조금 남겨 마커가 화면 끝에 딱 붙지 않게 만든다.
        map_object.fit_bounds(bounds, padding=(30, 30))

    return map_object


def render_recommendation_map(
    user_latitude: float,
    user_longitude: float,
    recommendations: pd.DataFrame,
    height: int = 460,
) -> None:
    """folium 지도를 Streamlit HTML 블록으로 렌더링한다.

    Streamlit 기본 지도 위젯 대신 folium HTML 을 쓰는 이유는
    작은 원형 마커와 직선 폴리라인을 현재 요구사항에 맞게 제어하기 쉽기 때문이다.
    """

    map_object = build_recommendation_map(
        user_latitude=user_latitude,
        user_longitude=user_longitude,
        recommendations=recommendations,
    )
    # folium 이 만든 HTML 을 그대로 렌더링해 Streamlit 안에서도 지도 스타일을 비교적 자유롭게 유지한다.
    # _repr_html_() 은 Folium 객체를 브라우저가 읽을 HTML 문자열로 바꿔 주는 메서드다.
    components.html(map_object._repr_html_(), height=height)
