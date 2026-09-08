# 레인 `rd-ship-gate` — WU-D2 ＋ WU-D3 (R-D-1 · 2026-09-08)

- 브랜치 `lane/wu-d2d3` · 기점 `origin/integration/r-d`. 계약 0 · 스키마 0 · 마이그레이션 0 · `frontend/` 0 · 제품 코드 = ops 점검기 1파일.
- ⚠ **기점 실측이 지시문 기대값과 다르다** — 지시문 기대 `2fecc19` · 실제 `7a97259`. `2fecc19` 는 `7a97259` 의 **조상**이고(`git merge-base --is-ancestor` exit 0), 사이 3커밋은 형제 레인 WU-D5(`eval/harness/**`·`R-D-2`·대장)로 **이 레인 파일과 겹침 0**(`git diff --name-only 2fecc19 7a97259` = 12파일 · `infra/`·`deploy_doctor`·`docs/DEPLOY` 0건). 지시문 §0 의 체크아웃 명령 자체가 이 HEAD 를 만든다. 정지 대신 진행하고 여기에 적는다.

## 1. 실측 (착수 시점 · 트리 `7a97259`)
| 무엇 | 값 |
|---|---|
| `$REPO` 유래 | `infra/dev/ship.sh:10` `REPO="$(cd "$HERE/../.." && pwd)"` — **이미 있다**(파생 불필요) |
| 반입 sha 형태 | `build.sh:13` `--short=12 HEAD` → `dist/colab-v2-dev.sha` → `ship.sh:14` 가 그대로 읽는다 → `candidate` 와 `CURRENT_SHA` 는 **같은 12자리 문자열** |
| 첫 ssh | `ship.sh:20` `mkdir` · `CURRENT_SHA` 기록은 `:23-25` 같은 ssh 안 |
| 원장 호출 | `infra/staging/deploy.sh` `ledger_append deploy` **3줄**(`:71` red 착수거부 · `:87` red abort · `:266` green) · `REPO` 는 `:19` |
| 드라이런 | `infra/staging/deploy.sh` 에 `DRY`·`dry-run` **0건** → ⓕ 는 실배포 없이 `bash -n` ＋ 3줄 전수 grep 으로 잰다 |
| doctor 인자 | `--repo` **없음** · `/opt/colab-v2` 상수 **0건** · `REPO_ROOT`(`deploy_doctor.py:52`) = `/repo` 마운트 |
| doctor docker run | `docs/DEPLOY.md:263-267` 마운트 = `/repo` ＋ 시크릿 2파일뿐 → `/opt/colab-v2` 가 컨테이너에서 **보이지 않았다**. 기존 시험 `tests/test_deploy_doctor.py`(358행) 헬퍼 정규식도 `[①-⑭]` 로 닫혀 있었다 |

## 2. 전 / 후 — `MAIN_SHA` 계약 축자 = `main=<12자리> candidate=<12자리> ancestor=yes|no|bypass` (한 줄)
| 파일 | 전 | 후 |
|---|---|---|
| `infra/dev/ship.sh` | 조상 검사 0 · `MAIN_SHA` 0 · 우회 경로 0 | `:14` 뒤 게이트 — 65(비조상 거절) · 78(origin 조회 실패) · `ancestor=yes\|bypass` 세 상태 · 같은 ssh 가 `/opt/colab-v2/MAIN_SHA` 기록 |
| `infra/dev/tag-release.sh` | 없음 | 신설 · `dev-YYYYMMDD-N`(N = 같은 날 태그 수＋1) · `prod-YYYYMMDD` · 대상 = 로컬 `dist/colab-v2-dev.sha` · **push 안 함**(명령만 출력) |
| `infra/dev/tests/ship-gate.sh` | 없음 | 신설 · 6 케이스 · 단언 26 |
| `infra/staging/deploy.sh` | 원장 비고에 브랜치 0 | `ledger_append deploy` **3줄 전부** 끝에 `브랜치=$(git -C "$REPO" branch --show-current)` |
| `infra/dev/README.md` | 손으로 재는 한 줄 | 그 줄 **무삭제** ＋ 게이트·우회·`MAIN_SHA`·태그 4줄 덧붙임 |
| `services/core-api/ops/deploy_doctor.py` | `MARKS` 14 · 항목 14 | `MARKS` 15 · `check_main_ancestry` · `--state-dir`(기본 `/state`) · 머리말·`description` 15 |
| `docs/DEPLOY.md` | `docker run` 마운트 3 · 14 항목 | `-v /opt/colab-v2:/state:ro` 추가 · 15 항목 · §6-1 ⑮ 항목표 행 ＋ 「파일 없음 = ✗」 경고 2줄 |
| `services/core-api/tests/test_deploy_doctor.py` | 358행 · 14 기준 | 456행 · 헬퍼 `[①-⑮]` · `len(statuses)==15` · ⑮ 시험 10건 |

## 3. WU-D3 조건 ⓐⓑⓒ — **셋 다 충족 · D3 폐기 없음**
- ⓐ `docs/DEPLOY.md:265` 에 `-v /opt/colab-v2:/state:ro` 추가(문서 변경 · 실행은 사람이 EC2 에서). 시험이 grep 으로 잡는다.
- ⓑ `--state-dir`(기본 `/state`) argparse 신설 · `Ctx.state_dir` 필드 · `check_main_ancestry` 가 그 밑의 두 파일을 읽는다.
- ⓒ 사유 6갈래 전부 ✗ 이고 문면이 다르다 — 「마운트 없음」(디렉터리 부재 ＋ 고치는 명령) · 「파일 없음」 · 「형식 불일치」 · 「후보 불일치」 · 「우회 반입」 · 「조상 아님」. **─(준비)로 내려앉는 경로 0**(spec 우려 4 ⓐ).

## 4. RED → GREEN
- `infra/dev/tests/ship-gate.sh` — **RED 선실측** 「요약 — 통과 7 · 실패 19」 exit 1. 인용: `✗ ⓐ 비조상 · exit — 기대 65 · 실제 0` · `✗ ⓐ 비조상 · ssh·scp 호출 수 — 기대 0 · 실제 4`(현 `ship.sh` 가 비조상 sha 로 EC2 에 4회 붙는다 = 창 9 의 결함) · `✗ ⓒ origin 부재 · exit — 기대 78 · 실제 0`. → **GREEN 26/26 · 6 케이스 · exit 0**.
- `services/core-api/tests/test_deploy_doctor.py` — **RED 선실측** `11 failed, 17 passed`. 인용: `FAILED …15번째_항목이_통과다 - StopIteration`(⑮ 줄 자체가 없다) · `FAILED …docker_run_명령이_state_를_읽기_전용으로_마운트한다 - AssertionError: assert '-v /opt/colab-v2:/state:ro' in …`. → **GREEN 28/28**(신설 10 ＋ 기존 갱신 1 ＋ 기존 17). **기존 14항목 회귀 0**.
- 생산자·소비자 한 계약 오라클 = `test_ship_sh_가_적는_형식을_점검기가_그대로_읽는다` — `ship.sh` 의 `printf` 형식을 정규식으로 뽑아 그 문자열로 doctor 를 돌린다. 형식이 갈리면 운영이 아니라 여기서 red 가 난다. 자기 결함 1건도 RED 가 잡았다 — `tag-release.sh` 가 `grep -c .`·`&&`-`exit` 로 `set -e` 에 걸려 첫 태그에서 exit 1(→ `wc -l` ＋ `if`).

## 5. 수용 기준 대조 (라운드 §2 WU-D2 · §5)
| 기준 | 판정 |
|---|---|
| 비조상 → exit 65 · 가짜 ssh 호출 0 | ✅ `exit = 65` · `ssh·scp 호출 수 = 0` |
| 조상 → 통과 ＋ `MAIN_SHA` ＋ `ancestor=yes` | ✅ ssh argv 에 `/opt/colab-v2/MAIN_SHA` ＋ ` <main> <candidate> yes` |
| `origin` 없음 → exit 78 · 우회 선언 → 통과 ＋ `ancestor=bypass` | ✅ 둘 다 · 78 은 ssh 호출 0 동반 |
| 같은 날 `tag-release.sh dev` 2회 → `-1`·`-2` | ✅ ＋ 원격 태그 0건 · dist 부재 exit 65 |
| 원장 행 `브랜치=` | ✅ 3/3 줄 · 값은 `branch --show-current` (드라이런 부재라 **정적 단언**) |
| doctor 시험 5 ＋ 회귀 0 · `len(MARKS)==15` · 부재 = ✗ | ✅ (시험 10건으로 넓혔다) |
| 요약줄 `항목 15 — ✓ N · ✗ N · ─ N` | ✅ 실행 실측 `항목 15 — ✓ 1 · ✗ 0 · ─ 14` |

## 6. 하지 않은 것
- 실배포 0 — dev·staging 어디에도 붙지 않았다. EC2 ssh 0회(시험의 ssh 는 `PATH` 앞의 가짜 스크립트). push 0 · 병합 0 · 실 저장소 태그 생성 0(시험 태그는 임시 저장소 안).
- 무접촉 — `infra/staging/rollback.sh` · `contracts/` · `db/` · `frontend/` · 대장 `work-items.yaml`(읽기만) · `PLAN-SoT §9` · `03-HANDOFF.md`. 〈N〉 하드코딩 0.

## 7. intent 대조 (`dev-package/intent/2026-09-08-r-d.md` 규칙 1·2·5·6)
- 규칙 1(`main` 유일 배포 원천 · `ship.sh` 거절) — **충족**. ⚠ 축자에는 `up.sh`·`deploy.sh --target dev` 도 검사한다고 적혀 있으나, **설계트리 Q2 가 「`ship.sh` 한 곳 ＋ doctor 사후」로 좁혔고**(`docs/BRANCHING.md:20` 동일) 그 확정을 따랐다. 규칙 6 원문 대비 **의도된 미달 1건**이고 판정 근거가 있다.
- 규칙 2(staging 예외 ＋ 원장에 브랜치명) — **충족**. red 2줄까지 붙여 3/3.
- 규칙 5(`00NN_merge` ＋ 두 순서 drift 오라클) — **이 레인 밖**. 마이그레이션 0 이라 대상 없음.
- 규칙 6(태그 `dev-YYYYMMDD-N` · `prod-YYYYMMDD`) — **충족**. 〈N〉 원장 행이 태그를 가리키는 부분은 오케스트레이터 몫.
- **미달** — 위 규칙 1 의 `up.sh` 이중 검사 1건(확정으로 제외). 그 밖 0건.
- **초과** — ⑴ `tag-release.sh` 에 `origin` fetch 실패 시 exit 78 · 중복 태그 exit 65(요구에 없던 거절 2갈래) ⑵ doctor 사유를 요구 6갈래 그대로 두되 「조상 아님」을 별도 문면으로 분리 ⑶ 시험을 요구 5→10건, ship-gate 5→6 케이스 ⑷ 기존 시험 헬퍼 정규식 `[①-⑭]`→`[①-⑮]` 갱신(항목 15 를 세지 못해 필수) ⑸ `docs/DEPLOY.md` 경고 2줄. 전부 같은 WU 안이고 계약·제품 코드를 넓히지 않는다.

## 8. 셀 수 없었던 것
- **실제 EC2 동작 `[미상]`** — 원격에서 `printf` 가 옳게 실행되는지는 실배포에서만 확인된다. 여기서 잰 것은 **로컬이 만든 argv** 까지다.
- **`deploy_doctor` 15/15 한 번에 `[미상]`** — 완료 판정(`CLAUDE.md §0`)의 계수가 14→15 로 바뀌었고 판정은 dev 배포 창에서만 난다. ⑮ 는 마운트가 실제로 걸린 뒤라야 ✓ 다.
- 원장 `브랜치=` 의 **실행 시 값 `[미상]`** — 드라이런 부재로 정적 단언까지다(값 확인은 다음 staging 회차).

## 9. 후속 항목
- `docs/BRANCHING.md:76` 의 「현재 트리에는 반입 게이트도 우회 경로도 없다 · `deploy_doctor` 도 14항목이다」가 **이 두 커밋으로 거짓이 된다.** 그 파일은 WU-D1 소관이라 이 레인에서 고치지 않았다 — 병합 시 오케스트레이터가 한 줄 정정할 자리.
- `infra/dev/up.sh` 에는 조상 검사가 없다(설계트리 Q2 로 의도됨). 어느 검사에도 걸리지 않는 상태이므로 기록만 남긴다.
