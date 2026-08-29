# I3-POSTDEPLOY — 첫 실배포 이후 측정

- **측정 시점** 2026-08-29 10:14~10:35 (KST) · DB 계수는 `now()` = `2026-08-29 01:14~01:30 UTC`
- **측정 대상** 릴리스 `30b3e0a7b3f3` (커밋 `30b3e0a7b3f305c9dd6ce79153314e83b7d364c7`)
- **측정 범위** 읽기 전용 + 무해 설계된 `PATCH` 3건(§3). 배포·롤백·컨테이너 조작·DDL·`DELETE`/`UPDATE` **0건**
- **문서 편집·커밋** 이 파일 신설 하나. 다른 문서 무수정

> ⚠ **지시와 실물의 어긋남 1건** — 지시는 「`~/colab-v2-releases/pipeline.log` 에 태그 28건 삭제 목록이 있다」고 했으나
> **그 파일은 존재하지 않는다**(디렉터리 실물 = `LAST-SUCCESS.txt` · `pipeline.lock` · `release-ledger.tsv` 셋).
> `pipeline.log` 는 `run-pipeline.sh` 가 만드는 파일이고(`lib.sh` `pipeline_state_dir()` = `$HOME/colab-v2-releases`),
> **`run-pipeline.sh` 는 한 번도 돌지 않았다.** 삭제 28건은 로그로 확인하지 못했다 → `[미확인]`.
> 대신 **코드와 현재 이미지 실물로 삭제가 일어난 이유를 확정**했다(§5).

---

## 1. 완료 정의 대조 (정본 = `I3.md §6` 15행 / `work-items.yaml` `I3.completion_def`)

| # | 항목 | 판정 | 이번 회차에 실제로 잰 근거 |
|---|---|---|---|
| 1 | 파이프라인 1회 완주 (**사람이 배포 명령을 부르지 않은 채**) | **열림** | `crontab -l` 실측 — 등재된 것은 백업 2건(`run-scheduled.sh backup-full.sh` 03:30 · `latest-check.sh` 월 04:10)과 무관한 크론 2건뿐. **`schedule.crontab`/`install-schedule.sh` 는 설치되지 않았다.** `pipeline.log` 부재로 `run-pipeline.sh` 미실행 확인. 원장의 green 1행은 `deploy.sh` 직접 호출 결과 |
| 2 | staging 배포 green — 헬스 6종 200 + 본문이 단위 이름으로 대답 | **닫힘** | §2 표. 공개 주소 `https://www.colab-hydro.com` 기준 6/6 200 · 본문 일치 |
| 3 | 컨테이너 8/8 `healthy` · `0.0.0.0` 0건 | **닫힘** | `verify-deploy.sh` 실측 — 8건 전부 healthy · 「호스트 노출 — 0.0.0.0 0건」. `docker ps` 의 유일한 호스트 바인딩은 `127.0.0.1:3000->80/tcp`(nginx) |
| 2-b | 배포 판정 = 헬스 6종 + 본문 대조. `deploy.sh` 종료코드가 `dc ps` 가 아닐 것. red 로그 1건 + green 1건 | **부분 — 열림** | 코드 확인: `deploy.sh` ⑪ 이 `verify/verify-deploy.sh` 의 종료코드에 매달린다. **green 실행 1건** = 원장 `2026-08-29T10:08:36 deploy 30b3e0a7b3f3 green`. **red 실행 1건은 `[미확인]`** — 원장의 red 1행(`2026-08-28T21:34:18 · 0a3ea797dbb1`)은 「롤 부트스트랩 실패」로 **헬스 판정 단계에 도달하기 전**이다. 판정기 자체의 red 능력은 §4-2 의 fixture 22건으로 증명되지만, **실배포에서 판정기가 red 를 낸 로그는 아직 없다** |
| 4 | 롤백 왕복 증명 (배포 → 롤백 → 재배포, 각 국면 본문 판정) | **열림 (이번 회차 의도적 미실행)** | 지시대로 롤백을 돌리지 않았다. ⭑ **추가 실측 — 지금은 롤백이 애초에 불가능하다.** `ledger_rollback_target()` 은 원장의 **green `deploy` 행 중 현재 태그를 제외한 최신**을 고르는데, 원장의 green `deploy` 행은 `30b3e0a7b3f3` **하나뿐**이다 → 대상 0건 → `rollback.sh` 가 `die` 한다. 닫으려면 **두 번째 green 릴리스**가 원장에 서야 한다(또는 `--to-tag prev` 를 명시해야 하는데 그건 「직전 릴리스로 갔다」의 증명이 아니다 — 5 참조) |
| 5 | 롤백이 자리표시가 아니라 **직전 릴리스**로 갔음이 태그·원장으로 확인 | **열림** | 4 의 선행 조건 미충족. ⭑ **`:prev` 는 「직전 릴리스」가 아니다** — `deploy.sh` ③ 이 `colab-v2/<n>:i2` 를 그대로 `:prev` 로 태그하고, `:i2` 는 **직전 green 배포의 말미**에만 갱신된다. 이번이 첫 green 배포이므로 현재 `:prev` 는 **원장에 없는 수동 빌드본**(ai-service·core-api·pipeline-worker = 2026-08-27 05:34 · frontend·viz-render = 2026-08-27 03:00 · migrator = 2026-08-23 13:20)을 가리킨다 |
| 6 | 두 체인 head + K2 시드 22행이 그대로 | **닫힘 (배포 후 시점만)** | `verify-chains.sh` — platform `0007_p2_human_written_meta` · ai `0005_k2b_concept_graph_seed`. 시드 = `d9_method_term` 13 + `d9_topic_synonym` 5 + `d9_place_alias` 4 = **22**. ⚠ 완료 정의는 「배포·**롤백·재배포**를 거쳐」를 요구하므로 **4 가 닫히기 전에는 이 항목도 전건 충족이 아니다** |
| 7 | 배포 전 백업이 실제로 걸렸다 (두 프로파일 GREEN) | **닫힘** | 원장 비고 축자 = `배포전백업GREEN 워킹트리변경=0`. `--skip-backup` 경로였다면 `배포전백업SKIP(2건)` 이 남는다(`deploy.sh` ⑤) — 남지 않았다 |
| 8 | 판정기 fail-closed 가 red fixture 로 증명 (죽은 단위 · 자리표시 본문 · 한쪽 체인 미적용) | **닫힘** | `infra/staging/verify/selftest.sh` → `verify selftest: GREEN (22건 전부 기대대로 · red fixture 가 실제로 red 를 냈다)` · `infra/staging/pipeline/selftest.sh` → `pipeline selftest: GREEN (16건 + 판정기 전건 기대대로)` |
| 9 | 승인 없이 prod 타깃이 도는 경로 없음 | **닫힘** | 같은 selftest 의 `F7 prod 타깃 → 거부여야 한다 (조용한 no-op 금지) — PASS [F7] red` · `F9`·`F10`(승인 기록 결손 거부) PASS |
| 10 | 게이트 전 종 green + `selftest` green | **부분 — 열림** | §4. 27종 중 **green 26 · red 1**(`work-item-consistency` — 불일치 12건, 그중 하나가 `I3` 자신의 산문 갈라짐). `schema-diff` 는 이번에 **살아 있는 staging 두 체인에 붙여 green**(드리프트 0) |
| 11 | 작업 전·후 `www.colab-hydro.com/healthz` 200 → 200 · 다른 레인 컨테이너 무접촉 | **부분 — 열림** | 후: 200 실측(§2). 전: **이번 세션에서 못 쟀다** — 원장 `2026-08-28T21:12:21 approve` 행의 「본것=staging 헬스 6종 200」이 배포 전 200 의 유일한 기록이고 배포 직전 시점이 아니다 → 「직전 200」은 `[미확인]`. 무접촉: 이번 세션에서 컨테이너 조작 0건 |
| 12 | DR-4 — 빌드 대상이 커밋 · 떠 있는 이미지 SHA 로 특정 · `deploy.sh:13` 주석이 동작과 일치 | **닫힘** | 태그 = 커밋 앞 12자(`30b3e0a7b3f3` ← `30b3e0a7b3f3...`) · `docker ps` 의 앱 5종 이미지가 전부 `:30b3e0a7b3f3` · 원장 `워킹트리변경=0`. 주석: 현행 머리말은 DR-4 를 **과거형 결함으로** 적고 거짓 단언이 없다 |
| 13 | DR-6 — 앱 5종에 헬스 게이트 · `deploy.sh:16` 주석 정정 | **닫힘** | 판정 15건 = 헬스 6 + 컨테이너 8 + 노출 1, SKIP 0. 주석에 「postgres 만」 류의 거짓 단언 없음 |
| 14 | DR-5 — 태그 보존이 **빌드보다 먼저** · 보존본 ≠ 신규본 이미지 ID | **닫힘 (코드·실물) / 실행 로그는 `[미확인]`** | 코드 순서 = ③ 보존 → ④ 빌드(`deploy.sh` 103~117행). 실물 대조 — `:prev` 와 `:30b3e0a7b3f3` 의 이미지 ID 가 6종 전부 다르다(예: core-api `c08220676167` ≠ `3caec581b0d4`). ⚠ 실행 중 출력된 대조 줄은 `pipeline.log` 부재로 확인 불가 |

**요약 — 닫힘 9 · 열림/부분 6** (1 · 2-b · 4 · 5 · 10 · 11). 6번은 「배포 후 시점만」 닫힘.

---

## 2. 헬스 6종 (2026-08-29 10:16 · 공개 주소 기준 · 축자)

```
/healthz                     -> 200 | ok
/healthz/core-api            -> 200 | {"unit":"core-api","status":"alive","implemented":true}
/healthz/pipeline-worker     -> 200 | {"unit": "pipeline-worker", "status": "alive", "implemented": true}
/healthz/viz-render          -> 200 | {"unit":"viz-render","status":"alive","implemented":true}
/healthz/ai-service          -> 200 | {"unit":"ai-service","status":"alive","implemented":true}
/healthz/frontend            -> 200 | {"unit":"frontend","status":"alive","implemented":true}
```

`verify-deploy.sh` 요약줄 축자:

```
배포 판정: GREEN (통과 15건 · SKIP 0 — 모든 항목이 실제로 돌았다)
```

`verify-chains.sh` 축자:

```
  PASS  [platform] head=0007_p2_human_written_meta (db=colab_platform)
  PASS  [ai] head=0005_k2b_concept_graph_seed (db=colab_ai)
체인 판정: GREEN (통과 2건 · SKIP 0 — 모든 항목이 실제로 돌았다)
```

---

## 3. `403` 2건 — 배포된 API 실측 (`updateDataset` · `updateProject`)

### 3-1. 안전 설계 (먼저 세운 것)

1. **경로 식별자를 존재하지 않는 ULID 로 고정** — `00000000000000000000000000`.
   두 핸들러 모두 쓰기 전에 `dataset_exists` / `project_exists` 를 지나야 하므로, 스위치가 켜져 있더라도 **404 에서 멈추고 아무것도 안 바뀐다.**
2. **본문을 빈 객체 `{}` 로 고정** — 바꿀 값을 하나도 싣지 않는다.
3. 전송 전 **권한 판정이 핸들러의 첫 문장인지 코드로 확인** — `catalog.py:436-437` `_require_upload_edit(db, subject)` · `project.py:85` `if not _can_manage(...)`. 둘 다 본문 검증·존재 확인보다 **앞**이다.
4. 전송 전·후 기준선을 각각 셌다(§4-3 — 전후 동일).

### 3-2. 보낸 것과 받은 것 (축자)

| 자격 | 요청 | 응답 |
|---|---|---|
| staging 주체 등기부에 심긴 **유일한 토큰** (계정 = `프로젝트 생성`·`업로드·편집` 둘 다 **켜짐**) | `PATCH /api/v1/datasets/00000000000000000000000000` · `{}` | `404` · `{"code":"NOT_FOUND","message":"데이터셋을 찾지 못했다."}` |
| 같은 자격 | `PATCH /api/v1/projects/00000000000000000000000000` · `{}` | `404` · `{"code":"NOT_FOUND","message":"프로젝트를 찾지 못했다."}` |
| **자격 없음**(`Authorization` 헤더 없음) | `PATCH /api/v1/datasets/00000000000000000000000000` · `{}` | `401` · `{"code":"UNAUTHORIZED","message":"Authorization: Bearer <토큰> 이 없다."}` |

(토큰·접속 문자열·비밀번호는 이 문서 어디에도 적지 않았고 명령줄·로그에도 값으로 남기지 않았다.)

### 3-3. 판정 — **`403` 은 여전히 `[미확인]`**

- **닫힌 것** — 두 op 이 **배포된 빌드에 실제로 존재하고 라우팅된다**(404/401 이 라우트 내부 판정문이다. 미배포였다면 `404 Not Found` 가 아니라 프런트 SPA 응답이나 `405` 가 났다). 그리고 **무자격 요청은 401 로 막힌다.**
- **닫히지 않은 것** — **권한 스위치가 꺼진 주체가 없다.** 실측:
  - `d2_permission_switch` 8행 — 두 계정(`...A1`, `...HYMETSC`) 모두 `업로드·편집 = t` · `프로젝트 생성 = t`
  - `d2_member_role` 6행 중 4명이 `교수` — `permissions_of()` 가 **역할만 보고 네 스위치를 전부 참으로 내린다**(`d2_access.py:78-79`)
  - 주체 등기부(`COLAB_STAGING_SUBJECTS_FILE`)에 심긴 토큰은 **1개**이고 그 계정의 `GET /api/v1/projects/{id}` 응답이 `"canManage": true`
  - `~/.colab-v2-staging-subjects.tokens.json` 의 3개(`a1-prof`·`a1-res`·`b1-prof`)는 전부 `401 UNAUTHORIZED` — 낡았다
- 따라서 **스위치가 꺼진 자격으로 `PATCH` 를 보낼 수단이 지금 staging 에 없다.** 있는 자격으로 실물 객체에 보내면 **200 이 날 조합**이므로 시도하지 않았다(지시대로).
- **푸는 법(하나)** — 주체 등기부에 **`업로드·편집`·`프로젝트 생성` 이 꺼진 계정**에 묶인 토큰을 1건 더 심고(등기부 파일 쓰기 = 이번 세션 경계 밖 · Ted 판정 자리), 실존 데이터셋·프로젝트에 대해 `PATCH` 를 보내 `403` 을 받는다. 그 계정은 **스위치 행이 `f` 이거나 아예 없는 `연구원`** 이어야 한다(교수는 역할만으로 전부 켜진다).
- 참고 — 코드 수준 red/green 증명은 이미 있다(`X5-403-VERIFY.md` §4 — 훅을 지우면 두 시험이 `200 == 403` 로 실패). **없는 것은 「배포된 실물에서의 403」 하나다.**

---

## 4. 게이트 전 종 재실행

### 4-1. `gates/run.sh all -j 4` (2026-08-29 10:25 · 27종)

```
  green  planning-freshness          green  contract-lint             green  contract-breaking
  green  event-lint                  green  event-breaking            green  seam-consistency
  green  generated-up-to-date        green  import-boundary           green  banned-import
  green  ai-no-lineage-write         green  db-boundary               green  migration-single-head
  green  rls-coverage                green  rls-effect                green  stage2-markers
  green  contract-selftest           green  event-selftest            green  boundary-selftest
  green  db-boundary-selftest        green  rls-effect-selftest       green  seam-consistency-selftest
  green  generated-selftest          green  work-item-selftest        green  stage2-markers-selftest
  red    schema-diff (exit 1)        red    work-item-consistency (exit 1)   red  db-selftest (exit 1)
```

### 4-2. red 3건의 정체 — 두 건은 **환경/호출자 문제였고 해소했다**

| 게이트 | 1차 red 사유 (축자) | 재실행 결과 |
|---|---|---|
| `schema-diff` | `::error::schema-diff red — 적용 DB 가 지정되지 않았다: COLAB_APPLIED_DB_URL_PLATFORM / COLAB_APPLIED_DB_URL_AI` — 원인 ① env 파일의 `*_OWNER_DB_URL_FILE` 이 가리키는 파일이 **uid 10001 소유 `0600`** 이라 실행 사용자(uid 1000)가 못 읽는다 ② 읽어 낸 URL 의 스킴이 **`postgresql+psycopg://`**(SQLAlchemy 방언)이라 `pg_dump` 가 해석하지 못하고 로컬 소켓으로 떨어진다(`FATAL: role "root" does not exist`) | **green** — 스킴을 `postgresql://` 로 정규화하고 `COLAB_PG_NETWORK=colab-v2-staging_default` 를 준 뒤: `db/platform green — 드리프트 없음.` · `db/ai green — 드리프트 없음.` · `schema-diff green — 두 체인 각각 선언 = 적용.` **살아 있는 staging 두 체인에 대해 드리프트 0** (읽기 = `pg_dump --schema-only` 뿐) |
| `db-selftest` | `schema-diff(e2e): 두 체인 모두 선언 = 적용 → red (기대 green) ✗` · `pg_dump: connection to server at "172.17.0.2" ... Operation timed out` — **내가 `all` 실행에 건 `COLAB_PG_NETWORK` 가 일회용 컨테이너의 네트워크를 바꾼 것**이 원인. 게이트의 결함이 아니다 | **green** — 그 변수 없이 재실행: `db-selftest green — DB 게이트 3종 모두 틀린 것을 틀렸다고 말한다 (fail-closed 증명).` |
| `work-item-consistency` | `::error::work-item-consistency — 불일치 12건` (`㈑ I0` 1건 + `㈓ conflict` 11건: `S2b`·`I1`·**`I3`**·`X-2`·`R-1`·`J-1`·`P6`·`S1`·`PA`·`S2`·`2단-BC120`) · 검사 대상 밖 9건 명시 | **red 유지** — 실물 결함이 아니라 **문서 상태 갈라짐**이다. `I3` 자신도 그중 하나(`03-HANDOFF §1 T-I` ⬜ ↔ `WORK-UNITS §10` ⛔ ↔ `§10.2-b` ✅ ↔ `§11` ⬜). **이 회차의 배포 결과를 대장·산문에 반영하면 `I3` 행은 풀린다** |

**계수 (이 회차 · 재실행 반영)** — 게이트 27종: **green 26 · red 1**(`work-item-consistency`). 도구·환경 부재로 **못 돈 게이트 0건**.
배포 판정기 selftest 2종(`verify/selftest.sh` 22건 · `pipeline/selftest.sh` 16건) **전건 green**.

### 4-3. 배포 판정기 selftest 축자 요약

```
verify selftest: GREEN (22건 전부 기대대로 · red fixture 가 실제로 red 를 냈다)
pipeline selftest: GREEN (16건 + 판정기 전건 기대대로)
```

포함된 red fixture — `F7 prod 타깃 → 거부` · `F9`·`F10 승인 기록 결손 거부` · `F12 한쪽 체인 미적용` · `F14`~`F16 프리플라이트 결손` · `F18 값 미출력`.

---

## 5. 배포 전후 기준선 대조

**세는 기준** = `colab_platform` 의 표 행 수를 컨테이너 안 로컬 소켓 `psql` 로 `SELECT COUNT(*)` (읽기 전용).
**세는 시점** = 2026-08-29 01:14:32 UTC (= 10:14 KST · `PATCH` 3건 **전**) 및 01:29:56 UTC (= 10:29 KST · `PATCH` 3건 **후**).

| 축 | 정본 기준선 (2026-08-28 실측 · `PLAN-SoT §9 〈184〉`) | 이번 실측 ①<br>01:14 UTC | 이번 실측 ②<br>01:29 UTC | 대조 |
|---|---|---|---|---|
| 데이터셋 `d3_dataset` | 12 | **12** | **12** | 일치 |
| 파일 — **본체 기준(정본)** `d3_file where kind='본체'` | **123** | **123** | **123** | 일치 |
| 파일 — 저장 전체(병기) `d3_file` | 129 (본체 123 + 기준 격자 6) | **129** (`kind=본체` 123 · `kind=기준 격자 파일` 6) | **129** | 일치 |
| 계보 관계 `d4_lineage_edge` | 6 | **6** | **6** | 일치 |
| 체인 head — platform | `0007_p2_human_written_meta` | 동일 | — | 일치 |
| 체인 head — ai | `0005_k2b_concept_graph_seed` | 동일 | — | 일치 |
| (참고) K2 시드 | 22 (13+5+4) | **22** | — | 일치 |

**어긋난 축 0건.** 배포도, §3 의 `PATCH` 3건도 데이터를 바꾸지 않았다.
⚠ 부수 관측 — `d4_lineage_unknown` = **7 행**(정본 기준선에 축으로 등재돼 있지 않다. 이번 회차 신규 관측값이며 배포 전 값은 `[미확인]`).

---

## 6. 삭제된 이미지 태그 — `COLAB_IMAGE_KEEP` 이 실제로 세는 것

### 6-1. 오케스트레이터 추정의 판정 — **맞다. 다만 한 칸 더 좁다.**

정본 = `infra/staging/pipeline/lib.sh` `image_prune()` (111~137행).

```
IMAGE_KEEP="${COLAB_IMAGE_KEEP:-3}"
ALIAS_TAGS=(prev i2)
image_prune() {
  local keep=("$1" "${ALIAS_TAGS[@]}") ...
  while IFS=$'\t' read -r _ts kind _sha tag ok _note; do
    [ "$kind" = deploy ] || continue; [ "$ok" = green ] || continue; [ -n "$tag" ] || continue
    case " ${keep[*]} " in *" $tag "*) continue ;; esac
    keep+=("$tag")
    [ $(( ${#keep[@]} - ${#ALIAS_TAGS[@]} )) -ge "$IMAGE_KEEP" ] && break
  done < <(tac "$f")
  ...  # keep 에 없는 colab-v2/* 태그를 전부 docker image rm
}
```

- `COLAB_IMAGE_KEEP` 은 **태그 개수가 아니다.** **릴리스 원장(`release-ledger.tsv`)에서 `kind=deploy` 이면서 `판정=green` 인 행의 개수**를 센다.
- 더 좁혀 말하면 — **보존 목록의 상한**이지 하한이 아니다. 원장이 그만큼 없으면 `keep` 은 그만큼만 찬다.
- **`approve` 행과 `red` 행은 세지 않는다.** 원장 3행 중 `approve` 1 · `red` 1 은 `continue` 로 걸러진다.
- 이번 시점의 원장 green `deploy` 행은 **`30b3e0a7b3f3` 단 하나**이고, 그건 이미 `$1`(지금 배포한 태그)로 `keep` 에 들어 있어 루프에서 `continue` 된다.
- 결과적으로 `keep = {30b3e0a7b3f3, prev, i2}` **3개로 확정**되고, `COLAB_IMAGE_KEEP=40` 은 **도달할 수 없는 상한**이라 아무 영향이 없었다. `colab-v2/*` 의 나머지 태그는 전부 삭제 대상이 됐다.

**정정할 것 없음.** 「원장의 릴리스 개수를 세는 것이지 태그 개수가 아니다」는 맞고, 덧붙일 한 줄은 **「그 릴리스는 `deploy`+`green` 행만이고, 지금 원장에는 그런 행이 하나뿐이라 상한 40 은 무의미했다」** 이다.

⚠ 삭제 **28건**이라는 숫자 자체는 이번에 확인하지 못했다 → `[미확인]`(§0 의 `pipeline.log` 부재). 확인 가능한 것은 **결과**뿐이다 — 현재 `colab-v2/*` 태그는 **18개 = 6종 × 3(`30b3e0a7b3f3`·`i2`·`prev`)** 로, 코드가 예측한 집합과 정확히 같다.

### 6-2. `:prev` 가 실제로 가리키는 것 — **직전 릴리스가 아니다**

`deploy.sh` ③(103~117행)은 `colab-v2/<n>:i2` 를 그대로 `:prev` 로 태그한다. `:i2` 는 **green 배포의 말미**(215행 직전)에만 갱신되는 **호환 별칭**이다. 이번이 첫 green 배포였으므로 `:prev` 가 물려받은 `:i2` 는 **원장에 없는 수동 빌드본**이다.

| 단위 | `:30b3e0a7b3f3` (현재 서빙) | `:i2` | `:prev` | `:prev` 의 이미지 생성 시각 |
|---|---|---|---|---|
| core-api | `3caec581b0d4` | `3caec581b0d4` | `c08220676167` | 2026-08-27 05:34:48 |
| ai-service | `0a76bbd3818d` | `0a76bbd3818d` | `18cb90b8ec48` | 2026-08-27 05:34:47 |
| pipeline-worker | `922072578bda` | `922072578bda` | `e4f6c59e8933` | 2026-08-27 05:34:47 |
| viz-render | `c703eac13a72` | `c703eac13a72` | `6f7e69c632c0` | 2026-08-27 03:00:35 |
| frontend | `b4469f09605a` | `b4469f09605a` | `0bc652f15716` | 2026-08-27 03:00:51 |
| migrator | `9a1fd7ccc8e6` | `9a1fd7ccc8e6` | `e518c3bb498d` | 2026-08-23 13:20:30 |

- **보존본 ≠ 신규본이 6종 전부에서 성립**한다(완료 정의 14의 실물 근거).
- 그러나 `ledger_rollback_target()` 은 `:prev` 를 **후보로 보지도 않는다** — 원장의 태그만 훑기 때문이다. `rollback.sh` 가 `:prev` 로 가려면 사람이 `--to-tag prev` 를 명시해야 하고, 그건 「직전 green 릴리스로 갔다」의 증명이 아니다.
- ⚠ 부수 관측 — `:30b3e0a7b3f3` 의 이미지 생성 시각이 **2026-08-28 21:34:09**(10:08 배포보다 앞)이다. 빌드가 캐시로 전부 히트해 **같은 이미지 ID 를 재사용**했다는 뜻이고, `deploy.sh` 도 이 경우를 「동일해도 실패는 아니다」로 명시해 둔다. `migrator` 는 2026-08-23 빌드본과 같다.

---

## 7. `[미확인]` 전건 — 각각 무엇이 푸는가

| # | `[미확인]` | 무엇을 하면 풀리나 |
|---|---|---|
| ㉠ | 자동 트리거 완주 (완료 정의 1) | `infra/staging/pipeline/install-schedule.sh` 로 5분 크론을 설치하고, `main` 에 커밋 하나를 올린 뒤 **사람이 아무 명령도 부르지 않은 채** 원장에 green `deploy` 행이 서는 것을 확인한다 |
| ㉡ | 실배포에서 판정기가 red 를 낸 로그 (완료 정의 2-b) | 다음 회차에 헬스 판정 단계까지 도달한 red 가 나면 그 로그를 채증한다. 인위 유발은 운영 스택 훼손이라 하지 않는다 |
| ㉢ | 롤백 왕복 4구간 (완료 정의 4·5·6) | **두 번째 green 릴리스**를 원장에 세운 뒤 배포 → 롤백 → 재배포. 지금 상태에서는 `ledger_rollback_target` 대상이 0건이라 `rollback.sh` 가 시작조차 못 한다 |
| ㉣ | 배포 **직전** `/healthz` 200 (완료 정의 11) | 다음 회차 배포 스크립트 실행 **전에** 6종을 재고 로그에 남긴다(현재 `deploy.sh` 는 배포 후만 잰다) |
| ㉤ | `deploy.sh` ③·④ 의 실행 중 대조 출력 (완료 정의 14) | `run-pipeline.sh` 경로로 배포해 `pipeline.log` 를 남긴다. `deploy.sh` 단독 호출은 표준출력만 내고 파일로 남기지 않는다 |
| ㉥ | **staging 실물의 `403` 2건** | 스위치가 꺼진 계정(스위치 행 `f` 이거나 부재인 **연구원**)에 묶인 토큰을 주체 등기부에 1건 심고 실존 객체에 `PATCH` → `403` 확인 (§3-3) |
| ㉦ | 태그 **28건** 삭제라는 계수 | 로그가 없어 사후 확인 불가. 다음 배포부터 `run-pipeline.sh` 로 돌려 `pipeline.log` 를 남긴다. ⭑ **사후 판정을 관측 개수로 쓰지 않는다** — 지금 말할 수 있는 것은 「현재 `colab-v2/*` 태그 18개 = 코드가 예측한 집합과 일치」뿐이다 |
| ㉧ | `d4_lineage_unknown` 의 배포 전 값 | 기준선 축으로 등재하고 다음 회차부터 전후를 함께 센다 (현재 관측 = 7행) |
| ㉨ | `work-item-consistency` red 12건 중 `I3` 외 11건 | 각 항목의 산문 갈라짐을 실물과 1:1 대조해 사람이 판정 (게이트가 이미 자리를 지목해 뒀다) |

---

## 8. 이번 회차에 **세지 않은** 판단기준 (다음 회차 진입조건)

- 롤백 후·재배포 후의 데이터 기준선 (4가 닫혀야 잴 수 있다)
- `POST /searches` 1회 · `preflight` 성질 판정 · `:i2` 태그 이력 (`R-1` 잔여 셋)
- 백업 크론 첫 회차 로그 (`R-1` 잔여 — 이 회차 범위 밖)
- prod 타깃의 실물 거부 (fixture 로만 증명 · 실물 prod 는 `I5`)
