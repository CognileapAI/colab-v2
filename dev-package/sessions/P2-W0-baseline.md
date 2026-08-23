# P2 · W0 기준선 실측 (P2-W0-baseline)

> **측정 전용 세션이다.** 소스·설정·컨테이너를 하나도 바꾸지 않았다. 읽기와 `curl`·`docker ps`·게이트·시험 실행만 했다.
> **측정 일시** 2026-08-23 · 실행 위치 = 워크트리 `.claude/worktrees/p2-exec`
> **근거** `P2-EXEC.md §2 「기준선 실측 (생략 금지)」` · `03-HANDOFF §4.5` · `gates/README.md`
> **서술 규약** — 증거(명령 + 실제 출력)와 해석을 갈라 적는다(`M-5`). 관측하지 않은 수는 적지 않는다(`M-4`).
> **절대경로를 적지 않는다**(`CLAUDE.md §3-8`). 출력에 절대경로가 있던 자리는 `…` 로 줄였다.

---

## A. `03-HANDOFF §4.5` 진입조건 4행

### A. 증거

| # | 확인 | 명령 | 실제 출력 (발췌 아님 — 판정에 쓰인 줄 전부) | 판정 |
|---|---|---|---|:--:|
| 1 | 기획 정본이 읽히는가 | `./gates/run.sh planning-freshness` | `::error::planning-freshness red — 1건` / `  - 정본 폴더가 없다 (위치 확인 — planning/README.md §1): …/.claude/worktrees/40 COLAB-기획/Co-Lab_ver2_1차마일스톤_목업패키지_260818_이태헌/에픽` | **red** |
| 1-보조 | 정본 폴더 실재 확인 | `ls -d "<작업공간>/40 COLAB-기획/Co-Lab_ver2_1차마일스톤_목업패키지_260818_이태헌/에픽"` | 경로 출력 + `EXISTS` | 존재함 |
| 1-보조 | 게이트의 경로 해석 | `grep -n "40 COLAB" dev-package/tools/check-package-freshness.py` | `28:#   <작업공간>/30 CoLAB-v2/dev-package/tools/  →  <작업공간>/40 COLAB-기획/<정본>` / `32:    os.path.dirname(_REPO_ROOT), "40 COLAB-기획",` | — |
| 2a | 워크트리가 원격과 같은가 | `git status -sb` (워크트리) | `## worktree-p2-exec...origin/main` (변경 파일 0줄 · ahead/behind 표기 없음) | **green** |
| 2b | 메인 체크아웃 | `git -C "<메인 체크아웃>" status -sb` | **실행 거부됨** — 이 세션은 워크트리에 격리되어 있어 공유 체크아웃을 향한 git 명령이 하네스에서 차단된다 | **[미확인]** |
| 3 | gh 인증 | `gh auth status` | `github.com` / `  ✓ Logged in to github.com account sungwooHa (…/gh/hosts.yml)` / `  - Active account: true` / `  - Git operations protocol: https` / `  - Token: gho_************************************` / `  - Token scopes: 'gist', 'read:org', 'repo', 'workflow'` | **green** |
| 4a | staging 컨테이너 | `docker ps --filter name=colab_v2_staging --format '{{.Names}}\t{{.Status}}'` | `colab_v2_staging_frontend  Up 59 minutes (healthy)` / `colab_v2_staging_viz_render  Up 59 minutes (healthy)` / `colab_v2_staging_core_api  Up 59 minutes (healthy)` / `colab_v2_staging_pipeline_worker  Up 59 minutes (healthy)` / `colab_v2_staging_ai_service  Up 59 minutes (healthy)` / `colab_v2_staging_nginx  Up 7 hours (healthy)` / `colab_v2_staging_pg  Up 7 hours (healthy)` / `colab_v2_staging_cloudflared  Up 7 hours` · `COUNT=8` | **8/8** |

#### A-4b. 헬스 6종 — 상태 코드 **와 본문**

> `RESTART.md §2-③`·`I2.md:180` — **자리표시 오리진도 루트에 200 을 낸다.** 그래서 본문까지 대조한다.
> 기대 본문의 정본은 `sessions/I2.md:18-24` 표다.

명령 (경로마다 1회씩):

```
curl -s -w '\n[HTTP %{http_code}]\n' https://www.colab-hydro.com/healthz
curl -s -w '\n[HTTP %{http_code}]\n' https://www.colab-hydro.com/healthz/<unit>
```

| 경로 | 코드 | 실제 본문 (그대로) | 기대 본문 (`I2.md:18-24`) | 본문 일치 |
|---|:--:|---|---|:--:|
| `/healthz` | 200 | `ok` | `ok` | ✅ |
| `/healthz/core-api` | 200 | `{"unit":"core-api","status":"alive","implemented":true}` | 동일 | ✅ |
| `/healthz/frontend` | 200 | `{"unit":"frontend","status":"alive","implemented":true}` | 동일 | ✅ |
| `/healthz/pipeline-worker` | 200 | `{"unit": "pipeline-worker", "status": "alive", "implemented": false}` | `…"implemented": false` | ✅ |
| `/healthz/viz-render` | 200 | `{"unit": "viz-render", "status": "alive", "implemented": false}` | `…"implemented": false` | ✅ |
| `/healthz/ai-service` | 200 | `{"unit": "ai-service", "status": "alive", "implemented": false}` | `…"implemented": false` | ✅ |

**A 집계 — 6행 중 green 4 · red 1(1번) · 미확인 1(2b).** 헬스는 6/6 코드·본문 모두 일치.

### A. 해석 `[잠정]`

- **호스트는 재부팅되지 않았다.** 컨테이너 8개가 `Up 7 hours` / `Up 59 minutes` 로 서 있고 단위별 본문이 I2 판이다. `RESTART.md` 절차는 이번 회차에 필요 없었다. **조용한 롤백(자리표시 오리진)도 아니다** — 자리표시라면 `/healthz/<unit>` 5종이 단위 JSON 을 낼 수 없다.
- **1번 red 는 워크트리 부작용으로 보인다** `[잠정]`. 게이트는 정본 폴더를 **레포 루트의 형제**로 계산하는데(`check-package-freshness.py:32`), 워크트리 루트가 `.claude/worktrees/p2-exec` 라서 `.claude/worktrees/40 COLAB-기획` 을 찾는다. 실제 정본은 메인 체크아웃의 형제 자리에 **실재한다**(A-1 보조행). 즉 「정본이 사라졌다」가 아니라 「게이트를 워크트리에서 돌렸다」다.
  - **다만 이것은 추론이지 실측이 아니다.** 메인 체크아웃에서 이 게이트를 돌린 출력을 나는 갖고 있지 않다. **W1 착수 전 메인 세션이 메인 체크아웃에서 `./gates/run.sh planning-freshness` 를 1회 돌려 green 을 확인**해야 A-1 이 실측으로 닫힌다.
- **2b 는 측정 불가였다** — 세션 격리 가드가 공유 체크아웃 대상 git 실행을 거부했다. 우회하지 않았다. 메인 세션이 직접 확인할 몫이다.
- gh 토큰 스코프에 `repo`·`workflow` 가 있어 P2 레인의 push·CI 조회에 부족함은 관측되지 않았다.

---

## B. 게이트 기준선 (P2 착수 시점)

### B. 증거

전부 워크트리 루트에서 `./gates/run.sh <gate>` 로 1회씩 실행. 마지막 판정 줄을 그대로 옮긴다.

| # | 게이트 | 판정 줄 (그대로) | 판정 |
|---|---|---|:--:|
| 1 | `contract-lint` | `contract-lint green — seam 3건, 룰 위반 0.` | **green** |
| 2 | `contract-breaking` | `contract-breaking green — 기준 HEAD (3건) 대비 파괴적 변경 없음.` | **green** |
| 3 | `event-lint` | `event-lint green — 스키마 2건 컴파일 · valid 5건 통과 · invalid 8건 거부.` | **green** |
| 4 | `event-breaking` | `event-breaking green — 기준 HEAD (2건) 대비 파괴적 변경 없음.` (`# 판정 — ERR 0건 · WARN 0건`) | **green** |
| 5 | `seam-consistency` | `seam-consistency green — G-e 258건 · G-b 7건 · ㉠ 0건 · ㉡ 15건.` | **green** |
| 6 | `import-boundary` | `Contracts: 8 kept, 0 broken.` / `import-boundary green — 계약 전부 통과.` | **green** |
| 7 | `banned-import` | `banned-import green — .py 59건, 금지 import 0.` | **green** |
| 8 | `ai-no-lineage-write` | `ai-no-lineage-write green — 계약·코드·체인 세 층 모두에서 쓰기 경로가 없다.` | **green** |

`seam-consistency` 부가 출력 (그대로):

```
# ㉠ — 기준선 대비 신설 검사 대상 0건 (신설 0건이면 대조할 것이 없어 green 이다 — 기준선이 곧 현재라는 뜻)
# ㉡ — 단계 15건 재생 (이월 1건)
#   ↩ 단계 11(직접 검색으로 부모 추가) — 의도적 이월: 계약 부재 — 의도적 P4 이월. fe-core.yaml 위임 산문에 「P4 가 연다」 명기 (D2c §2-3 · §10-3)
# ㉡ 끊긴 자리: 없음 (㉡-4)
```

`import-boundary` 계약 8건 (전부 `KEPT`): 배포 단위 4개 상호 미import · core-api 층 · D2·D3·D4·D6·D8 상호 미참조 · D1 미import · ai-service 층 · pipeline-worker 층 · viz-render 층 · D10→D9 Port 전용.

`banned-import` 단위별 대상 (그대로): `ai-service .py 7건 · deny 7개` / `core-api .py 28건 · deny 18개` / `pipeline-worker .py 17건 · deny 0개` / `viz-render .py 7건 · deny 0개`.

**B 집계 — 요구된 8게이트 전부 green. red 0건.**

> **범위 밖(측정하지 않음)** — `generated-up-to-date`(HANDOFF 가 실사유 red 로 이미 등재) · `schema-diff`(env 의존) · `migration-single-head` · `rls-coverage` · `rls-effect` · `selftest` 계열. `P2-EXEC §2` 가 기준선으로 지정한 것이 위 8종이라 그대로 8종만 쟀다. **재보지 않았다는 뜻이지 green 이라는 뜻이 아니다.**

### B. 해석 `[잠정]`

- **P2 가 딛고 서는 계약면은 착수 시점에 흔들리지 않는다.** 계약 4종이 전부 green 이므로 W1(`P2-db`) 이후 어느 레인에서든 이 8종 중 하나가 red 로 돌아서면 **그것은 그 레인이 만든 것**이다. 기준선의 쓸모가 여기다.
- **`seam-consistency` 의 `㉠ 0건` 은 「검사했더니 문제가 없다」가 아니라 「검사 대상이 없다」다.** `gates/README.md` 가 명시한 대로 ㉠ 은 **개정 회차의 게이트**이고 소급 감사가 아니다. P2 가 op·스키마를 신설하면 그때 비로소 대조가 생긴다 — **P2 레인은 ㉠ 이 자기 회차에 살아난다는 전제로 근거란을 채워야 한다.**
- **`banned-import` 의 `pipeline-worker deny 0개` 는 정상이다.** geo 라이브러리 금지는 core-api 전용 규칙이고 D5 는 rasterio 를 정당하게 쓴다.
- **`ai-no-lineage-write` green 의 현재 의미는 좁다** — `gates/README.md` 가 경고한 「AI 가 계보에 안 쓴다」와 「AI 가 아직 없다」의 구분 문제가 여전히 살아 있다. P2 는 D10 을 만들지 않으므로 이 게이트의 정보량은 P2 동안 늘지 않는다.

---

## C. D5 시험 32건 재실행 — 자기 보고 → 실측

> **왜 재는가.** `P2-EXEC §1` 이 `P2-pipeline` 레인의 성격을 「4종 파서를 만든다」에서 「이미 있는 판정을 이벤트로 내보낸다」로 **좁혔는데, 그 좁히기의 근거가 D5 의 자기 보고였다.** 여기서 실측으로 올린다.

### C. 증거

호출 방식의 정본 = `sessions/D5.md §재현`. 워크트리에는 `.venv` 가 없어 **메인 체크아웃의 `services/pipeline-worker/.venv` 인터프리터를 그대로 썼다**(pytest rootdir·`pythonpath` 는 `pyproject.toml [tool.pytest.ini_options]` 에 따라 워크트리 기준으로 잡힌다). 워크트리에는 아무것도 만들지 않았다.

실행 위치 = `services/pipeline-worker/`.

| # | 명령 | 실제 마지막 줄 | passed | failed | skipped |
|---|---|---|:--:|:--:|:--:|
| 1 | `COLAB_REFERENCE_DATA=<원천> <venv>/bin/python -m pytest tests/ -q -rs` | `32 passed, 8 warnings in 4.60s` | **32** | **0** | **0** |
| 2 | `<venv>/bin/python -m pytest tests/ -m "not e2e" -q` | `26 passed, 6 deselected in 1.89s` | 26 | 0 | 0 (deselected 6) |
| 3 | `COLAB_REFERENCE_DATA=<원천> <venv>/bin/python -m pytest tests/ -m e2e -q` | `6 passed, 26 deselected in 4.27s` | 6 | 0 | 0 (deselected 26) |
| 4 | `<venv>/bin/python -m pytest tests/ -q -rs` (**환경변수 없이**) | `6 failed, 26 passed in 2.70s` | 26 | **6** | **0** |

- **`-rs`(skip 사유 보고)를 붙였고, 어느 실행에서도 skip 요약이 출력되지 않았다.** 즉 **skip 0건**이며 이름을 댈 skip 테스트가 없다.
- 실행 4 의 실패 메시지 (그대로): `Failed: COLAB_REFERENCE_DATA 가 원천 디렉터리를 가리키지 않는다 — E2E 는 skip 하지 않는다` (`tests/test_e2e_real.py:27`)
- 원천 마운트 = 작업공간의 `03 Reference-Data`(`DATA-REFERENCE.md:34` 가 가리키는 그 원천). 환경변수로만 넘겼고 레포에 경로를 쓰지 않았다.
- 경고 8건은 전부 `DeprecationWarning`(NumPy 2.5 shape 설정, `tests/fixture_builders.py`) 과 `NotGeoreferencedWarning`(rasterio, 의도된 픽스처) 이다. 실패로 이어진 것은 없다.
- 구성 대조 — `D5.md:25` 가 적은 「단위 26(`test_detect` 8 · `test_cog_classify` 4 · `test_grid_and_hsr` 8 · `test_pipeline` 6) + E2E 6」의 **26/6 분할은 실행 2·3 에서 그대로 재현됐다.** 파일별 8/4/8/6 내역은 이번 실행에서 개별 집계하지 않았다 — **[미확인]**.

**C 집계 — 32 passed · 0 failed · 0 skipped. 이름 댈 skip 테스트 없음.**

### C. 해석 `[잠정]`

- **D5 의 자기 보고가 실측으로 확인됐다.** 32건이 실제로 32건이고, **green-by-skip 이 아니다.** 따라서 `P2-EXEC §1` 의 「`P2-pipeline` 레인 성격 변경」은 이제 자기 보고가 아니라 측정 위에 서 있다.
- **E2E 6건은 fail-closed 다 — 이 프로젝트가 v1 에서 당한 실패를 D5 가 구조적으로 막아 뒀다.** 원천 마운트가 없으면 **skip 이 아니라 fail** 한다(실행 4). `CLAUDE.md §4 게이트 정책` 이 말하는 「DB 없이 돌아 RLS 를 green-by-skip 했던」 무늬가 여기서는 재현되지 않는다. **레인은 이 성질을 깨지 않아야 한다** — E2E 를 `skipif` 로 바꾸는 편의 수정은 금지다.
- **다만 32 green 이 「P2-pipeline 이 쉽다」는 뜻은 아니다.** `P2-EXEC §1` 이 비어 있다고 적은 셋(outbox/워커 · `d5_*` DB 원장 · `renderable` 판정)은 **시험 32건이 검사하는 대상이 아니다.** 32 green 은 「감지·파싱·좌표·COG 판별이 산다」까지만 말한다. 그 셋은 여전히 0 에서 시작한다.
- E2E 가 원천을 실제로 읽고 통과했으므로, `W0-1` 채택 조건 ⓐ(실물 16건 전건 축 판별) 를 **같은 실행 경로 위에서** 잴 수 있다 `[잠정]`. 다만 ⓐ 는 이 세션의 측정 범위가 아니었고 **재지 않았다**.

---

## 종합 — W1 착수 판단에 필요한 것

| 구획 | green | red | 미확인 |
|---|:--:|:--:|:--:|
| A 진입조건 | 4 (git 워크트리 · gh · 컨테이너 8/8 · 헬스 6/6 본문 대조) | 1 (`planning-freshness`) | 1 (메인 체크아웃 `git status -sb`) |
| B 게이트 | 8 / 8 | 0 | — |
| C D5 시험 | 32 passed | 0 failed | 0 skipped |

**W1 을 막을 만한 red 는 관측되지 않았다** `[잠정]`. 남은 두 자리는 둘 다 **메인 세션이 메인 체크아웃에서 1회 실행하면 닫힌다**:

1. 메인 체크아웃에서 `./gates/run.sh planning-freshness` — green 확인 (워크트리 red 가 경로 부작용이라는 추론을 실측으로 바꾼다)
2. 메인 체크아웃에서 `git status -sb` — clean + ahead/behind 0 확인

> **이 두 줄을 확인하지 않은 채 「A 전행 green」이라고 적으면 그것이 `M-4` 다.** 여기서는 적지 않았다.


---

## 보론 — 메인 세션이 닫은 두 줄 (2026-08-23, 이 세션)

에이전트가 워크트리 격리 때문에 못 닫은 두 칸을 메인 세션이 직접 재고 기록한다. **증거**다.

| 칸 | 명령 | 결과 |
|---|---|---|
| `planning-freshness` | 메인 체크아웃에서 `./gates/run.sh planning-freshness` | **green** — 「15개 임베드 블록 전부 원본과 일치」. 즉 본문의 red 는 **정본 폴더 부재가 아니라 워크트리 경로 부작용**이었다는 잠정 해석이 **확인됐다**(게이트는 레포 루트의 형제 자리에서 정본을 찾는다) |
| 메인 체크아웃 `git status` | 세션 격리 진입 **이전에** 메인 체크아웃에서 실행한 `git status --porcelain` | **출력 0줄 = clean.** HEAD `00dcac7` (`git worktree list` 로 교차 확인) |

> ⚠ **한계를 적어 둔다** — 두 번째 칸은 **세션 격리 진입 이전 시점**의 측정이다. 그 뒤 메인 체크아웃을 건드리지 않았으므로 여전히 clean 이라고 보지만, **그 「여전히」는 해석이지 측정이 아니다**(`M-5`). 워크트리에서 작업하는 한 메인 체크아웃은 이 세션의 쓰기 대상이 아니다.

**따라서 A(진입조건 4행)는 4/4 로 닫힌다.** 기준선 종합 = **A 4/4 · B 게이트 8/8 green · C D5 32 passed / 0 failed / 0 skipped.**
