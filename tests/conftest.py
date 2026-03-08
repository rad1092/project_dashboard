"""pytest 공통 테스트 설정과 샘플 데이터 fixture.

테스트는 실제 Desktop 데이터 폴더에 의존하지 않고도 돌아가야 하므로,
이 파일은 최소한의 전처리 CSV 구조를 임시 디렉터리에 만들어 서비스 테스트가 같은 계약을 검증하게 한다.
또한 프로젝트 루트를 import 경로에 추가해 ``dashboard`` 패키지를 안정적으로 불러오게 한다.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    # 테스트 실행 위치가 달라도 dashboard 패키지를 항상 같은 루트에서 import 하게 만든다.
    sys.path.insert(0, str(ROOT))


@pytest.fixture()
def sample_preprocessing_dir(tmp_path: Path) -> Path:
    """서비스 테스트용 최소 전처리 데이터 폴더를 만든다."""

    base = tmp_path / "preprocessing_data"
    preprocessing = base / "preprocessing"
    # 실제 앱이 찾는 외부 폴더 구조를 그대로 흉내 내야 resolve_data_dir 이후 흐름까지 자연스럽게 검증할 수 있다.
    preprocessing.mkdir(parents=True)

    # 특보 샘플은 지역 필터, 최신 시각 정렬, 재난 그룹 정규화를 모두 검증할 수 있게 작게 구성한다.
    pd.DataFrame(
        [
            {
                "발표시간": "2026-03-06 12:00",
                "지역": "경북",
                "시군구": "포항",
                "재난종류": "풍랑",
                "특보등급": "주의보",
                "해당지역": "포항 앞바다",
            },
            {
                "발표시간": "2026-03-06 13:00",
                "지역": "경북",
                "시군구": "포항",
                "재난종류": "호우",
                "특보등급": "경보",
                "해당지역": "포항시",
            },
            {
                "발표시간": "2026-03-05 09:00",
                "지역": "부산",
                "시군구": "해운대구",
                "재난종류": "폭염",
                "특보등급": "주의보",
                "해당지역": "부산 해운대구",
            },
        ]
    ).to_csv(preprocessing / "danger_clean.csv", index=False, encoding="utf-8-sig")

    # 통합 대피소 샘플은 포항/안동/울산처럼 서로 떨어진 지역을 섞어 둬야
    # 좌표 기반 지역 감지와 fallback 추천을 함께 검증할 수 있다.
    pd.DataFrame(
        [
            {
                "대피소명": "포항 냉방쉼터",
                "주소": "경북 포항시 남구 1",
                "대피소유형": "무더위쉼터",
                "위도": 36.019,
                "경도": 129.343,
                "시도": "경북",
                "시군구": "포항시",
                "지역": "경북 포항시",
                "수용인원": 50,
            },
            {
                "대피소명": "포항 통합대피소",
                "주소": "경북 포항시 남구 2",
                "대피소유형": "한파쉼터,무더위쉼터",
                "위도": 36.021,
                "경도": 129.345,
                "시도": "경북",
                "시군구": "포항시",
                "지역": "경북 포항시",
                "수용인원": 120,
            },
            {
                "대피소명": "안동 체육관",
                "주소": "경북 안동시 서후면 1",
                "대피소유형": "무더위쉼터",
                "위도": 36.5685,
                "경도": 128.7294,
                "시도": "경북",
                "시군구": "안동시",
                "지역": "경북 안동시",
                "수용인원": 70,
            },
            {
                "대피소명": "울산 통합대피소",
                "주소": "울산 남구 1",
                "대피소유형": "한파쉼터",
                "위도": 35.538,
                "경도": 129.312,
                "시도": "울산",
                "시군구": "남구",
                "지역": "울산 남구",
                "수용인원": 80,
            },
        ]
    ).to_csv(preprocessing / "final_shelter_dataset.csv", index=False, encoding="utf-8-sig")

    # 지진 전용 CSV 는 원본에 대피소유형이 없다는 실제 상황을 재현해
    # 서비스 계층의 표시용 컬럼 합성 로직을 테스트하게 만든다.
    pd.DataFrame(
        [
            {
                "대피소명": "포항 지진대피소",
                "주소": "경북 포항시 북구 1",
                "위도": 36.032,
                "경도": 129.365,
                "수용인원": 300,
                "시도": "경북",
                "시군구": "포항시",
            }
        ]
    ).to_csv(preprocessing / "earthquake_shelter_clean_2.csv", index=False, encoding="utf-8-sig")

    # 해일 전용 CSV 도 같은 이유로 통합 CSV 와 다른 스키마를 유지한 채 fixture 에 넣는다.
    pd.DataFrame(
        [
            {
                "대피소명": "포항 지진해일대피소",
                "주소": "경북 포항시 북구 2",
                "위도": 36.050,
                "경도": 129.390,
                "수용인원": 200,
                "지역": "경상북도",
                "시도": "경북",
                "시군구": "포항시",
            }
        ]
    ).to_csv(preprocessing / "tsunami_shelter_clean_2.csv", index=False, encoding="utf-8-sig")

    # fixture 는 최종 base 경로를 돌려 줘야 서비스 함수들이 실제 외부 폴더처럼 이 경로를 시작점으로 사용한다.
    return base
