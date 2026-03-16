# 프로젝트 대시보드

재난 대피 의사결정을 돕기 위한 Streamlit 기반 대시보드입니다. 정적 전처리 데이터, 실시간 재난문자 크롤링 결과, 모의 재난문자 생성 흐름을 함께 두고 실험과 설명이 가능하도록 구성했습니다.

## 주요 기능

- 홈 화면에서 전처리 데이터 기준 요약 지표와 기본 현황을 확인합니다.
- `대피 안내 시뮬레이션` 페이지에서 지역과 재난 유형에 맞는 대피소 후보와 경로를 탐색합니다.
- `실시간 대피 안내` 페이지에서 재난문자 CSV 또는 모의 재난문자를 기반으로 최근 경보와 대피 추천을 확인합니다.
- `데이터 분석` 페이지에서 전처리 결과와 지도 HTML, 참조 DB를 활용해 분포와 비교 지표를 살펴봅니다.

## 실행 방법

### 1. Python 의존성 설치

이 저장소는 `pyproject.toml`과 `uv.lock` 기준으로 관리합니다.

```powershell
uv sync
```

되도록 uv 사용을 권장 드립니다.
`uv`를 사용하지 않는다면 가상환경을 만든 뒤 `pip install -e .`로 설치해도 됩니다.

### 2. Streamlit 실행

```powershell
streamlit run app.py
```

### 3. 데이터 경로 확인

기본 실행은 저장소 내부 `preprocessing_data` 폴더를 사용합니다. 다른 위치의 전처리 데이터를 쓰고 싶다면 `.streamlit/secrets.toml.example`을 참고해 `.streamlit/secrets.toml`을 만들고 `preprocessing_data_dir`를 지정하면 됩니다.

예시:

```toml
preprocessing_data_dir = "D:/my-preprocessing-data"
```

## 실시간 크롤링 참고

실시간 재난문자 수집은 `preprocessing_code/crawling.py`에서 Selenium과 Chromium을 사용합니다.

- Python 패키지는 `pyproject.toml`에 포함되어 있습니다.
- 시스템 패키지는 `packages.txt`에 정리되어 있으며, Linux 계열 배포 환경에서는 `chromium`, `chromium-driver`가 필요합니다.
- 크롤링 없이 화면 흐름만 확인하고 싶다면 `preprocessing_code/mock_disaster_message.py`로 모의 재난문자 CSV를 생성할 수 있습니다.

## 디렉터리 안내

- `app.py`: Streamlit 진입점
- `pages/`: 시뮬레이션, 실시간 안내, 데이터 분석 페이지
- `preprocessing_data/`: 앱이 직접 읽는 정제 CSV
- `preprocessing_code/`: 전처리 스크립트, 원본 데이터, 노트북, 참고 산출물
- `docs/`: 공개용 구조 문서와 데이터/전처리 참고 문서
- `.streamlit/`: 테마 설정과 비밀값 예시 파일

## 참조

`preprocessing_code/`와 `preprocessing_data/`는 원본 데이터를 어떤 방식으로 가공해 현재 앱의 입력 데이터로 만들었는지 보여주는 참고 자료입니다. GitHub에서 코드를 보는 사람도 전처리 흐름과 산출물의 관계를 함께 이해할 수 있도록 의도적으로 유지했습니다.

현재 앱 실행에 직접 쓰이는 것은 주로 아래 자원입니다.

- `preprocessing_data/preprocessing/*.csv`
- `preprocessing_code/data/disaster_message_realtime.csv`
- `preprocessing_code/shelter_type_layer_map1.html`
- `preprocessing_code/data/Emergency_shelter.db`

그 외 `preprocessing_code/raw/`, `preprocessing_code/jupyter/`, `preprocessing_code/py/`는 전처리 이력과 참고용 자료 모음입니다.

## 문서

- `docs/01_프로젝트_구조.md`
- `docs/02_데이터_흐름.md`
- `docs/03_전처리_및_참고자료.md`
