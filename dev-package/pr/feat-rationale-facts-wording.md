Ted 판정 필요 0건 — 미해결 질문 ⒜~⒞는 Ted 승인 「좋아 진행」 하 오케스트레이터 결정으로 intent에 기록했다(아래 「결정」)

# 검색 사용자가 「AI」 패널에서 친 낱말과 파일 조건만 한 줄씩 읽는다

Plan-Ref: dev-package/intent/2026-09-26-rationale-facts-wording.md
Head-SHA: e75aacc649f9d16d1cef94c0d895e1da5eba1901
검증 상태: 부분 검증

<!-- 저장소 파일의 Head-SHA 는 증거 커밋(e75aacc6)이다. 이 요약 파일 커밋이 그 위에 1개 더 있다. PR 본문은 Head-SHA 를 PR head 로 채워 pr_contract --mode draft 를 통과시킨 것이다. -->

## 목적
- dev 「AI」 패널에서 두 군더더기가 보였다(Ted 발의 「1,2 둘다 intent로 올리자」 · 승인 「좋아 진행」 2026-09-26).
  - ① 파일 근거 항목 끝에 저장소 경로·순번·앵커 괄호 「(출처 …)」가 붙어 한 항목이 여러 줄로 늘어난다.
  - ② 사용자가 치지 않은 주제 라벨(‘강우·강수’)이 「맞은 낱말」로 다시 나온다. 헤더가 이미 주제를 한 번 말한다.
  - ③ 「낱말 일치」 자리 목록에 「확인한 파일 근거」가 섞인다. 그 사실은 「파일 근거」·「연결된 자료」 종류가 말한다.
- 원한 결과: 파일 근거 항목은 「{파일명}에서 {조건} 조건이 맞았어요」로 끝나고, 낱말 일치는 사용자가 친 말과 실제 자리 이름만 싣는다.

## 범위
- intent 승인 기록(`e2032b6f`): `dev-package/intent/2026-09-26-rationale-facts-wording.md`
  - 메타 승인 서명 · 확인 문장 「좋아 진행」 · 해소 ⒜~⒞ · 원한 결과 ③ 추가 · 범위 밖에 `dataset_evidence_backfill.py:386` 명기
  - 초안은 #167 로 develop 에 병합됐다(미승인 표기). 이 PR 이 승인 커밋을 싣는다.
- core-api(`e75aacc6` · 계약·생성물·frontend 변경 0건)
  - `app/search_evidence_conditions.py` `supported_facts`: 「(출처 {label} · {locator})」를 싣지 않는다.
    - 상세 「검색 근거」 목록(`listDatasetSearchEvidence` · `routes/search_evidence.py:117`)은 `d3_search_evidence.list_for_dataset` 를 따로 읽는다. `supported_facts` 는 검색 경로(`routes/catalog.py:605`)에서만 쓴다. 상세 응답은 그대로다.
  - `app/dataset_search.py`
    - `_shown_terms`: 응답 `topic` 과 같은 검색어를 질의 원문에 없으면 뺀다(공백 접기·casefold 대조). 남는 낱말이 없으면 그대로 둔다. 3개 상한 전에 뺀다.
    - `rationale_facts`: 「낱말 일치」 자리 목록에서 「확인한 파일 근거」를 뺀다. `where == ("확인한 파일 근거",)` 는 지금처럼 파일 근거 항목 하나만 낸다.
    - `rationale_facts`·`compose` 에 선택 인자 `topic`·`query` 추가(기본값이면 종전 동작).
  - `app/routes/catalog.py`: `compose` 에 `topic=search_topic`·`query=query` 를 넘긴다. 검색어(`answer["terms"]`)·순위·`where` 판정은 그대로다.
- 시험
  - `tests/test_search_evidence_conditions.py`: 항목에 설명서 이름·절·「출처」 없음 · dev 질의 기대 문구 1건
  - `tests/test_search_assembly.py`: 주제 라벨 ⑴ 확장만이면 빠짐 ⑵ 친 라벨은 남음 ⑶ 라벨만이면 남음 ⑷ 뺀 자리에 4번째 낱말 · ③ 자리 목록 · `rationale` 한 줄 일치 · 파일 근거만이면 파일 근거 항목만
  - `tests/test_search_relay.py`: 라우트 경유 — 친/안 친 두 질의의 결과 집합·순서 동일 · 안 친 쪽 낱말 일치에 ‘강우·강수’ 없음
  - `tests/test_search_reference_evidence.py`(골든 · `search_golden` 표식): 12개 골든 응답 전 카드 항목·`rationale` 에 「(출처」 0건 · 상세 목록 API 가 label·locator 를 패킷 값 그대로 돌려줌
- 제외(intent 범위 밖): 패널 레이아웃·종류 · 결과 헤더 · 상세 검색 근거 UI · 앵커 중복 생성기와 dev 재적용 · 필드별 일치 계산 · ai-service 사전 확장 · 정본 파일

## 계획
- 커밋 순서
  1. `e2032b6f` intent 승인 기록(첫 커밋)
  2. `e75aacc6` core-api 구현 + 시험
  3. 이 요약(PR head)
- 남은 단계
  - advisor ② 수용 검토
  - PR 게시(Claude) → develop 병합(Ted)
  - dev 배포 뒤 재캡처: 같은 계정·질의 4건(`dev-queries.json`) · 「(출처」 0건 · 확장 주제 라벨 0건 계수 · 폰 폭 캡처 1장 이상(intent 검증 절)

## 결정
- 새 ADR 없음. intent 해소(Ted 승인 하 오케스트레이터 결정 · 2026-09-26)
  - ⒜ 라벨만 맞은 카드는 라벨을 남기고 현행 낱말 일치 문형을 쓴다(「‘강우·강수’가 이름·주제·요약에 맞았어요」). 낱말별 맞은 자리를 SQL이 주지 않아(Q2c) 「주제」 하나로 좁히는 새 문형은 데이터로 판정할 수 없다.
  - ⒝ 「확인한 파일 근거」 자리 이름을 낱말 일치 줄에서 뺀다(원한 결과 ③).
  - ⒞ 앵커 중복(`dev-package/tools/dataset_evidence_backfill.py:386`)은 범위 밖 후속.
- 구현 판정
  - 「친 낱말」 판정은 질의 원문 부분 문자열 대조다(공백 접기·casefold). `·` 는 해석이 자르지 않으므로(`ai-service app/interpret.py:68`) 「강우·강수」를 친 질의는 라벨을 남긴다.

## 검증
- 게이트(task `0a6ef136f5644e2991a52cf1fb78febf` · run `efd7cff3fadf410d8d5fb98245251a37` · 기준 커밋 `e75aacc6` · `gates/run.sh task` 1회 · 계 **green 5 / red(판정) 0 / red(준비) 0**)
  - gate-summary: 로컬 task runtime(생성물 · 커밋 안 함)
  - `search-golden` 이라는 이름의 게이트는 `gates/run.sh` 에 없다. 골든 비교는 `test_search_reference_evidence.py`(pytest 표식 `search_golden`)가 `service-tests-core-api` 안에서 돈다. 골든 파일(`eval/k4-search/golden-cases.json` · `fixtures/reference/*`)은 근거 문자열을 대조하지 않아 고치지 않았다.
  - frontend 변경 0건이라 frontend 게이트는 돌리지 않았다.

| 게이트 | 종료코드 | 요지 |
|---|---|---|
| contract-lint | 0 | seam 3건 · 룰 위반 0 |
| contract-breaking | 0 | task 실행분(기준 HEAD) green · 보충 실행 `COLAB_BREAKING_BASE_REF=origin/develop` exit 0 · 파괴적 변경 없음 |
| generated-up-to-date | 0 | 등기부 20건 재생성 일치 |
| service-tests-core-api | 0 | 1914 통과 · skipped 0 · deselected 9 |
| intent-ref | 0 | Intent-Ref 2건 유효(커밋 2 · 대상 경로 7) · 승인 intent 58건 대조 |

- RED 선확인(구현 전 · 시험만 추가한 상태): core-api 11 failed · 1903 passed
  - 예: `TypeError: rationale_facts() got an unexpected keyword argument 'topic'` · `assert not ['f1.npy에서 주기 조건이 맞았어요 (출처 처리 설…` · 라우트 `‘강우’, ‘강우·강수’가 이름·주제·요약·포맷·변수에 …`
  - 구현 뒤 1914 passed

| 원한 결과 (intent) | 실제 | 근거 | 가치 상태 |
|---|---|---|---|
| ① 파일 근거 항목에 출처 괄호 없음 | 전: 「pred_sample.npy에서 파일 역할(예측 결과) 조건이 맞았어요 (출처 01.level-data/01.precipitation/DATASETS.md · seq 5 pred_sample · DATASETS.md#01.level-data/01.precipitation/DATASETS.md#seq-5)」 → 후: 「pred_sample.npy에서 파일 역할(예측 결과) 조건이 맞았어요」 | `test_supported_fact_is_the_reason_sentence_without_source`(dev 질의 · 같은 조건) · 골든 12응답 「(출처」 0건 | 확인됨(시험) · dev 미재캡처 |
| ① `rationale` 한 줄에도 괄호 없음 | 같은 사실에서 다시 만든다 | `rationale_line` · 골든 `rationale` 대조 | 확인됨(시험) |
| ① 상세 「검색 근거」는 출처 유지 | 목록 API 가 label·locator 를 저장값 그대로 돌려준다 | `test_search_reference_evidence.py` 상세 대조 | 확인됨(시험) |
| ② 안 친 주제 라벨은 낱말 일치에서 빠짐 | `HSR 레이더 반사도 원자료`·`rn15 15분 누적강수` 전: 「‘강우’, ‘강우·강수’가 이름·주제·요약에 맞았어요」 → 후: 「‘강우’가 이름·주제·요약에 맞았어요」 | `test_사용자가_치지_않은_주제_라벨은_맞은_낱말에서_빠진다` · 라우트 시험 | 확인됨(시험) · dev 미재캡처 |
| ② 친 라벨은 남음 · 라벨만이면 남음 · 뺀 자리에 4번째 낱말 | 세 경우 단언 | `test_질의에_친_주제_라벨은_남는다` · `test_주제_라벨만_맞았으면_라벨을_남긴다` · `test_라벨을_빼면_다음_실제_낱말이_상한_안에_든다` | 확인됨(시험) |
| ② 검색어·순위 불변 | 친/안 친 질의의 결과 id 순서 동일 · `answer["terms"]` 무변경 | `test_topic_label_the_user_did_not_type_is_not_a_matched_term` · 골든 12건 회수 불변 | 확인됨(시험) |
| ③ 자리 목록에 「확인한 파일 근거」 없음 | `hsr_sample`·`rn15_sample` 전: 「‘강우’, ‘강우·강수’가 이름·주제·요약·확인한 파일 근거에 맞았어요」 → 후: 「‘강우’가 이름·주제·요약에 맞았어요」(「연결된 자료」 항목은 그대로) | `test_낱말_일치_자리_목록에_확인한_파일_근거가_없다` | 확인됨(시험) · dev 미재캡처 |
| ③ 파일 근거로만 맞으면 파일 근거 항목 하나 | 종류 = `evidence` 하나 | `test_파일_근거로_맞으면_파일_근거_항목이_선다` | 확인됨(시험) |
| `pred_sample` 낱말 일치 | 전·후 같음 「‘강우’, ‘예측’, ‘pred_sample.npy’가 이름·주제·요약·포맷·변수에 맞았어요」 `[추론 · 캡처는 앞 3개만 보여 뒤 낱말 목록 미확인]` | 캡처 `rationaleFacts[kind=term]` | 미검증(dev) |
| 가치 가설(dev 재캡처 계수 · Ted 화면 판정) | 미실행 | dev 배포 전 | 미검증 |

- 전 문자열 출처: `origin/deploy/dev-592ff4b7` `dev-package/reports/search-rationale-panel/20260926-dev/dev-search-response-llm.json`(dev `592ff4b7693d` · 운영자 · 질의 「강우 예측 pred_sample.npy 파일의 바로 앞 입력 데이터셋」 · `topic: 강우·강수`). 후 문자열은 서버 시험의 단언값이다(dev 실측 아님).

Evidence-Ref: 로컬 task runtime gate-summary(task `0a6ef136f5644e2991a52cf1fb78febf` · run `efd7cff3fadf410d8d5fb98245251a37`) — CI 증거 아님
Evidence-SHA256: 미생성(CI 증거 번들 없음)
CI-Ref: 미게시(PR 게시 뒤 CI)

## 볼 곳
- 전(dev 캡처): `origin/deploy/dev-592ff4b7` 의 `dev-package/reports/search-rationale-panel/20260926-dev/`
  - `dev-search-response-llm.json` · `dev-queries.json` · `dev-llm-light-390.png`
- 후: 서버 시험 단언값(위 표). dev 캡처는 배포 뒤 `dev-package/reports/search-rationale-panel/<날짜>-dev/` 에 둔다.
- 선행: #165(패널) · #167(이 intent 초안 병합)

## 남은 제약
- dev 재캡처·브라우저 캡처 미실행 — 배포는 이 PR 범위 밖이다. 화면 줄 수 감소는 배포 뒤 agent-browser 폰 폭으로 본다.
- 잠긴 카드(`bodyAccessible: false`)의 파일 근거 항목도 이제 출처 라벨·앵커를 싣지 않는다(intent ① 「이 차이도 함께 사라진다」).
- 후속(범위 밖)
  - 앵커 중복 `DATASETS.md#…/DATASETS.md#seq-N`: 생성기 `dev-package/tools/dataset_evidence_backfill.py:386` 수정 + payload 재생성 + dev 재적용(dev 데이터 쓰기 · 사용자 승인 범위).
  - 자리 목록에 「온톨로지 연결 근거」가 다른 자리와 함께 들어오면 낱말 일치 줄에 그 이름이 남는다(`d3_catalog.py:1075-1079` · `dataset_search.py` 자리 잇기). 선행 intent Q7(내부 기법 이름 미노출)과 긴장한다. 이 intent 의 결정 대상이 아니라 고치지 않았다. 걸리는 검사: 없음(시험·게이트 밖).
  - 자리 이름 「이름·주제·요약」의 「주제」는 묶음 이름이라 라벨을 뺀 뒤에도 남는다(Q2c · 필드별 일치 계산은 별건).

## 게시 절차
- Claude: `feat/rationale-facts-wording` → `develop` 일반 PR 게시(본문 = 이 파일 · Head-SHA 를 PR head 로 채움)
- 게시 전: `python3 scripts/harness/pr_contract.py` 에 PR 본문 파일과 `--head`(PR head 40자리) `--mode draft` → exit 0
- 병합: Ted. Claude 는 병합·배포하지 않는다.
