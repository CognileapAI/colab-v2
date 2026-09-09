# Claude 하네스 Codex 전수검사

요청: 기존 Claude 하네스 구조를 Codex에서도 사용하도록 전수검사·보완한다.
범위는 현재 CoLAB v2 하네스다. 제품 E2E와 과거 프로젝트 보관은 기존 전환 계획의 별도 항목이다.
**전체 운용 인수는 아직 완료하지 않았다.** 프로젝트·훅 신뢰 및 실제 역할 실행 검증이 남았다.

## 전수 목록

| 원본 스킬 | Codex 진입점 | 대응 |
|---|---|---|
| colab-v2-work | 동일 이름 | 공통 규율과 단계 라우팅 |
| agent-browser | 동일 이름 | WSL CLI와 추가 리소스 조회 |
| apple-design | 동일 이름 | 프로젝트 디자인 제약 우선 |
| design-review | 동일 이름 | 조사자는 읽기 전용 반환, 기록 주체 하나 |
| executing-plans | 동일 이름 | 지정 사본과 계획 상태 유지 |
| grill-me | 동일 이름 | grilling 파일 직접 로딩, 명시 호출 정책 유지 |
| grilling | 동일 이름 | 사실 조사와 사용자 결정 질문 분리 |
| receiving-code-review | 동일 이름 | 실제 근거 대조 후 수용 |
| test-driven-development | 동일 이름 | 원본 테스트 절차와 보조 문서 재사용 |
| to-spec | 동일 이름 | 승인된 intent 입력, 명시 호출 정책 유지 |
| verification-before-completion | 동일 이름 | intent와 실제 검증 대조 |
| writing-plans | 동일 이름 | 승인된 사양에서 계획 작성 |

모든 원본은 `.claude/skills/<이름>/SKILL.md`, Codex 연결은 `.agents/skills/<이름>/SKILL.md`다.
개인 `intent`는 `grill-me` 별칭이다. 개인 grill-me/to-spec은 상위 작업공간에서 같은 저장소 진입점을 찾는 연결이다.
원본 **12개**와 개인 별칭을 혼동하지 않는다. 호출명은 Codex의 `$이름`이다.

| 역할 4개 | 처리 |
|---|---|
| advisor | 원본 검토 기준 + read-only sandbox 설정 |
| researcher | 산출 경계, 단독 writer, 미승인 intent의 자동 승인 금지 |
| lane-worker | 격리·HEAD 확인 + 원본 frontmatter의 4개 스킬 명시 로딩 |
| gate-runner | 지정된 단일 게이트, 종료코드·세 계수·경로 회수 |

규칙 3개도 대조했다. `colab-rules.md`는 공통 규칙으로, `deploy.md`와 `s3-upload.md`는
원본 paths 조건과 같은 경로에 대해 AGENTS.md에서 명시적으로 읽도록 연결했다.

| 셸 훅 9개 | 이벤트 | Codex 대응 |
|---|---|---|
| bootstrap-diet | SessionStart | JSON context, 사용자의 지정 라운드가 mtime 추천보다 우선 |
| worktree-setup | SubagentStart | 기존 준비 작업, 격리 사본 생성은 별도 |
| git-guard | PreToolUse/Bash | 명령 검사, 명령 자체 실행 안 함 |
| migration-guard | PreToolUse/apply_patch | 모든 편집 경로 변환 |
| decision-number-guard | PreToolUse/apply_patch | 삭제·이동 목적지도 검사 |
| test-file-guard | PreToolUse/apply_patch | Windows fix 환경값을 WSL까지 전달 |
| css-edit-audit | PostToolUse/apply_patch | CSS 계측 출력을 additionalContext로 전달 |
| uncommitted-artifacts | SubagentStop/researcher | stdout JSON 변환, 차단은 exit 2 |
| lane-gate-summary | SubagentStop/lane-worker | 원본 판정 유지, stdout JSON 변환 |

## 발견하여 보완한 문제

1. 연결 검사가 스킬 2개만 고정 검사했다. 원본 12개 전체와 훅 이벤트·matcher 전수를 검사하도록 수정했다.
2. 자동 훅 등록 파일이 없었다. `.codex/hooks.json`에 5개 이벤트 등록을 준비했다.
3. Codex patch와 Claude Edit의 payload가 다르다. 추가·수정·삭제·이동의 전체 경로를 검사한다.
4. Claude 종료 훅의 plain text는 Codex SubagentStop 출력 계약에 맞지 않는다. JSON으로 변환한다.
5. Windows 환경변수가 WSL에 자동 전달되지 않았다. 제어 변수 4개만 값·미선언 상태를 명시 전달한다.
6. PowerShell은 native exit 2를 shell exit 1로 바꿀 수 있었다. 등록 명령 자체에서 정확한 차단 코드를 반환한다.
7. Git 루트/스크립트 로딩 오류가 exit 1로 열려 있었다. bootstrap 오류도 차단으로 변환한다.
8. 하위 폴더에서 저장소 문서를 찾지 못했다. AGENTS와 모든 연결 스킬에 저장소 경로 기준을 명시했다.
9. 준비 실패가 exit 1로 보고되는 실제 평가 실패를 발견했다. 원본 게이트 규약 0/1/78을 연결 문서에 명시했다.
10. lane-worker의 원본 frontmatter 스킬 로딩이 누락됐다. 네 스킬을 단계별로 명시 연결했다.
11. intent 초안 승인 대기와 H6 자동 커밋 요구가 충돌했다. 조사자는 초안을 부모에게 반환하고 부모가 기록한다.
12. 디자인 조사 복수 writer와 fix 테스트 차단/RED 작성 충돌을 발견했다. 단독 기록과 단계 분리를 명시했다.

## 검증 증거

- `skills/list(forceReload=true)` 실제 호출: 저장소 스킬 12개 enabled, 파싱 오류 0.
- `quick_validate.py`: 저장소 12개 전부 통과.
- 실제 Codex 읽기 전용 smoke: grill-me 원본 경로를 올바르게 보고하고 구현 승인 없음으로 판단.
  PowerShell Get-Content는 child CLI 정책에 거절됐고, 읽기 도구 fallback으로 두 파일을 읽었다.
  이는 **일반 셸 실행 준비 완료 증거가 아니다**.
- WSL `unittest discover -s scripts/tests`: **37개 중 34개 통과**, Windows 전용 3개는 별도 native 실행에 귀속.
- Windows bridge 테스트: 24개 중 18개 통과, Linux 전용 6개는 WSL 검사에 귀속.
  특히 하위 폴더 정상 명령, native fix 모드 차단, Git 루트 부재 차단을 실제 등록 명령으로 확인했다.
  이후 추가한 Linux 등록 명령의 하위 폴더 허용·강제 push 차단 검사도 WSL에서 통과했다.
- 기존 Claude runner selftest: 모델 호출 없이 7개 기대대로 통과. 기존 runner와 expect.sh를 수정하지 않았다.
- 기존 평가 20개 모두 task.md·fixture/·expect.sh 존재 확인.
- Codex 초기 실제 평가: H01 1/2, H14 0/2, H18 0/2. 실패를 성공으로 변경하지 않았다.
  결과: `eval/harness/results/codex-20260908-audit/summary.json`.
  H01의 한 실패는 실제 Git 객체를 읽었으나 판정부가 요구하는 git log 명령을 실행하지 못한 경우다.
  H14/H18 실패는 준비 실패 종료코드를 1로 제안한 경우다.
- 수정 후 H14/H18 재검증 결과는 아래 후속 기록에서 관리한다.

## 승인 전 미확인·제한 (후속 활성화 기록으로 갱신)

- `config/read`의 저장소 `.codex` 레이어는 trusted 미등록으로 disabled 상태다.
  `hooks/list`는 0개를 반환했다. 파일 등록 준비를 자동 활성화 완료로 보고하지 않는다.
- 프로젝트 trust 등록을 사용자에게 요청했다. `/hooks`의 정의별 review도 별도로 필요하다.
- 역할 4개 TOML은 정적 확인만 됐으며, 실제 역할 선택·제한 동작은 활성화 뒤 확인한다.
- H7 원본은 잘못된 JSON이나 일부 준비 실패에 관대하다. 원본을 몰래 바꾸지 않았으며,
  Codex 완료 판정에는 `verify-report`의 명시 게이트·스키마·현재 트리 검증을 추가로 사용해야 한다.
- 훅은 모든 파일 IO의 OS 경계가 아니다. 셸 내부 편집, 후속 write_stdin, 별도 MCP IO까지
  apply_patch 훅으로 강제한다고 주장하지 않는다.
- Codex runner는 Claude의 달러 예산 옵션을 지원하지 않는다. 명시 timeout, 2회 반복,
  사용 토큰과 미확인 모델 상태를 기록한다. 모델별 성능 비교나 달러 상한 증거로 쓰지 않는다.
- 실제 평가 나머지 17개와 제품 사용자 여정 E2E는 미실행이다.
- 브라우저 추가 references/templates와 graphify는 현재 로컬에 없다. 확보하지 않은 기능을 실행했다고 하지 않는다.

## 다음 인수 절차

프로젝트 신뢰 등록 → `/hooks` 정의별 검토 → 실제 허용/차단 이벤트 확인 → 역할별 최소 과제 →
셸 준비 실패 해소 → 나머지 평가 17개 및 전체 결과 인수.
커밋·push·배포·제품 데이터 변경은 이 검사에서 수행하지 않았다.

## 후속 실제 평가 — 첫 보완 후

`eval/harness/results/codex-20260908-audit-fixed/summary.json`: H14 **2/2 green**, H18 **1/2**.
판정부는 원본 그대로다. H18 실패 실행은 셸 정책 때문에 Git 루트를 찾지 못하고 지침을 읽지 못했다.
AGENTS.md에 파일 경로 기반 루트 확인과 필수 종료코드 규약을 추가한 후 H18을 별도로 재검증한다.
실제 모델은 runner에서 미확인으로 표시하며 특정 모델의 성능 결과로 귀속하지 않는다.

## 승인 전 기록 — 시작 지침 보완 후

`eval/harness/results/codex-20260908-audit-entry/summary.json`: **H18 2/2 green**.
H14도 앞선 보완 후 **2/2 green**이다. 원본 expect.sh는 변경하지 않았다.
H01은 최초 **1/2** 결과를 그대로 유지하며 셸 실행 정책 문제를 해소한 뒤 다시 검증해야 한다.
남은 17과제는 미실행이다. 일부 행동 개선을 전체 인수 완료로 확대하지 않는다.

최종 `config/read`에서도 저장소 레이어 disabled, `hooks/list` 0개를 재확인했다.
프로젝트 trust 승인 요청은 아직 답변 대기다. 권한·신뢰 설정을 임의로 변경하지 않았다.
독립 코드 재검토에서 Windows 환경 전달·bootstrap 차단·모델 미확인 표기의 수정 확인을 받았다.
`bridge check`와 `git diff --check`도 통과했다. 테스트의 플랫폼별 합집합은 37개이며
Windows 전용 3개는 native에서, 나머지 34개는 WSL에서 통과했다.

## 사용자 승인 후 실제 활성화 — 2026-09-09

사용자 「하자」 승인에 따라 이 저장소의 project trust를 등록하고 CLI `/hooks`에서
준비된 7개 정의를 검토·신뢰했다. 전역 훅 우회 플래그는 사용하지 않았다.
사용자 설정 백업: `<codex-config-backup>/config-before-colab-trust-20260908-234610.toml`.
`config/read`의 프로젝트 레이어 disabledReason은 null, `hooks/list`는 7개 모두
enabled=true/trustStatus=trusted/errors=[]였다. 실제 세션 모델 응답은 gpt-6-astra였다.

- 프로젝트 `.codex/config.toml`에 Windows unelevated 백엔드와 allow_login_shell=false를 설정.
  기본 로그인 셸 프로필이 cwd를 F:/로 바꾸는 현상을 재현했다. 파일·네트워크 권한과 승인 정책은 확장하지 않았다.
- 실제 Codex git status 실행 exit 0 및 자동 SessionStart/PreToolUse 실행 확인.
- `git push --dry-run --force origin main`은 자동 PreToolUse가 blocked로 차단했다.
  명령 본체는 실행되지 않았다. 증거: `eval/harness/results/activation-negative.json`.
- advisor 실제 등록 역할 spawn 및 읽기 전용 자식 실행 확인.
  부모 `01a08183-005a-7553-938d-89d29d26abae`, 자식 `01a08183-280a-7011-9232-0e2c16f4b3d5`.
  ephemeral 부모에서는 spawn이 실패해 일반 세션으로 검증했다.
- gate-runner 최초 실행은 Windows sandbox의 WSL 접근 거절로 **게이트 미실행**이었다.
  원인을 재현한 뒤 새 smoke에서 정확한 guard/게이트 명령만 일회 승인했다.
  실제 `scripts/dev.ps1 gate contract-lint` 1회 실행 exit 0, seam 3건·위반 0.
  green 1 / red(판정) 0 / red(준비) 0. 원 실행기는 전체 계 줄이나 로그 경로를 배출하지 않았다.
  증거: `eval/harness/results/activation-gate.json`. 전체 승인 캐시·전역 우회는 추가하지 않았다.

### 실제 행동 평가와 판정부 호환성

추가 18과제 각 2회 실행: `codex-20260908-active-a/summary.json`, `codex-20260908-active-b/summary.json`.
이전 H14 2회·H18 2회를 합쳐 전체 20과제·40개 응답을 확보했다. 동시 단일 전수 실행으로 부르지 않는다.
Windows text stdin이 LF를 CRLF로 바꿔 H07의 정확한 13건을 오답 처리했다.
러너를 UTF-8 bytes stdin으로 수정했다. H03은 `rg -n`과 행 번호를 붙이는 PowerShell
Get-Content/ForEach-Object를 기존 번호 출력 명령과 동등하게 인정했다.
fixture와 task는 바꾸지 않았다. 이전의 「expect 미변경」은 승인 전 기록이며 H03 expect만 이번에 변경했다.
번호 없는 조회·잘못된 행/건수 거절과 Windows→WSL 줄끝 회귀를 검증했다.

동일 저장 응답을 보정된 전달 방식으로 재판정한 결과 **39/40 green**.
`eval/harness/results/activation-rejudged.json`은 원 응답·판정부 hash와 원래 결과를 보존한다.
모델을 다시 실행한 결과로 포장하지 않는다. H09 두 번째는 같은 토큰이라는 근거를 맞혔으나
최종 「판정: 없음」으로 원 판정부에서 실패했다. 이 실패를 숨기거나 H09 정답을 바꾸지 않았다.

최신 테스트: WSL 42개 중 39개 통과·Windows 전용 3개 제외. Native bridge 테스트에서
그 Windows 전용 3개 모두 통과. 플랫폼 합집합 **42개 통과**. bridge check와 diff --check 통과.
이는 제품 전체 E2E·배포·원격 CI 완료 증거가 아니다. 미커밋 변경을 유지했다.

### 나머지 역할과 자동 환경 준비 실측

`activation-roles.json`에 researcher/lane-worker 실제 역할 호출과 AGENTS.md 존재 조회를 기록했다.
researcher H6는 현재 미추적 조사 문서를 찾아 종료 차단, lane-worker H7은 다른 커밋의 기존
보고서를 찾아 종료 차단했다. 이는 기대한 보호 동작이며 구현 완료나 해당 레인의 gate green은 아니다.
산출물 커밋이나 가짜 보고서로 차단을 해제하지 않았다.

자동 H2는 실제 호출됐으나 처음 core-api 환경 준비 1건이 실패했다. non-login WSL의 PATH에
이미 설치된 ~/.local/bin/uv가 빠져 pip 없는 uv venv를 pip로 갱신하려 했기 때문이다.
브리지 자식 프로세스에만 ~/.local/bin·~/.npm-global/bin을 연결해 수정했다. 전역 PATH는 유지했다.
같은 SubagentStart payload를 어댑터로 재실행한 `activation-environment-replay.json`은
**신설 1·재사용 5·실패 0**을 기록했다. 이는 수정 후 어댑터 재실행이며 새 모델 spawn 실측과 구분한다.
