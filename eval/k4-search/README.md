# eval/k4-search — 자연어 검색 실측 하네스

## Stage 3 골든셋과 낱말 기준선

- `golden-set.md`: 12문항의 의미·정답·오답·근거 기준.
- `golden-cases.json`: 같은 질문의 제품 ID·후보 범위·필수 포함 조건. 의미 판정의 정본은 Markdown이다.
- `golden_baseline.py`: 로컬 LiteralInterpreter → dev의 실제 D3 검색 함수. LLM·사전·그래프·HTTP/UI·근거 생성은 평가하지 않는다.
- `test_golden_baseline.py`: 잘림·중복·복수 정답 누락·범위 밖 후보·의미 미판정의 오판 방지 시험.

기존 dev 운영자 환경에서 `COLAB_DEV_SSH`, `COLAB_DEV_KEY_FILE`을 프로세스에 제공한다. 값은 출력하지 않는다.

```bash
python3 -m unittest discover -s eval/k4-search -p test_golden_baseline.py
python3 eval/k4-search/golden_baseline.py --output dev-package/reports/stage3-ai-search-plan/literal-run-new.json
python3 eval/k4-search/golden_baseline.py --mode expanded --output dev-package/reports/stage3-ai-search-plan/expanded-run-new.json
```

출력 경로가 이미 존재하면 준비 실패로 종료한다. 전체 스코프 매치 전수(최대100)를 확인한 뒤 문항별 허용 ID로 제한한다.
따라서 전체 연구실 검색이 0건일 때만 발동하는 이름 유사도 폴백은 그대로 유지된다. 독립 9건 DB의 실행과 동일하다고 주장하지 않는다.
필수 정답 포함 여부/빈 후보 검사는 자동, 추천 이유·품질·조건 단정은 미판정으로 별도 기록한다.
종료코드 0=자동 포함 검사 실패 없음(전체 품질 통과 아님), 1=자동 판정 실패, 78=준비 실패.
코드·해석기·평가셋·자료 스냅샷 hash, 실행 시점의 후보25건 및 검색 벡터, 순위·소요시간을 결과에 보존한다.
소요시간은 D3 호출 시간이며 LLM 지연·API 왕복·사용자 체감 속도를 뜻하지 않는다.
`--mode expanded`는 dev AI의 실제 낱말 해석·기능어 제거·사전·그래프를 실행하며 LLM은 호출하지 않는다.
`--omit-topic-filter`는 expanded에서만 쓰는 분리 실험으로, 확장 검색어를 유지하고 topic을 None으로 전달한다. 제품 정책 변경이 아니다.
사전 snapshot은 한 번 읽어 재사용하며 원자료·해석 결과·소스 hash를 결과에 보존한다. degraded 확장은 준비 실패다.

## 기존 그래프 확장 비교

`sessions/K1b-ONTOLOGY-CONTENT §D` 의 질의 예시들은 **지면 대조**였다 — 그 절이 스스로
`[미확인]` 이라 적었다. 여기 있는 둘이 그 대조를 `SELECT` 로 바꾼다.

| 파일 | 무엇 |
|---|---|
| `seed-15.sql` | `SEED-DATA §3.1` 의 데이터셋 15건. **이름·주제·원천 표기 세 칸뿐**이다 — `0005` 의 tsvector 가 훑는 글자가 그 셋이다 |
| `measure.py` | 그래프 확장 **전/후**를 같은 질의로 돌려 결과 집합·순위·일한 엣지를 나란히 찍는다 |

**제품 코드가 아니다.** 배포 단위 둘을 한 프로세스에서 부르는 것은 측정을 위해서다.
제품에서 두 단위는 HTTP 로만 만나고, core-api 는 AI 체인에 붙지 않는다
(`PLAN-SoT §9-〈90〉-㉮`). 이 하네스도 그 성질을 지킨다 — 그래프는 `colab_ai` 만 읽는다.

## 돌리는 법

```
# ① 두 체인의 DB (RESTART.md ④ 와 같은 방식 — 호스트 포트를 열지 않는다)
docker run -d --name <레인>_pg --tmpfs /var/lib/postgresql/data:rw,size=512m \
  -e PGDATA=/var/lib/postgresql/data/pg -e POSTGRES_PASSWORD=<임시> postgres:16-alpine

# ② 플랫폼 — 선언 스키마 + 앱 롤 + 이 시드
#    ⚠ 소유자에게 GRANT CREATE ON DATABASE 가 필요하다 (schema.sql 이 pg_trgm 을 만든다)
# ③ AI     — db/ai/schema.sql + db/ai/seed/*.sql
# ④ 측정
python3 eval/k4-search/measure.py <platform-app-url> <ai-app-url>
```

## 2026-08-25 실측 (`K4-b` · `〈89〉`·`〈90〉`)

| 질의 | 그래프 없이 | 그래프 있음 | 판정 |
|---|---|---|---|
| 재격자화한 NDVI 자료 | 8건 · 1위 `D-01` | 8건 · **상위 3 = `D-03`·`D-04`·`D-05`** | `NDVI` 가 이미 8건을 물었으므로 **집합이 아니라 순위**가 바뀐다. 올라온 것이 **정확히 셋**이고 `D-06`(Co-Kriging)은 아니다 — `F-4d` 기각(`〈86〉`)이 결과에 그대로 보인다 |
| 전처리한 강우 자료 | 3건 | **3건 (그대로)** | 금지 목록이라 확장이 **시작되지 않는다**. 초안이 걱정한 「15건 중 12건」이 일어날 수 없다 |
| Bilinear 로 만든 자료 | 1건 | **1건 (그대로)** | 하향 전용. 상향으로 탔다면 `D-03`·`D-05` 가 오답으로 딸려 왔다 |
| 한반도 전체 식생 자료 | 9건 | 10건 (`D-02` 추가) | `E2-1`. §D-5 가 예고한 `D-02` 혼입까지 그대로 재현된다 |
| 25년도 낙동강 유역 강우 | 3건 | 3건 | **그래프는 0건을 없애 주지 않는다** — 낙동강 자료가 애초에 없다 |

접두 질의(`〈89〉`)가 새로 여는 것 — 「충청」 **0 → 5건** · 「가뭄」 **0 → 1건** · 「격자」 **0 → 1건**.
유사도 보조 팔이 받는 것 — 「HSR레이더견본」·「레이더견본」 → `D-15`(자리 = `이름(비슷한 말)`).
**여전히 0건인 것** — 「강수량」·「위성」·「다운스케」. 매칭은 표기를 넘지 못한다.

## 2026-09-18 재측정 — 실무자 사례 어휘 13행 적재 전/후

같은 `measure.py`, 같은 15건 평가셋(`seed-15.sql`), 같은 플랫폼 DB. 바뀐 것은 **AI DB 의 리비전뿐**이다
(전 = `0008_dataset_knowledge` · 후 = `0009_practitioner_lexicon`). 모델 호출 0회.

| 질의 | 적재 전 | 적재 후 | 무엇이 바뀌었나 |
|---|---|---|---|
| 강수량 | **0건** | **3건** `D-08`·`D-07`·`D-15` | 새 동의어 「강수량」이 주제 `강우·강수` 로 가면서 후보집합에 진입한다. 위 2026-08-25 표의 「강수량 0건」이 닫힌 자리다 |
| 강수 | 3건 | 3건 (그대로) | 접두 질의로 이미 잡히던 자리다 — 동의어가 **순위를 바꾸지 않는다**(`〈72〉-㉮`) |
| 그 밖 7질의 | — | **전부 동일** | 지명 별칭 4행·동의어 9행은 개념 그래프를 건드리지 않았다 |

**여전히 0건인 것** — 「위성」·「다운스케」. 둘 다 이 회차의 승인 범위 밖이다(관측 기반 축 = 정본 개정 대기).

## 2026-09-18 재측정 — 자료 메타데이터 28건 적재 전/후

같은 `measure.py`, 같은 15건 평가셋(`seed-15.sql`), 같은 AI DB(`0010_practitioner_concept`).
**9질의 전부 동일하다** — 이 회차가 바꾼 것은 D3 의 검색 근거·`topic`·`source_label` 이고
`measure.py` 가 재는 것은 AI 그래프 확장이라 겹치는 자리가 없다. 「안 바뀌었다」를 적는 이유는
이 하네스로 이번 회차를 잰 것처럼 인용하지 않기 위해서다.

바뀐 자리는 `measure_evidence.py` 가 잰다 — DEV 정본 28건을 일회용 DB 에 세우고,
**같은 DB 안에서** 근거·`topic`·`source_label` 만 비운 상태(before)와 적재된 상태(after)를
나란히 센 뒤 rollback 한다. 두 DB 를 따로 세우면 시드 차이가 측정에 섞인다.

```bash
# ① 일회용 DB + 스키마·롤·시드 (service-tests 가 쓰는 것과 같은 재료)
CONTAINER=<컨테이너> DB=colab_platform bash services/core-api/tests/fixtures/setup-db.sh
# ② DEV 정본 28건 재현 + 근거 적재 (멱등)
python3 dev-package/tools/dataset_evidence_backfill.py
python3 dev-package/tools/dataset_evidence_apply.py --database-url <URL> --reviewer <ULID> --dry-run
python3 dev-package/tools/dataset_evidence_apply.py --database-url <URL> --reviewer <ULID>
# ③ 전/후 측정
services/core-api/.venv/bin/python eval/k4-search/measure_evidence.py <URL>
```

2026-09-18 실측 (모델 호출 0회):

| 질의·조건 | 적재 전 | 적재 후 |
|---|---|---|
| 주제 결합 「강수」 + `topic=강우·강수` | 2건(시드 A 두 건) | **7건** |
| 주제 결합 「가뭄」 + `topic=가뭄` | **0건** | **2건** |
| 원천 표기 「기상청」 | 1건 | **7건** |
| 조건 `platform=ground` | 0건 | **8건** |
| 조건 `platform=satellite` | 0건 | **14건** |
| 조건 `cadence=hourly`(결정 2-ⓐ 로 연 값) | 0건 | **1건** |
| 조건 `cadence=15min` | 0건 | **2건** |
| 조건 `directObservation=true` | 0건 | **20건** |
| 조건 `maxResolutionM<=5000` | 0건 | **6건** |
| 조건 `variable=precipitation` + `coverageYear=2022` | 0건 | **3건** |
| `d3_search_evidence` 행 | **0행** | **28행** |
| `topic` 비-NULL | 3행(시드) | 31행(시드 3 ＋ 28) |
| `source_label` 비-NULL | 2행(시드) | 11행(시드 2 ＋ 9) |

「가뭄」 주제 결합의 **0 → 2건**이 온톨로지 intent 의 미해결 질문 하나를 닫는다 — 2026-09-15
보고서가 지목한 0건의 원인은 코드가 아니라 **설명 행의 `topic` 이 전부 NULL** 이던 것이다.

`source_label` 은 28건 중 **9건만** 채웠다. 나머지 19건은 정본 문면이 원천 기관을 말하지 않는다
(`PLAN-SoT §9-㊴-②` — 정본에 없으면 만들지 않는다).

### 실무자 사례 오라클

`practitioner-conditions.json` ＋ `services/core-api/tests/test_practitioner_conditions.py`.
같은 일회용 DB 에서 적재 전 **11 failed / 4 passed**(실패는 전부 「근거 적재 0건」),
적재 후 **15 passed**. 집계는 가능 8 · 부분 3 · blocked 3 이고, blocked 3건
(`#1-5`·`#2-5` 자료 부재 · `#2-6` pressure level)은 green 을 주장하지 않는다.

## 2026-09-21 재측정 — 규칙 추론값을 초안으로 내린 2회차

같은 하네스·같은 일회용 DB 재료. 바뀐 것은 **생성물 payload 와 계약의 cadence 3값**이다.
Ted 결정 1 축자 — 「다 초안으로 넣는다. 실제로 얼마나 히트했냐를 측정하고 이에 따라 승격 또는
폐기하는 구조를 가져야한다.」 → `platform`·`representation`·`directObservation`·`interpolated`
와 규칙으로 이어받은 `nativeResolutionM`·`region` 은 **적재되지 않는다**.
조건 검색은 `status='reviewed'` 만 읽으므로(`d3_client_search.py:97`) 그 축은 0건이 된다.

돌리는 법은 위 2026-09-18 절의 3단계와 같다. 모델 호출 0회.

| 질의·조건 | 적재 전 | 1회차 적재 후 | **2회차 적재 후** |
|---|---|---|---|
| 주제 결합 「강수」 + `topic=강우·강수` | 2건 | 7건 | **7건** |
| 주제 결합 「가뭄」 + `topic=가뭄` | 0건 | 2건 | **2건** |
| 원천 표기 「기상청」 | 1건 | 7건 | **7건** |
| `platform=ground` | 0건 | 8건 | **0건 — 초안** |
| `platform=satellite` | 0건 | 14건 | **0건 — 초안** |
| `directObservation=true` | 0건 | 20건 | **0건 — 초안** |
| `cadence=hourly` | 0건 | 1건 | **1건** |
| `cadence=15min` | 0건 | 2건 | **2건** |
| `cadence=5min` (결정 3) | 0건 | — (enum 밖) | **1건** (seq 1 HSR) |
| `cadence=10min` (결정 3) | 0건 | — (enum 밖) | **1건** (seq 17 GK-2A LST) |
| `cadence=yearly` (결정 3) | 0건 | — (enum 밖) | **1건** (seq 11 LULC) |
| `maxResolutionM<=5000` | 0건 | 6건 | **5건** (seq 3 의 해상도는 규칙값 → 초안) |
| `variable=precipitation` + `coverageYear=2022` | 0건 | 3건 | **3건** |
| `d3_search_evidence` 행 | 0행 | 28행 | **28행** |

**「시간해상도 1시간 이하」 히트** — 1회차 **3건**(hourly 1 ＋ 15min 2) → 2회차 **5건**
(＋ 5min 1 ＋ 10min 1). 1회차 후속 6번이 「정본이 말하는데 적지 못했다」고 남긴 자리가 닫혔다.
`yearly` 1건은 1시간 이하가 아니라 별도다.

**사실 칸의 등급** — 1회차 reviewed 230칸 · draft 0칸 → 2회차 **reviewed 123칸 · draft 110칸**
(＋ cadence 3칸이 reviewed 로 늘었다). 규칙별 초안 셈은 생성물 옆
`dev-package/tools/generated/dataset-evidence-payloads-rule-summary.json` 에 있다 —
platform 26 · representation 28 · directObservation 26 · interpolated 28 ·
native-resolution-carried 1 · region-from-registration-note 1 · **bbox-korea-peninsula 0**.

적용기 멱등 실측 — 1회 `evidence 28 / unchanged 0`, 2회 `evidence 0 / unchanged 28`,
두 번 모두 `draft_withheld 110`.

### 실무자 사례 오라클 (2회차)

같은 일회용 DB 에서 **17 passed**. 집계가 1회차 가능 8 · 부분 3 · blocked 3 에서
**가능 3 · 부분 5 · blocked 3 · blocked_draft 3** 으로 바뀌었다. 줄어든 자리는 규칙 추론값을
초안으로 내린 만큼이고, 새 등급 `blocked_draft` 의 사유는 「규칙 추론값은 초안 — 사람 확인 후
승격」이다. `PC-1-2`·`PC-1-6`·`PC-2-2` 가 그 자리이고 `PC-1-3`·`PC-2-3` 은 reviewed 축만
남겨 partial 로 내렸다. **초안 사실 위에서 green 을 주장하지 않는다.**

지명 축은 여전히 비어 있다 — 정본을 고치지 않고 후보표만 만들었다
(`dev-package/reports/practitioner-place-candidates-260921.md` · 후보가 선 행 8 / 28,
보조 bbox 는 28행 전부 미상).

## 고정 snapshot 조건 결합 실험

`python3 eval/k4-search/structured_probe.py --output <새 JSON 경로>`

제품 검색과 분리된 오프라인 후보 실험이다. `unverified` 조건은 충족으로 표시하면 안 된다. 추가6문항은 구현 전 공개돼 blind holdout이 아니다. [범위와 결과](../../dev-package/sessions/20260912-ai-search-structured-probe.md)를 함께 읽는다.

## 조건·파일 역할과 로컬 제품 비교

- `file-role-evidence.json`, `condition-evidence.json`: 설명서 출처를 검토한 연구용 주석. 제품 DB 메타데이터가 아니다.
- `condition_assessment.py`: supported/contradicted/unknown 조건 컴포넌트.
- `heldout-cases.json`, `heldout_eval.py`: 최초 미공개6문항은3통과/3실패. 수정 후 결과는 개발 회귀 검사이며 파일 검색3개와 조건 컴포넌트3개를 구분한다.
- `search_journey.py`: 격리 DB와 실제 core/frontend를 사용하는 브라우저 여정. HTTP 해석 대역을 쓰므로 실제 AI/LLM 품질 평가가 아니다.

```bash
python3 -m unittest discover -s eval/k4-search -p 'test_*.py'
python3 eval/k4-search/heldout_eval.py --output <새 JSON 경로>
services/ai-service/.venv/bin/python eval/k4-search/golden_baseline.py --mode local-expanded --frozen-expansion dev-package/reports/stage3-ai-search-plan/expanded-baseline-01.json --output <새 JSON 경로>
```

`local-expanded`는 고정 사전/그래프를 실제 로컬 SearchService에 공급하고 dev D3를 읽기 전용 호출한다. 코드 hash를 기록하며 배포된 API나 전체 답변 검증으로 보고하지 않는다. 최신 결과와 미충족은 [실행 기록](../../dev-package/sessions/20260913-ai-search-execution.md)에 모은다.

## 설명서 원문 수집·변경 검사

`reference_evidence.py --reference-root <레퍼런스 루트> --output <새 JSON>`은 DOCX 문단과 내용 hash 및 snapshot 파일 ID 바인딩을 저장한다. 같은 이름 문서가 복수이면 임의 선택하지 않는다. `--verify <기존 JSON>`은 원문 변경·삭제를 검사한다. 자동 의미 추출이나 제품 저장이 아니며 대상 데이터 파일의 내용 버전까지 검사하지 않는다.

## 검색 변경 시 자동 골든 회귀

PR과 main push에서 core-api·ai-service·frontend·계약·DB·이 평가 폴더·고정 입력·실행 도구의 관련 경로가 바뀌면 CI의 `search-golden` 잡이 실행된다. 경로 정본은 `.github/workflows/ci.yml`의 같은 이름 필터다.

로컬에서도 같은 진입점을 쓴다(core-api 개발 의존과 Docker 필요):

```bash
services/core-api/.venv/bin/python eval/k4-search/run_regression.py
```

현재 helper 43건과 실제 core-api 공개 API를 통한 골든 12문항을 검사한다. DB는 일회용이며, 질문 해석은 고정 응답을 사용한다. Sonnet 호출·모델 품질 평가·배포 환경 데이터 변경은 하지 않는다.

문항 보강은 `golden-cases.json`에서 질문·필수 결과·빈 결과 기대를 수정하고, 대응하는 고정 해석을 `eval/k4-search/fixtures/reference/expanded-normalized-02.json`의 `expansion.responses`에 같은 ID와 순서로 반영한다. 사례 수는 늘릴 수 있다. 빈 입력, ID/순서 불일치, 시험 실패는 실패로 처리한다.

## 초안 사실 기여 측정 (intent `2026-09-21-evidence-promotion`)

규칙 추론 초안(payload `draftFacts` 110칸)을 일회용 DB 의 reviewed 사실에 한 트랜잭션 안에서 겹쳐 쓰고, 규칙 단위·사실 단위로 하나씩 빼며 경로 1(`d3_client_search.candidates`)·경로 2(`search_evidence_conditions` → `search_datasets`)를 따로 잰 뒤 rollback 한다. 경로 2 해석은 `interpret-fixture.json`(규칙 기반 녹화 — LLM 녹화는 후속 단계)으로 고정하고 모델을 부르지 않는다. heldout 은 사후 확인 열이며 제안에 쓰지 않는다. 경로 1 오라클은 `practitioner-conditions.json` 의 `probes` 와 `measureOnlyProbes`(2회차가 거두거나 바꾼 1회차 probe · 초안 값 측정 전용 · 정답 주장 아님 · 2026-09-26 Ted 「전부 권고대로」)다 — 조건 검색 pytest 는 measure_only 를 green 으로 세지 않는다.

```bash
CONTAINER=<일회용 컨테이너> DB=colab_platform bash services/core-api/tests/fixtures/setup-db.sh   # 앱 롤 URL 출력
services/core-api/.venv/bin/python eval/k4-search/measure_draft_contribution.py <앱 롤 URL> --seed-dev-like --i-know-this-is-disposable --output dev-package/reports/evidence-promotion/round-<N>-<날짜>
services/core-api/.venv/bin/python eval/k4-search/measure_draft_contribution.py <앱 롤 URL> --i-know-this-is-disposable --rehearse-promote <규칙 ID> --output <같은 회차>/rehearsal   # 승격 PUT 본문 대조만 · 보내지 않음
```

**온톨로지 회차 절차에 이 표(`draft-contribution-review.md` + `draft-contribution.json`)를 첨부한다.** 기계는 제안만 하고 Ted 가 회차 intent 의 「판정 결과」 절에서 판정한다(결정 6).

한계: 경로 2 는 `routes/catalog.py` 경로 2 블록을 도메인·순수 함수 호출로 재현한 것이다(HTTP 층 없이 부를 수 있는 제품 함수만 부르고 제품 코드는 고치지 않았다). 라우트의 verified 걸름·잠김 조립·근거 문장은 green 판정에 들어가지 않으며, 라우트가 바뀌면 이 재현도 따라가야 한다. 1회차 실측은 `dev-package/reports/evidence-promotion/round-1-2026-09-26/`.

2회차 지역(2026-09-26 Ted 「자료 지역 확정」)은 `--round "2회차 지역"` 과 `--payload <회차 입력>` 으로 돌렸다 — 입력·재현 스크립트·「한반도」 region probe 상태표(반사실 포함)는 `dev-package/reports/evidence-promotion/round-2-2026-09-26/`.
