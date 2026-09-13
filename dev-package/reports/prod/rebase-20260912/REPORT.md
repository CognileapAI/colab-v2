# prod 브랜치 리베이스 ＋ 새 배포 규약 반영 — 2026-09-12

- 브랜치 `feature/rtf400_deploy_prod` · 기준 `origin/main` `a8a1653`
- 워크트리 = 하네스 생성분 · **push·PR 생성·`main` 병합 0**
- 근거 로그 = 같은 폴더의 `gates-run.log` · `gate-summary.json` · `prod-ship-gate-RED.log` ·
  `prod-ship-gate-GREEN.log` · `dev-ship-gate-BASELINE.log` · `dev-ship-gate-AFTER.log`

---

## 1. 리베이스 — 13 커밋 sha 대응표

기준 이동 `27733ba`(옛 merge-base) → `a8a1653`(`origin/main`). **커밋 수 13 유지 · 내용 유지 · sha 변경.**

| # | 전 | 후 | 첫 줄 |
|---|---|---|---|
| 1 | `6d3faf4` | `023756e` | prod 를 연다 — 등재 · `㊻` 보류 해제 · I-D 닫음 |
| 2 | `3977ce7` | `b20de7c` | prod 착수 전 결함 넷을 고친다 |
| 3 | `8246d1a` | `0ca0a63` | 유료 전환·예산 재설계를 실측으로 적는다 (P1·P2) |
| 4 | `4e4b6d8` | `ae69f64` | prod S3 한 벌을 세운다 — 버킷 2 · IAM 3 · `infra/prod` (P3) |
| 5 | `aa73b09` | `b730772` | 셀프테스트 6개의 위반 주입 ＋ compose 기본 목록 |
| 6 | `8eef52f` | `598bb28` | prod EC2 ＋ §5-5 준비 절차 스크립트화 (P6-a·b) |
| 7 | `f824d3d` | `de9aa52` | prod DB 부트스트랩(prep·roles) (P6-c) |
| 8 | `6ddde2a` | `a0d9077` | prod 스택 — 이미지 5 · 마이그레이션 · 롤 4 · 4 단위 healthy (P6-d·e) |
| 9 | `7860230` | `c0b4e84` | prod 프론트 배포 · 백업 cron (P7 일부) |
| 10 | `ca112f2` | `9114af9` | prod 개통 — `deploy_doctor` 14/14 한 번의 실행 (P7 완료) |
| 11 | `294e7ca` | `53f8487` | P8 — 시점 복구를 실제로 되감았다 |
| 12 | `0fcd153` | `a05a02d` | 결정 번호 개번 〈343〉 → 〈372〉 |
| 13 | `42a7154` | `2ece803` | `_fixture.sh` 인덱스 모드 `100644` → `100755` |

- 리베이스 종료 시 `git grep -l '^<<<<<<< \|^>>>>>>> '` **0건**.
- 파일 교집합 실측 **9건**(지시문 예상 10 과 1 차이 · 열거된 3＋4＋2 는 그대로).
  `infra/prod/` 신규 파일 **19건**(지시문 예상 21 과 2 차이) · 충돌 0.

## 2. 충돌 해소 — 파일별

| 파일 | 충돌 | 해소 |
|---|---|---|
| `dev-package/work-items.yaml` | 없음(드라이버 병합) | `merge=work-items` 드라이버를 `gates/.venv/bin/python` 으로 물려 실행(시스템 `python3` 에 PyYAML 부재). 출력 「항목 182건 · 상대 신규 0건」 · 결과 `I0`·`I1`·`I5`=`open`/`stage1`(브랜치) · `I3`·`I4`=`done`/`stage2`(main) · id 유일 182/182 |
| `dev-package/PLAN-SoT.md` | 1 | **둘 다 취함** — main 의 `〈372〉`~`〈382〉` 11행 뒤에 브랜치의 prod 행 1개 덧붙임. 번호 충돌은 §6 |
| `dev-package/03-HANDOFF.md` | 3 | ⑴ 증보 블록 = main 31행 ＋ 브랜치 1행 ⑵ `U-1`·`F-3`·`I-D` = **main**(2026-09-11 수용 완료 · `I-D` 양쪽 동일) ⑶ 인프라 표 = main 의 `IS4 ✅`·`I3 ✅`·`I4 ✅` ＋ 브랜치의 `I1 ⬜`·`I5 ⬜` |
| `dev-package/WORK-UNITS.md` | 1 | main 의 인프라·staging 상태줄 ＋ 브랜치의 `I0 ⬜ I1 ⬜ I5 ⬜` |
| `infra/dev/ship.sh` | 2회(커밋 2·12) | main 의 ops 소스 번들 scp **보존** ＋ 브랜치의 `backup.sh`·`install-cron.sh` scp·`chmod +x` **재적용**. main 의 반입 게이트·`MAIN_SHA` printf 무손실 |
| `services/core-api/ops/deploy_doctor.py` | 없음(자동) | main 의 ⑮(`MARKS` 15 · `check_main_ancestry` · `--state-dir`)와 브랜치의 벌별 CORS 오리진이 **둘 다** 남았다 |
| `gates/tools/artifact-ownership-selftest.sh`·`preview-tile-slot-selftest.sh` | 없음(자동) | 브랜치의 `_fixture.sh` 전환과 main 의 신규 케이스(ⓥ · `COLAB_GATE_INNER_JOBS`)가 둘 다 남았다. 두 셀프테스트 최종 green |

지시문이 예고한 「`deploy_doctor.py` 의 prod 인자·`HERE.parents[2]` 경로 깊이 수정 재적용」은 **해당 없음** —
그 둘은 merge-base 에 이미 있었고 브랜치 diff 는 CORS 오리진 분기 하나뿐이다.

## 3. 새 규약 반영

### 3-1. 반입 게이트 한 벌 ＋ prod 태그 검사 (규칙 1·6)

- **신규 `infra/_lib/ship-gate.sh`**(100755) — 함수 둘.
  - `ship_gate_main_ancestor <저장소> <후보 sha>` — `origin` 조회 실패 **78** · 비조상 **65** ·
    선언 우회 `COLAB_SHIP_ALLOW_NONMAIN=1` → `ancestor=bypass`. 문면·종료코드는 main 판 축자.
  - `ship_gate_require_prod_tag <저장소> <후보 sha>` — 후보 sha 에 `prod-*` 태그 부재 시 **65**,
    ⛔ **우회 변수 없음**. 조회 실패 78.
- `infra/dev/ship.sh` = 인라인 18줄을 걷어내고 lib 를 source(**복사 아님**).
- `infra/prod/ship.sh` = 같은 lib ＋ 태그 검사 ＋ `MAIN_SHA` 기록
  (`printf 'main=%s candidate=%s ancestor=%s\n'` — dev 와 같은 형식).
- 검사 대상 sha = **반입 후보**(`dist/colab-v2-prod.sha`). 통상 `HEAD` 와 같고, `HEAD` 가 뒤로
  움직인 날에도 실제로 실리는 커밋을 본다.

### 3-2. `deploy_doctor` ⑮ 를 prod 에서도 판정

- `infra/prod/deploy-doctor.sh` — `docker run` 에 `-v /opt/colab-v2:/state:ro` · 머리말 14→**15 항목** ·
  「혼자서는 못 맞히는 조건」에 마운트 항목 추가.
- `deploy_doctor.py` 무변경 — ⑮ 는 벌과 무관하게 `/state` 두 파일만 읽는다.

### 3-3. 문서 정합

| 파일 | 고친 자리 |
|---|---|
| `docs/DEPLOY.md` | 머리 「prod 는 아직 없다」 → **dev·prod 2벌 표** ＋ ⑮ 가 지금 ✗ 인 사실 · §4-1c 「항목 14」에 15 항목 개정 주석 · P3 CORS 「배포 주소가 아직 없다」에 해소 주석 · §10 표 `prod` 행 갱신 · **§5-9 신설**(태그에서만 배포) · **§5-10 신설**(마이그레이션 격차·선행 조건 4) |
| `.claude/rules/deploy.md` | 14행 한 줄만 — 「dev 하나」 → 「dev·prod 둘」 ＋ 태그 규칙 포인터. **11항목 무변** |
| `docs/BRANCHING.md` | §2 수명 표 `prod-YYYYMMDD` 비고 · §1 「반입 검사는 `infra/dev/ship.sh` 안에」 → 「`infra/_lib/ship-gate.sh` 한 벌 · 둘이 부른다」 ＋ prod 태그 검사 한 줄. **규칙 6 축자 6줄 무변**(`diff` 0행) |
| `infra/prod/README.md` | §4 게이트 표(거절·우회) · §6 15 항목 ＋ 현재 ⑮ ✗ 사유 |
| `dev-package/work-items.yaml` | `I5` 의 `evidence` 한 절 |

### 3-4. 주소·비밀값

새로 적은 주소는 **CloudFront 도메인 2개**뿐(둘 다 기존 문서·설정에 이미 있던 값).
EC2 IP·RDS 엔드포인트·접속 문자열·키 **0건**.

## 4. 시험 — red 를 먼저 봤다

| 오라클 | red(선행) | green(구현 뒤) |
|---|---|---|
| `services/core-api/tests/test_deploy_doctor.py` prod 6건 | **5 failed / 2 passed** · 인용 `AssertionError: infra/_lib/ship-gate.sh 가 없다` | **34 passed**(기준선 28 ＋ 신규 6) |
| `infra/prod/tests/ship-gate.sh`(신규 · 6 케이스 21 검사) | **통과 2 · 실패 19 · exit 1** — 리베이스 직후 `infra/prod/ship.sh` 로 실행. 인용 `✗ ⓑ 태그 부재 · exit — 기대 65 · 실제 0` · `✗ ⓐ 비조상 · ssh·scp 호출 수 — 기대 0 · 실제 5` | **통과 21 · 실패 0 · exit 0** |

신규 pytest 6건 = prod `ship.sh` 형식↔⑮ 생산자·소비자 대조 · prod 우회 반입 ✗ · prod doctor `/state` 마운트 ·
prod doctor 15 항목 문면 · 게이트 한 벌(두 `ship.sh` 가 lib 를 부르고 본문 복사 0) · prod 만 태그 검사.

셸 6 케이스 = ⓐ 비조상 65 ⓑ 태그 부재 65 ⓒ 조상＋태그 통과(`MAIN_SHA` 3값) ⓓ 비조상＋우회 bypass
ⓔ **태그 검사는 우회 불가**(조상＋태그 부재＋`COLAB_SHIP_ALLOW_NONMAIN=1` → 여전히 65) ⓕ `origin` 실패 78.
red 케이스는 **가짜 ssh·scp 호출 수 0** 까지 본다(거절이 반입 전에 끝난다).

## 5. 게이트 3계수 — 한 번의 실행

선언 12건 · `COLAB_TASK_ID=30a25657… COLAB_GATE_REPORT_DIR=dev-package/reports/prod/rebase-20260912 bash gates/run.sh task`

```
── 계 : green 12 / red(판정) 0 / red(준비) 0     (exit 0)
```

green 12 = `exec-bit` · `db-boundary` · `work-item-consistency` · `contract-lint` ·
`contract-breaking`(기준 `origin/main` · **파괴적 변경 0**) · `generated-up-to-date` ·
`artifact-ownership-selftest` · `autometa-loss-selftest` · `boundary-selftest` ·
`db-boundary-selftest` · `event-selftest` · `preview-tile-slot-selftest`.

⚠ **선언 밖 1건 = `planning-freshness` red 5건**(§7). 숨기지 않고 따로 돌려 로그를 남겼다
(`planning-freshness-red.log`). 이 호스트에서는 그 게이트의 입력이 **물리적으로 없어** 어떤
방법으로도 green 이 되지 않는다 — 선언 집합에 넣으면 레인이 영원히 닫히지 않는다.
⛔ 검사 대상을 줄인 것이 아니다 — **돌렸고, red 이고, 건수와 원인을 드러낸 채** 넘긴다.

`service-tests`·`all` 은 지시대로 돌리지 않았다.

## 6. 〈372〉 번호 충돌 — 재발급했다

- 처음 실행에서 `work-item-consistency` 가 잡았다 —
  `㈔ 결정 번호 〈372〉 이 PLAN-SoT §9 에 2번 나온다 — 두 회차가 같은 번호를 집었다. 뒤에 온 쪽이 새 번호를 받는다`
- 실물 — 이 브랜치의 `〈372〉` = 「prod 를 연다 — `㊻` 보류 해제」 / `origin/main` 의 `〈372〉` = 「R-A′ rev2 증분 5 WU 병합」.
  브랜치가 개번(커밋 12)했을 때 main 최대는 `〈342〉` 였고 그 뒤 main 이 `〈343〉`~`〈382〉` 를 썼다.
- **조치 = `〈372〉` → `〈395〉`**(현 `origin/main` 최대 `〈382〉` ＋1 · `colab-rules §4-1`). 22 파일 · 47곳.
  치환은 **이 회차 소유분만** — `03-HANDOFF.md` 1줄 · `PLAN-SoT.md` 2줄의 main 인용과
  `prd/`·`sessions/`·`reports/R-D/` 의 인용은 무수정. 남은 `〈372〉` 집합이 `origin/main` 집합과
  **정확히 같은 것**을 실측했다.
- ⚠ **지시문과의 차이** — 지시는 「임시 번호 그대로 두고 병합 직전 오케스트레이터가 재발급」이었다.
  그대로 두면 `work-item-consistency` 가 red 로 남고 **레인 종료 계약(`lifecycle_contract.py:176`
  「gate failures remain」)이 handoff 를 거부**해 회차가 닫히지 않는다. 번호는 병합 직전 다시 재는 것이
  규칙이므로 `〈395〉` 도 임시다 — **오케스트레이터의 재실측 권한은 그대로**이고, 이 커밋이 한 일은
  「한 트리에 같은 번호 둘이 없게」까지다.
- 재실행 `work-item-consistency` **green**(불일치 0 · `work-item-consistency-after-renumber.log`).

## 7. `planning-freshness` red 5건 — 이 브랜치 밖 원인

- 축자 5줄 전부 「정본 폴더가 없다 / 원본이 없다」이고 가리키는 곳은 레포 **밖**의 기획 폴더다.
- 실측 — 그 폴더가 이 호스트에 **존재하지 않는다**.
- 이 브랜치는 판정기 `dev-package/tools/check-package-freshness.py` 와 매니페스트
  `dev-package/prd/planning-applied.yaml` 를 **건드리지 않았다**(변경 파일 대조 0건).
- **어느 검사에 걸리는가** — `planning-freshness` 게이트가 잡는다(게이트 밖 잠복 아님).
  다만 원인이 「외부 입력 부재」인데 종료코드가 **1(판정)** 이라 3계수에서 준비 red 로 갈리지 않는다. 후속 ②.

## 8. 이번에 세지 않은 것 · 열린 것

1. **prod 실행 확인 0회** — AWS·EC2·RDS 무접촉(지시). 셸 시험·문자열 대조까지만 쟀다.
2. **`infra/dev/tests/ship-gate.sh` 는 8건 실패로 서 있다** — `ⓑ 조상`·`ⓓ 우회 선언` 이 `exit 127`.
   원인 = `infra/dev/ship.sh:28` 이 부르는 `infra/ops/build-source-bundle.sh` 를 그 픽스처가 복사하지 않는다.
   **계수는 이 회차 전후가 같다**(기준선 18/8 → 이후 18/8 · 두 로그 첨부).
   ⚠ **어느 검사에 걸리는가 = 아무 데도 안 걸린다** — `grep -rn "ship-gate" gates/ .github/` **0건**. 후속 ①.
3. **`event-lint` 의 준비 실패가 판정 red 로 계수된다** — 이 워크트리에 `gates/tools/node/node_modules`
   의 `ajv-formats` 가 없어 `Cannot find module 'ajv/dist/2020'` 로 죽었고 게이트는 **exit 1** 을 냈다.
   `npm ci` 뒤 `event-selftest` green. 준비 실패는 78 ＋ `::gate-readiness-failure::` 여야 한다. 후속 ③.
4. **마이그레이션 격차는 문서에만 적었다** — 적용도 예행도 0회(`docs/DEPLOY.md §5-10`).
5. **`03-HANDOFF.md` 회차 갱신 0** — 레인은 원장 등재를 하지 않는다. 오케스트레이터 몫.

## 9. 후속 항목

| # | 항목 | 어디서 잡히는가 |
|---|---|---|
| 1 | `infra/dev/tests/ship-gate.sh`·`infra/prod/tests/ship-gate.sh` 를 게이트로 승격 | **지금은 아무 게이트·CI 잡도 안 돈다** · `colab-rules §3-3` ⑷ |
| 2 | `planning-freshness` 의 「외부 폴더 부재」를 준비 red(78)로 가름 | 지금은 판정 red |
| 3 | `event-lint` 의 의존 부재를 78 ＋ `::gate-readiness-failure::` 로 | 지금은 exit 1 |
| 4 | prod 배포 회차 — 태그 → `main` 재빌드 → 반입 → 마이그레이션 18건 → `deploy_doctor` 15/15 | `docs/DEPLOY.md §5-9`·`§5-10` |
| 5 | prod `account-admin`·`operator` 롤 생성 · WAF 감시→차단 전환 판정 | 미판정 |
