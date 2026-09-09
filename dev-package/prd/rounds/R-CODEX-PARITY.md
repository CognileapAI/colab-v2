> spec: dev-package/prd/specs/dual-agent-development.md
# Claude·Codex 동작 동등성 구현·검증 계획

> 2026-09-09 최종 현재 상태: Codex 신규 전체 평가 **40/40 통과, 판정 실패 0·준비 실패 0**. 실제 CLI `0.153.4` / `gpt-6-astra`, 고유 작업 40개이며 snapshot `3d0d6c9f301b69ab259d35edd849d70300235e8e84e2b844a5bf02f0684265b6`의 2,307개 파일이 실행 전후 일치했다. 독립 최종 감사 승인 완료. 저장소 compact 증거는 `eval/harness/results/codex-40-final-acceptance-20260909.json`, 외부 증거는 `../.parity-20260909/evidence/codex-final-40-h15-h16-v2`와 `../.parity-20260909/evidence/codex-40-final-acceptance.json`이다.

> 2026-09-09 후속 승인 구현 완료: H08의 고정 7곳을 세 CSS의 숫자 px font-size 리터럴 전수 범위로 재정의했다. 소수를 포함한 13px 미만 선언의 전체 위치 집합을 검사하며 주석·비리터럴 값과 공유 선택자의 집계 단위를 명시했다. CSS 원본은 바이트 그대로이고 모델 입력에 정답 개수·좌표·선택자를 주입하지 않았다. 독립 최종 검토의 차단 사항은 없다. 과거 38/40은 수정 전 이력으로 보존하며 소급 재분류하지 않는다.

> H15/H16의 동치 응답 오판과 최종 필드의 모순 응답 과잉 수용을 RED→GREEN으로 수정했다. 집중 회귀 12개, 전체 scripts 회귀 100통과·플랫폼 제외10, 하네스 자체검사15 통과 및 독립 최종 검토 승인을 확인했다. 실제 사전 실행은 4/4이며 최종 전체 평가에서 H08·H12는 각각 2/2다. 양쪽 러너의 준비 실패 분류·혼재 exit1 및 Codex snapshot 불일치 exit78 계약을 유지한다. 전체 parity 수용은 **미완료**다. Claude 신규 전체40회와 실제 개발 E2E는 주간 한도로 미확보이며 안내된 재개 시각은 **2026-09-11 03:00 KST**다. 한도 해제 성공과 데스크톱 앱 재시작 후 최신 코드 검증은 아직 확인하지 않았다.

> **For agentic workers:** 이 세션에서 순차 실행한다. 같은 checkout의 쓰기 주체는 하나다.
> 구현 단계에는 executing-plans를 적용한다. 독립 검토를 위임해도 최종 증거 인수는 부모가 한다.

**Goal:** 사용자의 Codex에서 기존 Claude 하네스의 정상 개발 흐름과 보호 동작을 재현하고 끝까지 검증한다.
**Architecture:** 공통 정책·판정은 원본 하나로 유지한다. Codex 어댑터는 실행 환경·이벤트·도구 차이를 처리한다.
단위 검사, 실제 런타임 검사, 양쪽 동일 과제 비교, 전체 작업 흐름을 별도 증거로 남긴다.
**Tech Stack:** Codex desktop/CLI, Claude Code, PowerShell, WSL, Python, Bash, agent-browser.
**Spec:** `dev-package/prd/specs/dual-agent-development.md`의 2026-09-09 필수 인수 기준.

## 현재 상태와 완료 기준

**T1 목록 확보 / T2 진입·자동 준비 확인 / T3·T5 구현 통합 / T4 Codex 시험 인계 확보·Claude 미검증 / T5 Codex 신규40/40 확인·Claude 미확보 / 전체 인수 미완료.** Claude 신규 실행은 주간 사용량 제한으로 준비 실패다. 앞선 「이제 실행된다」 보고는 전체 완료 근거가 아니다.
기존 증거는 `dev-package/sessions/20260908-harness-audit.md`에 보존한다. 아래 표는 계획 수립 당시의 증거·공백 대조 이력이며 현재 상태는 위 요약과 acceptance 문서를 따른다.

이전 `evidence/codex-final-40-h08-v2`의 **38/40**(snapshot `d3b816379668f0acde573d4b62ec39d3fe7ea0765c8af2a5a7eecdea55026f5d`)과 더 이전 `evidence/codex-final-40-env-restored`의 **38/40**(snapshot `118dfa504a2901669c978b9ab4252afd913d1724b30884878ec67c8f3ba29fdf`)은 각각의 원 결과·실패 분류를 보존한다. 신규 40/40은 별도 전체 실행이며 과거 결과를 소급 재분류하지 않는다.

제품 Core E2E 9개 통과는 이전 core 버전의 증거로 유지한다. 이번 평가기·하네스 수정에는 제품 코드 변경이 없으며 제품 E2E 신규 실행을 주장하지 않는다.

| 확보한 증거 | 아직 증명하지 못한 것 |
|---|---|
| 12개 스킬 discovery, 4개 역할 호출 | 스킬 본문 실행·리소스 접근·역할별 정상 작업 완주 |
| CLI 훅 신뢰 및 일부 자동 이벤트 | 사용자 데스크톱의 동일 활성 상태, 모든 정상/음성 경로 |
| H6/H7 종료 차단 | 무관한 파일 오차단 제거, 올바른 산출물로 정상 종료 |
| H2 수정 후 payload 재실행 성공 | 수정 후 새 에이전트·새 작업 사본 자동 준비 |
| 과거 응답 재판정 39/40 | 같은 최종 버전에서 양쪽 모델 신규 40/40 |
| 단일 contract-lint 성공 | 계획→구현→리뷰→관련 게이트→인계 연속 완주 |

완료 조건: 아래 T1~T6 모두 통과, 필수 동등성 목록 미검증 0, 각 모델 eval 40/40,
정상 시나리오 오차단 0, 음성 시나리오 누락 0, 재시작·새 사본 재현 성공.
이는 정해진 계약·검사 범위의 동등성 검증이다. 모델의 모든 미래 응답이 같음을 주장하지 않는다.

## Global Constraints

- 제품 규칙·승인 경계·검증 강도를 보존한다. 통과를 위해 fixture 정답이나 특정 과제 답을 지침에 주입하지 않는다.
- 기존 trust 승인은 유지한다. 지원되는 명령별 승인 경로를 사용하며 전역 우회·훅 비활성화를 해결책으로 쓰지 않는다.
- 다른 작업의 미커밋 변경은 보존한다. 구현·음성 검사는 지정 격리 사본/임시 fixture에서 실행한다.
- 사용자 승인 없는 산출물을 자동 커밋하지 않는다. 인계 증거는 작업별로 묶고 다른 레인의 파일을 재사용하지 않는다.
- 제품 배포·운영 데이터 변경·과거 저장소 보관은 기존 R-DUAL-AGENT의 별도 범위로 유지한다.
- 실패 시 관련 결함을 수정하고 그 검사를 다시 수행한다. 최종 인수는 수정 완료 후 새 전체 실행 한 묶음이다.
- 단계마다 변경 파일·실행 명령·결과·남은 결함을 이 계획과 증거 기록에 갱신한다.

## T1. 전수 목록과 공통 계약 고정

**Files:** 조사 `.claude/**`, `.agents/**`, `.codex/**`, `AGENTS.md`, `CLAUDE.md`,
`scripts/dev.ps1`, `scripts/agent-bridge.py`, `eval/harness/**`, 개인 intent/grill-me/to-spec.
생성 `dev-package/sessions/20260909-codex-parity-matrix.md`.
**Interface:** 각 행은 ID / 원본 / 사용자 입력 / 기대 산출물 / 허용·차단 / Claude 증거 / Codex 증거 / 상태.

- [x] Git 상태와 변경 파일 hash를 기록하고 현재 실제 실행 파일·버전·모델·설정 출처를 확보한다.
- [x] 등록 항목뿐 아니라 본문의 Skill/Agent/도구 호출·상대경로·references/templates까지 추적한다.
- [x] `/intent`·`$intent`·자연어 진입을 각각 검사할 사례로 등록한다. UI가 지원하는 호출 방식과 결과를 구분한다.
- [x] browser references/templates, graphify, 시각 설명 등 누락된 의존의 실제 소비처와 필요한 산출물을 기록한다.
- [x] 원래 의도와 기존 버그를 구분한다. H6 오차단·H7 증거 선택/유효성·H09 판정 의미를 공통 계약에 명시한다.
- [ ] 수용 기준 1~8마다 T1~T6과 증거 행을 연결하고 누락 0을 확인한다.

**검증:** `scripts/dev.ps1 bridge check`; 목록 수와 참조 파일 실존을 대조한다.
**인수:** 모든 원본에 대응 행이 있고 기대 결과가 판정 가능하다. 발견만 된 항목은 미검증으로 남긴다.

## T2. 사용자의 Codex 진입과 실행 환경 완성

**Files:** 수정 `.agents/skills/**`, `.codex/config.toml`, `scripts/dev.ps1`,
`scripts/agent-bridge.py`, `docs/development/dual-agent.md`; 개인 스킬 연결은 필요 부분만 수정.
검사 `scripts/tests/test_agent_bridge.py`; 증거 `dev-package/sessions/20260909-codex-runtime.md`.
**Interface:** T1의 입력을 받아 저장소 루트·실제 스킬 원본·실행 도구·종료코드가 일관된 진입 경로를 제공한다.

- [ ] 데스크톱 새 작업과 프로젝트 CLI를 각각 검사한다. 상위 workspace·루트·하위 폴더 시작을 포함한다.
- [ ] 스킬 발견 후 실제 본문과 중첩 리소스를 읽는지 확인한다. 개인 고정 절대경로가 다른 사본을 가리키는 사례를 재현한다.
- [ ] 재현 실패를 회귀검사로 고정하고 경로 탐색·WSL 도구 선택·LF 전달을 수정한다.
- [ ] 샌드박스 거절→지원되는 승인→정확한 명령 실행→결과 회수까지 사용자 실행 경로로 검증한다.
- [x] 새 격리 사본에서 H2가 자동 호출돼 의존을 준비하는지 확인한다. 준비 실패를 성공으로 표시하지 않는다.
- [ ] 데스크톱 재시작 후 같은 검사를 반복하고 CLI 결과와 별도 기록한다.

**검증:** native bridge tests, WSL bridge tests, 실제 환경 이벤트.
회귀는 최소한 `actual_root == assigned_checkout`, 반환코드 0/1/78 보존,
공백 포함 경로와 기존 환경 제어 변수 보존을 검사한다.
**인수:** 기본 사용자 경로로 실행 가능하며 테스트 전용 app-server 조작 없이는 쓸 수 없는 상태가 아니다.

## T3. 훅·역할의 정상 완료와 금지 동작을 쌍으로 구현

**Files:** 수정 `scripts/agent-bridge.py`, `.codex/hooks.json`, `.codex/agents/*.toml`;
공통 정책 결함은 해당 `.claude/hooks/*.sh`와 `.claude/agents/*.md`를 함께 수정.
검사 `scripts/tests/test_agent_bridge.py`; 생성 `scripts/tests/test_harness_lifecycle_contract.py`.
**Interface:** T1 계약의 작업 식별자·사본·산출물·검증 범위를 입력으로 받아 allowed/blocked와 원인·증거를 출력한다.

- [ ] 아래 정상/음성 사례를 실패 재현 테스트로 먼저 고정한다.
- [x] H6는 이 작업의 미추적 산출물과 기존 무관한 파일을 구분하도록 공통 계약과 구현을 정합화한다.
- [x] H7는 명시된 작업의 보고서만 소비하고, 없는/깨진/오래된/준비 실패 증거가 완료로 통과하지 않게 한다.
- [x] 미승인 초안 반환→부모 기록→승인 대기의 정상 흐름을 확인한다. 임의 커밋으로 종료하지 않는다.
- [ ] lane-worker의 사본·branch·HEAD, advisor 무수정, gate-runner 명령 범위와 결과 인계를 실제 작업으로 검증한다.
- [ ] 직접 adapter 테스트 뒤 같은 사례를 실제 모델 도구 호출로 반복한다. 수정한 hook 정의의 활성 상태도 재확인한다.

| 대상 | 정상 | 음성 |
|---|---|---|
| H1/H2 | 지정 라운드·지정 사본 준비 | 다른 라운드/사본, 필수 도구 부재 |
| Git guard | 안전 조회·허용된 작업 | worker main push·강제 push 시도 |
| patch guard | 허용 파일 변경 | migration·decision·fix 테스트 보호 위반, 삭제/이동 경로 우회 |
| CSS audit | 실제 CSS 편집 후 결과 전달 | 편집하지 않은 파일을 검사 완료라고 인용 |
| researcher/H6 | 무관한 기존 파일이 있어도 읽기 전용 종료 | 이 작업 산출물 누락·인계 없이 종료 |
| lane-worker/H7 | 현재 작업의 실제 정상 게이트 결과 | 다른 작업/옛 트리/깨진 JSON/준비 실패/미실행 |

**검증:** 새로운 테스트에서 정상 반환을 assert하고 음성은 예외/차단 및 실제 부작용 부재를 assert한다.
강제 push는 `--dry-run`과 격리된 로컬 remote만 사용한다. 보호 파일 검사는 fixture의 전후 hash로 검증한다.
**인수:** 모든 쌍이 양쪽 하네스에서 계약대로 동작하며 정상 종료를 수동 중단으로 대신하지 않는다.

## T4. 스킬과 개발 흐름의 실제 완주

**Files:** 필요한 `.agents/skills/**`, 공통 원본 `.claude/skills/**`, `docs/development/dual-agent.md` 수정.
생성 `dev-package/sessions/20260909-codex-parity-e2e.md`.
**Interface:** 고정된 시험 요구사항·승인 응답을 받아 intent/spec/계획/변경/리뷰/검증/인계 증거를 만든다.

- [x] 격리 fixture의 작은 입력 검증 기능을 시험 과제로 고정한다. 입력·정상 결과·잘못된 입력 거절을 사전에 적는다.
- [ ] intent로 시작해 질문·조사·초안 반환·사용자 확인·to-spec·계획 생성까지 실행한다.
- [ ] 시험 승인 응답은 fixture 시나리오임을 표시한다. 실제 사용자 승인과 혼동하거나 제품 승인 기록으로 옮기지 않는다.
- [ ] 계획에 따라 테스트 실패→구현→테스트 통과→advisor 리뷰→수정→gate-runner→인계를 완주한다.
- [ ] 나머지 스킬도 최소 한 실제 사용 사례를 T1 행에 연결한다. 이름 보고만 하는 사례는 제외한다.
- [ ] browser/design 스킬은 격리 로컬 화면에서 입력·저장·재조회·거절 동작과 시각 결과를 검사한다.
- [ ] 빠진 참조는 원본 리소스를 확보하거나 동등한 경로를 구현한다. 필수 기능이 없으면 미완료로 유지한다.
- [ ] Claude에도 같은 fixture와 승인 응답을 제공해 산출물·상태 전이·검증 결과를 비교한다.

**인수:** 정상 사이클 양쪽 완주, 미승인 상태 구현 차단, 사용자에게 돌아오는 산출물·증거가 공통 계약에 부합한다.

## T5. 평가 러너와 최종 동일 조건 비교

**Files:** 수정 `scripts/codex-harness-eval.py`, `scripts/tests/test_codex_harness_eval.py`,
`scripts/tests/test_harness_judge_compat.py`; 필요 시 양쪽에 공통인 `eval/harness/H*/task.md`·`expect.sh`.
**Interface:** 코드/fixture/판정부 hash, 실제 모델·CLI, 20과제×2회, 출력 디렉터리 → 원 로그와 최종 summary.

- [x] H09에서 「문제 있음」과 「층 구분 없음」의 혼동을 재현해 과제·판정부 의미를 대조한다.
- [ ] 실제 행동 결함은 실행 지침을 수정한다. 과제 자체가 모호하면 의미를 명확히 하고 양쪽 동일 적용한다.
- [x] 러너에 실제 모델 식별 증거와 입력/판정부/변경 파일 hash, 중간 결과 보존을 추가한다.
- [x] timeout·오류·완료 누락·틀린 판정이 green으로 바뀌지 않는 회귀검사를 실행한다.
- [x] 승인된 H08 전수 계약과 완전 목록 판정을 구현하고 CSS 원본 보존·정답 누출 제거·독립 최종 검토를 확인한다.
- [x] 양쪽 러너의 준비 실패 분류·혼재 exit1, Codex snapshot 불일치 exit78을 RED→GREEN으로 검증한다.
- [x] H08 실제 Astra 사전 실행2/2 및 snapshot `d3b816379668f0acde573d4b62ec39d3fe7ea0765c8af2a5a7eecdea55026f5d` 일치를 확인한다.
- [x] H15/H16 판정 수정·집중12개/전체100통과·제외10·독립 승인 및 실제 사전4/4를 확인한다.
- [x] 최종 Codex 전체40/40·판정0·준비0·고유 작업40개·전후2,307개 파일 일치를 별도 새 실행에서 확인한다.
- [ ] 모든 코드 수정 후 같은 스냅샷에서 Claude와 Codex 전체 20과제를 각각 2회 새로 실행한다.
  Codex는 `evidence/codex-final-40-h15-h16-v2`에서 40/40을 완료했다. Claude 신규 전체 실행은 아직 확보하지 못했다.
- [ ] 양쪽 40/40·준비 실패 0·미실행 0을 확인한다. 중간 실패 기록도 보존하고 마지막 성공만 골라 합치지 않는다.

Codex 실행 인터페이스는 기존 runner를 유지한다:
```powershell
python scripts/codex-harness-eval.py --codex $resolvedCodexExe --timeout 120 `
  --only H01 --only H02 --only H03 --only H04 --only H05 --only H06 --only H07 `
  --only H08 --only H09 --only H10 --only H11 --only H12 --only H13 --only H14 `
  --only H15 --only H16 --only H17 --only H18 --only H19 --only H20 `
  --output eval/harness/results/codex-parity-final
```
`$resolvedCodexExe`는 T2에서 실제 버전을 확인한 경로다. 출력 디렉터리는 새 경로여야 한다.
Claude는 `eval/harness/run.sh`의 실제 help/옵션을 읽고 같은 과제·반복 수를 설정한 정확한 명령을 기록한다.
**인수:** 결과가 다른 항목 0. 평가의 성공을 T4 개발 흐름 성공으로 대신하지 않는다.

## T6. 재현·회귀·최종 인수

**Files:** `.github/workflows/agent-bridge.yml`, `docs/development/dual-agent.md`,
`dev-package/sessions/20260909-codex-parity-acceptance.md`, 이 계획의 상태 갱신.
**Interface:** T1 목록 + T2~T5 원 증거 → 필수 항목별 pass/fail/미실행 및 최종 결론.

- [x] bridge check, Windows/WSL 회귀, 기존 Claude runner selftest를 실행한다.
- [ ] 변경 범위의 관련 게이트와 브라우저 검사를 실행한다. 동일 체크아웃에서 전수 두 벌을 동시에 돌리지 않는다.
- [ ] 데스크톱 재시작·새 CLI·새 격리 사본에서 intent 진입과 작은 작업 정상 종료를 재현한다.
- [ ] 최종 변경 뒤 T5 결과가 유효한지 hash로 확인한다. 영향 있는 수정이 있으면 전체 최종 평가를 다시 실행한다.
- [ ] 수용 기준 1~8·T1 행별 증거를 대조해 실패·준비 실패·미실행·필수 미지원 0을 검사한다.
- [ ] 실제 사용 명령과 산출물 위치를 문서화하고 남은 구현 결함 없이 최종 보고한다.

## 실행 순서와 중단 규칙

T1 → T2 → T3 → T4 → T5 → T6. 본 계획 작성 다음 작업은 T1이다.
보호 장치 차단은 기대한 음성 사례에서만 성공이다. 정상 작업 차단은 해결할 결함이다.
외부 입력이 필수로 없으면 정확한 의존만 명시하고 독립 작업을 계속한다.
필수 인수 실패가 하나라도 남으면 「동등성 구현 진행 중」으로 유지한다.
계획 수립을 요청받은 이번 응답에서는 실행 설계와 문서를 확정하며 구현 완료를 주장하지 않는다.

## 신규 실행 기록 — 2026-09-09

T1 원본 12 skills·4 roles·9 shell hooks·3 rules와 중첩 의존 조사 완료. 매트릭스: `dev-package/sessions/20260909-codex-parity-matrix.md`. baseline 205개 파일 hash 보존. `bridge check` exit 0.

T2 프로젝트 CLI 신규 진입은 실제 grill-me/grilling 원본 조회·미승인 경계 보고 exit 0. 현재 데스크톱 작업은 상위 폴더 프로젝트로 시작했으므로 저장소 자동 훅 성공으로 인정하지 않는다. 사용자가 실제 저장소 프로젝트를 추가하는 입력 대기와 독립인 구현은 계속한다. 환경 상세: `dev-package/sessions/20260909-codex-runtime.md`.

T3 공통 lifecycle 회귀·수정과 T5 러너 증거 보존 수정은 서로 다른 격리 사본에서 준비 중이다. 최종 신규 평가는 모든 변경 통합 후 실행한다.

후속: 사용자 등록 프로젝트의 새 데스크톱 작업에서 원본 스킬 진입·자동 Git 차단을 확인했다. 새 사본 자동 H2도 실제 child hook context와 독립 환경 검사로 확인했다. 공통 lifecycle 26파일 및 reviewer delta 7파일, 러너 3파일을 baseline hash 대조 후 통합했다. 자세한 증거는 runtime 문서와 외부 `.parity-20260909` 기록에 보존한다. Codex 격리 fixture의 단계별 정상 흐름 실행 중이며, Claude 신규 모델 실행은 주간 한도(9월 11일 03:00 재설정)로 대기한다.
