# 병렬 착수 지도 — 충돌·게이트 경합·웨이브

**작성 2026-09-02 · 기준 `main` `024f881`(clean) · 오라클 = `dev-package/work-items.yaml` ＋ `PLAN-SoT.md §9`(〈275〉까지).**
산문(`03-HANDOFF.md`·`WORK-UNITS.md`)과 갈리면 대장이 이긴다. 선행 조사 = `notes/STAGE2-REMAINING.md`(〈271〉 기준 · 이 문서가 갱신본).

---

## 0. 계수 — 산문과 갈린다

- **실측(대장 전수 · 이 회차)** — `stage2` 총 **32**, 미완 **12**(`IS4`·`I3`·`I4`·`R-1`·`V-1`·`V-2`·`J-1`·`CT-1`·`P8`·`PA-G`·`S3`·`2단-격자전용-실패3건-처분`).
  `deferred` 1건 제외 = **11** · `PA-G` 자신 제외 = **10**.
- `stage1` 미완 3 — `SC-5`(`partial` `:122`) · `LV-1`(`open` `:1389`) · `LV-2`(`open` `:1429`).
- ⚠ **`PLAN-SoT.md:626` 〈275〉-㉮ 은 「stage2 미완 14 → 13 → 12 · 총 15」로 적는다.** 같은 결정이 `A-1`·`P7` 을 닫혔다고 적으면서(`〈273〉`) 그 둘을 계수에서 빼지 않았다 — **2건 과다.** 실측 총 미완 = 3 ＋ 11 = **14**(`PA-G` 포함) / **13**(제외).
  이 문서는 값을 고치지 않고 갈림만 적는다(대장 변경 0건).

---

## 1. 착수 가능성

### 1.1 착수 가능 (전건 충족)

| 항목 | status / stage | depends_on 실상태 | 완료 정의 | 근거 |
|---|---|---|---|---|
| **R-1** 복원 절차 | `partial` / stage2 | `[]` | 정본 확정(〈255〉) | `work-items.yaml:767`·`:771`·`:772`. 남은 것 = 크론 **무인 연속 3회 GREEN** — 측정이 길다, 가장 먼저 건다 |
| **IS4** terraform state | `partial` / stage2 | `IS2` = `done` | 확정 | `:306`·`:310`·`:311`. 미달 2 = 마지막 `apply` 미실행 · 맨몸 호스트 미실험(`R-1` 대기 사유 아님) |
| **LV-2** AI 계보 추천 버튼 | `open` / **stage1** | `P2` = `done` | 확정 ⓐ~ⓔ | `:1428`·`:1432`·`:1433`. `entry_conditions` 축자 「**없음 — 지금 착수 가능하다**」(〈203〉) |
| **V-2** 값 조회 | `open` / stage2 | `P3`·`A-1` **둘 다 `done`** | **확정본**(〈254〉 · `:852`) | `A-1` 이 `〈273〉` 으로 `done`(`:622`) — `STAGE2-REMAINING §2` 의 「`A-1` = `open`」 실격 사유는 **소멸**했다. `#54` 대상에서도 빠졌다(〈275〉-㉰) |
| **P8** E-01 적용 지점 표 | `open` / stage2 | `P7` = `done` | 「각 P 의 완료 판정」 4항(`:1115`) | `:1117` note 축자 「**막는 것은 이제 0건**」(〈273〉) |
| **S3** 실데이터 5종 E2E | `open` / stage2 | `S2`·`P3` = `done` | 확정(〈248〉 · `:1247`) | 잔여 1행(NumPy 화면 렌더). ⛔ **`#58` 과 같은 파일** — §3 참조 |

### 1.2 조건부 — 판정 하나가 선행해야 착수·완주가 성립

| 항목 | 막는 사실 | 풀리는 조건 |
|---|---|---|
| **CT-1** | ⛔ 마지막 한 칸 `downloadDataset` 의 **파일 저장처 소유 WU 0건**(`PLAN-SoT.md:626` 〈275〉-㉯ · 대장 96항목 전수). `CT-1` 이 흡수하면 그 항목의 「새 요건 0건」(`:1024`)이 거짓이 된다 | Ted 판정(저장처 소유 배정). **나머지 칸은 지금 착수 가능** — 완주만 불가 |
| **LV-1** | 계약 동결 해제 **등급 ㉯ — Ted 승인 필수**(`:1391` `entry_conditions` · 〈258〉·`#53`). `DatasetUpdate.processingLevel` 제거는 파괴적 변경 | Ted 동결 해제 승인 기록 |
| **I3** | 완료 정의 15행 중 열림 6 · 그중 ⑷ 롤백 왕복·⑸ 직전 릴리스가 **열린 블로커 `#43`**(`03-HANDOFF.md:358` 표 #43 — green `deploy` 행 1건이라 `rollback.sh` 가 `die`) | `#43` 판정 ＋ 집행 |

### 1.3 착수 불가 (실격 사유)

| 항목 | 실격 사유 (전건) |
|---|---|
| **V-1** | `completion_def: 완료 정의 미작성`(`:800`) · 초안은 `completion_def_draft`(`:801`) · 축자 「**Ted 확정 전에는 이 항목을 착수 가능으로 보지 않는다**」. `#54` 대상 2건 중 하나(〈275〉-㉰). 의존은 이제 충족(`P3`·`A-1` 둘 다 `done`) — **막는 것은 완료 정의뿐** |
| **J-1** | `completion_def_draft`(`:939`) · `[미확인]` **5자리**(`J-1`⑷·`J-2`⑷·`J-3`⑶·`J-8`⑴·`J-9`⑶). `#54` 대상. ＋ `entry_conditions` = 「stage 2 마지막」(`:937` · 〈157〉-㉱). 의존(`A-1`)은 충족 |
| **SC-5** | **stage1 · `completion_def: 완료 정의 미작성`**(`:127`). `status: partial`(`:122`). 완료 정의가 없으면 닫는 기준이 없다 — 착수 불가 |
| **I4** | `depends_on: [I3]` · `I3` = `partial`(`:364`). ＋ 남은 조건 넷(분산 추적·로그·알람·레지던시) 레포 실물 0건(`:359` note · 〈249〉-㉮) |
| **PA-G** | `entry_conditions` = 「대장 `stage1`·`stage2` 미완 **0건**」(`:1217` · 〈258〉 규칙 넷). 지금 13건 |
| **2단-격자전용-실패3건-처분** | `status: deferred`(`:1357` · 〈145〉-㉳ Ted 「그대로 둬」) |

### 1.4 P8 재대조 (이번 회차 요청 항목)

- `work-items.yaml:1108-1118` — `status: open` · `stage: stage2` · `entry_conditions: ["P7"]` · `depends_on: [P7]` · `P7` = `done`(`:1098`, 〈273〉).
- `completion_def` = 「각 P 의 완료 판정」 4항(`:1115`) — **초안 아님 · 정본 참조형**. `completion_def_draft` 필드 **없음**.
- §9 에 `P8` 을 이연·재범위·재배정한 결정 **0건** — 〈273〉-㉵ 가 여는 쪽으로만 적었다(`:1117` 축자 「막는 것은 이제 0건이고, 착수는 다음 회차의 선택이다」).
- ⟹ **`P8` 은 착수 가능이다.** 실격 사유 0건.

---

## 2. 폭발 반경 (파일·계약·표·마이그레이션·게이트)

| 항목 | 코드·자리 | 계약·생성물 | DB·마이그레이션 | 게이트 |
|---|---|---|---|---|
| **S3** 잔여 1행 | `services/pipeline-worker/src/colab_pipeline/d5/formats.py:35` · `d5/renderable.py:32-36` · `services/viz-render/.../d7_visualization/readers.py:35-41` · `services/viz-render/tests/test_e2e_real.py` | 없음 | 없음 | `e2e-format-coverage`(＋selftest) · 정본 `gates/config/e2e-format-coverage.toml` |
| **#58** 파서 4→6 (판정 완료·미집행) | **위와 같은 3파일** ＋ `pipeline-worker/tests/test_detect.py`·`test_renderable.py`·`test_grib_support.py` | 없음 | 없음 | 같음 |
| **CT-1** | `frontend/src/components/catalog/{columns.ts,types.ts,ColumnMenu.tsx,localEngine.ts,catalog.css}` · 마지막 칸은 `services/core-api/.../routes/catalog.py` | `contracts/seams/fe-core.yaml`(`downloadDataset`) ＋ `frontend/src/generated/fe-core.ts` | 파일 저장처 `[미확인]`(소유 WU 0건) | `generated-up-to-date` · `contract-lint` · `contract-breaking` |
| **P8** | `services/core-api/**` D2 권한 적용 지점 · 화면별 표의 프런트 소비처 `[미확인]` | 정책·패키지 **재생성** — `dev-package/PERMISSION-PRINCIPLES.md`·기획 정본 임베드 | 없음 `[미확인]` | **`planning-freshness`**(임베드 md ↔ 원본 md) · `work-item-consistency` |
| **V-2** 값 조회 | `d7_visualization/{raster.py,readers.py,coords.py,tiles.py}` ＋ 신설 조회 경로 · 데이터셋 상세 프런트 | `contracts/seams/core-viz.yaml` ＋ `fe-core.yaml`(신규 op) ＋ 생성물 3벌 | 읽기만(경계 판정은 `datasetId` 경유 · `:852` 권한 ⓐⓑ) | `contract-lint`·`contract-breaking`·`generated-up-to-date`·`seam-consistency` |
| **V-1** 팔레트 재렌더 | `d7_visualization/{jobs.py,invalidation.py,palettes.py,colormap.py}` — **자리의 산출물을 지운다**(완료 정의 초안 ⑷) | `core-viz.yaml` `[미확인]` | 없음 | **`artifact-ownership`**(사이드카↔원장 대조) · `preview-tile-slot` · `render-latency` |
| **J-1** 9건 | 프런트 다수 ＋ `d5`·`d7` · 격자 경로 | 다수 `[미확인]` | **마이그레이션 1건**(`J-2` 연구실 기본 격자 · `:939` 축자 「`0004` 에 자리 없음」) → 다음 번호 **`0011`** | `schema-diff` · `migration-single-head` · `generated-up-to-date` |
| **LV-1** | `services/core-api/.../routes/catalog.py` · `domains/d3_catalog.py`(`processing_level` `user_set` 분기) · `db/platform/schema.sql` | `contracts/seams/fe-core.yaml` `DatasetUpdate.processingLevel` **제거** ＋ 생성물 | **마이그레이션 1건 ＋ down** → 다음 번호 **`0011`** (현 head `db/platform/versions/0010_p6_access_request.py`) | `contract-breaking`(**red 예상 · 동결 해제 기록과 짝**) · `contract-lint` · `seam-consistency` · `generated-up-to-date` · `schema-diff` · `migration-single-head` |
| **LV-2** | `frontend/src/components/lineage/LineageStep.tsx`(`:90` 자동 호출) ＋ core-api 중계 | 계약 개정 0(`:1433` ⓐ~ⓔ 어디에도 계약 항 없음) | 없음 | 프런트 시험만 |
| **R-1** | `infra/staging/backup/{backup-full.sh,install-schedule.sh,schedule.crontab,restore-rehearsal.sh,verify-*.sh,volume-lib.sh}` ＋ **호스트 크론** | 없음 | 원장·볼륨 백업 산출물(보관처) | 없음 — 게이트 밖. 대신 **staging 스택·볼륨을 실제로 만진다** |
| **IS4** | `infra/staging/tunnel/**`(terraform ＋ README §5-1) | 없음 | terraform state | 없음 |
| **I3** | `infra/staging/{deploy.sh,rollback.sh,pipeline/**}` ＋ `release-ledger.tsv` | 없음 | 릴리스 원장 | 없음 — **배포 자체가 공유 자원** |
| **I4** | `[미확인]` — 추적·로그·알람·레지던시 실물 0건 | `[미확인]` | `[미확인]` | `[미확인]` |
| **PA-G** | `services/core-api/.../kernel/authn.py` ＋ `ops/set-password.py`·`credentials.json` 폐기(`:1219`) | 인증 계약 `[미확인]` | `[미확인]` | 배포 green |

---

## 3. 충돌 행렬

`■` = 같은 파일/표/번호를 **쓰기**로 만진다(직렬 필수) · `▲` = 같은 게이트·공유 환경만 겹친다(게이트 실행만 직렬) · 공란 = 무충돌.

| | S3 | #58 | CT-1 | P8 | V-2 | V-1 | J-1 | LV-1 | LV-2 | R-1 | IS4 | I3 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **S3** | — | **■** | | | ▲ | ▲ | | | | | | ▲ |
| **#58** | **■** | — | | | ▲ | ▲ | | | | | | ▲ |
| **CT-1** | | | — | ▲ | **■** | | ▲ | **■** | | | | ▲ |
| **P8** | | | ▲ | — | | | | ▲ | | | | ▲ |
| **V-2** | ▲ | ▲ | **■** | | — | **■** | ▲ | **■** | | | | ▲ |
| **V-1** | ▲ | ▲ | | | **■** | — | ▲ | | | | | ▲ |
| **J-1** | | | ▲ | | ▲ | ▲ | — | **■** | ▲ | | | ▲ |
| **LV-1** | | | **■** | ▲ | **■** | | **■** | — | | | | ▲ |
| **LV-2** | | | | | | | ▲ | | — | | | ▲ |
| **R-1** | | | | | | | | | | — | ▲ | **■** |
| **IS4** | | | | | | | | | | ▲ | — | ▲ |
| **I3** | ▲ | ▲ | ▲ | ▲ | ▲ | ▲ | ▲ | ▲ | ▲ | **■** | ▲ | — |

**`■` 의 실체 — 하나씩 근거를 적는다**

1. **S3 ↔ #58 — `SUPPORTED_FORMATS`·`RENDERABLE_FORMATS`.** 선언은 `d5/formats.py:35` 하나이고 `d5/renderable.py:36` 이 그것에서 파생한다. `#58` 은 **선언을 줄이지 않고 처리를 4→6 으로 채운다**(`03-HANDOFF.md:358` #58 · 〈271〉-㉯). `S3` 의 잔여 1행이 바로 그 NumPy 렌더다. **한 레인으로 묶는다.**
2. **CT-1 ↔ LV-1 — `services/core-api/.../routes/catalog.py` ＋ `contracts/seams/fe-core.yaml` ＋ `frontend/src/generated/fe-core.ts`.** `LV-1` 은 그 계약에서 필드를 **제거**하고 `CT-1` 은 같은 계약에 `downloadDataset` 을 **채운다**. 생성물이 한 파일이라 두 레인이 각각 재생성하면 `generated-up-to-date` 가 어느 쪽에서도 green 이 아니다.
3. **V-2 ↔ CT-1 / LV-1 — `fe-core.yaml` ＋ 생성물 3벌**(`contracts/codegen/manifest.toml` 등기 3건 · `03-HANDOFF.md:358` #26). 계약 파일을 동시에 여는 레인은 하나여야 한다.
4. **V-2 ↔ V-1 — `d7_visualization` 산출물 자리.** `V-1` 은 옛 산출물을 **지우고**(초안 ⑷ · 「새 것이 선 뒤에 옛 것을 지운다」) `V-2` 는 **그 자리의 COG 에서 창을 읽는다**(`:852` 값의 출처 ⓒ). 지우는 레인과 읽는 레인이 같은 자리를 동시에 만진다.
5. **LV-1 ↔ J-1 — 마이그레이션 번호 `0011`.** 현 head = `db/platform/versions/0010_p6_access_request.py`. 둘 다 platform 체인에 1건씩 더한다 → 같은 번호를 집으면 `migration-single-head` 가 head 분기로 red 를 낸다. **동시에 열지 않는다.**
6. **R-1 ↔ I3 — staging 스택·볼륨·릴리스 원장.** `R-1` 은 전범위 백업·복원 리허설로 볼륨을 만지고, `I3` 은 배포·롤백으로 컨테이너와 원장을 만진다. 한 호스트 한 스택이다.

**`▲` 의 실체**

- **공유 게이트** — `contract-lint`·`contract-breaking`·`generated-up-to-date`·`seam-consistency` 는 계약을 건드리는 모든 레인이 공유한다(CT-1·V-1·V-2·LV-1·J-1).
- **공유 정본 파일** — `gates/config/e2e-format-coverage.toml`(S3·#58) · `dev-package/work-items.yaml`·`03-HANDOFF.md`(전 레인이 원장·산문을 갱신한다 — `〈273〉`-㉮ 가 실제로 이 자리에서 충돌 1건을 냈다).
- **공유 staging platform DB(읽기 전용)** — `artifact-ownership`·`autometa-loss`·`preview-tile-slot` 셋이 `COLAB_*_DB_URL` 로 **staging 실물**을 본다(`gates/tools/artifact-ownership.sh:60`·`autometa-loss.sh:69`·`preview-tile-slot.sh:55`). 셋 다 읽기 전용이라 서로는 안 부딪히지만, **staging 을 바꾸는 레인(I3 배포 · R-1 복원 · P8/V-2 의 배포 green 조건)이 돌면 셋의 판정이 통째로 흔들린다.**
- **`I3` 행 전체가 ▲** — 배포는 모든 항목의 공통 완료 조건(`CLAUDE.md §0` 「staging 배포 green」)이라, `I3` 이 스택을 만지는 동안 다른 레인은 자기 완주 판정을 낼 수 없다.

---

### 3-b. 갱신 — A ＋ B 3레인 (2026-09-03 · `main` `8cc54fe` · 등재 `PLAN-SoT §9 〈287〉`)

⚠ **위 §1~§3 은 `〈275〉` 기준이라 착수 가능 표 6행 중 셋이 이미 닫혔다** — `R-1`(`〈286〉`) · `P8`(`〈281〉`) · ＋ `ST-1` 신설·종결(`〈278〉`·`〈279〉`)로 `CT-1` 의 실격 사유도 소멸했다. **원문은 지우지 않고 이 절이 값을 갱신한다.**
**분류표 전문 = `dev-package/notes/REMAINING-20260903.md`.** 미완 32건 = A 2 · B 1 · C 7 · D 2 · E 20.

| | LV-1(닫기) | LV-2 | CT-1 |
|---|---|---|---|
| **LV-1(닫기)** | — | | |
| **LV-2** | | — | ▲ |
| **CT-1** | | ▲ | — |

- **`■` 0건** — 쓰기 파일 면이 겹치지 않는다. `LV-1`(닫기) = 대장 ＋ 산문(코드 0) · `LV-2` = `frontend/src/components/lineage/LineageStep.tsx` ＋ 시험 · `CT-1` = `frontend/test/catalog.test.tsx` ＋ 시험 도구 설정.
- **`▲` 하나** — `LV-2` ↔ `CT-1` 이 `frontend-typecheck`(＋selftest)와 프런트 시험 계수를 공유한다. **파일은 안 겹치고 게이트 실행만 직렬**이면 된다.
- **공유 정본 파일** — 셋 다 `work-items.yaml`·`03-HANDOFF.md`·`PLAN-SoT §9` 를 만진다. **번호 발급·§9 등재는 오케스트레이터가 직렬로**(`〈252〉`).
- **계약 개정 0건 · 마이그레이션 0건.** platform 체인 head = **`0011_lv1_drop_level_user_set`** ⟹ **`0012` 는 비어 있다**(지금 후보는 `J-1` 의 `J-2` 연구실 기본 격자 하나).
- **게이트 39 종**(`gates/run.sh:12` `ALL_GATES` 실측 · 종전 표기 33 은 낡았다). **`./gates/run.sh all` 은 한 번에 1 레인**(pg 슬롯 호스트 전역 한도 4 · 레인 기본 병렬도 2) · **staging 스택 1 레인 배타**.
- **권고 순서 = ⑴ `LV-1` 닫기 ⑵ `LV-2` ⑶ `CT-1`.** ⑴⑵ 로 `stage1` 미완이 3 → 1 이 되고 남는 자물쇠는 `SC-5` 완료 정의 하나다.

⭑ **`#43` 의 전제 소멸(2026-09-03 실측)** — 릴리스 원장 `deploy` **15행 · green 12** ⟹ 롤백 대상 **11건**. §1.2 의 `I3` 행 「green `deploy` 행 1건이라 `rollback.sh` 가 `die`」는 낡았다.

---

## 4. 공유 환경 경합 — `./gates/run.sh all` 동시 실행 한도

**측정 대상 셋: 일회용 postgres 슬롯 · staging 실물 DB · 시간을 재는 게이트.**

1. **일회용 postgres 슬롯이 호스트 전역이다.** `gates/tools/_pg.sh:68` — 슬롯 디렉터리 = `${TMPDIR:-/tmp}/colab-v2-gatepg-slots`, 한도 = `COLAB_PG_MAX_CONCURRENT` **기본 4**(`_pg.sh:71`). **워크트리별이 아니라 호스트 하나에 4개다.** 못 얻으면 재시도·건너뛰기 없이 **red(준비)**(`_pg.sh:83`).
2. **슬롯을 먹는 게이트가 10종이다** — `artifact-ownership-selftest`·`autometa-loss-selftest`·`e2e-format-coverage`·`preview-tile-slot-selftest`·`render-latency`·`rls-coverage`·`rls-effect`·`schema-diff`·`stage2-markers`(＋`db-selftest`). `rls-effect-selftest` 는 `rls-effect.sh` 를 케이스마다 다시 부르므로(`rls-effect-selftest.sh:12`·`:22`) 슬롯을 **반복해서** 집는다.
3. **한 레인의 기본 병렬도가 2다**(`gates/run.sh:239` `jobs_n=2`). ⟹ 레인 하나가 최대 2 슬롯. **레인 2개면 4 = 한도 정확히 소진**이고, 3번째 레인은 **즉시 red(준비)** 다. 선행 레인이 본 `rls-effect-selftest` red(준비)가 이 무늬다(`rls-effect-selftest.sh:105-107` 이 그 실패를 「판정하지 못했다 · 통과로 세지 않는다」로 찍는다).
4. **레인 2개도 안전하지 않다 — 시간을 재는 게이트가 있다.** `render-latency` 는 `parallelism.toml:119` 에서 `serial` 인데 **그 선언은 한 실행기 안에서만 지켜진다.** 다른 워크트리의 `run.sh` 는 남의 `render-latency` 를 모른다. `parallelism.toml:114-118` 축자 — 「다른 게이트와 CPU·디스크를 나눠 쓰면 렌더 시간이 늘고, 그 red 는 **배선이 낸 red** 다」. 같은 사유로 `preview-tile-slot-selftest` 도 `serial`(`:99` — `-j 2` 두 회차에서 **슬롯 고갈로 다른 게이트가 환경대기 red**).
5. **디스크도 한 자리다** — `e2e-format-coverage` 가 **원천 3.5 GB 를 읽는다**(`parallelism.toml:105-106`).
6. **staging 실물 DB 는 읽기 전용이라 동시 읽기는 안전하다**(`parallelism.toml:47-49`·`:62-71`·`:83-88` — 세 게이트 전부 쓰기 0). 위험은 동시 읽기가 아니라 **누가 그 DB·스택을 바꾸는가**다.

**⟹ 안전 동시 실행 수 = `./gates/run.sh all` 은 **1 레인**.**
근거 — ⑴ 2 레인이면 pg 슬롯 4/4 로 여유 0 이라 `db-selftest`(serial · 슬롯 1)나 `rls-effect-selftest`(반복 획득)가 대기 상한을 넘기는 순간 red(준비) ⑵ 2 레인이어도 `render-latency` 의 눈금이 남의 CPU 에 흔들려 **판정이 아닌 red** 를 만든다 ⑶ 3 레인 이상은 슬롯 계산상 확정 red.
**보조 규칙 셋** — ⓐ 게이트를 쓰지 않는 레인(문서·원장·프런트 시험만)은 **동시 수 제한 없음** ⓑ 단일 게이트 호출(`run.sh contract-lint` 등 pg·시간 미사용)은 동시 다수 가능 ⓒ `COLAB_PG_MAX_CONCURRENT` 를 올려 green 을 만들지 않는다(`parallelism.toml:98` 축자 「한도는 이 호스트가 감당하는 값이다」).
**staging 스택 동시 점유 = 1 레인**(배포·복원·백업은 상호 배타).

---

## 5. 권고 웨이브

### 웨이브 1 — 지금 열 수 있고 서로 무충돌 (레인 4)

| 레인 | 왜 여기인가 | 선행 결정 |
|---|---|---|
| **R-1** | `depends_on: []` · 완료 정의 확정(〈255〉). 합격선이 **크론 무인 연속 3회 GREEN** 이라 달력 시간이 든다 — 가장 먼저 걸어야 뒤 웨이브를 안 민다. 파일 면 = `infra/staging/backup/**` 단독 | 없음 |
| **IS4** | `IS2` = `done` · 파일 면 = `infra/staging/tunnel/**` 단독 · 게이트 0 | 없음 |
| **LV-2** | `entry_conditions` 축자 「없음 — 지금 착수 가능」 · 파일 면 = `LineageStep.tsx` ＋ 중계 · **계약 개정 0 · 마이그레이션 0** | 없음 |
| **V-2** | 완료 정의 **확정본**(〈254〉) · `P3`·`A-1` 둘 다 `done` · 계약을 여는 유일한 웨이브 1 레인이라 `fe-core.yaml` 을 독점한다 | 없음 (⚠ 완주에는 staging 배포 green 필요 → §4 스택 배타) |

⚠ **R-1 ↔ IS4 는 같은 호스트를 쓴다** — 파일 면은 갈리지만 백업·복원 회차와 terraform `apply` 를 **같은 시각에 돌리지 않는다**.

### 웨이브 2 — 판정 하나가 이미 서 있다 (레인 2)

| 레인 | 왜 여기인가 | 선행 결정 |
|---|---|---|
| **S3 ∪ #58 (한 레인)** | `#58` 판정은 이미 났다(〈271〉-㉯ · 미집행). 같은 3파일을 만지므로 **가르면 반드시 충돌한다** — 처리 4→6 을 채우고 그 자리에서 `S3` 잔여 1행을 닫는다 | 〈271〉-㉯ (기존) |
| **P8** | 막는 것 0건(〈273〉-㉵). `planning-freshness` 를 독점한다 — 웨이브 1·2 의 다른 레인은 기획 정본을 만지지 않는다 | 없음 |

웨이브 1 과 병행 가능하나, **게이트 `all` 은 §4 대로 한 번에 한 레인만** 돈다.

### 웨이브 3 — Ted 판정이 먼저 떨어져야 한다 (레인 3, 순차)

| 레인 | 착수 전 필요한 결정 | 왜 웨이브 3 인가 |
|---|---|---|
| **LV-1** | **계약 동결 해제 등급 ㉯ 승인**(`:1391`) | `fe-core.yaml`·`routes/catalog.py`·생성물을 `CT-1`·`V-2` 와 공유(`■`) → 웨이브 1 의 `V-2` 가 끝난 뒤 |
| **CT-1** | **`downloadDataset` 파일 저장처의 소유 WU 배정**(〈275〉-㉯) | `LV-1` 과 같은 계약·같은 라우트 파일(`■`) → `LV-1` 다음 |
| **I3** | **`#43` 판정 ＋ 집행**(롤백 대상 0건) | staging 스택 배타 — `R-1` 완주 뒤 |

### 웨이브 4 — 완료 정의가 확정된 뒤 (레인 3)

| 레인 | 선행 결정 |
|---|---|
| **V-1** | `#54` — `completion_def` 확정(초안 → 정본). ＋ `V-2` 병합 뒤(같은 산출물 자리 `■`) |
| **J-1** | `#54` — 초안의 `[미확인]` 5자리 확정. ＋ `LV-1` 병합 뒤(마이그레이션 `0011` `■`). `entry_conditions` 「stage 2 마지막」이 이 자리를 강제한다 |
| **I4** | `I3` 이 `done` 이 된 뒤. ＋ 남은 조건 넷의 실물 0건을 어느 회차가 지는지 `[미확인]` |

### 웨이브 5 — 마지막

- **PA-G** — `stage1`·`stage2` 미완 0건이 될 때. **`SC-5` 가 남는 한 열리지 않는다.**
- ⛔ **`SC-5` 는 어느 웨이브에도 못 넣는다** — `완료 정의 미작성`(`:127`). **`PA-G` 를 열려면 `SC-5` 완료 정의 기재가 별도 판정으로 먼저 서야 한다.** 지금 이 자리를 지는 항목·결정 **0건** `[미확인]`.

---

## 6. 이 문서가 재지 않은 것

- `P8` 의 프런트 소비처·DB 접촉 `[미확인]` — 완료 정의가 「4항」 참조형이라 파일 면이 대장에서 안 나온다.
- `I4` 의 폭발 반경 전건 `[미확인]`(실물 0건).
- `PA-G` 의 계약 접촉 `[미확인]`.
- `COLAB_PG_MAX_CONCURRENT` 를 4 에서 올렸을 때의 호스트 한계 `[미측정]` — 올리지 않는 것이 규율이므로 재지 않았다.
- 워크트리 2개가 **같은 도커 데몬**에서 `all` 을 돌 때의 실측 red 재현 `[미실행]` — 이 문서는 읽기 전용 조사다(게이트 실행 0건).
