# I3-BUILD — 배포 자동화 제작 회차 기록 (2026-08-28)

> 이 문서는 **제작 회차의 기록**이다. 값과 근거의 정본은 `PLAN-SoT §9`, 작업 정본은 `sessions/I3.md`.
> **이 회차에 staging 실배포는 하지 않았다.** 파이프라인을 세우고 멈췄다 — 실행은 Ted 의 별도 승인 사항이다.

---

## 0. 진입 상태

착수 전 판정 7건은 **전건 판정된 채로 들어왔다**(`PLAN-SoT §9 〈168〉-㉮~㉴`). 이 회차는 그 값을
**그대로 집행**했고 다시 판단하지 않았다.

| 항목 | 값 | 이 회차의 집행 자리 |
|---|---|---|
| 배포 실패 알림 (`㉮`) | 표식 파일 유지 · 알림 통로는 `I4` 로 이관 | `pipeline/lib.sh` `mark_failed` · `pipeline/watch.sh` |
| 감시 (`㉯`) | `cron` · 5분 | `pipeline/schedule.crontab` · `install-schedule.sh` |
| 이미지 (`㉰`) | 보관소 안 씀 · 최근 3개 보존 | `pipeline/lib.sh` `image_prune` |
| 배포 장부 (`㉱`) | `IS3 §10` 표식 3종과 같은 모양 · 릴리스 30건 | `release-ledger.tsv` · `DEPLOY-FAILED.txt` · `LAST-SUCCESS.txt` |
| 되돌림 (`㉲`) | **스키마는 되돌리지 않는다 — 전진 전용** | `rollback.sh` (이미지만 교체 · pgdata·스키마 무접촉) |
| 실패 시 (`㉳`) | **자동 되돌림 없음(기본 off)** · 중단 ＋ 표식 ＋ 사람 호출 | `deploy.sh` `abort()` · `--auto-rollback` 은 명시 옵션 |
| 승인 기록 (`㉴`) | 배포 장부와 같은 파일 · 승인자 이름 한 낱말 | `pipeline/approval/approve.sh` |

⚠ **지시가 가리킨 `sessions/I3-SEVEN.md` 는 실물이 없다.** 값은 `sessions/I3.md §3` 의 판정 블록과
지시문 본문에서 취했고, 둘은 서로 일치했다. 파일을 새로 만들지 않았다.

⚠ **`work-items.yaml` 의 `I3` 는 `status: conflict` 다.** `completion_def` 는 있다
(「파이프라인 1회 완주 · 정본 = `WORK-UNITS §10.2-b`」) — 미작성이 아니므로 멈추지 않았다.
대장 갱신은 이 레인의 몫이 아니다(오케스트레이터).

---

## 1. 만든 것

| 자리 | 내용 |
|---|---|
| `infra/staging/pipeline/lib.sh` | 릴리스 원장 · 표식 3종 · 이미지 보존 · 단일 실행 잠금 · 판정 어휘(`verdict`) |
| `infra/staging/pipeline/run-pipeline.sh` | 한 바퀴 — `git fetch` → fast-forward → `deploy.sh` |
| `infra/staging/pipeline/watch.sh` | 크론 껍데기 (`backup/run-scheduled.sh` 와 같은 모양) |
| `infra/staging/pipeline/schedule.crontab` · `install-schedule.sh` | `*/5` 크론 선언본과 설치기 |
| `infra/staging/pipeline/approval/target.sh` | 타깃 판정 — `prod` 는 선언만, 호출 시 `㊻` 인용 후 즉시 거부 |
| `infra/staging/pipeline/approval/approve.sh` | 승인 기록 (원장과 같은 파일) |
| `infra/staging/pipeline/selftest.sh` | 원장·롤백 대상·표식·거부 경로 fail-closed 증명 14건 |
| `infra/staging/verify/verify-deploy.sh` | **판정기** — 헬스 6종 + 본문 대조 + 컨테이너 8개 + `0.0.0.0` 0건 |
| `infra/staging/verify/verify-chains.sh` | 두 체인 head (읽기 전용 카탈로그 조회) |
| `infra/staging/verify/selftest.sh` | 판정기 red fixture 15건 |
| `infra/staging/deploy.sh` | 개정 — DR-4·DR-5·DR-6 본체 |
| `infra/staging/rollback.sh` | 개정 — 「직전 green 릴리스」로 간다 |
| `infra/staging/compose.i2.yml` | 이미지 태그를 `${COLAB_RELEASE_TAG:?}` 로 (기본값 없음) |
| `infra/staging/README.md` | 자동화 이후의 절차·상태 자리·한계 |
| `.github/workflows/ci.yml` | **노드 의존 설치 단계** 2개 잡에 |

---

## 2. DR-4 · DR-5 · DR-6 을 어떻게 닫았나

**세 얼굴의 뿌리는 하나였다 — 도구가 검증한 것보다 많이 단언했다.**

### DR-4 무엇을 굽는가
- 종전: 주석은 「커밋의 산출」, 코드는 **워킹트리**를 구웠다.
- 지금: **주장하지 않고 강제한다.** `git status --porcelain` 이 비지 않으면 배포하지 않는다.
  태그 = 커밋 SHA(`--short=12`). 굽겠다면 `--allow-dirty` 로 명시하고, 그때 태그가 `<sha>-dirty` 가
  되며 변경 건수가 원장에 남는다.
- **주석 정정** — `deploy.sh` 의 「이미지 안에서 빌드하니 커밋의 산출」 문장을 지우고, 그 자리에
  실제 동작(트리 청결 강제)을 적었다. **동작과 주석을 같은 변경 안에서 고쳤다**(`I3 §0-2`·`§5-13`).

### DR-5 무엇으로 돌아가는가
- 종전: 태그 `:i2` 고정 → 직전 이미지가 이름 없는 dangling.
- 지금: ⑴ **빌드 전에** `:prev` 로 보존하고 ⑵ 빌드 후 **보존본과 신규본의 이미지 ID 를 대조해 출력**한다
  ⑶ 롤백은 릴리스 원장의 「직전 green」으로 간다 ⑷ 이미지 보존 3개.
- **원장 한 줄이 곧 롤백 가능을 뜻하지 않는다** — `ledger_rollback_target` 은 이미지 실물 6종이
  전부 있는 태그만 짚는다. 없으면 **조용히 자리표시로 가지 않고 실패한다**(selftest P4·P5).

### DR-6 무엇이 성공했는가
- 종전: `dc ps` 로 끝. 앱 5종이 `starting` 인 채 `exit 0`.
- 지금: 종료 코드의 근거가 **헬스 6종 + 본문 대조 + 컨테이너 8개 healthy + `0.0.0.0` 0건 + 두 체인 head** 다.
  대기 타임아웃은 **red**. 200 만으로는 자리표시와 구분되지 않으므로 **각 단위가 자기 `unit` 이름으로
  대답해야** 통과한다.
- **주석 정정** — 「앱보다 postgres 가 먼저 healthy 여야 한다」를 「대기는 postgres 와 앱 5종 양쪽에
  걸고, 타임아웃은 통과가 아니라 red 다」로 고쳤다.

---

## 3. green-by-skip 자기점검 — 무엇을 찾았고 어떻게 고쳤나

**세 상태로 만들었다 — 선언되면 검사한다 / 명시적으로 면제하면 건수를 드러낸 채 넘어간다 /
아무 말도 없으면 실패한다.**

| # | 발견한 모양 | 어디 | 고친 방식 |
|---|---|---|---|
| 1 | **타깃 기본값 `staging`** — 어디에 배포하는지 안 밝혀도 돌 뻔했다 | `deploy.sh` · `run-pipeline.sh` | 미지정은 `exit 64` 거부. 기본값 없음 |
| 2 | **롤백 대상 기본값이 자리표시** — 종전 `rollback.sh` 의 실제 결함. N-1 이 아니라 0 으로 간다 | `rollback.sh` | 세 모드를 **명시**해야 돈다. 미지정은 거부 |
| 3 | **`compose.i2.yml` 태그 기본값** — `${VAR:-i2}` 로 뒀으면 DR-5 가 그대로 살아난다 | `compose.i2.yml` | `${COLAB_RELEASE_TAG:?}` — 기본값 없음. 실측으로 거부 확인 |
| 4 | **노출 검사 대상 0건이 통과** — 스택이 안 떠 있으면 `0.0.0.0` 이 0건이라 green 이 난다 | `verify-deploy.sh` | 대상 0건은 **red**. `verdict()` 가 `CHECKED=0` 을 red 로 낸다 |
| 5 | **체인 version 표가 비어도 통과** — 「표가 비었다」와 「올라갔다」가 같은 자리로 떨어진다 | `verify-chains.sh` | 빈 결과 = red. 조회 실패도 red |
| 6 | **요약줄이 SKIP 건수를 숨김** | `pipeline/lib.sh` `verdict()` | `backup/lib.sh` 의 `〈170〉-㉮` 규약을 그대로 가져왔다. 요약줄은 한 곳에서만 나오고 건수를 숨길 수 없다 |
| 7 | **배포 전 백업 면제가 조용함** | `deploy.sh` | `--skip-backup` 은 명시일 때만, 그리고 **원장에 `배포전백업SKIP(2건)` 로 남는다** |
| 8 | **`image_prune` 이 별칭까지 지움** — 정리하는 코드가 되돌릴 손잡이를 걷어 간다 | `pipeline/lib.sh` | `:prev`·`:i2` 는 보존 개수에 넣지도 지우지도 않는다 |
| 9 | **잠금 자기 교착** — `run-pipeline` → `deploy` 가 같은 잠금을 두 번 잡아 자기에게 막힌다 | `pipeline/lib.sh` | 흐름 하나당 잠금 하나(`COLAB_PIPELINE_LOCK_HELD`) |

**형제 찾기.** `infra/staging` · `gates` 전역에서 관대한 기본값(`${VAR:-1}` 계열)을 훑었다 —
`backup/` · `restore/` 쪽은 `〈170〉`·`〈171〉` 회차에 이미 세 상태로 정리돼 있었고 남은 것이 없었다.
남은 형제는 **CI 쪽 하나**였다(아래 §4).

**⚠ 남은 비대칭 1건(고치지 않음).** 노드 도구를 쓰는 게이트 셋 중 `contract-lint`·`event-lint` 는
부재를 보고 스스로 `npm ci` 를 하는데 **`generated-up-to-date` 는 하지 않는다.** 도구 부재를 red 로
내는 것 자체는 옳은 동작이라 **게이트를 건드리지 않았다.** 설치 단계를 CI 에 세우는 쪽으로 닫았다.
이 비대칭은 기록만 남긴다 — 게이트 소유 레인의 판단 자리다.

---

## 4. CI 의 노드 의존 설치 — 무엇을 어디에 세웠나

**실측(이 회차, 손대기 전).** `.github/workflows/ci.yml` 전문에 `npm`·`yarn`·`pnpm` **0건**,
`node_modules` 는 **캐시 복원만 4곳**, `frontend/` 는 캐시 대상에도 없었다.
그리고 `contracts/codegen/manifest.toml` 첫 등기 항목이 `frontend/node_modules/.bin/openapi-typescript`
를 직접 부른다.

**실측 — 손대기 전 게이트 결과 (축자):**

```
::error::generated-up-to-date red — [fe-core-ts] 재생성 실패 (exit 127): bash: line 1: frontend/node_modules/.bin/openapi-typescript: No such file or directory
generated-up-to-date red — 1건
```

**세운 자리 — `contract-gates` 와 `gate-selftest` 두 잡.** 둘 다 노드 도구를 쓰고, 둘 다
`generated-up-to-date`(후자는 `selftest` → `generated-selftest` 경유)를 돈다.

각 잡의 기존 `cache` 스텝 **뒤에** 셋을 붙였다.

1. `actions/cache@v4` — `frontend/node_modules` (키 = `frontend/package-lock.json` 해시). **없던 캐시다.**
2. `npm ci --prefix {contracts,gates/tools/node,frontend}` — `npm install` 이 아니다. **lock 이 정본**이고
   어긋나면 실패한다.
3. **설치 확인** — `spectral` · `ajv` · `openapi-typescript` 셋이 **실물로 있는지** `test` 로 본다.
   「설치가 돌았다」와 「도구가 있다」는 다르고, 확인 없이 넘어가면 부재가 게이트 red 로 위장해
   원인이 한 겹 멀어진다.

⚠ **`frontend` 전용 잡은 ci.yml 에 없다.** `changes` 잡이 `frontend` 출력을 내지만 그것을 쓰는 잡이
없다. 그래서 「frontend 대상」은 **두 노드 잡의 `frontend/node_modules` 설치**로 덮었다.
frontend 시험·빌드 잡을 새로 만드는 것은 이 WU 의 완료 정의에 없고 `frontend/**` 는 다른 레인 소유라
하지 않았다.

**실측 — 설치 후 (축자):**

```
generated-up-to-date green — 등기부 4건 전부 재생성 일치, 등기부 밖 자칭 생성물 0건.
```

---

## 5. 돌린 게이트 · 시험 (2026-08-28 · 이 워크트리 · 축자)

| 대상 | 결과 |
|---|---|
| `generated-up-to-date` (설치 전) | **RED** — `[fe-core-ts] 재생성 실패 (exit 127)` · **도구 부재 = RED 는 옳은 동작** |
| `generated-up-to-date` (설치 후) | green — 등기부 4건 전부 재생성 일치, 등기부 밖 자칭 생성물 0건 |
| `generated-selftest` | green — 9 케이스 전부 기대대로 (green 1 · red 8) |
| `contract-lint` | green — seam 3건, 룰 위반 0 |
| `event-lint` | green — 스키마 2건 컴파일 · valid 5건 통과 · invalid 8건 거부 |
| `seam-consistency` | green — G-e 336건 · G-b 7건 · ㉠ 0건 · ㉡ 18건 |
| `migration-single-head` | green — 두 체인 모두 head 1개 (platform 7건 · ai 5건) |
| `banned-import` | green — .py 113건, 금지 import 0 |
| `db-boundary` | green — 단위 7개 · 스캔 대상 215건 · 위반 0 |
| `work-item-consistency` | **RED** — conflict 12건 등. **이 회차와 무관한 선행 상태다**(대장 무접촉) |
| `verify/selftest.sh` | GREEN — 15건 전부 기대대로 · red fixture 가 실제로 red 를 냈다 |
| `pipeline/selftest.sh` | GREEN — 14건 + 판정기 전건 기대대로 |
| `compose.i2.yml` 보간 | 태그 있을 때 5종 전부 `:testtag` · **없을 때 거부**(`required variable COLAB_RELEASE_TAG is missing a value`) |

**안 돈 것 — 이름으로 적는다.** `schema-diff` · `rls-coverage` · `rls-effect` · `db-selftest` ·
`rls-effect-selftest` · `stage2-markers` 계열(각각 DB 또는 워커 런타임이 필요) · `gates/run.sh selftest`
전종. 이번 회차의 변경 표면(배포 배관 · CI 워크플로)에 걸리지 않는 게이트이고, **돌지 않은 것을
통과로 세지 않는다.**

---

## 6. 이 회차에 **하지 않은 것**

- **staging 실배포·롤백·재배포를 하지 않았다.** 운영 스택 `colab_v2_staging_*` 무접촉 —
  정지·재기동·재생성·`down` 없음, `DELETE`/`UPDATE`/DDL 없음, 파괴 플래그 없음.
- `compose.i2.yml` **파일명 개명 안 함.** `I3 §2-4` 는 릴리스 중립 이름을 권했지만, 이 이름을 참조하는
  자리가 레포에 **8곳**(`gates/db_boundary.py` · `db-boundary-selftest.sh` · `restore/RUNBOOK.md` ·
  서비스 README 등)이라 개명이 남의 레인 파일을 건드린다. **태그 중립화로 실질을 얻고 이름은 남겼다** —
  파일명이 릴리스를 좁히지 않는다는 사실을 헤더 주석에 적었다.
- `RESTART.md` 미갱신 — `I3 §4` 가 「다른 레인이 끝난 뒤 마지막에」로 못 박았고, 이번 회차는
  실배포 전이라 절차의 실물이 아직 안 섰다.
- `contracts/seams/` · `frontend/**` · `dev-package/work-items.yaml` · `03-HANDOFF.md` · `PLAN-SoT.md` ·
  `WORK-UNITS*` 전부 무접촉.
- `gates/` 무접촉 — 파이프라인이 게이트를 부르는 방식이지 게이트를 파이프라인 사정에 맞추지 않았다.

---

## 7. 완료 정의 대조 (`I3 §6` 14항)

| # | 항목 | 상태 |
|---|---|---|
| 1 | 파이프라인 1회 완주 | **못 닫음** — 기구는 섰다. 실행이 남았다 |
| 2 | staging 배포 green (헬스 6종 + 본문) | **못 닫음** — 배포 전 |
| 2-b | 종료 코드의 근거가 6종 판정 | **닫힘(구현)** — red fixture 로 증명. 실배포 로그 1건씩은 미확보 |
| 3 | 컨테이너 8개 healthy · `0.0.0.0` 0건 | **못 닫음** — 배포 전 (검사는 구현·증명됨) |
| 4 | 롤백 왕복 증명 | **못 닫음** — 배포 전 |
| 5 | 롤백이 자리표시가 아니라 직전 릴리스로 | **닫힘(구현)** — selftest P1~P6. 실물 왕복은 미실행 |
| 6 | 두 체인 head + 시드 22행 유지 | **못 닫음** — 배포 전 |
| 7 | 배포 전 백업이 실제로 걸린다 | **닫힘(구현)** — 두 프로파일 GREEN 아니면 중단. 실행은 배포 때 |
| 8 | 판정기 fail-closed red fixture (죽은 단위·자리표시 본문·한쪽 체인 미적용) | **닫힘** — F1·F2·F12 각각 red, 양성 대조군 F3·F13 green |
| 9 | 승인 없이 prod 가 도는 경로 부재 | **닫힘** — F7·P12 red. ⚠ 음성만 증명된다(양성 대조군 없음) |
| 10 | 게이트 전 종 green + selftest green | **못 닫음** — DB·워커 런타임 필요 게이트 미실행 · `work-item-consistency` 선행 RED |
| 11 | 작업 전·후 `/healthz` 200 → 200 | **해당 없음** — 운영 스택 무접촉 회차 |
| 12 | DR-4 닫힘 (+ `:13` 주석 정정) | **닫힘(구현)** — 트리 청결 강제 · 태그=SHA · 주석 정정. 실배포 태그 확인은 배포 때 |
| 13 | DR-6 닫힘 (+ `:16` 주석 정정) | **닫힘(구현)** — 앱 5종 헬스 게이트 · 주석 정정 |
| 14 | DR-5 닫힘 (보존이 빌드보다 먼저 · ID 대조) | **닫힘(구현)** — 순서 ③→④ · ID 대조 출력. 실행 중 출력은 배포 때 |

**부분 완료로 닫지 않는다.** `I3` 는 **여전히 열려 있다** — 남은 것은 「기구를 만드는 일」이 아니라
**「한 번 돌리는 일」**이다.

---

## 8. Ted 가 배포를 실행할 때

**전제** — 다른 레인이 staging 을 쓰고 있지 않아야 한다(`I3 §5-7`). 홈의 `0600` 설정 파일
(`~/.colab-v2-staging.env`) 과 백업 설정이 서 있어야 한다.

**한 줄:**

```bash
infra/staging/pipeline/run-pipeline.sh --target staging --force
```

- `--force` 는 「새 커밋이 없어도 한 바퀴 돌라」는 뜻이다. 크론이 부를 때는 안 붙는다.
- 이 한 줄이 게이트 → 태그 보존 → 빌드 → 백업 → 마이그레이션 → 교체 → **판정**까지 간다.
- 실패하면 **중단 ＋ 표식 파일**이다. 자동 롤백은 없다.
- 되돌리려면: `infra/staging/rollback.sh --to-last-green`
- 크론 상시화(승인 후): `infra/staging/pipeline/install-schedule.sh install`

**결과를 어디서 보나** — `~/colab-v2-releases/` 의 `release-ledger.tsv` · `DEPLOY-FAILED.txt` ·
`LAST-SUCCESS.txt` · `pipeline.log`.

---

## 9. `[미확인]` — 무엇을 하면 풀리나

| 항목 | 풀리는 조건 |
|---|---|
| 파이프라인 1회 완주 · staging 배포 green · 롤백 왕복 · 시드 22행 유지 | §8 의 한 줄을 Ted 승인 후 실행 |
| `deploy.sh` 가 **red 를 실제로 반환하는 실행 로그 1건**(완료 정의 2-b) | 위 실행 중 자연 발생하거나, 단위 하나를 일부러 죽인 회차 1건 |
| 이미지 보존 3개의 **digest** (`reference/IMAGE-DIGESTS.md` 와 묶는다 · `〈168〉-㉰`) | 릴리스가 3개 쌓인 뒤 digest 를 대장에 적는다. **지금은 릴리스가 0개다** |
| 컨테이너 `colab_v2_staging_cloudflared` 의 헬스체크 존재 여부 | `compose.i2.yml` 에 `healthcheck` 선언이 없다. `RESTART.md` 는 8개 healthy 를 적었으므로 **이미지 내장 HEALTHCHECK 로 추정**하되 재지 않았다. 판정기는 **healthy 가 아니면 red** 로 둔다(fail-closed) — 배포 회차에 실물로 갈린다 |
| staging 실물의 `403` 2건 (`work-items.yaml` X5 잔여) | 배포 후 `PATCH` 2회 |
| 클라우드 CI 와 호스트 게이트가 갈리는지 | 자동 탐지 없음. 갈리면 **호스트 쪽이 정본**이라고만 정해 뒀다(`I3 §7-10`) |
