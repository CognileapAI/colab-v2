# CoLAB v2 — 실제 개발 워크플로 프로파일 (2026-08-22 ~ 2026-09-06)

조사일 2026-09-06. 읽기 전용. 레포 파일 무수정.
근거 = `30 CoLAB-v2` 레포 실물 · git history · `40 COLAB-기획` 구조 · `~/.claude/projects/-mnt-f-00-Project-00-CoLAB/memory/*.md` 33건 · claude-mem timeline(가용, 표본 1회).
`[추론]` 표시가 없는 문장은 실측·문서 인용.

---

## A. 실제로 돌아간 파이프라인 (as practiced)

### A-1. 개발 회차(round) 1바퀴

| # | 단계 | 주체 | 산출물 | 통과 조건(게이트) |
|---|---|---|---|---|
| 1 | 기획 입력 수령 | Ted(수령) / 기획자 이태헌·조성진(작성) | `40 COLAB-기획/10_적용전/<날짜>_<제목>_<작성자>.<ext>` (원본 무수정) | 없음 |
| 2 | 적용현황 조사 · PRD 화 | 서브에이전트(격리) | `40 .../20_검토/<날짜>_<주제>/`, `dev-package/prd/PRD-*.md` | 없음 |
| 3 | 미결 판정 | Ted (ELI5 HTML 브리프를 보고 ⓐ/ⓑ 선택) | `결정서_Ted_<날짜>.md` + 메모리 `ted-decisions-*` | 「재개봉 금지」 선언 |
| 4 | 라운드 파일 작성 | 메인 세션 | `dev-package/prd/rounds/R-A-1-db.md` 등 (242~298행, 자족적) | ≤300행 · 부트스트랩 단일 파일 |
| 5 | 대장 등재(착수) | 레인 에이전트 첫 커밋 | `dev-package/work-items.yaml` 에 WU 블록 | `work-item-consistency` |
| 6 | 구현 | 레인 에이전트 (`Agent isolation:"worktree"`) | 코드 + 시험 | 해당 서비스 **단독 게이트** 연속 green |
| 7 | 수용 검토 | advisor(모델 Fable) | 검토 의견 | 게이트 ② |
| 8 | 병합 | **오케스트레이터만** | `integration/<x>` → main ff | 병합 직전 전수 `gates/run.sh all -j 4` 50/0/0 |
| 9 | 결정 번호 발급 | 오케스트레이터(직렬) | `PLAN-SoT.md §9` 〈N〉 | max+1 재실측 (`prd/tools/max-decision.sh`) |
| 10 | 인계 갱신 | 세션 종료 시 | `03-HANDOFF.md` 5줄 이내 | CLAUDE.md §6 |
| 11 | Ted 보고 | 메인 세션 | ELI5 자립형 HTML (루트) | 「기능이 어떻게 됐나」, 과정 나열 금지 |

주: 계약(contract) 파괴 변경은 라운드 파일 ㉰ 대로 **Ted 서명(동결 해제 N차 승인)** 없이 main 에 오르지 못한다. 19차 승인 실례 = 메모리 `ted-decisions-260906-ra-merge`.

### A-2. 배포 경로 (2026-09-05 전환 후)

- 종전: staging(`colab_v2_staging_*` docker 스택) 배포 = 완료 정의.
- 전환(〈334〉~〈336〉, PR #1 `feature/rtf400_deploy` 박홍진 통짜 병합): **AWS dev** 가 유일한 판정처.
- 현재 경로: 로컬 `build.sh`(arm64 크로스빌드, WSL2 는 QEMU 별도 등록 필요) → `ship.sh`(tar+scp) → EC2 `up.sh` → 로컬 `deploy_web.py`(S3 web) → `deploy_doctor` **14/14**.
- 브랜치 전략 = **main 한 줄 + `prod-YYYYMMDD` 태그**. 환경별 브랜치 불채택. 실측: 태그 0개(아직 prod 미개시), 원격 브랜치 5개.
- staging 은 내리지 않고 **Ted 개인 리허설 무대**로 존치(판정·기록 없음).
- 완료 정의 개정: 「staging green」 → 「**dev green + doctor 14/14**」.

### A-3. 게이트 시스템

- `gates/run.sh` 단일 진입점(33.6KB), 게이트 이름 53개(selftest 포함), README 47행 표, claude-mem 관측 = **직렬 8 + 병렬 42**.
- 각 게이트에 `-selftest`(실패 픽스처) 가 짝. 설계 목적 = **green-by-skip 방지**(v1 CI 가 DB 없이 돌아 RLS 를 skip-green 했던 실패).
- CI(`.github/workflows/ci.yml`) 잡 8개: changes(paths-filter) · contract-gates · frontend-gates · boundary-gates · schema-gates · dormant-tests · service-tests · planning-gates · gate-selftest. **CI 는 `./gates/run.sh <name>` 을 그대로 호출** — 로컬과 같은 판정부.
- 전수 실측: `-j 1` = 41분, `-j 4` = 21분, 같은 트리 판정 무변(Ted 판정으로 `-j 4` 채택).

---

## B. 아티팩트 지도

| 아티팩트 | 목적 | 쓰는 이 | 읽는 이 | 크기(실측) | 갱신 빈도 | 관측된 실패 양상 |
|---|---|---|---|---|---|---|
| `dev-package/03-HANDOFF.md` | 진행 상태 인계 | 세션 종료 시 각 세션 | 다음 세션 첫 읽기 | **172KB**(메모리 기록 시점 607KB → archive 다이어트 후) | 세션마다 | 블로커 표 4행이 동시에 실물과 어긋남. 상태 기호가 「최근 측정값」이 아니라 「마지막 기입값」 |
| `dev-package/work-items.yaml` | 항목 상태 **정본(SSOT)** | 레인 첫 커밋 | `work-item-consistency` 게이트 | **572KB**, 항목 140개 | 착수·완료마다 | 병렬 레인이 `items:` 끝에 각자 블록 덧붙임 → ff 불가·리베이스 충돌, 「양쪽 다 취함」 시 YAML 엇갈림 |
| `dev-package/PLAN-SoT.md §9` | 결정 원장 〈N〉 | 오케스트레이터만 | 인용 전용 | **1.30MB**, 고유 번호 **298개** | 병합마다 | 동시 세션 3개가 같은 번호 발급 → 308→309→310 2회 재번호, 참조 12자리 동반 이동 |
| `dev-package/WORK-UNITS.md` | 완료 정의·의존 그래프 | 반영본 | 세션 시작 | 147KB | 회차마다 | 대장과 갈리면 대장이 이김(규칙으로 해소) |
| `dev-package/prd/rounds/*.md` | **세션 부트스트랩 단일 파일** | 메인 세션 | 개발 세션 | 242~298행 ×5 | 라운드마다 | (신설 2026-09-05, 실패 미관측) |
| `dev-package/sessions/*.md` | 회차 작업지시서·조사 산출 | 서브에이전트 | 다음 에이전트 | **226 파일**, 폴더 4.5MB | 세션마다 | 미커밋 상태로 지목하면 워크트리에서 안 보임 — 하루 4회 발생 |
| `dev-package/reports/<회차>/` | 레인 보고서·게이트 로그 | 레인 | advisor·Ted | 20 항목 | 회차마다 | — |
| `40 COLAB-기획/` | 기획 정본 생애주기 | 기획자 | 개발 | 00원본 52 / 10적용전 4 / 20검토 27 / **30적용완료 0** / 90레퍼런스 5 / 99archive 34 | 기획 수령 시 | `30_적용완료` 가 **0건** — 적용 완료 환류가 실제로는 안 돎. 폴더 재편(9/5) 이 `planning-freshness` 게이트를 red 로 만듦 |
| ELI5/브리프 HTML (레포 밖 루트) | Ted 판정·완료 보고 | 서브에이전트 | Ted | 8개, 12KB~100KB | 판정·회차마다 | — |
| 메모리 `*.md` 33건 | 규칙·상태 축적 | 세션 | 다음 세션 | 64KB | 교정 발생 시 | 프로젝트 상태(type: project)와 행동 규칙(type: feedback)이 한 폴더에 섞임 |

메모리 33건 분류 실측: **feedback/교정 = 16건**, **project 상태 = 15건**, 프로세스 결정 = 2건(`orchestrator-delegation-policy`, `model-roles-fable-advisor`).

---

## C. 세션 케이던스와 형태

- **커밋/일** (2026-08-22~09-06, 15일, 총 803): 14·87·31·33·45·48·32·50·67·38·19·60·**136**·32·92·19. 일 평균 53.5, 중앙값 42.
- 무휴. 15일 연속 커밋. 새벽 커밋 다수(창 8-a/8-b 는 00:40~04:30 진행) — **[추론]** 하루 2~3 세션, 심야 세션이 배포·병합을 담당.
- 세션 시작: CLAUDE.md §1 이 5문서 순차 읽기를 지시 → 이 관행이 2.4MB 부트스트랩을 낳음 → 2026-09-05 `prd/rounds/<파일>.md` **하나만** 읽는 방식으로 교체.
- 세션 종료: CLAUDE.md §6 5항목(HANDOFF §1 상태 · 상단 3값 · §9 결정 · §4 블로커 · 다음 진입조건). 다이어트 후 **HANDOFF 갱신 5줄 이내**.
- 병렬 레인 수: 실측 최대 **7 레인**(2026-09-03 코드리뷰 회차, `merge: 레인 worktree-agent-*` 6~7건 연속), 통상 **3 레인**(R-A FE), 2026-09-05 Ted 지시 이후 원칙은 **직렬 1개**(진짜 독립일 때만 병렬).
- 커밋 메시지 규약(실측): 한국어 · `<유형> — <내용> (WU-XX)` · 유형 어휘 = `대장 등재` / `DB 계층 R-A-1` / `서버 계층 R-A-2` / `FE 계층 R-A-3` / `실측 R-A-4` / `병합` / `통합` / `merge:`. 결정 번호는 `〈343〉~〈346〉` 형태로 본문에.
- 병합 방식: **ff 선호**(레인→통합→main ff). merge 커밋은 통합 브랜치 조립과 충돌 해소에만 사용(2026-08-01 이후 merge 커밋 40건).

---

## D. 프릭션 로그 (반복 문제)

| # | 문제 | 근거 | 빈도 | 현행 우회책 |
|---|---|---|---|---|
| D1 | 워크트리에 `node_modules`·`services/*/.venv` 미승계 → 전수 red(준비) 10 | `worktree-gate-env-setup` | 새 워크트리마다 | 손으로 `npm ci` + `uv venv` ×4 (+ core-api `uv pip install -e .`) |
| D2 | 테스트 env 미source → red(준비) 6 | `gates-need-test-env-sourced` | 전수마다 | `set -a; . ~/.colab-v2-test.env; set +a` 관용구 암기 |
| D3 | 결정 번호 〈N〉 충돌 | `decision-number-issue-at-merge` | 2회 재번호(308→310), 동시 세션 3개 | 예약 금지 + 병합 직전 max+1 재실측 스크립트 |
| D4 | `work-items.yaml` 끝 덧붙임 리베이스 충돌 | `parallel-lanes-ledger-append-conflict` | 병렬 레인 2개 이상마다 | 「HEAD 판본 + 레인 블록」 수동 규칙 + `yaml.safe_load` id 유일성 |
| D5 | NTFS `core.filemode=false` → 새 `.sh` 100644 → Actions exit 126 | `ntfs-exec-bit-update-index` | 스크립트 20개 중 12개 잠복 | `git update-index --chmod=+x` 수동 |
| D6 | 서브에이전트 워크트리 핀 상속 → 형제 워크트리 Bash 전부 거부 | `subagent-worktree-isolation-pin` | 레인 5개 동시 정지 1회 | `Agent(isolation:"worktree")` + 지시문 첫 줄 `git merge --ff-only` |
| D7 | 부트스트랩 문서 2.4MB → 세션 느려짐·컨텍스트 요약·규칙 유실 | `session-bootstrap-diet` | 상시 | 라운드 파일 1개 + 대형 문서는 grep 한 줄 |
| D8 | 병합 뒤 불필요 전수 재실행 (10~41분) | `no-redundant-gate-rerun-after-merge` | Ted 가 직접 중단 | 트리 해시 동일성으로 「갈음」 |
| D9 | 조사 산출물 미커밋 → 다음 에이전트가 못 읽음 | `commit-survey-artifacts-immediately` | **하루 4회**(2026-08-29) | 회수 즉시 add/commit/push |
| D10 | 「main 과 동일한 오류」를 수용 근거로 씀 | `same-as-main-is-not-ok` | main 이 10.5시간 배포 불가 상태로 방치 | 「어느 검사에 걸리는지」를 레인 지시문 필수항으로 |
| D11 | green-by-skip (검사 대상 0건인데 통과) | SKILL §4, 실례 5곳 중 3곳 미지시 발견 | 반복 | selftest 픽스처 + 「형제 찾기」 |
| D12 | 게이트 red 의 「준비/판정」 오독 | `gates-need-test-env-sourced` | 레인 1개·20분 낭비 | 결과 읽을 때 수동 분류 |
| D13 | 행 번호 지시 → 전부 +7 밀림 | SKILL §1 | 1회 | 앵커 문자열로만 지시 |
| D14 | 높은 병렬도에서 게이트 거짓 red (일회용 DB 준비시간) | SKILL §1-b ⑸ | 병렬도 6에서 2건 | 낮은 병렬도 재현 후 병합 근거로 |
| D15 | 미병합 브랜치 위의 값을 사실로 지시문에 기재 | SKILL §1-b ⑷ | 1회(에이전트 정지) | main 존재 확인 후 기재 |
| D16 | 기획 폴더 이동이 `planning-freshness` 게이트 red 유발 | `gates-need-test-env-sourced` 증보 | 1회 | 게이트 상수 수정 |
| D17 | 워크트리 병합 후 미정리 | `worktree-cleanup-after-merge` | Ted 가 직접 지적 | 3단(remove·branch -d·push --delete) 수동 |
| D18 | 재기동 시 이미지 재빌드 누락 → 헬스 200 인데 온톨로지 소실 | SKILL §6 | 1회 | `RESTART.md` ㉲ |
| D19 | Ted 보고에 내부 코드·창 번호 노출 | `deploy-window-term-explain`, `explain-before-asking-judgment` | 최소 3회 지적 | 기능명으로 번역, ELI5 HTML |
| D20 | 메인 세션이 대형 문서 본문을 읽어 지시 누락 | `no-file-edits-in-main-session` | Ted 직접 지적 | 메인은 한 줄 수치 검증까지만 |
| D21 | API 529 과부하로 레인 중단 | `model-roles-fable-advisor` 보강 | 반복 | Sonnet 강등 금지, Fable 재시도·대기 |
| D22 | 기획 문서 vs 코드 드리프트 | `planning-folder-lifecycle`, rev2 판정-1 | 상시 | 「목업에 없다 ≠ 걷어라」, 코드→기획 정렬이 기본 |

---

## E. 자동화 vs 수동

### 자동(코드로 존재)
- `gates/run.sh` 53 게이트 + selftest 짝 · `-j` 병렬 · 직렬 8 지정.
- GitHub Actions 8잡 (paths-filter 로 변경 경로만).
- `work-item-consistency` — 대장 ↔ 산문 불일치·번호 중복을 기계 판정.
- `planning-freshness` / `check-package-freshness.py` — 기획 정본 신선도.
- `prd/tools/max-decision.sh` — 〈N〉 최대값 1줄 측정.
- `deploy_doctor` 14항목 · `build.sh`/`ship.sh`/`up.sh`/`deploy_web.py`.
- `purge_datasets.py` (고정 id + `--yes-delete` + rowcount 불일치 시 ROLLBACK).

### 수동(매번 사람 또는 메인 세션이 손으로)
| 수동 작업 | 후보 |
|---|---|
| 워크트리 env 구축(npm ci + venv ×4 + `-e .`) | **훅/스크립트** (`worktree-setup.sh`, PostWorktreeCreate 훅) |
| 테스트 env `set -a; . ...; set +a` | **훅/래퍼** (`gates/run.sh` 가 자동 source) |
| 게이트 red 의 준비/판정 분류 | **run.sh 출력 규격화** (red 사유 코드) |
| 〈N〉 재실측·전 파일 일괄 재번호 | **스크립트** (`renumber-decisions.sh`) |
| work-items.yaml 충돌 해소 | **merge driver** (`.gitattributes` custom merge) |
| `.sh` exec bit 부여 | **pre-commit 훅** |
| 워크트리·브랜치 정리 3단 | **Stop 훅 / 스킬** |
| 조사 산출물 즉시 커밋 | **SubagentStop 훅** |
| 병합·번호 발급·충돌 해소(오케스트레이터 전담) | 유지 — 의도된 직렬화 |
| ELI5 HTML 브리프 제작 | 이미 스킬(`explain-visually`·`eli5`), 위임 규율만 수동 |
| Ted 판정 수집 → 메모리 `ted-decisions-*` 기록 | **스킬**(판정 캡처 → 라운드 파일 §1 자동 반영) |
| 라운드 파일 작성 | **스킬**(PRD + 대장 → 라운드 파일 생성기) |

---

## F. 이상적 환경 요건 (A~E 근거 귀속)

**Must-have**
1. 워크트리 생성 즉시 게이트 실행환경(node_modules·venv 4벌·`-e .`)을 세우는 훅. ← D1
2. 게이트 실행 시 테스트 env 자동 주입, 미주입 시 「준비 red」로 명시 계수. ← D2·D12
3. 게이트 결과를 `green / red(판정) / red(준비) / 미실행` 4상태로 기계 출력. ← D12·SKILL §3
4. `work-items.yaml` 전용 merge driver (블록 단위 append + id 유일성 검증). ← D4
5. 결정 번호 발급을 **병합 시점 원자적 연산**으로 (재실측 + 전 파일 재번호 자동). ← D3
6. 부트스트랩은 라운드 파일 1개(≤300행)로 강제, 대형 문서 전체 읽기 차단. ← D7
7. 레인 스폰은 `isolation:"worktree"` 고정, 지시문 템플릿에 ff-merge 첫 줄·앵커 지시·「어긋나면 정지」·「완료 정의 미작성」 규칙 내장. ← D6·D13·D15·SKILL §1
8. 병합·번호·충돌 해소는 오케스트레이터 전용 권한으로 잠금(레인 불가). ← SKILL §1-b
9. advisor 3게이트를 파이프라인 단계로 고정(계획 전/수용 전/비가역 직전), 프롬프트 3필수항 템플릿. ← SKILL §2
10. 새 `.sh` exec bit 자동 부여 pre-commit. ← D5
11. 서브에이전트 산출물 자동 커밋(SubagentStop). ← D9
12. 전수 재실행 억제: 트리 해시 동일성 판정을 도구가 선언. ← D8
13. 「main 과 동일한 오류」 보고를 수용 검토에서 자동 플래그. ← D10
14. Ted 보고 경로 = ELI5 자립형 HTML 고정, 내부 코드·창 번호 자동 검출·차단. ← D19·B(ELI5 8건)
15. 배포 판정은 `deploy_doctor` 14/14 단일 기준, staging 은 기록 없는 리허설로 분리 유지. ← A-2

**Nice-to-have**
16. 라운드 파일 생성기(PRD §+대장 → rounds/*.md 초안). ← E
17. 판정 캡처 스킬(Ted 결정 → 메모리 + 라운드 파일 §1 「재개봉 금지」 자동 반영). ← A-1 #3
18. 워크트리·브랜치 정리 자동화(Stop 훅). ← D17
19. 게이트 병렬도 정책 자동화(단독=narrow, 병합 전=`all -j 4`). ← A-3·D14
20. `30_적용완료` 환류 자동화 — 적용 완료 WU 를 기획 폴더로 이동. ← B(0건)
21. API 529 시 Fable 재시도/대기 큐(Sonnet 강등 금지). ← D21

---

## G. 기존 자산 판정

| 자산 | 판정 | 근거 |
|---|---|---|
| `.claude/skills/colab-v2-work/SKILL.md` (169행) | **유지 + 분할** | 규율 밀도가 높고 각 항목에 실사건이 붙어 실효. 다만 §1-b(병행 집행)·§3(게이트)·§6(운영 접촉)은 **훅·스크립트로 내려야** 할 것을 문장으로 붙들고 있다. F1~F5·F10·F11 이 구현되면 해당 문단은 축약. |
| `advisor` 에이전트(Fable) | **유지** | 3게이트가 실제로 오류를 잡음(8-a 어드바이저 정정 커밋 `87d5b87` 실존). 스폰을 파이프라인 단계로 고정만 필요. |
| 프로젝트 `CLAUDE.md` §1(세션 시작 5문서) | **교체** | 2.4MB 부트스트랩의 직접 원인(D7). 라운드 파일 단일 부트스트랩으로 개정 필요 — **현재 문서와 실제 관행이 불일치**. |
| `CLAUDE.md` §2·§3(도메인·불변 규칙) | 유지 | 게이트가 기계 강제. 문서와 게이트가 1:1. |
| `CLAUDE.md` §4·§5·§6·§7 | 유지 | 세션 종료 규약·금지 목록은 계속 인용됨. §6 은 「5줄 이내」 다이어트 반영 필요. |
| `CLAUDE.md` 배포 절(§업로드·§배포) | **개정** | staging 기준 완료 정의가 dev+doctor 14/14 로 바뀜(A-2). |
| 메모리 — 규칙형 16건(`writing-style-korean-outline`·`explain-before-asking-judgment`·`no-metaphor-technical-terms`·`batch-questions-*`·`status-map-deliverable`·`final-report-eli5-*`·`no-file-edits-in-main-session`·`ux-first-*`·`convenience-features-deferred`·`same-as-main-*`·`narrow-gates-*`·`no-redundant-gate-*`·`worktree-cleanup-*`·`deploy-window-term-*`·`orchestrator-delegation-policy`·`model-roles-fable-advisor`) | **프로젝트 규칙 파일로 이관** | 세션마다 재주입돼야 하는 행동 규칙. 메모리 검색에 의존하면 유실 위험. 보고 규율 6건은 하나로 통합 가능. |
| 메모리 — 환경/버그형 6건(`worktree-gate-env-setup`·`gates-need-test-env-sourced`·`ntfs-exec-bit-*`·`subagent-worktree-isolation-pin`·`parallel-lanes-ledger-*`·`decision-number-issue-*`) | **코드로 대체 후 폐기** | 전부 F1~F5·F10 의 자동화로 소멸 가능한 「사람이 기억해야 하는 우회책」. |
| 메모리 — 상태형 11건(`ted-decisions-*` 4·`window-8a-done-*`·`aws-handoff-status-*`·`planner-authors`·`planning-folder-lifecycle`·`session-bootstrap-diet`·`same-as-main` 등) | **HANDOFF/원장으로 이관** | 프로젝트 상태는 이미 SSOT 가 있음(work-items.yaml·§9). 메모리에 중복 보관 중 — 갈릴 위험. |
| ELI5 HTML 브리프 관행(루트 8건) | **유지 + 위치 이동** | Ted 명시 요청(2026-08-27), 판정 비용을 실제로 낮춤. 다만 레포 밖 루트에 날짜 파일로 흩어짐 — 회차 폴더 귀속 권장. |
| `dev-package/prd/rounds/*.md` | **유지·확대** | 부트스트랩 다이어트의 유일한 성공 수단. R-B 4분할 예정. |
| `dev-package/sessions/*.md` 226건(4.5MB) | **정리** | 세션 지시서·조사 산출이 한 폴더에 누적. 회차별 하위 폴더 + archive 필요. |
| `40 COLAB-기획/30_적용완료/` | **활성화 또는 폐지** | 0건. 설계된 환류가 실제로는 안 돎(B). |
| `gates/` 전체 | **유지(핵심 자산)** | 이 레포 규율의 실물 근거. selftest 짝·fail-closed 설계는 대체 불가. |

---

## 부록 — 조사 한계

- claude-mem MCP 는 **가용**. 표본 1회(#9633~9636, 2026-09-06 00:20)만 조회 — 회차 유형 통계는 미산출.
- `git shortlog -sn` 이 **빈 출력**(작성자 메타 미설정 추정) — 커밋 주체 분리는 커밋 문면으로만 추정.
- `PLAN-SoT.md`·`03-HANDOFF.md`·`work-items.yaml` 본문은 열지 않음(크기 규율 준수). 구조·계수만 실측.
- `docs/superpowers` 없음. 레포 내 `.claude/settings*.json`·훅 **0건**(node_modules 내 타 패키지 것 제외).
