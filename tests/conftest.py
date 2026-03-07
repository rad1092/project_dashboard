"""pytest 공통 테스트 설정.

테스트 실행 시 프로젝트 루트를 import 경로에 추가해
``dashboard`` 패키지와 페이지 보조 모듈을 안정적으로 불러오게 한다.
특히 로컬 실행 위치가 달라져도 테스트가 같은 기준으로 동작하게 만드는 역할이다.
"""

from __future__ import annotations

import sys
from pathlib import Path

# tests 디렉터리 기준 상위 한 단계가 프로젝트 루트다.
ROOT = Path(__file__).resolve().parents[1]

# pytest 실행 위치에 따라 import 경로가 달라질 수 있으므로
# 루트를 sys.path 앞에 넣어 dashboard 패키지를 먼저 찾게 한다.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))