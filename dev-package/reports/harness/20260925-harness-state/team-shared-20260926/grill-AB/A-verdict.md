(Opus) 판정자: Opus 5.5 (Fable 대체, 주간 한도). spec A: `dev-package/prd/specs/S-HARNESS-TEAM-A-EVAL-20260926.md` · 입력: `~/.claude/reports/harness-state-20260925/team-shared-20260926/grill-AB/A-blind.md`

### A-#1
- 판정: ⓑ `claude-opus-5-5`
- 확신: 중간
- 사실 확인:
  - `results/20260926-143218/H01.raw.1.json` 의 `modelUsage` 키는 `claude-opus-5-5[1m]`, `canonicalModel` 은 `claude-opus-5-5` 이다(재확인).
  - `README.md:108` 은 `claude-fable-5-1` + 보조 `claude-haiku-4-5` 이고, 근거는 09-08 실측이다. 09-12 raw 는 이 worktree 에 없어 fable 이었는지 미확인이다.
  - 단가(claude-api 참조표, 2026-06-24 기준): Fable 5.1 $10/$50, Opus 5.5 $4/$20 → 토큰당 2.5배. 회차 실측은 32.45 vs 7.48–8.11 USD 로 약 4배다.
  - Fable 5.1 은 30일 데이터 보존이 필수다. ZDR org 에서는 400 이 난다. Q3 의 CI `harness-eval-run`(org 시크릿)에서 쓸 수 있는지는 미확인이다.
  - intent `:627` 의 PR 2 추가 항목이 이미 T12 를 「회차 ≈8 USD(09-26 실측)」로 적었다(권고 2–12 전부 수용).
- 이유:
  - 팀 원칙상 고정 모델은 모든 구성원이 한도 안에서 반복 실행할 수 있어야 한다. Fable 은 이 계정에서 이미 주간 한도에 걸렸다. 회차당 4배 비용이면 한도 소진이 앞당겨져 T12 대기가 반복된다.
  - 10-02 전에는 모델과 무관하게 회차가 불가능하다. 그래서 Fable 쪽의 대기 비용 논거는 단기적으로 동률이고, 결정 기준은 비용과 접근성으로 남는다.
  - 최근 4회차(125205 · 140939 · 143218 · 174808)와 10-02 에 돌 S-red 회차가 모두 opus-5-5 다. 과제별 불안정 관측(H15·H16·H18)도 같은 모델 위에 쌓여 있다.
- 위험·전제:
  - 회차가 「판정 모델(Fable) 기준」이 아니게 된다.
  - `--model claude-opus-5-5` 가 `[1m]` 변형을 고르는지는 미실측이다(`canonicalModel` 대조라 판정에는 영향 없음).
  - `COLAB_EVAL_BUDGET=2.01` 의 근거가 fable 값(`README.md:64`)이므로 근거 문구를 고쳐야 한다.
- 뒤집힐 조건:
  - Ted 가 eval 의 목적을 「Fable 이 맡는 advisor 판정 품질 측정」으로 명시하는 경우
  - 또는 전 구성원의 Fable 접근과 주간 여유가 실측으로 확인되는 경우

### A-#1a
- 판정: ⓐ (러너 78 · 대체 모델로 재지 않음 · 정본 교체는 별도 PR)
- 확신: 높음
- 사실 확인:
  - `run.sh:153-156`: `claude -p` rc≠0 이면 `task_ready`(준비)이다. `is_error` JSON 도 준비 red 로 처리된다(`run.sh` 주석 advisor ②). 따라서 접근 불가는 `:300-302` 에서 78 이다.
  - intent `:628`: 09-26 의 429 는 opus 회차 중에 났다. 주간 한도는 모델을 가리지 않는다.
- 이유:
  - 러너가 가용 모델로 조용히 바꿔 재면 #1 의 고정 자체가 무의미해진다.
  - ⓑ 도 결국 `model.txt` 변경 PR(해시 변경)이다. 그래서 ⓐ 는 ⓑ 를 막지 않고, 정본 교체를 사람이 판정하는 PR 로 한정한다.
  - #1 을 ⓑ 로 판정하면 10-02 대기는 모델 선택과 무관한 기존 조건이다.
- 위험·전제: 모델 접근권이 없는 구성원은 하네스 PR 회차를 만들 수 없다. 이 공백은 Q3 CI 회차 intent 가 메운다.
- 뒤집힐 조건: CI 회차(Q3)가 기각되고, 구성원 과반이 정본 모델에 접근하지 못하는 것이 실측되는 경우

### A-#2
- 판정: 「새 선택지: 순서 조건 삭제 — B 는 해시 집합 diff 0 이라 어느 순서든 A 회차에 무관 · 실제 순서 = B 선행(intent `:629`)」
- 확신: 높음
- 사실 확인:
  - ⓐ·ⓑ 의 공통 전제 「B 가 `gates/fixtures/intent-ref/*.json` 을 바꾼다」는 틀렸다.
    - spec B `:17`: 정답표는 해시 집합이라 손대지 않는다.
    - V-B7(`:147`): `git diff develop -- gates/fixtures/intent-ref/` 가 빈 diff 여야 한다.
    - V-B11(`:30`): 해시 집합 diff 0 이다.
    - v2 정답표는 `scripts/tests/**` 에 둔다(`:35`).
  - intent `:629`: 「소형 PR B 선행 · spec A 레인은 리셋 뒤까지 대기」로 이미 판정됐다.
  - spec A `:4`(「우려 #2 순서 조건」), `:117`, T13 「B 보다 먼저」는 낡은 문구다.
- 이유:
  - B 는 A 레인 착수(S-red 병합 뒤) 전에 병합될 예정이다. A 회차는 B 가 포함된 트리에서 한 번만 잰다.
  - B 가 해시 집합을 건드리지 않으므로 S-red(#178)의 Update branch 도 회차에 영향이 없다.
- 위험·전제: B 레인이 V-B7·V-B11 을 실제로 지켜야 한다. 이 두 검사가 B 의 병합 조건이다.
- 뒤집힐 조건: B 최종 diff 에 해시 집합 경로(`gates/**` · `.agents/**` 등)가 들어가는 경우

### A-#3
- 판정: ⓐ 포함(`:(exclude).agents/ci-producers.json`)
- 확신: 높음
- 사실 확인:
  - `ci-producers.json` 을 읽는 곳은 `scripts/harness/verify_evidence.py`, `scripts/tests/test_harness_evidence.py`, `.agents/harness.yaml` 참조뿐이다. 모델이 읽는 규칙·스킬·훅은 아니다.
  - 변경 이력은 제품 게이트 커밋이다: `00dd1375` region-within-drift, `0f88bfec` frontend-design-lint, `cf0114d7`.
  - 보고서 `:235` 권고 3에 명시돼 있고, intent `:627` 「권고 2–12 전부 수용」이 이를 덮는다.
- 이유:
  - `config-paths.txt:8` 이 이미 「판정기 · 모델 입력 아님」을 제외 기준으로 쓴다. 등록부도 같은 부류다.
  - 제품 게이트 PR 이 이 파일을 함께 바꾸므로, 남겨두면 `gates/**` 를 뺀 효과가 반감된다(C-1).
  - Q2 문장이 `gates/**` 만 적은 것은 범위를 제한한 것이 아니라 대표 항목이다.
- 위험·전제: 단일 파일 exclude 가 pathspec 으로 성립한다는 spec §4.2 실측을 레인이 ⓕ 시험으로 재확인해야 한다.
- 뒤집힐 조건: eval 과제 fixture 나 러너가 `ci-producers.json` 을 입력으로 읽는 경로가 발견되는 경우

### A-#4
- 판정: ⓐ (확정 3개만)
- 확신: 높음
- 사실 확인:
  - `dev-package/reports` 아래 홈 절대경로가 있는 파일은 82개, 일치는 약 182건이다(`<home>/` 146 · `<home>/` 34 · `<home>/` 2 · `/home/user/` 1).
  - `dev-package/reports/harness/` 하위만 봐도 5개 파일이다(`2026-09-06/pe-sweep-3.12.log`, `20260924-lane-hygiene-review/A2-turn-cuts.md`, `20260924-agent-model-tiering/M2-codex.md`, `20260925-external-harness-gap/G1-flow.md`, `G2-guards.md`).
  - `compatibility_read_roots` 는 `harness.yaml:93` 에 있다(재확인).
- 이유:
  - 뿌리를 추가하면 약 180건이 red 가 된다. 치환 범위가 이 PR 의 「10줄 diff」 병합 조건(§4.5)을 크게 넘는다.
  - 다른 구성원 홈(`<home>/`)이 포함돼 있어, 정리는 팀 공지를 동반한 별도 작업이 맞다.
- 위험·전제: 그때까지 reports 에 새 홈 경로가 들어와도 게이트가 잡지 못한다. B 반입물은 B 자신의 grep 검사가 막는다.
- 뒤집힐 조건: reports 전수 치환이 선행 PR 로 끝나 잔존이 0이 되는 경우 → 그때 뿌리를 추가한다.

### A-#5
- 판정: ⓐ 요약줄 끝 ` · 모델 <정본>` (별도 줄 `- 모델 — 정본 · 실측` 은 V-A1 대로 함께 둔다)
- 확신: 중간
- 사실 확인:
  - `run.sh:273` SUMMARY 한 줄이 `summary.md` 「- 요약 —」와 stdout 두 곳에 쓰인다.
  - 게이트 실행 모드는 stdout 요약줄만 `$` 앵커 정규식으로 읽는다(`harness-eval.sh:77-79`). 별도 줄은 stdout 에 없다.
  - `SUMMARY_RE`(`config_hash.py:37-38`)는 앞부분만 읽으므로 영향이 없다.
- 이유:
  - intent `:627` 과 보고서 권고 2의 「요약줄 모델 표기」 문구에 그대로 맞는다.
  - 실행 로그와 CI 출력 한 줄에서 모델이 보인다. 회차 비교표에서도 한 줄로 읽힌다.
  - 정규식 3곳과 가짜 러너 요약 4줄의 변경은 셀프테스트 red 로 드러난다(fail-closed).
- 위험·전제: 정규식 누락 시 run 모드가 red 가 된다. 판정이 풀리는 방향이 아니라 막히는 방향이다.
- 뒤집힐 조건: S-red 병합 뒤 요약줄 형식을 읽는 소비자가 더 있어서 변경 면이 크게 늘어나는 경우

### A-#6
- 판정: 「새 선택지: 러너가 판정하되 즉시 exit 하지 않음 — `정본 ∉ model_usage`(빈 목록 포함)면 `N_READY+1` · `summary.md` 를 끝까지 쓴 뒤 `:300-302` 의 78 · `verify` 의 `model-mismatch` 조건은 이중 방어로 유지」
- 확신: 중간
- 사실 확인:
  - 게이트 실행 모드(`harness-eval.sh:72-84`)는 러너 rc 와 요약줄 계수만 보고 `verify` 를 부르지 않는다.
  - ⓐ 이면, 모델을 쓰지 않았거나 다른 모델이 응답한 회차가 실행 모드에서는 green 이고 면제 모드 `verify` 에서는 78 이다. 같은 회차에 판정이 둘이 된다.
  - 문자 그대로의 ⓑ(즉시 78)는 spec §4.1 이 스스로 지적한 결함이 있다. `summary.md` 없는 디렉터리가 남아 `_summary()` ConfigHashError 로 전체 78 이 된다(`config_hash.py:157-166`).
- 이유:
  - 판정 시점을 가장 이른 곳으로 당기면서 두 모드의 판정을 일치시킨다.
  - 방식은 spec 이 `record-usage` 실패에 쓴 「준비 +1 · 요약 완주」 규약과 같다. 새 갈래가 아니다.
  - 셀프테스트 스텁은 green 응답에 `modelUsage` 를 넣으므로 규약을 하나로 유지할 수 있다.
- 위험·전제: 러너가 정본을 두 번 대조하게 된다(러너와 `verify`). 사유 문자열은 `model-mismatch` 로 통일해야 한다.
- 뒤집힐 조건: 게이트 실행 모드가 종료 전에 `verify` 를 부르도록 바뀌는 경우 → 그때는 ⓐ 로 충분하다.

### A-#7
- 판정: ⓐ 치환
- 확신: 높음
- 사실 확인:
  - results 는 6줄 12건이다(`125205`·`140939`·`143218` 의 `H02.out.{1,2}.txt`). S-red 브랜치에도 같은 6파일이 각 1줄이고, 174808 은 0건이다(`git grep` 재확인).
  - prd 4줄: `specs/stage3-login-hardening.md:7`, `rounds/R-STAGE3-LOGIN-HARDENING.md:14`, `rounds/R-SELECTED-PREVIEW-TIMING.md:55`, `rounds/R-SELECTED-PREVIEW-TIMING-PR.md:23`.
  - intent 는 `/home/user/` 만 있다(allow).
  - `home_path_allow` 는 `harness.yaml:101` 에 있다.
- 이유:
  - ⓑ 는 실행자 홈을 계약 파일에 싣는다. allow 는 exact 대조라 구성원마다 한 줄씩 늘어난다. 같은 보호가 아니라 검사를 무력화하는 방향이다.
  - 치환 대상은 모두 해시 집합 밖이고, 승인 intent 도 아니라 append-only 대상이 아니다.
- 위험·전제: 증거 원문(모델 응답)을 편집하게 된다. 커밋 본문에 치환 명령 원문과 red 16건 로그를 남겨 추적성을 유지해야 한다.
- 뒤집힐 조건: 치환 대상 중 승인 intent 나 서명 결속 증거(hash 로 참조되는 파일)가 발견되는 경우

### 묶음 메모
- #1 과 #1a: 10-02 전 회차 불가는 모델과 무관하다(`:628` 429 는 opus 회차에서 발생). #1 ⓑ 이면 spec §4.1 「값 = 우려 #1 판정」, §6 비용, T12 액수(≈8 USD), `README.md:64` 예산 근거 문구를 함께 고쳐야 한다.
- #2 는 전제가 폐기됐다. spec A `:4`·`:117`·T13 「B 보다 먼저」와 §9 「B 와의 병합 순서」를 삭제한다. 순서는 intent `:629` 의 B 선행을 따른다.
- #4 는 spec B 우려 #5 와 얽힌다. B 가 제안하는 「A 에 `dev-package/reports/harness` 1토큰 추가」는 그 하위에 이미 홈 경로 5파일이 있어, 정리를 먼저 하지 않으면 A 의 `harness-contract` 를 red 로 만든다. B #5 판정 때 이 조건을 넣어야 한다.
- #6 의 새 선택지는 #5 와 맞물린다. 모델 불일치는 요약줄 `준비 ≥1` 로 나타나고, 게이트 실행 모드 정규식 `준비 0` 이 이를 잡는다. #5 에서 정규식을 갱신할 때 이 경로를 셀프테스트 케이스 하나로 함께 단언한다.
- #3 과 #2: 축소 뒤에는 제품 PR 과 B 모두 해시 집합 밖이다. A 회차는 1회로 끝나고, 10-02 뒤 S-red 회차 → S-red 병합 → A 레인 착수 순서만 남는다.
