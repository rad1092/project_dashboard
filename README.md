# 영남권 재난 대피 안내 대시보드

영남권 재난 특보와 대피소 데이터를 기반으로, **사용자 위치에 맞는 대피소 추천**, **경로 안내**, **재난 패턴 분석**을 제공하는 Streamlit 기반 멀티페이지 대시보드입니다.

이 프로젝트는 정적 전처리 데이터와 실시간 재난문자 정보를 함께 활용하여, 사용자가 현재 상황에 맞는 대피소를 확인하고 이동 경로를 탐색할 수 있도록 구성하였습니다. 또한 분석 페이지를 통해 재난 특보의 시계열 패턴, 지역별 특성, 대피소 분포를 함께 살펴볼 수 있습니다.

> 배포 URL은 추후 추가 예정입니다.  
> 주요 화면 스크린샷 및 데모 GIF도 추후 보완 가능합니다.

---

## 목차

- [프로젝트 개요](#프로젝트-개요)
- [주요 기능](#주요-기능)
- [데이터 구성](#데이터-구성)
- [기술 스택](#기술-스택)
- [실행 방법](#실행-방법)
- [환경 설정](#환경-설정)
- [테스트](#테스트)
- [저장소 구조](#저장소-구조)
- [제한사항](#제한사항)
- [향후 개선 계획](#향후-개선-계획)
- [팀 및 작성 정보](#팀-및-작성-정보)
- [라이선스](#라이선스)

---

## 프로젝트 개요

본 프로젝트는 재난 발생 시 사용자가 빠르게 대피소를 찾고, 현재 위치 기준으로 이동 경로를 확인하며, 지역별 재난 패턴까지 함께 파악할 수 있도록 설계한 대시보드입니다.

특히 다음 흐름에 초점을 두었습니다.

- **대피 안내 시뮬레이션**을 통해 재난 유형별 대피소 추천 제공
- **실시간 대피 안내**를 통해 최근 재난문자 기반 안내 흐름 제공
- **데이터 분석 페이지**를 통해 재난의 시계열 패턴, 지역별 특성, 대피소 분포 시각화 제공

---

## 주요 기능

### 1. HOME
- 전체 대피소 수, 권역 범위, 최신 특보 시각을 요약해 보여줍니다.
- `st.navigation` 기반으로 각 페이지로 이동할 수 있는 시작 화면입니다.

### 2. 대피 안내 시뮬레이션
- 브라우저 위치 권한 또는 수동 좌표 입력으로 현재 위치를 지정할 수 있습니다.
- 선택한 재난 유형에 맞는 가까운 대피소 후보를 추천합니다.
- Folium 지도를 통해 현재 위치, 대피소 위치, 이동 경로를 함께 시각화합니다.
- OSRM 도보 경로 조회가 실패할 경우 직선 fallback 경로로 안내를 이어갑니다.
- 최근 특보 이력과 추천 결과 표를 함께 확인할 수 있습니다.

### 3. 실시간 대피 안내
- `preprocessing_code/crawling.py`를 통해 실시간 재난문자를 크롤링합니다.
- `preprocessing_code/mock_disaster_message.py`를 사용하여 모의 재난문자를 생성하고 동일한 흐름을 테스트할 수 있습니다.
- 지원 권역은 `대구`, `울산`, `부산`, `경북`, `경남`입니다.
- 감지된 지역을 기준으로 최근 재난문자, 추천 대피소, 경로 지도를 한 화면에서 제공합니다.
- 사이드바에서 재난문자 새로고침, 모의 재난문자 실행, 위치 입력 방식을 제어할 수 있습니다.

### 4. 데이터 분석
- 분석 필터: `지역`, `재난종류`, `특보등급`
- KPI: 특보 기록 수, 재난종류 수, 지역 수, 최신 특보 시각
- 탭 구성
  - `재난 분포`: 특보등급별 재난 분포, 지역별 재난 특성 비교
  - `시계열 추이`: 월별 재난 분포, 재난종류별 월별 특보 패턴
  - `지역 비교`: 지역별 주의보 현황, 지역별 경보 현황, 지역별 대피소 분포, 재난종류별 특보 발생 지역
  - `권역 대피소 지도`: HTML 지도를 임베드하여 전체 권역 대피소를 표시
- 하단 `원본 데이터` expander에서 필터 결과 테이블을 직접 확인할 수 있습니다.

---

## 데이터 구성

### 정적 데이터
- `preprocessing_data/preprocessing/danger_clean.csv`
- `preprocessing_data/preprocessing/final_shelter_dataset.csv`
- `preprocessing_data/preprocessing/earthquake_shelter_clean_2.csv`
- `preprocessing_data/preprocessing/tsunami_shelter_clean_2.csv`

### 실시간 및 런타임 데이터
- `preprocessing_code/data/disaster_message_realtime.csv`
- `preprocessing_code/data/Emergency_shelter.db`

### 데이터 출처 및 갱신 방식
본 프로젝트는 공공 재난 특보 데이터, 대피소 데이터, 실시간 재난문자 크롤링 결과를 활용합니다.

- 정적 전처리 데이터는 프로젝트 기준 데이터셋을 바탕으로 수동 관리합니다.
- 실시간 재난문자 데이터는 크롤링 실행 또는 페이지 새로고침 시 갱신됩니다.
- 분석 페이지는 SQLite DB를 우선 조회하고, DB가 없을 경우 CSV를 fallback으로 사용합니다.
- 실시간 페이지는 크롤링 결과를 세션 상태에 캐시하며, 갱신 실패 시 직전 결과를 유지하도록 설계되어 있습니다.

> 사용 데이터의 상세 출처와 갱신 주기는 추후 README에 더 구체적으로 보완할 수 있습니다.

---

## 기술 스택

- Python 3.12
- Streamlit
- Pandas / NumPy
- Plotly
- Folium
- Selenium
- streamlit-geolocation
- SQLite

---

## 실행 방법

### 1. 의존성 설치
이 저장소는 `pyproject.toml`과 `uv.lock`을 함께 사용합니다.

```powershell
uv sync --dev
```

`uv`를 사용하지 않는 경우에는 Python 3.12 환경에 맞추어 필요한 패키지를 직접 설치해야 합니다.

### 2. 앱 실행

```powershell
streamlit run app.py
```

### 3. 모의 재난문자 생성

```powershell
.\.venv\Scripts\python preprocessing_code\mock_disaster_message.py --sido 경북 --sigungu 포항시
```

위 명령은 `preprocessing_code/data/disaster_message_realtime.csv`를 덮어써서, 실시간 대피 안내 페이지에서 즉시 읽을 수 있는 모의 데이터를 생성합니다.

---

## 환경 설정

### 데이터 경로 오버라이드

```powershell
$env:PREPROCESSING_DATA_DIR="D:\\my-preprocessing-data"
```

또는 `.streamlit/secrets.toml`에 아래와 같이 설정할 수 있습니다.

```toml
preprocessing_data_dir = "D:/my-preprocessing-data"
```

### 경로 엔진 설정
앱은 OSRM 도보 경로 조회를 사용합니다.

```powershell
$env:OSRM_BASE_URL="http://router.project-osrm.org"
```

- 별도 값을 지정하지 않으면 기본 OSRM 엔드포인트를 사용합니다.
- 경로 조회가 실패할 경우 직선 fallback 경로를 표시합니다.

### 실시간 크롤링 실행 조건
- 실시간 재난문자 크롤링은 Selenium + Chromium 환경이 필요합니다.
- 배포용 시스템 패키지는 `packages.txt`에 `chromium`, `chromium-driver`로 정의되어 있습니다.

---

## 테스트

```powershell
.\.venv\Scripts\python -m pytest -q
```

현재 테스트는 아래 범위를 포함합니다.

- HOME 메타 정보 및 KPI 계산
- 대피 안내 시뮬레이션의 경로 계산, OSRM fallback, 지도 생성
- 실시간 재난문자 로딩, 모의 재난문자 생성, 세션 상태 처리
- 분석 페이지 필터 및 차트 builder
- 문서 존재 여부와 주요 모듈의 compile/import 가능 여부

테스트 환경에서는 `PROJECT_DASHBOARD_IMPORT_ONLY=1`을 사용하여, 페이지 import 시 `render_page()`가 자동 실행되지 않도록 설정합니다.

---

## 저장소 구조

```text
.
├─ app.py
├─ pages/
│  ├─ 1_대피_안내_시뮬레이션.py
│  ├─ 2_실시간_대피_안내.py
│  └─ 3_데이터_분석.py
├─ preprocessing_code/
├─ preprocessing_data/
├─ docs/
├─ tests/
├─ .streamlit/
├─ pyproject.toml
├─ packages.txt
└─ uv.lock
```

---

## 제한사항

- 실시간 재난문자 수집은 Selenium 및 Chromium 실행 환경이 필요합니다.
- 경로 안내는 OSRM 엔드포인트 상태에 영향을 받을 수 있으며, 실패 시 직선 fallback 경로를 사용합니다.
- 분석 및 추천 기능은 영남권 5개 권역을 중심으로 구성되어 있습니다.
- 데이터 품질은 원본 공공데이터 및 전처리 결과에 영향을 받습니다.
- 일부 실시간 기능은 배포 환경보다 로컬 환경에서 더 안정적으로 동작할 수 있습니다.

---

## 향후 개선 계획

- 전국 단위 권역 확장
- 실시간 재난문자 자동 갱신 고도화
- 사용자 위치 기반 추천 로직 개선
- 수용인원과 재난 유형을 함께 반영한 대피소 추천 기능 추가
- 모바일 UI 및 지도 인터랙션 개선
- 사용 데이터 출처 및 갱신 주기 문서화 보강
- 대표 스크린샷 및 서비스 데모 자료 추가

---

## 자료 참고 사이트
- 재난 안전 데이터 공유 플랫폼
- 국민 재난 안전 포털
- 공공데이터 포털
---

## 팀 및 작성 정보

- 개발 및 구현: 김홍대, 남연정, 오승주, 최해목
- 프로젝트 형태: 팀 프로젝트
- 주요 구현 범위: 대피소 추천, 실시간 대피 안내, 데이터 분석 페이지 구성



