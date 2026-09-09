# Claude와 Codex 공통 작업 연결

## 계획 중심 실행

이번 전환의 전체 실행 계획은 `dev-package/prd/rounds/R-DUAL-AGENT.md`다.
여러 단계의 요청은 목표·완료 조건·의존·승인 대기·검증 기준을 먼저 기록한다.
부분 작업이 끝나면 계획을 갱신하고 다음 실행 가능한 단계로 진행한다.
진행 보고와 최종 완료를 구분하며, 개별 오류 해결을 전체 작업의 종료 사유로 삼지 않는다.
승인이나 환경이 막는 것은 해당 의존 경로뿐이다. 독립 작업은 계속한다.
전체 완료는 계획의 수용 기준을 모두 확인했거나 사용자가 범위를 명시적으로 변경한 경우에만 선언한다.

## 원본과 도구별 연결

이번 변경은 기존 Claude 실행 설정을 유지하면서 Codex 진입점을 추가한다.
공통 원본을 새 폴더로 전부 이동하지 않는다. 기존 경로를 유지해야 스크립트·상대 링크가 끊기지 않는다.

| 대상 | 편집할 원본 | Codex 연결 |
|---|---|---|
| 제품 규칙 | `CLAUDE.md`, `.claude/rules/colab-rules.md` | `AGENTS.md`에서 필요한 절만 참조 |
| 작업 절차 | `.claude/skills/colab-v2-work/SKILL.md` | `.agents/skills/colab-v2-work/SKILL.md` |
| 브라우저 CLI | `.claude/skills/agent-browser/SKILL.md`와 그 옆 리소스 | `.agents/skills/agent-browser/SKILL.md` |
| 구현·조사·검토·게이트 역할 | `.claude/agents/*.md` 본문 | `.codex/agents/*.toml`에서 원본을 읽고 도구 차이 적용 |
| 검사 로직 | `.claude/hooks/*.sh`, `gates/` | `scripts/agent-bridge.py`와 기존 게이트 명령 |

`.agents`와 `.codex` 파일은 연결과 환경 차이만 담는다. 공통 본문 수정은 원본에서 한 번만 한다.
기존 12개 스킬 모두 `.agents/skills/<이름>/SKILL.md`로 등록한다.
`grill-me`와 `to-spec`의 명시 호출 정책은 원본 `agents/openai.yaml`에서 유지한다.
Codex에서는 `$grill-me`, `$to-spec`로 호출한다. 개인 `$intent`는 grill-me의 별칭이다.
각 스킬을 읽으면 **그 원본 디렉터리**를 기준으로 상대 링크·스크립트 경로를 해석한다.
`docs/`, `dev-package/`, `.claude/`, `.agents/`, `scripts/`, `gates/`로 시작하는 저장소 경로는
현재 셸의 하위 폴더가 아니라 Git 루트 기준이다. 원본 옆 `references/` 등의 링크만 원본 디렉터리 기준이다.
Claude의 도구 allowlist·maxTurns·모델 이름은 Codex 설정으로 해석하지 않는다.

## 도구 차이

### 전수검사에서 확인한 추가 대응

- `Skill(name)`은 그 원본 SKILL.md를 직접 읽어 수행한다. `TodoWrite`와 계획 도구는
  현재 사용 가능한 계획 도구 또는 지정 라운드 파일의 체크리스트로 대응한다.
- `lane-worker`의 Claude frontmatter 스킬 4개는 Codex 역할 본문에서 단계별로 읽는다.
- 조사자가 미승인 intent를 작성해야 하면 초안 내용을 부모에게 반환하고 **부모 한 명이 기록**한다.
  H6를 만족시키기 위한 에이전트 커밋을 Ted 승인으로 보지 않는다. H6 자체를 끄거나 성공으로 위장하지 않는다.
  작업 시작·종료 기록은 `docs/development/lifecycle-evidence.md`를 따른다. H6는 해당 작업의 산출물과 실제 인계를 검증한다.
- 디자인 조사도 같은 사본에서는 읽기 전용 결과를 부모에게 반환한다. 파일 작성이 필요한
  병렬 레인은 사본을 분리한다. 테스트 작성이 필요한 fix는 승인된 시험 작성 단계에서 RED를 확인한 뒤
  `COLAB_FIX_LANE=1`의 구현 단계로 진행한다. 보호된 fix 단계에서 테스트 수정 우회 값을 켜지 않는다.
- agent-browser의 `references/` 8개와 `templates/` 3개는 원본 스킬 옆에 복원했다.
  확보 경로와 출처는 `.claude/skills/VENDORED.md`에 기록하며, 상대 링크는 원본 디렉터리에서 해석한다.
- `/eli5`, `explain-visually`는 쉬운 설명과 현재 사용 가능한 시각화 도구로 목적을 수행한다.
  `/graphify`는 현재 설치된 기능이 아니므로 그래프 생성 완료를 주장하지 않는다.
- deploy_doctor 검사 수 등 오래된 숫자는 실행 시 정본과 실측으로 확인한다. 게이트 병렬도는
  현재 `.claude/rules/colab-rules.md`의 후속 운영 규칙과 실제 자원을 따른다.

### 자동 훅 등록 상태

`.codex/hooks.json`은 기존 9개 셸 훅의 5개 이벤트를 `scripts/agent-bridge.py codex-event`로 연결한다.
Windows 명령은 현재 Git 루트에서 Python 진입점을 찾고 WSL에 JSON stdin을 그대로 전달한다.
Linux도 Git 루트에서 같은 진입점을 실행한다. 하위 폴더에서 시작해도 상대 경로가 어긋나지 않는다.
PreToolUse의 patch 전체 경로(삭제·이동 목적지 포함)를 검사하고, PostToolUse CSS 출력은
additionalContext JSON으로, SubagentStop 성공 출력은 systemMessage JSON으로 변환한다.
실행 오류는 차단으로 전달한다. H2는 환경 준비이며 격리 사본 생성이나 성공 보장이 아니다.
프로젝트 trust와 `/hooks`의 정의별 review가 필요하다. 이 PC에서는 2026-09-09 확인 시
7개 등록 항목 모두 enabled/trusted이며 SessionStart 실행과 PreToolUse 차단을 실측했다.
다른 PC·새 훅 정의·다른 절대경로의 작업 사본에는 이 신뢰가 자동 이전되지 않는다.
새 사본에서는 프로젝트 신뢰와 별도로 7개 정의를 검토한다. 기존 승인 정의와 해시가 같아도
정상 CLI review가 필요하다. wrapper 내부 변경은 정의 해시만으로 검출되지 않으므로 코드 snapshot도 비교한다.
공식 이벤트 계약: https://learn.chatgpt.com/docs/hooks

- Claude `Read/Grep/Glob/Edit/Write/Bash`는 현재 Codex 세션의 파일·검색·패치·셸 도구에 대응한다.
  존재하지 않는 도구명이나 플러그인 호출을 그대로 시도하지 않는다.
- Claude `Agent(isolation: worktree)`와 자동 H2 준비는 Codex에서 발생한다고 가정하지 않는다.
  Codex 앱의 worktree 기능 또는 명시적으로 준비한 격리 사본을 사용하고 HEAD·경로를 확인한다.
  별도 사본이 없으면 쓰기 에이전트를 병렬 실행하지 않는다.
- 역할 파일의 쓰기 제한은 Codex 정책과 함께 적용한다. advisor는 read-only sandbox로 등록한다.
  researcher의 특정 폴더 제한과 gate-runner의 코드 무수정은 지침이며 OS 접근 제어는 아니다.
- Codex 사용자 정의 에이전트는 `.codex/agents/*.toml`에서 발견된다. 현재 세션에 후보가 없다면
  같은 역할 파일을 직접 읽어 수행하거나 프로젝트를 새 세션으로 연다. 자동 등록을 주장하지 않는다.
  2026-09-08 `config/read` 실측으로 이 Git 저장소의 프로젝트 신뢰 등록이 빠져 `.codex` 레이어가
  비활성화된 것을 확인했다. 상위 폴더의 신뢰만으로는 이 저장소 설정이 로드되지 않았다.
  프로젝트 신뢰 변경은 사용자 승인 후 이 저장소 경로에만 적용하고, 권한·sandbox는 별도로 유지한다.
- `.codex/agents/*.toml`에 `model`이 지정된 역할은 그 값을 부모보다 우선한다.
  실행·지원 역할인 `lane-worker`와 `researcher`는 `gpt-5.6-sol`, 검증·검토 역할인
  `gate-runner`와 `advisor`는 `gpt-6-astra`를 사용한다. 모델을 지정하지 않은 다른 역할만
  부모 설정을 상속한다. Claude 모델 별칭을 Codex 설정으로 복사하지 않는다.
- 공통 문서에 있는 옛 단계·모델·도구 규약이 실제 실행 환경과 다르면 이 연결 규칙으로 도구 차이만
  해결한다. 제품 결정의 충돌은 실물·대장·승인 기록을 대조하고 임의로 재정의하지 않는다.

## 검사 실행 — 기존 WSL 환경

게이트 종료코드는 성공 `0`, 판정 실패 `1`, 환경·입력 부재 등 준비 실패 `78`이다.
준비 실패는 건너뛴 성공이나 일반 판정 실패로 바꾸지 않는다. 실제 반환 코드와 상태를 함께 보고한다.

Windows 프로젝트 실행 진입점은 `scripts/dev.ps1`이다. 실행 파일 선택과 cwd를 여기서 처리한다.

```powershell
.\scripts\dev.ps1 codex --version
.\scripts\dev.ps1 codex
.\scripts\dev.ps1 browser --version
.\scripts\dev.ps1 browser doctor
.\scripts\dev.ps1 bridge check
.\scripts\dev.ps1 gate frontend-test
```

Codex는 사용자 npm 설치와 앱 번들을 탐색해 확인된 Astra 대응 버전인 0.153.0 이상 중
가장 높은 버전을 선택한다(동일 버전이면 정식판 우선). 업데이트로 경로가 바뀌어도 다시 찾는다.
사용자 설정·인증·승인 정책은 그대로 읽으며, `--ignore-user-config`나 권한 우회 플래그를 넣지 않는다.
브라우저와 게이트는 WSL에서 실행하고 해당 자식 프로세스의 PATH에 기존 npm bin을 추가한다.
PowerShell에서 snapshot ref는 `scripts/dev.ps1 browser click '@e2'`처럼 따옴표로 감싼다. `@e2`를 그대로 쓰면 splatting으로 해석되어 인자가 사라질 수 있다.
전역 PATH, PowerShell 프로필, WSL 프로필은 변경하지 않는다.

아래 명령은 저장소 루트에서 실행한다. Windows에서는 WSL에 들어가 해당 저장소로 이동한다.
Python 3.11 이상과 bash가 필요하다. 진단 명령은 설치·서버 기동·환경값 출력 없이 존재만 확인한다.

2026-09-08 실측: agent-browser 0.27.0은 WSL의 `$HOME/.npm-global/bin`에 이미 설치되어 있다.
비대화형 셸에서 PATH에 없으므로 `scripts/dev.ps1`가 프로세스 PATH를 구성한다.
WSL에서 직접 실행할 때도 `python3 scripts/agent-bridge.py run-tool browser -- <인자>` 또는
`run-tool gate -- <게이트>`를 사용하면 수동 export가 필요 없다.
이 PATH로 `agent-browser doctor`는 9 pass / 0 warn / 0 fail이며 headless Chrome 기동까지 확인했다.

```bash
python3 scripts/agent-bridge.py doctor
python3 scripts/agent-bridge.py check
python3 scripts/agent-bridge.py guard-command --command 'git status --short'
python3 scripts/agent-bridge.py guard-edit --path frontend/src/example.tsx
COLAB_GATE_REPORT_DIR=dev-package/reports/<회차>/<레인> bash gates/run.sh <게이트>
python3 scripts/agent-bridge.py verify-report --report dev-package/reports/<회차>/<레인>/gate-summary.json --gate <게이트>
```

`guard-command`는 명령을 **실행하지 않고 검사**한다. 성공한 뒤 같은 cwd에서 검사한 명령을 실행한다.
서브에이전트는 `--worker`를 추가한다. `guard-edit`는 편집 **전** 대상 파일마다 호출한다.
완료 보고 전에 현재 변경의 관련 게이트를 실행한다. 종료 훅의 최신 파일 탐색을 흉내 내지 않고
보고서 경로와 필요한 게이트를 명시한다. `docs/development/lifecycle-evidence.md`의 작업별 기록과
`verify-report --task <task_id>`는 미커밋 파일의 실제 hash를 검증한다. 작업 기록 없는 기존 경로는
clean checkout을 요구한다. 검사 때문에 사용자 승인 없는 커밋을 하지 않는다.

명시적 검사 호출 자체는 모든 명령·편집을 가로채지 않는다. 자동 적용 범위는 위의 등록된
Codex 이벤트·matcher다. 원격 브랜치 보호도 별도이며 이 변경이 설정하지 않는다.
H2 환경 준비는 작업 사본 격리를 대신하지 않는다. H6/H7과 별도로 완료 증거를 검증한다.
CSS 수정 후에는 기존 design-review 절차의 정적 검사·frontend-visual을 수행한다.

## 로컬 평가와 E2E

Windows 프로젝트 설정은 로그인 셸을 끄고 unelevated 샌드박스 백엔드를 선택한다.
이는 파일·네트워크 권한이나 승인 정책을 확장하지 않는다. Windows 샌드박스가 WSL 서비스에
접근하지 못해 도움말 또는 E_ACCESSDENIED를 반환하면 준비 실패로 기록한다. 사용자가 승인한
게이트는 지원되는 도구에서 **그 명령만** 샌드박스 밖 실행 승인을 요청한다. 전역 우회는 하지 않는다.
승인이 불가능한 세션에서는 해당 명령을 실행할 수 있는 호스트에서 실행하고 증거를 구분한다.

`eval/harness/run.sh`는 기존 Claude 평가 러너다. 그대로 유지하며 Astra 통과 근거로 쓰지 않는다.
Codex 연결 확인은 `scripts/agent-bridge.py check`와 별도의 로컬 Codex 읽기 전용 smoke로 수행한다.
smoke는 등록·원본 탐색 확인일 뿐 기존 20과제의 Astra 행동 평가나 제품 E2E 통과가 아니다.
CI의 기존 Claude eval 정책은 이번 변경에서 바꾸지 않는다. 별도 API 키 발급은 필요하지 않다.
새 `.github/workflows/agent-bridge.yml`은 관련 PR에서 연결 검사와 guard 음성 테스트만 실행한다.
모델·API 키·브라우저 서버가 필요 없으며 실제 Astra 행동 평가를 대체하지 않는다.

agent-browser 사용자 여정 테스트는 실행 전 다음을 고정한다:
테스트 URL·격리 계정/데이터·시나리오·기대 결과·정리 범위·대상 SHA.
실제 클릭·입력·파일 업로드 후 저장·조회·새로고침 지속성을 확인하고 단계별 증거를 남긴다.
화면 snapshot ref는 화면 변화 뒤 다시 얻는다. 스크린샷만으로 성공을 판정하지 않는다.
기존 `frontend-visual`은 읽기 전용 시각 검사이므로 쓰기 E2E로 바꾸지 않는다.
실행 환경·로그인·필수 도구가 없으면 미실행/준비 실패를 기록한다. 운영 데이터로 대체하지 않는다.

## 자동 훅 전환 조사 — 2026-09-08

공식 근거: https://learn.chatgpt.com/docs/hooks

Codex 프로젝트 훅 위치는 `.codex/hooks.json` 또는 `.codex/config.toml`의 hooks다.
프로젝트 trust와 **훅 정의별 hash trust**가 모두 필요하다. trust 우회 플래그는 사용하지 않는다.
아래 대응은 구현되어 있다. 실측 범위와 남은 제한은 `dev-package/sessions/20260908-harness-audit.md`에 기록한다.

| 기존 검사 | Codex 대응 | 필요한 변환·검증 |
|---|---|---|
| H1 시작 안내 | SessionStart | 실제 활성 라운드 선택, 모델에 전달되는 additionalContext 확인 |
| H2 worktree 준비 | SubagentStart | Codex 격리 경로/시점 확인 후 호출. Claude 자동 격리를 가정하지 않음 |
| H3 git guard | PreToolUse / Bash | command 재사용, 서브에이전트 식별 정보 존재 여부 확인 |
| H4 migration, H5 decision, test-file guard | PreToolUse / apply_patch | patch에서 **모든** 추가·수정·삭제·이동 경로를 추출해 file_path별 검사 |
| CSS 계측 | PostToolUse / apply_patch | 실제 변경 파일을 추출해 공통 판정부 연결. 사후 이벤트는 변경을 되돌리지 못함 |
| H6 조사 산출물 | SubagentStop | agent_type·산출물 경로·추적 상태가 현재 역할에 대응하는지 확인 |
| H7 게이트 결과 | SubagentStop | 보고서 경로·필수 gate·tree를 명시하고 판정 불가를 성공으로 처리하지 않음 |

중요한 입력 차이: Codex에서 matcher를 `Edit|Write`로 써도 실제 `tool_name`은 `apply_patch`이고,
입력은 `tool_input.command`의 patch다. 기존 Claude `tool_input.file_path`와 같지 않으므로
기존 스크립트를 그대로 등록하면 파일 검사를 조용히 건너뛸 수 있다.
Codex에서 Bash는 exec_command도 포함하지만 후속 write_stdin마다 PreToolUse가 다시 실행되지는 않는다.
이 도구 범위의 한계를 전체 셸·파일 접근의 강제 보장으로 확대해 보고하지 않는다.

## 작업공간 보관 후보

상위 작업공간의 `00 CoLAB-PoC`, `01 CoLAB-Plan`, `10 CoLAB-Launch`는 과거 작업 보관 후보다.
아직 이동·삭제하지 않았다. 각 저장소의 미커밋·미병합 변경, worktree 등록, 런타임 경로 참조를
확인한 뒤 `_archive`로 이동한다. `01 CoLAB-Plan`은 design-review 참고 경로가 남아 있으므로
미사용으로 단정하지 않는다. `03 Reference-Data`와 `40 COLAB-기획`은 현재 참조를 유지한다.
`99 temp`는 백업·리뷰 사본을 개별 판정한다. `locked`/`prunable` worktree는 폴더 이름만 보고 지우지 않는다.

## 검증 근거

- Codex 지침: https://learn.chatgpt.com/docs/agent-configuration/agents-md
- Codex 스킬: https://learn.chatgpt.com/docs/build-skills
- Codex 에이전트: https://learn.chatgpt.com/docs/agent-configuration/subagents
- 현재 Windows 기본 CLI: `codex-cli 0.153.4`(2026-09-08 npm 업데이트 완료, 이전 0.125.0).
  WSL의 실행 파일·인증·PATH는 별도 확인 대상이다.
