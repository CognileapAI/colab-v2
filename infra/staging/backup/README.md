# infra/staging/backup — staging 백업 체계

> **지금 백업 대상이 붙어 있지 않다.** staging 에는 데이터 저장소가 없다(`../README.md`).
> 그래서 이 디렉터리는 **기구(機構)와 그 실증**이다. postgres 가 I2 로 올라오면
> 설정 한 줄(`COLAB_BACKUP_TARGET=postgres`)로 붙는다 — 다시 쓰는 일이 아니다.

## 왜 이렇게 생겼나

2026-07-11 ~ 08-17, PoC 백업은 **8주 내내 20바이트 빈 gzip 을 성공으로 기록**했다
(`dev-package/DEPLOY-CURRENT.md §8`). 원인 셋을 그대로 반대로 세운 것이 이 구조다.

| 사건의 원인 | 여기서의 대응 |
|---|---|
| ① 크론이 죽은 트리를 가리켰다 | 대상을 설정으로 **명시**한다. 대상이 없으면 `exit 78` — 조용한 성공이 없다 |
| ② 리다이렉션이 pg_dump 보다 먼저 파일을 만들었다 | 임시파일에 받고 `PIPESTATUS[0]` 확인. 실패 시 최종 경로에 **아무것도 남기지 않는다** |
| ③ 가드가 크기·`gzip -t` 만 봤다 | `verify-artifact.sh` 가 **CREATE TABLE 수 · 데이터 행 수 · 신선도**까지 본다 |

성공 신호가 "명령이 0 으로 끝났다" 인 백업은 백업이 아니다.

## 파일

| 파일 | 하는 일 |
|---|---|
| `backup.sh` | 1회 백업. 검사 통과분만 최종본이 된다. 보존 정리 포함(최신 1개는 절대 안 지운다) |
| `verify-artifact.sh` | 산출물 검사 C1~C6. **fail-closed 의 본체** |
| `verify-restore.sh` | 복원 **결과** 검사 — 테이블 수 · 테이블별 행 수 · 총 행 수 |
| `roundtrip.sh` | 백업→파괴→복원 왕복 실증(리허설 인스턴스) |
| `selftest.sh` | fixture 10건이 전부 RED 임을 강제. 하나라도 GREEN 이면 셀프테스트가 실패한다 |
| `latest-check.sh` | 최신 산출물 재검사. 산출물이 **없는 것도 실패**다 |
| `schedule.crontab` · `install-schedule.sh` | 스케줄 선언과 설치. 경로는 실행 시점에 결정한다(①의 재발 방지) |
| `config.example.env` | 설정 예시. 비밀 없음 |
| `seed.sql` · `count-query.sql` · `content-digest.sql` · `expected-counts.tsv` | 리허설용. **staging 실데이터가 아니다** |

## 설정과 보관처 — 레포에 넣지 않는 것

- 설정 실값: 홈의 `.colab-v2-staging-backup.env` (권한 `0600`). `CF_TUNNEL_TOKEN` 과 같은 관행이다.
- 산출물: 기본 보관처는 **홈 아래 `colab-v2-backups/staging/`** — **레포 밖**이다.
  백업을 레포에 쓰면 git 이 데이터 저장소가 된다. 하지 않는다.

## 검사 항목 (verify-artifact.sh)

| | 검사 | 무엇을 잡나 |
|---|---|---|
| C1 | 존재 · 1KiB 이상 | 0바이트 · 20바이트 빈 gzip |
| C2 | `gzip -t` | 절단·손상 |
| C3 | 해제 후 바이트 > 0 | **사건의 실물** — 압축은 멀쩡한데 알맹이가 0 |
| C4 | `CREATE TABLE` >= 20 | 스키마 없음 · 덤프 중간 절단 |
| C5 | 데이터 행 >= 1 | 구조만 있고 내용이 없는 덤프 |
| C6 | 신선도 <= 1500분 | **옛 성공본이 오늘의 백업으로 오독되는 것** |

## 실행

```bash
./selftest.sh          # fail-closed 증명 (docker 필요 — F8 이 실제 postgres 를 쓴다)
./roundtrip.sh         # 왕복 실증 (일회용 d1_* 컨테이너를 만들고 지운다)
./backup.sh            # 1회 백업 — 대상이 붙기 전에는 exit 78
./verify-artifact.sh <파일.sql.gz>
./install-schedule.sh show | install | remove
```

리허설 컨테이너는 `d1_` 접두사이고 **호스트 포트를 열지 않으며** PGDATA 를 tmpfs 에 둔다.
끝나면 지운다. 살아 있는 staging 컨테이너(`colab_v2_staging_*`)는 건드리지 않는다.

## I2 뒤에 붙이는 절차

1. 홈의 설정 파일에서 `COLAB_BACKUP_TARGET=postgres` 로 바꾸고
   `COLAB_BACKUP_PG_CONTAINER` · `_DB` · `_USER` 를 채운다.
2. `./backup.sh` 1회 → GREEN 확인.
3. `./install-schedule.sh install` — **여기서 처음 스케줄을 건다.**
   대상이 없는 동안 걸어 두면 매일 실패 메일이 쌓이고, 그 알람 피로가 8주 침묵의 메커니즘이었다
   (`DEPLOY-CURRENT.md §9`).
4. `./roundtrip.sh` 를 실데이터 규모에서 한 번 더 — 복원 시간이 실측된다.

## 프로파일 — 두 체인은 두 백업이다 (2026-08-23)

`COLAB_BACKUP_PROFILES="platform ai"`. 산출물 이름은 `<프로파일>-<타임스탬프>.sql.gz` 이고,
프로파일마다 합격선(`_MIN_TABLES_<p>` · `_MIN_ROWS_<p>`)이 따로다.
**한쪽만 백업된 상태는 성공이 아니다** — `selftest.sh` 의 F9 가 그것을 fixture 로 못 박는다.

## 스케줄이 실패했을 때 어디에 보이는가

크론은 `run-scheduled.sh` 를 거쳐 실행된다. 실패하면 세 자리에 남는다.

| 자리 | 무엇 |
|---|---|
| `staging-backup.log` | `!!! <스크립트> 실패 (exit N)` 한 줄 |
| `BACKUP-FAILED.txt` | 실패 표식. **다음 성공에서만 사라진다** |
| `LAST-SUCCESS.txt` | 마지막 성공 시각. 크론이 아예 안 돈 경우를 이것으로 잡는다 |

여기에 더해 매주 월 04:10 `latest-check.sh` 가 최신 산출물의 **신선도(C6, 25시간)** 를 다시 묻는다.
백업이 조용히 멈추면 늦어도 그 주에 RED 가 된다.

**정직하게 적어 둔다 — 이 셋은 전부 "가서 봐야 보이는" 자리다.** push 알림 채널(메일·메신저)은
아직 없다(`§5-5`). 그것이 붙기 전까지 "실패했는데 아무도 모르는" 창은 최대 1주다.
