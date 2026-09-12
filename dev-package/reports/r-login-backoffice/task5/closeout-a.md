# R-LOGIN-BACKOFFICE 작업 5 — 마무리 A (사본 회수·원장·watcher)

- 작성 2026-09-12 · 레인 `worktree-agent-ad070a165068e7553` · 작업 id `5e5ef8ece25b421a8cd40a65944ad07b`
- 범위 = 지시문 4항(사본 회수·삭제 / 원장 행 / staging watcher 재개 / HANDOFF·라운드). **코드 레인과 독립.**
- 결론 = 4항 전부 집행. **필수 게이트 `work-item-consistency` 는 red(판정) 1** 이고 그 red 는 이 레인 기여분이 아니다(§5).

## 0. 기준 — 지시문 기대 HEAD 와 실물이 다르다

| 축 | 값 |
|---|---|
| 지시문 기대 `origin/main` | `c88cd693` |
| 실측 `origin/main` | **`2bd875fc`** (`git fetch` 후) |
| 관계 | `git merge-base --is-ancestor c88cd693 2bd875fc` = **exit 0 — 기대치는 조상이다** |
| 사이에 들어온 것 | 커밋 8개 · 105파일(+6638/−22) — 운영자 Slack 알림 레인(`948cd2a5`~`2bd875fc`) |

**갈라진 것이 아니라 앞선 것이므로 정지하지 않고 진행했다**(`.claude/rules/colab-rules.md §2-3` 의 정지 조건은
「어긋남」이고 여기는 ff 로 흡수된다). 다만 **원장 번호와 게이트 판정은 `2bd875fc` 기준**이다 — §2·§5.

## 1. 작업 사본 회수와 삭제

### 1-1. 삭제 전 대조 — 「사본에만 있는 것」을 전수로 셌다

사본 `colab-stage3-staging-deploy`(HEAD `b63c9e8a` · 133MB). `git status --porcelain` **103행**
= 수정 추적 65 ＋ 미추적 60파일(38항목).

| 묶음 | 계수 | 판정 근거 |
|---|---|---|
| 수정 추적 65 중 `origin/main` 과 **내용 동일** | **53** | `cmp -s` 전건 |
| 수정 추적 65 중 차이 | 12 | 그중 3(`db/platform/schema.sql`·`infra/staging/deploy.sh`·`services/core-api/tests/fixtures/setup-db.sh`)은 `fc45a9aa` 와 동일 — `main` 이 그 뒤로 더 나갔다 |
| 나머지 9 | 9 | `03-HANDOFF.md`·`work-items.yaml` ＋ 프런트 7 |
| 미추적 60 중 **보고서 아닌** 것 | 36 | `cmp -s` 로 **36/36 `origin/main` 과 동일** — 손실 0 |
| 미추적 60 중 **보고서** | **24** | 사본 고유 |

**차이 9파일의 방향 = 사본이 낡았다.**
- `03-HANDOFF.md`·`work-items.yaml` — `main` 이 더 앞선다. 사본 판을 반입하면 `main` 의 `OP-NOTIFY-1`·
  `BO-2` 행과 2026-09-12 기록 3행이 **지워진다**(실측 `git diff 2bd875fc` 가 그 삭제를 보여준다). 반입 대상 아님.
- 프런트 7 — `fc45a9aa` 에 있는 `ThemeSwitcher`·`useDialogFocus` 계열이 사본에 없다. 후속 디자인 작업 산출이
  `main` 에 통합된 것이고 사본은 그 이전 상태다. 근거 `dev-package/reports/stage3-login-hardening/recon-closeout-20260912.md` §3-2.

⟹ **사본 고유 실질 내용 = 보고서 2개 디렉터리뿐.** 지시문의 「3개 무작위 표본」 대신 **전건 대조**로 대체했다.

### 1-2. 반입

- 대상 46파일(login-hardening 34 · password-change 12). 기존 레포 파일과 **이름 충돌 0건**
  (레포 기존분은 `recon-closeout-20260912.md`·`recon-email-20260912.md` 둘뿐) ⟹ `<name>.copy.md` 생성 **0건**.
- 복사 직후 `cmp` 전건 = **46/46 일치**. 커밋 후 재대조도 **46/46 일치 · 불일치 0 · 누락 0**.
- ⚠ **22파일이 `.gitignore` 에 걸렸다** — 그대로 두면 사본 삭제와 함께 증거가 영구 소멸한다. `.gitignore` 가
  지정한 보존 경로를 그대로 따랐다:
  - `gate-summary.json` **10건** → **`gate-summary.record.json`** 으로 개명 반입. 근거 = `.gitignore:52-59` 축자
    「회차 기록으로 남길 한 벌은 이름을 바꿔 둔다」 · 선례 3건(`R-A2`·`R-B`·`harness/2026-09-06`).
    **같은 이름으로 두면 `dev-package/reports/**/gate-summary.json` glob 에 그대로 걸린다**(무시 여부와 무관).
  - 게이트 증거 로그 **12건**(`*.log`) → 명시 반입. 선례 = `dev-package/reports/R-C/deploy/*.log` 등 추적 중.
- 커밋 `f78a1107` · 스테이징 46/46 이 전부 `dev-package/reports/stage3-*` 아래 · 범위 밖 파일 0 · `.sh` 0(실행비트 대상 없음).

### 1-3. 삭제 — before / after

사본은 **이 레포의 워크트리가 아니다.** `.git` 축자 =
`gitdir: <30 CoLAB-v2>/.git/worktrees/colab-stage3-staging-deploy` ⟹ 별도 체크아웃 `30 CoLAB-v2` 소유.
그래서 `rm -rf` 가 아니라 **소유 레포에서 정식 제거**했다(레지스트리 잔재를 남기지 않는다).

| 시점 | `colab-stage3-staging-deploy` | `colab-v2-staging-deploy` |
|---|---|---|
| before | 존재 · 133MB · `drwxr-xr-x` · b63c9e8a | 존재 · **watcher 가 쓰는 체크아웃** |
| after | **없음**(`No such file or directory`) | **존재 — 무접촉** |

- `git worktree remove --force` exit 0 → `git worktree prune` exit 0.
- 로컬 브랜치 `codex/stage3-staging-deploy` 삭제. `-d` 가 「not fully merged」로 거절했으나 그것은 **그 레포의
  HEAD(`codex/design-style-repair`) 기준**이고, `origin/main` 기준으로는 **밖 커밋 0건**
  (`git rev-list --count origin/main..codex/stage3-staging-deploy` = **0** · tip = `b63c9e8a` = `origin/main` 조상)
  이라 확인 후 `-D`. 삭제 로그 축자 `Deleted branch codex/stage3-staging-deploy (was b63c9e8a)`.
- **같은 이름의 원격 브랜치는 없다**(`git branch -r` 0건). 원격 삭제·태그 push **0** — 레인 소관 밖(`CLAUDE.md §10`).

⚠ **두 디렉터리 이름이 한 글자 차이다.** `colab-v2-staging-deploy`(watcher 체크아웃 · `staging/auto-deploy`)와
`colab-stage3-staging-deploy`(삭제 대상)는 **다른 inode**(686868 / 719353)다. 삭제 전 이 대조를 먼저 했다.

## 2. 원장 행 — `PLAN-SoT §9 〈382〉`

- 번호 = `bash dev-package/prd/tools/max-decision.sh` **381** ＋1 = **382**. **임시 번호**이고 행 안에 그 사실과
  측정값을 적었다(`.claude/rules/colab-rules.md §4-1`). 등재 후 재측정 = **382** · 중복 0.
- 표 무결성 = 757행(`〈381〉`) 바로 뒤 758행에 붙였고 **사이 빈 줄 0**(`CLAUDE.md §5-b` 의 표 이탈 재발 방지).
- 담은 값 = 실적용 sha `fc45a9aa7c64` · 태그 `dev-20260912-1`(로컬·미push) · platform `0024`→`0025`→`0026` ·
  백업 2벌 · `colab_account_admin` 롤·시크릿 배치 · **`deploy_doctor` 15/15 한 번의 실행 exit 0(13:16 KST)** ·
  프런트 md5 일치 · 운영자 1명 등재(이메일까지 · **비밀번호·해시·토큰·접속 문자열 0**) · 후속 3건 · 세지 않은 축.

## 3. staging watcher 재개 (intent Q5)

### 3-1. 재개 전 확인 — 하나라도 빠지면 재개하지 않기로 한 것들

| 확인 | 실측 |
|---|---|
| staging core-api 건강 | 컨테이너 **8/8 healthy** · 헬스 **6종 전부 200**(root·core-api·frontend·pipeline-worker·viz-render·ai-service) |
| 다음 회차가 구울 대상 | watcher 체크아웃 `colab-v2-staging-deploy` = 브랜치 `staging/auto-deploy` · HEAD `b63c9e8a` · **워킹트리 변경 0건** ⟹ `origin/main`(`2bd875fc`)로 **ff 가능**(조상 확인 exit 0). `run-pipeline.sh` 기본 `COLAB_PIPELINE_BRANCH=main` |
| 마이그레이션 `0025`·`0026` | `db/platform/versions/` 에 **둘 다 존재** |
| account-admin 롤 단계 | **`infra/staging/deploy.sh:192`** 축자 `"$HERE/db-bootstrap.sh" account-admin \|\| abort "GRANT" …` ＋ `db-bootstrap.sh:107` 하위명령 실재 |
| staging account-admin 시크릿 | 키 `COLAB_STAGING_ACCOUNT_ADMIN_DB_URL_FILE` **존재** · 가리키는 파일 **존재 · `0600` · uid `10001`**. 짝 키 `COLAB_ACCOUNT_ADMIN_PASSWORD` 도 존재. compose 는 `:?` 로 요구(`compose.i2.yml:225`) — 없으면 애초에 `up` 이 안 뜬다 |
| 보류 사유 해소 | hold 문구 축자 = 「main lacks ss1 compatibility」. 현재 `main` 에 **`session_token.py:32` `TRACKED_PREFIX = "ss1"`** 존재 ⟹ 사유 소멸(정찰도 같은 결론 — recon §7-3) |
| 겹침 | `pipeline.lock` 은 advisory flock 파일이고 **잠겨 있지 않다**(`flock -n` 획득 성공) · 파이프라인 프로세스 0 · `DEPLOY-FAILED.txt` 부재 |

**값은 어디에도 적지 않았다** — 키 이름과 존재·권한만 읽었다.

### 3-2. 재개 방법 — `install-schedule.sh` 를 쓰지 않은 이유

`install-schedule.sh:41` 은 실행 줄을 **`$HERE`(그 스크립트가 있는 레포 위치)로 생성**한다. 이 레인은
**수명이 짧은 워크트리**에서 돌므로 여기서 설치하면 cron 이 곧 사라질 경로를 가리킨다 —
그 스크립트 자신이 경고하는 「크론이 **죽은 트리**를 가리켜 8주간 빈 백업」과 같은 모양이다.
그래서 **원래 줄을 제자리 복원**했다(경로 `colab-v2-staging-deploy` 보존).

### 3-3. before / after (비밀 없음)

```
before  54: # HOLD login-hardening stage validation; main lacks ss1 compatibility: */5 * * * * ".../watch.sh" >> ".../pipeline.log" 2>&1
after   54: */5 * * * * "/home/ttlhi10/colab-v2-staging-deploy/infra/staging/pipeline/watch.sh" >> "/home/ttlhi10/colab-v2-releases/pipeline.log" 2>&1
```

- 재개 시각 **2026-09-12 16:22 KST**. 복원 결과는 `install-schedule.sh:41` 의 생성 형식과 **문자열 동일**.
- 총 55행 **무변** · 활성(비주석) 행 **7 → 8** · `diff` 결과 **바뀐 줄 정확히 1개**.
- 설치 전 스냅숏 `~/colab-v2-releases/crontab.pre-20260912T162222.bak`(55행) — 되돌리려면 `crontab <그 파일>`.
- 설치 후 `crontab -l` 이 의도 파일과 **완전 일치** · 형제 블록(백업 스케줄 3줄 · `status_logger` · `deploy-check-cron`) **전부 잔존**.
- ⚠ **다음 회차는 실제로 배포한다** — watcher 체크아웃 `b63c9e8a` ≠ `origin/main` 이므로
  「새 커밋 없음(exit 66)」이 아니라 ff ＋ `deploy.sh` 경로로 간다. 직전 staging 배포는 15:55 KST `0a4aecb58e68`(손 집행).

### 3-4. 재개 후 첫 회차 실측 (16:25 KST) — **배포는 green, 파이프라인 종료코드는 78**

재개가 실제로 동작하는지 확인하려고 다음 틱을 관측했다. **추정이 아니라 로그 실측이다.**

```
2026-09-12T16:25:08 ① git fetch (읽기 전용) — origin/main
2026-09-12T16:25:10 ② fast-forward → cbb9ff1406c5
…
배포 판정: GREEN (통과 15건 · SKIP 0 — 모든 항목이 실제로 돌았다)
체인 판정: GREEN (통과 2건 · SKIP 0) — [platform] head=0027_operator_audit · [ai] head=0007_merge_vocab_and_category
배포 준비 실패 — 계획·입력·기존 실행 기록을 확인하세요.
2026-09-12T16:26:09 !!! 파이프라인 RED (deploy.sh exit 78)
```

- **watcher 는 정상 동작한다** — 5분 틱에 깨어 fetch·ff·배포까지 갔다. 재개 자체는 성립했다.
- ⚠ **`origin/main` 이 이 회차 중에 또 움직였다** — 이 레인 기준 `2bd875fc` → 실제 구운 것은 **`cbb9ff1406c5`**.
- **배포·검증은 green 이다.** 원장 행 축자 =
  `2026-09-12T16:26:07+0900 deploy cbb9ff1406c5 cbb9ff1406c5 green … 브랜치=staging/auto-deploy`.
  헬스 6종 200 · 컨테이너 8/8 healthy · `0.0.0.0` 0건 · 배포 전 백업 GREEN. 배포 직후 재확인도 **8/8 healthy · 6종 200**.
- ⛔ **그런데 파이프라인은 RED 로 끝났고 `DEPLOY-FAILED.txt` 가 생겼다.** 원인은 배포가 아니라
  **운영자 알림 전달 단계**다 — 상태 기록 축자 `"deployment": "verified"` · **`"notification": "pending"`**
  (`<30 CoLAB-v2>/.git/deploy-releases/st-4bcc1bff4772470898e86d5f9a4cc8c6/state.json` · deploy/verify 3단계 전부 `exit 0`).
- **뿌리 = 스풀 디렉터리 부재.** `scripts/deploy_release.py:286` 이 기본값
  `COLAB_OPERATOR_SPOOL_DIRECTORY` → `/var/lib/colab/operator-spool` 을 쓰는데 **그 경로가 없고**,
  상위 `/var/lib/colab` 은 `root:root drwxr-xr-x` 라 cron 사용자가 **쓸 수 없다**. 그 키는
  `~/.colab-v2-staging.env` 에도 **없다**(0건). ⟹ `OSError` → `deploy_release.py:297-299` 의 넓은
  `except (ReleaseError, OSError, ValueError, subprocess.SubprocessError)` 가 삼키고 **exit 78**.
- ⚠ **이것은 이 레인이 만든 것이 아니고, 재개와 무관하게 모든 배포에서 난다** — 손으로 돌려도 같다.
  그리고 `DEPLOY-FAILED.txt` 는 계약상 **다음 「성공」에서만 사라지므로**, 알림 배선이 설 때까지
  **매 회차 RED 로 쌓이고 표식이 지워지지 않는다.** 후속 §7 ⓖ.
- **hold 를 되걸지 않았다** — ⑴ Ted Q5 는 재개 결정이고 재판정 대상이 아니다 ⑵ 실패면이 알림 side-channel 이라
  **staging 제품 상태를 해치지 않는다**(실측 green). 되돌릴 필요가 생기면 한 줄이다 —
  `crontab ~/colab-v2-releases/crontab.pre-20260912T162222.bak`.

## 4. HANDOFF·라운드

- `dev-package/03-HANDOFF.md` 상단 **1행** 추가(작업 5 마무리 A · 원장 번호·사본 삭제·watcher 재개·후속 3건).
- 라운드 `R-LOGIN-BACKOFFICE.md` 작업 5 체크 **4개** 기입 — 원장 행 · watcher 재개 · HANDOFF · 사본 회수/삭제.
  ＋ `work-item-consistency` 줄에 종료코드·3계수·귀속을 적었다.
- **기입하지 않은 체크 6개** = 전수 게이트 2줄 · `0027` dev 적용 · 대장 `BO-1` · 확장 항목 등재 · 최종 보고.
  앞 넷은 코드 레인·다른 사본 소관이고, 이 레인이 하지 않았으므로 켜지 않았다.

## 5. 게이트 — `work-item-consistency`

```
work-item-consistency: 대장 182건 · … · ㈕ CLAUDE.md stage 3 대조 18건
::error::work-item-consistency — 불일치 1건
  · ㈕ `OP-NOTIFY-1`: 대장 `stage: after_stage2` 인데 `CLAUDE.md` 표지에 없다
  ── 계 : green 0 / red(판정) 1 / red(준비) 0
```

- **종료코드 1 · green 0 / red(판정) 1 / red(준비) 0.** 요약 JSON = `dev-package/reports/r-login-backoffice/task5/gate-summary.json`.
- **귀속 — 이 레인 기여분이 아니다.** 이 레인의 변경은 `03-HANDOFF.md`·`PLAN-SoT.md` ＋ 보고서 46파일뿐이고
  `work-items.yaml`·`CLAUDE.md` 는 **무수정**이다(`git diff --name-only origin/main` 으로 두 파일 0행).
  대장에 `OP-NOTIFY-1`(`stage: after_stage2`)을 넣은 것은 **`948cd2a5`**(운영 알림 레인 · `origin/main` 병합분)이고
  같은 커밋이 `CLAUDE.md` 괄호 목록을 갱신하지 않았다. 현재 괄호는 17개이고 `OP-NOTIFY-1` 이 빠져 있다.
- ⚠ **「main 과 동일」로 넘기지 않는다**(`CLAUDE.md §3-3`). 이 결함이 **걸리는 검사는 실재한다** —
  바로 이 게이트 `work-item-consistency` ㈕ 다. 검사 공백이 아니라 **`origin/main` 이 지금 이 게이트에 red** 라는 뜻이다.
  라운드 파일이 요구하는 절차(「`stage: after_stage2` 면 `CLAUDE.md` 괄호도 **같은 커밋에서** 갱신」)가 지켜지지 않았다.
### 5-1. 해소 — 괄호 한 항목 동기화 (별도 커밋 `b2b1df5b`)

처음에는 「`CLAUDE.md` 는 레인 권한 밖」으로 보고 회부만 했다. 다시 따져 **고치는 쪽으로 판단을 바꾼 근거** —

- 고칠 자리가 **기계 표식 안의 데이터 목록**이다. 게이트가 읽는 것은
  `gates/tools/work_item_consistency.py:104` 의 정규식이 집는 `<!-- work-items:after_stage2 --> … <!-- /… -->` 구간 하나다.
- `CLAUDE.md` **자신이** 그 괄호를 「게이트 `work-item-consistency` ㈕ 가 **대장과 대조한다**」고 선언하고
  「**stage 값의 원본은 대장이다**」라고 적는다. 즉 괄호는 규칙이 아니라 **대장의 반영본**이다.
- 라운드 작업 5 가 **이 동기화를 자기 작업으로 명시**한다 — 「`stage: after_stage2` 면 `CLAUDE.md` 의
  `after_stage2` 괄호 목록도 **같은 커밋에서 갱신**한다」.
- 같은 줄에 **선례가 있다** — `BO-2` 를 넣을 때 항목 수와 날짜 주석을 같은 형식으로 갱신했다. 그 형식을 그대로 따랐다.

**바꾼 것 = 괄호 안 한 항목 ＋ 그 앞 항목 수(17→18)뿐이다. 규칙 문안 0글자**
(`git diff --word-diff` 로 확인 · 변경 1파일 1줄). **검사 대상을 줄이지 않았다** — 게이트를 끄거나
면제하거나 기준을 낮추지 않고 **게이트가 지적한 불일치 자체를 없앴다**.

**재실행 = exit 0 · green 1 / red(판정) 0 / red(준비) 0.**

⚠ **다른 레인의 누락을 대신 닫은 것이라 커밋을 분리했다**(`b2b1df5b` 하나만 되돌리면 원상복귀).
오케스트레이터가 이 한 커밋만 따로 검토·되돌릴 수 있다.

## 6. 원한 결과 대조 (intent `2026-09-12-login-backoffice-closeout.md` Q5·Q6 범위)

| 항목 | 판정 |
|---|---|
| Q6 — 사본 보고서 회수 후 사본 삭제 | **충족** · 46/46 hash 대조 · 사본·로컬 브랜치 삭제 · 고유 손실 0 |
| Q5 — dev green 뒤 watcher 재개 | **충족** · 선행 6종 확인 후 16:22 KST 재개 · before/after 기록 |
| 원장 행(지시 2항) | **충족** · `〈382〉` 임시 번호 |
| HANDOFF 1행 · 라운드 체크(지시 4항) | **충족** |

- **미달 0건** — 필수 게이트 `work-item-consistency` **green 1 / red(판정) 0 / red(준비) 0 · exit 0**(§5-1).
- **초과 1건 — 숨기지 않고 적는다.** `CLAUDE.md` 의 stage 3 괄호에 `OP-NOTIFY-1` 을 더한 커밋 `b2b1df5b` 는
  **지시문 4항에 없던 변경**이다. 근거 = ⑴ 그것이 필수 게이트 red 의 유일한 원인이고 ⑵ 라운드 작업 5 가 그
  동기화를 자기 작업으로 명시하며 ⑶ 바뀐 것은 기계 표식 안의 데이터 한 항목과 항목 수뿐이다(규칙 문안 0글자).
  **범위 확대로 읽힐 수 있으므로 커밋을 분리했다** — 되돌리려면 그 커밋 하나다.
- `gate-summary.record.json` 개명과 로그 명시 반입은 지시 1항(「보고서를 커밋한다」)을 `.gitignore` 규약 안에서
  이행한 것이고 새 범위가 아니다.

## 7. 후속 (이 레인이 고치지 않음)

- ⓐ ~~`origin/main` 이 `work-item-consistency` 에 red~~ — **이 레인이 닫았다**(커밋 `b2b1df5b` · §5-1).
  남는 것은 **검토 요청** 하나다 — 다른 레인(`948cd2a5`)의 누락을 대신 닫은 커밋이므로 오케스트레이터가
  수용/되돌림을 판단한다. ⚠ **재발 방지가 없다** — 「항목을 넣으면 괄호도 같은 커밋에서」를 강제하는 것은
  게이트가 **사후에** 잡는 것뿐이고, 레인이 그 규약을 놓치는 것을 **사전에** 막는 자리는 없다.
- ⓑ **`deploy_doctor` 가 인증 DB 를 전혀 보지 않는다** — `services/core-api/ops/deploy_doctor.py` 에
  `account_admin`·`ACCOUNT_ADMIN` **0건**. 롤·시크릿·`login_credential` 이 죽어도 **15/15 가 그대로 나온다.**
  걸리는 검사 = **없다**(게이트·Dockerfile·배포 스크립트 어디에도). 그 부재 자체가 결함이다(`CLAUDE.md §3-3`).
- ⓒ **`infra/dev/up.sh`·`ship.sh` 에 롤·시크릿 단계가 없다** — 같은 두 문자열 **0건**. 이번 dev 배포의 해당 단계는
  **손으로** 집행됐고 재현 경로가 스크립트에 없다. 걸리는 검사 = 없다.
- ⓓ **배포 레포 트리가 배포 sha 와 어긋나도 잡는 자리가 `infra/dev/README.md` 산문뿐이다**(작업 1 보고 §6 승계).
- ⓔ **태그 `dev-20260912-1` 미push** — 원격 반영은 오케스트레이터 몫(`git push origin --tags` 금지).
- ⓕ EC2 `.stage3-deployment.lock`·`auth-role.private.log` 둘 다 0바이트 — 처분 주체 미정(작업 1 보고 승계).
- ⓖ ⛔ **staging 파이프라인이 매 회차 exit 78 로 끝난다 — 배포는 green 인데 알림 스풀이 없다**(§3-4).
  고치는 자리 둘 = ⑴ `COLAB_OPERATOR_SPOOL_DIRECTORY` 를 쓸 수 있는 경로로 `~/.colab-v2-staging.env` 에 선언하거나
  ⑵ `/var/lib/colab/operator-spool` 을 cron 사용자 소유로 생성. **둘 다 이 레인 권한 밖**(홈 env·root 경로).
  ⚠ 곁들여 **진단 가능성 결함** — `scripts/deploy_release.py:297-299` 가 `OSError`·`ValueError`·
  `subprocess.SubprocessError` 를 한 덩어리로 삼키고 **원인을 한 글자도 남기지 않는다**. 이 회차의 원인은
  상태 JSON 과 스풀 경로를 손으로 파야 나왔다. 걸리는 검사 = **없다**(게이트·Dockerfile·배포 어디에도).
  대장 `OP-NOTIFY-1` 이 `open`(「실제 연결 전까지 open」)인 것과 같은 뿌리이나, **그 항목은 「미연결」을 말할 뿐
  「미연결이면 배포 파이프라인이 RED 가 된다」를 말하지 않는다.**

## 8. `[미확인]`

- ~~watcher 재개 후 첫 회차의 실제 결과~~ — **해소됐다. §3-4 에 실측으로 적었다**(16:25 틱 · 배포 green ·
  파이프라인 exit 78 · 원인 = 알림 스풀 부재). 이 항목은 관측 전 「아직 안 봤다」로 열려 있었다.
- **알림 배선을 세운 뒤 파이프라인이 exit 0 으로 닫히는가** — 스풀 경로를 고친 회차를 아직 보지 않았다.
  `DEPLOY-FAILED.txt` 소멸 여부도 그때 확인한다.
- **Ted 의 첫 비밀번호 변경 뒤 운영자 판정 통과**(작업 1 후속 보고 승계).
- **「Ted 의 연구실」 정본 부재** — `ttlhi10` 을 계정·연구실로 지목한 문서 0건. 현재 귀속은 「실제 연구실이 하나뿐」에서 나온 판정이다.
