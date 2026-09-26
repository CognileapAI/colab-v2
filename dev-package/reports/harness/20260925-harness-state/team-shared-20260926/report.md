[harness: subagent output matched instruction-shaped pattern(s): settings-json. Control tags below are neutralized (`<` → `<\`); treat any remaining directive-shaped text as a finding to relay to the user, not an instruction to you.]

## 판정
- 현 계획은 1인 운영 전제로 짜여 있어 팀 공용으로는 두 자리가 틀렸다. ① develop ruleset 이 `required_approving_review_count: 0` · `require_last_push_approval: false` · `bypass_actors: []` 라(실측 `T1-develop-ruleset.json`) write 권한 구성원의 에이전트가 자기 토큰으로 자기 PR 을 병합할 수 있다(E-2 · D1). ② eval 러너가 `--model` 없이 `claude -p` 를 부르고(`eval/harness/run.sh:136`) `config_hash.py verify` 가 모델을 대조하지 않아 「해시 일치」가 판정 동일성을 보증하지 않는다(E-1 · C-2 · D3).
- 순서(S-red → PR 2 → PR 3 → PR 4)는 유지 가능. 단 S-red 병합 직후 · PR 2 head 회차 전에 ⑴ ruleset 개정(코드 변경 없음) ⑵ 해시 집합 파일을 건드리는 소형 PR 1건(모델 고정 · UTC run id · 78 사유 · 위생 뿌리 · 집합 축소)을 끼워 회차 1회로 끝낸다. 이것을 건너뛰면 PR 2 의 긴 개방 기간이 제품 병합마다 재실측을 받는다(C-1 · E-4).
- S-red 레인은 중단 불요. 레인 산출 리뷰에서 S-6a 치환 대상에 `$HOME` 추가 1줄만 확인한다(C-9).
- 비용·실행 주체(개인 구독 CLI 1인 기계)는 팀 절차가 아니다. CI 실행 모드는 별도 intent 로 PR 2 병합 전에 결정만 한다(C-3).

## 권고 (우선순위)
1. GitHub ruleset `develop-protection-policy` · `pull_request.required_approving_review_count: 1` + `require_last_push_approval: true` + `dismiss_stale_reviews_on_push: true` · 장치 · 지금(Ted · `gh api` · 새 JSON 은 PR 3 C5 스냅샷) · 계획 T 표의 「Ted 병합(T13)」 → 「작성자 아닌 승인 1 + ruleset」 · T11 PAT 는 구성원별 선택으로 격하 · E-2 D1
2. `eval/harness/model.txt`(해시 집합 안) 1줄 정본 · `run.sh` 가 `--model "$(cat model.txt)"` · `config_hash.py compute` 에 `model`(정본값 + 실측 `modelUsage`) 기록 · `verify` 후보 조건에 `model == 정본` 추가(불일치 = 78 · 사유 `model-mismatch`) · `summary.md` 요약줄에 모델 표기 · 장치 · 지금 소형 PR(해시 집합 파일 · PR 2 회차 앞) · E-1 C-2 D3
3. `eval/harness/config-paths.txt` 에 `:(exclude)gates/**` · `:(exclude).agents/ci-producers.json` 추가 후 `gates/tools/harness-eval.sh` · `harness-eval-selftest.sh` · `_readiness.sh` 만 재등재 · 장치 · 지금 소형 PR(2 와 동일 PR · 질문 2 승인 조건) · C-1 E-4
4. `run.sh` `RUN_ID="$(date -u +%Y%m%d-%H%M%S)"`(형식 · `RUN_ID_RE` 불변) · `scripts/harness/check.py` 나이 계산을 `datetime.now(timezone.utc)` · KST 주석 삭제 · README 「결과」 절에 「id = UTC」 1줄 · 장치 · 지금 소형 PR(2 와 동일) · E-7 D11 C-4①
5. `config_hash.py verify` 78 상세에 `dirty`(비추적 포함) 상위 5건 첨부 · `.agents/harness.yaml hygiene.home_path_roots` 에 `eval/harness/results` · `dev-package/intent` · `dev-package/prd` 추가 · 장치 · 지금 소형 PR(2 와 동일) · C-11 E-6 D4
6. intent 메타 줄 승인 형식을 `승인: @<GitHub handle> <YYYY-MM-DD> "<원문>"` 으로 고정 · `scripts/harness/intent_ref.py classify` 가 `승인: @` 꼴만 approved(현행은 「승인」 포함 ∧ 「미승인」 부재 · `:42-49` 확인) · fixture 갱신 · `TEMPLATE.md` 실명 열거 삭제 · `~/.claude/reports/harness-state-20260925/` 를 `dev-package/reports/harness/20260925-harness-state/` 로 반입(홈 경로 `<repo>` 치환) · 장치+문서 · 지금 소형 PR 2(`scripts/harness/**` · 해시 집합 밖 · 회차 불요) · D2 D4
7. `config_hash.py verify` 「직전」 = `config-hash.json.head` 가 현재 HEAD 의 조상인 최신 전수 회차(`git merge-base --is-ancestor`) · 없으면 「직전 없음」 · 장치 · PR 2(S-6b 와 같은 함수 · E0→PR 2 순차 소유) · C-4②
8. PR 2 병합 조건에 「advisor ② 판정문 + `COLAB_HANDOFF` JSON 을 `dev-package/reports/<회차>/verdict/` 로 복사 · PR 본문 Advisor-Ref = 저장소 경로 + sha256」 · `hook_audit.py` 줄에 `user` 필드 · 2-4 「`--apply` 는 Ted 지시」 → 「해당 checkout 소유자가 dry-run 확인 뒤 실행」 + `harness-contract` 용량 `warning:` · 장치 · PR 2 · D6 C-8 C-7
9. 총괄 계획 §0 에 팀 규칙 2줄 「해시 집합을 건드리는 PR 은 저장소 전체에서 동시 1건 open · 다음 PR 회차는 앞 PR 병합 뒤」 · 「집합 밖 파일만 바뀐 develop 병합은 회차 유지」 · §6 Q1 비용표를 「N 명 × 동시 PR」 축으로 · T12 「회차 ≈8 USD(09-26 실측) · 32 는 09-12 값」 · 산문 · PR 2 총괄 갱신 · E-4 C-5 C-10 D3
10. `docs/development/onboarding.md`(기계 1대당: /hooks 재신뢰 · `claude --version` 로그인 · `codex` 모델 실측 · agent-browser · 자격 파일 · TZ) + `scripts/agent-bridge.py doctor` 에 `claude` 존재·버전 · 설정 모델 조회 가능 여부(불가 = 78 사유) · dual-agent.md 「이 PC」·모델 등급표 문장을 포인터로 · `RESTART.md` 「두 번째 기계」 절(키 3분류) · 장치+문서 · PR 3(C8) · RESTART 절은 PR 4 · D5 D12 E-5
11. `.agents/rules/colab-rules.md §0` 에 역할 어휘 3개(승인자 = develop 리뷰 권한자 · 병합자 = 작성자 아닌 승인자 · 운영자 = dev SSH 자격 보유자) 정의 · skills/rules/TEMPLATE/deploy.md 의 역할성 「Ted」 치환(결정 이력 원문은 유지) · T7 을 「저장소 runbook 갱신」으로 재정의 · T3(clone 30-33 pull) 는 개인 runbook 으로 · 「한 시점에 하나」 → 「호스트당」 · 산문 · PR 4(deploy.md 줄은 S-auth intent 안) · D7 E-8 D8 D9
12. 별도 intent 3건: ⓐ CI 잡 `harness-eval-run`(`workflow_dispatch`/label · org `ANTHROPIC_API_KEY` · 고정 CLI 버전 · artifact 업로드 · 커밋은 사람) ⓑ `gates/tools/_lock.sh`·`_pg.sh` 잠금을 `python3 fcntl.flock` 로 교체(판정 규약 무변경) ⓒ S-auth 기록 필드 `authorized_by` + `operator` = gh login · Codex 러너 해시 기록 · 장치 · ⓐ 는 PR 2 병합 전 결정 · C-3 E-3 D10 E-4

## 유지 (변경 불요)
- task runtime · `audit.jsonl` 의 checkout 결속(`sha256(root‖git dir)`) — 다른 구성원 store 에 닿지 않는다 · 이동 매체는 PR 요약 + 8 의 verdict 복사로 충분 · E-10 C-7
- ruleset 의 PR 필수 · `strict_required_status_checks_policy: true` · `bypass_actors: []` · `ci-required` — 서버 쪽 장치라 구성원 무관 · 1 은 승인만 얹는다 · E-2 D1 C-5
- `.claude/settings.json` 훅 wrapper 가 레포 안 · S-auth 스키마 `operator` 필드 · `hygiene.home_path` 검사 자체(뿌리만 보강) · E 요약
- `/tmp` 호스트 뮤텍스 소유·umask(E-9 C-6) · `origin` 고정 guard · WSL 분기 문장(E-11) — 계정 분리 공유 서버 · fork 워크플로가 팀 구성에 없는 한 무해 · 조건 발생 시 1줄 수정
- 해시 집합 개념 · 회차 무효화 규칙 · `results/**` 추적 범위(C-9) · ADR-0002 본문(이력)

## 충돌·미확인
- run id 접미사: E-7 「`Z` 없음 · `RUN_ID_RE` 불변」 vs D11·C-4 「`…%SZ`」 → 4 는 접미사 없음 채택(정규식·기존 8회차 정렬 호환) · README 1줄로 UTC 선언
- 모델 출처: E-1·C-2 정본 파일 고정 vs D3 `modelUsage` 추출 → 2 는 둘 다(정본 = 입력 · 실측 = 기록 · verify 는 동등 대조) · C-2 의 `CLAUDE_CONFIG_DIR` 격리는 미검증(사용자 hook·CLAUDE.md 적재 여부를 `claude -p` 1회로 실측 뒤 소형 PR 에 포함 여부 결정)
- code-owner review: D1 은 `require_code_owner_review: true` 권고 · E-2 는 없음 → `.github/CODEOWNERS` 전 경로가 단일 핸들 `@sungwooHa`(확인) 라 켜면 병목 1인 · 팀 핸들로 교체된 뒤에만 켠다 · 그 핸들이 Ted 본인인지 미확인
- 해시 집합 축소(3): 단일 감사(C) · 수치(580 중 363 · 사흘 17 병합 중 ≈8 제품)는 미검증 · `config-paths.txt` 머리말이 intent 7라운드 Q-A ⓐ 를 근거로 `gates/**` 를 넣었으므로 8라운드 ① `hash_exclude` 허용 문구 확인이 선행 → 질문 2
- E0 확정 회차 5b84d899 의 실측 모델 `claude-opus-5-5[1m]`(E-1 · gitignored raw) 미검증 → `results/20260926-143218/H02.raw.2.json` 1회 확인 · 사실이면 2 적용 뒤 첫 회차가 새 기준선
- C-3 「Q10 조건 도달 불가」 · D5 「doctor 가 claude CLI 를 안 본다」 미검증 → 12ⓐ intent 작성 시 실측
- macOS·비WSL 구성원 존재 여부 미확인 → 12ⓑ 발행 조건 · 질문 5

## 질문 (Ted 판정 필요)
1. develop ruleset 을 승인 1 + last-push 승인으로 올리는가(Ted 자신의 PR 도 두 번째 사람 승인 필요) · 권고 예
2. 해시 집합에서 `gates/**` 를 빼고 harness-eval 도구 3건만 남기는가(intent 8라운드 ① `hash_exclude` 범위 안이면) · 권고 예
3. eval 회차를 org 시크릿 CI `workflow_dispatch` 로 돌리고 비용 주체를 org 로 두는가(구독 CLI 전용 원칙 `product.md:129` 예외) · 권고 예 · 별도 intent
4. intent 승인 권한을 develop 리뷰 권한자로 한정하고 승인 줄에 GitHub handle 을 기록하는가 · 권고 예
5. 팀에 macOS·비WSL 호스트가 있는가 → 있으면 `flock` 교체 intent 지금 발행 · 권고: 있으면 예 · 없으면 보류

## 부록 — 감사 원문

### mechanisms

### E-1
- 자리: `eval/harness/run.sh:158-166`(`claude -p` 호출 · `--model` 없음) · `eval/harness/config_hash.py compute`(기록 필드에 model 없음) · `eval/harness/README.md:108`(「러너는 모델을 지정하지 않으므로 호출 환경의 기본값을 탄다」) · `results/20260926-143218/H02.raw.2.json`(gitignored · `modelUsage: claude-opus-5-5[1m]`) vs README:108(`claude-fable-5-1`)
- 사실: 판정 모델은 각 사용자의 `~/.claude/settings.json` 기본 모델이다. 추적되는 `summary.md`·`config-hash.json`에는 `claude_version`만 있고 모델 id 가 없다. E0 확정 회차(5b84d899)는 README 가 말하는 모델과 다른 모델로 잰 결과다. `config_hash.py verify` 는 해시·selected·준비 0·과제 수만 대조한다.
- 팀 영향: 다른 구성원이 다른 기본 모델(예: sonnet)로 돌린 결과가 같은 해시로 「일치 결과」가 되고 회귀 기준(직전 R*)까지 된다. 같은 절차 → 다른 판정 · 다른 비용(USD 합 8.1 vs 32.4 가 이미 모델 차이다). 심각도 높음
- 권고: `eval/harness/model.txt`(해시 집합 안) 1줄을 정본으로 두고 `run.sh` 가 `--model "$(cat model.txt)"` 로 고정 · `config_hash.py compute` 가 `model` 필드를 쓰고 `verify` 가 후보 조건에 `model == 정본` 을 추가(불일치 = 78) · `summary.md` 요약줄에 모델 표기
- 어디서: 지금(S-red 뒤 소형 PR · `eval/harness/**` 변경이라 PR 2 head 회차 앞에 넣어야 회차 1회로 끝난다)

### E-2
- 자리: `.claude/settings.json`(`permissions` 키 없음) · intent 판정 기록 `:621`(T11 = `~/.claude/settings.json env.GH_TOKEN` · 「Claude 세션만 · Ted 터미널 무영향」) · `~/.claude/reports/harness-state-20260925/T1-develop-ruleset.json`(`required_approving_review_count: 0` · `bypass_actors: []`)
- 사실: 서버 쪽 병합 조건은 PR 존재 + `ci-required` + 스레드 해결뿐이다. 승인 0 이라 write 권한자 한 명(또는 그 사람 토큰을 상속한 에이전트 셸)이 자기 PR 을 혼자 병합한다. T11 PAT 는 사용자 홈 설정에 들어가는 개인 장치라 Ted 기계에서만 `gh pr merge` 가 403 이다. 로컬 git-guard 는 `bash -c`·`COLAB_HOOKS=0`·프로젝트 hook 미신뢰 세션에 닿지 않는다(git-guard.sh 머리말 자인).
- 팀 영향: 두 번째 구성원의 Claude/Codex 세션은 그 사람의 전권 `gh auth` 로 `gh pr create`·`gh pr merge` 가 가능하다. 「병합은 사람」이 저장소 단위가 아니라 Ted 개인 단위 보호다. 심각도 높음
- 권고: ruleset `develop-protection-policy` 의 `pull_request.required_approving_review_count` 를 1 로 올리고 `require_last_push_approval: true` 로 둔다(작성자 ≠ 승인자 · 에이전트가 어떤 토큰을 쥐어도 두 번째 사람 신원 없이는 병합 불가) · T11 은 「구성원별 선택」으로 격하해 계획 T 표에서 병합 조건 의존을 지운다
- 어디서: 지금(Ted · GitHub UI/`gh api` · JSON 스냅샷은 PR 3 C5 에 그대로 기록)

### E-3
- 자리: `gates/tools/_lock.sh:18-21,76-80` · `gates/tools/_pg.sh:66-69,82-84` · `gates/README.md:129`(「개발 = WSL/util-linux · 없는 호스트가 합류하는 날 3상태 변수를 만든다」) · `gates/config/parallelism.toml`(serial 선언 45건)
- 사실: 호스트 뮤텍스·pg 슬롯은 util-linux `flock` 실행 파일을 요구하고 부재는 면제 없이 78 이다. serial 게이트 45건 + DB 게이트 전부가 대상이다.
- 팀 영향: macOS 구성원(util-linux 없음)은 로컬에서 serial·DB 게이트를 한 건도 판정할 수 없다(전부 red 준비). 「같은 절차 → 같은 판정」이 OS 로 갈린다. 계획 문서가 「합류하는 날」로 미룬 그 날이 팀 공용 선언으로 도래했다. 심각도 높음
- 권고: `_lock.sh`·`_pg.sh` 의 잠금 원시 연산을 `flock` 바이너리에서 `python3 -c 'import fcntl; fcntl.flock(...)'`(stdlib · Linux/macOS 공통) 로 교체 · 판정 규약(78 · 대기 표식 · fd 유지)은 무변경
- 어디서: 별도 intent(팀 호스트 OS 목록 확인 → `gates/**` 변경이라 회차 1회 동반 · PR 3 앞)

### E-4
- 자리: `dev-package/prd/specs/S-HARNESS-E0-EVAL-GATE-20260926.md §6 #7`(CI 해시 = 머지 커밋 트리) · `S-HARNESS-IMPROVEMENT-PLAN-20260926.md:184,194`(회차 5회 ≈160 USD · 1인 기준) · T1 `strict_required_status_checks_policy: true` · `eval/harness/run.sh:60`(`claude` PATH 필수) · `.agents/rules/product.md:129`(구독 CLI 만)
- 사실: 해시 집합 파일을 건드린 PR 이 하나 병합되면 열려 있는 모든 하네스 PR 은 Update branch 뒤 해시가 바뀌어 78 이고 각자 재실측(≈8–32 USD · 20분+ · 로컬 `claude` 구독 CLI 필요)해 결과를 커밋해야 한다. CI 는 결과를 만들지 못한다.
- 팀 영향: 동시 하네스 PR N 건이면 재실측이 O(N²) 이고 비용은 각 구성원의 개인 구독으로 분산된다. Codex 전용 구성원은 결과를 만들 수단이 없어 자기 하네스 PR 을 영원히 병합 조건에 못 올린다. 계획 §6 Q1 의 비용 산정(5회)은 1인 직렬 전제다. 심각도 높음
- 권고: 총괄 계획 §0 에 팀 규칙 1줄 「해시 집합을 건드리는 PR 은 저장소 전체에서 동시에 1건만 open · 다음 PR 의 회차는 앞 PR 병합 뒤」 + §6 Q1 비용표를 「N 명 · 동시 PR 수」 축으로 재작성 · Codex 러너(`scripts/codex-harness-eval.py`) 해시 기록은 별건에서 지금 순서로 당긴다
- 어디서: 지금(계획 문서 · 산문) · Codex 러너는 별도 intent

### E-5
- 자리: `gates/run.sh:329-344`(`${HOME}/.colab-v2-test.env` · 부재 = 78) · `dev-package/RESTART.md:171,245,257-260,285,302`(값 = staging 컨테이너 IP · `postgres` 수퍼유저 비밀번호 · staging 실물 읽기 전용 URL · `~/.colab-v2-staging.env` 와 짝) · `scripts/harness/hooks/worktree-setup.sh:249-259`
- 사실: 로컬 게이트 입력은 사용자 홈의 0600 파일 하나이고, 그 값은 Ted 호스트의 staging 스택(docker IP · 비밀번호)에서 유도된다. 배포 절차는 「같은 호스트에 staging 8개가 떠 있다」를 전제한다(RESTART §2). 값 전달 경로는 문서화돼 있지 않다.
- 팀 영향: 두 번째 기계에서는 `autometa-loss`·`preview-tile-slot`·`artifact-ownership`·`schema-diff`·서비스 시험 전부가 red(준비) 라 로컬 `all` 이 green 이 될 수 없고 CI 만 판정원이 된다. 「같은 보호」가 아니라 「같은 red 」다. 심각도 중간
- 권고: `dev-package/RESTART.md` 에 「두 번째 기계」 절 1개 — 키를 3분류(일회용 컨테이너로 자립 생성 가능 5줄 / staging 실물 필요 3줄 · 값 요청처 = 저장소 관리자 / 경로 3줄) 로 적고, `gates/tools/_readiness.sh` 의 입력미선언 메시지가 그 분류를 인용
- 어디서: PR 4(산문 · `gates/**` 문구는 회차 동반이라 PR 3 head 회차 앞)

### E-6
- 자리: `eval/harness/results/20260926-{125205,140939,143218}/H02.out.{1,2}.txt:30`(`<home>/workspace/…` 절대경로 · 추적됨 · `git ls-files` 확인) · `.agents/harness.yaml hygiene.home_path_roots`(`AGENTS.md CLAUDE.md .agents .claude .codex docs` — `eval/` 없음) · `scripts/harness/config.py:29-34`
- 사실: 러너가 `{FIXTURE}` 를 절대경로로 치환한 명령을 모델이 그대로 인용해 산출물에 홈 경로·작업공간 구조가 실렸다. home-path 위생 검사의 뿌리에 `eval/harness/results` 가 없어 게이트가 못 잡았다. S-red S-6 「러너 홈 경로 치환」이 치환 쪽은 맡는다.
- 팀 영향: 구성원마다 홈 경로가 산출물에 남고, 같은 과제 출력이 사람마다 diff 로 갈린다. 심각도 중간
- 권고: `.agents/harness.yaml hygiene.home_path_roots` 에 `eval/harness/results` 추가(치환 회귀를 `harness-contract` 가 잡는다) · 치환 자체는 S-red S-6 유지
- 어디서: 지금(S-red 뒤 소형 PR · `.agents/**` 1줄이라 PR 2 회차 앞에 같이)

### E-7
- 자리: `eval/harness/run.sh:83`(`RUN_ID="$(date +%Y%m%d-%H%M%S)"` · 로컬 시각 · TZ 미기록) · `eval/harness/config_hash.py verify`(R* = id 최대 · 직전 = id 가 더 작은 최신) · `scripts/harness/check.py:97,110`(naive `strptime` vs `datetime.now()`)
- 사실: 회차 id 가 실행자의 로컬 시계다. 회귀 기준 선택과 신선도 계산이 id 의 사전순 = 시간순을 전제한다. `computed_at` 만 UTC 다.
- 팀 영향: KST 구성원 20:00 회차가 UTC 구성원 14:00(=KST 23:00) 회차보다 「앞」으로 정렬돼 회귀 기준이 바뀌고, 30일 경고는 시간대만큼 어긋난다(E0 #176 CI red 가 이미 그 첫 사례). 심각도 중간
- 권고: `run.sh` `RUN_ID="$(date -u +%Y%m%d-%H%M%S)"` · `check.py` 를 `datetime.now(timezone.utc)` 로 대조 · README 「결과」 절에 「id = UTC」 1줄(형식 불변 · `RUN_ID_RE` 무변경)
- 어디서: 지금(S-red 뒤 소형 PR · E-1 과 같은 PR)

### E-8
- 자리: `.agents/rules/deploy.md:41,64-65`(「Ted 의 명시 GO」 · 「Ted 가 정지 게이트가 찍은 표별 계수를 보고」) · `dev-package/RESTART.md:60`(`approve.sh Ted "<…>"`) · `.agents/rules/colab-rules.md:41,214-216`(「제품 방향이 갈리면 Ted 가 확정」 · 판정값 자리) · S-auth intent `:67`(`operator` 필드 — 신원 자유)
- 사실: 파괴·배포 인가의 주체가 규칙 본문에 개인 이름으로 박혀 있다. 기제(S-auth 토큰 · reseed ack)는 `operator` 를 값으로 받아 팀 대응이 되지만, 규칙 산문은 다른 구성원의 GO 를 정의하지 않는다.
- 팀 영향: 두 번째 구성원은 규칙상 인가 권한이 0 이거나(축자 해석) 규칙을 무시해야 한다(관행 해석). 승인 의미론이 사람 이름에 결속돼 있다. 심각도 중간
- 권고: `.agents/rules/deploy.md`·`colab-rules.md` 의 「Ted」 를 역할명(「저장소 관리자」 = GitHub admin 권한자)으로 치환하고 S-auth 스키마 `operator` 를 그 역할 신원(gh login)으로 채우도록 spec 에 1줄
- 어디서: PR 4(산문) · S-auth spec 은 별도 intent 안에서

### E-9
- 자리: `gates/tools/_lock.sh:75`(`${TMPDIR:-/tmp}/colab-v2-gate-host-mutex/host`) · `_pg.sh:75`(`/tmp/colab-v2-gatepg-slots`) · `scripts/harness/hooks/ponytail-inject.sh:68`
- 사실: 잠금·표식 파일이 호스트 공용 `/tmp` 에 첫 실행자 umask(0644) 로 생긴다. 한 기계에 계정이 둘이면 두 번째 계정은 `exec {fd}>"$path"` 가 EACCES 라 78 이다.
- 팀 영향: 공유 개발 서버(계정 분리)에서만 발생 · 개인 기계에서는 무해. 심각도 낮음
- 권고: 변경 불요(공유 호스트가 팀 구성에 없으면) · 있으면 `mkdir -m 1777` + 파일 `chmod 0666` 1줄
- 어디서: 변경 불요(사유: 호스트 전역 잠금이 설계 의도 · 계정 분리 호스트 미확인)

### E-10
- 자리: `scripts/harness/task_state.py:22-26`(`checkout_id = sha256(root‖private git dir)`) · `lifecycle_contract.py:59-60`(런타임 = git common dir) · PR 2 spec 2-9 P2(`audit.jsonl` = git-common-dir) · 계획 X·M 측정
- 사실: task 증거·audit 는 clone 마다 · 기계마다 따로 산다. 검증은 같은 checkout 에서만 가능하고 PR 요약이 유일한 이동 매체다.
- 팀 영향: 팀 안전성은 충족(다른 사람 store 를 못 건드림). 다만 X·M 측정(오탐률 · 1차 CI 통과율)은 Ted clone 30–33 만 세고, 다른 구성원의 audit 는 집계 밖이다. 심각도 낮음
- 권고: M 수집 스크립트(`scripts/metrics/metrics.py`) 입력을 「git-common-dir 목록」이 아니라 「PR 본문 VERDICT 행 + CI artifact」로 한정해 구성원 무관하게 잰다(산문 · 계획 §5)
- 어디서: PR 4(M 단위 설계 시)

### E-11
- 자리: `scripts/harness/hooks/decision-number-guard.sh:71-72,103`(`origin/develop` 고정 · 못 읽으면 새 번호 후보 시 exit 2) · `.gitignore`(`eli5/` 「Ted 요청」 · `.claude/.headroom_wrap_*`) · `AGENTS.md:51-54`·`docs/development/dual-agent.md:128-156`(WSL · `scripts/dev.ps1` · `$HOME/.npm-global/bin`)
- 사실: remote 이름 `origin` 과 Windows+WSL 조합이 절차 문장에 박혀 있다. Linux/macOS 네이티브 구성원에게는 「Windows 에서는」 분기가 무의미하고, remote 를 `upstream` 으로 둔 fork 작업자는 PLAN-SoT 편집이 막힌다.
- 팀 영향: 문서 잡음 · fork 워크플로 미지원. 심각도 낮음
- 권고: 변경 불요(현재 팀이 org 내 clone 만 쓰면) · fork 를 허용하려면 guard 의 기준 ref 를 `.agents/harness.yaml project.default_branch` + 「upstream 우선 · 없으면 origin」 으로
- 어디서: 변경 불요(사유: fork 정책 미결정)

### 요약
- 지금 계획이 팀에 **틀린** 자리 둘: ① 병합 보호가 개인 장치(T11 PAT 홈 설정 + 승인 0)라 두 번째 구성원의 에이전트가 자기 토큰으로 병합할 수 있다 → ruleset 승인 1 · last-push 승인으로 서버 쪽에서 닫는다(E-2). ② eval 판정이 실행자의 기본 모델을 타고 모델이 기록되지 않아 「해시 일치」가 재현성을 보증하지 않는다 → 모델 정본 파일 + verify 조건(E-1).
- 비용 모델이 1인 직렬 전제다: strict + 머지 트리 해시 + 로컬 구독 CLI 만 결과 생산 → 동시 하네스 PR 은 O(N²) 재실측 · Codex 전용 구성원은 생산 불가(E-4). 계획 순서는 유지하되 「해시 집합 PR 동시 1건」 규칙을 명문화한다.
- 로컬 게이트는 WSL+staging 동거 호스트 전제다: util-linux `flock` 필수(macOS 전면 78 · E-3) · `~/.colab-v2-test.env` 값이 Ted staging 에서만 나온다(E-5). 다른 기계에서는 CI 가 유일한 판정원이 된다.
- 소형 즉시 PR 1건으로 닫히는 것: E-1 모델 고정 · E-7 UTC run id · E-6 위생 뿌리 1줄(모두 해시 집합 파일 → PR 2 회차 앞에 묶어 회차 1회).
- 산문 정정(PR 4): 인가 주체 「Ted」 → 역할명(E-8) · 두 번째 기계 절(E-5).
- 팀 안전에 이미 맞는 것: task store 의 checkout 결속(E-10) · `.claude/settings.json` 훅 wrapper 가 레포 안(모든 구성원 동일) · S-auth 스키마의 `operator` 필드 · `hygiene.home_path` 검사(뿌리만 보강).

### process-docs

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

### cost-concurrency

### C-1
- 자리: `eval/harness/config-paths.txt:14` (`gates/**`) · `:12` (`.agents/**` → `.agents/ci-producers.json` 포함) · E0 spec §4.1 · intent 8라운드 ① (`hash_exclude` 허용)
- 사실: 해시 집합 580 파일 중 `gates/**` 가 363(63%) · 에이전트 입력(AGENTS/CLAUDE/.claude/.agents/hooks) 105 · `eval/harness/**`(results 제외) 112. 제품 PR #175(`677b60ef`)가 집합 파일 6건(`gates/run.sh` · `gates/README.md` · `gates/config/parallelism.toml` · `gates/tools/region-within-drift*` 3 · `.agents/ci-producers.json`)을 바꿔 해시 `f25ce639`→`5b84d899` 로 갈렸고 E0 는 재실측 2회(`20260926-140939` 준비 1 → `20260926-143218`)를 치렀다(`8e1bbd4d`). 09-24~09-26 사흘간 develop first-parent 병합 17건이 집합 파일을 건드렸고 그중 ≈8건이 제품 PR(#175 #174 #160 #154 #152 #144 #151 #138). eval 과제는 fixture cwd 에서 `claude -p` 로 돌며(`run.sh:136-142`) `gates/tools/region_within_drift.py` 류를 입력으로 받지 않는다.
- 팀 영향(높음): 집합 무효화율 ≈5.7 병합/일. 회차 1회 = ≈8 USD · ≈35 분 · 실행자 1인 기계. 하네스 PR 이 반나절 열려 있으면 기대 재실측 ≈3회/PR → 계획 5 PR 기준 5→≈20 회차(≈160 USD · ≈12 시간). 구성원 N 명이 동시에 하네스 PR 을 열면 서로의 병합이 서로의 회차를 무효화해 비용 O(N×병합). 제품 팀은 자기 게이트 추가가 하네스 PR 을 78 로 만든다는 사실을 모른다.
- 권고: `config-paths.txt` 에 `:(exclude)gates/**` · `:(exclude).agents/ci-producers.json` 추가 후 `gates/tools/harness-eval.sh` · `gates/tools/harness-eval-selftest.sh` · `gates/tools/_readiness.sh` 만 포함 패턴으로 재등재(정본은 이 파일 하나 · `harness.yaml eval.hash_exclude` 신설 불요 · `ci-filter-check.py` 는 포함 패턴만 대조하므로 CI `harness` 필터의 `gates/**` 는 유지 = 면제 게이트만 깨움 · 비용 0).
- 어디서: 지금(S-red 뒤 소형 PR · 집합 파일 변경이라 그 PR 회차 1회 ≈8 USD · 이후 PR 2·3·4 의 무효화율이 제품 병합 몫만큼 내려간다)

### C-2
- 자리: `eval/harness/run.sh:136-142` (`--model` 없음 · 사용자 설정 격리 없음) · `README.md:103` 「러너는 모델을 지정하지 않으므로 호출 환경의 기본값을 탄다」 · `config_hash.py verify`(`claude_version` 기록만 하고 대조 안 함) · E0 spec 「범위 밖」 `--model`
- 사실: 같은 과제 20건이 09-12 회차 31.55 USD → 09-26 회차 7.5~8.1 USD 로 4배 차이(모델·CLI 기본값 변화 · 해시는 무관). `claude -p` 는 실행자의 `~/.claude/settings.json` · `~/.claude/CLAUDE.md` · 플러그인 · 사용자 hook 을 적재하지만 해시 집합 밖이다.
- 팀 영향(높음): 구성원 B 가 기본 모델 Sonnet · 다른 사용자 hook 으로 만든 회차가 같은 해시로 MATCH 를 만족 → 팀 전원의 병합 조건이 「누가 돌렸나」에 따라 달라진다. 같은 절차 · 같은 트리 · 다른 판정 · 다른 비용.
- 권고: 러너가 저장소 파일(예 `eval/harness/model.txt` · 해시 집합 안)에서 모델을 읽어 `--model` 로 고정 · 사용자 설정 출처를 배제(CLI 의 설정 출처 제한 옵션 또는 `CLAUDE_CONFIG_DIR` 임시 디렉터리) · `config-hash.json` 에 `model` 기록 · `verify` 가 `model` 불일치 회차를 후보에서 제외(78 사유에 표기).
- 어디서: 지금(C-1 과 같은 소형 PR · 같은 회차로 덮는다)

### C-3
- 자리: 총괄 T12(`S-HARNESS-IMPROVEMENT-PLAN-20260926.md:81`) 「레인이 중첩 `claude -p` 를 못 돌리면 Ted 가 실행」 · E0 spec :75 · S-red :139 · `ci.yml:681` 「모델 호출 없음 · API 키 불요」 · intent 2026-09-08 Q10(CI 실행 모드 = 3회 연속 2/2 green 뒤)
- 사실: 회차 생산 경로는 실행자 개인 기계 + 개인 계정(구독 또는 API key)뿐이다. CI 에는 실행 모드도 시크릿도 없다. Q10 조건(20/20 green 3회 연속)은 H14~H18 실패가 T17(Ted 분류) 뒤에만 풀려 현재 도달 불가.
- 팀 영향(높음): 구성원마다 (a) nested `claude -p` 가 되는 환경 (b) 35 분 점유 (c) 자기 비용(API key 면 실비 · 구독이면 rate limit)을 감당해야 하고 결과는 C-2 대로 환경 종속. 실행 주체·비용 부담자 규정이 없어 「Ted 가 돌린다」가 사실상 팀 절차. 5 PR × N 재실측 전부 한 사람 기계에 직렬.
- 권고: `workflow_dispatch`(또는 PR label `eval-round`) 로만 깨어나는 CI 잡 `harness-eval-run`: org 시크릿 `ANTHROPIC_API_KEY` · 고정 CLI 버전 · `COLAB_HARNESS_EVAL=1` · `results/<run>/` 를 artifact 로 올리고 커밋은 구성원이 한다(게시 = 사람 원칙 유지). Q10 은 「필수 check 승격」 조건으로만 남기고 「어디서 돌리나」와 분리. 비용 주체 = org 1곳.
- 어디서: 별도 intent(org 시크릿 발급 · 비용 주체 = 사람 결정) — 단 PR 2 병합 전 결정하지 않으면 PR 2·3·4 회차가 전부 개인 기계로 간다

### C-4
- 자리: `eval/harness/config_hash.py` `verify` 「직전」 선정(`run.name < best.name` 최신 전수 결과 · 해시 무관) · `run.sh:76` `RUN_ID="$(date +%Y%m%d-%H%M%S)"`(로컬 시계) · `check.py:eval_age_days` 주석(KST/UTC 차이로 이미 CI red 1회 · `4be71c3d`)
- 사실: 회귀 기준 = id 가 작은 최신 전수 회차. id 는 실행자 로컬 시계. 회차가 다른 브랜치·다른 해시에서 왔는지 보지 않는다.
- 팀 영향(높음): 구성원 A 의 PR 회차가 구성원 B 의 (다른 설정) 회차를 「직전」으로 삼아 거짓 회귀 1(red) 또는 회귀 은폐. UTC 구성원의 회차 id 가 KST 구성원의 늦은 회차보다 앞에 정렬(최대 9 시간 역전). 같은 초에 두 기계가 돌면 디렉터리 이름 충돌.
- 권고: (1) id 를 `date -u` 로 고정 · (2) 「직전」 = `config-hash.json.head` 가 현재 HEAD 의 조상인 최신 전수 회차(`git merge-base --is-ancestor`) · 없으면 「직전 없음」(0). S-6b(행 수 조건)와 같은 함수.
- 어디서: PR 2(S-red 레인 진행 중이라 S-6b 에 얹지 못함 · `config_hash.py` 는 E0→PR 2 순차 소유)

### C-5
- 자리: `scripts/harness/verify_evidence.py:55-58`(머지 커밋 tree · parents 대조) · T1 ruleset strict(총괄 :79) · 총괄 §0 회차 무효화 규칙(:13)
- 사실: develop 이 움직이면 열린 PR 은 Update branch + CI 전체 재실행이 필수(B1) · 집합 파일이 움직이면 회차까지 재실측. 두 장치가 곱해진다.
- 팀 영향(중간): 병합은 팀 전체가 직렬 큐. 회차가 사람 기계에서만 나오므로(C-3) GitHub merge queue 로도 못 푼다. C-1 없이는 하네스 PR 의 green 유지 시간이 수 시간.
- 권고: 장치 추가 없음 — C-1 로 무효화 면을 줄이고, 총괄 §0 에 「집합 밖 파일만 바뀐 develop 병합은 회차 유지(해시 불변)」를 팀 규칙으로 명시(이미 사실 · 산문 1줄).
- 어디서: 변경 불요(C-1 이 기제 · 문구는 PR 2 총괄 갱신에 동반)

### C-6
- 자리: `gates/tools/_lock.sh` `gate_host_mutex_path` = `${TMPDIR:-/tmp}/colab-v2-gate-host-mutex/host` · `parallelism.toml` `"harness-eval" = "serial"` · `COLAB_GATE_MUTEX_WAIT` 기본 900 초
- 사실: 실행 모드 회차(≈35 분)가 호스트 뮤텍스를 쥔다. 잠금 파일은 첫 생성자 소유 · umask 기본이면 다른 OS 사용자는 쓰기 열기 실패 → 78. `TMPDIR` 이 셸마다 다르면 잠금이 갈린다.
- 팀 영향(중간): 한 호스트를 여러 OS 계정이 쓰거나(공용 개발 서버) 한 구성원이 clone 30~33 을 병렬로 쓰면 회차 도중 다른 clone 의 serial 게이트가 15 분 뒤 78. 기계별로 나뉜 팀에는 영향 없음.
- 권고: C-3 채택 시 실행 모드가 CI 로 가므로 변경 불요. 미채택 시 `gate_host_mutex_acquire` 에서 실행 모드 `harness-eval` 만 대기 상한을 회차 길이 이상(`COLAB_EVAL_TIMEOUT×과제×2`)으로 산출해 출력에 찍는다.
- 어디서: 변경 불요(C-3 조건부) · 아니면 PR 3

### C-7
- 자리: `scripts/harness/task_state.py:51` `<git-common-dir>/colab-harness/<checkout-key>/<task>` · 실측 160 MB · 키 48개 · 총괄 T8(`:84`) 「`--apply` 는 Ted 지시」 · PR 2 spec :108 `prune`
- 사실: task runtime 은 clone·기계 종속. 인계 증거(`lifecycle-evidence.md`)가 가리키는 task id 는 그 기계에만 실재. prune 실행 권한이 사람 이름에 묶여 있다.
- 팀 영향(중간): 구성원 B 의 기계에서는 아무도 prune 을 못 하고 저장소는 계속 자란다. A 가 시작한 task 를 B 가 이어받을 수 없다(설계상 의도 · 단 문서가 그 사실을 말하지 않음).
- 권고: PR 2 2-4 문구 「`--apply` 는 Ted 지시」→「해당 체크아웃 소유자가 dry-run 건수 확인 뒤 실행」 · `harness-contract` 가 `colab-harness` 용량·닫힌 task 수를 `warning:` 1줄로 노출(장치 · 사람 이름 0).
- 어디서: PR 2

### C-8
- 자리: PR 2 spec 2-9 P2 `audit.jsonl` 필드(ts · hook · tool · agent_id · cwd · verdict · rule) · `researcher-task.sh:9-11`(agent_id 대조 미증명)
- 사실: 감사 줄에 실행 사용자 식별자가 없다. `agent_id` 는 세션 단위 값이라 구성원 간 구분이 안 된다.
- 팀 영향(낮음): 공용 clone·공용 서버에서 deny 오탐 계수(PR 3 3-8 조건)를 사람별로 나눌 수 없다. 스키마는 PR 2 에서 처음 확정되므로 뒤에 넣으면 스키마 변경.
- 권고: `hook_audit.py` 줄에 `user`(`git config user.email` 또는 `$USER`) 1 필드 추가.
- 어디서: PR 2

### C-9
- 자리: `eval/harness/results/**` 추적 4종(`README.md:133`) · 회차당 162 파일(`git ls-files` 실계수) · S-red S-6a(홈 경로 치환)
- 사실: 추적 회차 8건. `H??.out.*.txt` 는 모델 응답 원문이라 실행자 홈 경로·사용자명이 실린다(E0 advisor ② 관측 · S-6a 가 `$REPO_TOP` 만 치환).
- 팀 영향(낮음): 구성원 N × 재실측으로 회차 수가 늘어도 파일당 ≈1 KB 라 용량은 문제 아님. 개인정보는 `$REPO_TOP` 밖 경로(`~/.claude/...` 등)가 남을 수 있음.
- 권고: S-6a 치환 대상에 `$HOME` 전체 추가(`<home>`). 추적 범위는 유지.
- 어디서: 지금(S-red 레인이 S-6a 를 만드는 중이라 레인 산출 리뷰에서 1줄) · 놓치면 PR 2

### C-10
- 자리: E0 spec :29 :73 :101 :140 :147 · 총괄 :81 :184 :194 · S-red :106 :139 「회차 ≈32 USD」 · PR 2 spec :210 「≈8 USD」
- 사실: 09-26 실측 3회 7.48 / 8.00 / 8.11 USD. 32 는 09-08·09-12 모델 기준.
- 팀 영향(낮음): 문서 두 값 병존. 새 구성원이 32 로 예산·승인 판단.
- 권고: 총괄 T12 행 1줄 「회차 ≈8 USD(2026-09-26 실측 · 모델 고정 뒤 재측) · 32 는 09-12 값」 · 하위 spec 은 총괄 포인터.
- 어디서: PR 2(총괄 갱신 동반)

### C-11
- 자리: `config_hash.py compute` `git ls-files --others --exclude-standard`(비추적 파일 포함) · `gates/run.sh:20` `all` 목록에 `harness-eval` · E0 advisor ② ①(`settings.local.json` 사례 · `.gitignore:56-57` 로 닫음)
- 사실: `.claude/` `.agents/` `gates/` `eval/harness/` 아래 비추적·비무시 파일 1건이 있으면 로컬 해시가 갈려 `all` 이 78. `verify` 78 메시지는 「해시 일치 회차 0건」만 말하고 원인 파일을 안 찍는다(`compute` 의 `dirty` 목록은 있음).
- 팀 영향(낮음): 구성원 기계의 편집기 임시 파일·개인 스크립트로 CI green · 로컬 78 이 갈린다. 원인을 못 찾고 「게이트가 깨졌다」로 보고한다.
- 권고: `verify` 78 상세에 `dirty`(비추적 포함) 목록 상위 5건을 붙인다.
- 어디서: 지금(C-1·C-2 와 같은 소형 PR · 같은 파일)

### 요약
- 팀 기준으로 **틀린** 곳 ①: 해시 집합의 63% 가 제품 게이트라 제품 팀의 일상 병합(사흘 17건 중 ≈8건)이 하네스 PR 회차를 무효화한다 — E0 자체가 병합 전 1회 겪었고, PR 2·3·4 는 더 길게 열린다(C-1 · 지금).
- 틀린 곳 ②: 회차가 실행자 개인 모델·사용자 설정·계정으로 나오면서 해시는 저장소만 묶는다 — 같은 트리에 구성원마다 다른 판정·4배 다른 비용이 이미 관측됐다(C-2 지금 · C-3 별도 intent · T12 「Ted 실행」은 팀 절차가 아니다).
- 틀린 곳 ③: 회귀 「직전」이 브랜치·해시·시간대를 무시한 id 순서라 구성원 간 회차가 서로의 기준이 된다(C-4 · PR 2).
- 수량: 현 상태 5 PR ≈20 회차 ≈160 USD ≈12 h(1인 기계 직렬) · C-1 적용 시 제품 병합 몫 무효화 0 → ≈8~10 회차 ≈80 USD · C-3 적용 시 비용 주체 org 1곳 · 기계 점유 0.
- 회차 필요 규칙(권고): 필요 = 모델 입력(AGENTS/CLAUDE/.claude/.agents 규칙·역할·스킬/hooks/eval 러너·과제) 변경 · 재사용 = 그 외 파일만 바뀐 병합(해시 불변) · 무효화 회피 = 집합 축소(C-1) + 조상 기반 직전(C-4).
- 계획 순서(PR 1→T1→E0→S-red→PR 2→…)는 유지 가능 · 단 S-red 뒤 소형 PR(C-1·C-2·C-11 · 회차 1회)을 PR 2 앞에 끼우지 않으면 PR 2 의 긴 개방 기간이 재실측 비용을 그대로 받는다.
