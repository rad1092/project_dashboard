from __future__ import annotations

import re
import sys
import time
from pathlib import Path

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL = "https://www.safetydata.go.kr/disaster-data/disasterNotification"
SYSTEM_CHROME_BINARY_PATH = Path("/usr/bin/chromium")
SYSTEM_CHROMEDRIVER_PATH = Path("/usr/bin/chromedriver")

REGION_MAP = {
    "경북": [
        "경북",
        "경상북도",
        "포항",
        "경주",
        "김천",
        "안동",
        "구미",
        "영주",
        "영천",
        "상주",
        "문경",
        "경산",
        "군위",
        "의성",
        "청송",
        "영양",
        "영덕",
        "청도",
        "고령",
        "성주",
        "칠곡",
        "예천",
        "봉화",
        "울진",
        "울릉",
    ],
    "경남": [
        "경남",
        "경상남도",
        "창원",
        "진주",
        "통영",
        "사천",
        "김해",
        "밀양",
        "거제",
        "양산",
        "의령",
        "함안",
        "창녕",
        "고성",
        "남해",
        "하동",
        "산청",
        "함양",
        "거창",
        "합천",
    ],
    "대구": [
        "대구",
        "대구광역시",
        "달성군",
        "군위군",
        "중구",
        "동구",
        "서구",
        "남구",
        "북구",
        "수성구",
        "달서구",
    ],
    "부산": [
        "부산",
        "부산광역시",
        "기장군",
        "중구",
        "서구",
        "동구",
        "영도구",
        "부산진구",
        "동래구",
        "남구",
        "북구",
        "해운대구",
        "사하구",
        "금정구",
        "강서구",
        "연제구",
        "수영구",
        "사상구",
    ],
    "울산": [
        "울산",
        "울산광역시",
        "울주군",
        "중구",
        "남구",
        "동구",
        "북구",
    ],
}

TARGET_REGIONS = ["대구", "울산", "부산", "경북", "경남"]

SIGUNGU_PATTERNS = (
    r"(포항시|경주시|김천시|안동시|구미시|영주시|영천시|상주시|문경시|경산시)",
    r"(창원시|진주시|통영시|사천시|김해시|밀양시|거제시|양산시)",
    r"(의성군|청송군|영양군|영덕군|청도군|고령군|성주군|칠곡군|예천군|봉화군|울진군|울릉군)",
    r"(의령군|함안군|창녕군|고성군|남해군|하동군|산청군|함양군|거창군|합천군)",
    r"(달성군|군위군|기장군|울주군)",
    r"(중구|동구|서구|남구|북구|수성구|달서구|영도구|부산진구|동래구|해운대구|사하구|금정구|강서구|연제구|수영구|사상구)",
)

DISASTER_KEYWORDS = (
    ("호우", ("호우",)),
    ("태풍", ("태풍",)),
    ("대설", ("대설", "폭설")),
    ("한파", ("한파",)),
    ("폭염", ("폭염", "무더위")),
    ("건조", ("건조",)),
    ("지진", ("지진",)),
    ("해일", ("지진해일", "해일", "쓰나미")),
    ("황사", ("황사",)),
)

ALERT_LEVEL_KEYWORDS = (
    ("경보", ("경보",)),
    ("주의보", ("주의보",)),
    ("특보", ("특보",)),
)


def extract_sender(title: str | None) -> str | None:
    if title is None or pd.isna(title):
        return None

    match = re.search(r"\[([^\]]+)\]\s*$", str(title).strip())
    if match:
        return match.group(1).strip()
    return None


def detect_region(text: str | None) -> str | None:
    if text is None or pd.isna(text):
        return None

    normalized = str(text).strip()
    for region, keywords in REGION_MAP.items():
        for keyword in keywords:
            if keyword in normalized:
                return region
    return None


def clean_sigg(text: str | None, region: str | None) -> str | None:
    if text is None or pd.isna(text):
        return None

    normalized = str(text).strip()
    if region in {"대구", "울산", "부산"}:
        return normalized
    if region in {"경북", "경남"} and normalized.endswith(("시", "군")):
        return normalized[:-1]
    return normalized


def extract_sigg(title: str | None, sender: str | None, region: str | None) -> str | None:
    candidates: list[str] = []
    if sender:
        candidates.append(str(sender))
    if title:
        candidates.append(str(title))

    for text in candidates:
        for pattern in SIGUNGU_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return clean_sigg(match.group(1), region)

    if sender:
        sender_text = str(sender).strip()
        if sender_text.endswith(("시", "군", "구")):
            return clean_sigg(sender_text, region)
    return region


def extract_disaster_type(title: str | None) -> str:
    if title is None or pd.isna(title):
        return "기타"

    text = str(title)
    for disaster_type, keywords in DISASTER_KEYWORDS:
        for keyword in keywords:
            if keyword in text:
                return disaster_type
    return "기타"


def extract_alert_level(title: str | None) -> str:
    if title is None or pd.isna(title):
        return "없음"

    text = str(title)
    for level, keywords in ALERT_LEVEL_KEYWORDS:
        for keyword in keywords:
            if keyword in text:
                return level
    return "없음"


def extract_datetime(text: str | None) -> str | None:
    if text is None or pd.isna(text):
        return None
    return str(text).strip()


def crawl_one_page(driver, wait) -> pd.DataFrame:
    rows_data: list[dict[str, str | None]] = []

    wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
    time.sleep(2)

    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    for row in rows:
        cols = row.find_elements(By.TAG_NAME, "td")
        if len(cols) < 3:
            continue

        number = cols[0].text.strip()
        title = cols[1].text.strip()
        published_at = cols[2].text.strip()

        sender = extract_sender(title)
        region = detect_region(sender) or detect_region(title)
        if region not in TARGET_REGIONS:
            continue

        rows_data.append(
            {
                "발표시간": extract_datetime(published_at),
                "지역": region,
                "시군구": extract_sigg(title, sender, region),
                "재난종류": extract_disaster_type(title),
                "특보등급": extract_alert_level(title),
                "내용": title,
                "발송기관": sender,
                "번호": number,
            }
        )

    return pd.DataFrame(rows_data)


def _running_on_linux() -> bool:
    return sys.platform.startswith("linux")


def _resolve_system_path(path: Path) -> Path | None:
    if not _running_on_linux():
        return None
    if path.exists():
        return path
    return None


def _build_chrome_options(*, headless: bool = True) -> Options:
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1600,1200")

    binary_path = _resolve_system_path(SYSTEM_CHROME_BINARY_PATH)
    if binary_path is not None:
        options.binary_location = str(binary_path)
    return options


def _build_chrome_driver_kwargs(*, headless: bool = True) -> dict[str, object]:
    driver_kwargs: dict[str, object] = {"options": _build_chrome_options(headless=headless)}

    driver_path = _resolve_system_path(SYSTEM_CHROMEDRIVER_PATH)
    if driver_path is not None:
        driver_kwargs["service"] = Service(executable_path=str(driver_path))
    return driver_kwargs


def crawl_disaster_notifications(*, headless: bool = True, wait_seconds: int = 15) -> pd.DataFrame:
    driver = webdriver.Chrome(**_build_chrome_driver_kwargs(headless=headless))
    try:
        wait = WebDriverWait(driver, wait_seconds)
        driver.get(BASE_URL)
        return crawl_one_page(driver, wait)
    finally:
        driver.quit()


if __name__ == "__main__":
    dataframe = crawl_disaster_notifications(headless=False)
    print(f"수집 건수: {len(dataframe)}")
