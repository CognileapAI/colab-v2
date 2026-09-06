# advisor ② — WU-A13R (공통 토스트 ＋ 문면 21행) 수용 검토

- 대상 = 워크트리 `.claude/worktrees/agent-acb1c2201b3bec43e` · `52bb4de`(기점 `93329a6` ＋1) · 작업 트리 clean.
- 검토 범위 = diff 9 파일(+679/−16) 전문 · 세션 노트 · PRD-43 표 · rev2 원문 `toast()` 전수 · intent 원한 결과 1항.

## For:
- 21행 상수·표(`COPY_ROWS`)가 `toastCopy.ts` 한 파일이고 표가 상수를 참조해 파일 안에서도 두 벌이 없다. 표의 `…`·「3종」 두 행은 rev2 원문 `toast()` 축자와 일치(직접 대조 — `S-04` 1건 · `E-07` 3건 전부 원문에 존재).
- 계약 0 · 스키마 0 · 마이그레이션 0 실측(`git diff 93329a6..52bb4de -- contracts/ db/` 공집합). 세션 노트에 「main 과 동일」류 수용 문구 0건 · 좁은 게이트 3종＋`work-item-consistency` green 은 오케스트레이터 재실행값.
- 폐기 비용 = 낮음. 남은 결함은 `Toast.tsx` 한 파일 5행 안이고 문면 상수·시험은 그대로 쓴다.

## Against:
- **완료 조건 「스스로 사라진다」가 실화면에서 성립하지 않는다.** `FileDropCard.tsx:195` 가 `onDismiss={() => setMixedNotice(false)}` 인라인 화살표를 넘기고 `Toast.tsx` `useEffect` deps 가 `[message, dismissMs, onDismiss]` 다. 부모가 다시 그릴 때마다 함수 identity 가 바뀌어 타이머가 **초기화**되고 `setShown(true)` 가 다시 선다. `UploadModal.tsx:161-191` 은 파일을 놓는 즉시 업로드를 시작하고 정수 퍼센트마다 `setTransfer` 로 재렌더한다(`FileDropCard` 는 memo 없음 · `:589`). 결과 = 혼합 놓기 뒤 업로드 진행 중엔 토스트가 진행이 끝난 뒤 4초까지 남는다. 시험 `ext-mixed-toast-20260906.test.tsx` 의 Harness 는 재렌더가 없어 green 이다 — **하네스 조건에서만 성립하는 green**.
- 이 컴포넌트는 A12R·A7R·A9R·B3·B5 가 그대로 부른다(PRD-43 「먼저 서야 한다」). 지금 병합하면 후속 레인 전부가 같은 호출 관례(`onDismiss={() => …}`)를 복제한다.

## Verdict: approve-with-changes — **ff-merge 는 Fix ① 반영·`frontend-test`·`frontend-typecheck` 재green 뒤에만.** 문면 21행·시험·format.ts 변경은 그대로 승인.

## 체크리스트
- ① revision 체인 = N/A. `db/platform`·`db/ai` 무접촉 실측.
- ② 「main 과 동일」 = 해당 문구 0건. 수용 근거는 게이트 4종 green 이고 동등성 주장 없음.
- ③ intent 원한 결과 1항(「공통 토스트 1개 ＋ 문면 21행 코드 존재 ＋ 하드코드 중복 0건」) 대조 —
  - 충족 = 컴포넌트 1개 · 21행 존재 · 완전일치 중복 0 · F-11/D-13 보간 · D-07 `2025-06 ~ 09`(시험 3건).
  - **미달 1** = 자동 사라짐이 부모 재렌더 아래서 성립하지 않음(Against 1).
  - **미달 2(계측 사각)** = 중복 시험 `literal()` 이 따옴표 구분자를 요구해 **JSX 맨몸 텍스트**를 세지 못한다. 실례 = `RegisterArea.tsx:615` 자체가 따옴표 없는 JSX 텍스트다. 21행 문면이 `<p>문면</p>` 로 적히면 「0건」이 그대로 green 이다.
  - 초과 = 없음. `.up-toast` 철거·`FileDropCard` 배선은 PRD-32 가 이 WU 몫이라 범위 안. staging DB 읽기(세션 노트 §7)는 PRD-32 「센다」 이행 · `SELECT` 만 · ㉴ 금지(쓰기) 위반 없음.
- PRD-43 21행 축자 대조 = **완전일치 18** · 원문 보완 3(`S-04` 표의 `…` 확장 · `E-07` 표 무문면→rev2 3종 · `V-01` 머리 `crs` 보간, 예시 인자로 표 문자열 재현). 3건 모두 rev2 `업로드_계보_260905_rev2_이태헌.html` 의 `toast()`/`d.meta.crs + ' · PNG + 경계 좌표'` 와 일치. 개발 세션 창작 0.

## Risks:
- 1 · `TOAST_DISMISS_MS = 4000` 은 PRD·rev2 어디에도 없는 레인 선택값 — `[미확인]` 표기 없이 상수로 굳음. 후속 WU 가 기준으로 인용할 위험.
- 2 · `toastCopy.ts` 머리 주석 「표에 다시 적지 않는 축자 2건」이라 적고 실제로는 PRD-32 1건만 있다. PRD-31 `가공 전 데이터를 추가했어요. 직접 연결로 남아요` 는 `src/` 전체에 0건 — 담는 WU 가 따로 적으면 「한 곳」이 파일 두 곳이 된다.
- 3 · `N-11` 은 R-A′ 5 WU 중 어느 것도 `LineageSection.tsx` 를 소유하지 않아 이 라운드에서 방치될 경로.

## Missed:
- JSX 맨몸 텍스트 중복 미계측(위 미달 2).
- `Toast` 타이머 deps 결함을 잡는 시험 부재(부모 재렌더 케이스).
- 대장 `WU-A13R` 은 `in_progress` 그대로 — 병합 시 `done` 전이는 오케스트레이터 몫이며 `evidence` 경로는 기재됨.

## Fixes:
- ① **[병합 전 필수]** `Toast.tsx` — `onDismiss` 를 ref 에 담고 effect deps 를 `[message, dismissMs]` 로 줄인다(`const cb = useRef(onDismiss); cb.current = onDismiss;` → 타이머 콜백에서 `cb.current?.()`). 시험 1건 추가 = 부모가 `onDismiss` 새 화살표로 3회 `rerender` 해도 `TOAST_DISMISS_MS` 경과 시 사라진다. `frontend-test`·`frontend-typecheck` 단독 재green 뒤 ff.
- ② **[병합 전 권장 · 5행]** `toast-copy-20260906.test.tsx` `literal()` 을 따옴표 또는 `>`…`<` 둘 다 잡게 확장 — `new RegExp(\`(['"\`])${esc}\\1|>\\s*${esc}\\s*<\`)`. `MemberPermissionGrid.tsx:67` 은 전체 문장이 달라 여전히 걸리지 않는다.
- ③ `toastCopy.ts` 머리 주석 「2건」→ PRD-31 문면을 같은 절에 상수로 추가(`PRE_LINEAGE_ADDED`)하거나 「1건」으로 정정. PRD-43 축자가 「같은 컴포넌트를 쓴다」이므로 추가 쪽이 「한 곳」 규칙과 정합.
- ④ `TOAST_DISMISS_MS` 주석에 `[미확인] 레인 선택값 · 정본 없음` 1행.

## 자기 표시 3건 판정 — Ted 결정 필요 여부
- ㈎ 완전일치 중복만 계측 = **Ted 결정 불요.** 부분 일치는 `MemberPermissionGrid.tsx:67` 오검출을 만든다는 레인 근거가 맞다. 다만 Fix ② 의 JSX 텍스트 사각은 결정 아닌 계측 보강.
- ㈏ `J-12` = **Ted 결정 불요.** `colab-rules §7` 「코드를 기획에 맞추는 방향이 기본」 → A7R 이 `RegisterArea.tsx:615` 를 `QUICK_PROJECT_NOTE` 호출로 교체. **`N-11` = Ted 결정 필요(라운드 끝 묶음 질의 · A12R/A7R 차단 아님)** — PRD 문면이 「가공 방식은 화살표 라벨」 안내를 잃는다. 선택지 = ⓐ PRD 축자로 교체(안내 손실) ⓑ 현재 문장을 정본으로 올리고 PRD-43 표 정정. 소유 WU 가 R-A′ 에 없으므로 결정 전까지 무변.
- ㈐ `D-07` 월 한정 = **Ted 결정 불요(기본 유지).** PRD-43 수용 기준이 단위 `월` 만 지목하고 `일` 확장은 PRD-18 시험 `interval-period-20260906.test.tsx:311` 과 충돌. 표 문면 「연·월이 겹치면」의 `일` 적용 여부는 라운드 끝 묶음 질의에 1행 첨부.

## A12R/A7R 착수 조건
- Fix ① 반영 커밋이 `integration/r-a2` 에 ff 된 뒤 착수. 후속 레인 지시문에 「`Toast` 의 `onDismiss` 는 인라인 화살표 허용(컴포넌트가 ref 로 받음)」 1행 명시.
