# infra/prod — AWS prod 한 벌

> **이 디렉터리는 `infra/dev` 의 사본이고, 값만 다르다.** 공통화하지 않은 이유가 아래 §1 이다.
> 절차의 정본은 `docs/DEPLOY.md §5`(재구성 절차)다 — **그 절만 보고 세우는 것이 그 문서의 인수 시험**이고,
> 이 파일은 그 절이 말하지 않는 **prod 만의 차이**를 적는다.

## 1. 왜 dev 를 파라미터화하지 않고 복사했나

`infra/dev/compose.yml:13-14` 가 축자로 적어 뒀다 —

> 저장 모드·버킷·리전은 **리터럴**이다. 치환으로 두면 빠뜨렸을 때 기본 `local` 이 이겨
> EC2 디스크에 쌓이고 전송 op 가 501 을 내며 FE 가 폴백해 **「성공처럼」 보인다**.

한 파일을 두 환경이 공유하면 그 「빠뜨림」이 **dev 작업 중에 prod 를 오염시킬 자리**가 된다.
`CLAUDE.md` 배포 절 8번(「DB 와 저장 백엔드를 따로 바꾸지 않는다 — env 파일을 통째로 바꿔 끼운다」)이
금지하는 바로 그 모양이다. **환경마다 한 벌씩 두고, 통째로 갈아 끼운다.**

## 2. dev 와 다른 것 — 넷

| | dev | prod | 왜 |
|---|---|---|---|
| **앱 IAM 정책** | `DiagnosticsDevOnly` 문 있음 | **없음** | 앱은 버킷 설정을 읽을 일이 없다. 서버가 털렸을 때 구성까지 새지 않게 한다 (`〈342〉`-㉯) |
| **운영자 IAM 정책** | `GetBucketTagging` 없음 | **있음** | 없으면 비용 할당 태그를 **도구로 못 잰다** — 2026-09-06 에 실제로 403 이 났고 눈으로만 확인해야 했다 |
| **CORS** | 배포 주소 ＋ `localhost:5173` | **배포 주소만** | 정본 `S3.md §1` 「그 환경의 실오리진만 · prod 는 와일드카드 금지」. ⛔ prod 버킷에 개발 기계 오리진을 열지 않는다 |
| **RDS 백업 보존** | **1일**(Free Plan 때 값) | **7일** | 시점 복구(PITR)가 그 기간 안에서 딸려 온다 — `〈256〉` 이 prod 개통 관문으로 정한 것이 이것이다 (`〈383〉`-㉯) |

## 3. 태그 — 자원을 만들 때 붙인다

모든 prod 자원에 **`Environment = prod`**.

⛔ **소급되지 않는다.** 비용 할당 태그는 활성화 시점부터의 비용만 가르고, 그 이전은 영영 못 가른다.
그리고 태그는 **그것을 쓴 자원이 하나라도 있어야** 콘솔의 「비용 할당 태그」 목록에 나타난다 —
자원을 만든 뒤 그 목록에서 **활성화**해야 예산 필터가 작동한다.

⚠ 콘솔이 개편돼 「사용자 정의 비용 할당 태그」 **탭은 없다**(2026-09-06 실측 · 한 목록에 합쳐졌다).

## 4. 배포 규율 — dev 와 다르다

`infra/README.md` 축자 — **prod 는 `main` 커밋에 태그를 찍고 태그에서만 배포한다.**
`〈335〉`-㉳ 가 확정한 것이고, **prod 용 장기 브랜치를 만들지 않는다.**

  - **dev** = `main` 이 곧 배포 기준
  - **prod** = dev 가 배포 창 N회를 green 으로 넘긴 `main` 커밋에 `prod-YYYYMMDD` 태그 → **그 태그에서만**
  - **핫픽스** = 태그에서 브랜치 → 수정 → `main` 에 되돌려 넣는다

⭑ **⟨증보 2026-09-12⟩ 위 규율은 이제 산문이 아니라 `ship.sh` 안의 검사다**(규칙 6 · `docs/BRANCHING.md` §1·§5).
`infra/prod/ship.sh` 가 `infra/_lib/ship-gate.sh`(dev 와 **같은 한 벌**)를 불러 둘을 잰다 —

| 검사 | 거절 | 우회 |
|---|---|---|
| 후보 sha ∈ `origin/main` | exit **65** (`origin` 조회 실패는 exit **78**) | `COLAB_SHIP_ALLOW_NONMAIN=1` **선언**(출력 ＋ `MAIN_SHA` 의 `ancestor=bypass` ＋ `deploy_doctor` ⑮ 의 ✗ 셋에 남는다) |
| 후보 sha 에 `prod-*` 태그 | exit **65** | ⛔ **없다** — 태그를 먼저 찍는다 |

통과하면 같은 ssh 가 `/opt/colab-v2/MAIN_SHA` 에 `main=… candidate=… ancestor=…` 한 줄을 적고,
`deploy_doctor` ⑮ 가 `CURRENT_SHA` 와 대조한다. 셸 시험 = `infra/prod/tests/ship-gate.sh`(6 케이스).

## 4-b. `/etc/colab` 시크릿 파일 — 11종

`compose.yml` 이 **파일 단위로** 마운트한다(디렉터리째 걸면 `700 root` 라 uid 10001 이 못 지난다).
⛔ **값은 이 표에 적지 않는다.** 적는 것은 이름·읽는 쪽·롤·소유뿐이다.

| 파일 | 읽는 쪽 | DB 롤 · 용도 | 소유 · 모드 |
|---|---|---|---|
| `core-database.url` | `core-api` 컨테이너 | `colab_app` @ `colab_platform` — 앱 질의(RLS 걸림) | `10001` · 0600 |
| `account-admin-database.url` | `core-api` 컨테이너 | `colab_account_admin` @ `colab_platform` — 로그인·계정 목록·운영자 지정. **앱 롤과 자격을 공유하지 않는다** | `10001` · 0600 |
| `subjects.json` | `core-api` 컨테이너 | 인증 주체 목록(DB 아님) | `10001` · 0600 |
| `credentials.json` | `core-api` 컨테이너 | 파일 자격 목록(DB 아님) | `10001` · 0600 |
| `pipeline-db.url` | `pipeline-worker` 컨테이너 | `colab_app` @ `colab_platform` | `10001` · 0600 |
| `ai-db.url` | `ai-service` 컨테이너 | `colab_ai_app` @ `colab_ai` — SELECT 만 | `10001` · 0600 |
| `platform-owner-db.url` | `migrate-platform`(＋ `deploy-doctor.sh`) | `colab_owner` @ `colab_platform` — 마이그레이션·⑥ 판정 | `10001` · 0600 |
| `ai-owner-db.url` | `migrate-ai`(＋ `deploy-doctor.sh`) | `colab_owner` @ `colab_ai` — 마이그레이션·⑦ 판정 | `10001` · 0600 |
| `ownership-platform-db.url` | **호스트 cron** `publish-ownership-hourly.sh` | `colab_backup` @ `colab_platform` — 소유권 스냅샷은 전수를 읽어야 하므로 BYPASSRLS 롤이다. **드라이버 접두는 `postgresql+psycopg://`**(dev 실측 · `dev-package/reports/stage12-tl2-deploy/release.md`) | `root` · 0600 |
| `operator-database.url` | **호스트 운영자 런타임**(`COLAB_OPERATOR_DATABASE_URL`) | `colab_operator_runtime` @ `colab_platform` — `colab_operator_exporter` 묶음 하나만 물린다(`db-bootstrap.sh operator`) | `root` · 0600 |
| `ops-slack-webhook.url` | **호스트 cron** `dispatch-current.sh --webhook-file` | DB 아님 — 배포·관측 probe 의 Slack 수신처(dev 실물 이름 · `dev-package/reports/i4-slack-closeout/results.json`) | `root` · 0600 |

⚠ **아래 셋은 컨테이너가 읽지 않는다** — `ownership-platform-db.url`·`operator-database.url`·`ops-slack-webhook.url`.
호스트의 root 작업(cron·운영자 런타임)이 읽으므로 **`root` 소유**이고 compose 에 마운트 줄이 없다.
`10001` 로 만들면 root 작업은 읽히지만 **연구실 경계를 우회하는 자격이 컨테이너 유저에게도 보인다.**

⚠ 운영자 알림의 **Slack webhook 값 자체**는 파일이 아니라 AWS Secrets Manager ARN 경유다
(`infra/notifications/handlers.py` `secret_arns`). 위 `ops-slack-webhook.url` 은 그것과 별개인
**probe 계열**(`infra/ops/dispatch-current.sh`)의 수신처다. 둘을 같은 것으로 묶지 않는다.

## 4-c. `prod.env` 필수 키

`up.sh` 가 `--env-file` 로 넘긴다. 소유 `ec2-user` · 모드 0600.
⭑ `:?` 가 붙은 것은 **없으면 기동에 실패한다** — 그것이 의도된 동작이다(`CLAUDE.md` 배포 절 6).

| 키 | 기본값 | 없으면 |
|---|---|---|
| `COLAB_IMAGE_TAG` | **없음**(`:?`) | 기동 실패. prod 는 태그에서만 배포한다 — `ship.sh` 가 `prod-<sha>` 로 적는다 |
| `COLAB_SECRETS_DIR` | **없음**(`:?`) | 기동 실패. `/etc/colab` |
| `COLAB_CORE_SESSION_SECRET` | **없음**(`:?`) | 로그인·다운로드가 서지 않는다 |
| `COLAB_VIZ_SERVICE_TOKEN` | **없음**(`:?`) | 미리보기 전량 503 |
| `COLAB_VIZ_TILE_SIGNING_SECRET` | **없음**(`:?`) | 기동 실패 |
| `COLAB_VIZ_WORK_MAX_BYTES` | **없음**(`:?`) | 기동 실패. 숫자 또는 `none`(명시 무제한) |
| `COLAB_VIZ_OWNERSHIP_SNAPSHOT_OWNER_UID` | **없음**(`:?`) | 기동 실패. 스냅샷을 적는 쪽의 uid — 호스트 cron 이 root 로 적으므로 `0` |
| `COLAB_VIZ_OWNERSHIP_SNAPSHOT_GROUP_GID` | **없음**(`:?`) | 기동 실패. **viz 컨테이너의 실제 gid**(dev 실측 `999` · prod 는 `docker exec … id -g` 로 잰다) |
| `COLAB_VIZ_OWNERSHIP_SNAPSHOT_MAX_AGE_SECONDS` | `7200` | 스냅샷이 이보다 오래면 viz 가 거절한다(정상 동작) |
| `COLAB_CORE_AI_BASE_URL` | `http://ai-service:8200` | — |
| `COLAB_MEM_*` · `COLAB_CPUS_*` | 표의 값 | — |

운영자 알림 런타임은 **`prod.env` 가 아니라 자기 0600 설정 파일**을 쓴다(`/etc/colab/operator-runtime.env` ·
`infra/notifications/run-runtime-job.sh` 가 `--config` 로 받아 source 한다). 필수 키 —
`COLAB_NOTIFICATION_ENVIRONMENT=prod` · `COLAB_NOTIFICATION_ROOT`(검증된 번들 루트) ·
`COLAB_NOTIFICATION_PYTHON`(그 번들의 `.operator-venv/bin/python` 절대경로) ·
`COLAB_OPERATOR_MANIFEST` · `COLAB_OPERATOR_SPOOL` · `COLAB_OPERATOR_STATE` ·
`COLAB_OPERATOR_DATABASE_URL`(＝ `operator-database.url` 의 값) ＋ `RUNTIME.md` 가 적은 AWS 키들.

## 4-d. 운영자 런타임 — 소스 번들 위에 세운다

절차 정본은 `infra/ops/OPERATOR_RUNTIME_SETUP.md` 다. 요지 —

1. `ship.sh` 가 이미 `/opt/colab-ops/versions/<sha>` 에 **검증된 소스 번들**을 풀어 두었다
   (manifest hash 대조 ＋ `verify-source.sh` · root 0755). 그 디렉터리가 런타임 루트다.
2. 그 루트에서 `python3.12 -m venv .operator-venv` → `requirements.txt` ＋ `infra/notifications/requirements.txt`
   → `--no-deps --no-build-isolation services/core-api`. **앱 가상환경을 건드리지 않는다.**
3. `manifest` 의 `runtime_python` 에 그 venv 파이썬의 절대경로를 적는다.
4. venv 는 생성물이라 hash manifest 에 들어가지 않는다 — root 소유 · group/world 쓰기 금지.
   **새 sha 를 반입하면 그 sha 의 venv 를 새로 만든다**(이전 sha 의 것을 덮지 않는다).
5. cron 연결은 `infra/prod/install-cron.sh`(§7)가 한다. 준비 실패(파이썬·의존·manifest 부재)면
   **일정을 켜지 않는다** — 그것이 fail-closed 다.

## 5. 백업이 dev 로 새지 않게 하는 장치

`infra/dev/backup.sh` 는 2026-09-06 까지 `COLAB_BACKUP_BUCKET` 기본값이 **dev 버킷**이었다.
prod 호스트에 그대로 올리면 **prod DB 를 덤프해 dev 버킷에 올리고 GREEN 을 보고했다** —
접속 문자열은 그 호스트 것이고 버킷만 기본값으로 떨어지기 때문이다.

⟹ 지금은 **버킷·벌 이름이 필수**(`:?`)이고 **크론이 값을 싣는다**(`install-cron.sh`). 양쪽에서 막는다.
`install-cron.sh` 는 `COLAB_ENV`·`COLAB_BACKUP_BUCKET` 를 요구하고 cron 파일도 `/etc/cron.d/colab-<벌>` 로 갈린다.

```bash
# prod EC2 에서
sudo COLAB_ENV=prod COLAB_BACKUP_BUCKET=colab-platform-data-prod /opt/colab-v2/install-cron.sh
```

## 6. 완료 판정

```bash
# prod EC2 위에서 · 한 번의 실행으로 · ─ 0
ops/deploy_doctor.py --env prod --endpoint https://<prod>.cloudfront.net …
```
⛔ **부분 실행 둘을 합쳐 green 이라 하지 않는다** — `─ 0` 이 나온 한 번의 결과만 근거다.
⭑ **⟨증보 2026-09-12⟩ 항목 수는 15 다**(⑮ 실행 sha ∈ main). `infra/prod/deploy-doctor.sh` 가
`-v /opt/colab-v2:/state:ro` 를 넘긴다 — 빼면 ⑮ 는 「마운트 없음」으로 **항상 ✗** 다.
⚠ 지금 돌고 있는 `prod-3922d01750d0` 은 규칙 6 이전 판이라 `MAIN_SHA` 가 없다 ⟹ **⑮ 는 ✗**.
`main` 재빌드 ＋ `prod-YYYYMMDD` 태그 ＋ `ship.sh` 반입으로만 지운다(`docs/DEPLOY.md §5-9`).
＋ **브라우저 실물** — 로그인 → 업로드 한 바퀴 → 파일 목록 → 다운로드 → 미리보기.
＋ **시점 복구를 되감아 본다**(`〈383〉`-㉯) — 「설정했다」는 관문이 아니다.

## 8. 한 번만 vs 재배포 때마다

⚠ **이 구분을 틀리면 두 방향으로 사고가 난다** — 한 번뿐인 것을 매번 하면 비밀번호가 회전해
살아 있는 접속이 끊기고, 매번 해야 하는 것을 한 번만 하면 **옛 이미지·옛 판정표로 green 이 난다.**

| 항목 | 언제 | 안 하면 |
|---|---|---|
| VPC·서브넷·보안그룹·IGW · EC2 인스턴스 · RDS · S3 버킷 2 · IAM 3 · CloudFront | **한 번** | — |
| `db-bootstrap.sh prep`·`roles`·`extensions` (소유자 롤·DB 2) | **한 번** | 마이그레이션이 붙을 롤이 없다 |
| `/etc/colab` 시크릿 11 (§4-b) | **한 번** · 자격 회전 때 다시 | 기동 실패 또는 런타임 500 |
| `db-bootstrap.sh app-grants`·`backup-role` | **한 번** · 새 표가 생긴 회차에 다시 | 앱 롤이 새 표를 못 읽는다 |
| `db-bootstrap.sh account-admin`·`operator` | **새 롤 권한이 바뀐 회차에 다시**(`0025`·`0027` 계열 마이그레이션이 낀 회차) | 로그인·백오피스·운영자 내보내기가 런타임 500. **걸리는 검사 없음** |
| 운영자 런타임 venv (§4-d) | **반입한 sha 마다** | 옛 sha 의 코드로 알림이 돈다 |
| `build.sh` → `tag-release.sh prod` → `ship.sh` | **매 배포** | — |
| `/opt/colab-repo` 동기화 (`ship.sh` 안) | **매 배포** | `deploy_doctor` ⑥⑦ 이 **옛 alembic head 를 정답으로 삼아 조용히 틀린다** |
| `prod.env` `COLAB_IMAGE_TAG` 갱신 (`ship.sh` 안) | **매 배포** | **옛 migrator 이미지로 마이그레이션이 돈다** |
| `up.sh`(마이그레이션 → 기동 → healthy 4) | **매 배포** | — |
| `install-cron.sh`(백업·업로드 정리·소유권 스냅샷·알림) | **매 배포**(멱등) | 스냅샷·백업이 옛 이미지 태그를 가리킨 채 남는다 |
| `deploy_doctor --env prod` **한 번의 실행** | **매 배포** | 완료 판정이 성립하지 않는다 |
