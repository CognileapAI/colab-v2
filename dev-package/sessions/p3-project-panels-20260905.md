# WU-A7 · 프로젝트·논문 패널 분리 (PRD-23) — 레인 `p3-project-panels`

- 라운드 `dev-package/prd/rounds/R-A-3-frontend.md` §2 WU-A7 · 기점 `origin/integration/r-a` = `947bf1f`
- 범위 = **프론트만**. `contracts/` · 서버 · DB 접촉 **0**. 마이그레이션 **0**. staging 접촉 **0**

## 1. 무엇이 바뀌었나 (경로:행)

| 자리 | 무엇 |
|---|---|
| `frontend/src/components/upload/types.ts:22-31` | `PickedProject`(projectId·name·**type**) 신설 · `PROJECT_PANEL_TYPES = ['국가과제','논문']` |
| `frontend/src/components/upload/types.ts:99` | `ProjectSource.create` 반환이 `PickedProject` — 만든 프로젝트도 유형을 들고 온다 |
| `frontend/src/components/upload/RegisterArea.tsx:221-226` | 유형별 빈 상태 축자 `PANEL_EMPTY` |
| `frontend/src/components/upload/RegisterArea.tsx:237` | `StepTwo` 를 **export** — 패널 수용 기준을 컴포넌트 단위로 잰다 |
| `frontend/src/components/upload/RegisterArea.tsx:288-327` | 칩 나열(종전 263-269) → **두 패널**. `reg-proj-panels` · `reg-proj-panel-{유형}` · `reg-proj-rows-{유형}` · 행마다 이름(`reg-proj-row-name`) ＋ `해제` |
| `frontend/src/components/upload/RegisterArea.tsx:370` | 링크 문면 `+ 여기서 새 프로젝트 만들기` → **`+ 새 프로젝트 만들기`** · 자리는 종전대로 두 패널 아래 **한 곳** |
| `frontend/src/components/upload/RegisterArea.tsx:479-480` | 겉 props `projects`/`onProjects` 가 `PickedProject[]` |
| `frontend/src/components/upload/UploadModal.tsx:86` | `projects` 상태가 `PickedProject[]`. `createDataset` 이 싣는 값은 종전대로 `projectIds` 뿐 |
| `frontend/src/components/upload/projectSource.ts:17-18` | 빠른 생성 응답에 `type` 을 실어 준다(응답에 없으면 보낸 값) |
| `frontend/src/components/upload/upload.css:184-196` | `.projpanels`(2열 · 720px 이하 1열) · `.projpanel` · `.projrows` · `.projrow` |

- **칩 자국을 남기지 않았다** — `reg-proj-chips` · 전역 빈 상태 `reg-proj-empty` 는 사라졌고 유형별 `reg-proj-empty-{유형}` 이 대신한다.
- 종전 `+ 추가` · 중복 경고 · 연구실 0건 안내 · `프로젝트 생성` 권한 게이트는 **그대로 둔다**.

## 2. 시험 — RED 선실측 → GREEN

- 새 파일 `frontend/test/project-panels-20260905.test.tsx` — **8건**
  1. 국가과제 1 · 논문 2 → 두 패널이 1행 / 2행 · 칩 묶음 부재
  2. 행마다 이름 ＋ `해제`, 해제하면 그 패널에서 빠진다
  3. 새로 담으면 해당 유형 패널에 **아래로** 붙고 같은 카드 안에 그대로 있다(화면 이동 0)
  4. 논문 0건이어도 논문 패널 ＋ 빈 상태 축자
  5. 둘 다 0건이어도 두 패널이 빈 상태로 선다
  6. `+ 새 프로젝트 만들기` **한 개** · 패널 안이 아니고 DOM 상 두 패널 **뒤**
  7. 링크를 누르면 유형 셀렉트(국가과제·논문)가 먼저 뜬다
  8. 빠르게 만든 논문이 논문 패널 행으로 붙는다
- **RED 실측** `npx vitest run test/project-panels-20260905.test.tsx` → `Test Files 1 failed (1) · Tests 8 failed (8)` (구현 전)
- **GREEN** 같은 명령 → `Test Files 1 passed (1) · Tests 8 passed (8)`
- 기존 `frontend/test/upload.test.tsx` §8② 첫 시험은 칩 오라클이라 **패널 오라클로 고쳐 썼다**(같은 행위·새 표시 방식). 나머지 4건(중복·인라인 빠른 생성·권한 꺼짐·연구실 0건)은 무수정 green.
- 회귀 방어선 `frontend/test/rev1-keep-regression.test.tsx`(WU-A12) **무수정 green**.

## 3. 게이트

| 게이트 | 판정 | 실측 |
|---|---|---|
| `frontend-typecheck` | **green** | `tsc --noEmit` 오류 **0건** |
| `frontend-test` | **green** | 43 파일 · 통과 **649건** · 실패 **0건** |

- `frontend-fixture-reach` 는 §5 가 WU-A7 에 걸지 않았다 — 돌리지 않았다.
- `all` 은 돌리지 않았다(§3-㉲ — 작업 중엔 단독 게이트).
- `detail-edit.test.tsx`(WU-A3) 부하 흔들림은 이번 회차에 **나타나지 않았다**.

## 4. PLAN-SoT §9 초안 — **병합 직전**에 `origin/main` 최대 ＋ 1 로 번호를 다시 잰다

```
| 〈N〉 | **R-A-3 FE 계층 — 상세 수정 진입점 신설 · 구역 메뉴 sticky(미결-9 ⓑ 최종형) · 종료 조건 개정** | **집행 (2026-09-05 · 워크트리 `p3-project-panels` · 병합 `<sha>` · 계약 개정 0 · 마이그레이션 0 · staging 접촉 0).** ①회차 = **해당 없음**(계약 미개방) ②값 = 없음 ③근거 = PRD-14·20·22·23·24 (`dev-package/prd/PRD-260905-적용전기획.md`) ④가·파 판정 = **해당 없음** · `contract-breaking` 출력 = `<축자 · 변경 0 확인>` ⑤소비자 = 해당 없음 ⑥마이그레이션 = **0건** ⑦승인 = 불요(㉮ 밖 · 계약 미접촉) ⑧이번에 세지 않은 축 = 대표 그림 저장 경로(WU-C2 별건) `[미측정]` |
```

## 5. 남긴 것 · `[미상]`

- 유형은 화면이 담을 때 붙인다. `createDataset` 요청은 종전대로 `projectIds` 만 싣는다 — 서버 계약을 열 이유가 없다.
- `POST /projects` 응답의 `type` 유무는 계약을 읽지 않고 방어했다(있으면 그것, 없으면 보낸 값). 계약 확인은 이 WU 범위 밖이다 — `[미상]`.
