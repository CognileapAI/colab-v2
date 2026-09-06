# 창 9 레인 보고 — dev(AWS) 배포 ＋ 창 8-b 가 남긴 열린 것 넷

집행 2026-09-06 · 워크트리 `.claude/worktrees/agent-af685d3b68124c4bb` · 브랜치 `integration/w9-dev-deploy`
작업지시 = `dev-package/03-HANDOFF.md` 「창 9」 블록 · 런북 = `infra/dev/README.md` · `docs/DEPLOY.md §6-1`
등재 = `PLAN-SoT §9 〈368〉`~`〈375〉`

---

## ⛔ 먼저 읽을 것 — 전 게이트 전수는 **돌리지 않았다**

**Ted 판정 2026-09-06 11:35** 축자 — 「이 레인에서 전수를 돌리지 않는다. **다음 세션이 `main` ff 전에 `-j 4` 전수를 돌린다**」.

- 이 레인의 전수 = **`[미실행]`**. ⛔ 「green」도 「red」도 아니다 — **안 돌렸다**.
- **`main` fast-forward 를 하지 않았다.** 이 레인은 `integration/w9-dev-deploy` 를 **push 까지만** 한다.
- **다음 세션의 진입조건** = `-j 4` 전수 **`green 50 / red(판정) 0 / red(준비) 0` 을 한 번의 실행으로** → **그 뒤에 ff**.
- 중단된 로그가 하나 있다 — `gates-all-w9-ABORTED.txt`(시작 11:21:50 · 중단 11:37 경 · **결과 줄 없음**). 옆의 `…-ABORTED.NOTE.txt` 가 그 사실을 못 박는다. **판정 근거로 쓰지 않는다.**
- 이 레인이 **실제로 돌린 것** = 좁은 문서 게이트 셋뿐이고 **전수를 갈음하지 않는다**(아래 `§7`).
  ⚠ 이 회차가 만진 코드·설정(`infra/dev/compose.yml` · `db/ai` 신설 리비전·시드·선언)은 **아직 전수의 판정을 받지 않았다.**

**한 줄** — **배포는 섰다**(4/4 healthy · `deploy_doctor` **14/14 를 한 번의 실행으로**). **열린 것 넷 중 둘을 닫았고**(ⓐ `sourceLabel`→`BF-9` · ⓒ 주제 동의어) **하나는 막는 것이 바뀌었으며**(ⓑ 스풀은 켜졌는데 회수가 s3 에서 못 돈다) **하나는 원인만 규명해 등록**했다(ⓓ). ⛔ **새 블로커 하나** — viz-render 가 직전 회차에 **3회 OOM-kill** 됐다.

---

## 0. 진입조건 — 실측

| | 조건 | 실측 | 판정 |
|---|---|---|---|
| ㉠ | 창 8-b done | `〈352〉`~`〈367〉` · `main` = `b0671f8` · 전수 green 50 한 실행(`〈367〉`) | **선다** |
| ㉡ | AWS 접근 | `aws sts get-caller-identity` 성공(`user/colab-platform-s3-uploader-dev`) ＋ 그 키로 ssh 성공 | **선다** |
| ㉢ | 유료 전환 | 이 레인 IAM 으로는 **영영 못 잰다**(`〈350〉`) | **미확인** (Ted 눈) |
| ㉣ | `t4g.medium` | IMDS 실조회 = **`t4g.small`** — `〈349〉` 완화 판정으로 연다 | **완화로 열었다** ⚠ `§6` |

---

## 1. 이 회차가 만진 것 — 코드·설정 3건 (전부 같은 커밋 `20b3715`)

| 무엇 | 왜 | 등재 |
|---|---|---|
| `infra/dev/compose.yml` — 볼륨 `events` ＋ 두 단위 env ＋ `volume-init` `chown` | Ted 판정 — dev 트리거 스풀을 켠다 | `〈368〉` |
| `db/ai` — `schema.sql` CHECK 6값 ＋ 시드 `topic_synonym_six.sql`(13행) ＋ 리비전 `0006_topic_vocab_six` | Ted 판정 — 주제 동의어. `〈359〉`-㉶ 가 스스로 적어 둔 다음 회차 | `〈369〉` |
| `infra/staging/manifest-refdata.json` — 뿌리 4건에 `sourceLabel` | ⓔ(`BF-9`)를 세우려면 잴 대상이 있어야 한다 | `〈371〉` |

⛔ **켜지 않은 것** — `COLAB_WORKER_STAGE2`(이 판정의 대상이 아니다 · dev 워커는 stage 1 그대로) · 개념 그래프 주제 노드 4개(별도 오라클 `k2b-graph-standard.tsv` 가 걸려 있다 · 등록만).

---

## 2. ⑵⑶ 배포 — 판정 기준 · 실측 · 로그

**배포 sha = `20b3715d1db0`** · **롤백 태그 = `COLAB_IMAGE_TAG=dev-ea036c50c921`**(직전 `CURRENT_SHA`) · 사슬 `dev-0045f2233a04` → `dev-ea036c50c921` → `dev-20b3715d1db0`.

| 단계 | 판정 기준 | 실측 | 로그 |
|---|---|---|---|
| `build.sh` | 이미지가 서고 종료 0 | **exit 0** · 5 이미지 **`Architecture=arm64` 실측 통과** · tar **273M** | `build.txt` |
| `ship.sh` | 전송 ＋ `docker load` ＋ 종료 0 | **exit 0** · `Loaded image` 5줄 · `:dev` 재태그 · **이미지 ID 대조 5/5 일치** | `ship.txt` |
| EC2 `up.sh` | **4 단위 healthy** ＋ 종료 0 | **exit 0** · **4/4 healthy** · `CURRENT_SHA` = `20b3715d1db0` | `up.txt` |
| `deploy_web.py` | 종료 0 ＋ CloudFront 가 새 번들 | **exit 0** · **96파일 · 5,682,848 B** | `deploy-web.txt` |

**헬스 본문(조용한 `local` 을 잡는 자리)** — `pipeline-worker storageMode=s3` · `viz-render sourceMode=s3` · `previewSink=s3` · `tileBranch=꺼짐`.

**CloudFront 실측** — 로컬 `dist` ↔ 서빙 중 `index.html` 이 **같은 해시 자산**(`assets/index-Rwvt3PTb.js` · `assets/index-DEWaifZ9.css`)을 가리키고 그 js 가 **200 · 446,416 B · `max-age=31536000, immutable`**, `index.html` 은 **`no-cache`**(`CLAUDE.md` 배포 절 5). `/api/v1/me` **401 JSON**. 로그 `cloudfront-check.txt`.

### 2-a. ⭑ 마이그레이션 — **직접 조회로 판정했다**

⛔ `up.sh` 출력으로 판정하지 않았다. **`colab_backup` 롤**로 DB 를 읽었다(`〈363〉` 규율 — RLS 아래에서 「없다」를 앱 롤로 판정하지 않는다).

| 체인 | 배포 전 | 배포 후 | head 개수 |
|---|---|---|---|
| platform | `0013_topic_vocab_six` | **`0014_merge_ra1_and_topic_vocab`** | **1** |
| ai | `0005_k2b_concept_graph_seed` | **`0006_topic_vocab_six`** | **1** |

- 두 head 가 **합류했다** — `rebase-report.md §5` 가 예고한 그대로(`0013_ra1_ext_interval_period` ＋ `0014_merge…` 둘이 올라갔다).
- `deploy_doctor` ⑥⑦ 도 **같은 값을 독립으로** 냈다(축자 「DB = 레포」).
- **R-A 신설 열 4개가 실제로 섰다**(`information_schema` 조회) — `d3_dataset_description.observation_interval_{value,unit}` · `d3_dataset_autometa.{file_extension,period_granularity}`.
- 로그 `migration-heads.txt`.

### 2-b. ⭑ 데이터 계수 — **무변**

| | 배포 전 | 배포 후 |
|---|---|---|
| `d3_dataset` | 14 | **14** |
| `d3_file` | 434 (본체 414 ＋ 기준 격자 20) | **434** (414 ＋ 20) |
| `d4_lineage_edge` | 6 | **6** |

⟹ **배포가 데이터를 건드리지 않았다.**

---

## 3. ⑷ `deploy_doctor` — 14/14 를 **한 번의 실행으로**

**판정 기준** = 축자 「14/14 를 **한 번의 실행으로**」 · **재시도해 모은 14 는 14 가 아니다**.
**실측** = `항목 14 — ✓ 14 · ✗ 0 · ─ 0` · 축자 **「전 항목 통과 (─ 0 — 14 항목이 실제로 돌았다)」** · **exit 0**. 로그 `deploy-doctor.txt`(전문).

- 집행 방식 = `docs/DEPLOY.md §6-1` 그대로 **EC2 위 컨테이너 격리 실행**.
- **선행** = EC2 `/opt/colab-repo` 를 배포 sha 로 **tar 동기화**(`〈361〉`-㉯ · 이제 `infra/dev/README.md` 에 적혀 있다). 동일성 실측 = `deploy_doctor.py` md5 **로컬 = 원격 `49ad1774…`** · ai 리비전 6개(신설 `0006` 포함) 확인. 로그 `repo-sync.txt`.
- 운영자 키는 `--env-file`(umask 077)로 넘기고 **실행 직후 `shred -u`** — 잔여 0 확인.
- 주요 값 — ⑪ 앱 자격증명 출처 **`imds`**(만료 372분) · ⑫ 환경 짝 dev · ⑬ `/api/v1/me` **401 JSON** · `/previews/*` **403 비-HTML** · ⑭ 백업 **7.3시간 전 · 객체 19건**.

---

## 4. ⑸ 배포 뒤 확인 — R-A 층별 연막

⛔ **읽기 전용 또는 비영속 요청만.** 새 데이터셋 0 · 삭제 0. 연막 전후 `totalCount` **14 무변**.

| 층 | 항목 | 판정 기준 | 실측 |
|---|---|---|---|
| DB | `WU-A5` 확장자 표기 | 상세에 확장자가 실린다 | ⭐ `basicInfo.fileExtension` = `'docx'` |
| 서버 | `WU-A4` 설명 필수 | 설명 없는 등록 **400** | ⭐ **400** 축자 「설명을 적어 주세요.」 · 공백만도 **400** |
| 서버 | `WU-A6` 관측 간격 | 반쪽이면 **400** | ⭐ **400** 축자 「관측 간격은 숫자와 단위를 함께 적어 주세요.」 |
| 서버 | 어휘 6값 | 어휘 밖 주제 **400** | ⭐ **400** ＋ `allowed` **6값**(`가뭄`·`파일 포맷 예제` 포함) |
| 서버 | `WU-A13` 확장자 혼합 | 2종이면 **400** | **설치본 확인**(아래) |

⛔ **`WU-A13` 의 400 실호출은 하지 않았다** — 2종 확장자 **업로드를 만들어야** 하고 dev 에 `deleteDataset` 이 없다(창 8-b ⓖ 선례 — 매니페스트 밖 데이터를 만들지 않는다).
⟹ **도는 이미지 안의 코드로 확인**했다 — `ingestion.py` 축자 「한 데이터셋의 조각은 확장자가 한 종류다 — 2종 이상이 실려 왔다」. 같은 방식으로 `_TOPICS` 6값 · `INTERVAL_UNITS` · `PERIOD_GRANULARITIES` · ai `TOPICS` 6값도 **설치본에서** 확인했다.
로그 `post-deploy-ra-smoke.txt` · `post-deploy-ra-installed-code.txt`.

---

## 5. ⑹ 열린 것 넷 — 항목별 판정

### ⓐ `sourceLabel` ⟹ ⓔ(`BF-9`) — ⭐ **green. `BF-9` `open` → `done`** (`〈371〉`)

- **막던 것은 코드가 아니라 잴 대상이었다**(`〈364〉`-㉯). `BF-9` 의 코드는 `〈330〉` 에서 이미 섰다.
- **값은 지어내지 않았다** — 각 `summary` 의 「출처 =」·「생산 =」 **축자**.
  ⭑ **뿌리는 4건이고 표기는 3종이다** — 강수 Lv.0 이 **HSR·RN15 둘**이고 둘 다 `기상청 API허브` 다. **「3건」으로 세면 하나가 빠진다.**
- **두 자리에 넣었다** — 매니페스트(다음 적재가 처음부터 든다) ＋ dev 는 **기존 op `updateDataset`**. ⛔ DB 손질 0.
- **실측** — `PATCH` **200 × 4** · 되읽기 **4/4 일치** · `lineageState` **`기록 없음` → `원천`** · **원천 노드 4 · 원천 간선 4**(`parentDatasetId: null` · **`method: null`** · `parentRole: 주입력` · `origin: manual`).
- ⭑ **원장 계수는 움직이지 않았다** — `d4_lineage_edge` **6** 그대로다. 원천 간선은 `source_label` 에서 **파생**이지 저장 행이 아니다(`routes/lineage.py:92-94`). **API 뷰의 수와 원장의 수는 다른 것이다.**
- 완료 정의 ⑴✅ ⑵(시험이 합격선 — `03-HANDOFF` ⓔ 에는 ⓑⓒⓓ 와 달리 **눈 확인 표시가 없다**)✅ ⑶✅ ⑷✅ ＋ dev 배포 green ⟹ **닫는다.**
- 산문 두 곳도 뒤집었다(`03-HANDOFF §1` · `WORK-UNITS §11`) — **`work-item-consistency` 가 red 로 잡아 준 자리**이고 고친 뒤 green.
- 로그 `post-deploy-e-sourcelabel.txt`.

### ⓑ `COLAB_VIZ_TRIGGER_SPOOL` — ⛔ **켰다. 그런데 `BF-12` ⑶ 은 여전히 안 선다** (`〈372〉`)

- **㉮ 종전 원인은 실제로 고쳐졌다** — 두 단위가 `/srv/viz-events` 를 **같은 아이노드(`66305:25586325`)** 로 보고 **양쪽 쓰기 성공**(uid 10001). ⭑ `volume-init` 의 `chown` 대상에 넣어 **staging 이 `#59` 로 물렸던 자리를 피했다**(`〈269〉`-㉲).
  **회수 요약 줄이 0줄 → 찍힌다.** ⟹ 「루프 미기동」 해소.
- **㉯ ⛔ 그런데 찍힌 줄이 이것이다** — 축자 **「지도 타일 회수 red(준비) — 주체 0건 · 계산 불가 0건 — 판정을 시작하지 않았다」**.
- **㉰ 원인 = 구조다.** `tile_reclaim.run_pass` → `tile_liveness.subjects_from_storage(storage_root)` 가 **로컬 디렉터리를 훑는다**(축자 「그리는 쪽(D7)에는 원장이 없어 **디렉터리가 곧 사실**」). dev 는 `COLAB_VIZ_SOURCE_MODE=s3` 라 **사실이 버킷에 있다** ⟹ **주체 0건** ⟹ fail-closed.
  ⭑ **새 결함이 아니라 드러난 결손이다** — staging(로컬)에서는 성립하고 **dev(s3)에서는 구조적으로 성립할 수 없다.** **스풀을 켠 것이 그 사실을 드러냈다.**
- **㉱ 안전 쪽은 지켜졌다** — `apply` 기본 `False` ＋ fail-closed ⟹ **삭제 0건**. ⑶ 의 「삭제가 0」은 만족하지만 **「첫 한 바퀴의 계수」가 없으므로 green 으로 세지 않는다.**
- **㉲ ⟨Ted 판정 11:30⟩ 60분을 기다리지 않는다** — 주기 한 바퀴(3600초)는 **다음 회차가 읽는다**.
  켠 시각 = **`2026-09-06T02:11:35Z`**(viz-render `StartedAt`) ⟹ 첫 주기 ≈ **`03:11Z`**.
  명령 = `docker logs colab_v2_dev_viz_render 2>&1 | grep '회수'` (트리거 쪽은 `| grep '트리거 집행'`).
  ⟹ **주기 계수 = `[미측정]`** 이고 **0 으로 적지 않는다.** ⚠ 다만 **㉰ 가 구조적 원인이라 시간이 바꾸지 않는다.**
- ⟹ **`BF-12` `open` 무변.** 막는 것이 「루프가 안 돈다」 → **「s3 에서 주체를 못 모은다」**로 바뀌었다(D7 설계 판정 · 등록만).
- 로그 `post-deploy-b-spool.txt`.

### ⓒ `db/ai` 주제 동의어 — ⭐ **green** (`〈369〉`)

- `〈360〉` 이 멈춘 이유는 **동의어 값이 정본 무근거**라서였고, **Ted 가 값을 내려 지어낼 것이 0** 이 됐다.
- 집행 셋 — 선언(`db/ai/schema.sql` CHECK **4값 → 6값**) ＋ 적재물(**신설** `topic_synonym_six.sql` 13행) ＋ 리비전(**신설** `0006_topic_vocab_six`).
  ⭑ **`k2_ontology_seed.sql` 에 덧붙이지 않았다** — 그 파일은 `0003` 이 실행하고 그때의 CHECK 는 4값이라 **빈 DB 에서 `0003` 이 죽는다**.
- **DB 실측** — `d9_topic_synonym` **18행**(기존 5 ＋ 신규 13) · CHECK 가 **6값** · 새 13행 전건 확인.
- **실동작 실측**(질의 → 결과) —

  | 질의 | 결과 |
  |---|---|
  | `SPI` · `가뭄` · `SPEI` · `drought` | **가뭄 — 시군구 주간 SPI/SPEI-4weeks (Lv.1)** 1건 |
  | `grib` · `netcdf` | **파일 포맷 실습 5건** |

  ⭑ `grib` 가 GRIB 하나가 아니라 5건을 내는 것은 **설계다** — 동의어는 **주제로** 가고 그 주제(`파일 포맷 예제`)에 5건이 있다.
- 로그 `post-deploy-c-synonyms.txt` · `migration-heads.txt`.

### ⓓ `load-seed.py` 409 — **등록 그대로. 원인은 규명했다** (`〈374〉`)

- ⭑ **원인은 「2패스」가 아니라 계수 단위 불일치다.** `decide()` 가 `have`(＝ `listDatasets` 의 `fileCount` — **본체만**, dev 실측 **414**)와 `planned`(＝ `len(ds["files"])` — **본체 ＋ 격자**, 매니페스트 **434**)를 견준다 ⟹ 격자를 가진 데이터셋은 **영원히 「이어붙임」** ⟹ 이미 붙은 격자를 다시 붙이려다 **409**.
- ⛔ **고치지 않았다 — 「작고 시험이 덮는 고침」이 아니다.** 본체끼리 견주면 409 는 사라지지만 **「격자만 빠진 것을 고치는」 능력을 잃는다**(그 판정이 지금 `have < planned` 하나에 얹혀 있다). 지키면서 고치려면 **격자가 이미 붙었는지 물어야** 하고 그것을 아는 op 이 이 도구의 **넷 안에 없다** ⟹ **R-1 선언을 넓히는 설계 판정**이다.
- **급하지 않은 근거** — fail-closed(`Abort`) · dev 는 이미 매니페스트와 일치(14/434/6) · 재적재 계획 없음.
- ⭑ `〈362〉`-㉱ 의 원인 서술(「2패스」)은 **이 회차가 정정한다.**

---

## 6. ⛔ 새 블로커 — viz-render OOM 3회 (`〈373〉`)

**〈349〉-㉱ 의 「멈추고 보고」 조건이 실제로 성립했는데 아무도 멈추지 않았다.**

- **실측** — `oom-kill` 전수 4건 중 **3건이 2026-09-06**(`00:09:16` · `00:12:01` · `01:31:22`), 전부 **같은 cgroup = `colab_v2_dev_viz_render`**(`docker inspect` 대조). 그 컨테이너 **`RestartCount` = 4**(다른 셋은 0).
- **창 8-b 보고는 틀리지 않았다 — 시점이 다르다.** 그 「신규 0건」은 **배포 70분 뒤** 관측이고, 3건은 **그 뒤 재적재·미리보기 구간**에 났다.
- **부하가 없을 때도 높았다** — 배포 직전 실사용 **436.3 MiB / 640 MiB (68.2%)**(요청 0). 재기동 뒤 **46.8 MiB** ⟹ **오래 도는 동안 쌓인다.**
- **이 회차는 막지 않았다** — 배포 뒤 4단위 합 **≈257 MiB / 1,792 MiB** · 스왑 사용 0 · **신규 OOM 0건** · 4/4 healthy.
- ⚠ **위험은 지우지 않는다** — `〈368〉` 로 켠 루프가 **하필 그 단위에 스레드를 하나 더 얹는다**. 실부하 회차의 판정 자리다.
- **판정처 = Ted**(`t4g.medium` 승격 여부). ⛔ 이 레인의 IAM 으로는 인스턴스 타입을 **바꿀 수도 조회할 수도 없다**(`ec2:DescribeInstances` **UnauthorizedOperation**).
- 로그 `oom-investigation.txt` · `pre-deploy-snapshot.txt`.

---

## 7. ⑺ 판정 — 대장 갱신

| 항목 | 종전 | 이번 | 막는 것 |
|---|---|---|---|
| `BF-9` | `open` | ⭐ **`done`** | **없다** — ⓔ 가 dev 실물에서 섰다(`§5` ⓐ) |
| `BF-12` | `open` | `open` 무변 | ⛔ **막는 것이 바뀌었다** — s3 에서 회수 주체를 못 모은다(`§5` ⓑ) |
| `BF-11` | `open` | `open` 무변 | ⓑ 눈 확인(Ted) |
| `BF-8` | `open` | `open` 무변 | ⓒ 눈 확인(Ted) |
| `BF-7` | `open` | `open` 무변 | ⓓ 실브라우저 크롬(Ted) |
| **R-A `WU-A1`~`A14`** | `done` | **`done` 무변** | **없다** — **「dev 배포 green」 증거 줄만 더했다.** ⛔ 상태를 다시 열지 않았다 |

⛔ **「배포했으니 닫는다」로 세지 않았다.**

**좁은 문서 게이트 셋 — 최종 트리에서 green** (로그 `narrow-doc-gates.txt` · `NARROW_GATES_EXIT=0`)

| 게이트 | 실측 |
|---|---|
| `work-item-consistency` | **green** — 대장 140건 · 불일치 0 · conflict 0 · 결정 번호 324개 |
| `planning-freshness` | **green** — 임베드 **15/15** 원본 일치 |
| `work-item-selftest` | **green** — 17 케이스(대조군 1 · red 증명 16) |

⚠ **`COLAB_PLANNING_ROOT` 은 「패키지 폴더」까지다** — `40 COLAB-기획` 까지만 주면 `…/에픽` 을 찾다 **red(준비)** 가 난다(이 레인이 한 번 물렸다). 정확한 값 = `<작업공간>/40 COLAB-기획/00_기획원본/Co-Lab_ver2_1차마일스톤_목업패키지_260818_이태헌`.

⛔ **이 셋은 전수를 갈음하지 않는다.**

---

## 8. Ted 가 눈으로 볼 자리 — 그대로 열려 있다

진입 `https://d31zgpff2091oh.cloudfront.net/` · 계정 = `~/.config/colab-platform/dev-secrets/dev-logins.txt` · **열 데이터셋 14건**.

- **ⓑ `BF-11`** — 정본 토큰으로 바뀐 **색 5종**이 종전과 같은 그림인가.
- **ⓒ `BF-8`** — S-01 연구실 화면(진입 `/`)의 뿌리 여백 > 0 · 본문 1200px · 히어로 680px 불변.
- **ⓓ `BF-7`** — 데이터셋 상세의 **스크린샷 버튼**이 실브라우저 크롬에서 완주하는가 · 잔존 앵커 0.
- **㉢ 유료 전환** — 콘솔 표시값(이 레인 IAM 으로는 영영 못 잰다 · `〈350〉`).
- **`〈373〉` `t4g.medium` 승격** — 위 `§6` 이 근거다.

---

## 9. 다음 세션이 할 것 (순서대로)

1. ⛔ **전 게이트 전수 `-j 4` 를 한 번의 실행으로** — 그 전에 서비스 `.venv` 넷 ＋ `gates/.venv` ＋ `frontend/node_modules` 를 세우고 `COLAB_PLANNING_ROOT` 을 **패키지 폴더까지** 선언한다.
2. 전수 green 이면 **`main` fast-forward** ＋ `〈376〉` 로 전수 결과 등재.
3. `docker logs colab_v2_dev_viz_render 2>&1 | grep '회수'` 로 **주기 한 바퀴 로그**를 읽어 `BF-12` ⑶ 의 `[미측정]` 을 채운다(⚠ `§5` ⓑ ㉰ 가 구조적 원인이라 같은 줄이 나올 것이다 — 그러면 **그 사실을 적는다**).
4. Ted 판정 대기 셋 — `t4g.medium`(`〈373〉`) · s3 회수 주체(`〈372〉`) · `load-seed` op 확장(`〈374〉`).

---

## 10. 산출물 · 로그 경로

전부 `dev-package/reports/window-9/` 아래다(`.txt`).

| 파일 | 무엇 |
|---|---|
| `pre-deploy-snapshot.txt` | 배포 직전 원격 실측 ＋ API 계수(정본은 API) |
| `oom-investigation.txt` | ⛔ OOM 3건 실사 — cgroup ↔ 컨테이너 대조 · `RestartCount` |
| `build.txt` · `ship.txt` · `up.txt` | 세 스크립트 전문 · `EXIT=0` |
| `migration-heads.txt` | 두 체인 head ＋ 계수 ＋ R-A 신설 열 ＋ 두 CHECK 정의 ＋ 새 동의어 13행 |
| `repo-sync.txt` | `/opt/colab-repo` 동기화 ＋ md5 대조 |
| `deploy-web.txt` · `cloudfront-check.txt` | 웹 번들 ＋ 서빙 해시 대조 |
| `deploy-doctor.txt` | `deploy_doctor` 전문 · `✓ 14 · ✗ 0 · ─ 0` |
| `post-deploy-b-spool.txt` | ⓑ 스풀 실측 ＋ 회수 요약 줄 ＋ 자원 ＋ OOM 재확인 |
| `post-deploy-c-synonyms.txt` | ⓒ 동의어 실동작 |
| `post-deploy-e-sourcelabel.txt` | ⓐ·ⓔ 쓰기 ＋ 되읽기 ＋ 계보 ＋ 계수 무변 |
| `post-deploy-ra-smoke.txt` · `post-deploy-ra-installed-code.txt` | R-A 층별 연막 ＋ 설치본 확인 |
| `narrow-doc-gates.txt` | 좁은 문서 게이트 셋 green |
| `gates-all-w9-ABORTED.txt` ＋ `.NOTE.txt` | ⛔ **중단된 전수 — 판정이 아니다** |
| `venv-setup.txt` | 시험 환경 구성 |
| `lane-report.md` | 이 문서 |

⛔ **어느 파일에도 비밀값이 없다** — DB URL·토큰·비밀번호·액세스 키는 경로로만 부르고 값은 한 번도 출력하지 않았다. 운영자 키는 `--env-file` 로 잠깐 넘기고 **`shred -u`** 했다(잔여 0 확인).
