# WU-D6 · 하네스 eval 과제 20건 ＋ 첫 실측 — 레인 `rd-eval-tasks` (2026-09-08)

기준 `origin/integration/r-d` = **`7a97259`**(그 뒤 통합은 `1982600` 로 앞섬 · WU-D2·D3) · 라운드 `prd/rounds/R-D-2-harness-eval.md §2 WU-D6` · 로스터 정본 `intent/2026-09-08-harness-evals.md`(표 20행 · 재작성 없음) · 제품 코드 0 · 계약 0 · 대장 0 · 픽스처 sha 둘 **OLD `947bf1f`**(검수 실측 기준 트리)·**CUR `7a97259`**, 재현 명령은 각 `fixture/SOURCE.md`.

## 1. 과제 20건 (id · 묶음 · 픽스처 원천 · expect 요지)

| id | 묶음 | 픽스처 원천 `sha:path` | expect(양성 / 음성) |
|---|---|---|---|
| H01 | 가 | CUR:`CLAUDE.md`(118-127) · CUR:`03-HANDOFF.md`(29-33) | `판정: 낡음`＋`git log`＋sha / `다음 단계:…R-C` |
| H02 | 가 | CUR:`skills/design-review/scripts/css_audit.py` ＋ 새 `sample.css` | `주석분 0건`＋`13px 미만 1건` / `2·3·4건` |
| H03 | 가 | CUR:`skills/VENDORED.md`(1-14) ＋ 빈 줄 1줄 심음 | `빈 줄 13행`＋`떨어진 행 2건`＋`sed -n` / 계수 오답 |
| H04 | 나 | OLD:`detail.css`·`tokens.css` | `판정: 없음`＋`4.66` / `실측…3.71` |
| H05 | 나 | OLD:`lineage.css` | `판정: 없음`＋`흐림 0건` / `opacity: 0.x` 지어냄 |
| H06 | 나 | OLD:`catalog.css` | `있음`＋`catalog.css:31`＋예외 `.colmenu` / 근거에 `colmenu` |
| H07 | 나 | OLD:`lineageGraph.css` | `건수 13`＋`최소 10px` / `9~12`(소수점 누락) |
| H08 | 나 | OLD:`detail.css`·`upload.css`·`lineageGraph.css` | `지목 7곳`＋3앵커＋`.vizerr` 무접촉 / `20~49곳` |
| H09 | 나 | OLD:`detail.css`·`catalog.css`·`tokens.css` | `있음`＋`detail.css:59`·`:62` / 「토큰이 다르다」 |
| H10 | 나 | OLD:`detail.css`·`shell.css` | `2건`＋`detail.css:93`·`shell.css:58` / `0·1건` |
| H11 | 나 | OLD:`lineageGraph.css`·`tokens.css`·`detail.css` | `:33`이`:29`덮음＋`참조 11건` / `6~10건`(가짓수 8) |
| H12 | 나 | CUR:`catalog.css`(134-136 삭제)·`CatalogTable.tsx` | `있음`＋`.lvl-3`＋무색 증상 / `.lvl-0~2` 지목 |
| H13 | 나 | OLD:`catalog.css`·`tokens.css` | `3.41`＋`있음`＋제안 / **수정 명령·수정 완료** |
| H14 | 다 | `SKILL.md:65` 모양 → 새 셸 `check-config.sh` | `결함 있음`＋현`exit 0`＋옳은`red(준비)·78` / `옳은…exit 0` |
| H15 | 다 | `SKILL.md:66` → `check-manifest.sh`＋`manifest.txt` | `대상 0건`＋「0건은 red」 / 「그대로 두면 된다」 |
| H16 | 다 | `SKILL.md:67`·`:69` → `check-coverage.sh`＋`cases.txt` | `COLAB_MIN_CASES`＋세 상태(면제=건수·무언=78) / 「기본값 유지」 |
| H17 | 다 | `SKILL.md:68` → `check-schemas.sh`＋`schemas/`3 | `숨은 계수 SKIPPED`＋건너뛴 건수 노출 / `결함 없음` |
| H18 | 다 | `SKILL.md:69` → `gate-render-latency.sh` | 세 상태＋`상태3 무언…exit 78` / `상태3…exit 0·생략` |
| H19 | 라 | CUR:`catalog.css`·`project.css`·`tokens.css` | `4.23`＋`2곳`＋`catalog.css:140`·`project.css:528` / `1곳` |
| H20 | 라 | CUR:`CLAUDE.md`(129-145)·`03-HANDOFF.md`(70-80)·`work-items.yaml`(3113-3124) | `먼저…work-items`＋`두 번째…HANDOFF` / `먼저…HANDOFF` |

(나) 8건은 결함이 **심긴 옛 트리 사본** · H04·H05 는 **음성 판정** · (다) 5건은 `SKILL.md` 모양 다섯을 담은 **새 셸**(라운드 §2 축자). **선검증** — 커밋 전 `expect.sh` 20건에 이상적 답·어긋난 답 두 벌을 먹여 **20/20 기대대로**(모델 호출 0회).

## 2. 스모크 (`COLAB_EVAL_ONLY=H01` · 2회차)

- **판본·모델** `claude` **2.1.263** · `claude-fable-5-1`(＋`claude-haiku-4-5` 보조) — 러너가 모델을 지정하지 않아 환경 기본값.
- **비용 필드 이름 = `total_cost_usd`** 실재(`cost_usd` 없음) → README `[미상]` **닫음**. **`--allowedTools` 공백 항목은 쪼개지지 않는다** — H02 가 `Bash(python3 {FIXTURE}/css_audit.py --root {FIXTURE}:*)` 를 실제로 써서 green 2/2 · `permission_denials` **`[]`** → 두 번째 `[미상]` **닫음**.
- **초안 예산 `0.50` 은 바닥 미달** — 1턴에 `total_cost_usd 0.713246` · `subtype: error_max_budget_usd` · rc 1 → red(준비)(설계대로).

⭑ 원인은 과제 본문이 아니라 **호출마다 실리는 컨텍스트**다 — cwd 가 레포 안이라 프로젝트 `CLAUDE.md`＋`rules/colab-rules.md` 가 매번 적재되고 `cacheCreationInputTokens 34840` 이 1턴 비용의 거의 전부다. 그래서 첫 실측은 예산 **3.00** 으로 돌렸다.

## 3. 첫 실측 — 회차 1 / 3 · `results/20260908-161538/`

`COLAB_EVAL_TIMEOUT=180 COLAB_EVAL_BUDGET=3.00 bash eval/harness/run.sh` 1회 · 20건×2회 = **40 실행**.
요약줄 축자 — `과제 20 · 실행 40 · green 15 · 불안정 5 · 준비 0 · 초 p50 32.8/p95 46.4 · USD 합 32.4506`
(러너 `불안정` 칸은 판정 red 전체 — 내역 **1/2 불안정 2 · 0/2 실패 3**). 과제별 20행 표는 그 `summary.md`.

- **계수** green **15** · 불안정(1/2) **2** · 실패(0/2) **3** · 준비 **0** · 묶음별 (가)3/3 · (나)9/10 · (다)**1/5** · (라)2/2.
- **초** p50 **32.8** · p95 **46.4** · 최대 46.6 · **USD** 합 **32.4506** · 1실행 평균 0.81 · **1회 최대 1.0067**(H08) · 2회 합 최대 1.9523.
- **README 기입** `COLAB_EVAL_TIMEOUT` = 46.4×2 = 92.8 → **93** · `COLAB_EVAL_BUDGET` = 1.0067×2 = 2.0134 → **2.01** · 남은 `[미측정]`·`[미상]` **0건**.

| red 5건 | 판정 | 사유(무수정) |
|---|---|---|
| H09 | 1/2 | 같은 근거(`detail.css:59`·`:62` · 토큰 둘 다 `--color-border`)를 적고 1회차 `있음` · 2회차 `없음`. 과제문이 「있음」을 「검수 지적이 해당한다」로 못 박지 않았다 |
| H14 | 0/2 | `결함 있음`·현 `exit 0`·옳은 `red(준비)` 까지 옳고 **`exit 1`·`exit 2`** 로 끝냄. **`78` 이 픽스처 어디에도 없다** |
| H15 | 1/2 | 두 회차 다 `대상 0건`·`exit 1` 로 옳게 답. expect 가 자유 서술 칸에 `red`·`실패` **낱말**을 요구해 1회차 불통과 |
| H16 | 0/2 | `COLAB_MIN_CASES` 지목·세 상태 제안 옳음. `상태3 무언` 을 `exit 1` 로 적음(78 요구) ＋ 2회차는 `상태2` 「건수」 낱말 부재 |
| H18 | 0/2 | 세 상태를 옳게 가르고 `상태3` 을 「red(준비)로 실패」라 적었으나 `exit 1`(78 요구) |

⭑ **(다) 4건이 한 뿌리다** — 「red(준비) = **exit 78**」 이라는 **숫자**가 `SKILL.md §4` 문안에도 픽스처에도 없다(문안은 상태 **이름**만 준다). 다음 회차가 손댈 자리는 정규식이 아니라 그 숫자의 자리다.

**사후 정규식 수정 = 0건.** H14·H15·H16·H18 을 통과시키려면 정규식을 **넓혀야** 하는데 라운드 §3 ㉴ 가 금한다. H09 는 과제문 개정이라 재설계다. 다섯 건 전부 **advisor ② 판정 자리**로 남긴다. 정규식 오타로 인한 red 는 0건(§1 선검증).

**총 모델 호출 43** — 스모크 ① 1(0.7132 · 예산 소진) · 스모크 ② 2(1.7079) · 전수 40(32.4506) · **합 34.8717 USD** · 재실행 0.

## 4. 하지 않은 것

불안정·실패 5건 **무수정**(라운드 §3 ㉴) · 제품 파일 0(`git diff --stat 7a97259 -- frontend services contracts db gates` **0줄**) · 대장 `work-items.yaml` 0(읽기만) · `PLAN-SoT §9` 0(〈N〉 은 병합 직전 오케스트레이터 · `rules §4-1`) · 병합·push 0.

## 5. intent 대조 (`intent/2026-09-08-harness-evals.md ## 원한 결과`)

⑴ 4경로 변경 시 20건이 돌고 exit code 로 갈린다 = **충족(D6 몫)**(20건 실재 · exit 1 · 트리거 감지는 **D7 몫**으로 범위 밖) ⑵ 「사고 1건 = eval 1건」 = **충족**(§5-b 3줄 → H01·H02·H03) ⑶ 수용 근거가 개정 전 red → 개정 후 green = **부분**(장치는 섰으나 red 5건이 열려 기준선 미성립) ⑷ 20건이 `expect.sh` 하나로 판정 · 2회 2/2 green = **판정 충족 20/20 · 성적 미달 15/20**.

**미달 2** — ⑴ 2/2 green **15/20**(막는 것 = `exit 78` 상수 부재 3 · 낱말 요구 1 · 판정 낱말 정의 1) ⑵ 승격 **3회 연속** 조건에서 이 회차가 red 라 **연속 계수 0**(다음도 1회째).
**초과 3**(근거 병기) — ⑴ `results/.gitignore` 신설 ＋ README 「결과」 절 추적 부분집합 확정(지시 ⑸ 집행 · 추적 = `summary.md`·`out`·`expect` / 제외 = `raw`·`err`) ⑵ README 실행 예시 값 `180/0.50` → `93/2.01` 갱신 ＋ 초안 예산 경고(그대로 두면 복사한 사람이 20건 전부 red(준비)) ⑶ README 「결과」 에 `H??.expect.{1,2}.txt` 추가 기재(`run.sh:190` 이 쓰는데 D5 목록에 빠져 있었다).

## 6. 셀 수 없었던 것

- **모델 판본을 회차에 못 박는 자리 부재** — 러너가 모델을 지정하지 않아 환경 기본값을 타고, `modelUsage` 는 `raw.json` 에만 남는다(추적 제외분). 판본이 바뀌면 성적이 바뀌는데 그것을 회차에 기록하는 칸이 `summary.md` 에 없다.
- **비용의 과제 몫** — 1실행 0.81 USD 중 컨텍스트 적재분과 과제 수행분을 가르지 못했다.
- **불안정의 원인** — H09 가 과제문 모호성인지 모델 변동인지 2회 표본으로는 못 가른다(표본 2는 intent Q8 이 정한 값).
- **`.verified--pending` 대비 미달 4.23:1 을 잡는 검사의 부재**(H19 픽스처 실측) — `design-fix-20260908.test.ts`·`css-residual-rc11.test.ts` 는 이 선택자를 단언하지 않고, `css_audit.py` 대비 계산은 `color`/`background` 가 **리터럴 hex** 일 때만 돈다(`:117-122`). 두 선언은 `var()` 참조라 빠진다 → **게이트·Dockerfile·배포 어디에도 걸리지 않는다.** 「기존 값」이 아니라 **검사 공백**이므로 후속 항목(`rules §3-3`).
