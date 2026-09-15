# CoLAB v2 — 공통 작업 진입점

개발 루트는 이 Git 저장소다. 상위 작업공간의 과거 프로젝트는 기본 탐색 대상이 아니다.
이 문서의 모든 저장소 상대 경로는 **이 AGENTS.md가 있는 저장소 루트 기준**이다.
하위 폴더에서 시작했으면 먼저 Git 루트를 확인한다. 과제의 입력 파일은 지정된 과제 디렉터리,
프로젝트 규칙·스킬·게이트는 저장소 루트를 기준으로 찾는다.
셸에서 Git 조회가 불가능하면 로드된 프로젝트 스킬의 실제 `.agents/skills/<이름>/SKILL.md`
경로에서 세 디렉터리 위를 저장소 후보로 찾아 AGENTS.md와 `.git` 존재를 파일 조회로 확인한다.
하위 폴더에 문서가 없다는 이유로 저장소 지침이 없다고 판단하지 않는다.
먼저 `docs/development/dual-agent.md`를 읽는다. 기존 제품 규칙의 원본은
`.agents/rules/product.md`이며 §0·§3·§5·§6·§10을 필요한 범위에서 확인한다.
`CLAUDE.md`는 이 진입점을 읽는 얇은 어댑터다. 제품 본문은 원문과 stage 표지를 보존했다.
그 안의 과거 세션 시작·종료 절차(§1·§6)와 공통 스킬의 legacy 기록 안내는
아래 신규 작업 절차를 대체하지 않는다. 제품 요구·완료 조건·검사 범위는 그대로 유지한다.
Codex 연결 문서는 제품 요구사항이나 승인된 결정을 변경하지 않는다.

여러 단계 작업은 전체 계획을 먼저 확인하고 단계·의존·검증 상태를 갱신하며 진행한다.
이번 Claude/Codex 전환의 실행 계획은 `dev-package/prd/rounds/R-HARNESS-PR-CENTRIC.md`다.
개별 수정이 끝났다는 이유로 전체 작업을 종료하지 않는다. 승인 대기와 독립인 작업은 계속한다.

- 신규 작업은 사용자가 명시한 task·intent/spec·PR 요약·로컬 계획을 우선한다.
  시작·인계 증거는 `docs/development/lifecycle-evidence.md`의 task runtime에 둔다.
  지정이 없으면 최근 Git 이력과 현재 요청을 대조하며 mtime으로 다음 작업을 결정하지 않는다.
  `dev-package/work-items.yaml`·HANDOFF·세션 문서는 미이전 제품 상태의 읽기 호환 자료다.
  해당 legacy 제품 항목을 실제로 변경할 때만 기존 대조 게이트와 기록 정합을 유지한다.
  신규 task를 만들었다는 이유만으로 legacy 대장·세션·결정번호를 추가하지 않는다.
- PR 게시는 사용자가 수행한다. 에이전트는 로컬 PR 요약·실제 검증 근거·게시 절차를 제공한다.
  PR 미게시를 로컬 전환 구현의 미완료와 혼동하지 않으며 게시 완료를 주장하지 않는다.
- 큰 문서는 해당 제목·앵커 주변만 읽는다. 규칙·스킬 본문을 양쪽에 복제하지 않는다.
- 공통 개발 절차는 `.agents/skills/colab-v2-work/SKILL.md`에서 연결한다.
- `.agents/rules/colab-rules.md`는 공통 규칙이다. 작업에 필요한 절을 읽는다.
  `infra/**`, `docs/DEPLOY*.md`, `services/core-api/ops/**` 변경 전에는 `.agents/rules/deploy.md`,
  `services/core-api/**` 변경 전에는 `.agents/rules/s3-upload.md`를 읽는다.
  Claude의 paths 메타데이터가 Codex에서 자동 적용된다고 가정하지 않는다.
- 브라우저 작업은 `.agents/skills/agent-browser/SKILL.md`를 읽고 agent-browser를 사용한다.
  `frontend-visual`의 읽기 전용 시각 검사는 사용자 여정 E2E를 대신하지 않는다.
- `.claude/settings.json`의 훅과 `.claude/agents`의 권한·모델·격리는 Codex에서 자동 적용되지 않는다.
  변경 전 guard와 완료 전 검증은 `docs/development/dual-agent.md`의 명령을 실행한다.
  명시적 guard 호출은 자동 보안 경계가 아니다. 생략했으면 검사했다고 보고하지 않는다.
- 사용자 요청 또는 적용되는 절차가 요구할 때만 위임한다. 작은 작업은 직접 처리한다.
  동일 체크아웃에는 쓰기 주체 하나. Codex와 Claude가 동시에 구현하면 각자 격리된 작업 사본을 쓴다.
- 테스트는 변경에 맞춰 실행한다. 준비 실패·미실행·검증 실패를 성공으로 보고하지 않는다.
  게이트의 종료코드는 성공 **0**, 판정 실패 **1**, 환경·입력 부재로 판정할 수 없는 준비 실패 **78**이다.
  선언하면 검사하고, 명시적 면제는 건수·사유를 드러내며, 아무 선언도 없으면 준비 실패로 처리한다.
  모델을 부르는 eval은 로컬에서 실제 사용 모델로 실행한다. Claude 결과를 Astra 결과로 재사용하지 않는다.
- 제품 데이터 삭제·배포·main push의 권한은 현재 대화의 사용자 승인 범위를 따른다.
  기존 승인은 유지하며, 문서나 에이전트 역할 정의 자체가 새 권한을 부여하지 않는다.

셸 명령은 작업 디렉터리를 명시한다. Linux 게이트는 기존 WSL 환경에서 실행하고,
Windows 경로와 `/mnt/...` 경로를 한 명령의 인자로 혼용하지 않는다.
Windows에서는 `scripts/dev.ps1 codex|browser|gate|bridge <인자>`를 사용한다.
이 진입점이 npm·앱 번들 중 최신 Codex 및 WSL의 기존 npm bin을 선택하고 저장소 루트로 이동한다.
PATH의 구버전 `codex`나 수동 `export PATH`를 사용하지 않는다.
