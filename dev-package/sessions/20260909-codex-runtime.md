> 2026-09-09 최종 현재 상태: Codex 신규 전체 평가 **40/40 통과, 판정 실패 0·준비 실패 0**. 실제 CLI `0.153.4` / `gpt-6-astra`, 고유 작업 40개이며 snapshot `3d0d6c9f301b69ab259d35edd849d70300235e8e84e2b844a5bf02f0684265b6`의 2,307개 파일이 실행 전후 일치했다. 독립 최종 감사 승인 완료. 외부 증거는 `../.parity-20260909/evidence/codex-final-40-h15-h16-v2`와 `../.parity-20260909/evidence/codex-40-final-acceptance.json`이다.

# Codex 동등성 실행 환경 — 신규 실행

상태: 진행 중. CLI 결과를 데스크톱 결과로 대체하지 않는다.

## 현재 검증 상태 — 최종 Codex 40/40

- H15/H16의 동치 응답 오판과 최종 필드의 모순 응답 과잉 수용을 RED→GREEN으로 수정했다. 집중 회귀 12개, 전체 scripts 회귀 100통과·플랫폼 제외10, 하네스 자체검사15 통과 및 독립 최종 검토 승인을 확인했다. 실제 사전 실행은 4/4이며 최종 전체 평가에서 H08·H12는 각각 2/2다. 양쪽 러너의 준비 실패 분류·혼재 exit1 및 Codex snapshot 불일치 exit78 계약을 유지한다.
- H08 승인 범위 구현과 독립 검토를 완료했고 CSS 원본 바이트를 유지했다.
- 전체 parity 수용은 **미완료**다. Claude 신규 전체40회와 실제 개발 E2E는 주간 한도로 미확보이며 안내된 재개 시각은 **2026-09-11 03:00 KST**다. 한도 해제 성공과 데스크톱 앱 재시작 후 최신 코드 검증은 아직 확인하지 않았다.
- 제품 Core E2E 9개 통과는 이전 core 버전의 유효한 증거로 유지한다. 후속 수정은 평가기·하네스에 한정하며 제품 코드 변경이나 제품 E2E 신규 실행을 주장하지 않는다.
- 원본 상태 문서 변경은 동결 evaluation 사본에 반영하지 않는다. 상세 수용 현황은 `20260909-codex-parity-acceptance.md`를 따른다.

## 이전 전체 평가 이력

이전 `evidence/codex-final-40-h08-v2`의 **38/40**(snapshot `d3b816379668f0acde573d4b62ec39d3fe7ea0765c8af2a5a7eecdea55026f5d`)과 더 이전 `evidence/codex-final-40-env-restored`의 **38/40**(snapshot `118dfa504a2901669c978b9ab4252afd913d1724b30884878ec67c8f3ba29fdf`)은 각각의 원 결과·실패 분류를 보존한다. 신규 40/40은 별도 전체 실행이며 과거 결과를 소급 재분류하지 않는다.

H08 v2 전체 평가 전 실제 Astra H08 사전 실행2/2와 d3b8 snapshot 일치를 확인했다. 근거는 `../.parity-20260909/evidence/h08-v2-model-preflight-console.log`다. 아래 실행·회귀 수치와 실패는 해당 시점의 이력으로 유지한다.

## 기준 — 최초 실행 시점

- 원본 HEAD: `47cce303f0efb9d9bfa37d1f5a086030caea1ab6`, branch `main`.
- 기존 변경 205개 파일 SHA-256: `eval/harness/results/parity-baseline-20260909.json`.
- 구현 사본: 상위 `.parity-20260909/implementation`, branch `codex-parity-implementation`.
- 평가 러너 사본: 상위 `.parity-20260909/evaluation`, branch `codex-parity-evaluation`.
- 사본은 같은 HEAD의 로컬 clone에 기존 미커밋 파일을 복사했다. 새 커밋·push 없음.

## 실측

| 경로 | 실측 | 상태 |
|---|---|---|
| 현재 데스크톱 새 작업 | task `01a081a7-a433-7d11-abad-869af137f949`, cwd 상위 `00 CoLAB`, source vscode, originator codex_work_desktop, CLI 0.153.0-alpha.5, turn model gpt-6-astra | 저장소 지침 수동 로딩·명시 cwd 조회 성공. 프로젝트 자동 훅 미검증 |
| 프로젝트 CLI | `scripts/dev.ps1 codex --version` → 0.153.4 | 버전 확인 |
| 새 CLI 진입 | task `01a081aa-d8be-7723-ace0-26ada55e4055`, cwd 저장소, source exec, CLI 0.153.4, turn model gpt-6-astra | 실행 중 |
| WSL 도구 | Python 3.12.3, Claude Code 2.1.263, agent-browser 0.27.0 | 버전/존재 확인 |
| 연결 검사 | `scripts/dev.ps1 bridge check` → 12 skills / 4 roles / 9 hooks / 5 events | exit 0 |

모델 값은 로컬 세션 JSONL의 turn_context에서 읽었다. originator 문자열만으로 데스크톱/CLI를 구분하지 않고 source와 실행 경로를 함께 기록했다. hook event 타입이 해당 JSONL에 없다는 사실만으로 훅 미실행을 단정하지 않는다.

## 남은 환경 인수

앱 재시작과 전체 정상 작업 종료는 추가 실측이 필요하다. 저장소 데스크톱 진입·하위 디렉터리 새 사본 진입·실제 lane-worker 자동 H2는 아래 후속 증거로 확인했다.

## 후속 실측

- 새 데스크톱 task `01a081af-ce49-7343-8247-20f3610def70`: 저장소 루트 cwd, codex_work_desktop 0.153.0-alpha.5, gpt-6-astra. 사용자 지정 R-CODEX-PARITY 시작 안내·원본 skill 읽기 확인.
- 자동 H3 음성: 격리 local remote 대상 강제 push dry-run이 PreToolUse에서 exit 2 차단. raw 호출/출력은 `eval/harness/results/desktop-parity-negative-20260909.json` (rollout ordinal 78/80). 명령 본체 실행 전 차단이며 외부 remote 사용 없음.
- 개인 grill-me/to-spec 고정 절대경로 fallback을 현재 사본 Git 루트/부모 탐색으로 바꿈. 개인 backup `~/.codex/backups/parity-personal-skills-20260909`, 두 skill quick_validate 통과.
- 새 사본 frontend의 첫 CLI intent 실행은 Git/Get-Content가 blocked by policy라 준비 실패. 실제 루트 확인 실패를 성공으로 세지 않음. 테스트 사본 두 곳의 정확한 project trust 등록 후 같은 기본 경로로 재검증 중. 사용자 기존 project trust 승인 범위의 격리 사본이며 전역 권한·hook hash를 바꾸지 않음. config backup `~/.codex/backups/config-before-parity-copies-20260909.toml`.
- H09 새 task 의미 명확화 후 Codex 준비 실행 2/2 green, 실제 gpt-6-astra runtime context 확보. 최종 전체 평가가 아님.
- agent-browser 0.27.0 core --full 조회 exit 0, references 8개·templates 3개 원문 확보 및 hash 보존. 원본 옆 복구와 격리 시험 사본 전달 완료.

## Claude 외부 실행 의존

새 H09 준비 실행은 API 429로 실패했다. raw `../.parity-20260909/evidence/claude-h09-preflight/20260909-005145/H09.raw.1.json`의 result는 주간 한도 및 9월 11일 03:00 Asia/Seoul 재설정을 알린다. duration_api_ms=0, modelUsage={}, cost=0. 모델 신규 응답이 없어 40/40이나 T4 Claude 완주 증거로 인정할 수 없다. 한도가 풀리거나 사용자가 사용할 수 있는 정당한 실행 경로를 제공하기 전까지 이 의존 경로는 준비 실패로 유지하고, 독립 Codex·공통 회귀를 계속한다.

개인 intent 신뢰 후 재검증은 현재 evaluation 사본의 frontend에서 시작해 같은 사본 루트·grill-me/grilling·읽기전용 조사와 질문까지 exit 0. 증거: `../.parity-20260909/evidence/personal-entry-trusted`.

## 새 사본의 자동 준비와 훅 신뢰

native CLI 0.153.4 / gpt-6-astra에서 새 lane-worker의 실제 developer 메시지에 `hooks.additional_context` H2 결과가 기록됐다. 대상 `h2-runtime`, 신설 5·재사용 1·실패 0·146초. 네 Python 환경의 3.12.3/pytest import와 frontend tsc, 사본 경로 stamp를 별도로 확인했다. 원 코드 snapshot 변경 0건. 증거: `../.parity-20260909/h2-runtime-evidence/h2-actual-hook-context.json`, `result-trusted.json`.

이 실행의 H7는 보고서 부재로 exit 2 차단됐으므로 정상 종료 성공으로 세지 않는다. 최초 H2 미실행은 project trust만 있고 사본별 7개 훅 정의가 untrusted인 상태에서 발생했다. 원본 승인 해시 7/7 일치를 확인하고 정상 CLI review에서 신뢰한 뒤 재실행했다. implementation/evaluation/codex-e2e도 같은 정상 review로 연결했다. 증거: `../.parity-20260909/h2-runtime-evidence/other-clone-trust-after-ui.json`. 전역 권한·검사 비활성화 없음.

최신 adapter delta 이후 재호출한 별도 child `01a081d0-c8e5-7461-bbbc-4390d1b66bf3`에서도 H2 자동 context에 지정 사본·신설 0·재사용 6·실패 0·2초가 기록됐다. 증거: `../.parity-20260909/evidence/actual-patch-guards/h2-latest-context-candidates.json`. 최초 신규 설치 성공과 최신 코드 재사용 성공을 별도 실행으로 구분한다.

## H08 변경 전 보호·회귀 검증 이력

리셋 후 최신 cleanup 수정: dev.ps1 SHA256 `010775a9de96c5a3b9987e5aedc529c58248d2b3378897ba90f1acb15dfcccd7`. descendant가 남아도 임시 stdin 파일을 상속하지 않도록 읽고 닫은 뒤 pipe 전달한다. 실제 PS5 exit37/0 RED→GREEN, Windows bridge 27통과/7제외, WSL 전체 70통과/10제외. `../.parity-20260909/evidence/final-regression-cleanup.json` 및 `launcher-cleanup-final-review.md`가 아래 과거 회귀보다 최신이다.

최종 추가 수정 후 회귀는 Windows 48개 중 41통과/7제외, WSL 79개 중 70통과/9제외이며 양쪽 exit 0이다. `../.parity-20260909/evidence/final-regression-latest.json`에 현재 파일 해시와 결과를 기록했다. 아래 이전 회귀 수치는 해당 시점의 기록으로 유지한다. PowerShell 5 UTF-8 표준입력 수정은 기존 Windows Python을 사용하며 원래 BOM 유무와 큰 입력을 보존한다. 독립 재검토 `final-launcher-review-after-stdin.md`도 통과했다. JSONL은 줄바꿈 LF로 분리하여 문자열 내부 NEL/U+2028/U+2029를 잘못 분할하지 않는다.

당시 기록: stage5는 Codex 사용량 오류로 중단됐고, 그 시점에는 최종 40회와 앱 재시작을 검증하지 못했다. 현재 최신 상태는 이 문서 상단 요약과 `20260909-codex-parity-acceptance.md`를 따른다. 앱 재시작 후 최신 코드 검증은 현재도 미확인이다.

- 최신 desktop 새 turn: bridge check와 git status exit 0, 실제 local force dry-run PreToolUse exit 2. 앱 재시작이 아니다. 원 raw 및 해당 source hash: `eval/harness/results/desktop-parity-final-source-20260909.json`.
- 최신 native CLI 실제 patch 8시도: 허용 text/CSS 2성공, migration·decision·fix test 수정/삭제/이동·경계 밖 경로 6차단. 보호된 세 파일 hash 전후 동일, 이동 목적지/경계 밖 파일 미생성. CSS `hooks.additional_context`도 실제 기록됐다. 증거: `../.parity-20260909/evidence/actual-patch-guards/{result.json,actual-hook-events.json}`.
- 최신 회귀: WSL 전체 71발견 중 66실행 통과·Windows전용 5제외. Windows bridge 22실행 통과·WSL전용 7제외, runner 11/11·judge 3/3. 플랫폼 제외는 반대 플랫폼에서 통과했다. 과거 native 전체의 Linux전용 실패 기록은 보존하며 성공으로 재분류하지 않는다. 증거: `../.parity-20260909/evidence/final-regression/summary.json`.
- 최신 공통 종료 계약: Windows 실제 복수 gate 2통과/판정 0/준비 0 후 verify·handoff·양쪽 H7 payload exit 0. 직접 adapter 증거로만 인정한다. 증거: `../.parity-20260909/implementation/dev-package/reports/parity-20260909/final-lifecycle-runtime/README.md`.
