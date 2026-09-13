-- 실연구실 C 신설 — **운영 기반 구성**이다. 시험 픽스처(`services/core-api/tests/fixtures/seed.sql`)와
-- 한 파일에 두지 않는다 (`S2-EXEC-PLAN §3.2` · `PLAN-SoT §9 〈93〉`).
--
-- 값의 근거 = `S2-EXEC-PLAN §3.3`(표시명·프로필) · `§3.4`(ID 확정값 · 최소 필수 행).
-- 소유자 롤로 돈다 — FORCE RLS 아래에서 다중 연구실 조작은 경계 밖에서만 성립한다.
--
-- **멱등** — 전 문장이 `ON CONFLICT DO NOTHING`. 재실행하면 행 수가 늘지 않는다 (`§5.4-㈁`).
-- **조건 없는 DELETE 를 두지 않는다** (`S2-BLOCKER-INVESTIGATION §1.7-1`).

\set ON_ERROR_STOP on
BEGIN;

-- 경계를 **먼저** 건다. `d1_lab` 에는 RLS 가 없지만 `d1_lab_profile`·`d1_account`·`d2_member_role` 은
-- FORCE RLS 아래의 `lab_boundary` 정책에 걸리고 그 정책은 `current_lab_id()` = 이 GUC 를 읽는다.
-- 안 걸면 두 번째 문장에서 축자 `new row violates row-level security policy for table "d1_lab_profile"`
-- 로 멈춘다. staging 에서 통했던 것은 실행기 `provision-lab.sh` 가 psql 을 **`postgres` 슈퍼유저**로
-- 불렀기 때문이고, dev(RDS)에는 그 롤이 없다 — 소유자 롤 `colab_owner` 는 `NOBYPASSRLS` 다.
-- `SET LOCAL` 이라 이 트랜잭션이 끝나면 함께 풀린다 (`ops/purge_datasets.py` 와 같은 규율).
SET LOCAL app.current_lab = '00000000000000000000HYMETS';

-- 연구실 C. 표시명 = `SEED-DATA.md:5` · `PLAN-SoT §9 〈52〉`.
-- `opened_at` 은 **[원천 무근거]** — 정본·원천에 개설일 기재가 없다. NOT NULL 이라 비울 수 없어
-- **v2 에 신설한 날**을 적는다. 연구실의 실제 개설일이 아니라 **원장 등재일**이다.
INSERT INTO d1_lab (id, name, opened_at) VALUES
  ('00000000000000000000HYMETS', '고려대학교 수문학연구실', '2026-08-26T00:00:00Z')
ON CONFLICT (id) DO NOTHING;

-- 프로필. 근거 없는 칸은 **NULL 로 둔다** — 지어내지 않는다 (`PLAN-SoT §9-㊴-②`).
--   department   = [원천 무근거] → NULL
--   introduction = [원천 무근거] → NULL
INSERT INTO d1_lab_profile
  (lab_id, university, department, principal_investigator, research_field,
   introduction, default_visibility) VALUES
  ('00000000000000000000HYMETS', '고려대학교', NULL, '전창현', '수문학', NULL, '열림')
ON CONFLICT (lab_id) DO NOTHING;

-- 교수 1인 (`§3.5` 권고 ★). 교수는 네 스위치가 **항상 켜진 것으로 판정된다**(P-5) —
-- `d2_permission_switch` 행을 두지 않는다.
-- `email` 은 **[원천 무근거]** — 원천에 주소가 없다. 라우팅되지 않는 `.invalid` 를 쓴다.
INSERT INTO d1_account (id, lab_id, name, email) VALUES
  ('000000000000000000HYMETSP1', '00000000000000000000HYMETS', '전창현', 'pi@hymets.invalid')
ON CONFLICT (id) DO NOTHING;

INSERT INTO d2_member_role (account_id, lab_id, role) VALUES
  ('000000000000000000HYMETSP1', '00000000000000000000HYMETS', '교수')
ON CONFLICT (account_id) DO NOTHING;

COMMIT;

-- 계수도 경계 안에서 읽는다. `SET LOCAL` 은 위 `COMMIT` 과 함께 풀리므로, 여기서 다시 걸지 않으면
-- `d1_lab_profile`·`d1_account`·`d2_member_role` 이 **행이 있는데도 0 으로 보인다**(`colab_owner` 는
-- `NOBYPASSRLS`). 「없다」는 경계가 실린 경로로만 판정한다 — `.claude/rules/deploy.md` 「깨뜨리면 안 되는 것」 10번.
-- 세션 단위 `SET` 이라 psql 이 끝나면 사라진다.
SET app.current_lab = '00000000000000000000HYMETS';

\echo '-- 삽입 후 계수 (연구실 C 한정)'
SELECT 'd1_lab' AS 표, count(*) AS 행 FROM d1_lab WHERE id = '00000000000000000000HYMETS'
UNION ALL SELECT 'd1_lab_profile', count(*) FROM d1_lab_profile WHERE lab_id = '00000000000000000000HYMETS'
UNION ALL SELECT 'd1_account', count(*) FROM d1_account WHERE lab_id = '00000000000000000000HYMETS'
UNION ALL SELECT 'd2_member_role', count(*) FROM d2_member_role WHERE lab_id = '00000000000000000000HYMETS'
UNION ALL SELECT 'd2_permission_switch', count(*) FROM d2_permission_switch WHERE lab_id = '00000000000000000000HYMETS'
ORDER BY 1;
