# 어드바이저 게이트 ② — WU-A9R (lane p3-close-copy · 516e252 ← ace3b6a)

## 체크리스트 3항
- ① revision 체인 — 해당 없음. `git diff --name-only ace3b6a..516e252` 에 contracts/db/alembic/server 0건(frontend 6 · dev-package 2).
- ② 「main 과 동일」 — 세션 노트·보고에 red 를 main 핑계로 넘긴 대목 0건. typecheck·test 두 좁은 게이트 green(855).
- ③ intent 대조 — `dev-package/intent/2026-09-06-r-a2.md:17` 「종료 확인 본문이 상황별 3종이고 계보 건수가 보간되며, 배경 클릭이 닫기 확인을 그대로 탄다」 · `:30` 「문면 축자는 원문에서 뜬다」.

| 항목 | 판정 | 근거 |
|---|---|---|
| 본문 3종 · N 보간 | 충족 | `toastCopy.ts:115·117·126·130` · 시험 `prd34-close-copy-20260907.test.tsx:161-178, 202-240` |
| 축자 = rev2 HTML | 충족 | grep -F 로 HTML `:1134·:1139·:1140·:2101·:2103·:2105` ↔ TS 각 1건 일치. `[미상]` 0 |
| 버튼 `계속하기`·`닫고 나가기` | 충족 | `toastCopy.ts:110·112` · `UploadModal.tsx:979·982` · `계속 작성` 부재 단언 :211 |
| 배경 클릭 → `requestClose()` · 내부 클릭 무반응 | 충족(jsdom) / **미달(실브라우저 드래그)** | `UploadModal.tsx:660-672` click 만 검사 — 아래 R1 |
| 손댐 + 프로젝트 건수 | 충족(기존 `projects.length` 유지) | `:353` |
| 손댐 + 대표 그림 교체 | 충족 / **결함** | `:123·:356·:810` · `PreviewPanel.tsx:73·223`. `removeFile()` `:423-444` 가 `thumbReplaced` 를 내리지 않음 |
| 자동 채움값 미계수 | 충족 | `name !== nameDraft` · Lv/공개범위/확장자/용량 상태값 자체가 판정식에 없음 |
| PRD-14 「사람 입력 필드 전부」 | **미달** | `intervalValue`·`intervalUnit`·`granularity`(`:140·145·146`, setter `:925-935`) 가 `hasHumanInput` `:346-357` 에 없음 |
| Esc 우선순위 5층 | 부분(자기 표시) | 하위 2층 실측 `:505-529` · 상위 3층 = `data-esc-layer` 표식 규약만. 코드 내 소비자 0(`grep data-esc-layer` = UploadModal·시험만) |
| 확장보기 배경 클릭 | 미달(자기 표시 · 이관 정합) | 라운드 `R-A2.md:103` 「이 라운드에 없는 것 (R-B `WU-B3` 이관) — … PRD-39 ⑤ 확장보기 오버레이(M)」. `completion_def` 도 확장보기 미포함 |
| 초과 | 2건 | `PreviewPanel.onThumbPick` prop(필요 최소 · 그림 자체 미노출) · 옛 시험 2건 상수 참조 전환(축자 단언은 새 파일 :161-178 로 이전 — 손실 0) |

## For
- 축자 6종 전부 원문 1:1 · 문면 자리 한 곳(`FIXED_COPY` 등재로 중복 시험 방어) · 배경/×/Esc 가 `requestClose` 판정을 공유(Esc 만 예외) · 15 시험 red→green · 계약 접촉 0. 폐기하면 문면 채택(미결-r2-2 ⓐ) 자체가 이 라운드에서 빠진다.

## Against
- 판정식을 이 레인이 재소유하며 「PRD-14 그대로」를 주장했으나 ② 의 사람 입력 3필드가 빠져 있어, 관측 간격·최소 단위만 적은 사용자는 Esc·배경 클릭 한 번에 소리 없이 잃는다 — PRD-14 가 없애려던 반대 증상(잃을 것이 있는데 안 묻는다)을 이 WU 가 넓힌 닫기 경로(배경·Esc)로 오히려 노출 면적을 키운다.
- `data-esc-layer` 규약은 소비자도 대장 소유자(WU-B3 항목 부재)도 없는 계약 — 시험 :320 이 검증하는 것은 자기 자신이 만든 표식이다.

## Verdict
**approve-with-changes** — F1·F2·F3 병합 전 필수. 나머지 후속.

## Risks
1. 실브라우저 드래그(텍스트 선택 → 배경에서 release) 시 click.target 이 공통 조상 = 배경이 되어 `requestClose()` 호출 — 입력 0 상태면 업로드가 확인 없이 취소된다(jsdom 미검출).
2. `thumbReplaced` sticky — 파일 빼고 다시 올린 뒤 아무것도 안 적어도 확인이 뜬다(PRD-14 수용 기준 1 위반 경로).
3. WU-B3 가 대장에 없어 확장보기 배경 클릭·Esc 표식 의무가 유실될 수 있다.

## Missed
- `hasHumanInput` 에 `intervalValue`·`intervalUnit`·`granularity` 누락.
- `removeFile()` 에 `setThumbReplaced(false)` 누락.
- Esc 갈래 `:519-520` 가 `requestClose()` 대신 판정을 복제(두 판정 자리).
- 시험 `:315` 주석의 `ESC_LAYERS_ABOVE_CLOSE_CONFIRM` 는 존재하지 않는 이름(실제 `ESC_LAYER_ATTR`).
- `upload.test.tsx:420` 시험 제목 「정본 문구 그대로」가 단언 내용과 어긋남.
- `UPLOAD_CLOSE_FILE_ONLY` 는 UI 도달 불가(PRD-14 로 모달 자체가 안 뜸) — 결함 아님, PRD-34 수용 기준 1 과 정합. 기록만.

## Fixes
- **F1 [병합 전 필수]** `UploadModal.tsx:423-444` `removeFile()` 에 `setThumbReplaced(false);` 추가 ＋ 시험 1건(파일 빼기 → 재첨부 → 닫기 = 안 묻는다).
- **F2 [병합 전 필수]** `hasHumanInput` 에 `intervalValue.trim() !== '' || intervalUnit.trim() !== '' || granularity.trim() !== ''` 추가 ＋ 시험 1건(관측 간격만 입력 → 닫기 = 묻는다). 판정식 주석의 필드 목록도 갱신.
- **F3 [병합 전 필수]** 배경 `onMouseDown={(e) => { downOnBackdrop.current = e.target === e.currentTarget; }}` ref 를 두고 `onClick` 은 `e.target === e.currentTarget && downOnBackdrop.current` 일 때만 `requestClose()` ＋ 시험 1건(`fireEvent.mouseDown(modal)` → `fireEvent.click(backdrop)` = 안 닫힘).
- F4 Esc 갈래 `:519-520` 를 `requestClose()` 호출로 교체(판정 자리 1개).
- F5 시험 `:315` 주석 이름을 `ESC_LAYER_ATTR` 로, `upload.test.tsx:420` 제목을 「입력 있음 갈래 상수」로 정정.
- F6 [오케스트레이터] `work-items.yaml` 에 `WU-B3` 항목 신설 또는 R-B 라운드 파일에 「확장보기 오버레이 = 배경 클릭 닫기 ＋ `data-esc-layer` 표식」 의무를 명기. 병합 시 A9R `status: done` · 세션 노트 §4 에 F1~F3 반영 줄 추가.
