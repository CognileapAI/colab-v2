VERDICT: CHANGES

## 필수 변경
**A. `dev-package/intent/2026-09-26-ci-harness-eval-run.md`**
1. `:28` · `:50` Q10 ⓐ 「커밋 ① = 워크플로 파일 + 문서(집합 밖 · 회차 0)」 — 틀림. 같은 절이 바꾸는 `eval/harness/README.md` · `.agents/rules/product.md:129` · `gates/tools/harness-eval.sh:105` 는 해시 집합 안(`eval/harness/config-paths.txt:15` `eval/harness/**` · `:12` `.agents/**` · PR A 뒤 `harness-eval.sh` 재등재). 고침: 커밋 ① 을 「`.github/workflows/harness-eval-run.yml` + 총괄 T12 행(집합 밖)」으로 좁히고 README·product.md·harness-eval.sh 문구는 커밋 ②(집합 안 · 첫 CI 회차 동반)로 이동.
2. `:9` · `:79` 총괄 `:81` T12 · `:12` `:184` 회차 5~20 — 실제 T12 = `S-HARNESS-IMPROVEMENT-PLAN-20260926.md:83`(`:81` 은 T1) · 「5회 ≈160 USD」 = `:186`(`:184` 공백). 줄 번호 정정.
3. `:42` Q2 ⓐ 「`COLAB_EVAL_TIMEOUT=150`(README 권장값)」 — README 권장값은 **93**(`eval/harness/README.md:63` p95 46.4×2 · `:14` · `harness-eval.sh:105` · 총괄 T12 동일). 150 을 쓰려면 근거(회차 3 p95 58.5×2 = 117 등)를 적거나 93 으로.
4. `:36` 제약 「순서 = PR A → 이 intent 의 PR → PR 2 head 회차부터 CI」 vs 총괄 §10.2 행 7 「판정만 · 구현은 별도 spec」 · 행 8 선행 = 「행 7 **결정**」. 구현 PR 을 PR 2 앞에 둘지는 Q10 의 선택지이지 제약이 아니다 — 제약에서는 「결정 = PR 2 병합 전(10라운드)」만 남기고 구현 시점은 Q10 판정으로.
5. 미해결 2(월 한도 값 · 초과 동작) · 4(`timeout-minutes`) 는 선택지 없음. 각각 ⓐ/ⓑ 값 후보(예: 100 USD/키 정지=78 · 150 USD/알림만 · 90/120 분)로 재작성.

**B. `dev-package/intent/2026-09-26-portable-gate-locks.md`**
1. `:9` 「`serial` 선언 45건」 — `gates/config/parallelism.toml` 에서 `= "serial"` 17건(`grep -c` · `:23` 주석 제외). 재계수 후 정정(감사 E-3 의 45 를 그대로 옮긴 것).
2. `:11` · `:76` 총괄 「2-3 `:64`」 — 2-3 행은 `:66`. 정정.
3. `:48` Q10 ⓐ 「PR A ∥ B 뒤 · PR 2 head 회차 앞」 vs 총괄 §10.2 행 12(선행 조건 = **PR 4**) · §10.5 「행 12」. 둘 중 하나로 통일 — 팀 원칙(macOS 구성원이 PR 4 까지 serial·DB 게이트 78)과 E-3 「PR 3 앞」 기준으로 intent 쪽이 맞음. 총괄 §3 `:152-153` 은 `_lock.sh`(2-3) · `_pg.sh`(2-1h) 를 PR 2 소유로 두므로 ⓑ → PR 2 순차 소유와 2-3 문구(`flock -w` → `_flock.py --wait`)를 같이 적어야 「같은 파일 동시 lane 0」이 선다.
4. `:26` 영향 범위(`db-selftest.sh` · `gates/README.md` · `parallelism.toml` · 신설 `_flock.py`) 가 총괄 §10.5 소유 목록(`_lock.sh` · `_pg.sh` · `gate-host-mutex-selftest.sh`)보다 넓다. `gates/README.md` 는 §3 `:154` PR 3 소유 — 순차 관계 1줄 추가.
5. `:45` Q4 `_pg.sh:40` → 실제 `:41-42`. 미해결 2·5·6 은 질문이 아니라 범위 진술·실측 항목 — 「범위 밖」으로 옮기거나 선택지(예: 미해결 6 = onboarding.md / gates/README.md)로 재작성.

**C. `dev-package/prd/specs/S-HARNESS-IMPROVEMENT-PLAN-20260926.md` §10**
1. `:222` 행 2 「T11 PAT(1인 판) ✓ 적용됨」 — 틀림. 부모 intent `:621` = T11 **보류**(Ted "나중에 만들자") · CI intent `:33,:75` 도 보류로 인용. 행 2 를 「T1 ✓ · T11 보류(`:621`) → 행 6 재판정」으로.
2. `:232` 행 12 ⓑ 선행 조건 PR 4 — B-3 과 동일 충돌. ⓑ 를 별도 행(5c · 선행 = PR A 병합 · 회차 0 · PR 2 lane 착수 전)으로 옮기고 §3 `:152-153` 에 「ⓑ → PR 2」 순차 추가.
3. `:236` 회차 단가 「`{125205,140939,143218}` 7.48 / 8.00 / 8.11」 — 실측 125205 = 7.9981 · 140939 = 7.4808(실행 39 · 준비 1 = 전수 아님) · 143218 = 8.1084. 순서 정정 + 140939 는 준비 1 표기.
4. 충돌·미확인 「C-2 `CLAUDE_CONFIG_DIR` 격리 미검증 → `claude -p` 1회 실측 뒤 PR A 포함 여부」가 §10 어디에도 없음. 행 5a 또는 §6 에 1줄(실측 담당 · 판정 시점).

## 개선(비차단)
- 두 intent 의 ADR 번호 가정이 서로 다름(CI `:51` 「0013 S-auth → 0014 후보」 · locks `:53` 「먼저 병합되면 0013」) — 둘 다 「병합 시점 다음 빈 번호」로만 적고 숫자 삭제.
- 두 intent 모두 메타 줄과 `## 문제` 사이에 출처·원칙·표기 3~4행 삽입 — TEMPLATE 에 없는 자리. `intent_ref.py:44` 는 `메타` 첫 줄만 읽어 판정 무영향이나, 부모 intent 「판정 기록」 포인터 1줄로 압축 권장.
- CI intent `:54-55` · locks `:53` 「Ted 판정/확인」 → 권고 11 역할 어휘(승인자) 로. locks `:70` 「macOS 1대 실측」 은 실행 주체(macOS 구성원 · Ted 는 WSL)를 명시.
- §10.3 마지막 항 「다른 구성원이 대신 회차 실행 · 실행자 무관」 은 PR A 모델 고정만으로는 사용자 훅·`~/.claude` 설정 차이(C-2)를 덮지 못함 — C-2 격리 판정과 연결.
- CI intent `:41` Q1 미해결 1 은 `refs/remotes/origin/HEAD` = `codex/design-style-repair` 실측과 일치(확인됨) · `gh repo view` 1회로 닫을 것.
