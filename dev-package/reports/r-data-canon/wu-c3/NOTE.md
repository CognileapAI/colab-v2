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
