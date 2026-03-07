"""페이지에 보여줄 텍스트와 예시 데이터를 모아 둔 콘텐츠 모듈.

이 파일은 자기소개, 프로젝트 카드, 학습 주제, 로드맵처럼
"화면에 보여줄 내용"을 한곳에 모아 관리한다.
페이지 파일이 텍스트를 직접 하드코딩하지 않게 해서
문구 수정 시 영향 범위를 줄이는 것이 목적이다.

이 모듈을 주로 참조하는 파일:
- ``pages/1_About.py``: PROFILE_DATA 사용
- ``pages/2_Projects.py``: PROJECT_ITEMS 사용
- ``pages/4_Learning_Log.py``: LEARNING_TOPICS, ROADMAP_STEPS 사용
- ``app.py``: 항목 개수와 페이지 소개 문구 보조 데이터 사용
- ``tests/test_content.py``: 구조가 깨지지 않았는지 확인
"""

from __future__ import annotations

# PROFILE_DATA는 About 페이지에서 보여줄 자기소개와 운영 원칙 원본이다.
# tests/test_content.py 는 이 딕셔너리의 핵심 키가 빠지지 않았는지 확인한다.
PROFILE_DATA = {
    "name": "Your Name",
    "headline": "Python과 Streamlit으로 프로젝트 결과와 분석 과정을 정리하는 개발자",
    "intro": (
        "이 저장소는 앱 화면 자체를 꾸미는 데 목적이 있는 것이 아니라, "
        "내가 어떤 문제를 다루고 어떤 방식으로 구조를 나누며 어떻게 확장해 나가는지 "
        "설명 가능한 형태로 남기기 위한 작업 공간입니다."
    ),
    "focus_areas": [
        "프로젝트 결과와 분석 흐름을 읽기 쉬운 화면으로 정리하기",
        "코드, 문서, 테스트가 같은 기준으로 유지되게 만들기",
        "나중에 실제 데이터와 기능이 들어와도 구조가 무너지지 않게 준비하기",
    ],
    "tech_stack": [
        "Python",
        "Streamlit",
        "Pandas",
        "NumPy",
        "Plotly",
        "SQLAlchemy",
    ],
    "principles": [
        "하드코딩 절대경로를 쓰지 않는다.",
        "데이터 로직을 페이지 파일에 몰아넣지 않는다.",
        "문서를 나중에 몰아서 쓰지 않고 코드와 같이 갱신한다.",
    ],
    "next_steps": [
        "실제 프로젝트 데이터셋 연결",
        "프로젝트 설명 문구를 실제 경험 기반으로 교체",
        "확장 절차와 검증 문서를 더 촘촘하게 연결",
    ],
}

# PROJECT_ITEMS는 Projects 페이지에서 카드 형태로 반복 출력되는 리스트다.
# 카드 필드 이름을 유지하면 페이지 코드가 단순해지고 테스트도 쉽게 유지된다.
PROJECT_ITEMS = [
    {
        "title": "저장소 구조 재정리",
        "status": "building",
        "summary": "이 저장소를 장기적으로 유지할 수 있도록 코드, 문서, 테스트 구조를 다시 세우는 작업",
        "role": "구조 설계, 문서 체계 정리, 실행 흐름 점검",
        "highlights": [
            "페이지, 데이터, 공통 UI, 문서를 역할별로 분리",
            "README와 docs만 읽어도 구조를 이해할 수 있게 정리",
            "나중에 실제 프로젝트 사례를 추가하기 쉬운 기반 마련",
        ],
        "next_action": "실제 경험 기반 프로젝트 설명으로 카드 내용을 교체한다.",
    },
    {
        "title": "분석 화면 예시 구축",
        "status": "planned",
        "summary": "샘플 데이터를 이용해 필터, KPI, 차트, 상세 표가 어떻게 연결되는지 보여주는 예시 화면",
        "role": "데이터 모델링, 분석 화면 설계, 재사용 구조 점검",
        "highlights": [
            "외부 CSV 없이도 재현 가능한 샘플 데이터 생성",
            "필터 결과가 KPI와 차트에 함께 반영되도록 구성",
            "나중에 CSV, API, DB로 소스를 바꿔도 페이지 구조는 유지되게 설계",
        ],
        "next_action": "실제 데이터 연결 시 컬럼 매핑과 검증 로직을 추가한다.",
    },
    {
        "title": "문서와 코드 기준 정비",
        "status": "active",
        "summary": "저장소 목적, 수정 절차, 코드 해설, 확장 기준을 문서로 남겨 이후 작업의 기준점으로 쓰는 작업",
        "role": "문서 설계, 코드 해설 작성, 개발 원칙 정리",
        "highlights": [
            "구조 설명 문서와 코드 해설 문서를 분리",
            "API 호출, 캐시, 클래스 책임 분리 같은 주의사항을 명시",
            "실제 수정 전에 빠르게 볼 수 있는 체크리스트 구성",
        ],
        "next_action": "새 기능이 생길 때마다 관련 문서와 체크리스트를 함께 갱신한다.",
    },
]

# LEARNING_TOPICS는 Learning Log 페이지의 학습 주제 탭에서 사용한다.
# 각 항목은 "무엇을 배우는가 / 왜 중요한가 / 다음 연습" 구조를 유지해
# 이 저장소를 통해 익힐 Streamlit 학습 흐름을 보여준다.
LEARNING_TOPICS = [
    {
        "phase": "01",
        "title": "기본 UI와 페이지 설정",
        "summary": "제목, 텍스트, 컬럼, 사이드바, 상태 메시지처럼 화면의 기본 조합을 이해하는 단계",
        "why_it_matters": "Streamlit은 작은 UI 요소를 조합해 빠르게 구조를 만드는 도구라 기본기 이해가 중요하다.",
        "next_practice": "공통 헤더나 반복 UI 패턴을 함수로 분리해본다.",
    },
    {
        "phase": "02",
        "title": "입력 위젯과 상호작용",
        "summary": "selectbox, multiselect, slider, checkbox 같은 위젯이 분석 화면과 어떻게 연결되는지 이해하는 단계",
        "why_it_matters": "사용자 선택이 KPI와 차트를 바꾸는 것이 분석 화면의 핵심 흐름이기 때문이다.",
        "next_practice": "사이드바 필터를 추가하고 그 결과가 표와 차트에 함께 반영되게 만든다.",
    },
    {
        "phase": "03",
        "title": "레이아웃과 정보 배치",
        "summary": "컬럼, 컨테이너, 카드형 영역을 이용해 읽는 순서를 설계하는 단계",
        "why_it_matters": "같은 데이터라도 어떤 순서로 보여주느냐에 따라 전달력이 달라진다.",
        "next_practice": "홈 페이지와 분석 페이지의 정보 밀도를 다르게 설계해본다.",
    },
    {
        "phase": "04",
        "title": "데이터 가공과 차트 함수 분리",
        "summary": "집계 로직과 차트 렌더링을 페이지 밖으로 분리해 재사용 구조를 만드는 단계",
        "why_it_matters": "페이지 안에 모든 로직을 넣으면 확장할수록 수정 비용이 커진다.",
        "next_practice": "새 차트를 추가할 때 집계와 표현을 어디서 나눌지 먼저 정한다.",
    },
    {
        "phase": "05",
        "title": "확장 준비와 운영 습관",
        "summary": "캐시, API 호출, 테스트, 문서화 같은 확장 준비를 미리 생각하는 단계",
        "why_it_matters": "작은 예제를 실제 프로젝트로 키울 때 가장 많이 무너지는 부분이 운영 습관이기 때문이다.",
        "next_practice": "API 연결 전 rate limit, timeout, retry, cache 기준을 먼저 문서로 정리한다.",
    },
]

# ROADMAP_STEPS는 앞으로 어떤 순서로 저장소를 실제 프로젝트에 맞게 확장할지 설명한다.
# Learning Log 페이지와 README/문서의 방향성이 어긋나지 않도록 이곳에서 단계 기준을 관리한다.
ROADMAP_STEPS = [
    {
        "stage": "Step 1",
        "goal": "저장소 설명 실제화",
        "plan": "현재 더미 자기소개와 프로젝트 설명을 실제 경험 기반 문장으로 교체한다.",
        "done_definition": "README, About, Projects 문장이 실제 작업 내용과 맞는다.",
    },
    {
        "stage": "Step 2",
        "goal": "실제 데이터 연결",
        "plan": "샘플 데이터 대신 CSV 또는 API를 연결하되 `analysis_data.py` 인터페이스는 유지한다.",
        "done_definition": "데이터 소스가 바뀌어도 분석 페이지 UI 코드는 거의 수정되지 않는다.",
    },
    {
        "stage": "Step 3",
        "goal": "프로젝트 상세화",
        "plan": "Projects 목록을 실제 작업 사례 중심으로 갱신하고 필요하면 상세 페이지를 추가한다.",
        "done_definition": "각 프로젝트 항목에 문제, 역할, 결과, 다음 액션이 분명히 보인다.",
    },
    {
        "stage": "Step 4",
        "goal": "운영 문서 고도화",
        "plan": "확장 경험이 쌓일수록 update, checklist, code guide 문서를 실제 사례로 보강한다.",
        "done_definition": "새 환경에서도 README와 docs만으로 실행, 수정, 확장 방향을 이해할 수 있다.",
    },
]