# Intent: D10 모델 호출 실행 원장 — K3·K4 공통, 별도 집행 단위

메타 — 발의자: Ted(게이트 ① 결정 ⑤) · 정리: Claude(researcher) · 작성 2026-09-24 · 승인 미승인

## 문제
- `PLAN-SoT.md:78`(D10 정의)와 `PLAN-SoT.md:313`(㊷ 근거③)이 "실행 원장"에 공급자·처리 리전을
  **필수 필드로 기록**할 의무를 이미 걸어 뒀지만, 실물 테이블·로그 스키마·필드 목록은 어디에도 없다.
  `dev-package/DOMAINS.md:78`이 실행 원장을 D10 소유물로 못박은 것과 `DOMAINS.md:48`
  "D10 AI Services — 제안만 생산, 기록하지 않는다"가 문면상 부딪힌다 — 이 intent는 그 부딪힘을
  "제안(도메인 데이터)은 기록하지 않는다"와 "호출 자체(운영 메타데이터)는 기록해야 한다"로 풀 것을 제안한다.
- 2026-09-24 게이트 ① 결정 ⑤(Ted, 「좋아 권고대로」)는 이 실행 원장이 K3(계보 제안) 작업의
  부산물이 아니라 K3·K4가 공유하는 별도 intent라고 판정했다. 지금 K3 lineage 작업 브랜치
  안에서 이 항목을 같이 처리하면 두 회차의 완료 조건이 뒤섞인다.

## 원한 결과 (proposed outcome)
- `LlmQueryInterpreter.interpret`(search.interpret, `interpret.py:144-195`)와 향후 K3 계보 제안
  모델 호출(lineage.suggest) 각각이, 성공·실패·폴백 어느 경로로 끝나도 **정확히 1건**의 실행
  원장 레코드를 남긴다.
- 그 레코드는 공급자·모델 id·호출 지점·지연·토큰·결과 상태를 담고, **질의 원문(raw query)이나
  질의에서 파생된 검색어(terms)는 담지 않는다.**
- 게이트·CI가 도는 동안에는 모델을 부르지 않으므로(`config.py` interpret_mode 기본 `literal`)
  원장에 레코드가 쌓이지 않는다 — 이것이 정상이고, "레코드 0건"을 실패로 재는 시험을 만들지 않는다.

## 영향 범위
- 사용자 / 화면: 없음. 원장은 운영 관측용이며 어떤 화면에도 노출되지 않는다.
- 서비스 · 스키마 · 계약: `services/ai-service/src/colab_ai/app/interpret.py`,
  `domains/d10_ai_services.py`(로깅 호출 지점 추가) · 저장소를 새 테이블로 정하면 `db/ai/versions/`
  alembic 리비전 1건 추가. `core-api`는 건드리지 않는다 — 원장은 D10 안에서 나고 D10 안에서 산다
  (`DOMAINS.md:91-96`의 "제안은 D10 안에서 태어나 D10 안에서 죽는다" 원칙을 호출 기록에도 그대로 적용).
- 계약 파괴 여부: 아니오. 기존 `Interpretation`/`SearchResults` 응답 계약에 필드를 추가하지 않는다.

## 제약
- D9/D10 저장소는 D1~D8과 마이그레이션 체인 분리(`DOMAINS.md:137`) — 새 테이블을 두면 반드시
  `db/ai` 체인(현재 head `0007_merge_topic_vocab_and_rc7_category`)에 붙인다. `config.py`
  주석은 "D9 사전 DB 가 이 단위가 붙는 유일한 저장소"라고 적어 뒀다(`config.py:76`) — 원장을
  DB 테이블로 두기로 하면 이 문구도 함께 정정해야 한다(아래 미해결 질문).
- CLAUDE.md §3 원칙 — AI 없이도 v2는 완결된 제품이어야 한다(`config.py:1-9` 그대로 인용).
  원장 적재 실패가 검색·계보 제안 응답을 막으면 안 된다 — 원장 쓰기는 best-effort, 응답 경로에서
  분리한다(로깅과 동일한 fire-and-forget 패턴).
- 질의 원문 비저장 — `interpret.py:1-14` 자체가 "모델이 순위·식별자·점수·문장을 얹어도 읽지 않는다"는
  최소 신뢰 원칙을 이미 코드로 못박았다. 같은 태도를 원장에도 적용해야 한다: 질의 원문이나
  검색어를 원장에 넣으면 검색 로그가 사실상 사용자 질의 로그가 되어 최소 수집 원칙과 충돌한다.

## 설계트리 (grill-me 결과)
- Q1 원장을 어디에 둘까(로그 vs DB 테이블 vs core-api 응답 메타데이터)?
  - (a) 구조화 로그 줄(stdout JSON, `_degraded_log`와 같은 `logging` 채널) — 장점: 기존
    `INTERPRETER_LOGGER`/`DEGRADED_LOGGER` 관례 재사용, DB 마이그레이션 불필요, 응답 경로에
    쓰기 지연을 안 만듦. 단점: 조회·집계가 로그 수집기 유무에 달림 — 이 저장소에는 loki·cloudwatch
    앱 로그 수집 배선이 보이지 않는다(인프라 `infra/notifications/`는 AWS 이벤트 알림 전용이고
    앱 stdout 수집기가 아니다) → dev/staging에서 원장을 "볼 방법"이 아직 없다.
  - (b) `db/ai` 체인에 새 테이블(alembic 리비전) — 장점: 조회·집계가 SQL로 바로 됨, `config.py`가
    이미 "D9 사전 DB가 이 단위가 붙는 유일한 저장소"라 적어 둔 전제를 조정하면 D10 도메인 안에
    깔끔히 들어감. 단점: config.py 주석 정정 필요, 쓰기 실패를 응답 실패로부터 격리하는 코드가
    별도로 필요(트랜잭션 밖 best-effort insert).
  - (c) core-api가 relay 응답에서 메타데이터를 기록 — 기각. `relay.py:292` `_record_suggest_failure`는
    실패 건수만 세고 모델 메타데이터를 모른다. 이 경로를 쓰면 D10 호출 세부사항이 core-api로
    새어나가 `DOMAINS.md:91-96`의 "제안은 D10 안에서 태어나 D10 안에서 죽는다" 경계를 깬다.
  - A (권장, Ted 최종 판단 대기): (b) DB 테이블 — "필수 필드로 기록"(㊷ 근거③)이라는 문면은
    조회 가능한 기록을 요구하는 것으로 읽는 것이 자연스럽고, (a)는 지금 수집기가 없어 사실상
    기록이 안 보이는 상태와 같다. 다만 (a)를 최소선으로 먼저 깔고 (b)를 다음 회차로 미루는
    단계적 채택도 가능 — 이 경우 "기록 의무"를 (a)만으로 충족했다고 선언하지 않는다.
- Q2 처리 리전 필드를 실제로 채울 수 있는가?
  - A 모른다 — OpenAI Chat Completions API 응답은 리전을 반환하지 않는다(`interpret.py:158-166`
    페이로드/응답 파싱에 리전 필드 없음). 알 수 있는 것은 고정된 엔드포인트 호스트
    (`base_url="https://api.openai.com/v1/chat/completions"`, `interpret.py:150` 부근)뿐이고,
    이는 리전이 아니라 API 표면 주소다. 데이터 레지던시 협약(예: 특정 리전 전용 엔드포인트) 없이는
    "처리 리전" 필드는 항상 `[미상]`이 되고, 이를 지어내지 않는다(§8.4 "국내 리전 고정"은 저장
    계층 얘기지 모델 호출 리전을 기술적으로 보장하지 않는다 — `PLAN-SoT.md:241`).
  - Q2a 그러면 ㊷ 근거③의 "처리 리전을 필수 필드로 기록"을 어떻게 충족하나?
    → A 필드는 만들되 값은 "OpenAI 공개 API는 리전을 노출하지 않음 — 알 수 없음"을 명시적으로
    기록한다(빈 문자열이 아니라 상태값 `unknown`). Ted 판단 필요 — 이 상태를 의무 충족으로
    볼지, 아니면 리전 고정 엔드포인트 계약이 별도로 필요하다고 볼지.

## 미해결 질문
- 저장 위치 최종 선택 (a)/(b)/(c) 중 — 위 권장은 (b)이나 Ted 판정 필요.
- 처리 리전 필드의 값이 항상 `unknown`일 수밖에 없는 상태를 §8.4 의무 충족으로 인정할지 — Ted 판정 필요.
- 원장 보존 기간 — 이 intent는 정하지 않는다(범위 밖).
- dev/staging에 구조화 로그를 볼 수단(로그 수집기)이 없다는 사실 자체를 별도 인프라 intent로
  뗄지, 이 intent 안에서 (b)를 택해 우회할지 — Ted 판정 필요.

## 범위 밖 (명시 제외)
- 과금 정산(billing reconciliation).
- 대시보드·알람 등 원장 데이터의 시각화.
- 보존 정책 수립(위 미해결 질문에 남긴다).
- K3 계보 제안 코드 자체의 구현(별도 K3 lineage 작업 — 이 intent는 그 작업이 완성되면 호출부에
  붙일 원장 훅의 계약만 먼저 정한다).

## 확인
- 프론티어 공집합 확인: 2026-09-24
- Ted 확인 문장(원문 그대로): "좋아 권고대로"
- 재개봉 금지: 아니오 — 이 intent 자체가 미승인 초안이며 Q1·Q2a는 Ted 판정 대기 상태로 남는다.

## 참조
- 결정: 2026-09-24 K3 게이트 ① 결정 ⑤ (Ted, 「좋아 권고대로」)
- 근거: `dev-package/PLAN-SoT.md:78`, `:313`(㊷), `:241`(§8.4)
- 근거: `dev-package/DOMAINS.md:48`, `:78`, `:91-96`, `:137`
- 근거: `services/ai-service/src/colab_ai/app/interpret.py:1-40,120-200`
- 근거: `services/ai-service/src/colab_ai/domains/d10_ai_services.py:34-41,199`
- 근거: `services/ai-service/src/colab_ai/kernel/config.py:1-90`
- 근거: `services/core-api/src/colab_core/app/relay.py:292-510`
- 근거: `db/ai/schema.sql`(원장/ledger 테이블 없음, 확인 완료), `db/ai/versions/`(체인 head `0007`)
