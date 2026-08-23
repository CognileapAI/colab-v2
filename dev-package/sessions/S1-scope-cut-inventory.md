# S1 범위 축소 — 폭발 반경 인벤토리

**작성** 2026-08-24 · 조사 전용 세션(워크트리 `p2-exec`, HEAD `a868d64`) · **소스 무수정 · 커밋 0 · staging 무접촉**

**전제(메인 세션이 준 것, 이 문서가 판정하지 않는다)**
- stage 1 = **데이터 업로드 · 데이터셋 인포 · AI 기반 검색 · 연구실-프로젝트-데이터셋 · 계보 설정**.
- **가공(데이터 처리) · 가시화(미리보기 포함) · 데이터 확인·검증류**는 빠진다.
- **D5 는 포맷 감지(매직바이트)까지만.** 헤더 파싱(포맷·변수·기간·좌표계·격자) · 좌표 변환 · COG 변환 · 이미-COG 3부류 판별은 stage1 밖.
- **가시화 계열은 「휴면」** — 코드는 남기고 배포 단위·화면·완료 정의에서만 뺀다.

**이 문서의 성격** — 계측과 의존 지도다. 철거를 권고하지 않는다. 처리 방식이 갈리는 자리는 두 안을 비용과 함께 병기했다.
EVIDENCE(관측)와 INTERPRETATION(잠정)을 절마다 갈라 적었다. 관측하지 않은 수는 `[미측정]` 이고 이유를 붙였다.

---

## 0. 이 워크트리에서 실제로 돌린 것 (기준선)

### EVIDENCE

| 대상 | 명령 | 결과 |
|---|---|---|
| pipeline-worker | `services/pipeline-worker/.venv/bin/python -m pytest -q` | **72 passed · 17 failed · 9 errors** (수집 98) |
| viz-render | `services/viz-render/.venv/bin/python -m pytest -q` | **42 passed · 6 failed** (수집 48) |
| frontend | `npx vitest run` | **147 passed · 1 failed** (총 148, 파일 7) |
| core-api | — | **[미측정]** — `services/core-api/` 에 venv 가 없고(`ls -a` 확인) DB 도 없다. 아래 수는 `grep -c '^def test_'` 정적 계수다 |
| `banned-import` | `bash gates/run.sh banned-import` | **green** — .py 90건(core-api 35 · pipeline 24 · viz 24 · ai 7), 금지 import 0 |
| `import-boundary` | `bash gates/run.sh import-boundary` | **green** — 계약 8건 전부 KEPT |
| `seam-consistency` | `bash gates/run.sh seam-consistency` | **green** — G-e 258건 · G-b 7건 · ㉠ 0건 · ㉡ 15단계(이월 1) |

**실패의 정체 (green-by-skip 금지 설계의 정상 동작이다)**
- pipeline 17 failed = `test_e2e_real.py`(6) · `test_axis_detect_real.py`(5) · `test_tiff_classes_pipeline_real.py`(5) · `test_grid_canonical_nc.py`(1) — 전부 `Failed: COLAB_REFERENCE_DATA 가 원천 디렉터리를 가리키지 않는다 — E2E 는 skip 하지 않는다`.
- pipeline 9 errors = `test_outbox_db.py` 등 — `Failed: COLAB_PIPELINE_DB_URL 가 없다`.
- viz 6 failed = `test_e2e_real.py` — 같은 `COLAB_REFERENCE_DATA` 사유.
- **frontend 1 failed 는 성격이 다르다** — `test/upload.test.tsx > §8 등록 결정 게이트 > `보기만 할게요` 는 아무것도 등록하지 않는다 — `createDataset` 0회` (`test/upload.test.tsx:544` `expect(calls.register).toBe(0)`). **원천 데이터·DB 와 무관한, 이 워크트리에서 이미 red 인 시험**이다.

### INTERPRETATION (잠정)
- 범위 축소 이전에 **FE 에 이미 red 가 하나 있다.** 축소 작업을 시작하면 이 red 가 축소 탓으로 오인될 수 있으니, 착수 전에 원인을 따로 못 박아 두는 편이 낫다.
- core-api 를 못 돌린 것이 이 인벤토리의 가장 큰 계측 공백이다. B절의 core-api 관련 판정은 **코드·시험 파일 읽기에 근거한 추론**이지 실행 결과가 아니다.

---

## A. 범위 밖으로 떨어지는 것 — 무엇이 얼마나 있고 무엇이 그것에 매달려 있나

### A-1. `services/viz-render/` — 배포 단위 통째

#### EVIDENCE
- 파일 계수(`wc -l`, `.venv`·`__pycache__` 제외): **src 1,809줄 · tests 909줄 · 의존 핀 61줄 = 2,779줄.**
- src 내역 — `domains/d7_visualization/` 8모듈 1,186줄(`readers.py` 341 · `jobs.py` 234 · `raster.py` 145 · `hsr.py` 122 · `grid.py` 117 · `tiles.py` 89 · `palettes.py` 82 · `failures.py` 56), `app/routes/renders.py` 146, `app/routes/style.py` 20, `ports/source.py` 104, `kernel/{config,errors,ids,signing}` 215, `app/{main,deps}` 123.
- 시험 **48건**(파일 8): `test_tile_signature.py` 10 · `test_errors.py` 8 · `test_render_flow.py` 8 · `test_e2e_real.py` 6 · `test_hsr_and_grid.py` 6 · `test_upload_target_and_partial.py` 5 · `test_palettes.py` 3 · `test_unconfigured.py` 2.
- 이 단위에 매달린 것 — ① `gates/config/boundaries.toml:25-29` `[units.viz-render]` ② `gates/config/importlinter.ini:15` `root_packages` 의 `colab_viz` 와 `:92-99` `viz-layers` 계약 ③ `infra/staging/compose.i2.yml:104-114` 컨테이너 ④ core-api 의 중계 2 op.
- **파이썬 import 로 매달린 것은 0건이다** — `import-boundary` 의 `units-independent` 계약(`importlinter.ini:22-29`)이 배포 단위 간 import 를 금지하고 green 이다.

#### INTERPRETATION (잠정)
- viz-render 는 **HTTP seam 하나로만 붙어 있다.** 휴면 처리의 비용이 가장 낮은 덩어리다.
- 다만 `boundaries.toml`·`importlinter.ini` 가 **패키지 실재를 전제**한다(B-2). 「휴면」이 「삭제」로 미끄러지면 게이트 두 개가 즉시 red 다.

### A-2. core-api 의 미리보기 중계

#### EVIDENCE
- `services/core-api/src/colab_core/app/routes/preview.py` **100줄 전부** — `createPreviewRender`(`:47`) · `getPreviewRender`(`:81`).
- `services/core-api/src/colab_core/ports/relay.py:21-29` `PreviewRenderPort` Protocol (약 11줄).
- `services/core-api/src/colab_core/app/relay.py` — **139줄 중 미리보기 전용은 `HttpPreviewRelay`(`:58-79`) 약 22줄뿐**이다. 같은 파일의 `:81-96 honest_empty_suggestions` · `:98- HttpLineageSuggestionRelay` 는 **AI 계보 제안용이고 stage1 안에 남는다.** `_request`(`:32`)·`_scope_headers`(`:52`)·`RelayUnavailable`(`:28`)은 **두 중계가 공유**한다.
- `services/core-api/src/colab_core/app/main.py:42-43` — `app.state.previews = HttpPreviewRelay(...) if settings.viz_base_url else None`. `:44-46` 은 ai 중계를 **주소가 없어도 세운다**(주석: 「AI 가 없다」가 「업로드를 못 한다」가 되면 안 된다).
- `services/core-api/src/colab_core/kernel/config.py:30` `COLAB_CORE_VIZ_BASE_URL`, `:40 viz_base_url`, `:70`.
- 시험 `services/core-api/tests/test_preview_relay.py` **212줄 · 10건**. 그중 `test_no_geo_library_is_imported_anywhere_in_core_api`(`:189`)는 **미리보기와 무관한 §3-4 음성 시험**이고, `test_when_the_render_server_is_unreachable_registration_still_works`(`:169`)는 **등록 쪽 보장**이다.

#### INTERPRETATION (잠정)
- **`relay.py` 를 파일 단위로 다루면 안 된다.** 미리보기와 AI 계보 제안이 같은 파일에서 배관을 공유한다. 파일째 휴면시키면 `listUploadLineageSuggestions`(stage1 안)가 같이 죽는다.
- `test_preview_relay.py` 10건 중 최소 2건은 **범위 밖으로 같이 옮기면 안 되는 시험**이다 — 하나는 geo 금지 음성 시험, 하나는 「그릴 수 없는 것과 등록할 수 없는 것은 다르다」의 유일한 실동작 증명이다.

### A-3. FE — S-08 미리보기 화면 · S-04 의 미리보기 부분

#### EVIDENCE (`wc -l`)
| 자리 | 줄 |
|---|---|
| `frontend/src/routes/UnregisteredPreviewPage.tsx` | 142 |
| `frontend/src/components/preview/` 8파일 | 798 (`PreviewPanels.tsx` 180 · `preview.css` 174 · `usePreviewRender.ts` 149 · `previewSource.ts` 94 · `types.ts` 81 · `handoff.ts` 57 · `PreviewControls.tsx` 50 · `tiles.ts` 13) |
| **S-08 소계** | **940** |
| `frontend/src/components/upload/PreviewPanel.tsx` | 216 |
| `frontend/src/components/upload/previewSource.ts` | 44 |
| **S-04 미리보기 소계** | **260** |

- 시험 — `test/preview.test.tsx` 390줄 **23건**(단독 실행 `23 passed` 확인). `test/upload.test.tsx` 51건 중 미리보기 축은 **`describe §8 미리보기`(`:367-524`) 9건** + **`describe §8 등록 단계 배치 — 미리보기는 등록 내내 접히지 않는다`(`:644-692`) 4건** = **13건**, 그리고 경계에 걸친 **`describe §8·§9 기준 격자 없음 — 그릴 수 없는 것과 등록할 수 없는 것은 다르다`(`:336-366`) 3건**.
- 라우트 등록 — `frontend/src/app/routes.tsx:11` import, `:22` `<Route path="/datasets/preview/:uploadId" .../>`.
- S-04 안의 사용처 — `UploadModal.tsx:16` import, `:213` `<PreviewPanel ... hasReferenceGrid={hasReferenceGrid} />`; `UploadEntry.tsx:13` `apiPreviewSource`.

#### INTERPRETATION (잠정)
- **S-08 은 미리보기 화면이면서 등록 진입 경로이기도 하다.** `components/preview/handoff.ts:20` 이 `REGISTER_FROM_PREVIEW_STATE_KEY = 'openUploadForRegister'` 를 정의하고 주석이 「S-08 에서 `연구실에 등록 →` 을 눌렀을 때 목록 화면에 실어 보낸다(정본 §7.2 「모달을 다시 열고 등록 단계까지 펼친다」)」라 적었다. S-08 을 화면에서 빼면 **등록 진입 경로 하나가 함께 사라진다.** 그 경로가 stage1 에서 대체되는지는 정본 판정 사항이다.
- S-04 쪽은 **레이아웃 앵커**다 — `UploadModal.tsx:213` 의 `PreviewPanel` 바로 아래(`:220-` 「등록 결정 게이트」)에 등록 버튼이 붙는다. 패널만 빼면 등록 게이트는 그대로 서지만 **`describe §8 등록 단계 배치`(4건)는 검사 대상 자체가 없어진다.**

### A-4. `services/pipeline-worker/src/colab_pipeline/d5/` — 매직바이트 너머

#### EVIDENCE (`wc -l`)
| 모듈 | 줄 | stage1 |
|---|---|---|
| `detect.py` | 124 | **안** — 매직바이트 감지 |
| `formats.py` | 11 | **안** — 값 집합 |
| `events.py` | 185 | **안(부분)** — 7종 봉투. `STAGE_ORDER`(`:31-37`)가 5단계 전부를 담는다 |
| `lineage.py` | 31 | 안(계보 기여) |
| `axis.py` | 253 | **밖(그러나 C-1 참조)** — 컨테이너 변수명·값범위·쌍정합으로 축 판별 |
| `parse.py` | 132 | 밖 — 헤더 파싱 |
| `grid.py` | 143 | 밖 — 기준 격자 |
| `hsr.py` | 120 | 밖 — Binary 헤더 디코드 |
| `cog.py` | 111 | 밖 — COG 변환 |
| `tiff_probe.py` | 83 | 밖 — 이미-COG 3부류 |
| `renderable.py` | 26 | 밖 — 렌더 가능 판정 |
| `pipeline.py` | 181 | 밖(오케스트레이션) — 파일 머리 「감지 → 파싱 → 좌표 → COG」 |
| `domains/d5_ingestion.py` | 452 | **혼합** — 단계 오케스트레이션 + outbox 원장 + 릴레이 + reaper |

- **범위 밖 모듈 합계 = 1,049줄**(axis·parse·grid·hsr·cog·tiff_probe·renderable·pipeline). 감지 축(detect+formats) = 135줄.
- 시험 98건의 배정 — 밖 전용 **62건**: `test_axis_detect.py` 11 · `test_grid_and_hsr.py` 8 · `test_pipeline.py` 6 · `test_e2e_real.py` 6 · `test_axis_detect_real.py` 5 · `test_grid_canonical_nc.py` 5 · `test_renderable.py` 5 · `test_tiff_classes_pipeline_real.py` 5 · `test_cog_classify.py` 4 · `test_worker_creates_grid_row.py` 4 · `test_grid_combined_nc.py` 3. 안/혼합 **36건**: `test_outbox_db.py` 9 · `test_detect.py` 8 · `test_worker_events.py` 8 · `test_events.py` 7 · `test_reaper_skips_processing.py` 4.
- `domains/d5_ingestion.py:19-34` 가 `axis`·`detect`·`events`·`pipeline`·`renderable` 을 한꺼번에 import 한다.

#### INTERPRETATION (잠정)
- `domains/d5_ingestion.py` 는 **가르는 자리가 파일 안에 있다.** 파일 단위 휴면이 불가능한 유일한 파이썬 모듈이다.
- `test_worker_events.py` 는 이름과 달리 순수 인프라가 아니다 — 수집 목록에 `test_resolved_grid_axes_are_written_as_two_booleans` 가 있다. 축이 휴면하면 이 시험도 함께 움직인다.

---

## B. 휴면시키면 무엇이 깨지나

### B-1. 시험 — 서비스별 계수

#### EVIDENCE
| 서비스 | 총 | 범위 밖을 실행하는 시험 | 남는데 영향받는 시험 |
|---|---|---|---|
| viz-render | 48 (42 pass · 6 real-data red) | **48 전부** | 0 (다른 단위가 이 코드를 import 하지 않는다) |
| pipeline-worker | 98 (72 pass · 17 real-data red · 9 DB error) | **62** | `test_worker_events.py` 8 · `test_outbox_db.py` 9 중 축·격자 행을 다루는 것들 (`test_worker_creates_the_grid_file_row_that_acceptance_did_not` · `test_no_grid_row_is_created_when_the_axis_cannot_be_determined` · `test_axis_row_is_two_booleans_and_empty_axis_is_refused_by_the_db` — 셋 다 현재 DB 부재로 error) |
| core-api | 170 (정적 계수 · `[미측정]`) | `test_preview_relay.py` **10** | `test_not_implemented.py` **6 전부** · `test_route_table.py` **3** (아래) |
| frontend | 148 (147 pass · 1 pre-existing red) | `test/preview.test.tsx` **23** + `test/upload.test.tsx` **13** = **36** | `test/upload.test.tsx` `:336-366` **3건**(격자 없음 — 미리보기 문구와 등록 보장이 한 describe 에 있다) |

**core-api 에서 반드시 손대야 하는 자리 (`cat -n` 확인)**
- `tests/test_not_implemented.py:59-62` — `def test_the_24_unimplemented_operations_are_exactly_these` / `assert len(OPERATIONS) == 24`.
- 같은 파일 `:23-36` `P2_REAL` 표에 `"createPreviewRender": "tests/test_preview_relay.py"` · `"getPreviewRender": "tests/test_preview_relay.py"` 가 **이름으로 박혀 있고**, `:65-73` `test_every_op_p2_took_out_has_a_behavioural_test_behind_it` 가 그 파일의 존재와 op 이름 포함을 검사한다.
- 같은 파일 `:76-80` `test_codes_are_the_two_kinds` / `assert len(p1) == 15`.

#### INTERPRETATION (잠정)
- **미리보기 2 op 을 501 표로 되돌리는 순간 `test_not_implemented.py` 의 세 단언이 동시에 red 다.** 이건 사고가 아니라 설계다 — 이 시험은 「목록이 줄어드는 것이 진척의 계측」(`not_implemented.py:8` · `test_not_implemented.py:60`)을 강제하는 오라클이고, 표가 **늘어나는** 방향은 상정돼 있지 않다. 표를 늘릴 때 시험이 함께 개정된다는 사실을 결정 로그에 남기지 않으면, 다음 사람은 「시험을 고쳐 통과시켰다」로 읽는다.

### B-2. 게이트 — 어느 것이 red 로 가나

#### EVIDENCE (게이트 구현을 직접 읽었다)
| 게이트 | 코드가 무엇을 보나 | 휴면 시 |
|---|---|---|
| `seam-consistency` | `gates/tools/seam_consistency.py:66-120` `Registry` 가 **`contracts/seams/*.yaml` 과 `contracts/events/*.json` 만** 읽는다. G-e 는 계약 산문 ↔ 계약 객체, G-b 는 이벤트 `source: {const}` ↔ **seam 의 op 실재**, ㉡ 은 fixture ↔ 계약. **구현 코드를 보는 경로가 없다.** | **green 유지** — 계약을 안 고치는 한 코드가 휴면해도 이 게이트는 모른다 |
| `import-boundary` | `gates/config/importlinter.ini:12-16` `root_packages` 에 `colab_viz`. `:8-9` 주석: 「루트 패키지가 하나라도 없으면 import-linter 는 그래프를 만들지 못하고 실패한다 — 그게 의도다」 | **코드를 남기면 green · `colab_viz` 를 지우면 red** |
| `banned-import` | `gates/tools/banned-import.py:91-93` — 「검사할 .py 가 0건이면 red」. 단위별 deny 목록은 `boundaries.toml:25-29` | 코드를 남기면 green(관측: 90건 green). **`services/viz-render/src` 를 비우면 그 단위 대상 0건** |
| `contract-lint` / `contract-breaking` | `contracts/seams` 만 (`gates/run.sh:17-24`) | **green 유지** (계약 동결) |
| `event-lint` / `event-breaking` | `contracts/events` 만 (`gates/run.sh:26-35`) | **green 유지** |
| `generated-up-to-date` | `contracts/codegen/manifest.toml` 엔트리 1건 — `fe-core.yaml → frontend/src/generated/fe-core.ts` | **green 유지** — 계약이 안 바뀌면 생성물도 안 바뀐다 |
| `rls-coverage` / `rls-effect` | `gates/config/rls-allowlist.toml`. `d5_*` 3표는 allow-list 에 **없고** `0004:238-252` 가 ENABLE+FORCE+`lab_boundary` 를 걸었다 | **표를 남기면 green** — B-4 참조 |
| `schema-diff` | 선언 `db/*/schema.sql` ↔ 적용 DB | **`0004` 를 되돌리면 red**(적용 DB 와 선언이 갈린다) |
| `migration-single-head` | down_revision 그래프 | 영향 없음 |
| `*-selftest` 6종 | 자기 red fixture | 영향 없음 |
| `db-selftest` | DB 필요 | **[미측정]** — 이 워크트리에 DB 가 없다 |

#### INTERPRETATION (잠정) — **이 절이 이 인벤토리의 중심 결론이다**
1. **「코드는 남기고 화면·배포에서만 뺀다」를 문자 그대로 지키면 게이트는 한 개도 red 로 가지 않는다.** 게이트 전부가 계약 아니면 코드 실재를 보고, 둘 다 그대로이기 때문이다.
2. **red 는 「휴면」이 「삭제」로 넘어가는 순간에만 난다.** 문턱이 셋이다 — ① `colab_viz` 패키지 삭제 → `import-boundary` ② `services/viz-render/src` 비우기 → `banned-import`(단위 대상 0건) ③ `0004` 되돌리기 → `schema-diff`.
3. **`seam-consistency` 는 이 축소를 잡지 못한다.** 질문이 「계약이 선언한 op 이 구현돼 있나」였다면 잡았겠지만, 실제 구현은 「계약 산문이 계약 객체를 옳게 가리키나」다. **stage1 이 만드는 계약↔코드 괴리는 어느 게이트도 보지 않는다** — `gates/README.md:69-78` 이 스스로 적어 둔 한계와 같은 계열이다(「게이트를 만들었다는 사실이 이 계열이 닫혔다는 뜻이 아니다」).

### B-3. 동결 계약 — 501 은 몇이 되나

#### EVIDENCE
- `contracts/seams/fe-core.yaml` op **45건**(`grep -c operationId`), `core-viz.yaml` **5**, `core-ai.yaml` **2**.
- `services/core-api/tests/test_route_table.py:41-42` — `assert len(contract_operations()) == 45`. `:45-50` — 앱 라우트 표 ≡ 계약. **즉 45 op 은 전부 등록돼 있어야 하고, 미구현은 사라지는 게 아니라 501 표로 옮겨진다.**
- 현재 501 표 = `not_implemented.py:46-83` **24건**(NO_STORE 9 · P1 15). 실동작 = 45 − 24 = **21건**.
- stage1 에서 실동작 → 501 로 돌아가는 것: **`createPreviewRender` · `getPreviewRender` 2건**(`routes/preview.py:47`·`:81`).
- 신규로 범위 안에 드는 op: **0건.** 45 op 안에 AI 검색·인포·계보·프로젝트-데이터셋 관련으로 아직 501 인 것들(`listProjects` `getProject` `linkProjectDataset` `getDatasetLineage` `updateDataset` 등)은 원래 P1·P5 배정(`not_implemented.py:17-22`)이지 stage1 이 새로 여는 것이 아니다 — **이 판단은 배정 문서 기준이고, stage1 정의가 이들을 끌어오는지는 정본 판정 사항이다.**
- `core-viz.yaml` 의 5 op(`createRender` `getRender` `getRenderTile` `listPalettes` `createScreenshot`) 중 4개가 구현돼 있다(`services/viz-render/README.md:11-17`). 이들은 fe-core 45 표에 들어가지 않으므로 **501 수에 영향 없다.**

#### 결론
> **stage1 의 501 = 24 + 2 = 26.** 실동작 21 → **19.** 궤적은 25 → 36 → 24 → **26** 이다.

#### INTERPRETATION (잠정)
- **숫자가 처음으로 늘어난다.** `not_implemented.py:8` 「하나 구현할 때마다 이 표가 한 줄씩 줄고, 그 줄어듦이 진척의 계측이 된다」가 이 회차에 반증된다. 표의 의미를 「진척」에서 「현재 범위 밖」으로 다시 정의하지 않으면 26 은 퇴행으로 읽힌다.
- **26 은 하한이다.** 격자 파일 관련 3 op(`addDatasetFile` 의 격자 갈래 · `replaceDatasetGridFile` · `deleteDatasetGridFile`)의 처리 방향에 따라 **최대 28** 이 된다 — C-1 의 축 결합이 그 갈림길이다.

### B-4. DB — `0004` 가 만든 것 중 무엇이 범위 밖만 위한 것인가

#### EVIDENCE (`db/platform/versions/0004_p2_grid_axis_and_d5.py`, `cat -n` 확인)
- **`:107-109`** `d3_file.carries_lat` · `carries_lon` `boolean NOT NULL DEFAULT false`.
- **`:112-119`** CHECK 2종 — ㈎ `d3_file_grid_carries_an_axis`(기준 격자 파일 → 둘 중 최소 하나 true) · ㈏ `d3_file_body_carries_no_axis`(본체 → 둘 다 false).
- **`:123`** 옛 인덱스 `d3_file_one_reference_grid_per_dataset` DROP. **`:127-130`** 새 부분 유니크 2종.
- **`:136-160`** `d5_upload`(수명·ready·renderable·metadata_complete·실패 3열·`registered_at`) · **`:168-195`** `d5_upload_file`(축 2열 + 같은 CHECK 2종 `:183-186` + `detected_format` `:180-181`) · **`:199-235`** `d5_pipeline_event`(이벤트 7종 CHECK `:208-210` · source CHECK `:226-227` · 멱등 키 UNIQUE `:229`).
- **`:238-252`** 세 표 RLS ENABLE+FORCE+`lab_boundary`.
- **`:70-102`** upgrade 가 기존 격자 행이 1건이라도 있으면 **예외로 멈춘다.**
- `gates/config/rls-allowlist.toml:24`·`:32` — `d5_upload_file` 은 주석 처리(면제 아님), `:34` `d7_viz_source` 도 주석(아직 없는 표).

**범위 밖만 위한 것 = 사실상 없다.**
- `d5_upload` · `d5_upload_file` — `createUpload`(`routes/ingestion.py:157-182`)가 직접 쓴다. **stage1 의 업로드 그 자체다.**
- `d5_pipeline_event` — `upload.accepted`(core-api 발행, `ingestion.py:180-182`)의 유일한 저장처.
- `detected_format`(`0004:180-181`) — 매직바이트 결과 자리이므로 **stage1 안**이다. `ingestion.py:329-332` 가 등록 때 데이터셋의 포맷 칸으로 옮긴다.
- `carries_lat`/`carries_lon` — C-1.
- 범위 밖에만 봉사하는 열의 후보는 **`d5_upload.renderable`(`:146`) 하나**다 — `renderable.py`(26줄, 범위 밖)의 산출을 담는다.

**`0004` 는 이미 적용돼 있다.** 되돌리려면 `downgrade()`(`:255-272`)가 `d5_*` 3표를 DROP 하고 축 2열을 DROP 하며 옛 인덱스를 되살린다 — 즉 **적재된 업로드 원장이 사라지고, 옛 인덱스가 돌아오면 `.npy` 격자 쌍의 두 번째 파일이 다시 막힌다**(`:20-24` 가 그 시급성을 적은 자리). **되돌리기를 권고하지 않는다. 되돌리지 않으면 무엇이 남는지만 적는다** — 축 2열은 남고, CHECK 도 남고, 따라서 C-1 의 결합도 남는다.

#### INTERPRETATION (잠정)
- **`0004` 는 stage1 축소의 대상이 아니다.** 대상처럼 보이는 것은 축 2열뿐이고, 그것은 지울 수 있는 것이 아니라 **채울 사람이 사라지는** 문제다.

### B-5. 배포 — `compose.i2.yml` 과 8 컨테이너

#### EVIDENCE
- `infra/staging/compose.i2.yml:104-114` `viz-render` — `image: colab-v2/viz-render:i2`, 헬스체크 `GET http://127.0.0.1:8100/healthz` 200.
- **환경변수가 하나도 안 걸려 있다.** 이 파일 전체에서 `COLAB_VIZ_*` 는 **0건**(grep 확인). `services/viz-render/src/colab_viz/kernel/config.py:64-71` 이 읽는 `COLAB_VIZ_SOURCE_ROOT` · `COLAB_VIZ_SERVICE_TOKEN` · `COLAB_VIZ_TILE_SIGNING_SECRET` · `COLAB_VIZ_EXECUTION` 어느 것도 없다.
- **core-api 쪽도 마찬가지다** — `:79-81` 에 `COLAB_CORE_DATABASE_URL` 하나뿐이고 `COLAB_CORE_VIZ_BASE_URL`(`config.py:30`)은 없다. `main.py:42-43` 에 따라 **`app.state.previews = None`** 이고, `routes/preview.py:67-70`·`:89-91` 이 **503 `RENDER_UNAVAILABLE`** 을 낸다.
- viz-render 시험이 이 상태를 명시적으로 못 박아 뒀다 — `tests/test_unconfigured.py::test_헬스는_살아_있다` · `test_렌더_표면은_503_이지_통과가_아니다`, `tests/test_tile_signature.py::test_서명_비밀이_없으면_렌더_표면은_503_이다_통과가_아니다`.
- `compose.i2.yml:91` 주석은 pipeline-worker·viz-render·ai-service 를 여전히 **「아직 비어 있는 세 단위. liveness 만 대답한다」**로 적고 있다.

#### 결론
> **staging 에서 미리보기는 이미 휴면이다.** 컨테이너는 뜨고 `/healthz` 는 200 이지만 렌더 표면은 503 이고, core-api 는 중계를 아예 만들지 않는다. **stage1 축소는 배포에서 아무것도 끄지 않아도 이미 성립해 있다.**

#### INTERPRETATION (잠정) — 두 처리안
| 안 | 하는 일 | 비용 |
|---|---|---|
| **㉮ 컨테이너를 그대로 둔다** | compose 무수정. 헬스 8/8 유지 | 아무것도 안 하는 컨테이너가 이미지 5종에 남아 `DR-5`(`:i2` 고정 태그로 직전 이미지가 dangling — `03-HANDOFF:198`)의 관리 대상이 하나 더 유지된다. `03-HANDOFF:177` 의 「8개」 점검 문장이 그대로 참이다 |
| **㉯ `viz-render` 서비스 블록을 뺀다** | 컨테이너 8 → 7, 이미지 5 → 4 | `03-HANDOFF:53`·`:177` 의 「5개 단위」·「8개」가 즉시 거짓이 된다. 롤백 대칭(`compose.yml` ↔ `compose.i2.yml`, `:6-9`)을 다시 증명해야 한다. **게이트는 어느 쪽이든 green** |

### B-6. 이벤트 — 7종 중 무엇이 남나

#### EVIDENCE
- `contracts/events/core-pipeline.json` `$defs` 파싱 결과 타입 7종: `upload.accepted`(source `core-api`) · `file.format-detected` · `file.header-parsed` · `file.crs-normalized` · `preview.cog-built` · `upload.ready` · `upload.failed`(뒤 여섯은 `pipeline-worker`).
- `d5/events.py:20-28` `EVENT_TYPES` 가 같은 7종. `:31-37` `STAGE_ORDER` = format-detected → header-parsed → crs-normalized → cog-built → ready.
- `0004:208-210` 이 DB CHECK 로 같은 7값을 강제. `:226-227` `CHECK ((event_type='upload.accepted') = (source='core-api'))`.
- `domains/d5_ingestion.py:45-53` `_FAILURE_MAP` — 실패 사유가 단계별로 매핑돼 있고, 그중 4줄(`TIFF 구조 판독 실패`·`파싱 실패`·`좌표/격자 없음`·`COG 변환 실패`)이 범위 밖 단계를 가리킨다.

#### 결론
| 이벤트 | stage1 | 근거 |
|---|---|---|
| `upload.accepted` | **남는다** | core-api 가 낸다(`ingestion.py:180-182`). 유일한 파이프라인 입구 |
| `file.format-detected` | **남는다** | 매직바이트 감지 = stage1 안 |
| `file.header-parsed` | **휴면** | 헤더 파싱 |
| `file.crs-normalized` | **휴면** | 좌표 변환 |
| `preview.cog-built` | **휴면** | COG |
| `upload.ready` | **남는다(단, 의미가 바뀐다)** | 완료 신호가 필요하다 |
| `upload.failed` | **남는다** | 감지 실패는 stage1 안의 실패다 |

#### INTERPRETATION (잠정)
- **`upload.ready` 가 조용히 다른 뜻이 된다.** 지금 `STAGE_ORDER` 는 4단계를 지나야 ready 다. stage1 에서는 format-detected 다음이 곧 ready 이므로, **같은 이름의 이벤트가 「전부 처리됐다」에서 「포맷만 알아냈다」로 바뀐다.** 계약도 DB CHECK 도 이 변화를 잡지 못한다 — 타입 문자열이 같기 때문이다. **이 인벤토리에서 두 번째로 위험한 자리다.**
- `d5_upload.renderable`·`metadata_complete`(`0004:146-147`)가 영영 NULL 로 남는다. 계약이 3값(모름 포함)이라 거짓말은 아니지만, **「아직 모른다」와 「영영 안 잰다」가 같은 값으로 표현된다.**

---

## C. 남는 것을 떠받치고 있는 것 — 「가공처럼 보이지만 업로드·인포·계보가 요구하는 것」

### C-1. ⚠ 가장 위험한 결합 — 기준 격자 파일의 축

#### EVIDENCE (전부 `cat -n` 확인)
1. `0004:112-114` — `CHECK (kind <> '기준 격자 파일' OR carries_lat OR carries_lon)`. **축 없는 격자 행은 DB 가 거절한다.**
2. `0004:183-186` — `d5_upload_file` 에 **같은 CHECK 2종**. 원장에서도 막는다.
3. `routes/ingestion.py:169-172` — `createUpload` 는 `carries_lat=False, carries_lon=False` 로 접수한다. 주석: 「**축을 추측하지 않는다** — 격자 파일의 축은 파일을 읽는 쪽이 정한다(`〈66〉`)」.
4. `routes/ingestion.py:344-346` — `createDataset` 는 원장의 값을 **그대로 옮긴다**: `d3_catalog.insert_file(..., carries_lat=f.carries_lat, carries_lon=f.carries_lon)`.
5. `routes/ingestion.py:412-418` — `addDatasetFile` 은 `kind == GRID` 이면 **400 을 낸다.** 문구: 「기준 격자 파일의 축(위도·경도)은 서버가 파일에서 판별한다 — 그 판별 경로(pipeline-worker)가 아직 이 op 에 연결되지 않았다.」
6. **축을 채우는 유일한 코드가 `d5/axis.py` 다** — `domains/d5_ingestion.py:19` 가 `detect_axes_for_upload` 를 import 하고 `:253-257`·`:377-393` 이 원장에 UPSERT 한다. `:384` 는 `if not (carries_lat or carries_lon)` 이면 행을 만들지 않는다.
7. `axis.py:1-30` 이 밝힌 판별 신호 — **① 컨테이너 내부 변수명(.nc/HDF5 의 `lat`·`lon`) ② 값 범위 ③ 쌍 정합 ④ 이방성 ⑤ 파일명.** ①②③④ 는 **파일 내용을 읽는다.**
8. `〈69〉`(`PLAN-SoT.md:332`) — 「접수는 업로드와 본체 파일 행까지만 만들고, **기준 격자 파일 행은 워커가 감지 단계에서 축을 판별한 뒤 세운다**」.

#### 결론
> **stage1 이 헤더 파싱을 빼면 기준 격자 파일은 아무 경로로도 등록되지 않는다.**
> 접수는 축을 False 로 두고 → 워커가 안 채우고 → `d5_upload_file` CHECK 가 격자 행을 거절하고 → `addDatasetFile` 은 원래부터 400 이다. **막는 것은 코드가 아니라 이미 적용된 DB CHECK 다.**

`axis.py` 는 **가공(가시화·COG)이 아니라 등록의 전제**다. 「헤더 파싱」이라는 한 단어로 함께 빠지면, 빠지는 것은 미리보기가 아니라 **격자 파일 등록 능력**이다.

#### INTERPRETATION (잠정) — 두 처리안
| 안 | 하는 일 | 비용 |
|---|---|---|
| **㉮ `axis.py` 를 stage1 안에 남긴다**(「헤더 파싱」에서 예외로 뺀다) | 격자 등록 경로가 산다. 시험 `test_axis_detect*` 16건 + `test_worker_creates_grid_row` 4건이 범위 안에 남는다 | 「헤더 파싱은 stage1 밖」이라는 규칙에 예외가 하나 생긴다. `axis.py` 253줄은 `.nc`/HDF5 를 열어 변수명을 읽으므로 **헤더 파싱 기능을 부분적으로 유지**하는 것이고, 그 사실을 숨기면 안 된다 |
| **㉯ 기준 격자 파일을 stage1 범위 밖으로 선언한다** | 축 판별 전부 휴면. `addDatasetFile`(격자 갈래)·`replaceDatasetGridFile`·`deleteDatasetGridFile` 이 501 로 → **501 = 28** | `SEED-DATA` 의 `04.Lat_Lon_info` 격자 14건이 stage1 에서 올라가지 못한다. `〈57〉`(격자 14건을 ③→① 로 옮긴 결정)과 `〈58〉`·`〈66〉` 이 대상 없는 결정이 된다. **`0004` 는 그래도 되돌리지 않는다**(B-4) — 채우지 않을 열이 남는다 |

**어느 안이든 `0004` 는 손대지 않는다.** `〈69〉` 가 이미 「CHECK 를 상태로 조건화하면 축이 빈 격자 행이 합법이 되어 불변식이 약해진다」고 닫아 뒀다.

### C-2. 반드시 살아남아야 하는 것 — 목록

#### EVIDENCE + 결론
| 살아야 하는 것 | 어디 | 왜 |
|---|---|---|
| **`d5_upload` · `d5_upload_file` 원장** | `0004:136-195` | `createUpload`(`ingestion.py:176-179`)가 직접 쓴다. `〈64〉`-ⓐ 가 「등록 전 저장 없음」의 대상은 **D3** 라고 못 박았고, 원장이 없으면 `getUploadStatus` 가 읽을 자리가 없다 |
| **`d5_pipeline_event` outbox** | `0004:199-235` | `upload.accepted` 의 유일한 저장처. 봉투가 `source: core-api` 를 const 로 박았고 DB CHECK(`:226-227`)가 강제한다 |
| **`upload.accepted` 발행** | `ingestion.py:180-182` | 계약이 「파이프라인의 입구」로 선언한 이벤트. 감지만 남아도 입구는 필요하다 |
| **outbox 릴레이 · 워커 · reaper** | `domains/d5_ingestion.py`(452줄 중 원장·릴레이·reaper 부분) | reaper 는 `〈67〉`-㉠ 의 이행 제약이다 — 미등록 업로드 수명(24h)이 없으면 파일이 눌러앉는다. 「처리 중은 건너뛴다」 보장도 여기 있다(`test_reaper_skips_processing.py` 4건) |
| **`detect.py` + `formats.py`** | 135줄 | stage1 이 명시적으로 남긴 것 |
| **`events.py` 봉투 생성** | 185줄 | 남는 4종(`accepted`·`format-detected`·`ready`·`failed`)이 이 모듈을 쓴다 |
| **`app/relay.py` 의 공유 배관**(`:28`·`:32`·`:52`) + `HttpLineageSuggestionRelay`(`:98-`) + `honest_empty_suggestions`(`:81-96`) | core-api | **AI 계보 제안이 stage1 안**이다. `HttpPreviewRelay`(`:58-79`)만 떼야 한다 |
| **`d5_upload_file.detected_format`** | `0004:180-181` → `ingestion.py:329-332` | 데이터셋 인포의 「포맷」 칸이 여기서 온다 |
| **`carries_lat`/`carries_lon`** | `0004:107-130` | C-1 |

#### INTERPRETATION (잠정)
- **파이프라인 배포 단위 자체는 휴면 대상이 아니다.** 감지 + outbox + 릴레이 + reaper 가 stage1 안이고, 이것들이 `d5/` 13모듈 중 4개(detect·formats·events·lineage, 351줄)와 `domains/d5_ingestion.py` 의 절반쯤이다.
- **`〈64〉` 가 이 축소를 미리 방어해 뒀다** — 「원장은 D3 등재가 아니다」를 안 갈라 뒀다면, 「가공이 빠지니 `d5_*` 도 빠진다」는 오독이 곧바로 업로드를 죽였을 것이다.

---

## D. 거짓이 되는 문서 · 결정

### D-1. 결정 6건 (`PLAN-SoT.md §9`) — 무엇이 무효, 무엇이 생존, 무엇이 개정 필요

#### EVIDENCE (행 번호는 `dev-package/PLAN-SoT.md`)

| 결정 | 행 | stage1 에서 | 근거 |
|---|---|---|---|
| **`〈63〉`-㉮** (STOP-7 = P2 가 렌더를 안고 간다 · `P2-viz` 레인 신설) | 326 | **무효(moot)** | 신설한 레인의 산출 전체가 휴면 대상이다. ⚠ **advisor 가 이 흡수에 반대했고 Ted 가 흡수를 골랐다**는 기록(같은 줄)은 그대로 남는다 — 반대 근거가 사후에 다른 이유로 맞았다는 사실을 지우면 안 된다 |
| **`〈63〉`-㉯** (`NB-6` 이미-COG 정의 = 타일+오버뷰 둘 다) | 326 | **무효** — 이미-COG 3부류 판별이 범위 밖 |
| **`〈63〉`-㉰**(`DR-17` 격자 축 서버 판별) + ⓐⓑⓒⓓ | 326 | **C-1 에 달렸다** — ㉮ 안이면 **생존**, ㉯ 안이면 무효 |
| **`〈63〉`-㉱** (업로드 원장 읽기·쓰기 Port) | 326 | **생존** — stage1 업로드의 뼈대 |
| **`〈64〉`** (「등록 전 저장 없음」의 대상은 D3) | 327 | **생존 · 그 어느 때보다 필요하다** — C-2 |
| **`〈65〉`** (축 판별 실측 16/16 · 값범위 단독 배제 유권해석) | 328 | **C-1 에 달렸다.** ㉯ 안이면 「재고 채택했는데 쓰지 않는 규칙」이 남는다 |
| **`〈66〉`** (축 = 두 불리언 · HSR 정본 격자는 `.nc`) | 329 | **부분 생존.** 두 불리언은 `0004` 에 이미 박혀 되돌리지 않는다(**생존**). **HSR 정본 격자 `.nc` 이행은 무효** — HSR 디코드(`hsr.py` 120줄)가 범위 밖이다 |
| **`〈67〉`-ⓐ** (미등록 업로드 수명 24h · reaper 가 처리중을 건너뛴다) | 330 | **생존.** ⚠ **근거가 흔들린다** — 24h 의 논거가 「파싱 + COG 변환은 오버뷰 피라미드까지 쌓아 규모에 선형 이상으로 붙는다」였다. **파싱도 COG 도 없어지면 그 논거가 없어진다.** 값은 운영 설정이라 정본을 안 고치고 바꿀 수 있다 — `〈67〉` 이 숫자를 정본 밖에 둔 이유가 정확히 이런 날을 위한 것이었다 |
| **`〈67〉`-ⓒ** (`DR-8` 정본 포맷 표기 7자리) | 330 | **생존** — 표기 정정이라 범위와 무관 |
| **`〈68〉`** (타일 서명 URL · `COLAB_VIZ_TILE_SIGNING_SECRET`) | 331 | **무효** — 타일 경로 전체가 휴면 |
| **`〈69〉`-⑴** (접수는 격자 행을 안 만든다 · 워커가 축 판별 후 세운다) | 332 | **C-1 의 원인 자체다.** ㉮ 안이면 생존, ㉯ 안이면 「행을 세울 워커가 없다」로 **개정 필요** |
| **`〈69〉`-⑵** (`.nc` 정본 격자 이행을 P2 후속 레인에 배정) | 332 | **무효** — 배정된 일이 범위 밖이다. ⚠ **이 결정이 존재한 이유가 「결정은 났는데 코드에 안 닿은 채 닫히면 `DR-8` 이 방금 낸 실패와 같은 무늬」였다.** 범위 축소로 조용히 닫으면 그 무늬를 다시 만드는 셈이니, 무효 처리를 **명시적으로** 적어야 한다 |

**계수** — 6개 결정(〈63〉〈65〉〈66〉〈67〉〈68〉〈69〉) 안의 **판정 12갈래 중 5갈래 무효 · 4갈래 생존 · 3갈래 C-1 결론에 종속.**

#### INTERPRETATION (잠정)
- **〈66〉/〈69〉가 grid axes 를 다루니 헤더 파싱 영역이고 따라서 무효**라는 읽기는 **절반만 맞다.** 축 판별 자체는 헤더 파싱이지만, **그 산출은 D3 카탈로그의 NOT NULL 열이고 CHECK 가 요구한다.** 결정을 무효화해도 **DB 제약은 무효화되지 않는다.** 이것이 C-1 을 1번 위험으로 꼽은 이유다.

### D-2. 거짓이 되는 문장 — 파일:행

#### EVIDENCE

**`dev-package/03-HANDOFF.md`**
- `:8` — 「**다음 WU** → **P2**(업로드 S-04 · **미등록 미리보기 S-08** · 계보 확정)」. S-08 이 범위 밖이면 P2 의 정의 자체가 바뀐다.
- `:53` — 「5개 단위 전부 헬스 green(`.../viz-render, ...`), 컨테이너 7/7 healthy」. **처리안 ㉯ 를 택하면 거짓.**
- `:79` — D5 행. 완료조건 ②(이미-COG 3부류)·④(감지→파싱→좌표→COG 완주)가 범위 밖 조건이 된다.
- `:86` — P2 행의 「⛔ 새 멈춤 `STOP-7`」 서술 전체와 「11 op 이 501 로 등재」. **현재도 24 라 이미 낡았고**, stage1 에서 26 이 된다.
- `:108` — S2 완료 정의 「화면 경로(S-04→**파싱→COG**→계보 확정)로만」. **파싱·COG 가 없어진다.**
- `:160` — `STOP-7` 해소 줄 전체(「P2 가 렌더를 안고 간다 · `P2-viz` 레인 신설 · **데이터셋 상세의 2D 렌더 3종은 P3 그대로**」).
- `:177` — 「`docker ps` 에 `colab_v2_staging_*` **8개**(… viz_render …)」. 처리안 ㉯ 면 7개.

**`dev-package/WORK-UNITS.md`**
- `:34` — 완료 기준 2 의 화면 목록에 「**S-08 미등록 미리보기**」.
- `:40` — 완료 기준 7 「실파일이 업로드→**파싱→COG→시각화**→계보 확정까지 완주」. stage1 에서 관통 불가.
- `:140` — G4 의 「S-08 미등록 미리보기(P2 편입 권장)」.
- `:155` — **D5 정의 행 전체.** ⑶ 헤더 파싱 · ⑷ 좌표계 변환 · ⑸ COG 변환이 **stage1 밖**이 된다. ⑴(매직바이트)·⑵(포맷 목록)·⑹(outbox/워커)만 남는다. 완료 조건 ②·④ 도 같이 무효.
- `:167` — P2 행의 「**＋ 미리보기 최소 렌더 경로**(…)」 전체.
- `:168` — P3 행의 「**단 D7 의 미리보기 렌더 경로는 P2 로 빠져나갔다**」.
- `:175-179` — `〈63〉`-㉮ 반영 블록 5줄 전체(「D7 의 절단선을 P2 와 P3 사이에 다시 그었다」·「P3 은 이만큼 작아졌다」).
- `:242` — S2 행 「업로드 모달 S-04 → **파싱 → COG** → 계보 확정」.

**`dev-package/DOMAINS.md`**
- `:68` — D5 정의 「presigned multipart · **헤더 파싱** · 포맷 감지 · **좌표계 변환** · **COG** · outbox/워커」. **6항 중 3항이 범위 밖.**
- `:70` D7 정의 행 · `:122` 배포 단위 표의 `viz-render` 행 · `:154` E-03 의 「D7 (시각화)」 · `:181` 소유자 표의 D7 행. ⚠ **`WORK-UNITS.md:157` 이 「`DOMAINS.md` 의 D4·D6·D7·D8 은 경계 정의로서 그대로 유효하다」고 못 박아 뒀다** — 도메인 경계는 살고 **배정만 바뀐다**는 읽기가 가능하다. DOMAINS 를 고칠지 배정 문서만 고칠지는 판정 사항이다.

**`dev-package/PLAN-SoT.md §9`** — D-1 표 그대로(`:326`·`:328`·`:329`·`:330`·`:331`·`:332`).

**`gates/README.md`** — **거짓이 되는 줄은 없다**(B-2). 다만 `:69-78`(게이트가 못 하는 것)에 **「계약이 선언한 op 이 코드에 실재하는지는 아무 게이트도 안 본다」를 추가할 자리**가 생긴다 — 지금은 안 적혀 있다.

**서비스 README**
- `services/viz-render/README.md:8` — 「## 지금 구현된 것 — 미리보기 최소 렌더 경로 (WU-P2 · `〈63〉-㉮`)」와 이하 표(`:11-17`). 배포 단위가 휴면이면 「지금 구현된 것」이라는 표제가 오해를 만든다.
- `services/pipeline-worker/README.md:27-40` — 축 판별 절 전체(`〈63〉-㉰`·`〈65〉`·`〈66〉` 인용 + 신호 5행 표). C-1 결론에 달렸다. 특히 `:30` 「출력은 `carries_lat`·`carries_lon` 두 불리언이다」.

**세션 문서**
- `dev-package/sessions/P2-viz-report.md` · `P2-fe-preview-report.md` — **문서 전체가 범위 밖 산출의 보고서**다. 삭제 대상이 아니라 **「휴면」 표기 대상**이다(기록은 남아야 한다).
- `dev-package/sessions/P2-EXEC.md` — `W2 P2-viz` 레인 지시와 `§8` 위험 1번(advisor 반대).
- `dev-package/sessions/P2.md` — `§2-19`(501 이 줄어드는 것이 진척) · `§2-21`·`§2-22`(격자) · `§2-27`(원장).
- `dev-package/sessions/P2-pipeline-report.md` · `P2-W0-1-measurement.md` · `P2-W0-HSR-grid-measurement.md` · `P2-W0-R1-code-usage.md` — 축·격자 실측. C-1 결론에 달렸다.
- `dev-package/sessions/D5.md` — D5 완료 보고. ②④ 조건이 범위 밖이 된다.

**게이트 픽스처 (문서는 아니지만 사람 고정 자산이다)**
- `gates/fixtures/seam-consistency/e04-flow.json` — 15단계 중 **「헤더 파싱」·「좌표계 정규화」·「COG 변환」·「미리보기 렌더 (중계)」 4단계가 범위 밖**이 된다. **게이트는 green 을 유지한다**(계약만 보므로). 즉 **이 픽스처는 조용히 거짓이 된다** — 이 인벤토리에서 게이트가 못 잡는 자리 중 가장 눈에 안 띄는 곳이다.

#### INTERPRETATION (잠정)
- 거짓이 되는 문장의 **대부분이 「D7 을 P2 로 옮겼다」와 「D5 는 4단계다」 두 문장의 파생**이다. 두 원문(`WORK-UNITS.md:155` · `:175-179`)을 고치면 나머지는 인용 정정이다.
- **`03-HANDOFF.md:108`(S2 완료 정의)이 조용한 시한폭탄이다.** S2 는 P2 다음 차례이고, 그 완료 조건이 「S-04→파싱→COG→계보」인데 파싱·COG 가 없어진다. **S2 의 완료 정의를 stage1 에 맞춰 다시 쓰지 않으면 S2 는 착수하는 순간 도달 불가능한 조건 위에 선다.**

---

## E. 위험 순위 (INTERPRETATION, 전부 잠정)

1. **격자 축 ↔ `0004` CHECK**(C-1). 헤더 파싱을 빼면 **DB 가 기준 격자 파일 등록을 거절한다.** 코드 결정이 아니라 이미 적용된 제약이라 「나중에」가 안 된다. **결정 없이는 착수 불가.**
2. **`upload.ready` 의 의미 변화**(B-6). 이름이 같아서 계약·DB·게이트 전부 못 잡는다.
3. **`app/relay.py` 의 공유**(A-2). 파일 단위로 다루면 AI 계보 제안이 같이 죽는다.
4. **`test_not_implemented.py` 의 24 하드코딩**(B-1). 501 이 **처음으로 늘어난다**(24 → 26). 시험 개정이 은폐로 읽히지 않게 로그가 필요하다.
5. **`e04-flow.json` 과 S2 완료 정의**(D-2). 둘 다 green 을 유지하면서 거짓이 된다.
6. **휴면 → 삭제 미끄러짐**(B-2). `colab_viz` 삭제 = `import-boundary` red, `src` 비우기 = `banned-import` red, `0004` 되돌리기 = `schema-diff` red.

## F. 이 조사가 재지 못한 것 (`[미측정]`)

- **core-api 시험 170건의 실제 통과 여부** — venv 도 DB 도 없다. 정적 계수(`grep -c '^def test_'`)만이다.
- **`db-selftest` · `rls-coverage` · `rls-effect` · `schema-diff`** — DB 부재.
- **`contract-lint` · `contract-breaking` · `event-lint` · `event-breaking` · selftest 6종** — 도구(도커/네트워크)·시간 제약으로 안 돌렸다. **B-2 의 판정은 `gates/run.sh:17-40` 의 대상 선언과 각 도구 소스를 읽은 것이지 실행 결과가 아니다.**
- **원천 데이터가 필요한 시험 23건**(pipeline 17 · viz 6) — `COLAB_REFERENCE_DATA` 미설정.
- **staging 실측** — 접촉 금지 지시에 따라 안 했다. B-5 는 `compose.i2.yml` 과 코드를 읽은 결론이다.
