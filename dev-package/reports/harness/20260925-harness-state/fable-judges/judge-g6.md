[harness: subagent output matched instruction-shaped pattern(s): settings-json. Control tags below are neutralized (`<` → `<\`); treat any remaining directive-shaped text as a finding to relay to the user, not an instruction to you.]

### C1
- 판정: ⓐ (＋ 근거 ADR 을 ADR-0005·spec `2026-09-18-gate-host-mutex.md` 로 바꾸고 ADR-0002 는 「superseded · 이력」으로만 인용)
- 확신: 높음
- 사실 확인: 확인. `.agents/roles/measurement-lane.md:13-17` ADR-0002 인용 · 「`gates/run.sh` 에 프로세스 간 뮤텍스가 없다」 · `.codex/agents/measurement-lane.toml:12` "has no cross-process mutex". 코드: `gates/run.sh:148-191` 이 `serial` 게이트마다 `gate_host_mutex_acquire`(`gates/tools/_lock.sh`, flock · `${TMPDIR}/colab-v2-gate-host-mutex/host` · 상한 900s · 실패 78) · `gates/config/parallelism.toml:21-24` 「`serial` 은 이제 호스트 전역」 · `docs/decisions/0002-*.md:3-6` 상태 superseded → ADR-0005. `lane-worker.md:52` 「게이트 대기는 호스트 뮤텍스가 한다」와 어긋남 확인. `_lock.sh` 주석 「`serial` 이 잡은 동안 다른 프로세스의 `parallel` 은 돈다」 · 잠금 키는 `TMPDIR` 하나.
- 이유: 전제 문장이 코드와 반대라 역할 본문의 신뢰가 깨진다 · 그러나 규율(레인 하나)의 실근거는 남아 있다 — `parallel` 선언 게이트(`schema-diff`·`rls-*`·`stage2-markers` 등 pg 슬롯 소비자)는 뮤텍스 밖이고 postgres 슬롯 4개는 호스트 전역 · 측정 레인은 `all`/선언 집합을 돌려 pool 을 띄우므로 형제 레인과 겹치면 슬롯 고갈 78 이 판정을 오염한다 · ⓑ 완화는 실측 없이 격리 요구를 없애는 결정이라 이 intent 범위 밖.
- 위험·전제: TMPDIR 이 다른 샌드박스(Codex)에서 뮤텍스·슬롯이 갈린다는 미해결 질문(findings R3) → 규율 문장에 「호스트 = 같은 TMPDIR」 를 적지 않으면 또 틀린 전제가 된다.
- 뒤집힐 조건: `parallel` 게이트 전부가 pg 슬롯을 안 쓰거나 pg 슬롯이 레포별로 키잉되는 변경이 들어오면 규율 자체를 재검토(ⓑ 후보).

### C2
- 판정: ⓑ (표 삭제 · 정본 링크 ＋ `COLAB_HOOKS` 절 교정) — 단 `:75` decision-number-guard `origin/main` 은 **현재 코드와 일치**하므로 C5 ⓐ 와 같은 PR 에서만 바꾼다
- 확신: 중간
- 사실 확인: `README.md:64` 「훅 7개」 ↔ `.claude/settings.json` 등록 11(bootstrap-diet · worktree-setup · researcher-task · uncommitted-artifacts · lane-gate-summary · git-guard · migration-guard · decision-number-guard · test-file-guard · css-edit-audit · ponytail-inject) 확인. `:73` main/master ↔ `git-guard.sh:145·156·267` `main|master|develop|product` 확인. `:74` migration-guard `origin/main` ↔ `migration-guard.sh:72-77` `origin/develop` 확인. **정정**: `:75` decision-number-guard `origin/main` 은 `decision-number-guard.sh:63-66` 과 일치(코드가 낡은 쪽 · C5). `:105` 「모든 훅 스크립트의 첫 줄」 ↔ `scripts/harness/hooks/` 12개 중 `uncommitted-artifacts.sh`·`lane-gate-summary.sh` 에 `COLAB_HOOKS` 0건(나머지 10개는 2행에 있음) 확인. 추가 drift: `:57-58` 「스크립트는 `.claude/hooks/` · 전부 bash」 — 현재 `.claude/hooks/` 는 `scripts/harness/hooks` 로 넘기는 어댑터 ＋ `lifecycle_contract.py`. `:60` 「`CLAUDE.md §1`」 — CLAUDE.md 는 얇은 어댑터, 진입점은 AGENTS.md.
- 이유: 표는 이미 한 번 7→11 로 조용히 낡았고 `scripts/harness/check.py` 는 README 를 읽지 않는다(harness.yaml:85 는 존재만 요구) · 검사 없는 표는 다시 낡는다 · 훅 목록의 검사되는 정본은 `.agents/harness.yaml`(settings.json 과 일치 검사 존재 · findings R1) 이고 훅별 설명은 `dual-agent.md` 에 있다 → README 는 「어디서 보나 · 어떻게 끄나 · 못 끄는 것(H6/H7)」 세 가지만 남기면 된다.
- 위험·전제: 클론 첫 페이지에서 훅 목록이 사라져 가독성이 준다 → 링크 두 개(`harness.yaml` 훅 절 · `dual-agent.md` 앵커)를 절 머리에 둔다. ⓐ 를 택하면 PR 3 안에서 검사 추가 없이 또 drift 를 기약한다.
- 뒤집힐 조건: harness-contract 가 README 훅 표를 파싱해 settings.json 과 대조하는 검사를 이미 갖게 되면 ⓐ 로 전환.

### C3
- 판정: ⓐ (＋ 잘못 놓인 주석은 3곳)
- 확신: 높음
- 사실 확인: `ci.yml` 잡 16(`changes` 제외 15): product-safety · search-golden · contract-gates · frontend-gates · boundary-gates · schema-gates · dormant-tests · service-tests · planning-gates · repo-hygiene · intent-ref · harness-eval · gate-selftest · required-gates · ci-required. `gates/README.md:233-245` 표 11행 · `search-golden`·`product-safety`·`required-gates`·`ci-required` 부재 확인. `:236` frontend-gates 행에 `frontend-fixture-reach` 없음 ↔ `ci.yml:324` 실행 확인. `:244` 「시크릿 참조 · 부재는 78」 ↔ `ci.yml:681-700` secrets 참조 0 · `COLAB_HARNESS_EVAL_EXEMPT=1` · 주석 「모델 API 키가 필요 없다」 확인. 주석: `:167-171` 「WU-D3 골격」이 search-golden 잡 스텝 사이에 잔존 · `:641-652` harness-eval 설명이 repo-hygiene 잡 안 · **추가** `:702-703` 「red 를 낼 수 있는지 증명」(gate-selftest 머리말)이 harness-eval 잡 안. `agent-bridge.yml` 존재 · README 언급 0 확인.
- 이유: 표의 값(조건 · 도는 게이트)은 870행 ci.yml 을 대신하는 유일한 요약이라 삭제(ⓒ)는 손실 · ⓑ 의 대조 검사는 harness-contract 에 실리는데 그 게이트는 path-filter 된 `agent-bridge.yml` 에서만 돌아(findings R4-2) ci.yml 만 바꾼 PR 에서 안 돈다 → 검사가 지키지 못하는 자리에 검사를 더하는 셈 · 기계 대조는 이미 `ci-producers.json` ↔ ci.yml 층(required-gates/ci-required)에 있다.
- 위험·전제: 표는 다시 낡을 수 있다 → 표 머리에 「행 = ci.yml `jobs` 키와 1:1 · 잡 추가 시 이 표」 한 줄과 `agent-bridge.yml`·`product-promotion.yml` 을 별표로 적는다.
- 뒤집힐 조건: harness-contract(또는 새 producer)가 ci.yml 변경 PR 마다 required 집합으로 돌게 되면 ⓑ 로 승격.

### C4
- 판정: 새 선택지: ⓑ 의 포인터 이동 ＋ ⓐ 의 append 포인터 — `AGENTS.md:18` 은 `harness-transition-handoff.md` 머리의 신설 「이후 이력」 절(#130 · #131 · #140 · 이 intent · PR 1-3)을 가리키고, `R-HARNESS-PR-CENTRIC.md:4` 아래엔 그 절로 가는 1줄만 · `:162`·`:175` 본문은 고치지 않고 그 위 「당시 기록」 표지에 날짜·해소 범위를 덧붙인다
- 확신: 중간
- 사실 확인: `AGENTS.md:18` → `R-HARNESS-PR-CENTRIC.md` 확인 · 그 파일 `:4-8` 「전면 전환·추가 고도화는 보류」 · handoff `:28-46` 같은 범위 확인. #131(`23cdf03c` agent-model-tiering) · #140(`bf261d4a` harness-external-gap) 병합 확인 · #130 은 findings R5-1. **정정**: handoff `:25` 가 「아래 이전 상태는 당시 기록이다」로 `:155-180` 을 이력으로 이미 표지 → `:162`·`:175` 는 모순이 아니라 표지가 멀어 보이지 않는 문제. `:51-66` 실측은 **Codex 앱 · 루트 사본**만(「모든 훅 이벤트 · 별도 worktree · Claude 에서 같은 결과를 뜻하지 않는다」 자체 명시) → 「native hook 미확인」을 전부 해소한 것도 아니다.
- 이유: 매 세션 읽히는 건 AGENTS.md 한 줄이고 그 줄이 「보류」 문서로 보낸다 · rounds 파일은 bootstrap-diet 가 legacy 로 표시하는 대장(findings R1-12)이라 현재 계획의 자리가 아니다 · 이력 문서 두 벌을 다 고쳐 쓰는 대신 색인 하나(handoff 머리)에 append 하면 append-only 규율과 맞다 · 세 PR 이 끝나면 색인이 그대로 이력이 된다.
- 위험·전제: 색인이 「이 intent」를 가리키면 intent 완료 뒤 낡는다 → 항목마다 PR 번호·병합 SHA 로 적고 PR 3 마지막에 갱신. `:162` 정정은 「Codex 루트 사본 2건 확인 · Claude 쪽은 훅 단위시험 ＋ #140」으로 범위를 갈라 적는다.
- 뒤집힐 조건: Ted 가 rounds 파일을 계속 현재 계획 정본으로 쓰겠다고 하면 ⓐ 단독.

### C5
- 판정: ⓐ (ruleset JSON 의 required check 이름은 T1·B1 결론에 맞춰 PR 3 시점에 확정 · guard 기준 `origin/develop` ＋ 기준 부재 = 준비 실패)
- 확신: 중간
- 사실 확인: `github-ruleset.json:6` `refs/heads/main` · `:9` check `required-gates` · 이름 「proposal only」 확인. `release-evidence.md:45` 「미적용」 · `:42-43` 「dev/main 릴리스」 확인. `decision-number-guard.sh:63-66` `origin/main` → 실패 시 `max-decision.sh` → `:73` `[ -n "$BASE" ] || exit 0` 확인(fail-open · 원격 main 부재라 1차 경로는 항상 죽어 있음). `migration-guard.sh:72-74` origin/develop 부재 시 준비 실패 · `:5·:10-11·:55·:70` 주석 `origin/main` 확인. findings R3-3: 원격 main 404 · `branches/main` → develop 리다이렉트(rename) · 적용 ruleset 은 product 하나 · develop 은 required check 0. **추가**: `git-guard.sh:271` 거부 문구 「`git branch -D main|master`」인데 집합은 `:267` develop·product 포함 — 문구 drift.
- 이유: decision-number-guard 는 「`origin/main` 기준 재실측」 규율의 1차 경로가 한 번도 실행되지 않는 상태 · 두 ref guard 의 실패 방향이 반대인 것은 같은 PreToolUse 에서 한쪽만 조용히 통과하는 형태라 맞춘다 · ruleset JSON 은 제안서라도 존재하지 않는 브랜치를 가리키면 T1 논의의 입력값으로 못 쓴다 · PLAN-SoT 가 legacy 라 사용자 노출은 낮고 변경 비용도 낮다.
- 위험·전제: JSON 이 `required-gates` 를 develop required check 로 두면 B1(병합 부모 대조 · #160 red)이 해결되기 전엔 base 가 움직인 PR 마다 병합 차단 → PR 3 은 PR 2 뒤라 순서는 맞지만 문서에 「B1 결과 반영」을 적는다 · 준비 실패 전환은 origin/develop 없는 오프라인 클론에서 PLAN-SoT 편집을 막는다(migration-guard 와 동일 조건이라 신규 마찰은 아님).
- 뒤집힐 조건: Ted 가 develop 에 required check 를 두지 않기로(T1) 하면 JSON 은 ⓑ 「폐기 표기」로 · PLAN-SoT 가 완전 동결되면 guard 자체 제거가 더 싸다.

### C6
- 판정: ⓐ ＋ ⓒ (adapter 에 `disable-model-invocation` 값 승계 · agent-bridge 양방향 검사 · VENDORED.md `:5`·`:98` 정정) · description 복사(ⓑ)는 하지 않음
- 확신: 높음
- 사실 확인: 본문 flag 4건(`to-spec:4` · `grill-me:4` · `apple-design:4` · `agent-browser:5`) · `.claude/skills/**` 0건 확인(`grill-me` adapter 9행 · frontmatter name·description 만). 실증: 이 세션의 사용 가능 스킬 목록에 grill-me · to-spec · apple-design · agent-browser 가 모델 호출 후보로 올라 있다(Claude 는 adapter 의 frontmatter 만 읽는다). `agent-bridge.py:98-111` 본문 → adapter 존재 · 경로 문자열 포함 · 길이 비교만 · 역방향·flag 검사 없음 확인 · codex_only = `slack-completion`(`harness.yaml:63`). `VENDORED.md:5` 「전 8종 명시 호출 전용」 ↔ flag 는 4종 · `:19` ponytail 은 「명시 호출 전용과 달리」 자체 명시 → 문장 거짓 확인. `:98` diff 대상 `.claude/skills/<name>/SKILL.md` 확인 → 본문 경로여야 한다.
- 이유: flag 는 Claude 실행 시 실제 동작(자동 발동 여부)이라 doc drift 가 아니라 정책 미적용 · 값 승계는 frontmatter 1줄이고 검사는 기존 루프에 2조건(양방향 존재 · flag 동일) 추가로 끝난다 · description 복사는 본문 트리거 문구의 두 번째 사본을 만들어 「규칙·스킬 본문을 양쪽에 복제하지 않는다」(AGENTS.md)와 어긋나고, flag 붙은 4종은 어차피 자동 발동 대상이 아니라 이득이 없다.
- 위험·전제: flag 승계 뒤 4종이 Claude 자동 목록에서 빠진다 → 경로로 읽는 소비자(`design-review` → apple-design · VENDORED:64)는 영향 없음 · `/agent-browser` 는 명시 호출로 쓰던 대로. agent-bridge 검사는 `agent-bridge.yml` path-filter 안에서만 돈다(R4-2) — `.claude/skills` 가 필터에 있는지 PR 3 에서 확인.
- 뒤집힐 조건: Claude Code 가 adapter frontmatter 대신 참조 본문의 frontmatter 를 읽는 동작이 확인되면 ⓒ 만으로 충분.

### 묶음 메모
- C2 `README:75`(decision-number-guard 기준)는 지금 코드와 일치 → C5 guard 변경과 같은 PR 에서만 고친다. 순서를 어기면 README 가 코드보다 앞서 낡는다.
- C5 의 guard 기준·실패 방향 변경은 Ted 정의로는 「blocking guard」(PR 1 범주)다 → PR 3 에 두려면 그 예외를 spec 에 적거나 PR 1 로 옮긴다. `git-guard.sh:271` 문구 drift 는 PR 1 에서 같이.
- C5 ruleset JSON 의 required check 는 B1(PR 2) 결과와 T1 판정에 종속 → PR 3 착수 시점에 값을 넣는다.
- C4 색인은 PR 1·2 병합 SHA 를 담아야 하므로 PR 3 의 마지막 커밋에서 쓴다. C2 의 README 정본 링크도 같은 색인을 가리키면 포인터가 하나로 모인다.
- C1·C2·C3 은 코드가 맞고 문서가 틀린 drift 라 동작 변경 0 · C5(guard) · C6(flag) 만 실제 동작이 바뀐다 — PR 3 검증 범위를 이 둘에 집중한다.