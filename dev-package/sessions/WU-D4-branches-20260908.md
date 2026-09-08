# WU-D4 · 브랜치 실측 표 (2026-09-08)

- 레인 `rd-branch-sweep` · 브랜치 `lane/wu-d4` · 기점 `integration/r-d` `785ed88`.
- 기준 `main` = `18c0228`(로컬 = `origin/main` 동일 실측).
- 이 레인이 한 것 = **측정 ＋ 로컬 `archive/*` 태그**. 삭제 0 · push 0 · 대장 0(spec 우려 11 · advisor ① 조건 ⑵).
- 「밖 커밋 수」 = `git rev-list --count main..<tip>` · 「밖 파일」 = `git diff --stat main...<tip>`(three-dot). two-dot 값은 브랜치별 상세에 병기.

## 1. 판정 대상 11건

| 브랜치 | 로컬/원격 | 로컬=원격 | 워크트리 | tip(sha·일자) | main 조상 | 밖 커밋 수 | merge-base | 밖 파일과 main 동등물 | 용도 | 권고 | archive 태그 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `integration/r-a2` | 둘 다 | 예 | 없음 | `ccd9372` · 2026-09-07 | 예 | 0 | `ccd9372`(＝tip) | 밖 파일 0 — 전량 `main` 안 | R-A′ 라운드 통합 브랜치(마감 완료) | 즉시 삭제(조상·병합 완료) | `archive/integration/r-a2` |
| `integration/r-b` | 둘 다 | 예 | 없음 | `9a4b257` · 2026-09-08 | 예 | 0 | `9a4b257`(＝tip) | 밖 파일 0 — 전량 `main` 안 | R-B 라운드 통합 브랜치(마감 완료) | 즉시 삭제(조상·병합 완료) | `archive/integration/r-b` |
| `plan/r-d-0908` | 둘 다 | 예 | `.claude/worktrees/r-d-plan` | `18c0228` · 2026-09-08 | 예 | 0 | `18c0228`(＝`main` tip) | 밖 파일 0 — `main` tip 과 동일 커밋 | R-D 계획 세션 발판 | R-D 병합 뒤 삭제(자기 발판) — **워크트리 제거 선행** | `archive/plan/r-d-0908` |
| `w9-rebase` | 로컬만 | 해당 없음(원격 동명 없음 · 같은 sha 가 `origin/integration/w9-dev-deploy-rebased`) | `.claude/worktrees/w9` | `97f1d99` · 2026-09-07 | 아니오 | 3 | `ccd9372` | 30파일 중 ai 체인 2파일 흡수 · 나머지 28 동등물 없음(§2) | 창 9 재번호본 | Ted 한 줄 뒤 삭제 — **워크트리 제거 선행** | `archive/w9-rebase` |
| `integration/w9-dev-deploy` | 둘 다 | 예 | 없음 | `13589fe` · 2026-09-06 | 아니오 | 2 | `b0671f8` | `w9-rebase` 와 같은 30파일 집합 · 판정 동일(§2) | 창 9 원본 통합 브랜치 | Ted 한 줄 뒤 삭제 | `archive/integration/w9-dev-deploy` |
| `integration/w9-dev-deploy-rebased` | 원격만 | 해당 없음 | 없음 | `97f1d99` · 2026-09-07 | 아니오 | 3 | `ccd9372` | `w9-rebase` 와 **동일 커밋**(sha 일치) | 창 9 재번호본 원격 사본 | Ted 한 줄 뒤 삭제 | `archive/integration/w9-dev-deploy-rebased` |
| `feature/rtf400_deploy_prod` | 원격만 | 해당 없음 | 없음 | `42a7154` · 2026-09-06 | 아니오 | 13 | `27733ba` | 39파일 · `infra/prod/**` 20파일은 `main` 에 **경로 자체가 없음**(§3) | prod 스택 구축(P1~P8 · 개통·복구 예행) | Ted 한 줄 뒤 삭제 — ⚠ 삭제 전 원격 태그 push 필수 | `archive/feature/rtf400_deploy_prod` |
| `feature/rtf400_dev_scale_up` | 원격만 | 해당 없음 | 없음 | `809f311` · 2026-09-06 | 아니오 | 1 | `f2b61cd` | 1파일(`docs/DEPLOY.md`) · 동등물 **없음**(§4) | dev EC2 `t4g.small`→`t4g.medium` 실측 기록 | Ted 한 줄 뒤 삭제 — ⚠ 실물과 `main` 문서가 갈린다(§4) | `archive/feature/rtf400_dev_scale_up` |
| `feature/rtf400_upload_reaper` | 원격만 | 해당 없음 | 없음 | `5c1458e` · 2026-09-06 | 아니오 | 1 | `f2b61cd` | 3파일(원장 3) · 동등물 **없음**(§5) | `U-2` 근거 정정 ＋ prod 고아 8건 실측 | Ted 한 줄 뒤 삭제 — ⚠ 정정이 `main` 에 없다(§5) | `archive/feature/rtf400_upload_reaper` |
| `urgent-upload-lineage-rev1` | 원격만 | 해당 없음 | 없음 | `ff8688b` · 2026-09-03 | 아니오 | 1 | `15fcda3` | 7파일(`deliverables/**`) · `main` 없음 · 기획 폴더에 동명 rev1 있으나 바이트 상이(§6) | 긴급 범위 rev1 전달본 사본 | Ted 한 줄 뒤 삭제 | `archive/urgent-upload-lineage-rev1` |
| `gh-pages` | 원격만 | 해당 없음 | 없음 | `8e8c5d2` · 2026-09-03 | 아니오 | 1 | **없음**(고아 브랜치 · `git merge-base` exit 1) | 4파일(`.nojekyll`·`index.html`·`urgent-upload-lineage-rev1/index.html`·`mockup.html`) · `main` 없음 | **가동 중인 GitHub Pages 배포 원천**(§7) | 보류(운영 중 사이트 원천 · 삭제 시 공개 URL 중단) | 없음 — 보류라 태그 미생성 |

### 판정 밖 4건 (각주)

| 브랜치 | 사유 |
|---|---|
| `main` `18c0228` | 기준선 |
| `integration/r-d` `785ed88` | 이 라운드의 가동 중 통합 브랜치 · 워크트리 `.claude/worktrees/r-d` |
| `lane/wu-d4` `785ed88` | 이 레인 자신 |
| `worktree-agent-a704543d0bb869e59` `18c0228` | 이 워크트리의 하네스 브랜치 |

- 고유 이름 실측 = 판정 대상 **11** ＋ 판정 밖 **4** = **15**. 라운드 파일 `R-D-1-branching.md §2` 의 「고유 이름 11」 = 판정 대상 기준이고 **일치**한다.
- 전 계수 = `git branch -a` **21행** · `git ls-remote --heads origin` **12건** · `git tag -l 'archive/*'` **10건**(측정 전 0).

## 2. 창 9 계열 3건 상세 (`w9-rebase` · `integration/w9-dev-deploy` · `origin/integration/w9-dev-deploy-rebased`)

- `w9-rebase` ＝ `origin/integration/w9-dev-deploy-rebased` **동일 커밋** `97f1d99`. 브랜치 이름만 둘.
- `w9-rebase` 밖 커밋 3 = `80aeb00`(창 9 개시) · `de1a5a2`(집행 원장) · `97f1d99`(재번호 〈368〉~〈376〉 → 〈373〉~〈381〉).
- `integration/w9-dev-deploy` 밖 커밋 2 = `20b3715`(개시) · `13589fe`(집행). 세 브랜치의 three-dot 파일 집합은 **30파일로 동일**.
- two-dot 값은 크게 다르다 — `main..w9-rebase` 517파일 · `main..integration/w9-dev-deploy` 830파일. merge-base 이후 `main` 이 바꾼 분량이 섞인 값이라 **동등물 판정에 쓰지 않았다**(three-dot 30파일이 판정 대상).

### ai 체인 = WU-C13 이 흡수 (spec 축자 확인)

- 흡수 커밋 = `5001b36`(「WU-C13 · ai 체인 흡수 — w9 `0006_topic_vocab_six` ＋ 주제 어휘 6값 선언」) · `30178dd`(`0007` 머지 리비전) · `83d3eb5`(대장·세션 노트).
- 실측 = `git diff --name-status main w9-rebase -- db/ai` 에서 `db/ai/seed/topic_synonym_six.sql` · `db/ai/versions/0006_topic_vocab_six.py` **미출력** ⟹ 두 파일은 `main` 과 **바이트 동일**.
- `db/ai/schema.sql` 은 상이하나 `main` 이 6값 CHECK 를 **이미 들고 있고**(`main:db/ai/schema.sql:90` `'가뭄', '파일 포맷 예제'`) WU-C7 `category` 5값을 더 얹은 상태 ⟹ **흡수 ＋ 추가**.
- `main` 에만 있는 것(브랜치에 없음) = `db/ai/versions/0006_rc7_synonym_category.py` · `0007_merge_topic_vocab_and_rc7_category.py` · `db/ai/tests/0006-assertions.sql`·`0006-drift.sh`·`0007-drift.sh`.

### 남은 것 — 파일별 동등물 판정

| 파일 | 브랜치 변경분 | `main` 동등물 | 근거 |
|---|---|---|---|
| `db/ai/schema.sql` | 주제 6값 CHECK ＋ 주석 | **있음(흡수)** | `main:db/ai/schema.sql:90` |
| `db/ai/seed/topic_synonym_six.sql` | 신규 | **있음(동일)** | `git diff --name-status main w9-rebase` 미출력 |
| `db/ai/versions/0006_topic_vocab_six.py` | 신규 | **있음(동일)** | 동상 |
| `infra/dev/compose.yml` | `events` 볼륨 ＋ `COLAB_WORKER_EVENT_SPOOL`·`COLAB_VIZ_TRIGGER_SPOOL` = `/srv/viz-events` ＋ `volume-init` chown | **없음** | `main:infra/dev/compose.yml` 에서 `COLAB_WORKER_EVENT_SPOOL`·`COLAB_VIZ_TRIGGER_SPOOL`·`viz-events` **0건** · `git log main -S'COLAB_VIZ_TRIGGER_SPOOL' -- infra/dev/compose.yml` **0건** |
| `infra/dev/README.md` | 위 짝의 규약 8줄 | **없음** | `main:infra/dev/README.md` 에서 `COLAB_WORKER_EVENT_SPOOL` **0건** |
| `infra/staging/manifest-refdata.json` | `sourceLabel` 4값 ＋ 규약 1줄 | **없음** | `main:infra/staging/manifest-refdata.json` 에서 `sourceLabel` **0건** |
| `dev-package/PLAN-SoT.md` | 8행 〈373〉~〈380〉 | **부분** — 〈374〉(ai 6값)는 WU-C13 이 흡수 · 〈375〉의 sha `20b3715d1db0` 는 `main` 〈378〉이 인용 · 나머지 6행 동등 기재 **없음** | `main:PLAN-SoT` 의 「트리거 스풀」 = 〈361〉(등록만·미해소) · 「계수 단위 불일치」 **0건** |
| `dev-package/WORK-UNITS.md` | `BF-9` ⬜ → ✅ | **없음** | `main:WORK-UNITS` = `BF-9 ⬜` |
| `dev-package/work-items.yaml` | 창 9 상태 갱신 82행 | **부분** — ai 체인분만 흡수 · `BF-9`·`BF-12`·OOM 갱신 없음 | 위 두 행과 같은 근거 |
| `dev-package/03-HANDOFF.md` | 창 9 작업지시 블록 44행 | **없음**(경위는 `main:dev-package/sessions/R-C-ROUND-20260908.md §9` 에 존재) | `git ls-tree main` 확인 |
| `dev-package/reports/window-9/*.txt`·`lane-report.md` **20파일** | 신규 | **없음** — `main:dev-package/reports/` 에 `window-9` 디렉터리 부재 | `git ls-tree --name-only main dev-package/reports/` |

- ⛔ **삭제 시 태그에만 남는 실체** = ⑴ dev 트리거 스풀 배선(compose ＋ README) ⑵ 매니페스트 `sourceLabel` 4값 ⑶ 창 9 원장 6행 ⑷ 창 9 실행 로그 20파일. spec 「남은 것 = dev 트리거 스풀 · 매니페스트 원천 표기 · 원장 사본 · 재번호」와 **일치**.
- ⚠ 재번호 충돌 — 브랜치의 〈373〉~〈381〉 은 `main` 이 이미 쓴 번호다(`main` 최대 = 378). 흡수를 택하면 재번호가 다시 필요하다.

## 3. `feature/rtf400_deploy_prod` 상세 (밖 커밋 13)

- 커밋 = `6d3faf4`(prod 개시·〈343〉) · `3977ce7` · `8246d1a` · `4e4b6d8`(prod S3) · `aa73b09`(셀프테스트 6) · `8eef52f`(EC2) · `f824d3d`(DB 부트스트랩) · `6ddde2a`(스택 기동) · `7860230`(프론트·백업 cron) · `ca112f2`(prod 개통 · doctor 14/14) · `294e7ca`(시점 복구 예행) · `0fcd153`(번호 개번 〈343〉→〈372〉) · `42a7154`(exec-bit 정정).
- three-dot 39파일 / two-dot 716파일.
- `main` 에 **경로가 없는 것** = `infra/prod/**` 20파일(`compose.yml` 199행 · `ec2-prep.sh` 123 · `backup.sh` 114 · `db-bootstrap.sh` 84 · `install-cron.sh` 59 · `deploy-doctor.sh` 53 · `build.sh` 46 · `up.sh` 40 · `ship.sh` 33 · `migrator/Dockerfile` · `cloudfront/` 2 · `iam/` 6 · `README.md`) ＋ `gates/tools/_fixture.sh`(65행) ＋ `gates/tools/_compose_list.py`(14행) — `git ls-tree --name-only main infra/` = `README.md`·`dev`·`staging` 뿐.
- `main` 에 있으나 내용 상이 = `docs/DEPLOY.md`(＋200행) · `infra/dev/ship.sh` · `infra/dev/backup.sh` · `infra/dev/install-cron.sh` · `services/core-api/ops/deploy_doctor.py` · `s3_doctor.py` · `gates/tools/*-selftest.sh` 6 · `db_boundary.py` — 각 파일의 브랜치 변경분이 `main` 에 반영됐는지는 파일 단위로 재지 않았다(`[미상]` · §8).
- 위상 = prod 는 `PLAN-SoT §9-㊻` 로 **보류**. 삭제하면 `archive/feature/rtf400_deploy_prod` 태그가 유일한 복원 출처가 되므로 **원격 태그 push 가 삭제의 선행 조건**이다.

## 4. `feature/rtf400_dev_scale_up` 상세 (밖 커밋 1)

- `809f311` — dev EC2 를 `t4g.small` → `t4g.medium` 으로 변경한 실측 기록. three-dot 1파일(`docs/DEPLOY.md` ＋23/−1) / two-dot 809파일.
- 브랜치 문면 = 인스턴스 유형 `t4g.medium` · OOM 4건이 전부 `CONSTRAINT_MEMCG`(viz-render cgroup 640 MiB) · `dev.env` 를 `CORE 512m · WORKER 768m · VIZ 1536m · AI 384m` 로 상향 · 이미지 정리 25→14개(742 MB 회수).
- `main` 동등물 = **없음**. `main:docs/DEPLOY.md:160` 은 `t4g.small` 이고 `CONSTRAINT_MEMCG` 0건 · `1536m` 0건 · `git log main -S'CONSTRAINT_MEMCG'` 0건.
- ⚠ **어느 검사에도 걸리지 않는다** — `docs/DEPLOY.md` 의 인스턴스 유형을 실물과 대조하는 게이트가 `ALL_GATES`(`gates/run.sh:153-172`) 에 없고, `deploy_doctor.py` 14항목에도 인스턴스 유형이 없다. 「main 과 동일」이 아니라 **검사 부재**다(§9 후속 ①).

## 5. `feature/rtf400_upload_reaper` 상세 (밖 커밋 1)

- `5c1458e` — `U-2` 근거 정정 ＋ prod 첫 고아 실측 〈368〉. three-dot 3파일(`PLAN-SoT.md` ＋1 · `WORK-UNITS.md` ±1 · `work-items.yaml` ±4) / two-dot 809파일.
- 브랜치 문면 요지 = `UploadLedgerAdapter.reap_expired`(`d5_ingestion.py:314`)가 **운영 코드에서 호출 0건**(호출처는 테스트 3곳뿐) · 밤 크론이 부르는 `_reap_expired`(`upload_transfers.py:142,247`)는 전송 어댑터라 완결 접수에 닿지 않음 ⟹ 미등록 접수의 행·바이트가 영구 잔존 · prod 고아 8건 3.00 MB(지우지 않음).
- `main` 동등물 = **없음**. `git log main -S'운영에서 호출 0건' -- dev-package/work-items.yaml` 0건 · `git log main -S'고아 8건'` 0건 · `main:work-items.yaml` 에 「prod 실측 (2026-09-06」 0건 · `main:PLAN-SoT.md` 에 「`U-2` 근거 정정」 0건.
- ⟹ `main` 의 `U-2` 근거는 여전히 「워커 만료가 DB 행만 지운다」이고, 브랜치는 그것을 「절반」이라고 정정한다. 삭제하면 정정이 태그에만 남는다(§9 후속 ②).

## 6. `urgent-upload-lineage-rev1` 상세 (밖 커밋 1)

- `ff8688b`(작성자 lth0610) — `deliverables/urgent-upload-lineage-rev1/` 7파일 9,454행 추가. three-dot 7파일 / two-dot 1,288파일.
- `main` 에 `deliverables/` **경로 부재**(`git ls-tree --name-only main`).
- 브랜치 README 축자 = 「이 폴더는 전달용 사본이다. 정본은 이 레포 밖 기획 작업공간에 있다」.
- 기획 작업공간 대조 = `40 COLAB-기획/10_적용전/업로드_계보_260826_rev1_이태헌.html` 존재(1,729,588 B) · 브랜치 `mockups/업로드_계보_260826_rev1.html` 은 1,518,188 B · `package/업로드_계보_260826_rev1.html` 은 1,722,826 B 로 **셋 다 md5 불일치** ⟹ 「같은 rev1 계열이나 바이트 동등물은 아니다」(`[미상]` — 어느 쪽이 최신인지 이 레인에서 판정하지 않음).
- 문서 3건(`PRD_`·`Policy_`·`Validation_업로드_계보.md`)은 기획 폴더의 E-04 `…업로드와_계보_확정.md` 와 **파일명·범위가 다른 별건** ⟹ 동등물 **없음**.

## 7. `gh-pages` 상세 — 용도 확정

- `gh api repos/CognileapAI/colab-v2/pages` 응답(읽기 전용) 축자 —
  `{"status":"built","cname":null,"build_type":"legacy","source":{"branch":"gh-pages","path":"/"},"public":true,"https_enforced":true,"html_url":"https://cognileapai.github.io/colab-v2/"}`
- ⟹ **가동 중인 GitHub Pages 배포 원천이 맞다.** 삭제하면 공개 URL 이 즉시 끊긴다.
- 고아 브랜치(커밋 1개 · `main` 과 merge-base 없음) · 트리 4파일 · `index.html` 에 `<meta name="robots" content="noindex">`.
- 권고 = **보류**. spec 우려 8 의 「`gh-pages` 는 용도 확인 전 무접촉」에서 확인이 끝났고, 확인 결과가 **가동 중**이므로 삭제 대상이 아니다. 처분하려면 Pages 설정 해제가 선행이고 그것은 이 라운드 범위 밖이다.
- 태그 미생성(보류 항목).

## 8. 셀 수 없었던 것

1. `feature/rtf400_deploy_prod` 의 「`main` 에 있으나 상이」 17파일 각각에 대해 브랜치 변경분이 `main` 에 반영됐는지 — 파일 단위 내용 대조 미수행(`[미상]`). 39파일 중 22파일(`infra/prod/**` 20 ＋ `gates/tools/_fixture.sh` ＋ `_compose_list.py`)만 「경로 부재 = 동등물 없음」으로 확정.
2. `urgent-upload-lineage-rev1` 의 HTML 3벌 중 어느 것이 최신인지 — 바이트 상이만 확인, 내용 비교 미수행.
3. 창 9 브랜치의 `dev-package/03-HANDOFF.md` 44행 중 `main:dev-package/sessions/R-C-ROUND-20260908.md §9` 가 실제로 몇 항목을 재수록하는지 — 파일 존재만 확인, 항목 대조 미수행.
4. dev EC2 실물이 지금 어느 `compose.yml` 로 돌고 있는지 — 원격 접촉은 이 레인 범위 밖. 「compose 스풀 배선이 실물에 살아 있는가」는 `[미상]`.
5. `feature/rtf400_*` 3건의 작성자 — `%an` 이 전부 `rtf400`(계정 표기)이고 실인물 대응은 레포에서 확인 불가.

## 9. 후속 항목 (이 레인이 고치지 않는다)

1. **`docs/DEPLOY.md` 의 dev 인스턴스 유형이 실물과 갈릴 수 있는데 어느 검사도 잡지 않는다** — 게이트 `ALL_GATES` 에 항목 없음 · `deploy_doctor.py` 14항목에 없음 · Dockerfile·배포 스크립트에도 없음. §4 근거.
2. **`U-2` 근거 정정(정리기 호출 0건)이 `main` 에 없다** — 원장 정정이 브랜치에만 있고, `work-item-consistency` 는 `main` 안의 대장↔산문만 보므로 브랜치의 정정을 잡지 않는다. §5 근거.
3. **dev 트리거 스풀 배선이 `main:infra/dev/compose.yml` 에 없다** — 「`main` 유일 배포 원천」(규칙 1)과 직접 관계된다. compose 를 검사하는 게이트가 `ALL_GATES` 에 없고 `deploy_doctor.py` 에도 스풀 항목이 없다(`SPOOL`·`viz-events`·`EVENT` 검색 0건). §2 근거.

## 10. 집행 명령 (오케스트레이터 · 게이트 ③ 뒤)

⛔ 이 레인은 아래를 **실행하지 않았다.** `git push origin --tags` 는 금지(잡태그 유출) — 태그는 개별 push.

### ㉮ 즉시 (조상·병합 완료 — Ted 한 줄 불요)

```
git push origin archive/integration/r-a2
git push origin archive/integration/r-b
git branch -d integration/r-a2
git branch -d integration/r-b
git push origin --delete integration/r-a2
git push origin --delete integration/r-b
```

### ㉯ Ted 한 줄 뒤 (창 9 계열 3 ＋ 원격 4)

```
git push origin archive/w9-rebase
git push origin archive/integration/w9-dev-deploy
git push origin archive/integration/w9-dev-deploy-rebased
git push origin archive/feature/rtf400_deploy_prod
git push origin archive/feature/rtf400_dev_scale_up
git push origin archive/feature/rtf400_upload_reaper
git push origin archive/urgent-upload-lineage-rev1

git worktree remove .claude/worktrees/w9
git branch -d w9-rebase
git branch -d integration/w9-dev-deploy
git push origin --delete integration/w9-dev-deploy
git push origin --delete integration/w9-dev-deploy-rebased
git push origin --delete feature/rtf400_deploy_prod
git push origin --delete feature/rtf400_dev_scale_up
git push origin --delete feature/rtf400_upload_reaper
git push origin --delete urgent-upload-lineage-rev1
```

- `git branch -d w9-rebase` 와 `git branch -d integration/w9-dev-deploy` 는 미병합이라 `-d` 가 거절한다. **거절이 정상**이고, 태그 push 성공을 확인한 뒤에만 `-D` 로 바꾼다 — 태그 push 가 green 이 아니면 실행하지 않는다.

### ㉰ R-D 가 `main` 에 ff 된 뒤

```
git push origin archive/plan/r-d-0908
git worktree remove .claude/worktrees/r-d-plan
git branch -d plan/r-d-0908
git push origin --delete plan/r-d-0908
git worktree prune
```

### ㉱ 처분하지 않는 것

- `gh-pages` — 가동 중 Pages 원천(§7). 태그도 만들지 않았다.
- `main` · `integration/r-d` · `lane/wu-d4` · `worktree-agent-a704543d0bb869e59` — 판정 밖.
