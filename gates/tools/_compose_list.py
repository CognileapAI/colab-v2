"""`db_boundary.py` 의 **기본** compose 목록을 읽어 낸다 — 셀프테스트 전용.

게이트를 import 하지 않고 원문에서 뽑는다. import 하면 그 순간 `COMPOSES` 가
환경변수(`COLAB_DB_BOUNDARY_COMPOSE`)에 덮여, **정작 재려던 기본값이 사라진다.**
"""
from __future__ import annotations

import pathlib
import re
import sys

src = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
block = src.split("COMPOSES:", 1)[1].split("COMPOSE =", 1)[0]
print("\n".join(sorted(re.findall(r'ROOT / "([^"]+)"', block))))
