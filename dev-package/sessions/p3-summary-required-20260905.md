# WU-A4 · 설명 필수 ＋ 레이아웃 (PRD-15 · PRD-28) — 레인 `p3-summary-required`

기준 = `origin/integration/r-a-c19`(cf55920) · 19차 묶음(A5 완 ＋ **A4** ＋ A6) 중 A4 한 건.
**DB 변경 0 · 마이그레이션 0** — `NOT NULL` 금지·일괄 채우기 금지(미결-5 ⓐ).

## 1. 바뀐 것

| 자리 | 무엇 |
|---|---|
| `contracts/seams/fe-core.yaml:2744,2758,2828` | `DatasetCreate.required = [uploadId, name, summary]` · `DatasetCreate.summary` = `string · minLength 1`(종전 `[string,"null"]`) · `DatasetUpdate.summary` 동일(**열쇠가 오면 비울 수 없다**) |
| `routes/catalog.py:593,598,601` | 문구·판정을 **한 자리에** — `EMPTY_SUMMARY_MESSAGE`「설명을 적어 주세요.」 · `BLANK_SUMMARY_ON_UPDATE_MESSAGE`「설명이 아직 없어요 — 수정에서 채워 주세요.」 · `is_blank_summary`(`strip` 후 길이 — `d3_dataset_description.name` CHECK 와 같은 모양) |
| `routes/ingestion.py:33,505,560` | `createDataset` 가 공백만 있는 설명을 **400** · 저장은 `strip()` 값(검사한 값 ≠ 저장한 값을 만들지 않는다). 생성물 `frontend/src/generated/fe-core.ts` 재생성(`openapi-typescript` 7.13.0 · 등기부 명령 그대로) |
| `routes/catalog.py:723-730` | `updateDataset` 두 갈래 — ⑴ 열쇠가 오면 공백·`null` 400 ⑵ **열쇠가 없고 저장값이 비었으면** 400(미결-5 ⓐ 「그 행을 수정할 때 채우게 한다」). 빈 몸통 `{}` 은 수정이 아니라 400 이 아니다. ⚠ ⑵ 는 저장값을 봐야 해 **계약이 못 내는 판정**이다 |
| `upload/RegisterArea.tsx:194,237-249` | **`form-3` 한 줄 3칸**(기간 = 한 셀 안 `시작~끝` · 좌표계 · 격자 — `격자` 가 자동 줄에서 내려와 그 줄도 2칸으로 찬다) ／ 설명 = `필수` 배지 ＋ `textarea rows=3` · **아래 안내 문구 없음**(rev1 이 없앴다) · 빈 채 제출하면 `reg-summary-error` |
| `upload/UploadModal.tsx:96,344,413-434` | `summaryError` 상태 ／ 제출 전 판정 → ① 로 되돌리고 초점 이동 ／ **`up-split` 두 칸**(`up-split-preview` ｜ `up-split-form`, 등록 카드가 그 안 아래) ／ `summary: summary.trim()`(`null` 아님) |
| `upload/upload.css:57,71-79,200-220` | 본문 `max-width` 960 → **1232px**(수용 기준이 1280px 폭) · `.up-split {2fr 3fr}` · `.form-3 {repeat(3, minmax(0,1fr))}` · `.reqtag` · `textarea.inp` |
| `detail/DetailHeader.tsx:25,54` · `detail.css:40,136` · `editFields.ts:44,118` · `DatasetEditForm.tsx:57` | `EMPTY_SUMMARY_NOTICE` ＋ `dh-sum-empty` — 설명이 비면 안내 한 줄, 있으면 종전 본문(**둘 중 하나만**) ／ `summary.required = true`(배지) ／ `toPatch` 는 설명을 **빈 문자열로 보낸다**(`null` 을 계약이 닫았다) ／ `draftError` 는 이름만 본다 — **화면이 서버 판정을 흉내 내지 않는다**(400 을 그대로 올린다) |
| `frontend/vite.config.ts:34` | `upload.css?raw` 를 css 스텁 예외에 넣었다 — 비율을 **규칙 원문**으로 재려면 원문이 실려야 한다(`node:fs` 는 쓰지 않는다 · 집 관례) |
| 시험 파장 | 서버 12파일·FE `upload.test.tsx` 의 `createDataset` 호출부에 설명을 채웠다(필수화의 직접 파장). `test_dataset_update.py` 3건은 **의미가 바뀐 자리**라 사유를 적고 고쳤다 — 「`null` 로 비운다」 규칙은 `sourceLabel` 로 옮겨 잰다(규칙이 없어진 게 아니라 적용 칸이 줄었다) |

## 2. 계약 동결 해제 19차 근거 (㉰)

⑴ `./gates/run.sh contract-breaking` **축자**
```
error [request-property-became-not-nullable]  in API POST /datasets — the request property `summary` became not nullable
error [request-property-became-required]      in API POST /datasets — the request property `summary` became required
error [request-property-min-length-increased] in API POST /datasets — the `summary` request property's minLength was increased from `0` to `1`
error [request-property-became-not-nullable]  in API PATCH /datasets/{datasetId} — the request property `summary` became not nullable
error [request-property-min-length-increased] in API PATCH /datasets/{datasetId} — the `summary` request property's minLength was increased from `0` to `1`
::error::contract-breaking red — 기준(HEAD) 대비 파괴적 변경이 있다 (oasdiff exit 1).
```
→ **이 red 는 판정 red 가 아니라 증거다**(§5-㉱-1) — 등급 ㉯ 를 만드는 파괴(**요청 필수 칸 신설**)가 여기 실물로 있다. A5 조각은 「가」였고 판정은 **목적 단위**로 한 회차에 한다.

⑵ 소비자 `grep -rn 'DatasetCreate\|summary' contracts/ services/ frontend/src | wc -l` → **286** ⑶ 마이그레이션 = **0건**(이 WU) · 묶음 누계 **1 파일 · head 1개**(A5 의 `0013_ra1_ext_interval_period` = M-9)
⑷ 되돌림 — **데이터를 안 건드려 코드 되돌림이 전부다.** 계약의 `required += summary` 와 두 `minLength`, `ingestion.py` 400 검사, `catalog.py` 두 갈래를 지우면 끝. **DB 는 종전 그대로 nullable · 채운 행 0** — 이 회차가 만든 값은 그 뒤 새로 등록된 행의 설명뿐이고 그것은 사람이 적은 값이다.

## 3. 시험 — RED 선실측 → GREEN

- 서버 신규 `services/core-api/tests/test_summary_required.py` **10건** — RED **6 실패 / 4 통과**(구현을 `git stash` 로 걷어낸 트리에서 실측) → GREEN **10 통과**.
  덮은 것 = 열쇠 없음·`null`·공백 3칸 400 · 정상 201＋trim · 빈 행 상세 200 · **빈 행이 DB 에서 백필되지 않음** · 빈 행을 이름만 고치면 400 · 채우면 200 · 있는 설명을 비울 수 없음 · **빈 몸통은 400 이 아님**(400 남발 방지).
- FE 신규 `frontend/test/summary-required-20260905.test.tsx` **11건** — RED **9 실패 / 2 통과** → GREEN **11 통과**.
  덮은 것 = 배지·`(선택)` 소거 · `TEXTAREA rows=3` · 칸 아래 문단 0개 · 빈 설명 제출 차단 · `dh-sum-empty` 문면 축자 ＋ 헤더 무손상 ＋ **대조군**(설명 있으면 안내 없음) · `up-split` 두 칸 ＋ `.up-split`=`2fr 3fr` · `reg-short-row` 3칸 ＋ 기간 두 칸이 그 안 · `.form-3`=`repeat(3, minmax(0, 1fr))` · 자동 줄 2칸.
  ⚠ **jsdom 은 폭을 못 잰다** — 비율은 **선언**(클래스 ＋ CSS 원문)으로 잰다. 그 한계를 파일 머리에 적었다.

## 4. 게이트 (단독 · `all` 없음)

`contract-lint` green(seam 3건 · 위반 0) · **`contract-breaking` red = 위 축자(19차 ㉯ 증거이지 결함이 아니다)** · `generated-up-to-date` green(등기부 4건 일치 · 자칭 생성물 0) · `service-tests-core-api` green(수집 664 · 실행 664 · skipped 0 · deselected 6 · failed 0) · `rls-effect` green(본체 음성 · 메타 양성 P-13 · cross-tenant 전수 0행) · `frontend-typecheck` green(오류 0) · `frontend-test` green(48파일 · 691 통과 · 실패 0 / 종전 680) · `frontend-fixture-reach` green(도달 134 · 금지 모듈 0건).

중간 red 2종을 해소했다 — ⑴ `upload.css?raw` 가 vitest css 스텁에 걸려 빈 문자열이었다(설정에 예외 추가) · ⑵ `detail-edit.test.tsx` 1건 **부하 flaky**(실패 시험명이 회차마다 달랐고 단독 재실행 18/18 green). 실행 전 `~/.colab-v2-test.env` 로드. 준비 = `.venv` 신설 · `frontend/node_modules` 심링크(gitignored).

## 5. PLAN-SoT §9 초안 — 병합 직전 `origin/main` 최대 ＋1 로 `〈N〉` 재실측

```
| 〈N〉 | **R-A-2 계약·서버·FE — 설명 필수 400 ＋ 등록 화면 2:3 · 짧은 값 3칸** | **집행 (2026-MM-DD · 워크트리 `p3-summary-required` · 병합 `<sha>`).** ①회차 = **19차**(WU-A4 분 · 직전 18차) ②값 = `DatasetCreate.required += summary` · `DatasetCreate.summary minLength 1` · `DatasetUpdate.summary minLength 1`(null 불가) ③근거 = PRD-15·28 (`dev-package/prd/PRD-260905-적용전기획.md`) ④가·파 판정 = **파괴**(요청 필수 칸 신설) · `contract-breaking` 출력 = `request-property-became-required` · `request-property-became-not-nullable` · `request-property-min-length-increased 0→1`(POST /datasets · PATCH /datasets/{datasetId}) ⑤소비자 = `286` 건 · 측정법 = `grep -rn 'DatasetCreate\|summary' contracts/ services/ frontend/src` ⑥마이그레이션 = **0건**(이 WU · 묶음 누계 1파일 head 1개) ⑦승인 = `[승인 대기]` ⑧이번에 세지 않은 축 = 설명이 빈 기존 행의 실제 건수(staging 접촉 0 · 읽기도 0) `[미측정]` |
```
