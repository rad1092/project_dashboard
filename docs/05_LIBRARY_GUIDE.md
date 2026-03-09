# 라이브러리 가이드

## 이 문서의 목적

이 저장소가 어떤 라이브러리를 왜 쓰는지 빠르게 파악하도록 돕는 문서다.
초보자라면 "이 기능이 어느 파일에서 쓰이는가"까지 같이 보는 것이 도움이 된다.

## 현재 바로 쓰는 라이브러리

### `streamlit`
- 페이지 구성, 입력 위젯, 데이터 표시에 사용
- 현재 사용 위치: `app.py`, `pages/*`, `dashboard/config.py`, `dashboard/components/*`
- 초보자 메모: `st.columns`, `st.container`, `st.sidebar`, `st.dataframe` 같은 UI 조립 함수가 여기서 나온다.

### `pandas`
- 전처리 CSV 로딩, 컬럼 정리, 필터링, 집계에 사용
- 현재 사용 위치: `dashboard/services/*`, `pages/6_Data_Analysis.py`
- 초보자 메모: `copy()`, `groupby()`, `sort_values()`, `head()`, `map()` 같은 데이터 처리 패턴이 자주 보인다.

### `plotly`
- 과거 특보와 대피소 분포 차트 렌더링에 사용
- 현재 사용 위치: `dashboard/components/charts.py`
- 초보자 메모: 차트 함수는 DataFrame 을 받아 `Figure` 를 반환하는 공통 패턴을 따른다.

### `folium`
- 무료 OSM 지도 렌더링에 사용
- 현재 사용 위치: `dashboard/components/disaster_map.py`
- 초보자 메모: 추천 계산은 하지 않고, 이미 계산된 대피소 후보를 지도에 그리는 역할만 맡는다.

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
- 새로운 라이브러리를 넣을 때는 "페이지에서 직접 호출할지, 서비스 계층에서 감쌀지"를 먼저 결정한다.
