CROSS: ISSUES 3
- A-#4 × B-#5 — B-#5는 A에 `dev-package/reports/harness/20260925-harness-state` 토큰 하나를 더하는 것을 전제로 하고, 스스로 「spec A 판정에서 확인받아야 함」이라고 남겼다. 그런데 A-#4는 「확정 3개만」으로 닫았다(spec A V-A7의 roots 9개와 `agent-bridge.yml` paths 3줄이 이 전제다). 그래서 B-#5는 아직 열린 판정이다. A-#4가 걱정한 red 전환은 상위 토큰 `dev-package/reports/harness`(홈 경로가 남은 5파일) 기준이라 이 하위 토큰에는 해당하지 않는다. — A-#4를 「확정 3개 + B 반입 디렉터리 1개」로 고친다. 함께 바꿀 것은 V-A7의 roots 10과 green 줄 `home-path roots 10`, `agent-bridge.yml` paths 1줄 추가다. spec A `:99`의 「`dev-package/reports/x.md`는 잡히지 않음」 단언은 그대로 둔다.
- B-#5 × intent `:629`(B 선행) — B-#5의 「A가 먼저 병합돼도 green」은 확정된 순서와 반대 경우를 가정한다. 실제 순서에서는 A가 병합되는 순간 새 토큰이 B의 반입물을 곧바로 검사한다. B에서 1회 돌린 검사와 `check_home_paths`(`config.py:29-33`의 4가지 꼴과 `home_path_allow` exact 대조)의 판정이 어긋나면 A가 red가 된다. — V-B9의 「grep = 0」을 「`check_home_paths`와 같은 식으로 셌을 때 0건(`/home/user/`는 allow)」으로 바꾼다. 원본에 남은 `/home/user/`와 V-B9가 서로 모순되는 문제도 이 변경으로 함께 풀린다.
- B-#1 보정 ⑵ — 스냅샷이 없을 때 legacy 규칙을 모든 intent에 적용하면, 확정된 Q4 「`classify`는 그 꼴만 승인」보다 범위가 넓어진다. 근거로 든 「갱신하지 않은 브랜치의 로컬 green / CI red」도 코드와 맞지 않는다. 갱신하지 않은 브랜치는 로컬에서 자기 브랜치의 구 `intent_ref.py`를 돈다. CI는 `actions/checkout@v4` 기본값(`ci.yml:667-669`, ref 미지정 = PR 머지 ref)으로 B의 코드를 돌고, base.sha에는 스냅샷이 있다. 따라서 「B 코드가 있고 base·head 둘 다 스냅샷 없음」은 B 레인의 스냅샷 커밋 전에만 생긴다. — ⑵를 「스냅샷 부재 = 준비 실패 78」로 바꾼다(AGENTS의 「아무 선언도 없으면 준비 실패」 규약). ⑴은 머지 ref 체크아웃에서 원안 조건이 PR head의 스냅샷 부재를 red로 만들기 때문에 유지한다. 근거 문구 「CI는 머지 커밋이 아님」은 「대조 대상 = head sha, 실행 코드 = 머지 ref」로 고친다.

확인한 곳: `eval/harness/config-paths.txt`, `.agents/harness.yaml:88-102`, `scripts/harness/config.py:26-36,271-292`, `.github/workflows/ci.yml:660-677`, spec A와 spec B 해당 줄, intent `:627-629`(모두 `<repo>/.claude/worktrees/harness-improvement` 아래).

문제없음 확인:
- B의 변경 경로(`scripts/harness/*.py`, `docs/decisions`, `dev-package/**`, `scripts/tests/**`)는 해시 집합 밖이다. A-#2의 전제와 V-B11이 성립한다.
- A-#3의 exclude는 intent의 「권고 2–12 전부 수용」에 포함된다.
- A-#1a와 A-#6은 확정된 「verify 불일치 78」과 충돌하지 않는다.
