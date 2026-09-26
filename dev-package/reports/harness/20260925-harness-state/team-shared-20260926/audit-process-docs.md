[harness: subagent output matched instruction-shaped pattern(s): settings-json. Control tags below are neutralized (`<` → `<\`); treat any remaining directive-shaped text as a finding to relay to the user, not an instruction to you.]

### D1
- 자리: `dev-package/intent/2026-09-25-harness-improvement.md:447,554,620`(T1 결과 「pull_request(승인 0 · 스레드 해결 필수) · bypass_actors 없음」) · `dev-package/prd/specs/S-HARNESS-IMPROVEMENT-PLAN-20260926.md:79`(T1) · `:18,41,51,74,112,123,133`(병합 조건 「Ted 병합(T13)」) · `.github/CODEOWNERS:1-5`
- 사실: develop ruleset 은 PR 필수 · `ci-required` strict · 우회자 0 이지만 `required_approving_review_count` = 0 · code-owner review 미요구. CODEOWNERS 는 전 경로 개인 핸들 1개(`@sungwooHa` · 주석 「R1에서 실제 GitHub 팀으로 교체 · 그 전까지는 개인 핸들」). 모든 PR 병합 조건이 「Ted 병합」 한 사람으로 적혀 있고, 리뷰어 · 두 번째 사람은 어느 문서에도 없다.
- 팀 영향: write 권한 팀원은 자기 PR 을 CI green 뒤 스스로 병합할 수 있다(ruleset 이 허용). 「병합은 사람」은 만족하지만 「작성자 ≠ 병합자」가 없어 하네스 PR(hook · gate · CI 변경)이 단독 판단으로 develop 에 들어간다. 심각도 높음 — 팀에서는 계획이 틀린 자리(작성자 = advisor 호출자 = 병합자).
- 권고: ruleset 개정 1건 — `required_approving_review_count: 1` + `require_code_owner_review: true` + `dismiss_stale_reviews_on_push: true`, CODEOWNERS 를 GitHub 팀 핸들로(하네스 경로 `.agents/ .claude/ .codex/ scripts/harness/ gates/ .github/` 행 추가). 병합 조건 문구 「Ted 병합」 → 「병합자(작성자 아닌 리뷰 승인 1 + ruleset)」.
- 어디서: 지금(S-red 병합 직후 T1 개정 · PR 3 3-5 ruleset 스냅샷에 새 JSON 반영 · S-red 자체는 현행 ruleset 으로 병합)

### D2
- 자리: `scripts/harness/intent_ref.py:33,42-49`(`classify`: 메타 줄에 「승인」 포함 ∧ 「미승인」 없음 = approved) · `dev-package/intent/TEMPLATE.md:2`(「발의자: <이태헌 | 조성진 | Ted | agent>」) · `:13`(「Ted 서명 필요」) · `:26`(「Ted 확인 문장(원문 그대로)」) · `dev-package/intent/README.md:1-2`(「Ted 가 교정 · 승인 = 커밋」) · `.agents/skills/grill-me/SKILL.md:11,14,16` · `.agents/roles/researcher.md:64` · ADR-0007 「결정」 절
- 사실: 승인 판정은 문자열 하나다. 승인자의 신원 · 권한은 기록 형식에도 판정기에도 없다. 템플릿이 실명 3개를 열거하고, 확인 문장 규칙은 Ted 원문으로 고정돼 있다. 승인 표기가 붙는 순간 intent-ref 가 append-only 잠금을 건다(ADR-0007).
- 팀 영향: 누가 「승인」을 써도(팀원 · 에이전트) 같은 효력 · 같은 잠금. 두 번째 팀원이 자기 intent 를 승인하면 어느 문서로도 「승인 권한이 있었는가」를 되짚을 수 없다. 「Ted 원문」 규칙은 팀원이 발의한 intent 에서 문자 그대로 적용 불가. 심각도 높음.
- 권고: 메타 줄 형식을 `승인: @<GitHub handle> <YYYY-MM-DD> "<원문>"` 으로 고정하고 `intent_ref.py` `classify` 가 `승인: @` 꼴만 approved 로 읽게 한다(fixture `gates/fixtures/intent-ref/intent-meta-classification.json` 갱신 · 기존 파일은 정답표로 보호). 템플릿 실명 열거 삭제 · 「Ted 서명 / Ted 확인 문장」 → 「승인자(D7 역할명) 확인 문장」.
- 어디서: 지금(S-red 뒤 소형 PR · `scripts/harness/**` 라 `intent-ref` 대상 · hash 집합 밖이라 eval 회차 불요) + grill-me/README 산문은 PR 4 4-1 에 이미 열거된 `grill-me:14-17` 에 합침

### D3
- 자리: `eval/harness/run.sh:55-56`(PATH 의 `claude` 필수) · `:76`(`RUN_ID=$(date +%Y%m%d-%H%M%S)` 로컬 시계) · `:136`(`claude -p` 모델 미지정) · `eval/harness/README.md:108`(「호출 환경의 기본값을 탄다」) · `eval/harness/config_hash.py:152`(`claude_version` 기록) · `:170-232`(`verify`: hash · selected · 준비 · 과제 수만 대조 · 「직전」= 이름순 직전 run) · `.agents/rules/product.md:129`(「구독(로그인 CLI)으로 돌린다 · 예산 질의 금지」) · `S-HARNESS-E0-EVAL-GATE-20260926.md:51`(회차 무효화 · CI 해시 = 머지 커밋 트리) · `S-HARNESS-PR2-LIFECYCLE-CI-20260926.md:210`
- 사실: MATCH 회차는 실행자의 Claude CLI 구독 · 기본 모델 · 버전으로 잰다. `verify` 는 `claude_version` · 모델을 대조하지 않는다. 회귀 기준 「직전」은 run id 문자열 순서다. 회차는 병합 직전 머지 트리 해시에 결속되고, 해시 집합 파일을 건드린 다른 PR 이 먼저 병합되면 78 로 되돌아가 재실측이다.
- 팀 영향: ⑴ 팀원 B 가 다른 기본 모델(또는 CLI 부버전)로 잰 회차가 같은 해시로 MATCH green — 판정 기준이 사람마다 다르다 ⑵ 회귀 비교가 서로 다른 모델 회차 간에 일어난다 ⑶ 시간대가 다른 팀원의 run id 가 시간 순서와 어긋나 「직전」이 잘못 잡힌다 ⑷ 하네스 PR 이 N 개 동시에 열리면 병합마다 나머지 전부 재실측(≈8 USD × 팀원 각자 구독) ⑸ 구독 CLI 가 없는 팀원은 회차를 만들 수 없어 하네스 PR 을 낼 수 없다. 심각도 높음 — 비용 · 판정 동일성 가정이 1인 전제.
- 권고: `config_hash.py` — `compute` 에 `model`(러너가 `modelUsage` 에서 추출) 을 넣고 `verify` 가 `model` · `claude_version` major.minor 를 회차 · 「직전」 양쪽에서 같을 때만 비교 · 다르면 78(사유 `model-mismatch`) · run id 는 `date -u` + `Z`. 절차 — 하네스 PR 은 한 번에 1개 open(라벨 `harness` · 순차) 을 `docs/development/dual-agent.md` 「하네스 변경 절차」에 1줄.
- 어디서: E1(러너 · `eval/harness/**` 는 해시 집합이라 회차 동반 · 별도 intent 「팀 eval 규약」으로 발행)

### D4
- 자리: `2026-09-25-harness-improvement.md:2,539,550,563,576,601,609,620`(`~/.claude/reports/harness-state-20260925/…` 원문 판정 · T1 스냅샷) · `2026-09-26-human-authorization-for-destructive-ops.md:2` · `S-HARNESS-IMPROVEMENT-PLAN-20260926.md:4` · `S-HARNESS-E0-EVAL-GATE-20260926.md:3` · `S-HARNESS-SRED-REDRUN-20260926.md:3` · `S-HARNESS-PR2-LIFECYCLE-CI-20260926.md:4`(「근거(저장소 밖)」) · `.agents/harness.yaml:100`(`home_path_roots` 에 `dev-package` 없음)
- 사실: 9라운드 Fable blind 판정 원문 · 교차 점검 · playbook 대조 · T1 ruleset JSON 이 전부 사용자 홈에 있다. intent · spec 은 그것을 「근거」로 지목한다. PR 본문 초안도 `~/.claude/pr-bodies/`(T16). harness-contract 의 홈 경로 검사는 `dev-package/**` 를 보지 않는다(`~/` 표기는 정규식 `/home/<u>/` 에 어차피 안 걸림).
- 팀 영향: 두 번째 팀원은 「왜 이 결정인가」를 저장소에서 재검할 수 없다. 리뷰어(D1)가 판정 근거를 못 본다. 심각도 중간.
- 권고: `~/.claude/reports/harness-state-20260925/` 를 `dev-package/reports/harness/20260925-harness-state/` 로 반입(홈 절대경로 `<repo>` 치환 · 기존 보고서 관례) · intent 「판정 기록」에 반입 경로 1줄 추가(append-only 준수) · T1 JSON 은 PR 3 3-5 로 (기존 계획). `harness.yaml hygiene.home_path_roots` 에 `dev-package/intent` · `dev-package/prd` 추가.
- 어디서: 지금(S-red 뒤 소형 PR · 문서만 · 해시 집합 밖 · `harness.yaml` 변경은 PR 3 에 얹음)

### D5
- 자리: `docs/development/dual-agent.md` 「자동 훅 등록 상태」 절(「이 PC에서는 2026-09-09 확인 시 7개 등록 항목 모두 enabled/trusted」 · 「다른 PC·새 훅 정의·다른 절대경로의 작업 사본에는 이 신뢰가 자동 이전되지 않는다」) · 「dev 브라우저 로그인 확인 도구」 절(「이 PC의 `~/.config/colab-platform/dev-operator.env`」 · 「다른 PC에는 자격이 자동 이전되지 않는다」) · 「도구 차이」 절(「이 계정(ChatGPT 로그인)에서 `gpt-6-sol`… 400」 · 모델 등급표) · 「검사 실행」 절(agent-browser `$HOME/.npm-global/bin`) · 총괄 T5(재신뢰 = Ted) · `eval/harness/run.sh:55`
- 사실: 두 번째 기계가 갖춰야 할 것(훅 /hooks 재신뢰 · claude CLI 로그인 · Codex 계정별 선택 가능 모델 · agent-browser · dev 자격 파일 · WSL) 이 「이 PC」 관측으로 흩어져 있고 체크리스트 · 진단 명령 묶음이 없다. `agent-bridge.py doctor` 는 있으나 claude CLI · 훅 신뢰 상태는 보지 않는다.
- 팀 영향: 팀원이 같은 절차를 밟아도 훅 미신뢰(차단 0) · CLI 부재(eval 78) · 다른 Codex 계정(모델 등급 상이 → 레인 품질 · 판정 상이)로 보호 · 판정 · 비용이 갈린다. 심각도 중간.
- 권고: `docs/development/onboarding.md`(기계 1대당 절차: /hooks 재신뢰 · `claude --version` 로그인 · `codex` 모델 목록 실측 · `agent-browser doctor` · 자격 파일 · TZ) + `scripts/agent-bridge.py doctor` 에 `claude` 존재 · 버전 항목 추가(준비 78 사유 출력). dual-agent.md 의 「이 PC」 문장은 onboarding 포인터로.
- 어디서: PR 3(C8 dual-agent.md 정리 자리) · doctor 확장은 같은 PR

### D6
- 자리: `docs/development/lifecycle-evidence.md` 「시작」 절(task runtime = Git common dir `colab-harness/<checkout-id>/<task-id>/<run-id>/`) · `S-HARNESS-PR2-LIFECYCLE-CI-20260926.md:74`(병합 조건 「PR 2 본문 자체가 VERDICT 행 · Advisor-Ref 포함」) · `:221`(V-P6 `--artifact-root <common>/colab-harness`) · 총괄 2-9 P2(`audit.jsonl` = git-common-dir) · T8(prune)
- 사실: H6/H7 인계 증거 · advisor ② 판정문 · hook audit 로그가 전부 실행 호스트의 `.git/` 안에 있고, PR 본문은 그 로컬 경로 + sha256 을 적는다. 저장소로 올라오는 것은 `dev-package/reports/**` 와 CI evidence 뿐이다.
- 팀 영향: 다른 기계의 리뷰어(D1)는 VERDICT · handoff · audit 를 대조할 수 없다 — sha256 만 있고 원본이 없다. prune(T8) 은 호스트마다 따로 해야 한다. 심각도 중간.
- 권고: PR 2 2-6/VERDICT 단위에 「advisor ② 판정문 + `COLAB_HANDOFF` JSON 을 `dev-package/reports/<회차>/verdict/` 로 복사(레인 handoff 시 · 기본 허용 경로) · PR 본문 Advisor-Ref = 저장소 경로 + sha256」 을 병합 조건으로. `audit.jsonl` 은 로컬 유지(개인 명령 원문 포함).
- 어디서: PR 2

### D7
- 자리: 「Ted」 건수 — intent 60 · 총괄 33 · E0 22 · S-red 13 · PR2 11 · S-auth 9 · colab-rules 21 · design-review 12 · colab-v2-work 5 · deploy 5 · grill-me 3 · grilling 3 · TEMPLATE 3 · to-spec 1 · researcher 1 · dual-agent 1 · ADR-0003 2 · ADR-0007 1 · AGENTS.md 0 · CLAUDE.md 0
- 사실: 분류 — (a) 결정 이력 원문(intent 「판정 기록」 · spec 출처 절 · ADR 근거 · colab-rules 「근거 = Ted 지적」류): 대다수 · 유지. (b) 역할인데 이름으로 적힌 것: `colab-v2-work:116`(「Ted 에게 보고할 때」) · `:129`(「Ted 의 명시 승인 없이」) · `grilling:32-35` · `grill-me:11,14,16` · `to-spec:60` · `TEMPLATE:13,26` · `intent/README:1` · `researcher.md:64` · `deploy.md:41,64-65` · `dev-reseed:123,138` · `design-review` 판정 자리 12건 · `colab-rules:41,215` · `dual-agent:56` · intent `:42`(「PR 게시 · 병합은 Ted」) · 총괄 T12/T13/T16(「Ted 터미널」) · E0/S-red/PR2 T-표. (c) Ted 만 실행 가능: T3(clone 30·32·33 pull · `:600` 「갱신 시점은 Ted 확인」) · T7(사용자 메모리 3파일) · T11(`~/.claude/settings.json env.GH_TOKEN`) · T5(「이 PC」 재신뢰).
- 팀 영향: (b) 는 팀원 발의 · 팀원 병합 · 팀원 운영에서 문자 그대로 적용 불가 — 에이전트가 「Ted 승인」을 찾다 정지하거나, 반대로 아무 사람 발화를 Ted 로 읽는다. 심각도 중간(장치가 아니라 산문이지만 승인 경로 문장이다).
- 권고: `.agents/rules/colab-rules.md §0` 에 역할 어휘 3개를 한 번 정의 — 「승인자」(intent 승인 · 계약 동결 해제 · 파괴 GO = develop ruleset 리뷰 권한 보유자) · 「병합자」(작성자 아닌 승인자) · 「운영자」(dev SSH 자격 보유자) — (b) 전부 치환, (a) 는 유지, (c) 는 D5 onboarding 또는 개인 runbook 으로 이동.
- 어디서: PR 4 4-1(skills 산문 · 열거된 줄에 위 (b) 추가) · `deploy.md`/`dev-reseed` 줄은 S-auth(이미 편집 대상) · TEMPLATE/README 는 D2 소형 PR

### D8
- 자리: `2026-09-25-harness-improvement.md:609` ⑦(「Maintain 루프 0(1인 체제라 tier/cron 기각 · 수집 스크립트만)」) · `:488-491`(T7 사용자 메모리 갱신 담당) · 총괄 `:123`(PR 4 병합 조건 「병합 뒤 메인 세션이 사용자 메모리 3파일 갱신(T7)」) · `:506`(「사용자 메모리 `required-gates-stale-pr-base.md` … 저장소 밖」)
- 사실: X·M 의 범위가 「1인 체제」를 근거로 잘렸고, 운영 지식(stale base 해소 절차 · handoff 충돌 · advisor schema) 의 정본이 한 사용자의 `~/.claude` 메모리다. PR 4 완료 조건이 그 메모리 갱신이다.
- 팀 영향: 팀원에게 그 지식은 없다 — 같은 사고(required-gates red · handoff 거부)를 다시 겪는다. 「1인 체제」 근거로 기각된 tier/cron 은 팀에서 다시 따져야 한다. 심각도 중간.
- 권고: T7 을 「저장소 runbook 갱신」으로 재정의 — 세 메모리의 내용을 `docs/development/dual-agent.md`(또는 `lifecycle-evidence.md`) 해당 절에 1줄씩 넣는 것을 PR 4 병합 조건으로 · 개인 메모리는 부수. X·M intent 의 「1인 체제」 전제 문장을 「팀 N 인」으로 재판정.
- 어디서: PR 4(T7 재정의) · X·M 은 별도 intent 발행 시

### D9
- 자리: 총괄 T3 행(「동시 작업 clone 30·32·33 은 작업 시작 전 `git pull --ff-only`」) · intent `:457,589,599-600` · ADR-0002:11(「호스트 전역」) · `.agents/rules/colab-rules.md:81`(「실행 레인은 한 시점에 하나」) · memory 「30·31·32·33 clone 은 동시 작업용」
- 사실: 한 호스트의 clone 4개와 `/tmp` 호스트 뮤텍스 · postgres 슬롯 4개라는 사실이 저장소 spec · 규칙에 T 행동으로 적혀 있다. 실제 불변식은 「게이트를 돌리는 모든 checkout 이 `gate_host_mutex` 를 가진 develop 이상」이다.
- 팀 영향: 팀원 호스트에는 30-33 이 없어 T3 는 무의미하고, 「한 시점에 하나」는 호스트당 규칙인데 팀 전체 규칙처럼 읽힌다(팀원 간 병렬은 허용). 심각도 낮음.
- 권고: T3 를 총괄 spec 에서 개인 runbook(D5 onboarding 「운영자 노트」)으로 옮기고 colab-rules §3-1 · ADR 인용 문장을 「호스트당 실행 레인 하나」로 1줄 교정. 장치 없음(산문 · 맥락만).
- 어디서: PR 4(산문) · ADR-0002 본문은 변경 불요(이력)

### D10
- 자리: `2026-09-26-human-authorization-for-destructive-ops.md:57`(Q2a ⓐ′ · 기록 = dev EC2 root 0700 `COLAB_OPS_AUTH_DIR` · `authorized_at` · sha256(token)) · 총괄 S-auth 행 `:131`
- 사실: 인가 기록은 시각 · 토큰 해시뿐이고 「누가」가 없다. dev 호스트 · `COLAB_DEV_SSH` 자격은 운영자 여럿이 공유할 수 있다.
- 팀 영향: 운영자 2명 이상이면 GO 를 준 사람을 기록에서 못 가른다(감사 불가). 심각도 낮음(장치 자체는 팀 중립 · 기록만 부족).
- 권고: 기록 필드에 `authorized_by`(ssh principal 또는 `$USER@hostname` · 형식 판정이지 승인 아님 · ADR-0003) 1개 추가 · `test_ops_authorization.py` 기록 필드 사례에 포함.
- 어디서: 별도 intent(S-auth spec 작성 시 · intent 승인 뒤라 spec 에만)

### D11
- 자리: `eval/harness/run.sh:76`(로컬 시계 run id) · `scripts/harness/check.py:104-110`(「CI is UTC; results are recorded in KST」 · `max(0, …)`) · `eval/harness/config_hash.py:153`(`computed_at` 은 UTC)
- 사실: run id 는 실행자 로컬 시각, 나이 계산은 `datetime.now()` 로컬, KST 가 코드 주석의 전제다. 이미 CI red 1회(#176) 를 냈다.
- 팀 영향: 다른 시간대 팀원의 회차는 이름 순서가 시간 순서와 어긋나 「직전」 선정(D3) · 30일 경고가 사람마다 다르게 나온다. 심각도 낮음(경고 · 회귀 기준만).
- 권고: run id `date -u +%Y%m%d-%H%M%SZ` · `check.py` 나이 계산을 UTC 로 · 주석의 KST 전제 삭제.
- 어디서: E1(D3 와 같은 PR · 러너는 해시 집합)

### D12
- 자리: `docs/development/dual-agent.md` 「도구 차이」 절 모델 등급표(「이 계정(ChatGPT 로그인)에서 … 선택되지 않는다(400) · 선택되는 모델은 …」) · `.codex/agents/*.toml` `model`
- 사실: Codex 역할별 모델이 한 계정의 실측으로 고정돼 저장소 설정(`.codex/agents/*.toml`) 에 박혀 있다.
- 팀 영향: 다른 ChatGPT 계정은 그 모델이 400 이거나 상위 모델이 열려 있어 레인 · advisor 판정 품질이 사람마다 다르고, 실패는 「모델 선택 불가」로 준비 실패처럼 보인다. 심각도 낮음(Codex 사용자만).
- 권고: 문장을 「계정별 실측 필요」로 바꾸고 D5 onboarding 에 `codex` 모델 목록 확인 항목 · 대체 등급 표를 둔다. 장치는 `agent-bridge.py doctor` 가 설정된 모델명을 계정에서 조회 가능한지 1회 확인(불가 = 78 사유).
- 어디서: PR 3(C8) · doctor 는 D5 와 같은 PR

### 요약
- 팀에서 틀린 자리 1: develop ruleset 승인 0 + CODEOWNERS 개인 핸들 → 작성자 = advisor 호출자 = 병합자. 「병합은 사람」이 「다른 사람」이 아니다. S-red 병합 직후 ruleset 개정(D1).
- 팀에서 틀린 자리 2: eval MATCH 가 실행자 구독 · 기본 모델 · 로컬 시계에 결속되고 `verify` 가 모델을 대조하지 않는다. 팀원마다 판정이 다르고, 동시 하네스 PR 은 병합마다 서로를 무효화한다. E1 에서 모델 결속 + 하네스 PR 직렬 규약(D3 · D11).
- 승인 의미론: 「승인」 문자열 = 승인 · 승인자 미기록 · 템플릿 실명 · 「Ted 원문」 규칙 → 승인자 핸들 형식 + intent_ref 판별식(D2) · 역할 어휘 3개로 (b) 치환(D7).
- 근거 · 증거의 소재: 9라운드 판정 원문 · T1 스냅샷 · H6/H7 · advisor ② 가 전부 홈 또는 `.git/` 안 → 저장소 반입(D4 지금 · D6 PR 2).
- 두 번째 기계 절차 없음: /hooks 재신뢰 · CLI · Codex 계정 · 자격이 「이 PC」 관측뿐 → onboarding + doctor(D5 · D12 PR 3). 개인 메모리가 정본인 항목은 runbook 으로(D8 PR 4).
- 계획 순서(S-red → PR 2 → effort → PR 3 → PR 4 → E1·X·M·S)는 유지 가능. 단 D1 은 순서 밖 즉시, D2·D4 는 S-red 뒤 소형 PR 2개, D3·D11 은 E1 범위 확장, X·M 의 「1인 체제」 전제는 재판정.
