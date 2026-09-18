# Intent: 결측률 수치 술어를 열기 전 근거원을 정찰한다
메타 — 발의자: `2026-09-18-dataset-metadata-backfill.md` 「후속 — 별도 결정으로 분리한 항목」 2번(Ted 결정 2-ⓒ) ·
정리: Claude(researcher) · 작성 2026-09-18 · 승인 미승인

## 문제
- 실무자 사례 3건(`#2-7`·`#1-1`·`#2-1`)이 결측률을 요구한다. `eval/k4-search/practitioner-conditions.json` 축자 —
  `#2-7` 은 이미 `mode:"full"` 이지만 「결측치가 가장 적은」 순위 질문 자체는 `deferred` 로 남았고,
  `#1-1`·`#2-1` 은 `mode:"partial"` 로 결측 여부가 `deferred` 항목 중 하나다.
- `d3_client_search.py::candidates`(`services/core-api/src/colab_core/domains/d3_client_search.py:60-64`)에
  결측률 술어가 없다 — `key` 가 매치되지 않으면 `raise ValueError('unsupported typed predicate')` 다.
- `d3_dataset_variable.missing_rate` 는 `text`(`db/platform/schema.sql:648`, CHECK 없음)이고, 실제 값은
  `'20%'`(`services/core-api/tests/test_search_changes.py:76`) 같은 자유 문면이다.
- `services/core-api/src/colab_core/app/search_evidence_conditions.py:35,98`은 「품질」(결측 포함) 조건을
  질의에서 감지하면 **항상** `('unknown','품질 검증값을 수집하지 않음')` 을 반환하도록 의도적으로 고정했고,
  `services/core-api/tests/test_search_numeric_quality.py` 골든 4개가 「품질 수치 질의는 후보를 넓히지
  않는다」를 못 박는다. 이것은 버그가 아니라 **결측률 실체가 없던 시절의 안전장치**다.
- ⭑ **신규 확인(이 정찰의 결과)** — `dev-package/reports/reference-data/datasets-md/**/DATASETS.md`
  4개 파일 856행 전수를 `%`·`결측`·`누락`·`gap`·`NA` 로 grep 하면 **0건**이다. 즉 28건의 정본 문서 자체에는
  결측률 수치가 **한 글자도 없다** — 결측률의 유일한 후보 근거원은 정본이 아니라 DEV 에 이미 등록돼
  있을 `d3_dataset_variable.missing_rate` 뿐이고, 그 값이 실제로 몇 건이나 채워져 있는지, 파싱 가능한
  형식인지는 이 정찰에서 **DEV 를 읽지 않아 미실측**이다.

## 원한 결과 (proposed outcome)
- O1. `d3_dataset_variable.missing_rate` 가 DEV 28건 중 몇 건에 값이 있고, 그중 몇 건이 수치로 파싱
  가능한 형식(`'20%'`류)인지 **실측**한다. 실측 없이 스키마·술어를 먼저 열지 않는다.
- O2. 실측이 「쓸 만하다」로 나오면, `maxResolutionM`(`nativeResolutionM` 의 CASE 패턴,
  `d3_client_search.py:46-47`)과 같은 방식으로 **마이그레이션 없이** `missingRatePercent` 술어를 여는
  설계를 확정한다. 실측이 「쓸 게 없다」로 나오면 이 후속 항목은 종결하고 남겨 적는다.
- O3. `SearchEvidenceFacts`·`Evidence.oneOf`·생성물·편집기·NL 해석 경로 중 **무엇을 바꾸고 무엇을
  그대로 둘지**가 Ted 판정으로 남는다 — 특히 `search_evidence_conditions.py` 의 「품질=항상 unknown」
  정책을 typed 조건 검색과 분리 유지할지 여부.
- O4. 이 회차도 이전 회차와 같이 **DEV 자료를 고치지 않는다.** 실측은 읽기 전용 질의로 한다.

## 영향 범위
- 사용자 / 화면: 이 회차(정찰) 는 화면 변화 없음. 뒤따르는 구현 회차(승인 시)가 상세 화면의
  `SearchEvidenceEditor` 에 결측률 표시를 더할 수 있다 — 그 회차의 몫.
- 서비스 · 스키마 · 계약: 이 회차는 **무변경**. 뒤따르는 구현 회차는 최소 다음을 건드린다 —
  `contracts/seams/fe-core.yaml` `SearchEvidenceFacts`(신규 필드), `contracts/schemas/knowledge-lifecycle.json`
  의 `Evidence.oneOf`(15종→16종), `d3_client_search.py`(신규 predicate 분기), `fe-core.ts`·core/ai
  `knowledge_wire.py`(재생성), `dev-package/tools/dataset_evidence_backfill.py`/`_apply.py`(신규 성분).
- 계약 파괴 여부: 이 회차 — 아니오(계약 무변경). 뒤따르는 구현 회차 — enum 확장이 아니라 **신규
  필드 추가**이므로 원칙적으로 breaking 아님(추가 전용), 단 실제 판정은 그 회차의 `contract-breaking`
  게이트가 낸다.

## 제약
- 「정본에 없으면 만들지 않는다」(`PLAN-SoT §9-㊴-②`) — 정본 문서(datasets-md)에는 결측률이 전혀
  없으므로, `d3_dataset_variable.missing_rate` 를 근거원으로 쓰는 것이 이 원칙과 같은 급인지
  Ted 판정이 필요하다(판정 필요 1).
- DEV 자료·설정·배포를 변경하지 않는다. 이 회차는 실측조차 **읽기 전용**으로 한다.
- 모델 호출 0회.
- `search_evidence_conditions.py`·`test_search_numeric_quality.py` 는 결측 질의가 후보를 부풀리지
  않도록 만든 **의도적** 안전장치다 — 이 회차의 실측·설계가 그 정책을 뒤집자는 제안이 아니다.

## 설계트리 (grill-me 결과)
- Q1 결측률의 근거원을 정본 문서로 삼는가 → A **아니다.** 정본 문서 856행 전수에 결측률 문구가
  0건이다(datasets-md 전수 grep). 유일한 후보는 `d3_dataset_variable.missing_rate` 뿐이다
  (반대 관점 없음 — 실측으로 반박 가능한 사실 진술)
- Q2 그 필드를 근거원으로 채택하는가 → A **판정 보류.** DB 를 읽지 않아 실측이 없다(판정 필요 2)
- Q3 성분을 어디에 싣는가 → A **후보 ㈎ `SearchEvidenceFacts.missingRatePercent`(파일 단위 사실로
  대표 변수 값을 전재 — `cadence`·`period` 와 같은 데이터셋→파일 스탬프 패턴 재사용).** 후보 ㈏
  `d3_client_search.py` 가 `d3_dataset_variable` 을 직접 JOIN(계약·생성물 무변경이나 typed predicate
  신뢰축이 facts 밖에 하나 더 생긴다) (판정 필요 3)
- Q4 술어 형태는 무엇인가 → A **`maxMissingRatePercent`, `nativeResolutionM`/`maxResolutionM`
  선례(`d3_client_search.py:46-47`)와 같은 CASE 비교.** 결측치가 「가장 적은」 질문은 상한 비교 하나로
  충분하다 — 범위 술어(이상·이하 쌍)는 이 세 사례 어디도 요구하지 않는다 (권장안, 반대 관점:
  향후 「결측률 5% 이상만 제외」류 하한 질의가 나오면 다시 열어야 한다 — 지금은 YAGNI 로 접는다)
- Q5 NL/리터럴 해석 경로(`search_evidence_conditions.py`)도 갱신하는가 → A **후보 ㈎ 유지 —
  typed 조건 검색에만 새 술어를 열고, NL 의 「품질=unknown」 골든은 그대로 둔다.** 후보 ㈏ NL 도
  갱신해 실측값을 답하게 한다(골든 4개 재작성 필요, 대화 기능 축과 섞인다) (판정 필요 4)
- Q6 실측이 비어 있으면(값이 거의 없거나 파싱 불가) 어떻게 하는가 → A **이 후속 항목을 종결하고
  「자료 부재」류로 남긴다** — 후속 5번(AWS·disdrometer·CCTV)·1번(pressure level)과 같은 급의
  기다림 항목이 된다 (권장안 수용)

## 완료 정의
1. `d3_dataset_variable.missing_rate` 실측 쿼리(읽기 전용, DEV 또는 그 사본)의 결과 — 28건 중
   값이 있는 건수, 그중 `\d+(\.\d+)?%` 류로 정규식 파싱 가능한 건수, 대표 변수(`is_representative`)
   기준인지 여부 — 가 문서로 남는다. ⭑ 현재 상태 — **미실측**(이 정찰은 DB 를 읽지 않았다).
2. 실측이 「쓸 만하다」(파싱 가능 건수가 실무자 사례를 채울 만큼)로 나오면, 다음 회차의
   red 오라클이 정의된다 — `eval/k4-search/practitioner-conditions.json` 의 `PC-2-7`·`PC-1-1`·
   `PC-2-1` 세 케이스에 `maxMissingRatePercent` 프로브를 추가하고, 적재 전 상태에서 **red** 임을
   증명한다.
3. 실측이 「쓸 게 없다」로 나오면, 이 항목은 `2026-09-18-dataset-metadata-backfill.md` 「후속」
   목록에 **판정 종결**(자료 부재, 코드로 못 고침)로 되돌려 적고 이 intent 는 그 판정만으로 닫힌다.
4. Ted 가 판정 필요 1~4 를 확인한다 — 그 전까지 구현 회차(계약 개정)는 시작하지 않는다.

### 완료 주장 전 green 이어야 하는 게이트
| 게이트 | 왜 |
|---|---|
| (이 회차는 코드·계약 무변경이라 게이트 없음) | 정찰·판정 문서이며 구현은 후속 회차의 몫 |

뒤따르는 구현 회차가 서면 최소 다음이 필요하다(이 intent 의 완료 조건이 아니라 예고):
`service-tests-core-api`(신규 predicate·NL 회귀) · `generated-up-to-date`(`fe-core.ts`·`knowledge_wire.py`) ·
`seam-consistency` · `contract-breaking`(필드 추가가 파괴 아님의 증명) · `schema-diff`(변경 여부에 따라).

종료코드 — green **0** · 판정 실패 **1** · 준비 실패 **78**. 준비 실패를 성공으로 보고하지 않는다.

## 판정 필요 항목 (Ted)
1. **근거원 채택 여부** — ㈎ `d3_dataset_variable.missing_rate`(DEV 등록 필드, free text, CHECK 없음)를
   결측률 술어의 근거원으로 채택한다. ㈏ 채택하지 않는다(정본 문서에 값이 없다는 이유로 이 후속
   항목 전체를 「자료 부재」로 접는다). **권장 ㈎ — 단, 실측(판정 필요 2) 전에는 가결이 아니라
   조건부다.**
2. **실측 선행 여부** — ㈎ DEV(또는 DEV 스냅숏)를 읽기 전용으로 질의해 값 채움률·파싱 가능률을
   먼저 재고, 그 결과로 판정 필요 1·3·4 를 다시 연다. ㈏ 실측 없이 스키마부터 연다(값이 없으면
   빈 칸으로 두는 기존 관례를 그대로 믿는다). **권장 ㈎ — free text 필드는 형식 CHECK 가 없어
   파싱 실패율을 모르면 술어 자체가 조용히 대부분 「매치 없음」이 될 위험이 있다.**
3. **성분이 실리는 자리** — ㈎ `SearchEvidenceFacts.missingRatePercent` 신규 필드(데이터셋 대표
   변수 값을 파일 단위로 전재). ㈏ `d3_client_search.py` 가 `d3_dataset_variable` 을 직접 JOIN(계약
   무변경). **권장 ㈎ — 2026-09-18 intent Q1 이 「조건 검색이 읽는 자리는 facts 하나」로 이미
   정리한 축과 일치시킨다. ㈏ 는 typed predicate 신뢰축을 facts 밖에 하나 더 만든다.**
4. **NL/리터럴 해석 경로 처리** — ㈎ typed 조건 검색에만 새 술어를 열고 `search_evidence_conditions.py`
   의 「품질=항상 unknown」 정책·골든 4개는 그대로 둔다. ㈏ NL 도 실측값을 반영하도록 갱신한다(골든
   재작성). **권장 ㈎ — 이번 후속의 범위를 좁혀 대화 기능 축(2026-09-18 intent 가 이미 분리해 둔
   「내 연구」 맥락 등)과 섞지 않는다.**

## 미해결 질문
- `d3_dataset_variable.missing_rate` 의 DEV 실측치(값 채움률·형식) — 이 정찰이 직접 잰 것이 아니다.
- `PC-2-7`(이미 `mode:"full"`)에 결측률 술어를 더하면 **모드가 바뀌지는 않고** 순위·설명 품질만
  좋아진다 — 오라클 스키마가 「순위」를 판정 대상으로 다루는지(`expectedCount`·`probes` 확장) 별도
  설계가 필요하다.
- `PC-1-1`·`PC-2-1` 은 결측률 외에도 변수 사전 미개방(온톨로지 intent 결정 7)·「내 연구」 맥락 등
  다른 `deferred` 항목이 남아 있어, 결측률 하나를 열어도 두 사례는 여전히 `mode:"partial"` 로
  남을 가능성이 높다 — 「green 전환」을 과장하지 않는다.

## 범위 밖 (명시 제외)
- 계약 개정, 코드 변경, DB 마이그레이션, DEV 쓰기 — 전부 이 정찰의 판정이 선 **다음** 회차의 몫.
- pressure level(후속 1번, Ted 결정 2-ⓑ) — 별도 intent. 참고로 이 정찰과 같은 방식으로 정본
  856행을 `hPa`·`기압면`·`pressure level`·`ERA5` 로 grep 한 결과도 **0건**이었고(`ERA5` 만 예외 —
  `plan-manifest.yaml:237` 의 `surface (ERA5 GRIB 원자료)` 뿐, pressure-level 산출물은 28건에 없다),
  스키마를 열어도 `PC-2-6` 이 green 으로 바뀌지 않는다는 `practitioner-conditions.json` 자체의
  `reason` 필드와 일치한다.
- `d3_dataset_variable.missing_rate` 를 `text`→`numeric` 으로 바꾸는 마이그레이션 — 판정 필요 3 이
  ㈎ 로 가면(파일 단위 전재) 필요 없어진다. ㈏ 로 가면 다시 열릴 수 있는 질문이다.

## 확인
- Ted 확인: **미수령**
- 프론티어 공집합 확인: 미수행.
- 재개봉 금지: 아니오 — 기존 판정을 뒤집지 않는다. `2026-09-18-dataset-metadata-backfill.md`
  결정 2-ⓒ(별도 결정으로 분리)를 그대로 잇는다.

## 참조
- 선행 intent: `dev-package/intent/2026-09-18-dataset-metadata-backfill.md` 「후속 — 별도 결정으로
  분리한 항목」 2번
- 오라클: `eval/k4-search/practitioner-conditions.json`(`PC-2-7`·`PC-1-1`·`PC-2-1`) ·
  `services/core-api/tests/test_practitioner_conditions.py`
- 코드: `services/core-api/src/colab_core/domains/d3_client_search.py:14-65`(predicate 분기,
  `maxResolutionM` 선례는 46-47행) · `services/core-api/src/colab_core/app/search_evidence_conditions.py`
  (`criteria['quality']` 35·98행) · `services/core-api/tests/test_search_numeric_quality.py`(골든)
- 스키마: `db/platform/schema.sql:648`(`d3_dataset_variable.missing_rate text`)
- 정본 grep 근거: `dev-package/reports/reference-data/datasets-md/**/DATASETS.md`(4파일 856행,
  `%`·`결측`·`누락`·`gap`·`NA`·`hPa`·`기압면` 전수 0건)
- 계약: `contracts/seams/fe-core.yaml` `SearchEvidenceFacts` · `contracts/schemas/knowledge-lifecycle.json`
  `Evidence.oneOf`
- spec: 미작성.
