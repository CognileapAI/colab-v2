## WU-B8 gate ② review — lane p3-lineage-unknown (3427ec4..c11efa2 +128b256)

For:
- 6-branch `lineage_state()` matches PRD-27 table verbatim in order and source: ④ via `user_set_level(core)` (human column), ③ via injected `unknown_declared` (no N+1), ①② byte-identical. 14 new server tests map 1:1 to the 7 acceptance criteria; auto `mark_unknown` provably gone (row-count test). Contract opens exactly one key, generated in sync, schema 0, 7 gates green on rebased tree.
- Server 400 remains the final defence even though the modal computes `lineageUnknownEffective` from confirmed parents (`LineageStep.tsx:194` filters `confirmed`) and `level !== 'Lv0'`.

Against:
- Criterion ⑦ 「홈 타일 숫자 = 링크가 여는 목록 건수」 is claimed green but false in the running app: `DatasetsPage.tsx:30` `params.get('lineageState')` takes the first repeated value → list = `확인 필요` only while tile counts `확인 필요`+`기록 없음`. The lane's own test ㈒ checks `URLSearchParams.getAll` on the constant and never renders the page — the mismatch the WU was told to close has moved from constant-vs-constant to link-vs-parser.
- No other whole-lane objection; evidence that would reverse the verdict: a page-level test showing the list honours both values.

Verdict: approve-with-changes (Fix 1 병합 전 필수).

Risks:
1. Prod/staging rows with 0 parents ∧ no unknown row ∧ no `source_label` ∧ human Lv NULL flip `기록 없음`→`확인 필요` silently; gate DB (seed via SQL) cannot show this. Deploy-window measurement still owed.
2. Whitespace-only `sourceLabel` ("  ") passes ⑤ as `원천` — `ingestion.py:551` stores untrimmed. Pre-existing, now load-bearing for a state decision.
3. Modal keeps `lineageUnknown=true` while disabled/hidden; after unlinking or Lv0→Lv1 the box reappears checked. Reason text promises this, but untested.

Missed:
- Docstring ⑥ 「사람 Lv ≥ Lv1」 vs code `return "확인 필요"` for NULL Lv (round §134 intends NULL→⑥; docstring should say so).
- `test_registering_without_parents_is_recorded_as_unknown_not_as_a_guess` name contradicts its new assertion.
- Flip-back (Lv0→Lv1 shows checkbox again) not exercised; `Policy_홈_대시보드 §4` file not located for the 2-value justification.
- `UploadModal.tsx:473` uses literal `'Lv0'` while `:756` uses `LV0` const.

Fixes:
1. [병합 전 필수] `DatasetsPage.tsx:30` → `const lineageState = params.getAll('lineageState'); if (lineageState.length) filters['계보'] = lineageState;` and extend FE test ㈒ to render `DatasetsPage` at `LINEAGE_TODO_PATH` and assert both states reach the catalog filter.
2. Rename the registration test to `…is_needs_check_not_a_guess`; fix `lineage_state()` docstring ⑥ to 「부모 0 ∧ 선언 없음 ∧ 원천 표기 없음 (사람 Lv NULL 포함)」.
3. `ingestion.py:551` strip `sourceLabel` and treat empty as absent (or state explicitly that ⑤ is truthiness-based).
4. Log deploy-window item: run `부모 0 ∧ unknown 행 없음 ∧ source_label NULL` count on staging/prod before release.
