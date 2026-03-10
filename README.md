# project_dashboard

전처리된 재난 특보 이력과 대피소 데이터를 이용해 대피소 추천 흐름과 분석 구조를 함께 정리하는 Streamlit 프로젝트입니다.

현재 앱은 과거 전처리 데이터 기준으로 동작합니다. 유료 API, 유료 지도 API, 실시간 공공 API는 연결하지 않았고, 그 확장 위치만 코드와 문서에 남겨 두었습니다.

처음 들어온 사람이 가장 먼저 이해하면 좋은 핵심은 아래 세 가지입니다.

- 추천 페이지는 `좌표 입력 -> 감지 지역 -> 활성 지역 -> 추천 후보` 흐름으로 움직입니다.
- 현재 지역 감지는 행정경계 기반 역지오코딩이 아니라, 통합 대피소 지역 중심 좌표를 이용한 근접 추정입니다.
- 실시간 기능은 아직 실행하지 않고, `4 실시간 준비` 페이지와 관련 주석에서만 확장 위치를 설명합니다.

## 페이지 구성

- `Home`: 프로젝트 목적, 데이터 범위, 페이지 읽는 순서
- `1 About`: 프로젝트 소개, 현재 한계, 다음 확장 계획
- `2 대피소 추천`: 좌표 입력을 기준으로 감지 지역과 활성 지역을 정한 뒤 Top 3 대피소 추천
- `3 작동 설명`: 감지 지역, 활성 지역, 추천 규칙, 직선 거리 기준을 단계별로 설명
- `4 실시간 준비`: 자동 위치, 실시간 특보, 경로 API 를 나중에 어디에 붙일지 정리
- `5 Projects`: 현재 구현 작업 기록
- `6 Data Analysis`: 과거 특보와 대피소 분포 분석
- `7 Learning Log`: 학습 포인트와 확장 로드맵

처음 읽을 때 권장 순서는 `Home -> 1 About -> 2 대피소 추천 -> 3 작동 설명 -> 4 실시간 준비` 입니다.
이 순서대로 보면 현재 동작과 미래 확장을 섞지 않고 이해하기 쉽습니다.

## 데이터 폴더

앱은 기본적으로 저장소 내부 `preprocessing_data` 폴더를 읽습니다.
그래서 클론 직후에도 추가 설정 없이 실행할 수 있습니다.

다른 위치의 전처리 데이터를 쓰고 싶으면 아래 둘 중 하나로 경로를 덮어쓰면 됩니다.

1. 환경변수 `PREPROCESSING_DATA_DIR`
2. `.streamlit/secrets.toml` 의 `preprocessing_data_dir`

저장소에는 앱 실행에 필요한 `preprocessing_data/preprocessing/*.csv` 만 포함합니다.
외부 CSV와 저장소 내부 CSV 모두 읽기 전용으로 사용하며 앱 코드에서 수정하지 않습니다.

현재 앱이 기대하는 핵심 CSV 는 아래 4개입니다.

- `danger_clean.csv`: 재난 특보 이력
- `final_shelter_dataset.csv`: 통합 또는 일반 대피소
- `earthquake_shelter_clean_2.csv`: 지진 전용 대피소
- `tsunami_shelter_clean_2.csv`: 지진해일/쓰나미 전용 대피소

서비스 계층은 이 CSV 들을 읽은 뒤 컬럼을 정리하고, 페이지는 정리된 DataFrame 만 사용합니다.

## 실행 방법

```powershell
.venv\Scripts\activate
uv sync --dev
streamlit run app.py
```

## 테스트

```powershell
.venv\Scripts\python.exe -m pytest
```

현재 테스트는 아래 질문을 중심으로 구성되어 있습니다.

- 데이터 폴더 탐색 우선순위가 맞는가
- CSV 컬럼 계약이 유지되는가
- 감지 지역 계산과 최근 특보 요약이 기대대로 동작하는가
- 전용/기본/대체 대피소 추천 규칙이 유지되는가
- 콘텐츠 데이터와 페이지 문법이 깨지지 않았는가

## 문서

- `docs/01_PROJECT_DIRECTION.md`: 프로젝트 목표와 개발 원칙
- `docs/02_STRUCTURE_GUIDE.md`: 현재 폴더/파일 구조 설명
- `docs/03_STREAMLIT_LEARNING_GUIDE.md`: 이 저장소를 통해 배우는 Streamlit 포인트
- `docs/04_UPDATE_AND_EXPANSION_GUIDE.md`: 수정 및 확장 절차
- `docs/05_LIBRARY_GUIDE.md`: 사용 라이브러리와 주의점
- `docs/06_PROJECT_EXPLANATION_GUIDE.md`: 프로젝트 설명용 문장 가이드
- `docs/07_WORKING_CHECKLIST.md`: 작업 전후 점검표
- `docs/08_CODEBASE_OVERVIEW.md`: 전체 코드 흐름 설명
- `docs/09_ENTRYPOINT_AND_CONFIG_GUIDE.md`: 진입점과 설정 파일 안내
- `docs/10_CONTENT_AND_DATA_GUIDE.md`: 콘텐츠와 데이터 서비스 설명
- `docs/11_COMPONENT_AND_PAGE_GUIDE.md`: 컴포넌트와 페이지 역할 정리
- `docs/12_TEST_AND_VERIFICATION_GUIDE.md`: 테스트와 검증 방법
- `docs/13_EXPORT_GUIDE.md`: 문서/발표 자료로 옮길 때의 기준
- `docs/14_CODING_AND_CLASS_GUIDELINES.md`: 코드 작성과 책임 분리 원칙
- `docs/15_DATA_SOURCE_EXPANSION_GUIDE.md`: 실시간 데이터 확장 가이드
- `docs/16_PAGE_AND_FEATURE_EXPANSION_GUIDE.md`: 페이지와 기능 확장 기준
- `docs/17_CONNECTION_MAP_GUIDE.md`: 전체 연결 구조와 추천 페이지 호출 흐름 다이어그램

입문자라면 먼저 `docs/01` 부터 `docs/04` 까지 읽고,
그다음 실제 코드와 연결되는 `docs/08` 부터 `docs/12` 를 보는 순서를 권장합니다.
