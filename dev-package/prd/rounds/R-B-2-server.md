# R-B-2 · 계약·서버 계층 — WU-B5 · WU-B7 · WU-B8

> 이 파일 하나로 세션을 시작한다. 라운드 = **R-B** · 계층 = **계약·서버(＋FE 꼬리)** · WU **3건**.
> R-A 이월 1건(PRD-21 「`nc` 로도 찾는다」＝ `M-10`)이 **WU-B7 뒤에서 닫힌다.**
> 의도 문서 = `dev-package/intent/2026-09-07-r-b.md` — **미승인 초안**(Ted 가 `## 확인` 을 채우기 전에는 정본이 아니다). 승인 전까지 이 파일이 판단 근거다.
> 출처 = `dev-package/prd/rounds/R-B.md` §6(쪼개기 지침). 형판 = `dev-package/prd/rounds/R-A-1-db.md`.

---

## 0. 읽기 규칙 — 이 파일이 유일한 부트스트랩

> ⛔ **아래 4개를 통째로 열지 않는다.** 세션이 느려지는 원인이 이것이다.
> `dev-package/03-HANDOFF.md`(약 127 KB) · `dev-package/PLAN-SoT.md`(1.17 MB) · `dev-package/work-items.yaml`(513 KB) · `dev-package/WORK-UNITS.md`(138 KB)

- **허용된 접근은 아래 세 줄뿐이다.**
  1. 결정 번호 최대값 — `bash dev-package/prd/tools/max-decision.sh`
  2. 대장에서 항목 하나 — `grep -n -A14 '^  - id: WU-B5' dev-package/work-items.yaml`
  3. 게이트 이름 확인 — `sed -n '12,30p' gates/run.sh` (`ALL_GATES` 배열)
- `03-HANDOFF.md` · `CLAUDE.md` · `RESTART.md` 는 **머리 부분만** 읽는다. 본문 통독 금지.
- 요구사항 정본은 이 파일과 `dev-package/prd/PRD-260905-적용전기획.md` 다. 이 파일에 옮겨 적힌 축자 문면이 우선이고, 더 필요하면 PRD 사본에서 **해당 `#### PRD-xx` 절만** 읽는다.
- **코드 파일은 고칠 때만 연다.** 현황 정찰·grep 스윕·다수 파일 읽기는 **서브에이전트에 위임**하고 결론만 회수한다.
- 이 파일의 `path:line` 은 **integration/r-b HEAD `ccd9372` 실측값**이다. `R-B.md` 에 적힌 옛 라인번호를 옮겨 쓰지 않는다 — 필요하면 `grep -n` 으로 다시 잰다.
- 못 읽으면 `[미상]` 이고 실패다. 지어내지 않는다.

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
- 미결-17 ⓐ — pdf 항목 8 잘린 1행은 원문 요청 중. **회신 대기가 착수를 막지 않는다.** ⛔ **추정 전사를 하지 않는다**
- 미결-18 ⓐ — 기간은 시각값 저장 유지, 화면만 구조화 (R-A 에서 닫힘)
- ⭑ **미결-10 = 개발 실측** — R-A 의 WU-A11 판정표가 WU-B11(R-B-4) 의 범위다. 미결-8 = 해소(값 표가 pdf 원문).

---

## 2. 범위 — 이 파일의 WU 3건

### WU-B5 · Lv 연결 규칙 (PRD-07 · 08 · 09 · 10) — 계층 계약·서버·FE · 크기 L · 레인 `p3-lv-rules`

- **의존**: **WU-B1**(사람 Lv 열 `processing_level_user_set` 이 서야 기준값이 생긴다) · **WU-B3**(등록 ③ 화면 골격). 미결 의존 없음(미결-2 ⓐ · 7 ⓐ · 14 ⓐ 확정).
- **현재 코드**
  - 파생 계산 = `services/core-api/src/colab_core/domains/d3_catalog.py:970` `processing_level(summary)` — 부모가 없으면 `0` 을 돌려준다.
  - 계보 쓰기 경로 = `services/core-api/src/colab_core/app/routes/lineage.py:165`(`add_lineage_parent`) · `:205`(`remove_lineage_parent`) · `:221`(`confirm_lineage`).
  - FE 안내 문면(종전 자동 보정) = `frontend/src/components/lineage/LineageStep.tsx:490-495` — 축자 「가공 단계는 이어 붙인 앞선 데이터에서 **자동으로 정해져요.**」 · `:17` 축자 「**가공 단계 Lv 를 화면이 계산하지 않는다.** 파생값이고 core 가 계산한다(`PLAN-SoT §9-⑳`)」. **이 두 자리가 이번에 반전된다**(`〈194〉` 반전).
- **요구 문면 축자 (PRD-07 rev1)** — 「실사례가 Lv0 > Lv1-A > Lv1-B > Lv2 로 간다. 같은 단계끼리 가공하는 일이 있어 부모+1 로 강제하면 담기지 않는다. 규칙은 하나다 — 부모 Lv ≤ 자기 Lv. 기준은 분류에서 고른 자기 Lv 다.」
- **요구 문면 축자 (PRD-08 rev1)** — 「자기 Lv 이하만 필터에 뜨고, 더 높은 후보는 흐리게 + 이유를 적어 고를 수 없다. **숨기지는 않는다.** 없는 것과 못 고르는 것은 다르다.」
- **요구 문면 축자 (PRD-09 rev1)** — 「연결한 뒤 자기 Lv 를 낮추면 연결을 지우지 않고 그 항목에 `확인 필요` 를 붙이고 데이터셋 만들기를 막는다. 사람이 한 연결을 시스템이 되돌리지 않는다.」
- **변경 — 계약**: 부모 후보 검색에 `processingLevel` 질의 파라미터. `DatasetBasicInfo`·`DatasetRow` 에 `processingLevelDerived`·`processingLevelMismatch` 두 열쇠(nullable) 추가.
- **변경 — 서버**: `createDataset`·계보 확정 경로에서 `부모 Lv ≤ 자기 Lv` 검증, 위반이면 **400** 이고 문면이 위반 항목을 열거한다. 응답에 사람 값·파생값·불일치 플래그를 **셋 다** 싣는다(표시용 `processingLevel` = 사람 값 우선). ⛔ **서버가 초과 후보를 지우지 않는다** — 전부 내려보내고 화면이 상태로 가른다.
- **변경 — 필터 축**: 카탈로그 질의 파라미터 `processingLevel` 은 **사람이 고른 값**(`processing_level_user_set`)을 거른다. 사람 값이 NULL 인 행만 파생값으로 대신 걸린다. ⛔ `processingLevelDerived` 로 거르는 질의 파라미터를 만들지 않는다.
- **변경 — 프론트**: 연결 단계 상단 안내 축자 = `지금 이 데이터는 Lv{n} · Lv0~Lv{n} 가공 전 데이터만 연결할 수 있어요. 분류에서 바꾸기`. 찾기 모달에 가공 단계 셀렉트 ＋ 초과 행 `is-over` 상태. 사유 축자 = `이 데이터(Lv{n})보다 높은 단계예요. 연결을 지우거나 분류에서 가공 단계를 올려 주세요.` 사후 충돌은 `chip chip--warning` `확인 필요` ＋ `데이터셋 만들기` 비활성. 불일치 안내 축자 = `고른 가공 단계는 Lv{사람}이고, 연결한 데이터로 계산하면 Lv{파생}이에요. 그대로 두어도 등록돼요.`
- **기존 데이터 처리**: 기존 엣지는 검사하지 않는다(사람 Lv 가 NULL 이라 기준값이 없다). 사람이 그 데이터셋의 Lv 를 처음 고르는 순간부터 PRD-09 규칙이 적용된다. 사람 값 NULL 행은 `processingLevelMismatch=false`.
- **수용 기준**
  - Given 자기 Lv=Lv2, When 부모 Lv2 연결, Then 허용된다(같은 레벨).
  - Given 자기 Lv=Lv1, When 부모 Lv2 연결 시도, Then **400** 이고 화면이 그 후보를 고를 수 없게 막는다.
  - Given 자기 Lv=Lv0, When 연결 단계 진입, Then 안내가 「Lv0 가공 전 데이터만 연결할 수 있어요」이고 부모 후보가 Lv0 만 뜬다.
  - Given 자기 Lv=Lv1 이고 후보에 Lv2, When 찾기 모달 열기, Then Lv2 행이 **보이고** 선택 불가이며 사유 문구가 읽힌다 · 대비 **4.5:1 이상**.
  - Given Lv2 로 Lv2 부모 연결 뒤 자기 Lv 를 Lv1 로 내림, Then 연결이 **남아 있고** `확인 필요` 가 붙고 버튼이 안 눌린다. 되돌리면 칩이 사라지고 버튼이 산다. 같은 상태에서 API 직접 호출 시 **400**.
  - Given 사람 Lv1 · 파생 Lv2, When 상세 조회, Then `processingLevel=Lv1`·`processingLevelDerived=Lv2`·`mismatch=true` 이고 위 안내가 뜬다. **저장은 성공한다**(차단하지 않는다).
- ⛔ **자기 Lv 를 시스템이 바꾸거나 잠그지 않는다.** ⛔ 화면 차단이 유일한 방어선이 되지 않게 한다 — 서버 400 이 최종 방어선이다.

### WU-B7 · 목록 필터·상세 3행 (PRD-05 · 06) — 계층 계약·서버·FE · 크기 M · 레인 `p3-axis-filters`

- **의존**: **WU-B1**(세 축 컬럼·CHECK).
- **현재 코드**
  - 질의 파라미터 `topic` = `contracts/seams/fe-core.yaml:2466` (`name: topic`).
  - 서버 필터 = `services/core-api/src/colab_core/app/routes/catalog.py:128`(`_apply_filters`) · `:135-136`(`topic` 절) · `:167`·`:456`(`topic: list[str] | None = Query(default=None)`) · `:50`(`"주제": lambda row: row["topic"] or ""`) · `:100`(`"topic": core.topic`).
  - 상세 격자 = `frontend/src/components/detail/BasicInfoGrid.tsx` — `topic` 문자열 매치 **0건** `[미상]`(행 위치 불명 · 고칠 때 `grep -n` 으로 다시 잰다).
  - 계약 `DatasetBasicInfo` 블록 = `contracts/seams/fe-core.yaml:3795` (`processingLevel` `:3914` · `accessState` `:3917`).
- **요구 문면 축자 (PRD-05)** — 원천 `P-4` 「이 기준대로 넣고 필터를 만드는게 좋을 것 같습니다」 · `R-04` 「목록 필터가 이 세 축을 그대로 받는다」.
- **변경 — 계약**: 질의 파라미터 `category` · `dataType` · `processingLevel` 3종. `topic` 파라미터는 **한 릴리즈 동안 유지**하되 description 에 「이관 중 · 신규 사용 금지」를 적는다. `DatasetBasicInfo` required 에 `category`·`dataType` 추가.
- **변경 — 서버**: `catalog.py` 목록 질의에 3축 `WHERE` 절과 패싯 집계를 더한다. 세 축은 **AND**.
- **변경 — 프론트**: 카탈로그 필터 바를 3축으로. 각 축 첫 항목 축자 = `분류 전체` / `유형 전체` / `가공 단계 전체`. 상세 기본 정보에 `분류`·`유형`·`가공 단계` 3행을 이 순서로. 홈 데이터 맵이 주제 축을 넘기던 자리를 분류 축으로 바꾼다.
- **기존 데이터 처리**: 값이 NULL 인 행은 어느 축 필터에도 걸리지 않는다. **「미지정」 필터 항목을 각 축에 하나씩 둔다** — 재선택이 필요한 행을 사람이 찾아낼 유일한 경로다. 상세는 NULL 이면 「미지정」 ＋ 수정 진입 유도.
- **수용 기준**
  - Given `category=수문 인자` 질의, Then 그 분류의 데이터셋만 나온다.
  - Given 세 축 동시 지정, Then **AND** 로 걸린다.
  - Given 유형 NULL 행 존재, When `dataType=미지정` 필터, Then 그 행이 나온다.
  - Given 상세 조회, Then 세 행이 이 순서로 있고 각 값이 목록 필터 값과 **문자열이 같다**.

### `M-10` — 이 라운드에서 한 번 (R-A 이월 · PRD-21)

- **자리** — R-B.md §6 축자 「B7 뒤에서 R-A 이월분(`nc` 검색)이 닫힌다」. ⭑ `M-10` 자체는 **WU-B2 뒤**(변수 행 표가 서야 트리거 대상이 있다)이고, **`nc` 검색의 닫힘 판정이 WU-B7 뒤**다. ⛔ **라운드에서 두 번 돌리지 않는다.**
- **이월 사유 축자 (`R-A-1-db.md` WU-A5 마지막 ⚠)** — 「**「`nc` 로도 찾는다」는 이 WU 의 완료 판정에서 뺀다.** 색인 재정의(부록 B `M-10`)는 `category` 이관·변수명 미러와 한 마이그레이션으로 묶여 **R-B 에서 한 번만** 돈다(생성 컬럼 재계산 ＋ GIN 재생성을 두 번 하지 않는다). **R-A 는 컬럼만 세우고 색인식을 손대지 않으며, 검색은 종전대로 `format` 으로 잡힌다**(`netcdf` 는 되고 `nc` 는 아직 안 된다).」
- **현재 색인식 실측** — `db/platform/schema.sql:426-432` `search_vector tsvector GENERATED ALWAYS AS (…) STORED`: **B 가중치** = `format`(`:413`) ＋ `d3_search_join(variables)`(`:414`) · **C 가중치** = `crs`·`grid`·`bundle_file_name`. `file_extension`(`:445`)은 **아직 색인식에 없다** ⟹ `nc` 로 안 잡히는 이유가 여기다.
- ⚠ **`topic`→`category` 색인 재정의 문면이 실측과 어긋난다.** `topic` 컬럼은 `d3_dataset_autometa` 에 **없고**(`grep` 결과 0건) `d3_dataset_description:370` 에만 있으며, `search_vector` 는 그 컬럼을 물지 않는다. **미해결 질문 — 「`topic`→`category` 이관」이 색인식에서 무엇을 가리키는가.** ⛔ **지어내서 봉합하지 않는다.** Ted/PRD 확인 전까지 `[미상]`.
- **`M-10` 이 실제로 해야 하는 것 (실측 기준 3건)** — ⑴ 색인식에 `file_extension` 을 넣는다 ⑵ 색인식에 `category`(WU-B1 신설)를 넣는다 ⑶ `d3_dataset_variable` → `autometa.variables` **미러 트리거**를 세운다.
- ⚠ **축자 (`R-B.md` §2 마이그레이션 블록)** — 「「생성 컬럼이라 자동 재계산」은 **변수명 경로에는 거짓**이다 — 생성 컬럼은 같은 행의 열만 참조하므로 새 표를 색인식에 넣을 수 없다.」
- **수용 기준** — `nc` 검색으로 `*.nc` 데이터셋이 잡힌다 · `netcdf` 검색이 **종전과 같이** 잡힌다(회귀) · 변수명 검색이 종전과 같이 잡힌다 · 생성 컬럼 재계산·GIN 재생성이 **1회**다(`migration-single-head` green).

### WU-B8 · 계보 상태 판정식 ＋ 「기록 없음」 체크박스 (PRD-27) — 계층 계약·서버·FE · 크기 M · 레인 `p3-lineage-unknown`

- **의존**: **WU-B1**(사람 Lv 열) · **WU-B3**(등록 ③ 화면). **스키마 변경 0.**
- **현재 코드**
  - 판정 함수 = `services/core-api/src/colab_core/domains/d3_catalog.py:988` `def lineage_state(core: DatasetCore, summary: LineageSummary | None) -> str:`
  - 파생 Lv = 같은 파일 `:970` `processing_level(summary)` — 부모 0이면 `0`.
  - 자동 `mark_unknown` 호출부 = `services/core-api/src/colab_core/app/routes/ingestion.py:614` `d4_lineage.mark_unknown(db, dataset_id=dataset_id, actor_id=subject.account_id)`.
  - 도메인 함수 = `services/core-api/src/colab_core/domains/d4_lineage.py:199`(`mark_unknown`) · `:204`(`is_unknown`).
  - 서버 수용 목록 = `services/core-api/src/colab_core/app/routes/ingestion.py:382`(`_ALLOWED_CREATE_FIELDS` 선언) · `:477`(`unknown = set(body) - _ALLOWED_CREATE_FIELDS`).
  - 4값 enum = `contracts/schemas/common.json:157` `"enum": ["확정", "확인 필요", "기록 없음", "원천"]`.
  - 저장 자리 = `db/platform/schema.sql:688` `CREATE TABLE d4_lineage_unknown (` — **이미 있다**.
  - 계약 `lineageUnknown` 키 = `contracts/seams/fe-core.yaml` 에 **0건** — 이 WU 가 신설한다.

**개정 판정식 (PRD-27 6항 판정식 — 축자 전문, load-bearing)**

`lineage_state()` 를 아래로 대체한다 · 위에서부터 먼저 맞는 항이 이긴다

| # | 조건 | 상태 |
|---|---|---|
| 1 | 부모 ≥1 ∧ (확정일 없음 ∨ 마지막 수정 > 확정일) | `확인 필요` |
| 2 | 부모 ≥1 ∧ 확정일이 최신 | `확정` |
| 3 | 부모 0 ∧ **`d4_lineage_unknown` 에 행이 있다**(사람이 선언했다) | `기록 없음` |
| 4 | 부모 0 ∧ **사람이 고른 가공 단계 = `Lv0`** | `원천` |
| 5 | 부모 0 ∧ `source_label` 있음 | `원천` |
| 6 | 그 밖 (부모 0 ∧ 선언 없음 ∧ 사람 Lv 가 `Lv1` 이상) | `확인 필요` |

- **⑷ 가 Lv0 제외 조항이다.** Lv0 은 부모가 없는 것이 정상이라 확인을 요구할 대상이 아니다. 이 조항이 없으면 **Lv0 전부가 `확인 필요` 로 뜬다.**
- ⚠ **⑷ 는 사람이 고른 Lv(`processing_level_user_set`)만 본다 — 파생 Lv 를 쓰면 안 된다.** 파생 계산은 부모가 없으면 `0` 을 돌려주므로, 파생값으로 판정하면 **부모 0건 행이 전부 Lv0 이 되어 조항 자체가 무의미해진다.** 사람 Lv 가 NULL 인 행은 ⑷ 를 지나 ⑸·⑹ 으로 간다.
- **⑹ 이 이 요구가 새로 만드는 값이다** — 「아직 안 골랐다」가 처음으로 `기록 없음` 과 갈린다.

- **변경 — 계약**: `DatasetCreate` 에 `lineageUnknown: boolean` 을 더해 **선언과 미선택을 가른다**(현재 0건 → 신설).
- **변경 — 서버**: ⑴ `lineageUnknown=true` 면 `d4_lineage_unknown` 을 붙인다 ⑵ `false` 이고 부모 0건이면 **아무것도 붙이지 않는다** — 자동 `mark_unknown` 호출(`ingestion.py:614`)을 **걷는다**. 그러면 판정 ⑹ 이 `확인 필요` 를 낸다. `_ALLOWED_CREATE_FIELDS`(`:382`)에 `lineageUnknown` 을 **같은 회차에** 더한다. 부모 1건 ∧ `lineageUnknown=true` 를 API 로 직접 보내면 **400**.
- **변경 — 프론트**: ③ 연결 단계에 체크박스. 라벨 축자 = `가공 전 데이터를 못 찾았어요 — 기록 없이 등록할게요`. 확정 부모 ≥1 이면 **비활성 ＋ 사유 한 줄**(숨기지 않고, 연결을 지우지도 않는다). 가공 단계가 `Lv0` 이면 체크박스를 **보이지 않는다**(판정 ⑷ 가 이미 `원천` 으로 가른다).
- **변경 — 홈 대시보드 모수 불일치 (실측)**: `frontend/src/components/dashboard/SummaryTiles.tsx:52` `LINEAGE_TODO_PATH` 가 `lineageState: '확인 필요'` **한 값**으로 링크를 만들고, `frontend/src/components/dashboard/dashboardSource.ts:20` 은 `const UNSETTLED = ['확인 필요', '기록 없음']` **두 값**으로 센다. 타일 숫자와 그 링크가 여는 목록의 모수가 갈린다. **이 WU 가 둘을 한 값으로 맞춘다.**
- **기존 데이터 처리**: 기존 `기록 없음` 행은 그대로 둔다 — 자동으로 붙은 것이라 어느 쪽이었는지 사후에 알 방법이 없다. 종전 규칙에서는 부모 0건 행에 `d4_lineage_unknown` 행이 **빠짐없이** 붙어 있으므로 개정 판정식에서도 ⑶ 을 타 **종전과 같이 `기록 없음`**이다(화면 값이 바뀌는 기존 행 0). **이 사실을 마이그레이션 전에 실측한다** — `부모 0건 ∧ d4_lineage_unknown 행 없음` 건수를 세고, 0 이 아니면 그 행들이 `확인 필요` 로 넘어감을 보고한다.
- **수용 기준**
  - 부모 0 · 체크 안 함 · 사람 Lv=`Lv1` ⟹ `확인 필요` / 부모 0 · 체크함 ⟹ `기록 없음` / 부모 0 · 체크 안 함 · 사람 Lv=`Lv0` ⟹ **`원천`**(Lv0 제외 조항).
  - 사람 Lv NULL ∧ `d4_lineage_unknown` 행 있음 ⟹ 종전과 같이 `기록 없음`(회귀).
  - **부모 ≥1 경로의 판정이 종전과 같다** — 부모가 있는 경로는 이 개정이 건드리지 않았다(회귀 증명).
  - 부모 1건 확정 ⟹ 체크박스 비활성 ＋ 사유가 읽히고 **칸이 사라지지 않는다**.
  - 라벨이 축자와 같고 **종전 문면 `못 찾은 것이 있어요 (기록 없음)` 문자열이 코드에 남아 있지 않다.**
  - 부모 1건 ＋ `lineageUnknown=true` 직접 전송 ⟹ **400**.
  - 홈 타일 숫자와 그 링크가 여는 목록의 건수가 **같다**.

### 이관 항목 — R-A′ 에서 이 파일로 넘어온 서버 3건 (⭑ **Ted 판정 대기** · 착수 차단 아님)

출처 = `dev-package/sessions/R-A2-ROUND-20260907.md` §5(A7R advisor). ⛔ **§5 완료 판정에 넣지 않는다.**
1. `frontend/src/components/project/projectSource.ts:50-51` — 서버 문면 우선 노출 통일. ⚠ `R-B.md`·R-A′ 노트가 적은 `projectSource.ts:53` 은 현재 트리에서 **`:50-51`** 이다(같은 이름 파일이 `frontend/src/components/upload/projectSource.ts` 에도 있으나 29행뿐 — 혼동 주의).
2. 프로젝트 이름 **UNIQUE 제약 마이그레이션 후보** — 현재는 응용 층 400 뿐(`services/core-api/src/colab_core/app/routes/project.py:157-158` `if d6_project.name_is_taken(db, name=name):`)이라 **동시 생성 경합에서 둘 다 통과한다.**
3. `PATCH /projects` **409 계약 미선언**.

---

## 3. 지켜야 하는 규약 — 명령으로

### ㉮ 워크트리 레인

- WU 하나에 레인 하나. 레인 이름 = `p3-lv-rules`(B5) · `p3-axis-filters`(B7) · `p3-lineage-unknown`(B8).
- 각 레인은 통합 브랜치에서 딴 자기 워크트리에서 돈다. 병합은 **ff-merge**, 병합 뒤 워크트리·로컬/원격 브랜치를 정리한다.
- 한 레인 = 한 WU. 세 WU 를 한 브랜치에 섞지 않는다.

### ㉯ 착수 전 — `work-items.yaml` **등재 확인**

⭑ **등재는 이미 끝났다** — WU-B5(`work-items.yaml:2801`) · WU-B7(`:2827`) · WU-B8(`:2840`) 을 포함한 R-B 10건이 실재한다. 이 절은 **등재 방법이 아니라 등재 확인**으로 쓴다.

```bash
grep -n -A14 '^  - id: WU-B5' dev-package/work-items.yaml
grep -n -A14 '^  - id: WU-B7' dev-package/work-items.yaml
grep -n -A14 '^  - id: WU-B8' dev-package/work-items.yaml
```
확인 항목 = `status` · `entry_conditions`(B8 에 20차 승인이 있는가) · `depends_on`(B5·B7·B8 이 B1 을 잇는가) · `completion_def` 가 §5 와 어긋나지 않는가. **어긋나면 고치지 말고 보고한다.** 완료 시 `status: done` ＋ `evidence` 만 갱신한다.

### ㉰ 계약 동결 해제 — **20차 · 등급 ㉯ · Ted 승인 필수**

근거 문서 = `dev-package/sessions/X2-FREEZE-PROTOCOL.md` §5. **R-A 가 19차를 썼으므로 이 라운드는 20차**다. 회차 번호는 `PLAN-SoT §9` 가 **유일한 발급처**다.
승인 요청 패키지 = `dev-package/sessions/R-B-C20-REQUEST-20260907.md` — **Ted 미승인**. **이 파일에서 20차를 필요로 하는 것은 WU-B8**(`lineageUnknown` 신설)이고, WU-B5(`processingLevelDerived`·`processingLevelMismatch`·후보 검색 파라미터)·WU-B7(3축 질의 파라미터 ＋ `DatasetBasicInfo` required 확장)이 같은 20차에 함께 실린다.
⛔ **§5-㉰-6(묶음 쪼개기) 금지** — WU 별로 쪼개 각 조각을 ㉮ 로 통과시키지 않는다. **목적 단위로 판정한다.**

```bash
# ⑴ 파괴 판정을 실행 출력으로 낸다 (주장하지 않는다 — §5-㉱-1)
./gates/run.sh contract-breaking
# ⑵ 소비자 수를 grep 출력으로 낸다 (§5-㉱-3) — 실측 163 건 (HEAD ccd9372)
grep -rn 'variables\|accessState\|lineageUnknown\|category' contracts/ services/ frontend/src | wc -l
# ⑶ 이 파일이 여는 마이그레이션 = M-10 1건(색인 재정의 ＋ 미러 트리거) · head 1개
# ⑷ 되돌림 경로를 적는다
```
⛔ **승인 없이 `contracts/` 를 고치지 않는다.**
⛔ **§5-㉰-4(집행 없는 신설) 금지** — 계약만 열고 서버 수용 목록(`_ALLOWED_CREATE_FIELDS` `ingestion.py:382`)을 다음 회차로 미루지 않는다. **계약 · 서버 · 화면 · 시험을 한 회차에 세운다.**

### ㉱ 결정 번호 〈N〉 — 예약하지 않는다

```bash
git fetch origin main && bash dev-package/prd/tools/max-decision.sh   # 병합 직전에 다시 잰다
```
2026-09-07 실측 최대 = **〈372〉**(참고값). **병합 직전 `origin/main` 최대 ＋ 1** 이 이번 번호다.
`PLAN-SoT §9` 표에 아래 한 행을 **병합 직전에** 덧붙인다 — 필드 8개(X2 §5-㉲). `〈194〉`·`〈276〉` 반전은 **R-B-1(WU-B1) 이 적는다** — 이 파일이 중복해서 적지 않는다.

```
| 〈N〉 | **R-B-2 계약·서버 계층 — 20차 · 3축 질의 파라미터 ＋ Lv 연결 규칙 ＋ `lineageUnknown`** | **집행 (2026-MM-DD · 워크트리 `<레인>` · 병합 `<sha>`).** ①회차 = **20차**(직전 19차 = R-A) ②값 = `category`·`dataType`·`processingLevel` 질의 파라미터 · `processingLevelDerived`·`processingLevelMismatch` · `lineageUnknown` ③근거 = PRD-05·06·07·08·09·10·21·27 (`dev-package/prd/PRD-260905-적용전기획.md`) ④가·파 판정 = **파괴** · `contract-breaking` 출력 = `<축자>` ⑤소비자 = `<n>` 건 · 측정법 = `grep -rn 'variables\|accessState\|lineageUnknown\|category' contracts/ services/ frontend/src` ⑥마이그레이션 = **M-10 1건 · head 1개** ⑦승인 = Ted · `<일자>` ⑧이번에 세지 않은 축 = `topic`→`category` 색인 이관의 실체 `[미상]` · 이관 항목 3건(Ted 판정 대기) |
```
⛔ **HANDOFF 에는 값을 적지 않는다**(`CLAUDE.md §6-3`).

### ㉲ 게이트 — 작업 중엔 단독, 병합 전엔 전건

```bash
./gates/run.sh contract-lint                # B5 · B7 · B8
./gates/run.sh contract-breaking            # 같음
./gates/run.sh service-tests-core-api       # B5 · B7 · B8
./gates/run.sh ai-no-lineage-write          # B5
./gates/run.sh e2e-format-coverage          # M-10 (`nc` 검색)
./gates/run.sh migration-single-head        # M-10
./gates/run.sh schema-diff                  # M-10 (색인식 변경)
./gates/run.sh frontend-typecheck
./gates/run.sh frontend-test
# 병합 직전 한 번
./gates/run.sh all -j 1
```
⛔ **게이트를 끄거나 검사 대상을 줄이지 않는다.** **green 으로 시작한 테스트는 오라클이 아니다** — 실패 테스트 red 를 먼저 확인한다.

### ㉳ 커밋 문면

```
R-B-2 <WU-키> — <한 줄 요지>

- <계약 / 서버 / 화면 / M-10 중 이 커밋이 움직인 것>
- 계약 동결 해제 20차 · 등급 ㉯ · Ted 승인 <일자> · PLAN-SoT §9 〈N〉 등재
- RED 선실측 → GREEN: <시험 파일>:<건수>
```

### ㉴ 금지

- ⛔ `main` 에 직접 push. ⛔ staging DB 직접 쓰기(변경은 마이그레이션 경유로만). ⛔ 원장 행 없이 마이그레이션.
- ⛔ `M-10` 을 두 번 돌리기(라운드에서 **한 번**). ⛔ `topic`·`variables`·`format` 컬럼 삭제.
- ⛔ 자기 Lv 를 시스템이 바꾸거나 잠그기. ⛔ 초과 부모 후보를 서버가 지우거나 숨기기.
- ⛔ 불일치(mismatch)로 저장을 차단하기 — **경고만**. ⛔ 유형↔가공 단계 조합 검증 신설.
- ⛔ `processingLevelDerived` 질의 파라미터 신설. ⛔ 자동 `mark_unknown` 을 남겨 둔 채 체크박스만 얹기.
- ⛔ `topic`→`category` 색인 문면의 어긋남을 **추정으로 봉합**하기 — `[미상]` 으로 보고한다.
- ⛔ 이관 항목 3건을 Ted 판정 없이 집행하기. ⛔ `40 COLAB-기획/` 문서 수정. ⛔ 문서·주석에 절대경로.
- ⛔ 이 세션이 `03-HANDOFF.md` 를 직접 고치기 — §4 의 5줄만 넘긴다.

---

## 4. 산출물과 근거

| 무엇 | 어디 |
|---|---|
| 계약 | `contracts/seams/fe-core.yaml` — 3축 질의 파라미터 · `DatasetBasicInfo`(`:3795`) required ＋ `processingLevelDerived`·`processingLevelMismatch` · `DatasetCreate`(`:3401`) `lineageUnknown` · `topic`(`:2466`) description 「이관 중 · 신규 사용 금지」 |
| 서버 | `services/core-api/.../routes/catalog.py`(`_apply_filters:128` · `:167`·`:456`) · `routes/lineage.py:165,205,221` · `routes/ingestion.py:382,477,614` · `domains/d3_catalog.py:988`(`lineage_state()`)·`:970`(`processing_level()`) · `domains/d4_lineage.py:199,204` |
| 마이그레이션 | `db/` — `M-10` 1건(색인식에 `file_extension`·`category` ＋ `d3_dataset_variable`→`autometa.variables` 미러 트리거) ＋ 원장 행. **스키마 표 신설 0**(WU-B8 은 변경 0) |
| 프론트 | 3축 필터 바 · 상세 3행(`detail/BasicInfoGrid.tsx`) · `lineage/LineageStep.tsx`(안내·찾기 모달·체크박스) · `dashboard/SummaryTiles.tsx:52` ↔ `dashboard/dashboardSource.ts:20` 모수 통일 |
| 세션 노트 | `dev-package/sessions/p3-lv-rules-<YYYYMMDD>.md` · `p3-axis-filters-<YYYYMMDD>.md` · `p3-lineage-unknown-<YYYYMMDD>.md` — **각 ≤ 60행** |
| 대장 | `dev-package/work-items.yaml:2801`·`:2827`·`:2840` — 등재 확인 후 완료 시 `status: done` ＋ `evidence` |
| 원장 | `PLAN-SoT §9` 한 행(㉱ 문안) — **병합 직전** |

**오케스트레이터에 넘기는 HANDOFF 갱신문 — 5줄 이하. 세션이 `03-HANDOFF.md` 를 직접 고치지 않는다.**

```
R-B-2(계약·서버) 완료 — WU-B5 · WU-B7 · WU-B8, 레인 p3-lv-rules · p3-axis-filters · p3-lineage-unknown, 병합 <sha1>·<sha2>·<sha3>
계약 동결 해제 20차 승인 <일자> · PLAN-SoT §9 〈N〉 등재 · M-10 1회(색인 재정의 ＋ 미러 트리거)
R-A 이월 1건 종결 — PRD-21 「nc 로도 찾는다」가 WU-B7 뒤 M-10 으로 닫혔다
게이트: ./gates/run.sh all -j 1 = green <n>/<n> (red(판정) 0) · 미해결 질문 1건 = topic→category 색인 이관의 실체 [미상]
근거: dev-package/sessions/p3-lv-rules-<YYYYMMDD>.md · p3-axis-filters-<YYYYMMDD>.md · p3-lineage-unknown-<YYYYMMDD>.md
```

---

## 5. 완료 판정

- **WU-B5** — 같은 레벨 부모 허용 · 초과 부모 **400** ＋ 화면 차단 · Lv0 안내와 후보가 Lv0 만 · 찾기 모달이 초과 후보를 **보이되 못 고르게** 하고 사유 대비 **4.5:1 이상** · 사후 충돌이 연결을 **지우지 않고** `확인 필요` ＋ 버튼 비활성 · 불일치는 **경고만**이고 저장이 성공한다 · 필터가 **사람 값**을 거른다.
- **WU-B7** — 3축이 **AND** · 각 축에 `미지정` 항목이 있어 재선택 대상을 찾을 수 있다 · 상세 3행이 이 순서이고 값 문자열이 목록 필터와 같다 · `topic` 파라미터가 살아 있고 description 에 「이관 중 · 신규 사용 금지」가 있다.
- **`M-10`(R-A 이월 종결)** — `nc` 로 잡힌다 · `netcdf` 가 **종전과 같이** 잡힌다 · 변수명 검색이 **종전과 같이** 잡힌다 · 색인 재생성이 **1회**. ⭑ **라운드 종료 보고에 「R-A 이월 1건(PRD-21 `nc` 검색) 닫힘」을 명시한다.**
- **WU-B8** — 6항 판정식이 `lineage_state()` 를 대체한다 · 자동 `mark_unknown`(`ingestion.py:614`)이 걷혔다 · `lineageUnknown` 이 계약·`_ALLOWED_CREATE_FIELDS` 양쪽에 **같은 회차에** 섰다 · 부모 0/체크/Lv0 세 갈래가 `확인 필요`·`기록 없음`·`원천` 으로 갈린다 · **부모 ≥1 경로 회귀 green** · 라벨 축자 일치 ＋ 종전 문면 문자열 **0건** · 부모 1건 ＋ `true` 전송 **400** · 홈 타일 숫자와 링크 목록 건수가 **같다** · **스키마 변경 0**.
- **게이트** — ㉲ 목록이 WU 마다 green, 병합 직전 `./gates/run.sh all -j 1` green.
- **절차** — 20차 승인이 `contracts/` 첫 수정보다 **먼저** 있었음이 커밋 순서로 보인다 · 〈N〉 이 병합 직전 실측값이다 · 등재 확인(㉯)이 착수 커밋 앞에 있다.
- ⛔ **이관 항목 3건(§2 말미)은 이 판정에 넣지 않는다** — Ted 판정 대기.

---

### 다음 파일

`dev-package/prd/rounds/R-B-3-frontend.md`(B3 · B10) → `R-B-4-verify.md`(B11 ＋ R-B 종료 검증).
⚠ **이 파일의 FE 꼬리는 `R-B-3` 의 WU-B3(등록 3단계 재구성)에 얹힌다.** 계약·서버 부분은 WU-B1 만 서 있으면 시작할 수 있다.
