# 재난 대피소 추천 워크스페이스

전처리된 재난 특보 이력, 대피소 데이터, 크롤링된 실시간 재난문자를 바탕으로 추천, 실시간 테스트, 재난문자 안내, 분석 화면을 제공하는 Streamlit 앱이다.

## 프로젝트 개요

- `app.py`는 홈 화면이다.
- `dashboard_data.py`는 기존 `danger_clean.csv` 기반 공용 데이터 로더다.
- `crawler_alerts_data.py`는 `preprocessing_code/crawling.py` 결과 CSV 전용 로더다.
- `realtime_support.py`는 위치 입력, OSRM 경로, folium 지도 생성을 Page 2와 Page 4가 함께 쓰는 공용 helper 모듈이다.
- 실제 화면은 `pages/` 아래 4개 파일로 나뉜다.

## 현재 화면 구성

- 홈
  - 현재 데이터 상태, 주요 KPI, 페이지 이동 흐름을 보여준다.
- `1. 대피소 추천`
  - 입력 좌표로 지역을 추정하고, 재난 유형에 맞는 대피소 Top 3를 추천한다.
- `2. 실시간 테스트`
  - 브라우저 위치와 OSRM 도보 경로를 붙여 추천 흐름을 테스트한다.
- `3. Data Analysis`
  - 과거 특보 이력과 대피소 분포를 차트로 요약한다.
- `4. 재난문자 대피 안내`
  - `preprocessing_code/data/disaster_message_realtime.csv` 기준 최근 재난문자를 현재 위치와 연결해 대피소와 경로를 안내한다.

## 데이터 폴더 구조와 경로 우선순위

앱은 아래 CSV를 읽는다.

```text
preprocessing_data/
`- preprocessing/
   |- danger_clean.csv
   |- final_shelter_dataset.csv
   |- earthquake_shelter_clean_2.csv
   `- tsunami_shelter_clean_2.csv

preprocessing_code/
`- data/
   `- disaster_message_realtime.csv
```

`dashboard_data.py`의 `resolve_data_dir()`는 아래 순서대로 기존 전처리 폴더를 찾는다.

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

테스트는 `PROJECT_DASHBOARD_IMPORT_ONLY=1`를 사용해서 페이지가 import될 때 화면을 자동 렌더링하지 않게 막고, helper 함수와 데이터 흐름을 직접 검증한다.

## docs 안내

- `docs/01_프로젝트_구조.md`
  - 실행 파일 구조와 공용 모듈 분리 이유를 설명한다.
- `docs/02_데이터_흐름.md`
  - 기존 전처리 CSV와 크롤러 CSV가 어떤 페이지에서 어떻게 쓰이는지 설명한다.
- `docs/03_테스트_가이드.md`
  - fixture 구조와 테스트 모듈 구성을 정리한다.
