# project_dashboard

전처리된 재난 특보 이력과 대피소 데이터를 이용해 대피소 추천 흐름과 분석 구조를 함께 정리하는 Streamlit 프로젝트입니다.

현재 앱은 과거 전처리 데이터 기준으로 동작합니다. 유료 API, 유료 지도 API, 실시간 공공 API는 연결하지 않았고, 그 확장 위치만 코드와 문서에 남겨 두었습니다.

## 페이지 구성

- `Home`: 프로젝트 목적, 데이터 범위, 페이지 읽는 순서
- `1 About`: 프로젝트 소개, 제약 사항, 다음 확장 계획
- `2 대피소 추천`: 선택 지역과 좌표 기준 Top 3 대피소 추천
- `3 작동 설명`: 추천 흐름과 데이터 계약 설명
- `4 실시간 준비`: 미래 실시간 확장 포인트 정리
- `5 Projects`: 현재 구현 작업 기록
- `6 Data Analysis`: 과거 특보와 대피소 분포 분석
- `7 Learning Log`: 학습 포인트와 확장 로드맵

## 데이터 폴더

앱은 기본적으로 저장소 내부 `preprocessing_data` 폴더를 읽습니다.
그래서 클론 직후에도 추가 설정 없이 실행할 수 있습니다.

다른 위치의 전처리 데이터를 쓰고 싶으면 아래 둘 중 하나로 경로를 덮어쓰면 됩니다.

1. 환경변수 `PREPROCESSING_DATA_DIR`
2. `.streamlit/secrets.toml` 의 `preprocessing_data_dir`

저장소에는 앱 실행에 필요한 `preprocessing_data/preprocessing/*.csv` 만 포함합니다.
외부 CSV와 저장소 내부 CSV 모두 읽기 전용으로 사용하며 앱 코드에서 수정하지 않습니다.

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
