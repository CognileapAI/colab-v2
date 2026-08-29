# 시드·픽스처의 계보 출처 레이블 이행 — `infra/staging/**`

**회차** 2026-08-29 · 브랜치 `seed-labels`(base `origin/main` = `12063d7`)
**배경** `PLAN-SoT §9 〈205〉`-⑤-ⓒ · `⑧-ⓐ` 가 알려진 미완으로 남긴 것. 직전 회차 지시가 `infra/**` 무접촉을 못 박아 손대지 못했다.

## 1. 전수 재조사 (`grep -rn` · `.git`·`node_modules`·`.venv` 제외)

옛 값 두 종(`AI 제안을 사람이 확인` · `사람이 직접 연결`) 전체 출현 = **13 파일**.

### 고친 것 — 다시 실행되면 죽는 것 (4 파일 · 9 회)

| 파일 | 회 | 넣은 값 | 근거 |
|---|---|---|---|
| `infra/staging/load-seed.py:211` | 1 | `manual` | `createDataset` 의 `lineageParents[].origin` 기본값. 등록 API 가 `("ai","manual")` 만 받는다(`routes/ingestion.py:369`). 시드는 사람이 매니페스트에 적은 부모를 그대로 옮긴다 — AI 제안 확인 경로가 아니다 |
| `infra/staging/load-seed-test.py:204` | 1 | `manual` | 위 로더의 시험 매니페스트. 로더가 실제로 싣는 값과 같아야 한다 |
| `infra/staging/manifest-s2.json` | 5 | `manual` | 실적재 매니페스트 5 부모 전부. 사람이 저작한 계보다 |
| `infra/staging/reseed-fixture-d345.sql:60` | 1 | `manual` | `d4_lineage_edge` 직접 INSERT. `confirmed_by_account_id`·`confirmed_at` 이 채워진 사람 확인 간선이고, 픽스처 정본 `services/core-api/tests/fixtures/seed.sql`(직전 회차가 `manual` 로 이미 옮김)의 D4 블록을 값 그대로 옮긴 파일이다 |

**`processed` 는 넣지 않았다** — 만드는 경로가 없다(`〈205〉`-⑧-ⓑ). 등록 API 도 거절한다.
**`ai` 를 넣은 자리 0** — 네 파일의 옛 값은 전부 `사람이 직접 연결` 이었다. `AI 제안을 사람이 확인` 은 `infra/**` 에 **0 회**.

### 일부러 남긴 것 (9 파일)

- **이력 문서 6** — `sessions/D2.md` · `sessions/LINEAGE-LEVEL.md`(3회) · `sessions/R1-REHEARSAL-01.md` · `sessions/S2b-DATASET-DESCRIPTIONS.md`(2회) · `reports/p0-core-api-spec-20260823.md` · `PLAN-SoT §9`(〈198〉·〈205〉 의 실측 축자) · `SEED-DATA.md`(개정 표시 안의 옛 값). 그때의 실측이라 고치지 않는다.
- **`db/platform/versions/0001_p0_platform.py:321`** — 적용된 마이그레이션은 불변. 차분은 `0008` 이 든다.
- **`db/platform/versions/0008_lineage_origin_labels.py`** — 이행 마이그레이션 자신. 옛 값이 `UPDATE ... WHERE origin = '…'` 의 좌변으로 필요하다.
- **`services/core-api/tests/test_lineage_origin_labels.py`** — `OLD_VALUES` 상수. 옛 값이 **거절되는지**를 시험한다.

## 2. 증명 — 일회용 postgres

`docker run -d --rm --tmpfs /pgdata --env PGDATA=/pgdata/db postgres:16` · **호스트 포트 미공개** · `--network container:` 로만 접속 · 종료 후 컨테이너·이미지 제거. 운영 스택 `colab_v2_staging_*` 무접촉(전·후 8 컨테이너 그대로).

마이그레이션 = `infra/staging/migrator/Dockerfile` 로 구운 러너로 `upgrade head`.

```
current → 0008_lineage_origin_labels (head)
CHECK ((origin = ANY (ARRAY['ai'::text, 'manual'::text, 'processed'::text])))
```

선행 = 픽스처 정본의 D1·D2 블록(1~36 행)만 적재(FK 충족용).

### ① 고치기 전 (`git show 12063d7:infra/staging/reseed-fixture-d345.sql`) — **죽는다**

```
BEGIN
DO
INSERT 0 3
INSERT 0 3
INSERT 0 3
INSERT 0 4
psql:<stdin>:61: ERROR:  new row for relation "d4_lineage_edge" violates check constraint "d4_lineage_edge_origin_check"
DETAIL:  Failing row contains (000000000000000000000EDGA1, 0000000000000000000000000A, 0000000000000000000000DSA2, 0000000000000000000000DSA1, 주입력, 역거리가중 격자화, 사람이 직접 연결, 00000000000000000000000AP1, 2026-02-03 00:00:00+00).
-- 계수: d3_dataset=0 / d4_lineage_edge=0   (트랜잭션 통째 롤백)
```

### ② 고친 뒤 — **돈다**

```
BEGIN
DO
INSERT 0 3
INSERT 0 3
INSERT 0 3
INSERT 0 4
INSERT 0 1
COMMIT
-- 계수·값: d3_dataset=3 / d4_lineage_edge=1 / origin=manual
```

### ③ 로더 두 파일

- `python3 infra/staging/load-seed-test.py` → **`Ran 17 tests in 12.653s` / `OK`**(가짜 API 서버 상대. 계보 부모 경로 포함)
- `infra/staging/load-seed.py` 자체는 **못 돌렸다** — 살아 있는 core-api 와 원천 데이터 루트(`.nc`·GeoTIFF 실파일)를 요구한다. 돌리려면 ⑴ core-api ⑵ 매니페스트가 가리키는 원천 파일 트리 ⑶ 적재 자격증명이 있어야 한다. 대신 `load-seed-test.py` 17 시험이 같은 코드경로를 태우고, `manifest-s2.json` 의 `origin` 분포를 등록 API 허용집합과 대조했다 — **`{'manual': 5}` · 허용집합 밖 0**.

## 3. 잔존 계수

```
$ grep -rc '사람이 직접 연결' infra/staging/{load-seed.py,load-seed-test.py,manifest-s2.json,reseed-fixture-d345.sql}
load-seed.py:0  load-seed-test.py:0  manifest-s2.json:0  reseed-fixture-d345.sql:0
$ grep -rn '사람이 직접 연결\|AI 제안을 사람이 확인' infra/
(출력 없음)
```

**다시 실행되는 파일의 옛 값 = 0 건.**

## 4. 이번에 세지 않은 축

- **staging 실재시드는 돌리지 않았다** — 운영 스택 무접촉이 경계였다. `reseed-fixture-d345.sh` 는 대상 8표 0행을 선행 조건으로 요구하므로, 실행 자리는 그 조건이 성립하는 회차다.
- `load-seed.py` 실행 증명 → `[미확인]`(위 ③ 의 세 조건이 갖춰지는 회차에서 푼다).
