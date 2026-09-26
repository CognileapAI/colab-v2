VERDICT: ACCEPT-WITH-CHANGES

**1. Factual claims (spot-checked at develop 67a03a05)**
- All load-bearing cites hold: `git-guard.sh:167` `set -- $seg`, `:193` `shift 2`, `:143` branch from payload `$CWD`, `:149` unquoted segment split, `:182`/`:207`/`:234`/`:242`/`:257`, `:81-83` exit 2, `:90` unreachable `|| exit 0`; `test-file-guard.sh:32` `COLAB_FIX_LANE` gate, `:38` exit 2, `:42` unreachable; `verify_evidence.py:57-58`, `:362-365`; `run.sh:9`, `:795`, `:971-977`; `lifecycle_contract.py:365/369/377/386-389/500/611-613`; `pr_contract.py:47`; `decision-number-guard.sh:67` `origin/main` (ref absent, rc=1), `:73 exit 0`; ruleset JSON `:6` `refs/heads/main`; `414f51e7` exists; `researcher-task.sh:9-11`; `live_audit.sh:29/35`; `_pg.sh:193`; `service-tests.sh:81-82`; `lifecycle-evidence.md:36/42/95-96`; `measurement-lane.md:17-18`; `settings.json:58-66` (Bash) / `:68-84` (Edit|Write); `COLAB_FIX_LANE` only in `agent-bridge.py:278` and `dev.ps1:102`.
- Nothing from the must-not list is stated as fact. T5 「기록 없음」, C12 「문서 근거 · 미측정」, L4 title 「추론」, L3 「사용자 메모리뿐 — 미검증」, C2 「동작은 의도 · README 쪽 drift」, A1 「줄·segment 시작일 때만」, T3 「33 사용 여부 미검증」 are all correctly hedged. Header line 6 correctly limits "verified" `-missed` items to the three cases.
- One cite gap: `grep 'exit 1 은 통과' scripts/harness/hooks/*.sh` also hits `decision-number-guard.sh:27`, which C10 does not list. In that file the header may actually be true (I see only `exit 0` paths at `:37`, `:38`, `:73`, no exit 2), so C10's completion grep over `*.sh` either forces an unjustified rewrite or fails. Change: narrow the C10 grep to the two named files, or add decision-number-guard with a "fail-open 여부 확인" step tied to C5.

**2. PR boundaries**
- A3 「세 guard 머리말에 … 명시」 edits `migration-guard.sh` and `decision-number-guard.sh` headers, which are PR 3 files (C5, C10). Line 138 「A2–A4 는 파일이 겹치지 않아」 is therefore wrong. Change: keep only the README sentence in A3 (PR 1) and move the two guard headers to C10, or add an explicit shared-file note.
- A2 ⓐ has a forward dependency on PR 2: line 106 「「열린 task」 정의를 PR 2(L1 task 종료 기록)와 맞춤」. PR 1 cannot rely on close records that PR 2 introduces. Change: either define "open task" in PR 1 without close records (e.g. newest scoped lane-worker task in the checkout, stale-task risk stated) or split A2 into ⓒ (docs, PR 1) + ⓐ (code, PR 2 after L1 ⓐ). State the choice as part of A2's 판정 질문.
- PR 1 size: A1 ⓐ is a tokenizer rewrite + target-checkout resolution + 6 argv forms in one commit on a hook every Bash call passes through. ⓑ is the small-PR fallback and is offered; acceptable, but the 구현 형태 line should say PR 1 = "A1 ⓐ or ⓑ per Ted" so the "small" expectation is explicit.
- Shared files across PRs (`gates/run.sh` A4/B3/L6, `README.md` A1⑺·A3/C2) are noted at lines 47, 92, 315. OK.

**3. Options / recommendations**
- L2 ⓑ (begin 연쇄 차단) has a migration hole: the store already holds 204 tasks with no close record and stale baselines. On the rule as written 「종료 기록 없는 researcher task 가 있고 그 baseline 대비 변경이 있으면 거부」, nearly every researcher begin (including the SubagentStart auto begin) would be rejected right after PR 2 merges, until prune `--apply`, which is Ted-gated. Change: add a rule for pre-existing tasks (treat tasks created before PR 2 as closed, or only consider tasks with a close-record schema) to L2's 완료 기준, and make it a 판정 질문.
- L2 ⓑ vs documented researcher flow (`lifecycle-evidence.md:43`, artifact task opened after auto task): 완료 기준 ③ covers the "no changes yet" order only; say explicitly that writing under `runtime:artifacts/` before the artifact begin will be rejected under ⓑ, or exclude `runtime:artifacts/**` from the change set.
- No recommendation contradicts an approved intent/ADR: B3 ⓐ is compatible with ADR-0004, C9 aligns with ADR-0001 `baseRef: head`, A4 ⓐ matches AGENTS.md 78 semantics, B1 ⓒ correctly flags that it loosens `414f51e7` and asks. T1 ⓐ ordering after PR 2 is right.
- Missing option, minor: B1 could also list ⓓ "re-run `required-gates` on base-branch update (`pull_request` `synchronize` only fires on head)" as considered-and-rejected, so Ted sees why ⓒ is the only code fix.

**4. Completeness vs advisor2 §4 top-7**
- 1→A1, 2→A2/A3, 3→T1/C5/B4/B6, 4→L3/L4, 5→L1/L2, 6→B1/A4/B3, 7→C1/C2/T3: covered.
- Gap in #7: the user-memory index lines (「뮤텍스 없다」 · 12/30 turns · 「보류」 · 「worktree 훅 없음」 · `required-gates-stale-pr-base`) have no owner; only B1 mentions memory (line 454). Add one T item or a 범위 밖 line: 「사용자 메모리 갱신 — 저장소 밖 · 메인 세션 · PR 2/3 병합 뒤」.
- advisor2 §3 "positive baseline" is absent (harness-contract, agent-bridge, 156 unit tests green at 67a03a05). One line in 메타 or at the top of 문제 would help grill-me readers size the gap. Optional.

**5. Template and judgeability**
- Headings match TEMPLATE order; extra 구현 형태 and group sections sit between 제약 and 설계트리 as requested; 설계트리/확인 hold 〈판정 대기〉 placeholders, fine pre-grill. Every item has 선택지 · 권장 · 완료 기준 · 판정 질문, so group-wise judging works.
- Deviation: 문제 is 9 code-dense bullets with file:line, versus the template's 「현상 1~3행. 코드가 아니라 사용자·운영 관점」. Suggest 5 operator-view lines (one per group) and leave cites to the items. Optional.
- Load: 39 items / ~48k tokens. Judgeable in one session only group-by-group as planned; A (5 items, 4 questions) is the right first gate.

Required changes before /grill-me: (a) A2 ⓐ dependency on L1 resolved or split, (b) A3 guard-header ownership fixed and line 138 corrected, (c) C10 grep vs `decision-number-guard.sh:27`, (d) L2 ⓑ pre-existing-task rule and `runtime:artifacts` ordering, (e) memory-drift owner line. Files: <home>/.claude/jobs/aa678208/tmp/intent-draft/2026-09-25-harness-improvement.md (lines 106, 113-118, 138, 242-246, 378-384, 449-468).