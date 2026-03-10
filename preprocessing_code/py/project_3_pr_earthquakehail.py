"""지진해일 대피소 원본 데이터를 수집하는 참고용 스크립트.

이 파일도 현재 Streamlit 앱이 직접 호출하지 않는다.
이미 전처리된 CSV 가 준비되어 있기 때문에, 이 스크립트는 원본 데이터를 다시 받아야 할 때의 참고용으로만 남긴다.

입력:
- 공공 API 응답(JSON)

출력:
- ``tsunami_shelter_raw.csv``

의미:
- 이후 노트북에서 정리할 해일 대피소 원본을 수집하는 1차 단계다.
"""

from __future__ import annotations

import os
import time

import pandas as pd
import requests


API_URL = "https://www.safetydata.go.kr/V2/api/DSSP-IF-10944"
SERVICE_KEY = os.environ.get("SAFETYDATA_TSUNAMI_KEY", "YOUR_PUBLIC_API_KEY")
ROWS_PER_PAGE = 1000
# 환경변수 이름을 코드에 남겨 두면 재수집 시 어떤 키를 준비해야 하는지 바로 확인할 수 있다.


def fetch_tsunami_shelters() -> pd.DataFrame:
    """지진해일 대피소 원본 데이터를 페이지 단위로 수집한다.

    원본 API 응답을 최대한 그대로 CSV 로 남겨 이후 전처리 노트북이 컬럼을 선택하게 한다.
    """

    all_records: list[dict[str, object]] = []
    page = 1

    while True:
        # 페이지 단위 수집 구조를 명시적으로 남겨 두면 나중에 API 사양이 바뀌었을 때 수정 지점이 분명하다.
        params = {
            "serviceKey": SERVICE_KEY,
            "pageNo": page,
            "numOfRows": ROWS_PER_PAGE,
            "type": "json",
        }

        # 이 단계에서는 응답을 최대한 원본 그대로 보존하는 것이 중요하므로, 가공은 하지 않고 바로 누적만 한다.
        response = requests.get(API_URL, params=params, timeout=30)
        # HTTP 오류를 바로 올려야 누락된 페이지를 나중에 눈치채지 못하는 상황을 막을 수 있다.
        response.raise_for_status()
        payload = response.json()
        body = payload.get("body") or []

        if not body:
            break

        all_records.extend(body)
        print(f"{page} 페이지 / {len(all_records)}건")

        page += 1
        # 너무 빠른 연속 호출을 피하기 위한 짧은 대기이며, 참고용 스크립트라도 재수집 안정성에 도움을 준다.
        time.sleep(0.2)

    return pd.DataFrame(all_records)


def main() -> None:
    """원본 데이터를 받아 CSV 로 저장한다.

    이 파일의 역할은 전처리 전 원본 CSV 확보까지이며, 정제는 노트북 단계에서 이어진다.
    """

    if SERVICE_KEY == "YOUR_PUBLIC_API_KEY":
        raise RuntimeError("환경변수 `SAFETYDATA_TSUNAMI_KEY` 에 실제 공개 API 키를 넣어 달라.")

    dataframe = fetch_tsunami_shelters()
    # 후속 노트북이 원본 스키마를 직접 보고 정제할 수 있게 1차 수집 결과를 그대로 저장한다.
    # 즉, 이 파일의 목적은 앱용 최종 CSV 가 아니라 "전처리 전 원본 확보"에 있다.
    dataframe.to_csv("tsunami_shelter_raw.csv", index=False, encoding="utf-8-sig")
    print("CSV 저장 완료")


if __name__ == "__main__":
    main()
