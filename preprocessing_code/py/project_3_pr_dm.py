"""재난 문자/특보 데이터를 수집하고 정리하는 참고용 전처리 스크립트.

이 파일은 현재 Streamlit 앱이 직접 실행하는 코드가 아니다.
과거에 어떤 방식으로 공공 데이터를 받아 전처리 CSV 를 만들었는지 남겨 두는 참고용 스크립트이며,
향후 원본 데이터를 다시 수집해야 할 때 어디를 바꿔야 하는지 보여주는 역할을 한다.

입력:
- 공공 API 응답(JSON)

출력:
- ``disaster_clean_2020_2024.csv`` 같은 정리된 CSV

주의:
- 실제 서비스 키는 코드에 넣지 않는다.
- 현재 앱은 이 스크립트 대신 이미 전처리된 CSV 만 읽는다.
"""

from __future__ import annotations

import os
import time

import pandas as pd
import requests


API_URL = "https://www.safetydata.go.kr/V2/api/DSSP-IF-00247"
SERVICE_KEY = os.environ.get("SAFETYDATA_ALERT_KEY", "YOUR_PUBLIC_API_KEY")
ROWS_PER_PAGE = 1000
# 환경변수 이름을 코드에 남겨 두는 이유는 재수집 시 "어떤 키를 준비해야 하는지"를 바로 알게 하기 위해서다.


def collect_alert_history(start_year: int = 2020, end_year: int = 2024) -> pd.DataFrame:
    """여러 연도의 재난 문자 데이터를 페이지 단위로 수집한다.

    연도별로 API 요청 범위를 나누는 이유는 한 번에 너무 큰 기간을 요청할 때
    누락이나 응답 실패를 추적하기 어렵기 때문이다.
    """

    all_records: list[dict[str, object]] = []

    for year in range(start_year, end_year + 1):
        print(f"\n==== {year}년 수집 시작 ====")
        page = 1

        while True:
            # API 가 페이지네이션 구조이므로 요청 파라미터를 매 반복마다 명시적으로 만든다.
            # crtDtStart / crtDtEnd 를 연도 단위로 쪼개는 이유는 대량 호출 실패가 났을 때 어느 연도에서 깨졌는지 추적하기 쉽기 때문이다.
            params = {
                "serviceKey": SERVICE_KEY,
                "pageNo": page,
                "numOfRows": ROWS_PER_PAGE,
                "type": "json",
                "crtDtStart": f"{year}0101",
                "crtDtEnd": f"{year}1231",
            }

            # 현재는 참고용 스크립트지만, 재수집 시 네트워크 오류를 바로 알 수 있게 예외를 그대로 올린다.
            response = requests.get(API_URL, params=params, timeout=30)
            # raise_for_status() 를 바로 호출하는 이유는
            # 참고용 스크립트라도 수집 실패를 조용히 넘기면 누락된 연도를 나중에 찾기 더 어려워지기 때문이다.
            response.raise_for_status()
            payload = response.json()
            body = payload.get("body") or []

            if not body:
                print(f"{year}년 데이터 수집 완료")
                break

            all_records.extend(body)
            print(f"{year}년 {page}페이지 / 총 {len(all_records)}건")

            page += 1
            # 짧게 쉬는 이유는 재수집 시 연속 호출 부담을 조금 낮추고 실패 원인을 덜 복잡하게 만들기 위해서다.
            time.sleep(0.2)

    return pd.DataFrame(all_records)


def preprocess_alert_history(dataframe: pd.DataFrame) -> pd.DataFrame:
    """앱에서 쓰기 좋은 최소 컬럼 구조만 남기도록 전처리한다.

    원본 메시지 전체를 다 들고 가지 않고, 추천/분석에 필요한 시간·연도·지역·재난 종류만 남긴다.
    """

    filtered = dataframe.copy()

    # 실종자 탐색 문자처럼 대피소 추천과 직접 관련 없는 문자는 제거한다.
    filtered = filtered[~filtered["MSG_CN"].str.contains("찾습니다|실종|배회|목격", na=False)]

    # 날짜와 연도 컬럼은 이후 필터링과 집계에 쓰이므로 먼저 정리한다.
    filtered["CRT_DT"] = pd.to_datetime(filtered["CRT_DT"])
    filtered["year"] = filtered["CRT_DT"].dt.year

    # 수신 지역명은 지역 단위 비교가 쉽도록 광역 단위 문자열만 남긴다.
    # 여기서 광역 단위로 줄여 두어야 이후 노트북과 앱이 같은 지역 기준으로 묶기 쉬워진다.
    filtered["region"] = filtered["RCPTN_RGN_NM"].str.split().str[0]
    filtered["region"] = filtered["region"].str.replace("특별시", "")
    filtered["region"] = filtered["region"].str.replace("광역시", "")
    filtered["region"] = filtered["region"].str.replace("특별자치도", "")
    filtered["region"] = filtered["region"].str.replace("도", "")

    # 반환 열을 고정해 두면 이후 노트북/스크립트가 같은 최소 구조를 기준으로 이어진다.
    return filtered[["CRT_DT", "year", "region", "DST_SE_NM", "MSG_CN"]]


def main() -> None:
    """수집과 전처리를 순서대로 실행한다.

    현재 앱은 이 스크립트를 직접 호출하지 않지만,
    원본 데이터 재생성이 필요할 때 어떤 순서로 실행해야 하는지 보여 주는 진입점이다.
    """

    if SERVICE_KEY == "YOUR_PUBLIC_API_KEY":
        raise RuntimeError("환경변수 `SAFETYDATA_ALERT_KEY` 에 실제 공개 API 키를 넣어 달라.")

    dataframe = collect_alert_history()
    print("수집 데이터:", len(dataframe))

    cleaned = preprocess_alert_history(dataframe)
    print("최종 데이터:", len(cleaned))

    # 앱은 이미 만들어진 CSV 를 읽기만 하므로, 이 저장 단계는 데이터 재생성용 참고 절차다.
    # utf-8-sig 로 저장하는 이유는 Windows 기반 노트북/엑셀에서도 한글 컬럼이 덜 깨지게 하기 위해서다.
    cleaned.to_csv("disaster_clean_2020_2024.csv", index=False, encoding="utf-8-sig")
    print("CSV 저장 완료")


if __name__ == "__main__":
    main()
