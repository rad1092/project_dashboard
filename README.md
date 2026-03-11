# 재난 대피소 추천 워크스페이스

전처리된 재난 특보 이력과 대피소 데이터를 바탕으로, 현재 좌표 기준 추천과 실시간 테스트, 데이터 분석 화면을 함께 제공하는 Streamlit 앱이다.

## 프로젝트 개요

- `app.py`는 홈 화면이다.
- `dashboard_data.py`는 여러 화면이 같이 쓰는 데이터 로딩과 전처리 기준을 모아 둔 공용 모듈이다.
- 실제 화면은 `pages/` 아래 3개 파일로 나뉜다.

## 현재 화면 구성

- 홈
  - 현재 데이터 상태, 주요 KPI, 페이지 이동 안내를 보여준다.
- `1. 대피소 추천`
  - 입력 좌표로 지역을 추정하고, 재난 유형에 맞는 대피소 Top 3를 계산한다.
- `2. 실시간 테스트`
  - 브라우저 위치와 OSRM 도보 경로를 붙여 추천 흐름을 시험한다.
- `3. Data Analysis`
  - 과거 특보 이력과 대피소 분포를 차트로 요약한다.

## 데이터 폴더 구조와 경로 우선순위

앱은 아래 CSV를 읽는다.

```text
preprocessing_data/
`- preprocessing/
   |- danger_clean.csv
   |- final_shelter_dataset.csv
   |- earthquake_shelter_clean_2.csv
   `- tsunami_shelter_clean_2.csv
```

`dashboard_data.py`의 `resolve_data_dir()`는 아래 순서대로 데이터 폴더를 찾는다.

1. 함수 인자로 직접 넘긴 경로
2. 환경변수 `PREPROCESSING_DATA_DIR`
3. `.streamlit/secrets.toml`의 `preprocessing_data_dir`
4. 저장소 내부 `preprocessing_data/`
5. `~/Desktop/preprocessing_data`

## 실행 방법

```powershell
streamlit run app.py
```

## 테스트 방법

```powershell
.\.venv\Scripts\python -m pytest -q
```

테스트는 `PROJECT_DASHBOARD_IMPORT_ONLY=1`를 사용해서 페이지가 import될 때 화면을 자동 렌더링하지 않게 막고, 각 helper 함수와 데이터 흐름을 직접 검증한다.

## docs 안내

- `docs/01_프로젝트_구조.md`
  - 현재 실행 파일 구조와 `dashboard_data.py`를 분리한 이유를 설명한다.
- `docs/02_데이터_흐름.md`
  - CSV 경로 우선순위와 화면별 데이터 사용 방식을 설명한다.
- `docs/03_테스트_가이드.md`
  - fixture 구조와 테스트 목적, 환경 이슈 확인 포인트를 설명한다.
