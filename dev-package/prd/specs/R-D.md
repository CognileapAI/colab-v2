# Spec: R-D — 브랜치 전략(축 ①) ＋ 하네스 eval 20건(축 ②) · 7 WU (제품 코드 0 · 계약 0 · 스키마 0 · 마이그레이션 0)
출처 intent: `dev-package/intent/2026-09-08-r-d.md`(우산) · `dev-package/intent/2026-09-08-harness-evals.md`(축 ② · 로스터 20) — **미승인 초안 · 커밋이 승인** · grill-me 2026-09-08 완료(프론티어 공집합 · Ted 「좋아 intent에 얹어」·「모전부 권고대로 계획」·「전부권고대로」)

> ⛔ 이 spec 은 intent 두 벌을 재인터뷰 없이 합성한 것이다. 판정 밖의 값은 「레인 실측 위임」 또는 `[미측정]` 으로 적었다. `path:line` 은 트리 `52c10af`(= `origin/main` `a31111f` ＋ intent 커밋) 실측.

## 문제 진술
- 배포 도구가 브랜치를 보지 않는다 — `infra/dev/ship.sh:14` 은 `dist/colab-v2-dev.sha` 만 읽고 `:20-26` 에서 scp·`docker load`·`CURRENT_SHA` 기록까지 간다. `origin/main` 조상 검사 0. 창 9 가 `main` 밖 sha 를 dev 에 실었고(〈378〉 ⑧) 그 흔적(`integration/w9-dev-deploy`·`w9-rebase`·`origin/integration/w9-dev-deploy-rebased`)이 살아 있다.
- 브랜치 수명 규칙이 문서에 없다 — `grep -rn "브랜치 전략\|branching" CLAUDE.md docs/` 0건. 실측 잔존 브랜치 = 로컬 5(`integration/r-a2`·`r-b`·`w9-dev-deploy`·`plan/r-d-0908`·`w9-rebase`) ＋ 원격 10(`feature/rtf400_{deploy_prod,dev_scale_up,upload_reaper}`·`gh-pages`·`integration/{r-a2,r-b,w9-dev-deploy,w9-dev-deploy-rebased}`·`plan/r-d-0908`·`urgent-upload-lineage-rev1`) = **고유 이름 11**(intent 의 「18개」는 `lane/wu-c*`·`integration/r-c` 가 이미 삭제된 뒤의 낡은 수).
- `deploy_doctor` 14항목(`services/core-api/ops/deploy_doctor.py:62` `MARKS` 14자 · `:696-700` 호출 순서)에 「실행 sha ∈ main」 이 없다. EC2 에 git 이 없어 파일 대조만 가능.
- 하네스(지침·스킬·훅·에이전트)를 고쳐도 행동이 바뀌었는지 재는 자리가 0. `CLAUDE.md:118-126` §5-b 재발 사고 3건이 산문으로만 남았다. `eval/README.md` 는 D10 품질 3벌뿐이고 `claude`/LLM 호출 0.

## 해법 개요
- **책(main)에 없는 층은 배포하지 않는다** — 반입 스크립트가 후보 sha 의 `origin/main` 조상 여부를 로컬에서 재고 아니면 거절한다. 같은 반입에 `MAIN_SHA` 를 실어 EC2 점검기가 사후 대조한다. 규칙 6개를 `docs/BRANCHING.md` 로 세우고 `CLAUDE.md §10` 이 요지·링크를 가진다.
- **살아 있는 브랜치를 없앤다** — 창 9 계열은 잔여 2커밋 실측 보고 → Ted 한 줄 → 삭제. 나머지는 `main` 조상 확인분 즉시 삭제.
- **하네스를 실과제로 잰다** — `eval/harness/` 러너 ＋ 과제 20건(`expect.sh` 기계 판정 · 2회 2/2). 첫 실측으로 상한을 정하고, 3회 연속 green 뒤 게이트 세 상태로 승격한다. 사용자 관점 동일 행위(게이트 실행·원장 기록)는 기존 `gates/run.sh`·원장 함수 재사용.

## 사용자 스토리
1. 운영하는 사람으로서 `main` 에 없는 sha 는 반입 단계에서 거절되기를 원한다, 창 9 처럼 「책에 없는 층」이 dev 에 남지 않기 위해.
2. 운영하는 사람으로서 배포 점검기가 「실행 중 sha 가 main 에 있는가」를 15번째로 재기를 원한다, 반입 게이트를 우회한 경우를 사후에 잡기 위해.
3. 운영하는 사람으로서 staging 원장 행에 브랜치 이름이 남기를 원한다, 리허설이 어느 통합 브랜치였는지 되짚기 위해.
4. 운영하는 사람으로서 dev 실적용마다 `dev-YYYYMMDD-N` 태그가 찍히기를 원한다, 원장 없는 dev 의 「안전 복구 세대」가 이미지 잔존에만 의존하지 않기 위해.
5. 오케스트레이터로서 브랜치 수명(생성 기점·복귀 방식·삭제 시점)이 문서 한 장에 있기를 원한다, 라운드마다 관행을 다시 설명하지 않기 위해.
6. 오케스트레이터로서 창 9 계열 브랜치의 잔여 2커밋이 무엇인지 실측 보고를 받고 싶다, 흡수/폐기를 근거로 정하기 위해.
7. 하네스를 고치는 사람으로서 지침을 바꾼 뒤 `eval/harness/run.sh` 한 번으로 20건이 돌고 exit code 로 갈리기를 원한다, 「읽어 보니 낫다」 대신 red→green 으로 수용하기 위해.
8. 하네스를 고치는 사람으로서 §5-b 에 줄이 늘 때 과제도 하나 늘기를 원한다, 같은 실수의 회귀를 기계가 잡기 위해.
9. 하네스를 고치는 사람으로서 과제가 비결정이면 「불안정」으로 red 가 나기를 원한다, 운으로 통과한 하네스 문안을 정본으로 받지 않기 위해.
10. 하네스를 고치는 사람으로서 `claude -p` 호출이 시간·예산 상한을 넘으면 skip 이 아니라 red(준비)가 나기를 원한다, 조용한 통과를 막기 위해.
11. 레인 워커로서 eval 과제가 읽기 전용 도구만 허용하기를 원한다, 과제가 재는 것이 「판정」이지 「수정 능력」이 아니기 위해.
12. 다음 세션으로서 게이트 `harness-eval` 이 로컬 `all` 에서는 명시 면제·건수 노출로, CI 에서는 paths-filter 잡에서만 돌기를 원한다, 모델 호출 비용이 매 커밋에 붙지 않기 위해.

## 구현 결정
- **WU 7건 · 순서 고정 D4 → D1 → D2 → D3 → D5 → D6 → D7**(D4 가 먼저여야 D2 의 조상 검사가 죽은 브랜치에 흔들리지 않고, D2 가 `MAIN_SHA` 를 실어야 D3 가 읽는다). D5 는 D1 과 파일 겹침 0 이라 병렬 가능(표시만 · 기본 직렬).
  - **WU-D4 브랜치 정리** — ⑴ 창 9 계열 3개(`w9-rebase` `80aeb00`·`integration/w9-dev-deploy` `20b3715`·`origin/integration/w9-dev-deploy-rebased`)의 `main` 밖 커밋 실측: `git log main..w9-rebase` = 3(`80aeb00` 개시 · `de1a5a2` 집행 원장 · `97f1d99` 재번호) · `main..integration/w9-dev-deploy` = 2. ai 체인분은 WU-C13 이 흡수했으므로 남은 것 = dev 트리거 스풀 · 매니페스트 원천 표기 · 원장 사본 · 재번호. 각 파일이 현 `main` 에 동등물이 있는지 `git diff main..80aeb00 --stat` 로 표 보고 → **Ted 한 줄**(흡수/폐기) → 삭제. ⑵ `feature/rtf400_*` 3·`urgent-upload-lineage-rev1`·`gh-pages` 는 조상 여부와 용도(`gh-pages` 는 사이트 배포 브랜치 가능성)를 실측해 같은 표에 넣는다 — 삭제는 Ted 한 줄 뒤. ⑶ `integration/r-a2`·`r-b`(main 조상 · 병합 완료)는 즉시 삭제(로컬＋원격). ⑷ 삭제 전 `git tag archive/<브랜치>` 로 보존(우려 6 권고 ⓐ). 산출 = `dev-package/sessions/WU-D4-branches-<날짜>.md` 표.
  - **WU-D1 문서** — `docs/BRANCHING.md` 신설(규칙 6 ＋ 브랜치 수명 표 `main`/`integration/r-N`/`lane/wu-*`/`plan/*`/태그 ＋ 「하지 말 것」 = git-flow 계층 · 미병합 sha 배포 · 병합 뒤 브랜치 존치). `CLAUDE.md` **§10** 신설(현 마지막 절 `§9` `CLAUDE.md:161` · 파일 169행) — 요지 6줄 ＋ 링크. 원문 무삭제.
  - **WU-D2 반입 게이트 ＋ 원장 필드 ＋ MAIN_SHA** — `infra/dev/ship.sh:14`(`SHA=` 읽기) 직후·`:20` 첫 ssh 전에: `git -C "$REPO" fetch -q origin main && git -C "$REPO" merge-base --is-ancestor "$SHA" origin/main || { echo "sha 가 origin/main 조상이 아니다: $SHA" >&2; exit 65; }` ＋ `MAIN_SHA="$(git -C "$REPO" rev-parse --short=12 origin/main)"` 를 `:25` 의 `CURRENT_SHA` 기록 줄과 같은 ssh 에서 `/opt/colab-v2/MAIN_SHA` 로 기록. 명시 우회 = `COLAB_SHIP_ALLOW_NONMAIN=1` 이면 **거절하지 않되 출력에 「비조상 반입 · 우회 선언」 한 줄** ＋ `MAIN_SHA` 에 `nonmain:<sha>` 기록(세 상태). `infra/staging/deploy.sh:266` `ledger_append deploy … green "…"` 비고 끝에 `브랜치=$(git -C "$REPO" branch --show-current)` 추가(`:71`·`:87` red 행도 동일). `rollback.sh` 는 무접촉(브랜치 무관). 태그: `infra/dev/` 에 `tag-release.sh` 신설 — doctor 전건 뒤 사람이 호출 · `dev-YYYYMMDD-N`(N = 같은 날 기존 태그 수＋1) · `prod-YYYYMMDD` 는 기존 규약 유지.
  - **WU-D3 doctor 15항목** — `deploy_doctor.py:62` `MARKS` 에 `⑮` 추가 · `check_main_ancestry(ctx, rep)` 신설 · `:700` `check_backups` 뒤 호출. 판정 = `/opt/colab-v2/CURRENT_SHA` 와 `/opt/colab-v2/MAIN_SHA` 를 읽어 ⑴ 둘 다 있고 `MAIN_SHA` 가 `nonmain:` 아님 ∧ `CURRENT_SHA` 가 `--repo` 트리의 `git`… — ⛔ EC2 에 git 없음 → 대조는 **문자열**: `MAIN_SHA` 파일에는 ship.sh 가 「`origin/main` sha ＋ 후보 sha 가 조상임을 로컬에서 확인했다」는 두 값(`main=<sha> candidate=<sha> ancestor=yes|no|bypass`)을 적고 doctor 는 `candidate == CURRENT_SHA ∧ ancestor == yes` 를 ✓ 로 · `bypass` 는 ✗ ＋ 사유 · 파일 부재는 **─(준비) 아닌 ✗**(우려 4 권고). 요약줄 `항목 15 — ✓ N · ✗ N · ─ N`.
  - **WU-D5 eval 러너** — `eval/harness/run.sh`: 과제 디렉터리 전수(`eval/harness/H??-*/`) · 각 과제 = `task.md`(지시) · `fixture/`(심은 조각) · `expect.sh`(exit 0 = green) · 실행 = `timeout "$COLAB_EVAL_TIMEOUT"` ＋ `claude -p --output-format text --allowedTools "Read,Grep,Glob,Bash(<read-only 목록>)" --no-session-persistence --add-dir <fixture> --max-budget-usd "$COLAB_EVAL_BUDGET" < task.md` → 출력을 `expect.sh` 에 stdin 으로 · 과제당 **2회** · 2/2 green 만 통과 · 1/2 = red(판정 · 「불안정」) · timeout/예산 초과 = red(준비 · exit 78) · 과제 0건 = red · `fixture/`·`expect.sh` 부재 = red(준비). 요약줄 `과제 N · 실행 2N · green N · 불안정 N · 준비 N`. `COLAB_EVAL_TIMEOUT`(초안 180)·`COLAB_EVAL_BUDGET`(초안 0.50)는 **미선언이면 red(준비)**(관대한 기본값 금지 · `${VAR:-}` 없음). `eval/README.md` 하네스 표에 `harness/` 한 행. read-only Bash 목록 = `git log`·`git show`·`git diff`·`sed -n`·`grep`·`ls`·`cat`·`wc`·`python3 <계측기>` — 과제 디렉터리 `README` 에 축자.
  - **WU-D6 과제 20건 ＋ 첫 실측** — 로스터 H01~H20(원본 intent 표 · 픽스처 원천 path:line 그대로) 각각 디렉터리화. 픽스처는 **사본**(`git show <sha>:<path>` 로 옛값 복원 · 제품 파일 무접촉). `expect.sh` 는 정규식 고정(예: H01 = 출력에 `git log` 와 최신 회차 문자열 · HANDOFF 축자 재진술이면 red · H13 = 실측 `3\.41` ＋ 수정 명령 부재). 첫 실측 = 20건×1회 → 소요·비용 표 → `p95×2` 를 상한으로 확정해 `eval/harness/README.md` 에 기록(`[미측정]` → 값). 3회 연속 2/2 기록은 D7 승격 조건.
  - **WU-D7 승격 준비** — `gates/run.sh` `ALL_GATES`(`:153-172`)에 `harness-eval` ＋ `harness-eval-selftest` 등재 · dispatch(`:174~`) 에 세 상태: `COLAB_HARNESS_EVAL=1` 선언이면 `eval/harness/run.sh` 실행 · `COLAB_HARNESS_EVAL_EXEMPT=1` 이면 「면제 · 과제 N건」 노출하고 green · 둘 다 없으면 **red(준비 · 78)**. selftest 3케이스 = ⓐ 과제 0건 red ⓑ 면제 시 건수 노출 ⓒ 상한 초과(픽스처 `sleep`)는 red(준비). CI = `.github/workflows/ci.yml:36` filters 에 `harness: ['CLAUDE.md','.claude/skills/**','.claude/hooks/**','.claude/agents/**']` 출력 신설 ＋ 잡 `harness-eval`(`if: needs.changes.outputs.harness == 'true'`) — **시크릿 미배선**(`secrets.ANTHROPIC_API_KEY` 참조만 · 발급은 Ted) · 시크릿 부재 시 잡이 red(준비)로 끝나야 한다(skip 금지). 실제 실행은 Q10 조건(3회 연속) 충족 뒤.
- 모듈 · 인터페이스: 셸 스크립트 3(`ship.sh` 게이트 · `tag-release.sh` · `eval/harness/run.sh`) · Python 1(`deploy_doctor.py` 항목 함수 1) · 문서 3(`BRANCHING.md`·`CLAUDE.md §10`·`eval/README.md` 행) · 게이트 2(`harness-eval`＋selftest) · CI 필터 1.
- 스키마 · 마이그레이션: **0** · Alembic 무접촉 · `migration-single-head` 회귀만.
- API 계약: **무접촉**(파괴/비파괴 해당 없음).
- 상태 값(코드 대신 결정만): `MAIN_SHA` 파일 형식 `main=<12> candidate=<12> ancestor=yes|no|bypass` · 러너 exit = 0 green · 1 red(판정) · 78 red(준비).

## 시험 결정
- 외부 행위 기준 검증 항목
  - D4 — 삭제 전 `archive/<브랜치>` 태그 존재 · 삭제 후 `git branch -a` 에서 대상 0건 · 보고 표에 브랜치별 「main 조상 yes/no · 밖 커밋 수 · Ted 판정」 열.
  - D1 — `docs/BRANCHING.md` 규칙 6 문면이 intent 축자 · `CLAUDE.md` `## 10.` 존재 ＋ §9 원문 무변(`git diff` 로 삭제 줄 0).
  - D2 — 픽스처 저장소에서 ⑴ 비조상 sha → `ship.sh` exit 65 · ssh 0회(스파이 `SSH=(echo)`) ⑵ 조상 sha → 통과 ＋ `MAIN_SHA` 내용 `ancestor=yes` ⑶ `origin` fetch 실패 → red(준비 · 진행 금지) ⑷ 우회 선언 → 통과 ＋ 출력에 「우회 선언」 ＋ `ancestor=bypass` · staging 원장 행에 `브랜치=` 필드(deploy.sh 드라이런 픽스처) · `tag-release.sh` 같은 날 2회 → `-1`·`-2`.
  - D3 — doctor 단위 시험(`services/core-api/tests/test_deploy_doctor*.py` 선례 grep) ⑴ 두 파일 일치·`yes` → ✓ ⑵ `bypass` → ✗ ⑶ 파일 부재 → ✗ ⑷ 요약줄 `항목 15` · `MARKS` 길이 15.
  - D5 — 과제 0건 → red · `expect.sh` 부재 → red(준비 78) · 상한 미선언 → red(준비) · 1/2 green → 「불안정」 red · 2/2 → green · 요약줄 건수 5칸.
  - D6 — 20건 각 2회 · 2/2 · 첫 실측 표(과제 · 초 · USD) 20행 · p95 계산이 표에서 재현.
  - D7 — selftest 3케이스 · `ALL_GATES` 포함 · 로컬 `all -j 1` 에서 면제 선언 시 「면제 · 과제 20건」 노출 · CI 필터 출력 `harness` 가 `CLAUDE.md` 한 줄 변경에 `true`.
- 재사용 seam: `gates/tools/*-selftest.sh`(exit 78 준비 실패 규약 · `migration-drift-selftest.sh` 최근 선례) · `infra/staging/deploy.sh` `ledger_append` · `eval/s2b-alayer/run.py:126` timeout 선례 · `frontend-visual.sh` 세 상태(`COLAB_VISUAL_EXEMPT`) 선례 · doctor 기존 `check_*` 함수 형태.
- 신설 seam: `eval/harness/run.sh`(러너 · exit 3값) · `MAIN_SHA` 파일 형식 · `harness-eval` 게이트 · CI 필터 `harness`.
- 해당 서비스 단독 게이트 이름: `exec-bit` · `work-item-consistency` · `planning-freshness` · `service-tests-core-api`(D3) · `harness-eval-selftest`(D7) · `migration-single-head`(회귀) · 전수 `all -j 1` 은 라운드 끝 1회.
- green-by-skip 방지: 대상 0건이 아님을 무엇으로 보이나 — D2 는 ssh 스파이 호출 횟수 0/1 단언 · D4 는 삭제 대상 목록 길이 단언(0 이면 red) · D5 는 과제 수를 요약줄에 내고 0 이면 red · D6 는 실측 표 20행 단언 · D7 은 면제 시에도 건수 노출 단언 · 상한 변수 미선언 → red(준비) 로 관대한 기본값 봉쇄.

## 정책 대조 (작성 시점 제약)
- CLAUDE.md §2 도메인 / §3 불변 규칙 중 저촉 항목: **없음** — 제품 코드·계약·스키마 무접촉. §4 게이트 세 상태(선언·명시 면제·무언 실패)를 D2·D5·D7 이 그대로 따른다. §5-b 「사고 1건 = eval 1건」 규칙은 D6 로스터 (가) 3건이 첫 집행.
- CLAUDE.md §5 저촉: **없음** — 부분 완료로 닫지 않는다 · 게이트 우회 0 · `main` push 는 Ted.
- 계약 동결 해제 필요: **아니오**(계약 0).
- 결정 번호: 〈N〉 병합 직전 재실측(현 최대 **378**). 예상 행 = 브랜치 전략 정본화 1 · 하네스 eval 신설 1.
### 디자인 제약 확인
대상 화면: **해당 없음(백엔드·인프라·문서 전용 — `frontend/` 무접촉)**
| 항목 | 충족/미충족/해당 없음 | 근거 |
|---|---|---|
| 토큰만 사용 | 해당 없음 | `frontend/` 변경 0 (`git diff --stat` 로 병합 전 재확인) |
| 글자 13px 이상 | 해당 없음 | 동일 |
| 대비 4.5:1 이상 | 해당 없음 | 동일 |
| 카드 그림자 0 | 해당 없음 | 동일 |
| 여백은 컨테이너 소유 | 해당 없음 | 동일 |
| 인터랙션 하한 | 해당 없음 | 동일 |
- 디자인 판정 25건은 값만 확정(intent) · 집행은 R-E.

## 우려 항목 (판정 필요)
> 프론티어는 공집합이다. 아래는 Ted 질문이 아니라 **레인 실측 위임 · advisor ② 판정 자리**다. 결과가 판정과 어긋나면 고치지 말고 보고한다.

| # | 항목 | ⓐ | ⓑ | 권고 |
|---|---|---|---|---|
| 1 | 모델 호출 상한을 실측 전에 어떻게 두나 — 첫 20건 실측이 상한 자체를 정한다 | 초안 180초·0.50달러로 돌리고 초과는 red(준비)로 기록만, 상한은 p95×2 로 갱신 | 실측 없이 초안값 고정 | **ⓐ** — 판정 축자. 초안값 초과가 나오면 그 과제는 「상한 미확정」으로 표에 남긴다 |
| 2 | 같은 과제를 두 번 돌려 한 번만 통과하면 「불안정」으로 실패 처리한다 — 모델 응답의 자연 변동이 과제 결함으로 읽힐 수 있다 | 판정 축자(1/2 = red)를 유지하고 불안정 과제는 기대 정규식을 좁히는 쪽으로 고친다 | 3회 중 2회 통과 허용 | **ⓐ** — 비결정을 허용하면 재는 것이 운이 된다 |
| 3 | 읽기 전용 셸 명령 허용 목록이 좁으면 과제가 판정을 못 내고, 넓으면 과제가 파일을 고쳐 「수정 능력」을 재게 된다 | 목록을 `git log/show/diff` · `sed -n` · `grep` · `ls` · `cat` · `wc` · 계측기 `python3` 로 고정하고 과제 README 에 축자 | 과제별로 다르게 | **ⓐ** — 한 자리 정본 |
| 4 | 배포 점검기 15번째 항목에서 대조 파일이 아예 없을 때 — 「준비 실패(─)」로 낼지 「실패(✗)」로 낼지 | ✗ — 파일 부재는 반입 게이트를 거치지 않았다는 뜻이라 판정 실패다 | ─ 준비 실패 | **ⓐ** — ─ 로 두면 옛 반입 방식이 영원히 통과한다 |
| 5 | 창 9 계열 브랜치의 잔여 커밋(트리거 스풀·매니페스트 원천 표기·원장 사본)을 흡수할지 폐기할지 | 실측 표(파일별 현 main 동등물 유무) 뒤 Ted 한 줄 | 실측 없이 폐기 | **ⓐ** — 판정 축자(Q4a) · 삭제는 그 뒤 |
| 6 | 브랜치 삭제는 되돌리기 어렵다 — 삭제 전에 무엇을 남기나 | 삭제 전 `archive/<브랜치>` 태그로 보존(원격까지) · 태그는 배포 대상 아님 | 태그 없이 삭제 · reflog 에 맡김 | **ⓐ** — reflog 는 원격에 없다 |
| 7 | 반입 게이트를 우회해야 하는 날(긴급 핫픽스)이 있을 때 | 명시 변수로 우회하되 출력·`MAIN_SHA`·점검기에 「우회」가 남아 ✗ 로 보인다 | 우회 불가 | **ⓐ** — 세 상태 규칙 · 조용한 우회만 막는다 |
| 8 | 원격에만 있는 오래된 브랜치 5개(`feature/rtf400_*` 3 · `urgent-upload-lineage-rev1` · `gh-pages`)를 이번에 함께 정리하나 | 같은 실측 표에 넣고 Ted 한 줄 뒤 처리 · `gh-pages` 는 용도 확인 전 무접촉 | 이번 범위 밖 | **ⓐ** — 표 한 장에 다 보이는 것이 규칙 3·4 의 취지 |

## 범위 밖
- git-flow 식 `develop`·`release/*` 계층 · prod 배포 재개(⏸ 유지) · 마이그레이션 되돌림 정책 · staging 원장 형식 전면 개정.
- 디자인 fix 16 WU · R-C 후속 9건(intent 「이월 → R-E」) · 계약 22차.
- CI 시크릿 발급(Ted) · 승격 실행 자체(Q10 조건 충족 뒤 별건).
- 기존 `eval/k4-search/`·`s2b-alayer*/` 개정 · 모델·프롬프트 튜닝.
- 제품 코드·`frontend/`·`contracts/`·`db/` 무접촉.

## 산출 계획
- 라운드 파일: **2개** — `dev-package/prd/rounds/R-D-1-branching.md`(D4 · D1 · D2 · D3) · `R-D-2-harness-eval.md`(D5 · D6 · D7). 각 ≤300행 · 첫 줄에서 이 spec 링크.
- 예상 레인 수: **7 직렬**(D5 ‖ D1 병렬 가능 표시 · 기본 직렬). 레인 = `lane-worker` `Agent(isolation:"worktree")` · advisor ①(fan-out 전) ②(산출 수용) ③(병합 전).
- 통합 브랜치 `integration/r-d` · 기점 `main` tip(해시 박지 않음) · 워크트리는 `Agent(isolation)` 가 만든다(손으로 형제 워크트리 금지).
- 대장 = `WU-D1`~`WU-D7` `status: open` · `depends_on` 위 순서 · 결정 〈N〉 병합 직전 재실측(현 최대 378).
- 착수 조건 = Ted 가 intent 2건 커밋(승인). 그 전 레인 0.
