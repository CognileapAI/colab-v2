# 공통 함수 — 단독 실행하지 않는다. source 전용.
# 이 파일은 어떤 절대경로도 담지 않는다. 경로는 전부 $HOME 또는 스크립트 상대다.

set -o pipefail

log()  { printf '%s %s\n' "$(date +%Y-%m-%dT%H:%M:%S)" "$*" >&2; }
pass() { printf '  PASS  %s\n' "$*"; }
fail() { printf '  FAIL  %s\n' "$*"; FAILED=$((FAILED+1)); }
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
skip_ack() { printf '  SKIP  %s\n' "$*"; SKIPPED=$((SKIPPED+1)); }

# 요약줄 정본. SKIP 건수를 숨기는 GREEN 을 만들 수 없게 한 곳에 모은다.
verdict() { # $1=대상 이름(요약줄 앞머리)
  local what="${1:-결과}"
  local sk=""; [ "${SKIPPED:-0}" -ne 0 ] && sk=" · 승인된 SKIP ${SKIPPED}건"
  if [ "${FAILED:-0}" -ne 0 ]; then
    echo "$what: RED (실패 ${FAILED}건${sk})"; return 1
  fi
  if [ "${SKIPPED:-0}" -ne 0 ]; then
    echo "$what: GREEN (전부 통과 · **승인된 SKIP ${SKIPPED}건** — 무엇을 안 봤는지는 위 SKIP 줄)"; return 0
  fi
  echo "$what: GREEN (SKIP 0 — 모든 항목이 실제로 돌았다)"; return 0
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
#   ⑵ 이름 모양 (`secret_shaped`) — 볼륨 트리처럼 허용 목록을 못 쓰는 자리에서 쓴다.
#
# ⚠ **값을 절대 읽지도 찍지도 않는다.** 이름과 건수만 다룬다 (`〈121〉-㉰` 계열).

# 비밀 7종과 그 이웃의 이름 모양. 하나라도 맞으면 비밀 취급한다.
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
profile_min_tables() { local v; v="$(_pvar "COLAB_BACKUP_MIN_TABLES_$1")"; [ -n "$v" ] && printf '%s' "$v" || printf '%s' "$COLAB_BACKUP_MIN_TABLES"; }
profile_min_rows()   { local v; v="$(_pvar "COLAB_BACKUP_MIN_ROWS_$1")";   [ -n "$v" ] && printf '%s' "$v" || printf '%s' "$COLAB_BACKUP_MIN_ROWS"; }
