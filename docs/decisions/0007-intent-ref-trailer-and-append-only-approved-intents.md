# ADR-0007: 커밋은 Intent-Ref 로 intent 를 가리키고 승인된 intent 는 줄 추가만 허용한다

- 상태: accepted
- 날짜: 2026-09-25
- 대체함: 없음
- 대체됨: 없음

## 배경
커밋에서 그 변경을 승인한 intent 로 가는 연결이 사람의 판독에만 있었다. 승인된 intent 는 고치지 않는다는 규칙(`dev-package/intent/README.md` 「개정 금지」)도 문서에만 있고 검사기가 없었다.
외부 하네스 `sungwooHa/ai-sdlc-harness` 는 같은 연결을 `Plan-Ref` 커밋 트레일러로 두고 경고로 시작했다. 우리 규칙은 「조용한 exit 0 은 판정도 준비 실패도 아니다」다(ADR-0005 2026-09-18 개정). 그래서 경고만 두는 선택은 이 규칙과 부딪친다.

## 결정
- PR 범위(`base..head`)가 코드·하네스 경로(`services/`·`frontend/src/`·`contracts/`·`db/`·`scripts/`·`gates/`·`.agents/`·`.claude/`·`.codex/`)를 바꾸면, 범위 안 커밋 중 적어도 하나는 `Intent-Ref: dev-package/intent/<파일>.md` 트레일러를 달아야 한다. 그 파일은 head 에 있어야 한다. 빈 커밋의 트레일러도 인정한다(트레일러 없는 기존 브랜치의 소급 경로).
- 기준 시점 또는 분기 시점에 승인 표기가 있는 intent 는 범위에서 줄 추가만 허용한다. 판정은 원본 바이트의 기존 줄이 새 내용에 순서대로 남는지로 한다.
- 위반은 `red(판정)` 이다. 게이트 `intent-ref` 가 판정하고, CI 는 `pull_request` 이벤트 중 대상 브랜치가 `product` 가 아닌 PR 에서 돌린다(`github.base_ref != 'product'` · product 대상 릴리스 PR 제외). 훅은 두지 않는다(ADR-0003).
- 승인 근거: intent `dev-package/intent/2026-09-25-external-harness-gap.md` 질문 4 ⓐ — Ted 원문 "권고댜로"(2026-09-25, 뜻 = 권고대로).

## 검토한 대안
- 경고 전용(외부 방식) + ADR-0005 예외 명기: 트레일러는 1줄이라 바로 고칠 수 있어 경고 단계의 이득이 작다. 예외를 두면 「조용한 통과 없음」 규칙에 구멍이 하나 생긴다. 배제.
- PreToolUse 훅으로 커밋 시점에 막기: 재신뢰가 필요하고 Codex 경로에 예외가 생긴다. ADR-0003(판정은 CLI·게이트) 과도 맞지 않는다. 배제.
- 승인 intent 전체 잠금(추가도 금지): 판정 기록을 덧붙이는 정상 흐름(「판정」·「확인」 절 추가)을 막는다. 배제.

## 결과와 감수한 비용
- 얻는 것: 커밋에서 승인 intent 로 기계 판독 연결이 생긴다. 승인된 intent 가 PR 안에서 조용히 고쳐지지 않는다.
- 부담: 트레일러가 없는 열린 PR·브랜치는 첫 실행에서 red 다. 빈 커밋 1개로 소급한다. 문서만 바꾼 PR 은 대상 밖(건수 출력).
- 알려진 비보호: 메타 줄이 없는 intent 5건, 그리고 메타에 `미승인` 문구가 남은 채 실제로는 승인된 intent 1건(`2026-09-08-harness-evals.md`)은 판별식상 보호되지 않는다. 정답표는 `gates/fixtures/intent-ref/intent-meta-classification.json` 에 둔다.
- 2026-09-26 추가 — 소형 PR B(intent `dev-package/intent/2026-09-25-harness-improvement.md` 10라운드 Q4 · 11라운드 우려 #3 ⓐ)로 승인 판별식을 바꿨다. 아래 재검토 조건 「메타 형식이 바뀌어 승인 판별식이 틀리기 시작할 때」에 해당하는 같은 결정의 개정이라 새 번호를 쓰지 않는다. 승인 = 첫 `메타` 줄의 `승인: @<GitHub handle> <YYYY-MM-DD> "<원문>"`(형식 검사만 · 네트워크·토큰 없음 · 승인 행위는 사람의 병합 · ADR-0003), 또는 동결 스냅샷 `scripts/harness/intent_legacy_approved.txt`(develop `2ed59e9a` 에서 `intent_ref.py --freeze-legacy` 로 1회 생성 · 64건)에 이름이 있는 legacy 표기(「승인」 ∧ ¬「미승인」). 스냅샷은 도입 뒤 불변이다(바꾼 범위는 base 와 바이트가 다르면 red). base · head 모두에 스냅샷이 없으면 준비 실패 78 이다. 알려진 비보호에 `2026-09-18-missing-rate-predicate-recon.md`(메타가 두 줄로 나뉘어 첫 메타 줄에 승인 표기가 없음)를 더한다. 새 정답표는 `scripts/tests/fixtures/intent-ref/intent-meta-classification-v2.json` 이고 위 v1 정답표는 이력으로 바꾸지 않는다.

## 재검토 조건
- 정상 PR 이 같은 이유로 red 가 되는 일이 반복될 때. 예를 들어 대상 경로가 너무 넓거나, 트레일러 소급이 잦을 때.
- intent 메타 형식이 바뀌어 승인 판별식이 틀리기 시작할 때.
- 리뷰 도구가 PR 본문의 intent 링크를 기계 검증하게 되어 트레일러가 중복될 때.

## 근거
- 판정기 `scripts/harness/intent_ref.py` · 게이트 `gates/run.sh` `intent-ref` · CI `.github/workflows/ci.yml` `intent-ref` 잡 · 시험 `scripts/tests/test_harness_record_gates.py` `IntentRefGateTests`.
- 검토: `dev-package/reports/harness/20260925-external-harness-gap/REVIEW.md`(반증 3회차).
- 외부 비교: `dev-package/reports/harness/20260925-external-harness-gap/G1-flow.md` a3·b2.
