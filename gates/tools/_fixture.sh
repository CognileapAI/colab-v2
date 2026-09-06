#!/usr/bin/env bash
# 셀프테스트가 **픽스처에 위반을 주입하는 자리**를 한 곳에 둔다. source 해서 쓴다.
#
# 왜 생겼나 (2026-09-06):
#   셀프테스트 6개가 `sed -i 'EXPR' FILE` 로 위반을 주입하고 있었다. **GNU 문법이다.**
#   BSD(macOS)의 `sed -i` 는 뒤에 **백업 접미사를 요구**하므로 `'EXPR'` 이 접미사로 먹히고
#   파일 이름이 스크립트로 넘어가 `invalid command code` 로 죽는다. 그런데 아무도 그 종료코드를
#   보지 않았다 —
#
#     sed -i 's/a/b/' "$f"        # ← 죽는다. rc 를 아무도 안 본다
#     expect "위반" red "$GATE"    # ← 픽스처는 **깨끗한 채**다. 게이트는 당연히 green
#
#   ⟹ 「red 를 기대했는데 green 이 나왔다」로 실패한다. 원인은 게이트가 아니라 이 한 줄인데
#   출력은 게이트를 가리킨다. 2026-09-06 실측 — 6개 파일 · 주입 실패 **25건**.
#
#   ⚠ 더 나쁜 쪽은 따로 있다. 기대가 **green** 인 자리에서 주입이 실패하면 **아무 말 없이
#   통과한다.** 검사기가 아무것도 검사하지 않고 통과를 보고하는 것 — 이 레포의 대표 실패형
#   (green-by-skip · `CLAUDE.md §4`)이고, `_expect.sh` 가 종료코드 78 을 두고 막았던 것과
#   **같은 구멍이 주입 단계에 하나 더 있었던** 셈이다.
#
# ── 규율 ──────────────────────────────────────────────────────────────
#   주입은 **성공했거나, 죽는다.** 조용히 넘어가는 갈래를 두지 않는다.
#   · sed 가 0 이 아닌 값을 내면 그 자리에서 죽는다
#   · 바뀐 것이 없으면(대상 문자열 부재) 그것도 죽는다 — 「돌았지만 아무것도 안 했다」가
#     제일 찾기 어려운 모양이다

# ── fx_sed <파일> <sed 표현식>... ────────────────────────────────────
#: 파일을 sed 로 **제자리 수정**한다. `-i` 를 쓰지 않으므로 GNU·BSD 양쪽에서 같다.
#: 표현식 문법은 그 기계의 sed 것이다 — 주소범위·`d`·`s` 는 양쪽이 같지만
#: **치환문의 `\n` 은 GNU 전용**이다. 줄을 늘리려면 `fx_replace` 를 쓴다.
fx_sed() {
  local f="$1"; shift
  local before after e
  before=$(cat "$f") || { echo "fx_sed: 읽지 못한다 — $f" >&2; return 1; }
  for e in "$@"; do
    if ! sed "$e" "$f" > "$f.fx"; then
      rm -f "$f.fx"
      echo "fx_sed: sed 가 거부했다 — $f : $e" >&2
      return 1
    fi
    mv "$f.fx" "$f"
  done
  after=$(cat "$f")
  if [ "$before" = "$after" ]; then
    echo "fx_sed: 파일이 그대로다 — 주입이 안 됐다. $f : $*" >&2
    return 1
  fi
}

# ── fx_replace <파일> <옛 문자열> <새 문자열> ────────────────────────
#: **정규식이 아니라 리터럴**이다. `\n` 은 **양쪽 다** 진짜 줄바꿈이 된다 —
#: 옛 문자열에서만 안 풀면 `^` 를 대신하려던 자리가 조용히 대상 부재가 된다(2026-09-06 실측).
#: 픽스처에 줄을 끼워 넣는 자리(서비스 하나를 더 붙이는 등)가 이것을 쓴다.
#: 첫 한 번만 바꾼다. 대상이 없으면 죽는다.
fx_replace() {
  python3 - "$@" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1])
old, new = (a.replace("\\n", "\n") for a in sys.argv[2:4])
s = p.read_text(encoding="utf-8")
if old not in s:
    sys.exit(f"fx_replace: 대상이 없다 — {p}: {old!r}")
p.write_text(s.replace(old, new, 1), encoding="utf-8")
PY
}
