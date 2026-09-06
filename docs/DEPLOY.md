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
| **RDS 생성이 「backup retention exceeds free tier」** | 백업 보존 기간 | Free Plan 상한이었다. ⭑ **⟨해소 2026-09-06⟩ 유료 전환으로 풀렸다** — **7일 선택 가능**(콘솔 실측). prod 는 7일로 세운다(`〈372〉`-㉯ — 이것이 시점 복구 관문의 열쇠다). ／ 종전 ~~`1`일로 낮춘다~~ |
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

⭑ **⟨증보 2026-09-06 · `〈372〉`⟩ 두 벌이 됐다 — 아래 표는 dev 이고, prod 는 그 아래 절이다.**
이름 규칙이 **접미사로만 갈린다**(`-dev` / `-prod`) — `deploy_doctor` 의 「환경 짝」 검사(⑫)가
그 접미사로 「다른 환경의 벌을 보고 있지 않은가」를 판정하므로 **규칙을 깨지 않는다.**

### 4-0. dev 한 벌

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

### 4-0b. prod 한 벌 (2026-09-06 ~ · `〈372〉`)

| 자원 | 이름 | 상태 |
|---|---|---|
| S3 데이터 버킷 | `colab-platform-data-prod` | ✅ 버저닝 · SSE-S3+Bucket Key · `DenyInsecureTransport` · 수명 주기 3 · 태그 `Environment=prod` |
| S3 웹 버킷 | `colab-platform-web-prod` | ✅ 퍼블릭 차단 4 · 버저닝/CORS/수명 주기 **없음**(정본대로) · 태그 `Environment=prod` |
| IAM 정책(운영자) | `colab-platform-s3-prod-policy` | ✅ ⭑ dev 와 달리 **`s3:GetBucketTagging` 포함** — 없으면 태그를 도구로 못 잰다(2026-09-06 실측 403) |
| IAM 사용자 | `colab-platform-s3-uploader-prod` + 키 1 | ✅ 콘솔 로그인 없음 · 키는 `~/.config/colab-platform/prod.env`(0600) · **로컬 도구 전용** |
| IAM 정책(앱) | `colab-platform-app-prod-policy` | ✅ ⭑ dev 의 `DiagnosticsDevOnly` 문을 **뺐다** — 앱은 버킷 설정을 읽을 일이 없고, 서버가 털렸을 때 구성까지 새지 않게 한다 |
| IAM 역할 | `colab-platform-app-prod-role` | ✅ 신뢰 주체 EC2 · 인스턴스 프로파일로 P6 에서 붙인다 |
| VPC | `colab-platform-prod-vpc` (`10.1.0.0/16`) | ✅ P4 · 서브넷 4(public 2 · private 2) · IGW · S3 게이트웨이 엔드포인트 · **NAT 없음** · 태그 `Environment=prod` |
| DB 서브넷 그룹 | `colab-platform-prod-db-subnet-group` | ✅ P4 · 프라이빗 2 (⚠ AZ 만 고르면 안 된다 — **서브넷까지** 골라야 「Subnet IDs are required」가 안 난다) |
| 보안그룹 | `colab-platform-app-prod-sg` · `colab-platform-db-prod-sg` | ✅ P4 · db 가 app 을 **이름으로** 참조 |
| RDS | `colab-platform-prod-db` (PG16, `db.t4g.small`) | ✅ P5 · **보존 7일** ⭐ · 퍼블릭 액세스 **아니오** · 스토리지 자동 조정 최대 100 GiB · 암호화 · 삭제 방지 ON · 단일 AZ. 엔드포인트는 **레포에 안 적는다**(dev 도 그렇다) — `~/.config/colab-platform/prod.env`(0600) |
| EC2 | `colab-platform-app-prod` · `i-07e7b2b740bb79619` (`t4g.medium`, arm64) | ✅ P6 · RAM 3.7 GiB · 루트 30 GiB gp3 · 스왑 4 GB(fstab) · IMDSv2 홉 **2** 실측 확인 · 태그 인스턴스＋**볼륨** |
| 탄력적 IP | `54.116.55.178` | ✅ P6 · ⚠ **EC2 를 종료해도 남는다 — 따로 반환한다** |
| 키 페어 | `colab-platform-prod-key` | ✅ P6 · ⚠ 내려받은 직후 권한이 `0644` 였다(macOS 기본) — `600` 이 아니면 ssh 가 거부한다 |
| RDS 안의 것 | 롤 4 · DB 2 · 연구실 1 · 계정 2 | ✅ P6 · 아래 §4-1b |
| CloudFront 배포 | `colab-platform-prod` · `E1HUNU140VL6BK` · `d1aje00ns2hjsl.cloudfront.net` | ✅ P7 · 오리진 3 · 동작 3 · **무료 플랜** · WAF **감시 모드** |
| CloudFront 함수 | `colab-platform-prod-spa-rewrite` | ✅ P7 · 기본 동작 뷰어 요청 · 태그 `Environment=prod` |
| 백업 cron | `/etc/cron.d/colab-prod` | ✅ P7 · **한 번 돌려 GREEN 확인** — `_ops/backups/prod/` |

**⭑ prod 는 CloudFront 「무료 플랜」이다**(2026-09-06 신설 · dev 도 같은 날 맞췄다).
필요한 것이 다 들어간다 — 동작 **3**(한도 5) · 도메인 **1**(한도 1) · Edge compute.
⚠ 「Custom cache policies 는 Business」 배너가 뜨지만 그건 **새로 만드는** 정책 얘기이고,
**관리형 `CachingDisabled`·`AllViewer` 는 무료에서 쓴다**(실측으로 확인 — 아래).
⭑ 고른 이유는 용량이 아니라 **상한**이다 — flat-rate 는 초과 과금이 없고 pay-as-you-go 는
「no max monthly spend cap」이다. 크레딧 $140 에 예산 경보를 세운 방향과 맞다.

**⚠ WAF 는 감시 모드다.** 무료 플랜에 WAF 가 **포함이고 끄는 선택지가 없다**(옛 콘솔에서
「비활성화」였던 것과 다르다). 차단 모드면 `/api/*` 의 정상 요청이 오탐으로 막힐 수 있고
**그 증상이 앱 버그처럼 보인다** — 개통 판정과 브라우저 한 바퀴를 오염시킨다.
⟹ 감시 모드로 세어 두고, **막았을 요청이 0 이거나 전부 진짜 공격일 때** 차단으로 돌린다.
측정 안 한 차단 장치를 먼저 켜지 않는다. ⬜ **그 전환은 아직 안 했다.**

**⚠ CloudFront 가 원시 IP 오리진을 더는 받지 않는다**(2026-09-06 실측 · `Origin domain cannot
be an IP address`). dev 의 `ec2-core-api` 는 그 제한 **전에** 만들어져 DNS 이름으로 들어가 있다
(`ec2-54-116-191-208.ap-northeast-2.compute.amazonaws.com`). prod 도 같은 형태로 넣었다 —
**EC2 는 오리진 드롭다운에 안 나온다**(CloudFront 가 열거하지 못한다). 직접 타이핑한다.
`Origin type: EC2` 는 고르는 것이 아니라 **도메인 패턴을 보고 붙는다.**

**⚠ 앱 SG 8000 은 CloudFront 에서만 연다** — 소스 = 관리형 접두사 목록
`com.amazonaws.global.cloudfront.origin-facing`. dev 도 같다(실측: 밖에서 `000`,
CloudFront 로는 401 JSON). ⛔ `0.0.0.0/0` 으로 두면 CloudFront 를 건너뛰어 **WAF·로그·
오리진 정책이 통째로 우회**된다.

### 4-1c. prod 완료 판정 (2026-09-06)

```
항목 14 — ✓ 14 · ✗ 0 · ─ 0     전 항목 통과 · exit 0 · 한 번의 실행으로
```

실행은 `infra/prod/deploy-doctor.sh` 다. **혼자서는 못 맞히는 조건이 넷** 있고 넷 다 red 를
하나씩 내며 드러났다 — 컨테이너 안에서 돌 것 · **레포를 통째로** 마운트할 것(⑥⑦ 은
`alembic.ini`, ⑧ 은 `rls_coverage.py` 를 읽는다) · `/etc/colab` 을 **파일 단위로** 줄 것
(700 root 라 uid 10001 이 못 지난다) · **운영자 키로** 돌 것(IMDS 로 돌면 ③ 이 403 —
prod 앱 역할은 진단 권한을 일부러 뺐다). 그 넷이 그 스크립트 머리말에 있다.

함께 실측 — `s3_doctor --bucket colab-platform-data-prod` **10/10**(CORS 포함) ·
CloudFront 로 로그인 **201** → 그 토큰으로 `/me` **200**(⟹ `AllViewer` 가 `Authorization` 을
넘긴다) · 반복 요청에도 **`x-cache: Miss`**(⟹ `CachingDisabled` 가 실제로 캐시를 막는다).

**⭑ prod EC2 사이징이 dev 와 다르다** — `t4g.medium`(dev 는 `t4g.small`). 근거는 `infra/prod/compose.yml`
의 `viz-render` 주석에 있다(dev 커널 OOM 4건 실측 · 전부 cgroup 상한). 루트 30 GiB 도 실측 근거다 —
dev 는 20 GiB 에 65% 이고 불변 태그라 배포마다 이미지가 쌓인다.

**⚠ 지금 도는 이미지는 `main` 이 아니라 기능 브랜치에서 빌드한 것이다** — 태그 `prod-3922d01750d0`.
정본 `〈335〉`-㉳ 는 「`main` 커밋에 찍은 `prod-YYYYMMDD` 태그에서만」이므로, **PR 병합 뒤
`main` 에서 다시 빌드·전송해 그 규율로 돌아온다.** 그때까지는 「브랜치에서 세운 prod」다.

### 4-1b. prod DB 안에 든 것

| | |
|---|---|
| 롤 | `colab_owner`(소유자·마이그레이션) · `colab_app` · `colab_ai_app` · **`colab_backup`**(유일하게 `bypassrls=t`) — 나머지 셋은 전부 `f` 실측 |
| 데이터베이스 | `colab_platform`(표 27 · head `0012_merge_lv1_and_transfer`) · `colab_ai`(head `0005_k2b_concept_graph_seed`) |
| FORCE RLS | 27개 중 **25개** 켜짐 (`verify` 통과) |
| 연구실 | `00000000000000000000HYMETS` 고려대학교 수문학연구실 (`〈52〉` 정본값) |
| 계정 | `전창현`(PI · 정본 SQL 이 심는다) · **`admin`** `01M1TPA0JBQGND6ZJN47NHPXP7` |
| 로그인 | ⚠ **`admin` 하나만 만들었다**(사용자 판정 2026-09-06). 비밀번호·주체 토큰은 32자 난수 · `~/.config/colab-platform/prod-secrets/`(0600) |

**P6 검증 실측 (2026-09-06)** — 4 단위 healthy · `storageMode`·`sourceMode`·`previewSink` 전부 **`s3`** ·
로그인 **201** · 틀린 비밀번호 **401** · 무자격 `/me` **401** · 토큰으로 `/me` **200**(역할 `연구원` ·
`승인 위임: false` — 최소 권한 그대로).

⚠ **`subjects.json`·`credentials.json` 을 만들기 전에 `up.sh` 를 돌리면 도커가 그 자리에 디렉터리를
만든다** — `IsADirectoryError` 로 core-api 만 unhealthy 가 되고 나머지 셋은 healthy 다.
`rmdir` 로 지우고 파일을 놓은 뒤 다시 올린다. **살아 있는 쪽이 속이는** 그 모양이다.

⚠ **`db.t3.small` 로 한 번 잘못 만들었다가 「수정 → 즉시 적용」으로 바꿨다**(2026-09-06).
기능 문제는 없었다 — **RDS 의 CPU 아키텍처는 클라이언트에게 안 보인다.** 값이 더 비쌌을 뿐이고,
레포의 나머지가 전부 t4g 라 여기만 x86 으로 남으면 다음 사람이 이유를 못 찾는다.
⛔ **`:39` 의 「x86 이미지는 t4g 에서 안 뜬다」와 헷갈리지 않는다** — 그건 **EC2 의 도커 이미지** 이야기다.

**P5 가 여는 것 — 시점 복구(PITR)**
보존 7일이 걸리면 그 기간 안의 **어느 시점으로도** 되감을 수 있다. 별도 WAL 기구를 짜지 않는다.
⛔ **다만 「설정했다」는 관문이 아니다** — 실제로 되감아 보는 것이 `〈256〉` 이 요구한 것이고, P8 이다.

**P3 검증 실측 (2026-09-06)**
- `ops/s3_doctor.py` **9/10** — 유일한 ✗ 가 **CORS** 이고 **그것이 지금 옳은 상태다**:
  AllowedOrigins 에 넣을 **배포 주소가 아직 없다**(CloudFront 는 P7). dev 때도 같은 순서였다.
  ⛔ **통과시키려고 임시값을 넣지 않는다** — 배포가 생기면 그 주소로 채운다.
- `ops/s3_smoke.py` **전 항목 통과** — 프리사인드 PUT(ASCII·**한글·공백 키**) · CreateMultipartUpload ·
  파트 2개(5MiB+1KiB) · ListParts→Complete→Head · Abort→소멸 · DeleteObjects 뒷정리(남은 객체 0).
  ⟹ **자작 SigV4 가 prod 에서도 옳게 서명한다**(에뮬레이터가 아니라 진짜 S3 로 쟀다).

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

⭑ **⟨개정 2026-09-06 · `〈372〉`-㉱ · 유료 전환 뒤 실측⟩** ／ 종전 ~~Free Plan 전제의 누적·월간 두 벌~~

**⚠ 크레딧이 남아 있는 동안 실제 청구는 계속 `$0` 이다.** 요금 유형이 `Credit`·`Tax`·`Usage`
셋으로 갈리고(2026-09-06 콘솔 실측), 필터를 안 걸면 크레딧이 사용액을 덮어 **알림이 영영 안 온다.**
Free Plan 이든 유료든 이 함정은 같다 — 달라진 것은 **크레딧이 다 탄 뒤**다:
Free Plan 은 **계정 정지**였고, 유료는 **청구로 넘어간다**(서비스가 안 멈춘다).

**⟹ 예산은 `Usage` 만 본다.**
- **범위 옵션 → 특정 AWS 비용 차원 필터링 → 차원 `요금 유형` → `Usage` 만 포함**
  - 종전엔 `Excludes: Credit, Refund` 였다. 요금 유형이 셋뿐이니 **포함할 것 하나를 고르는 쪽이 명확하다.**
  - `Tax` 는 뺀다 — 사용량 급증을 보려는 것이지 세금을 보려는 것이 아니다.
- **예산 갱신 유형 = `기본 예산`** — 매달 자동 갱신된다. `만료 예산` 은 정한 달 뒤로 **아무것도 안 잰다.**
- 「작업 연결」(자동 정지)은 걸지 않는다 — 알림만 받고 판단은 사람이 한다.

**서 있는 예산 (2026-09-06 실측)**

| 이름 | 기간·금액 | 필터 | 왜 |
|---|---|---|---|
| `colab-platform-monthly-all` | 월 **$150** | `Usage` | 계정 전체 급증 감지 |
| `colab-platform-monthly-dev` | 월 **$60** | `Usage` ＋ 태그 `Environment=dev` | dev 실측이 $32~44 — 정상 운전에선 안 울리고 늘면 운다 |
| `colab-platform-monthly-prod` | 월 **$60** | `Usage` ＋ 태그 `Environment=prod` | 같음 |
| `colab-platform-credit-burn` | 연 **$140** | `Usage` | 크레딧 잔액 감시. 2026-09-06 실측 **$140 중 $0.44 사용** · 만료 2027-08-20 |

⚠ **뒤 둘(dev·prod)은 비용 할당 태그가 활성화된 뒤에만 만들 수 있다.**
태그는 **그 태그를 쓴 자원이 하나라도 있어야** 「비용 할당 태그」 목록에 나타난다 —
자원 생성(`§5-2` 이후)에서 `Environment` 태그를 붙인 뒤 콘솔에서 **활성화**한다.
⛔ **활성화는 소급되지 않는다** — 활성화 시점부터의 비용만 갈린다. 그래서 **자원을 만들 때 붙인다.**
⚠ 콘솔이 개편돼 「사용자 정의 비용 할당 태그」 **탭이 없다** — 한 목록에 합쳐졌다(2026-09-06).

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

### 6-1-1. 데이터셋 행 삭제 — `ops/purge_datasets.py` (일회성)

**제품 기능이 아니다.** `deleteDataset` 은 `NOT_IMPLEMENTED_P1` 이고 이 도구가 그것을 여는 것도 아니다.
**바이트가 이미 없어진 데이터셋의 원장 행**처럼 제품이 표현할 수 없는 상태를 운영자가 치우는 자리다.

⛔ **고정 id 목록 ＋ `--yes-delete` 없이는 돌지 않는다. `PLAN-SoT §9` 행과 Ted 의 명시 GO 없이 실행하지 않는다.**
선례 = `〈365〉`(준비·dry-run)·`〈366〉`(집행 114행). 자세한 가드는 파일 docstring.

⚠ **경계를 먼저 건다** — `colab_owner` 는 `NOBYPASSRLS` 이고 표는 FORCE RLS 라
`set_config('app.current_lab', …, true)` 가 없으면 **DELETE 가 0행에 조용히 성공**한다.

### 6-2. 재배포 · 되돌리기

재배포 = 1) 절. 되돌리기 = `dev.env` 의 `COLAB_IMAGE_TAG=dev-<직전 sha>` 로 바꾸고 `up.sh`. **마이그레이션은 되돌리지 않는다**(`0009` 처럼 백필이 든 판은 downgrade 가 값을 잃는다).

### 6-3. 백업과 복원

- **두 겹이다** — ⑴ RDS 자동 백업 — dev **1일**(Free Plan 때의 값 그대로) · **prod 7일**(`〈372〉`-㉯ · 그 기간 안에서 **임의 시점으로 되감을 수 있다**) ⑵ **`backup.sh` 가 하루 1회 `pg_dump` → S3 `_ops/backups/<벌>/`, 30일 보관**(수명 주기가 강제)
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

### 6-3-0. 시점 복구(PITR) — 되감아 본 기록 (`〈256〉` 관문 · 2026-09-06)

⭑ **관문이 요구한 것은 기능이 아니라 증명이다.** 「보존 7일로 설정했다」는 관문이 아니다.
실제로 되감아 본 회차 —

| 시각(KST) | 한 것 |
|---|---|
| 17:37:57 | `colab_platform` 에 표식 한 행을 심는다 (`_ops_pitr.probe`) |
| 17:45:20 | **그 행을 지운다** |
| 17:42:00 | ← **복원 목표**(심은 뒤 · 지우기 전). 「특정 시점으로 복원」 → 새 인스턴스 `-pitr` |
| — | **복원본에 그 행이 있다** · **원본에는 0건** · 복원본에 운영 데이터도 함께(계정 2·연구실 1·head `0012`) |

⟹ 되감기가 **일어났고**, **원본을 건드리지 않았다.** 둘 다 확인해야 증명이다.

**여기서 배운 것 넷 — 사고 때 이걸 모르면 「복구가 안 된다」고 오판한다**

⓵ **「최신 복원 가능 시간」은 지금보다 5분쯤 뒤처진다.** RDS 가 WAL 을 밀어내는 주기 때문이다.
   ⛔ **「방금 전」으로는 못 되감는다.** 심은 직후에 지우면 되감을 자리가 없다 — 표식을 심고
   그 시각이 「최신 복원 가능 시간」을 넘을 때까지 기다린 뒤에 지워야 한다.
⓶ **가장 이른 복원 시점은 인스턴스 생성 시각**이다(실측 `2026-09-06T03:12:45Z`). 그 이전을
   지정하면 `no older backups available` 로 거부된다.
⓷ **원본을 되돌리는 것이 아니다 — 새 인스턴스가 선다.** 엔드포인트가 다르다.
   진짜 사고 때의 갈아타기는 **이름 바꿔치기**다: 원본 → `-broken`, 복원본 → 원래 이름.
   엔드포인트가 식별자를 따라오므로 `/etc/colab/*.url` 을 **안 고쳐도 된다**.
   ⭑ **롤·비밀번호도 함께 되감긴다** — 복원본이 원본과 같은 자격으로 붙는 것을 실측했다.
⓸ ⛔ **S3 는 같이 안 돌아간다.** DB 를 되감아도 버킷의 객체는 그대로다 —
   복원 시점 이후에 올린 파일은 **DB 에 행이 없고 S3 에 객체만 남는다**(고아 객체).
   반대 방향(행은 있는데 객체가 없음)이 아닌 것이 그나마 다행이다. **시점 복구는 「DB 사고」의
   수단이지 「전체 롤백」이 아니다.** 되감은 뒤 고아 객체 정리는 사람이 판단한다.

**⛔ 표식은 반드시 지운다.** `deploy_doctor ⑧` 의 facts SQL 은 `pg_catalog`·`information_schema` 를
뺀 **모든 스키마**를 훑는다 — `_ops_pitr` 를 남기면 RLS 미적용으로 **red** 다.
실측: 지운 뒤 표 27개 · 비표준 스키마 0 · **`deploy_doctor` 14/14 ─ 0 재확인**.

**리허설 인스턴스는 삭제 방지를 끄고 만든다** — 켜면 끝에 못 지운다. 단일 AZ 로 만든다(요금 2배 방지).

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
| **백업이 두 겹** | RDS 자동 백업은 **되감기**(시점 복구)를 주고 자체 잡은 **길이**(30일)를 준다. dev 는 Free Plan 때 1일에 막혀 있었고, ⭑ **⟨2026-09-06⟩ 유료 전환 뒤 prod 는 7일**이다 |
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
| 인스턴스를 크게 잡는 게 낫지 않나 | `t4g.medium` | Free Plan 이 막았다. ⭑ **⟨2026-09-06⟩ 그 제약은 풀렸다** — 그래도 **올리지 않는다**: 실측으로 충분함이 확인됐고(55 MB·8파일 처리에 컨테이너 4 합 268 MiB · 스왑 사용 0) **재지 않은 것을 근거로 키우지 않는다.** ⚠ **렌더 부하는 아직 안 재봤다** — 그것을 재고 나서 판단한다 |
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

⭑ **⟨개정 2026-09-06 · `〈372〉`-㉰⟩ 유료로 전환했다 — 「어느 날 그냥 멈춘다」는 사라졌다.**

- **크레딧** — 2026-09-06 실측 **$140 중 $0.44 사용** · 만료 **2027-08-20**. 다 타면 **청구로 넘어간다**
  (Free Plan 때처럼 **계정이 정지되지 않는다**). `colab-platform-credit-burn`(연 $140)이 그 소진을 알린다
- ~~무료 플랜 기간 만료 2027-02-22~~ — **사라졌다.** 유료 전환이 이 날짜를 없앴다
- **이제 챙길 것은 「멈추는 날」이 아니라 「얼마 나가는가」다** — 월간 예산 셋이 그 자리다(`§5-1`)

／ 종전 ~~Free Plan 이다. 먼저 오는 쪽에서 무료 이용이 끝나고 dev 가 정지된다 ·
크레딧 소진 추정 2026-11~12월 · 무료 플랜 만료 2027-02-22(날짜라 예산이 못 잡는다) ·
유료 전환 시점을 미리 정해 두지 않으면 어느 날 그냥 멈춘다~~
