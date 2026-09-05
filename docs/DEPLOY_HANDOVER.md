# AWS dev 환경 구축 — 변경 요약

프론트·백엔드·DB 를 AWS(서울 리전)에 올렸습니다. 기존 S3 업로드 버킷과 **같은 계정**입니다.
접속: **https://d31zgpff2091oh.cloudfront.net** · 로그인 자격은 `~/.config/colab-platform/dev-secrets/dev-logins.txt`

## 먼저 알아야 할 것 — 돈

**월 $32~44** 정도 나갑니다 (EC2 `t4g.small` + RDS `db.t4g.micro` + 스토리지 + 탄력적 IP).
예산 알람 2개가 감시 중입니다 — 연 $120(크레딧 소진) · 월 $50(급증).

⏰ **이 계정에는 마감이 둘 있습니다. 먼저 오는 쪽에서 dev 가 그냥 멈춥니다.**
- **크레딧 $120 소진 — 2026-11~12월 추정** (예산 알람이 50/80/90% 에서 알립니다)
- **무료 플랜 기간 만료 — 2027-02-22** (날짜라 예산이 못 잡습니다. **달력으로 챙겨야 합니다**)

안 쓸 때 EC2·RDS 를 중지하면 요금이 줍니다. 탄력적 IP 를 붙여놔서 **다시 켜도 주소는 그대로**입니다.
다만 **오래 중지할 때는 탄력적 IP 를 반환**하세요 — 꺼져 있어도 주소값(월 $3.6)이 나갑니다.

## 먼저 해야 할 일

### 한 번만 — 누가 하든 한 번이면 됩니다
- **맥에서 한글 파일명 업로드 확인** ⛔ **아직 안 했습니다.** 맥은 파일명을 NFD(자모 분해)로 주고
  서버는 NFC 로 정규화해서, 한글 이름만 「계획에 있는 파일이 선택에 없어요」로 막혔습니다.
  고쳤고 시험도 붙였지만(`normalizeName.ts`·`normalize-name.test.ts`), **실물 확인은 윈도우에서만 했습니다.**
  윈도우는 원래 NFC 라 이 버그가 일어나지 않는 환경이라 **그 성공이 고침을 증명하지 못합니다**
- **동료(hsw) SSH 규칙 추가** — 보안그룹 `colab-platform-app-dev-sg` 의 22번에 규칙 하나. 설명에 `hsw`

### 사람마다 각자 — **없음**
- 로컬은 **파일 폴더 모드**로 동작하므로 개인 AWS 자원이 필요 없습니다.
  `local.env` 에 버킷 설정이 **없는 것이 정상**입니다
- **머지만 받으면 바로 쓸 수 있습니다**

### 환경마다 — 새 환경을 만들 때 반복합니다
- `docs/DEPLOY.md` 5) 절(재구성 절차)을 그 환경 이름으로 다시 실행합니다
- prod 는 **아직 없습니다** — 정본이 ⏸ 로 두었고 판정이 선행합니다

## 새로 생긴 것 (AWS · dev 한 벌)

VPC · 서브넷 4 · 보안그룹 2 · EC2 · **탄력적 IP** · RDS · CloudFront(+함수) ·
IAM 역할·정책 2 · IAM 사용자 1(+키 1) · 키 페어 · **S3 버킷 2**(데이터 · 웹) · 예산 2
→ 전체 목록과 **지우는 순서**: `docs/DEPLOY.md` 4) 절

## 새로 생긴 것 (저장소)

`infra/dev/**`(빌드·전송·기동·DB 부트스트랩·백업·cron·IAM 정책) ·
`services/core-api/ops/deploy_doctor.py`·`deploy_web.py` · `.dockerignore` ×5 ·
worker·viz 의 S3 커널 복제와 Port · `docs/DEPLOY.md`(운영 문서) · 이 문서

## 기존 코드에 손댄 것  ← 여기만 보셔도 됩니다

| 파일 | 무엇을 | 왜 |
|---|---|---|
| `core-api/kernel/{sigv4,aws_credentials,s3}.py` | 절대→상대 import · `put_object(cache_control=)` | worker·viz 에 **바이트 동일 복제**를 두려고 |
| `core-api/app/main.py` | `GET /healthz/storage` 추가 | 저장 모드가 조용히 `local` 인 것을 잡는다 |
| `contracts/codegen/manifest.toml` | S3 커널 복제 등기 6 | 복제본이 갈라지면 게이트가 red |
| `pipeline-worker/app/{worker,health}.py` | `drive_uploads` 가 Port 사용 · healthz `storageMode` | 워커가 S3 바이트를 읽으려면 |
| `viz-render/{main,renders,jobs,config,source}.py` | `materialize` · 소스 모드 · preview sink · **캐시 키를 ETag 로** | mtime 이면 `previews/` 가 렌더마다 는다 |
| `infra/staging/db-bootstrap.sh` | `COLAB_PG_MASTER_URL_FILE` 분기(**미설정 = 현행**) | RDS 는 마스터 접속이 파일로 온다 |
| `gates/tools/db_boundary.py`·`db-boundary-selftest.sh`·`gates/README.md` | compose 단일 → 목록(staging+dev) | dev compose 가 검사 사각이었다 |
| `frontend/vite.config.ts` | dev 프록시 `/api`→`127.0.0.1:8000` | 없으면 로컬 화면에서 로그인 404 |
| `services/{pipeline-worker,viz-render}/Dockerfile` | **2단계 빌드** | `pyhdf` 는 arm64 휠이 없어 소스 컴파일이 필요하다 |
| `CLAUDE.md` | 「배포 — 고칠 때 알아야 할 것」 절 추가 | 선의로 개선하다 정확히 깨뜨리는 것 10가지 |

## 기존 AWS 자원을 바꾼 것  ← 여기도요

| 자원 | 무엇을 | 왜 |
|---|---|---|
| S3 `colab-platform-data-dev` | CORS 에 CloudFront 오리진 추가 | 배포 환경에서 업로드 |
| S3 `colab-platform-data-dev` | 버킷 정책에 `CloudFrontReadsPreviews` **합침** | 미리보기 배달. ⚠ 콘솔의 「정책 복사」를 그대로 붙이면 기존 `DenyInsecureTransport` 가 사라진다 |
| S3 `colab-platform-data-dev` | 라이프사이클에 `backups-30d` 추가 | DB 백업 정리 |
| Budgets | 옛 `credit-burn-50` 삭제 → 예산 2 재구성 | 크레딧을 제외해야 「쓴 금액」이 보인다 |
| IAM (로컬용) | `…-s3-uploader-phj`·`-hsw` 사용자·키·정책 **삭제** · 로컬 버킷 2개 삭제 | 로컬은 파일 폴더 모드로 바뀌어 필요 없어졌다 |

## 배포하려면

1. `infra/dev/build.sh` (arm64 빌드 + 아키텍처 실측) 2. `infra/dev/ship.sh` 3. EC2 에서 `/opt/colab-v2/up.sh`
4. 프론트는 `npm run build` → `ops/deploy_web.py` — 전체는 `docs/DEPLOY.md` 1) 절

## 안 되면

1. **`ops/deploy_doctor.py --env dev`** 를 먼저 돌립니다 — 14 항목 중 어디가 `✗` 인지가 원인의 절반입니다
2. `docs/DEPLOY.md` 3) 절 **증상별 진단표** — 이번 구축에서 **실제로 겪은 22건**이 들어 있습니다

## 일부러 안 한 것

- **미리보기(previews) 실검증** — 배선은 다 서 있지만 **한 번도 안 돌았습니다**(`previews/` 객체 0건).
  미리보기 개발이 예정돼 있어 지금 검증하면 곧 무효가 됩니다
- **기존 staging 내리기** — dev 가 선 지 이틀이고 위 미리보기가 미검증이라 **되돌릴 곳을 남겼습니다.**
  터널을 끄는 것부터 하면 되고, 되돌리는 비용은 없습니다
- **prod** · 도메인 연결 · CI 자동 배포 · ECR · 무중단 배포 — 자리는 `docs/DEPLOY.md` 10) 절에 있습니다

## 자세한 건

`docs/DEPLOY.md` (운영 문서 · 진단 · 재구성 절차) · `infra/dev/README.md` (기계적 절차) ·
`dev-package/PLAN-SoT.md §9` (값과 근거)
