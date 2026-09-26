# Intent: 「시간해상도 1시간 이하」를 주기(산출 간격) 순서로 거른다 — 조건 검색 두 경로의 주기 상한 술어
메타 — 발의자: Ted · 작성 2026-09-26 · 승인 2026-09-26 (Ted, 진행 순서 권고안 채택 · 원문 「권고안대로핡」) · 선행 intent `dev-package/intent/2026-09-26-region-containment-expansion.md` 「완료 정의 ⑥」(「「1시간 이하」 범위 술어가 없다(cadence는 등호 비교만 한다)」) · 조사 기준 트리 develop `677b60ef`(PR #175 병합본 — 아래 줄번호는 이 트리 기준)

## 문제
- 실무자 두 사례가 「시간해상도 1시간 이하」를 직접 묻는다 — PC-1-4(사례 제공자 #1) 「시간해상도 1시간 이하이고 공간해상도가 가장 높은 강수자료」 · PC-2-4(사례 제공자 #2) 「시간해상도 1시간 이하, 공간해상도 5 km 이하 한반도 강수자료」(`eval/k4-search/practitioner-conditions.json`).
- 두 조건 검색 경로 모두 주기를 **같은지**만 본다. 「1시간 이하」를 5분·10분·15분·매시 자료로 풀어 주는 길이 없다.
  - 사용자는 주기 값을 하나씩 바꿔 네 번 물어야 하고, 어느 값이 있는지 미리 알아야 한다.
- 오라클 기록 오류 하나가 같이 있다. 1회차 승격(platform-from-instrument · direct-observation-from-level · native-resolution-carried)은 dev 에 반영됐는데(PR #169 · `2026-09-21-evidence-promotion.md` 「dev 반영 완료 2026-09-25T23:52Z」), 오라클은 세 사례를 아직 `blocked_draft`(초안 대기)로 적는다. 점수판이 dev 실상태보다 낮게 적혀 있다.

## 정의 (Ted 판정 2026-09-26 · 구속)
- **「1시간 이하」 = 산출 간격(주기, cadence) ≤ 1시간.** Ted 원문 그대로: 「측정 간격같은데 1시간이하는 산출간격(주기)」.
- 산출 간격(time step)은 다음과 다르다.
  - 누적 기간 — 예: rn15 「15분 누적강수」는 값 하나가 15분 동안 쌓인 양이라는 뜻이다. 값이 몇 분마다 나오는지는 따로다.
  - 파일 묶음 단위 — 파일 하나가 담는 시간 폭.
  - 자료 기간 — 관측이 시작·끝나는 날(`period`).
- **주기(cadence)는 정본(DATASETS.md) 선언값의 전재이며 파일 시간축 실측이 아니다(메타데이터 1회차 결정 3 · 파서 부활 보류). 범위 비교는 선언값 비교이고 연속 관측을 보증하지 않는다.**
  - 예: HSR 원자료(seq 1)는 「시/공간해상도 5분」이지만 파일 10점은 2019~2024 에 흩어진 샘플이다(정본 판정 ㈏ 「연속 계열 아님」).

## 현재 상태 (path:line 으로 확인한 사실)

### 경로 1 — 조건 검색(`plan_query` · `d3_client_search.candidates` · `client_search.evaluate`)
- 주기 술어는 등호뿐이다. `services/core-api/src/colab_core/domains/d3_client_search.py:87-89` 가 `e.facts->'cadence'=CAST(:v AS jsonb)` 로 비교한다. 목록에 없는 술어는 `:92` 가 ValueError 로 거절한다.
- `plan_query` 는 주기를 「일별」(→ daily) · 「월별」(→ monthly)로만 세운다(`app/client_search.py:174-181`). 「1시간」「1시간 이하」는 아무 조건도 만들지 않는다.
- 순서 있는 「이하」 술어의 선례는 `maxResolutionM` 이다.
  - 질의문 파싱 `app/client_search.py:136-138` · 인식 `:198-201` · 판정 `:228-230`(값 없음 → None = unknown) · SQL `domains/d3_client_search.py:73-74`(수가 아니면 false).
- 판정 최상위 `evaluate`(`app/client_search.py:253-266`)는 None 을 unknown 으로, False 를 contradicted 로 둔다.

### 경로 2 — 자연어 검색의 파일 근거(`search_evidence_conditions`)
- `parse` 의 주기는 등호 목록이다(`app/search_evidence_conditions.py:44`). 「5분」「10분」은 읽지만 「15분」은 읽지 않는다(`(?<!\d)5\s*분` 이 「15분」을 비켜 간다). 「15분누적」은 `:66` 이 「가공·누적 간격 unknown」으로 표시한다.
- `assess` 는 주기를 압축 표기 등호로 비교한다(`:84-100`).
- 3회차 측정에서 PC-2-4 「한반도 15분 주기」 경로 2 probe 가 red 였던 이유가 이것이다(`2026-09-26-region-containment-expansion.md` 「측정 결과 — 3회차」 표).

### 계약·어휘
- 주기 값 집합: `contracts/seams/fe-core.yaml:5958-5972` `SearchEvidenceFacts.cadence` enum = daily · weekly · monthly · 15min · hourly · 5min · 10min · yearly. **순서는 어디에도 없다.**
- 검색 어휘 정본 `contracts/search/semantics.json` 에는 주기가 없다. 생성기 `contracts/codegen/gen_search_semantics.py:7-11` 가 두 커널(`services/core-api/src/colab_core/kernel/search_semantics.py` · `services/ai-service/src/colab_ai/kernel/search_semantics.py`)을 만든다(`contracts/codegen/manifest.toml` `search-semantics-core`·`-ai`).

### 주기 사실의 정본 근거 (reviewed cadence 12 자료 전수)
- 입력: develop 생성물 `dev-package/tools/generated/dataset-evidence-payloads.json`(sha256 `c12b50d9…`)의 `facts.cadence`. 판독표 `dev-package/tools/dataset_evidence_backfill.py:140-265` `READINGS`. 문장은 `dev-package/reports/reference-data/datasets-md/**/DATASETS.md` 기계 블록 `description` 축자다.
- 분류: (a) 산출 간격을 명시 · (b) 누적 기간만 · (c) 파일 단위만 · (d) 기타. 해석을 보태지 않는다 — 문장이 말하는 것만 적는다.

| seq | 자료 | reviewed | 정본 문장(축자) | 분류 | 범위 비교 근거 |
|---:|---|---|---|---|---|
| 1 | HSR 레이더 반사도 원자료 | 5min | 「시/공간해상도 5분 / 0.5 km, 변량은 반사도」 | (a) | 충분 |
| 2 | rn15 15분 누적강수 | 15min | 「지상 격자 15분 누적강수. … 이 중 15분 누적 강수를 사용한다」 | (b) | **산출 간격 근거 약함 · Ted 확인 필요**(질문 1) |
| 4 | rn15_sample | 15min | 「rn15 15분 누적강수를 … WGS84 로 좌표계 변환하고 연구대상지를 중심으로 crop 한 전처리 자료. 형태는 (10, 128, 128).」 — 판독표 인용문 「WGS84 로 좌표계 변환하고 연구대상지를 중심으로 crop」은 주기를 말하지 않는다 | (d) 부모 이름 속 누적 기간뿐 | **산출 간격 근거 약함 · Ted 확인 필요**(질문 2) |
| 6 | GK-2A 일 단위 식생자료 | daily | 「시/공간해상도는 1일 / 2 km 다」 | (a) | 충분 |
| 7 | GK2A_NDVI_mean_202305 | monthly | 「일 단위를 월 단위 평균으로 변환했다」 | (a) | 충분 |
| 8 | HLS_S30_NDVI_mean_202305 | monthly | 「3~7일 간격 자료를 월평균 100 m 로 변환한 것이다」 | (a) | 충분 |
| 11 | LULC_2023 | yearly | 「연 단위 100 m 토지피복지도다」 | (a) | 충분 |
| 12 | Prediction (공간상세화) | daily | 「Lv.0 처럼 일 단위 시간해상도를 갖고」 | (a) | 충분 |
| 13 | SPI-4weeks | weekly | 「2000-01-01 ~ 2025-12-31 을 주 단위로 담는다」 | (a) | 충분 |
| 14 | SPEI-4weeks | weekly | 「2000-01-01 ~ 2025-12-31 을 주 단위로 담는다」 | (a) | 충분 |
| 16 | ERA5 변환 결과 | hourly | 「변수는 잠열속(slhf)·단파복사(ssr)·장파복사(str) 셋이고 각 24시각이다」 | (d) 시각 수만 · 간격 문장 없음 | **산출 간격 근거 약함 · Ted 확인 필요**(질문 3) |
| 17 | GK-2A LST 원자료 | 10min | 「GK-2A 지표온도(LST)를 10분 간격으로 담은 NetCDF4 원자료」 | (a) | 충분 |

- (b)·(c)·(d) 세 자료(seq 2 · 4 · 16)의 reviewed 값은 **그대로 둔다**(PR #174 과 같은 규칙 — reviewed 사실을 지우지 않는다). 범위 술어도 이 값을 읽는다. 대신 이 표와 PR 본문에 약한 근거로 드러내고 Ted 질문으로 올린다.
  - ⭑ 판정 뒤(2026-09-26 「전부 권고대로」 · 아래 「판정 결과」): seq 2 · 16 은 reviewed 유지 + provenance 판정 주석 · seq 4 는 reviewed 에서 거두고 계보 초안으로 내림(승인된 제거 — `reviewedRemovals`).
- 자르기·표본 자료의 주기 — 부모의 선언 주기를 **규칙으로 이어받지 않는다**.
  - hsr_sample(seq 3): 정본 문장에 주기가 없다(「형태는 (10, 128, 128)」). reviewed 에도 초안에도 주기가 없다 → 범위 술어에서 unknown(맞추지 않는다).
  - rn15_sample(seq 4): 정본 문장이 자기 주기를 말하지 않는다. 값은 규칙 ID 가 없는 판독표 사실(`provenance` 「정본전재」)로 reviewed 에 실려 있다 — 규칙으로 이어받은 값이 아니므로 초안 규칙이 아니고, 문장 근거도 없다. 질문 2 로 올린다.

### 사례 오라클 (`eval/k4-search/practitioner-conditions.json`)
- 등급: full 3(PC-1-4 · 2-4 · 2-7) · partial 5 · blocked 3 · blocked_draft 3(PC-1-2 · 1-6 · 2-2).
- blocked_draft 사유는 전부 「규칙 추론값은 초안 — 사람 확인 후 승격」이다. 그 규칙 셋이 1회차에 승격돼 dev 에 실렸다.
- 그런데 조건 검색 pytest(`services/core-api/tests/test_practitioner_conditions.py:77-94`)는 develop 생성물(승격 전)을 싣는다. 그래서 pytest 의 일회용 DB 는 dev 보다 한 회차 뒤다.
- 2회차 판정 결과 절은 이미 적었다 — 「1회차 승격 뒤 초안 대기 3사례(PC-1-2 · 1-6 · 2-2)의 measure_only probe 7건은 reviewed 만으로 전부 green 이다(전·후 같음). 오라클 등급(blocked_draft)의 개정은 이 회차 범위 밖이라 두었다.」(`2026-09-21-evidence-promotion.md:308`)

## 원한 결과 (proposed outcome)
- 「1시간 이하」「한 시간 이하」「60분 이하」「30분 이내」가 두 경로에서 같은 주기 상한 조건이 된다.
  - 5분·10분·15분·매시 자료는 맞고, 일·주·월·연 자료는 어긋나고, 주기를 모르는 자료는 모른다(unknown)로 남는다.
- 오라클·점수판이 dev 실상태(1회차 승격 반영)와 같은 숫자를 말한다.

## 가치 가설
- 실무자는 「1시간 이하」 한 번으로 해당 주기 자료(현재 5 건)를 받아, 주기 값을 하나씩 바꿔 묻지 않아도 된다.
- 확인 방법: PC-1-4 · PC-2-4 의 「1시간 이하」 probe 가 경로 1 에서 green 이고, 경로 2 자연어 판이 같은 강수 자료를 파일 근거 후보로 올린다. 다른 probe·골든은 뒤집히지 않는다.

## 영향 범위
- 사용자 / 화면: 경로 2 카드 근거에 「주기 범위(15분 — 1시간 이하 · 등록 설명의 선언값, 파일 시간축 실측 아님) 조건이 맞았어요」가 붙는다. 경로 1 조건 판정 패널(`frontend/src/components/search/SearchAssessment.tsx`)은 새 조건을 「주기 · 1시간 이하」로 보인다(판정 6 · 실제 브라우저 확인).
- 서비스 · 스키마 · 계약:
  - `contracts/search/semantics.json` 에 `cadenceSeconds`(주기 → 명목 초) 추가 · 생성물 두 벌 재생성.
  - core-api 커널 `kernel/cadence_scope.py` 신설(순서 비교 · 문구 파싱 한 곳). 경로 1 `plan_query` · `_predicate` · `d3_client_search.candidates` 와 경로 2 `parse` · `assess` · `supported_facts` 가 이것을 읽는다.
  - `fe-core.yaml` 은 바꾸지 않는다 — 경로 1 응답의 `conditions` 는 `additionalProperties: true` 이고, 연구 조건(`SearchContext.research`)에는 이번에 싣지 않는다.
- 계약 파괴 여부: 아니오(semantics.json 키 추가 · fe-core 무변경 — `gates/tools/contract-breaking.sh` 로 확인).

## 제약
- 순서의 정본은 한 곳(`semantics.json` `cadenceSeconds`)이다. 두 경로가 같은 커널 도우미로 판정한다.
- 모르는·표에 없는 주기는 범위 술어를 맞추지 않는다(unknown ≠ supported). SQL 은 표에 있는 값 목록만 부른다.
- 기존 술어(`cadence` 등호 · `maxResolutionM` 등)의 뜻을 바꾸지 않는다. 범위 술어 하나로 경로 1 인식(`recognized`)을 세우지 않는다 — 제품 갈림(경로 1 ↔ 경로 2)을 바꾸지 않는다.
- 월·연의 초는 명목값(30일 · 365일)이다. 순서 비교 전용이며 기간 계산에 쓰지 않는다.
- reviewed 사실을 지우거나 바꾸지 않는다. 약한 근거는 드러내고 Ted 에게 묻는다.
- 모델 호출 0. 측정은 일회용 DB 에서만 한다(DEV·운영 무접속).

## 설계트리 (grill-me 결과)
- Q1 순서를 어디에 두는가? → A `semantics.json` 에 주기 → 명목 초 표(`cadenceSeconds`)를 두고 생성기로 두 커널에 싣는다(권장안 수용). 순서 목록만 두면 「30분 이내」처럼 enum 에 없는 경계를 못 표현한다.
  - Q1a 계약 enum 과 어긋나면? → A 단위 테스트가 `fe-core.yaml` `SearchEvidenceFacts.cadence` enum 과 표 키 집합이 같은지 본다. 값 추가가 표를 빠뜨리면 red.
- Q2 술어 이름·단위는? → A `maxCadenceSeconds`(양의 유한 초). `maxResolutionM` 처럼 단위를 이름에 싣는다.
- Q3 SQL 은 어떻게 거르는가? → A 커널이 경계 이하 주기 값 목록을 내고 SQL 은 `e.facts->>'cadence' IN (목록)` 으로 거른다. 목록이 비면 아무것도 맞지 않는다. 표 밖 값·수는 목록에 없어 빠진다.
- Q4 「1시간」만 쓰면? → A 범위가 아니다. 지금도 두 경로 모두 「1시간」을 조건으로 세우지 않는다 — 그대로 둔다. 「이상」「미만」도 이번에 열지 않는다(범위 밖).
- Q5 경로 2 에서 「10분 이내」의 「10분」이 등호로도 읽히는가? → A 아니다. 범위 문구를 먼저 떼고 남은 글에서 등호 주기를 찾는다.
- Q6 경로 2 가 「15분」을 주기로 읽어도 되는가? → A 된다. 단 「15분 누적」은 누적 기간이라 주기로 읽지 않는다(정의 절). 다른 probe·골든이 뒤집히지 않는지 측정으로 확인한다.
- Q7 오라클 재채점 규칙은? → A 오라클 `modes` 의 뜻 그대로다. `full` = 정본이 고정한 사실만으로 판정이 선다. 승격된 세 규칙에 기대던 measure_only probe 가 reviewed 만으로 green 이면 판정 probe 로 옮긴다. 아직 초안(지역 규칙)에 기대는 probe 는 measure_only 에 남긴다.
  - Q7a pytest 의 일회용 DB 를 dev 와 맞추는 법은? → A develop 생성물에 1회차 승격 세 규칙을 같은 함수(`measure_draft_contribution.promote_payload`)로 겹쳐 싣는다. 2·3회차 측정 입력(`round-2-2026-09-26/input-payload.json` · sha256 `73a523f0…`)과 같은 방식이다.

## 완료 정의
- ① 코드: 커널 도우미 한 곳으로 두 경로가 판정한다. 단위 테스트 — 5min·10min·15min·hourly 는 「1시간 이하」 supported · daily·weekly·monthly·yearly 는 contradicted · 주기 없음·표 밖 값은 unknown · 문구 파싱 · 「1시간」 등호 무변화 · 경로 2 카드 문구.
- ② 오라클: PC-1-4 · PC-2-4 에 「1시간 이하」 probe 를 싣고 경로 1 green · 경로 2 자연어 판을 녹화해 잰다.
- ③ 오라클 재채점: blocked_draft 3사례를 오라클 규칙대로 다시 매기고, pytest 일회용 DB 를 dev 승격 상태와 맞춘다.
- ④ 측정: 일회용 DB · develop payload + 1회차 승격 · `measure_draft_contribution.py` · 다른 probe·골든 역전 0.
- ⑤ 점수판: 두 intent(이 파일 · `2026-09-21-evidence-promotion.md`)의 숫자를 dev 실상태와 맞춘다.

## 미해결 질문 (Ted 확인 필요 · 번호) — 2026-09-26 전부 판정됨(아래 「판정 결과」)
1. rn15 15분 누적강수(seq 2) — 정본 문장은 누적 기간 「15분 누적강수」만 말한다. 산출 간격도 15분으로 읽어도 되는가? (지금 reviewed `15min` · 범위 술어가 이 값을 읽는다)
2. rn15_sample(seq 4) — 정본 문장이 자기 주기를 말하지 않는다(부모 이름 「rn15 15분 누적강수」뿐). reviewed `15min` 을 그대로 둘 것인가, 초안 규칙(부모 주기 이어받기)으로 내릴 것인가? 내리면 PC-1-4·2-4 의 15분 probe 기대가 [2, 4] → [2] 로 바뀐다.
3. ERA5 변환 결과(seq 16) — 정본 문장은 「각 24시각이다」로 시각 수만 말한다. 산출 간격을 매시(`hourly`)로 읽어도 되는가?
4. hsr_sample(seq 3) — 주기 사실이 없다. 부모 HSR 의 「5분」을 초안 규칙으로 이어받는 규칙을 둘 것인가? (지금은 범위 술어에서 unknown)
5. 점수판 — PC-1-3 · PC-2-3 을 1회차 등급(full)으로 되돌린 재채점(아래 측정 결과 · 8 · 3 · 3 · 0)을 받을 것인가, 지역 probe 가 초안 대기인 동안 partial(6 · 5 · 3 · 0)로 둘 것인가?

## 판정 결과 — 미해결 질문 1~5 · 패널 라벨(2026-09-26, Ted, 원문 그대로)
> 전부 권고대로

1. rn15(seq 2) 「15분 누적강수」 = 산출 간격 15분 — reviewed `15min` 유지. provenance 에 판정 주석을 단다(「판정 2026-09-26 Ted 「전부 권고대로」 — 누적 기간 15분을 산출 간격 15분으로 읽는다」).
2. rn15_sample(seq 4) — reviewed `cadence` 를 거두고 계보 초안 `rule:cadence-from-lineage-parent`(부모 seq 2 · 15min)로 내린다. **Ted 가 승인한 의도적 제거**다 — PR #174 규칙대로 조용히 지우지 않고 대조 증명의 `reviewedRemovals` 절(`round-4-2026-09-26/reviewed-diff-vs-dev-41f488a4.json` · `-vs-73a523f0.json`)과 PR 본문에 이름 붙여 적는다. 15분·「1시간 이하」 probe 기대에서 seq 4 를 뺐다(`apply_cadence_decisions.py`).
3. ERA5 변환 결과(seq 16) 「각 24시각」 = 매시 — reviewed `hourly` 유지 + provenance 판정 주석.
4. hsr_sample(seq 3) — 계보 초안 `rule:cadence-from-lineage-parent` 5min(부모 HSR seq 1)을 싣는다(reviewed 아님 · 승격은 다음 승격 회차).
5. 점수판 8 · 3 · 3 · 0 을 받는다.
6. 경로 1 조건 패널은 새 조건을 사람 말로 보인다 — 「주기 · 1시간 이하」(초 → 분/시간). 구현 `SearchAssessment.tsx` · 단위 시험 `frontend/test/client-search.test.tsx` · 실제 브라우저 확인 `round-4-2026-09-26/browser/`(아래 측정 결과).

## 범위 밖 (명시 제외)
- 주기 실측(파일 시간축 간격 측정) — 헤더 파서 부활과 함께 별도 과제.
- 「이상」「미만」「초과」 하한·엄격 술어, 연구 조건(`SearchContext.research`)의 주기 상한 필드.
- 파일 포맷 예제 주제(seq 15~28)의 경로 2 주제 연결 — 경로 2 는 강우·식생·가뭄 세 주제만 읽어서 ERA5(16) · GK-2A LST(17) 는 경로 2 「1시간 이하」에 닿지 않는다.
- 지역 초안 규칙(`region-from-lineage-parent` 등)의 승격 — 다음 승격 회차.
- dev 반영. 이 PR 은 dev 에 쓰지 않는다.

## 확인
- 프론티어 공집합 확인: <미기입>
- Ted 확인 문장(원문 그대로): "권고안대로핡" (2026-09-26 · 진행 순서 「지역 넓혀 읽기 → 「1시간 이하」 범위 비교 → 자료 요청 목록」 권고안 채택)
- Ted 정의 판정(원문 그대로): "측정 간격같은데 1시간이하는 산출간격(주기)" (2026-09-26 · 「1시간 이하」 = 산출 간격(주기) ≤ 1시간 · 구속)
- 재개봉 금지: 예(정의·진행 순서) · 미해결 질문 1~4 는 열려 있다

## 참조
- 선행: `dev-package/intent/2026-09-26-region-containment-expansion.md` 「완료 정의 ⑥」 · `dev-package/intent/2026-09-21-evidence-promotion.md` 「판정 결과 — 1회차」·「2회차 지역」·「3회차」
- 오라클: `eval/k4-search/practitioner-conditions.json` · 사례 원문 `eval/k4-search/practitioner-cases.md`
- 정본: `dev-package/reports/reference-data/datasets-md/**/DATASETS.md` · 판독표 `dev-package/tools/dataset_evidence_backfill.py` `READINGS`
- 측정: `dev-package/reports/evidence-promotion/round-4-2026-09-26/`
- 결정: 〈N〉 (병합 시 기입)

## 측정 결과 — 4회차(2026-09-26 · 제품 코드 · 반사실 패치 없음)
- 입력: `dev-package/reports/evidence-promotion/round-2-2026-09-26/input-payload.json`(develop 생성물 `c12b50d9…` + 1회차 승격 3규칙 = dev 적재 모양 · 재생성 sha256 `73a523f0…` 동일 확인). 일회용 postgres · 시드 evidence 543 · draft_withheld 69 · 평가 77회 · 모델 호출 0 · DB 지문 전후 동일.
- 산출: `dev-package/reports/evidence-promotion/round-4-2026-09-26/` — `measurement/`(재채점 뒤) · `measurement-code/`(재채점 전 · 구현만) · `cadence-probe-states.json` · 재현 `run_measurement.sh` · probe 추가 `add_cadence_probes.py` · 재채점 `regrade_oracle.py`(+ `oracle_format.py`).

### 「1시간 이하」 probe (reviewed 만 = 초안 포함 · 결과 같음)

| probe | 경로 | 결과 | 맞은 자료(seq · 이름 · 주기) |
|---|---|---|---|
| PC-1-4#p8 1시간 이하(전 자료) `maxCadenceSeconds=3600` | 1 | green | 1 HSR 레이더 반사도 원자료(5min) · 2 rn15 15분 누적강수(15min) · 4 rn15_sample(15min) · 16 ERA5 변환 결과(hourly) · 17 GK-2A LST 원자료(10min) |
| PC-1-4#p9 강수 변수 + 1시간 이하 | 1 | green | 2 · 4 |
| 〃 자연어 판 PB-CADENCE-1 「시간해상도 1시간 이하 강수 자료 찾아줘」 | 2 | green | 파일 근거 후보 1 · 2 · 4(강우·강수 주제) |
| PC-1-4#p10 1시간 이하 + 5 km 이하 | 1 | green | 1 |
| PC-2-4#p5 한반도 + 1시간 이하 | 1 | green | 1 · 2(남한 ⊂ 한반도) |
| 〃 자연어 판 PB-CADENCE-2 「시간해상도 1시간 이하 한반도 강수 자료 찾아줘」 | 2 | green | 파일 근거 후보 1 · 2 |
| PC-2-4#p6 한반도 + 1시간 이하 + 5 km 이하 | 1 | green | 1 |

- 일·주·월·연 자료(6 · 7 · 8 · 11 · 12 · 13 · 14)와 주기 없는 자료(3 · 5)는 들어오지 않는다.
- 경로 2 는 강우·식생·가뭄 세 주제만 읽는다 — ERA5(16) · GK-2A LST(17)는 「파일 포맷 예제」 주제라 경로 2 「1시간 이하」에 닿지 않는다(범위 밖).
- 약한 근거(질문 1~3): 맞은 5 자료 중 seq 2 · 4 · 16 의 주기는 정본 문장이 산출 간격을 직접 말하지 않는다. 값은 그대로 두고 Ted 확인을 기다린다.
- 대조 녹화 PB-CADENCE-3 「30분 이내 강우 자료 찾아줘」 → 경로 2 조건 `maxCadenceSeconds=1800`.

### 다른 probe·골든 (역전 0)
- 3회차 측정(같은 입력 · develop 코드)과 비교: 경로 1 초안 포함 green 33 → 38 · 초안 제외 29 → 34(늘어난 5 = 새 probe) · 잃은 green 0 · 골든 경로 2 9/10 · heldout 경로 2 초안 포함 4/6 · 제외 3/6 불변.
- 경로 2 「15분」 주기 읽기(설계트리 Q6): 영향은 PC-2-4 「한반도 강수 + 15분 주기」 자연어 판(PB-REGION-4) 하나다 — reviewed red(후보 [1, 2] → [2], seq 4 지역이 초안) · 초안 포함 red [1..5] → **green [2, 4]**. 3회차가 이 probe 의 red 원인으로 적은 「「15분」 주기를 파서가 읽지 않는다」가 풀렸다. 골든·heldout 은 뒤집히지 않았다.

### 14사례 점수판 (오라클 등급 · 답 가능 = full · 부분 = partial · 불가 = blocked · 초안 대기 = blocked_draft)

| | 답 가능 | 부분 | 불가 | 초안 대기 |
|---|---:|---:|---:|---:|
| 전 — 오라클 기록(2회차 이후 · dev 보다 한 회차 뒤) | 3 | 5 | 3 | 3 |
| 후 — 4회차 재채점(dev 실상태 = 1회차 승격 반영) | **8** | **3** | 3 | **0** |

- 기대했던 6 · 5 · 3 · 0 이 아니라 **8 · 3 · 3 · 0** 이다. 오라클 규칙대로 매기면 이렇게 된다.
  - blocked_draft 3사례(PC-1-2 · 1-6 · 2-2): 사유였던 규칙이 승격돼 1회차 probe 가 reviewed 만으로 green 이다 → full.
  - PC-1-3 · PC-2-3: 2회차가 **platform 초안 때문에** full → partial 로 내린 사례다. 그 사례 deferred 가 사유를 축자로 적었다 — 「… 기간 축만 남겨 partial 로 내렸다」 · 「… 연도 축만 남겨 partial 로 내렸다」. 1회차에는 같은 probe 로 full 이었다(`git show d533d374^:eval/k4-search/practitioner-conditions.json`). 사유가 풀렸으므로 1회차 등급으로 되돌렸다.
  - 두 사례에 남은 deferred(지역 초안 · NWP 원천 0건 · 기간 교집합)는 1회차 full 때도 있던 것이다. 지역 probe 는 measure_only 에 남는다 — PC-2-4 · 2-7 과 같은 모양이다.
  - 이 두 건을 partial 로 둘지는 Ted 판정으로 되돌릴 수 있다(`regrade_oracle.py` 의 `BACK_TO_FULL` · pytest 집계 두 줄).
- 이번 회차의 주기 범위 술어는 등급을 바꾸지 않는다. PC-1-4 · 2-4 는 이미 full 이었고, deferred 「「1시간 이하」 범위 술어」가 닫혔다.
- dev 실상태 주의: 등급은 develop 생성물 + 1회차 승격(= 2회차 payload 가 dev 에 반영될 때의 모양) 기준이다. dev 에는 2회차 지역 reviewed(seq 1 · 2 · 19 · 20 남한)가 아직 없다(dev 반영 GO 대기). 그래서 지역을 쓰는 판정 probe 2건(PC-1-4#p7 「한반도 + 5분 주기」 · PC-2-4#p5 「한반도 + 1시간 이하」)은 지금 dev 에서는 0건이다. 두 probe 가 든 사례의 다른 probe 는 dev 에서도 선다. 승격 3규칙(platform · directObservation · seq 3 해상도)은 dev 에 이미 있다(`2026-09-21-evidence-promotion.md` dev 반영 표 — platform=ground 8건 · directObservation=true 20건 · 5 km 이하 6건).

## 측정 결과 — 4회차 판정 반영 뒤(2026-09-26 · 「전부 권고대로」)
- 생성물: `dev-package/tools/generated/dataset-evidence-payloads.json` `c12b50d9…` → `9d6c54e3…`(reviewed 127칸 · 초안 124칸 · `cadence-from-lineage-parent` 2). 측정 입력 `round-4-2026-09-26/input-payload.json` sha256 `a5f68030…`(생성물 + 1회차 승격 3규칙 · 같은 함수 · 옮긴 사실 53 · 남은 초안 71).
- 대조 증명(`round-4-2026-09-26/reviewed_diff.py` — 승인 밖 제거가 있으면 판정 실패):

| 대조 | 승인 밖 제거 | 승인된 제거(`reviewedRemovals`) | 추가 | 값 변경 |
|---|---:|---|---:|---:|
| dev 현재(`41f488a4…`) → 새 입력 | 0 | seq 4 rn15_sample `cadence` 15min → 초안(rule:cadence-from-lineage-parent · 부모 seq 2) | 5(2회차 지역) | 0 |
| 2·3회차 입력(`73a523f0…`) → 새 입력 | 0 | 같음 | 0 | 0 |

- 「1시간 이하」 probe(reviewed = 초안 포함 · `cadence-probe-states-decided.json`): 경로 1 5/5 · 경로 2 2/2 green. 바뀐 것 — 전 자료 hit 가 [1, 2, 4, 16, 17] → **[1, 2, 16, 17]**(seq 4 는 reviewed 에서 주기를 모른다) · 「강수 + 1시간 이하」 [2, 4] → [2] · 경로 2 PB-CADENCE-1 후보 [1, 2, 4] → [1, 2]. 15분 등호 probe 2건(PC-1-4 「15분 주기」 · PC-2-4 「강수 변수 + 15분 주기」) 기대 [2, 4] → [2].
- 역전 0: 판정 전 측정(`measurement/`)과 green 집합이 초안 포함·제외 모두 같다(경로 1 38 · 34 · 골든 경로 2 9/10 · heldout 불변). 새 규칙 `cadence-from-lineage-parent` 경로 1 기여 1(PC-2-4#m1 한반도 강수 + 15분 · 초안 포함) · 역전 0.
- 경로 1 조건 패널(판정 6) — 실제 브라우저(agent-browser) · 이 브랜치의 로컬 core-api + vite · 일회용 fixture DB · 해석은 HTTP 테스트 대역(모델 0): 「시간해상도 1시간 이하, 공간해상도 5 km 이하 한반도 강수자료」 → 패널 「주기 / 1시간 이하」, 「30분 이내, 공간해상도 5 km 이하 강수자료」 → 「주기 / 30분 이하」. 원래 키·초 값은 보이지 않는다. 스크린숏 `round-4-2026-09-26/browser/panel-1h.png` · `panel-30min.png`. fixture DB 에 주기 근거가 없어 비교 결과는 0건이다 — 이 확인은 패널 라벨에 한정한다. 경로 2 카드 문구는 단위 시험으로만 확인했다(브라우저 미확인).
