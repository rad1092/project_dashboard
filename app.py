"""홈 페이지 엔트리포인트.

이 파일은 ``streamlit run app.py`` 로 앱을 열었을 때 가장 먼저 보이는 화면이다.
현재 프로젝트가 무엇을 목표로 하는지, 어떤 데이터가 연결되어 있는지,
그리고 사용자가 어느 페이지부터 보면 되는지를 한 번에 안내하는 역할을 맡는다.

이 파일이 주로 호출하는 모듈:
- ``dashboard.config``: 공통 페이지 제목과 메타데이터
- ``dashboard.services.disaster_data``: 전처리 데이터 로딩과 데이터셋 요약
- ``dashboard.services.analysis_data``: 홈에서 쓸 기본 KPI 계산
- ``dashboard.utils.formatters``: 숫자와 날짜 표시 형식

나중에 이 파일을 바꾸는 대표 상황:
- 홈 화면 소개 문구를 재난 앱 기준으로 조정하고 싶을 때
- 첫 화면 KPI 카드 구성을 바꾸고 싶을 때
- 새 페이지가 추가되어 홈 안내 순서를 손보고 싶을 때
"""

from __future__ import annotations

import streamlit as st

from dashboard.config import PAGE_META, apply_page_config
from dashboard.content import HOME_OVERVIEW_POINTS, LIMITATIONS
from dashboard.services.analysis_data import build_kpis, load_analysis_dataset
from dashboard.services.disaster_data import (
    build_dataset_catalog,
    load_dataset_bundle,
    resolve_data_dir,
)
from dashboard.utils.formatters import format_datetime, format_number


# 홈 화면도 다른 페이지와 같은 공통 설정 함수를 사용해 제목과 레이아웃 기준을 맞춘다.
# 이렇게 해야 브라우저 탭 제목, 아이콘, 레이아웃 폭이 페이지마다 따로 놀지 않는다.
apply_page_config("home")

# PAGE_META 에 적어 둔 label 을 그대로 재사용하는 이유는
# 홈 문구와 실제 페이지 제목 체계가 서로 엇갈리지 않게 하기 위해서다.
st.title(PAGE_META["home"]["label"])
st.write(
    "이 앱은 전처리된 재난 특보 이력과 대피소 좌표 데이터를 이용해 "
    "대피소 추천 흐름과 분석 화면을 함께 보여주는 Streamlit 프로젝트입니다."
)
st.caption(
    "실시간 API나 유료 지도 API는 아직 연결하지 않았으며, 현재는 과거 전처리 데이터 기준으로 동작합니다."
)

try:
    # 홈 화면에서부터 실제 데이터 연결 상태를 확인할 수 있게 외부 데이터 폴더를 바로 읽는다.
    data_dir = resolve_data_dir()
    bundle = load_dataset_bundle()
    analysis_frame = load_analysis_dataset()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.info(
        "`.streamlit/secrets.toml` 또는 `PREPROCESSING_DATA_DIR` 환경변수에 "
        "`C:/Users/Admin/Desktop/preprocessing_data` 같은 경로를 지정하면 된다."
    )
    st.stop()

# 홈 KPI 는 사용자가 지금 연결된 데이터 규모를 첫 화면에서 바로 파악하게 하는 요약 영역이다.
# 아래 metric_columns 는 숫자만 나열하는 것이 아니라 "이 앱이 어떤 데이터 위에서 움직이는지"를 압축해서 보여 준다.
kpis = build_kpis(analysis_frame)
catalog = build_dataset_catalog(bundle)

metric_columns = st.columns(4)
metric_columns[0].metric("특보 기록 수", format_number(kpis["alert_count"]))
metric_columns[1].metric("통합 대피소 수", format_number(len(bundle.shelters)))
metric_columns[2].metric("권역 수", format_number(kpis["region_count"]))
metric_columns[3].metric("최근 특보 시각", format_datetime(kpis["latest_period"]))

st.divider()

# 왼쪽은 "무엇을 볼 수 있는가", 오른쪽은 "어떤 데이터와 한계 위에서 움직이는가"를 나눠 보여 준다.
left, right = st.columns([1.05, 0.95], gap="large")

with left:
    with st.container(border=True):
        st.subheader("이 앱에서 바로 볼 수 있는 것")
        # overview 포인트는 홈에서 가장 먼저 읽히는 문장이라 길게 설명하지 않고
        # 사용자가 바로 다음 행동을 정할 수 있을 정도의 정보만 남긴다.
        for point in HOME_OVERVIEW_POINTS:
            st.markdown(f"- {point}")

    with st.container(border=True):
        st.subheader("추천 흐름 페이지")
        # 페이지 키를 하드코딩 문자열로 반복하지 않고 PAGE_META 를 함께 쓰는 이유는
        # 페이지 순서나 이름이 바뀌어도 홈 안내가 같은 기준표를 따라가게 하기 위해서다.
        for page_key in ["about", "recommendation", "flow", "realtime"]:
            page = PAGE_META[page_key]
            st.markdown(f"- **{page['label']}**: {page['summary']}")

    with st.container(border=True):
        st.subheader("보조 페이지")
        for page_key in ["projects", "analysis", "learning"]:
            page = PAGE_META[page_key]
            st.markdown(f"- **{page['label']}**: {page['summary']}")

with right:
    with st.container(border=True):
        st.subheader("현재 연결된 데이터셋")
        # 데이터셋 카탈로그를 홈에서도 보여 주면 사용자가 CSV 역할을 페이지 진입 전에 이해할 수 있다.
        # item 딕셔너리 구조는 build_dataset_catalog() 의 반환 계약을 그대로 따른다.
        for item in catalog:
            st.markdown(
                f"- **{item['name']}**: {format_number(item['rows'])}건, "
                f"{item['description']}"
            )

    with st.container(border=True):
        st.subheader("현재 단계의 한계")
        for item in LIMITATIONS:
            st.markdown(f"- {item}")

    with st.container(border=True):
        st.subheader("외부 데이터 폴더")
        st.code(str(data_dir), language="text")
        st.write(
            "이 경로의 CSV는 앱이 읽기 전용으로 사용한다. "
            "전처리 원본은 수정하지 않고, 페이지와 문서만 구조화하는 것이 이번 단계의 기준이다."
        )

st.divider()

with st.container(border=True):
    st.subheader("실행 방법")
    st.code("streamlit run app.py", language="powershell")
    # 실행 명령과 페이지 읽는 순서를 같은 박스에 두는 이유는
    # 처음 보는 사용자가 "어떻게 켜고 어디부터 보면 되는지"를 한 번에 이해하게 만들기 위해서다.
    st.write(
        "왼쪽 사이드바에서 `1 About` 부터 `7 Learning Log` 까지 순서대로 이동하면 "
        "소개 → 추천 → 작동 설명 → 실시간 확장 준비 → 보조 문서를 한 흐름으로 볼 수 있다."
    )
