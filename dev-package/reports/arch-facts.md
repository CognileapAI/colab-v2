# arch-facts.md — CoLAB v2 ground-truth architecture evidence

> ## ⚠ 낡음 표시 (2026-08-29 종결 회차에 덧붙임)
>
> **이 문서는 `f06c995`(2026-08-29 낮) 시점의 레포를 수확한 것이고, 커밋된 시점의 `main` 은 그보다 여러 회차 앞이다**
> (기준 `c45da8f`). **정본이 아니다** — 값·근거의 정본은 `dev-package/PLAN-SoT.md §9`, 상태의 정본은
> `dev-package/work-items.yaml`, 서술의 진실원은 `dev-package/03-HANDOFF.md` 다.
>
> **내용의 정확성은 이 회차에서 검증하지 않았다 → `[미확인]`.** 푸는 법 = 인용된 `path:line` 을 현재 `main` 과 1:1 로
> 다시 대조한다. 그 사이에 이 문서가 그린 것과 실물이 갈린 것으로 **이미 아는 자리** — 별칭 재부착(`deploy.sh` ⑫ 이
> 고쳐졌다 · `9c6fc92`·`31f36a5`) · 계보 출처 레이블(`ai`·`manual`·`processed` 로 통일 · `12063d7`) ·
> 저장 규약의 산출물 종류 신설(`826c482`) · `createScreenshot`(`f06c995` 이후분).
>
> **남긴 이유** = 이 수확본이 없으면 다음 회차가 같은 조사를 처음부터 다시 한다. 낡았다는 사실을 문서 안에 드러내
> 두는 편이, 지우고 기억으로 되살리는 것보다 싸다.
>
> **함께 든 것** = `architecture-diagrams/` 의 도면 5종(자립형 HTML). **뺀 것** = 같은 산출의 `visual-check` PNG 20 개 ·
> `visual-check.json` 5 개 · `visual-check.html` 5 개. 뺀 근거 = **이 레포에 추적되는 바이너리가 0 건**이고
> (`git ls-files | grep -iE '\.(png|jpg|pdf|zip)$'` = 0), `.gitignore` 가 브라우저 자동화 산출물을 명시적으로 뺀다.
> PNG 는 도면 HTML 의 **QA 스냅숏**이지 산출물 자체가 아니다 — 원본 HTML 이 같은 것을 그린다.

---

> **Machine input for diagram authors.** Harvested 2026-08-29 from repo `main` @ `f06c995`.
> Every non-obvious claim carries a `path:line` citation, repo-root-relative.
> `UNVERIFIED:` marks anything not confirmed in code. **Do not add nodes/edges/states not listed here.**

**Repo root** — this repository checkout. ⭑ *(2026-08-29 종결 회차 정정 — 원문은 절대경로였다. `CLAUDE.md §3-8`「문서에 절대경로를 적지 않는다」위반이라 걷었다. 아래 인용은 전부 레포 루트 상대경로다.)*
**Domain model** 10 domains / 3 layers, 5 deploy units — `CLAUDE.md:38-52`, `dev-package/DOMAINS.md:121-123`
- 지식 D9 Ontology&KG · 추론 D10 AI Services · 기록 D1 Identity&Lab, D2 Access&Policy, D3 Catalog, D4 Lineage, D5 Ingestion&Pipeline, D6 Project, D7 Visualization, D8 Insight
- `core-api`=D1 D2 D3 D4 D6 D8 · `pipeline-worker`=D5 · `viz-render`=D7 · `ai-service`=D9 D10 · `frontend`
- Invariant: **no D10 → D4 write path exists** (AI proposes, humans commit) — `CLAUDE.md:57`, enforced by gate `ai-no-lineage-write`
- Invariant: D9/D10 storage has a **separate migration chain** from D1–D8 — `CLAUDE.md:59`

---

## 1. System topology

### 1.1 Node inventory — 9 runtime nodes (5 deploy units + 2 datastores + edge + storage volumes)

| Node | Kind | Language / framework | Entrypoint | Port | Citation |
|---|---|---|---|---|---|
| `core-api` | service | Python · FastAPI | `colab_core.app.main:create_app` | **8000** | `services/core-api/src/colab_core/app/main.py:15,36`; `services/core-api/Dockerfile:19,21` |
| `ai-service` | service | Python · FastAPI | `colab_ai.app.main:create_app` | **8200** | `services/ai-service/src/colab_ai/app/main.py:20,48`; `services/ai-service/Dockerfile:30,31` |
| `pipeline-worker` | worker (no web framework) | Python · plain loop + threading | `python -m colab_pipeline.app.worker` | **8000** (health only) | `services/pipeline-worker/Dockerfile:31,37,41`; `services/pipeline-worker/src/colab_pipeline/app/worker.py:274-286` |
| `viz-render` | service | Python · FastAPI | `colab_viz.app.main:create_app` | **8100** | `services/viz-render/src/colab_viz/app/main.py:10,24`; `services/viz-render/Dockerfile:45,46` |
| `frontend` | static SPA behind own nginx | React + TypeScript · Vite | `frontend/src/main.tsx` → `dist/` | **8080** | `frontend/vite.config.ts:1-9`; `frontend/Dockerfile:9,16`; `frontend/nginx.conf:4` |
| `postgres / colab_platform` | datastore | PostgreSQL | — | 5432 (no host port) | `infra/staging/db-bootstrap.sh:45-49` |
| `postgres / colab_ai` | datastore | PostgreSQL | — | 5432 (no host port) | `infra/staging/db-bootstrap.sh:45-49` |
| `nginx` (staging edge) | edge / reverse proxy | nginx | — | container **80** → host **127.0.0.1:3000** | `infra/staging/nginx.i2.conf:13`; `infra/staging/compose.i2.yml` nginx `ports:` |
| `cloudflared` | tunnel connector | Cloudflare Tunnel | — | — | `infra/staging/compose.i2.yml` (present in `compose.i2.yml` and `compose.yml`, absent from `compose.throwaway.yml:9-11`) |

**Storage nodes (Docker named volumes, not an object store):**

| Volume | Mounted by | Path | Citation |
|---|---|---|---|
| `uploads` | core-api (rw), pipeline-worker (rw), viz-render (**ro**) | `/var/lib/colab/uploads` | `infra/staging/compose.i2.yml` (`COLAB_CORE_UPLOAD_DIR`, `COLAB_WORKER_UPLOAD_DIR`, `COLAB_VIZ_SOURCE_ROOT`); default `services/viz-render/src/colab_viz/kernel/config.py:33,72` |
| `previews` | viz-render (rw), nginx (ro static) | `/srv/viz-previews` | `infra/staging/compose.i2.yml`; `infra/staging/nginx.i2.conf:69-74`; `services/viz-render/src/colab_viz/kernel/config.py:40,68` |

> **There is no S3/MinIO/object store.** PoC had MinIO (`dev-package/DEPLOY-CURRENT.md:27`) but that deployment is **torn down** (`dev-package/DEPLOY-CURRENT.md:3`). v2 uses shared Docker volumes only.

### 1.2 Message queue — **NONE. This is DB-polling with an outbox table.**

Evidence (all negative results are explicit, not assumed):
- `grep -rniE "redis|celery|rabbitmq|kafka|amqp|sqs" services/` → **no matches**
- No `LISTEN`/`NOTIFY` in `services/` or `db/`
- Worker loop is `while True: run_once(); time.sleep(5.0)` — `services/pipeline-worker/src/colab_pipeline/app/worker.py:268-271`
- The "publish" step is `stdout_publish()`, printing the envelope JSON to stdout; the transport is explicitly **not yet chosen** — `services/pipeline-worker/src/colab_pipeline/app/worker.py:21-24,64-69`
- Outbox table is `d5_pipeline_event` — `db/platform/schema.sql:579`
- Event envelope contract describes an outbox/worker structure, not a broker — `contracts/events/envelope.json`, `contracts/events/README.md:12-18`

**Diagram note:** draw core-api → `d5_pipeline_event` (write) and pipeline-worker → `d5_pipeline_event` (poll, 5s). Do **not** draw a broker/topic node.

### 1.3 Exposed routes

**core-api** — prefix `/api/v1` (`services/core-api/src/colab_core/app/main.py:31`), health `GET /healthz` unprefixed (`main.py:83-85`), routers mounted at `main.py:87-90`. 34 seam ops total; **22 implemented, the rest return 501** via `routes/not_implemented.py`.

| Route | Op | Citation |
|---|---|---|
| `POST /sessions` (201) | createSession | `routes/session.py:45` |
| `DELETE /sessions/current` (204) | endSession | `routes/session.py:72` |
| `GET /me` | getCurrentAccount | `routes/identity.py:15` |
| `GET /lab` · `PATCH /lab` | getLab · updateLab | `routes/identity.py:77,42` |
| `GET /lab/members` | listLabMembers | `routes/members.py:73` |
| `PUT /lab/members/permissions` | saveLabMemberPermissions | `routes/members.py:79` |
| `GET /datasets` | listDatasets | `routes/catalog.py:154` |
| `GET /datasets/{id}` | getDataset | `routes/catalog.py:490` |
| `PATCH /datasets/{id}` | **updateDataset** | `routes/catalog.py:420` |
| `GET /datasets/{id}/files` | listDatasetFiles | `routes/catalog.py:334` |
| `GET /datasets/facets` | listDatasetFacets | `routes/catalog.py:350` |
| `POST /dataset-searches` | searchDatasets | `routes/catalog.py:228` |
| `GET /dataset-field-suggestions` | listDatasetFieldSuggestions | `routes/catalog.py:201` |
| `POST /uploads` (201) | createUpload | `routes/ingestion.py:227` |
| `GET /uploads/{id}` | getUploadStatus | `routes/ingestion.py:290` |
| `GET /uploads/{id}/lineage-suggestions` | listUploadLineageSuggestions | `routes/ingestion.py:319` |
| `POST /datasets` (201) | createDataset | `routes/ingestion.py:384` |
| `POST /datasets/{id}/files` (201) | addDatasetFile | `routes/ingestion.py:509` |
| `POST /datasets/{id}/grid-files` (201) | attachUploadGridFiles | `routes/ingestion.py:554` |
| `PUT /datasets/{id}/files/{fileId}` | replaceDatasetGridFile | `routes/ingestion.py:653` |
| `DELETE /datasets/{id}/files/{fileId}` | deleteDatasetGridFile | `routes/ingestion.py:696` |
| `POST /datasets/{id}/lineage/parents` (201) | addLineageParent | `routes/lineage.py:117` |
| `DELETE /datasets/{id}/lineage/parents/{pid}` | removeLineageParent | `routes/lineage.py:156` |
| `POST /datasets/{id}/lineage/confirmation` | confirmLineage | `routes/lineage.py:173` |
| `GET /projects` · `POST /projects` (201) | listProjects · createProject | `routes/project.py:233,115` |
| `GET /projects/{id}` | getProject | `routes/project.py:307` |
| `PATCH /projects/{id}` | **updateProject** | `routes/project.py:69` |
| `PUT /projects/{id}/datasets/{dsId}` | linkProjectDataset | `routes/project.py:341` |
| `GET /preview-palettes` | listPalettes | `routes/preview.py:47` |
| `POST /previews` (202) | createPreviewRender | `routes/preview.py:73` |
| `GET /previews/{renderId}` | getPreviewRender | `routes/preview.py:107` |

**ai-service** — root-mounted, no prefix: `GET /healthz` (`main.py:67`), `POST /searches` (`main.py:71`). `suggestLineage` is **not implemented here** — `services/ai-service/src/colab_ai/app/main.py:1-4`.

**viz-render** — prefix `/viz/v1` (`main.py:19`), health unprefixed (`main.py:38`): `POST /renders` (202) `routes/renders.py:71`; `GET /renders/{id}` `routes/renders.py:120`; `GET /renders/{id}/tiles/{z}/{x}/{y}.png` `routes/renders.py:129`; `POST /screenshots` `routes/screenshots.py:60`; `GET /palettes` `routes/style.py:16`.

**pipeline-worker** — **no business HTTP routes.** Health server only — `services/pipeline-worker/src/colab_pipeline/app/health.py:42`, `worker.py:283-286`.

### 1.4 Inter-service edges (13 edges)

| # | Source → Target | Protocol | Concrete route / mechanism | Config env | Citation |
|---|---|---|---|---|---|
| E1 | browser → nginx | HTTPS/HTTP | `127.0.0.1:3000` → container 80 | — | `infra/staging/nginx.i2.conf:13` |
| E2 | nginx → frontend | HTTP proxy | `location /` → `http://frontend:8080` | — | `infra/staging/nginx.i2.conf:76-83` |
| E3 | nginx → core-api | HTTP proxy | `location /api/v1/` → `http://core-api:8000`; `client_max_body_size 8g`, `proxy_request_buffering off`, read/send timeout 600s | — | `infra/staging/nginx.i2.conf:46-63` |
| E4 | nginx → `previews` volume | static file | `location /previews/` → `alias /srv/viz-previews/`, `Cache-Control public,max-age=300` | — | `infra/staging/nginx.i2.conf:69-74` |
| E5 | nginx → all 5 units | HTTP health fan-out | `/healthz/core-api`→8000, `/healthz/pipeline-worker`→8000, `/healthz/viz-render`→8100, `/healthz/ai-service`→8200, `/healthz/frontend`→8080 | — | `infra/staging/nginx.i2.conf:24-43` |
| E6 | frontend → core-api | HTTP `fetch` (openapi-fetch) | `window.location.origin + '/api/v1'` | contract-fixed, no env var | `frontend/src/api/client.ts:8,13-16,18-22` |
| E7 | core-api → viz-render | HTTP (urllib), bearer | `POST {base}/renders`, `GET {base}/palettes`, `GET {base}/renders/{id}` | `COLAB_CORE_VIZ_BASE_URL`, `COLAB_CORE_VIZ_SERVICE_TOKEN` (both required or relay not built) | env `services/core-api/src/colab_core/kernel/config.py:96-99`; wired `app/main.py:69-71`; call `app/relay.py:82-100` |
| E8 | core-api → ai-service | HTTP (urllib) | `POST {base}/searches` (dataset search relay) | `COLAB_CORE_AI_BASE_URL` (optional; missing → `unavailable`/503) | env `kernel/config.py:100`; wired `app/main.py:77`; call `app/relay.py:196-224` |
| E9 | core-api → ai-service | HTTP (urllib) | `POST {base}/lineage-suggestions` (lineage relay) | `COLAB_CORE_AI_BASE_URL` (optional; missing → 0 results + degraded) | `kernel/config.py:100`; wired `app/main.py:74`; call `app/relay.py:252-273`. **Target endpoint does not exist in ai-service yet** — `services/ai-service/src/colab_ai/app/main.py:1-4` |
| E10 | core-api → `colab_platform` | DB (SQLAlchemy) | app role `colab_app` | `COLAB_CORE_DATABASE_URL` / `_FILE` | `services/core-api/src/colab_core/kernel/config.py:15,44`; role `infra/staging/db-bootstrap.sh:60-63` |
| E11 | pipeline-worker → `colab_platform` | DB (SQLAlchemy) | app role `colab_app`; poll every 5s | `COLAB_PIPELINE_DB_URL` / `_FILE` | `services/pipeline-worker/src/colab_pipeline/app/worker.py:51-54,250` |
| E12 | ai-service → `colab_ai` | DB, **SELECT only** | role `colab_ai_app`; never connects to `colab_platform` | `COLAB_AI_DB_URL` / `_FILE` | `services/ai-service/src/colab_ai/kernel/config.py:24-27`; `app/main.py:50-51`; role `infra/staging/db-bootstrap.sh:65-73` |
| E13 | core-api ↔ pipeline-worker | **indirect only** — shared `d5_pipeline_event` outbox table + `uploads` volume. No RPC. | — | — | `services/pipeline-worker/src/colab_pipeline/app/worker.py:113-160` |

**Non-edges (assert explicitly, do not draw):**
- `viz-render` has **no DB connection at all** — filesystem only, via `FilesystemSourcePort` — `services/viz-render/src/colab_viz/app/main.py:16,31`; `services/viz-render/ports/source.py:7-9`
- `ai-service` never touches `colab_platform` — `infra/staging/db-bootstrap.sh:65-73`
- No `core-api → pipeline-worker` direct call

### 1.5 Roles / DB boundary

| Role | Grants | Citation |
|---|---|---|
| `colab_owner` | LOGIN, NOSUPERUSER, **NOBYPASSRLS**; runs migrations | `infra/staging/db-bootstrap.sh:37-43` |
| `colab_app` | core-api + pipeline-worker app role on `colab_platform` | `infra/staging/db-bootstrap.sh:60-63`; `services/core-api/ops/app-role.sql` |
| `colab_ai_app` | **SELECT only**, `colab_ai` only | `infra/staging/db-bootstrap.sh:65-73` |

Host exposure: **only** `127.0.0.1:3000` on nginx. postgres, core-api, ai-service, viz-render, pipeline-worker, frontend publish **no host ports** — `infra/staging/compose.i2.yml`; asserted by `verify-deploy.sh:105-109` (0 bindings on `0.0.0.0`).

---

## 2. Data flow / lineage — upload → visualization

### 2.1 Storage path templates (single source of truth)

`contracts/storage/layout.json`, generated into all 3 services' `kernel/storage_layout.py` by `contracts/codegen/gen_storage_layout.py`:

| Key | Value | Citation |
|---|---|---|
| `uploadsPrefix` | `"uploads"` | `contracts/storage/layout.json:3` |
| `targetId` | `uploadId` **before** registration, `datasetId` **after** | `contracts/storage/layout.json:4` |
| `gridDirname` | `"grid"` | `contracts/storage/layout.json:5` |
| body key | `{uploadsPrefix}/{targetId}/{fileId}` | `contracts/storage/layout.json:7` |
| grid-file key | `{uploadsPrefix}/{targetId}/{gridDirname}/{fileName}` | `contracts/storage/layout.json:8` |

Concrete: `uploads/{uploadId}/{fileId}` → relocated to `uploads/{datasetId}/{fileId}` on registration.

### 2.2 The path, stage by stage

| # | Step | Actor | Mechanism | Citation |
|---|---|---|---|---|
| 1 | `POST /uploads` (createUpload, 201) | frontend → core-api | multipart `files` + `fileKinds` | `services/core-api/src/colab_core/app/routes/ingestion.py:227-229` |
| 2 | bytes written to disk | core-api | `_store()` → `path.write_bytes(payload)`; root from `_storage_root()` (`settings.upload_storage_dir` or per-process tempdir) | `routes/ingestion.py:64-72,44-57` |
| 3 | `d5_upload` + `d5_upload_file` rows inserted (`ready=false`) | core-api | INSERT | `db/platform/schema.sql:516,548` |
| 4 | `upload.accepted` outbox row → `d5_pipeline_event` | core-api | INSERT (outbox) | `db/platform/schema.sql:579-611`; event enum `services/pipeline-worker/src/colab_pipeline/d5/events.py:20-27` |
| 5 | **poll (5s)** | pipeline-worker | `serve(interval_seconds=5.0)` → `run_once()` → per-lab `_lab_pass()` | `worker.py:268-271,213-256,189-210` |
| 6 | pending set query | pipeline-worker | `ledger.pending_uploads(limit=BATCH=20)`; SQL `WHERE u.ready=false AND u.failed_at IS NULL AND EXISTS(...)` | `worker.py:113-160`; `services/pipeline-worker/src/colab_pipeline/domains/d5_ingestion.py:370` |
| 7 | process | pipeline-worker | `IngestionService.process_upload(work, stage1=True)` | `domains/d5_ingestion.py:144` |
| 8 | relay outbox | pipeline-worker | `relay_unpublished()` → `stdout_publish()` (**stdout, not a queue**) | `worker.py:189-210,64-69` |
| 9 | reap | pipeline-worker | `reap_expired_uploads()` — hard `DELETE FROM d5_upload` | `worker.py:189-210`; `services/core-api/src/colab_core/domains/d5_ingestion.py:118-124` |
| 10 | `POST /datasets` (createDataset, 201) — registration | frontend → core-api | sets `d5_upload.registered_at`, inserts `d3_dataset`, **relocates bytes** uploadId dir → datasetId dir | `routes/ingestion.py:384,439,445-453,486`; `_relocate()` `routes/ingestion.py:132-165` |
| 11 | lineage edges written | core-api | `d4_lineage.add_parent()` → `d4_lineage_edge` | `routes/ingestion.py:471-476` |
| 12 | lineage confirmed / unknown | core-api | `d3_catalog.confirm_lineage()` sets `d3_dataset.lineage_confirmed_at`; or `d4_lineage.mark_unknown()` → `d4_lineage_unknown` | `domains/d3_catalog.py:758-759` @ `routes/ingestion.py:477`; `domains/d4_lineage.py:196` @ `routes/ingestion.py:479` |
| 13 | `POST /previews` (202) | frontend → core-api | relayed to viz-render | `routes/preview.py:73` |
| 14 | `POST /renders` (202) | core-api → viz-render | `HttpPreviewRelay` | `app/relay.py:82-100`; `services/viz-render/src/colab_viz/app/routes/renders.py:71` |
| 15 | viz reads source | viz-render | `SourcePort.resolve()`, **filesystem adapter** over the storage-layout paths, `uploads` volume mounted `:ro` — **not the DB** | `services/viz-render/ports/source.py:1-11,44-46` |
| 16 | preview written | viz-render | `/srv/viz-previews` (`previews` volume) | `services/viz-render/src/colab_viz/kernel/config.py:40,68` |
| 17 | preview served | nginx | `/previews/` static alias | `infra/staging/nginx.i2.conf:69-74` |

### 2.3 pipeline-worker stages

Canonical `STAGE_ORDER` (5 stages) — `services/pipeline-worker/src/colab_pipeline/d5/events.py:29-35`:
```
file.format-detected → file.header-parsed → file.crs-normalized → preview.cog-built → upload.ready
```
`EVENT_TYPES` (7) adds `upload.accepted` (head) and `upload.failed` (failure branch, deliberately outside `STAGE_ORDER`) — `d5/events.py:20-27`.

**Only stage 1 is wired into the poll loop today**: detect → `file.format-detected` → `upload.ready`. Parse / CRS / COG are stage 2 and not driven by the worker — `worker.py:14-18`; `domains/d5_ingestion.py:144-157,218-227`.
Stage-2 per-file function exists but is unwired: `run_file()` — steps 1 감지/detect, 2 파싱/parse_metadata, 3 좌표/find_reference_grid, 4 COG/`convert_tif_to_cog`|`write_cog_from_grid` — `services/pipeline-worker/src/colab_pipeline/d5/pipeline.py:56-121`.

### 2.4 AI / ontology step

- ai-service exposes **only** `GET /healthz` and `POST /searches` — `services/ai-service/src/colab_ai/app/main.py:67,71`
- `/searches` is **interpretation-only**: it does not query the catalog; core-api performs the actual dataset search with the interpreted terms — `services/ai-service/src/colab_ai/app/main.py:5-7`
- `GET /uploads/{id}/lineage-suggestions` in core-api is a **stub that always returns `degraded: true` + empty list** — the ai-service counterpart does not exist — `services/core-api/src/colab_core/app/routes/ingestion.py:319-343`
- Ontology reads: `d9_ontology.expand()` / `expand_by_graph()` — `services/ai-service/src/colab_ai/domains/d9_ontology.py:50,184`
- **No AI call occurs inside the upload → dataset flow today.** The only live cross-service AI call is `/searches` from dataset search.

### 2.5 Table inventory — 27 tables (platform 21 + ai 6, both incl. version table)

**`colab_platform`** (`db/platform/schema.sql:88-844`): `d1_lab:88`, `d1_lab_profile:97`, `d1_account:111`, `d2_member_role:128`, `d2_permission_switch:139`, `d2_permission_change:152`, `d2_dataset_access:171`, `d2_dataset_access_grant:181`, `d2_verified:198`, `d3_dataset:227`, `d3_dataset_description:289`, `d3_dataset_autometa:319`, `d3_file:357`, `d4_lineage_edge:474`, `d4_lineage_unknown:495`, `d5_upload:516`, `d5_upload_file:548`, `d5_pipeline_event:579`, `d6_project:621`, `d6_project_dataset:640`, `d8_activity:660`, `d8_download:675`, `alembic_version_platform:844`

**`colab_ai`** (`db/ai/schema.sql:51-200`): `d9_method_term:51`, `d9_topic_synonym:78`, `d9_place_alias:102`, `d9_concept:125`, `d9_concept_edge:161`, `alembic_version_ai:200`

### 2.6 Lineage edge model

| Table | Columns | Citation |
|---|---|---|
| `d4_lineage_edge` | `id, lab_id, child_dataset_id, parent_dataset_id, parent_role, method, origin, confirmed_by_account_id, confirmed_at` | `db/platform/schema.sql:474-490` |
| `d4_lineage_unknown` | `dataset_id (PK), lab_id, marked_at, marked_by_account_id` | `db/platform/schema.sql:495-503` |
| `d3_dataset` | `id, lab_id, owner_account_id, uploader_account_id, source_label, uploaded_at, last_modified_at, lineage_confirmed_at, deleted_at, deleted_by_account_id, file_count, search_vector, processing_level_user_set, representative_file_id, source_label_normalized` | `db/platform/schema.sql:227-266` |
| `d3_file` | `id, lab_id, dataset_id, kind, file_name, size_bytes, storage_key, created_at, carries_lat, carries_lon` | `db/platform/schema.sql:357-378` |
| `d3_dataset_description` | `dataset_id (PK/FK), lab_id, name, topic, summary, updated_at, search_vector` | `db/platform/schema.sql:289-306` |
| `d3_dataset_autometa` | `dataset_id (PK/FK), lab_id, format, variables[], period_start, period_end, crs, grid, total_size_bytes, bundle_file_name, updated_at, search_vector` | `db/platform/schema.sql:319-354` |

Lineage edge direction: `child_dataset_id` ← `parent_dataset_id`, qualified by `parent_role` + `method`, with `origin` recording provenance and `confirmed_by_account_id`/`confirmed_at` recording the **human confirmation** required by the D10→D4 invariant.

### 2.7 viz-render input contract

`POST /renders` body carries **only** `target{datasetId|uploadId, fileIds}`, `variable`, `instant`, `style{palette, classCount}`, `withoutReferenceGrid` — **no geo/CRS/pixel/band parameters, by design** — `services/viz-render/src/colab_viz/app/routes/renders.py:35-58`; seam `contracts/seams/core-viz.yaml:1-40`.

---

## 3. Auth & permission sequence

Both `updateProject` and `updateDataset` are **FastAPI REST handlers**, not GraphQL resolvers.
- `updateProject` = `PATCH /projects/{projectId}` — `services/core-api/src/colab_core/app/routes/project.py:69`
- `updateDataset` = `PATCH /datasets/{datasetId}` — `services/core-api/src/colab_core/app/routes/catalog.py:420`

### 3.1 Token parsing → subject

| Step | Detail | Citation |
|---|---|---|
| Dependency | `current_subject` | `services/core-api/src/colab_core/app/deps.py:14` |
| Bearer parse | `bearer_token()` — splits `"Bearer <token>"`, case-insensitive scheme, empty → `None` | `services/core-api/src/colab_core/kernel/auth.py:49-55` |
| Decoded shape | `Subject{account_id: Ulid, lab_id: Ulid}` — **no role in the token** | `kernel/auth.py:20-23` |
| No token | `errors.unauthorized(...)` → **401** | `app/deps.py:24` |
| Unknown token | `errors.unauthorized(...)` → **401** | `app/deps.py:27` |
| Resolution | `app.state.authenticators.resolve(token)` → `AuthenticatorChain.resolve` | `app/deps.py:25`; `kernel/authn.py:173-178` |
| Chain order | `StaticTokenAuthenticator` (planted token table, `authn.py:73-80`) → `SignedSessionAuthenticator` (`authn.py:83-91`); first match wins, empty chain rejects | `kernel/authn.py:181-198` |
| Token table | `SubjectRegistry.resolve()` over a JSON file (`SubjectRegistry.from_file`) — a planted token→Subject map, **not a DB user query** | `kernel/auth.py:32-46` |
| Role lookup | separate + later, in-handler: `d2_access.role_of(db, account_id)` → `SELECT role FROM d2_member_role WHERE account_id = :account_id` | `services/core-api/src/colab_core/domains/d2_access.py:18,72-73` |

### 3.2 Lab-boundary enforcement — RLS, not application code

**There is no application-level `if lab_id != subject.lab_id: reject`.** Enforcement is PostgreSQL RLS, wired per request:

| Step | Detail | Citation |
|---|---|---|
| Scoped session | `scoped_db` dependency opens the txn and calls `apply_scope` | `app/deps.py:31-44` |
| GUC injection | `SELECT set_config('app.current_lab', <lab_id>, true)` + `app.current_account`, i.e. `SET LOCAL` — transaction-scoped, so pooled connections cannot leak lab_id | `kernel/scope.py:36-41` |
| Predicate fn | `current_lab_id()` regex-validates the ULID GUC, returns `NULL` when unset/malformed | `db/platform/schema.sql:41-49` (and `current_account_id()` `:41-58`) |
| Policy (`d6_project`) | `lab_boundary`: `USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id())` + `ENABLE`/`FORCE ROW LEVEL SECURITY` | `db/platform/schema.sql:818-821` |
| Policy (`d3_dataset`) | identical triad | `db/platform/schema.sql:739-742` |
| Fail-closed | `lab_id = NULL` is always false → default-deny when the GUC is missing | `db/platform/schema.sql:41-49` |
| Observable effect | cross-lab rows are **invisible**, so the handler falls into its own `not_found` branch — 404, not 403. Default message is literally `"없거나 연구실 경계 밖이다."` | `kernel/errors.py:37-38` |
| Deliberate design | locked datasets must stay discoverable ("잠겼다고 행이 사라지면 안 된다") — meta tables get boundary-only policy, no body gate | `db/platform/schema.sql:687-697` |
| Body-level gate | `body_access` RESTRICTIVE policy on `d3_file` **only** (allowlist + expiry) | `db/platform/schema.sql:756-780` |

### 3.3 `d2_access` — what it actually is

`d2_access` is a **Python domain module** (`services/core-api/src/colab_core/domains/d2_access.py`), *not* a DB table or column. `grep d2_access db/platform/` → no hits; `grep d2_access contracts/` → no hits. It is a façade over six tables.

**The four permission switches** — `SWITCHES` tuple, `domains/d2_access.py:16`:
```python
SWITCHES = ("업로드·편집", "프로젝트 생성", "승인 위임", "연구실 설정")
```

| Switch (verbatim) | Gates | Read site | Consumed by |
|---|---|---|---|
| `업로드·편집` | all dataset/upload writes | `permissions_of()` `domains/d2_access.py:76-82` | `_require_upload_edit` `routes/ingestion.py:164-173`, called from **updateDataset** `routes/catalog.py:436` |
| `프로젝트 생성` | all project writes | `permissions_of()` `domains/d2_access.py:76-82` | `_can_manage` `routes/project.py:168-174`, called from **updateProject** `routes/project.py:84` |
| `승인 위임` | approval delegation | `permissions_of()` / `member_permissions()` | `routes/members.py:44-45,53,94` — not on the update paths |
| `연구실 설정` | lab-config screen | same | not on the update paths |

**Backing tables:**

| Table | Columns / purpose | Citation |
|---|---|---|
| `d2_member_role` | `account_id → role` | `db/platform/schema.sql:128`; SQL `domains/d2_access.py:18,72-73` |
| `d2_permission_switch` | `account_id, switch, enabled` | `db/platform/schema.sql:139`; read `d2_access.py:19,76-82`; upsert `d2_access.py:56-61,151-164` (only via `apply_switch()`) |
| `d2_permission_change` | append-only audit: `switch`, `direction` ∈ {`켬`,`끔`} | `db/platform/schema.sql:152`; write `d2_access.py:63-69,161-164` |
| `d2_dataset_access` | `state` column (incl. `'열림'`) — dataset-level lock, **separate from the 4 switches** | `db/platform/schema.sql:171`; `d2_access.py:21-48,85-122` |
| `d2_dataset_access_grant` | allowlist + `expires_at` | `db/platform/schema.sql:181` |
| `d2_verified` | verification flag | `db/platform/schema.sql:198` |

All six carry a `lab_boundary` RLS policy — `db/platform/schema.sql:706-737`.

### 3.4 Professor auto-grant rule

`permissions_of()` — `services/core-api/src/colab_core/domains/d2_access.py:76-79`:
```python
def permissions_of(session, account_id, role) -> dict[str, bool]:
    """교수는 네 스위치가 항상 켜진 것으로 내려간다..."""
    if role == "교수":
        return {s: True for s in SWITCHES}
```
- Literal role string is `"교수"` (Professor).
- **All four switches return `True` unconditionally, bypassing `d2_permission_switch` entirely.**
- Duplicated for the member-grid read path in `member_permissions()` — `d2_access.py:142-143`.
- Professor status itself is stored (`d2_member_role`), the *permissions* are computed, not stored — `d2_access.py:50-51`.
- Consequence on staging: `d2_permission_switch` has 8 rows all `t`, and professors bypass anyway, so **no subject exists that can produce a 403** — `dev-package/03-HANDOFF.md:323` (blocker #44).

### 3.5 Ordering — `updateProject` (PATCH /projects/{projectId})

| # | Call | Citation | Failure / short-circuit |
|---|---|---|---|
| 1 | `current_subject(request, authorization)` → `bearer_token` → `authenticators.resolve` | `app/deps.py:14-28`; route param `routes/project.py:71` | **401 UNAUTHORIZED** (`kernel/errors.py:29-30`) |
| 2 | `scoped_db(request)` → open txn, `apply_scope` sets `app.current_lab` / `app.current_account` | `app/deps.py:31-44`; route param `routes/project.py:72` | malformed ULID → `ValueError` (`kernel/scope.py:38-39`), unhandled → 500 |
| 3 | `_can_manage(db, subject)` → `role_of()` then `permissions_of(...)["프로젝트 생성"]` | `routes/project.py:168-174`, called `routes/project.py:84` | **403 FORBIDDEN** `"프로젝트 생성 스위치가 꺼져 있다."` (`routes/project.py:85`) |
| 4 | payload keys ⊆ `_PROJECT_UPDATE_FIELDS` | `routes/project.py:88-91` | **400 BAD_REQUEST** |
| 5 | `Ulid.is_valid(projectId)` | `routes/project.py:92-93` | **400 BAD_REQUEST** |
| 6 | `d6_project.project_exists(db, project_id)` — **under RLS scope**, so cross-lab rows are invisible | `routes/project.py:95-96` | **404 NOT_FOUND** `"없거나 연구실 경계 밖이다."` (`kernel/errors.py:37-38`) — this *is* the lab-boundary rejection |
| 7 | field validation: `name` dup via `d6_project.name_is_taken`, `period` format | `routes/project.py:98-108` | 400 / **409 CONFLICT** |
| 8 | `d6_project.update_project(...)` — write; RLS `WITH CHECK` re-enforced | `routes/project.py:110-111`; policy `db/platform/schema.sql:818-821` | policy violation → DB exception |
| 9 | `get_project(...)` response assembly | `routes/project.py:111` | — |

### 3.6 Ordering — `updateDataset` (PATCH /datasets/{datasetId})

| # | Call | Citation | Failure / short-circuit |
|---|---|---|---|
| 1 | `current_subject` | `app/deps.py:14-28`; route param `routes/catalog.py:422` | **401 UNAUTHORIZED** |
| 2 | `scoped_db` → `apply_scope` (RLS GUCs) | `app/deps.py:31-44`; `kernel/scope.py:36-41`; route param `routes/catalog.py:423` | `ValueError` → 500 |
| 3 | `_require_upload_edit(db, subject)` (imported from `ingestion.py` to dodge a circular import — `routes/catalog.py:434-435`) → `role_of()` then `permissions_of(...)["업로드·편집"]` | `routes/ingestion.py:164-173`; called `routes/catalog.py:436` | **403 FORBIDDEN** `"업로드·편집 스위치가 꺼져 있다."` (`routes/ingestion.py:173`) |
| 4 | payload keys ⊆ `_UPDATE_FIELDS` | `routes/catalog.py:438-442` | **400 BAD_REQUEST** |
| 5 | `Ulid.is_valid(datasetId)` | `routes/catalog.py:444-445` | **400 BAD_REQUEST** |
| 6 | `d3_catalog.dataset_exists(db, dataset_id)` — RLS-scoped | `routes/catalog.py:447-448` | **404 NOT_FOUND** (doubles as lab-boundary rejection) |
| 7 | field validation: `name`, `processingLevel` ≤ `LV_CAP`, `representativeFileId` via `d3_catalog.file_belongs_to`, `variables` | `routes/catalog.py:452-479` | **400 BAD_REQUEST** variants |
| 8 | `d3_catalog.update_dataset(...)` — write; RLS `WITH CHECK` on `d3_dataset` | `routes/catalog.py:485-486`; policy `db/platform/schema.sql:739-742` | policy violation → DB exception |
| 9 | `get_dataset(...)` response | `routes/catalog.py:486` | — |

### 3.7 Canonical ordering (both handlers)

```
authenticate (401)
  → open RLS-scoped transaction (SET LOCAL app.current_lab / app.current_account)
  → permission-switch check (403)          ← note: BEFORE resource lookup
  → payload/ID validation (400)
  → resource lookup under RLS (404 == lab-boundary rejection)
  → field validation (400/409)
  → write, RLS WITH CHECK re-enforces boundary
  → response assembly
```
**Diagram note:** the permission check precedes the resource lookup, so a permission failure is indistinguishable from a nonexistent resource in the other direction — and a cross-lab resource yields **404, never 403**.

### 3.8 RLS gate coverage

- `gates/config/rls-allowlist.toml` defines required policy names `lab_boundary` + `body_access`, `body_tables = ["d3_file"]`, and `allow_no_rls` exemptions (`alembic_version_platform`, `d1_lab`; ontology seed tables on the `ai` chain).
- `d1_lab` is RLS-exempt — this is why pipeline-worker can read the lab roster without BYPASSRLS — `dev-package/03-HANDOFF.md:34`.
- Enforced by gates `rls-coverage`, `rls-effect`, `rls-effect-selftest` (see §4).
- `UNVERIFIED:` exact `POLICY` line numbers inside `db/platform/versions/0001_p0_platform.py` and `0004_p2_grid_axis_and_d5.py` — confirmed present by `grep -l` only, files not opened.
- `UNVERIFIED:` the trigger that makes `d2_permission_change` append-only — referenced by comment `domains/d2_access.py:64`, schema definition not located.

---

## 4. Deploy workflow + gates

### 4.1 `deploy.sh` stages — 14 steps in order

`infra/staging/deploy.sh`:

| # | Banner (verbatim) | Lines | Note |
|---|---|---|---|
| ⓪ | `⓪ 타깃` — `approval/target.sh` check | `deploy.sh:37-38` | approval gate |
| ⓪-b | `⓪-b 필수 설정 프리플라이트` — `preflight.sh` + `preflight_required` | `deploy.sh:44-53` | **moved ahead of build/backup** after the 1st-deploy red |
| ① | `① 무엇을 굽는가 — 커밋이다 (DR-4)` — dirty-tree check, tag decision | `deploy.sh:55-78` | `TAG="$SHA"` (`:72-78`) |
| ② | `② 호스트에서 게이트를 다시 돈다` — `gates/run.sh migration-single-head` | `deploy.sh:94-98` | **only gate deploy.sh runs** |
| ③ | `③ 직전 이미지 보존 (:prev) — 빌드 전에 한다` | `deploy.sh:100-113` | `docker tag colab-v2/$n:i2 colab-v2/$n:prev` (`:107`) |
| ④ | `④ 이미지 빌드 — 태그는 커밋 SHA 다` | `deploy.sh:115-135` | |
| ⑤ | `⑤ 배포 전 백업` — `backup/backup.sh` (skippable via `--skip-backup`) | `deploy.sh:137-148` | |
| ⑥ | `⑥ postgres 기동 대기` (healthy, 120s timeout) | `deploy.sh:150-161` | |
| ⑦ | `⑦ 롤 · 데이터베이스` — `db-bootstrap.sh roles` | `deploy.sh:163-165` | |
| ⑧ | `⑧ 마이그레이션` — `migrate-platform`, then `migrate-ai` | `deploy.sh:167-175` | **two separate chains** |
| ⑨ | `⑨ 앱 롤 GRANT` — `db-bootstrap.sh app-grants` | `deploy.sh:177-181` | |
| ⑩ | `⑩ 5개 배포 단위 + 엣지 교체` — `dc up -d --remove-orphans` | `deploy.sh:183-185` | |
| ⑪ | `⑪ 판정` — retry loop over `verify/verify-deploy.sh` (`COLAB_VERIFY_TRIES:-30`, 5s sleep) | `deploy.sh:187-202` | |
| ⑪-b | `⑪-b 체인 판정` — `verify/verify-chains.sh` | `deploy.sh:203-204` | |
| ⑫ | `⑫ 원장 · 표식 · 보존` — `ledger_append`, `mark_success`, `:i2` retag, `image_prune` | `deploy.sh:206-220` | |

`RELEASE_IMAGES` has **6** entries (`core-api pipeline-worker viz-render ai-service frontend migrator`) — `infra/staging/pipeline/lib.sh:99` — although the ⑩ banner says "5개 배포 단위" (`deploy.sh:184`). `UNVERIFIED:` whether the banner/array mismatch is intentional (migrator is a build-time unit, not a serving unit).

### 4.2 Image tagging scheme

| Tag | Meaning | Set where | Pruned? |
|---|---|---|---|
| `:$TAG` (= commit SHA, or `$SHA-dirty` with `--allow-dirty`) | **the release identity** — what is built and what the ledger records | `deploy.sh:72-78`, built `:116-117` | kept 3 deep, `IMAGE_KEEP="${COLAB_IMAGE_KEEP:-3}"` `pipeline/lib.sh:111,109-138` |
| `:i2` | **compatibility alias only, not a release identity** — used by `compose.throwaway.yml` restore-rehearsal lookups | preserved at `deploy.sh:106`; **re-tagged onto the new `$TAG` at the end of a green deploy** `deploy.sh:213`; rationale `deploy.sh:210-212` | never (`ALIAS_TAGS=(prev i2)` `pipeline/lib.sh:113-116,135`) |
| `:prev` | alias applied to the outgoing `:i2` image **before** the build so it keeps a name | `deploy.sh:107` (stage ③) | never |

> ⚠ **`:prev` is NOT the previous release.** `deploy.sh` ③ tags whatever `:i2` points at, and `:i2` is only refreshed at the tail of a *green* deploy — so after the first green deploy `:prev` points at a hand-built image that is not in the ledger at all. `ledger_rollback_target()` never even considers `:prev`. — `dev-package/03-HANDOFF.md:323` (blocker #43)

### 4.3 Release ledger

| Property | Value | Citation |
|---|---|---|
| Path | `${COLAB_PIPELINE_STATE_DIR:-$HOME/colab-v2-releases}/release-ledger.tsv` | `pipeline/lib.sh:44,46,51` |
| Format | append-only TSV, 6 tab-separated fields | `pipeline/lib.sh:57-62` |
| Fields | `시각(timestamp) · 종류(kind: deploy\|rollback\|approve) · 커밋SHA · 이미지태그 · 판정(green\|red) · 비고(note)` | `pipeline/lib.sh:57-62` |
| Writer | `ledger_append()` | `pipeline/lib.sh:65-70` |
| Write sites | `deploy.sh:68` (red, rejected), `:84` (red, abort), `:207` (green); `rollback.sh:54,77,92` | as cited |
| Retention | last **30** rows, `LEDGER_KEEP=30`, `ledger_prune()` | `pipeline/lib.sh:63,72-77` |

### 4.4 Rollback

`infra/staging/rollback.sh` — three mutually exclusive modes, **no default**:

| Mode | Behavior | Citation |
|---|---|---|
| `--to-last-green` | `ledger_rollback_target()` picks the newest green `deploy` row that is not the current tag | `rollback.sh:61-67` |
| `--to-tag <TAG>` | requires all 6 images present (`images_exist`) | `rollback.sh:68-72` |
| `--to-placeholder` | reverts to `compose.yml` placeholder origin — explicitly **"N-1 이 아니라 0"** | `rollback.sh:50-56` |

Order: resolve tag → `docker compose -f compose.i2.yml up -d --remove-orphans` with `COLAB_RELEASE_TAG=$TAG` (`:76`) → retry-poll `verify/verify-deploy.sh` (`:74-91`) → `ledger_append rollback ... green|red` (`:88-93`).
Restores **serving state only** — does **not** revert schema (migrations are forward-only, `rollback.sh:16-17`) and does **not** touch the pgdata volume.

> ⚠ **There is currently no working script rollback path.** The ledger holds exactly one green `deploy` row (`30b3e0a7b3f3`), so `ledger_rollback_target()` returns 0 candidates and `rollback.sh` calls `die`. It is resolved by the next green deploy. — `dev-package/03-HANDOFF.md:323` (blocker #43)

### 4.5 Preflight checks (5)

`infra/staging/preflight.sh`, function `preflight_required` (`:72-103`):
1. env file `$COLAB_STAGING_ENV` exists and loads — `:75-79`
2. every `${VAR:?}` key grepped out of `compose.i2.yml` is non-empty — `:58-59`
3. every key reported by `db-bootstrap.sh required-env` is non-empty — `:61`
4. `*_FILE` keys → the path must exist (`-f`) — `:96`
5. `*_DIR` keys → the directory must exist (`-d`) — `:97`

No SKIP permitted ("필수 설정은 유예 대상이 아니다", `:71`); values are never printed, only key names (`:23-24,86-87,96-97`).

### 4.6 Verify scripts (3)

| Script | Asserts | Citation |
|---|---|---|
| `verify/verify-deploy.sh` | 6 health endpoints return 200 **and** each body matches the expected `unit` name regex (200 alone is insufficient — the placeholder origin returns 200 everywhere); 8 named containers `healthy`; host exposure is exactly `127.0.0.1:3000` with **zero** `0.0.0.0` bindings | `:36-77`, `:86-95`, `:105-109` |
| `verify/verify-chains.sh` | both `platform` and `ai` Alembic version tables are non-empty and single-head; read-only `SELECT` only | `:27,43,48,53` |
| `verify/selftest.sh` | fail-closed self-proof of `verify-deploy.sh`/preflight using green/dead/placeholder HTTP fixtures + a docker PATH shim; asserts a red fixture never reports green | `:4-19,66-115` |

### 4.7 Cron poll trigger

- Cron line: `*/5 * * * * "$HERE/watch.sh" >> "$LOG" 2>&1` — **every 5 minutes** — `infra/staging/pipeline/install-schedule.sh:20`
- Installed/removed as a marked block `# >>> colab-v2-staging-deploy >>>` via `install|show|remove` — `install-schedule.sh`
- Chain: **cron → `watch.sh` → `run-pipeline.sh` → `deploy.sh`**
- `watch.sh` writes `pipeline.log` and `LAST-SUCCESS.txt` / `DEPLOY-FAILED.txt` markers; treats **exit 75** (`EX_TEMPFAIL`, lock contention or fetch failure) as *skip, not failure* — `watch.sh:20-32`
- `run-pipeline.sh`: ① `git fetch --quiet origin "$BRANCH"` read-only (`:40-41`) → no-op when `LOCAL == REMOTE` and no `--force` (`:45-48`) → ② **fast-forward-only** checkout, refuses on dirty tree or non-ff (`:50-63`) → ③ `deploy.sh --target "$TARGET"` (`:65-67`), propagating the exit code
- **It polls the git ref (`origin/main`), not a container registry** — `run-pipeline.sh:37,40-41`

### 4.8 Backup / restore

| Script | Behavior | Citation |
|---|---|---|
| `backup/backup.sh` | `pg_dump` per profile (platform/ai) in-container → gzip → temp → `verify-artifact.sh` content check → **atomic `mv` only if green**; exit 78 when `COLAB_BACKUP_TARGET=none` (not counted as success) | `:13-60` |
| `backup/backup-full.sh` | stage 0 secret-shaped-file hygiene check on the backup dir (`:17-29`) → `1단` ledger dump (`:31-38`) → volume archive **only if the ledger dump succeeded** (paired-artifact rule, `:8-9,36-38`) | as cited |
| `backup/backup-volume.sh` | volume tar archive, paired to the platform dump | header `backup-full.sh:2-9` |
| `backup/install-schedule.sh` | separate cron marker block from the pipeline's, so removing one does not remove the other | `:7-8` |
| `backup/schedule.crontab` | **03:30 daily** full backup; **04:10 Mondays** re-verify latest artifacts across both profiles + full volume, incl. freshness | `:9-11` |
| `restore/preflight.sh` | P1–P9 read-only preconditions incl. sha256 digest match, `--skip-age` handling | `:1-9` |
| `restore/restore-db.sh` | irreversible in-place restore (`DROP SCHEMA public CASCADE`); requires **3 gates**: `--yes-drop-schema`, a real `COLAB_RESTORE_PRE_BACKUP` file, and zero live app connections | `:1-11` |
| `restore/restore-volume.sh` | overwrite-only (not sync/prune); requires `--yes-overwrite-volume`, all holding containers stopped, and a GREEN archive | `:1-13` |
| `restore/rehearsal.sh` | read-only-against-live rehearsal of the DROP SCHEMA path, secret-file overwrite-vs-mv semantics, RLS/GRANT survival, volume round-trip — entirely in throwaway `r1_*` instances/tmpfs | `:1-12` |

`UNVERIFIED:` numeric retention for backup *artifacts* — only release retention (`LEDGER_KEEP=30`, `IMAGE_KEEP=3`, `pipeline/lib.sh:63,111`) was located; `backup/lib.sh` and `config.example.env` were not opened.

### 4.9 Compose file variants (3)

| File | Project | Services | Distinguishing facts |
|---|---|---|---|
| `compose.yml` | `colab-v2-staging` | `nginx`, `cloudflared` only (37 lines) | **placeholder origin** — no datastores, no app units. Only target of `rollback.sh --to-placeholder` (`rollback.sh:50-56`). Its `nginx.conf` serves only `/healthz` + a static page, no proxying — `infra/staging/nginx.conf:1-19` |
| `compose.i2.yml` | `colab-v2-staging` | `nginx, cloudflared, postgres, volume-init, core-api, pipeline-worker, viz-render, ai-service, frontend, migrate-platform, migrate-ai` (393 lines) | **the real staging stack.** `migrate-*` behind `profiles: ["migrate"]` (`:349,368`). App images use `${COLAB_RELEASE_TAG:?}` (`:149,229,270,301,337,352,371`) — the tag is mandatory and supplied at runtime by deploy.sh/rollback.sh |
| `compose.throwaway.yml` | `colab-v2-r1throw` | 7 services (159 lines) | isolated restore-rehearsal: separate project/volumes/network (`:4-5`), no `container_name` (`:6`), **no host ports** (`:7-8`), **no cloudflared** (`:9-11`), **no `build:`** — reuses `:i2` tags (`:12-13`, e.g. `:46`), postgres on `tmpfs` not the live PGDATA bind (`:14,21-29`), freshly-generated `THROW_*` secrets (`:16-17,52-60`) |

> ⚠ **`compose.i2.yml` requires `COLAB_RELEASE_TAG`, and the only place that supplies it is `deploy.sh:77` — it is absent from the env file.** So the documented restart command does not currently bring the stack up. — `dev-package/03-HANDOFF.md:323` (blocker #46)

### 4.10 Gate inventory — **27 gates** (verified count)

`ALL_GATES` array = **27 entries** — `gates/run.sh:11-20`. The `case` statement has **29** branches = 27 gates + the `selftest` and `all` meta-targets. **The claimed "~34 gate implementations" is wrong**; 27 also matches the measured run in `dev-package/03-HANDOFF.md:14` ("게이트 27종 = green 26 · red 1").

`gates/config/` holds **5** config files, not gates: `boundaries.toml`, `db-boundaries.toml`, `importlinter.ini`, `rls-allowlist.toml`, `seam-consistency-allowlist.toml`.

**Split: 16 substantive checks + 11 fail-closed selftests.**

| # | Gate ID | Enforces | Blocking | Citation |
|---|---|---|---|---|
| 1 | `planning-freshness` | embedded md in planning-package HTML matches source md; unmounted source = red | ✅ | `gates/run.sh:23-27` |
| 2 | `contract-lint` | seam OpenAPI lint (spectral); tool absence / network fail / 0 targets = red | ✅ | `gates/run.sh:28-32` |
| 3 | `contract-breaking` | breaking-change detection vs git HEAD baseline (oasdiff) | ✅ | `gates/run.sh:33-36` |
| 4 | `event-lint` | event schema validity + `$ref` resolution + instance fixtures (ajv) | ✅ | `gates/run.sh:37-42` |
| 5 | `event-breaking` | `$defs`-level breaking change detection in event contracts | ✅ | `gates/run.sh:43-47` |
| 6 | `seam-consistency` | seam↔event cross-consistency: G-e dangling delegation refs, G-b source-const capability claims, ㉠ provenance citation, ㉡ E-04 flow completeness | ✅ | `gates/run.sh:112-117`; config `gates/config/seam-consistency-allowlist.toml` |
| 7 | `generated-up-to-date` | codegen manifest vs regenerated artifacts diff | ✅ | `gates/run.sh:153-158` |
| 8 | `import-boundary` | cross-domain direct imports banned (import-linter); 0 code = red | ✅ | `gates/run.sh:56-60`; config `gates/config/importlinter.ini` |
| 9 | `banned-import` | per-deploy-unit import allow/deny list (e.g. no geo libs in core-api) | ✅ | `gates/run.sh:61-64`; config `gates/config/boundaries.toml` |
| 10 | `ai-no-lineage-write` | **negative gate** — proves no D10→D4 write path exists in contracts/code/migrations | ✅ | `gates/run.sh:65-68` |
| 11 | `db-boundary` | per-deploy-unit DB chain boundary, via real DB connections | ✅ | `gates/run.sh:69-74`; config `gates/config/db-boundaries.toml` |
| 12 | `migration-single-head` | no branching Alembic heads in either chain; 0 migrations = red | ✅ | `gates/run.sh:83-87` |
| 13 | `schema-diff` | declared `db/<chain>/schema.sql` vs applied DB drift; no DB URL = red | ✅ | `gates/run.sh:88-92` |
| 14 | `rls-coverage` | RLS policy presence for every table outside the allow-list | ✅ | `gates/run.sh:93-97`; config `gates/config/rls-allowlist.toml` |
| 15 | `rls-effect` | RLS actually hides rows (3 oracles, NOBYPASSRLS non-owner role; a bypass role = red) | ✅ | `gates/run.sh:98-103` |
| 16 | `work-item-consistency` | `dev-package/work-items.yaml` ledger vs prose consistency, 6 sub-checks | ✅ | `gates/run.sh:142-148` |
| 17 | `stage2-markers` | dormant `stage2` module tests still run in CI; 0 collected / skipped / failed = all red | ✅ | `gates/run.sh:122-126` |
| 18 | `contract-selftest` | proves gates 2–3 fail-closed | ✅ | `gates/run.sh:52-55` |
| 19 | `event-selftest` | proves gates 4–5 fail-closed | ✅ | `gates/run.sh:48-51` |
| 20 | `boundary-selftest` | proves gates 8–10 fail-closed | ✅ | `gates/run.sh:79-82` |
| 21 | `db-boundary-selftest` | proves gate 11 fail-closed, incl. reproducing the real 2026-08-25 violation | ✅ | `gates/run.sh:75-78` |
| 22 | `db-selftest` | proves gates 12–14 fail-closed | ✅ | `gates/run.sh:108-111` |
| 23 | `rls-effect-selftest` | proves gate 15 fail-closed by literally removing protection in fixtures | ✅ | `gates/run.sh:104-107` |
| 24 | `seam-consistency-selftest` | proves gate 6 fail-closed, incl. the real DR-7 dangling-delegation prose fixture | ✅ | `gates/run.sh:118-121` |
| 25 | `generated-selftest` | proves gate 7 fail-closed | ✅ | `gates/run.sh:159-162` |
| 26 | `work-item-selftest` | proves gate 16 fail-closed | ✅ | `gates/run.sh:149-152` |
| 27 | `stage2-markers-selftest` | proves gate 17 fail-closed (0-case, skip-case, fail-case) | ✅ | `gates/run.sh:127-130` |

Meta-targets (not gates): `selftest` — runs 9 of the selftest suites, **excluding** `stage2-markers-selftest` (runtime deps) — `gates/run.sh:131-141`; `all` — runs every `ALL_GATES` entry — `gates/run.sh:163`.

**Every gate is blocking.** `gates/run.sh` runs under `set -euo pipefail` (`:6`) and each branch `exec`s its tool, so the gate's exit code becomes `run.sh`'s. The `all` target additionally captures each `$?` and sets `rc=1` on any nonzero (`:177-186,196`). **There is no advisory/soft exit path anywhere in the file.** Stated policy: an unimplemented gate is red by design — `gates/run.sh:4-5`, `CLAUDE.md:119-124`.

### 4.11 Gate wiring

| Caller | Gates invoked | Citation |
|---|---|---|
| `infra/staging/deploy.sh` | **only** `migration-single-head`, at stage ②; failure aborts the deploy | `infra/staging/deploy.sh:98` |
| `.github/workflows/ci.yml` | `contract-lint`:116, `contract-breaking`:118, `event-lint`:120, `event-breaking`:122, `seam-consistency`:124, `generated-up-to-date`:126, `import-boundary`:144, `banned-import`:146, `ai-no-lineage-write`:148, `migration-single-head`:166, `schema-diff`:168, `rls-coverage`:170, `rls-effect`:172, `stage2-markers-selftest`:195, `stage2-markers`:197, `selftest`:259 — all under `set -euo pipefail` steps (`:103,111,237`) | as cited |

**Known wiring gaps** (from `dev-package/03-HANDOFF.md`, blockers §4):
- `#39` — `work-item-consistency` is **not wired into CI**; only `work-item-selftest` runs, so ledger/prose divergence is not caught by CI — `03-HANDOFF.md:323` region
- `#41` — `generated-up-to-date` fails in CI (exit 127, missing `frontend/node_modules/.bin/openapi-typescript`)
- `#42` — doc-only commits produce an empty CI success: all 5 jobs `skipped` because no path filter covers `dev-package/**`
- `#45` — `deploy.sh` ⑫ alias re-tag uses `docker tag … 2>/dev/null || true`, so a failed alias re-tag still reports GREEN (green-by-skip shape)

---

## 5. Dataset / file lifecycle states

### 5.1 Important structural fact

**Neither `d3_dataset` nor `d3_file` has a `status` enum column.** Dataset state is a tombstone/timestamp model; file `kind` is a type discriminator, not a lifecycle. The real lifecycle machine lives on **`d5_upload`**, as a composite of booleans + timestamps, plus the `d5_pipeline_event` event log.

### 5.2 Enum inventory — 6 enum-like fields, 23 values total

| Field | Values | Count | Citation |
|---|---|---|---|
| `d5_upload.failure_class` | `'재시도 가능'` (retryable), `'영구'` (permanent) | 2 | `db/platform/schema.sql:531` |
| `d5_upload.failure_reason` | `'업로드 중단'`, `'형식 인식 실패'`, `'헤더 인식 실패'`, `'조각이 서로 다름'`, `'좌표계 변환 실패'`, `'미리보기 준비 실패'`, `'시간 초과'`, `'내부 오류'` | 8 | `db/platform/schema.sql:532-534` |
| `d5_pipeline_event.event_type` | `upload.accepted`, `file.format-detected`, `file.header-parsed`, `file.crs-normalized`, `preview.cog-built`, `upload.ready`, `upload.failed` | 7 | CHECK `db/platform/schema.sql:589-590`; enum `services/pipeline-worker/src/colab_pipeline/d5/events.py:20-27` |
| `d3_file.kind` / `d5_upload_file.kind` | `'본체'` (body), `'기준 격자 파일'` (reference grid file) — **discriminator, not lifecycle** | 2 | `db/platform/schema.sql:363`, `:552` |
| `d6_project.status` | `'진행 중'` (default), `'닫힘'` | 2 | `db/platform/schema.sql:630` |
| `PipelineResult.status` (in-memory, stage 2, **unpersisted**) | `"SUCCESS"`, `"FAILURE"` | 2 | `services/pipeline-worker/src/colab_pipeline/d5/pipeline.py:41-47,51,100,121` |

### 5.3 `d5_upload` state fields (the actual state machine)

`db/platform/schema.sql:516-539`: `ready (bool)`, `renderable (bool|NULL)`, `metadata_complete (bool|NULL)`, `failed_at (timestamptz|NULL)`, `failure_class`, `failure_reason`, `registered_at (timestamptz|NULL)`, `expires_at`.

Derived states:

| State | Predicate | Kind |
|---|---|---|
| PENDING | `ready=false AND failed_at IS NULL` | initial; this is exactly the worker's poll predicate (`domains/d5_ingestion.py:370`) |
| READY | `ready=true` | success |
| READY (grid-only) | `ready=true, renderable=false, metadata_complete=false` | success, short-circuit branch |
| FAILED | `failed_at IS NOT NULL` (+ `failure_class`, `failure_reason`) | **terminal** — excluded from the poll predicate regardless of class |
| REGISTERED | `registered_at IS NOT NULL` | **terminal (consumed into a dataset)** |
| REAPED | row hard-deleted | **terminal (expiry)** |

### 5.4 Transitions — 11 identified (10 active, 1 stubbed)

| # | Transition | Write site |
|---|---|---|
| T1 | ∅ → PENDING (`d5_upload` inserted, `ready=false` default) | `POST /uploads` handler `services/core-api/src/colab_core/app/routes/ingestion.py:227` |
| T2 | PENDING → READY (grid-only short-circuit): `ready=true, renderable=false, metadata_complete=false` | `services/pipeline-worker/src/colab_pipeline/domains/d5_ingestion.py:172-173` |
| T3 | PENDING → READY (stage-1 happy path, format detected): `ready=true` | `domains/d5_ingestion.py:222` |
| T4 | PENDING → FAILED: `ready=false, failed_at=now(), failure_class, failure_reason` via `_fail()` | `domains/d5_ingestion.py:135-137`; call sites `:189-191` (no files), `:209`, `:214` (format-detect failure / non-uniform pieces) |
| T5 | per-file `detected_format` recorded (`UPDATE d5_upload_file SET detected_format`) | `domains/d5_ingestion.py:517-520` |
| T6 | READY → REGISTERED: `d5_upload.registered_at = now()` (only when currently NULL) | `_MARK_REGISTERED` `services/core-api/src/colab_core/domains/d5_ingestion.py:115-118`; invoked from `createDataset` `routes/ingestion.py:439` and `attachUploadGridFiles` `routes/ingestion.py:629` |
| T7 | dataset created (`d3_dataset` inserted via `d3_catalog.register_dataset()`) | `routes/ingestion.py:445-453` |
| T8 | dataset → lineage confirmed (`d3_dataset.lineage_confirmed_at` set) | `domains/d3_catalog.py:758-759` @ `routes/ingestion.py:477` |
| T9 | dataset → lineage explicitly unknown (`d4_lineage_unknown` row) | `domains/d4_lineage.py:196` @ `routes/ingestion.py:479` |
| T10 | PENDING/expired → REAPED (`DELETE FROM d5_upload`, only when not registered and not processing) | `_REAP` `services/core-api/src/colab_core/domains/d5_ingestion.py:118-124`; worker `reap_expired_uploads()` `worker.py:189-210` |
| T11 | dataset → soft-deleted (`deleted_at`) | **`UNVERIFIED:` not implemented.** `deleteDataset` is a stub returning `NOT_IMPLEMENTED_P1` — `services/core-api/src/colab_core/app/routes/not_implemented.py:66`. No `SET deleted_at` write site exists anywhere in `services/core-api/src` (grep). The columns exist (`db/platform/schema.sql:236-240`) but nothing writes them. |

### 5.5 Terminal and failure states

| Class | State | Note |
|---|---|---|
| Terminal (success) | READY + REGISTERED | upload consumed into a dataset; the dataset then has no further upload-lifecycle state |
| Terminal (failure) | `failed_at IS NOT NULL`, `failure_class='영구'` | permanent |
| Terminal in practice (failure) | `failed_at IS NOT NULL`, `failure_class='재시도 가능'` | nominally retryable, but **`failed_at` being set excludes the row from the poll predicate regardless of class**, and **no code path clears `failed_at`** — `domains/d5_ingestion.py:370`. `UNVERIFIED:` whether retryable failures are ever retried — no retry-scheduling code found. |
| Terminal (expiry) | row hard-deleted by the reaper | `services/core-api/src/colab_core/domains/d5_ingestion.py:118-124` |
| Failure event | `upload.failed` | in `EVENT_TYPES` (`d5/events.py:26`) but deliberately **excluded from `STAGE_ORDER`** (`:29-35`) — it is the failure branch, not a stage |

### 5.6 Separate state models (do not conflate — 3 distinct machines)

1. **`d5_upload` current status** — booleans + timestamps, the derived "where is this upload now" — `db/platform/schema.sql:516-539`
2. **`d5_pipeline_event` event log** — the stage-by-stage trace (7 event types), *plus its own independent delivery/retry state*: `attempt`, `max_attempts` (default 5), `first_published_at`, `published_at`, `dead_lettered` — `db/platform/schema.sql:579-611`, `:596-599,603`
3. **`PipelineResult.status`** — in-memory per-file run status for stage-2 code, **never persisted** — `services/pipeline-worker/src/colab_pipeline/d5/pipeline.py:41-47`

---

## Appendix — UNVERIFIED items (7)

| # | Item | What was checked |
|---|---|---|
| U1 | `RELEASE_IMAGES` has 6 entries but the ⑩ banner says "5개 배포 단위" | `pipeline/lib.sh:99` vs `deploy.sh:184`; not resolved whether `migrator` is intentionally excluded from the count |
| U2 | Backup-artifact retention count | `backup/backup.sh`, `backup-full.sh`, `schedule.crontab` read; `backup/lib.sh` and `config.example.env` not opened |
| U3 | `POLICY` line numbers inside `db/platform/versions/0001_p0_platform.py`, `0004_p2_grid_axis_and_d5.py` | `grep -l` confirmed the string is present; files not opened |
| U4 | The trigger making `d2_permission_change` append-only | referenced by comment `domains/d2_access.py:64`; schema definition not located |
| U5 | Whether `failure_class='재시도 가능'` uploads are ever retried | grepped for writes clearing `failed_at` — none found |
| U6 | `T11` dataset soft-delete | `deleteDataset` is a 501 stub (`routes/not_implemented.py:66`); no `SET deleted_at` write site |
| U7 | `services/core-api/src/colab_core/app/dataset_search.py` internals | filename confirmed via grep as the `/searches` consumer; file not read in full |

## Appendix — counts for diagram authors

| Section | Count |
|---|---|
| §1 topology | **9 runtime nodes** (5 deploy units + 2 DBs + edge nginx + cloudflared) + 2 storage volumes; **13 edges**; 0 queues |
| §2 data flow | **17 steps** upload→viz; **5 pipeline stages** (`STAGE_ORDER`), 7 event types; **27 tables** (platform 21 + ai 6) |
| §3 auth | **9 ordered steps** per handler; **4** `d2_access` switches; **6** backing tables; 1 professor auto-grant bypass |
| §4 deploy | **14 deploy stages**; **3** image tags; **27 gates** (16 checks + 11 selftests), all blocking |
| §5 lifecycle | **6 enum fields / 23 values**; **6 derived upload states**; **11 transitions** (10 active); **4 terminal states** |
