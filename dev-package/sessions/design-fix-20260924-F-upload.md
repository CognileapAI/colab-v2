# design-fix 20260924 · 수정 레인 F-upload 보고

- spec: `dev-package/prd/specs/S-DESIGN-FIX-20260924.md` 「통합 수정」 수정 레인 표 F-upload 행 · 「확정 값」 2
- 결함 원문: `dev-package/sessions/design-fix-20260924-acceptance.md` A17 · A19
- 기준 HEAD: `bee7786f`(브랜치 `worktree-design-review-apple-20260924`) · 레인 브랜치 `worktree-wf_808554ed-fad-2`
- lifecycle task: `0d856d1fa8334f2db16311dc7b0c2b8e`(role lane-worker · 선언 게이트 4 — frontend-typecheck · frontend-test · frontend-fixture-reach · frontend-design-lint)
- 준비: `frontend/` 에서 `npm ci` 종료 0
- 파일 면: `frontend/src/components/upload/UploadModal.tsx`(변경) · `frontend/src/components/upload/GridAttachEntry.tsx`(변경 0) · 새 시험 `frontend/test/design-fix-20260924-F-upload.test.tsx` · 이 보고서

## 1. 단계 · 커밋

| 단계 | 커밋 | 변경 파일 |
|---|---|---|
| 시험 작성 | `dc821b1a` | `frontend/test/design-fix-20260924-F-upload.test.tsx`(새 파일 · 8건) |
| 구현 | `6d254ff4` | `frontend/src/components/upload/UploadModal.tsx`(+4행) |
| 보고 | 이 파일의 커밋 | `dev-package/sessions/design-fix-20260924-F-upload.md` |

구현 커밋의 변경 파일은 `frontend/src/**` 1개뿐이고 `frontend/test/**` · `gates/**` · `contracts/**` 는 0(`git show --stat 6d254ff4`). `COLAB_FIX_LANE` 훅은 이 환경에서 걸리지 않아 규율로 지켰다.

## 2. 항목 · before → after · 시험

| id | 파일 | before | after | 시험(`design-fix-20260924-F-upload.test.tsx`) |
|---|---|---|---|---|
| A17 | `UploadModal.tsx` 배경 `div[data-testid=upload-backdrop]` | 닫는 동안 `data-state="closing"` 만 붙고, 누름 차단은 `upload.css` 의 배경 `pointer-events: none` 한 겹 — 안쪽에서 `pointer-events: auto` 를 명시한 자손은 누름을 받음 | `inert={closing ? true : undefined}` — 닫는 동안 배경과 하위 전체가 hit-test·초점에서 빠짐(명시 `auto` 자손 포함). 다시 열어 `closing` 이 풀리면 `inert` 도 풀림 | 「A17 닫는 동안 모달 전체가 inert」 5건 — 열림 중 inert 0 · 닫는 중 배경 inert ＋ 하위 전 요소 `[inert]` 조상 보유 · 명시 `pointer-events:auto` 패널·그 안 단추도 inert 안 · UploadEntry 다시 열기 뒤 inert 해제 · 전환 0 이면 같은 틱 닫힘 |
| A19 | `GridAttachEntry.tsx` | `open`/`rendered`/`onCloseStart` 배선에 동작 시험 0 | 코드 변경 0 · 동작 시험 3건 추가 | 「A19 GridAttachEntry — 닫는 도중 「기준 격자 추가」를 다시 누르면 같은 창으로 돌아온다」 3건 — 격자 추가 모드로 뜸 · × (0.3s 스텁) → closing → 다시 열기 → closing 해제 · transitionend 와 대비 타이머(350ms) 뒤에도 언마운트 없음(onClose 미호출) · 다시 열지 않으면 transitionend 뒤 언마운트 → 새 모달 |

## 3. RED 증거

- 시험 작성 커밋 `dc821b1a` 에서 `npx vitest run test/design-fix-20260924-F-upload.test.tsx`: `Tests 3 failed | 5 passed (8)`.
  - A17 3건 실패, 사유는 단언 불일치 — `AssertionError: expected false to be true`(배경 `hasAttribute('inert')`) · `AssertionError: expected null not to be null`(명시 `auto` 패널의 `[inert]` 조상).
  - 구현 전 green 5 = A17 회귀 고정 2(열림 중 inert 0 · 전환 0 즉시 닫힘) ＋ A19 3.
- A19 는 기존 배선을 고정하는 동작 시험이라 구현 전 GREEN 이다. 오라클 확인용 변이: `GridAttachEntry.tsx` 의 `open={open}` 을 `open={true}` 로 바꾸면(커밋하지 않고 되돌림) `AssertionError: expected 'closing' not to be 'closing'` 으로 RED(`Tests 1 failed | 2 passed | 5 skipped`).
- 구현 커밋 `6d254ff4` 뒤: F-upload 8건 ＋ L2 35건 `Tests 43 passed (43)`.

## 4. 시험 계수

- 구현 전(기준 `bee7786f` · `npx vitest run`): `Test Files 134 passed (134)` · `Tests 1732 passed (1732)`.
- 구현 뒤: 135 파일 · 1740건(＋8). 게이트 run 계수는 §5.

## 5. 게이트

증거 위치: `.git/colab-harness/c3bd22c78b4357f629784d96aebcfccd/0d856d1fa8334f2db16311dc7b0c2b8e/<run_id>/gate-summary.json`

| run_id | HEAD | green | red_판정 | red_준비 | 비고 |
|---|---|---|---|---|---|
| `ea9c7ee532f24f63b2e8dfc6643403c3` | `6d254ff4` | 3 | 1 | 0 | `frontend-test` 1건 실패 — `test/dataset-preview-source-grid.test.tsx` 「격자 해상도와 원본 배열 크기를 함께 캡션으로 낸다」 `findByTestId('preview-map')` 기본 1000ms 대기 초과(`Tests 1 failed \| 1739 passed (1740)`). 같은 파일 단독 실행 `Tests 5 passed (5)` · 기준 전수 실행에서도 green |

- 최종 판정 run 은 이 보고서 커밋 뒤 같은 task 로 실행하며, run_id 와 3계수는 레인 최종 메시지의 `COLAB_HANDOFF` 행에 적는다(보고서를 게이트 뒤에 고치면 H7 파일 hash 대조가 깨진다).
- `frontend-visual` 은 선언·실행하지 않았다 — agent-browser 를 띄우지 않았다.

## 6. 하지 않은 것

- 실제 브라우저에서 닫는 중 미리보기 도구 패널 누름 통과 확인(agent-browser) — 미실행. jsdom 은 `inert` 의 hit-test 효과를 계산하지 않으므로 이 레인의 증거는 속성 단언까지다.
- `preview.css`:255-260 의 `pointer-events: auto` 선언 변경 — 파일 면 밖(F-upload 는 TSX 2개). `inert` 가 조상에서 덮으므로 필요 없다.
- `GridAttachEntry.tsx` 코드 변경 — A19 는 시험 추가 항목이며 기존 배선이 시험을 통과했다.
- `test/dataset-preview-source-grid.test.tsx` 의 1000ms 대기 초과 — 파일 면 밖. 어느 게이트에도 「부하 중 시간 초과」로 따로 걸리지 않고 `frontend-test` 판정 red 로만 드러난다 → 후속 항목.
- 병합·PR 게시 — 하지 않음.
