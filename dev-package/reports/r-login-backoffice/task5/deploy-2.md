# R-LOGIN-BACKOFFICE 작업 5 — dev 배포 2차 (`71ee15757737`)

- 작성 2026-09-12 · 레인 `worktree-agent-a7e021108ef17f356` · 작업 id `172f9dea04634f66bf3aade884ade86e`
- 결론 = **`deploy_doctor --env dev` 15/15 · 한 번의 실행 · exit 0**(2026-09-12 14:25:03Z). 재시도 0회 · 부분 실행 합산 0.
- 이 보고에 접속 문자열·비밀번호·토큰을 적지 않는다.

## 0. 기준과 착수 시점 실물

| 항목 | 값 | 관측 |
|---|---|---|
| 기준 | `git merge --ff-only origin/main` — `Already up to date` · HEAD `71ee15757737` = 지시문 기대치 | 로컬 |
| 착수 시 `CURRENT_SHA` | `0a4aecb58e68` | EC2 `cat` |
| 착수 시 `MAIN_SHA` | `main=0a4aecb58e68 candidate=0a4aecb58e68 ancestor=yes` | EC2 `cat` |
| 착수 시 컨테이너 4종 | `:dev-0a4aecb58e68` · 전부 healthy · `/healthz` 4종 200 | `docker ps` · `curl` |
| 착수 시 platform head | **`0027_operator_audit`** (지시문 허용값 2개 중 하나) | 살아 있는 DB |
| 착수 시 ai head | `0007_merge_vocab_and_category` | 살아 있는 DB |
| `0a4aecb5` → `71ee1575` | 코드 경로 diff **46파일 · +3384/−87**(`services/core-api` · `frontend` · `db/platform` · `gates/tools/rls-effect.sh` · `infra/notifications`) — 문서만의 회차가 아니다 | `git diff --stat` |

## 1. 집행 경로 — 공통 실행기

`infra/releases/README.md` 축자 「배포는 `python3 scripts/deploy_release.py run --plan <release.json>` 으로 실행한다」.
`ops/deploy_web.py` 의 실제 업로드는 실행기 자식 명령에서만 허용되므로(단독 CLI 는 exit 78) 이 경로를 벗어나지 않았다.
계획 JSON 에 자격값을 넣지 않았다 — `ship.sh`·`deploy_web.py` 의 자격은 보호된 홈 파일에서만 왔다.
계획·단계 스크립트·전 단계 로그 = `dist/release-dv-20260912-2/`(gitignore) ＋ 실행 기록 `<git-common-dir>/deploy-releases/`.

| 배포 기록 id | 결과 | 단계 |
|---|---|---|
| `dv-20260912-2-71ee15757737` | `deployment: failed` (단계 5 exit 3) | build · ship · 배포 레포 트리 · 마이그레이션 · **롤(실패)** |
| `dv-20260912-2b-71ee15757737` | **`deployment: verified`** (배포 4/4 · 검증 2/2 전부 exit 0) | ai 체인 · 롤(2차) · 기동 · 프런트 · 검증 2 |

## 2. 지시문 단계별 증거

### ① 선행 — 헬스·체인·백업

- core-api 를 포함한 4 단위 healthy · `/healthz` 200 ×4 (위 §0).
- platform 체인 `0027_operator_audit` 기록.
- **마이그레이션 전 백업** = 문서화된 dev 경로 `sudo /opt/colab-v2/backup.sh`(`docs/DEPLOY.md §6-3`), 2026-09-12 14:14:50Z · exit 0.
  - 백업 id **`2026-09-12T141450Z`**
  - `_ops/backups/dev/2026-09-12T141450Z-colab_platform.sql.gz` 109,584 B
  - `_ops/backups/dev/2026-09-12T141450Z-colab_ai.sql.gz` 5,518 B
  - 스크립트 축자 「GREEN — 두 데이터베이스 모두 올렸다」. `deploy_doctor` ⑭ 가 뒤에 「0.2시간 전 · 객체 55건」으로 같은 세대를 다시 확인했다.

### ② 마이그레이션 — head `0030_merge_audit_and_backoffice`

문서화된 migrate 프로파일(`up.sh` ① 단계와 같은 명령)로 집행했다.
`dev.env` 의 `COLAB_IMAGE_TAG` 를 `dev-0a4aecb58e68` → `dev-71ee15757737` 로 올린 뒤 실행했다(옛 migrator 이미지에는 `0028`~`0030` 이 없다). 직전 파일은 `dev.env.bak-before-71ee15757737` 로 보존했다.

| | 값 |
|---|---|
| 적용 전 platform | `0027_operator_audit` |
| 적용 후 platform | **`0030_merge_audit_and_backoffice`** |
| 적용 후 ai | `0007_merge_vocab_and_category`(무변) |

경로에 든 리비전 = `0028_account_status` · `0029_operator_read_policy` · `0030_merge_audit_and_backoffice`(두 형제 `0027_operator_audit`·`0029_operator_read_policy` 의 머지).

⚠ **1차 단계 스크립트의 결함 1건(이 레인이 만든 것)** — `ssh … bash -s` 의 heredoc 안에서 `docker compose run` 이 **남은 스크립트를 자기 stdin 으로 삼켰다.** 그래서 `migrate-platform` 은 돌았고 `migrate-ai` 와 사후 조회는 실행되지 않았는데 종료코드는 0 이었다. 값으로 확인해 드러냈고(위 표) 2차에서 `-T … < /dev/null` 로 고쳤다. **「exit 0 이니 다 돌았다」로 읽지 않은 것이 이 항목을 살렸다.**

### ③ `account-admin-role.sql` 재적용 — 문서 경로가 RDS 에서 성립하지 않는다

문서 경로 그대로(`infra/dev/db-bootstrap.sh account-admin` · 비밀번호는 기존 0600 시크릿에서 파생, 회전 없음) 1차 실행 → **exit 3**.

```
ERROR:  permission denied to alter role
DETAIL:  Only roles with the SUPERUSER attribute may change the SUPERUSER attribute.
```

- 걸린 문장 = 파일 안의 `SELECT format('ALTER ROLE %I NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT BYPASSRLS PASSWORD %L', …)` ＋ `\gexec` 한 덩어리.
- 원인 = PostgreSQL 은 `SUPERUSER`/`NOSUPERUSER` 를 **명시하면 값이 같아도** superuser 를 요구한다. **RDS 마스터는 superuser 가 아니다** — 실측 `current_user=postgres · rolsuper=f · rolcreaterole=t`.
- 즉 **이 문장은 dev(RDS)에서 구조적으로 성립하지 않는다.** 파일은 `\set ON_ERROR_STOP on` 이라 뒤따르는 REVOKE·GRANT 가 **한 줄도 실행되지 않는다.**
- **「기존 값이라 넘긴다」로 적지 않는다 — 이 결함이 걸리는 검사가 어디에도 없다.** `deploy_doctor` 15항목에 롤 권한 대조가 없고(⑨ 는 `colab_app`·`colab_owner` 속성만 본다), `rls-coverage`·`rls-effect` 도 보지 않으며, 파일 자기 점검은 superuser·membership·소유만 본다. 걸리는 자리는 **런타임 500 하나뿐**이다. → §6 후속.

**2차 = 그 한 문장만 빼고 같은 파일을 그대로 실행.** 검사는 하나도 빼지 않았다 — 파일 꼬리의 자기 점검(`rolsuper OR rolcreatedb OR rolcreaterole OR rolinherit OR NOT rolbypassrls` → 예외)이 ALTER 가 세우려던 속성을 그대로 판정하고 통과했다. 빠진 것은 **같은 값으로의 비밀번호 재설정** 하나다(실측 롤 속성 `rolsuper=f · rolcreatedb=f · rolcreaterole=f · rolinherit=f · rolbypassrls=t` — ALTER 의 목표값과 이미 일치). 실행 결과 `REVOKE`×4 · `GRANT`×8.

`has_table_privilege('colab_account_admin', …)` 전후 —

| 대상 | 전 | 후 |
|---|---|---|
| `account_admin.service_operator` INSERT | `f` | **`t`** |
| `account_admin.service_operator` DELETE | `f` | **`t`** |
| `account_admin.service_operator` SELECT | `t` | `t` |
| `public.d2_member_role` SELECT | `f` | **`t`** |
| `public.d2_member_role` INSERT | `t` | `t` |

지시문이 요구한 네 값(`service_operator` INSERT·DELETE · `d2_member_role` SELECT)이 전부 `t` 다.

### ④ 이미지 반입·교체·배포 레포 트리·sha 파일

- `infra/dev/build.sh` — 5 이미지 `linux/arm64` 실측 통과 · `dist/colab-v2-dev-71ee15757737.tar` 285 MB.
- `infra/dev/ship.sh` — 조상 게이트 통과(`ancestor=yes`) · 5 이미지 `docker load` · ops 소스 번들 「manifest 전건 일치」.
- **배포 레포 트리 동기화(선행 단계)** — 밀기 전 EC2 `/opt/colab-repo/db/platform/versions` 최신은 **`0026_login_sessions`** 였고 살아 있는 DB 는 `0027` 이었다. 밀지 않았다면 `deploy_doctor` ⑥ 이 **옛 head 를 정답으로 삼아 조용히 틀린다.** 밀고 md5 4건 대조 전건 일치(`deploy_doctor.py` `a2d5651512ff786f0a71eeb36e51ed9c` · `0030_merge_operator_audit_and_backoffice.py` `61719b2d1befe4345d4c64ba468d2bbd` · `rls_coverage.py` `d91556ed4b165ce21bec96e4295729a7` · `account-admin-role.sql` `f8f68b9f6b690ec6c2c6b0a680fd2d05`).
- `up.sh` — 4 단위 healthy(fail-closed 통과) · 헬스 본문 `storageMode=s3` · `sourceMode=s3`.
- 교체 후 `CURRENT_SHA` = **`71ee15757737`** · `MAIN_SHA` = **`main=71ee15757737 candidate=71ee15757737 ancestor=yes`** · 컨테이너 4종 전부 `:dev-71ee15757737` healthy.

### ⑤ 프런트 정적 번들

- `npm run build`(`tsc --noEmit && vite build`) → `ops/deploy_web.py` (실행기 자식) → **96 파일 · 6,531,699 B · `index.html` 마지막**.
- **CloudFront `index.html` md5 = 로컬 빌드 md5 `f59709d887d84af9f919ce860385511e`** — 일치.
- `index.html` 이 가리키는 해시 자산 `assets/index-CZFndcLN.css` · `assets/index-D5BlvQHg.js` 둘 다 **200**.
- 직전 판(`release.md`)의 `index.html` md5 는 `d360bb38…` 이었다 — 값이 바뀌었으므로 갱신이 실제로 반영됐다.

### ⑥ `deploy_doctor --env dev` — 한 번의 실행

진입점 = `infra/ops/probes/deploy-verification.sh`(EC2 `/opt/colab-repo` 의 배포 sha 트리 · 이미지 `colab-v2/core-api:dev-71ee15757737`).

```
항목 15 — ✓ 15 · ✗ 0 · ─ 0
전 항목 통과 (─ 0 — 15 항목이 실제로 돌았다)
DOCTOR_EXIT=0
```

- 실행 1회(2026-09-12 14:25:03Z) · 재시도 0 · `--allow-skip` 미사용 · 부분 실행 합산 0.
- ⑥ `0030_merge_audit_and_backoffice (DB = 레포)` · ⑦ `0007_merge_vocab_and_category` · ⑧ 테이블 **50건** 전부 FORCE RLS ＋ 경계 정책 · ⑨ `colab_app` 소유 0(전체 41: `colab_owner` 41) · ⑪ 자격 출처 `imds` · ⑭ 백업 0.2시간 전 · 객체 55건.
- ⑮ 축자 = `71ee15757737 ∈ main (origin/main=71ee15757737 · 반입 시 조상 확인됨)`.

### ⑦ 제품 확인 — 비밀번호 없이 닿는 것만

Ted 의 운영자 계정 비밀번호가 없으므로 **로그인이 필요한 확인은 하지 않았다.** 상태 코드만 읽고 본문·토큰은 출력하지 않았다.
판독 규약 — `401` = 경로 있음(인증 앞단에서 차단) · `405` = 경로 있음, 그 메서드가 없음 · `404` = 경로 없음.
앱이 OpenAPI 를 내주지 않으므로(`main.py` `openapi_url=None`) 이것이 라우트 표를 읽는 유일한 무자격 수단이다.

| 호출 | 실측 | 판독 |
|---|---|---|
| `GET /api/v1/admin/accounts` | **401** | `listServiceAccounts` 존재. **직전 판에서는 405 였다**(`release.md` §1 — `POST` 만 있었다) |
| `POST /api/v1/admin/accounts` | 401 | `createServiceAccount` 존재 |
| `GET /api/v1/admin/accounts/{id}/password-reset` | **405** | `resetServiceAccountPassword`(POST) 존재 |
| `GET /api/v1/admin/accounts/{id}/operator` | **405** | `setServiceAccountOperator`(POST) 존재 — 지정·해제는 **한 경로**이고 요청 본문 `{operator: true|false}` 로 갈린다(`fe-core.yaml:311`) |
| `GET /api/v1/admin/accounts/{id}/status` | **405** | `setServiceAccountStatus`(POST) 존재 |
| `GET /api/v1/admin/accounts/{id}/no-such-route` | **404** | **대조군** — 없는 경로는 실제로 404 다. 위 405 셋이 「존재」를 뜻한다는 근거 |
| `GET /api/v1/admin/account-options` | 401 | 기존 경로 무변 |
| `GET /api/v1/me` | 401 | 인증 앞단 동작 |

### ⑧ 태그

- `infra/dev/tag-release.sh dev` → **`dev-20260912-2` → `71ee15757737`**(로컬 · **미push**). 같은 날 기존 `dev-20260912-*` 1건이라 N=2.
- 대상 sha 는 로컬 `dist/colab-v2-dev.sha` 이고 EC2 를 읽지 않는다(스크립트 규약). 이번에는 **실적용 sha 와 같다**.
- 원격 반영(`git push origin dev-20260912-2`)은 오케스트레이터 몫이다.

## 3. 읽기 전용·비가역 규율

- 사용자 데이터에 `SELECT` 외의 조작 0. `DELETE`·`UPDATE` 손 실행 0. DDL 은 **alembic 체인과 문서화된 롤 SQL(REVOKE/GRANT)** 뿐이다.
- `ops/purge_datasets.py` 미실행. `main` push 0 · 태그 push 0 · PR 조작 0.
- 접속 문자열·비밀번호·토큰을 화면·레포·보고 어디에도 적지 않았다. 롤 비밀번호는 기존 시크릿 파일에서 파생해 **표준입력으로만** 넘겼고 회전하지 않았다.

## 4. 원장 행 문안 (오케스트레이터가 `PLAN-SoT §9` 에 옮긴다 — 이 레인은 쓰지 않는다)

> dev 배포 — 2026-09-12(2차). 실적용 코드 sha `71ee15757737`(= `origin/main`). 태그 `dev-20260912-2` → `71ee15757737`(로컬 · 미push).
> 마이그레이션 `0028_account_status` · `0029_operator_read_policy` · `0030_merge_audit_and_backoffice` 적용 — 적용 전 `0027_operator_audit`, 적용 후 `0030_merge_audit_and_backoffice`. ai 체인 `0007_merge_vocab_and_category` 무변.
> 적용 전 백업 = `_ops/backups/dev/2026-09-12T141450Z-colab_platform.sql.gz`(109,584 B) ＋ 같은 세대 ai.
> `account-admin-role.sql` 재적용으로 `service_operator` INSERT·DELETE 와 `d2_member_role` SELECT 를 부여(전 `f` → 후 `t`).
> 프런트 번들 `index.html` md5 `f59709d887d84af9f919ce860385511e` = CloudFront 본문 일치.
> `deploy_doctor --env dev` **15/15 · 한 번의 실행 · exit 0**(2026-09-12 14:25:03Z). 집행 창 = 2026-09-12 14:14~14:25Z.
> ⚠ `account-admin-role.sql` 의 `ALTER ROLE … NOSUPERUSER …` 는 RDS 에서 성립하지 않아 그 한 문장을 빼고 적용했다(후속 항목).

## 5. 원한 결과 대조 (미달 · 초과)

지시문 8단계 기준.

| 단계 | 판정 |
|---|---|
| ① 선행·백업 | 충족 |
| ② 마이그레이션 `0030` | 충족 |
| ③ 롤 재적용·`has_table_privilege` | **조건부 충족** — 요구한 GRANT 4건은 전부 `t`. 다만 문서 경로 그대로는 실행되지 않아 한 문장을 뺐다(§2③) |
| ④ 빌드·반입·교체·트리·sha 파일 | 충족 |
| ⑤ 프런트 번들·hash 대조 | 충족 |
| ⑥ `deploy_doctor` 1회 15/15 | 충족 |
| ⑦ 무자격 API 확인 | 충족 |
| ⑧ 태그·보고·라운드·HANDOFF·커밋 | 충족 |

- **미달 0건.**
- **초과 1건** — `dev.env` 의 `COLAB_IMAGE_TAG` 갱신(`dev-0a4aecb58e68` → `dev-71ee15757737`). 지시문에 없지만 **없으면 옛 이미지로 마이그레이션·기동이 돌아** 이번 회차가 성립하지 않는다. 직전 파일은 `dev.env.bak-before-71ee15757737` 로 보존했다.
- **[미확인]** 로그인한 상태의 제품 동작(계정 목록 표가 실제로 그려지는가 · 재설정·비활성화·관리자 토글이 200 을 내는가). **Ted 의 비밀번호가 없어 이 레인에서 닫히지 않는다.** 닿은 자리는 라우트 표와 롤 권한까지다.
- **[미확인]** 운영자 판정(`_require_operator`) 통과 자체. `operator.md §5` 의 [미확인]이 그대로 남아 있다 — Ted 의 첫 비밀번호 변경 뒤에만 관측된다.

## 6. 후속 항목 (이 레인은 고치지 않았다)

1. **`services/core-api/ops/account-admin-role.sql` 이 dev(RDS)에서 통째로 실패한다.** `ALTER ROLE … NOSUPERUSER …` 한 문장 때문이고, `ON_ERROR_STOP` 이라 뒤의 REVOKE·GRANT 가 한 줄도 안 돈다. **걸리는 검사 = 없다** — `deploy_doctor` ⑨ 는 `colab_app`·`colab_owner` 속성만 보고, 롤 권한 대조는 게이트에도 doctor 에도 없다. 드러나는 자리는 런타임 500 하나다. 고칠 자리 = 그 문장을 「속성 대조 ＋ 어긋나면 예외」로 바꾸거나 비밀번호 재설정만 남기는 것.
2. **`db-bootstrap.sh` 가 EC2 `/opt/colab-v2` 에 없다.** `ship.sh` 의 ops 소스 번들 목록(`infra/ops`·`infra/notifications`)에 `infra/dev`·`infra/staging` 이 빠져 있어, 롤 단계는 **손으로 민 `/opt/colab-repo`** 에만 의존한다. 트리가 낡으면 옛 롤 SQL 이 적용된다 — 이번에도 트리는 `0026` 세대로 낡아 있었다.
3. **배포 레포 트리 어긋남을 잡는 검사가 여전히 없다**(`release.md §6` 과 같은 항목 · 이번에도 실제로 어긋나 있었다).
4. **`deploy_doctor` 가 인증 DB·롤 권한을 보지 않는다.** 15/15 가 green 인 채로 백오피스 목록이 500 일 수 있다 — 이번 회차의 §2③ 이 정확히 그 구간이었다.
