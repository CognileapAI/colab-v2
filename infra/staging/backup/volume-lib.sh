# 볼륨 백업 공통 함수 — 단독 실행하지 않는다. source 전용.
# `lib.sh` 를 먼저 source 한 뒤 이 파일을 source 한다. 절대경로를 담지 않는다.
#
# 왜 파일을 갈랐나 — `lib.sh` 는 **원장 덤프**의 설정이고 여기는 **볼륨 아카이브**의 설정이다.
# 둘은 산출물 형태도 합격선도 다르다. 한 파일에 섞으면 `COLAB_BACKUP_MIN_ROWS` 가
# 볼륨에도 적용되는 척하게 되고, 그 「척」이 IS3 가 막으려던 실패의 형태다.

load_volume_config() {
  : "${COLAB_VOLBACKUP_PROJECT:=colab-v2-staging}"
  : "${COLAB_VOLBACKUP_VOLUMES:=uploads previews}"
  : "${COLAB_VOLBACKUP_HELPER_IMAGE:=alpine:3.20}"
  # 볼륨 아카이브 보존 — 원장 덤프(14일)와 **따로** 둔다. 근거는 README 「보존 정책」.
  : "${COLAB_VOLBACKUP_RETENTION_DAYS:=3}"
  # 디스크 여유 사전점검 — 「예상 아카이브 크기 x 배수」만큼 안 남아 있으면 시작하지 않는다.
  : "${COLAB_VOLBACKUP_FREE_MULTIPLIER:=3}"
  # 신선도 상한(분). 원장 덤프와 같은 값을 기본으로 둔다 — 같은 회차에 같이 뜨기 때문이다.
  : "${COLAB_VOLBACKUP_MAX_AGE_MIN:=${COLAB_BACKUP_MAX_AGE_MIN:-1500}}"
}

volume_list() { printf '%s\n' ${COLAB_VOLBACKUP_VOLUMES}; }

# 도커가 아는 실제 볼륨 이름 = <프로젝트명>_<볼륨명>. compose 의 `name:` 이 접두사를 만든다.
volume_real_name() { printf '%s_%s' "$COLAB_VOLBACKUP_PROJECT" "$1"; }

# ── 볼륨별 합격선 · 오라클 ────────────────────────────────────────────────────
# `F9` 가 원장 프로파일에 세운 것과 **같은 형태**다: 볼륨마다 따로 걸고, 하나라도 실패하면 전체가 실패.
#   COLAB_VOLBACKUP_MIN_FILES_<볼륨>   아카이브 안 파일 최소 건수
#   COLAB_VOLBACKUP_ORACLE_<볼륨>      원장 대조 오라클의 테이블 이름. 비면 오라클 없음
_vvar() { local n="$1"; eval "printf '%s' \"\${$n:-}\""; }
volume_min_files() { local v; v="$(_vvar "COLAB_VOLBACKUP_MIN_FILES_$1")"; [ -n "$v" ] && printf '%s' "$v" || printf '1'; }
volume_oracle()    { _vvar "COLAB_VOLBACKUP_ORACLE_$1"; }

# 산출물 이름 — 원장 덤프(`<프로파일>-<stamp>.sql.gz`)와 **접두사로 갈린다**.
# `ls "$DIR/$P"-*.sql.gz` 같은 기존 글로브에 볼륨 산출물이 섞여 들어가지 않게 하기 위해서다.
volume_artifact_base() { printf '%s/vol-%s-%s' "$1" "$2" "$3"; }
