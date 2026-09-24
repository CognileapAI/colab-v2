# gates — 경계를 기계가 지킨다

v1(PoC)에서 터진 버그는 전부 **"관례로 지키기로 했던 것"** 이었다. v2는 관례를 두지 않는다.

| 게이트 | 무엇을 막나 |
|---|---|
| `contract-lint` | seam 스펙 오류 |
| `agent-bridge` | Codex/Claude 연결, 완료 훅 및 배포 자동 알림의 진입점·상태·중복 방지 |
| `harness-contract` | `.agents/harness.yaml`의 공통 원본·adapter·필수 gate·0/1/78 계약 누락과 경로 이탈 |
| `harness-contract-selftest` | malformed config·빈 필수 gate·누락 adapter를 조용히 통과시키는 회귀 |
| **`gate-host-mutex-selftest`** ⭑신설 | **호스트 뮤텍스가 `serial` 선언을 프로세스 경계 너머로 집행함을 증명한다** — **ⓐ 점유 중 호출은 기다리다 red(준비 · 78)** 이고 **실경과가 상한 이상**이다(표식만 grep 하지 않는다) · **ⓑ 점유가 풀리면 green 이고 `waited` ≥ 1** — 이 두 시간값이 「잠금이 실제로 걸렸다」의 값 증거다 · ⓒ 잠금 파일을 열 수 없으면 78 · ⓓ `flock` 부재면 78(PATH 수술 · 면제 변수가 없으므로 주입 훅이 없다) · **ⓔ 면제는 선언(`parallel`)과 `COLAB_GATE_MUTEX_HELD=1` 둘뿐이다 — `COLAB_GATE_SUMMARY_CHILD=1` 만 있는 호출은 면제되지 않는다**(그것이 면제면 `task` 경로의 `serial` 게이트가 전부 무잠금이다) · ⓕ 배출처를 선언한 레인 경로에서도 **부모**가 잡는다 · **ⓖ 선언표를 못 읽으면 단독 호출도 그 메모를 stdout 에 찍고 안전한 쪽(잠근다)으로 접는다** — 종전에는 그 메모를 `all` 만 찍어 단독 호출이 침묵했고, 접은 근거가 실행기 안에만 남았다. · **ⓗ `task` 경로의 모양(`COLAB_GATE_SUMMARY_CHILD=1`)에서도 잠금 사실이 stdout 에 남고 줄은 정확히 1회다** — 요약 줄이 래퍼 블록 안에 있던 동안 전수 회차의 71게이트 로그 어디에도 잠금 건수가 0건이었다(2026-09-18 실측). 대상 게이트는 `exec-bit` 이고 선언표는 픽스처 toml(`COLAB_GATE_PARALLELISM_MANIFEST`)을 물린다 — 실제 `parallelism.toml` 에서 `exec-bit` 은 `parallel` 이므로 이 셀프테스트가 green 이면 **실행기가 표를 실제로 읽은 것**이다. `TMPDIR` 을 자기 `mktemp -d` 로 물려 **실제 호스트 잠금을 한 번도 잡지 않는다** |
| `operator-notifications` | 운영자 사건 20개 선언과 영속 전달·일일 보고·AWS 정규화·두 loopback Slack 수신처 검증 |
| `operator-notifications-selftest` | 필수 사건 manifest 누락을 판정 실패로 거부하는 음성 검사 |
| `contract-breaking` | emit된 스펙이 frozen seam과 충돌 |
| `event-lint` | 이벤트 계약(`contracts/events/**`)의 스키마 오류 · `$ref` 미해석 · 인스턴스 계약 위반 |
| `event-breaking` | 이벤트 계약의 `$defs` 단위 파괴적 변경 (규칙표 = `dev-package/sessions/D2b.md §2`) |
| `generated-up-to-date` | 생성물이 계약보다 낡음 |
| `import-boundary` | 도메인 간 직접 참조 |
| `banned-import` | core-api의 geo 라이브러리 |
| **`db-boundary`** | **배포 단위가 허용된 DB 체인 밖에 접속을 선언** (정본 = `gates/config/db-boundaries.toml`). `import-boundary` 가 못 보는 계열 — 횡단이 import 가 아니라 **DB 접속**일 때 |
| **`ai-no-lineage-write`** | **D10 → D4 쓰기 경로 존재** (음성) |
| `migration-single-head` | 마이그레이션 head 분기 (platform / ai 각각) |
| `schema-diff` | 선언 스키마 ↔ 적용 DB 드리프트 (**체인별로 각각** — `COLAB_APPLIED_DB_URL_PLATFORM` · `_AI` 둘 다 필요). ⭑ **⟨증보 2026-09-08 · `WU-C6` · 질의 17⟩ 비교 전에 적용 DB 를 `alembic upgrade head` 로 올린다** — 종전에는 「누군가 이미 올려 뒀다」를 가정하고 바로 덤프했고, 그래서 이 회차의 마이그레이션이 아직 안 올라간 상태에서는 **선언 변경 자체가 드리프트로 읽혔다**(게이트가 낸 red 가 「스키마가 갈라졌다」가 아니라 「아직 안 올렸다」였고 둘이 안 갈렸다). 준비 단계가 실패하면 그 자리에서 red 이고, `alembic` 부재·체인 자리(`db/<체인>/alembic.ini`) 부재는 **red(준비 · 78)** 다. 생략(`COLAB_SCHEMA_DIFF_SKIP_UPGRADE`)은 **명시 선언일 때만** 가능하고 그 사실이 출력에 그대로 찍힌다 — 조용한 폴백은 없다 |
| **`migration-drift`** | **되돌리면 red 가 나는가 — 마이그레이션 오라클(`db/<체인>/tests/*-drift.sh`)을 게이트가 실제로 돈다** (`WU-C6` · 질의 3·4·30). ⭑ **오라클 12벌(platform 11 · ai 1)이 레포에 있는데 `ALL_GATES` 어디에도 없었다** — 시험이 레포에 있는 것과 게이트가 그것을 판정하는 것은 다른 사실이다(`frontend-test`·`service-tests-*` 가 닫은 것과 같은 계열). 아무도 돌리지 않는 오라클은 깨진 채로 조용히 늙는다. 세는 단위 = **`*-drift.sh` 파일 1건**, 기대 건수의 정본은 `gates/config/migration-drift.toml`(체인별 `min` · `min = 0` 은 쓰지 않는다). 요약줄이 **체인별로 `오라클 N · 실행 N · 실패 M`** 를 내고 합계를 덧붙인다. **red 조건** — 오라클 하나라도 비영 종료(실패한 오라클을 **이름으로** 낸다) · 실측 건수 < 선언 `min`(「줄었다」를 기대값 인하로 덮지 않는다) · **대상 0건**(볼 것이 없으니 통과가 아니라 조회가 빗나간 것이다) · `alembic`·`docker` 부재는 skip 이 아니라 **red(준비 · 78)**. ⚠ 이 게이트는 적용 DB 를 보지 않는다 — 오라클이 저마다 **일회용 postgres**(`s1db_` 접두사 · 호스트 포트 0 · staging 무접촉)를 세운다. 선언 ↔ 적용 대조는 `schema-diff` 의 일이다 |
| **`migration-drift-selftest`** | 위 게이트가 red fixture 로 fail-closed 임을 증명한다 — **ⓐ 대조군 green · ⓑ 되돌린 델타(오라클 1벌 비영 종료) red · ⓒ 대상 0건 red · ⓓ `alembic` 부재 red(준비 · 입력미선언) · ⓔ 실측 건수 < 선언 최소 red · ⓕ `docker` 부재 red(준비) · ⓖ 요약줄이 계수를 낸다**. 케이스마다 `mktemp -d` 안에 **가짜 `*-drift.sh`** 를 짓고 `COLAB_MIGRATION_DRIFT_DIRS`/`_MIN` 으로 물린다 — `db/**` 에는 한 글자도 쓰지 않고 컨테이너를 하나도 띄우지 않는다(실물 오라클을 다시 돌리지 않는다) |
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
| **`work-item-consistency`** | **개발 항목 상태의 대장 ↔ 산문 불일치** (정본 = `dev-package/work-items.yaml`). stage 허용값은 `stage1`·`stage2`·`after_stage2`·`backlog`·`out_of_scope`다. `backlog`는 전체 항목 수에는 남되 Stage 1·2·3과 따로 집계하며, open 상태와 상태·의존 참조 검사를 그대로 받는다. 기존 미분류 값 `unknown`은 별도 집계하고 그 밖의 미지원 값은 red다. ⭑ **⟨증보 2026-09-01 · `PLAN-SoT §9 〈268〉`⟩ 검사 8종** — 종전 일곱 ＋ **㈕ `CLAUDE.md` stage 3 표지 ↔ 대장 `stage: after_stage2` 집합 대조**(표지 부재·미폐쇄·`CLAUDE.md` 부재는 red). ／ 이전 표기 ~~⭑ ⟨증보 2026-08-31 · `PLAN-SoT §9 〈252〉`⟩ 검사 7종~~ — ㈎ 대장 스키마 · ㈏ `WORK-UNITS §11` 완주 체크리스트 대조 · ㈐ `03-HANDOFF §1` 진실원 표 대조 · ㈑ `⏸`(하지 않기로 한 것)의 착수 후보 표 혼입 · ㈒ 기한 발동인데 안 열린 항목 · ㈓ `conflict` 잔존 · **㈔ `PLAN-SoT §9` 결정 번호 `〈n〉` 중복**. ／ 이전 표기 ~~검사 6종 — ㈎~㈓~~. **상태 관리가 「관례를 두지 않는다」의 마지막 사각지대였다** |
| **`frontend-fixture-reach`** | **운영 진입점(`frontend/src/main.tsx`)에서 실제로 닿는 모듈에 개발용 픽스처가 섞여드는가** (레인 E · `CODE-REVIEW-20260903-E.md §5·§8`). 판정부는 `frontend/scripts/reachable-from-entry.mjs`(레인 E 신설)를 **그대로** 돈다 — 상대 import 를 따라가 닿는 모듈을 세고, `fixture.ts`·`graphFixture.ts`·`localEngine.ts` 에 하나라도 닿으면 rc=1. ⭑ **이 워커는 사람이 손으로 부를 때만 돌았다** — rc 로 말하도록 이미 짜여 있는데 아무도 게이트로 세지 않으면 폴백 회귀는 사람이 그 명령을 다시 칠 때까지 아무도 모른다. **red 조건** — 도달 모듈이 금지 목록에 닿음 · 진입점 말고 도달 0건(그래프가 비면 검사한 것이 아니다) · `tsconfig.json` 의 `paths`/`baseUrl` 또는 `vite.config.ts` 의 `resolve.alias` 선언(이 워커는 **상대 import 만** 따라가 별칭 뒤를 못 본다 — 오늘은 둘 다 없음을 레인 E 가 실측했다). `node`·판정부 스크립트·진입점 부재는 skip 이 아니라 **red(준비 · 코드 78)** |
| **`frontend-design-lint`** ⭑신설 | **토큰 정의가 정본 `frontend/src/shell/tokens.css` 한 곳에 있고, 참조되는 토큰이 모두 정의돼 있으며, 라이트 색 토큰마다 다크 값이 있는가** (spec `S-DESIGN-STRUCTURE-P1-20260924` · 대안 B). **왜 있는가** — 2026-09-24 실측으로 정본 밖 7개 화면 CSS 의 `:root` 에 토큰 정의 77건이 흩어져 있었고(다크 값만 정본에 있는 이름 17종), BF-13 시험(`shared-css-tokens.test.ts`)은 화면 파일끼리 값이 같은지만 봐 새로 흩어지는 것을 막지 못했다. 판정부 = `frontend/scripts/design-lint.mjs`(zero-dependency · node 만). **세는 단위** — 대상 = `git ls-files --cached --others --exclude-standard` 의 `frontend/src/**/*.css`(주석 제거 뒤) · a·b 는 선언/참조 1건 · c 는 이름 1개 · d 는 셀렉터 블록·`@import` 1건. **red 조건** — a. tokens.css 밖 `:root` 안의 `--*:` 정의, 또는 화면 범위 규칙에서 정본 계열 이름(`--color-`·`--space-`·`--text-`·`--radius-`·`--font-`·`--shadow-`·`--leading-`·`--tracking-`·`--fg-`·`--bg-`·`--accent-`) 정의 · b. 어디에도(정본·다크·화면 루트 범위·TS/TSX 의 `'--x'` 문자열) 정의되지 않은 `var(--x)` 참조(폴백 유무 무관) · c. 라이트 `:root` 의 색 계열 이름(`--color-`·`--fg-`·`--bg-`·`--accent-`·`--shadow-`)이 다크 블록에도, 별칭(`var()` 대상이 덮임)으로도, 면제 목록(`gates/fixtures/frontend-design-lint/same-in-dark.txt` · 이름 · 사유)에도 없음 · 다크에만 있는 이름 · 면제 목록의 구멍 셋(사유 빈칸 · 라이트에 없는 낡은 항목 · 다크에 이미 있는 항목) · d. tokens.css 밖 `:root` 셀렉터(`html:root` 등 compound 포함) · tokens.css 밖 전 CSS 의 `@import`(P2a · 셸이 더는 정본을 `@import` 하지 않는다 · `@layer` 블록 뒤의 `@import` 는 무효다) · f. (P3 · spec `S-DESIGN-STRUCTURE-P3-20260924`) tokens.css 밖 CSS 선언 값의 색 리터럴 — hex(3·4·6·8자리) · `rgb()`·`rgba()`·`hsl()`·`hsla()`·`hwb()`·`lab()`·`lch()`·`oklab()`·`oklch()`·`color()`·`color-mix()`(색 인자가 전부 `var()`·`transparent`·`currentColor` 인 토큰 혼합은 제외) · CSS 표준 색 이름 148개 — 직접 값이든 `var()` 폴백이든(1건 = 리터럴 1개 · 문자열·`url()` 안과 글꼴·애니메이션·격자 이름 속성은 제외) · 제외 키워드 `transparent`·`currentColor`·`inherit`·`initial`·`unset` · 면제는 같은 목록의 `f · 파일 · 선택자 · 속성 · 리터럴 · 사유` 줄(사유 빈칸 · 걸리는 리터럴 없는 낡은 항목은 red · 사유 없는 줄은 면제하지 않는다) · g. (P3) `src/**/*.tsx` 의 JSX `style` 속성과 JSX 펼침 속성 안의 `style` 키마다 값이 `--*` 키만 가진 객체 리터럴이 아니면 1건(축약형 `{ width }` · 펼침 · 비리터럴 계산 키 · 객체 아닌 값 포함 · `as`·괄호는 벗겨 읽음) — 판정은 `typescript` devDependency 의 AST(정규식 아님)이고 `--*` 키만인 것은 변수 대입 v 로 센다 · e. (P2b · spec `S-DESIGN-STRUCTURE-P2B-20260924`) `src/shell/primitives.css` 밖 CSS 의 프리미티브 **맨 정의** — 선택자 목록의 인자(1건 = 인자 1개)가 `:is()`/`:where()` 를 펼친 뒤 compound 하나이고, 그 compound 가 프리미티브 목록(`gates/fixtures/frontend-design-lint/primitives.txt` · 한 줄에 클래스 하나 · 접두 표기 `.chip--*` · 계열을 옮긴 커밋마다 그 계열만 더한다)의 클래스 + 가상 클래스/요소 · 속성 선택자만으로 되어 있음(`.btn` · `.btn:hover` · `.chip--warning` · `:is(.inp, .sel)`) — `:not()`·`:has()` 인자는 보지 않고, 목록 밖 클래스·요소·id 와 섞인 compound(`.btn.foo` · `button.btn`)와 조상·자손 문맥(`.memgrid .btn`)은 허용 · `primitives.css`·`base.css` 안의 `!important` 1건 · 면제는 따로(`primitives-exempt.txt` · `파일 · 선택자 · 사유` · 사유 빈칸은 면제하지 않고 red · 걸리는 맨 정의 없는 낡은 항목 red) · h. (P5 · spec `S-DESIGN-STRUCTURE-P5-20260924`) `docs/design-system.md` 의 생성 표지 두 블록(`<!-- generated:tokens -->` · `<!-- generated:primitives -->`)이 실물(`tokens.css` · `primitives.css` · `primitives.txt` · `primitives-exempt.txt` · `same-in-dark.txt`)에서 다시 만든 표와 다름(1건 = 갈린 블록 1개 · 판정부 `frontend/scripts/design-docs.mjs --check` · 블록 밖 손글은 비교하지 않는다 · 입력 sha256 이 블록 안에 있어 입력의 주석만 바꿔도 다시 쓰기가 필요하다 · h 의 입력은 저장소 문서·실물이고 `COLAB_FRONTEND_DIR` 픽스처와 무관 · 문서 경로만 env `COLAB_DESIGN_LINT_DOC`). `@layer` 블록은 투명하다(층 안 규칙도 같은 판정). 요약줄에 면제 건수와 「범위 색 토큰 n(다크 미검사)」·「색 리터럴 f(면제 m) · 인라인 g(변수 대입 v) · 프리미티브 맨 정의 밖 e(면제 m) · 문서 표 갈림 h」를 낸다. **78 조건** — `node`·판정부 스크립트·면제 목록 부재 · 대상 CSS 0건 · 대상 목록(Git)에 있으나 디스크에 없는 CSS(추적 중 삭제) · `typescript` 를 불러오지 못함(P3) · 프리미티브 목록·프리미티브 면제 목록 부재(P2b) · 문서 표 판정부·문서·표지 짝·h 입력 파일 부재(P5)는 skip 이 아니라 **red(준비 · 코드 78)**. **못 보는 것** — 화면 루트 범위로 내린 색 값 토큰(리터럴 색)은 c 의 대상이 아니다 — 그 건수를 요약줄에 「범위 색 토큰 n(다크 미검사)」로 따로 낸다(그 값의 리터럴은 f 가 센다) · 색 계열 접두사가 아닌 정본 이름(`--up-*` 등)의 다크 짝 · 셀렉터가 실제 DOM 에서 루트 범위 안에 있는지(범위 토큰의 도달성은 캡처 대조가 본다) · f: 시스템 색(`Canvas` 등)·TSX/TS 안의 색 문자열·색 아닌 폴백 리터럴(px 등) · g: 펼침 속성 밖에서 만든 객체를 펼치는 경우(`{...props}` 안의 style)는 키를 읽을 수 없어 보지 않는다 · `.ts` 의 `createElement`·DOM `el.style.x =` 대입 · 대상 TSX 0건은 78 이 아니다(계수 줄 `tsx=` 로 드러낸다) |
| **`frontend-test`** | **화면 동작 시험(`frontend/test` · vitest)이 게이트 안에서 도는가** — `frontend/package.json` 의 `test`(`vitest run`) 와 **같은 명령**을 레포의 `vite.config.ts`(jsdom · `include`=`test/**/*.test.ts(x)`) 그대로 돈다. ⭑ **2026-09-03 화면 검수** — 시험 24파일 446건이 이미 있는데 **게이트 39개 어디에도 없었다.** `frontend-typecheck` 는 타입만 보고 라벨·문구·표기 규칙 같은 **화면 동작**은 아무도 재지 않았다 — 그래서 정본과 어긋난 화면 30행이 전 게이트 green 인 채로 staging 에 서 있었다. **갈림 방지** — `package.json` 의 `test` 가 `vitest run` 으로 시작하지 않으면 red. ⭑ **수집된 시험 0건도 red** — 통과 0·실패 0 은 「전부 통과」가 아니라 「아무것도 검사하지 않았다」다(`CLAUDE.md §4` green-by-skip). 통과 건수를 요약에서 읽지 못해도 red(`CLAUDE.md §5`). `node_modules`·`.bin/vitest` 부재는 skip 이 아니라 **red(준비 · 코드 78)**. ⚠ jsdom 밖(실제 CSS 레이아웃·휠 이벤트·캔버스 렌더)은 이 게이트가 보지 않는다 — ⭑ ⟨개정 2026-09-08⟩ 그 자리는 **더 이상 물음이 아니다.** 되먹임 고리는 `frontend-visual`(= `agent-browser`)이 받는다 — Playwright 를 새로 들이지 않는다(`.claude/skills/design-review/SKILL.md §2-5`). ⚠ 그 게이트가 재는 것은 **글자 크기와 대비**이고, 스크린샷은 **근거**이지 판정이 아니다 — 누름 피드백·드래그 추적 같은 항목의 판정은 사람이 한다 |
| **`frontend-visual`** ⭑신설 | **실화면에서 글자가 13px 이상이고 대비가 4.5:1 이상인가** — `agent-browser`(vercel-labs)로 페이지를 열어 **computed** 글자 크기와 **상속 배경 기준** 대비를 재고, 라이트·다크 스크린샷을 근거로 남긴다. 판정부는 design-review 스킬의 `scripts/live_audit.sh` ＋ `live_probe.js` 를 **그대로** 돈다 — 게이트가 자기 사본을 만들면 「게이트가 보는 것」과 「사람이 보는 것」이 갈린다(`frontend-fixture-reach` 와 같은 원칙). **입력의 세 상태** — `COLAB_VISUAL_URLS` 로 선언하면 검사한다 · `COLAB_VISUAL_EXEMPT=1` 로 **명시 면제**하면 건수(페이지 0건)를 드러낸 채 넘어간다 · **아무 말 없으면 red(준비 · 입력미선언 · 78)** 다. **red(판정)** = 허용 목록(`gates/fixtures/frontend-visual/allow.txt` · 셀렉터 접두사) 적용 후 `counts.small > 0` 또는 `counts.lowContrast > 0` · probe 실패 페이지 존재 · 선언된 URL 이 있는데 probe 결과 0건. `agent-browser`·판정부·`python3` 부재는 skip 이 아니라 **red(준비 · 코드 78)**. ⚠ 앱을 향해서는 **읽기 전용**이다 — 클릭·입력·폼 제출을 하지 않는다(`SKILL.md §2-5`·§4) |
| **`backup-cron-streak`** | **크론 무인 백업의 연속 GREEN 이 지금도 서 있는가** (`PLAN-SoT §9 〈286〉` ① · 등재 `〈296〉`-㉴). ⚠ **이 게이트는 다시 재지 않는다 — 읽는다.** 판정 입력은 크론 04:40 회차(`infra/staging/backup/check-cron-streak.sh`)가 `~/colab-v2-backups/staging-backup.log` 에 남긴 **마지막 요약줄** 하나다. 재실행하지 않는 이유 = 게이트 호스트가 보관처를 못 보면 재실행은 **항상 RED** 가 되고 그때 「보관처 없음」과 「연속 깨짐」이 **안 갈린다**(`render-latency` 와 같은 「보관처 있는 호스트에서만 도는 게이트」 배치). 세는 단위 = **`크론 연속 GREEN:` 으로 시작하는 요약줄 1건**. ⚠ **요약줄 자체에는 시각이 없다** — 시각은 `run-scheduled.sh` 가 **그 다음 줄**(`… check-cron-streak.sh 성공|실패`)에 적고, 게이트는 둘을 **짝으로** 읽는다. **짝을 못 찾으면 red** 다(나이를 못 재는 GREEN 은 판정이 아니다). red 조건 넷 — ⓐ 로그 부재·요약줄 0건(**대상 0건은 통과가 아니다**) ⓑ 요약줄이 **36시간**보다 오래됨(일 1회 ＋ 12h 여유 · green-by-stale 차단) ⓒ 요약줄이 RED ⓓ 요약줄이 **「검사 0건 · 승인된 SKIP」 GREEN**(`lib.sh verdict` 의 SKIP-GREEN 을 그대로 받지 않는다). 근사 한계(무인 판별 창 `COLAB_CRON_WINDOW_MIN`)는 **게이트 출력에 그대로 옮긴다** — 안 보이는 근사는 거짓말이 된다 |
| **`exec-bit`** | **`.sh` 의 실행비트가 인덱스에 있는가** (D5 · `rules/colab-rules.md §4-3` · 스펙 C 「삭제한 훅과 대체」). 판정 = `git ls-files -s -- '*.sh'` 에 `100644` 이 한 줄이라도 있으면 red(판정) — 위반 파일을 **이름으로** 낸다. ⭑ **왜 게이트인가** — 레포가 NTFS(drvfs) 위라 `core.filemode=false` 이고 로컬 `chmod +x` 는 **인덱스에 남지 않는다.** 100644 로 커밋된 스크립트는 로컬에서 `bash <파일>` 로 불려 통과하고 **Actions 가 직접 exec 하는 자리에서만** `Permission denied`(exit 126)로 죽는다 — 로컬 green 과 CI red 가 갈리는 자리다. 2026-09-03 draft PR #2 실측: 스크립트 20개 중 12개가 `main` 에도 100644 였고 그 잡이 미실행이라 잠복해 있었다. v1 의 `exec-bit-guard` 훅(=`git commit` 문자열 가로채기)은 **취약해서 철회**됐고 이 게이트가 그 자리를 받는다. **대상 0건도 red**(`.sh` 가 0건일 리 없으므로 조회가 빗나간 것이다 · green-by-skip 금지). 체크아웃이 아니면 준비 red(78). 고치는 법 = `git update-index --chmod=+x <파일…>` 뒤 커밋 |
| **`exec-bit-selftest`** | 위 게이트가 red fixture 로 fail-closed 임을 증명한다 — **ⓐ 뿌리의 100644 red · ⓑ 하위 폴더의 100644 red · ⓒ 대상 0건 red · ⓓ 전부 100755 green**. 케이스마다 `mktemp -d` 안에 **일회용 레포**를 `core.fileMode=false` 로 세우고 게이트에 `COLAB_EXEC_BIT_ROOT` 로 물린다 — 이 레포의 인덱스에는 한 글자도 쓰지 않는다 |
| **`harness-eval`** ⭑신설 | **하네스 자체의 문안이 실제 행동을 바꾸는가** — `CLAUDE.md`·`.claude/skills/**`·`.claude/hooks/**`·`.claude/agents/**` 를 고쳤을 때 그 개정이 판정을 바꾸는지를 **실과제**(`eval/harness/H??-*/` · 과제당 `claude -p` 2회)로 잰다. 수용 근거가 「읽어 보니 낫다」에서 **「개정 전 red → 개정 후 green」**으로 바뀌는 자리다(intent `dev-package/intent/2026-09-08-harness-evals.md`). 판정부는 `eval/harness/run.sh`(WU-D5)를 **그대로** 돌고 그 종료코드를 전달한다 — 게이트가 자기 사본을 만들면 「게이트가 보는 것」과 「사람이 보는 것」이 갈린다(`frontend-visual` 과 같은 원칙). **입력의 세 상태** — `COLAB_HARNESS_EVAL=1` 이면 돈다(**실제 모델 호출** · 시간·달러 상한은 `COLAB_EVAL_TIMEOUT`·`COLAB_EVAL_BUDGET` 이고 **미선언은 red(준비)**) · `COLAB_HARNESS_EVAL_EXEMPT=1` 이면 **명시 면제**로 과제 건수를 드러낸 채 넘어간다 · **아무 말 없으면 red(준비 · 입력미선언 · 78)**. 값 대조는 **`=1` 하나뿐**이다(`true`·`yes` 는 미선언 — 세 상태가 두 상태로 무너지는 자리). **red(판정)** = 과제 2/2 가 아님(1/2 「불안정 — 과제 설계 결함」 · 0/2 「실패」) · **면제인데 과제 0건**(대상 0건은 통과가 아니다). **red(준비 · 78)** = 상한 변수 미선언 · 세 파일(`task.md`·`fixture/`·`expect.sh`) 부재 · 시간·예산 상한 초과 · 결과가 오류(`is_error:true`). ⚠ **승격 전이다** — 로컬 `all` 과 CI 잡은 지금 **면제 모드**로 돌고, 실행 모드(`COLAB_HARNESS_EVAL=1`) 전환은 과제 20건이 **3회 연속 2/2 green** 인 뒤의 **별건**이다(intent Q10) |
| **`harness-eval-selftest`** ⭑신설 | 위 게이트가 red fixture 로 fail-closed 임을 증명한다 — **ⓐ 면제 선언 ＋ 과제 0건 red(판정) · ⓑ 면제 선언 ＋ 과제 3건 green(출력에 `과제 3건` — 조용한 건너뛰기 금지) · ⓒ 실행 선언 ＋ 스텁 `sleep` 4s > 상한 1s → red(준비 · 78 · 러너 exit 그대로 전달) · ⓓ 둘 다 미선언 red(준비 · 입력미선언)**. 과제 뿌리는 `mktemp -d` 안이고(`COLAB_EVAL_TASKS_DIR`) `claude` 는 `PATH` 앞의 스텁이다 — **실제 모델 호출 0회** · `eval/harness/` 에는 한 글자도 쓰지 않는다. ＋ **CI 필터 대조**(`gates/tools/ci-filter-check.py`) — `.github/workflows/ci.yml` 의 `harness` 필터가 `CLAUDE.md`·`.claude/skills/**`·`hooks/**`·`agents/**` 를 잡고 `frontend/**`·`services/**` 를 안 잡는지, `changes` 잡 `outputs.harness` 와 잡 `harness-eval` 의 조건·시크릿 참조·`continue-on-error` 부재까지. ⚠ `dorny/paths-filter` 자체는 로컬에서 돌지 않는다 — **실제 GitHub 평가는 `[미상]`** 이고 여기서 재는 것은 glob 문법의 뜻이다 |
| **`service-tests-core-api`** · **`service-tests-ai-service`** · **`service-tests-viz-render`** · **`service-tests-pipeline-worker`** | **서비스 pytest 묶음이 CI 안에서 도는가** (2026-09-03 코드리뷰 #6). ⭑ **종전에는 `grep -rn pytest .github/` = 0 이었다** — CI 가 도는 pytest 는 `stage2-markers` 의 `stage2 and not e2e` 부분 집합 하나뿐이었고, **서비스 측 시험 함수 1102 중 871 이 CI 에서 한 번도 실행되지 않았다**(core-api 51파일·533함수 · ai-service 13·133 · viz-render 28·205). 시험이 레포에 있는 것과 CI 가 그것을 판정하는 것은 다른 사실이다 — `frontend-test` 가 닫은 것과 같은 계열. 판정부 = `gates/tools/service-tests.sh <단위> <표식 선택자>`, 선택자의 정본은 `gates/run.sh` 의 case 한 곳(viz `not e2e and not perf` · pipeline `not e2e and not dbint` · ai `not dictdb` · core-api `not e2e`). **red 조건 여섯** — ⓐ 단위·선택자 인자 부재(빈 선택자를 「전부」로 읽지 않는다) ⓑ 단위·`tests/` 자리 부재 ⓒ **수집 0건** ⓓ **실행 0건(전부 skip)** ⓔ failed·errors ⓕ pytest 비영 종료. **skipped·deselected 는 막지 않고 요약줄에 건수로 드러낸다** — 감춘 건너뜀이 green-by-skip 이지 드러낸 건너뜀은 판정의 일부다. venv 부재는 skip 이 아니라 **red(준비 · 78)**. `core-api` 는 게이트가 **일회용 Postgres 를 스스로 세운다** (`_pg.sh` ＋ `services/core-api/tests/fixtures/setup-db.sh` — 포트 미공개 · PGDATA tmpfs · `--rm` ＋ trap · **접속 문자열을 출력하지 않는다**). ⚠ 뺀 표식은 **취소가 아니다** — 표식은 붙어 있고 그 환경이 있는 실행에서 함께 돈다. `stage2-markers` 는 그대로 남는다(휴면 모듈의 시험이 **계속 도는지**를 재는 다른 질문이다) |
| **`service-tests-selftest`** | 위 네 게이트가 red fixture 로 fail-closed 임을 증명한다 — **ⓐ 통과 1건 green(대조군) · ⓑ 실패 1건 red · ⓒ 수집 0건 red · ⓓ 실행 0건(전부 skip) red · ⓔ venv 부재 red(준비 · 78) · ⓕ·ⓖ 필수 인자 부재 red · ⓗ 단위 자리 부재 red · ⓘ 요약줄이 계수를 낸다**. 픽스처 원본 = `gates/fixtures/service-tests/`(트리 넷 ＋ README), 판정은 `mktemp -d` 사본에서만 난다 — `services/**` 에는 한 글자도 쓰지 않고 서비스 묶음을 다시 돌리지 않는다. 서비스 venv 가 하나도 없으면 skip 이 아니라 red(준비 · 78) |
| **`seed-plan-drift`** ⭑신설 | **참조자료 정본 md 4건과 커밋된 등재표(`dev-package/tools/dev-seed/plan-manifest.yaml`)가 갈라졌는가** — `build_plan.py` 는 **아무 게이트도 부르지 않는 생성기**였고 그 생성물은 커밋돼 러너가 읽는다. 그래서 md 를 고치고 생성기를 다시 돌리지 않으면 **낡은 등재표가 그대로 통과한다** — 대조하는 자리가 「사람이 기억해서 다시 돌리는 것」 안에만 있었다(`frontend-test`·`frontend-typecheck` 가 닫은 것과 같은 계열의 green-by-skip). **보는 것 셋** — ⑴ md 안의 사람이 읽는 표 ↔ 기계 블록(이름·건수·바이트) ⑵ md 만으로 등재표를 되만들어 커밋된 것과 **한 줄 단위 대조**(다르면 갈린 줄을 낸다) ⑶ 총계 **데이터셋 28 · 계보 18간선**. ⭑ **총계는 md 에서 세고 플래그로 낮출 수 없다** — 기본값 아닌 `--expect-datasets`·`--expect-edges` 로 생성물을 쓰려는 호출은 생성기가 **종료코드 4** 로 막는다(짧은 계획으로 총계 검사를 통과시키는 길). 판정부는 `build_plan.py --check-manifest` 를 **그대로** 돈다 — 게이트가 자기 사본을 만들면 「게이트가 보는 것」과 「사람이 보는 것」이 갈린다(`frontend-visual` 과 같은 원칙). **입력의 세 상태** — `COLAB_REF_ROOT` 가 실재하면 글롭이 맞히는 파일 수·바이트까지 **실물 대조** · `COLAB_SEED_PLAN_NO_FILES=1` 이면 **명시 면제**로 「실물 대조 미실행(참조자료 미장착)」을 요약에 드러낸 채 ⑴⑵⑶ 만 판정 · **아무 말 없으면 red(준비 · 입력미선언 · 78)**. 값 대조는 **`=1` 하나뿐**이다. ⚠ ⑴⑵⑶ 은 **참조자료 드라이브 없이 돈다** — md 블록이 선언한 값만 쓰기 때문이고, 그래서 면제가 등재표 드리프트를 덮지 않는다. CI 는 참조자료가 없어 **면제 모드**로 돈다(`planning-gates` 잡) |
| **`seed-plan-drift-selftest`** ⭑신설 | 위 게이트가 red fixture 로 fail-closed 임을 증명한다 — **ⓐ 등재표를 손으로 고침(`expect_bytes` 한 칸) red(판정 · 출력에 `MANIFEST-DRIFT` 와 갈린 줄) · ⓑ md 에서 데이터셋 한 행 삭제(표＋블록) red(판정 · 출력에 총계 기대값 `28`) · ⓒ 참조자료도 면제도 미선언 red(준비 · 입력미선언 · 78) · ⓓ 명시 면제 green(요약에 「면제」와 「실물 대조 미실행(참조자료 미장착)」)**. ⚠ ⓐⓑ 는 **면제를 선언한 채로** 돈다 — 면제가 md→등재표 대조까지 덮지 않음을 함께 증명한다. 픽스처 원본 = `gates/fixtures/seed-plan-drift/{green,red}/`, 판정은 `mktemp -d` **사본**에서만 난다(이 레포 경로에는 공백(`00 CoLAB`)이 있고 원본을 그 자리에서 고치면 레포가 더러워진다 — 끝에 원본↔사본 동일성까지 본다). **참조자료 드라이브를 한 번도 읽지 않는다** — 네 케이스 전부 `COLAB_REF_ROOT` 를 비운다 |
| **`dev-reseed-selftest`** ⭑신설 | **`dev-package/tools/dev-reseed/` 의 판독부가 red fixture 로 fail-closed 임을 증명한다.** 왜 있나 — 그 판독부(요약줄 파싱·계획 계수 대조·미리보기 판정)는 **어느 검사에도 걸리지 않았고**, 전부 dev 를 한 번 돌려 보고서야 드러날 자리였다(검사가 사람의 실행 안에만 있으면 그것은 검사가 아니다 · `CLAUDE.md §4`). **픽스처 셋** — ⓐ `tests/doctor-parse.sh` = `deploy_doctor` 실물 출력 표본(`DeployReport`·`verdict` 로 찍은 것 · `tests/fixtures/`)으로 요약줄 파서를 판정한다. **요약줄 앞에는 공백 2칸이 붙는다**(`print(f"\n  {text}")`) — 벗기지 않으면 `^항목` 으로 한 줄도 안 잡혀 15/15 를 판정한 적이 없게 된다. 케이스 = 15/15 통과 · 14/15 미달 · 요약줄 부재 미달 · 두 벌 이어 붙으면 **마지막 한 벌**. ⓑ `tests/preflight-red.sh` = 조건을 어긋나게 두고 `reseed.sh` 를 실제로 돌린다 — 미달 10 항목을 이름으로 냄 · 뒤 단계 미시작 · 계획 요약줄 4케이스(`datasets 28 edges 18` 과 `… data_bytes N` **두 모양 다 통과** · 27 은 미달 · 요약줄 부재는 미달) · 실패해도 `result.json` 이 섬(멈춘 단계·종료코드·로그) · `--from` 이 preflight 를 건너뛰지 않음 · `--preflight-only` 가 바꾸는 단계를 0건 실행 · `die` 가 프로세스를 죽이지 않고 복귀 · 미리보기 값 부재는 「성립」이 아니라 **「판정불가」** · 픽스처가 레포에 회차 기록을 남기지 않음. ⓒ `tests/preflight-secrets.sh` = preflight ⑻ `secrets` 가 **통과할 수 있는 항목**임을 증명한다 — ssh 대역이 실물 `stat` 처럼 **받은 경로 그대로** 답하므로 9건 0600 은 통과 · 1건 부재·1건 0644 는 각각 이름을 대고 미달 · 원격 경로의 출처는 `COLAB_RESEED_EC2_SECRETS_DIR` 하나(운영자 기계의 `COLAB_DEV_SECRETS_DIR` 는 로컬 폴더라 읽지 않는다) · `--preflight-only` 가 마운트 자리와 계정 신원을 찍는다. 왜 = ⓑ 는 ssh 미접속만 재서 `printf` 짝짓기 결함(9건 중 1건만 물음)으로 이 항목이 **green 이 된 적이 없던** 것을 놓쳤다(DR-4 §5 ⑵). ⓓ `tests/remote-transport.sh` = **원격 셸로 값을 나르는 자리**를 판정한다 — ssh 대역이 받은 원격 스크립트를 로컬 bash 로 **실제로 실행**하므로 「원격 셸이 그 문장을 어떻게 읽는가」가 재현된다. 왜 = `psql_master_query` 가 SQL 을 `export SQL='<값>'` 한 겹에 실어 값 속 작은따옴표가 바깥을 닫았고 `column "colab_platform" does not exist` 로 `reset` 이 멈췄다(DR-4 §6). 그 경로는 **실모드로 돈 적이 없었고** `--dry-run` 은 본문을 찍기만 해 어느 검사에도 걸리지 않았다. 케이스 = 따옴표·`$`·백틱이 든 SQL 이 한 바이트도 바뀌지 않고 psql 에 닿음 · 원격 본문에 원문 미노출(base64) · 정지(①′) 뒤 실패 시 **앱 자동 재기동 ＋ `recovery.jsonl`** · 오류 한 건이 로그에 **한 번만** · `--rehearse` 가 `--dry-run` 에서 무접촉 · 리허설 응답이 어긋나면 **이름을 대고** 비영 · `='<값>'` 한 겹 적재 0건(정적 대조). **dev·AWS 무접촉** — `ssh`·`scp`·`docker`·`sudo`·`aws`·`agent-browser` 를 PATH 대역으로 가려 실물에 한 바이트도 나가지 않는다. red 두 갈래 = 판정(종료 1) · 준비(실행기 `bash`·`python3`·`git` 부재 → 78 ＋ `::gate-readiness-failure::`). 판정한 픽스처가 4건 미만이면 red — 대상 0건은 통과가 아니다 |
| `selftest` | **위 게이트들이 실제로 red를 낼 수 있는지.** ⭑ **⟨개정 2026-09-03 · 코드리뷰 #6⟩ 집합을 손으로 적지 않는다** — 구성원 정본은 `gates/run.sh` 의 `ALL_GATES` 안에서 이름이 `*selftest` 인 것 전부다. 종전에는 이 자리에 이름 14개가 손으로 적혀 있었고 `ALL_GATES` 에는 셀프테스트가 18개 있었다 — **`autometa-loss-`·`preview-tile-slot-`·`artifact-ownership-`· `stage2-markers-selftest` 넷이 조용히 빠져 있었다.** 빠진 것이 목록의 부재로만 존재하면 아무도 그것을 세지 않는다(green-by-skip 의 목록판). **세 상태** — 선언되면 돈다 · **명시 면제는 이름과 사유와 건수를 드러낸 채** 넘어간다 · 아무 말 없으면 red. 요약줄이 `선언 N · 실행 M · 면제 K` 와 `green / red(판정) / red(준비)` 를 낸다. 현재 면제 2건 = `stage2-markers-selftest`(pipeline-worker 런타임 필요 · CI 는 `dormant-tests` 잡이 돈다) · `service-tests-selftest`(서비스 venv 필요 · CI 는 `service-tests` 잡이 돈다). ⚠ 면제는 「검사하지 않아도 된다」가 아니라 **다른 잡이 그것을 돈다**는 선언이고, `gates/run.sh all` 은 면제 없이 전부 돈다. 케이스가 종료코드 78 로 나가면 집합 전체가 78 로 나간다 — **못 돈 것을 통과로 세지 않는다** |
| **`ops-observability`** | **I4 운영 관측 정본 대조.** core→viz/AI `traceparent`, HTTP 3단위 JSON span, pipeline pass 요약, dev S3 서울 리전 3자리, CloudFront global edge/서울 origin, OpenAI 공급자 관리 처리 위치, 알람 5분·3대상을 검사한다. 국내 고정이 아닌 외부 처리를 국내라고 쓰거나 관측 커널 복제본이 갈리면 red다. |
| **`ops-observability-selftest`** | 위 게이트와 상태형 알람 runner의 fail-closed 증명 10건 — 리전 drift, 외부 AI 국내 고정 거짓 선언, 5분 drift, 실패 임계 raise 1회, 반복 통지 0, 회복 clear 1회, 손상 state red, webhook 미선언 준비 red(78). 운영 webhook 호출은 0건이다. |

## 돌리기 전 — 시험용 값은 실행기가 스스로 읽는다

- **`~/.colab-v2-test.env` 가 없고 `CI`·`GITHUB_ACTIONS` 도 비어 있으면, 게이트 이름을 준 실행은 무엇이든 dispatch 전에 red(준비 · 입력미선언 · 종료코드 78)로 끝난다** — `exec-bit`·`contract-lint`·`work-item-consistency` 처럼 그 값을 안 쓰는 게이트도 예외가 아니다(판정부 = `gates/run.sh` 의 env 블록). 파일이 있으면 실행기가 `set -a; . <파일>; set +a` 를 대신 친다. 자리를 옮기려면 `COLAB_TEST_ENV_FILE=<경로>`, 값이 이미 실려 있으면 `COLAB_TEST_ENV_SOURCED=1`. CI 는 이 파일을 쓰지 않고 게이트가 일회용 DB 를 스스로 세운다. 파일 세우는 법 = `dev-package/RESTART.md §2-④`.

- **전수 회차의 정본 호출문은 아래 한 줄이다.** `seed-plan-drift`·`frontend-visual`·`harness-eval` 세 게이트는 운영자 입력이 없으면 red(준비 · 입력미선언 · 78)이고, 셋 다 **선언이든 명시 면제든 말을 해야** 병합 진입 조건 `red_준비 == 0`(`:137`)을 채운다. 변수를 아무것도 주지 않은 호스트에서는 어떤 브랜치도 그 조건을 만족할 수 없다. **명시 면제도 병합 진입 조건 충족이다**(intent `dev-package/intent/2026-09-17-gate-input-env-vars-block-merge-gate.md` 결정 · 2026-09-18). 면제 건수는 전수 요약 줄이 아니라 **해당 게이트 자신의 출력**에 드러난다 — `frontend-visual` 은 페이지 건수, `harness-eval` 은 과제 건수다.

  ```bash
  COLAB_REF_ROOT=<참조 데이터 루트> COLAB_VISUAL_EXEMPT=1 COLAB_HARNESS_EVAL_EXEMPT=1 bash gates/run.sh all
  # 측정 레인은 자기 task 의 선언 집합으로 돈다
  COLAB_REF_ROOT=<참조 데이터 루트> COLAB_VISUAL_EXEMPT=1 COLAB_HARNESS_EVAL_EXEMPT=1 COLAB_TASK_ID=<task_id> bash gates/run.sh task
  ```

  `seed-plan-drift` 는 **면제가 아니라 실선언**이다 — 참조 데이터 루트의 기본 자리는 `dev-package/tools/dev-seed/README.md` §0 이 적고, 실물이 있는 호스트에서는 `COLAB_SEED_PLAN_NO_FILES=1` 대신 `COLAB_REF_ROOT` 를 준다. 그러므로 명시 면제가 필요한 것은 `frontend-visual`·`harness-eval` **2건**뿐이다.
  **대신 실행하려면** — `COLAB_VISUAL_URLS=<url…>`(앱 기동이 전제다 · `:39`) · `COLAB_HARNESS_EVAL=1 COLAB_EVAL_TIMEOUT=<초> COLAB_EVAL_BUDGET=<USD>`(**실제 모델을 부른다** · 승격 전이므로 로컬 `all` 과 CI 가 면제 모드로 도는 것이 현 규정이다 · `:43`).

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
- ⭑ **⟨2026-09-18 · ADR-0005 개정의 후속 ②⟩ 호스트 뮤텍스 — `serial` 선언은 이제 프로세스 경계를 넘는다.**
  종전에 이 선언은 **`gates/run.sh all` 한 프로세스 안에서만** 효력이 있었다(선언표를 읽는 자리가 `all)`
  갈래 하나뿐이었다). 그래서 「게이트 레인은 호스트에 하나」(`rules §3-1`)는 오케스트레이터가 레인
  지시문에 그 문장을 적어서 지켜졌다 — 지시문을 읽지 않은 프로세스(다른 세션·Codex·사람 손)는
  걸리지 않았다. 강제가 아니라 예의였다. 이제 실행기가 줄을 세운다.
  - **무엇을 잡나** — 호스트 전역 `flock` **하나**(`${TMPDIR:-/tmp}/colab-v2-gate-host-mutex/host`)를,
    **`serial` 로 선언된 게이트를 실행하는 부모 프로세스만** 잡는다. 잠금 단위는 **게이트 1건**이다.
    ⛔ **면제 변수는 없다.** `parallel` 선언이 곧 면제이고, 그 외의 면제는 **잠금을 쥔 부모가 자식에게
    주는 `COLAB_GATE_MUTEX_HELD=1`** 하나뿐이다(재진입 교착 방지). ⚠ **`COLAB_GATE_SUMMARY_CHILD=1` 은
    면제 키가 아니다** — `task` 경로가 게이트마다 그 자식을 부르므로, 그것을 키로 쓰면 측정 레인의
    `serial` 게이트가 전부 무잠금으로 돈다.
  - **잠금 키는 `TMPDIR` 하나다.** 경합 자원(호스트 CPU·메모리·도커 데몬)이 레포별이 아니기 때문이다.
    레포 경로를 키에 넣으면 워크트리마다 잠금이 갈려 실효 한도가 배수로 늘어난다.
  - **대기는 보인다** — `::gate-waiting::gate=<게이트>|waited=<초>|limit=<초>|lock=<경로>` 를 stdout 에
    찍는다(획득 시도 직전 1회 ＋ 획득 직후 실경과 1회). 조용히 기다리면 멈춘 것과 구분되지 않는다.
  - **상한** = `COLAB_GATE_MUTEX_WAIT`, 기본 **900초**(선례 `COLAB_PG_SLOT_WAIT`). 잠금이 게이트 1건
    단위이므로 최장 대기는 상대 레인의 `serial` 게이트 **1건**이다.
  - **세 갈래가 `red(준비 · 78)`** — ⑴ `flock` 부재 ⑵ 잠금 디렉터리·파일을 만들 수 없다 ⑶ 상한 초과.
    셋 다 기존 보고 경로 하나(`_readiness.sh` `readiness_env_wait`)로 나간다. ⚠ **상한을 늘리거나
    재시도해서 green 을 만들지 않는다** — 78 이 나면 그 값이 곧 실측이다.
  - ⚠ **`serial` 이 잡은 동안 다른 프로세스의 `parallel` 게이트는 돈다.** 의도된 형태다 —
    `serial` 이 보장하는 것은 「다른 `serial` 과 겹치지 않는다」이지 「혼자 돌았다」가 아니다.
  - **잠금 여부가 결정된 그 자리에서** 한 줄이 선다: `── 호스트 뮤텍스 : 잠금 N건 · 면제(parallel 선언) M건 · 대기 누계 Xs`.
    ⚠ 요약 래퍼 안이 아니다 — 래퍼는 `COLAB_GATE_SUMMARY_CHILD` 가 빈 실행에서만 돌아서, 거기 두면
    `task` 경로(게이트마다 `CHILD=1` 자식)의 로그에서 잠금 사실이 **통째로 사라진다**(2026-09-18 실측).
    N ＋ M = 실행 건수이고 N 은 `serial` 선언 건수와 같아야 한다. 증명 = `gate-host-mutex-selftest`.
- `gates/run.sh all` 은 시작할 때 **실행 계획**(단독 N · 병렬 M · 미선언 K)을 찍고, 요약에도 미선언 건수를
  다시 적는다. `COLAB_GATE_OUTDIR=<경로>` 를 주면 게이트별 실행 구간(`*.span`)이 남아 **「단독으로 돌았다」를
  주장이 아니라 값으로** 대조할 수 있다.
- 도구 설치 구간(`gates/.venv` · `node_modules`)에는 잠금을 걸었다(`_lock.sh`). 잠금이 없으면 둘이 동시에
  설치하다 한쪽이 「도구 없음」 red 를 내는데, 그건 검사 결과가 아니라 배선이 만든 red 다.
  ⭑ **⟨2026-09-18 · ADR-0005 개정⟩ 잠글 수단(`flock`)이 없으면 `red(준비 · 78)` 이다.** 종전에는 잠그지 않고
  그냥 진행했다 — 실행기가 「잠금이 서지 않았다」를 **알고도** 삼킨 자리다. `_pg.sh` 의 슬롯 세 갈래도 같이
  승격했다(`flock` 부재 · 슬롯 디렉터리 생성 실패 · 슬롯 파일 열기 실패). **면제 변수는 두지 않는다** —
  오늘 모든 호스트에 `flock` 이 있고(CI = `ubuntu-latest` · 개발 = WSL/util-linux), 없는 호스트가 합류하는
  날 3상태 변수를 만든다.
- ⭑ **⟨2026-09-17 · 이슈 #56⟩ 미선언은 이제 `harness-contract` 가 red(판정)으로 막는다.**
  `scripts/harness/check.py` 의 `check_gate_parallelism()` 이 `ALL_GATES ⊆ parallelism.toml` 을 단언한다 —
  빠진 이름도, **선언표에만 있는 이름**도, `serial`·`parallel` 아닌 값도 전부 `red(판정)` ＋ 종료코드 **1** 이다.
  판정 대상이 **선언표**이므로 판정 red 가 맞다. 선언표나 `ALL_GATES` 를 **읽지 못하면** 그때는
  `::gate-readiness-failure::` ＋ **78** 이다 — 대상을 못 읽은 것이지 대상이 규율을 어긴 것이 아니다(ADR-0004).
  선언표를 읽는 자리는 실행기와 **같은 하나**다(`gates/tools/parallelism.py`). 두 벌로 두면 한쪽이 언젠가
  다른 말을 한다. 단독 게이트 실행에서도 걸리므로 전수를 돌기 전에 안다.
  ⚠ 이것은 결함 수정이 아니라 **결정 전환**이다 — 위의 「미선언 → 안전한 쪽(단독) ＋ 출력에 명시」는
  의도된 설계였고, 승격은 그 결정을 뒤집는다(승인 2026-09-17). 새 게이트는 선언 없이는 들어오지 못한다.

## 게이트 요약 JSON — 기계가 읽는 한 벌 (스키마 `colab-gate-summary/1`)

요약은 사람이 읽는 3상태 텍스트로만 있었다. 그래서 레인 종료 검사와 「전수를 다시 돌릴 것인가」
판단이 **사람이 옮겨 적은 계수**에 기대고 있었고, 옮겨 적는 자리는 언젠가 틀린다.
이제 실행기가 **요약이 이미 센 같은 변수**로 JSON 한 개를 더 낸다. ⚠ **게이트 로직은 무변경이다.**

- 배출처 = `COLAB_GATE_REPORT_DIR=<경로>` (상대경로는 레포 루트 기준). 레인은
  `dev-package/reports/<회차>/<레인>` 을 준다. `all` 은 `COLAB_GATE_OUTDIR` 안에도 같은 파일을 남긴다.
- **배출처를 주면 단독 게이트도 요약과 JSON 을 낸다** — 레인의 반복 검증은 전수가 아니라 단독
  게이트이기 때문이다(`rules §3-1`). 주지 않으면 종전 그대로 아무것도 더 찍지 않는다.

```bash
COLAB_GATE_REPORT_DIR=dev-package/reports/<회차>/<레인> ./gates/run.sh service-tests-viz-render
COLAB_GATE_REPORT_DIR=dev-package/reports/<회차>/<레인> ./gates/run.sh all -j 4
```

- 상태값은 **`green` / `red_판정` / `red_준비` 셋뿐이다. `SKIP` 은 없다** — 이 레포는 대상 0건을
  red 로 못박았고, SKIP 은 green-by-skip 통로를 다시 여는 것이다.
- `counts` = 요약줄의 그 계수 그대로(`green` · `red_판정` · `red_준비` · `red_준비_입력미선언`).
  **계수를 다시 세는 자리를 만들지 않았다** — 배출기(`gates/tools/gate_summary_json.py`)는 직렬화만 한다.
- `tree` = `HEAD^{tree}`. **직전 판정본과 같으면 전수 재실행을 갈음한다**(`rules §3-2`).
- 소비자 = `SubagentStop:lane-worker` 훅(H7). 부재 = 「게이트를 돌리지 않은 레인」으로 차단하고,
  `counts.red_판정 > 0` 이면 red 게이트 이름을 열거하며 차단한다.
- ⭑ **⟨2026-09-06⟩ 이 파일은 추적하지 않는다**(`.gitignore` 의 `dev-package/reports/**/gate-summary.json`).
  커밋되면 새 체크아웃마다 따라와 H7 의 「가장 최근 하나」가 그것을 뽑고 게이트를 안 돌린 레인이
  통과한다. 회차 기록으로 남길 한 벌은 이름을 바꾼다(예 `final/gate-summary.record.json`).
  H7 은 이름 규약에 더해 **JSON 의 `commit`·`tree` 를 그 워크트리의 HEAD 와 대조**하고, 둘 다
  어긋나면 부재와 같이 차단한다 — **게이트는 마지막 커밋 뒤에 돌린다**(커밋 후 돌리지 않으면
  JSON 이 직전 트리를 가리킨다).
- ⚠ **병합 진입 조건은 `red_판정 == 0` 과 `red_준비 == 0` 둘 다**다(준비 red 도 red 다).
  H7 은 레인 종료만 보므로 준비 red 로 종료를 막지 않는다 — 그 판정은 병합 시점 몫이다.

### 게이트 행의 `failures` — 실패한 시험의 이름을 싣는 공용 표식 ⟨2026-09-17 · 이슈 #55⟩

red(판정)인데 **무엇이 깨졌는지 요약 어디에도 없으면** 사람이 1300줄 출력을 뒤진다.
그래서 게이트 행에 열을 하나 더했다. **`counts` 키 집합은 그대로이고 스키마도 `colab-gate-summary/1`
그대로다** — 새 열은 게이트 **행**에 붙지 `counts` 에 붙지 않으므로 ADR-0004 재검토 조건에 걸리지 않는다.

- **표식 형식**(게이트가 stdout 에 찍는다) — `::gate-failure::gate=<이름>|file=<경로>|test=<시험 이름>`.
  기존 `::gate-readiness-failure::gate=…|waited_for=…` 선례와 같은 모양이다. 게이트마다 열을
  하나씩 늘리지 않고 **이 표식 하나**를 쓴다.
- **접는 법** — 실패는 여럿이라 표식도 여러 줄인데 게이트 행은 TSV 한 셀이다. 실행기가 표식 줄을
  **전부** 모아 ` || ` 로 이어 한 셀에 넣는다(`gates/run.sh` `summary_failure_marks()`).
  준비 표식의 `grep -m1` 과 달리 **첫 줄만 남기지 않는다** — 그러면 나머지 실패를 잃는다.
  ⚠ ` || ` 는 사람이 읽기 위한 구분자다. 이 값은 진단용이고 되파싱해서 판정에 쓰는 자리가 없다.
- **경로** — 게이트가 찍고 → 실행기(`summary_gate_row()` 5번째 열)가 옮기고 → 배출기가 직렬화한다.
  **계수를 다시 세는 자리도, 실패를 다시 찾는 자리도 만들지 않았다.**
- 지금 이 표식을 찍는 게이트는 `frontend-test` 하나다. 다른 게이트로 넓히는 것은 별도 범위다.
- ⚠ **게이트 행을 만드는 자리가 둘이다.** 하나는 위 경로(`gates/run.sh`)이고, 다른 하나는
  `scripts/harness/hooks/lifecycle_contract.py` 의 `run_gates()` 다 — 그쪽은 `gates/run.sh` 의
  `summary_gate_row()` 를 거치지 않고 같은 스키마의 행을 **자기 손으로** 짓는다.
  이번에 `failures` 는 `run.sh` 쪽에만 더했다. `run_gates()` 에는 `::gate-failure::` 를 집는 코드가
  없어 거기에 키를 더하면 **항상 `null`** 이 되고, 그것은 재지 않은 것을 잰 것처럼 쓰는 모양이다.
  두 생산처를 하나로 합치는 일은 아직 담는 이슈가 없다 — 사실만 여기 적어 둔다.

## selftest가 있는 이유

"전부 green"과 "전부 무력"은 구분되지 않는다. v1 CI는 DB 없이 돌아 RLS 테스트를 **green-by-skip** 했다.
각 게이트는 red fixture로 자신이 fail-closed임을 증명해야 한다.

⭑ **⟨2026-09-05⟩ 「준비됐다」의 정본은 `_pg.sh` 의 `pg_wait_ready` 하나 — 실서버만 센다.** `postgres:16-alpine` 은 initdb 동안 **임시 서버**를 띄웠다 내리므로(초기화 완료 표식과 실서버 기동 사이 ≈0.2초 공백), 첫 `pg_isready` 성공에서 멈추던 옛 대기는 60초 예산 중 **1초** 만에 red(준비) 오탐을 냈다(`rls-effect-selftest` 단독 3연속). 이제 **초기화 완료 표식 ＋ 그 뒤 `pg_isready` 성공**을 함께 본다 — **대기 정밀화이지 범위 축소가 아니다**(예산 60초·재시도 없음·판정 그대로). 증거 프로브 = `gates/fixtures/pg-ready/temp-server-probe.sh`, fail-closed 케이스 = `rls-effect-selftest` 의 「실서버가 끝내 안 뜨면 상한에서 red(준비)」.

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
| **`frontend-gates`** ⭑신설 | **`frontend` \|\| `contracts`** | `frontend-typecheck`·`frontend-test`·`frontend-design-lint` |
| `boundary-gates` | core-api ∥ ai-service ∥ **viz-render ∥ pipeline-worker ∥ infra ∥ contracts** ⭑확대 | `import-boundary`·`banned-import`·`ai-no-lineage-write`·**`db-boundary`** ⭑신설 |
| `schema-gates` | `db` ∥ core-api | `migration-single-head`·`schema-diff`·`rls-coverage`·`rls-effect` |
| `dormant-tests` | pipeline-worker | `stage2-markers-selftest` → `stage2-markers` |
| **`service-tests`** ⭑신설 | 단위별 `<단위> \|\| contracts` (matrix 4) | `service-tests-selftest` → `service-tests-<단위>` |
| `planning-gates` | `dev-package` | `work-item-consistency`·`planning-freshness` |
| **`repo-hygiene`** ⭑신설 | **조건 없음(항상)** | `exec-bit-selftest` → `exec-bit`. 실행비트 결함은 `db/`·`infra/`·`services/` 어디서나 생기므로 경로 필터를 걸지 않는다 |
| **`harness-eval`** ⭑신설 | **`harness`**(`CLAUDE.md`·`.claude/skills\|hooks\|agents/**`) | `harness-eval`. 시크릿은 **참조만**(`secrets.ANTHROPIC_API_KEY` · 발급은 Ted) 이고 **부재는 red(준비 · 78) — skip 이 아니다**. 승격 전이라 **면제 모드**로 돌아 과제 건수만 드러낸다 |
| `gate-selftest` | `contracts` | `selftest` 집합(`ALL_GATES` 의 `*selftest` 전부 ＋ 명시 면제 2 — 계수는 요약줄이 정본) |

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
| **`db-boundary`** | ✅ 구현 (2026-08-25) · compose 2 (2026-08-30 `〈342〉`) | — green (단위 7 · 스캔 대상 = 소스 + compose **2**(staging·dev) · 위반 0). `COLAB_AI_CATALOG_DB_URL` 이 판정 ㈎ 로 사라진 뒤의 배치를 기준으로 한다. selftest 에 「두 번째 compose 부재 = red · dev 횡단 = red · 둘 정상 = green」 3건 |
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
| `harness-contract-selftest` | **5** | 없음(Python 표준 라이브러리). malformed config는 red(준비·78), 누락 adapter는 red(판정·1), 정상 계약은 green을 증명 |
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
| `work-item-selftest` | **18** ⭑ backlog 정상 분류와 미지원 stage 거절을 함께 검증한다. ／ 이전 **14** ⭑ ⟨2026-08-31 · `〈252〉` 로 ㈔ 4건 증설: 중복·행 0건·문서 부재·§9 부재⟩ ／ 이전 ~~10~~ | 없음 (bash + python3 + pyyaml) — 대조군 1 · red 증명 17. 대조군의 open backlog는 stage 3 표지를 요구받지 않으며, backlog의 잘못된 `depends_on`과 `stage: not_a_stage`는 각각 red다. **픽스처가 자기 산문 문서(`03-HANDOFF` · `WORK-UNITS` 스텁)를 들고 다닌다.** 레포 실물의 항목 상태는 정당하게 어긋나 있을 수 있고(그것이 이 게이트를 만든 이유다) selftest 가 거기 볼모잡히면 안 된다 — `db-selftest`·`generated-selftest` 와 같은 이유. red 픽스처의 ㈑ 는 **2026-08-27 실물 재현**(`WORK-UNITS §10` 착수 후보 표에 `I0 ⏸` 가 올라 있던 것) |
| `frontend-fixture-reach-selftest` | **6** | 없음(node 만) — `gates/fixtures/frontend-fixture-reach/` 트리 여섯을 **그대로**(사본 없이) `COLAB_FRONTEND_DIR` 로 가리켜 돈다: 깨끗한 진입점 green(대조군) · 픽스처 실도달 red · 도달 0건 red · 별칭 선언 red · 판정부 스크립트 부재 red(준비) · 진입점 부재 red(준비) |
| `frontend-design-lint-selftest` ⭑신설 | **26** | 없음(node 만) — `gates/fixtures/frontend-design-lint/` 트리 열을 **그대로**(사본 없이) `COLAB_FRONTEND_DIR` 로 가리키고 트리 안 `same-in-dark.txt` 를 면제 목록으로, 트리 안 `primitives.txt`·`primitives-exempt.txt` 를 프리미티브 목록·면제로 준다(P2b · e 를 보지 않는 트리는 빈 파일): 정본 짝·루트 범위·면제 1건 green(대조군 · 요약줄 「면제 1」 확인) · `red-a`(화면 `:root` 정의 ＋ 범위의 정본 계열 이름) · `red-b`(미정의 참조 · 폴백 있음) · `red-c`(다크 누락 ＋ 다크 전용) · `red-d`(화면 CSS ＋ 셸 CSS `@import` · d=2) · `red-exempt`(사유 빈칸 · 낡은 항목 · 다크에 이미 있음) · `red-root-html`(층 블록 안 `html:root` 정의) · `red-accent`(화면 범위 `--accent-` 정의) red 7 — 각 red 는 출력의 계수 줄로 **그 규칙 때문에** red 임을 확인한다 · `green-layer`(정본·화면 CSS 가 `@layer` 블록 안) green · `empty`(대상 CSS 0건) · node 부재(`COLAB_NODE_BIN` 을 없는 경로로) · 판정부에 디스크에 없는 대상 파일 red(준비) 3 · (P3) `green-fg`(토큰 참조 · 제외 키워드 · 사유 있는 f 면제 1건이 실제 리터럴에 걸림 · `--*` 키만인 인라인 2건 → green · 요약줄 「색 리터럴 0(면제 1) · 인라인 0(변수 대입 2)」 확인) · `red-f`(직접 hex · 폴백 hex · 색 이름 · 사유 없는 면제 · 낡은 면제 → `f=6 f_direct=2 f_fallback=1 f_name=1 f_holes=2`) · `red-g`(인라인 색 · px · 축약형 `{ width }` · 변수 대입만 1건은 세지 않음 → `g=3 g_vars=1`) · `red-g-spread`(펼침 속성 안 `style` 비변수 키 1 · 변수 대입만 1 → `g=1 g_vars=1 g_spread=2`) · `green-mix`(토큰끼리의 `color-mix()` → green) · `red-mix`(리터럴 색이 섞인 `color-mix()` → `f=1`) · `typescript` 부재(`COLAB_DESIGN_LINT_TYPESCRIPT` 를 없는 경로로) red(준비) · (P2b) `green-e`(맨 정의는 `primitives.css` 에만 · 화면의 문맥 `.x-page .btn` · 섞인 compound `.btn.x-go`·`button.btn` · `:not()`/`:has()` 인자 · 목록 밖 `.btn-ghost` · 사유 있는 e 면제 1건이 실제 맨 정의에 걸림 → green · 요약줄 「프리미티브 맨 정의 밖 0(면제 1)」 확인) · `red-e`(화면의 맨 정의 · 상태 맨 정의 `.btn-primary:hover` · `:is(.x-go, .chip)` 펼침 · 사유 없는 면제(면제 안 함) · 낡은 면제 → `e=6 e_bare=4 e_important=0 e_holes=2`) · `red-e-important`(`primitives.css`·`base.css` 안 `!important` · 화면 파일의 것은 대상 밖 → `e=2 e_important=2`) · 프리미티브 목록 부재(`COLAB_DESIGN_LINT_PRIMITIVES` 를 없는 경로로) red(준비) · (P5 · h) 대조군 ⓐ 요약줄 「문서 표 갈림 0」 확인 · 저장소 문서 사본의 `generated:tokens` 블록 안 한 줄을 고쳐 `COLAB_DESIGN_LINT_DOC` 로 → red(「문서 표 갈림 1」·「h tokens 갈림」) · 문서 부재(없는 경로) red(준비) · 블록 밖에만 한 줄 더한 사본 → green — 준비 실패 기대 케이스는 판정 red(rc 1)로 끝나면 기대와 다름으로 센다 |
| `frontend-visual-selftest` ⭑신설 | **4** | `agent-browser`(0.27.0 · 오프라인 `file://` 로 돈다 — 앱을 띄우지 않는다) — ⓐ 13px 이상·대비 ≥4.5·`:active`·reduced-motion 픽스처 green(대조군) · ⓑ **11px 글자 ＋ 대비 4.2:1 red(판정)**(위반 요소를 셀렉터로 내는지까지 본다) · ⓒ 미선언 red(준비 · `cause=입력미선언`) · ⓓ `COLAB_VISUAL_EXEMPT=1` green(**건수 노출까지 본다** — 건수를 숨긴 통과는 green-by-skip 이다). 픽스처 원본 = `gates/fixtures/frontend-visual/{green,red}.html`, 판정은 `mktemp -d` **사본**에서만 난다 — 이 레포 경로에는 공백(`00 CoLAB`)이 있고 `COLAB_VISUAL_URLS` 는 공백으로 나눈 목록이라 원본 자리를 그대로 가리키면 URL 이 갈라진다 |
| `harness-eval-selftest` ⭑신설 | **4** | 없음(bash + python3 + PyYAML) — `claude` 는 `mktemp -d` 안의 스텁이고 과제 뿌리도 임시 자리다(**모델 호출 0회**). ⓐ 과제 0건 red(판정) · ⓑ 면제 건수 노출 green · ⓒ 상한 초과 red(준비) · ⓓ 미선언 red(준비·입력미선언) ＋ CI 필터 대조 |
| `generated-selftest` | **9** | 없음 (bash + python3) — green 기준 케이스도 fixture 다. 레포 실물은 재생성 파이프라인 상태에 따라 정당하게 red 일 수 있어, selftest 가 레포 상태에 볼모잡히지 않게 했다 |
| `product-release-selftest` | **필수 15 + 전체 회귀** | pytest — 동일 저장소 `develop → product` 사람 병합, GitHub API 재검증, merge 부모·manifest 결속, 실제 merge SHA 배포·reseed 계획 생성과 자식 전달, 설정 부재 78, 중복·낡은 후보 차단, 알림 0건, 변경 산출물 거부, 병합 전 출발 브랜치 검사와 작업 사본 SHA를 검증한다. 필수 시나리오 누락·수집/실행 0건은 red(판정), pytest 실행기 부재는 red(준비)다. 실제 GitHub·배포·Slack 호출은 0건이다. |
| `product-reseed-selftest` | **필수 10 + 전체 회귀** | 영속 최초 실행 기록·수동 재개·프로세스 종료 시 잠금·입력 변조·재초기화 거부와 프로젝트 카드/표에서 정확한 이름·ID 추출을 시험한다. 실제 운영 접촉은 없다. pytest·Node·jsdom 부재는 78, 시나리오 누락·skip·실패는 1, 실제 전건 성공은 0이다. |
| `service-tests-selftest` | **9** | 서비스 venv 하나(파이썬만 빌린다) — ⓐ 통과 1건 green · ⓑ 실패 1건 red · ⓒ 수집 0건 red · ⓓ 실행 0건(전부 skip) red · ⓔ venv 부재 red(준비 · 78) · ⓕⓖ 필수 인자 부재 red · ⓗ 단위 자리 부재 red · ⓘ 요약줄 계수 노출. 픽스처 = `gates/fixtures/service-tests/` |
| `is4-recovery-selftest` | **25** | 실제 Cloudflare apply 0회. 정확한 resource 1건·값 동일 metadata update만 허용하고 address/unknown/output/replace/값 변경을 거부한다. private bundle의 plan·state·선언·image·권한·symlink 변조, drift exit 2/1, 사전 health 오류·503, apply 실패 뒤 재사용, 동시 호출 둘 중 apply 1회를 fixture와 Docker/curl 스텁으로 검증한다. |
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
- **두 compose(`infra/staging/compose.i2.yml`·`infra/dev/compose.yml`) 가 아닌 배선** — `.env` 파일·호스트 환경변수·
  prod 매니페스트는 대상이 아니다. dev 는 `〈342〉` 로 대상에 들어왔고(둘 중 하나라도 없으면 red), prod 가 서면 그 파일도 목록에 넣는다.
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
- **`after_stage2` 밖의 stage** — `stage1`·`stage2`·`backlog`는 산문과 대조하지 않는다. backlog는
  Stage 1·2·3 미배정이며 stage 3 표지에 넣지 않는다. 세 단을 다 옮겨
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
