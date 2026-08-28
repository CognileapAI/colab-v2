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
# flock 이 없으면 잠그지 않고 그냥 진행한다 — 직렬 실행에서는 원래 필요 없던 장치이고,
# 여기서 red 를 내면 「도구 없음」을 검사 실패로 둔갑시키는 꼴이 된다.

gate_lock_fd() { # $1 = 잠금 이름(경로 등 임의 문자열)
  local key path
  key="$(printf '%s' "$1" | cksum | tr -d ' ')"
  path="${TMPDIR:-/tmp}/colab-gate-lock-$key"
  exec 9>"$path" 2>/dev/null || return 1
  command -v flock >/dev/null 2>&1 && flock 9 2>/dev/null
  return 0
}
gate_unlock_fd() { exec 9>&- 2>/dev/null || true; }
