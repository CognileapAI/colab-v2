# Intent: 검색 근거 사실 문구 다듬기 — 파일 근거 항목의 출처 경로 제거 · 낱말 일치에서 주제 라벨 분리
메타 — 발의자: Ted · 작성 2026-09-26 · 승인 **Ted 2026-09-26**(확인 문장 원문 「좋아 진행」 — 설계트리 Q1~Q2c 권장안 그대로 · 미해결 질문은 아래 「해소」의 오케스트레이터 결정). 이 서명을 적은 커밋이 승인이다(`README.md` 「승인 = 커밋」) · 선행 intent `dev-package/intent/2026-09-25-search-rationale-separation.md`(승인 Ted 2026-09-26 · 패널·근거 종류·사실 규칙의 정의처)

## 문제
- 발의: Ted가 dev에서 새 「AI」 근거 패널 화면을 보고 두 가지 다듬기를 요청했다. 원문 「1,2 둘다 intent로 올리자」(2026-09-26).
- 실측 근거(모두 같은 캡처)
  - 가지 `origin/deploy/dev-592ff4b7` · 파일 `dev-package/reports/search-rationale-panel/20260926-dev/dev-search-response-llm.json`
  - dev `592ff4b7693d` · 운영자(무소속) 계정 · `POST /api/v1/dataset-searches`
  - 질의 「강우 예측 pred_sample.npy 파일의 바로 앞 입력 데이터셋」 · `interpretation: llm` · `topic: 강우·강수` · 결과 5건
  - 같은 폴더 `dev-queries.json`은 질의 4건 모두 `topic: 강우·강수`로 기록했다.
- ① 파일 근거 항목이 출처 경로까지 싣는다
  - 실측(카드 `pred_sample` · `rationaleFacts[kind=evidence]`)
    > pred_sample.npy에서 파일 역할(예측 결과) 조건이 맞았어요 (출처 01.level-data/01.precipitation/DATASETS.md · seq 5 pred_sample · DATASETS.md#01.level-data/01.precipitation/DATASETS.md#seq-5)
  - 괄호 안은 저장소 상대 경로·순번·앵커다. 검색 사용자에게 「왜 이 결과인가」를 더하지 않는다. 한 항목이 패널 폭에서 여러 줄로 늘어난다.
  - 코드 근거(develop `6ac67e79`)
    - 조립: `services/core-api/src/colab_core/app/search_evidence_conditions.py:123-151` `supported_facts()`. `:149-150`이 「{파일명}에서 {조건} 조건이 맞았어요 (출처 {source['label']} · {source['locator']})」를 만든다.
    - 사용: `app/routes/catalog.py:603-607`이 이 결과로 `facts['evidence']`를 채운다. `rationale` 한 줄도 같은 항목을 이어 만든다(`dataset_search.py:117-122` `rationale_line`). 그래서 `rationale` 문자열에도 같은 괄호가 들어간다(캡처 `rationale` 값에서 확인).
    - `source`는 저장된 검색 근거 행의 `source_label`·`source_locator`다(`domains/d3_search_evidence.py:44` · `domains/d3_client_search.py:112`).
  - 같은 출처는 상세 화면에 이미 있다
    - 자료 상세 파일 목록의 「검색 근거」 버튼(`frontend/src/components/detail/FileList.tsx:151-162`)이 `SearchEvidenceEditor`를 연다(`FileList.tsx:285-294`).
    - 읽기 보기가 「설명서 이름」=`source.label` · 「절 또는 문단」=`source.locator` · 「원문 발췌」=`source.text`를 보인다(`SearchEvidenceEditor.tsx:249-251`). 편집 권한이 있으면 같은 세 값이 입력칸으로 선다(`:274-276`).
    - 이 목록 API는 파일 본문 접근 권한이 있는 사람에게만 근거 원문을 돌려준다(`contracts/seams/fe-core.yaml:1783-1795` `listDatasetSearchEvidence` 설명).
  - 사실 기록: 앵커 중복은 데이터 생성기 결함이다
    - 캡처의 `locator` 「DATASETS.md#01.level-data/01.precipitation/DATASETS.md#seq-5」는 파일명 `DATASETS.md`가 앞뒤로 두 번 나온다.
    - 생성: `dev-package/tools/dataset_evidence_backfill.py:386` `f"DATASETS.md#{source['document']}#seq-{seq}"`. `source['document']`는 이미 `…/DATASETS.md`로 끝나는 상대 경로다(`:268` `path.relative_to(DATASETS_MD_ROOT).as_posix()`). 앞에 붙인 고정 접두 `DATASETS.md#`가 중복을 만든다.
    - 산출 payload `dev-package/tools/generated/dataset-evidence-payloads.json`에 같은 값이 들어 있다(seq 5 `source.locator`). dev 행은 이 payload를 적용한 값이다 `[추론 · 캡처 값과 payload 값이 같음]`.
    - `label`(`:385` 「{document} · seq {seq} {name}」)도 경로·순번을 이미 담아 카드 괄호 안에서 경로가 두 번 나온다.
  - 잠긴 카드(`bodyAccessible: false`)에서도 `supported_facts`가 출처 라벨·앵커를 싣는지는 확인하지 않았다 `[미확인]`. 검색 근거 읽기(`catalog.py:553` `read_reviewed(ro, include_source_text=False)`)는 원문 발췌만 빼고 라벨·앵커는 싣는다(`d3_search_evidence.py:87-96`). 상세 API는 본문 접근 권한자에게만 준다(위). 이 항목을 카드에서 빼면 이 차이도 함께 사라진다.
- ② 낱말 일치에 주제 라벨이 낱말처럼 섞인다
  - 실측(카드 `HSR 레이더 반사도 원자료` · `rn15 15분 누적강수` · `rationaleFacts[kind=term]`)
    > ‘강우’, ‘강우·강수’가 이름·주제·요약에 맞았어요
  - 같은 응답의 최상위 `topic`이 `강우·강수`이고, 헤더가 이미 「주제 ‘강우·강수’로 좁혀 뒤졌어요」를 한 번 적는다(선행 intent Q8). 사용자가 치지 않은 주제 라벨이 「맞은 낱말」로 다시 나온다.
  - `hsr_sample` · `rn15_sample` 카드도 「‘강우’, ‘강우·강수’가 이름·주제·요약·확인한 파일 근거에 맞았어요」다.
  - 경로(코드 근거)
    - ai-service 사전 확장이 주제 동의어를 만나면 동의어와 **주제 라벨을 둘 다 검색어에 넣는다**: `services/ai-service/src/colab_ai/domains/d9_ontology.py:73` `out.append(synonym)` · `:74` `out.append(mapped)`. `mapped`가 주제 라벨(`강우·강수`)이다. 같은 값이 `topic`도 정한다(`:77-78`).
    - `d10_ai_services.py:196-203`(`:202`)이 해석 검색어 뒤에 확장 검색어를 잇고(`terms = (*kept, *expansion.terms)`), `:215` `cut`을 응답 `terms`로 내보낸다.
    - core-api는 이 `terms`로 검색한다(`catalog.py:577` `terms=answer["terms"]`). SQL은 검색어마다 실제로 맞았는지 따로 모아 `matched_terms`로 돌려준다(`domains/d3_catalog.py:1045` · `:1052-1059`). 주제 열은 설명 tsvector에 들어 있다(`db/platform/schema.sql:472` `setweight(to_tsvector('simple', coalesce(topic, '')), 'B')`). 그래서 주제 라벨이 그 주제의 모든 자료에서 「맞은 낱말」이 된다.
    - 문장 조립: `app/dataset_search.py:101-105`가 `matched_terms` 앞 3개(`MAX_TERMS_IN_RATIONALE = 3` · `:24`)를 따옴표로 잇는다. 주제 라벨이 끼면 실제 질의 낱말 한 자리를 차지한다. 캡처의 `pred_sample` 카드는 ‘강우’, ‘예측’, ‘pred_sample.npy’ 3개로 차서 라벨이 밀려났다.
  - 「이름·주제·요약」의 「주제」는 낱말별 맞은 자리가 아니다
    - `d3_catalog.py:1075` `_WHERE_LABELS`의 `("hit_description", "이름·주제·요약")`는 설명 tsvector 전체가 맞았는지를 가리키는 **묶음 이름**이다. 어떤 낱말이 이름·주제·요약 중 어디에 맞았는지는 SQL이 돌려주지 않는다.
    - 따라서 「실제 질의 낱말이 주제에 맞았을 때만 ‘주제’를 남긴다」는 현재 데이터로 판정할 수 없다.
  - 사용자가 주제 라벨을 직접 칠 수 있다
    - 낱말 해석은 `·`에서 자르지 않는다(`services/ai-service/src/colab_ai/app/interpret.py:68` 「`·` 는 주제 표기(`강우·강수`)의 일부라 남긴다」). 질의에 「강우·강수」를 그대로 치면 해석 검색어에 그 말이 들어간다.
    - 이 경우 라벨은 사용자가 친 낱말이므로 「낱말 일치」에 남아야 한다.

## 원한 결과 (proposed outcome)
- ① 파일 근거 항목
  - 카드 `rationaleFacts[kind=evidence]` 항목은 「{파일명}에서 {조건} 조건이 맞았어요」까지만 싣는다. 캡처 질의의 기대 문구는 「pred_sample.npy에서 파일 역할(예측 결과) 조건이 맞았어요」다.
  - 「(출처 …)」 괄호, `source.label`, `source.locator` 문자열은 카드 항목과 `rationale` 한 줄 어디에도 없다.
  - 출처는 상세 화면 「검색 근거」(`SearchEvidenceEditor.tsx:249-251`)에만 남는다. 상세 화면은 바꾸지 않는다.
- ② 낱말 일치 항목
  - 응답 `topic`과 같은 검색어가 **사용자 질의 원문에 없으면** 「낱말 일치」 항목의 낱말 목록에서 뺀다. 캡처 질의의 기대 문구는 「‘강우’가 이름·주제·요약에 맞았어요」다.
  - 빼는 일은 3개 상한(`dataset_search.py:24`)을 적용하기 **전에** 한다. 실제 질의 낱말이 그 자리를 쓴다.
  - 질의 원문에 주제 라벨이 그대로 있으면 목록에 남긴다.
  - 주제 라벨 말고 맞은 낱말이 하나도 없으면 라벨을 남긴다. 이유가 0개가 되지 않게 한다(근거 필수 · `.agents/rules/product.md:76`).
  - 검색어·순위는 바꾸지 않는다. 표시 문장만 바꾼다.
- ③ 낱말 일치 항목의 자리 이름(해소 ⒝로 추가 · 2026-09-26)
  - 「낱말 일치」 항목의 자리 목록에서 「확인한 파일 근거」를 뺀다. 캡처 `hsr_sample` · `rn15_sample` 카드의 기대 문구는 「‘강우’가 이름·주제·요약에 맞았어요」다.
  - 파일 근거로만 맞은 결과(`match.where == ("확인한 파일 근거",)`)는 지금처럼 「낱말 일치」 항목 없이 「파일 근거」 항목 하나만 낸다.
  - 검색·순위·`where` 판정은 바꾸지 않는다. 표시 문장만 바꾼다.
- 검증
  - 서버 시험(core-api)
    - `supported_facts` 결과에 「출처」, 레코드의 `source.label`, `source.locator`가 없음을 단언한다. 현행 `services/core-api/tests/test_search_evidence_conditions.py:33`은 라벨 「처리 설명서」가 항목에 **있음**을 단언하므로 반대로 고친다.
    - `rationale_facts`(또는 구현에서 정한 조립 지점)에 대해 네 경우를 단언한다: ⑴ 라벨이 확장으로만 들어오면 목록에서 빠짐 ⑵ 질의 원문에 라벨이 있으면 남음 ⑶ 라벨만 맞으면 남음 ⑷ 라벨을 빼면 4번째 실제 낱말이 3개 안에 들어옴.
    - ③: 낱말 일치 항목에 「확인한 파일 근거」가 없음 · 파일 근거로만 맞은 결과는 파일 근거 항목 하나만 냄을 단언한다.
    - 현행 `services/core-api/tests/test_search_assembly.py:74` 「‘강우’가 이름·주제·요약에 맞았어요」 단언은 그대로 green이어야 한다.
    - 게이트: `service-tests-core-api` green. ai-service를 바꾸지 않으면 `service-tests-ai-service`는 회귀 확인용으로만 돌린다.
  - dev 재캡처(배포 뒤)
    - 같은 계정·같은 질의 4건(`dev-queries.json`)을 다시 캡처한다. 응답 JSON에서 ⑴ 「(출처」 0건 ⑵ `topic`과 같은 낱말이 `term` 항목에 0건(질의 원문에 라벨이 없는 질의 한정)을 계수한다.
    - 캡처 JSON·스크린샷은 `dev-package/reports/search-rationale-panel/<날짜>-dev/`에 두고, 이번 캡처(`20260926-dev`)와 전후 비교한다.
    - agent-browser로 카드 패널을 폰 폭 1장 이상 찍어 항목 줄 수가 줄었는지 본다(`AGENTS.md` · UI 영향 확인).

## 가치 가설
- 검색 사용자는 패널에서 이유만 읽는다. 파일 근거 항목이 한 문장으로 끝나고, 헤더에 이미 있는 주제 라벨이 낱말 목록에 다시 나오지 않아 「맞은 낱말」이 사용자가 친 말만 가리킨다.
- 확인 방법: 배포 뒤 dev 재캡처 계수(「(출처」 0건 · 확장 주제 라벨 0건)와 Ted의 화면 판정. Ted가 여전히 군더더기라고 하면 가설이 틀린 것으로 본다.

## 영향 범위
- 사용자 / 화면: S-06 검색 결과 카드의 「AI」 패널 문구(파일 근거 · 낱말 일치). 패널 레이아웃·종류·헤더는 그대로다. 상세 화면 검색 근거는 그대로다.
- 서비스 · 스키마 · 계약
  - core-api만 바꾸는 것이 예상이다.
    - ① `app/search_evidence_conditions.py:149-150`(괄호 제거)
    - ② `app/dataset_search.py:84-105`와 호출부 `app/routes/catalog.py:584-588`. 조립 지점에 `topic`(`catalog.py:557` `search_topic`)과 질의 원문(`query`)을 넘겨야 한다. 현재 `compose`는 둘 다 받지 않는다(`dataset_search.py:125-127`).
  - ai-service · DB · 생성기(`dataset_evidence_backfill.py`)는 바꾸지 않는다(설계트리 Q2 · Q1b).
  - 계약: `rationaleFacts[].items`는 `AiRationale` 문자열 배열이다(`contracts/seams/fe-core.yaml:5553-5557` · `contracts/schemas/common.json:186-191` · `minLength 1`·줄바꿈 금지 패턴만). 문구 규칙을 스키마가 정하지 않으므로 문구 변경은 계약 변경이 아니다.
  - 계약 파괴 여부: **아니오**(계약 파일 변경 0건 예상) `[구현 PR에서 contract-breaking 실측]`

## 제약
- 선행 intent 규칙을 그대로 따른다.
  - 검색된 이유만 싣는다. 한계·부정 문장(「확인하지 못」「미확인」「불일치」「보장하지 않」「아니에요」「없었어요」)을 새로 만들지 않는다(선행 Q6).
  - UI에 내부 기법 이름(온톨로지·계보)을 쓰지 않는다(선행 Q7).
  - 쿼리 공통부(범위·주제·해석 여부)는 헤더에 한 번만 쓴다(선행 Q8). ②는 이 규칙을 낱말 목록까지 적용하는 것이다.
- 근거 필수·한 줄(`.agents/rules/product.md` §3 `:76` · `:79`). 항목을 줄이다가 종류 안 항목이 0개가 되거나, 근거 종류가 모두 비는 카드가 생기면 안 된다.
- 문장은 서버 템플릿 조립이다. 해요체 종결을 유지한다(`dataset_search.py:93-94`).
- 순위·검색어는 건드리지 않는다. 표시 문장 변경이 검색 결과 집합·순서를 바꾸면 안 된다.

## 설계트리 (grill-me 결과)
- Q1 파일 근거 항목의 출처를 어떻게 줄이나
  - ⓐ 괄호 전체를 뺀다(「…조건이 맞았어요」로 끝) → **권장**
  - ⓑ 설명서 이름(`label`)만 남기고 앵커를 뺀다 → 반대: `label` 자체가 저장소 경로·순번이라(`backfill.py:385`) 괄호가 여전히 길다.
  - ⓒ 화면에서 괄호를 잘라 그린다 → 반대: 문장은 서버가 만들고 화면은 그대로 싣는다(`dataset_search.py:93-94`). `rationale` 한 줄에는 그대로 남는다.
  - Q1a 출처를 볼 자리 → 상세 화면 「검색 근거」 그대로(`SearchEvidenceEditor.tsx:249-251`). 새 UI 없음 → **권장**
    - 반대 관점(기록): 카드에서 상세 파일 근거로 가는 바로가기가 없다. 사용자는 상세로 들어가 파일 행의 「검색 근거」 버튼을 눌러야 한다. 바로가기는 범위 밖(아래)이다.
  - Q1b 앵커 중복(`backfill.py:386`)을 이 intent에서 고치나
    - ⓐ 별건으로 둔다 → **권장**: 카드에서 앵커가 사라지면 사용자 노출은 상세 「절 또는 문단」 한 곳이다. 고치려면 payload 재생성과 dev 재적용(dev 데이터 쓰기 · 사용자 승인 범위)이 필요하다.
    - ⓑ 이 intent에 포함한다 → 반대: server-only 변경이 데이터 재적용을 끌고 온다. 재시드 절차 문서(`dev-package/tools/dev-reseed/`)와 엮인다.
- Q2 주제 라벨을 어디서 걸러내나
  - ⓐ core-api 표시 조립에서 뺀다(검색어·순위 불변) → **권장**
  - ⓑ ai-service 사전 확장에서 라벨을 검색어에 넣지 않는다(`d9_ontology.py:74`) → 반대: 검색어 집합이 바뀐다. 주제 열은 tsvector 가중치 B(`schema.sql:472`)라 라벨 검색어가 `ts_rank_cd` 순위에 들어간다 `[추론 · 순위 영향 미실측]`. 표시 문제를 순위 변경으로 푸는 셈이다.
  - ⓒ 화면에서 뺀다 → 반대: Q1ⓒ와 같은 이유.
  - Q2a 사용자가 라벨을 직접 친 경우 판정 → 질의 원문에 라벨 문자열이 그대로 있으면 남긴다 → **권장**
    - 반대 관점(기록): 「강우 강수」처럼 가운뎃점 없이 치면 라벨과 같지 않아 뺀다. 이때 ‘강우’·‘강수’는 따로 맞은 낱말로 남으므로 이유는 줄지 않는다 `[추론]`.
  - Q2b 라벨만 맞은 카드 → 라벨을 남긴다 → **권장**(근거 필수)
    - 반대 관점(기록): 이 카드는 헤더와 같은 말을 한 번 더 한다. 대신 「주제 ‘강우·강수’에 맞았어요」처럼 문형을 바꾸는 안도 있다. 문형 확정은 구현 때 한다.
  - Q2c 위치 이름 「이름·주제·요약」의 「주제」 → 그대로 둔다 → **권장**
    - 사유: 묶음 이름이고(`d3_catalog.py:1075`) 낱말별 맞은 자리를 SQL이 주지 않는다. 「실제 낱말이 주제에 맞았을 때만 ‘주제’」는 필드별 일치 계산을 새로 넣어야 한다.
    - 반대 관점(기록): 라벨을 뺀 뒤에도 「주제」가 남아 사용자는 친 낱말이 주제에 맞았다고 읽을 수 있다. 필드별 일치(설명 tsvector를 이름·주제·요약으로 나눠 판정)는 SQL 변경이라 별건으로 둔다.

## 미해결 질문
- 해소(2026-09-26 · 오케스트레이터 결정 · Ted 승인 「좋아 진행」 하 결정)
  - ⒜ Q2b 라벨만 맞은 카드: 라벨을 낱말 목록에 남긴다. 문형은 현행 낱말 일치 문형 그대로다(「‘강우·강수’가 이름·주제·요약에 맞았어요」). 라벨은 ⑴ 맞은 낱말이 그것 하나뿐이거나 ⑵ 사용자가 질의에 친 말이면 남는다.
    - 사유: 낱말별 맞은 자리를 SQL이 주지 않으므로(Q2c) 자리 이름을 「주제」 하나로 좁히는 새 문형은 데이터로 판정할 수 없다.
  - ⒝ 관찰 항목(「확인한 파일 근거」가 낱말 일치 자리 목록에 섞임)을 원한 결과 ③으로 올린다. 이 자리 이름은 낱말 일치 항목에서 뺀다.
    - 사유: 파일 근거로 들어온 결과는 「파일 근거」(확인된 조건 · `catalog.py:603-607`) 또는 「연결된 자료」(바로 앞 단계 · `catalog.py:612-614`) 종류가 이미 말한다. 낱말 줄에 같은 사실을 다시 적지 않는다(선행 Q8과 같은 규칙).
    - `match.where == ("확인한 파일 근거",)`(`dataset_search.py:96-97`)는 지금처럼 낱말 일치 없이 파일 근거 항목 하나만 낸다. 자리 이름을 뺀 뒤 목록이 비는 경우가 이것뿐이다.
  - ⒞ 앵커 중복(`dev-package/tools/dataset_evidence_backfill.py:386`)은 이 intent 범위 밖이다. 생성기 수정과 dev 재적용은 별건으로 연다(아래 「범위 밖」).
- Q2b 라벨만 맞은 카드의 문형(「‘강우·강수’가 이름·주제·요약에 맞았어요」 유지 / 「주제 ‘강우·강수’에 맞았어요」). 구현 때 정하고 PR 요약에 적는다. → 해소 ⒜(현행 문형 유지)
- 관찰(이 intent의 결정 대상 아님): `hsr_sample` 카드 「낱말 일치」 항목의 자리 이름에 「확인한 파일 근거」가 섞인다(「…이름·주제·요약·확인한 파일 근거에 맞았어요」). `dataset_search.py:104`가 `match.where` 전체를 잇고, `where`에 `hit_evidence` 이름이 들어가기 때문이다(`d3_catalog.py:1078`). 같은 카드에 「파일 근거」 종류가 따로 서지 않았다. 다룰지 여부는 Ted 판정 대상이다. → 해소 ⒝(원한 결과 ③)

## 범위 밖 (명시 제외)
- 패널 레이아웃·태그·색·2단계 구조, 근거 종류 넷과 그 이름·순서(선행 intent Q1·Q1a·Q1b·Q7에서 확정).
- 결과 헤더 문장(범위 줄 · 주제 문장 · 해석 여부 문장).
- 상세 화면 「검색 근거」의 표시·편집 UI, 카드에서 상세 파일 근거로 가는 바로가기.
- 앵커 중복 생성기 수정과 dev 데이터 재적용(Q1b · 해소 ⒞ · 후속 항목). 결함 자리 `dev-package/tools/dataset_evidence_backfill.py:386` `f"DATASETS.md#{source['document']}#seq-{seq}"` · 산출 `dev-package/tools/generated/dataset-evidence-payloads.json`.
- 필드별 일치 계산(Q2c) · ai-service 사전 확장 변경(Q2ⓑ).
- 정본(`40 COLAB-기획/…`) 파일 수정.
- 추기(2026-09-26 · PR #170 검토 반영 · 오케스트레이터 결정): 「온톨로지 연결 근거」 자리 이름도 ③과 같은 방식으로 「낱말 일치」 자리 목록에서 뺐다(선행 intent Q7 내부 기법 이름 미노출). 그 사실은 「관련 개념」 종류가 말한다. 이 자리로만 맞은 결과는 종전처럼 「관련 개념」 항목 하나를 낸다. 파일 근거·온톨로지 자리로만 맞으면 낱말 일치 없이 두 종류가 선다. 표시 문장만 바꾸며 검색·순위·`where` 판정은 그대로다.

## 확인
- 프론티어 공집합 확인: 2026-09-26 — 설계트리 Q1~Q2c 권장안 확정 · 미해결 질문 2건과 앵커 중복은 해소 ⒜~⒞로 닫음.
- Ted 확인 문장(원문 그대로): "좋아 진행" (2026-09-26 · PR #167 승인 · 발의 「1,2 둘다 intent로 올리자」)
- 재개봉 금지: 아니오

## 참조
- 선행 intent: `dev-package/intent/2026-09-25-search-rationale-separation.md`(Q6 · Q7 · Q8 · 미해결 ⒜ ⒝)
- dev 캡처: `origin/deploy/dev-592ff4b7` `dev-package/reports/search-rationale-panel/20260926-dev/dev-search-response-llm.json` · `dev-queries.json` · `dev-llm-light-390.png`
- 코드
  - core-api: `app/search_evidence_conditions.py:123-151` · `app/dataset_search.py:24`·`:84-122`·`:125-148` · `app/routes/catalog.py:532`·`:553-557`·`:577`·`:581-614` · `domains/d3_catalog.py:1045-1059`·`:1075-1079` · `domains/d3_search_evidence.py:44`·`:87-96` · `db/platform/schema.sql:472`
  - ai-service: `domains/d9_ontology.py:50-94` · `domains/d10_ai_services.py:195-220` · `app/interpret.py:68`
  - 화면: `frontend/src/components/detail/SearchEvidenceEditor.tsx:249-251`·`:274-276` · `frontend/src/components/detail/FileList.tsx:151-162`·`:285-294`
  - 계약: `contracts/seams/fe-core.yaml:1783-1795`·`:5537-5557` · `contracts/schemas/common.json:186-191`
  - 데이터 생성기: `dev-package/tools/dataset_evidence_backfill.py:268`·`:385-386` · `dev-package/tools/generated/dataset-evidence-payloads.json`
  - 시험: `services/core-api/tests/test_search_evidence_conditions.py:33` · `services/core-api/tests/test_search_assembly.py:74`
- 결정: 〈N〉 (병합 시 기입)
