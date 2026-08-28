#!/usr/bin/env bash
# 필수 설정 프리플라이트 — **배포가 무엇을 필요로 하는지 빌드 전에 전부 묻는다.**
#
#   preflight.sh [<env 파일>]        # 단독 실행 (red fixture 용)
#   . preflight.sh                   # 함수만 얻는다 (deploy.sh 가 이렇게 쓴다)
#
# ── 왜 생겼나 (2026-08-28 staging 첫 배포) ───────────────────────────────────
# 배포가 단계 ⑦(롤 부트스트랩)에서 죽었다. 사유는 `COLAB_OWNER_PASSWORD` 미설정이다.
# 값 자체는 홈 env 파일에 **있었다.** 없던 것은 배선이었다 —
#   · `deploy.sh` 는 env 파일을 `docker compose --env-file` 로만 넘겼다.
#     그건 **compose 가 뜨우는 컨테이너에만** 닿는다.
#   · `db-bootstrap.sh` 는 compose 서비스가 아니라 호스트에서 직접 도는 스크립트다.
#     그래서 자기 환경이 **비어 있었고**, 필수 변수 단언에서 죽었다.
# 그리고 그 사실이 **⑦ 에 가서야** 드러났다. 그 앞의 게이트·태그 보존·빌드·백업이
# 전부 헛돈 뒤다. 종전의 사실상 프리플라이트는 `compose.i2.yml` 의 `:?` 뿐이었고,
# 그것은 **compose 가 아는 키만** 안다 — `db-bootstrap.sh` 가 필요로 하는 키는 보이지 않았다.
#
# 그래서 이 파일이 하는 일은 둘이다.
#   ① env 파일을 **프로세스 환경으로 실제로 싣는다** (compose 만 받던 것을 호스트 단계도 받는다)
#   ② 필요한 키 목록을 **필요로 하는 쪽에서 받아 온다** — compose 의 `:?` + `db-bootstrap.sh required-env`.
#      목록을 여기에 손으로 베껴 두면 언젠가 어긋나고, 어긋난 순간 이 검사기는 무력해진다.
#
# ⚠ **값을 출력하지 않는다.** 이 파일이 말할 수 있는 것은 **키 이름과 건수**뿐이다
#   (`〈121〉-㉯` — 접속 문자열은 값이 아니라 파일로 넘긴다. 로그에도 남기지 않는다).
set -uo pipefail

_PF_HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# lib.sh 의 판정 어휘(`verdict`)를 쓴다 — 요약줄은 한 곳에서만 나온다.
if ! declare -F verdict >/dev/null 2>&1; then . "$_PF_HERE/pipeline/lib.sh"; fi

# ── env 파일 적재 ───────────────────────────────────────────────────────────
# docker env-file 문법의 부분집합만 읽는다: `KEY=VALUE` · `#` 주석 · 빈 줄.
# **이미 환경에 있는 값은 덮지 않는다** — compose 의 우선순위(셸 > --env-file)와 같게 둔다.
# 값은 변수에만 들어간다. echo · log · set -x 대상이 되지 않는다.
env_load() { # $1=env 파일
  local f="${1:-}" line k v
  [ -n "$f" ] && [ -f "$f" ] || return 1
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in ''|'#'*) continue ;; esac
    case "$line" in *=*) ;; *) continue ;; esac
    k="${line%%=*}"; v="${line#*=}"
    case "$k" in [A-Za-z_]*) ;; *) continue ;; esac
    # 따옴표로 감싼 값은 벗긴다(compose 와 같은 처리).
    case "$v" in \"*\") v="${v:1:${#v}-2}" ;; \'*\') v="${v:1:${#v}-2}" ;; esac
    [ -n "${!k:-}" ] && continue
    export "$k=$v"
  done < "$f"
  return 0
}

# ── 필요한 키는 **필요로 하는 쪽에 묻는다** ──────────────────────────────────
# `COLAB_RELEASE_TAG` 는 제외한다 — 그건 설정이 아니라 `deploy.sh` 가 커밋에서 짓는 이름이다.
PREFLIGHT_NOT_CONFIG=(COLAB_RELEASE_TAG)

preflight_required_keys() {
  {
    # compose 가 `:?` 로 요구하는 것
    grep -oE '\$\{[A-Za-z_][A-Za-z0-9_]*:\?' "$_PF_HERE/compose.i2.yml" \
      | sed 's/^\${//; s/:?$//'
    # 호스트에서 직접 도는 단계가 요구하는 것 (⑦ 롤 부트스트랩 · ⑨ GRANT)
    "$_PF_HERE/db-bootstrap.sh" required-env
  } | sort -u | while read -r k; do
    [ -n "$k" ] || continue
    case " ${PREFLIGHT_NOT_CONFIG[*]} " in *" $k "*) continue ;; esac
    printf '%s\n' "$k"
  done
}

# ── 판정 ────────────────────────────────────────────────────────────────────
# 세 상태 규약: 선언되면 검사한다 · 명시 면제는 건수를 드러낸다 · **아무 말 없으면 실패한다.**
# 여기에 승인된 SKIP 은 없다 — 필수 설정은 유예 대상이 아니다.
preflight_required() { # $1=env 파일
  local f="${1:-}" k n
  FAILED=0; SKIPPED=0; CHECKED=0
  if [ -z "$f" ] || [ ! -f "$f" ]; then
    echo "  FAIL  [설정파일] \$COLAB_STAGING_ENV 가 가리키는 파일이 없다"
    FAILED=1; verdict "필수 설정 프리플라이트"; return 1
  fi
  env_load "$f" || { echo "  FAIL  [설정파일] 읽지 못했다"; FAILED=1; verdict "필수 설정 프리플라이트"; return 1; }

  local before
  while read -r k; do
    [ -n "$k" ] || continue
    CHECKED=$((CHECKED+1)); before="$FAILED"
    if [ -z "${!k:-}" ]; then
      # ⭑ **키 이름만** 말한다. 값은 없을 때조차 화면에 올리지 않는다.
      fail "$k 이(가) 비어 있다 — 배포가 이 값을 쓴다"
      continue
    fi
    # 경로로 넘기는 설정(`〈121〉-㉯`)은 **실물까지** 본다. 경로만 있고 파일이 없으면
    # 마운트가 조용히 빈 것을 덮어쓰고, 그 결함은 컨테이너가 뜬 뒤에나 보인다.
    case "$k" in
      # ⚠ 존재만 본다(`-f`), **읽기 권한은 보지 않는다**. 이 파일들은 root 소유 0600 이고
      #    마운트하는 주체는 도커 데몬이다 — 프리플라이트를 도는 사람이 읽을 수 있는지는
      #    배포가 서는지와 다른 질문이다. 여기서 `-r` 을 요구하면 멀쩡한 배포를 red 로 만든다.
      *_FILE) [ -f "${!k}" ] || fail "$k 가 가리키는 파일이 없다 (경로는 출력하지 않는다)" ;;
      *_DIR)  [ -d "${!k}" ] || fail "$k 가 가리키는 디렉터리가 없다 (경로는 출력하지 않는다)" ;;
    esac
    [ "$FAILED" = "$before" ] && pass "$k"
  done < <(preflight_required_keys)

  verdict "필수 설정 프리플라이트"
}

# 단독 실행일 때만 돈다.
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
  preflight_required "${1:-${COLAB_STAGING_ENV:-$HOME/.colab-v2-staging.env}}"
fi
