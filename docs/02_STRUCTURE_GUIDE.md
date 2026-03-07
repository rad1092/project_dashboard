# 폴더와 파일 구조 가이드

## 이 문서의 목적

이 문서는 "폴더가 왜 이렇게 나뉘었는가"만 설명하는 문서가 아니다. 실제로 존재하는 관리 대상 파일을 빠짐없이 훑으면서, 각 파일이 무엇을 담당하는지, 언제 수정해야 하는지, 어떤 파일과 연결되는지를 한 번에 파악하게 하는 문서다.

## 먼저 알아둘 점

- 이 문서는 저장소에 직접 관리되는 파일만 설명한다.
- `__pycache__`, `.pytest_cache` 같은 생성 산출물은 설명 대상에서 제외한다.
  - 이유: 직접 수정하는 파일이 아니고, 실행 과정에서 자동 생성되기 때문이다.

## 루트 파일

| 파일 | 역할 | 왜 필요한가 | 언제 수정하는가 | 연결 파일 | 주의점 |
| --- | --- | --- | --- | --- | --- |
| `README.md` | 저장소 첫 소개 | 처음 보는 사람이 저장소 목적을 가장 먼저 이해하게 해준다. | 저장소 목적, 문서 목록, 실행 방법이 바뀔 때 | `docs/*`, `app.py` | README와 실제 구조가 다르면 신뢰도가 떨어진다. |
| `pyproject.toml` | 프로젝트 메타와 의존성 정의 | 실행 환경과 패키지 버전을 관리한다. | 라이브러리를 추가/삭제하거나 설명 문구를 바꿀 때 | `uv.lock`, `.venv` | 버전 제약을 무리하게 올리면 Streamlit과 충돌할 수 있다. |
| `uv.lock` | 실제 해석된 의존성 잠금 파일 | 환경 재현성을 높여준다. | `pyproject.toml` 변경 후 lock을 다시 맞출 때 | `pyproject.toml` | 직접 손으로 편집하지 않는다. |
| `.gitignore` | Git 추적 제외 규칙 | 비밀정보, 캐시, 로컬 산출물이 올라가지 않게 한다. | 새 산출물이나 비밀파일이 생길 때 | `.streamlit/secrets.toml`, 테스트/캐시 폴더 | secrets나 캐시를 빼먹으면 저장소가 지저분해진다. |
| `app.py` | 홈 화면 진입점 | 저장소 목적, 현재 상태, 문서 진입 경로를 보여준다. | 홈 화면 메시지나 요약 KPI가 바뀔 때 | `dashboard/config.py`, `dashboard/content.py`, `dashboard/services/analysis_data.py` | 화면 설명과 실제 docs가 어긋나지 않게 해야 한다. |

## 설정 파일

| 파일 | 역할 | 왜 필요한가 | 언제 수정하는가 | 연결 파일 | 주의점 |
| --- | --- | --- | --- | --- | --- |
| `.streamlit/config.toml` | Streamlit 테마와 브라우저 설정 | 앱 전체 톤과 기본 동작을 맞춘다. | 테마, 색상, 사용 통계 옵션을 바꿀 때 | `app.py`, `pages/*` | TOML 문법과 인코딩이 틀리면 앱 시작 시 경고가 난다. |
| `.streamlit/secrets.toml.example` | 비밀정보 템플릿 | 실제 secrets 파일 구조를 미리 설명한다. | API 키, DB URL 같은 비밀정보 형식이 생길 때 | 향후 `requests`, `sqlalchemy` 연동 코드 | 예시 파일만 Git에 두고 실제 secrets는 올리지 않는다. |

## `dashboard/` 패키지

### `dashboard/__init__.py`

- 역할: `dashboard`를 패키지로 인식하게 한다.
- 왜 필요한가: `from dashboard...` 형태의 import를 안정적으로 쓰기 위해서다.
- 언제 수정하는가: 거의 수정하지 않는다.
- 연결 파일: `app.py`, `pages/*`, `tests/*`
- 주의점: 내용이 짧아도 지우면 import 구조가 흔들릴 수 있다.

### `dashboard/config.py`

- 역할: 앱 제목, 아이콘, 페이지 메타데이터, 공통 페이지 설정 함수를 둔다.
- 왜 필요한가: 페이지별 설정을 제각각 쓰지 않게 막아준다.
- 언제 수정하는가: 홈 라벨, 앱 제목, 페이지 요약, 아이콘을 바꿀 때
- 연결 파일: `app.py`, `pages/*`
- 주의점: 페이지 제목과 README 설명 톤이 다르면 저장소 메시지가 흔들린다.

### `dashboard/content.py`

- 역할: 자기소개, 프로젝트 카드, 학습 주제, 로드맵 텍스트 원본을 모은다.
- 왜 필요한가: 문구를 여러 파일에 흩어두지 않기 위해서다.
- 언제 수정하는가: 소개 문구, 프로젝트 설명, 로드맵, 학습 내용이 바뀔 때
- 연결 파일: `pages/1_About.py`, `pages/2_Projects.py`, `pages/4_Learning_Log.py`, `app.py`
- 주의점: 값을 바꾸면 여러 페이지가 동시에 영향받으므로 연결 화면을 같이 확인한다.

## `dashboard/components/`

### `dashboard/components/__init__.py`

- 역할: `components` 폴더를 패키지로 인식하게 한다.
- 왜 필요한가: 공통 UI 유틸 import를 안정적으로 유지하기 위해서다.
- 언제 수정하는가: 거의 수정하지 않는다.
- 연결 파일: `pages/*`
- 주의점: 빈 파일처럼 보여도 import 안정성 역할이 있다.

### `dashboard/components/layout.py`

- 역할: 페이지 소개, 칩 목록, 보더 박스 목록 같은 반복 UI를 함수로 제공한다.
- 왜 필요한가: 비슷한 UI 마크업을 여러 페이지에 복붙하지 않게 한다.
- 언제 수정하는가: 페이지 공통 헤더 모양이나 반복 리스트 표현을 바꿀 때
- 연결 파일: `pages/1_About.py`, `pages/2_Projects.py`, `pages/4_Learning_Log.py`
- 주의점: 표현 함수 안에 데이터 가공 로직까지 넣지 않는다.

### `dashboard/components/charts.py`

- 역할: Plotly 차트 생성 함수를 모아둔다.
- 왜 필요한가: 페이지 파일에서 집계와 차트 구성을 중복하지 않기 위해서다.
- 언제 수정하는가: 새 차트가 필요하거나 기존 차트 표현을 바꿀 때
- 연결 파일: `pages/3_Data_Analysis.py`
- 주의점: 특정 페이지 전용 예외처리를 너무 많이 넣으면 재사용성이 떨어진다.

## `dashboard/services/`

### `dashboard/services/__init__.py`

- 역할: `services` 폴더를 패키지로 인식하게 한다.
- 왜 필요한가: 데이터 관련 모듈을 import할 때 경로를 안정화한다.
- 언제 수정하는가: 거의 수정하지 않는다.
- 연결 파일: `app.py`, `pages/3_Data_Analysis.py`, `tests/test_analysis_data.py`
- 주의점: 파일이 짧아도 패키지 경계 역할이 있다.

### `dashboard/services/analysis_data.py`

- 역할: 샘플 데이터 생성과 KPI 계산을 담당한다.
- 왜 필요한가: 데이터 준비를 페이지 밖으로 빼서 CSV/API/DB 확장을 쉽게 하기 위해서다.
- 언제 수정하는가: 컬럼 구조, 샘플 데이터, KPI 계산이 바뀔 때
- 연결 파일: `app.py`, `pages/3_Data_Analysis.py`, `tests/test_analysis_data.py`
- 주의점: 반환 컬럼 구조를 바꾸면 페이지와 테스트가 동시에 영향을 받는다. API 연결 시에도 페이지에서 직접 요청하지 말고 이 계층을 먼저 확장한다.

## `dashboard/utils/`

### `dashboard/utils/__init__.py`

- 역할: `utils` 폴더를 패키지로 인식하게 한다.
- 왜 필요한가: 포맷팅 유틸 import를 안정적으로 유지한다.
- 언제 수정하는가: 거의 수정하지 않는다.
- 연결 파일: `app.py`, `pages/2_Projects.py`, `pages/3_Data_Analysis.py`
- 주의점: 작은 파일처럼 보여도 import 구조를 위해 필요하다.

### `dashboard/utils/formatters.py`

- 역할: 숫자, 퍼센트, 날짜, 상태 라벨 포맷을 공통 처리한다.
- 왜 필요한가: 표시 형식을 여러 파일에서 제각각 쓰지 않게 한다.
- 언제 수정하는가: 표기 방식, 상태 라벨, 자릿수를 바꿀 때
- 연결 파일: `app.py`, `pages/2_Projects.py`, `pages/3_Data_Analysis.py`
- 주의점: 내부 값과 표시용 라벨을 섞어 쓰면 필터나 테스트에서 혼란이 생길 수 있다.

## `pages/` 폴더

### `pages/1_About.py`

- 역할: 저장소 소개, 운영 기준, 기술 스택을 보여준다.
- 왜 필요한가: 저장소 설명을 코드 구조와 연결해 보여주는 첫 소개 페이지이기 때문이다.
- 언제 수정하는가: 소개 문장, 운영 기준, 기술 스택이 바뀔 때
- 연결 파일: `dashboard/content.py`, `dashboard/components/layout.py`
- 주의점: README와 전혀 다른 설명을 하지 않게 맞춘다.

### `pages/2_Projects.py`

- 역할: 현재 저장소 안에서 정리 중인 작업을 카드 형태로 보여준다.
- 왜 필요한가: 프로젝트 기록을 일관된 형식으로 남기기 위해서다.
- 언제 수정하는가: 프로젝트 카드 내용이나 표시 방식이 바뀔 때
- 연결 파일: `dashboard/content.py`, `dashboard/utils/formatters.py`
- 주의점: 카드가 예쁜 것보다 문제, 역할, 다음 액션이 분명해야 한다.

### `pages/3_Data_Analysis.py`

- 역할: 샘플 데이터 기반 필터, KPI, 차트, 상세 테이블을 보여준다.
- 왜 필요한가: 실제 데이터 확장을 위한 구조 예시를 보여주는 핵심 페이지이기 때문이다.
- 언제 수정하는가: 필터, KPI, 차트, 상세 테이블 구조가 바뀔 때
- 연결 파일: `dashboard/services/analysis_data.py`, `dashboard/components/charts.py`, `dashboard/utils/formatters.py`
- 주의점: 페이지 안에서 직접 API를 반복 호출하거나 집계 로직을 중복 작성하지 않는다.

### `pages/4_Learning_Log.py`

- 역할: 이 저장소를 통해 배우는 주제와 확장 로드맵을 보여준다.
- 왜 필요한가: 학습 내용을 실제 구조와 연결해 보여주기 위해서다.
- 언제 수정하는가: 학습 주제, 로드맵, 운영 규칙이 바뀔 때
- 연결 파일: `dashboard/content.py`
- 주의점: 과거 학습 회고로만 흐르지 않고 현재 코드 기준으로 유지한다.

## `tests/` 폴더

### `tests/conftest.py`

- 역할: 테스트 실행 시 루트 경로를 import 가능하게 잡아준다.
- 왜 필요한가: `dashboard` 패키지를 테스트에서 바로 import하기 위해서다.
- 언제 수정하는가: 프로젝트 루트 구조가 크게 바뀔 때
- 연결 파일: `tests/test_analysis_data.py`, `tests/test_content.py`
- 주의점: 경로 설정이 깨지면 테스트가 수집 단계에서 실패한다.

### `tests/test_analysis_data.py`

- 역할: 데이터 컬럼 구조, KPI 계산, 빈 데이터 처리를 검증한다.
- 왜 필요한가: `analysis_data.py`의 계약이 깨지지 않게 하기 위해서다.
- 언제 수정하는가: 컬럼 구조, KPI 키, 데이터 수가 바뀔 때
- 연결 파일: `dashboard/services/analysis_data.py`
- 주의점: 너무 세세한 난수 값 자체를 검증하기보다 구조와 범위를 검증한다.

### `tests/test_content.py`

- 역할: `content.py`의 필수 키와 최소 데이터 구조를 검증한다.
- 왜 필요한가: 페이지가 기대하는 콘텐츠 형태가 깨지지 않게 하기 위해서다.
- 언제 수정하는가: `PROFILE_DATA`, `PROJECT_ITEMS`, `LEARNING_TOPICS`, `ROADMAP_STEPS` 구조가 바뀔 때
- 연결 파일: `dashboard/content.py`
- 주의점: 문장 표현 하나하나에 테스트를 묶지 말고 구조에 초점을 둔다.

## `docs/` 폴더

| 파일 | 역할 | 언제 먼저 보는가 |
| --- | --- | --- |
| `01_PROJECT_DIRECTION.md` | 저장소 목적과 운영 기준 | 이 저장소가 무엇인지 다시 정리하고 싶을 때 |
| `02_STRUCTURE_GUIDE.md` | 파일과 폴더 전체 설명 | 어디를 수정해야 할지 모를 때 |
| `03_STREAMLIT_LEARNING_GUIDE.md` | 현재 저장소를 통해 배우는 개념 | 학습 관점에서 구조를 보고 싶을 때 |
| `04_UPDATE_AND_EXPANSION_GUIDE.md` | 수정과 확장 절차 허브 | 작업을 시작하기 전에 |
| `05_LIBRARY_GUIDE.md` | 라이브러리 사용 이유와 시점 | 패키지 추가/사용 판단이 필요할 때 |
| `06_PROJECT_EXPLANATION_GUIDE.md` | 이 저장소로 무엇을 했는지 설명하는 기준 | README, 자기소개서, 소개 문장을 쓸 때 |
| `07_WORKING_CHECKLIST.md` | 최종 점검 문서 | 수정 전, 커밋 전 |
| `08_CODEBASE_OVERVIEW.md` | 전체 코드 흐름 해설 | 코드 전체 구조를 먼저 이해할 때 |
| `09_ENTRYPOINT_AND_CONFIG_GUIDE.md` | 진입점과 설정 해설 | README, 설정, 앱 시작점을 볼 때 |
| `10_CONTENT_AND_DATA_GUIDE.md` | 콘텐츠, 데이터, 포맷팅 해설 | 텍스트나 데이터 계층을 수정할 때 |
| `11_COMPONENT_AND_PAGE_GUIDE.md` | 컴포넌트와 페이지 해설 | UI와 페이지 구성을 바꿀 때 |
| `12_TEST_AND_VERIFICATION_GUIDE.md` | 테스트와 검증 해설 | 테스트를 수정하거나 추가할 때 |
| `13_EXPORT_GUIDE.md` | Word/PPT/PDF 변환 기준 | 외부 문서 형식으로 옮길 때 |
| `14_CODING_AND_CLASS_GUIDELINES.md` | 코드와 클래스 설계 원칙 | 새 함수나 클래스를 설계할 때 |
| `15_DATA_SOURCE_EXPANSION_GUIDE.md` | CSV, API, DB 확장 | 데이터 소스를 실제로 바꿀 때 |
| `16_PAGE_AND_FEATURE_EXPANSION_GUIDE.md` | 페이지와 기능 확장 | 새 페이지, 필터, 차트, 카드 추가 시 |

## 파일 이름을 영어로 두는 이유

- 운영체제와 Git에서 인코딩 문제를 줄이기 위해
- 검색과 자동화 도구에서 안정적으로 다루기 위해
- 공개 저장소에서 구조를 빠르게 읽기 쉽게 하기 위해

## 새 파일이나 폴더를 추가하는 기준

- 같은 성격의 코드가 세 번 이상 반복될 때
- 페이지 파일 하나가 화면과 데이터 로직을 동시에 너무 많이 떠안을 때
- 문서가 한 파일 안에서 여러 목적을 동시에 수행해 읽기 어려워질 때

반대로, 파일이 거의 하나뿐인데 폴더만 늘어나는 구조는 피한다.