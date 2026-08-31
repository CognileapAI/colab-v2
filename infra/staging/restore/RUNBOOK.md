# staging 제자리 복원 런북 (실행본)

> **설계 근거와 판정은 `dev-package/sessions/R1-RESTORE-DRAFT.md` 에 있다. 여기는 「무엇을 어떤 순서로 치는가」다.**
> 두 문서가 어긋나면 초안이 정본이고, 실물을 점검해 초안을 먼저 고친다(`CLAUDE.md §1`).
>
> ⚠ **리허설을 통과하기 전에는 이 런북을 실사고에 쓰지 않는다.** 통과 여부는 `03-HANDOFF §1` 의 `R-1` 행이 말한다.

---

## 0. 표기 · 준비

| 이름 | 뜻 |
|---|---|
| `$ENVFILE` | 홈의 `0600` staging env 파일 (`--env-file` 이 가리키는 것) |
| `$BK` | 백업 보관처 (`COLAB_BACKUP_DIR` · 기본 = 홈 아래 `colab-v2-backups/staging`) |
| `$OWNER` | 플랫폼/AI **소유자 롤** 이름. 앱 롤이 아니다 |

```
set -a; . "$ENVFILE"; set +a
export COLAB_STAGING_ENV_FILE="$ENVFILE"
export COLAB_RESTORE_CAUSE="<원인을 한 줄로. 비면 P9 가 RED 다>"
```

**모든 경로는 레포 상대 또는 `~` 기준이다.** 문서에 절대경로를 적지 않는다(`CLAUDE.md §5`).

### 0.1 이번 릴리스의 **공식 복원 수준** — 회차 단위 (2026-08-31 · Ted RULING ㉚ · `PLAN-SoT §9 〈256〉`)

| | |
|---|---|
| **복원 입도** | **하루 1회 회차 단위.** 크론 `30 3 * * *` 이 만든 그 회차로 되돌아간다 |
| **잃을 수 있는 최대 구간** | **정상 운전에서 약 24시간** — 직전 03:30 회차 이후 쌓인 것은 **전량 사라진다** |
| **백업이 조용히 멈춘 경우** | **최악 약 8일.** 자동 감시가 월요 04:10 주 1회뿐이라(`10 4 * * 1`) 발견까지 최대 7일이 더 붙는다 |
| **임의 시점 복구** | **없다.** `archive_mode`·WAL 보관·`recovery_target`·basebackup 의 실물이 **0건**(전수 grep · `〈249〉`-㉯) — `[미확인]` 이 아니라 **없는 것이 확인됐다** |

⛔ **시점 복구(WAL)는 이번 범위 밖이고, `PLAN-SoT §9-㊻` 의 prod 개통 필수 관문 (다) 로 옮겼다.**
prod 는 이 회차 단위 복원만으로 열지 않는다. staging 에서는 위 최대 구간을 **감수하기로 한 것**이지 모르는 것이 아니다.

---

## 1. 사전조건 — 하나라도 아니면 **시작하지 않는다**

> ⭑ **`preflight.sh` 의 합격 성질 (2026-08-31 확정 · Ted RULING ㉙-⑶ · `PLAN-SoT §9 〈255〉`)**
> **「입력을 다 주면 GREEN 이 된다.」** RED 의 사유가 **입력 부재(P6 환경 미source · P7 복원 직전 백업 미지목 · P8 `--record-digests` 미지정)**
> 와 **의도된 fail-closed(P9 `COLAB_RESTORE_CAUSE` 빈 값)** 뿐일 때만 정상이다.
> **그 밖의 사유가 하나라도 있으면 결함이다 — 「리허설이라 원래 RED」로 넘기지 않는다.**
> ／ 종전 문면 ~~「리허설 경로에서 GREEN 이 못 되는 것은 의도다」~~ — 이 문면은 **새 결함을 의도로 흡수했고**,
> 실제로 `P5-b`(산출물 회차 짝 깨짐)가 그렇게 8일을 숨었다(`〈207〉`-㉲). 자동 강제 = `selftest-restore.sh`.


```
infra/staging/backup/backup-full.sh                  # P7 · 되돌림의 되돌림 재료
export COLAB_RESTORE_PRE_BACKUP="$BK/platform-<방금 stamp>.sql.gz"
infra/staging/restore/preflight.sh --record-digests /tmp/pre-digests.tsv
```

`preflight.sh` 가 P1~P9 를 센다. 각 항목의 뜻은 초안 `§4.0`.

- **P3 이 `--skip-age` 를 붙인다** — 사고 복원은 옛 산출물을 쓴다. **C6·V7 을 없애는 것이 아니라 이 경로에서만 뺀다.**
- **P4 `sha256` 대조 · P5-b 볼륨↔원장 짝 확인이 기구화됐다** — 손으로 채우던 자리다(초안 `§6` #5).
- **P8 이 찍은 `/tmp/pre-digests.tsv` 를 잃어버리면 `§4.6-④` 를 못 잰다.** 다른 창에 남긴다.
- **P9 는 사람만 채울 수 있다.** 원인 미상인 채 복원하면 같은 손상이 다시 온다.

> ⚠⚠ **완전 복원의 실효 창은 볼륨 보존 3일이다. 그보다 오래된 원장 덤프의 복원은 파일 결손을 전제로 한다.**
> 원장 덤프는 14일(`COLAB_BACKUP_RETENTION_DAYS`) 남고 볼륨 아카이브는 3일(`COLAB_VOLBACKUP_RETENTION_DAYS`)만 남아
> **4~14일 된 덤프에는 짝이 되는 볼륨이 없다.** 그리고 **오늘의 볼륨은 옛 원장의 상위집합이 아니다** —
> `storage_key` 는 추가만 되는 것이 아니라 **이동·재작성된다**(`app/routes/ingestion.py` 의 `createDataset` 접수분 이관 ·
> `attachUploadGridFiles` · `replaceDatasetGridFile` 의 옛 키 폐기). 옛 원장이 가리키는 키가 오늘의 볼륨에는 **이미 옮겨져 없다.**
> **10일 된 덤프를 최신 볼륨에 대고 복원하면 `#20` 실패 계열이 재현된다** — 원장이 존재하지 않는 키를 가리킨다.
> 그 창 밖의 복원은 **하지 않는 것이 아니라, 결손을 알고 하는 것이다.** P5-b 짝 확인이 RED 를 낸다.

---

## 2. 정지 — 쓰는 쪽부터, DB 는 마지막

```
docker compose -f infra/staging/compose.i2.yml --env-file $ENVFILE stop \
  frontend nginx core-api pipeline-worker viz-render ai-service
```

- **`pg` 를 세우지 않는다.** 세우면 되돌릴 대상이 사라진다 — 커넥션만 없애면 된다.
- **`cloudflared` 를 건드리지 않는다.** 터널·DNS 는 어느 쪽에서도 손대지 않는다.
- 확인 ① `docker ps --filter name=colab_v2_staging` 에 `pg` · `cloudflared` **둘만** 남는다.
- 확인 ② 잔여 커넥션 0 — `restore-db.sh` 가 이것을 **문 ③** 으로 다시 센다. 0 이 아니면 시작하지 않는다.

---

## 3. 복원 — 비밀 → 원장 → 볼륨

### 3.1 비밀 파일 (필요한 경우에만 · 초안 `§7`)

- **제자리 덮어쓰기만. `mv` 금지** — 파일 바인드는 inode 에 붙어 옛 파일을 계속 읽는다.
- 덮어쓰기 **전에** 같은 디렉터리에 `.bak-<stamp>`(`0600`) 사본을 만든다. 안 만들면 옛 값이 어디에도 안 남는다.
- 권한 `0600` · 소유자 uid `10001` 재확인.
- 절차의 정본은 초안 `§7.2` 다 — env 키 목록도 거기 있다.

### 3.2 원장 둘 — **반드시 둘 다**

```
infra/staging/restore/restore-db.sh --db colab_platform --owner $OWNER \
  --dump "$BK/platform-<stamp>.sql.gz" --yes-drop-schema
infra/staging/restore/restore-db.sh --db colab_ai --owner $OWNER \
  --dump "$BK/ai-<stamp>.sql.gz" --yes-drop-schema
```

⚠ **한쪽만 되돌리면 원장의 데이터셋과 사전이 다른 세대가 된다. 지난 사고가 정확히 `ai` 쪽이었다.**

문 셋(`--yes-drop-schema` · `COLAB_RESTORE_PRE_BACKUP` · 커넥션 0)이 전부 서야 한 글자라도 쓴다.
`DROP SCHEMA public CASCADE` 는 되돌릴 수 없다.

### 3.3 볼륨 — **원장보다 뒤**

```
infra/staging/restore/restore-volume.sh --volume uploads \
  --archive "$BK/vol-uploads-<stamp>.tar.gz" --yes-overwrite-volume
infra/staging/restore/restore-volume.sh --volume previews \
  --archive "$BK/vol-previews-<stamp>.tar.gz" --yes-overwrite-volume
```

- 원장이 파일 행의 정본이고 볼륨은 그 행이 가리키는 바이트다.
- **덮어쓰기이지 동기화가 아니다** — 아카이브에 없는 파일을 지우지 않는다. 고아 바이트는 **정상**이다(초안 `§4.4-㈏`).
- 풀고 나서 `chown -R 10001:10001` 을 한 번 더 한다(스크립트가 안에서 한다).
- 되돌린 결과를 **매니페스트 전건 sha256** 으로 센다 — 크기만 보면 내용이 뒤바뀐 복원이 통과한다.

> **`previews` 를 「재생성 가능」으로 취급하지 않는다.** 지금 재생성 수단이 없다 — 아래 §6.

---

## 4. 기동

```
docker compose -f infra/staging/compose.i2.yml --env-file $ENVFILE up -d
```

- **`-f compose.i2.yml` 을 확인한다.** 빼면 되살리는 명령이 아니라 `rollback.sh` 와 같은 일을 하고, 그러고도 루트 헬스는 200 이다.
- **`--build` 를 붙이지 않는다.** 붙이면 §5-④ 의 digest 대조가 「복원 전과 같은가」에서 「방금 빌드한 것과 같은가」로 바뀌어 **오라클이 사라진다.**
- 컨테이너 **8개**가 healthy 가 될 때까지 기다린다 — **여기까지는 아직 검증이 아니다.**

---

## 5. 검증 — 헬스가 아니라 실측

```
infra/staging/restore/verify-restored.sh \
  --platform-dump "$BK/platform-<stamp>.sql.gz" \
  --ai-dump       "$BK/ai-<stamp>.sql.gz" \
  --owner "$OWNER" --pre-digests /tmp/pre-digests.tsv \
  --base-url https://www.colab-hydro.com
```

⭑⭑ **기대치는 짝 덤프에서 읽는다. 상수를 박지 않는다.**
「데이터셋 12 · 계보 간선 6 · 파일 129」는 **그 회차의 기대치**이지 상수가 아니다 —
여러 문서가 계보 간선을 「5」로 적고 있었고 실측은 6 이었다(`〈159〉`).
`expectations.sh` 가 되돌린 덤프를 읽어 그 회차의 값을 만든다. **숫자를 손으로 옮겨 적지 않는다.**

| # | 항목 | 어디서 |
|---|---|---|
| ① ② ⑥ | 데이터셋 · 계보 간선 · 파일 원장 | 스크립트(짝 덤프 기준) |
| ③ | 사전 3종 ＋ 개념 그래프 2표 | 스크립트(짝 덤프 기준) |
| ③-보 | **읽는 경로** — `POST /searches` 정문 1회 | **손으로.** `_UnavailableDictionaries` 는 검색 시점에야 터진다 |
| ④ | 이미지 digest | 스크립트 — **`dev-package/reference/IMAGE-DIGESTS.md` 를 읽는다.** ＋ P8 기록과 대조 |
| ⑤ | 권한·RLS | **손으로.** 앱 롤로 붙어 **양성·음성 둘 다** |
| ⑦ | 헬스 6종 | 스크립트. **루트 하나만 보지 않는다** |

**판정 — ①~⑤ 가 전부 통과해야 복원 성공이다.** 하나라도 어긋나면 §7.

---

## 6. `previews` — 「재생성 가능」이 지금은 거짓이다

- 초안 `§2` #4 가 `previews` 를 「재생성 가능하지만 재생성이 원본에 의존한다」로 적었다.
- **그보다 더 나쁘다 — 재생성 수단 자체가 아직 없다.** 미리보기 3층을 다시 그리는 일은
  가공(`viz-render` 렌더 재실행)에 걸려 있고 그 기구는 **stage 2 범위**다(`CLAUDE.md §0` stage 표).
- 그래서 `previews` 를 **백업 대상에 넣는다.** 값이 싸고(정적 자산), 「나중에 다시 그리면 된다」가
  지금 실행 가능한 문장이 아니기 때문이다.
- ⚠ **stage 2 에서 재생성 수단이 서면 이 판단을 다시 잰다** — 그때는 보존을 더 짧게 가져갈 수 있다.

---

## 7. 되돌림의 되돌림

- 재료 = **P7 에서 뜬 복원 직전 백업 하나뿐.**
- 절차 = §2 → §3.2 → §4 를 **P7 산출물을 대상으로** 한 번 더. 새 절차가 아니다.
- ⚠ **비밀 파일은 되돌아가지 않는다** — `.bak-<stamp>` 를 안 만들었으면 옛 값이 어디에도 없다.
- ⚠ **볼륨은 「지우지 않는」 복원이라 되돌림이 부분적이다** — 덮어쓴 파일은 P7 회차의 아카이브로만 되돌아간다.
- **되돌림의 되돌림이 실패하면 그 자리는 인프라 사고다.** 조립하지 말고 멈추고 보고한다(`CLAUDE.md §4`).

---

## 8. 리허설

`REHEARSAL.md` 를 본다. **리허설은 살아 있는 staging 을 읽기만 하고 일회용에만 쓴다** — 어떤 파괴적 단계보다 먼저 돌아도 안전하다.

---

## 9. 볼륨 백업이 정지해 있을 때 — **복원 재료가 없다** (2026-08-27 · `PLAN-SoT §9 〈171〉-㉱`)

**이 절은 복원 절차가 아니라 그 앞에 오는 것이다.** 복원 재료는 「최신 원장 덤프 ＋ 그 짝 볼륨 아카이브」인데,
볼륨 백업은 **선다.** 서면 아카이브가 아예 안 생기고, 보존 규칙이 **가장 최신 1개는 안 지우므로**
보관처에는 **옛 아카이브가 남아 있다.** 그 상태로 `§3.3` 을 들어가면 **파일만 며칠 과거로 되돌린다.**

**정지의 조건.** 볼륨 트리에 **비밀 모양 파일**이 있으면 `backup-volume.sh` 가 그 볼륨을 뜨지 않는다
(`〈170〉-㉰` · Ted 판정 「지우고, 생기지 않게 막는다」). 조용히 빼면 원장과 어긋나 오라클이
**거짓 RED** 를 내고 사람이 그 RED 를 「원래 그렇다」로 읽는다 — 그래서 **제외가 아니라 실패**다.
⚠ 볼륨 쪽 판정기는 **모양만** 본다(`secret_shaped_volume`) — `station_token_map.csv` 같은 연구 데이터
이름으로는 서지 않는다. 근거는 `../backup/README.md` 「볼륨 백업이 정지했을 때」.

**조작자가 보는 것.**

| 어디 | 무엇 |
|---|---|
| `staging-backup.log` | `⛔ <볼륨 안 상대경로>` (이름과 건수만 · **값은 안 찍는다**) |
| `BACKUP-FAILED.txt` | 실패 표식. **다음 성공에서만** 사라진다 |
| `latest-check.sh` (월 04:10) | **표식을 읽어 RED** ＋ 해당 볼륨의 `V7 신선도` RED |

**푸는 순서.**

1. `latest-check.sh` 를 돌려 지금 서 있는지 되묻는다. 「야간 실행 표식」 블록이 나오면 서 있는 것이다.
2. 로그에서 `⛔` 줄의 파일 이름을 찾아 **볼륨에서 치운다.** 진짜 비밀이면 지우고, 어떻게 들어갔는지 막는다.
3. `../backup/backup-full.sh` — **원장 덤프부터 다시 뜬다.** 짝이 새로 필요하기 때문이다.
4. 표식이 사라지고 `latest-check.sh` 가 GREEN 이 된 뒤에 복원을 시작한다.

⚠ **정지 상태에서 복원을 강행하지 않는다.** 원장은 최신, 볼륨은 며칠 전 — `§5` 검증이 파일 대조에서
RED 를 낼 것이고, 그때는 되돌릴 재료(`§7`)를 이미 써 버린 뒤다.
⚠ **예외 목록·유예로 정지를 푸는 것은 금지다.** 그 완화가 곧 「빠진 파일을 못 보는 가드」다.
