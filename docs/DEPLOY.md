# DEPLOY — CoLAB v2 배포 운영 문서

> **이 문서가 배포의 정문이다.** 반년 뒤 「배포가 안 되는데」로 돌아왔을 때, 이것 하나로 원인을 찾고 고칠 수 있어야 한다.
>
> **기계적 절차의 정본은 `infra/dev/README.md`**(스크립트와 같은 자리에 있어 함께 낡는다). 이 문서는 **왜·무엇이·어디가 고장 나면 어디를 보는가**를 맡는다. 값과 근거는 `dev-package/PLAN-SoT.md §9`.

**지금 서 있는 것** — dev 환경 하나. 주소 `https://d31zgpff2091oh.cloudfront.net`. **prod 는 아직 없다**(정본 `㊻` 가 ⏸, Ted 판정 선행).

---

## 1) 5분 요약 — 지금 배포하려면

개발 기계에서 셋, EC2 에서 하나.

```bash
# ① 이미지 5개를 arm64 로 빌드 → 아키텍처 실측 → tar 로 묶는다
infra/dev/build.sh
#    (안에서 도는 것: docker buildx build --platform linux/arm64 --load
#                     → docker image inspect --format '{{.Architecture}}' 로 arm64 확인
#                     → docker save -o dist/colab-v2-dev-<sha>.tar)

# ② EC2 로 실어 docker load
COLAB_DEV_SSH=ec2-user@<탄력적 IP> \
COLAB_DEV_KEY_FILE=~/.config/colab-platform/colab-platform-dev-key.pem \
  infra/dev/ship.sh

# ③ 프론트 번들 → 웹 버킷
cd frontend && npm run build && cd ../services/core-api
.venv/bin/python ops/deploy_web.py --dist ../../frontend/dist --bucket colab-platform-web-dev
```

```bash
# ④ EC2 위에서 — 마이그레이션 2체인 → 기동 → healthy 대기(fail-closed) → 헬스 본문
/opt/colab-v2/up.sh
```

**끝나면 반드시 `deploy_doctor`** — 6) 절.

> ⚠ **아키텍처 확인을 건너뛰지 않는다.** `build.sh` 가 자동으로 하지만, 손으로 빌드했다면 `docker image inspect` 로 `arm64` 인지 본다. x86 이미지는 EC2(t4g)에서 **아예 안 뜬다**.
> ⚠ **백엔드 코드를 고쳤으면 ①②④ 까지가 배포다.** Vite 는 자동 반영되지만 컨테이너는 아니다.

---

## 2) 설정 레퍼런스

### 2-1. 값을 어디에 두는가 — 세 자리

| 자리 | 무엇 | 왜 거기인가 |
|---|---|---|
| **`compose.yml` 리터럴** | 저장 모드·버킷·리전 (`COLAB_*_STORAGE_MODE=s3` 등) | **치환으로 두면 빠뜨렸을 때 기본 `local` 이 이긴다** — EC2 디스크에 쌓이고 전송 op 가 501 을 내며 FE 가 폴백해 「성공처럼」 보인다 |
| **`/opt/colab-v2/dev.env`** (0600) | 서명 비밀값·자원 상한·이미지 태그 | `up.sh` 가 `--env-file` 로 읽는다 |
| **`/etc/colab/*`** (0600) | **접속 문자열·주체 표·자격 해시** | 값이 아니라 **경로**를 env 로 준다(`*_FILE`) — `docker inspect` 로 값이 새던 사고 이후 규약(`〈121〉-㉯`) |

**AWS 액세스 키는 어디에도 없다.** EC2 는 인스턴스 프로파일(IMDSv2)로 받는다.

### 2-2. core-api

| 변수 | 필수 | 기본값 | 없으면 어떻게 되나 |
|---|---|---|---|
| `COLAB_CORE_DATABASE_URL` (또는 `…_URL_FILE`) | ✅ | — | **기동 거부** |
| `COLAB_CORE_SESSION_SECRET` | ✅ | — | **로그인·다운로드 티켓이 서지 않는다**(500 `DOWNLOAD_UNAVAILABLE`) |
| `COLAB_CORE_CREDENTIALS_FILE` | ✅ | — | 자격 파일이 없으면 기동 거부. **빈 `{}` 는 정상**(계정 0명) |
| `COLAB_CORE_SUBJECTS_FILE` | 선택 | 없음 | 심어 둔 토큰 표. 없으면 그 경로 인증만 안 된다 |
| `COLAB_CORE_STORAGE_MODE` | ✅(배포) | `local` | **모르는 값은 기동 거부.** 안 주면 조용히 `local` — 배포에서 가장 위험한 기본값이라 compose 에 리터럴로 박았다 |
| `COLAB_CORE_S3_BUCKET` · `…_S3_REGION` | s3 모드 ✅ | — | **반쪽 설정(모드만 s3)은 기동 거부** — 의도된 동작 |
| `COLAB_CORE_UPLOAD_DIR` | local 모드 ✅ | — | local 모드에서 없으면 기동 거부 |
| `COLAB_CORE_VIZ_BASE_URL` · `COLAB_CORE_VIZ_SERVICE_TOKEN` | ✅ | — | **둘 다** 있어야 미리보기 중계가 선다. 하나만 있으면 **전량 503** |
| `COLAB_CORE_AI_BASE_URL` | 선택 | compose 내부 주소 | |
| `COLAB_CORE_SESSION_TTL_MINUTES` | 선택 | `720` | |
| `COLAB_CORE_LOGIN_MAX_FAILURES` · `…_WINDOW_SECONDS` | 선택 | `5` · `900` | |
| `COLAB_CORE_UPLOAD_TTL_HOURS` | 선택 | `24` | |

### 2-3. pipeline-worker · viz-render · ai-service

| 변수 | 단위 | 없으면 |
|---|---|---|
| `COLAB_PIPELINE_DB_URL(_FILE)` | worker | 기동 거부 |
| `COLAB_WORKER_STORAGE_MODE` / `…_S3_BUCKET` / `…_S3_REGION` / `…_WORKDIR` | worker | 모르는 값·반쪽 설정은 기동 거부 |
| `COLAB_WORKER_UPLOAD_DIR` | worker(local) | 없으면 기동 거부 — **바이트를 못 여는 워커는 「형식 인식 실패」로 위장한다** |
| `COLAB_VIZ_SOURCE_MODE` / `…_S3_*` / `…_WORKDIR` | viz | 같음 |
| `COLAB_VIZ_WORK_MAX_BYTES` | viz | **3상태**: 숫자 · `none`(명시 무제한) · **미설정 = 기동 거부** |
| `COLAB_VIZ_PREVIEW_SINK` / `…_PREVIEW_S3_PREFIX` / `…_PREVIEW_URL_BASE` | viz | 싱크가 안 서면 미리보기 산출물이 갈 곳이 없다 |
| `COLAB_VIZ_SERVICE_TOKEN` · `COLAB_VIZ_TILE_SIGNING_SECRET` | viz | 없으면 기동 거부 |
| `COLAB_AI_DB_URL(_FILE)` | ai | 기동 거부 |
| `OPENAI_API_KEY` · `COLAB_MODEL_*` · `COLAB_AI_QUERY_INTERPRETATION` | ai | 선택 — **AI 없이도 v2 는 완결된 제품이다** |

### 2-4. 환경별 한 벌

| 환경 | env 파일 | DB | 저장 백엔드 |
|---|---|---|---|
| **로컬** | `~/.config/colab-platform/local.env` | 도커 `colab_local_pg` | **파일 폴더(`local`)** — S3 안 쓴다 |
| **dev** | EC2 `/opt/colab-v2/dev.env` + `/etc/colab/*` | RDS `colab-platform-dev-db`(프라이빗) | S3 `colab-platform-data-dev` |
| **prod** | 아직 없음 | — | — |

**새 개발자에게 그대로 전할 세 문장** — *"로컬은 S3 를 쓰지 않는다. 파일 폴더 모드가 기본이고 `local.env` 에 버킷 설정이 없는 것이 정상이다. dev·prod 버킷은 배포된 서버만 쓴다."*

> **임시로 다른 환경에 붙어야 하면 파일을 통째로 바꿔 끼우고 끝나면 되돌린다. 부분 변경 금지** — 반쪽 설정은 가장 찾기 어려운 고장을 만든다.

---

## 3) 증상별 진단표

> **첫 줄은 언제나 이것이다 — `deploy_doctor` 를 먼저 돌린다**(6) 절). 어느 항목이 `✗` 인지가 원인의 절반이다.

### 3-1. 이번 구축에서 실제로 겪은 것

| 증상 | 확인할 곳 | 원인 · 조치 |
|---|---|---|
| **SSH 가 시간 초과.** 보안그룹·라우팅·서브넷이 다 맞다 | 인스턴스 요약의 **`탄력적 IP 주소`** 칸 | 탄력적 IP 를 붙이면 주소가 바뀐다. `퍼블릭 IPv4 주소` 칸에는 처음 자동 할당된 것이 남아 보인다 |
| **`dnf`·`curl` 이 멈춘다. DNS 는 되고 SSH 도 된다** | 앱 보안그룹의 **아웃바운드** | 아웃바운드가 비어 있다. SG 는 상태 저장이라 *들어온* 연결의 응답만 나가고, **먼저 거는 연결은 막힌다.** DNS 는 VPC 내부 리졸버라 영향이 없어 「네트워크는 되는데」로 보인다 → `모든 트래픽 / 0.0.0.0/0` |
| `dnf install` 이 `[Errno 2] … .rpm` | — | 앞선 설치가 끊겨 캐시가 깨졌다 → `dnf clean all && rm -rf /var/cache/dnf` |
| `docker compose` 가 없다 | — | **AL2023 저장소에 컴포즈 플러그인이 없다.** 릴리스 바이너리를 `/usr/libexec/docker/cli-plugins/` 에 직접 놓는다 |
| **cron 등록이 「No such file or directory」** | `/etc/cron.d` | **AL2023 은 cron 을 기본으로 안 깐다** → `dnf install cronie && systemctl enable --now crond`(`install-cron.sh` 가 스스로 한다) |
| `/etc/colab/<파일>` **Permission denied** — 소유자는 맞는데 | 디렉터리 모드 | 디렉터리가 `700 root` 면 안의 파일을 못 연다. 컨테이너(uid 10001)에는 **파일 단위로** 마운트한다 |
| **`pg_dump` 가 `query would be affected by row-level security policy`** | RLS FORCE | 소유자도 정책에 걸린다. **백업 전용 `colab_backup`(BYPASSRLS) 롤로 뜬다** — 7) 절 |
| **원격 스크립트의 뒷부분이 조용히 사라진다** | `ssh 'bash -s' <<EOF` | 스크립트 안의 `docker run -i` 가 **heredoc 의 나머지를 stdin 으로 먹는다.** 파일로 `scp` 해서 실행한다 |
| `ast.parse: source code string cannot contain null bytes` | 맥에서 보낸 `*.py` | 맥 `tar` 가 **AppleDouble(`._*`)** 을 딸려 보낸다(점 파일이라 `ls` 에 안 보이는데 `*.py` 글롭에 걸린다) → `COPYFILE_DISABLE=1 tar` 또는 `find -name '._*' -delete` |
| **vite 빌드가 `styleText` 없음으로 죽는다** | `node -v` | **Node 22 미만.** 기계에 Node 가 둘일 수 있다 — `PATH` 의 것과 brew Cellar 의 것 |
| `npm` 자체가 모듈을 못 찾고 죽는다 | `NODE_OPTIONS` | 없는 파일을 preload 하고 있다 → `env -u NODE_OPTIONS npm …` |
| **RDS 생성이 「backup retention exceeds free tier」** | 백업 보존 기간 | Free Plan 상한. `1`일로 낮춘다 — 30일치는 자체 백업이 맡는다(7) 절) |
| 콘솔 목록과 S3 실물이 다르다(수명 주기) | API | **판정은 콘솔 화면이 아니라 실호출로만 한다** |
| **폴더를 올리려는데 눌러도 아무 일이 없다** | 드롭존 | **폴더는 드래그 앤 드롭으로만 받는다.** 파일 선택창으로는 못 고른다(인풋에 `webkitdirectory` 를 붙이면 낱개 선택이 죽는다) — 화면 문구가 그 말을 한다 |
| 업로드가 실패했는데 **아무 메시지가 없다** | — | 2026-09-01 이전 판의 증상. 접수 실패가 무음이었다 → 지금은 드롭 카드 아래 배너 + [다시 시도] |
| **S3 에 폴더가 안 보인다** | 버킷 키 | **정상이다.** 키는 `uploads/<uploadId>/<fileId>` 이고 폴더 경로는 **원장 메타**(`d5`→`d3_file.relative_path`)로 산다 |
| vitest 가 `ERR_REQUIRE_ESM` 로 안 뜬다 | `node -v` | Node 22.12 미만 → `NODE_OPTIONS=--experimental-require-module` |
| **한글 파일명만 「계획에 있는 파일이 선택에 없어요」** | 이름 정규화 | **맥은 NFD, 서버는 NFC.** 프론트가 정규화를 안 하면 같은 파일을 못 찾는다. 영문 이름은 두 형태가 같아 **한글에서만 터진다** → `normalizeName.ts`(서버 `objectpath.py` 와 같은 규칙) |
| **실패했는데 「올리다 만 것」이 여러 개 쌓인다** | 재시도 방식 | 재시도가 **새 전송**이면 시도마다 원장이 는다. 실패는 `TransferInterrupted(uploadId)` 로 나와야 하고 재시도는 **재개**여야 한다 |
| **올리다 만 것이 어디에도 안 보인다** | 미완결의 종류 | 두 가지다 — 전송 미완(72h·서버 목록)과 **등록 미완**(24h·목록 op 없음, 브라우저가 기억). 메인 카드가 둘을 합쳐 보여준다 |
| **로그인돼 보이는데 모든 요청이 401** | 세션 수명 | 세션은 **12시간**이다. `AuthGate` 는 `/me` 를 토큰이 바뀔 때만 부르므로 마운트 뒤 만료를 몰랐다 → `client.ts` `onResponse` 가 401 에 토큰을 버린다 |
| **자격 파일을 바꿨는데 옛 비밀번호가 그대로** | 컨테이너 안 파일의 sha256 | **파일 단위 바인드 마운트는 inode 를 붙든다.** `install`·`mv`·`set-password.py` 는 새 inode 를 만들므로 컨테이너는 **옛 파일을 계속 본다**. 호스트와 컨테이너에서 `sha256sum` 을 대조해 확인하고 `docker restart` 로 다시 붙인다 |
| **자격 파일 교체 뒤 로그인이 전부 401** | `ls -ln /etc/colab` | 컨테이너는 **uid 10001** 로 돈다. `root:root` 0600 으로 깔면 앱이 못 읽고, 「계정이 없다」와 **똑같은 401** 이 난다(있고 없고를 안 가르는 게 옳은 설계다). 옆 파일들과 같은 `10001:10001` 로 맞춘다 |

### 3-2. 아직 안 겪었지만 나올 만한 것

| 증상 | 확인할 곳 | 원인 |
|---|---|---|
| 배포 후에도 옛 화면 | `index.html` 캐시 헤더 | `no-cache` 가 안 붙었다(`deploy_web.py` 가 붙인다) |
| 새로고침하면 404 | CloudFront 함수 연결 | SPA 되쓰기 함수가 기본 동작에 안 붙었거나 **게시(publish)를 안 했다** |
| **화면은 뜨는데 API 가 전부 실패** | CloudFront 오리진 B 주소 ↔ EC2 실제 주소 | 탄력적 IP 가 풀렸다 · 앱이 안 떠 있다 · 보안그룹 8000 |
| **API 가 전부 401** | `/api/*` 동작의 원본 요청 정책 | `AllViewer` 가 아니면 `Authorization` 헤더가 잘린다 |
| API 응답에 남의 데이터 | `/api/*` 캐시 정책 | `CachingDisabled` 여야 한다 |
| 폴더 골라도 아무 일 없음 | `window.isSecureContext` | HTTPS 아님 |
| 업로드가 CORS 에러 | 데이터 버킷 CORS | 오리진 미등록 · **스킴/포트 불일치**(`https://` 와 `http://` 는 다른 오리진이다) |
| 큰 파일이 중간부터 403 | 프리사인드 TTL | 임시 자격증명 만료. 클램프 확인 |
| 서버가 기동하다 죽음 | 컨테이너 로그 **첫 줄** | 필수 환경변수 누락 — **의도된 동작이다** |
| 미리보기가 전량 503 | `COLAB_CORE_VIZ_BASE_URL` **와** `…_SERVICE_TOKEN` | 둘 중 하나만 있으면 중계가 안 선다 |

---

## 4) AWS 자원 목록 — 그리고 지울 때의 순서

**리전은 전부 `ap-northeast-2`(서울).**

| 자원 | 이름 | 의존 |
|---|---|---|
| CloudFront 배포 | `colab-platform-dev` · ID `E7J6EMHMYCTSK` · `d31zgpff2091oh.cloudfront.net` | 오리진 3 · 함수 1 |
| CloudFront 함수 | `colab-platform-dev-spa-rewrite` | 기본 동작에 연결 |
| S3 데이터 버킷 | `colab-platform-data-dev` | 버킷 정책이 배포 ARN 을 가리킨다 |
| S3 웹 버킷 | `colab-platform-web-dev` | OAC |
| EC2 | `colab-platform-app-dev` · `i-0bf4fad1ead85071d` (`t4g.small`, arm64) | 서브넷·SG·역할·EIP |
| 탄력적 IP | `54.116.191.208` | ⚠ **EC2 를 종료해도 남는다 — 따로 반환한다** |
| RDS | `colab-platform-dev-db` (PG16, `db.t4g.micro`) | 서브넷 그룹·SG · **삭제 방지 ON** |
| DB 서브넷 그룹 | `colab-platform-dev-db-subnet-group` | 프라이빗 서브넷 2 |
| VPC | `colab-platform-dev-vpc` · `vpc-010f7840e476df2ae` (`10.0.0.0/16`) | 서브넷 4 · IGW · 라우트 테이블 · S3 게이트웨이 엔드포인트 |
| 서브넷 | public1/2 · private1/2 (`/20`) | |
| 보안그룹 | `colab-platform-app-dev-sg` · `colab-platform-db-dev-sg` | db 가 app 을 **이름으로** 참조 |
| IAM 정책 | `colab-platform-s3-dev-policy`(운영자) · `colab-platform-app-dev-policy`(서버) | |
| IAM 역할 | `colab-platform-app-dev-role` | EC2 인스턴스 프로파일 |
| IAM 사용자 | `colab-platform-s3-uploader-dev` + 액세스 키 1 | **로컬 도구 전용.** 키는 `~/.config/colab-platform/dev.env`(0600) · 발급 csv 백업은 저장소 **밖**(0600) |
| 키 페어 | `colab-platform-dev-key` | |
| 예산 | `colab-platform-credit-burn`(연 $120) · `colab-platform-monthly-usage`(월 $50) | |

**지우는 순서** — 안에서 밖으로. 순서를 어기면 「종속성이 있다」로 거부된다.

```
1. CloudFront 배포 비활성화 → 배포 완료 대기 → 삭제   (가장 오래 걸린다)
2. CloudFront 함수 삭제
3. S3 버킷 2개 — 비우기(Empty) → 삭제
   ⚠ 버저닝이 켜져 있어 「비어 보여도」 거부된다. Empty 를 먼저.
4. EC2 종료
5. 탄력적 IP 연결 해제 → 릴리스        ← 잊으면 계속 요금이 나간다
6. RDS — 삭제 방지 끄기 → 삭제 (최종 스냅샷 여부 결정)
7. DB 서브넷 그룹 삭제
8. 보안그룹 — db 먼저, app 나중 (db 가 app 을 참조한다)
9. VPC 삭제 (서브넷·IGW·라우트 테이블이 함께 간다)
10. IAM — 사용자(키 포함) → 역할 → 정책
11. 키 페어 삭제
12. 예산 삭제
```

### 4-1. dev DB 안에 든 것

로컬과 같은 시드다 — **연구실 2**(`고려대학교 수문학연구실` · `B 연구실`) · 프로필 2 · **계정 4**
(`admin`·`colab`·전창현 교수·B 교수) · 역할 4 · 권한 스위치 4. **예제 데이터셋은 안 옮겼다.**
스키마 = platform head `0009_file_management`(25테이블) · ai head `0005_k2b_concept_graph_seed`(6테이블) ·
**RLS 23/23 FORCE** · `pg_trgm`.

로그인 자격(계정 이름 · scrypt 해시만 저장)은 저장소 **밖** `~/.config/colab-platform/dev-secrets/` 에 있다.
회전은 `§6-5`.

> **기본 VPC(`172.31.0.0/16`)는 우리 것이 아니다.** AWS 가 계정에 자동으로 넣은 것이고, 무료다. 지우지 않는다.

---

## 5) 재구성 절차 — 빈 계정에서 여기까지

**이 절만 보고 끝까지 갈 수 있어야 한다.** (prod 를 세울 때도 이름의 `dev` 를 `prod` 로 바꾸고 이 절을 따른다.)

### 5-1. 예산 (자원을 켜기 전에)

**⚠ 새 프리 티어(Free Plan) 계정이면 크레딧이 소진될 때 「청구」가 아니라 「계정 정지」다.** 실지출 예산으로는 아무것도 못 잡는다.

- **누적 예산** — 기간 `연별` · 금액 = 크레딧 총액 · **범위 옵션 → 특정 AWS 비용 차원 필터링 → 차원 `요금 유형` → `Excludes` → `Credit, Refund`** · 알림 50/80/90%
  - **크레딧을 제외해야 「쓴 금액」이 보인다.** 포함하면 차감되어 $0 이 되고 알림이 영영 안 온다
- **월간 예산** — 급증 감지용. 같은 필터
- 「작업 연결」(자동 정지)은 걸지 않는다 — 알림만 받고 판단은 사람이 한다

### 5-2. S3 (계획서 G4-c)

1. **IAM 정책** `colab-platform-s3-<환경>-policy` — 내용은 `infra/dev/iam/user-policy.json`. **와일드카드 금지**(`…-data-*` 는 prod 까지 dev 열쇠에 연다)
2. **IAM 사용자** + 액세스 키(콘솔 로그인 없음) → 키는 **저장소 밖** `~/.config/colab-platform/<환경>.env` (0600)
3. **데이터 버킷** `colab-platform-data-<환경>` — 서울 · 퍼블릭 차단 4개 유지 · **버저닝 Enable** · SSE-S3 + Bucket Key · **이름에 점(`.`) 금지**
4. **버킷 정책** — `DenyInsecureTransport` (CloudFront 문장은 배포가 생긴 뒤 **합쳐서** 넣는다)
5. **CORS** — 그 환경의 실오리진만. `PUT/GET/HEAD` · ExposeHeaders 에 **`ETag` 필수**(없으면 멀티파트 완결이 실패한다)
6. **수명 주기 3** — `abort-incomplete-multipart-7d` · `expire-noncurrent-30d` · `backups-30d`(접두사 `_ops/backups/`). **전체 만료 규칙은 걸지 않는다**
7. **웹 버킷** `colab-platform-web-<환경>` — 퍼블릭 차단 · CORS·수명 주기·버저닝 **없음**
8. **검증** — `ops/s3_doctor.py` **10/10** · `ops/s3_smoke.py` 전 항목

### 5-3. 네트워크 (G4-d)

VPC `10.0.0.0/16` · AZ 2 · 퍼블릭 2 · 프라이빗 2 · **NAT 게이트웨이 `없음`**(월 $45 갈림길) · S3 게이트웨이 엔드포인트.
퍼블릭 서브넷의 **퍼블릭 IPv4 자동 할당 켜기**. 보안그룹 둘 — **app 을 먼저**(db 가 app 을 참조한다).

### 5-4. RDS (G5)

DB 서브넷 그룹(**프라이빗 2개** — CIDR 을 보고 고른다) → PostgreSQL **16** · `db.t4g.micro` · 20 GiB · **스토리지 자동 조정 끄기** · 단일 AZ · **퍼블릭 액세스 아니오** · db-sg · **삭제 방지 켜기** · **초기 DB 이름 비움**.

### 5-5. EC2 (G6)

역할(`role-policy.json`) → 키 페어 → AL2023 **arm64** · `t4g.small` · 퍼블릭 서브넷 · app-sg · **IAM 인스턴스 프로파일 지정** · **IMDSv2 필수 · 홉 제한 `2`** → 탄력적 IP 연결.

EC2 준비: 스왑 4 GB · Docker · compose 플러그인(수동) · `postgresql16` · `/opt/colab-v2` · `/etc/colab`(700).

DB 부트스트랩: `prep` → `roles` → (마이그레이션) → `app-grants` → **`backup-role`** → `verify`.

### 5-6. 프론트·CloudFront·CORS (G7~G9)

`deploy_web.py` → 배포 생성(웹 버킷 OAC · SPA 함수 · **WAF 비활성화**) → 오리진 B(EC2 `:8000` HTTP · 응답 60s) + 동작 `/api/*`(**CachingDisabled · AllViewer · 전 메서드**) → 오리진 C(데이터 버킷 OAC) + 동작 `/previews/*` → **데이터 버킷 정책에 CloudFront 문장 합치기** → **CORS 에 배포 주소 추가**.

### 5-7. 백업·정리 (G10)

`backup.sh` + `install-cron.sh`. **복원 실습까지 해야 끝이다** — 6) 절.

---

## 6) 운영 작업

### 6-1. 확인 — `deploy_doctor`

**EC2 위에서 한 번에 14 항목을 돌린다.** 시크릿은 **파일 단위** 마운트(디렉터리가 700 이라 컨테이너가 못 지난다), 운영자 키는 `--env-file` 로 잠깐 넘기고 **실행 직후 지운다**.

```bash
docker run --rm --network host --env-file /tmp/op.env \
  -v /opt/colab-repo:/repo:ro \
  -v /etc/colab/core-database.url:/s/core.url:ro \
  -v /etc/colab/ai-db.url:/s/ai.url:ro \
  colab-v2/core-api:dev python /repo/services/core-api/ops/deploy_doctor.py --env dev \
    --endpoint https://<배포>.cloudfront.net \
    --app-base http://127.0.0.1:8000 --worker-base http://127.0.0.1:8001 \
    --viz-base http://127.0.0.1:8100 --ai-base http://127.0.0.1:8200 \
    --db-url-file /s/core.url --ai-db-url-file /s/ai.url \
    --bucket colab-platform-data-dev --web-bucket colab-platform-web-dev
```

> ⚠ **맥에서 터널로 돌리면 ⑫ 가 red 다** — DB 호스트가 `127.0.0.1` 로 보여 「환경이 다르다」로 판정된다. **검사가 옳게 동작한 것이니 무르지 않는다.** 위 방식으로 돌린다.
> ⚠ **부분 실행 둘을 합쳐서 green 이라 하지 않는다.** `─ 0` 이 나온 한 번의 결과만 근거다.

### 6-2. 재배포 · 되돌리기

재배포 = 1) 절. 되돌리기 = `dev.env` 의 `COLAB_IMAGE_TAG=dev-<직전 sha>` 로 바꾸고 `up.sh`. **마이그레이션은 되돌리지 않는다**(`0009` 처럼 백필이 든 판은 downgrade 가 값을 잃는다).

### 6-3. 백업과 복원

- **두 겹이다** — ⑴ RDS 자동 백업 **1일**(Free Plan 상한) ⑵ **`backup.sh` 가 하루 1회 `pg_dump` → S3 `_ops/backups/dev/`, 30일 보관**(수명 주기가 강제)
- 손으로: `sudo /opt/colab-v2/backup.sh` · 로그 `/var/log/colab-backup.log`
- **복원 실습(정기적으로 한다 — 해보지 않은 백업은 백업이 아니다)**

```bash
# ① 백업 하나 내려받아 풀기 (운영자 키로)  ② 일회용 PG 에 복원 — RDS 를 덮어쓰지 않는다
docker run -d --rm --name restore_probe -e POSTGRES_PASSWORD=probe -e PGDATA=/pgdata \
  --tmpfs /pgdata:rw,size=512m --tmpfs /var/run/postgresql:rw postgres:16-alpine
docker exec restore_probe psql -U postgres -c "CREATE DATABASE restored"
docker exec -i restore_probe psql -U postgres -v ON_ERROR_STOP=1 -d restored < platform.sql
# ③ 대조 — 테이블 수 · alembic head · 연구실/계정 수
docker rm -f restore_probe
```

> ⚠ **일회용 인스턴스는 `--rm` + tmpfs + `PGDATA` 지정 + 호스트 포트 미공개.** 이 호스트는 `--tmpfs` 와 `PGDATA` 가 없으면 `initdb` 가 죽는다.

### 6-3-1. 만료 전송 정리 — 무엇이 지워지나

**별도 잡이 아니라 지연 정리다** — 업로드 op 가 불릴 때 그 자리에서 돈다. 업로드가 없는 날에도 돌게
`cron ②` 가 하루 한 번 읽기 전용 op 를 부른다(UTC 19:20).

대상 = **이어올리기 창 72시간이 지났는데 완결되지 않은 전송**. 지우는 것 = 멀티파트 abort · 이미 올라간 객체 삭제 ·
원장 행 삭제. **원장이 아는 것만 지운다 — 버킷 루트를 스캔하지 않는다.** S3 정리가 실패하면 원장 행을 남겨 다음에 다시 시도한다.

**2026-09-01 실측** — 버려진 전송 하나(객체 1 · 미완결 멀티파트 1 · 원장 전송 1 · 파일 2)가 호출 한 번에 **전부 0** 이 됐고,
**다른 전송 3건과 백업 5건은 무손상**이었다.

> ⚠ 손으로 만료시켜 시험하려면 **`created_at` 도 함께 과거로** 민다 — `CHECK (expires_at > created_at)` 가 막는다.
> ⚠ 결과를 소유자 롤로 세면 **경계 미설정 탓에 0 이 나와** 「지워졌다」로 오독한다. 전수 확인은 `colab_backup` 으로.

### 6-4. SSH · DB 조회 · 로그

```bash
ssh -i ~/.config/colab-platform/colab-platform-dev-key.pem ec2-user@<탄력적 IP>
docker logs --tail 50 colab_v2_dev_core_api      # 단위 이름은 colab_v2_dev_*
docker stats --no-stream                          # 메모리
sudo cat /etc/cron.d/colab-dev                    # cron 확인 (시각은 UTC)
```

- **IP 가 바뀌면 SSH 가 막힌다.** 보안그룹 22번 규칙의 소스를 `내 IP` 로 다시 지정한다. **사람마다 규칙 하나 · 설명에 누구인지 적는다**(안 적으면 나중에 어느 줄이 누구 것인지 몰라 못 지운다). `0.0.0.0/0` 금지
- **DB 조회는 환경마다 다르다** — **dev 는 터널로 로컬에서**(`ssh -L 15432:<rds>:5432 …`), **prod 는 SSH 로 들어가 그 안에서**
- **인스턴스를 오래 중지할 때는 탄력적 IP 를 릴리스한다** — 꺼져 있어도 주소값이 나간다

### 6-5. 로그인 비밀번호 회전

**평문은 어디에도 안 들어간다** — 자격 파일에는 scrypt 해시만 있다. 바꾸는 자리는 하나다.

```bash
cd services/core-api
F=~/.config/colab-platform/dev-secrets/credentials.json
cp "$F" "$F.bak-$(date +%Y%m%d%H%M)"                      # 되돌릴 자리를 먼저 만든다
printf '<새 비밀번호>\n' | .venv/bin/python ops/set-password.py --file "$F" --name admin
#   ⚠ 비밀번호를 **인자로 주지 않는다** — argv 는 `ps` 와 셸 히스토리에 남는다. 표준입력이다.

scp -i <키> "$F" ec2-user@<IP>:/tmp/creds.json
ssh -i <키> ec2-user@<IP> '
  sudo install -o 10001 -g 10001 -m 0600 /tmp/creds.json /etc/colab/credentials.json && rm -f /tmp/creds.json
  sudo docker restart colab_v2_dev_core_api'          # 기동 시 한 번만 읽는다 (`main.py:67`)
```

**확인은 세 걸음이다. 하나라도 빼면 「바꿨는데 안 바뀐」 상태가 조용히 남는다.**

1. **소유자** — `sudo ls -ln /etc/colab/credentials.json` 이 `10001 10001` 인가
2. **컨테이너가 새 파일을 보는가** — 호스트와 컨테이너의 `sha256sum` 이 같은가 (파일 바인드 마운트는 **inode 를 붙든다**)
3. **실제로 로그인되는가** — `POST /api/v1/sessions` 로 **201** 과 토큰. 옛 비밀번호가 **401** 인 것까지 본다

> 로그인 입력은 이메일이 아니라 **`accountName`** 이다(`SessionCredentials` — `accountName`＋`password` 또는 `accessCode`).
> 2·3 을 빼면 **1번만 맞고 나머지가 옛것**인 상태가 생기고, 「계정 없음」과 「비밀번호 틀림」이 **같은 401** 이라 원인이 안 보인다.

---

## 7) 설계 요약 — 왜 이렇게 되어 있나

| 무엇 | 왜 |
|---|---|
| **NAT 게이트웨이가 없다** | 월 $45. EC2 가 퍼블릭 서브넷에 있어 IGW 로 직접 나간다. RDS 는 밖으로 나갈 일이 없다 |
| **nginx 가 없다** | 라우팅은 CloudFront 가 한다. 컨테이너 하나를 줄이면 관리할 설정도 하나 준다 |
| **CloudFront 를 쓴다** | 도메인 없이 **HTTPS** 를 얻는다. HTTPS 가 없으면 브라우저의 `crypto.subtle`·디렉터리 선택이 보안 컨텍스트 밖이라 **이어올리기가 조용히 죽는다** |
| **SPA 폴백이 오류 응답이 아니라 함수다** | 오류 응답 치환은 배포 **전역**이라 `/api/*` 의 진짜 오류 JSON 까지 HTML 로 바꾼다 |
| **IAM 역할(인스턴스 프로파일)** | 서버에 액세스 키를 두지 않는다. 서버가 털려도 키가 새지 않는다. env 에 `AWS_ACCESS_KEY_ID` 를 두면 공급자 순서상 키가 먼저 잡혀 역할이 무의미해진다 |
| **IMDSv2 홉 제한 2** | 앱이 컨테이너 안에서 도니 네트워크를 한 번 더 건넌다. 1 이면 자격증명을 못 받고 **권한 문제처럼 보이는 고장**이 된다 |
| **비밀은 값이 아니라 `_FILE` 경로** | `docker inspect` 로 값이 샜던 사고 |
| **백업이 두 겹** | RDS 자동 백업은 Free Plan 에서 1일뿐이다. 30일치는 자체 잡이 든다 |
| **백업 전용 `colab_backup`(BYPASSRLS) 롤** | RLS 가 **FORCE** 라 소유자도 정책에 걸리고, 경계가 없으면 `current_lab_id()` 가 NULL 이라 **어떤 롤도 전수를 못 읽는다**(RDS 마스터조차). 백업은 본질적으로 전수를 읽어야 하므로, 그 예외를 **이름 붙은 읽기 전용 롤 하나로 드러내 놓고** 만들었다. ⚠ **이 자격 파일이 새면 연구실 경계가 통째로 뚫린다** — EC2 `root` 소유 0600 |
| **워커·viz 가 S3 를 「내려받아」 읽는다** | 감지·파싱이 로컬 경로와 랜덤 액세스를 전제한다. 작업 디렉터리는 **캐시이지 상태가 아니다** |
| **arm64(t4g)** | 같은 값에 더 싸다. `pyhdf` 만 휠이 없어 2단계 빌드로 소스 컴파일한다 |

---

## 8) 부록 — 만들면서 나온 질문들 (왜 다른 길을 안 갔나)

**「결정」은 자원에 흔적이 남지만 「왜 그렇게 안 했는지」는 어디에도 안 남는다.**

| 물음 | 안 간 길 | 왜 |
|---|---|---|
| x86 으로 가면 `pyhdf` 문제가 없지 않나 | x86 EC2 | 환경당 월 +$3 이고, HDF4 를 포기하면 정본 포맷 4종이 깨진다. 2단계 빌드로 닫혔고 **실제 MODIS 자료 8건으로 검증됐다** |
| 백업을 연구실별로 나눠 뜨면 BYPASSRLS 가 필요 없지 않나 | 연구실별 분할 덤프 | **새 연구실이 목록에서 빠지면 조용히 누락된다** — 백업에서 가장 나쁜 실패 모양. 복원 절차도 복잡해진다 |
| RDS 스냅샷으로 대체하면? | 스냅샷 | `deploy_doctor` ⑭ 를 만족 못 해 **검사를 무르게 된다.** 복원이 「새 인스턴스 생성」이라 무겁다 |
| WAF 를 켜는 게 안전하지 않나 | WAF | 요청이 없어도 월 $5~10 이 고정으로 나간다. 크레딧이 $120 뿐이다. **prod 에서는 다시 판단한다** |
| 인스턴스를 크게 잡는 게 낫지 않나 | `t4g.medium` | Free Plan 이 막았다. **실측으로 충분함이 확인됐다**(55 MB·8파일 처리에 컨테이너 4 합 268 MiB · 스왑 사용 0). **렌더 부하는 아직 안 재봤다** |
| 미리보기까지 확인해야 인수 아닌가 | 지금 검증 | **추가 개발이 예정돼 있어 지금 검증하면 곧 무효가 된다.** 다음 회차로 이월 — 9) 절 |
| 콘솔이 준 버킷 정책을 그냥 붙이면? | 「정책 복사」 그대로 | **기존 `DenyInsecureTransport` 가 사라지고 `Resource` 가 버킷 전체가 된다** — 미리보기만 열려던 구멍으로 업로드 원본까지 나간다 |
| 로컬 비밀번호를 dev 에도 쓰면 편하지 않나 | 재사용 | G8 에서 CloudFront 가 붙으면 이 환경이 **인터넷에 열린다** |

---

## 9) 기계마다 다른 것 — **이 표가 정본이다**

배포는 두 사람 다 할 수 있어야 한다. **재배포 절차를 어디에 또 쓰지 말고 이 절을 가리킨다.**

| | 맥 | 윈도우 |
|---|---|---|
| **이미지 빌드** | **같다** — `docker buildx build --platform linux/arm64` | **같다.** 네이티브가 아니라 QEMU 라 느리다 |
| **아키텍처 확인** | **같다** — `docker image inspect --format '{{.Architecture}}'` → `arm64` | **같다. 여기가 윈도우에서 진짜로 걸리는 자리다** |
| **키 파일 권한** | `chmod 600` | **`icacls … /inheritance:r /grant:r "%USERNAME%:R"`** — `chmod` 는 NTFS 에 반영되지 않고, 윈도우 OpenSSH 는 ACL 을 본다. 그대로 두면 `UNPROTECTED PRIVATE KEY FILE` 로 **접속이 거부된다** |
| **`.sh` 실행** | 그대로 | **Git Bash 또는 WSL.** `.gitattributes` 에 `*.sh text eol=lf` 가 있어야 한다 |
| **파이썬** | `python3` | `python` |
| **홈 경로** | `~/.config/colab-platform/` | PowerShell `$HOME\.config\colab-platform\` · Git Bash 는 `~` 그대로 |
| **압축해서 보내기** | **`COPYFILE_DISABLE=1 tar`** — 안 그러면 AppleDouble(`._*`)이 딸려 간다 | 해당 없음 |
| **`.env` 작성** | **둘 다 EC2 위에서.** 로컬에서 만들어 올리지 않는다(CRLF) ||

> **다른 것은 이 표가 전부다.** `ssh`·`scp` 는 윈도우 10/11 에 내장이다.
> **로컬 개발은 아키텍처와 무관하다** — `postgres:16-alpine` 은 멀티아치고 프론트·백엔드는 네이티브로 돈다. **아키텍처가 걸리는 건 배포 이미지뿐이다.**

---

## 10) 아직 안 한 것 — 정직하게

| 항목 | 상태 | 다음에 무엇부터 |
|---|---|---|
| **S3 고아 바이트** | ⛔ 치우는 주체 없음 — **실측 3건 · 25.3 MB**(2026-09-02) | 워커 만료가 DB 행만 지운다. 워커의 `UploadBlobPort` 는 **읽기 Port** 라 삭제를 얹으면 정체가 바뀐다(로컬 모드는 소유 경계도 넘는다) → **별도 WU**. 판별식 = `d3_dataset`·`d5_upload`·열린 전송 **셋 다** 없어야 고아 |
| **본체 전송 진행률 「문구」** | 🟧 **막대는 섰다**(`§D.7 ①` 근거 · 문구 없음). `§E.2` 의 상태 문구 행은 정본 개정 대기 | Ted 판정 뒤 문구를 붙인다 |
| **미리보기(previews) 실검증** | ⛔ **한 번도 안 돌았다.** `previews/` 객체 0건 | 배선은 다 서 있다(CloudFront 동작 · 버킷 정책 · viz `previewSink=s3` · 역할 `PreviewsPut` · 프로브 왕복 200 — **사람이 놓은 객체로만** 확인). 미리보기 개발이 끝난 뒤 ⑴ 업로드→렌더→객체 생성 ⑵ 화면 표시 ⑶ **큰 래스터 렌더 메모리 실측**(남은 유일한 사이징 미지수) |
| **prod** | ⏸ 정본 `㊻` — **Ted 판정 선행** | 5) 절만 보고 세운다. 그것이 이 문서의 인수 시험이다 |
| **동료(hsw) SSH 규칙** | 없음 | 보안그룹 22번에 규칙 추가 · 설명에 `hsw` |
| **가격 분류** | 전체 엣지 | `PriceClass_200` 으로 낮출 수 있다 |
| **소스맵** | dev 는 올린다 | **prod 는 빼는 쪽이 기본** — Ted 판정 |

---

## ⏰ 이 계정의 마감

**Free Plan 이다. 먼저 오는 쪽에서 무료 이용이 끝나고 dev 가 정지된다.**

- **크레딧 소진** — 추정 **2026-11~12월** (예산 `colab-platform-credit-burn` 이 50/80/90% 에서 알린다)
- **무료 플랜 기간 만료 — 2027-02-22** (날짜라 **예산이 못 잡는다. 달력으로 챙긴다**)

**유료 전환 시점을 미리 정해 두지 않으면 어느 날 그냥 멈춘다.**
