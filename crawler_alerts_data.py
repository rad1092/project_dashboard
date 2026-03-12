from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd

from dashboard_data import normalize_sigungu_name

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
(
    PUBLISHED_AT_COLUMN,
    REGION_COLUMN,
    SIGUNGU_COLUMN,
    DISASTER_TYPE_COLUMN,
    ALERT_LEVEL_COLUMN,
    CONTENT_COLUMN,
    SENDER_COLUMN,
    NUMBER_COLUMN,
) = CRAWLED_ALERT_COLUMNS
SIGUNGU_NORMALIZED_COLUMN = "시군구정규화"
DISASTER_GROUP_COLUMN = "재난그룹"
ALERT_KEY_COLUMN = "alert_key"
SUPPORTED_CRAWLED_REGIONS = ["대구", "울산", "부산", "경북", "경남"]
DEFAULT_CRAWLED_ALERTS_PATH = (
    Path(__file__).resolve().parent / "preprocessing_code" / "data" / "disaster_message_realtime.csv"
)
CRAWLING_MODULE_PATH = Path(__file__).resolve().parent / "preprocessing_code" / "crawling.py"
CRAWLING_MODULE_NAME = "project_dashboard_live_crawling_runtime"
DEFAULT_CRAWLING_WAIT_SECONDS = 15
COLUMN_ALIASES = {
    "발표시간": PUBLISHED_AT_COLUMN,
}


def resolve_crawled_alerts_path(path_override: str | Path | None = None) -> Path:
    if path_override is None:
        return DEFAULT_CRAWLED_ALERTS_PATH

    candidate = Path(path_override).expanduser().resolve()
    if candidate.is_dir():
        nested_path = candidate / "preprocessing_code" / "data" / "disaster_message_realtime.csv"
        if nested_path.exists():
            return nested_path

        flat_path = candidate / "disaster_message_realtime.csv"
        if flat_path.exists():
            return flat_path

        return nested_path

    return candidate


def map_crawled_disaster_group(disaster_type: str | None) -> str:
    if disaster_type is None:
        return "기타"

    text = str(disaster_type).strip()
    mapping = {
        "호우": "호우/태풍",
        "태풍": "호우/태풍",
        "호우/태풍": "호우/태풍",
        "강풍": "강풍/풍랑",
        "풍랑": "강풍/풍랑",
        "강풍/풍랑": "강풍/풍랑",
        "폭염": "폭염",
        "한파": "한파",
        "대설": "대설",
        "건조": "건조",
        "지진": "지진",
        "해일": "해일/쓰나미",
        "지진해일": "해일/쓰나미",
        "쓰나미": "해일/쓰나미",
        "해일/쓰나미": "해일/쓰나미",
    }
    return mapping.get(text, "기타")


def build_empty_crawled_alerts_dataframe() -> pd.DataFrame:
    alerts = pd.DataFrame({column: pd.Series(dtype="object") for column in CRAWLED_ALERT_COLUMNS})
    alerts[PUBLISHED_AT_COLUMN] = pd.Series(dtype="datetime64[ns]")
    alerts[SIGUNGU_NORMALIZED_COLUMN] = pd.Series(dtype="object")
    alerts[DISASTER_GROUP_COLUMN] = pd.Series(dtype="object")
    alerts[ALERT_KEY_COLUMN] = pd.Series(dtype="object")
    return alerts


def load_crawling_module():
    if CRAWLING_MODULE_NAME in sys.modules:
        return sys.modules[CRAWLING_MODULE_NAME]

    if not CRAWLING_MODULE_PATH.exists():
        raise FileNotFoundError(f"크롤링 모듈이 없다: {CRAWLING_MODULE_PATH}")

    spec = importlib.util.spec_from_file_location(CRAWLING_MODULE_NAME, CRAWLING_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {CRAWLING_MODULE_PATH}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[CRAWLING_MODULE_NAME] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(CRAWLING_MODULE_NAME, None)
        raise
    return module


def _validate_columns(dataframe: pd.DataFrame, *, source_name: str) -> None:
    missing_columns = [column for column in CRAWLED_ALERT_COLUMNS if column not in dataframe.columns]
    if missing_columns:
        raise ValueError(f"{source_name} 에 필요한 컬럼이 없다: {missing_columns}")


def _coerce_crawled_alert_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    normalized = dataframe.copy()
    rename_map = {
        source_name: target_name
        for source_name, target_name in COLUMN_ALIASES.items()
        if source_name in normalized.columns and target_name not in normalized.columns
    }
    if rename_map:
        normalized = normalized.rename(columns=rename_map)
    return normalized


def _build_alert_key(row: pd.Series) -> str:
    return "|".join(
        [
            str(row.get(NUMBER_COLUMN, "")).strip(),
            str(row.get(PUBLISHED_AT_COLUMN, "")).strip(),
            str(row.get(REGION_COLUMN, "")).strip(),
            str(row.get(SIGUNGU_COLUMN, "")).strip(),
            str(row.get(CONTENT_COLUMN, "")).strip(),
        ]
    )


def _prepare_crawled_alerts_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    alerts = dataframe[CRAWLED_ALERT_COLUMNS].copy()
    alerts[PUBLISHED_AT_COLUMN] = pd.to_datetime(alerts[PUBLISHED_AT_COLUMN], errors="coerce")
    for column in [
        REGION_COLUMN,
        SIGUNGU_COLUMN,
        DISASTER_TYPE_COLUMN,
        ALERT_LEVEL_COLUMN,
        CONTENT_COLUMN,
        SENDER_COLUMN,
        NUMBER_COLUMN,
    ]:
        alerts[column] = alerts[column].fillna("").astype(str).str.strip()

    alerts[SIGUNGU_NORMALIZED_COLUMN] = alerts[SIGUNGU_COLUMN].map(normalize_sigungu_name)
    alerts[DISASTER_GROUP_COLUMN] = alerts[DISASTER_TYPE_COLUMN].map(map_crawled_disaster_group)
    alerts[ALERT_KEY_COLUMN] = alerts.apply(_build_alert_key, axis=1)
    alerts = alerts.dropna(subset=[PUBLISHED_AT_COLUMN]).sort_values(PUBLISHED_AT_COLUMN).reset_index(drop=True)
    return alerts


def _normalize_live_crawled_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataframe.empty and dataframe.columns.empty:
        return build_empty_crawled_alerts_dataframe()[CRAWLED_ALERT_COLUMNS].copy()

    normalized = _coerce_crawled_alert_columns(dataframe)
    _validate_columns(normalized, source_name="preprocessing_code/crawling.py 결과")
    return normalized


def load_crawled_alerts_dataframe_uncached(path_override: str | Path | None = None) -> pd.DataFrame:
    path = resolve_crawled_alerts_path(path_override)
    try:
        dataframe = pd.read_csv(path, encoding="utf-8-sig")
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"크롤링 재난문자 CSV가 없다: {path}") from exc

    normalized = _coerce_crawled_alert_columns(dataframe)
    _validate_columns(normalized, source_name="disaster_message_realtime.csv")
    return _prepare_crawled_alerts_dataframe(normalized)


def load_live_crawled_alerts_dataframe_uncached(*, headless: bool = True) -> pd.DataFrame:
    crawling_module = load_crawling_module()
    options = crawling_module.Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1600,1200")

    driver = None
    try:
        driver = crawling_module.webdriver.Chrome(options=options)
        wait = crawling_module.WebDriverWait(driver, DEFAULT_CRAWLING_WAIT_SECONDS)
        driver.get(crawling_module.BASE_URL)
        dataframe = crawling_module.crawl_one_page(driver, wait)
    except Exception as exc:
        raise RuntimeError(f"실시간 재난문자 크롤링 실행 실패: {exc}") from exc
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass

    if not isinstance(dataframe, pd.DataFrame):
        raise RuntimeError("실시간 재난문자 크롤링 결과가 DataFrame이 아니다.")

    normalized = _normalize_live_crawled_dataframe(dataframe)
    return _prepare_crawled_alerts_dataframe(normalized)


def get_recent_crawled_alerts(
    dataframe: pd.DataFrame,
    sido: str,
    sigungu: str | None = None,
    limit: int = 5,
) -> pd.DataFrame:
    filtered = dataframe[dataframe[REGION_COLUMN] == sido]
    if sigungu:
        filtered = filtered[filtered[SIGUNGU_NORMALIZED_COLUMN] == normalize_sigungu_name(sigungu)]
        if filtered.empty:
            filtered = dataframe[dataframe[REGION_COLUMN] == sido]

    return filtered.sort_values(PUBLISHED_AT_COLUMN, ascending=False).head(limit).reset_index(drop=True)


def select_default_crawled_alert(
    dataframe: pd.DataFrame,
    sido: str,
    sigungu: str | None = None,
) -> dict[str, object] | None:
    recent_alerts = get_recent_crawled_alerts(dataframe, sido=sido, sigungu=sigungu, limit=1)
    if recent_alerts.empty:
        return None

    return recent_alerts.iloc[0].to_dict()
