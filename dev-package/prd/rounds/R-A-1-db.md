# R-A-1 · DB · 마이그레이션 계층 — WU-A5 · WU-A6

> 이 파일 하나로 세션을 시작한다. 라운드 = **R-A** · 계층 = **DB(＋계약·서버·FE 꼬리)** · WU **2건**.
> 마이그레이션 **M-9 · M-6 · M-7** 을 **한 head 에** 담는다.

---

## 0. 읽기 규칙 — 이 파일이 유일한 부트스트랩

> ⛔ **아래 4개를 통째로 열지 않는다.** 세션이 느려지는 원인이 이것이다.
> `dev-package/03-HANDOFF.md`(다이어트 후 약 127 KB, 그래도 통째로 열지 않는다) · `dev-package/PLAN-SoT.md`(1.17 MB) · `dev-package/work-items.yaml`(513 KB) · `dev-package/WORK-UNITS.md`(138 KB)

- **허용된 접근은 아래 세 줄뿐이다.**
  1. 결정 번호 최대값 — `bash dev-package/prd/tools/max-decision.sh`
  2. 대장에서 항목 하나 — `grep -n -A14 '^  - id: WU-A5' dev-package/work-items.yaml`
  3. 게이트 이름 확인 — `sed -n '12,30p' gates/run.sh` (`ALL_GATES` 배열)
- `03-HANDOFF.md` · `CLAUDE.md` · `RESTART.md` 는 **머리 부분만** 읽는다. 본문 통독 금지.
- 요구사항 정본은 이 파일과 `dev-package/prd/PRD-260905-적용전기획.md` 다. 이 파일에 옮겨 적힌 문면이 우선이고, 더 필요하면 PRD 사본에서 **해당 `#### PRD-xx` 절만** 읽는다.
- **코드 파일은 고칠 때만 연다.** 현황 정찰·grep 스윕·다수 파일 읽기는 **서브에이전트에 위임**하고 결론만 회수한다 — 메인 컨텍스트에 파일 덤프를 들이지 않는다.
- 못 읽으면 `[미상]` 이고 실패다. 지어내지 않는다.

---

## 1. 확정 결정 — 다시 열지 않는다 (PRD §1 · Ted 2026-09-05)

미결 18건이 전부 닫혔다 = 확정 16 ＋ 해소 1(미결-8) ＋ 개발 실측 1(미결-10). **기획자에게 받아야 하는 답은 0건이다.**
아래 16줄이 요구사항이다. 다르게 구현할 사유를 찾으면 **고치지 말고 보고한다.**

- 미결-1 ⓐ — 공개 범위는 **연구실 내부 3값**(`연구실 구성원 전체`/`나만 보기`/`지정한 사람만`). RLS 경계를 열지 않고 PRD-37·WU-C5 를 열지 않는다
- 미결-2 ⓐ — 가공 단계를 **사람이 고르고**, 계보 계산값과 어긋나면 **경고만** 낸다(등록을 막지 않는다)
- 미결-3 ⓐ — 기존 13행의 3축은 **전 행 NULL**, 자동 매핑 없음. 표기 「분류를 아직 안 골랐어요」, `topic` 열은 남긴다
- 미결-4 ⓐ — 관측 간격은 **선택 입력**. 저장은 수치＋단위 두 칸, 표기는 기간 뒤 괄호
- 미결-5 ⓐ — 설명 필수화 후 빈 기존 행은 **그대로 두고** 그 행을 수정할 때 채우게 한다(`NOT NULL` 금지 · 일괄 채우기 금지)
- 미결-6 ⓐ — 확정 부모 1건 이상이면 체크박스 **잠금＋사유 한 줄**. 라벨 = `가공 전 데이터를 못 찾았어요 — 기록 없이 등록할게요`
- 미결-7 ⓐ — 가공 단계 **Lv0~Lv3 네 단**(CHECK·enum·칩 4단)
- 미결-9 ⓑ — 상세는 **한 페이지 스크롤 유지 ＋ sticky 구역 메뉴 ＋ 활성 표시**. 정본을 개정하지 않고 탭·패널 전환을 만들지 않는다
- 미결-11 ⓐ — 원천 표기는 **Lv 무관 상시 노출**, `출처 주소`·`내려받은 날` 두 칸만 Lv0 게이팅
- 미결-12 ⓐ — 유형별 주의 문구는 **선택기 아래 보조 문구 ＋ 설명란 힌트**(저장 칸 없음)
- 미결-13 ⓐ — 분류·유형은 **표시만 국문＋영문 병기**, 저장·CHECK·필터·색인은 국문 단일
- 미결-14 ⓐ — 유형↔가공 단계 **제약 없음**(조합 검증을 만들지 않는다)
- 미결-15 ⓐ — 종료 모달은 **조건만** 고치고 **문면은 유지**한다(PRD-34 범위 밖)
- 미결-16 ⓐ — 등록 ③ 의 쓰임 한 줄은 **받지 않는다**(PRD-36 · WU-C4 범위 밖)
- 미결-17 ⓐ — pdf 항목 8 잘린 1행은 원문 요청 중이다. **회신 대기가 착수를 막지 않는다**
- 미결-18 ⓐ — 기간은 **시각값 저장 유지**, 화면이 최소 단위 셀렉트＋Start/End 를 조립한다. 신규는 `period_granularity` 열 하나
- (미결-8 = 해소 · 미결-10 = WU-A11 실측 결과가 곧 범위 — 이 파일 밖이다)

---

## 2. 범위 — 이 파일의 WU 2건

### WU-A5 · 확장자 표기 (PRD-21) — 계층 DB·계약·서버·FE · 크기 M · 레인 `p3-extension-label`

- **의존**: 없음. FE 부분은 WU-A3(상세 수정 골격)이 서 있으면 그 위에 얹는다.
- **현재 코드** — `services/core-api/src/colab_core/domains/d3_catalog.py:666,682`(`detected_format` 을 `autometa.format` 에 저장 → 상세가 보이는 `format` 은 **판별 결과 문자열**) · `services/core-api/.../routes/ingestion.py:9`(「확장자로 포맷을 정하지 않는다」 규칙 주석) · `db/platform/schema.sql:411` 부근(`d3_dataset_autometa.search_vector` 가 `format` 을 B 가중치로 물고 있다).
- **판정 (PRD 축자)** — 두 규칙이 **충돌하지 않는다.** 코드 규칙은 「확장자로 포맷을 단정하지 않는다」이고, 문서 요구는 「단정한 포맷 이름을 화면에 쓰지 말고 확장자를 써라」다. 같은 방향이다.
- **변경 — DB** (부록 B `M-9`): `d3_dataset_autometa` 에 `file_extension text` 신설. 조각의 확장자다(모든 조각이 같은 확장자여야 하므로 **데이터셋당 1값** — `P-5` 정책). `format` 컬럼은 **남긴다**(판별 결과는 파이프라인·미리보기가 계속 쓴다).
- **변경 — 계약**: `DatasetBasicInfo` 의 표시용 열쇠를 `fileExtension` 로 더한다. `format` 은 유지하되 「내부 판별값 · 화면에 쓰지 않는다」를 description 에 적는다.
- **변경 — 프론트**: 상세·목록·등록의 포맷 표기를 `*.nc` 형태로. 등록 ② 라벨은 `확장자` 이며 `자동` 태그가 붙는다. 업로드 안내를 **업로드 가능 / 미리보기 가능** 둘로 가른다 — 진입 = `어떤 포맷이든 올려요 · 같은 확장자면 여러 개를 한 데이터셋으로 묶어요`, 미리보기 = `지도 미리보기까지 되는 확장자: *.nc *.tif *.hdf *.bin`, 그 밖은 `이 확장자는 지도로 못 그려요`.
- **기존 데이터 처리**: `file_extension` 은 마이그레이션이 `d3_file` 의 파일명에서 뽑아 채운다(마지막 `.` 뒤, 소문자화). 뽑히지 않으면 NULL 이고 화면은 `format` 값을 그대로 보인다(퇴행 표시).
- **수용 기준**
  - Given `nakdong_precip_2025.nc` 조각, When 상세 조회, Then 포맷 자리에 `*.nc` 가 보이고 `NetCDF-4` 같은 판별 문자열이 보이지 않는다.
  - Given `.hdf` 파일, When 상세 조회, Then `*.hdf` 다(HDF4/HDF5 를 단정하지 않는다).
  - Given 확장자 없는 파일명, When 상세 조회, Then 판별값 표기로 떨어지고 화면이 깨지지 않는다.
  - Given 마이그레이션 후, When 기존 13행 조회, Then `file_extension` 이 파일명과 일치한다.
- ⚠ **「`nc` 로도 찾는다」는 이 WU 의 완료 판정에서 뺀다.** 색인 재정의(부록 B `M-10`)는 `category` 이관·변수명 미러와 한 마이그레이션으로 묶여 **R-B 에서 한 번만** 돈다(생성 컬럼 재계산 ＋ GIN 재생성을 두 번 하지 않는다). **R-A 는 컬럼만 세우고 색인식을 손대지 않으며, 검색은 종전대로 `format` 으로 잡힌다**(`netcdf` 는 되고 `nc` 는 아직 안 된다). ⟹ **라운드 종료 보고에 「미충족 1건 · 사유 = 색인 재생성 1회로 묶음」을 적는다.**

### WU-A6 · 관측 간격 · 기간 최소 단위 · 기간 표기 (PRD-17 · 18 · 35) — 계층 DB·계약·서버·FE · 크기 M · 레인 `p3-interval-period`

- **의존**: **WU-A5(같은 마이그레이션 head)** · WU-A3(FE 편집 화면). 미결 의존 없음(미결-4 ⓐ · 18 ⓐ 확정).

**PRD-17 · 관측 간격 — 부가 정보의 선택 입력**
- **현재 코드**: 컬럼·계약 열쇠 어디에도 없다.
- **변경 — DB** (`M-6`): `d3_dataset_description` 에 **두 칸** — `observation_interval_value numeric` · `observation_interval_unit text CHECK (… IS NULL OR … IN ('초','분','시','일','월','년'))`. 한쪽만 채워지지 않게 **「둘 다 NULL 이거나 둘 다 값」** CHECK 를 건다. (사람이 적는 값이라 `autometa` 가 아니다.)
- **변경 — 계약**: `DatasetCreate`·`DatasetUpdate`·`DatasetBasicInfo` 에 `observationInterval: {value: [number,"null"], unit: [string,"null"]}`(객체 · nullable). **표시 문자열을 계약에 싣지 않는다** — 화면이 조립한다.
- **변경 — 프론트**: ② 단계 부가 정보에 입력 1칸. placeholder = `예: 10분 · 1시간 · 1일`(rev1 축자). 단위 선택기를 곁들여 조립한다 — 단위 목록 `초·분·시·일·월·년`.
- **기존 데이터**: 전 행 NULL. 상세는 「관측 간격 미기재」. **재선택을 강제하지 않는다.**
- **수용 기준** — 단위 `분`＋`10` 저장 후 재조회 시 `value=10`·`unit='분'` 이고 화면 표기 `10분` / 숫자만 채우고 단위를 비우면 `createDataset` **400** / 값을 비운 채 등록하면 **성공**(선택 항목) / 기존 행 상세는 「관측 간격 미기재」이고 화면이 안 깨진다.
- ⛔ **관측 간격을 등록 게이트에 올리지 않는다.**

**PRD-18 · 기간에 최소 단위(granularity)를 더한다**
- **현재 코드**: `contracts/seams/fe-core.yaml:2302` `DataPeriod` = `start`/`end`, `format: date-time` · `db/platform/schema.sql:398` `period_start`/`period_end timestamptz`. **저장은 이미 구조화돼 있다** — 없는 것은 **최소 단위 선택**뿐이다.
- **변경 — DB** (`M-7`): `d3_dataset_autometa` 에 `period_granularity text CHECK (… IN ('년','월','일','시','분','초'))`.
- **변경 — 계약**: `DataPeriod` 에 `granularity: [string,"null"]` 추가. ⚠ `DataPeriod` 는 `additionalProperties: false` 라 **열쇠 추가가 계약 파괴 변경이다**(`catalog.py:630-640` 주석이 명시). 계약 개정 절차를 탄다 — §3-㉰.
- **변경 — 서버**: 값 검사 6값. 기간 파싱 로직(`catalog.py` `_period()` 계열)에 granularity 를 통과시킨다.
- **변경 — 프론트**: 기간 입력 앞에 최소 단위 셀렉트. 고른 단위까지만 칸이 열린다 — `분` 이면 `연·월·일·시·분` 다섯 칸이 Start/End 각각. 저장은 timestamptz 로 조립하되 **비운 하위 자리는 0 으로 채운다**.
- **기존 데이터**: 전 행 NULL = 「단위 미지정」. 화면은 종전과 같이 `date-time` 전체를 보인다. **재선택 없음.**
- **수용 기준** — 단위 `일` 선택 시 연·월·일 세 칸만 열린다 / `2025-06-01`~`2025-06-30`·단위 `일` 저장 후 재조회 시 시·분·초를 노출하지 않는다 / granularity NULL 인 기존 행 상세는 **종전 표기 그대로**다.

**PRD-35 · 기간 표기에 관측 간격을 괄호로 병기한다**
- **변경 — 프론트만.** 기간을 보이는 **모든 자리**(상세 기본 정보 · 목록 카드 · 등록 미리보기)에서 관측 간격이 있으면 기간 뒤에 ` ({값}{단위})` 를 붙인다 — **한 곳에서만 조립하고 세 자리가 그 함수를 쓴다.** 비면 괄호를 그리지 않는다. DB·계약·서버 변경 **없음**.
- **수용 기준** — 기간 `2020-05-01 00:00 ~ 03:00` ＋ 간격 `10분` ⟹ 표기 `2020-05-01 00:00 ~ 03:00 (10분)` / 간격이 비면 `2020-05-01 00:00 ~ 03:00` 이고 **빈 괄호가 없다** / 목록 카드가 상세와 같은 규칙으로 그려진다.

### 마이그레이션 — 한 head

`M-9`(WU-A5) ＋ `M-6`·`M-7`(WU-A6) 을 **한 마이그레이션 파일에 묶는다**. `migration-single-head` 게이트가 그것을 잰다.
⛔ **`M-10`(색인 재정의)은 R-A 에 넣지 않는다.** ⛔ **`topic`·`variables`·`format` 컬럼을 지우지 않는다** — 되돌림 경로이자 이관 대조 근거다.

---

## 3. 지켜야 하는 규약 — 명령으로

### ㉮ 워크트리 레인

- WU 하나에 레인 하나. 레인 이름 = `p3-extension-label`(WU-A5) · `p3-interval-period`(WU-A6).
- 각 레인은 `origin/main` 에서 딴 자기 워크트리에서 돈다. 병합은 **ff-merge**, 병합 뒤 워크트리·로컬/원격 브랜치를 정리한다.
- 한 레인 = 한 WU. 두 WU 를 한 브랜치에 섞지 않는다.

### ㉯ 착수 전 — `work-items.yaml` 등재가 먼저다

⛔ **원장 행 없이 마이그레이션을 만들지 않는다.** 순서 = 대장 등재 → 마이그레이션 원장 등재 → 스키마.
`dev-package/work-items.yaml` 의 `items:` 리스트 **끝에** 아래를 그대로 덧붙인다(들여쓰기 2칸).

```yaml
  - id: WU-A5
    name: 확장자 표기 (PRD-21)
    status: in_progress
    stage: stage2
    owner: "T-R"
    entry_conditions: ["계약 동결 해제 19차 승인 (등급 ㉯)"]
    depends_on: []
    completion_def: "상세가 *.nc 를 보이고 판별 문자열을 안 보인다 · file_extension backfill 이 기존 13행 파일명과 일치 · 검색은 종전대로 format 으로 잡힌다(「nc 로도 찾는다」는 R-B M-10)"
    evidence: "dev-package/sessions/p3-extension-label-<YYYYMMDD>.md"
    deadline: null
    note: "M-9. WU-A6 의 M-6·M-7 과 한 마이그레이션 head 로 묶는다"
    sources: ["dev-package/prd/rounds/R-A-1-db.md", "PRD-21", "부록 B M-9"]

  - id: WU-A6
    name: 관측 간격 · 기간 최소 단위 · 기간 표기 (PRD-17·18·35)
    status: in_progress
    stage: stage2
    owner: "T-R"
    entry_conditions: ["계약 동결 해제 19차 승인 (등급 ㉯)", "WU-A5 와 같은 마이그레이션 head"]
    depends_on: ["WU-A3", "WU-A5"]
    completion_def: "단위 분 선택 시 다섯 칸이 열리고 value=10·unit='분' 이 저장되며 화면이 10분 으로 조립한다 · 숫자만 채우면 400 · 값을 비우면 등록 성공 · granularity NULL 기존 행 표기가 종전과 같다 · 간격이 있으면 기간 뒤 (10분), 없으면 빈 괄호가 없다"
    evidence: "dev-package/sessions/p3-interval-period-<YYYYMMDD>.md"
    deadline: null
    note: "M-6·M-7. DataPeriod 는 additionalProperties:false 라 granularity 추가가 계약 파괴 변경이다"
    sources: ["dev-package/prd/rounds/R-A-1-db.md", "PRD-17", "PRD-18", "PRD-35", "부록 B M-6·M-7"]
```

### ㉰ 계약 동결 해제 — **19차 · 등급 ㉯ · Ted 승인 필수**

근거 문서 = `dev-package/sessions/X2-FREEZE-PROTOCOL.md` §5. 직전 회차 = **18차**. 이 라운드가 여는 것은 **19차**다.
**이 파일의 WU-A6 이 계약을 연다**(`DataPeriod.granularity`). 같은 19차에 R-A-2 의 **WU-A4**(`DatasetCreate.required` 에 `summary`)가 함께 실린다 — ⛔ **WU 별로 쪼개 각 조각을 ㉮ 로 통과시키지 않는다**(§5-㉰-6 묶음 쪼개기 금지). **목적 단위로 판정한다.**
㉯ 인 사유 = 파괴적 변경(`additionalProperties: false`) ＋ 마이그레이션 ≥1(M-6·M-7·M-9) ＋ 소비자 ≥1(`DataPeriod` 를 읽는 화면·서버 전 지점).

```bash
# ⑴ 파괴 판정을 실행 출력으로 낸다 (주장하지 않는다 — §5-㉱-1)
./gates/run.sh contract-breaking
# ⑵ 소비자 수를 grep 출력으로 낸다 (§5-㉱-3)
grep -rn 'DataPeriod\|granularity' contracts/ services/ frontend/src | wc -l
# ⑶ 마이그레이션 건수 = 3 (M-9 · M-6 · M-7, 한 head)
# ⑷ 되돌림 경로를 적는다 (컬럼 drop 없이 되돌아가는 길)
```
⛔ **승인 없이 `contracts/` 를 고치지 않는다.** ⛔ **§5-㉰-4(집행 없는 신설) 금지** — 계약만 열고 서버 수용 목록(`_ALLOWED_CREATE_FIELDS`)을 다음 회차로 미루지 않는다. **계약 · 서버 · 화면 · 시험을 한 회차에 세운다.**

### ㉱ 결정 번호 〈N〉 — 예약하지 않는다

```bash
git fetch origin main && bash dev-package/prd/tools/max-decision.sh   # 병합 직전에 다시 잰다
```
착수 시점 참고값 = **〈326〉**(2026-09-05 실측). **병합 직전 `origin/main` 최대 ＋ 1** 이 이번 번호다.
`PLAN-SoT §9` 표에 아래 한 행을 **병합 직전에** 덧붙인다 — 필드 8개(X2 §5-㉲).

```
| 〈N〉 | **R-A-1 DB 계층 — 계약 동결 해제 19차 · `DataPeriod.granularity` ＋ `file_extension` ＋ 관측 간격 2칸** | **집행 (2026-MM-DD · 워크트리 `<레인>` · 병합 `<sha>`).** ①회차 = **19차**(직전 18차) ②값 = `DataPeriod.granularity` · `DatasetBasicInfo.fileExtension` · `observationInterval{value,unit}` ③근거 = PRD-17·18·21·35 (`dev-package/prd/PRD-260905-적용전기획.md`) ④가·파 판정 = **파괴** · `contract-breaking` 출력 = `<축자>` ⑤소비자 = `<n>` 건 · 측정법 = `grep -rn 'DataPeriod\|granularity' contracts/ services/ frontend/src` ⑥마이그레이션 = **3건 · head 1개**(M-9·M-6·M-7) ⑦승인 = Ted · `<일자>` ⑧이번에 세지 않은 축 = `M-10` 색인 재정의(R-B 로 묶음) `[미측정]` |
```
⛔ **HANDOFF 에는 값을 적지 않는다** — 두 곳에 적으면 갈라진다(`CLAUDE.md §6-3`).

### ㉲ 게이트 — 작업 중엔 단독, 병합 전엔 전건

```bash
# 작업 중 (단독 게이트만 하나씩)
./gates/run.sh schema-diff
./gates/run.sh migration-single-head
./gates/run.sh contract-lint
./gates/run.sh contract-breaking
./gates/run.sh service-tests-core-api
./gates/run.sh e2e-format-coverage          # WU-A5
./gates/run.sh frontend-typecheck
./gates/run.sh frontend-test
# 병합 직전 한 번
./gates/run.sh all -j 1
```
⛔ **게이트를 끄거나 검사 대상을 줄이지 않는다.** 미구현 게이트의 red 는 버그가 아니다. **green 으로 시작한 테스트는 오라클이 아니다** — 실패 테스트 red 를 먼저 확인한다.

### ㉳ 커밋 문면

```
DB 계층 R-A-1 — file_extension · 관측 간격 2칸 · period_granularity 한 head (WU-A5·A6)

- M-9 · M-6 · M-7 을 한 마이그레이션에 묶었다 (migration-single-head green)
- 계약 동결 해제 19차 · 등급 ㉯ · Ted 승인 <일자> · PLAN-SoT §9 〈N〉 등재
- RED 선실측 → GREEN: <시험 파일>:<건수>
```

### ㉴ 금지

- ⛔ `main` 에 직접 push. ⛔ staging DB 직접 쓰기(변경은 마이그레이션 경유로만).
- ⛔ 원장 행 없이 마이그레이션. ⛔ `topic`·`variables`·`format` 컬럼 삭제. ⛔ `M-10` 을 R-A 에서 돌리기.
- ⛔ `40 COLAB-기획/` 문서 수정(읽기 전용 · 고칠 것은 제안만). ⛔ 문서·주석에 절대경로.
- ⛔ 이 세션이 `03-HANDOFF.md` 를 직접 고치기 — §4 의 5줄만 넘긴다.

---

## 4. 산출물과 근거

| 무엇 | 어디 |
|---|---|
| 마이그레이션 | `db/` 아래 신규 파일 **1개**(M-9·M-6·M-7 합본) ＋ 마이그레이션 원장 행 |
| 계약 | `contracts/seams/fe-core.yaml` — `DataPeriod` · `DatasetBasicInfo` · `DatasetCreate` · `DatasetUpdate` |
| 서버 | `services/core-api/.../routes/catalog.py`(`_period()` 계열) · `_ALLOWED_CREATE_FIELDS`(`routes/ingestion.py:400`) |
| 프론트 | 포맷 표기 · 관측 간격 입력 · 기간 최소 단위 셀렉트 · 기간 표기 조립 함수(**한 곳**) |
| 세션 노트 | `dev-package/sessions/p3-extension-label-<YYYYMMDD>.md` · `dev-package/sessions/p3-interval-period-<YYYYMMDD>.md` — **각 ≤ 60행** |
| 대장 | `dev-package/work-items.yaml` — 위 두 블록. 완료 시 `status: done` ＋ `evidence` 갱신 |
| 원장 | `PLAN-SoT §9` 한 행(㉱ 문안) — **병합 직전** |

**오케스트레이터에 넘기는 HANDOFF 갱신문 — 5줄 이하. 세션이 `03-HANDOFF.md` 를 직접 고치지 않는다.**

```
R-A-1(DB) 완료 — WU-A5 · WU-A6, 레인 p3-extension-label · p3-interval-period, 병합 <sha1>·<sha2>
마이그레이션 1 head (M-9·M-6·M-7) · 계약 동결 해제 19차 승인 <일자> · PLAN-SoT §9 〈N〉 등재
게이트: ./gates/run.sh all -j 1 = green <n>/<n> (red(판정) 0)
미충족 1건 — PRD-21 「nc 로도 찾는다」는 M-10 색인 재생성 1회로 묶어 R-B(WU-B7 뒤)로 이월
근거: dev-package/sessions/p3-extension-label-<YYYYMMDD>.md · p3-interval-period-<YYYYMMDD>.md
```

---

## 5. 완료 판정

- **WU-A5** — 상세가 `*.nc` 를 보이고 판별 문자열을 안 보인다 · `.hdf` 는 `*.hdf` · 확장자 없는 파일명은 판별값으로 떨어지고 화면이 안 깨진다 · backfill 이 기존 13행 파일명과 일치 · 검색이 종전대로 `netcdf` 로 잡히고 **안 깨진다**. ⚠ 「`nc` 로 잡힌다」는 **이월** — 라운드 종료 보고에 미충족 1건으로 적는다.
- **WU-A6** — 단위 `분` 선택 시 다섯 칸이 열리고 `value=10`·`unit='분'` 저장 · 화면 조립 `10분` · 숫자만이면 **400** · 값 비우면 등록 **성공** · granularity NULL 기존 행 표기가 종전과 같다 · 간격 있으면 `… ~ 03:00 (10분)`, 없으면 **빈 괄호 없음**.
- **게이트** — `schema-diff` · `migration-single-head` · `contract-lint` · `contract-breaking` · `service-tests-core-api` · `e2e-format-coverage` · `frontend-typecheck` · `frontend-test` 전건 green, 그리고 병합 직전 `./gates/run.sh all -j 1` green.
- **절차** — 대장 등재가 마이그레이션보다 **먼저** 있었음이 커밋 순서로 보인다 · 19차 승인이 `contracts/` 첫 수정보다 **먼저** 있었음이 보인다 · 〈N〉 이 병합 직전 실측값이다.

---

### 다음 파일

`dev-package/prd/rounds/R-A-2-server.md`(서버·계약) → `R-A-3-frontend.md` → `R-A-4-verify.md`.
⚠ **이 파일의 FE 꼬리는 `R-A-3` 의 WU-A3(상세 수정 골격)에 얹힌다.** DB·계약·서버 부분은 WU-A3 없이 시작할 수 있다.
