# R-B-1 · DB · 마이그레이션 계층 — WU-B1 · WU-B2 · WU-B4 · WU-B6

> 이 파일 하나로 세션을 시작한다. 라운드 = **R-B** · 계층 = **DB(＋계약·서버·FE 꼬리)** · WU **4건**.
> 마이그레이션 **M-1 · M-2 · M-3 · M-5 · M-4 · M-8** 을 **한 head 에** 담는다(`M-10` 은 이 파일 밖 — `R-B-2-server.md`).
> 의도문 = `dev-package/intent/2026-09-07-r-b.md` (**미승인 초안**). ⚠ 실측 — 이 트리에 해당 파일 **부재**(`dev-package/intent/` = `2026-09-06-r-a2.md`·`README.md`·`TEMPLATE.md`). 승인 전에는 이 파일이 요구 정본이다.

---

## 0. 읽기 규칙 — 이 파일이 유일한 부트스트랩

> ⛔ **아래 4개를 통째로 열지 않는다.** 세션이 느려지는 원인이 이것이다.
> `dev-package/03-HANDOFF.md` · `dev-package/PLAN-SoT.md` · `dev-package/work-items.yaml` · `dev-package/WORK-UNITS.md`

- **허용된 접근은 아래 세 줄뿐이다.**
  1. 결정 번호 최대값 — `bash dev-package/prd/tools/max-decision.sh`
  2. 대장에서 항목 하나 — `grep -n -A14 '^  - id: WU-B1' dev-package/work-items.yaml`
  3. 게이트 이름 확인 — `sed -n '12,30p' gates/run.sh` (`ALL_GATES` 배열)
- `03-HANDOFF.md` · `CLAUDE.md` · `RESTART.md` 는 **머리 부분만** 읽는다. 본문 통독 금지.
- 요구사항 정본은 이 파일과 `dev-package/prd/PRD-260905-적용전기획.md` 다. 이 파일에 옮겨 적힌 문면이 우선이고, 더 필요하면 PRD 사본에서 **해당 `#### PRD-xx` 절만** 읽는다.
- **코드 파일은 고칠 때만 연다.** 현황 정찰·grep 스윕·다수 파일 읽기는 **서브에이전트에 위임**하고 결론만 회수한다.
- 이 파일의 `path:line` 은 **HEAD `ccd9372` 실측값**이다. 코드를 고친 뒤에는 다시 잰다. 못 재면 `[미상]` 이고 지어내지 않는다.

---

## 1. 확정 결정 — 다시 열지 않는다 (PRD §1 · Ted 2026-09-05)

미결 18건이 전부 닫혔다 = 확정 16 ＋ 해소 1(미결-8) ＋ 개발 실측 1(미결-10). **기획자에게 받아야 하는 답은 0건이다.**
아래 16줄이 요구사항이다. 다르게 구현할 사유를 찾으면 **고치지 말고 보고한다.**

- 미결-1 ⓐ — 공개 범위는 **연구실 내부 3값**(`연구실 구성원 전체`/`나만 보기`/`지정한 사람만`), 기본 선택 `연구실 구성원 전체`. 저장은 `열림`·`잠김`·`지정 공개`. RLS 경계를 열지 않고 PRD-37·WU-C5 를 열지 않는다
- 미결-2 ⓐ — 가공 단계를 **사람이 고르고**, 계보 계산값과 어긋나면 **경고만** 낸다(등록을 막지 않는다). `processing_level_user_set` 재신설 ＋ 원장에 `〈194〉` 반전 기재
- 미결-3 ⓐ — 기존 13행의 3축은 **전 행 NULL**, 자동 매핑 없음. 표기 「분류를 아직 안 골랐어요」, `topic` 열은 남긴다
- 미결-4 ⓐ — 관측 간격은 **선택 입력**. 저장은 수치＋단위 두 칸, 표기는 기간 뒤 괄호 (R-A 에서 닫힘)
- 미결-5 ⓐ — 설명 필수화 후 빈 기존 행은 **그대로 두고** 그 행을 수정할 때 채우게 한다 (R-A 에서 닫힘)
- 미결-6 ⓐ — 확정 부모 1건 이상이면 체크박스 **잠금＋사유 한 줄**. 라벨 = `가공 전 데이터를 못 찾았어요 — 기록 없이 등록할게요`
- 미결-7 ⓐ — 가공 단계 **Lv0~Lv3 네 단**(CHECK 4값 · 계약 enum 4값 · 화면 칩 4단)
- 미결-9 ⓑ — 상세는 **한 페이지 스크롤 유지 ＋ sticky 구역 메뉴** (R-A WU-A8 이 최종형)
- 미결-11 ⓐ — 원천 표기(`sourceLabel`)는 **Lv 무관 상시 노출**, `sourceUrl`·`sourceDownloadedOn` 두 칸만 Lv0 게이팅
- 미결-12 ⓐ — 유형별 주의 문구는 **선택기 아래 보조 문구 ＋ 설명란 힌트**(저장 칸 없음 · 표시층 문자열)
- 미결-13 ⓐ — 분류·유형은 **표시만 국문＋영문 병기**(`기상·기후 인자 (Meteorological & Climatic Factors)`), 저장·CHECK·필터·색인은 국문 단일
- 미결-14 ⓐ — 유형↔가공 단계 **제약 없음**(조합 검증을 만들지 않는다)
- 미결-15 ⓐ — 종료 모달은 조건만 고치고 문면 유지 (R-A 에서 닫힘)
- 미결-16 ⓐ — 등록 ③ 의 쓰임 한 줄은 **받지 않는다**(PRD-36 · WU-C4 범위 밖)
- 미결-17 ⓐ — pdf 항목 8 잘린 1행은 원문 요청 중. **회신 대기가 WU-B2 착수를 막지 않는다** — 변수 표 본문은 `T-38`~`T-44` 로 확보돼 있다. ⛔ **추정 전사를 하지 않는다**
- 미결-18 ⓐ — 기간은 시각값 저장 유지, 화면만 구조화 (R-A 에서 닫힘)
- ⭑ **미결-10 = 개발 실측** — WU-A11 판정표가 WU-B11 의 범위다(`R-B-4-verify.md`). 미결-8 = 해소.

---

## 2. 범위 — 이 파일의 WU 4건

### WU-B1 · 분류 3축 스키마·계약 (PRD-01 · 02 · 03) — 계층 DB·계약·서버 · 크기 L · 레인 `p3-axes-schema`

- **의존**: 없음(R-B 의 첫 WU). **이 WU 가 R-B 의 마이그레이션 head 를 만든다.**
- **현재 코드** — `db/platform/schema.sql:363`(`d3_dataset_description` 정의) · `:370`(`topic text CHECK (topic IS NULL OR topic IN ('강우·강수', …))`) · `:332`(`0011` 이 `processing_level_user_set` 을 지운 근거 주석) · `services/core-api/src/colab_core/app/routes/catalog.py:553`(`_TOPICS`)·`:626-627`(값 밖 400) · `frontend/src/components/upload/types.ts:171`(`TOPICS`) · `contracts/schemas/common.json:161-166`(`ProcessingLevel`).
- **요구 문면 축자 (PRD-01)** — 「저장값은 국문 5값뿐이고, 화면은 국문 옆에 영문을 병기한다」 · 「기본 선택값 = `기상·기후 인자`」. 5값 = `수문 인자`·`기상·기후 인자`·`식생·탄소 인자`·`사회·경제 인자`·`환경 인자`.
- **요구 문면 축자 (PRD-02)** — 「저장값은 국문 6값뿐이고, 화면은 국문 옆에 영문을 병기한다」 · 「기본 선택값 = `재분석자료`」 · 「컬럼명은 `type` 을 피한다 — SQL·TS 양쪽에서 예약어·내장 이름과 겹친다.」 6값 = `지상관측자료`·`위성자료`·`재분석자료`·`수치모형자료`·`합성자료`·`관측 기반 산출물`.
- **요구 문면 축자 (PRD-03)** — 「상한은 Lv3 이다」(미결-7 ⓐ) · 「`0007` 이 세운 `processing_level_user_set` 열과 그 CHECK 를 지웠다. 「레벨은 언제나 계보에서 나온다 … 예외 없음」」(`schema.sql:332` 주석 · `〈194〉`).
- **변경 — DB** (`M-1`·`M-2`·`M-3`): `d3_dataset_description` 에 `category text CHECK (category IS NULL OR category IN (…5값…))` · `data_type text CHECK (… 6값 …)` 신설. `d3_dataset` 에 `processing_level_user_set text CHECK (… IN ('Lv0','Lv1','Lv2','Lv3'))` **재신설**. `topic` 열은 **남긴다**.
- **변경 — 계약**: `DatasetCreate`(`contracts/seams/fe-core.yaml:3401`)·`DatasetUpdate`(`:3492`)·`DatasetBasicInfo`(`:3795`) 에 `category`·`dataType`·`processingLevelUserSet` 세 열쇠. ⚠ `common.json:161-166` `ProcessingLevel` 은 **`readOnly: true` 파생값**으로 선언돼 있다 — 사람 값 칸 신설은 **그 원칙의 반전**(`〈194〉`·`〈276〉` 반전)이다. ⛔ **기존 description 문면을 지우지 않고 반전 문장을 덧붙인다.**
- **변경 — 서버**: `catalog.py:553` `_TOPICS` 와 같은 모양으로 `_CATEGORIES`(5값)·`_DATA_TYPES`(6값)·`_PROCESSING_LEVELS`(4값) 검증. 값 집합 밖은 **400**(IntegrityError 500 로 떨어뜨리지 않는다 — `catalog.py:626-627` 선례).
- **기존 데이터 처리**: 세 컬럼 **전 행 NULL**. 자동 매핑 없음(미결-3 ⓐ). `topic` 값은 그대로 남아 대조 근거가 된다. 파생 Lv 는 계속 계산되고 상세는 `자동` 표시를 붙인다. **일괄 backfill 금지.**
- **수용 기준**
  - Given 5값 밖 문자열, When `createDataset`, Then **400** 이고 응답에 `allowed` 5값이 실린다(500 이 아니다).
  - Given 마이그레이션 적용, When `SELECT topic, category FROM d3_dataset_description`, Then 전 13행이 `category IS NULL` 이고 `topic` 값은 그대로다.
  - Given `category` NULL 인 기존 행, When 목록·상세 조회, Then 「분류를 아직 안 골랐어요」가 뜨고 화면이 깨지지 않는다.
  - Given 유형 `관측 기반 산출물` ＋ 가공 단계 `Lv1`, When `createDataset`, Then **성공**한다(조합 제약 없음 — 미결-14 ⓐ).
  - Given 사람 Lv 와 파생 Lv 가 어긋남, When `createDataset`, Then 성공하고 **경고만** 뜬다.
  - Given 마이그레이션 후 기존 13행, When 상세 조회, Then `processingLevel` 이 종전 값이고 `자동` 표시가 붙는다.

### WU-B2 · 변수 행 표 (PRD-16) — 계층 DB·계약·서버·FE · 크기 L · 레인 `p3-variable-rows`

- **의존**: **WU-B1(같은 마이그레이션 head)**.
- **현재 코드** — `d3_dataset_variable` 표는 **아직 없다**(`grep -n 'd3_dataset_variable' db/platform/schema.sql` → 0건). 현재 저장은 `db/platform/schema.sql:414` `variables text[] NOT NULL DEFAULT '{}'` 하나다. 색인 = `:426-432` `search_vector … GENERATED ALWAYS AS (setweight(… coalesce(format,'') || ' ' || d3_search_join(variables), 'B') || setweight(… crs · grid · bundle_file_name …, 'C')) STORED`. 계약 `variables` = `fe-core.yaml:3462`·`:3550`·`:3808`.
- **요구 문면 축자** — 「변수 3개에 단위 1개면 어느 변수 것인지 알 수 없다.」 · 「열 구성은 5열(변수 · 단위 · 값 범위 · 결측률 · 대표)로 확정, 회신 불요.」 · 「기존 표에 컬럼을 더하지 않는다」 · 「행이 0개인 데이터셋은 허용하지 않는다」 · 「ⓐ 채택 — `d3_dataset_variable` 에 트리거를 걸어 `d3_dataset_autometa.variables` 를 행 표의 미러로 유지한다.」
- **변경 — DB** (`M-5`): 새 표 `d3_dataset_variable` — `dataset_id ulid` · `lab_id ulid NOT NULL` · `ordinal integer NOT NULL` · `name text NOT NULL CHECK(length(btrim(name))>0)` · `unit text` · `value_range text` · `missing_rate text` · `is_representative boolean NOT NULL DEFAULT false`. `PRIMARY KEY (dataset_id, ordinal)` · 대표 1개 **부분 UNIQUE 색인** · `lab_id` 에 RLS. ⛔ **D3 소유다** — D2 가 이 표를 FK 하지 않는다(`CLAUDE.md §3-1`).
- **변경 — 계약**: `DatasetVariable` 신설(`name` required · 나머지 nullable · `representative: boolean`). `DatasetCreate`·`DatasetUpdate`·`DatasetBasicInfo` 의 `variables` 를 **문자열 배열 → 객체 배열**(파괴적 변경 — §3-㉰).
- **변경 — 서버**: 등록·수정 시 행 집합을 **통째로 교체**(delete-then-insert). 대표 1개 규칙을 서버가 검사. 등록·수정 경로에서 `autometa.variables` 를 **직접 쓰지 않는다**(트리거만 쓴다).
- **변경 — 프론트**: 표 UI(`+ 변수 추가` · 행 삭제 · 대표 라디오). 열 순서·라벨 = `변수 · 단위 · 값 범위 · 결측률 · 대표`. 상세는 같은 표를 읽기 전용으로 그린다.
- **기존 데이터 처리**: `autometa.variables` 문자열 배열을 마이그레이션이 옮긴다 — `ordinal` = 배열 순서 · `name` = 원소 · `unit`·`value_range`·`missing_rate` = NULL · `is_representative` = **첫 행만 true**. 원본 `variables` 컬럼은 **남긴다**. 빈 배열 행은 이관 대상이 아니고 수정 시 1행 이상을 요구한다.
- **수용 기준**
  - Given 변수 3행에 각각 다른 단위, When 상세 조회, Then 세 행이 각자의 단위와 함께 보인다.
  - Given 대표를 고르지 않음, When 저장, Then 첫 행이 대표가 된다(자동 보정).
  - Given 변수 행이 1개, When 삭제 시도, Then 막히고 「변수는 하나 이상 있어야 해요」가 뜬다.
  - Given 마이그레이션 후, When 3원소이던 기존 행 조회, Then `d3_dataset_variable` 에 3행이 **순서대로** 있고 첫 행만 대표다.
  - Given 다른 연구실 계정, When 변수 행 조회 시도, Then **0건**(cross-tenant 음성).
  - Given 변수 `precipitation`, When 검색어 `precipitation`, Then 이관 전후 **같은** 데이터셋이 나온다.
- ⚠ **변수명 미러 트리거는 `M-10` 소속이고 이 파일 밖이다** — `M-10` 은 `R-B-2-server.md`(WU-B7 뒤)에서 **라운드 1회**만 돈다. 이 WU 는 **표와 이관까지** 세운다.

### WU-B4 · 공개 범위 3값 (PRD-11) — 계층 DB·계약·서버·FE · 크기 M · 레인 `p3-visibility-3`

- **의존**: WU-B3(FE 등록 ② 화면 · `R-B-3-frontend.md`). **DB·계약·서버 부분은 WU-B3 없이 시작할 수 있다.**
- **현재 코드** — `db/platform/schema.sql:171`(`CREATE TABLE d2_dataset_access`)·`:174`(`state text CHECK (state IN ('열림', '잠김'))`) · `:104-105`(`default_visibility text NOT NULL DEFAULT '열림' CHECK (default_visibility IN ('열림', '잠김'))`) · `services/core-api/src/colab_core/domains/d2_access.py:147`(`body_accessible=bool(open_ or r["granted"])`)·`:363`(`decide_access_request`) · `frontend/src/components/detail/DetailHeader.tsx:93`(`d.accessState === '잠김'`).
- ⚠ **계약은 신설이 아니라 확장이다** — `contracts/schemas/common.json:66-71` `AccessState` 가 **이미 있고 2값**(`enum ["열림","잠김"]` · `default "열림"`)이다. `LabDefaultVisibility`(`common.json:73-76`)가 `AccessState` 를 `$ref` 하므로 **한 곳을 3값으로 넓히면 둘이 같이 움직인다** — 매핑 표를 새로 만들지 않는다. `fe-core.yaml` 의 `accessState` 참조 = `:3626`·`:3917`·`:4222`.
- **요구 문면 축자** — 「기준축은 연구실 내부다 — 연구실 밖 열람 상태를 만들지 않고 RLS 경계를 손대지 않는다.」 · 「⚠ docx 3값을 이 표에 이름으로 짝지으면 안 된다 — 기준축이 한 칸씩 어긋난다.」 · 「불변식을 어디서 지키나 — 서버다. `잠김` ∧ 유효 grant ≥ 1 이 성립하지 않게 하는 검사를 서버에 둔다.」
- **값 대응 (정본)** — `열림` = 연구실 구성원 전체 / `잠김` = 나만 보기(허용 목록이 비어 있다) / `지정 공개` = 지정한 사람만(`d2_dataset_access_grant` · 만료 = 승인일 + 6개월 현행 유지).
- **변경 — DB** (`M-4` · **두 표**): `d2_dataset_access.state` CHECK 를 `IN ('열림','잠김','지정 공개')` 로 교체 ＋ `d1_lab_profile.default_visibility` CHECK 도 **같은 3값**으로 넓힌다. ⛔ 한쪽만 넓히면 연구실 기본값이 표현 못 하는 상태가 생긴다. 「열림/잠김」 어휘는 **지우지 않는다**.
- **변경 — 계약**: `common.json` `AccessState` enum 을 3값으로 확장(`default` 는 `열림` 유지). `DatasetCreate`·`DatasetUpdate` 에 `accessState: [string,"null"]` — NULL = 연구실 기본값(현행 의미 유지). `decideAccessRequest` 응답에 바뀐 상태를 싣는다.
- **변경 — 서버**: 등록 시 값을 `d2_dataset_access` 에 쓴다. **접근 판정 함수는 고치지 않는다** — `지정 공개` 는 grant 판정을 그대로 탄다(`d2_access.py:147`). 바뀌는 것은 **승인이 상태를 함께 올린다**는 점 하나다(`d2_access.py:363` `decide_access_request` — 지금은 grant 만 쓴다). 소유자가 `잠김` 으로 내리면 **같은 트랜잭션에서 유효 grant 전부 만료**.
- **변경 — 프론트**: 등록 ② 부가 정보에 셀렉트 · `DetailHeader.tsx:93` 표시를 3값 표기로 교체.
- **기존 데이터 처리**: **자동 매핑한다.** `열림`→`열림` · `잠김` ∧ 유효 grant 0건 →`잠김` · `잠김` ∧ 유효 grant ≥1 →`지정 공개` · NULL→NULL 유지. **재선택을 요구하지 않는다.**
- **수용 기준**
  - Given 마이그레이션 적용, When 유효 grant 를 가진 잠김 데이터셋 조회, Then 상태가 `지정 공개` 이고 그 사람의 접근이 종전과 같다(**양성·음성 둘 다**).
  - Given `나만 보기` 데이터셋에 접근 요청 승인, When 조회, Then 상태가 `지정 공개` 로 바뀌고 본체 접근이 열린다(같은 트랜잭션).
  - Given `지정 공개` ＋ 유효 grant 2건, When 소유자가 `나만 보기` 로 내림, Then 되묻는 문면에 `2명` 이 뜨고 확인 후 grant 2건이 만료된다.
  - Given 어느 시점이든, When `state='잠김'` 인 데이터셋의 유효 grant 를 셈, Then **0건**(불변식 회귀).
  - Given `나만 보기` 데이터셋, When 다른 구성원이 접근 요청, Then 접수된다(마이그레이션 `0010` 회귀).
  - Given 연구실 밖 계정, When 어느 상태의 데이터셋이든 조회, Then 보이지 않는다(**cross-tenant 음성 0건** = RLS 무개방 증명).
- ⛔ **RLS 경계를 넓히지 않는다**(연구실 밖 공개 = PRD-37 · 범위 밖).

### WU-B6 · Lv0 출처 칸 (PRD-19) — 계층 DB·계약·서버·FE · 크기 M · 레인 `p3-lv0-source`

- **의존**: WU-B1 · WU-B3(FE 등록 ③ · `R-B-3-frontend.md`).
- **현재 코드** — `db/platform/schema.sql:309`(`source_label text`)·`:343-347`(`source_label_normalized`)·`:354-356`(`d3_dataset_source_label_normalized_idx`). `sourceLabel` 계약 = `fe-core.yaml:3073`·`:3187`·`:3452`·`:3532`·`:3863`. ⚠ **`sourceUrl`·`sourceDownloadedOn` 키는 `contracts/seams/fe-core.yaml` 에 0건**(실측 grep) — **신설**이다.
- **요구 문면 축자** — 「원시 데이터라 부모가 없어요. 대신 어디서 언제 받았는지를 남겨요.」 · 「Lv.0 원천데이터의 경우 출처나 URL을 입력할 수 있는 속성이 있어야 합니다」(pdf 항목 3) · 「Lv 조건으로 갈리는 것은 두 칸(sourceUrl·sourceDownloadedOn)의 표시뿐이다. 그 둘은 Lv0 에서만 보이고, 보이는 동안에도 선택 입력이다.」 · 「목업 배지를 근거로 400 을 세우지 않는다.」
- **변경 — DB** (`M-8`): `d3_dataset` 에 `source_url text` · `source_downloaded_on date` 신설. `source_label` 은 **그대로 둔다**(정규화 컬럼·자동완성 색인이 붙어 있다).
- **변경 — 계약**: `DatasetCreate`·`DatasetUpdate`·`DatasetBasicInfo` 에 `sourceUrl: [string,"null"]` · `sourceDownloadedOn: [string,"null"], format: date`.
- **변경 — 서버**: 두 값은 **선택 입력**이다. 비어도 등록된다. **`Lv1` 이상에서 값이 와도 거절하지 않고 저장한다.**
- **변경 — 프론트**: 등록 ③, 원천 표기 아래 Lv0 전용 블록. `필수` 배지를 **붙이지 않는다** — `선택` 표기. 안내 = `원시 데이터라 부모가 없어요. 대신 어디서 언제 받았는지를 남겨요.` placeholder = `예: https://cds.climate.copernicus.eu/...` · `예: 2026-08-20`. ① 에서 Lv 를 바꾸면 즉시 열리고 닫힌다.
- **기존 데이터 처리**: 두 컬럼 **전 행 NULL**. 필수 검사가 없으므로 기존 행 수정이 막히지 않는다. 파생 Lv 가 Lv0 인 기존 행 상세에 「Lv0 인데 출처 주소·내려받은 날이 비어 있어요 — 수정에서 채워 주세요」를 **안내로만** 표시한다.
- **수용 기준**
  - Given ① 에서 Lv0 선택, When ③ 진입, Then 두 칸이 보이고 `선택` 표기가 붙는다.
  - Given ① 에서 Lv1 선택, When ③ 진입, Then 두 칸이 보이지 않고 **원천 표기는 그대로 보인다**.
  - Given Lv0 이고 출처 주소가 빔, When `createDataset`, Then **성공**한다.
  - Given Lv1 인데 `sourceUrl` 을 실어 보냄, When `createDataset`, Then **성공하고 값이 저장된다**.
  - Given ③ 에서 두 칸을 채운 뒤 ① 로 돌아가 Lv2 로 바꿈, When ③ 재진입, Then 두 칸이 숨고 저장 시 두 값이 전송되지 않는다.
- ⛔ **종전 완료 판정(「Lv0 이면 두 칸 필수·400」·「Lv1 이상 값 전송 시 400」)은 폐기됐다.**

### 마이그레이션 — 한 head

- **현재 단일 head = `0014_merge_ra1_and_topic_vocab`**(`db/platform/versions/0014_merge_ra1_and_topic_vocab.py`). **WU-B1 의 새 head 가 이것을 잇는다.**
- `M-1`·`M-2`·`M-3`(WU-B1) ＋ `M-5`(WU-B2) ＋ `M-4`(WU-B4 — **두 표**) ＋ `M-8`(WU-B6) = **한 head**. `migration-single-head` 게이트가 그것을 잰다.
- ⛔ **`M-10`(색인 재정의 ＋ 변수명 미러 트리거)은 이 파일에 넣지 않는다** — `R-B-2-server.md`(WU-B7 뒤)에서 **라운드 1회**만 돈다(생성 컬럼 재계산 ＋ GIN 재생성을 두 번 하지 않는다).
- ⛔ **`topic`·`variables`·`format` 컬럼을 지우지 않는다** — 되돌림 경로이자 이관 대조 근거다.
- ⚠ **미해결 질문 1건 — `M-10` 의 「색인 재정의 `topic`→`category`」 문면이 실측과 어긋난다.** 실측: `topic` 컬럼은 `d3_dataset_autometa` 에 **없고**(`d3_dataset_description:370` 뿐이다), `d3_dataset_autometa.search_vector`(`schema.sql:426-432`)는 **`format` ＋ `d3_search_join(variables)` 를 B**, **`crs`·`grid`·`bundle_file_name` 을 C** 로 물고 **`topic` 을 물지 않는다**. ⟹ 「`topic` 항을 `category` 로 교체」할 대상 항이 그 색인식에 존재하지 않는다. **여기서 지어내 봉합하지 않는다.** 해소는 **`M-10`(`R-B-2-server.md` · WU-B7 뒤)** 로 넘기고, 그 자리에서 ㈎ `d3_dataset_description.search_vector` 를 고칠 것인가 ㈏ `autometa` 색인에 `category` 를 새로 넣을 것인가를 **실측 후 판정**한다.

---

## 3. 지켜야 하는 규약 — 명령으로

### ㉮ 워크트리 레인

- WU 하나에 레인 하나. 레인 이름 = `p3-axes-schema`(B1) · `p3-variable-rows`(B2) · `p3-visibility-3`(B4) · `p3-lv0-source`(B6).
- 각 레인은 통합 브랜치에서 딴 자기 워크트리에서 돈다. 병합은 **ff-merge**, 병합 뒤 워크트리·로컬/원격 브랜치를 정리한다.
- **B1 이 head 를 만든 뒤에 B2·B4·B6 이 그 head 를 잇는다** — 마이그레이션 순서는 직렬이다.

### ㉯ 착수 전 — `work-items.yaml` 등재는 **이미 끝났다**

- **네 블록(`WU-B1`·`WU-B2`·`WU-B4`·`WU-B6`)이 대장에 이미 있다.** 확인 = `grep -n -A14 '^  - id: WU-B1' dev-package/work-items.yaml`.
- 이 세션이 하는 것은 **등재가 아니라 상태 갱신**이다 — 완료 시 `status: done` ＋ `evidence` 를 채운다.
- ⛔ **원장 행 없이 마이그레이션을 만들지 않는다.** 순서 = 대장(완료) → 마이그레이션 원장 등재 → 스키마.

### ㉰ 계약 동결 해제 — **20차 · 등급 ㉯ · Ted 승인 필수**

근거 문서 = `dev-package/sessions/X2-FREEZE-PROTOCOL.md` §5. 직전 회차 = **19차(R-A)**. 이 라운드가 여는 것은 **20차**다.
승인 요청 패키지 = `dev-package/sessions/R-B-C20-REQUEST-20260907.md` — **Ted 미승인**. ⚠ 실측 — 이 트리에 해당 파일 **부재**(`ls dev-package/sessions/ | grep C20` → 0건).
**이 파일이 여는 값** — `category`·`dataType`·`processingLevelUserSet`(B1) · `variables` 문자열 배열 → **객체 배열**(B2) · `AccessState` **2값 → 3값**(B4) · `sourceUrl`·`sourceDownloadedOn`(B6).
㉯ 인 사유 = 파괴적 변경 ＋ 마이그레이션 ≥1(M-1·M-2·M-3·M-5·M-4·M-8) ＋ 소비자 다수 ＋ 설계 판단 다수(기각한 대안이 있다 — PRD-16 ⓑ).

```bash
# ⑴ 파괴 판정을 실행 출력으로 낸다 (주장하지 않는다 — §5-㉱-1)
./gates/run.sh contract-breaking
# ⑵ 소비자 수를 grep 출력으로 낸다 (§5-㉱-3) — 2026-09-07 실측 163
grep -rn 'variables\|accessState\|lineageUnknown\|category' contracts/ services/ frontend/src | wc -l
# ⑶ 이 파일의 마이그레이션 건수 = 6 (M-1·M-2·M-3·M-5·M-4·M-8, head 1개)  ⑷ 되돌림 경로를 적는다
```
⛔ **승인 없이 `contracts/` 를 고치지 않는다.** ⛔ **§5-㉰-4(집행 없는 신설) 금지** — 계약만 열고 서버 수용 목록(`_ALLOWED_CREATE_FIELDS` · `services/core-api/src/colab_core/app/routes/ingestion.py:382`)을 다음 회차로 미루지 않는다. ⛔ **§5-㉰-6(묶음 쪼개기) 금지** — WU 별로 쪼개 각 조각을 ㉮ 로 통과시키지 않는다. **목적 단위로 판정한다.**

### ㉱ 결정 번호 〈N〉 — 예약하지 않는다

```bash
git fetch origin main && bash dev-package/prd/tools/max-decision.sh   # 병합 직전에 다시 잰다
```
착수 시점 참고값 = **〈372〉**(2026-09-07 실측). **병합 직전 `origin/main` 최대 ＋ 1** 이 이번 번호다.
`PLAN-SoT §9` 표에 **두 행**을 병합 직전에 덧붙인다 — 필드 8개(X2 §5-㉲).

```
| 〈N〉 | **R-B-1 DB 계층 — 계약 동결 해제 20차 · 분류 3축 ＋ 변수 행 표 ＋ 공개 범위 3값 ＋ 출처 2칸** | **집행 (2026-MM-DD · 워크트리 `<레인>` · 병합 `<sha>`).** ①회차 = **20차**(직전 19차 = R-A) ②값 = `category`·`dataType`·`processingLevelUserSet` · `variables` 객체 배열 · `AccessState` 3값 확장 · `sourceUrl`·`sourceDownloadedOn` ③근거 = PRD-01·02·03·11·16·19 (`dev-package/prd/PRD-260905-적용전기획.md`) ④가·파 판정 = **파괴** · `contract-breaking` 출력 = `<축자>` ⑤소비자 = `<n>` 건 · 측정법 = `grep -rn 'variables\|accessState\|lineageUnknown\|category' contracts/ services/ frontend/src` ⑥마이그레이션 = **6건 · head 1개**(M-1·M-2·M-3·M-5·M-4·M-8) ⑦승인 = Ted · `<일자>` ⑧이번에 세지 않은 축 = `M-10` 색인 재정의(R-B-2 로 넘김 · 대상 항 실측 불일치 미해결) `[미측정]` |
| 〈N+1〉 | **`〈194〉`·`〈276〉` 반전 — 「레벨은 언제나 계보에서 나온다 — 예외 없음」을 되돌린다. 사람이 Lv 를 고르고 불일치는 경고만 낸다** | **반전 (미결-2 ⓐ · Ted 2026-09-05).** ⛔ **원래 근거 문단과 마이그레이션 `0011` 의 삭제 근거 주석(`db/platform/schema.sql:332`)을 지우지 않는다** — 남긴 채 이 반전 항목을 덧붙인다 |
```
⛔ **HANDOFF 에는 값을 적지 않는다**(`CLAUDE.md §6-3`).

### ㉲ 게이트 — 작업 중엔 단독, 병합 전엔 전건

```bash
# 작업 중 (단독 게이트만 하나씩)
./gates/run.sh schema-diff                 # B1 · B2 · B4 · B6
./gates/run.sh migration-single-head       # B1 · B2 · B4 · B6
./gates/run.sh contract-lint               # B1 · B2 · B4 · B6
./gates/run.sh contract-breaking           # 같음
./gates/run.sh generated-up-to-date        # B1
./gates/run.sh service-tests-core-api      # B1 · B2 · B4 · B6
./gates/run.sh rls-coverage                # B2
./gates/run.sh rls-effect                  # B2 · B4
./gates/run.sh autometa-loss               # B2
./gates/run.sh frontend-typecheck          # FE 가 닿는 전부
./gates/run.sh frontend-test               # 같음
# 병합 직전 한 번
./gates/run.sh all -j 1
```
⛔ **게이트를 끄거나 검사 대상을 줄이지 않는다.** 미구현 게이트의 red 는 버그가 아니다. **green 으로 시작한 테스트는 오라클이 아니다** — 실패 테스트 red 를 먼저 확인한다.

### ㉳ 커밋 문면

```
DB 계층 R-B-1 — 분류 3축 · 변수 행 표 · 공개 범위 3값 · 출처 2칸 한 head (WU-B1·B2·B4·B6)

- M-1·M-2·M-3·M-5·M-4·M-8 을 한 head 로 묶었다 (migration-single-head green · 앞 head = 0014_merge_ra1_and_topic_vocab)
- 계약 동결 해제 20차 · 등급 ㉯ · Ted 승인 <일자> · PLAN-SoT §9 〈N〉 ＋ 〈194〉 반전 〈N+1〉 등재
- RED 선실측 → GREEN: <시험 파일>:<건수>
```

### ㉴ 금지

- ⛔ `main` 에 직접 push. ⛔ staging DB 직접 쓰기(변경은 마이그레이션 경유로만). ⛔ 원장 행 없이 마이그레이션.
- ⛔ `topic`·`variables`·`format` 컬럼 삭제. ⛔ `M-10` 을 이 파일에서 돌리기.
- ⛔ `〈194〉`·`〈276〉` 원문 문단과 `0011` 삭제 근거 주석(`schema.sql:332`) 지우기 — **반전은 덧붙이는 것**이다.
- ⛔ `ProcessingLevel`·`AccessState` 의 기존 description 지우기 — **덧붙인다**.
- ⛔ WU-B6 에서 두 칸을 필수로 잠그거나 Lv1 이상 값을 400 으로 거절하기(**폐기된 판정**).
- ⛔ WU-B4 에서 RLS 경계 넓히기. ⛔ 유형↔가공 단계 조합 검증 신설. ⛔ D2 가 `d3_dataset_variable` 을 FK 하기.
- ⛔ 미결-17 의 잘린 1행을 **추정 전사**하기. ⛔ `40 COLAB-기획/` 문서 수정. ⛔ 문서·주석에 절대경로.
- ⛔ 이 세션이 `03-HANDOFF.md` 를 직접 고치기 — §4 의 5줄만 넘긴다.

---

## 4. 산출물과 근거

| 무엇 | 어디 |
|---|---|
| 마이그레이션 | `db/platform/versions/` 아래 신규 파일 — **head 1개**(M-1·M-2·M-3·M-5·M-4·M-8) · 앞 head = `0014_merge_ra1_and_topic_vocab` ＋ 마이그레이션 원장 행 |
| 계약 | `contracts/schemas/common.json` — `AccessState`(3값)·`ProcessingLevel`(반전 문면 증보) / `contracts/seams/fe-core.yaml` — `DatasetCreate`·`DatasetUpdate`·`DatasetBasicInfo` · `DatasetVariable` 신설 |
| 서버 | `services/core-api/.../routes/catalog.py`(`_CATEGORIES`·`_DATA_TYPES`·`_PROCESSING_LEVELS`) · `routes/ingestion.py:382`(`_ALLOWED_CREATE_FIELDS`) · `domains/d2_access.py:363`(`decide_access_request`) |
| 프론트 | 분류·유형·Lv 셀렉트 · 변수 표(5열) · 공개 범위 셀렉트 ＋ `DetailHeader.tsx:93` 3값 표기 · Lv0 출처 블록 |
| 세션 노트 | `dev-package/sessions/p3-axes-schema-<YYYYMMDD>.md` · `p3-variable-rows-…` · `p3-visibility-3-…` · `p3-lv0-source-…` — **각 ≤ 60행** |
| 대장 | `dev-package/work-items.yaml` — 네 블록이 **이미 등재됨**. 완료 시 `status: done` ＋ `evidence` 갱신 |
| 원장 | `PLAN-SoT §9` 두 행(㉱ 문안) — **병합 직전** |

**오케스트레이터에 넘기는 HANDOFF 갱신문 — 5줄 이하. 세션이 `03-HANDOFF.md` 를 직접 고치지 않는다.**

```
R-B-1(DB) 완료 — WU-B1·B2·B4·B6, 레인 p3-axes-schema · p3-variable-rows · p3-visibility-3 · p3-lv0-source, 병합 <sha…>
마이그레이션 1 head (M-1·M-2·M-3·M-5·M-4·M-8, 앞 head 0014_merge_ra1_and_topic_vocab) · 계약 동결 해제 20차 승인 <일자> · PLAN-SoT §9 〈N〉·〈N+1〉 등재
게이트: ./gates/run.sh all -j 1 = green <n>/<n> (red(판정) 0) · cross-tenant 음성 0건 · state='잠김' ∧ 유효 grant ≥1 = 0건
미해결 1건 — M-10 「색인 재정의 topic→category」 문면이 실측과 불일치(autometa.search_vector 에 topic 항 없음). R-B-2 WU-B7 뒤에서 판정
근거: dev-package/sessions/p3-axes-schema-<YYYYMMDD>.md 외 3건
```

---

## 5. 완료 판정

- **WU-B1** — 5값·6값·4값 CHECK 가 서고 계약에 세 열쇠가 있다 · 값 집합 밖은 **400**(500 아님) · 기존 13행이 전부 `category`·`data_type`·`processing_level_user_set` NULL 이고 `topic` 값은 그대로 · 사람 Lv 와 파생 Lv 불일치가 **경고만** · 유형↔Lv 조합 제약 **없음**.
- **WU-B2** — `d3_dataset_variable` 이 서고 RLS ＋ 대표 1개 부분 UNIQUE 가 걸린다 · 배열 이관이 **순서대로** 되고 **첫 행이 대표** · 마지막 행 삭제가 막힌다 · **cross-tenant 음성 0건** · 변수명 검색이 이관 전후 같은 데이터셋을 낸다. ⚠ 미러 트리거는 `M-10` 소속(이 파일 밖).
- **WU-B4** — `state` 3값 ＋ `default_visibility` 3값이 **둘 다** 선다 · 자동 매핑 후 기존 허용자의 접근이 종전과 같다(**양성·음성 둘 다**) · 승인이 상태를 같은 트랜잭션에서 올린다 · **`state='잠김'` ∧ 유효 grant ≥1 인 행이 어느 시점에도 0건** · **cross-tenant 음성 0건**.
- **WU-B6** — 두 칸이 서고 **선택 입력**이다 · Lv0 에서 비운 채 등록 **성공** · Lv1 이상에서 값을 실어도 **저장** · `sourceLabel` 은 **늘 보인다** · Lv 변경 시 두 칸이 열리고 닫히며 숨은 값이 전송되지 않는다.
- **게이트** — `schema-diff` · `migration-single-head` · `contract-lint` · `contract-breaking` · `generated-up-to-date` · `service-tests-core-api` · `rls-coverage` · `rls-effect` · `autometa-loss` · `frontend-typecheck` · `frontend-test` 전건 green, 그리고 병합 직전 `./gates/run.sh all -j 1` green.
- **절차** — 20차 승인이 `contracts/` 첫 수정보다 **먼저** 있었음이 커밋 순서로 보인다 · `〈N〉` 이 병합 직전 실측값이다 · `〈194〉` 반전이 **원문을 지우지 않고** 덧붙여져 있다 · head 가 `0014_merge_ra1_and_topic_vocab` 을 잇는다.

---

### 다음 파일

`dev-package/prd/rounds/R-B-2-server.md`(계약·서버 · B5·B7·B8 ＋ **`M-10`**) → `R-B-3-frontend.md`(B3·B10) → `R-B-4-verify.md`(B11 ＋ 라운드 종료 검증).
⚠ **이 파일의 FE 꼬리(B4 셀렉트 · B6 Lv0 블록 · B2 변수 표)는 `R-B-3` 의 WU-B3 등록 3단계 재구성 위에 얹힌다.** DB·계약·서버 부분은 WU-B3 없이 시작할 수 있다.
