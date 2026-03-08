# 진입점과 설정 가이드

## `app.py`

- 홈 화면 진입점
- 현재 데이터 범위와 페이지 순서를 안내
- 외부 전처리 데이터 폴더가 실제로 읽히는지 가장 먼저 확인하는 화면

## `dashboard/config.py`

- 앱 제목, 아이콘, 페이지 메타데이터 관리
- 페이지별 라벨과 요약을 한곳에서 유지
- 새 페이지를 추가하면 가장 먼저 이 파일을 확인

## `.streamlit/config.toml`

- 앱 테마와 브라우저 설정 담당
- 현재는 밝은 테마와 기본 색상만 관리

## `.streamlit/secrets.toml.example`

- `preprocessing_data_dir` 예시 제공
- 미래 API 키 자리표시자만 포함
- 실제 키는 Git 에 올리지 않음
