"""홈 페이지 엔트리포인트.

이 파일은 Streamlit 앱이 처음 열릴 때 보이는 홈 화면을 정의한다.
실제 데이터 준비는 ``dashboard.services.analysis_data`` 에 맡기고,
표시 형식은 ``dashboard.utils.formatters`` 에 맡겨서 홈 파일은
"어떤 내용을 어떤 순서로 보여줄지"만 조합하도록 유지한다.

이 파일이 연결하는 주요 모듈:
- ``dashboard.config``: 앱 공통 제목과 페이지 메타데이터
- ``dashboard.content``: 홈에서 소개할 프로젝트/학습/로드맵 원본 데이터
- ``dashboard.services.analysis_data``: 데모 데이터와 KPI 계산
- ``dashboard.utils.formatters``: 숫자와 날짜 표시 형식

주요 수정 시점:
- 홈 화면 소개 문구를 바꾸고 싶을 때
- 첫 화면 KPI 카드 구성을 바꾸고 싶을 때
- 어떤 문서와 페이지를 먼저 읽게 할지 안내를 조정하고 싶을 때
"""

from __future__ import annotations

import streamlit as st

from dashboard.config import APP_TITLE, PAGE_META, apply_page_config
from dashboard.content import LEARNING_TOPICS, PROJECT_ITEMS, ROADMAP_STEPS
from dashboard.services.analysis_data import build_kpis, load_demo_dataset
from dashboard.utils.formatters import format_number, format_percent, format_period


# 각 페이지는 자신의 키를 넘겨 같은 설정 함수를 재사용한다.
apply_page_config("home")

# 홈 화면 제목과 한 줄 소개는 config.py의 메타데이터를 기준으로 맞춘다.
st.title(PAGE_META["home"]["label"])
st.write(
    "Streamlit을 이용해 프로젝트 결과, 데이터 분석 과정, 학습 내용을 정리하고 설명하는 저장소입니다. "
    "이 앱은 화면 자체를 자랑하기보다, 어떤 구조로 작업을 쌓고 설명하는지 보여주는 기준점 역할을 합니다."
)
st.caption(
    "왼쪽 사이드바에서 About, Projects, Data Analysis, Learning Log 페이지를 이동할 수 있습니다."
)

# 홈 화면도 분석 페이지와 같은 데이터 인터페이스를 사용해 요약 수치를 계산한다.
# 이렇게 해 두면 나중에 데이터 소스가 CSV/API/DB로 바뀌어도 홈 화면 로직은 거의 유지된다.
dataframe = load_demo_dataset()
kpis = build_kpis(dataframe)

# 숫자와 날짜 표시는 formatters.py를 통과시켜 페이지마다 형식이 달라지지 않게 한다.
metric_columns = st.columns(4)
metric_columns[0].metric("분석 기록 수", format_number(kpis["record_count"]))
metric_columns[1].metric("프로젝트 수", format_number(kpis["project_count"]))
metric_columns[2].metric("평균 전환율", format_percent(kpis["avg_conversion_rate"]))
metric_columns[3].metric("최근 기준일", format_period(kpis["latest_period"]))

st.divider()

# 홈 화면은 왼쪽에 저장소 설명, 오른쪽에 운영 원칙과 다음 문서 안내를 배치한다.
left, right = st.columns([1.1, 0.9], gap="large")

with left:
    with st.container(border=True):
        st.subheader("이 저장소에서 보여주는 것")
        for item in PAGE_META.values():
            st.markdown(f"- **{item['label']}**: {item['summary']}")

    with st.container(border=True):
        st.subheader("현재 포함된 내용")
        # content.py에 모아둔 리스트 길이를 그대로 보여주면
        # 홈 화면 설명과 실제 데이터 개수가 어긋나지 않는다.
        st.markdown(f"- 프로젝트 기록: **{len(PROJECT_ITEMS)}개**")
        st.markdown(f"- 학습 주제 정리: **{len(LEARNING_TOPICS)}개**")
        st.markdown(f"- 확장 로드맵: **{len(ROADMAP_STEPS)}단계**")
        st.markdown("- 외부 CSV 없이 실행 가능한 분석 화면 예시")

with right:
    with st.container(border=True):
        st.subheader("운영 원칙")
        st.markdown("- 페이지는 화면 조합만 담당하고, 데이터 로직은 서비스 모듈로 분리한다.")
        st.markdown("- 설명 문구와 코드는 서로 다른 이야기를 하지 않게 함께 수정한다.")
        st.markdown("- 실험 코드는 바로 합치지 않고 구조 기준에 맞게 다시 정리한다.")

    with st.container(border=True):
        st.subheader("다음에 볼 문서")
        st.markdown("- 구조를 이해할 때: `docs/02_STRUCTURE_GUIDE.md`")
        st.markdown("- 수정 절차와 확장 기준: `docs/04_UPDATE_AND_EXPANSION_GUIDE.md`")
        st.markdown("- 코드 해설: `docs/08_CODEBASE_OVERVIEW.md`부터 순서대로")

st.divider()

with st.container(border=True):
    st.subheader("저장소 시작 안내")
    st.code("streamlit run app.py", language="powershell")
    # 공통 제목은 config.py의 APP_TITLE을 사용해 홈과 하위 페이지의 명명 규칙을 맞춘다.
    st.write(
        f"`{APP_TITLE}`는 홈 화면이며, 나머지 페이지는 Streamlit의 멀티페이지 기능으로 자동 연결됩니다."
    )