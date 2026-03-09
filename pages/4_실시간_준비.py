"""향후 실시간 버전 확장 포인트를 설명하는 준비 페이지.

현재는 과거 전처리 데이터 기반 앱이지만,
이 페이지는 자동 위치, 실시간 특보, 실제 경로 안내를 나중에 붙일 자리를 먼저 정리한다.
즉시 실행보다 "어디를 바꿔야 하는지"를 설명하는 설계 페이지에 가깝다.

초보자 메모:
- 여기의 버튼과 코드 조각은 지금 동작하는 기능이 아니라, 미래 확장 위치를 설명하는 표지판이다.
- 그래서 이 파일은 실제 API 호출 코드보다 설명용 텍스트와 스텁 예시가 중심이다.
"""

from __future__ import annotations

import streamlit as st

from dashboard.components.layout import render_bordered_points, render_page_intro
from dashboard.config import apply_page_config
from dashboard.content import FUTURE_CODE_SNIPPETS, REALTIME_EXPANSION_ITEMS


apply_page_config("realtime")

render_page_intro(
    "4 실시간 준비",
    "현재는 실행하지 않지만, 나중에 자동 위치·실시간 특보·경로 안내를 어디에 붙일지 설명과 주석으로 먼저 정리한 페이지입니다.",
    "이 페이지의 버튼은 설명용 자리표시자이며 실제 API 호출을 하지 않습니다.",
)

# 비활성화된 버튼은 미래 기능의 위치를 시각적으로 보여 주는 자리표시자다.
# 실제 기능이 없더라도 버튼 모양을 먼저 고정해 두면 나중에 어떤 사용자 행동이 추가될지 UI 차원에서 미리 정리할 수 있다.
button_columns = st.columns(3)
# columns() 를 먼저 만들고 각 칸에서 button() 을 호출하면 같은 줄에 버튼 3개를 나란히 놓을 수 있다.
button_columns[0].button("현재 위치 자동 감지 (준비중)", disabled=True)
button_columns[1].button("실시간 특보 새로고침 (준비중)", disabled=True)
button_columns[2].button("실제 경로 안내 (준비중)", disabled=True)

st.info(
    "현재 앱은 과거 전처리 데이터와 수동 좌표 입력을 기준으로 동작한다. "
    "아래 내용은 미래에 어떤 코드를 어디에 붙일지 설명하기 위한 준비 문서 역할을 한다."
)

for item in REALTIME_EXPANSION_ITEMS:
    with st.container(border=True):
        st.subheader(item["title"])
        st.write(item["summary"])
        # why_blocked 를 따로 보여 주는 이유는 "왜 지금은 안 되는지"를 단순 미구현이 아니라 의도된 범위 제한으로 설명하기 위해서다.
        # item 은 content.py 의 dict 데이터이므로 키 이름이 바뀌면 이 페이지도 함께 수정돼야 한다.
        st.markdown(f"**지금 막아 둔 이유**: {item['why_blocked']}")

left, right = st.columns(2, gap="large")

with left:
    with st.container(border=True):
        st.subheader("자동 위치 스텁")
        # 스텁 코드는 지금은 실행하지 않지만, 나중에 어떤 모듈 인터페이스가 필요한지 보여 준다.
        # st.code 로 노출하는 이유는 실제 주석 처리 코드를 페이지 안에서 읽게 해 확장 위치를 개발자에게 바로 드러내기 위해서다.
        st.code(FUTURE_CODE_SNIPPETS["geolocation"], language="python")

    with st.container(border=True):
        st.subheader("실시간 특보 스텁")
        st.code(FUTURE_CODE_SNIPPETS["alerts"], language="python")

with right:
    with st.container(border=True):
        st.subheader("경로 안내 스텁")
        st.code(FUTURE_CODE_SNIPPETS["routing"], language="python")

    render_bordered_points(
        "실시간 전환 전에 먼저 정리할 것",
        [
            "위치 권한을 받을 브라우저/컴포넌트 방식을 정한다.",
            "실시간 공공 API의 인증 방식과 호출 제한을 문서화한다.",
            "직선 거리와 실제 경로를 어떤 버튼과 어떤 문구로 구분할지 정한다.",
        ],
    )
