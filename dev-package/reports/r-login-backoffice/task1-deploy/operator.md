# R-LOGIN-BACKOFFICE 작업 1 후속 — dev 서비스 운영자 1명 등재

- 작성 2026-09-12 · 기준 `main` `aa3fce46` · 작업 id `99e4f20fce7e4a538059ee08d1a2fe35`
- 결론 = **`account_admin.service_operator` 0행 → 1행.** 대상 계정 `01M29ZX6RRC7H3G159Y86XK2DZ`
  (`ttlhi10@gmail.com` · 이름 `Ted`). `release.md §6` 의 `[Ted 입력 대기]` 두 건 중
  **운영자 등재와 실제 로그인 1회가 닫혔다.**
- 이 보고에 비밀번호·해시·소금·토큰·접속 문자열을 적지 않는다. 초기 비밀번호는 전달 파일에서만
  읽었고 실행 직후 `shred -u` 했다.

## 1. 착수 시점 실측 (등재 전)

| 항목 | 값 | 관측 |
|---|---|---|
| 배포 sha | `fc45a9aa7c64` | EC2 `CURRENT_SHA` |
| `MAIN_SHA` | `main=fc45a9aa7c64 candidate=fc45a9aa7c64 ancestor=yes` | EC2 파일 |
| core-api | `colab-v2/core-api:dev-fc45a9aa7c64` · healthy | `docker ps` |
| `d1_lab` | 2행 — `0000000000000000000000000A 고려대학교 수문학연구실` · `0000000000000000000000000B B 연구실` | `colab_account_admin` 조회 |
| `d1_account` | 5행. 대상 이메일 행 **0** | 같은 조회 |
| `account_admin.login_credential` | **0행** | 같은 조회 |
| `account_admin.service_operator` | **0행** | 같은 조회 |
| 자격 파일 `credentials.json` 로그인 이름 | `admin`·`colab`·`pi`·`TEST-stage12-labB-20260911` — 대상 이메일 **부재** | EC2 `json.load` 키 목록 |

덮어쓰기 금지 조건(`intent/stage3-login-hardening.md` 「기존 이메일은 덮어쓰지 않는다」)은
**DB 0행 ＋ 자격 파일 부재**로 충족됐다.

## 2. 연구실·역할 판정 — 근거와 한계

- **연구실 = `0000000000000000000000000A`(`고려대학교 수문학연구실`).** 근거 = `03-HANDOFF.md`
  결정 `〈52〉` 축자 「초기 데이터 귀속 = 고려대학교 수문학연구실(전창현 교수) — **v2 의 첫 실제 연구실**」.
  남은 하나(`B 연구실`)는 cross-tenant 음성 증명용 픽스처 계열이고 dev 에도 `TEST-stage12-labB-20260911`
  계정이 들어 있다.
- ⚠ **「Ted 의 연구실」을 명시한 문서는 없다.** `dev-package/`·`docs/` 에 `ttlhi10` 을 계정·연구실로
  지목한 행이 0건이다(grep). 위 판정은 **「실제 연구실이 하나뿐」**이라는 사실에서 나온 것이지
  Ted 귀속을 적은 문서에서 나온 것이 아니다 — 연구실을 바꾸려면 계정 행을 고쳐야 한다.
- **역할 = `연구원`.** 근거 = `services/core-api/ops/provision-account.sql` 머리말 축자
  「없는 역할을 지어내지 않는다 … 그래서 아래 기본값은 **최소 권한**이다 — `연구원`」.
  운영자 권한은 역할이 아니라 `account_admin.service_operator` 행이 준다
  (`accounts.py::_require_operator`), 따라서 최소 권한 역할과 양립한다.
- **권한 스위치 4종은 심지 않았다.** 제품 경로 `POST /admin/accounts` 가 스위치를 만들지 않기 때문이다
  (`accounts.py` INSERT 3개 = `d1_account`·`d2_member_role`·`login_credential`).
  `provision-account.sql` 은 스위치를 심지만 그 파일은 `login_credential` 을 만들지 않아 이번 경로가 아니다.

## 3. 계정 생성 — 제품과 같은 경로

`POST /admin/accounts` 를 쓸 수 없다(운영자 0명 → 자기 자신을 만들지 못한다). ops SQL 중
`login_credential` 을 만드는 것도 없다 — `provision-account.sql` 은 `d1_account`·`d2_member_role`·
스위치까지이고, `set-password.py` 는 **DB 가 아니라 자격 파일**에 심는다.

그래서 `accounts.py::create_account` 의 트랜잭션을 **그대로** core-api 컨테이너 안에서 실행했다.
같은 모듈을 import 했으므로 해시·정규화·잠금·INSERT 가 제품과 동일하다.

- 해시 = `colab_core.kernel.password.hash_password` (`scrypt` · `n=16384 r=8 p=1`)
- 로그인 이름 정규화 = `colab_core.kernel.db_credentials.normalize_login_name`
- ID = `colab_core.kernel.ids.Ulid.generate()`
- 같은 `pg_advisory_xact_lock(1131379081)` · 같은 이메일 중복 검사 2종 · 한 트랜잭션
- `must_change_password`·`session_version` 은 **INSERT 에서 생략** — 제품과 같이 DB 기본값(`true` · `1`)을 받는다
- 접속 = 컨테이너에 마운트된 `/etc/colab/account-admin-database.url`(`colab_account_admin` 롤)
- 비밀번호는 **표준입력 한 줄**로만 넘겼다. argv·파일·로그에 적지 않았다.

집행 뒤 실측 —

| 열 | 값 |
|---|---|
| `account_id` | `01M29ZX6RRC7H3G159Y86XK2DZ` |
| `login_name` | `ttlhi10@gmail.com` |
| `lab_id` / `role` | `0000000000000000000000000A` / `연구원` |
| `kdf` / `n` / `r` / `p` | `scrypt` / `16384` / `8` / `1` |
| `must_change_password` | `true` |
| `session_version` | `1` |

### 3-1. 읽기 되짚기에서 걸린 권한 — 판정 red 가 아니다

집행 스크립트의 **사후 조회**가 `permission denied for table d2_member_role` 로 죽었다.
INSERT 트랜잭션은 이미 커밋된 뒤였고, 원인은 `ops/account-admin-role.sql` 이
`d2_member_role` 에 **`INSERT` 만 주고 `SELECT` 를 주지 않는 것**이다(축자 확인).
같은 결손을 라운드 파일 작업 2 가 이미 적어 두었다 — 「`account-admin-role.sql` 에
`GRANT SELECT ON d2_member_role` 를 더한다(현재 `INSERT` 만 — 실측)」(`R-LOGIN-BACKOFFICE.md`).
**이 레인은 롤 권한을 고치지 않았다** — 작업 2 의 소유분이다. 역할 행 확인은 소유자 롤로 대신했다(§4).

## 4. 운영자 등재 — `provision-service-operator.sql`

- 파일 동일성 = 개발 기계 ↔ EC2 `md5 ad86e5833ddaa11a9afe3fa5d1b60688` 일치.
- 실행 롤 = 소유자(`/etc/colab/platform-owner-db.url`). 스크립트 축자 「migration owner만 실행한다」.
  접속 문자열은 `PG*` 환경변수로만 넘겼다(argv 미탑재).
- **1차 실행은 실패했다** — `INSERT 0 0` ＋ 스크립트 자체 가드
  `ERROR: 지정한 계정이 없어 운영자를 등록하지 못했다`. 원인은 계정 부재가 아니라 **FORCE RLS** 다.
  `d1_account` 는 FORCE RLS 라 소유자도 정책을 받고, `app.current_lab` 이 없으면
  `current_lab_id()` 가 NULL 이라 `SELECT id FROM d1_account WHERE id=…` 가 0행을 낸다
  (`.claude/rules/deploy.md` 10 · `schema.sql:41` `current_lab_id()`).
- **2차 = 같은 psql 세션에서 `SET app.current_lab` 을 먼저 걸고 같은 파일을 실행.**
  `ops/purge_datasets.py` 가 쓰는 것과 같은 방식이다(`set_config('app.current_lab', …)`).
  스크립트·롤·권한은 고치지 않았다.

| 계수 | 전 | 후 |
|---|---|---|
| `account_admin.service_operator` | 0 | **1** (`01M29ZX6RRC7H3G159Y86XK2DZ` · `created_at 2026-09-12 05:03:41Z`) |

## 5. 동작 확인 — 상태 코드만

CloudFront 공개 진입으로 3회 호출. 본문은 파싱만 하고 토큰·값은 출력하지 않았다.

| 호출 | 기대 | 실측 | 판독 |
|---|---|---|---|
| `POST /api/v1/sessions` (이메일 ＋ 초기 비밀번호) | 성공 | **201** · 응답 키 `expiresAt`·`revocationToken`·`sessionId`·`token` | 계약이 `status_code=201` 이다(`session.py`) — 「200」이 아니라 201 이 정상값 |
| `GET /api/v1/me` (그 토큰) | 변경 강제 신호 | **200** · `mustChangePassword = true` | 첫 변경 미완 세션임이 응답에 드러난다(`identity.py`) |
| `POST /api/v1/admin/accounts` (같은 토큰) | 403 | **403** · `code = PASSWORD_CHANGE_REQUIRED` | `deps.py::current_subject` 가 운영자 판정 **앞에서** 막는다 — 의도된 동작 |

- 프로브 계정은 **생성되지 않았다** — `d1_account` 에 `probe-must-not-be-created%` **0행**,
  총 계정 수 6(등재 전 5 ＋ 이번 1).
- ⚠ **운영자 판정 자체가 통과하는 것은 아직 관측되지 않았다.** 403 의 코드가
  `PASSWORD_CHANGE_REQUIRED` 라 `_require_operator` 까지 가지 못한다. 그 통과는 **Ted 가 첫 로그인에서
  비밀번호를 바꾼 뒤**에만 관측된다. 이 레인은 Ted 의 비밀번호를 바꾸지 않는다.

## 6. 비밀 취급

- 초기 비밀번호는 0600 전달 파일에서 셸 변수로만 읽고 표준입력으로 넘겼다. `cat`·`echo` 로
  화면에 내지 않았고 레포·서버 어느 파일에도 쓰지 않았다.
- 확인 뒤 `shred -u` 했다. 사후 `ls` = `No such file or directory`.
- 확인용으로 발급된 세션 1건이 남는다 — `expires 2026-09-12 17:04:20Z` · `revoked NULL`.
  회수 토큰을 보관하지 않았으므로 손으로 끊지 않았다. **Ted 의 첫 비밀번호 변경이
  `session_version` 을 +1 하면 그 시점에 무효가 된다**(`db_credentials.change_password`).
- 임시 실행 스크립트는 레포에 남기지 않았다(커밋 0 · 작업 종료 시 삭제).

## 7. 남은 것 · 후속

- **[후속] `account-admin-role.sql` 에 `d2_member_role` 의 `SELECT` 가 없다.** 이 결손은
  **어느 게이트에도 걸리지 않는다** — 롤 권한을 대조하는 검사는 `deploy_doctor` 에도
  `rls-coverage` 에도 없고, `account-admin-role.sql` 의 자기 점검은 superuser·membership·소유만 본다.
  현재 걸리는 자리 = 런타임 조회 실패뿐. 라운드 작업 2 의 항목과 같은 대상이다.
- **[후속] `provision-service-operator.sql` 은 그대로는 성립하지 않는다.** FORCE RLS 아래에서
  `app.current_lab` 없이 실행하면 **`INSERT 0 0` 뒤 가드가 예외**를 낸다. 스크립트 머리말에
  경계 설정이 전제로 적혀 있지 않다. 걸리는 검사 = 없음(게이트·`deploy_doctor` 모두 이 스크립트를
  실행하지 않는다). 머리말에 `-v lab_id` 또는 `SET app.current_lab` 을 명시하는 것이 후속 항목이다.
- **[미확인] `POST /admin/accounts` 201.** Ted 의 첫 비밀번호 변경 뒤에야 관측 가능하다.
- **[미확인] 초기 비밀번호 길이가 제품 하한보다 짧다.** 전달 파일은 **9자**이고 제품 하한은 **10자**다
  (`accounts.py` `initialPassword: Field(min_length=10)` · `frontend/src/auth/passwordRules.ts`
  `length >= 10`). DB·로그인 경로에는 길이 하한이 없어 심기·로그인 모두 성립했고 실측으로 확인했다.
  다만 **같은 비밀번호를 `POST /admin/accounts` 로는 발급할 수 없다.** 첫 변경은 10자 이상을
  요구하므로 변경 뒤에는 해소된다. 이 레인은 비밀번호를 지어내지 않았다.
