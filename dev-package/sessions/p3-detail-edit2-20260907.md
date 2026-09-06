# 레인 `p3-detail-edit2` — WU-A3R ＋ WU-A4R (R-A′ · 2026-09-07)

- 통합 브랜치 = `integration/r-a2` · 레인 브랜치 = `lane/p3-detail-edit2` · 기점 HEAD = `e01206c`.
- 정본 = `dev-package/prd/rounds/R-A2.md §2-⑤` · `dev-package/prd/specs/R-A2.md:47` ·
  `dev-package/prd/PRD-260905-적용전기획.md` `#### PRD-22`·`#### PRD-28`.
- 계약 0 · 서버 0 · DB 0 · 마이그레이션 0.

## 1. 완료 조건 ↔ 판정 ↔ 근거

### WU-A3R — 편집 중 다운로드 숨김 ＋ 저장 뒤 재동기

완료 조건(라운드 파일 §2-⑤ 축자) — 「⑴ **편집 중에는 다운로드가 숨고 `취소`/`저장` 이 그 자리에
온다.** ⑵ **저장 뒤 헤더 칩과 공개 범위 설명이 같은 값으로 다시 그려진다.**」

| 조건 | 판정 | 근거 (`파일:행`) |
|---|---|---|
| ⑴ 편집 중 다운로드 숨김 — 기본 정보 아래 행 | 충족 | `frontend/src/routes/DatasetDetailPage.tsx:229-247` — `edit.editing` 이면 `dt-download` 를 그리지 않는다 |
| ⑴ 편집 중 다운로드 숨김 — 활용 구역 | 충족 | `frontend/src/components/detail/UsageSection.tsx:39-48,81` — `downloadHidden` 이 참이면 `detail-download` 구역째 없다. 전달은 `DatasetDetailPage.tsx:308` |
| ⑴ `취소`/`저장` 이 그 자리 | 충족 | `frontend/src/components/detail/DatasetEditForm.tsx:150-181` `DatasetEditActions` ＋ `DatasetDetailPage.tsx:104-107,229-233` — 다운로드가 서 있던 `dt-gridact` 행에 선다 |
| ⑴ 진입점 중복 0 | 충족 | 폼에서 행동 줄을 걷었다 — `DatasetEditForm.tsx` 의 `de-act` 블록이 `DatasetEditActions` 하나로 이동. 시험이 `getAllByTestId('detail-edit-save')` 를 1건으로 잰다 |
| ⑵ 헤더 칩 재동기 | 충족 | `DatasetDetailPage.tsx:186` `detail={shown}` — `shown` = `useDatasetEdit` 이 저장 응답으로 갈아 끼운 상세(`useDatasetEdit.ts:107-110`). 칩은 `DetailHeader.tsx:89-99` |
| ⑵ 공개 범위 설명 재동기 | 충족(결함 1건 수정) | `DatasetDetailPage.tsx:238,282,308` — 종전 `detail.detail.actions`(처음 읽은 값)를 `shown.actions` 로 바꿨다. 그 전에는 저장 응답이 `canDownload` 를 바꿔도 다운로드 관문·`access-origin` 이 옛 판정으로 남아 **새로고침해야** 맞았다 |
| ⑵ 새로고침 불요 | 충족 | 시험이 상세 조회 횟수를 센다 — 저장 뒤 `get` 호출 1회(`test/prd22-detail-edit2-20260907.test.tsx:172-201`) |
| `topic` 읽기 전용 | 충족 | `editFields.ts:12-13,65-70` — `TEXT_FIELDS` 에 `topic` 없음. 시험 `prd22-detail-edit2-20260907.test.tsx:216-220` |

구조 변경 1건 — 편집 값·저장 중·문구를 `useDatasetEdit` 으로 올렸다(`useDatasetEdit.ts:14-40`).
사유 = `취소`/`저장` 이 폼 **밖**에 서므로 두 자리가 같은 값을 봐야 한다. 폼(`DatasetEditForm.tsx:24-31`)은
값을 그리기만 한다. 필드 표 `editFields.ts` 는 무수정 — 뒤 WU 가 줄만 더하는 골격이 그대로다.

### WU-A4R — 등록 화면 `좌표계 (선택)`

완료 조건(라운드 파일 §2-⑤ 축자) — 「등록 화면 좌표계 칸 보조 라벨을 `좌표계 (선택)` 로 한다
(III-B ⓐ · 코드가 이미 `변수 (선택)`·`기간 시작 (선택)` 패턴을 쓴다).」

| 조건 | 판정 | 근거 (`파일:행`) |
|---|---|---|
| 라벨 = `좌표계 (선택)` | 이미 충족 | `frontend/src/components/upload/RegisterArea.tsx:355` — 커밋 `a32e580`(WU-A4 · PRD-28 짧은 값 3칸)이 세웠다. 이 레인의 코드 변경 0 |
| 같은 `(선택)` 패턴 | 충족 | `RegisterArea.tsx:278` `변수 (선택)` · `:293` `{periodLabel} (선택)` — 짧은 값 한 줄(`reg-short-row`)에서 **사람이 적는 칸** 2개의 라벨이 `(선택)` 으로 끝난다. 셋째 칸 `격자` 는 자동 판독 읽기 전용(`AutoField` · `자동` 표기)이라 선택 항목이 아니다 |
| 회귀 시험 | 신설 | `frontend/test/upload.test.tsx:869-894` 2건 |

⚠ **RED 선실측 불가** — 라벨은 이 레인 기점(`e01206c`)에 **이미 서 있었다**(`git log -L` 실측:
`a32e580`). 없던 것을 있는 것처럼 적지 않는다. 이 레인의 몫은 **판정을 시험으로 고정**한 것이고,
목업 HTML 이 맨 `좌표계` 를 그리더라도 Ted 판정 III-B 가 이긴다는 사실이 시험에 남았다.
「판정 없이 고치지 않는다」에 따라 상세 편집 폼의 `좌표계` 라벨(`editFields.ts:69`)은 손대지 않았다 —
그 칸은 등록 화면이 아니고 III-B 의 대상이 아니다.

## 2. RED → GREEN

RED 선실측 (구현 전 · `npx vitest run test/prd22-detail-edit2-20260907.test.tsx`) — `Tests 3 failed | 4 passed (7)`

```
FAIL  test/prd22-detail-edit2-20260907.test.tsx > WU-A3R ⑴ — 편집 중 다운로드 숨김 · 그 자리에 `취소`/`저장` > `수정` 을 누르면 다운로드가 **DOM 에서 사라진다** (두 자리 모두)
AssertionError: expected <button type="button" …(2)></button> to be null
FAIL  test/prd22-detail-edit2-20260907.test.tsx > WU-A3R ⑴ — 편집 중 다운로드 숨김 · 그 자리에 `취소`/`저장` > 다운로드가 있던 행에 `취소`/`저장` 이 선다
TestingLibraryElementError: Unable to find an element by: [data-testid="detail-edit-save"]
FAIL  test/prd22-detail-edit2-20260907.test.tsx > WU-A3R ⑵ — 저장 뒤 헤더 칩과 공개 범위 설명이 서버 값으로 다시 그려진다 > 서버가 돌려준 칩 값과 접근 판정이 **다시 읽지 않고** 화면에 선다
AssertionError: expected <button type="button" …(2)></button> to be null
```

GREEN — `test/prd22-detail-edit2-20260907.test.tsx` 7건 ＋ 회귀 `test/detail-edit.test.tsx` 18건 = 25건 통과.
WU-A4R 2건은 `test/upload.test.tsx` 에 붙였다(같은 화면의 다른 시험과 한자리).

⚠ **시험 1건이 첫 전수에서 판정 red 를 냈고, 고친 것은 시험이다** —
`짧은 값 한 줄의 라벨이 전부 (선택) 으로 끝난다` 가 `AssertionError: expected '격자자동' to match /\(선택\)$/`.
`격자` 는 **자동 판독 읽기 전용 칸**(`RegisterArea.tsx:67-83` `AutoField`)이라 선택 항목이 아니다 —
PRD-28 수용 기준 축자가 말하는 것은 「**선택 항목인데** 보조 라벨이 없는 칸」이다. 오라클을 그 축자에
맞춰 좁혔고(사람이 적는 칸 = `label[for]` 2건 · 자동 칸 1건은 `자동` 표기로 따로 잰다), 코드는 안 고쳤다.
그 red 는 **레인이 만든 시험의 결함**이고 화면 결함이 아니다.

## 3. 게이트 (배출처 `dev-package/reports/R-A2/p3-detail-edit2`)

```
frontend-typecheck green — tsc --noEmit(frontend/tsconfig.json · include=src·test) 오류 0건.
  ── 계 : green 1 / red(판정) 0 / red(준비) 0

frontend-test green — vitest run(frontend/vite.config.ts · jsdom) 통과 868건 · 실패 0건.
  ── 계 : green 1 / red(판정) 0 / red(준비) 0

frontend-fixture-reach green — 진입점 src/main.tsx 에서 도달 151개(진입점 제외 150개), 금지 모듈(fixture.ts·graphFixture.ts·localEngine.ts) 0건.
  ── 계 : green 1 / red(판정) 0 / red(준비) 0

work-item-consistency: green — 대장과 산문의 불일치 0
  ── 계 : green 1 / red(판정) 0 / red(준비) 0
```

## 4. 자기 표시

- 새로 그린 칸 0개 — 이 레인은 **자리·판정 출처**만 바꿨다.
- 편집 값 상태를 폼에서 훅으로 올린 것은 **요청된 범위 안**이다(`취소`/`저장` 이 폼 밖에 서는 조건).
- `shown.actions` 로 바꾼 3자리는 요청 문면의 「재동기」에 해당한다 — 초과분 아님.
- 초과분(요청되지 않은 추가 변경) = 없음.
- 미달 = 없음. 단 WU-A4R 은 **RED 없이 GREEN**(라벨이 기점에 이미 존재) — 위 §1 에 실측 근거 기재.

## 5. 하지 않은 것

- **R-B(`WU-B3`)가 더하는 필드를 그리지 않았다** — 분류 · 유형 · 가공 단계 · 변수 표 ·
  **공개 범위 값** · 관측 간격(신규 칸) · 기간 최소 단위(신규 칸) · Lv0 2칸.
  공개 범위는 **값 칸 없이 출처 문장 한 줄**(`UsageSection.tsx:36-37`)만 종전대로 남았다.
- `topic` 편집 진입 미신설(읽기 전용 유지).
- 존치 6종 무수정 — 기준 격자 파일 흐름 · AI 계보 제안 · 2단 등록 게이트 · 이어올리기 배너 ·
  **승인·검증 층**(`detail/DetailHeader.tsx:72,81-85` 인용 자리 · `detail/LockedNotice.tsx`) · 값 조회.
  편집 행동 줄은 그 옆에 세웠고 무엇도 걷지 않았다.
- 계약(`contracts/`) · 서버 · DB · 마이그레이션 접촉 0. `03-HANDOFF.md`·`PLAN-SoT.md` 미수정.
- A6 기간 달력 팝오버 · PRD-39 ⑤ 확장보기 오버레이 미착수(WU-B3 몫).
