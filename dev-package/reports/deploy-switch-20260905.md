# 배포 방식 전환 — 현행 staging → 박홍진 AWS dev 방식

작성 2026-09-05 · 근거 = `main` 실물 + `origin/feature/rtf400_deploy`(PR #1) 실물 + `gh pr view 1`
레포에서 확인되지 않는 것은 **「레포에 없음」** 으로 적었다.

---

## 1. 현 방식 (main · `infra/staging`)

**호스트**
- WSL2 머신 1대. 「호스트가 WSL2 머신 1대다. 재부팅·업데이트가 곧 중단이다」(`infra/staging/README.md` 말미).
- 공개 경로 = Cloudflare 터널 1개(`www.colab-hydro.com` → compose 서비스명 `nginx:80`). 터널 ingress 정본은 `infra/staging/tunnel/*.tf`(Terraform · WU-IS2 적용 완료 · `terraform plan` = No changes).
- 호스트 포트는 `127.0.0.1:3000` 만. 외부 노출은 터널 하나.

**deploy.sh 가 하는 일** — `infra/staging/deploy.sh`, 단계 헤더 실측 15개
| 단계 | 내용 |
|---|---|
| ⓪ | 타깃 판정(`pipeline/approval/target.sh`) — 기본값 없음, 미지정 거부. `prod` 는 선언만·실행 경로 없음(`㊻` 인용 후 거부) |
| ⓪-b | 필수 설정 프리플라이트(`preflight.sh`) — env 파일을 프로세스에 싣고 compose `:?` + `db-bootstrap.sh required-env` 에서 키 목록을 받아 검사. 빌드보다 먼저 |
| ① | 「무엇을 굽는가」 — 워킹트리 dirty 면 거부(`--allow-dirty` 로만 통과, 건수 원장 기재). 태그 = 커밋 SHA |
| ② | 호스트에서 게이트 재실행 |
| ③ | 태그 보존(`:prev`) — 빌드보다 먼저 |
| ④ | 빌드 (`docker compose build`, 태그 = SHA) |
| ⑤ | 배포 전 백업 — 두 프로파일 GREEN 아니면 중단(`--skip-backup` 면제 시 원장 기재) |
| ⑥ | 저장소(postgres) 먼저 기동 · healthy 대기 타임아웃 = red |
| ⑦ | 롤·DB 부트스트랩(체인마다 따로, `db-bootstrap.sh`) |
| ⑧ | 마이그레이션 — 체인 2개(platform·ai) 각각, 소유자 롤 |
| ⑨ | 앱 롤 GRANT |
| ⑩ / ⑩-b | 교체 · 엣지 설정 반영 판정 |
| ⑪ | 판정(`verify/verify-deploy.sh`) — 헬스 6종 + 본문 대조 + 컨테이너 8개 + `0.0.0.0` 0건 + 두 체인 head. 종료 코드의 근거 |
| ⑫ | 별칭 재부착 · 릴리스 원장 · 표식 · 이미지 보존 3개 |

**compose 서비스** — `infra/staging/compose.i2.yml`: `nginx`(1.27-alpine) · `cloudflared` · `postgres:16-alpine` · `volume-init` · `core-api` · `pipeline-worker` · `viz-render` · `ai-service` · `frontend` · `migrate-platform`/`migrate-ai`(migrator 이미지). 컨테이너 8개 + 마이그레이터. 볼륨 = `uploads` · `events` · `previews` 등.

**저장 모드** — local. 업로드 바이트는 호스트 docker 볼륨(`uploads`). S3 없음.

**DB** — 같은 호스트의 `postgres:16-alpine` 컨테이너(`colab_v2_staging_pg`), DB 2체인(`colab_platform`·`colab_ai`), 볼륨 `pgdata`.

**nginx/TLS** — 엣지 nginx 컨테이너가 라우팅, TLS 는 Cloudflare 터널이 종단. 인증서 관리 없음.

**시크릿** — 홈의 `~/.colab-v2-staging.env`(0600) 한 파일. 터널 토큰 · Cloudflare 3종 · DB 비밀 3종 · pgdata 경로. compose 에는 `--env-file`, 접속 문자열은 `*_FILE` 규약(`〈121〉-㉯`).

**백업·롤백**
- 백업 = `infra/staging/backup/**`(full·volume·검증·복원 리허설·crontab). 배포 ⑤ 가 이것을 게이트로 쓴다.
- 롤백 = `rollback.sh --to-last-green` / `--to-tag` / `--to-placeholder`. 이미지만 되돌리고 **스키마는 되돌리지 않는다**(forward-only · `〈168〉-㉲`). pgdata 무접촉.
- 자동 롤백 기본 off(`〈168〉-㉳`). 판정 red = 중단 + 표식 파일 + 사람 호출.

**자동 트리거** — `pipeline/run-pipeline.sh`(fetch → ff → deploy.sh) + `watch.sh` + `install-schedule.sh`(`*/5` 크론). 상태는 레포 밖 `~/colab-v2-releases`(`release-ledger.tsv`·`DEPLOY-FAILED.txt`·`LAST-SUCCESS.txt`·`pipeline.log`).

**수동 단계 수** — 명령 1줄(`./deploy.sh --target staging`)이면 게이트→백업→마이그레이션→교체→판정까지 끝난다. 사람이 하는 것은 **배포 창 진입조건 판단 + Ted go/no-go** 다.

**「배포 창」 이 무엇인가** — `dev-package/03-HANDOFF.md §4.5` 는 「다음 세션 진입조건」이고, 배포 창 정의는 그 아래 블록들에 있다(`03-HANDOFF.md` 522행 창 6 · 540행 창 7). 실측 정의:
- 창 = **한 번의 staging 배포 회차**이며 **내용물이 못 박혀 있다**. 창 6 = `BF-12` 로깅 하나(＋문서) · 「다른 것을 이 창에 붙이지 않는다」(`〈325〉`). 창 7 = 프론트 버그 4건 + 게이트 고침(`〈333〉` — Ted 가 창을 나눴다).
- 각 창은 자기 진입조건을 갖는다 — 짝 백업(`sessions/WINDOW-20260905-A5b.md` 5b 런북: 단계 A GREEN → 짝 백업 → go/no-go → 배포) · **Ted go/no-go** · 배포 뒤 확인 항목(각 항목의 완료 정의 그대로).
- 완료 정의 = **staging 배포 green**(`CLAUDE.md §0`). 그래서 코드가 `main` 에 있어도 대장 `status` 는 `open` 이다.
- ⛔ **순서 = 창 6 → 창 7. 한 배포로 합치지 않는다.**

---

## 2. 박홍진 방식 (PR #1 · `infra/dev` · AWS dev)

**IaC 인가** — **아니다.** `infra/dev` 에 `.tf`·CDK·CloudFormation **0건**. 실물은 셸 스크립트 4(`build.sh`·`ship.sh`·`up.sh`·`db-bootstrap.sh`·`backup.sh`·`install-cron.sh`) + IAM/버킷 JSON 7(`iam/*.json`) + `compose.yml` + CloudFront Function(`cloudfront/spa-rewrite.js`).
- AWS 자원 생성은 **콘솔 수작업**이다 — 「콘솔 체크리스트(G4~G6)는 `dev-package/sessions/ID.md §6`」(`infra/dev/README.md` 머리말), 재구성 절차는 `docs/DEPLOY.md 5)`.
- ⚠ `infra/README.md` 의 「**콘솔 수작업 0. 모든 리소스는 여기서 나온다**」는 **현재 실물과 어긋난다**(문서 정정 대상). Terraform 이 실제로 있는 곳은 `infra/staging/tunnel/` 하나뿐이다.

**무엇이 뜨나**(`infra/dev/README.md`)
| 자리 | 무엇 |
|---|---|
| EC2 1대 (AL2023 · arm64 · `t4g.small` · IMDSv2 **hop 2**) | `compose.yml` — core-api(:8000) · pipeline-worker · viz-render · ai-service + migrator(프로파일). **nginx·postgres·frontend 컨테이너 없음** |
| RDS PostgreSQL 16 (`db.t4g.micro` · 프라이빗) | DB 2 · 롤 = 마스터 / `colab_owner` / `colab_app`·`colab_ai_app`(NOBYPASSRLS) |
| S3 `colab-platform-data-dev` | `uploads/` · `previews/` · `_ops/backups/dev/` |
| S3 `colab-platform-web-dev` | 프론트 정적 번들. OAC 만 읽는다 |
| CloudFront 1 | 오리진 3 · 동작 3 · SPA 함수 |
| 그 밖 | VPC(**NAT 없음**) · 서브넷 4 · SG 2 · 탄력적 IP · IAM 역할·정책 2 · IAM 사용자 1 · 키페어 · 예산 2 |

**EC2 가 코드를 어떻게 받나** — git pull 도 레지스트리도 아니다. **이미지 tar 전송**이다.
1. 개발 기계: `infra/dev/build.sh` — `docker buildx build --platform linux/arm64 --load` ×5 → `docker image inspect` 로 `arm64` 실측(불일치 시 중단) → `docker save -o dist/colab-v2-dev-<sha>.tar`. 태그 둘: 움직이는 `:dev` · 불변 `:dev-<sha>`.
2. `COLAB_DEV_SSH=ec2-user@<EIP> COLAB_DEV_KEY_FILE=… infra/dev/ship.sh` — scp tar + `compose.yml` + `up.sh` → EC2 에서 `docker load` → `:dev` 재태깅 → `/opt/colab-v2/CURRENT_SHA` 기록.
3. EC2: `/opt/colab-v2/up.sh`.
- 레지스트리(ECR) 없음. systemd 없음(docker compose 만). `ship.sh` 는 `db-bootstrap.sh` 를 싣지 않는다 — 첫 배포 때 손으로 scp(1회).

**마이그레이션** — `up.sh` ① `dc --profile migrate run --rm migrate-platform` → `migrate-ai`(체인 2개, 소유자 롤). ② `up -d --remove-orphans`. ③ 4 단위 healthy 대기 120s **fail-closed**(staging `deploy.sh` 가 fail-open 이라 놓쳤던 교훈). ④ `/healthz` 본문 4개를 찍어 저장 모드가 `s3` 인지 확인.
- 롤 부트스트랩은 별도 — `db-bootstrap.sh prep|roles|extensions|app-grants|verify`, RDS 마스터 접속을 `COLAB_PG_MASTER_URL_FILE` 로 받는다(`infra/staging/db-bootstrap.sh` 를 분기로 파라미터화 · `〈281〉-㉰`).

**프론트** — CloudFront + S3 웹 버킷. `cd frontend && npm run build` → `services/core-api/ops/deploy_web.py --dist … --bucket colab-platform-web-dev`. SPA 라우팅은 CloudFront Function `spa-rewrite.js`(오류 응답 치환을 쓰지 않는다 — `/api/*` 의 진짜 401/403 JSON 이 HTML 로 바뀌기 때문). 판정 = `/api/v1/me` 가 401 JSON.

**deploy_doctor** — `services/core-api/ops/deploy_doctor.py`(741줄). `ops/s3_doctor.py`·`s3_smoke.py` 의 `Report`·`_s3_call`·`check_credentials`·`check_bucket` 을 import 해 재사용.
- 인자는 **값이 아니라 파일/URL**(`--db-url-file` 등 · argv 에 값 안 싣는다).
- **항목 14** = 운영자 자격증명 · 데이터 버킷 7항목 · 웹 버킷 · DB ×2 · head ×2 · RLS 전수 · 앱 롤 · 4 단위 헬스(`storageMode`/`sourceMode`=s3) · 앱 자격증명 출처 `imds` · 환경 짝 · 진입/API 라우팅/previews · 백업 24h.
- **미지정 항목이 남으면 exit 1**. 면제는 `--allow-skip` 명시. **부분 실행 둘을 합쳐 green 이라 하지 않는다** — `─ 0` 인 한 번의 실행만 근거(`CLAUDE.md` 「배포」절).
- 실측 = **14/14 · ✗0 · ─0**(PR 본문 · 증거 `docs/DEPLOY-evidence-doctor.txt`).

**시크릿·env** — SSM 아님. 3자리로 나뉜다(`docs/DEPLOY.md 2-1`).
| 자리 | 무엇 | 이유 |
|---|---|---|
| `compose.yml` 리터럴 | `COLAB_*_STORAGE_MODE=s3`·버킷·리전·`COLAB_VIZ_PREVIEW_*` 등 | 치환으로 두면 빠뜨렸을 때 기본 `local` 이 이긴다 |
| `/opt/colab-v2/dev.env`(0600) | 서명 비밀값(`COLAB_CORE_SESSION_SECRET`·`COLAB_VIZ_SERVICE_TOKEN`·`COLAB_VIZ_TILE_SIGNING_SECRET`)·`COLAB_VIZ_WORK_MAX_BYTES`·자원 상한·`COLAB_IMAGE_TAG` | `up.sh` 가 `--env-file` |
| `/etc/colab/*`(0600 · uid 10001) | 접속 문자열 5 · `subjects.json` · `credentials.json` | 값이 아니라 **경로**를 env 로(`*_FILE` · `〈121〉-㉯`) |
- **AWS 액세스 키는 어디에도 없다** — EC2 인스턴스 프로파일 + IMDSv2(`credentialSource: imds` 실측).

**되돌리기** — `dev.env` 의 `COLAB_IMAGE_TAG=dev-<직전 sha>` 로 바꾸고 `up.sh`. 이미지는 EC2 로컬에 불변 태그로 남아 있다. **마이그레이션은 되돌리지 않는다**(staging 과 같은 forward-only).

**백업** — `infra/dev/backup.sh` + `install-cron.sh`(cron). 대상 = S3 `_ops/backups/dev/`, 라이프사이클 `backups-30d`. `pg_dump` 는 일회용 `postgres:16-alpine` 컨테이너. 백업 롤은 `colab_backup`(RLS FORCE 때문에 소유자·마스터도 전수를 못 읽는다).

**비용** — **월 $32~44**(EC2 t4g.small + RDS db.t4g.micro + 스토리지 + EIP). 예산 알람 2(연 $120 크레딧 소진 · 월 $50 급증). ⏰ **Free Plan 마감 둘** — 크레딧 $120 소진 2026-11~12 추정 · 무료 플랜 기간 만료 **2027-02-22**(날짜라 예산이 못 잡는다).

---

## 3. 차이표

| 축 | main / staging | PR dev (박홍진) |
|---|---|---|
| 호스트 | WSL2 1대 (재부팅 = 중단) | AWS 서울 EC2 `t4g.small` arm64 + RDS |
| IaC | Terraform 은 터널 하나(`infra/staging/tunnel`) | **없음** — 콘솔 수작업 + 셸 스크립트 + IAM JSON |
| 코드 전달 | 호스트에서 `docker compose build`(워킹트리 dirty 거부) | 개발 기계 buildx arm64 → `docker save` tar → scp → `docker load` |
| 오케스트레이션 | docker compose (컨테이너 8 + 마이그레이터) | docker compose (앱 4 + 마이그레이터). nginx·postgres·frontend 컨테이너 **없음** |
| DB | 같은 호스트 `postgres:16-alpine` 컨테이너 + pgdata 볼륨 | RDS PG16 프라이빗 |
| 저장 모드 | `local`(docker 볼륨 `uploads`) | **`s3`** — 업로드 프리사인드 직행, worker·viz 는 내려받아 읽는다 |
| 프론트 | `frontend` 컨테이너 + 엣지 nginx | S3 웹 버킷 + CloudFront + SPA Function(`deploy_web.py`) |
| TLS/공개 경로 | Cloudflare 터널(도메인 `colab-hydro.com`) | CloudFront 기본 도메인 `d31zgpff2091oh.cloudfront.net`. **자체 도메인 없음** |
| 시크릿 | 홈 `~/.colab-v2-staging.env` 1개 | EC2 `dev.env` + `/etc/colab/*` 7파일 + compose 리터럴 |
| AWS 자격 | 해당 없음 | 인스턴스 프로파일 IMDSv2(키 0개) |
| 마이그레이션 | `deploy.sh` ⑦⑧⑨ 안에서 | `up.sh` ① (부트스트랩은 별도 수동) |
| 판정 | `verify/verify-deploy.sh`(헬스 6 + 본문 + 컨테이너 8 + `0.0.0.0` 0건 + 체인 head) — `deploy.sh` 종료 코드에 직결 | `up.sh` healthy fail-closed + **`deploy_doctor` 14항목(별도 실행)** |
| 롤백 | `rollback.sh --to-last-green`(원장 기반) · 이미지만 | `COLAB_IMAGE_TAG=dev-<sha>` + `up.sh` · 이미지만 |
| 릴리스 원장 | `~/colab-v2-releases/release-ledger.tsv` 등 4종 | **없음** — `CURRENT_SHA` 파일 1개 |
| 자동 트리거 | `pipeline/watch.sh` + 크론 `*/5` · 승인 기록 | **없음**(CI 자동 배포는 「일부러 안 한 것」) |
| 백업 | `backup/**` (full·volume·복원 리허설·crontab) · 배포 게이트 | `infra/dev/backup.sh` + cron → S3 `_ops/backups/dev/`(30일) |
| 비용 | 전기값(자체 호스트) | 월 $32~44 · 크레딧 마감 2건 |
| 명령 수 | 1 (`./deploy.sh --target staging`) | **4** (build → ship → up.sh → deploy_web) + doctor |

---

## 4. 전환에 필요한 것

### (a) `main` 에 들어가야 할 코드

PR #1 = **169 파일 · +17,771 / −490 · 17 커밋**. 배포 인프라와 기능이 **분리 불가**하다.

| 커밋 | 성격 |
|---|---|
| `570b29b` S3 커널 + 운영 진단 도구 | **배포 기반**(`kernel/{sigv4,aws_credentials,s3,objectpath}.py` · `ops/s3_doctor.py`·`s3_smoke.py`) |
| `12b364f` 저장 Port (local/s3) | **배포 기반 겸 U-1** — dev compose 의 `COLAB_CORE_STORAGE_MODE=s3` 가 이것 없이는 기동 거부 |
| `a4a2258`·`00d9863`·`f72d8f8`·`04af1a0` | U-1 기능(폴더 드롭 · 프리사인드 전송 9 op · 전송 원장 `0008`) |
| `70b5140`·`6085108`·`23ea6fd`·`1147e87`·`e270522`·`025d3c3`·`c7965aa` | F-3 기능(파일 관리 · 다운로드 200 티켓 · `0009`) |
| `bb895e9` 업로드 수명주기 개편 결함 5 | 기능 |
| **`82c03cf` AWS dev 환경 구축 + 인수인계** | **배포 본체** — `infra/dev/**` · `ops/deploy_doctor.py`·`deploy_web.py` · `docs/DEPLOY*.md` · `CLAUDE.md` 절 · `.dockerignore`×5 · `gates/tools/db_boundary.py` 확장 · **worker·viz S3 커널 복제(V-3)** · Dockerfile 2단계 빌드 |
| `b530a6d`·`30b3f08`·`0e294e5` | 병합 정리(번호 `〈276〉`~`〈281〉` · 인용 371곳 · 마이그레이션 머지 `0011`) · viz `Settings` dataclass 정정 · PR 본문 |

**인프라만 체리픽 가능한가 — 아니다.**
1. `82c03cf` 는 앞선 7커밋의 `kernel/s3.py`·`ports/storage.py` 를 전제한다. 없으면 import 실패.
2. `infra/dev/compose.yml` 이 `COLAB_CORE_STORAGE_MODE=s3` 를 리터럴로 박는데, 저장 Port(=U-1 코드)가 없으면 **반쪽 설정 기동 거부** 규약에 걸린다. **s3 저장 모드는 하드 의존이다.**
3. worker·viz 가 S3 바이트를 읽는 V-3 코드도 `82c03cf` 안에 있다 — 이것 없이 s3 모드로 올리면 워커가 바이트를 못 연다(「형식 인식 실패」로 위장).
4. `82c03cf` 는 F-3 의 `0009` 스탬프를 전제로 doctor 가 head 를 본다(dev 는 `0009_file_management` 로 스탬프돼 있었고, 병합 후 head 는 `0011`).
⟹ **PR #1 은 통짜로 간다.** 쪼개려면 `b530a6d` 의 번호 재배치 371곳과 `0011` 머지 리비전을 다시 짜야 하고, 그 비용이 통짜 병합보다 크다.

**충돌 실측** — `git merge-tree` 로 **20 파일 CONFLICT**:
`dev-package/work-items.yaml` · `frontend/src/components/catalog/CatalogTable.tsx` · `detail/{FileList.tsx(add/add), detail.css, detailSource.ts, useDatasetDetail.ts}` · `routes/{DatasetDetailPage.tsx, DatasetsPage.tsx}` · `frontend/vite.config.ts` · core-api `{app/main.py, routes/ingestion.py, routes/not_implemented.py, domains/d8_insight.py, tests/test_dataset_registration.py, tests/test_not_implemented.py, tests/test_route_table.py}` · `pipeline-worker/app/worker.py` · `viz-render/{app/main.py, app/routes/renders.py, kernel/config.py}`.
⭑ **`infra/dev/**` · `docs/DEPLOY*.md` · `ops/deploy_doctor.py` 는 충돌 0**(순수 신규). 충돌은 전부 기능면과 대장이다.

### (b) AWS 계정 선행조건
- **AWS 계정** — 이미 존재(박홍진이 구축한 계정, 기존 S3 업로드 버킷과 **같은 계정**). ⚠ 계정 소유·결제 주체가 Ted 인지 박홍진인지는 **레포에 없음**.
- **운영자 자격증명** — `deploy_web.py`·`deploy_doctor.py` 는 운영자 기계의 AWS 자격증명을 쓴다(IAM 사용자 1 + 키 1 · 정책 `iam/user-policy.json`). Ted 기계에 이 자격을 놓는 절차는 **레포에 없음**.
- **SSH 접근** — `COLAB_DEV_SSH`(ec2-user@탄력적 IP) + 키 파일. 새 사람은 SG `colab-platform-app-dev-sg` 22번에 규칙 추가 필요(HANDOVER 가 hsw 건으로 명시).
- **리전** — 서울(ap-northeast-2) 고정.
- **예산** — 예산 2개 이미 설정(연 $120 · 월 $50). 금액 확정은 Ted 판정 ⑯.
- **도메인/TLS** — **없다.** CloudFront 기본 도메인만. 자체 도메인을 붙이려면 **ACM 인증서는 반드시 us-east-1**(`CLAUDE.md` 확장 절). `colab-hydro.com` 은 지금 staging 터널이 쓰고 있다.
- **빌드 기계** — `docker buildx` (arm64). 없으면 EC2 네이티브 빌드 또는 `COLAB_BUILD_PLATFORM` 으로 x86 EC2.

### (c) staging → dev 데이터 이관
- **DB** — 레포에 **staging→dev 이관 절차 없음**. 재료는 있다: `infra/staging/backup/backup-full.sh`(pg_dump) + `infra/staging/restore/restore-db.sh`. RDS 로 넣으려면 소유자 롤·RLS FORCE·`colab_backup` 롤 제약을 다시 통과해야 한다(`CLAUDE.md` 10번). **새로 써야 하는 절차다.**
- **업로드 파일** — staging 은 docker 볼륨 `uploads`(local 모드), dev 는 S3 `uploads/{targetId}/…` 이고 **객체 키 규약이 `objectpath.py` 로 다르다**. 볼륨 → S3 복사 도구 **레포에 없음**. 대안 = 이관하지 않고 dev 에서 재적재(`infra/staging/load-seed.py` 가 공개 API 4 op 으로 적재하며 멱등 — base-url 을 CloudFront 주소로 바꾸면 재사용 가능). ⚠ 단 매니페스트가 아직 없다(README 「2026-08-26 현재 매니페스트가 없다」 · `03-HANDOFF §4 #28`).
- **권고** — 마이그레이션이 아니라 **재적재**. dev 는 이미 MODIS HDF4 8건 55MB 업로드 실측이 있다.

### (d) 문서·원장 갱신
- `dev-package/work-items.yaml` — 병합 충돌 파일. PR 이 `U-1`·`U-2`·`F-3`·`I-D`·`V-3` 5행을 등재했고 main 쪽은 `BF-*` 행이 늘었다. **줄 단위 병합**이 필요하다.
- `dev-package/03-HANDOFF.md §4.5` 아래 **배포 창 블록** — 창 6(`BF-12`) · 창 7(프론트 4건) 이 살아 있다. dev 전환은 **창의 대상 환경이 바뀌는 일**이라 「창 = staging 배포 green」 정의 자체를 고쳐야 한다. 창 8(또는 새 이름)에 「dev 배포 green + `deploy_doctor` 14/14」를 완료 판정으로 박는 개정이 필요하다.
- `CLAUDE.md §0` 「완료 = staging 배포 green」 — **정의 개정 대상**.
- `dev-package/PLAN-SoT.md §9` — 〈N〉 은 **예약하지 않고 병합 직전 `origin/main` 최대 +1 로 재실측**(선례 `〈310〉`·`〈318〉`-㉤·`〈333〉`). PR 이 이미 `〈276〉`~`〈281〉` 을 썼으므로 병합 시점에 재확인.
- `infra/README.md` — 「콘솔 수작업 0」 문장이 실물과 어긋난다. 정정.
- `infra/staging/README.md` — staging 을 남길지 내릴지에 따라 상태 표기 갱신.

---

## 5. 권고 절차

| # | 무엇 | 누구 | 명령/파일 | 게이트·검증 | 롤백 |
|---|---|---|---|---|---|
| 1 | **17건 Ted 판정을 배포 차단분과 기능분으로 갈라 처리** (아래 표) | Ted | PR #1 본문 「⚠ Ted 판정」 | 배포 차단 6건 확정 기록 = `PLAN-SoT §9` 신규 〈N〉 | 판정 보류 시 병합 중단 |
| 2 | **창 6 을 먼저 닫는다** — `BF-12` 로깅, staging 배포 | dev 세션 + Ted go/no-go | `03-HANDOFF` 창 6 블록 · `sessions/WINDOW-20260905-A5b.md` 5b 런북 | 8/8 healthy 후 ≥60분 → viz 회수 요약 1줄(계수 · 삭제 0) | `rollback.sh --to-last-green` |
| 3 | **창 7 을 닫는다** — 프론트 4건, staging 배포 | dev 세션 + Ted go/no-go | 창 7 블록 ⓐ~ⓓ | 눈 확인 4항목 → 대장 `open`→`done` | 동일 |
| 4 | **PR #1 병합 준비 레인** — 워크트리에서 `main` 위로 리베이스/머지, 충돌 20파일 해소 | dev 세션 (`isolation: worktree`) | `git merge origin/feature/rtf400_deploy` | 충돌 해소 후 **전 게이트 전수**(`~/.colab-v2-test.env` source 후 · 서비스 `.venv` 세운 뒤 red(준비) 0) + pytest 654 + vitest 492 + tsc 0 | 워크트리 폐기 |
| 5 | **〈N〉 재실측** — `origin/main` 최대 +1 로 번호 재배치 | dev 세션 | `dev-package/PLAN-SoT.md §9` | `work-item-consistency` green | 커밋 revert |
| 6 | **PR #1 병합** | Ted 승인 → dev 세션 | `gh pr merge 1` (또는 통합 브랜치 push) | CI 게이트 + 병합 트리 전수(트리 해시가 이미 판정된 트리와 같으면 재실행 생략) | `git revert -m 1` |
| 7 | **staging 에 마이그레이션 적용** — `0008`·`0009`·`0011` | dev 세션 | 백업 회차 확인 후 `alembic upgrade head` | ⛔ **`0009` 백필이 `0004` 이후 처음 `NO FORCE RLS` 창을 연다**(같은 트랜잭션 안 복구·자가검증). 배포 전 백업 필수 | **되돌리지 않는다**(forward-only) — 백업 복원만 |
| 8 | **staging 회귀 배포** — local 모드 그대로 | dev 세션 | `./deploy.sh --target staging` | `verify-deploy.sh` green. staging 은 local 모드라 저장 분기 무영향 | `rollback.sh --to-last-green` |
| 9 | **AWS 접근 인수인계** — 계정·결제 주체 확정 · 운영자 IAM 키 · SSH 키·SG 22 규칙 | Ted ↔ 박홍진 | `docs/DEPLOY_HANDOVER.md` · SG `colab-platform-app-dev-sg` | Ted 기계에서 `aws sts get-caller-identity` + `ssh` 성공 | 규칙 삭제 |
| 10 | **dev 재배포 1회(현 main 코드로)** | dev 세션 | `infra/dev/build.sh` → `ship.sh` → EC2 `up.sh` → `deploy_web.py` | `up.sh` 4 단위 healthy fail-closed + `/healthz` 전부 `s3` | `COLAB_IMAGE_TAG=dev-<직전 sha>` + `up.sh` |
| 11 | **`deploy_doctor` 전량 재실행** | dev 세션 | `ops/deploy_doctor.py --env dev …` | **14/14 · ✗0 · ─0** 한 번의 실행. 부분 실행 합산 금지 | ✗ 나오면 10번으로 |
| 12 | **미리보기 1건 실호출** — I-D 완료 정의 미충족분 | dev 세션 | 브라우저에서 업로드→등록→미리보기 | `previews/` 객체 ≥1 · 같은 객체 2회 materialize = 같은 cache_key | — |
| 13 | **맥 한글 파일명 업로드 실물 확인** | 박홍진 또는 맥 보유자 | 브라우저 업로드 | NFD 파일명 성공 | `normalizeName.ts` 재수정 |
| 14 | **staging→dev 데이터** — 재적재 방식 확정 | Ted 결정 + dev 세션 | `infra/staging/load-seed.py --base-url https://<cloudfront>` | 멱등 판정(이름 완전 일치) | dev 데이터셋 삭제 = `deleteDataset` 501 ⟹ **되돌리기 경로 없음. 매니페스트 확정 전 실행 금지** |
| 15 | **완료 정의·창 정의 개정** | Ted 판정 → dev 세션 | `CLAUDE.md §0` · `03-HANDOFF §4.5` 창 블록 · `work-items.yaml` | `work-item-consistency` green | 커밋 revert |
| 16 | **staging 내리기 판정** | Ted | `infra/staging` 터널 중지 | dev 가 창 2회분을 green 으로 넘긴 뒤에만 | 터널 재기동(비용 0) |
| 17 | **prod 판정** — `㊻` 개정 | Ted | PR 판정 ⑫⑬ | 별건. dev 전환과 분리 | — |

**PR #1 병합 위치** — **6번**(창 6·7 이 닫힌 뒤). 이유: ⑴ 창 6·7 의 내용물이 「다른 것을 붙이지 않는다」로 못 박혀 있어 PR 을 얹으면 규칙이 창 안에서 깨진다. ⑵ 충돌 20파일이 창 7 의 프론트 4건과 같은 파일군(`CatalogTable.tsx`·`detail/*`·`vite.config.ts`)이라 창 7 병합 **뒤**에 푸는 것이 한 번에 끝난다. ⑶ `0009` 백필의 `NO FORCE RLS` 창은 staging 이 안정된 상태에서 열어야 한다.

**17건 Ted 판정 — 배포 전환을 막는 것 vs 기능·이월**

| 배포 차단 (선행 필수) | 사유 |
|---|---|
| ⑫ `㊻` prod 개정 | dev 한정 해제는 `〈279〉` 로 끝났다. **dev 전환 자체는 ⑫ 없이 가능** — 단 「배포 = staging」 정의를 바꾸려면 정본이 dev 를 배포처로 인정해야 한다 |
| ⑬ `〈279〉` prod 확장 여부 | staging 을 내릴지의 전제. 16번 단계와 직결 |
| ⑭ V-3 방식(내려받기 · 커널 복제 등기 · previews 데이터 버킷) | dev 아키텍처 그 자체. 뒤집으면 `82c03cf` 재작성 |
| ⑮ 사이징 `t4g.small` 2GB | 자원 상한 합 2.3GB > 2GB ⟹ **`t4g.medium` 권고**. 렌더 부하 미측정 |
| ⑯ 예산 금액 · dev 소스맵 공개 · 첫 연구실/계정 · ARM64 실패 시 x86 | 계정 운영 조건 |
| ⑰ ⭑ **유료 계정 전환 시점** | 마감 2건(크레딧 2026-11~12 · 무료 플랜 2027-02-22). **전환 결정과 동시에 정해야 한다** |
| ③ `〈281〉`-㉻ `UploadStatus.registered` | 이미 집행됨 — 병합 전 사후 판정 |

| 기능 전용 (전환 뒤로 미뤄도 됨) | |
|---|---|
| ① `〈277〉` 8차 계약 동결 해제 | 병합 조건이지 배포 방식 조건은 아니다 |
| ② `〈280〉` 9차 묶음 | 동일 |
| ④ `〈59〉`-③ 번복(본체 파일 추가·교체·삭제) | 기능 |
| ⑤ 본체 변경 시 「마지막 수정」 이동 | 기능 |
| ⑥ 다운로드 형태(200 티켓) | 기능 |
| ⑦ `〈78〉` J-10 폴더 드롭 승격(사후 등재) | 기능 |
| ⑧ 미완결 업로드를 S-01 에 두는 것 | 기능(이미 집행·사후 판정) |
| ⑨ `deleteDataset` 범위 밖 유지 | 기능 |
| ⑩ 격자 op 이름 유지 vs 개명 | 기능 |
| ⑪ `[정본 무근거]` 2건 | 문서 |

⟹ **①②④~⑪ 은 병합 판정에는 필요하지만 배포 방식 전환의 차단 요인이 아니다.** 다만 PR 이 통짜라 **병합 자체가 전부를 요구**한다 — 실질적으로 17건 전건이 6번 단계 앞에 온다.

---

## 6. 위험·미결

1. **staging admin 비밀번호가 레포에 평문**(`〈155〉`-㉳-ⓐ · **이미 `main` 에 있다**). dev 3계정도 같은 값으로 맞췄다. ⟹ **prod 를 열기 전 회전 필수**(`03-HANDOFF §4 #11`). dev 가 CloudFront 로 공개 주소를 갖게 된 이상 staging(터널 뒤)보다 노출면이 넓다 — **전환 전에 회전하는 것이 맞다.**
2. **Free Plan 마감 2건** — 크레딧 $120 소진 2026-11~12 추정(예산 알람이 잡는다) · 무료 플랜 기간 만료 **2027-02-22**(날짜라 예산이 못 잡는다 · 달력으로 챙긴다). 전환하면 **유일한 배포처가 이 마감을 갖는다.**
3. **미리보기 미검증** — `previews/` 객체 **0건**. `I-D` 는 `partial` 이고 `done` 이 아니다. 「배선은 다 서 있지만 한 번도 안 돌았다」(HANDOVER). ⟹ staging 을 내리기 전에 반드시 닫는다.
4. **`U-2` S3 고아 바이트** — 치우는 주체가 없다. 워커 만료가 DB 행만 지운다. dev 실측 3건 26,579,847 B 를 손으로 지웠다. 판별식 = `d3_dataset`·`d5_upload`·열린 전송 셋 다 없어야 고아. 추가로 **완결된 전송 원장 행이 안 지워진다**(행 누수).
5. **`0009` 백필의 `NO FORCE RLS` 창** — `0004` 이후 처음. 같은 트랜잭션 안에서 복구·자가검증하지만 **그 창이 열려 있는 동안 연구실 경계가 없다**. 배포 전 백업 GREEN 이 전제.
6. **arm64** — geo 스택(rasterio·netCDF4·h5py·pyhdf) 휠. `pyhdf` 는 arm64 휠이 없어 2단계 빌드로 소스 컴파일. 빌드 시간·재현성 위험. 실패 시 x86 전환은 Ted 판정 ⑯.
7. **`t4g.small` 2GB에 자원 상한 합 2.3GB** — 초과 배분. 렌더 부하 미측정. `t4g.medium` 권고.
8. **SPOF·롤백 낙차** — dev 에는 릴리스 원장·자동 판정 트리거·승인 기록이 **없다**. staging 의 `pipeline/**`·`verify/**`·`backup/**` 자산이 dev 로 이식되지 않았다. 전환하면 **I3 가 세운 판정 장치를 잃는다** — 이것이 전환의 가장 큰 회귀다.
9. **IaC 부재** — dev 자원 재구성은 `docs/DEPLOY.md 5)` 의 **콘솔 절차 문서**뿐이다. 계정 사고 시 복구가 사람 손이다.
10. **묶음 zip 대용량(>166 MB) 미실측** · **삭제 확인 단계 없음**(서버 409 만 방어) · **상태 2 목록 op 부재**(브라우저 저장 의존 — 다른 기기·시크릿창에서 못 되찾는다).
11. **CI 사각** — `db-boundary` 본 게이트·서비스 pytest 잡이 CI 에 **없다**(`DEPLOY_NOTES §2-1` · `HANDOFF §4 #42`). dev 회귀는 로컬 실행으로만 잡힌다.
12. **staging→dev 데이터 이관 절차 레포에 없음**. 볼륨→S3 복사 도구 없음. `load-seed.py` 매니페스트도 아직 없다.
13. **AWS 계정의 소유·결제 주체 레포에 없음.** 박홍진 개인 계정이면 인수인계가 계정 이전 문제가 된다.

---

## 7. 한 줄 결론

**전환은 가능하나 PR #1 은 통짜로만 들어가고(체리픽 불가 · 충돌 20파일 · Ted 17건 선행), 순서는 창 6 → 창 7 → PR 병합 → dev 재배포 + `deploy_doctor` 14/14 → 미리보기 실호출까지 선 뒤에야 staging 을 내린다 — 잃는 것은 I3 가 세운 릴리스 원장·자동 판정·승인 기록이고, 그것을 dev 로 옮기는 일이 전환의 실질 비용이다.**
