#!/usr/bin/env bash
# 스코프 커널이 **staging 에서도** 살아 있는지 — 실물 DB 에 대고 값으로 확인한다.
#
# P0(services/core-api/tests/)는 일회용 DB 에서 증명했다. 그 증명이 staging 에도 성립하는지는
# 별개 질문이다 — 롤·정책·FORCE RLS 중 하나만 다르게 깔려도 조용히 무너진다.
#
# 전부 **한 트랜잭션 안에서 돌리고 ROLLBACK 한다.** staging 데이터를 남기지 않는다.
# 접속 주체는 core-api 와 같은 앱 롤(colab_app)이다.
set -euo pipefail
PG="${PG_CONTAINER:-colab_v2_staging_pg}"
: "${COLAB_APP_PASSWORD:?COLAB_APP_PASSWORD 가 필요하다}"

docker exec -i -e PGPASSWORD="$COLAB_APP_PASSWORD" "$PG" \
  psql -v ON_ERROR_STOP=0 -U colab_app -d colab_platform <<'SQL'
BEGIN;
-- 정규 ID = Crockford base32 26 자 (I·L·O·U 제외). 임의 문자열을 쓰면 도메인 제약이 먼저 막는다.
\set LAB '''0000000000000000000000000A'''
\set OTHER '''0000000000000000000000000B'''

-- ① GUC 없음 = 기본 거부. current_lab_id() 가 NULL 이고 쓰기가 WITH CHECK 에 막혀야 한다.
SELECT '① 스코프 없음: current_lab_id()' AS 검사, coalesce(current_lab_id()::text,'NULL') AS 값;
SAVEPOINT s1;
INSERT INTO d1_lab (id, name, opened_at) VALUES ('0000000000000000000000000A','경계실험실', now());
SELECT set_config('app.current_lab', :OTHER, true);   -- 다른 연구실을 자처하고
INSERT INTO d1_lab_profile (lab_id) VALUES ('0000000000000000000000000A');  -- 남의 행을 심으려 한다
SELECT '① 스코프 밖 쓰기' AS 검사, '막히지 않았다 — RED' AS 값;
ROLLBACK TO s1;

-- ② 스코프 안 쓰기는 통과한다 (양성 대조군). 막기만 하고 통과시키지 못하면 그것도 고장이다.
INSERT INTO d1_lab (id, name, opened_at) VALUES ('0000000000000000000000000A','경계실험실', now());
SELECT set_config('app.current_lab', :LAB, true);
INSERT INTO d1_lab_profile (lab_id, university) VALUES ('0000000000000000000000000A','증명용');
SELECT '② 스코프 안 쓰기·읽기' AS 검사, count(*)::text || ' 행' AS 값 FROM d1_lab_profile;

-- ③ 같은 트랜잭션에서 다른 연구실로 스코프를 바꾸면 그 행이 사라져야 한다 (cross-tenant 음성).
SELECT set_config('app.current_lab', :OTHER, true);
SELECT '③ 다른 연구실 스코프' AS 검사, count(*)::text || ' 행 (0 이어야 한다)' AS 값 FROM d1_lab_profile;

-- ④ 스코프를 지우면 다시 0.
SELECT set_config('app.current_lab', '', true);
SELECT '④ 스코프 제거' AS 검사, count(*)::text || ' 행 (0 이어야 한다)' AS 값 FROM d1_lab_profile;

ROLLBACK;
SELECT '⑤ 증명 후 잔여물' AS 검사, count(*)::text || ' 행 (0 이어야 한다)' AS 값 FROM d1_lab;
SQL
