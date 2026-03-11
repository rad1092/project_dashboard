import os
import re
import time
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

######################################
# while True 부분 무조건 (1회 실행+ 그때그때 수집)으로 변경 (그러면 1딸깍에 1수집으로 돌아갑니다.)
# 수집이랑 app.py에 넣을거 분리하기
# 같은 문자는 중복 저장되지 않는다.
# 실시간 반영이니 1페이지만 뽑아서 하는거라 한번 수집시 10개 이상(1페이지 초과 분량)이 들어오게 되면 놓칠 가능성이 있음
# 다른 변수와 연결할 때는 특보등급 기준으로 비교하는 것이 좋다고 생각.
# ( @_@/ ) 아자아자 화이팅 ( \@_@ )
######################################


# ===================================
# 1. 기본 설정
# ===================================

# 현재 이 파이썬 파일(.py)이 있는 폴더 경로
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# data 폴더 경로 만들기
DATA_DIR = os.path.join(BASE_DIR, "data")

# data 폴더가 없으면 자동 생성
os.makedirs(DATA_DIR, exist_ok=True)

# 최종 csv 저장 경로
SAVE_PATH = os.path.join(DATA_DIR, "disaster_message_realtime.csv")

# 크롤링할 재난문자 페이지 주소
BASE_URL = "https://www.safetydata.go.kr/disaster-data/disasterNotification"

# 수집 주기: 3분 = 180초
INTERVAL_SECONDS = 180


# ===================================
# 2. 지역 키워드 설정
# ===================================

# 지역 판별용 키워드 사전
# 예를 들어 제목이나 발송기관에 "포항"이 있으면 경북으로 판단
REGION_MAP = {
    "경북": [
        "경북", "경상북도", "포항", "경주", "김천", "안동", "구미", "영주", "영천",
        "상주", "문경", "경산", "군위", "의성", "청송", "영양", "영덕", "청도",
        "고령", "성주", "칠곡", "예천", "봉화", "울진", "울릉"
    ],
    "경남": [
        "경남", "경상남도", "창원", "진주", "통영", "사천", "김해", "밀양", "거제",
        "양산", "의령", "함안", "창녕", "고성", "남해", "하동", "산청", "함양",
        "거창", "합천"
    ],
    "대구": [
        "대구", "대구광역시", "달성군", "군위군",
        "중구", "동구", "서구", "남구", "북구", "수성구", "달서구"
    ],
    "부산": [
        "부산", "부산광역시", "기장군",
        "중구", "서구", "동구", "영도구", "부산진구", "동래구", "남구", "북구",
        "해운대구", "사하구", "금정구", "강서구", "연제구", "수영구", "사상구"
    ],
    "울산": [
        "울산", "울산광역시", "울주군",
        "중구", "남구", "동구", "북구"
    ]
}

# 실제로 저장할 대상 지역
TARGET_REGIONS = ["대구", "울산", "부산", "경북", "경남"]


# ===================================
# 3. 보조 함수
# ===================================

def extract_sender(title: str):
    """
    제목 끝에 있는 [기관명] 추출
    예: "... [포항시]" -> "포항시"
    """
    if pd.isna(title):
        return None

    title = str(title).strip()

    # 제목 끝의 [ ... ] 패턴 찾기
    match = re.search(r"\[([^\]]+)\]\s*$", title)
    if match:
        return match.group(1).strip()

    return None


def detect_region(text: str):
    """
    문자열 안의 키워드를 보고 광역지역 판별
    반환값: 대구 / 울산 / 부산 / 경북 / 경남 / None
    """
    if pd.isna(text):
        return None

    text = str(text).strip()

    # REGION_MAP에 등록된 키워드가 text 안에 포함되어 있는지 확인
    for region, keywords in REGION_MAP.items():
        for keyword in keywords:
            if keyword in text:
                return region

    return None


def clean_sigg(text: str, region: str):
    """
    시군구 이름 정리
    - 대구/울산/부산: 그대로 유지
    - 경북/경남: ~시, ~군이면 마지막 글자 제거
      예) 포항시 -> 포항 / 울진군 -> 울진
    """
    if pd.isna(text) or text is None:
        return None

    text = str(text).strip()

    # 광역시 지역은 원래 이름 그대로 사용
    if region in ["대구", "울산", "부산"]:
        return text

    # 경북/경남은 끝 글자 시/군 제거
    if region in ["경북", "경남"]:
        if text.endswith("시"):
            return text[:-1]
        elif text.endswith("군"):
            return text[:-1]
        return text

    return text


def extract_sigg(title: str, sender: str, region: str):
    """
    시군구 추출
    우선순위:
    1) 발송기관(sender)에서 찾기
    2) 제목(title)에서 찾기
    3) 못 찾으면 광역지역명(region)으로 대체
    """
    candidates = []

    # 먼저 발송기관 후보 추가
    if sender:
        candidates.append(sender)

    # 다음으로 제목 후보 추가
    if title:
        candidates.append(title)

    # 시군구 패턴 목록
    sigg_patterns = [
        r"(포항시|경주시|김천시|안동시|구미시|영주시|영천시|상주시|문경시|경산시)",
        r"(창원시|진주시|통영시|사천시|김해시|밀양시|거제시|양산시)",
        r"(의성군|청송군|영양군|영덕군|청도군|고령군|성주군|칠곡군|예천군|봉화군|울진군|울릉군)",
        r"(의령군|함안군|창녕군|고성군|남해군|하동군|산청군|함양군|거창군|합천군)",
        r"(달성군|군위군|기장군|울주군)",
        r"(중구|동구|서구|남구|북구|수성구|달서구|영도구|부산진구|동래구|해운대구|사하구|금정구|강서구|연제구|수영구|사상구)"
    ]

    # 발송기관 -> 제목 순서로 시군구 찾기
    for text in candidates:
        for pattern in sigg_patterns:
            match = re.search(pattern, text)
            if match:
                return clean_sigg(match.group(1), region)

    # 혹시 발송기관이 그냥 "포항시", "울진군"처럼 끝나는 경우 처리
    if sender:
        sender = sender.strip()
        if sender.endswith(("시", "군", "구")):
            return clean_sigg(sender, region)

    # 아무것도 못 찾으면 광역지역명 반환
    return region


def extract_disaster_type(title: str):
    """
    제목에서 재난종류 추출
    예: 호우, 강풍, 태풍, 지진 등
    """
    if pd.isna(title):
        return "기타"

    text = str(title)

    # 재난종류별 키워드 목록
    disaster_keywords = [
        ("호우", ["호우"]),
        ("태풍", ["태풍"]),
        ("대설", ["대설", "폭설"]),
        ("한파", ["한파"]),
        ("폭염", ["폭염", "무더위"]),
        ("건조", ["건조"]),
        ("지진", ["지진"]),
        ("해일", ["지진해일", "해일", "쓰나미"]),
        ("황사", ["황사"])
    ]

    # 제목 안에 해당 키워드가 있으면 재난종류 반환
    for disaster_type, keywords in disaster_keywords:
        for keyword in keywords:
            if keyword in text:
                return disaster_type

    return "기타"


def extract_alert_level(title: str):
    """
    제목에서 특보등급 추출
    예: 경보 / 주의보 / 특보 / 없음
    """
    if pd.isna(title):
        return "없음"

    text = str(title)

    # 특보등급 키워드 목록
    level_keywords = [
        ("경보", ["경보"]),
        ("주의보", ["주의보"]),
        ("특보", ["특보"])
    ]

    # 제목 안에 해당 단어가 있으면 등급 반환
    for level, keywords in level_keywords:
        for keyword in keywords:
            if keyword in text:
                return level

    return "없음"


def extract_datetime(text: str):
    """
    발표시간 문자열 정리
    현재는 공백만 제거하고 그대로 반환
    """
    if pd.isna(text):
        return None

    text = str(text).strip()
    return text


def build_unique_key(row):
    """
    중복 제거용 고유키 생성
    기준:
    발표시간 + 지역 + 시군구 + 내용

    같은 문자가 반복 수집되더라도
    이 값이 같으면 같은 데이터로 보고 중복 제거
    """
    return (
        str(row.get("발표시간", "")).strip() + "|" +
        str(row.get("지역", "")).strip() + "|" +
        str(row.get("시군구", "")).strip() + "|" +
        str(row.get("내용", "")).strip()
    )


# ===================================
# 4. 1페이지만 수집하는 함수
# ===================================

def crawl_one_page(driver, wait):
    """
    현재 열린 페이지(1페이지)에서 표 데이터를 읽어서
    원하는 지역만 추출 후 DataFrame으로 반환
    """
    rows_data = []

    # 테이블이 화면에 나타날 때까지 대기
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))

    # 페이지 렌더링 안정화를 위해 잠깐 대기
    time.sleep(2)

    # 표 본문 안의 모든 행(tr) 가져오기
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    print(f"현재 페이지 행 수: {len(rows)}")

    # 각 행을 하나씩 처리
    for row in rows:
        cols = row.find_elements(By.TAG_NAME, "td")

        # 보통 [번호, 제목, 등록일] 3개 이상이 있어야 정상 행
        if len(cols) < 3:
            continue

        # 각 칼럼 값 추출
        no = cols[0].text.strip()
        title = cols[1].text.strip()
        created_at = cols[2].text.strip()

        # 제목 끝의 [기관명] 추출
        sender = extract_sender(title)

        # 지역 판별: 발송기관 우선, 없으면 제목으로 판별
        region = detect_region(sender)
        if region is None:
            region = detect_region(title)

        # 대상 지역이 아니면 건너뜀
        if region not in TARGET_REGIONS:
            continue

        # 세부 정보 추출
        sigg = extract_sigg(title, sender, region)
        disaster_type = extract_disaster_type(title)
        alert_level = extract_alert_level(title)
        발표시간 = extract_datetime(created_at)

        # 한 행의 데이터를 딕셔너리 형태로 저장
        rows_data.append({
            "발표시간": 발표시간,
            "지역": region,
            "시군구": sigg,
            "재난종류": disaster_type,
            "특보등급": alert_level,
            "내용": title,
            "발송기관": sender,
            "번호": no
        })

    # 리스트를 DataFrame으로 변환해서 반환
    return pd.DataFrame(rows_data)


# ===================================
# 5. 기존 파일 불러오기
# ===================================

def load_existing_data():
    """
    기존에 저장된 csv 파일이 있으면 불러오고,
    없으면 빈 DataFrame 반환
    """
    if os.path.exists(SAVE_PATH):
        try:
            df = pd.read_csv(SAVE_PATH, encoding="utf-8-sig")
            return df
        except Exception as e:
            print("기존 CSV 읽기 실패:", e)
            return pd.DataFrame()
    else:
        return pd.DataFrame()


# ===================================
# 6. 저장 전 중복 제거
# ===================================

def merge_and_deduplicate(old_df, new_df):
    """
    기존 데이터(old_df)와 새 데이터(new_df)를 합친 뒤
    unique_key 기준으로 중복 제거
    """
    # 기존 데이터가 없으면 새 데이터만 사용
    if old_df is None or len(old_df) == 0:
        merged = new_df.copy()
    else:
        # 기존 + 신규 데이터 합치기
        merged = pd.concat([old_df, new_df], ignore_index=True)

    # 데이터가 하나도 없으면 그대로 반환
    if len(merged) == 0:
        return merged

    # 중복 제거용 키 생성
    merged["unique_key"] = merged.apply(build_unique_key, axis=1)

    # unique_key가 같은 행 제거
    merged = merged.drop_duplicates(subset=["unique_key"]).reset_index(drop=True)

    # 최종 저장 전 보조 컬럼 제거
    merged = merged.drop(columns=["unique_key"], errors="ignore")

    # 최종 저장할 칼럼 순서 지정
    final_cols = ["발표시간", "지역", "시군구", "재난종류", "특보등급", "내용", "발송기관", "번호"]

    # 혹시 없는 칼럼이 있으면 빈값(None)으로 생성
    for col in final_cols:
        if col not in merged.columns:
            merged[col] = None

    # 칼럼 순서 맞추기
    merged = merged[final_cols]

    return merged

# ===================================
# 7. 메인 루프
# ===================================

def main():
    """
    전체 실행 함수
    1) 크롬 실행
    2) 사이트 접속
    3) 1페이지 수집
    4) 기존 csv와 합치기
    5) 중복 제거 후 저장
    6) 3분 대기
    7) 반복
    """
    options = Options()

    # 크롬 창을 띄우고 실행
    # 창 없이 돌리고 싶으면 아래 headless 주석 해제
    # options.add_argument("--headless=new")

    # 창 최대화
    options.add_argument("--start-maximized")

    # 크롬 실행
    driver = webdriver.Chrome(options=options)

    # 특정 요소가 뜰 때까지 최대 15초 기다리기 위한 객체
    wait = WebDriverWait(driver, 15)

    try:
        # 무한 반복
        while True:
            print("\n" + "=" * 50)
            print("재난문자 수집 시작")

            try:
                # 재난문자 페이지 접속
                driver.get(BASE_URL)

                # 현재 1페이지 데이터 수집
                new_df = crawl_one_page(driver, wait)
                print(f"이번 주기 신규 수집 건수(필터 후): {len(new_df)}")

                # 기존 csv 불러오기
                old_df = load_existing_data()

                # 기존 데이터 + 신규 데이터 합치고 중복 제거
                total_df = merge_and_deduplicate(old_df, new_df)

                # 최종 csv 저장
                total_df.to_csv(SAVE_PATH, index=False, encoding="utf-8-sig")

                print(f"누적 저장 건수: {len(total_df)}")
                print(f"저장 경로: {SAVE_PATH}")

            except Exception as e:
                # 수집 도중 에러가 나도 프로그램이 바로 종료되지 않도록 처리
                print("수집 중 오류 발생:", e)

            # 다음 수집 전 3분 대기
            print(f"{INTERVAL_SECONDS}초 대기 후 다시 수집합니다...")
            time.sleep(INTERVAL_SECONDS)

    finally:
        # 프로그램 종료 시 크롬 닫기
        driver.quit()


# ===================================
# 8. 실행
# ===================================

# 이 파일을 직접 실행했을 때만 main() 실행
if __name__ == "__main__":
    main()