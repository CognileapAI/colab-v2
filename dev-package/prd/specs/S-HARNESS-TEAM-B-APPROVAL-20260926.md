# Spec: 하네스 개선 — 소형 PR B (팀 공용 · intent 승인 형식 `승인: @handle` · legacy 스냅샷 · TEMPLATE 역할화 · 저장소 밖 보고서 반입)
출처 intent: `dev-package/intent/2026-09-25-harness-improvement.md`
출처 절: 10라운드 판정(`:627` · Ted 원문 "pr은 사람이 승인하기만 하면된다 꼭 / 팀에 맥이나 비 wsl호스트가 있음 다른사람일필욘없다 / 나머진 전브 권고로") 중 Q4 예(승인 형식 `승인: @<GitHub handle> <YYYY-MM-DD> "<원문>"` · `intent_ref.py classify` 는 그 꼴만 승인 · 승인 권한 = develop 리뷰 권한자) · 「소형 PR B」 문장(해시 집합 밖 · 회차 불요 · A 와 동시 open 가능 · 승인 형식 + classify + fixture 갱신 + TEMPLATE 실명 열거 삭제 + 보고서 반입). 근거(저장소 밖 → 이 PR 이 반입): `~/.claude/reports/harness-state-20260925/team-shared-20260926/report.md` 권고 6(`:15`) · 감사 D2(`:144-149`) · D4(`:158-163`) · D7(`:179-184`) · 원본 `audit-process-docs.md` · `audit-mechanisms.md` · `audit-cost-concurrency.md`. 총괄 = `dev-package/prd/specs/S-HARNESS-IMPROVEMENT-PLAN-20260926.md`(§0 `:9` · §1 `:28` 이 「§10 10라운드 개정」을 가리키나 §10 절은 아직 없다 — PR 2 총괄 갱신 몫 · 이 문서는 그 절을 쓰지 않는다).
줄 번호 기준 = 브랜치 `claude/harness-s-red` = develop `5bb3d6fe`(E0 #176 병합 · 2026-09-26 재열람). 트레일러 규칙 = E0 · S-red 와 같다(마지막 문단 하나에 `Intent-Ref` + `Co-Authored-By` + `Claude-Session`). 훅 정의(`.claude/settings.json` hooks · `.codex/hooks.json`) 무변경 · 해시 집합(`eval/harness/config-paths.txt:9-17`) 파일 diff 0 → 회차 불요.
단위 규칙 = E0 spec 머리와 같다(⑴ 강제 기제 ⑵ 시험 ⑶ 병합 조건 ⑷ 지우는 산문 ⑸ 소유 PR = B · 장치 없는 단위는 「산문 · 맥락만」). 팀 원칙(10라운드): 모든 결정은 「다른 팀원이 다른 머신(OS · 시간대 · 홈 경로 · clone)에서 같은 절차를 밟아도 같은 판정 · 같은 보호 · 같은 비용」이어야 한다.

## 0. 출처 · 순서
- 순서: S-red 병합 뒤 착수 · 소형 PR A 와 병렬 open 가능(파일 교집합 0 — A 는 `eval/harness/**` · `gates/tools/harness-eval*.sh` · `_readiness.sh` · `scripts/harness/check.py` · `.agents/harness.yaml` · B 는 아래 §7 scope) · PR 2 착수 전 병합. 총괄 §3 소유표(`:135-170`)에 B 의 파일은 등재돼 있지 않다(`intent_ref.py` · `test_harness_record_gates.py` · `TEMPLATE.md` · `intent/README.md` · `dev-package/reports/harness/**`) → 다른 lane 과 충돌 0. 총괄 문서 자체는 「메인(각 PR 착수 전 상세화) · lane 은 spec 을 쓰지 않음」(`:170`) → 총괄 포인터 1구는 메인 몫(§7).
- 고정 사항: 시스템 강제 > 산문 · 병합은 사람 · 승인 intent append-only(ADR-0007 `:14`) · ADR 이력 무수정 · 훅 정의 무변경 · ADR 번호 PR 2 = 0011 · PR 4 = 0012(B 는 새 번호를 쓰지 않는다 · 우려 #3).
- Q1 확정(승인 수 0 유지 · 「사람 승인」 = 사람이 병합 · 에이전트 토큰 병합 불가 = T11 구성원별 PAT · 재판정 = A·B 뒤 PR 2 전)은 이 PR 의 장치가 아니다. B 의 승인 줄은 **기록 형식**이고 승인 행위는 그 줄을 담은 커밋을 사람이 develop 에 병합하는 것이다(ADR-0003 `:18-19` 「검사 green 은 형식 판정이며 승인이 아니다」).

## 1. 문제 진술
- 승인 판정이 문자열 하나다: `scripts/harness/intent_ref.py:41-49` `classify` = 첫 `메타` 줄에 「미승인」 없음 ∧ 「승인」 있음 → approved. 승인자 신원 · 날짜 · 원문이 형식에 없다. 팀원 · 에이전트 누가 「승인」을 써도 같은 효력 · 같은 append-only 잠금(D2).
- 실명 열거: `dev-package/intent/TEMPLATE.md:2` 「발의자: <이태헌 | 조성진 | Ted | agent(전수 red 로그)>」 · `:13` 「예(Ted 서명 필요)」 · `:26` 「Ted 확인 문장(원문 그대로)」 · `dev-package/intent/README.md:1-2` 「Ted 가 교정 · 승인 = 커밋(별도 승인 표기 없음)」 — 두 번째 팀원이 발의 · 승인하는 경로가 문자 그대로 없다(D2 · D7 (b)).
- 근거가 저장소 밖: 9라운드까지의 Fable 판정 원문 · T1 ruleset 스냅샷 · 팀 공용 감사 3 + 종합 1 이 `~/.claude/reports/harness-state-20260925/`(88 파일 · 1.6 MB)에 있고 intent `:2,539,550,563,576,601,609,620,627` · S-auth intent `:2,162,168-169` · 총괄 `:4` · E0/S-red spec 이 그것을 「근거」로 지목한다. 다른 기계의 리뷰어는 재검할 수 없다(D4).
- 전환 제약: 현재 승인 intent 63건(`5bb3d6fe` · 84 파일 = approved 63 · unapproved 15 · no-meta 6 · 새 형식 0건)은 전부 legacy 표기이고 append-only 라 `메타` 줄을 고칠 수 없다. 「새 꼴만 승인」을 그대로 적용하면 63건이 한꺼번에 비보호가 된다(ADR-0007 `:30` 재검토 조건 「메타 형식이 바뀌어 승인 판별식이 틀리기 시작할 때」에 해당).
- 정답표 `gates/fixtures/intent-ref/intent-meta-classification.json`(`:2` 기준 `0a3b9923` · `:4` 62건 · 44/13/5)은 `gates/**` 안 = 해시 집합(`config-paths.txt:13`) → 이 파일을 고치면 회차가 필요해진다. B 는 「회차 불요」가 조건이다.

## 2. 원한 결과 (V-id)
- V-B1 `classify(text, name)` 이 `메타` 줄의 `승인: @<handle> <YYYY-MM-DD> "<원문>"` 꼴을 approved 로 읽는다(handle = GitHub login 형식 · 날짜 = `\d{4}-\d{2}-\d{2}` · 원문 = 큰따옴표 안 1자 이상 · 줄바꿈 없음). `미승인` 이 같은 줄에 있어도 새 꼴이 맞으면 approved(명시 형식 > 부분 문자열).
- V-B2 legacy 표기(「승인」 ∧ ¬「미승인」)는 `scripts/harness/intent_legacy_approved.txt`(동결 스냅샷)에 이름이 있는 파일에서만 approved · 밖이면 unapproved → 비보호(편집 green).
- V-B3 스냅샷은 `intent_ref.py freeze-legacy --commit <sha>` 가 1회 생성한다(그 commit 의 `dev-package/intent/*.md` 중 legacy approved · `EXCLUDED` 제외 · 정렬 · 머리 주석에 sha) · 같은 sha 로 재실행하면 바이트 동일.
- V-B4 게이트 출력이 어느 규칙이 맞았는지 말한다: `⑵ 기준·분기 시점 승인 intent N건 대조(형식 a · legacy 스냅샷 b)`.
- V-B5 스냅샷은 도입 뒤 불변 — base 에 `LEGACY_SNAPSHOT` 이 있으면 head 블롭과 바이트 동일해야 한다 · 차이(이름 추가 · 삭제 · 주석 · 파일 부재) = `red(판정)` · base 부재(도입 PR)만 검사 생략. 이름 추가도 red 인 이유 = 새 intent 를 legacy 표기(「승인」)로 쓰고 같은 PR 에서 스냅샷에 이름 1줄을 더하면 handle 없이 approved · 보호가 된다(Q4 「그 꼴만 승인」 우회).
- V-B6 handle 형식 위반(`@-x` · `@x--y` · 40자 · `@` 뒤 공백) · 날짜 형식 위반 · 따옴표 없음 → unapproved.
- V-B7 기존 정답표 v1(`gates/fixtures/…json`)은 **바이트 무변경** · 시험은 v1 44건이 스냅샷 경유로 여전히 approved 임을 단언 · 새 정답표 v2 `scripts/tests/fixtures/intent-ref/intent-meta-classification-v2.json`(base sha · 84 파일 · rule 열 = `form|legacy|none`)이 실측과 일치.
- V-B8 `TEMPLATE.md` · `intent/README.md` 에 실명 0건(`grep -c '이태헌\|조성진\|Ted'` = 0) · 역할 2개(발의자 · 승인자 = develop 리뷰 권한자) · 새 승인 줄 예시 1개.
- V-B9 `dev-package/reports/harness/20260925-harness-state/` 에 88 파일 · `grep -rcE '/home/[A-Za-z0-9._-]+/|/Users/[A-Za-z0-9._-]+/'` = 0 · `README.md` 색인 1개 · 비밀 0(사전 스캔 결과 0 · T1 JSON 은 ruleset 스냅샷 · `integration_id: 15368` 은 GitHub Actions 앱 id).
- V-B10 두 intent 에 반입 경로 줄 각 1개 추가(줄 추가만) · `intent-ref` green.
- V-B11 기존 시험 green(`harness-contract-selftest` 전부) · 훅 정의 diff 0 · 해시 집합 diff 0(`git diff --stat develop -- AGENTS.md CLAUDE.md .claude .agents gates scripts/harness/hooks eval/harness` 빈 출력) · `harness-eval` 게이트가 develop 과 같은 회차로 green.

## 3. 해법 개요
- `intent_ref.py`: 정규식 `APPROVAL_FORM` + 스냅샷 로더(`scripts/harness/intent_legacy_approved.txt` · base 우선 · base 부재면 head · 둘 다 부재 = 빈 집합) + `classify(text, name, legacy)` + `approval_rule()` + ⑵ 루프에 스냅샷 불변 검사 + `freeze-legacy` 하위 명령. 판정기만 바뀌고 게이트 등록(`gates/run.sh:365-369`) · CI 잡(`ci.yml:663-677`) · parallelism(`parallelism.toml:44` `parallel`) 무변경 — 네트워크 0 · 토큰 0 이라 어느 기계에서도 같은 판정.
- 전환 = 「형식 OR (legacy ∧ 스냅샷)」. 스냅샷은 PR B base 에서 1회 동결 · 영구 · 도입 뒤 불변(V-B5 · 우려 #1). 새 intent 는 형식만. 스냅샷 밖 legacy 표기는 비보호 — 즉 앞으로 「승인」 단어만 쓰면 보호되지 않고 게이트 출력의 `형식 0` 이 그것을 드러낸다.
- 시험 · v2 정답표는 `scripts/tests/**`(해시 집합 밖 · `config-paths.txt:8` 「scripts/harness/*.py 는 밖」과 같은 이유) · v1 정답표는 손대지 않는다.
- 보고서 반입 = 복사 + 절대 홈 경로 치환(`<repo>` · `<home>`) + README 색인. 증거이지 유지 대상 산문이 아니다(E0 회차 `results/**` 와 같은 지위).

## 4. 구현 결정

### 4.1 승인 형식 · 전환 규칙 (단위 B-1)
- 파일 `scripts/harness/intent_ref.py` — 상수(`:29-34` 뒤): `LEGACY_SNAPSHOT = "scripts/harness/intent_legacy_approved.txt"` · `HANDLE = r"[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}"`(GitHub login 규칙 · 하이픈 선두·말미·연속 금지 · ≤39) · `APPROVAL_FORM = re.compile(r'승인:\s*@(' + HANDLE + r')\s+(\d{4}-\d{2}-\d{2})\s+"([^"\n]+)"')`.
- `classify(text, name=None, legacy=frozenset())`(`:41-49` 교체): `META` 부재 → `no-meta` · `APPROVAL_FORM.search(line)` → `approved` · 그 외 `name in legacy` ∧ 「승인」 ∧ ¬「미승인」 → `approved` · 나머지 `unapproved`. `approval_rule(text, name, legacy) -> "form" | "legacy" | None` 같은 판별을 라벨로. `is_protected(name, text, legacy)`(`:52-53`) 는 `classify(..)=="approved"` ∧ `name not in EXCLUDED`.
  ```
  def classify(text, name=None, legacy=frozenset()):
      match = META.search(text)                      # :33 첫 `메타` 줄 · 기존
      if match is None: return "no-meta"
      line = match.group(0)
      if APPROVAL_FORM.search(line): return "approved"          # 규칙 form
      if name in legacy and "승인" in line and "미승인" not in line:
          return "approved"                                     # 규칙 legacy(스냅샷 안)
      return "unapproved"
  ```
  기존 호출 `classify(text)`(name 없음 · legacy 빈 집합)는 「형식만」으로 동작한다 — 시험 fixture 가 스냅샷을 안 주면 legacy 표기가 unapproved 로 관측되는 것이 red-first 의 첫 관측이다.
- 스냅샷 파일 형식(`scripts/harness/intent_legacy_approved.txt`): 1행 `# intent_ref legacy-approved snapshot · commit <40자 sha> · rule: meta has 승인 and not 미승인 · frozen once · names only` · 이후 파일명(`2026-09-06-r-a2.md` 꼴 · 경로 없음) 1줄씩 · 정렬 · LF · 말미 개행. 로더는 `#` 로 시작하는 줄과 빈 줄을 버리고 `strip()` 한 이름만 담는다. 도입 뒤 손 편집은 추가 · 삭제 · 주석 모두 red(V-B5 불변) 이고 재생성 명령이 있어 바이트 대조가 가능하다(V-B3).
- 스냅샷 로더 `legacy_names(root, base, head)`: `show(root, base, LEGACY_SNAPSHOT)`(`:77-79` 재사용)이 있으면 그 내용 · 없으면(도입 PR) `show(root, head, …)` → `#` 주석 · 빈 줄 제외. 합집합 없음(base 우선). `judge()` `:153-160` 은 `legacy = legacy_names(root, base, head)` 로 `is_protected` 를 부른다(스냅샷을 아직 안 가진 열린 PR 도 Update branch 전에 base 쪽 스냅샷으로 보호된다 · base 에 있으면 불변 검사가 head 와의 바이트 동일을 강제하므로 head 쪽은 판정에 쓰지 않는다).
- 불변 검사(`:175` 앞): `LEGACY_SNAPSHOT` 이 base 에 있으면 `blob(root, base, LEGACY_SNAPSHOT) != blob(root, head, LEGACY_SNAPSHOT)`(`:71-74` 원본 바이트 · head 부재 포함) → `red.append("⑵ legacy 승인 스냅샷이 바뀌었다 — 도입 뒤 불변 · 추가 · 삭제 · 주석 모두 금지 · 새 intent 는 승인: @handle 형식")`. base 에 없으면(도입 PR) 검사 생략.
- 출력(`:175`): `⑵ 기준·분기 시점 승인 intent {n}건 대조(형식 {a} · legacy 스냅샷 {b})`.
- `freeze-legacy` 하위 명령(`main()` `:179-184` argparse 를 subparser 없이 `--freeze-legacy <commit>` 옵션으로): 그 commit 의 `intent_names()`(`:149-151`) 중 `name ∉ EXCLUDED` ∧ legacy 규칙 approved → 정렬 → stdout 에 `# intent_ref legacy-approved snapshot · commit <sha> · rule: meta has 승인 and not 미승인 · frozen once · names only` + 이름 1줄씩 · 출력은 `sys.stdout.buffer.write`(UTF-8 · LF 고정 — Windows python 의 텍스트 stdout 은 CRLF 라 V-B3 바이트 동일이 OS 로 갈린다). 파일 쓰기는 호출자(`> scripts/harness/intent_legacy_approved.txt`). 기존 판정 경로와 배타(옵션 있으면 판정 안 함 · exit 0).
- 강제 기제: 게이트 `intent-ref`(`gates/run.sh:365-369`) · CI `intent-ref` 잡(`ci.yml:663-677` · base..head) · fail-closed(스냅샷 부재 = 형식만 · 도입 뒤 스냅샷 변경 = red) · Claude/Codex 공통(판정기 1개 · 훅 아님 · ADR-0007 `:15` 「훅은 두지 않는다」). 시험(4.2)의 CI 실행처 = `agent-bridge.yml` `compatibility` 잡뿐(필수 check 아님 · 4.2) — 병합 차단 장치는 `intent-ref` 잡 하나.
- 시험 = 4.2 · 병합 조건 = `harness-contract-selftest` green ∧ V-B1–B6 ∧ PR 의 `Agent bridge compatibility / compatibility` green 을 병합자가 확인(필수 check 아님 · 4.2) · 지우는 산문 = 정답표 v1 `:3` 「rule」 문장은 파일 무변경이므로 그대로(v2 가 현행 규칙) · ADR-0007 `:26` 「알려진 비보호」 문장은 이력(무수정).
- 출처: intent `:627` Q4 · report.md 권고 6 · D2 · 우려 #1(전환 규칙) · #2(handle 검증).

### 4.2 시험 · 정답표 (단위 B-2 · red-first)
- 파일 `scripts/tests/test_harness_record_gates.py` `IntentRefGateTests`(`:149`) — 상수 `APPROVED`(`:24-26`) 의 `승인: **Ted 2026-01-01**` → `승인: @fixture-approver 2026-01-01 "approve"` · `:245` `:254` 의 `"승인 2026-01-03 Ted"` → `'승인: @fixture-approver 2026-01-03 "ok"'` · `:383` TEMPLATE 단언의 메타를 새 꼴로. `repo()`(`:154-163`)에 legacy 표기 intent `2026-01-03-legacy.md` 와 스냅샷 파일(그 이름 1줄) 추가.
- 새 사례: ① 새 꼴 approved · 줄 편집 → red(V-B1) ② `2026-01-03-legacy.md` 를 스냅샷에서 뺀 fixture → 편집 green(V-B2) + base 에 스냅샷이 있는 repo 에서 head 스냅샷의 이름 삭제 · 이름 추가(legacy 표기 새 intent 동반) · 주석 1자 변경 · 파일 삭제 → 각각 red(V-B5) · base 부재 repo 에서 스냅샷 신설 → 검사 생략 green ③ 스냅샷 안 legacy → 편집 red(V-B2·B3) ④ 형식 위반 6꼴 → `classify == "unapproved"`(V-B6) ⑤ 새 꼴 + 같은 줄 「미승인 3건 잔존」 → approved(V-B1) ⑥ `--freeze-legacy HEAD` 출력 = 기대 목록 · 2회 실행 바이트 동일(V-B3) ⑦ 출력 문구 `형식 1 · legacy 스냅샷 1`(V-B4).
  - ⑦ 오탐 방지 근거: 4.3 TEMPLATE 주석 줄(`<!-- 승인 시 … 승인: @<GitHub handle> <YYYY-MM-DD> "<원문>" … -->`)은 `<!--` 로 시작해 `META`(`intent_ref.py:33` `^메타` · `re.M`)에 걸리지 않는다 → TEMPLATE 을 복사한 새 intent 도 판정 대상은 첫 `메타` 줄(`승인: 미승인` · 형식 불일치 = unapproved)뿐 · `EXCLUDED`(`:30`)와 별개로 성립.
- ④ 의 6꼴(모두 `subTest` · 스냅샷 밖 이름으로 호출):
  - `승인: @-ted 2026-01-01 "ok"` — 선두 하이픈
  - `승인: @te--d 2026-01-01 "ok"` — 연속 하이픈
  - `승인: @` + 40자 영숫자 + ` 2026-01-01 "ok"` — 길이 초과(≤39)
  - `승인: @ ted 2026-01-01 "ok"` — `@` 뒤 공백
  - `승인: @ted 2026-1-1 "ok"` — 날짜 자릿수
  - `승인: @ted 2026-01-01 ok` — 따옴표 없음
  통과 대조 2꼴: `승인: @ted 2026-01-01 "권고대로"` · `승인:@a1-b2 2026-01-01 "x"`(콜론 뒤 공백 0 허용 · `\s*`).
- 정답표: `test_classification_matches_the_frozen_62_intent_answer_table`(`:365-383`)은 v1 파일을 그대로 읽되 `classify(text, row["name"], legacy=<실제 스냅샷>)` 로 호출 · 44/13/5 단언 유지(44건 전부 스냅샷 ⊆ 이므로 성립 · append-only 라 메타 줄이 바뀔 수 없다). 새 시험 `…_v2_answer_table` — `scripts/tests/fixtures/intent-ref/intent-meta-classification-v2.json`(`source` = base sha · `total` 84 · `counts` {approved 63 · unapproved 15 · no-meta 6} · 행마다 `rule`) 과 `classify` · `approval_rule` 대조 · `intended_unprotected` 의 `2026-09-08-harness-evals.md` 유지(우려 #4).
- 실행 게이트 = `harness-contract-selftest`(`gates/run.sh:356-357` 가 이 파일을 돈다). 수치(63/15/6 · 84)는 lane begin 시점 develop 에서 재측정해 v2 에 적는다(이 문서 값은 `5bb3d6fe` 실측).
- CI 실행처 = `.github/workflows/agent-bridge.yml` `compatibility` 잡(`:61` · paths `scripts/harness/**` `:19` · `scripts/tests/**` `:22`)뿐이고 필수 check 가 아니다. `ci.yml` · `.agents/ci-producers.json` 에 이 게이트 이름 0건 · `ci.yml` `gate-selftest` 잡(`:716-718`)은 `contracts` 필터(`:70-75` `contracts/**` · `gates/**` · `db/ai/seed/…`)라 B 경로에서 깨지 않는다 · ruleset 필수 check = `ci-required` 하나(`T1-develop-ruleset.json:23`). 병합 차단 = `intent-ref` 잡(`ci.yml:663-677` · `ci-required` needs `:851`) 뿐.
- 강제 기제 = 시험(FC · 로컬 게이트 + 비필수 CI) · 병합 조건 = 위 ①–⑦ + v1 + v2 green ∧ PR 의 `compatibility` green 을 병합자가 확인(필수 check 아님) · 지우는 산문 = 없음.

### 4.3 TEMPLATE · README 역할화 (단위 B-3 · 「산문 · 맥락만」)
- `dev-package/intent/TEMPLATE.md:2` → `메타 — 발의자: <@GitHub handle | agent(<출처>) | 이슈 #N 작성자 @handle> · 작성 YYYY-MM-DD · 승인: 미승인` 와 그 아래 주석 1줄 `<!-- 승인 시 메타 줄의 「승인: 미승인」을 승인: @<GitHub handle> <YYYY-MM-DD> "<원문>" 으로 바꾼다 · 승인자 = develop 리뷰 권한자 · 이 줄을 담은 커밋을 사람이 병합하면 승인이고 그 뒤 이 파일은 줄 추가만 허용된다(게이트 intent-ref · ADR-0007) -->`. `:13` 「예(Ted 서명 필요)」 → 「예(승인자 서명 필요)」 · `:26` 「Ted 확인 문장(원문 그대로)」 → 「승인자 확인 문장(원문 그대로 · 메타 줄의 "<원문>" 과 같다)」.
- `dev-package/intent/README.md:1` 「Ted 가 교정한다」 → 「승인자(develop 리뷰 권한자)가 교정한다」 · `:2` 「승인 = 커밋(별도 승인 표기 없음)」 → 「승인 = 메타 줄 `승인: @<handle> <날짜> "<원문>"` 을 담은 커밋의 병합 · 판별 = `scripts/harness/intent_ref.py`(legacy 표기는 `intent_legacy_approved.txt` 동결분만)」.
- 강제 기제: 없음(양식) · 검사 = V-B8 grep · `TEMPLATE.md` 는 `EXCLUDED`(`intent_ref.py:30`) 라 판정 대상 아님 · `README.md` 도 같다.
- 범위 밖: `.agents/skills/grill-me/SKILL.md:11,14,16` 의 「Ted」 · `researcher.md:64` · colab-rules 역할 어휘 → PR 4 4-1(10라운드 「PR 4 추가」 · D7).

### 4.4 보고서 반입 (단위 B-4 · 증거 · 유지 대상 아님)
- 원본 `~/.claude/reports/harness-state-20260925/` = 88 파일 · 1.6 MB · 하위 13 디렉터리(`fable-judges` · `fable-recheck-r3` · `fable-recheck-r4` · `intent-draft`(task 열거에 없었으나 실재 · 8 파일 · 포함) · `master-plan-20260926` · `opus55-prompt-audit` · `playbook-gap-20260926` · `pr2-spec-20260926` · `sauth-grill-20260926` · `system-first-recut` · `team-shared-20260926`) + 루트 12 파일(`R1`–`R5` · `REPORT-eli7.md` · `findings-verified.md` · `advisor2.md` · `measurement.json` · `guard_probe.py` · `T1-develop-ruleset.json` · `T1-rulesets-after.json`). 대상 `dev-package/reports/harness/20260925-harness-state/`(같은 트리).
- 반입 트리(README 표의 골격 · 파일 수는 `find -type f` 실측):
  | 경로 | 파일 | 내용 | 가리키는 판정 줄 |
  |---|---|---|---|
  | `R1-hooks.md` … `R5-governance.md` · `findings-verified.md`(132행) · `advisor2.md` · `REPORT-eli7.md` · `measurement.json` · `guard_probe.py` | 10 | 1–2라운드 원자료 · 검증 결과 · 측정 · git-guard 우회 재현 스크립트 | intent `:539` |
  | `T1-develop-ruleset.json` · `T1-rulesets-after.json` | 2 | develop ruleset 입력 · 적용 뒤 스냅샷(승인 0 · strict · bypass 0) | `:620` |
  | `fable-judges/` | 9 | 39건 blind 재판정 8 + 교차 | `:550` |
  | `intent-draft/` | 8 | 초안 절 A · B1 · B2 · CT · advisor 검토 · 대체 메모 | 초안 이력 |
  | `fable-recheck-r3/` · `fable-recheck-r4/` | 10 + 5 | 3 · 4라운드 반박 재검토 + spec gate ① | `:563` · `:576` |
  | `opus55-prompt-audit/` | 9 | 5라운드 감사 4 + 검증 4 + 교차 | `:601` |
  | `playbook-gap-20260926/` | 7 | 6라운드 대조 3 + 검증 3 + 방향 | `:609` |
  | `system-first-recut/` | 7 | 7라운드 설계 3 + 검증 3 + recut | `:609` 이후 · 총괄 `:4` |
  | `master-plan-20260926/` · `pr2-spec-20260926/` | 5 + 2 | 총괄 · E0/S-red · PR 2 spec 의 저자/검증 판정 | 총괄 `:4` · S-red `:3` |
  | `sauth-grill-20260926/` | 10 | 9라운드 S-auth blind 판정 · 교차 · 재검 · 정정 | S-auth `:2,168-169` |
  | `team-shared-20260926/` | 4 | 10라운드 감사 3(86 · 93 · 86행) + 종합 `report.md`(314행) | `:627` · 이 spec |
- 치환(순서 고정 · `find <dir> -type f -exec sed -i 's#…#…#g' {} +` 1패턴 1명령 · 리터럴만 · `sed -i` 는 GNU 형식이라 macOS BSD sed 에서 그대로 돌지 않는다 → 1회 반입 명령 · 결과 파일이 정본 · 재현 대상 아님): ⑴ `<home>/workspace/00_Project/00 CoLAB/31 CoLAB-v2/.claude/worktrees/harness-improvement` → `<repo>/.claude/worktrees/harness-improvement`(9곳) ⑵ `<home>/workspace/00_Project/00 CoLAB/31 CoLAB-v2` → `<repo>`(5곳) ⑶ 남은 실행자 홈 절대경로 → `<home>`(`.claude/jobs/…` 13 · `.claude/reports/…` 4 · `workspace/…` 2) — 이 문서의 `<home>` = 실행자 `$HOME`(명령에서는 sed 패턴을 큰따옴표로 써 `$HOME` 을 전개 · 문서에 실제 홈 경로를 적지 않는다). `~/.claude/...`(40곳) 은 절대경로가 아니므로 원문 유지 · `/home/user/`(1곳 · `harness.yaml:101` allow 값 인용) 유지. 검사 = `grep -rcE '/home/[A-Za-z0-9._-]+/|/Users/[A-Za-z0-9._-]+/' <dir>` 0 · `grep -rlE 'ghp_|github_pat_|sk-ant-|AKIA|PRIVATE KEY' <dir>` 0(사전 스캔 0).
- `README.md`(새 파일 · `dev-package/reports/harness/2026-09-06/README.md` 꼴): 첫 문단 「근거 보관소 · 결론 아님 · 판정 정본 = intent 「판정 기록」 · 원 위치 `~/.claude/reports/harness-state-20260925/`(1:1) · 경로 표기 `<repo>` = 실행 checkout 루트 · `<home>` = 실행자 홈 · 내용 무수정」 + 표(라운드 ↔ 디렉터리 ↔ intent 줄: 1–2라운드 `R*`·`findings-verified`·`advisor2` ↔ `:539,550` · 3 `fable-recheck-r3` ↔ `:563` · 4 `fable-recheck-r4` ↔ `:576` · 5 `opus55-prompt-audit` ↔ `:601` · 6 `playbook-gap-20260926` ↔ `:609` · 7 `system-first-recut` · `master-plan-20260926` · `pr2-spec-20260926` · 9 `sauth-grill-20260926` ↔ S-auth `:2,168-169` · 10 `team-shared-20260926` ↔ `:627` · T1 JSON ↔ `:620` · `intent-draft` ↔ 초안 이력). `report.md:1` 의 하네스 주석 줄(`[harness: subagent output matched …]`)은 원문의 일부 · 유지 · README 에 1줄 설명.
- 게이트 영향: `.gitignore:35` `*.log`(해당 파일 0) · `:83` `gate-summary.json`(0) · `exec-bit` 는 `.sh` 만(`exec-bit.sh:16` · 반입에 `.sh` 0) · `decision-number-guard` 는 `PLAN-SoT.md` 만(`:60`) · `harness-contract` `home_path_roots`(`harness.yaml:100`)에 `dev-package/reports` 없음 → 이 PR 의 검사는 grep(우려 #5).
- 강제 기제: 없음(증거) · 병합 조건 = V-B9 · 지우는 산문 = 없음.

### 4.5 포인터 (단위 B-5 · 줄 추가만)
- `dev-package/intent/2026-09-25-harness-improvement.md` 「판정 기록」 절 끝(`:628` 뒤) 1줄: `- 2026-09-26 소형 PR B — 위 라운드들의 저장소 밖 원문(~/.claude/reports/harness-state-20260925/ · :2,539,550,563,576,601,609,620,627 이 가리키는 것 전부)을 dev-package/reports/harness/20260925-harness-state/ 로 반입했다(88 파일 · 홈 경로 <repo>·<home> 치환 · 내용 무수정 · README 색인). 승인 형식 Q4 의 판별기 = scripts/harness/intent_ref.py · legacy 동결 = scripts/harness/intent_legacy_approved.txt(base <sha> · 63건).`
- `dev-package/intent/2026-09-26-human-authorization-for-destructive-ops.md` 「추가 기록 (승인 뒤 줄 추가만)」(`:171-173`) 끝 1줄: `- 2026-09-26 소형 PR B — :2 · :162 · :168-169 의 ~/.claude/reports/harness-state-20260925/ 원문은 dev-package/reports/harness/20260925-harness-state/(sauth-grill-20260926 · system-first-recut · playbook-gap-20260926) 에 있다.`
- 총괄 `S-HARNESS-IMPROVEMENT-PLAN-20260926.md:4` 근거 문장 끝에 「(소형 PR B 로 `dev-package/reports/harness/20260925-harness-state/` 반입)」 1구 — 메인 몫(§7). E0 · S-red spec 의 「근거(저장소 밖)」 문장은 손대지 않는다(이력 · 총괄 포인터로 충분).
- 강제 기제 = `intent-ref` ⑵(두 intent 는 스냅샷 안 = 보호 · 추가만 통과) · 병합 조건 = V-B10 · 지우는 산문 = 없음.

## 5. 시험 결정 (TDD 순서)
1. `test_harness_record_gates.py` 상수 3곳 + 사례 ①–⑦ + v2 정답표 시험 작성 · `scripts/tests/fixtures/intent-ref/intent-meta-classification-v2.json` 생성(실측) → `bash gates/run.sh harness-contract-selftest` RED(`classify()` 인자 · `--freeze-legacy` 미지원 · 새 꼴 unapproved 관측).
2. `intent_ref.py` 구현 → ①–⑦ GREEN · v1 시험은 스냅샷 없이 RED 상태 유지.
3. `python3 scripts/harness/intent_ref.py --freeze-legacy <lane begin 시점 develop sha> > scripts/harness/intent_legacy_approved.txt` → 63줄(+주석 1) → v1 · v2 GREEN.
4. `bash gates/run.sh intent-ref` 로 이 브랜치 자체 판정(두 intent 추가 줄 · 형식 0 · legacy 63 출력 확인).
5. 기존 시험 무변경 green 확인 · 시험 수 증가분 기록(v1 62건 표 + 새 사례 7 + v2 1).
- seam: throwaway `git init` fixture(`:2-4`) · 스냅샷 파일을 fixture repo 안에 쓴다 · 실 checkout 무변경.

## 6. 위험 · 롤백
- 보호 축소 창: 스냅샷 없는 head(B 병합 전 분기한 열린 PR)의 CI 는 base 쪽 스냅샷(base 우선)으로 보호된다 · 같은 실행에서 불변 검사는 head 부재 = 차이 → red(판정) · 해소 = Update branch · ruleset strict(`T1-develop-ruleset.json` `strict_required_status_checks_policy: true`) 라 병합 판정 실행은 어차피 Update branch 뒤 = head 도 같은 스냅샷 보유.
- 새 꼴 오탐: 「승인: @」 뒤 handle 이 실제 계정인지 판정하지 않는다(우려 #2 · 형식 판정) · 날짜의 달력 유효성도 형식만.
- legacy 오탐 유지: `2026-09-08-harness-evals.md`(실승인 · 메타 「미승인」)는 계속 비보호(우려 #4).
- 스냅샷 손상 · 우회: base 에 있으면 head 와의 바이트 차이 전부 red(이름 삭제 · 이름 추가 · 주석 · 파일 삭제 · V-B5) — 이름 추가를 막는 이유 = legacy 표기 새 intent + 같은 PR 스냅샷 1줄로 형식 없이 보호되는 경로 차단.
- 반입 용량 1.6 MB(텍스트) · 회차 `results/**` 8회 × 162 파일과 같은 지위 · 검색 잡음은 `dev-package/reports/harness/` 관례상 수용.
- 동시 open 인 PR A 와의 간섭: A 가 먼저 병합되면 B 의 Update branch 는 해시 집합 파일을 안 건드리므로(§7 scope) B 의 `harness-eval` 은 A 회차와 같은 해시로 green · B 가 먼저 병합되면 A 는 회차를 이미 자기 head 에서 잰 뒤라 무관(총괄 §0 「집합 밖 파일만 바뀐 develop 병합은 회차 유지」 · 10라운드 PR 2 추가 문구).
- 스냅샷 생성 시점: lane begin 시점 develop sha 로 동결 · 그 뒤 B 가 열려 있는 동안 develop 에 legacy 표기로 새 승인 intent 가 들어오면(다른 PR) 그 파일은 스냅샷 밖 = B 병합 직후 비보호. 완화 = 병합 전 메인이 `--freeze-legacy <병합 직전 develop>` 재실행 → 차이가 있으면 추가 줄만 커밋(B 자체는 base 에 스냅샷 부재 = 불변 검사 생략이라 가능 · B 병합 뒤에는 불가) · 이 절차를 §9 「게시 뒤」 에 둔다.
- 롤백 단위: 커밋 ②(판정기 + 스냅샷)만 되돌리면 legacy 단일 규칙으로 복귀(시험 ① 도 함께) · ④(반입)는 독립.

## 7. 레인 지시 (PR B · lane-worker 1개)
- 선행: 10라운드 기록 · spec · intent 커밋 `12ad099b`(intent `:627` · S-auth 추가 기록 · 총괄 §10 · spec A/B · intent ⓐⓑ)가 develop 에 병합돼 있거나 B 브랜치가 그 커밋을 조상으로 가진다(확인 = `git merge-base --is-ancestor 12ad099b HEAD` 종료코드 0) — 없으면 B-5 「`:628` 뒤」 · `Plan-Ref` 대상이 head 에 없다.
- 스폰: `Agent(subagent_type: "lane-worker", isolation: "worktree")` · 기준 = S-red 병합 뒤 develop · 첫 행동 `git merge --ff-only develop` · 부모 checkout 판정 정지 규칙 동일 · A 레인과 동시 가능.
- begin: `python3 scripts/agent-bridge.py lifecycle begin --role lane-worker --gate harness-contract-selftest --gate harness-contract --gate intent-ref --gate exec-bit --scope 'scripts/harness/intent_ref.py' --scope 'scripts/harness/intent_legacy_approved.txt' --scope 'scripts/tests/test_harness_record_gates.py' --scope 'scripts/tests/fixtures/intent-ref/**' --scope 'dev-package/intent/TEMPLATE.md' --scope 'dev-package/intent/README.md' --scope 'dev-package/reports/harness/20260925-harness-state/**' --scope 'dev-package/intent/2026-09-25-harness-improvement.md' --scope 'dev-package/intent/2026-09-26-human-authorization-for-destructive-ops.md'`(우려 #3 ⓐ 채택 시 `--gate adr-records --scope 'docs/decisions/0007-intent-ref-trailer-and-append-only-approved-intents.md'` 추가).
- 반입 명령(한 호출 1명령): `cp -r ~/.claude/reports/harness-state-20260925 dev-package/reports/harness/20260925-harness-state` → `find … -type f -exec sed -i '…' {} +` ×3(4.4 순서) → `grep -rcE '/home/[A-Za-z0-9._-]+/|/Users/[A-Za-z0-9._-]+/' …` → README 작성. `git add` 는 디렉터리 단위.
- 커밋 단위(각 트레일러): ① B-2 시험 + v2 정답표(RED) ② B-1 판정기 + `--freeze-legacy` + 스냅샷 파일(GREEN) ③ B-3 TEMPLATE · README ④ B-4 반입 + README 색인 ⑤ B-5 두 intent 줄 추가(우려 #3 ⓐ 면 ADR-0007 추가 줄 동반) — 되돌림 단위 = ② · ④.
- 게이트: `COLAB_TASK_ID=<id> bash gates/run.sh task` 1회 + `bash gates/run.sh harness-eval`(회차 불요 증명 · V-B11) · 호스트 단독 규칙은 serial 게이트 없음(`intent-ref` parallel · `harness-contract-selftest` 도 python) → 뮤텍스 무관.
- 인계: `lifecycle handoff --task <id> --mode complete --summary '…'` · `COLAB_HANDOFF` · `WORKTREE= BRANCH=`. 메인 = 총괄 `:4` 1구(4.5) 같은 브랜치 커밋(트레일러 동일) → PR 본문 초안 → push · 게시(T16) = 게시자 · 병합(T13) = 병합자(사람).
- 트레일러(마지막 문단 하나): `Intent-Ref: dev-package/intent/2026-09-25-harness-improvement.md` / `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>` / `Claude-Session: https://claude.ai/code/session_019Mw7WhebGjZa4yVkM79Wpk`.

## 8. 검증표
| V | 명령(worktree 루트) | 기대 | 완료 기준 |
|---|---|---|---|
| V-B1·B2·B3·B5·B6 | `bash gates/run.sh harness-contract-selftest`(사례 ①–⑤) · 수동: `python3 -c` 로 `classify` 6꼴 호출 | green · unapproved 6/6 | 4.1 · 4.2 |
| V-B3 | `python3 scripts/harness/intent_ref.py --freeze-legacy <base sha>` 2회 → `diff` 출력 vs 파일 | 빈 diff · 63 이름 | 4.1 |
| V-B4 | `bash gates/run.sh intent-ref`(이 브랜치) | `형식 0 · legacy 스냅샷 63` 출력 · green | 4.1 |
| V-B7 | `harness-contract-selftest`(v1 · v2 표) · `git diff develop -- gates/fixtures/intent-ref/` | green · 빈 diff | 4.2 |
| V-B8 | `grep -c '이태헌\|조성진\|Ted' dev-package/intent/TEMPLATE.md dev-package/intent/README.md` | 0 · 0 | 4.3 |
| V-B9 | `find dev-package/reports/harness/20260925-harness-state -type f \| wc -l` · `grep -rcE '/home/[A-Za-z0-9._-]+/|/Users/[A-Za-z0-9._-]+/' …` · `ls …/README.md` | 89(88 + README) · 0 · 존재 | 4.4 |
| V-B10 | `git diff develop --stat -- dev-package/intent/2026-09-25-harness-improvement.md dev-package/intent/2026-09-26-human-authorization-for-destructive-ops.md` · `bash gates/run.sh intent-ref` | 각 +1 · green | 4.5 |
| V-B11 | `git diff --stat develop -- AGENTS.md CLAUDE.md .claude .agents gates scripts/harness/hooks eval/harness` · `bash gates/run.sh harness-eval` · `git diff develop -- .claude/settings.json .codex/hooks.json` | 빈 출력 · 0(develop 과 같은 회차 id) · 빈 diff | 공통 |
| 공통 | `bash gates/run.sh harness-contract` · `bash gates/run.sh exec-bit` · `python3 scripts/agent-bridge.py check` | 0 · 0 · green | |

## 9. PR 본문 계획
- 파일 `~/.claude/pr-bodies/PR-BODY-harness-improvement-B.md` · `pr_contract.py … --mode draft` → 0 · 게시 = T16(게시자).
- 첫 줄: 「하네스 개선 소형 PR B — intent 승인 줄을 `승인: @handle 날짜 "원문"` 으로 고정하고 legacy 승인 63건은 동결 스냅샷으로 보호를 잇는다 · 저장소 밖 판정 원문 88 파일 반입」.
- `Plan-Ref: dev-package/prd/specs/S-HARNESS-TEAM-B-APPROVAL-20260926.md`(총괄 §0 10라운드 · PR A 와 병렬) · 결정 = 형식 OR legacy∧스냅샷 · 스냅샷 도입 뒤 불변(차이 red) · 형식 판정만(ADR-0003) · v1 정답표 무변경(해시 집합) · 회차 불요 증명 = V-B11 · 남은 제약 = handle 실재 미검증 · harness-evals 비보호 유지 · `dev-package/reports` 홈 경로 검사는 grep(PR A `home_path_roots` 후속 · 우려 #5) · `harness-contract-selftest` 의 CI 실행처는 `agent-bridge.yml` `compatibility`(필수 check 아님) · 병합 차단은 `intent-ref` 잡(`ci-required`)뿐 → `compatibility` green 은 병합자가 확인.
- 게시 뒤 · 병합 직전: 메인이 `python3 scripts/harness/intent_ref.py --freeze-legacy origin/develop` 출력과 스냅샷을 `diff` — 추가 이름이 있으면 그 줄만 덧붙여 커밋(§6 두 번째 항목) · 삭제 이름은 있을 수 없다(승인 intent 는 삭제 red).
- 게시 뒤: 병합자 병합(T13) → T11 재판정 · PR 2 착수(총괄 §10.5 가 이 spec 을 참조 행으로 둔다 · 12ad099b).

## T-항목 (사람 행동 · 역할어 · 번호 = 총괄 §2 「Ted 행동」 표)
| T | 행동 | 명령/UI | 기록 |
|---|---|---|---|
| T16 | PR 게시(게시자) — 메인 초안(`~/.claude/pr-bodies/PR-BODY-harness-improvement-B.md`) · `gh pr create` | 게시자 터미널 | PR 번호 → intent 「확인」 |
| T13 | 병합(병합자 = 사람 · ruleset 승인 0 유지 = Q1) | GitHub UI | 병합 sha → intent 「판정 기록」 줄 |
| T11′ | 재판정(A·B 병합 뒤 · PR 2 전): 구성원별 에이전트 PAT(`Pull requests: Read`) — 이 PR 의 승인 줄은 그 PAT 와 무관 | 대화 판정 | intent 「판정 기록」 |
| T19 | 첫 새 꼴 승인 1건(다음 intent 승인 때 `승인: @<승인자 handle> <날짜> "<원문>"` 직접 기입) → `intent-ref` 출력 `형식 1` 관측 | 편집 · 커밋 | intent 「확인」 |

## 우려 항목
| # | 항목 | ⓐ | ⓑ | 권고 | 판정 |
|---|---|---|---|---|---|
| 1 | legacy 63건 전환 규칙 | 형식 OR (legacy ∧ 동결 스냅샷 `intent_legacy_approved.txt` · base 1회 생성 · 도입 뒤 불변(차이 red) · 영구) | 형식만 · legacy 63건은 비보호로 두고 필요 시 새 intent 재발행 | ⓐ — ⓑ 는 append-only 를 잃고(ADR-0007 `:14`) 재발행은 승인 원문을 새로 쓸 수 없다 · ⓐ 는 스냅샷 밖 legacy 를 비보호로 만들어 「새 intent 는 새 꼴」을 게이트가 강제 · 만료 없음(파일은 영구 동결) | 〈판정 대기〉 |
| 2 | handle 검증 | 형식만(GitHub login 정규식 · 네트워크 0 · 토큰 0) | `gh api users/<handle>` 실재 확인 | ⓐ — ⓑ 는 오프라인 기계 · 토큰 없는 CI fork 에서 78 → 기계마다 판정이 갈린다(팀 원칙 위반) · 승인은 사람이 병합으로 한다(ADR-0003 `:18-19`) · 권한(develop 리뷰 권한자)도 기계가 안 본다 | 〈판정 대기〉 |
| 3 | ADR 기록 | ADR-0007 「결과와 감수한 비용」 끝에 날짜 줄 1개 추가(ADR-0003 `:35` 「2026-09-17 추가 —」 선례 · 기존 줄 무수정 · 번호 0011/0012 무영향) | 새 ADR-0013(0011·0012 는 PR 2·4 예약 · 병합 순서와 번호 역전) | ⓐ — 판별식 변경은 ADR-0007 `:30` 재검토 조건 적중이며 같은 결정의 개정 · 번호 역전을 피한다 · 채택 시 §7 gate/scope 추가 | 〈판정 대기〉 |
| 4 | `2026-09-08-harness-evals.md`(실승인 · 메타 「미승인」 · v1 `:13-15` 의도된 비보호) | 그대로(비보호 유지 · 사람이 원하면 새 꼴로 메타 줄 수정 = 미승인이라 편집 가능 · 날짜는 수정 커밋일) | 스냅샷에 예외로 넣어 보호 | ⓐ — 스냅샷은 규칙의 기계 출력이어야 재현된다(`--freeze-legacy` 바이트 동일) · 예외 1건은 손 편집 | 〈판정 대기〉 |
| 5 | 반입 보고서의 홈 경로 검사 | 이 PR = grep 검사 · `home_path_roots` 는 A 의 `.agents/harness.yaml` 몫 → A 에 `dev-package/reports/harness` 1토큰 추가(같은 파일 · 같은 회차 · 단 기존 `dev-package/reports/**` 에 홈 절대경로(`HOME_PATH` 꼴 · `scripts/harness/config.py:29-33`) 잔존 0 확인 뒤) | B 에서 `harness.yaml` 수정 | ⓐ — `.agents/**` 는 해시 집합(`config-paths.txt:12`) 이라 B 가 만지면 회차 조건이 생긴다 · A 는 10라운드 확정 목록(`eval/harness/results` · `dev-package/intent` · `dev-package/prd`) 에 1토큰 추가 = Ted 판정 | 〈판정 대기〉 |
| 6 | `~/.claude/...` 상대 표기 40곳 | 원문 유지 + README 대응 1줄 | 반입 경로로 재작성 | ⓐ — 증거 무수정 · 절대경로가 아니라 위생 검사 대상도 아님 | 〈판정 대기〉 |

## 정책 대조
- 시스템 강제 > 산문: 승인 형식 · 전환 · 스냅샷 불변 = 게이트(`intent-ref`) · 역할 어휘 = 양식(장치 없음 · PR 4 가 규칙 본문) — 일치.
- 병합은 사람 · ruleset 승인 0(Q1): 이 PR 은 서버 설정을 건드리지 않는다 · 승인 줄 = 기록 — 일치.
- 승인 intent append-only: 두 intent 는 줄 추가만 · 스냅샷 안이라 게이트가 보호 — 일치. ADR 이력 무수정: 우려 #3 ⓐ 도 줄 추가 — 일치.
- 훅 정의 무변경 · 해시 집합 diff 0 · 회차 불요: V-B11 — 일치. 팀 원칙: 판정기는 파일 · 정규식 · git 만(네트워크 · 토큰 · OS · 시간대 무관) — 일치.
- 제품 요구 무변경: `services/**` · `frontend/**` diff 0.

## 범위 밖
- ruleset 개정 · T11 PAT · CODEOWNERS(`.github/CODEOWNERS:5` `@sungwooHa`) 교체 · `grill-me`/`researcher.md`/`colab-rules §0` 역할 어휘(PR 4) · `.agents/harness.yaml`(A) · `gates/fixtures/intent-ref/*.json` 수정(해시 집합) · S-auth `authorized_by`(별도 intent ⓒ) · 총괄 §10 작성(PR 2) · E0/S-red spec 의 「근거(저장소 밖)」 문구 · `~/.claude/pr-bodies/` 반입 · handle ↔ GitHub 권한 조회 · 승인 날짜 달력 검증.
