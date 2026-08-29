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

  # ⭐ **오라클은 코드가 쥔다 — 설정 파일이 아니다** (`PLAN-SoT §9 〈170〉-㉮` · 2026-08-27).
  #   `R-1` 1회차에서 실 설정 파일에 `COLAB_VOLBACKUP_ORACLE_uploads` 가 **없어서** V5 가 SKIP 됐고,
  #   그 SKIP 이 「원장 오라클 포함 GREEN」으로 요약됐다. 원인은 오라클이 아니라 **배선**이었다 —
  #   손으로 켜니 진짜 GREEN 이 났다. **손으로 켠 GREEN 은 기구가 아니다.**
  #   그래서 값을 홈의 env 파일에 의존시키지 않고 **레포 안 코드인 여기에 기본값으로 박는다.**
  #   ⚠ `:=` 는 **미설정과 빈 값을 모두** 덮는다 — 실 설정에 빈 줄이 있어도 기본값이 산다.
  : "${COLAB_VOLBACKUP_ORACLE_uploads:=d3_file}"
  # `previews` 는 원장에 대응 표가 없다. **빈 값이 아니라 `none` 이라 적는다** — `volume_oracle` 주석 참조.
  : "${COLAB_VOLBACKUP_ORACLE_previews:=none}"

  # 볼륨별 최소 건수 기본값 — 실측(`R1-REHEARSAL-01 §2.2` · uploads 135 · previews 39)의 **절반**.
  # 근거는 원장 쪽과 같다(`〈128〉`): 막아야 하는 것은 「거의 빈 아카이브」이지 소폭 변동이 아니고,
  # 절반으로 두면 **데이터가 늘수록 자동으로 보수적**이 된다. 여기 두는 이유도 오라클과 같다 —
  # 실 설정에 이 키가 없어 기본 `1` 로 돌던 것이 `R-1` 1회차의 결손 12 였다.
  : "${COLAB_VOLBACKUP_MIN_FILES_uploads:=67}"
  : "${COLAB_VOLBACKUP_MIN_FILES_previews:=19}"

  # 회차 편입 선언 — 세 상태. 판정은 `preflight.sh P2/P5-b` 가 한다. 자세한 것은 `volume_pairing` 주석.
  : "${COLAB_VOLBACKUP_PAIRING_uploads:=round}"
  : "${COLAB_VOLBACKUP_PAIRING_previews:=round}"
}

volume_list() { printf '%s\n' ${COLAB_VOLBACKUP_VOLUMES}; }

# 도커가 아는 실제 볼륨 이름 = <프로젝트명>_<볼륨명>. compose 의 `name:` 이 접두사를 만든다.
volume_real_name() { printf '%s_%s' "$COLAB_VOLBACKUP_PROJECT" "$1"; }

# ── 볼륨별 합격선 · 오라클 ────────────────────────────────────────────────────
# `F9` 가 원장 프로파일에 세운 것과 **같은 형태**다: 볼륨마다 따로 걸고, 하나라도 실패하면 전체가 실패.
#   COLAB_VOLBACKUP_MIN_FILES_<볼륨>   아카이브 안 파일 최소 건수. **오라클과 같은 세 상태다**
#   COLAB_VOLBACKUP_ORACLE_<볼륨>      원장 대조 오라클의 테이블 이름. `none` = 명시 면제 · 비면 RED
_vvar() { local n="$1"; eval "printf '%s' \"\${$n:-}\""; }

# ⭐ **최소 건수도 세 상태다** (`PLAN-SoT §9 〈171〉-㉮` · 2026-08-27).
#   종전에는 미선언이면 **조용히 `1`** 로 떨어졌다. 그것은 `〈170〉-㉳` 가 실물로 잡은 결함
#   (「기본 1 이던 것이 결손 12」)과 **같은 모양**이고, 플래그 하나 거리에 있었다 —
#   새 볼륨을 `ORACLE_<볼륨>=none` 으로 **정당하게 면제**하면 V5 는 승인된 SKIP 이 되는데
#   V6 는 조용히 합격선 1 이 되어 **파일 1건짜리 아카이브가 통과**한다.
#   오라클만 3상태로 두면 둘이 갈라진다. 그래서 **대칭으로 맞춘다.**
#     <숫자>         = 합격선. V6 가 그 값으로 돈다
#     none           = **명시적 면제.** 사람이 「이 볼륨엔 합격선을 두지 않는다」고 적은 것. 승인된 SKIP
#     빈 값·미설정   = **선언 자체가 없다.** V6 는 **RED**
#   ⚠ 판정은 `verify-volume-artifact.sh V6` 가 한다. 여기서는 **값을 지어내지 않고 그대로 돌려준다** —
#     `volume_oracle` 과 완전히 같은 형태다. 둘이 같은 모양이어야 다시 갈라지지 않는다.
volume_min_files() { _vvar "COLAB_VOLBACKUP_MIN_FILES_$1"; }
# 오라클 선언은 **세 상태**다. 두 상태(있다/없다)로 두면 「선언을 잊은 것」과
# 「없다고 판단한 것」이 같은 값이 되고, 그 구분이 없는 것이 `〈170〉-㉮` 의 실패였다.
#   <테이블명>     = 오라클 있음. V5 가 돈다
#   none           = **명시적 면제.** 사람이 「이 볼륨엔 대조 기준이 없다」고 적은 것. V5 는 승인된 SKIP
#   빈 값·미설정   = **선언 자체가 없다.** V5 는 **RED** — 새 볼륨을 오라클 없이 추가하면 백업이 선다
volume_oracle()    { _vvar "COLAB_VOLBACKUP_ORACLE_$1"; }

# 산출물 이름 — 원장 덤프(`<프로파일>-<stamp>.sql.gz`)와 **접두사로 갈린다**.
# `ls "$DIR/$P"-*.sql.gz` 같은 기존 글로브에 볼륨 산출물이 섞여 들어가지 않게 하기 위해서다.
volume_artifact_base() { printf '%s/vol-%s-%s' "$1" "$2" "$3"; }

# ── 회차(round) — 원장 덤프와 볼륨 아카이브를 **짝으로** 고르는 자리 ─────────────
# ⭐ `PLAN-SoT §9` · Ted 판정 2026-08-29. 종전 `preflight.sh:29-31` 의 `pick()` 은
#   원장과 볼륨을 **각각 독립으로 「최신」** 으로 골랐다. 원장 전용 백업(배포전 백업 등)이
#   한 번이라도 볼륨보다 뒤에 뜨면 짝이 깨지고, `--stamp` 도 우회로가 되지 못했다 —
#   `backup-full.sh` 가 **볼륨마다 다른 스탬프**를 찍기 때문이다(실측 35초 차).
#   ⟹ 네 산출물을 한꺼번에 옳게 고르는 스탬프가 존재하지 않았다. **입력을 다 줘도 GREEN 이 안 됐다.**
#
# 고침 = **회차 이름으로 묶는다.** 회차의 이름은 그 회차의 platform 원장 덤프 파일명이고,
# 볼륨 아카이브는 이미 `.pair` 에 그 이름을 적고 있다(`backup-full.sh:40-46`). 없던 것은 값이 아니라
# **그 값으로 고르는 기구**였다. 백업이 뜨는 방식은 바꾸지 않는다.

# 보관처의 회차 이름을 **새것부터** 줄줄이 낸다. 회차 이름 = platform 덤프의 basename.
backup_rounds() { # $1=보관처
  ls -1t "$1"/platform-*.sql.gz 2>/dev/null | while IFS= read -r f; do basename "$f"; done
}

# 회차 이름에서 스탬프만 뽑는다.  platform-20260829T033005.sql.gz → 20260829T033005
round_stamp() { local b="${1##*/}"; b="${b%.sql.gz}"; printf '%s' "${b##*-}"; }

# 그 회차에 속한 볼륨 아카이브 경로. `.pair` 가 회차 이름과 같은 것 하나. 없으면 비출력 ＋ 1.
round_volume_archive() { # $1=보관처  $2=볼륨  $3=회차 이름
  local a p
  for a in "$1"/vol-"$2"-*.tar.gz; do
    [ -e "$a" ] || continue
    p="${a%.tar.gz}.pair"
    [ -f "$p" ] || continue
    if [ "$(cat "$p" 2>/dev/null)" = "$3" ]; then printf '%s' "$a"; return 0; fi
  done
  return 1
}

# 그 회차에 속한 프로파일 원장 덤프. platform 은 회차 이름 그 자체이고,
# 나머지 프로파일은 `backup.sh` 가 **순차로** 뜨므로 스탬프가 몇 초 어긋난다(실측 8초 차).
# 그래서 **회차 스탬프에 가장 가까운 것**을 고르고, 30분을 넘으면 그 회차에 없다고 본다(P5 와 같은 창).
round_profile_dump() { # $1=보관처  $2=프로파일  $3=회차 이름
  local want got best="" bestd=99999999 f s d
  want="$(round_stamp "$3")"
  got=$(date -d "${want:0:8} ${want:9:2}:${want:11:2}:${want:13:2}" +%s 2>/dev/null) || return 1
  [ -n "$got" ] || return 1
  if [ "$2" = platform ]; then [ -f "$1/$3" ] && { printf '%s' "$1/$3"; return 0; }; return 1; fi
  for f in "$1"/"$2"-*.sql.gz; do
    [ -e "$f" ] || continue
    s="$(round_stamp "$f")"
    d=$(date -d "${s:0:8} ${s:9:2}:${s:11:2}:${s:13:2}" +%s 2>/dev/null) || continue
    d=$(( got > d ? got - d : d - got ))
    if [ "$d" -lt "$bestd" ]; then bestd="$d"; best="$f"; fi
  done
  [ -n "$best" ] && [ "$bestd" -le 1800 ] && { printf '%s' "$best"; return 0; }
  return 1
}

# ⭐ **볼륨의 회차 편입 선언도 세 상태다** — `volume_oracle`·`volume_min_files` 와 같은 모양이다.
#   둘이 같은 모양이어야 다시 갈라진다는 것이 `〈171〉-㉮` 의 교훈이다.
#     round          = 이 볼륨은 회차의 짝이다. 맞는 아카이브가 없으면 그 회차는 **성립하지 않는다**
#     none           = **명시적 면제.** 사람이 「이 볼륨은 원장 회차에 매이지 않는다」고 적은 것. 승인된 SKIP
#     빈 값·미설정   = **선언 자체가 없다.** → **RED.** 새 볼륨을 선언 없이 추가하면 사전조건이 선다
volume_pairing() { _vvar "COLAB_VOLBACKUP_PAIRING_$1"; }

# 회차 하나를 고른다. **「최신」을 각각 고르지 않는다.**
#   $1=보관처  $2=스탬프(비면 최신 회차부터 훑는다)
# 성립 조건 = 그 회차의 platform 덤프가 있고, `round` 로 선언된 **모든** 볼륨의 아카이브가 그 회차에 있다.
# 아무 회차도 성립하지 않으면 **비출력 ＋ 1** 을 낸다 — 부르는 쪽이 관대한 기본값으로 떨어지지 않게 한다.
select_backup_round() {
  local dir="$1" stamp="${2:-}" r v pv ok
  local rounds
  if [ -n "$stamp" ]; then rounds="platform-$stamp.sql.gz"; else rounds="$(backup_rounds "$dir")"; fi
  for r in $rounds; do
    [ -f "$dir/$r" ] || continue
    ok=1
    for v in $(volume_list); do
      pv="$(volume_pairing "$v")"
      case "$pv" in
        none) continue ;;
        round) ;;
        *) return 2 ;;   # 선언 없음 — 회차를 고르는 것 자체가 틀렸다. 부르는 쪽이 RED 를 낸다
      esac
      round_volume_archive "$dir" "$v" "$r" >/dev/null || { ok=0; break; }
    done
    if [ "$ok" -eq 1 ]; then printf '%s' "$r"; return 0; fi
  done
  return 1
}
