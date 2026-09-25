# 1회차 승격 적용 계획 — platform-from-instrument · direct-observation-from-level

정본 판정: `dev-package/intent/2026-09-21-evidence-promotion.md` 「판정 결과 — 1회차(2026-09-26)」.
**dev 반영은 별도 GO 대기다. 이 문서의 명령은 아직 dev 에 대고 돌린 적이 없다.**

## 입력

| 파일 | sha256 |
|---|---|
| 원본 payload `dev-package/tools/generated/dataset-evidence-payloads.json` (dev 적재본) | `27c6ed87c178a8b6bcd686b7c55ad86391c659668e1888f1dbc789c7ff9192ca` |
| 승격 payload `promotion-plan/promoted-payload.json` (두 규칙 52칸을 `facts` 로 옮긴 사본) | `724dcbd6ad56ff0330df1e550dbb54d203bd5705bc3181cd68ddd858708c1941` |

승격 payload 는 아래 명령으로 다시 만들 수 있다(일회용 DB 에서, 전송 없음):

```bash
services/core-api/.venv/bin/python eval/k4-search/measure_draft_contribution.py <일회용 앱 롤 URL> \
  --i-know-this-is-disposable \
  --rehearse-promote platform-from-instrument,direct-observation-from-level \
  --output <새 디렉터리> --write-promoted-payload <새 경로>/promoted-payload.json \
  --promotion-note "dev-package/intent/2026-09-21-evidence-promotion.md 판정 결과 — 1회차(2026-09-26) · 규칙 단위 fast-track(결정 5)"
```

## 일회용 DB 리허설 결과 (2026-09-26)

- PUT 본문 리허설(`rehearsal/rehearse-platform-from-instrument+direct-observation-from-level.json`):
  파일 541 · 본문 541 · reviewed 사실 2071 → 2071 유지 · 승격 추가 1082 · 충돌 0 · 누락 0 ·
  `EvidenceWrite` 계약 검증 541 · 전송 0.
- 기존 적재기로 승격 payload 적용(일회용 DB · superuser URL — 적재기는 스코프를 걸지 않으므로
  앱 롤로는 RLS 에 가려 `missing 28` 이 된다):
  - dry-run: `{"datasets": 28, "missing": [], "evidence": 541, "evidence_unchanged": 2, "topic": 0, "source_label": 0, "files": 543, "draft_withheld": 58}`
  - 적용: 같은 셈
  - 다시 dry-run: `evidence 0 · evidence_unchanged 543` (멱등)
  - 변경 없는 2 = seq 9·10(DEM·Aspect) — 두 규칙의 초안이 없다.

## dev 적용 순서 (GO 뒤에만 · 명령은 `2026-09-18-dataset-metadata-backfill.md` 절차와 같은 꼴)

`COLAB_DEV_DB_URL` = 그 절차가 쓴 dev 적재 접속(적재기는 스코프를 걸지 않는다 — 앱 롤이면 RLS 로
0건이 된다). `<검토자 ULID>` = 판정자 계정(d1_account 에 있어야 한다).

### ① 되돌림 스냅숏
```bash
psql "$COLAB_DEV_DB_URL" -c "\copy (SELECT file_id, revision, status, facts::text, source_sha256, reviewed_by, reviewed_at FROM d3_search_evidence ORDER BY file_id) TO 'rollback-evidence-round1-before.tsv'"
sha256sum rollback-evidence-round1-before.tsv
```

### ② dry-run (아무것도 쓰지 않는다)
```bash
services/core-api/.venv/bin/python dev-package/tools/dataset_evidence_apply.py \
  --database-url "$COLAB_DEV_DB_URL" --reviewer <검토자 ULID> \
  --payloads dev-package/reports/evidence-promotion/round-1-2026-09-26/promotion-plan/promoted-payload.json --dry-run
```
기대 — `missing []` · `evidence 541` · `evidence_unchanged 2` · `topic 0` · `source_label 0` · `files 543` ·
`draft_withheld 58`. dev 의 본체 수가 543 이 아니거나 `missing` 이 비어 있지 않으면 **멈춘다**.

### ③ 적용 (한 트랜잭션)
```bash
services/core-api/.venv/bin/python dev-package/tools/dataset_evidence_apply.py \
  --database-url "$COLAB_DEV_DB_URL" --reviewer <검토자 ULID> \
  --payloads dev-package/reports/evidence-promotion/round-1-2026-09-26/promotion-plan/promoted-payload.json
```
같은 명령을 다시 dry-run 하면 `evidence 0 · evidence_unchanged 543` 이어야 한다.

### ④ 되돌림
원본 payload 를 같은 적재기로 다시 싣는다 — `facts` 가 승격 전 값으로 돌아간다(리비전은 1 오른다).
```bash
services/core-api/.venv/bin/python dev-package/tools/dataset_evidence_apply.py \
  --database-url "$COLAB_DEV_DB_URL" --reviewer <검토자 ULID> \
  --payloads dev-package/tools/generated/dataset-evidence-payloads.json
```
① 의 TSV 는 되돌린 뒤 facts 가 같은지 대조하는 근거다.

PUT 경로(`PUT /datasets/{id}/files/{id}/search-evidence`)로 하려면 파일마다 「현재 reviewed facts 전부 +
승격 사실」 전체 본문을 보내야 한다(전체 교체 · 비멱등). 리허설이 그 본문 541건을 계약으로 검증했다.
적재기 경로가 같은 결과를 멱등으로 내므로 이 계획은 적재기를 쓴다.
