# Claude/Codex 연결 적용 기록 — 2026-09-08

## 요청과 범위

사용자 요청: 기존 Claude 구조의 공통 절차·검사 로직을 재사용하되 Codex에 맞게 연결하고 검증한다.
과거 작업 폴더는 보관 후보로 분류한다. 실제 이동·삭제는 하지 않는다.

## 적용

- `AGENTS.md` 진입점, `.agents/skills/` 연결 2종, `.codex/agents/` 역할 4종 추가.
- 본문 원본은 기존 `.claude`에 유지. Claude 지침에 연결 문서 링크만 추가.
- `scripts/agent-bridge.py`는 기존 settings의 PreToolUse 등록을 읽어 명시적으로 검사한다.
  대상 명령·편집은 실행하지 않는다. 자동 훅 등록이나 접근 제어를 보장하지 않는다.
- 명시한 보고서의 schema·필수 계수·게이트 목록·HEAD tree·깨끗한 checkout 확인 추가.
- `agent-bridge.yml`은 모델 호출 없이 위 연결과 음성 테스트를 검사한다. 원격 실행은 미검증.
- 제품 코드, 기존 Claude 훅/에이전트/스킬 본문, 기존 eval 러너, 전역 Codex 설치는 무변경.

## 검증 실측

| 검사 | 결과 |
|---|---|
| Windows Python 3.14.4 원본 링크·역할 TOML·스킬 metadata·훅 등록 경로 | 통과 |
| WSL 동일 연결 검사 | 통과 |
| WSL unittest 8개(보고서 판정 4, 기존 훅 연결 4) | 8/8 통과 |
| 보고서 음성 사례 | 부재·잘못된 형식·옛 tree·불일치 계수·중복·준비 실패·다른 게이트 거절 |
| 실제 기존 훅 호출 | 안전한 조회 허용, worker main push 거절, fix 테스트 편집 거절 |
| guard 부작용 | 테스트의 push·편집 명령 미실행 |
| PATH의 Codex 0.125.0에서 Astra smoke | 서버가 새 Codex 버전 필요로 거절 |
| 앱 번들 Codex 0.153.0-alpha.5에서 Astra smoke | 모델 응답 수신, 연결 스킬 2종 available 확인 |
| smoke의 파일 읽기 | 자동 실행 정책의 blocked by policy 거절. 원본 실존은 부모 검사에서 확인 |
| 사용자 정의 에이전트 실등록·스폰 | 미검증. smoke는 4종 available을 확인하지 못함 |
| agent-browser 실행 | 점검한 Windows/WSL PATH에서 미발견. 브라우저 E2E 미실행 |

smoke 프로세스 exit 0은 **전체 호환성 통과가 아니다**. 모델이 보고한 파일 읽기 차단과
에이전트 availability 미확인을 함께 판정한다. Claude 20과제 결과도 Astra 평가로 재사용하지 않았다.

## 다음 사용 시 확인

1. Codex 앱에서 이 저장소를 프로젝트 루트로 새 작업을 시작한다.
2. `AGENTS.md`와 두 연결 스킬이 로드되는지 확인한다.
3. 역할 4종의 실제 discovery를 확인한다. 후보에 없으면 역할 원본을 직접 읽어 수행하며
   자동 등록됐다고 주장하지 않는다. 런타임 버전·프로젝트 신뢰 설정은 사용자 환경에서 확인한다.
4. 제품 E2E를 수행할 셸에 agent-browser와 테스트 환경을 준비하고 선언된 시나리오를 실행한다.
5. 자동 훅 강제가 필요하면 현재 Codex 훅의 지원 이벤트·신뢰 정책을 별도 확인한 뒤 연결한다.

커밋·push·폴더 이동은 수행하지 않았다.

## 후속 확인 — 브라우저 실행 경로

처음의 agent-browser 미발견은 비대화형 WSL PATH 문제였다. 추가 검색으로
`$HOME/.npm-global/bin/agent-browser` 설치를 확인했다. 같은 셸에서 해당 bin을 PATH에
추가한 뒤 CLI 0.27.0 및 `doctor` 9 pass / 0 warn / 0 fail을 확인했다.
Chrome for Testing 152.0.7977.82의 headless about:blank 기동도 통과했다.
기존 design 세션은 종료·조작하지 않았다. 이는 실행 환경 확인이며 제품 사용자 여정 E2E는 아니다.

## 실행 경로 고정

사용자 요청에 따라 `scripts/dev.ps1`을 프로젝트 실행 진입점으로 추가했다.
Codex는 앱 번들의 0.153.0 이상을 탐색하고, browser/gate/bridge는 저장소 루트의 WSL에서
실행한다. WSL 자식 프로세스에 기존 npm bin PATH를 설정하며 전역 프로필·권한은 변경하지 않는다.

- `dev.ps1 codex --version`: 0.153.0-alpha.5 선택 확인.
- `dev.ps1 browser --version`: 기존 0.27.0 선택 확인.
- 별도 임시 브라우저 세션에서 about:blank 열기 → snapshot -i → close 성공.
- `dev.ps1 bridge check`: 연결 검사 통과.
- guard 거절 exit 1이 PowerShell 실행 진입점에서도 유지됨을 확인.
- WSL 연결 테스트 8/8 통과. 제품 사용자 여정 E2E와 에이전트 실등록 검증은 별도다.

## 기본 CLI 업데이트 및 로딩 차단 원인 확인

사용자 요청으로 `npm install -g @openai/codex@latest`를 실행했다.
Windows 기본 `codex --version`과 `scripts/dev.ps1 codex --version` 모두 **0.153.4**를 반환한다.
프로젝트 실행기는 npm과 앱 설치를 함께 비교해 가장 높은 호환 버전을 선택하도록 수정했다.

최신 CLI의 `debug prompt-input`에서 AGENTS 지침과 연결 스킬 이름을 확인했다.
`app-server`의 읽기 전용 `config/read`는 이 저장소 `.codex` 레이어의 disabledReason으로
**이 Git 저장소 경로의 trusted 등록 필요**를 반환했다. 상위 작업공간만 trusted였다.
따라서 전체 셋업 완료가 아니다. 해당 경로의 프로젝트 신뢰 등록 승인을 사용자에게 요청했다.
프로젝트 신뢰·sandbox·승인 정책은 이 확인 과정에서 변경하지 않았다.

## Codex 이벤트 변환 회귀 검사

`codex-event` 진입점에서 Bash 명령과 apply_patch의 추가·수정·삭제·이동 경로를
기존 Claude PreToolUse 가드 입력으로 변환한다. 잘못된 입력·저장소 외부 경로·가드 거절은
Codex 차단 규약에 맞춰 exit 2를 반환한다. 검사 대상 명령 자체는 실행하지 않는다.
WSL `python3 -m unittest discover -s scripts/tests -v`: 14개 통과.
이는 합성 이벤트와 기존 가드의 통합 검사이며, Codex 런타임 자동 호출 증거는 아니다.
훅 등록·프로젝트 신뢰·실제 호출 검증은 아직 남아 있다.
