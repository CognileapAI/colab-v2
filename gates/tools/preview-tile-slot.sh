#!/usr/bin/env bash
# preview-tile-slot 게이트 — **지도 타일이 자리에 놓였고, 놓인 것을 다시 쓸 수 있는가.**
#
# 강제하는 것 (완료 정의 축자 ⑵ · 대장 `dev-package/work-items.yaml` `PV-1`):
#   「산출물이 그 자리에 **기록되어 다시 만들지 않고 찾아 쓸 수 있다.**」
# 그리고 정본 `contracts/storage/layout.json` 축자 —
#   「**자리가 있어야 이미 구운 것을 찾아 쓴다.** 자리가 없으면 같은 그림을 매번 다시 굽는다.」
#
# **자리 자체가 기록이다** — 키가 내용 주소라 별도의 표가 없다. 그래서 이 게이트가 보는 것도
# 표가 아니라 **자리**이고, 판정도 「행이 있는가」가 아니라 **「쓸 수 있는가」**다.
#
# 세는 단위 = **자리에 놓인 지도 타일 파일 1건**. 사건으로 세지 않는다 — 재사용이 성립하면
#   사건 여러 건이 타일 하나를 함께 쓰므로 사건 수와 파일 수는 애초에 같지 않다.
#
# 대조 둘:
#   ⑴ **발행됐는데 자리가 비었나** — `preview.cog-built` 가 난 업로드가 있는데 자리에
#      지도 타일이 한 건도 없으면 red. 「파이프라인은 성공했다는데 산출물이 없다」가 그 상태다.
#   ⑵ **자리에 있는데 쓸 수 없나** — 지도 타일 이름을 달고 있으나 COG 층이 아닌 파일.
#      그런 파일은 재사용이 매번 거절되어 **같은 그림을 영원히 다시 굽는다.**
#
# 세 상태 (`CLAUDE.md §4`):
#   · 대상이 있으면                                    → 검사한다
#   · `gates/config/preview-tile-slot.toml` 에 **이름으로** 적혀 있으면 → **건수를 드러낸 채** 넘어간다
#   · 아무 말도 없으면(대상 0건 · 입력 미선언 · 면제 파일 부재) → **red**
#
# ⚠ **관대한 기본값을 두지 않는다.** 자리 경로가 없으면 red 다 — 「자리를 못 봐서 검사를 못 했다」를
#   통과로 세는 것이 이 레포의 대표 실패다.
#
# 환경변수
#   COLAB_APPLIED_DB_URL_PLATFORM  db/platform 이 적용된 DB 접속 URL. 없으면 red (skip 아님)
#   COLAB_PREVIEW_TILE_DIR         미리보기 산출물 루트(지도 타일이 놓이는 자리). 없으면 red
#   COLAB_PREVIEW_TILE_EXEMPT      면제 선언 파일 (기본 gates/config/preview-tile-slot.toml)
#   COLAB_PREVIEW_TILE_PSQL        psql 명령 (기본 psql). selftest 가 일회용 DB 로 바꿔 끼운다
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
EXEMPT_FILE="${COLAB_PREVIEW_TILE_EXEMPT:-$REPO_ROOT/gates/config/preview-tile-slot.toml}"
PSQL="${COLAB_PREVIEW_TILE_PSQL:-psql}"
URL="${COLAB_APPLIED_DB_URL_PLATFORM:-}"
TILE_DIR="${COLAB_PREVIEW_TILE_DIR:-}"

red() { echo "::error::preview-tile-slot red — $*"; exit 1; }

# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/_readiness.sh"
red_undeclared() { readiness_undeclared_input preview-tile-slot "$1" "$2"; exit "$READINESS_EXIT"; }

# ── 1. 면제 선언 — **파일이 없으면 red.** 「선언이 없다」와 「면제가 없다」는 다르다 ────
[ -f "$EXEMPT_FILE" ] || red_undeclared "면제 선언 파일 (${EXEMPT_FILE#"$REPO_ROOT"/})" \
  "이 파일은 면제를 **이름으로** 고정하는 유일한 정본이다. 없으면 무엇이 면제인지 아무도 모른다.
   → 빈 목록(files = [])으로라도 선언한다. 「비어 있다」는 「면제 없음」이라는 **선언**이다."

EXEMPT_NAMES="$(python3 - "$EXEMPT_FILE" <<'PY'
import re, sys
raw = open(sys.argv[1], encoding="utf-8").read()
m = re.search(r"^\s*files\s*=\s*\[(.*?)\]", raw, re.S | re.M)
if m is None:
    print("::MISSING::")
else:
    print("\n".join(x.strip() for x in re.findall(r'"([^"]*)"', m.group(1))))
PY
)" || red "면제 선언을 읽지 못했다."
if [ "$EXEMPT_NAMES" = "::MISSING::" ]; then
  red_undeclared "면제 선언의 files 항목 (${EXEMPT_FILE#"$REPO_ROOT"/})" \
    "항목이 없는 것을 「면제 0건」으로 세지 않는다 — 비어 있어도 **적혀 있어야** 한다."
fi
EXEMPT_COUNT=0
[ -n "$EXEMPT_NAMES" ] && EXEMPT_COUNT="$(printf '%s\n' "$EXEMPT_NAMES" | grep -c .)"

# ── 2. 입력 둘 — 없으면 red ────────────────────────────────────────────────
[ -n "$URL" ] || red_undeclared "COLAB_APPLIED_DB_URL_PLATFORM (db/platform 적용 DB)" \
  "적용 DB 없이 사건 발행 건수를 셀 수 없다. 검사를 못 한 것은 통과가 아니다 (CLAUDE.md §4).
   autometa-loss·schema-diff 와 같은 변수·같은 규율이다."
[ -n "$TILE_DIR" ] || red_undeclared "COLAB_PREVIEW_TILE_DIR (미리보기 산출물 루트)" \
  "자리를 보지 않고 「자리에 놓였다」를 말할 수 없다. 규약은 루트가 둘이라는 사실만 못 박고
   실제 경로는 배포가 준다 (contracts/storage/layout.json previewsRoot).
   → 배포의 미리보기 볼륨 경로를 지정하고 다시 돌린다."
[ -d "$TILE_DIR" ] || red_undeclared "COLAB_PREVIEW_TILE_DIR 가 가리키는 디렉터리 ($TILE_DIR)" \
  "경로가 선언됐으나 그런 디렉터리가 없다. 없는 자리를 「비어 있다」로 읽지 않는다."

# ── 3. 발행 — 사건이 났는가 ────────────────────────────────────────────────
EMITTED="$("$PSQL" "$URL" -At -v ON_ERROR_STOP=1 \
  -c "SELECT count(DISTINCT upload_id) FROM d5_pipeline_event WHERE event_type = 'preview.cog-built';" 2>&1)" \
  || red "적용 DB 에 질의하지 못했다. 검사를 못 한 것은 통과가 아니다.
   psql 이 낸 말: $(printf '%s' "$EMITTED" | tr '\n' ' ' | cut -c1-400)"
EMITTED="$(printf '%s' "$EMITTED" | tail -n 1)"
case "$EMITTED" in
  [0-9]*) : ;;
  *) red "발행 건수가 숫자가 아니다 — 무엇을 셌는지 모르는 채로 통과시키지 않는다: $EMITTED" ;;
esac

# ── 4. 자리 — 놓인 지도 타일과 그 상태 ─────────────────────────────────────
# 지도 타일만 센다. 한 자리에 렌더 산출물과 지도 타일이 함께 살고, 접두사가 둘을 가른다
# (`contracts/storage/layout.json` contentKeys).
mapfile -t TILES < <(find "$TILE_DIR" -type f -name 'tile-*.tif' 2>/dev/null | sort)
TOTAL="${#TILES[@]}"

USABLE=0; EXEMPTED=0; BROKEN=0; BROKEN_NAMES=""
for t in "${TILES[@]}"; do
  name="$(basename "$t")"
  # COG 층인가 — IFD 가 둘 이상이고 본 IFD 가 타일 배치다. 판정은 파이프라인과 같은 규칙이다.
  if python3 - "$t" <<'PY' >/dev/null 2>&1
import struct, sys
p = sys.argv[1]
with open(p, "rb") as f:
    bo = f.read(2)
    if bo not in (b"II", b"MM"):
        raise SystemExit(1)
    e = "<" if bo == b"II" else ">"
    (magic,) = struct.unpack(e + "H", f.read(2))
    if magic == 42:
        big, off_fmt, tag_len = False, e + "I", 12
        (off,) = struct.unpack(e + "I", f.read(4))
    elif magic == 43:
        big = True
        f.read(4)
        (off,) = struct.unpack(e + "Q", f.read(8))
        off_fmt, tag_len = e + "Q", 20
    else:
        raise SystemExit(1)
    ifds, tiled = 0, False
    while off and ifds < 64:
        f.seek(off)
        n = struct.unpack(e + ("Q" if big else "H"), f.read(8 if big else 2))[0]
        entries = f.read(n * tag_len)
        if ifds == 0:
            for i in range(n):
                (tag,) = struct.unpack(e + "H", entries[i * tag_len:i * tag_len + 2])
                if tag == 322:      # TileWidth — 타일 배치다
                    tiled = True
        (off,) = struct.unpack(off_fmt, f.read(8 if big else 4))
        ifds += 1
    # COG = 타일 배치 + 개관(IFD 2 이상)
    raise SystemExit(0 if (tiled and ifds >= 2) else 1)
PY
  then
    USABLE=$((USABLE + 1))
  elif printf '%s\n' "$EXEMPT_NAMES" | grep -Fxq "$name"; then
    EXEMPTED=$((EXEMPTED + 1))
  else
    BROKEN=$((BROKEN + 1)); BROKEN_NAMES="$BROKEN_NAMES $name"
  fi
done

echo "지도 타일 자리 — 발행 업로드 $EMITTED · 자리의 타일 $TOTAL · 쓸 수 있음 $USABLE · 면제 $EXEMPTED (선언 $EXEMPT_COUNT 건) · 못 씀 $BROKEN"
echo "  세는 단위 = 자리에 놓인 지도 타일 파일 · 자리 = $TILE_DIR · 시점 = $(date -Iseconds)"

# ── 5. 판정 — 세 상태 ──────────────────────────────────────────────────────
if [ "$TOTAL" -eq 0 ]; then
  red "자리에 지도 타일 0건. **대상이 없다는 것은 통과가 아니다** — 검사할 것을 한 건도 못 봤다.
   발행 업로드는 $EMITTED 건이다.
   → 워커의 stage 2 선언(COLAB_WORKER_STAGE2=on)과 미리보기 루트(COLAB_WORKER_PREVIEW_DIR)가
     배포에 들어갔는지, 그리고 새 업로드 1건이 실제로 돌았는지 확인한다."
fi
if [ "$EMITTED" -gt 0 ] && [ "$USABLE" -eq 0 ]; then
  red "사건은 $EMITTED 건 발행됐는데 자리에 **쓸 수 있는 타일이 0건**이다.
   「파이프라인은 성공했다는데 산출물이 없다」가 정확히 이 상태다."
fi
if [ "$BROKEN" -gt 0 ]; then
  red "자리에 있으나 지도 타일로 **쓸 수 없는 파일 $BROKEN 건**:$BROKEN_NAMES
   재사용이 매번 거절되어 같은 그림을 영원히 다시 굽는다.
   → 잔재면 지우고, 남겨야 하면 **이름으로** 면제 선언에 적는다: ${EXEMPT_FILE#"$REPO_ROOT"/}"
fi
[ "$EXEMPTED" -gt 0 ] && echo "::warning::preview-tile-slot — 못 쓰는 타일 $EXEMPTED 건이 선언된 채 통과했다."
echo "preview-tile-slot green — 쓸 수 있음 $USABLE / 자리의 타일 $TOTAL · 면제 $EXEMPTED · 발행 업로드 $EMITTED"
exit 0
