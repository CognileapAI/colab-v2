# R-DATA-CANON — 자료 설명 정본화와 dev 반복 재생성

입력 intent: `dev-package/intent/2026-09-14-data-canon-and-reseed.md` · 확정 2026-09-14(Ted 판정 8 ＋ advisor 파생 4 ＋ 정본 md 열린 질문 14 · §2).
대장 항목: `DR-4`(`dev-package/work-items.yaml` · `in_progress` · 이슈 #40 #44 #48 #49 #50 포섭 · 관련 #41 #42).
기점: `integration/r-data-canon` tip `3fc6ea01`(WU-C0 스폰 시 실측). 레인은 이 브랜치를 기점으로 삼는다.
이 파일은 부트스트랩에서 읽는 유일한 문서다(`CLAUDE.md §1`). 다른 문서는 상대경로 ＋ 앵커 문자열로만 따라간다.
결정 번호 〈N〉 은 병합 시 오케스트레이터가 기입한다(`dev-package/prd/tools/max-decision.sh` · 하드코딩 금지).

## 1. 회차 목적

- 참조자료 유형 폴더 4곳에 사람이 확정한 설명 정본 `DATASETS.md` 를 세우고, 등재표·계획 파일은 그 정본에서 생성되는 파생물로 바꾼다.
- 화면 결함 2건(분석 실패 시 등록 잠금 · 가공 단계 기본값 `Lv2`)을 정본대로 고친다.
- 「데이터 전체 초기화하고 다시 셋팅해줘」 한 마디가 명령 한 줄(`reseed.sh` · 10단계 · `--from` 재개)로 끝까지 가게 한다.
- dev 를 무인 재생성 1회로 정본과 일치시킨다 — 데이터셋 28 · 프로젝트 4 · 계보 간선 18 · 「미지정」 0 · 미리보기 판정 표 1건.

## 2. 확정 결정 요약 (intent 「판정 결과」 절에 근거 · 재개봉 금지 `.claude/rules/colab-rules.md §8`)

Ted 판정(2026-09-14)
1. ㈎ ⓐ 정본 md 자리 = 참조자료 폴더 안(`01.level-data/01.precipitation/DATASETS.md` · `01.level-data/02.vegetation/DATASETS.md` · `01.level-data/03.drought/DATASETS.md` · `02.File-format/DATASETS.md` · 참조자료 뿌리 기준). 기존 파일 무수정 · 추가만. 레포 사본 = `dev-package/reports/reference-data/datasets-md/` 같은 트리(정본은 폴더 · 레포는 반영본).
2. ㈏ ⓐ 분석 실패라도 등록 허용. 활성 조건 「ready 또는 failure」. 문면 「지도로 못 그려요 · 등록은 됩니다」. GeoPackage 판독은 `FMT-GPKG` 별도.
3. ㈐ 가공 단계 = 빈 칸 시작 ＋ 계보 규칙 자동 갱신 ＋ 규약 제약만. Ted 축자 「빈칸으로 시작하되, 다른 데이터를 계보로 연결하면 그 계보 규칙에 따라 바뀌어야 한다(제약필요, 자동으로 변경되어도된다) 그리고 이 계보 규약에 따라서만 제한을 받고 레벨은 맘대로 선택해도되게 하라.」 기록값 ⑴~⑸ 는 intent 「판정 결과」 ㈐. 제품 값 집합 `Lv0`~`Lv3` 무변.
4. ㈑ ⓑ 기존 26건은 개별 수정(PATCH) 없이 재생성으로 닫는다.
5. ㈒ ⓑ dev 한정 상시 승인 — `.claude/rules/deploy.md` 개정 선행(WU-C0 에서 집행). staging·prod 매회 GO 유지.
6. ㈓ ⓒ `dev-package/tools/dev-reseed/reseed.sh` 본체 ＋ 스킬 `/dev-reseed` 껍데기.
7. ㈔ ⓐ 개발 기계 실행. preflight = QEMU/binfmt 등록 · AWS 자격 환경변수 사슬 · 타 세션 컨테이너 잔존 · 참조자료 드라이브 · `agent-browser doctor` · dev 실행 sha == origin/main tip.
8. ㈕ ⓐ 미리보기는 판정 표만(28건 각각 · 성립/미성립 이름). 뒷단은 `PV-2`(#42).

advisor 파생 확정
9. 재생성 흐름 10단계 = `preflight → deploy → reset → bootstrap → up+doctor → s3 → prelude → seed(browser) → verify → report`(`dev-package/sessions/DR-2-runbook.md` 머리 「배포 → 초기화」 순서와 일치).
10. 정본 md 안 fenced `yaml` 기계 블록 — `build_plan.py` 는 그 블록만 읽고 표와 대조해 어긋나면 비영 종료.
11. 러너 `runner.py` 수정은 WU-C1b 로 분리.
12. prelude = 운영 SQL 선행 4단계(`DR-2-runbook.md §5`) 포함 · 운영자 계정은 seed 단계가 계정 관리 화면으로 재생성(비밀값 0600 파일).

정본 md 열린 질문 14건(md 반영은 WU-C1)
13. 가뭄 ㈎ = ㈏ 로 닫힘 · ㈏ = md 생성으로 교체 · ㈐ = `Lv1` ＋ 「L1 Calibrated」 설명 칸.
14. 포맷 ㈎ = ㈕ · ㈏ = 초안 문장 확정 · 출처 「코드 주석」 · 어긋난 주석은 비고 · 생산자 문서 요청은 비차단 후속 · ㈐ = `00.Data`→`Lv0` · `02.Results`→`Lv1` · ㈑ = 14/7 유지.
15. 강수 ㈎ = 이름 대응 확정 · ㈏ = 설명 칸 명시 · ㈐ ＝ 식생 ㈑ = 전건 판정 대상.
16. 식생 ㈎ = 실물 기준 부모 없음 · 문서 차이 비고 · ㈏ = 격자 부착 없음 · ㈐ = `Lv1` ＋ 「보조 입력」 설명 칸.

## 3. 진입조건

| # | 조건 | 닫는 법 |
|---|---|---|
| ㄱ | `integration/r-data-canon` 이 `main` tip 기점이고 WU-C0 커밋이 그 위에 있다 | 오케스트레이터(§8) |
| ㄴ | 참조자료 드라이브가 붙어 있고 `COLAB_REF_ROOT` 가 그 뿌리를 가리킨다(WU-C1·C4) | 사람이 연결 · 레인 지시문에 값 명시 |
| ㄷ | `frontend` 워크트리에 `npm ci` 완료(WU-C2a·C2b) | 훅 `worktree-setup.sh` · 미비 시 레인이 실행 |
| ㄹ | WU-C4 만 — C1·C1b·C2a·C2b·C3 가 `main` 에 병합되고 그 sha 가 dev 에 배포됨 · `deploy_doctor` 15/15 | 오케스트레이터 배포 뒤 preflight 가 `MAIN_SHA` 대조 |
| ㅁ | WU-C4 만 — `.claude/rules/deploy.md` 상시 승인 개정이 `main` 에 있다 | WU-C0 병합 |

## 4. 실측 근거 (레인이 다시 재지 않는다 · advisor 2026-09-14)

- `frontend/src/components/upload/UploadModal.tsx` — 「다음 →」 활성 조건에 `!status?.ready` 가 잔존(`disabled={gridReuseBusy || !uploadId || !status?.ready || Boolean(status?.failure) || …}`). 워커 실패 경로가 `ready=False` 를 쓰므로(`services/pipeline-worker/src/colab_pipeline/domains/d5_ingestion.py` 「ready=False, failed_at」) `failure` 항 제거만으로는 열리지 않는다 — 조건을 「ready 또는 failure」로 바꿔야 한다.
- `frontend/src/components/lineage/ParentPicker.tsx` — 자기 Lv 를 넘는 부모는 `disabled={over}`. 손대기 전(`selfLv=null`)에는 이 규칙을 적용하지 않는다(㈐ ⑵).
- `frontend/src/components/upload/RegisterArea.tsx` — 주석 축자 「⚠ 빈 선택지가 없다 — 기본값 `Lv2` 가 늘 서 있어 「비어 있음」이 성립하지 않는다」 · 「셋 다 **필수**이고 셋 다 **기본 선택값**이 있다」. 빈 선택지 신설 자리.
- 서버 부모 Lv 거절은 사람 값이 있을 때만 — `services/core-api/src/colab_core/app/routes/catalog.py` `parent_level_violations(db, *, self_level: int | None, …)`. 빈 칸(`None`) 등록은 서버 변경 0 으로 성립한다.
- `dev-package/tools/dev-seed/build_plan.py` — `DEFAULT_REF_ROOT = REPO_ROOT.parent / "03 Reference-Data"` 는 워크트리(`.claude/worktrees/agent-*`)에서 어긋난다 ⟹ 레인은 `COLAB_REF_ROOT` 를 필수로 받는다.
- 배경 서브에이전트는 레포 밖 쓰기가 막힌다 ⟹ 참조자료 폴더에 `DATASETS.md` 를 놓는 것은 오케스트레이터가 `cp` 로 한다. 레인은 레포 사본(`dev-package/reports/reference-data/datasets-md/`)까지가 끝이다.
- `frontend/test/` — `reg-level` 참조 7파일 · `Lv2` 참조 22파일(합집합 22 · 2026-09-14 실측). WU-C2b 가 기본값 전제 시험을 판정값에 맞춰 고친다(검사 범위 축소 0).
- `.claude/rules/deploy.md` 의 `paths:` 에 `dev-package/tools/dev-reseed/**` 가 없었다 ⟹ WU-C0 에서 추가(WU-C3 레인이 그 파일을 열 때 규칙이 지연 로딩된다).
- 도구 4건은 실재한다 — 초기화 `services/core-api/ops/reset_dev_environment.py` · 부트스트랩 `infra/dev/db-bootstrap.sh` · 배포 실행기(`infra/dev/README.md`) · 러너 `dev-package/tools/dev-seed/`. 넷을 잇는 진입점만 없다.
- 런북 정정 6건은 `dev-package/prd/rounds/R-DEV-RESET.md §11-1` ⑴~⑹(스킴 · `--user 0` · 버킷·리전 리터럴 · `psql` 이미지 · 비밀번호 환경변수 4건 · 체인별 버전 표). 러너 정정 7건은 `dev-package/tools/dev-seed/README.md` 9 절.
- 초기화 게이트 넷 = `.claude/rules/deploy.md` 〈395〉 증보 문단(`--target dev`＋`--yes-reset-dev` · 버킷 정확 일치 · DB URL 호스트 `-dev` · 계획 키 `uploads/`·`previews/` 안). `_ops/` 무접촉 · exact-key＋sha256.

## 5. WU 표

| WU | 이름 | 성격 | 선행 |
|---|---|---|---|
| WU-C0 | 회차 판정 등재(intent 확정 · 대장 · HANDOFF · 규칙 개정 · 이 파일) | 레인 1개(`lane-worker`) · 유일한 원장 편집 레인 | 없음 |
| WU-C1 | 정본 md 4건 확정 ＋ `build_plan.py` yaml 블록 생성 | 레인 1개 | 없음(C0 와 병렬) |
| WU-C2a | 등록 활성 조건 「ready 또는 failure」 ＋ 문면 ＋ 시험 | 레인 1개 | 없음(C0·C1 과 병렬) |
| WU-C1b | 러너 `runner.py` — 레벨 명시 선택 · 실패 시 등록 진행 · `registered(no preview)` | 레인 1개 | WU-C1 |
| WU-C2b | 가공 단계 빈 칸 ＋ 계보 규칙 자동 갱신 ＋ 규약 제약 ＋ 시험 | 레인 1개 · C2a 와 같은 파일군이라 직렬 | WU-C2a |
| WU-C3 | `reseed.sh` 10단계 ＋ preflight ＋ 스킬 ＋ 문서 ＋ dry-run 증명 | 레인 1개 | WU-C0(규칙 개정) |
| WU-C4 | dev 무인 재생성 1회 ＋ 정본 일치 검증 ＋ 등재 | 오케스트레이터 ＋ advisor 게이트 ③ · 레인 작업 아님 | C1·C1b·C2a·C2b·C3 병합 ＋ dev 배포 |

선행 도식 = C0 ∥ C1 ∥ C2a → C1b ∥ C2b ∥ C3 → C4.

### WU-C0 — 완료 정의
- ⑴ 5개 파일(intent · `work-items.yaml` · `03-HANDOFF.md` · `.claude/rules/deploy.md` · 이 파일)이 한 커밋 ⑵ `work-item-consistency`·`planning-freshness` green ⑶ 〈N〉 하드코딩 0 ⑷ `PLAN-SoT.md` 무수정.

### WU-C1 — 완료 정의
- ⑴ 4건이 레포 사본 자리에 있고 각 행에 11개 항목(이름 · 가공 단계 · 부모 · 파일 글롭 · 파일 건수 · 바이트 · 기준 격자 쌍 · 포맷 · 설명 축자 · 미리보기 기대 · 비고) ⑵ 축자 인용에 출처 파일명 ⑶ `Lv.N` ↔ `LvN` 대응 명시 ⑷ fenced `yaml` 블록 ＋ `build_plan.py` 가 그 블록만 읽어 `plan-manifest.yaml`·`upload-plan.json` 생성 · 표와 어긋나거나 계수(28 · 18 · 파일 건수 · 바이트)가 어긋나면 비영 종료(실패 픽스처 1건 이상) ⑸ Ted 확정 표시 ⑹ 기존 자료 파일 수정 0 ⑺ 열린 질문 14건 판정값 반영 · 「열린 질문」 절 → 「판정」 절.
- 입력 = `dev-package/reports/reference-data/datasets-md-draft/*.DATASETS.md`(초안 4건) · `COLAB_REF_ROOT`.

### WU-C1b — 완료 정의
- ⑴ 가공 단계를 md 값으로 명시 선택(기본값 의존 0) ⑵ 분석 실패 시 등록 진행 · 상태 `registered(no preview)` ⑶ 28건 각각의 미리보기 성립/미성립을 결과 JSON 에 기록 ⑷ 시험 red → green ⑸ 계보 AI 제안 단추 미사용 유지.

### WU-C2a — 완료 정의
- ⑴ 실패 상태(`ready=false` ＋ `failure`)에서 잠기는 것을 재현하는 시험 **먼저 red** → green ⑵ 분석 실패 업로드가 화면에서 등록까지 ⑶ 문면 「지도로 못 그려요 · 등록은 됩니다」 ⑷ 계약·마이그레이션 0 ⑸ `frontend-test`·`frontend-typecheck` 단독 green.

### WU-C2b — 완료 정의
- ⑴ 초기값 빈 칸 ⑵ 손대기 전 부모 연결·해제 시 계보 규칙(부모 최대 Lv ＋ 1 · 부모 없으면 빈 칸)으로 자동 갱신 ⑶ 손댄 뒤 어떤 값이든 허용 · 부모 Lv 초과만 거절 ⑷ 빈 레벨 등록 시험 1건(`None` 저장 · 파생값 표시 · 「미지정」 필터 포착) ⑸ 각 시험 red → green ⑹ `Lv2` 기본값 전제 시험은 판정값으로 고치되 검사 범위 축소 0 ⑺ 계약·마이그레이션 0 ⑻ `frontend-test`·`frontend-typecheck` 단독 green.

### WU-C3 — 완료 정의
- ⑴ 10단계가 `--from` 으로 재개 ⑵ `--dry-run` 무접촉 · 전 단계 명령·계수 출력 · exit 0 ⑶ 런북 정정 6건 ＋ 러너 정정이 본문에 반영 · 각 자리 근거 주석 ⑷ preflight 6항목 판정 · 미달 이름 · 비영 종료(실패 픽스처 ≥1) ⑸ prelude 에 SQL 선행 4단계 ⑹ 결과 JSON 스키마 1건 ⑺ 비밀값 argv·로그·JSON 0건 ⑻ 실행비트 인덱스 기록(`git update-index --chmod=+x`) ⑼ 실행마다 `dev-package/sessions/` 기록 자동 등재 ⑽ `exec-bit` green.
- ⛔ 이 WU 에서 dev 실환경에 대고 파괴 단계를 돌리지 않는다. 실행은 WU-C4 다.

### WU-C4 — 완료 정의
- ⑴ 사람 입력 0회 완주 ⑵ `deploy_doctor` 15/15 한 번의 실행 ⑶ 데이터셋 28 · 프로젝트 4 · 간선 18 · 프로젝트 미연결 0 ⑷ 가공 단계 분포 정본 일치 · 「미지정」 0 ⑸ 미리보기 판정 표 1건(28건 · 이름) ⑹ 차단은 이름·사유 ⑺ 구간별 소요 ⑻ `_ops/`·staging·prod 무접촉 · 파괴 단계 재시도 0 ⑼ 운영자 계정 재생성 완료.

## 6. 레인 규약

- 레인은 `Agent(subagent_type: "lane-worker", isolation: "worktree")` 로 스폰한다. 손으로 만든 형제 워크트리를 쓰지 않는다.
- **레인 하나 = 작업 하나.** 리베이스·조건 수정·구현·전수를 한 지시문에 싣지 않는다(`CLAUDE.md §5-b`).
- 레인 시작은 `git checkout -B lane/wu-c* origin/integration/r-data-canon`. 기대 HEAD 를 지시문 첫 줄에 적고 다르면 멈춘다.
- 반복 검증은 단독 게이트 — 프런트 레인 `frontend-test`·`frontend-typecheck` · 도구 레인 `exec-bit` ＋ 자기 시험 · 문서 레인 `work-item-consistency`·`planning-freshness`. 전수는 병합 직전 1회(오케스트레이터 · `gate-runner`).
- **원장 편집은 WU-C0 만 한다.** 다른 레인은 대장·HANDOFF·`PLAN-SoT` 를 건드리지 않고 등재문만 자기 최종 메시지에 적는다.
- 〈N〉 을 하드코딩하지 않는다 — 병합 직전 재실측(`dev-package/prd/tools/max-decision.sh`).
- 새 `.sh` 는 `git update-index --chmod=+x <파일>` 후 커밋.
- 최종 메시지에 `WORKTREE=… BRANCH=… HEAD=…` 를 적는다. 병합·원격 삭제·태그 push 는 레인이 하지 않는다.
- **지시가 실물과 어긋나면 멈추고 보고한다.** 우회하지 않는다.
- **기존 오류를 발견하면 「기존」이라 적지 말고 어느 검사(게이트·Dockerfile·배포)에 걸리는지 적는다.** 「main 과 동일」은 수용 근거가 아니다.
- 참조자료 폴더 쓰기는 레인이 하지 않는다(§4) — 레포 사본까지.

## 7. 운영 경계

- dev 한정. staging·prod 는 어느 단계에서도 접촉하지 않는다(초기화 도구의 식별자 거부 그대로).
- `_ops/` 무접촉 · S3 는 exact-key 계획 ＋ sha256 대조로만.
- 비밀 값(접속 문자열 · 키 · 비밀번호 · 토큰)은 0600 파일 경로로만 받는다. argv·로그·결과 JSON·문서·커밋에 0건.
- **거부가 올바른 동작이다** — preflight·게이트 넷 중 하나라도 어긋나면 부분 실행 없이 멈춘다.
- dev 재생성(WU-C4) 실행 직전에 advisor 게이트 ③(go/no-go)를 붙인다 — 상시 승인은 회차별 Ted GO 를 대체하지 advisor 판정을 대체하지 않는다.
- DB 직접 쓰기는 prelude 의 SQL 선행 4단계뿐이다. 데이터 투입은 브라우저 화면 조작(화면단 원칙 유지 · 직전 회차 확정).

## 8. 브랜치 처리 (오케스트레이터가 한다)

- 통합 `integration/r-data-canon` = `main` tip 기점(`3fc6ea01` · 2026-09-14 실측). 레인 `lane/wu-c0-ledger` · `lane/wu-c1-*` · `lane/wu-c1b-*` · `lane/wu-c2a-*` · `lane/wu-c2b-*` · `lane/wu-c3-*`.
- 레인은 통합에 rebase ＋ ff 로 얹고 즉시 삭제. 통합은 `main` 으로 ff-only 한 줄(`docs/BRANCHING.md`).
- 병합 직전 〈N〉 재실측 ＋ `work-item-consistency` 1회. 같은 트리 전수 재실행은 하지 않는다(`.claude/rules/colab-rules.md §3-2`).
- WU-C4 는 `main` 병합 ＋ dev 배포(태그 `dev-YYYYMMDD-N`) 뒤에만 실행한다 — preflight 가 dev 실행 sha == origin/main tip 을 판정한다.

## 9. 등재문 초안 (PLAN-SoT §9 · 오케스트레이터가 병합 시 번호 부여)

> **〈N〉 R-DATA-CANON 회차 — 자료 설명 정본화 ＋ dev 반복 재생성 · 판정 8건 ＋ dev 초기화 상시 승인 (2026-09-14)**
> ㉮ **문제** — 26건 전건 가공 단계 `Lv2`(등록 폼 기본값이 그대로 저장 · 러너가 사람 값을 고른 적 없음) · 가뭄 2건 등록 차단(화면이 분석 실패로 「다음 →」 잠금 · 서버·정본은 201) · 재생성이 사람 손 12단계.
> ㉯ **정본 자리** — ㈎ ⓐ 참조자료 유형 폴더 안 `DATASETS.md` 4건 · 기존 파일 무수정 · 레포 사본 `dev-package/reports/reference-data/datasets-md/`.
> ㉰ **등록 허용** — ㈏ ⓐ 분석 실패라도 등록. 활성 조건 「ready 또는 failure」(워커가 `ready=False` 를 쓰므로 `failure` 항 제거만으로 열리지 않는다). 문면 「지도로 못 그려요 · 등록은 됩니다」. GeoPackage 판독은 `FMT-GPKG`.
> ㉱ **가공 단계** — ㈐ 빈 칸 시작 · 손대기 전 계보 규칙(부모 최대 Lv ＋ 1)으로 자동 갱신 · 손댄 뒤 어떤 값이든 허용하되 부모 Lv 초과만 거절 · 빈 칸 등록 허용(`None` · 파생값 표시 · 「미지정」) · 시딩은 md 값 명시 선택. Ted 축자는 intent 「판정 결과」 ㈐.
> ㉲ **기존 26건** — ㈑ ⓑ PATCH 없이 재생성으로.
> ㉳ **승인** — ㈒ ⓑ **dev 한정 상시 승인**(`reseed.sh` 경유 · 게이트 넷 충족 · 실행마다 결과 JSON ＋ 세션 기록 · Ted 철회 시 소멸). `.claude/rules/deploy.md` 〈395〉 증보 문단 개정. staging·prod 매회 GO 무변. ／ 종전 `〈395〉`-㉲ 「승인은 1회 소진」은 dev 에서 이 행으로 대체된다.
> ㉴ **형태·장소** — ㈓ ⓒ `dev-package/tools/dev-reseed/reseed.sh` 본체 ＋ 스킬 `/dev-reseed` · ㈔ ⓐ 개발 기계 · preflight 6항목(QEMU/binfmt · AWS 자격 사슬 · 타 세션 컨테이너 · 참조자료 드라이브 · `agent-browser doctor` · dev sha == origin/main tip).
> ㉵ **미리보기** — ㈕ ⓐ 판정 표만(28건 · 이름). 뒷단 `PV-2`.
> ㉶ **10단계** — `preflight → deploy → reset → bootstrap → up+doctor → s3 → prelude → seed(browser) → verify → report`(배포 단계 신설 · 종전 9단계). yaml 기계 블록 · 러너 수정 C1b 분리 · prelude = SQL 선행 4단계 · 운영자 계정은 화면 재생성.
> ㉷ **md 열린 질문 14건** — §2 13~16 그대로.
> ㉸ **작업 단위** — C0 ∥ C1 ∥ C2a → C1b ∥ C2b ∥ C3 → C4. 대장 `DR-4` `in_progress` · 이슈 #40 #44 #48 #49 #50 포섭(관련 #41 #42).
> ㉹ **완료 판정** — dev `deploy_doctor` 15/15 한 번의 실행 ＋ 데이터셋 28 · 프로젝트 4 · 간선 18 · 「미지정」 0 · 판정 표 1건 · 사람 입력 0회.
> ㉺ **근거** — intent `dev-package/intent/2026-09-14-data-canon-and-reseed.md` · 라운드 `dev-package/prd/rounds/R-DATA-CANON.md` · 원인 조사 `dev-package/reports/r-dev-reset/feedback-2026-09-14.md`.
> ㉻ **재개봉 금지** — 위 판정 전건 · 직전 회차 확정(화면단 투입 · 파일 전건 · 목적 단위 데이터셋 · 타일별 분리 · 계보 AI 제안 미사용) 유지.

## 10. 범위 밖 (명시 제외)

- GeoPackage(`.gpkg` 등 벡터) 판독·미리보기 구현 — `FMT-GPKG` 별도.
- 미리보기 뒷단 개선(중계 대기 시간 · 렌더 서비스 메모리 · 비동기 생성 전환) — `PV-2` 별도.
- staging·prod 에 대한 초기화·재셋팅 적용. dev 식별자 밖에서 어느 조건으로도 돌지 않는다.
- 새 화면 기능(데이터셋 삭제 화면 · 연구실 생성 화면 · 등록된 데이터셋을 프로젝트에 붙이는 화면 `DS-ATTACH`).
- 상세 편집 폼에 분류 3축(분류·유형·가공 단계)을 더하는 일.
- 게이트 기반 개선(전수 실행 시간 단축 · 새 게이트 신설).
- 참조자료 기존 파일(ppt · word · 자료) 수정.
