-- 계정 한 건을 심는다 (P-17 — 계정 발급 주체는 개발자다. **회원가입 경로가 아니다**).
--
-- ⚠ **이 파일은 이 회차에서 실행되지 않았다.** Ted 지시 = 「계정 생성 스크립트는 본 레인이
--    작성하되 실행은 보고 후」. staging 무접촉.
--
-- ⚠ **역할과 연구실 귀속은 `[정본 무근거]` 다.**
--    정본의 역할 체계는 **교수 · 연구원 두 층뿐**이고(P-2 · `Policy_역할과_권한 §2` ·
--    `db/platform/schema.sql` `d2_member_role.role CHECK`), **관리자 역할은 정본에 없다.**
--    없는 역할을 지어내지 않는다 (`PLAN-SoT §9-㊴-②`). 그래서 아래 기본값은 **최소 권한**이다 —
--    `연구원` ＋ 스위치 4종 중 위임 성격 둘은 꺼짐(P-4). 값은 `PLAN-SoT §9 〈108〉-㉲` 의
--    Ted 판정으로 확정된다.
--
-- 사용 (psql 변수로 값을 준다 — 코드에 ID 를 박지 않는다):
--   psql -v ON_ERROR_STOP=1 \
--        -v account_id="'…26자…'" -v lab_id="'…26자…'" \
--        -v name="'colab'" -v email="'colab@example.invalid'" -v role="'연구원'" \
--        -f ops/provision-account.sql
--
-- 소유자 롤로 돈다 — 앱 롤은 RLS 경계 안에서만 쓰므로 계정 최초 생성에 쓰지 않는다.

BEGIN;

-- 연구실이 없으면 **멈춘다.** 계정을 붙일 자리를 지어내지 않는다.
--
-- ⚠ **`DO $$ … $$` 안에서는 psql 변수가 치환되지 않는다** — 달러 인용 문자열은 psql 이 손대지
--    않는 구간이라 `:lab_id` 가 글자 그대로 서버에 가고 `syntax error at or near ":"` 로 죽는다.
--    2026-08-26 첫 실행에서 실측됐다. 그래서 **문장을 만들어 `\gexec` 로 실행한다** —
--    연구실이 있으면 무해한 `SELECT 1`, 없으면 예외를 던지는 블록이 만들어진다.
SELECT CASE WHEN EXISTS (SELECT 1 FROM d1_lab WHERE id = :lab_id)
  THEN 'SELECT 1'
  ELSE format(
    'DO $guard$ BEGIN RAISE EXCEPTION ''연구실 %%가 없다. 계정을 붙일 자리를 만들지 않는다.'', %L; END $guard$',
    :lab_id)
END \gexec

INSERT INTO d1_account (id, lab_id, name, email)
VALUES (:account_id, :lab_id, :name, :email)
ON CONFLICT (id) DO NOTHING;

INSERT INTO d2_member_role (account_id, lab_id, role)
VALUES (:account_id, :lab_id, :role)
ON CONFLICT (account_id) DO NOTHING;

-- 스위치 4종 (P-3). 기본값은 스위치 성격을 따른다 (P-4) — 앞의 둘 켜짐, 위임 둘 꺼짐.
-- 다섯 번째를 만들지 않는다.
INSERT INTO d2_permission_switch (account_id, lab_id, switch, enabled) VALUES
  (:account_id, :lab_id, '업로드·편집',   true),
  (:account_id, :lab_id, '프로젝트 생성', true),
  (:account_id, :lab_id, '승인 위임',     false),
  (:account_id, :lab_id, '연구실 설정',   false)
ON CONFLICT (account_id, switch) DO NOTHING;

COMMIT;

-- 다음 단계 — 비밀번호는 **DB 에 두지 않는다.** 자격 파일에 해시로 심는다:
--   python3 ops/set-password.py --file <자격파일> --name colab \
--       --account-id <위와 같은 ULID> --lab-id <위와 같은 ULID>
