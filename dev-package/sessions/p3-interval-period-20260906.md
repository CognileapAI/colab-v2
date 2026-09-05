# WU-A6 · 관측 간격 · 기간 최소 단위 · 기간 표기 (PRD-17·18·35) — 레인 `p3-interval-period`

기준 = `origin/integration/r-a-c19`(c8f209d) · 19차 묶음(A5 완 ＋ A4 완 ＋ **A6**) 중 마지막 한 건.

## 1. 바뀐 것

| 자리 | 무엇 |
|---|---|
| `db/platform/versions/0013_ra1_ext_interval_period.py` UPGRADE ⑶⑷ · DOWNGRADE ⑴⑵ | **같은 파일에 이어 적었다**(새 리비전 0). M-6 = `d3_dataset_description.observation_interval_value numeric`＋`_unit text` ＋ CHECK 둘(6값 · **둘 다 NULL 이거나 둘 다 값**) · M-7 = `d3_dataset_autometa.period_granularity text` ＋ CHECK 6값. ⛔ 백필 0. down 은 열·제약을 지우되 ⚠ M-9 와 성질이 다르다 — **사람이 고른 값**이라 다시 올려도 안 돌아온다(정규 경로는 §2-⑷) |
| `db/platform/schema.sql:378-392,437-447` | 선언 순서 **맨 뒤**(ADD COLUMN 이 뒤에 붙는다). 제약에 **이름을 박았다** — pg_dump 가 이름을 뽑아 schema-diff 가 그것으로 대조한다 |
| `db/platform/tests/0013-assertions.sql` C·D절(+122행) · `0013-drift.sh:52` | 존재 확인이 아니다 — **반쪽을 실제로 밀어 본다**(양쪽 다 거절) · 6값 전건 통과 · 6값 밖 거절 · NULL 로 비우기 · **기간 두 칸이 여전히 `timestamptz`**(시각값 저장 무변경) ／ head SQL 에 세 토큰 전부 = 한 head 임을 렌더 산출로 잰다 |
| `contracts/seams/fe-core.yaml:2302,2337,2775,2879,3138` | `DataPeriod.granularity: [string,null]`(⛔ `required` 에 안 넣는다 — 요청 몸통에도 실려 필수화하면 기존 클라이언트 전부 400) · 신설 `ObservationInterval{value,unit}` · `DatasetCreate`·`DatasetUpdate`·`DatasetBasicInfo`(＋`required`) 에 `observationInterval` · `createPreviewRender` 에 **`403` 선언 하나**(WU-A2 · 스키마·봉투 신설 0) · 생성물 재생성(등기부 명령) |
| `routes/catalog.py:582,608-616,690-703,760-786,835-849` | `_observation_interval`(Decimal→숫자 · 정수는 정수로) · 상수 `INTERVAL_UNITS`·`PERIOD_GRANULARITIES`·`HALF_INTERVAL_MESSAGE` · `validate_human_metadata` 가 **6값 둘 ＋ 반쪽 400 ＋ 0 이하 400** · `_UPDATE_FIELDS`＋1 · 상세가 `period.granularity`·`basicInfo.observationInterval` 을 내린다 |
| `routes/ingestion.py:401,414,517` · `domains/d3_catalog.py:56,85,110,131,177,206,745-757` | `_ALLOWED_CREATE_FIELDS`·`_HUMAN_METADATA_FIELDS` ＋1 (§5-㉰-4 — **계약과 같은 회차**) · 두 칸이 다 빈 객체는 「안 적었다」(⛔ 반쪽은 안 접는다 = 400) ／ `_ONE`·`_AUTOMETA` 가 세 열을 더 읽고, `update_dataset` 이 `period`→3열·`observationInterval`→2열로 가른다(`#62` 의 `KeyError` 를 두 번 배우지 않는다) |
| `detail/format.ts:12,74-148` | **조립 한 곳** — `formatPeriod`(단위별 자리 자르기 · 같은 날이면 날짜 생략) · `formatInterval` · `formatPeriodWithInterval` · `INTERVAL_MISSING_NOTICE`. ⛔ `Date` 파싱 없음(시간대가 날짜를 하루 민다) |
| `detail/BasicInfoGrid.tsx:44,66-73` · `search/SearchHitCard.tsx:9,95` | 기간 칸이 `… (10분)` · NULL 이면 「관측 간격 미기재」 한 줄 · **칸 수는 아홉 그대로**(간격은 자기 칸을 안 얻는다) ／ 목록 카드가 **같은 함수**를 쓴다 — ⚠ `SearchResultRow` 에 간격 열쇠가 없어 값이 `undefined` 이고 **규칙이 같아 괄호가 안 그려지는 것**이지 다른 규칙이 아니다 |
| `upload/periodParts.ts`(신설) · `RegisterArea.tsx:68-104,290-330,395-450` · `UploadModal.tsx:89-99,352-378` | 자리표·`partsFor`/`assemble`(비운 하위 자리 = **월·일 01 · 시·분·초 00** — `2025-00-00` 은 시각이 아니다) ／ 최소 단위 셀렉트가 **기간 입력 앞**, 고른 단위까지만 칸, **미지정이 기본**이면 종전 날짜 칸 두 개 · 관측 간격 1칸＋단위 셀렉트(placeholder rev1 축자) · **등록 미리보기 한 줄**(PRD-35 세 번째 자리) ／ 반쪽은 **그대로 보내 서버 400 을 받는다**(화면이 버리면 사용자는 적었다고 믿고 떠난다) |
| `detail/editFields.ts:27-45,61,116,150-186,210` · `DatasetEditForm.tsx` | A3 골격의 「표에 줄을 더한다」 그대로 — `periodGranularity` 는 `periodOf` 에 합류(복합 칸) · `intervalOf`/`sameInterval` 은 `periodOf`/`samePeriod` 를 본떴다 |
| 시험 파장 3건 | `test_dataset_detail.py`(아홉 칸 열쇠 집합 — **열쇠가 는 것 ≠ 칸이 는 것**) · `detail-edit.test.tsx`(칸 6→7 · 셀렉트 2 · 「R-B 가 더할 칸」 목록에서 `관측 간격` 제거 = 이제 **이 회차가 세운 칸**) · `upload.test.tsx`(`period` 에 `granularity: null`). 의미가 바뀐 자리라 **사유를 각 자리에 적었다** |

## 2. 계약 동결 해제 19차 근거 (㉰) — 이 WU 몫

⑴ `./gates/run.sh contract-breaking` **축자**
```
No breaking changes to report, but the specs are different.
Run 'oasdiff diff' to see structural differences.
contract-breaking green — 기준 HEAD (3건) 대비 파괴적 변경 없음.
```
⚠ **주장하지 않고 출력을 그대로 적는다**(§5-㉱-1). PRD-18 은 `additionalProperties: false` 스키마의 **열쇠 추가**를 파괴로 판정했는데 **oasdiff 는 그것을 파괴로 세지 않았다**(응답 열쇠 가산·요청 선택 열쇠 가산 둘 다 그 도구의 목록 밖). **이 회차를 ㉯ 로 만드는 실물 파괴 출력은 A4 몫**(`request-property-became-required` 외 4건 · `p3-summary-required-20260905.md §2`)이고 판정은 **목적 단위**로 한 회차에 한다(§5-㉰-6). ⛔ 이 green 을 「19차는 안 파괴적이다」로 읽지 않는다 — 계약을 `additionalProperties:false` 로 읽는 소비자에게는 여전히 파괴다.

⑵ 소비자 `grep -rn 'DataPeriod\|granularity' contracts/ services/ frontend/src | wc -l` → **97**

⑶ 마이그레이션 = **1 파일 · head 1개**, 그 안에 M-9·M-6·M-7 **셋**. `migration-single-head` 축자 = `# db/platform: 리비전 12건 · head 1개 (0013_ra1_ext_interval_period)` · `# db/ai: 리비전 5건 · head 1개` · `migration-single-head green — 두 체인 모두 head 1개.`

⑷ 되돌림 — **열을 지우지 않는 길이 정규 경로다.** 계약·서버·화면의 `observationInterval`·`granularity` 소비만 되돌리면 열은 남은 채 아무도 안 읽고(전 행 NULL 이라 무해) 사람이 적어 둔 값은 그대로 산다. ⚠ `downgrade` 로 열까지 지우는 것은 **값이 0 행일 때만** — M-9 와 달리 파생값이 아니다(`0007` 류). ⛔ 어느 경로에서도 `topic`·`variables`·`format` 은 안 지운다.

## 3. 시험 — RED 선실측 → GREEN

- 서버 신규 `services/core-api/tests/test_interval_period.py` **16건** — RED **10 실패 / 6 통과**(구현을 `git stash` 로 걷어낸 트리에서 실측 · 통과 6은 「계약에 없는 필드다」 400 을 우연히 만족한 음성 시험) → GREEN **16 통과**.
- FE 신규 `frontend/test/interval-period-20260906.test.tsx` **24건** — RED **17 실패 / 7 통과**(같은 방법) → GREEN **24 통과**. 덮은 것 = 미지정이면 종전 칸 두 개 · `일`→3칸 · `분`→Start/End 각 5칸 · 두 방식 비중첩 · `partsFor` 6값 전수 · 조립 3건 · 요청 몸통 형상 2건 · placeholder 축자 · 단위 셀렉트 7옵션 · **비운 채 등록 시 열쇠 미탑재** · 반쪽은 경고하되 보낸다 · 목업 축자 `2020-05-01 00:00 ~ 03:00 (10분)` · **빈 괄호 없음**(대조군 2) · granularity NULL 종전 표기 · 상세 「미기재」＋**아홉 칸 유지** · 등록 미리보기 2건.
- `db/platform/tests/0013-drift.sh` — ㈎green ㈏red ㈐red＋0011 복원 ㈑백필 green ㈑-b 대조군 red.

## 4. 게이트 (단독 · ⛔ `all` 없음 · 실행 전 `~/.colab-v2-test.env` 로드)

`contract-lint` green(seam 3 · 위반 0) · **`contract-breaking` green**(§2-⑴ 축자·단서) · `generated-up-to-date` green(등기부 4건 일치 · 자칭 생성물 0) · `migration-single-head` green(platform 12 head 1 · ai 5 head 1) · `schema-diff` green(두 체인 선언＝적용 — ⚠ 홈 `COLAB_APPLIED_DB_URL_PLATFORM` 은 다른 체인이라 **이 브랜치 체인으로 지은 일회용 DB**에 대고 쟀다 · A5 와 같은 절차) · `db-boundary` green(단위 7 · 스캔 298 · 위반 0) · `service-tests-core-api` green(수집 680 · 실행 680 · skipped 0 · deselected 6 · failed 0) · `rls-effect` green(본체 음성 · 메타 양성 P-13 · cross-tenant 전수 0행) · `frontend-typecheck` green(오류 0) · `frontend-test` green(49파일 · **715 통과** · 실패 0 / 종전 691) · `frontend-fixture-reach` green(도달 135 · 금지 모듈 0) · `work-item-consistency` green(불일치 0).

중간 red 2종 해소 — ⑴ 아홉 칸 열쇠 집합 ⑵ 파장 4건(위 표). `detail-edit.test.tsx` **부하 flaky 1건**은 단독 3회 18/18 green 으로 확인했다.

## 5. 넘길 것

**`[미상]` 없음.** 번호 충돌 주의는 A5 노트 그대로 — 병합 직전 `down_revision` 을 `main` head 로 다시 겨눈다. PRD-35 「목록 카드」는 같은 함수를 쓰되 `SearchResultRow` 에 간격 열쇠가 없어 괄호가 안 그려진다 — 그 열쇠는 이 회차가 여는 셋 밖이라 **별건**이다.

## 6. PLAN-SoT §9 초안 — 병합 직전 `origin/main` 최대 ＋1 로 `〈N〉` 재실측

```
| 〈N〉 | **R-A-1 DB 계층 — 계약 동결 해제 19차 · `DataPeriod.granularity` ＋ `file_extension` ＋ 관측 간격 2칸** | **집행 (2026-MM-DD · 워크트리 `p3-extension-label`·`p3-interval-period` · 병합 `<sha>`).** ①회차 = **19차**(직전 18차) ②값 = `DataPeriod.granularity` · `DatasetBasicInfo.fileExtension` · `observationInterval{value,unit}`(＋`createPreviewRender` 403 선언) ③근거 = PRD-17·18·21·35 (`dev-package/prd/PRD-260905-적용전기획.md`) ④가·파 판정 = **파괴** · `contract-breaking` 출력 = A6 조각은 축자 `No breaking changes to report, but the specs are different.` · **실물 파괴 출력은 A4 몫**(`request-property-became-required` 외 4건) · `DataPeriod` 의 `additionalProperties: false` 열쇠 가산은 oasdiff 가 안 센다 ⑤소비자 = `97` 건(A6 몫) · 측정법 = `grep -rn 'DataPeriod\|granularity' contracts/ services/ frontend/src` ⑥마이그레이션 = **3건 · head 1개**(M-9·M-6·M-7 · 파일 `0013_ra1_ext_interval_period`) ⑦승인 = `[승인 대기]` ⑧이번에 세지 않은 축 = `M-10` 색인 재정의(R-B 로 묶음) `[미측정]` |
```
