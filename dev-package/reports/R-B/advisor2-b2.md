# 게이트 ② 수용 검토 — WU-B2 `p3-variable-rows` (3889c30..4e3247e)

For:
- 표·색인·정책·계약·서버·FE·시험이 한 회차에 섰고 오라클이 동작 기반(거부 확인 · 대조군 red). 폐기 시 5커밋 1,829행 재작업.
- 계약 해석 정확 — `DatasetCreate.required: [uploadId, name, summary]`(변수 optional), `[]`→400, FE `variablesPayload` 가 빈 표면 열쇠 미송신 → 변수 없는 등록 경로 무회귀.
- RLS = 형제 표와 자구 동일(`schema.sql:1090-1098` vs `:1085-1088`), FORCE, 시험 `t_app` NOBYPASSRLS 롤로 측정. 체인 = 0016 만 0015 를 revises, head 1.

Against:
- **이관이 실배포에서 0행이다.** `0016` UPGRADE ⑵ 는 `d3_dataset_autometa`(FORCE RLS · `schema.sql:1085-1086`)를 읽는데 마이그레이터 롤은 `colab_owner NOSUPERUSER NOBYPASSRLS`(`db-bootstrap.sh:33` · `compose.yml:156 「소유자 롤로 돈다」`). `app.current_lab` 미설정 → `current_lab_id()` NULL(`schema.sql:41-49`) → SELECT 0행 → INSERT 0행, 오류 없음. `0013_ra1_ext_interval_period.py:38-40, 116-117` 이 정확히 이 이유로 `NO FORCE` 구간을 열었고 0016 산문이 그것을 인용하면서 **대상 표(새 표 정책 시점)에만 적용**했다.
- 드리프트 ㈑ 는 `psql -U postgres`(superuser · RLS 무조건 우회)로 델타를 적용해 green — 수용 기준 4 「순서대로 이관」의 증거가 아니다. 0013 식 「돌았다가 아니라 맞다를 센다」 DO 단언도 0016 에 없다.
- `_variables_payload` 의 0행→배열 퇴행이 이 결함을 **상세 화면에서 은폐**한다(이관 0행이어도 종전 이름 표시). 요청되지 않은 초과분이 결함 탐지를 막는 방향으로 작동.

Verdict: **DB 이관 단계 reject(재작업 후 재게이트) · 계약·서버·FE·시험 approve.** 대장 `done` 은 수정 커밋 뒤 유효.

Risks:
1. 동시 PATCH 2건 — `replace_variables` 에 행 잠금 없음(`FOR UPDATE` 는 삭제 경로 `:792`·`:968` 만). T2 의 INSERT 가 T1 커밋 행과 PK 충돌 → IntegrityError → 500.
2. M-10 전 새 변수명 검색·자동완성(`SUGGESTABLE_FIELDS` `:343-347`) 미반영 — 레인 표시·시험 고정, 수용. dev 13행에는 사람이 적은 새 변수가 늘어날수록 검색 불일치 확대.
3. `variables: null` 처리 비대칭 — 생성 `_human_metadata` 는 `None` 을 조용히 버림(`ingestion.py:426`), 수정은 400. 계약은 둘 다 비허용.

Missed (intent 대조 · 미달/초과):
- 미달 ① 「배열 이관이 순서대로」 — 실배포 롤에서 미성립(위). ② 「변수명 검색이 종전과 같이」 — 새 행 미성립(M-10 · 레인 표시 · 수용).
- 초과 ① 읽기 퇴행(0행→배열) ② `DatasetCreate.variables` `null` 제거(파괴 14건 중 1건 · 승인 범위 「문자열→객체 배열」 밖의 축소) ③ `ordinal` 1-based 확정 ④ 시드 5행 · `_VARIABLE_FIELDS` 런타임 additionalProperties 검사.
- 되돌림 손실(단위·값 범위·결측률·대표) — 마이그레이션 산문·세션 노트에 기재. 라운드 파일 §3-㉴ 는 「컬럼 삭제 금지」만 말함 → 〈N〉 원장 ④ 에 「되돌림 = 표 DROP · 사람 입력 3칸＋대표 소실 · 정규 경로는 소비 중단」 축자 기입 필요(오케스트레이터).
- `frontend/test/rev1-keep-regression.test.tsx:213` `variables: ['강수량']` 문자열 배열 잔존 — `as unknown as` 캐스트로 typecheck 맹점. 소비자 178 계수에 낡은 형상 1건 포함.
- `db/platform/tests/*-drift.sh` 가 어느 게이트에도 없음(레인 후속 1) — §3-3-⑷ 게이트 승격 대상. 승격해도 superuser 실행이면 이번 결함류를 못 잡음.
- 같은 데이터셋 안 변수명 중복 허용(name UNIQUE 없음) — PRD 무언급, 결정 기록 없음.

Fixes:
- **[병합 전 필수]** `0016` UPGRADE ⑵ 앞 `ALTER TABLE d3_dataset_autometa NO FORCE ROW LEVEL SECURITY;`, INSERT 뒤 `FORCE` 복원 ＋ 0013 식 DO 단언 2건 — ⓐ `relforcerowsecurity = true` 되묻기 ⓑ `count(d3_dataset_variable) = sum(공백 제외 원소 수)` 불일치 시 RAISE. 
- **[병합 전 필수]** `0016-drift.sh` ㈑·㈑-b — 델타 적용을 `NOSUPERUSER NOBYPASSRLS` 소유자 롤(`CREATE ROLE t_owner … ; ALTER DATABASE/TABLE OWNER` 또는 `SET ROLE`)로 실행해 「0행 이관 = red」 대조군 1건 추가(수정 전 red 를 축자로 세션 노트에 기록).
- **[병합 전 필수]** `service-tests-core-api`·`schema-diff`·`migration-single-head`·드리프트 재실행 축자, 대장 `done` 유지 여부 재판정.
- 권고: `replace_variables` 첫 줄에 `d3_dataset` 행 `FOR UPDATE` 잠금(기존 헬퍼 `:968` 재사용). `_human_metadata` 의 `variables: null` 을 `[]` 와 같이 400 으로 통일. `rev1-keep-regression.test.tsx:213` 객체 배열로 교정. M-10(WU-B7) 지시문에 `SUGGESTABLE_FIELDS`·`test_registration_does_not_write_autometa_variables` 기대값 전환 명기.
