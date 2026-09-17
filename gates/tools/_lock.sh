#!/usr/bin/env bash
# 도구 설치 구간의 상호배제. source 해서 쓴다.
#
# 왜 필요한가: 게이트를 병렬로 돌리면 여러 프로세스가 같은 gates/.venv · node_modules 를
# 동시에 만들려 들 수 있다. 한쪽이 rm -rf 하는 사이 다른 쪽이 그 안을 읽으면 「도구가 없다」로
# red 가 난다 — 검사 결과가 아니라 배선이 만든 red 다. 잠금은 그것만 막는다.
#
# 잠금 파일은 **레포 밖**(TMPDIR)에 둔다. 레포에 파일을 떨어뜨리면 generated-up-to-date 같은
# 스캔 게이트의 대상이 되어 버린다.
#
# ⭑ ⟨2026-09-18 개정 · ADR-0005 개정 블록⟩ **flock 이 없으면 red(준비 · 78) 다.**
# 종전 정책은 「flock 이 없으면 잠그지 않고 그냥 진행한다 — 여기서 red 를 내면 「도구 없음」을
# 검사 실패로 둔갑시키는 꼴이 된다」였다. 그 걱정은 남는다 — 그래서 **판정 red 가 아니라 준비 red** 다.
# 채택한 규칙 — 「실행기가 아는 사실은 무의미하거나 판정이거나 — 둘 중 하나다」.
# 잠글 수단이 없다는 사실은 무의미하지 않다: 바로 그 상태가 위에 적힌 「배선이 만든 red」를 낳는다.
# 알고도 삼키면, 뒤에 나는 「도구 없음」 red 의 원인이 사후에 귀속되지 않는다.
# ⛔ 면제 변수를 두지 않는다 — `_pg.sh` 의 같은 자리와 같은 이유다(CI 는 전부 `ubuntu-latest` ·
#    개발 호스트는 WSL/util-linux). 없는 호스트가 합류하는 날 3상태 변수를 만든다.
# ⚠ 한 디렉터리가 서로 어긋나는 두 정책을 갖지 않는다 — `_pg.sh` 와 이 파일은 이제 같은 말을 한다.
#
# API — 종전 그대로 **0=잠갔다 / 0 아님=실패**다. 바뀐 것은 실패값(1 → 78)과
# 실패 시 `::gate-readiness-failure::` 표식이 함께 나간다는 것뿐이다. 표식이 있으면 실행기는
# 종료코드와 무관하게 `red(준비)` 로 가른다(`gates/run.sh:787`).
# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/_readiness.sh"
GATE_LOCK_READINESS_EXIT=78

gate_lock_fd() { # $1 = 잠금 이름(경로 등 임의 문자열) → 0=잠갔다 / 78=red(준비)
  local key path gate="${2:-gate-lock}"
  key="$(printf '%s' "$1" | cksum | tr -d ' ')"
  path="${TMPDIR:-/tmp}/colab-gate-lock-$key"
  command -v flock >/dev/null 2>&1 || {
    readiness_env_wait "$gate" "flock 실행 파일(도구 설치 구간의 상호배제 수단)" "대기 없음" "0초" \
      "flock 이 PATH 에 없다. 잠금 없이 설치 구간에 들어가면 병렬 실행에서 한쪽이 「도구 없음」 red 를 내는데, 그건 검사 결과가 아니라 배선이 만든 red 다. 알고도 통과시키지 않는다 — 이 호스트에 util-linux 를 깐다. 대상=$1"
    return "$GATE_LOCK_READINESS_EXIT"; }
  exec 9>"$path" 2>/dev/null || {
    readiness_env_wait "$gate" "잠금 파일 열기($path)" "대기 없음" "0초" \
      "잠금 파일을 쓰기로 열지 못했다(권한·fd 고갈·읽기 전용 TMPDIR). 잠글 대상이 없으면 상호배제가 서지 않는다. 대상=$1"
    return "$GATE_LOCK_READINESS_EXIT"; }
  flock 9 2>/dev/null || {
    readiness_env_wait "$gate" "잠금 획득(flock · $path)" "대기 없음" "0초" \
      "flock 이 잠금을 잡지 못했다. 대상=$1"
    exec 9>&- 2>/dev/null
    return "$GATE_LOCK_READINESS_EXIT"; }
  return 0
}
gate_unlock_fd() { exec 9>&- 2>/dev/null || true; }
