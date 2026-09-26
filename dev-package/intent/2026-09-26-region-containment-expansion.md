# Intent: 조건 검색의 지역 조건을 포함 관계로 한 단계 넓힌다 — 「한반도」로 찾으면 그 안의 남한·충청권 자료도 맞춘다
메타 — 발의자: Ted · 작성 2026-09-26 · 승인 2026-09-26 (Ted, 「권고대로 하자」) — 방향 승인 · 승인 2026-09-26 (Ted, 결정 1~4 권고안 채택 · 원문 「권고안대로핡」) · 선행 intent `dev-package/intent/2026-09-21-evidence-promotion.md` 「판정 결과 — 2회차 지역(2026-09-26)」 · 조사 기준 트리 `feat/region-round2`(develop `501ef439` + PR #174, HEAD `1b8c75a8`) · path:line 재확인 기준 develop `e4bd039a`(PR #174 병합본 — 아래 줄번호는 이 트리 기준)

## 문제
- 실무자 14사례 중 6사례(PC-1-3 · 1-4 · 2-3 · 2-4 · 2-6 · 2-7)가 지역을 「한반도」로 묻는다.
  - 2회차 판정으로 정본이 지역을 확정했다. 기상청 4건(seq 1·2·19·20)은 「남한」, GK-2A(seq 6)는 「한반도」다.
  - D9 그래프에는 「남한 안에 있다 한반도」 엣지를 실었다(`db/ai/seed/region_south_korea.sql` · 0012).
- 두 조건 검색 경로 모두 지역을 표기가 같은지만 비교한다. 그래서 「한반도」 조건으로 남한 자료가 나오지 않는다.
  - 2회차 측정에서 「한반도」 region probe 5건은 두 경로 모두 red였다. 초안을 넣었을 때와 뺐을 때 결과가 같다.
- 반사실 측정(판정 근거 아님)도 했다. 경로 1 표기 사전에 그래프 한 홉(남한 · 충청권 · Korea)을 더하면 결과가 이렇다.
  - reviewed만: 1/5 green(PC-1-4#m2 · seq 1).
  - 초안 포함: 5/5 green.
  - 규칙 단위로는 `region-from-lineage-parent`가 4건을 열고 역전은 0이다.
  - 출처: `dev-package/reports/evidence-promotion/round-2-2026-09-26/region-probe-states.json`(커밋본).

## 현재 상태 (path:line 으로 확인한 사실)

### 경로 1 — 조건 검색(`plan_query` → `d3_client_search.candidates` → `client_search.evaluate`)
- 지역 어휘는 `contracts/search/semantics.json:11-15` `regions`다. 식별자는 seoul · jeju · korean_peninsula이고, korean_peninsula의 별칭은 「한반도」 하나다.
  - 코드 생성: `contracts/codegen/gen_search_semantics.py:7-11`이 두 파일을 만든다. `services/core-api/src/colab_core/kernel/search_semantics.py`와 ai-service의 같은 파일이다.
  - 생성물 내용은 `SEMANTICS`와 `SEMANTIC_VERSION`(파일 sha256)이다.
- 조건이 만들어지는 자리는 셋이다. 셋 모두 의미 식별자(`korean_peninsula`)로 만든다.
  - 질의문: `app/client_search.py:77-80` `mentions()`가 별칭을 부분 문자열로 찾는다. 지역이 하나면 `:109-113`이 `c['region']`을 세우고, 둘 이상이면 되묻는다.
  - 연구 조건: `:32-34`가 `context.research.region`이 `SEMANTICS['regions']`의 키인지 검사한다.
  - 기준 파일(reference_match): `app/routes/catalog.py:691-697`이 기준 파일의 region을 `canonical()`로 바꾼다. 질의 지역과 다르면 되묻는다.
- 경로 1 진입 조건은 `client_search.py:197-200` `recognized`다.
  - 지역 하나만으로는 진입하지 않는다. format·representation과 region이 함께 있거나, finest·latest·reference_match·research 문맥이어야 한다.
  - 그 밖의 질의는 경로 2로 간다(`catalog.py:508-512`).
- 매칭은 두 겹이다.
  - SQL 후보(`domains/d3_client_search.py:56-60`): `[식별자, *별칭]`을 압축한 집합(공백·`_`·`-` 제거, 소문자)에 `facts->>'region'`이 들어 있는지 IN으로 본다. 대상은 `e.status='reviewed'`인 현재 본체 파일만이다(`:89-90`).
  - 판정(`client_search.py:244-245`): `canonical(fact_region,'regions') == wanted`다.
  - `canonical()`(`:69-74`)은 별칭이면 키로 바꾸고, 아니면 압축한 원문을 그대로 돌려준다.
  - 그래서 「남한」 사실은 `'남한' != 'korean_peninsula'`가 되어 contradicted로 판정된다.
- 응답:
  - 카드 근거는 `catalog.py:734`의 고정 문장 「현재 파일의 검토된 근거에서 해석된 조건을 함께 확인했어요」다.
  - 조건별 판정은 `assessment.comparisons[].checks`에 실린다(`contracts/seams/fe-core.yaml:5437-5475`). 값은 `supported|unknown|contradicted` enum 맵이고 설명 칸은 없다.
- 네트워크·모델 호출은 0이다. 모듈 머리말(`client_search.py:1`)에 「No database or model side effects」라고 적혀 있다.

### 경로 2 — 자연어 검색의 파일 근거(`search_evidence_conditions`)
- 지역 파싱(`app/search_evidence_conditions.py:43-47`)은 LLM 해석과 무관하게 원문에서 한다.
  - 고정 목록 `['제주','한반도','서울','강원','전라','경상']`에서 첫 일치를 고른다.
  - 「충청」과 「경기」가 함께 있으면 `경기남부충청`, 「시군구」가 있으면 `대한민국시군구`로 정한다.
  - 「남한」은 목록에 없다.
- 판정(`:88-90`): `_compact(actual)==_compact(wanted)`이면 supported이고, 아니면 unknown이다. contradicted로 판정하지 않는다.
  - 테스트 `tests/test_search_evidence_conditions.py:68-69`가 「모르는 지역을 지리적으로 배타라고 선언하지 않는다」를 고정한다.
- 쓰임(`catalog.py:552-565`): 주제가 하나이고 reviewed 근거가 있을 때만 쓴다.
  - `candidates()`(`:106-120`)는 모든 조건이 supported인 자료를 `evidence_ids`로 올린다.
  - `supported_facts()`(`:123-151`)는 카드의 「파일 근거」 한 줄을 만든다. 괄호 세부는 `기간`·`파일 역할`에만 붙는다(`:145`).
  - 근거는 `d3_search_evidence.read_reviewed`(`catalog.py:553`)로 읽으므로 reviewed만 본다.
- 같은 요청의 LLM 해석은 이미 그래프를 한 홉 넓힌다.
  - ai-service `expand_by_graph`(`services/ai-service/src/colab_ai/domains/d9_ontology.py:184-243`)가 한다. 하향 전용 · 깊이 1 · 팬아웃 6(`:130`, `:227`) · `expandable` 경계를 지킨다.
  - 「한반도」를 「남한」·「충청권」으로 넓혀 `answer['terms']`와 `answer['expansions']`(core `services/core-api/src/colab_core/app/relay.py:366`, `:472`)로 돌려준다.
  - 이 값은 tsvector 후보(`d3_catalog.search_datasets`)와 「낱말 일치」 근거에만 쓰인다. `search_evidence_conditions`는 읽지 않는다.
- ai-service가 응답하지 않으면 경로 2 전체가 503이다(`catalog.py:518-530`).

### core가 그래프를 얻을 수 있는 길 (D9 DB 무접속)
- D3에 게시된 연구실별 manifest에는 다이제스트만 있다.
  - 위치: `d3_search_ontology_release/head` · `domains/d3_search_ontology.py:24-27`, `:123-126`.
  - 형태(`ports/ontology.py:15-32`): `{protocol, entries:{'discovery'|'concept:<id>': sha256}, version}`.
  - 라벨·엣지·별칭이 없다. core는 이것만으로 「한반도」의 하위를 알 수 없다.
  - 그래서 방향 승인 문안의 「D3에 있는 manifest를 읽어 로컬로 편다」는 현재 구조로는 할 수 없다.
- 그래프 내용은 ai-service `/ontology-concepts` lookup(`services/ai-service/src/colab_ai/app/main.py:272`)으로만 온다.
  - 응답은 개념별 한 홉 증명(node · edges · neighbors)이고, `MAX_CONCEPTS=6`이다.
  - core는 `validate_lookup`(`ports/ontology.py:35-58`)으로 D3 head 다이제스트와 대조한다.
  - 호출하는 쪽은 `OntologyHttpClient`(`app/ontology_client.py:37-41`, 기본 timeout 5초 `:19`)다.
  - 지금은 오프라인 색인 갱신에서만 쓰고(`app/search_refresh_tools.py:57`, `:110`), 검색 요청 경로에서는 부르지 않는다.
- D3의 개념 선택(`d3_search_concept_match` · `domains/d3_search_annotations.py`)은 자료별로 고른 개념 라벨이다. 지역 포함 관계는 담지 않는다.
- manifest의 `discovery` 다이제스트에는 `SEMANTIC_VERSION`이 들어 있다(`services/ai-service/src/colab_ai/app/ontology_manifest.py:12`, `:30-31`).
  - `semantics.json`을 바꾸면 manifest version이 바뀐다. 그러면 기존 D3 바인딩이 무효가 되고(`d3_search_ontology.py:78-84` `_VALID`) requeue·재바인딩이 필요하다.
  - 0012 적용도 `concept:p-korea-peninsula`와 discovery를 이미 바꾼다. 따라서 재게시는 어차피 한 번 필요하다.

### 그래프와 데이터 (2회차 입력 `input-payload.json` · `regionTrace`)
- 「한반도」(`p-korea-peninsula`, expandable=t)의 직계 하위(`안에 있다`)는 두 개다. 충청권(E2-1)과 남한(E2-2026-09-26)이다.
  - 같은 말은 Korea다(`db/ai/seed/k2b-graph-standard.tsv:102`, `:123-124`).
  - 팬아웃 2는 상한 6 이하다.
- 별칭 `d9_place_alias`:
  - 남한 ← 남한 · 대한민국
  - 충청권 ← 충청권 · southern Gyeonggi and Chungcheong regions
- 사실 region 값:
  - reviewed: 남한(1·2·19·20) · 한반도(6) · 경기남부충청(7) · 대한민국시군구(13·14).
  - 초안: 남한(3·4·5, `region-from-lineage-parent`) · 경기남부충청(8~12) · 한반도(21~24, bbox) · 전지구(16).
- 표기가 정확히 같아야만 맞추므로, 다음 두 값은 이번 확장에 걸리지 않는다. 의도한 보수성이다.
  - 「경기남부충청」은 충청권 노드의 라벨·별칭 어느 것과도 다르다.
  - 「대한민국시군구」는 남한 별칭 「대한민국」과 다르다.

### 사례 오라클 (`eval/k4-search/practitioner-conditions.json`)
- 「한반도」 region probe 5건은 모두 `measureOnlyProbes`다. pytest는 이것을 green으로 세지 않는다(`modes.measure_only`).
  - PC-1-3#m3 · PC-1-4#m2 · PC-2-3#m2 · PC-2-4#m1 · PC-2-7#m1.
- 사례 등급:
  - PC-1-4 · 2-4 · 2-7 = full. 이미 답 가능으로 집계되고, region은 deferred에 적혀 있다.
  - PC-1-3 · 2-3 = partial.
  - PC-2-6 = blocked.
- 경로 2 녹화 질의 집합에는 「한반도」 질의가 0건이다. 그래서 경로 2에서는 잴 자리가 없다.

## 원한 결과 (proposed outcome)
- 「한반도」 지역 조건은 다음 reviewed 파일에서 supported가 된다. 두 경로가 같은 표를 읽는다.
  - 사실 region이 한반도(별칭 포함)인 파일.
  - 사실 region이 그 직계 하위(남한 · 충청권과 그 별칭)인 파일.
- 반대 방향은 열지 않는다. 「남한」 조건으로 한반도 자료가 나오지 않는다. 두 단계 아래와 초안도 열지 않는다.
- 맞은 지역이 질의어와 다르면 카드 근거가 그 사실을 적는다(결정 2).
- ai-service가 없어도 경로 1은 지금처럼 동작한다. 권고안 ㈎는 네트워크에 의존하지 않는다.

## 가치 가설
- 「한반도」로 묻는 실무자가 기상청 남한 관측 자료를 후보로 받는다. 표기 차이 때문에 빈 결과를 받는 일이 없어진다.
- 확인 방법: 아래 두 가지를 본다. 이것이 PR 요약 「원한 결과 ↔ 실제 ↔ 근거」 표의 근거가 된다.
  - 완료 정의의 probe 5건 green 수(경로별 · reviewed만 · 다음 승격 후).
  - 역방향 금지 테스트가 계속 red로 막히는지.

## 영향 범위
- 사용자 / 화면: 「한반도」 질의의 후보 집합과 「파일 근거」 한 줄이 바뀐다. 화면 컴포넌트는 바꾸지 않는다(결정 2 ㈎ 기준).
- 서비스 · 스키마 · 계약:
  - `contracts/search/semantics.json`에 하향 표를 추가하고, 두 kernel 생성물을 다시 만든다.
  - core-api의 `client_search`·`d3_client_search`·`search_evidence_conditions`를 고친다.
  - 드리프트 게이트를 새로 만들고 오라클 JSON을 고친다.
  - DB 스키마는 바꾸지 않는다.
- 계약 파괴 여부: 아니오(결정 2 ㈎). ㈏를 고르면 `fe-core.yaml`에 칸이 추가된다. 파괴는 아니지만 Ted 서명이 필요하다.

## 제약
- core-api는 D9 DB에 접속하지 않는다. 그래프 사실은 Port 값이나 계약으로만 받는다.
- 경로 1은 모델·네트워크에 의존하지 않는다. 지금 성질을 유지한다.
- 초안은 조건 검색 대상이 아니다(선행 intent 결정 1).
- UI 문구에 내부 기법 이름(온톨로지·계보)을 쓰지 않는다(`2026-09-25-search-rationale-separation.md` Q7).
- 모델을 부르는 eval은 로컬에서 실제 모델로 실행한다.

## 설계안

### ㈎ 계약 어휘에 하향 한 홉 표를 싣고, 두 경로가 로컬에서 넓힌다 — 권고
- `semantics.json`에 `regionWithin`(가칭)을 더한다. 구조는 부모 식별자 → 직계 하위 라벨 → 그 하위의 별칭이다.
  - 예: `{ "korean_peninsula": { "남한": ["대한민국"], "충청권": ["southern Gyeonggi and Chungcheong regions"] } }`
  - 기존 `regions` 별칭에는 넣지 않는다.
  - 이유: 별칭에 넣으면 `mentions()`·`canonical()`이 「남한」 질의를 `korean_peninsula`로 바꾼다. 그러면 한반도 자료(seq 6)까지 나오는 상향 누수가 생긴다.
  - 반사실 측정기(`region_probe_states.py:62-65`)는 별칭 목록에 더하는 방식이었다. 따라서 그 측정은 방향을 검증하지 않았다.
- core kernel에 공통 도우미 하나를 둔다. `region_scope(wanted)`가 `{압축 표기: 경유 부모|None}`을 돌려준다.
  - 경로 1: SQL IN 집합(`d3_client_search.py:58-59`)과 판정(`client_search.py:244-245`)이 이 집합을 쓴다. 판정은 「사실 표기 ∈ 집합」이다.
  - 경로 2: `assess`(`search_evidence_conditions.py:88-90`)가 같은 도우미를 쓴다. 파싱 결과 「한반도」를 식별자로 옮기는 매핑이 한 줄 필요하다. 불일치는 지금처럼 unknown이다.
- 표의 원본은 D9 그래프다. 새 드리프트 게이트가 둘을 대조하고, 어긋나면 red를 낸다.
  - 대조 대상: `db/ai/seed/k2b-graph-standard.tsv`의 `안에 있다` 엣지 · expandable · 팬아웃, 그리고 `d9_place_alias`.
- 장점:
  - 결과가 결정적이다. 지연·가용성 영향이 없다.
  - 경로 1의 모델·네트워크 무의존 성질이 유지된다.
  - 측정기가 제품과 같은 코드로 잰다.
- 비용:
  - 그래프 사실을 계약에 한 번 더 적는다. 그래서 그래프를 개정할 때마다 계약도 함께 개정해야 한다. 어긋나면 게이트가 막는다.
  - `SEMANTIC_VERSION`이 바뀌므로 manifest 재게시와 requeue가 한 번 필요하다. 0012 반영과 같은 창에서 하면 한 번으로 끝난다.

### ㈏ 요청마다 ai-service lookup을 부르고, 실패하면 표기 일치로 물러난다
- 경로 1: region 조건이 서면 `OntologyHttpClient.lookup`을 짧은 timeout으로 부른다.
  - D3 head와 `validate_lookup`으로 대조한다.
  - 증명의 edges 가운데 `안에 있다`이고 dst가 질의 개념인 것만 골라 하위로 넓힌다.
- 경로 2: 추가 호출 없이 이미 받은 `answer['expansions']`를 쓴다. relation이 `안에 있다`이고 parent가 질의 지역인 항목이다.
- 문제점:
  - 경로 1이 네트워크에 의존하게 된다.
  - ai-service 상태에 따라 같은 질의가 다른 답을 낸다. 경로 1 응답은 지금 `degraded:false` 고정(`catalog.py:745`)이므로 이를 알릴 칸도 새로 필요하다.
  - 연구실 head가 게시되지 않았으면 manifest가 없어 항상 물러난다.
  - lookup 증명은 양방향 이웃을 담는다. 방향 거르기를 core가 다시 구현해야 한다.
  - 요청당 최대 5초 지연이 생긴다.

### ㈐ 증거 적용 시점에 조상 지역을 사실로 미리 적는다
- `dataset_evidence_backfill`이 남한 파일 facts에 `regionWithin:["한반도"]`를 붙인다. 매칭은 `region OR regionWithin`으로 한다.
- 문제점:
  - 사람이 검토하지 않은 파생값이 reviewed facts에 섞인다.
  - 그래프를 개정할 때마다 전 파일 facts가 바뀐다. 이번 판에서만 143파일이 바뀐다.
  - `SearchEvidenceFacts`에 성분이 늘어 계약을 개정해야 한다.
  - DEV 적재 자료에만 적용되고, 사용자가 올린 자료의 근거에는 적용되지 않는다.

### 권고
- ㈎를 권한다.
  - 경로 1의 결정성을 지킨다.
  - 두 경로가 한 표를 공유한다.
  - 방향·깊이·팬아웃을 게이트로 고정한다.
  - 네트워크가 끊겨도 확장 결과가 같다.
- ㈏ 가운데 「경로 2는 `expansions` 재사용」은 추가 비용이 없어 매력적이다. 하지만 두 경로가 서로 다른 원본을 읽게 되므로 채택하지 않는다.

## 안전 규칙 (구현이 테스트로 고정할 것)
1. 하향 전용. 표는 부모 → 하위 방향만 갖는다.
   - 「남한」 질의로 한반도 자료가 supported가 되지 않는지 확인하는 red 테스트를 먼저 세운다.
   - 「남한」은 아직 경로 2 목록과 경로 1 별칭 어디에도 없다.
2. 깊이 1. 표에는 직계만 싣고, 코드는 전이 폐포를 만들지 않는다. 게이트는 표 항목마다 D9 엣지 1개가 있는지 본다.
3. 다음 부모는 표에 싣지 않는다(`d9_ontology.py:227`과 같은 규칙).
   - `expandable=false`인 부모.
   - 직계 하위가 6을 넘는 부모. 이 경우 일부만 싣지 않고 전체를 뺀다.
4. reviewed만 매칭한다. 두 경로의 근거 읽기가 이미 reviewed 전용이다(`d3_client_search.py:89` · `catalog.py:553`).
   - 초안 region은 확장 대상이 아니다.
   - 확장은 「질의어 → 표기 집합」 쪽에서만 한다.
5. 압축 후 표기가 정확히 같아야 맞춘다. 부분 문자열로 넓히지 않는다(「대한민국시군구」 ≠ 「대한민국」).
6. reference_match는 기준 파일의 지역을 그대로 쓴다(`catalog.py:694-697`). 「같은 지역」은 포함 관계와 다른 질문이기 때문이다.

## 완료 정의
- ① 코드
  - 경로 1·2가 같은 도우미로 「한반도」의 표기 집합을 매칭한다. 집합은 한반도 · Korea · 남한 · 대한민국 · 충청권 · southern Gyeonggi and Chungcheong regions다.
  - 단위 테스트: 하향 supported · 상향 금지 · 깊이 2 금지 · 초안 불참 · 부분 문자열 금지.
- ② 경로 1 측정(일회용 DB · `run_measurement.sh`와 같은 절차 · 반사실 패치 없이 제품 코드로 잰다)
  - reviewed만: 1/5 green(PC-1-4#m2).
  - 초안 포함: 5/5 green.
  - 역방향과 기존 probe 역전은 모두 0.
- ③ 다음 승격 회차에서 `region-from-lineage-parent`(초안 4 · seq 3·4·5 남한 등)의 제품 경로 기여를 다시 잰다.
  - 결정 5 지름길(기여 ≥1 · 두 경로 역전 0)이 서면 승격한다.
  - 그 뒤 reviewed만으로 5/5 green을 목표로 한다.
- ④ 경로 2: 「한반도」 녹화 질의 5건을 추가한다(결정 3). 같은 5 probe가 경로 2에서도 green인지 본다.
  - 이번 PR은 규칙 기반 해석 녹화로 잰다. 실모델 녹화는 별도 승인 대기다(모델 호출 eval이다).
- ⑤ 오라클: 5 probe를 `measureOnlyProbes`에서 `probes`로 옮기고, 각 사례 deferred의 region 항목을 닫는다.
- ⑥ 14사례 점수판 전후를 기록한다. 등급 수치는 3/5/3/3에서 바뀌지 않을 가능성이 높다.
  - 이번 변경이 실제로 바꾸는 것은 region 축이 실제 판정으로 서는 것이다. 사례 등급 이동은 기대하지 않는다.
  - 사례별로 이번 변경 뒤에도 답 가능을 막는 요인은 아래와 같다.
  - PC-1-3(partial → partial):
    - DEV 28건에 NWP 원천 자료가 0건이다.
    - 기간 교집합 계산 기능이 없다.
    - platform(지상·모형) 축이 초안이라 승격 대기다.
    - region probe 5중 4건 몫(seq 3·4·5 남한)은 `region-from-lineage-parent` 승격 대기다.
  - PC-1-4(full 유지):
    - 이 사례의 region probe는 seq 1 reviewed로 즉시 green이다.
    - 남은 deferred: 「1시간 이하」 범위 술어가 없다(cadence는 등호 비교만 한다).
    - rn15의 공간해상도가 정본에 없다.
    - seq 3 해상도는 `native-resolution-carried` 초안이다.
  - PC-2-3(partial → partial):
    - DEV 28건에 NWP 원천이 0건이다.
    - 격자 해상도 대조 문장이 없다.
    - platform(모형) 축이 초안이라 승격 대기다.
    - region probe는 `region-from-lineage-parent` 승격 대기다.
  - PC-2-4(full 유지):
    - region probe(seq 2·4)는 seq 4 초안 남한이 승격되어야 green이다.
    - 남은 deferred: 「1시간 이하」 범위 술어와 결측률 비교가 없다.
  - PC-2-6(blocked → blocked): 지역과 무관하다.
    - SearchEvidenceFacts 15종에 pressure level 성분이 없다(결정 2-ⓑ 미개봉).
    - DEV 28건에 ERA5 pressure-level 자료가 없다.
  - PC-2-7(full 유지):
    - region probe(seq 2·4·5)는 seq 4·5 초안 남한이 승격되어야 green이다.
    - 남은 deferred: DEV 28건에 결측률 값이 없어 후보가 0건이다. 순위도 재지 않는다.
    - 2016~2025 전 기간을 덮는 자료가 없다.
- ⑦ dev 반영
  - 다음 두 가지가 먼저 되어야 dev에 남한 reviewed 사실이 생긴다. 이 intent의 dev 확인은 그 뒤에 한다.
    - 2회차 payload의 dev 반영 GO.
    - ai 체인 0012 적용.
  - manifest 재게시와 requeue는 같은 창에서 한 번만 한다.

## 게이트
- 드리프트 게이트(신설 · `region-within-drift` + `region-within-drift-selftest`): `semantics.json` `regionWithin`을 `k2b-graph-standard.tsv`의 지명 `안에 있다` 엣지·expandable·팬아웃, 그리고 `d9_place_alias`와 대조한다.
  - 종료 코드: 입력 부재 78 · 불일치 1 · 일치 0.
- 코드 생성 일치: 두 kernel의 `search_semantics.py`가 생성물과 같은지 대조한다.
  - 기존 게이트 `generated-up-to-date`가 한다 — `contracts/codegen/manifest.toml`의 `search-semantics-core`·`search-semantics-ai` 두 등기(재생성 뒤 byte-diff). 새로 세우지 않는다.
- core-api pytest: `test_client_search.py` · `test_search_evidence_conditions.py` · `test_practitioner_conditions.py`(probe 승격 후).
- 측정기: `eval/k4-search/measure_draft_contribution.py --seed-dev-like`(일회용 DB · 모델 호출 0).
- 경로 2 녹화 추가분은 실제 모델로 로컬에서 실행한다 — 별도 승인 대기. 이번 PR은 규칙 기반 해석(`LiteralInterpreter`) 녹화로만 잰다.
- 계약: 기본은 `fe-core.yaml` 무변경(결정 2 ㈎)이다. 바꾸면 계약 게이트와 Ted 서명이 필요하다.

## 위험
- 상향 누수: 구현이 편의상 별칭에 넣으면 「남한」 질의로 한반도 자료가 나온다. 안전 규칙 1의 red 테스트를 먼저 세운다.
- manifest 재바인딩:
  - `SEMANTIC_VERSION`이 바뀌면 discovery 다이제스트가 바뀌고, D3 바인딩이 전부 무효가 된다.
  - 재게시 전까지 「관련 개념」 근거가 사라진다.
  - 0012 반영과 한 창에 묶고, dev 배포 절차에 requeue를 적는다.
  - dev 배포 절차(이 PR에서는 실행하지 않는다): ① ai 체인 0012 적용 → ② 연구실별 ontology manifest 재게시(새 `SEMANTIC_VERSION`의 discovery 다이제스트) → ③ D3 바인딩 requeue·재바인딩 → ④ 「관련 개념」 근거가 돌아왔는지 확인. ①~③은 한 창에서 한 번만 한다.
- 계약·그래프 이중 기재: 드리프트 게이트가 유일한 방어선이다. 게이트가 없으면 ㈎를 채택하지 않는다.
- 경로 2 질의 누락: 「한반도」 녹화 질의가 없으면 경로 2 완료를 주장할 수 없다. 녹화에 모델 비용이 든다.
- 기대 관리: 이번 변경 뒤에도 6사례 모두 다른 축이 답 가능을 막는다.
  - PC-1-3: NWP 부재 · 기간 교집합 · platform 초안 · region 초안 승격.
  - PC-1-4: 「1시간 이하」 범위 술어 · rn15 해상도 부재 · seq 3 해상도 초안.
  - PC-2-3: NWP 부재 · 격자 해상도 대조 · platform 초안 · region 초안 승격.
  - PC-2-4: 「1시간 이하」 범위 술어 · 결측률 비교 · region 초안 승격(seq 4).
  - PC-2-6: pressure level 성분 · ERA5 자료 부재.
  - PC-2-7: 결측률 값 부재 · 2016~2025 전 기간 자료 부재 · region 초안 승격(seq 4·5).

## Ted 결정 (번호)
1. 설계안
   - ㈎ 계약 표 + 드리프트 게이트(권고).
   - ㈏ 요청마다 lookup, 실패하면 표기 일치로 물러남.
   - ㈐ 적용 시점에 facts에 미리 기재.
2. 설명 표면
   - ㈎ 계약 무변경(권고): 경로 2 「파일 근거」의 조건 세부에 「지역(남한 — 한반도 안의 지역)」을 붙인다. 경로 1의 고정 문장과 `checks.region=supported`는 그대로 둔다.
   - ㈏ `SearchAssessment.comparisons[]`에 경유 부모 칸을 신설한다. 계약 개정이며 Ted 서명이 필요하다.
3. 경로 2 측정
   - 「한반도」 녹화 질의 5건 추가(권고). 5 probe 조건을 자연어로 옮기고, 실제 모델로 로컬에서 녹화한다.
   - 또는 단위 테스트로만 확인.
4. 완료 기준
   - probe 기준(권고): 5 probe가 두 경로에서 green이면 완료로 본다. reviewed만 1/5는 즉시, 5/5는 다음 승격 후다. 점수판 수치 불변을 수용한다.
   - 반대안: 「6사례 답 가능」을 등급 수치로 요구한다. 그러려면 NWP · pressure level · 범위 술어 · 결측률 축을 다룰 별도 intent가 먼저 필요하다.

## 판정 결과 — 결정 1~4 (승인 2026-09-26 (Ted, 결정 1~4 권고안 채택 · 원문 「권고안대로핡」))
- 결정 1 = ㈎ 계약 표 + 드리프트 게이트.
  - 표 모양(`contracts/search/semantics.json` `regionWithin`):
    `{ "korean_peninsula": { "place": "한반도", "placeAliases": ["Korea"], "within": { "남한": ["대한민국"], "충청권": ["southern Gyeonggi and Chungcheong regions"] } } }`.
  - `place` = 의미 식별자가 가리키는 D9 지명 노드 라벨(게이트가 노드를 찾는 열쇠). `placeAliases` = 그 노드 자신의 별칭(`d9_place_alias`에서 `place_name=place`이고 자기 자신이 아닌 행). 사실 쪽에서만 맞추고 질의 인식(`mentions()`)에는 넣지 않는다 — 「Korea」를 질의 별칭에 넣으면 「South Korea」·「Korean」 같은 질의가 부분 문자열로 한반도가 된다.
  - `within` = 직계 하위 라벨 → 그 하위의 별칭. 기존 `regions` 별칭에는 넣지 않는다(상향 누수).
  - 도우미 = `services/core-api/src/colab_core/kernel/region_scope.py`(생성물 `search_semantics.py`는 손으로 고칠 수 없어서 별도 커널 모듈이다). `region_scope(wanted, expand=True)` → `{압축 표기: 경유 하위 라벨|None}`.
  - reference_match는 넓히지 않는다(안전 규칙 6). 경로 1은 `plan['intent']=='reference_match'`이면 `expand=False`로 SQL·판정 둘 다 부른다.
  - 드리프트 게이트 = `gates/tools/region-within-drift.sh`(+ `-selftest`). 대조 입력 = `db/ai/seed/k2b-graph-standard.tsv`(지명 노드·`안에 있다` 엣지·expandable) + `db/ai/seed/*.sql`의 `d9_place_alias` 행.
- 결정 2 = ㈎ 계약 무변경. 경로 2 「파일 근거」 세부에 `지역(남한 — 한반도 안의 지역)`을 붙인다. 표기가 같아 맞은 지역은 지금처럼 `지역`만 적는다. 경로 1 고정 문장·`checks.region`은 그대로다. `fe-core.yaml` 무변경.
- 결정 3 = 「한반도」 경로 2 질의 5건 추가 — **실모델 녹화는 별도 승인 대기**. 이번 PR은 모델을 부르지 않는다.
  - 5 probe마다 `pathBQuery`(자연어)를 달고, 해석은 `eval/k4-search/interpret-fixture.json` 관례대로 규칙 기반 해석기(`LiteralInterpreter().interpret(query)`, 사전·그래프 확장 없음) 출력을 녹화 항목으로 싣는다(`recordedFrom` 명기 · `modelCalls` 0).
  - 경로 2 판정은 측정기 곁가지 군(`probe_B` — 결정 5의 기여·역전 계산에 넣지 않는다)으로 낸다. green = 파일 근거 조건 후보(`search_evidence_conditions.candidates`의 포함 집합)가 expectSeq를 모두 담고 forbidSeq를 담지 않음. 전체 검색 결과(낱말 일치 포함) 기준 green은 참고 열로만 낸다.
  - 경로 2 파서에 「남한」을 더한다(목록 끝 · 「남한강」「남한산」 제외). 이유: 상향 금지 시험이 경로 2에서 빈 시험이 되지 않게 하려는 것이다. 「남한」은 의미 식별자가 아니므로 표기 일치로만 맞추고 넓히지 않는다.
- 결정 4 = probe 기준. 점수판 등급 수치 불변(3/5/3/3 — `practitioner-conditions.json` 2회차 집계 기준)을 수용한다.

## 설계트리 (grill-me 결과)
- Q1 확장은 조건 생성 시점과 매칭 시점 중 언제 하는가?
  - A: 매칭 직전(권장안 · 두 경로가 같은 시점). `conditions.region`은 식별자 그대로 두므로 계약·receipt가 바뀌지 않는다. 도우미가 매칭 직전에 표기 집합으로 넓힌다.
- Q2 core가 D3 manifest만으로 넓힐 수 있는가?
  - A: 아니다. manifest는 다이제스트뿐이다(`ports/ontology.py:15-32`). 그래프 내용은 lookup 증명으로만 온다.
- Q3 반사실 측정처럼 별칭에 더하면 되는가?
  - A: 안 된다. `canonical()`·`mentions()`가 양방향이 되어 상향 누수가 생긴다.
  - Q3a 그렇다면 1/5·5/5 측정값은 유효한가?
    - A: 하향 probe 5건에 대해서는 유효하다. 상향 금지는 재지 않았으므로 새 red 테스트로 잰다.
- Q4 초안 사실도 확장 대상인가?
  - A: 아니다. 근거 읽기가 reviewed 전용이고, 확장은 질의 쪽에서만 한다.
- Q5 경기남부충청·대한민국시군구를 남한·충청권에 잇는가?
  - A: 범위 밖이다. 이으려면 별칭·그래프 판정이 따로 필요하다.

## 미해결 질문
- (해소) 코드 생성 드리프트 대조는 `generated-up-to-date`가 한다(`contracts/codegen/manifest.toml` `search-semantics-core`·`search-semantics-ai`).
- 경로 1 `recognized`는 지역 하나만으로 서지 않는다. 따라서 실무자 원문 질의는 대부분 경로 2로 간다. 경로 1 probe green이 실제 질의에 닿는 비율은 따로 재야 한다.

## 범위 밖 (명시 제외)
- 깊이 2 이상 확장, 상향 확장, bbox 기반 공간 포함 판정.
- reference_match의 지역 판정.
- 경기남부충청 ↔ 충청권, 대한민국시군구 ↔ 남한 연결.
- 지역 초안 규칙의 승격 자체. 다음 승격 회차에서 한다(선행 intent 결정 3·5).
- PC-2-6의 pressure level, NWP 원천 부재, 「1시간 이하」 범위 술어, 결측률 값.

## 확인
- 프론티어 공집합 확인: <미기입>
- Ted 확인 문장(원문 그대로): "권고대로 하자" (2026-09-26 · 방향 승인)
- Ted 결정 확인(원문 그대로): "권고안대로핡" (2026-09-26 · 결정 1~4 권고안 채택 — 「권고안대로 한다」의 오타)
- 재개봉 금지: 예(결정 1~4 확정 · 결정 3 의 실모델 녹화만 별도 승인 대기)

## 참조
- 선행: `dev-package/intent/2026-09-21-evidence-promotion.md` 「판정 결과 — 2회차 지역(2026-09-26)」
- 측정: `dev-package/reports/evidence-promotion/round-2-2026-09-26/`(`region_probe_states.py` · `region-probe-states.json` · `before-dev-current/`)
- 오라클: `eval/k4-search/practitioner-conditions.json`
- 그래프: `db/ai/seed/region_south_korea.sql` · `db/ai/seed/k2b-graph-standard.tsv` · `services/ai-service/src/colab_ai/domains/d9_ontology.py`
- 근거 패널 규칙: `dev-package/intent/2026-09-25-search-rationale-separation.md`(Q6·Q7) · `2026-09-26-rationale-facts-wording.md`
- 결정: 〈N〉 (병합 시 기입)
