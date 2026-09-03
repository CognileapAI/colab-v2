#!/usr/bin/env bash
# 이미지 digest 대조 — **자체 빌드 6종은 `§5` 원장, 외부 4종은 `§3` 대장.**
#
# ⭑ digest 값을 이 스크립트에 박지 않는다. 값을 두 곳에 적으면 갈라지고, 갈라진 대조는 대조가 아니다.
#
# ⭑ 출처가 둘로 갈린 이유 (Ted 판정 2026-09-03 · `PLAN-SoT §9 〈297〉` · `〈284〉-㉳` 해소):
#   ⓐ `deploy.sh:65` 은 워킹트리 변경이 있으면 **착수를 거부**한다 — 배포가 레포 파일(`§3`)을
#      고치면 다음 배포가 자기 산출로 막힌다. 그래서 대장은 **배포가 못 쓴다**. 손으로 적는 한
#      「지금 무엇인가」가 늘 한 회차 늦는다.
#   ⓑ `deploy.sh` ⑫-a2 / `rollback.sh` 는 별칭을 옮길 때마다 원장
#      (`~/colab-v2-releases/image-digest-ledger.tsv`)에 이미지 하나당 한 줄씩 append 한다.
#      **원장은 자동이고 정확하며 회차 태그를 가진다.** 자체 6종의 기대값은 여기서 온다.
#   ⓒ 외부 4종(postgres·nginx·cloudflared·alpine)은 우리가 별칭을 옮기지 않으므로 원장에 남지 않는다.
#      그 넷은 `§3` 이 계속 정본이다.
#   ⟹ `§3` 의 자체 6줄은 **참고**다. 이 스크립트는 자체 이미지에 대해 `§3` 을 읽지 않는다.
#      원장에 서빙 회차 행이 없으면 **RED 다 — `§3` 으로 되돌아가지 않는다.**
#
# ⭑ 「서빙 중 회차」를 어떻게 고르나 (되물음 없이 결정되는 규칙):
#   1. 원장에서 별칭이 `$ALIAS_TAG`(기본 i2) 인 행만 본다. 파일 순서 = 시간 순서다(append-only).
#   2. 회차 태그를 **최신부터** 훑는다.
#   3. 그 회차의 행 가운데 **살아 있는 이미지의 실측 digest 와 일치하는 것이 하나라도 있으면**
#      그 회차를 「지금 서빙 중」으로 확정하고 훑기를 멈춘다.
#   4. 확정된 회차의 행 전부를 기대값으로 삼아 6종을 한 줄씩 대조한다.
#   5. 어느 회차에서도 하나도 안 맞으면 **RED**(서빙 회차 미상). 롤백으로 별칭이 옛 회차를
#      가리키는 경우도 3 이 옛 회차를 고르므로 그대로 맞는다 — 「마지막 배포」가 아니라
#      「지금 가리키는 것」을 고르기 때문이다.
#   ⭑ 6종 가운데 하나가 어긋나도 나머지 5종이 회차를 고정하므로, 어긋난 한 줄이 「회차 미상」으로
#     뭉개지지 않고 **이미지 이름으로 적발된다.**
#
# 왜 헬스로 대신할 수 없는가: `〈153〉` 때 배선만 바꾸고 **옛 이미지로 올려** ai-service 만
# healthy 였고 사전 DB 가 `None` 으로 조용히 비었다. **죽은 쪽은 바로 보이고 살아 있는 쪽이 속인다.**
#
# 사용: check-image-digests.sh [--ledger <대장.md>] [--digest-ledger <원장.tsv>]
#                             [--record <출력.tsv>] [--compose <compose.yml>]
#   `--record` 는 복원 **전** 상태를 적어 두는 용도다(`R1-RESTORE-DRAFT §4.0 P8`).
#   `--compose` 는 **배포되는 이미지 목록의 정본**이다(기본 `infra/staging/compose.i2.yml`).
#
# ⭑ 세 상태 (Ted 판정 2026-08-29 · `CLAUDE.md §4`):
#     ⓐ 기대값이 있다(자체=원장 행 · 외부=`§3` digest) → **대조한다**
#     ⓑ `§3` 에 `면제: <사유>` 로 명시 면제했다        → **통과하되 건수를 요약줄에 드러낸다**
#     ⓒ 아무 말도 없다(미선언)                          → **RED**
#   ⓒ 가 없던 것이 결함이었다 — 배포되는 이미지가 어디에도 없으면 **검사 대상에서 조용히 빠지고**
#   남은 행만 보고 「전건 일치 GREEN」이 나왔다. 검사 범위를 대장이 스스로 정하면 검사가 아니다.
# 종료코드: 0 = 전건 일치(＋승인된 면제) / 1 = 불일치·미측정·미선언·서빙회차 미상 / 2 = 사용법 오류
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
LEDGER="$REPO/dev-package/reference/IMAGE-DIGESTS.md"
RECORD=""
COMPOSE="$REPO/infra/staging/compose.i2.yml"
ALIAS_TAG="${COLAB_DIGEST_ALIAS_TAG:-i2}"
DLEDGER="${COLAB_DIGEST_LEDGER:-${COLAB_PIPELINE_STATE_DIR:-$HOME/colab-v2-releases}/image-digest-ledger.tsv}"
# 자체 빌드 이미지의 이름 규약. 원장에 남는 것과 같은 집합이다(`pipeline/lib.sh RELEASE_IMAGES`).
SELF_PREFIX="${COLAB_DIGEST_SELF_PREFIX:-colab-v2/}"
while [ $# -gt 0 ]; do
  case "$1" in
    --ledger) LEDGER="${2:?}"; shift 2 ;;
    --digest-ledger) DLEDGER="${2:?}"; shift 2 ;;
    --record) RECORD="${2:?}"; shift 2 ;;
    --compose) COMPOSE="${2:?}"; shift 2 ;;
    *) echo "모르는 인자: $1" >&2; exit 2 ;;
  esac
done
[ -f "$LEDGER" ] || { echo "대장을 찾지 못했다: $LEDGER" >&2; exit 1; }

# 실측 수단은 갈아끼울 수 있게 둔다 — 셀프테스트가 docker 없이 fail-closed 를 증명해야 하기 때문이다.
# 기본값은 도커다. 이미지의 `.Id` 와 `RepoDigests` 를 **둘 다** 내놓는다:
#   자체 빌드 이미지(`colab-v2/*:i2`)는 레지스트리에 올라간 적이 없어 RepoDigest 가 없고
#   `.Id`(=config digest)가 신원이다. 외부 이미지는 RepoDigest 가 붙는다. 어느 쪽이든 일치하면 통과다.
: "${COLAB_DIGEST_INSPECT:=}"
inspect_digests() { # $1=이미지 → 공백으로 구분된 digest 목록
  if [ -n "$COLAB_DIGEST_INSPECT" ]; then "$COLAB_DIGEST_INSPECT" "$1"; return; fi
  docker image inspect "$1" --format '{{.Id}}{{range .RepoDigests}} {{.}}{{end}}' 2>/dev/null
}
# RepoDigest 는 `repo@sha256:…` 형태라 `@` 뒤만 본다.
digest_hit() { # $1=실측목록 $2=기대값
  printf '%s' "$1" | tr ' ' '\n' | sed 's/.*@//' | grep -qx "$2"
}

# 대장 `§3` 의 표 행: `| \`이미지\` | \`sha256:…\` |`
# ⭑ 자체 6줄은 여기 그대로 있으나 **참고**다(개정 2026-09-03). 아래에서 외부 이미지만 이 표를 쓴다.
#   그래도 표를 통째로 읽는 이유 = 표 형식이 깨진 것을 「기대값 0건」으로 조용히 넘기지 않기 위해서다.
ROWS="$(grep -E '^\| *`[^`]+` *\| *`sha256:[0-9a-f]{64}` *\|' "$LEDGER" \
        | sed -E 's/^\| *`([^`]+)` *\| *`(sha256:[0-9a-f]{64})` *\|.*/\1\t\2/')"
[ -n "$ROWS" ] || { echo "대장에서 digest 행을 하나도 읽지 못했다 — 표 형식이 바뀌었는가" >&2; exit 1; }

# ── ⓑ 명시 면제 행: `| \`이미지\` | 면제: <사유> |` ─────────────────────────────
# **사유가 비면 면제가 아니다.** 사유 없는 면제는 검사를 끄는 스위치일 뿐이다.
EXEMPT="$(grep -E '^\| *`[^`]+` *\| *면제:' "$LEDGER" \
          | sed -E 's/^\| *`([^`]+)` *\| *면제: *(.*[^ ]|) *\|.*/\1\t\2/')"

# ── 배포되는 이미지 목록 = compose 의 `image:` (정본) ────────────────────────
# 대장이 자기 검사 범위를 정하지 못하게 한다. 실제로 뜨는 것이 검사 대상이다.
if [ -f "$COMPOSE" ]; then
  REQUIRED="$(grep -E '^[[:space:]]*image:' "$COMPOSE" \
    | sed -E 's/^[[:space:]]*image:[[:space:]]*//; s/[[:space:]]*$//' \
    | sed -E "s/:\\\$\\{COLAB_RELEASE_TAG[^}]*\\}$/:$ALIAS_TAG/" \
    | grep -v '\$' | sort -u)"
  [ -n "$REQUIRED" ] || { echo "compose 에서 image: 를 하나도 읽지 못했다: $COMPOSE" >&2; exit 1; }
else
  echo "배포 이미지 목록의 정본을 찾지 못했다: $COMPOSE" >&2; exit 1
fi

# 면제된 이미지인가 / 면제 사유
is_exempt() { printf '%s' "$EXEMPT" | cut -f1 | grep -qxF "$1"; }
exempt_reason() { printf '%s' "$EXEMPT" | awk -F'\t' -v i="$1" '$1==i{print $2}'; }

# ── 자체·외부로 가른다 ──────────────────────────────────────────────────────
SELF_IMGS=""; EXT_IMGS=""
while IFS= read -r IMG; do
  [ -n "$IMG" ] || continue
  case "$IMG" in
    "$SELF_PREFIX"*) SELF_IMGS="$SELF_IMGS$IMG"$'\n' ;;
    *)               EXT_IMGS="$EXT_IMGS$IMG"$'\n' ;;
  esac
done <<< "$REQUIRED"

[ -n "$RECORD" ] && : > "$RECORD"
BAD=0; N=0; SKIPPED=0

# 실측은 이미지당 한 번만 한다(기록도 여기서 남긴다).
declare -A LIVE=()
measure() { # $1=이미지
  [ -n "${LIVE[$1]+x}" ] && return
  LIVE["$1"]="$(inspect_digests "$1")"
  [ -n "$RECORD" ] && printf '%s\t%s\n' "$1" "${LIVE[$1]:-[미측정]}" >> "$RECORD"
  return 0
}
while IFS= read -r IMG; do [ -n "$IMG" ] && measure "$IMG"; done <<< "$REQUIRED"

# ══ ① 자체 빌드 — `§5` 원장의 「서빙 중 회차」 행 ═════════════════════════════
SERVING=""
SELF_TODO="$(printf '%s' "$SELF_IMGS" | grep -v '^$')"
if [ -n "$SELF_TODO" ]; then
  if [ ! -f "$DLEDGER" ]; then
    echo "  FAIL  자체 빌드 이미지의 기대값 원장을 찾지 못했다: $DLEDGER"
    echo "        → \`§3\` 표로 되돌아가지 않는다. 원장이 없으면 서빙 회차를 특정할 수 없다"
    BAD=$((BAD+1))
  else
    # 회차 태그를 파일 순서(=시간 순서)대로, 중복 없이. 훑기는 최신부터.
    RELS="$(awk -F'\t' -v a="$ALIAS_TAG" '$3==a && !seen[$2]++ {print $2}' "$DLEDGER" | tac)"
    while IFS= read -r R; do
      [ -n "$R" ] || continue
      HIT=0
      while IFS= read -r IMG; do
        [ -n "$IMG" ] || continue
        NAME="${IMG%:*}"
        EXP="$(awk -F'\t' -v a="$ALIAS_TAG" -v r="$R" -v n="$NAME" '$2==r && $3==a && $4==n {d=$5} END{if(d!="")print d}' "$DLEDGER")"
        [ -n "$EXP" ] || continue
        digest_hit "${LIVE[$IMG]:-}" "$EXP" && { HIT=1; break; }
      done <<< "$SELF_TODO"
      [ "$HIT" -eq 1 ] && { SERVING="$R"; break; }
    done <<< "$RELS"

    if [ -z "$SERVING" ]; then
      echo "  FAIL  서빙 중 릴리스를 원장에서 특정하지 못했다 — 살아 있는 \`:$ALIAS_TAG\` 가 원장의 어느 회차와도 맞지 않는다"
      echo "        원장 $DLEDGER"
      echo "        → **\`§3\` 표로 되돌아가지 않는다.** 기대 기준을 모르는 채 통과시키는 것이 \`〈153〉\` 의 모양이다"
      BAD=$((BAD+1))
    else
      echo "── 자체 빌드 — 기대값 출처: \`§5\` 원장 회차 \`$SERVING\` ($DLEDGER)"
      while IFS= read -r IMG; do
        [ -n "$IMG" ] || continue
        if is_exempt "$IMG"; then
          REASON="$(exempt_reason "$IMG")"
          if [ -n "$REASON" ]; then echo "  SKIP  $IMG — 명시 면제: $REASON"; SKIPPED=$((SKIPPED+1)); continue; fi
          echo "  FAIL  $IMG — 면제 사유가 비어 있다. **사유 없는 면제는 면제가 아니라 검사를 끈 것이다**"
          BAD=$((BAD+1)); continue
        fi
        NAME="${IMG%:*}"
        EXP="$(awk -F'\t' -v a="$ALIAS_TAG" -v r="$SERVING" -v n="$NAME" '$2==r && $3==a && $4==n {d=$5} END{if(d!="")print d}' "$DLEDGER")"
        if [ -z "$EXP" ]; then
          echo "  FAIL  $IMG — 대장에 선언이 없다 (원장 회차 $SERVING 에 이 이미지 행이 없다)"
          echo "        → 배포되는 이미지가 검사 대상에서 빠지는 것은 통과가 아니다"
          BAD=$((BAD+1)); continue
        fi
        N=$((N+1))
        GOT="${LIVE[$IMG]:-}"
        if [ -z "$GOT" ]; then
          echo "  FAIL  $IMG — 실측 불가(이미지가 호스트에 없다). **모르는 것을 일치로 읽지 않는다**"
          BAD=$((BAD+1)); continue
        fi
        if digest_hit "$GOT" "$EXP"; then echo "  PASS  $IMG"
        else
          echo "  FAIL  $IMG"
          echo "        원장 $EXP"
          echo "        실측 $GOT"
          BAD=$((BAD+1))
        fi
      done <<< "$SELF_TODO"
    fi
  fi
fi

# ══ ② 외부 이미지 — `§3` 대장 표 ══════════════════════════════════════════════
EXT_TODO="$(printf '%s' "$EXT_IMGS" | grep -v '^$')"
if [ -n "$EXT_TODO" ]; then
  echo "── 외부 이미지 — 기대값 출처: 대장 \`§3\` ($LEDGER)"
  while IFS= read -r IMG; do
    [ -n "$IMG" ] || continue
    if is_exempt "$IMG"; then
      REASON="$(exempt_reason "$IMG")"
      if [ -n "$REASON" ]; then echo "  SKIP  $IMG — 명시 면제: $REASON"; SKIPPED=$((SKIPPED+1)); continue; fi
      echo "  FAIL  $IMG — 면제 사유가 비어 있다. **사유 없는 면제는 면제가 아니라 검사를 끈 것이다**"
      BAD=$((BAD+1)); continue
    fi
    EXP="$(printf '%s' "$ROWS" | awk -F'\t' -v i="$IMG" '$1==i{print $2}' | tail -1)"
    if [ -z "$EXP" ]; then
      echo "  FAIL  $IMG — 대장에 선언이 없다. 배포되는 이미지가 검사 대상에서 빠지는 것은 통과가 아니다"
      echo "        → digest 한 줄을 대장에 적거나, \`면제: <사유>\` 로 **드러내 놓고** 뺀다"
      BAD=$((BAD+1)); continue
    fi
    N=$((N+1))
    GOT="${LIVE[$IMG]:-}"
    if [ -z "$GOT" ]; then
      echo "  FAIL  $IMG — 실측 불가(이미지가 호스트에 없다). **모르는 것을 일치로 읽지 않는다**"
      BAD=$((BAD+1)); continue
    fi
    if digest_hit "$GOT" "$EXP"; then echo "  PASS  $IMG"
    else
      echo "  FAIL  $IMG"
      echo "        대장 $EXP"
      echo "        실측 $GOT"
      BAD=$((BAD+1))
    fi
  done <<< "$EXT_TODO"
fi

echo
if [ "$BAD" -eq 0 ]; then
  SRC="자체=원장 회차 ${SERVING:-없음} · 외부=대장 §3"
  if [ "$SKIPPED" -gt 0 ]; then
    echo "digest 대조 GREEN — $N 건 일치 · **승인된 면제 ${SKIPPED}건** ($SRC · 무엇을 안 봤는지는 위 SKIP 줄)"
  else
    echo "digest 대조 GREEN — $N 건 전건 일치 · 면제 0 ($SRC · 배포되는 이미지가 전부 실제로 돌았다)"
  fi
  exit 0
fi
cat <<'MSG'
digest 대조 RED.
  · 자체 6종이 어긋나면 **재기동을 계속하지 않는다.** 기대값은 원장이 진다 — 대장 §3 을 고쳐도 판정은 안 바뀐다.
  · 「서빙 회차 미상」은 원장에 없는 이미지가 떠 있다는 뜻이다(수동 빌드·수동 태그 이동). 배포 경로로 다시 올린다.
  · 외부 이미지 불일치가 **의도된 것**이면(업스트림 갱신) 대장 §3 을 갱신하고 `PLAN-SoT §9` 에 등재한다.
  · `cloudflare/cloudflared:latest` 한 줄만 어긋나는 것은 업스트림 갱신일 수 있다 — 그래도 모르고 넘어가지 않는다.
MSG
echo "불일치·미측정·미선언 $BAD 건 (대조 $N 건 · 승인된 면제 ${SKIPPED}건)"
exit 1
