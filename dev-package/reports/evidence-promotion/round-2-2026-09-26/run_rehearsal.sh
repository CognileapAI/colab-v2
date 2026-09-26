#!/usr/bin/env bash
# 확정값과 공존하는 초안(타일 21~24 region: 확정 타일 코드 ↔ 초안 「한반도」)의 승격 리허설 두 벌 —
# ① 대체 허가 없이(거절 · conflictsWithReviewed action=refused · 기대 종료코드 1)
# ② --allow-replace bbox-korea-peninsula(대체 · action=replace · 기대 종료코드 0).
# 새 일회용 postgres(포트 공개 없음)에 --seed-dev-like 로 싣고 PUT 본문만 만든다. 보내지 않는다.
#
#   bash run_rehearsal.sh <payload> <산출 디렉터리>
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../../.." && pwd)"
PAYLOAD="$1"; OUT="$2"
C="rr2_rehearse_$$"
docker run -d --rm --name "$C" -e POSTGRES_PASSWORD=x -e POSTGRES_HOST_AUTH_METHOD=trust \
  -e POSTGRES_DB=colab_platform postgres:16-alpine >/dev/null || { echo "준비 실패: 컨테이너"; exit 78; }
trap 'docker rm -f "$C" >/dev/null 2>&1' EXIT
for _ in $(seq 1 60); do docker exec "$C" pg_isready -U postgres -d colab_platform -q && break; sleep 1; done
sleep 2
URL="$(CONTAINER="$C" DB=colab_platform bash "$REPO/services/core-api/tests/fixtures/setup-db.sh" | tail -1 | cut -f1)"
[ -n "$URL" ] || { echo "준비 실패: setup-db"; exit 78; }
cd "$REPO" || exit 78
PY=services/core-api/.venv/bin/python
TOOL=eval/k4-search/measure_draft_contribution.py
SEED="$(mktemp -d)"
"$PY" "$TOOL" "$URL" --i-know-this-is-disposable --seed-dev-like --payload "$PAYLOAD" --round "리허설 시드" \
  --output "$SEED/seed" >/dev/null
echo "seed rc=$?"
rm -rf "$SEED"
"$PY" "$TOOL" "$URL" --i-know-this-is-disposable --payload "$PAYLOAD" \
  --rehearse-promote bbox-korea-peninsula --output "$OUT/refused"
echo "refused rc=$?"
"$PY" "$TOOL" "$URL" --i-know-this-is-disposable --payload "$PAYLOAD" \
  --rehearse-promote bbox-korea-peninsula --allow-replace bbox-korea-peninsula --output "$OUT/allow-replace"
echo "allow-replace rc=$?"
