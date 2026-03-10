"""pytest 공통 설정과 모듈 로더, 샘플 전처리 데이터 fixture."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("PROJECT_DASHBOARD_IMPORT_ONLY", "1")


def load_project_module(relative_path: str, module_name: str):
    """상대 경로의 프로젝트 파일을 import 전용 모드로 로드한다."""

    if module_name in sys.modules:
        return sys.modules[module_name]

    file_path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {file_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def home_module():
    return load_project_module("app.py", "project_dashboard_home")


@pytest.fixture(scope="session")
def about_page_module():
    return load_project_module("pages/1_About.py", "project_dashboard_about")


@pytest.fixture(scope="session")
def recommendation_page_module():
    return load_project_module("pages/2_대피소_추천.py", "project_dashboard_recommendation")


@pytest.fixture(scope="session")
def flow_page_module():
    return load_project_module("pages/3_작동_설명.py", "project_dashboard_flow")


@pytest.fixture(scope="session")
def realtime_page_module():
    return load_project_module("pages/4_실시간_준비.py", "project_dashboard_realtime")


@pytest.fixture(scope="session")
def projects_page_module():
    return load_project_module("pages/5_Projects.py", "project_dashboard_projects")


@pytest.fixture(scope="session")
def analysis_page_module():
    return load_project_module("pages/6_Data_Analysis.py", "project_dashboard_analysis")


@pytest.fixture(scope="session")
def learning_page_module():
    return load_project_module("pages/7_Learning_Log.py", "project_dashboard_learning")


@pytest.fixture()
def sample_preprocessing_dir(tmp_path: Path) -> Path:
    """테스트용 최소 전처리 데이터 폴더를 만든다."""

    base = tmp_path / "preprocessing_data"
    preprocessing = base / "preprocessing"
    preprocessing.mkdir(parents=True)

    pd.DataFrame(
        [
            {
                "발표시간": "2026-03-06 12:00",
                "지역": "경북",
                "시군구": "포항시",
                "재난종류": "풍랑",
                "특보등급": "주의보",
                "해당지역": "포항 앞바다",
            },
            {
                "발표시간": "2026-03-06 13:00",
                "지역": "경북",
                "시군구": "포항시",
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

    pd.DataFrame(
        [
            {
                "대피소명": "포항 체육센터",
                "주소": "경북 포항시 북구 1",
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
                "주소": "경북 포항시 북구 2",
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
                "주소": "경북 안동시 풍천면 1",
                "대피소유형": "무더위쉼터",
                "위도": 36.5685,
                "경도": 128.7294,
                "시도": "경북",
                "시군구": "안동시",
                "지역": "경북 안동시",
                "수용인원": 70,
            },
            {
                "대피소명": "부산 통합대피소",
                "주소": "부산 동구 1",
                "대피소유형": "한파쉼터",
                "위도": 35.538,
                "경도": 129.312,
                "시도": "부산",
                "시군구": "동구",
                "지역": "부산 동구",
                "수용인원": 80,
            },
        ]
    ).to_csv(preprocessing / "final_shelter_dataset.csv", index=False, encoding="utf-8-sig")

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

    pd.DataFrame(
        [
            {
                "대피소명": "포항 해일대피소",
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

    return base
