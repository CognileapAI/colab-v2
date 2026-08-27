# gates — 경계를 기계가 지킨다

v1(PoC)에서 터진 버그는 전부 **"관례로 지키기로 했던 것"** 이었다. v2는 관례를 두지 않는다.

| 게이트 | 무엇을 막나 |
|---|---|
| `contract-lint` | seam 스펙 오류 |
| `contract-breaking` | emit된 스펙이 frozen seam과 충돌 |
| `event-lint` | 이벤트 계약(`contracts/events/**`)의 스키마 오류 · `$ref` 미해석 · 인스턴스 계약 위반 |
| `event-breaking` | 이벤트 계약의 `$defs` 단위 파괴적 변경 (규칙표 = `dev-package/sessions/D2b.md §2`) |
| `generated-up-to-date` | 생성물이 계약보다 낡음 |
| `import-boundary` | 도메인 간 직접 참조 |
| `banned-import` | core-api의 geo 라이브러리 |
| **`db-boundary`** | **배포 단위가 허용된 DB 체인 밖에 접속을 선언** (정본 = `gates/config/db-boundaries.toml`). `import-boundary` 가 못 보는 계열 — 횡단이 import 가 아니라 **DB 접속**일 때 |
| **`ai-no-lineage-write`** | **D10 → D4 쓰기 경로 존재** (음성) |
| `migration-single-head` | 마이그레이션 head 분기 (platform / ai 각각) |
| `schema-diff` | 선언 스키마 ↔ 적용 DB 드리프트 (**체인별로 각각** — `COLAB_APPLIED_DB_URL_PLATFORM` · `_AI` 둘 다 필요) |
| `rls-coverage` | allow-list 밖 테이블의 RLS 누락 (정책이 **걸려 있는가**) |
| **`rls-effect`** | **RLS 가 실제로 막는가** — 본체 음성(허용자 아님·만료됨 0행) · 메타 양성(`P-13`) · cross-tenant 0행. NOBYPASSRLS·비소유자 롤로 판정하고, 우회 롤이면 red |
| `planning-freshness` | 기획 패키지 HTML의 임베드 md가 원본 md보다 낡음 (정본 미마운트 포함) |
| `stage2-markers` | 휴면(`stage2` 대기) 모듈의 시험이 CI 에서 **안 도는 것** — 수집 0건 · skipped · failed 가 전부 red (`PLAN-SoT §9 〈71〉-㉰`) |
| **`seam-consistency`** | **seam ↔ 이벤트 계약의 사이** — G-e 산문 위임 참조(실재하지 않는 seam·op 에의 위임 — `DR-7` 의 모양) · G-b `source: const` 능력 주장(촉발 HTTP op 부재) · ㉠ 신설 op·스키마의 정본 근거 공란 · ㉡ E-04 흐름 완주(사람 고정 fixture 재생) |
| `selftest` | **위 게이트들이 실제로 red를 낼 수 있는지** (contract · event · boundary · db-boundary · db · rls-effect · seam-consistency · generated 증명 여덟). ⚠ **`stage2-markers-selftest` 는 여기 없다** — pipeline-worker 런타임 의존(rasterio 등)이 필요해 `contract-gates` 잡 환경에서 못 돈다. CI 는 `dormant-tests` 잡에서 따로 부른다 |

## selftest가 있는 이유

"전부 green"과 "전부 무력"은 구분되지 않는다. v1 CI는 DB 없이 돌아 RLS 테스트를 **green-by-skip** 했다.
각 게이트는 red fixture로 자신이 fail-closed임을 증명해야 한다.

## 현재 상태 (2026-08-25)

**미구현 게이트는 red 를 낸다.** 우회하거나 끄지 않는다.

| 게이트 | 상태 | 지금 red 인 이유 |
|---|---|---|
| `planning-freshness` | ✅ 구현 (WU-G1) | — green |
| `contract-lint` · `contract-breaking` | ✅ 구현 (WU-D2) | — green |
| `event-lint` · `event-breaking` | ✅ 구현 (WU-D2b) | — green |
| `import-boundary` · `banned-import` · `ai-no-lineage-write` | ✅ 구현 (WU-D3) | — **green (2026-08-25 P2 실측).** 이전 판에는 「red — `services/` 에 코드가 없다」라고 적혀 있었으나 P0·P1 이 네 단위를 채운 뒤로 셋 다 green 이다. **이 줄만 낡아 있었다** (`DATA-REFERENCE §0 M-6`) | ⭑ **2026-08-27 — `ai-no-lineage-write` ⑨⑩ 의 산문 오탐 제거**(`PLAN-SoT §9 〈172〉`). `origin/main` 도 같은 red 였다
| **`db-boundary`** | ✅ 구현 (2026-08-25) | — green (단위 7 · 스캔 대상 182건 · 위반 0). `COLAB_AI_CATALOG_DB_URL` 이 판정 ㈎ 로 사라진 뒤의 배치를 기준으로 한다 |
| `migration-single-head` · `rls-coverage` | ✅ 구현 (WU-D3) | — green (P0 이 `db/` 를 채웠다) |
| `rls-effect` | ✅ 구현 (WU-D3b) | — green (A2 의 시드·앱 롤을 그대로 쓴다) |
| `seam-consistency` | ✅ 구현 (WU-D2c) — 단, 5종 중 **G-e·G-b 만** (최소 채택선) + 〈61〉-㉠·㉡ | — green (D2c 개정 후 계약 기준. **G-a 식별자 도달성 · G-c 짝 op 대칭 · G-d 공유 값 집합 재선언은 미구현** — 감추지 않는다, `D2c.md §2-13`) |
| `schema-diff` | ✅ 구현 (WU-D3) · 체인별 URL 로 수정 | 체인별 적용 DB URL 을 **둘 다** 주면 green. 하나라도 없으면 red. ⭑ **2026-08-27 살아 있는 staging 실측 — 두 체인 다 green(드리프트 0)** (`PLAN-SoT §9 〈172〉-㉴`). 적용 DB 는 `pg_dump --schema-only` **읽기만** 했고, 일회용 postgres 를 컴포즈 네트워크에 붙이려고 `_pg.sh` 에 `COLAB_PG_NETWORK` 를 더했다(포트는 여전히 미공개) |
| `generated-up-to-date` | ✅ 구현 | **green (2026-08-23 P2 W0-7 실측).** 이전 판에는 「red — `fe-core.ts` 가 D2c 개정 이전 판」이라 적혀 있었으나, **재생성해 보니 diff 0 이고 게이트가 green** 이다 — 생성물은 D2c 개정과 함께 이미 갱신돼 있었고 **이 줄만 낡아 있었다**(`DATA-REFERENCE §0 M-6` — 문서·주석을 실물 확인 없이 인용하지 않는다). 재현 = `cd frontend && npm ci && npm run generate` 뒤 `./gates/run.sh generated-up-to-date` |

> **red 인 것이 정상인 게이트가 있다.** "AI 가 계보에 쓰지 않는다"와 "AI 가 아직 없다"는 다른 사실이라, 검사 대상 0건을 green 으로 세지 않는다. 이 게이트들은 P0 이 코드를 만들면 비로소 green 이 될 수 있다.

## 자기 증명 (selftest)

각 게이트가 **자기가 fail-closed 임을 red fixture 로 증명**한다. 증명 셋은 셋으로 나뉘어 있다 — 서로의 인프라 사고에 걸리지 않게 하기 위해서다.

| 셋 | 케이스 | 의존 |
|---|---|---|
| `contract-selftest` | **15** | docker(oasdiff) · spectral |
| `event-selftest` | **33** | node + ajv (`gates/tools/node`) |
| `boundary-selftest` | **37** | python venv |
| `db-boundary-selftest` | **18** | python3 + pyyaml — red fixture 에 **2026-08-25 위반 실물**(`COLAB_AI_CATALOG_DB_URL`)을 소스·Dockerfile·compose 세 자리에서 재현. 픽스처는 자기 매니페스트를 들고 다닌다 |
| `db-selftest` | **43** | docker(postgres) — 24 는 docker 없이도 돈다 |
| `seam-consistency-selftest` | **13** | python3 + pyyaml — red fixture 에 **개정 전 `fe-core.yaml:13-16` 위임 산문 원문**(`DR-7` 실물) 포함 |
| `rls-effect-selftest` | **18** | docker(postgres) — 매 케이스가 자기 일회용 DB 를 새로 짓는다 |
| `stage2-markers-selftest` | **3** | pipeline-worker venv — ⓐ 마커 0건 · ⓑ skip · ⓒ fail 셋이 전부 red 임을 증명한다. ⓑ 가 핵심이다: **green-by-skip 이 v1 의 실패 형태**다 |
| `generated-selftest` | **9** | 없음 (bash + python3) — green 기준 케이스도 fixture 다. 레포 실물은 재생성 파이프라인 상태에 따라 정당하게 red 일 수 있어, selftest 가 레포 상태에 볼모잡히지 않게 했다 |
| `selftest` | 위 전부 | |

> `db-selftest` 의 픽스처 케이스는 **레포의 `gates/config/rls-allowlist.toml` 을 읽지 않는다.**
> 합성 스키마에 없는 테이블이 allow-list 에 정당하게 추가되면(K1 이 그랬다) 기준 케이스가 red 가 되기 때문이다 —
> 게이트가 옳고 selftest 의 배선이 틀린 경우다. 픽스처는 자기 allow-list 를 들고 다닌다 (`WU-D3b`).

`planning-freshness` 의 증명은 `dev-package/tools/check-package-freshness.py --selftest`(3 케이스).

## seam-consistency 가 기계화하지 못하는 것 (WU-D2c §2-14 — 정직하게)

능력을 실제보다 크게 말하는 것이 `DR-4`·`DR-6` 이 만든 사고다. 이 게이트가 **못 하는 것** —

- **어느 seam 이 정본인가** — 값 판단이다. 게이트는 **「갈렸다」까지만** 말한다. `〈54〉` 같은 결정을 대신하지 않는다.
- **자유 문자열이 의도적 개방인지 누락인지** — `core-pipeline.json:54` 는 이유가 붙은 의도적 개방이고 `fe-core.yaml` 의 `topic` 은 이유가 없다. 둘의 차이는 산문에만 있어, 기계는 사람이 allow-list 로 가르기 전까지 구분하지 못한다 (G-d 미구현 사유이기도 하다).
- **정본 문구 ↔ 계약 어휘 대조(`DR-8`)** — 정본이 md 산문이라 값 집합을 기계가 못 뽑는다. 결정 → 계약 반영 체크리스트(사람 절차)로 갈 수밖에 없다 `[추론]`. `planning-freshness` 는 임베드↔원본만 보지 결정↔정본은 아무도 안 본다.
- **화면 요구 충족 여부** — op 이 있어도 그 화면을 그릴 수 있는지는 판정 불가.
- **㉠ 은 근거의 존재만 본다** — 근거를 달았는데 그 근거가 엉뚱해도 통과한다. **㉡ 은 흐름의 연결만 본다** — 이어지는데 이상한 흐름도 통과한다. 그래서 ㉢(사람 승인)이 형식이 아니라 실질이어야 한다 (`D2c.md §7-8`·`§10-12`).
- **G-e 의 근본 한계** — 정규식이 산문에서 파일명·op 이름·「X seam」 위임 문구처럼 **생긴 것**을 뽑는다. 「이벤트/업로드 seam」이 잡히는 것은 그 문장에 `seam` 어휘가 있어서다 — **다음 번 같은 실수가 이름 아닌 서술로 오면 못 잡는다.** 게이트를 만들었다는 사실이 이 계열이 닫혔다는 뜻이 아니다.
- **㉡ 의 fixture 의존** — E-04 단계 분해는 사람이 고정한 fixture(`gates/fixtures/seam-consistency/e04-flow.json`)다. **그 표가 틀리면 ㉡ 은 틀린 흐름을 완주로 판정한다** (`PLAN-SoT 〈61〉` 경고). 검토 없이 fixture 를 고치지 않는다.
- **⭑ `stage2` 마커가 **옳은 시험**에 붙었는지** — `stage2-markers` 는 「마커가 붙은 것이 도는가」만 본다. 휴면 모듈을 단언하는데 마커가 **안 붙은** 시험은 못 잡는다. 대상 판정 기준은 `d5/` 모듈 docstring 의 `stage2 대기` 표기이고 **사람이 대조한다**.
- **⭑ 계약이 선언한 op 이 코드에 실재하는지** — **아무 게이트도 안 본다.** 계약에 op 이 있고 구현이 없어도, 구현이 있고 계약이 비어도 전부 green 이다. 501 표(`test_not_implemented.py`)가 그 자리를 사람 손으로 메우고 있다.
- **⭑ 포맷 목록이 서비스마다 갈라지는 것** — `SUPPORTED_FORMATS` 가 `pipeline-worker` 와 `viz-render` **두 곳에 따로** 있는데 게이트는 둘을 대조하지 않는다(`〈77〉`).
- **㉠ 의 기준선 의존** — 「신설」은 git HEAD(또는 지정 기준선) 대비다. 개정이 커밋된 뒤에는 그 회차의 신설분이 기준선 안으로 들어가 대조 대상이 0건이 된다 — ㉠ 은 **개정 회차의 게이트**이지 소급 감사가 아니다.

## db-boundary 가 **못 보는** 것 (정직하게)

`import-boundary` 가 green 인 채로 ai-service 가 D3 에 붙어 있었던 것이 이 게이트를 만든 이유다.
그러니 이 게이트의 능력도 실제보다 크게 말하지 않는다.

**보는 것** — ① 각 단위 `Dockerfile` 의 `ENV`/`ARG` (주석 제외) · ② 각 단위 `src/`·`tests/` 파이썬 소스의
**문자열 리터럴**(AST, docstring 제외 — 주석은 애초에 AST 에 없다) · ③ `infra/staging/compose.i2.yml` 의
서비스별 `environment` · ④ `chains = []` 인 단위 안의 접속 개시 호출(`create_engine` 류).

**못 보는 것** —

- **런타임에 조각으로 조립하는 접속 문자열** — `f"postgresql://{host}/{db}"` 처럼 이름이 통째로 문자열에
  안 나타나면 못 잡는다. `*_DB_URL` 관례를 지키는 동안만 유효한 게이트다.
- **HTTP 로 우회하는 질의** — 다른 단위의 API 를 불러 그쪽 DB 를 대신 읽게 하면 DB 접속 선언이 아니라
  통과한다. 그 계열은 seam 계약과 `〈90〉` 같은 사람 판정이 지킨다.
- **체인 안에서의 도메인 횡단** — `db/platform` 안에서 D5 가 D3 테이블을 직접 읽는 것은 **같은 체인**이라
  이 게이트가 보지 못한다. 그 자리는 `import-boundary`·`rls-*` 와 사람 리뷰의 몫이다.
- **파이썬이 아닌 소스** — 프론트엔드 TS·쉘 스크립트·CI 워크플로의 env 선언은 스캔하지 않는다
  (`frontend` 는 `chains = []` 이지만 Dockerfile·compose 만 본다).
- **compose.i2.yml 이 아닌 배선** — `.env` 파일·호스트 환경변수·prod 매니페스트는 대상이 아니다.
  I2 staging 의 그 파일 하나만 본다.
- **매니페스트가 틀린 경우** — 표가 정본이라, 표를 넓히면 게이트는 조용해진다. `chains` 를 늘리는 편집은
  경계를 넓히는 결정이지 게이트 수리가 아니다 (`CLAUDE.md §4`).
