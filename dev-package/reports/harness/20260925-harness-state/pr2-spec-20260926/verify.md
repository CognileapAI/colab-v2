VERDICT: GO-WITH-CHANGES

For: B3 선행 · 판정 예외 클래스 · P 커밋 1회 · T11 무의존 · S-red 기대값 78→1 을 의도로 명시 — Ted 판정(B3 ⓐ · Q-D ⓐ · Q1 ⓐ · Q3 ⓐ · Q4 ⓐ · Q5 ⓐ · L2 ⓑ · 8라운드 ⑧⑨⑫ · T11 보류)과 전부 일치. 핵심 인용 실재 확인: `verify_evidence.py:57-58/:289,:293/:362/:406` · `lifecycle_contract.py:313,315/:500/:549/:566/:601-604/:611-613` · `git_guard_parse.py:423/:448/:490,:492/:521/:552` · `test-file-guard.sh:42-43/:49/:81-86` · `check_scope_declarations:81-92` · `docs/decisions/0010-*` 존재. `ci.yml` 은 E0 병합 드리프트(RUN `:494` · intent-ref `:654` · ci-required `:837` · always_required `:854` · required-gates `:799`) — 「레인 재열람」 규칙으로 흡수.
Against: 단위 수(코드 신설 4파일 · hook 3 · CI 잡 2 · 역할 산문 전면)가 한 레인·한 PR 에 과다 — 되돌림은 묶음 revert 로 가능하나 리뷰 수정 시 eval 재실측(≈32 USD) 재발 위험. 분할 근거(총괄 §2)가 있으므로 폐기 사유는 아님.

차단급
- §8 scope · `gates/tools/harness-eval-selftest.sh` 누락 — §10 #7 ⓐ · 4.2 B5 · §5 게이트 배정이 이 파일 편집을 요구 → handoff 가 scope 위반 rc 1. 교체: `--scope 'gates/tools/harness-eval-selftest.sh'` 추가 · `adr-records` 가 색인을 요구하면 `--scope 'docs/decisions/README.md'` 도 추가.
- 4.3 ⑵ · Intent-Ref 집합 == 「출처 intent」 — B1 출구 「Update branch」가 만드는 병합 커밋은 트레일러 0 → 자기 모순으로 red. 교체: 「`git log --no-merges <base>..<head> --format=%(trailers:key=Intent-Ref,valueonly)` · 빈 값 제외 · 집합 동일」 + `pr-contract.yml` 에 `actions/checkout fetch-depth: 0` · `env: GH_TOKEN: ${{ github.token }}` 명기.
- §6 · §10 #5 · 열린 질문 8 ↔ §8 begin — §8 은 S-red 시점 CLI(`--spec` 없음)로 begin 하므로 「판정 대기 0 이어야 레인 시작」은 성립하지 않음. 교체(§6 · #5 양쪽): 「`--spec` 자기 적용은 PR 2 병합 뒤 다음 레인(PR 3)부터 · 이 레인은 §8 대로 `--spec` 없이 begin · §10 판정은 advisor ① 게이트 요건으로만 선행」.

개선
- 4.8 전제 — L8(intent :622)은 SubagentStart/Stop 만 관측 · PreToolUse `agent_type` 은 문서 근거(`git-guard.sh:42-46`)뿐 · intent :551 은 A2 ⓐ 선결을 「PreToolUse agent_id ↔ task agent_id」로 명시. 교체: 「새 사실」 절에 「PreToolUse `agent_type` 은 문서 근거 · 미관측」 · 4.8 에 폴백 「`agent_type` 부재 ∧ `agent_id` 있음 → `open-tasks` 의 `task.agent_id` 일치 role 사용 · 둘 다 없음 = 메인 통과」 · V-P13 에 「audit.jsonl 첫 subagent Edit 줄의 `agent_type` 값 관측 1」.
- 4.8 ⓓ · `COLAB_ALLOW_TEST_EDIT` 무효화에 출구 없음(`test-file-guard.sh:21` 「사람이 선언한 뒤」 삭제 효과). 교체 deny 문구: 「fix task 는 보호 경로 편집 불가 — 시험이 틀렸다는 판단은 메인이 `lifecycle close <id>` 뒤 시험 경로를 scope 에 넣은 새 task(fix 없음)로」.
- 4.6 ⓑ · 승계된 baseline 의 미인계 변경 때문에 새 researcher 의 H6 가 모든 mode 에서 거절 → 8회 소진. 교체: stop() 거절 문구 「inherited from task <old>: <paths> — exits: main `lifecycle close <old>` + 그 경로 revert/commit 뒤 재스폰」 · `test_task_runtime.py` ⑨ 사례 추가.
- 출처 절 · 「8라운드 ⑩(⑼ role 결합은 bridge 실측 뒤)」 — intent ⑩ 은 S-auth 별도 intent. 교체: 4.8 · 머리말의 ⑩ 인용을 「intent :551 그룹 A 보강(A2 ⓐ 선결 = L8)」로.
- §10 #1 · 8라운드 ⑪ 이 「ADR 2줄 = 새 ADR-0011」로 번호를 이미 확정. 교체: #1 항목명을 「⑪ 재판정: B3 = 0011 · 2줄 ADR = 0012」로 적어 번호 이동임을 드러냄.
- §8 인계 명령 — intent :622 「공백 인자는 worktree 가드 거부 → `--mode=complete`」를 PR 2 지시에 반영하기로 함. 교체: `--mode=complete --summary='…'` · 60개 `--scope` 단일 명령 통과를 첫 행동에서 확인(거부 시 `--scope=` 형태).
- 4.8 Codex — `COLAB_AGENT_TYPE` 을 누가 export 하는지 없음(부재 = FO 통과 = 분기 무효). 교체: 「Codex 레인 기동 = `scripts/dev.ps1 codex --role <r>` / bridge `--worker` 런처가 export · 미설정 = 통과 · PR 본문 「남은 제약」에 기재」.
- 4.2 B1 · B2 ⓓ 실행 게이트 이름 없음. 교체: 「게이트 `harness-contract-selftest`(`test_harness_evidence.py`)」 1줄씩.
- §1 B2 진술 — 현행 `RUN`(`:494`)은 ai-service · pipeline-worker → core-api 를 이미 포함(등록부보다 넓음). 교체: 「RUN ⊋ 등록부 filters → 등록부 기준 「비적용 생산자 증거」로 판정 불일치」.

검사 결과: 단위 5요소 전부 충족(L4 · L7 · 4.12 「산문 · 맥락만」 표기 ✓) · 역할 파일 편집 P 1회 ✓ · E0/S-red/PR 3 중복 0 ✓ · Codex 병행 4.1/4.5/4.7/4.8/4.10 명시(4.8 만 위 보강) · T11 무의존 ✓(Ted 원문 「나중에 · intent 로만」과 일치).