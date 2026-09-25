# Intent: 결측률 수치 술어를 열기 전 근거원을 정찰한다
메타 — 발의자: `2026-09-18-dataset-metadata-backfill.md` 「후속 — 별도 결정으로 분리한 항목」 2번(Ted 결정 2-ⓒ) ·
정리: Claude(researcher) · 작성 2026-09-18 · 승인 **사용자 2026-09-25**(선택지 「포함 · 린트 예외 지정」 — 판정 1~4 「권고대로」(2026-09-18) · 후속 2번 먼저 · ㈐-2 · 소수 6자리 그대로 · 계약 필드 `maxMissingRatePercent` 는 `contracts/.spectral.yaml` `colab-no-numeric-confidence` 의 이름 지정 예외)

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

## 증보 — 상시 등록·정기 갱신 관점 (2026-09-18 Ted 질의 · 위 권고를 이 절이 고친다)
전제(Ted) — 자료는 계속 등록되고, 온톨로지 기반 KG 는 하루 2~3회 정기 갱신한다.

### 코드로 확인한 사실
- 갱신 경로는 `missing_rate` 를 **이미 원본에서 직접 읽는다.** `d3_search_facts.py:45` 의 `metadata`
  source 가 `d3_dataset_variable` 을 SELECT 해 `variables` 사실로 싣고, 그 칸의 UPDATE 는
  `d3_search_change` 의 `requested_version` 을 올린다(`test_search_changes.py`
  `test_variable_quality_and_child_delete_are_metadata_changes`). 즉 KG 쪽은 등록·수정을 자동으로 따라간다.
- typed 조건 검색은 다른 자리를 읽는다. `d3_client_search.py` 는 `d3_search_evidence.facts` 를
  `JOIN LATERAL … ON true` 로 읽어, **`reviewed` 근거가 없는 데이터셋은 결과에서 통째로 빠진다.**
  데이터셋 단위 술어(`descriptionAll`·`uploadedMonth`)는 같은 함수의 `where` 목록에 이미 있다.
- `d3_search_evidence` 는 검토자가 쓰는 자리다. 이번 28건은 일회용 적용기(사용자 실행)가 썼고,
  신규 등록분에 facts 를 자동으로 싣는 경로는 없다(후속 3번 헤더 파서가 그 자리, stage2 대기).
- 입력은 `catalog.py:1085` `_VARIABLE_FIELDS` 의 `missingRate` — 형식 검증 없는 문자열이다.

### 판정별로 달라지는 점
1. **판정 1** — 권고 ㈎ 유지, 조건부 해제. 등록 필드는 이미 KG 의 근거원이다. 남는 질문은 채택 여부가
   아니라 **입력 형식**이다.
2. **판정 2** — 권고 ㈎ 유지, **목적 변경.** 28건 채움률은 시점값이라 가부를 정하지 못한다. 실측은
   「사람들이 실제로 어떤 문자열을 넣는가」를 보고 입력 검증·정규화 규칙을 정하는 용도다.
   설계트리 Q6·완료 정의 3(「비어 있으면 자료 부재로 종결」)은 **철회** — 지금 비어 있다는 것은
   등록 폼이 값을 받지 못한다는 뜻이지 앞으로도 없다는 뜻이 아니다.
3. **판정 3** — **권고를 ㈎ → ㈐ 로 바꾼다.**
   - ㈎(facts 로 전재)의 문제: 사본이 생긴다. `missing_rate` 가 고쳐져도 변경 큐는 `metadata`
     source 만 올리고 facts 사본을 다시 쓰는 주체가 없다. 신규 등록분은 검토자가 근거를 쓰기
     전까지 값이 없다. 상시 등록에서는 적용기를 매번 사람이 돌려야 한다.
   - ㈏(text 를 직접 JOIN)의 문제: 질의 시점 문자열 파싱, 형식이 제각각이면 조용히 매치 없음.
   - **㈐ 원본을 정규화하고 거기서 읽는다** — `d3_dataset_variable` 에 수치 칸(예 `missing_rate_percent
     numeric`, 0~100 CHECK)을 새 리비전으로 두고, 등록·수정 입력에서 검증해 채운다. typed 술어는
     데이터셋 단위 `where` 로 그 칸을 읽는다. KG 는 기존 `metadata` source 로 다음 정기 갱신에 자동
     반영된다. `SearchEvidenceFacts`·`Evidence.oneOf` 는 무변경, 대신 변수 입력 계약
     (`fe-core.yaml` `missingRate`)과 마이그레이션 1건이 든다.
   - ㈐ 의 반대 관점: 검토를 거치지 않은 등록자 입력이 곧바로 검색 조건이 된다(facts 는 `reviewed`
     만 읽는다). 또 typed 검색은 여전히 `reviewed` 근거가 있는 데이터셋만 돌려주므로, 근거 없는
     신규 자료는 결측률이 있어도 나오지 않는다 — 이 제약은 ㈎㈏㈐ 공통이고 후속 3번의 몫이다.
4. **판정 4** — 권고 ㈎ 유지, **기한을 붙인다.** `search_evidence_conditions.py:98` 의 문구
   「품질 검증값을 수집하지 않음」은 값이 수집·검색되기 시작하면 사실과 다른 답이 된다. 이번 회차는
   typed 만 열되, 술어가 열리는 같은 회차에 최소한 결측 질의의 문구·분기를 「품질」 묶음에서
   떼어낼지 판정한다(오차·정확도는 그대로 unknown).
5. **두 경로의 시차** — typed 검색은 등록 즉시, KG 는 다음 정기 갱신(최대 반나절) 뒤에 반영된다.
   같은 질문에 두 경로가 잠시 다르게 답하는 것은 구조상 정상이며, 검증 시나리오에 명시한다.
6. **우선순위 재고** — 상시 등록 전제에서는 신규 업로드가 `variables`·`period`·`crs`·`grid` 를
   자동으로 얻는 **후속 3번(헤더 파서)** 이 결측률 술어보다 검색 품질에 미치는 범위가 넓다.
   결측률은 헤더에 없고 사람이 넣는 값이라 3번이 대신해 주지는 않는다 — 둘은 대체가 아니라 순서의 문제다.

### 로컬 실측 (2026-09-18 · 읽기 전용 SELECT · 원격 DEV 는 미실측)
| DB | 데이터셋 | 변수 행 | `missing_rate` 채움 | `^\s*\d+(\.\d+)?\s*%?\s*$` 파싱 가능 | reviewed 근거 데이터셋 |
|---|---|---|---|---|---|
| staging `colab_platform`(`colab_v2_staging_pg`) | 15 | 22 | **0** | 0 | 1 |
| 30 개발 `colab_platform_30`(`a2_pg_30`) | 3 | 5 | **1**(`0.2%`) | 1 | 0 |

읽히는 것 — 칸은 사실상 비어 있다. 관측된 형식은 `0.2%`(개발 DB)·`20%`(테스트)·`0.2%`(계약 예시)로
전부 「숫자 + 선택적 %」다. 술어를 열어도 값이 입력되기 전에는 매치가 거의 없다 — 이 회차가 여는
것은 기능이고, 채움은 등록 쪽의 일이다.

### ㈐ 의 구현 형태 — 기존 승인 결정과의 충돌과 회피
- `contracts/seams/fe-core.yaml:4083` 은 `missingRate` 를 「자유 입력. `0.2%` 처럼 사람이 적은
  그대로」로 못 박았다(PRD-16 · WU-B2 · `VAL-006` 계열). 증보 3 의 「등록·수정 입력에서 검증」은
  이 결정을 뒤집는다.
- **㈐-1 입력 검증** — 값이 깨끗해지지만 기존 결정의 재개봉이고 등록 폼·계약 설명이 바뀐다.
- **㈐-2 generated column(채택 가정)** — text 칸과 입력 계약은 그대로 둔다. `missing_rate_percent numeric
  GENERATED ALWAYS AS (위 정규식에 맞으면 수치, 아니면 NULL) STORED` 를 새 리비전으로 더한다.
  원본에서 파생되므로 사본 동기화 주체가 필요 없고, 파싱 불가 문자열은 NULL 로 남아 술어에서
  빠질 뿐 등록을 막지 않는다. 반대 관점 — 파싱 불가 입력이 조용히 검색에서 빠진다(등록자에게
  알려 주는 표시는 이 회차 밖).
- Ted 확인 전이므로 **가정으로 진행**하고, ㈐-1 을 원하면 그 자리에서 바꾼다.

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
- Ted 확인 문장(원문 그대로): **「권고대로」(2026-09-18)** — 증보 절의 권고에 대한 답. 판정 1=㈎,
  2=㈎(실측 선행 · 목적은 형식 파악), 3=㈐, 4=㈎(기한부). 후속 2번·3번의 순서와 ㈐-2 구현 형태는
  권고가 명시되지 않았던 자리라 **에이전트 가정**(2번 먼저 · ㈐-2)이며 Ted 확인 미수령이다.
- 2026-09-25 사용자 확인: 위 에이전트 가정(2번 먼저 · ㈐-2)과 소수 6자리 제한을 그대로 승인 · 결측률 계약 필드는 숫자 확신도 금지 린트의 이름 지정 예외로 둔다(검색 조건이지 확신도가 아니다).
- 프론티어 공집합 확인: 미수행.
- 재개봉 금지: 아니오 — 기존 판정을 뒤집지 않는다. `2026-09-18-dataset-metadata-backfill.md`
  결정 2-ⓒ(별도 결정으로 분리)를 그대로 잇는다.

## 구현 결과 (2026-09-18 · 브랜치 `codex/ai-search-missing-rate-predicate`)
판정 1=㈎ · 2=㈎ · 3=㈐-2 · 4=㈎ 대로 구현했다. 아래는 전부 이 체크아웃의 실측이다.

### red → green
| 오라클 | red | green |
|---|---|---|
| core-api pytest(신규 `test_search_missing_rate.py` ＋ `test_practitioner_conditions.py`) | 13 failed / 13 passed | 0 failed |
| `db/platform/tests/0043-drift.sh` | exit 1 (`alembic 렌더 실패: upgrade 0043_variable_missing_rate`) | exit 0 |

### 게이트 (선언 7 + 프론트 2)
| 게이트 | 종료코드 | 실측 |
|---|---|---|
| `service-tests-core-api` | 0 | 수집 1726 · 실행 1726 · failed 0 · errors 0 · skipped 0 · deselected 6 · 160.8초 |
| `generated-up-to-date` | 0 | 등기부 20건 재생성 일치 · 등기부 밖 자칭 생성물 0건 |
| `seam-consistency` | 0 | G-e 543 · G-b 10 · ㉠ 0 · ㉡ 18 |
| `schema-diff` | 0 | 두 체인 각각 `upgrade head` 뒤 선언 = 적용 |
| `migration-drift` | 0 | 오라클 33 · 실행 33 · 실패 0 · 준비 실패 0 (platform 선언 27→28) |
| `rls-coverage` | 0 | `d3_dataset_variable` rls=on force=on 정책=2 — 생성 컬럼이 새 정책을 만들지 않았다 |
| `contract-breaking` | 0 | 기준 HEAD 3건 대비 파괴적 변경 0 |
| `frontend-typecheck` | 0 | `tsc --noEmit` 오류 0 |
| `frontend-test` | 0 | vitest 1563 통과 / 0 실패 (128 파일) |

구 체인 오라클 `db/platform/tests/0042-drift.sh` 는 **exit 0** 이다. head 를 `alembic heads` 로
읽으므로 박힌 값이 없고, 이번 회차가 그 스크립트를 고치지 않았다.

### 실물
- 리비전 `0043_variable_missing_rate`(`0042_reconcile_admin_access` 위) —
  `d3_dataset_variable.missing_rate_percent numeric GENERATED ALWAYS AS (…) STORED`.
  downgrade 는 칸을 지우며 0042 shape 복원의 pg_dump 차이가 0줄이다.
  ⚠ 리비전 id 는 26자다 — `alembic_version_platform.version_num` 이 varchar(32) 라
  처음 쓴 `0043_variable_missing_rate_percent`(34자)는 적용 시점에 터졌다.
  ⚠ 선언 `schema.sql` 에서 새 칸의 자리는 **표 마지막**이다. `ADD COLUMN` 이 뒤에 붙으므로
  위로 올리면 선언과 적용의 pg_dump 가 열 순서에서 갈린다(첫 시도에서 실제로 갈렸다).
  ⚠ 조건식은 중첩 CASE 다. `~ … AND …::numeric` 는 AND 두 항의 계산 순서가 보장되지 않아
  `'낮음'::numeric` 가 터진다.
- `d3_client_search.candidates` 의 `where` 에 `maxMissingRatePercent` — 대표 변수 EXISTS.
  인자는 0~100 의 수만 받으며 그 밖은 `ValueError('maxMissingRatePercent must be a number in 0..100')` 다.
- `client_search`: `validate_context` allowlist ＋ 0~100 밖 400, `_predicate` 가 facts 가 아니라
  후보 줄의 `missing_rate_percent` 를 읽는다(그래서 `candidates` 가 그 값을 함께 싣는다).
- 계약: `SearchContext.research.maxMissingRatePercent`(number · 0~100) ＋ `fe-core.ts` 재생성 1줄.
  `SearchAssessment.tsx` 는 `conditionLabels` 만 더했다.

### 이 문서와 다르게 확인된 것
- 「영향 범위」가 예고한 `SearchEvidenceFacts` 신규 필드와 `Evidence.oneOf` 15종→16종은
  **일어나지 않았다.** 판정 3 이 ㈎ 에서 ㈐ 로 바뀐 결과이고, 두 파일은 무변경이다.
  `dataset_evidence_backfill.py`/`_apply.py` 도 무변경이다 — 파생에는 적용기가 필요 없다.
- 「완료 정의 2」가 말한 「세 사례의 red 오라클」은 `expectSeq` 가 아니라 `expectEmpty` 로만
  세울 수 있었다. `test_practitioner_conditions.py` 의 DEV 재현 픽스처는 `d3_dataset_variable`
  행을 아예 심지 않고, 정본 856행에 결측률이 0건이라 심을 근거도 없다. 세 사례의 `mode` 는
  바꾸지 않았고 `deferred` 문면만 사실에 맞게 고쳤다.
- `maxResolutionM` 은 `eval/k4-search/measure_evidence.py` 의 측정 조건 목록에도 있으나
  결측률은 더하지 않았다 — 값이 0건이라 측정 수치가 0으로 고정되고, 그 파일은 술어 집합의
  선언이 아니라 측정 도구다.

### 후속 수정 — 생성식 정규식을 좁혔다 (2026-09-18 · 같은 브랜치)
- **결함**: 위 정규식(intent 축자 `\d+`)은 자유 입력 칸의 **등록을 막았다** — 이 회차가 세운
  「파싱 불가는 오류가 아니라 NULL」의 정반대다. `missing_rate` 에는 길이 상한이 없다
  (`catalog.py:1114-1116` 의 검사는 「문자열이거나 null」까지이고 DB 에도 CHECK 가 없다).
  로컬 postgres:16 · postgres:16-alpine(둘 다 16.15) 실측 — `repeat('9',140000)` 과
  `'0.'||repeat('9',20000)` 은 numeric 한계(정수부 131072 · 소수부 16383)를 넘어
  `value overflows numeric format`, ICU collation 판의 전각 숫자 `'５%'`(U+FF15)는
  locale 의존 클래스인 `\d` 가 잡아 `invalid input syntax for type numeric: "５"` 로
  INSERT 가 죽었다. libc collation(공식 이미지 기본)에서는 안 잡혀 판마다 결론이 갈린다.
- **수정**: 리비전과 `schema.sql` 을 같은 값으로 고쳤다 —
  `^\s*([0-9]{1,3}(?:\.[0-9]{1,6})?)\s*%?\s*$`. ASCII 명시 ＋ 자릿수 묶음.
  0044 를 더하지 않았다(지속 제품 DB 미적용이라 제자리 수정이 맞다). 기존 기대 불변:
  `'0.2%'`→0.2 · `' 20 % '`→20 · `'100'`→100 · `'101'`→NULL · `'낮음'`→NULL.
  ⚠ **묶은 자릿수 밖은 값이 아니라 NULL 이 된다** — `'0.1234567'` 이 종전 0.1234567 에서
  NULL 로 바뀐다. 소수 6자리는 이 회차의 선택이고, 넘침만 막는 것이 목적이면 `{1,15}` 로도
  된다(numeric 소수부 한계 16383). 값을 되찾아야 하면 그 자리에서 넓히면 된다.
- **red → green**: `0043-drift.sh` exit 1(㈎ `value overflows numeric format`) → exit 0 ·
  `service-tests-core-api` failed 2(`overflow-int`·`overflow-frac`) → failed 0(수집·실행 1730).
  오라클은 행동(`0043-assertions.sql` ②-h~m)과 식(⑥)을 따로 잰다 — 기본 collation 이 libc 인
  판에서는 행동만으로 locale 의존이 드러나지 않는다. ⑥ 은 정규식을 다시 적지 않고
  살아 있는 `generation_expression` 에서 꺼내 ICU collation 아래에서 돌린다.
- ⚠ **공유 게이트 픽스처**: 이 PC 의 `schema-diff` 적용 DB(`colab_platform_applied`)에는
  0043 이 이미 **구 정규식으로 적용돼 있었다**. `alembic upgrade head` 는 리비전이 이미
  기록돼 있으면 제자리 수정을 반영하지 않으므로 그 DB 를 0042 로 내렸다가 다시 올려 맞췄다.
  제자리로 고친 리비전은 이 손질이 따라붙는다.

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
