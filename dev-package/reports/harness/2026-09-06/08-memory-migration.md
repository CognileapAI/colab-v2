# 08 · 메모리 이관표 (phase P-M)

- 근거 = `docs/superpowers/specs/2026-09-06-harness-fable51-design.md` **G절**(메모리 이행 · 삭제 전 검증 · 파일명 앵커) · **H절 순서 5**(P-M) · `dev-package/reports/harness/2026-09-06/02-workflow-profile.md` 6절 분류.
- 집행일 = 2026-09-06. 집행 범위 = **이관 표기까지**. **삭제는 P-C** — 아래 §4 탐침 3문을 새 세션에서 통과한 뒤에만 수행.
- 산출 = `.claude/rules/colab-rules.md` (215행, 파일명 앵커 24). 옛 메모리 파일에는 `> MIGRATED …` 한 줄을 frontmatter 아래에 덧붙였고 **파일은 하나도 삭제하지 않았다**.

## 0. 실측 계수와 스펙 계수의 차이

| 구분 | 스펙 G / 프로파일 6절 | 이번 실측 | 차이 사유 |
|---|---|---|---|
| 규칙형 (rules 흡수) | 16 | **18** | 프로파일이 `commit-survey-artifacts-immediately`(type: feedback)를 어느 갈래에도 넣지 않았고, `session-bootstrap-diet`(type: feedback)를 상태형 11건 목록에 넣었다. 둘 다 값이 아니라 **행동 규칙**이므로 rules 로 흡수했다. |
| 훅/스크립트 대체 | 6 | **6** | 동일. 규칙문은 **삭제하지 않고** rules 에 앵커와 함께 남겼다(P-G 미집행분 3건이 아직 코드로 강제되지 않으므로). |
| 상태형 (HANDOFF/원장) | 8 + 원장 4 = 12 | **10** | 프로파일 목록의 `same-as-main`·`session-bootstrap-diet`·`planner-authors`·`planning-folder-lifecycle` 중 앞의 둘은 규칙형으로 갈랐고, 뒤의 둘은 상태형으로 유지했다. 프로파일 작성 후 신설된 `ted-decisions-260906-ra-merge`·`window-9-260906`·`next-round-ra2-rb-260906` 3건이 늘었다. |
| 이관 제외 | — | **2 + MEMORY.md** | `harness-redesign-260906`·`ra-prime-rb-owner-plan-0906-4` = 2026-09-06 당일 작성분(진행 중 회차 소유권·이 이행 자체의 기록). 지시에 따라 무수정. |
| 파일 합계 | 33 | **36 + MEMORY.md** | 스펙 작성 시점(33) 이후 당일 3건 추가. |

## 1. 규칙형 18건 → `.claude/rules/colab-rules.md`

| 메모리 파일 | 이관처 | 상태 |
|---|---|---|
| `orchestrator-delegation-policy.md` | rules §1-1 | 흡수 완료 (앵커 있음) |
| `no-file-edits-in-main-session.md` | rules §1-2 | 흡수 완료 |
| `model-roles-fable-advisor.md` | rules §1-3 | 흡수 완료 |
| `session-bootstrap-diet.md` | rules §1-4 | 흡수 완료 · **훅/스크립트로 강제됨**(P-B H1 `bootstrap-diet.sh` + `CLAUDE.md §1`) — 규칙문은 참고 |
| `batch-questions-product-framed.md` | rules §1-5 | 흡수 완료 |
| `worktree-cleanup-after-merge.md` | rules §2-1 | 흡수 완료 |
| `commit-survey-artifacts-immediately.md` | rules §2-2 | 흡수 완료 |
| `narrow-gates-one-at-a-time.md` | rules §3-1 | 흡수 완료 |
| `no-redundant-gate-rerun-after-merge.md` | rules §3-2 | 흡수 완료 (탐침 ① 대상) |
| `same-as-main-is-not-ok.md` | rules §3-3 | 흡수 완료 (탐침 ③ 대상) |
| `writing-style-korean-outline.md` | rules §5-1 | 흡수 완료 |
| `explain-before-asking-judgment.md` | rules §5-2 | 흡수 완료 |
| `no-metaphor-technical-terms.md` | rules §5-3 | 흡수 완료 |
| `deploy-window-term-explain.md` | rules §5-4 | 흡수 완료 (탐침 ② 대상) |
| `status-map-deliverable.md` | rules §5-5 | 흡수 완료 |
| `final-report-eli5-content-not-process.md` | rules §5-6 | 흡수 완료 |
| `ux-first-design-criterion.md` | rules §6-1 | 흡수 완료 |
| `convenience-features-deferred.md` | rules §6-2 | 흡수 완료 |

## 2. 훅/스크립트 대체 6건 → 코드 + rules(규칙문 보존)

| 메모리 파일 | 대체 코드 | 이관처 | 상태 |
|---|---|---|---|
| `worktree-gate-env-setup.md` | P-E H2 `SubagentStart:lane-worker` + `worktree-setup.sh` (커밋 `15bc4e0`) | rules §2-4 | **집행 완료** — 규칙문은 red(준비) 판독법으로 존치 |
| `gates-need-test-env-sourced.md` | P-E `gates/run.sh` 자체 source (커밋 `15bc4e0`) | rules §3-4 | **집행 완료** — 규칙문은 `-j 4` 실측값·판독법으로 존치 |
| `subagent-worktree-isolation-pin.md` | P-A `lane-worker` frontmatter `isolation: worktree` | rules §2-3 | **미집행(P-A)** — 규칙문이 현재 유일한 강제 |
| `decision-number-issue-at-merge.md` | P-G `renumber-decisions.sh` | rules §4-1 | **미집행(P-G)** — 규칙문이 현재 유일한 강제 |
| `parallel-lanes-ledger-append-conflict.md` | P-G `work-items.yaml` merge driver + `work-item-consistency` | rules §4-2 | **미집행(P-G)** — 규칙문이 현재 유일한 강제 |
| `ntfs-exec-bit-update-index.md` | P-G exec-bit 게이트 | rules §4-3 | **미집행(P-G)** — 규칙문이 현재 유일한 강제 |

> ⛔ **P-C 삭제 판정 주의** — 위 4건(P-A·P-G 미집행)은 rules 에 규칙문이 남아 있으므로 메모리 파일 삭제로 손실이 발생하지 않는다. 반대로 **rules 에서 이 절을 걷는 것은 P-A·P-G 집행 확인 뒤에만** 가능하다.

## 3. 상태형 10건 → HANDOFF / 원장 / 기획 문서

| 메모리 파일 | 이관처(값의 자리) | 판정 |
|---|---|---|
| `ted-decisions-260905-prd.md` | `dev-package/prd/PRD-260905-적용전기획.md` 미결 표 「확정 (Ted 2026-09-05)」 열 · `PLAN-SoT §9 〈194〉` | **이미 기록됨** — 16건 전부 확정 열에 있음. 「재개봉 금지」 규칙만 rules §8 로 승격 |
| `ted-decisions-260905-deploy-switch.md` | `PLAN-SoT §9 〈334〉`·`〈335〉`·`〈336〉` · `03-HANDOFF.md §4.5` · `dev-package/reports/deploy-switch-20260905.md` | **이미 기록됨** (SoT 각 2~6회 · HANDOFF 각 8~11회 히트) |
| `ted-decisions-260906-ra-merge.md` | `PLAN-SoT §9 〈346〉`-⑦(19차 승인 축자) · `03-HANDOFF.md §4.5` 최상단 블록 | **이미 기록됨** |
| `ted-decisions-260906-rev2.md` | `40 COLAB-기획/20_검토/260906_업로드계보rev2/결정서_Ted_260906.md`(레포 밖) | **누락 — 추가함** · `03-HANDOFF.md §4.5` 에 근거 경로 + 판정-1/판정-2 요지 1줄 추가(레포 안에 `rev2`·「달력 팝오버」 문자열 0건이었음) |
| `window-8a-done-260906.md` | `PLAN-SoT §9 〈348〉`~`〈367〉` · `03-HANDOFF.md §4.5` · `dev-package/reports/window-8a/`·`window-8b/` | **이미 기록됨** — main `b0671f8` ff·20차·`0014_merge_ra1_and_topic_vocab` 까지 등재됨 |
| `window-9-260906.md` | (이관 전 부재) | **누락 — 추가함** · `03-HANDOFF.md §4.5` 에 1줄: dev sha `20b3715`·doctor 14/14·`integration/w9-dev-deploy` `13589fe` 미 ff·다음 세션 첫 일 5단계·Ted 판정 ⑭⑮·BF-12 구조적 red |
| `next-round-ra2-rb-260906.md` | (이관 전 부재) | **누락 — 추가함** · `03-HANDOFF.md §4.5` 에 1줄: R-A′ 5건 순서·워크트리 `r-a2`·R-B 앵커 `WU-B3`·`WU-A6` 달력 팝오버 → `WU-B3` 이관·시작 문서 3종 |
| `aws-handoff-status-260905.md` | `infra/dev/README.md`(운영자 env 변수·ship 절차) · `03-HANDOFF.md §4.5 ㉡`(인수 판정 기준·`dev-key.pem` 경로) | **이미 기록됨** — 잔여 미착수분 `t4g.medium` 승격은 `window-9` 의 Ted 판정 ⑮ 로 갱신됨(개발 종료 후로 유예). 계정 유료 여부는 「재확인 금지」로 종결 |
| `planner-authors.md` | `dev-package/prd/PRD-260905-적용전기획.md` 자료·작성자 표(이태헌 3건 · 조성진 1건) | **이미 기록됨** — 「작성자별로 질의 분리」 규칙만 rules §7 로 승격 |
| `planning-folder-lifecycle.md` | `dev-package/prd/개발계획서-260905.md`(「`10_적용전/` 은 읽기 전용」) · `40 COLAB-기획/README.md`(폴더 색인) | **이미 기록됨** — 「기획자 문서 우선」 규칙만 rules §7 로 승격 |

### HANDOFF 편집 요약 (수술적, 재작성 없음)

- 편집 위치 = `dev-package/03-HANDOFF.md §4.5` 최상단 블록 끝, 「미충족 이월 1건」 줄 **다음**.
- 추가한 줄 = **3줄**(창 9 dev 배포 · 다음 라운드 R-A′/R-B 준비 · rev2 판정 근거 경로). 각 줄에 출처 메모리 파일명을 명기했다.
- 기존 줄 수정·삭제 = **0**.

## 4. 삭제 전 검증 — 탐침 3문 (P-C 전제, 스펙 G)

새 세션 **1개**를 `30 CoLAB-v2` 루트에서 열고 둘 다 통과할 때만 P-C 삭제를 집행한다.

**⑴ 로딩 확인** — `/context` 의 Memory files 에 `colab-rules.md` 가 표시되는가.
- 기대 = 표시됨. 근거 = 이 파일에 `paths` frontmatter가 없으므로 launch 로딩(스펙 K절 V1 인용 — "Rules without `paths` frontmatter are loaded at launch with the same priority as `.claude/CLAUDE.md`").
- 미표시 시 = **삭제 보류**. 원인 후보 = 세션 루트가 아직 `00 CoLAB` (J-0 루트 이동 미완).

**⑵ 탐침 3문** — 규칙대로 답하는가.

| # | 질문 | 기대 답 | 근거 절 |
|---|---|---|---|
| ① | **같은 트리를 다시 전수 돌리나?** | 돌리지 않는다. 병합 커밋의 트리가 이미 전수 판정된 통합 브랜치 끝 트리와 같으면 `git log -1 --format=%T` 로 동일성을 확인하고 원장에 「갈음」으로 적는다. 재실행 조건은 트리가 달라졌을 때뿐이고, 문서만 바꾼 커밋은 원장 게이트 3종만 돈다. | rules §3-2 |
| ② | **보고서에 창 번호를 쓰나?** | 쓰지 않는다. 「창 6」·「단독 창 5b」는 내부 색인 용어이므로 「다음 staging 배포 회차(내용물: …)」처럼 기능·내용물로 풀어 쓰고, 원장 번호·창 번호는 괄호로만 병기하거나 생략한다. 처음 쓰는 용어에는 한 줄 정의를 붙인다. | rules §5-4 (§5-2 와 짝) |
| ③ | **main 과 동일한 오류는 수용 근거인가?** | 근거가 아니다. 「main 과 같다」는 레인이 새로 만든 결함이 아니라는 뜻일 뿐이므로, 즉시 **main 이 배포 가능한가**를 되묻고 그 오류가 어느 검사(게이트·Dockerfile·배포)에 걸리는지 확인한다. 검사가 Dockerfile·배포 스크립트 안에만 있고 게이트에 없으면 그 자체가 결함이므로 게이트로 올린다. | rules §3-3 |

- 3문 중 **1문이라도 규칙과 다르게 답하면 삭제 보류**하고 rules 문안을 먼저 고친다.
- 통과 시 P-C 집행 순서 = ⑴ 옛 메모리 디렉터리를 `~/.claude/_archive/2026-09-06-harness/memory/` 로 복사 → ⑵ 이관 표기된 34건 삭제 → ⑶ `MEMORY.md` 3줄 포인터로 축소 → ⑷ 잔존 계수 확인(목표 ≤4).

## 5. 옛 메모리 디렉터리 현재 상태

⭑ **⟨증보 2026-09-06 · P-C 부분⟩ archive 복사 완료.**
`~/.claude/projects/-mnt-f-00-Project-00-CoLAB/memory/` → `~/.claude/_archive/2026-09-06-harness/memory/`
**37/37 파일 · `diff -rq` 차이 0.** 스펙 I 절 되돌리기 보증이 이것으로 성립한다 — 삭제분은
이 사본에서 그대로 복원된다.

⛔ **삭제와 `MEMORY.md` 3줄화는 이번에 하지 않았다.** 조건 = §4 탐침 3문을 **새 세션에서** 통과.
새 세션이 필요한 이유는 `colab-rules.md` 의 launch 로딩 여부가 이번 세션에서는 확인되지 않기
때문이다(스펙 G 「삭제 전 검증」). 통과 뒤 남은 순서 = ⑵ 이관 표기된 34건 삭제 → ⑶ `MEMORY.md`
3줄 포인터 축소 → ⑷ 잔존 계수 ≤4 확인.

- 표기 방식 = frontmatter 닫는 `---` 바로 아래에 `> MIGRATED 2026-09-06 → …` 한 줄. 본문 무수정.
- 삭제 = **0건**.
- `MEMORY.md` = 유지. 첫 줄에 이관 안내 1줄만 추가(3줄 축약은 P-C).
- 무수정 2건 = `harness-redesign-260906.md` · `ra-prime-rb-owner-plan-0906-4.md`.
- 새 루트 메모리 디렉터리(`…-30-CoLAB-v2/memory/`, 2건) = 무수정.

## 6. 후속 (P-M 범위 밖)

1. `advisor-must-argue-both-sides.md` — 새 루트 메모리에만 있고 옛 루트에 없다. P-A 에서 `advisor` 에이전트 정의에 흡수할지 판정 필요.
2. rules §2-3·§4-1·§4-2·§4-3 은 P-A·P-G 집행 후 「훅/스크립트로 강제됨」으로 표기 전환.
3. `03-HANDOFF.md §2 현재 상태 스냅샷`의 `origin/main` = `179c949` 는 실물(`f2b61cd`)과 어긋난다. 이번 이관 범위 밖이라 손대지 않았다.
4. 창 9 등재 〈N〉 은 다음 세션의 ff 커밋이 발급한다(rules §4-1 — 예약 금지).
