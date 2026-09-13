# dev 최소 구성 데이터 투입 시나리오 (WU-R3 · 원장 `DR-3`)

- 성격 = **사람이 한 줄씩 따라 읽는 체크리스트.** 브라우저 자동화 도구는 이 회차 범위 밖이다(라운드 결정 14).
- 근거 정본 = `dev-package/prd/rounds/R-DEV-RESET.md §5 WU-R3` · `dev-package/intent/2026-09-13-dev-reset-reference-scenario.md` · 등록표 `dev-package/reports/reference-data/2026-09-13-inventory-v2.md §5`＋`§5-6`.
- 상태 = **미승인 초안.** Ted 의 명시 승인 전에는 실행 근거가 아니다.

## 0. 머리말

- 목적 = 초기화 직후의 dev 에 프로젝트 4 · 데이터셋 28 · 계보 간선 18 을 **화면 조작만으로** 세운다.
- 시작 상태(이 넷이 모두 참이어야 1절로 간다) —
  1. WU-R2 초기화 도구 실행 직후다(`services/core-api/ops/reset_dev_environment.py` · 비가역 · Ted GO 소진).
  2. 마이그레이션이 재적용됐다(`migrate-platform`·`migrate-ai`).
  3. `db-bootstrap.sh app-grants` ＋ `account-admin` 이 끝났다.
  4. `deploy_doctor` 15/15 가 **한 번의 실행**으로 나왔다.
- 원천 = 외부 드라이브 `03 Reference-Data`(**읽기 전용 · 무수정**). 이 문서의 파일 경로는 전부 그 드라이브 안 상대경로다.
- 총량 ≈ **6.1 GB** = 데이터 3,641,736,593 B ＋ 격자 부착 2,489,512,224 B(재목록 v2 §5-5). 16 MiB 이상 파일은 멀티파트로 갈려 올라간다.
- 예상 소요 = `[미확인 — 첫 실행에서 측정]`. 업로드는 화면에서 1건씩이라 파일 수·바이트에 비례한다.
- 되돌리는 수단 = WU-R2 도구뿐이다. 오입력은 그대로 남는다(9절).

## 1. 화면 밖 선행 4건 (SQL · 결정 4 의 유일한 예외)

- 전면 초기화 뒤 연구실 0 · 계정 0 · 자격 0 이라 화면보다 먼저 세운다. **예외는 이 넷뿐이다.**
- 실행 위치 = EC2 호스트. 명령 형태의 선례 = `dev-package/reports/r-dev-reset/dev-access-recon.md §3`(컨테이너 안 실행 · URL 은 `/etc/colab/*.url` **파일 경로**로만 마운트 · argv·로그에 접속 문자열을 싣지 않는다).
- **한 단계가 비영 종료하면 그 자리에서 멈춘다.** 다음 명령을 내지 않는다.
- `[미확인 · 실행 시 확인]` — core-api 이미지 안의 `psql` 가용 여부. 부재 시 postgres 클라이언트 이미지를 같은 마운트 형태로 쓴다.

### ① 연구실 행 — `infra/staging/provision-lab.sql`

- 형태(선례 축자 구조) —
  ```
  docker run --rm --network host --user 0 \
    -v /etc/colab/platform-owner-db.url:/s/owner.url:ro \
    -v /opt/colab-repo/infra/staging/provision-lab.sql:/s/lab.sql:ro \
    <psql 이미지> psql -v ON_ERROR_STOP=1 -f /s/lab.sql
  ```
- 심는 값(파일 축자) = `d1_lab` `00000000000000000000HYMETS` 「고려대학교 수문학연구실」 ＋ `d1_lab_profile`(`고려대학교` · `전창현` · `수문학` · `열림`) ＋ 교수 계정 ＋ `d2_member_role`.
- 파일 이름이 `staging` 이지만 내용은 환경 무관이다. 전 문장 `ON CONFLICT DO NOTHING` — 재실행해도 행이 늘지 않는다.
- ⭑ **소유자 롤(`NOBYPASSRLS`)로 돌아간다** — 파일이 `BEGIN;` 직후 `SET LOCAL app.current_lab` 을 스스로 건다. 종전 판은 `d1_lab_profile` 에서 축자 `new row violates row-level security policy` 로 멈췄고, staging 에서 통한 것은 실행기가 psql 을 `postgres` 슈퍼유저로 불렀기 때문이다(dev·RDS 에는 그 롤이 없다). 증명 = `dev-package/sessions/DR-1b-provision-lab-proof.md`.
- 기대 결과 = `d1_lab` 1행 · `d1_lab_profile` 1행. 파일 끝의 계수표가 5행(`d1_account` 1 · `d1_lab` 1 · `d1_lab_profile` 1 · `d2_member_role` 1 · `d2_permission_switch` 0)을 찍는다.
- 실패 시 멈춤 = 오류 출력을 그대로 기록하고 ② 로 넘어가지 않는다.

### ② 첫 계정 — `services/core-api/ops/provision-account.sql`

- 변수 5개를 준다(파일 머리말 축자) — `-v account_id -v lab_id -v name -v email -v role`.
- `lab_id` = `00000000000000000000HYMETS`. `role` = `연구원` 또는 `교수`(정본 역할은 두 층뿐 · 관리자 역할은 없다).
- 연구실이 없으면 스크립트가 멈춘다 — ① 이 먼저다.
- 기대 결과 = `d1_account` 1행 ＋ `d2_member_role` 1행.
- 실패 시 멈춤.

### ③ 첫 로그인 자격 — 절차 축자 (선례 실측본)

- 근거 = `dev-package/reports/r-login-backoffice/task1-deploy/operator.md` 「## 3. 계정 생성 — 제품과 같은 경로」(＋ `§6` 비밀 취급 · `§7` 남은 것 · `§8` 재설정 1회). 아래는 그 절의 축자 이관이다.
- **왜 화면·API 가 아닌가** — 축자: 「`POST /admin/accounts` 를 쓸 수 없다(운영자 0명 → 자기 자신을 만들지 못한다). ops SQL 중 `login_credential` 을 만드는 것도 없다 — `provision-account.sql` 은 `d1_account`·`d2_member_role`·스위치까지이고, `set-password.py` 는 **DB 가 아니라 자격 파일**에 심는다.」
- **무엇을 하는가** — 축자: 「그래서 `accounts.py::create_account` 의 트랜잭션을 **그대로** core-api 컨테이너 안에서 실행했다. 같은 모듈을 import 했으므로 해시·정규화·잠금·INSERT 가 제품과 동일하다.」
- **동일성 조건 6 (축자)** —
  > - 해시 = `colab_core.kernel.password.hash_password` (`scrypt` · `n=16384 r=8 p=1`)
  > - 로그인 이름 정규화 = `colab_core.kernel.db_credentials.normalize_login_name`
  > - ID = `colab_core.kernel.ids.Ulid.generate()`
  > - 같은 `pg_advisory_xact_lock(1131379081)` · 같은 이메일 중복 검사 2종 · 한 트랜잭션
  > - `must_change_password`·`session_version` 은 **INSERT 에서 생략** — 제품과 같이 DB 기본값(`true` · `1`)을 받는다
  > - 접속 = 컨테이너에 마운트된 `/etc/colab/account-admin-database.url`(`colab_account_admin` 롤)
  > - 비밀번호는 **표준입력 한 줄**로만 넘겼다. argv·파일·로그에 적지 않았다.
- **실행 자리** = dev core-api 컨테이너(`§8` 실측 이름 `colab_v2_dev_core_api`) 안. 임시 실행 스크립트는 **레포에 남기지 않는다** — 축자: 「임시 실행 스크립트는 레포에 남기지 않았다(커밋 0 · 작업 종료 시 삭제).」
- **비밀 취급 4 (축자)** —
  > - 초기 비밀번호는 0600 전달 파일에서 셸 변수로만 읽고 표준입력으로 넘겼다. `cat`·`echo` 로 화면에 내지 않았고 레포·서버 어느 파일에도 쓰지 않았다.
  > - 확인 뒤 `shred -u` 했다. 사후 `ls` = `No such file or directory`.
  > - 확인용으로 발급된 세션 1건이 남는다 — 회수 토큰을 보관하지 않았으므로 손으로 끊지 않았다. **Ted 의 첫 비밀번호 변경이 `session_version` 을 +1 하면 그 시점에 무효가 된다**(`db_credentials.change_password`).
- **초기 비밀번호는 10자 이상으로 정한다.** 축자: 「전달 파일은 **9자**이고 제품 하한은 **10자**다(`accounts.py` `initialPassword: Field(min_length=10)` · `frontend/src/auth/passwordRules.ts` `length >= 10`). DB·로그인 경로에는 길이 하한이 없어 심기·로그인 모두 성립했고 실측으로 확인했다. 다만 **같은 비밀번호를 `POST /admin/accounts` 로는 발급할 수 없다.**」 ⟹ 9자로 심으면 로그인은 되지만 첫 변경 화면이 막는다.
- **집행 뒤 확인할 열 (선례 실측표의 열 그대로)** — `account_id` · `login_name` · `lab_id`/`role` · `kdf`/`n`/`r`/`p` = `scrypt`/`16384`/`8`/`1` · `must_change_password` = `true` · `session_version` = `1`.
- **알려진 잡음 — 판정 red 가 아니다.** 축자: 「집행 스크립트의 **사후 조회**가 `permission denied for table d2_member_role` 로 죽었다. INSERT 트랜잭션은 이미 커밋된 뒤였고, 원인은 `ops/account-admin-role.sql` 이 `d2_member_role` 에 **`INSERT` 만 주고 `SELECT` 를 주지 않는 것**이다.」 ⟹ 역할 행 확인은 소유자 롤로 대신한다.
- **상태 코드 확인** = `POST /api/v1/sessions` **201** · `GET /api/v1/me` **200** `mustChangePassword=true`. ⚠ 401 이 5건 쌓이면 **429**(시도 제한 창 900초 · 한도 5)가 나므로 창이 지난 뒤 다시 낸다(`§8` 실측).
- 기대 결과 = `account_admin.login_credential` 1행 · `must_change_password = true` · `session_version = 1`.
- 실패 시 멈춤.

### ④ 서비스 운영자 등록 — `services/core-api/ops/provision-service-operator.sql`

- 변수 = `-v account_id`(② 에서 쓴 값).
- ⚠ **FORCE RLS 아래라 `app.current_lab` 을 먼저 걸지 않으면 `INSERT 0 0` 뒤 가드가 예외를 낸다**(operator.md §7). 실행 세션에서 경계를 먼저 설정한다.
- 기대 결과 = `account_admin.service_operator` 1행.
- 실패 시 멈춤.

## 2. 로그인

- 주소 = `https://d31zgpff2091oh.cloudfront.net` (`dev-package/reports/r-dev-reset/dev-access-recon.md §4` · 출처 `docs/DEPLOY.md`).
- 화면 = 제목 「로그인」 · 안내 「운영자에게 받은 이메일과 초기 비밀번호를 넣어 주세요.」
- 입력 = 「이메일」 칸에 ② 의 이메일 · 「비밀번호」 칸에 ③ 의 초기 비밀번호 → 「들어가기」.
- 첫 로그인은 비밀번호 변경을 강제한다 — 제목 「비밀번호 변경」 · 안내 「처음 로그인하셨습니다. 사용할 새 비밀번호로 바꿔 주세요.」
  - 칸 = 「새 비밀번호」 · 「새 비밀번호 확인」. 규칙 「10~512자로 입력하세요. 영문·숫자·특수문자 조합은 필수가 아니며, 초기 비밀번호와 달라야 해요.」
- 기대 결과 = 변경 뒤 `/lab` 로 들어간다(`/` 는 `/lab` 으로 보낸다).
- 실패 시 멈춤 = 「계정 또는 비밀번호가 맞지 않아요.」 가 뜨면 ③ 의 자격 행부터 다시 본다.

## 3. 계정 화면 (선택 · 기본값 = 추가 없음)

- 경로 = `/account-admin` · 제목 「계정 관리」 · 「서비스 운영자만 사용할 수 있어요.」
- 추가 연구원이 필요할 때만 「계정 추가」 → 「이름」·「이메일」·「연구실」·「역할」·「초기 비밀번호」 입력.
- **기본값 = 추가하지 않는다.** 이 시나리오는 계정 1개로 끝까지 간다.

## 4. 프로젝트 생성 4건

- 경로 = `/projects` → 「새 프로젝트」 버튼 → 모달 「새 프로젝트」.
- 칸 = 「이름」 · 「유형」(「국가과제」/「논문」 · **나중에 바꿀 수 없다**) · 「설명」 · 「기간」 · 「연결 주소」 → 「만들기」.
- 유형은 네 건 모두 `[미확인 · 실행 시 화면에서 확인]` — 정본에 프로젝트 유형 지정이 없다. 하나로 통일하고 실행 기록에 적는다.

| # | 이름 | 설명(입력 문안) |
|---|---|---|
| 1 | `precipitation` | HSR 레이더 반사도와 rn15 지상강수를 좌표변환·crop 한 뒤 U-Net 예측까지 잇는 강수 3단 자료. Lv.0 2갈래 → Lv.1 2갈래 → Lv.2 예측 1건. |
| 2 | `vegetation` | GK-2A 식생자료(Lv.0)에서 월평균 NDVI(Lv.1)를 만들고, 수치표고모형·경사향·토지피복을 추가 입력으로 써 100 m 일 단위 공간상세화 예측(Lv.2)까지 잇는다. |
| 3 | `drought` | SPI-4weeks 와 SPEI-4weeks 두 가뭄지수의 L1 보정 결과. 두 자료는 서로 독립이며 파생 관계가 없다. |
| 4 | `포멧테스트` | grib · nc · bin · tif · hdf4 다섯 포맷의 원자료와 변환 결과를 한 쌍씩 담아 포맷별 미리보기 렌더를 확인하는 프로젝트. |

- 기대 결과 = `/projects` 목록에 4건.

## 5. 데이터셋 투입 28건

- 경로 = 「업로드」 진입 → 업로드 모달 「이 파일을 연구실에 등록할까요?」 → 「① 분류」 → 「② 메타데이터 입력」 → 「③ 연결」 → 「데이터셋 만들기 →」.
- 파일 고르기 = 「파일을 끌어다 놓으세요」 / 「파일 고르기」. 다중 = 「여러 개를 한 번에, 폴더째 끌어다 놓아도 돼요」.
- 기준 격자 = 「기준 격자 파일」 블록 → 「격자 파일 올리기」. **데이터셋당 2건이 상한**이라 위도·경도 `.npy` 쌍 하나만 붙인다. 격자가 없는 행은 「건너뛰기 — 나중에 올릴게요」.
- 이름·설명은 「데이터셋 이름」·「설명」 칸에 적는다. 프로젝트는 「연관 프로젝트·논문」에서 고른다.
- **순서를 지킨다** — 부모가 먼저다(Lv.0 → Lv.1 → Lv.2 · 원자료 → 결과). 아래 번호 순서 그대로 투입한다.
- 확인 항목 2개 = ⓐ 업로드 완료 표시(「분석 완료 · 확장자와 용량을 읽었어요」 → 데이터셋 생성) ⓑ 상세 화면 미리보기 렌더 여부.

| 순번 | 프로젝트 | 데이터셋 이름 | 설명(1줄) | 파일 glob ＋ 건수 | 기준 격자 쌍 | 부모 | 포맷 | 확인 |
|---|---|---|---|---|---|---|---|---|
| 1 | precipitation | HSR 레이더 반사도 원자료 | 기상청 HSR 합성 반사도 원본 | `01.level-data/01.precipitation/01.precipitation/Lv.0/01.HSR/RDR_CMP_HSR_PUB_*.bin.gz` · **10건**(업로드 모달에서 다중 선택 10건) | `#metadata/LAT_HSR.npy`·`LON_HSR.npy` | — | bin(gzip) | ⓐⓑ |
| 2 | precipitation | rn15 15분 누적강수 | 지상 격자 15분 누적강수 원본 | `…/Lv.0/02.rn15/sfc_grid_rn_15m_*.nc` · **10건**(다중 선택 10건) | `#metadata/LAT_RN15.npy`·`LON_RN15.npy` | — | NetCDF4 | ⓐⓑ |
| 3 | precipitation | hsr_sample | WGS84 변환·crop 한 HSR 전처리 자료 | `…/Lv.1/hsr_sample.npy` · **1건** | `#metadata/LAT_crop.npy`·`LON_crop.npy` | 1 | npy | ⓐⓑ |
| 4 | precipitation | rn15_sample | WGS84 변환·crop 한 rn15 전처리 자료 | `…/Lv.1/rn15_sample.npy` · **1건** | `#metadata/LAT_crop.npy`·`LON_crop.npy` | 2 | npy | ⓐⓑ |
| 5 | precipitation | pred_sample | U-Net 기반 강수 예측 결과 | `…/Lv.2/pred_sample.npy` · **1건** | `#metadata/LAT_crop.npy`·`LON_crop.npy` | 3 ＋ 4 | npy | ⓐⓑ |
| 6 | vegetation | GK-2A 일 단위 식생자료 | GK-2A AMI 일 단위 식생 원본 | `01.level-data/02.vegetation/02.vegetation/Lv.0/gk2a_ami_le2_vgt_ko_*.nc` · **31건**(다중 선택 31건) | `#metadata/LAT.npy`·`LON.npy` | — | NetCDF4 | ⓐⓑ |
| 7 | vegetation | GK2A_NDVI_mean_202305 | GK-2A 기반 2023-05 월평균 NDVI | `…/Lv.1/GK2A_NDVI_mean_202305.tif` · **1건** | `#metadata/LAT_crop.npy`·`LON_crop.npy` | 6 | GeoTIFF | ⓐⓑ |
| 8 | vegetation | HLS_S30_NDVI_mean_202305 | 검증용 HLS S30 2023-05 월평균 NDVI | `…/Lv.1_(Model_Input_Data)/HLS_S30_NDVI_mean_202305.tif` · **1건** | `[미확인]` — 부착 여부 실행 시 판단 | — | GeoTIFF | ⓐⓑ |
| 9 | vegetation | DEM | 100 m 수치표고모형 입력 | `…/Lv.1_(Model_Input_Data)/DEM.tif` · **1건** | `[미확인]` | — | GeoTIFF | ⓐⓑ |
| 10 | vegetation | Aspect | DEM 에서 산출한 100 m 경사향 | `…/Lv.1_(Model_Input_Data)/Aspect.tif` · **1건** | `[미확인]` | 9 | GeoTIFF | ⓐⓑ |
| 11 | vegetation | LULC_2023 | 2023년 연 단위 토지피복지도 | `…/Lv.1_(Model_Input_Data)/LULC_2023.tif` · **1건** | `[미확인]` | — | GeoTIFF | ⓐⓑ |
| 12 | vegetation | Prediction (공간상세화) | U-Net 기반 100 m 일 단위 NDVI 예측 | `…/Lv.2/Prediction_2023*.npy` · **31건**(다중 선택 31건) | `#metadata/LAT_crop.npy`·`LON_crop.npy` | 7 ＋ 8 ＋ 9 ＋ 10 ＋ 11 | npy | ⓐⓑ |
| 13 | drought | SPI-4weeks | 4주 SPI 유의구간 벡터 (L1 Calibrated) | `01.level-data/03.drought-…/03.drought/Lv.1/SPI_4weeks_sig_wide.gpkg` · **1건** | 없음(벡터) | — | GeoPackage | ⓐⓑ |
| 14 | drought | SPEI-4weeks | 4주 SPEI 유의구간 벡터 (L1 Calibrated) | `…/Lv.1/SPEI_4weeks_sig_wide.gpkg` · **1건** | 없음(벡터) | — | GeoPackage | ⓐⓑ |
| 15 | 포멧테스트 | surface (ERA5 GRIB 원자료) | ERA5 지표 변수 GRIB 원본 | `02.File-format/file_format_1_grib/00.Data/surface.grib` · **1건** | `…/04.Lat_Lon_info/lat2d.npy`·`lon2d.npy` | — | GRIB1 | ⓐⓑ |
| 16 | 포멧테스트 | ERA5 변환 결과 | GRIB 에서 변환한 slhf·ssr·str 시각별 배열 | `file_format_1_grib/02.Results/{slhf,ssr,str}/ERA5_*_*.npy` · **72건**(다중 선택 72건) | `…/04.Lat_Lon_info/lat2d.npy`·`lon2d.npy` | 15 | npy | ⓐⓑ |
| 17 | 포멧테스트 | GK-2A LST 원자료 | GK-2A 지표온도 10분 간격 원본 | `file_format_2_nc/00.Data/gk2a_ami_le2_lst_ko_*.nc` · **143건**(다중 선택 143건) | `…/04.Lat_Lon_info/lat2d.npy`·`lon2d.npy` | — | NetCDF4 | ⓐⓑ |
| 18 | 포멧테스트 | GK-2A LST 변환 결과 | nc 에서 변환한 지표온도 배열 | `file_format_2_nc/02.Results/gk2a_ami_le2_lst_ko_*.npy` · **143건**(다중 선택 143건) | 동일 쌍 | 17 | npy | ⓐⓑ |
| 19 | 포멧테스트 | HSR 레이더합성 원자료 | HSR 합성 바이너리 원본 | `file_format_3_bin/00.Data/RDR_CMP_HSR_PUB_*.bin.gz` · **12건**(다중 선택 12건) | `…/04.Lat_Lon_info/Lat_HSR.npy`·`Lon_HSR.npy` | — | bin(gzip) | ⓐⓑ |
| 20 | 포멧테스트 | HSR 레이더합성 변환 결과 | bin 에서 변환한 합성 반사도 배열 | `file_format_3_bin/02.Results/RDR_CMP_HSR_PUB_*.npy` · **12건**(다중 선택 12건) | 동일 쌍 | 19 | npy | ⓐⓑ |
| 21 | 포멧테스트 | HLS S30 T51SYB 원자료 | HLS S30 T51SYB 타일 밴드 3종 | `file_format_4_tif/00.Data/HLS.S30.T51SYB.*.tif` · **3건**(다중 선택 3건) | `…T51SYB…_lat2d.npy`·`…T51SYB…_lon2d.npy` | — | GeoTIFF | ⓐⓑ |
| 22 | 포멧테스트 | HLS S30 T52SCE 원자료 | HLS S30 T52SCE 타일 밴드 3종 | `file_format_4_tif/00.Data/HLS.S30.T52SCE.*.tif` · **3건**(다중 선택 3건) | `…T52SCE…_lat2d.npy`·`…T52SCE…_lon2d.npy` | — | GeoTIFF | ⓐⓑ |
| 23 | 포멧테스트 | HLS S30 T51SYB 변환 결과 | T51SYB 타일 밴드 3종의 변환 배열 | `file_format_4_tif/02.Results/HLS.S30.T51SYB.*.npy` · **3건**(다중 선택 3건) | T51SYB 쌍 | 21 | npy | ⓐⓑ |
| 24 | 포멧테스트 | HLS S30 T52SCE 변환 결과 | T52SCE 타일 밴드 3종의 변환 배열 | `file_format_4_tif/02.Results/HLS.S30.T52SCE.*.npy` · **3건**(다중 선택 3건) | T52SCE 쌍 | 22 | npy | ⓐⓑ |
| 25 | 포멧테스트 | hdf4 MOD15A2H h27v05 원자료 | 폴더명 hdf5 · 실물 HDF4. h27v05 타일 4일치 | `file_format_5_HDF5/00.Data/MOD15A2H.*.h27v05.*.hdf` · **4건**(다중 선택 4건) | `…/04.Lat_Lon_info/lat2d_h27v05.npy`·`lon2d_h27v05.npy` | — | HDF4 | ⓐⓑ |
| 26 | 포멧테스트 | hdf4 MOD15A2H h28v05 원자료 | 폴더명 hdf5 · 실물 HDF4. h28v05 타일 4일치 | `file_format_5_HDF5/00.Data/MOD15A2H.*.h28v05.*.hdf` · **4건**(다중 선택 4건) | `lat2d_h28v05.npy`·`lon2d_h28v05.npy` | — | HDF4 | ⓐⓑ |
| 27 | 포멧테스트 | hdf4 MOD15A2H h27v05 변환 결과 | 폴더명 hdf5 · 실물 HDF4. h27v05 변수 6종 × 4일 | `file_format_5_HDF5/02.Results/MOD15A2H.*.h27v05.*.npy` · **24건**(다중 선택 24건) | h27v05 쌍 | 25 | npy | ⓐⓑ |
| 28 | 포멧테스트 | hdf4 MOD15A2H h28v05 변환 결과 | 폴더명 hdf5 · 실물 HDF4. h28v05 변수 6종 × 4일 | `file_format_5_HDF5/02.Results/MOD15A2H.*.h28v05.*.npy` · **24건**(다중 선택 24건) | h28v05 쌍 | 26 | npy | ⓐⓑ |

- 적재 제외 = `desktop.ini` 74 · `01.Code` 13 · `03.Figure` png·jpg · `*.pdf` · `03_KWRA_conference-…` 전체.
- 1회 업로드 상한 = 파일 500건 · 파일명 255자. 위 최대 행(143건)은 상한 안이다.

## 6. 계보 설정 18간선

- 자리 = 업로드 모달 「③ 연결」 단계(`LineageStep`). 「가공 전 데이터」 블록에서 「앞 데이터 직접 추가」로 부모를 고르고 「확인」을 누른다.
- **사람이 직접 고르는 것이 기본이다.** 화면 문구 축자 —
  > 앞 데이터는 **직접 이어 붙이는 것이 기본**이에요. 필요하면 AI 제안을 받아 볼 수 있어요.
- AI 제안은 「AI 제안 받기」 버튼을 눌렀을 때만 온다. **제안은 참고일 뿐이고 그대로 받아들이지 않는다** — 아래 표의 부모와 다르면 「거절」하고 직접 고른다. 확신도는 `확실|애매|모름` 이고 퍼센트가 없다.
- 「부모 역할」은 화면에서 묻지 않고 서버 기본값 `주입력` 이 실린다. 「가공 방식 (선택)」은 비워도 된다.

| 간선 | 자식(순번) | 부모(순번) |
|---|---|---|
| 1 | 3 hsr_sample | 1 HSR 레이더 반사도 원자료 |
| 2 | 4 rn15_sample | 2 rn15 15분 누적강수 |
| 3 | 5 pred_sample | 3 hsr_sample |
| 4 | 5 pred_sample | 4 rn15_sample |
| 5 | 7 GK2A_NDVI_mean_202305 | 6 GK-2A 일 단위 식생자료 |
| 6 | 10 Aspect | 9 DEM |
| 7 | 12 Prediction | 7 GK2A_NDVI_mean_202305 |
| 8 | 12 Prediction | 8 HLS_S30_NDVI_mean_202305 |
| 9 | 12 Prediction | 9 DEM |
| 10 | 12 Prediction | 10 Aspect |
| 11 | 12 Prediction | 11 LULC_2023 |
| 12 | 16 ERA5 변환 결과 | 15 surface |
| 13 | 18 GK-2A LST 변환 결과 | 17 GK-2A LST 원자료 |
| 14 | 20 HSR 레이더합성 변환 결과 | 19 HSR 레이더합성 원자료 |
| 15 | 23 T51SYB 변환 결과 | 21 T51SYB 원자료 |
| 16 | 24 T52SCE 변환 결과 | 22 T52SCE 원자료 |
| 17 | 27 h27v05 변환 결과 | 25 h27v05 원자료 |
| 18 | 28 h28v05 변환 결과 | 26 h28v05 원자료 |

- drought(13·14)는 간선 0이다 — 「가공 전 데이터를 못 찾았어요 — 기록 없이 등록할게요」로 두고 그대로 등록한다.
- 소계 = precipitation 4 · vegetation 7 · drought 0 · 포멧테스트 7 = **18**.

## 7. 확인

1. **데이터셋 계수** — `/datasets` 목록에서 **28건**. 프로젝트별 = 5 · 7 · 2 · 14.
2. **계보 간선** — 자식 데이터셋 상세의 계보에서 6절 표와 1:1 대조. 합 **18**.
3. **미리보기 렌더 5포맷** — 아래 표를 채운다. **그려지지 않으면 이름을 적는다. 조용히 넘기지 않는다.**

| 포맷 | 확인 대상(순번) | 렌더 | 비고 |
|---|---|---|---|
| grib | 15 | ☐ | |
| nc | 17 | ☐ | |
| bin | 19 | ☐ | |
| tif | 21 | ☐ | |
| hdf4 | 25 | ☐ | |

4. **`deploy_doctor` 15/15 를 한 번의 실행으로** — EC2 에서 `sudo bash /opt/colab-repo/infra/ops/probes/deploy-verification.sh`(선례 `dev-package/reports/r-dev-reset/dev-access-recon.md §3` · `--allow-skip` 미사용 · 재시도 0 · 부분 실행 합산 0).
   - 선행 = `/opt/colab-repo` 트리를 배포 sha 로 맞춘다(같은 문서 §1 tar-sync 3줄). 낡으면 ⑥ 이 조용히 틀린다.

## 8. 기록

- 자리 = `dev-package/sessions/DR-3-run-<YYYY-MM-DD>.md`. 양식 —

```
# DR-3 실투입 실행 기록 — <YYYY-MM-DD>

- 실행자 / 시작 시각 / 종료 시각 / 총 소요
- 시작 상태 확인: 초기화 직후 ☐ · 마이그레이션 ☐ · app-grants ☐ · doctor 15/15 ☐
- 선행 4건: ① ☐ ② ☐ ③ ☐ ④ ☐   (실패한 단계와 오류 원문)
- 프로젝트 4건 생성 결과 / 고른 유형
- 데이터셋 28행 결과 — 성공한 순번 목록 · 실패한 순번과 사유(행 단위)
- 계보 18간선 결과 — 선 간선 수 · 실패 간선 번호
- AI 제안을 거절한 건수와 대상
- 미리보기 렌더 표 5행 — 그려지지 않은 포맷 이름
- deploy_doctor 결과(한 번의 실행 · ✓/✗/─ 계수 · 실패 항목 번호)
- 미측정으로 남긴 값 [미확인] 목록
```

## 9. 반복 실행 조건

- 이 시나리오는 **빈 dev 를 전제로 한다.** 데이터가 남은 상태에서 다시 돌리면 계수가 28을 넘고 이름이 충돌한다.
- 다시 돌리려면 **WU-R2 초기화 도구부터 다시 밟는다** — `services/core-api/ops/reset_dev_environment.py` ＋ 부트스트랩 5단계.
- ⛔ 그 실행은 **비가역**이고 `PLAN-SoT §9` 행에 기록된 **Ted 의 명시 GO** 를 요구한다. **승인은 1회 소진이다.**
- 화면에서 데이터셋을 지우는 길은 없다 — 서버가 501 로 응답한다. 오입력은 초기화 전까지 남는다.
