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
