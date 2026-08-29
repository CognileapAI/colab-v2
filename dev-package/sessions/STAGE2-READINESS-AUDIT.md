# Stage 2 개발 준비 실측 감사

- 시점 = 2026-08-29 · `main` = `1ee753e`
- 대상 = `dev-package/sessions/STAGE2-REMAINING.md` 의 주장 전부
- 방법 = 문서를 믿지 않고 게이트·시험·코드를 직접 돌려 대조. 세 갈래 병렬(대장 정합성 · 착수가능 5건 실물 · 환경 기동)

---

## 1. 문서가 틀린 것 (정정 4건)

| 문서 서술 | 실측 | 근거 |
|---|---|---|
| 대장 검사기 red **1** (`W-1`) | red **3건** | `./gates/run.sh work-item-consistency` → `불일치 3건` = `S2b` · `R-1` · `S2` |
| `X-6` 별칭 재부착 = 착수 가능 1순위 | **이미 끝남** | 삼킴 구문 부재. `9c6fc92` · `31f36a5` 가 제거. `infra/staging/pipeline/lib.sh:135-159` 가 종료코드＋이미지 ID 대조로 판정, `infra/staging/deploy.sh:220-226` 이 원장 green 앞에 섬. 실패 픽스처 P15·P16·P20 존재, selftest 37/22 GREEN |
| `F-2` 카탈로그 키워드 입력 제거 | **제거할 입력이 없음** | `components/catalog/**` 에 `<input>` 0건, `useCatalog.ts:29` 질의 모델에 `keyword` 필드 없음. 진입점은 이미 `SearchHero` 하나 |
| `unknown` 단계 미배정 = 2건 | **5건** | `R1` · `IS4` · `G1b` · `P4` · `LV-4` |

- `X-6` · `F-2` 의 잔여는 코드가 아니다 — `X-6` 는 대장 상태(`work-items.yaml:713` `status: open` · `evidence: null`) 갱신, `F-2` 는 문구 정합 하나
- `F-2` 문구는 무의존이 아니다 — `DatasetsPage.tsx:60`(「홈의 AI 검색」)과 `SearchHero.tsx:34-37`(「적혀 있는 낱말 그대로」)이 정반대를 말하고, 정답은 `T-1` 한국어 검색 재작성이 무엇을 바꾸느냐에 달림. **`F-2` 는 `T-1` 종속**
- 문서가 든 `F-2` 막이(「`frontend/**` 가 `F-1` 과 겹침」)는 실재하지 않음 — 겹치는 파일 0건

## 2. 문서가 맞은 것

- 총 95건 · `stage: stage2` 34건 · 상태 분포(끝남 9 · 진행 4 · 대기 19 · 갈라짐 1 · 하지않기 1) 전부 정합
- 표 25건 ＋ 끝난 9건 = 34, 대장과 id 기준 완전 일치. 편도 누락·과잉 0건
- 게이트 27종 중 26종 green — `planning-freshness` · `import-boundary` · `banned-import` · `ai-no-lineage-write` · `migration-single-head` · `stage2-markers`(17 passed · skipped 0)

## 3. 착수가능 3건의 진짜 손잡이

| 항목 | 판정 | 실작업 |
|---|---|---|
| `PV-1` 미리보기 뒷단 | 조건부 | ⑴ `app/worker.py:147` `stage1=True` **하드코딩 해제**(`d5_ingestion.py:218` `if stage1:` 이 감지 직후 `ready` 로 빠진다) ⑵ **autometa 소비자 신설** — `crs` · `grid` 를 채우는 코드가 `core-api` 에 0건(`d3_catalog.py:492-496` 은 `format`·`bundle_file_name`·`total_size_bytes` 만) ⑶ `layout.json` 슬롯은 이미 있으나 **렌더 산출물용** → 「종류 신설」이 아니라 **재사용 판정** |
| `F-1` 미등록 미리보기 화면 | 조건부 | 완료 정의 ⑵(`work-items.yaml:785`)는 「구간 조절 없음」인데 `PreviewControls.tsx:33-48` 이 **구간 수 select(3~9, 기본 6)** 를 렌더. **정의와 코드가 정면 충돌 — 판정 없이 못 닫는다.** 프론트 277 passed(문서의 274 보다 3 늘었음) |
| `K3` 계보 제안 서비스 | 조건부 | 선행 3건(K2 시드 · `core-ai.yaml:64-90` `suggestLineage` 선언 · 업로드 모달) 전부 실물로 끝남. 다만 완료 정의(`work-items.yaml:980`)가 「제안 품질」 한 줄뿐 **합격선 부재 = 닫기 오라클 미정의**. 평가셋 `eval/s2b-alayer/run.py` 는 staging 컨테이너 실호출 의존이라 로컬 재측정 불가(기준선 = 충족 7 · 미충족 8 · 보류 1) |

## 4. 환경 — 대체로 준비됨

- staging **8/8 healthy**, 앱 5종 전부 `:30b3e0a7b3f3`. 재기동 불필요
- env 결손 **0** — `~/.colab-v2-staging.env`(0600) 가 compose 요구 19키를 덮음
- 툴체인 — docker 29.3.0 / compose v5.1.1 · python 3.12.3 ＋ uv · node v22.22.1 ＋ pnpm 11.1.2
- env 를 손으로 채우면 **전건 green** — core-api 471 · pipeline-worker 160 · viz-render 119 · frontend 277

**단, env 없이 돌리면 붕괴로 보인다** — core-api `471 errors`, pipeline-worker `23 failed·15 errors`, viz-render `8 failed`. 전부 환경 게이트이고 **skip 이 아니라 fail 로 떨구는 의도적 설계**(green-by-skip 금지). 즉 「118/0 섬」은 staging 밖에서 재현되지 않는다.

## 5. 오늘의 블로커 (순위)

| 순위 | 블로커 | 한 줄 수정 |
|---|---|---|
| 1 | **테스트 env 4종이 미문서화** — `COLAB_CORE_TEST_SUBJECTS_FILE` · `COLAB_REFERENCE_DATA` · `COLAB_PIPELINE_DB_URL` · `COLAB_AI_TEST_DICT_DB_URL`. `RESTART §2-④` 는 `COLAB_CORE_TEST_DATABASE_URL` 하나만 적는다 → 모르면 471 errors 를 「환경 붕괴」로 오진 | `RESTART §2-④` 에 4종의 이름·값 출처를 표로 추가 |
| 2 | **`services/ai-service/.venv` 부재** — 4개 서비스 중 유일 | `uv venv .venv && uv pip install -r requirements.txt -r requirements-dev.txt` (실측 설치 성공 → 72 passed) |
| 3 | **ai 체인 일회용 DB 절차 부재** — `setup-db.sh` 대응물이 core-api 에만 있어 ai-service 26건이 구조적으로 못 돈다 | `db/ai` 체인용 부트스트랩을 `services/ai-service/tests/fixtures/` 에 core-api 와 같은 규약으로 추가 |
| 4 | **`I3` ⑷⑸ 롤백 왕복이 원리적으로 막힘** — 원장 green `deploy` 행이 1건뿐 → 롤백 대상 0건 | 코드 무변경으로 `approve.sh` → `deploy.sh --target staging` 1회 더 돌려 green 2행을 만든 뒤 왕복 측정 |
| 5 | **`I3` ⑴ 자동 트리거 미설치** — `install-schedule.sh` 미실행, crontab 에 배포 블록 없음(백업 블록만) | `infra/staging/pipeline/install-schedule.sh` 실행 후 첫 무인 회차 로그를 원장과 대조 |
| 6 | **`work-item-consistency` red 3건이 `I3` ⑽ 을 잠근다** | `S2b`·`S2` 는 staging 실물 계수(데이터셋·파일·계보)를 세어 한쪽으로 확정, `R-1` 은 잔여 셋(`POST /searches` · `preflight` 성질 · `:i2` 이력) 실측 |
| 7 | **문서 참조 오류** — `I3` 15행 정본은 `DEPLOY-CURRENT.md` 가 아니라 `sessions/I3.md §6` | `DEPLOY-CURRENT.md` 머리에 포인터 한 줄 |

- **1~3 만 닫으면 오늘 코드 착수 가능** — 전부 환경·문서 문제, 코드 문제 아님
- **4~6 은 착수를 막지 않고 종결을 막는다** — `CLAUDE.md §4`(「I2 이후 staging 배포 green 이 완료 판정에 붙는다」)를 적용하면 ⑽ 이 red 인 동안 **어떤 Stage 2 항목도 완료 판정을 못 받는다**

## 6. `I3` 15행 — 닫힘 9 · 열림/부분 6

- 열림 = ⑴ 무인 완주 · ⑷ 롤백 왕복 · ⑸ 롤백 대상 확인 · ⑽ 게이트 전 종 green
- 부분 = ⑵-b 판정기 red 증거(원장 red 행은 헬스 판정 **미도달** 단계라 증거 아님) · ⑾ 배포 직전 `/healthz` 값 미측정
- 기구는 전부 있다(`infra/staging/` 21종) — **부족한 것은 돌린 회차다**

## 7. `[미확인]`

- `K3` 완료 정의의 합격선 수치 — 어디에도 없음. 정하는 것은 사람의 자리
- `F-1` 구간 조절 select 를 걷어낼지 정의를 고칠지 — 판정 대기
- `PV-1` COG 산출물이 `layout.json` 의 렌더 슬롯을 그대로 쓰는지 — 규약 본문에 없음
- `unknown` 5건의 단계 배정 — 임의로 정하지 않았다
