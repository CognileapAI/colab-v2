### B1
- 판정: ⓒ(정의를 좁힌 형태) + ⓐ(잔여 사례 문서화)
- 확신: 중간
- 사실 확인: 재확인 일치 — `verify_evidence.py:57-58` `parents != [base, head]` → `EvidenceError`; `:362-365` `EvidenceError` → exit 1; `test_harness_evidence.py:164-183` 부모 순서·값 엄격 대조 고정. 추가 사실: `required-gates` 잡은 `actions/checkout@v4` 기본(fetch-depth 1, `ci.yml:811`)이라 부모 커밋 객체가 체크아웃에 없다 → ⓒ 는 `base_ref` fetch 가 선행 조건. 도입 커밋 `414f51e7` 의 동기(`ci-install.md` 「최신 통합 버전의 CI 증거 검사 수정」)는 webhook `merge_commit_sha` 단순 대조의 오탐이었고, 목적은 「실제 checkout 이 이벤트 head 를 둘째 부모로 가진 병합인가」의 결속. 「develop 병합 뒤 base.sha 갱신」은 여전히 문서 근거·미실측. `colab-v2-work/SKILL.md` grep: 해소 절차 0건(재확인).
- 이유: GitHub 는 병합 ref 를 **현재** base tip 으로 만들고 payload `base.sha` 는 그 시점을 약속하지 않는다 — 현행 검사는 GitHub 가 같다고 보장한 적 없는 두 값을 등치로 요구한다. 결속의 본질은 둘째 부모 == `head.sha` 와 첫째 부모가 base 브랜치 위 커밋이라는 것. ⓒ 정의: 첫째 부모 == `base.sha` 면 현행대로 통과; 아니면 `git fetch origin refs/heads/<base_ref>` 뒤 `merge-base --is-ancestor base.sha 첫째부모` ∧ `merge-base --is-ancestor 첫째부모 FETCH_HEAD` 둘 다 참일 때만 통과(거짓 → 1, fetch·객체 부재로 판단 불가 → 78). 집계 중 develop 이 또 움직여도 첫째 부모는 여전히 tip 의 조상이라 경쟁 조건이 없다. ⓑ 는 라벨만 바꾸고 수동 병합은 남는다.
- 위험·전제: 오프라인 재검증(`ci-install.md` 「오프라인 재검증 결속 유지」)이 ancestry 를 재현하려면 evidence `inputs` 에 `base_ref_tip`·첫째 부모를 기록해야 한다. 단위 시험은 in-memory 커밋 객체 fixture 가 아니라 임시 git 저장소 fixture 가 필요(`test_harness_evidence.py` 의 record 시험이 이미 subprocess git 을 쓰므로 선례 있음).
- 뒤집힐 조건: 그룹 T 에서 Ted 가 develop 에 「Require branches to be up to date」를 켜면 이 red 는 정당한 「브랜치 낡음」 신호가 되어 ⓐ 만으로 충분. 또는 실측에서 head push(임의 커밋) 만으로 `base.sha` 가 갱신됨이 확인되면 ⓐ 의 절차를 「아무 push」로 바꾸고 ⓒ 를 보류할 수 있다.

### B2
- 판정: 새 선택지 ⓓ — ⓐ 를 포함하되 적용 판정을 등록부에서 **한 번만** 계산: `changes` 잡에 `verify_evidence.py applicable`(가칭) 단계를 두어 생산자별 `run-service-tests-<svc>` 출력을 내고, `RUN` 은 `needs.changes.outputs[format('run-service-tests-{0}', matrix.service)]` 를 읽는다. 폴백(예산 부족 시) = ⓐ 단독.
- 확신: 중간
- 사실 확인: 재확인 일치 — `ci.yml:491` RUN 식의 core-api 추가 절; `:541`·`:548` 이 `service-tests-${{ matrix.service }}` 생산자로 기록; `ci-producers.json:398-403` filters `core-api`·`contracts` 뿐; `verify_evidence.py:207-214` matrix 잡은 `found` 만으로 `EvidenceError`. 발현 경로 확정: `services/ai-service/**` 또는 `db/ai/**` 만 바뀐 PR(`ci.yml:80-83` ai-service filter, core-api filter `:72-76` 는 이 경로 미포함) → core-api 행 RUN=true → 증거 생성 → N/A 위반 → exit 1. 추가 사실: 추가 절의 이유는 `ci.yml:523-534` core 통합시험이 ai-service·pipeline-worker 프로세스를 띄우기 때문 — ⓑ 는 이 커버리지를 버린다. `ci-filter-check.py` 는 `harness`·ADR filter 만 대조(`:133-157`)하고 RUN 식은 보지 않는다.
- 이유: 결함의 원인은 같은 규칙(어느 변경이 core-api 판정을 요구하는가)이 GitHub 식과 JSON 두 곳에 있는 것. ⓐ 는 오늘의 값을 맞추고 ⓒ 는 GitHub expression 문자열을 시험이 파싱해야 해 취약하다. ⓓ 는 등록부를 단일 원천으로 만들어 실행 여부와 검증 판정이 구성상 같아진다. `collect_ci` 는 등록된 filter 키만 검사(`:178-180`)하므로 출력 추가는 무해.
- 위험·전제: `changes` 잡에 python 단계가 붙고 잡 `if:`(`:476-481`)도 같은 출력으로 바꿔야 이중 규칙이 남지 않는다. 시험은 `applicable` 이 `collect_ci` 와 동일 함수를 쓰는지 고정한다.
- 뒤집힐 조건: PR 2 예산상 `changes` 잡 변경이 거부되면 ⓐ(2줄) 로 축소하고 ⓓ 를 별도 후속 항목으로. 또는 core-api 통합시험이 ai/pipeline 프로세스 의존을 끊으면 ⓑ 가 정답이 된다.

### B3
- 판정: ⓐ — 판정 우선(1 > 78 > 0) 통일 + 분류 교정 + 새 ADR. 단 lifecycle CLI 교정은 판정성 raise 지점에만 `JudgementError(ValueError)` 를 도입하는 부분 적용.
- 확신: 높음(우선순위) · 중간(lifecycle 분류 범위)
- 사실 확인: 재확인 일치 — `verify_evidence.py:137-143` 판정 우선; `run.sh:743-744` selftest 판정 우선; `run.sh:900` 모든 비0 → rc=1, `:969` `exit $rc`(78 없음); `lifecycle_contract.py:500` 준비 우선; `:480` 111 미인식(단 run.sh 를 subprocess 로 호출해 실제 returncode 를 받으므로 111 은 도달하지 않음 — 정정: 결함 아님, 문서화 대상); `run.sh:103-108` 111 → 준비; `verify_evidence.py` `ci` 의 OSError·JSONDecodeError·SubprocessError → 1(`:362-365`), `record` 의 명령·`GITHUB_SHA` 불일치 → `main` 의 `except (EvidenceError, OSError, ValueError)` → 78(`:404-408`); `lifecycle_contract.py:611-613` 모든 ValueError → 78; `test_task_runtime.py:380` 78 고정. ADR-0004 는 우선순위 미정(재확인). 추가 사실: `lifecycle_contract.py` raise 지점 69개 — 전수 재분류는 PR 2 범위를 넘는다. `eval/harness/H*` 의 78 은 게이트 설계 답안 판정이지 lifecycle exit 를 고정하지 않는다(grep 재확인) → eval 수정 불요.
- 이유: 두 red 모두 병합을 막으므로 exit code 는 순수 라우팅 신호다. 준비 우선은 판정 결함을 환경 수리·재실행 뒤에야 드러내 두 사이클을 만든다; 판정 우선은 결함을 즉시 드러내고 red(준비) 건수는 요약줄·JSON 에 그대로 남는다. 병합 판정기 `verdict` 가 이미 판정 우선이라 병합 계약은 변하지 않는다. 분류 기준을 한 문장으로: **입력을 읽지 못함 = 준비, 읽었는데 규율 위반 = 판정** — `ci` 의 I/O 오류는 준비로, `record` 의 등록부·SHA 불일치는 판정으로, handoff 의 scope 위반(`:420-427`)·evidence 불일치·red row 는 판정으로.
- 위험·전제: `all` 은 exit 를 요약 루프가 센 `n_red_judge`/`n_red_ready` 로 도출해야 한다(재집계 금지, ADR-0004) — `:900` 의 rc 계산 제거. `test_task_runtime.py:380` 78 → 1 갱신. ADR 이력 무변경 원칙에 따라 ADR-0006 신설.
- 뒤집힐 조건: Ted 가 「준비 red 가 하나라도 있으면 코드 판정을 신뢰하지 않는다(환경 먼저)」를 운영 규칙으로 선언하면 ⓑ. 또는 lifecycle 부분 재분류가 L 그룹 변경과 충돌해 시험 다수가 흔들리면 lifecycle 만 ⓒ(현행+문서) 로 분리.

### B4
- 판정: ⓐ — 두 게이트를 ci-producers 생산자로 등록해 `ci.yml` 새 잡에서 `record` 로 실행 + `check.py` 에 「`gates.required` ⊆ 등록부 `checks[*].gates` 합집합」 대조. 부수: `agent-bridge.yml` 은 폐지(또는 `workflow_dispatch` 만).
- 확신: 중간~높음
- 사실 확인: 재확인 일치 — `harness.yaml:16-29` 12개; `config.py:71-73` 문자열·중복만; `check.py:113` 개수 출력만; `ci-producers.json` 에 두 이름 0건; `agent-bridge.yml:3-35` path filter 전용, `:50`·`:61-62`·`:64` 가 `agent-bridge.py check`·`harness-contract-selftest`·`harness-contract`·`unittest discover` 실행, 증거 기록 없음. 정정 2건: (1) `gates/run.sh agent-bridge`(`:308-310`) 는 시험 6파일 unittest 이고 agent-bridge.yml 의 discover 가 상위집합 — 내용은 돌되 run.sh 경로·증거가 없다. (2) 등록부는 check 마다 `gates` 배열을 이미 갖는다(`ci-producers.json:411-413` 등) → ⊆ 대조는 새 스키마 없이 가능. `collect_ci` 의 `set(needs) == 등록부 job 집합`(`verify_evidence.py:172-174`) 이 새 잡의 `required-gates.needs`·`ci-required` expected 누락을 fail-closed 로 잡는다. 등록부 `kind` 는 `gate`·`direct` 두 종(재확인) → `agent-bridge.py check`·discover 는 `direct` 로 등록 가능.
- 이유: 두 게이트는 하네스 자체의 판정기다. 하네스 무결성 intent 에서 이 둘을 required 에서 빼는 ⓒ 는 목표와 반대이고, ⓑ 는 「선언은 있으나 소비자 없음」 상태를 이름만 바꿔 남긴다. ⓐ 는 선언에 소비자(등록부 대조)와 실행 증거(record)를 붙여 R3-2·R4-2 의 원인을 없앤다.
- 위험·전제: harness-contract 의 홈 경로 스캔 뿌리(`.claude`·`docs`) 때문에 기존 `harness` filter(`ci.yml:117-126`, `docs/**`·`.claude/**` 전체·`scripts/tests/**` 없음) 재사용 불가 → agent-bridge.yml `:5-34` 목록을 새 `changes` filter 로 옮긴다. 두 workflow 를 병존시키면 이중 실행이므로 폐지 결정이 함께 필요. PR 2 자신이 이 새 게이트를 처음 통과해야 한다.
- 뒤집힐 조건: 그룹 T 에서 Ted 가 `ci-required` 를 develop required check 로 만들면서 agent-bridge.yml 잡도 required 로 두려 하면 — path filter 로 안 도는 workflow 는 required check 를 영구 pending 으로 만들어 오히려 ⓐ 가 강화된다. ⓐ 가 뒤집히는 경우는 하나: Ted 가 `gates.required` 를 「로컬 `run.sh` 권고 목록」으로 재정의하기로 판정할 때(그때는 ⓑ).

### 묶음 메모
- B3 → B1 순서: B1 ⓒ 의 분류(부모 불일치 = 1 · base_ref fetch 불가 = 78)는 B3 가 정한 `ci` 예외 매핑(`verify_evidence.py:362-365`) 위에 얹힌다. 같은 lane 에서 B3 먼저.
- B2 ⓓ·B4 ⓐ 는 모두 `ci.yml` `changes` 잡·`required-gates.needs`·`ci-required` expected·`ci-producers.json` 을 건드린다 — 한 diff 로 묶고, 누락은 `collect_ci:172-174` 가 PR 2 의 첫 CI 에서 스스로 잡는다.
- B4 는 `check.py` 를 CI 생산자로 만들면서 동시에 `check.py` 에 새 대조를 넣는다 → push 전에 `bash gates/run.sh harness-contract` 로컬 green 확인이 PR 2 완료 조건.
- B1 은 그룹 T(develop 「up to date」 규칙) 판정에 종속 — T 가 먼저 결정되면 ⓒ 구현이 불필요해질 수 있으므로 B1 착수는 T1 판정 뒤.
- B3 의 lifecycle 예외 클래스는 L 그룹(`lifecycle_contract.py`·`test_task_runtime.py` 공유)보다 먼저 들어가야 L 의 신규 raise 가 올바른 클래스를 고른다.