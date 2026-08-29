# 공통 함수 — 단독 실행하지 않는다. source 전용.
# 이 파일은 어떤 절대경로도 담지 않는다. 경로는 전부 $HOME 또는 스크립트 상대다.

set -o pipefail

log()  { printf '%s %s\n' "$(date +%Y-%m-%dT%H:%M:%S)" "$*" >&2; }
# ⚠ 통과 건수를 **센다.** 세지 않으면 「한 건도 안 봤다」와 「전건 통과」가 구분되지 않는다 —
#   그 구분이 없던 것이 아래 `verdict` 의 결함이었다.
pass() { printf '  PASS  %s\n' "$*"; PASSED=$(( ${PASSED:-0} + 1 )); }
fail() { printf '  FAIL  %s\n' "$*"; FAILED=$(( ${FAILED:-0} + 1 )); }
die()  { log "ERROR: $*"; exit 1; }

# ── SKIP 규약 (`〈170〉-㉮` · 2026-08-27) ──────────────────────────────────────
# **SKIP 을 GREEN 으로 요약하지 않는다.** `R-1` 1회차에서 V5 원장 오라클이 설정 부재로
# SKIP 된 채 「원장 오라클 포함 GREEN」이 찍혔다 — `CLAUDE.md §4` 가 막으려던 green-by-skip 이
# 그것을 막으려고 만든 기구 안에서 재현된 것이다. 그래서 SKIP 을 두 종으로 가른다.
#
#   · **승인된 SKIP** = 사람이 **명시 플래그로** 유예한 것(`--skip-age` 등). `skip_ack` 로 센다.
#     통과할 수 있지만 **요약줄에 건수가 반드시 나온다.** 「무엇을 안 봤는가」가 안 보이면 승인이 아니다.
#   · **암묵적 SKIP** = 설정·인자가 없어서 꺼진 것. **이제 존재하지 않는다 — 전부 `fail` 이다.**
#     모르는 것을 통과로 읽지 않는다.
skip_ack() { printf '  SKIP  %s\n' "$*"; SKIPPED=$(( ${SKIPPED:-0} + 1 )); }

# 요약줄 정본. SKIP 건수를 숨기는 GREEN 을 만들 수 없게 한 곳에 모은다.
#
# ── 검사 대상 0건 가드 (2026-08-30) ──────────────────────────────────────────
# 종전에는 `FAILED` 만 봤다. 그래서 **통과도 실패도 SKIP 도 하나도 없는 상태** —
# 즉 검사가 한 건도 돌지 않은 상태 — 가 「GREEN (SKIP 0 — 모든 항목이 실제로 돌았다)」로
# 찍혔다. 요약줄이 스스로 거짓말을 한 것이고, `CLAUDE.md §4` 의 green-by-skip 그 자체다.
# 세 상태로 가른다:
#   ⓐ 검사 대상 있음(`PASSED` > 0)      → 검사한다. 요약줄에 **통과 건수**를 적는다.
#   ⓑ 명시 면제만 있음(`SKIPPED` > 0)   → 통과하되 요약줄에 **「검사 0건」과 SKIP 건수**를 적는다.
#   ⓒ 아무것도 선언·발견되지 않음(0/0/0) → **RED.** 모르는 것을 통과로 읽지 않는다.
verdict() { # $1=대상 이름(요약줄 앞머리)
  local what="${1:-결과}"
  local sk=""; [ "${SKIPPED:-0}" -ne 0 ] && sk=" · 승인된 SKIP ${SKIPPED}건"
  if [ "${FAILED:-0}" -ne 0 ]; then
    echo "$what: RED (실패 ${FAILED}건 · 통과 ${PASSED:-0}건${sk})"; return 1
  fi
  if [ "${PASSED:-0}" -eq 0 ] && [ "${SKIPPED:-0}" -eq 0 ]; then
    echo "$what: RED (검사 0건 — 통과·실패·명시 면제가 하나도 없다. 검사 대상이 선언되지 않았거나 발견되지 않았다. 대상 0건은 통과가 아니다)"; return 1
  fi
  if [ "${PASSED:-0}" -eq 0 ]; then
    echo "$what: GREEN (**검사 0건 · 승인된 SKIP ${SKIPPED}건** — 실제로 본 항목이 없다. 무엇을 안 봤는지는 위 SKIP 줄)"; return 0
  fi
  if [ "${SKIPPED:-0}" -ne 0 ]; then
    echo "$what: GREEN (통과 ${PASSED}건 · **승인된 SKIP ${SKIPPED}건** — 무엇을 안 봤는지는 위 SKIP 줄)"; return 0
  fi
  echo "$what: GREEN (통과 ${PASSED}건 · SKIP 0 — 모든 항목이 실제로 돌았다)"; return 0
}


# ── 비밀 배제 (`PLAN-SoT §9 〈170〉-㉰` · Ted 판정 2026-08-27 「지우고, 생기지 않게 막는다」) ──
# `〈163〉-㉲` = **비밀 7종을 백업하지 않는다.** 사본이 원본과 같은 머신 1대 위에 놓이기 때문이다.
# `R-1` 1회차에 보관처에서 `subjects-*.json` 사본이 발견됐다 — `〈152〉` 가 픽스처 3건을 걷기 전에
# 뜬 덮어쓰기 전 백업이고, **폐기된 픽스처 토큰이 그 안에 살아 있었다.** `〈152〉-㉱` 가 401 로 증명한
# 폐기를 사본 하나가 무르는 모양이다. 주석으로는 못 막는다. 그래서 **기구를 둘 둔다.**
#
#   ⑴ 이름 규약 (`backup_dir_offenders`) — 보관처에는 **산출물만** 있어야 한다.
#      규약에 안 맞는 파일이 하나라도 있으면 RED. 배제 목록이 아니라 **허용 목록**이라,
#      「아직 생각 못 한 모양의 비밀」도 걸린다. 배제 목록은 언제나 뒤늦다.
#   ⑵ 이름 모양 (`secret_shaped*`) — 볼륨 트리처럼 허용 목록을 못 쓰는 자리에서 쓴다.
#
# ⚠ **값을 절대 읽지도 찍지도 않는다.** 이름과 건수만 다룬다 (`〈121〉-㉰` 계열).
#
# ── 판정기가 **둘**인 이유 (`PLAN-SoT §9 〈171〉-㉰` · 2026-08-27) ─────────────
# 두 자리는 **누가 이름을 짓는가**가 다르고, 그래서 오탐의 값이 다르다.
#
#   · **보관처**(`secret_shaped`) — 이름을 **기계가** 짓는다. 규약이 닫혀 있어(`backup_dir_offenders`)
#     낱말이 하나라도 걸리면 그것은 진짜 이상 신호다. **오탐 비용이 사실상 0** 이므로 **최대로 넓게** 잡는다.
#     실제 비밀 사본이 떨어질 자리도 여기다(`R-1` 1회차의 `subjects-*.json`). **여기는 절대 좁히지 않는다.**
#   · **볼륨 트리**(`secret_shaped_volume`) — 이름을 **연구자가** 짓는다. `uploads` 는 사용자가 올린
#     연구 데이터이고, 수문 관측 자료에 `station_token_map.csv` 같은 이름은 **정상적으로 온다.**
#     그런데 여기서 걸리면 `〈170〉-㉰` 판정에 따라 **그 볼륨의 야간 백업이 통째로 선다** —
#     오탐 하나가 백업 정지다. 그래서 **낱말(`*token*`·`*secret*`·`*password*`)을 뺀다.**
#
# ⭑ 뺀 것과 남긴 것의 기준 = **낱말인가 모양인가.** 진짜 비밀이 볼륨에 흘러드는 경로는 어휘가 아니라
#   **꼴**을 갖는다 — 확장자(`.env`·`.pem`·`.key`·`.envrc`) · 알려진 고정 이름(`id_rsa`·`credentials*`·
#   `subjects*`) · 접속 문자열 키(`*_DB_URL*`). 그 셋은 연구 데이터 파일명으로 거의 나오지 않는다.
#   반대로 `token`·`secret`·`password` 는 **관측 지점표·설정 표에 흔한 낱말**이고, 잡아 봐야
#   비밀이 아닐 확률이 압도적이다. **좁힌 것이 아니라 자리를 나눈 것이다** — 보관처 쪽은 그대로다.
# ⚠ **남는 위험을 적어 둔다.** 볼륨에 `api-token.txt` 라는 **진짜** 비밀이 놓이면 볼륨 판정기는 못 잡는다.
#   그 경우 아카이브에 들어간다. 대신 그 파일은 **보관처로 복사되지 않으므로** ⑴ 이 여전히 유효하고,
#   `uploads` 볼륨에 비밀을 두는 것 자체는 접수 경로가 만들지 않는 상태다(사람이 손으로 넣어야 한다).
#   **정지를 사람이 못 보는 위험**(README 「볼륨 백업이 정지했을 때」)이 이 위험보다 컸다는 것이 판단이다.

# 보관처용 — **최대로 넓다.** 낱말까지 잡는다. 좁히지 않는다.
secret_shaped() { # $1=경로(또는 파일명) → 0 = 비밀 모양이다
  local b; b="$(basename "$1")"
  case "$b" in
    subjects*|*subjects*.json|credentials*|*credentials*.json) return 0 ;;
    *.env|.env|.env.*|*.envrc)                                  return 0 ;;
    *_DB_URL*|*db-url*|*db_url*|*DB-URL*)                       return 0 ;;
    *token*|*secret*|*password*|*passwd*|*.pem|*.key|id_rsa*)   return 0 ;;
  esac
  return 1
}

# 볼륨 트리용 — **모양만.** 낱말 넷(`token`·`secret`·`password`·`passwd`)을 빼고,
# 확장자·고정 이름·접속 문자열 키는 **보관처와 똑같이** 잡는다.
secret_shaped_volume() { # $1=볼륨 안 상대 경로 → 0 = 비밀 모양이다
  local b; b="$(basename "$1")"
  case "$b" in
    subjects*|*subjects*.json|credentials*|*credentials*.json) return 0 ;;
    *.env|.env|.env.*|*.envrc)                                  return 0 ;;
    *_DB_URL*|*db-url*|*db_url*|*DB-URL*)                       return 0 ;;
    *.pem|*.key|id_rsa*)                                        return 0 ;;
  esac
  return 1
}

# 보관처 허용 목록 — 산출물 이름 규약. 여기 안 맞는 파일 경로를 표준출력에 줄줄이 낸다(없으면 무출력).
backup_dir_offenders() { # $1=보관처 (기본 $COLAB_BACKUP_DIR)
  local d="${1:-$COLAB_BACKUP_DIR}" f b
  [ -d "$d" ] || return 0
  for f in "$d"/* "$d"/.[!.]*; do
    [ -e "$f" ] || continue
    [ -f "$f" ] || { printf '%s\n' "$f"; continue; }
    b="$(basename "$f")"
    case "$b" in
      *.sql.gz|*.sql.gz.sha256) continue ;;                       # 원장 덤프
      vol-*.tar.gz|vol-*.tar.gz.sha256) continue ;;               # 볼륨 아카이브
      vol-*.manifest.tsv|vol-*.pair) continue ;;                  # 볼륨 아카이브의 사전
      .inflight-*) continue ;;                                    # 작업 중 임시본(스스로 걷힌다)
    esac
    printf '%s\n' "$f"
  done
}

# 설정 로드. 순서: 환경변수 > 설정파일 > 기본값
load_config() {
  local cfg="${COLAB_BACKUP_CONFIG:-$HOME/.colab-v2-staging-backup.env}"
  if [ -f "$cfg" ]; then set -a; . "$cfg"; set +a; fi
  : "${COLAB_BACKUP_TARGET:=none}"
  : "${COLAB_BACKUP_DIR:=$HOME/colab-v2-backups/staging}"
  : "${COLAB_BACKUP_MIN_TABLES:=20}"
  : "${COLAB_BACKUP_MIN_ROWS:=1}"
  # ⭐ **프로파일 합격선도 코드가 쥔다** (`〈171〉-㉯` · 조용한 기본값 스윕에서 나온 형제 결함).
  #   종전에는 `COLAB_BACKUP_MIN_ROWS_<p>` 가 실 설정(홈 env 파일)에만 있었고, 없으면
  #   **조용히 전역 `1`** 로 떨어졌다 — `〈170〉-㉮ ⑴` 이 볼륨 오라클에서 없앤 것과 **같은 배선**이다.
  #   실측(staging 2026-08-27 · platform 381행 · ai 91행)의 절반을 여기 박는다(`〈128〉`·`〈144〉`).
  : "${COLAB_BACKUP_MIN_TABLES_platform:=20}"
  : "${COLAB_BACKUP_MIN_ROWS_platform:=190}"
  : "${COLAB_BACKUP_MIN_TABLES_ai:=4}"
  : "${COLAB_BACKUP_MIN_ROWS_ai:=45}"
  : "${COLAB_BACKUP_MAX_AGE_MIN:=1500}"
  : "${COLAB_BACKUP_RETENTION_DAYS:=14}"
}

# ── 프로파일 ────────────────────────────────────────────────────────────────
# 체인이 분리이므로(CLAUDE.md §3-3) 백업도 분리다. 한 산출물이 두 DB 를 덮는 척하지 않는다.
#   COLAB_BACKUP_PROFILES="platform ai"
#   프로파일별 재정의: COLAB_BACKUP_DB_<p> · COLAB_BACKUP_MIN_TABLES_<p> · COLAB_BACKUP_MIN_ROWS_<p>
# 미설정이면 구 단일대상 설정(COLAB_BACKUP_PG_DB)을 프로파일 `platform` 하나로 읽는다 — 기존 fixture 호환.
backup_profiles() {
  if [ -n "${COLAB_BACKUP_PROFILES:-}" ]; then printf '%s\n' ${COLAB_BACKUP_PROFILES}; else echo platform; fi
}
_pvar() { local n="$1"; eval "printf '%s' \"\${$n:-}\""; }
profile_db()         { local v; v="$(_pvar "COLAB_BACKUP_DB_$1")";         [ -n "$v" ] && printf '%s' "$v" || printf '%s' "${COLAB_BACKUP_PG_DB:-}"; }
# ⚠ **미선언은 전역 기본값으로 떨어지지 않는다** (`〈171〉-㉯`). 전역 `COLAB_BACKUP_MIN_ROWS` 는 `1` 이라,
#   새 프로파일을 하나 추가하면 「행 1건이면 통과」가 조용히 붙었다 — `volume_min_files` 의 `1` 과 같은 모양이다.
#   이제 미선언은 `미선언` 이라는 **숫자가 아닌 값**을 돌려주고, `verify-artifact.sh` 의 합격선 검사(C0)가 RED 를 낸다.
#   호출처가 넷(`backup.sh`·`latest-check.sh`·`restore-rehearsal.sh`·`../restore/preflight.sh`)이라
#   **판정을 소비처 한 곳에 모았다** — 넷에 같은 가드를 흩으면 그중 하나가 언젠가 빠진다.
#   ⚠ 전역 `COLAB_BACKUP_MIN_TABLES`/`_MIN_ROWS` 자체는 **그대로 둔다.** `verify-artifact.sh` 를 손으로
#     한 파일에 대고 돌릴 때 쓰는 값이고, 그쪽을 없애는 것은 기존 검사를 줄이는 일이다.
profile_min_tables() { local v; v="$(_pvar "COLAB_BACKUP_MIN_TABLES_$1")"; [ -n "$v" ] && printf '%s' "$v" || printf '미선언'; }
profile_min_rows()   { local v; v="$(_pvar "COLAB_BACKUP_MIN_ROWS_$1")";   [ -n "$v" ] && printf '%s' "$v" || printf '미선언'; }
