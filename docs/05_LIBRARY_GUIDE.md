# 라이브러리 가이드

## 현재 바로 쓰는 라이브러리

### `streamlit`
- 페이지 구성, 입력 위젯, 데이터 표시에 사용
- 현재 사용 위치: `app.py`, `pages/*`, `dashboard/config.py`, `dashboard/components/*`

### `pandas`
- 전처리 CSV 로딩, 컬럼 정리, 필터링, 집계에 사용
- 현재 사용 위치: `dashboard/services/*`, `pages/6_Data_Analysis.py`

### `plotly`
- 과거 특보와 대피소 분포 차트 렌더링에 사용
- 현재 사용 위치: `dashboard/components/charts.py`

### `folium`
- 무료 OSM 지도 렌더링에 사용
- 현재 사용 위치: `dashboard/components/disaster_map.py`

## 가까운 확장에서 쓸 수 있는 라이브러리

### `requests`
- 실시간 공공 API 연동 시 사용 가능
- 현재 앱에서는 직접 호출하지 않음

### `sqlalchemy`
- 장기적으로 사용자 위치 기록이나 결과 저장이 필요할 때 검토 가능
- 현재는 미사용

## 주의점

- 유료 지도 SDK 나 유료 경로 API 전용 라이브러리는 현재 구조에 넣지 않는다.
- rerun 이 자주 일어나는 Streamlit 특성상, 무거운 CSV 로딩은 서비스 계층과 캐시로 분리한다.
