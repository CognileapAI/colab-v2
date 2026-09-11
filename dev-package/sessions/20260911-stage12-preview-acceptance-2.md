# Stage 1·2 preview acceptance — 2026-09-11

> 부모 수용 정정: 아래는 여러 시점의 누적 이력이다. 최신 기능 검증 대상은 f8ac7ee이며, 30f5adf 최종 배포/doctor는 별도 `reports/stage12-release-acceptance/release.md`로 확인한다. browser doctor12와 배포 doctor15를 혼용하지 않는다. 과거 raw/netcdf.har의 완전 비밀 제거 주장은 부모 검사에서 성립하지 않아 해당 HAR를 반입·공유하지 않았다. BF7의 과거 출처 불명 저장파일은 수용에서 제외하고 fresh headed64,138B 증거만 사용한다. J1 기능은 독립 검토 수용, 새 버전 관련 전체 게이트 연결 전까지 대장은 partial이다.

## Boundary

- Source checkout: `f8ac7ee07ff6a532447ac73e3cf3735b6db9d3e5`
- Observed dev: server `9e3ff19`, web `16710a4`
- A new deployment was announced while testing. New write journeys were paused so results from two versions are not mixed.
- Browser sessions: `stage12-preview-acceptance` (professor), `stage12-preview-researcher` (researcher).

## Result

NetCDF passed the complete deployed journey with real bytes: upload, `LST` choice, map render, `TEST Stage12 Preview NetCDF 20260911` registration, and detail reload. The resulting dataset is `01M27HVH4VG6B75RGQQQZGH87Q`.

A registered `surface.grib` also decoded on dev: the UI exposed 72 message candidates and rendered message 1 with a real map and legend. This is partial WU-PREVIEW evidence because GRIB1 was not independently exercised and the selected source file returned to the representative PNG after reload.

The map-state filter changed the live list from 16 total datasets to 2 with maps. A same-lab researcher saw no default-grid action and the corresponding PUT returned 403. No other-lab credential was available, so cross-lab behavior is unverified.

The exact row-by-row classification is in `dev-package/reports/stage12-preview-acceptance/summary.json`. Neither WU-PREVIEW nor J1 is a done candidate from this run.

## Safety and evidence

One new TEST dataset was registered. No original or existing dataset was deleted. `raw/netcdf.har` was sanitized: known password and bearer-secret occurrence counts are zero and signed query values were replaced with `[REDACTED]`.

Screenshots:

- `dev-package/reports/stage12-preview-acceptance/screens/netcdf-registered.png`
- `dev-package/reports/stage12-preview-acceptance/screens/grib-surface-rendered.png`
- `dev-package/reports/stage12-preview-acceptance/screens/map-state-has-map.png`

The temporary no-preview route was classified as expected behavior because `보기만 할게요` was clicked before a render id existed. It is not a product failure.

## Post-deployment continuation (`f8ac7ee`)

The lane browser doctor passed 12/0/0. A real 4,282,486-byte HDF4 file exposed six variables, rendered `Fpar_500m`, registered as `TEST Stage12 Preview HDF4 20260911`, and survived detail reload as dataset `01M27JPHB9T832QXQNCSBNC7EF`. Evidence: `dev-package/reports/stage12-preview-acceptance/screens/hdf4-registered-reload-f8ac7ee.png`.

Additional `f8ac7ee` evidence completed GeoTIFF (`01M27JS8RY9GJQWF0E7C2GM4AY`), NumPy (`01M27JV56A70BABDMQQDZYGDCT`), and general HDF5 (`01M27JXV7C2QASRJPJ5VZCS5V9`) actual upload/render/TEST registration/reload journeys. A real GRIB1 fixture exposed four message/time/layer candidates and rendered message 2; the registered GRIB2 dataset supplied the complementary selection/render/reload evidence. The registered Binary dataset reloaded and rendered its `.bin.gz` body with its companion grid present. WU-PREVIEW is therefore a done candidate; J1 remains incomplete.

The remaining format gaps were closed: GRIB1 and GRIB2 each used an independent real four-message fixture, selected message 2, rendered, registered a TEST dataset, and reloaded (`01M27K5C02NJPSPZZKSXMY75Z6`, `01M27K6SQQPQZJM81P3MM1JF1D`). Binary used a real body plus an explicitly uploaded NetCDF grid, rendered after the user confirmation `맞습니다`, registered, and reloaded as `01M27K98TYS08G8VF8GYKEEXM7`. The earlier NetCDF dataset was reopened on `f8ac7ee`; reload preserved `LST` and the preview. WU-PREVIEW is now a done candidate.

The latest gate evidence could not be created because lifecycle archival attempts an atomic move from the mandated `/tmp` worktree to the `/mnt` Git metadata and returns EXDEV. The parent is handling this lifecycle helper issue. The prior successful work-item-consistency result is retained as prior evidence and is not represented as current.

## J1 continuation

The professor set the new Binary TEST dataset as the lab default grid. A later body-only upload displayed that dataset as the default candidate with expected bounds `118.84577941894531, 30.107118606567383, 133.5606689453125, 43.57255935668945`. Semantic keyboard activation issued `grid-reuse` 201, produced the `맞습니다` confirmation, and acceptance completed. The pointer-oriented CLI `click` had earlier reported success without dispatching any request; that tool result and its no-grid preview were excluded from product evidence.

An incompatible NetCDF grid was also tried against a Binary body. The server rejected it because it could not distinguish the two axes when both stayed within ±90. Palette `다색 · 무지개` and class count 9 were both selected and rendered.

J1 stands at 7 success, 0 partial, and 2 readiness failures. Other-lab isolation still needs an actual other-lab dataset ID from a read-only source. True folder drag/drop is not executable with agent-browser 0.27's file-path upload, and the live input has `webkitdirectory=false`; multi-file selection was not mislabeled as a folder drop.

## Supplemental BF-7

Semantic keyboard activation of the deployed Screenshot button completed `POST /api/v1/preview-screenshots` with 200 and wrote an actual 5,848-byte PNG to the browser download directory. The preserved artifact is `dev-package/reports/stage12-preview-acceptance/downloads/binary-preview-01M27G421ZYVBCTJV1FMH3P59Z.png` (1024×911 RGBA; SHA-256 `cfc0a2494269a48553ca934d52bc6c2c873e99a6566d22e75395dd7c728566f3`).

## Supplemental BF-11, BF-13, F-3

The deployed Projects page computed the five BF-11 colors as `#f4f7fb`, `#e8ecf2`, `#a85400`, `#efffef`, and `#565c63`. Its live CSSOM contained 78 custom properties and 18 duplicate names with zero conflicting values, which supports BF-13 while remaining distinct from its repository test oracle. File management expanded with semantic keyboard input, but an API audit of every visible dataset found no stored file path containing `/`; no genuine nested tree expander was available for the remaining F-3 UI journey.

## Folder persistence completion

A first synthetic `DataTransfer` fallback demonstrated that a browser-only `webkitRelativePath` property is not enough to represent an OS folder: the fallback treats those as two flat files. That TEST dataset is `01M27MJ7SV1KS71CT4TEDCQV15`; it was retained and not mislabeled as folder evidence.

A second synthetic browser drop supplied a real `FileSystemEntry` directory tree to the deployed recursive drop handler. Its two real 286,683-byte NetCDF files uploaded and `POST /datasets` returned 201 for `01M27MPFKZG68WB7MVD7N7B3DZ`. After reload, the files API returned `TEST-stage12-tree/north/part-a.nc` and `TEST-stage12-tree/south/part-b.nc`. Semantic focus plus Enter expanded File management and displayed both nested folders. Evidence: `screens/folder-tree-persist-reload-f8ac7ee.png`. This is honest synthetic browser directory-entry evidence; an OS file-manager drag was not performed.

J1 is now 8 success, 0 partial, 1 readiness failure, 0 product failure. The remaining row is a genuine other-lab boundary because lab B currently has no dataset. A minimal app-layer TEST B fixture plan is recorded in `summary.json`; it remains unexecuted pending parent review.

## Corrected J1 acceptance boundary

The earlier 8/9 claim was too broad. The axis-ambiguous NetCDF rejection does not satisfy J-3's valid, identifiable mismatch warning that remains nonblocking and shows pair-derived distance. That row is partial until a valid deployed pair is exercised. J1 is currently 7 success, 1 partial, and 1 readiness pending the authorized lab-B TEST fixture.

J-9 now has timing evidence from one actual S3 transfer: a 286,683-byte first NetCDF completed and `early-preview` returned 201 before the 28,668,300-byte second multipart file completed and before final transfer 201. The UI showed the first-file notice at performance time 624334.0 ms, the full-file recheck at 627108.8 ms, and the final convergence at 632786.3 ms. At terminal state the convergence notice occurred exactly once. Evidence: `dev-package/reports/stage12-preview-acceptance-2/j9-terminal-f8ac7ee.png`.

## 2026-09-11 headed 보강과 TEST B 복구

- BF7 fresh headed: 실제 Binary dataset `01M27K98TYS08G8VF8GYKEEXM7`에서 rainbow/7을 선택하고 focus+Enter로 screenshot을 실행했다. POST `/api/v1/preview-screenshots` 200 뒤 Chrome History에 GUID `8957cc08-d8ed-44d6-b66b-a7f5b488dd9e`, 64,138/64,138 bytes, state 1, interrupt 0인 새 행이 생겼다. 디스크 PNG `01M27R8N30279WVFSWCK6DX4G2`는 779x1024, SHA-256 `76597d49...`다.
- BF11 headed: 실제 프로젝트/데이터셋 UI에서 gray-100, surface-alt, text-muted, warning-600, success-50의 다섯 사용처를 computed style로 확인했다. 검증용 `TEST Stage12 Palette Usage 20260911` 프로젝트 한 건만 새로 만들었고 기존 자료 수정은 0이다.
- TEST B 사전 조회는 경계 없는 app role에서 0이었으나, read-only transaction에 `app.current_lab=B`를 설정하자 account/role/switch가 정확히 1/1/4였다. 미지속 추정은 철회했다.
- 4-key credential 후보는 기존 3객체 불변, uid10001 parse, atomic replace, pinned core-only recreate까지 성공했다. 그러나 runtime password를 B 브라우저가 소비하기 전에 제거해 B login을 시도할 수 없었다. 추측 없이 즉시 중지했고 B 업로드/S3 write는 0이다.
- 실패 4-key 자격은 private snapshot으로 보존하고 원래 3-key snapshot SHA `31cb38d7...`을 atomic restore했다. core-only pinned recreate 후 core StartedAt은 `2026-09-11T08:00:36.986500799Z`; viz/pipeline은 각각 최초 `2026-09-11T06:28:25.733838727Z`/`2026-09-11T06:28:25.805722357Z` 그대로다.
- revised supervised runner는 `testb-supervised-resume.py`이며 아직 실행하지 않았다. 부모와 독립 검토가 exact hash를 승인하기 전 재개하지 않는다.

## TEST B 및 J1 최종 수용

- 승인된 supervised runner SHA `d580cec...`로 4-key credential을 설치했다. 기존 3객체는 불변이고, B login 201, `/me` 200, headed session 전달이 성공했다. runtime 평문 입력과 remote staging은 제거됐다. 후속 doctor는 15/0/0, A 기존 session `/me`는 200이었다.
- 첫 상대경로 file-input은 `d5_upload_transfer 01M27RPPZK79KQXFCXBXQJNBQR`에 byte 0 대기행만 만들고 renderer가 응답하지 않았다. 새 target을 같은 headed browser context에 열어 session token을 보존하고 hung target만 닫아 복구했다. 이후 절대경로 입력으로 정상 제품 여정을 진행했다. 이 미완료 TEST transfer는 삭제하지 않았다.
- B dataset `01M27S31B82M6BG21HFK368R42`를 Binary body + grid, render, 맞습니다, 등록, reload로 생성했다. B body-only upload `01M27S45BC9KQA43XYWBGTB9AK`에서 후보가 실제 노출됐고 grid-reuse는 201이었다.
- A body-only upload `01M27S60JHGCRHN3RFZ60WGX01` 후보에는 A dataset만 보였고 B dataset은 없었다. B source ID를 직접 보낸 grid-reuse는 404 `NOT_FOUND`였다. B detail/files는 200/200, A는 404/404였다.
- valid mismatch upload `01M27SBF15C29HP682KE4QZ3RF`는 같은 2881x2305 shape의 유효 NetCDF에서 bounds가 1도 이동했다. API는 `hashDiffers=true`, `distanceMeters=146707`, `blocksRegistration=false`; 실제 UI는 거리 146,707m와 비차단 문구 및 두 예상영역을 표시했고 `맞습니다` 뒤 다음 단계가 활성화됐다.
- 따라서 J1은 9 성공 / 0 partial / 0 readiness failure 후보이며 WU-PREVIEW 7/7과 함께 done 후보이다.
