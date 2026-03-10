# 재난 대피소 추천 워크스페이스

전처리된 재난 특보 이력과 대피소 좌표 데이터를 이용해
대피소 추천 흐름과 분석 화면을 함께 보여주는 Streamlit 프로젝트다.


- 홈 엔트리포인트는 `app.py` 하나다.
- 실페이지는 `pages/` 아래 각 파일이 직접 소유한다.
- 공용 계층은 없고, 각 페이지가 자기 화면에 필요한 상수, 데이터 로더, 계산 로직, 렌더 헬퍼를 직접 가진다.

## 실행

```powershell
streamlit run app.py
```

## 테스트

```powershell
.\.venv\Scripts\python -m pytest -q
```

테스트는 `PROJECT_DASHBOARD_IMPORT_ONLY=1` 환경변수로 페이지 자동 렌더링을 막고,
각 파일 내부 helper 를 직접 검증한다.

## 현재 파일 구조

```text
c:\project_dashboard
|- app.py
|- pages/
|  |- 1_About.py
|  |- 2_대피소_추천.py
|  |- 3_작동_설명.py
|  |- 4_실시간_준비.py
|  |- 5_Projects.py
|  |- 6_Data_Analysis.py
|  `- 7_Learning_Log.py
|- preprocessing_data/
|- tests/
`- docs/
```

## 페이지 기준 책임

- `app.py`: 홈 소개, 현재 연결 데이터 요약, 공통 페이지 안내
- `pages/2_대피소_추천.py`: 좌표 기반 지역 감지, 특보 요약, 추천 계산, 지도/카드/표 출력
- `pages/6_Data_Analysis.py`: 분석용 DataFrame, KPI, Plotly 차트
- 나머지 페이지: 소개, 작동 설명, 실시간 준비, 프로젝트 기록, 학습 로그

## 데이터 경로

전처리 데이터 경로 우선순위는 아래와 같다.

1. 함수 인자 override
2. `PREPROCESSING_DATA_DIR`
3. `.streamlit/secrets.toml` 의 `preprocessing_data_dir`
4. 저장소 내부 `preprocessing_data`
5. `~/Desktop/preprocessing_data`

앱은 CSV 를 읽기 전용으로만 사용한다.
