> spec: [R-DEVELOP-PRODUCT](../specs/R-DEVELOP-PRODUCT.md)
# develop·product 전환 Implementation Plan

> **For agentic workers:** 태스크별 격리와 `lane-worker`, 또는 `executing-plans`로 직접 실행한다. 같은 체크아웃의 작성자는 한 명이다.

**Goal:** 사람의 develop → product PR 병합으로 운영 배포하고, 첫 회차에만 dev와 동일한 계정·비밀번호·자료로 운영을 전면 초기화한다.
**Architecture:** 기존 배포·reseed 명령을 재사용하고 PR 판정 진입점과 영속 최초 실행 기록을 추가한다. 브랜치 전환은 검사·보호 설정과 함께 수행하며, 파괴 단계는 환경 파일·dev 완주·첫 PR 증거가 갖춰진 뒤 실행한다.
**Tech Stack:** GitHub Actions·Git, Python 3.11+, bash, 기존 Docker·PostgreSQL·S3·agent-browser.
**Spec:** `dev-package/prd/specs/R-DEVELOP-PRODUCT.md`.

## Global Constraints
- 승인된 사용자 결정은 intent가 정본. spec의 기술 권고는 계획 검토에서 결정한다.
- `product`는 브랜치 이름, `prod`는 기존 운영 환경 이름. 일괄 치환 금지.
- 제품 계약·화면·마이그레이션 신규 설계 없음. 플랫폼·AI 체인과 연구실 경계를 유지한다.
- 초기화는 첫 배포 PR 1회. 실패 시 점검 유지, 사람이 재개 결정. 기존 dev reset 차단을 운영 우회에 쓰지 않는다.
- 비밀번호는 dev와 동일한 외부 입력을 사용하고 값·추측 가능한 해시를 문서·로그·커밋에 넣지 않는다.
- 모든 셸은 저장소 루트를 cwd로 지정. 편집 전 guard, 변경별 RED→GREEN, 종료코드 0/1/78과 세 계수를 보존한다.
- 커밋·원격 변경·운영 접촉은 현재 대화의 승인 범위 안에서만 수행한다. 검사를 위해 임의 커밋하지 않는다.
- Slack·이메일 전송 권한은 이번 요청에 없다. 기존 배포 실행기의 알림 부작용은 명시적 무전송 경로로 분리하고 테스트한다.

## 현재 상태와 의존
- [x] intent 승인: 2026-09-15, 원문 `ㅇㅇ`.
- [x] spec 및 시험 경계 확인. 계획 진행 요청 원문 `계쏙해`.
- [x] 실행 계획 자기 점검 및 advisor 검토 — 2026-09-15 재검토 approve, 계획 인계에 한정.
- [ ] 구현·로컬 시험 진행 중. 환경별 ref·PR 승인 artifact·상위 배포 복구·최초 실행·reset·점검 adapter·dev 프로젝트/미리보기 수정 통합. product-release 74건/product-reseed 87건 통과. 실제 단계 명령 연결·운영자 쓰기 중지 검사·백업 수집/복원 리허설은 운영 연결 의존으로 남는다. 전체 배포 가능 판정은 아직 없다.
- [ ] dev 10단계 단일 완주.
- [x] 운영 설정 파일 수령 및 파일 내부 대상 비교. `transition-inventory.md`에 누락 입력 기록.
- [x] 배포 비활성 브랜치 전환: 기본 develop, 동일 SHA product 및 PR·필수 검사·강제 push/삭제 금지 ruleset 적용. [실측과 남은 연결](../../reports/develop-product/cutover.md). 승격 검사 원격 설치·정상/다른 head 거부 확인, 준비 PR 61 초안. frontend CI 실패와 최초 배포용 artifact 연결은 미완료.
- [ ] 첫 배포 PR 사람 병합·운영 초기화·후속 일반 배포 검증.
- 대장: `DEVELOP-PRODUCT` open. 선행 결함은 `DR-4b`·`DR-4-TOOLING`과 대조하며 기존 항목을 일괄 완료 처리하지 않는다.
- 의존: 작업 1 → 작업 2·3·4 로컬 구현 → 작업 5의 배포 비활성 브랜치 전환 → 작업 4 dev 실환경 완주 → 작업 5 첫 PR 준비 → 작업 6. dev preflight가 실제 origin/develop을 요구하므로 원격 전환 전에 dev 완주를 선행 조건으로 두지 않는다. 병렬 작성은 격리 사본에서만 한다.
- 운영 EC2 조회 권한 해결 및 IP 확인. SSH 호스트 키 확인·실제 운영 연결은 미완료이며, 사용자 요청에 따라 브랜치 전환부터 실행했다.
- 2026-09-15 구현 advisor 판정 reject: 상위 latest 유실 차단, 후속 배포 reseed 제외, 실패 수동 복구, 사전 승인 입력 결속 미달. 계획 승인을 구현 승인으로 재사용하지 않고 네 항목을 보완 중이다.
- 후속 검토에서 위 네 항목과 점검 해제 복구를 보완했다. 마지막 approve-with-changes의 reset → maintenance 잠금 전달 지적은 실제 subprocess 중단 시험 RED→GREEN으로 수정했다. 검토는 로컬 코드에 한정하며 원격 실행 승인으로 재사용하지 않는다. 증거: `dev-package/reports/develop-product/local-validation.md`.

## 작업 1: 전환 정책과 실제 대상 지도
**Files:** Modify `docs/BRANCHING.md`, `CLAUDE.md` §10, `.claude/rules/deploy.md`, `docs/DEPLOY.md`; Create `dev-package/reports/develop-product/transition-inventory.md`.
**Interfaces:** 입력 = 승인 intent·현재 Git/PR/보호 설정. 출력 = 기준 SHA, 열린 PR 목록, 변경할 ref 목록, 실행 호스트 판정, 첫 배포 비활성 상태의 생성 순서.
- [ ] `git status --short`, `git worktree list --porcelain`, `git log -5 --oneline`, `rg -n 'origin/main|refs/heads/main|branches:.*main' .github infra scripts gates`로 실제 의존을 기록한다. 과거 증거 파일은 변경하지 않는다.
- [ ] GitHub 읽기 조회로 기본 브랜치·규칙·열린 PR·허용 병합 방식·사용 가능한 실행 환경을 기록한다. 원격 조회 불가면 로컬 사실과 구분하며 설정 완료로 처리하지 않는다.
- [ ] 정책을 dev=develop, 운영=product로 개정하고 merge commit 승격과 기존 통합 ff 규칙을 구분한다. product 생성 자체는 배포하지 않는다.
- [ ] 전환 순서를 고정한다: 양쪽 ref를 이해하는 검사 준비 → 자동 배포 비활성 유지 → main rename/기본 develop 확인 → product 기준점 생성·보호 → develop에 첫 배포용 차이 준비 → PR 생성. 열려 있는 PR과 로컬 추적 ref를 함께 갱신한다.
- [ ] 배포 호스트는 제공 환경의 접근 가능성과 기존 명령 실행 능력으로 결정한다. 주소·비밀 없이도 사용할 수 있는 입력 스키마는 작업 3에서 만든다.
- [ ] 정본 정책 diff와 승인 intent를 대조한다. 완료 증거 = 전환 지도와 누락 없는 실행 ref 목록. 이 단계는 실제 rename을 실행하지 않는다.

## 작업 2: 환경별 배포 원천과 CI 비교 기준
**Files:** Modify `infra/_lib/ship-gate.sh`, `infra/dev/ship.sh`, `infra/prod/ship.sh`, `infra/dev/tag-release.sh`, `services/core-api/ops/deploy_doctor.py`, `.github/workflows/ci.yml`, `dev-package/tools/dev-reseed/preflight.sh`, `dev-package/tools/dev-reseed/reseed.sh`; Test `infra/dev/tests/ship-gate.sh`, `infra/prod/tests/ship-gate.sh`, `services/core-api/tests/test_deploy_doctor.py`.
**Interfaces:** 입력 `environment=dev|prod`, 고정 `candidate_sha`; 출력 dev는 develop, prod는 product의 조상 검사 결과. 운영 태그는 후보와 일치해야 한다. 과도기 main 허용은 명시적 전환 설정에서만 쓰고 전환 뒤 제거한다.
- [ ] 변경 전 deploy·s3-upload 규칙을 읽는다. 임시 Git 저장소에 develop-only, product-only, unrelated 세 후보를 만들어 dev/prod 반입 결과를 시험한다.
```bash
bash infra/dev/tests/ship-gate.sh
bash infra/prod/tests/ship-gate.sh
```
- [ ] 추가한 실패 픽스처의 RED와 변경 없는 기존 픽스처 결과를 기록한다. 거부는 65, 원격 ref 준비 실패는 78인 기존 반입 규약을 보존한다.
- [ ] 공통 검사에서 환경으로 기준 ref를 선택하고 모든 호출자·태그 검사·doctor 사후 대조를 동일하게 수정한다. PR 비교 기준은 실제 base ref로 fetch한다.
- [ ] 원격 `MAIN_SHA` 기록의 생산자와 doctor 소비자를 함께 전환한다. 새 기록은 source_ref/source_sha/candidate/ancestor를 저장하고 구형 main 기록을 새 product 통과 증거로 재해석하지 않는다. 전환 전 구형 판독과 전환 후 새 형식 필수 조건을 fixture로 구분한다.
- [ ] 위 시험을 GREEN으로 만들고 누락 태그·원격 조회 실패·존재하지 않는 기준 ref·fork PR을 각각 검증한다. 운영 최초 merge commit을 dev에서 시험한 원본 SHA와 혼동하지 않는다.
- [ ] 완료 증거 = 환경/후보별 수용 표, CI base 비교 fixture, doctor 사후 대조 결과. 실제 배포 성공은 주장하지 않는다.

## 작업 3: 사람 병합 검증과 고정 배포 연결
**Files:** Create `.github/workflows/product-deploy.yml`, `scripts/product_release.py`, `scripts/tests/test_product_release.py`, `infra/prod/operator-input.example.json`; Modify `scripts/deploy_release.py`, `scripts/tests/test_deploy_release.py`.
**Interfaces:** 신규 Python 경계 `select_release(event: dict, repository: str, allowed_actor_ids: set[int]) -> dict`; 반환 키 `sha`, `pr_number`, `actor_id`. 거부는 `ValueError`. 신규 CLI `python3 scripts/product_release.py --event EVENT --config CONFIG --check`는 무변경 검증만 수행한다. PR 전 고정하는 값은 head/base SHA와 manifest digest이며 실제 병합 SHA는 병합 후 그 부모·입력과 대조해 영속 결속한다.
- [ ] 아래 계약의 외부 이벤트 시험과 fork·다른 head·봇·미병합·누락 SHA 음성 시험을 먼저 만든다. EVENT는 GitHub 실제 이벤트 형식으로 fixture를 구성한다.
```python
def test_closed_without_merge_is_rejected():
    import pytest
    from scripts.product_release import select_release
    event = {'action': 'closed', 'pull_request': {'merged': False}}
    with pytest.raises(ValueError):
        select_release(event, 'example/repo', {42})
```
- [ ] `python3 -m pytest scripts/tests/test_product_release.py scripts/tests/test_deploy_release.py -q`로 RED를 확인한다.
- [ ] repository/head/base/merged_by/merge_commit_sha를 검증하고 실제 GitHub API 결과와 대조하는 진입점을 구현한다. PR 검증 중에는 운영 자격을 제공하지 않는다. 수동 실행은 새 배포 권한이 아니라 승인된 실패 실행 재개 경로로만 허용한다.
- [ ] manifest는 자신의 파일 hash나 아직 존재하지 않는 merge SHA를 본문에 넣지 않는다. PR 검증 결과가 head/base/manifest digest를 결속하고, 병합 시 merge 부모·파일 내용·필수 검사 결과를 대조한다. 승인 뒤 head/base 변경·manifest 변조는 재검증 없이는 거부한다.
- [ ] `operator-input.example.json`에 비밀 값 대신 파일/secret 참조를 둔다: repository, allowed_actor_ids, environment, 운영 호스트 참조, 정본 manifest, 상태 저장 위치. 누락 입력은 준비 실패 78, 잘못된 입력은 1로 구분한다.
- [ ] GitHub 작업은 product 대상 PR closed/merged에만 진입하고 `cancel-in-progress: false`를 사용한다. 원격 영속 배포 잠금·후보 순서 검사로 runner 간 중복과 역순 실행도 차단한다.
- [ ] 기존 release plan의 후보·산출물 hash 고정과 deploy→verify 흐름을 재사용한다. 기존 알림 전송과 영속 상태 경로는 명시적으로 제어해 임시 runner 작업 디렉터리를 상태 정본으로 쓰지 않는다.
- [ ] 위 pytest를 GREEN으로 만들고 이벤트 재전달·후속 develop 변경·낡은 후보·알림 전송 0건·변경된 산출물 거부를 확인한다. PR origin 검사만 통과하고 실제 설정으로 우회할 수 있는 경우는 실패다.
- [ ] 신규 `product-release-selftest`를 `gates/run.sh`·`gates/README.md`·`.github/workflows/ci.yml`에 등록하고 실행기 `gates/tools/product-release-selftest.sh`를 만든다. 위 정상·거부·재시도·manifest·알림 시나리오를 필수 목록으로 수집해 누락/0건을 거부한다. 준비 실패 78, 시험 실패/누락 1, 전건 통과 0과 공통 요약의 세 계수를 검증한다.
- [ ] 완료 증거 = 대역 배포 호출의 후보 SHA/횟수, 부적격 이벤트의 변경 호출 0건. 실제 GitHub 연결 확인은 작업 5에서 수행한다.

## 작업 4: 최초 운영 초기화 기록과 dev 완주
**Files:** Modify `dev-package/tools/dev-reseed/stages.sh`, `dev-package/tools/dev-reseed/preflight.sh`, 관련 `tests/`; Create `dev-package/tools/product-reseed/reseed.py`, `dev-package/tools/product-reseed/test_reseed.py`, `services/core-api/ops/reset_product_environment.py`, `services/core-api/tests/test_reset_product_environment.py`, `infra/prod/maintenance.py`, `infra/prod/tests/test_maintenance.py`; 기존 `services/core-api/ops/reset_dev_environment.py`의 dev 거부 조건은 유지한다.
**Interfaces:** `decide_initialization(record: dict, manifest_sha: str, resume: bool) -> str`의 결과는 `start|skip|resume`; 금지 상태는 `ValueError`. 상태 `ready|running|failed|succeeded`, run_id·manifest_sha·candidate_sha·완료 단계·부분 단계 결과를 보관한다. 레코드 없음/읽기 오류는 모두 자동 start 금지다.
- [ ] 운영 초기화 상태 fixture를 작성한다. 성공/실패/실행 중 상태에서 일반 재시도에 reset 호출이 없는지 명령 대역으로 확인한다.
```python
def test_failed_run_needs_human_resume():
    import pytest
    from reseed import decide_initialization
    record = {'state': 'failed', 'manifest_sha': 'a' * 64}
    with pytest.raises(ValueError):
        decide_initialization(record, 'a' * 64, resume=False)
```
- [ ] `python3 -m pytest dev-package/tools/product-reseed/test_reseed.py -q`와 `bash gates/run.sh dev-reseed-selftest`로 추가 fixture의 RED를 기록한다.
- [ ] 기존 project_index 앵커·미리보기 최종 상태 대기 결함을 재현하고 수정한다. 원격 transport의 dev 자동 재기동 동작은 운영 점검 해제와 분리한다.
- [ ] 운영 대상·정확한 삭제 목록·입력 hash를 preflight에서 대조한다. 외부 상태 저장소의 배포 잠금 안에서 ready 레코드를 최초 등록하고, 변경 전에 running을 영속 저장한다. 권한·원자적 쓰기·읽기 실패·프로세스 중단을 시험한다.
- [ ] 영속 상태는 운영 실행 호스트의 설정으로 지정한 전용 디렉터리에 보관한다. 모든 runner는 그 호스트에서 하나의 fcntl 잠금을 획득하며 0600 임시 기록의 fsync→원자적 교체→디렉터리 fsync를 사용한다. 첫 ready 등록은 작업 5의 명시 provisioning 명령으로만 수행하며 일반 run에는 생성 권한을 주지 않는다. 기존 배포 상태와 최초 초기화 상태는 다른 파일로 보관한다.
- [ ] `maintenance.py --action enter|status|leave --config CONFIG`를 신규 경계로 둔다. 현재 운영은 CloudFront 기본/API/previews 세 동작이므로 세 경로 모두를 차단하고 적용 완료를 읽기 확인한 뒤 reset을 허용한다. 구성 저장·ETag 경합 거부·실패 시 점검 유지·기존 SPA 함수 복원을 대역 시험한다. 실제 분배 설정은 작업 5의 제공 파일과 대조한다.
- [ ] 점검 중 seed·검증 트래픽은 외부에 공개하지 않는 운영자 전용 접근 경로를 사용한다. 사용자 공개 경로에서 로그인해야 검증할 수 있다는 이유로 점검을 해제하지 않는다. 진입점 노출·우회 공개 여부와 기존 연결/진행 중 작업의 정지를 preflight에서 확인한다.
- [ ] 운영 reset은 플랫폼/AI 스키마와 exact-key S3 계획을 manifest와 대조하고 dev 대상/다른 운영 식별자/보호 prefix를 거부한다. `python3 -m pytest services/core-api/tests/test_reset_product_environment.py infra/prod/tests/test_maintenance.py -q`에서 잘못된 대상의 변경 0건과 점검 미확인 시 reset 0건을 증명한다.
- [ ] 첫 PR manifest와 기록이 일치할 때만 deploy→reset→bootstrap→up→s3→prelude→seed→verify→report를 진행한다. reset 이후 재개는 DB·S3·계정 단계의 실물과 완료 기록을 대조하며 중복 쓰기를 방지한다.
- [ ] 비밀 입력은 존재·권한만 로그에 남긴다. 검증은 계정 구성·로그인, 정본 자료·연결·미리보기 최종 상태와 연구실 경계를 포함한다. 미리보기 0건·값 부재는 성공 금지다.
- [ ] 위 pytest·selftest를 GREEN으로 만들고, 단계별 중단·기록 유실·동시 runner·manifest 변경·성공 뒤 반복 호출을 검증한다.
- [ ] 신규 `product-reseed-selftest`를 `gates/run.sh`·`gates/README.md`·`.github/workflows/ci.yml`에 등록하고 `gates/tools/product-reseed-selftest.sh`에서 상태·운영 reset·점검 fixture를 묶는다. 각 필수 시나리오 실행 여부와 0/1/78·세 계수를 기록한다. `bash gates/run.sh product-release-selftest` 및 `bash gates/run.sh product-reseed-selftest`를 실제 실행한다.
- [ ] dev 전용 스킬을 읽고 승인된 dev 경계에서 실제 단일 10단계 실행을 수행한다. 입력이 없으면 78로 기록하고 로컬 음성 시험을 계속한다. 관련 DR 항목은 실제 해소한 범위만 갱신한다.
- [ ] 완료 증거 = 단일 실행 식별자와 모든 단계 결과, 입력 manifest, 로그인·자료 조회 증거, 미실행·면제 수. 운영 실제 초기화는 아직 수행하지 않는다.

## 작업 5: 환경 연결·전환 리허설·보호 규칙
**Files:** Modify `infra/prod/operator-input.example.json`, `docs/DEPLOY.md`, `docs/BRANCHING.md`; Create `dev-package/reports/develop-product/cutover.md`와 검토용 최초 배포 manifest. 실제 비밀 파일은 Git에 추가하지 않는다.
**Interfaces:** 입력 = 작업 1 지도·작업 2~4 GREEN·사용자 환경 파일. 출력 = 검토 가능한 원격 변경 목록, 첫 PR의 대상/head·base/삭제/재적재 manifest 및 digest, 실행 기록 ready. 실제 merge SHA는 병합 후 결속한다.
- [ ] 환경 파일에서 주소·저장소·DB·접근 방식·정본 위치를 확인한다. 비밀 값을 문서에 옮기지 않고 대상 식별 결과만 기록한다.
- [ ] 권한 조회로 product PR 필수·동일 repo develop 검사 필수·직접/강제 push·삭제·봇 bypass 차단을 준비한다. merge commit 허용과 product 선형 이력 요구의 충돌을 제거한다.
- [ ] 변경 없는 preflight와 원격 도구 리허설로 실제 명령·권한·저장소 도달·백업 자료·점검 유지/해제 방법을 확인한다. 사용자가 제공하지 않은 환경값을 추측해 채우지 않는다.
- [ ] DB 백업만으로 삭제 파일을 복구할 수 있다고 주장하지 않는다. `infra/prod/backup.sh`의 두 DB dump와 동일 중지 구간의 S3 exact-key/version 또는 보존 사본 manifest를 함께 확보하고 읽기/복원 리허설로 대조한다. 준비 실패면 첫 PR을 배포 가능으로 만들지 않는다.
- [ ] advisor go/no-go에 현재 변경 목록·실제 검증·외부 변경 승인 범위를 제출한다. 브랜치 전환과 최초 운영 배포를 별도 판정하며 첫 운영 PR은 dev 완주와 운영 준비 전에는 배포 가능으로 만들지 않는다. 단순 스킬/문서가 원격 실행 권한을 부여한 것으로 취급하지 않는다.
- [ ] 작업 1 순서로 브랜치 rename·기본 분기·product 생성·보호 설정·CI 연결을 실행한다. 생성 이벤트에서 배포 0건을 확인한다. 아직 운영 reset은 실행하지 않는다.
- [ ] 잘못된 head/fork PR·직접 push 경로 거부와 정상 승격 PR의 필수 검사 상태를 GitHub에서 확인한다. 사용자가 직접 병합할 첫 PR에 정확한 삭제/계정/자료 범위와 실패 처리·재개 절차를 적는다.
- [ ] 완료 증거 = 보호 설정 읽기 결과, 첫 PR 링크·head/base·manifest digest, 배포 미실행, dev 완주 근거. 사람이 첫 PR을 병합하기 전 운영 초기화를 시작하지 않는다.

## 작업 6: 최초 운영 배포·재개·후속 일반 배포 검증
**Files:** Create `dev-package/reports/develop-product/first-release.md`; Modify `dev-package/work-items.yaml`, 본 라운드의 상태. 최초 운영 초기화와 후속 검증을 별도 실행 식별자로 기록한다.
**Interfaces:** 입력 = 사람 병합 이벤트와 승인된 manifest. 출력 = 운영 후보 SHA, 최초 실행 succeeded 또는 실패 유지, 실제 로그인·자료 검증 증거.
- [ ] 병합 이벤트·사람 식별·후보·원격 기록을 대조한다. 실행 전 검증된 DB/파일 복구 자료와 삭제 목록을 확인한다.
- [ ] 자동 배포의 단계 기록을 회수하고 실패 시 점검 상태가 유지되는지 확인한다. 실패 재개는 사용자 결정 없이 실행하지 않는다.
- [ ] agent-browser 스킬에 따라 URL·계정·자료·시나리오·기대 결과·대상 SHA를 고정하고 실제 로그인·조회·미리보기·새로고침을 검증한다. 정본 적재 과정의 저장 사용자 여정 증거도 연결한다.
- [ ] 운영 doctor 결과·배포 태그·실제 이미지 SHA를 대조한다. 모든 검증 성공 후 점검 해제를 확인한다.
- [ ] 동일 이벤트 재전달의 무변경 결과와 이후 사람이 병합한 일반 배포의 reset 0건을 확인한다. 후속 PR이 없으면 이 수용 조건을 미실행으로 남기고 전체 완료를 선언하지 않는다.
- [ ] 완료 전 verification-before-completion으로 intent 항목별 미달·초과를 기록하고, 실제 게이트의 세 계수·로그를 확인한 뒤 대장을 갱신한다. 현재 대화에서 승인하지 않은 외부 메시지는 보내지 않는다.

## 계획 검증과 인계
- [x] spec 모든 요구를 작업 1~6에 매핑: 정책/생성=1·5, ref/CI=2, 사람 PR/고정 버전=3·5, 최초 기록/실패/동일 계정=4·6, 사용자 여정/후속 배포=6.
- [x] 300행 이하, 상대경로, 정의된 인터페이스 일치, 정책·우려 절 존재, 대장 source 링크를 검사했다.
- [x] `COLAB_GATE_REPORT_DIR=dev-package/reports/develop-product/planning bash gates/run.sh work-item-consistency` 실행. 첫 실행 exit 1: 새 항목의 CLAUDE stage 표지 누락. 표지 추가 후 exit 0, green 1 / red(판정) 0 / red(준비) 0. 기존 파싱 대상 밖 10건은 미검사이며 면제·성공으로 계산하지 않는다.
- [x] advisor 최초 approve-with-changes의 merge SHA 사전 고정 문제와 신규 게이트 등록 누락을 수정했다. 재검토 approve. 운영 설정·실제 보호 규칙·점검·복구 증거는 실행 단계 의존 조건으로 남는다. 검토 승인은 제품 배포 승인이 아니다.
- 실행 방식 기본은 직렬 1개 작성자다. 작업별 격리 lane-worker 방식 또는 이 세션 직접 실행 중 선택 가능하며, 실행 시 기존 사용자 승인 범위를 유지한다.
