from __future__ import annotations

import argparse
import random
from datetime import datetime
from pathlib import Path
from typing import Sequence

import pandas as pd

CRAWLED_ALERT_COLUMNS = [
    "발표시각",
    "지역",
    "시군구",
    "재난종류",
    "특보등급",
    "내용",
    "발송기관",
    "번호",
]

SUPPORTED_SIDOS = ("대구", "울산", "부산", "경북", "경남")
DISASTER_TYPES = ("호우", "태풍", "강풍", "풍랑", "폭염", "한파", "대설", "건조", "지진", "해일")
ALERT_LEVELS = ("경보", "주의보")

FULL_REGION_NAMES = {
    "대구": "대구광역시",
    "울산": "울산광역시",
    "부산": "부산광역시",
    "경북": "경상북도",
    "경남": "경상남도",
}

DEFAULT_OUTPUT_PATH = Path(__file__).resolve().parent / "data" / "disaster_message_realtime.csv"


def validate_supported_sido(sido: str) -> str:
    normalized = str(sido).strip()
    if normalized not in SUPPORTED_SIDOS:
        supported = ", ".join(SUPPORTED_SIDOS)
        raise ValueError(f"지원하지 않는 시도입니다: {normalized}. 지원 목록: {supported}")
    return normalized


def build_sender_name(sido: str, sigungu: str) -> str:
    return f"{FULL_REGION_NAMES[sido]} {sigungu}"


def build_message_content(*, sido: str, sigungu: str, disaster_type: str, alert_level: str) -> str:
    sender = build_sender_name(sido, sigungu)
    return (
        f"[모의훈련] {sender} 지역에 {disaster_type} {alert_level}가 발효되었습니다. "
        "주변 안전을 확인하고 필요 시 가까운 대피소로 이동하세요."
    )


def build_mock_alert_row(
    *,
    sido: str,
    sigungu: str,
    now: datetime | None = None,
    rng: random.Random | None = None,
) -> dict[str, str]:
    normalized_sido = validate_supported_sido(sido)
    normalized_sigungu = str(sigungu).strip()
    if not normalized_sigungu:
        raise ValueError("시군구를 비워둘 수 없습니다.")

    current_time = now or datetime.now()
    random_source = rng or random.SystemRandom()
    disaster_type = random_source.choice(DISASTER_TYPES)
    alert_level = random_source.choice(ALERT_LEVELS)

    row = {
        "발표시각": current_time.strftime("%Y-%m-%d %H:%M:%S"),
        "지역": normalized_sido,
        "시군구": normalized_sigungu,
        "재난종류": disaster_type,
        "특보등급": alert_level,
        "내용": build_message_content(
            sido=normalized_sido,
            sigungu=normalized_sigungu,
            disaster_type=disaster_type,
            alert_level=alert_level,
        ),
        "발송기관": build_sender_name(normalized_sido, normalized_sigungu),
        "번호": f"MCK-{current_time.strftime('%Y%m%d%H%M%S%f')}",
    }
    return row


def write_mock_disaster_message_csv(
    *,
    sido: str,
    sigungu: str,
    output_path: str | Path = DEFAULT_OUTPUT_PATH,
    now: datetime | None = None,
    rng: random.Random | None = None,
) -> Path:
    row = build_mock_alert_row(sido=sido, sigungu=sigungu, now=now, rng=rng)
    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([row], columns=CRAWLED_ALERT_COLUMNS).to_csv(
        output,
        index=False,
        encoding="utf-8-sig",
    )
    return output


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a mock disaster_message_realtime.csv for the live guidance page.",
    )
    parser.add_argument("--sido", required=True, help="Target province/city. Example: 경북")
    parser.add_argument("--sigungu", required=True, help="Target district/city. Example: 포항시")
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help="Optional output CSV path. Defaults to preprocessing_code/data/disaster_message_realtime.csv",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    output = write_mock_disaster_message_csv(
        sido=args.sido,
        sigungu=args.sigungu,
        output_path=args.output,
    )
    print(f"모의 재난문자 CSV 생성 완료: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
