---
name: dev-reseed
description: dev 환경을 한 번에 초기화하고 정본 자료로 다시 채운다. 「데이터 전체 초기화하고 다시 셋팅해줘」·「dev 초기화하고 재셋팅」·「/dev-reseed」 처럼 **명시적으로 요구할 때만** 쓴다. 실행 대상은 `dev-package/tools/dev-reseed/reseed.sh` 하나이고 10단계(preflight → deploy → reset → bootstrap → up → s3 → prelude → seed → verify → report)를 순서대로 밟는다. 제외 — staging·prod 는 이 스킬이 다루지 않는다(매회 Ted GO 가 따로 필요하다). 배포만 하거나 게이트만 돌리는 일, dev 상태를 읽기만 하는 조회에는 발동하지 않는다.
---

# dev 재생성

## 무엇을 실행하는가

```bash
bash dev-package/tools/dev-reseed/reseed.sh --dry-run          # 명령만 찍고 아무것도 건드리지 않는다
bash dev-package/tools/dev-reseed/reseed.sh --preflight-only    # 검사만 — dev 를 읽기만 한다
bash dev-package/tools/dev-reseed/reseed.sh                     # 10단계 무인 실행
bash dev-package/tools/dev-reseed/reseed.sh --from s3           # 그 단계부터 재개
```

- 10단계 = `preflight → deploy → reset → bootstrap → up → s3 → prelude → seed → verify → report`.
- ⭑ **`preflight` 는 `--from` 과 무관하게 언제나 먼저 돈다.** 읽기 전용이고, **배포 대상 sha 를 해석하는
  자리가 거기 하나뿐**이다 — 건너뛰면 이미지 태그가 `…:dev-` 로, 승인 기록의 `targetSha` 가 빈 값으로 선다.
  `--from` 이 고르는 것은 **바꾸는 단계 여덟**(`deploy`~`verify`) 중 시작 지점 하나다.
- `--preflight-only` = preflight 만 돌고 바꾸는 단계는 **0건**. dev 를 읽기만 한다
  (ssh 조회 · `aws sts` · `docker ps` · 파일 · `agent-browser doctor` · 계획 생성 dry-run).
- dev 접속 값(`COLAB_DEV_SSH`·`COLAB_DEV_KEY_FILE`)이 없으면 **셸이 죽지 않는다** —
  `dev-sha`·`secrets`·`leftovers` 가 그 변수 이름을 대고 미달로 떨어지고, 접속이 필요 없는 항목은 그대로 잰다.
- 절차의 원본 = `dev-package/sessions/DR-2-runbook.md`(사람이 실제로 밟은 순서). 이 스크립트가 그 실행형이다.
- 값은 환경변수로 준다 — `COLAB_DEV_SSH` · `COLAB_DEV_KEY_FILE` · `COLAB_DEV_SECRETS_DIR` ·
  `COLAB_REF_ROOT` · `COLAB_DEV_URL` · `RESEED_ACCOUNT_ID`/`_EMAIL`/`_NAME`.
  비밀번호는 `--operator-password-file`(0600 · 10자 이상)로만 받는다. argv·로그·결과 JSON 에 값이 0건이다.

## 승인

- **dev 한정 상시 승인**이다 — `.claude/rules/deploy.md` 11번 증보 문단(2026-09-14 개정). 회차별 Ted GO 가 필요 없다.
- 조건 = 게이트 넷 충족(`--target dev`＋`--yes-reset-dev` · 버킷 정확 일치 · 두 DB URL 호스트에 `-dev` ·
  계획 키가 `uploads/`·`previews/` 안). 하나라도 어긋나면 아무것도 지우지 않고 비영 종료한다.
- `reset` 단계 직전에 `approval-record.json`(누가·언제·어느 sha·어느 게이트)이 실행 자리에 먼저 선다.
- ⛔ **에이전트가 몰아서 실행할 때는 `reset` 앞에 advisor 게이트 ③(go/no-go)을 붙인다.**
  상시 승인은 회차별 Ted GO 를 대체하지 advisor 판정을 대체하지 않는다(`R-DATA-CANON §7`).
- staging·prod 는 무변 — 매회 GO 이고 이 도구는 dev 식별자 밖에서 어느 조건으로도 돌지 않는다.

## 결과를 읽는 법

- `<실행 자리>/result.json` — 스키마 `colab-reseed-result/1`(`dev-package/tools/dev-reseed/result-schema.json`).
  - `stages[]` — 단계별 `status`(ok/failed/skipped) · `exitCode` · `durationSec` · `log`.
  - `preflight` — 통과·미달 항목 **이름**.
  - `counts` — 데이터셋 28 · 프로젝트 4 · 간선 18 · 가공 단계 불일치 · 「미지정」 · 프로젝트 미연결.
  - `previewJudgment[]` — 데이터셋 1건당 **성립 / 미성립 / 판정불가**와 소요 ms.
    ⭑ **「판정불가」는 값을 못 받은 것**(브라우저 무응답·선택자 변경)이고 통과로 세지 않는다 — `verify` 가 비영 종료한다.
  - `doctorSummary` — `deploy_doctor` 요약줄 축자(**한 번의 실행** 결과다. 부분 실행을 합치지 않는다).
  - `blocked[]` — 차단 항목의 이름과 사유.
  - `outcome` — `ok` · `failed` · `dry-run`. 실패면 `failedStage` 가 멈춘 자리다.
- 실행 자리 = `$COLAB_JOB_DIR/tmp/dev-reseed/<시각>` 또는 `dev-package/reports/dev-reseed-runs/<시각>`(추적 제외).
- 회차 기록 뼈대는 `dev-package/sessions/DR-4-run-<날짜＋시각>.md` 로 나온다(같은 날 두 번째 실행이 첫 기록을
  덮어쓰지 않게 시각까지 쓴다). **레포에 남는 조건 = 바꾸는 단계가 실제로 돌았다** — `--dry-run`·
  `--preflight-only`·preflight 에서 멈춘 회차는 실행 자리에만 남는다. 원장·대장·HANDOFF 갱신은 오케스트레이터가 한다.
- 검사기 = `bash gates/run.sh dev-reseed-selftest`(요약줄 파서 · preflight fail-closed · 계획 요약줄 ·
  `result.json` · `--from` · `--preflight-only` · `die` 복귀 · 미리보기 판정불가). dev 무접촉이다.

## 멈췄을 때

- 단계 하나가 비영 종료하면 그 자리에서 멈춘다. **자동 재시도는 없다** — 등록 확정과 삭제는 되돌릴 수 없다.
- 출력 마지막 줄이 멈춘 단계 이름과 로그 경로를 낸다. 원인을 본 뒤 `--from <그 단계>` 로 잇는다.
- `preflight` 미달은 이름으로 나온다. 이름을 고치기 전에 다음 단계로 넘어가지 않는다.
