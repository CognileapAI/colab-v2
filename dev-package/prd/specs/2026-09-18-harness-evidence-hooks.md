# Spec: 하네스 증거 계약 3건 — 측정 레인 종료 훅 · spec 을 WATCH 안으로 · 전수 호출문 정본
출처 intent(전부 승인 2026-09-18):
- A `dev-package/intent/2026-09-17-measurement-lane-subagent-stop-hook.md`
- B `dev-package/intent/2026-09-17-spec-artifacts-outside-lifecycle-watch.md`
- C `dev-package/intent/2026-09-17-gate-input-env-vars-block-merge-gate.md`(미결 1건은 §C 에서 권고대로 확정)
근거 사슬: [ADR-0005](../../../docs/decisions/0005-harness-controls-are-declarative.md) 「2026-09-18 개정」의 후속 **③(WATCH)·④(측정 레인 SubagentStop)** ＋ C 의 문서 정본화. ADR-0006(본문 `.agents/`·`scripts/harness/` · `.claude/` 는 어댑터).

⚠ 세 건은 **한 레인·한 PR** 이다. A·B 가 같은 파일(`scripts/harness/hooks/lifecycle_contract.py` · `scripts/tests/*`)을 건드리고 C 는 문서 한 곳이다. 형제 spec `2026-09-18-gate-host-mutex.md`(ADR-0005 ②)와 **코드 표면은 독립이나 문서 3곳을 공유한다** — `gates/README.md` · `docs/decisions/0005-…md:58-60`(인접 행) · `R-HARNESS-PR-CENTRIC.md`. 레인은 **직렬**로 돌고 **이 spec 이 먼저**다. 이 레인은 자기 행(③④ · README 「돌리기 전」 항목 · 자기 R-HARNESS 행)만 건드린다. 게이트 회차는 두 레인이 겹치지 않게 오케스트레이터가 직렬화한다.
⚠ 정찰에서 intent 의 전제 2건이 실물과 달랐다. 아래 §A-1·§A-2 가 그 정정이며, 판정이 바뀌는 항목은 「우려 항목」에 올렸다.

## 문제 진술
- A. `measurement-lane` 은 전수를 재고 3계수·종료코드를 `gate-summary.json` 에 남기는 것이 산출물 전부인데, 그 존재를 기계가 확인하지 않는다. `.claude/settings.json:29-48` `SubagentStop` 에 `researcher`·`lane-worker` 매처만 있고 `measurement-lane` 은 없다. `.codex/hooks.json:42-65` 도 같다.
- B. `WATCH`(`lifecycle_contract.py:23`)는 `sessions/`·`reports/`·`intent/` 셋뿐이라 `dev-package/prd/specs/` 는 「산출물 범위」로 선언된 적이 없다. spec 은 lane-worker 가 구현 근거로 읽는 입력인데 증거 계약 밖에 산다(intent Q0 → 증거를 지닌 산출물이다).
- C. `seed-plan-drift`·`frontend-visual`·`harness-eval` 세 게이트는 운영자 입력(선언 또는 명시 면제)이 없으면 red(준비 · 78)이고, 그 호출문이 아무 데도 적혀 있지 않다. `gates/README.md:54` 「돌리기 전」 절은 `~/.colab-v2-test.env` 한 항목뿐이다(`:56`).

## 해법 개요
- A. 새 훅 파일 없이 `lane-gate-summary.sh` 를 **역할 집합**으로 일반화하고 매처를 `lane-worker|measurement-lane` 으로 넓힌다. 종료 시 `gate-summary.json` 이 있고 선언한 게이트 전부의 행·3계수·종료코드가 정합이며 트리 증거가 현재와 같으면 통과, 아니면 차단(exit 2). **red 가 있어도 통과한다 — red 를 재는 것이 이 역할의 임무다**(intent A 제약).
- B. `WATCH` 에 `dev-package/prd/specs/` 를 더하고, 「researcher 는 spec 을 쓰지 않는다 · 부모가 쓴다」를 문서와 legacy 선언 검사 양쪽에 일치시킨다.
- C. `gates/README.md` 「돌리기 전」 절에 전수 호출문 정본(선언형·면제형 두 줄)을 둔다. 코드 변경 없음.

## 사용자 스토리
1. 오케스트레이터로서 측정 레인이 「쟀다」고 말하면 그 증거 파일이 실제로 있기를 원한다, 보고를 믿지 않아도 되게.
2. 측정 레인으로서 red 가 나온 회차를 그대로 닫고 싶다, red 를 기록하는 것이 내 산출물이므로.
3. 부모로서 spec 이 증거 계약 안의 산출물이기를 원한다, researcher 가 spec 을 쓰고 read-only 로 닫는 경로가 성립하지 않게.
4. 게이트를 돌리는 사람으로서 전수 호출문 한 줄을 한 자리에서 복사하고 싶다, 세 변수를 매번 78 로 배우지 않게.

## 구현 결정

### A-1. 역할 인자는 매처에서 넘어올 수 없다 — 집합으로 일반화한다 (intent Q3 의 형태 정정)
- intent Q3 는 「`lane-gate-summary.sh:5` 의 고정 `--role lane-worker` 를 역할 인자로 받게」라 했다. 그런데 어댑터 문장은 `config.py:153` 이 `exec bash … "$@"` 한 줄로 고정하고, `.claude/settings.json` 의 command 는 `agent-bridge.py:67` 정규식이 **인자 없는 형태만** 허용한다. 매처에서 인자를 넘길 자리가 없다.
- 그래서 역할은 **이벤트 페이로드의 `agent_type`** 에서 온다. `lifecycle_contract.py stop --role` 을 반복 가능하게(`--role lane-worker --role measurement-lane`) 바꾸고, `stop()`(`:274-278`)은 `data['agent_type']` 이 그 집합 안이면 그 값을 `expected_role` 로 쓴다. `lane-gate-summary.sh:5` 는 두 역할을 나열한다. 새 훅 파일 없음 → `harness.yaml:48` `hook_names` 불변(intent Q3 「신규 훅 기각」 유지).
- 매처: `.claude/settings.json:40` → `"lane-worker|measurement-lane"`(매처는 정규식 fullmatch — `agent-bridge.py:63`). `.codex/hooks.json` 에 `measurement-lane` 항목을 `lane-worker`(`:54-63`) 와 같은 command 로 추가 — 훅 선택은 어차피 `dispatch_event`(`agent-bridge.py:314-318`)가 `.claude/settings.json` 에서 한다.
- 기존 `lane-worker` 경로의 판정은 한 글자도 바뀌지 않는다.

### A-2. 측정 레인의 완료 판정 — red 는 차단 사유가 아니다 (test 정정)
- `validate_report()`(`:238-239`)는 `red_판정`·`red_준비` 가 하나라도 있으면 `gate failures remain` 을 던지고, `scripts/tests/test_task_runtime.py:159-166` 은 측정 레인에서 **그 차단을 단언**한다. 이것은 PR #113 이 「stop() 의 lane 갈래로 자동으로 떨어진다」를 그대로 굳힌 것이며(55-56 spec 우려 #6), 승인된 intent A 제약(「red 판정으로 차단하면 역할이 성립하지 않는다」)과 정면 충돌한다. **승인 문면이 이긴다.**
- `validate_report(data, required, *, allow_red)` 로 분기한다. `measurement-lane` 은 `allow_red=True`. 나머지 검사(행 유효·중복 없음·상태∈`STATES`·`exit` 정수·green 이면 exit 0·계수=행 합·선언 게이트 전부 존재)와 `verify_task_report()` 의 트리 증거 대조(`:260-266`)는 **그대로 요구한다.** 즉 측정 레인이 못 닫는 경우는 「안 쟀다·덜 쟀다·다른 트리를 쟀다·계수를 손봤다」 넷뿐이다.
- `lane-worker` 는 `allow_red=False` 그대로. `test_task_runtime.py:159-166` 은 「red 행이 있어도 측정 레인은 H7 로 닫힌다 · 선언 게이트 누락은 여전히 막힌다 · lane-worker 의 red 는 여전히 막힌다」로 고쳐 쓴다.

### B. `WATCH` 확장 — 무엇이 실제로 바뀌는지를 정확히 적는다
- `lifecycle_contract.py:23` 에 `'dev-package/prd/specs/'` 추가. **한 줄.**
- 실물 대조 결과, 이 한 줄이 바꾸는 판정은 둘이다. ⑴ researcher `artifacts` 모드(`:308-312`)에서 `prd/specs/` 변경이 「범위 밖」(`:310`)이 아니라 「미인계 산출물」(`:312`)로 분류된다 — colab-task/2 의 `task['artifacts']` 는 런타임 절대경로(`task_state.py:77`)라 트리 경로와 부분집합이 될 수 없으므로 **어느 쪽이든 차단**이고 사유 문장만 달라진다. ⑵ legacy `begin --legacy` 의 산출물 선언(`:189`)이 `prd/specs/` 를 **허용하게 된다.**
- `read-only`·`draft-return`(`:305-307`)은 `snapshot()`(`:86-92`, `git ls-files --cached --others`)이 트리 전체를 보므로 **오늘도 어떤 변경이든 막는다.** 따라서 intent 의 9/17 관측(researcher 가 spec 을 쓰고 read-only 로 닫았다)은 `WATCH` 로 설명되지 않는다 — 레인이 먼저 재현한다(우려 #2).
- ⑵ 는 두 Ted 문면이 **서로 어긋나는 자리**다. `docs/development/lifecycle-evidence.md:12-13`(Ted · 2026-09-09 · `3e5be9dc`)은 「researcher 산출물은 sessions/reports/intent 로 제한 · specs 를 추가해 통과시키지 않는다」이고, intent B Q4(Ted · 2026-09-18)는 「기존 `prd/specs/**` 를 고치는 researcher 도 task 선언을 해야 한다 — 그것이 원하는 바다」로 researcher 의 spec 선언을 **전제**한다. 나중 문면이 이기는 것이 원칙이나 intent B 는 `:12-13` 을 폐기한다고 적지 않았다. **Ted 판정(우려 #3)** 전까지 레인은 `:189` 를 건드리지 않고 `WATCH` 한 줄만 넣는다.
- 문서: `lifecycle-evidence.md` 에 「`prd/specs/` 는 WATCH 안의 산출물이다」 한 문장을 더하고, `:12-13` 은 우려 #3 판정에 따라 ⓐ 그대로 두거나 ⓑ 「researcher 는 legacy 선언으로만 spec 을 쓴다」로 고친다. `.agents/roles/researcher.md:27` 도 같은 판정을 따른다. intent B 의 「소급 비용」 문장은 실물대로 적는다 — 훅이 도는 것은 researcher 종료뿐이며 사람·부모의 spec 편집은 훅 대상이 아니다.
- `lifecycle-evidence.md:13` 「부모의 spec 인계는 승인 범위·파일 경로·실제 내용 hash 를 확인한다」는 **어디에도 구현돼 있지 않다.** intent B 가 요구하지 않았으므로 범위 밖으로 두고 드러낸다.
- intent B ⑴ 2단 승격 경로: 승격 함수가 존재하지 않는다(`write-artifact` `:484-490` · `archive_report` `:133-156` 이 가장 가깝다). **범위 밖.**

### C. 전수 호출문 정본 — `gates/README.md` 「돌리기 전」(미결 1건 권고대로 확정)
- 자리: `gates/README.md:56` 아래 두 번째 항목 ＋ 코드 블록. `dual-agent.md` 에는 본문을 복제하지 않되, `:138` 의 단독 게이트 명령 옆에 이 절을 가리키는 **링크 한 줄**을 둔다(intent C 영향 범위가 그 자리를 들었다).
- 내용: 정본 한 줄 = `COLAB_REF_ROOT=<참조 데이터 루트> COLAB_VISUAL_EXEMPT=1 COLAB_HARNESS_EVAL_EXEMPT=1 bash gates/run.sh all`(측정 레인은 `COLAB_TASK_ID=<id> bash gates/run.sh task`). **`seed-plan-drift` 는 면제가 아니라 실선언이다** — intent C 「닫힌 것」(`:43`)이 참조 데이터 실물을 확인하고 그렇게 못박았다. 명시 면제는 `frontend-visual`·`harness-eval` **2건**. 선언형(`COLAB_VISUAL_URLS=<url…>` · `COLAB_HARNESS_EVAL=1`)은 그 아래 「대신 실행하려면」으로 적는다. 「면제도 병합 진입 조건 충족이다(intent C 결정) · 면제 건수는 해당 게이트 출력에 드러난다」 한 문장.
- 소비처 앵커(레인이 실물 대조): `seed-plan-drift.sh:72-73`·`:104` / `frontend-visual.sh:46-48`·`:54-55` / `harness-eval.sh:57-58`·`:87-95`·`:99`.
- 코드 변경 없음. `.agents/roles/measurement-lane.md:34` 는 이 절을 가리키는 한 줄만 더한다(우려 #4).

- 모듈 · 인터페이스: `scripts/harness/hooks/lifecycle_contract.py`(`stop` 역할 집합 · `validate_report` 분기 · `:189` 역할 조건 · `WATCH`) · `scripts/harness/hooks/lane-gate-summary.sh` · `.claude/settings.json` · `.codex/hooks.json` · 문서 4곳.
- 스키마 · 마이그레이션: 없음. `colab-task/2`·`colab-gate-summary/1` 불변.
- API 계약: 비파괴. `stop --role` 은 단일 인자 호출이 그대로 동작한다.

## 시험 결정
- 재사용 seam: `scripts/tests/test_task_runtime.py`(측정 레인 Python 수준 `:121-182`) · `scripts/tests/test_harness_lifecycle_contract.py`(`hook()` `:35-46` 이 stdin 페이로드를 `bash .claude/hooks/<name>` 에 먹이고 `assert_routes()` `:69-74` 가 claude·codex 두 경로를 돈다 — `:70` 의 역할→훅 표를 `measurement-lane` 까지 넓힌다).
- 외부 행위 기준 검증 항목:
  - A-ⓐ 측정 레인 페이로드 ＋ 정합한 `gate-summary.json`(red 1건 포함) → claude·codex 두 경로 모두 exit 0.
  - A-ⓑ 보고 파일 없음 / 선언 게이트 1건 누락 / 계수≠행 합 / 트리 불일치 → exit 2.
  - A-ⓒ `lane-worker` 페이로드 ＋ red 1건 → 여전히 exit 2(회귀).
  - A-ⓓ `agent_type` 이 집합 밖(`researcher`)인 페이로드가 이 훅에 오면 `hook role differs` 로 exit 2.
  - B-ⓐ researcher 가 `dev-package/prd/specs/x.md` 를 쓰고 `read-only` → 2. `artifacts`(런타임 산출물 선언) → 2, 사유가 `unhanded output`. **둘 다 오늘도 2 다** — 이 케이스는 WATCH 확장이 「바꾼」 판정이 아니라 「고정하는」 계약 시험이다.
  - B-ⓑ researcher `begin --legacy` 로 `dev-package/prd/specs/x.md` 선언 → 우려 #3 판정 ⓐ 면 **허용**(WATCH 안이므로), ⓑ 면 거절. lane-worker 의 같은 선언은 기존 동작 유지. 판정 전에는 이 케이스를 쓰지 않는다.
  - C-ⓐ README 의 정본 한 줄을 실제로 실행해 `seed-plan-drift`(실선언) green · `frontend-visual`·`harness-eval`(면제) 이 red(준비) 0 ＋ 각자 출력에 면제 건수 표시.
- 해당 서비스 단독 게이트 이름: `agent-bridge`(`gates/run.sh:218-220` — `test_harness_lifecycle_contract`·`test_task_runtime`·`test_harness_source_layout`) · `harness-contract`(어댑터·훅 정합) · `harness-contract-selftest`.
- green-by-skip 방지: A-ⓐ 의 보고에 **red 행이 반드시 1건** 들어간다 — all-green 픽스처만으로는 §A-2 의 분기가 있는지 없는지 구분되지 않는다. B-ⓐ 는 파일을 실제로 쓴다.

## 커밋 순서 (레인이 그대로 따른다)
1. §A-2 `validate_report` 분기 ＋ `test_task_runtime.py:159-166` 정정 — 판정 본문부터.
2. §A-1 `stop` 역할 집합 ＋ `lane-gate-summary.sh` ＋ `.claude/settings.json` 매처 ＋ `.codex/hooks.json` 항목 ＋ `test_harness_lifecycle_contract.py` 경로 시험.
3. §B `WATCH` 한 줄 ＋ 시험 B-ⓐ ＋ `lifecycle-evidence.md` 한 문장. (`:189` 역할 조건·B-ⓑ·`:12-13` 개정은 우려 #3 판정 뒤 같은 커밋에 얹거나 뺀다.)
4. §C README 절 ＋ `dual-agent.md:138` 링크 한 줄 ＋ measurement-lane 역할 한 줄 ＋ ADR-0005 ③④ 갱신 ＋ 라운드 파일.

## 완료 조건 (레인이 스스로 대조한다)
1. 측정 레인이 red 를 포함한 정합 보고로 닫히고, 보고 없이는 못 닫는다(A-ⓐⓑ, claude·codex 두 경로).
2. `lane-worker` 판정 무변경(A-ⓒ).
3. `prd/specs/` 가 WATCH 안에 있고, researcher 의 colab-task/2 종료는 `prd/specs/` 변경을 어느 모드에서도 통과시키지 않는다(B-ⓐ). legacy 선언의 허용 여부는 우려 #3 판정대로(B-ⓑ).
4. README 의 정본 한 줄이 실제로 돌아 세 게이트 red(준비) 0 · 면제 2건 표시(C-ⓐ).
5. `agent-bridge`·`harness-contract`·`harness-contract-selftest` green.

## 검증 계획
### ① 단독 게이트로 증명하는 것
- `agent-bridge` green — A·B 의 전 케이스가 여기 산다.
- `harness-contract`·`harness-contract-selftest` green — 매처 변경이 `agent-bridge.py:63-69` 파싱을 깨지 않는다.
- C-ⓐ: `seed-plan-drift`·`frontend-visual`·`harness-eval` 을 정본 한 줄로 단독 실행(`frontend-visual`·`harness-eval` 은 `serial` 선언 — 형제 spec 병합 전까지는 사람이 단독을 지킨다).
### ② 호스트 독점 전수 실행으로만 증명되는 것
- 전수 1회, **README 의 정본 호출문 그대로**. 요약에 red(준비) 0 ＋ 면제 2건. 이 회차의 `gate-summary.json` 이 곧 A 의 실물 픽스처 형태다.
### ③ 하지 않는 것
- 실제 `measurement-lane` 서브에이전트를 띄워 훅을 발화시키는 것. `hook()` 시험이 같은 stdin 페이로드로 같은 스크립트를 부른다(`test_harness_lifecycle_contract.py:35-46`). 실발화는 다음 측정 레인 회차가 자연히 한다.
- 모델 호출 `harness-eval` 의 선언형 실행. 면제형만 돈다(구독 CLI 예산 질의 금지 — product.md §5-b).
- 실브라우저 검증. UI 변경 0건.

## 정책 대조 (작성 시점 제약)
대조 원본 `.agents/rules/product.md` §3·§5 — **원문을 직접 읽었다.**
- §3-1~7: **저촉 없음.** 하네스 파이썬·셸·설정·문서만 바뀐다. 제품 코드·DB·계약 0건.
- §3-8 절대경로: **준수.** 런타임 절대경로는 코드가 만드는 값이고 문서엔 접두사 규약만 적는다.
- §5 게이트 우회·비활성화: **반대 방향.** 다만 §A-2 는 「red 가 있어도 닫힌다」라 표면상 완화로 보인다 — 완화가 아니라 **역할 정의**다. lane-worker 의 red 차단은 그대로이고, 측정 레인은 red 를 **기록하는** 역할이지 green 을 만드는 역할이 아니다(intent A 제약 · `.agents/roles/measurement-lane.md`).
- §5 「나중에」: **부분 해당 — 드러낸다.** ⓐ `lifecycle-evidence.md:13` 의 hash 확인 미구현 ⓑ 역할↔훅 대응의 `harness-contract` 강제(intent A Q4 별건) ⓒ `agent-bridge.py:80` `check()` 가 `measurement-lane` toml 을 검사하지 않음(기존 공백).
- §5 범위 늘리기: **저촉 없음.** 세 intent 의 승인 절 안이다. §A-1 의 형태 정정은 결정(일반화·신규 훅 기각)을 바꾸지 않고 수단만 바꾼다.
- 계약 동결 해제 필요: **아니오.**
- 결정 로그: 신규 legacy 결정번호·새 ADR·GitHub 이슈 없음. ADR-0005 `:58-60` 의 ③④ 를 완료로 갱신한다.
### 디자인 제약 확인
**해당 없음.** 화면 코드 0건.

## 우려 항목 (판정 필요)
| # | 항목 | ⓐ | ⓑ | 권고 |
|---|---|---|---|---|
| 1 | 측정 레인의 red 허용(§A-2)은 PR #113 의 시험 단언을 뒤집는다. 승인된 intent A 제약이 근거이지만, #113 spec 우려 #6 은 「의도한 결과」라고 적었다. 둘 중 어느 문면이 결정인가. | intent A 제약대로 — 측정 레인만 red 허용, 구조·트리 증거는 전부 요구 | #113 대로 red 차단 유지 — 그러면 측정 레인은 all-green 회차만 닫을 수 있어 역할이 성립하지 않는다 | ⓐ — intent A 가 나중 승인(9/18)이고 역할 정의와 일치한다 |
| 2 | 9/17 관측(researcher 가 spec 을 쓰고 read-only 로 닫았다)은 현재 코드로 설명되지 않는다 — `snapshot()` 이 트리 전체를 보므로 read-only 는 어떤 변경이든 막는다. 훅이 발화하지 않았거나 다른 경로였을 개연이 있다. | 레인이 먼저 재현을 시도하고, 재현되면 그 원인을 이 PR 에서 닫는다 · 안 되면 「WATCH 는 선언적 정합」으로 범위를 명시한다 | 재현 없이 WATCH 한 줄만 넣는다 | ⓐ — 「고쳤다」를 재현 없이 적지 않는다 |
| 3 | **(Ted 판정 필요 — 레인 착수 전)** researcher 가 spec 을 쓸 수 있는가. intent B Q4(9/18)는 「`prd/specs/**` 를 고치는 researcher 도 task 선언을 해야 한다 — 그것이 원하는 바다」로 **전제**하고, `lifecycle-evidence.md:12-13`(9/09)은 「researcher 는 specs 를 추가해 통과시키지 않는다 · 부모가 쓴다」로 **금지**한다. colab-task/2 에서 researcher 는 트리 경로를 선언할 수 없으므로(`task_state.py:66-68`) 「researcher 가 spec 을 쓴다」는 legacy 선언으로만 가능하다. | intent B 대로 — WATCH 안이므로 legacy 선언 허용, `:12-13` 을 「legacy 선언으로만」으로 개정 | `:12-13` 대로 — `:189` 에 역할 조건 한 줄, researcher 는 어느 schema 에서도 `prd/specs/` 를 선언하지 못한다 | ⓑ — 이 spec 자체가 `:12-13` 의 절차(부모가 쓴다)로 만들어졌고, 9/17 관측이 문제였던 이유도 researcher 의 spec 쓰기였다. 그러나 두 문면 모두 Ted 의 것이라 spec 이 고를 수 없다 |
| 4 | `.agents/roles/measurement-lane.md:34` 가 환경변수를 하나도 이름하지 않는다 — 측정 레인이 78 을 만나는 실제 자리. intent A 는 「역할 본문 변경」을 범위 밖으로 뒀다. | README 절을 가리키는 한 줄만 더한다(intent C 의 문서화 범위로 본다) | 건드리지 않는다 | ⓐ — 한 줄 링크는 역할 정의 변경이 아니다 |
| 5 | `stop --role` 을 집합으로 받으면 `data['agent_type']` 이 곧 판정 역할이 된다. 페이로드를 위조한 프로세스가 역할을 고를 수 있다. | 그대로 간다 — ADR-0005 「훅은 신뢰 경계가 아니다」. 어차피 `:295` 가 task 기록의 역할·agent_id 와 대조한다 | 어댑터 규약을 바꿔 인자를 허용 | ⓐ — ⓑ 는 `config.py:153`·`agent-bridge.py:67` 두 규약을 흔든다 |

## 범위 밖
- (A 승계) 역할↔훅 매처 대응의 `harness-contract` 강제 · `measurement-lane` 역할 본문·권한·모델 변경(§C 의 링크 한 줄 제외).
- (B 승계) 기존 `prd/specs/**` 소급 증거 · `runtime:artifacts/` 규약 개정 · `rounds/`·`work-items.yaml` 등 다른 미감시 경로 · ⑴ 2단 승격 경로.
- `lifecycle-evidence.md:13` 부모 spec 인계 hash 확인의 구현. `agent-bridge.py:80` `check()` 의 역할 목록 보강.
- ADR-0005 ② 호스트 뮤텍스 — 형제 spec.
- 커밋·push·PR 게시·이슈 댓글. PR 게시는 사용자가 한다.

## 산출 계획
- 라운드 파일: `dev-package/prd/rounds/R-HARNESS-EVIDENCE-HOOKS.md`(≤300행, 첫 줄에서 이 spec 을 링크). 미작성 — 레인 커밋 4 에서 쓴다. `R-HARNESS-PR-CENTRIC.md` 에 한 행 추가.
- 예상 레인 수: **1 (직렬).** A·B 가 같은 파이썬 파일·같은 시험 파일이다.
- 커밋 4개, PR 1건.
- 게이트 3계수·종료코드 · 전수 1회 요약(면제 3건 표시) · A-ⓐ 픽스처의 red 행 · 사용자 게시용 로컬 PR 요약(저장소 밖)을 남긴다.

## 미확인 (레인이 구현 전에 확인한다)
1. ~~`.codex/hooks.json` command 가 매처 문자열을 품는지~~ → 닫혔다. `:59` command 는 매처를 품지 않고 `dispatch_event:314-318` 이 `.claude/settings.json` 에서 훅을 고른다 — 항목 복제로 충분.
2. 면제 건수 표기의 실제 자리 — `run.sh:338`·`:344`·`:352`·`:359` 주석대로 **각 게이트 출력**에 나온다. 전수 요약(`:804` 이하)에는 면제 줄이 없다. C-ⓐ·완료 조건 4 의 「면제 2건 표시」는 두 게이트의 stdout 으로 확인한다.
3. `test_harness_lifecycle_contract.py` 의 codex 경로가 `.codex/hooks.json` 을 실제로 읽는지, `agent-bridge.py dispatch_event` 만 도는지 — 후자면 codex 항목 추가의 증명은 `harness-contract`(required_files 파싱)뿐이다.
