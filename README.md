# project_dashboard

Streamlit을 이용해 프로젝트 결과, 데이터 분석 과정, 학습 내용을 정리하고 설명하는 저장소입니다.

이 저장소의 목적은 화면 하나만 완성하는 것이 아니라, 내가 어떤 문제를 다뤘고 어떤 구조로 구현했고 어떻게 확장해 나가는지를 한 저장소 안에서 일관되게 보여주는 것입니다.

## 이 저장소에서 볼 수 있는 것

- `Home`: 저장소 목적, 현재 상태, 문서 읽는 순서
- `About`: 이 저장소를 어떤 기준으로 운영하는지
- `Projects`: 프로젝트 기록과 다음 확장 방향
- `Data Analysis`: 샘플 데이터 기반 분석 화면과 구조 예시
- `Learning Log`: 학습 주제, 로드맵, 운영 원칙

## 실행 방법

```powershell
.venv\Scripts\activate
uv sync --dev
streamlit run app.py
```

## 문서

- `docs/01_PROJECT_DIRECTION.md`: 이 저장소가 왜 존재하는지와 운영 기준
- `docs/02_STRUCTURE_GUIDE.md`: 실제 파일과 폴더를 어떻게 이해하고 수정해야 하는지
- `docs/03_STREAMLIT_LEARNING_GUIDE.md`: 이 저장소를 통해 배우는 Streamlit 개념과 실습 포인트
- `docs/04_UPDATE_AND_EXPANSION_GUIDE.md`: 수정 절차와 확장 절차를 한 번에 보는 허브 문서
- `docs/05_LIBRARY_GUIDE.md`: 현재 의존성과 사용 시점, 주의점
- `docs/06_PROJECT_EXPLANATION_GUIDE.md`: 이 저장소로 내가 무엇을 했는지 설명하는 가이드
- `docs/07_WORKING_CHECKLIST.md`: 수정 전과 커밋 전 빠르게 보는 점검 문서
- `docs/08_CODEBASE_OVERVIEW.md`: 전체 코드 흐름과 데이터 흐름 해설
- `docs/09_ENTRYPOINT_AND_CONFIG_GUIDE.md`: 진입점과 설정 파일 해설
- `docs/10_CONTENT_AND_DATA_GUIDE.md`: 콘텐츠, 데이터, 포맷팅 코드 해설
- `docs/11_COMPONENT_AND_PAGE_GUIDE.md`: 컴포넌트와 페이지 코드 해설
- `docs/12_TEST_AND_VERIFICATION_GUIDE.md`: 테스트와 검증 흐름 해설
- `docs/13_EXPORT_GUIDE.md`: Word/PPT/PDF로 옮길 때의 기준
- `docs/14_CODING_AND_CLASS_GUIDELINES.md`: 코드 작성과 클래스 설계 주의사항
- `docs/15_DATA_SOURCE_EXPANSION_GUIDE.md`: CSV, API, DB 확장 가이드
- `docs/16_PAGE_AND_FEATURE_EXPANSION_GUIDE.md`: 페이지와 기능 확장 가이드