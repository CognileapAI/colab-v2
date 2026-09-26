---
name: ontology-round
description: 새로 올라온 자료를 대조해 검색 어휘·지명 관계·자료 카드 후보를 만들고, Ted 판정을 거쳐 반영하는 온톨로지 보강 회차를 돈다. 「회차 돌려」, 「새 자료로 온톨로지 보강」, 「올라온 자료 반영」처럼 명시로 요청할 때 쓴다. 단순 검색 질문이나 한 건 수정에는 쓰지 않는다.
---

# 온톨로지 보강 회차

목표는 하나다 — **실무자가 조건으로 찾을 때 새 자료가 실제로 걸리게 한다.** 어휘·관계·카드는 수단이다.
보고의 맨 위에는 늘 실무자 사례 점수판(`eval/k4-search/practitioner-conditions.json` 등급: 답 가능·부분·불가·초안 대기)을 둔다.

## 불변 규칙

- **정본에 없으면 만들지 않는다.** 값의 출처는 정본 문서·등록 칸(등록자 선언)·표준표 계산뿐이다. 추측은 **초안**이다.
- **값 확정은 Ted 판정이다.** 에이전트는 후보와 권고를 낸다. 판정 원문은 회차 intent 에 축자로 남긴다.
- **초안은 검색에 안 쓰인다.** 조건 검색은 `status='reviewed'` 만 읽는다. 초안은 측정(반사실 기여·역전)을 거쳐 승격한다.
- **DEV·운영 DB 에 쓰지 않는다** — 수집은 읽기 전용, 측정은 일회용 DB. dev 적재는 PR 머지 뒤 Ted 의 명시 GO 로만 한다.
- **확정값은 조용히 사라지지 않는다.** 적재 전 `reviewed_diff.py` 로 제거 0 을 증명하고, 승인된 제거만 따로 적는다.
- 사용자에게 보이는 문구에 내부 기법 이름(온톨로지·계보)을 쓰지 않는다.

## 설정 (처음 한 번)

`bash dev-package/tools/ontology-round/setup.sh` — 실행 환경을 만들고 준비 상태를 점검한다(0 = 준비 · 78 = 부족한 것을 줄마다 적음).
dev 수집 자격이 없으면 `--database-url` 로 로컬 DB 회차만 가능하다. 자세한 것은 `dev-package/tools/ontology-round/README.md`.

## 절차

1. **열기** — `bash dev-package/tools/ontology-round/round.sh init` (지난 회차 이후만 · 처음이면 `--all`).
   회차 폴더(레포 밖)에 `datasets.json`·`analysis.json`·`summary.md`·`state.json` 이 생긴다.
2. **읽기** — `summary.md` 와 `analysis.json` 을 읽는다. 자료마다 상태(no-evidence·partial·covered)·빈 칸·후보·사전에 없는 낱말이 있다.
3. **판단(에이전트 몫)** — 세 갈래로 가른다.
   - **어휘·지명·관계**: 사전에 없는 낱말 중 검색에 의미 있는 것(기관·관측 방식·변수·지명)을 골라
     「같은 말 / 안에 있다 / ~의 한 가지다」 후보로 만든다. 표기 잡음(조사·파일 이름 조각)은 버린다.
     정본 개정이 필요한 축(`dev-package/ONTOLOGY-SCOPE.md` §③)은 따로 표시한다.
   - **자료 카드 후보**: 등록 칸 선언(관측 간격·자료 유형·출처)과 설명 문장 파서 결과를 칸별로 정리한다.
     등록 칸 선언은 「등록자 선언」, 파서·계보·위경도 추론은 「초안 규칙」으로 출처를 나눈다.
   - **점수판 영향**: 이 회차가 실무자 사례 어느 것을 움직이는지 사례 ID 로 적는다. 움직이지 않으면 그렇다고 적는다.
4. **판정 페이지** — 결정마다 상황·선택지·권고를 `decisions.json`(형식은 `page.py` 머리말)에 쓰고
   `round.sh page <회차 폴더>` 로 `decision-page.html` 을 만든다. 쉬운 말로 쓰고, 권고에는 이유 한 줄을 붙인다.
   Ted 가 「결정 문장」을 붙여 주면 그것이 판정 원문이다.
5. **반영** — 판정대로 한다.
   - 어휘·관계: 새 시드 SQL + `db/ai/versions/` 새 리비전 + 드리프트 오라클 + 기준 TSV 를 **손으로** 갱신.
     어휘 오라클(`eval/k4-search/practitioner-lexical.json`)을 먼저 red 로 세우고 green 으로 옮긴다.
     지명 포함 관계를 바꾸면 `contracts/search/semantics.json` `regionWithin` 과 `region-within-drift` 게이트를 함께 맞춘다.
   - 정본 28건의 카드: `dev-package/tools/dataset_evidence_backfill.py` 로 payload 를 다시 만들고
     `round.sh measure <회차 폴더> <payload>` 로 측정한 뒤, 승격은 `--rehearse-promote` 리허설로 확인한다.
   - 새로 올라온 자료의 카드: 확정값은 자료 상세 화면의 검색 근거 편집기에서 등록자·Ted 가 확인해 저장한다.
     회차는 무엇을 넣을지(칸·값·출처)를 표로 넘긴다.
6. **PR** — 회차 intent(`dev-package/intent/<날짜>-ontology-round-<n>.md`, 판정 원문 포함)와 변경을 한 PR 로 올린다.
   회차 폴더에서는 `summary.md`·`decisions.json`·`decision-page.html`·측정 결과만 `dev-package/reports/ontology-rounds/<회차>/` 로 옮긴다
   (`datasets.json` 원문은 옮기지 않는다). 머지는 Ted.
7. **dev 적재** — Ted GO 뒤: 스냅숏 → dry-run(missing 0) → `reviewed_diff.py` 제거 0 증명 → 한 트랜잭션 적용 →
   재 dry-run 0 → dev 컨테이너 안 읽기 전용 조건 검색으로 사례 확인. 선례 `dev-package/reports/evidence-promotion/`.

## 완료 보고

점수판 전후 · 반영한 어휘/관계/카드 수 · 승인된 확정값 제거 목록 · 측정표 · PR · 남은 판정을 적는다.
점수판이 안 움직였으면 그 이유(자료 부재·술어 부재 등)를 사례 ID 로 적는다.
