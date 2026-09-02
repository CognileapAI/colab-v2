# infra/dev — AWS dev 환경 배포 런북 (배치 · 재배포 · 진단) — 정본

> 값과 근거는 `dev-package/PLAN-SoT.md §9 〈176〉·〈178〉`. S3 벌(버킷·IAM·CORS·라이프사이클·env) 정본은
> `dev-package/S3.md §1`. 콘솔 체크리스트(G4~G6)는 `dev-package/sessions/ID.md §6`. 집행 계획서 원문은
> `sessions/ID-AWS-PLAN.md`(참조·비정본). **절차가 실제와 다르면 이 문서를 고친다.**

## 무엇이 뜨나

| 자리 | 무엇 | 비고 |
|---|---|---|
| EC2 1대 (AL2023 · arm64 · IMDSv2 **hop limit 2**) | `compose.yml` — core-api(`:8000`) · pipeline-worker · viz-render · ai-service + migrator(프로파일) | 서비스명은 staging 과 같다(`db-boundary` 가 이 파일도 본다). nginx·postgres·frontend 컨테이너 **없음** |
| RDS PostgreSQL 16 (`db.t4g.micro`, 프라이빗) | DB 2 (`colab_platform`·`colab_ai`) · 롤 = 마스터 / `colab_owner`(마이그레이션) / `colab_app`·`colab_ai_app`(앱, NOBYPASSRLS) | 부트스트랩 = `db-bootstrap.sh` |
| S3 데이터 버킷 `colab-platform-data-dev` | 업로드 바이트(`uploads/…`) · 미리보기(`previews/…`) · 백업(`_ops/backups/dev/`) | 역할 정책 = `iam/role-policy.json` |
| S3 웹 버킷 `colab-platform-web-dev` | 프론트 정적 번들 (`ops/deploy_web.py`) | OAC 만 읽는다 |
| CloudFront 1 | 오리진 3 · 동작 3 · SPA 함수 | `cloudfront/README.md` |

배치 결정의 이유(왜 nginx 가 없고, 왜 previews 가 데이터 버킷이고, 왜 `_FILE` 인가)는 `〈178〉`-㉮·㉯.

## 환경변수 — 전체 표 (`compose.yml` 이 정본, 여기는 사람용 요약)

**리터럴(compose 에 고정 — 빠뜨리면 조용히 local 로 떨어지는 값)**: `COLAB_CORE_STORAGE_MODE=s3` ·
`COLAB_CORE_S3_BUCKET` · `COLAB_CORE_S3_REGION` · `COLAB_WORKER_STORAGE_MODE=s3` · `COLAB_WORKER_S3_*` ·
`COLAB_WORKER_WORKDIR` · `COLAB_VIZ_SOURCE_MODE=s3` · `COLAB_VIZ_S3_*` · `COLAB_VIZ_WORKDIR` · `COLAB_VIZ_PREVIEW_SINK=s3` ·
`COLAB_VIZ_PREVIEW_S3_PREFIX` · `COLAB_VIZ_PREVIEW_URL_BASE=/previews` · `COLAB_CORE_VIZ_BASE_URL` · `COLAB_HEALTH_PORT`.

**`dev.env`(EC2 `/opt/colab-v2/dev.env`, 0600) 에 두는 값** — `up.sh` 가 `--env-file` 로 읽는다:

| 이름 | 필수 | 뜻 |
|---|---|---|
| `COLAB_DEV_SECRETS_DIR` | ✅ | 시크릿 파일 디렉터리(EC2 `/etc/colab`) — 아래 표의 파일 7개 |
| `COLAB_CORE_SESSION_SECRET` | ✅ | 세션·다운로드 티켓 서명. 없으면 로그인 500 |
| `COLAB_VIZ_SERVICE_TOKEN` | ✅ | core↔viz 같은 문자열. 없으면 미리보기 전량 503 |
| `COLAB_VIZ_TILE_SIGNING_SECRET` | ✅ | 타일 URL 서명 |
| `COLAB_VIZ_WORK_MAX_BYTES` | ✅ | viz 캐시 상한(바이트) 또는 `none`(명시 무제한). 미설정 = 기동 거부 |
| `COLAB_IMAGE_TAG` | 선택 | 기본 `dev`. 되돌릴 땐 `dev-<sha>` |
| `COLAB_MEM_*` · `COLAB_CPUS_*` | 선택 | 자원 상한(기본 core 512m · worker 768m · viz 768m · ai 384m — 합 2.3 GB → **t4g.medium 권고**, Ted 항목 ④) |
| `OPENAI_API_KEY` · `COLAB_MODEL_*` · `COLAB_AI_QUERY_INTERPRETATION` | 선택 | ai-service (staging 과 같다) |
| `COLAB_CORE_AI_BASE_URL` | 선택 | 기본 compose 내부 주소 |

**시크릿 파일(`$COLAB_DEV_SECRETS_DIR`, 각 0600 · 소유자 uid 10001 — 컨테이너 유저)** — 값은 env 에 **싣지 않는다**(`〈121〉-㉯`):

| 파일 | 내용 | 만드는 곳 |
|---|---|---|
| `core-database.url` | `postgresql+psycopg://colab_app:…@<rds>/colab_platform` | EC2 위에서 |
| `pipeline-db.url` | 같은 앱 롤 · 같은 DB | EC2 위에서 |
| `ai-db.url` | `colab_ai_app@…/colab_ai` | EC2 위에서 |
| `platform-owner-db.url` · `ai-owner-db.url` | 소유자 롤(마이그레이션) | EC2 위에서 |
| `subjects.json` | 심어 둔 주체 표 — **픽스처(`tests/fixtures/subjects.json`)를 올리지 않는다**(값이 곧 토큰) | 로컬에서 만들어 scp |
| `credentials.json` | 계정 이름 → scrypt 해시 (`ops/set-password.py`) | 로컬에서 만들어 scp(해시만) |

AWS 액세스 키는 **어디에도 없다** — EC2 인스턴스 프로파일(`iam/role-trust.json`·`role-policy.json`).

## 올리기 (첫 배포 · 재배포 같다)

```bash
# 개발 기계
infra/dev/build.sh                # 5 이미지 buildx linux/arm64 → 아키텍처 실측 → dist/colab-v2-dev-<sha>.tar
COLAB_DEV_SSH=ec2-user@<EIP> COLAB_DEV_KEY_FILE=~/.config/colab-platform/dev-key.pem infra/dev/ship.sh
# EC2 (첫 배포만: 부트스트랩 → 이후 매번 up.sh)
COLAB_PG_MASTER_URL_FILE=/etc/colab/master.url COLAB_OWNER_PASSWORD=… COLAB_APP_PASSWORD=… COLAB_AI_APP_PASSWORD=… \
  /opt/colab-v2/db-bootstrap.sh prep && … roles && … extensions   # [미확인 G6 실측] 확장 단계 필요 여부
/opt/colab-v2/up.sh                # migrate-platform → migrate-ai → up -d → 4 단위 healthy 대기(fail-closed) → 헬스 본문
… db-bootstrap.sh app-grants && … verify
# 프론트 (개발 기계, 운영자 키)
cd frontend && npm run build && cd ../services/core-api && .venv/bin/python ops/deploy_web.py --dist ../../frontend/dist --bucket colab-platform-web-dev
```

`ship.sh` 는 `db-bootstrap.sh` 를 싣지 않는다 — 첫 배포 때 `scp infra/dev/db-bootstrap.sh infra/staging/db-bootstrap.sh services/core-api/ops/app-role.sql` 을 같은 상대 배치로 손으로 올린다(1회).

## 되돌리기

`dev.env` 의 `COLAB_IMAGE_TAG=dev-<직전 sha>` 로 바꾸고 `up.sh`. 이미지는 `docker images colab-v2/*` 에 남아 있다(불변 태그).
마이그레이션은 되돌리지 않는다 — `0009` 처럼 백필이 든 판은 downgrade 가 값을 잃는다(각 마이그레이션 머리말).

## 확인 — 콘솔 눈이 아니라 `deploy_doctor`

```bash
cd services/core-api && .venv/bin/python ops/deploy_doctor.py --env dev \
  --endpoint https://<id>.cloudfront.net --app-base http://127.0.0.1:18000 \
  --db-url-file <0600 파일> --ai-db-url-file <0600 파일> --bucket colab-platform-data-dev --web-bucket colab-platform-web-dev \
  [--worker-base http://127.0.0.1:18001 --viz-base http://127.0.0.1:18100 --ai-base http://127.0.0.1:18200]
```
(`--app-base` 들은 SSH 터널 `-L 18000:127.0.0.1:8000 …` 뒤.) 인자는 파일/URL 이고 값은 argv 에 싣지 않는다.
**미지정 항목이 남으면 exit 1** — 콘솔 단계 사이의 부분 실행은 `--allow-skip` 을 적어야 통과다(면제 명시).
항목 14 = 운영자 자격증명 · 데이터 버킷 7항목 · 웹 버킷 · DB ×2 · head ×2 · RLS 전수 · 앱 롤 · 4 단위 헬스(`storageMode`/`sourceMode`=s3) ·
앱 자격증명 출처 `imds` · 환경 짝 · 진입/API 라우팅(`/api/v1/me` 401 JSON)/previews · 백업 24h.

## 진단표 — 실제로 겪은 것만 적는다

| 증상 | 원인 | 확인 |
|---|---|---|
| SSH 가 **시간 초과**. 보안그룹 22 규칙·라우팅·서브넷이 전부 맞다 | **탄력적 IP 를 붙이면 주소가 바뀐다.** 인스턴스 요약의 `퍼블릭 IPv4 주소` 는 처음 자동 할당된 것이 남아 보일 수 있다 | 요약 오른쪽의 **`탄력적 IP 주소`** 칸이 정본 |
| `dnf`·`curl` 이 응답 없이 멈춘다. **DNS 는 되고 SSH 도 된다** | **보안그룹 아웃바운드가 비어 있다.** SG 는 상태 저장이라 *들어온* 연결의 응답은 나가지만, **먼저 거는 연결은 막힌다** — DNS 는 VPC 내부 리졸버라 영향이 없어 「네트워크는 되는데」로 보인다 | EC2 에서 `curl -s https://checkip.amazonaws.com`. 고침 = 아웃바운드 `모든 트래픽 / 0.0.0.0/0` |
| `dnf install` 이 `[Errno 2] … .rpm` 으로 죽는다 | 앞선 설치가 중간에 끊겨 **캐시가 깨졌다** | `sudo dnf clean all && sudo rm -rf /var/cache/dnf` 뒤 재시도 |
| `cat /etc/colab/<파일>` 이 **Permission denied** — 파일 소유자는 맞는데 | 디렉터리가 `700 root` 면 안의 파일을 못 연다(디렉터리 실행 권한이 먼저다) | `sudo chown ec2-user:ec2-user /etc/colab` |
| `docker compose` 가 없다 | **AL2023 저장소에 컴포즈 플러그인이 없다** — `dnf install docker` 는 엔진만 준다 | `/usr/libexec/docker/cli-plugins/docker-compose` 로 릴리스 바이너리(aarch64)를 직접 놓는다 |

## 탈출구

- `buildx` 가 없거나 QEMU 가 너무 느리면 → EC2 에서 `git clone` 후 `docker build`(arm64 네이티브). `build.sh` 의 `COLAB_BUILD_PLATFORM` 으로 x86 EC2 도 가능(Ted 항목 ⑧).
- IMDSv2 hop limit 이 1 이면 컨테이너 안 앱이 토큰을 못 받고 `credentialSource: null` — 인스턴스 메타데이터 옵션을 2 로.
