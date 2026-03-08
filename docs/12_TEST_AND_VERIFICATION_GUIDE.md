# 테스트와 검증 가이드

## 자동 테스트

```powershell
.venv\Scripts\python.exe -m pytest
```

## 현재 테스트 파일

- `tests/test_analysis_data.py`: 분석용 특보 DataFrame 과 KPI 검증
- `tests/test_content.py`: 콘텐츠 구조와 페이지 문법 검증
- `tests/test_disaster_data.py`: 경로 탐색, CSV 로딩, 최근 특보 요약 검증
- `tests/test_shelter_recommendation.py`: 재난 정규화, 거리 계산, 추천 규칙 검증

## 수동 검증

1. `Home` 에서 데이터 로딩과 페이지 안내가 보이는지 확인
2. `2 대피소 추천` 에서 좌표 입력, 추천 카드, 지도, 표가 함께 보이는지 확인
3. `3 작동 설명` 이 이미지 없이도 플로우를 설명하는지 확인
4. `4 실시간 준비` 가 실제 호출 없이 준비 페이지로 읽히는지 확인
5. `6 Data Analysis` 차트와 표가 필터에 맞게 바뀌는지 확인

## 특히 확인할 것

- 외부 CSV 를 수정하지 않았는가
- 유료 API 호출 코드가 들어가지 않았는가
- 새 Python 파일과 함수에 설명 주석이 충분한가
