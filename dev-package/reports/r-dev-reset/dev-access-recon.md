# R-DEV-RESET — dev 접근·배포 경로 정찰 (읽기 전용)

- 작성 2026-09-13 · 역할 `researcher` · 작업 id `fe31748ef1e14b3d94bb200dd3095514`
- 성격 = **읽기 전용.** 레포 파일 수정 0 · 원격 상태 변경 0 · 배포 0 · DB 쓰기 0. 접속 문자열·키·비밀번호 미기재.
- 원격 실측 = `ssh` 읽기 명령 1회(`cat`·`ls`·`md5sum`·`sudo ls`).

## 1. 배포 경로 — `main` 커밋이 dev 에 올라가는 절차

- 경로 = **로컬 WSL → EC2 (`ssh`/`scp`)**. GitHub Actions 배포 0 · SSM Session Manager 0(`session-manager-plugin` 미설치이고 절차에도 없다).
- 진입점 정본 = 공통 실행기. 근거 `infra/dev/README.md:55-57`
  > 완료 배포는 [공통 실행기](../releases/README.md)의 release 계획으로 실행한다.
  > 아래 반입·기동 명령은 계획의 자식 단계 또는 최초 부트스트랩 절차다. 각각의 성공을 전체 배포 완료로 세지 않는다.
- 실행 명령 = `python3 scripts/deploy_release.py run --plan <release.json>` (`infra/releases/README.md:3`). 사전 검토는 `--check`.
- 자식 단계 축자 (`infra/dev/README.md:60-72`)
  > ```bash
  > # 개발 기계
  > infra/dev/build.sh                # 5 이미지 buildx linux/arm64 → 아키텍처 실측 → dist/colab-v2-dev-<sha>.tar
  > COLAB_DEV_SSH=ec2-user@<EIP> COLAB_DEV_KEY_FILE=~/.config/colab-platform/dev-key.pem infra/dev/ship.sh
  > # EC2 (첫 배포만: 부트스트랩 → 이후 매번 up.sh)
  > /opt/colab-v2/up.sh                # migrate-platform → migrate-ai → up -d → 4 단위 healthy 대기(fail-closed) → 헬스 본문
  > ```
  > (⋯ 생략분 = 첫 배포 전용 `db-bootstrap.sh prep/roles/extensions`·`app-grants`·`verify` 줄과 프런트 `deploy_release.py` 줄)
- 반입 게이트 = `infra/dev/ship.sh:20-33` — `git fetch origin main` 후 `merge-base --is-ancestor`. 비조상 **exit 65** · `origin` 조회 실패 **exit 78** · `COLAB_SHIP_ALLOW_NONMAIN=1` 선언 시 `ancestor=bypass`.
- `up.sh` 는 EC2 위에서 돈다 — `dev.env`(0600)를 `--env-file` 로 읽고 4 단위 healthy 를 fail-closed 로 기다린다(`infra/dev/up.sh:8-38`).
- `db-bootstrap.sh` 는 staging 스크립트의 원격 래퍼 · 단계 `prep`·`roles`·`extensions`·`app-grants`·`verify`(`infra/dev/db-bootstrap.sh:1-12`).

### ⟨선행 단계 · `〈361〉`-㉯⟩ 축자 (`infra/dev/README.md:92-104`)

> ⭑ **⟨선행 단계 · 실측 2026-09-06 · `〈361〉`-㉯⟩ `deploy_doctor` 전에 EC2 `/opt/colab-repo` 를 배포 sha 로 맞춘다.**
> `deploy_doctor` 는 `--repo` 로 받은 트리에서 **`db/<체인>/versions`(스키마 head 대조)** 와 **`gates/tools`** 를 읽는다 —
> 레포가 낡으면 ⑥⑦ 이 **옛 head 를 정답으로 삼아** 조용히 틀린다.
> ⛔ **EC2 에 `git` 이 없다**(AL2023 최소 설치). 그래서 개발 기계에서 tar 로 민다:
>
> ```bash
> tar czf /tmp/repo.tgz --exclude=__pycache__ --exclude=.venv db gates services/core-api/ops infra
> scp -i "$COLAB_DEV_KEY_FILE" /tmp/repo.tgz "$COLAB_DEV_SSH":/tmp/
> ssh -i "$COLAB_DEV_KEY_FILE" "$COLAB_DEV_SSH" 'sudo tar xzf /tmp/repo.tgz -C /opt/colab-repo --overwrite'
> ```
>
> ⚠ **`--overwrite` 와 `sudo` 가 둘 다 필요하다** — 기존 파일 일부가 root 소유다.
> **판정 = 개발 기계와 EC2 의 `services/core-api/ops/deploy_doctor.py` md5 가 같다.**

## 2. 이 기계의 접근 자격 — 실측

| 항목 | 실측 | 관측 |
|---|---|---|
| `~/.ssh/config` | colab·dev 항목 **없다**(`Host github.com` 1건) | `grep -i` |
| SSH 개인키 | 운영자 키 디렉터리에 `.pem` 2건 존재(0600) | `ls -la`(값 미출력) |
| 운영자 env 파일 | 레포 밖 1건(8줄) · 키 이름 `COLAB_DEV_SSH`·`COLAB_DEV_KEY_FILE`·`COLAB_DEV_SECRETS_DIR`·`COLAB_DEV_ENV`·`COLAB_DEV_WEB_URL` | `grep -o`(값 미출력) |
| **SSH 실접속** | **성공** — `BatchMode=yes` 무암호 접속 · 원격 `sudo` 무암호(`sudo ls /etc/colab` 동작) | 읽기 명령 1회 |
| `~/.aws/config` 프로파일 | `colab-dev` · `colab-hsw` · `colab-notifications-deployer` · `credentials` 에 `colab-dev` | `grep '^\['` |
| `aws sts get-caller-identity --profile colab-dev` | **성공**(IAM 사용자 = dev S3 업로더) | 1회 실행 |
| 기본 프로파일 | 자격 없음(exit 253) | 같은 명령 |
| EC2 API 권한 | **없다** — `DescribeInstances`·`DescribeAddresses` 가 `UnauthorizedOperation` | 1회 실행 |
| `which` | `ssh` ✓ · `scp` ✓ · `aws` ✓ · **`session-manager-plugin` 없음**(절차상 불요) | `which` |
| `~/.colab-v2-dev.env` | **부재**. dev 값의 자리는 레포 밖 운영자 env 파일이다. `~/.colab-v2-test.env`·`~/.colab-v2-staging.env` 는 존재 | `test -f` |
| `$COLAB_DEV_SECRETS_DIR` 로컬 사본 | 디렉터리 존재 · 소유자 URL 파일 이름 `platform-owner-db.url`·`ai-owner-db.url` 포함 | `test -d`·`ls`(이름만) |
| EC2 `/etc/colab` | 존재 — `platform-owner-db.url`·`ai-owner-db.url`·`core-database.url`·`pipeline-db.url`·`account-admin-database.url`·`master.url`·`subjects.json`·`credentials.json` 등 | 원격 `sudo ls`(이름만) |

## 3. 초기화 도구가 도는 자리

- 정본 = `dev-package/prd/rounds/R-DEV-RESET.md §5 WU-R2` — **레인 작업이 아니다.** 오케스트레이터가 절차를 밟고 Ted 가 GO 를 준다.
- 실행 위치 = **EC2 호스트.** 다섯 명령을 그 순서로 내고 각 명령이 비영 종료하면 그 자리에서 멈춘다(같은 절).
- URL 은 `$COLAB_DEV_SECRETS_DIR` 의 **파일 경로**로만 받고 argv·로그에 싣지 않는다(같은 절 「dev 식별자 정의」 ⓑ).
- 선례 = `ops/purge_datasets.py` 를 core-api 이미지 안에서 실행. 축자 `dev-package/reports/window-8b/orphan-purge-plan.md:93-102`
  > ```
  > docker run --rm --network host --user 0 \
  >   -v /etc/colab/platform-owner-db.url:/s/owner.url:ro \
  >   -v /tmp/purge_datasets.py:/tmp/purge.py:ro \
  >   colab-v2/core-api:dev python /tmp/purge.py \
  >     --db-url-file /s/owner.url --lab 0000000000000000000000000A \
  >     --id 01M1FSEWYJVAV20VPMPT3EDDW9 --id 01M1C0F19DFGA80AM4HR63S1ND \
  >     --id 01M1H2DYX821ZR33SVVVQGJZ9R --id 01M1H4XH0XMQ7CNJ8256WP16SF \
  >     --id 01M1GR9N0DSK2AVRWJEBM5D0SD
  > ```
  - 비밀값 0 — 마운트는 경로이고 인자는 파일 경로와 ULID 뿐이다. 도구 파일은 `/tmp` 로 올려 읽기 전용 마운트한다.
- `deploy_doctor` 실행 선례 = EC2 `sudo bash /opt/colab-repo/infra/ops/probes/deploy-verification.sh`(`dev-package/reports/r-login-backoffice/task5/deploy-3-verify.md` §2 · `--allow-skip` 미사용 · 재시도 0 · 부분 실행 합산 0). 로컬에 같은 파일 존재(`infra/ops/probes/deploy-verification.sh`).
- 원격 실측 — `/opt/colab-repo/services/core-api/ops/` 에 `purge_datasets.py`·`deploy_doctor.py`·`app-role.sql`·`account-admin-role.sql`·`provision-account.sql`·`provision-service-operator.sql` 존재. **`reset_dev_environment.py` 는 로컬·원격 모두 부재**(WU-R1a 미착수).

## 4. 현재 dev 상태

| 항목 | 값 | 관측 |
|---|---|---|
| `CURRENT_SHA` | `6ff0eecd2cba` | 원격 `cat`(오늘 실측) |
| `MAIN_SHA` | `main=6ff0eecd2cba candidate=6ff0eecd2cba ancestor=yes` | 원격 `cat`(오늘 실측) |
| `/opt/colab-repo` platform versions 최신 | **`0030_merge_operator_audit_and_backoffice.py`**(`0031` 부재) | 원격 `ls`(오늘 실측) |
| `deploy_doctor.py` md5 개발 기계 ↔ EC2 | **일치** `a2d5651512ff786f0a71eeb36e51ed9c` | 양쪽 `md5sum`(오늘 실측) |
| `deploy_doctor --env dev` 최근 결과 | **✓ 14 · ✗ 1 · ─ 0 · exit 1**(한 번의 실행) | `dev-package/reports/r-login-backoffice/task5/deploy-3-verify.md` §2 |
| 유일한 ✗ | **⑥ 스키마 head (platform)** | 같은 보고 |
| 살아 있는 DB platform head | `0031_search_evidence` · ai head `0007_merge_vocab_and_category` | 같은 보고 §1 |
| 공개 주소 | `https://d31zgpff2091oh.cloudfront.net` | `docs/DEPLOY.md:7`·`:142` |

- **⑥ ✗ 원인** = DB·실행 코드가 아니라 **대조용 EC2 레포 트리가 낡았다.** 살아 있는 DB `0031` ↔ `/opt/colab-repo` 최신 `0030`. 해소는 §1 tar-sync 3줄이다. 오늘 원격 실측에서 `0030` 이 그대로다.
- `deploy_doctor.py` md5 는 이미 일치한다 — `[추론]` md5 일치는 ⑥ green 을 뜻하지 않는다. ⑥ 의 판정 입력은 `db/<체인>/versions` 목록이고 그 동기화가 남아 있다.
- 미결 1건 = `core_api`·`viz_render` 컨테이너가 태그 없는 이미지 ID 로 동작(같은 보고 §6-2). 걸리는 검사 없음.

## 5. WU-R2 착수 차단 요인

| # | 차단 | 해소 | 담당 |
|---|---|---|---|
| 1 | `services/core-api/ops/reset_dev_environment.py` 부재 | WU-R1a 구현 ＋ 가드 시험 7건 ＋ 로컬 증명 | `lane-worker` |
| 2 | 원장 행·`deploy.md` 예외·대장 등재 미완 | WU-R1b | `lane-worker` |
| 3 | 진입조건 ㄹ — `deploy_doctor` ⑥ ✗ | §1 tar-sync 3줄 실행 후 `deploy_doctor` 1회 재실행 | 오케스트레이터(이 기계에서 실행 가능) |
| 4 | Ted 명시 GO 미기록 | `PLAN-SoT §9` 행에 승인 기록. **승인은 1회 소진** | **Ted 본인** |
| 5 | WU-R1a·R1b 의 `main` 병합 ＋ dev 배포 미완 | 병합 후 배포 1회 | 오케스트레이터 |

- **이 기계에서 해소되는 것** = 1·2·3·5. SSH·원격 `sudo`·S3 자격이 모두 동작한다.
- **Ted 본인이 해야 하는 것은 4 하나다.** `! ssh …` 형식의 사람 로그인은 필요 없다 — 무암호 `BatchMode` 접속이 실측으로 성립한다.
- ⚠ EC2 API 권한이 없어 탄력적 IP·인스턴스 상태를 `aws` 로 확인할 수 없다. 주소 정본은 운영자 env 의 `COLAB_DEV_SSH` 와 콘솔의 「탄력적 IP 주소」 칸이다(`infra/dev/README.md:123`).

## 6. 후속 항목 (이 작업에서 고치지 않는다)

1. `ship.sh` 가 `/opt/colab-repo` 트리를 같은 회차에 밀지 않는다 — ⑥ 가 반복 ✗ 가 되는 구조적 원인. 고칠 자리 = `ship.sh` 단계화.
2. 실행 중 컨테이너 이미지 ID ↔ `colab-v2/<서비스>:dev-<sha>` 대조 항목이 `deploy_doctor` 에 없다.
3. 배포 잠금이 호스트에 없다 — 동시 배포가 실제로 3차 배포를 중단시켰다(`dev-package/reports/r-login-backoffice/task5/deploy-3.md` §3).
