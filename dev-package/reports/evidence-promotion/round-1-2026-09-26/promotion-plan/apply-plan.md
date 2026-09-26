# 1회차 승격 적용 계획 — platform-from-instrument · direct-observation-from-level · native-resolution-carried

정본 판정: `dev-package/intent/2026-09-21-evidence-promotion.md` 「판정 결과 — 1회차(2026-09-26)」.
Ted 2026-09-26 「전부 권고대로」 — ① dev 반영 GO ② native-resolution-carried 도 승격(규칙 3개)
③ 공용 AI 게이트 DB 재구성은 별도 레인 몫.

## 입력

| 파일 | sha256 |
|---|---|
| 원본 payload `dev-package/tools/generated/dataset-evidence-payloads.json` (dev 적재본 · 되돌림 기준) | `27c6ed87c178a8b6bcd686b7c55ad86391c659668e1888f1dbc789c7ff9192ca` |
| 승격 payload `promotion-plan/promoted-payload.json` (세 규칙 53칸을 `facts` 로 옮긴 사본) | `41f488a42ffb07c1c64d4460ea86a6b98c72b63494ec45291f72f5c73561c6fc` |
| 적재기 `dev-package/tools/dataset_evidence_apply.py` | `b7d4f327af609afd14e17357aa9d56b0c3402743f136dfe14f025d6ff94ff017` |

두 규칙판 승격 payload(sha256 `724dcbd6…`, 52칸)는 이 세 규칙판으로 대체됐다(같은 경로 · git 이력에 남음).

승격 payload 재생성(일회용 DB 에서, 전송 없음):

```bash
services/core-api/.venv/bin/python eval/k4-search/measure_draft_contribution.py <일회용 앱 롤 URL> \
  --i-know-this-is-disposable \
  --rehearse-promote platform-from-instrument,direct-observation-from-level,native-resolution-carried \
  --output <새 디렉터리> --write-promoted-payload <새 경로>/promoted-payload.json \
  --promotion-note "dev-package/intent/2026-09-21-evidence-promotion.md 판정 결과 — 1회차(2026-09-26) · 규칙 단위 fast-track(결정 5) · native-resolution-carried 포함(Ted 2026-09-26 「전부 권고대로」)"
```

## 일회용 DB 리허설 (2026-09-26 · 새 컨테이너 · `setup-db.sh` 스키마·시드 → `--seed-dev-like`)

- 시드 재측정: 데이터셋 28 · 본체 543 · 계보 18 · 적재 evidence 543 · topic 3 · source_label 9 ·
  draft_withheld 110 · 평가 118 · 경로 1 28/17 · 경로 2 9/9 · 규칙 기여 platform 8/0 · directObservation 2/0 ·
  nativeResolution 2/0 · 지문 전후 동일 — 1회차 표와 같다.
- PUT 본문 리허설(`rehearsal/rehearse-platform-from-instrument+direct-observation-from-level+native-resolution-carried.json`):
  승격 사실 53 · 데이터셋 26 · 파일 541 · 본문 541 · reviewed 사실 2071 → 2071 유지 · 승격 추가 1083 ·
  충돌 0 · 누락 0 · `EvidenceWrite` 계약 검증 541 · 전송 0 · ok.
- 적재기(superuser · `PGOPTIONS=-c app.current_lab=<A 연구실>`):
  dry-run datasets 28 · missing 0 · evidence 541 · evidence_unchanged 2 · topic 0 · source_label 0 · files 543 ·
  draft_withheld 57 → 적용 같은 셈 → 재 dry-run evidence 0 · evidence_unchanged 543(멱등).
  변경 없는 2 = seq 9·10(DEM·Aspect) — 세 규칙의 초안이 없다.
- 적용 뒤 facts 키 보유 행: platform 541 · directObservation 541 · nativeResolutionM 45 (전 543행).
- 경로 1 조건 검색(`d3_client_search.candidates`) 적용 뒤: platform=ground 8건 · directObservation=true 20건 ·
  maxResolutionM=5000 6건(hsr_sample 포함).

## dev 적용 순서 (2026-09-18 · 2026-09-25 적재와 같은 꼴 — dev 호스트에서 실행)

적재기는 스코프를 걸지 않는다 — 앱 롤이면 RLS 로 `missing 28` 이 된다. 그래서 dev 호스트에서
배포 이미지 `colab-v2/core-api:dev-<sha>` 를 `--network colab-v2-dev_default` 로 띄우고
`/etc/colab/platform-owner-db.url`(소유자 롤)과 `PGOPTIONS=-c app.current_lab=00000000000000000000HYMETS` 로 돈다.
dev.env 변경·서비스 재시작·reset·재시드 없음. 읽기 계수는 `colab_backup`(BYPASSRLS · `row_security=off`)로 한다.

1. 되돌림 스냅숏 — `colab_backup` 으로 `d3_search_evidence` 전 543행(file_id · revision · status · source_sha256 ·
   facts · reviewed_by · reviewed_at)을 `\copy … TO STDOUT` 해 dev 호스트 파일과 로컬 사본
   (`~/.local/state/colab/evidence-promotion-<ts>/`, 저장소 밖)에 둔다. sha256 대조.
2. 적재기·승격 payload·원본 payload 를 dev 호스트 `/var/tmp/colab-evidence-promotion-<ts>/dev-package/tools/` 로 보낸다(sha256 대조).
3. dry-run — 기대 missing 0 · evidence 541 · evidence_unchanged 2 · files 543. missing 이 0 이 아니거나
   리허설과 2행 넘게 다르면 **멈춘다**.
4. 적용(한 트랜잭션).
5. 확인 — 재 dry-run evidence 0 / unchanged 543 · 행 수 543 · facts 키 표본 · 경로 1 조건 검색 전후.

검토자(`--reviewer`) = 판정자 Ted 의 dev 계정 ULID(d1_account FK). 적재기 문서는 FK 만 요구한다.
적용된 541행의 reviewed_by 가 이 ULID 로 바뀌고, 변경 없는 2행은 종전 검토자를 유지한다.

## 되돌림

원본 payload(`27c6ed87…`)를 같은 적재기·같은 접속으로 다시 싣는다 — facts 가 승격 전 값으로 돌아간다
(리비전은 1 더 오른다). 스냅숏 TSV 는 되돌린 뒤 facts 가 같은지 대조하는 근거다.
실제 명령과 결과는 PR 본문과 intent 「판정 결과」 절에 적는다.

PUT 경로(`PUT /datasets/{id}/files/{id}/search-evidence`)는 파일마다 전체 본문(비멱등 · 업로드·편집 권한)을
요구한다. 리허설이 그 본문 541건을 계약으로 검증했고, 같은 결과를 멱등으로 내는 적재기를 쓴다.
