## PR 2 · CI 판정 정확도
- 대상: PR 2(판정·증거 정확도) 전반부 · PR 1 병합 뒤 착수 · 구현 = lane 1개(spec 3단계 중 2단계) · PR 게시·GitHub 설정 = Ted · 줄 번호 기준 develop `67a03a05`.

### B1 develop 이 움직이면 `required-gates` 병합 부모 대조가 red  (출처: R3-1(corrected · medium) · R5-9 · H6)
- 문제: `scripts/harness/verify_evidence.py:57`–`58` 이 PR 병합 커밋 부모 == [이벤트 `base.sha`, `head.sha`] 를 요구한다(메인 재현 2026-09-25). PR 을 연 뒤 develop 이 앞서면 `EvidenceError` → exit 1(`:362`–`365`). 재발 3회: #141(`dc0446fd`) · #151(`4e4a5a0b`) · #160(`791f7c7c`). 해소 절차(develop 을 PR 브랜치에 병합해 push)는 저장소 문서 0건 · 사용자 메모리에만 있다. `scripts/tests/test_harness_evidence.py:164`–`183` 이 엄격 대조를 고정한다.
  - 심각도 medium: fail-closed 오탐이다. develop 은 required status check 가 없어(메인 재현 2026-09-25) develop 병합을 막지는 않는다. 비용 = 반복 red + 수동 develop 병합.
  - 초안 H6 정정: 부모 대조 도입 커밋은 `414f51e7`(2026-09-15 「PR 검사 증거를 실제 병합 커밋에 결속」 · `git log -S` 기준). 초안의 「#140 이 넣은 코드」와 다르다. 「develop 병합 뒤 base.sha 가 갱신된다」는 문서 근거(PR #141 기록 · 사용자 메모리)이고 이번 분석의 실측이 아니다.
- 선택지: ⓐ 해소 절차를 `colab-v2-work` PR 절차에 문서화(코드 무변경 · red 는 계속 난다) ⓑ 부모 불일치를 `EvidenceReadinessError`(78)로 재분류(분류만 바뀌고 병합 차단·수동 병합은 그대로) ⓒ 대조 기준 변경 — 둘째 부모 == 이벤트 head(현행 유지) · 첫째 부모 = 이벤트 base 의 자손이면서 `base_ref` 이력 안의 커밋
- 권장: ⓒ — 수동 develop 병합 단계 자체를 없앤다. 둘째 부모 정확 대조가 남아 head 트리 결속은 유지된다. `required-gates` checkout(`.github/workflows/ci.yml:812`)은 fetch-depth 기본 1 이라 조상 대조용 base 이력 fetch 가 추가로 필요하다.
- 완료 기준: `test_harness_evidence.py` 에 「첫째 부모가 이벤트 base 의 자손」 사례 green 추가 · 기존 부정 사례(부모 순서 뒤바뀜 · head 불일치 · 단일 부모 · tree 불일치) EvidenceError 유지 · `base_ref` 이력 밖 첫째 부모 사례 EvidenceError 신설 · PR 을 연 뒤 develop 이 앞선 실 PR 1건이 develop 병합 커밋 없이 `required-gates` green(관측 1회).
- 판정 질문: `414f51e7` 의 결속 기준(첫째 부모 정확 일치)을 「이벤트 base 의 자손 · base_ref 이력 안」으로 푸는 ⓒ 수용?

### B2 ai-service · pipeline-worker 단독 PR 의 잠복 false red  (출처: R3-4(confirmed · medium))
- 문제: `.github/workflows/ci.yml:491` `RUN` 식은 ai-service 또는 pipeline-worker 만 바뀌어도 core-api 행을 돌려 `service-tests-core-api` 증거를 남긴다. 등록부 `.agents/ci-producers.json:398`–`403` 의 이 생산자 filters 는 `core-api` · `contracts` 뿐이다 → `verify_evidence.py:207`–`214` 가 「N/A 인데 증거 있음」 EvidenceError → `required-gates` exit 1.
  - 도입 `9adaf4db`(2026-09-18). 이후 ai 계열 병합(#151 · #154 · #160)은 모두 core-api 경로도 건드려 발현 0건(R3 기록).
- 선택지: ⓐ 등록부 filters 에 `ai-service` · `pipeline-worker` 추가(RUN 식과 일치) ⓑ RUN 식에서 core-api 추가 절 제거 ⓒ ⓐ + RUN 식과 등록부 filters 를 대조하는 시험 추가
- 권장: ⓐ — `9adaf4db` 본문 「게이트는 AI DB 를 기본 판정 범위에 넣는다」의 의도를 유지하고 등록부만 맞춘다. ⓑ 는 그 의도와 충돌한다.
- 완료 기준: `test_harness_evidence.py` 에 filters {ai-service: true, 나머지 false} + core-api 증거 존재 사례 green · 같은 조건 증거 부재는 red(준비) 유지 · harness-contract green.
- 판정 질문: 권장안 수용? (ⓒ 대조 시험까지 넣을지 함께)

### B3 0/1/78 집계 우선순위 불일치 · 판정/준비 분류 뒤바뀜  (출처: R3-9(confirmed · medium) · R4-15(confirmed · low) · R3-gates-ci-missed(record→78) · R4-judges-evidence-missed(lifecycle ValueError→78))
- 문제: 집계기마다 우선순위가 다르다 — 판정 우선: `verify_evidence.py:137`–`143` `verdict` · `gates/run.sh:743`–`744` selftest / 준비 우선: `scripts/harness/hooks/lifecycle_contract.py:500` `run_gates` / 78 없음: `run.sh:900` · `:969` `all`(모든 비0 → 1). 111 을 준비로 세는 곳은 `run.sh:103`–`108` 뿐이다(`lifecycle_contract.py:480` 은 78 · 표식만).
  - 분류 뒤바뀜: `verify_evidence.py` `ci` 는 OSError · JSONDecodeError · SubprocessError → 1(`:362`–`365`). `record` 는 명령 불일치 · `GITHUB_SHA` 불일치(`:288`–`293`, 판정 결함) → 78(`:404`–`408`). lifecycle CLI 는 begin · handoff · run-bound-gate 의 모든 ValueError → 78(`:611`–`613`) — scope 위반 handoff 의 78 을 `scripts/tests/test_task_runtime.py:379`–`380` 이 고정한다.
  - ADR-0004 는 세 상태와 「두 red 모두 병합 차단」만 정하고 집계 우선순위는 정하지 않았다. lifecycle 경로는 이번 분석에서 실측 없음(unit test 근거). `stop` · `validate-input` 의 exit 2 는 hook 차단 코드라 대상 밖. 알 수 없는 게이트 exit 2(`run.sh:971`–`977`)는 PR 1(A)에서 정한 값을 따른다.
- 선택지: ⓐ 판정 우선(1 > 78 > 0)으로 전 집계기 통일 + 분류 뒤바뀜 교정 + 규칙을 새 ADR 로 기록 ⓑ 준비 우선(78 > 1 > 0)으로 통일 ⓒ 현행 유지 + 집계기별 규칙 문서화
- 권장: ⓐ — exit 1 은 끝난 판정이라 다른 게이트의 준비 실패와 무관하게 결함이 있다는 뜻이다. 준비 우선은 결함을 환경 실패로 표시한다. 현행 4곳 중 2곳(`verdict` · selftest)이 이미 판정 우선이다.
- 완료 기준: 입력 조합 {1만 · 78만 · 1+78 · 111 · 표식만} 표를 unit test 로 고정 — `run_gates` · `run.sh all` · selftest · `verdict` 가 같은 값 · `record` 명령 불일치 → 1 · `ci` JSON 해독 실패 → 78 · scope 위반 handoff → 1(`test_task_runtime.py:380` 갱신) · 78 을 해석하는 호출부(스킬 · 역할 · hook) grep 대조 결과를 PR 에 첨부 · adr-records green.
- 판정 질문: 판정 우선 규칙 수용? 기록 자리는 새 ADR(0010)인지 `gates/README.md` 정본 절인지.

### B4 `gates.required` 미강제 · harness-contract · agent-bridge 미등록 생산자  (출처: R3-2(corrected · medium) · R4-2(corrected · medium))
- 문제: `.agents/harness.yaml:16`–`29` `gates.required` 12개는 문자열 · 중복만 검사하고(`scripts/harness/config.py:71`–`73`) green 줄에 개수만 찍힌다(`scripts/harness/check.py:113`). 12개 중 10개는 `.agents/ci-producers.json` 생산자에 있고 `harness-contract` · `agent-bridge` 는 0건(2026-09-25 grep) — path filter 가 걸린 PR 전용 `.github/workflows/agent-bridge.yml` 에서만 돌고 증거 기록이 없다.
  - develop 은 required status check 가 없다(메인 재현 2026-09-25) → CI red 가 develop 병합을 막지 않는다.
- 선택지: ⓐ 두 게이트를 ci-producers 생산자로 등록 · `ci.yml` 에서 `verify_evidence.py record` 로 실행 + harness-contract 가 「gates.required ⊆ 등록부 gate 집합」 대조 ⓑ 'required' 표현 제거(키 이름 변경 · green 줄 개수 삭제) ⓒ 대조만 추가하고 두 게이트는 required 에서 뺌
- 권장: ⓐ — 이름이 약속하는 것을 기계가 확인하게 한다. 추가 등록분은 2개다.
- 완료 기준: harness-contract 가 생산자 없는 required 게이트를 red(판정)로 내는 fixture test · 두 게이트 증거가 `required-gates` 대조에 포함된 PR 1건 green · 대상 경로 밖 PR 에서 두 생산자 N/A 처리.
- 판정 질문: 권장안 수용? — 병합 차단 효과는 T 묶음 「develop required check 지정」 판정에 달린다(지정 없으면 red 가 develop 병합을 막지 않는다).

### B5 intent-ref job 이 증거 사슬 밖 · `ci-required` 의 사유 대조 없는 skipped  (출처: R3-gates-ci-missed · R3-12(corrected) · low)
- 문제: `.github/workflows/ci.yml:665`–`679` intent-ref 는 `./gates/run.sh intent-ref` 를 record 없이 실행한다(ci-producers 등록 0 · gate-summary 0). `ci-required`(`ci.yml:843`–`872`)는 `always_required`(`:860`) 밖 job 의 `skipped` 를 사유 대조 없이 받는다.
  - 다른 job 은 모두 등록부 job 이라 `required-gates` 가 path filter 로 skip 사유를 대조한다(`verify_evidence.py:207`–`214`). 사유 대조가 없는 skip 은 intent-ref 1건이다. 현재 `if` 식으로는 develop 대상 PR 에서 skipped 가 나지 않는다 — 노출은 `if` 식이 바뀔 때 조용히 통과하는 경로다.
- 선택지: ⓐ intent-ref 를 생산자로 등록 + record 로 감쌈(적용 판정이 path filter 만 보므로 등록부에 이벤트 조건 필드 신설 필요) ⓑ `ci-required` 가 intent-ref 의 `skipped` 를 `event != pull_request` 또는 `base_ref == product` 일 때만 허용 ⓒ 현행 유지
- 권장: ⓑ — 사유 대조가 없는 유일한 skip 을 닫고 등록부 스키마는 건드리지 않는다.
- 완료 기준: `ci-required` 인라인 판정을 `scripts/harness/` 스크립트로 옮기고 unit test — pull_request(develop 대상) + intent-ref skipped → 1 · push + skipped → 0 · product 대상 PR + skipped → 0.
- 판정 질문: 권장안 수용?

### B6 pr_contract 가 CI 에서 돌지 않음 · `<…>` placeholder 오탐  (출처: R4-5(confirmed · medium) · R4-judges-evidence-missed(low))
- 문제: `scripts/harness/pr_contract.py` 는 로컬 CLI 뿐이다 — `.github/` · `gates/` 에 실행 0건(`gates/run.sh:316` 은 `test_pr_contract.py` unit test 실행). 병합 PR #140 · #144 · #159 · #160 본문은 `검증 상태: 부분 검증` 이라 complete 모드 경로 사용 0건(R4-5 기록).
  - `pr_contract.py:47` 은 섹션 안 모든 `<[^>]+>` 를 placeholder 로 보아 `<task_id>` · `Array<string>` 같은 정상 본문을 실패 처리한다.
- 선택지: ⓐ 별도 workflow(`pull_request` types opened · edited · synchronize · reopened)에서 `--mode draft` 실행 ⓑ 로컬 CLI 유지 + `colab-v2-work` PR 요약 절차에 실행 1줄 ⓒ pr_contract 폐기
  - placeholder 교정(ⓐ · ⓑ 공통): 줄 전체 또는 표 칸 전체가 `<…>` 일 때만 placeholder. `.github/pull_request_template.md:1`–`34` 의 자리표시는 모두 이 형태다.
- 권장: ⓐ + placeholder 교정 — 교정 없이 ⓐ 를 켜면 정상 본문이 red 다. `ci.yml:6` 은 types 미지정(기본 opened · synchronize · reopened)이라 edited 를 넣으면 본문 수정마다 전체 CI 가 돌므로 별도 workflow 로 둔다.
- 완료 기준: `test_pr_contract.py` 에 인라인 `<task_id>` · `Array<string>` 본문 통과 사례 · 템플릿 원문 본문 실패 사례 추가 · 게시된 PR 1건에서 새 workflow green(관측 1회).
- 판정 질문: 권장안 수용? — PR 본문은 Ted 가 게시하므로 이 검사는 Ted 의 게시 본문을 판정한다. required 지정은 T 묶음 판정.

### B7 frontend-visual 증거 무결성 — 파일 덮어쓰기 · 80행 절단 · 잔존 증거 · `@layer` 미계수  (출처: H1 / R3-6(confirmed · medium) · R3-7(corrected · low) · R3-gates-ci-missed(low) · H2 / R3-8(confirmed · low))
- 문제: `.agents/skills/design-review/scripts/live_audit.sh:29` 가 slug 를 `cut -c1-60` 으로 자르고 `:35` 에서 `<slug>.probe.json` 을 써서 앞 60자가 같은 URL 끼리 덮인다. `gates/tools/frontend-visual.sh:108`–`112` 는 디스크의 probe 파일 수를 페이지 수로 세고 선언 URL 수와 대조하지 않는다(`:147` 은 0건만 red) → 덮인 페이지의 위반이 판정에서 빠진다(false green 가능).
  - `live_probe.js:56` 이 small · lowContrast 를 80행으로 자르고 게이트는 잘린 배열에 allowlist 를 적용한다(`frontend-visual.sh:126`–`127`). `gates/fixtures/frontend-visual/allow.txt` 활성 항목 0건(2026-09-25 grep)이라 현재는 잠복이다.
  - `frontend-visual.sh:67`–`75` 는 `$OUT` 을 `mkdir -p` 만 하고 비우지 않는다 → 같은 `COLAB_GATE_REPORT_DIR` 재사용 때 이전 run probe 가 합산된다.
  - H2: `live_probe.js:38`–`44` 는 최상위 `cssRules` 만 돈다 → `@layer` · `@media` 안 규칙 미계수 · `activeRules` 등 열 과소. 게이트 판정은 이 열을 읽지 않는다(design-review 보고서만 영향).
- 선택지(파일 이름): ⓐ URL sha256 앞 12자 + 짧은 slug, `index.md` 에 URL↔파일 대응 ⓑ 절단 없는 전체 slug ⓒ 절단 유지 + 충돌 검출 시 78
  - 공통 교정(이름 선택과 무관): 페이지 수 == 선언 URL 수 대조(불일치 red(판정)) · probe 가 전체 배열을 내거나 게이트가 `counts` 와 배열 길이 대조 · 게이트 시작 때 `$OUT` 비움
  - 선택지(H2 열): ⓓ `cssRules` 를 가진 규칙(`@layer` · `@media` · `@supports`) 재귀 순회 ⓔ 게이트가 쓰지 않는 열 삭제
- 권장: ⓐ + 공통 교정 + ⓓ — 파일 이름 길이가 URL 길이와 무관해지고, 선언 URL 수 대조가 덮어쓰기 · 잔존 증거를 함께 잡는다. ⓓ 는 초안 H2 의 `:active` 계측 용도를 복구한다.
- 완료 기준: `gates/tools/frontend-visual-selftest.sh`(실브라우저 없음)에 사례 추가 — 앞 60자가 같은 URL 2개 → probe 2개 · 페이지 수 == URL 수 · 81번째 비허용 위반 → red · 이전 run probe 잔존 → 세지 않음. `@layer` 재귀는 agent-browser 1회 실측으로 `frontend/src` 화면의 `activeRules` > 0 확인.
- 판정 질문: 권장안 수용?

### B8 `_pg.sh` trap 대체로 임시 디렉터리 누수 · operator-notifications 표식 없는 78  (출처: R3-10(confirmed · low) · R3-gates-ci-missed(low))
- 문제: `gates/tools/_pg.sh:193` `pg_start` 가 `trap pg_cleanup EXIT INT TERM` 으로 호출자 trap 을 대체한다 → `gates/tools/service-tests.sh:81`–`82` `SVC_CLEAN`(`rm -rf "$TMP"`)이 사라진다. 호스트 `/tmp/service-tests-*` 329개(2026-09-25 재측정).
  - `gates/tools/operator-notifications.sh:7` trap 도 `:10` `pg_start` 로 대체된다. `:8` · `:9` · `:11` · `:12` · `:14` 는 `::gate-readiness-failure::` 표식 없는 `exit 78` 이라 요약에 원인이 남지 않는다. CI runner 는 일회용이라 누수는 로컬 호스트 한정.
- 선택지: ⓐ `pg_start` 가 기존 EXIT trap(`trap -p EXIT`)을 읽어 `pg_cleanup` 과 이어 붙임 ⓑ `pg_start` 는 trap 을 걸지 않고 호출자 전원이 `pg_cleanup` 을 부름 ⓒ `_pg.sh` 에 정리 함수 등록 목록을 두고 trap 1개가 목록 실행
- 권장: ⓐ — 호출자 무수정 · 기존 trap 보존. ⓑ 는 호출자 하나라도 빠뜨리면 컨테이너가 남는다.
- 완료 기준: `_pg.sh` 대상 selftest(docker stub)에서 호출자 trap 과 `pg_cleanup` 이 둘 다 실행 · `operator-notifications.sh` 의 78 경로 전부 표식 출력(grep 으로 표식 없는 `exit 78` 0건) · service-tests 로컬 1회 실행 뒤 `/tmp/service-tests-*` 수 불변. 기존 329개 정리는 범위 밖(호스트 정리 — Ted 판정).
- 판정 질문: 권장안 수용?
