#!/usr/bin/env bash
# 릴리스 태그를 찍는다 (규칙 6 · `docs/BRANCHING.md` §3 · WU-D2).
#
#   infra/dev/tag-release.sh dev [DIST]    → dev-YYYYMMDD-N  (N = 같은 날 기존 태그 수 ＋1)
#   infra/dev/tag-release.sh prod [DIST]   → prod-YYYYMMDD   (기존 규약 · `PLAN-SoT §9-㊻`)
#
# 부르는 때 = **`deploy_doctor` 전건 통과 뒤, 사람이**. dev 에는 원장이 없어 「안전 복구 세대」가
# 이미지 잔존에만 기대고 있었다 — 태그가 그 자리를 닫는다(설계트리 Q3).
# ⭑ EC2 를 접촉하지 않는다. 대상 sha 는 **로컬 `dist/colab-v2-dev.sha`** 이고 `CURRENT_SHA` 는 읽지 않는다.
# ⭑ push 하지 않는다 — 명령만 출력하고 원격 반영은 사람이 한 줄로 한다(비가역 원격 행위).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
MODE="${1:?인자가 필요하다: dev | prod}"
DIST="${2:-$REPO/dist}"
case "$MODE" in dev|prod) ;; *) echo "인자는 dev | prod 다: $MODE" >&2; exit 64 ;; esac
# ⭑ ⟨2026-09-13⟩ **sha 파일은 모드별이다.** 종전에는 `prod` 도 `colab-v2-dev.sha` 를 읽었고
#   (`build.sh` 는 `colab-v2-<모드>.sha` 를 쓴다), 그래서 prod 만 빌드한 회차는 태그를 못 찍거나
#   **dev 의 sha 에 prod 태그가 붙었다.** 태그가 가리키는 커밋이 배포 원천 판정의 입력이다.
SHA_FILE="$DIST/colab-v2-$MODE.sha"

[ -f "$SHA_FILE" ] || { echo "반입한 sha 를 모른다: $SHA_FILE 이 없다 — build.sh 먼저" >&2; exit 65; }
SHA="$(cat "$SHA_FILE")"
[ -n "$SHA" ] || { echo "sha 파일이 비었다: $SHA_FILE" >&2; exit 65; }
FULL_SHA="$(git -C "$REPO" rev-parse --verify "$SHA^{commit}")" || exit 78
if [ "$MODE" = dev ]; then
  if [ -z "${COLAB_RELEASE_PRE_EVIDENCE:-}" ] || [ -z "${COLAB_RELEASE_POST_EVIDENCE:-}" ]; then
    echo "release pre/post evidence required before tag" >&2; exit 78
  fi
  FULL_SHA="$(git -C "$REPO" rev-parse --verify "$SHA^{commit}")" || exit 78
  python3 "$REPO/scripts/harness/release_evidence.py" post --pre "$COLAB_RELEASE_PRE_EVIDENCE" --post "$COLAB_RELEASE_POST_EVIDENCE" --sha "$FULL_SHA" --environment dev --root "$REPO"
else
  [ -n "${COLAB_RELEASE_PRE_EVIDENCE:-}" ] || { echo 'prod tag requires pre evidence' >&2; exit 78; }
  python3 "$REPO/scripts/harness/release_evidence.py" pre --pre "$COLAB_RELEASE_PRE_EVIDENCE" --sha "$FULL_SHA" --environment prod --root "$REPO"
fi
if [ "${COLAB_RELEASE_DRY_RUN:-0}" = 1 ]; then
  echo "dry-run: no fetch, tag or push; candidate=$SHA"; exit 0
fi

# 태그도 `main` 조상만 가리킨다 — 반입 게이트와 같은 판정기준(규칙 1).
git -C "$REPO" fetch -q origin main \
  || { echo "origin 조회 실패 — 진행 금지" >&2; exit 78; }
git -C "$REPO" merge-base --is-ancestor "$SHA" origin/main \
  || { echo "sha 가 origin/main 조상이 아니다: $SHA — 태그는 배포 원천만 가리킨다" >&2; exit 65; }

DAY="$(date +%Y%m%d)"
case "$MODE" in
  # `wc -l` 로 센다 — `grep -c .` 는 0건일 때 exit 1 이라 `set -e` 가 첫 태그를 막는다.
  dev)  N=$(( $(git -C "$REPO" tag -l "dev-$DAY-*" | wc -l) + 1 )); TAG="dev-$DAY-$N" ;;
  prod) TAG="prod-$DAY" ;;
esac

if git -C "$REPO" rev-parse -q --verify "refs/tags/$TAG" >/dev/null; then
  # ⭑ ⟨2026-09-13⟩ prod 이름에는 회차 번호가 없다(`prod-YYYYMMDD`) — 같은 날 다시 부르면
  #   반드시 여기로 온다. **같은 sha 를 가리키면 그 태그를 그대로 쓴다**(반입 게이트 ②는
  #   `git tag --points-at` 로 태그 존재만 본다 — 재실행이 막힐 이유가 없다).
  #   ⛔ **다른 sha 면 거절한다** — 태그를 옮기면 그날의 배포 원천 기록이 사라진다.
  EXISTING="$(git -C "$REPO" rev-parse --short=12 "refs/tags/$TAG^{commit}")"
  if [ "$EXISTING" = "$SHA" ]; then
    echo "태그가 이미 있다(같은 sha — 재사용): $TAG → $SHA"
    echo "원격 반영은 사람이 한 줄로 — git push origin $TAG"
    exit 0
  fi
  echo "태그가 이미 있다: $TAG → $EXISTING (지금 후보는 다른 sha 다: $SHA)" >&2
  echo "  태그를 옮기지 않는다 — 그날의 배포 원천 기록이 사라진다" >&2
  exit 65
fi

if [ "$MODE" = dev ]; then
  git -C "$REPO" tag -a "$TAG" "$FULL_SHA" -m "Verified dev release; pre=$COLAB_RELEASE_PRE_EVIDENCE post=$COLAB_RELEASE_POST_EVIDENCE"
else
  git -C "$REPO" tag "$TAG" "$SHA"
fi
echo "태그 생성(로컬): $TAG → $SHA"
echo "원격 반영은 사람이 한 줄로 — git push origin $TAG"
