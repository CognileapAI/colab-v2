# LV-1 계약 동결 해제 ㉯ — 변경 범위 보고 (판정용)

작성 2026-09-02 · 기준 `main` `024f881` · 조사 전용(파일 무접촉 · 게이트 미실행 — 다른 두 레인의 pg 슬롯 보호)
권위 = `dev-package/PLAN-SoT.md §9` ＋ `dev-package/work-items.yaml`. 산문(`03-HANDOFF.md`·`WORK-UNITS.md`)은 열등 순위.

---

## 1. LV-1 이 무엇인가 — 원장 대조

- 항목 = `work-items.yaml:1386` `LV-1` 「사람이 가공 단계를 직접 고르는 경로 제거 (레벨은 언제나 계보에서 나온다)」 · `status: open` · `stage: stage1` · `owner: D3 / core-api ＋ contracts ＋ db` · `depends_on: [P2]`.
- **완료 정의는 확정 정본이다 — 초안이 아니다.** 필드 이름이 `completion_def`(`work-items.yaml:1393`)이고, `J-1` 처럼 `completion_def_draft` 가 아니다(대조 = `PARALLEL-LAUNCH-MAP.md:44` 「`J-1` `completion_def_draft`(`:939`)」). ⟹ 이 사유로 인한 결격 없음.
- 완료 정의 축자(`work-items.yaml:1393-1411`) 요지 — ⓐ 사람이 고른 값을 담는 경로 전부 제거(`schema.sql` 열·`CHECK` · `fe-core.yaml` `DatasetUpdate.processingLevel` · `routes/catalog.py`·`domains/d3_catalog.py` 대응표 · `processing_level` 의 `user_set` 분기 · 그 시험) ⓑ 쌓인 값 재계수 후 목록 고정 ⓒ down 마이그레이션 ＋ `schema-diff` 두 체인 ⓓ 게이트 4종 판정을 돌린 결과로 적기 ⓔ **화면 변경 없음**(`RegisterArea.tsx` 읽기 전용 칸 그대로).
- 원장 판정 근거 = `PLAN-SoT.md:541` 〈194〉 「레벨은 언제나 계보에서 나온다 — 사람이 직접 정하지 못한다 … 예외 없음」(2026-08-29 Ted). 그 회차는 **문서 등재 전용**이었고 코드 제거는 LV-1 로 남았다.
- 데이터 이행 대상 = 0건(`work-items.yaml:1412` evidence · staging `d3_dataset` 12행 중 `processing_level_user_set` 비-NULL **0건** · `sessions/LINEAGE-LEVEL.md §9.1`). ⓑ 는 착수 시점 재계수 조건이므로 **[미확인]** 로 다시 세야 한다(2026-08-29 값).

## 2. 등급 ㉯ 가 무엇인가 · 선례

- 규칙 정본 = `dev-package/sessions/X2-FREEZE-PROTOCOL.md §5`(확정 = Ted 2026-08-27 · `PLAN-SoT §9 〈163〉` · `X2-FREEZE-PROTOCOL.md:5`).
- ㉮ 자동 허용 5조건(`:107-114`) — ① `contract-breaking` ERR 0 ② **마이그레이션 0 · 스키마 변경 0** ③ 소비자 0건 출력 증명 ④ 설계 판단 0건 ⑤ 정본 무개정. 하나라도 미충족이면 ㉯.
- ㉯ 축자(`:118-127`) — 「**마이그레이션 ≥ 1** 또는 스키마 변경 — 되돌리기 어려운 것은 언제나 사람이 연다(`〈69〉`)」 · 「파괴적 변경(ERR ≥ 1) — 소비자 0이어도 예외 없다」 · 승인자 = **Ted**.
- ㉰ 금지(`:129-136`) 중 LV-1 저촉 여부 = **없음.** 2항(소비자 ≥ 1 표면의 무예고 파괴)은 쓰기 소비자 0건이라 해당 안 되고, 4항(집행 없는 신설)·6항(묶음 쪼개기)도 해당 없음.
- 증거 요구 ㉱ 7항(`:140-150`) · 기록 ㉲ 8필드(`:152`) — 회차마다 게이트 **출력째** 남기고 `PLAN-SoT §9` 한 항목으로 등재. 회차 번호 발급처는 §9 뿐.
- 등급 확정 = `work-items.yaml:1391` `entry_conditions` — 2026-08-31 Ted RULING ㉝ · `PLAN-SoT §9 〈258〉`(`PLAN-SoT.md:609`). **실측으로 매겼다** — `contract-breaking` 을 `COLAB_CONTRACTS_REV` 로 긁힘용 사본에 물려 `DatasetUpdate.processingLevel` 뺀 판 실행 → `1 changes: 0 error, 1 warning, 0 info` · `[request-property-removed]` **WARN 1 · ERR 0 · exit 0(green)**.
- **선례 — ERR 0 인데 ㉯ 인 회차가 이미 셋.**
  - 10차 `〈205〉`(`X2-FREEZE-PROTOCOL.md:39` · `PLAN-SoT.md:556`) — 계보 출처 레이블 영어 3값 통일 · 마이그레이션 1 · 스키마 변경 · 소비자 ≥ 1 · ERR 0. 축자 「**등급은 게이트 수가 아니라 성질로 정한다**」(`:40`).
  - 11차 `〈231〉`(`:35` · `PLAN-SoT.md:582`) — `createPreviewScreenshot` op 신설 · ERR 0 · op 총계 53→54.
  - 12차 `〈253〉`(`:29` · `PLAN-SoT.md:604`) — 이벤트 계약 3종 신설 ＋ 마이그레이션 1 · ERR 0 · WARN 6.
- ⟹ **LV-1 은 13차 해제가 된다**(직전 12차 `〈253〉`). `X2-FREEZE-PROTOCOL.md:33` 축자 「스키마를 여는 회차는 이제 예외가 아니라 **㉯ 가 받는 정상 경로**다」.

## 3. 구체적 변경 범위 — 파일별

**계약 (1파일 1자리)**
| 파일:행 | 변경 | 사유 |
|---|---|---|
| `contracts/seams/fe-core.yaml:2692-2699` | `DatasetUpdate.processingLevel` 속성 **삭제** (스키마 머리 = `:2661` `DatasetUpdate:`) | 완료 정의 ⓐ 가 지정한 유일한 계약 자리. 축자 「`null` 을 보내면 사람의 선택을 지우고 계보에서 파생하는 상태로 되돌린다」 |

**계약에서 손대지 않는 자리 (오판 방지 — 전부 존치)**
- `fe-core.yaml:2623` = `DatasetCreate.processingLevel`(스키마 머리 `:2580`). 완료 정의 ⓐ 는 `DatasetUpdate` 만 지목한다. ⚠ **판정 필요** — 〈194〉 「예외 없음」과 문면이 어긋난다. 이 보고는 정의대로 존치로 적고 **[미확인]** 로 남긴다.
- `fe-core.yaml:1971` `FilterProcessingLevel`(질의 조건) · `:2751`·`:2993`·`:3100`·`:3237` 응답 필드 — 전부 **파생값 읽기**다. 계약 축자 「파생값이지만 조건으로는 걸 수 있다 — **쓰기 바디에는 없다**」(`:1975`).

**생성물 (1벌만)**
| 파일 | 사유 |
|---|---|
| `frontend/src/generated/fe-core.ts` | `contracts/codegen/manifest.toml:18-21` 등기 · `frontend/package.json:5` `openapi-typescript … -o src/generated/fe-core.ts`. 재생성 필수 |
- ⚠ manifest 의 나머지 3벌(`storage_layout.py` × core-api·pipeline-worker·viz-render · `manifest.toml:32-48`)은 **`contracts/storage/layout.json` 파생**이라 무관하다. `PARALLEL-LAUNCH-MAP.md:103` 의 「생성물 3벌」은 계약 파일 공유 레인 일반론이고, LV-1 이 흔드는 것은 1벌이다.

**서비스 (2파일 · `processing_level_user_set` 4파일 18곳 중)**
| 파일:행 | 변경 | 사유 |
|---|---|---|
| `services/core-api/src/colab_core/app/routes/catalog.py:416` | `_UPDATE_FIELDS` 에서 `"processingLevel"` 제거 | 화이트리스트가 런타임의 `additionalProperties:false` 강제 자리(`:414-415` 주석) |
| `catalog.py:460-466` | `if "processingLevel" in changes` 검증 블록 삭제 | 수용 경로 제거 |
| `catalog.py:100-101`·`579-580` | `d3_catalog.processing_level(summary, core.processing_level_user_set)` → 2번째 인자 제거 | 사람 값 참조 소멸 |
| `services/core-api/src/colab_core/domains/d3_catalog.py:661` | `_UPDATABLE` 대응표에서 `"processingLevel": ("d3_dataset","processing_level_user_set")` 행 삭제 | 완료 정의 ⓐ 「필드 대응표」 |
| `d3_catalog.py:792-807` | `processing_level(summary, user_set)` 시그니처에서 `user_set` 인자·`if user_set is not None` 분기 삭제 | 완료 정의 ⓐ 「`user_set` 분기」 |
| `d3_catalog.py:21`·`:63`·`:131`·`:145`·`:163` | SELECT 열·`DatasetCore` 필드·행 매핑에서 `processing_level_user_set` 제거 | 열이 사라지면 SELECT 가 깨진다 |
- 무접촉 확인 — `routes/lineage.py:74-75`·`routes/project.py:228` 은 이미 `processing_level(summary)` 1인자 호출이라 손댈 것이 없다.

**프런트 (변경 0건)**
- `frontend/src` 의 `processingLevel` 참조는 전부 **응답 읽기 또는 필터 질의**다 — `catalog/catalogSource.ts:19`(질의) · `CatalogTable.tsx:157` · `detail/DetailHeader.tsx:31-32` · `localEngine.ts:20`·`:50` · `catalog/fixture.ts`·`detail/fixture.ts`(픽스처).
- `DatasetUpdate` 를 쓰기로 소비하는 손으로 쓴 프런트 코드 **0건**(원장 선언 = `work-items.yaml:1418`). 이 조사에서도 반례 미발견.
- 완료 정의 ⓔ = `RegisterArea.tsx` 읽기 전용 칸 **그대로 둔다** — 화면 변경 없음이 전제.

**DB**
| 파일 | 변경 |
|---|---|
| `db/platform/schema.sql:336-338` | `processing_level_user_set smallint` 열 ＋ `CONSTRAINT d3_dataset_processing_level_user_set_range CHECK` 삭제 (＋ `:333-335` 주석 정리) |
| `db/platform/versions/0011_*.py` **신설** | up = 열·CHECK DROP · down = 복원. `0007_p2_human_written_meta.py:61`·`:67-69`(생성) 과 `:98`·`:101`(그 회차 down) 이 되돌림 문장을 그대로 준다 |

## 4. 계약 밖 파급

- **마이그레이션 = 필요하다 (1건 ＋ down).** 현 head = `db/platform/versions/0010_p6_access_request.py` ⟹ 다음 번호 **`0011`**. `J-1` 도 platform 체인에 `0011` 을 집는다(`PARALLEL-LAUNCH-MAP.md:69`) — **동시 개방 금지**(`:105` 축자 「같은 번호를 집으면 `migration-single-head` 가 head 분기로 red 를 낸다」).
- **게이트** — `contract-breaking`(**WARN 1 · ERR 0** 예측 · 실측 근거는 §2) · `contract-lint`(green 기대) · `generated-up-to-date`(`fe-core.ts` 재생성 필수 · 안 하면 red) · `seam-consistency`(계약↔라우트 대조) · **추가로** `migration-single-head` · `schema-diff` **두 체인 각각**(완료 정의 ⓒ · `gates/README.md:17` — `COLAB_APPLIED_DB_URL_PLATFORM`·`_AI` 둘 다 필요).
- **시험** — `services/core-api/tests/` 의 `processingLevel`/`processing_level_user_set` 참조 **25곳**. 실제 수정 대상은 사람 선택 경로를 단언하는 자리 = `test_dataset_update.py:89-121`(PATCH 로 값 넣기·되돌리기·400 경계). `test_dataset_detail.py:53`·`:62`·`:132` · `test_dataset_registration.py:90`·`:98` 은 **파생값 응답 단언**이라 존치 가능(값이 파생과 같으므로) — 개별 확인은 착수 회차 몫 **[미확인]**.
- **staging 배포** — 필요하다. 마이그레이션이 있으므로 선언＝적용을 배포 스택에서 확인해야 `schema-diff` ⓒ 가 선다.
- **프런트 시험** — 변경 예상 0건(쓰기 소비자 0).

## 5. 파괴인가 가산인가

- **계약 계수로는 파괴가 아니다** — 실측 `[request-property-removed]` **WARN 1 · ERR 0 · exit 0**(`work-items.yaml:1391`). oasdiff 는 요청 속성 제거를 ERR 로 세지 않는다.
- **실질도 파괴가 아니다** — 제거 대상은 **요청 바디의 선택 속성**이고, 그 속성을 싣는 소비자가 0건이다. 응답의 `processingLevel` 은 전부 남는다(§3) ⟹ 읽는 화면·시험은 아무 영향이 없다.
- **그런데도 ㉯ 다.** 사유는 파괴성이 아니라 **마이그레이션 ≥ 1 · 스키마 변경**(`X2-FREEZE-PROTOCOL.md:120`). ㉮ 조건 ①③④⑤ 는 충족하고 **②만 어긴다**(`work-items.yaml:1391` 축자 그대로).
- ⟹ 이 해제의 값은 **싼 ㉯** 다 — 10차 `〈205〉`(소비자 ≥ 1 · 의미 파괴)보다 가볍고, 12차 `〈253〉`(이벤트 계약 개정 ＋ 마이그레이션)과 같은 성질에 표면은 더 작다. op 총계 불변(54).

## 6. 해제를 피하는 더 싼 길이 있는가

- **없다 — 완료 정의를 유지하는 한.** ㉯ 를 부르는 것은 계약 편집이 아니라 **DB 열 제거**다. 계약 필드를 남기고 서버만 무시해도(가산 경로) 완료 정의 ⓐ 가 열·`CHECK` 제거를, ⓒ 가 down 마이그레이션을 요구하므로 마이그레이션 ≥ 1 이 그대로 남아 ㉯ 로 간다.
- **쪼개기는 금지다** — 「계약만 먼저 / DB 는 나중」은 `X2-FREEZE-PROTOCOL.md:136` ㉰-6(묶음 쪼개기로 자동 허용 만들기 · **목적 단위 판정**)에 정면으로 걸린다. 제안하지 않는다.
- **유일하게 가능한 대안 = 완료 정의 자체의 개정**(Ted 판정 사항). 열을 남긴 채 쓰기 경로만 닫으면 마이그레이션 0 · ERR 0 · 소비자 0 ⟹ **㉮ 자동 허용**으로 내려갈 가능성이 있다. 대가 = ⑴ `d3_dataset` 에 아무도 안 쓰는 열이 영구히 남고 ⑵ 〈194〉 「예외 없음」이 스키마 층에서 미집행으로 남으며 ⑶ 다음 회차가 그 열을 보고 경로를 되살릴 위험이 남는다. **권하지 않는다** — LV-1 의 취지가 「경로를 없앤다」이지 「막는다」가 아니다(`PLAN-SoT.md:541` 〈194〉-㉮).
- **비용 자체가 낮다는 사실이 더 값싸다** — 데이터 이행 0건 · 프런트 변경 0건 · 화면 변경 0건(ⓔ) · 응답 표면 불변. 원장 축자 「**화면에는 아직 없어 지금이 가장 싸다**」(`work-items.yaml:1417`). 미루면 소비자가 생겨 ㉰-2 로 굳을 수 있다.

## 7. 순서

1. **지금 열려 있는 두 레인(`V-2` 등)이 끝나야 한다** — `fe-core.yaml` ＋ `frontend/src/generated/fe-core.ts` 는 **한 번에 한 레인만**(`PARALLEL-LAUNCH-MAP.md:103` · `:161`).
2. **LV-1** — 계약·라우트·생성물·마이그레이션 `0011` 을 한 레인이 독점한다.
3. **CT-1 은 LV-1 뒤** — 같은 계약·같은 `routes/catalog.py`(`PARALLEL-LAUNCH-MAP.md:102`·`:162`). LV-1 이 필드를 빼고 CT-1 이 `downloadDataset` 을 채우므로 동시 재생성 시 `generated-up-to-date` 가 양쪽 red.
4. **J-1 은 LV-1 병합 뒤** — 마이그레이션 번호 `0011` 경합(`:105`·`:170`). J-1 은 `0012` 를 집는다. ＋ J-1 자체가 `completion_def_draft` 라 별건 결격.
5. **LV-2 는 병행 가능** — 공유 자리는 `LineageStep.tsx:90-91` 뿐이고 LV-1 은 프런트 변경 0건이므로 실질 충돌 없음. 다만 원장상 `LineageStep.tsx` 를 LV-2 가 독점하게 두는 것이 안전하다.
- **착수 전 필요한 것** = ⑴ Ted 의 ㉯ 승인 ⑵ 13차 회차 번호로 `PLAN-SoT §9` 등재(㉲ 8필드) ⑶ ⓑ 의 재계수(현재 값은 2026-08-29 실측).

## 8. 세지 않은 축 (㉱-7)

- 게이트를 이 회차에 **돌리지 않았다** — pg 슬롯 보호. §2 의 WARN 1 · ERR 0 은 `〈258〉` 실측 인용이다.
- `DatasetCreate.processingLevel`(`fe-core.yaml:2623`) 의 존폐 — **[미확인]**, Ted 판정 필요.
- `test_dataset_detail.py`·`test_dataset_registration.py` 의 개별 존치 여부 — **[미확인]**.
- `services/core-api` 밖(pipeline-worker·viz-render·ai-service)의 `processing_level_user_set` 참조 = **0건**(전수 grep 결과 4파일뿐).
