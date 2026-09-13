# DR-2 — `main` 병합 뒤 연속 실행 창 명령 런북 (배포 → 초기화 → 재적용 → SQL 선행 → 확인)

- 작성 2026-09-13 · 역할 `researcher` · 성격 = **미승인 초안 · 레포 읽기 전용으로 작성.** 이 문서 작성 중 dev·AWS 접촉 0.
- 적용 범위 = `DR-1a`·`DR-1b`·`DR-1c` 가 `main` 에 ff-only 로 올라간 **직후 한 번의 연속 창**.
- 근거 = 라운드 `dev-package/prd/rounds/R-DEV-RESET.md §5 WU-R2` · 정찰 `dev-package/reports/r-dev-reset/dev-access-recon.md` ·
  선행 실측 `dev-package/sessions/DR-2-tree-sync-2026-09-13.md` · 실행기 `infra/releases/README.md` · 도구 머리말 `services/core-api/ops/reset_dev_environment.py`.
- 비밀 취급 = 접속 문자열·키·비밀번호를 이 문서·argv·로그·원장에 싣지 않는다. **환경변수 이름과 파일 경로만** 적는다.
- 호스트 경로(`/opt/colab-v2`·`/opt/colab-repo`·`/etc/colab`)는 EC2 위 운영 식별자다. 레포 경로는 전부 루트 기준 상대경로다.

---

## 0. 전제 확인 (셋을 모두 확인한 뒤 1절로 간다)

| # | 전제 | 확인 자리 | 기대 |
|---|---|---|---|
| ㄱ | `main` tip = `<MAIN_SHA>` (값을 이 문서에 박지 않는다) | 개발 기계 `git fetch origin && git rev-parse origin/main` | 병합 커밋 sha 와 일치 |
| ㄴ | 다른 작업 사본의 배포·컨테이너가 멈춰 있다 | 다른 clone 의 `<git-common-dir>/deploy-releases/*/state.json` 이 진행 중 아님 ＋ EC2 `docker ps` 에 `colab-ops-*` 임시 컨테이너 0 | 실행 주체 1 |
| ㄷ | `deploy_doctor` 기준선 15/15 (2026-09-13 실측 · 실행 sha `6ff0eecd2cba`) | `dev-package/sessions/DR-2-tree-sync-2026-09-13.md §4` 축자 「`항목 15 — ✓ 15 · ✗ 0 · ─ 0`」 | 재배포 뒤 **다시 잰다**(같은 문서 §5) |

- ㄴ 의 근거 = `deploy_release.py` 잠금이 **작업 사본의 git common directory** 에 있어 다른 clone 의 배포를 막지 않는다(`dev-package/reports/r-login-backoffice/task5/deploy-3.md §8-1`). 3차 배포가 이것으로 중단됐다.
- ㄷ 의 기준선은 **직전 sha 의 값**이다. 이번 배포로 실행 sha 가 바뀌므로 1-4 의 재측정이 판정값이다.
- `[미확인 · 실행 시 확인]` `/opt/colab-v2/dev.env` 소유자 — 배포마다 `root:root` 로 표류한다(`deploy-3.md §8-2`). `sudo` 전제로 읽는다.

---

## 1. 배포 — 공통 실행기 1회 → 트리 동기화 → doctor 1회

### 1-1. release 계획 JSON (sha 자리만 비운다)

- 자리 = `dist/release-dr2-<MAIN_SHA>/release.json`(`.gitignore` · 레포에 커밋하지 않는다). 계획에 비밀값 0.
- 필수 필드 = `schema`(`colab-deploy/1` 고정) · `id`(`[A-Za-z0-9._-]{1,120}`) · `targets`(1~2건 · 각 `name`·`version`·`deploy`·`verify` 는 argv 배열의 배열) · `inputs`(선택 · `path` ＋ 64자리 hex `sha256`). 근거 `scripts/deploy_release.py:76-101`.
- `deploy`·`verify` 는 **셸 문자열이 아니다** — `~`·`$변수`·`&&` 가 해석되지 않는다(`infra/releases/README.md`).

```json
{
  "schema": "colab-deploy/1",
  "id": "dr2-dev-<MAIN_SHA>",
  "summary": "dev 초기화 도구와 규칙 예외를 반영했습니다.",
  "inputs": [],
  "targets": [
    {
      "name": "dv",
      "version": "<MAIN_SHA>",
      "deploy": [
        ["bash", "<계획 폴더>/01-build.sh"],
        ["bash", "<계획 폴더>/02-ship.sh"],
        ["bash", "<계획 폴더>/03-image-tag.sh"],
        ["bash", "<계획 폴더>/04-backup.sh"],
        ["bash", "<계획 폴더>/05-up.sh"],
        ["bash", "<계획 폴더>/06-repo-tree.sh"],
        ["bash", "<계획 폴더>/07-web.sh"]
      ],
      "verify": [
        ["bash", "<계획 폴더>/v0-doctor.sh"],
        ["bash", "<계획 폴더>/v1-public-hash.sh"]
      ]
    }
  ]
}
```

- 단계 스크립트의 내용물 정본 = `infra/dev/README.md:59-72` — `infra/dev/build.sh` → `infra/dev/ship.sh`(환경변수 `COLAB_DEV_SSH`·`COLAB_DEV_KEY_FILE`) → EC2 `/opt/colab-v2/up.sh` → 프런트 `ops/deploy_web.py`(실행기 자식 단계에서만 쓰기 허용).
- 단계 이름·건수는 3차 배포 실측 표를 따랐다(`deploy-3.md §2`). `[미확인 · 실행 시 확인]` 각 단계 스크립트의 본문은 회차마다 새로 작성한다 — 레포에 고정본이 없다.

### 1-2. 실행 명령 (개발 기계 · 레포 루트에서)

```bash
python3 scripts/deploy_release.py run --plan <계획 폴더>/release.json --check
python3 scripts/deploy_release.py run --plan <계획 폴더>/release.json
python3 scripts/deploy_release.py status dr2-dev-<MAIN_SHA>
```

- `--check` = 구조·고정 입력 hash 만 본다. 배포·검증·Slack 미실행.
- 종료코드(`infra/releases/README.md`) — `0` 배포·검증·알림 성공 · `1` 배포/검증 실패 · `20` 배포·검증 성공 ＋ 알림 실패 · `75` 다른 배포 실행 중 · `78` 계획·입력·상태 확인 불가.
- **`1`·`75`·`78` 이면 그 자리에서 멈춘다.** 같은 id 로 무조건 재배포하지 않는다(같은 문서).
- 반입 게이트 = `infra/dev/ship.sh:20-33` — 비조상 **exit 65** · `origin` 조회 실패 **exit 78**. 우회 선언(`COLAB_SHIP_ALLOW_NONMAIN=1`)을 쓰지 않는다.
- `20` 은 배포 실패 표식이 아니다 — 알림만 `--retry-notification` 으로 재시도한다.

### 1-3. 배포 레포 트리 동기화 (새 `main` 기준 · 3줄)

- 이유 = `ship.sh` 가 `/opt/colab-repo` 를 같은 회차에 밀지 않아 `deploy_doctor` ⑥ 이 옛 head 를 정답으로 삼는다(`dev-access-recon.md §6-1`).
- 이 창에서는 **초기화 도구 파일을 EC2 로 올리는 경로이기도 하다** — `services/core-api/ops/reset_dev_environment.py` 가 이 tar 에 실려 `/opt/colab-repo/services/core-api/ops/` 에 놓인다(정찰 §3 실측 = 원격 부재).

```bash
git archive origin/main -- db gates services/core-api/ops infra | gzip > <로컬 tgz>
scp -q -o BatchMode=yes -i "$COLAB_DEV_KEY_FILE" <로컬 tgz> "$COLAB_DEV_SSH":/tmp/repo.tgz
ssh -o BatchMode=yes -i "$COLAB_DEV_KEY_FILE" "$COLAB_DEV_SSH" 'sudo tar xzf /tmp/repo.tgz -C /opt/colab-repo --overwrite'
```

- 선례 = `dev-package/sessions/DR-2-tree-sync-2026-09-13.md §2`(전 명령 exit 0 · 체크아웃 0 · 작업 트리 미사용).
- `--overwrite` 와 `sudo` 가 둘 다 필요하다 — 기존 파일 일부가 root 소유다(`infra/dev/README.md` 앵커 「⟨선행 단계 · `〈361〉`-㉯⟩」).
- 판정 = 개발 기계와 EC2 의 `services/core-api/ops/deploy_doctor.py` md5 일치 ＋ `/opt/colab-repo/db/platform/versions` 최신이 `0031_search_evidence.py` ＋ `reset_dev_environment.py` 존재.

### 1-4. `deploy_doctor` 1회

```bash
ssh -o BatchMode=yes -i "$COLAB_DEV_KEY_FILE" "$COLAB_DEV_SSH" 'sudo bash /opt/colab-repo/infra/ops/probes/deploy-verification.sh'
```

- 기대 = exit 0 ＋ 요약줄 **`항목 15 — ✓ 15 · ✗ 0 · ─ 0`**. `--allow-skip` 미사용 · 재시도 0 · 부분 실행 합산 0.
- ⑮ 실행 sha 가 `<MAIN_SHA>` 이고 `/opt/colab-v2/MAIN_SHA` 가 `ancestor=yes` 여야 한다.
- 이 프로브는 `/opt/colab-v2/CURRENT_SHA` 를 읽어 `colab-v2/core-api:dev-<sha>` 이미지 안에서 `ops/deploy_doctor.py --env dev` 를 돌린다(`infra/ops/probes/deploy-verification.sh:7-21`).
- **15/15 가 아니면 그 자리에서 멈춘다** — 2절 이하를 시작하지 않는다.

---

## 2. Go/no-go 체크리스트 (advisor 게이트 ③ 입력)

| # | 항목 | 값 · 자리 | 판정 |
|---|---|---|---|
| 1 | 실행 전 계수 보고서 존재 | 3절 ①(`count`)의 `--report` JSON 이 실제로 서 있고 `db.platform.rows` ＋ `s3.objects` 가 들어 있다 | 없으면 no-go |
| 2 | 버킷 식별자 | `COLAB_CORE_S3_BUCKET` = `colab-platform-data-dev` 정확 일치(도구 상수 `EXPECTED_BUCKET`) | 불일치면 도구가 거부(exit 2) |
| 3 | 호스트 식별자 | 두 DB URL 의 **호스트**에 `-dev` 포함(도구 상수 `ENV_HOST_MARK`) · URL 은 `/etc/colab/platform-owner-db.url`·`/etc/colab/ai-owner-db.url` 파일로만 전달 | DB 이름 단독은 판별력 0 |
| 4 | Ted GO 기록 | `dev-package/PLAN-SoT.md §9 〈396〉`-㉲ 축자 「**순차적으로 다 이어서해 3의 초기화도 진행하고**」(2026-09-13) | 기록 있음 |
| 5 | 승인 1회 소진 | 같은 행 축자 「승인은 1회 소진이다」 ＋ 「`DR-2` 를 두 번 돌리려면 새 GO 와 새 §9 행이 필요하다」 | 이 창에서만 유효 |
| 6 | 선행 완료 | 같은 행 ⛔ 축자 「`DR-1a`·`DR-1b` 의 `main` 병합 ＋ dev 배포가 끝나기 전에는 실행하지 않는다」 | 1절 green 이 조건 |
| 7 | 백업 정책 | 사전 백업 없음(`〈396〉`-㉯⑵ · 전량 검증용 임시 데이터) · `_ops/` 무접촉 | 도구가 `_ops/` 키 1건에도 전체 거부 |

- 비가역이다. 되돌리는 수단은 없고 S3 버저닝의 이전 판 30일 보존이 전부다(`dev-package/S3.md`).

---

## 3. 초기화 — EC2 위 단계별 명령 (각 단계 「실패 시 멈춤 · 재시도 금지」)

- 공통 형태 = core-api 이미지 안에서 실행. 선례 축자 `dev-access-recon.md §3`(`docker run --rm --network host --user 0` ＋ URL 파일 읽기 전용 마운트).
- 도구 파일 = `/opt/colab-repo/services/core-api/ops/reset_dev_environment.py`(1-3 에서 올라온 것). 보고서·계획 자리 = `/tmp/out`(도구가 실행자 소유 0600 으로 쓴다 · `_write_private_json`).
- 이미지 태그 = `colab-v2/core-api:dev-<MAIN_SHA>`.
- 도구 종료코드 — `0` 정상 · `2` 인자·환경·계획 가드 거부 · `3` DB 실물이 기대와 다름 · `4` 실행 중 부분 실패(`reset_dev_environment.py:133-135`).
- AWS 자격증명 — 해석 순서는 **환경변수 → ECS → EC2 IMDSv2**(`services/core-api/src/colab_core/kernel/aws_credentials.py:62`). 환경변수 갈래를 쓰면 이름은 `AWS_ACCESS_KEY_ID`·`AWS_SECRET_ACCESS_KEY`(임시 자격이면 `AWS_SESSION_TOKEN`) ＋ `COLAB_CORE_S3_BUCKET`·`COLAB_CORE_S3_REGION`. **값은 표준입력·0600 파일로만 심고 argv·로그에 싣지 않는다.**
  ⭑ ⟨해소 2026-09-13 · 코드 실측⟩ **자격 = `colab_core.kernel.aws_credentials.load_credentials` 가 env → ECS → EC2 IMDSv2 순으로 조회한다**(모듈 머리말 축자 「AWS 자격증명 공급자 — 환경변수 → ECS → EC2 IMDSv2 순서.」 · 상수 `_IMDS_BASE` = `http://169.254.169.254`).
  → **`--network host` 컨테이너는 키 주입 없이 인스턴스 프로파일로 `count`·`s3-plan`·`s3-apply` 를 수행한다.** 호스트 네임스페이스라 링크로컬 주소에 그대로 닿는다.
  → 라운드 §5 WU-R2 1. 의 「AWS 자격증명 환경변수를 넘겨야 한다」 문면은 **불요**다(정정). `infra/dev/up.sh` 의 「AWS 키는 어디에도 없다 — 인스턴스 프로파일」쪽이 맞다.
  → 환경변수 갈래는 **대체 경로로만** 남긴다 — IMDSv2 가 막힌 경우에만 쓰고, 그때도 값은 표준입력·0600 파일로 심고 argv·로그에 싣지 않는다. `COLAB_CORE_S3_BUCKET`·`COLAB_CORE_S3_REGION` 둘은 자격이 아니라 대상 식별자라 **어느 갈래에서도 필요하다**.

### ① `count` — 실행 전 계수

```bash
docker run --rm --network host --user 0 \
  -v /etc/colab/platform-owner-db.url:/s/platform.url:ro \
  -v /etc/colab/ai-owner-db.url:/s/ai.url:ro \
  -v /opt/colab-repo/services/core-api/ops/reset_dev_environment.py:/tmp/reset.py:ro \
  -v /tmp/out:/out \
  -e COLAB_CORE_S3_BUCKET -e COLAB_CORE_S3_REGION \
  colab-v2/core-api:dev-<MAIN_SHA> python /tmp/reset.py \
    --target dev --yes-reset-dev --phase count \
    --platform-url-file /s/platform.url --ai-url-file /s/ai.url --report /out/count-before.json
```

- 기대 출력 = `── 계수 (연구실 경계를 건 상태에서 센 값)` ＋ 체인별 스키마 ＋ `S3 uploads/`·`previews/` 객체 수 ＋ `S3 진행 중 멀티파트 N` ＋ `── 보고서: /out/count-before.json` · exit 0.
- 계수는 `d1_lab` 전 행을 돌며 `set_config('app.current_lab', …)` 를 걸고 센다(`_row_counts`) — 경계 없는 `count(*)` 는 조용히 0 이다. 대상 표 = `d3_dataset`·`d3_file`·`d6_project`·`d4_lineage_edge`.
- **보고서 파일 존재를 확인한 뒤 다음 명령을 낸다**(라운드 §5 WU-R2 1′). 없으면 멈춘다. **실패 시 멈춤 · 재시도 금지.**

### ② `schema` — 두 체인 스키마 재생성

- ① 과 같은 마운트에서 `--phase count` 를 `--phase schema` 로, `--report` 를 `/out/schema.json` 으로 바꾼다. S3 를 부르지 않으므로 AWS 자격이 필요 없다.
- 기대 출력 = `── 두 체인 스키마 재생성 COMMIT.` ＋ `── 다음은 이 도구가 하지 않는다. 사람이 이 순서로 낸다` 목록 4줄 ＋ `⚠ 각 명령이 비영 종료하면 그 자리에서 멈춘다 — 다음 명령을 내지 않는다.` · exit 0.
- 선조건 = platform 의 비시스템 스키마가 정확히 `{public, account_admin}` · ai 가 `{public}`. 어긋나면 exit 3 이고 아무것도 지우지 않는다.
- 재생성 DDL 은 `COMMENT ON SCHEMA public IS 'standard public schema'` 까지 낸다 — 없으면 `schema-diff` 가 red 다(도구 주석 실측).
- **실패 시 멈춤 · 재시도 금지.**

### ③ `db-bootstrap.sh extensions`

```bash
sudo COLAB_PG_MASTER_URL_FILE=/etc/colab/master.url bash /opt/colab-repo/infra/dev/db-bootstrap.sh extensions
```

- 동작 = `colab_platform`·`colab_ai` 각각에 `CREATE EXTENSION IF NOT EXISTS pg_trgm`(`infra/dev/db-bootstrap.sh:72-78`). 멱등.
- 기대 출력 = `extensions: ok` · exit 0.
- `extensions` 는 **dev 래퍼 자체에 있다**(staging 으로 위임하지 않는다). `roles`·`app-grants`·`account-admin`·`verify` 는 `exec bash $STAGING "$STEP"` 로 `infra/staging/db-bootstrap.sh` 에 넘어가고 그쪽에 세 단계가 실재한다(staging `app-grants:72` · `account-admin:107` · `verify:118`).
- **실패 시 멈춤 · 재시도 금지.**

### ④ 마이그레이션 — `up.sh` 의 ① 단계만

```bash
sudo docker compose -f /opt/colab-v2/compose.yml --env-file /opt/colab-v2/dev.env --profile migrate run --rm -T migrate-platform < /dev/null
sudo docker compose -f /opt/colab-v2/compose.yml --env-file /opt/colab-v2/dev.env --profile migrate run --rm -T migrate-ai < /dev/null
```

- 원본 = `infra/dev/up.sh:14-16`(`dc --profile migrate run --rm migrate-platform` ＋ `migrate-ai`). 여기서는 **기동·healthy 대기(②③④)를 돌리지 않는다** — 컨테이너는 이미 떠 있다.
- `-T … < /dev/null` 은 2차 배포 실측 교정이다 — heredoc 안에서 `docker compose run` 이 남은 스크립트를 stdin 으로 삼켜 `migrate-ai` 가 누락됐는데 종료코드는 0 이었다(`deploy-2.md:56`).
- 기대 = 두 명령 각각 exit 0. 판정값은 살아 있는 DB 의 head = platform `0031_search_evidence` · ai `0007_merge_vocab_and_category`.
- **실패 시 멈춤 · 재시도 금지.**

### ⑤ `db-bootstrap.sh app-grants` ＋ `account-admin`

```bash
sudo COLAB_PG_MASTER_URL_FILE=/etc/colab/master.url bash /opt/colab-repo/infra/dev/db-bootstrap.sh app-grants
sudo COLAB_PG_MASTER_URL_FILE=/etc/colab/master.url bash /opt/colab-repo/infra/dev/db-bootstrap.sh account-admin
```

- 재실행이 **필수**다 — 기본 권한이 `pg_default_acl.defaclnamespace` 로 스키마에 매달려 있어 스키마와 함께 사라진다(라운드 §5 WU-R1a ⑷ · `services/core-api/ops/app-role.sql` 의 `ALTER DEFAULT PRIVILEGES … IN SCHEMA public`).
- `[미확인 · 실행 시 확인]` 두 단계의 축자 성공 출력 — staging 스크립트로 위임되며 이 문서 작성 시점에 실행 로그를 재지 않았다.
- `[미확인 · 실행 시 확인]` staging 갈래가 요구하는 추가 환경변수(앱 롤 비밀번호 계열) — `bash /opt/colab-repo/infra/staging/db-bootstrap.sh required-env` 로 먼저 이름만 확인한다.
- **실패 시 멈춤 · 재시도 금지.**

### ⑥ `s3-plan` — 삭제 계획 생성

- ① 의 마운트에 `--phase s3-plan --plan-out /out/plan.json --report /out/s3-plan.json` 을 준다.
- 기대 출력 = `── 계획 /out/plan.json — 키 N 건 · 진행 중 멀티파트 M 건` ＋ `sha256 <64자리>` ＋ `적용은 \`--phase s3-apply --apply-plan <위 파일> --plan-sha256 <위 값>\` 이다.` · exit 0.
- `--plan-out` 없이 부르면 exit 2.
- **실패 시 멈춤 · 재시도 금지.**

### ⑦ 계획 검토 (사람 · 적용 전 정지점)

- 본다 = ⓐ `keys` 건수가 ① 계수와 어긋나지 않는가 ⓑ **`_ops/` 로 시작하는 키가 0 건인가** ⓒ 접두사가 `uploads/`·`previews/` 둘뿐인가 ⓓ 계획 파일이 실행자 소유 0600 인가.
- 도구 쪽 강제 = `NEVER_TOUCH_PREFIXES = ("_ops/",)` 가 1건이라도 잡히면 전체 거부(exit 2) · 소유·모드 검사 `reset_dev_environment.py:203`.
- `_ops/` 를 지우면 `deploy_doctor` ⑭(백업 24h)가 red 다.
- **어긋나면 멈춤 · 계획을 손으로 고치지 않는다.**

### ⑧ `s3-apply` — 계획의 키만 삭제 ＋ 멀티파트 중단

- ① 의 마운트에 `--phase s3-apply --apply-plan /out/plan.json --plan-sha256 <⑥ 출력값> --report /out/s3-apply.json` 을 준다.
- 기대 출력 = `── s3-apply — 키 N 건 · 멀티파트 M 건` ＋ `실행 후 uploads/ 객체 0` · `실행 후 previews/ 객체 0` · `실행 후 진행 중 멀티파트 0` ＋ `── 보고서: /out/s3-apply.json` · exit 0.
- 부분 실패가 있으면 `⛔` 줄을 stderr 로 내고 **exit 4** 다.
- 멀티파트를 객체보다 **먼저** 중단한다 — 순서를 바꾸면 조각이 원장 없이 남는다(도구 주석 축자).
- `--plan-sha256` 불일치·계획 파일 권한 불일치는 exit 2.
- **실패 시 멈춤 · 재시도 금지.**

---

## 4. 재확인 (셋 모두 · 한 번씩)

1. `deploy_doctor` — 1-4 와 같은 한 줄. 기대 `항목 15 — ✓ 15 · ✗ 0 · ─ 0` · exit 0. **부분 실행 둘을 합쳐 15 라 하지 않는다.**
2. 실행 후 계수 — 3절 ① 과 같은 명령에 `--report /out/count-after.json`. 기대 = `d3_dataset`·`d3_file`·`d6_project`·`d4_lineage_edge` 전부 0 ＋ `uploads/`·`previews/` 객체 0 ＋ 멀티파트 0. 경계가 실린 같은 경로로 본다.
3. ⑧ RLS 전수 — `deploy_doctor` ⑧ 항목이 green(살아 있는 DB 대상). 스키마 재생성 뒤 RLS 정책은 마이그레이션이 다시 만든다(`infra/dev/db-bootstrap.sh:5` 축자 「스키마는 여기서 만들지 않는다 — alembic 체인이 정본이다.」).

- `_ops/` 객체 수 무변도 함께 기록한다(완료 정의 · 라운드 §5 WU-R2).

---

## 5. SQL 선행 4단계 (화면 밖 예외 · 이 넷뿐이다)

- 근거 = `dev-package/scenarios/dev-minimal-data-setup.md §1` · `〈396〉`-㉰. 실행 위치 = EC2. **한 단계가 비영 종료하면 그 자리에서 멈춘다.**
- `[미확인 · 실행 시 확인]` core-api 이미지 안의 `psql` 가용 여부 — 부재 시 `postgres:16-alpine` 을 같은 마운트 형태로 쓴다(선례 `infra/dev/db-bootstrap.sh:23` 의 `docker run --rm -i postgres:16-alpine psql`).
- `[미확인 · 실행 시 확인]` 접속 문자열을 psql 에 넘기는 형태 — 아래 예시는 컨테이너 **안에서** 파일을 여는 모양이고, argv 노출을 더 줄이려면 환경변수 갈래를 실행 시 정한다.

### ① 연구실 — `infra/staging/provision-lab.sql`

```bash
docker run --rm --network host --user 0 \
  -v /etc/colab/platform-owner-db.url:/s/owner.url:ro \
  -v /opt/colab-repo/infra/staging/provision-lab.sql:/s/lab.sql:ro \
  <psql 이미지> sh -c 'psql -v ON_ERROR_STOP=1 "$(cat /s/owner.url)" -f /s/lab.sql'
```

- 소유자 롤(`colab_owner` · `NOBYPASSRLS`)로 돈다. 파일이 `BEGIN;` 직후 `SET LOCAL app.current_lab = '00000000000000000000HYMETS'` 를 **스스로** 건다 — 밖에서 다시 걸지 않는다.
- 기대 = 파일 끝 계수표 5행 — `d1_account` 1 · `d1_lab` 1 · `d1_lab_profile` 1 · `d2_member_role` 1 · `d2_permission_switch` 0.
- 전 문장 `ON CONFLICT DO NOTHING` — 재실행해도 행이 늘지 않는다. 증명 `dev-package/sessions/DR-1b-provision-lab-proof.md`.
- **실패 시 멈춤.**

### ② 첫 계정 — `services/core-api/ops/provision-account.sql`

- 변수 5개(파일 머리말 축자) — `-v account_id -v lab_id -v name -v email -v role`. `lab_id` = `00000000000000000000HYMETS` · `role` = `연구원` 또는 `교수`(정본 역할은 두 층뿐 · 관리자 역할은 없다).
- 마운트 = `/opt/colab-repo/services/core-api/ops/provision-account.sql`. 소유자 롤로 돈다.
- 기대 = `d1_account` 1행 ＋ `d2_member_role` 1행 ＋ `d2_permission_switch` 4행(`업로드·편집` true · `프로젝트 생성` true · `승인 위임` false · `연구실 설정` false).
- 연구실이 없으면 스크립트가 멈춘다 — ① 이 먼저다. **실패 시 멈춤.**

### ③ 첫 로그인 자격 — `accounts.py::create_account` 트랜잭션을 컨테이너 안에서

- 이유 = 초기화 뒤 `account_admin.login_credential` 0행이라 `POST /admin/accounts` 를 쓸 수 없고(운영자 0명 · 자기 자신을 만들지 못한다), `login_credential` 을 만드는 ops SQL 이 없다. `ops/set-password.py` 는 DB 가 아니라 자격 파일에 심는다.
- 실행 자리 = 컨테이너 `colab_v2_dev_core_api` 안. 임시 실행 스크립트는 레포에 남기지 않는다(커밋 0 · 종료 시 삭제).
- 동일성 조건 6 (시나리오 §1 ③ 축자) —
  > - 해시 = `colab_core.kernel.password.hash_password` (`scrypt` · `n=16384 r=8 p=1`)
  > - 로그인 이름 정규화 = `colab_core.kernel.db_credentials.normalize_login_name`
  > - ID = `colab_core.kernel.ids.Ulid.generate()`
  > - 같은 `pg_advisory_xact_lock(1131379081)` · 같은 이메일 중복 검사 2종 · 한 트랜잭션
  > - `must_change_password`·`session_version` 은 **INSERT 에서 생략** — 제품과 같이 DB 기본값(`true` · `1`)을 받는다
  > - 접속 = 컨테이너에 마운트된 `/etc/colab/account-admin-database.url`(`colab_account_admin` 롤)
  > - 비밀번호는 **표준입력 한 줄**로만 넘겼다. argv·파일·로그에 적지 않았다.
- **초기 비밀번호는 10자 이상**으로 정한다 — 제품 하한이 10자다(`accounts.py` `initialPassword: Field(min_length=10)` · `frontend/src/auth/passwordRules.ts`). 9자로 심으면 로그인은 되지만 첫 변경 화면이 막는다.
- 전달 파일은 0600 으로 두고 확인 뒤 `shred -u`.
- 기대 = `account_admin.login_credential` 1행 · `must_change_password` = `true` · `session_version` = `1`. 확인 열 = `account_id` · `login_name` · `lab_id`/`role` · `kdf`/`n`/`r`/`p` = `scrypt`/`16384`/`8`/`1`.
- 알려진 잡음(판정 red 아님) — 사후 조회가 `permission denied for table d2_member_role` 로 죽는다(`ops/account-admin-role.sql` 이 `INSERT` 만 주고 `SELECT` 를 주지 않는다). 역할 행 확인은 소유자 롤로 대신한다.
- 상태 코드 확인 = `POST /api/v1/sessions` **201** · `GET /api/v1/me` **200** `mustChangePassword=true`. 401 이 5건 쌓이면 **429**(창 900초 · 한도 5)라 창이 지난 뒤 다시 낸다.
- **실패 시 멈춤.**

### ④ 서비스 운영자 — `services/core-api/ops/provision-service-operator.sql`

- 변수 = `-v account_id`(② 의 값). 마운트 = `/opt/colab-repo/services/core-api/ops/provision-service-operator.sql`.
- ⚠ FORCE RLS 아래라 **같은 세션에서 `app.current_lab` 을 먼저 걸지 않으면** `INSERT 0 0` 뒤 파일 7~10행의 `\gexec` 가드가 「지정한 계정이 없어 운영자를 등록하지 못했다」 예외를 낸다. 이 파일은 경계를 스스로 걸지 않는다 — ① 과 다르다.
- 기대 = `account_admin.service_operator` 1행. **실패 시 멈춤.**

---

## 6. Ted 인계

- 주소 = `https://d31zgpff2091oh.cloudfront.net`(`docs/DEPLOY.md:7`·`:142`).
- 로그인 계정 = 5절 ② 에서 만든 계정 **하나**(이름만 전달 · 이메일과 초기 비밀번호는 0600 경로로 1회 전달하고 이 문서·원장에 적지 않는다).
- Ted 가 처음 보는 화면 = 로그인 직후 **비밀번호 변경 강제** 화면. 제목 「비밀번호 변경」 · 안내 「처음 로그인하셨습니다. 사용할 새 비밀번호로 바꿔 주세요.」 · 규칙 「10~512자로 입력하세요. 영문·숫자·특수문자 조합은 필수가 아니며, 초기 비밀번호와 달라야 해요.」
- 변경 뒤 `/lab` 로 들어간다. 그 시점에 ③ 의 확인용 세션 1건은 `session_version` 이 +1 되며 무효가 된다.
- 이후 절차 = `dev-package/scenarios/dev-minimal-data-setup.md` **§2 로그인 → §4 프로젝트 4건 → §5 데이터셋 28건 → 계보 18간선 → 미리보기 5종**. 계정 추가는 기본값 「추가하지 않는다」(§3).

---

## 7. 기록 (창을 닫기 전에)

| # | 자리 | 쓰는 값 |
|---|---|---|
| 1 | `dev-package/work-items.yaml` `DR-2` | `done` ＋ 증거 경로(이 런북 · 보고서 JSON 계수 · doctor 요약줄) |
| 2 | `dev-package/03-HANDOFF.md §1` ＋ 상단 3줄 | 상태 ✅ · 최종 갱신 · 현재 단계 · 다음 WU(`DR-3`) · 5줄 이내 |
| 3 | `dev-package/PLAN-SoT.md §9 〈396〉` | 실행 결과 — 실행 sha · 삭제 계수(전/후) · `deploy_doctor` 요약줄 · 승인 1회 소진 표시 |
| 4 | 태그 | `infra/dev/tag-release.sh dev` 를 `deploy_doctor` 전건 통과 **뒤** 호출. `dev-YYYYMMDD-N` · **N = 같은 날 기존 태그 수 ＋1** · 대상 sha 는 로컬 `dist/colab-v2-dev.sha` · **push 없음 · 명령만 출력**(`docs/BRANCHING.md:41`) |
| 5 | 브랜치 정리 | `integration/r-dev-reset`·`worktree-intent-dev-reset-scenario` 로컬·원격 삭제(라운드 §8) |

- 원격 태그 push·브랜치 삭제는 **게이트 ③ 뒤 오케스트레이터**가 한다. `git push origin --tags` 금지 — 개별 push 만(`docs/BRANCHING.md:57`).
- 계수를 적을 때 **계수 기준을 함께** 적는다(어느 경로로 셌는가 · 연구실 경계를 건 상태인가).

---

## 8. 이 문서가 고치지 않는 후속 항목

1. `deploy_release.py` 배포 잠금이 작업 사본을 넘지 못한다 — 같은 호스트에 두 clone 이 동시에 배포한다(`deploy-3.md §8-1`). 걸리는 검사 없음.
2. `ship.sh` 가 `/opt/colab-repo` 트리를 같은 회차에 밀지 않는다 — `deploy_doctor` ⑥ 재발의 구조적 원인(`dev-access-recon.md §6-1`).
3. `/opt/colab-v2/dev.env` 소유자가 배포마다 `root:root` 로 표류한다(`deploy-3.md §8-2`). 걸리는 검사 없음.
4. 원격 `/tmp/repo.tgz` 잔존 — 절차 문서에 삭제 단계가 없다(`DR-2-tree-sync-2026-09-13.md §5`).
