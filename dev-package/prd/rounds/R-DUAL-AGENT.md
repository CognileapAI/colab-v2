> spec: dev-package/prd/specs/dual-agent-development.md
# Claude·Codex 공통 개발 환경 실행 계획

> 2026-09-09 최신 상태: Codex Astra 전체 평가는 **40/40 통과**했으며 저장소 compact 증거는 `eval/harness/results/codex-40-final-acceptance-20260909.json`이다. 전체 parity 수용은 **미완료**다. Claude 신규 전체40회·Claude 실제 개발 E2E·데스크톱 재시작 후 최신 코드 검증이 남아 있다. 아래 39/40과 38/40 표기 및 실행 기록은 당시 이력이며 현재 상태가 아니다.

> 실행자는 이 계획과 spec을 함께 읽고 현재 대화의 승인 범위를 적용한다. 이 세션에서 순차 실행한다.

**Goal:** 두 도구가 공통 원본을 사용하고 실제 개발·검증·인계를 재현할 수 있는 상태까지 전환한다.
**Architecture:** 공통 원본 유지 + 도구별 연결 + 공통 검증 + 환경별 실제 실행 증거.
**Tech Stack:** Codex/Astra, Claude Code, Python, PowerShell, WSL Bash, agent-browser, 기존 gates/eval.
**Spec:** `dev-package/prd/specs/dual-agent-development.md`

## 전체 상태

**진행 중. 전체 완료 아님.** 완료 판정은 이 계획의 필수 단계와 spec 수용 기준을 대조한다.
2026-09-09 사용자 정정에 따른 현재 하네스 실행 계획은 **`R-CODEX-PARITY.md`**다.
등록·호출 확인을 완료로 확대했던 기준을 강화했다. 제품 E2E·보관의 기존 범위는 이 파일에 유지한다.
개별 명령이나 단계가 끝나면 다음 실행 가능한 단계로 진행한다.
진행 보고는 전체 목표·완료 범위·현재 작업·차단·다음 실행 순서를 함께 적는다.

| 단계 | 상태 | 의존 | 완료 증거 또는 남은 일 |
|---|---|---|---|
| 실행 환경 정비 | 완료 | 없음 | 기본/프로젝트 CLI 0.153.4, 브라우저 임시 세션 기동·snapshot·종료 |
| 공통 원본·연결 파일 | 완료 | 없음 | 스킬 12개 discovery·역할 4개·규칙 3개·훅 9개 연결. 전수검사 후속 기록 참조 |
| 설정·역할 실등록 | 등록·호출 확인 | 승인 완료 | 역할별 정상 완주는 R-CODEX-PARITY T3/T4에서 검증 |
| 자동 훅 연결 | 일부 런타임 확인 | 승인 완료 | 전체 정상/음성·데스크톱 동등성은 미완료 |
| 로컬 Claude/Codex eval | 부분 인수 | 최종 동일 스냅샷 | Codex Astra 신규 40/40 완료. Claude 신규 전체40회와 양쪽 최종 비교 필요 |
| agent-browser 사용자 여정 E2E | 미착수 | 테스트 환경·데이터·합격 기준 확보 | 도구 기동만 확인됨. 제품 시나리오는 아직 실행 안 함 |
| 과거 작업 보관 준비 | 진행 중 | 없음 | 7개 저장소 1차 조사 완료. 상세 목록·참조·WSL worktree 확인 필요 |
| 전체 회귀·인수 | 미착수 | 앞 단계 | 부분 통과를 합쳐 전체 통과로 보고하지 않음 |

## Global Constraints

- 제품 코드와 데이터의 무관한 변경, 다른 작업의 파일 덮어쓰기, 전역 권한 완화 금지.
- 동일 checkout의 쓰기 주체 하나. 추가 구현 에이전트는 격리 사본에서만 실행.
- 프로젝트·hook trust는 승인 및 등록 완료. 기존 요청을 반복 질의하지 않는다.
- API 키 발급·클라우드 모델 CI 도입은 필수 작업에 넣지 않는다.
- 폴더 이동은 정확한 원본·목적지와 참조 수정 목록을 만든 뒤 수행. 삭제는 범위 밖.
- 기존 제품 라운드는 이 계획과 별개다. 사용자 지정 작업이 이 전환이면 이 파일을 읽는다.

## 1. 설정·역할 실등록

- [x] `AGENTS.md`, `.agents/skills/*/SKILL.md`, `.codex/agents/*.toml` 준비 및 원본 실존 검사.
- [x] 최신 CLI의 `debug prompt-input`에서 AGENTS와 연결 스킬 확인.
- [x] `config/read`로 실제 레이어 비활성 원인 확인. 프로젝트 신뢰 승인 요청 전송.
- [ ] 승인 도착 시 해당 저장소 경로만 trust 등록. 현재 설정 백업, 관련 항목만 변경.
- [ ] `config/read` 재조회로 disabledReason 해소를 확인하고 파일 읽기 smoke를 반복.
- [ ] advisor·lane-worker·researcher·gate-runner가 실제 후보로 발견되는지 확인.
- [ ] 역할별 최소 과제로 읽기 전용 검토·격리 요구·출력 경계 확인. 실패를 설정 통과로 대체하지 않음.

검증 명령: `scripts/dev.ps1 bridge check`, `scripts/dev.ps1 codex debug prompt-input`.
추가 증거는 `dev-package/sessions/20260908-codex-bridge.md`에 기록.

## 2. 자동 훅 연결

- [x] 현재 CLI 공식 문서에서 hook 위치·지원 이벤트·차단 응답·trust 조건을 확인.
- [x] `.claude/settings.json`의 등록별 대응표 작성. `docs/development/dual-agent.md`의 자동 훅 전환 조사 참조.
- [x] 기존 `scripts/agent-bridge.py`와 기존 hook 본문을 재사용하는 이벤트 변환 구현.
- [ ] Codex hook 등록 파일 준비 및 실행 경로 검증.
- [ ] 사용자 trust를 우회하지 않고 활성화. 활성화 전에는 설정 준비로만 보고.
- [ ] 실제 Codex 명령에서 안전한 조회 허용·worker main push 차단·fix 시험 편집 차단 증명.
- [x] `scripts/tests/test_agent_bridge.py`에 발견된 payload 차이·실행 오류의 음성 회귀 추가. WSL 14/14 통과.

검증: `python3 -m unittest discover -s scripts/tests -v` + 활성 런타임 이벤트 증거.

## 3. 로컬 eval

- [ ] `eval/harness/run.sh`, `H01`~`H20`의 fixture/expect 계약을 확인.
- [ ] 기존 Claude 실행을 유지하고 Codex 응답 추출·종료 상태 변환만 별도 연결.
- [ ] 먼저 H01·H14·H18로 낡은 상태/조용한 통과/세 상태 판정을 각각 확인.
- [ ] 오류 응답·타임아웃·예상 출력 부재를 준비 실패로 분류. 모델의 문장만으로 성공 처리 금지.
- [ ] 원본·모델·CLI·과제·반복 수·코드 식별자·실행 시간을 결과에 기록하고 두 모델 결과 비교.
- [ ] 비교 결과에 따라 나머지 과제 실행. 실패 원인이 판정부인지 행동인지 구분해 수정 범위를 결정.

기존 fixture/expect를 복사하지 않는다. CI는 결정적 연결 검사만 유지한다.

## 4. 사용자 여정 E2E

- [x] 기존 WSL agent-browser 0.27.0 경로와 Chrome 기동 확인.
- [ ] `infra`, 배포 문서, 기존 테스트 fixture에서 격리 환경·계정·실파일 입력을 확인.
- [ ] 시나리오와 기대 결과를 먼저 고정: 로그인 → 파일 업로드 → 등록 → 검색 → 상세/미리보기 → 새로고침.
- [ ] 실패 시나리오 고정: 잘못된 파일·권한 없는 접근의 거절과 상태 보존.
- [ ] agent-browser로 실제 행동을 수행하고 API/저장 결과와 사용자 화면을 대조.
- [ ] 결과에 대상 SHA·URL 식별·시나리오별 결과·증거 경로·준비 실패를 명시. 인증 비밀은 기록하지 않음.
- [ ] 기존 frontend-visual과 별도 판정으로 연결하고 전체 사용자 여정 결과를 보고.

도구 진입: `scripts/dev.ps1 browser <인자>`. about:blank 성공을 이 단계 완료로 처리하지 않는다.

## 5. 과거 작업 보관

- [x] 후보는 `00 CoLAB-PoC`, `01 CoLAB-Plan`, `10 CoLAB-Launch`로 한정.
- [x] 총 7개 Git 저장소의 최근 커밋·status 항목 수·worktree 등록 1차 조사.
- [ ] 미커밋 파일 목록·미병합 브랜치·원격 반영 여부를 각 저장소에서 확인.
- [ ] Windows의 prunable 표시를 WSL에서 재확인. OS 경로 표기 차이를 삭제 근거로 사용하지 않음.
- [ ] design-review의 Plan 참조 등 현재 소비처를 모아 보관 이후 경로표와 변경 목록 작성.
- [ ] 보존 대상·목적지를 목록으로 확정하고 충돌 없는 이동 수행. 작업 중인 worktree는 유지.
- [ ] 이동 뒤 원본 수·Git 상태·현재 제품 참조를 재검증.

1차 실측은 아래와 같다. status 건수는 `git status --porcelain --untracked-files=normal`의 **행 수**이며
파일 수나 삭제 가능 수가 아니다. 원격 fetch·hash 중복 검사·폴더 이동은 아직 하지 않았다.

| 저장소 | HEAD / 최근 커밋일 | status 행 | 주의 |
|---|---|---|---|
| PoC | 5a364d3 / 2026-05-10 | 9 | 미커밋 내용 보존 |
| Plan | 2393dd7 / 2026-08-23 | 8 | 현재 design-review의 참고 경로 존재 |
| Launch/backend | 081d1ab / 2026-07-17 | 0 | Windows 조회에서 prunable worktree 2 |
| Launch/contracts | 385a9f0 / 2026-07-17 | 0 | 현재 feature branch, prunable worktree 2 |
| Launch/frontend | 7f9977e / 2026-05-31 | 1 | prunable worktree 1 |
| Launch/infra | 8e65652 / 2026-05-31 | 0 | 미병합·소비처 점검 필요 |
| Launch/dev-package | be666fc / 2026-07-17 | 3 | prunable 1, locked worktree 1 |

## 6. 전체 인수

- [ ] 위 단계의 실제 결과와 spec의 여덟 수용 기준을 하나씩 대조.
- [ ] 기존 Claude 사용 경로와 결과에 회귀가 없는지 확인.
- [ ] 완료·실패·준비 대기·범위 제외를 구분하고 남은 것을 완료로 숨기지 않음.
- [ ] 다음 세션 진입점과 일상 실행 명령을 공통 문서에 정리.
- [ ] 변경 diff·검증 기록을 검토 가능한 상태로 제출. 커밋·push는 대화의 권한 범위 적용.

## 현재 실행 순서

### 2026-09-08 후속 — Claude 하네스 전수검사

요청과 결과 원본은 `dev-package/sessions/20260908-harness-audit.md`.

- [x] 스킬 12·역할 4·규칙 3·셸 훅 9·평가 과제 20개 구성 전수 대조.
- [x] 모든 스킬의 Codex 진입점과 실제 skills/list discovery 확인.
- [x] 규칙 경로 라우팅·역할 스킬 주입·초안 승인 충돌·하위 폴더 경로 기준 보완.
- [x] 5개 이벤트 등록 파일, Windows↔WSL 제어 변수 전달, stdout JSON 및 차단 종료코드 변환.
- [x] 기존 Claude runner selftest 7개 통과. Windows/Linux 등록 명령의 허용·차단 직접 검증.
- [x] Codex 별도 평가 runner와 오류/완료 응답 검사 추가. 원본 fixture/expect 유지.
- [x] 사용자 승인 후 프로젝트 신뢰·훅 7개 review 완료. 실제 SessionStart 및 PreToolUse 강제 push 차단 확인.
- [x] 초기 실패를 보완한 실제 행동 재검증: H14 0/2→2/2, H18 0/2→1/2→2/2. 원본 판정부 유지.
- [x] 전체 20과제 각 2회 응답 확보. H01은 활성화 후 2/2. Windows stdin·H03 명령 호환 보정 후 39/40 통과.
- [ ] 행동 평가 전체 green 인수: H09 두 번째 판정 표기 실패 유지. 근거는 맞혔으나 성공 처리하지 않음.
- [x] advisor 실제 역할 spawn 및 gate-runner 실제 contract-lint 실행 exit 0 확인.
- [x] researcher/lane-worker 실제 호출, H2 자동 준비·H6 미추적 문서 차단·H7 오래된 증거 차단 기록.
- [x] H2의 non-login WSL uv 탐색 실패 수정. 같은 payload 재검증 신설 1·재사용 5·실패 0.

이 요청의 하네스 검사와 기존 제품 E2E·보관 단계는 구분한다. 그 단계의 상태를 이 검사로 완료 처리하지 않는다.

2026-09-09 현재 project/hook trust 승인·실등록 완료. 활성화 증거와 39/40 평가 결과는 감사 기록에 연결했다.
검증 의존이 충족되는 순서로 실행하며, 의존 없는 작업을 하나의 승인 대기로 멈추지 않는다.
