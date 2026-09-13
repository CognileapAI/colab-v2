# 레인 A2 — 업로드 모달 「연결」 단계 문구와 「가공 전 데이터」 후보 선택 모달을 rev2 ＋ 기획자 2026-09-13 피드백에 맞춤

- 기점 = 레인 A1 결과 `fef2aa59`(`git reset --hard` 로 대조 확인 · 지시문 기대값과 일치).
- 프론트 전용 — **계약·서버·DB·마이그레이션 변경 0건.** `contracts/` 무접촉.
- 오라클 = `업로드_계보_260905_rev2.html` 의 `#reg-s2`(연결 단계) · `#findModal`(후보 모달) 축자
  ＋ 기획자 2026-09-13 구두 피드백(핵심 정보만 · 대표 파일명 외 N개 · 검색어 하나 · 하단 고정 영역).

## 1. 변경 파일

| 파일 | 내용 |
|---|---|
| `frontend/src/components/lineage/ParentPicker.tsx` | 행을 라디오 단일 선택으로 · 표시값 4종으로 축소 · 「외 N개」 · 필터 1칸 · 하단 고정 영역(요약＋가공 방식＋버튼) |
| `frontend/src/components/lineage/LineageStep.tsx` | `lin-add` 문구 · 연결 0건 빈 상태 한 줄 신설 · 모달 가공 방식을 카드 초기값으로 전달 |
| `frontend/src/components/lineage/lineage.css` | 목록 고정 높이·스크롤 · 라디오 행 배치 · 하단 고정 영역 · `lin-hint` · 초과 후보 선택자 교체 |
| `frontend/test/parent-picker-20260914.test.tsx` | **신규 12건** — 이 회차의 오라클 |
| `frontend/test/lineage-continuation.test.tsx` | 개정 2건(기간 칸·주제 칸 제거에 따른 측정 자리 이동) |
| `frontend/test/lv-rules-20260907.test.tsx` | 개정 1건(가공 단계 셀렉트 제거) |

## 2. 화면 변경 목록

**연결 단계 (`LineageStep`)**

- 직접 추가 버튼 문구 `앞 데이터 직접 추가` → **`+ 가공 전 데이터 추가`**(rev2 `#findModal` 여는 버튼 축자).
- 연결 0건 빈 상태 한 줄 신설 — `lin-hint` · 문면 **`아직 연결한 가공 전 데이터가 없어요`**(rev2 `#linHint` 축자).
  자리 = 추가 버튼 바로 위(rev2 배치). 연결이 1건이라도 생기면 사라진다.
- 후보 모달에서 적은 가공 방식이 연결 카드의 `lin-method` **초기값**으로 들어온다. 카드 안의 칸은
  편집용으로 그대로 남는다. 빈 칸이면 두 번째 인자를 **싣지 않는다** — 기존 값을 빈 문자열로 덮지 않는다.
- `수정` 경로(`lin-edit-picker`)도 같은 규칙으로 값을 받는다(적었을 때만 덮음).

**후보 선택 모달 (`ParentPicker` · `onClose` 있는 모달 모드)**

- 행 = **라디오 단일 선택**(`lin-pick-<id>` 가 `<input type="radio">` 로 바뀜 · 같은 `name` 한 벌).
  누르는 것은 선택이고, 확정은 하단의 `이 데이터로 연결` 이 한다.
- 행이 적는 값 = **이름 · 가공 단계 · 분류 · 기간** 넷. `topic`·`source.label` 표기 제거.
- 파일 = **`대표 파일명 외 N개`**(`candidateFilesLabel`). 1건이면 이름만, 0건이면 줄 자체가 없다.
  종전 `fileNames.join(', ')` 전체 나열 제거.
- 필터 = **검색어 한 칸**. 분류·주제·가공 단계·기간 시작·기간 끝 5칸 제거.
- 목록 = **고정 높이 320px(`max-height: 42vh`) ＋ 세로 스크롤**(`.lin-cand-list`).
- 하단 고정 영역(`.lin-find-f`) = 선택 요약(`lin-find-summary`) ＋ 가공 방식(`lin-find-method`) ＋ `취소`／`이 데이터로 연결`.
  후보를 고르기 전 요약 자리 문면 = **`후보를 고르세요`**, 고른 뒤 = `이름 · Lv · 분류`.
- 초과 후보(부모 Lv > 자기 Lv) 동작·문면 **무변** — 목록에 남고 라디오만 비활성이며 사유 한 줄이 읽힌다(`R-21`).
- 글자 크기는 전부 `var(--text-caption)`(`tokens.css:37` = **13px**) 이상.

**무변**

- 상세 계보 모달(`LineageFixModal`)이 쓰는 **인라인 모드는 문면·동작 무변**. 하단 고정 영역은
  `onClose` 가 있는 모달 모드에서만 선다 — 그쪽은 자기 바닥(`lin-fix-pick`)을 이미 갖고 있다.
- `ParentPicker` 의 props 형상 무변(`onPick` 두 번째 인자만 **선택 인자로 추가**). `LineageFixModal.tsx` 무접촉.
- AI 제안(`lin-ask` 버튼·훅·시험) 무접촉 — `LineageStep.tsx` diff 에 `lin-ask` 0줄.
- `RegisterArea.tsx`·`UploadModal.tsx`·`PreviewPickRow.tsx`·`PreviewPanel.tsx` 무접촉.

## 3. 지시문과 실물이 어긋난 곳 (구현하지 않음 · 판정 필요)

지시문 = 「연결 0건 빈 상태 문구 `가공 전 데이터를 못 찾았어요 (기록 없음)`」.

- 그 문자열은 rev2 HTML 에서 **0건 빈 상태가 아니라 「기록 없음」 체크박스의 라벨**이다
  (`#unknownChk` 라벨 · rev2 축자). 0건 빈 상태는 `#linHint` 이고 문면이 다르다
  (`아직 연결한 가공 전 데이터가 없어요`).
- 그 체크박스 라벨은 **Ted 확정 판정**(미결-6 ⓐ · 2026-09-05)이 정한 축자
  `가공 전 데이터를 못 찾았어요 — 기록 없이 등록할게요` 다
  (`PRD-260905-적용전기획.md:71`·`:687`·`:698` · `LineageStep.tsx:64` · 시험
  `lineage-unknown-20260907.test.tsx:188` 이 상수를 축자로 단언).
- 두 문면을 바꾸면 **판정 재개봉**(`colab-rules §8`)이고 소유 밖 시험 1건이 깨진다. 그래서
  **체크박스 라벨은 손대지 않고**, 0건 빈 상태는 rev2 `#linHint` 축자로 신설했다.
  체크박스 라벨을 rev2 축자로 되돌릴지는 **Ted 판정 대상**이다.

## 4. 존치 6종 (`dev-package/prd/specs/R-A2.md` 범위 밖 절) 대조

| 존치 항목 | 이 레인의 접촉 |
|---|---|
| 기준 격자 파일 흐름 | **없음** |
| AI 계보 제안 | **없음**(`lin-ask` 0줄) |
| 2단 등록 게이트 | **없음** |
| 이어올리기 배너 | **없음** |
| 승인·검증 층 | **없음** |
| 값 조회 패널 | **없음** |

## 5. 시험 계수

| 시점 | 계수 | 비고 |
|---|---|---|
| 기점(`fef2aa59`) | 계보 3파일 단독 **33/33 통과** | 이 레인이 실측한 것은 이 3파일뿐이다 — 기점 전수는 돌리지 않았다(A1 보고 5절이 그 값을 갖는다) |
| 신규 시험 최초 실행(RED) | 12건 중 **10 red** · 2 green | red 로그 한 줄 — `AssertionError: expected 'button' to be 'radio'` ／ `TestingLibraryElementError: Unable to find an element by: [data-testid="lin-find-summary"]` ／ `AssertionError: expected '앞 데이터 직접 추가' to be '+ 가공 전 데이터 추가'`. green 2건 = 검색어 한 조건 질의·확정 전 비활성(종전부터 참) |
| 구현 후 소유 밖 파급 | red 3건(＋간헐 1) | `lineage-continuation` 2 · `lv-rules-20260907` 1 — 전부 제거된 필터 칸을 잡던 자리. 같은 실행의 `upload-transfer` 1건은 단독 재실행 통과(간헐) |
| 후 1회차 | 파일 110 / 시험 1355 — **전건 통과** | |
| 후 2회차 | 파일 110 / 시험 1354 통과 · 1 실패 | 실패 = `preview-slot-4x3.test.tsx` 「세 문구가 순서대로…」 대기 만료. **단독 재실행 8/8 통과** — Rosetta 간헐 시간 초과(A1 보고 5절과 같은 양상) |
| 후 3회차 | 파일 110 / 시험 1355 — **전건 통과** | 간헐 실패 재현 없음 |
| `tsc --noEmit` | 2회 연속 오류 0건 | |

## 6. 게이트

```
frontend-test green — vitest run(frontend/vite.config.ts · jsdom) 통과 1355건 · 실패 0건.
frontend-typecheck green — tsc --noEmit(frontend/tsconfig.json · include=src·test) 오류 0건.
── 계 : green 2 / red(판정) 0 / red(준비) 0
```

- 한 실행(`gates/run.sh task` · 선언 게이트 2종)이고 부분 실행 합산이 아니다.
- 배출처 `dev-package/reports/upload-form-rev2/lane-A2/gate-summary.json`(`colab-gate-summary/1` ·
  `task_id` `0f34ab2882184230a7d47c3e1f2c2c51` · `verify-report` green · before/after 파일 hash 동일).
- 전수 `all` 은 이 레인이 돌리지 않았다 — 병합 직전 1회는 오케스트레이터 몫(`colab-rules §3-1`).

## 7. 원한 결과 대조

지시문 작업 5건 기준. `dev-package/intent/` 에 이 회차 항목 파일 **없음** — 대조 원본은 지시문 본문.

- **미달 1건** — 「연결 0건 빈 상태 문구 `가공 전 데이터를 못 찾았어요 (기록 없음)`」.
  막는 것 = 그 문자열이 Ted 확정 판정이 폐기한 체크박스 라벨 자리라는 사실(위 3절). 판정 대기.
- **초과 3건** —
  1. 소유 밖 시험 `frontend/test/lineage-continuation.test.tsx` 2건 개정. 사유 = 「검색어 하나만」이
     기간 2칸·주제 칸을 없애 그 칸을 잡던 단언이 red. 조치 = UTC 하루 경계 변환은
     `lineageSource.lineagePeriodStart/End` 를 직접 재고(규칙 자체는 살아 있다), 「새 필터」의
     자리는 검색어가 맡는다. **재는 대상은 그대로**다.
  2. 소유 밖 시험 `frontend/test/lv-rules-20260907.test.tsx` 1건 개정. 사유 = 가공 단계 셀렉트 제거.
     조치 = 셀렉트 부재 ＋ 초과 후보가 목록에 남는다는 단언으로 갈아탔다.
  3. `ParentPicker.onPick` 에 선택 인자 `method` 추가. 사유 = 하단 가공 방식 값을 카드로 옮기는
     유일한 경로. 기존 호출부(`LineageFixModal`)는 인자 하나로 계속 동작 — 그 파일 무접촉.

## 8. 완료 정의

`dev-package/work-items.yaml` 에 이 작업의 항목이 **없다** — 완료 정의 **미작성**.
대장·원장·HANDOFF 무접촉(지시문 지시).

## 9. 후속 항목

1. **Ted 판정** — 「기록 없음」 체크박스 라벨을 rev2 축자 `가공 전 데이터를 못 찾았어요 (기록 없음)` 로
   되돌릴지. 되돌리면 미결-6 ⓐ 재개봉이고 `lineage-unknown-20260907.test.tsx:188` 이 함께 바뀐다.
2. **가공 단계 필터 제거의 대가** — 후보가 많은 연구실에서 초과 후보를 걸러 내는 유일한 수단이
   사라졌다. 검색어만으로는 Lv 로 좁힐 수 없다. 어느 검사에도 걸리지 않는다 — 게이트에도
   Dockerfile 에도 배포 스크립트에도 그 기능을 재는 자리가 없었다(제거 전에도 시험 2건뿐).
3. **`ParentPicker.onLevelFilterChange` 가 죽은 prop 이 됐다** — 화면 셀렉트가 사라져 호출되지 않는다.
   `levelFilter` 는 서버 질의로 계속 간다. 두 호출부(`LineageStep`·`LineageFixModal`)가 여전히 상태를
   쥐고 있어 타입은 green 이다. prop 을 걷을지는 `LineageFixModal` 소유 레인과 함께 판정 필요.
4. **상세 계보 모달과 등록 ③ 의 후보 줄 모양이 갈렸다** — 인라인 모드는 하단 영역이 없고 고르는
   즉시 확정된다. 같은 `ParentPicker` 한 벌이지만 확정 지점이 둘이다. 통일 여부 판정 필요.
