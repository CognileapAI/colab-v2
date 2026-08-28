# `#22` D2·D8 고아 행 — 실측 보고 (측정 전용 · 삭제 없음)

- 측정 일시: 2026-08-28
- 대상: staging `colab_v2_staging_pg` / DB `colab_platform`
- 수행 범위: **읽기 전용 SELECT 만**. DELETE/UPDATE/INSERT·컨테이너 기동/재기동·레포 편집 **없음**.
- 근거 문서: `dev-package/03-HANDOFF.md §4 #22` · `dev-package/WORK-UNITS.md §10.3 1단-㉮` · `db/platform/schema.sql`

---

## 1. `[미확인]` 판정 — **해소: 정형 열이다**

**확인된 사실.** `d8_activity` 에 payload·json·text 자유서술 열은 **없다**. 데이터셋 참조는 **정형 2열 조합**이다.

| 열 | 타입 | 제약 |
|---|---|---|
| `id` | ulid | PK |
| `lab_id` | ulid | NOT NULL, FK → `d1_lab(id)` |
| `actor_account_id` | ulid | NOT NULL, FK → `d1_account(id)` |
| `action` | text | NOT NULL, `length(btrim(action)) > 0` |
| `target_kind` | text | NOT NULL, **CHECK IN ('데이터셋','프로젝트')** |
| `target_id` | ulid | NOT NULL, **FK 없음 (bare 컬럼)** |
| `occurred_at` | timestamptz | NOT NULL DEFAULT now() |

- 출처(정본): `db/platform/schema.sql:660-672`, 동일 정의가 `db/platform/versions/0001_p0_platform.py:384-396`.
- staging 실물 `\d d8_activity` 로 **정본과 일치 확인**(드리프트 없음).
- 따라서 고아 술어는 **`target_kind` 로 분기한 `target_id` NOT EXISTS** 로 쓴다. 텍스트 파싱·LIKE 는 **불필요**.
  - `target_kind='데이터셋'` → `d3_dataset(id)` 대조
  - `target_kind='프로젝트'` → `d6_project(id)` 대조
- ⚠ `target_id` 에 FK 가 없는 것이 고아가 생긴 구조적 원인이다(D8 이 D3/D6 을 직접 FK 하지 않는 경계 규칙, `CLAUDE.md §3-1` 와 같은 계열).

## 2. D2 테이블 실제 열 (정본 `schema.sql:171-211`)

| 테이블 | 데이터셋 참조 열 | 비고 |
|---|---|---|
| `d2_dataset_access` | `dataset_id` (PK, **bare 컬럼 · FK 없음**) | `lab_id` FK→`d1_lab`, `state` CHECK('열림','잠김'), `updated_at` |
| `d2_verified` | `dataset_id` (PK, **bare 컬럼 · FK 없음**) | `verified`, `approver_account_id`, `approved_at`, `cancelled_by_account_id`, `cancelled_at`, `cancellation_reason(≤120)` + CHECK 3종 |
| `d2_dataset_access_grant` | `dataset_id` (**bare**) | `#22` 문안에는 없으나 같은 성질이라 함께 쟀다 |

→ D2 3종 모두 **정형 FK-형태 열**. `WORK-UNITS §10.3` 의 서술과 일치.

## 3. ⛔ 집행 차단 요인 — **`d8_activity` 는 DELETE 가 트리거로 막혀 있다** (신규 발견)

staging 실측:
```
CREATE TRIGGER d8_activity_append_only BEFORE DELETE OR UPDATE ON public.d8_activity
  FOR EACH ROW EXECUTE FUNCTION deny_update_delete()
```
`deny_update_delete()` 는 무조건 `RAISE EXCEPTION 'append-only 기록이다 — 수정·삭제 경로를 만들지 않는다 (PLAN-SoT 9-28)'` 를 던진다
(`db/platform/schema.sql:62-68`). `d8_download` 에도 같은 트리거가 있다.

**함의 — 사람 판정이 하나 더 필요하다.** `id` 를 못 박은 DELETE 라도 **그대로는 실패한다.**
집행하려면 ⓐ 트리거를 한시 비활성(`ALTER TABLE ... DISABLE TRIGGER`) 후 복구, 또는 ⓑ 삭제 자체를 철회 중 하나를 **Ted 가 골라야 한다.**
`#28`(경위 증거 보존)과 `PLAN-SoT §9-㉘`(append-only)이 같은 방향을 가리키므로 **ⓑ 도 실질 후보다.**
이 문서는 판정하지 않는다 — **[미판정]** 으로 올린다.

## 4. 고아 행 실측 결과

### 4.1 D2 — 고아 **0건** (대상 테이블이 비어 있다)

| 테이블 | 전체 행 수 | 고아 |
|---|---|---|
| `d2_dataset_access` | **0** | 0 |
| `d2_verified` | **0** | 0 |
| `d2_dataset_access_grant` | **0** | 0 |

⭑ **`#22` 의 「D2 고아 행」은 지금 staging 에 존재하지 않는다.** 테이블이 통째로 비었으므로 삭제할 것이 없다.
(과거 관측 시점과 현재 사이에 이미 사라졌는지, 애초에 D8 만이었는지는 **[미확인]** — 이 세션은 현재 상태만 쟀다.)

### 4.2 D8 `d8_activity` — 전체 9행 중 **고아 6건**

사용 질의(읽기 전용):
```sql
SELECT a.id, a.action, a.target_kind, a.target_id, a.occurred_at,
       (a.target_kind='데이터셋' AND NOT EXISTS (SELECT 1 FROM d3_dataset d WHERE d.id=a.target_id)) AS ds_orphan,
       (a.target_kind='프로젝트' AND NOT EXISTS (SELECT 1 FROM d6_project p WHERE p.id=a.target_id)) AS pj_orphan
FROM d8_activity a ORDER BY a.occurred_at;
```
※ RLS 는 `ENABLE + FORCE` 이나 `postgres` 슈퍼유저로 조회해 우회했다(`is_superuser = on` 확인). 즉 **전 연구실 전수**다.

| # | `id` (삭제 대상 못 박기용) | `action` | `target_kind` | `target_id` | `occurred_at` | 고아 |
|---|---|---|---|---|---|---|
| 1 | `00000000000000000000000AC1` | 데이터셋 등록 | 데이터셋 | `0000000000000000000000DSA1` | 2026-08-24 19:36:11.342413+00 | **O** |
| 2 | `00000000000000000000000BC1` | 데이터셋 등록 | 데이터셋 | `0000000000000000000000DSB1` | 2026-08-24 19:36:11.342413+00 | **O** |
| 3 | `01M0WG5QCZMDXA26AJHRGV5PDS` | 좌표계·격자 변경 | 데이터셋 | `01M0WG5MF4MV38Y25TXBSHBFZA` | 2026-08-25 13:01:24.246754+00 | **O** |
| 4 | `01M0WG657G9AAF7WC86QW76AJW` | 좌표계·격자 변경 | 데이터셋 | `01M0WG62EK6B3A389D1H5HFNS6` | 2026-08-25 13:01:38.40804+00 | **O** |
| 5 | `01M0WGCM6H7262MH9N288HMW2M` | 좌표계·격자 변경 | 데이터셋 | `01M0WGCH93NE9G6PREH2R7SSQP` | 2026-08-25 13:05:10.345588+00 | **O** |
| 6 | `01M0WMNREVDT5A6XX8CPMAYSDJ` | 좌표계·격자 변경 | 데이터셋 | `01M0WMNNGNT7KPWPJGDGBFC0J6` | 2026-08-25 14:20:03.922007+00 | **O** |
| 7 | `01M0YTM9XF8CPNYNDSS9S68C1F` | 좌표계·격자 변경 | 데이터셋 | `01M0Y1WM5JBDJRZ8FT3AX8HXE1` | 2026-08-26 10:42:36.581345+00 | 정상 |
| 8 | `01M0YTT8SX206VKHJT8W3RB2TB` | 좌표계·격자 변경 | 데이터셋 | `01M0Y1WMH6M87QFM790QPEYJ2R` | 2026-08-26 10:45:52.054077+00 | 정상 |
| 9 | `01M0YTTD2JMW26GZWC0WRF379Y` | 좌표계·격자 변경 | 데이터셋 | `01M0Y1WPE3G340DSYDW4Y7QNTF` | 2026-08-26 10:45:56.426649+00 | 정상 |

- **`target_kind='프로젝트'` 행은 0건**이다. 즉 D6 대조에서 걸리는 고아는 없다.
- 성격이 둘로 갈린다 — **1·2 는 자리표시(`...DSA1`/`DSB1`) 시드 잔재**, **3~6 은 실제 파이프라인이 만든 뒤 데이터셋이 사라진 것**(2026-08-25 오후, 같은 날 `좌표계·격자 변경` 계열). 3~6 이 `#28` 이 말한 「경위 증거」에 해당한다고 **추론**된다 — 확정은 아니다 **[미확인]**.

### 4.3 확정 삭제 대상 id 목록 (조건 병기 · `〈152〉` 방식)

```sql
-- 집행하지 않았다. 문서화된 후보일 뿐이다.
DELETE FROM d8_activity
WHERE id IN (
  '00000000000000000000000AC1',
  '00000000000000000000000BC1',
  '01M0WG5QCZMDXA26AJHRGV5PDS',
  '01M0WG657G9AAF7WC86QW76AJW',
  '01M0WGCM6H7262MH9N288HMW2M',
  '01M0WMNREVDT5A6XX8CPMAYSDJ'
)
  AND target_kind = '데이터셋'
  AND NOT EXISTS (SELECT 1 FROM d3_dataset d WHERE d.id = d8_activity.target_id);
-- ⛔ 위 문장은 d8_activity_append_only 트리거에 의해 현재 상태로는 반드시 실패한다 (§3).
```

### 4.4 ⭑ 범위 밖 발견 — `d8_download` 에도 고아 2건

`#22` 문안은 `d8_download` 를 대상으로 적지 않았으나, 같은 성질(`dataset_id` bare 컬럼)이라 함께 쟀다.

| `id` | `dataset_id` | 상태 |
|---|---|---|
| `00000000000000000000000AD1` | `0000000000000000000000DSA1` | 고아 |
| `00000000000000000000000BD1` | `0000000000000000000000DSB1` | 고아 |

§4.2 의 1·2 와 **같은 시드 뭉치**다. **`#22` 범위에 넣을지는 사람 판정 [미판정]** — 넣지 않으면 「고아 0」 사후 실측의 정의를 `d8_activity` 로만 좁혀 적어야 한다.

## 5. 삭제 전 기준선 재확인 (`§10.3` 표의 「삭제 전」 칸)

| 축 | 실측값 | `〈165〉-㉮` 기대 | 일치 |
|---|---|---|---|
| 데이터셋 (`d3_dataset`) | **12** | 12 | ✅ |
| 파일 (`d3_file`) | **129** | 129 | ✅ |
| 간선 (`d4_lineage_edge` `confirmed_at IS NOT NULL`) | **6** | 6 | ✅ |
| `d4_lineage_edge` **전체** `COUNT(*)` | **6** | 6 이어야 한다(`〈166〉-㉰`) | ✅ **미확정 행 없음** |
| `d6_project_dataset` | **12** | 12 | ✅ |
| `d2_dataset_access` / `d2_verified` / `d2_dataset_access_grant` | **0 / 0 / 0** | — | 삭제 전 값 |
| `d8_activity` | **9** (고아 6) | — | 삭제 전 값 |
| `d8_download` | **2** (고아 2) | — | 삭제 전 값 |
| `d6_project` | **2** | — | 참고 |

⭑ **`d4_lineage_edge` 전체 행 수 = 6** 을 실측했다. `§10.3` 이 「지금까지 세지 않은 축」이라 걸어 둔 항목이고, **전체와 confirmed 가 같으므로 미확정 행은 없다.**
※ 이미지 digest 대장(`reference/IMAGE-DIGESTS.md`) 대조는 **이 세션의 과업이 아니라 수행하지 않았다 — [미확인]**.

## 6. staging 접근성

**확인된 사실.** 이 호스트에서 staging 은 **이미 가동 중**이었다. 기동·재기동·설정 변경은 하지 않았다.

```
colab_v2_staging_core_api        Up 29 hours (healthy)
colab_v2_staging_pipeline_worker Up 31 hours (healthy)
colab_v2_staging_ai_service      Up 31 hours (healthy)
colab_v2_staging_viz_render      Up 32 hours (healthy)
colab_v2_staging_frontend        Up 32 hours (healthy)
colab_v2_staging_pg              Up 32 hours (healthy)
colab_v2_staging_nginx           Up 32 hours (healthy)
colab_v2_staging_cloudflared     Up 32 hours
```
- 호스트에 `psql` 바이너리는 **없다**. 접속은 `docker exec colab_v2_staging_pg psql -U postgres -d colab_platform` 로 했다.
- `RESTART.md` 는 「도커 데몬이 자동 기동하지 않는다」고 적지만, 이번에는 **이미 떠 있었으므로 기동 절차를 밟지 않았다.**

## 7. 확인 / 추론 / 미확인 갈라 적기

**확인된 사실 (실측)**
- `d8_activity` 참조 방식 = 정형 `target_kind`+`target_id`. payload 텍스트 아님. 정본·staging 실물 일치.
- D2 3종 전부 0행 → **D2 고아 0**.
- `d8_activity` 9행 중 고아 6행, id 목록 §4.3.
- `d8_download` 고아 2행.
- `d8_activity`·`d8_download` 에 DELETE 차단 트리거 존재.
- 기준선 12 · 129 · 6 · 6(전체) · 12 일치.

**추론 (측정 아님)**
- §4.2 의 1·2 및 §4.4 두 행은 같은 시드 뭉치 잔재.
- 3~6 은 2026-08-25 파이프라인 작업 중 데이터셋이 사라져 남은 것.

**[미확인] / [미판정]**
- `#22` 가 애초 관측한 「D2 고아」가 그 사이 사라진 것인지, 처음부터 없었는지.
- 트리거 우회(ⓐ) 대 삭제 철회(ⓑ) 선택 — 사람 판정.
- `d8_download` 2건을 `#22` 범위에 넣을지 — 사람 판정.
- 이미지 digest 대장 대조 — 미수행.
- 선백업 GREEN(`§10.3` 2번) — 이 세션에서 확인하지 않았다.

---

# 8. 집행 기록 (2026-08-28 · `PLAN-SoT §9 〈174〉-㉯`)

**§3 의 `[미판정]` 둘이 판정됐다.** Ted 2026-08-28 —
- 트리거 우회(ⓐ) 대 삭제 철회(ⓑ) → **ⓐ 트리거 한시 해제 후 삭제, 즉시 원복**
- `d8_download` 2건 → **범위에 넣지 않는다.** 승인 범위는 `d8_activity` 6건이다

## 8.1 선행 — 전범위 백업 GREEN

- 시각 **2026-08-28 12:42:47 ~ 12:43:22**
- 원장 2 프로파일 ＋ 볼륨 2 개 · 보관처 규약 밖 파일 **0**
- `uploads` **341,527,870 B** · 아카이브 항목 **135** = 매니페스트 **135**(경로·크기 전건 일치)
- **V5-a 원장 행 129 = 고유 저장키 129** · **V5-b 원장이 가리키는 129 건 전건 매니페스트 포함**
- 아카이브에만 있는 **6건** = 덤프 이후 접수분(정상 · `§4.4-㈏`)
- `previews` **6,472,714 B · 39건** — V5 는 **오라클 명시 면제(`none`)로 SKIP**, 요약줄에 드러남
- 짝 원장 = **`platform-20260828T124246.sql.gz`**
- ⭑ `§7` 의 **[미확인]** 이던 「선백업 GREEN」이 이로써 확인됐다

## 8.2 집행 — 단일 트랜잭션

`DISABLE TRIGGER` → `DELETE`(id 6건 ＋ 고아 조건 병기) → `ENABLE TRIGGER` → **원복 확인** → `COMMIT`.
커밋 전에 `pg_trigger.tgenabled` 를 조회했다. **원복이 확인되지 않으면 커밋하지 않는다**는 것이 절차다.

| 관측 | 값 |
|---|---|
| 삭제 전 `d8_activity` | **9** |
| `DELETE` | **6** |
| 트리거 상태(커밋 전 조회) | **`O`** — 원복됨 |
| 삭제 후 `d8_activity` | **3** |
| 잔여 고아 (`d8_activity`) | **0** |

## 8.3 사후 — 트리거 실효 음성 시험

「원복했다」는 표기는 증명이 아니다. **트리거가 실제로 다시 막는지를 쟀다.**

```
BEGIN; DELETE FROM d8_activity WHERE id = (SELECT id FROM d8_activity LIMIT 1);
ERROR:  append-only 기록이다 — 수정·삭제 경로를 만들지 않는다 (PLAN-SoT 9-28)
CONTEXT:  PL/pgSQL function deny_update_delete() line 3 at RAISE
ROLLBACK
```

**거부됐다.** append-only 성질은 회복돼 있다.

## 8.4 삭제 후 기준선

| 축 | 값 | 판정 |
|---|---|---|
| 데이터셋 `d3_dataset` | **12** | 불변 |
| 파일 `d3_file` | **129** | 불변 |
| 간선 `d4_lineage_edge` (`confirmed_at IS NOT NULL`) | **6** | 불변 |
| `d4_lineage_edge` **전체** | **6** | 불변 · **미확정 행 없음**(`〈166〉-㉰` 해소) |
| `d6_project_dataset` | **12** | 불변 |
| `d8_activity` | **3** | 9 → 3 |
| `d8_download` | **2** | 손대지 않았다 |

**삭제가 다른 축을 건드리지 않았다.**

## 8.5 남은 것 — 정직하게

- ⚠ **`d8_download` 고아 2건 잔존.** 사후 「고아 0」의 정의는 **`d8_activity` 한정**이다.
  **전역 「고아 0」이라고 적으면 거짓이다.** 처분은 **열린 판정**이다
- **`#22` 의 「D2 고아 행」은 집행 시점에 존재하지 않았다** — D2 3종 전부 0행.
  애초에 없었는지 그 사이 사라졌는지는 **[미확인]**
- **이미지 digest 대장 대조** — 이 회차의 과업이 아니라 수행하지 않았다 **[미확인]**.
  `X-1`·`X-4` 재기동 전에 `reference/IMAGE-DIGESTS.md` 와 한 줄씩 대조해야 한다(`§10.3`)
