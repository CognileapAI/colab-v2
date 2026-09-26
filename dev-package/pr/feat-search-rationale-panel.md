Ted 판정 필요 1건 — `interpretation` 응답 필드·범위 줄 문장 「질문의 낱말 그대로 찾았어요.」는 Ted 가 본 합집합 결정을 〈148〉 준수를 위해 오케스트레이터가 부재 중 교체한 것

# 검색 사용자가 결과 카드에서 자료 설명과 「검색된 이유」를 한눈에 구분한다

Plan-Ref: dev-package/intent/2026-09-25-search-rationale-separation.md
Head-SHA: 53327e07a98f5e40aa13ce1558a85c4eed9e359d
검증 상태: 부분 검증

<!-- 저장소 파일의 Head-SHA 는 증거 커밋(53327e07)이다. 이 요약 파일 커밋이 그 위에 1개 더 있다. PR 본문은 Head-SHA 를 PR head 로 채워 pr_contract --mode draft 를 통과시킨 것이다. -->

## 목적
- 결과 카드에서 요약(자료 등록자가 쓴 설명)과 검색 근거가 같은 글자·배경으로 붙어 구분되지 않았다(Ted 발의).
- 근거 문장에 카드마다 같은 공통부와 한계·부정 문장이 반복돼 검색된 이유가 묻혔다.
- 원한 결과: 요약 아래 별도 「✦ AI」 패널 + 근거 종류별 2단계 목록(이유만) · 공통부는 결과 머리에 한 번.

## 범위
- 계약(비파괴): `contracts/seams/fe-core.yaml`
  - `SearchResultRow.rationaleFacts`(선택 · `kind` = term/concept/linked/evidence · `items` = `AiRationale` 한 줄 배열)
  - `SearchResults.topic`(선택)
  - `SearchResults.interpretation`(선택 · `llm`|`literal` · 해석 출처)
  - `rationale`·검색 오퍼레이션 설명 개정 · `degraded` 설명에 `〈148〉` 문장 추가(뜻은 종전 그대로)
  - 생성물 `frontend/src/generated/fe-core.ts` 재생성
- core-api
  - `dataset_search.py`: `rationale()` → `rationale_facts` · `ordered_facts` · `rationale_line`, `compose` 인자에서 연구실·건수·주제·해석 여부 제거
  - `routes/catalog.py`
    - AI 해석 경로: 종류별 사실 조립, 응답 `topic` 추가
    - 조건 검색 경로: 고정 문장을 「파일 근거」 1항목(해요체)으로 바꾸고 「미확인입니다」 삭제
  - `search_evidence_conditions.explain` → `supported_facts`(확인 항목만)
  - `search_conditions.explain_unverified_conditions` 삭제
  - `relay.py`: `degraded` 는 ai-service 값 그대로(합집합은 `48585a6d` 에서 되돌림)
  - `routes/catalog.py`: 해석 `source` 가 `llm`·`literal` 이면 응답 `interpretation` 을 싣는다
  - `dataset_search.py`: 「낱말 일치」 조사를 닫는 따옴표 앞 마지막 한글 음절의 받침으로 고른다(`53327e07`)
    - 예: 「‘강우량’이」·「‘강수’가」 · 같은 말 엣지 「‘최근린보간’과」·「‘강수’와」
    - 한글로 끝나지 않는 말(「‘NDVI’가」)은 종전 모양 그대로
- 계약 설명(스키마 무변경): `contracts/seams/core-ai.yaml` 해석 `source` 설명 → 「그 사실은 fe-core 응답 `interpretation` 과 검색 결과 범위 줄이 밝힌다(카드 근거 접두가 아니다)」(`53327e07` · 생성물 영향 없음 · generated-up-to-date green)
- frontend
  - `SearchHitCard.tsx`: `RationalePanel` 추가
  - `search.css`: 패널 규칙 추가, 「코랄」 주석을 보라(accent · 판정 48)로 정정
  - `SearchResultsPage.tsx`: `ScopeLine` 뒤에 주제 문장 추가 · `interpretation == "literal"` 이고 `degraded == false` 면 끝에 「질문의 낱말 그대로 찾았어요.」
- 제외(intent 범위 밖): 관련도 막대 · Verified 배지 · 연구실 칩 · `DetailHeader` · 상세 검색 근거 편집 · 조건 검색 판단 패널 · 정본(기획 원본) 파일 · dev 재시드·배포 · `common.json` `AiRationale`(이유 항목도 한 줄이라 무수정)

## 계획
- 커밋 순서
  1. `34964b91` 계약 + 생성물
  2. `c97e5e23` core-api
  3. `86ed3c17` frontend
  4. `f4cba295` 브라우저 증거
  5. `3d63a686` 이 요약
  6. `48585a6d` 정정: `degraded` 합집합 되돌림 · `interpretation` 필드 · 범위 줄 문장 · intent 추기
  7. `82c3f0d6` 정정 증거 캡처 + 이 요약 갱신
  8. `53327e07` 조사 받침 분기 + core-ai `source` 설명 정정
  9. 이 요약 갱신(PR head)
- 남은 단계
  - advisor ② 수용 검토
  - PR 게시(Claude) → Ted 판정 1건 → develop 병합(Ted)
  - #163(intent 승인 PR)을 먼저 병합하거나 함께 병합한다. 이 PR 은 #163 위에 쌓였다
  - dev 배포 후 교수·운영자 계정 실측(가치 가설 확인)

## 결정
- 새 ADR 없음. 구현 중 판정한 것
  - 조건 검색 갈래(`AssessmentPanel`)에는 「주제」 문장을 두지 않는다. 그 갈래에는 해석 주제가 없고 서버가 `topic` 을 싣지 않는다(intent 남은 질문 1).
  - 「파일 근거」
    - 확인(supported) 조건이 있으면 그것이 일반 문장 「확인한 파일 근거가 질문 조건에 맞았어요」를 대신한다.
    - 확인 조건이 없는 파일은 항목을 만들지 않는다.
  - 「관련 개념」
    - 개념 주석 일치가 있으면 「자료에 적힌 개념 ‘X’에 연결돼요」로 적는다.
    - 없고 `where == ("온톨로지 연결 근거",)` 뿐이면 「자료에 적힌 개념이 질문과 연결돼요」로 적는다. 이것으로 근거 필수를 지킨다.
  - 「연결된 자료」: 「‘파일명’ 파일이 속한 자료의 바로 앞 단계 자료예요」로 적고 「계보·부모」 말은 쓰지 않는다.
  - ~~`degraded` 합집합을 `relay.py` 해석 결과 지점에서 계산한다.~~ → 정정(`48585a6d` · intent ⑤ 「추기 2026-09-26」 · 오케스트레이터 결정 교체 · Ted 판정 아님)
    - 합집합은 설정으로 고른 낱말 그대로 해석에도 경고 상자를 세워 `PLAN-SoT §9-〈148〉` 과 어긋났다.
    - `degraded` = ai-service 값 그대로. 해석 출처는 응답 `interpretation` 이 싣는다.
    - 로컬 ai-service 실측 값: `degraded:false` · `source:"literal"` · `degradedReason` 있음(loopback 전달 로그).
    - 이 경우 응답은 `degraded:false` · `interpretation:"literal"` 이고, 경고 상자 없이 범위 줄 끝에 「질문의 낱말 그대로 찾았어요.」가 선다.

## 검증
- 게이트(최종 · `53327e07` · task `c629781b24b843cebd7039f2b45d78ba` · run `320e636c260b4c73bc5cb2860797be9d` · `gates/run.sh task` 1회 · 계 **green 8 / red(판정) 0 / red(준비) 0**)
  - gate-summary: 로컬 task runtime `.git/colab-harness/c5c2052bdc2e059a73f9df08ae7d6b35/c629781b24b843cebd7039f2b45d78ba/320e636c260b4c73bc5cb2860797be9d/gate-summary.json`(생성물 · 커밋 안 함)
  - 이전 실행(표로 대체): 정정 전 task `dadf133f898543d48424f0b693e8f3ad` · 정정 뒤 task `f68a22d3f91b4775a81334b6535e1bfe` · 각각 green 8 / 0 / 0

| 게이트 | 종료코드 | 요지 |
|---|---|---|
| contract-lint | 0 | seam 3건 · 룰 위반 0 |
| contract-breaking | 0 | task 실행분(기준 HEAD) green · 보충 실행 `COLAB_BREAKING_BASE_REF=origin/develop`(`536e7a68`) exit 0 · 3건 대비 파괴적 변경 없음 |
| generated-up-to-date | 0 | 등기부 20건 재생성 일치 |
| frontend-typecheck | 0 | tsc 오류 0 |
| frontend-test | 0 | vitest 145 파일 · 1902 통과 · 실패 0 |
| frontend-design-lint | 0 | 색 리터럴 0 · 미정의 var 0 · 인라인은 변수 대입 7건뿐 · 프리미티브 맨 정의 0 |
| service-tests-core-api | 0 | 1905 통과 · skipped 0 · deselected 9 |
| intent-ref | 0 | Intent-Ref 11건 유효(커밋 11 · 대상 경로 17) · 승인 intent 56건 대조 |

- RED 선확인
  - core-api 43 failed(예: `compose() missing … 'lab_name'`, `KeyError: 'rationaleFacts'`, `assert '확인하지 못' not in …`)
  - frontend 6 failed(`search-rationale-panel` 없음)
  - 구현 뒤 green
  - 조사 분기(`53327e07`) RED: `test_낱말_일치_조사는_끝_글자_받침을_본다` 「assert '‘강우량’가 이름에 맞았어요' == '‘강우량’이 이름에 맞았어요'」 · `test_같은_말_엣지도_읽어_준다` 「‘최근린보간’와」 → 구현 뒤 assembly 24 passed
  - 정정(`48585a6d`) RED: core-api `test_search_relay.py` 4 failed(`assert (True is False)` · `KeyError: 'interpretation'`) · frontend 1 failed(범위 줄에 「질문의 낱말 그대로 찾았어요.」 없음) → 구현 뒤 relay·assembly 55 passed · vitest search 28 passed

| 원한 결과 (intent) | 실제 | 근거 | 가치 상태 |
|---|---|---|---|
| 요약 아래 별도 DOM 근거 패널(면 accent-50 · 좌측 2px AI 선 · 본문 text-body) | `.hit-rationale` 이 `hit-summary` 와 다른 요소로 선다. 계측값: 라이트 bg `rgb(241,232,255)`·선 `2px solid rgb(103,66,245)` · 다크 bg `rgb(48,36,69)`·선 `rgb(198,175,255)` | `SearchHitCard.tsx` `RationalePanel` · `search.css` `.hit-rationale` · `probe-llm.json` · vitest 「근거는 요약과 다른 요소…」 | 확인됨 |
| 맨 위 왼쪽 「✦ AI」 태그(accent-700 글자 · accent-200 테두리 · surface 바탕 · 내용 폭) | 태그 높이 20px · 폭 44px(패널 804px) · 목록 밖 · 목록보다 앞 | `probe-llm.json` `tagWidth`·`tagOutsideFacts` · vitest | 확인됨 |
| 2단계 목록(상위 = 굵은 종류 + 보라 점 · 하위 = 「–」 들여쓰기) | 종류 4개가 서버 순서대로 그려지고, 빈 종류는 생략된다 | vitest 「근거 종류가 서버 순서대로…」·「사실이 없는 종류는…」 · 캡처 | 확인됨 |
| 잠긴·Verified 카드도 같은 패널 | 두 카드 모두 패널이 선다 | 캡처 `search-rationale-llm-light-1280.png` · vitest | 확인됨 |
| 한계·부정 문장 제거 · 이유만 | 서버 단언: 부정 문구 7종 부재 · 파일 근거는 확인 항목만. `test_search_reference_evidence` 골든 011·012 에서 「미확인」「불일치」 부재 | `test_search_assembly.py` · `test_search_evidence_conditions.py` · `test_search_reference_evidence.py` · `test_search_numeric_quality.py` | 확인됨 |
| 관련 개념만으로 맞아도 이유 ≥1 · 「온톨로지」 미노출 | concept 항목 1개가 남는다. 실제 개념 선택 경로에서도 concept 에 ‘강수’가 있다 | `test_관련_개념으로만_맞아도_이유가_하나_이상_있다` · `test_search_concept_integration.py` | 확인됨 |
| 공통부를 결과 머리에 한 번(범위 · 주제) | 범위 줄 「… 2건을 뒤졌어요. 주제 ‘강우·강수’로 좁혀 뒤졌어요.」가 서고 카드에는 없다 | `probe-llm.json` `scope` · relay 시험 topic 유무 | 확인됨 |
| 「해석 없이 찾았다」를 결과 머리에 한 번 · 설정으로 고른 낱말 그대로 해석은 `degraded` 아님(`〈148〉`) | 로컬 ai-service(`degraded:false` · `source:literal`) 경유 응답 `degraded:false` · `interpretation:"literal"`. 범위 줄 「A 연구실 데이터 2건을 뒤졌어요. 질문의 낱말 그대로 찾았어요.」 한 줄(글자색 `rgb(86, 92, 99)` = `--color-text-muted`) · 경고 상자 없음. `degraded:true` 면 경고 상자만 서고 범위 줄 문장은 없다 | `probe-literal-scope.json` · `search-rationale-literal-scope-light-1280.png` · `test_search_relay.py` `test_an_intentional_literal_interpretation_is_not_degraded`·`test_a_broken_literal_interpretation_stays_degraded`·`test_an_unknown_interpretation_source_is_not_said`·`test_a_model_interpretation_is_not_degraded` · vitest 「낱말 그대로 해석이고 degraded 가 아니면…」·「degraded 면 경고 상자가 말하고…」·「모델 해석이면…」 | 확인됨(로컬 · dev 아님) |
| `rationaleFacts` 없으면 `rationale` 한 줄로 그림(구 응답 호환) | 같은 패널 안 `search-rationale` 에 원문 그대로 그린다 | vitest 「rationaleFacts 가 없으면…」 | 확인됨 |
| agent-browser 캡처(라이트·다크 · 폰 폭) | 격리 fixture + 이 브랜치 서버로 찍었다. 가로 넘침 없음. 「llm」 캡처 4장은 로컬 가짜 해석기(loopback 스텁)가 낸 `source:"llm"` 응답을 거쳤다 | 아래 「볼 곳」 | 부분 확인(dev 아님 · 실제 LLM 아님) |
| 「낱말 일치」 조사가 받침을 따른다 | 「‘강우량’이」·「‘강수’가」·「‘NDVI’가」 · 엣지 「‘최근린보간’과」·「‘강수’와」 | `test_search_assembly.py` `test_낱말_일치_조사는_끝_글자_받침을_본다`·`test_같은_말_엣지도_읽어_준다` | 확인됨 |
| 가치 가설(Ted 가 dev 에서 구분·이유만 판정) | 미실행 | dev 배포 전 | 미검증 |

Evidence-Ref: 로컬 task runtime gate-summary(task `f68a22d3f91b4775a81334b6535e1bfe` · run `a9a2692f67414aedb67e72347a3adeb0` · 정정 전 task `dadf133f898543d48424f0b693e8f3ad`) — CI 증거 아님
Evidence-SHA256: 미생성(CI 증거 번들 없음)
CI-Ref: 미게시(PR 게시 뒤 CI)

## 볼 곳
- `dev-package/reports/search-rationale-panel/20260926/`
  - `search-rationale-llm-light-1280.png`
  - `search-rationale-llm-dark-1280.png`
  - `search-rationale-llm-light-390.png`
  - `search-rationale-llm-dark-390.png`
  - `search-rationale-literal-light-1280.png`(정정 전 · 합집합 때 경고 상자가 선 모습 · 대체됨)
  - `search-rationale-literal-scope-light-1280.png`(정정 후 · 범위 줄 끝 「질문의 낱말 그대로 찾았어요.」 · 경고 상자 없음)
  - `probe-llm.json` · `probe-literal.json`(정정 전) · `probe-literal-scope.json`(정정 후)
- 실행 방법
  - `scripts/e2e-login.py --journey`(격리 fixture DB · 실제 로그인 · 새로고침 지속 · 로그아웃 포함 PASS)
  - agent-browser 0.27 · `set media light|dark` · `set viewport 1280×900 | 390×844`

## 남은 제약
- 실제 LLM 해석은 부르지 않았다.
  - 로컬 ai-service 가 `COLAB_AI_QUERY_INTERPRETATION=literal` 이다.
  - 「llm」 캡처 4장은 로컬 가짜 해석기 — `source:"llm"` 응답 모양을 내는 loopback 스텁(커밋 안 함) — 를 거쳤다. 실제 LLM 이 낸 주제·확장어가 아니다.
  - 실제 LLM 검증은 develop 병합·dev 배포 뒤 dev 에서 한다(교수·운영자 계정 캡처 · intent 가치 가설).
- 0건 화면 관찰: `ScopeLine` 이 건수와 무관하게 서므로 주제 문장(「주제 ‘X’로 좁혀 뒤졌어요.」)·낱말 문장(「질문의 낱말 그대로 찾았어요.」)이 0건 화면에도 나타난다(`SearchResultsPage.tsx:122`).
  - 무해하다: 0건일 때도 뒤진 범위를 밝히는 문장이고 판정 문장이 아니다.
  - 다만 intent :33 「0건 화면과 검색 불가 화면은 변하지 않는다」 문면과 긴장한다. 검색 불가 화면은 변하지 않았다. 0건 화면에서 두 문장을 끌지는 Ted 판단 대상이다.
- 캡처 fixture 는 「낱말 일치」 종류만 만든다. 관련 개념·연결된 자료·파일 근거의 화면 모양은 vitest 로만 확인했다.
- ~~⚠ `〈148〉` 과 긴장~~ → 해소(`48585a6d`). `degraded` 는 ai-service 값 그대로이고, 낱말 그대로 해석은 범위 줄 문장으로 밝힌다.
  - 이 정정은 오케스트레이터 결정 교체다. Ted 판정은 아니며 게시 전 Ted 확인 대상이다.
- ~~`core-ai.yaml` 해석 `source` 설명 낡음~~ → 해소(`53327e07` · 설명만 · 스키마 무변경).
- 정본·계약 개정 항목 ①~⑤(한계 병기 · 한 줄 · 코랄 · 「왜 이 결과?」 · degraded)
  - 계약 설명은 이 PR 에서 고쳤다.
  - 기획 원본 개정은 별도 절차다.
- ~~「낱말 일치」 조사가 받침을 보지 않는다~~ → 해소(`53327e07` · 위 「범위」).
- develop 이 이 가지보다 1커밋 앞섰다(`536e7a68` · #162 문서만). 병합 부모 대조가 red 면 develop 을 이 가지에 병합해야 한다 — 병합은 Ted 몫이다.
- 시안: 시안 v4(A–D 비교) https://claude.ai/artifact/SQfiAUVaU7JFqCaZv7fpQr (A 채택)

## 게시 절차
- Claude: `feat/search-rationale-panel` → `develop` 일반 PR 게시(본문 = 이 파일 · Head-SHA 를 PR head 로 채움)
- 게시 전: `python3 scripts/harness/pr_contract.py` 에 PR 본문 파일과 `--head`(PR head 40자리) `--mode draft` → exit 0
- 병합: Ted(#163 먼저 또는 함께). Claude 는 병합하지 않는다.
