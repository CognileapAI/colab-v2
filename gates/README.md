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
| **`autometa-loss`** | **사건이 발행되고도 장부에 반영되지 않았는가** (`PLAN-SoT §9 〈190〉-㉱`). 세는 단위 = (업로드, 칸) 쌍 · 칸 = `format`·`crs`·`grid`. 발행 ↔ 반영을 대조하고 어긋나면 red. **대상 0건도 red** 이고, **대조 정본**(`COLAB_AUTOMETA_STAGING_DB_URL`)이 없어도 red 다. ⭑ **⟨개정 2026-08-31 · `PLAN-SoT §9 〈237〉` · `#50` 해소⟩ 대조 정본은 staging 실물 platform DB 다** — 질문이 「실제로 접수한 것 중 메타가 빠진 것이 있는가」라 정답지가 실물이어야 한다. 종전에는 `schema-diff` 와 **공유하는** 스키마 전용 일회용 DB 를 봐서 접수분이 구조적으로 0건이었다(어떤 회차에도 green 이 될 수 없었다). **접근은 읽기 전용이다** — 선언이 읽기 전용이 아니면 red · 매 회차 **쓰기 탐침**을 던져 거부당하는지 확인하고 통과하면 red · 스크립트에 `COMMIT` 이 없다. 면제는 `gates/config/autometa-loss.toml` 에 **이름으로** 적혀야 하고 그 건수가 출력에 드러난다 |
| **`preview-tile-slot`** | **지도 타일이 자리에 놓였고, 놓인 것을 다시 쓸 수 있는가** (완료 정의 ⑵ 축자 「산출물이 그 자리에 기록되어 다시 만들지 않고 찾아 쓸 수 있다」). 세는 단위 = 자리에 놓인 지도 타일 파일 1건 — **사건으로 세지 않는다**(재사용이 성립하면 사건 여럿이 타일 하나를 함께 쓴다). 대조 둘 = ⑴ 발행됐는데 자리가 비었나 ⑵ 자리에 있는데 COG 층이 아니라 재사용이 영원히 거절되나. **대상 0건도 red** 이고, 대조 정본(`COLAB_PREVIEW_TILE_DB_URL` = **staging 실물 platform DB · 읽기 전용**)·경계 롤 이름(`COLAB_PREVIEW_TILE_BOUNDARY_ROLE`)·자리 경로(`COLAB_PREVIEW_TILE_DIR`)가 없어도 red 다. ⭑ **2026-09-02 · `#57` (Ted 판정 ⓒ 둘 다 · `〈271〉`-㉮)** — 롤 판정 두 겹(㉮ 관리자 롤인가 · ㉯ 경계 롤 재조회 값이 갈리는가) ＋ **발행 0건 자체가 red** ＋ 배선을 스키마 전용 DB 에서 staging 실물로 옮겼다. 종전에는 경계 롤이면 발행이 0 이 되어 핵심 판정이 통째로 건너뛰고 green 이 났다. 면제는 `gates/config/preview-tile-slot.toml` 에 **파일 이름으로** 적혀야 하고 그 건수가 출력에 드러난다 |
| **`artifact-ownership`** | **자리에 쌓인 산출물이 지금 누구 것인가** (`A-1` 완료 정의 ⑴⑵⑸ · Ted 판정 「안 ⑷ 사이드카 판정」 · **갈래 B — 게이트 대조** · `PLAN-SoT §9 〈270〉`·`〈271〉`). 세는 단위 = **한 캐시 키 아래 선 산출물 한 벌**(파일로 세지 않는다 — 한 벌은 함께 산다). 판정 = 사이드카 `sources`(fileId 배열) → **원장 대조**. 이음은 **`d5_upload_file.id = d3_file.id`**(`NB-A` 동일성 · 업로드→데이터셋 FK 는 없다) — 선례 `autometa-loss.sh:14` 의 같은 조인이다. **네 등급** 계수(살아 있다 / 접수분에만 닿는다 / 고아 / 판정 불가)와 **회수 전 전수 스냅숏**(키·확장자·크기·사이드카 `source`·등급)을 낸다. ⚠⚠ **덫 ① — `baked_for` 를 「현재 소유」로 읽지 않는다**: 그 값은 「구울 때의 대상」이라 등록 전환 뒤 낡고, 그것으로 판정하면 **등록된 대상이 전부 불일치로 뜬다.** 판정 입력은 `sources` ＋ 원장뿐이다(정본 규칙 = `d7_visualization/ownership.py` `grade()` · 게이트가 그 파일을 **경로로 그대로 실어** 쓴다 — 규칙을 두 곳에 적지 않는다). ⚠⚠ **덫 ② — 구판은 「고아」가 아니라 「구판 · 판정 보류」다**: `sidecarVersion`·`baked_for` 가 없으면 판정을 하지 않는다. **없는 필드를 근거로 지우면 그것이 오삭제다.** 보류는 `gates/config/artifact-ownership.toml` `[legacy] tolerate` 로 **선언**하고 **건수를 드러낸 채** 넘어간다(완료 정의 ⑴ 축자). **대상 0건도 red** · **원장 두 표 0행도 red**(경계에 걸린 0 을 「없다」로 읽어 전건을 고아로 센 파괴적 오판이 실재했다 — `DATA-REFERENCE §0 M-9`) · 대조 정본(`COLAB_ARTIFACT_OWNER_DB_URL` = staging 실물 platform DB · **읽기 전용**)·경계 롤(`COLAB_ARTIFACT_OWNER_BOUNDARY_ROLE`)·자리(`COLAB_ARTIFACT_OWNER_DIR`) 미선언도 red. 롤 판정 두 겹과 쓰기 탐침은 `preview-tile-slot`(#57)의 규율을 그대로 잇는다. ⚠ **이 게이트는 아무것도 지우지 않는다** — 회수 집행은 `invalidation.apply()` 한 자리이고(완료 정의 ⑶ · `invalidation.reclaim_plan`), 지도 타일(`tile-`)과 접수분 루트는 애초에 대상이 아니다(완료 정의 ⑷ · 음성 시험이 잠근다) |
| **`e2e-format-coverage`** | **지원 포맷 목록의 각 포맷이 실파일로 실제 그려지는가** (`WORK-UNITS §7` `S3` 행 축자 「4종 각각 최소 1건이 시각화 화면에 그려지고 … 실패 파일은 목록으로 남긴다」). 판정 목록의 정본 = `gates/config/e2e-format-coverage.toml`(같은 행이 `〈77〉` 로 `NumPy` 를 더해 다섯으로 판정하라고 적는다). 세는 단위 = **포맷 표식이 붙은 시험 케이스 1건** — 파일 수로 세지 않는다. **표식 붙은 케이스 0건도 red** 이고, 원천 마운트(`COLAB_REFERENCE_DATA`)가 없어도 red 다(준비 red · skip 아님). 실패·건너뜀 케이스는 **이름으로** 출력에 나온다. 면제는 그 파일에 **포맷 이름으로** 적혀야 하고 그 건수가 출력에 드러난다. ⚠ **이 게이트는 `S3` 를 닫지 않는다** — 계보 확정 상태와 staging 배포 green 은 여기서 재지 않는다 |
| **`render-latency`** | **미리보기가 합격선 안에 그려지는가** (`PLAN-SoT §9 〈233〉` · 정본 `Policy_데이터셋_상세` v2.6 `§8` 조건 ⑺). 눈금의 정본 = **`gates/config/render-latency.toml` 하나**(미리보기 최초 표시 **p95 10초 · 상한 60초**). 재는 것은 시험(`services/viz-render/tests/test_perf_render_latency.py` · 표식 `perf`)이고 **판정은 여기서만** 한다 — 양쪽에서 재면 기준이 두 곳으로 갈린다. 세는 단위 = **junit 속성 `렌더초` 가 붙은 시험 케이스 1건**. **표본 0건도 red** · 표본 10건 미만·포맷 5종 미만 red · 실패·건너뛴 케이스 red(**그리지 못한 것은 시간이 짧다**) · **상한만이 아니라 p95 도 본다** · 원천 마운트(`COLAB_REFERENCE_DATA`)·venv 부재는 준비 red(skip 아님). ⚠ **이 게이트는 화면 왕복을 재지 않는다** — 잰 지점과 안 잰 넷은 시험 머리말에 이름으로 있다. ⚠ **확대·이동 반응은 이 게이트가 아니라 시험이 진다**(`frontend/test/dataset-preview-zoom-latency.test.tsx`) — 레포에 frontend 시험을 도는 게이트가 없다 |
| **`frontend-typecheck`** | **프런트 타입 검사가 이미지 빌드 밖에서도 도는가** — `frontend/Dockerfile` 의 `npm run build`(`tsc --noEmit && vite build`) 가 도는 **바로 그 검사**를 같은 tsconfig(`frontend/tsconfig.json` · `include` = `src`·`test`)로 돈다. ⭑ **2026-09-02 사고** — 이 검사는 **이미지 빌드 안에만** 있었고 게이트에는 한 줄도 없었다(`grep -rl 'tsc --noEmit' gates/` = 0). 그래서 `node:fs` 를 import 한 시험 파일이 들어간 12:01 부터 22:32 의 staging 배포가 이미지 빌드에서 깨질 때까지 **`main` 이 배포 불가인 채로 전 게이트 green** 이었고, 그 사이 다섯 레인이 「tsc 오류 4건 = main 동일」을 보고했으나 **기존 상태로 수용**됐다 — 아무도 재지 않는 검사는 「원래 그렇다」로 굳는다. **갈림 방지 두 겹** — `package.json` `build` 가 `tsc --noEmit` 으로 시작하지 않으면 red · `Dockerfile` 이 `npm run build` 를 안 돌면 red. **범위 축소 금지** — `tsconfig` `include` 에서 `src`·`test` 가 빠지면 red(통과시키려 보는 범위를 줄이는 것은 수정이 아니다 · `CLAUDE.md §3`). `node_modules`·`.bin/tsc` 부재는 skip 이 아니라 **red(준비 · 코드 78)** |
| **`seam-consistency`** | **seam ↔ 이벤트 계약의 사이** — G-e 산문 위임 참조(실재하지 않는 seam·op 에의 위임 — `DR-7` 의 모양) · G-b `source: const` 능력 주장(촉발 HTTP op 부재) · ㉠ 신설 op·스키마의 정본 근거 공란 · ㉡ E-04 흐름 완주(사람 고정 fixture 재생) |
| **`work-item-consistency`** | **개발 항목 상태의 대장 ↔ 산문 불일치** (정본 = `dev-package/work-items.yaml`). ⭑ **⟨증보 2026-09-01 · `PLAN-SoT §9 〈268〉`⟩ 검사 8종** — 종전 일곱 ＋ **㈕ `CLAUDE.md` stage 3 표지 ↔ 대장 `stage: after_stage2` 집합 대조**(표지 부재·미폐쇄·`CLAUDE.md` 부재는 red). ／ 이전 표기 ~~⭑ ⟨증보 2026-08-31 · `PLAN-SoT §9 〈252〉`⟩ 검사 7종~~ — ㈎ 대장 스키마 · ㈏ `WORK-UNITS §11` 완주 체크리스트 대조 · ㈐ `03-HANDOFF §1` 진실원 표 대조 · ㈑ `⏸`(하지 않기로 한 것)의 착수 후보 표 혼입 · ㈒ 기한 발동인데 안 열린 항목 · ㈓ `conflict` 잔존 · **㈔ `PLAN-SoT §9` 결정 번호 `〈n〉` 중복**. ／ 이전 표기 ~~검사 6종 — ㈎~㈓~~. **상태 관리가 「관례를 두지 않는다」의 마지막 사각지대였다** |
| **`frontend-test`** | **화면 동작 시험(`frontend/test` · vitest)이 게이트 안에서 도는가** — `frontend/package.json` 의 `test`(`vitest run`) 와 **같은 명령**을 레포의 `vite.config.ts`(jsdom · `include`=`test/**/*.test.ts(x)`) 그대로 돈다. ⭑ **2026-09-03 화면 검수** — 시험 24파일 446건이 이미 있는데 **게이트 39개 어디에도 없었다.** `frontend-typecheck` 는 타입만 보고 라벨·문구·표기 규칙 같은 **화면 동작**은 아무도 재지 않았다 — 그래서 정본과 어긋난 화면 30행이 전 게이트 green 인 채로 staging 에 서 있었다. **갈림 방지** — `package.json` 의 `test` 가 `vitest run` 으로 시작하지 않으면 red. ⭑ **수집된 시험 0건도 red** — 통과 0·실패 0 은 「전부 통과」가 아니라 「아무것도 검사하지 않았다」다(`CLAUDE.md §4` green-by-skip). 통과 건수를 요약에서 읽지 못해도 red(`CLAUDE.md §5`). `node_modules`·`.bin/vitest` 부재는 skip 이 아니라 **red(준비 · 코드 78)**. ⚠ jsdom 밖(실제 CSS 레이아웃·휠 이벤트·캔버스 렌더)은 이 게이트가 보지 않는다 — 그 자리는 화면 스모크(Playwright) 물음으로 남아 있다 |
| **`backup-cron-streak`** | **크론 무인 백업의 연속 GREEN 이 지금도 서 있는가** (`PLAN-SoT §9 〈286〉` ① · 등재 `〈296〉`-㉴). ⚠ **이 게이트는 다시 재지 않는다 — 읽는다.** 판정 입력은 크론 04:40 회차(`infra/staging/backup/check-cron-streak.sh`)가 `~/colab-v2-backups/staging-backup.log` 에 남긴 **마지막 요약줄** 하나다. 재실행하지 않는 이유 = 게이트 호스트가 보관처를 못 보면 재실행은 **항상 RED** 가 되고 그때 「보관처 없음」과 「연속 깨짐」이 **안 갈린다**(`render-latency` 와 같은 「보관처 있는 호스트에서만 도는 게이트」 배치). 세는 단위 = **`크론 연속 GREEN:` 으로 시작하는 요약줄 1건**. ⚠ **요약줄 자체에는 시각이 없다** — 시각은 `run-scheduled.sh` 가 **그 다음 줄**(`… check-cron-streak.sh 성공|실패`)에 적고, 게이트는 둘을 **짝으로** 읽는다. **짝을 못 찾으면 red** 다(나이를 못 재는 GREEN 은 판정이 아니다). red 조건 넷 — ⓐ 로그 부재·요약줄 0건(**대상 0건은 통과가 아니다**) ⓑ 요약줄이 **36시간**보다 오래됨(일 1회 ＋ 12h 여유 · green-by-stale 차단) ⓒ 요약줄이 RED ⓓ 요약줄이 **「검사 0건 · 승인된 SKIP」 GREEN**(`lib.sh verdict` 의 SKIP-GREEN 을 그대로 받지 않는다). 근사 한계(무인 판별 창 `COLAB_CRON_WINDOW_MIN`)는 **게이트 출력에 그대로 옮긴다** — 안 보이는 근사는 거짓말이 된다 |
| **`service-tests-core-api`** · **`service-tests-ai-service`** · **`service-tests-viz-render`** · **`service-tests-pipeline-worker`** | **서비스 pytest 묶음이 CI 안에서 도는가** (2026-09-03 코드리뷰 #6). ⭑ **종전에는 `grep -rn pytest .github/` = 0 이었다** — CI 가 도는 pytest 는 `stage2-markers` 의 `stage2 and not e2e` 부분 집합 하나뿐이었고, **서비스 측 시험 함수 1102 중 871 이 CI 에서 한 번도 실행되지 않았다**(core-api 51파일·533함수 · ai-service 13·133 · viz-render 28·205). 시험이 레포에 있는 것과 CI 가 그것을 판정하는 것은 다른 사실이다 — `frontend-test` 가 닫은 것과 같은 계열. 판정부 = `gates/tools/service-tests.sh <단위> <표식 선택자>`, 선택자의 정본은 `gates/run.sh` 의 case 한 곳(viz `not e2e and not perf` · pipeline `not e2e and not dbint` · ai `not dictdb` · core-api `not e2e`). **red 조건 여섯** — ⓐ 단위·선택자 인자 부재(빈 선택자를 「전부」로 읽지 않는다) ⓑ 단위·`tests/` 자리 부재 ⓒ **수집 0건** ⓓ **실행 0건(전부 skip)** ⓔ failed·errors ⓕ pytest 비영 종료. **skipped·deselected 는 막지 않고 요약줄에 건수로 드러낸다** — 감춘 건너뜀이 green-by-skip 이지 드러낸 건너뜀은 판정의 일부다. venv 부재는 skip 이 아니라 **red(준비 · 78)**. `core-api` 는 게이트가 **일회용 Postgres 를 스스로 세운다** (`_pg.sh` ＋ `services/core-api/tests/fixtures/setup-db.sh` — 포트 미공개 · PGDATA tmpfs · `--rm` ＋ trap · **접속 문자열을 출력하지 않는다**). ⚠ 뺀 표식은 **취소가 아니다** — 표식은 붙어 있고 그 환경이 있는 실행에서 함께 돈다. `stage2-markers` 는 그대로 남는다(휴면 모듈의 시험이 **계속 도는지**를 재는 다른 질문이다) |
| **`service-tests-selftest`** | 위 네 게이트가 red fixture 로 fail-closed 임을 증명한다 — **ⓐ 통과 1건 green(대조군) · ⓑ 실패 1건 red · ⓒ 수집 0건 red · ⓓ 실행 0건(전부 skip) red · ⓔ venv 부재 red(준비 · 78) · ⓕ·ⓖ 필수 인자 부재 red · ⓗ 단위 자리 부재 red · ⓘ 요약줄이 계수를 낸다**. 픽스처 원본 = `gates/fixtures/service-tests/`(트리 넷 ＋ README), 판정은 `mktemp -d` 사본에서만 난다 — `services/**` 에는 한 글자도 쓰지 않고 서비스 묶음을 다시 돌리지 않는다. 서비스 venv 가 하나도 없으면 skip 이 아니라 red(준비 · 78) |
| `selftest` | **위 게이트들이 실제로 red를 낼 수 있는지.** ⭑ **⟨개정 2026-09-03 · 코드리뷰 #6⟩ 집합을 손으로 적지 않는다** — 구성원 정본은 `gates/run.sh` 의 `ALL_GATES` 안에서 이름이 `*selftest` 인 것 전부다. 종전에는 이 자리에 이름 14개가 손으로 적혀 있었고 `ALL_GATES` 에는 셀프테스트가 18개 있었다 — **`autometa-loss-`·`preview-tile-slot-`·`artifact-ownership-`· `stage2-markers-selftest` 넷이 조용히 빠져 있었다.** 빠진 것이 목록의 부재로만 존재하면 아무도 그것을 세지 않는다(green-by-skip 의 목록판). **세 상태** — 선언되면 돈다 · **명시 면제는 이름과 사유와 건수를 드러낸 채** 넘어간다 · 아무 말 없으면 red. 요약줄이 `선언 N · 실행 M · 면제 K` 와 `green / red(판정) / red(준비)` 를 낸다. 현재 면제 2건 = `stage2-markers-selftest`(pipeline-worker 런타임 필요 · CI 는 `dormant-tests` 잡이 돈다) · `service-tests-selftest`(서비스 venv 필요 · CI 는 `service-tests` 잡이 돈다). ⚠ 면제는 「검사하지 않아도 된다」가 아니라 **다른 잡이 그것을 돈다**는 선언이고, `gates/run.sh all` 은 면제 없이 전부 돈다. 케이스가 종료코드 78 로 나가면 집합 전체가 78 로 나간다 — **못 돈 것을 통과로 세지 않는다** |

## 빨리 도는 것과 덜 보는 것은 다르다

게이트를 병렬로 돌린다. **검사 대상·기대값·판정 기준은 하나도 바뀌지 않았고, 바뀐 것은 실행 순서뿐이다.**
출력은 등록 순서로 되돌려 재생하므로 로그도 직렬판과 같은 줄이 같은 순서로 나온다.

- `gates/run.sh all [-j N]` — 전 게이트를 동시 N 개씩. 하나라도 red 면 red 이고, 끝에 게이트별 판정을 요약한다.
- `contract-selftest` · `event-selftest` · `boundary-selftest` · `rls-effect-selftest` 는 케이스를
  `gates/tools/_expect_pool.sh` 의 풀로 돈다. 케이스마다 자기 임시 픽스처(또는 자기 일회용 컨테이너)를
  들고 있어 서로를 볼 수 없다 — 격리는 그대로다. 종료코드가 없는 케이스는 **미실행으로 red** 다.
- `COLAB_GATE_JOBS=1` 이면 사실상 직렬이다. 재현이 필요하면 이 값을 쓴다.
- **병렬 안전성은 게이트가 선언하고 실행기가 지킨다** — 정본 = `gates/config/parallelism.toml`.
  **세 상태다**: `serial` → 단독으로 돈다(그 구간에 다른 게이트가 하나도 안 돈다) · `parallel` → 풀에서
  동시에 · **선언 없음 → 실행기가 안전한 쪽(단독)을 고르고 「미선언이라 단독으로 돌렸다」를 출력에 적는다.**
  선언 없는 것을 조용히 병렬 안전으로 가정하지 않는다 — 그것이 green-by-skip 의 병렬판이다.
- **`db-selftest` 는 병렬로 돌리지 않는다.** schema-diff e2e 묶음이 한 적용 DB 를 순서대로 훼손해 가며
  보기 때문에, 동시에 돌리면 케이스가 서로의 드리프트를 본다. 격리를 깨는 속도는 속도가 아니다.
  ⚠ **이 문장은 전에도 여기 있었는데 실행기가 읽지 않았다.** 그래서 `-j 2` 에서 red · 단독에서 green 이
  났다 — **판정이 아니라 배선이 낸 red** 이고, 앞선 거짓 red 와 같은 뿌리다. 고친 방향은 병렬도 인하도 ·
  재시도도 · 건너뛰기도 아니다: **선언을 표로 옮기고 실행기가 집행한다.** 이제 산문과 집행이 한 값을 본다.
- `gates/run.sh all` 은 시작할 때 **실행 계획**(단독 N · 병렬 M · 미선언 K)을 찍고, 요약에도 미선언 건수를
  다시 적는다. `COLAB_GATE_OUTDIR=<경로>` 를 주면 게이트별 실행 구간(`*.span`)이 남아 **「단독으로 돌았다」를
  주장이 아니라 값으로** 대조할 수 있다.
- 도구 설치 구간(`gates/.venv` · `node_modules`)에는 잠금을 걸었다(`_lock.sh`). 잠금이 없으면 둘이 동시에
  설치하다 한쪽이 「도구 없음」 red 를 내는데, 그건 검사 결과가 아니라 배선이 만든 red 다.

## selftest가 있는 이유

"전부 green"과 "전부 무력"은 구분되지 않는다. v1 CI는 DB 없이 돌아 RLS 테스트를 **green-by-skip** 했다.
각 게이트는 red fixture로 자신이 fail-closed임을 증명해야 한다.

### 셀프테스트의 판정 갈래 — 정본은 `gates/tools/_expect.sh` 하나

⭑ **⟨2026-09-03 · 코드리뷰 #6⟩ 준비 실패(종료코드 78)를 「기대한 red」로 세지 않는다.**
자체 `expect()` 를 가진 셀프테스트 12개 중 **10개가 78 을 그냥 red 로 접고 있었다.** 가르는 코드는
`_expect_pool.sh`(병렬판) 안에만 있었고, 직렬판은 각자 `got="green"; [ $rc -eq 0 ] || got="red"` 를
손으로 적었다. 보호 장치를 떼고 red 를 기대한 케이스가 **준비 실패로** red 가 났다면 그 보호 장치는
**판정된 적이 없는데 출력은 「red OK」라고 말한다** — 검사기가 아무것도 검사하지 않은 채 통과를
보고하는 모양이다.

**네 갈래** (판정 축은 하나 — 대상이 판정됐는가):

| 갈래 | 언제 | 기대에 쓰는 이름 |
|---|---|---|
| `green` | 종료 0 | `green` |
| `red` | 종료 0 아님 | `red` |
| `ready` | 종료 78(또는 준비 표식) — 환경을 기다리다 못 떴다 | `ready` |
| `미선언` | 종료 78 ＋ `cause=입력미선언` — 필요한 값이 아무 데도 선언되지 않았다 | `미선언` |

`ready` 와 `미선언` 을 가르는 이유 — **미선언은 간헐이 아니다.** 매번 같은 답을 내므로 「판정 못 함」으로
접지 않고 그 자리에서 판정한다. 기대가 `ready`·`미선언` 이 아닌데 78 이 오면 그 케이스는 **통과로도
실패로도 세지 않고** `EXPECT_READINESS` 에 쌓이며, 셀프테스트 전체가 **종료코드 78** 로 나간다
(`expect_readiness_verdict`). 실행기가 요약에서 `red(준비)` 로 갈라 적는다.

⚠ 함께 고친 형제 넷 — ⑴ `stage2-markers-selftest` 의 `expect_red` 도 78 을 「✓ red」로 셌다
(pipeline-worker venv 가 없는 체크아웃에서 **세 케이스 전부를 판정하지 않은 채 green** 이었다).
⑵⑶⑷ `contract-selftest`·`event-selftest`·`boundary-selftest` 는 풀이 `EXPECT_READINESS` 에
쌓아 둔 것을 **한 번도 읽지 않아** 못 돈 케이스가 조용히 사라진 채 green 이 나갈 수 있었다.

## CI 배선 — 어느 잡이 무엇을 판정하나 (2026-09-03 개정)

정본은 `.github/workflows/ci.yml` 이고 아래는 그 요약이다. 게이트를 잡에 **한 번씩만** 싣는다 —
같은 게이트가 두 잡에 실리면 어느 쪽 결과가 판정인지 사후에만 갈린다.

| 잡 | 조건 | 도는 것 |
|---|---|---|
| `contract-gates` | `contracts` | `contract-lint`·`contract-breaking`·`event-lint`·`event-breaking`·`seam-consistency`·`generated-up-to-date` |
| **`frontend-gates`** ⭑신설 | **`frontend` \|\| `contracts`** | `frontend-typecheck`·`frontend-test` |
| `boundary-gates` | core-api ∥ ai-service ∥ **viz-render ∥ pipeline-worker ∥ infra ∥ contracts** ⭑확대 | `import-boundary`·`banned-import`·`ai-no-lineage-write`·**`db-boundary`** ⭑신설 |
| `schema-gates` | `db` ∥ core-api | `migration-single-head`·`schema-diff`·`rls-coverage`·`rls-effect` |
| `dormant-tests` | pipeline-worker | `stage2-markers-selftest` → `stage2-markers` |
| **`service-tests`** ⭑신설 | 단위별 `<단위> \|\| contracts` (matrix 4) | `service-tests-selftest` → `service-tests-<단위>` |
| `planning-gates` | `dev-package` | `work-item-consistency`·`planning-freshness` |
| `gate-selftest` | `contracts` | `selftest` 집합(실행 17 ＋ 명시 면제 2) |

⭑ **고친 세 자리** — ⑴ 프런트 게이트 2종이 `contracts` 필터 잡 안에 있어 **`frontend/` 만 바꾼 PR 은
게이트 잡이 0개**였다(`outputs.frontend` 는 선언만 되고 소비처가 0개였다). ⑵ `db-boundary` 는 **판정을
어느 잡도 돌리지 않았고** 셀프테스트만 CI 에 있었다. ⑶ 서비스 pytest 를 도는 잡이 없었다.

## 현재 상태 (2026-08-28)

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
| **`work-item-consistency`** | ✅ 구현 (2026-08-28 · `PLAN-SoT §9 〈176〉`) | **red — 그리고 red 로 태어나는 것이 설계다.** 실측 = 대장 84항목 · ㈐ 진실원 대조 48행 · ㈏ 체크리스트 대조 41건 · ㈑ 착수 후보 33행 · ㈒ 기한 5건 · **㈓ conflict 12건** · 검사 대상 밖 **10건** ＋ 항목표가 아닌 표 1건(둘은 성격이 다르다 — 앞은 「항목 행인데 못 읽음」, 뒤는 「애초에 항목표가 아님」). ⭑ **⟨개정 2026-08-29 · 병합 회차 실측⟩ 현재 불일치는 **0 건**이고 게이트는 **green** 이다** — `S2b`·`S2` 를 `PLAN-SoT §9 〈208〉` 이, `R-1` 을 `〈207〉` 이 닫았다(`conflict` → `partial`). 함께 자란 값 — 대장 **95 항목**(84 → 95) · ㈐ 진실원 대조 **70 행** · ㈏ 체크리스트 대조 **49 건** · ㈒ 기한 **6 건** · 검사 대상 밖 **9 건**. ／ 직전 표기 ~~**3 건**(`S2b`·`R-1`·`S2` · ㈐ 67 행 · ㈏ 47 건)~~. **세는 명령은 이 게이트의 요약줄이고, 여기 적힌 숫자가 아니다** — `./gates/run.sh work-item-consistency`. 경위는 `03-HANDOFF §4` `#38`(11 → 6 → 5 → 3). ／ 이전 표기 ~~**불일치 13건 = conflict 12 ＋ ㈑ `I0` 1.**~~ ⚠ **둘 다 「고칠 위반」이 아니라 「드러난 실물」이다** — conflict 12 는 산문이 갈린 채 사람의 실측 판정을 기다리는 자리이고, `I0` 는 ⏸(prod 보류)인데 `WORK-UNITS §10` 착수 후보 표에 실려 있는 실물이다. **green 으로 만들려고 검사 대상을 줄이지 않았다.** 닫히는 조건 = 대장 `W-1` 완료 정의 ⓓ(conflict 전건 판정) ＋ `I0` 행 정리 ⭑ **⟨2026-08-30⟩ 그 조건이 충족돼 `W-1` 이 닫혔다** — conflict **0건** · 불일치 **0** · green. ⛔ **그리고 이 게이트는 그때까지 CI 에서 한 번도 돌지 않았다** — `work-item-selftest` 만 `gate-selftest` 잡의 집합 `selftest` 에 실려 「red 를 낼 수 있다」를 증명했고 **판정 자체는 어느 잡도 돌리지 않았다.** **신설 = `planning-gates` 잡**(`.github/workflows/ci.yml` · 이 게이트 ＋ 형제 `planning-freshness` · 경로 필터 `dev-package/**`·`gates/**` — 판정기가 바뀌어도 다시 판정한다). ⚠ 이 게이트가 **못 보는** 범위는 아래 절 그대로다 — 항목이 닫혔다고 덮이지 않는다 |
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
| `autometa-loss-selftest` | **17** | docker(postgres) — 일회용 DB 에 선언 스키마·시드·픽스처를 넣고 **12 케이스**를 돈다. ⓐ 대조 정본 미지정 · ⓑ 면제 선언 부재 · ⓑ' 면제 항목 부재 · ⓒ **대상 0건** · ⓓ 유실 3건 이 red, ⓔ 전건 반영 · ⓕ 이름으로 면제 가 green(**ⓕ 는 면제 건수 노출까지 본다** — 건수를 숨긴 통과는 green-by-skip 이다). ⭑ **⟨증보 2026-08-31 · `〈237〉`⟩ 갈린 배선의 fail-closed 증명 다섯** — ⓖ **스키마 전용(빈) DB 를 가리키면 red**(**`#50` 의 결함 그 자체**) · ⓗ 접속 실패 red · ⓘ **선언이 읽기 전용이 아니면 red** · ⓙ **변이① 쓰기 탐침을 떼면 그 상태가 green 이 된다**(오라클이 그 차이를 만든다는 증명) · ⓚ **변이② 읽기 전용 트랜잭션을 풀면 탐침이 실제로 쓰기를 잡는다**(사유 문구까지 대조) |
| `preview-tile-slot-selftest` | **20** | docker(postgres) — 일회용 DB 에 `preview.cog-built` 픽스처를 넣고, 픽스처 TIFF 를 **바이트로 지어**(라이브러리를 들이면 판정이 라이브러리로 옮겨간다) 10 케이스를 돈다: ⓐ 적용 DB 미지정 · ⓑ 면제 선언 부재 · ⓑ' 면제 항목 부재 · ⓒ 자리 경로 미선언 · ⓓ 없는 디렉터리 · ⓔ **자리에 타일 0건** · ⓕ 못 쓰는 타일 · ⓖ 발행 있음·쓸 수 있는 타일 0 이 전부 red, ⓗ 이름으로 면제 · ⓘ 쓸 수 있는 타일 1건 이 green 이며 **ⓗ 는 면제 건수 노출까지, ⓐ 는 원인 표식(`cause=입력미선언`)까지 본다**. ⭑ 증보 2026-09-02(`#57`) — ⓙ 경계 롤 미선언 · **ⓚ 경계 롤로 붙은 접속** · ⓛ 경계 롤 = 관리자 롤 · ⓜ 스키마 전용 DB(발행 0건) 가 red 이고, **변이① 이 종전 게이트를 재현해 같은 상태가 green 임을 보인다**(음성 증명) · 변이② ㉯ 대조 제거 · 변이③ 읽기 전용 탐침 제거 |
| `stage2-markers-selftest` | **3** | pipeline-worker venv — ⓐ 마커 0건 · ⓑ skip · ⓒ fail 셋이 전부 red 임을 증명한다. ⓑ 가 핵심이다: **green-by-skip 이 v1 의 실패 형태**다 |
| `work-item-selftest` | **14** ⭑ ⟨2026-08-31 · `〈252〉` 로 ㈔ 4건 증설: 중복·행 0건·문서 부재·§9 부재⟩ ／ 이전 ~~10~~ | 없음 (bash + python3 + pyyaml) — 대조군 1 · red 증명 13. **픽스처가 자기 산문 문서(`03-HANDOFF` · `WORK-UNITS` 스텁)를 들고 다닌다.** 레포 실물의 항목 상태는 정당하게 어긋나 있을 수 있고(그것이 이 게이트를 만든 이유다) selftest 가 거기 볼모잡히면 안 된다 — `db-selftest`·`generated-selftest` 와 같은 이유. red 픽스처의 ㈑ 는 **2026-08-27 실물 재현**(`WORK-UNITS §10` 착수 후보 표에 `I0 ⏸` 가 올라 있던 것) |
| `generated-selftest` | **9** | 없음 (bash + python3) — green 기준 케이스도 fixture 다. 레포 실물은 재생성 파이프라인 상태에 따라 정당하게 red 일 수 있어, selftest 가 레포 상태에 볼모잡히지 않게 했다 |
| `service-tests-selftest` | **9** | 서비스 venv 하나(파이썬만 빌린다) — ⓐ 통과 1건 green · ⓑ 실패 1건 red · ⓒ 수집 0건 red · ⓓ 실행 0건(전부 skip) red · ⓔ venv 부재 red(준비 · 78) · ⓕⓖ 필수 인자 부재 red · ⓗ 단위 자리 부재 red · ⓘ 요약줄 계수 노출. 픽스처 = `gates/fixtures/service-tests/` |
| `selftest` | **`ALL_GATES` 의 `*selftest` 전부 = 실행분 ＋ 명시 면제 2** | ⭑ ⟨개정 2026-09-03 · 코드리뷰 20260903-F #6⟩ **여기에 숫자를 박지 않는다** — 종전 표기 ~~「선언 19 = 실행 17 ＋ 명시 면제 2」~~ 는 `ALL_GATES` 에 셀프테스트를 하나 더하는 순간 조용히 틀린 값이 된다(문서가 실물보다 낡는 그 무늬 · `CLAUDE.md §0`). 구성원 정본은 `gates/run.sh` 의 `ALL_GATES` 안에서 이름이 `*selftest` 인 것 전부이고, 빼려면 `SELFTEST_EXEMPT` 에 이름과 사유를 적어야 한다(현재 면제 **2건** — `stage2-markers-selftest` · `service-tests-selftest`, 둘 다 CI 의 다른 잡이 돈다). **세는 명령은 게이트의 요약줄이지 이 표가 아니다** — `COLAB_GATE_JOBS=1 ./gates/run.sh selftest` 의 `선언 N · 실행 M · 면제 K` 줄이 정본이다 |

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

## work-item-consistency 가 **못 보는** 것 (정직하게)

이 게이트는 **상태가 갈렸는가**만 본다. 상태가 **옳은가**는 보지 않는다.

**보는 것** — ① 대장(`dev-package/work-items.yaml`)의 스키마·값·의존 참조 ② `WORK-UNITS §11`
완주 체크리스트 **코드 블록 안의 `<식별자> <표기>` 쌍** ③ `03-HANDOFF §1` 각 트랙 **표**의
`WU` 열과 `상태` 열(**헤더명으로 찾는다** — 트랙마다 열 수가 다르고 T-P 만 상태가 3열째다)
④ `WORK-UNITS §10` 착수 후보 표의 식별자 ⑤ 대장의 `deadline.fired` ⑥ 대장의 `conflict` 잔존
⑦ `PLAN-SoT §9` 결정 번호 행의 중복 ⭑ **⑧ ⟨증보 2026-09-01 · `〈268〉`⟩ `CLAUDE.md` 의 stage 3 표지 블록**
(`<!-- work-items:after_stage2 -->` … `<!-- /work-items:after_stage2 -->`) **↔ 대장 `stage: after_stage2` 집합.**

**못 보는 것** —

- **대장에 적힌 상태가 실물과 맞는지** — 게이트는 **문서끼리의 일치**만 본다. 세 문서가 사이좋게
  같이 틀려 있으면 green 이다. **「열려 있다」는 최근에 잰 값이 아니라 마지막으로 적은 값이다.**
  실측은 여전히 사람의 몫이다.
- **완료 정의의 품질** — `completion_def` 가 **비었는지**는 보지만(㈎ 필수 필드), 가리키는 자리에
  실제로 오라클이 적혀 있는지는 못 본다. **엉뚱한 곳을 가리키는 참조는 통과한다.**
- **evidence 가 진짜 근거인지** — `done`·`partial` 에 evidence 가 **있는지**만 본다.
  그 인용이 실제로 그 내용인지는 못 본다(「잘못된 포인터」 계열).
- **`deadline.fired` 를 누가 참으로 만드는가** — **사람이 손으로 적는다.** 조건 문장을 기계가
  판정하지 않는다(조건이 「stage 1 완료 판정과 동시」 같은 산문이라 값으로 뽑히지 않는다).
  **`fired: unknown` 은 red 가 아니라 「검사 대상 밖」으로 출력된다** — 미판정을 통과로 세지 않되,
  기계가 판정할 수 없는 것을 판정한 척하지도 않는다.
- ⭑ **⟨증보 2026-09-01 · `〈268〉`⟩ `CLAUDE.md` 의 *나머지*** — ㈕ 가 보는 것은 **표지 블록 하나**다.
  그 파일의 다른 서술(제품 성격·불변 규칙·금지 목록)은 여전히 대조 대상 밖이다. ／ 이전 표기
  ~~`CLAUDE.md` 는 아예 대조 대상이 아니다~~ — **0 에서 1 로 늘었지 전수가 된 것이 아니다.**
- **`after_stage2` 밖의 stage** — `stage1`·`stage2` 는 산문과 대조하지 않는다. 세 단을 다 옮겨
  적게 하면 `CLAUDE.md` 가 대장의 사본이 되고, **사본은 다시 갈린다.**
- **산문 안의 서술 문장** — 「~는 아직 열려 있다」 같은 문장은 **일부러 안 본다.** 정규식으로
  산문을 판정하면 오탐이 잦아지고, 오탐이 잦은 게이트는 곧 무시당한다. 표와 코드 블록만 본다.
  **따라서 같은 실수가 표 아닌 서술로 오면 못 잡는다** (`seam-consistency` G-e 와 같은 한계다).
- **`PLAN-SoT §9` 의 *내용*** — **상태의 대조 대상이 아니다.** 거기는 **결정과 근거**의 자리이고
  상태의 자리가 아니다. 결정이 상태로 옮겨졌는지는 `03-HANDOFF §3.5`(결정 이행 현황)와 사람이 본다.
  ⭑ **⟨증보 2026-08-31 · `〈252〉`⟩ 다만 그 표의 *번호*는 이제 본다** — ㈔ 가 `〈n〉` 의 중복을 센다.
  ／ 이전 표기 ~~`PLAN-SoT §9` — 대조 대상이 아니다~~ (내용은 지금도 아니다).
- **결정 번호의 *충돌 자체*** — ㈔ 는 **막지 못한다.** 두 레인이 같은 번호를 집는 일은 각자의
  작업 트리에서 벌어지고, 게이트는 둘이 한 파일에 모인 **병합 시점**에 비로소 본다.
  **그 자리가 이 검사가 사는 자리다** — 그때는 반드시 red 가 난다.
- **건너뛴 결정 번호** — **red 가 아니다.** 「번호를 비우지 않는다」는 규칙이 이 레포 어디에도
  쓰여 있지 않아 게이트가 그 규칙을 만들어 강제하지 않는다. 대신 **세어서 관측치로 출력한다**
  (실측 2026-08-31 = `〈51〉`~`〈243〉` 193행 · 빈칸 0).
- **동그라미 계열 번호(`①`~`㊻`)** — ㈔ 가 세지 않는다. 실측상 그 계열은 「확정으로 내려간 것」
  표가 `⑯`·`⑰`·`⑱`·`⑳` 를 **이관 기록으로 다시 인쇄**한다(중복 4건 · 어긋남이 아니라 이력).
  새 결정은 2026-08-24 이후 전건 `〈n〉` 이라 **막으려는 사고가 사는 계열은 그 하나다.**
- **파싱 못 한 자리** — 식별자로 시작하지 않는 행, 한 행에 식별자가 둘 이상인 행
  (`§10` 의 `C3 · C4` 같은 것), 상태 표기가 없는 행은 **「검사 대상 밖」으로 건수와 함께 출력한다.**
  **그 건수가 0 이 아니면 green 은 「전부 봤다」는 뜻이 아니다.**
- **⭑ 「검사 대상 밖」과 「항목표가 아닌 표」를 섞어 세지 않는다.** 앞은 **항목 행인데 못 읽은 것**이고,
  뒤는 **애초에 항목이 아닌 표**다(`§10.3` 재기동 계측 기준선 표가 그렇다 — 첫 열이 `축`).
  ㈑ 는 **첫 열 머리글이 `WU` 인 표만** 항목표로 본다. 이것은 범위 축소가 아니라 대상 선택이고,
  둘의 구분은 픽스처가 증명한다 — **계측표 안의 `I0` 는 green, 항목표 안의 `I0` 는 여전히 red,
  그리고 `WU` 머리글 표가 0 개가 되면 조용한 통과가 아니라 red 다.**
  ⚠ **좁히기 전에는 오탐 red 가 가능했다** — 계측 행의 축 이름이 식별자로 시작하기만 하면
  「보류 항목이 착수 후보에 재등장」으로 잘못 걸렸다. 실제 문서에서 안 터진 것은 그 행들이
  **우연히** 식별자로 시작하지 않았기 때문이지 게이트가 옳아서가 아니었다.
