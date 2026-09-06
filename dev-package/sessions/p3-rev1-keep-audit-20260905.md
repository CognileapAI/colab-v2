# WU-A12 — rev1 유지 항목 실측 (PRD-39) · 레인 `p3-rev1-keep-audit` · 2026-09-05

원천 = `R-A-4-verify.md` §A 13행(표 14행 중 ⑼ 는 PRD-31 ⑶ 소관이라 뺐다).
**판정만 했고 아무것도 고치지 않았다.** `없음` 8건은 후속 WU 범위다.

## 1. 판정표 — 13행

| # | 항목 | 판정 | 근거 `path:line` | 회귀 시험 |
|---|---|---|---|---|
| 1 | 파일 분석 3단계 표시 ＋ 완료 전 `다음` 비활성 | **없음** | `frontend/src/components/upload/PreviewPanel.tsx:275-281`(서버 `stage` 문자열 한 줄 · 3단계 아님) · `components/upload/RegisterArea.tsx:9`(축자 「막지 않는다」)·`:534-541`(`다음 →` 무조건 활성) | — |
| 2 | 모달 전역 드롭 수신 | **없음** | `frontend/src` 전역에 `drop`·`dragover`·`dataTransfer` 핸들러 **0건** · `components/upload/FileDropCard.tsx:70-80` 은 `label` ＋ `input[type=file]` 뿐 | — |
| 3 | 파일 빼기 즉시 반영 ＋ 초기화 고지 | **없음** | 업로드 경로에 파일 제거 UI 0건(`FileDropCard.tsx:82-128` 목록만) · `RegisterArea.tsx:266-276` 의 `빼기` 는 **프로젝트 칩**이다 · 문면 `파일을 뺐어요…` 0건 | — |
| 4 | 대표 그림 되돌리기(`×`→자동본) ＋ 교체 시 파일명 | **없음** | `components/upload/PreviewPanel.tsx:312-320`·`:347-348` 은 자동 썸네일 **표시만** · 교체·되돌리기 조작 0건 | — |
| 5 | 미리보기 확장보기 오버레이 ＋ 그리는 중 잠금 | **없음** | `frontend/src` 에 확장보기·오버레이 상당 0건(`aria-expanded` 는 카탈로그 열 메뉴·검수 메뉴) | — |
| 6 | 뷰어 휠 확대 · 끌어 이동 · 커서 위경도 · 초기화 | **있음(3/4)** | 휠 `components/preview/useZoomPan.ts:143-153` · 끌기 `:156-178` · 초기화 `:128` ＋ `components/preview/PreviewPanels.tsx:355-357`(`기본 배율로`). ⚠ **커서 상시 위경도 표기는 없음** — 클릭 값조회(`PreviewPanels.tsx:156-172` ＋ `datasetpreview/ValueLookupPanel.tsx`)로 갈렸다 | `test/rev1-keep-regression.test.tsx:101-130` |
| 7 | 상세 미리보기 실패 문면 ＋ 지원 형식 | **있음** | 문면 `components/datasetpreview/datasetPreviewSource.ts:76`·`:89` · 형식 나열 `components/preview/PreviewPanels.tsx:118-129`(`renderableFormats`) | `test/rev1-keep-regression.test.tsx:137-159` |
| 8 | 계보 노드 이동 ＋ 원천 노드 이동 없음 | **있음** | 이동 `components/lineage/LineageSection.tsx:111-124`(`navigable` → `Link`) · 원천 `:126-135`(`div`) ＋ 문면 `:74` | `test/rev1-keep-regression.test.tsx:166-207` |
| ~~9~~ | ~~파생 행 읽기 전용~~ | — | PRD-31 ⑶ 소관 — 이 WU 범위 밖 | — |
| 10 | 접근 구역의 출처 문장 | **없음** | 문면 `업로드할 때 정한 값이에요…`·`설정 권한자` 가 `frontend/src` 에 0건 (근사 문장은 `components/lab/LabInfoPanel.tsx:216` 뿐 — 연구실 기본값 설명이라 다른 자리다) | — |
| 11 | 파일 목록 접힘 기본 ＋ 조각별 기간 없음 | **있음** | 상세 `components/detail/BasicInfoGrid.tsx:18`(`useState(false)`)·`:60-64`(`보기`/`접기`) · 조각 행에 기간 칸 없음 `components/detail/FileList.tsx:34-58` · 업로드 `components/upload/FileDropCard.tsx:57`·`:96-102` | `test/rev1-keep-regression.test.tsx:213-268` |
| 12 | 행동 줄 바닥 고정 ＋ 할 일 안내 3문면 | **없음** | `components/upload/upload.css:179-180` 의 `.reg-actions` 는 평범한 `flex`(`sticky`·`fixed` 없음) · `upload.css` 전체 `sticky` 0건 · `#ufHint` 상당 안내 0건 | — |
| 13 | 데이터셋 용량 = 조각 합계 | **있음** | 상세 `components/detail/format.ts:37-41`(`조각 N개 · 합계 …`) · 업로드 `components/upload/RegisterArea.tsx:63-65`·`:82`(`용량 (조각 합계)`) ＋ `FileDropCard.tsx:18-19`·`:93` | `test/rev1-keep-regression.test.tsx:275-296` |
| 14 | Esc 닫기 우선순위(확장보기→찾기→계보 수정→닫기 확인→업로드) | **없음** | `frontend/src` 에 `Escape`·`keydown`·`onKeyDown` 핸들러 **0건** — 전역 키 핸들러 자체가 없다 | — |

**집계 — 있음 5 / 없음 8 / 13.** `없음` 8건 = #1 #2 #3 #4 #5 #10 #12 #14.

## 2. 회귀 시험

- 파일 = `frontend/test/rev1-keep-regression.test.tsx` (신규 · 이 WU 가 유일하게 더한 코드).
- `있음` 5건에 **각 1건 이상** — 시험 케이스 총 **12건 전부 green**. 빈 집합 통과 방지로 모든 단언이 대상 건수를 먼저 잰다.
- jsdom 불가로 건너뛴 항목 **0건**. #6 의 커서 위경도는 「없음」쪽이라 시험을 걸지 않았다(green-by-skip 아님).

## 3. 게이트 — 단독만, `all` 없음

```
./gates/run.sh frontend-typecheck → green (tsc --noEmit · 오류 0건)
./gates/run.sh frontend-test      → green (vitest jsdom · 40 파일 · 619건 통과 · 실패 0건)
```
- 판정 red **0건** · 준비 red **0건**. 시험 env 는 실행 전 `~/.colab-v2-test.env` 를 로드했고, 두 게이트 모두 DB 를 쓰지 않는다.
- 워크트리 준비 — `frontend/node_modules` 를 본 트리로 심링크(gitignored · `git status` 무영향).

## 4. PLAN-SoT §9 초안 — **병합 직전에** `origin/main` 최대 ＋1 로 〈N〉 을 재실측해 넣는다

착수 시점 참고값 = 〈326〉(2026-09-05). 이 세션은 `PLAN-SoT.md` 를 고치지 않았다.

```
| 〈N〉 | **R-A-4 실측 — rev1 유지 13건 · 디자인 검수 11건 · 조각 수 표기 판정. 판정 없이 고치지 않는다** | **실측 (2026-09-05 · 워크트리 `p3-rev1-keep-audit` · 병합 `<sha>` · 계약 0 · 마이그레이션 0 · staging 접촉 0).** ①회차 = **해당 없음**(계약 미개방) ②값 = 없음 ③근거 = PRD-29·38·39 · 미결-10 (`dev-package/prd/PRD-260905-적용전기획.md`) ④가·파 판정 = 해당 없음 ⑤소비자 = 해당 없음 ⑥마이그레이션 = **0건** ⑦승인 = 불요 ⑧이번에 세지 않은 축 = `있음` 판정 항목의 수정(= R-B `WU-B11` 범위) `[미집행]`. **판정 결과** — rev1 유지 있음 **5**/13 · 디자인 결함 있음 `<n>`/11 · 조각 수 하드코드 `<n>`건 |
```

## 5. 후속으로 넘기는 것

- `없음` 8건(#1 #2 #3 #4 #5 #10 #12 #14) 이 rev1 유지 항목 중 **v2 미적용분**이다 — 후속 WU 의 범위 정의서로 쓴다.
- #6 의 **커서 위경도 상시 표기**는 부분 미적용이라 같은 목록에 붙인다(클릭 값조회는 다른 조작이다).
- 겹치는 화면(PRD-12·13·14·20·21·24·28)을 고칠 때 위 시험 파일이 방어선이다 — 지우거나 완화하지 않는다.
