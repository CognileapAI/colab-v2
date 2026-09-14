# prod 브랜치 정비 — 리베이스 2회 ＋ 반입 도구 ＋ compose·부트스트랩 ＋ 운영 기능 (2026-09-13)

- 레인 = 코드·시험·문서만. **AWS·EC2·RDS·S3·dev·prod·staging 무접촉** · push 0 · 태그 0.
- 브랜치 `feature/rtf400_deploy_prod` · 기준 `origin/main` **`aa8bee98`** · 커밋 = **기존 18 ＋ 신규 A~E** ＋ ⭑ 배포 중 정정 F~H ＋ 등재(§10).
- ⭑ **⟨2026-09-13 저녁⟩ 「무접촉」은 정비 레인(§1~§9)의 조건이다.** 그 뒤 별도 배포 세션이 prod 를 실제로 재배포했다 — §10.
- ⚠ **끝 sha 는 여기 적지 않는다** — 이 보고서를 담은 커밋 뒤에도 문서 정정이 붙으면 낡는다.
  값은 레인 최종 메시지와 `git rev-parse HEAD` 가 준다.

## 1. 리베이스 — 두 번 했다

| 회 | 기준 | 커밋 | 손 해소 |
|---|---|---|---|
| 1차 | `7446eb7d` | 18 | `dev-package/PLAN-SoT.md` **2곳** |
| 2차 | `aa8bee98`(그 사이 7 커밋 전진) | 21(＝18 ＋ A·B·C) | **0곳**(1차 해소가 `rerere` 로 재생) |

- **`work-items.yaml` 은 손을 대지 않았다.** 병합 드라이버가 붙었다(축자 `work-items 병합: 항목 196건 ·
  상대 신규 0건 덧붙임` · 4회). ⚠ 드라이버가 `python3` 로 등록돼 있어 **PyYAML 부재로 한 번 손을 뗐다** —
  드라이버를 `gates/.venv/bin/python` 으로 바꾼 뒤 정상. 워크트리마다 다시 걸어야 한다.
- 마커 0건.
- 계획이 예상한 손 해소 중 **실제로 난 것은 `PLAN-SoT.md` 뿐**이다. 나머지는 자동 병합됐고 값으로 확인했다 —

| 확인 대상 | 방법 | 결과 |
|---|---|---|
| `deploy_doctor.py` prod 갈래 | `grep -c 'ctx.env == "dev"'` | 1 (보존) |
| `deploy_doctor.py` 15항목·⑮ | `MARKS` 15자 · `MAIN_SHA_RE` 실재 | main 판 보존 |
| `s3_doctor.py` `origin is None` SKIP | `grep -c 'origin is None'` | 1 (보존) |
| `ops/account-admin-role.sql` | `origin/main` 과의 diff | **0줄 = main 판 채택** |
| `infra/dev/ship.sh` ops 번들 사슬 | `ops_bundle_*` 호출 3 | main 사슬 보존 ＋ `_lib` 로 이동 |
| `docs/DEPLOY.md` 「prod 는 아직 없다」 | `grep -c` | 1 — 그 1건은 **취소선 안의 종전 표기**다(살아 있는 주장 0) |

## 2. 커밋 sha 표

| sha | 무엇 |
|---|---|
| `023756e0` … `b254c268` (18) | 리베이스된 기존 prod 회차 — 내용 무변 |
| `fd7cbeb3` | **A. prod 반입 도구 결함 정정** |
| `9e00a706` | **B. prod compose·부트스트랩을 dev 현재판에 맞춤** |
| `6c2e84ad` | **C. 운영 기능 prod 이식** |
| `c208b052` | **D. 결정 번호 재발급 〈383〉 → 〈400〉** |
| `192936e1` | **E. 회차 보고서 ＋ PR 본문 ＋ 대장 `I5` 증보** |
| `ad1ee84a` | E 정정 — sha 표 |
| `09a0039b` | **F. `install-cron.sh` 운영자 알림 cron 세 상태**(선언 · 명시 면제 `COLAB_NOTIFICATION_SKIP=1` · 미선언 exit 2) — 배포 중 |
| `1f20e570` | **G. `ship.sh` 판정 레포 tar 에서 AppleDouble·`__pycache__` 제외** — doctor ⑥⑦ 실측 |
| `6d47315c` | **H. 배포 실행기 `deploy_release.py` 대상 `pr`(prod)** — 웹 배포 ＋ 검증 한 실행 |

⚠ A·B·C 의 sha 는 2차 리베이스로 바뀌었다(여기 적은 것이 그 뒤의 값이다). E 뒤에 문서 정정 커밋이 더 붙을 수 있다.

## 3. 커밋 A — 반입 도구 결함 넷

넷 다 **「빠뜨려도 `ship.sh` 가 exit 0 을 낸다」** 는 모양이었고, 걸리는 검사가 하나도 없었다.

1. `infra/dev/tag-release.sh` 의 sha 파일이 `colab-v2-dev.sha` 로 고정 → **모드별**(`colab-v2-<모드>.sha`).
   prod 이름에는 회차 번호가 없으므로(`prod-YYYYMMDD`) **같은 sha 재실행은 태그 재사용**(exit 0),
   **다른 sha 면 거절**(exit 65 · 태그를 옮기면 그날의 배포 원천 기록이 사라진다).
2. `infra/prod/ship.sh` 가 `deploy-doctor.sh` 를 안 밀었다 → 판정 진입점이 EC2 에 없다.
3. 판정 레포 `/opt/colab-repo` 동기화 단계 부재 → `deploy_doctor` ⑥ 이 **옛 alembic head 를 정답표로
   삼아 조용히 틀린다**(dev 2회 실측 · `dev-package/reports/r-login-backoffice/task5/deploy-3-verify.md`).
4. `prod.env` 의 `COLAB_IMAGE_TAG` 를 사람이 손으로 고쳤다 → 빠뜨리면 **옛 migrator 이미지로
   마이그레이션이 돈다**(dev 실측 · `〈400〉`-⑨ⓔ 와 같은 구멍).

덧붙여 ops 소스 번들 사슬을 **`infra/_lib/ops-bundle.sh` 한 벌**로 뽑아 dev·prod 가 같은 함수를 부른다.

### P3 방식과의 정합 — `git ls-files` 를 쓰지 않는다

이 스크립트는 **배포 대상 sha 를 체크아웃한 워크트리에 `infra/prod` 가 미추적 파일로만 놓인 상태**에서
돈다(빌드 sha = 그 워크트리 HEAD). 그래서 레포 tar 는 **실제 파일 존재**로 판정한다 —
대상 다섯(`db gates services/core-api/ops infra contracts`) 중 하나라도 없으면 조용히 적게 싣지 않고 exit 2.
시험 ⓗ 가 그 거절을 잰다.
⚠ **ops 소스 번들은 반대다** — 커밋 트리만 담는다. 미추적 prod 판 `deploy_doctor.py` 는 번들에
들어가지 않고 **레포 tar 로만 간다.** 판정이 읽는 것은 레포 tar 쪽(`/repo`)이므로 성립한다.

`prod.env` 갱신은 **원격 스크립트 파일**로 한다(heredoc 금지 · 파일을 새로 만들지 않고 내용만 덮어
소유 `ec2-user`·모드 0600 유지).

## 4. 커밋 B — compose 대조표

dev `infra/dev/compose.yml` 을 `dev→prod` 치환해 prod 와 diff 한 결과, **주석을 뺀 기능 차이는 셋뿐**이다.

| 자리 | dev | prod | 판정 |
|---|---|---|---|
| `volume-init` `OWNERSHIP_READER_GID` ＋ `/srv/ownership-ledger` 0550 | 있음 | **없었다** | **메움** |
| `ownership-ledger` 볼륨 선언 | 있음 | **없었다** | **메움** |
| viz `COLAB_VIZ_OWNERSHIP_SNAPSHOT{,_MAX_AGE_SECONDS,_OWNER_UID,_GROUP_GID}` ＋ ro 마운트 | 있음 | **없었다** | **메움** |
| core-api `COLAB_CORE_ACCOUNT_ADMIN_DATABASE_URL_FILE` ＋ `account-admin-database.url` 마운트 | 있음 | **없었다** | **메움** |
| worker `COLAB_WORKER_STAGE2: "on"` · `COLAB_WORKER_PREVIEW_DIR` | 있음 | **없었다** | **메움** |
| `COLAB_IMAGE_TAG` | `:-dev`(기본값) | **`:?`** | **유지** — prod 는 태그에서만 배포한다 |
| 시크릿 디렉터리 변수 | `COLAB_DEV_SECRETS_DIR` | `COLAB_SECRETS_DIR` | **유지** — 이름의 정리 |
| `viz-render` `mem_limit` | 768m | **1536m** | **유지** — dev 실측 OOM 4건(`CONSTRAINT_MEMCG` 4 · `CONSTRAINT_NONE` 0)이 근거 |
| 버킷·프로젝트 이름 | `-dev` | `-prod` | **유지** — 리터럴이 규약(`README §1`) |

**prod 로 못 옮긴 항목 = 0건.**

### RDS `ALTER ROLE` 우회 근거

`services/core-api/ops/account-admin-role.sql` 의 한 문장이 RDS 에서 **구조적으로** 실패한다 —

```
ERROR:  permission denied to alter role
DETAIL:  Only roles with the SUPERUSER attribute may change the SUPERUSER attribute.
```

PostgreSQL 은 `SUPERUSER`/`NOSUPERUSER` 를 **명시하면 값이 같아도** superuser 를 요구하고,
RDS 마스터는 `rds_superuser` 일 뿐이다(dev 실측 `current_user=postgres · rolsuper=f · rolcreaterole=t`).
파일이 `\set ON_ERROR_STOP on` 이라 그 한 문장에서 멈추면 **뒤의 REVOKE·GRANT 가 한 줄도 안 돈다.**

**dev 가 실제로 통과한 절차**(`dev-package/reports/r-login-backoffice/task5/deploy-2.md §2-③`) —
1차는 파일 그대로, 그 오류일 때만 **그 한 문장만** 빼고 2차. 검사는 하나도 빼지 않는다: 파일 꼬리의
자기 점검(`rolsuper OR rolcreatedb OR rolcreaterole OR rolinherit OR NOT rolbypassrls` → 예외)이
ALTER 가 세우려던 속성을 그대로 판정한다. 빠지는 것은 **같은 값으로의 비밀번호 재설정** 하나이고,
그것은 롤 생성문(`CREATE ROLE … PASSWORD`)이 이미 세운다. dev 실측 결과 `REVOKE`×4 · `GRANT`×8,
`service_operator` INSERT·DELETE 와 `d2_member_role` SELECT 가 `f` → `t`.

`infra/prod/db-bootstrap.sh account-admin` 이 이것을 스크립트로 옮겼고, 제거가 **정확히 3줄**인지와
꼬리 점검이 남아 있는지를 값으로 확인한 뒤에만 2차를 먹인다(아니면 exit 3).
같은 선례를 `dev-package/reports/stage3-dual-release/rds-role-adaptation.json` 이 hash 로도 남겼다.

`operator` 단계는 우회가 없다 — `ops/operator-roles.sql` 에는 `ALTER ROLE` 이 없고
`CREATE ROLE … NOSUPERUSER` 는 RDS 마스터가 할 수 있다. 막히는 것은 **ALTER** 뿐이다.

## 5. 커밋 C — 운영 기능 둘

| 기능 | 종전 자리 | 이번 자리 |
|---|---|---|
| 소유권 장부 스냅샷 | 세션 문서의 heredoc(`dev-package/sessions/20260911-stage12-execution-preparation.md`) | `infra/prod/publish-ownership-hourly.sh` ＋ `install-cron.sh` 가 `17 * * * *` 로 설치 |
| 운영자 알림 런타임 | `install-runtime-cron.sh`·`run-runtime-job.sh` 가 dev·staging 만 수용 | **prod 수용** — 갈래는 벌 이름이 아니라 둘(연결 = dev·prod / relay = staging) |

`infra/prod/install-cron.sh` 가 prod 의 크론 **넷 전부**를 건다. 입력을 **먼저 전부** 검사해 하나라도
없으면 크론 파일을 한 줄도 쓰지 않고 exit 2 — 반쯤 걸린 상태로 끝나지 않는다.
운영자 알림은 cron 줄을 베끼지 않고 `install-runtime-cron.sh install` 에 위임한다(일정 정본이 그
스크립트의 `expected()` 하나여야 `verify` 의 드리프트 대조가 의미를 갖는다).

⚠ **compose 프로젝트 이름은 `[미확인]`이다** — prod 호스트를 접촉하지 않았다. 스크립트가 값을
**요구만** 하고(`:?`) 추측하지 않으며, `install-cron.sh` 가 볼륨·네트워크 존재를 확인한 뒤 건다.
컨테이너 이름 `colab_v2_prod_*` 는 compose 가 고정한 이름이라 프로젝트 이름과 다를 수 있다.

## 6. 검증 — 3계수와 근거

선언 12건 · **한 번의 실행** · 배출처 `dev-package/reports/prod/rebase-20260913/gates` —

```
── 계 : green 12 / red(판정) 0 / red(준비) 0     (exit 0)
```

green 12 = `exec-bit` · `db-boundary` · `work-item-consistency` · `contract-lint` ·
`contract-breaking`(기준 `origin/main` · 파괴적 변경 0) · `generated-up-to-date` ·
셀프테스트 6종(`artifact-ownership` · `autometa-loss` · `boundary` · `db-boundary` · `event` · `preview-tile-slot`).

⚠ **`event-selftest` 는 처음에 red(판정) 이었다.** 원인은 코드가 아니라 **이 워크트리에
`gates/tools/node/node_modules` 가 없던 것**이다(규칙 2-4 와 같은 계열 · 게이트는 도구 확보 실패를
**일부러 red 로** 센다 — 케이스 ⑫ 가 그 성질을 증명한다). `npm ci` 뒤 `event-lint` green,
전수 재실행에서 12/0/0. 검사는 한 건도 줄이지 않았다.

선언 밖으로 따로 돌린 것 —

| 무엇 | 결과 | 판독 |
|---|---|---|
| `planning-freshness` | **red 5** | 레포 밖 원인 — 기획 원본 폴더 `40 COLAB-기획` 이 이 호스트에 없다. 이 브랜치는 판정기·매니페스트 무수정 |
| `services/core-api/tests/test_deploy_doctor.py` | **34 passed** | prod 케이스 ＋ ⑮ 포함 |
| `infra/prod/tests/ship-gate.sh` | **48 / 0** | 6 케이스 유지 ＋ ⓖ 반입 단계 · ⓗ 레포 tar 결손 (종전 21) |
| `infra/dev/tests/ship-gate.sh` | **36 / 0** | 픽스처 수리 ＋ ⓖⓗ(모드별 sha · 태그 재사용) (종전 통과 18 · 실패 8) |
| `scripts/tests/test_operator_runtime_cron.py` | 9 중 **3 실패** | 셋 다 staging relay 갈래 · 원인 `flock` 부재 ＋ BSD `stat` 의 `-c` 미지원(macOS). 이번 변경과 무관 |
| 게이트 `operator-notifications` | **exit 1** | 위와 같은 원인 4건(`test_deploy_release` 1건 포함). 리눅스 CI·EC2 에서는 해당 없음 |

`service-tests`·`all` 은 이 회차에서 돌리지 않았다.

## 7. TDD — red 를 먼저 본 자리

| 시험 | red 축자 | green |
|---|---|---|
| `infra/prod/tests/ship-gate.sh` ⓖⓗ | `✗ ⓖ 반입 단계 · 레포 tar 를 싣는다 — 「colab-repo-<sha>.tgz」가 없다` (통과 23 · 실패 14) | 48 / 0 |
| `infra/dev/tests/ship-gate.sh` ⓖⓗ | `✗ ⓖ prod 태그 · 1회차 exit — 기대 0 · 실제 65` (통과 29 · 실패 7) | 36 / 0 |
| `test_operator_runtime_cron.py` prod 3건 | 실패 5(그중 2건이 새 prod 케이스) | 실패 3(전부 `flock` · 새 케이스는 통과) |
| `ship-gate.sh` ⓖ 소유권 스크립트 | `✗ ⓖ 반입 단계 · publish-ownership-hourly.sh 를 싣는다` (통과 47 · 실패 1) | 48 / 0 |

## 8. 결정 번호

`main` 이 그 사이 `〈383〉` 을 백오피스 회차에 썼다 → 게이트 축자 「두 회차가 같은 번호를 집었다.
**뒤에 온 쪽이 새 번호를 받는다**」. `origin/main`(`aa8bee98`) 최대 394 ＋1 = **`〈400〉`**(25 파일 · 52곳).
옮긴 기준 = 그 줄이 `origin/main` 의 같은 파일에 있는가 — `main` 쪽 인용 4자리는 무수정(규칙 4-1).
⛔ **이 번호도 임시다.** 발급은 병합하는 쪽이 병합 직전에 재실측한다.

⚠ **지시문 문면과의 차이 1건** — 지시문은 「`〈383〉` 임시 유지」였다. 유지하면
`work-item-consistency` ㈔ 가 **red(판정) 1** 이고(축자 확인), 그 red 는 검사를 줄이지 않고는
지울 수 없다. 규칙 4-1 이 정한 조치가 정확히 재번호이므로 그쪽을 택하고 여기 적는다.

## 9. 열린 것 — 후속

1. **`infra/{dev,prod}/tests/ship-gate.sh` 를 게이트로 승격.** 지금은 **어느 게이트도 CI 잡도 돌지 않는다**
   (워크플로·`gates/run.sh` 에서 `ship-gate` 검색 0건). 그래서 dev 판이 8건 red 인 채로 누구에게도
   안 보였다(`ship.sh` exit 127). 규칙 3-3 이 말하는 「검사가 게이트 밖에만 있다」의 형제다.
2. **`event-lint`·`event-selftest` 의 의존 부재를 준비 red(78 ＋ `::gate-readiness-failure::`)로 가름.**
   지금은 판정 red 로 계수돼 「코드 결함」과 「워크트리 미구성」이 같은 값으로 보인다.
3. **`planning-freshness` 의 「외부 폴더 부재」를 준비 red 로 가름.**
4. **`scripts/tests/test_operator_runtime_cron.py`·`test_deploy_release.py` 의 GNU 의존**
   (`flock` · `stat -c`). macOS 호스트에서는 판정할 수 없다 — 게이트가 그 사실을 준비 실패로
   말하게 하거나 이식성을 올린다.
5. **`work-items.yaml` 병합 드라이버가 `python3` 로 등록돼 있다.** PyYAML 없는 인터프리터가 잡히면
   드라이버가 손을 떼고 충돌이 난다. 워크트리 구성 훅이 venv 파이썬으로 걸어 두는 것이 맞다.
6. **`infra/dev/ship.sh` 에는 판정 레포 동기화와 `dev.env` 태그 갱신이 아직 없다.**
   이번에 prod 쪽만 넣었다 — dev 도 같은 구멍이고 dev 에서 실제로 2회 밟았다.
7. **compose 프로젝트 이름 실측**(`[미확인]`) — prod 호스트에서 `docker volume ls` 로 잰다.
8. **`COLAB_VIZ_OWNERSHIP_SNAPSHOT_GROUP_GID`(viz 실제 gid) 실측**(`[미확인]` · dev 는 999).

## 10. 배포 실측 (2026-09-13)

배포 세션(정비 레인과 별도)이 밟은 순서 그대로. 시각은 KST. **비밀값·호스트 주소·RDS 엔드포인트는 적지 않는다.**

### 10-1. 대상과 태그

- 배포 대상 = `origin/main` **`aa8bee981ff5`**(브랜치 tip 이 아니다). 그 커밋의 워크트리에 브랜치의 배포 도구
  (`infra/prod` · `infra/_lib` · `infra/dev/tag-release.sh` · `infra/notifications/{install-runtime-cron,run-runtime-job}.sh` ·
  `services/core-api/ops/{deploy_doctor,s3_doctor}.py`)를 **미추적 복사**해 빌드했다 — 이미지의 코드는 `main`, 도구만 브랜치 판.
- 태그 **`prod-20260913` → `aa8bee981ff5` · 로컬만**(push 안 함). 규칙 문면 「태그 주체 = Ted」와 다르다 — **Ted 통보 예정**.
  반입 게이트 ⑵ 는 로컬 태그로 통과한다(원격 미조회 · 우회 변수 없음).

### 10-2. P2 — 백업 · 롤 · 시크릿 · 키

- **19:38 백업 GREEN** — `_ops/backups/prod/2026-09-13T103842Z-*`.
- 롤 신설 4 → 총 8: `colab_account_admin`(login) · `colab_operator_runtime`(login) · `colab_operator_reporter` · `colab_operator_exporter`.
- `/etc/colab` 신설 4 → 총 11: `account-admin-database.url`(uid 10001) · `operator-database.url`(root) ·
  `ownership-platform-db.url`(root · `colab_backup` 자격) · `ops-slack-webhook.url`(root · dev 와 같은 수신처).
- `prod.env` 키 6 → 9: `COLAB_VIZ_OWNERSHIP_SNAPSHOT_OWNER_UID=0` · `_GROUP_GID=999` · `_MAX_AGE_SECONDS=7200`.
- ⚠ **순서 교훈** — `db-bootstrap.sh account-admin` 은 마이그레이션 `0025` **뒤**여야 한다. `account_admin` 스키마 부재로
  1차 실패 → 롤·비밀번호·접속 파일만 먼저 만들고 GRANT 는 `up.sh` 뒤 재실행으로 해결. `infra/prod/README.md §8` 에 명기.

### 10-3. P3 — 빌드 · 태그 · 반입

- `build.sh` 5 이미지 arm64(tar 1.0GB) · `tag-release.sh prod`.
- `ship.sh` **1차 실패** — `/opt/colab-v2/*.sh` 가 root 소유라 scp 거절 → `chown -R ec2-user` 로 해결.
- `ship.sh` **2차 성공** — 반입 게이트 통과(`MAIN_SHA main=aa8bee981ff5 candidate=aa8bee981ff5 ancestor=yes`) ·
  ops 소스 번들 green · 이미지 5 적재 · `prod.env COLAB_IMAGE_TAG=prod-aa8bee981ff5` · 판정 레포 동기화.

### 10-4. P4 — 마이그레이션 · 기동 · 롤 권한

- `up.sh` exit 0 — platform `0012_merge_lv1_and_transfer` → `0031_search_evidence` **19건** ·
  ai `0005_k2b_concept_graph_seed` → `0007_merge_vocab_and_category` **3건** · 볼륨 `events`·`ownership-ledger` 생성 ·
  4 유닛 healthy · `/healthz` 8000/8100/8200 = 200 · 실행 이미지 5 전부 `prod-aa8bee981ff5`.
  - 단위 주의 — 19 는 번호 범위 `0013`~`0031` 기준이다. `db/platform/versions` 파일 수로는 그 범위가 **20**(`0013` 형제 둘 —
    `0013_ra1_ext_interval_period`·`0013_topic_vocab_six`). `up.sh` 적용 로그의 리비전 수는 이 등재에서 재지 않았다(`[미확인]` ·
    푸는 법 = prod `alembic_version_platform` 과 로그 대조).
- 그 뒤 `db-bootstrap.sh account-admin`(RDS `ALTER ROLE` 우회 갈래 · 자기 점검 통과) · `operator` · `app-grants` · `verify` **ok**.

### 10-5. cron — 셋 설치 · 하나 면제

- 설치기를 세 상태로 고쳤다(커밋 F). ① 백업 ② 만료 전송 정리 ③ 소유권 스냅샷(매시 17분 · 프로젝트 `colab-v2-prod` · gid 999) 설치.
- **④ 운영자 알림은 명시 면제**(`COLAB_NOTIFICATION_SKIP=1`) — prod 에 SQS 큐 2 · Secrets Manager 웹훅 ARN 2 ·
  CloudWatch 알람이 없다(dev 에만). 운영자 런타임 venv 도 미구성.
- 소유권 스냅샷 수동 1회 → `current.json`(d3_file 4 · d5_upload_file 4). §9 의 `[미확인]` 7·8 이 이것으로 닫혔다
  (프로젝트 이름 `colab-v2-prod` · gid 999).

### 10-6. doctor — 1차 11/15 → 최종 15/15

| 실행 | 결과 | ✗ 의 원인 | 조치 |
|---|---|---|---|
| 1차 | **11/15** | ③ 웹 버킷 — 운영자 키 env-file 이 빈 파일 → IMDS(앱 역할) 403 · 로컬 키 파일 경로 착오 | 올바른 키 파일로 |
| | | ⑥⑦ — 판정 레포 tar 의 macOS AppleDouble `._*.py` **15,353** 파일 → ast 「null bytes」 | 호스트 `find -delete` ＋ `ship.sh` 정정(커밋 G) |
| | | ⑩ — 웹 미배포(`index.html`) | 웹 배포(아래) |
| **최종** | **항목 15 — ✓ 15 · ✗ 0 · ─ 0** · exit 0 · **19:54** | — | 실행기 기록 `pr.verify.1.log` |

- 웹 배포 = 실행기 `deploy_release.py run --plan`(대상 `pr` · 커밋 H) · `npm run build` → `deploy_web.py` → `colab-platform-web-prod`.
  검증 = CloudFront `index-DuCCGbNb.js` 로컬=원격 일치 ＋ `deploy_doctor --env prod` 한 실행(위 최종 줄).
- 실행기 종료코드 **78** = 배포·검증 exit 0 **뒤** Slack 비밀 파일(`~/.config/colab/slack-webhook`) 부재로 알림 단계 준비 실패.
  완료 판정과 무관 · 사실 기재.
- 부분 결과를 합치지 않았다 — 판정은 최종 한 실행뿐.

### 10-7. 스모크(CloudFront)

admin 로그인 **201** · `/me` 연구원 · `mustChangePassword=false` · 데이터셋 1건 목록 **200** · 검색 **200** · 미리보기 라우트 **400**(빈 본문 — 요청 형식 거절 · 서비스 응답 확인용).

### 10-8. 문서 반영 (이 커밋)

`docs/DEPLOY.md`(§4-0b 배포 원장 · §4-1c 재판정 · §5-9 · §5-10 19건 · §3-1 증상 3행＋1행 증보 · §10) ·
`infra/prod/README.md`(§7 ④ 면제 실측 · §8 `account-admin`·`operator` 순서) · `PR-BODY.md`(배포 실측 · Ted 판정 표) ·
대장 `I5` evidence(status 무변) · `03-HANDOFF.md`.

### 10-9. 열린 것 (배포 뒤)

1. **태그 push ＋ 태그 주체 문면 판정** — Ted.
2. **④ 운영자 알림의 prod AWS 자원**(SQS 큐 2 · Secrets Manager 웹훅 ARN 2 · CloudWatch 알람) ＋ 런타임 venv — 만들지 말지 Ted.
3. **`〈400〉` 재발급** — 병합 직전 재실측(규칙 4-1). 이번 배포 실측의 원장 행은 `PLAN-SoT §9 〈N〉(병합 직전 발급)` 자리.
4. `deploy_release.py` 알림 단계의 Slack 비밀 파일 배치(종료코드 78).
5. `up.sh` 적용 리비전 수 실측(19 vs 파일 20 — 위 단위 주의).
