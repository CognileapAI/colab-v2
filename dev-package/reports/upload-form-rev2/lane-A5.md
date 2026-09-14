# 레인 A5 — 업로드 ③ 연결 단계의 후보 팝업·연결 카드를 기획서 rev2 목업에 맞춘다

- 기점 `2e9b223a` (`feature/rtf400_upload_form`) · 브랜치 `feature/rtf400_upload_reaper`.
- 오라클 = 기획자 목업 `업로드_계보_260905_rev2.html` (읽기 성공 · 2,740행)
  — `#findModal`(`.findbar`·`#findList .frow`·`.modal-f`) · `pickFind()` 가 세우는 `.lin-item` ·
  CSS `.findbar`·`.frow`·`.lin-item`·`.li-top`·`.li-sub`·`.li-act`·`.manflag`.
- 사용자 지시(2026-09-14) 다섯 항목 전부 반영. 범위 = 프런트만(계약·서버·마이그레이션 0).

---

## 1. 대조표 — 목업 ↔ 기점 코드 ↔ 이번 결과

### 1-1. 후보 찾기 팝업 (`#findModal`)

| 목업 자리 | 목업 실물 | 기점 `2e9b223a` | 이번 결과 |
|---|---|---|---|
| `.findbar` 칸 ① | `<input placeholder="이름이나 파일명으로 찾아요">` | 검색 칸 1개 있음 | 무변 (`aria-label="데이터셋 이름 또는 파일명 검색"`) |
| `.findbar` 칸 ② | `<select>` 분류 전체 ＋ 5값 | **없음** | 복원 — `lin-cat-filter` · `분류 전체` ＋ `CATEGORIES` |
| `.findbar` 칸 ③ | `<select>` 기간 전체 ＋ 연도 | **없음** | 복원 — `lin-period-filter` · `기간 전체` ＋ **후보가 실제로 가진 연도** |
| `.findbar` 칸 ④ | `<select id="findLv">` · `buildFindLv()` 가 자기 Lv 이하만 | **없음** | 복원 — `lin-lv-filter` · `연결 가능 전체 · Lv0~Lv{자기}` ＋ `Lv0`…`Lv{자기}` |
| `#findList .frow` | 라디오 ＋ 이름 ＋ 부제 ＋ `.fmt`·`.lvl LvN` | 라디오 ＋ 이름 ＋ `Lv{n}` ＋ 분류·기간 ＋ 파일 | 무변 (＋ 줄마다 Lv 표시 시험 신설) |
| `.frow.is-over` | 흐리게 ＋ `over-why` · 라디오 `disabled` | 같음 | 무변 (PRD-08 회귀) |
| 목록 높이 | 모달 본문 스크롤 | `height:320px` ＋ `overflow-y:auto` | 무변 |
| `.modal-f` | `취소` ＋ `이 데이터로 연결` **둘뿐** | 요약 ＋ **가공 방식 입력** ＋ 두 버튼 | 가공 방식 입력 **제거** · 요약 ＋ 두 버튼 |

- 질의 연결 — 네 칸이 **한 질의**로 나간다(PRD-41 「네 조건은 AND」).
  `q` · `category` · `periodStart`/`periodEnd`(연도 → `YYYY-01-01`~`YYYY-12-31`) · `processingLevel`.
  UTC 하루 경계 변환은 기존 `lineageSource.candidateQuery` 가 그대로 한다(그 파일 무수정).
- 죽어 있던 `levelFilter`／`onLevelFilterChange` prop 이 가공 단계 칸에 다시 연결됐다.
- 연도 항목은 **후보가 실제로 가진 연도**(기간 시작 연도)만 세운다 — 없는 연도를 지어내지 않는다.
  고른 연도는 결과가 줄어도 목록에 남긴다(되돌릴 길).

### 1-2. 연결 카드 (`pickFind()` 가 만드는 `.lin-item`)

| 목업 자리 | 목업 실물 | 기점 `2e9b223a` | 이번 결과 |
|---|---|---|---|
| `.li-kind` | `가공 전 데이터` | **없음** | 추가 |
| `.li-name` | 파일명 | 이름 있음 | `lin-card-name` 로 표식 |
| `.lvl` | `LvN` | **없음** | 추가 — `lin-card-lv` |
| `.manflag` | `직접 연결` (오른쪽 끝) | **없음** | 추가 |
| `.li-warn` | `확인 필요` 칩 | 있음 | 무변 (PRD-09) |
| `.li-sub` | 분류·기간 등 한 줄 | **없음** | 추가 — `lin-card-info` = `분류 · 기간` |
| `.li-act` 입력 | `가공 방식 (선택)` 1칸 | 있음 | 무변 — **빈 값으로 시작**(팝업이 채우지 않는다) |
| `.li-act` 버튼 | `지우기` **하나** | `확인`·`수정`·`거절` 셋 | `지우기` 하나(`lin-del`) |
| 확정 상태 | 없음(연결이 곧 확정) | `확인함` 표시 ＋ `confirmed:false` 시작 | `확인함` 제거 · 연결 시 `confirmed:true` |

### 1-3. 목업에 없는데 코드에 남긴 것 — **판정 필요 1건**

| 항목 | 목업 | 이번 처분 | 사유 |
|---|---|---|---|
| 카드의 `부모 역할` 셀렉트(`lin-role` · `주입력`／`보조입력`) | **없음** | **존치** | 지시문의 제거 대상은 「확인·수정·거절 버튼과 그 상태(AI 제안 흔적)」로 닫혀 있고 부모 역할은 그 둘 어디에도 없다. 계약 `UploadLineageParent.parentRole` 을 화면에서 정하는 유일한 자리이고 `upload.test.tsx` 가 두 값의 전송을 잰다. 지우면 요청이 늘 `주입력` 으로 굳는다. **목업 통일을 우선하려면 판정이 필요하다.** |

- ⭑ **⟨해소 2026-09-14 · 레인 A6⟩ 위 1건은 사용자 결정으로 제거했다** — 셀렉트·라벨을 걷고 요청의 `parentRole` 은 계약 기본값 `주입력`(`contracts/schemas/common.json#ParentRole` 의 `default`) 고정. 계약·DB 무변이고 고치는 자리는 상세의 계보 수정(`LineageFixModal`)이다. 위 표의 「존치 · 판정 필요」는 A5 시점 값이다.

---

## 2. 되돌린 것 — PRD-08 개정 표시 3자리

- `343bc02b` 가 넣은 PRD 파일 hunk 를 역적용(`git apply -R`). 되돌린 자리 셋 —
  1. 제목 — `#### PRD-08 · 찾기 모달에 가공 단계 필터 · 초과 후보는 흐리게 + 사유`
  2. 제목 아래 개정 블록(⭑ ⟨개정 2026-09-14 …⟩ 5행) 삭제
  3. `- **변경 — 프론트**: 찾기 모달에 가공 단계 필터 셀렉트. …`
  4. §3 등록 3단계 요약 ③ — `+ 가공 전 데이터 추가` → 찾기 모달. 모달에 가공 단계 필터. …
- 실측 — `개정 2026-09-14 · 기획자 2026-09-13 구두 피드백 「핵심 정보만 · 필터는 검색어 하나」` **0건**.
- 문서와 화면의 판정 충돌이 소멸 — PRD-08·PRD-41 이 요구한 필터가 화면에 실재한다.
- `dev-package/reports/upload-form-rev2/lane-A2.md` 의 같은 커밋 추가분은 A2 실적 기록이라 무접촉.

---

## 3. 재는 대상이 바뀐 시험 (A2 단언의 개정)

| 파일 · 시험 | 종전 단언 | 이번 단언 | 사유 |
|---|---|---|---|
| `parent-picker-20260914` ㈎ | 「검색어 한 칸만 · 셀렉트 0개」 | 「네 칸 · combobox 3개」 ＋ Lv 항목 상한 ＋ 연도 항목 ＋ 네 조건 한 질의 | 목업 `.findbar` 축자 |
| `parent-picker-20260914` ㈒ | 하단 가공 방식 입력값이 `onPick` 2번째 인자로 간다 | **하단에 가공 방식 칸이 없다** ＋ `onPick` 인자 1개 | 목업 `.modal-f` 축자 · 지시 ⑶ |
| `parent-picker-20260914` ㈓ | 모달에서 적은 가공 방식이 카드 초기값 | 카드의 가공 방식 칸이 **빈 값으로 시작**하고 거기서 적는다 | 지시 ⑶ |
| `lv-rules-20260907` ㈎ | 「후보 목록에 가공 단계 필터가 **없다**」 | 「자기 Lv=Lv0 이면 필터 항목이 `['', '0']` 하나다」 | 목업 `buildFindLv()` |
| `upload.test` ③ 블록 | 확인 / 수정 / 거절 3버튼 · `확인` 뒤 전송 | 연결이 곧 전송 대상 · `지우기` 하나 · 3버튼 부재 | 목업 `.li-act` |

- 신설 시험 6건 — 필터 4칸 · Lv 항목 상한 · 연도 항목 · 네 조건 한 질의 · 줄마다 Lv · 카드 4건(버튼 하나 · 이름/Lv/분류/기간 · 가공 방식 빈 시작 · 지우기).
- **red 확인 로그(구현 전)** — `Tests 18 failed | 168 passed (186)`.
  대표 한 줄 = `FAIL test/parent-picker-20260914.test.tsx > 후보 선택 모달의 필터 > 이름 검색 · 분류 · 기간 · 가공 단계 네 칸이 선다` ·
  `TestingLibraryElementError: Unable to find an accessible element with the role "combobox"`.

---

## 4. 범위 밖 접촉 — 2건 (초과로 기재)

1. `frontend/src/components/lineage/types.ts` — `ParentCard` 에 `parentCategory`·`parentPeriod`(선택) 추가,
   `picking` 을 선택으로 완화. 카드가 분류·기간을 되읽으려면 그 값을 들고 있어야 하고, 그 열쇠의 자리가 이 파일뿐이다.
   `picking` 열쇠 자체는 남겼다 — `upload-form-rev2-20260914.test.tsx`(A4 소유)가 그 이름으로 카드를 만든다.
2. `frontend/test/lineage-unknown-20260907.test.tsx` — `lin-confirm` 클릭 1행 제거.
   그 버튼이 사라져 이 시험이 판정 red 가 되므로 불가피하다. 재는 사실(기록 없음 체크박스 비활성 ＋ 사유)은 무변.

- `RegisterArea.tsx`·`UploadModal.tsx`·`PreviewPanel.tsx` 무접촉(`git status` 실측).
- `dev-package/prd/specs/R-A2.md` 존치 6종 무접촉 — `git diff --name-only -- dev-package/prd/specs/` 0건.
- `lineageSource.ts` 무수정 — 연도→구간 두 값은 화면이 만들고, UTC 경계 변환은 기존 `candidateQuery` 가 한다.

---

## 5. 게이트

- 실행 = `COLAB_TASK_ID=… COLAB_GATE_REPORT_DIR=dev-package/reports/upload-form-rev2/lane-A5 bash gates/run.sh task`
  (선언된 두 게이트를 한 `run_id` 아래 각각 1회).

| 게이트 | 요약줄 |
|---|---|
| `frontend-typecheck` | `green — tsc --noEmit(frontend/tsconfig.json · include=src·test) 오류 0건.` |
| `frontend-test` | `green — vitest run(frontend/vite.config.ts · jsdom) 통과 1363건 · 실패 0건.` |

- **3계수 — green 2 / red(판정) 0 / red(준비) 0** (`gate-summary.json` · `colab-gate-summary/1`).
- 부하 대기 만료 0건 — 단독 재실행 불요.
- 단독 실측(게이트 실행 전과 같은 값) — `npx tsc --noEmit` 오류 0 · `npx vitest run` Test Files 112 passed / Tests 1363 passed.
- 워크트리 준비 — `npm install --no-save @rolldown/binding-darwin-x64` 1회(darwin 바인딩 부재 · `package.json` 무수정).
