# 하네스 재설계 조사 산출물 — 2026-09-06

CoLAB v2 개발 하네스(세션 주입·에이전트·스킬·플러그인·훅·게이트) 재설계를 위해 2026-09-06 하루에 수행한 조사 8건의 원본이다. 이 폴더는 **근거 보관소**이며 결론이 아니다. 확정 결론과 Ted 판정(J-0~J-12), 이행 계획·상태는 스펙 문서 [`docs/superpowers/specs/2026-09-06-harness-fable51-design.md`](../../../../docs/superpowers/specs/2026-09-06-harness-fable51-design.md) 에 있다. 문서끼리 어긋나면 **스펙이 우선**한다. 07 은 스펙의 직전 판본이므로 판정 항목이 아직 선택지(ⓐ/ⓑ) 형태로 남아 있다 — 확정 판정은 스펙 J 절에서 읽는다.

⭑ **⟨증보 2026-09-06 · 마감⟩ 08~13 은 조사가 아니라 이행 phase 의 실행·검증 기록이다.** 조사(00~07)는 설계의 **입력**이고 08~13 은 집행의 **증적**이다. 원장 등재는 `dev-package/PLAN-SoT.md §9 〈368〉`~`〈371〉` · 이행 상태표는 스펙 `§0-2`·`H` · **잔여 후속 9건은 스펙 `§0-5`** 한 자리에 모았다.

| 파일 | 내용 |
|---|---|
| `00-brief.md` | 착수 브리프 — 결함 D1~D22, 요구 F1~F21 |
| `01-inventory.md` | 하네스 자산 실측 인벤토리(에이전트·스킬·플러그인·훅·메모리) |
| `02-workflow-profile.md` | 실제 세션 로그 기반 워크플로 프로파일 |
| `03-market-survey.md` | 외부 하네스·에이전트 운영 사례 조사 |
| `04-grill-me.md` | mattpocock 스킬 계열 조사(`grilling`·`grill-me`·`to-spec` 외) |
| `05-playbook-gap.md` | 「AI-native SDLC 플레이북」 대비 갭 16건 + 아티팩트 템플릿 초안 |
| `06-advisor-review-gate1.md` | advisor 게이트① 계획 검토 지적 18건 |
| `07-design-v3.md` | 설계 v3 원본(스펙의 직전 판본) |
| `08-memory-migration.md` | **P-M** — 옛 자동메모리 33건 → `.claude/rules/colab-rules.md` 이관표. 삭제 조건인 **탐침 3문**이 `§4` 에 있다 |
| `09-agents-verification.md` | **P-A** — 프로젝트 에이전트 4종(`advisor`·`lane-worker`·`researcher`·`gate-runner`) 검증. **스폰 기동 실측은 다음 세션 몫**(`§3` 수용 절차) |
| `10-skills-vendoring.md` | **P-S** — vendored 스킬 8종(superpowers 5 ＋ mattpocock 3)·`intent/`·`prd/specs/` 템플릿. `grill-me` **실전 1회는 다음 세션**(`§6`) |
| `11-merge-guards-verification.md` | **P-G** — H3·H4·H5 의도적 위반 5/5 차단 · `renumber-decisions.sh` 역링크 대조 · **`exec-bit` 도입 시 잠복 `100644` 57건 조치**(`§6`) |
| `12-gate-json-verification.md` | **P-J** — `colab-gate-summary/1` 배출·H6·H7 검증. **후속 항목 4건**(DB 게이트 접속 분류 13곳 · 스펙 D 필드명 · H7 env 한계 · 전수 1회)이 `§6` |
| `13-planning-applied-wiring.md` | **P-C 부분** — `30_적용완료` 환류 배선(매니페스트·`planning-freshness` 확장·워크트리 경로 해소). **범위 밖 = 메모리 삭제·`MEMORY.md` 3줄화**(`§7`) |
| `pe-sweep-3.12.log` | P-E 전수 실행 로그(Python 3.12) — `06`~`13` 이 인용하는 수치의 원본 |
</content>
