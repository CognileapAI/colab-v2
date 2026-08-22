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
