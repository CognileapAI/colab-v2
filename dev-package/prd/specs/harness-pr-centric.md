# Spec: Claude·Codex 공통 PR 중심 하네스 전환

출처: 2026-09-14 사용자 인계 지시(승인됨). 이 문서는
`dev-package/prd/specs/dual-agent-development.md`의 공통 원본 위치와 상태 기록 방식을 이번 전환 범위에서 개정한다.

## 문제 진술

- 현재 공통 규칙·스킬·검사 본문이 `.claude/`에 있고 `.agents/`와 `.codex/`가 이를 역참조해, 도구 중립 원본과 연결 계층의 경계가 뒤집혀 있다.
- 작업 목적·계획·결정·검증·인계가 대형 저장소 문서와 81.8MB의 보고서에 중복되어 시작 비용과 관리 비용이 크며, 커밋·CI·배포 SHA와 강제로 연결되지 않는다.
- GitHub `main`에는 필수 체크·리뷰·ruleset이 없고, `event-breaking`은 CI에서 기본값 `HEAD`로 자기 트리를 비교한다. 프런트 시험은 세션 문서의 마크다운 표를 런타임 입력으로 읽는다.

## 원한 결과

1. `AGENTS.md`, `.agents/skills/`, `.agents/harness.yaml`, `scripts/harness/`가 도구 중립 원본이고 `.claude/`와 `.codex/`는 도구별 등록·payload 변환만 가진다.
2. 작업 중 상세 문서는 로컬에 두고, 영구 인계는 Draft PR의 목적·범위·계획·결정·검증 요약과 커밋 SHA·CI run으로 연결한다.
3. 미착수·백로그·블로커는 GitHub Issue로 이전하되, 비밀값은 Issue나 PR에 복사하지 않는다.
4. 제품의 tenant isolation·권한·migration·계약·생성물·도메인 경계·서비스·프런트·배포·데이터 검증을 유지한다. 준비 실패와 검사 대상 0건은 통과가 아니다.
5. 기존 기록은 소비자와 외부 PR 충돌을 해소하고 이전 완료를 검증한 뒤에만 별도 승인으로 폐기한다. 신구 체계를 영구 병행하지 않는다.

## 기준선 및 재조사 결과

### Codex 기준선 `2e009aef`

| 측정 | 결과 | 판정 |
|---|---|---|
| `scripts/agent-bridge.py check` | 역할 4, 스킬 연결 13, 훅 9/6; exit 0 | 통과 |
| `gates/run.sh exec-bit` | green 1 / 판정 red 0 / 준비 red 0; exit 0 | 통과 |
| `gates/run.sh agent-bridge` | 77 tests, skipped 10; exit 0 | 통과 |
| fresh Codex 시작 주입·baseline 훅 실발화 | 당시 PATH 조회로 실행기 부재로 오판. 후속 확인에서 PowerShell은 존재하나 UNC의 unsigned `dev.ps1` 실행 정책으로 차단. baseline 실발화는 측정하지 못함 | 준비 실패·미판정 |
| 파일 무수정 | 실행 전후 detached `2e009aef`, tracked diff 0 | 통과 |

### 제품 게이트와 CI

- 게이트 정본은 본 게이트 38개와 selftest 29개다. `all`, `selftest`, `task`는 집계 진입점이다.
- 권한은 `rls-effect`, `service-tests-core-api`, `frontend-test` 조합으로 검증한다. 실제 `deploy_doctor`는 로컬 게이트가 아니라 dev 배포 후 15항목 실환경 검사다.
- `event-breaking` CI는 base ref를 전달하지 않아 `HEAD`와 작업 트리를 비교한다. `contract-breaking`과 같은 `origin/main` 기준으로 고정해야 한다.
- `frontend-test`와 `frontend-typecheck`는 `dev-package/sessions/P8-E01-APPLY-POINTS-DRAFT.md`를 실제 입력으로 읽는다. 저장소 네이티브 계약 fixture로 선이전해야 한다.
- `main` 보호 API는 필수 상태 검사·필수 리뷰·관리자 강제·push 제한이 모두 없고 ruleset도 없다. 최근 확인한 CI run은 artifact를 남기지 않는다.
- 최근 dev 태그는 lightweight와 annotated가 섞여 있고, CI 실패 SHA에 dev 태그와 `deploy_doctor` 15/15 기록이 공존한 사례가 있어 CI↔배포 증거가 강제되지 않는다.

## 유지·교체·이전·폐기

| 판정 | 대상 | 이유와 종료 조건 |
|---|---|---|
| 유지 | 제품 불변 규칙, 38개 본 게이트·29개 selftest, Claude/Codex 역할, `deploy_doctor` 15항목, agent-browser E2E | 검사 범위나 판정부를 줄이지 않는다. 정적·실발화·모델 행동·사용자 여정을 구분한다. |
| 유지 | `CLAUDE.md`와 `.claude/`, `.codex/`의 도구별 진입점 | 공통 본문을 제거하고 등록·호출·payload 차이만 남긴다. |
| 교체 | `.claude/skills` 공통 본문 → `.agents/skills` 원본 | Claude 연결은 얇은 adapter로 바꾸고 동일 본문 중복 0건을 검사한다. |
| 교체 | `.claude/hooks` 판정 본문·`scripts/agent-bridge.py` 중심 구조 → `scripts/harness/` 공통 판정 + 양쪽 adapter | `harness.yaml` 스키마와 fail-closed selftest가 두 도구에서 같은 허용·차단을 낸다. |
| 교체 | 세션/보고서 경로를 요구하는 완료 증거 → 로컬 task 상태 + 커밋 tree/SHA + CI summary/artifact + PR 요약 | 손상·부재·다른 SHA·준비 실패를 모두 거절한다. 배포는 `MAIN_SHA`와 main 조상·CI 성공을 함께 확인한다. |
| 이전 | E-01 권한 표, seed/service/search-golden 등 시험 입력 | 코드·계약 인접 fixture로 먼저 옮기고 이전 전후 같은 시험이 green이어야 한다. |
| 이전 | 대장 open/partial/deferred/blocked와 HANDOFF 블로커 → GitHub Issue | 중복 대조, 기존 Issue 링크 보존, 비밀 내용 제외, 게시 전 사용자 승인. 과거 비밀 2건 계수는 최신 제외 목록이 아님. |
| 이전 | 현재 작업의 목적·계획·결정·검증·인계 → Draft PR | `Plan-Ref` trailer, head SHA, gate 3계수, CI run을 기계 검증. PR은 사용자 직접 게시, push는 사전 승인. |
| 폐기 후보 | `dev-package/sessions/`, 실행 보고서, 대형 HANDOFF·PLAN 이력, 중복 미러 | 시험 입력 선이전, Issue 이전, 외부 PR #35/#38 충돌 해소, 새 하네스 green, 사용자 별도 삭제 승인 후에만 제거. |
| 폐기 안 함 | 현재 유효 제품 명세·지속 결정·규칙·검사 코드, 비밀 회전 기록의 안전한 원본 | 새 정본 경로가 확정되지 않은 값은 유지한다. 비밀은 GitHub로 이전하지 않는다. |

## 구현 결정

- `.agents/harness.yaml`은 JSON 호환 YAML로 두고 표준 라이브러리로 fail-closed 파싱한다. CoLAB의 `main`, 서비스 경로, 게이트 명령, 세 상태, 로컬 전용 경로, PR/SHA 계약을 선언한다.
- 공통 검사기는 `scripts/harness/`에 작은 모듈로 분리한다. `.claude/hooks`와 `scripts/agent-bridge.py`는 입력을 공통 schema로 변환해 호출한다.
- 로컬 task 상태와 gate summary는 checkout의 Git common dir 아래에 둔다. 실행 이력은 커밋하지 않고 PR 요약과 CI artifact만 영구 검토 단위로 사용한다.
- GitHub 보호 설정 변경은 저장소 코드와 분리한다. 이번 branch는 요구 check를 정의·검증하고, ruleset 적용안은 게시 전 사용자 승인을 받는다.
- 외부 PR #35/#38의 기존 기록 경로 변경은 호환 기간 동안 허용한다. 기존 소비자가 0이 되기 전에는 retired path를 차단하지 않는다.

## 시험 결정

- `agent-bridge`와 신규 harness selftest에서 잘못된 config, 빈 선언, 준비 실패, 다른 SHA, 누락 artifact, 경로 이탈을 음성 fixture로 거절한다.
- CI fixture로 `event-breaking` base ref 누락과 PR evidence SHA 불일치를 red로 고정한다. pull request는 event의 base/head SHA, push는 before/after SHA를 사용하며 움직이는 `origin/main`을 실행 증거 식별자로 저장하지 않는다.
- E-01 마크다운 의존은 JSON fixture로 옮긴 뒤 `frontend-test`와 `frontend-typecheck`를 실행한다.
- 정적 검사, Claude/Codex 훅 실발화, 구독 CLI 모델 행동 평가, 양방향 Draft PR 인계 모의시험을 별도 결과로 기록한다.

## 단계와 승인 경계

1. 공통 config·검사기와 fail-closed selftest.
2. CI base/SHA/PR 증거 연결과 모든 문서 의존 시험 fixture 선이전.
3. 스킬·규칙·역할·인접 resource·훅의 공통 원본 이전 및 양쪽 adapter.
4. 로컬 task 상태와 PR 중심 인계 전환, 문서 의존 검사·Slack·task gate 소비자 교체, 이전 호환 읽기.
5. 배포 전 PR·main SHA·CI 성공 판정기와 음성 시험, ruleset·deployment 적용안 작성.
6. 전체 정적·실발화·모델·양방향 인계 검증.
7. PR 요약·절차는 사용자 직접 게시용으로 제공한다(2026-09-15 사용자 개정). push·Issue·ruleset은 내용·대상 제시 후 승인받으며, 게시 대기로 독립 로컬 구현을 멈추지 않는다.
8. 병합·배포·기존 기록 삭제는 각각 별도 승인 후 실행.

## 수용 기준

- 공통 정책·스킬·검사 본문은 각 1개 원본이며 양쪽 adapter가 같은 hash/schema를 검사한다.
- config 오류·검사 미선언·준비 실패·검사 대상 0건·SHA 불일치는 exit 78 또는 1이고 green이 아니다.
- CI의 breaking 검사 둘 다 pull request event의 고정 base SHA를 사용한다. gate summary와 artifact는 PR head SHA, merge 시험 SHA, push after SHA를 구분해 포함한다.
- tenant isolation, 권한, migration, contract/generated, boundary, service, frontend, data, harness의 관련 게이트가 green이다. `deploy_doctor`는 실제 배포 검증으로 별도 표기한다.
- Claude와 Codex에서 정상 허용 1건·보호 편집 차단 1건을 각각 실발화하고, 모델 행동 평가를 동일 fixture/판정부에서 별도 실행한다.
- Claude→Codex와 Codex→Claude가 PR 요약·commit SHA·CI 증거만으로 다음 행동과 승인 경계를 재현한다.
- PR은 사용자에게 요약·절차만 제공한다. Issue/push/ruleset 쓰기는 내용·대상 제시 후 별도 승인받는다. 병합·배포·삭제는 별도 승인 없이 수행하지 않는다.
- 기존 기록 폐기는 이전 대상 0건, 기존 소비자 0건, 외부 PR 충돌 0건, 별도 승인 전에는 실행하지 않는다.
- 배포 전 판정기는 대상 full SHA가 `main` 조상이고 병합 PR과 연결되며 같은 SHA의 필수 CI가 성공했을 때만 통과한다. doctor는 첫 배포의 선행 조건이 아니다. dev 배포 후 같은 환경·release·SHA의 새로운 doctor 15항목을 한 번의 실행으로 검증한 뒤에만 태그와 완료를 확정한다. staging 리허설은 dev 완료 근거가 아니다.

## 범위 밖

- 제품 기능·데이터 변경, 실제 dev/prod 배포, `main` 병합·push, 원격 branch/tag 정리.
- `30 CoLAB-v2`의 파일·브랜치·worktree 접근 또는 변경.
- 노출 자격증명 내용을 Issue/PR로 복사하는 일.

## 산출 계획

- 실행 뷰: `dev-package/prd/rounds/R-HARNESS-PR-CENTRIC.md`.
- 구현은 현재 `codex/harness-pr-centric` worktree에서 직렬로 수행한다.
