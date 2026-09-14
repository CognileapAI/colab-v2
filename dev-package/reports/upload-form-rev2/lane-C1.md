# 레인 C1 — 업로드 ③ 「AI 제안받기」 버튼과 호출 경로 제거

- 회차 = 업로드 폼 rev2 · 기점 `feature/rtf400_upload_form` (`5a172e78`)
- 근거 = 기획자 2026-09-13 피드백 「반쪽 AI 제거」 · 사용자 결정 2026-09-13/14 「제거 구현 · 병합은 Ted 판정 대기(판정문 ㉮)」
- 범위 = **프런트만.** AI 서비스 · 계약(`contracts/**`) · 생성 타입(`frontend/src/generated/**`) · DB · 마이그레이션 **무접촉**

---

## 1. 실측 — 제거 전 자리 목록

`grep -rn "lin-ask\|suggestLineage\|lineageSuggest\|ai-suggest" frontend/src frontend/test` 실측 9건.

| 자리 | 파일 | 처리 |
|---|---|---|
| 버튼 `lin-ask` · 안내문 `lin-ask-note` | `frontend/src/components/lineage/LineageStep.tsx` | 제거 |
| `.lin-ask` · `.lin-ask .muted` | `frontend/src/components/lineage/lineage.css` | 제거(개정 표시) |
| `lin-ask` 클릭 3자리 | `frontend/test/upload.test.tsx` | 제거·재작성 |
| `lin-ask` 클릭 1자리 | `frontend/test/lv-display-unify-20260908.test.tsx` | 블록 제거 |

지시문 패턴(`suggestLineage`·`lineageSuggest`·`ai-suggest`)은 **실물 0건**. 실제 식별자는
`suggestions` / `LineageSuggestionResponse` / `ParentCandidateSuggestion` / `ProcessingMethodSuggestion` 이다.

## 2. 제거한 것 — `LineageStep.tsx`

- 버튼 블록 `<div className="lin-ask">` 전체(버튼 · `lin-ask-note`)
- 호출 훅 `askSuggestions` (`useCallback`) · `clues` (`useRef`) · `source.suggestions(...)` 호출 1자리
- 상태 넷 — `resp` · `unavailable` · `asked` · `asking`, 그리고 `methods`(가공 방식 제안 카드 상태)
- 제안 산출물 렌더 — `lin-scope`(뒤진 범위) · `lin-unavailable` · `lin-degraded` · `lin-raw` · `lin-empty`(0건 3문면) · `lin-method-card` 묶음(`lin-method-parent` 포함)
- 제안만 채우던 칸 — `ConfidenceChip`(`lin-confidence`) · 근거 줄 `lin-rationale` · `lin-method-done`
- 타입 가드 `isParentCandidate` · `isProcessingMethod` · `interface MethodCard` · 함수 `confirmMethod`
- 죽은 import — `useCallback` · `useRef` · `AiConfidence` · `LineageOrigin` · `LineageSuggestionResponse` · `ParentCandidateSuggestion` · `ProcessingMethodSuggestion` · `ctx.uploadId` 구조분해
- 자리 합침 — 종전 `{!asked && addBlock}` ＋ 버튼 ＋ `{asked && addBlock}` → `{addBlock}` 하나

## 3. 남긴 것 — 이유와 함께

| 남긴 것 | 이유 |
|---|---|
| `LineageSource.suggestions` (`types.ts`) · `lineageSource.ts` 의 구현 | **지시문 소유 범위 밖.** 두 파일은 「AI 제안 전용」이 아니고(`candidates()` 동거), 인터페이스 멤버를 걷으면 **시험 15개 파일**의 `const lineage: LineageSource = { async suggestions() … }` 스텁이 초과 속성 오류로 전부 red 가 된다(형제 레인이 편집 중인 `parent-picker-20260914.test.tsx`·`upload-form-rev2-20260914.test.tsx` 포함). **후속 항목 ①** |
| `frontend/src/generated/fe-core.ts` · `contracts/**` | 지시문 축자 「생성 타입과 계약은 손대지 않는다」 |
| `ParentCard.confidence` · `rationale` · `confirmedMethodText` (`types.ts`) | 계약 타입. 값이 항상 `null` 이 될 뿐 |
| `lineage.css` 의 `.lin-scope` · `.lin-empty` · `.lin-method-done` · `.conf*` | 거는 대상이 0건이 된 규칙. `.lin-empty` 는 상세 화면 `LineageSection.tsx` 가 **같은 이름으로 쓴다** — 이름만 보고 지우면 그 화면이 깨진다. **후속 항목 ②** |
| `upload/types.ts` 의 `datasetNameDraft`·`topic` 주석(제안 단서 언급) | 소유 범위 밖 파일 |

## 4. 시험 — red → green

**RED(실측)** — 새 음성 시험 3건 중 1건이 실패했다.

```
FAIL  test/upload.test.tsx > ③ 계보 확정 — AI 제안 버튼과 호출 경로가 없다 (기획자 9/13 · 판정 대기) > 제안 버튼과 안내문이 화면에 없다
AssertionError: expected <button type="button" …(2)></button> to be null
  ❯ test/upload.test.tsx:2217:45
```

**신설 음성 시험**(`frontend/test/upload.test.tsx`) 3건 —

1. `lin-ask`·`lin-ask-note` 부재 ＋ 화면 문자열에 `AI 제안` 0건
2. **스텁이 제안 3건을 내주는데도** 조회 호출 0건 · `lin-scope`·`lin-empty`·`lin-confidence`·`lin-rationale`·`lin-method-card`·`lin-unavailable`·`lin-degraded`·`lin-raw` 전부 0건
3. AI 없이 등록 완주 — 사람이 이은 관계 1건만 `origin: manual` 로 실린다

⛔ **빈 집합 위에서 통과하지 않는다** — 스텁(`kwraSuggestions()`)은 그대로 부모 후보 2건 ＋ 가공 방식 1건을 내준다. 스텁을 0건으로 낮춰 통과시키지 않았다.

**삭제한 시험 블록** — 재는 대상이 사라진 것만.

| 블록 | 재던 것 | 지금 |
|---|---|---|
| `③ 계보 확정 — 뒤진 범위를 먼저 밝힌다` (2건) | `lin-scope` · 단서 전달(`datasetNameDraft`·`subject`) | 제안 응답이 없다 |
| `③ 계보 확정 — 정직한 빈 상태` (7건) | `lin-empty` 3문면 · `degraded` · `rawDataLikely` · 조회 실패 | 같음 |
| `③ 계보 확정 — AI 응답 규격` (2건) | `[모두 승인]` 부재 · 확신도 enum ＋ 근거 필수 | 확신도·근거를 그리는 자리가 없다. **계약 쪽 규격은 그대로이고 서버 시험이 잰다** |
| `③ 계보 확정 — AI 제안은 사용자가 눌러 받는 보조다 (LV-2)` (6건) | 자동 호출 0건 · 누른 횟수 = 호출 횟수 | 버튼이 없다 |
| `lv-display-unify-20260908.test.tsx` 의 `② · ③` 블록 (2건) | **제안이 실어 온** `parentProcessingLevel` 로 서버 400 전 경고 | 제안이 부모 Lv 를 실어 올 자리가 없다 |

**재작성한 시험**(단언은 보존 · 카드 출처만 사람으로) — `확인 / 수정 / 거절` 3건, `부모 역할 2값` 1건, `직접 추가` 1건, `가공 방식` 1건, `확정 건수 표시기` 1건, 안내 문면 2건. 헬퍼 `openLineageWithAi`/`askAi` → `addParentByPicker(datasetId)`.

⚠ **커버리지 손실 1건을 숨기지 않는다** — `lv-display-unify` 의 수용 기준 ②③(제안이 실어 온 부모 Lv 로 **서버 400 전** 경고)을 재는 자리가 사라졌다. 사후 충돌 경고 자체는 사람이 이은 부모의 Lv 로 `upload.test.tsx` 와 서버 `test_lv_parent_rules.py` 가 그대로 잰다.

## 5. 문서 개정 표시

- `dev-package/prd/specs/R-A2.md` 「존치 6종」 행 — 「AI 계보 제안」에 취소선 ＋ 개정 주석
- `CLAUDE.md §0` 「AI 두 지점 ①」 행 — 현재 위상 개정 ＋ 종전 문면 취소선
- `dev-package/work-items.yaml` `LV-2` `note` — 개정 한 문단 추가. **`status: done` 무변경**(판정 재개봉 금지 · `.claude/rules/colab-rules.md §8`)

## 6. 후속 항목

1. **`LineageSource.suggestions` 인터페이스 멤버와 `lineageSource.ts` 구현이 호출자 0건으로 남았다.** 걷으려면 시험 15개 파일의 스텁을 같은 커밋에서 고쳐야 한다 — 형제 레인과 파일이 겹치므로 별도 레인이 맞다.
2. **`lineage.css` 에 거는 대상 0건인 규칙이 남았다**(`.lin-scope`·`.lin-empty`·`.lin-method-done`·`.conf`·`.lin-mcard`·`.lin-mparent`·`.lin-why`). ⚠ `.lin-empty`·`.lin-why` 는 상세 화면이 같은 이름을 쓴다 — **선택자 이름만 보고 지우면 안 되고** 컴포넌트별 실사용을 먼저 대조해야 한다.
3. **죽은 CSS 를 잡는 검사가 게이트에 없다.** `css_audit.py` 는 도구이고 `gates/run.sh` 의 판정 대상이 아니다 — 게이트 밖에만 있는 검사이므로 그 자체를 항목으로 올린다.
4. `frontend/src/components/upload/types.ts` 의 `datasetNameDraft`·`topic` 주석이 「제안 조회의 단서」를 설명한다 — 그 조회가 없어졌다(소유 범위 밖이라 이 레인은 손대지 않았다).
5. **`frontend-test` 가 같은 트리에서 뒤집힌다 — 시험 쪽 시간 초과다.** 실측 = 같은 커밋 트리(`4f4be08…`)로 게이트 묶음 6회 실행 · green 4회 · red(판정) 2회. red 일 때 실패한 파일은 매번 달랐고(`upload-transfer.test.tsx` · `dataset-preview-zoom.test.tsx` · `lineage-unknown-20260907.test.tsx`) **셋 다 이 레인이 건드리지 않은 파일**이다. 같은 셋을 단독 실행하면 42건 전건 통과하고, 게이트와 **같은 호출**(`CI=1 vitest run --reporter=default`)도 단독으로는 1342건 전건 통과했다. 원인 = `findByRole` 의 기본 대기 1초가 호스트 부하에서 초과된다(실례 `frontend/test/upload-transfer.test.tsx:326` `findByRole('button', { name: '표준 격자 가져오기' })`). ⚠ **어느 검사에 걸리는가** — `gates/run.sh frontend-test` 가 red 로 잡는다(green-by-skip 아님). 걸리는 자리가 있으니 결함은 **검사가 아니라 시험의 대기 시간**이다. ⛔ 이 레인은 시험 대기 시간을 늘리지 않았다 — 범위 밖이고, 늘리는 것이 옳은지부터 판정이 필요하다.
