"""과거 재난 이력 분석 화면용 데이터 준비 모듈.

왜 필요한가:
- 추천 화면은 한 번의 선택 결과를 보여 주지만, 분석 화면은 전체 특보 흐름을 본다.
- 이 모듈은 분석에 필요한 최소 컬럼과 KPI 계산만 따로 분리해 차트/홈 화면이 재사용하게 만든다.

누가 사용하는가:
- ``app.py`` 가 홈 KPI 를 만들 때 사용한다.
- ``pages/6_Data_Analysis.py`` 가 분석용 DataFrame 과 KPI 를 읽는다.

초보자 메모:
- 이 파일은 추천 페이지용 데이터가 아니라 "분석에 맞게 다듬은 특보 데이터"를 만든다.
- 즉, 같은 원본 CSV 를 읽더라도 분석에 필요한 열만 남기고 다시 정리하는 중간 계층이다.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from dashboard.services.disaster_data import (
    DisasterDatasetBundle,
    load_dataset_bundle,
    load_dataset_bundle_uncached,
)
from dashboard.services.shelter_recommendation import classify_disaster_type

ANALYSIS_COLUMNS = ["발표시간", "지역", "시군구", "재난종류", "재난그룹", "특보등급"]
# 분석 페이지와 홈 KPI 가 동시에 기대하는 최소 열 집합이라
# 차트 함수와 카드 계산은 이 컬럼 순서를 공통 계약으로 본다.


def load_analysis_dataset(data_dir: str | Path | None = None) -> pd.DataFrame:
    """분석 페이지가 공통으로 사용할 특보 이력 DataFrame 을 반환한다.

    분석 차트가 같은 열 집합을 공유해야 하므로, 여기서 필요한 컬럼만 남긴다.
    """

    bundle: DisasterDatasetBundle
    if data_dir is None:
        # 일반 앱 실행에서는 Streamlit 캐시를 쓰는 기본 로더를 사용해 반복 rerun 비용을 줄인다.
        bundle = load_dataset_bundle()
    else:
        # 테스트나 명시적 경로 검증에서는 override 경로를 그대로 읽는 uncached 버전을 사용한다.
        bundle = load_dataset_bundle_uncached(data_dir)

    # 추천 서비스와 분석 화면이 같은 재난 그룹 체계를 쓰도록 정규화 결과를 추가한다.
    analysis_frame = bundle.alerts.copy()
    # copy() 를 쓰는 이유는 원본 alerts DataFrame 에 분석 전용 열을 덧붙여도
    # 다른 페이지가 공유하는 원본 번들을 직접 바꾸지 않게 하기 위해서다.
    # 추천 서비스와 같은 분류 함수를 재사용하는 이유는
    # 추천 페이지의 재난 그룹 이름과 분석 차트 범례가 서로 다르게 보이지 않게 하기 위해서다.
    analysis_frame["재난그룹"] = analysis_frame["재난종류"].map(classify_disaster_type)
    # 필요한 열만 마지막에 잘라 두면 차트 함수와 KPI 계산이 같은 최소 계약을 공유하기 쉬워진다.
    return analysis_frame[ANALYSIS_COLUMNS].sort_values("발표시간").reset_index(drop=True)


def build_kpis(dataframe: pd.DataFrame) -> dict[str, object]:
    """분석 화면과 홈 화면에 필요한 기본 KPI 를 계산한다.

    홈 카드와 분석 카드가 같은 숫자를 보여 주도록 한 곳에서 계산한다.
    """

    if dataframe.empty:
        # 빈 경우에도 같은 키 구조를 반환해야 홈/분석 페이지 metric 코드가 조건문 없이 재사용된다.
        return {
            "alert_count": 0,
            "disaster_count": 0,
            "region_count": 0,
            "warning_count": 0,
            "latest_period": None,
        }

    # 카드 UI 가 바로 읽기 쉬운 단순 dict 형태로 반환한다.
    # 별도 객체 대신 dict 를 쓰는 이유는 metric 카드에서 필요한 값이 고정적이고 얕기 때문이다.
    # nunique() 는 "중복을 뺀 고유 개수"를 세는 pandas 메서드라 재난 그룹 수나 지역 수 계산에 자주 쓰인다.
    return {
        "alert_count": int(len(dataframe)),
        "disaster_count": int(dataframe["재난그룹"].nunique()),
        "region_count": int(dataframe["지역"].nunique()),
        "warning_count": int((dataframe["특보등급"] == "경보").sum()),
        "latest_period": pd.Timestamp(dataframe["발표시간"].max()),
    }
