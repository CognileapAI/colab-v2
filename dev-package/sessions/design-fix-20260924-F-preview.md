# design-fix 20260924 · 수정 레인 F-preview

- 기준: `bee7786f`(통합 브랜치 `worktree-design-review-apple-20260924`) · 브랜치 `worktree-wf_808554ed-fad-3`
- 오라클: `dev-package/prd/specs/S-DESIGN-FIX-20260924.md` 「통합 수정」 F-preview 행 · 확정 값 5·6 · 결함 원문 `dev-package/sessions/design-fix-20260924-acceptance.md` A23–A41 중 F-preview 14건
- 파일 면: `frontend/src/components/preview/{useZoomPan.ts,spring.ts}` · 새 시험 `frontend/test/design-fix-20260924-F-preview.test.tsx` · 기존 `design-fix-20260924-L3.test.tsx` · `-L3b.test.tsx`(시험 작성 단계만)
- lifecycle: `begin --role lane-worker` task `5e58a4455801455d9609d88a1d95c5b3` · 선언 게이트 4(`frontend-typecheck` · `frontend-test` · `frontend-fixture-reach` · `frontend-design-lint`)
- 커밋: `f346f825`(시험 작성 1) · `b4211f69`(시험 작성 2 · L3 #3 전제 정정) · `57195160`(구현) · 이 보고서 커밋

## 1. 항목 → 전후 → 시험

시험 파일 = `frontend/test/design-fix-20260924-F-preview.test.tsx`(12건). 행 번호는 구현 커밋 `57195160` 기준.

| 항목 | 전 | 후 | 시험 |
|---|---|---|---|
| A23 · A25 · A33 · A40 | `pointercancel` → `up()` 과 같은 처리 — 관성 시작 · 취소 좌표가 마지막 속도 표본 | 별도 `cancel()`(`useZoomPan.ts:514`) — `drag`·표본·`dragged` 비우고 관성 없음 | 「10px 넘게 끈 뒤 pointerCancel(0,0)」(:128) · 「취소 뒤 같은 포인터의 이동은 끌기가 아니다」(:146) |
| A26 | 잘린 목표 + `v0 > ω·\|x0\|` 이면 스프링이 목표를 지나치고 `clampView` 가 끝에서 급정거로 가림 | `capHandoffVelocity`(`spring.ts:28`) — `\|v0\| ≤ ω·\|x0\|` · 인계 때 적용(`useZoomPan.ts:496-497`). 잘리지 않은 투영 목표는 상한(≈7.8·\|v0\|)에 걸리지 않아 종전과 같음 | 단위 3건(:163 · :175 · :180) · 동작 「끝까지 50px 남기고 2000px/s」(:186) |
| A31 | L3b 주석 「매 프레임 범위 안이다」, 실제 표본 2점 | 매 프레임(`advance(16)` × 60) `y ≤ 경계` 단언 ＋ 경계 도달 직전 프레임 거리 ≤ 1px · L3b 주석을 「두 시점 표본」으로 고치고 위치를 가리킴 | :186 · `design-fix-20260924-L3b.test.tsx:222` |
| A24 · A28 · A34 | 출발 자리 = 렌더 시점 ref `viewNow` — 커밋 전 마지막 이동이 빠짐 | 출발 자리 = 첫 프레임 갱신 함수의 `cur`(최신 값) · 목표·인계 속도도 거기서 계산 · `viewNow` 제거 | 「마지막 pointermove 의 렌더 전에 pointerup」(:217 · act 밖 `dispatchEvent`) |
| A27 | 두 번째 포인터의 누름이 끌기를 가로챔 | `drag.current` 가 다른 id 면 누름 무시(`useZoomPan.ts:405`) | 「두 번째 손가락의 누름·이동·놓기」(:239) |
| A29 | `baseScale` effect 가 관성을 멈추지 않아 다음 프레임이 시작 자리(편차 0)를 덮음 | effect 첫 줄 `stopInertia()`(`useZoomPan.ts:573`) | renderHook — 경계 WIDE→NARROW(기본 배율 0.668)(:287) |
| A41 | 관성 프레임이 놓을 때의 목표·범위를 쥔 채 크기 변화 뒤에도 진행 | `remeasure`(resize · 원본 폭 학습) 첫 줄 `stopInertia()`(:539) · 포인터 리스너 effect 정리 때 `stopInertia()`(:529) | renderHook — 관성 중 resize(:303) |
| A30 | 속도 인계를 재는 동작 시험 없음 | 코드 변화 없음 · 시험 추가 | 「첫 프레임(16ms)의 자리가 놓은 속도 인계 값」(:318) — `spring(13, 목표, v, 0.016)` ± 5e-4 · v0=0 값과 1px 이상 차이 |
| A35 | 관성을 잡은 탭 뒤 click 이 값 조회로 감 | 누름 때 `caught = inertia.current !== null`(:407) · 놓기 때 `dragged = active \|\| caught`(:448) | 「관성 중 임계 안 누름·놓기 뒤 click 은 조회 0 · 그다음 평소 탭은 조회 1」(:343) |

### L3 #3 시험 전제 정정(`b4211f69` · 시험 작성 단계)

`design-fix-20260924-L3.test.tsx` 「11px 끌고 놓은 뒤의 click 은 값 조회 0 · 이어서 4px 안의 click 은 조회 1」은 실시간 타이머로 돈다. 첫 11px 끌기가 관성을 띄우고 둘째 탭이 그 관성 중에 떨어졌다(시각 의존). A35 구현 뒤 그 둘째 탭은 「관성을 잡는 탭」이 되어 조회 0 → 시험 실패. 첫 끌기를 150ms 멈췄다 놓게 해(마지막 100ms 이동 없음 → 관성 0) 둘째 탭이 평소 탭임을 보장했다. 두 단언은 그대로다. 구현 전 코드(`f346f825` 제품 파일)에서 L3·L3b 29건 통과를 확인한 뒤 커밋했다.

## 2. RED 증거

시험 작성 커밋 `f346f825` 시점(제품 코드 = `bee7786f` ＋ `capHandoffVelocity` 항등 자리표시) `npx vitest run test/design-fix-20260924-F-preview.test.tsx` → **10 실패 · 2 통과**. 실패는 전부 단언 실패(import 오류 0).

- A23/A25/A33/A40: `expected 'translate(0px, -521.4476492126457px) …' to be 'translate(0px, -464px) scale(1)'` · 취소 뒤 이동: `expected 'translate(0px, -1088px) scale(1)' to be 'translate(0px, -504px) scale(1)'`
- A26 단위: `expected 2000 to be less than or equal to 785.3981633984482` · `expected 2000 to be +0`
- A26/A31 동작: `expected 3.5643462163424147 to be less than or equal to 1`(경계 도달 직전 프레임 거리 3.56px)
- A24/A28/A34: `expected -396.8541666666668 to be close to -395.8541666666668, received difference is 1`
- A27: `expected -474 to be close to -524, received difference is 50`
- A29: `expected { x: +0, y: 278.336 } to deeply equal { x: +0, y: +0 }`
- A41: `expected 288 to be 138.67221304710762`
- A35: `expected "vi.fn()" to be called +0 times, but got 1 times`
- 통과 2건: A26 「상한에 걸리지 않으면 속도를 바꾸지 않는다」(항등 자리표시와 같은 값 — 회귀 고정용) · A30(속도 인계는 종전 코드도 맞음 — 시험 공백 항목).
- A30 변이 확인(커밋하지 않음): 구현 전 `useZoomPan.ts` 의 `spring(start.y, goal.y, vy, t)` 를 `v0 = 0` 으로 바꾸자 A30 실패(`expected -527.38 to be close to -524.01, received difference is 3.37`) · L3b 「상세 — 투영 목표에 정확히 선다」는 통과. 즉 A30 시험이 L3b 가 놓치던 변이를 잡는다. 변이는 백업본으로 되돌렸다.

GREEN: 구현 커밋 뒤 F-preview·L3·L3b 41건 통과 · 전체 vitest 135 파일 · 1744 통과 · 실패 0(로컬 `npx vitest run`).

## 3. 게이트

`COLAB_TASK_ID=5e58a4455801455d9609d88a1d95c5b3 bash gates/run.sh task`(선언 게이트 4 · 한 번에 · 저장소 루트).

| run_id | 커밋(보고서 기재 전 · 작업 사본에 미커밋 보고서) | 계 | 증거 |
|---|---|---|---|
| `db5db2c6824f49daad57c4673d36622f` | `57195160` | green 4 / red(판정) 0 / red(준비) 0 | `.git/colab-harness/5b8b54126b48254e5de7f1cdee5aac03/5e58a4455801455d9609d88a1d95c5b3/db5db2c6824f49daad57c4673d36622f/gate-summary.json` · `logs/0.log`–`3.log` |

- 게이트별: `frontend-typecheck` 오류 0(include=src·test) · `frontend-test` 135 파일 · 통과 1744 · 실패 0 · `frontend-fixture-reach` 도달 207 · 금지 모듈 0 · `frontend-design-lint` 파일 21 · 전 조건 0 · 다크 누락 0(면제 6) · 문서 표 갈림 0.
- 호스트 뮤텍스 대기 누계 0s. 이 레인은 `frontend-visual`·agent-browser 를 띄우지 않았다.
- 시험 수: 전 1732(기준 `bee7786f` · 1744 − 이 레인 새 시험 12 로 산출 · 기준 단독 실행은 하지 않음) → 후 1744.
- 이 run 뒤 이 보고서에 run_id 를 적어 파일 hash 가 바뀐다. 인계(`handoff --mode complete`) 증거는 보고서 커밋 뒤 같은 명령을 다시 돌린 run 이며 그 run_id 는 레인 최종 메시지의 `COLAB_HANDOFF` 줄에 있다. 제품 파일은 두 run 사이에 같다.

## 4. 규율

- `COLAB_FIX_LANE` 훅은 이 환경에서 걸 수 없어 규율로 지켰다. 커밋별 변경 파일(`git show --stat`):
  - `f346f825`(시험 작성): `frontend/test/design-fix-20260924-F-preview.test.tsx` · `frontend/test/design-fix-20260924-L3b.test.tsx`(주석 2행) · `frontend/src/components/preview/spring.ts`(항등 자리표시) · 이 보고서
  - `b4211f69`(시험 작성): `frontend/test/design-fix-20260924-L3.test.tsx` 만
  - `57195160`(구현): `frontend/src/components/preview/spring.ts` · `frontend/src/components/preview/useZoomPan.ts` 만 — `frontend/test/**` · `gates/**` · `contracts/**` 0
  - 보고서 커밋: `dev-package/sessions/design-fix-20260924-F-preview.md` 만
- 파일 면 밖 제품 파일 변경 0.

## 5. 하지 않은 것

- 실브라우저 검증(agent-browser)·`frontend-visual` — 이 레인은 선언 게이트 4개와 vitest 만 돌았다. 관성 체감(끝에서 스며들 듯 서는가 · 두 손가락 · 탭으로 잡기)은 통합 단계 실화면 몫이다.
- `isPrimary === false` 판정(A27 원문의 대안) — jsdom `PointerEvent` 의 `isPrimary` 기본값이 `false` 라 기존 시험 전부의 누름이 무시된다. id 비교만 넣었다. 첫 포인터의 pointerup/cancel 이 끝내 오지 않으면 다른 id 의 누름이 계속 무시되는 위험이 남는다(마우스는 id 가 같아 해당 없음).
- 인계 속도 상한으로 목표가 잘린 경우 놓는 순간 속도가 줄어든다(예: 2000 → 785px/s). spec 값 대로이며 체감 확인은 실화면 몫.
- A30 시험 제목 「16ms 마다 1px 씩」은 실제 이동(11 · 1 · 1px)과 다르다 — 단언은 실제 값으로 계산한다. 구현 커밋 뒤 시험 파일을 고치지 않으려고 두었다.
- 관성 갱신 함수가 렌더까지 미뤄지면 `settled` 를 한 프레임 늦게 읽어 빈 프레임 하나가 더 돈다. 그 16ms 안의 탭은 「관성을 잡는 탭」으로 처리된다.

## 수정 라운드(리뷰 확정 FP-1)

- 기준: 레인 브랜치 `worktree-wf_808554ed-fad-3` 머리 `45ca2112`(조상에 `bee7786f` 확인) · lifecycle task `416ca440fb60432e9b48512187b2827a` · 선언 게이트 4(같음)
- 결함 FP-1(minor · `frontend/src/components/preview/useZoomPan.ts:485`): 관성 `setView` 갱신 함수가 클로저 플래그 `settled` 를 쓰고 `if (settled) return cur;` 로 빠진다. React 19.2.8 DEV StrictMode 는 렌더 때 몰아서 처리하는 갱신에서 갱신 함수를 두 번 부르고 첫 결과를 버린다(`react-dom-client.development.js:8044-8048`). 멈춤 프레임의 첫 호출이 `settled = true` 로 목표를 돌려주고 버려지며, 둘째 호출은 앞 프레임 값을 돌려준다. 앱은 `<StrictMode>` 아래(`frontend/src/main.tsx:17`)라 dev 에서 목표보다 ≥ 0.5px 모자란 자리에 선다.

### 항목 → 전후 → 시험

| 항목 | 전 | 후 | 시험 |
|---|---|---|---|
| FP-1 | 갱신 함수 첫 줄 `if (settled) return cur;` — 멈춤 뒤 호출은 앞 프레임 값 | (구현 커밋에서 기재) | `design-fix-20260924-F-preview.test.tsx` 「FP-1 … reactStrictMode=true · 빠른 끌기 뒤 panOffset 이 잘린 투영 목표와 같다」(＋ 같은 본문 `reactStrictMode=false` 대조) — renderHook `reactStrictMode` · 한 act 안 `advance(3000)` 으로 갱신을 렌더 때 몰아 처리 |

### RED 증거

시험 작성 커밋 시점(제품 코드 = `45ca2112`) `npx vitest run test/design-fix-20260924-F-preview.test.tsx` → **1 실패 · 13 통과**. 실패는 단언 실패(import 오류 0).

- `reactStrictMode=true`: `AssertionError: expected { x: +0, y: 543.4196964154335 } to deeply equal { x: +0, y: 544 }` — 목표(경계 544)보다 0.58px 모자람(SETTLE_PX 0.5 이상).
- `reactStrictMode=false`: 통과(같은 본문 · 이중 호출 없음 → 결함 경로 밖. 회귀 고정용).
