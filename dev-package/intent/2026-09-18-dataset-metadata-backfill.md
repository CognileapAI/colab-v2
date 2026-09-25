# Intent: 자료 메타데이터 28건을 검색 근거로 적재한다
메타 — 발의자: 2026-09-15 DEV 검토 보고서 후속 2번 · 정리: Claude(lane-worker) · 작성 2026-09-18 · 승인 **승인 2026-09-18 (Ted, 「다 권고대로」)**

선행 intent `2026-09-18-practitioner-cases-ontology.md` §(iv) 가 후속 2번으로 인계한 자리다.
그 문서 축자 — 「14건 중 **14건**이 이 항목에 걸려 있다」.

## 문제
- 조건 검색(`d3_client_search.candidates`)은 `d3_search_evidence.facts` 만 읽는데 **그 표가 0건**이다.
  2026-09-15 보고서 축자 — 「파일별 검색 근거 d3_search_evidence는 해당 연구실 범위에서 0건이다.」
- 같은 보고서 축자 — 「살아 있는 28개 자료의 출처 source_label은 모두 NULL.」 / 「설명 행은 삭제 자료
  포함 30개이며 topic은 모두 NULL이다.」 주제 결합 검색이 0건인 것은 **정상 동작**이었다.
- 실무자 사례 14건은 비교·추천·순위를 요구하고, 그 전부가 자료 메타데이터 사실을 먹는다.
  어휘를 늘려도 붙을 자료 속성이 없었다.

## 원한 결과 (proposed outcome)
- O1. 적재 **전** 에 red 를 내는 조건 검색 오라클이 존재하고, 적재 후 green 으로 전이한 것이
  파일 변경으로 증명된다.
- O2. 28건의 검색 근거가 **정본 전재**로 실리고, 정본이 값을 고정하지 않은 칸은 **비어 있다**.
- O3. `topic`·`source_label` 이 같은 회차에 정합화되고, 주제 결합 검색의 0건이 수치로 닫힌다.
- O4. DEV 적용은 **사용자가 실행할 수 있는 명령과 되돌림 경로**로 남고, 에이전트는 DEV 에 쓰지 않는다.
- O5. 판정이 서지 않는 사례는 `mode:"blocked"` 로 남고 green 을 주장하지 않는다.

## 영향 범위
- 사용자 / 화면: 조건 검색 결과가 나타나기 시작한다. **새 UI 없음** — `SearchEvidenceEditor` 는
  이미 상세 화면에 연결돼 있다(`frontend/src/components/detail/FileList.tsx:286`).
  편집기의 주기 선택지에 「매시」 한 줄이 는다.
- 서비스 · 스키마 · 계약: `SearchEvidenceFacts.cadence` 에 `hourly` 값 하나. **스키마 무변경**
  (`cadence` 에는 DB CHECK 가 없다 — `db/platform/schema.sql`·`versions/**` 전수 grep 0건).
  새 표·새 열·새 마이그레이션이 없다.
- 계약 파괴 여부: **아니오**. `contract-breaking` = error 0 · warning 4(enum value added).

## 제약
- 「정본에 없으면 만들지 않는다」(`PLAN-SoT §9-㊴-②`).
- **DEV 자료·설정·배포를 변경하지 않는다.** 적재는 추가·정합화뿐이고 재시드가 아니다
  (`R-AI-SEARCH-RELEASE.md:14` — 자료 전체 초기화·재시드 금지).
- 모델 호출 0회. 이 회차의 모든 판정은 `SELECT` 로 선다.
- 생성물은 커밋하고 손으로 고치지 않는다.

## 사용자 판정 (2026-09-18 · Ted 「다 권고대로」 · 전부 정찰 보고의 권고대로)
1. **사실의 자리** — ㈎ `d3_search_evidence.facts`(`source_kind` evidence). 계약 무변경, 새 표 없음.
   ㈏ `source_kind='metadata'` projection 확장과 ㈐ 새 D3 표는 채택하지 않는다.
2. **부족한 3성분 중 무엇을 여는가** — ⓐ `cadence` enum 에 `hourly` **만** 연다.
   ⓑ pressure level 과 ⓒ 결측률 수치 술어는 **별도 결정으로 분리**한다.
3. **자동 추출을 어디까지 살리는가** — ㈐ 자동은 현행 유지, 28건 전부 **정본 전재**.
   파서 부활 없음. `measured_format` CHECK 무변경.
4. **등록 폼 변경 여부** — ㈎ 새 칸 없음. 상세의 `SearchEvidenceEditor` 동선만 연결한다.
5. **DEV 쓰기 승인** — ㈎ 로컬 재현 환경에서만 검증하고 **DEV 적재는 별도 승인**.
6. **불가 3건의 처리** — ㈎ `mode:"blocked"` 로 두고 green 을 주장하지 않는다.

## 설계트리 (grill-me 결과)
- Q1 자료 사실을 어디에 싣는가 → A **㈎ `d3_search_evidence.facts`**. 조건 검색이 읽는 자리가
  그것 하나이고 계약·서버·편집기 3층이 이미 서 있다 (권장안 수용 / 반대 관점: `metadata`
  projection 을 쓰면 지식 수명주기와 한 축으로 묶이지만, `d3_search_facts.load_source` 의
  metadata 술어 9종이 `Evidence.oneOf` 15종 어디에도 없어 계약 개정이 선행한다)
- Q2 15종으로 부족한 3성분을 이 회차에 여는가 → A **ⓐ 만**. `hourly` 는 사례 #1-4·#2-4 가 직접
  부르고 정본 축자(seq 16 「각 24시각이다」)가 값을 고정한다 (권장안 수용 / 반대 관점: ⓒ 결측률이
  사례 3건에 걸려 있는데 그대로 남는다 — 「부분」·「deferred」로 드러내는 것으로 갈음했다)
  - Q2a `hourly` 를 여는 것이 파괴인가 → A **아니다.** 값 추가뿐이고 `contract-breaking` error 0
  - Q2b 마이그레이션이 필요한가 → A **아니다.** `cadence` 에 DB CHECK 가 없다(전수 grep 0건).
    0042 리비전도 드리프트 오라클도 만들지 않는다
- Q3 자동 추출(파서)을 살리는가 → A **㈐ 살리지 않는다.** 28건의 기간은 `canonical-metadata.json`
  에 `basis` 까지 확정돼 있어 파서 없이도 정확하다 (권장안 수용)
- Q4 등록 폼에 칸을 더하는가 → A **아니다.** 검색 사실은 파일 단위라 데이터셋 단위 폼과 축이 다르다
  - Q4a 상세 동선 연결은 몇 줄인가 → A **0줄.** `SearchEvidenceEditor` 가 이미
    `FileList.tsx:286` 에서 렌더된다 — 더할 링크가 없어 UI 를 건드리지 않았다
- Q5 DEV 에 쓰는가 → A **쓰지 않는다.** 일회용 postgres 에서만 검증하고 DEV 적용 명령을
  아래 절로 넘긴다 (권장안 수용)
- Q6 판정이 안 서는 사례는 → A **`mode:"blocked"`**. 자료 부재는 코드로 못 고친다
- Q7 규칙 추론 필드를 실어도 되는가 → A **싣는다 — 정찰 계획 §6-2 가 `platform`·
  `representation`·`directObservation`·`interpolated` 를 「추론(규칙)」으로 세웠고 §6-3 이
  `locator` 에 `rule:<규칙ID>` 를 박아 되돌림 경로를 남기라고 적었다.** 이 회차는 그 규칙 ID 를
  payload 의 `provenance` 에 필드마다 남긴다 (반대 관점은 남는다: 규칙은 정본 전재가 아니다.
  그래서 `status` 는 행 단위로 `reviewed` 지만 **어느 칸이 규칙인지 읽을 수 있게** 적었고,
  규칙 5종의 정의를 payload 머리의 `rules` 에 박아 두었다)
- Q8 정본이 값을 말하지 않는 칸은 → A **비운다.** `source_label` 은 28건 중 9건만 찼고
  19건은 정본 문면에 원천 기관이 없다. `region` 은 한반도를 문면으로 고정한 자료가 0건이라
  「한반도」 술어를 green 근거로 쓰지 않았다

## 완료 정의
1. `eval/k4-search/practitioner-conditions.json` 과 그 pytest 가 존재하고, 적재 **전** 상태에서
   **red** 다. ⭑ 실측 — 11 failed / 4 passed, 실패 사유는 전부 「근거 적재 0건」.
2. `hourly` 가 계약·생성물 3종·서버 검증·자연어 해석·편집기에 같은 커밋으로 들어간다.
   ⭑ 실측 — `generated-up-to-date` green(등기부 20건), `contract-breaking` error 0.
3. 28×본체파일 payload 가 정본에서 생성되고 서버 `EvidenceFacts` 검증을 전건 통과한다.
   ⭑ 실측 — 데이터셋 28 · 사실 230칸 · invalid 0.
4. 적용기가 **멱등**이다. ⭑ 실측 — 1회차 evidence 28 · 2회차 evidence 0 / unchanged 28.
5. 적재 후 오라클이 **green**. ⭑ 실측 — 15 passed. 가능 8 · 부분 3 · blocked 3.
6. 전/후가 수치로 기록된다. ⭑ `eval/k4-search/README.md` 의 「2026-09-18 재측정」 절.
7. DEV 적용은 **하지 않는다.** 명령·전제·되돌림만 아래 절에 남는다.

### 완료 주장 전 green 이어야 하는 게이트
| 게이트 | 왜 |
|---|---|
| `service-tests-core-api` | 새 오라클 ＋ evidence·조건 검색 회귀(`test_search_evidence.py`·`test_search_numeric_quality.py`) |
| `service-tests-ai-service` | 생성물 `knowledge_wire.py` 가 AI 쪽에도 복제된다 |
| `generated-up-to-date` | `fe-core.ts`·core/ai `knowledge_wire.py` 재생성 일치 |
| `seam-consistency` | 계약 개정 뒤 이음매 대조 |
| `schema-diff` | 「스키마 무변경」의 증명 |
| `migration-drift` | 새 리비전이 없다는 것의 증명(체인 무변경) |
| `rls-coverage` | `d3_search_evidence` RLS 전제 유지 |
| `contract-breaking`(선언 밖 추가 실행) | enum 값 추가가 파괴가 아님의 증명 |

종료코드 — green **0** · 판정 실패 **1** · 준비 실패 **78**. 준비 실패를 성공으로 보고하지 않는다.

## DEV 적용 명령 (사용자 실행 · Ted 결정 5 의 「별도 승인」 자리)

⚠ **에이전트는 이 명령을 실행하지 않았다.** 아래는 전부 사용자가 승인한 뒤 직접 도는 절차다.

### 전제
- `services/core-api/.venv` 가 이 체크아웃에 있다(`sqlalchemy`·`psycopg` 가 필요하다).
- DEV 플랫폼 DB 접속 URL. **앱 롤이 아니라 쓰기 권한이 있는 롤**이어야 한다
  (`d3_dataset`·`d3_dataset_description`·`d3_search_evidence` 에 UPDATE/INSERT).
  URL 은 로그·커밋·채팅에 넣지 않는다.
- `--reviewer` 는 **DEV 의 `d1_account` 에 실재하는 검토자 계정 ULID** 다(FK).
  없는 ID 를 주면 트랜잭션이 통째로 실패한다 — 그것이 맞는 동작이다.
- 자료 이름이 정본 28건과 같아야 한다. 다르면 그 건은 `missing` 으로 빠지고 **적재되지 않는다**.

### ① 되돌림 스냅숏 (적용 전에 반드시 먼저)
```bash
psql "$COLAB_DEV_DB_URL" -c "\copy (SELECT dataset_id, topic FROM d3_dataset_description) TO 'rollback-topic.tsv'"
psql "$COLAB_DEV_DB_URL" -c "\copy (SELECT id, source_label FROM d3_dataset) TO 'rollback-source-label.tsv'"
psql "$COLAB_DEV_DB_URL" -c "\copy (SELECT file_id FROM d3_search_evidence) TO 'rollback-evidence-before.tsv'"
```

### ② 생성물 재생성과 셈 확인 (아무것도 쓰지 않는다)
```bash
python3 dev-package/tools/dataset_evidence_backfill.py
services/core-api/.venv/bin/python dev-package/tools/dataset_evidence_apply.py \
  --database-url "$COLAB_DEV_DB_URL" --reviewer <검토자 계정 ULID> --dry-run
```
기대 출력 — `{"datasets": 28, "missing": [], "evidence": 28, "evidence_unchanged": 0, "topic": 28, "source_label": 9, "files": <DEV 의 본체 파일 수>}`.
`missing` 이 비어 있지 않으면 **멈춘다** — 이름이 어긋난 것이고, 이름으로 못 찾은 자료에
근거를 붙이지 않는다.

### ③ 적용 (한 트랜잭션)
```bash
services/core-api/.venv/bin/python dev-package/tools/dataset_evidence_apply.py \
  --database-url "$COLAB_DEV_DB_URL" --reviewer <검토자 계정 ULID>
```
같은 명령을 다시 돌리면 `evidence 0 / evidence_unchanged N` 이 나온다(멱등).

### ④ 되돌림
```bash
# 이번 적용이 만든 근거만 지운다 — ① 의 스냅숏에 없던 file_id 가 그것이다
psql "$COLAB_DEV_DB_URL" -c "\copy rollback_evidence_before FROM 'rollback-evidence-before.tsv'"
psql "$COLAB_DEV_DB_URL" -c "DELETE FROM d3_search_evidence e WHERE NOT EXISTS (SELECT 1 FROM rollback_evidence_before b WHERE b.file_id = e.file_id)"
# topic·source_label 은 ① 의 TSV 를 임시 표로 올려 UPDATE 로 되돌린다
```
`d3_search_evidence` 는 `d3_file` 에 `ON DELETE CASCADE` 로 달려 있고 자료 자체는 건드리지
않으므로, 되돌림이 자료·파일·계보를 지우는 일은 없다.

## 후속 — 별도 결정으로 분리한 항목
1. **pressure level**(사례 #2-6). `SearchEvidenceFacts` 에 성분 신설 → 계약 개정 ＋ 생성물
   재생성 ＋ `knowledge-lifecycle.json` 의 `Evidence.oneOf` 동반 개정. Ted 결정 2-ⓑ.
2. **결측률 수치 술어**(사례 #2-7·#1-1·#2-1). `d3_dataset_variable.missing_rate` 가 `text` 이고
   `d3_client_search` 에 술어가 없으며, `test_search_numeric_quality.py` 골든이 품질 질의의
   후보 확대를 **의도적으로 막는다**. 세 자리를 함께 여는 결정이 필요하다. Ted 결정 2-ⓒ.
3. **헤더 파서 부활**(`services/pipeline-worker/src/colab_pipeline/d5/parse.py`, stage2 대기).
   신규 업로드가 `variables`·`period`·`crs`·`grid` 를 자동으로 얻는 자리다. GRIB 은
   `cfgrib`/`eccodes` 추가가 선행한다. `stage2-markers` 게이트가 표지 해제를 검사한다. Ted 결정 3.
4. **`measured_format` CHECK 4값 → 7값**. GRIB·HDF4·Binary 5건이 자동 측정 밖에 있다.
   새 리비전이 필요하다. Ted 결정 3 의 「이후 ㈏」.
5. **AWS·disdrometer·CCTV 자료 확보**(사례 #1-5·#2-5). 코드 문제가 아니라 자료 부재다.
   2026-09-15 후속 5번 축자 — 「별도 승인된 평가 자료가 있어야 검증 가능하다」.
6. **시간 주기 enum 의 빈칸** — HSR 5분·GK-2A LST 10분·LULC 연 단위는 정본이 값을 말하는데
   `cadence` enum 에 자리가 없어 **적지 않았다**. 여는 것은 위 1·2 와 같은 계약 개정이다.
7. **`region` 의 한반도 부재** — 28건 중 한반도를 문면으로 고정한 정본이 0건이라 지명 술어가
   green 근거로 서지 않는다. 자료 등록 쪽에서 공간 범위를 받는 것이 선행이다.

## 미해결 질문
- DEV 의 실제 본체 파일 수가 28건보다 많다(정본 계수로 470여 건). 적용기는 **데이터셋의 모든
  본체 파일**에 같은 근거를 싣는다 — 데이터셋 단위 사실이라 그것이 맞지만, DEV 실행 전
  `--dry-run` 의 `files` 수를 사람이 확인해야 한다.
- 원격 DEV DB 를 직접 질의하지 못했다. 자료 이름이 정본 28건과 같은지는 `--dry-run` 의
  `missing` 으로만 확인된다.
- `measure.py`(AI 그래프 확장)는 이 회차에서 한 글자도 움직이지 않았다. 온톨로지 쪽 재측정은
  선행 intent 의 몫이다.

## 범위 밖 (명시 제외)
- DEV·staging 자료 수정, 재시드, 배포, 커밋·push·PR 게시.
- 새 D3 표, 새 열, 새 마이그레이션.
- 등록 폼 개편, `topic` 칸 신설.
- 실제 LLM 호출·모델 품질 평가(후속 4번의 몫).
- 라운드 1~2 의 온톨로지 파일(`db/ai/seed/**`·`db/ai/tools/**`).

## 확인
- Ted 확인 문장(원문 그대로): **「다 권고대로」(2026-09-18)** — 결정 1=㈎, 2=ⓐ만, 3=㈐,
  4=㈎, 5=㈎, 6=㈎.
- 프론티어 공집합 확인: 미수행.
- 재개봉 금지: **아니오** — 이 회차는 기존 판정을 뒤집지 않는다. `SearchEvidenceFacts` 15종은
  2026-09-13 사용자 승인분이고 값 하나를 더할 뿐이다.

## 참조
- 선행 intent: `dev-package/intent/2026-09-18-practitioner-cases-ontology.md` §(iv)
- 관측: `dev-package/reports/ai-search-dev-review-20260915.md` `:56`(후속 2번)
- 사례 원문: `eval/k4-search/practitioner-cases.md`
- 오라클: `eval/k4-search/practitioner-conditions.json` · `services/core-api/tests/test_practitioner_conditions.py`
- 생성기·적용기: `dev-package/tools/dataset_evidence_backfill.py` · `dataset_evidence_apply.py`
- 생성물: `dev-package/tools/generated/dataset-evidence-payloads.json`
- 측정: `eval/k4-search/measure_evidence.py` · `eval/k4-search/README.md` 「2026-09-18 재측정」
- 정본: `dev-package/tools/dev-seed/canonical-metadata.json` · `plan-manifest.yaml` ·
  `dev-package/reports/reference-data/datasets-md/**/DATASETS.md`
- 계약: `contracts/seams/fe-core.yaml` `SearchEvidenceFacts` · `contracts/schemas/knowledge-lifecycle.json`
- spec: 미작성.

---

# 2회차 (2026-09-21)

⭑ **위 절들은 1회차 기록이다. 한 글자도 고치지 않았다.** 이 절이 2회차에 바뀐 것만 적는다.

## 사용자 판정 (2026-09-21 · Ted · 축자)

> 1. 다 초안으로 넣는다. 실제로 얼마나 히트했냐를 측정하고 이에 따라 승격 또는 폐기하는 구조를
>    가져야한다. (온톨로지를 만들때 이를 검토하는 형태)

> 2. 가를 넣고, 보조하는 용도로 나를 해야하지 않을까?

> 3. 가 권고대로

- **결정 1** = 1회차 미해결의 마지막 줄(규칙 추론 필드)에 대한 판정. 규칙 추론값은 전부 **초안**이다.
- **결정 2** = 지역 문면(1회차 후속 7번). ㈎ 정본 문면으로 지명을 세우고 ㈏ bbox 로 **보조** 검증한다.
- **결정 3** = cadence 의 빈칸(1회차 후속 6번). ㈎ `5min`·`10min`·`yearly` 를 연다.

## 무엇이 바뀌었나

### ① 규칙 추론값 → 초안 (결정 1)

`platform`·`representation`·`directObservation`·`interpolated` 와 규칙으로 이어받은
`nativeResolutionM`(seq 3)·`region`(seq 16) — 110칸이 `draftFacts` 로 갈라졌다.

⚠ **초안 행을 따로 쓰지 못한다.** `d3_search_evidence` 는 `file_id` 가 PRIMARY KEY 이고
`status` 가 **행 단위**다(`db/platform/schema.sql:813`). 한 파일이 reviewed 사실과 draft 사실을
동시에 가질 수 없고, 행을 통째로 `draft` 로 내리면 **정본 전재 사실까지** 조건 검색에서 사라진다.
그래서 초안은 `rule:<규칙ID>` locator 를 단 채 **생성물에만** 남고 적용기는 `draft_withheld` 로
칸 수만 보고한다. 이 제약은 1회차가 열어 둔 자리가 아니라 표 구조가 정한 것이다.

승격·폐기 **구조 자체는 이 회차가 만들지 않는다**(별도 intent — 조사자가 초안 작성 중).
이 회차가 남기는 것은 그 구조가 찾아올 자리와 셈뿐이다:
`dev-package/tools/generated/dataset-evidence-payloads-rule-summary.json` 과 생성기 stdout 의
규칙별 셈 — platform 26 · representation 28 · directObservation 26 · interpolated 28 ·
native-resolution-carried 1 · region-from-registration-note 1 · bbox-korea-peninsula 0.

**오라클이 그만큼 green 주장을 거둔다.** 1회차 가능 8 · 부분 3 · blocked 3 →
2회차 **가능 3 · 부분 5 · blocked 3 · blocked_draft 3**. 새 등급 `blocked_draft` 의 사유 문구는
「규칙 추론값은 초안 — 사람 확인 후 승격」이다. pytest 는 그 등급을 blocked 과 같은 자리에서
「green 을 주장하지 않는다」로 검사한다(`test_blocked_cases_claim_nothing`) — 초안 사실 위에
서 있던 probe 8개는 **삭제가 아니라 등급으로** 드러난다. 승격되면 그대로 되살아난다.

### ② 지역 — 후보표만 (결정 2)

**정본 `DATASETS.md` 4건을 고치지 않았다.** 대신 Ted 확인용 후보표를 만들었다 —
`dev-package/reports/practitioner-place-candidates-260921.md`(28행). 후보가 선 행은 **8행**
(직접 3 = seq 7·13·14 · 간접 5 = 기관 문면뿐인 seq 1·2·6·19·20)이고 나머지 20행은 「?」다.

보조(㈏)는 생성기의 `region_from_bbox` 로 구현했다 — bbox 가 한반도 상자(위도 33~39 ·
경도 124~132) 안에 **온전히** 들어갈 때만 `rule:bbox-korea-peninsula` 초안 `region` 을 만든다.
보조이므로 값이 서도 초안이고 reviewed `region` 은 정본 문면에서만 온다.
⭑ **지금 만든 초안이 0건이다** — `d3_dataset_grid_profile` 에도 `canonical-metadata.json` 에도
bbox 가 0건이다. 규칙은 서 있고 먹일 값이 없다.

### ③ cadence 3값 (결정 3)

`5min`·`10min`·`yearly` 를 `hourly`(1회차 `cade1f40`)와 **같은 방식**으로 열었다 —
계약 ＋ 생성물 3종 재생성 ＋ 서버 검증 ＋ 자연어 해석 ＋ 근거 문면 표 ＋ 편집기 선택지.
값은 정본 축자로만 채웠다 — seq 1 「시/공간해상도 5분 / 0.5 km」 · seq 17 「10분 간격으로 담은」 ·
seq 11 「연 단위 100 m 토지피복지도」. `contract-breaking` error 0 · warning 12(enum value added).

seq 19·20(HSR 합성)과 seq 18(LST 변환 결과)은 **정본이 주기를 말하지 않아 비웠다** —
같은 계열이라고 부모의 주기를 자식에 적지 않는다(`PLAN-SoT §9-㊴-②`).

## 2회차 완료 정의와 실측

1. 규칙 추론값이 `reviewed` 로 실리지 않는다. ⭑ 실측 — reviewed 123칸 · draft 110칸.
   `test_rule_inferred_facts_are_never_loaded_as_reviewed` 가 생성물에서 그 경계를 검사한다.
2. 초안마다 `rule:<ID>` locator 가 남는다. ⭑ 같은 시험이 검사한다. 규칙별 셈이 JSON 으로 나간다.
3. 보조 bbox 규칙이 한반도 상자 안일 때만 말한다. ⭑ `test_bbox_auxiliary_rule_only_speaks_inside_the_peninsula`.
4. cadence 3값이 계약·생성물·서버·편집기에 같은 커밋으로 들어간다. ⭑ `generated-up-to-date` green.
5. 오라클이 초안 위에서 green 을 주장하지 않는다. ⭑ 17 passed · blocked_draft 3.
6. 전/후가 수치로 기록된다. ⭑ `eval/k4-search/README.md` 「2026-09-21 재측정」 절.
7. 정본과 DEV 를 고치지 않는다. ⭑ `DATASETS.md` 무변경 · DEV 제품 DB 에 쓴 것 0건.

## 2회차가 남기는 의문

- **승격 구조가 없는 동안 조건 검색은 좁아졌다.** platform·directObservation 축이 0건이 되었고
  그것은 사용자가 보기에 **후퇴**다. 「초안을 쓰지 않는 것」과 「검색이 되는 것」을 함께 만족시키려면
  승격 단계가 서야 한다 — 그 intent 가 언제 서는지가 이 회차 밖의 의존이다.
- **초안을 DB 에 둘 자리가 없다.** 지금 초안은 생성물 파일에만 있어 「얼마나 히트했냐」를 잴
  대상이 제품 DB 에 존재하지 않는다. 승격 구조는 아마 `d3_search_evidence` 밖의 자리
  (파일 단위 PK 가 아닌 표)를 필요로 한다 — 그 설계는 이 회차가 하지 않았다.
- **지역 후보 8/28 중 5건이 「기관 이름」 근거다.** 기상청 = 남한, GK-2A = 한반도/동아시아 —
  둘 다 정본이 말하지 않는다. 승격해도 초안 등급이 맞는지 Ted 판정이 필요하다.
- **bbox 가 어디에도 없다.** 보조 규칙은 죽은 채로 서 있다. DEV 의 `d3_dataset_grid_profile` 을
  이 회차에서도 직접 질의하지 않았다(결정 5 ㈎ 유지) — DEV 에 값이 있으면 후보표를 다시 채워야 한다.
- `schema-diff` 의 블로커 72 는 이번 회차도 DB 객체를 하나도 만들지 않았다는 사실과 무관하다.

## 2회차 커밋

| | 제목 |
|---|---|
| C1 | cadence 에 5min·10min·yearly 를 더해 정본이 말하는 주기를 적을 수 있게 한다 |
| C2 | 규칙 추론값을 초안으로 내리고 오라클에서 그만큼 green 주장을 거둔다 |
| C3 | 정본을 고치지 않고 28건의 지역 후보표를 Ted 확인용으로 남긴다 |
| C4 | 2회차 재측정을 기록하고 intent 에 결정 3건을 축자로 남긴다 |
