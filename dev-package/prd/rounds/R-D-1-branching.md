# R-D-1 · 브랜치 전략 — WU-D4 · WU-D1 · WU-D2 · WU-D3 — spec: `dev-package/prd/specs/R-D.md` (출처 intent `dev-package/intent/2026-09-08-r-d.md` 우산 · `dev-package/intent/2026-09-08-harness-evals.md` 축 ②)

> ⛔ **착수 조건 = Ted 가 intent 2건을 커밋(승인). 그 전에는 이 파일로 세션을 열지 않는다.**
> 이 파일 하나로 세션을 시작한다. 라운드 = **R-D** · 계층 = **인프라·문서·점검기** · WU **4건**(순서 고정 D4 → D1 → D2 → D3).
> 통합 브랜치 `integration/r-d` · 기점 = `main` tip(**해시를 박지 않는다** · `git rev-parse HEAD` 로 읽는다) · 워크트리는 `Agent(isolation:"worktree")` 가 만든다(손으로 형제 워크트리 금지 · `colab-v2-work §1-b`).
> 계약 **0** · 스키마 **0** · 마이그레이션 **0** · 제품 코드 **0** · `frontend/` **0**.
> spec 이 「무엇을·왜·어떤 결정으로」의 정본이고 이 파일은 실행 뷰다. 어긋나면 spec 이 우선한다(`prd/specs/README.md`).

---

## 0. 읽기 규칙 — 이 파일이 유일한 부트스트랩

> ⛔ **아래 4개를 통째로 열지 않는다.**
> `dev-package/03-HANDOFF.md` · `dev-package/PLAN-SoT.md`(1.17 MB) · `dev-package/work-items.yaml` · `dev-package/WORK-UNITS.md`

- **허용된 접근은 아래 세 줄뿐이다.**
  1. 결정 번호 최대값 — `bash dev-package/prd/tools/max-decision.sh`
  2. 대장에서 항목 하나 — `grep -n -A14 '^  - id: WU-D4' dev-package/work-items.yaml`
  3. 게이트 이름 확인 — `grep -n -A20 '^ALL_GATES=(' gates/run.sh`
- `03-HANDOFF.md` · `CLAUDE.md` · `RESTART.md` 는 **머리 부분만** 읽는다.
- 요구사항 정본은 spec `R-D.md` ＋ intent 2건 ＋ 이 파일이다. 창 9 경위가 필요하면 `dev-package/sessions/R-C-ROUND-20260908.md` **§9 만**.
- **코드 파일은 고칠 때만 연다.** 정찰·grep 스윕은 `researcher` 에 위임하고 결론만 회수한다.
- 이 파일의 `path:line` 은 **트리 `52c10af`(= `origin/main` `a31111f` ＋ intent) 실측값**이다. 고친 뒤에는 다시 잰다. 못 재면 `[미상]`.

### 세션 시작

```bash
cd "<작업공간>/30 CoLAB-v2" && claude --add-dir "../40 COLAB-기획"
git fetch origin main && git log --oneline -8 origin/main     # §5-b (a) — 최근 회차를 먼저 본다
git branch -a | sed 's/^[* ] *//'                              # WU-D4 대상 실측(값을 미리 적지 않는다)
bash dev-package/prd/tools/max-decision.sh                     # 착수 시점 참고값(근거 아님)
```

- 에이전트 역할 — `advisor`(fable · ① fan-out 전 · ② 산출 수용 · ③ 병합 전) · `lane-worker`(opus · `isolation: "worktree"` · TDD·`verification-before-completion` 자동 탑재 → **intent 대조(미달·초과 0)** 가 레인 종료 조건) · `researcher`(sonnet) · `gate-runner`(haiku · `COLAB_GATE_OUTDIR` 필수).
- 훅 — H2 `worktree-setup.sh` 가 스폰마다 의존성을 건다. `test-file-guard`(`COLAB_FIX_LANE=1` 전용)는 **이 라운드에서 쓰지 않는다**(R-E 용). `git-guard.sh`·`decision-number-guard.sh` 는 켜져 있다.

---

## 1. 확정 결정 — 다시 열지 않는다

다르게 구현할 사유를 찾으면 **고치지 말고 보고한다.** 기획자에게 받아야 하는 답은 **0건**(프론티어 공집합 · intent `## 확인`) — 단 WU-D4 안에 「실측 보고 → Ted 한 줄」 자리가 하나 있다(판정이 아니라 삭제 승인).

- Ted 원문 3줄(2026-09-08) — 「좋아 intent에 얹어」(규칙 6) · 「모전부 권고대로 계획」(라운드 1 Q1~Q25) · 「전부권고대로」(하네스 eval Q1~Q8).
- **규칙 6**(intent 축자): ⑴ `main` 유일 배포 원천 · dev/prod sha 는 `origin/main` 조상 · `ship.sh` 거절 ⑵ staging 예외 ＋ 원장에 브랜치명 ⑶ `integration/r-N` 은 main tip 기점 · ff-only 한 줄 · 병합 뒤 삭제 ⑷ `lane/wu-*` 는 integration 기점 · rebase＋ff · 즉시 삭제 ⑸ 마이그레이션 형제 → `00NN_merge` ＋ 두 순서 drift 오라클 ⑹ 태그 `dev-YYYYMMDD-N` · `prod-YYYYMMDD`.
- 설계 트리 A — Q1 doctor 15항목 = `MAIN_SHA` 파일 대조 · Q2 게이트는 `ship.sh` 한 곳 ＋ doctor 사후 · Q3 태그 명명 · Q4 브랜치 정리 = 첫 WU · Q4a 창 9 잔여 = 실측 보고 → Ted 한 줄 → 삭제.
- 순서 합의 — 하네스 강화 → 배포(R-D) → 재검사 → 리스트업 → R-E. 디자인 판정 25건은 값만(집행 R-E).
- 하지 않는 것 — git-flow 계층 · prod 재개 · 마이그레이션 되돌림 정책 변경 · 원장 형식 전면 개정.

---

## 2. 범위 — 이 파일의 WU 4건

### WU-D4 · 브랜치 정리 (규칙 3·4 · Q4·Q4a) — 계층 저장소 · 크기 S · 레인 `rd-branch-sweep`

- **의존**: 없음 — 맨 앞(D2 의 조상 검사가 죽은 브랜치에 흔들리지 않게).
- **현재 코드(실측 `git branch -a` · 트리 52c10af)** — 로컬 5: `integration/r-a2` · `integration/r-b` · `integration/w9-dev-deploy` · `plan/r-d-0908` · `w9-rebase`. 원격 10: `feature/rtf400_deploy_prod` · `feature/rtf400_dev_scale_up` · `feature/rtf400_upload_reaper` · `gh-pages` · `integration/{r-a2,r-b,w9-dev-deploy,w9-dev-deploy-rebased}` · `plan/r-d-0908` · `urgent-upload-lineage-rev1`. 고유 이름 **11**(intent 「18」은 낡은 수 — `lane/wu-c*`·`integration/r-c` 는 이미 없다). 창 9 밖 커밋: `main..w9-rebase` = 3(`80aeb00`·`de1a5a2`·`97f1d99`) · `main..integration/w9-dev-deploy` = 2(`20b3715`·`13589fe`).
- **할 일** — ⑴ 실측 표 `dev-package/sessions/WU-D4-branches-<YYYYMMDD>.md`: 브랜치 | 로컬/원격 | `main` 조상 여부(`git merge-base --is-ancestor`) | 밖 커밋 수 | 밖 파일 중 현 `main` 동등물 유무(`git diff main..<tip> --stat` · 창 9 는 ai 체인분이 WU-C13 흡수됐음을 명시) | 용도(`gh-pages` 는 사이트 배포 브랜치인지 `git log -3` 로) | 권고(삭제/보류) ⑵ 조상이고 병합 완료인 것(`integration/r-a2`·`r-b`·`plan/r-d-0908` 은 R-D 병합 뒤) 즉시 삭제 — 삭제 전 `git tag archive/<브랜치명> <tip>` ＋ `git push origin --tags` ⑶ 창 9 계열 3 ＋ 원격 5 는 표를 오케스트레이터에 넘기고 **Ted 한 줄** 뒤 삭제(같은 태그 보존) ⑷ `plan/r-d-0908` 은 이 라운드가 `main` 에 ff 된 뒤 삭제(자기 발판).
- **수용 기준** — Given 표, Then 브랜치 11건 전행 · 조상/밖 커밋/동등물 열이 비지 않음(`[미상]` 허용 · 공란 금지) · Given 삭제, Then 각 대상에 `archive/*` 태그 선재 ＋ 원격 태그 존재 ＋ `git branch -a` 에서 0건 · Given Ted 한 줄 없음, Then 창 9 계열·원격 5 는 **남아 있다**(삭제 0).
- **시험 seam** — 셸 검증 `git tag -l 'archive/*'` · `git ls-remote --heads origin` 건수 전/후(`WU-D4` 노트에 축자).
- **좁은 게이트** — `exec-bit` · `work-item-consistency` · `planning-freshness`.

### WU-D1 · `docs/BRANCHING.md` ＋ `CLAUDE.md §10` (규칙 6 정본화) — 계층 문서 · 크기 S · 레인 `rd-branching-doc`

- **의존**: WU-D4(표의 실측값을 「하지 말 것」 예시로 인용).
- **현재 코드** — `grep -rn "브랜치 전략\|branching" CLAUDE.md docs/` = 0건 · `CLAUDE.md` 마지막 절 = `## 9. 업로드(S3)·배포`(`CLAUDE.md:161` · 파일 169행).
- **할 일** — ⑴ `docs/BRANCHING.md` 신설: 규칙 6 축자 · 브랜치 수명 표(`main` / `integration/r-N` / `lane/wu-*` / `plan/*` / `archive/*` 태그 / `dev-*`·`prod-*` 태그 — 기점 · 복귀 · 삭제 시점 · 누가) · 「하지 말 것」(git-flow 계층 · 미병합 sha 배포 · 병합 뒤 존치 · 손 워크트리) · 창 9 사례 한 문단(〈378〉 ⑧ 링크) ⑵ `CLAUDE.md` `## 10. 브랜치·배포 원천` 신설 — 요지 6줄 ＋ `docs/BRANCHING.md` 링크 · §9 원문 무삭제 ⑶ `RESTART.md`·`infra/dev/README.md` 에 「반입 전 main 조상 검사」 한 줄씩(원문 덧붙임).
- **수용 기준** — Given `docs/BRANCHING.md`, Then 규칙 6 문면이 intent `## 원한 결과` 1~6 과 축자 일치(diff 0) · Given `CLAUDE.md`, Then `## 10.` 존재 ＋ `git diff` 삭제 줄 0 · `planning-freshness` green.
- **시험 seam** — 문면 대조 스크립트 `dev-package/prd/tools/`(선례 `renumber-decisions.sh` 형태) 또는 `diff <(sed …)` 한 줄을 노트에 축자.
- **좁은 게이트** — `planning-freshness` · `work-item-consistency` · `exec-bit`.

### WU-D2 · 반입 게이트 ＋ `MAIN_SHA` ＋ 원장 브랜치 필드 ＋ 태그 (규칙 1·2·6 · Q2·Q3) — 계층 인프라 · 크기 M · 레인 `rd-ship-gate`

- **의존**: WU-D4(죽은 브랜치 제거 뒤 조상 검사).
- **현재 코드** — `infra/dev/ship.sh:14` `SHA="$(cat "$DIST/colab-v2-dev.sha")"` · `:20` 첫 ssh(`mkdir`) · `:21-22` scp · `:23-26` `docker load`＋재태그＋`echo $SHA > /opt/colab-v2/CURRENT_SHA` — 조상 검사 0 · `infra/staging/deploy.sh:266` `ledger_append deploy "$SHA" "$TAG" green "$ALIAS_NOTE digest이력=… $BACKUP_NOTE 워킹트리변경=${DIRTY_N}"` · red 행 `:71`·`:87` · `rollback.sh:59,82,93` 은 무접촉 · 태그 스크립트 없음(`prod-YYYYMMDD` 규약만 `〈334〉`).
- **할 일** — ⑴ `ship.sh:14` 직후: `git -C "$REPO" fetch -q origin main` 실패 → `exit 78`(준비 · 「origin 조회 실패 — 진행 금지」) · `git merge-base --is-ancestor "$SHA" origin/main` 실패 → `exit 65` ＋ 사유 · `COLAB_SHIP_ALLOW_NONMAIN=1` 선언 시 거절 대신 출력 「비조상 반입 · 우회 선언」 ＋ `ancestor=bypass` ⑵ `MAIN_SHA="$(git -C "$REPO" rev-parse --short=12 origin/main)"` · `:25` 같은 ssh 에 `printf 'main=%s candidate=%s ancestor=%s\n' … > /opt/colab-v2/MAIN_SHA` ⑶ `deploy.sh:266`(＋`:71`·`:87`) 비고 끝 `브랜치=$(git -C "$REPO" branch --show-current)` ⑷ `infra/dev/tag-release.sh` 신설 — 인자 `dev|prod` · `dev` = `dev-$(date +%Y%m%d)-N`(N = `git tag -l "dev-$(date +%Y%m%d)-*" | wc -l` ＋1) · `prod` = 기존 `prod-YYYYMMDD` · doctor 전건 뒤 사람이 호출 · 태그 대상 = `CURRENT_SHA` 와 같은 sha(로컬 `dist/colab-v2-dev.sha` 대조 · 불일치 → exit 65) ⑸ `infra/dev/README.md` 반입 절에 게이트·우회·`MAIN_SHA`·태그 4줄.
- **수용 기준** — 픽스처 저장소(임시 `git init` · `origin` 을 로컬 bare 로) ＋ `SSH=(echo)`·`SCP=(echo)` 스파이(`ship.sh` 는 env 로 명령 배열을 바꿀 수 없으므로 시험은 `bash -c 'source' ` 대신 **`PATH` 앞에 가짜 `ssh`·`scp`** 를 둔다): Given 비조상 sha, Then exit 65 · 가짜 ssh 호출 0 · Given 조상 sha, Then 통과 · 가짜 ssh 에 `MAIN_SHA` 기록 명령 ＋ `ancestor=yes` · Given `origin` 없음, Then exit 78 · Given 우회 선언, Then 통과 ＋ 출력 「우회 선언」 ＋ `ancestor=bypass` · Given `deploy.sh` 드라이런(선례 `WINDOW-…A5b.md` 방식), Then 원장 행 끝 `브랜치=integration/r-d` · Given 같은 날 `tag-release.sh dev` 2회, Then `-1`·`-2`.
- **시험 seam** — `gates/tools/*-selftest.sh` 픽스처 방식(임시 dir · exit 78 규약) · 신설 `infra/dev/tests/ship-gate.sh`(셸 시험 · 케이스 5).
- **좁은 게이트** — `exec-bit` · `work-item-consistency` · 신설 `infra/dev/tests/ship-gate.sh` 5/5.

### WU-D3 · `deploy_doctor` 15번째 항목 「실행 sha ∈ main」 (Q1) — 계층 점검기 · 크기 S · 레인 `rd-doctor-15`

- **의존**: WU-D2(`MAIN_SHA` 형식).
- **현재 코드** — `services/core-api/ops/deploy_doctor.py:62` `MARKS = "①…⑭"` · `:104` `mark = MARKS[no - 1]` · `check_*` 12 함수(`:200`~`:645`) · `:696-700` 호출 순서(`check_env_pair` → `check_routing` → `check_backups`) · EC2 에 git 없음(`infra/dev/README.md`).
- **할 일** — ⑴ `MARKS` 에 `⑮` ⑵ `check_main_ancestry(ctx, rep)` 신설: `/opt/colab-v2/CURRENT_SHA`·`/opt/colab-v2/MAIN_SHA` 읽기 → `candidate == CURRENT_SHA ∧ ancestor == yes` → ✓ · `bypass` → ✗ 「우회 반입」 · `no` → ✗ · 파일 부재·형식 불일치 → **✗**(─ 아님 · spec 우려 4 ⓐ) ⑶ `:700` 뒤 호출 · 요약줄 `항목 15 — ✓ N · ✗ N · ─ N` ⑷ 경로는 `ctx` 의 기존 `/opt/colab-v2` 상수 재사용(하드코드 중복 금지) ⑸ `docs/DEPLOY.md §6-1` 항목표에 ⑮ 한 행.
- **수용 기준** — 단위 시험(선례 `grep -rln "deploy_doctor" services/core-api/tests`): ⑴ 일치·`yes` → ✓ ⑵ `bypass` → ✗ ⑶ `MAIN_SHA` 부재 → ✗ ⑷ `candidate ≠ CURRENT_SHA` → ✗ ⑸ 요약줄 「항목 15」 · `len(MARKS) == 15` · 기존 14항목 시험 회귀 0.
- **시험 seam** — `services/core-api/tests/test_deploy_doctor*.py`(있으면 재사용 · 없으면 신설 1파일 · 파일 시스템은 `tmp_path`).
- **좁은 게이트** — `service-tests-core-api` · `exec-bit` · `work-item-consistency`.

---

## 3. 지켜야 하는 규약 — 명령으로

### ㉮ 워크트리 레인
- WU 하나에 레인 하나 = `rd-branch-sweep`(D4) · `rd-branching-doc`(D1) · `rd-ship-gate`(D2) · `rd-doctor-15`(D3). `Agent(subagent_type:"lane-worker", isolation:"worktree")` 로만 만든다. 통합 `integration/r-d` 로 rebase＋**ff** · 얹은 즉시 레인 브랜치 삭제(규칙 4 를 이 라운드부터 지킨다).
- 병렬 = **없음**(직렬 4). `R-D-2` 의 D5 는 D1 과 병렬 가능(파일 겹침 0).

### ㉯ 착수 전 — `work-items.yaml` 등재는 **이미 끝났다**
- `WU-D1`~`WU-D7` 7 블록(`status: open`). 확인 = `grep -n -A14 '^  - id: WU-D4' dev-package/work-items.yaml`. 이 세션이 하는 것은 상태 갱신(`done` ＋ `evidence`).

### ㉰ 계약 동결 해제 — **해당 없음**(계약 0). `contracts/` 무접촉이 곧 판정 — `contract-breaking` 회귀만.

### ㉱ 결정 번호 〈N〉 — 예약하지 않는다
```bash
git fetch origin main && bash dev-package/prd/tools/max-decision.sh   # 병합 직전에 다시 잰다
```
- 착수 시점 참고값 = **〈378〉**(2026-09-08 실측 · 근거 아님). 예상 행 2(브랜치 전략 정본화 · 하네스 eval 신설) — 문안은 `R-D-2 §4`.

### ㉲ 게이트 — 작업 중엔 단독, 병합 전엔 전건
```bash
COLAB_GATE_REPORT_DIR=dev-package/reports/R-D/<레인> ./gates/run.sh <좁은 게이트>
./gates/run.sh all -j 1        # 라운드 끝 · R-D-2 §5 에서 한 번(harness-eval 은 면제 선언 · 건수 노출)
```
- ⛔ 게이트를 끄거나 대상을 줄이지 않는다 · 구현 전 **red 를 눈으로 확인** · 대상 0건은 red · 관대한 기본값(`${VAR:-}`) 금지.

### ㉳ 커밋 문면
```
인프라 R-D-1 <WU 제목> (WU-D_)

- <바뀐 자리 1~3줄>
- 제품 코드 0 · 계약 0 · 마이그레이션 0
- RED 선실측 → GREEN: <시험 파일>:<건수>
```

### ㉴ 금지
- ⛔ `main` 직접 push(규칙 3 은 Ted 의 ff 한 줄) · ⛔ 손으로 만든 형제 워크트리 · ⛔ Ted 한 줄 없이 창 9 계열·원격 5 삭제 · ⛔ 태그 없이 브랜치 삭제.
- ⛔ `ship.sh` 게이트의 조용한 우회(우회는 선언·출력·`MAIN_SHA`·doctor 에 남는다) · ⛔ `rollback.sh` 접촉 · ⛔ staging/dev 실배포(이 라운드는 도구만 고친다 · 배포 창은 별건).
- ⛔ CLAUDE.md §9 · README 원문 삭제 — 덧붙인다.

---

## 4. 산출물과 근거

| 무엇 | 어디 |
|---|---|
| 브랜치 실측 표 | `dev-package/sessions/WU-D4-branches-<YYYYMMDD>.md` · `archive/*` 태그 |
| 문서 | `docs/BRANCHING.md` · `CLAUDE.md §10` · `RESTART.md`·`infra/dev/README.md` 한 줄씩 |
| 반입 게이트 | `infra/dev/ship.sh` · `infra/dev/tag-release.sh` · `infra/dev/tests/ship-gate.sh` · `infra/staging/deploy.sh:266`(＋`:71`·`:87`) |
| 점검기 | `services/core-api/ops/deploy_doctor.py`(`MARKS` 15 · `check_main_ancestry`) · `docs/DEPLOY.md §6-1` 행 1 · 시험 1파일 |
| 세션 노트 | `dev-package/sessions/rd-<레인>-<YYYYMMDD>.md` 4건 · 각 ≤60행(전/후 · 수용 기준 · 「하지 않은 것」 · intent 대조 미달·초과) |
| 대장 | `work-items.yaml` — 4 블록 `done` ＋ `evidence` |

**HANDOFF 갱신문(오케스트레이터 · 5줄 이하 · 세션은 `03-HANDOFF.md` 를 직접 고치지 않는다)**
```
R-D-1(브랜치 전략) 완료 — WU-D4·D1·D2·D3, 레인 rd-branch-sweep · rd-branching-doc · rd-ship-gate · rd-doctor-15, 통합 integration/r-d <sha>
브랜치 11 → <n>(archive 태그 <n>) · Ted 한 줄 <일자> · ship.sh 조상 게이트(exit 65/78 · 우회 선언) · MAIN_SHA · 원장 브랜치 필드 · tag-release.sh · doctor 15항목
게이트: 좁은 집합 green · service-tests-core-api green · ship-gate.sh 5/5
근거: dev-package/sessions/rd-*-<YYYYMMDD>.md 4건 · WU-D4-branches-<YYYYMMDD>.md
다음 = R-D-2-harness-eval.md(D5 · D6 · D7)
```

---

## 5. 완료 판정

- **WU-D4** — 표 11행 공란 0 · 즉시 삭제분에 `archive/*` 태그 선재 · 창 9 계열·원격 5 는 Ted 한 줄 전 무삭제.
- **WU-D1** — 규칙 6 축자 diff 0 · `CLAUDE.md ## 10.` · 원문 삭제 0 · `planning-freshness` green.
- **WU-D2** — `ship-gate.sh` 5 케이스(65 · 통과＋`ancestor=yes` · 78 · 우회 · 태그 N) · 원장 행 `브랜치=` · 가짜 ssh 호출 횟수 단언.
- **WU-D3** — 시험 5 ＋ 기존 14항목 회귀 0 · `len(MARKS)==15` · 부재 = ✗.
- **절차** — 레인마다 advisor ② 「intent 대조 미달·초과 0」 · 병합 전 advisor ③ · 레인 브랜치 즉시 삭제 · 〈N〉 병합 직전 실측.

### 다음 파일
`dev-package/prd/rounds/R-D-2-harness-eval.md`(D5 · D6 · D7 ＋ 라운드 종료 검증). D5 는 D1 과 병렬 가능하나 기본은 이 파일 4건 뒤.
