# WU-C3 — `reseed.sh` 10단계 · 실측 메모

- 산출물 = `dev-package/tools/dev-reseed/`(`reseed.sh`·`lib.sh`·`preflight.sh`·`stages.sh`·`report.py`·`result-schema.json`·`tests/preflight-red.sh`) · 스킬 `.claude/skills/dev-reseed/SKILL.md`.
- 증명 = `--dry-run` 전 10단계 exit 0(dev·AWS·docker 무접촉 · 레포 작업 트리 무변) · 실패 픽스처 exit 1 ＋ 미달 10항목 이름.
- preflight 10항목은 **전건 실물 검사**다. 대역(stub)으로 채운 항목 0건. dev 접속이 필요한 셋(`dev-sha`·`secrets`·`leftovers`)은 조회가 실패하면 **미달**로 떨어진다 — 「못 물어본 것」을 「0 건」으로 읽지 않는다.
- `--dry-run` 은 preflight 를 **판정하지 않고 검사 항목만 찍는다**. 이유 = 검사 자체가 dev·AWS·docker·참조자료 드라이브를 건드려 무접촉 요구와 양립하지 않는다.
- 자원 하한 = 메모리 4,096 MiB · 디스크 20 GiB(`COLAB_RESEED_MIN_MEM_MIB`·`COLAB_RESEED_MIN_DISK_GIB` 로 변경). 근거 = 호스트 WSL 12 GB 에서 전수 ＋ 에이전트 동시 실행 OOM 실측(`.claude/rules/colab-rules.md §9`) · `infra/dev/build.sh` 가 arm64 5벌을 tar 한 벌로 `dist/` 에 저장.
- 미리보기 대기 = 45,000 ms(`COLAB_RESEED_PREVIEW_WAIT_MS`). 근거 = `dev-package/sessions/DR-3-run-2026-09-13.md §6` — viz-render 실소요 20,037~38,391 ms · core-api 가 10,02x ms 에 503. 뒷단은 `PV-2` 로 범위 밖이라 **판정만** 한다.
- 런북 정정 6건은 자리마다 「근거: R-DEV-RESET §11-1 ⑴」 주석으로 반영 — ⑴⑵⑷ psql(스킴 치환·`--user 0`·`postgres:16-alpine`) · ⑶ 버킷·리전 리터럴 · ⑸ 비밀번호 이름 넷 · ⑹ 체인별 버전 표 `alembic_version_platform`·`alembic_version_ai` 질의(bootstrap ②′ · head 값의 정오는 `up` 단계 `deploy_doctor` ⑥⑦ 이 레포 트리와 대조).
- 러너 `--accounts-file` 은 이 기준(`dc07aab8`)에 **없다**. `[ -n "$ACCOUNTS_FILE" ]` 뒤에만 넘긴다 — WU-C1b 가 붙이면 그대로 동작한다.
- 사람 입력이 필요한 자리 **0건**. `ssh` 는 `BatchMode=yes` 고정이고 `docker compose run` 은 `-T … < /dev/null`, 러너·`build_plan.py` 는 비대화형이다.
- 검사에 걸리지 않는 기존 결함 2건(기존이라 적지 않고 어디에 걸리는지 적는다) — ⓐ `ship.sh` 가 `/opt/colab-repo` 트리를 밀지 않아 `deploy_doctor` ⑥ 이 옛 head 를 정답으로 삼는다(걸리는 검사 = `deploy_doctor` ⑥ 뿐 · 배포 계획에는 없다 · 이슈 #48 ⑴). ⓑ `deploy_web.py` 가 `AWS_PROFILE` 을 해석하지 않는다(걸리는 검사 = 배포 9단계 실행 자체뿐 · 게이트 없음 · 이슈 #48 ⑵). 이번 레인은 둘 다 **preflight 로 앞당겨 잡을 뿐** 원인을 고치지 않았다.
- 실행 자리 `dev-package/reports/dev-reseed-runs/` 를 `.gitignore` 에 추가(로그에 원격 경로·접속 문자열이 들어온다).
- 하지 않은 것 — dev 실환경 실행(WU-C4) · `dev-seed/**` 수정 · 원장·HANDOFF·`PLAN-SoT` 편집 · 새 게이트 신설.

## 수정 회차 — 인수 검토 반려 7건 반영

- ① `stages.sh doctor_summary_line` — 요약줄 앞에 **공백 2칸**이 붙는다(`deploy_doctor.py` `print(f"\n  {text}")`). `^항목` 으로는 한 줄도 안 잡혀 **15/15 를 판정한 적이 없다**. 공백을 벗겨 잡고 **마지막 한 벌**만 읽는다. 픽스처 `tests/doctor-parse.sh` ＋ 표본 `tests/fixtures/`(`DeployReport`·`verdict` 로 찍은 것 · 손으로 적지 않음).
- ② `preflight.sh pf_build_plan` — 요약줄 두 모양(`datasets 28 edges 18` / `… data_bytes N`)을 낱말 경계로 끊어 둘 다 읽고, 요약줄 부재는 미달. **실측 정정** — `--dry-run` 경로는 `data_bytes` 없는 앞 모양을 낸다(`build_plan.py` `main`), `data_bytes` 는 `--check-manifest` 경로(`check_manifest`)다. 종전 `grep -qx` 도 실제 호출에서는 맞았고, 고친 것은 **두 모양 다 견디게** 한 것이다.
- ③ `reseed.sh` 단계 선택 — **preflight 는 언제나 돈다.** `--from` 은 바꾸는 단계 여덟 중 시작 지점만 고른다. 종전 `--from reset` 은 preflight 를 건너뛰어 `TARGET_SHA` 가 빈 채로 이미지 태그(`…:dev-`)·승인 기록에 들어갔다. `--preflight-only` 신설.
- ④ `lib.sh die` — `exit` → `return`. 종전에는 단계 순환이 끊겨 `stage_end`·`report` 가 못 돌아 **실패 회차에 `result.json` 이 없었다**. `stage_prelude` 의 `${VAR:?}` 넷도 같은 이유로 항목 열거 ＋ 복귀로 바꿨다.
- ⑤ `stages.sh preview_verdict` — 빈 값·숫자 아닌 값은 「성립」이 아니라 **「판정불가」**이고 `verify` 가 비영 종료한다. `result-schema.json` enum ＋ `report.py`(모르는 값을 「미성립」으로 접던 자리)도 함께.
- ⑥ `preflight.sh pf_leftovers` — `--path-format=absolute --git-common-dir`. 상대경로면 `deploy-releases` 검사가 **언제나 거짓**이라 진행 중 배포를 못 본 채 「0 건」으로 통과시켰다(fail-open).
- ⑦ `stages.sh stage_report` — 회차 기록 이름에 `RUN_ID`(날짜＋시각). **레포에 남기는 조건 = 바꾸는 단계가 실제로 돌았다** — preflight 에서 멈춘 회차·`--preflight-only`·`--dry-run` 은 실행 자리에만 남는다(픽스처가 `dev-package/sessions/` 를 더럽히던 자리).
- 실행 중 추가로 찾은 것 2건(검토 목록 밖) — ⓐ `pf_build_plan`·`stage_seed` 의 `$COLAB_REF_ROOT` 가 `set -u` 아래 **unbound 로 터져** 실행 전체가 죽었다(`${…:-}` 로 고침) ⓑ dev 접속 값 부재가 `${VAR:?}` 로 셸을 끝내 `result.json` 이 없었다 — `dev-sha`·`secrets`·`leftovers` 가 변수 이름을 대고 미달로 떨어지게 고쳤다.
- 게이트 `dev-reseed-selftest` 신설(`gates/run.sh` ＋ `gates/tools/dev-reseed-selftest.sh` ＋ `gates/README.md` 행). 이 판독부가 **걸리던 검사는 0건**이다 — 게이트에도 Dockerfile 에도 배포 스크립트에도 없었고 dev 를 한 번 돌려야만 드러났다.
- 실모드 증명 = `--preflight-only` 1회. 통과 4(qemu · agent-browser · resources · **build-plan `datasets 28 edges 18`**) · 미달 6(git 작업 트리 미정리 · dev-sha/secrets/leftovers = `COLAB_DEV_SSH`·`COLAB_DEV_KEY_FILE` 미설정 · aws 자격 미해석 · ref-root = `COLAB_REF_ROOT` 미설정). 출력·로그·`result.json` 에 접속 문자열·비밀번호·키 **0건**.
- 이번에도 하지 않은 것 — dev 전 단계 실행(접속 값 부재) · `dev-seed/**` 수정 · 원장·HANDOFF·대장 편집 · `deploy_release.py` 연동.

## 2차 수정 — 계수 판독 fail-closed ＋ 3건

- ⑧ `stage_verify` 계수 판독 — 「미지정」·usage-card 계수를 `tr -dc '0-9'` 로 받아 **부재와 「0」이 같은 모양**이 됐고, 표에 `${unset_lv:-0}`·`${level:-?}` 로 기본값까지 박아 **한 값도 못 받은 회차가 「미지정 0건 · 전건 연결」로 통과**했다(fail-open). 고침 = `tr -d ' \t\r\n'` 로 받고 받은 값을 그대로 적는다.
- ⑨ 판정을 `count_verdict()` 로 떼어냈다 — `cnt()` 가 숫자 아닌 값을 `None` 으로 내고, `None` 은 **연결로도 미연결로도 세지 않고** 「판정불가」로 따로 미달을 낸다. `미지정 = (cnt or 0) > 0` · `미연결 = cnt == 0`. 등재표 쪽 가공 단계가 빈 행도 종전에는 `if w and …` 로 건너뛰어 양쪽이 다 비면 통과했다 — `manifestLevelMissingSeq` 로 미달. `counts.json` 에 `processingLevel.undecidedSeq`·`usageUndecidedSeq`·`manifestLevelMissingSeq` 세 자리 신설.
- ⑩ 픽스처 `tests/preflight-red.sh` 에 계수 판정 4케이스(ⓠ) 추가 — `""`·`x` → 판정불가 ＋ 비영 · `0` → 통과 · `2` → 「미지정」 2건 ＋ 비영. 구현 전 red 확인(`count_verdict: command not found` · 4건 미달).
- ⑪ `blocked_add` 인자 수 — `lib.sh` 는 2인자(이름·사유)인데 `stage_verify` 가 2자리에서 3인자로 불러 **사유가 통째로 버려졌다**. `blocked_add verify "seq=… — <사유>"` 한 인자로 병합.
- ⑫ 픽스처가 `git fetch -q origin main` 을 회당 7회 실제로 냈다(공용 체크아웃 · 원격 접촉 ＋ ref 부작용). `$TMP/bin/git` 대역을 PATH 앞에 두어 `fetch` 만 비영으로 막고 나머지는 실물에 위임 — 기대 판정 무변(`✗ git` 은 그대로 서고 사유만 「origin/main 조회 실패」로 바뀐다). 실측 9.5s → 4.9s.
- ⑬ `--preflight-only` 두 케이스(ⓛ·ⓞ)에 `approval-record.json` 부재 단언 추가 — 검사만 한 회차가 승인 기록을 남기면 `report.py` 의 `approvalRecord` 가 서서 승인된 회차로 읽힌다.

## 3차 수정 — preflight `secrets` 참값화 ＋ 실행 차단 2건

- ⑭ `preflight.sh` `pf_secrets` — `printf "'%s/%s' " "$dir" "${SECRET_FILE_NAMES[@]}"` 이 서식 둘에 인자 10개를 **둘씩** 묶어 5개 엉뚱한 경로를 냈고, 9건 중 `master.url` 하나만 실제로 물었다. 나머지 8건은 구조적으로 「부재」라 **이 항목이 green 이 된 적이 없다**(DR-4 §5 ⑵). 고침 = `printf "'%s' " "${SECRET_FILE_NAMES[@]/#/$dir/}"`.
- ⑮ 이름 충돌 해소 — 원격 시크릿 경로의 출처를 `COLAB_RESEED_EC2_SECRETS_DIR`(기본 `/etc/colab`) 하나로 분리. `reseed.sh`·`stages.sh`·`preflight.sh` 가 운영자 기계의 `COLAB_DEV_SECRETS_DIR`(로컬 폴더)를 더는 읽지 않는다.
- ⑯ 계정 신원 기본값을 `infra/staging/provision-lab.sql` 의 `INSERT INTO d1_account`(＋ `d2_member_role` 역할)에서 **실행 때 읽는다**(레포에 사본 0). `d1_account` 의 `UNIQUE (lab_id, email)` 때문에 새 ULID 는 prelude ② 를 죽인다.
- ⑰ prelude ② 멱등 — `RESEED_ACCOUNT_ID` 가 ① 의 id 와 같으면 **건너뛴다**(2026-09-13 회차와 같은 순서 · `DR-2-run-2026-09-13.md` §5 ②). ② 를 돌리면 `d2_permission_switch` **4행**이 새로 서서 그 기준선과 갈린다(① 은 0행).
- ⑱ `--preflight-only` 가 마운트할 EC2 시크릿 폴더와 쓸 계정 신원을 각 한 줄로 찍는다(경로·신원만 · 비밀 0건).
- ⑲ 픽스처 `tests/preflight-secrets.sh` 신설 — GREEN(9건 0600 통과 · 물어본 경로 9건 대조) ＋ RED(1건 부재 · 1건 0644) ＋ 경로 출처·표기·기본값. ssh 대역이 실물 `stat` 처럼 **받은 경로 그대로** 답해 짝짓기 결함을 잡는다. `dev-reseed-selftest` 픽스처 **2 → 3**.

## 4차 수정 — 원격 전송로 ＋ 실패 순서 ＋ 리허설

- ⑳ `lib.sh` `b64_of`·`remote_assign` 신설 — 원격 셸로 가는 값은 **base64 한 길**로만 나른다. 종전 `export SQL='<값>'` 는 값이 작은따옴표를 품는 순간 바깥 따옴표가 닫혀 `reset` ①″ 가 `column "colab_platform" does not exist` 로 멈췄다(DR-4 §6). 이스케이프로 깁지 않는다 — 겹이 늘 때마다 다시 틀린다.
- ㉑ 같은 계열 전수 정리 — `psql_master_query`(전송부 `psql_master_run` 과 판정부로 분리) · `prelude` ②④ 계정 신원 다섯 · `prelude_login_credential` 의 `-e` 둘. 값은 원격 셸 변수에서만 꺼내고 SQL 리터럴은 원격 `sqlq()` 가 `''` 규칙까지 함께 지킨다. 정적 대조 = `stages.sh` 에 `='$…'` 한 겹 적재 **0건**.
- ㉒ `stage_reset` 실패 순서 — 읽기 전용(① 계수 · ①ᵃ 활성 트랜잭션 사전 관찰)을 **정지보다 앞**에 두고, 정지(①′)는 되돌릴 수 없는 걸음(② 스키마 DROP) 직전에만 내린다. 정지 뒤 실패하면 `reset_recover_apps` 가 같은 compose·env 로 앱을 **자동 재기동**하고 `recovery.jsonl` → `result.json` `recovery` ＋ 회차 기록 §4-1 에 남긴다. 종전에는 역연산이 없어 dev 가 내려간 채 남고 사람이 손으로 올렸다(DR-4 §7·§8 ⑶). **이탈** — ①″ 활성 트랜잭션 **판정**은 정지 **뒤**에 남겼다. 정지 전에 재면 앱 자신의 질의가 세어져 「정지가 들었는가」라는 뜻이 서지 않는다. 그 자리의 실패는 자동 재기동이 받는다.
- ㉓ 이중 기록 제거 — `psql_master_query`·`stage_s3` ① 의 `>> $STAGE_LOG` 재기록 삭제(`ssh_script` 가 이미 `tee` 한다). 오류 한 건이 로그에 한 번만 보인다.
- ㉔ `reseed.sh --rehearse` 신설 — 부수기 **전에** 원격 원시동작 10 을 실모드로 한 번씩 내 보고 기대와 대조한다(psql:master 따옴표 SQL · `ssh_script` 되받기 · compose `ps` · 마이그레이터 `alembic current` 두 체인 · 초기화 도구 `--phase s3-plan` 임시 폴더 **적용 없음** · `postgres:16-alpine` 소유자 URL `select 1` · `deploy_doctor` 1회 `doctor_summary_line` · 러너 `--phase report` · `agent-browser` 제목). 어긋나면 **이름을 대고** 비영. 바꾸는 단계 0건 · `--dry-run` 은 무접촉. 왜 = 실모드 정지가 세 회차 내리 「한 번도 실행된 적 없는 원격 줄」에서 났다.
- ㉕ 픽스처 `tests/remote-transport.sh` 신설 — ssh 대역이 받은 원격 스크립트를 **로컬 bash 로 실제 실행**해 원격 셸의 읽기를 재현한다. 구현 전 red 6건 확인(축자 `받은 것 [… datname in (colab_platform,colab_ai) …]` — 따옴표가 사라진 채 도착). `dev-reseed-selftest` 픽스처 **3 → 4**.
