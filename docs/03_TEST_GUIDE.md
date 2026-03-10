# 테스트 가이드

## 기본 실행

```powershell
.\.venv\Scripts\python -m pytest -q
```

## 테스트 구조

- `tests/conftest.py`: 샘플 전처리 데이터 fixture, 파일 경로 기반 모듈 로더
- `tests/test_recommendation_page.py`: 추천 페이지 내부 helper, 데이터 경로 해석, 추천 규칙
- `tests/test_analysis_page.py`: 분석용 DataFrame, KPI, 차트 생성
- `tests/test_home_page.py`: 홈 메타데이터, KPI, 데이터셋 카탈로그
- `tests/test_static_pages.py`: 정적 페이지 요약 콘텐츠, docs 연계, 문법

## import-only 모드

테스트는 `PROJECT_DASHBOARD_IMPORT_ONLY=1`을 사용한다.

이 모드에서는 `app.py`와 `pages/*.py`가 import 시 자동 렌더링되지 않고,
테스트가 파일 내부 helper 함수를 직접 검증할 수 있다.

## 검증 기준

- 페이지 파일 import 시 Streamlit 렌더링이 바로 실행되지 않아야 한다.
- 데이터 경로 우선순위와 오류 메시지가 유지돼야 한다.
- 추천 결과 컬럼 순서가 유지돼야 한다.
- 분석 KPI 와 차트가 샘플 데이터에서 정상 생성돼야 한다.
- 설명 페이지는 과한 구현 설명 대신 요약 상수와 docs 경로를 유지해야 한다.
