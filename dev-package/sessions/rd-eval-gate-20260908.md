# rd-eval-gate — WU-D7 승격 준비 (2026-09-08 · 라운드 R-D-2)

- 레인 `rd-eval-gate` · 브랜치 `lane/wu-d7` · 기점 `origin/integration/r-d` = `1982600`.
- 근거 = `dev-package/prd/rounds/R-D-2-harness-eval.md` §2 WU-D7 · `dev-package/prd/specs/R-D.md:39` · intent `dev-package/intent/2026-09-08-harness-evals.md` Q6·Q7·Q10.
- 제품 코드 0 · 계약 0 · 마이그레이션 0 · **실제 모델 호출 0회**.

## 전 / 후

| 자리 | 전 | 후 |
|---|---|---|
| `gates/run.sh` `ALL_GATES` | 56개 · `harness` 0건 | **58개** · `harness-eval` · `harness-eval-selftest` |
| dispatch | 해당 case 0 | case 2건 신설 |
| `gates/tools/` | `harness-eval*` 부재 | `harness-eval.sh` · `harness-eval-selftest.sh` · `ci-filter-check.py` |
| `gates/config/parallelism.toml` | 선언 없음 | `"harness-eval" = "serial"`(시간·달러 상한을 재므로 경합이 판정을 흔든다 — `render-latency` 와 같은 배치) |
| `gates/README.md` | 행 0 | 게이트 표 2행 ＋ selftest 케이스수 표 1행 ＋ CI 잡 표 1행 |
| `.github/workflows/ci.yml` | filters 9 · `secrets.` 참조 0 | filters **10**(`harness`) ＋ `outputs.harness` ＋ 잡 `harness-eval` |

## 세 상태 — 실측 exit

| 선언 | 기대 | 실측 | 요약줄 |
|---|---|---|---|
| `COLAB_HARNESS_EVAL_EXEMPT=1`(과제 3건 · 임시 뿌리) | green | **0** | `harness-eval green — 면제 선언 · 과제 3건(미실행)` |
| `COLAB_HARNESS_EVAL_EXEMPT=1`(이 트리 · 과제 **0건**) | red(판정) | **1** | `::error::harness-eval red(판정) — 면제 선언인데 **과제 0건**이다` |
| `COLAB_HARNESS_EVAL=1` ＋ 스텁 `sleep` 4s > 상한 1s | red(준비) | **78** | 러너 exit 78 을 그대로 전달 |
| 둘 다 미선언 | red(준비·입력미선언) | **78** | `cause=입력미선언\|missing=COLAB_HARNESS_EVAL` |
| 둘 다 `=1` | 실행이 이긴다 | 출력에 「면제 선언은 무시했다」 기재 | — |

- 값 대조는 **`=1` 하나뿐**(`ship.sh` 규약). `true`·`yes`·`0` 은 미선언으로 읽힌다.
- ⚠ **이 트리의 과제 0건은 정상이다** — `eval/harness/H01..H20` 은 형제 레인 `lane/wu-d6` 것이고 아직 얹히지 않았다. 건수는 **게이트 실행 시점에** 센다(하드코딩 0건).

## RED → GREEN

- RED(선실측) — 게이트 스크립트 부재 상태에서 selftest 실행: `::error::harness-eval-selftest red — 판정 재료가 없다: gates/tools/harness-eval.sh` · exit **1**.
- GREEN — `harness-eval-selftest` **4/4**(green 1 · red(판정) 1 · red(준비) 1 · red(준비·입력미선언) 1) ＋ CI 필터 대조.
- 대조부 자체의 fail-closed 실측 — `harness` 필터의 `.claude/skills/**` 를 `frontend/**` 로 바꾼 사본에 물리니 **exit 1 · 지적 3건**(㈏ 패턴 불일치 · ㈐ 스킬 경로 미포착 · ㈑ 제품 경로 포착).

## CI 필터 대조 (`gates/tools/ci-filter-check.py`)

- 결과 green — 패턴 4개 · 잡히는 경로 4건(`CLAUDE.md`·`.claude/skills/…`·`hooks/…`·`agents/…`) · 안 잡히는 경로 3건(`frontend/src/a.tsx`·`services/core-api/…`·`dev-package/…`) · `outputs.harness` 있음 · 잡 `harness-eval` 조건·시크릿 참조 확인 · `continue-on-error` 0건.
- 검사 7종 = ㈎ 필터 존재 ㈏ 패턴 집합 축자 ㈐ 양성 ㈑ 음성 ㈒ outputs ㈓ 잡 조건 ㈔ 시크릿 참조만·값 0.

## `[미상]`

- **`dorny/paths-filter` 의 실제 GitHub 평가** — 로컬 실행 불가 · `act` **부재**(`command -v act` 0건). 여기서 잰 것은 glob 문법의 뜻이다.
- **`secrets.ANTHROPIC_API_KEY` 실재 여부** — 레포 시크릿을 이 자리에서 조회하지 않았다. 발급은 Ted 몫이고, 부재 시 잡은 exit 78(red 준비)로 끝난다.
- **실행 모드(`COLAB_HARNESS_EVAL=1`)의 실제 러너 판정** — 과제 0건 트리라 재지 않았다.

## 하지 않은 것

- 실제 모델 호출 **0회**(모든 케이스가 `PATH` 앞 스텁 · 과제 뿌리는 `mktemp -d`).
- 승격 **미실시** — CI 잡·로컬 `all` 둘 다 면제 모드. 실행 모드 전환은 별건.
- 시크릿 **값 기입 0** · `continue-on-error` 0 · `eval/harness/**` 무접촉(읽기만).
- 대장·`03-HANDOFF`·`PLAN-SoT` 무접촉(오케스트레이터 몫).

## intent 대조 — `dev-package/intent/2026-09-08-harness-evals.md`

| 항목 | 상태 |
|---|---|
| Q6 과제 형식 `H<번호-이름>/{task.md,fixture/,expect.sh}` | 충족 — 건수 세기가 `H??-*/` 를 그 형식대로 센다(`_template/` 은 그 모양이 아니라 빠진다) |
| Q7 상한 · 초과 = red(준비) | 충족(전달) — 게이트는 상한을 정하지 않고 러너 exit 78 을 그대로 낸다 |
| Q10 승격 — 게이트 등재 · 로컬 `all` 명시 면제·건수 노출 · CI paths-filter 잡 | 충족 |

- **미달 1** — Q10 의 「3회 연속 2/2 green」 **기록 0회**. 막는 것 = 과제 20건이 이 트리에 없다(WU-D6). 실행 모드 전환은 그 뒤 별건.
- **미달 2** — Q7 의 상한 실측값(p95×2 · 예산) 확정은 WU-D6 몫이라 이 레인에서 재지 않았다.
- **초과 2** — ⑴ `gates/README.md` selftest 케이스수 표 1행 ＋ CI 잡 표 1행(지시문은 「2행」). 근거 = 두 표가 각각 「selftest 전부」·「CI 잡 전부」를 열거하므로 빠지면 그 자리가 낡는다. ⑵ `gates/tools/ci-filter-check.py` 를 별도 파일로 분리(지시문이 「or inline in the selftest」로 허용한 갈래 중 파일 쪽).

## 후속 (이 레인 밖)

- `eval/harness/H01..H20` 병합 뒤 `COLAB_HARNESS_EVAL_EXEMPT=1 ./gates/run.sh harness-eval` 이 `과제 20건` 을 찍는지 1회 확인. **과제 0건이면 `all` 이 red(판정)** 이다 — 설계대로다.
- `secrets.ANTHROPIC_API_KEY` 발급(Ted) → CI 잡의 78 이 사라지는지 확인.
- 3회 연속 2/2 green 뒤 `ci.yml` 의 `COLAB_HARNESS_EVAL_EXEMPT: '1'` → `COLAB_HARNESS_EVAL: '1'` 별건 변경.
