# 내부 함수 정리 기준

## 왜 구조는 유지하고 내부 함수만 줄이나

- 이 저장소의 기준 구조는 `app.py + pages/*.py` 평면 구조다.
- 페이지 간 import 를 다시 늘리거나 새 공용 모듈을 만들면 읽는 흐름이 다시 복잡해진다.
- 대신 각 파일 안에서 과하게 잘게 쪼개진 UI helper, 얕은 포맷 함수, 한 번만 쓰는 변수와 `with` 중첩을 줄여 `render_page()` 기준으로 위에서 아래로 읽히게 만든다.

## 남길 함수와 접을 함수

### 남길 함수

- 테스트가 직접 검증하는 데이터 경로, CSV 로더, 분석/추천 계산 함수
- 같은 파일 안에서 2회 이상 재사용되는 비사소한 데이터 처리 함수
- 차트 생성처럼 화면에서 바로 대체하기 어려운 계산 함수

### 접을 함수

- `apply_page_config`
- `render_page_intro`
- 단순 `format_*`
- 얕은 카드 렌더 함수
- 한 번만 쓰는 상태 라벨 함수
- 설명 페이지에서만 쓰던 긴 스텁 코드와 데이터셋 카탈로그 계산

## 설명성 페이지 운영 원칙

- `pages/1_About.py`, `pages/3_작동_설명.py`, `pages/4_실시간_준비.py` 는 더 이상 CSV 를 직접 읽지 않는다.
- 상세 설명과 긴 코드 스텁은 docs 로 이동하고, Streamlit 페이지에는 핵심 요약만 남긴다.
- `pages/5_Projects.py`, `pages/7_Learning_Log.py` 는 유지하되 `render_page()` 중심으로 읽히도록 단순화한다.

## 실페이지 정리 원칙

### `pages/2_대피소_추천.py`

- `resolve_data_dir`, `load_*_dataframe*`, `get_recent_alerts`, `build_alert_summary`, `classify_disaster_type`, `haversine_km`, `recommend_shelters` 는 유지한다.
- `_haversine_km` 는 제거하고 `haversine_km` 하나만 사용한다.
- 카드/지도 렌더 glue 와 단순 포맷 함수는 `render_page()` 쪽으로 접는다.

### `pages/6_Data_Analysis.py`

- 데이터 로더, `classify_disaster_type`, `load_analysis_dataset`, `build_kpis`, 차트 빌더는 유지한다.
- 페이지 소개와 단순 포맷 helper 는 `render_page()` 로 이동한다.
- 빈 Figure helper 처럼 여러 차트에서 재사용되는 함수는 유지한다.

### `app.py`

- 홈 메타데이터, 데이터 로더, `load_analysis_dataset`, `build_kpis`, `build_dataset_catalog` 는 유지한다.
- 페이지 크롬과 단순 포맷 helper 는 인라인 처리한다.

## `with` 와 지역변수 기준

- 한 번만 쓰는 컨테이너 변수는 만들지 않는다.
- UI 블록은 `render_page()` 에서 위에서 아래로 읽히게 둔다.
- `with st.container(...)` 는 섹션 단위로만 남기고, 얕은 중첩은 줄인다.
- 한 번만 쓰는 포맷 함수 대신 그 자리에서 바로 문자열을 만든다.

## 상세 설명을 docs 로 옮긴 항목

### 설명 페이지 세부 흐름

- 좌표 입력 후 지역 중심 좌표로 활성 지역을 감지하는 과정
- 최근 특보 요약과 재난 그룹 정규화 과정
- 전용 대피소 우선 추천과 통합 대피소 fallback 기준
- 직선 거리 기반 지도 시각화와 실제 경로 미지원 이유

### 실시간 준비 스텁

```python
def get_browser_location() -> tuple[float, float] | None:
    # 브라우저 위치 권한을 받은 뒤 사용자의 현재 좌표를 반환한다.
    return None


def fetch_realtime_alerts() -> list[dict[str, str]]:
    # 실시간 공공 API가 준비되면 최신 특보를 읽어 현재 재난 유형을 갱신한다.
    return []


def build_live_route(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
) -> dict[str, object] | None:
    # 실제 경로 API를 붙이면 도로 기준 경로와 이동 시간을 반환한다.
    return None
```

## 구현 후 확인 기준

- 설명 페이지는 docs 경로를 안내하고, 긴 구현 설명은 페이지 안에 직접 늘어놓지 않는다.
- 추천/분석/홈 페이지는 핵심 데이터 helper 이름을 유지한다.
- 테스트는 정적 페이지의 요약 상수와 docs 기준 존재를 함께 검증한다.
