# F-1 집행 기록 — 미등록 파일 미리보기 화면(S-08) 도달 경로

／ 2026-08-28 · 워크트리 `worktree-agent-abdcbad3955889aa2` · 파일 면 `frontend/**` 단독
／ 완료 정의 = Ted 2026-08-28 확정 3항 (① 도달 경로 ② 표현 변경 없음 ③ 화면 시험 + 관련 게이트 green · staging 배포는 조건 아님)

## 1. 착수 전 실측 (조사 문서 `F1-SCOPE.md` 대조)

| 조사 문서 진술 | 실측 |
|---|---|
| `UnregisteredPreviewPage.tsx` 142 행 | 일치 |
| `routes.tsx` 에 import·Route 통째로 없음 | 일치 (13~14 행 주석만) |
| 모달 「보기만 할게요」가 `requestClose` 만 부름 | 일치 (`UploadModal.tsx` reg-viewonly) |
| `previewNavigation()` 호출처 0건 | 일치 |
| 화면 시험 `test/preview.test.tsx` 390 행 | 일치 |
| 팔레트 주석이 낡음(계약·구현 둘 다 존재) | 일치 — `contracts/seams/fe-core.yaml:1589 listPalettes` · `services/core-api/src/colab_core/app/routes/preview.py:47 GET /preview-palettes` |

**시험 기준선** (구현 전, `npm ci` 직후 `npm test -- --run`) — **13 파일 / 274 통과 / 0 실패.**

## 2. 한 일

1. `frontend/src/app/routes.tsx` — `UnregisteredPreviewPage` import + `<Route path={PREVIEW_ROUTE_PATH}>`. 주소 문자열을 새로 적지 않고 `components/preview/handoff.ts` 의 상수를 쓴다.
2. `frontend/src/components/upload/UploadModal.tsx` — 「보기만 할게요」가 `viewOnly()` 를 부른다: 모달을 닫고 `previewNavigation()` 이 만든 주소·짐으로 이동. `createDataset` 은 부르지 않는다. `uploadId` 가 없으면 주소를 지어내지 않고 닫기만 한다.
3. `frontend/src/components/upload/PreviewPanel.tsx` — 선택 prop `onRender` 추가. 모달이 `renderId`·`withoutReferenceGrid` 를 알아야 S-08 이 **다시 그리지 않고 이어서 본다**(정본 §8.1 미리보기 행).
4. `frontend/src/components/preview/PreviewControls.tsx` — **낡은 주석만** 정정. 「계약에 `listPalettes` 가 없다」→ 「계약·구현 둘 다 있고, 이 자리가 빈 이유는 이 화면의 범위가 「보기만」이기 때문」. **팔레트 컨트롤은 만들지 않았다.**
5. 시험 2건 신설 — `test/preview.test.tsx`(라우팅 표가 S-08 을 세운다) · `test/upload.test.tsx`(「보기만 할게요」가 S-08 로 보내고 짐을 싣는다).

## 3. 시험이 실제로 무언가를 검사한다는 증거 (되돌림 → red → 복원)

- 라우트 한 줄 제거 → `preview.test.tsx` **1 실패 / 23 통과** — `완료 정의 ① — 앱 라우팅 표가 S-08 을 세운다 > … AssertionError: expected null not to be null`. 복원 후 24 통과.
- `onClick={viewOnly}` → `onClick={requestClose}` 로 되돌림 → `upload.test.tsx` **2 실패 / 73 통과** — `expected '/datasets' to be '/datasets/preview/01JYZ9K7WQ3N8V4M2X6…'` · `expected '' to be '?render=01JYZ9K7WQ3N8V4M2X6C5B0RE1'`. 복원 후 75 통과.

## 4. 마무리 측정 (2026-08-28)

| 측정 | 값 |
|---|---|
| `npm test -- --run` | **13 파일 / 277 통과 / 0 실패** (기준선 274 → +3) |
| `npm run build` (`tsc --noEmit` 포함) | green — `✓ built in 1.14s` |
| `./gates/run.sh generated-up-to-date` | **green** — 「등기부 4건 전부 재생성 일치, 등기부 밖 자칭 생성물 0건」 |
| `./gates/run.sh stage2-markers` | **red (도구 부재로 계수)** — 「pipeline-worker 파이썬이 없다: `services/pipeline-worker/.venv/bin/python`」. **이 변경 전에도 같은 red** (frontend 변경을 치워 두고 재실행해 확인) |
| `./gates/run.sh work-item-consistency` | **red** — ㈓ conflict 12건(산문 문서끼리 갈림). **이 변경 전에도 같은 red**, 원인은 `dev-package` 산문이고 이 레인은 그 파일들을 소유하지 않는다 |

## 5. 범위 밖으로 남긴 것

확대 · 타일 · 지도 값 조회 · 스크린샷 · 팔레트 컨트롤 · 「연구실에 등록으로 되돌아가기」(S-08 은 열쇠만 건네고, 모달을 등록 단계로 펼치는 쪽은 모달 레인) — 전부 손대지 않았다.
`contracts/seams/` · `work-items.yaml` · `03-HANDOFF.md` · `PLAN-SoT.md` · `WORK-UNITS*` 무접촉.

## 6. `[미확인]` — 무엇을 하면 풀리는가

| `[미확인]` | 푸는 방법 |
|---|---|
| 화면 시험이 정본 §8.1 의 **몇 행을 덮는지** | 시험을 §8.1 행 목록과 1:1 대조해 계수 (이번 회차에 세지 않았다) |
| 화면의 **만료 표시가 서버 실제 만료와 맞는지** | 정리기 동작 후 같은 주소 재조회 1회 실측 |
| 팔레트 목록 중계가 **화면에서 실제로 200 을 내는지** | 배포된 API 로 `GET /preview-palettes` 1회 호출 (이 화면은 부르지 않으므로 완료 정의와 무관) |
| 실제 브라우저에서 모달→S-08 이 뜨는지 | staging 배포 후 1회 조작. **완료 정의에서 조건이 아니다** |
| 기존 `구간 수` 컨트롤을 **없애야 하는지** | Ted 판정. 완료 정의 ②「표현 변경 없음」을 「추가 금지」로 읽어 **기존 구간 수 컨트롤은 그대로 뒀다** — 없애면 정본 §8.1 대비 화면 시험 3건(`컨트롤은 팔레트와 구간 수 둘뿐이다`)이 red 가 된다 |
