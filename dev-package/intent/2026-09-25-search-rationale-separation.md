# Intent: 검색 결과 카드의 검색 근거를 「AI」 패널로 분리하고, 검색된 이유만 2단계 개조식으로 보인다
메타 — 발의자: Ted · 작성 2026-09-25 · 개정 2026-09-26(트랙 A 시각 분리 + 트랙 B 근거 재구성 병합) · 승인 **Ted 2026-09-26**(확인 문장 원문 「좋아결정다하고 한참을 자리비우고 개발시킬거야」 — 설계트리 Q0~Q8 그대로 · 앞선 답 「좋아 그렇게 가보자 좋아」(시안 A) · 「권고대로 좋아」(상위 이름)). 이 서명을 적은 커밋이 승인이다(`README.md` 「승인 = 커밋」).

## 문제
- 트랙 A(시각 분리)
  - 검색 결과 카드에서 자료 설명(요약) 바로 아래에 검색 근거 문장이 이어진다. 두 문단은 글자 크기·행간이 같고 라벨·구분선·배경이 없다. 사용자는 어느 문장이 자료 등록자가 쓴 설명이고 어느 문장이 검색이 붙인 이유인지 구분하지 못한다(Ted 발의 원문: "llm검색이 된 이유를 같이 알려주는거같은데 이건 구분되게 표기해서 데이터의 디스크립션과 구분해줄수있을까? 이건 인텐트로 넣어줘").
  - 코드 근거(develop `67a03a05`)
    - 요약: `frontend/src/components/search/SearchHitCard.tsx:73-75` `<p className="hit-summary">`
    - 근거: `SearchHitCard.tsx:77-79` `<p className="hit-why" data-testid="search-rationale">`. 라벨 없이 문장만 넣는다.
    - 스타일: `frontend/src/components/search/search.css:95-98` `.hit-summary`는 13px·행간 1.6·`--color-text`, `:99` `.hit-why`는 13px·행간 1.6이고 색 지정이 없다.
  - 주석 `search.css:93-94`는 「근거는 코랄 라벨을 단 AI 문장」이라 적지만 `:99`에는 색도 라벨도 없다. 주석과 구현이 다르다. 저장소 AI 액센트는 보라다(`frontend/src/shell/tokens.css:42` 「판정 48 · 코랄이 아니다」).
- 트랙 B(근거 재구성)
  - 근거 문장은 core-api가 한 문자열로 조립한다. 카드마다 같은 공통부와 한계 문장이 반복되고, 검색된 이유가 그 사이에 묻힌다.
    - 공통부: 「{연구실} 안 N건에서」(`services/core-api/src/colab_core/app/dataset_search.py:83`) · 「(주제 X로 좁혀 뒤졌어요)」(`:88-89`) · 「질의 해석 없이 질문의 낱말 그대로 찾았고,」(`:91-92`)
    - 한계·부정 문장
      - 기본 tail 「기간·지역·품질은 이 검색이 확인하지 못했으니 카드의 값으로 직접 봐 주세요」(`dataset_search.py:90`)
      - 미확인 조건 「요청한 X 조건은 현재 검색 근거만으로 충족 여부를 확인하지 못했어요.」(`search_conditions.py:48-61`)
      - 파일 근거 tail 교체 「기록되지 않은 조건과 자료 품질은 보장하지 않아요」(`routes/catalog.py:601-603`)
      - 파일 근거 조각의 「불일치: …」「미확인: …」(`search_evidence_conditions.py:139-146`)
      - 조건 검색 고정 문장 뒷절 「기록되지 않은 품질은 미확인입니다.」(`routes/catalog.py:717`)
    - 카드별 이유: 맞은 낱말·자리(`dataset_search.py:80-83`) · 온톨로지 연결(`catalog.py:606-608`) · 직접 부모 계보(`catalog.py:609-611`) · 파일 근거 확인 항목(`search_evidence_conditions.py:123-146`)
  - 「{연구실} 안 N건」은 헤더 `ScopeLine`(`frontend/src/routes/SearchResultsPage.tsx:18-31` · `:29` 「{labName} 데이터 {searchedCount}건을 뒤졌어요.」)과 이미 중복이다. 「질의 해석 없이」도 헤더 degraded 안내(`SearchResultsPage.tsx:117-122`)와 뜻이 겹친다.
  - 문장에 내부 기법 이름(「온톨로지 연결」·「직접 부모 관계」)이 그대로 나온다.

## 원한 결과 (proposed outcome)
- 패널(트랙 A)
  - 결과 카드마다 요약 문단(`hit-summary`) 아래에 별도 DOM 요소인 근거 패널이 선다.
  - 패널 = 면 `--color-accent-50` · 좌측 2px `--color-ai` 선 · 본문 `--color-text-body`. 새 토큰 0개.
  - 패널 맨 위 왼쪽에 작은 태그 「✦ AI」를 둔다. 태그는 글자 `--color-accent-700` · 테두리 `--color-accent-200` · 바탕 `--color-surface`이고, 가로로 늘이지 않는다(내용 폭만).
  - 태그 다음 줄에 2단계 개조식 목록을 둔다(시안 A).
    - 상위 = 근거 종류. 굵게, 앞에 보라 점(`--color-ai`).
    - 하위 = 사실. 들여쓰고 앞에 「–」(`--color-accent-500`).
  - 잠긴 카드와 Verified 카드에도 같은 패널이 선다. 0건 화면과 검색 불가 화면은 변하지 않는다.
  - 펼침·더보기는 두지 않는다. 항목은 항상 전부 보인다.
- 내용(트랙 B)
  - 패널에는 **검색된 이유만** 싣는다. 한계·부정 문장(「~확인하지 못했어요」「~아니에요/없었어요」「미확인」「불일치」「보장하지 않아요」)은 카드에서 모두 뺀다.
  - 상위 근거 종류는 넷이다: 「낱말 일치 · 관련 개념 · 연결된 자료 · 파일 근거」. 사실이 없는 종류는 통째로 생략한다.
  - UI에 내부 기법 이름(온톨로지·계보)을 쓰지 않는다. 서버 문장의 「온톨로지 연결」도 「관련 개념」으로 바꾼다.
  - 쿼리마다 같은 공통부는 결과 헤더에 한 번만 쓴다.
    - 「{lab} 데이터 N건을 뒤졌어요.」: 기존 `ScopeLine` 그대로(`SearchResultsPage.tsx:29`)
    - 「주제 X로 좁혀 뒤졌어요.」: `ScopeLine` 뒤에 잇는다. 응답 최상위 선택 필드 `topic`이 필요하다(아래 영향 범위).
    - 「질의 해석 없이…」: 헤더 degraded 안내(`SearchResultsPage.tsx:117-122`)로 대체한다. 두 조건의 동치는 확인 항목이다.
  - 자료 설명(요약)은 전문 그대로 둔다(현행).
- 화면 예(라이트 · 시안 A)

```
│ 낙동강 유역 강우 (2025) · 유역 평균 강수량        │ ← hit-summary 그대로
│ ┃ [✦ AI]                                          │ ← 작은 태그, 왼쪽
│ ┃ • 낱말 일치                                     │ ← 굵게, 보라 점
│ ┃   – ‘강수’가 제목·키워드에 맞았어요             │
│ ┃ • 관련 개념                                     │
│ ┃   – 자료에 적힌 강수량과 연결돼요               │
│ ┃ • 연결된 자료                                   │
│ ┃   – 낙동강 관측 원자료의 직접 하위 자료예요     │
```

- 검증
  - vitest: 카드 안에서 ⑴ 태그 「AI」가 있고 ⑵ 근거 패널이 `hit-summary`와 다른 요소·다른 클래스이며 ⑶ `rationaleFacts`의 종류 순서·항목이 그대로 그려지고 ⑷ 사실 없는 종류는 그려지지 않으며 ⑸ 필드가 없으면 `rationale` 한 줄로 그린다(구 응답 호환).
  - 서버 시험: 카드 근거 조립 결과에 한계·부정 문구(「확인하지 못」「미확인」「불일치」「보장하지 않」「아니에요」「없었어요」)가 없음을 단언한다. `where == ("온톨로지 연결 근거",)`만으로 맞은 결과에도 「관련 개념」 항목이 1개 이상 있음을 단언한다(근거 필수).
  - 게이트: `frontend-design-lint` · `frontend-test` · `contract-lint` · `contract-breaking` · `generated-up-to-date` green.
  - agent-browser: dev 검색 결과 카드를 라이트·다크 각 1장, 폰 폭 1장 캡처하고 요약·패널 구분을 대조한다(`AGENTS.md` · UI 변경은 실제 브라우저로 검증).

## 가치 가설
- 검색 사용자는 자료 설명과 검색 근거를 한눈에 구분한다. 근거는 종류별로 짧게 나뉘어 있어 결과를 고를 때 「왜 이 결과가 나왔는지」를 한 번에 읽는다. 공통부가 카드마다 반복되지 않아 목록을 훑는 시간이 준다.
- 확인 방법: Ted가 dev 결과 화면(교수 계정 1개 · 운영자 계정 1개)을 보고, 추가 설명 없이 ⑴ 두 영역이 구분되는지 ⑵ 근거가 이유만으로 읽히는지 판정한다. 캡처 전후 비교와 시험 green을 PR 요약의 「원한 결과 ↔ 실제 ↔ 근거」 표에 싣는다. Ted가 여전히 헷갈린다고 하면 가설이 틀린 것으로 본다.

## 영향 범위
- 사용자 / 화면: S-06 검색 결과 카드와 결과 헤더.
  - `SearchHitCard.tsx:73-79`(패널 · 태그 · 2단계 목록) · `search.css:93-99`(패널 규칙 추가, 「코랄」 주석을 「보라(accent) · 판정 48」로 정정)
  - `SearchResultsPage.tsx:18-31` `ScopeLine`(주제 문장 추가) · `:117-122` degraded 안내(재사용)
  - AI 해석 경로(`catalog.py:581-614`)와 조건 검색 경로(`catalog.py:708-723`)가 같은 카드를 쓴다(`SearchResultsPage.tsx:175`). 조건 검색 경로는 헤더 자리에 `AssessmentPanel`이 선다(`:115`).
- 계약(비파괴 · 선택 필드 추가)
  - `SearchResultRow.rationale`(문자열 · 필수 · `AiRationale`)은 호환을 위해 유지한다(`contracts/seams/fe-core.yaml:5505-5509` · `contracts/schemas/common.json:186-191`).
  - `SearchResultRow`에 선택 필드를 더한다. 이름은 제안이다: `rationaleFacts: [{ kind: 'term' | 'concept' | 'linked' | 'evidence', items: string[] }]`
    - 기존 규약: 결과 행 추가 값은 `SearchResultRow` 두 번째 객체에 칸을 더한다(`fe-core.yaml:5473` 「두 번째 객체에 칸을 더하는 것이 이 스키마의 규약」). 선택 필드는 `required`에 넣지 않는다(`labName` 선례 `:5510-5516`).
    - `items` 원소는 `AiRationale`과 같은 한 줄 문자열(줄바꿈 금지)로 둔다. `kind` 순서는 서버가 정한다(낱말 일치 → 관련 개념 → 연결된 자료 → 파일 근거).
  - `SearchResults`(`fe-core.yaml:5344-5382`)에 선택 필드 `topic`(문자열 · minLength 1)을 더한다. 현재 응답 최상위는 `scope · isDataQuery · degraded · items · totalCount · nextCursor (+degradedReason)`이고 `topic`이 없다(`catalog.py:650-659`).
  - 생성물 재생성: `frontend/package.json:5` `npm run generate`(`openapi-typescript ../contracts/seams/fe-core.yaml -o src/generated/fe-core.ts`). 생성물은 손으로 고치지 않는다(`.agents/rules/product.md` §3 7항). 게이트 `generated-up-to-date`(`gates/run.sh:771`)가 대조한다.
  - 계약 파괴 여부: **아니오**(선택 필드 추가만) `[PR 게이트 contract-breaking에서 실측]`. 단 설명 문구 개정이 필요하다(아래 「정본·계약과 어긋나는 점」).
- core-api 조립 지점
  - `dataset_search.py:66-93` `rationale()`: 공통부(연구실·건수·주제·degraded 접두)와 기본 tail을 카드 문자열에서 뺀다. 「낱말 일치」 항목을 만든다(맞은 낱말 최대 3개 `:24` · 자리 `:82`).
    - `where == ("확인한 파일 근거",)`(`:84-85`) → 「파일 근거」 항목
    - `where == ("온톨로지 연결 근거",)`(`:86-87`) → 「관련 개념」 항목. 문면의 「온톨로지 연결」을 「관련 개념」으로 바꾼다.
    - 확장어 문구(`_EXPANSION_PHRASE` `:44-48` 「‘강우’와 같은 말인 ‘강수’」)는 「낱말 일치」 항목에 둔다 `[결정 2026-09-26 · 아래 미해결 질문 해소 ⒜]`.
  - `catalog.py:597-611`
    - `:598-599` `search_conditions.explain_unverified_conditions`: 부정 문장이므로 카드 근거에 붙이지 않는다.
    - `:600-605` 파일 근거: tail 교체(「보장하지 않아요」)를 없앤다. `search_evidence_conditions.explain`(`:123-146`)의 조각 중 「확인(supported)」 항목만 「파일 근거」 하위로 싣고 「불일치」「미확인」은 싣지 않는다.
    - `:606-608` → 「관련 개념」 하위 「자료에 적힌 {labels}와 연결돼요」류 `[문면 구현 때 확정]`
    - `:609-611` → 「연결된 자료」 하위(직접 부모 관계를 「연결된 자료」 말로 표현)
  - `catalog.py:717` 조건 검색 고정 문장: 앞절 「현재 파일의 검토된 근거에서 해석된 조건을 함께 확인했습니다」를 「파일 근거」 하위 1항목으로 옮기고 뒷절 「기록되지 않은 품질은 미확인입니다.」는 뺀다. 해요체로 맞춘다(`dataset_search.py:73-77` 종결 규약).
  - `rationale` 문자열: `rationaleFacts`의 항목을 한 줄로 이어 만든다(구 클라이언트 fallback과 화면이 같은 사실을 말하게 한다) `[결정 2026-09-26 · 아래 미해결 질문 해소 ⒝]`. 이 경우 문자열에서도 한계·공통부가 빠진다.
  - 응답 `topic`: `catalog.py:650-659` `out`에 `search_topic`이 있을 때만 싣는다.
- 시험
  - `frontend/test/search.test.tsx:159-166`: 태그는 `search-rationale` 요소 밖에 둔다. 픽스처 `rationale`(`:41`)은 공통부·한계가 든 옛 문장이다. `rationale` 문자열을 위 제안대로 바꾸면 픽스처와 `:163` 단언(`textContent === rationale`)을 새 형식에 맞게 고쳐야 한다. `rationaleFacts`를 그릴 때 `search-rationale` testid를 어느 요소에 둘지 구현 때 정한다.
  - core-api 근거 문장 시험(서버 단위 시험) 다수가 옛 문면을 단언할 수 있다 `[미확인 · 구현 때 grep]`.

## 제약
- 린트 `frontend-design-lint`(`gates/tools/frontend-design-lint.sh:12-31`)
  - f: 화면 CSS 색 리터럴 금지(`var()` 폴백 안 포함).
  - b: 정의되지 않은 `var()` 금지. 목업의 `--color-surface-sunken`·`--color-ai-text`는 `tokens.css`에 없다. 쓰는 토큰은 전부 정의돼 있다: `--color-accent-50`(`tokens.css:43` · 다크 `:176`) · `--color-accent-200`(`:44` · `:177`) · `--color-accent-500`(`:45` · `:178`) · `--color-accent-700`(`:46` · `:179`) · `--color-ai`(`:52` · accent-500 별칭) · `--color-surface`(`:56` · `:148`) · `--color-text-body`(`:72` · `:157`).
  - g: JSX 인라인 style은 `--*` 변수 대입만.
  - e: `.chip` 맨 정의 금지(`primitives.txt`). 「✦ AI」 태그는 `.chip`을 쓰지 않고 `.search-page` 범위의 새 클래스로 둔다.
  - 다크 모드는 `[data-theme="dark"]` 블록이 토큰을 바꾼다. 화면 CSS에 다크 분기를 따로 쓰지 않는다.
- 대비(UI 조사 실측 · sRGB 상대휘도 계산, 라이트/다크)
  - 본문 `--color-text-body` → 면 accent-50: 9.03 / 11.18
  - 태그·강조 `--color-accent-700` → accent-50: 7.05 / 9.24
  - 점·선 `--color-ai` → accent-50: 4.82 / 7.50 · → 카드 `--color-surface`: 5.72 / 8.39
  - 면 accent-50 ↔ 카드 surface: 1.18 / 1.12. 면 색만으로는 구분이 약하다. 구분은 좌측 선(WCAG 1.4.11 · 3:1 이상)과 글자 태그(1.4.1)가 맡는다. 강제 색상 모드에서는 배경이 사라질 수 있어(Carbon AI label 사례 carbon-design-system/carbon PR #23324) 선과 태그가 남는 구조가 필요하다.
  - 잠긴 카드 바탕은 `--color-surface-alt`(`search.css:81`)다. 이 조합의 대비는 계산하지 않았다 `[미확인]`.
- 표지 관례: 저장소 AI 표지는 「✦ + accent-50 면 + accent-700 글자」다(`lineageGraph.css:35-38` `.lin-way` · `:90-91` `.aiflag` · `LineageSection.tsx:156-159`). `.aiflag`는 `.detail-page` 범위라 직접 쓸 수 없어 같은 토큰 조합을 `.search-page` 범위에 둔다. ✦는 텍스트와 짝으로만 쓴다(PatternFly AI iconography 지침).
- 근거 문장은 **서버 템플릿 조립**이다. LLM(ai-service interpret)이 주는 것은 검색어·주제·`source`뿐이다(`services/ai-service/src/colab_ai/domains/d10_ai_services.py:152`). 태그 「AI」는 「AI 검색이 붙인 이유」 영역의 표지이고, 문장을 LLM이 썼다는 뜻으로 쓰지 않는다.
- 근거 필수: `rationale`은 필수·nullable 아님(`.agents/rules/product.md:76` · `common.json:186-191`). 「관련 개념」만으로 맞은 결과(`where == ("온톨로지 연결 근거",)`)는 그 항목이 없으면 이유가 0개가 된다. 그래서 내부 이름은 숨기되 사실은 남긴다.
- 관련도는 막대만이다. 패널에 관련도 수치·등급 텍스트를 넣지 않는다(`SearchHitCard.tsx:1-5` · `fe-core.yaml:5497-5504`).

## 정본·계약과 어긋나는 점 (개정 항목 · 정본 개정 절차 별도)
- ① 한계 병기 요구 — **Ted 수용 · 정본/계약 개정 동반(별도 절차)**
  - `Policy_데이터_찾기.md §4:97` 「한계 표시 … AI 근거 한 줄 안에서 함께 밝히는 말」 · 비고 「별도 줄을 두지 않는다. 좋은 것만 보여주면 다음부터 안 믿는다」
  - `§8:148` 「맞는 점만 적지 않고 어긋나는 점을 같은 줄에서 함께 밝힌다」
  - `fe-core.yaml:5507-5509` 「한계도 이 한 줄 안에서 함께 밝힌다 — 별도 필드를 두지 않는다」 · `fe-core.yaml:1354` 검색 오퍼레이션 설명 「한계도 그 한 줄 안에서 밝힌다」
  - `dataset_search.py:69-72` docstring(한계를 같은 줄에 붙인다는 설계 설명)
  - Ted 결정 「이유만」은 이 넷과 정면으로 어긋난다. 정본 원문은 무수정이므로 개정은 기획 절차로 따로 연다.
  - 참고: `.agents/rules/product.md:73-80` §3 AI 응답 규격은 한계 병기를 요구하지 않는다(근거 필수 `:76` · 한 줄 고정 `:79`만).
- ② 한 줄 고정 — **Ted 수용 · 정본/계약 개정 동반(별도 절차)**
  - `.agents/rules/product.md:79` 「근거는 **한 줄** 고정」 · `common.json:186-191` `AiRationale` 「화면에서 한 줄로 서므로 줄바꿈을 허용하지 않는다」 · `Policy §8:148` 「한 줄로 고정한다」 · `fe-core.yaml:1354`
  - 2단계 개조식 목록은 화면에서 여러 줄로 선다. 데이터(`rationale` 문자열·각 항목)는 줄바꿈 없이 유지해 스키마 패턴은 지키지만, 「화면 한 줄」 문면과는 어긋난다. §3 개정 또는 해석(「항목마다 한 줄」) 확정이 필요하다.
- ③ 색 이름 — **Ted 수용 · 정본/계약 개정 동반(별도 절차)**: `Policy §8:148` 「좌측 코랄 선과 코랄 라벨」 · `search.css:93-94` 주석 「코랄 라벨」. 채택 색은 보라다(`tokens.css:42` 판정 48). 정본 문면 개정 항목, 주석은 구현 때 정정한다.
- ④ 라벨 문구 — **Ted 수용 · 정본/계약 개정 동반(별도 절차)**: `Policy §4:96`·`§8:148` 「왜 이 결과?」. Ted 결정은 「AI」 태그다. 정본 용어표 개정 항목.
- ⑤ 해석 degraded 표기 — **Ted 수용 · 정본/계약 개정 동반(별도 절차)**: 카드 접두 조건은 `interpretation.source != "llm"`(`catalog.py:584` · `relay.py:462-463`)이고 헤더 안내 조건은 응답 `degraded`(`relay.py:466` ← ai-service 본문)다. 두 값은 서로 다른 필드에서 온다. 헤더로 올릴 때 `source != "llm"`이고 `degraded == false`인 경우가 생기면 해석 없이 찾은 사실이 화면에서 사라진다 `[미확인 · 확인 항목]`.
  - 결정(2026-09-26): 헤더 degraded 안내의 표시 조건을 합집합(`source != "llm"` 또는 `degraded == true`)으로 둔다. 카드 접두를 없애도 「해석 없이 찾았다」는 사실이 화면에서 사라지지 않는다. 구현 때 dev에서 두 필드를 모두 실측·대조한다.

## 설계트리 (grill-me 결과)
- Q0 트랙 A(시각 분리)와 트랙 B(근거 재구성)를 한 intent로 → **합친다** [답: Ted 2026-09-25 「ab 둘다 이번에 합쳐서 허자 / 나머진 권고대로」]
- Q1 표기 방식: ⓐ 라벨 + 좌측 선 + 틴트 면 / ⓑ 접이식 블록 / ⓒ 아이콘+색만 → **ⓐ** [답: Ted 2026-09-25 · 「나머진 권고대로」]
  - 면 `--color-accent-50` · 좌측 2px `--color-ai` · 태그 글자 `--color-accent-700`·테두리 `--color-accent-200`·바탕 `--color-surface` · 본문 `--color-text-body`. 새 토큰 없음. 코랄이 아니라 보라(판정 48 · `tokens.css:42`).
  - 반대 사유(기록 유지): 카드마다 면·선이 늘어 목록 밀도가 떨어진다. ⓑ는 `§8:148` 「펼침·더보기 금지」에 걸리고, ⓒ는 색만으로 뜻을 전해 WCAG 1.4.1에 걸린다.
  - Q1a 라벨 문구 → **「AI」**(✦ 붙은 작은 태그 · 패널 맨 위 왼쪽 · 가로로 늘이지 않음) → 줄바꿈 → 2단계 개조식 [답: Ted 2026-09-25/26 「왜 이 결과? 보다는 AI 라고 간소하게표현하고 개조식으로 설명」 · 「ai 태그 왼쪽(좌우 폭 길게 금지) 줄바꾸고 개조식 2단계로」]
    - 대안이었던 「왜 이 결과?」(정본 축자)는 채택하지 않았다 → 정본 용어 개정 항목 ④.
  - Q1b 패널 안 배치 시안(시안 v4 A–D) → **A** [답: Ted 2026-09-26 「좋아 그렇게 가보자 좋아」 · A 권고에 대한 답]
    - A(채택): 상위 = 굵은 종류명 + 보라 점(`--color-ai`), 하위 = 들여쓰기 + 「–」(`--color-accent-500`). 폰 폭에서도 줄바꿈이 항목 경계와 맞는다.
    - B(대안): 종류를 캡션 글자로 두고 세로 안내선 트리로 하위를 묶는다. 선이 좌측 AI 선과 겹쳐 선이 둘이 된다.
    - C(대안): 종류 chip + 건수 요지 줄 + 작은 점 하위. 요지 줄을 서버가 따로 조립해야 하고, chip이 카드의 자료 속성 chip(`SearchHitCard.tsx:44-61·90`)과 같은 모양이 된다.
    - D(대안): ✓ 굵은 줄 + 하위 인라인 나열. 인라인 나열은 폰 폭에서 줄바꿈 위치가 항목 경계와 어긋난다.
- Q2 자료 설명(요약) 노출 범위 → **전문(현행 유지)** [답: Ted 2026-09-26 「기본적으로 데이터셋 보이는 화면 똑같이하고 ai가 검색해준 이유만 보여주면될거같은데」]
- Q3 AI 해석/규칙 근거 라벨 분리 → **라벨 하나(「AI」)** [답: Ted 2026-09-25 「나머진 권고대로」]. 종류 구분은 상위 항목(Q6)이 맡는다.
- Q4 접근성 → **보이는 태그 텍스트** [답: Ted 2026-09-25 「나머진 권고대로」]. 색·선은 보조 수단이다(WCAG 1.4.1).
- Q5 적용 범위 → **검색 결과 카드만** [답: Ted 2026-09-25 「나머진 권고대로」]. 잠긴 카드·Verified 카드에도 같은 패널을 둔다. 상세 검색 근거 편집(`SearchEvidenceEditor.tsx:209`)·조건 검색 판단 패널(`SearchAssessment.tsx:29-44`)은 대상 밖.
- Q6 근거 내용 → **검색된 이유만. 한계·부정 문장 전부 제거** [답: Ted 2026-09-26 「뭐뭐는 아니에요 없었어요 같은 표현은 다 빼버리고 검색된 이유만」 · 「아닌이유를 말하는건 불필요함」]
  - 반대 사유(기록 유지): 정본 §4:97 비고 「좋은 것만 보여주면 다음부터 안 믿는다」. 이 결정은 정본·계약 개정 항목 ①을 낳는다.
- Q7 2단계 구조의 상위 이름 → **「낱말 일치 · 관련 개념 · 연결된 자료 · 파일 근거」** [답: Ted 2026-09-26 「권고대로 좋아」]
  - 내부 기법 이름(온톨로지·계보)은 UI에 쓰지 않는다. 서버 문면 「온톨로지 연결」도 「관련 개념」으로 바꾼다.
  - 사실을 남기는 이유: `where == ("온톨로지 연결 근거",)`로만 맞은 결과는 이 항목이 없으면 이유 0개가 되어 근거 필수(`product.md:76`)를 어긴다.
  - 사실 없는 종류는 통째로 생략한다.
- Q8 쿼리 공통부 → **결과 헤더에 한 번** [답: Ted 2026-09-25 「나머진 권고대로」]
  - 「{lab} 데이터 N건을 뒤졌어요.」 = 기존 `ScopeLine`(`SearchResultsPage.tsx:29`) · 「주제 X로 좁혀 뒤졌어요.」 = 응답 선택 필드 `topic` 신설 · 「질의 해석 없이」 = 기존 degraded 안내(동치 확인 항목 ⑤)

## 미해결 질문
- 해소(2026-09-26 · 오케스트레이터 결정 · Ted 일괄 승인 하 결정 · Ted 부재 중)
  - ⒜ 확장어 문구(「‘강우’와 같은 말인 ‘강수’」)와 그래프 확장 홉(`dataset_search._matched_phrase`)은 「낱말 일치」 아래에 둔다. 「관련 개념」은 온톨로지 개념 주석 일치(`d3_search_annotations.matching`)에만 쓴다.
  - ⒝ 옛 `rationale` 문자열은 새 사실(`rationaleFacts`)에서 다시 만든다. 이유만 담고 한 줄이며 한계·부정 절은 넣지 않는다. 패널은 `rationaleFacts`를 그리고, 필드가 없으면 `rationale`로 대체해 그린다.
  - ⒞ degraded 표기(⑤): 헤더 안내 조건 = `source != "llm"` 또는 `degraded == true`(합집합). 위 ⑤ 결정 참조.
- 남은 질문
  - 조건 검색 갈래(`AssessmentPanel` · `catalog.py:708-723`)의 헤더에 「주제」 문장을 둘지. 이 갈래는 `ScopeLine` 대신 `AssessmentPanel`이 선다(`SearchResultsPage.tsx:115`). 구현 때 정하고 PR 요약에 적는다.
  - 정본·계약 개정 항목 ①~⑤를 누가 어느 절차로 여는지(기획 원본은 무수정 · 계약 설명 문구는 이 구현 PR에서 고칠 수 있음).

## 범위 밖 (명시 제외)
- 관련도 막대, Verified 배지와 「교수 승인이라 위로 올렸어요」, 연구실 칩(`labName`)의 모양.
- 목업에는 있고 카드에는 없는 `원천` 메타(별건).
- 상세 헤더 요약의 여러 줄 펼침 판정(`DetailHeader.tsx:11-24`).
- 상세 검색 근거 편집 화면·조건 검색 판단 패널의 표기(Q5).
- 정본(`40 COLAB-기획/00_기획원본/…`) 파일 수정. 개정 항목은 기록만 한다.
- dev 재시드·배포.

## 확인
- 프론티어 공집합 확인: 2026-09-26 — 설계트리 Q0~Q8 확정 · 미해결 ⒜~⒞ 해소. 남은 2건은 구현 판정(조건 검색 갈래 주제 문장)과 정본 개정 절차 주체로, 설계트리 결정을 바꾸지 않는다.
- Ted 확인 문장(원문 그대로): "좋아결정다하고 한참을 자리비우고 개발시킬거야" (2026-09-26 · 앞선 답: 시안 A 「좋아 그렇게 가보자 좋아」 · 상위 이름 「권고대로 좋아」)
- 재개봉 금지: 아니오

## 참조
- 기획 원본: `40 COLAB-기획/00_기획원본/Co-Lab_ver2_1차마일스톤_목업패키지_260818_이태헌/에픽/E-02_데이터_찾기/documents/Policy_데이터_찾기.md` §4:96-97 · §8:120·146-148 (무수정) · 목업 `…/package/데이터_찾기_260817.html:218-221`(`.rc-why`) · `:958`(항목별 짧은 사실 문장 예) · `:180-183`(`.ai-badge` 「✦ AI 검색」)
- 시안: 시안 v4(A–D 비교) https://claude.ai/artifact/SQfiAUVaU7JFqCaZv7fpQr — A 채택
- UI 레퍼런스(요지 · 조사 원본은 임시 파일이라 여기에 핵심만 옮긴다)
  - 공통 이유는 그룹 머리에 한 번: Netflix 「Because you watched X」(줄 제목) · Cloudscape 생성형 AI 출력 라벨(여러 출력이 모두 AI면 그룹 헤더에 한 번 · https://cloudscape.design/gen-ai/patterns/generative-ai-output-label/) · Consensus/Elicit(목록 위 요약 + 항목별 이유)
  - 항목별 이유는 항목 내용과 별도 블록: Semantic Scholar TLDR(짧은 라벨로 저자 초록과 기계 요약 분리) · Amazon 「Customers say」(원문 리뷰와 AI 문단 블록 분리)
  - 이유를 요인별 짧은 항목으로 분해: Google 「About this result」(matching keywords · related terms 등 · https://support.google.com/websearch/answer/10563935)
  - AI 표지는 아이콘+텍스트 짝: PatternFly 「Icons with AI sparkles should always be paired with text」(https://www.patternfly.org/ai/guidelines/iconography/)
  - 면 색 표지의 한계: Carbon AI label 배경이 강제 색상 모드에서 투명해진 결함(carbon-design-system/carbon PR #23324) → 선·텍스트 표지 병용
- spec: `dev-package/prd/specs/AI-SEARCH-DELTA.md` · `AI-SEARCH-FACTS.md` · `STAGE3-AI-SEARCH-EVIDENCE.md`(같은 검색 결과 계통 · 선행 spec 아님)
- 같은 화면 선행 intent: `dev-package/intent/2026-09-25-operator-search-scope.md`(PR #160 · `67a03a05` · 카드 연구실 칩 `SearchHitCard.tsx:41-47`)
- 코드: `frontend/src/components/search/SearchHitCard.tsx:73-79` · `search.css:93-99` · `frontend/src/routes/SearchResultsPage.tsx:18-31`·`:115-122` · `frontend/test/search.test.tsx:41`·`:159-166` · `contracts/seams/fe-core.yaml:1354`·`:5344-5382`·`:5456-5517` · `contracts/schemas/common.json:186-191` · `services/core-api/src/colab_core/app/dataset_search.py:44-48`·`:66-93` · `app/routes/catalog.py:581-614`·`:650-659`·`:717` · `app/search_conditions.py:48-61` · `app/search_evidence_conditions.py:123-146` · `app/relay.py:455-467` · `frontend/src/shell/tokens.css:42-52`·`:148-179` · `gates/tools/frontend-design-lint.sh:12-31`
- 결정: 〈N〉 (병합 시 기입)
