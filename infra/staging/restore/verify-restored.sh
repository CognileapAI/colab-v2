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

# ── 세는 롤은 소유자 롤이 **아니다** (2026-09-03 실측 · `sessions/WINDOW-20260903-D2.md §2`) ──
# ⛔ 종전 `cmp_table` 은 `-U "$OWNER"` 로 셌다. 그런데 `db/platform/schema.sql` 은 연구실 경계
#    테이블에 **FORCE ROW LEVEL SECURITY** 를 건다 — FORCE 는 **테이블 소유자에게도 적용된다.**
#    그래서 살아 있는 staging 에서 `app.current_lab` 없이 소유자 롤로 세면 `d3_dataset` 이
#    **언제나 0** 이고, 짝 덤프의 기대치가 13 이면 **복원이 완벽해도 RED** 가 나온다.
#    실측(2026-09-03 · 복원 전 · 읽기 전용) = 소유자 롤 `SELECT count(*) FROM d3_dataset` → **0**,
#    같은 접속에서 `SET app.current_lab='<연구실>'` 뒤 → **13**. 덤프 기대치도 13.
# ⭑ 이 결함이 8일 넘게 숨은 이유 = **제자리 경로가 한 번도 돌지 않았다.** 리허설
#    (`rehearsal.sh` · `throwaway-stack.sh`)은 일회용 postgres 에 `-U postgres` 로 붙고
#    **superuser 는 RLS 를 무조건 건너뛴다.** 리허설 GREEN 은 이 자리를 재지 않았다.
# ⟹ 세는 것은 **superuser** 로 한다. 검사 범위를 줄인 것이 아니다 — 같은 표·같은 기대치이고,
#    **경계가 살아 있는가는 ⑤ 가 앱 롤로 따로 잰다**(양성·음성 둘 다). 「몇 줄이 들어왔나」와
#    「경계가 서 있나」는 다른 질문이고, 한 롤로 둘 다 재려던 것이 결함의 원인이었다.
: "${COLAB_VERIFY_COUNT_ROLE:=postgres}"
# ⚠ psql `-c` 는 SQL 문자열 안의 `\t` 를 탭으로 바꾸지 않는다 — 두 값을 한 줄로 붙일 때는
#   `chr(9)` 를 쓴다. `'\t'` 로 적으면 `cut -f1` 이 줄 전체를 가져간다(2026-09-03 실측).
qc() { docker exec "$COLAB_STAGING_PG_CONTAINER" psql -U "$COLAB_VERIFY_COUNT_ROLE" -d "$1" -At -c "$2" 2>/dev/null </dev/null; }
# 셀프테스트용 주입구 — docker 없이 fail-closed 를 증명해야 한다(`selftest-restore.sh`).
[ -n "${COLAB_VERIFY_COUNT_HOOK:-}" ] && qc() { "$COLAB_VERIFY_COUNT_HOOK" "$1" "$2"; }

# ⛔ **0 을 「부재」로 읽지 않는다.** 세는 롤이 superuser 가 아닌데 그 표에 FORCE RLS 가 걸려
#    있으면 0 은 「없다」가 아니라 「못 봤다」다. 그 둘을 가르지 못하면 위 결함이 그대로 돌아온다.
count_role_can_see() { # $1=DB $2=테이블 → 0 = 볼 수 있다 / 1 = RLS 에 걸린다 / 2 = 판정 불가
  local v
  v="$(qc "$1" "SELECT (SELECT rolsuper FROM pg_roles WHERE rolname=current_user)::text||' '||coalesce((SELECT c.relforcerowsecurity FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relname='$2')::text,'?')")"
  # ⚠ psql 의 `boolean::text` 는 `t`/`f` 가 아니라 **`true`/`false`** 다. 짧은 쪽으로 적으면
  #   모든 표가 「판정 불가」로 떨어진다(2026-09-03 실측 — 첫 판이 그렇게 8건 FAIL 을 냈다).
  case "$v" in
    true\ *)      return 0 ;;          # superuser — RLS 를 건너뛴다
    false\ false) return 0 ;;          # FORCE 아님 — 소유자도 다 본다
    false\ true)  return 1 ;;          # 걸린다
    *)            return 2 ;;
  esac
}

cmp_table() { # $1=DB $2=덤프 $3=테이블
  local exp got
  exp="$("$HERE/expectations.sh" "$2" "$3" | cut -f2)"
  [ -n "$exp" ] || { fail "기대치를 못 읽었다: $3 — **지어내지 않는다**"; return; }
  count_role_can_see "$1" "$3"; case $? in
    1) fail "$3 — 세는 롤($COLAB_VERIFY_COUNT_ROLE)이 FORCE RLS 에 걸린다. **0 을 부재로 읽지 않는다** — COLAB_VERIFY_COUNT_ROLE 을 superuser 로 준다"; return ;;
    2) fail "$3 — 세는 롤의 성질·표의 RLS 상태를 읽지 못했다. **모르는 채로 세지 않는다**"; return ;;
  esac
  got="$(qc "$1" "SELECT count(*) FROM $3")"; got="${got:-측정실패}"
  if [ "$got" = "$exp" ]; then pass "$3 = $got (기대치 = 짝 덤프에서 읽은 값 · 세는 롤 $COLAB_VERIFY_COUNT_ROLE)"
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
# ── ③-보 **읽는 경로** — 자동화됐다 (2026-09-03 · `STAGING-WINDOW-RUNBOOK §4` 손검사 2건 중 하나) ──
# 「사전 표가 차 있다」와 「읽는 경로가 산다」는 다른 사실이다. `_UnavailableDictionaries` 는
# 기동·헬스 어디에도 신호를 안 내고 **검색 시점에야** RuntimeError 를 던진다(초안 §3-㉲).
# ⭑ **베어러가 필요 없다** — `ai-service` 직행이다(정문 중계 다리는 `〈255〉` 가 stage 3 으로 뺐다).
# ⭑ **상태코드만 보지 않는다.** 판정 = 200 ＋ `degraded:false` ＋ **원 질의에 없던 확장 낱말 ≥1**
#   (`〈255〉-⑵`). 사전이 끊겨도 200 은 나온다 — 그것이 이 검사가 존재하는 이유다.
# ⭑ **질의를 상수로 박지 않는다.** 되돌린 `d9_topic_synonym` 에서 `synonym <> topic` 인 행을
#   골라 그 `synonym` 을 질의로 쓰고 `topic` 이 확장으로 돌아오는지 본다 — 기대치를 실물에서 읽는다.
: "${COLAB_STAGING_AI_CONTAINER:=colab_v2_staging_ai_service}"
search_probe() { # $1=labId $2=labName $3=accountId $4=query → "<status>\t<degraded>\t<확장낱말수>"
  if [ -n "${COLAB_VERIFY_SEARCH_HOOK:-}" ]; then "$COLAB_VERIFY_SEARCH_HOOK" "$1" "$2" "$3" "$4"; return; fi
  docker exec -e L="$1" -e N="$2" -e A="$3" -e Q="$4" "$COLAB_STAGING_AI_CONTAINER" python -c '
import json, os, urllib.request, urllib.error
q = os.environ["Q"]
body = json.dumps({"scope": {"labId": os.environ["L"], "labName": os.environ["N"]}, "query": q}).encode()
req = urllib.request.Request("http://127.0.0.1:8200/searches", data=body, headers={
    "Content-Type": "application/json",
    "X-CoLAB-Account": os.environ["A"], "X-CoLAB-Lab": os.environ["L"]})
try:
    with urllib.request.urlopen(req, timeout=15) as f:
        st, doc = f.status, json.loads(f.read().decode())
except urllib.error.HTTPError as e:
    print("%d\t?\t0" % e.code); raise SystemExit(0)
except Exception:
    print("0\t?\t0"); raise SystemExit(0)
deg = doc.get("degraded")
terms = doc.get("interpretation", {}).get("terms") or []
# **원 질의에 없던 낱말만 센다** — 질문을 되돌려준 것을 확장으로 세지 않는다.
extra = [t for t in terms if t and t not in q]
print("%d\t%s\t%d" % (st, "false" if deg is False else ("true" if deg is True else "?"), len(extra)))
' 2>/dev/null </dev/null
}

echo "  ── ③-보 읽는 경로 (ai-service 직행 · 자동)"
S3_SYN="$(qc "$COLAB_STAGING_AI_DB" "SELECT synonym||chr(9)||topic FROM d9_topic_synonym WHERE synonym <> topic ORDER BY synonym LIMIT 1")"
S3_LAB="$(qc "$COLAB_STAGING_PLATFORM_DB" "SELECT a.lab_id||chr(9)||l.name||chr(9)||a.id FROM d1_account a JOIN d1_lab l ON l.id=a.lab_id ORDER BY a.id LIMIT 1")"
if [ -z "$S3_SYN" ]; then
  # ⛔ 조용히 넘어가지 않는다. 확장을 증명할 재료가 없으면 **검사 대상 0 건**이고, 그것은 통과가 아니다.
  fail "③-보 확장을 증명할 동의어 행이 없다(d9_topic_synonym 에 synonym<>topic 0건) — **대상 0 을 통과로 세지 않는다**"
elif [ -z "$S3_LAB" ]; then
  fail "③-보 질의를 던질 연구실·주체를 못 골랐다(d1_account 0건) — **모르는 채로 통과시키지 않는다**"
else
  S3_Q="$(printf '%s' "$S3_SYN" | cut -f1)"; S3_T="$(printf '%s' "$S3_SYN" | cut -f2)"
  S3_L="$(printf '%s' "$S3_LAB" | cut -f1)"; S3_N="$(printf '%s' "$S3_LAB" | cut -f2)"; S3_A="$(printf '%s' "$S3_LAB" | cut -f3)"
  S3_OUT="$(search_probe "$S3_L" "$S3_N" "$S3_A" "$S3_Q")"
  S3_ST="$(printf '%s' "$S3_OUT" | cut -f1)"; S3_DEG="$(printf '%s' "$S3_OUT" | cut -f2)"; S3_EXP="$(printf '%s' "$S3_OUT" | cut -f3)"
  if [ "$S3_ST" = "200" ] && [ "$S3_DEG" = "false" ] && [ "${S3_EXP:-0}" -ge 1 ] 2>/dev/null; then
    pass "③-보 POST /searches 200 · degraded=false · 확장 낱말 ${S3_EXP}건 (질의 「$S3_Q」 → 「$S3_T」 기대)"
  else
    fail "③-보 POST /searches — 상태 ${S3_ST:-측정실패} · degraded=${S3_DEG:-?} · 확장 낱말 ${S3_EXP:-0}건 (셋 다 서야 통과다 · 질의 「$S3_Q」)"
  fi
fi

echo "════ ④ 이미지 digest"
# 대장(reference/IMAGE-DIGESTS.md)과 대조한다 — 값을 여기 박지 않는다.
# 셀프테스트 주입구 — docker 없이 나머지 판정을 증명해야 한다(`check-image-digests.sh` 의
# COLAB_DIGEST_INSPECT 와 같은 성질의 이음매다. 기본값은 실물 대조기다).
: "${COLAB_VERIFY_DIGEST_CMD:=$HERE/check-image-digests.sh}"
if "$COLAB_VERIFY_DIGEST_CMD"; then pass "④ 대장 대조 GREEN"; else fail "④ 대장 대조 RED"; fi
if [ -n "$PRE" ] && [ -f "$PRE" ]; then
  NOW="$(mktemp)"; "$COLAB_VERIFY_DIGEST_CMD" --record "$NOW" >/dev/null 2>&1 || true
  if diff -q "$PRE" "$NOW" >/dev/null 2>&1; then pass "④-b 복원 전(P8)과 동일"
  else fail "④-b 복원 전과 다르다 — **복원이 아니라 재배포를 한 것이다**"; diff "$PRE" "$NOW" | head -10 | sed 's/^/        /'; fi
  rm -f "$NOW"
else
  fail "④-b P8 기록(--pre-digests)이 없다 — 「복원 전과 같은가」를 잴 수 없다"
fi

echo "════ ⑤ 권한·RLS 가 살아 있다 (앱 롤 · 양성·음성 둘 다 · 자동)"
# `--no-privileges` 덤프라 **GRANT 가 덤프에 없다.** 앱 롤이 못 읽거나, 반대로 RLS 없이
# 다 읽히면 **둘 다 RED** 다 — 그 둘을 가르려면 **앱 롤로 실제로 붙어야** 한다.
# ⭑ 2026-09-03 자동화(`STAGING-WINDOW-RUNBOOK §4` 손검사 2건 중 나머지 하나).
#   ⚠ **`DROP SCHEMA public CASCADE` 는 스키마 USAGE 와 `ALTER DEFAULT PRIVILEGES` 항목까지
#   같이 지운다.** 그래서 제자리 복원 뒤 앱 롤은 권한이 **0** 이고, 복구 수단은
#   `infra/staging/db-bootstrap.sh app-grants`(정본 = `services/core-api/ops/app-role.sql`)다.
#   이 검사가 RED 면 「복원이 틀렸다」가 아니라 **「재부여를 안 했다」**일 수 있다 — 사유를 갈라 적는다.
: "${COLAB_VERIFY_APP_ROLE:=colab_app}"
: "${COLAB_VERIFY_AI_APP_ROLE:=colab_ai_app}"
qa() { # $1=DB $2=롤 $3=SQL — 앱 롤로 잰다
  if [ -n "${COLAB_VERIFY_APPSQL_HOOK:-}" ]; then "$COLAB_VERIFY_APPSQL_HOOK" "$1" "$2" "$3"; return; fi
  docker exec "$COLAB_STAGING_PG_CONTAINER" psql -U "$2" -d "$1" -At -c "$3" 2>/dev/null </dev/null | tail -1
}

# ⓪ 앱 롤의 성질 — 여기가 깨지면 아래 음성 시험이 **거짓 green** 이 된다(`ops/app-role.sql` 머리말).
APPPROP="$(qc "$COLAB_STAGING_PLATFORM_DB" "SELECT coalesce((SELECT (rolsuper OR rolbypassrls)::text FROM pg_roles WHERE rolname='$COLAB_VERIFY_APP_ROLE'),'없음')")"
case "$APPPROP" in
  false) pass "⑤-0 앱 롤 $COLAB_VERIFY_APP_ROLE 은 superuser 도 BYPASSRLS 도 아니다" ;;
  true)  fail "⑤-0 앱 롤 $COLAB_VERIFY_APP_ROLE 이 superuser 이거나 BYPASSRLS 다 — **경계 음성 시험이 거짓 green 이 된다**" ;;
  *)     fail "⑤-0 앱 롤 $COLAB_VERIFY_APP_ROLE 이 없다 — 앱이 붙을 주체가 없다" ;;
esac

# ⓐ 양성·ⓑ 음성 — **모수를 실물에서 고른다.** 행이 있는 연구실과 다른 연구실을 superuser 로 뽑는다.
LABROW="$(qc "$COLAB_STAGING_PLATFORM_DB" "SELECT lab_id||chr(9)||count(*)::text FROM d3_dataset GROUP BY lab_id ORDER BY count(*) DESC, lab_id LIMIT 1")"
LAB_A="$(printf '%s' "$LABROW" | cut -f1)"; LAB_N="$(printf '%s' "$LABROW" | cut -f2)"
LAB_B="$(qc "$COLAB_STAGING_PLATFORM_DB" "SELECT id FROM d1_lab WHERE id <> '${LAB_A:-x}' ORDER BY id LIMIT 1")"
if [ -z "$LAB_A" ] || [ "${LAB_N:-0}" -lt 1 ] 2>/dev/null; then
  # ⛔ 행이 0 이면 양성 시험이 **아무것도 증명하지 않는다.** 통과로 세지 않는다.
  fail "⑤ 데이터셋 행이 있는 연구실이 없다 — 양성 시험의 모수가 0 이다. **대상 0 을 통과로 세지 않는다**"
elif [ -z "$LAB_B" ]; then
  fail "⑤ 비교할 다른 연구실이 없다(d1_lab 1건) — **음성 시험 없이 경계가 섰다고 말하지 않는다**"
else
  GOT_A="$(qa "$COLAB_STAGING_PLATFORM_DB" "$COLAB_VERIFY_APP_ROLE" "SET app.current_lab='$LAB_A'; SELECT count(*) FROM d3_dataset")"
  if [ "$GOT_A" = "$LAB_N" ]; then pass "⑤-a 양성 — 앱 롤이 자기 연구실 행 ${GOT_A}건을 본다 (superuser 실측과 같다)"
  else fail "⑤-a 양성 실패 — 앱 롤이 본 것 ${GOT_A:-측정실패} · 실제 $LAB_N. GRANT 가 없거나(제자리 복원 뒤 재부여 누락) 정책이 과하다"; fi

  GOT_B="$(qa "$COLAB_STAGING_PLATFORM_DB" "$COLAB_VERIFY_APP_ROLE" "SET app.current_lab='$LAB_B'; SELECT count(*) FROM d3_dataset WHERE lab_id='$LAB_A'")"
  if [ "$GOT_B" = "0" ]; then pass "⑤-b 음성 — 다른 연구실 맥락에서 그 ${LAB_N}건이 0행으로 보인다 (RLS 가 산다)"
  else fail "⑤-b 음성 실패 — 다른 연구실 맥락에서 ${GOT_B:-측정실패}행이 보인다. **RLS 가 안 선다**"; fi
fi

# ⓒ ai 쪽 앱 롤 — `--no-privileges` 는 이쪽 GRANT 도 지운다. 여기가 죽으면 검색이 사전을 못 읽는다.
AI_EXP="$("$HERE/expectations.sh" "$ADUMP" d9_concept | cut -f2)"
AI_GOT="$(qa "$COLAB_STAGING_AI_DB" "$COLAB_VERIFY_AI_APP_ROLE" "SELECT count(*) FROM d9_concept")"
if [ -n "$AI_EXP" ] && [ "$AI_GOT" = "$AI_EXP" ]; then pass "⑤-c ai 앱 롤 $COLAB_VERIFY_AI_APP_ROLE 이 사전을 읽는다 (d9_concept = $AI_GOT)"
else fail "⑤-c ai 앱 롤이 사전을 못 읽는다 — 본 것 ${AI_GOT:-측정실패} · 기대 ${AI_EXP:-읽기실패}. 재부여(db-bootstrap.sh app-grants) 누락일 수 있다"; fi
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
# ⭑ **손검사 2건(③-보 · ⑤)은 2026-09-03 에 기계가 돈다** — 위 ③-보 블록과 ⑤ 블록이 그것이다.
#   둘 다 fail-closed 다: 재료를 못 고르면 SKIP 이 아니라 FAIL 이고, 실패는 위에서 이미 계수됐다.
#   ⟹ 여기까지 왔으면 **안 본 것이 없다.** 종전의 exit 3(미완)은 그래서 사라진다.
# ⚠ `--manual-ok` 는 **더 이상 필요 없다.** 사람이 붙이던 그 플래그가 곧 SKIP 이었다(`〈170〉-㉮`).
#   인자는 남겨 두되(옛 호출이 깨지지 않게) 판정을 바꾸지 않는다 — 붙였다는 사실만 적는다.
echo "복원 검증 GREEN — 자동분 전건 통과 ＋ **손검사 2건(③-보 읽는 경로 · ⑤ 앱 롤 양성·음성)도 기계가 돌았다**$([ "$MANUAL_OK" -eq 1 ] && echo " (--manual-ok 는 판정에 쓰이지 않았다)")$([ "${SKIPPED:-0}" -ne 0 ] && echo " · 승인된 SKIP ${SKIPPED}건")"
exit 0
