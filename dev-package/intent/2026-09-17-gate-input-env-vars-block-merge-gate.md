# Intent: 운영자 입력 미선언 3건이 병합 진입 조건을 영구 불충족으로 만든다
메타 — 발의자: Claude(전수 게이트 관측) · 방향 결정: Ted · 작성 2026-09-17 · 승인: 미승인 — Ted 승인 대기

## 문제
- 이 호스트에서 `gates/run.sh all -j 4` 전수 결과는 `green 68 / red(판정) 0 / red(준비) 3`, 종료코드 1 이다. red(준비) 3건 전부 `cause=입력미선언`이다.
  - `seed-plan-drift` — `COLAB_REF_ROOT` 미선언(`gates/run.sh:232`, `gates/README.md:47`)
  - `frontend-visual` — `COLAB_VISUAL_URLS` 미선언(`gates/run.sh:324`, `gates/README.md:39`)
  - `harness-eval` — `COLAB_HARNESS_EVAL` 미선언(`gates/run.sh:337-338`, `gates/tools/harness-eval.sh:57-58`·`:99-100`)
- 병합 진입 조건은 `red_판정 == 0` **과** `red_준비 == 0` 둘 다다(`gates/README.md:112`, ADR-0004).
- 이 셋은 브랜치 내용과 무관한 **호스트 환경변수**다. 변수를 선언하지 않은 호스트에서는 어떤 브랜치도 병합 진입 조건을 만족할 수 없다. 조건이 엄격한 것이 아니라 **충족 불가능**하다.
- 정정: 세 게이트 모두 **명시 면제 변수를 이미 설계에 갖고 있다.** `COLAB_SEED_PLAN_NO_FILES=1`(`gates/README.md:47`) · `COLAB_VISUAL_EXEMPT=1`(`:39`) · `COLAB_HARNESS_EVAL_EXEMPT=1`(`gates/tools/harness-eval.sh:58`·`:90`). 즉 입력의 세 상태(선언 / 명시 면제 / 무언 → red(준비))는 **의도된 설계**이고, red(준비) 3건은 결함이 아니라 "아무 말도 안 하고 돌렸다"의 정상 출력이다.

## 원한 결과 (proposed outcome)
- 전수 호출이 세 변수에 대해 선언이든 명시 면제든 **말을 하도록** 규정되고, 그 호출문이 한 자리에 문서화된다.
- 병합 진입 조건 `red_준비 == 0` 은 그대로 둔다. 면제를 선언하면 충족된다.

## 영향 범위
- 문서: `gates/README.md` 의 "돌리기 전"(`:54`) 절에 전수 호출 정본 한 줄 추가.
- `docs/development/dual-agent.md` 의 전수 게이트 명령, `.agents/roles/measurement-lane.md` 의 실행 절차.
- 코드 변경 없음. 게이트 판정부·`gates/run.sh` 를 고치지 않는다.
- 계약 파괴 여부: 아니오.

## 제약
- `AGENTS.md:46` — 명시적 면제는 건수·사유를 드러내야 한다. 세 게이트의 면제 경로는 이미 건수를 출력한다(`harness-eval.sh:90` 은 면제인데 과제 0건이면 red 로 잡는다). 면제가 green-by-skip 이 되지 않도록 설계돼 있다.
- `COLAB_HARNESS_EVAL=1` 은 **실제 모델을 호출한다.** 시간·달러 상한(`COLAB_EVAL_TIMEOUT`·`COLAB_EVAL_BUDGET`) 미선언은 다시 red(준비)다(`gates/README.md:43`). 전수 회차마다 켤 수 없다. `gates/README.md:43` 은 로컬 `all` 과 CI 가 **면제 모드**로 도는 것이 현 규정임을 명시한다.
- `COLAB_REF_ROOT` 만은 문서화된 기본 경로가 있다 — 본 체크아웃과 나란한 `03 Reference-Data`(`dev-package/tools/dev-seed/README.md:29`, `build_plan.py:126`·`:451`). 이 호스트에 실물이 있으면 면제 대신 실선언이 가능하다.

## 설계트리 (grill-me 결과)
- Q1 (b) 게이트가 변수 부재 시 기본값을 자급하게 하는가 → A 아니다. 아무것도 검사하지 않으면서 green 을 내는 게이트가 된다. 이 레포가 `SKIP` 을 없앤 이유 그대로다(`gates/README.md:99`).
- Q2 (c) 병합 진입 조건을 고쳐 준비 red 를 비차단으로 돌리는가 → A 아니다. `red_준비` 를 조건에서 빼면 DB 미기동·도구 부재 같은 진짜 준비 실패까지 함께 통과한다. ADR-0004 의 근거를 무너뜨린다.
- Q3 (a) 세 변수를 필수 호스트 준비물로 문서화하고 실제로 설정하는가 → A `COLAB_REF_ROOT` 는 그렇다. 나머지 둘은 안 된다. `COLAB_VISUAL_URLS` 는 앱 기동이 전제고 `COLAB_HARNESS_EVAL=1` 은 매 회차 유료 모델 호출이다.
- Q4 (d) 명시 면제로 선언하는가 → A **권장.** 기존 설계가 정확히 이것을 위해 만들어졌고, 면제 경로가 건수를 드러내며(`AGENTS.md:46` 충족), 판정 코드를 한 줄도 건드리지 않는다.
- Q5 그러면 고칠 것이 무엇인가 → A 코드가 아니라 **호출문의 부재**다. 전수 회차의 정본 호출 한 줄이 어디에도 문서화돼 있지 않아 사람마다 맨몸으로 `gates/run.sh all` 을 친다.

## 미해결 질문
- 이 호스트에 `03 Reference-Data` 실물이 있는지 미확인. 있으면 `seed-plan-drift` 는 면제가 아니라 실선언으로 돌려야 한다. `dev-package/tools/dev-seed/README.md:29` 의 기본 경로를 확인한다.
- 정본 호출문을 `gates/README.md:54` 에 둘지 `docs/development/dual-agent.md` 에 둘지 미정.

## 범위 밖 (명시 제외)
- `harness-eval` 실행 모드 승격. `gates/README.md:43` 이 과제 20건 3회 연속 2/2 green 뒤의 별건으로 못박았다.
- `gates/run.sh`·게이트 판정부 코드 수정.
- ADR-0004 병합 진입 조건 개정.
- 커밋·push·PR 게시·배포·이슈 댓글·종결.

## 확인
- Ted 확인 문장: 대기 중.
- 승인 필요 지점:
  - ⚠ **이 결정이 PR #113 의 병합 가부를 가른다.** 전수 회차에서 세 변수를 명시 면제로 선언하는 것을 병합 진입 조건 충족으로 인정하는가. 인정하지 않으면 #113 은 이 호스트에서 병합 진입 조건을 만족할 수 없다.
  - 정본 호출문을 `gates/README.md` 에 둘 것인가 `docs/development/dual-agent.md` 에 둘 것인가.

## 참조
- 병합 진입 조건: `gates/README.md:112` (ADR-0004)
- 상태값 규정: `gates/README.md:99` (`SKIP` 없음)
- 게이트 명세: `gates/README.md:39`(frontend-visual) · `:43`(harness-eval) · `:47`(seed-plan-drift)
- 러너: `gates/run.sh:232` · `:324` · `:337-338`
- 판정부: `gates/tools/harness-eval.sh:57-58`·`:90`·`:99-100`
- 기본 경로: `dev-package/tools/dev-seed/README.md:29`, `dev-package/tools/dev-seed/build_plan.py:126`·`:451`
- 면제 규정: `AGENTS.md:46`
- 관측: `gates/run.sh all -j 4`, 2026-09-17, `green 68 / red(판정) 0 / red(준비) 3`, 종료코드 1
- spec: 미작성. Ted 승인 뒤 합성한다.
