# R-D-2 · 하네스 eval — WU-D5 · WU-D6 · WU-D7 ＋ 라운드 종료 검증 — spec: `dev-package/prd/specs/R-D.md` (출처 intent `dev-package/intent/2026-09-08-harness-evals.md` 축 ② · 우산 `dev-package/intent/2026-09-08-r-d.md`)

> ⛔ **착수 조건 = Ted 가 intent 2건을 커밋(승인) ＋ `R-D-1-branching.md` 4건 done(D5 만 D1 과 병렬 허용).**
> 라운드 = **R-D** · 계층 = **평가 하네스·게이트·CI 필터** · WU **3건**(순서 고정 D5 → D6 → D7).
> 통합 브랜치 `integration/r-d` · 워크트리는 `Agent(isolation:"worktree")` · 제품 코드 **0** · 계약 **0** · 마이그레이션 **0** · 외부 서비스 호출 = `claude -p` 뿐(로컬).
> spec 이 정본 · 이 파일은 실행 뷰(`prd/specs/README.md`).

---

## 0. 읽기 규칙 — 이 파일이 유일한 부트스트랩

> ⛔ `03-HANDOFF.md` · `PLAN-SoT.md` · `work-items.yaml` · `WORK-UNITS.md` 를 통째로 열지 않는다.

- 허용된 접근 세 줄 — `bash dev-package/prd/tools/max-decision.sh` · `grep -n -A14 '^  - id: WU-D5' dev-package/work-items.yaml` · `grep -n -A20 '^ALL_GATES=(' gates/run.sh`.
- 요구사항 정본 = spec `R-D.md` ＋ intent `2026-09-08-harness-evals.md`(**로스터 20건 표가 과제 정의의 정본** · 여기서 재작성하지 않는다) ＋ 이 파일.
- `path:line` 은 트리 `52c10af` 실측. 픽스처 원천(옛값)은 `git show <sha>:<path>` 로 복원한다 — 제품 파일을 고치지 않는다.
- 사실 확인은 `researcher` 에, 판정은 이 세션에. `claude -p` 호출은 레인이 러너를 통해서만 한다(대화 세션에서 과제를 손으로 돌려 「됐다」고 하지 않는다).

### 세션 시작
```bash
cd "<작업공간>/30 CoLAB-v2" && claude --add-dir "../40 COLAB-기획"
git fetch origin main && git log --oneline -8 origin/main
claude --version                      # 2.1.263 실측 · --max-turns 부재 · --max-budget-usd 존재
bash dev-package/prd/tools/max-decision.sh
```
- 역할 — `advisor`(① fan-out 전 · ② 산출 수용 · ③ 병합 전) · `lane-worker`(opus · worktree · TDD·intent 대조 자동) · `researcher` · `gate-runner`(haiku · `COLAB_GATE_OUTDIR` 필수).

---

## 1. 확정 결정 — 다시 열지 않는다

Ted 「전부권고대로」(2026-09-08 · 하네스 eval Q1~Q8) — intent 설계 트리 Q1~Q12 축자:
- 위치 `eval/harness/` · 트리거 = `CLAUDE.md`·`.claude/skills/**`·`.claude/hooks/**`·`.claude/agents/**` diff 일 때만 · 처음엔 게이트 밖(승격은 Q10).
- 배분 **(가) 3 · (나) 10 · (다) 5 · (라) 2** = 로스터 H01~H20(intent 표).
- 형식 `eval/harness/<번호-이름>/{task.md, fixture/, expect.sh}` · exit 0 = green · 출력 대조는 정규식 고정.
- 상한 = `timeout 180s` ＋ `--max-budget-usd 0.50` **초안** → 첫 실측(20건×1회) p95 ×2 로 확정 · 초과 = **red(준비)** · skip 금지.
- 비결정 = 과제당 **2회 · 2/2 green** 통과 · 1/2 = red(판정 · 「불안정 — 과제 설계 결함」).
- 실행처 = **로컬 러너 먼저** · CI 는 승격 때(시크릿 0건 · 필터 부재 실측).
- 승격 = **3회 연속 2/2 green** 뒤 `gates/run.sh` `harness-eval` — 로컬 `all` 은 명시 면제·건수 노출 · CI paths-filter 잡에서만 실행.
- 권한 = `--allowedTools Read,Grep,Glob,Bash(read-only 목록)` · `--no-session-persistence` · `--add-dir` 픽스처만. 과제는 **판정**을 재지 수정 능력을 재지 않는다.
- 라운드 = R-D 합류.
- spec 우려 항목 권고(advisor ② 자리) — 상한 실측 뒤 갱신 ⓐ · 불안정 = red ⓐ · read-only 목록 한 자리 ⓐ.

---

## 2. 범위 — 이 파일의 WU 3건

### WU-D5 · 러너 `eval/harness/run.sh` ＋ 과제 형식 ＋ README 행 — 계층 평가 하네스 · 크기 M · 레인 `rd-eval-runner`

- **의존**: 없음(D1 과 병렬 가능 — ⭑ advisor ① 조건: 파일 겹침은 0 이 아니라 **대장 `work-items.yaml`·`dev-package/sessions/` 1건**이므로 그 둘의 갱신은 **오케스트레이터 단독** · 레인은 무접촉). 기본은 R-D-1 뒤.
- **현재 코드** — `eval/README.md` 하네스 표 3행(`k4-search/`·`s2b-alayer/`·`s2b-alayer-g2/`) · `eval/` 에 `claude`/LLM 호출 0 · `eval/s2b-alayer/run.py:126` `subprocess.run(..., timeout=180)` 상한 선례 · `gates/tools/frontend-visual.sh` 세 상태 선례(`COLAB_VISUAL_URLS` / `COLAB_VISUAL_EXEMPT=1` / 둘 다 없으면 78) · `claude` 2.1.263 flags: `-p`·`--output-format`·`--allowedTools`·`--no-session-persistence`·`--add-dir`·`--max-budget-usd`(`--max-turns` 없음).
- **할 일** — ⑴ `eval/harness/run.sh`: 과제 전수 `eval/harness/H??-*/` · 과제마다 `task.md`·`fixture/`·`expect.sh` 존재 검사(부재 → red(준비 78) · 과제 0건 → red 1) · 실행 `timeout "$COLAB_EVAL_TIMEOUT" claude -p --output-format json --allowedTools "$ALLOWED" --no-session-persistence --add-dir "<fixture 절대경로>" --max-budget-usd "$COLAB_EVAL_BUDGET" < task.md > out.N.txt` · `expect.sh < out.N.txt` · **2회** · 판정 = 2/2 green · 1/2 「불안정」 red(1) · timeout(124)/예산 초과 → red(준비 78) · 요약줄 `과제 N · 실행 2N · green N · 불안정 N · 준비 N · 초 p50/p95 · USD 합` · exit 0/1/78 · `COLAB_EVAL_TIMEOUT`·`COLAB_EVAL_BUDGET` **미선언 → 78**(관대한 기본값 금지) · `COLAB_EVAL_ONLY=H01` 로 단건 · 결과 `eval/harness/results/<YYYYMMDD-HHMM>/{summary.md, H??.out.{1,2}.txt}` ⭑ ⟨정정 2026-09-08 · advisor ② WU-D5⟩ 종전 ~~`text`~~ — 요약줄 `USD 합` 이 `text` 출력으로는 측정 불가 · 러너는 `result` 본문만 `expect.sh` stdin 으로 넘겨 대조 조건 유지 · `is_error`/`subtype≠success` 는 red(준비). ⑵ `ALLOWED` 정본 = `eval/harness/README.md` 한 표(`Read,Grep,Glob,Bash(git log:*),Bash(git show:*),Bash(git diff:*),Bash(sed -n:*),Bash(grep:*),Bash(ls:*),Bash(cat:*),Bash(wc:*),Bash(python3 <fixture 사본>/css_audit.py --root <fixture 사본>:*)`(⭑ advisor ① — 계측기와 인자 경로를 **fixture 안 사본으로 고정** · 자유 경로 인자는 읽기 전용을 깨뜨린다)`` — 실제 `--allowedTools` 문법은 레인이 `claude -p --help` 로 실측해 맞춘다 · `[미상]` 이면 멈추고 보고) ⑶ 과제 템플릿 `eval/harness/_template/` ⑷ `eval/README.md` 하네스 표에 `harness/` 한 행(「지침·스킬·훅·에이전트가 바뀔 때만 · 20건 · 2/2」) — 기존 3행·경고문 무삭제 ⑸ `eval/harness/README.md`: 형식 · 상한(초안 · `[미측정]` 표시) · 세 상태 · 「사고 1건 = eval 1건」 규칙(§5-b 링크).
- **수용 기준** — 러너 시험 `eval/harness/tests/run-selftest.sh`(claude 를 가짜 `PATH` 스텁으로 대체 · 실제 모델 호출 0): Given 과제 0건 → exit 1 · Given `expect.sh` 부재 → 78 · Given 상한 변수 미선언 → 78 · Given 스텁이 1회차 green·2회차 red → 「불안정」 exit 1 · Given 2/2 → exit 0 ＋ 요약줄 5칸 · Given 스텁 `sleep` > `COLAB_EVAL_TIMEOUT` → 78. 실제 `claude -p` 1회 스모크(H01 만 · 결과 파일 존재)는 D6 에서.
- **시험 seam** — `gates/tools/frontend-visual-selftest.sh` 형식(임시 dir · 스텁 · exit 코드 단언).
- **좁은 게이트** — `exec-bit` · `work-item-consistency` · `planning-freshness` · 신설 `eval/harness/tests/run-selftest.sh` 6/6.

### WU-D6 · 과제 20건 ＋ 첫 실측(p95·예산) — 계층 평가 하네스 · 크기 L · 레인 `rd-eval-tasks`

- **의존**: WU-D5.
- **현재 코드(픽스처 원천 · intent 로스터 축자)** — (가) `CLAUDE.md:122-124` 3줄 · (나) `dev-package/sessions/p3-design-audit-20260905.md:9-19` 판정표 ＋ `frontend/test/design-fix-20260908.test.ts:74-155` ＋ `frontend/test/css-residual-rc11.test.ts:79-111` · (다) `.claude/skills/colab-v2-work/SKILL.md:65-69` 다섯 모양 · (라) `catalog.css:140`·`project.css:528` `.verified--pending` · `CLAUDE.md:131,137` §6-1.
- **할 일** — ⑴ H01~H20 디렉터리화(로스터 표 순서·이름 그대로 · `task.md` = 과제 한 줄을 지시문으로 · `fixture/` = 옛값 사본(`git show <sha>:<path>` · (나)는 결함이 **심긴** 상태 · (다)는 다섯 모양을 각각 한 셸 파일로 · H19 는 두 파일 · H20 은 HANDOFF·대장 사본 둘) · `expect.sh` = 정규식 고정(green 조건 ＋ **red 조건 음성 단언**: H01 HANDOFF 축자 재진술 → red · H13 수정 명령 등장 → red)) ⑵ 첫 실측 = `COLAB_EVAL_TIMEOUT=180 COLAB_EVAL_BUDGET=0.50 eval/harness/run.sh` 1회(20건×2회) → `results/…/summary.md` 에 과제별 초·USD 표 20행 ＋ p50/p95/합 → 상한 = **p95×2**(초) · 예산 = 과제별 최대×2 를 `eval/harness/README.md` 의 `[미측정]` 자리에 기입 ⑶ 불안정(1/2)·준비(78) 과제는 **고치지 말고** 표에 남기고 보고(advisor ② 자리 · 기대 정규식 좁히기는 판정 뒤) ⑷ 3회 연속 기록 시작(`results/` 에 회차 누적 · D7 승격 조건).
- **수용 기준** — Given `eval/harness/H??-*/` 20개, Then 각각 세 파일 존재 · `expect.sh` 실행 비트 · Given 첫 실측, Then 표 20행 공란 0 · p95 값 · README `[미측정]` 0건 · Given 2/2 green 과제 수 N, Then 요약줄과 표 일치 · Given 불안정·준비 과제, Then 이름과 사유가 표에.
- **시험 seam** — 러너 자체(D5) ＋ `results/` 실측 표. 픽스처 복원 명령을 각 `fixture/SOURCE.md` 에 축자(재현 가능).
- **좁은 게이트** — `exec-bit` · `work-item-consistency` · `planning-freshness`. ⛔ `frontend-*`·`service-tests-*` 는 무관(제품 파일 무접촉을 `git diff --stat` 로 증명).

### WU-D7 · 승격 준비 — `harness-eval` 게이트 세 상태 스텁 ＋ selftest ＋ CI 필터 — 계층 게이트·CI · 크기 S · 레인 `rd-eval-gate`

- **의존**: WU-D6(과제 20건 실재).
- **현재 코드** — `gates/run.sh:153-172` `ALL_GATES`(`frontend-visual`·`frontend-visual-selftest` 최근 등재 선례) · dispatch `:174~`(`frontend-visual)` `:242`) · `.github/workflows/ci.yml:19-70` `changes` 잡 · filters 9출력 — `CLAUDE.md`·`.claude/**` 를 덮는 것 0 · `secrets.` 참조 0 · `gates/README.md` 표.
- **할 일** — ⑴ `gates/tools/harness-eval.sh`: `COLAB_HARNESS_EVAL=1` → `eval/harness/run.sh` 실행·exit 전달 · `COLAB_HARNESS_EVAL_EXEMPT=1` → `harness-eval green — 면제 선언 · 과제 N건(미실행)` (N 은 디렉터리 실계수 · 0 이면 red) · 둘 다 없음 → red(준비 78 · 「선언 없음」) ⑵ `harness-eval-selftest.sh` 3케이스: ⓐ 과제 0건 red ⓑ 면제 시 건수 노출 green ⓒ 상한 초과 픽스처 → 78 ⑶ `ALL_GATES` 두 이름 · dispatch · `gates/README.md` 표 2행 ⑷ `ci.yml` filters 에 `harness:` (`CLAUDE.md`·`.claude/skills/**`·`.claude/hooks/**`·`.claude/agents/**`) ＋ `changes` outputs · 잡 `harness-eval`(`if: needs.changes.outputs.harness == 'true'` · `env: ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}` · 스텝이 키 부재를 감지하면 `exit 78` — **skip 금지**) · 실제 실행은 Q10 조건(3회 연속) 충족 뒤 `COLAB_HARNESS_EVAL=1` 을 잡에 넣는 별건 ⑸ `gates/config/parallelism.toml` 에 `harness-eval = serial`.
- **수용 기준** — Given 로컬 `all -j 1` 에 `COLAB_HARNESS_EVAL_EXEMPT=1`, Then 요약에 `면제 · 과제 20건` 노출 ＋ green · Given 둘 다 미선언, Then 78 · selftest 3/3 · Given `CLAUDE.md` 한 줄 diff 픽스처, Then paths-filter 출력 `harness=true`(`dorny/paths-filter` 는 로컬 실행 불가 → `act` 없으면 필터 문법 검증은 `yq`/`python -c yaml` 로 파싱 ＋ 패턴 대조 스크립트로 대체 · `[미상]` 이면 명시).
- **시험 seam** — `gates/tools/frontend-visual-selftest.sh` 4케이스 형식 · `gates/README.md:37` selftest 집합 규칙.
- **좁은 게이트** — `harness-eval-selftest` · `exec-bit` · `work-item-consistency` · `planning-freshness`.

---

## 3. 지켜야 하는 규약 — 명령으로

### advisor ① 반영 (2026-09-08)
- 판정 = 조건부 승인 · 이 파일 해당 조건 2 = D5 ‖ D1 병행 시 대장·sessions 는 오케스트레이터 단독 · `--allowedTools` 계측기 경로 fixture 고정. `harness-eval` 세 상태 설계는 CLAUDE.md §4 정합(깨끗 · 선례 `frontend-visual`). 정본 = `specs/R-D.md` 「advisor ① 반영」.

### ㉮ 워크트리 레인
- 레인 = `rd-eval-runner`(D5) · `rd-eval-tasks`(D6) · `rd-eval-gate`(D7) — `Agent(isolation:"worktree")` · rebase＋ff · 얹은 즉시 삭제. 직렬 3(D5 는 D1 과만 병렬 가능).

### ㉯ 대장 — `WU-D5`~`WU-D7` 등재 완료(`status: open`). 상태 갱신만.

### ㉰ 계약 — 해당 없음. `contracts/`·`frontend/`·`services/`(doctor 제외 · 그것도 R-D-1) 무접촉을 `git diff --stat main..integration/r-d` 로 증명.

### ㉱ 결정 번호 〈N〉 — 병합 직전 실측(참고 378). 예상 2행(문안 초안):
- 〈N〉 **브랜치 전략 정본화** — `docs/BRANCHING.md` 규칙 6 · `ship.sh` 조상 게이트(exit 65/78 · 우회 선언) · `MAIN_SHA` · doctor ⑮ · 원장 브랜치 필드 · 태그 `dev-YYYYMMDD-N` · 브랜치 정리 표(삭제 n · 보존 태그 n · Ted 한 줄 <일자>) · 근거 = R-C 창 9 사고(〈378〉 ⑧) · intent:`2026-09-08-r-d.md` · spec:`R-D.md`.
- 〈N+1〉 **하네스 eval 신설** — `eval/harness/` 20건(3·10·5·2) · 2회 2/2 · 상한 실측 p95=<초>·×2 · 예산 <USD> · 게이트 `harness-eval` 세 상태(면제 노출) · CI 필터 `harness`(시크릿 미배선) · 「사고 1건 = eval 1건」 · intent:`2026-09-08-harness-evals.md` · spec:`R-D.md`.

### ㉲ 게이트
```bash
COLAB_GATE_REPORT_DIR=dev-package/reports/R-D/<레인> ./gates/run.sh <좁은 게이트>
COLAB_HARNESS_EVAL_EXEMPT=1 COLAB_GATE_REPORT_DIR=dev-package/reports/R-D/all ./gates/run.sh all -j 1   # 라운드 끝 1회 · 면제·건수 노출
```
- ⛔ 대상 0건 red · 관대한 기본값 금지 · 상한 초과 = 78 · 실제 모델 호출은 D6 첫 실측과 D7 ⓐ 케이스 밖에서 하지 않는다.

### ㉳ 커밋 문면
```
하네스 R-D-2 <WU 제목> (WU-D_)

- <바뀐 자리 1~3줄>
- 제품 코드 0 · 계약 0 · 모델 호출 <n>회(실측 표 링크)
- RED 선실측 → GREEN: <시험>:<건수>
```

### ㉴ 금지
- ⛔ 과제 픽스처를 제품 파일 제자리에서 만들기(사본만) · ⛔ 불안정 과제를 기대를 넓혀 green 으로 만들기(판정 뒤에만) · ⛔ CI 시크릿 값 기입 · ⛔ `--dangerously-skip-permissions` 를 러너에 박기(권한은 `--allowedTools` 로만).
- ⛔ 기존 `eval/` 3벌·README 경고문 삭제.

---

## 4. 산출물과 근거

| 무엇 | 어디 |
|---|---|
| 러너 | `eval/harness/run.sh` · `_template/` · `tests/run-selftest.sh` · `README.md`(형식·상한·세 상태·allowed 표) |
| 과제 | `eval/harness/H01-…`~`H20-…`(각 `task.md`·`fixture/`·`fixture/SOURCE.md`·`expect.sh`) |
| 실측 | `eval/harness/results/<회차>/summary.md`(20행 · p50/p95 · USD) · 3회 누적 |
| 게이트 | `gates/tools/harness-eval.sh` ＋ `-selftest.sh` · `gates/run.sh` 2이름 · `gates/README.md` 2행 · `parallelism.toml` |
| CI | `.github/workflows/ci.yml` filters `harness` ＋ 잡 `harness-eval`(시크릿 참조만) |
| 세션 노트 | `dev-package/sessions/rd-eval-{runner,tasks,gate}-<YYYYMMDD>.md` · 라운드 `dev-package/sessions/R-D-ROUND-<YYYYMMDD>.md` |
| 대장 | `work-items.yaml` 3 블록 `done` ＋ `evidence` |

**HANDOFF 갱신문(오케스트레이터 · 5줄 이하)**
```
R-D 완료 — WU-D1~D7, 통합 integration/r-d <sha> → Ted ff · 등재 〈N〉〈N+1〉
하네스 eval 20건 실측 p95 <초>·예산 <USD> · 2/2 green <n>/20 · 불안정 <n> · 준비 <n> · 게이트 harness-eval 세 상태(면제 노출) · CI 필터 harness(시크릿 미배선 · Ted)
브랜치 11 → <n> · archive 태그 <n> · ship.sh 조상 게이트 · doctor 15항목
게이트: all -j 1 green <n>/0/0(harness-eval 면제 선언)
다음 = 배포 창(ship.sh 게이트 첫 실전 · 태그 dev-<날짜>-1) → 재검사(design-review · staging 실화면) → R-E
```

---

## 5. 완료 판정 (라운드 종료 검증)

- **WU-D5** — selftest 6/6 · 상한 미선언 78 · 과제 0건 red · 불안정 red · README allowed 표.
- **WU-D6** — 20 디렉터리 · 실측 표 20행 · README `[미측정]` 0 · 불안정·준비 과제 보고(무수정).
- **WU-D7** — selftest 3/3 · `all -j 1` 면제 시 건수 노출 · 필터 `harness` 파싱 대조 · 시크릿 부재 78.
- **라운드** — `git diff --stat main..integration/r-d` 에 `frontend/`·`contracts/`·`db/` 0 · `services/` 는 doctor 1파일＋시험 · advisor ② 7건 · advisor ③ 병합 전 · 〈N〉 2행 실측 · 레인 브랜치 0 잔존(규칙 4 첫 집행) · `plan/r-d-0908` 은 Ted ff 뒤 삭제.
- **인계** — 시크릿 발급·CI 잡 실제 실행(3회 연속 뒤) · 배포 창에서 `ship.sh` 게이트·`tag-release.sh` 첫 실전 · 재검사(design-review audit) → R-E.
