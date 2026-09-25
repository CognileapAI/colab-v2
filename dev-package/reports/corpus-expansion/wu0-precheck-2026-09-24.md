# WU0 사전대조 · WU1 리허설 — 코퍼스 확장(dev 재시드) 착수 전 실측

메타 — intent `dev-package/intent/2026-09-24-corpus-expansion-dev-reseed.md` · 레인 lane-worker ·
기준 커밋 `fb89cd71` · 측정 2026-09-24T07:02Z · **dev 쓰기 0건**(읽기 전용 조회 · 게이트 · preflight 뿐).
계수 원본 = `dev-package/reports/corpus-expansion/wu0-precheck-2026-09-24.json`.

---

## 1. AI 체인 손실 예측표 — **손실 0행**

dev AI 사전 DB 의 alembic head 는 **`0007_merge_vocab_and_category`** 다.
지금 dev 에 선 다섯 표의 행은 **전부 마이그레이션이 심은 것**이고, 손으로 넣은 행은 **한 건도 없다.**
판정은 계수 일치가 아니라 **키 수준 집합 차분**으로 했다(`term`·`synonym`·`alias`·`concept_id`·`(src,relation,dst)`).

| 표 | 현재 행(dev) | reset 후 행 | 손실 | dev 에만 있는 키 |
|---|---:|---:|---:|---|
| `d9_concept` | 49 | 49 | **0** | 없음 |
| `d9_concept_edge` | 19 | 19 | **0** | 없음 |
| `d9_method_term` | 13 | 13 | **0** | 없음 |
| `d9_place_alias` | 4 | 4 | **0** | 없음 |
| `d9_topic_synonym` | 18 | 18 | **0** | 없음 |
| **계** | **103** | **103** | **0** | — |

근거 — 시드 정본의 행수가 dev 와 **키까지** 같다.
`k2_ontology_seed.sql`(method 13 · synonym 5 · alias 4) ＋ `topic_synonym_six.sql`(synonym 13)
＋ `k2b_concept_graph_seed.sql`(concept 49 · edge 19) = 13·18·4·49·19.
세 시드 파일은 `origin/develop` 과 `k3-resume` 사이에 **차분이 0** 이다(`git diff --name-only … db/ai/seed/` 공집합).

부기 셋 —

- ⭑ **재시드의 기본 대상 ref 는 `origin/develop`(`02d251d81b54`)이지 `k3-resume` 가 아니다.**
  develop 의 AI 체인은 `0007` 에서 끝나므로 `migrate-ai` 는 지금 dev 와 **같은 head** 로 되돌린다.
  `k3-resume` 를 대상으로 잡아도 손실은 0 이다 — `0008_d10_model_call_ledger` 는 빈 표 `d10_model_call` 하나를 **더할** 뿐이다.
- `codex/ai-search-next` 의 19행(`0009` synonym 9 · alias 4 / `0010` concept 5 · edge 1)과
  `0008_dataset_knowledge`(`knowledge` 스키마)는 **dev 에 적용된 적이 없다**(head 0007). 지금 잃을 것이 아니다.
- ⚠ **두 갈래가 같은 `0007` 을 부모로 `0008` 을 둘 세웠다** — `k3-resume` 의 `0008_d10_model_call_ledger` 와
  `codex/ai-search-next` 의 `0008_dataset_knowledge`. 두 갈래가 언젠가 합쳐지면 AI 체인이 **두 head** 가 되고
  `alembic upgrade head` 가 거부한다. 이 재시드의 조건은 아니지만 병합 전에 머지 리비전이 필요하다.
- 플랫폼 체인은 dev·develop·`k3-resume` 가 모두 `0033_admin_body_access` 로 **차분 0** 이다.

---

## 2. 계수표

### 2-1 dev 플랫폼 DB (읽기 전용 · 2026-09-24)

| 항목 | 값 |
|---|---:|
| 데이터셋(live / deleted) | 0 / 0 |
| 계정 · 연구실 | 0 · 1 |
| 프로젝트 · 프로젝트-데이터셋 | 0 · 0 |
| 파일 · 업로드 | 0 · 0 |
| `d3_dataset_autometa` 행 | 0 |
| `d3_dataset_variable` 행 | 0 |
| `d4_lineage_edge` · `d4_lineage_unknown` | 0 · 0 |
| `alembic_version_platform` | `0033_admin_body_access` |

자동 메타 fill(`format`·`variables`·`period_start`·`period_end`·`crs`·`grid`) = **전 축 0** — 표 자체가 비었다.
`d3_dataset_autometa` 의 실제 칸은 15개이고 그중 축 다섯이 여기 해당한다.
⇒ intent 의 「`01M1SC…` 는 이미 아무것도 가리키지 않는다」가 실측으로 확인됐다.

### 2-2 dev AI 사전 DB — 위 §1 표와 같다 (head `0007_merge_vocab_and_category`)

### 2-3 재시드 입력

| 항목 | 값 |
|---|---|
| `plan-manifest.yaml` `expected` | datasets 28 · edges 18 · data_bytes 3,641,736,593 |
| `build_plan.py --dry-run` 실측 | datasets 28 · edges 18 · files 543 · bytes 3,641,736,593 · grid_bytes 1,534,685,472 |
| 누락 파일 · 행 불일치 | **0 · 0** |
| 프로젝트별 | precipitation 5 · vegetation 7 · drought 2 · 포멧테스트 14 |
| `canonical-metadata.json` | 28행 · `start`/`end`/`granularity`/`basis` **28/28 채움** · `auxiliaryParents` 2 |
| 승인 계정 파일 | 0600 · 5행 · 칸 = `account_id`·`admin`·`email`·`initial_password_strategy`·`lab`·`lab_id`·`name`·`role` |

가공 단계 — 등재표의 칸 이름은 `processing_level` 이 아니라 **`level`** 이고 **28/28 전건에 있다**(Lv0 10 · Lv1 16 · Lv2 2).
⇒ intent §Q3 의 「28건 이름에 「(Lv.n)」 이 없으므로 이 열은 필수」는 맞되, **값의 출처는 이미 등재표에 있다.**

계보 — `parents` 는 **이름 문자열의 배열**이다. 역할 칸도 `method` 칸도 **없다**(18간선 전수).
⇒ intent 미해결 질문 3 의 답 = **28건 재적재는 `method` 를 기록하지 않는다.**
K3 정답의 `method` 는 빈 값으로 두고 그 사실을 WU4 보고서 첫 줄에 적는다.
역할은 `canonical-metadata.json` 의 `auxiliaryParents` 2건(Prediction(공간상세화) ← DEM · Aspect)만 `보조입력`, 나머지 16은 `주입력`.

### 2-4 참조 자료 (`COLAB_REF_ROOT` · 로컬 실재 확인)

| 항목 | 값 |
|---|---:|
| 파일 수 · 총량 | 2,474 · 4,686,003,775 B (4.4 GiB) |
| `.npy` | 1,831 · 3,867,520,824 B |
| `.tif` | 62 · 288,294,102 B |
| `.grib` · `.nc` | 1 · 149,514,336 B / 186 · 123,439,450 B |
| `.png` · `.hdf` · `.gpkg` · `.gz` | 249 / 8 / 2 / 22 |
| 계획이 고르는 양 | 3,641,736,593 B (543 파일) |

⇒ intent 미해결 질문 1 해소 — 참조 자료 뿌리는 **실재한다**(체크아웃과 나란한 `03 Reference-Data`).

---

## 3. ID 재박기 대상

`01M1SC` 총 4,424회 · 46파일. 실행 경로에 박힌 것은 **6파일 490회 · 서로 다른 ULID 122개**뿐이다.

| 재박기 대상 (실행 경로) | 횟수 |
|---|---:|
| `eval/k4-search/fixtures/reference/expanded-normalized-02.json` | 228 |
| `eval/k4-search/fixtures/reference/dev-data-snapshot.json` | 123 |
| `eval/k4-search/golden-cases.json` | 113 |
| `eval/k4-search/golden-set.md` | 11 |
| `eval/k3-lineage/lineage-cases.json` | 10 |
| `eval/k3-lineage/test_llm_lineage_probe.py` | 5 |

- 건수가 코드에 박힌 자리 = `eval/k4-search/golden_baseline.py:134` `if len(expected) != 9:`.
- 재박기 **불요** = `eval/k4-search/fixtures/reference/stage-evidence-packet-02.json` — ID 0건(이름 기준).
- `services/**` 에 박힌 ID **0건** — 제품 코드 무변 목표가 성립한다.
- 문서 19회(intent·PRD·세션)는 선택. `dev-package/reports/**` 33파일 3,915회는 **과거 실측 기록이라 고치지 않는다.**
- `01M2F4` 총 6회 — **실행 경로 0건.** 전부 세션·보고서 기록이라 재박기 대상이 아니다.

---

## 4. 게이트 · preflight · 리허설

### 4-1 게이트 (선언 집합 `gates/run.sh task`)

```
seed-plan-drift     green — datasets 28 edges 18 data_bytes 3641736593 · 등재표 = md 재생성본과 동일
dev-reseed-selftest green — 픽스처 7 · 통과 7 · 결함 0 · 판정 못 함 0
── 계 : green 2 / red(판정) 0 / red(준비) 0
```

### 4-2 `--preflight-only` — **통과 9 · 미달 2**

| 미달 항목 | 내용 |
|---|---|
| `dev-sha` | dev 실행 sha `ea21d8c2aa54` ≠ 대상 `02d251d81b54`. **deploy 단계가 꺼진 탓**이라 전 단계 실행에서는 해소된다. |
| `resources` | **EC2 디스크 여유 1,894,973,440 B < 2,147,483,648 B (2 GiB)** — 부족 252,510,208 B. |

디스크 실측 = 총 21,396,172,800 B · 사용 92% · 여유 1.76 GiB.
회수 가능분 = 도커 이미지 3.911 GB(41개 중 활성 5) ＋ 빌드 캐시 123.5 MB ≈ **4.03 GB**.
⇒ `docker image prune` 한 번이면 임계값을 넘는다. **WU2 전에 사람이 해야 한다.**

### 4-3 `--rehearse` — **실행되지 않았다 (원격 원시동작 0건)**

preflight 가 위 두 항목에서 fail-closed 해 리허설 단계에 닿기 전에 멈췄다.
멈추지 않았더라도 `rehearse_release_plan`(stages.sh:1015·1029)이 `--release-plan` 부재로 **78** 을 냈을 것이고,
그 검사는 `HEAD == TARGET_SHA` 도 요구하는데 현재 HEAD(`fb89cd71`)와 대상(`02d251d81b54`)이 다르다.

**리허설 불가 — 사유 3** ⑴ preflight `resources` 미달 ⑵ preflight `dev-sha`(deploy 꺼짐) ⑶ `--release-plan` 입력 부재.

리허설이 **원격에 아무것도 쓰지 않는다**는 것은 소스에서 먼저 확인했다(돌리기 전 · 항목 아홉) —

| 원시동작 | 근거 | 판정 |
|---|---|---|
| `psql_master_query` | `stages.sh:1037` — `SELECT 'quoted', count(*) FROM pg_stat_activity` | 읽기 |
| `ssh_script` | `stages.sh:1038-1045` — `printf` 되받기뿐 | 읽기 |
| `compose_ps` | `stages.sh:1047-1052` — `compose ps --services` | 읽기 |
| `migrator_platform` · `migrator_ai` | `stages.sh:1055-1065` — `alembic current`(upgrade 아님) | 읽기 |
| `reset_tool_s3_plan` | `stages.sh:1071-1080` — `--phase s3-plan` 만. 삭제는 `--phase s3-apply` 한 자리에만 있고(`reset_dev_environment.py:429-446`) `--apply-plan`＋`--plan-sha256` 을 요구한다 | 읽기 (＋원격 임시 폴더 `mkdir`→`rm -rf`) |
| `psql_owner_url` | `stages.sh:1082-1090` — `:ro` 마운트 · `select 1` | 읽기 |
| `doctor_summary_line` | `deploy-verification.sh` — `/repo:ro`·`/state:ro`·`/etc/colab:ro`·`--rm` · `deploy_doctor.py:318-319` 가 `default_transaction_read_only=on` 으로 접속 · S3 는 ListObjects 뿐 | 읽기 |
| `runner_phase_report` | `runner.py:1968 phase_report` — 로컬 상태 파일로 표를 찍을 뿐 네트워크 0 | 읽기 |
| `agent_browser_title` | `stages.sh:1109-1112` — `open` ＋ `get title` | 읽기 |

⛔ 유일한 원격 쓰기 = ⑸ 가 EC2 에 만드는 **임시 폴더**(`$REMOTE_OUT/rehearse`)이고 같은 스크립트가 `rm -rf` 로 지운다.
제품 데이터·DB·S3 를 바꾸는 줄은 **없다.**

---

## 5. 게이트 ③ 에 올릴 판단 요약

1. **AI 사전 손실 위험은 없다** — dev 의 103행은 전부 마이그레이션 시드이고 키까지 일치한다. `reset` 뒤 같은 103행이 되돌아온다. 손으로 넣은 행 0.
2. **지금 no-go 사유는 디스크 하나다** — EC2 여유 1.76 GiB < 2 GiB. `docker image prune`(회수 가능 ≈ 4.0 GB) 뒤 preflight 를 다시 돌려 `resources` 가 ✓ 가 되기 전에는 `reset` 을 내지 않는다.
3. **리허설이 아직 한 번도 실모드로 돌지 않았다** — DR-4 가 남긴 「실행된 적 없는 원격 줄」 위험이 그대로다. 디스크 해소 ＋ `--release-plan` 준비 ＋ 대상 ref 확정(`origin/develop` 기본값을 쓸지 `k3-resume` 로 바꿀지) 뒤 `--rehearse` 를 통과시키고서 게이트 ③ 을 다시 연다.
