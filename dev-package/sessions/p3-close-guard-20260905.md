# WU-A9 · 종료 확인 조건 (PRD-14 · 미결-15 ⓐ) — 레인 `p3-close-guard`

- 기점 = `origin/integration/r-a` `78a9a67` (WU-A12 회귀 방어선 병합 뒤). 계약 0 · 마이그레이션 0 · 서버 0 · staging 접촉 0.
- 바뀐 것은 **조건 하나**다. **문면은 손대지 않았다** — `확인한 계보와 입력한 내용이 사라져요. 데이터셋은 만들어지지 않아요.` 문자열이 종전과 같고, 시험이 축자로 단언한다.

## 1. 변경 (경로:줄)

| 경로:줄 | 무엇 |
|---|---|
| `frontend/src/components/upload/UploadModal.tsx:79` | `nameDraft` 상태 신설 — 파일명에서 만든 **자동 초안**을 따로 들고 있는다 |
| `frontend/src/components/upload/UploadModal.tsx:120-122` | 접수 응답에서 초안을 `nameDraft` 에도 넣는다(`name` 초기값과 같은 값) |
| `frontend/src/components/upload/UploadModal.tsx:172-192` | `hasHumanInput` 판정식 신설 — ①②③ 사람 입력 필드 ＋ 확정 계보 부모 건수 |
| `frontend/src/components/upload/UploadModal.tsx:270-275` | `requestClose()` 가 `registerOpen` 대신 `hasHumanInput` 을 본다 |
| `frontend/test/close-guard-20260905.test.tsx` (신규 253행) | 수용 기준 8건 |
| `frontend/test/upload.test.tsx:368-378` | 종전 조건을 단언하던 1건을 새 조건으로 고쳤다 (아래 §4) |

## 2. 사람 입력으로 세는 필드 — 판정 대상

- ① 이름(**자동 초안과 다를 때만**) · 주제 · 변수 · 기간 시작 · 기간 끝 · 좌표계 · 설명
- ② 담은 프로젝트·논문 건수 (`projects.length`)
- ③ 원천 표기 · **확정된** 계보 부모 건수 (`lineageParents.length` — `LineageStep` 이 `confirmed` 만 올린다)

**세지 않는 것(자동으로 채워진 값)**

- 파일명에서 만든 이름 초안 · 확장자 · 용량 · 읽기 전용 가공 단계 칸(`reg-lv` = 「계보를 확정하면 정해져요」)
- R-B 가 더할 기본 선택값 `Lv2` · `연구실 구성원 전체` 도 같은 이유로 판정식 밖이다(지금 화면에는 아직 없다)
- 파일을 놓은 사실 자체도 입력이 아니다 — 수용 기준 1행이 그것이다

## 3. RED 선실측 → GREEN

- RED: `npx vitest run test/close-guard-20260905.test.tsx` → **실패 3 · 통과 5 (8건)**. 실패한 3건이 「안 묻고 닫힌다」 쪽 — 종전 코드는 등록 단계만 열려 있으면 무조건 물었다.
- GREEN(구현 뒤): 같은 명령 → **통과 8 · 실패 0**.
- 회귀 방어선 3종 동시 실행 → **통과 109 · 실패 0** (`upload.test.tsx` · `rev1-keep-regression.test.tsx`(WU-A12) · `project-panels-20260905.test.tsx`(WU-A7)).

## 4. 종전 시험 1건을 고친 근거 — 숨기지 않는다

`upload.test.tsx` 「등록 단계가 열려 있으면 확인을 받는다」는 **개정 대상인 종전 조건 자체**를 단언하고 있었다(파일만 올리고 등록 단계를 연 뒤 닫으면 확인 모달). PRD-14 가 그 조건을 뒤집었으므로 그대로 두면 요구사항과 시험이 서로 반대다. **문면 단언은 그대로 두고**, 설명에 한 글자를 적는 줄 하나를 앞에 넣어 「사람이 적은 값이 있으면 묻는다」로 이름과 절차를 바꿨다. 「빈 상태면 안 묻는다」 쪽은 신규 파일이 새로 잡는다. 다른 시험은 한 줄도 고치지 않았다.

## 5. 게이트

| 게이트 | 판정 | 출력 |
|---|---|---|
| `frontend-typecheck` | **green** | `tsc --noEmit`(include=src·test) 오류 **0건** |
| `frontend-test` | **green** | `vitest run`(jsdom) 통과 **657건** · 실패 **0건** · 파일 **44건** |

- `./gates/run.sh all` 은 돌리지 않았다(지시 범위). `detail-edit.test.tsx` 는 이번에 재시도 없이 통과했다.
- 워크트리 `frontend/node_modules` 는 본체 트리로 건 심링크다(gitignored · 커밋 대상 아님).

## 6. PLAN-SoT §9 초안 — 병합 직전에 `〈N〉` 을 다시 잰다

```
| 〈N〉 | **R-A-3 FE 계층 — 상세 수정 진입점 신설 · 구역 메뉴 sticky(미결-9 ⓑ 최종형) · 종료 조건 개정** | **집행 (2026-09-05 · 워크트리 `p3-close-guard` · 병합 `<sha>` · 계약 개정 0 · 마이그레이션 0 · staging 접촉 0).** ①회차 = **해당 없음**(계약 미개방) ②값 = 없음 ③근거 = PRD-14·20·22·23·24 (`dev-package/prd/PRD-260905-적용전기획.md`) ④가·파 판정 = **해당 없음** · `contract-breaking` 출력 = `<축자 · 변경 0 확인>` ⑤소비자 = 해당 없음 ⑥마이그레이션 = **0건** ⑦승인 = 불요(㉮ 밖 · 계약 미접촉) ⑧이번에 세지 않은 축 = 대표 그림 저장 경로(WU-C2 별건) `[미측정]` |
```

## 7. 남은 것

- `[미상]` 없음. 미접촉 = `components/detail/` · `DatasetDetailPage.tsx` · `PreviewPanel.tsx`(WU-A8·A10 레인).
