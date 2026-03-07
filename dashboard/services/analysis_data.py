"""분석용 데이터 생성과 KPI 계산을 담당하는 서비스 모듈.

이 파일은 페이지 코드가 데이터 준비 로직까지 직접 들고 있지 않도록
샘플 데이터 생성과 KPI 계산을 함수로 분리해 둔 곳이다.
현재는 데모 데이터를 생성하지만, 나중에 CSV/API/DB를 연결하더라도
가능하면 같은 함수 인터페이스를 유지하는 것이 목표다.

이 모듈을 참조하는 주요 파일:
- ``app.py``: 홈 화면 KPI 요약
- ``pages/3_Data_Analysis.py``: 필터 전 원본 데이터와 KPI 계산
- ``tests/test_analysis_data.py``: 데이터 스키마와 KPI 동작 검증
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# REQUIRED_COLUMNS는 이 저장소가 분석 데이터에 기대하는 기준 스키마다.
# 데이터 소스를 교체하더라도 이 컬럼 집합을 유지하면 pages/3_Data_Analysis.py 와
# tests/test_analysis_data.py 를 크게 바꾸지 않고 재사용할 수 있다.
REQUIRED_COLUMNS = [
    "period",
    "project",
    "category",
    "owner",
    "status",
    "visitors",
    "conversion_rate",
    "satisfaction_score",
    "impact_score",
    "release_count",
]

# PROJECT_PROFILES는 데모 데이터에서 반복 생성할 프로젝트 기본 정보다.
# 기간별로 각 프로젝트를 한 행씩 만들기 때문에 추이 차트와 표가 자연스럽게 연결된다.
PROJECT_PROFILES = [
    {"project": "Shelter Story", "category": "Civic Data", "owner": "Planning"},
    {"project": "Learning Journal", "category": "Education", "owner": "Analysis"},
    {"project": "Portfolio Board", "category": "Portfolio", "owner": "Product"},
    {"project": "Operations Watch", "category": "Operations", "owner": "Research"},
]

# 상태값 목록은 charts.py 와 formatters.py 가 함께 참조하는 분석용 분류 기준이다.
STATUSES = ["Healthy", "Watch", "Boost", "Needs Review"]


def load_demo_dataset(seed: int = 42) -> pd.DataFrame:
    """학습과 화면 검증에 사용할 데모 데이터프레임을 생성한다.

    Args:
        seed: 난수 시드 값.
            같은 시드를 쓰면 항상 같은 데이터가 생성되어 테스트와 화면 검증이 쉬워진다.

    Returns:
        ``REQUIRED_COLUMNS`` 순서를 갖는 정렬된 pandas DataFrame.

    이 함수를 따로 둔 이유:
    - 페이지 파일에서 난수 생성과 컬럼 조립 코드를 제거하기 위해
    - 이후 CSV/API/DB 소스로 교체할 때 같은 호출 지점을 유지하기 위해
    """
    # 랜덤 생성기를 함수 안에서 만들면 테스트가 시드별로 재현 가능하다.
    rng = np.random.default_rng(seed)

    # 주차 단위 기간을 만들어 추이 차트가 의미 있게 보이도록 한다.
    periods = pd.date_range("2025-09-01", periods=16, freq="W-MON")
    records: list[dict[str, object]] = []

    for period in periods:
        for profile in PROJECT_PROFILES:
            # 한 기간에 한 프로젝트당 한 행을 만들면
            # 차트와 표가 "기간 x 프로젝트" 구조로 깔끔하게 맞아 떨어진다.
            visitors = int(rng.integers(800, 4600))
            conversion_rate = round(float(rng.uniform(0.022, 0.108)), 4)
            satisfaction_score = round(float(rng.uniform(72.0, 96.0)), 1)
            impact_score = round(float(rng.uniform(61.0, 95.0)), 1)
            release_count = int(rng.integers(1, 5))

            # 상태값은 균등 분포보다 현실적인 편차를 보기 위해 가중치를 둔다.
            status = str(rng.choice(STATUSES, p=[0.42, 0.28, 0.2, 0.1]))

            # records는 이후 DataFrame으로 변환되므로
            # dict 키 이름을 REQUIRED_COLUMNS와 같은 기준으로 유지한다.
            records.append(
                {
                    "period": period,
                    "project": profile["project"],
                    "category": profile["category"],
                    "owner": profile["owner"],
                    "status": status,
                    "visitors": visitors,
                    "conversion_rate": conversion_rate,
                    "satisfaction_score": satisfaction_score,
                    "impact_score": impact_score,
                    "release_count": release_count,
                }
            )

    # 컬럼 순서를 고정해서 생성하면 테스트와 화면 코드가 같은 스키마를 기대할 수 있다.
    dataframe = pd.DataFrame.from_records(records, columns=REQUIRED_COLUMNS)

    # 정렬과 인덱스 초기화를 미리 해 두면 페이지 파일은 표시와 필터링에 집중할 수 있다.
    return dataframe.sort_values(["period", "project"]).reset_index(drop=True)


def build_kpis(dataframe: pd.DataFrame) -> dict[str, object]:
    """분석 화면과 홈 화면에 필요한 핵심 지표를 계산한다.

    Args:
        dataframe: 원본 또는 필터링된 분석 데이터프레임.

    Returns:
        KPI 카드에 바로 쓸 수 있는 딕셔너리.
        키 이름은 홈 화면과 분석 페이지가 함께 사용한다.

    주의점:
    - 필터 결과가 비었을 때도 같은 키 구조를 반환해야 페이지가 깨지지 않는다.
    - 화면 파일에서 직접 평균과 개수를 계산하지 않고 이 함수로 모아 두면
      계산 기준이 바뀌어도 수정 지점을 줄일 수 있다.
    """
    # 빈 데이터도 같은 형태의 응답을 반환해야
    # Streamlit 페이지가 조건문 없이 안전하게 다룰 수 있다.
    if dataframe.empty:
        return {
            "record_count": 0,
            "project_count": 0,
            "avg_conversion_rate": 0.0,
            "avg_impact_score": 0.0,
            "latest_period": None,
        }

    return {
        "record_count": int(len(dataframe)),
        "project_count": int(dataframe["project"].nunique()),
        "avg_conversion_rate": round(float(dataframe["conversion_rate"].mean()), 4),
        "avg_impact_score": round(float(dataframe["impact_score"].mean()), 1),
        "latest_period": pd.Timestamp(dataframe["period"].max()),
    }