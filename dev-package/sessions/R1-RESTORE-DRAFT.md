# WU-R-1 — 살아 있는 staging 제자리 복원 절차 (초안)

> **이 문서는 초안이고, 집행 기록이 아니다.** 여기 적힌 어떤 명령도 이 세션에서 실행하지 않았다.
> 판정·등재는 `PLAN-SoT §9` 소관이고 여기는 **절차와 그 근거**만 담는다.
>
> 세우는 이유 = **백업은 있는데 되돌리는 절차가 없다**(`STAGE2-PREP §6`). 복원 리허설은
> **일회용 인스턴스 전용**이고(`infra/staging/backup/restore-rehearsal.sh` 머리말),
> 실사고가 나면 복원 명령을 사람이 그 자리에서 조립해야 한다. `X-1`·`X-4` 재기동의 전제조건이다
> (`WORK-UNITS §10.2` · `PLAN-SoT §9 〈158〉-㉯`).

---

## 1. 지금 있는 기구 — 무엇을 하고 무엇을 안 하는가

> ⭑ **2026-08-27 갱신 — 이 절의 진단(「되쓰는 쪽이 하나도 없다」)이 이 회차에 해소됐다.**
> 아래 표는 **그 전의 상태**이고, 새로 선 것은 `§1.1` 에 따로 적는다. 진단을 지우지 않고 남긴다 —
> 무엇이 없어서 무엇을 세웠는지가 흐려지면 다음 회차가 같은 자리를 다시 판단한다.

`infra/staging/backup/` 아래 12개 파일. **전부 「뜨는 쪽」과 「일회용에 되살리는 쪽」이고,
살아 있는 대상에 되쓰는 쪽은 하나도 없다.**

| 파일 | 하는 일 | 살아 있는 staging 에 쓰는가 |
|---|---|---|
| `backup.sh` | 프로파일 루프 덤프. 임시파일 → `PIPESTATUS` → 검사 통과분만 최종본 | **읽기만**(`docker exec … pg_dump`) |
| `verify-artifact.sh` | 산출물 검사 C1~C6 — fail-closed 의 본체 | 아니오 |
| `verify-restore.sh` | 복원 **결과** 검사 — 테이블 수 · 테이블별 행 수 · 총 행 수 | 아니오 |
| `roundtrip.sh` | 씨앗 → 백업 → 파괴 → 복원 왕복(`d1_*` 일회용) | 아니오 |
| `restore-rehearsal.sh` | **실 staging 백업**을 `is3_pg_*` 일회용에 복원 · 원본과 대조 | **읽기만** |
| `selftest.sh` | fixture 11건이 전부 RED 임을 강제 | 아니오 |
| `latest-check.sh` · `run-scheduled.sh` · `schedule.crontab` · `install-schedule.sh` | 스케줄·침묵 감지 | 아니오 |
| `lib.sh` · `config.example.env` | 설정 로드 · 프로파일 조회 | — |

⚠ **`restore-rehearsal.sh` 를 살아 있는 staging 에 겨누는 개조로 이 WU 를 때우지 않는다.**
그 스크립트의 안전성이 「대상이 언제나 방금 만든 빈 일회용 인스턴스」라는 전제 위에 서 있다 —
전제를 빼면 남는 건 `gunzip | psql` 한 줄이고, 그건 절차가 아니다.

### 1.1 이 회차에 선 것 (2026-08-27) — **기구만. 실행은 0회다**

| 파일 | 하는 일 | 살아 있는 staging 에 |
|---|---|---|
| `backup/volume-lib.sh` | 볼륨 설정·합격선·오라클 조회. 원장 쪽 `lib.sh` 와 **갈라 둔다** | — |
| `backup/backup-volume.sh` | 볼륨 → 매니페스트 ＋ tar. 디스크 여유 사전점검 · 볼륨별 보존 | **읽기만**(`:ro` 마운트) |
| `backup/verify-volume-artifact.sh` | 볼륨 산출물 검사 **V1~V7**. **오라클이 본체** | 아니오 |
| `backup/backup-full.sh` | **원장 먼저 · 볼륨 나중**. 스케줄이 부르는 정문 | **읽기만** |
| `backup/selftest-volume.sh` | fixture **14건** 전건 RED 강제. **docker 불필요** | 아니오 |
| `restore/RUNBOOK.md` · `REHEARSAL.md` | 실행본 런북 · 리허설 절차 | — |
| `restore/preflight.sh` | **P1~P9** — sha256 대조 · `--skip-age` · 볼륨↔원장 짝 확인 | **읽기만** |
| `restore/expectations.sh` | **기대치를 짝 덤프에서 읽는다**(상수 0) | 아니오 |
| `restore/check-image-digests.sh` | **`reference/IMAGE-DIGESTS.md` 를 읽어** 대조 | 읽기만 |
| `restore/restore-db.sh` | §4.3 — **문 셋**을 통과해야 쓴다 | ⚠ **되쓴다** |
| `restore/restore-volume.sh` | §4.4-㈎ — 덮어쓰기(삭제 없음) ＋ 매니페스트 sha256 대조 | ⚠ **되쓴다** |
| `restore/verify-restored.sh` | §4.6 ①~⑦. **숫자가 한 개도 없다** | 읽기만 |
| `restore/rehearsal.sh` | §5 의 1·3·6 ＋ 볼륨 왕복 | **읽기만**(쓰기는 `r1_*` 일회용에만) |
| `restore/selftest-restore.sh` | fixture **10건**. docker 불필요 | 아니오 |

⚠ **`restore-db.sh`·`restore-volume.sh` 는 이 문서가 「없다」고 적었던 「되쓰는 쪽」이다.**
그래서 우회로가 아니라 **문**을 세웠다 — 손으로 붙이는 확인 인자 · 되돌림 재료 존재 · 커넥션 0(또는 컨테이너 정지).
`restore-rehearsal.sh` 를 살아 있는 대상에 겨누는 개조는 **하지 않았다**(그쪽 전제는 그대로 살아 있다).

### 산출물 — 어디에 · 어떤 이름으로

| 항목 | 값 | 근거 |
|---|---|---|
| 보관처 | 홈 아래 `colab-v2-backups/staging/` (`COLAB_BACKUP_DIR` 기본값) | `lib.sh` `load_config` |
| 이름 | `<프로파일>-<YYYYMMDDTHHMMSS>.sql.gz` ＋ 같은 이름 `.sha256` | `backup.sh` `backup_one` |
| 프로파일 | `platform`(`colab_platform`) · `ai`(`colab_ai`) | `COLAB_BACKUP_PROFILES` |
| 형식 | `pg_dump --no-owner --no-privileges` **평문 SQL** ＋ gzip | 〃 |
| 보존 | `COLAB_BACKUP_RETENTION_DAYS=14`. **프로파일별 최신 1개는 어떤 경우에도 안 지운다** | 〃 |
| 설정 실값 | 홈의 `.colab-v2-staging-backup.env`(`0600`) — 레포 밖 | `IS3 §7` |

### GREEN 이 실제로 보증하는 것 / 보증하지 않는 것

`verify-artifact.sh` 의 GREEN 은 **여섯 항목의 논리곱**이다.

| | 검사 | 보증 |
|---|---|---|
| C1 | 파일 존재 · ≥ 1024 B | 0바이트·20바이트 빈 gzip 아님 |
| C2 | `gzip -t` | 절단·손상 아님 |
| C3 | 해제 후 바이트 > 0 | 압축은 멀쩡한데 알맹이가 0 인 상태 아님 |
| C4 | `CREATE TABLE` ≥ 프로파일 합격선(platform 20 · ai 4) | 스키마 없음·중간 절단 아님 |
| C5 | 데이터 행 ≥ 합격선(platform 190 · ai 45 — **실측의 절반**) | 거의 빈 덤프 아님 |
| C6 | mtime 신선도 ≤ 1500분 | 옛 성공본이 오늘 백업으로 오독되지 않음 |

**GREEN 이 말하지 않는 것 — 이쪽이 복원 절차에 더 중요하다.**

1. **복원 가능성을 시험하지 않았다.** C1~C6 은 파일을 **읽어 센 것**이지 `psql` 에 먹여 본 것이 아니다.
   실제 적재 시험은 `restore-rehearsal.sh` 쪽이고 그건 백업과 **다른 실행**이다.
2. **행 수는 세지만 값의 정합은 안 본다.** 「행 수는 같은데 값이 뒤바뀐 덤프」는 C5 를 통과한다.
   내용 대조(md5 다이제스트)는 `restore-rehearsal.sh` 의 ④ 단계에만 있다.
3. **행 수 세기가 근사다.** `awk` 로 `COPY … FROM stdin;` 블록 안의 줄과 `INSERT INTO` 를 센다 —
   본문에 `\.` 이나 `CREATE TABLE` 로 시작하는 텍스트 값이 있으면 어긋난다.
4. **두 프로파일의 시점 일치를 보증하지 않는다.** `platform` 과 `ai` 는 **서로 다른 덤프**이고
   `backup.sh` 가 순차로 뜬다(`IS3 §8` 실측 8초 차). 원자적 스냅숏이 아니다.
5. **`sha256` 은 만들 뿐 검증 경로가 없다.** 어떤 스크립트도 복원 전에 이 값을 다시 대조하지 않는다.

---

## 2. 백업되는 것 / 안 되는 것 — 전면 복원에 필요한 목록 대조

| # | 전면 복원에 필요한 것 | 판정 | 근거 |
|---|---|---|---|
| 1 | **`colab_platform` DB** | **백업됨** | `COLAB_BACKUP_DB_platform` 프로파일. `IS3 §13` 실측 23테이블·381행 |
| 2 | **`colab_ai` DB** (온톨로지 사전 3종 ＋ 개념 그래프 2표) | **백업됨** | `ai` 프로파일. `IS3 §13` 실측 6테이블·91행 |
| 3 | **업로드 원본** (`/var/lib/colab/uploads` = named volume `colab-v2-staging_uploads`) | ⭑ **기구 생김 · 실행 0회** (2026-08-27) | `backup-volume.sh` 의 `uploads` 대상. 오라클 = `d3_file.storage_key`(저장 키가 곧 볼륨 안 상대 경로 · `contracts/storage/layout.json`) |
| 4 | **미리보기 산출물** (`/srv/viz-previews` = `colab-v2-staging_previews`) | ⭑ **기구 생김 · 실행 0회** · **오라클 없음** | ⚠ **「재생성 가능」이 지금은 실제로 거짓이다** — 원본 의존을 넘어 **재생성 수단 자체가 없다**(렌더 재실행은 stage 2 범위). 그래서 싸게 백업한다. stage 2 에서 수단이 서면 이 판단과 보존을 다시 잰다 |
| 5 | **`credentials.json`** (`COLAB_STAGING_CREDENTIALS_FILE`) | **백업 안 됨** | 홈의 `0600` 파일. 백업 대상 목록 어디에도 없다. ⚠ **`d1_account` 행과 짝이라 DB 만 되돌리면 로그인 상태가 갈린다** |
| 6 | **`subjects.json`** (`COLAB_STAGING_SUBJECTS_FILE`) | **백업 안 됨** | 〃. **그 안의 키 문자열이 곧 베어러 토큰**이다(`RESTART §2-1`) |
| 7 | **`COLAB_STAGING_*_DB_URL_FILE` 5종 파일** | **백업 안 됨** | 홈의 `0600` 파일 5개. 없으면 `:?` 로 컨테이너가 **아예 안 뜬다** |
| 8 | **env 파일** (`--env-file` 이 가리키는 홈의 `0600` 파일) | **백업 안 됨** | staging 의 모든 비밀을 쥔 파일. 백업 대상 아님 |
| 9 | **이미지 태그·digest** (`colab-v2/*:i2` 5종) | **백업 안 됨 · ✅ 기록은 생겼다** | `compose.i2.yml` 이 태그만 고정한다. **`:i2` 는 움직이는 태그**다. ⭑ **2026-08-27 — digest 대장을 세웠다: `dev-package/reference/IMAGE-DIGESTS.md`** (8 건 · `PLAN-SoT §9 〈165〉-㉱`). 이미지 자체의 백업은 여전히 없다 — **대조는 되고 복원은 재빌드다** |
| 10 | **PGDATA 자체** (`COLAB_STAGING_PGDATA_DIR` 바인드) | **백업 안 됨**(논리 덤프로 대체) | 물리 백업 없음 — PITR·WAL 아카이빙 없다 |
| 11 | **알렘빅 리비전 상태** | **백업됨**(#1·#2 안) | `alembic_version_platform` · `alembic_version_ai` 가 덤프에 포함 |
| 12 | **터널·DNS·terraform state** | ✅ **확정 — `R-1` 범위 밖** (2026-08-27 · `PLAN-SoT §9 〈165〉`) | `RESTART §1` 상 재시작에는 살아남는다. **호스트 소실 시나리오는 재지 않는다 — 그것이 이 WU 의 범위가 아니라는 것이 판정이다.** `[미확인]` 이 아니라 **안 재기로 한 것**이다. 재려면 `IS2` 의 `terraform plan` 을 빈 state 에서 재현하는 별건 WU 를 연다(`IS4` 가 부분 리허설했다) |
| 13 | **오프호스트 사본** | **없음** | `IS3 §5-4` — 백업이 원본과 **같은 WSL2 머신 1대** 위에 있다 |

**요약 (2026-08-27 갱신) — 백업 대상이 원장 둘에서 원장 둘 ＋ 볼륨 둘로 늘었다.**
남은 결손은 **5·6·7·8(비밀 7종)** 과 **9(이미지 자체)** 이고, 비밀 쪽은 **백업하지 않기로 판정된 것**이다(`§7`) —
결손이 아니라 선택이다. 이미지는 **대조는 되고 복원은 재빌드**다.
**아래 종전 요약을 이력으로 남긴다.** ~~3·5·6·7·8·9 여섯이 비어 있고, 그중 **5·6·7·8 은 없으면 기동 자체가 안 되며**,~~
**3 은 없으면 기동은 되는데 제품이 빈 껍데기가 된다**(파일 129건의 바이트가 사라진다).

⚠ **가장 조용한 결손은 #9 다.** `〈153〉` 때 배선만 바꾸고 옛 이미지로 올렸더니 **ai-service 만 healthy** 였고
사전 DB 가 `None` 으로 조용히 비었다(`STAGE2-PREP §3`). 복원 뒤 **어느 이미지로 올렸는지 대조할 기준이 없다**는 뜻이다.

---

## 3. 제자리 복원이 실제로 요구하는 것 — 제약 다섯

| # | 제약 | 어기면 |
|---|---|---|
| ㉮ | **`-f infra/staging/compose.i2.yml` 을 반드시 붙인다** | 기본값 `compose.yml`(자리표시 오리진)이 떠 **조용히 I2 이전으로 롤백**된다. 그 상태에서도 **루트 헬스는 200** 이다(`RESTART §2-②`) |
| ㉯ | **`COLAB_STAGING_*_DB_URL_FILE` 5키가 있어야 한다** | `:?` 로 `up` 이 아예 안 뜬다. 뒤 둘(`PLATFORM_OWNER`·`AI_OWNER`)은 `--profile migrate` 전용이지만 **없으면 마이그레이션이 안 돈다** |
| ㉰ | **`credentials.json`·`subjects.json` 은 읽기 전용 바인드 · inode 에 붙는다** | 새 파일 생성 후 `mv` 하면 컨테이너가 **옛 파일을 계속 읽는다.** **제자리 덮어쓰기 ＋ 재기동**이 유일한 경로. 권한 `0600` · 소유자 uid `10001` |
| ㉱ | **서비스가 커넥션을 쥔 채로는 DB 를 되돌릴 수 없다** | `DROP SCHEMA` 가 `being accessed by other users` 로 막히거나, 반쯤 적재된 상태에 앱이 쓰기를 얹는다. **먼저 비운다(drain)** |
| ㉲ | **ai-service 는 사전이 비어도 healthy 를 낸다** | `services/ai-service/src/colab_ai/app/main.py` — `settings.dict_db_url` 이 없으면 `_UnavailableDictionaries` 로 떨어지는데 `/healthz` 는 `{"status":"alive","implemented":true}` 를 그대로 낸다. **검증은 헬스가 아니라 내용으로 한다** |

⚠ ㉲ 보강 — **`_UnavailableDictionaries` 는 검색 시점에야 `RuntimeError` 를 던진다.** 기동·헬스·컨테이너 상태
어디에도 신호가 없다. **살아 있는 쪽이 속인다**(`STAGE2-PREP §3`).

⚠ 회전 음성 확인은 **네트워크 경유로** 잰다 — pg 컨테이너 안 루프백은 `pg_hba` 가 `trust` 라 엉터리 비밀번호도 통과한다.

---

## 4. 런북 — 살아 있는 staging 제자리 복원 (초안 · 미리허설)

> **표기** — 모든 경로는 레포 상대 또는 `~` 기준이다. `$ENVFILE` = 홈의 `0600` staging env 파일,
> `$BK` = `~/colab-v2-backups/staging`. 컨테이너 이름은 `compose.i2.yml` 의 `container_name` 그대로다.

### 4.0 사전조건 — 하나라도 아니면 **복원을 시작하지 않는다**

| # | 확인 | 통과 기준 |
|---|---|---|
| P1 | 도커 데몬이 산다 | `docker ps` 가 응답 |
| P2 | 되돌릴 산출물이 **둘 다** 있다 | `$BK` 에 `platform-*.sql.gz` · `ai-*.sql.gz` 각 1개 이상 |
| P3 | 산출물이 GREEN 이다 | `infra/staging/backup/verify-artifact.sh <파일> --skip-age` 가 두 프로파일 다 GREEN. ⚠ **사고 복원은 옛 파일을 쓰므로 `--skip-age` 가 맞다 — C6 를 없애는 게 아니라 이 경로에서만 뺀다** |
| P4 | 무결성이 맞다 | `.sha256` 과 대조. **지금 스크립트에 이 단계가 없다 — 런북이 처음 넣는다** |
| P5 | **두 산출물이 같은 회차다** | 이름의 `<YYYYMMDDTHHMMSS>` 가 서로 몇 분 안. 다른 회차를 섞으면 원장과 사전이 다른 세대가 된다 |
| P6 | 비밀 6종이 **제자리에 있다** | `$ENVFILE` · `credentials.json` · `subjects.json` · `*_DB_URL_FILE` 5개가 존재하고 `0600`/uid `10001` |
| P7 | **복원 직전 상태를 한 번 더 뜬다** | `infra/staging/backup/backup.sh` 1회 GREEN. ⚠ **이것이 「되돌림의 되돌림」의 유일한 재료다**(§4.7) |
| P8 | 현재 이미지 digest 를 **적어 둔다** | `docker inspect --format '{{.Id}}'` 로 5종. **비교 기준이 없으면 §4.6-④ 를 못 잰다** |
| P9 | 원인이 규명됐다 | ⚠ **원인 미상인 채 복원하면 같은 손상이 다시 온다.** `S2-BLOCKER-INVESTIGATION §1.4`(2026-08-25 소실에서 삭제 주체를 못 잰 사례) |

### 4.1 정지 순서 — **쓰는 쪽부터, DB 는 마지막**

```
docker compose -f infra/staging/compose.i2.yml --env-file $ENVFILE stop \
  frontend nginx core-api pipeline-worker viz-render ai-service
```

| 순서 | 대상 | 왜 이 자리 |
|---|---|---|
| ① | `frontend` · `nginx` | **유입을 먼저 끊는다.** 뒤에 끊으면 정지 중인 서비스에 요청이 계속 들어간다 |
| ② | `core-api` | 원장에 쓰는 유일한 정문 |
| ③ | `pipeline-worker` | outbox 폴링이 살아 있으면 **복원 도중에 상태 전이를 쓴다** |
| ④ | `viz-render` | uploads 를 `:ro` 로 읽는다 — 볼륨 복원(§4.4)의 전제 |
| ⑤ | `ai-service` | `colab_ai` 커넥션 보유자 |
| — | **`pg` 는 세우지 않는다** | 세우면 복원할 대상이 사라진다. **커넥션만 없애면 된다** |
| — | `cloudflared` | **건드리지 않는다.** 터널·DNS 는 어느 쪽에서도 손대지 않는다(`compose.i2.yml` 머리말) |

정지 확인 — `docker ps --filter name=colab_v2_staging` 에 `pg`·`cloudflared` 둘만 남는다.
잔여 커넥션 확인 — `pg_stat_activity` 에서 `colab_platform`·`colab_ai` 가 **0행**.

### 4.2 복원 순서 — 넷을 이 순서로

> **원칙 — 「기동을 막는 것」을 먼저, 「내용」을 나중에.** 비밀이 없으면 검증조차 못 돌린다.

| 순 | 대상 | 하는 일 |
|---|---|---|
| **1** | **비밀 파일 7종**(§2 #5~#8) | 제자리 덮어쓰기만. **`mv` 금지**(㉰). 권한 `0600` · `chown 10001` 재확인 |
| **2** | **`colab_platform`** | §4.3 |
| **3** | **`colab_ai`** | §4.3 (같은 절차, DB 이름만 다름) |
| **4** | **uploads 볼륨** | §4.4 — ⚠ **원장보다 뒤에 둔다.** 원장이 파일 행의 정본이고, 볼륨은 그 행이 가리키는 바이트다 |

⚠ **플랫폼과 AI 를 반드시 둘 다 되돌린다.** 한쪽만 되돌리면 원장의 데이터셋과 사전이 다른 세대가 된다.
**지난 사고가 정확히 `ai` 쪽이었다**(`STAGE2-PREP §2` 1단-2).

### 4.3 DB 하나를 되돌리는 법 — 스키마 교체

```
# ① 대상 스키마를 비운다 — 소유자 롤로. 앱 롤은 DDL 권한이 없다.
docker exec -i colab_v2_staging_pg psql -v ON_ERROR_STOP=1 -U <owner> -d colab_platform \
  -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
# ② 덤프를 적재한다.
gunzip -c $BK/platform-<stamp>.sql.gz \
  | docker exec -i colab_v2_staging_pg psql -q -v ON_ERROR_STOP=1 -U <owner> -d colab_platform
```

| 항목 | 값 · 이유 |
|---|---|
| 롤 | **소유자 롤**(`COLAB_OWNER_PASSWORD` 쪽). 앱 롤은 비소유자·NOBYPASSRLS 라 `DROP SCHEMA` 가 막힌다 |
| `--no-owner --no-privileges` | 덤프가 그렇게 떴다 → **GRANT·롤 부여가 덤프에 없다.** ⚠ **적재 후 앱 롤 권한과 RLS 정책 생존을 따로 확인해야 한다**(§4.6-⑤) |
| `ON_ERROR_STOP=1` | 없으면 **절반만 적재된 DB 가 exit 0** 로 끝난다 — `IS3 §3` F8 이 fixture 로 박아 둔 실패다 |
| `DROP DATABASE` 를 안 쓰는 이유 | 데이터베이스를 지우면 롤 부여·확장·`ts_config` 등 스키마 밖 객체가 함께 날아간다. **교체 범위를 `public` 로 한정한다** |
| ✅ **해소 · 없음** (2026-08-27) | staging 의 `public` 밖 객체가 **없다** — `\dn` = `public` 하나뿐 · `pg_ts_config` 29 항목 전부 기본(사용자 정의 0). 값·근거 = `PLAN-SoT §9 〈165〉-㉰`. **즉 교체 범위를 `public` 로 한정하는 이 절차가 성립한다.** ⚠ `T-1` 이 한국어 `ts_config` 를 만들면 **이 값은 즉시 낡는다** — 재측정을 `T-1` 완료 정의에 넣는다 |

### 4.4 uploads 볼륨 — ⭑ **재료를 만드는 기구가 섰다 (2026-08-27)**

- ~~**현재 백업이 없다**~~ → **`backup-volume.sh` · `backup-full.sh` 로 뜬다.** 산출물 = `vol-<볼륨>-<stamp>.tar.gz`
  ＋ `.manifest.tsv`(경로·크기·sha256) ＋ `.pair`(짝 원장 덤프) ＋ `.sha256`.
- 그러므로 런북의 이 자리는 여전히 **두 갈래**이고, **이제는 ㈎ 가 기본**이다.
  - ㈎ **볼륨 백업이 있을 때** — `infra/staging/restore/restore-volume.sh`. 헬퍼 컨테이너로 풀고 `chown -R 10001:10001`,
    그리고 **매니페스트 전건 `sha256` 대조**까지 한다. ⚠ **덮어쓰기이지 동기화가 아니다** — 아카이브에 없는 파일을 지우지 않는다.
    (`--prune` 같은 선택지를 두지 않았다. 없는 기능은 잘못 쓰이지 않는다.)
  - ㈏ **아카이브가 없거나 RED 일 때** — 볼륨은 **손대지 않는다.** DB 만 과거로 되돌리면 **원장에 없는 고아 바이트**가
    볼륨에 남는다. ⚠ **이것을 「정상」으로 적어 둔다** — 지우는 쪽이 더 위험하다(되돌림의 되돌림이 막힌다).
    같은 이유로 **백업 시점의 고아 바이트도 정상**이고, 볼륨 검사 오라클이 그것을 `INFO` 로만 적는다.
- ⚠ **`R-1` 을 「볼륨 백업 없이」 닫지 않는다.** `STAGE2-PREP §2` 1단-2 의 전범위 백업이 **볼륨을 명시**한다.
  ⚠ **기구가 섰다는 것과 한 번 돌았다는 것은 다르다** — 실 staging 실행은 아직 0회다.

### 4.5 기동 순서

```
docker compose -f infra/staging/compose.i2.yml --env-file $ENVFILE up -d
```

- ⚠ **`-f compose.i2.yml` 확인**(㉮). 빼면 되살리는 명령이 아니라 `rollback.sh` 와 같은 일을 한다.
- ⚠ **`--build` 를 붙이지 않는다.** 복원은 **코드를 바꾸는 일이 아니다.** 재빌드하면 §4.6-④ 의 digest 대조가
  「복원 전과 같은가」가 아니라 「방금 빌드한 것과 같은가」가 되어 **오라클이 사라진다**.
- `volume-init` 이 `chown 10001` 을 먼저 돌고(`service_completed_successfully`) 나머지가 뜬다.
- 컨테이너 **8개**가 `healthy` 가 될 때까지 기다린다 — 여기까지는 **아직 검증이 아니다**.

### 4.6 검증 블록 — **헬스가 아니라 실측 다섯**

> **`/healthz` 6종 200 은 통과 조건이 아니라 최소 전제다.** 자리표시 오리진도 루트 200 을 내고,
> 사전이 빈 ai-service 도 200 을 낸다.

| # | 항목 | 질의 | 통과 기준 |
|---|---|---|---|
| ① | **데이터셋** | `psql -U <owner> -d colab_platform -At -c "SELECT count(*) FROM d3_dataset"` | **12** |
| ② | **계보 간선** | `… -c "SELECT count(*) FROM d4_lineage_edge"` | **6** (2026-08-27 실측 · 전건 확정 · `§9 〈159〉`). ⚠ `B`(`D-09`→`D-16`)는 **이미 그어져 있었다** — 여러 문서의 「5」는 틀린 값이다. **런북은 「복원 시점의 기대치」를 쓰는 것이지 상수를 박는 것이 아니다** |
| ③ | **온톨로지 사전 non-`None`** | `psql -U <owner> -d colab_ai -At -c "SELECT (SELECT count(*) FROM d9_method_term), (SELECT count(*) FROM d9_place_alias), (SELECT count(*) FROM d9_topic_synonym), (SELECT count(*) FROM d9_concept), (SELECT count(*) FROM d9_concept_edge)"` | 앞 셋 = **13 · 4 · 5**(합 **22** = K2 시드) · 뒤 둘 **> 0**. 표 이름은 `app/dictionaries.py` 의 5개 질의가 정본 |
| ③-보 | **읽는 경로까지 살아 있다** | `POST /searches` 를 정문으로 한 번 | `_UnavailableDictionaries` 면 여기서 **`RuntimeError`** 가 난다. **사전 표가 차 있어도 배선이 끊기면 검색에서만 드러난다**(㉲) |
| ④ | **이미지 digest** | `docker inspect --format '{{.Id}}'` — `core-api`·`pipeline-worker`·`viz-render`·`ai-service`·`frontend` 의 `:i2` | **P8 에서 적어 둔 5개와 전건 일치.** 하나라도 다르면 **복원이 아니라 재배포를 한 것**이다 |
| ⑤ | **권한·RLS 가 살아 있다** | 앱 롤로 붙어 cross-tenant 음성 확인 1건 | `--no-privileges` 덤프라 **GRANT 가 덤프에 없다.** 앱 롤이 못 읽거나, 반대로 RLS 없이 다 읽히면 **둘 다 RED** |
| ⑥ | 파일 원장 | `… -c "SELECT count(*) FROM d3_file"` | **129**(`IS3 §14` 실측). ⚠ §4.4-㈏ 를 택했으면 **원장과 볼륨의 대조는 성립하지 않는다 — 그 사실을 적는다** |
| ⑦ | 헬스 | `/healthz` ＋ `/healthz/<unit>` **5종** | 전부 200. **루트 하나만 보지 않는다** |

**판정 — ①~⑤ 가 전부 통과해야 복원 성공이다.** 하나라도 어긋나면 §4.7.

### 4.7 되돌림의 되돌림 (rollback-of-the-rollback)

- **재료 = P7 에서 뜬 「복원 직전 백업」 하나뿐이다.** 이것을 안 뜨고 §4.3 을 실행하면
  **현재 상태가 영구히 사라진다** — `DROP SCHEMA public CASCADE` 는 되돌릴 수 없다.
- 절차는 §4.1 → §4.3 → §4.5 를 **P7 산출물을 대상으로** 한 번 더 도는 것이다. 새 절차가 아니다.
- ⚠ **비밀 파일(§4.2-1)은 되돌아가지 않는다.** 제자리 덮어쓰기라 **옛 값이 어디에도 안 남는다.**
  → **덮어쓰기 전에 같은 디렉터리에 `.bak-<stamp>`(`0600`) 사본을 만든다.** 런북이 이 한 줄을 강제한다.
- ⚠ **볼륨도 되돌아가지 않는다**(§4.4-㈏ 를 택했다면 애초에 안 건드렸으므로 무해하다).
- **되돌림의 되돌림이 실패하면 그 자리는 인프라 사고다** — 조립하지 말고 멈추고 보고한다(`CLAUDE.md §4`).

---

## 5. 살아 있는 staging 에서 **리허설할 수 없는 것**

| # | 리허설 불가 구간 | 왜 | 일회용 인스턴스가 대신 덮는 것 |
|---|---|---|---|
| 1 | **`DROP SCHEMA public CASCADE`** | 비가역이다. 여기서 실패하면 되돌릴 대상 자체가 사라진다 | ✅ **전부 덮인다.** 일회용에 실 산출물 적재 → 스키마 교체 → 재적재까지 그대로 돈다 |
| 2 | **8개 컨테이너 stop/up 왕복** | 공개 staging 이 그동안 죽는다. `-f` 를 빠뜨리면 **조용한 롤백**이 실사고가 된다 | ⚠ **부분만.** 별도 compose 프로젝트명으로 전체를 띄우면 순서·`:?` 키·`volume-init` 은 검증되지만 **터널·DNS·실 태그 경합은 안 덮인다** |
| 3 | **비밀 파일 제자리 덮어쓰기 ＋ inode 동작** | 실패하면 core-api·ai-service 가 **뜨지 않거나** 옛 값을 계속 읽는다 | ✅ 덮인다. 같은 규약(`0600`·uid `10001`·`:ro` 바인드)으로 `mv` vs 덮어쓰기를 **양성·음성 둘 다** 재현 |
| 4 | **uploads 볼륨 복원** | 재료가 없다(§2 #3) | ✅ 덮인다 — **먼저 볼륨 백업 절차부터 세워야 한다.** 이것이 `R-1` 의 실제 선행 결손 |
| 5 | **이미지 digest 대조(④)** | 실 이미지를 지우거나 다시 태그하는 실험을 살아 있는 배포에 못 한다 | ⚠ **부분만.** 「태그 같고 digest 다른」 상황은 만들 수 있으나, **`:i2` 가 언제 움직였는지의 이력은 어디에도 없다** |
| 6 | **RLS·GRANT 생존(⑤)** | 앱 롤 권한을 실 DB 에서 깨 보는 실험이 곧 사고다 | ✅ 덮인다. 소유자·앱 두 롤을 세우고 `--no-privileges` 덤프를 적재해 **앱 롤이 못 읽는 상태**를 재현 |
| 7 | **복원 소요 실측** | 실규모 값은 이미 있다 — platform **317 ms** · ai **130 ms**(`IS3 §15`) | ⚠ **그 값에 업로드 바이트가 안 들어 있다.** 볼륨이 붙으면 다시 잰다 |
| 8 | **원인 규명(P9)** | 사고의 원인은 사고가 나야 있다 | 덮이지 않는다. **P9 를 게이트로 남기는 것이 유일한 대응** |

**리허설 1회차 권고 = 1·3·6 을 일회용 인스턴스에서 한 묶음으로.** 셋 다 완전히 덮이고, 셋이 §4 의
가장 비가역적인 부분이다. 2·5 는 **부분 리허설임을 적어 두고** 넘어간다 — 완전 리허설은 staging 을
하나 더 세우는 일이고 그건 이 WU 의 범위가 아니다.

---

## 6. 이 초안이 닫히려면 — 남은 것

> ⭑ **2026-08-27 갱신 — 이 표는 이제 「남은 것」이 아니라 「무엇이 섰고 무엇이 안 섰는가」다.**
> 기구는 대부분 섰고, **남은 것은 리허설 1건과 그 리허설이 낳는 실측 몇 개**다.

| # | 남은 것 | 상태 |
|---|---|---|
| 1 | **uploads·previews 볼륨 백업 절차** | ✅ **기구 신설 (2026-08-27)** — `infra/staging/backup/` 에 `backup-volume.sh` · `verify-volume-artifact.sh` · `backup-full.sh` · `volume-lib.sh` · `selftest-volume.sh`. **원장 덤프 먼저, 볼륨 tar 나중**(순서를 `backup-full.sh` 가 쥔다). 검사 오라클 = **매니페스트(경로·크기·sha256) ↔ 짝 덤프의 `d3_file`** 대조. 스케줄(`03:30` 매일)이 `backup.sh` → `backup-full.sh` 로 바뀌었고 주간 `latest-check.sh` 가 볼륨도 묻는다. fail-closed 증명 = fixture **14건 전건 RED**(docker 불필요). ⭑ **2026-08-27 실 staging 1회 GREEN** — `R1-REHEARSAL-01 §2.1`. ⭑ **2026-08-27 2차 — 오라클 배선이 닫혔다**(`〈170〉-㉮` · `R1-REHEARSAL-02 §3`). 종전 결손(실 설정 파일에 `COLAB_VOLBACKUP_ORACLE_uploads` 가 없어 V5 가 SKIP → 상위 요약줄은 「원장 오라클 포함 GREEN」)은 **값을 사람 손에서 빼서** 고쳤다 — 기본값이 `volume-lib.sh` 안에 있고, **미선언은 RED · `none` 만 면제**다. fixture 는 **19건**(`VF14`~`VF18` 신설) |
| ~~2~~ | ~~**비밀 7종의 백업·보관 정책**~~ | ✅ **판정 완료 (Ted 2026-08-27 · `PLAN-SoT §9 〈163〉-㉲`) — 백업하지 않는다.** 사본을 늘리는 대가가 되찾는 이득보다 크다(백업이 원본과 **같은 머신 1대** 위에 있다 · `§2` #13). **대신 재발급 절차를 완료 정의에 넣는다 — `§7`** |
| ~~3~~ | ~~**이미지 digest 대장**~~ | ✅ **해소 (2026-08-27 · `PLAN-SoT §9 〈165〉-㉱`)** — 대장을 세웠다: **`dev-package/reference/IMAGE-DIGESTS.md`** (8 건 · 자체 5 ＋ 외부 3). `WORK-UNITS §10.3` 1 단의 「이미지 digest 일치」가 이제 대조 기준을 갖는다 |
| ~~4~~ | ~~**`public` 밖 객체 목록**~~ | ✅ **해소 · 없음 (2026-08-27 · `PLAN-SoT §9 〈165〉-㉰`)** — `public` 스키마 하나뿐이고 사용자 정의 `ts_config` 0. 목록으로 적을 것이 없다는 것이 결과다(§4.3) |
| 5 | **`sha256` 대조 · `--skip-age` 를 스크립트에 넣기** | ✅ **해소 (2026-08-27)** — `infra/staging/restore/preflight.sh` 가 P1~P9 를 센다. **P3 이 `--skip-age`**(원장·볼륨 양쪽), **P4 가 `.sha256` 대조**, **P5-b 가 볼륨↔원장 짝(`.pair`) 확인**. ⚠ **C6·V7 을 없앤 것이 아니라 이 경로에서만 뺀다** — 정기 검사에는 그대로 산다 |
| 6 | **리허설 실행** | ✅ **2회차까지 집행 완료 · 둘 다 GREEN.** ⭑ **2회차 (2026-08-27 19:36 · 기록 `R1-REHEARSAL-02.md`)** — 신설 **7단(일회용 compose 스택)** 이 붙어 `§5-2` 가 덮였다. **완-비2·완-비3·기동 시간·볼륨별 합격선이 전부 닫혔고**, 1회차가 연 둘(오라클 배선 `〈170〉-㉮` · 백틱 `-㉯`)도 닫혔다. 실물 결함 넷을 새로 잡았다(`R1-REHEARSAL-02 §5-㉰`). ⚠ **남은 것은 `R-1` 밖이다** — crontab 재설치·`POST /searches`·`:i2` 이력. 종전 1회차 기록 — ~~1회차 집행 완료 · GREEN (2026-08-27 17:18 · 기록 = `R1-REHEARSAL-01.md`)** — `§5` 의 **1·3·6 ＋ 볼륨 왕복** 전건 통과. 살아 있는 staging 은 읽기만 했고 파괴 플래그를 한 번도 쓰지 않았다. **닫힌 것** = `§8` 의 1·3·4·5·7·8·11 ＋ 볼륨 실크기(12 앞단). **안 닫힌 것** = 완-비2·완-비3(둘 다 컨테이너 왕복 · `§5-2`) ＋ 오라클 배선(`§4-㉮`) ＋ 볼륨별 합격선. ⚠ 실물 결함 둘을 함께 봤다 — **V5 오라클 green-by-skip** · **`rehearsal.sh` 의 백틱 명령치환**(무해했으나 `ops/app-role.sql` 이 셸로 실행됐다). 종전 문구는 아래에 남긴다 — ~~절차는 섰고 실행은 안 했다.~~ `infra/staging/restore/rehearsal.sh` ＋ `REHEARSAL.md` 가 §5 의 **1·3·6 ＋ 볼륨 왕복**을 한 묶음으로 엮는다. **살아 있는 staging 을 읽기만 하고 일회용에만 쓴다** — 어떤 파괴적 단계보다 먼저 돌아도 안전하다. **이것을 돌기 전에는 `R-1` 이 닫히지 않는다** |
| 7 | **런북의 실행본** | ✅ **신설 (2026-08-27)** — `infra/staging/restore/RUNBOOK.md` ＋ `preflight.sh` · `restore-db.sh` · `restore-volume.sh` · `verify-restored.sh` · `expectations.sh` · `check-image-digests.sh` · `selftest-restore.sh`(fixture 10건). 이 문서는 **설계 근거**, 저쪽은 **무엇을 어떤 순서로 치는가**다 |
| 8 | **이미지 digest 대조의 배선** | ✅ **해소 (2026-08-27)** — `check-image-digests.sh` 가 **`reference/IMAGE-DIGESTS.md` 를 읽는다.** digest 를 스크립트에 박지 않았다(대장이 정본 · `IMAGE-DIGESTS §4-4`). P8 이 복원 전 상태를 tsv 로 기록하고 `verify-restored.sh ④-b` 가 그것과 대조한다 — **미측정을 일치로 읽지 않는다**(fixture `SR5`) |
| 9 | **`§4.6` 기대치를 상수로 박지 않기** | ✅ **기구화 (2026-08-27)** — `expectations.sh` 가 **되돌릴 덤프의 COPY 블록을 세어** 그 회차의 기대치를 만든다. `verify-restored.sh` 에는 숫자가 한 개도 없다. fixture `SR0` 이 「같은 스크립트가 다른 덤프에 다른 값을 낸다」를 실증한다 |
| 10 | **일회용 compose 기동 단** | ✅ **신설 (2026-08-27 · Ted 판정 「만들어 돌린다」 · `〈170〉-㉱`)** — `infra/staging/compose.throwaway.yml`(프로젝트 `colab-v2-r1throw`) ＋ `restore/throwaway-stack.sh`. **살아 있는 것과 한 자리도 안 겹친다**: 프로젝트명·볼륨·네트워크 분리 · `container_name:` 없음 · **`ports:` 0** · `cloudflared` 없음 · `build:` 없음 · PGDATA tmpfs. 비밀 7종은 **그 회차에만 존재하는 새 값**이고 `trap EXIT` 에서 지워진다. 겹침 가드 넷이 **돌기 전에** 스스로 선다(주석이 아니라 실제 키만 본다)
| 11 | **보관처 비밀 사본 배제** | ✅ **신설 (2026-08-27 · Ted 판정 「지우고, 생기지 않게 막는다」 · `〈170〉-㉰`)** — `subjects-20260827T051347.json` **1건 삭제**(값 미기록). 재발 방지 = **허용 목록**(`backup_dir_offenders`)을 `backup-full.sh` 0단 · `latest-check.sh` · `preflight P10` 셋에 걸고, 볼륨 트리에는 **이름 모양 판정기**(`secret_shaped`)를 `backup-volume.sh` 매니페스트 직후에 건다. **조용히 제외하지 않고 선다.** fixture `VF17`·`VF18`·`SR10`

---

---

## 7. 비밀 7종 — **백업하지 않는다 · 소실 시 재발급한다** (`〈163〉-㉲`)

**판정 (Ted 2026-08-27).** `credentials.json` · `subjects.json` · `COLAB_STAGING_*_DB_URL_FILE` 5종 · env 파일을
**백업 대상에 넣지 않는다.** 백업하면 비밀의 사본이 하나 더 생기고, 그 사본은 원본과 **같은 WSL2 머신 1대** 위에 놓인다(`§2` #13).

⚠ **「백업 안 함」과 「되찾을 수 없음」은 다르다.** 절차가 문서에 없으면 백업 안 함은 그냥 소실이다.
**`R-1` 은 아래 절차가 문서로 서기 전에는 닫히지 않는다.**

### 7.1 `R-1` 완료 정의에 더해지는 것

| # | 항목 | 통과 기준 |
|---|---|---|
| **완-비1** | **비밀 7종 재발급 절차 문서화** | 7종 각각에 대해 **누가 · 무엇으로 · 어떤 순서로** 다시 만드는지가 `§7.2` 에 값으로 있다 |
| **완-비2** | **재발급 뒤 기동이 선다** | 재발급본으로 `compose.i2.yml` 기동 → 컨테이너 8개 healthy → `§4.6` ①~⑤ 통과 |
| **완-비3** | **원장과 짝이 맞는다** | `credentials.json` 의 계정이 `d1_account`·`d2_member_role` 의 행과 **같은 주체**를 가리킨다(로그인 200 · cross-tenant 음성 1건) |

### 7.2 재발급 절차 — 지금 알 수 있는 범위

**공통 규약 — 셋 다 어긋나면 재발급이 아니라 사고다.**

- **제자리 덮어쓰기만 한다. `mv` 금지.** 마운트가 `:ro` 파일 바인드라 **inode 가 바뀌면 컨테이너가 옛 파일을 계속 읽는다**(`〈93〉-㉰` · `〈109〉-㉳`)
- 권한 **`0600`** · 소유자 **uid `10001`** 재확인
- **덮어쓰기 전에 같은 디렉터리에 `.bak-<stamp>`(`0600`) 사본** — 옛 값이 어디에도 안 남기 때문이다(`§4.7`)

| 대상 | 재발급 수단 | 뒤따르는 일 |
|---|---|---|
| **`credentials.json`** | `services/core-api/ops/set-password.py` — 비밀번호를 **표준입력으로** 받고(`argv` 금지 — `ps`·셸 히스토리에 남는다) `0600` 임시 파일 → 제자리 반영. **scrypt 해시만 저장**(`〈108〉-㉯`) | ① 원장 짝 확인 — `d1_account` 1행 ＋ `d2_member_role` 1행이 **같은 계정**을 가리키는가. 없으면 `services/core-api/ops/provision-account.sql`(⚠ `\gexec` 형태 · `〈109〉-㉱`) ② **core-api 재기동** ③ 로그인 200 · 구 비밀번호 **401** 음성 확인 |
| **`COLAB_STAGING_*_DB_URL_FILE` 5종** | DB 접속 URL 5개를 각각 `0600` 파일로 **다시 쓴다**. 값의 출처 = 현재 살아 있는 롤의 비밀번호(모르면 `X-1`·`〈153〉` 의 회전 절차로 **롤 비밀번호부터 회전**하고 그 값을 쓴다) | ① 5키가 전부 있어야 한다 — 하나라도 없으면 compose 의 `:?` 로 **컨테이너가 아예 안 뜬다**(`§2` #7) ② 전 단위 재기동 ③ `§4.6` ①~⑤ |
| **`subjects.json`** | ⭑ **항목을 둘로 가른다 (2026-08-27).** ⓐ **형식 = 확정.** `{"<토큰문자열>": {"accountId": "<ULID>", "labId": "<ULID>"}}` — 근거는 `services/core-api/tests/fixtures/subjects.json` 실물과 `kernel/auth.py` 가 그 표를 읽는 방식이다. 토큰은 새로 만든다(예: `openssl rand -hex 32`). ⚠ **레포 픽스처 값을 staging 에 올리지 않는다** — 그렇게 배포된 적이 있다(`RESTART §2-1`). ⓑ **「재발급본으로 기동이 선다」(완-비2) = 여전히 미증명.** 컨테이너 왕복이 필요해 **리허설 2회차** 항목이다(`§5-2` 부분 리허설) | 재발급 시 **도구·시험·staging 설정이 쥔 옛 토큰이 함께 끊긴다**(`〈107〉-㉱`) — 끊기는 자리를 먼저 센다 |
| **env 파일** (`--env-file`) | ✅ **해소 — 키 목록 정본은 아래 `§7.3` 이다 (2026-08-27).** 「최소한 5키」가 아니라 **26 키**이고, 그중 `up` 을 막는 `:?` 는 **13** 이다 | ⚠ **`COLAB_CORE_SESSION_SECRET` 이 바뀌면 발급된 세션이 전부 무효다**(무상태 서명 · `〈107〉-㉯`) — 재로그인이 필요하다 |

⚠ **`[미확인]` 둘 중 하나(env 키 목록)는 닫혔고, 하나(`subjects.json`)는 절반만 닫혔다.**
**형식을 안 것과 기동이 선 것은 다르다** — 값을 만들어 적지 않는다.

### 7.3 env 파일 키 목록 — **정본** (2026-08-27 · 레포에서 도출)

**도출 방법 = 세 출처의 합집합.** ⓐ `infra/staging/compose.i2.yml` 의 `${…}` 전건(`:?` 와 `:-` 를 갈라서)
ⓑ `RESTART §2-1` 표 ⓒ `PLAN-SoT §9 〈109〉-㉲`(그 회차가 더한 두 키).
**추정 0 · 값 0** — 아래는 **이름과 성격**뿐이고 어떤 값도 적지 않는다.

**Ⓐ `compose` 가 `:?` 로 요구한다 — 하나라도 없으면 `up` 이 아예 안 뜬다 (13)**

| 키 | 성격 |
|---|---|
| `CF_TUNNEL_TOKEN` | 비밀 — compose 가 `:?` 로 요구하는 터널 키는 **이 하나뿐**이다 |
| `COLAB_PG_SUPER_PASSWORD` | 비밀 |
| `COLAB_CORE_SESSION_SECRET` | 비밀 — 바뀌면 발급된 세션이 **전부 무효** |
| `COLAB_VIZ_SERVICE_TOKEN` | 비밀 — core-api ↔ viz-render **같은 문자열**. 없으면 미리보기 전량 503 |
| `COLAB_VIZ_TILE_SIGNING_SECRET` | 비밀 |
| `COLAB_STAGING_PGDATA_DIR` | 경로(WSL ext4) |
| `COLAB_STAGING_SUBJECTS_FILE` · `COLAB_STAGING_CREDENTIALS_FILE` | 경로 — **가리키는 파일이 비밀** |
| `COLAB_STAGING_CORE_DB_URL_FILE` · `…_PIPELINE_DB_URL_FILE` · `…_AI_DB_URL_FILE` | 경로 — **앱 롤** 접속 URL 파일 |
| `COLAB_STAGING_PLATFORM_OWNER_DB_URL_FILE` · `…_AI_OWNER_DB_URL_FILE` | 경로 — **소유자 롤**. `--profile migrate` 전용이지만 **없으면 마이그레이션이 안 돈다** |

**Ⓑ `compose` 가 `:-` 로 받는다 — 없어도 `up` 은 뜬다 (5)**

`OPENAI_API_KEY`(비밀) · `COLAB_CORE_AI_BASE_URL` · `COLAB_MODEL_HELPER` · `COLAB_MODEL_ORCHESTRATOR` · `COLAB_AI_QUERY_INTERPRETATION`
⚠ **`COLAB_CORE_AI_BASE_URL` 을 비우면 core-api 가 relay 를 안 만들어 검색·제안이 503 이다** — 「없어도 뜬다」와 「없어도 된다」는 다르다.

**Ⓒ `compose` 가 안 읽는다 — 다른 것이 읽는다 (8)**

| 키 | 읽는 쪽 |
|---|---|
| `COLAB_OWNER_PASSWORD` · `COLAB_APP_PASSWORD` · `COLAB_AI_APP_PASSWORD` | DB 롤 세우기·회전(`ops/app-role.sql` 계열). **URL 파일의 내용이 이 값에서 나온다** |
| `CF_API_TOKEN` · `CF_ACCOUNT_ID` · `CF_TUNNEL_ID` | `infra/staging/terraform`(IS2). `up` 은 이것 없이 뜬다 |
| `COLAB_WORKER_LAB_ID` · `COLAB_WORKER_ACCOUNT_ID` | **선택 · 비밀 아님**(시드 ULID). 2026-08-26 부터 필수가 아니다(`〈110〉-㉱`). **원장에 없는 값이면 워커가 안 뜬다** |

**⚠ env 파일에 없는데 있다고 오해하기 쉬운 것** — `COLAB_CORE_CREDENTIALS_FILE`·`COLAB_CORE_SUBJECTS_FILE`·
`COLAB_CORE_UPLOAD_DIR`·`COLAB_VIZ_SOURCE_ROOT`·`COLAB_VIZ_PREVIEW_DIR` 은 **`compose.i2.yml` 안에 값이 박혀 있다.**
호스트에서 손댈 것이 없고, **비면 헬스는 200 인 채로 제품이 잠긴다**(`RESTART §2-1` 말미).

**합계 = 26.** 재발급은 Ⓐ 13 을 먼저 세우고(그래야 기동이 선다), Ⓒ 의 롤 비밀 3 으로 URL 파일 5 를 다시 쓴 뒤,
Ⓑ 를 채우는 순서다.

---

## 8. `R-1` 완료 정의 — **지금 무엇이 닫혔고 무엇이 안 닫혔나** (2026-08-27)

> **닫힘 판정은 `PLAN-SoT §9` 소관이다. 여기는 현황이다.**
> ⚠ **「기구가 섰다」를 「닫혔다」로 적지 않는다** — 이 표가 있는 이유가 그것이다.

| # | 항목 | 상태 |
|---|---|---|
| 1 | 볼륨 백업 절차 (`uploads`·`previews`) | ✅ **기구 · 증명 완료** (fixture 14건) ＋ **실 staging 1회 GREEN (2026-08-27)** · ⚠ V5 오라클 배선은 열려 있다(`R1-REHEARSAL-01 §4-㉮`) |
| 2 | 제자리 복원 런북 | ✅ **실행본 · 스크립트화 완료** (`restore/RUNBOOK.md`) |
| 3 | `sha256` 대조 · `--skip-age` 기구화 | ✅ (`preflight.sh` P3·P4·P5-b) |
| 4 | 이미지 digest 대조 배선 | ✅ 대장을 읽는다 (`check-image-digests.sh`) |
| 5 | `§4.6` 기대치 = 짝 덤프에서 읽기 | ✅ (`expectations.sh` · 상수 0) |
| 6 | env 키 목록 정본 | ✅ **§7.3 · 26 키** |
| 7 | 비밀 7종 재발급 절차 문서화 (**완-비1**) | ✅ 6종 확정 ＋ `subjects.json` **형식** 확정 |
| 8 | 리허설 1회차 실행 | ✅ **집행 완료 · GREEN (2026-08-27) — 기록 `R1-REHEARSAL-01.md`** |
| 9 | **완-비2** 재발급본으로 기동이 선다 | ✅ **닫힘 (2026-08-27 2회차)** — 재발급 7종으로 **7/7 healthy**. `R1-REHEARSAL-02 §2.2` |
| 10 | **완-비3** 원장과 짝이 맞는다(로그인 200 · cross-tenant 음성) | ✅ **닫힘 (2026-08-27 2회차)** — 로그인 **201**(계약값) · 무토큰 **401** · 표 밖 토큰 **401** · 양성 12건 · **음성㈎ 목록 0건 · 음성㈏ id 직접 조회 404**. `R1-REHEARSAL-02 §2.3` |
| 11 | 볼륨 포함 복원 소요 실측 | ✅ **실측 (2026-08-27)** — 원장 `platform` **0.307 s** · `ai` **0.135 s** · 볼륨 `uploads` **4.17 s** → **코어 합 4.62 s**, 검증(V1~V7 4.90 s ＋ 전건 sha256 2.42 s)까지 **11.9 s**. ⭑ **기동 시간이 붙었다 (2회차)** — **7 컨테이너 healthy 까지 5.0 s**(`cloudflared` 제외 · 이미지 기존). **실사고 총 소요 = 4.62 ＋ 11.9 ＋ 5.0 s.** `[미확인]` 소멸 |
| 12 | 볼륨 실제 크기 · 볼륨별 합격선 | ✅ **실크기 닫힘** — `uploads` **503,320 KiB**(아카이브 325.7 MiB · 파일 135) · `previews` **6,484 KiB**(6.17 MiB · 39). 3일 보존 = 약 **1.04 GB**, 여유 **912 GiB** → 현실적. 실사용×3 가드 요구 1.44 GiB 대비 여유 **633 배** → 현실적. ⭑ **합격선도 닫혔다 (2회차)** — `uploads` **67** · `previews` **19** = 실측(135·39)의 **절반**. 근거는 원장 `〈128〉` 과 같다(막을 것은 「거의 빈 아카이브」 · 늘수록 자동으로 보수적 · 두 배가 되면 갱신). ⚠ **값을 설정 파일이 아니라 `volume-lib.sh` 에 뒀다** — 실 설정 부재로 기본 `1` 이던 것이 `〈170〉-㉮` 와 같은 모양이었다 |

**⭑ 2026-08-27 2회차 — 위 12행이 전건 ✅ 가 됐다.** 1회차가 새로 연 둘(오라클 배선 `〈170〉-㉮` · 백틱 `-㉯`)도 닫혔고,
Ted 판정 둘(비밀 사본 `-㉰` · 일회용 기동 단 `-㉱`)도 집행됐다. 기록 = `R1-REHEARSAL-02.md`.

⚠ **그래도 「`R-1` 이 끝났다」로 읽지 않는다 — 이 12행 밖에 남은 것이 있다.**

| 남은 것 | 왜 |
|---|---|
| **crontab 재설치**(`install-schedule.sh install`) | 호스트 crontab 이 아직 `backup.sh` 를 부른다 — **야간 회차는 원장만 뜬다**(`〈169〉-㉳`). 시스템 설정이라 리허설 회차의 권한 밖이었다 |
| **오라클을 켠 채 스케줄이 도는가** | 위와 한 몸. 확인 수단 = 재설치 뒤 **다음 03:30 회차의 로그**. 손으로 돌린 GREEN 은 기구가 아니다 |
| `§4.6-③-보` `POST /searches` 1회 | 2회차는 `datasets` 로 경계를 쳤다. `_UnavailableDictionaries` 는 검색 시점에야 터진다 |
| `preflight` 가 리허설 경로에서 GREEN 이 될 수 없는 성질 | 결함인지 의도인지 **판정 대기** |
| `:i2` 태그 이동 이력 · `§5-8` 원인 규명(P9) | `§5-5` 의 남은 절반 · 사고가 나야 있는 값 |

**종전 문구 — 이번 회차에 사실이 아니게 됐다.** ~~즉 `R-1` 은 9·10 이 남아 있고, 둘 다 「컨테이너 8개 왕복」 하나에 걸려 있다.~~

---

*작성 2026-08-27. 읽기 전용 감사의 산출이고 어떤 명령도 집행하지 않았다 — 판정은 `PLAN-SoT §9`.*
*⭑ 2026-08-27 2차 — `§1.1`·`§4.4`·`§6`·`§7.3`·`§8` 을 더했다. **기구를 세웠고 어떤 명령도 살아 있는 staging 에 집행하지 않았다.***
