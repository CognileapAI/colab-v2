# WU-A5 · 확장자 표기 (PRD-21) — 레인 `p3-extension-label`

기준 = `origin/integration/r-a-c19`(0e7ba01) · 19차 묶음(A5＋A4＋A6) 중 A5 한 건.

## 1. 바뀐 것

| 자리 | 무엇 |
|---|---|
| `db/platform/schema.sql:416-427` | `d3_dataset_autometa.file_extension text` — **선언 순서는 맨 뒤**(ADD COLUMN 이 뒤에 붙는다) |
| `db/platform/versions/0013_ra1_ext_interval_period.py` | 마이그레이션 **1개**(M-9). down = `0011_lv1_drop_level_user_set` |
| `db/platform/tests/0013-drift.sh` ＋ 오라클 3개 | ㈎적용 green ㈏없으면 red ㈐downgrade red＋0011 복원 **㈑백필 일치(대조군 red)** |
| `contracts/seams/fe-core.yaml:3079-3120` | `DatasetBasicInfo.fileExtension` 신설(required · nullable) · `format` description = 「내부 판별값 · 화면에 쓰지 않는다」 |
| `frontend/src/generated/fe-core.ts` | 재생성(`openapi-typescript` 7.13.0 · 등기부 명령 그대로) |
| `domains/d3_catalog.py:86,116,180,537,673,692` · `routes/ingestion.py:557` · `routes/catalog.py:791` | 조회·dataclass·INSERT·`register_dataset(file_extension=)` / 등록 전환이 조각 확장자를 심는다(혼합 400 검사가 이미 만든 `extensions`) / 상세 `basicInfo.fileExtension` |
| `detail/format.ts:formatExtension` · `BasicInfoGrid.tsx:45` · `RegisterArea.tsx:93` | **조립 한 곳**(`*.nc` · 없으면 `format` 퇴행 · 둘 다 없으면 `—`) · 상세 포맷 칸 · 등록 자동 칸 라벨 `확장자`＋`자동` |
| `upload/FileDropCard.tsx` ＋ `upload.css` | 업로드 안내 **둘로 분리**(업로드 가능 / 미리보기 가능) |

**목록(`DatasetRow`)에는 포맷 칸이 없다** — 계약에도 화면에도 없어 고칠 자리가 0건이다(`ProjectDatasetTable.tsx:4` 가 그 이유를 적고 있다). 계약 변경은 `DatasetBasicInfo` **하나뿐**이다.

되돌림 = `downgrade` 가 열을 지운다. **잃는 값이 없다** — 전량 `d3_file.file_name` 파생이라 재적용이 같은 값을 낸다.

## 2. 계약 동결 해제 19차 근거 (㉰) — 이 WU 몫

⑴ `./gates/run.sh contract-breaking` 축자
```
No breaking changes to report, but the specs are different.
Run 'oasdiff diff' to see structural differences.
contract-breaking green — 기준 HEAD (3건) 대비 파괴적 변경 없음.
```
→ **A5 조각만 보면 「가」다**(응답 스키마에 열쇠를 더한 것뿐). 19차를 **㉯** 로 만드는 파괴는 A6 의 `DataPeriod.granularity`(`additionalProperties: false`)이고, 판정은 **목적 단위**로 한다(§5-㉰-6 묶음 쪼개기 금지) — 이 출력을 「19차는 안 파괴적이다」로 읽지 않는다.

⑵ 소비자 `grep -rn 'DatasetBasicInfo\|fileExtension\|file_extension' contracts/ services/ frontend/src | wc -l` → **48**

⑶ 마이그레이션 = **1 파일 · head 1개** (지금은 `M-9` 하나. `M-6`·`M-7` 은 A6 가 **같은 파일**에 이어 적는다 — 새 리비전을 만들지 않는다)

⑷ 되돌림 경로 — **열을 지우지 않고 되돌아가는 길이 있다.** 화면·서버의 `fileExtension` 소비만 되돌리면 화면이 종전대로 `format` 을 보인다(확장자 NULL 행의 퇴행 경로가 이미 그 길이다). 열은 남아도 아무도 안 읽어 무해하고 재배포 시 백필을 다시 돌릴 필요가 없다. 열까지 지우려면 `downgrade`. ⛔ `topic`·`variables`·`format` 은 어느 경로에서도 지우지 않는다.

## 3. 게이트 (단독 · 전건 재실행 아님)

| 게이트 | 결과 |
|---|---|
| `contract-lint` · `contract-breaking` · `generated-up-to-date` | green — seam 3건 위반 0 / 위 축자 / 등기부 4건 재생성 일치 · 자칭 생성물 0 |
| `migration-single-head` | green — platform 13건 head 1개(`0013_ra1_ext_interval_period`) · ai 5건 head 1개 |
| `schema-diff` | green — 두 체인 선언＝적용 ⚠ 홈 `COLAB_APPLIED_DB_URL_PLATFORM` 은 `origin/main` 체인(`0012_merge_lv1_and_transfer`)이라 비교 대상이 아니다. **이 브랜치 체인으로 지은 일회용 DB**에 대고 쟀다(RESTART §2-④-㉮ 절차 그대로) |
| `db-boundary` · `service-tests-core-api` | green — 단위 7·스캔 296·위반 0 / 654 통과 · skipped 0 · failed 0 |
| `frontend-typecheck` · `frontend-test` | green — 오류 0 / 47 파일 · 680 통과 |
| `e2e-format-coverage` | green — 필수 5종 전건(초회 red(준비): viz-render venv 부재 → venv 세운 뒤 green) |
| `work-item-consistency` | green — 대장↔산문 불일치 0 |
| `db/platform/tests/0013-drift.sh` | green — ㈎green ㈏red ㈐red＋0011 복원 ㈑백필 green ㈑-b 대조군 red |

RED 선실측 → GREEN — `services/core-api/tests/test_file_extension.py` **6건**(red 6 → green 6) · `frontend/test/extension-label-20260905.test.tsx` **11건**(red 10/11 → green 11) · `frontend/test/upload.test.tsx` 증설 **2건**(red 2 → green 2).

## 4. 넘길 것

- **`[미상]` 없음.** 다만 **번호 충돌 1건** — `origin/main` 은 이미 `0011_merge_transfer_and_access`·`0012_merge_lv1_and_transfer` 를 갖고 있다(이 레인의 기준 `r-a-c19` 에는 없다). 그래서 파일명을 `0013` 으로 두었고 `down_revision` 은 기준 브랜치의 head(`0011_lv1_drop_level_user_set`)다. **`main` 병합 직전에 `down_revision` 을 `main` head 로 다시 겨눠야 한다** — 안 하면 `0011_lv1` 에 자식이 둘이 되어 head 가 갈라진다(`migration-single-head` red).
- 미충족 1건 — PRD-21 「`nc` 로도 찾는다」는 색인 재정의(`M-10`)와 함께 **R-B** 로 이월. 지금 검색은 종전대로 `format` 으로 잡힌다(`0013-assertions.sql` C⑵ 가 그것을 붙잡는다).

## 5. PLAN-SoT §9 초안 (병합 직전 `〈N〉` 재실측 · ⑦은 아직 대기)

```
| 〈N〉 | **R-A-1 DB 계층 — 계약 동결 해제 19차 · `DataPeriod.granularity` ＋ `file_extension` ＋ 관측 간격 2칸** | **집행 (2026-MM-DD · 워크트리 `p3-extension-label` · 병합 `<sha>`).** ①회차 = **19차**(직전 18차) ②값 = `DataPeriod.granularity` · `DatasetBasicInfo.fileExtension` · `observationInterval{value,unit}` ③근거 = PRD-17·18·21·35 (`dev-package/prd/PRD-260905-적용전기획.md`) ④가·파 판정 = **파괴** · `contract-breaking` 출력 = A5 조각 축자 `No breaking changes to report, but the specs are different.` · 파괴는 A6 의 `DataPeriod`(`additionalProperties: false`) ⑤소비자 = `48` 건(A5 몫) · 측정법 = `grep -rn 'DatasetBasicInfo\|fileExtension\|file_extension' contracts/ services/ frontend/src` ⑥마이그레이션 = **3건 · head 1개**(M-9·M-6·M-7 · 파일 `0013_ra1_ext_interval_period`) ⑦승인 = `[승인 대기]` ⑧이번에 세지 않은 축 = `M-10` 색인 재정의(R-B 로 묶음) `[미측정]` |
```
