#!/usr/bin/env bash
# service-tests 게이트 — **서비스 pytest 묶음이 게이트 안에서 돈다.**
#
# 왜 생겼나 (2026-09-03 코드리뷰 #6):
#   CI 가 core-api(51파일)·ai-service(13)·viz-render(28) 의 pytest 를 **어느 잡에서도 돌리지
#   않았고**, pipeline-worker 만 `stage2 and not e2e` 부분 집합을 돌았다. 서비스 측 시험 함수
#   1102 중 **871 이 CI 에서 한 번도 실행되지 않았다**(`grep -rn pytest .github/` = 0).
#   시험이 레포에 있는 것과 CI 가 그것을 판정하는 것은 다른 사실이다 — 아무도 돌리지 않는
#   시험은 「원래 그렇다」로 굳는다(`frontend-test` 가 닫은 것과 같은 계열).
#
# 무엇을 강제하나:
#   서비스가 선언한 pytest 설정(`services/<단위>/pyproject.toml` 의 `[tool.pytest.ini_options]`)
#   그대로, 게이트가 넘긴 **표식 선택자**로 돈다. 게이트가 자기 사본 설정을 만들지 않는다 —
#   만드는 순간 「게이트는 green 인데 실제 시험은 red」가 열린다.
#
# 세 상태 · fail-closed (CLAUDE.md §4 green-by-skip 금지):
#   · 인자 부족(단위·선택자 중 하나라도 빔)  → red. **필수 인자 없이 대상 0건인 채 통과**가
#     이 레포의 대표 실패형이다. 「전부 돈다」를 뜻하려면 선택자를 말로 적는다(`not e2e` 등)
#   · 단위 자리·`tests/` 부재                 → red (대상 0건은 통과가 아니다)
#   · venv·파이썬 부재                        → **red(준비 · 78)**. skip 이 아니다
#   · 일회용 DB 를 못 띄움(core-api)          → red(준비 · 78)
#   · ⭑ **수집 0건**                          → red. 통과 0·실패 0 은 「전부 통과」가 아니라
#                                               「아무것도 검사하지 않았다」다
#   · ⭑ **실행 0건(전부 skip)**               → red. 수집만 하고 안 돈 것도 판정이 아니다
#   · failed·errors 1건 이상                  → red
#   · pytest 비영 종료                        → red
#   skipped·deselected 는 **막지 않는다 — 대신 요약줄에 건수로 드러난다.** 감춘 건너뜀이
#   green-by-skip 이지, 드러낸 건너뜀은 판정의 일부다(세 상태의 가운데 칸).
#
# 사용:  gates/tools/service-tests.sh <단위> <표식 선택자>
#   예:  gates/tools/service-tests.sh viz-render "not e2e and not perf"
#
# 환경변수 (전부 selftest 전용 주입구다 — 실운전에서는 쓰지 않는다)
#   COLAB_SERVICE_TESTS_DIR   단위 자리를 갈아끼운다(픽스처 트리)
#   COLAB_SERVICE_TESTS_PY    파이썬 실행 파일을 갈아끼운다
#   COLAB_PG_FORCE_UNAVAILABLE=1  일회용 postgres 부재 주입 (`_pg.sh`)
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
SERVICE="${1:-}"
SELECT="${2:-}"
GATE="service-tests${SERVICE:+-$SERVICE}"

red() { echo "::error::$GATE red — $*"; exit 1; }

# 준비 실패(readiness)는 판정 실패와 **가른다** — 표식·종료코드는 DB 게이트의 것을 그대로 쓴다.
# 두 벌로 두면 한쪽이 언젠가 다른 말을 한다 (`rls-effect.sh` 와 같은 배치).
# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/_pg.sh"
ready_red() { pg_readiness_report "$GATE" "$1" "$2" "$3" "$4"; exit "$PG_READINESS_EXIT"; }

# ── ⑴ 인자 — 없는 인자를 관대한 기본값으로 채우지 않는다 ─────────────────────
[ -n "$SERVICE" ] || red "단위 이름이 없다. 사용: gates/tools/service-tests.sh <단위> <표식 선택자>.
   인자 없이 도는 시험 게이트는 대상 0건을 통과로 세는 자리가 된다 (CLAUDE.md §4)."
[ -n "$SELECT" ] || red "표식 선택자가 없다. 사용: gates/tools/service-tests.sh $SERVICE <표식 선택자>.
   **빈 선택자를 「전부」로 읽지 않는다** — 뜻하는 바를 말로 적는다(예: \"not e2e\").
   기본값이 관대한 쪽으로 떨어지는 것이 이 레포의 대표 실패형이다 (CLAUDE.md §4)."

SVC="${COLAB_SERVICE_TESTS_DIR:-$REPO_ROOT/services/$SERVICE}"
[ -d "$SVC" ]         || red "단위 자리가 없다: ${SVC#"$REPO_ROOT"/}. 대상 0건은 통과가 아니다."
[ -d "$SVC/tests" ]   || red "시험 자리가 없다: ${SVC#"$REPO_ROOT"/}/tests. 대상 0건은 통과가 아니다."

# ── ⑵ 준비 — 없으면 red(준비). 「못 돌았음」을 「통과」로 세지 않는다 ─────────
PY="${COLAB_SERVICE_TESTS_PY:-$SVC/.venv/bin/python}"
[ -x "$PY" ] || ready_red "$SERVICE 파이썬 실행 파일(${PY#"$REPO_ROOT"/})" "대기 없음" "0초" \
  "venv 가 이 체크아웃에 없다. services/$SERVICE 에서 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt [-r requirements-dev.txt] && .venv/bin/pip install -e .' 를 돌린 뒤 재실행한다."

TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" service-tests-XXXXXX)"
XML="$TMP/junit.xml"
OUT="$TMP/pytest.out"
SVC_CLEAN() { rm -rf "$TMP"; pg_cleanup; }
trap SVC_CLEAN EXIT INT TERM

# ── ⑶ core-api 는 일회용 Postgres 를 스스로 세운다 ───────────────────────────
# 재료는 A2 가 남긴 것을 그대로 쓴다(`services/core-api/tests/fixtures/setup-db.sh`) — 게이트가
# 자기 시드를 따로 들면 시드가 두 벌이 되어 갈라진다. 컨테이너는 `_pg.sh` 가 만든다:
# 이름은 staging 접두와 겹치지 않고 · **포트를 하나도 publish 하지 않으며** · PGDATA 는 tmpfs ·
# `--rm` ＋ trap 으로 반드시 지운다. ⚠ 접속 문자열은 **어디에도 출력하지 않는다.**
PYENV=()
case "$SERVICE" in
  core-api)
    SETUP="$SVC/tests/fixtures/setup-db.sh"
    [ -f "$SETUP" ] || red "일회용 DB 구성 재료가 없다: ${SETUP#"$REPO_ROOT"/}."
    pg_start "$GATE" || exit "$PG_READINESS_EXIT"
    if ! docker exec "$PGC" createdb -U postgres colab_platform >"$TMP/db.err" 2>&1; then
      ready_red "일회용 postgres 안의 DB 생성(createdb colab_platform)" "대기 없음" "0초" \
        "$(tr '\n' ' ' < "$TMP/db.err" | cut -c1-300)"
    fi
    DB_URL="$(CONTAINER="$PGC" DB=colab_platform bash "$SETUP" 2>"$TMP/db.err")"
    if [ -z "$DB_URL" ]; then
      DB_ERR="$(tr '\n' ' ' < "$TMP/db.err" | cut -c1-400)"
      if pg_is_readiness_error "$DB_ERR"; then
        ready_red "일회용 postgres 에 스키마·롤·시드 적용(tests/fixtures/setup-db.sh)" \
          "대기 없음" "0초" "$DB_ERR"
      fi
      red "선언 스키마·앱 롤·시드를 적용하지 못했다. 적용되지 않는 스키마는 검사할 수 없다:
     $DB_ERR"
    fi
    echo "# 일회용 postgres 준비 완료 — 스키마·앱 롤·시드 적용(접속 문자열은 출력하지 않는다)"
    PYENV=(
      "COLAB_CORE_TEST_DATABASE_URL=$DB_URL"
      "COLAB_CORE_TEST_SUBJECTS_FILE=$SVC/tests/fixtures/subjects.json"
    )
    ;;
esac

# ── ⑷ 판정 — 서비스가 선언한 설정 그대로 ─────────────────────────────────────
# `--strict-markers` — 등록되지 않은 표식은 red 다. 표식이 오타나면 선택자가 조용히 빗나가고,
#   그 순간 「고른 것이 0건인데 green」이 열린다.
# `-p no:cacheprovider` — 레포에 `.pytest_cache` 를 떨어뜨리지 않는다(스캔 게이트의 대상이 된다).
# `junit_family=xunit1` — 이 레포의 다른 junit 게이트(`render-latency`·`e2e-format-coverage`)와
#   같은 판이다. xunit2 는 `record_property` 를 버리고 그때마다 케이스당 경고를 찍는다.
( cd "$SVC" && env "${PYENV[@]+"${PYENV[@]}"}" "$PY" -m pytest -q --strict-markers \
    -p no:cacheprovider -m "$SELECT" -o junit_family=xunit1 --junitxml="$XML" ) >"$OUT" 2>&1
rc=$?
tail -c 4000 "$OUT" | sed 's/^/   /'

python3 - "$XML" "$rc" "$OUT" "$GATE" "$SELECT" <<'PY'
import re
import sys
import xml.etree.ElementTree as ET

xml, rc, out_path, gate, select = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5]

try:
    raw = open(out_path, encoding="utf-8", errors="replace").read()
except OSError:
    raw = ""

try:
    root = ET.parse(xml).getroot()
except Exception as exc:  # 리포트 자체가 없으면 red — 판정 근거가 없다
    print(f"::error::{gate} red — junit 리포트를 읽지 못했다: {exc}")
    print("   시험이 아예 시작되지 못했을 수 있다. 위 pytest 출력이 사유다.")
    sys.exit(1)

suites = [root] if root.tag == "testsuite" else list(root)
tot = sum(int(s.get("tests", 0)) for s in suites)
skip = sum(int(s.get("skipped", 0)) for s in suites)
fail = sum(int(s.get("failures", 0)) for s in suites)
err = sum(int(s.get("errors", 0)) for s in suites)
secs = sum(float(s.get("time", 0) or 0) for s in suites)
ran = tot - skip

# deselected 는 junit 에 없다 — pytest 요약줄에서 읽는다. **못 읽으면 「0」이라고 말하지 않는다.**
m = re.search(r"(\d+)\s+deselected", raw)
desel = m.group(1) if m else "미상"

print(f"{gate} — 선택자 «{select}» · 수집 {tot} · 실행 {ran} · skipped {skip} · "
      f"deselected {desel} · failed {fail} · errors {err} · 소요 {secs:.1f}초")

bad = False
if tot == 0:
    print(f"::error::{gate} red — **수집된 시험이 0건이다.** 통과 0·실패 0 은 「전부 통과」가 아니라\n"
          "   「아무것도 검사하지 않았다」다 (CLAUDE.md §4 green-by-skip). 선택자가 빗나갔거나\n"
          "   시험 자리가 비었다.")
    bad = True
elif ran == 0:
    print(f"::error::{gate} red — 수집 {tot}건이 **전부 skip 됐다(실행 0건).** 수집만 하고 돌지 않은 것은\n"
          "   판정이 아니다 (CLAUDE.md §4).")
    bad = True
if fail or err:
    print(f"::error::{gate} red — failed {fail} · errors {err}. 위 pytest 출력에 실패한 케이스 이름이 있다.")
    bad = True
if rc != 0 and not bad:
    print(f"::error::{gate} red — pytest 종료 코드 {rc}. 계수로는 설명되지 않는 실패다(수집 오류·플러그인 등).")
    bad = True
if bad:
    sys.exit(1)
print(f"{gate} green — 실행 {ran}건 전부 통과 (skipped {skip} · deselected {desel} 은 요약줄에 드러나 있다).")
PY
exit $?
