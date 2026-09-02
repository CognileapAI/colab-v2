# LV-1 · 13차 계약 동결 해제 — 등재문 초안 (번호 미발급)

작성 2026-09-02 · 워크트리 `lane-lv1`(브랜치 `lane-lv1` · `main` `e1c0a11` 기점) · **레인은 `PLAN-SoT §9` 에 직접 쓰지 않는다.**
번호 발급·등재는 오케스트레이터 몫이다(직전 발급 `〈275〉` ⟹ 이 항목은 `〈276〉` 이 될 자리이나 **번호를 짓지 않는다**).
직전 해제 = **12차 `〈253〉`** ⟹ 이 회차는 **13차**.

---

## ㉲ 8필드 등재문 (§9 한 항목 · 표 한 행으로 옮겨 붙일 것)

| 〈n〉 | **`LV-1` 집행 — 사람이 가공 단계를 직접 고르는 경로를 제거한다(생성 요청 포함). 13차 동결 해제** | **집행 ＋ 실측 (2026-09-02 · 워크트리 `lane-lv1`)** … 아래 ①~⑧ |

**① 회차 번호** — **13차**(직전 12차 `〈253〉` · 등급 **㉯** · `sessions/X2-FREEZE-PROTOCOL.md §5-㉯`).

**② 값(파일·op·필드 단위)** — **op 총계 불변(54)** · **필드 제거 2**(`DatasetCreate.processingLevel` · `DatasetUpdate.processingLevel`) · 응답 필드 5자리와 목록 질의 조건 `FilterProcessingLevel` 은 **존치**(계약 축자 「파생값이지만 조건으로는 걸 수 있다 — 쓰기 바디에는 없다」). 파일 = 계약 1 · 생성물 1(`frontend/src/generated/fe-core.ts`) · 서비스 2(`routes/catalog.py`·`domains/d3_catalog.py`) · DB 2(`db/platform/schema.sql` ＋ 신설 `0011_lv1_drop_level_user_set.py`) · 시험 2.

**③ 근거** — `PLAN-SoT §9 〈194〉`(2026-08-29 Ted) 「레벨은 언제나 계보에서 나온다 — 사람이 직접 정하지 못한다 … **예외 없음**」. 그 회차는 **문서 등재 전용**이었고 코드 제거가 `LV-1` 이다. 등급 확정 = `〈258〉`(2026-08-31 Ted RULING ㉝). 범위 조사 = `notes/LV-1-UNFREEZE-SCOPE.md`.
⭑ **완료 정의 개정도 이 회차다** — 종전 문면은 `DatasetUpdate` 만 지목했고 조사가 `DatasetCreate` 를 `[미확인]` 로 올렸다. **Ted 판정(2026-09-02) = `〈194〉` 의 「예외 없음」이 문면보다 위다 ⟹ 생성 요청에서도 뺀다.** `work-items.yaml` `LV-1` `completion_def` ⓐ 를 그에 맞춰 개정했다(원문은 지우지 않고 개정 표시).

**④ 가·파 판정과 게이트 출력** — **파괴 아님(계수·실질 둘 다).** `contract-breaking` = **`2 changes: 0 error, 2 warning, 0 info`** · `[request-property-removed]` × 2(`POST /datasets` · `PATCH /datasets/{datasetId}`) · **ERR 0 · green**. `〈258〉` 예측(WARN 1)에서 **WARN 2 로 늘어난 유일한 사유가 생성 요청 확대**다. 함께 = `contract-lint`·`seam-consistency`·`generated-up-to-date`·`migration-single-head`·`schema-diff`(두 체인) 전건 green. **전체 = green 37 / red(판정) 0 / red(준비) 0**(`./gates/run.sh all -j 1` · 직렬).
**그런데도 ㉯ 다** — 사유는 파괴성이 아니라 **마이그레이션 ≥ 1 · 스키마 변경**(§5-㉯). ㉮ 5조건 중 ②만 어긴다. **등급은 게이트 수가 아니라 성질로 정한다**(10차 `〈205〉` 축자).

**⑤ 소비자 수와 그 측정법** — 쓰기 소비자 **0건**. 측정 = ⑴ `frontend/src` 전수 grep — `processingLevel` 참조는 전부 **응답 읽기 또는 필터 질의**(`catalogSource.ts`·`CatalogTable.tsx`·`DetailHeader.tsx`·`localEngine.ts`·픽스처 2) ⑵ `tsc --noEmit` 통과 ⑶ frontend 시험 **422 passed**(기준선과 같다) ⑷ ⭑ **생성 요청은 서버가 이미 막고 있었다** — `routes/ingestion.py` `_ALLOWED_CREATE_FIELDS` 에 `processingLevel` 이 애초에 없어 실어 보내면 400 이었다. **계약만 열려 있던 드리프트**이고 이번 제거가 그것을 닫는다.

**⑥ 마이그레이션 건수** — **1건**. `0011_lv1_drop_level_user_set`(head `0010_p6_access_request` → `0011`). up = `CHECK` DROP ＋ 열 DROP · **down = `0007` UPGRADE ⑴ 의 거울**(열 ＋ `CHECK` 복원). 적용 DB 에서 `upgrade → downgrade -1 → upgrade` **왕복 실측**. ⚠ 리비전 id 는 32자 상한에 걸려 `..._drop_processing_level_user_set` → **`0011_lv1_drop_level_user_set`** 으로 줄였다(`alembic_version_platform.version_num varchar(32)`).
⚠ **되돌려도 잃는 값이 없는 회차다** — 지우기 직전 비-NULL 0건이라 복원된 열의 전량 `NULL` 이 정확히 직전 상태다.

**⑦ 승인자·일자** — **Ted · 2026-09-02**(13차 해제 승인 ＋ 생성 요청 확대 판정 ＋ 완료 정의 개정 승인).

**⑧ 이번에 세지 않은 축** —
- ⓐ **staging 배포** — 안 했다. 적용 DB(`COLAB_APPLIED_DB_URL_PLATFORM`)는 `0011` 까지 올라갔으나 **staging 실물 `colab_platform` 에는 열이 그대로 있다.** 배포 전까지 「선언＝적용」은 게이트 DB 에서만 성립한다. **다음 회차 진입조건.**
- ⓑ **`RegisterArea.tsx` 화면 실물** — 코드 무접촉이 확인의 전부다(완료 정의 ⓔ 는 「그대로 둔다」이므로 충족). 브라우저 왕복은 재지 않았다.
- ⓒ `DatasetCreate` 의 **다른 계약↔런타임 드리프트** — `variables`·`crs`·`period` 도 계약에는 있는데 `_ALLOWED_CREATE_FIELDS` 에 없다(400). **이 회차의 대상이 아니고 고치지 않았다.** 별건으로 세울 자리다.
- ⓓ 병합·병합 순서 — 레인 밖이다.

---

## 참고 — 이 회차가 `X2-FREEZE-PROTOCOL.md §1` 에 남길 한 줄 (오케스트레이터가 등재 시 함께)

**⟨개정 2026-09-02 · `PLAN-SoT §9 〈n〉`⟩ 13차가 발급됐다 — 다음 해제는 14차다.** 원문은 지우지 않는다.
**13차 = `〈n〉`**(`fe-core.yaml` 의 `DatasetCreate`·`DatasetUpdate` 에서 `processingLevel` **필드 2 제거** ＋ 마이그레이션 1 · 2026-09-02 Ted 승인 · 등급 ㉯ — **마이그레이션 ≥ 1 · 스키마 변경**).
⚠ **게이트 계수로는 ERR 0(WARN 2)이지만 등급은 ㉯ 다** — 10차 `〈205〉`·11차 `〈231〉`·12차 `〈253〉` 에 이어 **넷째**다. 스키마를 여는 회차는 예외가 아니라 ㉯ 가 받는 정상 경로다(`§1` 축자).
⭑ **§5-㉰-6(묶음 쪼개기) 회피** — 「계약만 먼저 / DB 는 나중」으로 ㉮ 를 만들지 않았다. 계약·수용 경로·열·시험을 **한 회차에** 걷었다.
