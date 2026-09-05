# 고아 데이터셋 5건 삭제 계획 — **준비만. 삭제 0.**

작성 2026-09-06 · 창 8-b 레인 `integration/w8b-dev-deploy` · 근거 = 어드바이저 게이트 ③ GO-with-conditions
전제 = `PLAN-SoT §9 〈349〉`(S3 삭제 · 승인 1회 소진) · `〈358〉`(계수 오류 정정)

> ⛔ **이 문서는 집행 문서가 아니다.** `--yes-delete` 는 **돌리지 않았다.**
> 실측 확인 = 계획 작성 뒤 API `listDatasets` **totalCount 19** (변화 없음).
> ⛔ **남은 전제 둘** — ⑴ **Ted 의 명시 GO**(아래 `§6` 문장) ⑵ **박홍진 통보**.

---

## 1. 대상 5건 — **목록으로 못 박았다** (조건문이 아니다)

| # | 데이터셋 id | 이름 | `fileCount` | 올린 계정 |
|---|---|---|---:|---|
| 1 | `01M1FSEWYJVAV20VPMPT3EDDW9` | `온보딩_박홍진_lecture_01` | 7 | `…AP1`(admin) |
| 2 | `01M1C0F19DFGA80AM4HR63S1ND` | `MOD15A2H.A2019281.h28v05.061.2020314051209` | 8 | `…AP1` |
| 3 | `01M1H2DYX821ZR33SVVVQGJZ9R` | `RDR_CMP_HSR_PUB_202107031745.bin` | 31 | `…AP1` |
| 4 | `01M1H4XH0XMQ7CNJ8256WP16SF` | `RDR_CMP_HSR_PUB_202508131025.bin` | 12 | `…AP1` |
| 5 | `01M1GR9N0DSK2AVRWJEBM5D0SD` | `rn15_sample` | 31 | `…AP1` |
| | | **계** | **89** | |

**연구실** = `0000000000000000000000000A`(고려대학교 수문학연구실) — 5건 전부 같다.
⭑ **다섯 다 `…AP1` 이 올렸다** — 재적재 14건은 전부 `…A1`(`colab`)이다. **올린 계정이 갈라 준다.**

## 2. 도출과 이중 확인 — 네 가지가 전부 맞물린다

**⑴ 전 연구실 전수 조회** — `colab_backup` 롤(`pg_read_all_data`)로 **연구실 경계 없이** 쟀다.
`d1_lab` **2행**(A · B)이고 **`d3_dataset` 19건이 전부 연구실 A** 다 ⟹ **B 에 고아 없음.**
전체 계수 = `d3_dataset` **19** · `d3_file` **523** · `d4_lineage_edge` **6**.
⭑ **523 = 434(적재) ＋ 89(고아)** — 검산이 맞는다.

**⑵ 이름 완전 일치로 뺐다** — 19건에서 매니페스트 14건 이름을 빼면 **정확히 위 5건**이다(`〈106〉` 동일성 규칙).

**⑶ ⭐ `storage_key` 가 삭제 목록과 1:1 이다** — 5건의 `d3_file.storage_key` **89개**를
`s3-pre-wipe.txt` 의 `uploads/` **89키**와 대조했다:
**DB 에 있는데 삭제 목록에 없는 키 = 0 · 삭제했는데 이 5건 것이 아닌 키 = 0.**
⟹ `〈349〉` 가 지운 것이 **정확히 이 5건의 바이트**이고 그 밖은 없다.

**⑷ HeadObject 전수 404** — 89키 전부 `aws s3api head-object` **404**(존재 0 · 그 밖 0).
⟹ **바이트가 실제로 없다.** 반대로 적재 14건의 키는 살아 있다(`uploads/` 460 객체).

## 3. 표별 예정 행수 — dry-run 실측 (`orphan-purge-dryrun.txt`)

⭐ **읽기 전용 조회(`colab_backup`)와 dry-run(`colab_owner` ＋ 경계)이 표마다 같은 값을 냈다.**

| 표 | 행 | 왜 지우나 |
|---|---:|---|
| `d3_file` | **89** | 진짜 FK. **먼저 지운다** — `sync_dataset_file_count` 트리거 때문 |
| `d3_dataset_description` | 5 | 진짜 FK |
| `d3_dataset_autometa` | 5 | 진짜 FK |
| `d4_lineage_edge` | **0** | 진짜 FK(child·parent 양쪽 조회) — 고아 5건은 간선이 없다 |
| `d4_lineage_unknown` | 5 | 진짜 FK |
| `d2_dataset_access` | 0 | bare 컬럼 |
| `d2_dataset_access_grant` | 0 | bare 컬럼 |
| `d2_dataset_access_request` | 0 | bare 컬럼 |
| `d2_verification_request` | **2** | bare 컬럼 — 남기면 정책이 유령 행을 참조한다 |
| `d2_verified` | **2** | 같음 |
| `d6_project_dataset` | **1** | ⚠ **고아 하나가 프로젝트에 묶여 있다** — 그 묶음 줄만 빠진다(프로젝트는 남는다) |
| `d3_dataset` | **5** | 대장 — **마지막** |
| **계** | **114** | |

⛔ **손대지 않는 표** — `d8_download`(**4행 있다**)·`d8_activity` 는 `deny_update_delete` 트리거가
DELETE 를 예외로 막는 **감사 기록**이다. FK 가 아니라 bare 컬럼이라 남겨도 무결성이 안 깨진다.
`d5_upload*` 는 `dataset_id` 열 자체가 없다 — 무접촉.
⚠ `d8_activity` 에는 `dataset_id` 열이 아예 없다(조회가 `UndefinedColumn`) — 계획표에도 없다.

## 4. 백업 — 실행했다

`sudo /opt/colab-v2/backup.sh`(기존 경로 · `colab_backup` 롤) · 2026-09-05 18:46:15Z **GREEN**.

| 객체 키 | 크기 |
|---|---:|
| **`_ops/backups/dev/2026-09-05T184611Z-colab_platform.sql.gz`** | 73,983 B |
| `_ops/backups/dev/2026-09-05T184611Z-colab_ai.sql.gz` | 5,111 B |

⭑ **적재 14건이 든 뒤의 덤프**다 — 되돌릴 지점으로 이 키를 쓴다. 새 백업 장치를 만들지 않았다.

## 5. 집행 도구 — `services/core-api/ops/purge_datasets.py`

**가드 다섯** — ⑴ 트랜잭션 안에서 **`set_config('app.current_lab', …, true)` 를 먼저** 건다
(⭑ `colab_owner` 는 **`NOBYPASSRLS`** 이고 표는 **FORCE RLS** 다 — 경계가 없으면 DELETE 가
**0행에 조용히 성공**한다. `〈358〉` 함정의 쓰기판) ⑵ **순서 고정** — `d3_file` → 자식·bare → `d3_dataset`
⑶ **`--yes-delete` 없으면 dry-run** ⑷ `d3_dataset`·`d3_file` 이 0 이거나 `d3_dataset` ≠ 인자 개수면
**중단**(0행 삭제를 성공으로 세지 않는다) ⑸ 실집행에서 표별 `rowcount` 가 dry-run 과 하나라도
다르면 **ROLLBACK**. ⛔ 접속 문자열은 **파일 경로로만** 받고 값을 어디에도 출력하지 않는다.

**가드 시험 11건 green**(`tests/test_purge_datasets_guard.py` · DB 무의존) — 금지 표 불포함 ·
대장이 마지막 · 계보 간선 양방향 · ULID 아님/중복/연구실 형식 거부 · 기본값이 dry-run.

**집행 명령**(GO 뒤에 이 줄에 `--yes-delete` 만 붙인다) —

```
docker run --rm --network host --user 0 \
  -v /etc/colab/platform-owner-db.url:/s/owner.url:ro \
  -v /tmp/purge_datasets.py:/tmp/purge.py:ro \
  colab-v2/core-api:dev python /tmp/purge.py \
    --db-url-file /s/owner.url --lab 0000000000000000000000000A \
    --id 01M1FSEWYJVAV20VPMPT3EDDW9 --id 01M1C0F19DFGA80AM4HR63S1ND \
    --id 01M1H2DYX821ZR33SVVVQGJZ9R --id 01M1H4XH0XMQ7CNJ8256WP16SF \
    --id 01M1GR9N0DSK2AVRWJEBM5D0SD
```

## 6. 남은 전제 — 이 둘 없이는 열지 않는다

**⑴ Ted 의 명시 GO** — `〈349〉` 축자 「승인 범위 = **재적재 전 1회뿐** · 이후 삭제로 연장되지 않는다」이고
그 1회는 S3 삭제로 소진됐다. 물을 문장 —

> **「박홍진 시험 데이터셋 5건(`온보딩_박홍진_lecture_01` · `MOD15A2H.A2019281.h28v05.061.2020314051209` ·
> `RDR_CMP_HSR_PUB_202107031745.bin` · `RDR_CMP_HSR_PUB_202508131025.bin` · `rn15_sample`)의 DB 행
> 114줄을 지운다 — 바이트는 9/6 S3 삭제로 이미 없다(89키 전수 404). 지우나?」**

**⑵ 박홍진 통보** — 삭제 전 한 줄. 그의 데이터셋이 이미 비었고 행을 정리한다는 사실.

## 7. 사후 판정 기준 (집행할 때 쓴다)

**두 경로가 같아야 green** — ⑴ `colab_backup` 롤 전 연구실 재계수 = `d3_dataset` **14** ·
`d3_file` **434** · `d4_lineage_edge` **6** ⑵ API `listDatasets` **totalCount 14**.
⛔ 하나라도 어긋나면 백업(`§4` 키)으로 되돌린다.
