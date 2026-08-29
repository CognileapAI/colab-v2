# Stage 2 완주 로드맵

- 시점 = 2026-08-29 · `main` = `d05171b` · 작업트리 clean · `origin/main` 과 동기
- 정본 = `dev-package/work-items.yaml`(95건 · `stage: stage2` 34건)
- 근거 문서 = `sessions/STAGE2-REMAINING.md` · `sessions/STAGE2-READINESS-AUDIT.md` · `sessions/STAGE2-READY.md` · `sessions/X5-DECISION-BRIEF.md` · `RESTART.md`
- 실측 = 게이트 전 종 1회 완주(`./gates/run.sh all -j 6`) · `docker ps` · `crontab -l` · 릴리스 원장 · 대장 파싱
- 판정 용어 — **착수 가능**(선행 실물 성립 · 완료 정의 있음 · 판정 대기 없음) / **차단**(선행 미완 · 판정 대기 · 측정 대기 중 하나 이상) / **판정 대기**(코드 아님 · 사람이 고를 자리)

---

## 1. 잔여 항목 표

- 34건 중 `done` 9 · 잔여 25 (`open` 19 · `partial` 2 · `in_progress` 2 · `conflict` 1 · `deferred` 1)
- 대장 실측 계수와 산문 계수 일치 — 편도 누락·과잉 0건

| ID | 항목 | 대장 상태 | 판정 | 막는 것 | 종류 |
|---|---|---|---|---|---|
| `PV-1` | 미리보기 뒷단 — 헤더 파싱·좌표계 통일·지도용 영상 변환 | open | **착수 가능** | 없음 (선행 `D5` 인제스트 stage 1 파트 실물 완료) | — |
| `F-1` | S-08 미등록 미리보기 화면 | in_progress | **착수 가능(조건부)** | 완료 정의 ⑵ ↔ `PreviewControls.tsx:33-48` 정면 충돌 | 판정 대기 |
| `K3` | 계보 제안 서비스 | open | **착수 가능(조건부)** | 완료 정의에 합격선 수치 없음 = 닫기 오라클 미정의 | 판정 대기 |
| `X-6` | 별칭 재부착 실패 삼킴 | open | **코드 끝남 · 상태 판정만** | 대장 `status: open` · `evidence: null` 갱신 | 판정 대기 |
| `F-2` | 카탈로그 키워드 입력 제거 | open | 차단 | 걷어낼 입력 실물 0건 · 잔여는 문구 정합 하나이고 답이 `T-1` 에 달림 | 선행(`T-1`) |
| `I3` | 배포 자동화 | partial | 차단(부분 진행) | 15행 중 6행 열림/부분 — ⑴⑷⑸⑽ 열림 · ⑵-b ⑾ 부분 | 코드 ＋ 측정 |
| `I4` | 운영 준비 (추적·알람·복구 리허설) | open | 차단 | `I3` 미완 · `R-1` 과의 중복 범위 미기재 | 선행 |
| `R-1` | 복원 절차 | conflict | 차단 | 산문 3문서가 서로 다른 상태 · 잔여 셋 미실측 | 판정 대기 |
| `T-1` | `ts_config` 한국어 재작성 | open | 차단 | 잔여가 평가셋 실패 8건 재측정뿐인지 미판정 | 측정 ＋ 판정 |
| `V-1` | 팔레트 선택 재렌더 | open | 차단 | `P3` 미착수 · **완료 정의 없음** | 선행 ＋ 정의 부재 |
| `V-2` | 값 조회 (지도 점 클릭) | open | 차단 | `P3` 미착수 · **완료 정의 없음** | 선행 ＋ 정의 부재 |
| `P3` | 계보 그래프·2D 시각화 3종·`createScreenshot`·렌더 표현 확장 | open | 차단 | `PV-1`(COG) 없이는 타일 산출 불가 — 엄격 직렬 | 선행 |
| `Y-1` | 자동 무효화 | open | 차단 | `P3` · `PV-1` 미착수 | 선행 |
| `P6` | 승인 처리 | open | 차단 | `P3` · `P4` · `P5` 미완 | 선행 |
| `P7` | 연구실 대시보드 | open | 차단 | `P6` 미완 | 선행 |
| `P8` | E-01 적용 지점 표 | open | 차단 | `P7` 미완 | 선행 |
| `K5` | 제안 원장 | open | 차단 | `K3` 미착수 | 선행 |
| `PA-G` | 구글 IdP 어댑터 | open | 차단 | 「v2 기존 기능 전부 완성」 조건 미충족 | 선행(전건) |
| `S3` | 실데이터 4종 E2E | open | 차단 | `S2` 갈라짐 · `P3` 미착수 | 선행 ＋ 판정 |
| `S3-e2e-4종` | 위 항목의 무식별자 중복 계상 줄 | open | 차단 | `S3` 과 동일 대상 — 별건 아님 | 선행 |
| `#22` | D2·D8 고아 행 삭제 | open | 차단 | `R-1` 갈라짐 · 삭제 대상 id 목록 미고정 | 판정 대기 |
| `전범위백업` | 전범위 백업 (platform ＋ ai ＋ 볼륨) | partial | 차단 | **완료 정의 없음** · 크론 회차 누적 미확인 | 정의 부재 ＋ 측정 |
| `J-1` | 편의 기능 묶음 9건 | open | 차단 | Stage 2 마지막으로 못 박음 · **완료 정의 없음** | 선행(순서) |
| `W-1` | 항목 상태 대장·검사기 | in_progress | 차단 | `work-item-consistency` red 3건(`S2b`·`R-1`·`S2`) | 코드 아님 — 실측 판정 |
| `2단-격자전용-실패3건-처분` | 실패로 굳은 격자 전용 업로드 3건 처분 | deferred | 하지 않기로 함 | — | — |

- 단계 미배정 `unknown` 5건 = `R1`(done) · `IS4`(partial) · `G1b`(open) · `P4`(open) · `LV-4`(open)
  - 위 34건 계수 밖 — `P4` 는 `P6` 의 선행이므로 **Stage 2 완주의 실질 경로에 들어간다**
  - 계수와 경로가 갈리는 자리 = 단계 배정 판정이 필요한 자리

---

## 2. 선행·후행 의존 순서

- 사슬 A (시각화) — `PV-1` → `P3` → `V-1` · `V-2` · `Y-1` · `S3`(＋`S2` 판정)
- 사슬 B (화면·승인) — `P3` ＋ `P4` ＋ `P5` → `P6` → `P7` → `P8`
- 사슬 C (배포·운영) — `I3` → `I4` · `R-1`(판정) → `#22` · `전범위백업`
- 사슬 D (검색) — `T-1` → `F-2` · `K3` 완료 판정 · `S2b` 판정
- 사슬 E (계보 제안) — `K3` → `K5`
- 전건 후행 — `PA-G` 는 「v2 기존 기능 전부 완성」 조건 · `J-1` 은 Stage 2 마지막
- 횡단 — `W-1` 은 전 항목의 상태를 적으므로 **회차 끝에 한 번만**
- 완료 판정 자체를 잠그는 축 — `I3` ⑽ 게이트 전 종 green. `CLAUDE.md §4` 적용 시 ⑽ 이 red 인 동안 **어떤 Stage 2 항목도 완료 판정을 못 받는다**
- 병렬 최대 묶음 = 4 — ①배포·게이트 면(`infra/**`·`gates/**`) ②미리보기 뒷단 면(`services/pipeline-worker/**`·`contracts/storage/layout.json`) ③화면 면(`frontend/**`) ④계보 제안 면(`services/ai-service/**`·`services/core-api/**`)
- 파일 면 충돌 실측 — `F-1` ↔ `F-2` 겹치는 파일 0건. `F-2` 를 막는 것은 파일 면이 아니라 `T-1`

---

## 3. 착수 가능 항목

| 순위 | ID | 실작업 | 선결 |
|---|---|---|---|
| 1 | `PV-1` | ⑴ `services/pipeline-worker/src/colab_pipeline/app/worker.py:147` `stage1=True` 하드코딩 해제(`d5_ingestion.py:218` `if stage1:` 이 감지 직후 `ready` 로 빠진다) ⑵ autometa 소비자 신설 — `crs`·`grid` 를 채우는 코드가 `core-api` 에 0건(`d3_catalog.py:492-496` 은 `format`·`bundle_file_name`·`total_size_bytes` 만) ⑶ `layout.json` 슬롯 **재사용 판정** | 계약 개정과 구현을 같은 회차에 |
| 2 | `F-1` | 완료 정의 ⑵(`work-items.yaml:785` 「구간 조절 없음」) ↔ `PreviewControls.tsx:33-48`(구간 수 select 3~9 · 기본 6) 충돌 판정 후 한쪽 정렬 | Ted 판정 ①(§6) |
| 3 | `K3` | 선행 3건(`K2` 시드 · `core-ai.yaml:64-90` `suggestLineage` 선언 · 업로드 모달) 전부 실물 완료. 구현 착수 가능 · 닫기만 오라클 대기 | Ted 판정 ②(§6) |
| — | `X-6` | 코드 무변경. 대장 `status`·`evidence` 갱신만 | 상태 판정 |

- 착수 전 환경 선결 3건 (전부 환경·문서 · 코드 아님)
  - ⓐ 시험 env 4종 — `COLAB_CORE_TEST_SUBJECTS_FILE` · `COLAB_REFERENCE_DATA` · `COLAB_PIPELINE_DB_URL` · `COLAB_AI_TEST_DICT_DB_URL`. `RESTART §2-④` 에 표로 등재됨(2026-08-29 추가 확인). 마지막 하나는 여전히 `[미확인]`
  - ⓑ `services/ai-service/.venv` 부재 — **실측 확인**(`.venv` 보유 = core-api · pipeline-worker · viz-render 3종뿐)
  - ⓒ `db/ai` 체인 일회용 DB 부트스트랩 부재 — **실측 확인**(`services/ai-service/tests/fixtures/` 디렉터리 자체 없음. `tests/` 아래는 `conftest.py` ＋ 테스트 11개)

---

## 4. 차단 항목과 차단 원인

| ID | 차단 원인 | 여는 조건 |
|---|---|---|
| `I3` | ⑴ 배포 자동 트리거 미설치 · ⑷⑸ 롤백 대상 0건 · ⑽ 게이트 전 종 green 미달 | 아래 실측 3건 |
| `I4` | `I3` 미완 ＋ 복원 리허설이 `R-1` 을 흡수하는지 미기재 | `I3` 종결 · 완료 정의 1:1 대조 |
| `R-1` | `03-HANDOFF §1 T-X`(🟧＋⛔ 혼용) · `WORK-UNITS §10.2`(⛔) · `§10.3`(진행) 3자 갈라짐. 잔여 넷 중 첫째(크론 첫 회차 로그)는 2026-08-29 03:30 GREEN 으로 닫힘, 남은 셋(`POST /searches` 1회 · `preflight` 성질 판정 · `:i2` 태그 이력) 미실측 | 남은 셋 실측 후 사람이 하나로 확정 |
| `T-1` | 검색 평가셋 A층 재측정 미실행(기준선 = 충족 7 · 미충족 8 · 보류 1) | 평가셋 1회 완주 |
| `F-2` | `DatasetsPage.tsx:60`(「홈의 AI 검색」) ↔ `SearchHero.tsx:34-37`(「적혀 있는 낱말 그대로」) 정반대 문구, 답이 `T-1` 에 종속 | `T-1` 종결 |
| `P3` | `PV-1`(COG) 산출물 없이 타일 불가 | `PV-1` 종결 |
| `V-1`·`V-2`·`Y-1` | `P3` 미착수 ＋ `V-1`·`V-2` 는 완료 정의 자체가 없음 | `P3` 종결 ＋ 완료 정의 작성 |
| `P6`·`P7`·`P8` | 직렬 사슬 · `P4` 는 단계 미배정 | 사슬 B 순차 |
| `K5` | `K3` 미착수 | `K3` 종결 |
| `PA-G` | 「v2 기존 기능 전부 완성」 조건 미충족 | Stage 2 사실상 전건 종결 |
| `S3`·`S3-e2e-4종` | `S2` 갈라짐(계수만 `〈184〉` 로 해소, 계수 외 잔여 유무 미판정) ＋ `P3` 미착수 | `S2` 실물 계수 확정 ＋ `P3` |
| `#22` | `R-1` 갈라짐 ＋ 삭제 대상 id 목록 미고정 | `R-1` 확정 ＋ 목록 확정 |
| `전범위백업` | 완료 정의 부재 ＋ 크론 누적 회차 미확인 | 완료 정의 작성 ＋ 로그 대조 |
| `J-1` | Stage 2 마지막 배치 · 완료 정의 부재 | 순서 도달 |
| `W-1` | `work-item-consistency` red 3건 | `S2b`·`S2` 는 staging 실물 계수, `R-1` 은 잔여 셋 실측 |

---

## 5. 게이트 실측 결과

- 실행 = `./gates/run.sh all -j 6` (2026-08-29 · 전 종 완주 · 우회 0)
- 결과 = **27종 중 green 25 · red 2**

| 게이트 | 실측 | 비고 |
|---|---|---|
| `schema-diff` | **red** | `COLAB_APPLIED_DB_URL_PLATFORM` · `_AI` 미지정. 설계상 「DB 없으면 red」(green-by-skip 금지) — 환경 게이트이지 드리프트 아님 |
| `work-item-consistency` | **red** | 불일치 3건 = ㈓ `S2b` · ㈓ `R-1` · ㈓ `S2` (전부 `conflict` 잔존). 부수 출력 — 검사 대상 밖 9건 · 항목표 아님 1건 |
| 나머지 25종 | green | `planning-freshness` · `contract-lint` · `contract-breaking` · `event-lint` · `event-breaking` · `seam-consistency` · `generated-up-to-date` · `import-boundary` · `banned-import` · `ai-no-lineage-write` · `db-boundary` · `migration-single-head` · `rls-coverage` · `rls-effect` · `stage2-markers` ＋ selftest 10종 |

- selftest 10종 전건 green — 게이트가 red 를 낼 수 있음이 증명됨(무력화 아님)
- 환경 실측
  - staging 컨테이너 **8/8 healthy** (앱 5종 `Up 10 hours` · nginx·pg `Up 30 hours`)
  - 릴리스 원장 3행 = `approve` 1 · `deploy` red 1(`0a3ea797dbb1`) · `deploy` green 1(`30b3e0a7b3f3`)
  - crontab — 백업 블록만 존재(`30 3 * * *` `backup-full.sh` · `10 4 * * 1` `latest-check.sh`). **배포 스케줄 블록 없음**
- 문서 ↔ 실측 차이

| 문서 서술 | 실측 | 판정 |
|---|---|---|
| `STAGE2-READINESS-AUDIT §2` — 「게이트 27종 중 26종 green」 | green 25 · red 2 | `schema-diff` 를 계수에서 뺀 표기. 적용 DB URL 을 주지 않은 조건에서는 red 가 정상 결과 |
| `STAGE2-REMAINING` — 대장 검사기 red 1건 | red **3건**(`S2b`·`R-1`·`S2`) | 감사의 정정이 실측과 일치 |
| `STAGE2-READINESS-AUDIT §5-4` — 롤백 대상 0건 | 원장 green `deploy` 1행 확인 | 일치 |
| `STAGE2-READINESS-AUDIT §5-5` — 배포 자동 트리거 미설치 | crontab 에 백업 블록만 | 일치 |
| `STAGE2-READINESS-AUDIT §5-2` — `ai-service/.venv` 부재 | 부재 확인 | 일치 |
| `STAGE2-READINESS-AUDIT §5-3` — ai 체인 부트스트랩 부재 | `tests/fixtures/` 디렉터리 자체 부재 | 일치 |
| `STAGE2-READINESS-AUDIT §5-1` — 시험 env 4종 미문서화 | `RESTART §2-④` 에 표로 등재됨 | **해소됨** (`COLAB_AI_TEST_DICT_DB_URL` 값 출처만 `[미확인]` 잔존) |
| `RESTART §2` — 현재 서빙 태그 `30b3e0a7b3f3` | `docker ps` 및 원장 최종 green 행과 일치 | 일치 |

- 미측정 — 서비스 시험 전량(core-api 471 · pipeline-worker 160 · viz-render 119 · frontend 277)은 이번 회차에서 돌리지 않음. env 4종 주입이 선결이고, 주입 없이 돌리면 fail 로 떨어지는 의도적 설계

---

## 6. Ted 판단 필요 항목

| # | 판정 대상 | 종류 | 열리는 것 |
|---|---|---|---|
| ① | `F-1` 구간 조절 select — 코드를 걷을지 완료 정의를 고칠지 | 제품 판정 | `F-1` 닫기 |
| ② | `K3` 완료 정의의 합격선 수치 — 어디에도 없음 | 제품 판정 | `K3` 닫기 오라클 |
| ③ | `R-1` 상태를 하나로 확정 (3문서 갈라짐 · 잔여 셋 실측 후) | 실측 판정 | `I4` · `#22` · `전범위백업` · `W-1` |
| ④ | `S2` 계수 외 잔여 유무 · `S2b` 평가셋 재판정 | 실측 판정 | `W-1` red 해소 · `S3` |
| ⑤ | 삭제할 고아 행 id 목록 확정 | 판정 | `#22` |
| ⑥ | `V-1` · `V-2` · `J-1` · `전범위백업` 완료 정의 신규 작성 | 정의 판정 | 해당 4건의 닫기 기준 |
| ⑦ | `unknown` 5건(`R1`·`IS4`·`G1b`·`P4`·`LV-4`) 단계 배정 — 특히 `P4` 는 `P6` 의 선행 | 범위 판정 | 사슬 B 착수 순서 |
| ⑧ | `PV-1` 순서표 자리(몇 단인지) · 미리보기 산출물 수신 창구의 형태 · `layout.json` 렌더 슬롯 재사용 여부 | 설계 판정 | `PV-1` 집행 세부 |
| ⑨ | `I4` 복원 리허설이 `R-1` 을 흡수하는지 (완료 정의 12행 1:1 대조) | 범위 판정 | `I4` 범위 확정 |
| ⑩ | `X-5` 잔여 갈래 — 생산자 0 인 `422` 선언 2건(`core-viz.yaml:98` · `core-ai.yaml:142`) 철회 여부. 파괴적 변경이라 ㉯ 등급 = Ted 승인 필수 · 목적 단위 한 건이므로 쪼개지 않는다 | 계약 판정 | 계약 정합 |

- 판정 없이 진행 가능한 것 — `PV-1` ⑴⑵ 구현 · 환경 선결 ⓐⓑⓒ · `X-6` 대장 갱신
- 판정 대기가 종결을 잠그는 구조 — `I3` ⑽ 이 red 인 동안 완료 판정 자체가 서지 않으므로, ③④ 는 코드 작업보다 앞선다
