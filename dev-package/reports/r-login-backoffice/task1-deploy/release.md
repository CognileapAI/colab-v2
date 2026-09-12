# R-LOGIN-BACKOFFICE 작업 1 — dev 배포 기록

- 작성 2026-09-12 13:17 KST · 레인 `worktree-agent-a90befdd2b16c30a4` · 작업 id `8548d12f3a3e4ea4ae80c481d88307e7`
- 판정 결론 = **`deploy_doctor --env dev` 15/15 · 한 번의 실행 · exit 0**(2026-09-12 13:16 KST).

## 0. 착수 시점의 실물 — 지시문 전제와 다른 자리

지시문 전제 = 「`c71eed91` 을 dev 에 새로 올린다 · `alembic_version` 0024 → 0026」.
실측 = **배포가 이미 서 있었다.** 이 레인이 도착하기 전(2026-09-12 01:28~02:06 KST)에 다른 사본이 집행했고,
프런트 번들은 2026-09-12 10:54 KST 에 올라가 있었다.

| 실물 | 값 | 관측 근거 |
|---|---|---|
| `/opt/colab-v2/CURRENT_SHA` | `fc45a9aa7c64` | ssh `cat` |
| `/opt/colab-v2/MAIN_SHA` | `main=fc45a9aa7c64 candidate=fc45a9aa7c64 ancestor=yes` | ssh `cat` |
| core-api 컨테이너 | `colab-v2/core-api:dev-fc45a9aa7c64` · healthy | `docker ps` |
| pipeline-worker · viz-render · ai-service | `dev-42cffb328b1e` · healthy | `docker ps` |
| platform 체인 head | `0026_login_sessions` | 살아 있는 DB 조회 |
| `colab_account_admin` 롤 | 존재 | `pg_roles` 조회 |
| `${COLAB_DEV_SECRETS_DIR}/account-admin-database.url` | 존재 · 0600 · uid 10001 | `ls -l` 시크릿 디렉터리 |
| 프런트 번들 | `index-YdOxNYzp.js` · `index-BYbRg-dF.css` | CloudFront `index.html` |

`42cffb32 → c71eed91` 변경 경로 = `frontend`·`services/core-api`·`db/platform`·`infra/dev` 뿐이고
`services/pipeline-worker`·`viz-render`·`ai-service` 는 **변경 0**이다(`git diff --name-only`).
세 단위가 `dev-42cffb328b1e` 로 남아 있는 것은 코드 동일이며 미반영이 아니다.

`fc45a9aa` → `c71eed91` 의 diff 는 10파일 전부 문서·CI 다(`.github/workflows/ci.yml` · `CLAUDE.md` ·
`dev-package/**`). 코드 경로(`services/ frontend/ db/ infra/ contracts/ gates/`) diff = **0파일**.

## 1. 선행조건 증거

| 항목 | 명령 | 결과 |
|---|---|---|
| 기준 | `git merge --ff-only origin/main` | `Already up to date` · HEAD `c71eed9164321b84e0702ee2c6250a2292e993db` — 기대치 일치 |
| P0 로컬 | `COLAB_TASK_ID=… COLAB_GATE_REPORT_DIR=… bash gates/run.sh task` | `frontend-typecheck` green · `frontend-test` green(통과 1253 · 실패 0) · **계 green 2 / red(판정) 0 / red(준비) 0** |
| P0 배출 | `agent-bridge.py verify-report --task …` | `green: task identity, explicit report/gates and current working files verified` |
| P3 백업(마이그레이션 前) | EC2 `stage3-dual-20260912/platform-before.sql.gz` 를 `zcat \| grep` | `alembic_version_platform = 0024_s2_grid_convenience` · 덤프 시각 2026-09-12 01:28 KST |
| P3 백업(정기) | `aws s3 ls s3://colab-platform-data-dev/_ops/backups/dev/` | 마이그레이션 직전 세대 `2026-09-11T115350Z-colab_platform.sql.gz` · 최신 `2026-09-11T190001Z-*` |
| P3 적용 후 | 살아 있는 DB `SELECT version_num FROM alembic_version_platform` | `0026_login_sessions` — 기대치 일치 |
| P2 순서 | 실측 시각 — 덤프 01:28 → 이미지 load 01:29~01:35 → ops 번들 01:50 → 롤·시크릿 파일 01:52 → core-api 교체 01:52 → `MAIN_SHA` 02:06 | 마이그레이션 → 롤 → 시크릿 → 기동 순서가 지켜졌다 |
| P1 시크릿 선행 | 시크릿 디렉터리 `ls -l` | `account-admin-database.url` 0600 · uid/gid 10001 · 2026-09-12 01:52 — 이미지 교체와 같은 분에 선행 |
| P5 프런트 | `npm run build`(이 워크트리 `c71eed91`) → 산출물 해시 대조 | `index-YdOxNYzp.js`·`index-BYbRg-dF.css` 로 **동일 파일명(내용 해시)** · `index.html` md5 `d360bb38628e73fbbc3ce2f4a8f97ca1` = CloudFront 본문 md5 **일치** |
| P4 인증 DB | `colab_account_admin` 접속 `SELECT count(*)` | `login_credential` 0 · `service_operator` 0 · `login_session` 7 — 접속·조회 권한 동작 |
| P4 경로 | `curl -X PUT …/api/v1/me/password` | 401 JSON `UNAUTHORIZED` — 경로 존재(로그인 강화 코드가 실제로 떠 있다) |
| P4 경로 | `curl …/api/v1/admin/accounts` | 405 — 경로에 `POST` 만 있다(작업 3 의 `GET` 은 아직 없다 · 배포본이 `fc45a9aa` 수준임을 재확인) |

## 2. `deploy_doctor` 선행 단계 — `/opt/colab-repo` 동기화

`infra/dev/README.md` 「선행 단계」대로 배포 sha 트리를 밀었다. 밀기 전 EC2 쪽 `db/platform/versions`
최신은 `0024_s2_grid_convenience.py` 였다 — **살아 있는 DB(0026)와 어긋나 ⑥ 이 옛 head 를 정답으로 삼는 자리**였다.

```
tar czf /tmp/repo.tgz --exclude=__pycache__ --exclude=.venv db gates services/core-api/ops infra
scp /tmp/repo.tgz <dev>:/tmp/ ; ssh <dev> 'sudo tar xzf /tmp/repo.tgz -C <배포 레포 경로> --overwrite'
```

md5 대조(개발 기계 = EC2) — `ops/deploy_doctor.py` `a2d5651512ff786f0a71eeb36e51ed9c` ·
`db/platform/versions/0026_login_sessions.py` `7a852e2d3cac8c83d73b1d0b21dba640` ·
`gates/tools/rls_coverage.py` `d91556ed4b165ce21bec96e4295729a7`.

## 3. `deploy_doctor` — 한 번의 실행

`docs/DEPLOY.md §6-1` 명령 그대로. 이미지만 `colab-v2/core-api:dev` 대신 **`:dev-fc45a9aa7c64`** 를 썼다
(`:dev` 태그가 2026-09-11 판을 가리켜 배포본과 갈리기 때문이다 · 검사 대상은 줄이지 않았다).
운영자 키는 `--env-file` 로 잠깐 넘기고 **실행 직후 `shred -u`** 했다(EC2·개발 기계 양쪽).

```
항목 15 — ✓ 15 · ✗ 0 · ─ 0
전 항목 통과 (─ 0 — 15 항목이 실제로 돌았다)
DOCTOR_EXIT=0
```

재시도 없음 · 부분 실행 합산 없음. ⑮ 축자 = `fc45a9aa7c64 ∈ main (origin/main=fc45a9aa7c64 · 반입 시 조상 확인됨)`.

## 4. 태그

- 생성(로컬) `dev-20260912-1` → **`fc45a9aa7c64`**. 같은 날 기존 `dev-20260912-*` 0건이라 N=1.
- ⚠ **지시문은 `c71eed91` 을 지목했으나 그 sha 로 찍지 않았다.** `docs/BRANCHING.md §2` 표가
  이 태그의 대상을 **「dev 실적용 sha」**로 못박고 있고, 실적용 sha 는 `fc45a9aa7c64` 다
  (`CURRENT_SHA`·`MAIN_SHA`·컨테이너 이미지 태그 셋이 모두 그 값이다). `c71eed91` 로 찍으면
  **돌고 있지 않은 sha 를 배포 기록으로 남긴다.** 두 sha 의 코드 diff 는 0파일이므로 제품 차이는 없다.
  오케스트레이터가 `c71eed91` 을 원하면 `git tag -d dev-20260912-1` 뒤 다시 찍으면 된다(로컬 태그 · 미push).
- push 하지 않았다. 원격 반영은 오케스트레이터 몫이다.

## 5. 원장 행 문안 (오케스트레이터가 `PLAN-SoT §9` 에 옮긴다 — 이 레인은 쓰지 않는다)

> dev 배포 — 2026-09-12. 실적용 코드 sha `fc45a9aa7c64`(= `origin/main` `c71eed916432` 와 코드 diff 0파일 ·
> 차이는 문서·CI 10파일). 태그 `dev-20260912-1` → `fc45a9aa7c64`(로컬 · 미push).
> 마이그레이션 `0025_stage3_accounts` · `0026_login_sessions` 적용 — 적용 전 `0024_s2_grid_convenience`,
> 적용 후 `0026_login_sessions`. 적용 전 백업 = EC2 덤프 `stage3-dual-20260912/platform-before.sql.gz`
> (2026-09-12 01:28 KST) ＋ S3 `_ops/backups/dev/2026-09-11T115350Z-colab_platform.sql.gz`.
> `colab_account_admin` 롤·시크릿 파일 `account-admin-database.url` 배치 완료.
> 프런트 번들 = `c71eed91` 빌드와 `index.html` md5 일치. `deploy_doctor --env dev` **15/15 · 한 번의 실행 · exit 0**
> (2026-09-12 13:16 KST). 배포 집행 창 = 2026-09-12 01:28~02:06 KST(백엔드·DB) ＋ 10:54 KST(프런트),
> 판정 실행 = 13:16 KST.

## 6. 남은 것

- **[Ted 입력 대기] 서비스 운영자 1명 등록.** `account_admin.service_operator` **0행**이라 지금은
  `POST /admin/accounts` 가 누구에게나 403 이다. 등록 스크립트 `services/core-api/ops/provision-service-operator.sql`
  는 **`account_id`(UUID)** 를 받는데, 어느 계정을 운영자로 세울지가 정본·원장·docs 어디에도 없다
  (`운영자 계정`·`operator email` grep 전무). **추정으로 채우지 않고 멈췄다.**
- **[미확인] 실제 로그인 1회(`POST /sessions` → 200).** `login_credential` **0행**이라 DB 기반 계정이 없고,
  이 레인은 비밀번호를 만들 권한이 없다. 운영자 등록이 닫히면 같이 닫힌다.
- **[후속] 배포 레포 트리가 배포 sha 와 어긋나도 아무 검사에 걸리지 않는다.** 이번에도 실제로 어긋나 있었고
  (트리 0024 / DB 0026), 밀지 않았다면 `deploy_doctor` ⑥ 이 **옛 head 를 정답으로 삼아** 조용히 틀렸다.
  이 어긋남을 잡는 자리는 `infra/dev/README.md` 산문뿐이고 게이트에도 `infra/dev/ship.sh` 에도 없다.
  `ship.sh` 가 ops 번들을 hash 대조로 심는 것과 달리 `deploy_doctor` 가 읽는 트리는 손 tar 다.
- **[후속] 이번 배포에는 배포 기록이 없었다.** EC2 에 `.stage3-deployment.lock`(0바이트) 과
  `auth-role.private.log`(0바이트) 가 남아 있으나 어느 사본이 언제 무엇을 했는지는 파일 mtime 으로만 재구성된다.
  다음 회차 전에 이 잠금 파일의 처분 주체를 정할 필요가 있다 — 이 레인은 건드리지 않았다.
