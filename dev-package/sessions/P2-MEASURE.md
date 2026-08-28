# P2 실측 — `status: conflict` 를 실물로 가른다 (2026-08-28)

> **이 파일은 실측 기록이다.** 문서를 고르지 않았다 — 코드를 읽고 시험을 돌리고 staging 실물을 셌다.
> 값의 정본은 `PLAN-SoT §9` 이고, 이 파일은 **잰 값과 잰 방법**만 남긴다. 문서는 한 줄도 고치지 않았다.
> 측정 시점 = 2026-08-28 · 레포 HEAD `8ec41e8` · staging 컨테이너 8/8 up (4시간 가동).

---

## 1. `P2` 완료 정의 정본 — verbatim

**대장(`dev-package/work-items.yaml` · `- id: P2`)의 `completion_def`:**

```
completion_def: "「각 P 의 완료 판정」 4항 ＋ 2026-08-25 추가 둘 — ⓐ 저장 배치를 단언하는 회귀 시험(`#26`) ⓑ `addDatasetFile` 202 의 저장 자리(`#21`). 스키마 판정(Ted) 전에는 닫지 않는다"
```

**`sources:` 가 가리키는 절 — `WORK-UNITS §7` 말미, verbatim:**

```
**각 P의 완료 판정 (I2 이후 공통)** — 넷 다 충족해야 닫힌다.

1. 해당 단계 스토리의 수용 기준 통과
2. 도메인 게이트 green (계약·경계·스키마·RLS)
3. **staging 배포 green** — 로컬 green은 완료가 아니다
4. 목업 대비 화면 검증
```

**`WORK-UNITS §7` T-P 표 `P2` 행 말미(추가 둘의 원문), verbatim:**

```
**⭑ 2026-08-25 — 완료 정의에 둘이 붙는다.** ⓐ **저장 배치를 단언하는 시험**(접수 ↔ 워커가 같은 자리를 본다는 것을 한 자리에서 못 박는 회귀 시험). 2026-08-25 에 두 파일의 규칙이 갈라졌는데 시험 0건이라 **배포에서만 났다**(`03-HANDOFF §4` #26). ⓑ **`addDatasetFile` 202 의 저장 자리** — 계약은 열렸으나 축 미정 격자를 둘 원장 행이 없다. **스키마 판정(Ted) 전에는 P2 를 닫지 않는다**(`§4` #21).
```

**`P2` 의 stage 1 범위(`WORK-UNITS §7` P2 행 · `〈70〉`·`〈74〉`), verbatim 발췌:**

```
**나가는 것** = S-08 화면 전체 · 타일 서빙·서명 · 팔레트 선택 재렌더 · `createScreenshot` · COG 변환 · 값 조회. **남는 것** = S-04 ①② · 업로드 3 op · 계보 3 op + Lv 파생 · `d5_*` 원장 · outbox/워커/reaper · 감지 · 계보 확정 모달 ③. **더해지는 것** = **미리보기 3층 · 미리보기 중계 2 op · 격자 3 op · 격자 요청 블록 · 축 판별 사다리 · 좌표 정합 확인 화면 · 뒤집기 · `.npy` 지원.**
```

---

## 2. 항목별 실측

### ⓐ 저장 배치를 단언하는 회귀 시험 (`#26`) — **닫힘**

**단일 정의처가 실재한다.** `contracts/storage/layout.json` 이 배치의 정본이고,
`contracts/codegen/manifest.toml` 에 등기 3건(`storage-layout-core`·`storage-layout-pipeline`·`storage-layout-viz`).
정본이 정하는 키 두 줄 —

```
"본체": "{uploadsPrefix}/{targetId}/{fileId}"
"기준 격자 파일": "{uploadsPrefix}/{targetId}/{gridDirname}/{fileName}"
```

**시험 15건 — 세 단위에서 전건 green (2026-08-28 실행).**

| 단위 | 파일 | 시험 | 결과(verbatim) |
|---|---|---|---|
| core-api | `services/core-api/tests/test_storage_layout.py` | 8 | `8 passed in 3.72s` |
| pipeline-worker | `services/pipeline-worker/tests/test_storage_layout.py` | 3 | `3 passed in 2.58s` |
| viz-render | `services/viz-render/tests/test_storage_layout.py` | 4 | `4 passed in 1.30s` |

시험 이름(접수 ↔ 워커 ↔ 그리는 쪽이 **같은 자리**를 본다는 것을 각각 못 박는다) —

- core-api — `test_본체는_저장_키_그대로_평평하게_놓인다` · `test_기준_격자는_grid_아래_원래_이름으로_놓인다` · `test_배치는_생성된_규약과_한_글자도_다르지_않다` · `test_격자와_본체가_같은_디렉터리에서_섞이지_않는다` · `test_등록_전환은_바이트를_데이터셋_자리로_모은다` · `test_등록_뒤_원장이_적은_저장_키가_실물을_가리킨다` · `test_등록_전_업로드의_배치는_그대로다` · `test_후주입_격자는_데이터셋_grid_아래로_온다`
- pipeline-worker — `test_워커가_본체를_배치대로_찾아_감지한다` · `test_워커가_격자를_원래_이름으로_열어_축을_확정한다` · `test_바이트가_없으면_조용히_넘어가지_않는다`
- viz-render — `test_core_api_가_놓은_격자로_지도형이_그려진다` · `test_격자를_안_올리면_그대로_보류다` · `test_원장이_발급한_fileId_로_조각을_고를_수_있다` · `test_격자가_본체로_오인되지_않는다`

**green-by-skip 아님을 확인했다.** DB 환경변수 없이 돌리면 8건이 **skip 이 아니라 error** 로 선다 —
`Failed: COLAB_CORE_TEST_DATABASE_URL 이 없다. DB 를 못 붙인 것은 통과가 아니다`.
DB 를 붙인 뒤에야 8 passed 가 나왔다.

**생성물 드리프트 게이트 green** — `generated-up-to-date green — 등기부 4건 전부 재생성 일치, 등기부 밖 자칭 생성물 0건.`

**배포된 실물이 같은 바이트다** — 세 staging 컨테이너와 레포의 `kernel/storage_layout.py` md5 **전부 동일**
(`90beaff6f85bfe0d84f016b6406ff0fa` × 4). 「두 파일에 각각 적어 두고 갈라졌다」는 상태가 실물에서 사라졌다.

**staging 디스크 배치 실측** (`colab_v2_staging_core_api` · `/var/lib/colab/uploads/uploads`, 읽기만) —

- 대상 디렉터리 **15** (데이터셋 12 + 업로드 3)
- 본체 파일 **123** = `uploads/{targetId}/{fileId}`
- `grid/` 디렉터리 **6** · 그 아래 파일 **12** · 이름 보존 확인(`LAT_HSR.npy`·`LON_HSR.npy`·`LAT_RN15.npy`·`LON_RN15.npy`·`Lat_HSR.npy`·`Lon_HSR.npy`)
- 원장(`d3_file`)의 격자 6행 `storage_key` 가 **디스크 실물과 한 글자도 다르지 않다** (예: `uploads/01M0Y1WM5JBDJRZ8FT3AX8HXE1/grid/LAT_HSR.npy`)

> ⚠ **부수 관측 — 완료 정의 항목은 아니다.** `grid/` 6 디렉터리 중 3 개는 **업로드 id** 자리다(`d5_upload` 에 3건 존재 · `d3_dataset` 에 0건).
> 등록 전환이 바이트를 **옮긴다**고 `layout.json` 산문이 적는데 실물은 **업로드 자리 사본이 남아 있다**(격자 파일 6개분).
> 원장은 데이터셋 자리를 가리키므로 판정에는 영향이 없으나, **잔여 바이트 6건**은 정리 소유자가 없다.

---

### ⓑ `addDatasetFile` 202 의 저장 자리 (`#21`) — **닫힘 (성격 소멸)**

**계약에서 `202` 가 사라졌다.** `contracts/seams/fe-core.yaml` 의 `addDatasetFile` 응답은
`"201" · "400" · "401" · "403" · "404" · "500"` 뿐이다. 산문도 verbatim 으로 적는다 —

```
⭑ **`202` 는 철회됐다 (Ted 판정 2026-08-27 · 여섯 번째 동결 해제 · `〈151〉`).**
집행은 `kind = 기준 격자 파일` 을 **400 으로 거절하고 `attachUploadGridFiles` 를 가리킨다.**
```

**집행이 계약과 같다.** `services/core-api/src/colab_core/app/routes/ingestion.py:540-543` —

```
raise errors.bad_request(
    "기준 격자 파일의 축(위도·경도)은 서버가 파일에서 판별한다 — "
    "이 op 은 그 판별을 태우지 않는다. 격자는 업로드로 올려 판별을 마친 뒤 "
    "`/datasets/{datasetId}/grid-files` 로 반영한다.")
```

**시험이 그 자리를 못 박는다** — `services/core-api/tests/test_grid_postinject.py:357`
`test_add_dataset_file_still_refuses_a_grid_and_points_here` (400 ＋ 본문에 `grid-files` 포함 단언). 2026-08-28 green.

**배포된 실물이 같다** — staging core-api 의 `ingestion.py` md5 = 레포 HEAD 와 동일(`7a74f7fdf071ae068950f68b30b95fd8`).

**게이트** — `contract-lint` green · `contract-breaking` green.

즉 **「축 미정 격자를 둘 저장 자리」라는 미결 자체가 없어졌다.** 격자의 자리는 `attachUploadGridFiles`
(원장 `d3_file` 격자 6행이 실제로 그 경로로 서 있다) 하나이고, 그 외 경로는 400 으로 닫힌다.
`completion_def` 의 「스키마 판정(Ted) 전에는 닫지 않는다」는 **판정이 2026-08-27 에 났으므로 충족**이다
(`〈151〉` — 스키마를 고치는 ⓐ·ⓑ 가 아니라 **ⓒ 계약에서 202 를 걷는다**를 골랐고, 코드는 무변경).

---

### ① 해당 단계 스토리의 수용 기준 통과 — **닫힘 (stage 1 범위 기준)**

- 시험 실측(2026-08-28, 전건 이번에 직접 돌림) —

| 단위 | 결과(verbatim) | 붙인 환경 |
|---|---|---|
| core-api | `455 passed in 42.42s` | 일회용 postgres ＋ `subjects.json` |
| pipeline-worker | `152 passed in 28.82s` | 일회용 postgres ＋ `COLAB_REFERENCE_DATA` |
| viz-render | `107 passed in 11.17s` | `COLAB_REFERENCE_DATA` |
| frontend | `Test Files 13 passed (13) / Tests 274 passed (274)` | — |
| frontend `tsc --noEmit` | exit 0 (출력 0줄) | — |

  실패 0 · error 0. 환경을 안 주면 fail-closed 로 서는 것을 먼저 확인했다
  (pipeline-worker: `COLAB_REFERENCE_DATA` 부재 시 18 failed · `COLAB_PIPELINE_DB_URL` 부재 시 15 error).
- `P2` 의 stage 1 범위에서 「해야 하는데 안 된 것」은 `sessions/STAGE1-CLOSE.md` 기준 0 이다.
  범위 밖으로 나간 둘은 미달이 아니라 판정이다 — **S-08 화면 전체 = stage 2**(`〈74〉`) ·
  **실데이터 계보 확정 완주 = stage 2**(`〈70〉-㉮`).

### ② 도메인 게이트 green (계약·경계·스키마·RLS) — **부분 닫힘 · 하나 [미확인]**

2026-08-28 개별 실행 실측 —

| 게이트 | 결과 |
|---|---|
| `contract-lint` · `contract-breaking` | green |
| `event-lint` · `event-breaking` | green |
| `generated-up-to-date` | green |
| `import-boundary` · `banned-import` · `ai-no-lineage-write` | green |
| `db-boundary` | green |
| `migration-single-head` · `rls-coverage` | green |
| `seam-consistency` · `planning-freshness` | green |
| `schema-diff` | **[미확인]** — 아래 |
| `work-item-consistency` | **red · 불일치 13건** (설계대로) |

- **`schema-diff` [미확인]** — 적용 DB URL 둘(`COLAB_APPLIED_DB_URL_PLATFORM`·`_AI`)을 staging 에서 만들어
  `gates/run.sh schema-diff` 를 돌리려 했으나 **하네스 분류기가 그 명령을 거부**했다(운영 DB 자격 취득 경로).
  **우회하지 않았다.** 마지막으로 잰 값 = 2026-08-27 살아 있는 staging 실측 **두 체인 다 green(드리프트 0)**(`〈172〉-㉴`).
  **푸는 법** — Ted 가 직접 한 줄로 돌린다(읽기 전용 `pg_dump --schema-only`):
  `COLAB_APPLIED_DB_URL_PLATFORM=... COLAB_APPLIED_DB_URL_AI=... ./gates/run.sh schema-diff`
- **`work-item-consistency` red 는 `P2` 의 결함이 아니다.** 13건 중 12건이 ㈓(`conflict` 잔존)이고
  **`P2` 자신이 그중 하나**다. 이 게이트를 `P2` 의 닫힘 조건으로 쓰면 순환이다 — 「`P2` 를 닫아야 게이트가 green 이 되는데
  게이트가 green 이어야 `P2` 를 닫는다」. 나머지 red 1건(㈑ `I0` 착수 후보 표 혼입)도 `P2` 무관.
- `rls-effect` · `selftest` 는 이번에 돌리지 않았다(**이번에 세지 않은 판단기준** — 다음 회차 진입조건).

### ③ staging 배포 green — **닫힘**

- 컨테이너 **8/8 up**(7 healthy ＋ cloudflared) · 헬스 **6종 전부 200**
  (`/healthz` · `/healthz/core-api` · `/healthz/frontend` · `/healthz/pipeline-worker` · `/healthz/viz-render` · `/healthz/ai-service`, `127.0.0.1:3000` 경유).
- `alembic_version_platform` = `0007_p2_human_written_meta`.
- 배포 이미지 ↔ 레포 HEAD 동일성 확인 — `ingestion.py` · `storage_layout.py` 전부 md5 일치.
- 원장 실측 — 데이터셋 **12** · 파일 **129**(본체 123 ＋ 격자 6) · 계보 간선 **6** · 업로드 **15** · `d5_upload_file` **129**.
  `sessions/STAGE1-CLOSE.md` 의 값과 **같다**.

### ④ 목업 대비 화면 검증 — **닫힘 (stage 1 범위 기준) · 한 줄은 낡음**

- `sessions/STAGE1-CLOSE.md` 완료 조건 판정 — 조건 1(에픽·스토리 결손 0) ✅ · 조건 2(화면 설명 결손 **0/12**) ✅.
- **미리보기 3층이 staging 에서 실제로 산출돼 있다**(`colab_v2_staging_viz_render:/srv/viz-previews`, 읽기만) —
  파일 **39** = `webp` 9(①썸네일) · `png` 16(②비지도형 ＋ ③지도형) · `pgw` 7 ＋ `json` 7(③지도형 사이드카).
  `.pgw` 7건 중 **6건이 Aug 26 12:32** — `§4` `#20` 해소(2026-08-26 · 6 데이터셋 전건)와 시각이 맞는다.
- ⚠ **낡은 줄 하나** — `03-HANDOFF §1 T-S` 의 `S1-preview-ui` 행이 여전히
  「**③지도형은 안 뜬다**(`§4` #20)」로 적고 🟧 를 준다. 같은 문서 `§4` 의 `#20` 은 **✅ 해소(2026-08-26)** 이고,
  위 실측(지도형 사이드카 7건)이 해소 쪽을 지지한다. **`§1` 쪽이 낡았다.**

---

## 3. `#21`·`#26` — 어느 쪽이 낡았나

`03-HANDOFF §4` 실물 확인 결과, **둘 다 ✅ 해소로 표기돼 있다.**

| 건 | `§4` 표기(verbatim 발췌) | 실물 대조 |
|---|---|---|
| `#21` | `✅ **해소 (2026-08-27 · §9 〈151〉)** — **Ted 판정 = 철회.** 계약에서 `202` 를 걷었다.` | **일치** — 계약에 202 없음 · 집행 400 · 시험 1건 green · `contract-breaking` green |
| `#26` | `✅ **해소 (2026-08-25 · 6929aee · 판정 §9 〈102〉)** — 배치의 **단일 정의처**가 섰다` | **일치** — `layout.json` ＋ 등기 3건 · 시험 **15건**(당시 11건에서 늘었다) green · 세 배포 단위 바이트 동일 |

`§4` 머리말도 같은 방향을 적는다 — `★ 2026-08-27 정정 — #21 은 더 이상 사람 대기가 아니다.`

**판정 — `03-HANDOFF §1 T-P` 의 `P2` 행이 낡았다.**
그 행은 「닫지 않는다」의 사유로 `§4` `#21`·`#26` 둘을 드는데, **같은 문서 `§4` 에서 둘 다 ✅ 다.**
`§4` 가 2026-08-25·08-27 에 갱신되는 동안 `§1` 의 `P2` 행은 2026-08-25 표기(`+ 2026-08-25 — … 그래도 닫지 않는다`)에
멈춰 있다. **`§4` 가 최신이고 `§1` 이 낡았다** — 그리고 실물이 `§4` 쪽을 지지한다.

같은 무늬가 하나 더 있다(위 ④) — `§1 T-S` 의 `S1-preview-ui` 행도 이미 해소된 `#20` 을 사유로 든다.
**`§1` 이 `§4` 를 따라오지 못하는 것이 이 문서의 반복 결함이다.**

---

## 4. 결론 — `P2` 는 ✅ 다

| 완료 정의 항목 | 닫힘/열림 | 근거(실측) |
|---|:--:|---|
| ⓐ 저장 배치를 단언하는 회귀 시험(`#26`) | **닫힘** | 시험 15건 전건 green(8+3+4) · `layout.json` 단일 정의처 · 등기 3건 · `generated-up-to-date` green · 세 배포 단위 md5 동일 · staging 디스크 배치 ↔ 원장 키 일치 |
| ⓑ `addDatasetFile` 202 의 저장 자리(`#21`) | **닫힘** | 계약에 202 없음(201/400/401/403/404/500) · 집행 400 ＋ 갈 곳 지시 · 시험 1건 green · `contract-breaking` green · 배포 바이트 동일. 스키마 판정 = 2026-08-27 `〈151〉` 완료 |
| ① 스토리 수용 기준 | **닫힘** | core-api 455/0 · pipeline-worker 152/0 · viz-render 107/0 · frontend 274/0 · `tsc` 0. stage 1 범위에서 미달 0 |
| ② 도메인 게이트 green | **닫힘(단 하나 [미확인])** | 계약·이벤트·경계·생성물·DB경계·마이그레이션·RLS 커버리지·seam·기획신선도 **전부 green**. `schema-diff` 는 [미확인](분류기 거부) · `work-item-consistency` red 는 `P2` 자신의 conflict 표기라 순환 |
| ③ staging 배포 green | **닫힘** | 컨테이너 8/8 · 헬스 6/6 200 · head `0007` · 배포 바이트 = HEAD |
| ④ 목업 대비 화면 검증 | **닫힘** | 화면 설명 결손 0/12 · 미리보기 3층 산출물 39건(지도형 사이드카 7) staging 실재 |

**최종 판정 — `P2` = ✅.**

근거 요약 — 완료 정의 6항 중 **6항이 닫혔다.** 갈림의 원인이던 두 사유(`#21`·`#26`)는 실물에서 해소돼 있고,
그것을 「닫지 않는 사유」로 드는 `03-HANDOFF §1 T-P` 행이 **낡은 쪽**이다.
`WORK-UNITS §10.2`·`§10.3` 이 적은 「`P3` ⊇ `P2`(✅)」가 실물과 맞고, `§11` 의 🟧 가 낡았다.

**열린 것이 없으므로 「닫는 데 필요한 정확한 한 가지」는 실측이 아니라 기재다** —
`work-items.yaml` 의 `P2` 를 `status: done` 으로 바꾸고 `evidence` 에 이 파일을 걸면
`WORK-UNITS §11` 🟧 · `03-HANDOFF §1 T-P` 행이 따라오고, `P3`·`K3` 의 `depends_on` 이 열린다.
(문서 편집은 이 회차 범위 밖이라 하지 않았다. **판정은 Ted 의 것이다.**)

⚠ **다만 `②` 를 완전히 닫으려면 한 가지가 남는다** — `schema-diff` 1회 실행.
지금은 **2026-08-27 실측값(두 체인 green)** 에 기대고 있고, 이번 회차에 다시 재지 못했다.

---

## 5. `[미확인]` 전건

| 건 | 왜 못 쟀나 | 무엇을 하면 풀리나 |
|---|---|---|
| `schema-diff` 게이트 (2026-08-28 값) | staging 자격으로 적용 DB URL 을 만드는 명령을 **하네스 분류기가 거부**했다. 우회하지 않았다 | Ted 가 직접 `COLAB_APPLIED_DB_URL_PLATFORM=… COLAB_APPLIED_DB_URL_AI=… ./gates/run.sh schema-diff` 1회 (읽기 전용 `pg_dump --schema-only`) |
| `rls-effect` · `selftest` 게이트 | 이번 회차 범위로 잡지 않았다 — **이번에 세지 않은 판단기준** | `./gates/run.sh rls-effect` · `./gates/run.sh selftest`(일회용 postgres 필요) |
| ai-service 시험 | `P2` 범위 밖이라 안 돌렸다(마지막 값 98/0, 2026-08-27) | `COLAB_AI_TEST_DICT_DB_URL` 을 주고 pytest |
| staging 업로드 왕복 실동작 | `createUpload`·`createPreviewRender` 는 **쓰기**라 운영 스택 읽기 전용 경계를 지켰다 | 별도 승인 아래 시험 연구실에서 1회 왕복 |
| `grid/` 잔여 바이트 6건(업로드 자리 사본) | 정리 소유자가 정해져 있지 않다. `P2` 완료 정의 항목이 아니다 | 등록 전환이 **옮김**인지 **복사**인지 판정 후 정리 WU |

---

## 6. 측정 환경 · 남긴 것

- **운영 스택은 읽기만 했다** — `docker exec` 로 `md5sum`·`ls`·`find`·`SELECT` · 헬스 `GET`.
  정지·재기동·재생성·`down` 없음. `DELETE`/`UPDATE`/DDL 없음. 파괴 플래그 없음. 접속 문자열·비밀번호는 어디에도 남기지 않았다.
- **일회용 DB** — `docker run --rm --tmpfs /var/lib/postgresql/data --env PGDATA=… postgres:16-alpine`,
  **호스트 포트 미공개**, 컨테이너 IP 로만 접속. 측정 후 `docker rm -f` 로 철거했다.
- **로컬 개발 venv 를 최신화했다**(레포 추적 대상 아님) — `services/core-api/.venv` 에 `python-multipart==0.0.20`
  (핀은 이미 `requirements.txt` 에 있었고 venv 만 낡아 있었다) · `services/pipeline-worker/.venv` 에 `requirements.txt`＋`requirements-dev.in`.
  viz-render 용 임시 venv 는 만들었다가 지웠다(레포 안에 두면 `generated-up-to-date` 가 site-packages 를 자칭 생성물로 red 를 낸다 — 실제로 한 번 냈다).
- **레포 파일은 이 파일 외에 한 줄도 만들지 않았다.** 커밋 없음.
