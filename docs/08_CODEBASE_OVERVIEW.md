# 코드베이스 개요

## 이 문서의 목적

이 문서는 현재 코드 전체가 어떤 흐름으로 연결되는지 먼저 보여주는 문서다. 세부 함수 설명보다 먼저, "데이터가 어디서 시작해서 어디로 표시되는가"와 "문구가 어디서 관리되는가"를 이해하는 데 초점을 둔다.

## 전체 흐름

1. `app.py`가 홈 화면을 띄운다.
2. `dashboard/config.py`가 공통 페이지 설정을 제공한다.
3. `dashboard/content.py`가 설명 문구 원본을 제공한다.
4. `dashboard/services/analysis_data.py`가 샘플 데이터와 KPI를 준비한다.
5. `dashboard/components/*`가 공통 UI와 차트를 만든다.
6. `pages/*`가 각 화면을 조합해 보여준다.
7. `tests/*`가 데이터 구조와 콘텐츠 구조가 유지되는지 확인한다.

## 데이터 흐름 예시

### 홈 화면

- `app.py`에서 `load_demo_dataset()` 호출
- `build_kpis()`로 요약 수치 계산
- `format_number()`, `format_percent()`, `format_period()`로 표시용 형식 맞춤
- Streamlit metric과 markdown으로 출력

### 분석 화면

- `pages/3_Data_Analysis.py`에서 샘플 데이터 로드
- 사이드바 필터로 DataFrame 필터링
- `build_kpis()`로 KPI 계산
- `build_trend_chart()`, `build_category_impact_chart()`, `build_status_share_chart()` 호출
- 포맷 함수로 테이블 표시 형식 통일

## 텍스트 흐름 예시

- `PROFILE_DATA`, `PROJECT_ITEMS`, `LEARNING_TOPICS`, `ROADMAP_STEPS`는 모두 `dashboard/content.py`에서 시작한다.
- About, Projects, Learning Log 페이지는 이 값을 읽어 화면에 표시한다.
- 따라서 소개 문구를 바꿀 때는 페이지보다 `content.py`를 먼저 봐야 한다.

## 왜 이렇게 나누었는가

- 페이지는 화면 조합만 담당한다.
- 데이터 준비는 `services`가 담당한다.
- 표시 형식은 `utils`가 담당한다.
- 반복 UI와 차트는 `components`가 담당한다.
- 설명 문구는 `content.py`가 담당한다.

이 분리 덕분에 화면을 바꾸고 싶을 때와 데이터 원천을 바꾸고 싶을 때 영향을 받는 파일을 구분할 수 있다.

## 현재 코드 예시

```python
# app.py
from dashboard.services.analysis_data import build_kpis, load_demo_dataset


dataframe = load_demo_dataset()
kpis = build_kpis(dataframe)
```

이 구조는 홈 화면이 데이터가 어디서 오는지 몰라도 되게 만든다. 홈 화면은 "불러온 데이터로 무엇을 보여줄지"만 신경 쓰면 된다.

## 수정 예시

### 예시 1. 홈 화면 문장을 바꾸고 싶을 때

- 먼저 `README.md`와 `app.py`를 본다.
- 공통 소개 문구까지 바뀌면 `docs/01`도 같이 수정한다.

### 예시 2. 분석 화면에 새 KPI를 추가하고 싶을 때

- 먼저 `dashboard/services/analysis_data.py`에서 KPI 계산 가능 여부를 본다.
- 그 다음 `pages/3_Data_Analysis.py`에 표시를 추가한다.
- 필요하면 `tests/test_analysis_data.py`를 같이 수정한다.

## 주의점

- 홈 화면이나 페이지 파일 안에 데이터 생성, API 호출, 가공, 포맷팅을 모두 몰아넣지 않는다.
- 설명 문구를 페이지마다 따로 고치면 나중에 저장소 설명이 흩어진다.
- 새 기능을 추가할 때는 먼저 기존 `services`, `components`, `utils`로 해결 가능한지 확인한다.

## 잘못 수정하면 생길 문제

- `content.py` 대신 페이지마다 문구를 하드코딩하면 문장 불일치가 생긴다.
- `analysis_data.py` 반환 형태를 바꿔놓고 페이지를 안 고치면 차트와 테스트가 함께 깨진다.
- 페이지 파일이 비대해지면 확장 문서와 실제 코드가 어긋나기 시작한다.