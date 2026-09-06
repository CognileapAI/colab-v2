#!/usr/bin/env bash
# 접속 URL 파일 참조 시험 — platform 체인 (`PLAN-SoT §9 〈121〉-㉯`).
#
# `COLAB_PLATFORM_DB_URL_FILE` 이 다섯 규칙대로 도는지 기계가 증명한다.
#   ① `_FILE` 이 있으면 그 파일을 읽는다 — 끝의 공백·개행만 벗긴다
#   ② 없거나 못 읽거나 비었으면 **죽는다** (조용한 폴백 금지)
#   ③ 둘 다 있으면 **죽는다** (두 출처가 갈리면 어느 것이 진실인지 아무도 모른다)
#   ④ 둘 다 없으면 지금과 같다 (빈 값)
#   ⑤ **값을 메시지에 싣지 않는다**
#
# 판독기는 `db/platform/platform_db_url.py` 다. **ai 체인과 공유하지 않는다** —
# 두 체인은 마이그레이션 체인이 갈라져 있다 (`CLAUDE.md §3-3`).
# alembic·DB 는 필요 없다: 판독기만 부른다. 못 돈 시험은 통과가 아니다.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHAIN_DIR="$(cd "$HERE/.." && pwd)"
PY="${COLAB_PYTHON:-python3}"

red() { echo "::error::db-url-file(platform) red — $*"; exit 1; }

command -v "$PY" >/dev/null 2>&1 || red "python 을 찾지 못했다($PY). COLAB_PYTHON 으로 지정한다."
[ -f "$CHAIN_DIR/platform_db_url.py" ] || red "판독기(platform_db_url.py)가 없다."

COLAB_CHAIN_DIR="$CHAIN_DIR" "$PY" - <<'PY' || red "규칙 시험이 실패했다 (위 출력)"
import os
import pathlib
import sys
import tempfile

sys.path.insert(0, os.environ["COLAB_CHAIN_DIR"])
from platform_db_url import resolve_db_url  # noqa: E402

VAR = "COLAB_PLATFORM_DB_URL"
FILE_ENV = VAR + "_FILE"
URL = "postgresql+psycopg://u:p@h:5432/colab_platform"
fails = []


def check(name, ok):
    if not ok:
        fails.append(name)


def dies(env):
    try:
        resolve_db_url(env)
    except RuntimeError as e:
        return str(e)
    return None


with tempfile.TemporaryDirectory() as d:
    good = pathlib.Path(d, "platform.url")
    good.write_text(URL + "  \n\n", encoding="utf-8")
    empty = pathlib.Path(d, "empty.url")
    empty.write_text("\n  \n", encoding="utf-8")
    missing = pathlib.Path(d, "nope.url")
    adir = pathlib.Path(d, "dir.url")
    adir.mkdir()

    check("① 파일에서 읽는다 · 끝만 벗긴다", resolve_db_url({FILE_ENV: str(good)}) == URL)

    m = dies({FILE_ENV: str(missing)})
    check("② 파일이 없으면 죽는다", m is not None and str(missing) in m)
    check("② 파일이 비었으면 죽는다", dies({FILE_ENV: str(empty)}) is not None)
    m = dies({FILE_ENV: str(adir)})
    check("② 못 읽으면 죽는다", m is not None and URL not in m and str(adir) in m)

    m = dies({VAR: URL, FILE_ENV: str(good)})
    check("③ 둘 다 있으면 죽는다", m is not None and FILE_ENV in m)
    check("⑤ 값을 메시지에 싣지 않는다", m is not None and URL not in m)

    check("④ 둘 다 없으면 빈 값", resolve_db_url({}) == "")
    check("④ 환경변수만 있으면 지금과 같다", resolve_db_url({VAR: URL}) == URL)

for f in fails:
    print(f"  · {f}")
sys.exit(1 if fails else 0)
PY

echo "db-url-file(platform): green — 규칙 5항"
