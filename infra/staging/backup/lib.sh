# 공통 함수 — 단독 실행하지 않는다. source 전용.
# 이 파일은 어떤 절대경로도 담지 않는다. 경로는 전부 $HOME 또는 스크립트 상대다.

set -o pipefail

log()  { printf '%s %s\n' "$(date +%Y-%m-%dT%H:%M:%S)" "$*" >&2; }
pass() { printf '  PASS  %s\n' "$*"; }
fail() { printf '  FAIL  %s\n' "$*"; FAILED=$((FAILED+1)); }
die()  { log "ERROR: $*"; exit 1; }

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
