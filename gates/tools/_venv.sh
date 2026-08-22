#!/usr/bin/env bash
# 경계 게이트용 파이썬 도구 확보. source 해서 쓴다. 성공하면 $GATE_PY 가 인터프리터다.
#
# 원칙 (CLAUDE.md §4): 도구가 없거나 네트워크가 죽어 설치를 못 하면 **skip 이 아니라 red** 다.
# 버전은 gates/requirements.txt 가 고정한다. pip 최신 끌어오기 금지.
ensure_gate_venv() { # $1 = red() 를 부를 게이트 이름 (메시지용)
  local gate="$1"
  # COLAB_GATE_VENV / COLAB_GATE_REQUIREMENTS 는 selftest 전용이다 (도구 부재 케이스 주입).
  local venv="${COLAB_GATE_VENV:-$REPO_ROOT/gates/.venv}"
  local reqs="${COLAB_GATE_REQUIREMENTS:-$REPO_ROOT/gates/requirements.txt}"
  local stamp="$venv/.requirements.sha"
  local want; want="$(sha256sum "$reqs" 2>/dev/null | cut -d' ' -f1)"
  [ -n "$want" ] || { echo "::error::$gate red — 도구 핀 파일이 없다: $reqs"; return 1; }
  GATE_PY="$venv/bin/python"

  if [ ! -x "$GATE_PY" ] || [ "$(cat "$stamp" 2>/dev/null || true)" != "$want" ]; then
    rm -rf "$venv"
    python3 -m venv "$venv" >/dev/null 2>&1 || {
      echo "::error::$gate red — python venv 를 만들지 못했다. 검사를 못 한 것은 통과가 아니다."; return 1; }
    if ! "$venv/bin/pip" install -q --disable-pip-version-check \
          -r "$reqs" >/dev/null 2>&1; then
      echo "::error::$gate red — $reqs 설치 실패 (네트워크/pypi). skip 아님.
   → 온라인에서 'python3 -m venv gates/.venv && gates/.venv/bin/pip install -r gates/requirements.txt' 한 번 돌린 뒤 재실행한다."
      return 1
    fi
    echo "$want" > "$stamp"
  fi
  return 0
}
