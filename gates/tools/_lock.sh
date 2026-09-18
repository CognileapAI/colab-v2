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

# ── 호스트 뮤텍스 — `serial` 선언을 **프로세스 경계 너머로** 강제한다 ─────────
# ⭑ ⟨2026-09-18 신설 · ADR-0005 개정의 후속 ② · spec `2026-09-18-gate-host-mutex.md`⟩
#
# 왜 위의 `gate_lock_fd` 를 쓰지 않나: 그것은 fd 9 고정이고 상한이 없다(`flock 9` = 무한 대기).
# 게이트 실행 전체를 무한히 잡으면 「기다리는 것」과 「멈춘 것」이 구분되지 않는다. 여기는
# 상한(`flock -w`)과 대기 표식을 갖는다 — 못 얻으면 **red(준비 · 78)** 이지 green 이 아니다.
#
# 무엇을 잡나: `gates/config/parallelism.toml` 이 `serial` 로 선언한 게이트를 실행하는 **부모**
# 프로세스 하나. `parallel` 선언 게이트는 아예 잡지 않는다 — **선언이 곧 면제**이고, 그래서
# 새 면제 변수를 두지 않는다(ADR-0005 개정 「쓸 일 없는 면제 변수는 그 자체가 green-by-skip 통로」).
# ⚠ 따라서 「`serial` 이 잡은 동안 다른 프로세스의 `parallel` 은 돈다」 — 의도된 형태다
#   (spec 우려 #4 ⓐ). `serial` 이 보장하는 것은 **다른 `serial` 과 겹치지 않는다**이지
#   「혼자 돌았다」가 아니다.
#
# 잠금 키 = `TMPDIR` **하나**다. 경합 자원(호스트 CPU·메모리·도커 데몬)이 레포별이 아니므로
# 레포 경로를 키에 넣으면 워크트리마다 잠금이 갈려 실효 한도가 배수로 늘어난다(intent Q4 기각 사유).
# ⛔ 주입구 변수(`COLAB_GATE_MUTEX_DIR` 따위)를 두지 않는다 — 있으면 그것이 곧 워크트리별
#    잠금 분리 통로다. 셀프테스트는 `TMPDIR` 자체를 자기 `mktemp -d` 로 물려 부른다.
#
# 세 실패 갈래는 전부 **기존 보고 경로 하나**(`readiness_env_wait`)로 78 이다 — 새 경로를
# 만들지 않는다: ⑴ `flock` 부재 ⑵ 잠금 디렉터리·파일을 만들 수 없다 ⑶ 상한 초과.
#
# ⚠ 잠금은 fd 로 산다. `gates/run.sh` 의 `case` 는 게이트 본체를 `exec` 로 갈아타는데,
#   `{VAR}>` 로 연 fd 는 **exec 를 건너 살아남는다**(실측 2026-09-18). 그래서 잡은 뒤 갈아타도
#   잠금이 유지되고, 프로세스가 죽으면 커널이 푼다 — 죽은 잠금이 남지 않는다.
GATE_HOST_MUTEX_FD=""
GATE_HOST_MUTEX_PATH=""
GATE_HOST_MUTEX_WAITED=0

gate_host_mutex_path() { printf '%s/colab-v2-gate-host-mutex/host' "${TMPDIR:-/tmp}"; }

gate_host_mutex_acquire() { # $1=게이트 이름 → 0=잡았다 / 78=red(준비)
  local gate="${1:-gate}" wait_s="${COLAB_GATE_MUTEX_WAIT:-900}"
  local path dir started now
  path="$(gate_host_mutex_path)"; dir="$(dirname "$path")"
  GATE_HOST_MUTEX_WAITED=0
  # 상한은 선례 `COLAB_PG_SLOT_WAIT`(900) 를 따른다. 잠금 단위가 **게이트 1건**이므로
  # 최장 대기는 상대 레인의 `serial` 게이트 **1건**이다(직전 전수 67건 총 9분 52초).
  [[ "$wait_s" =~ ^[0-9]+$ ]] || wait_s=900
  # ⑴ 잠글 **수단**이 없다. 아는 사실이므로 판정이다 — 면제 변수는 두지 않는다.
  command -v flock >/dev/null 2>&1 || {
    readiness_env_wait "$gate" "호스트 뮤텍스($path)" "${wait_s}초" "0초" \
      "flock 이 PATH 에 없다. 잠글 수단이 없으면 serial 선언이 프로세스 경계에서 사라지는데, 그 사실을 알고도 통과시키면 뒤에 부하로 나는 red 를 게이트 결함으로 오인하게 된다. 이 호스트에 util-linux 를 깐다."
    return "$GATE_LOCK_READINESS_EXIT"; }
  # ⑵ 잠글 **대상**을 둘 자리가 없다 / 열 수 없다.
  mkdir -p "$dir" 2>/dev/null || {
    readiness_env_wait "$gate" "호스트 뮤텍스($path)" "${wait_s}초" "0초" \
      "잠금 디렉터리를 만들지 못했다(권한·읽기 전용 TMPDIR·같은 이름의 파일). 잠글 자리가 없으면 호스트 직렬이 서지 않는다."
    return "$GATE_LOCK_READINESS_EXIT"; }
  { exec {GATE_HOST_MUTEX_FD}>"$path"; } 2>/dev/null || {
    GATE_HOST_MUTEX_FD=""
    readiness_env_wait "$gate" "호스트 뮤텍스($path)" "${wait_s}초" "0초" \
      "잠금 파일을 쓰기로 열지 못했다(권한·fd 고갈·읽기 전용). 잠글 대상이 없으면 호스트 직렬이 서지 않는다."
    return "$GATE_LOCK_READINESS_EXIT"; }
  # 비어 있으면 표식을 찍지 않는다 — 안 기다린 회차에 대기 로그를 남기면 값이 값을 못 한다.
  if flock -n "$GATE_HOST_MUTEX_FD" 2>/dev/null; then
    GATE_HOST_MUTEX_PATH="$path"; return 0
  fi
  # 대기는 **보인다.** 조용히 900초 기다리면 멈춘 것과 구분되지 않는다(intent Q5).
  # 찍는 자리는 둘뿐이다 — 시도 직전 1회 ＋ 결과 1회. 값 두 개면 충분하고 로그가 안 는다.
  # 요약 분류기는 `^::gate-readiness-failure::`·`^::gate-failure::` 만 보므로 충돌하지 않는다.
  started="$(date +%s)"
  printf '::gate-waiting::gate=%s|waited=0|limit=%s|lock=%s\n' "$gate" "$wait_s" "$path"
  if flock -w "$wait_s" "$GATE_HOST_MUTEX_FD" 2>/dev/null; then
    now="$(date +%s)"; GATE_HOST_MUTEX_WAITED=$(( now - started ))
    printf '::gate-waiting::gate=%s|waited=%s|limit=%s|lock=%s\n' \
      "$gate" "$GATE_HOST_MUTEX_WAITED" "$wait_s" "$path"
    GATE_HOST_MUTEX_PATH="$path"; return 0
  fi
  # ⑶ 상한 초과. ⚠ 여기서 상한을 늘려 green 을 만들지 않는다 — 78 이 나면 그 값이 곧 실측이다.
  now="$(date +%s)"; GATE_HOST_MUTEX_WAITED=$(( now - started ))
  eval "exec ${GATE_HOST_MUTEX_FD}>&-" 2>/dev/null || true
  GATE_HOST_MUTEX_FD=""
  readiness_env_wait "$gate" "호스트 뮤텍스($path)" "${wait_s}초" "${GATE_HOST_MUTEX_WAITED}초" \
    "다른 프로세스가 serial 선언 게이트를 잡고 있었다. 이 게이트는 판정되지 않았다 — 부하가 섞인 green 을 내는 대신 안 돌았다고 말한다. 상한은 COLAB_GATE_MUTEX_WAIT 초."
  return "$GATE_LOCK_READINESS_EXIT"
}

gate_host_mutex_release() {
  [ -n "$GATE_HOST_MUTEX_FD" ] || return 0
  eval "exec ${GATE_HOST_MUTEX_FD}>&-" 2>/dev/null || true
  GATE_HOST_MUTEX_FD=""
}
