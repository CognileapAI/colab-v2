#!/usr/bin/env bash
# 이미지 digest 대조 — **대장(`dev-package/reference/IMAGE-DIGESTS.md`)을 읽는다.**
#
# ⭑ digest 값을 이 스크립트에 박지 않는다. 대장이 정본이고 다른 문서는 가리키기만 한다
#   (`IMAGE-DIGESTS.md §4-4`). 값을 두 곳에 적으면 갈라지고, 갈라진 대조는 대조가 아니다.
#
# 왜 헬스로 대신할 수 없는가: `〈153〉` 때 배선만 바꾸고 **옛 이미지로 올려** ai-service 만
# healthy 였고 사전 DB 가 `None` 으로 조용히 비었다. **죽은 쪽은 바로 보이고 살아 있는 쪽이 속인다.**
#
# 사용: check-image-digests.sh [--ledger <대장.md>] [--record <출력.tsv>]
#   `--record` 는 복원 **전** 상태를 적어 두는 용도다(`R1-RESTORE-DRAFT §4.0 P8`).
# 종료코드: 0 = 전건 일치 / 1 = 하나라도 불일치·미측정 / 2 = 사용법 오류
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
LEDGER="$REPO/dev-package/reference/IMAGE-DIGESTS.md"
RECORD=""
while [ $# -gt 0 ]; do
  case "$1" in
    --ledger) LEDGER="${2:?}"; shift 2 ;;
    --record) RECORD="${2:?}"; shift 2 ;;
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

echo
if [ "$BAD" -eq 0 ]; then echo "digest 대조 GREEN — $N 건 전건 일치"; exit 0; fi
cat <<'MSG'
digest 대조 RED.
  · 불일치가 **의도된 것**이면(재빌드·업스트림 갱신) 대장을 먼저 갱신하고 `PLAN-SoT §9` 에 등재한다.
  · 의도한 적이 없으면 **재기동을 계속하지 않는다.** 헬스 200 은 이 불일치를 잡지 못한다.
  · `cloudflare/cloudflared:latest` 한 줄만 어긋나는 것은 업스트림 갱신일 수 있다 — 그래도 모르고 넘어가지 않는다.
MSG
echo "불일치·미측정 $BAD 건 / $N 건"
exit 1
