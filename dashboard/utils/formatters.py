"""화면 표시용 포맷터 모음.

왜 필요한가:
- 같은 숫자/날짜라도 화면마다 표현이 달라지면 사용자가 결과를 비교하기 어렵다.
- 이 모듈은 카드, 표, 설명 텍스트가 같은 표시 형식을 쓰게 만드는 작은 규칙 모음이다.

초보자 메모:
- 포맷터는 값을 "계산"하기보다 "사람이 읽기 좋은 문자열"로 바꾸는 마지막 단계다.
- 그래서 추천 규칙이나 분석 로직과는 분리해 두는 편이 유지보수에 유리하다.
"""

from __future__ import annotations

import pandas as pd

STATUS_LABELS = {
    "building": "구축 중",
    "planned": "계획 단계",
    "active": "운영 중",
}

# 상태 코드는 내부 데이터 표현이고, 화면에는 사람이 읽기 쉬운 한국어 라벨을 보여 준다.
# 이렇게 분리해 두면 content.py 는 짧은 코드값을 유지하고, 페이지는 표시용 문구만 바꿔 쓸 수 있다.


def format_number(value: int | float) -> str:
    """천 단위 구분 기호가 있는 문자열로 바꾼다.

    KPI 카드와 수용인원 표시가 같은 포맷을 쓰도록 공통 함수로 둔다.
    """

    # float 로 한 번 감싸는 이유는 int/float 가 섞여 들어와도 같은 포맷 문자열로 처리하기 위해서다.
    # :,.0f 는 "천 단위 쉼표를 넣고 소수점 없이 출력"하라는 Python 포맷 문법이다.
    return f"{float(value):,.0f}"


def format_decimal(value: float, digits: int = 1) -> str:
    """소수점이 필요한 수치를 고정 자릿수 문자열로 바꾼다.

    거리나 비율처럼 소수점 자릿수가 필요한 값을 일관되게 표현한다.
    """

    # 자릿수를 인자로 받는 이유는 거리, 비율, 평균값처럼 화면별 요구 정밀도가 다르기 때문이다.
    # f-string 안에서 {digits} 를 다시 쓰는 형태는 "가변 자릿수" 포맷을 만들 때 자주 쓰인다.
    return f"{value:.{digits}f}"


def format_distance_km(value: float | None) -> str:
    """직선 거리 값을 km 문자열로 바꾼다.

    추천 결과 표와 카드가 같은 거리 표시 형식을 쓰도록 만든다.
    """

    if value is None or pd.isna(value):
        # 결측값을 "-" 로 통일해 두면 카드와 표가 NaN, None 같은 내부 표현을 그대로 노출하지 않는다.
        return "-"
    return f"{float(value):.2f} km"


def format_datetime(value: pd.Timestamp | None) -> str:
    """날짜/시간 값을 화면용 문자열로 바꾼다.

    특보 시각을 카드와 표에서 같은 포맷으로 보여 주기 위한 공통 함수다.
    """

    if value is None or pd.isna(value):
        # pd.isna(value) 는 pandas 기준으로 이 값이 결측인지 확인하는 함수라 None, NaN 같은 경우를 함께 잡는다.
        return "-"
    # pd.Timestamp 로 한 번 감싸 두면 datetime, str, Timestamp 가 섞여 들어와도 같은 출력 형식을 유지한다.
    # strftime() 은 날짜/시간 객체를 원하는 문자열 모양으로 바꾸는 표준 메서드다.
    return pd.Timestamp(value).strftime("%Y-%m-%d %H:%M")


def label_status(status: str) -> str:
    """내부 상태 코드를 화면용 라벨로 바꾼다.

    Projects 페이지처럼 내부 코드값을 그대로 노출하면 딱딱해 보이기 때문에 변환한다.
    """

    # 매핑되지 않은 값은 원문 그대로 돌려 보내 새 상태 코드가 들어와도 화면이 즉시 깨지지 않게 한다.
    # dict.get(status, status) 는 사전에 값이 있으면 번역 라벨을, 없으면 원래 문자열을 돌려주는 fallback 패턴이다.
    return STATUS_LABELS.get(status, status)
