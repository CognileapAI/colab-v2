# P2-viz 실행 보고 — 미리보기 최소 렌더 경로 (W2 · `〈63〉-㉮`)

> **작성** 2026-08-23 · 레인 `P2-viz` · 소유 디렉터리 `services/viz-render/` 하나.
> **`services/viz-render/` 는 착수 시점에 53줄(헬스 + 빈 도메인 자리)이었다.** 여기서 D7 이 처음 섰다.
>
> **읽는 규칙** — 이 문서는 **증거(EVIDENCE)와 해석(INTERPRETATION)을 갈라 적는다**(`M-5`).
> 「증거」로 표시된 것은 명령과 그 출력이고, 「해석」으로 표시된 것은 **잠정**이다.
> 인용한 `파일:행` 은 전부 `cat -n`/`grep -n` 으로 확인했다(`M-7`).
> 커밋하지 않았다 — 커밋과 `03-HANDOFF`·`PLAN-SoT` 갱신은 메인 세션 몫이다.

---

## 0. 한 줄 결론

**4 op 이 실동작하고, 지원 4종이 실파일로 각각 그려졌으며, `uploadId` 대상 렌더가 동작한다.
`NB-B` 는 계약 개정 없이 닫혔다.** 다만 **정본 드리프트 1건 · 실측으로 드러난 스펙 공백 1건**을
새로 올린다(`§7`). 그리고 **이 레인은 작업지시서가 가정한 크기의 상단에 걸쳐 있다**(`§10`).

---

## 1. 진입조건 — 착수 시점 실측 (증거)

```
##### GATE contract-lint      exit=0   contract-lint green — seam 3건, 룰 위반 0.
##### GATE contract-breaking  exit=0   contract-breaking green — 기준 HEAD (3건) 대비 파괴적 변경 없음.
##### GATE event-lint         exit=0   event-lint green — 스키마 2건 컴파일 · valid 5건 통과 · invalid 8건 거부.
##### GATE event-breaking     exit=0   event-breaking green — 기준 HEAD (2건) 대비 파괴적 변경 없음.
##### GATE seam-consistency   exit=0   seam-consistency green — G-e 258건 · G-b 7건 · ㉠ 0건 · ㉡ 15건.
##### GATE banned-import      exit=0   banned-import green — .py 59건, 금지 import 0.
##### GATE import-boundary    exit=0   import-boundary green — 계약 전부 통과.
```

**계약은 동결 상태 그대로다.** `contracts/` 를 한 글자도 고치지 않았다 —
착수 시점과 종료 시점의 `contract-breaking` 이 둘 다 「파괴적 변경 없음」이다.

---

## 2. 만든 것 — 4 op

계약 정본 `contracts/seams/core-viz.yaml` 중 미리보기가 요구하는 넷.

| op | 경로 | 상태 |
|---|---|---|
| `createRender` | `POST /viz/v1/renders` | ✅ 202 + `RenderJob` · 400/404/413/415/401/503 |
| `getRender` | `GET /viz/v1/renders/{renderId}` | ✅ **실패도 200**, 이유는 `failure` |
| `getRenderTile` | `GET /viz/v1/renders/{renderId}/tiles/{z}/{x}/{y}.png` | ✅ PNG · 빈 타일도 200 · 409 · 410 |
| `listPalettes` | `GET /viz/v1/palettes` | ✅ 3종 · `ListEnvelope` |

### 파일 (전부 `services/viz-render/` 안)

```
src/colab_viz/kernel/     config.py · errors.py · ids.py
src/colab_viz/ports/      source.py          (대상 → 파일 Protocol + 파일시스템 어댑터)
src/colab_viz/domains/d7_visualization/
                          failures.py · palettes.py · hsr.py · grid.py
                          readers.py · raster.py · tiles.py · jobs.py
src/colab_viz/app/        main.py · deps.py · routes/{renders,style}.py
tests/                    conftest.py + 시험 6파일
Dockerfile · README.md · pyproject.toml · requirements{,-dev}.{in,txt}
```

**규모** — `src` 1,662줄 · `tests` 726줄 (`find … | xargs wc -l`).

### 정본이 값을 준 자리 — 그대로 썼다

- **단계 3값** `파일 읽는 중` → `지도 그리는 중` → `범례 만드는 중`
  (`Policy_업로드와_계보_확정.md:193` 문구 그대로). 한 덩어리 「로딩 중」이 없다.
- **상태 3값** `그리는 중`·`완료`·`실패`. **취소 경로가 코드에 없다.**
- **구간 수** 3~9 · 기본 6. **컨트롤은 팔레트와 구간 수 둘뿐**이고 표현 종류는 요청에 없다.
- **값 하나.** `variable` 생략 시 viz-render 가 고른다.
- **`partialFailure` 는 `status` 를 `실패` 로 만들지 않는다.**
- **`withoutReferenceGrid`** — 파일 안에 위경도가 있을 수 있는 포맷은 미리 막지 않는다.

---

## 3. 순서 — 진입조건 → 계약 게이트 → RED → 구현 → GREEN

### RED ① 시험이 먼저 있었다 (증거)

```
$ .venv/bin/python -m pytest -q -m "not e2e"
ImportError while loading conftest 'tests/conftest.py'
    from colab_viz.app.main import create_app
E   ModuleNotFoundError: No module named 'colab_viz.app.main'
```

**정직하게 적는다 — 이 RED 는 수집 단계 실패라 「오라클이 작동한다」의 증거로는 약하다.**
그래서 구현 뒤에 **변이 시험(mutation)** 으로 음성 오라클이 실제로 red 를 내는지 따로 증명했다.

### RED ② 변이 시험 — 음성 오라클이 fail-closed 임을 증명 (증거)

구현을 **일부러 PoC 의 버그로 되돌린** 뒤 시험이 red 를 내는지 봤다.

```
===== 변이 ① fill 을 범위 비교로 되돌린다 (mask = chunk <= DISPLAY_MIN)
FAILED tests/test_hsr_and_grid.py::test_fill_은_정확일치로_판정한다_20000은_살린다
  - assert np.float32(nan) == -200.0 ± 2.0e-04
===== 변이 ② 격자를 못 찾으면 지어내게 한다 (linspace 합성 후 성공 반환)
FAILED tests/test_hsr_and_grid.py::test_좌표를_못_구하면_경성_실패다_근사_격자를_만들지_않는다
  - Failed: DID NOT RAISE GridUnavailableError
===== 복원 후 재확인
30 passed, 6 deselected
```

**해석(잠정)** — 두 음성 시험은 「그럴듯하게 틀린 값」을 실제로 잡는다.
`DATA-REFERENCE §0` 이 「여덟 중 여섯이 에러를 안 냈다」고 적은 바로 그 부류를 겨눈 자리다.
⚠ **변이 ② 는 2건 중 1건만 red 였다** — 나머지 1건(`격자 없는 HSR 은 실패다`)은
**격자 로더에 닿기 전에** 「이 포맷은 파일 안에 좌표가 없다」로 먼저 막히기 때문이다.
즉 두 시험이 **서로 다른 층**을 지킨다. 한 시험이 두 층을 다 지킨다고 적지 않는다.

### GREEN — 최종 (증거)

```
$ .venv/bin/python -m pytest -q -m "not e2e"
32 passed, 6 deselected in 1.36s

$ COLAB_REFERENCE_DATA=<원천 루트> .venv/bin/python -m pytest -q -m e2e
6 passed, 30 deselected in 2.55s
```

---

## 4. 실렌더 증거 — 지원 4종 각각 실파일 1건 (GeoTIFF 를 가장 먼저 돌렸다)

**전부 원천 실파일이다. 지어낸 픽스처가 아니다.** 아래 값은 응답에서 그대로 옮겼다.
`불투명 픽셀` 은 경계 중심을 덮는 z6 타일을 PNG 로 디코드해 센 값이다 —
**200 + PNG 매직만으로는 투명 타일도 통과하므로** 거기까지 본다(`M-4` 의 무늬).

| # | 포맷 | 실파일 | 그린 값 | 경계(WGS84 · w/s/e/n) | 값 범위 | 타일 | 불투명 픽셀 |
|:--:|---|---|---|---|---|---|---:|
| ① | **GeoTIFF** | `HLS.S30.T51SYB.2025359T023019.v2.0.B02.tif` | `band1` | 125.245323 / 36.907034 / 126.522552 / 37.925591 | −1946.0 ~ 15762.165 | z6/54/24 (2,515 B) | **3,104** |
| ② | **NetCDF** | `gk2a_ami_le2_lst_ko_202005010000.nc` | `LST` (K) | 113.996422 / 29.31225 / 138.003586 / 46.35796 | 276.370 ~ 306.220 | z6/54/24 (6,467 B) | **14,825** |
| ③ | **Binary(HSR)** | `RDR_CMP_HSR_PUB_202508131000.bin.gz` | `에코` (dBZ) | 118.845779 / 30.107119 / 133.560669 / 43.572559 | −296.870 ~ 58.090 | z6/54/24 (11,473 B) | **30,231** |
| ④ | **HDF4** | `MOD15A2H.A2019273.h27v05.061.2020313082826.hdf` | `Fpar_500m` (Percent) | 103.936365 / 30.010417 / 130.523149 / 39.997917 | 0.0 ~ 1.0 | z6/52/25 (22,632 B) | **64,447** |

**격자 출처** — ② `lat2d.npy`+`lon2d.npy` · ③ **`rdr_500m_latlon.nc`**(`〈66〉` 정본 격자, 한 파일에 lat·lon 둘 다) ·
④ `lat2d_h27v05.npy`+`lon2d_h27v05.npy`(타일 짝을 맞춰 붙였다) · ① 파일 안 CRS(격자 파일 없음).

**교차검증 2건 (해석은 아래, 값은 증거)**
- ② `LST` 276.37~306.22 K 는 `DATA-REFERENCE §6` 의 PoC 실측 `LST vmin 270 / vmax 320` 안에 든다.
- ③ 경계 남단 `30.107119` 는 `DATA-REFERENCE §1` 이 적은 **`.nc` 판 lat min `30.107119`** 와 **자릿수까지 일치**한다
  (`.npy` 판은 `30.102751`). **`〈66〉` 이 고른 정본 격자를 실제로 쓰고 있다는 뜻이다.**

**음성 1건 (증거)** — 같은 HSR 실파일에서 **격자만 빼면** 결과가 이렇게 바뀐다:

```json
{"상태": "실패",
 "failure": {"code": "REFERENCE_GRID_MISSING",
             "message": "위경도를 담은 짝 파일이 없어요.",
             "details": {"detail": "RDR_CMP_HSR_PUB_202508131000.bin.gz: 위경도를 담은 짝 파일이 없다"}}}
```

**「완료」가 아니다.** PoC 구세대는 이 자리에서 격자를 지어내고 성공을 반환했다(`DR-9`).

---

## 5. RED→GREEN 시험 목록 (38건)

| 파일 | 건수 | 무엇을 지키는가 |
|---|---:|---|
| `test_palettes.py` | 3 | 팔레트 **정본대로 3종** · `PaletteOption` 모양 · 인증 |
| `test_render_flow.py` | 8 | 202+`RenderJob` · **단계 3값이 실제로 흐름** · `그리는 중`일 때만 `stage` · 결과 3필드 · 구간 3~9 · PNG/빈 타일 200 · 409 · 404 |
| `test_errors.py` | 7 | 대상 정확히 하나 · 404 · **413** · **415 + `renderableFormats`** · 실패 3종 code 구분 · **실패도 200** · **410** · 401 |
| `test_upload_target_and_partial.py` | 5 | **`uploadId` 대상(S-08)** · `expiresAt` 유무 · **부분 실패는 `완료`** · 전부 실패는 `실패` · `fileIds` 로 조각 하나 |
| `test_hsr_and_grid.py` | 6 | **fill 정확일치(−20000 생존)** · `num_data` 판독 · **좌표 합성 금지** · 격자 없는 HSR 은 실패 · 격자 주면 그려짐 · `짝 파일 없이 그려 보기` |
| `test_unconfigured.py` | 2 | 자격 증명 미배선 시 **헬스는 살고 렌더 표면은 503**(통과가 아니다) |
| `test_e2e_real.py` | 6 | **실데이터 4종** + 격자 없음 음성 + 기본 변수 선택·**이중 스케일 회귀** |

**단계 3값이 흐른 증거는 상태 스냅샷이 아니라 이력이다** — `job.stage_history == ["파일 읽는 중", "지도 그리는 중", "범례 만드는 중"]`
을 단언한다. 마지막 상태만 보면 「단계를 안 거치고 완료」와 구분되지 않는다.

---

## 6. `NB-B` — `RenderFailureCode` 부재를 어떻게 처리했나

**결론: 계약 개정 없이 표현된다. 멈출 사유가 아니었다.**

**증거** — `contracts/schemas/common.json:22-32`:

```json
"ErrorEnvelope": { "type": "object", "required": ["code", "message"],
  "properties": { "code": { "type": "string" }, ... } }
```

`code` 는 **enum 이 없는 자유 문자열**이다. 그리고 `contracts/seams/core-viz.yaml:351-353` 이
요구하는 것은 「`code` 로 정본의 실패 종류를 **구분**한다」이지 「전용 enum 을 신설한다」가 아니다.
따라서 3종을 서로 다른 문자열로 내면 계약이 요구한 구분이 성립한다.

| 정본 §9 상황 | `failure.code` | `failure.message` (정본 문구 그대로) |
|---|---|---|
| 그리는 서버에 연결 못 함 | `RENDER_SERVER_UNREACHABLE` | 지금 미리보기를 만들 수 없어요. 잠시 뒤 다시 시도해 주세요. |
| 그리다 시간 초과 | `RENDER_TIMEOUT` | 그리는 데 너무 오래 걸려요. 조각 하나나 좁은 기간으로 다시 해 보세요. |
| 그리다 알 수 없는 오류 | `RENDER_UNKNOWN_ERROR` | 미리보기를 만들다 문제가 생겼어요. |
| **기준 격자 파일 없음** | `REFERENCE_GRID_MISSING` | 위경도를 담은 짝 파일이 없어요. |

⚠ **넷째를 더한 것이 이 레인의 판단이다 — 짚어 둔다.** 정본 §9 는 「기준 격자 파일 없음」을
**별도 행**으로 두고 안내 문구도 복구 경로(`짝 파일 없이 그려 보기`)도 다르게 적었다.
「알 수 없는 오류」에 섞으면 화면이 정본의 그 행을 그릴 수 없다. **계약은 안 고쳤고**
(`code` 가 자유 문자열이라 고칠 필요가 없다), 남는 것은 아래 `[정본 무근거]` 한 줄뿐이다.

---

## 7. 새로 올리는 것 — 실측이 드러낸 3건

### ⓐ ⚠ `STOP-2` 가 「닫힘」인데 **260818 정본에는 옛 목록이 그대로 있다** (증거)

```
E-03 …/Policy_데이터셋_상세.md:199
| 그릴 수 없는 형식 | … **지금 그릴 수 있는 형식을 함께 적는다**(GRIB · NetCDF · BIN · GeoTIFF · HDF5) |
E-04 …/Policy_업로드와_계보_확정.md:238
| 그릴 수 없는 형식 | "이 형식은 아직 지도로 못 그려요. 지금 그릴 수 있는 형식은 GRIB · NetCDF · BIN · GeoTIFF · HDF5 예요." |
```

`P2.md §7 STOP-2` 는 「✅ 해결 — 정본 갱신 완료(260808 정본 md 4건·planning-base 2건)」로 적혀 있다.
**그런데 `planning/README.md §1` 이 정본으로 지목한 폴더는 `…_260818_이태헌` 이고, 그 안의 두 파일이
아직 5종 목록(GRIB 포함·HDF 버전 다름)을 말한다.** 이 문구가 그대로 화면에 서면 사용자에게
**없는 포맷을 안내**한다 — `STOP-2` 가 막으려던 바로 그 일이다.

**이 레인이 한 것** — 415 응답의 `details.renderableFormats` 는 **`〈51〉` 의 4종**을 낸다
(`["NetCDF","Binary","HDF4","GeoTIFF"]`). **정본 문구는 고치지 않았다** — 정본은 레인이 만지지 않는다.
**메인 세션에 올린다.** *(해석: `STOP-2` 이행이 260808 판에만 적용되고 260818 판에 안 따라온 것으로 보인다. 잠정이다.)*

### ⓑ ⚠ HSR 실파일에 **문서화되지 않은 음수 코드값이 2,073종** 있다 (증거)

`DATA-REFERENCE §2.1` 은 NULL 이 **정확히 세 값**(`-20000` 유효 하한 · `-25000` · `-30000`)이라고 적었다.
실파일을 직접 세었다:

```
파일: RDR_CMP_HSR_PUB_202508131000.bin.gz · 헤더 num_data: 3 · 실재 블록: 1
-20000 미만~ 구간의 서로 다른 값 개수: 2073
상위 8개(값,빈도): [(-30000, 3966662), (-29687, 2044), (-29381, 7), (-29375, 10),
                   (-29068, 1), (-29062, 1389), (-28756, 5), (-28750, 2233)]
-20000 정확일치 개수: 12 · -25000: 1964787 · -30000: 3966662
전체 최소/최대 원시값: -30000 5809
```

**사실 셋** — ① **`-20000` 은 실제로 12칸 존재한다.** 범위 비교(`<= -20000`)를 썼다면
이 12칸이 조용히 사라진다 — `§2.1` 의 경고가 이 파일에서 실물이다.
② 세 NULL 말고도 `-29687`·`-29062`·`-28750` 같은 값이 **수천 칸** 있다.
③ 그 결과 범례 하한이 **−296.87 dBZ** 로 잡혀(값/100) 실제 강수 구간이 한 색으로 뭉친다.

**이 레인이 한 것 — 규칙을 바꾸지 않았다.** 정확일치 판정을 그대로 두고 값을 살렸다.
범위로 자르면 그것이 `P2.md §2-26` 이 금지한 바로 그 행동이고, **무엇을 지우는지 모르는 채 지우는 것**이다.
**해석(잠정)** — −296 dBZ 는 물리적으로 반사도일 수 없으므로 이 값들은 **미문서화 코드값**일
가능성이 높다. 그러나 **어느 값이 무엇인지는 재지 않았고 정본·포맷 명세에도 없다.**
**`[정본 무근거]` 로 올리고 규칙을 짓지 않는다** — 값 집합의 정의는 레인이 관례로 정할 것이 아니다(`㊴-②`).

### ⓒ 구현 도중 잡은 조용한 버그 1건 — netCDF4 이중 스케일 (증거)

`netCDF4` 는 기본으로 `scale_factor`·`add_offset` 을 **자동 적용**한다. 그 위에 우리가 한 번 더
적용해 **GK2A `LST` 가 276 K 가 아니라 `2.76`** 으로 나왔다. **예외도 경고도 없었다.**
`set_auto_maskandscale(False)` 로 끄고 **원시값에서 정확일치로 fill 을 판정한 뒤** 스케일하도록 고쳤고
(`P2.md §10-(가)` 의 순서 규칙 그대로), 회귀 시험을 e2e 에 박았다(`200 < lo < hi < 400`).
**해석** — 이것 역시 「에러 없이 그럴듯한 값」 부류다. 자릿수를 단언하지 않았으면 통과했을 것이다.

---

## 8. `[정본 무근거]` — 지어내지 않고 표시한 것

| # | 무엇 | 정본이 말한 데까지 | 이 레인이 한 것 |
|---|---|---|---|
| **V-1** | **팔레트의 이름·라벨·색값** | `Policy_데이터셋_상세.md:163` 은 **「팔레트 3종」**까지만. 이름을 열거하지 않는다 | 개수 3 을 지키고 키·라벨·색은 viz-render 소유로 서빙(`listPalettes`). **계약에 이름을 안 박았다** |
| **V-2** | **`failure.code` 문자열 값** | 정본은 실패 **상황과 안내 문구**까지. 코드 어휘는 없다 | 4개 문자열은 레포 결정. **메시지는 정본 문구 그대로** |
| **V-3** | **`variable` 을 생략했을 때 어느 값이 기본인가** | 「한 번에 값 하나」까지. *어느* 값인지는 없다 | 「품질 플래그(`DQF_`·`QC`·`flag` …)를 **뒤로 미룬다**」 — 플래그는 값에 대한 메타데이터라는 근거. **지우는 것이 아니라 미루는 것**이고, 플래그밖에 없으면 그것을 그린다 |
| **V-4** | **렌더 시간 예산(시간 초과 판정선)** | 「그리다 시간 초과」 상황까지 | 120초 기본. 레포 결정 |
| **V-5** | **미리보기 격자 한 변 상한** | 없음 | 1024. `DR-11`(전체 적재 금지)의 렌더 쪽 표현 — 레포 결정 |
| **V-6** | **HSR 의 미문서화 음수 코드값 2,073종의 의미** | `DATA-REFERENCE §2.1` 은 3값까지 | **규칙을 만들지 않았다.** 정확일치만 적용하고 `§7-ⓑ` 로 올린다 |
| **NB-2 승계** | 임시 업로드 보관 시간 | 「이 화면을 벗어나면 사라진다」까지 | 1시간 기본(설정값). 계약이 발행자에게 열어 둔 자리 |
| **가정 승계** | 렌더 상한 500MB | 정본이 스스로 **[가정]** 이라 표시 | 그 표시를 지우지 않고 그대로 씀 |

---

## 9. 안 한 것 — 명시적으로

**범위 밖이라 안 했다 (`P2-EXEC §3` 레인 경계)**
- **데이터셋 상세의 2D 렌더 3종(격자·경계·점)** — P3. 표현 종류는 요청에도 없다.
- **`createScreenshot`** — P2 아님. 라우트를 501 로 잡아 두지도 **않았다**
  (이 seam 에는 「미구현 501 표」 규약이 없다. 그것은 `fe-core` 쪽 장치다).
- **`createPreviewRender`·`getPreviewRender` FE 중계 2 op** — `services/core-api/` 소유라 **`P2-api` 레인의 것**이다.
- **층 겹쳐 보기·불투명도·시각 선택 UI** — 지도 위젯의 일이고 계약에 없다.

**못 했다 / 남의 디렉터리라 안 건드렸다**
- **`infra/staging/` 환경변수 배선** — `COLAB_VIZ_SOURCE_ROOT`·`COLAB_VIZ_SERVICE_TOKEN` 을
  compose 가 넣어야 한다. `infra/` 는 어느 레인 소유도 아니다. **대신 없어도 뜨게 만들고,
  렌더 표면은 503 을 내게 했다** — 인증을 조용히 끄는 것과 반대다(시험 `test_unconfigured.py` 2건).
- **대상 해석의 실물 배선** — `datasetId`/`uploadId` → 파일은 `ports/source.py` 의 Protocol 이고
  들어 있는 어댑터는 **파일시스템 하나**다. `d5_*` 원장(W1)·객체 저장은 이 레인 소유가 아니다.
  **Protocol 이 그 자리를 비워 둔 것이 이 파일의 요점**이고, 원장이 서면 어댑터를 하나 더 붙인다.
- **`fileId` 동일성(`NB-A`)** — 파일시스템 어댑터에는 원장이 없어 **파일명에서 결정적으로 파생한
  ULID 모양 값**을 쓴다. `d3_file.id` 의 대체물이 아니고, 코드 주석에 그렇게 적어 두었다.
- **staging 배포** — 레인은 staging 을 건드리지 않는다(8 컨테이너 실서비스 중). ⚠ **다만
  `Dockerfile` 이 바뀌었다** — CMD 가 헬스 서버에서 uvicorn 앱으로 간다. 포트(8100)·경로(`/healthz`)는
  그대로지만 **본문의 `implemented` 가 false → true** 다. 재빌드·배포는 메인 세션 판단이다.
- **다중 인스턴스** — 렌더 결과가 프로세스 메모리에 있어 인스턴스가 여럿이면 타일 요청이 엉뚱한
  인스턴스로 갈 수 있다. 배포 형상은 `WU-I1` 소관이라 여기서 정하지 않고 코드 주석에 남겼다.
- **`planning-freshness` 게이트** — 이 워크트리에서 red 다. 사유는 **워크트리 상대경로에서
  정본 폴더를 못 찾음**(`…/.claude/worktrees/40 COLAB-기획/…`)이지 내 변경 때문이 아니다.
  착수 기준선에서도 돌리지 않았던 게이트라 **「내가 깼다/안 깼다」를 단정하지 않고 사실만 적는다.**

---

## 10. 게이트 — 종료 시점 (증거, 출력 그대로)

```
##### GATE banned-import          exit=0
  ai-service       .py    7건 · deny 7개
  core-api         .py   28건 · deny 18개
  pipeline-worker  .py   24건 · deny 0개
  viz-render       .py   23건 · deny 0개      ← 착수 시점 7건 (빈 스캐폴드) 에서 늘었다
banned-import green — .py 82건, 금지 import 0.

##### GATE import-boundary        exit=0
viz-render 층 — app > domains > ports > kernel  KEPT
Contracts: 8 kept, 0 broken.
import-boundary green — 계약 전부 통과.

##### GATE ai-no-lineage-write    exit=0   green — 계약·코드·체인 세 층 모두에서 쓰기 경로가 없다.
##### GATE contract-lint          exit=0   green — seam 3건, 룰 위반 0.
##### GATE contract-breaking      exit=0   green — 기준 HEAD (3건) 대비 파괴적 변경 없음.
##### GATE event-lint             exit=0   green — 스키마 2건 컴파일 · valid 5건 통과 · invalid 8건 거부.
##### GATE event-breaking         exit=0   green — 기준 HEAD (2건) 대비 파괴적 변경 없음.
##### GATE seam-consistency       exit=0   green — G-e 258건 · G-b 7건 · ㉠ 0건 · ㉡ 15건.
##### GATE migration-single-head  exit=0   green — 두 체인 모두 head 1개.
##### GATE rls-coverage           exit=0   green
##### GATE boundary-selftest      exit=0   green — 경계 게이트 3종 모두 틀린 것을 틀렸다고 말한다 (fail-closed 증명)
##### GATE planning-freshness     exit=1   red — 정본 폴더가 없다 (워크트리 상대경로 문제 · §9 참조)
```

⚠ **`banned-import` 가 viz-render 를 「deny 0개」로 세는 것은 설정대로다** —
`gates/config/boundaries.toml:25-29` 가 이 단위의 `banned` 를 빈 목록으로 두었다
(「정본이 *여기에만* 들어간다고 못 박은 곳」). **즉 이 게이트가 지키는 것은 「viz 가 geo 를 쓴다」가
아니라 「core-api 가 geo 를 안 쓴다」다.** 내가 rasterio·netCDF4·pyhdf 를 넣었어도 green 인 것이
정상이고, **green 이 「geo 를 안 썼다」는 뜻이 아니다** — 감추지 않고 적는다.

### 컨테이너 실동작 (증거 · 일회용 `p2viz_` 접두사, 호스트 포트 비공개)

```
$ docker build -t p2viz_build_check services/viz-render        → sha256:692ee99df353…
$ docker run -d --name p2viz_probe p2viz_build_check
$ docker exec p2viz_probe … /healthz
{"unit":"viz-render","status":"alive","implemented":true}
$ docker exec p2viz_probe … /viz/v1/palettes
palettes -> 503 {"code":"SERVICE_TOKEN_UNCONFIGURED","message":"이 인스턴스에 서비스 자격 증명이 배선되지 않았다."}
$ docker rm -f p2viz_probe
```

---

## 11. 완료 판정 대조 (`P2-EXEC §4 W2·P2-viz`)

| 판정 항목 | 결과 |
|---|:--:|
| 4 op 실동작 | ✅ `§2`·`§5` |
| 지원 4종 각각 최소 1건 실렌더 (**GeoTIFF 를 가장 먼저**) | ✅ `§4` — ①GeoTIFF ②NetCDF ③Binary ④HDF4 |
| 진행 단계 3값이 실제로 흐름 | ✅ `stage_history` 단언 |
| **`uploadId` 대상 렌더 동작 (S-08)** | ✅ `test_uploadId_대상_렌더가_동작한다` + e2e 6건 전부 `uploadId` 로 돌렸다 |
| `banned-import` · `import-boundary` green | ✅ `§10` |

**`P2-EXEC §6-10`(미리보기가 실제로 그려진다)의 절반만 이 레인이 닫는다** —
「S-04 에서 그린 미리보기가 S-08 로 그대로 이어진다」는 **FE 두 레인(W3)** 이 소비해야 증명된다.
서버 쪽 전제(같은 `renderId` 로 `uploadId` 대상 결과를 계속 조회할 수 있다)는 여기서 섰다.

---

## 12. ⚠ 레인 크기 — 정직하게

**`P2-EXEC §8` 위험 1번이 나에 관한 것이라 답한다.**
advisor 는 흡수(㈎)에 반대하며 「렌더 4포맷 + 타일 + 팔레트는 사실상 P3 의 심장이라 P2 가 한 WU 로
감당 못 한다」고 적었고, Ted 가 흡수를 골랐다.

**관측(증거)** — 산출은 `src` 1,662줄 + `tests` 726줄, 새 런타임 의존 24개(전이 포함),
그리고 **작업지시서에 없던 발견 3건**(`§7`)이 나왔다. **범위를 줄이지 않았다** — 4 op·4포맷·타일·팔레트를
다 만들었고, 완료 판정 다섯 항을 다 충족했다.

**해석(잠정) — 「감당 못 한다」까지는 아니었지만 「가정한 크기의 상단」이었다.** 근거 셋:
1. **advisor 가 걱정한 부분(4포맷 디코딩)이 예상보다 쌌다** — `D5` 가 이미 실측한 지식
   (매직바이트·HSR 헤더·격자 파일 위치·3 NULL)이 `DATA-REFERENCE` 에 값으로 적혀 있어
   **다시 재지 않았다.** 이 문서가 없었으면 이 레인은 몇 배가 됐다.
2. **대신 걱정 목록에 없던 것이 비쌌다** — 타일 좌표 변환이 아니라 **「그려졌다」를 무엇으로
   판정하는가**(투명 타일 문제) · **이중 스케일 같은 조용한 오류**였다.
3. **가장 큰 미완은 코드가 아니라 배선이다** — 대상 해석 어댑터와 환경변수는 남의 디렉터리다.
   **P2 가 「미리보기가 실제로 그려진다」로 닫히려면 W3·메인 세션에서 그 배선이 붙어야 한다.**

**따라서 절단을 재론해 달라고 요청하지 않는다.** 다만 **`WORK-UNITS §7` 개정 시
「P3 에서 무엇이 빠져나갔는지」에 이 목록을 그대로 넣기를 권한다**(`§8` 위험 1-ⓑ):
*미리보기 렌더 4 op · 4포맷 판독 · XYZ 타일 서빙 · 팔레트 3종*. **P3 에 남는 것은
2D 렌더 3종(격자·경계·점) · 스크린샷 · 겹쳐 보기 합성**이다. 안 적으면 P3 이 자기 크기를 모른다.

---

## 13. 메인 세션에 올리는 것

| # | 무엇 | 왜 레인이 못 닫나 |
|---|---|---|
| **1** | **`STOP-2` 재개봉 여부** — 260818 정본 `E-03:199`·`E-04:238` 이 아직 5종 목록(GRIB 포함)이다 | 정본 문구는 Ted 결정 사항이다. 레인이 고치면 코드가 정본을 덮어쓴다 |
| **2** | **HSR 미문서화 음수 코드값 2,073종** — `DATA-REFERENCE §2.1` 의 「NULL 은 세 값」이 실물과 안 맞는다 | 값 집합의 정의다. 관례로 정하면 `㊴-②` 위반. 규칙을 안 만들고 정확일치만 유지했다 |
| **3** | **`infra/staging/` 환경변수 2개 배선** + Dockerfile 변경분 재빌드 판단 | `infra/` 는 이 레인 소유가 아니고 staging 은 실서비스 중이다 |
| **4** | **`ports/source.py` 어댑터 교체** — `d5_*` 원장(W1)·객체 저장이 서면 | 남의 디렉터리의 산출을 전제한다 |
| **5** | **`NB-B` 를 「자유 문자열로 표현됨」으로 닫아도 되는가** + 넷째 코드(`REFERENCE_GRID_MISSING`) 승인 | 계약 해석이라 기록(`PLAN-SoT §9`)이 필요하다 |
| **6** | **`banned-import` 가 viz 쪽은 아무것도 안 막는다는 사실** | 게이트 설정 정본(`boundaries.toml`)의 문제이고, 바꿀지 말지는 메인 판단이다 |

**다음 세션(W3 FE) 진입조건** — ① `services/viz-render` 의 4 op 이 이 보고서대로 동작
② `listPalettes` 가 팔레트 값의 출처다(FE 하드코딩 금지) ③ FE 는 `tileUrlTemplate` 을
**해석하지 않고 그대로** 지도 위젯에 넘긴다 ④ 실패는 4xx 가 아니라 **200 + `failure`** 로 온다.

---
---

# 부록 A — 후속 레인 (게이트 ② `approve-with-changes` 2건 처리)

> **작성** 2026-08-23 · 레인 `P2-viz` 후속 · 소유 디렉터리 `services/viz-render/` 하나.
> 본문(`§1`~`§13`)은 **한 글자도 고치지 않았다.** 아래는 추가분이다.
> **커밋하지 않았다.** `contracts/` 무수정 — 본문의 「계약은 동결 상태 그대로다」가 그대로 유효하다.
> 증거·해석 분리 규칙(`M-5`)은 여기서도 같다.

## A-0. 무엇을 닫았나

| # | advisor 지적 | 처리 |
|---|---|---|
| **A** | `getRenderTile` 이 서비스 토큰을 요구해 **브라우저 지도 위젯이 도달할 수 없다** — 구현은 계약대로인데 실배포에서 전량 401 | `PLAN-SoT §9-〈68〉` 대로 **렌더에 묶인 단명 서명**을 `tileUrlTemplate` 안에 실었다. 계약 무수정 |
| **B** | 값 범위 단언이 **LST 하나뿐**이라 `§7-ⓒ`(100배 틀린 값) 부류를 다른 포맷에서 못 잡는다 | Fpar·dBZ·HSR 남단 3건 추가 + **각각 변이로 red 확인** |

---

## A-1. Task A — 타일 경로 인증, 만든 대로

### 설계 (계약을 왜 안 고쳤나)

계약 `core-viz.yaml` 의 `RenderResult.tileUrlTemplate` 은 **「core 는 이 문자열을 해석하지
않고 전달만 한다」**는 **불투명 문자열**이다. 따라서 **그 문자열 안에 무엇이 들었는지는
계약 사항이 아니다.** 서명을 템플릿 안에 실으면 계약을 한 글자도 안 고치고 닫힌다.

```
GET /viz/v1/renders/{renderId}/tiles/{z}/{x}/{y}.png?exp=<epoch초>&sig=<HMAC-SHA256 hex>
```

| 결정 | 값 | 근거 |
|---|---|---|
| 서명 알고리즘 | `HMAC-SHA256(비밀, "renderId\n exp")` · hex · **상수시간 비교** | `〈68〉-ⓐ` |
| 서명이 덮는 것 | **`renderId` + 만료 시각** | 렌더 경계는 `renderId` 가 긋는다 |
| 서명이 **안** 덮는 것 | 타일 좌표 `z/x/y` | 한 렌더의 타일 수백 장이 서명 하나로 서야 지도가 성립한다. 좌표를 덮으면 **치환 전 템플릿 자체가 성립하지 않는다** |
| 적용 범위 | **타일 경로 하나뿐.** 나머지 렌더 표면은 서비스 토큰 그대로 | `〈68〉-ⓑ`. 라우터를 갈라 **기계가 지키게** 했다 |
| 수명 | `tile_signature_ttl_seconds`(기본 = 결과 수명) **와 작업 `expires_at` 중 이른 쪽** | `〈68〉-ⓓ` |
| 비밀 | `COLAB_VIZ_TILE_SIGNING_SECRET` — **코드에 기본값 없음** | 기본 비밀을 두면 모든 배포가 같은 비밀을 쓴다 |
| 미배선 | **렌더 표면 전체가 503** (`TILE_SIGNING_UNCONFIGURED`) | 본문 `§9` 가 세운 「조용히 인증을 끄지 않는다」 그대로 |

**FE 는 아무것도 안 바뀐다** (`〈68〉-ⓒ`) — 템플릿을 받아 `{z}`·`{x}`·`{y}` 만 치환한다.
W3 진입조건 ③(「해석하지 않고 그대로 넘긴다」)이 **그대로 유효**하다.

### 왜 비밀 미배선이 「503」이고 「서명 검사 생략」이 아닌가

비밀이 없으면 `createRender` 는 **서명 없는 `tileUrlTemplate`** 을 발급하게 된다. 그 상태로
202 를 내면 FE 는 「받았는데 타일이 전부 401」이라는 **이 결정이 막으려던 바로 그 자리**에
다시 선다. 그래서 서비스 토큰과 **같은 층에서** 막는다 — `app/deps.py:_require_configured`.

### 새로 생기거나 바뀐 파일 (전부 `services/viz-render/` 안)

```
src/colab_viz/kernel/signing.py            신규 — 서명 발급·검증 (kernel 층: 위 세 층이 쓴다)
src/colab_viz/kernel/config.py             `tile_signing_secret` · `tile_signature_ttl_seconds` · 환경변수
src/colab_viz/app/deps.py                  `_require_configured` · `require_caller_or_tile_signature`
src/colab_viz/app/routes/renders.py        `tile_router` 분리 (타일만 다른 Depends)
src/colab_viz/app/main.py                  `tile_router` 등록 · JobStore 에 비밀·수명 주입
src/colab_viz/domains/d7_visualization/jobs.py  `JobStore._tile_url` — 템플릿에 서명을 싣는다
tests/conftest.py                          `make_client(...)` + `SIGNING_SECRET`
tests/test_errors.py                       세 곳이 `Settings` 를 직접 세워서 비밀을 넘긴다 (단언은 무수정)
tests/test_tile_signature.py               신규 10건
README.md                                  「타일 경로 인증」절 + 환경변수 3개
```

**규모** — `src` 1,662 → **1,809줄** · `tests` 726 → **909줄**.
층 순서(`app > domains > ports > kernel`)를 지켰다 — `signing` 은 kernel 이라 domains·app 둘 다 쓴다(`import-boundary` green).

### RED → GREEN — 다섯 경우를 **전부 red 로 먼저 봤다**

⚠ **첫 red 는 수집 실패라 약한 오라클이었다** (`Settings.__init__() got an unexpected
keyword argument 'tile_signing_secret'`). 본문 `§3` 이 같은 약점을 적어 둔 자리라 반복하지
않았다 — **설정 필드만 먼저 넣어** 앱이 뜨게 한 뒤, **각 시험이 자기 이유로 red 를 내는
행동 수준 RED** 를 다시 받았다. 아래가 그것이다 (증거 · 출력 그대로).

```
##### RED ② 행동 수준 — 서명 도입 전 구현에 대고
FAILED test_템플릿의_서명만으로_타일을_받는다_토큰_없이
  AssertionError: assert ('sig=' in '/viz/v1/renders/01M0QDV96W3GPPN561R3EJ5GZE/tiles/6/54/24.png')
                          ↑ 템플릿에 서명이 없다
FAILED test_만료된_서명은_거절된다
  AssertionError: assert '만료' in '호출자 신원을 확인할 수 없다.'
FAILED test_다른_렌더의_서명은_통하지_않는다      IndexError (템플릿에 질의부가 없다)
FAILED test_변조된_서명은_거절된다                ValueError (같은 이유)
FAILED test_틀린_서비스_토큰은_서명이_없으면_401  (비ASCII 헤더 — 시험 쪽 결함, 아래 참조)
FAILED test_서명_수명은_렌더_결과_수명을_넘지_않는다  IndexError
FAILED test_서명_비밀이_없으면_렌더_표면은_503_이다   AssertionError: assert 200 == 503
```

**정직하게 적는다 — 열 중 둘은 이 시점에 이미 green 이었다**:
`서명이_아예_없으면_401` 과 `서비스_토큰은_서명_없이도_여전히_통한다`.
**그것이 정상이다** — 이 둘은 **새 기능이 아니라 새 기능이 깨뜨리면 안 되는 것**을 잡는
가드다(전자는 「서명 도입이 곧 타일 개방」이 되는 것을, 후자는 회귀를). 새 행동에 대한
red 를 낸 것은 나머지 여덟이다.
⚠ 그리고 `틀린_서비스_토큰…` 의 red 는 **구현이 아니라 내 시험이 틀려서**였다(헤더에 한글
`틀린값`을 넣어 `UnicodeEncodeError`). ASCII 로 고쳤다 — **오라클이 아니었던 red 를
오라클이었던 것처럼 세지 않는다.**

**GREEN — 다섯 경우 (증거)**

| # | 요구된 경우 | 시험 | 결과 |
|:--:|---|---|:--:|
| ① | **유효한 서명이 통과한다** | `test_템플릿의_서명만으로_타일을_받는다_토큰_없이` — Authorization 헤더 **없이** 200 + PNG | ✅ |
| ② | **만료된 서명은 실패한다** | `test_만료된_서명은_거절된다` — 수명 0초 인스턴스에서 **실제로 1.1초 기다려** 만료시킨다. 시계를 흉내내지 않았다 | ✅ 401 |
| ③ | **렌더 A 의 서명이 렌더 B 에서 안 통한다** | `test_다른_렌더의_서명은_통하지_않는다` — B 자기 서명 200(대조군) vs A 서명 이식 401 | ✅ 401 |
| ④ | **변조된 서명은 실패한다** | `test_변조된_서명은_거절된다` — ㉠ 서명 끝 한 글자 뒤집기 ㉡ **서명은 그대로 두고 `exp` 만 +86400** | ✅ 둘 다 401 |
| ⑤ | **서비스 토큰은 여전히 통한다** | `test_서비스_토큰은_서명_없이도_여전히_통한다` (+ 틀린 토큰은 401) | ✅ 200 |

**④-㉡ 이 이 표의 핵심이다** — `exp` 를 서명에서 빼면 호출자가 만료 시각을 늘려 **영구
자격**을 만든다. 「만료가 있다」와 「만료를 못 늘린다」는 다른 사실이고, ② 만으로는 안 갈린다.

**덧붙인 3건 (요구 밖이지만 이 다섯을 떠받친다)**
- `test_서명_수명은_렌더_결과_수명을_넘지_않는다` — 서명 수명을 **24시간**으로, 결과 수명을
  **60초**로 배선해도 발급된 `exp` 가 `expiresAt` 를 안 넘는다(`〈68〉-ⓓ`). 두 수명이 같은
  기본값이면 이 규칙이 **작동하는지 안 하는지 구분되지 않아서** 일부러 벌려 놓고 본다.
- `test_비밀이_다르면_서명이_통하지_않는다` — 비밀이 진짜로 서명에 들어가는지. 상수를
  반환하는 구현이면 여기서 걸린다.
- `test_서명_비밀이_없으면_렌더_표면은_503_이다_통과가_아니다` — 본문 `test_unconfigured.py`
  2건과 같은 무늬를 서명 축으로 한 번 더.

```
$ .venv/bin/python -m pytest -q -m "not e2e"
42 passed, 6 deselected in 3.10s          (착수 시 32 → 42, 새 10건)

$ COLAB_REFERENCE_DATA=<원천 루트> .venv/bin/python -m pytest -q -m e2e
6 passed, 42 deselected in 2.93s
```

### 컨테이너 실동작 — 503 갈래가 실제로 갈리는지 (증거 · 일회용 `p2viz_`, 호스트 포트 비공개)

```
$ docker build -t p2viz_sig_check services/viz-render     → sha256:8357c0162a68…

# ㉠ 아무것도 안 넣음
/healthz          200 {"unit":"viz-render","status":"alive","implemented":true}
/viz/v1/palettes  503 {"code":"SERVICE_TOKEN_UNCONFIGURED", …}
…/tiles/6/54/24.png 503 {"code":"SERVICE_TOKEN_UNCONFIGURED", …}   ← 타일도 열리지 않는다

# ㉡ 서비스 토큰만 넣음 — 여기서 갈린다
/viz/v1/palettes  503 {"code":"TILE_SIGNING_UNCONFIGURED","message":"이 인스턴스에 타일 서명 비밀이 배선되지 않았다."}

# ㉢ 둘 다 넣음
/viz/v1/palettes  200 {"items":[{"palette":"단색-파랑", …
$ docker rm -f … ; docker rmi -f p2viz_sig_check
```

**㉡ 이 새 사실이다** — 토큰만 배선한 인스턴스는 **뜨지만 렌더를 안 연다.** 「토큰은 넣었는데
타일 비밀을 빠뜨린」 배선 실수가 **조용히 통과하지 않는다**는 뜻이다.

### ⚠ 감추지 않고 적는 것 — 만료된 렌더의 타일이 FE 에는 410 이 아니라 401 로 보인다

서명 수명이 결과 수명 안에 들어 있으므로(`〈68〉-ⓓ`) **결과가 만료되면 서명도 같이 만료**된다.
인증은 작업 조회보다 **먼저** 서므로(안 그러면 404/410 이 인증 없이 「그 렌더가 있느냐」를
알려 주는 신탁이 된다) FE 가 받는 응답은 **401 + 「타일 주소의 서명이 만료됐다. 미리보기를
다시 그려 주세요.」**이고, 계약의 **410 은 서비스 토큰으로 부를 때 그대로 살아 있다**
(`test_수명이_다한_렌더의_타일은_410` 무수정 통과). 두 응답의 **행동 지시는 같다**(다시 그려라).
**계약 위반이 아니다** — 410 이 사라진 것이 아니라 서명 경로가 그 앞에서 답하는 것이다.
다만 **FE 가 「410 이면 다시 그리기」로 분기하려 했다면 401 도 같이 봐야 한다.** W3 에 넘긴다.

### 이번에도 안 한 것

- **서명 회전·폐기·CDN 캐시 키 설계** — `〈68〉` 이 P3·I3 로 명시했다.
- **엣지가 타일 요청에 무엇을 붙이는지** — `〈68〉` 대로 **W5 staging 실측**에서 눈으로 본다.
  계약대로인 것과 배포에서 도달하는 것은 다른 사실이다(이 지적 자체가 그 사례였다).
- **`infra/staging/` 배선** — 환경변수가 **둘에서 셋으로 늘었다**(`COLAB_VIZ_TILE_SIGNING_SECRET`).
  `infra/` 는 이 레인 소유가 아니다. 본문 `§13-3` 을 **이 한 줄만큼 키워** 다시 올린다.
- **다중 인스턴스** — 비밀이 인스턴스마다 다르면 서명이 인스턴스를 넘지 못한다.
  작업 저장소가 이미 프로세스 메모리라(본문 `§9`) **새로 생긴 제약이 아니다.** 배포 형상은 `WU-I1`.

---

## A-2. Task B — 포맷별 값 범위 단언 3건

**왜 필요한가** — 본문 `§7-ⓒ` 의 이중 스케일 버그는 **픽셀이 존재하고 값이 100배 틀렸다.**
불투명 픽셀 세기(`_assert_drawn`)는 그 부류를 **원리적으로** 못 잡는다. LST 하나에만 있던
자릿수 단언을 나머지로 넓혔다.

| 포맷 | 새 단언 | 값의 출처 | 실측값 |
|---|---|---|---|
| **HDF4 (Fpar)** | `0 <= lo <= hi <= 1` | `DATA-REFERENCE §6` cmap 정본 `Fpar_500m` **vmin 0 / vmax 1** · 본문 `§4-④` 실측 `0.0 ~ 1.0` | 0.0 ~ 1.0 |
| **Binary (dBZ)** | `hi <= 100` | `DATA-REFERENCE §2`·`§2.2` 「반사도(dBZ) = **값/100**」 · 본문 `§4-③` 실측 상한 `58.09` | 58.09 |
| **Binary (남단)** | `south == 30.107119 ± 1e-6` | `DATA-REFERENCE §1` **`.nc` 판 lat min `30.107119`**(`.npy` 판은 `30.102751`) · `〈66〉` | 30.107119 |

### ⚠ 지어내지 않은 자리 두 곳 — 명시한다 (`M-4`)

**ⓐ dBZ 의 `100` 은 `DATA-REFERENCE` 에도 본문 보고에도 없는 숫자다.** 후속 지시가 준
값이고, 이 자리에서는 **「물리 상한」이 아니라 자릿수 그물**로만 쓴다 — 스케일(`/100`)이
빠지면 상한이 `5,809` 로 뛰므로 100 이든 200 이든 잡힌다. **정본 근거가 있는 숫자인 척
하지 않는다.** 실측 상한 58.09 와 그물 100 사이의 여유는 의도된 것이다.

**ⓑ dBZ 의 하한은 단언하지 않았다.** 이 실파일의 하한은 **−296.87 dBZ** 이고, 그 원인인
**미문서화 음수 코드값 2,073종**은 본문 `§7-ⓑ` 로 **상신된 열린 질문**이다. 여기서 하한을
박으면 레인이 값 집합의 정의를 관례로 정하는 것이 된다(`㊴-②`). **그물을 위쪽에만 친다.**

### 변이 확인 — 세 단언이 **실제로 red 를 낸다** (증거 · 출력 그대로)

「단언을 넣었다」와 「단언이 작동한다」는 다른 사실이라 셋 다 **구현을 일부러 틀리게 만들어** 봤다.

```
===== 변이 ① dBZ 스케일 제거 — hsr.py: SCALE_DIVISOR = 100.0 → 1.0
FAILED test_e2e_3_binary_hsr
  AssertionError: ('dBZ 상한이 물리 범위를 넘는다 — 스케일(/100)이 빠졌을 수 있다', -29687.0, 5809.0)

===== 변이 ② HDF4 스케일 인자 제거 — readers.py: values = values * scale_factor → values
FAILED test_e2e_4_hdf4
  AssertionError: ('Fpar 가 0~1 밖이다 — 스케일 인자를 놓쳤을 수 있다', 0.0, 100.0)

===== 변이 ③ HSR 격자를 `.npy` 판으로 바꿔 먹인다 (시험 쪽 변이)
FAILED test_e2e_3_binary_hsr
  AssertionError: 남단이 정본 격자(.nc)의 lat min 과 다르다 — .npy 판을 읽고 있을 수 있다
  assert 30.102750778198242 == 30.107119 ± 1.0e-06

===== 셋 복원 후 재확인
42 passed, 6 deselected   ·   6 passed, 42 deselected
```

**관측 세 줄 — 이것이 이 작업의 요점이다.**
1. **변이 ①·② 모두 「에러 없이 그럴듯한 값」이었다.** `5,809` 도 `100.0` 도 **타일은 멀쩡히
   그려졌고 불투명 픽셀도 그대로였다.** 자릿수를 안 봤으면 셋 다 green 이었다 — `§7-ⓒ` 가
   실제로 그렇게 통과할 뻔했던 경로다.
2. **변이 ②의 값이 `0.0 ~ 100.0` 인 것을 그대로 적어 둔다.** 「Percent」 이름을 가진 값이
   0~1 로 정규화돼 나온다는 본문 `§4-④` 의 관측과 정확히 맞물린다 — **스케일 인자 0.01 이
   실제로 적용되고 있다**는 뜻이고, 이제 그것이 시험으로 고정됐다.
3. **변이 ③ 은 `.npy` 격자로도 렌더가 성공했다** — 상태 `완료`, 픽셀도 그려졌다.
   **잘못된 격자를 쓰는 것은 픽셀 세기로 절대 안 잡힌다.** `〈66〉` 의 정본 격자 선택이
   코드에서 유지되는지를 지키는 것은 이제 이 한 줄뿐이다.

---

## A-3. 게이트 — 후속 종료 시점 (증거, 출력 그대로)

```
##### GATE banned-import          exit=0   green — .py 88건, 금지 import 0.  (viz-render 24건 · deny 0개)
##### GATE import-boundary        exit=0   green — Contracts: 8 kept, 0 broken.
##### GATE ai-no-lineage-write    exit=0   green — 계약·코드·체인 세 층 모두에서 쓰기 경로가 없다.
##### GATE contract-lint          exit=0   green — seam 3건, 룰 위반 0.
##### GATE contract-breaking      exit=0   green — 기준 HEAD (3건) 대비 파괴적 변경 없음.  ("No changes detected")
##### GATE event-lint             exit=0   green — 스키마 2건 컴파일 · valid 5건 통과 · invalid 8건 거부.
##### GATE event-breaking         exit=0   green — 기준 HEAD (2건) 대비 파괴적 변경 없음.
##### GATE seam-consistency       exit=0   green — G-e 258건 · G-b 7건 · ㉠ 0건 · ㉡ 15건.
##### GATE migration-single-head  exit=0   green — 두 체인 모두 head 1개.
##### GATE rls-coverage           exit=0   green
##### GATE boundary-selftest      exit=0   green — 경계 게이트 3종 모두 틀린 것을 틀렸다고 말한다
##### GATE planning-freshness     exit=1   red — 정본 폴더가 없다 (워크트리 상대경로 · 본문 §9 와 같은 사유)
```

**본문 `§10` 과 판정이 한 줄도 다르지 않다** — `banned-import` 의 `.py` 총계만 82 → 88 로 늘었다
(다른 레인이 같은 시각에 돈다. **viz-render 는 23 → 24**, 늘어난 하나가 `kernel/signing.py` 다).
`contract-breaking` 이 「No changes detected」라고 답하는 것이 **계약을 안 고쳤다는 증거**다.
`planning-freshness` red 는 본문 `§9` 가 적은 그 사유 그대로이고 **내 변경 때문이 아니다.**

⚠ **본문 `§10` 의 경고가 여기서도 유효하다** — `banned-import` 는 viz-render 쪽에서 아무것도
막지 않는다(`boundaries.toml` 이 이 단위의 `banned` 를 빈 목록으로 뒀다). **`hmac`·`hashlib`
를 새로 쓴 것이 green 인 것은 정상이고, green 이 「검사됐다」는 뜻이 아니다.**

---

## A-4. 메인 세션에 올리는 것 (본문 `§13` 에 더하는 분)

| # | 무엇 | 왜 레인이 못 닫나 |
|---|---|---|
| **3′** | **`infra/staging/` 환경변수가 2개 → 3개다** — `COLAB_VIZ_TILE_SIGNING_SECRET` 이 늘었다. 이것이 없으면 **렌더 표면 전체가 503** 이다(헬스는 산다) | `infra/` 는 이 레인 소유가 아니고 staging 은 실서비스 중이다 |
| **7** | **만료된 렌더의 타일이 FE 에 401 로 보인다**(`A-1` 끝) — 계약의 410 은 서비스 토큰 경로에 그대로 살아 있다. W3 지시에 「401 도 「다시 그리기」로 분기」를 한 줄 넣을지 | FE 두 레인의 소비 규약이다 |
| **8** | **서명 비밀의 인스턴스 간 공유** — 다중 인스턴스면 비밀이 같아야 서명이 넘어간다 | 배포 형상은 `WU-I1` |

**W3 FE 진입조건 — 본문 `§13` 의 넷은 그대로 유효하다.** ③ 「`tileUrlTemplate` 을 해석하지
않고 그대로 넘긴다」가 **이번 변경으로 더 중요해졌다** — 템플릿에서 질의부를 떼거나 다시
조립하면 서명이 깨진다. **치환은 `{z}`·`{x}`·`{y}` 셋뿐이다.**
