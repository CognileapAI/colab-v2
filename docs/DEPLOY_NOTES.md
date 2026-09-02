# AWS dev 환경 구축 — 상세 기록 (진행 파일의 넘침분)

> 이 파일은 **문답 기록**(왜 다른 길을 안 갔나)을 남긴다. 진행 원장과 집행 계획서는 G13 에서 지웠다.
> 그 상한을 넘는 상세를 여기 둔다 — **정합성 보고서 전문 · 결정 기록 전문 · 콘솔 체크리스트 · 함정 · 완료 판정**.
> G11 에서 `docs/DEPLOY.md` 의 부록이 되고, G13 에서 이 파일은 남긴다(계획서 §14-1 6).
> 계획서 원문은 **G13 에서 삭제했다**(작업용 비계). 남은 것은 `docs/DEPLOY.md`·`DEPLOY_HANDOVER.md` 와 이 파일이다.

## 2. 정합성 보고서 (G1 · 계획서 §4-2 양식 그대로)

계획서는 「레포를 보지 않고 썼다 — 배포·인프라에 관한 것은 하나도 확인되지 않았다」고 고지했고(머리말) §4-0 은 「어긋나면 계획을 고친다. 저장소 관습을 계획에 맞추지 않는다」다. 대조 = 계획서 전문 읽기 + 실물 확인(2026-08-29~30). **아래 표의 「실제」열은 이 회차에 파일로 다시 확인한 것**이다(Dockerfile 경로 6 · `/healthz` 라우트 · `compose.i2.yml` 의 `_FILE` 키 · `.gitattributes` · `kernel/` 파일 목록 · `aws_credentials.py` 공급자 순서 · `manifest.toml` 등기 · `db-bootstrap.sh` · `jobs.py:241` · `ci.yml`).

### 2-1. 확인된 전제 — 계획이 맞았다

| 계획의 가정 | 실제 |
|---|---|
| `COLAB_CORE_STORAGE_MODE` local/s3 · 기본 local · 반쪽 설정 기동 거부 | `kernel/config.py` `_storage_settings()` 그대로 |
| 신규 런타임 의존 0 · SigV4 자작 · MinIO 금지 · `ops/` 는 이미지 밖 | `〈173〉`·`S3.md` 그대로. `kernel/{sigv4,aws_credentials,s3,objectpath}.py` 실물 |
| 버킷 이름·리전·BPA·버저닝·SSE·CORS 헤더·라이프사이클 2 | `S3.md §1` 과 글자 그대로 일치 |
| RLS FORCE 는 DB 가 강제 · 설정은 env 주입·없으면 기동 실패 | 불변규칙 5 · `〈121〉` |
| 헬스 경로 필요 | **이미 있음** — `/healthz` 5 단위(core·viz·ai `@app.get("/healthz")` · worker 헬스 스레드 · frontend nginx). 계약 밖. 신설 불필요(계획서 §6-3 무효) |
| `deploy_doctor`·`deploy_web` 이름 | `services/core-api/ops/` 에 비어 있음(`app-role.sql`·`provision-account.sql`·`s3_doctor.py`·`s3_smoke.py`·`set-password.py` 뿐) |
| `.gitattributes` `*.sh eol=lf` | 있음(`* text=auto eol=lf` + `*.sh text eol=lf`) — 계획서 §4-1 19 의 「제안」은 불필요 |
| 자격증명 공급자 env → ECS → EC2 IMDSv2 | `kernel/aws_credentials.py` `load_credentials()` — `(_from_env, _from_ecs, _from_imds)` 순서, 출처 `'env'|'ecs'|'imds'` 반환 |
| Dockerfile 이 있는지 `❓` | **있다 — 5+1**: `services/{core-api,pipeline-worker,viz-render,ai-service}/Dockerfile` · `frontend/Dockerfile` · `infra/staging/migrator/Dockerfile`. 비특권 uid 10001 |
| 시크릿 취급 `❓` | **`_FILE` 경로 규약**이 이미 규칙이다 — `compose.i2.yml` 의 `COLAB_CORE_DATABASE_URL_FILE`·`SUBJECTS_FILE`·`CREDENTIALS_FILE`·`COLAB_PIPELINE_DB_URL_FILE`·`COLAB_AI_DB_URL_FILE`(`〈121〉`-㉯, `docker inspect` 유출 사고가 근거) |
| 마이그레이션 적용 방법 `❓` | **migrator 이미지**(`infra/staging/migrator`) + `db-bootstrap.sh {roles|app-grants|verify}` · 체인 2(`db/platform`·`db/ai`) · 소유자 롤 `colab_owner` / 앱 롤 비소유자 |
| CI `❓` | `.github/workflows/ci.yml` — 계약 게이트 6 · 경계 3 · DB 4 · `stage2-markers` · `selftest`. ⚠ `db-boundary` 본 게이트·서비스 pytest 잡은 **없다**(§7 · `HANDOFF §4 #42`) |

### 2-2. 조정한 것 — 계획을 저장소에 맞춰 고쳤다 (규칙으로 확정 · `〈178〉`)

| 계획 | 저장소 관습 | 바꾼 내용 |
|---|---|---|
| 진행 원장 + `CLAUDE.md` 재개 블록 + 결정 기록 | HANDOFF 진실원 · 값은 `PLAN-SoT §9` 에만(`CLAUDE.md §6-3` 이원화 금지) | 진행 = `HANDOFF §1 T-U`(I-D·V-3) · 결정 = `〈178〉` · 지시서 = 이 파일. 재개 블록·별도 원장 안 만듦(`〈178〉`-㉵) |
| `/etc/colab-platform/dev.env` 에 값 직접 | `_FILE` 경로 규약(`〈121〉`-㉯) | compose 는 `*_FILE` + `/etc/colab/*` 0600 파일. 값은 env 에 안 실림(`〈178〉`-㉯) |
| `alembic upgrade head` 1회, 체인 1개 | 체인 2개(platform·ai) · 소유자 롤 · `migrator` 이미지 · `db-bootstrap.sh` | staging 배선 재사용 — `db-bootstrap.sh` 를 `COLAB_PG_MASTER_URL_FILE` 분기로 파라미터화(`su_psql` + `app-grants` 의 직접 `docker exec` 줄), RDS 마스터(`rds_superuser`)로 부트스트랩(`〈178〉`-㉰) |
| `S3_REGION` · env 목록(세션·VIZ·WORKER·AI 누락) | `COLAB_CORE_S3_REGION` 등 실물 이름 | env 표를 실물로 재작성(필수/선택) — `infra/dev/README.md`(`〈178〉`-㉱) |
| core 이미지 2단계 빌드 · `postgresql-client` | 단일 스테이지 · 백업은 별 컨테이너 관례(`infra/staging/backup`) | 이미지 무변경, `pg_dump` 는 일회용 `postgres:16-alpine`(`〈178〉`-㉮) |
| 이미지 1개(`colab-api`) | 5 이미지 | buildx arm64 → `Architecture=arm64` 검사 → save/scp/load ×5 · 5 healthy 대기(`infra/dev/{build,ship,up}.sh`) |
| 「core-api 하나」 배치 | `〈176〉` = 같은 EC2 compose 에 worker·viz(+ai) 자원 상한 | `infra/dev/compose.yml` 5 단위(core·worker·viz·ai + migrator 프로파일) · EC2 nginx 없음 · SPA = CloudFront Function · previews = 데이터 버킷 `previews/`(`〈178〉`-㉮) |
| 커밋 마지막 1개(§0-3 9 · §14-2) | `CLAUDE.md §7` 한 커밋 = 한 논리 단계 | 단계별 커밋 C1~C6(§4) |
| `docs/DEPLOY.md` 정본 · `HANDOVER.md` · `CLAUDE.md` 불변식 절 | `dev-package/` 가 운영 정본 자리(`S3.md`·`RESTART`·`DEPLOY-CURRENT`) · `CLAUDE.md` 는 작업 면 밖 | `S3.md §1` = S3 벌 정본 유지(EC2 역할 3문 + previews PUT 추가) · 런북 = **`infra/dev/README.md` 하나**(`dev-package/DEPLOY-AWS.md` 는 만들지 않는다) · 계획서 원문 = `sessions/ID-AWS-PLAN.md` 보관 · 사람용 요약 = `ID-PR.md`(`〈178〉`-㉶) |
| 헬스 신설(§6-3) · 환경 표시값 `COLAB_CORE_ENV` 신설 검토(§4-1 9) | `/healthz` 실물 · 반쪽 거부가 이미 짝 검사 | 헬스 신설 안 함 + core `GET /healthz/storage`(출처·만료만) 신설 · **`COLAB_CORE_ENV` 안 만듦** — doctor 「환경 짝」 항목이 대신(`〈178〉`-㉱·㉲) |

### 2-3. 계획이 틀린 것 — 상의가 필요했고 결정됨

| 항목 | 문제 | 결정 |
|---|---|---|
| G12 prod | 정본 `㊻` prod ⏸ · `〈176〉` dev 한정 | **Ted 판정 요청**(`㊻` 개정 — `〈178〉`-㉷ ①②). 판정 전 dev 까지 |
| V-3 「범위 밖」(§16) | `WORK-UNITS` I-D 진입조건이 V-3 완료 · `CLAUDE.md §5` 부분 완료 금지 | **I-D 에 포함**(사용자 2026-08-29) — 코드는 C2·C4·C5, 완료 정의는 V-3 행(초안 §5) |
| 「병합 후 시작」 선행조건(§2-1) | 브랜치 미병합·Ted 판정 대기 | 스택 브랜치 `feature/rtf400_deploy` 위에서 코드 구간 진행, 콘솔은 판정 후 |
| 「도메인 없다」(§2-3 ④) | `colab-hydro.com` 이 Cloudflare 에 살아 있다(staging 터널) | 계획서대로 **도메인 없이**(사용자) — `〈178〉`-㉳ |
| 사이징 근거 「바이트가 서버를 안 지난다」(§1) | `〈175〉`-(다) 묶음 zip 은 core-api 를 통과한다 | 실측 항목으로 — Ted ④ `t4g.medium` 권고 · EBS ≥ 2×최대 묶음 |
| 참조 문서(업로드 계획서 `S3_UPLOAD_PLAN.md §5` · `UPLOAD_PROGRESS.md`) | 레포에 없음 | IAM JSON 은 `S3.md §1` 3문 구성으로 `infra/dev/iam/*.json` 재생성 |
| 예산 결정 ⑤(그대로) vs G4-a/b(재구성) | 내부 모순 | 사용자 콘솔 몫에서 확정 — Ted ⑤ 금액 |
| SPA 라우팅 = 오류 응답 치환(§8-2 3) | `/api/*` 의 진짜 403/404 JSON 까지 HTML 로 바뀐다 | **CloudFront Function**(`spa-rewrite.js`) — 판정은 `/api/v1/me` 401 JSON |

### 2-4. 재사용할 것 — 새로 만들지 않는다

`kernel/{sigv4,aws_credentials,s3,objectpath}.py` · `ops/s3_doctor.py`·`s3_smoke.py`(`Report`·`_s3_call`·`check_credentials`·`check_bucket` 을 doctor 가 import) · Dockerfile 5+1 · `infra/staging/{compose.i2.yml,db-bootstrap.sh,migrator,backup,restore,provision-lab.sh,provision-lab.sql}` · `ops/provision-account.sql`·`set-password.py` · `/healthz` 5 · `storage_layout.py`(생성물 ×3 — 복제 등기의 선례) · `gates/tools/rls-coverage.sh` 의 facts SQL 블록 + `rls_coverage.main` 판정기 · `gates/tools/db_boundary.py`(compose 목록으로 확장) · `frontend/vite.config.ts` 프록시(`137be9c`, 사다리 ② 전제) · CI 게이트

### 2-5. 위험 신호

- **배포 코드가 이미 `infra/staging` 에 있다** — 계획서 G3·G10 은 「새로 만들기」가 아니라 **dev 변형**이다. 계획서를 그대로 따르면 두 벌이 생긴다.
- ARM64 geo 휠 미검증(rasterio·netCDF4·h5py·pyhdf) · t4g.small 2 GB 에 geo 2단위 미측정 · 계획서 env 대로 가면 G6/G8 에서 로그인 불가(`subjects`·`credentials` `_FILE` 누락).
- viz 캐시 키가 mtime 을 본다(`jobs.py::_source_digest` `st_mtime_ns`) — S3 내려받기마다 새 키 → `previews/` 무한 증가(§7).
- CI 가 `db-boundary` 본 게이트·서비스 pytest 를 안 돈다 — I-D 의 회귀는 로컬 실행으로만 잡힌다(§5).


## 5. 완료 판정 (오라클)

**I-D 완료 정의**(`WORK-UNITS §10.2` I-D 행 그대로) = `S3.md §1` 7단계 + `ops/s3_doctor.py` 10/10 + `ops/s3_smoke.py` 전 항목 + 5 배포 단위 헬스 + 업로드→등록→미리보기 1건 실호출 (+ `ops/deploy_doctor.py` 전 항목 ✓ · 무입력 실행이 정직한 ✗/─ 를 낸다). 코드 구간(C1~C6)만으로는 닫히지 않는다 — 콘솔(§6)과 dev 검증이 뒤따른다.

**V-3 완료 정의 — 초안 (미작성 · Ted ⑼ 뒤 `WORK-UNITS` V-3 행에 확정)**

1. worker s3 모드 **실호출 1건** — 검증용 버킷(`colab-platform-data-local-phj`)에 올린 업로드를 `S3UploadBlobs.materialize` 로 내려받아 `process_upload` 가 포맷 감지·축 판별까지 끝낸다(원장 행으로 확인). 로컬 모드는 기존 시험 전건 무변경 green 이 오라클.
2. viz `S3SourcePort` **실호출 1건** — `uploads/{targetId}/` 의 parts + `grid/` 를 내려받아 `create_render` 가 미리보기를 만든다.
3. `S3PreviewSink` **실호출 1건** — 산출물이 데이터 버킷 `previews/{name}` 에 content-type·`cache_control public,max-age=300` 으로 올라간다. FE 는 무변경(`previewResult.ts imageUrl` = `/previews/...`).
4. **같은 객체 2회 materialize = 같은 `cache_key`** — 시험으로 단언(ETag 또는 S3 `Last-Modified` 로 `os.utime`). 실패하면 `previews/` 가 매 렌더마다 는다.
5. **처리 뒤 작업 디렉터리 삭제** — worker `rmtree(workdir/upload_id)` · viz LRU 가 상한 아래로 내린다. 시험은 처리 후 디렉터리 부재를 단언.
6. **작업 디렉터리 상한 3상태** — `COLAB_VIZ_WORK_MAX_BYTES` 숫자(검사) · `none`(명시 면제, 건수 노출) · 미설정(**거부**). 미설정이 조용히 무제한으로 떨어지면 안 된다(green-by-skip 의 같은 모양).
7. 모르는 모드 값은 기동 거부 — `COLAB_WORKER_STORAGE_MODE`·`COLAB_VIZ_SOURCE_MODE` 오타가 local 로 접히지 않는다.

**커밋별 오라클** = §4 표. **검증 총합** = pytest(core 567+ · worker · viz 각 전건) · vitest 316 · tsc 0 · 게이트 전 종 · buildx arm64 실측 · doctor 무입력 정직 ✗ · 로컬 s3 모드 실호출은 검증용 버킷으로 worker `materialize`·viz `S3SourcePort`·`S3PreviewSink` 1건씩(→ §8). ⚠ CI 는 이 중 `db-boundary` 본 실행·서비스 pytest 를 돌리지 않는다(`HANDOFF §4 #42`) — 로컬 실행 출력을 §8 에 남긴다.


## 6. 콘솔 체크리스트 (G4~G6 · 사용자 몫 · 한 화면에 한 동작)

> 계획서 §7 의 순서를 레포 조정값으로 다시 적은 것이다. 각 단계 끝의 **검증 = `deploy_doctor` 항목**은 이름으로 대조한다 — **항목 번호(C3 확정, `0e64f13`)** = ① 운영자 자격증명 ② 데이터 버킷 ③ 웹 버킷 ④⑤ DB platform/ai ⑥⑦ head platform/ai ⑧ RLS 전수 ⑨ 앱 롤 ⑩ 4 단위 헬스 ⑪ 앱 자격증명 출처(imds) ⑫ 환경 짝 ⑬ 진입·라우팅 ⑭ 백업 24h. 콘솔 단계 사이의 부분 실행은 **`--allow-skip` 을 적어야** exit 0(면제 명시 — 없으면 ─ 가 남는 한 exit 1). 값(키·비밀번호·접속 문자열)은 채팅·커밋·이 문서 어디에도 적지 않는다. AWS 에 무엇을 만들면 **그 자리에서 §9 대장에 한 줄**.

| 단 | 콘솔 동작 | 조정값(레포 우선) | 검증 |
|---|---|---|---|
| 0 | **계정 실물 목록** — S3 버킷 전체(객체 수·용량) · IAM 정책·사용자·액세스 키 · Budgets · 로컬 설정 파일 | 계획서 §4-1 18 그대로. 「알려진 것」은 §9 — 나머지는 콘솔이 정본 | 콘솔 육안 → §9 대장에 `삭제`/`유지`/`변경` |
| 1 | **예산 2**(실지출 · Usage) + 이메일 알림 — **새 자원을 켜기 전에** | 금액 = Ted ⑤ / 사용자. 옛 예산은 3단 마지막에 | 콘솔 육안 · §9 |
| 2 | **옛 자원 정리** — 버킷(비우고) → 키 → 사용자 → 정책 | ⚠ **0단 실물 목록을 승인받은 뒤에만.** 검증용 `colab-platform-data-local-phj` 는 **유지**(`〈173〉`-②). 이름을 지운 뒤 재사용하지 않는다 | 콘솔 육안 · §9 |
| 3 | **dev 벌** — IAM 정책 `colab-platform-s3-uploader-dev-policy`(3문) · 사용자 + 키(운영자용) · **EC2 역할**(같은 3문 + `previews/*` PutObject) · 데이터 버킷 `colab-platform-data-dev`(ap-northeast-2 · BPA · 버저닝 · SSE-S3 · TLS 정책 · CORS `http://localhost:5173` 만 · 라이프사이클 2) · 웹 버킷 `colab-platform-web-dev`(BPA · CORS·라이프사이클 없음) | **`S3.md §1`** + `infra/dev/iam/*.json`(C6). 계획서 4-c 의 이름·재료는 쓰지 않는다 | `s3_doctor` 10/10 · `s3_smoke` 전 항목 · doctor **운영자 자격증명**(잠정 1) · **데이터 버킷 7항목**(잠정 2 — 오리진은 아직 localhost 뿐이라 그 소항목은 정직한 ✗/─) · **웹 버킷 index.html**(잠정 3 = ─, `deploy_web` 뒤) |
| 4 | **네트워크** — VPC `10.0.0.0/16` · 퍼블릭 1 + 프라이빗 2(AZ 2) · IGW · 퍼블릭 자동 IP · SG 2(app: CloudFront 프리픽스 8000 + SSH 개발자 IP 각각 / db: app SG 에서 5432) | **NAT Gateway 없음**(월 $45 갈림길) · ALB 없음 · SSH `0.0.0.0/0` 금지 | doctor 는 못 본다 — 콘솔 육안 · §9. 실질 검증은 6단 SSH |
| 5 | **RDS** — PostgreSQL 16 · `db.t4g.micro` · 20 GB gp3 · 자동 조정 끔 · Multi-AZ 아니오 · 퍼블릭 아니오 · db SG · 자동 백업 7일 · **삭제 방지 켬** · 마스터 비밀번호는 콘솔 생성 → 레포 밖 보관 | 계획서 §7-2 그대로. **스키마 적용은 8단**(프라이빗) | 콘솔 `Available` · 예상 월 요금 §9 · doctor **DB ×2**(잠정 4) 는 8단까지 ─ |
| 6 | **EC2** — AL2023 **ARM64** · 타입 = Ted ④(`t4g.medium` 권고, 판정 전 `t4g.small`) · 퍼블릭 서브넷 · app SG · **인스턴스 프로파일 = 3단 역할** · **IMDSv2 필수 + hop limit 2** · 20 GB(Ted ④ EBS ≥ 2×최대 묶음) · 키 페어(레포 밖, `chmod 600`) · EIP 할당·연결 · docker 설치 | hop limit 2 = 컨테이너 안 앱이 브리지 한 홉을 더 지난다(`〈178〉`-㉯). **AWS 키를 EC2 에 넣지 않는다** | SSH 접속 · `docker version` · EIP 를 §9 에 |
| 7 | **시크릿** — `/etc/colab/` 에 `_FILE` 5(core DB URL · subjects · credentials · pipeline DB URL · ai DB URL) + 소유자 DB URL 2(migrator) — **EC2 위에서 직접 작성**(CRLF 회피) · uid 10001 · 0600 | `compose.i2.yml` 규약 그대로(`〈121〉`-㉯). 값을 로컬에서 만들어 scp 하지 않는다 | `ls -l` 권한 · 값은 어디에도 적지 않음 |
| 8 | **부트스트랩 → 마이그레이션 → 기동** — `infra/dev/db-bootstrap.sh roles`(마스터 URL 파일) → `app-grants` → 이미지 5 load(`ship.sh`) → `migrate-platform`·`migrate-ai` 프로파일 → `up.sh`(5 healthy 대기) → 첫 연구실/계정(Ted ⑦ — `provision-lab.sql` HYMETS · `provision-account.sql` + `set-password.py`) | 절차 = `infra/dev/README.md`(C6). `pg_trgm` 확장은 `[미확인 — 여기서 실측]` | doctor **DB ×2 · head ×2 · RLS 전수 · 앱 롤 속성 · 5 단위 헬스(`storageMode==s3`) · 앱 자격증명 출처 `imds` · 환경 짝**(잠정 4~10) 전 ✓ · 사다리 ② = SSH 터널 + 로컬 `npm run dev` 로 업로드 1건 → dev 버킷 객체 |
| 9 | **`deploy_web`** — `frontend/dist` → 웹 버킷(assets immutable · `index.html` no-cache · **index 마지막**) | 소스맵 공개 여부 = Ted ⑥ | doctor **웹 버킷 index.html**(잠정 3) ✓ |
| 10 | **CloudFront** — 오리진 3(웹 버킷 OAC · EC2 EIP:8000 · 데이터 버킷 `previews/` OAC) · 동작 3(`/api/*` 캐시 비활성·헤더 전부 · `/previews/*` · 기본) · HTTP→HTTPS · **CloudFront Function `spa-rewrite.js`**(기본 동작 뷰어 요청) · 웹·데이터 버킷 정책에 OAC 문 | 오류 응답 치환은 쓰지 않는다(`〈178〉`-㉮). 배포 주소를 §9 에 — 네 곳이 쓴다(CORS · doctor `--endpoint` · README · PR) | doctor **HTTPS · API 라우팅(`/api/v1/me` 401 JSON) · previews**(잠정 11~13) — 전파 15~20분 뒤 |
| 11 | **CORS** — 데이터 버킷 `AllowedOrigins` 에 CloudFront 주소 **추가**(localhost 는 유지) | `S3.md §1` 4 | doctor 데이터 버킷 오리진 소항목 ✓ · 브라우저 실업로드 |
| 12 | **dev 검증** — 브라우저(CloudFront)에서 로그인 → 업로드 → 등록 → 미리보기 1건 · 묶음 zip 다운로드(core 경유 트래픽 실측 — Ted ④ 입력) | I-D 완료 정의(§5) | doctor 전 항목 ✓(백업 항목은 G10 전이라 ─) · 실호출 원문 → §8 |

**하지 않는 것** — NAT · ALB · 도메인/ACM · prod(G12) · staging 내리기(G13) · 옛 자원의 「이름으로 삭제」(실물 목록 없이) · RDS 삭제 방지 해제 · 값을 채팅에 붙여넣기.


## 7. 함정

- **계획서를 그대로 구현하면 두 벌이 생긴다** — Dockerfile·compose·부트스트랩·백업이 `infra/staging` 에 이미 있다. 계획서 G3·G10 은 dev 변형이다.
- **viz 캐시 키 = mtime** — `jobs.py::_source_digest` 가 `st_mtime_ns` 를 넣는다(실물 `:241`). S3 에서 내려받으면 매번 새 파일이라 **cache_key 가 매번 바뀌고 `previews/` 가 무한히 는다.** E 면: `S3SourcePort.materialize` 가 S3 `Last-Modified` 로 `os.utime` 하거나 디지스트를 ETag 로 — 시험 「같은 객체 두 번 = 같은 키」.
- **`db-bootstrap.sh` 는 `su_psql` 만이 아니다** — `app-grants` 가 `app-role.sql` 을 **직접 `docker exec … psql`** 로 흘린다(실물 `:47`). `su_psql` 만 파라미터화하면 app-grants 가 여전히 로컬 컨테이너를 찾는다. F 면: 두 자리 다.
- **`db-boundary` 게이트의 사각** — `gates/tools/db_boundary.py` 의 `COMPOSE` 가 `compose.i2.yml` 단일 경로(`COLAB_DB_BOUNDARY_COMPOSE` 로 한 파일만). dev compose 가 횡단 DB URL 을 선언해도 확장 전까지 아무 게이트도 안 본다. F 면: 목록 확장 + selftest 픽스처 3(두 번째 compose 부재 red · 횡단 선언 red · 두 파일 green) + `:` 목록 호환 + `gates/README.md` 두 곳.
- **CI 에 `db-boundary` 본 게이트·서비스 pytest 잡이 없다**(`ci.yml` — `selftest` 만) — 이 브랜치의 회귀는 CI 가 못 잡는다. 로컬 실행 출력을 §8 에 남기고, CI 는 별건(`HANDOFF §4 #42`).
- **manifest 등기 = 강제** — core 커널 3파일을 한 글자 고치면 worker·viz 복제본 재생성이 같은 커밋에 있어야 `generated-up-to-date` 가 green 이다. 복제본 헤더에 `generated`/`do not edit` 낱말을 쓰면 등기 밖 자칭 생성물로 red.
- **IMDSv2 hop limit** — 기본 1 이면 컨테이너에서 `PUT /latest/api/token` 이 조용히 실패하고 공급자가 「자격증명 없음」으로 기동을 거부한다. 원인이 EC2 설정 한 칸이라 증상으로는 안 보인다.
- **EC2 에 키를 두면 역할이 무의미** — `aws_credentials.py` 는 env 를 먼저 본다. doctor 의 「출처 `imds`」 항목이 이것을 잡는다.
- **`COLAB_CORE_STORAGE_MODE=s3` 를 빠뜨리면 성공처럼 보인다** — 기본 `local` 이 이겨 EC2 디스크에 쌓이고 전송 op 가 501, FE 가 form-data 로 폴백한다. compose 리터럴 + doctor 헬스 `storageMode==s3` 가 잡는다.
- **`drive_uploads` 호출 시험 7곳**(`test_stage1_worker.py` 4 · `test_storage_layout.py` 3) — kwarg 호환(`upload_dir` 주면 Local 어댑터) 없이 시그니처를 바꾸면 전부 깨진다. 격자는 한 디렉터리(`work.grid_dir`)에 내려야 하고, `run_once` 의 `UPLOAD_DIR` 부재 raise 는 모드별.
- **viz 요청 스레드에서 내려받으면 202 가 늦는다** — 큰 parts 면 `create_render` 응답이 다운로드 시간만큼 밀린다. 전환 조건(렌더 중 API p95 붕괴 · `〈176〉`)의 실측 항목.
- **정본 원본 부재** — `〈175〉〈176〉〈178〉` 전부 2차 기재 위에 섰다. 원본 개정은 기획 소유(`HANDOFF §4 #38`).
- **ARM64 geo 휠** — rasterio·netCDF4·h5py·pyhdf 의 aarch64 manylinux 휠 가용성 `[미확인]`. buildx arm64 5회 성공이 완료 정의. 실패 시 Ted ⑧(x86 전환).
- **RDS 소유권** — 마스터는 `rds_superuser` 지 진짜 슈퍼유저가 아니다. `colab_owner` 로 DB 를 만들려면 `GRANT colab_owner TO 마스터` 가 먼저. 확장(`pg_trgm`)은 rds_superuser 로 된다고 알려져 있으나 `[미확인 — 8단 실측]`.
- **문서에 절대경로 금지**(`CLAUDE.md §3-8`) — 이 문서의 홈 설정 디렉터리 표기는 계획서 인용뿐이다.

## 결정 기록 — `PLAN-SoT §9 〈178〉`

**전문은 `dev-package/PLAN-SoT.md §9 〈178〉` 로 옮겼다**(2026-09-02 · G13).
값과 근거는 그 한 곳에만 둔다(`CLAUDE.md §6-3` 이원화 금지) — 여기 있던 사본은 지웠다.

- `㉮` 배치 · `㉯` 시크릿 · `㉰` DB · `㉱` env · `㉲` 헬스 · `㉳` 도메인 없음 · `㉴` V-3 ·
  `㉵` 진행 기록 · `㉶` 정본 자리 · `㉷` prod = Ted 판정 대기
- `㉸`~`㊃` 는 2026-09-02 집행 완결분(인프라 실측 · 백업 롤 · 업로드 개편 · 계약 동결 해제 ·
  회귀 · Ted 판정 11항 · 남은 결함 · 마감)

코드 32파일이 이 번호를 인용한다. **인용된 하위 기호(`㉮`~`㉷`)는 등재 뒤에도 그대로다.**
