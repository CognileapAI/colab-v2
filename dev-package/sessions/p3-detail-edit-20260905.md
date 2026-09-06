# WU-A3 — 상세 수정 UI · 현행 필드만 (PRD-22) · 레인 `p3-detail-edit` · 2026-09-05

원천 = `R-A-3-frontend.md §2 WU-A3`. **프론트만 바뀐다**(`contracts/`·서버·DB 변경 0). 여는 칸 = `DatasetUpdate` 가 이미 받는 다섯 — 이름 · 설명 · 원천 표기 · 좌표계 · 기간. `topic` 은 **읽기 전용**(표시만).

## 1. 바뀐 것 — `path:line`

| 파일 | 무엇 |
|---|---|
| `frontend/src/components/detail/editFields.ts:41` `TEXT_FIELDS` | **필드 표**(이름·설명·원천 표기·좌표계) ＋ 기간(`:49` `PERIOD_LABEL`) |
| 〃 `:104` `toPatch` ／ `:124` `applyDraft` ／ `:86` `periodOf` | 바뀐 칸만 담기(빈 칸은 생략이 아니라 `null` — 계약 축자) ／ 낙관값 조립(헤더 ＋ `basicInfo`) ／ 날짜 칸 2개 → `DataPeriod` 하나(끝이 비면 무기한) |
| `frontend/src/components/detail/updateSource.ts:19` `apiDatasetUpdateSource` | 계약 op `updateDataset`(PATCH `/datasets/{datasetId}`) — 생성물 클라이언트로만 나간다. 오류 문구는 서버 봉투 `message` 를 그대로 올린다 |
| `frontend/src/components/detail/useDatasetEdit.ts:26` | 낙관 → 왕복 → 실패 시 되돌리기. `base` 가 새로 읽히면 쥔 값을 버린다(`:34`) |
| `frontend/src/components/detail/DatasetEditEntry.tsx:12` | `PermissionGate requires="업로드·편집"` — 꺼지면 **DOM 에서 사라진다**(P-12) |
| `frontend/src/components/detail/DatasetEditForm.tsx:57` | 표를 훑어 그린다. `:39` 이름 빈칸은 **보내기 전에** 막고 서버와 같은 문구(`ERR-001`) |
| `frontend/src/components/detail/DetailHeader.tsx:39`·`:96` | `editAction` 슬롯 신설 — 승인 자리(`dh-act`)와 **다른 판정**이라 다른 슬롯 |
| `frontend/src/routes/DatasetDetailPage.tsx:80-88`·`:158-172` | 골격 배선. 화면이 그리는 값은 `shown`(낙관값 → 서버 응답) |
| `frontend/src/components/detail/detail.css:+35행` | `.dh-edit`·`.dt-edit` — 토큰만 쓴다. 폼은 헤더 아래 제 자리(탭 전환 없음) |
| `dev-package/sessions/P8-E01-APPLY-POINTS-DRAFT.md §1.1` | `PermissionGate` 실물 9곳 → **10곳**(신설 행). 이 표는 `test/e01-apply-points.test.ts` 가 실물과 대조한다 |

## 2. A4·A6·R-B 가 얹을 자리 — **골격 3점**

칸이 늘어도 **화면 코드는 안 고친다.** 늘리는 자리는 셋뿐이다(`editFields.ts` 머리말 축자).

1. `editFields.ts` 의 `TEXT_FIELDS` 에 **한 줄**(`{ key, label, multiline?, required? }`)
2. `DatasetEditDraft` 에 **열쇠 하나** ＋ `toDraft` 에 한 줄
3. 값이 `basicInfo` 쪽이면 `applyDraft` 의 그 갈래에 한 줄

- 복합 칸(기간처럼 두 입력이 한 값)은 `periodOf`/`samePeriod` 쌍을 본뜬다. 진입점은 `DetailHeader` 의 `editAction` 슬롯 하나다.
- ⛔ **`topic` 편집 칸을 만들지 않는다** — R-B PRD-01 이 `category` 로 갈아친다. 폼에 없음이 시험으로 고정돼 있다.

## 3. 시험 — RED 선실측 → GREEN

- 신규 `frontend/test/detail-edit.test.tsx` — **18건**(전부 통과). 모든 단언이 대상 건수를 먼저 잰다(빈 집합 통과 방지).
- **RED 선실측** = 구현 전 실행에서 `editFields`·`updateSource` 미해결로 수집 0건 실패(`Failed to resolve import … detail/editFields`).
- 덮은 것 — 권한 0건/1건 · 이름만 고친 저장의 열쇠 `['name']` · 무변경은 빈 몸통 · 입력 칸 정확히 6개(주제·R-B 필드 0건) · NULL 5칸이 빈 문자열 · 낙관 갱신 → 서버 응답으로 갈아탐 · 실패 되돌리기 ＋ 서버 문구 · 빈 이름 미발신 · 취소 · `PATCH /api/v1/datasets/{id}` 축자 · 400 봉투 `message`.
- WU-A12 방어선 `test/rev1-keep-regression.test.tsx` **12건 그대로 green**(완화·삭제 0).

## 4. 게이트 — 단독만, `all` 없음

```
./gates/run.sh frontend-typecheck     → green (tsc --noEmit · 오류 0건)
./gates/run.sh frontend-test          → green (vitest jsdom · 41 파일 · 637건 통과 · 실패 0건 / 종전 619건)
./gates/run.sh frontend-fixture-reach → green (진입점 도달 133개 · 금지 모듈 0건)
```
- 판정 red **0건** · 준비 red **0건**. 실행 전 `~/.colab-v2-test.env` 로드, 세 게이트 모두 DB 를 쓰지 않는다.
- 중간 1회 red 가 있었다 — `e01-apply-points` 가 신설 `PermissionGate` 자리를 표에서 못 찾았다. **표를 고쳐 해소**(검사 완화 아님).
- 워크트리 준비 — `frontend/node_modules` 를 본 트리로 심링크(gitignored · `git status` 무영향).

## 5. PLAN-SoT §9 초안 — **병합 직전에** `origin/main` 최대 ＋1 로 〈N〉 을 재실측해 넣는다

착수 시점 참고값 = 〈326〉(2026-09-05). 이 세션은 `PLAN-SoT.md` 를 고치지 않았다.

```
| 〈N〉 | **R-A-3 FE 계층 — 상세 수정 진입점 신설 · 구역 메뉴 sticky(미결-9 ⓑ 최종형) · 종료 조건 개정** | **집행 (2026-09-05 · 워크트리 `p3-detail-edit` · 병합 `<sha>` · 계약 개정 0 · 마이그레이션 0 · staging 접촉 0).** ①회차 = **해당 없음**(계약 미개방) ②값 = 없음 ③근거 = PRD-14·20·22·23·24 (`dev-package/prd/PRD-260905-적용전기획.md`) ④가·파 판정 = **해당 없음** · `contract-breaking` 출력 = `<축자 · 변경 0 확인>` ⑤소비자 = 해당 없음 ⑥마이그레이션 = **0건** ⑦승인 = 불요(㉮ 밖 · 계약 미접촉) ⑧이번에 세지 않은 축 = 대표 그림 저장 경로(WU-C2 별건) `[미측정]` |
```

## 6. 넘기는 것

- `representativeFileId`·`variables` 는 `DatasetUpdate` 에 있으나 **이 폼이 열지 않았다** — 앞은 WU-C2(대표 그림 저장 경로), 뒤는 자동 추출 칸이라 사람이 타이핑하지 않는다(`DatasetBasicInfo.variables` 축자).
- 저장 뒤 색인 갱신(수용 기준 ③)은 서버 몫이라 이 WU 가 시험을 걸지 않았다 `[미측정]`. 잠긴 데이터에서도 진입점 조건은 스위치 하나다(P-7).
