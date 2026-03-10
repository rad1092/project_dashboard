# 페이지 흐름

## 홈

- `app.py`는 앱 소개, 데이터셋 요약, 페이지 순서 안내를 담당한다.
- 홈 KPI 는 홈 파일 내부의 `load_analysis_dataset()` 과 `build_kpis()` 로 계산한다.

## 추천 페이지

- `pages/2_대피소_추천.py`가 핵심 허브다.
- 흐름은 `좌표 입력 -> 지역 감지 -> 활성 지역 확정 -> 최근 특보 요약 -> 재난 선택 -> 추천 계산 -> 카드/지도/표 출력` 순서다.
- 추천 규칙은 같은 파일 안의 `recommend_shelters()` 와 보조 helper 들이 담당한다.

## 분석 페이지

- `pages/6_Data_Analysis.py`는 특보 이력을 분석용 DataFrame 으로 다시 만들고 KPI 와 차트를 생성한다.
- 추천 페이지와 같은 CSV 원본을 읽되, 분석 목적에 맞게 `재난그룹` 열을 추가한다.

## 정적 페이지

- `pages/1_About.py`: 프로젝트 소개와 데이터 연결 상태
- `pages/3_작동_설명.py`: 추천 흐름 설명
- `pages/4_실시간_준비.py`: 미래 확장 포인트
- `pages/5_Projects.py`: 현재 작업 기록
- `pages/7_Learning_Log.py`: 학습 포인트와 로드맵
