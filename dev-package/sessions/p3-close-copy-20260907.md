# WU-A9R — 닫기 문면 3종 ＋ 배경 클릭 닫기 ＋ 손댐 판정 (레인 `p3-close-copy` · R-A′ · 2026-09-07)

- 기준 = `integration/r-a2` `ace3b6a` (`git merge --ff-only` 로 맞춤)
- 범위 = 프론트만. 계약 0 · 스키마 0 · 마이그레이션 0 · 서버 0
- 근거 문서 = `dev-package/prd/rounds/R-A2.md §2-④` · `dev-package/prd/specs/R-A2.md` · PRD-14 · PRD-34 · PRD-44 · PRD-39 ⑭

## 1. 완료 조건 ↔ 판정 ↔ 근거

완료 조건 축자(라운드 파일 §2-④ · 대장 `completion_def`) — 「본문이 상황별 3종이고 계보 3건이면 문면에 3 이 보간되며 버튼 라벨이 계속하기·닫고 나가기 다 · 배경 클릭이 닫기 확인을 그대로 타고 모달 내부 클릭은 닫지 않는다 · 손댐 판정에 담은 프로젝트 건수와 대표 그림 교체 여부가 더해진다」

| 완료 조건 | 판정 | 근거 (파일:행) |
|---|---|---|
| 본문 상황별 3종 | 충족 | `frontend/src/components/common/toastCopy.ts:130` `uploadCloseMessage()` · 화면 `frontend/src/components/upload/UploadModal.tsx:967` · 시험 `frontend/test/prd34-close-copy-20260907.test.tsx:202` |
| 계보 3건 → `3` 보간 | 충족 | `toastCopy.ts:126` `uploadCloseWithLineage()` · 시험 `prd34-close-copy-20260907.test.tsx:214` |
| 제목 `업로드를 닫을까요?` 유지 | 충족 | `toastCopy.ts:108` · `UploadModal.tsx:961` |
| 버튼 `계속하기` · `닫고 나가기` | 충족 | `toastCopy.ts:110`·`:112` · `UploadModal.tsx:979`·`:982` |
| 배경 클릭이 닫기 확인을 그대로 탄다 | 충족 | `UploadModal.tsx:663-672` (`requestClose()` 하나만 부른다) · 시험 `prd34-close-copy-20260907.test.tsx:277` |
| 모달 내부 클릭은 닫지 않는다 | 충족 | 같은 자리 `e.target === e.currentTarget` · 시험 `:293` |
| 손댐 판정 ＋ 담은 프로젝트 건수 | 충족 | `UploadModal.tsx:353` `projects.length > 0` (종전분 유지) · 시험 `:249` |
| 손댐 판정 ＋ 대표 그림 교체 여부 | 충족 | `UploadModal.tsx:123`·`:356`·`:810` ＋ `PreviewPanel.tsx:73`·`:223` · 시험 `:258` |
| 자동 채움값은 세지 않는다 (PRD-14 유지) | 충족 | `UploadModal.tsx:324-357` 주석·판정식 · 시험 `:268` · 기존 `test/close-guard-20260905.test.tsx` |
| Esc 우선순위 (PRD-39 ⑭) | 부분 — 아래 §4 | `UploadModal.tsx:505-529` · 시험 `:303`·`:313`·`:320` |

## 2. RED → GREEN

`npx vitest run test/prd34-close-copy-20260907.test.tsx`

| 시점 | 계수 | 실측 줄 |
|---|---|---|
| RED (구현 전) | `Tests 8 failed \| 7 passed (15)` | `TestingLibraryElementError: Unable to find an element by: [data-testid="upload-backdrop"]` · `AssertionError: expected <div class="modal" …(1)>…(3)</div> to be null` |
| GREEN (구현 후) | `Tests 15 passed (15)` | — |

- 문면이 열려 종전 축자를 잡고 있던 시험 2건은 상수 참조로 옮겼다 — `test/close-guard-20260905.test.tsx`(조건 시험은 무변) · `test/upload.test.tsx`. 함께 돌린 3파일 `Tests 124 passed (124)`.
- 처음부터 green 이던 7건은 오라클로 세지 않는다(문면 상수 대조·순수 함수분).

## 2-1. 게이트 (좁은 게이트 2종 · 배출처 `dev-package/reports/R-A2/p3-close-copy`)

```
frontend-typecheck green — tsc --noEmit(frontend/tsconfig.json · include=src·test) 오류 0건.
  ── 계 : green 1 / red(판정) 0 / red(준비) 0
frontend-test green — vitest run(frontend/vite.config.ts · jsdom) 통과 855건 · 실패 0건.
    Test Files  61 passed (61)
         Tests  855 passed (855)
  ── 계 : green 1 / red(판정) 0 / red(준비) 0
```

- 두 게이트 다 판정 red 0 · 준비 red 0. `gates/run.sh` 는 게이트를 한 번에 하나만 받아 두 번 돌렸다(요약 JSON 은 마지막 실행분).
- 전수 `all` 은 돌리지 않았다 — 레인 규약 §3-1.

## 3. 문면 출처 표

원문 = `40 COLAB-기획/10_적용전/업로드_계보_260905_rev2_이태헌.html` (읽기 전용 · 채록본 경유). 개발 세션이 새로 지은 문장 0건.

| 문면 | 원문 자리 | 코드 자리 |
|---|---|---|
| `업로드를 닫을까요?` | HTML `:1134` 확인 모달 제목 | `toastCopy.ts:108` |
| `계속하기` | HTML `:1139` `data-name="계속하기"` | `toastCopy.ts:110` |
| `닫고 나가기` | HTML `:1140` `data-name="닫기 확정"` | `toastCopy.ts:112` |
| `올린 파일이 취소돼요. 원본 파일은 그대로라 다시 올리면 돼요.` | HTML `:2101` `closeUpload()` `!dirty` 갈래 | `toastCopy.ts:115` |
| `적은 내용이 사라지고, 데이터셋은 만들어지지 않아요. 원본 파일은 그대로예요.` | HTML `:2105` `dirty && lin===0` 갈래 | `toastCopy.ts:117` |
| `적은 내용과 연결한 계보 N건이 사라지고, 데이터셋은 만들어지지 않아요. 원본 파일은 그대로예요.` | HTML `:2103` `dirty && lin>0` 갈래(`lin` 보간) | `toastCopy.ts:126` |
| 배경 클릭 핸들러 | HTML `:815` `onclick="if(event.target===this)closeUpload()"` | `UploadModal.tsx:663-672` |
| Esc 우선순위 | HTML `:2725-2737` `keydown` 핸들러 | `UploadModal.tsx:505-529` |
| 손댐 판정 `proj:`·`thumb:` | HTML `:2081-2093` `upState()` | `UploadModal.tsx:353`·`:356` |

`[미상]` 0건 — 필요한 축자가 전부 원문에 있었다.

## 4. 자기 표시 (초과·미달)

- 미달 1 — **확장보기(라이트박스) 배경 클릭은 넣지 않았다.** 그 오버레이가 코드에 없다(`src/components/` 전수 grep 0건). 라운드 파일 「이 라운드에 없는 것」이 `PRD-39 ⑤ 확장보기 오버레이(M)` 를 R-B `WU-B3` 로 보냈다. 없는 화면에 핸들러를 지어 붙이지 않았다.
- 미달 2 — **Esc 우선순위 5층 중 앞 3층(확장보기·찾기·계보 수정)은 이 레인에 화면이 없다.** 층 이름을 코드에 박는 대신 표식 `data-esc-layer` 하나를 보게 했다(`UploadModal.tsx:53`) — 표식이 떠 있으면 업로드는 Esc 를 먹지 않는다. 남은 두 층(닫기 확인 → 업로드)의 순서는 실측했다. 앞 3층이 그 표식을 붙이는 것은 그 층을 담는 WU 몫이다.
- ⭑ 반영 3 — advisor ② 의 F1~F3(대표 그림 플래그 초기화 · 관측 간격 3필드 계수 · 배경 드래그 거짓 닫기 방지)을 이 레인에서 반영했다. 상세는 §6.
- 초과 1 — `PreviewPanel` 에 프로퍼티 `onThumbPick` 1개를 더했다. 대표 그림 교체 사실이 그 컴포넌트 안에만 있어 모달의 판정식이 닿을 자리가 없었다. 그림 자체는 바깥으로 넘기지 않는다.
- 초과 2 — 종전 문면을 축자로 잡던 기존 시험 2건의 단언을 상수 참조로 바꿨다. PRD-34 가 문면을 열었으므로 그대로 두면 red 다. 조건 시험(미결-15 ⓐ)은 한 건도 지우지 않았다.
- 문면 중복 0건 — `test/toast-copy-20260906.test.tsx` 의 「하드코드 중복 0건」 검사 대상 목록(`FIXED_COPY`)에 새 고정 문면 5개를 등재했다(`toastCopy.ts:202-203`). 화면에 문자열을 다시 적으면 그 시험이 red 를 낸다.

## 5. 하지 않은 것

- 계약·스키마·마이그레이션·서버 — 손대지 않음(`contracts/`·`db/`·`alembic` 무변).
- 존치 6종 — 무변.
- `RegisterArea.tsx` 행동 줄(sticky `.reg-actions`)·`UploadModal` 전역 드롭·`removeFile` 초기화(WU-A12R 분) — 되돌리지 않았다.
- 확인 모달 자체의 배경(`confirm-back`) 클릭 닫기 — 요구에 없다. 지어 붙이지 않았다.
- 대표 그림 저장 경로(`WU-C2`) — 무변. 고른 그림은 화면에서만 산다.

## 6. advisor ② 반영

어드바이저 게이트 ② 판정 `approve-with-changes`. F1·F2·F3 은 병합 전 필수, F4·F5 는 동반 정정.

| 항목 | 자리 | 내용 |
|---|---|---|
| F1 | `UploadModal.tsx` `removeFile()` | `setThumbReplaced(false)` 추가. 파일을 빼면 대표 그림 교체 표시도 내린다 — 재첨부 뒤 아무것도 안 적은 사람이 되묻히던 자리 |
| F2 | `UploadModal.tsx` `hasHumanInput` | `intervalValue`·`intervalUnit`·`granularity` 를 trim 후 계수에 추가. 판정식 주석의 필드 목록에 「② 관측 간격 값·단위 · 기간 최소 단위」 한 줄 추가 |
| F3 | `UploadModal.tsx` 배경 `div` | `onMouseDown` 이 `downOnBackdrop` ref 에 눌린 자리를 기록하고, `onClick` 은 `e.target === e.currentTarget && downOnBackdrop.current` 일 때만 `requestClose()`. 모달 안에서 눌러 배경에서 뗀 드래그(텍스트 선택)가 확인 없이 취소시키던 자리 |
| F4 | `UploadModal.tsx` Esc 갈래 | 손댐 판정 복제를 걷고 `requestClose()` 호출로 교체. 판정 자리 1곳 |
| F5 | `prd34-close-copy-20260907.test.tsx` · `upload.test.tsx` | 주석의 상수명을 실재하는 `ESC_LAYER_ATTR` 로 정정. `upload.test.tsx` 시험 제목을 「입력 있음 갈래 상수」로 정정(단언 내용과 일치) |

RED 선실측 → GREEN — `frontend/test/prd34-close-copy-20260907.test.tsx` 신규 4건.

```
     × 파일을 빼면 대표 그림 교체 표시도 내린다 — 재첨부 뒤 닫기는 되묻지 않는다 61ms
     × 관측 간격만 적어도 묻는다 — 사람 입력 필드 전부를 센다 1027ms
     × 관측 간격 단위만 골라도 묻는다 1036ms
     × 모달 안에서 눌러 배경에서 뗀 드래그는 닫지 않는다 27ms
 Test Files  1 failed (1)
      Tests  4 failed | 15 passed (19)
```

GREEN — 같은 파일 19 passed. 기존 Esc 시험 3건·배경 클릭 시험 3건 무변 green(F3 으로 배경 클릭 시험 2건은 `mouseDown` ＋ `click` 을 함께 보내는 `backdropClick()` 헬퍼 경유로 바꿨다 — 실브라우저의 배경 클릭이 그 두 사건 순서이기 때문이고, 단언은 그대로다).

게이트 — `COLAB_GATE_REPORT_DIR=dev-package/reports/R-A2/p3-close-copy bash gates/run.sh <게이트>`.

```
frontend-typecheck green — tsc --noEmit(frontend/tsconfig.json · include=src·test) 오류 0건.
  green  frontend-typecheck
  ── 계 : green 1 / red(판정) 0 / red(준비) 0
         Tests  859 passed (859)
  green  frontend-test
  ── 계 : green 1 / red(판정) 0 / red(준비) 0
```

후속(이 레인 밖) — F6 은 오케스트레이터 몫이다. `work-items.yaml` 에 `WU-B3` 항목을 신설하거나 R-B 라운드 파일에 「확장보기 오버레이 = 배경 클릭 닫기 ＋ `data-esc-layer` 표식」 의무를 명기해야, 표식 규약의 소비자가 서고 §4 미달 2 가 닫힌다.
