### B5
- 판정: ⓑ (보강: 허용 조건을 `event_name != 'pull_request' || base_ref == 'product'` 로 job `if` 와 거울상으로 두고, `workflow_dispatch` 도 같은 식에 포함)
- 확신: 높음
- 사실 확인: 확인 — `ci.yml:665-679` intent-ref job `if: github.event_name == 'pull_request' && github.base_ref != 'product'` · `run: ./gates/run.sh intent-ref` 직접 실행(record 없음). `ci.yml:860` `always_required` 4개 밖 `skipped` 는 사유 대조 없이 통과. `.agents/ci-producers.json` 에 intent-ref 항목 없음. 추가 사실: `ci.yml:806` required-gates `needs` 에 intent-ref 없음이고 `verify_evidence.py:182-184` 는 `set(needs) == 등록부 job ∪ {changes}` 를 강제, `:203` 은 `filters == []` 를 「항상 적용」으로 본다 → ⓐ 로 등록하면 push(`ci.yml:4-5` develop·product)·workflow_dispatch 마다 intent-ref 가 skipped 라 `missing required check evidence`(EvidenceReadinessError) 로 required-gates 가 78. 등록부 스키마(`colab-ci-producers/1`)·`verify_evidence.py`·`test_harness_evidence.py` 동시 변경 없이는 ⓐ 불가. 정정: `intent_ref.py:15-18` 은 base 미선언 시 merge-base 로 자체 해석하므로 게이트 자체는 push 에서도 돌 수 있다(빈 범위 → green) — 그러나 그 길은 등록·이벤트 필드 없이도 「항상 실행」이 되어 product 승격 PR 에서 develop..product 전 범위를 판정하게 되므로 채택 안 함.
- 이유: 노출은 `if` 식 변경 시의 잠복 경로 1건(low)이고, ⓑ 는 `ci-required` python 에 `EVENT_NAME`·`BASE_REF` env 두 줄 + 조건 3줄로 닫힌다. ⓐ 는 등록부 스키마 버전·검증기·테스트·required-gates needs 까지 4곳을 건드려 PR 2 의 「CI verdict」범위를 넘는 고도화다. ⓒ 는 R3-12 정정 ⑵ 를 그대로 남긴다.
- 위험·전제: job `if` 와 ci-required 허용식이 두 곳에 중복된다(GitHub job-level `if` 는 env 참조 불가라 단일화 못 함) → 드리프트 검출은 `scripts/harness/check.py`(harness-contract) 에 ci.yml 두 문자열 대조 1건 추가로 막는다.
- 뒤집힐 조건: intent-ref 판정을 PR 본문 evidence(`verify_ci_bundle`)에 포함시키기로 결정되면(B6 complete 모드가 실제 사용) ⓐ 가 필요해진다 · 등록부에 이미 이벤트 조건 필드가 다른 이유로 신설되면 ⓐ 비용이 0 에 가까워진다.

### B6
- 판정: ⓐ + ⓑ 조합 + 새 선택지 보강: CI 실행은 `--mode draft` 이되 Head-SHA 불일치를 구조 실패와 분리 보고(`--stale-head warn` 류 플래그 → `::warning::` + step summary, 종료 0) · 구조·placeholder 실패만 exit 1
- 확신: 중간
- 사실 확인: 확인 — `pr_contract.py` 는 CLI 만(`main()` :98-), `.github/` 실행 0건(grep), `gates/run.sh:316` 은 `harness-contract-selftest` 에서 `test_pr_contract.py` 만. `pr_contract.py:47` `<[^>]+>|\bTODO\b|\bTBD\b` 를 필수 절 본문 전체에 적용 → `<task_id>`·`Array<string>` 오탐 확인. 추가: `:38` Plan-Ref 는 `TODO` 경계 없음(`TODOS` 오탐) · `:66` Evidence-Ref/CI-Ref 도 같은 `<…>` 규칙. 필수 절은 `harness.yaml:38` `evidence.required_pr_sections` 6개(`pr_contract.required_sections` 는 `:112` 빈 배열). `pull_request_template.md:1-34` 자리표시는 전부 줄 전체 또는 표 칸 전체 `<…>` — 공통 교정 규칙과 일치. `ci.yml:3-7` `pull_request` 는 types 미지정(opened·synchronize·reopened) → 본문 `edited` 는 재실행 안 됨 → 별도 workflow 가 맞다. `.agents/skills/colab-v2-work/SKILL.md` 에 pr_contract 언급 0(`:16,112,127` PR 요약만) · 유일한 문서 언급은 `docs/development/harness-transition-handoff.md:122`.
- 이유: 13건 실측에서 구조 실패 5(모두 Plan-Ref·필수 절 부재)는 CI 가 아니면 잡히지 않았고, ⓑ 만으로는 「선언하면 검사」가 에이전트 자율에 남아 R4-5 가 그대로다. Head-SHA 불일치 1건(#159)은 「본문 낡음」신호라 참이지만 push 마다 red 가 되면 develop 병합 push(required-gates stale base 대응) 뒤에도 본문 편집을 강제해 Ted 부담이 된다 → 경고로 분리. develop protection 에 required checks 가 없으므로(orchestrator 실측) 이 workflow 는 병합 차단이 아니라 표시이고, 승격 여부는 그룹 T.
- 위험·전제: PR 본문은 `github.event.pull_request.body` 로 읽는다(fork PR 도 read 권한 충분). complete 모드는 CI 에서 돌리지 않는다(artifact bundle 필요). 새 workflow 는 ci-producers 등록부 밖 → R3-12 의 「모든 검사 = record」예외가 intent-ref 에 이어 2건이 되므로 문서에 「advisory · evidence 아님」으로 적는다.
- 뒤집힐 조건: Ted 가 Head-SHA 일치를 병합 조건으로 삼겠다고 판정하면 경고 분리를 버리고 exact 로 · 새 workflow 가 `/hooks` 나 GitHub 설정 재신뢰를 유발한다는 증거가 나오면 ⓑ 단독.

### B7
- 판정: ⓐ (slug 앞 40자 + `-` + sha256 12자) + 공통 교정 3건 + ⓓ
- 확신: 높음
- 사실 확인: 확인 — `live_audit.sh:29` `cut -c1-60` · `:35` `<slug>.probe.json`. `frontend-visual.sh:108-112` 디스크 glob 계수, `:147` 0건만 red, `:67-75` `mkdir -p` 만, `:126-127` 잘린 배열에 allowlist. `live_probe.js:56` `slice(0, 80)` · `:38-44` 최상위 `cssRules` 만(`r.media` 검사는 top-level `@media` 만 · `@layer` 내부 불투명). `allow.txt` 활성 0건. 정정·추가: ⓐ 의 「`index.md` 에 URL↔파일 대응」은 이미 있다 — `live_audit.sh:23-27` 헤더 + `:39-46` 행마다 URL 과 `<slug>.light.png` 를 함께 적는다(index.md 만 `>` 로 절단 재생성). 선언 URL 중복은 같은 slug 가 되므로 대조 전 dedupe 가 필요하다(`URLS` 는 공백 분리 · `:50`).
- 이유: ⓑ 전체 slug 는 query 가 긴 URL 에서 파일명 255B 한계에 걸리고, ⓒ 는 도구 결함(계측 누락)을 78(환경)로 분류해 0/1/78 계약과 어긋난다. ⓐ 는 human-readable 앞부분을 남기며 충돌 확률을 없앤다. 공통 교정: ① dedupe 후 선언 수 ≠ pages → red(판정)(`:91-93` 「못 쟀다≠문제 없다」원칙) ② probe 는 `slice` 제거로 전체 배열을 내고 게이트는 `counts.small == len(small)` 불일치 시 red(판정)(이중 잠금) ③ `$OUT` 은 `rm -rf` 가 아니라 `*.probe.json`·`*.png`·`index.md` 만 삭제(사용자 지정 `COLAB_GATE_REPORT_DIR` 하위 보호). H2 는 ⓓ — `r.cssRules` 를 가진 규칙(CSSGroupingRule: `@layer`·`@media`·`@supports`) 재귀 10줄이고 ⓔ 는 design-review SKILL 이 읽는 열을 없애는 손실.
- 위험·전제: `live_audit.sh`·`live_probe.js` 는 `.agents/skills/design-review` 스킬 소유(사람용) → 파일명 변경은 SKILL 문서·`frontend-visual-selftest.sh` 픽스처(60자 공유 접두 URL 2건 · counts 불일치 1건) 동반. `agent-browser eval --json` 출력 크기 상한은 미실측 → 전체 배열이 잘리면 ② 의 불일치 red 가 잡는다.
- 뒤집힐 조건: agent-browser 가 큰 JSON 을 절단한다는 실측이 나오면 ② 를 「probe 는 `counts` 만 신뢰 · 배열은 allowlist 적용 전 하한」으로 바꾼다 · Ted 가 파일명 human-readable 을 요구하지 않으면 sha256 만으로 단순화.

### B8
- 판정: ⓒ (보강: 등록 함수 `pg_on_cleanup` 자체가 `trap pg_cleanup EXIT INT TERM` 을 멱등 설치 · `pg_cleanup` 은 등록 목록을 역순 실행 뒤 컨테이너·슬롯 정리) + operator-notifications 5개 exit 에 `_readiness.sh` 표식
- 확신: 높음
- 사실 확인: 확인 — `_pg.sh:193` `trap pg_cleanup EXIT INT TERM` · `pg_cleanup:168-172` 는 컨테이너 `rm -f` + 슬롯 release. `service-tests.sh:81-82` trap 이 `:99`·`:136` `pg_start` 앞 → 대체됨. `operator-notifications.sh:7` trap 이 `:10` 앞 · `:8,9,11,12,14` 표식 없는 `exit 78`(단 `:10` 은 `pg_start` 가 `pg_readiness_report` 를 이미 찍으므로 정상). 추가: operator-notifications 는 `ci.yml` 에 없고 `run.sh:285` `ALL_GATES` 로컬 전용. 호출자 9곳 중 `rls-coverage.sh:42→45` · `schema-diff.sh:145→148` · `artifact-ownership-selftest:62→66` · `autometa-loss-selftest:59→63` · `preview-tile-slot-selftest:54→58` 은 pg_start 뒤에 trap 을 걸어 정상 · `ci-schema-diff.sh:21-22` 는 「pg_start 가 설치한 trap 을 유지한다」고 명시해 의존. 슬롯은 어느 경로에서도 pg_start 의 trap 으로 풀리므로 누수는 `$TMP` 한정(low 유지).
- 이유: ⓑ 는 ci-schema-diff 등 의존 호출자를 전부 고쳐야 하고 미래 호출자가 `pg_cleanup` 을 빠뜨리면 컨테이너·슬롯까지 샌다(현재보다 나쁨). ⓐ 는 `trap -p` 출력(`trap -- 'cmd' EXIT`)을 eval 로 되파싱해야 해 따옴표 중첩에 취약하고 INT/TERM 을 따로 다뤄야 한다. ⓒ 는 `_pg.sh` 한 곳 + 깨진 호출자 2곳(`trap` 줄을 `pg_on_cleanup 'rm -rf "$TMP"'` 로 치환)이고, 기존 「pg_start 뒤 trap」호출자는 pg_cleanup 을 포함하므로 그대로 동작한다.
- 위험·전제: `pg_on_cleanup` 이 trap 을 설치하므로 pg_start 를 안 부르는 분기(service-tests 비-core-api 서비스)에서도 정리가 돈다 — `pg_cleanup` 은 `PGC` 빈 값·`PG_SLOT_FD` 빈 값에 안전(`:113-114,:169`). 최소안(두 호출자 trap 재설치 재배치)도 PR 2 범위 압박 시 대안으로 유효하나 재발 방지 없음.
- 뒤집힐 조건: `_pg.sh` 를 source 하는 스크립트에 `set -e` 와 `ERR` trap 조합이 있어 목록 실행 중 한 hook 실패가 뒤 hook 을 끊는 사례가 나오면 hook 마다 `|| true` 격리 추가 · CI 에서 operator-notifications 를 돌리기로 하면 표식 교정이 low 에서 상향.

### 묶음 메모
- B5 ⓑ 와 B6 ⓐ 는 둘 다 「등록부 밖 검사」를 늘린다 — PR 2 문서(`gates/README.md`·R3-12 정정)에 evidence 사슬 예외 2건(intent-ref · pr-contract advisory)을 한 번에 적는다.
- B6 ⓑ 의 SKILL 한 줄은 `colab-v2-work/SKILL.md` 공유 문서라 PR 3(C 그룹 docs drift)과 편집 충돌 → 어느 PR 이 싣는지 spec 에서 먼저 정한다.
- B7 은 `.agents/skills/design-review/scripts/*`(스킬 소유) 와 `gates/tools/frontend-visual*.sh` 를 같이 바꾸므로 selftest 픽스처 갱신이 필수이고, B8 은 `_pg.sh` 를 source 하는 9 스크립트에 걸치므로 postgres selftest 군을 한 lane 에서 순차 실행한다(슬롯 호스트 전역).
- B7 `$OUT` 삭제 범위는 `run.sh:47` 의 「report dir = 현재 task run」결합과 맞물린다 — 하위 `frontend-visual/` 안 파일만 지워 task evidence 디렉터리 전체를 건드리지 않는다.
- B5·B8 모두 78/1 분류 원칙(AGENTS.md)을 기준으로 골랐다 — `R3-gates-ci-missed`(verify_evidence record 가 등록부 불일치를 78 로 냄) 도 같은 원칙 위반이라 PR 2 에서 함께 볼 후보.