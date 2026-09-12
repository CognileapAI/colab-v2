# 정찰 — 발신 이메일 역량 · 임시 비밀번호 전송 (2026-09-12)

- 역할 = researcher(읽기 전용 정찰 + 이 보고 1건). 판정·승인 아님.
- 조사 범위 = `services/` · `infra/` · `docs/` · `gates/` · `.claude/` · `frontend/src/`(정적 grep + 파일 통독). AWS·컨테이너 미접촉.

## 1. 결론

- **발신 이메일 역량 = 0건.** SMTP · SES · sendmail · `email.mime` · boto3 SES 클라이언트 **전부 부재**.
- `email` 문자열 hit 는 **계정 식별자(로그인 이름) 컬럼**뿐 — 전송 코드 아님.
- 아웃바운드 HTTP 선례 = **Slack Incoming Webhook 1건**(`infra/ops/alarm_runner.py`) — 표준 라이브러리 `urllib.request` 기반.

## 2. 항목별 근거

### ① 기존 메일 코드

| 판정 | 근거 |
|---|---|
| 전송 코드 0건 | `grep -rInE "smtp\|sendmail\|email\.mime\|ses_client\|boto3.*ses\|SESv2"` → `services` · `infra` · `docs` · `.claude` · `gates` 전 범위 **hit 0** |
| `\bSES\b` 0건 | 같은 범위 hit 0 |
| 무관 hit(계정 식별자) | `services/core-api/src/colab_core/app/routes/accounts.py` — `email: str = Field(...)` · `INSERT INTO d1_account(... email)` · `SELECT 1 FROM d1_account WHERE lower(btrim(email))=:email` |
| 무관 hit(기타) | `routes/identity.py` · `routes/members.py` · `domains/d1_identity.py` · `ops/provision-account.sql` · 시험 fixture — 전부 컬럼·시드 |
| 무관 hit(git 설정) | `infra/dev/tests/ship-gate.sh` — `git -c user.email=t@t` |
| 프런트 무관 hit | `frontend/src/routes/AccountAdminPage.tsx` · `components/members/MemberPermissionGrid.tsx` · `generated/fe-core.ts` — 입력 필드·생성 타입 |

### ② AWS dev 인프라

- **SES 언급 0건** — `infra/**` · `docs/DEPLOY*.md` 전부.
- **리전** = `ap-northeast-2`(서울). 근거 `docs/DEPLOY.md` §4 「리전은 전부 `ap-northeast-2`(서울).」
- **권한을 붙일 자리** = `infra/dev/iam/role-policy.json`(EC2 인스턴스 프로파일 `colab-platform-app-dev-role`). 현재 Statement 4문 — `UploadObjects` · `Multipart` · `DiagnosticsDevOnly` · `PreviewsPut`. 전부 S3 한 버킷. **Terraform·CDK 없음**(staging 터널 `infra/staging/tunnel/` 만 terraform) — dev IAM 은 **JSON 문서 + 콘솔/CLI 수작업**.
- **컨테이너 env 자리** = `infra/dev/compose.yml` `core` 서비스 `environment:` 블록.
- **검증 도메인 = 없음.** dev 프런트 주소는 CloudFront 기본 도메인 `d31zgpff2091oh.cloudfront.net`(`docs/DEPLOY.md` §1·§4). 「도메인 없이」가 확정(`docs/DEPLOY_NOTES.md` — `〈342〉`-㉳).
- **레포에 등장하는 유일한 도메인명** = `colab-hydro.com`(Cloudflare · staging 터널용 · `docs/DEPLOY_NOTES.md`). SES 검증 여부 `[미확인]`.
- EC2 는 퍼블릭 서브넷 + IGW 직결(NAT 없음) → 아웃바운드 443 가능 `[추론]`. SG 아웃바운드 규칙 실물 `[미확인]`.

### ③ 비밀 주입 규약 — `*_FILE`

- 규약 확정 = **값이 아니라 0600 파일 경로를 env 로 준다**(`〈121〉-㉯`, 근거 = `docker inspect` 유출 사고).
- 구현 = `services/core-api/src/colab_core/kernel/config.py` `FILE_SUFFIX = "_FILE"` (동형 구현이 `ai-service` · `pipeline-worker` · `viz-render` 에도 존재).
- 실제 배선 = `infra/dev/compose.yml` — `COLAB_CORE_DATABASE_URL_FILE` · `COLAB_CORE_ACCOUNT_ADMIN_DATABASE_URL_FILE` · `COLAB_CORE_SUBJECTS_FILE` · `COLAB_CORE_CREDENTIALS_FILE`, 값은 `/etc/colab/*`.
- 파일 요건 = `infra/dev/README.md` — `$COLAB_DEV_SECRETS_DIR` 아래 각 `0600` · 소유자 uid 10001.
- 조용한 무시 방지 시험 선례 = `services/core-api/tests/test_secret_file_refs.py` · `services/viz-render/tests/test_secret_from_file.py`.
- 귀결 = 메일 자격(API 키·SMTP 비밀번호)은 `COLAB_CORE_MAIL_*_FILE` 형태로 같은 규약을 따르는 것이 정합 `[추론 · 이름은 미확정]`.

### ④ Slack 알람 발신자 — 재사용 가능 패턴

- 모듈 = `infra/ops/alarm_runner.py`. 선택자 `_webhook(path)` · `urllib.request.Request` · `urlopen(..., timeout=10)`.
- 자격 취급 = **webhook URL 을 0600 파일 한 줄로 읽고 `https` 강제**(`--webhook-file` · 미지정 시 `::gate-readiness-failure::gate=ops-alarm|missing=COLAB_OPS_ALERT_WEBHOOK_FILE`).
- 성질 = 상태형(연속 실패·회복 전이에만 발신) · 구조화 로그 `colab.ops.v1` 배출 · 선택자 `_emit`.
- 검사기 = `gates/tools/ops-alarm-notify-selftest.py` · `gates/tools/ops-observability-selftest.sh`.
- 재사용 가능성 = **HTTP API 방식 메일 발신(자격 파일 + `urllib` POST + 실패 전이 처리)의 형판으로 직접 전용 가능**. 다만 위치가 `infra/ops/`(cron 운영 스크립트)이고 core-api 요청 경로가 아니므로 **동기 전송에는 코드 이식이 필요**하다.

### ⑤ 현재 화면·API 표면

- `frontend/src/auth/LoginPage.tsx` — **「비밀번호 찾기」 링크·플레이스홀더 부재**(해당 문자열 hit 0). 안내문은 「운영자에게 받은 이메일과 초기 비밀번호를 넣어 주세요.」 · 실패 문구는 초기 비밀번호 재시도 안내.
- 인접 화면 = `frontend/src/auth/PasswordChangePage.tsx`(최초 변경) 존재.
- `services/core-api/src/colab_core/app/routes/accounts.py` `POST /admin/accounts`(`createServiceAccount`) — **초기 비밀번호를 응답에 넣지 않는다(no).** 응답 필드 = `accountId` · `email` · `name` · `labId` · `role`. 초기 비밀번호는 **요청 본문 `initialPassword`(운영자가 직접 정함)** 이고 저장은 `hash_password` 결과만.
- 귀결 = 임시 비밀번호 메일 기능은 **서버가 비밀번호를 생성하는 경로 자체가 없어** 발급 흐름 신설이 선행(계약 변경).
- 비밀번호 회전 절차는 이미 문서에 존재 — `docs/DEPLOY.md` §6-5 「로그인 비밀번호 회전」.

### ⑥ 규칙 제약 — 새 의존·새 env 가 닿는 항목

`.claude/rules/deploy.md` 「깨뜨리면 안 되는 것 (전부 이유가 있다)」 11항 중 닿는 것(제목만):

| # | 제목 요지 | 닿는 이유 |
|---|---|---|
| 1 | NAT 게이트웨이를 만들지 않는다 | 아웃바운드 경로를 NAT 로 해결하려는 설계 배제 |
| 2 | EC2 env 에 AWS 액세스 키를 넣지 않는다 | SES 사용 시 키가 아니라 **IAM 역할 문 추가**가 유일한 길 |
| 6 | 설정에 관대한 기본값을 도입하지 않는다 | 메일 설정 누락 시 **기동 거부**가 의도된 동작 |
| 8 | DB 와 저장 백엔드를 따로 바꾸지 않는다 | env 는 통째로 교체 — 메일 env 도 환경별 한 벌에 편입 |
| 9 | 정리 잡·백업을 앱 안의 백그라운드 태스크로 옮기지 않는다 | 메일 재시도 큐를 앱 내 백그라운드로 두는 설계 배제 |

- `docs/DEPLOY.md` 에는 「깨뜨리면 안 되는 것」 절이 **없다**(헤딩 목록 대조 완료). 대신 닿는 자리 = §2-2 core-api env 표 · §2-4 「환경별 한 벌」 · §9 「기계마다 다른 것 — 이 표가 정본이다」.
- `deploy_doctor` 15 항목 중 env 짝 검사 = `services/core-api/ops/deploy_doctor.py` 선택자 `check_env_pair` / `env_pair_findings`. 새 필수 env 추가 시 이 검사와 §9 표를 함께 갱신해야 판정이 갈리지 않는다 `[추론]`.

## 3. 선택지와 비용

| 안 | 내용 | 비용 | dev | staging(WSL) |
|---|---|---|---|---|
| A | AWS SES(API · boto3) | SES 샌드박스 해제 신청 · 발신 도메인/주소 검증 · IAM 역할에 `ses:SendEmail` 문 1개 추가 · core-api 에 boto3 SES 경로 | 리전 `ap-northeast-2` 동일 · 역할 기반이라 키 불요(규칙 2 준수) | AWS 자격이 필요 — WSL 에는 EC2 역할 없음. 0600 키 파일 필요(규칙 2 는 EC2 한정) |
| B | 외부 메일 API(HTTP) | API 키 1개(0600 파일) · `alarm_runner` 패턴 이식 · 도메인 검증은 공급자 몫 | AWS 자원 변경 0 | 동일 코드가 그대로 동작 — 터널 밖 아웃바운드만 필요 |
| C | SMTP 릴레이 | 자격 2종 · 포트 587 아웃바운드 · 라이브러리 추가 | SG 아웃바운드 확인 필요 | 동일 |
| D | 메일 미전송 | 운영자가 초기 비밀번호를 대면 전달(현행) | 0 | 0 |

- 공통 선행 = **서버 측 임시 비밀번호 생성·재설정 엔드포인트 신설**(현행 `POST /admin/accounts` 는 운영자 입력 비밀번호만 받음) + 계약 동결 절차.
- 공통 선행 = 발신 주소용 도메인. 현재 dev 는 도메인 없음 — `colab-hydro.com` 전용 여부는 판정 사항.

## 4. 권고

1. 이메일 전송을 **stage 3 항목으로 분리**하고 본 라운드는 D(현행 유지)로 둔다 — 도메인·SES 샌드박스·계약 변경 셋이 동시에 걸린다.
2. 진행 시 B안(HTTP 메일 API)이 dev·staging 양쪽에서 같은 코드로 서는 유일한 안이다. 자격은 `*_FILE` 규약, 발신 코드는 `infra/ops/alarm_runner.py` 형판.
3. 착수 전 필요한 판정 2건 — ⑴ 발신 도메인 ⑵ 임시 비밀번호를 서버가 생성할 것인가(계약 변경 여부).

## 5. 후속 항목 (이 보고에서 고치지 않음)

- `docs/DEPLOY.md` §2-2 env 표에 메일 관련 항목 자리 없음 — 도입 시 §2-4·§9 와 동시 갱신 필요.
- `deploy_doctor` 에 메일 자격 검사 항목 부재 — 도입 시 16번째 항목 여부가 완료 정의(15/15)를 건드린다.

## 6. `[미확인]`

- SES 샌드박스 상태 · 검증된 발신 주소 존재 여부 (AWS 미접촉).
- EC2 보안그룹 아웃바운드 규칙 실물 (AWS 미접촉).
- `colab-hydro.com` 의 MX·SPF·DKIM 구성.
- WSL staging 호스트의 외부 SMTP(587/465) 도달 가능 여부.
