"""화면 표시용 포맷터 모음.

이 파일은 숫자, 퍼센트, 날짜, 상태 라벨을 화면에 맞게 바꾸는 역할을 한다.
페이지 파일이 직접 문자열 포맷 규칙을 들고 있지 않게 해서
표시 형식을 바꿀 때 수정 지점을 줄이는 것이 목적이다.

이 모듈을 참조하는 주요 파일:
- ``app.py``: 홈 화면 KPI 카드
- ``pages/2_Projects.py``: 프로젝트 상태 라벨 변환
- ``pages/3_Data_Analysis.py``: KPI 카드와 상세 표 표시
"""

from __future__ import annotations

import pandas as pd

# STATUS_LABELS는 내부 코드에서 쓰는 상태값을 화면용 한국어 라벨로 바꾼다.
# 새 상태값을 추가하면 charts.py, content.py, 실제 데이터 소스와 함께 기준을 맞춰야 한다.
STATUS_LABELS = {
    "building": "구축 중",
    "planned": "계획 단계",
    "active": "운영 중",
    "Healthy": "정상",
    "Watch": "관찰 필요",
    "Boost": "개선 중",
    "Needs Review": "검토 필요",
}


def format_number(value: int | float) -> str:
    """정수형 KPI를 천 단위 구분 기호가 있는 문자열로 바꾼다."""
    return f"{value:,.0f}"


def format_percent(value: float, digits: int = 1) -> str:
    """0~1 범위 비율 값을 퍼센트 문자열로 바꾼다.

    Args:
        value: 예를 들어 0.1234 같은 비율 값.
        digits: 소수점 표시 자릿수.
    """
    return f"{value * 100:.{digits}f}%"


def format_decimal(value: float, digits: int = 1) -> str:
    """평균 점수처럼 소수점이 필요한 수치를 고정 자릿수 문자열로 바꾼다."""
    return f"{value:.{digits}f}"


def format_period(value: pd.Timestamp | None) -> str:
    """기간 컬럼 값을 화면 표시용 날짜 문자열로 바꾼다.

    ``None`` 이나 결측값은 ``-`` 로 바꿔서 빈 KPI 카드가 깨지지 않게 한다.
    """
    if value is None or pd.isna(value):
        return "-"
    return pd.Timestamp(value).strftime("%Y-%m-%d")


def label_status(status: str) -> str:
    """내부 상태 코드를 화면용 라벨로 바꾼다.

    매핑되지 않은 값은 원문을 그대로 반환해 예기치 않은 새 상태값도 표시할 수 있게 한다.
    """
    return STATUS_LABELS.get(status, status)