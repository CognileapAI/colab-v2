# BRANCHING — 브랜치·태그 수명 정본

> 요지 6줄과 이 파일 링크는 `CLAUDE.md §10`. 배포 절차 정본은 `docs/DEPLOY.md`, 규약은 `.claude/rules/deploy.md`.
> 이 문서는 **어느 브랜치가 어디서 나고 어디로 돌아가며 언제 사라지는가**만 정한다. 배포 값·자원 목록은 여기 두지 않는다.
> 출처 = `dev-package/intent/2026-09-08-r-d.md` 「원한 결과」 축 ① · spec `dev-package/prd/specs/R-D.md` · 실측 `dev-package/sessions/WU-D4-branches-20260908.md`.

---

## 1. 규칙 6 (intent 축자 — 병합 뒤 정본 = 이 파일 · 개정은 새 intent ＋ 이 파일 동시, 축자 대조는 그 intent 로 옮긴다)

<!-- rule6:begin -->
1. `main` 은 **유일한 배포 원천**. dev·prod 에 올라가는 sha 는 반드시 `origin/main` 의 조상. `ship.sh`·`up.sh`·staging `deploy.sh --target dev` 가 `git merge-base --is-ancestor` 로 검사하고 아니면 거절.
2. staging 은 예외 — `integration/*` HEAD 를 굽는다(리허설). 단 원장 행에 **브랜치 이름**을 같이 적는다.
3. `integration/r-N` 은 `main` tip 에서 따고, `main` 으로는 **ff-only 한 줄**. 병합 뒤 브랜치 삭제.
4. `lane/wu-*` 는 `integration` 에서 따고 rebase＋ff 로 돌아온다. 통합에 얹힌 즉시 삭제.
5. 마이그레이션은 **한 라운드 = 한 체인 구간**. 형제가 생기면 `00NN_merge` ＋ 두 순서 drift 오라클(0007 선례) 의무.
6. 릴리스 = 태그. dev 실적용 때 `dev-YYYYMMDD-N`, prod 는 기존 `prod-YYYYMMDD`. 〈N〉 행이 태그를 가리킨다.
<!-- rule6:end -->

- 검사 자리는 설계트리 Q2 로 `ship.sh` 한 곳 ＋ `deploy_doctor` ⑮ 사후 대조로 확정 · `up.sh`·`deploy.sh` 이중 검사 없음(WU-D2·D3)
- 위 6줄의 문면 대조 = 아래 한 줄(출력 0행 = 일치).

```bash
diff <(sed -n '/^\*\*축 ① 규칙 6개\*\*/,/^\*\*축 ① 산출물\*\*/p' dev-package/intent/2026-09-08-r-d.md | grep -E '^[1-6]\. ') \
     <(sed -n '/<!-- rule6:begin -->/,/<!-- rule6:end -->/p' docs/BRANCHING.md | grep -E '^[1-6]\. ')
```

- 규칙 1 의 반입 검사는 **`infra/dev/ship.sh` 안에 있다**(WU-D2 반영) — 비조상 거절 exit 65 · `origin` 조회 실패 exit 78 · 선언 우회 `COLAB_SHIP_ALLOW_NONMAIN=1`. 사후 대조는 `deploy_doctor` ⑮(§5).

---

## 2. 브랜치·태그 수명 표

| 이름 | 기점 | 복귀 — 어디로·어떻게 | 삭제 시점 | 누가 | 비고 |
|---|---|---|---|---|---|
| `main` | 없음(정본 줄기) | 해당 없음 — 도착점 | 없음 | Ted(ff 한 줄) | 유일한 배포 원천(규칙 1) · 직접 push 금지 |
| `integration/r-N` | `main` tip(해시를 박지 않고 `git rev-parse HEAD` 로 읽는다) | `main` 으로 **ff-only 한 줄** | `main` ff 직후 | 병합 = Ted · 삭제 = 오케스트레이터 | staging 리허설 대상(규칙 2) · 원장 행에 브랜치 이름 |
| `lane/wu-*` | 해당 `integration/r-N` | 통합으로 **rebase ＋ ff** | 통합에 얹힌 **즉시** | 생성 = `Agent(isolation:"worktree")` · 병합·삭제 = 오케스트레이터 | 레인의 끝 = 자기 브랜치 · 레인은 병합·원격 삭제 0 |
| `plan/*` | `main` tip | 복귀 없음 — 산출(라운드 파일·spec)은 통합 브랜치 커밋으로 들어간다 | 해당 라운드가 `main` 에 ff 된 뒤 | 오케스트레이터 | 워크트리 제거 선행(`git worktree remove`) |
| `archive/*` 태그 | 삭제 직전 브랜치 tip | 복귀 없음 — 보존 전용 | 없음(영구) | 로컬 생성 = 레인 · 원격 push = 오케스트레이터(게이트 ③ 뒤) | 배포 대상 아님 · `git push origin archive/<이름>` **개별** · `--tags` 금지 |
| `dev-YYYYMMDD-N` 태그 | dev 실적용 sha(로컬 `dist/colab-v2-dev.sha`) | 복귀 없음 | 없음 | 사람 — `deploy_doctor` 전건 뒤 호출 | N = 같은 날 기존 태그 수 ＋1 · 도구 = `infra/dev/tag-release.sh`(push 없음 · 명령만 출력) |
| `prod-YYYYMMDD` 태그 | dev 배포 창 N회를 green 으로 넘긴 `main` 커밋 | 복귀 없음 | 없음 | Ted | prod 는 `PLAN-SoT §9-㊻` 로 보류 · 그 태그에서만 배포 |

- 표 밖 이름은 **정본이 없다.** 새 접두어가 필요하면 이 표에 행을 먼저 추가한다.
- 하네스가 만드는 `worktree-agent-*` 는 레인 워크트리의 기술 브랜치이고 위 수명 규칙의 대상이 아니다.

---

## 3. 하지 말 것

| # | 하지 말 것 | 실측 예시 | 근거 |
|---|---|---|---|
| 1 | git-flow 계층(`develop`·`release/*`) 신설 | 없음 — 이번 라운드가 **명시 제외**로 닫았다. 사람 1 ＋ 에이전트 레인 구조에서 층만 늘고, 사고 원인(「책에 없는 층」)은 층수와 무관 | `dev-package/intent/2026-09-08-r-d.md` 「범위 밖」 |
| 2 | 미병합 sha 배포 | 창 9(2026-09-06)가 `integration/w9-dev-deploy` `20b3715` 를 dev 에 실었다 → §4 | `dev-package/sessions/WU-D4-branches-20260908.md` §2 · `PLAN-SoT §9 〈378〉 ⑧` |
| 3 | 병합 뒤 브랜치 존치 | `integration/r-a2` `ccd9372` · `integration/r-b` `9a4b257` — 둘 다 `main` 조상 · 밖 커밋 0 인데 로컬·원격에 잔존 | 같은 파일 §1 표 |
| 4 | 손으로 만든 형제 워크트리 | `git worktree add` 로 만든 형제 경로에서 레인 5개가 동시 정지(2026-09-03) — Bash 가드가 형제 경로를 공유 체크아웃으로 취급 | `.claude/rules/colab-rules.md §2-3` |
| 5 | `git push origin --tags` | `archive/*` 10건과 함께 잡태그가 원격으로 나간다. 개별 push 만 한다 | `dev-package/sessions/WU-D4-branches-20260908.md` §10 머리 |
| 6 | 태그 없이 브랜치 삭제 | 창 9 계열 삭제 시 **태그에만 남는 실체 4종** = dev 트리거 스풀 배선(compose ＋ README) · 매니페스트 `sourceLabel` 4값 · 창 9 원장 6행 · 창 9 실행 로그 20파일. reflog 는 원격에 없다 | 같은 파일 §2 |
| 7 | 열린 PR 의 head 를 통보 없이 삭제 | 원격 브랜치 삭제가 곧 PR close — 실측 open 3건: `feature/rtf400_deploy_prod`(#6) · `feature/rtf400_dev_scale_up`(#4) · `feature/rtf400_upload_reaper`(#5) | 같은 파일 §1 표 |

- ⑺ 의 이웃 사례 — `gh-pages` 는 **가동 중인 GitHub Pages 배포 원천**(`"status":"built"` · `"source":{"branch":"gh-pages"}`)이라 삭제하면 공개 URL 이 즉시 끊긴다. 처분하려면 Pages 설정 해제가 선행이고, 그 전까지 **보류·태그 미생성**이다. 근거 = 같은 파일 §7.
- 원격 브랜치 삭제·태그 push·PR close 는 **비가역 원격 행위**다. 레인은 표와 로컬 태그까지 하고, 집행은 게이트 ③ 뒤 오케스트레이터가 한다.

---

## 4. 창 9 사례 — 규칙 1 이 없던 자리에서 난 것

2026-09-06 창 9 는 `main` 밖 레인 sha `20b3715`(`integration/w9-dev-deploy`)를 dev 에 반입했고, 그 브랜치의 ai 마이그레이션 `0006_topic_vocab_six` 가 **dev 에만 적용된 채** 남았다. R-C 배포 창의 **dev 사전 실측에서 `alembic_version_ai` 스탬프 `0006_topic_vocab_six` 가 `main` 에 없는 리비전으로 발견**됐고(레포 체인에는 형제 `0006_rc7_synonym_category` 가 있었다 · STOP·중단 기록 0), Ted 판정 ⓐ 뒤 `WU-C13` 이 그 두 파일(`db/ai/versions/0006_topic_vocab_six.py` · `db/ai/seed/topic_synonym_six.sql`)을 파일 단위로 흡수하고 `0007_merge_vocab_and_category`(부모 둘 ＋ 두 적용 순서 drift 오라클)로 닫았다. **흡수되지 않고 `main` 에 동등물이 0 인 것**은 넷이다 — dev 트리거 스풀 배선(`infra/dev/compose.yml` 의 `COLAB_WORKER_EVENT_SPOOL`·`COLAB_VIZ_TRIGGER_SPOOL`·`viz-events` 볼륨 ＋ `infra/dev/README.md` 규약 8줄) · `infra/staging/manifest-refdata.json` 의 `sourceLabel` 4값 · 창 9 원장 6행 · `dev-package/reports/window-9/` 실행 로그 20파일. 반입 게이트가 있었으면 `20b3715` 는 dev 에 실리지 못했고, 이 넷은 `main` 을 통과하며 흡수 여부가 그때 갈렸을 것이다. 상세 = `PLAN-SoT §9 〈378〉 ⑧` · `dev-package/sessions/R-C-ROUND-20260908.md` §9 · `dev-package/sessions/WU-D4-branches-20260908.md` §2.

---

## 5. staging 예외와 긴급 우회 — 집행 자리 = `ship.sh` ＋ `deploy_doctor` ⑮

- **staging 예외(규칙 2)** — staging 은 `integration/*` HEAD 를 굽는다. 리허설이므로 조상 검사의 대상이 아니고, 대신 **원장 행에 브랜치 이름**을 같이 적는다(`infra/staging/deploy.sh` 의 `ledger_append` 비고 끝 `브랜치=`). staging 에서 완료 판정을 하지 않는다(`CLAUDE.md §0` 완료 조건).
- **긴급 우회** — 반입 게이트를 넘겨야 하는 날은 `COLAB_SHIP_ALLOW_NONMAIN=1` 을 선언한다. 거절 대신 통과하되 ⑴ 출력에 「비조상 반입 · 우회 선언」 한 줄 ⑵ EC2 `MAIN_SHA` 파일에 `ancestor=bypass` ⑶ `deploy_doctor` 15번째 항목이 그 값을 ✗ 로 판정 — 셋이 함께 남는다. 조용한 우회만 막고 선언된 우회는 허용한다.
- ⭑ **⟨개정 2026-09-08 · WU-D2·D3 병합⟩ 위 두 문단은 구현된 동작이다** ／ 종전 ~~「현재 트리에는 반입 게이트도 우회 경로도 없다 · `deploy_doctor` 도 14항목이다 · 예정 동작이다」~~ — `infra/dev/ship.sh` 가 `dist/colab-v2-dev.sha` 를 읽은 직후 `origin/main` 을 fetch 해 조상 검사를 하고, EC2 `/opt/colab-v2/MAIN_SHA` 에 `main=<12자리> candidate=<12자리> ancestor=yes|no|bypass` 한 줄을 적는다. `deploy_doctor` 는 **15항목**이고 ⑮ 가 `CURRENT_SHA`·`MAIN_SHA` 를 대조한다.
- 손으로 재던 한 줄(`git merge-base --is-ancestor <sha> origin/main`)은 `ship.sh` 게이트가 대신한다 — 반입 전 확인용으로 남겨 두되 반입의 조건은 게이트 쪽이다. 태그는 `infra/dev/tag-release.sh`(`dev-YYYYMMDD-N` · `prod-YYYYMMDD`).
