# 콘텐츠와 데이터 가이드

## `dashboard/content.py`

이 파일은 소개 문구, 프로젝트 카드, 흐름 설명, 미래 확장 설명을 한곳에 모은다.
문구를 여러 페이지에 복사해 두지 않기 위해 존재한다.

## `dashboard/services/disaster_data.py`

이 파일은 저장소 내부 기본 `preprocessing_data` 폴더를 찾고, CSV 를 읽고, 특보 요약과 데이터셋 설명 정보를 만든다.
현재 구조에서 데이터 경로 계약의 중심 파일이다.

### 핵심 함수

- `resolve_data_dir()`: 기본 데이터 폴더 탐색과 optional override 처리
- `load_dataset_bundle()`: CSV 4종 로딩
- `get_recent_alerts()`: 최근 특보 일부 반환
- `build_alert_summary()`: 추천 페이지 상단 요약
- `build_dataset_catalog()`: 설명 페이지용 데이터셋 메타 정보

## `dashboard/services/shelter_recommendation.py`

이 파일은 재난 그룹 정규화, 직선 거리 계산, 전용/대체 대피소 추천 규칙을 관리한다.
추천 정책이 바뀌면 가장 먼저 이 파일을 봐야 한다.

## `dashboard/services/analysis_data.py`

과거 특보 데이터를 분석 페이지에서 쓰기 좋은 형태로 정리하고 KPI 를 계산한다.

## `dashboard/utils/formatters.py`

숫자, 날짜, 거리 표시 형식을 한곳에 모아 페이지마다 문자열 포맷이 달라지지 않게 한다.
