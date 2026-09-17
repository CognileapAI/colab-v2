# Intent: spec 이 증거 계약 밖에 있다 — 의도인지 누락인지 정한다
메타 — 발의자: Claude(researcher 인계 실패 관측) · 방향 결정: Ted · 작성 2026-09-17 · 승인: 미승인 — Ted 승인 대기

## 문제
- `scripts/harness/hooks/lifecycle_contract.py:23` 의 `WATCH` 는 `('dev-package/sessions/', 'dev-package/reports/', 'dev-package/intent/')` 셋이다. **`dev-package/prd/specs/` 가 없다.**
- 오늘 관측된 결과: `dev-package/prd/specs/` 에 spec 을 쓴 researcher 가 그것을 task 산출물로 선언하지 못했고, task 를 `--mode read-only` 로 닫았다. **그 spec 에는 수명주기 증거가 없다** — 누가 어느 run 에서 만들었는지 기계가 아는 기록이 없다.
- 신규 산출물 경로는 `runtime:artifacts/<이름>` 형식만 받는다. `scripts/harness/task_state.py:61-63` 의 `relative_artifact()` 가 `runtime:artifacts/` 접두사가 아니면 `ValueError('new artifact must use runtime:artifacts/<name> (legacy needs --legacy)')` 를 던진다.
- 즉 `WATCH` 와 `relative_artifact` 는 서로 다른 두 축이다. `WATCH` 는 커밋 트리에서 감시할 경로, `relative_artifact` 는 task run 디렉터리 안의 산출물 이름. spec 은 **양쪽 어디에도 자리가 없다.**

## 원한 결과 (proposed outcome)
- spec 이 증거 계약 안에 있는지 밖에 있는지가 문서로 확정된다. 지금은 답이 없는 것이 아니라 **질문이 제기된 적이 없다.**

## 영향 범위
- `scripts/harness/hooks/lifecycle_contract.py:23` (선택지 a 를 택할 경우)
- `docs/development/lifecycle-evidence.md` — 어느 산출물이 증거 대상인지 규정하는 자리.
- `.agents/roles/researcher.md` — spec 을 쓰는 역할의 종료 절차.
- 계약 파괴 여부: 아니오. 다만 (a) 를 택하면 기존 `dev-package/prd/specs/` 커밋들이 소급으로 감시 대상이 된다.

## 제약
- `WATCH` 에 경로를 더하면 그 경로의 **모든** 변경이 task 선언을 요구한다. `dev-package/prd/specs/` 에는 과거 spec 이 다수 있고, 사람이 손으로 고치는 경우도 계약 위반이 된다.
- `runtime:artifacts/` 는 task run 디렉터리 안(체크아웃 사설 git 디렉터리)이고 `dev-package/prd/specs/` 는 커밋되는 트리다. 두 자리의 목적이 다르므로 spec 을 `runtime:artifacts/` 로 옮기는 것은 답이 아니다.

## 설계트리 (grill-me 결과)
- Q0 근본 질문 — spec 은 증거를 지닌 산출물인가, 계약 밖에 사는 기획 문서인가 → A **증거를 지닌 산출물이다.** spec 은 lane-worker 가 구현의 근거로 읽는 입력이고, 구현이 spec 을 벗어났는지 판정하려면 "어느 spec 을 어느 run 이 만들었는가"가 필요하다. `intent/` 가 이미 `WATCH` 안에 있는데 그 intent 를 구현 가능한 형태로 옮긴 spec 이 밖에 있는 것은 일관되지 않는다. intent 와 spec 은 같은 계보의 두 단계다.
- Q1 (b) spec 을 `dev-package/reports/` 로 옮기는가 → A 아니다. `prd/specs/` 는 의미 있는 이름이고 `reports/` 는 조사 산출물 자리다. 증거 계약을 만족시키려고 문서 분류를 무너뜨리는 것은 꼬리가 개를 흔드는 것이다.
- Q2 (c) 의도적으로 밖에 두고 문서화하는가 → A 아니다. Q0 의 답과 모순된다. 다만 이 선택지를 택한다면 `docs/development/lifecycle-evidence.md` 에 "spec 은 증거 대상이 아니다"를 명문화해야 한다 — 지금처럼 침묵으로 밖에 있는 상태는 어느 쪽도 아니다.
- Q3 (a) `WATCH` 에 `dev-package/prd/specs/` 를 더하는가 → A **권장.** 단 제약의 소급 문제를 함께 푼다.
- Q4 소급 문제를 어떻게 푸는가 → A 미해결. `WATCH` 가 신규 파일만 보는지 수정까지 보는지에 달렸다.

## 미해결 질문
- `WATCH` 가 신규 추가만 보는지 기존 파일 수정까지 보는지 미확인. `scripts/harness/hooks/lifecycle_contract.py:23` 의 `WATCH` 소비 지점(같은 파일 내 `stop` 경로)을 열어 확인해야 (a) 의 소급 비용을 산정할 수 있다.
- researcher 가 spec 을 `runtime:artifacts/` 에 먼저 쓰고 커밋 시 `prd/specs/` 로 승격하는 2단 경로가 가능한지 미검토. `scripts/harness/task_state.py:61-63` 과 `docs/development/lifecycle-evidence.md` 의 handoff 절차를 대조한다.
- 오늘 read-only 로 닫힌 그 task 의 task_id 미기록. 해당 spec 파일 경로도 미확정.

## 범위 밖 (명시 제외)
- 기존 `dev-package/prd/specs/**` 파일에 소급 증거를 만들어 붙이는 일.
- `runtime:artifacts/` 접두사 규약 자체의 개정.
- `dev-package/prd/rounds/`·`work-items.yaml` 등 다른 미감시 경로의 처리.
- 커밋·push·PR 게시·배포·이슈 댓글·종결.

## 확인
- Ted 확인 문장: 대기 중.
- 승인 필요 지점:
  - spec 을 증거를 지닌 산출물로 볼 것인가(Q0). 이 답이 (a)/(c) 를 가른다.
  - (a) 를 택할 경우 기존 spec 파일 수정에 task 선언을 요구하는 소급 비용을 감수하는가.

## 참조
- 감시 경로: `scripts/harness/hooks/lifecycle_contract.py:23`
- 산출물 경로 규약: `scripts/harness/task_state.py:61-63`
- 수명주기 규정: `docs/development/lifecycle-evidence.md`
- 역할: `.agents/roles/researcher.md`
- 관측: 2026-09-17, researcher 가 spec 을 `dev-package/prd/specs/` 에 쓰고 task 를 `--mode read-only` 로 종료
- spec: 미작성. Ted 승인 뒤 합성한다.
