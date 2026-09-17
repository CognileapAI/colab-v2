# Intent: measurement-lane 의 완료를 훅이 검증하게 만든다
메타 — 발의자: Claude(하네스 공백 관측) · 방향 결정: Ted · 작성 2026-09-17 · 승인 2026-09-18

⚠ **이 intent 는 독립 결정이다.** `2026-09-17-harness-enforces-facts-it-holds.md` 의 규칙 문장에
자동 정렬되지 않는다 — 「새 훅이냐 일반화냐」와 「역할↔훅 대응 검사를 별건으로 두느냐」는
그 규칙에서 연역되지 않고 이 파일이 자기 근거로 답한다.

## 문제
- 신설 역할 `measurement-lane` 에 `SubagentStop` 매처가 없다. `.claude/settings.json:29-48` 의 `SubagentStop` 은 `researcher`(:31 → `uncommitted-artifacts.sh`)와 `lane-worker`(:40 → `lane-gate-summary.sh`) 둘만 건다. 나머지 역할은 종료가 무검증이다.
- `measurement-lane` 은 전수 게이트를 돌고 3계수·종료코드를 그 task 의 증거로 남기는 역할이다(`.agents/roles/measurement-lane.md` · PR #113 로 develop 병합). 즉 **증거를 남기는 것이 산출물 전부인 역할인데 그 증거의 존재를 기계가 확인하지 않는다.**
- 이 공백을 `harness-contract` 가 잡지 못한다. `scripts/harness/config.py:141-159` 의 `hook_names` 검증은 선언된 훅 이름마다 `scripts/harness/hooks/<이름>` 원본과 `.claude/hooks/<이름>` 어댑터 한 줄이 있는지만 본다. **역할 → 훅 매처 대응은 검사 대상이 아니다.** 역할 검증(`config.py:134-140`)도 `.codex/agents/<이름>.toml` 과 Claude 어댑터 본문 일치만 본다.
- 따라서 이것은 잠재 게이트 실패가 아니다. 훅 없이 역할을 추가해도 `harness-contract` 는 green 이다. 무검증 역할이 조용히 늘어나는 구조적 공백이다.

## 원한 결과 (proposed outcome)
- `measurement-lane` 이 종료할 때 그 task 가 3계수·종료코드 증거를 실제로 남겼는지 훅이 확인하고, 없으면 차단한다.
- ADR-0006 배치를 지킨다. 판정 본문은 `.agents/`(`scripts/harness/hooks/`)에, `.claude/` 는 어댑터다.

## 영향 범위
- `.claude/settings.json` 의 `SubagentStop` 배열에 매처 1건 추가.
- 판정 본문은 `scripts/harness/hooks/lane-gate-summary.sh` 재사용 또는 분기. 현재 이 스크립트는 `:5` 에서 `lifecycle_contract.py --role lane-worker` 로 역할을 고정하므로 그대로는 못 쓴다.
- 새 훅 파일을 만든다면 `.agents/harness.yaml:48` 의 `hook_names` 에 이름을 등재해야 `harness-contract` 가 어댑터 정합을 강제한다.
- 계약 파괴 여부: 아니오. Codex 쪽은 `.codex/hooks.json` 에 같은 대응을 따로 넣어야 한다(Claude 설정은 Codex 에 자동 적용되지 않는다 — `AGENTS.md`).

## 제약
- `lane-gate-summary.sh` 는 `gate-summary.json` 존재와 `counts.red_판정 == 0` 을 요구한다(`gates/README.md:104-105`). `measurement-lane` 은 **red 를 재는 것이 임무**라 red 판정으로 차단하면 역할이 성립하지 않는다. 그러므로 검사 조건은 "게이트를 돌렸고 계수를 남겼는가" 이지 "green 인가" 가 아니다.
- ~~`task_state.py` 의 `report` 필드는 `role == 'lane-worker'` 일 때만 채워진다~~ — **이 전제는 낡았다(2026-09-18 정정).** develop 에서 `scripts/harness/task_state.py:12` 가 `GATE_ROLES = ('lane-worker', 'measurement-lane')` 를 단일 정본으로 두고, `:81` 이 `task['role'] in GATE_ROLES` 일 때 `<run 디렉터리>/gate-summary.json` 을 묶는다. `lifecycle_contract.py:45` 가 그 튜플을 **읽어서** 쓰므로 사본이 갈릴 자리도 없다. 즉 **gate-summary 경로는 이미 확정돼 있고**, 이 intent 가 할 일은 그 파일의 존재를 종료 시점에 확인하는 배선뿐이다.

## 설계트리 (grill-me 결과)
- Q1 지금 게이트가 이 공백을 이미 red 로 잡는가 → A 아니다. `config.py:141-159` 는 훅 파일 존재만 본다. 역할↔매처 대응 검사가 없다.
- Q2 `lane-gate-summary.sh` 를 그대로 매처에 붙이면 되는가 → A 안 된다. `:5` 의 `--role lane-worker` 고정과 red 차단 의미가 이 역할과 충돌한다.
- Q3 최소 배선은 → A **초안의 「새 훅 파일」을 기각하고 일반화로 간다(2026-09-18 결정).** `scripts/harness/hooks/lane-gate-summary.sh:5` 의 고정 `--role lane-worker` 를 **역할 인자**로 받게 고치고, `.claude/settings.json` 의 `SubagentStop` 배열에 `measurement-lane` 매처 1건을 더해 같은 스크립트를 역할 인자와 함께 부른다. 새 훅 파일을 만들지 않으므로 `.agents/harness.yaml:48` 의 `hook_names` 등재도, `.claude/hooks/` 어댑터 신설도 없다. 사유 — 판정 본문이 하나면 두 역할의 종료 검사가 갈릴 자리가 없다. `task_state.py:12` 의 `GATE_ROLES` 가 이미 같은 형태로 **한 벌**을 유지하고 있고, 그 옆에 훅만 두 벌로 두는 것은 앞뒤가 맞지 않는다.
- Q4 역할↔훅 대응 자체를 `harness-contract` 가 검사하게 할 것인가 → A **권장하되 별건으로 분리한다(2026-09-18 결정).** 이번 범위가 아니다. 지금 배선을 넣어도 다음 역할에서 같은 공백이 재발한다는 판단은 유효하며, 그것이 별건 intent 의 근거가 된다.

## 미해결 질문
- 없음. 승인 시점에 남은 설계 질문이 없다.
- ~~`measurement-lane` 이 3계수를 어느 파일 이름으로 남기는지~~ — 닫혔다. `scripts/harness/task_state.py:81` 이 `<run 디렉터리>/gate-summary.json` 을 묶는다.
- 참고(후속 레인이 착수 때 확인할 것, 승인 조건 아님) — `.codex/hooks.json` 에 `SubagentStop` 대응 개념이 있는지. Claude 설정은 Codex 에 자동 적용되지 않는다(`AGENTS.md`).

## 범위 밖 (명시 제외)
- 역할↔훅 매처 대응을 `harness-contract` 가 강제하게 만드는 일반화. 별건으로 분리한다.
- `measurement-lane` 역할 본문·권한·모델 변경.
- 커밋·push·PR 게시·배포·이슈 댓글·종결.

## 확인
- Ted 확인 문장(원문 그대로): "좋아 그렇게해"
- 승인 2026-09-18. **남은 승인 필요 지점: 없음.**
  - 배선 형태 — **`lane-gate-summary.sh` 를 역할 인자로 일반화한다.** 신규 훅 1건은 기각(Q3).
  - 역할↔훅 대응 검사의 일반화 — **별건으로 둔다**(Q4).
- 재개봉 금지: 예.

## 참조
- 설정: `.claude/settings.json:29`(`SubagentStop`)·`:31`(researcher)·`:40`(lane-worker) — `measurement-lane` 매처 없음
- 하네스 선언: `.agents/harness.yaml:45`(roles) · `:48`(hook_names)
- 검증부: `scripts/harness/config.py:134-140`(역할) · `:141-159`(훅)
- 훅: `scripts/harness/hooks/lane-gate-summary.sh:5`(`--role lane-worker` 고정 — 일반화 대상)
- 역할 정본: `scripts/harness/task_state.py:12`(`GATE_ROLES`) · `:81`(`gate-summary.json` 결속),
  `scripts/harness/hooks/lifecycle_contract.py:45`(같은 튜플을 읽어 쓴다)
- 상위 규칙 intent: `2026-09-17-harness-enforces-facts-it-holds.md`(승격 ⑤ · 실행 순서 4단).
  이 intent 는 **독립 결정**이며 그 규칙에서 연역되지 않는다.
- 역할 본문: `.agents/roles/measurement-lane.md` · `.claude/agents/measurement-lane.md` · `.codex/agents/measurement-lane.toml` — PR #113 으로 develop 에 병합됐다(초안 작성 시점의 브랜치 `claude/issue-55-56-gate-verdict-reliability`).
- 근거 규정: ADR-0006(본문 `.agents/` · `.claude/` 어댑터)
- spec: 미작성. Ted 승인 뒤 합성한다.
