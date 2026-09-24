# Intent: 외부 하네스(sungwooHa/ai-sdlc-harness) 대비 하네스 개선
메타 — 발의자: Ted · 작성 2026-09-25 · 승인: **미승인 (Ted 판정 대기)**
- Ted 원문: "완료되면 https://github.com/sungwooHa/ai-sdlc-harness 여기까지 개선" (2026-09-25)
- 적용 방침(Ted 2026-09-24 원문): "저대로만 개선하기보다 진지하게 따져보고 개선하는게좋을듯하니" — 장치마다 채택·변형·보류·불채택을 가른다.
- advisor ② 2026-09-25 approve-with-changes — 차단급 3 · 개선 5 반영(Intent-Ref 방식 · 줄 상한 대상 · ADR CI 필터 · 누락 장치 2행 추가).
- 대조 기준: 외부 저장소 커밋 `78b2d0f`(2026-09-14 푸시 · 파일 138개) · 우리 `claude/agent-model-tiering`(PR #130 병합분 + PR #131).
- 근거 폴더: `dev-package/reports/harness/20260925-external-harness-gap/`(G1 흐름 11행 · G2 강제 장치 7행 · G3 지식 계층 12행 · 모든 행에 파일:행).

## 문제
- 외부 하네스는 우리와 뼈대가 같다(`.agents/harness.yaml` 계약 · `.agents/skills` 원본 · Claude/Codex 어댑터). 원칙은 「설득은 문서가, 강제는 훅이」다.
- 대조하니 우리에게 없는 검사가 있다(G2 · G3):
  - 훅 등록 누락: `hook_names` 와 shim 은 있는데 `.claude/settings.json` 등록이 빠지면 `harness-contract` 와 `agent-bridge check` 가 둘 다 green 이다(보안 가드 4개가 조용히 꺼질 수 있는 경로).
  - ADR 구조 검사 코드 `scripts/harness/adr_gate.py` 는 있으나 `--all` 로 `docs/decisions/*` 전체를 검사하는 게이트·CI 지점이 없다(`seam-consistency`·`pr_contract` 는 모듈 일부만 쓴다). ADR-0003 이 이 검사를 「로컬 CLI · lifecycle 훅 없음」으로 정했으므로 훅이 아니라 게이트로 붙인다.
  - 사용자 홈 절대경로 검사가 없다(WSL `/home/…` 와 Windows 경로를 함께 쓰는 저장소).
  - 자동 로드 문서(`AGENTS.md` 55행 · `CLAUDE.md` 6행 · `.claude/rules/*` 어댑터)에 줄 상한과 검사가 없다. AGENTS.md 가 필요할 때 읽게 하는 `product.md`·`colab-rules.md` 등 578행은 상한 대상이 아니며 이 intent 에서 다루지 않는다(미해결로 남김).
- 흐름에서 빠진 것(G1): PR 요약에 「원한 결과 ↔ 실제 ↔ 근거」 대응표와 가치 상태가 정형으로 없다 · 레인이 선언한 범위 밖 변경을 인계 때 대조하지 않는다 · 커밋에서 intent 로 가는 기계 판독 연결이 없다.
- 문서 드리프트: `docs/development/dual-agent.md` 「공통 스킬 13개」 ↔ 실제 17개(+Codex 전용 1) · 벤더 스킬 2곳의 출처 커밋 SHA 부재(`.agents/skills/VENDORED.md`).
- 우리가 동등 이상인 것: advisor ①②③(외부에 독립 반론 역할 없음) · 행동 평가 20과제×2회·3상태(외부 5건 수동) · 작업별 증거 H6/H7 · 호스트 뮤텍스 · Codex bridge · 역할 5개(외부 verifier 1개).

## 원한 결과 (proposed outcome)
판정에서 채택한 항목만 해당한다.
1. 훅 등록 누락이 검사된다 — `hook_names` 항목마다 event·matcher 를 적고, `.claude/settings.json` 에 그 shim 이 등록되지 않으면 `harness-contract` 가 red 다. red 시험은 매처는 두고 명령 1줄만 뺀 settings.json 으로 한다(매처 통째 삭제는 `agent-bridge check` 가 이미 잡는다).
2. ADR 구조 검사가 게이트로 돈다 — `gates/run.sh adr-records` 가 `docs/decisions/*` 를 검사하고 CI 에 등록되며, CI 경로 필터에 `docs/decisions/**` 가 들어가 ADR 만 바꾼 PR 에서도 실행된다(`gates/tools/ci-filter-check.py` 대조 포함).
3. 사용자 홈 절대경로가 하네스 문서·설정(`AGENTS.md`·`.agents/**`·`.claude/**`·`.codex/**`·`docs/**`)에 들어가면 `harness-contract` 가 red 다. 패턴 = `/home/<u>/`·`/Users/<u>/`·`C:\Users\<u>\`·`/mnt/c/Users/<u>/` · 허용 = `git-guard.sh` 머리말 예시 `/home/user/`. 현재 트리 0건이므로 red 시험은 fixture 로 한다.
4. 자동 로드 문서(`AGENTS.md`·`CLAUDE.md`·`.claude/rules/*`)의 줄 상한 120 이 `.agents/harness.yaml` 에 선언되고 `scripts/harness/config.py` 가 초과를 red 로 판정한다(현재 합계 약 61행 · 예방 목적).
5. PR 요약 템플릿에 「원한 결과 ↔ 실제 ↔ 근거」 표와 가치 상태 4종(확인됨·부분 확인·미검증·미달)이 있고 기존 「게시 절차」「병합 뒤」 절을 유지한다. intent 템플릿에 「가치 가설」 절, UI spec 에 선택 항목 `mockup.html`.
6. 레인이 `lifecycle begin` 에 파일 범위(glob)를 선언하면 `handoff --mode complete` 가 범위 밖 변경을 차단한다(선언 없으면 현행 동작).
7. 커밋 트레일러 `Intent-Ref:` 누락과 승인 표기가 있는 intent 본문 수정을 CI 가 잡는다. 방식은 질문 4 판정대로 — ⓐ `red(판정)` 으로 막는다(트레일러 1줄은 즉시 추가 가능 · ADR-0005 2026-09-18 개정 「조용한 return 0 은 셋 중 무엇도 아니다」와 정합) / ⓑ 경고 전용으로 두고 ADR-0005 예외로 명기한다.
8. 하네스 판정 질문 4~5줄과 「하네스 변경 절차」 절이 `dual-agent.md` 에 있고 각 줄이 기존 ADR 로 연결된다. 스킬 개수 문구 정정 · ADR README 「언제 남기나」 · VENDORED 출처 SHA 기록 · ADR-0006 대안 절에 symlink 미채택 사유 1줄.

## 영향 범위
- 사용자·화면: 없음. 서비스·스키마·계약: 없음. 계약 파괴: 아니오.
- 하네스: `.agents/harness.yaml` · `scripts/harness/{config,check}.py` · `scripts/harness/hooks/lifecycle_contract.py`(범위 대조) · `gates/run.sh` · `gates/config/parallelism.toml` · `.github/workflows/ci.yml` · 템플릿(`dev-package/intent/TEMPLATE.md` · PR 요약 템플릿 신설 · `.agents/skills/to-spec/SKILL.md`) · `docs/development/dual-agent.md` · `docs/decisions/README.md` · `.agents/skills/VENDORED.md` · 시험.
- 새 훅 0개 · `/hooks` 재신뢰 0회(채택 항목 기준).

## 제약
- Ted 의 자연어 승인과 「intent 커밋 = 승인」(`dev-package/intent/README.md`)을 바꾸지 않는다.
- 레인의 복합 셸(파이프·`&&`)을 막는 장치는 넣지 않는다.
- 결정적 강제는 게이트·CI·기존 인계 검사에 붙인다(ADR-0005 「하네스 제어는 선언이며 OS 강제가 아니다」와 충돌하지 않게 문구를 맞춘다).
- 선행: PR #131(모델 배정)이 먼저 병합된다. 이 브랜치는 그 위에 쌓였다.

## 설계트리 — 장치별 판정 (증거 → 권고)
| 묶음 | 장치 | 외부 | 우리 | 권고 | 비용 | 근거 |
|---|---|---|---|---|---|---|
| 검사 | 훅 등록 누락 | 선언↔배선 검사 | Claude↔Codex 대칭만 | **채택(변형)** | 스키마 1 · 시험 | G2 d |
| 검사 | ADR 게이트 | Stop·pre-commit | 코드만 있고 미실행 | **채택(게이트로)** | 게이트 1 · CI 1 | G2 e |
| 검사 | 홈 절대경로 | fast guard | 없음 | **채택(게이트로)** | 기존 게이트 확장 | G2 c |
| 검사 | 자동 로드 문서 줄 상한 | 120행 · 체커 | 없음(현재 약 61행) | **채택(예방)** | 코드 ~15행 · 시험 1 | G3 b1 |
| 흐름 | PR 가치 대응표 | pr.md 템플릿 | 자유 서술 | **채택(변형)** | 템플릿 1 | G1 c1 |
| 흐름 | intent 가치 가설 · spec V-id · UI mockup | 템플릿 | 없음 | **채택(변형)** | 템플릿 2곳 | G1 a1·a4 |
| 흐름 | 레인 범위 선언·대조 | PreToolUse 차단 | 없음 | **채택(변형: 인계 시 사후 대조)** | lifecycle 코드 · 훅 0 | G1 b3 |
| 흐름 | Intent-Ref 트레일러 · 승인 intent 수정 검사 | Plan-Ref · 경고 | 없음 | **채택 — 판정(red) 또는 ADR 예외 경고(질문 4)** | 스크립트 ~40행 · CI 1 | G1 a3·b2 |
| 문서 | 판정 질문 · 변경 절차 · 스킬 수 · ADR 언제 · 벤더 SHA | 원칙·계약 문서 | 흩어짐 · 드리프트 | **채택(짧게)** | 문서 수 곳 | G3 a1·a2·c1·c2·f2 |
| 보류 | 질문 게이트(AskUserQuestion 4개·추천 첫 자리) | PreToolUse+Stop | 메모리 규칙뿐 | **보류** — Codex 에 AskUserQuestion 없음 · 재신뢰 · 번호 목록 차단은 우리 보고 형식과 오탐 | 훅 1 · 재신뢰 1 · bridge 예외 | G2 a |
| 보류 | git pre-commit(`.githooks`) | husky | 없음 | **보류** — drvfs 실행비트 · 작업 사본마다 hooksPath | 파일 1~2 | G2 f |
| 보류 | 보호 경로 선언(+ Bash 쓰기 검사) | 범용 가드 | 전용 가드 4개(Edit\|Write 만) | **보류** — 선언 목록만 두는 싼 변형(훅 0)도 지금 새로 보호할 경로가 0건이고 `generated-up-to-date`·`migration-drift` 가 사후 검출한다. 재검토: 생성물 직접 편집 사고 1회 | 훅 0~1 | G2 b |
| 보류 | 스킬 symlink 미러 · 어댑터 분리 | symlink · `user-invocable:false` | 텍스트 어댑터 · 원본 개조 | **보류** — Windows/Codex 호환 확인 뒤 · 다음 상류 갱신 때 선별 | 17파일 | G3 c1·c3 |
| 보류 | UserPromptSubmit 입력 기록 전용 훅 | 64자 승인 명령의 대안 | 없음 | **보류** — Ted 원문 인용의 대조 근거가 되지만 훅 1 · 재신뢰 1 · 차단 없음. 재검토: 승인 원문 오기 사고 1회 | 훅 1 · 재신뢰 1 | G1 b1 |
| 보류 | ADR 후보 안내(`adr-advice.py`) | 합의 훅 안에서 경로 규칙으로 비차단 안내 | 없음(advisor ① 이 계획을 검토) | **보류** — 합의 훅을 채택하지 않아 붙일 자리가 없다. 재검토: ADR 누락 사고 1회 | 스크립트 1 | 외부 `scripts/harness/adr-advice.py` |
| 보류 | 스킬별 Codex 메타(`agents/openai.yaml` · `allow_implicit_invocation: false`) | 표시 이름 · 암묵 호출 금지 | 없음 | **보류** — Ted 의 「스킬은 명시 호출 전용」과 방향이 같으나 Codex 0.154 가 이 정책을 지키는지와 우리 스킬 중 명시 전용 목록을 먼저 확인 | 스킬당 1파일 | 외부 `.agents/skills/*/agents/openai.yaml` |
| 불채택 | 로컬 전용 변경 폴더 | 커밋 금지 · 이력은 PR | intent 커밋 = 승인 | **불채택** — 승인 증거와 에이전트 읽기 경로가 사라진다 | — | G1 a2 |
| 불채택 | 64자 해시 승인 명령 | UserPromptSubmit | 자연어 승인 | **불채택** — Ted 승인 방식과 충돌(대안: 입력 기록만 하는 훅은 보류 목록) | — | G1 b1 |
| 불채택 | 합의 PreToolUse 셸 차단 | `;&\|><` 포함 셸 차단 | 없음 | **불채택** — 레인의 docker·pytest·npm 파이프 전면 차단 | — | G1 b3 |
| 불채택 | PR 본문 형태 훅 | 3 이벤트 | 없음 | **불채택** — PR 6건 규모에서 재신뢰 비용 > 이득 · 결함 3회 반복 시 재검토 | — | G1 c2 |
| 유지 | plan 템플릿 · verifier · eval 러너 | — | 라운드 파일 · advisor ② · 20과제 | **가져올 것 없음** | — | G1 b5 · G3 d1·e1·f1 |

## 미해결 질문 (Ted 판정)
1. 검사 묶음 4개(훅 등록 누락 · ADR 게이트 · 홈 절대경로 · 줄 상한) 채택 ⓐ(권고).
2. 흐름 묶음(PR 가치 대응표 · intent 가치 가설 · spec V-id · UI mockup 선택) 채택 ⓐ(권고).
3. 레인 범위 선언·인계 대조 채택 ⓐ(권고) / 보류 ⓑ.
4. Intent-Ref 트레일러·승인 intent 수정 검사: 판정(red)으로 막는다 ⓐ(권고 · ADR-0005 정합) / 경고 전용 + ADR-0005 예외 명기 ⓑ / 보류 ⓒ.
5. 문서 정비 채택 ⓐ(권고).
6. 보류 7개(질문 게이트 · pre-commit · 보호 경로 · symlink · 입력 기록 훅 · ADR 후보 안내 · Codex 스킬 메타)는 보류하고 재검토 조건을 기록 ⓐ(권고) / 질문 게이트는 지금 채택 ⓑ.
7. 불채택 4개 확정 ⓐ(권고).
8. 진행: #131 병합 뒤 별도 PR · 레인 2개(검사·게이트 / 흐름·문서) · advisor ①② ⓐ(권고).

## 범위 밖 (명시 제외)
- 외부 템플릿 초기화 스크립트 · 플레이스홀더 · 벤더 스킬 재수입 도구 · 제품 코드 · 사용자 전역 설정.

## 확인
- Ted 확인 문장: (판정 뒤 원문 그대로 적는다)
- 재개봉 금지: 아니오(초안).

## 참조
- 외부: https://github.com/sungwooHa/ai-sdlc-harness (커밋 `78b2d0f` · README 「원칙」「4개 계층」「검사는 스크립트가 한다」)
- 우리: `.agents/harness.yaml` · `scripts/harness/config.py` · `scripts/agent-bridge.py` `check` · `docs/decisions/0005-harness-controls-are-declarative.md` · `dev-package/intent/README.md`
- 선행 intent: `dev-package/intent/2026-09-24-harness-lane-hygiene.md` · `dev-package/intent/2026-09-24-agent-model-tiering.md`
