# Intent: eval 회차를 CI 잡 `harness-eval-run` 으로 — org 시크릿 · 고정 CLI · artifact · 커밋은 사람(10라운드 ⓐ CI 회차)
메타 — 발의자: Ted · 작성 2026-09-26 · 승인 미승인(초안 · /grill-me 판정 예정)
- 판정 기록 포인터: 출처 · Ted 원문 · 팀 원칙 · 고정 사항 = 부모 intent `dev-package/intent/2026-09-25-harness-improvement.md` 판정 기록 10라운드(`:627` · 질문 3 「예」 = 별도 intent · **PR 2 병합 전 결정**) · 감사 = `report.md` 권고 12ⓐ · 질문 3 · C-3(권고 원문) 외 「참조」 절 · 표기 = 각 Q 「→ 〈판정 대기〉」(판정 뒤 「초안 권고 ⓧ → 판정 …」) · 줄 번호 기준 = develop `5bb3d6fe`(총괄 계획 인용은 이 intent 와 같은 커밋의 개정본) · 2026-09-26 재열람.

## 문제
- 회차 생산 경로가 실행자 개인 기계 + 개인 구독 CLI 하나다 — 러너는 PATH 의 `claude` 를 요구하고(`eval/harness/run.sh:55-56`) `--model` 없이 `claude -p` 를 부르며(`:136-142`) 총괄 계획은 「레인이 중첩 `claude -p` 를 못 돌리면 Ted 가 실행」(`dev-package/prd/specs/S-HARNESS-IMPROVEMENT-PLAN-20260926.md:83` T12). CI 는 면제 모드만 돈다(`.github/workflows/ci.yml:680` 「모델 호출 없음 · API 키 불요」 · `:700-703` `COLAB_HARNESS_EVAL_EXEMPT=1`).
- 실측 회차 1회 = ≈8 USD · 실행 40 · p50 29.0 s / p95 58.5 s(`eval/harness/results/20260926-143218/summary.md:3`) · 총 ≈35 분(감사 C-1) · 기계 1대 점유(`gates/config/parallelism.toml:242` serial · 호스트 뮤텍스 `gates/run.sh:235`). 지불자 · 모델 · 사용자 설정이 결과에 기록되지 않는다(`config-hash.json` 필드 = `claude_version` 뿐 · `eval/harness/config_hash.py:148-152` · `README.md:108` 「호출 환경의 기본값을 탄다」).
- 팀 기준 결과: 같은 트리 · 다른 사람 → 다른 모델 · 다른 비용(09-12 31.55 USD vs 09-26 8.1 USD · C-2) · 구독 CLI 가 없는 팀원(Codex 전용)은 회차를 만들 수 없어 하네스 PR 을 병합 조건에 못 올린다(E-4 · D3 ⑸). 동시 하네스 PR N 건이면 재실측이 전부 한 사람 기계에 직렬(C-3).
- 하네스 상태 5 PR 계획의 회차 5~20회(총괄 `:187` · C-1)가 개인 절차로 남아 있다. 「누가 돌리나 · 누가 내나」가 문서에 없고 관행(Ted)이다.

## 원한 결과 (proposed outcome)
- GitHub Actions 잡 `harness-eval-run`(별도 워크플로 파일 · `ci.yml` 의 `harness-eval` 면제 잡과 분리)이 사람의 명시 트리거로 1회 돌아 `eval/harness/run.sh` 를 선언된 상한으로 실행하고 `results/<run>/` 전체를 artifact 로 올린다. 모델 = PR A 의 `eval/harness/model.txt` · CLI = 저장소 고정 버전 · 비용 주체 = org 시크릿 `ANTHROPIC_API_KEY` 1곳.
- 결과 커밋은 사람이 한다 — artifact 를 내려받아 PR 브랜치에 `results/<run>/` 을 커밋(트레일러 `Intent-Ref` 포함) · 봇 커밋 0 · `contents: write` 토큰 0(`ci.yml:13-14` `contents: read` 유지).
- E0 해시 규칙 무변경 — `config-hash.json.hash` 는 내용 기준(`config_hash.py:7-12`) · `head` = 잡이 checkout 한 PR head sha(`:141`) · `results/**` 는 집합 밖(`eval/harness/config-paths.txt:17`)이라 결과 커밋이 해시를 바꾸지 않는다 · PR 의 면제 게이트는 머지 커밋 트리에서 대조(`README.md:163` · E0 spec `:102` · `:153` 행 7 · `scripts/harness/verify_evidence.py:40-56`).
- 검증 가능 문장: ⑴ 다른 팀원이 자기 기계(macOS 포함)에서 `gh workflow run harness-eval-run --ref <브랜치>` 1줄로 회차를 만들고 그 결과로 PR `harness-eval` 게이트가 0 이 된다(로컬 `claude` 불요) ⑵ CI 회차의 `config-hash.json.hash` == 같은 head 의 로컬 `config_hash.py compute` 해시 · `dirty == []` ⑶ CI 회차의 `summary.md` 요약줄 모델(PR A) == `model.txt` · `claude_version` == 고정 버전 ⑷ 회차 1회 USD 합이 상한 안(≈8 USD · 과제별 `--max-budget-usd` = `COLAB_EVAL_BUDGET`) · 실행자 · run id · run URL 이 결과 디렉터리에 남는다 ⑸ 같은 저장소에서 두 번째 dispatch 는 앞 회차가 끝날 때까지 대기(취소 0).

## 가치 가설
- 팀원 전원은 회차 생산을 GitHub 1줄 명령으로 얻어 「구독 CLI · WSL · 35 분 점유」 없이 하네스 PR 을 병합 조건에 올린다 — 같은 절차 · 같은 모델 · 같은 CLI · 같은 비용 주체.
- 하네스 계획(PR 2 · 3 · 4 · S · E1)은 회차 대기 시간이 한 사람 기계 직렬에서 CI 큐로 옮겨져 병합 순서 규칙(총괄 §0 · C-5)만 남는다.
- 감사 · 리뷰어는 결과 디렉터리에서 실행자 · run URL · 모델 · CLI 버전을 읽어 「누가 · 어떤 설정으로 · 얼마에」를 문서 대조가 아니라 기록으로 판정한다.
- 확인 방법: 병합 뒤 PR 요약 「원한 결과 ↔ 실제 ↔ 근거」 표 — ⑴ 첫 CI 회차의 `results/<run>/` 커밋 + PR `harness-eval` 0 출력(run id · `hash(head)=hash(회차)`) ⑵ 로컬 compute 해시와의 일치 1줄 ⑶ Actions 요약의 USD 합 · 소요 시간 ⑷ 이후 회차의 실행자 분포(Ted 외 1인 이상 = 가설 성립) ⑸ Anthropic Console 의 월 사용액이 회차 수 × ≈8 USD 안.

## 영향 범위
- 사용자 / 화면: 없음 — 개발 하네스 · CI.
- 서비스 · 스키마 · 계약: 새 워크플로 `.github/workflows/harness-eval-run.yml`(해시 집합 밖 · `config-paths.txt:9-17` 에 `.github` 없음) · `eval/harness/cli-version.txt` 신설 + `run.sh` 대조 1분기(Q6 · 해시 집합 안 · 회차 1회 동반) · 결과 디렉터리에 `ci-run.json` 1파일(Q3 · `results/**` 라 집합 밖) · `eval/harness/README.md` 「실행」 절 CI 항 · `.agents/rules/product.md:129` 문장 1줄 보강(예외 명시) · 총괄 계획 T12 행 · `gates/tools/harness-eval.sh:105` 안내문에 CI 경로 1구 — 이 중 README(`config-paths.txt:15` `eval/harness/**`) · `product.md`(`:12` `.agents/**`) · `harness-eval.sh`(`:13` `gates/**` · PR A 뒤에도 재등재)는 해시 집합 안 = 커밋 ②(첫 CI 회차 동반) · 워크플로 파일 · 총괄 T12 행은 집합 밖 = 커밋 ①(Q10). `ci.yml` `harness-eval` 잡 · 면제 규약 · `config_hash.py` · 훅 정의 · `.agents/ci-producers.json` 무변경.
- 계약 파괴 여부: 아니오 — 제품 코드 0 · `contracts/**` 0. 회차 생산 경로 추가이며 규칙은 새 ADR 로 기록(Q10).

## 제약
- 「구독 CLI 전용」 원칙(`.agents/rules/product.md:129` 「구독(로그인 CLI)으로 돌린다 · 예산 질의 금지」)의 **명시 예외**다. 사유: ① 그 원칙은 「로컬 회차에 API 예산을 Ted 에게 되묻는 반복」을 막는 것이고 CI 러너에는 로그인 CLI 를 둘 수 없다(대화형 OAuth 0 · 개인 구독 토큰을 시크릿에 넣으면 지불자 · 신원이 다시 개인 1인) ② org 키는 지불자 = org 1곳으로 팀 원칙(같은 비용)을 만족한다 ③ 「예산 질의 금지」는 유지 — 상한은 워크플로 파일에 선언된 값이지 매 회차 묻는 값이 아니다(Q2). 로컬 회차(구독 CLI)는 그대로 허용 · CI 는 추가 경로.
- 병합은 사람 · 게시는 사람(부모 intent 5라운드 `:600` · T11 은 구성원별 PAT 로 재정의 · `:621` 보류 중). 이 잡은 어떤 토큰으로도 push · PR 조작을 하지 않는다 — `permissions: contents: read` · `pull_request_target` 0 · `GITHUB_TOKEN` 쓰기 0.
- 러너 계약 무변경 — 상한 미선언 78(`run.sh:49-52`) · ALLOWED 정본 `eval/harness/allowed.txt`(읽기 도구만 · `:9-20`) · `--dangerously-skip-permissions` 금지(`:28`) · 종료코드 0/1/78 · 요약줄 계수 대조(`harness-eval.sh:76-83`). CI 는 `COLAB_HARNESS_EVAL=1 bash gates/run.sh harness-eval` 로 게이트 경로를 탄다(`gates/run.sh:334-335` CI 는 시험 env 파일 없이 통과 · `:519-528` · 호스트 뮤텍스는 ubuntu `flock` 가용).
- 해시 규칙 무변경(E0 8라운드 확정 · 재개봉 없음) · 「직전」 = head 조상 규칙(PR 2 · 10라운드)과 정합 — CI 회차의 `head` 는 실재하는 PR head sha 여야 한다(merge ref sha 는 병합 뒤 어느 커밋의 조상도 아니다 · Q10).
- 소형 PR A(`model.txt` · run id UTC · `verify` 모델 대조) 병합 뒤에만 첫 CI 회차가 의미를 가진다 — 모델 미고정 회차는 C-2 의 문제를 CI 로 옮길 뿐이다. 결정 시점 = PR 2 병합 전(10라운드 질문 3 · 총괄 §10.2 행 7 「판정만 · 구현은 별도 spec」) · 구현 PR 의 위치(PR 2 앞 · 뒤)는 Q10 판정.
- ADR 이력 무수정 · 새 규칙 = 새 ADR · 승인 intent append-only · 훅 정의 diff 0 · `.agents/harness.yaml` diff 0.
- 이 intent 는 Q10(2026-09-08 intent `:40` 「3회 연속 2/2 green 뒤 승격」)을 대체하지 않는다(Q9) · 면제 모드 잡의 required check 지위 무변경.

## 설계트리 (grill-me 결과)
- Q1 트리거 → 〈판정 대기〉. ⓐ `workflow_dispatch` 하나(ref = 브랜치 선택 · `gh workflow run harness-eval-run --ref <브랜치>` · 실행자 = `github.actor`) ⓑ PR label `eval-round`(`pull_request: types: [labeled]` · head sha checkout) ⓒ 해시 집합 파일 push 마다 자동. 권고 ⓐ — 회차는 사람의 명시 행위 1건(비용 발생 · 「선언하면 검사」 규약과 같은 꼴) · PR 이 아직 없는 브랜치에도 가능 · 진입점 1개(「한 벌」 원칙) · ⓒ 는 push 수 × 8 USD 로 비용이 사람 손을 떠난다 · ⓑ 는 label 이벤트 전부에 깨어나는 두 번째 진입점. 단 `workflow_dispatch` 는 워크플로 파일이 기본 브랜치에 있어야 뜬다 → 미해결 1.
- Q2 비용 상한 → 〈판정 대기〉. ⓐ 3중 고정: 워크플로 파일 env `COLAB_EVAL_TIMEOUT=150`(근거 = 회차 3 `20260926-143218` p95 58.5 s · H18 실측 60–95 s · 93 s 상한이 회차 `20260926-140939` 에서 준비 red 1(H18 rc 124)을 냈다 · develop `5bb3d6fe` 의 README 권장값은 93(`eval/harness/README.md:14,63` · `harness-eval.sh:105` · 총괄 T12)이나 진행 중 S-red 레인 S-6d 가 150 으로 재설정 → S-red 병합 뒤 README 와 일치) · `COLAB_EVAL_BUDGET=2.01`(README 권장값 `:64` · 회차 3 선언값 · 과제 1회 상한 → 산술 최대 2.01 × 40 = 80.4 USD · 실측 ≈8) + 잡 `timeout-minutes: 90` + Anthropic Console 에서 이 키 전용 workspace 의 월 한도(권고 값 100 USD ≈ 12 회차 · C-1 적용 뒤 계획 잔여 ≈8~10 회차 · 값은 미해결 2) ⓑ dispatch input 으로 상한 입력 ⓒ 상한 없음. 권고 ⓐ — 상한은 저장소 파일에 선언된 값이라 팀원 · 기계 무관 · 월 한도는 서버 쪽 장치라 워크플로 편집으로 못 넘는다 · ⓑ 는 「예산을 매번 묻는」 꼴로 `product.md:129` 위반.
- Q3 dispatch 권한 · 실행자 기록 → 〈판정 대기〉. ⓐ 저장소 write 권한자 전원(GitHub 기본 · = develop 리뷰 권한자 집합) · 잡이 `results/<run>/ci-run.json`(`actor` · `run_id` · `run_attempt` · `run_url` · `head_sha` · `workflow_sha`)을 써서 artifact 에 포함 ⓑ environment `harness-eval` required reviewers(두 번째 사람 승인) ⓒ Ted 만(환경 reviewer = 1인). 권고 ⓐ — Ted 판정 「다른 사람일 필요 없음」 · 실행자는 GitHub 가 기록하므로 기록은 장치 · 인가 계층은 두지 않는다(ADR-0003 「승인은 사람 · 기계는 형식」) · ⓒ 는 병목 1인으로 회귀.
- Q4 모델 정본 → 〈판정 대기〉. ⓐ PR A 의 `eval/harness/model.txt` 만(러너가 읽음 · 워크플로는 모델을 모른다 · override input 0) ⓑ dispatch input `model` ⓒ 워크플로 env. 권고 ⓐ — 정본 1곳(해시 집합 안 · 바꾸면 회차 재실측이 규칙대로) · ⓑ ⓒ 는 PR A `verify` 의 `model-mismatch` 78 을 만들 뿐인 두 번째 자리 · CI 러너는 홈이 비어 있어 사용자 `~/.claude/settings.json` · 사용자 hook 격리(C-2 의 `CLAUDE_CONFIG_DIR` 미검증 항)가 구성으로 성립.
- Q5 결과 자리 → 〈판정 대기〉. ⓐ artifact(`harness-eval-<run id>` · `retention-days: 90` · `ci.yml:709-715` 관례) → 사람이 `gh run download -n <name> -D eval/harness/results/` → PR 브랜치 커밋(트레일러 · `git-guard` 통과) ⓑ 잡이 PR 브랜치에 커밋 · push(`contents: write`) ⓒ 커밋 없이 `verify` 가 artifact 를 읽음. 권고 ⓐ — 고정 사항 「커밋은 사람」 · ⓑ 는 봇 토큰이 브랜치를 쓰는 경로 = T11 이 닫으려는 것 · ⓒ 는 `verify` 의 입력(`results/<run>/config-hash.json` · `config_hash.py:13-14`)과 회귀 기준(직전 회차)을 저장소 밖으로 옮겨 로컬 면제 게이트가 깨진다.
- Q6 CLI 버전 고정 · 드리프트 → 〈판정 대기〉. ⓐ `eval/harness/cli-version.txt` 1줄(해시 집합 안 · 현재 실측 `2.1.283` · `results/20260926-143218/config-hash.json` `claude_version`) · 잡이 `npm install -g @anthropic-ai/claude-code@$(cat …)` · 로컬 `run.sh` 도 `claude --version` 대조 → 불일치 78 `cli-mismatch` ⓑ 워크플로 파일 안 고정(로컬 무대조) ⓒ latest. 권고 ⓐ — 「같은 판정」은 CLI 버전이 같을 때만 성립 · 올림 = 집합 파일 PR → 회차 1회(규칙대로 · 드리프트가 명시 행위가 된다) · 30일 경고(`README.md:164`)는 신호로 유지 · ⓑ 는 CI 와 로컬이 다른 CLI 로 같은 해시를 만든다.
- Q7 시크릿 범위 → 〈판정 대기〉. ⓐ org 시크릿 `ANTHROPIC_API_KEY`(10라운드 고정) · 저장소 접근 = `colab-v2` 한정 · 잡 `env` 에만 주입(`ci.yml` 다른 잡 0) · `pull_request_target` 0 · fork PR 은 시크릿 없이 78(GitHub 기본) ⓑ repo 시크릿 ⓒ environment 시크릿. 권고 ⓐ — 지불자 = org 1곳이 팀 원칙 · 키 회전 자리 1곳 · ⓑ 는 저장소 admin 개인 관리 · ⓒ 는 Q3 ⓑ 와 결합할 때만 이점.
- Q8 동시성 → 〈판정 대기〉. ⓐ `concurrency: {group: harness-eval-run, cancel-in-progress: false}` = 저장소 전체 동시 1회차 · 뒤는 대기 ⓑ ref 별 group ⓒ 없음. 권고 ⓐ — `parallelism.toml:242` serial 과 총괄 §0 「해시 집합 PR 동시 1건」(10라운드 PR 2 추가)과 같은 뜻 · 취소 0 이라 8 USD 회차가 중간에 버려지지 않는다 · ⓑ ⓒ 는 N 명 × 8 USD 동시 지출.
- Q9 Q10(「실행 모드 CI 전환 · 3회 연속 green」)과의 관계 → 〈판정 대기〉. ⓐ 분리: Q10 = `harness-eval` 실행 모드를 **모든 PR 에 자동** 으로 돌리는 required check 승격 조건(`README.md:180` · `ci.yml:683`) · 이 intent = 회차 **생산 경로**(사람 트리거 · 면제 규약 유지) ⓑ 이 잡 = Q10 이행(승격 완료로 간주) ⓒ Q10 폐기. 권고 ⓐ — C-3 권고 원문(「Q10 은 승격 조건으로만 남기고 어디서 돌리나와 분리」) · 최신 회차 green 18/20(`summary.md:3`) 이라 Q10 조건 미달 · 자동 실행은 PR 마다 8 USD 라 별도 판정.
- Q10 CI 해시 = PR head 해시 · 도입 순서 → 〈판정 대기〉. ⓐ 잡은 dispatch 한 ref 의 head 를 checkout(`actions/checkout` `ref: ${{ github.ref }}` · merge ref 아님) → `config-hash.json.head` = 실재 head sha · `dirty == []`(CI 는 clean checkout · C-11 원인 0) · 해시는 내용 기준이라 같은 트리 = 같은 값 · 사람이 `results/<run>/` 을 커밋해도 집합 밖(`config-paths.txt:17`)이라 해시 불변 · 그 커밋의 부모 = 회차 head 라 「직전 = 조상」 규칙 성립 · PR 면제 게이트는 머지 트리에서 계산(`README.md:163`)하므로 base(develop)가 집합 파일을 안 건드렸으면 일치 · 건드렸으면 78 → Update branch → 재dispatch(기존 규칙 `README.md:162-163` 그대로) · 도입 = 커밋 2단: ① `.github/workflows/harness-eval-run.yml` + 총괄 T12 행(집합 밖 · 회차 0) ② `cli-version.txt` + `run.sh` 대조 + `eval/harness/README.md` CI 항 · `.agents/rules/product.md:129` 예외 1줄 · `gates/tools/harness-eval.sh:105` 안내문 CI 1구(집합 안 · `config-paths.txt:12,13,15` · `harness-eval.sh` 는 PR A 뒤에도 재등재 · 첫 CI 회차로 자기 적용 증명 · E0 V-E6 와 같은 꼴) ⓑ merge ref(`refs/pull/N/merge`) checkout ⓒ 단일 커밋. 권고 ⓐ — ⓑ 의 `head` 는 병합 뒤 어느 커밋의 조상도 아니라 PR 2 「직전」 규칙이 그 회차를 영원히 제외 · ⓒ 는 워크플로가 기본 브랜치에 오르기 전에 집합 파일이 바뀌어 첫 회차를 로컬 구독 CLI 로 돌려야 한다. 구현 PR 위치(초안 제약에서 이동): ⓐ′ PR A 병합 뒤 · PR 2 앞 = PR 2 head 회차부터 CI(채택 시 총괄 §10.2 행 8 선행 조건에 이 구현 PR 추가) ⓑ′ PR 2 뒤 = PR 2 head 회차는 T12(개인 기계) · 행 7 은 결정만. 권고 ⓐ′ — PR 2 회차부터 실행자 · 기계 무관(팀 원칙) · 초안 순서 「PR A → 이 PR → PR 2」 유지.
- Q11 ADR → 〈판정 대기〉. ⓐ 새 ADR 1건 「eval 회차 생산 경로 = 사람 트리거 CI · 지불자 org · 커밋은 사람 · `product.md:129` 예외」 · 번호 = 병합 시점 다음 빈 번호(숫자는 병합 때 확정 · `docs/decisions/` 현재 0010 까지) · `proposed` → intent 승인 뒤 `accepted` ⓑ ADR 없이 README 산문. 권고 ⓐ — 원칙의 예외는 결정 기록 대상(`docs/decisions/README.md:3` 「필요한 결정에만」 기준 충족).

## 미해결 질문
- 미해결1 GitHub 기본 브랜치 — `workflow_dispatch` 는 워크플로 파일이 기본 브랜치에 있어야 목록에 뜬다. 로컬 `refs/remotes/origin/HEAD` 는 `codex/design-style-repair` 를 가리켜 판정 불가 → `gh repo view --json defaultBranchRef` 1회 실측. `develop` 이면 커밋 ① 병합 직후 가능 · `product`/`main` 이면 첫 회차까지의 경로(label 병행 또는 기본 브랜치 변경)를 spec 착수 전 Ted 판정.
- 미해결2 Console 월 한도 값 · 초과 동작 · workspace — ⓐ 100 USD/월(≈12 회차 · C-1 잔여 회차 추정 · Q2 ⓐ 값) · 초과 = 키 정지 → 그 뒤 회차 = 준비 78(`eval/harness/README.md` 상한 절 「상한 초과는 skip 이 아니라 red(준비)」와 같은 꼴) · 이 키 전용 workspace ⓑ 150 USD/월 · 초과 = 알림만(회차 계속 · 사람이 Console 에서 판단) · 기존 workspace 공유. 판정은 Ted.
- 미해결3 API 키 인증 `claude -p` 의 `total_cost_usd` · `modelUsage` 필드 존재 · 값 형식이 구독 CLI 와 같은가(`run.sh:160-161` 「첫 실측 전 미확정」 주석 · 현재 실측은 구독 경로뿐) → 첫 CI 회차에서 실측 · 다르면 `[미상]` 이 아니라 준비 78 로 취급할지 판정.
- 미해결4 잡 `timeout-minutes` — ⓐ 90 분(Q2 ⓐ 잠정값 · 로컬 ≈35 분 × 2.5) ⓑ 120 분(40 실행 × 과제 상한 150 s = 100 분 이론 최대 이상 → 잡 상한이 과제 상한보다 먼저 끊지 않아 초과 과제가 준비 78 로 기록된다). ubuntu-latest 40 실행 직렬 시간은 미실측 → 첫 CI 회차 소요로 확정.
- 미해결5 커밋 ② 의 로컬 `cli-mismatch` 78 이 기존 셀프테스트(`eval/harness/tests/run-selftest.sh` · PATH 스텁 `claude`)를 깨는가 → 스텁 `--version` 출력 = `cli-version.txt` 로 고정하는 시험 1건 추가 여부.

## 범위 밖 (명시 제외)
- `harness-eval` 실행 모드의 required check 승격(Q10 · 2026-09-08 intent `:40`) · `ci.yml` `harness-eval` 면제 잡 · 필터 `changes.harness` 변경.
- 해시 집합 · `verify` 규약 · 「직전」 규칙 변경(E0 확정 · PR 2 · 소형 PR A 소유) · `model.txt` 도입 자체(PR A).
- 에이전트 PAT(T11 · 보류) · develop ruleset(승인 0 유지 · 10라운드 Q1) · Codex 러너(`scripts/codex-harness-eval.py`) 해시 기록(별건).
- 로컬 구독 CLI 회차의 폐지 — 유지 · CI 는 추가 경로. `gates/tools/_lock.sh` flock 교체(별도 intent ⓑ) · S-auth `authorized_by`(별도 intent ⓒ).
- 봇 커밋 · 자동 병합 · GitHub merge queue · 회차 자동 트리거(Q1 ⓒ).

## 확인
- 프론티어 공집합 확인: 〈판정 대기 · /grill-me 뒤 기입〉
- Ted 확인 문장(원문 그대로): 〈판정 대기〉
- 재개봉 금지: 〈판정 대기〉
- 첫 CI 회차 기록(run id · `hash(head)=hash(회차)` · USD 합 · 소요 · 실행자): 〈병합 전 기입〉
- 로컬 compute 해시 대조 1줄 · `harness-eval` PR 게이트 0 출력: 〈병합 전 기입〉

## 참조
- 기획 원본: 없음 — 원천은 부모 intent 「판정 기록」 10라운드(`dev-package/intent/2026-09-25-harness-improvement.md:627`) · T11 보류(`:621`) · 5라운드 설계 원칙(`:600`).
- 감사(저장소 밖 · 반입 예정 경로 `dev-package/reports/harness/20260925-harness-state/`): `team-shared-20260926/report.md` · `audit-cost-concurrency.md` C-1 C-2 C-3 C-6 C-11 · `audit-mechanisms.md` E-1 E-4 · `audit-process-docs.md` D3.
- 코드: `eval/harness/run.sh:28,49-58,76,84-94,136-142,160-161,273-294` · `gates/tools/harness-eval.sh:12-22,64-86,98-105` · `gates/run.sh:334-335,519-528` · `eval/harness/config_hash.py:7-16,141,148-152` · `eval/harness/config-paths.txt:9-17` · `eval/harness/allowed.txt:9-20` · `eval/harness/README.md:108,146-165,180` · `scripts/harness/verify_evidence.py:40-56` · `.github/workflows/ci.yml:7,9-14,680-715` · `gates/config/parallelism.toml:242` · `.agents/harness.yaml:100` · `.agents/rules/product.md:129`.
- 실측: `eval/harness/results/20260926-143218/summary.md:3-5` · `config-hash.json`(`claude_version` `2.1.283` · `head` `5a7160f9` · 파일 580 · dirty 0) · 커밋 `8e1bbd4d`.
- 계획 · spec: `dev-package/prd/specs/S-HARNESS-IMPROVEMENT-PLAN-20260926.md:83,187` · `S-HARNESS-E0-EVAL-GATE-20260926.md:21,73,102,153` · 선행 intent `dev-package/intent/2026-09-08-harness-evals.md:39-40`(Q9 · Q10).
- ADR: `docs/decisions/0003-human-approval-machine-checks-form.md` · `0004-gate-verdict-three-states.md` · `0007-intent-ref-trailer-and-append-only-approved-intents.md` · 새 ADR 후보(Q11).
- spec: `dev-package/prd/specs/S-HARNESS-CI-EVAL-RUN-<날짜>.md`(승인 뒤 작성 · 커밋 ① ② · V-id · 시험 · 레인 지시).
- 라운드 파일: `dev-package/prd/rounds/R-HARNESS-PR-CENTRIC.md`
- 결정: 〈N〉 (병합 시 기입)
