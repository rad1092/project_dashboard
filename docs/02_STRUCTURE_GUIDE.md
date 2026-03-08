# 폴더와 파일 구조 가이드

## 루트

- `app.py`: 홈 화면 진입점
- `README.md`: 프로젝트 소개와 실행 방법
- `pyproject.toml`: 실행 환경과 의존성
- `.streamlit/config.toml`: Streamlit 테마 설정
- `.streamlit/secrets.toml.example`: 외부 데이터 경로와 미래 API 자리표시자 예시

## `dashboard/`

- `config.py`: 앱 제목, 페이지 메타데이터, 공통 설정 함수
- `content.py`: 소개 문구, 흐름 설명, 로드맵, 미래 확장 텍스트
- `components/layout.py`: 공통 제목/리스트 UI
- `components/charts.py`: 분석 페이지용 Plotly 차트
- `components/disaster_sections.py`: 추천 카드, 흐름 카드, 데이터셋 카드
- `components/disaster_map.py`: 무료 OSM 지도 렌더링
- `services/disaster_data.py`: 외부 전처리 폴더 탐색, CSV 로딩, 특보 요약, 좌표 기반 지역 자동 감지
- `services/shelter_recommendation.py`: 재난 유형 정규화, 거리 계산, 추천 규칙
- `services/analysis_data.py`: 분석 페이지용 특보 DataFrame 과 KPI
- `utils/formatters.py`: 숫자, 날짜, 거리 표시 포맷

## `pages/`

- `1_About.py`: 프로젝트 소개
- `2_대피소_추천.py`: 좌표 입력 -> 지역 자동 감지 -> 필요 시 수동 보정 -> 추천 결과를 보여주는 핵심 화면
- `3_작동_설명.py`: 추천 플로우 설명
- `4_실시간_준비.py`: 미래 실시간 확장 준비
- `5_Projects.py`: 작업 카드 기록
- `6_Data_Analysis.py`: 과거 특보/대피소 분석
- `7_Learning_Log.py`: 학습 로그와 로드맵

## `tests/`

- `conftest.py`: 루트 import 설정과 임시 전처리 데이터 fixture
- `test_analysis_data.py`: 분석용 특보 DataFrame 계약 검증
- `test_content.py`: 콘텐츠 구조와 페이지 문법 검증
- `test_disaster_data.py`: 경로 탐색, CSV 로딩, 특보 요약 검증
- `test_shelter_recommendation.py`: 정규화, 거리 계산, 추천 규칙 검증

## 데이터 폴더

저장소 안의 `preprocessing_data` 폴더는 다음처럼 본다.

- `preprocessing/*.csv`: 앱이 읽는 전처리 완료 데이터
- `py/*.py`: 전처리 참고 스크립트
- `jupyter/*.ipynb`: 전처리 과정 설명 노트북
- `raw/*.csv`: 원본 데이터

이 폴더의 CSV는 앱에서 수정하지 않는다.
앱 실행에 실제로 포함되는 파일은 `preprocessing/*.csv` 4개이며,
나머지 하위 폴더는 참고 자료 또는 원본 보관 용도로만 둔다.

## 추천 페이지 구조 메모

현재 추천 페이지는 `시도/시군구 먼저 선택` 구조가 아니다.
앱은 먼저 위도/경도를 받고, `dashboard/services/disaster_data.py` 에서
통합 대피소 기준 지역 중심 좌표를 계산한 뒤 가장 가까운 지역을 감지한다.

이후 흐름은 아래처럼 연결된다.

1. 좌표 입력
2. 감지 지역 계산
3. 감지 지역으로 최근 특보 요약과 기본 재난 선택 계산
4. 필요 시 `지역 직접 수정` 영역에서 시도/시군구 보정
5. 최종 활성 지역으로 추천 후보 필터링

중요한 한계도 함께 기억해야 한다.

- 현재 지역 감지는 행정경계 기반 역지오코딩이 아니다.
- 외부 지도 API 없이 동작해야 하므로 `가장 가까운 지역 중심 좌표` 방식이다.
- 따라서 감지 결과가 애매할 때를 대비해 수동 보정 UI 를 유지한다.
