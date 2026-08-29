# R3 · lane1 — 측정 회차 (schema-diff · 프런트엔드 시험 · 백업 요약줄 대상 0건 가드)

측정 시각 2026-08-30 · 브랜치 `wt/lane1-measure` (base `main` = 76e6ed5) · 병합 0건 · push 0건.
운영 스택(`colab_v2_staging_*`) 무접촉 — 컨테이너 생성·정지·재기동 0건, 운영 DB 접속 0건.

---

## 1. `schema-diff` — 적용 DB 를 대 놓고 실측했다

### 무엇을 대 놓았나

- 일회용 postgres 1대(`--rm` · tmpfs `PGDATA` · **호스트 포트 미공개** · 전용 도커 네트워크)를 세우고
  DB 두 개(`applied_platform` · `applied_ai`)를 만들었다.
- 각 체인을 **마이그레이션 러너 이미지**(`colab-v2/migrator:i2`)로 `alembic upgrade head` 했다.
  체인 디렉터리는 `:ro` 로 마운트했다. `db/platform` 8 리비전 · `db/ai` 5 리비전.
- 게이트의 일회용 컨테이너를 같은 네트워크에 붙여(`COLAB_PG_NETWORK`) 체인별 URL 을 넘겼다.

실측 테이블 수 — `applied_platform` **23** (`alembic_version_platform` 포함) · `applied_ai` **6** (`alembic_version_ai` 포함).

### 결과

```
── db/platform ── db/platform green — 드리프트 없음.
── db/ai ──       db/ai green — 드리프트 없음.
schema-diff green — 두 체인 각각 선언 = 적용.
```

### ⚠ 이 green 이 말하는 것과 말하지 않는 것

- **말하는 것** — `db/<체인>/schema.sql`(선언 정본)과 `db/<체인>/versions/*.py`(마이그레이션 체인)의
  head 결과가 **정규화 후 한 줄도 다르지 않다.** 두 산출 경로가 갈라져 있지 않다는 사실이다.
  `db/<체인>/env.py` 가 autogenerate 를 쓰지 않으므로 이 일치는 자동으로 보장되는 것이 아니다 — 실측값이다.
- **말하지 않는 것** — **살아 있는 staging 의 적용 스키마**와의 대조가 아니다. 이번 회차의 「적용 DB」는
  방금 만든 일회용 인스턴스다. staging 실물과의 대조는 별개 축이고, 마지막 실측은
  **2026-08-27**(두 체인 다 드리프트 0 · `PLAN-SoT §9 〈172〉-㉴`)이다.
- 따라서 **드리프트는 두 축 어디에서도 발견되지 않았다.** 다만 이번 실행이 재는 축은 선언↔마이그레이션이고,
  staging 축의 값은 이번에 새로 재지 않았다 — 그 값은 `[미확인 · 2026-08-27 이후]` 다.
  푸는 방법 = 소유자 접속 파일이 있는 자리에서 `COLAB_PG_NETWORK` 를 staging 컴포즈 네트워크로 두고
  체인별 URL 을 staging 으로 지정해 같은 게이트를 돌린다(적용 DB 는 `pg_dump --schema-only` 읽기만 한다).
- 게이트의 검사 범위·정규화 규칙·판정 기준은 **한 글자도 고치지 않았다.**

### 재현 (값은 환경변수로만 넘긴다 — 문서에 접속 문자열을 적지 않는다)

```
docker network create colab_v2_lane1_net
docker run -d --rm --name colab_v2_lane1_applied --network colab_v2_lane1_net \
  --tmpfs /pgdata:uid=70,gid=70 -e PGDATA=/pgdata/db \
  -e POSTGRES_PASSWORD=… -e POSTGRES_HOST_AUTH_METHOD=trust postgres:16-alpine
docker exec … createdb -U postgres applied_platform ; … applied_ai
docker run --rm --network colab_v2_lane1_net -v "$PWD/db/platform:/chain:ro" \
  -e COLAB_PLATFORM_DB_URL=… colab-v2/migrator:i2 upgrade head        # ai 는 COLAB_AI_DB_URL
COLAB_PG_NETWORK=colab_v2_lane1_net COLAB_APPLIED_DB_URL_PLATFORM=… COLAB_APPLIED_DB_URL_AI=… \
  ./gates/run.sh schema-diff
```

---

## 2. 프런트엔드 시험 — 277 의 `[미확인]` 을 해소한다

- 측정 명령 = `cd frontend && npm test` (= `vitest run`). 2026-08-30 실측.
- **시험 파일 13 · 시험 277 · 전건 통과 · 실패 0 · 건너뜀 0.** 소요 242.37초.
- 지시문은 `pnpm test` 였으나 **레포에는 `pnpm-lock.yaml` 이 없고 `package-lock.json` 이 있다** —
  패키지 관리자는 npm 이다. 값이 갈릴 수 있는 자리이므로 실행한 명령을 그대로 적는다.
- 따라서 **277 은 이제 실측값**이다. 세는 단위 = vitest 의 개별 시험 건수, 시점 = 2026-08-30.

---

## 3. 백업 검사기 요약줄 — 검사 대상 0건 가드 (독립 회차)

### 결함

`infra/staging/backup/lib.sh` 의 요약줄 정본 `verdict()` 이 `FAILED` 만 봤다. 통과도 실패도
명시 면제도 **하나도 없는 상태**(검사가 한 건도 돌지 않은 상태)가 GREEN 으로 찍혔다.
통과 건수를 아무도 세지 않았기 때문에 「전건 통과」와 「한 건도 안 봄」이 구분되지 않았다.

### 고친 방법 — 세 상태

| 상태 | 판정 | 요약줄 |
|---|---|---|
| 검사 대상 있음 (`PASSED` > 0) | 검사한다 | 통과 건수를 적는다 |
| 명시 면제만 있음 (`SKIPPED` > 0 · `PASSED` = 0) | 통과 | **「검사 0건」과 SKIP 건수**를 적는다 |
| 아무것도 선언·발견되지 않음 (0/0/0) | **RED** | 대상 0건은 통과가 아니다 |

`pass()` 가 `PASSED` 를 세게 하고, 소비처 셋(`verify-artifact.sh`·`verify-restore.sh`·
`verify-volume-artifact.sh`)에서 `PASSED=0` 을 초기화했다. 판정은 여전히 `verdict()` **한 곳**에 있다.

### 요약줄 before / after (실측)

| 경우 | before | after |
|---|---|---|
| 통과·실패·SKIP 전부 0 | `결과: GREEN (SKIP 0 — 모든 항목이 실제로 돌았다)` · exit 0 | `결과: RED (검사 0건 — 통과·실패·명시 면제가 하나도 없다. …)` · **exit 1** |
| 명시 면제 1건만 | `결과: GREEN (전부 통과 · **승인된 SKIP 1건** …)` · exit 0 | `결과: GREEN (**검사 0건 · 승인된 SKIP 1건** — 실제로 본 항목이 없다 …)` · exit 0 |
| 통과 2건 | `결과: GREEN (SKIP 0 — 모든 항목이 실제로 돌았다)` | `결과: GREEN (통과 2건 · SKIP 0 — 모든 항목이 실제로 돌았다)` |
| 통과 1 · 실패 1 | `결과: RED (실패 1건)` | `결과: RED (실패 1건 · 통과 1건)` |

⭑ **모든 검사기의 요약줄이 통째로 바뀐다.** before 의 문장 「전부 통과」는 통과 건수를 세지 않은 채
쓰던 말이라 그대로 둘 수 없었다. 이것이 이 변경을 독립 회차로 돌린 이유다.

### 실패 픽스처를 먼저 썼다 (red 경로 증명)

`backup/selftest.sh` 에 3건 추가 — F12(대상 0건 → RED) · F12-b(명시 면제만 → GREEN 이되 건수 노출) ·
F12-c(대조군 · 통과 1건 → GREEN). **추가 직후 셋 다 기대와 반대로 나와 셀프테스트가 RED** 였고
(`셀프테스트 RED — 3 건이 fail-closed 가 아니다`), `lib.sh` 를 고친 뒤 GREEN 이 됐다.

### 시험 실측 (2026-08-30)

- `backup/selftest.sh` — **GREEN · 픽스처 16건**(13 → 16)
- `backup/selftest-volume.sh` — **GREEN · 픽스처 24건**
- `restore/selftest-restore.sh` — **GREEN · 픽스처 23건**

---

## 4. 복원 리허설의 프로파일별 최신본 선택 — 결함 아님 (Ted 판정 2026-08-30)

- 지적된 모양 = `infra/staging/backup/restore-rehearsal.sh` 가 프로파일마다 독립으로
  `ls -1t … | head -1` 을 돌려 최신 산출물을 고른다 → 두 프로파일의 산출물이 **같은 회차가 아닐 수 있다.**
- **판정 = 고치지 않는다.** 프로파일은 회차와 **다른 축**이다. `platform` 과 `ai` 는 마이그레이션 체인이
  분리된 별개 DB 이고(`CLAUDE.md §3-3`) 백업도 각자 돈다. 회차로 묶으면 「짝이 맞는 회차가 없다」로
  리허설이 통째로 서고, 그것은 **각 체인의 최신 백업이 실제로 복원되는가**라는 이 스크립트의 목적을 깎는다.
  프로파일을 가로질러 각자의 최신본을 검증하는 것이 의도다.
- **다음 회차가 다시 파지 않도록 그 자리에 주석으로 박았다** — `restore-rehearsal.sh` 의 `ART=` 바로 위.
  이 문서 한 곳에만 두면 스크립트를 읽는 사람이 못 본다.

---

## 4-b. 게이트 실측 (`./gates/run.sh all -j 2` · 2026-08-30)

**green 25 / red 2.** 기준선은 green 26 / red 1(`schema-diff` 단독)이었다.

| 게이트 | -j 2 | 단독 재측 | 사유 |
|---|---|---|---|
| `schema-diff` | **green** | green | 이 회차에 적용 DB 를 대 놓았다(§1). 기준선의 red 가 닫혔다 |
| `db-selftest` | **red** | **green** | 병렬에서만 뒤집혔다. `gates/README.md` 는 이 게이트를 **병렬로 돌리지 않는다**고 적고 있다(e2e 묶음이 한 적용 DB 를 순서대로 훼손해 가며 본다). 판정부가 아니라 배선에서 난 red 로 보이나, **-j 2 에서 실제로 red 였다는 사실은 지우지 않는다** |
| `stage2-markers` | **red** | **red** | `services/pipeline-worker/.venv` 가 이 워크트리에 없다. **환경 부재이므로 검사를 못 돈 것이고, 못 돈 것은 통과가 아니다.** 푸는 방법 = `services/pipeline-worker` 에 venv 를 만들고 `requirements.txt` 를 설치한다 |

⚠ 기준선 표기(`red 1 = schema-diff 만`)와 어긋난 자리가 둘이다. 둘 다 **코드 변경이 만든 것이 아니다** —
이번 회차의 변경은 `infra/staging/backup/**` 뿐이고 게이트 대상에 들어가지 않는다.

---

## 5. 이번에 세지 않은 판단기준 (다음 회차 진입조건)

- staging 실물 적용 스키마 ↔ 선언 스키마 대조 — 마지막 실측 2026-08-27. 이번 회차는 재지 않았다.
- 프런트엔드 시험의 커버리지·타입체크(`npm run typecheck`) — 이번에 세지 않았다.
- `verdict()` 를 쓰지 않는 다른 요약줄(`backup.sh`·`latest-check.sh` 자체 출력)의 대상 0건 형제 — 미조사.

---

## 6. `PLAN-SoT §9` 등재용 초안 (번호는 오케스트레이터가 채운다)

> **〈NNN〉 백업 검사기 요약줄의 검사 대상 0건 가드 · `schema-diff` 체인별 실측 · 프런트엔드 시험 실측** (2026-08-30)
>
> ㉮ `infra/staging/backup/lib.sh` 의 `verdict()` 이 **통과·실패·명시 면제가 전부 0인 상태를 GREEN 으로**
> 찍었다. 통과 건수를 세는 곳이 없어 「전건 통과」와 「한 건도 안 봄」이 같은 문장을 냈다.
> 세 상태로 갈랐다 — 대상 있음 → 검사(통과 건수 노출) · 명시 면제만 → 통과하되 「검사 0건」과 건수 노출 ·
> 0/0/0 → **RED**. `pass()` 가 `PASSED` 를 세고 소비처 셋이 초기화한다. 판정은 `verdict()` 한 곳.
> **모든 검사기의 요약줄 문안이 바뀐다**(before/after 표 = `sessions/R3-LANE1-MEASURE.md §3`).
> 실패 픽스처를 **먼저** 넣어 RED 를 확인한 뒤 고쳤다. 시험 = `backup/selftest.sh` **16건 GREEN**(13 → 16) ·
> `selftest-volume.sh` 24건 GREEN · `restore/selftest-restore.sh` 23건 GREEN.
>
> ㉯ `schema-diff` 의 red 는 결함이 아니라 **적용 DB 미지정**이었다. 두 체인을 일회용 인스턴스에
> `alembic upgrade head` 로 올려(`colab-v2/migrator:i2` · 체인 `:ro` · 포트 미공개 · tmpfs) 체인별 URL 을
> 주고 실측 → **두 체인 다 드리프트 0.** ⚠ **이 축은 선언 ↔ 마이그레이션이다.** 살아 있는 staging 과의
> 대조는 다른 축이고 마지막 실측은 2026-08-27(`〈172〉-㉴`)이다. 게이트의 검사 범위·정규화는 무변경.
>
> ㉰ 프런트엔드 시험 **277** 의 `[미확인]` 해소 — `cd frontend && npm test`(`vitest run`) 2026-08-30 실측 =
> **시험 파일 13 · 시험 277 전건 통과 · 실패 0 · 건너뜀 0.** 레포에 `pnpm-lock.yaml` 은 없다(npm 이 정본).
>
> ㉱ `restore-rehearsal.sh` 의 **프로파일별 독립 최신본 선택은 결함이 아니다**(Ted 판정 2026-08-30) —
> 프로파일은 회차와 다른 축이고 교차 검증이 의도다. 근거를 그 자리 주석에 박았다.
