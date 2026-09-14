# dev(AWS) 배포 정찰 — `main` `e9ca26b1` (읽기 전용)

- 작성 2026-09-14 09:10 KST · 작업 사본 `.claude/worktrees/lth-review-260913` · 브랜치 `integration/r-lth-1`
- 성격 = 읽기 전용 조사. 배포·태그·push·재기동·EC2 쓰기·DB 조회 0. EC2 접촉 = 읽기 전용 ssh 1회(파일 `cat`·`stat`·`docker ps`·`ls`·`md5sum`·`df`·로그 끝 1행).
- 비밀값 미기재. 환경 파일은 변수 이름만 적었다.
- 승인 근거(오케스트레이터 전달) = Ted 「dev zjalt gkrh qovh go」(= 「dev 커밋하고 배포해」). 이 문서는 그 승인을 해석하지 않는다.

## 1. 결론

- **배포 가능(차단 0).** 조건 4 — 아래 §7 순서 그대로 · 실행 주체 1개 · 착수 직전 동시 배포 재확인 · `deploy_doctor` 한 번의 실행 15/15.
- 배포 형태 = **DV 전체 배포**(이미지 ＋ `up.sh` ＋ 프런트). `services/core-api/src` 3파일 변경이 있어 프런트 단독 배포로 줄일 수 없다.
- 신규 마이그레이션 = **0건**(platform·ai 둘 다). `up.sh` 의 마이그레이션 단계는 올릴 판이 없다 `[추론]`.
- 태그 이름 = **`dev-20260914-1`**(로컬·원격 모두 `dev-20260914-*` 0건).

## 2. 현재 dev 상태 (실측)

| 항목 | 값 | 관측 |
|---|---|---|
| `CURRENT_SHA` | `81784897ec74` | EC2 `cat /opt/colab-v2/CURRENT_SHA` |
| `MAIN_SHA` | `main=81784897ec74 candidate=81784897ec74 ancestor=yes` | EC2 `cat` |
| `dev.env` | `ec2-user:ec2-user` 0600 · mtime 2026-09-13 12:24 UTC · `COLAB_IMAGE_TAG=dev-81784897ec74` | EC2 `stat`·`grep` |
| 컨테이너 | 4종 전부 `:dev-81784897ec74` 태그 표기 · healthy(core/worker/ai 11h · viz 9h) | EC2 `docker ps` |
| `/opt/colab-repo` 최신 판 | platform `0031_search_evidence.py` · ai `0007_merge_topic_vocab_and_rc7_category.py` | EC2 `ls` |
| EC2 `deploy_doctor.py` md5 | `a2d5651512ff786f0a71eeb36e51ed9c` | EC2 `md5sum` |
| 백업 마지막 행 | `2026-09-13T19:00:08Z backup[dev] GREEN` (관측 시각 00:10 UTC 기준 약 5시간 전) | `/var/log/colab-backup.log` |
| 디스크 | 20G 중 15G 사용 · **5.0G 여유 · 76%** | EC2 `df -h /` |
| 마지막 dev 태그 | `dev-20260913-3` → `81784897ec74` — **원격에도 있다** | `git tag --list` · `git ls-remote --tags origin` |

- 태그 뒤 무태그 이미지 배포 = **0건**. 근거 = `CURRENT_SHA`·`COLAB_IMAGE_TAG`·컨테이너 태그가 모두 `81784897ec74`.
- 같은 sha 위에서 dev 초기화(스키마 재생성 ＋ 계정 관리 롤 SQL)가 뒤이어 실행됨 — 커밋 `8d5ae5e4`·`de0855f7`·`873b29ef`. 살아 있는 DB 의 alembic head 는 이번에 조회하지 않았다 `[미확인]`.
- 마지막 완주 배포 기록 = `dev-package/sessions/DR-2-deploy-2026-09-13.md` §15~§17(계획 id `dr2-dev-81784897ec74-3` · 전 단계 exit 0 · `deploy_doctor` 축자 `항목 15 — ✓ 15 · ✗ 0 · ─ 0`).

## 3. 변경 delta — `81784897..e9ca26b1`

- 커밋 **40건** · 파일 **91건**(+7,509 / −211). 계수 기준 = `git log --oneline` 행수 · `git diff --stat` 요약줄.
- `origin/main` = `e9ca26b1` = 작업 사본 HEAD. 로컬 `main` ref 는 `7446eb7d`(낡음) — `ship.sh` 는 `origin/main` 을 fetch 해 비교하므로 영향 없음(`infra/dev/ship.sh:22`).

| 경로 | 변경 | 배포 영향 |
|---|---|---|
| `db/platform/versions/` · `db/ai/` | **0** | 마이그레이션 없음 |
| `infra/` | **0** | 절차·compose·`up.sh` 무변 |
| `services/core-api/src` | 3파일 +115/−14 — `app/routes/catalog.py` · `app/routes/members.py` · `domains/d1_identity.py` | core-api 이미지 교체 필요 |
| `services/core-api/ops/` | `account-admin-role.sql` 1파일(+8/−2) — `ALTER ROLE` 을 비밀번호 한 줄 ＋ 어긋날 때만 속성 한 줄로 분리(RDS 마스터 실행 가능화) | §5 참조 |
| `services/core-api/ops/deploy_doctor.py` | **0** | EC2 md5 `a2d5…ed9c` 유지 기대 |
| `services/pipeline-worker` · `viz-render` · `ai-service` | **0** | `build.sh` 가 5종을 모두 다시 만든다 |
| `contracts/seams/fe-core.yaml` | +11 — 구성원 행에 선택 열쇠 `accountStatus`(`active`·`inactive`) 추가 | 추가형 · 파괴 아님 `[추론]` |
| `frontend/src/generated/fe-core.ts` | +11 (위 계약의 생성물) | 프런트 번들 교체 필요 |
| `frontend/src` 기타 | auth·catalog·common·detail·lab·lineage·members·project·upload·routes·shell | 프런트 번들 교체 필요 |
| 그 밖 | `dev-package/**`(intent·prd·reports·sessions·tools/dev-seed) · `frontend/test` · `services/core-api/tests` | 배포 산출물 밖 |

## 4. 마이그레이션

- 신규 0건 확인 — `git diff --stat 81784897 e9ca26b1 -- db/` 출력 0행.
- `up.sh` 는 `migrate-platform → migrate-ai → up -d` 순서(`infra/dev/README.md` 「올리기」 블록). 새 판이 없어 head 무변 `[추론]`.
- 적용 전 백업 단계는 계획에 그대로 둔다(DR-2 계획 `04-backup.sh`). 선례 = `deploy-3.md` §4 — `0031` 이 백업 없이 올라간 사건.

## 5. `account-admin-role.sql` 재적용 여부

- 배포 절차 안에 이 SQL 을 적용하는 단계 **없음** — `infra/dev/up.sh` 에 `account-admin-role`·`grants` 문자열 0건(grep).
- 이번 변경은 권한 내용이 아니라 **실행 가능성**(RDS 마스터가 `NOSUPERUSER` 를 적은 `ALTER ROLE` 을 거절) 수정이다. 파일 주석 축자 —
  > 비밀번호는 항상, 나머지 속성은 실제로 어긋났을 때만.
  근거 `services/core-api/ops/account-admin-role.sql` 변경 hunk.
- 수정본은 dev 초기화 회차에서 실행됨 — 커밋 제목 `de0855f7` 「계정 관리자 롤 SQL 을 RDS 마스터에서 실행 가능하게 고친다」 → `873b29ef` 「dev 초기화 실행을 끝까지 기록한다(… SQL 선행 4단계)」. 적용 결과 실측값은 이번에 대조하지 않았다 `[미확인]`.
- 권고 = 이번 배포에 넣지 않는다. `deploy_doctor` ⑨(앱 롤)가 red 일 때만 별도 판단.

## 6. 동시 배포 확인

| 확인 | 결과 | 관측 |
|---|---|---|
| 이 호스트 배포 프로세스 | **0**(`deploy`·`ssm send-command`·`terraform`·`ansible`·`ship.sh`·`build.sh`·`buildx`·EC2 ssh 패턴) | `ps -eo args` |
| EC2 잠금 파일(최근 240분) | **0**(`/opt/colab-v2` · `/tmp`) | `sudo find -iname '*lock*' -mmin -240` |
| EC2 배포 프로세스 | **0**(`up.sh`·`docker load`·`backup.sh`·`docker compose`·`deploy_doctor`) | `pgrep -af` |
| 배포 기록 `31 CoLAB-v2` | 최신 `r-login-260913-dv-6ff0eecd2cba`(09-13 03:29) | `.git/deploy-releases` `ls -lt` |
| 배포 기록 `32 CoLAB-v2` | 최신 `dr2-dev-81784897ec74-3`(09-13 21:25) | 같음 |
| 배포 기록 `30 CoLAB-v2` | 최신 `st-e1989fca…`(09-13 14:08 · staging) | 같음 |
| 2026-09-14 배포 기록 | **0**(세 clone) | 같음 |

- deploy-3 충돌 원인 = `scripts/deploy_release.py` 잠금이 **clone 별 git common dir** 에 선다(`scripts/deploy_release.py:62-68` `deployment.lock` · `deploy-3.md` §3·§8-1). 다른 clone 의 배포를 막지 못한다.
- **현재도 막는 장치 없음** — `infra/dev/ship.sh` 에 `lock`·`flock` 0건(grep). EC2 쪽 잠금 없음. 방지 수단은 실행 주체 1개 운영뿐.
- 착수 직전 재확인 명령(읽기 전용) — EC2 `pgrep -af "up.sh|docker load|backup.sh|docker compose"` ＋ 세 clone `deploy-releases` 최신 항목 시각.

## 7. 자격·도구 준비

| 항목 | 상태 | 비고 |
|---|---|---|
| `aws` CLI | `aws-cli/2.36.40` | |
| 기본 자격(프로파일 미지정) | **없음** | `sts get-caller-identity` 실패 |
| 프로파일 `colab-dev` | **자격 있음** | `sts get-caller-identity --profile colab-dev` 성공(계정 id 미기재) |
| 운영자 env `~/.config/colab-platform/dev-operator.env` | 변수 이름 = `AWS_PROFILE` · `COLAB_DEV_SSH` · `COLAB_DEV_KEY_FILE` · `COLAB_DEV_SECRETS_DIR` · `COLAB_DEV_ENV` · `COLAB_DEV_WEB_URL` | `AWS_PROFILE` 값이 `colab-dev` 인지 grep 정규식 불일치(따옴표·`export` 표기 추정) `[미확인]` |
| 로컬 `~/.config/colab-platform/dev.env` | 변수 이름 = `AWS_ACCESS_KEY_ID` · `AWS_SECRET_ACCESS_KEY` · `COLAB_S3_BUCKET` · `COLAB_S3_REGION` · `COLAB_S3_ORIGIN` | 로컬 도구 전용 키(`docs/DEPLOY.md` §4 IAM 사용자 행). **EC2 로 옮기지 않는다** |
| SSH | **접속 성공** — `~/.config/colab-platform/dev-key.pem` · `ec2-user@<탄력적 IP>` | 읽기 전용 probe 1회 |
| Docker · buildx | `29.3.0` · `v0.31.1` | |
| QEMU arm64 등록(WSL) | `[미확인]` — DR-2 1차가 `build.sh` 에서 실패한 원인 | 확인 `ls /proc/sys/fs/binfmt_misc/qemu-aarch64` · 없으면 `docker run --privileged --rm tonistiigi/binfmt --install arm64`(`infra/dev/README.md` 진단표) |
| Node 22.12 이상 | `[미확인]` | `npm run build` 단계 |
| 프런트 업로드 자격 주입 | DR-2 3차 방식 = 같은 하위 셸에서 `aws configure export-credentials --profile "$AWS_PROFILE" --format env` 를 `eval` | `DR-2-deploy-2026-09-13.md` §14. 선례 실패 = `deploy-3.md` §3 `KeyError: 'SessionToken'` |

## 8. 실행 명령 순서

기계적 절차 정본 = `infra/dev/README.md`(「올리기」·「확인」). 실행 진입점 = `infra/releases/README.md`. 계획 구조 선례 = `dev-package/sessions/DR-2-runbook.md` §1. 계획 단계 스크립트 고정본은 레포에 없다 — 회차마다 새로 작성(`DR-2-runbook.md` §1-1 축자 「레포에 고정본이 없다」).

### 하지 않는다 (`.claude/rules/deploy.md` 「깨뜨리면 안 되는 것」)

- 저장 모드 변경 금지 — dev 는 `s3`(`compose.yml` 리터럴). `local` 로 바꾸지 않는다(규칙 7).
- EC2 env(`/opt/colab-v2/dev.env`·`/etc/colab/*`)에 AWS 액세스 키를 넣지 않는다 — 인스턴스 프로파일 IMDSv2(규칙 2).
- CloudFront 동작·원본 요청 정책(`AllViewer`)·캐시 정책을 바꾸지 않는다 · `index.html` 긴 캐시 금지(규칙 3·4·5).
- NAT 게이트웨이를 만들지 않는다(규칙 1).
- env 파일은 통째로만 바꾼다 — DB 와 저장 백엔드를 따로 바꾸지 않는다(규칙 8). 이번 배포는 `COLAB_IMAGE_TAG` 한 값 교체만 한다(선례 `03-image-tag.sh`).
- **`services/core-api/ops/reset_dev_environment.py`·`services/core-api/ops/purge_datasets.py` 를 실행하지 않는다** — 둘 다 `PLAN-SoT §9` 행 ＋ Ted 명시 GO 필요(규칙 11). 이번 배포 승인은 그 GO 가 아니다.
- `COLAB_SHIP_ALLOW_NONMAIN=1` 우회 선언을 쓰지 않는다. `deploy_web.py` 를 실행기 밖 단독으로 올리지 않는다(`infra/releases/README.md` 「기존 진입점」). `--allow-skip` 을 쓰지 않는다.
- 태그 push 는 이 순서에 넣지 않는다 — `tag-release.sh` 는 로컬 태그와 명령 출력까지(`infra/dev/tag-release.sh` 머리말 「push 하지 않는다」). 원격 반영은 오케스트레이터 판단(`CLAUDE.md` §10).

### 순서

1. **기준 확인** — 작업 사본 HEAD = `origin/main` = `e9ca26b1`. 추적 파일 변경 0. `git merge-base --is-ancestor e9ca26b1 origin/main` exit 0.
2. **동시 배포 재확인** — §6 끝의 읽기 전용 명령. 하나라도 진행 중이면 멈춘다.
3. **도구 준비** — QEMU arm64 등록 확인 · Node 버전 확인(§7 `[미확인]` 2건).
4. **계획 작성** — `dist/release-lth-review-260913-dv/release.json`(gitignore · 비밀값 0) · id 예 `lth-review-dev-e9ca26b1`(동일 id 재사용 금지). 단계는 DR-2 3차 실측(`DR-2-deploy-2026-09-13.md` §15)과 같은 배열:
   - `deploy[0]` `infra/dev/build.sh` — 5 이미지 `linux/arm64` · `dist/colab-v2-dev-<sha>.tar` · `dist/colab-v2-dev.sha` 기록(`infra/dev/build.sh:40`)
   - `deploy[1]` `COLAB_DEV_SSH=… COLAB_DEV_KEY_FILE=… infra/dev/ship.sh` — 반입 게이트(비조상 exit 65 · origin 조회 실패 exit 78) · `CURRENT_SHA`·`MAIN_SHA` 기록
   - `deploy[2]` EC2 `dev.env` `COLAB_IMAGE_TAG=dev-e9ca26b1xxxx`(12자리) 확인·교체
   - `deploy[3]` EC2 `sudo /opt/colab-v2/backup.sh`(적용 전 백업)
   - `deploy[4]` EC2 `/opt/colab-v2/up.sh` — 마이그레이션(0건) → `up -d` → 4 단위 healthy 대기 · 헬스 본문 `storageMode`·`sourceMode`·`previewSink` = `s3`
   - `deploy[5]` **배포 레포 트리 동기화**(§9 참조) — `git archive origin/main -- db gates services/core-api/ops infra | gzip` → `scp` → `ssh 'sudo tar xzf /tmp/repo.tgz -C /opt/colab-repo --overwrite'`
   - `deploy[6]` `npm ci`(frontend) · `deploy[7]` `npm run build` · `deploy[8]` `services/core-api/ops/deploy_web.py`(자격은 §7 마지막 행 방식)
   - `verify` — ⓐ 개발 기계 ↔ EC2 `deploy_doctor.py` md5 일치 ⓑ `deploy_doctor` 1회(§9 명령) ⓒ `MAIN_SHA` = `main=<12> candidate=<12> ancestor=yes` ⓓ `CURRENT_SHA` = 새 sha ⓔ `/` 200 ⓕ `/api/v1/me` 401 ⓖ `index.html` md5 개발 기계 빌드 ↔ 공개 주소 일치
5. `python3 scripts/deploy_release.py run --plan <절대경로>/release.json --check` → exit 0(축자 「배포 계획 확인 완료 — 실행·전송 없음」).
6. `python3 scripts/deploy_release.py run --plan <절대경로>/release.json` → exit 0 또는 20. **1·75·78 이면 그 자리에서 멈춘다 — 같은 id 로 재실행하지 않는다**(`infra/releases/README.md` 「상태·중복·실패」). 20 은 `--retry-notification` 만.
7. `python3 scripts/deploy_release.py status <id>` → `deployment: verified`.
8. `deploy_doctor` 결과가 §9 기준을 충족하면 `infra/dev/tag-release.sh dev` → 로컬 태그 `dev-20260914-1` → 출력된 push 명령은 실행하지 않고 오케스트레이터에 넘긴다.
9. 기록 — 세션 노트·원장 반영은 오케스트레이터 지시 범위.

## 9. 검증 기준

- 트리 동기화 선행 — `infra/dev/README.md` 앵커 「⟨선행 단계 · 실측 2026-09-06 · `〈361〉`-㉯⟩ `deploy_doctor` 전에 EC2 `/opt/colab-repo` 를 배포 sha 로 맞춘다」. 판정 = EC2 ↔ 개발 기계 `services/core-api/ops/deploy_doctor.py` md5 일치.
  - 이번 delta 는 `db/` 0 · `deploy_doctor.py` 0 이라 동기화 누락 시에도 ⑥⑦ 판정값은 같다 `[추론]`. 절차상 단계는 생략하지 않는다(ops SQL·`gates` 등 트리 최신화).
- `deploy_doctor` 명령(`DR-2-runbook.md` §1-4 · 진입점 `infra/ops/probes/deploy-verification.sh` — 인자는 스크립트에 고정: `--env dev` · `--endpoint https://d31zgpff2091oh.cloudfront.net` · owner DB URL 파일 2 · app/worker/viz/ai base 4 · 버킷 2 · `--state-dir /state`):
  ```bash
  ssh -o BatchMode=yes -i "$COLAB_DEV_KEY_FILE" "$COLAB_DEV_SSH" 'sudo bash /opt/colab-repo/infra/ops/probes/deploy-verification.sh'
  ```
- green = exit 0 ＋ 요약줄 **`항목 15 — ✓ 15 · ✗ 0 · ─ 0`**.
- 판정 규칙 — `deploy_doctor` 판정은 `─ 0` 이 나온 **한 번의 실행**만 근거. 부분 실행 둘을 합쳐 green 이라 하지 않는다.
  근거 `.claude/rules/deploy.md` 「고치기 전에 돌릴 것」 —
  > **부분 실행 둘을 합쳐 green 이라 하지 않는다** — `─ 0` 이 나온 한 번의 결과만 근거다.
- ⑮ 판정 입력 = `/opt/colab-v2/CURRENT_SHA`·`MAIN_SHA`(`docs/DEPLOY.md` §6-1 표). `verify` 에 doctor 를 넣으면 그 1회가 판정 실행이다 — 뒤에 따로 다시 돌려 결과를 섞지 않는다.
- 추가 대조 — 컨테이너 4종이 `:dev-<새 sha>` 태그 표기로 도는지 `docker ps`(deploy-3 에서 태그 없는 이미지 ID 로 돈 사례 · `deploy-3-verify.md` §6-2 · doctor 가 보지 않는 항목).

## 10. 위험과 되돌리기

### 위험

| # | 위험 | 근거 | 대응 |
|---|---|---|---|
| R1 | 다른 clone·세션의 동시 배포 — 잠금이 clone 단위라 막지 못함 | `deploy-3.md` §3·§8-1 · `ship.sh` lock 0건 | §8 순서 2 재확인 · 실행 주체 1개 |
| R2 | EC2 디스크 5.0G 여유(76%) — 전일 6.4G(69%)에서 감소. 이미지 tar 약 285M ＋ 5 이미지 추가 | EC2 `df` · `deploy-3-verify.md` §1 · `DR-2-deploy` §15 | `build`·`ship` 전에 `df` 확인. 정리(`docker image prune` 등)는 파괴적 조작이라 이 문서에서 권고하지 않고 판단 항목으로 넘긴다 |
| R3 | 계획 단계 스크립트 고정본 부재 — 매 회차 손작성 | `DR-2-runbook.md` §1-1 | DR-2 3차 단계 배열 그대로 · `--check` |
| R4 | `build.sh` QEMU 미등록 실패 | `DR-2-deploy` 1차 | §7 확인 |
| R5 | `deploy_web.py` 자격 주입 실패(`SessionToken`) | `deploy-3.md` §3 · `DR-2-deploy` §14 | `export-credentials` 하위 셸 주입 |
| R6 | `dev.env` 소유자 `root:root` 표류 → `03-image-tag` `Permission denied` | `deploy-3.md` §8-2 | 현재 `ec2-user:ec2-user` 0600 확인됨 |

### 되돌리기 (`docs/DEPLOY.md` §6-2 · `infra/dev/README.md` 「되돌리기」)

- 백엔드 = EC2 `dev.env` 의 `COLAB_IMAGE_TAG=dev-81784897ec74` 로 교체 → `/opt/colab-v2/up.sh`. 직전 이미지는 현재 실행 중이라 EC2 에 존재.
- 마이그레이션은 되돌리지 않는다 — 이번 신규 0건이라 해당 없음.
- ⚠ 롤백 뒤 ⑮ 는 마지막 `ship.sh` 반입 sha(새 sha) 판정을 유지 — `CURRENT_SHA`·`MAIN_SHA` 미갱신(`docs/DEPLOY.md` §6-1 경고).
- 프런트 되돌리기 절차는 두 문서에 명시 없음 `[미확인]` — 선택지 = `81784897` 트리 빌드를 실행기 계획 안에서 `deploy_web.py` 로 재업로드.

## 11. `[미확인]` 목록

1. 살아 있는 DB alembic head(platform·ai) — 이번에 DB 조회하지 않음.
2. `account-admin-role.sql` 수정본의 dev 적용 결과값.
3. 운영자 env `AWS_PROFILE` 값 표기(`colab-dev` 여부) — 프로파일 `colab-dev` 자체는 자격 있음.
4. 개발 기계 QEMU arm64 등록 상태 · Node 버전.
5. 최종 트리 `e9ca26b1` 전수 게이트 green 여부 — Ted 판정 「배포 보류」 조건 축자 「전수 green ＋ `main` ff 뒤 Ted 허락」(`dev-package/reports/issues/2026-09-13-ted-decisions.md:67`). 최근 커밋 제목은 `frontend-test` 연속 2회 green 만 언급.
6. `tag-release.sh` 의 날짜 기준 시간대(KST/UTC) — 09:00 KST 이전 실행이면 이름이 갈릴 수 있다.
7. 프런트 되돌리기 절차.
8. DR-2 계획 단계 스크립트 사본의 잔존 위치(「작업 임시 폴더」 · 레포 밖).
9. `DR-2-deploy` §15 `verify[1]` 「원격 프로브」가 `deploy_doctor` 실행이었는지.

## 12. 후속 항목 (고치지 않음)

1. `dev-package/03-HANDOFF.md` 에 `dev-20260913-3`(미push) 표기 — 원격 `refs/tags/dev-20260913-3` 존재(`git ls-remote`). 표기 갱신 필요.
2. 배포 잠금을 EC2 위(`/opt/colab-v2`)로 옮기는 항목 — `deploy-3.md` §8-1 과 동일, 미해소.
3. dev 계획 단계 스크립트 고정본을 레포에 두는 항목 — `DR-2-runbook.md` §1-1.
4. EC2 디스크 사용률 추세(69% → 76%) 감시·이미지 보존 규칙.
