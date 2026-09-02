# staging 단독 창 — 실행 런북 (설계본 · 2026-09-02)

> **이 문서는 절차서다. 값·근거의 정본은 각 회차 기록과 `PLAN-SoT §9` 다.**
> 작성 조건 = 읽기 전용 설계(레포 무접촉 · staging 무접촉 · 게이트 0회 실행 · 이 파일 외 편집 0건).
> **창 안에서 새로 나온 값은 이 문서가 아니라 그 회차의 `sessions/` 기록에 적는다.**

## 0. 창의 전제 — 왜 한 창인가

- staging 스택 동시 점유 = **1 레인**(`notes/PARALLEL-LAUNCH-MAP.md §4` 「배포·복원·백업은 상호 배타」).
- pg 슬롯 풀은 **호스트 전역 4**(`gates/tools/_pg.sh:68`·`:71`) — 창이 열려 있는 동안 다른 레인의 `gates/run.sh all` 은 red(준비)를 낸다.
- 아래 각 단계는 **뒤 단계의 측정을 오염시킨다.** 그래서 순서를 고정하고, 단계마다 「오염 범위」를 적는다.

### 0.1 창 전체의 선행 조건 (하나라도 아니면 창을 열지 않는다)

| # | 조건 | 확인 방법 |
|---|---|---|
| ⓐ | `lane-62` 병합 완료 · `main` 워킹트리 변경 **0건** | `git -C <레포> status --porcelain \| grep -c .` = 0 (`deploy.sh:62`) |
| ⓑ | 창 전체를 **`main` 체크아웃**에서 돈다 — 워크트리 금지 | 크론 설치가 `$HERE` 경로를 crontab 에 박는다(`backup/install-schedule.sh:39-41`) |
| ⓒ | env 파일 `$COLAB_STAGING_ENV`(홈 0600) 실재 | `deploy.sh:45` 가 없으면 die |
| ⓓ | 다른 레인 0개 — 게이트·백업·복원 동시 실행 없음 | `docker ps` · 호스트 crontab 시각 확인 |
| ⓔ | 창 시각이 **03:30 · 04:10(월) · 04:40 크론과 겹치지 않는다** | `backup/schedule.crontab`. 겹치면 무인 회차와 창이 같은 스택을 문다 |
| ⓕ | 원장(`release-ledger.tsv`)의 green `deploy` 행 **≥2** | `#43` 해소 여부. `b3c4085ccdf0`·`14d3136aa55a` 등재분 확인 |

⛔ **`--skip-backup`·`--skip-alias-reattach`·`--allow-dirty`·`COLAB_PG_MAX_CONCURRENT` 상향은 이 창에서 금지다.**
스크립트가 파괴적 플래그 없이 거부하면 **그 거부가 올바른 동작**이다 — 우회하지 않고 멈추고 보고한다.

---

## 1. 단계 A — 배포 전 짝 백업 (**追加: 이 창이 새로 넣는 단계**)

| 축 | 값 |
|---|---|
| **파괴 등급** | additive (보관처에 산출물만 쓴다) |
| **선행 조건** | `0.1` 전건 · 스택이 **올라간 상태**(`sessions/DEPLOY-269-20260901.md:15-17` — 스택을 내린 채 돌려 pg 를 못 찾아 red 를 낸 회차가 있다) |
| **명령** | `infra/staging/backup/backup-full.sh` |
| **증거** | platform·ai 두 프로파일 **GREEN**(통과 7 · SKIP 0) ＋ 같은 회차 스탬프의 `vol-uploads`·`vol-previews` 아카이브가 보관처에 실재. 로그에 `═══ 1단` 표지 |
| **되돌림** | 없음(산출물만 생성). 되돌릴 것이 없다 |
| **오염 범위** | 없음 |

**왜 `deploy.sh ⑤` 로 충분하지 않은가 — 이 창의 핵심 판단.**
`deploy.sh:149` 가 부르는 것은 `backup/backup.sh` = **원장 덤프 2프로파일뿐**이다. 이번 배포는
`0011_lv1_drop_level_user_set` 로 **열 ＋ CHECK 를 떨어뜨린다**. 롤백은 **스키마를 되돌리지 않으므로**
(`deploy.sh:14-16` · `rollback.sh:15-18` forward-only) 그 마이그레이션의 유일한 되돌림 재료는 **덤프**다.
그리고 복원은 **원장 덤프와 볼륨 아카이브가 한 벌인 회차**를 요구한다(`restore/preflight.sh` P5-b ·
`RUNBOOK.md:63-69`). ⟹ **`backup-full.sh` 를 배포 직전에 손으로 한 번 돌린다.** `deploy.sh ⑤` 는
그대로 두고(끄지 않는다), 이 단계는 그 **위**에 얹는 짝 회차다.

---

## 2. 단계 B — `main` staging 배포

| 축 | 값 |
|---|---|
| **파괴 등급** | **destructive** (마이그레이션이 열·CHECK 를 떨어뜨린다 · forward-only) |
| **선행 조건** | 단계 A GREEN · Ted 배포 승인 행이 **원장에 배포 행보다 먼저**(`DEPLOY-269:10`) · 워킹트리 0건 |
| **명령** | `infra/staging/deploy.sh --target staging` (플래그 없음) |
| **되돌림** | 이미지 = `infra/staging/rollback.sh --to-last-green`. **스키마는 되돌아가지 않는다.** 스키마까지 되돌리려면 단계 A 의 덤프로 `restore/restore-db.sh --yes-drop-schema` = **파괴적 복원**이다 |
| **오염 범위** | 이후 **전 단계**. 배포가 red 면 창을 닫는다 |

**증거 — 200 은 증거가 아니다.** `verify-deploy.sh` 요약줄의 다음 여섯을 이름으로 적는다
(`DEPLOY-269 §2` 가 쓰는 표 그대로):

1. 실행 이미지 태그 **앱 5종 전부** `= 배포 커밋`, 별칭 `:i2` **6/6** 이 같은 이미지 ID
2. 마이그레이션 체인 head — platform **`0011_lv1_drop_level_user_set`** · ai `0005_k2b_concept_graph_seed` (`verify-chains.sh`)
3. 헬스 **본문 대조** — 루트 `^ok$` ＋ 단위 5종 `"unit"` 값 일치(6종 200 만으로는 부족)
4. 컨테이너 **8개 healthy** · 호스트 노출 `0.0.0.0` **0건**
5. `⑩-b` **엣지 설정 바이트 대조** — 레포 판 sha16 ＝ 도는 컨테이너 안의 판(`deploy.sh:205-214`)
6. 원장 마지막 줄 = `deploy … green … 배포전백업GREEN 워킹트리변경=0`

**이 회차에 반드시 함께 재는 것 (배포가 실어 나른 변경분 · 헬스가 감추는 자리)**

| 대상 | 잴 것 |
|---|---|
| `0011` 스키마 변경 | 대상 열·CHECK 가 **실물에서 사라졌는가**(`information_schema` 조회 · 읽기 전용) |
| `kernel/file_store.py` · `downloadDataset` | 302 **두 홉**이 실제로 두 번 서고 마지막이 본체 바이트인가 — 첫 302 의 200 만 보지 않는다 |
| 소유권 게이트 | 남의 연구실 자원 접근이 **404**(403 이 아니다 — `DEPLOY-269 §3` 의 판정 규약) |
| 주기 트리거 드레인 | 봉투 1건이 실제로 소비돼 무효화가 일어나는가(`〈60〉` 의 배경 루프) |
| `DatasetCreate` 확대 3필드 | `variables`·`crs`·`period` 를 실어 **400 이 아닌** 것 1회(`#62`) |
| 등록 화면 변경 | 목업 대비 화면 1회(`lane-62` 범위) |

⚠ **`deploy.sh ⑧` 이 마이그레이션을 돌린다 — 손으로 DDL 을 치지 않는다**(`DEPLOY-269:20`).

---

## 3. 단계 C — 크론 셋째 줄 설치 (`check-cron-streak.sh`)

| 축 | 값 |
|---|---|
| **파괴 등급** | mutating (호스트 crontab) |
| **선행 조건** | **`main` 체크아웃에서 실행**(워크트리 경로가 crontab 에 박히면 워크트리 삭제 시 크론이 죽은 트리를 가리킨다 — `schedule.crontab` 머리말의 8주 사건) |
| **명령** | `infra/staging/backup/install-schedule.sh install` |
| **증거** | 출력 `스케줄 설치: GREEN (블록 표식 · 실행 줄 3건 · 블록 밖 보존 전부 실측)` (`install-schedule.sh:93`) ＋ `install-schedule.sh verify` 를 **따로 한 번 더** 돌려 실행 줄 3건 재확인. 「설치했다」와 「걸려 있다」는 다르다(`:11-14`) |
| **되돌림** | 설치 전 스냅숏으로 `crontab "$SNAP"`(`install-schedule.sh:108`). **비파괴** |
| **오염 범위** | 04:40 회차가 창 중에 뜨면 백업 로그가 섞인다 — `0.1-ⓔ` 로 회피 |

⚠ **연속 3회 무인 GREEN 은 이 창에서 나오지 않는다** — `COLAB_CRON_STREAK_MIN` 기본 3 이고
회차는 하루 1회다(`check-cron-streak.sh` 머리말 C1). 창의 산출은 **기구 설치**이지 streak 값이 아니다.
창 안에서 손으로 돌린 GREEN 은 **무인으로 세지 않는다**(`〈255〉-㉮` 축자).

---

## 4. 단계 D — `R-1` 복원 실측

| 축 | 값 |
|---|---|
| **파괴 등급** | **destructive** (`DROP SCHEMA public CASCADE` · 볼륨 덮어쓰기) |
| **선행 조건** | 단계 B GREEN · 단계 A 의 **짝 회차** 존재 · `COLAB_RESTORE_CAUSE` 기재(비면 P9 RED) · `COLAB_RESTORE_PRE_BACKUP` 지목 · `/tmp/pre-digests.tsv` 를 **다른 창에** 보관 |
| **오염 범위** | 복원 시점 이후 staging 에 쌓인 것 **전량 소멸**(입도 = 하루 1회 회차 · `RUNBOOK §0.1`). ⟹ **단계 E(S3 적재)를 복원보다 먼저 하면 적재분이 지워진다** |

**순서 — 무해 리허설을 먼저 돌린다.**
`restore/rehearsal.sh` 는 살아 있는 staging 을 **읽기만 하고 일회용 `r1_*` 에만 쓴다**
(`rehearsal.sh:4-9`) — **어떤 파괴적 단계보다 먼저 돌려도 안전하다.** 제자리 복원 전에 한 번 돌려
재료(회차 짝·볼륨 아카이브)가 서는지 확인한다.

**절차 (`restore/RUNBOOK.md` 그대로 · 새 절차를 만들지 않는다)**

```
set -a; . "$ENVFILE"; set +a
export COLAB_RESTORE_CAUSE="<한 줄>"            # 비면 P9 RED — 이것이 올바른 거부다
infra/staging/backup/backup-full.sh             # §1 P7 · 되돌림의 되돌림 재료
export COLAB_RESTORE_PRE_BACKUP="$BK/platform-<방금 stamp>.sql.gz"
infra/staging/restore/preflight.sh --record-digests /tmp/pre-digests.tsv
# §2 정지 — 쓰는 쪽부터. pg·cloudflared 는 남긴다
docker compose -f infra/staging/compose.i2.yml --env-file $ENVFILE stop \
  frontend nginx core-api pipeline-worker viz-render ai-service
# §3.2 원장 둘 — 반드시 둘 다
infra/staging/restore/restore-db.sh --db colab_platform --owner $OWNER --dump "$BK/platform-<stamp>.sql.gz" --yes-drop-schema
infra/staging/restore/restore-db.sh --db colab_ai       --owner $OWNER --dump "$BK/ai-<stamp>.sql.gz"       --yes-drop-schema
# §3.3 볼륨 — 원장보다 뒤
infra/staging/restore/restore-volume.sh --volume uploads  --archive "$BK/vol-uploads-<stamp>.tar.gz"  --yes-overwrite-volume
infra/staging/restore/restore-volume.sh --volume previews --archive "$BK/vol-previews-<stamp>.tar.gz" --yes-overwrite-volume
# §4 기동 — --build 를 붙이지 않는다(붙이면 §5-④ 오라클이 사라진다)
docker compose -f infra/staging/compose.i2.yml --env-file $ENVFILE up -d
```

⚠ **`--yes-drop-schema`·`--yes-overwrite-volume` 없이 스크립트가 거부하면 그것이 올바른 동작이다.**
문 셋(`--yes-drop-schema` · `COLAB_RESTORE_PRE_BACKUP` · 커넥션 0)이 전부 서야 한 글자라도 쓴다(`RUNBOOK:107`).

**증거**

```
infra/staging/restore/verify-restored.sh \
  --platform-dump "$BK/platform-<stamp>.sql.gz" --ai-dump "$BK/ai-<stamp>.sql.gz" \
  --owner "$OWNER" --pre-digests /tmp/pre-digests.tsv --base-url https://www.colab-hydro.com
```

- 기대치는 **짝 덤프에서 읽는다** — 상수를 옮겨 적지 않는다(`verify-restored.sh:3-7`).
- **④-b** = 복원 전(P8) digest 와 동일. 다르면 「복원이 아니라 재배포를 한 것」(`verify-restored.sh:70`).
- **`--manual-ok` 없이 나오는 exit 3(「복원 검증 미완」)이 올바른 출력이다** — 손검사 2건을 안 돌고 GREEN 이라 말하지 않는다(`:102-110`).

**손검사 2건의 자동화 — 이 창의 산출물 하나**

| 항 | 지금 | 이 창이 세울 것 |
|---|---|---|
| ③-보 | 스크립트가 인증을 안 쥐어 사람이 돈다(`:59-60`) | `ai-service` 컨테이너 안에서 `POST /searches` 1회. **판정 = 200 ＋ `degraded:false` ＋ 원 질의에 없던 확장 낱말 ≥1**(`〈255〉-⑵`). 상태코드만 보면 사전이 끊겨도 통과한다 |
| ⑤ | 앱 롤 접속을 스크립트가 안 쥔다(`:77-78`) | env 파일의 **앱 롤**로 붙어 ⓐ 자기 연구실 행이 보이고 ⓑ 타 연구실 행 **0행** — 양성·음성 둘 다 |

두 검사는 **베어러 자격증명이 필요 없다** — ③-보 는 `ai-service` 직행(정문 중계 다리는 `〈255〉` 가
stage 3 으로 뺐다), ⑤ 는 DB 앱 롤이다. ⟹ **단계 E 와 달리 이 단계는 막혀 있지 않다.**
자동화가 서면 `verify-restored.sh --manual-ok` 를 **사람 확인 없이 기계가 채운다** —
그전까지 `--manual-ok` 를 사람이 손으로 붙이는 것은 SKIP 이다.

**되돌림** — `RUNBOOK §7`. 재료 = **P7 백업 하나뿐**. 절차 = §2 → §3.2 → §4 를 P7 산출물로 한 번 더.
**되돌림 자체가 파괴적이다**(다시 `DROP SCHEMA`). 비밀 파일은 `.bak-<stamp>` 없이는 되돌아가지 않는다.
**되돌림의 되돌림이 실패하면 인프라 사고 — 조립하지 말고 멈추고 보고한다.**

---

## 5. 단계 E — `S3` 잔여 (NumPy 본체 적재 ＋ 포맷 5종 엣지 왕복)

| 축 | 값 |
|---|---|
| **파괴 등급** | mutating (staging 쓰기 — 데이터셋·파일 행 ＋ 볼륨 바이트) |
| **선행 조건** | 단계 D 완료(복원이 뒤에 오면 적재분이 지워진다) · **베어러 자격증명 경로** ⛔ **미입수** |
| **오염 범위** | 데이터셋·파일 계수가 늘어난다 ⟹ 이후 복원 검증의 기대치(짝 덤프 기준)와 어긋난다. 단계 D 를 다시 돌 수 없다 |

**막힌 것 — 정확히 무엇이 필요한가.**
자격증명은 **두 곳에서** 필요하고 지금 둘 다 같은 값에 걸려 있다.

1. **적재** — `infra/staging/load-seed.py --base-url … --token-file PATH --manifest … --source-root …`
   이 도구는 **DB 에 접속하지 않고 공개 API 넷만 부른다**(`load-seed.py` 머리말 · `createUpload`·
   `createDataset`·`attachUploadGridFiles`·`listDatasets`). ⟹ `--token-file` 이 가리킬 **0600 파일 경로**가 필요하다.
2. **엣지 왕복** — 주 화면 요청에 `Authorization: Bearer` 가 필요하다(`S3` note ㉱).

**Ted 에게 요청할 것 = 한 줄** — 「staging 실연구실 베어러가 든 **홈 0600 파일의 경로**」.
후보(확인 필요 · 지어내지 않는다) = 컨테이너 안 `/etc/colab/subjects.json` 경로로 이미 한 번 읽은 전례가 있다(`#29`).
**값은 어디에도 적지 않는다 — 경로만 받는다.**

**절차 (경로를 받는 즉시 실행 가능한 형태)**

1. **NumPy 본체 1건 적재.** 원천 = `01.level-data/02.vegetation/02.vegetation/Lv.2/Prediction_*.npy`
   (본체) ＋ 동봉 격자 `#metadata/LAT_crop.npy`·`LON_crop.npy` **(1280,1280) 짝**
   (`services/viz-render/tests/test_e2e_real.py:290-317`).
   ⚠ **`04.Lat_Lon_info` 의 `.npy` 는 기준 격자다 — 그것을 올리면 지금 상태(본체 0건)가 그대로다.**
   ⚠ `LAT.npy`·`LON.npy` 는 `(852,1200)` 이라 **짝이 아니다** — 붙이면 형상 대조에서 거절되는 것이 정상이다.
2. **포맷 5종 공개 엣지 왕복.** `tif`·`nc`·`gz`·`hdf`·`npy` 각 1건, 주 화면 경로로.

**증거**

- 적재 = `d3_file` 에 `kind = 본체` 인 `npy` **≥1행**(적재 전 실측 0건 — `S3` note ㉰).
  적재 전후 계수를 **둘 다** 적는다(데이터셋 13 · 파일 130 이 적재 전 값).
- 왕복 = **포맷 이름과 함께** `200 ＋ Content-Type: image/png ＋ 매직 `89504e47``, `text/html` **0건**.
  **5종 각각을 이름으로 적는다** — 「13/13 200」처럼 포맷 구성이 안 적힌 계수는 이 조항을 못 닫는다(`S3` note 이전 문면).
- 게이트 `e2e-format-coverage` 는 **로컬** 오라클이고 이 조항을 닫지 않는다(그 게이트 머리말 축자).

**되돌림** — 만든 데이터셋·파일 행을 `DELETE` 하고 **잔재를 표별로 0건 실측**(`DEPLOY-269 §7` 의 방식).
볼륨 바이트는 고아로 남을 수 있다 — 그것은 정상이다(`RUNBOOK:120`). **되돌림은 mutating**.

---

## 6. 단계 F — `#43` 롤백 경로 → `I3 ⑷⑸`

| 축 | 값 |
|---|---|
| **파괴 등급** | **destructive** (도는 릴리스를 의도적으로 되돌린다) |
| **선행 조건** | 원장 green `deploy` 행 **≥2** ＋ **그 태그의 이미지 6종이 실물로 남아 있을 것**(보존 3개 · `rollback.sh:68-69` 「원장 한 줄이 곧 롤백 가능을 뜻하지 않는다」) · 단계 D·E 의 측정이 **전부 끝나 있을 것** |
| **명령** | `infra/staging/rollback.sh --to-last-green` → 판정 후 `infra/staging/deploy.sh --target staging` 로 **다시 앞으로** |
| **오염 범위** | 되돌리는 동안 서빙 릴리스가 옛 것이다 ⟹ 단계 E 의 왕복·단계 D 의 digest 대조를 이 뒤에 재면 **다른 릴리스를 잰 것**이 된다 |

**증거 (⑷ 롤백 왕복 · ⑸ 직전 릴리스 확인)**

- `ledger_rollback_target()` 이 **대상을 골랐다**는 사실 — 인자 없이 부르면 exit 64 로 거부하고,
  대상이 0건이면 exit 69 로 거부한다(`rollback.sh:39-48`·`:66-72`). **그 거부가 올바른 동작이다.**
- 헬스 green **＋ `serving_tag_is $TAG`** — 「헬스는 태그를 묻지 않는다」(`rollback.sh:97-104`).
  옛 이미지로 살아 있어도 6종 200 이 나온다. **이것이 이 창에서 200 을 증거로 쓰지 않는 대표 자리다.**
- `:i2` 재부착 GREEN(붙인 뒤 이미지 ID 대조 · `:119-126`) ＋ digest 이력 append(`:129`).
- 원장에 `rollback … green … (직전 배포=<이전 태그>)` 1행 ＋ 되돌아온 배포의 green 1행.

⚠ **스키마는 되돌아가지 않는다.** `0011` 이 떨어뜨린 열은 롤백 뒤에도 없다 —
**옛 이미지가 그 열을 읽으면 그 자리가 red 로 드러난다.** 그것이 forward-only 의 실제 위험이고,
이 창이 롤백 왕복을 **`0011` 배포와 같은 창에 두는 이유**다(다른 창으로 미루면 아무도 안 잰다).
red 가 나면 즉시 앞으로 되돌아간다(`deploy.sh` 재실행) — 그것이 이 단계의 되돌림이다.

---

## 7. 단계 G — `IS4 ①` terraform apply (실 터널)

| 축 | 값 |
|---|---|
| **파괴 등급** | **destructive** (실 터널 · 공개 엣지) |
| **선행 조건** | 단계 E 의 엣지 왕복이 **이미 끝나 있을 것**(아래 판단) · `terraform` 설치 · `CF_API_TOKEN`·`CF_ACCOUNT_ID`·`CF_TUNNEL_ID` 주입(`tunnel/README §3`·`§5-1`) |
| **명령** | `terraform init` → `terraform import …` → **`terraform plan`(사람이 읽는다)** → `terraform apply` → `terraform plan` |
| **증거** | ⑴ apply 전 plan 이 **`ingress_rule` 값 불변 · `destroy`/`replace` 0건 · `1 to change`(민감도 표시만)** ⑵ apply 후 plan 이 **문자 그대로 `No changes.`** ⑶ `https://www.colab-hydro.com/healthz` 200 ＋ **단위 5종 본문 대조** ⑷ 단계 E 왕복 중 **1건 재측정**이 같은 결과 |
| **되돌림** | `tunnel.tf` 를 직전 커밋으로 되돌리고 다시 apply(`README §4 롤백`). **되돌림도 apply 다 = destructive** |
| **오염 범위** | 공개 엣지 전체. 실패하면 단계 E·B 의 엣지 측정이 전부 무효 |

⛔ **plan 에 `destroy`·`replace` 나 `ingress_rule` 값 변경이 하나라도 보이면 멈추고 보고한다**(`README §4`).

---

## 8. 단계 H — `IS4 ②`(맨몸 호스트 조건) · `I4`(운영 리허설)

| 축 | 값 |
|---|---|
| **파괴 등급** | read-only ~ additive (문서·기록) |
| **선행 조건** | 단계 D 의 복원 결과 · 단계 G 의 `No changes.` |

- **`I4` 는 리허설을 다시 돌리지 않는다** — `R-1` 의 결과를 **받아 쓴다**(`〈215〉`-㉮ 축자 · 대장 `I4.completion_def`).
  이 창에서 `I4` 가 받는 것 = 단계 D 의 `verify-restored` GREEN **하나뿐**이다.
- ⛔ **`I4` 는 이 창에서 닫히지 않는다.** 남은 넷 중 **분산 추적·로그·알람·데이터 레지던시의 실물이 0건**이다
  (`〈249〉`-㉮ 전수 grep — 히트는 `infra/README.md:33`·`:37` 산문 두 줄뿐).
- ⛔ **`IS4 ②`(맨몸 호스트 조건)도 `R-1` 로 충족되지 않는다.** `R-1` 의 백업 산출물에 **terraform state 가 들어 있지 않다**
  (규약 = `platform-*`·`ai-*`·`vol-*` · `preflight` P10 이 규약 밖 파일 0건으로 통과 — 대장 `IS4.note`).
  ⟹ 이 창의 산출은 「`R-1` 이 닫혀도 `IS4` 미달 2건 중 ②는 남는다」는 **재확인**이다. 상태값을 고치지 않는다.

---

## 9. 순서 — 확정본과 바꾼 이유

| 순 | 단계 | 파괴 등급 |
|---|---|---|
| A | 배포 전 **짝 백업**(`backup-full.sh`) | additive |
| B | `main` 배포(`0011` 포함) | **destructive** |
| C | 크론 셋째 줄 설치 | mutating |
| D | `R-1` 복원 ＋ 손검사 2건 자동화 | **destructive** |
| E | `S3` — NumPy 본체 적재 ＋ 5종 엣지 왕복 | mutating ⛔ **차단** |
| F | `#43` → `I3 ⑷⑸` 롤백 왕복 | **destructive** |
| G | `IS4 ①` terraform apply | **destructive** |
| H | `IS4 ②` · `I4` 판정 | read-only |

**바꾼 것 셋**

1. **A 를 신설했다** — 스키마를 떨어뜨리는 마이그레이션 직전에 **볼륨까지 짝지은** 백업이 필요하다.
   `deploy.sh ⑤` 는 원장 덤프뿐이라(`deploy.sh:149` → `backup.sh`) 단계 D 의 P5-b 짝 조건을 못 채운다.
2. **D(복원)를 F(롤백 왕복)보다 앞에 둔다.** 근거 셋 —
   ⓐ 복원 검증 ④-b 는 **복원 전 digest 와 같은가**를 묻는다(`verify-restored.sh:70`). 롤백은 서빙 이미지와
   `:i2` 를 **옛 태그로 옮기므로**(`rollback.sh:119-126`) 롤백 뒤 복원하면 이 오라클이 「어느 릴리스 기준인가」를 잃는다.
   ⓑ 복원 리허설은 `:i2` 로 이미지를 찾는다(`compose.throwaway.yml`) — 롤백 직후에는 그 이름이 **되돌린 옛 것**을 가리킨다.
   ⓒ `I4` 가 받아 쓸 복원 결과는 **배포된 릴리스 기준**이어야 한다.
3. **E(엣지 왕복)를 G(터널 apply)보다 앞에 둔다.** apply 는 공개 엣지의 ingress 를 대상으로 하고,
   README 는 값 불변을 **plan 으로 사전 증명**하라고 요구한다 — 즉 **불변이 보장된 것이 아니라 확인 대상**이다.
   왕복을 apply 뒤로 미루면 실패 시 「포맷 문제인가 터널 문제인가」가 갈리지 않는다.
   ⟹ **왕복 먼저 → apply → 왕복 1건 재측정**(단계 G 증거 ⑷).

**바꾸지 않은 것** — F(롤백) 를 E 뒤에 두는 것은 원안 그대로다. 롤백은 서빙 릴리스를 바꾸므로
그 앞의 모든 실측이 끝나 있어야 한다.

---

## 10. Go/No-go 체크포인트 (advisor 게이트 ③ 적용 자리)

| # | 자리 | 보이는 증거 | no-go 면 |
|---|---|---|---|
| ① | **B 착수 직전** | A 의 두 프로파일 GREEN ＋ 볼륨 산출물 실재 · 워킹트리 0건 · 승인 행 | 창을 닫는다 |
| ② | **B ⑧(마이그레이션) 직전** | `0011` 이 떨어뜨릴 열·CHECK 의 현재 실물 · 되돌림 재료 경로 1줄 | 배포를 멈춘다(스키마 무접촉 상태로 남는다) |
| ③ | **D 착수 직전** | `preflight.sh` P1~P9 · `COLAB_RESTORE_CAUSE` 실값 · 회차 짝 · `/tmp/pre-digests.tsv` | 복원을 하지 않는다. B 는 그대로 산다 |
| ④ | **D 판정 후** | `verify-restored` 자동분 전건 ＋ 손검사 2건 자동 판정 | `RUNBOOK §7` 되돌림의 되돌림 — **그 자체가 파괴적**이라 별도 승인 |
| ⑤ | **F 착수 직전** | 원장 green 2행 ＋ **그 태그 이미지 6종 실재** ＋ D·E 측정 완료 | 롤백을 하지 않는다(`#43` 은 열린 채) |
| ⑥ | **G apply 직전** | `terraform plan` 전문 — `destroy`·`replace` 0건 · `ingress_rule` 값 불변 | apply 하지 않는다 |

---

## 11. 이 창에서 할 수 없는 것 (감추지 않는다)

| # | 항목 | 막는 것 |
|---|---|---|
| ⛔1 | **`S3` 단계 E 전체** | **베어러 자격증명 파일 경로 미입수.** 적재(`load-seed.py --token-file`)와 엣지 왕복 **둘 다** 같은 값에 걸린다. 경로 한 줄이면 즉시 집행 가능 |
| ⛔2 | `R-1` ⑴ 무인 **연속 3회** GREEN | 회차가 하루 1회다. 창의 산출은 **기구 설치**뿐 |
| ⛔3 | `I4` 완결 | 분산 추적·로그·알람·데이터 레지던시 **실물 0건**(`〈249〉`-㉮). 창 안에서 만들 것이 아니다 |
| ⛔4 | `IS4 ②` 맨몸 호스트 | `R-1` 산출물에 terraform state 가 없다(`IS4.note`). 별도 재료가 필요하다 |
| ⛔5 | 시점 복구(WAL) | 실물 0건이 **확인됐다**. `〈256〉` 로 prod 개통 관문 (다) 로 옮겼다 — 이 창의 범위가 아니다 |
| ⛔6 | `terraform` 설치 여부 | `tunnel/README §5`(2026-08-22) 는 **호스트에 미설치**라고 적는다. 창 전에 실물 확인 필요 — `[미확인]` |

---

## 12. 시간

| 단계 | 추정 | 근거 |
|---|---|---|
| A 짝 백업 | **`[미확인]`** | 회차 기록에 소요가 안 적혀 있다 |
| B 배포 | **약 30분** | `〈185〉` 회차 — 원장 green `10:08` · 판정 실측 `10:16`(`DEPLOY-269 §2` 시점 표기) ＋ ⑤ 백업·⑧ 마이그레이션 포함 |
| C 크론 설치 | **약 5분** | 명령 1회 ＋ `verify` 1회 |
| D 복원 | **`[미확인]`** | 제자리 복원은 **한 번도 실행된 적이 없다**(리허설만) |
| E `S3` | **`[미확인]`** | 자격증명 차단으로 착수 전례 0회 |
| F 롤백 왕복 | **`[미확인]`** | 롤백 실행 전례 0회(`I3 ⑷` 가 열린 이유) ＋ 되돌아오는 배포 약 30분 |
| G terraform apply | **`[미확인]`** | apply 실행 전례 0회(`IS4.md:110`) |
| H 판정 | **약 20분** | 문서 대조뿐 |

⟹ **확정된 것은 B·C·H 뿐(약 55분)이고 나머지는 전부 `[미확인]`이다.**
**총 소요를 하나의 수로 적지 않는다** — 전례가 없는 단계가 넷이다.
