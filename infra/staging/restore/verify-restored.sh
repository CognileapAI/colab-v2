#!/usr/bin/env bash
# 복원 검증 블록 (`R1-RESTORE-DRAFT §4.6`) — **헬스가 아니라 실측이다.**
#
# ⭑⭑ **기대치는 짝 덤프에서 읽는다. 상수를 박지 않는다** (`§4.6-②`).
#    「129 · 12 · 6」은 복원 시점의 기대치이지 상수가 아니다. 여러 문서가 계보 간선을 「5」로
#    적고 있었고 실측은 6 이었다(`〈159〉`) — 상수를 박으면 문서가 낡는 만큼 오라클이 틀린다.
#    그래서 이 파일에는 숫자가 없다. `expectations.sh` 가 덤프를 읽어 그 회차의 값을 만든다.
#
# 사용: verify-restored.sh --platform-dump <…> --ai-dump <…> --owner <소유자롤>
#                          [--pre-digests <P8 기록.tsv>] [--base-url <https://…>]
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HERE/../backup/lib.sh"
load_config
: "${COLAB_STAGING_PG_CONTAINER:=colab_v2_staging_pg}"
: "${COLAB_STAGING_PLATFORM_DB:=colab_platform}"
: "${COLAB_STAGING_AI_DB:=colab_ai}"

PDUMP=""; ADUMP=""; OWNER=""; PRE=""; BASE=""; NO_HEALTH=0; MANUAL_OK=0
while [ $# -gt 0 ]; do
  case "$1" in
    --platform-dump) PDUMP="${2:?}"; shift 2 ;;
    --ai-dump) ADUMP="${2:?}"; shift 2 ;;
    --owner) OWNER="${2:?}"; shift 2 ;;
    --pre-digests) PRE="${2:?}"; shift 2 ;;
    --base-url) BASE="${2:?}"; shift 2 ;;
    # ⭑ 아래 둘은 **명시 승인 플래그**다 (`〈170〉-㉮`). 없으면 해당 항목은 SKIP 이 아니라 RED·미완이다.
    --no-health) NO_HEALTH=1; shift ;;        # 헬스를 일부러 안 본다고 사람이 적은 경우
    --manual-ok) MANUAL_OK=1; shift ;;        # ③-보·⑤ 손검사를 사람이 돌고 통과를 확인한 경우
    *) echo "모르는 인자: $1" >&2; exit 2 ;;
  esac
done
[ -n "$PDUMP" ] && [ -n "$ADUMP" ] && [ -n "$OWNER" ] || { echo "사용법은 머리말을 본다" >&2; exit 2; }

FAILED=0; SKIPPED=0
q() { docker exec "$COLAB_STAGING_PG_CONTAINER" psql -U "$OWNER" -d "$1" -At -c "$2" 2>/dev/null </dev/null; }

cmp_table() { # $1=DB $2=덤프 $3=테이블
  local exp got
  exp="$("$HERE/expectations.sh" "$2" "$3" | cut -f2)"
  [ -n "$exp" ] || { fail "기대치를 못 읽었다: $3 — **지어내지 않는다**"; return; }
  got="$(q "$1" "SELECT count(*) FROM $3")"; got="${got:-측정실패}"
  if [ "$got" = "$exp" ]; then pass "$3 = $got (기대치 = 짝 덤프에서 읽은 값)"
  else fail "$3 = $got · 기대 $exp (짝 덤프 기준)"; fi
}

echo "════ ① 데이터셋 · ⑥ 파일 원장 · ② 계보 간선"
cmp_table "$COLAB_STAGING_PLATFORM_DB" "$PDUMP" d3_dataset
cmp_table "$COLAB_STAGING_PLATFORM_DB" "$PDUMP" d3_file
cmp_table "$COLAB_STAGING_PLATFORM_DB" "$PDUMP" d4_lineage_edge

echo "════ ③ 온톨로지 사전 · 개념 그래프"
# 표 이름의 정본은 ai-service 의 `app/dictionaries.py` 5개 질의다. 여기서 늘리지 않는다.
for T in d9_method_term d9_place_alias d9_topic_synonym d9_concept d9_concept_edge; do
  cmp_table "$COLAB_STAGING_AI_DB" "$ADUMP" "$T"
done
# ⚠ 「사전이 차 있다」와 「읽는 경로가 산다」는 다르다 — `_UnavailableDictionaries` 는
#   기동·헬스 어디에도 신호를 안 내고 **검색 시점에야** RuntimeError 를 던진다(§3-㉲).
echo "  ③-보 읽는 경로: POST /searches 를 정문으로 한 번 던진다 — 이 스크립트는 인증을 쥐지 않으므로"
echo "        런북 §4.6-③-보 를 손으로 돈다. **사전 표가 차 있어도 배선이 끊기면 여기서만 드러난다.**"

echo "════ ④ 이미지 digest"
# 대장(reference/IMAGE-DIGESTS.md)과 대조한다 — 값을 여기 박지 않는다.
if "$HERE/check-image-digests.sh"; then pass "④ 대장 대조 GREEN"; else fail "④ 대장 대조 RED"; fi
if [ -n "$PRE" ] && [ -f "$PRE" ]; then
  NOW="$(mktemp)"; "$HERE/check-image-digests.sh" --record "$NOW" >/dev/null 2>&1 || true
  if diff -q "$PRE" "$NOW" >/dev/null 2>&1; then pass "④-b 복원 전(P8)과 동일"
  else fail "④-b 복원 전과 다르다 — **복원이 아니라 재배포를 한 것이다**"; diff "$PRE" "$NOW" | head -10 | sed 's/^/        /'; fi
  rm -f "$NOW"
else
  fail "④-b P8 기록(--pre-digests)이 없다 — 「복원 전과 같은가」를 잴 수 없다"
fi

echo "════ ⑤ 권한·RLS 가 살아 있다"
# `--no-privileges` 덤프라 **GRANT 가 덤프에 없다.** 앱 롤이 못 읽거나, 반대로 RLS 없이
# 다 읽히면 **둘 다 RED** 다. 이 스크립트는 소유자 롤만 쥐므로 여기서 판정하지 않는다.
echo "  ⚠ 앱 롤 접속은 이 스크립트가 쥐지 않는다(비밀 파일을 읽지 않는다). 런북 §4.6-⑤ 를 손으로 돈다:"
echo "     앱 롤로 붙어 ⓐ 자기 연구실 행이 보이고 ⓑ 타 연구실 행이 0행인지 — **양성·음성 둘 다.**"
FORCE_OFF="$(q "$COLAB_STAGING_PLATFORM_DB" "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind='r' AND c.relrowsecurity=false")"
echo "  INFO  public 의 RLS 미적용 테이블 ${FORCE_OFF:-측정실패}개 — 면제 목록(gates/config/rls-allowlist.toml)과 대조한다"

echo "════ ⑦ 헬스 — 통과 조건이 아니라 최소 전제다"
if [ -n "$BASE" ]; then
  for u in "" core-api frontend pipeline-worker viz-render ai-service; do
    P="/healthz"; [ -n "$u" ] && P="/healthz/$u"
    C="$(curl -s -o /dev/null -w '%{http_code}' "$BASE$P" 2>/dev/null)"
    if [ "$C" = "200" ]; then pass "⑦ $P 200"; else fail "⑦ $P $C"; fi
  done
elif [ "$NO_HEALTH" -eq 1 ]; then
  skip_ack "⑦ 헬스 (--no-health · 사람이 명시한 유예). ⚠ **루트 하나만 보지 않는다** — 자리표시 오리진도 루트 200 을 낸다"
else
  # ⭑ 종전에는 여기서 조용히 SKIP 하고 최종 요약이 「복원 검증 GREEN」이었다. 헬스를 한 건도
  #   안 재고 GREEN 을 말한 것이다 — `〈170〉-㉮` 와 같은 형태라 같이 닫는다.
  fail "⑦ --base-url 을 안 줬다 — 헬스를 한 건도 재지 않았다. 일부러 빼려면 --no-health 로 **명시**한다"
fi

echo
if [ "$FAILED" -ne 0 ]; then
  echo "복원 검증 RED (실패 ${FAILED}건$([ "${SKIPPED:-0}" -ne 0 ] && echo " · 승인된 SKIP ${SKIPPED}건")) — 다음 수는 §4.7 되돌림의 되돌림이다"
  exit 1
fi
# ⭑ **손검사 2건(③-보 · ⑤)을 안 돌고 「GREEN」이라 말하지 않는다** (`〈170〉-㉮`).
#   종전 요약은 「복원 검증 GREEN — 단, ③-보 와 ⑤ 는 손으로…」였다. 그 「단,」이 곧 SKIP 이고,
#   그럼에도 종료코드가 0 이었다. 안 본 것이 있으면 **성공 판정이 아니다** — exit 3(미완)로 가른다.
if [ "$MANUAL_OK" -eq 1 ]; then
  echo "복원 검증 GREEN — 자동분 전건 통과 ＋ 손검사 2건(③-보·⑤) 사람이 확인(--manual-ok)$([ "${SKIPPED:-0}" -ne 0 ] && echo " · 승인된 SKIP ${SKIPPED}건")"
  exit 0
fi
echo "복원 검증 **미완** — 자동분은 전건 통과했으나 손검사 2건(③-보 POST /searches · ⑤ 앱 롤 양성·음성)이 아직 판정되지 않았다."
echo "  런북 §4.6-③-보 · §4.6-⑤ 를 돌고, 통과했으면 --manual-ok 로 다시 부른다. (exit 3 = GREEN 아님)"
exit 3
