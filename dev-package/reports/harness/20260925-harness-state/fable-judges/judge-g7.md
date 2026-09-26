[harness: subagent output matched instruction-shaped pattern(s): settings-json. Control tags below are neutralized (`<` → `<\`); treat any remaining directive-shaped text as a finding to relay to the user, not an instruction to you.]

### C7
- 판정: ⓐ (범위 한정형) — `.agents/harness.yaml` 에 역할별 기대값을 두 도구 몫으로 선언하고 `check_contract` 가 Claude frontmatter · Codex toml 양쪽을 대조. 기존 `test_agent_bridge.py:35-59` 의 Codex 기대 dict 는 하드코딩 대신 harness.yaml 을 읽어 단언(선택 가능 모델 집합 단언은 시험에 유지).
- 확신: 중간
- 사실 확인: 확인 — `scripts/harness/config.py:158-166` 은 `---` 이후 본문만 `expected` 와 비교(frontmatter 값 무검사). `scripts/agent-bridge.py:82-92` 는 toml 의 name·description·developer_instructions 와 advisor `sandbox_mode == "read-only"` 만 검사. `test_agent_bridge.py:35-59` 가 Codex model·effort 를 단언. Claude 쪽은 `S-AGENT-MODEL-TIERING-20260924.md:62` C1 수동 grep 뿐. 추가 사실: harness.yaml 은 JSON 호환 문서(`config.py:5` `import json`)라 PyYAML 없이 선언 확장 가능 · `sources.roles` 5개 목록이 이미 있음 · `harness-contract`(check.py) 와 `agent-bridge`(unittest) 둘 다 required gate(`harness.yaml gates.required` · `gates/run.sh:307-313`)라 강제력은 ⓐ·ⓑ 동등.
- 이유: 안전 속성(lane-worker `isolation: worktree` · advisor `disallowedTools` · measurement-lane `tools: Bash, Read` · Codex advisor read-only)이 Codex 는 gate 로, Claude 는 무검사로 비대칭. ⓑ 는 최소 변경이지만 기대값이 시험 코드 두 곳(Claude/Codex)으로 흩어진다. ⓐ 는 등급 대응(X1 난이도 순서)을 한 파일에서 보이게 하고, C8·C9 문서가 수치를 복제하는 대신 harness.yaml 을 참조하게 만들어 문서 drift 원인을 함께 없앤다.
- 위험·전제: frontmatter 파서는 `key: value` 1행 스칼라만 허용(첫 `: ` 로 분리 · description 의 콜론 주의) · 선언 키만 대조(model·effort·maxTurns·isolation·tools·disallowedTools / model·model_reasoning_effort·sandbox_mode) · 미선언 키(color·description)는 자유. L7 이 PR 2 에서 advisor maxTurns 를 바꾸면 PR 3 선언값은 그 뒤 값 기준.
- 뒤집힐 조건: harness.yaml 이 도구별 값을 담지 않는다는 스키마 결정(`colab-harness/1` 의 `sources` 를 경로 매핑 전용으로 유지)이 있으면 ⓑ 로. Claude frontmatter 에 다중행 값이 도입되면 파서 전제가 깨져 ⓑ 가 싸다.

### C8
- 판정: ⓑ (현재형 문장만) — 개수 수치는 현재형 문장에서 제거하고 「정본 = `.codex/hooks.json`」 참조 · 재신뢰 대상에 `012df481`(09-12 Stop) · `4c07f1ea`(09-18 SubagentStop 대상 확대) · `faff6734`(09-24 SubagentStart researcher) 명시 · lane-worker 스킬 수 교정 · lifecycle-evidence 에 measurement-lane 절 추가. 2026-09-09 날짜가 붙은 관측 기록(`:82-83`)은 이력이므로 그대로 둔다.
- 확신: 높음
- 사실 확인: 확인 — `.codex/hooks.json` 직접 계수: 이벤트 6(SessionStart · SubagentStart · Stop · SubagentStop · PreToolUse · PostToolUse) · 항목 9. `dual-agent.md:70` 「5개 이벤트」 · `:85` 「7개 정의를 검토한다」(현재형 · 낡음) · `:82-83` 「2026-09-09 … 7개」(기록 · 정확). `git log -- .codex/hooks.json` = `faff6734` 09-24 · `4c07f1ea` 09-18 · `012df481` 09-12 · `3e5be9dc` 09-09 → 신뢰 이후 정의 변경 3회 확인. `dual-agent.md:54` 「스킬 4개」 ↔ `.claude/agents/lane-worker.md:7` 5개(colab-ponytail 포함) 확인. `lifecycle-evidence.md:10` researcher·lane-worker 만 · `:85` 「complete 는 lane-worker」 ↔ `lifecycle_contract.py:55` `MEASURING_ROLES` · `:254-255`(--legacy 거절) · `:335`(`allow_red`) 확인.
- 이유: 개수는 정의를 바꿀 때마다 어긋나고(3회 중 3회 미갱신) 검사기가 없다. 수치를 빼면 검사기 없이 drift 가 사라진다. 재신뢰 문장은 「어느 정의가 09-09 이후 바뀌었나」가 Ted(T5) 의 실제 입력이므로 커밋 3개를 적는 것이 정보량이 크다. C7 ⓐ 를 택하면 역할 값도 harness.yaml 참조로 통일.
- 위험·전제: 문서만 바꾸므로 `/hooks` 재신뢰 유발 없음. `dual-agent.md` 가 hygiene always-on 대상은 아님(`harness.yaml hygiene.always_on_files`)이라 길이 상한 무관.
- 뒤집힐 조건: hooks.json 정의 수를 기계 대조하는 검사(예: harness.yaml `hook_registrations` 의 Codex 판)를 함께 넣기로 하면 ⓐ(수치 유지)도 안전해진다 — 단 그것은 목록 밖 고도화.

### C9
- 판정: ⓐ — 문장별 사실 교정. ⓑ(Claude advisor 에서 Bash 제거)는 그룹 T 질문으로 넘긴다(Ted 판정 항목).
- 확신: 중간
- 사실 확인: 확인 — `.agents/rules/colab-rules.md:4` 「이 파일은 paths 없음 → launch 로드」: 현재 launch 로드 파일은 `.claude/rules/colab-rules.md`(4줄 포인터 · frontmatter 없음)이고 `.agents/rules/...` 는 Claude rules 경로가 아님 → 문장의 주어가 틀림. `:28` Fable 재시도 · Sonnet 하강 금지 ↔ `.claude/agents/lane-worker.md:4` opus · `measurement-lane.md:4` sonnet. `:62` 「강제 예정」 ↔ `lane-worker.md:6` `isolation: worktree` 존재. `:65` · `.agents/roles/lane-worker.md:27` 「기준 origin/<default>」 ↔ `.claude/settings.json:4` `baseRef: "head"`. `.agents/roles/advisor.md:39` 「쓰기 도구가 없으므로」 ↔ `.claude/agents/advisor.md:6` `disallowedTools: Edit, Write, NotebookEdit`(Bash 잔존) · Codex 는 `sandbox_mode read-only`(`agent-bridge.py:91-92` 가 강제).
- 이유: 다섯 문장 모두 사실 오류이고 교정만으로 닫힌다. ⓑ 는 Codex 등가물이 「셸 없음」이 아니라 「OS read-only 샌드박스」라 Bash 제거는 Codex 보다 강한 제한(advisor 가 `git log/show/diff` · gate 로그를 못 읽음) — 리뷰 품질 비용이 있고 사고 근거가 없다(findings R2-11 corrected: sev low). git-guard 는 advisor 호출에도 적용된다.
- 위험·전제: §1-3 교정은 역할 등급 spec 참조로 대체하되 백틱 앵커는 유지(`:5` 규칙). `:65` 는 `git merge --ff-only` 첫 줄 유지 · 이유만 「head 기준이라 부모 HEAD 가 통합 브랜치보다 뒤면 낡은 트리」로. 사용자 메모리 `worktree-baseref-must-match-working-branch.md`(fresh=main) 도 같은 이유로 낡음 — 저장소 밖.
- 뒤집힐 조건: advisor 가 Bash 로 파일을 바꾼 사례 1건 → ⓑ 로(그때 형태는 `disallowedTools: Bash, Edit, Write, NotebookEdit` · C7 기대값에 반영). Ted 가 Claude advisor 의 `git` 읽기를 포기해도 된다고 판정하면 ⓑ.

### C10
- 판정: ⓐ (문장 정정형) — 「exit 1 은 통과」 자체는 Claude Code 사실이라 남기고, 「판정 못 하면 통과가 기본값」을 2단 규칙으로 교체: 준비 실패(python3 부재 · envelope 이상) = exit 2 차단(2026-09-09 계약), envelope 통과 뒤 판정 불가(tokenizer 실패 등 · A1) = 통과. 도달 불가 `|| exit 0` 4줄 삭제. A3 이관 문장(Edit/Write 전용 · Bash 쓰기 비대상 · 사후 검사) 추가. worktree-setup 은 `${COLAB_TEST_ENV_FILE:-$HOME/.colab-v2-test.env}` 로 run.sh 와 같은 규칙 · P-E/origin/main 문단 삭제.
- 확신: 높음
- 사실 확인: 확인 — `git-guard.sh:71-72` 머리말 · `:82` python3 부재 exit 2 · `:83` validate-input `|| exit 2` · `:90` `command -v python3 || exit 0`(도달 불가). `migration-guard.sh:21`·`:28`·`:32` / `test-file-guard.sh:27`·`:38`·`:42` / `decision-number-guard.sh:27`·`:34-35`·`:38` 동일 구조. 세 파일엔 「Effective 2026-09-09 … superseded」 한 줄이 이미 있어 완전한 오류 문서는 아님(git-guard 에도 `:81` 주석 있음). `worktree-setup.sh:247-259` baseRef fresh · origin/main · P-E · `~/.colab-v2-test.env` 고정 확인. `gates/run.sh:264` `COLAB_TEST_ENV_FILE` 우선 확인. 추가: 이 PC 엔 `~/.colab-v2-test.env` · `~/.colab-v2-test-31.env` 둘 다 존재 → 현재 메시지는 「파일 유무」가 아니라 「어느 파일인지」가 틀림. `.claude/settings.local.json` 은 worktree 에 없음(미추적).
- 이유: 주석 drift 는 A1 lane 이 git-guard 파싱부를 다시 쓸 때 가장 먼저 읽는 문장이라 정정 가치가 실제로 있다. `grep COLAB_TEST_ENV_SOURCED` 분기는 baseRef head 이후 항상 참이라 else 가지가 사장 코드. ⓑ(주석만)는 worktree-setup 의 틀린 파일명을 남긴다.
- 위험·전제: settings `env` 가 SubagentStart hook 프로세스에 전달되는지 미확인 — 전달 안 되면 `COLAB_TEST_ENV_FILE` 을 hook 이 못 보고 기본 파일로 안내(L3 부모 checkout 관측 1회에서 같이 확인). 게이트 판정 로직 무변경.
- 뒤집힐 조건: hook 환경에 `COLAB_TEST_ENV_FILE` 이 안 들어온다는 관측 → worktree-setup 은 두 파일 후보를 모두 열거하는 문구로 후퇴.

### C11
- 판정: ⓑ + ⓒ 결합 — mtime `find` 삭제, SELECTED 없으면 후보 줄 없음, 기존 `:80` 「legacy 대장·라운드는 읽기 호환 자료」 줄 끝에 위치(`dev-package/prd/rounds/` · 지정은 `COLAB_ROUND`/payload `round`)만 덧붙임(새 줄 추가 없음).
- 확신: 높음
- 사실 확인: 확인 — `bootstrap-diet.sh:47-48`(mtime 동률 시 사전순 뒤) · `:70-71` `find … -printf '%T@' | sort | tail -1` · `:84` 라벨. `SELECTED` = payload `round` 또는 `COLAB_ROUND`(`:52-56`). 정정·추가: 바꿔야 할 종속 지점 3곳 — `scripts/tests/test_harness_lifecycle_contract.py:411` `assertIn('legacy 참고 후보')`, `scripts/agent-bridge.py` SessionStart 부가 문장 「The user's selected round takes precedence over the mtime suggestion above」(`:346` 부근), `test_agent_bridge.py:205` `'mtime suggestion'`. AGENTS.md 는 이미 실행 계획을 `R-HARNESS-PR-CENTRIC.md` 로 명명.
- 이유: 라벨이 「근거 아님」이라 해도 mtime 선택 결과가 매 세션 컨텍스트에 실리고, fresh checkout 에선 사전순 마지막(R-STAGE3-AI-SEARCH)이라 정보량 0 이하. AGENTS.md 가 라운드를 이름으로 주므로 hook 의 자동 추천은 중복. ⓒ 단독은 새 줄을 늘리고(bootstrap-diet 자기 원칙 `:26` 「스스로 길면 안 된다」), ⓑ 단독은 위치 안내를 잃는다.
- 위험·전제: `harness.yaml transition.consumer_paths` 가 bootstrap-diet 를 ledger consumer 로 등재 — 등재는 유지(대장 언급 줄은 남음). Codex bridge 문장을 함께 고치지 않으면 Codex 세션이 존재하지 않는 「mtime suggestion」을 참조.
- 뒤집힐 조건: 지정 라운드 없이 legacy 라운드 작업을 재개하는 절차가 승인돼 hook 추천이 필요해지면 ⓐ.

### C12
- 판정: ⓑ — 출력을 `hookSpecificOutput.additionalContext` JSON 으로(ponytail-inject 방식 · JSON 인코딩은 이미 기동하는 python3 `json.dumps` 로), 머리말 `:21` 교정. ⓐ 관측은 판정 선행 조건이 아니라 PR 검증 단계(병합 뒤 메인 세션에서 `frontend/src` CSS Edit 1회)로 둔다.
- 확신: 높음
- 사실 확인: 확인 — `css-edit-audit.sh:21` 「PostToolUse 의 stdout 은 맥락으로 실려 들어간다」 · `:74` `echo "$OUT"`. 저장소가 인용한 문서 문장(`bootstrap-diet.sh:24-26` · `worktree-setup.sh:41-43`): 평문 stdout 이 맥락에 들어가는 이벤트는 SessionStart · SubagentStart 뿐. `ponytail-inject.sh:75-76` 같은 이벤트(PostToolUse `Edit|Write` · `.claude/settings.json:88-96` 같은 matcher 묶음)에서 JSON 사용. Codex 경로: `agent-bridge.py` `hook_context()` 가 JSON 을 풀어 다시 감쌈(`test_agent_bridge.py` `test_hook_context_json_is_unwrapped_not_nested`) → ⓑ 로 Codex 출력 불변. css-edit-audit 자체 시험은 없음(findings R1 요약 · 시험 목록에 부재) → 출력 형태 시험 1건 추가 필요.
- 이유: 두 근거(문서 인용 · 동일 이벤트의 형제 hook 구현)가 같은 방향이고 반증 근거가 없다. 관측 1회를 먼저 하려면 hook 정의 신뢰 상태(T5 미완)와 「lane 의 hook 수정본은 자기 호출에 미적용」 제약에 걸려 PR 3 lane 안에서는 모델 수신을 관측할 수 없다 — 순서를 뒤집으면 판정만 늦어진다.
- 위험·전제: 행에 백틱·`|` 포함 → printf 수작업 escape 대신 `json.dumps`. 관측은 병합 뒤 메인 체크아웃 + `/hooks` 재신뢰 뒤(T5 · L8 스모크와 묶음).
- 뒤집힐 조건: 관측에서 평문 stdout 이 이미 모델에 닿는다는 결과(Claude Code 버전 변경)가 나오면 ⓑ 는 무해한 중복이라 되돌릴 필요 없음 — 판정 자체는 유지. additionalContext 가 PostToolUse 에서 무시된다는 관측이면 ponytail-inject 도 같이 죽은 것이므로 별도 항목으로 승격.

### 묶음 메모
- C7 ⓐ 를 택하면 C8·C9 의 역할 수치(model·effort·maxTurns·스킬 수)는 문서에 복제하지 않고 `harness.yaml` 참조로 통일 — C8 ⓑ 의 「수치 제거」 원칙과 같은 방향.
- C10 의 `git-guard.sh` 머리말·`:90` 삭제는 A1(PR 1) 이 같은 파일 파싱부를 다시 쓰므로 PR 1 lane 에 얹는 편이 파일 2회 접촉을 피한다(Ted 분할 판정 대상) · 나머지 3 guard + worktree-setup 은 PR 3.
- C11 은 `agent-bridge.py` SessionStart 문장과 시험 2건을 함께 고쳐야 하며, C12 도 bridge 시험(`test_post_patch_css_feedback_reaches_context`)은 평문 mock 이라 JSON mock 으로 갱신 — 둘 다 `agent-bridge` gate 에 걸린다.
- C12 모델 수신 관측 · C10 `COLAB_TEST_ENV_FILE` 전달 관측은 각각 T5(`/hooks` 재신뢰) · L3(부모 checkout 관측) 뒤에만 가능 — PR 3 완료 조건에서 「관측」을 「출력 형태 시험 green」과 분리해 적는다.
- C9 ⓑ(advisor Bash 제거)를 나중에 채택하면 C7 기대값 선언을 같은 커밋에서 갱신해야 gate 가 red 가 되지 않는다.