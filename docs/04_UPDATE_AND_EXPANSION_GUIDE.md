# 업데이트와 확장 가이드

## 이 문서의 역할

이 문서는 단순한 수정 절차만 다루지 않는다. 지금 있는 내용을 어떻게 고치고, 앞으로 어떻게 키워 나갈지를 함께 보는 허브 문서다. 즉, "지금 뭘 고쳐야 하는가"와 "이후 어디로 확장해야 하는가"를 한 번에 연결해준다.

## 먼저 작업 유형을 구분한다

- 문구 수정: README, About, Projects 같은 설명 텍스트 수정
- 구조 수정: 새 파일, 새 함수, 새 페이지 추가
- 데이터 수정: 샘플 데이터 컬럼 변경, KPI 변경
- 데이터 확장: CSV, API, DB 연결
- 기능 확장: 차트, 필터, 탭, 카드, 상태관리 추가

작업 유형을 먼저 구분하면 어디를 건드려야 할지 빨라진다.

## 1. 텍스트와 소개 문구를 수정할 때

### 순서

1. `dashboard/content.py`에서 공통 문구 수정
2. 페이지 파일에서 개별 문구 수정
3. `README.md`와 관련 docs 수정
4. 앱 화면에서 문구 흐름 확인

### 영향 파일

- `dashboard/content.py`
- `pages/1_About.py`
- `pages/2_Projects.py`
- `README.md`
- 관련 docs

### 주의점

- 페이지만 바꾸고 README를 안 바꾸면 저장소 설명이 어긋난다.
- 같은 뜻의 문장을 여러 파일에 중복으로 적지 않는다.

### 다음에 볼 문서

- `docs/06_PROJECT_EXPLANATION_GUIDE.md`
- `docs/07_WORKING_CHECKLIST.md`

## 2. 새 페이지를 추가할 때

### 순서

1. `pages/` 아래에 번호가 붙은 새 파일 생성
2. `apply_page_config()` 호출
3. 페이지용 콘텐츠가 공통이라면 `dashboard/content.py`에 추가
4. 반복 UI가 있으면 `dashboard/components/`로 분리
5. README와 docs 갱신

### 영향 파일

- `pages/*`
- `dashboard/config.py`
- `dashboard/content.py`
- `README.md`
- `docs/02`, `docs/16`

### 주의점

- 새 페이지를 만들었다고 바로 데이터 로직까지 모두 그 파일에 넣지 않는다.
- 화면 조합과 데이터 준비를 분리하지 않으면 확장 때마다 페이지가 비대해진다.

### 다음에 볼 문서

- `docs/11_COMPONENT_AND_PAGE_GUIDE.md`
- `docs/16_PAGE_AND_FEATURE_EXPANSION_GUIDE.md`

## 3. 샘플 데이터와 KPI를 수정할 때

### 순서

1. `dashboard/services/analysis_data.py`에서 컬럼 또는 계산 수정
2. `pages/3_Data_Analysis.py`에서 표시 항목 점검
3. `tests/test_analysis_data.py` 갱신
4. 관련 문서 갱신

### 영향 파일

- `dashboard/services/analysis_data.py`
- `pages/3_Data_Analysis.py`
- `tests/test_analysis_data.py`
- `docs/10`, `docs/15`

### 주의점

- 컬럼 이름을 바꾸면 차트, 테이블, 테스트가 같이 깨질 수 있다.
- 서비스 함수 반환 형태를 자주 바꾸면 페이지 재사용성이 낮아진다.

### 다음에 볼 문서

- `docs/10_CONTENT_AND_DATA_GUIDE.md`
- `docs/15_DATA_SOURCE_EXPANSION_GUIDE.md`

## 4. 차트나 필터를 추가할 때

### 순서

1. 어떤 질문에 답하는 차트인지 먼저 정한다.
2. 필요한 집계 로직을 정의한다.
3. 차트 함수는 `dashboard/components/charts.py`에 추가한다.
4. 페이지에서 호출만 하게 연결한다.
5. 필터 변경이 기존 KPI와 충돌하지 않는지 확인한다.

### 영향 파일

- `dashboard/components/charts.py`
- `pages/3_Data_Analysis.py`
- 필요 시 `dashboard/utils/formatters.py`

### 주의점

- 페이지 안에 차트 집계 로직을 중복 작성하지 않는다.
- 필터가 많아질수록 Streamlit rerun 비용이 커지므로 불필요한 중복 계산을 줄여야 한다.

### 다음에 볼 문서

- `docs/11_COMPONENT_AND_PAGE_GUIDE.md`
- `docs/16_PAGE_AND_FEATURE_EXPANSION_GUIDE.md`

## 5. CSV 데이터를 연결할 때

### 순서

1. CSV 파일 위치와 컬럼 정의를 먼저 확정
2. `analysis_data.py`에 로딩 함수 추가
3. 반환 컬럼 이름을 기존 구조와 맞춤
4. `build_kpis()`가 그대로 동작하는지 확인
5. 테스트와 문서 업데이트

### 주의점

- CSV 컬럼명을 바로 페이지에서 기대하지 말고 서비스 계층에서 정규화한다.
- 로컬 절대경로를 쓰지 않는다.

### 다음에 볼 문서

- `docs/15_DATA_SOURCE_EXPANSION_GUIDE.md`

## 6. API 데이터를 연결할 때

### 순서

1. 인증 방식, 호출 제한, 응답 구조를 먼저 문서화한다.
2. API 요청 함수는 페이지가 아니라 `services`에 만든다.
3. 응답을 DataFrame으로 정규화한다.
4. `build_kpis()`와 차트 함수가 그 데이터를 그대로 받을 수 있는지 확인한다.
5. 실패 처리, 빈 응답 처리, 캐시를 추가한다.
6. secrets와 문서를 갱신한다.

### 영향 파일

- `dashboard/services/analysis_data.py` 또는 별도 service 파일
- `.streamlit/secrets.toml.example`
- `pages/3_Data_Analysis.py`
- `tests/*`
- `docs/15`, `docs/14`

### 반드시 주의할 점

- `rate limit`: 호출 횟수 제한을 먼저 확인한다.
- `pagination`: 여러 페이지 응답을 어떻게 합칠지 먼저 설계한다.
- `timeout`: 외부 서비스 지연이 앱 전체를 멈추지 않게 한다.
- `retry`: 실패 시 무조건 재시도하지 말고 횟수와 간격을 정한다.
- `cache`: 같은 요청을 매번 다시 보내지 않게 한다.
- `N+1 요청`: 목록을 받은 뒤 루프 안에서 상세 API를 계속 호출하면 느리고 비용이 커진다.
- `secrets 분리`: API 키와 토큰은 코드에 직접 넣지 않는다.

### 다음에 볼 문서

- `docs/14_CODING_AND_CLASS_GUIDELINES.md`
- `docs/15_DATA_SOURCE_EXPANSION_GUIDE.md`

## 7. DB로 확장할 때

### 순서

1. 어떤 데이터를 저장할지 먼저 정의
2. 읽기 전용인지 쓰기까지 필요한지 구분
3. 서비스 계층에 세션 또는 연결 로직 추가
4. UI는 가능한 한 기존 함수 인터페이스를 유지
5. 테스트와 secrets 처리 추가

### 주의점

- DB 연결을 페이지 파일에서 직접 열고 닫지 않는다.
- 커넥션 관리와 에러 처리를 한 곳에서 통제한다.

### 다음에 볼 문서

- `docs/15_DATA_SOURCE_EXPANSION_GUIDE.md`

## 8. 테스트와 문서를 함께 갱신할 때

### 순서

1. 구조 변경 시 테스트 영향 확인
2. 문구 변경 시 README와 docs 영향 확인
3. `uv run --dev pytest` 실행
4. `streamlit run app.py` 스모크 체크

### 주의점

- 문서만 맞고 코드가 틀리면 공개 저장소 품질이 떨어진다.
- 코드만 맞고 문서가 틀리면 설명 자료로서 가치가 떨어진다.

### 다음에 볼 문서

- `docs/07_WORKING_CHECKLIST.md`
- `docs/12_TEST_AND_VERIFICATION_GUIDE.md`

## 확장용 세부 문서

- `docs/15_DATA_SOURCE_EXPANSION_GUIDE.md`: 데이터 소스를 더 깊게 확장할 때
- `docs/16_PAGE_AND_FEATURE_EXPANSION_GUIDE.md`: 페이지, 차트, 카드, 기능을 더 늘릴 때