# 컴포넌트와 페이지 가이드

## 설명 대상 파일

- `dashboard/components/layout.py`
- `dashboard/components/charts.py`
- `pages/1_About.py`
- `pages/2_Projects.py`
- `pages/3_Data_Analysis.py`
- `pages/4_Learning_Log.py`

## `dashboard/components/layout.py`

### 왜 있는가

반복되는 페이지 헤더, 칩 목록, 박스형 목록 UI를 한 곳에 모아 재사용하기 위해 있다.

### 현재 코드 예시

```python
def render_page_intro(title: str, subtitle: str, caption: str | None = None) -> None:
    st.title(title)
    st.write(subtitle)
    if caption:
        st.caption(caption)
```

### 수정 예시

- 모든 페이지의 소개 헤더 형식을 바꾸고 싶으면 이 함수부터 수정한다.

### 주의점

- 표현 함수 안에 데이터 조회나 API 요청을 넣지 않는다.

## `dashboard/components/charts.py`

### 왜 있는가

차트 로직을 페이지 파일 밖으로 빼서 재사용하기 위해 있다.

### 현재 코드 예시

```python
def build_trend_chart(dataframe: pd.DataFrame) -> go.Figure:
    ...
```

### 수정 예시

- 새 차트를 추가할 때는 이 파일에 함수로 만들고, 페이지에서는 호출만 하게 한다.

### 주의점

- 페이지에서 직접 groupby와 차트 생성을 반복하지 않는다.
- 특정 페이지 전용 처리로 차트 함수를 너무 복잡하게 만들지 않는다.

## `pages/1_About.py`

### 왜 있는가

이 저장소를 어떤 기준으로 운영하는지 보여주는 소개 페이지다.

### 언제 수정하는가

- 소개 문구
- 기술 스택
- 운영 원칙

### 주의점

- README와 다른 정체성을 말하지 않게 한다.

## `pages/2_Projects.py`

### 왜 있는가

현재 정리 중인 작업을 카드 형태로 기록하는 페이지다.

### 언제 수정하는가

- 프로젝트 카드 내용
- 카드 표시 형식

### 주의점

- 카드가 예쁜 것보다 문제, 역할, 결과, 다음 액션이 분명해야 한다.

## `pages/3_Data_Analysis.py`

### 왜 있는가

현재 구조에서 가장 중요한 분석 화면 예시를 보여준다.

### 현재 코드 예시

```python
filtered = dataframe[
    dataframe["project"].isin(selected_projects)
    & dataframe["category"].isin(selected_categories)
    & dataframe["status"].isin(selected_statuses)
].copy()
```

### 수정 예시

- 새 필터를 추가하고 싶다면 먼저 어떤 컬럼이 필요한지 `analysis_data.py`에서 확인한다.
- 새 차트를 추가하고 싶다면 `charts.py`에 함수를 만들고 여기서는 호출만 한다.

### 주의점

- 페이지에서 직접 API를 반복 호출하지 않는다.
- 필터와 KPI, 차트 계산을 한 파일에 계속 쌓으면 금방 복잡해진다.
- rerun마다 무거운 계산을 여러 번 하지 않도록 구조를 본다.

## `pages/4_Learning_Log.py`

### 왜 있는가

이 저장소를 통해 배우는 것과 확장 순서를 정리하는 페이지다.

### 언제 수정하는가

- 학습 주제
- 로드맵
- 운영 규칙

### 주의점

- 과거 회고만 적지 말고 현재 구조 기준으로 유지한다.

## 잘못 수정하면 생길 문제

- 공통 UI를 페이지마다 복붙하면 유지보수가 힘들어진다.
- 분석 페이지에서 직접 서비스 역할까지 떠안으면 확장 문서와 코드가 같이 무너진다.
- 상태관리를 필요 이상으로 넣으면 Streamlit 흐름을 이해하기 어려워진다.