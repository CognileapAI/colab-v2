# design-fix 20260924 · 통합 레인 F-int 보고

- spec: `dev-package/prd/specs/S-DESIGN-FIX-20260924.md` 「확정 값」 2(닫는 도중 다시 열면 입력 유지) · PRD-13(완전히 닫힌 모달은 ① 에서 연다)
- 입력: Fable advisor ② 지적 4건(등록 뒤 재열기 · setPointerCapture 가드 · 정리 주석 · 보고서 정정)
- 기준 HEAD: `e086bd67`(브랜치 `worktree-design-review-apple-20260924`) — `git merge --ff-only e086bd67…` 뒤 `git rev-parse HEAD` 일치 · 레인 브랜치 `worktree-wf_fea14b91-0c8-1`
- lifecycle task: `4eebb149e5af47c7b3550f276091edb6`(role lane-worker · 선언 게이트 4 — frontend-typecheck · frontend-test · frontend-fixture-reach · frontend-design-lint)
- 준비: `frontend/` 에서 `npm ci` 종료 0
- 파일 면: `frontend/src/components/upload/{UploadModal,UploadEntry,GridAttachEntry}.tsx` · `frontend/src/components/preview/useZoomPan.ts` · 새 시험 `frontend/test/design-fix-20260924-F-int.test.tsx` · 보고서 4개(`-L1` · `-L2` · `-L3` · `-F-upload`) · 이 보고서. CSS 변경 0 → `frontend-visual` 미선언·미실행(agent-browser 기동 0).

## 1. 단계 · 커밋

| 단계 | 커밋 | 변경 파일 |
|---|---|---|
| 시험 작성(RED) | `d6dc9517` | `frontend/test/design-fix-20260924-F-int.test.tsx`(새 파일 · 5건) |
| 구현 2·3 | `bee4f7d6` | `frontend/src/components/preview/useZoomPan.ts` |
| 구현 1 | `275ba067` | `UploadModal.tsx` · `UploadEntry.tsx` · `GridAttachEntry.tsx` |
| 보고 정정 4 | `6b9272b4` | 보고서 4개 |
| 보고 | 이 파일의 커밋 | 이 파일 |

- 구현 커밋 `bee4f7d6`(1파일) · `275ba067`(3파일)의 변경 파일은 `frontend/src/**` 뿐이고 `frontend/test/**` · `gates/**` · `contracts/**` 는 0(`git show --stat` 로 확인).

## 2. 항목 · before → after

| # | 파일 | before | after | 시험(`design-fix-20260924-F-int.test.tsx`) |
|---|---|---|---|---|
| 1 | `UploadModal.tsx` · `UploadEntry.tsx` · `GridAttachEntry.tsx` | 등록 성공(submit 두 갈래 `navigate` 앞) · 격자 반영 성공 뒤에도 `beginClose()` → `onCloseStart()` → 부모 `open=false`. 0.3초 닫기 전환 사이 진입 단추를 누르면 부모가 `open=true` 로 되돌려 **끝난 모달**(등록 카드 · 입력 그대로)이 되살아남 | 성공 경로 3곳이 `closeAfterCommit()` → 같은 `beginClose()` 를 타되 `onCloseStart({ completed: true })`. 부모의 열림·그려 둠·세션 번호를 `useUploadModalPresence()`(UploadModal.tsx) 한 벌로 합치고, 완료된 닫기 도중 다시 열면 세션 번호를 올려 `key` 로 **새 모달**(① · PRD-13)을 세움. 사람이 닫은 미완 세션의 되살리기(값 2)는 그대로 | 「F-int 1 UploadEntry」 1건 · 「F-int 1 GridAttachEntry」 1건 — 성공 → `data-state="closing"` → 진입 단추 → `data-scene="pick"` · `up-files` 0 · `reg-steps` 0 · closing 아님 · 앞 모달의 대비 타이머(420ms) 뒤에도 같음. UploadEntry 는 `/datasets/<id>` 이동도 확인 |
| 2 | `useZoomPan.ts` 누름 처리기 | `setPointerCapture?.()` 가 던지면(NotFoundError) 처리기가 예외를 밖으로 내고 `drag.current` 가 남음 → A27 「끌기 중 다른 포인터 무시」가 뒤이은 포인터를 모두 막음 | `try/catch` — 예외를 삼키고 그 포인터의 `drag.current`·표본을 지움. 원문 `setPointerCapture?.(` 는 유지(L3 정적 단언 `:244`) | 「F-int 2 useZoomPan」 3건 — 예외 미전파 · 다른 포인터 끌기가 화면을 옮김 · 던진 포인터 자신의 이동은 끌기가 아님 |
| 3 | `useZoomPan.ts` 창 리스너 효과 정리 주석 | 「리스너를 새로 걸 때 멈춘다(A41)」 | 「언마운트 때만 돈다 — `clampView`·`stopInertia` 는 안정 참조 · A41 은 `remeasure` 가 맡는다」. 안정 참조 근거: `stopInertia` 의존 `[]`(:218) · `clampView` → `boxes` → `box`·`contentSize` 의존 `[]` | 주석만 |
| 4 | 보고서 4개 | 아래 §4 | 〔정정 2026-09-25 · 통합 F-int〕 표지로 추가 | — |

- `UploadModal` 공개 인터페이스 변화: `onCloseStart` 인자 `{ completed: boolean }` 추가(선택 prop 그대로) · 새 export `useUploadModalPresence`.
- 「완료된 닫기」 범위 = 등록 성공 2곳(`submit` 의 대표 이미지 재시도 갈래 · 신규 등록 갈래) ＋ 격자 반영 성공 1곳. 데이터셋이 생긴 뒤 대표 이미지 실패로 남은 모달을 사람이 × 로 닫는 경우는 미완 세션으로 두었다(재시도할 입력이 남아 있음).

## 3. RED 증거

- 시험 작성 커밋 `d6dc9517` 에서 `npx vitest run test/design-fix-20260924-F-int.test.tsx`: `Tests 5 failed (5)` · 모두 단언 실패.
  - F-int 1 UploadEntry: `AssertionError: expected 'register' to be 'pick'`(등록 카드가 되살아남)
  - F-int 1 GridAttachEntry: `AssertionError: expected 'analyze' to be 'pick'`(입력이 남은 모달이 되살아남)
  - F-int 2 ①: `AssertionError: expected DOMException{ stack: 'NotFoundError:…', …(1) } to be null`
  - F-int 2 ②: `AssertionError: expected 0 to be greater than 0`(두 번째 포인터 무시됨)
  - F-int 2 ③: `AssertionError: expected { x: +0, y: 40 } to deeply equal { x: +0, y: +0 }`(끝난 포인터의 끌기가 남음)
- 구현 뒤 같은 파일 5/5 통과 · 관련 8파일(`F-int` · `F-upload` · `L2` · `L3` · `F-preview` · `grid-attach` · `register-steps-20260907` · `unfinished-uploads`) `Tests 142 passed` · `tsc -p frontend --noEmit` 종료 0.

## 4. 보고서 정정(docs only)

| 파일 | 항목 | 정정 |
|---|---|---|
| `design-fix-20260924-L1.md` §1 RED 확인 | A9 | 구현 전 green 17 의 설명 목록에 `.btn-primary:active` 불변 · `primitives.css` `!important` 0 추가(시험 `:176` · `:179`) |
| `design-fix-20260924-L2.md` 상태줄 · §4-2 | A16 | 최종 run = `9e10e397e0294bda9418d9033f1b92c8`(커밋 `1b263dae`) green 5 / 0 / 0. `9e65e0d6` 은 `3d1cbb2e` 에서 잰 낡은 run |
| `design-fix-20260924-L2.md` §2 RED | A20 | PRD-13 시험의 RED = 모달이 남지 않아 고정물(`transitionEnd(modal()…)`)이 던짐 — 단언 실패 아님 |
| `design-fix-20260924-L2.md` §6 | — | 「등록 뒤 0.3초 안 재열기 = 끝난 모달」 서술이 이 레인 수정으로 바뀌었음을 표지 |
| `design-fix-20260924-L3.md` 추기 | 최종 run | `ec36f40a` → 유효 `6b3eef0a034748edb93ee6b8b1dd54dc`(커밋 `cfaa1344`) green 5 / 0 / 0 |
| `design-fix-20260924-L3.md` RED 기록 | A32 | 커밋된 L3b RED 는 import 해석 실패 · 동작 RED 는 커밋하지 않은 임시 스텁에서 나옴 |
| `design-fix-20260924-F-upload.md` §5 | 최종 run | `75767f9bbbfe4707bb2797f0eed2947a`(커밋 `50bab4d6`) green 4 / 0 / 0 |

- 세 run 은 Git common `colab-harness/<checkout>/<task>/<run>/gate-summary.json` 을 직접 읽어 `counts` · `commit` 을 대조했다.

## 5. 시험 수 · 게이트

- 구현 뒤 전체 `npx vitest run`: `Test Files 139 passed (139)` · `Tests 1819 passed (1819)`. 새 파일 1개 · 5건 추가, 기존 시험 파일 변경 0.
- 게이트: `COLAB_TASK_ID=4eebb149e5af47c7b3550f276091edb6 bash gates/run.sh task`(선언 4종 순차 1회). 이 보고서를 커밋한 **뒤** 실행하며, run_id 와 3계수는 레인 최종 메시지의 `COLAB_HANDOFF` 행이 정본이다(보고서를 게이트 뒤에 고치면 H7 파일 hash 대조가 깨진다).

## 6. 하지 않은 것 · 남은 위험

- 실제 브라우저(agent-browser)에서 등록 성공 직후 재열기 확인 — 미실행. 증거는 jsdom RTL(0.3s 전환 스텁)까지다.
- `frontend-visual` — CSS 변경 0 이라 선언하지 않았다.
- `setPointerCapture` 가 NotFoundError 외 이유(예: 연결 끊긴 요소의 InvalidStateError)로 던지고 포인터가 실제로 살아 있으면, 그 한 번의 끌기는 시작되지 않는다(다음 누름부터 정상). 끌기 상태를 남겨 이후 모든 포인터를 막는 것보다 작은 손실로 판단했다.
- 모달 쪽 되살리기 효과(`props.open` 복귀)는 완료된 닫기를 따로 거르지 않는다 — 두 부모가 `key` 로 새로 마운트하므로 앞 인스턴스는 `open=true` 를 받지 않는다. 다른 부모가 `useUploadModalPresence` 없이 `open` 만 되돌리면 끝난 모달이 되살아난다.
- 병합·PR 게시 — 하지 않음.
