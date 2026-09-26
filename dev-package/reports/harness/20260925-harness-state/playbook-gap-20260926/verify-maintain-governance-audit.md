VERDICT: ACCEPT-WITH-CHANGES

For: 「없음」 4건 표본 전부 실측 일치 — ⑴ `.github/` 에 `schedule:`·dependabot·CodeQL·pip-audit 0건(M2·M4) ⑵ `scripts/harness/hooks/` 에 판정 로그 0(유일한 audit 은 `css-edit-audit.sh` = 제품 CSS 감사, G4) ⑶ `ci.yml:699` `COLAB_HARNESS_EVAL_EXEMPT: '1'` · 결과 회차 마지막 `20260912-211809`(D1) ⑷ `settings.json` 키 = effortLevel·worktree·hooks 뿐 · PreToolUse 3 훅 2행 모두 `COLAB_HOOKS=0` 조기 exit · `COLAB_FIX_LANE=1` 은 Codex 경로만(`test-file-guard.sh:26,42`)(G2). 순위 1(D1) 지목은 옳다.
Against: 제안 8건 중 절반이 「오케스트레이터 1인」 조건을 잊었다 — P4 의 30일 이동 중앙값·MAD 대역은 주 PR 몇 건 규모에서 통계량이 아니고, P3 의 `authorized_by` 는 항상 Ted 라 신원 필드가 아니라 timestamp 필드이며, P8 은 `git-guard.sh:86` 이 명시한 존재 이유(「오탐이 붙은 차단 훅은 `COLAB_HOOKS=0` 상시화로 끝난다」)를 오탐 데이터(P2) 없이 제거하려 한다. 분석 자체의 D3 판정(「evals ✗ → 전제 미충족」)이 P4·P5 의 PR 5 를 스스로 부정한다.

대조표 판정 — M1·M2·M4·M5·M7·G1·G4·D2·D3 유지 / M3 유지 / M6 조정(SLA 부재는 1인 체제에서 격차 아님, 기록 부재만 유지) / G2 유지 / G3 조정(「특정 사람」 요구는 1인 체제에서 timestamp 결속으로 축소) / S1 조정(`harness.yaml:125-130 transition.mode` 가 이미 선언이며 격차는 「종료 조건」뿐) / S2 유지 / D1 유지.
제안 판정:
- P1 조정 — 기제(runner `harness_hash` + `changes.harness` 분기) 유지. 배치 기각: `harness-eval.sh` 헤더·intent 2026-09-08 Q10 이 「실행 모드 전환 = 별건」으로 못박았으므로 T1 옆에 끼우지 말고 Q10 재개 결정 + 소형 PR 로 분리. 회차당 ≈32 USD × PR 4건 비용 승인은 Ted 몫.
- P2 유지 — 단 `git common dir` 은 저장소 밖(분석 G4 자체 지적)이므로 「audit 층」 충족 주장은 축소. 규칙별 차단·오탐 계수가 P8 의 전제 데이터.
- P3 조정 — Q6 ⓐ 와 중복. 별도 토큰 발급 스크립트 기각, pre JSON `authorized_at` 필드 1개만 Q6 ⓐ 소형 PR 에 편입.
- P4 기각(현 시점) — tier 2/3·cron·PR 5 는 1인 체제 scope creep · 대역 통계 무의미 · 분석 D3 와 자기모순. 수집 스크립트만 intent 후보로 기록.
- P5 유지 — 배치만 조정: PR 3 3-2 는 permissions/contract 범위라 N-8 재사용 근거 약함 → 독립 소형 PR.
- P6 조정 — `truth: repo` 선언은 게이트가 읽지 않으면 산문. 링크 조건 1개만 유지하되 intent 제도 이전 legacy 항목 red 방지용 날짜 컷오프 필수. `ledger_exit` 는 Ted 결정 전 기각.
- P7 유지 — 차단급. Ted 원칙 직접 위반 확인, PR 2 2-8 동일 파일.
- P8 조정 — 순서 강제: P2 로 오탐 계수 확보 뒤 제거. 킬스위치 제거 자체가 PR 3 병합 조건 ⑵ 의 유일한 실제 기제라는 점은 옳다(훅은 자기 생략을 감지 못함).
Risks: ⑴ P1 없이 PR 2–4 병합 시 eval 미측정 4회 누적 — 분석 X1 그대로 ⑵ P8 선행 시 정상 경로 오탐이 곧 사용자 우회 습관으로 회귀 ⑶ P6 컷오프 없으면 planning-gates 전면 red.
Missed(분석자가 건너뛴 playbook 항목, 기억 기반 `[미확인 원문]`): ⑴ skill/role trigger-accuracy eval — `eval/harness/results/activation-*.json` 5종이 이미 존재하는데 대조표에 0회 등장 ⑵ Ship 단계 rollback/canary — 릴리스 증거 pre/post 만 다루고 되돌림 경로 감사 미검토 ⑶ managed settings 부재 시 대체 — 1인 체제엔 조직 강제층이 없으므로 P8 이 유일 대체라는 판단이 X5 에 빠짐.
Fixes: 차단급 — P7 PR 2 2-8 편입 · P1 을 Q10 재개 결정으로 분리(T1 묶음 금지) · P6 날짜 컷오프. 개선 — P2→P8 순서 명문화 · P3 을 Q6 ⓐ 필드 1개로 축소 · P4 기각 후 수집 스크립트만 intent 후보 · P5 독립 PR · activation 결과 5종을 D1 행에 추가.