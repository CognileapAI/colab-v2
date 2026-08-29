#!/usr/bin/env bash
# 이미지 digest 대조 — **대장(`dev-package/reference/IMAGE-DIGESTS.md`)을 읽는다.**
#
# ⭑ digest 값을 이 스크립트에 박지 않는다. 대장이 정본이고 다른 문서는 가리키기만 한다
#   (`IMAGE-DIGESTS.md §4-4`). 값을 두 곳에 적으면 갈라지고, 갈라진 대조는 대조가 아니다.
#
# 왜 헬스로 대신할 수 없는가: `〈153〉` 때 배선만 바꾸고 **옛 이미지로 올려** ai-service 만
# healthy 였고 사전 DB 가 `None` 으로 조용히 비었다. **죽은 쪽은 바로 보이고 살아 있는 쪽이 속인다.**
#
# 사용: check-image-digests.sh [--ledger <대장.md>] [--record <출력.tsv>] [--compose <compose.yml>]
#   `--record` 는 복원 **전** 상태를 적어 두는 용도다(`R1-RESTORE-DRAFT §4.0 P8`).
#   `--compose` 는 **배포되는 이미지 목록의 정본**이다(기본 `infra/staging/compose.i2.yml`).
#
# ⭑ 세 상태 (Ted 판정 2026-08-29 · `CLAUDE.md §4`):
#     ⓐ digest 가 선언되어 있다        → **대조한다**
#     ⓑ `면제: <사유>` 로 명시 면제했다 → **통과하되 건수를 요약줄에 드러낸다**
#     ⓒ 아무 말도 없다(미선언)          → **RED**
#   ⓒ 가 없던 것이 결함이었다 — 배포되는 이미지가 대장에 없으면 **검사 대상에서 조용히 빠지고**
#   남은 행만 보고 「전건 일치 GREEN」이 나왔다. 검사 범위를 대장이 스스로 정하면 검사가 아니다.
# 종료코드: 0 = 전건 일치(＋승인된 면제) / 1 = 불일치·미측정·미선언 / 2 = 사용법 오류
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
LEDGER="$REPO/dev-package/reference/IMAGE-DIGESTS.md"
RECORD=""
COMPOSE="$REPO/infra/staging/compose.i2.yml"
ALIAS_TAG="${COLAB_DIGEST_ALIAS_TAG:-i2}"
while [ $# -gt 0 ]; do
  case "$1" in
    --ledger) LEDGER="${2:?}"; shift 2 ;;
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

# 대장의 표 행: `| \`이미지\` | \`sha256:…\` |`
ROWS="$(grep -E '^\| *`[^`]+` *\| *`sha256:[0-9a-f]{64}` *\|' "$LEDGER" \
        | sed -E 's/^\| *`([^`]+)` *\| *`(sha256:[0-9a-f]{64})` *\|.*/\1\t\2/')"
[ -n "$ROWS" ] || { echo "대장에서 digest 행을 하나도 읽지 못했다 — 표 형식이 바뀌었는가" >&2; exit 1; }

# ── ⓑ 명시 면제 행: `| \`이미지\` | 면제: <사유> |` ─────────────────────────────
# **사유가 비면 면제가 아니다.** 사유 없는 면제는 검사를 끄는 스위치일 뿐이다.
EXEMPT="$(grep -E '^\| *`[^`]+` *\| *면제:' "$LEDGER" \
          | sed -E 's/^\| *`([^`]+)` *\| *면제: *(.*[^ ]|) *\|.*/\1\t\2/')"

# ── 배포되는 이미지 목록 = compose 의 `image:` (정본) ────────────────────────
# 대장이 자기 검사 범위를 정하지 못하게 한다. 실제로 뜨는 것이 검사 대상이다.
REQUIRED=""
if [ -f "$COMPOSE" ]; then
  REQUIRED="$(grep -E '^[[:space:]]*image:' "$COMPOSE" \
    | sed -E 's/^[[:space:]]*image:[[:space:]]*//; s/[[:space:]]*$//' \
    | sed -E "s/:\\\$\\{COLAB_RELEASE_TAG[^}]*\\}$/:$ALIAS_TAG/" \
    | grep -v '\$' | sort -u)"
  [ -n "$REQUIRED" ] || { echo "compose 에서 image: 를 하나도 읽지 못했다: $COMPOSE" >&2; exit 1; }
else
  echo "배포 이미지 목록의 정본을 찾지 못했다: $COMPOSE" >&2; exit 1
fi

[ -n "$RECORD" ] && : > "$RECORD"
BAD=0; N=0
while IFS=$'\t' read -r IMG EXP; do
  [ -n "$IMG" ] || continue
  N=$((N+1))
  GOT="$(inspect_digests "$IMG")"
  [ -n "$RECORD" ] && printf '%s\t%s\n' "$IMG" "${GOT:-[미측정]}" >> "$RECORD"
  if [ -z "$GOT" ]; then
    echo "  FAIL  $IMG — 실측 불가(이미지가 호스트에 없다). **모르는 것을 일치로 읽지 않는다**"
    BAD=$((BAD+1)); continue
  fi
  # RepoDigest 는 `repo@sha256:…` 형태라 `@` 뒤만 본다.
  if printf '%s' "$GOT" | tr ' ' '\n' | sed 's/.*@//' | grep -qx "$EXP"; then
    echo "  PASS  $IMG"
  else
    echo "  FAIL  $IMG"
    echo "        대장 $EXP"
    echo "        실측 $GOT"
    BAD=$((BAD+1))
  fi
done <<< "$ROWS"

# ── ⓑ·ⓒ 배포 목록과 대장을 맞춘다 ──────────────────────────────────────────
SKIPPED=0
while IFS= read -r IMG; do
  [ -n "$IMG" ] || continue
  printf '%s' "$ROWS" | cut -f1 | grep -qxF "$IMG" && continue      # ⓐ 위에서 이미 대조했다
  REASON="$(printf '%s' "$EXEMPT" | awk -F'\t' -v i="$IMG" '$1==i{print $2}')"
  if printf '%s' "$EXEMPT" | cut -f1 | grep -qxF "$IMG"; then
    if [ -n "$REASON" ]; then
      echo "  SKIP  $IMG — 명시 면제: $REASON"
      SKIPPED=$((SKIPPED+1)); continue
    fi
    echo "  FAIL  $IMG — 면제 사유가 비어 있다. **사유 없는 면제는 면제가 아니라 검사를 끈 것이다**"
    BAD=$((BAD+1)); continue
  fi
  echo "  FAIL  $IMG — 대장에 선언이 없다. 배포되는 이미지가 검사 대상에서 빠지는 것은 통과가 아니다"
  echo "        → digest 한 줄을 대장에 적거나, \`면제: <사유>\` 로 **드러내 놓고** 뺀다"
  BAD=$((BAD+1))
done <<< "$REQUIRED"

echo
if [ "$BAD" -eq 0 ]; then
  if [ "$SKIPPED" -gt 0 ]; then
    echo "digest 대조 GREEN — $N 건 일치 · **승인된 면제 ${SKIPPED}건** (무엇을 안 봤는지는 위 SKIP 줄)"
  else
    echo "digest 대조 GREEN — $N 건 전건 일치 · 면제 0 (배포되는 이미지가 전부 실제로 돌았다)"
  fi
  exit 0
fi
cat <<'MSG'
digest 대조 RED.
  · 불일치가 **의도된 것**이면(재빌드·업스트림 갱신) 대장을 먼저 갱신하고 `PLAN-SoT §9` 에 등재한다.
  · 의도한 적이 없으면 **재기동을 계속하지 않는다.** 헬스 200 은 이 불일치를 잡지 못한다.
  · `cloudflare/cloudflared:latest` 한 줄만 어긋나는 것은 업스트림 갱신일 수 있다 — 그래도 모르고 넘어가지 않는다.
MSG
echo "불일치·미측정·미선언 $BAD 건 (대조 $N 건 · 승인된 면제 ${SKIPPED}건)"
exit 1
