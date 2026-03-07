# 콘텐츠와 데이터 가이드

## 설명 대상 파일

- `dashboard/content.py`
- `dashboard/services/analysis_data.py`
- `dashboard/utils/formatters.py`

## `dashboard/content.py`

### 왜 있는가

자기소개, 프로젝트 카드, 학습 주제, 로드맵처럼 자주 바뀌는 문구를 한 곳에서 관리하기 위해 있다.

### 언제 쓰는가

- About 소개 문구 수정
- Projects 카드 내용 수정
- Learning Log 주제와 로드맵 수정

### 현재 코드 예시

```python
PROFILE_DATA = {
    "headline": "Python과 Streamlit으로 프로젝트 결과와 분석 과정을 정리하는 개발자",
}
```

### 수정 예시

- 실제 경험이 쌓이면 `PROJECT_ITEMS`의 더미 제목을 실제 프로젝트 이름으로 교체한다.
- 학습 단계가 늘어나면 `LEARNING_TOPICS`에 새 항목을 추가한다.

### 주의점

- 공통 문구를 페이지 파일에 복사해 두면 나중에 수정 누락이 생긴다.
- 키 이름을 바꾸면 그 값을 읽는 페이지와 테스트를 같이 수정해야 한다.

## `dashboard/services/analysis_data.py`

### 왜 있는가

데이터 생성, 정규화, KPI 계산을 페이지 밖에서 처리하기 위해 있다.

### 현재 코드 예시

```python
def load_demo_dataset(seed: int = 42) -> pd.DataFrame:
    ...

def build_kpis(dataframe: pd.DataFrame) -> dict[str, object]:
    ...
```

### 언제 쓰는가

- 샘플 데이터 구조를 바꿀 때
- CSV/API/DB 데이터로 바꿀 때
- KPI 항목을 추가할 때

### 수정 예시

- `conversion_rate` 외에 `retention_rate`를 추가하고 싶다면 여기서 컬럼을 만들고 KPI 계산도 추가한다.
- CSV 파일을 읽도록 바꿀 때도 페이지가 아니라 여기부터 바꾼다.

### 주의점

- 페이지에서 직접 외부 데이터를 가져오지 않고 이 계층을 통해 들어오게 해야 한다.
- API를 붙일 때 목록을 받고 루프 안에서 상세 API를 계속 부르면 느리고 비용이 커진다.
- 캐시를 고려하지 않으면 Streamlit rerun마다 무거운 로딩이 반복된다.
- 반환 컬럼 구조를 자주 바꾸면 차트 함수와 테스트가 연쇄적으로 깨진다.

## `dashboard/utils/formatters.py`

### 왜 있는가

숫자, 퍼센트, 날짜, 상태 라벨을 한 곳에서 관리하기 위해 있다.

### 현재 코드 예시

```python
def format_percent(value: float, digits: int = 1) -> str:
    return f"{value * 100:.{digits}f}%"
```

### 언제 쓰는가

- 퍼센트 자릿수를 바꾸고 싶을 때
- 상태 라벨 표시 문구를 바꿀 때
- 날짜 형식을 통일하고 싶을 때

### 수정 예시

- 상태 값 `Needs Review`를 `검토 필요` 대신 다른 표현으로 바꾸고 싶다면 `STATUS_LABELS`에서 수정한다.

### 주의점

- 내부 상태 값과 화면 표시용 라벨을 섞어 쓰면 필터가 꼬일 수 있다.
- 각 페이지에서 각자 포맷 함수를 만들기 시작하면 관리 지점이 늘어난다.

## 잘못 수정하면 생길 문제

- `content.py` 구조를 바꾸고 테스트를 안 바꾸면 페이지 진입 전에 오류가 날 수 있다.
- `analysis_data.py` 컬럼명이 바뀌면 차트 함수가 기대하는 입력과 어긋난다.
- 포맷 함수가 제각각이면 사용자는 같은 의미의 값을 다른 형식으로 보게 된다.