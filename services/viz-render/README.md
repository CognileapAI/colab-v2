# viz-render

**담는 도메인** — D7 Visualization

프로파일: 중 CPU · 지연 민감 · 캐시 가능. **geo 라이브러리가 여기에만 들어간다**
(`CLAUDE.md §3-4` · `gates/config/boundaries.toml` 의 `core-api.banned`).

## 지금 구현된 것 — 미리보기 최소 렌더 경로 (WU-P2 · `〈63〉-㉮`)

계약 정본은 `contracts/seams/core-viz.yaml` 이다. 그중 **4 op** 이 선다.

| op | 경로 |
|---|---|
| `createRender` | `POST /viz/v1/renders` → 202 + `RenderJob` |
| `getRender` | `GET /viz/v1/renders/{renderId}` → **실패도 200**, 이유는 `failure` |
| `getRenderTile` | `GET /viz/v1/renders/{renderId}/tiles/{z}/{x}/{y}.png` — **core-api 를 지나지 않는 유일한 경로** |
| `listPalettes` | `GET /viz/v1/palettes` — `RenderStyle.palette` 값의 출처 |

지원 포맷 = **`NetCDF` · `Binary` · `HDF4` · `GeoTIFF`** (`〈51〉` — 숫자가 아니라 목록이다).

## 아직 없는 것 (그리고 그것이 정상인 이유)

- **데이터셋 상세의 2D 렌더 3종(격자·경계·점)** 과 **`createScreenshot`** 은 **P3** 다.
  이 레인의 경계는 「미리보기가 요구하는 범위까지」였다 (`P2-EXEC §3` 레인 표).
- **대상 해석의 실물 배선** — `datasetId`/`uploadId` → 파일은 `ports/source.py` 의
  Protocol 이고, 지금 들어 있는 어댑터는 **파일시스템 하나**다. `d5_*` 원장(W1)과
  객체 저장 배선은 이 레인의 소유가 아니다.
- **환경변수 주입** — `COLAB_VIZ_SOURCE_ROOT`·`COLAB_VIZ_SERVICE_TOKEN`·
  **`COLAB_VIZ_TILE_SIGNING_SECRET`** 을 `infra/staging/compose.*.yml` 이 넣어야 한다.
  `infra/` 는 이 레인 소유가 아니라 손대지 않았고, **없으면 렌더 표면이 503** 을 낸다(헬스는 산다).

## 소스 모드 · 미리보기 싱크 (`ports/source.py` · `ports/preview_sink.py` · `PLAN-SoT §9 〈178〉-㉮·㉴`)

읽기(`readers.py`·`detect_format`)는 로컬 경로만 본다. s3 모드는 대상을 **작업 디렉터리로 통째로 내려받아**
같은 배치(`storage_layout`)로 놓는다 — 목록 크기로 413 을 판정한 뒤 `materialize` 가 내려받고(HeadObject·받은
바이트 크기 대조 — 어긋나면 413), 캐시 키는 mtime 이 아니라 **ETag** 로 든다(내려받을 때마다 mtime 이 새로워져
`previews/` 가 렌더마다 늘던 결함을 막는다 — `domains/d7_visualization/source_digest.py`).

| env | 모드 | 뜻 |
|---|---|---|
| `COLAB_VIZ_SOURCE_MODE` | — | `local`(기본, `COLAB_VIZ_SOURCE_ROOT`) \| `s3`. **모르는 값은 기동 거부** |
| `COLAB_VIZ_S3_BUCKET` · `COLAB_VIZ_S3_REGION` | s3 소스 또는 s3 싱크 **필수** | core-api 와 같은 버킷·리전. 자격증명은 `kernel/aws_credentials.py` 사슬(env→ECS→IMDSv2) — 액세스 키를 env 에 두지 않는다 |
| `COLAB_VIZ_WORKDIR` | s3 소스 **필수** | 내려받은 바이트의 자리(캐시 — 상태 아님) |
| `COLAB_VIZ_WORK_MAX_BYTES` | s3 소스 **필수** | 캐시 상한 3상태 — 숫자(바이트) · `none`(명시 무제한) · **미설정 = 거부**. 넘으면 가장 오래 안 쓴 대상부터 지운다 · 대상 하나가 상한보다 크면 내려받기 전 413 |
| `COLAB_VIZ_PREVIEW_SINK` | — | `local`(기본 — `preview_dir` 를 nginx 가 서빙) \| `s3`(데이터 버킷 `previews/` 에 PUT, CloudFront 가 `/previews/*` 를 그 버킷으로) |
| `COLAB_VIZ_PREVIEW_S3_PREFIX` | s3 싱크 선택 | 기본 `previews`. URL(`COLAB_VIZ_PREVIEW_URL_BASE`)은 어느 싱크든 그대로 — FE 무변경 |

- 헬스 본문 `sourceMode`·`previewSink` 는 설정에 **선언된** 값(정적). `deploy_doctor` 가 읽는다.
- `kernel/{sigv4,aws_credentials,s3}.py` 는 core-api 원본의 byte-identical 복제본(`contracts/codegen/manifest.toml` 등기) —
  **여기서 고치지 않는다.**

## 타일 경로 인증 (`PLAN-SoT §9-〈68〉`)

`getRenderTile` 만 **서비스 토큰 또는 렌더에 묶인 단명 서명** 둘 중 하나를 받는다.
나머지 렌더 표면은 서비스 토큰 그대로다. 브라우저 지도 위젯은 서비스 토큰을 가질 수
없고 가져서도 안 되며, 이 경로는 계약상 **core-api 를 통과하지 않는 유일한 경로**다.

- 서명은 `tileUrlTemplate` **안에** 실린다(`?exp=…&sig=…`). 계약이 이 값을
  **불투명 문자열**로 정의했으므로 계약 개정이 없다. **FE 는 템플릿을 그대로 쓴다.**
- 서명이 덮는 것 = `renderId` + 만료 시각. **수명은 렌더 결과 수명 안**이다.
- 비밀은 `COLAB_VIZ_TILE_SIGNING_SECRET` 에서만 온다 — 코드에 기본 비밀이 없다.

## 정본이 값을 준 것 — 지어내지 않는다

- **진행 단계 3값** `파일 읽는 중` → `지도 그리는 중` → `범례 만드는 중` (문구 그대로).
  한 덩어리 「로딩 중」으로 두지 않는다 — 멈춘 것과 진행이 구분되지 않는다.
- **상태 3값** `그리는 중`·`완료`·`실패`. **취소 없음** — 정본에 취소 화면이 없다.
- **컨트롤은 둘뿐** — 팔레트(3종)와 구간 수(3~9, 기본 6).
- **한 번에 값 하나.** `variable` 을 생략하면 **viz-render 가 고른다.**
- **부분 실패는 `완료` 로 남는다.** 읽힌 조각으로 그리고, 못 읽은 조각을 이름으로 밝힌다.
- **좌표를 못 구하면 경성 실패다.** 근사 격자를 지어내지 않는다 (`DR-9`).
- **fill 은 정확일치로 판정한다.** `-20000` 은 HSR 의 **유효 하한**이지 결측이 아니다.

## 돌리기

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/python -m pytest -m "not e2e"                      # 단위 32건
COLAB_REFERENCE_DATA=<원천 루트> .venv/bin/python -m pytest -m e2e   # 실데이터 6건
```

`COLAB_REFERENCE_DATA` 가 없으면 e2e 는 **skip 이 아니라 fail** 이다 (`CLAUDE.md §4`).
