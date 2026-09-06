# WU-A14 · 조각 수 표기 (PRD-38) — 실측 판정 ＋ 회귀 방어선

레인 `p3-part-count` · 기준 `origin/integration/r-a` `0e7ba01` · 프론트만 · 계약 0 · 마이그레이션 0 · staging 접촉 0.
오라클 = `dev-package/prd/rounds/R-A-4-verify.md §B-2`.

## 1. 실측 — 조각 수를 그리는 자리 전수

| # | 자리 (`path:line`) | 값의 출처 | 판정 |
|---|---|---|---|
| 1 | `frontend/src/components/detail/format.ts:41` (`조각 ${files.count}개 · 합계 ${size}`) | 응답 `DatasetBasicInfo.files.count` | 하드코드 **없음** |
| 2 | `frontend/src/components/detail/BasicInfoGrid.tsx:45` (`['파일', formatFiles(b.files, …)]`) | ①을 그대로 부른다 | 하드코드 **없음** |
| 3 | `frontend/src/components/catalog/CatalogTable.tsx:156` (`조각 {row.fileCount}`) | 응답 `DatasetRow.fileCount` | 하드코드 **없음** |
| 4 | `frontend/src/components/search/SearchHitCard.tsx:41` (`조각 {row.fileCount}`) | 응답 `SearchResultRow.fileCount` | 하드코드 **없음** |
| 5 | `frontend/src/components/project/ProjectDatasetTable.tsx:45` (`조각 {row.fileCount}`) | 응답 `ProjectDatasetRow.fileCount` | 하드코드 **없음** |

**하드코드 = 0건.** 화면 상수·`files.length`·목록 길이·목업 잔재를 쓰는 자리가 없다.

근거 셋:
- 행 타입이 전부 계약 생성물이다 — `catalog/types.ts:9` · `search/types.ts:7` · `project/types.ts:9` 가 `components['schemas']` 를 그대로 별칭한다. 화면이 모양을 다시 선언하지 않는다.
- 계약이 두 값을 **같은 정의**로 못박았다 — `frontend/src/generated/fe-core.ts:2033`(`files.count` = 본체 파일 건수, 기준 격자 제외) 과 `:2231`(`DatasetRow.fileCount` 와 같은 정의). ⟹ `d3_dataset.file_count` 한 곳.
- 상세에 **픽스처 폴백이 없다** — `frontend/src/components/detail/detailSource.ts:35-39` (`defaultDetailSource` = `apiDetailSource`). `detail/fixture.ts:78` 의 `files: { count: row.fileCount, … }` 와 `:111` 의 `count: 4` 는 **시험 시드**이고 화면 경로가 아니다.

범위 밖 1건 — `frontend/src/components/upload/FileDropCard.tsx:137,147` 의 `조각 {bodies.length}`. **등록 전** 화면이라 응답 자체가 아직 없고, 사람이 방금 고른 로컬 파일 목록이 정본이다. PRD-38 이 지적한 「등록후 표현」이 아니다.

## 2. 변경

**없다.** ⛔ 없는 결함을 고치지 않는다 (§B-2 · §3-㉴). 코드 수정 0줄.

### 문면 이견 1건 — 고치지 않고 보고한다

§B-2 의 「표기 문면 = `파일 조각 {n}개 · 합계 {용량}`」 은 **하드코드가 있을 때만** 걸리는 조건절이라 이번에 발동하지 않았다. 다만 수용 기준 첫 줄의 「조각 1개면 표기가 `파일 조각 1개`」 는 현재 코드와 다르다 — `format.ts:39` 는 조각 1건이면 `{파일명} · {용량}` 으로 세운다. 이는 정본 `Policy_데이터셋_상세 §5` 축자이고, **WU-A12 rev1 유지 #13 의 방어선**(`frontend/test/detail.test.tsx:141-146`)이 이미 지키는 성질이다. 두 요구가 충돌하므로 **판정 없이 고치지 않는다** — 회귀 시험은 수용 기준의 실질(「다른 수가 보이지 않는다」 = 지어낸 조각 수 0)로 옮겨 잡았다. 문면을 바꿀지는 R-B 로 넘긴다.

## 3. 회귀 시험 1건

`frontend/test/part-count-20260905.test.tsx` — 3 it (파일 1건).

| 시험 | 무엇을 막는가 |
|---|---|
| 조각 1개면 상세 `파일` 칸에 `조각 N` 도 `4` 도 없다 | 목업 잔재(`조각 4개`)의 부활 |
| 조각 4개면 상세 표기가 `files.count` 그대로 (`조각 4개 · 합계 148 MB`) | 상세 값의 출처가 갈리는 것 |
| 목록 칩 수 = 상세 `files.count` | 두 화면의 수가 갈리는 것 |

## 4. 게이트

| 게이트 | 결과 |
|---|---|
| `./gates/run.sh frontend-typecheck` | **green** — `tsc --noEmit` 오류 0건 |
| `./gates/run.sh frontend-test` | **green** — 47 파일 · 통과 **670** · 실패 0 (신규 3건 포함) |

`all` 은 돌리지 않았다 (§3-㉲ — 작업 중엔 단독 게이트).

## 5. `PLAN-SoT §9` 초안 — 병합 직전 `〈N〉` 재실측

```
| 〈N〉 | **R-A-4 실측 — rev1 유지 13건 · 디자인 검수 11건 · 조각 수 표기 판정. 판정 없이 고치지 않는다** | **실측 (2026-09-05 · 워크트리 `p3-part-count` · 병합 `<sha>` · 계약 0 · 마이그레이션 0 · staging 접촉 0).** ①회차 = **해당 없음**(계약 미개방) ②값 = 없음 ③근거 = PRD-29·38·39 · 미결-10 (`dev-package/prd/PRD-260905-적용전기획.md`) ④가·파 판정 = 해당 없음 ⑤소비자 = 해당 없음 ⑥마이그레이션 = **0건** ⑦승인 = 불요 ⑧이번에 세지 않은 축 = `있음` 판정 항목의 수정(= R-B `WU-B11` 범위) `[미집행]`. **판정 결과** — rev1 유지 있음 `<n>`/13 · 디자인 결함 있음 `<n>`/11 · **조각 수 하드코드 0건**(자리 5곳 전부 응답 출처 · 회귀 시험 1건 green) |
```
