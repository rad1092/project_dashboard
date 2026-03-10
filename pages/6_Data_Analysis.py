"""과거 재난 특보와 대피소 분포를 보는 분석 페이지."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

APP_TITLE = "재난 대피소 추천 워크스페이스"
APP_ICON = "🛟"
PAGE_LABEL = "6 Data Analysis"

ALERT_COLUMNS = ["발표시간", "지역", "시군구", "재난종류", "특보등급", "해당지역"]
SHELTER_COLUMNS = ["대피소명", "주소", "대피소유형", "위도", "경도", "시도", "시군구", "지역", "수용인원"]

DATASET_FILE_MAP = {
    "alerts": Path("preprocessing") / "danger_clean.csv",
    "shelters": Path("preprocessing") / "final_shelter_dataset.csv",
}

RAW_TO_GROUP = {
    "지진": "지진",
    "지진해일": "지진해일/쓰나미",
    "쓰나미": "지진해일/쓰나미",
    "호우": "호우/태풍",
    "태풍": "호우/태풍",
    "강풍": "강풍/풍랑",
    "풍랑": "강풍/풍랑",
    "폭염": "폭염",
    "한파": "한파",
    "대설": "대설",
    "건조": "건조",
}

DEFAULT_DISASTER_OPTIONS = [
    "호우/태풍",
    "강풍/풍랑",
    "폭염",
    "한파",
    "대설",
    "건조",
    "지진",
    "지진해일/쓰나미",
]

ANALYSIS_COLUMNS = ["발표시간", "지역", "시군구", "재난종류", "재난그룹", "특보등급"]
COLOR_SEQUENCE = ["#0f766e", "#1d4ed8", "#f59e0b", "#dc2626", "#0f172a"]
def _maybe_get_secret_data_dir() -> str | None:
    """Streamlit secrets 에 설정된 외부 데이터 경로가 있는지 읽는다."""

    try:
        if "preprocessing_data_dir" in st.secrets:
            return str(st.secrets["preprocessing_data_dir"])
        if "app" in st.secrets and "preprocessing_data_dir" in st.secrets["app"]:
            return str(st.secrets["app"]["preprocessing_data_dir"])
    except Exception:
        return None
    return None


def _get_repo_default_data_dir() -> Path:
    """저장소에 포함된 기본 전처리 데이터 폴더 경로를 반환한다."""

    return Path(__file__).resolve().parents[1] / "preprocessing_data"


def _get_desktop_default_data_dir() -> Path:
    """기존 로컬 실행 호환용 Desktop 기본 경로를 반환한다."""

    return Path.home() / "Desktop" / "preprocessing_data"


def resolve_data_dir(path_override: str | Path | None = None) -> Path:
    """전처리 데이터 폴더 경로를 결정한다."""

    candidates: list[Path] = []
    if path_override is not None:
        candidates.append(Path(path_override))

    env_path = os.environ.get("PREPROCESSING_DATA_DIR")
    if env_path:
        candidates.append(Path(env_path))

    secret_path = _maybe_get_secret_data_dir()
    if secret_path:
        candidates.append(Path(secret_path))

    candidates.append(_get_repo_default_data_dir())
    candidates.append(_get_desktop_default_data_dir())

    checked_paths: list[Path] = []
    for candidate in candidates:
        resolved = candidate.expanduser().resolve()
        checked_paths.append(resolved)
        if resolved.exists():
            return resolved

    searched = "\n".join(f"- {path}" for path in checked_paths)
    raise FileNotFoundError(
        "전처리 데이터 폴더를 찾지 못했다.\n"
        "기본 실행은 저장소 내부 `preprocessing_data` 폴더를 사용한다.\n"
        "다음 경로를 차례대로 확인했다:\n"
        f"{searched}\n"
        "다른 위치를 쓰려면 환경변수 `PREPROCESSING_DATA_DIR` 또는 "
        "`.streamlit/secrets.toml` 의 `preprocessing_data_dir` 를 지정해 달라."
    )


def _read_csv(path: Path) -> pd.DataFrame:
    """UTF-8 기반 전처리 CSV 를 읽는다."""

    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"전처리 데이터 파일이 없다: {path}\n"
            "저장소 기본 데이터(`preprocessing_data/preprocessing/*.csv`)가 모두 있는지 확인하거나 "
            "다른 위치를 쓰려면 `PREPROCESSING_DATA_DIR` 또는 `.streamlit/secrets.toml` 의 "
            "`preprocessing_data_dir` 를 지정해 달라."
        ) from exc


def _validate_columns(dataframe: pd.DataFrame, expected_columns: list[str], label: str) -> None:
    """CSV 에 기대한 컬럼이 모두 있는지 확인한다."""

    missing_columns = [column for column in expected_columns if column not in dataframe.columns]
    if missing_columns:
        raise ValueError(f"{label} CSV 에 필요한 컬럼이 없다: {missing_columns}")


def _prepare_alerts(dataframe: pd.DataFrame) -> pd.DataFrame:
    """재난 특보 DataFrame 을 앱 공통 형식으로 정리한다."""

    _validate_columns(dataframe, ALERT_COLUMNS, "danger_clean.csv")

    alerts = dataframe.copy()
    alerts["발표시간"] = pd.to_datetime(alerts["발표시간"], errors="coerce")
    alerts["지역"] = alerts["지역"].astype(str).str.strip()
    alerts["시군구"] = alerts["시군구"].astype(str).str.strip()
    alerts["재난종류"] = alerts["재난종류"].astype(str).str.strip()
    alerts["특보등급"] = alerts["특보등급"].fillna("미분류").astype(str).str.strip()
    return alerts.dropna(subset=["발표시간"]).sort_values("발표시간").reset_index(drop=True)


def _prepare_shelters(dataframe: pd.DataFrame) -> pd.DataFrame:
    """통합/일반 대피장소 DataFrame 을 분석에서 쓰기 좋게 정리한다."""

    _validate_columns(dataframe, SHELTER_COLUMNS, "final_shelter_dataset.csv")

    shelters = dataframe.copy()
    shelters["위도"] = pd.to_numeric(shelters["위도"], errors="coerce")
    shelters["경도"] = pd.to_numeric(shelters["경도"], errors="coerce")
    shelters["수용인원"] = pd.to_numeric(shelters["수용인원"], errors="coerce")
    shelters["시도"] = shelters["시도"].astype(str).str.strip()
    shelters["시군구"] = shelters["시군구"].astype(str).str.strip()
    shelters["대피소유형"] = shelters["대피소유형"].fillna("미분류").astype(str).str.strip()
    shelters["수용인원_정렬값"] = shelters["수용인원"].fillna(0)
    return shelters.dropna(subset=["위도", "경도"]).reset_index(drop=True)


def load_alerts_dataframe_uncached(path_override: str | Path | None = None) -> pd.DataFrame:
    """전처리 폴더에서 재난 특보 DataFrame 을 읽는다."""

    data_dir = resolve_data_dir(path_override)
    return _prepare_alerts(_read_csv(data_dir / DATASET_FILE_MAP["alerts"]))


@st.cache_data(show_spinner=False)
def load_alerts_dataframe(path_override: str | None = None) -> pd.DataFrame:
    """Streamlit rerun 시 재난 특보 CSV 재로딩을 줄이기 위한 캐시 래퍼."""

    return load_alerts_dataframe_uncached(path_override)


def load_shelters_dataframe_uncached(path_override: str | Path | None = None) -> pd.DataFrame:
    """전처리 폴더에서 통합 대피소 DataFrame 을 읽는다."""

    data_dir = resolve_data_dir(path_override)
    return _prepare_shelters(_read_csv(data_dir / DATASET_FILE_MAP["shelters"]))


@st.cache_data(show_spinner=False)
def load_shelters_dataframe(path_override: str | None = None) -> pd.DataFrame:
    """Streamlit rerun 시 통합 대피소 CSV 재로딩을 줄이기 위한 캐시 래퍼."""

    return load_shelters_dataframe_uncached(path_override)


def classify_disaster_type(disaster_name: str | None) -> str:
    """원본 재난 명칭을 내부 그룹으로 정규화한다."""

    if disaster_name is None:
        return "기타"

    text = str(disaster_name).strip()
    return RAW_TO_GROUP.get(text, text if text in DEFAULT_DISASTER_OPTIONS else "기타")


def load_analysis_dataset(data_dir: str | Path | None = None) -> pd.DataFrame:
    """분석 페이지가 공통으로 사용할 특보 이력 DataFrame 을 반환한다."""

    if data_dir is None:
        alerts_frame = load_alerts_dataframe()
    else:
        alerts_frame = load_alerts_dataframe_uncached(data_dir)

    analysis_frame = alerts_frame.copy()
    analysis_frame["재난그룹"] = analysis_frame["재난종류"].map(classify_disaster_type)
    return analysis_frame[ANALYSIS_COLUMNS].sort_values("발표시간").reset_index(drop=True)


def build_kpis(dataframe: pd.DataFrame) -> dict[str, object]:
    """분석 화면에 필요한 기본 KPI 를 계산한다."""

    if dataframe.empty:
        return {
            "alert_count": 0,
            "disaster_count": 0,
            "region_count": 0,
            "warning_count": 0,
            "latest_period": None,
        }

    return {
        "alert_count": int(len(dataframe)),
        "disaster_count": int(dataframe["재난그룹"].nunique()),
        "region_count": int(dataframe["지역"].nunique()),
        "warning_count": int((dataframe["특보등급"] == "경보").sum()),
        "latest_period": pd.Timestamp(dataframe["발표시간"].max()),
    }


def _build_empty_figure(message: str) -> go.Figure:
    """비어 있는 데이터셋에도 깨지지 않는 안내용 Figure 를 만든다."""

    figure = go.Figure()
    figure.add_annotation(text=message, showarrow=False, font=dict(size=16))
    figure.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(t=40, b=20, l=20, r=20),
    )
    return figure


def build_alert_trend_chart(dataframe: pd.DataFrame) -> go.Figure:
    """일자별 재난 그룹 건수를 선 차트로 만든다."""

    if dataframe.empty:
        return _build_empty_figure("선택한 조건에 맞는 특보 데이터가 없다.")

    summary = (
        dataframe.assign(발표일=dataframe["발표시간"].dt.strftime("%Y-%m-%d"))
        .groupby(["발표일", "재난그룹"], as_index=False)
        .size()
        .rename(columns={"size": "건수"})
    )
    figure = px.line(
        summary,
        x="발표일",
        y="건수",
        color="재난그룹",
        markers=True,
        color_discrete_sequence=COLOR_SEQUENCE,
    )
    figure.update_layout(
        title="일자별 재난 그룹 추이",
        margin=dict(t=60, b=20, l=20, r=20),
        legend_title_text="재난 그룹",
    )
    figure.update_xaxes(title="")
    figure.update_yaxes(title="특보 건수")
    return figure


def build_region_alert_chart(dataframe: pd.DataFrame) -> go.Figure:
    """권역별 특보 건수를 막대 차트로 만든다."""

    if dataframe.empty:
        return _build_empty_figure("선택한 조건에 맞는 권역 데이터가 없다.")

    summary = (
        dataframe.groupby("지역", as_index=False)
        .size()
        .rename(columns={"size": "건수"})
        .sort_values("건수", ascending=False)
    )
    figure = px.bar(
        summary,
        x="지역",
        y="건수",
        color="지역",
        text_auto=True,
        color_discrete_sequence=COLOR_SEQUENCE,
    )
    figure.update_layout(
        title="권역별 특보 건수",
        showlegend=False,
        margin=dict(t=60, b=20, l=20, r=20),
    )
    figure.update_xaxes(title="")
    figure.update_yaxes(title="특보 건수")
    return figure


def build_hazard_share_chart(dataframe: pd.DataFrame) -> go.Figure:
    """재난 종류별 비중을 도넛 차트로 만든다."""

    if dataframe.empty:
        return _build_empty_figure("선택한 조건에 맞는 재난 종류 데이터가 없다.")

    summary = (
        dataframe.groupby("재난종류", as_index=False)
        .size()
        .rename(columns={"size": "건수"})
        .sort_values("건수", ascending=False)
    )
    figure = px.pie(
        summary,
        names="재난종류",
        values="건수",
        hole=0.55,
        color="재난종류",
        color_discrete_sequence=COLOR_SEQUENCE,
    )
    figure.update_layout(
        title="재난 종류 비중",
        margin=dict(t=60, b=20, l=20, r=20),
        legend_title_text="재난 종류",
    )
    return figure


def build_shelter_type_chart(dataframe: pd.DataFrame) -> go.Figure:
    """대피소 유형 분포를 막대 차트로 만든다."""

    if dataframe.empty:
        return _build_empty_figure("선택한 조건에 맞는 대피소 데이터가 없다.")

    summary = (
        dataframe.assign(대피소유형=dataframe["대피소유형"].fillna("미분류"))
        .groupby("대피소유형", as_index=False)
        .size()
        .rename(columns={"size": "건수"})
        .sort_values("건수", ascending=False)
    )
    figure = px.bar(
        summary,
        x="대피소유형",
        y="건수",
        color="대피소유형",
        text_auto=True,
        color_discrete_sequence=COLOR_SEQUENCE,
    )
    figure.update_layout(
        title="대피소 유형 분포",
        showlegend=False,
        margin=dict(t=60, b=20, l=20, r=20),
    )
    figure.update_xaxes(title="")
    figure.update_yaxes(title="대피소 수")
    return figure


def render_page() -> None:
    """분석 페이지를 렌더링한다."""

    st.set_page_config(
        page_title=f"{APP_TITLE} | {PAGE_LABEL}",
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("6 Data Analysis")
    st.write("현재 앱이 참고하는 과거 재난 특보와 대피소 분포를 분석 관점에서 정리한 페이지입니다.")
    st.caption(
        "추천 페이지가 한 지역의 결과를 보여준다면, 이 페이지는 전체 데이터 흐름과 분포를 읽는 데 초점을 둡니다."
    )

    try:
        shelters_frame = load_shelters_dataframe()
        dataframe = load_analysis_dataset()
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.stop()

    st.sidebar.header("분석 필터")
    sidos = sorted(dataframe["지역"].dropna().unique().tolist())
    groups = sorted(dataframe["재난그룹"].dropna().unique().tolist())
    grades = sorted(dataframe["특보등급"].dropna().unique().tolist())

    selected_sidos = st.sidebar.multiselect("시도", options=sidos, default=sidos)
    selected_groups = st.sidebar.multiselect("재난 그룹", options=groups, default=groups)
    selected_grades = st.sidebar.multiselect("특보 등급", options=grades, default=grades)

    filtered = dataframe[
        dataframe["지역"].isin(selected_sidos)
        & dataframe["재난그룹"].isin(selected_groups)
        & dataframe["특보등급"].isin(selected_grades)
    ].copy()

    if filtered.empty:
        st.warning("선택한 조건에 맞는 분석 데이터가 없다. 필터를 조금 넓혀 달라.")
        return

    kpis = build_kpis(filtered)
    metric_columns = st.columns(4)
    metric_columns[0].metric("특보 기록 수", f"{float(kpis['alert_count']):,.0f}")
    metric_columns[1].metric("재난 그룹 수", f"{float(kpis['disaster_count']):,.0f}")
    metric_columns[2].metric("경보 건수", f"{float(kpis['warning_count']):,.0f}")
    metric_columns[3].metric(
        "최근 특보 시각",
        "-"
        if kpis["latest_period"] is None or pd.isna(kpis["latest_period"])
        else pd.Timestamp(kpis["latest_period"]).strftime("%Y-%m-%d %H:%M"),
    )

    regional_shelters = shelters_frame[shelters_frame["시도"].isin(selected_sidos)]

    chart_left, chart_right = st.columns(2, gap="large")
    with chart_left:
        st.plotly_chart(build_alert_trend_chart(filtered), use_container_width=True)
        st.plotly_chart(build_region_alert_chart(filtered), use_container_width=True)
    with chart_right:
        st.plotly_chart(build_hazard_share_chart(filtered), use_container_width=True)
        st.plotly_chart(build_shelter_type_chart(regional_shelters), use_container_width=True)

    st.subheader("상세 특보 데이터")
    display_frame = filtered.copy()
    display_frame["발표시간"] = display_frame["발표시간"].dt.strftime("%Y-%m-%d %H:%M")
    st.dataframe(display_frame, use_container_width=True, hide_index=True)


if os.environ.get("PROJECT_DASHBOARD_IMPORT_ONLY") != "1":
    render_page()
