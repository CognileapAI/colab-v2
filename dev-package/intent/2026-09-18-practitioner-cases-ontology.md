# Intent: 실무자 사례 14건 기반 온톨로지 보강
메타 — 발의자: 구서영·변종윤(실무자 사례) · 정리: Claude(researcher, 대조 조사) · 작성 2026-09-18 · 승인 **승인 2026-09-18 (Ted, 「다 권고대로」)**

**판정 결과(2026-09-18, Ted):** 아래 8개 결정 전부 권고대로. (i) 19행 전부 채택, (v) 픽스처 선행. (ii)·(iii)·(iv) 는 이 회차에서 열지 않는다. `PLAN-SoT §9-㊴-②` — 「정본에 없으면 만들지 않는다」.

## 사례 출처 (원본)
- **#1 검색 상황 6건 — 구서영님 제공** (적합 데이터셋 / 특성 차이 / 기간·지역 매칭 / 해상도 조건 / 관측-보조자료 매칭 / 원본-가공 구분)
- **#2 질문·기대답변 8건 — 변종윤님 제공** (기대답변에 `XXXX` 자리표시자 포함)
- 전달 2026-09-18, 사용자 경유. 대조 결과는 `case-gap-matrix`(조사 산출물, 레포 외부 작업 경로)에 있다.

## 문제
- 실무자 14건이 요구하는 검색 성분 중 **현재 온톨로지가 닿는 것은 어휘 관문뿐**이고, 14건 모두 자료 메타데이터 사실을 추가로 요구한다.
- 어휘 관문조차 막혀 있다. `eval/k4-search/README.md:68` 축자 — 「**여전히 0건인 것 — 「강수량」·「위성」·「다운스케」. 매칭은 표기를 넘지 못한다.**」
- `d9_place_alias` 는 4행뿐이라 **「한반도」가 사전에 없다.** 같은 값이 `d9_concept` 에는 `p-korea-peninsula`(등급 ②)로 이미 있다 — 사전과 그래프가 **비대칭**이다. 14건 중 6건이 한반도를 조건으로 쓴다.
- `ERA5`·`ECMWF`·`유럽중기예보센터`는 `ONTOLOGY-SCOPE.md §2.7-⑴` 정본 인용에 있는데도 개념 노드가 없다. 2026-08-25 보류 사유는 `db/ai/seed/k2b_concept_graph_seed.sql` 축자 「**15 데이터셋에 그 원천이 0 건이라 결과를 안 바꾼다**」였고, 사례 6건이 ERA5 를 명시로 부르면서 **그 사유가 무너졌다**.
- 레이더·AWS·disdrometer·CCTV·NWP 는 `d9_concept.kind` CHECK 4값(`db/ai/schema.sql:147`) 어디에도 들어가지 않는다. 「관측 기반」 축은 `ONTOLOGY-SCOPE.md §③` 10건 목록에 **항목으로도 없다**.
- CAPE·CIN·상대습도·수증기량·바람·온도·반사도·pressure level 은 `ONTOLOGY-SCOPE.md §③` **3행이 「범위 밖」으로 닫은 변수 사전**이다.
- 자료 쪽도 비어 있다. 2026-09-15 보고서 축자 — 「살아 있는 28개 자료의 출처 source_label은 모두 NULL.」 / 「설명 행은 삭제 자료 포함 30개이며 topic은 모두 NULL이다.」 **동의어를 늘려도 주제 결합에서 0건이 될 수 있다.**

## 원한 결과 (proposed outcome)
- O1. 시드 변경 **전에** red 를 내는 어휘 오라클이 존재하고, 시드 적재 후 green 으로 전이한 것이 파일 변경으로 증명된다.
- O2. 현 정본 범위 안의 후보 19행이 Ted 판정을 받아 확정되거나 기각되며, **판정 없이 적재되는 행이 0건**이다.
- O3. 정본 개정이 필요한 항목(관측 기반 축·변수 사전·신규 관계값)이 「보강」에 섞이지 않고 별도 결정으로 분리된다.
- O4. 14건 중 자료 메타데이터 사실을 요구하는 성분이 2026-09-15 보고서 **후속 2번**으로 명시 인계되고, 온톨로지 작업이 그것을 대신했다고 주장하지 않는다.
- O5. `XXXX` 자리표시자가 어떤 형태로도 문자열 비교 기대값이 되지 않는다.

## 범위 — 다섯 갈래로 가른다

### (i) 현 정본 범위 안 시드 추가 — 후보 **19행**
| 표 | 행 | 내용 |
|---|---|---|
| `d9_topic_synonym` | **9** | 강수량·강수·강우·강우량·강수자료·강우관측·집중호우·호우·precipitation → 주제 `강우·강수`. `topic` CHECK 6값 안이라 **스키마 무변경** |
| `d9_place_alias` | **4** | 한반도 · Korea→한반도 · 충청권 · southern Gyeonggi and Chungcheong regions→충청권. 전부 `d9_concept` 에 등급 ②로 이미 승인·적재된 값 |
| `d9_concept` | **5** | 원천표기 `s-era5`·`s-ecmwf`·`s-ecmwf-ko`(등급 ⑤, §2.7-⑴ 인용) + 주제 `t-drought`·`t-fileformat`(등급 ①, 4→6 정합화) |
| `d9_concept_edge` | **1** | `s-ecmwf` 같은 말이다 `s-ecmwf-ko`(F-12 ㈎ 기존 판정). 현 3값 CHECK 로 표현 가능한 유일한 행 |

동반 개정 — `db/ai/seed/k2-coverage-standard.tsv` 의 `place` 기준 **4→8**, `db/ai/seed/k2b-graph-standard.tsv` 노드 49→54·엣지 19→20, `db/ai/tools/k2b_graph_check.py:42 CANON_TOPICS` 4→6, 새 alembic 리비전 1개 + 새 시드 SQL 1개(회차마다 제 적재물을 갖는 체인 규율).

⚠ **출처 등급 문제.** `K1b-ONTOLOGY-CONTENT.md:28` 의 등급 ①~⑥ 어디에도 「실무자 사례」가 없고 `source_grade` CHECK 는 `BETWEEN 1 AND 6` 이다. 9행 동의어만 이 문제에 걸린다(지명 4행·ERA5 3노드는 등급 ②·⑤ 근거가 따로 있다). 권고 = `topic_synonym_six.sql` 선례대로 **Ted 가 값을 직접 판정해 내려보내고** `source_note` 를 「Ted 판정 2026-MM-DD — 실무자 사례 #1-6(구서영)·#2-1(변종윤) 검토」로 적는다. 스키마·등급 무변경.

### (ii) 정본 개정이 선행해야 하는 항목
| 항목 | 고쳐야 할 정본 조항 |
|---|---|
| 변수 사전 (강수량·반사도·CAPE·CIN·상대습도·수증기량·바람 u·v·온도, pressure level) | **`dev-package/ONTOLOGY-SCOPE.md` §③ 3행** — 「\| 3 \| **변수 사전** (표준명·단위·한국어명·동의어). `유출·수위`는 정본에 변수로 없다 \| **범위 밖** \|」. 같은 문서 §2 「**변수 사전이 없다.** … 변수 동의어(`tp`↔`강수량`↔`강우`)도 없다」 |
| 관측 기반 축 (레이더·위성·AWS·disdrometer·CCTV·NWP·재분석) | `ONTOLOGY-SCOPE.md` §2 에 **절 신설**이 필요하다 — §③ 10건에 항목으로도 없어 고칠 줄이 아직 없다. 동시에 `db/ai/schema.sql:147` `kind` CHECK 4값 개정 |
| 「우리나라」·「남한」 등 무근거 별칭 | 근거 0건. `k2_ontology_seed.sql` 축자 「**지어낸 별칭을 넣지 않는 것이 이 표의 값어치다**」 |

⚠ 변수 사전은 `MATCHER`·discovery digest 정의를 바꾸므로 **모든 기존 manifest version 무효화 → `requeue` 전면 재처리**다. 이 intent 는 이를 **열지 않는다.**

### (iii) 신규 관계값 — 스키마 CHECK 변경
`db/ai/schema.sql:187` `relation IN ('같은 말이다','~의 한 가지다','안에 있다')` 3값.
- `~이 제공한다` — ECMWF → ERA5. CHECK + `k2b_graph_check.py:33 RELATIONS` + 기준 TSV 동시 개정.
- `~을 관측한다` — (ii) 의 두 항목이 **둘 다** 선행해야 성립한다.
- `~에서 가공되었다` · `~을 보정한다` — ⚠ 자료↔자료 사실이면 **D3 계보·지식 KG 의 몫**이다. `d9_concept` 머리 주석 축자 — 「**여기에 「데이터셋에 대한 사실」은 한 줄도 들어오지 않는다.**」 개념↔개념 층에서는 `m-bias-corr`(편의 보정)·`m-regrid`(재격자화) 어휘가 이미 표현한다.

### (iv) 자료 메타데이터 사실 — 온톨로지 밖, 후속 2번으로 인계
기간·bbox·시간/공간 해상도·결측률·변수 목록·pressure level 보유·관측 기반·원 해상도·출처.
`dev-package/reports/ai-search-dev-review-20260915.md:56` 축자 — 「**변수·지역·기간·관측 기반·원 해상도·가공 역할·출처를 검토 근거로 적재하고 주제 분류의 누락을 정합화한다. 자료 전체 초기화는 필요하지 않다.**」
14건 중 **14건**이 이 항목에 걸려 있고, **온톨로지 단독으로 답이 되는 사례는 0건이다.** 공통 기간·영역 계산, 반경 거리 계산, 「내 연구」 맥락 참조는 각각 계산·대화 기능이며 온톨로지 대상이 아니다.

### (v) 평가 픽스처 우선 — **이 intent 의 첫 작업 단위**
- `eval/k4-search/practitioner-lexical.json` — `d9_ontology.expand()`·`expand_by_graph()` 순수 함수 오라클. DB·모델 호출 0회. 현재 기대값은 전부 `miss`.
- `eval/k4-search/practitioner-cases.json` — 14건 본체. `client-golden.json` 형식(`version`/`source`/`clock`/`scope`/`cases`) + `by` 필드로 제공자 보존.
- `XXXX` 처리 — 건수는 `null`, 제품명은 필수 포함 ID 집합, 수치는 `requiredEvidence` 성분 목록. **문자열 비교 0건.** 선례 = `golden-set.md` 축자 「**예시 문장과 축자 일치시키지 않는다.**」
- 후속 2번 없이 판정 불가한 사례는 `mode:"blocked"` 로 두고 **green 을 주장하지 않는다**(`gates/README.md:108-109` 의 `SKIP` 부재 규약과 같은 정신).
- 러너는 기존 `eval/k4-search/run_regression.py:76` 의 `["core-api","search_golden"]` 두 묶음에 붙인다. 새 러너를 만들지 않는다.

## 영향 범위
- 사용자 / 화면: 검색 결과 집합이 넓어진다. 새 UI 없음.
- 서비스: `services/ai-service` 의 사전 조회·확장 경로. **쓰기 API 없음**이 유지된다(변경 수단 = 새 리비전 + 새 시드 + 기준 TSV 동시 개정).
- 스키마: (i) 범위에서는 **무변경**. (ii)·(iii) 는 CHECK 변경이며 이 intent 의 승인 대상이 아니다.
- 계약: (i) 범위에서는 파괴 없음. manifest digest 는 **내용 해시라 값이 바뀌면 version 이 바뀐다** — 재게시·`requeue` 가 따라온다.
- 계약 파괴 여부: (i) 아니오 / (ii)·(iii) 예(별도 서명 필요).

## 제약
- 「정본에 없으면 만들지 않는다」(`PLAN-SoT §9-㊴-②`). 후보 19행 중 값 판정이 없는 행은 적재하지 않는다.
- 기준(TSV)과 적재물(SQL)을 분리한 규약을 유지한다 — `k2_ontology_seed.sql` 축자 「**기준을 적재물에서 만들면 커버리지 체크가 영원히 green 이 된다.**」
- 등급 ⑥ 은 `k2b_graph_check.py::APPROVED_G6` 와 정확히 일치해야 한다. 노드는 현재 등급 ⑥ 0건이며 이 회차도 **0건을 유지**한다.
- 실제 Sonnet 평가 보류를 유지한다. 이 회차의 모든 판정은 **모델 호출 0회**다.
- DEV 자료·설정·배포를 변경하지 않는다. 커밋·push·PR 게시는 사용자 몫이다.
- 자료 전체 초기화·재시드를 하지 않는다(`R-AI-SEARCH-RELEASE.md:14`).

## 완료 정의
1. (v) 픽스처 2파일이 존재하고, 시드 적재 **전** 상태에서 어휘 오라클이 **red** 를 낸다(전이의 출발점 확정).
2. Ted 가 (i) 19행 각각에 채택/기각을 판정하고, 채택분만 새 시드 SQL + 새 alembic 리비전 + 기준 TSV 동시 개정으로 들어간다.
3. 적재 후 어휘 오라클이 **green**, K2 커버리지 오라클과 K2b 판정기가 **green**.
4. `eval/k4-search/measure.py` 재측정 표가 갱신되고, 2026-08-25 표의 「강수량·위성·다운스케 0건」이 어떻게 바뀌었는지 **수치로** 기록된다.
5. (ii)·(iii)·(iv) 는 **이 intent 에서 구현하지 않고** 결정·인계 상태로 남는다.

### 완료 주장 전 green 이어야 하는 게이트
| 게이트 | 왜 |
|---|---|
| K2 커버리지 오라클 (`db/ai/seed/k2-coverage-standard.tsv`) | place 기준 4→8 개정의 대조 |
| K2b 그래프 판정기 (`db/ai/tools/k2b_graph_check.py`) | 노드·엣지 완전일치, 등급⑥ 승인목록 일치, 주제 노드 수, 팬아웃 ≤6, 양끝 kind 규약 |
| `gates/tools/migration-drift.sh` | 새 alembic 리비전의 체인 정합 |
| `gates/tools/schema-diff.sh` | (i) 범위는 스키마 무변경임의 증명 |
| `gates/tools/rls-coverage.sh` | D9 에 `lab_id` 가 없다는 전제 유지 확인 |
| pytest `search_golden` (`run_regression.py` 의 두 묶음) | 신규 픽스처 포함 회귀 |
| `eval/k4-search/measure.py` 재측정 | 그래프 확장 전/후 결과집합·순위 실측 |

종료코드 규약 — green **0** · 판정 실패 **1** · 준비 실패 **78**. 준비 실패를 성공으로 보고하지 않는다.

## 사용자가 결정해야 하는 것 (번호로)
1. **실무자 사례를 출처 등급으로 인정할 것인가.** `source_grade` CHECK 는 `1~6`이고 사례는 ①~⑥ 어디에도 없다. ㈎ 등급 ⑥ 으로 싣고 `APPROVED_G6` 에 승인 줄 추가(노드 ⑥ 0건 규약이 깨진다) / ㈏ 등급 ⑦(실무자 요구 사례) 신설 — CHECK 개정 / ㈐ **(권고)** 사례를 등급으로 쓰지 않고 `topic_synonym_six.sql` 선례대로 Ted 가 값을 직접 판정해 내려보낸다.
2. **주제 동의어 9행의 값을 확정해 달라.** 강수량 · 강수 · 강우 · 강우량 · 강수자료 · 강우관측 · 집중호우 · 호우 · precipitation 중 무엇을 「강우·강수」에 싣는가. (`rainfall` 은 사례에 문자열이 없어 후보에서 뺐다.)
3. **지명 별칭 4행(한반도 · Korea · 충청권 · southern Gyeonggi and Chungcheong regions)을 `d9_place_alias` 에 실어 사전-그래프 비대칭을 없앨 것인가.** 실으면 `k2-coverage-standard.tsv` 의 place 기준이 4→8 로 개정된다.
4. **ERA5 · ECMWF · 유럽중기예보센터를 원천표기 노드로 실을 것인가.** 2026-08-25 F-12 ㈎ 의 보류 사유(「15 데이터셋에 그 원천이 0건이라 결과를 안 바꾼다」)가 사례 6건에서 무너진다.
5. **개념 그래프 주제 노드를 4→6 으로 맞출 것인가.** `k2b_graph_check.py:42 CANON_TOPICS` 상수 개정이 따라오고, 그 상수는 2026-08-25 판정을 박제한 자리다.
6. **「관측 기반」(레이더·위성·AWS·disdrometer·CCTV·NWP·재분석)을 온톨로지에 들일 것인가.** `d9_concept.kind` CHECK 4값 개정 + `ONTOLOGY-SCOPE.md` 에 해당 절 **신설**이 선행이다. 들이지 않으면 사례 4건은 어휘 단계에서 계속 0건이다.
7. **변수 사전(강수량·반사도·CAPE·CIN·상대습도·수증기량·바람·온도 및 pressure level)을 열 것인가.** `ONTOLOGY-SCOPE.md §③` 3행이 「범위 밖」으로 닫은 자리라 정본 개정이 먼저다. 열면 manifest digest 전면 무효화 → `requeue` 전면 재처리다.
8. **신규 관계값 4종(`~이 제공한다` · `~을 관측한다` · `~에서 가공되었다` · `~을 보정한다`)을 `d9_concept_edge.relation` CHECK 에 추가할 것인가, 아니면 자료↔자료 사실로 보아 D3 계보·지식 KG 에 남길 것인가.** 권고 = 후자(뒤 두 값). `~이 제공한다` 만 개념↔개념이라 CHECK 개정으로 성립한다.

## 위험
- **manifest digest 변경 → requeue.** discovery digest 는 사전 3종 내용 + 개념 ID/kind/label 을 먹는다. (i) 범위의 19행만 실어도 **모든 연구실의 manifest version 이 바뀐다.** `d3_search_ontology.publish` 의 CAS 와 `requeue` 경로가 함께 회귀 대상이고, 연구실별 `pg_advisory_xact_lock` 직렬화 아래에서 재처리 시간이 든다.
- **옵션 B 의 주제 필터 상호작용 결함.** 2026-09-15 축자 — 「동일 terms에서 topic=가뭄이면 0건, topic=None이면 1건으로 원인 분리했다.」 이 결함이 남아 있으면 **동의어 9행을 실어도 주제 결합 검색은 여전히 0건**이고, 보강이 효과 없는 것으로 오독될 수 있다. 픽스처의 어휘 오라클(순수 함수)과 검색 오라클(결합 경로)을 갈라 둔 이유가 이것이다.
- **자료 쪽 값이 비어 있다.** `source_label` 28건 전부 NULL, 설명 행 30개 `topic` 전부 NULL, `d3_search_evidence` 0건. 후속 2번 전에는 **어휘를 늘려도 붙을 자료 속성이 없다.**
- **기준 TSV 를 적재물에서 생성하려는 유혹.** 그렇게 하면 커버리지 체크가 영원히 green 이 된다. 두 파일을 각각 손으로 옮겨 적는 규약을 깨지 않는다.
- **정본 개정 없이 (ii)·(iii) 를 「보강」에 끼워 넣는 것.** `ONTOLOGY-SCOPE.md` 축자 — 「§③ 의 `[정본 무근거]` 10건은 K1 이 채우지 않는다. **채우려면 정본 개정이 먼저다**」.
- **사례가 정답을 담고 있지 않다.** #2 의 기대답변은 `XXXX` 자리표시자를 쓴다. 이를 정본에 하드코딩하면 `2026-09-15-knowledge-lifecycle.md` 의 O6 축자 「**평가용 답을 개념 정본에 하드코딩하지 않는다**」를 위반한다.

## 미해결 질문
- 현재 정본 28자료에 레이더·AWS·disdrometer·CCTV·NWP 실물이 있는지 **미확인**. 없으면 사례 4건은 어휘를 고쳐도 「자료 없음」이 정답이며, 2026-09-15 보고서 후속 5번(「현재 없는 … 긍정 사례는 별도 승인된 평가 자료가 있어야 검증 가능하다」)과 같은 상황이다.
- `s-ecmwf` / `s-ecmwf-ko` 의 `src < dst` 정규형 정렬 순서는 적재 시 확인이 필요하다.
- 옵션 B 결함의 실제 원인 위치(`interpret.py` / `d9_ontology.py` / `d3_catalog.py` / 자료 쪽 `topic` NULL) **미확정**.

## 범위 밖 (명시 제외)
- 정본 개정 없이 변수 사전·관측 기반 축을 만드는 것.
- `mappings=[]` 해소, 개념↔자료 typed mapping — `R-KNOWLEDGE-LIFECYCLE.md:89` 이 「후속」으로 못 박은 자리.
- 실제 LLM 호출·Sonnet 품질 평가.
- DEV/staging 자료 수정, 재시드, 배포, 커밋·push·PR 게시.
- 기존 12문항 골든셋·핵심 7문항의 대체.

## 확인
- Ted 확인 문장: **「다 권고대로」(2026-09-18)** — 결정 1=㈐, 2=9행 전부, 3=채택, 4=채택, 5=채택, 6=이번 회차 미개방, 7=이번 회차 미개방, 8=후자(관계 CHECK 무변경).
- 프론티어 공집합 확인: 미수행.
- 재개봉 금지: 해당 없음 — 승인 전이다.

## 참조
- 범위 정본: `dev-package/ONTOLOGY-SCOPE.md` §2.7-⑴ · §2.8-⑶ · §③ 3·6·8·9행 · §④-1·④-2·④-3
- 내용 정본: `dev-package/sessions/K1b-ONTOLOGY-CONTENT.md` §A·§B · `:19`(노드 등급⑥ 0건) · `:28`(등급 정의)
- 적재물: `db/ai/seed/k2_ontology_seed.sql` · `db/ai/seed/topic_synonym_six.sql` · `db/ai/seed/k2b_concept_graph_seed.sql`
- 기준: `db/ai/seed/k2-coverage-standard.tsv` · `db/ai/seed/k2b-graph-standard.tsv`
- 판정기: `db/ai/tools/k2b_graph_check.py`
- 스키마: `db/ai/schema.sql:147`(kind CHECK) · `:187`(relation CHECK) · `:189`(source_grade CHECK) · `:198`(정규형)
- 관측: `dev-package/reports/ai-search-dev-review-20260915.md` — 실패표 · `:56`(후속 2번) · 「필요한 후속 순서」 5항
- 실측: `eval/k4-search/README.md:68`
- 평가 형식: `eval/k4-search/golden-set.md` · `client-golden.json` · `heldout-cases.json` · `run_regression.py:76`
- 선행 의도: `dev-package/intent/2026-09-12-ai-search.md` · `dev-package/intent/2026-09-15-knowledge-lifecycle.md`
- 사용자 지시: `dev-package/prd/rounds/R-STAGE3-AI-SEARCH.md:22` 축자 「필요한 용어·관계를 보강하는 것이다」 · 제품 항목 **T-1**(`dev-package/work-items.yaml:826`, `status: open`) 완료 정의 = ⓑ 온톨로지 어휘·관계 확장
- spec: 미작성. Ted 승인 뒤 합성한다.
