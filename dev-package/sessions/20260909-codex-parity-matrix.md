# Claude·Codex 동등성 전수 매트릭스

상태: Codex 신규 최종40/40 확인·독립 감사 승인. Claude·데스크톱 재시작 검증이 남아 전체 parity 수용은 미완료다.

## 현재 요약 — 최종 Codex 40/40

- 2026-09-09 최종 현재 상태: Codex 신규 전체 평가 **40/40 통과, 판정 실패 0·준비 실패 0**. 실제 CLI `0.153.4` / `gpt-6-astra`, 고유 작업 40개이며 snapshot `3d0d6c9f301b69ab259d35edd849d70300235e8e84e2b844a5bf02f0684265b6`의 2,307개 파일이 실행 전후 일치했다. 독립 최종 감사 승인 완료. 외부 증거는 `../.parity-20260909/evidence/codex-final-40-h15-h16-v2`와 `../.parity-20260909/evidence/codex-40-final-acceptance.json`이다.
- H15/H16의 동치 응답 오판과 최종 필드의 모순 응답 과잉 수용을 RED→GREEN으로 수정했다. 집중 회귀 12개, 전체 scripts 회귀 100통과·플랫폼 제외10, 하네스 자체검사15 통과 및 독립 최종 검토 승인을 확인했다. 실제 사전 실행은 4/4이며 최종 전체 평가에서 H08·H12는 각각 2/2다. 양쪽 러너의 준비 실패 분류·혼재 exit1 및 Codex snapshot 불일치 exit78 계약을 유지한다.
- H08 승인 전수 계약과 완전 목록 판정을 구현했다. CSS 바이트는 유지했고 정답 개수·좌표·선택자 누출이 없다.
- 전체 parity 수용은 **미완료**다. Claude 신규 전체40회와 실제 개발 E2E는 주간 한도로 미확보이며 안내된 재개 시각은 **2026-09-11 03:00 KST**다. 한도 해제 성공과 데스크톱 앱 재시작 후 최신 코드 검증은 아직 확인하지 않았다.
- 제품 Core E2E 9개 통과는 이전 core 버전의 유효한 증거로 유지한다. 후속 수정은 평가기·하네스에 한정하며 제품 코드 변경이나 제품 E2E 신규 실행을 주장하지 않는다.
- 이전 `evidence/codex-final-40-h08-v2`의 **38/40**(snapshot `d3b816379668f0acde573d4b62ec39d3fe7ea0765c8af2a5a7eecdea55026f5d`)과 더 이전 `evidence/codex-final-40-env-restored`의 **38/40**(snapshot `118dfa504a2901669c978b9ab4252afd913d1724b30884878ec67c8f3ba29fdf`)은 각각의 원 결과·실패 분류를 보존한다. 신규 40/40은 별도 전체 실행이며 과거 결과를 소급 재분류하지 않는다.
- 상세와 근거는 `20260909-codex-parity-acceptance.md`를 따른다. 아래 과거 실행·회귀 기록은 당시 증거이며 Claude 모델 실행으로 세지 않는다.

| ID | 원본 | 입력 → 기대 산출물 / 경계 | Claude 증거 | Codex 증거 | 상태 |
|---|---|---|---|---|---|
| S01 | `.claude/skills/agent-browser/SKILL.md` | URL·행동 → 입력·저장·재조회·거절 증거 | 신규 모델 미실행 | stage4 browser 12/12·관련 시각 게이트 | 부분 증거 확보·전체 동일성 미완료 |
| S02 | `.claude/skills/apple-design/SKILL.md` | 화면 → 피드백·추적·중단·reduced-motion 검증 | 신규 모델 미실행 | stage4 디자인 판정·실화면 계측 | 부분 증거 확보·전체 동일성 미완료 |
| S03 | `.claude/skills/colab-v2-work/SKILL.md` | 실행 → 실물·지정 계획·검증·인계 / 무근거 완료 금지 | 신규 모델 미실행 | stage1~4 절차·인계, stage5 재개·stage6 완료 | 부분 증거 확보·전체 동일성 미완료 |
| S04 | `.claude/skills/design-review/SKILL.md` | audit·승인 fix → 판정표·실화면·게이트 | 신규 모델 미실행 | stage4 정적 audit·frontend-visual | 부분 증거 확보·전체 동일성 미완료 |
| S05 | `.claude/skills/executing-plans/SKILL.md` | 계획 → 격리 구현·상태 갱신·전체 검증 | 신규 모델 미실행 | stage4 계획→구현→인계 | 부분 증거 확보·전체 동일성 미완료 |
| S06 | `.claude/skills/grill-me/SKILL.md` | 명시 인터뷰 → 미승인 intent / 승인 전 spec·구현 금지 | 신규 모델 미실행 | stage1~2 질문·미승인 intent | 부분 증거 확보·전체 동일성 미완료 |
| S07 | `.claude/skills/grilling/SKILL.md` | 결정 질문 → 사실 조사와 사용자 결정 분리 | 신규 모델 미실행 | stage1 named researcher·질문 | 부분 증거 확보·전체 동일성 미완료 |
| S08 | `.claude/skills/receiving-code-review/SKILL.md` | 리뷰 → 근거 확인·수정·재검증 | 신규 모델 미실행 | stage4 리뷰 수용, fresh 재검증 stage5 재개·stage6 완료 | 부분 증거 확보·전체 동일성 미완료 |
| S09 | `.claude/skills/test-driven-development/SKILL.md` | 행동 요구 → 실제 RED·구현·GREEN | 신규 모델 미실행 | stage4 행동 RED20/4→GREEN24/24 | 부분 증거 확보·전체 동일성 미완료 |
| S10 | `.claude/skills/to-spec/SKILL.md` | 승인 intent → spec / 미승인 입력 차단 | 신규 모델 미실행 | stage3 시험 승인 spec | 부분 증거 확보·전체 동일성 미완료 |
| S11 | `.claude/skills/verification-before-completion/SKILL.md` | 완료 주장 → 새 증거·intent 미달/초과 | 신규 모델 미실행 | stage4 현재 hash·인계, stage5 재개·stage6 완료 | 부분 증거 확보·전체 동일성 미완료 |
| S12 | `.claude/skills/writing-plans/SKILL.md` | spec → spec 링크와 300행 이내 실행 계획 | 신규 모델 미실행 | stage4 실행 계획·상태 갱신 | 부분 증거 확보·전체 동일성 미완료 |
| A01 | `.claude/agents/advisor.md` | 역할 입력 → 정의된 산출물·권한 경계 | 신규 모델 미실행 | stage4 named advisor; fresh stage5·stage6 완료 | 부분 증거 확보·전체 동일성 미완료 |
| A02 | `.claude/agents/gate-runner.md` | 역할 입력 → 정의된 산출물·권한 경계 | 신규 모델 미실행 | stage4 미호출; stage5 새 runner 및 stage6 관련9개·인계 완료 | 부분 증거 확보·전체 동일성 미완료 |
| A03 | `.claude/agents/lane-worker.md` | 역할 입력 → 정의된 산출물·권한 경계 | 신규 모델 미실행 | actual-normal-stops named lane 정상완료·2/0/0 | 부분 증거 확보·전체 동일성 미완료 |
| A04 | `.claude/agents/researcher.md` | 역할 입력 → 정의된 산출물·권한 경계 | 신규 모델 미실행 | actual-normal-stops named researcher 정상완료 | 부분 증거 확보·전체 동일성 미완료 |
| K01 | `.claude/hooks/bootstrap-diet.sh` | 이벤트 → 정상 허용과 금지 차단 쌍 | 신규 모델 미실행 | desktop 지정 round·CLI 원본 조회 | 부분 증거 확보·전체 동일성 미완료 |
| K02 | `.claude/hooks/css-edit-audit.sh` | 이벤트 → 정상 허용과 금지 차단 쌍 | 신규 모델 미실행 | 공통 원본/회귀와 actual 짝검증 별도 대조 | 행별 actual 최종 인수 전 |
| K03 | `.claude/hooks/decision-number-guard.sh` | 이벤트 → 정상 허용과 금지 차단 쌍 | 신규 모델 미실행 | 공통 원본/회귀와 actual 짝검증 별도 대조 | 행별 actual 최종 인수 전 |
| K04 | `.claude/hooks/git-guard.sh` | 이벤트 → 정상 허용과 금지 차단 쌍 | 신규 모델 미실행 | desktop force 및 CLI worker main 실제 자동차단 | 부분 증거 확보·전체 동일성 미완료 |
| K05 | `.claude/hooks/lane-gate-summary.sh` | 이벤트 → 정상 허용과 금지 차단 쌍 | 신규 모델 미실행 | 공통 회귀·실제 lane 인계검증; auto H7 성공 context 미노출 | 부분 증거 확보·전체 동일성 미완료 |
| K06 | `.claude/hooks/migration-guard.sh` | 이벤트 → 정상 허용과 금지 차단 쌍 | 신규 모델 미실행 | 공통 원본/회귀와 actual 짝검증 별도 대조 | 행별 actual 최종 인수 전 |
| K07 | `.claude/hooks/test-file-guard.sh` | 이벤트 → 정상 허용과 금지 차단 쌍 | 신규 모델 미실행 | 공통 원본/회귀와 actual 짝검증 별도 대조 | 행별 actual 최종 인수 전 |
| K08 | `.claude/hooks/uncommitted-artifacts.sh` | 이벤트 → 정상 허용과 금지 차단 쌍 | 신규 모델 미실행 | 공통 회귀·실제 researcher 완료; auto H6 성공 context 미노출 | 부분 증거 확보·전체 동일성 미완료 |
| K09 | `.claude/hooks/worktree-setup.sh` | 이벤트 → 정상 허용과 금지 차단 쌍 | 신규 모델 미실행 | CLI child 자동 H2 context·신설5/실패0 | 부분 증거 확보·전체 동일성 미완료 |
| R01 | `.claude/rules/colab-rules.md` | 적용 경로 → 공통 정책 준수 | 신규 모델 미실행 | 공통 원본/회귀와 actual 짝검증 별도 대조 | 행별 actual 최종 인수 전 |
| R02 | `.claude/rules/deploy.md` | 적용 경로 → 공통 정책 준수 | 신규 모델 미실행 | 공통 원본/회귀와 actual 짝검증 별도 대조 | 행별 actual 최종 인수 전 |
| R03 | `.claude/rules/s3-upload.md` | 적용 경로 → 공통 정책 준수 | 신규 모델 미실행 | 공통 원본/회귀와 actual 짝검증 별도 대조 | 행별 actual 최종 인수 전 |

## 진입·의존·결함

- E01 /intent, E02 $intent, E03 자연어 intent: UI 호출 지원과 실제 원본 수행을 구분한다.
- 개인 intent → 옆 grill-me → 프로젝트 연결. 개인 grill-me/to-spec의 고정 checkout fallback을 수정했고, evaluation/frontend에서 같은 사본 루트 탐색과 실제 인터뷰 진입을 확인했다(`evidence/personal-entry-trusted`).
- agent-browser references 8개(commands, snapshot-refs, authentication, trust-boundaries, session-management, profiling, video-recording, proxy-support)와 templates 3개를 CLI core 전체 조회로 원본 옆에 복원했다. 실제 소비 범위는 개발 흐름 증거에서 별도로 판정한다.
- TDD writing-good-tests.md, intent/spec TEMPLATE, design-review css_audit.py/live_audit.sh/live_probe.js는 실존한다.
- graphify 미설치. 지식그래프가 필요한 사례는 실제 대체 산출물로 검증하며 이름만으로 지원이라 하지 않는다. eli5/explain-visually는 쉬운 설명·자립 HTML로 실제 검증한다.
- H1 지정 round 우선, H6 작업별 시작 hash·선언 산출물·인계 검증으로 수정했다. 무관한 기존 미추적 파일은 종료 차단 근거가 아니며 자동 커밋을 요구하지 않는다.
- H7는 선언한 작업 보고서·실제 파일 hash·필수 gate·run identity를 검증한다. 깨진 JSON·준비 실패·옛 보고서·중간 코드 변경은 통과하지 않는다. 최신 lifecycle 회귀 18개를 양쪽 payload 계약으로 검증했다.
- H09는 문제 유무 판정이라는 의미만 공통 task에서 명확화하고 expect 강도를 보존했다. Codex 신규 준비 평가 2/2는 전체 평가와 구분한다.
- design-review 시험 작성 RED → 승인된 보호 fix 단계 구분을 공통 원본에 반영했다.

## 확보한 부분 실행 증거 — H08 변경 전 이력

아래 경로는 원본 저장소의 형제 `.parity-20260909`를 기준으로 한다. 실제 자동 호출과 명시적 adapter 호출을 섞지 않는다.

| 행 | 실행 증거 | 확인 범위 / 남은 범위 |
|---|---|---|
| S06·S07, E02 | `evidence/personal-entry-trusted`, `evidence/codex-e2e-stage1` | 개인 intent 원본 탐색·질문·승인 전 코드 변경 0. 전체 사이클 진행 중 |
| S01 | sessions의 e2e 문서 | stage4 실제 browser 12/12·거절 보존·재조회 지속성 확인. stage5 최신-source 인수 중단 |
| K01·K04 | 원본 `eval/harness/results/desktop-parity-negative-20260909.json` | 새 desktop의 지정 round·강제 push dry-run 자동차단. 최신 코드 재시작 재현은 별도 |
| K09·A03 | `h2-runtime-evidence/h2-actual-hook-context.json`, `result-trusted.json` | CLI child 실제 자동 신규 환경 준비 5·재사용 1·실패 0. H7 정상 종료 아님 |
| K03·K05·K06·K07·K08 | `evidence/final-regression/summary.json` | 최신 공통/adapter 회귀, WSL 66 실행 통과와 Windows 전용 5 통과. 실제 모델 짝검증은 별도 |
| T5 러너 | `evidence/final-regression/summary.json` | runner 11·judge 3 통과. 최종 모델 40/40 미실행 |

## 게이트 정본

`gates/run.sh` ALL_GATES의 각 등록명이 공통 실행 계약이다. 관련 게이트 실행은 T6, 모델 행동은 T5, 브라우저 동작은 T4에서 별도 판정한다. 전수 게이트 실행은 이번 제품 배포 인수를 대신하지 않는다.

## 수용 기준 연결

| spec 기준 | 실행 단계 | 상태 |
|---|---|---|
| 1 원본·참조·명령 전수 | T1 + 각 신규 실행 | 목록 확보 / 실행 미검증 |
| 2 데스크톱·CLI 진입 | T2·T6 | 진행 중 |
| 3 전체 상태 전이 | T4 | Codex stage4 완주·stage5 재개·stage6 인계 확보, Claude 미실행 |
| 4 정상/음성 | T3 | 구현 중 |
| 5 공통 원본 회귀 | T3·T6 | 100통과·플랫폼 제외10, H15/H16 집중12, 자체검사15 통과 |
| 6 동일 snapshot 신규 40/40씩 | T5 | Codex 신규40/40·판정0·준비0, Claude 전체40·한도 해제 미확인 |
| 7 실제 개발·브라우저 | T4 | Codex stage4 DOM24/24·browser12/12, 이전 core 버전 Core E2E9 통과, Claude 미실행 |
| 8 재시작·필수 실패 0 | T6 | 미검증 |

근거: 원본 12 skills / 4 roles / 9 shell hooks / 3 rules 실존 대조, bridge check exit 0. 기준 hash와 환경: `20260909-codex-runtime.md`.

## 개별 게이트 대응

| ID | 공통 gate 이름 | 원본 실행 | Claude 증거 | Codex 증거 | 상태 |
|---|---|---|---|---|---|
| G01 | `planning-freshness` | `gates/run.sh planning-freshness` | 모델 신규 미실행 | 공통 WSL related-gates 최종7개 묶음 exit0 | 관련·공통 실행통과/양쪽 모델 증거 아님 |
| G02 | `contract-lint` | `gates/run.sh contract-lint` | 모델 신규 미실행 | actual-normal-stops named lane 2/0/0 | 제품변경 비관련·H7 실제 정상경로 smoke 수행 |
| G03 | `contract-breaking` | `gates/run.sh contract-breaking` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G04 | `event-lint` | `gates/run.sh event-lint` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G05 | `event-breaking` | `gates/run.sh event-breaking` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G06 | `seam-consistency` | `gates/run.sh seam-consistency` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G07 | `generated-up-to-date` | `gates/run.sh generated-up-to-date` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G08 | `import-boundary` | `gates/run.sh import-boundary` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G09 | `banned-import` | `gates/run.sh banned-import` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G10 | `ai-no-lineage-write` | `gates/run.sh ai-no-lineage-write` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G11 | `db-boundary` | `gates/run.sh db-boundary` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G12 | `migration-single-head` | `gates/run.sh migration-single-head` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G13 | `schema-diff` | `gates/run.sh schema-diff` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G14 | `migration-drift` | `gates/run.sh migration-drift` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G15 | `rls-coverage` | `gates/run.sh rls-coverage` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G16 | `rls-effect` | `gates/run.sh rls-effect` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G17 | `work-item-consistency` | `gates/run.sh work-item-consistency` | 모델 신규 미실행 | 공통 WSL related-gates 최종7개 묶음 exit0 | 관련·공통 실행통과/양쪽 모델 증거 아님 |
| G18 | `stage2-markers` | `gates/run.sh stage2-markers` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G19 | `autometa-loss` | `gates/run.sh autometa-loss` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G20 | `frontend-typecheck` | `gates/run.sh frontend-typecheck` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G21 | `frontend-test` | `gates/run.sh frontend-test` | 모델 신규 미실행 | Codex stage4 fixture 최종2/0/0 | 관련·stage4 통과/최신 stage5 usage 중단 |
| G22 | `frontend-fixture-reach` | `gates/run.sh frontend-fixture-reach` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G23 | `frontend-visual` | `gates/run.sh frontend-visual` | 모델 신규 미실행 | Codex stage4 fixture 최종2/0/0 | 관련·stage4 통과/최신 stage5 usage 중단 |
| G24 | `preview-tile-slot` | `gates/run.sh preview-tile-slot` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G25 | `artifact-ownership` | `gates/run.sh artifact-ownership` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G26 | `e2e-format-coverage` | `gates/run.sh e2e-format-coverage` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G27 | `render-latency` | `gates/run.sh render-latency` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G28 | `backup-cron-streak` | `gates/run.sh backup-cron-streak` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G29 | `exec-bit` | `gates/run.sh exec-bit` | 모델 신규 미실행 | 공통 WSL related-gates 최종7개 묶음 exit0 | 관련·공통 실행통과/양쪽 모델 증거 아님 |
| G30 | `harness-eval` | `gates/run.sh harness-eval` | weekly429 준비실패·해제 미확인 | Codex 신규 최종40/40·판정0·준비0 | Codex 확인·Claude 미확보로 필수 미완료 |
| G31 | `service-tests-core-api` | `gates/run.sh service-tests-core-api` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G32 | `service-tests-ai-service` | `gates/run.sh service-tests-ai-service` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G33 | `service-tests-viz-render` | `gates/run.sh service-tests-viz-render` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G34 | `service-tests-pipeline-worker` | `gates/run.sh service-tests-pipeline-worker` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G35 | `contract-selftest` | `gates/run.sh contract-selftest` | 모델 신규 미실행 | actual-normal-stops named lane 2/0/0 | 제품변경 비관련·H7 실제 정상경로 smoke 수행 |
| G36 | `event-selftest` | `gates/run.sh event-selftest` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G37 | `boundary-selftest` | `gates/run.sh boundary-selftest` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G38 | `db-boundary-selftest` | `gates/run.sh db-boundary-selftest` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G39 | `db-selftest` | `gates/run.sh db-selftest` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G40 | `rls-effect-selftest` | `gates/run.sh rls-effect-selftest` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G41 | `seam-consistency-selftest` | `gates/run.sh seam-consistency-selftest` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G42 | `generated-selftest` | `gates/run.sh generated-selftest` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G43 | `work-item-selftest` | `gates/run.sh work-item-selftest` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G44 | `stage2-markers-selftest` | `gates/run.sh stage2-markers-selftest` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G45 | `autometa-loss-selftest` | `gates/run.sh autometa-loss-selftest` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G46 | `preview-tile-slot-selftest` | `gates/run.sh preview-tile-slot-selftest` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G47 | `artifact-ownership-selftest` | `gates/run.sh artifact-ownership-selftest` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G48 | `e2e-format-coverage-selftest` | `gates/run.sh e2e-format-coverage-selftest` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G49 | `render-latency-selftest` | `gates/run.sh render-latency-selftest` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G50 | `backup-cron-streak-selftest` | `gates/run.sh backup-cron-streak-selftest` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G51 | `exec-bit-selftest` | `gates/run.sh exec-bit-selftest` | 모델 신규 미실행 | 공통 WSL related-gates 최종7개 묶음 exit0 | 관련·공통 실행통과/양쪽 모델 증거 아님 |
| G52 | `migration-drift-selftest` | `gates/run.sh migration-drift-selftest` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G53 | `frontend-typecheck-selftest` | `gates/run.sh frontend-typecheck-selftest` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G54 | `frontend-test-selftest` | `gates/run.sh frontend-test-selftest` | 모델 신규 미실행 | 공통 WSL related-gates 최종7개 묶음 exit0 | 관련·공통 실행통과/양쪽 모델 증거 아님 |
| G55 | `frontend-fixture-reach-selftest` | `gates/run.sh frontend-fixture-reach-selftest` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |
| G56 | `frontend-visual-selftest` | `gates/run.sh frontend-visual-selftest` | 모델 신규 미실행 | 공통 WSL related-gates 최종7개 묶음 exit0 | 관련·공통 실행통과/양쪽 모델 증거 아님 |
| G57 | `harness-eval-selftest` | `gates/run.sh harness-eval-selftest` | 모델 신규 미실행 | 공통 WSL related-gates 최종7개 묶음 exit0 | 관련·공통 실행통과/양쪽 모델 증거 아님 |
| G58 | `service-tests-selftest` | `gates/run.sh service-tests-selftest` | 모델 신규 미실행 | 공통 원본 경로 확인·실행 안 함 | 이번 하네스 diff 비관련(gate-scope-review)·통과 아님 |

## H08 변경 전 인수 기록 — 2026-09-09 문서 대조

- Codex stage4는 계획·행동 RED 20실패/4통과 → DOM GREEN 24/24 → browser 12/12 → 최종 frontend-test/frontend-visual 2/0/0 → 인계까지 exit 0이다. 모델 로그의 Unicode 줄구분자 파서 오류는 원문 hash를 보존한 별도 재추출 증거이며 모델 재실행이 아니다.
- stage5 최신-source 재검증은 Codex usage limit로 error/turn.failed, result exit 1이다. 일부 advisor/시각/인계 파일이 있어도 단계 완료로 세지 않는다. 근거 `evidence/codex-e2e-stage5-final-source/result.json` 및 events.jsonl. 새 advisor·named gate-runner의 최종 인수는 중단 상태로 유지한다.
- Claude 신규 모델은 weekly API 429로 준비 실패, 안내된 재설정은 2026-09-11 03:00 Asia/Seoul. 양쪽 최종 H01~H20 각2회 40/40은 미실행이다. 과거 응답·Codex 결과·공통 단위검사로 대체하지 않는다.
- desktop 저장소 진입과 실제 H3 자동차단은 확인됐지만 데스크톱 앱 재시작 후 재현은 미확인이다. CLI H2 성공을 desktop H2로 옮겨 적지 않는다.
- 실제 named researcher/lane 정상 task_complete 및 직접 verify/handoff 성공 증거는 `evidence/actual-normal-stops/README.md`에 있다. 성공 자동 H6/H7 context는 노출되지 않았으므로 정상 완료만으로 성공 hook 실행을 독립 입증했다고 주장하지 않는다. H2는 별도로 실제 자동 context를 확보했다.

## 게이트 상태 판독과 범위 — 당시 실행 이력

G58행의 범위 근거는 `evidence/gate-scope-review.md`다. 관련 10개 중 공통 WSL 검증 7개는 `evidence/related-gates/final-gate-summary.json`과 `summary.json`의 마지막 단일 묶음 7/0/0·exit0을 인용한다. 앞선 5/1/1 및 6/1/0 실패 기록은 보존하며 합산하지 않는다. 해당 실행은 evaluation 사본과 당시 snapshot 근거이며 현재 양쪽 모델 최종 통과가 아니다. 당시 native planning env 전송 누락 메모는 당시 기록으로 보존하고 이후 launcher 수정·회귀와 구분한다.

나머지 관련 3개는 fixture frontend-test/frontend-visual(stage4 통과, stage5 최종-source 인수 중단)과 실제 모델 harness-eval(필수 미실행)이다. contract-lint/contract-selftest는 제품변경상 비관련이지만 named lane 정상 인계의 실제 smoke에서 2/0/0으로 수행돼 별도 표시했다. 비관련 게이트는 원본 실행 경로·범위만 확인했으며 실행통과나 면제 green으로 세지 않는다. 다른 사용자의 제품변경 관련 검증 책임을 이 분류로 지우지 않는다.

필수 미검증0은 관련 실행 집합과 실제 역할·스킬·정상/음성 인수에 적용한다. 현 상태는 여전히 미충족이다. graphify 대체·자립 HTML도 파일 존재만으로 실제 요구 전체를 검증했다고 세지 않는다. stage5 재개·stage6 완료 상태와 최종 평가/재시작 미확인을 유지한다.
## 09:35 KST 후속 인수 — 변경 전 이력

새 모델 40회는 38/40 통과, 준비 실패 0이다. H08 과제 계약은 미해결이며, H12 동의어 판정 수정 이후 전체 재실행이 필요하다. 자동 H7 음성 4종은 모두 실제 차단됐다. 최신 정상 lane은 2/0/0 및 verify/handoff 0을 확인했지만 성공 자동 훅 context 미노출 한계는 유지한다. stage6 관련 9개는 9/0/0, 부모 인계 0, 보고서 43개 해시 일치다. Claude 및 재시작 공백은 남아 있다. 최신 상세는 acceptance 문서를 따른다.
