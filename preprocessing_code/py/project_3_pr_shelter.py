"""지진 대피소 원본 데이터를 수집하는 참고용 스크립트.

현재 앱은 이 파일을 직접 실행하지 않는다.
이미 전처리된 ``earthquake_shelter_clean_2.csv`` 를 읽기 때문에,
이 스크립트는 원본 데이터를 다시 받을 때 어떤 API 와 컬럼을 쓰는지 보여주는 보조 자료다.

의미:
- 이후 노트북에서 정리할 지진 대피소 원본을 확보하는 첫 단계 스크립트다.
"""

from __future__ import annotations

import os
import time

import pandas as pd
import requests


API_URL = "https://www.safetydata.go.kr/V2/api/DSSP-IF-10943"
SERVICE_KEY = os.environ.get("SAFETYDATA_EARTHQUAKE_KEY", "YOUR_PUBLIC_API_KEY")
ROWS_PER_PAGE = 1000
# 환경변수명을 명시해 두면 나중에 재수집 담당자가 코드 수정 없이 준비할 값만 바로 알 수 있다.


def fetch_earthquake_shelters() -> pd.DataFrame:
    """지진 대피소 원본 데이터를 페이지 단위로 수집한다.

    수집 단계에서는 가공을 최소화하고, 이후 노트북이 컬럼 선택과 주소 정리를 맡는다.
    """

    all_records: list[dict[str, object]] = []
    page = 1

    while True:
        # API 요청 파라미터를 명시적으로 남겨 두면 재수집 시 어떤 조건으로 받았는지 추적하기 쉽다.
        params = {
            "serviceKey": SERVICE_KEY,
            "pageNo": page,
            "numOfRows": ROWS_PER_PAGE,
            "type": "json",
        }

        # 원본 API 응답이 이후 전처리의 기준이 되므로, 이 스크립트 단계에서는 컬럼 가공 없이 바로 적재한다.
        response = requests.get(API_URL, params=params, timeout=30)
        # 수집 단계에서는 "조용한 실패"가 가장 위험하므로 HTTP 오류를 바로 예외로 올린다.
        response.raise_for_status()
        payload = response.json()
        body = payload.get("body") or []

        if not body:
            print("수집 완료")
            break

        all_records.extend(body)
        print(f"{page}페이지 수집 / 총 {len(all_records)}건")

        page += 1
        # 짧은 대기 시간은 참고용 스크립트라도 재수집 시 연속 호출 부담을 조금 낮추기 위한 안전장치다.
        time.sleep(0.2)

    return pd.DataFrame(all_records)


def main() -> None:
    """원본 데이터를 받아 CSV 로 저장한다.

    앱에서 직접 쓰는 최종 CSV 가 아니라, 후속 전처리의 출발점이 되는 원본 파일을 저장한다.
    """

    if SERVICE_KEY == "YOUR_PUBLIC_API_KEY":
        raise RuntimeError("환경변수 `SAFETYDATA_EARTHQUAKE_KEY` 에 실제 공개 API 키를 넣어 달라.")

    dataframe = fetch_earthquake_shelters()
    print("총 데이터:", len(dataframe))

    # 최종 앱용 CSV 가 아니라, 노트북에서 다시 정제할 출발점 원본을 남기는 저장 단계다.
    # 그래서 여기서는 컬럼을 손대지 않고 API 원문을 최대한 그대로 저장하는 쪽을 택한다.
    dataframe.to_csv("earthquake_shelter_raw.csv", index=False, encoding="utf-8-sig")
    print("CSV 저장 완료")


if __name__ == "__main__":
    main()
