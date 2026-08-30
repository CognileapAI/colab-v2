# PV-1 착수 1회차 — 배포 선언을 세우고 멈춘 자리 (2026-08-30 · 워크트리 `lane-pv1`)

> **한 줄** — `PV-1` 세 갈래는 **코드로 전부 서 있었다.** 없던 것은 **배포 선언 하나**였고,
> 그것을 세웠다. **닫지 않았다** — 남은 셋은 배포 권한과 사람 판정의 자리다.

## 1. 먼저 쟀다 — 착수 전 상태

대장이 이번 세션에도 양방향으로 틀릴 수 있다는 전제로, 세 갈래를 각각 코드에서 확인했다.

| 갈래 | 착수 전 실측 | 자리 |
|---|---|---|
| ⑶ 헤더 파싱 | **서 있다** — `file.header-parsed` 를 변수·기간·좌표계·격자·바이트합·못 읽은 파일까지 채워 발행 | `domains/d5_ingestion.py` ③ 블록 |
| ⑷ 좌표계 통일 | **서 있다** — `file.crs-normalized`(`source_crs` → `TARGET_CRS` · 변환 파일 목록) | 같은 파일 ④ 블록 |
| ⑸ 지도용 영상 변환 | **서 있다** — `previews_root` 를 받아 `tile-*.tif` 를 자리에 굽고 `preview.cog-built` 발행 | `d5/pipeline.py run_file` · `kernel/storage_layout.preview_path` |
| 완료 조건 ⑵ 저장 규약 | **서 있다** — 「미리보기 산출물」 종류 ＋ 「지도 타일」 내용 키(접두사 `tile-` · 필수 6필드) | `contracts/storage/layout.json` |
| 완료 조건 ⑶ 유실 감지 | **집행부가 서 있다** — 게이트 `autometa-loss`·`preview-tile-slot` ＋ 셀프테스트 12·12건 | `gates/tools/` |
| **배포 선언** | ⛔ **없었다** — `pipeline-worker` 블록에 `COLAB_WORKER_STAGE2`·`COLAB_WORKER_PREVIEW_DIR` **둘 다 없고** 미리보기 볼륨도 안 붙어 있었다 | `infra/staging/compose.i2.yml` |

**따라서 두 red 게이트의 원인은 하나였다** — 워커가 stage 1 만 돌아 사건이 한 건도 발행되지
않았고(`autometa-loss` 대조 대상 0건), 지도 타일이 놓일 자리가 배포에 없었다(`preview-tile-slot`
입력 미선언). **「입력을 안 줘서」가 아니라 「stage 2 가 아직 안 돌아서」** 라는 `RESTART §2-④-㉯`
의 판단이 실측으로 맞았다.

## 2. red 를 먼저 세웠다

`services/pipeline-worker/tests/test_stage2_deployment_declaration.py` — **5건, 착수 시 5 failed.**

오라클은 지어낸 것이 아니라 이 레포가 이미 적어 둔 셋이다.

1. `app/worker.py stage2_declaration` — **무언은 면제가 아니다.** `on` 을 말해야 돈다
2. 같은 파일 — `on` 인데 미리보기 루트가 없으면 **뜨지 않는다**(자리를 모른 채 굽지 않는다)
3. `contracts/storage/layout.json previewsRoot` — 미리보기 루트는 **하나**다. 굽는 쪽(D5)과
   찾아 쓰는 쪽(D7)이 갈리면 재사용이 영영 성립하지 않고, 그 실패는 에러가 아니라
   **「매번 다시 굽는다」로 조용히** 나온다 (접수분 루트에서 한 번 일어난 무늬 · `§4 #20`)

시험은 그 셋에 더해 **볼륨이 실제로 그 경로에 붙어 있는가**와 **`volume-init` 이 주인을 맞추는가**
까지 본다 — 선언만 있고 볼륨이 없으면 컨테이너 안 임시 자리에 굽고 다음 바퀴에 사라진다.

## 3. 한 것

`infra/staging/compose.i2.yml` `pipeline-worker` 블록에 셋을 붙였다.

- `COLAB_WORKER_STAGE2: "on"`
- `COLAB_WORKER_PREVIEW_DIR: /srv/viz-previews` — **`viz-render` 의 `COLAB_VIZ_PREVIEW_DIR` 과 같은 값**
- `previews` 볼륨 마운트(**쓰기** — 굽는 쪽이라 `viz-render` 의 `:ro` 와 다르다)

**그 밖은 손대지 않았다** — 계약 개정 0 · 계약 동결 해제 0 · 마이그레이션 0 · 생성물 0 ·
`services/**/src` 0 · 프론트 0 · 게이트 정의 0 · 배포 0.

## 4. 닫지 않는다 — 남은 조건 셋

- **㈎ staging 재배포.** 배선은 트리에 있고 **도는 배포에는 아직 없다.** 배포는 이 회차의 권한
  밖이라 **멈추고 보고했다**(`CLAUDE.md §4` 경계 규약).
- **㈏ `COLAB_PREVIEW_TILE_DIR` 를 선언할 호스트 경로가 아직 없다.** ⭑ **재배포만으로는 안 풀린다** —
  실측: `docker volume inspect colab-v2-staging_previews` 의 마운트 지점이 게이트 사용자에게
  **`Permission denied`** 다. named volume 이라 도커 밖에서 못 읽는다. 호스트 경로로 내주려면
  볼륨 형태를 바꿔야 하고 그것은 **백업 범위**(`infra/staging/backup`)를 함께 건드린다.
  compose 에 호스트 절대경로를 적을 수도 없다(`CLAUDE.md §3-8` · 파일이 스스로 그렇게 적어 두었다).
  **없는 자리를 지어내지 않는다** — 앞 회차의 판단을 뒤집지 않고 그대로 둔다. → `§4 #49`
- **㈐ 그 뒤 게이트 `autometa-loss`·`preview-tile-slot` 실판정 green.**

⚠ **`#48`(타일 서빙의 화면 도달)은 이 회차가 손대지 않았다.** 이유 둘 —
⑴ `§4 #48` 이 적어 둔 푸는 법 자체가 「**자리를 `PV-1` 이 내주면** 결과에 타일 갈래를 싣는 회차를
`P3` 안에 세운다」이고, 그 자리가 위 ㈏ 로 아직 안 섰다. ⑵ 계약 `core-viz.yaml RenderResult` 는
`oneOf`(`imageUrl` **택일** `tileUrlTemplate`)라, 타일 갈래를 실으면 **지도형 주 화면이 단일 PNG 에서
타일로 바뀐다** — 제품 표면의 갈아끼움이고 `P3` 의 소유다. **순서를 바꾸지 않았다.**

## 5. 계수

| 축 | 값 |
|---|---|
| 게이트 `all` | before **green 33 / red(판정) 1 `autometa-loss` / red(준비) 1 `preview-tile-slot`** → after **동일** |
| 이번 변경이 만든 red | **0건** |
| pipeline-worker | **196 → 201 passed / 0 failed** (신규 5건 · red 5 선행 확인) |
| 계약 동결 해제 | **0회** (직전은 11차 그대로) |
| push · 병합 · 배포 | **0건** |
