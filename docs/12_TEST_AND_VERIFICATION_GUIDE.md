# 테스트와 검증 가이드

## 설명 대상 파일

- `tests/conftest.py`
- `tests/test_analysis_data.py`
- `tests/test_content.py`

## 왜 테스트가 필요한가

이 저장소는 단순한 실험 코드가 아니라, 구조와 설명을 함께 보여주는 공개용 저장소다. 따라서 작은 구조 변경도 최소한 검증해야 한다.

## `tests/conftest.py`

### 왜 있는가

테스트 실행 시 프로젝트 루트를 import 경로에 넣어 `dashboard` 패키지를 바로 가져오게 하기 위해 있다.

### 주의점

- 루트 구조가 바뀌면 가장 먼저 여기부터 확인해야 한다.

## `tests/test_analysis_data.py`

### 왜 있는가

`analysis_data.py`가 기대하는 데이터 계약을 지키는지 확인한다.

### 현재 검증하는 것

- 컬럼 이름과 순서
- 샘플 데이터 개수
- KPI 계산 결과 타입과 범위
- 빈 데이터 처리

### 현재 코드 예시

```python
assert list(dataframe.columns) == REQUIRED_COLUMNS
```

### 수정 예시

- 새 컬럼을 추가했다면 `REQUIRED_COLUMNS`와 관련 assertion을 같이 수정한다.
- KPI 키를 추가했다면 반환 딕셔너리 검증도 늘린다.

### 주의점

- 난수 값 자체를 고정적으로 강하게 검증하면 테스트가 취약해질 수 있다.
- 구조와 계약을 검증하는 데 집중한다.

## `tests/test_content.py`

### 왜 있는가

페이지가 읽는 콘텐츠 구조가 최소한 유지되는지 확인한다.

### 현재 검증하는 것

- `PROFILE_DATA` 필수 키
- `PROJECT_ITEMS` 최소 필드
- `LEARNING_TOPICS`, `ROADMAP_STEPS` 존재 여부

### 수정 예시

- `PROFILE_DATA`에 필수 키를 추가했다면 테스트도 같이 업데이트한다.

### 주의점

- 문장 하나하나의 표현을 테스트하지 말고 구조를 검증한다.

## 검증 순서

1. 문구나 구조 변경
2. 관련 테스트 수정
3. `uv run --dev pytest`
4. `streamlit run app.py` 스모크 테스트
5. README와 docs 설명 확인

## 자주 하는 실수

- 테스트를 통과시켰다고 문서 확인을 생략함
- 문서만 고치고 실행 확인을 하지 않음
- 컬럼 구조를 바꾸고 테스트를 안 고침
- 콘텐츠 키를 바꾸고 페이지 연결을 안 봄

## 잘못 수정하면 생길 문제

- 테스트 수집 단계에서 import 에러가 날 수 있다.
- 구조가 어긋난 채로 화면은 일부만 보이고 문서는 맞는 척할 수 있다.
- 공개 저장소에서 재현성과 신뢰도가 떨어진다.