# P0 기준선 — 하네스 재설계 지표 실측

**측정일** 2026-09-06 · **측정처** 워크트리 `harness-fable51-spec` · **스펙** `docs/superpowers/specs/2026-09-06-harness-fable51-design.md` A-2 절(지표 정의가 여기 있다).

이 문서는 **바꾸기 전의 값**을 남기는 자리다. 뒤에 「좋아졌다」를 말하려면 여기 적힌 수와 대조해야 하고,
대조할 수가 없으면 그 주장은 측정이 아니라 인상이다. 근거는 전부 경로로 건다 — 기억으로 적지 않는다.

---

## S1 — 후보 목록(에이전트·스킬) 계수

**측정법**(스펙 A-2) — 새 세션 시스템리마인더에 열거되는 agents/skills 개수.

| | 이전(실측) | 목표 | 근거 |
|---|---|---|---|
| 에이전트 | **≈42** | ≤12 | `2026-09-06/01-inventory.md` + 스펙 A-1 재계수(글로벌 13 · 루트 15 − 이름중복 6 = 유니크 22 · 플러그인 14 · 내장 5~6) |
| 스킬 | **47** | ≤20 | `01-inventory.md` — "글로벌 8 + 플러그인 39 = 47개"(대화 상단 목록 실측치와 일치) |

⚠ `01-inventory.md` 본문의 「에이전트 총 26개」는 **오계다.** 루트 프로젝트 `00 CoLAB/.claude/agents/` 15개를
세지 않았다. 스펙 A-1 이 이 재계수를 수용해 **≈42** 로 고쳤다(advisor 지적 2). 여기서는 고친 값을 쓴다.

### P-T 집행 뒤 **남긴 것**(2026-09-06 · 스펙 0-1)

| 층 | 남긴 것 |
|---|---|
| 플러그인 활성 6 | `context7` · `skill-creator` · `code-review` · `typescript-lsp` · `pyright-lsp` · `eli5` |
| 플러그인 비활성 9 | superpowers · claude-mem · understand-anything · ralph-loop · claude-md-management · frontend-design · feature-dev · codex · playwright |
| 글로벌 에이전트 | **1** — `advisor` (humanize 계열 12 는 `~/.claude/_archive/2026-09-06-harness/` 로 이동) |
| 글로벌 스킬 | **3** — `archify` · `explain-visually` · `graphify` (apple-design · travel-proposal · humanize 3종 = 5 는 archive) |
| 프로젝트 스킬 | **1** — `.claude/skills/colab-v2-work/` |
| 세션 루트 자산 | humanize 6 + presentation 9 에이전트 · humanize 스킬 6 → 형제 폴더 `10_Humanize-Presentation/.claude/` 로 이동(J-3) |

**⚠ 집행 후 계수는 아직 재지 않았다.** 시스템리마인더는 **세션이 뜰 때** 조립된다 — 이 세션은 토글 이전에
뜬 목록을 들고 있어 여기서 세면 옛 수가 나온다. **다음 새 세션에서 1회 실측**한다(스펙 A-2 「측정 시점」).
그때까지 「42→N」의 N 은 **비어 있는 칸이지 0 이 아니다.**

---

## S2 — 게이트 요약 기계가독

| 이전 | 목표 | 측정 시점 |
|---|---|---|
| `gate-summary.json` **없음** | `counts` 가 `run.sh` 요약줄과 일치(이진) | P-J 종료 후 전수 1회 |

`gates/run.sh` 는 이미 `green / red(판정) / red(준비)` 3상태를 **사람이 읽는 줄로** 찍는다(run.sh 요약 블록).
없는 것은 판정이 아니라 **기계가 읽는 출구**다. P-J 가 같은 변수로 JSON 한 개를 더 배출한다.

---

## S3 — 새 워크트리 첫 전수의 red(준비) 건수 ← **P-E 의 판정 지표**

| 원인 | 이전(실측) | 근거 |
|---|---|---|
| D1 — `node_modules`·`services/*/.venv` 미승계 | **10** | `2026-09-06/02-workflow-profile.md` D절 D1 행 · 메모리 `worktree-gate-env-setup` |
| D2 — 테스트 env 미source | **6** | 같은 표 D2 행 · 메모리 `gates-need-test-env-sourced` |
| **계** | **16** | **목표 0** |

**16 이 무엇이었나** — 둘 다 「검사 대상이 규율을 어겼다」가 아니라 **「검사기가 판정을 못 냈다」**였다.
워크트리는 추적 파일만 들어온 신선한 체크아웃이고, 시험용 값은 HOME 의 파일에 있는데 아무도 읽지 않았다.
그런데 출력에서 둘이 같은 `red` 로 보여, 레인은 「내 코드가 깼나」를 20분 뒤졌다(D12).

**P-E 의 해소** — ⑴ H2 `SubagentStart:lane-worker` → `.claude/hooks/worktree-setup.sh` 가 스폰 시점에
`node_modules` + 서비스 `.venv` 4벌 + `gates/.venv` 를 세운다(복사 아님 · **재생성**). ⑵ `gates/run.sh` 가
`~/.colab-v2-test.env` 를 **스스로 source** 한다. 관용구를 사람 기억에 두지 않는다.

### P-E 실측 (이 워크트리 · 2026-09-06)

**⚠ 측정 기준 = 직접 실행이다.** 아래 수는 `worktree-setup.sh` 를 **손으로 돌린** 것이고,
`SubagentStart:lane-worker` 로 **레인이 스폰될 때 같은 수가 나오는지는 아직 재지 않았다.**
`.claude/agents/lane-worker` 가 아직 없어서(P-A 소관) 스폰 자체를 못 한다. 미검증으로 남는 두 가지 —
⑴ 스펙 K-7 (SubagentStart stdout 이 레인 컨텍스트로 들어가는가), ⑵ `isolation:"worktree"` 스폰에서
훅이 받는 `cwd` 가 **격리 워크트리**인가 부모 체크아웃인가. 부모라면 훅은 부모 venv 를 다시 짓고
레인은 red(준비) 10건으로 그대로 연다. **레인 스폰 경유 검증은 P-A 이후 레인 1개로 실측한다.**

| 항목 | 값 |
|---|---|
| `worktree-setup.sh` 첫 실행 (5개 신설 · 병렬 · 3.13 판) | **94초** — frontend 60 · core-api 54 · ai-service 53 · viz-render 66 · pipeline-worker 61 · gates/.venv 재사용 |
| 인터프리터 정정 뒤 재빌드 (서비스 4벌 · 병렬 · frontend 재사용) | **43초** — core-api 28 · ai-service 28 · viz-render 43 · pipeline-worker 37 |
| 같은 스크립트 재실행 (전부 재사용) | **2초** — 스폰 지연으로 체감되지 않는다(스펙 K 미검증 6 해소) |
| 스탬프 훼손 실험 (남의 트리 경로 1벌 · 3.13 판 1벌) | **18초** — 훼손된 2벌만 재생성 · 나머지 4벌 재사용 |
| 전수 red(준비) — env 구축·source 뒤 | **아래 「전수 실측」 절** |

#### 인터프리터 정정 (advisor 게이트 ② 지적 1)

첫 회차의 `uv venv` 는 `--python` 을 주지 않아 **uv 가 관리하는 최신 = CPython 3.13.13** 으로 4벌을 지었다.
그런데 `services/*/pyproject.toml` 은 전부 `requires-python = "==3.12.*"`, CI 는 `setup-python 3.12`
(`.github/workflows/ci.yml`), Dockerfile 은 `python:3.12-slim` 이다. **레포가 금지한 판에서 돈 시험의 green 은
3.12 의 증거가 아니다.** 훅을 고쳤다 — 판은 `pyproject.toml` 의 `requires-python` 에서 읽고
(`uv python find <판>` → PATH 의 `python<판>` 순으로 찾는다), 못 찾으면 **짓지 않고 요약에 실패로 적는다.**
지은 뒤 `sys.version_info` 로 되확인한다. 재빌드 후 실측 — 서비스 4벌 + `gates/.venv` 전부 **Python 3.12.3**.

「이 venv 가 내 워크트리 것인가」의 판별도 같이 고쳤다. 옛 검사 3개는 uv venv 에서 전부 헛돌았다 —
venv 안에서 `sys.prefix` 는 **부른 경로**에서 유도돼 언제나 자기 자신과 같고(항진명제), uv 는 `pyvenv.cfg` 에
`command =` 를 적지 않으며, uv venv 에는 `bin/pip` 이 없다. 복사본이 「재사용」으로 통과해 **남의 트리 소스를
시험할 수 있었다.** 지금은 지을 때 `<venv>/.colab-worktree` 에 **워크트리 절대경로 + 파이썬 판**을 박고,
다음 회차에 그 스탬프를 되읽어 없거나·다른 트리를 가리키거나·판이 다르면 다시 짓는다
(`pyvenv.cfg` 의 `version`/`version_info` 도 교차로 본다). 위 「스탬프 훼손 실험」 행이 그 실측이다.

---

## S4 — 회차 비용 (턴 수·토큰)

| 이전 | 목표 | 측정 시점 |
|---|---|---|
| **미측정** | 기록만(판정 없음) | `effortLevel: high` 적용 전후 |

`.claude/settings.json` 의 `effortLevel: high` 는 **프로젝트 스코프**다(글로벌은 건드리지 않았다 — J-10).
⚠ 이 값은 **세션 루트가 `30 CoLAB-v2` 로 옮겨진 뒤에 발효한다**(스펙 0-3 · V1: `settings.json` 은 하위 폴더
스코프가 없다). 그 전의 회차 비용을 「high 적용 후」로 적으면 거짓이 된다.

---

## S5 — 판정 재개봉

| 이전(실측) | 목표 |
|---|---|
| 2026-09-05 **16건** + rev2 **3건** | 회차 종료 후 **0** |

근거 = 메모리 `ted-decisions-260905-prd` · `ted-decisions-260906-rev2`. 확정 판정을 개발 세션에서 다시 여는 것이
재개봉이고, 세는 자리는 intent 확인절 대조다(스펙 A-2).

---

## 전수 실측 — P-E 적용 뒤 (이 워크트리 · `-j 4`)

2026-09-06 · `bash gates/run.sh all -j 4` · **17.1분** · 50 게이트(단독 8 · 병렬 42 · 미선언 0).

| | 건수 |
|---|---|
| green | **49** |
| red(판정) | **1** — `planning-freshness` |
| **red(준비)** | **0** ← S3 목표 달성 (16 → 0) |
| red(준비·입력미선언) | 0 |

- **red(준비) 0 이 P-E 의 판정값이다.** 같은 워크트리의 이전 조건(env 미구축 + env 미source)에서
  이 자리는 16 이었다. 게이트 로직은 한 줄도 바뀌지 않았고, **값이 선언되는 자리만** 옮겼다.
- `service-tests-*` 4종 · `frontend-*` 3종 전부 green — 이 7종이 D1(venv·node_modules 미승계)의 직접 피해자였다.
- `schema-diff` · `autometa-loss` · `preview-tile-slot` · `artifact-ownership` green — 이 4종이
  D2(테스트 env 미source)의 직접 피해자였다. 이제 `run.sh` 가 스스로 읽는다.

**⚠ 남은 red(판정) 1건은 P-E 소관이 아니다.** `planning-freshness` 는 기획 정본 폴더를 **레포 상위의
형제 폴더**(`../40 COLAB-기획`)로 찾는데, 워크트리는 `.claude/worktrees/<이름>/` 아래에 있어 그 상대
경로가 `.claude/worktrees/40 COLAB-기획` 로 풀린다 — 실물이 없다. 축자 로그:

```
::error::planning-freshness red — 1건
  - 정본 폴더가 없다 (위치 확인 — planning/README.md §1): .../.claude/worktrees/40 COLAB-기획/...
```

**이 red 는 워크트리 경로가 낸 것이지 이 회차의 변경이 낸 것이 아니다.** 반증 —
`run.sh` 를 거치지 않고 `python3 dev-package/tools/check-package-freshness.py` 를 직접 돌려도
**같은 한 줄로 red** 다(env source 경로를 타지 않는다). 고칠 자리도 이미 있다 —
`check-package-freshness.py:38` 의 `COLAB_PLANNING_ROOT` 가 기준점을 받는 구멍이다.
게이트 로직 소관이라 P-E 에서 손대지 않았다(D16 계열 · 후속).
⚠ 「main 과 동일」로 수용하지 않는다 — **원인과 고칠 자리를 적어 남긴다.**

---

## 이 문서를 다시 쓸 때

- 수를 고치면 **근거 경로를 같이 고친다.** 경로 없는 수는 다음 회차에 「어디서 나온 값인가」로 20분을 먹는다.
- 「좋아졌다」를 적지 않는다 — **이전/이후 두 수와 측정 시점**을 적는다. 판정은 읽는 사람이 한다.
- 아직 안 잰 칸은 **비워 두고 「안 쟀다」고 적는다.** 0 으로 채우지 않는다(green-by-skip 의 문서판이다).
