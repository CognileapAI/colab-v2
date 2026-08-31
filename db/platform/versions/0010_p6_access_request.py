"""승인 처리의 **요청** 표 둘을 세운다 — WU-P6

선언 정본은 db/platform/schema.sql 이다. 이 파일은 0009 까지의 스키마에 그 정본의
**차분만** 더한다 — 두 쪽이 갈라지면 schema-diff 게이트가 red 를 낸다.

━━ 무엇을 더하나 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  · `d2_dataset_access_request`  — 접근 요청 (정본 §7.2 · 검토 대기 / 승인됨 / 거절됨)
  · `d2_verification_request`    — Verified 승인 요청 (정본 §7.1 · 검토 대기 / 승인됨)

각 표에 부분 유니크 1 · 인덱스 2 · 경계 정책 1.

━━ 왜 여는가 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**결과 쪽은 P0 부터 있었고 이미 시험으로 서 있다.** 허용 목록(`d2_dataset_access_grant`)에
미만료 줄이 있으면 본체가 열린다는 것을 `tests/test_body_access.py` 가 DB 층·HTTP 층 양쪽에서
증명하고, 배지 기록(`d2_verified`)도 `d2_access.py::verification` 이 이미 읽는다.

**없던 것은 그 결과를 만드는 경로다.** 계약은 여섯 op 을 다 열어 뒀는데 실물은 501 이었고,
`not_implemented.py` 가 적은 사유가 곧 이 회차의 작업이다 — 「저장처 자체가 P0 스키마에 없다」.
같은 사실을 조립 루트도 두 자리에서 적고 있었다:

    routes/catalog.py:594  「그 자리는 P6(`createAccessRequest` = NOT_IMPLEMENTED_NO_STORE)다」
    routes/catalog.py:608  「**검토 대기의 저장처가 없다**(P6) — 대기 건이 존재할 수 없으므로
                             지금 참이 될 수 없다」

그래서 표 둘을 **한 리비전에서** 세운다. 승인 처리는 정본이 한 문서로 묶은 한 기능이고,
둘을 갈라 두 회차로 나누면 그 사이 회차의 `P6` 은 반드시 부분 완료가 된다.

━━ 왜 결과 표에 상태 열을 붙이지 않았나 ━━━━━━━━━━━━━━━━━━━━━━━━━━

허용 목록은 승인 **결과**다 — 줄이 있고 안 만료면 본체가 열리고, 없으면 닫힌다. 거기에
'검토 대기'·'거절됨' 을 앉히면 `body_access` RESTRICTIVE 정책이 상태 문자열을 읽어야 하고,
그 순간 **잠금 판정이 요청 워크플로에 얽힌다.** 정본 §7.2 는 요청의 전이(검토 대기 →
승인됨/거절됨)와 허용의 만료를 **다른 축**으로 적었다. 표를 가르는 것이 그 축을 지키는 방법이고,
그래서 이 리비전은 `d2_dataset_access_grant` 와 `d2_verified` 를 **한 글자도 건드리지 않는다.**

━━ ⚠ 두 표의 상태 집합이 다르다 — 실수가 아니라 정본이다 ━━━━━━━━━━━━━

정본 §1.2 축자 「거절 ｜ Verified: **없음 (승인 / 미승인)** ｜ 접근 요청: **있음 (사유 필수)**」.
그래서 `d2_verification_request` 에는 '거절됨' 도 `rejection_reason` 도 없다. 두 표를 하나로
합치거나 상태 집합을 맞추면 이 조항이 사라진다.

━━ ⚠ 순수 가산이다 — 기존 표·행·제약을 하나도 건드리지 않는다 ━━━━━━━━━

  · 기존 표 변경 0 · 값 이행 0 행 · 인덱스 재작성 0
  · `d2_dataset_access_grant`·`d2_verified` 무변경 — 승인 op 이 그 표에 쓸 뿐이다
  · `body_access` 정책 무변경 · 시드 무변경

Revision ID: 0010_p6_access_request
Revises: 0009_preview_stale_event_types
"""
from __future__ import annotations

from alembic import op

revision = "0010_p6_access_request"
down_revision = "0009_preview_stale_event_types"
branch_labels = None
depends_on = None


UPGRADE = r"""
-- ── 접근 요청 (정본 §7.2) ────────────────────────────────────────────────────
CREATE TABLE d2_dataset_access_request (
  id                    ulid        PRIMARY KEY,
  lab_id                ulid        NOT NULL REFERENCES d1_lab(id),
  dataset_id            ulid        NOT NULL,
  requester_account_id  ulid        NOT NULL REFERENCES d1_account(id),
  reason                text        CHECK (reason IS NULL OR
                                           (length(reason) BETWEEN 1 AND 300)),
  requested_at          timestamptz NOT NULL DEFAULT now(),
  state                 text        NOT NULL DEFAULT '검토 대기'
                                    CHECK (state IN ('검토 대기', '승인됨', '거절됨')),
  decided_by_account_id ulid        REFERENCES d1_account(id),
  decided_at            timestamptz,
  rejection_reason      text        CHECK (rejection_reason IS NULL OR
                                           (length(rejection_reason) BETWEEN 1 AND 300)),
  CHECK ((decided_by_account_id IS NULL) = (decided_at IS NULL)),
  CHECK ((state = '검토 대기') = (decided_at IS NULL)),
  CHECK ((state = '거절됨') = (rejection_reason IS NOT NULL))
);

CREATE UNIQUE INDEX d2_dataset_access_request_pending_key
  ON d2_dataset_access_request (dataset_id, requester_account_id)
  WHERE state = '검토 대기';
CREATE INDEX d2_dataset_access_request_pending_idx
  ON d2_dataset_access_request (lab_id, requested_at)
  WHERE state = '검토 대기';
CREATE INDEX d2_dataset_access_request_lab_idx ON d2_dataset_access_request (lab_id);

ALTER TABLE d2_dataset_access_request ENABLE ROW LEVEL SECURITY;
ALTER TABLE d2_dataset_access_request FORCE  ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d2_dataset_access_request FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());

-- ── Verified 승인 요청 (정본 §7.1 · 거절 없음) ───────────────────────────────
CREATE TABLE d2_verification_request (
  id                    ulid        PRIMARY KEY,
  lab_id                ulid        NOT NULL REFERENCES d1_lab(id),
  dataset_id            ulid        NOT NULL,
  requester_account_id  ulid        NOT NULL REFERENCES d1_account(id),
  requested_at          timestamptz NOT NULL DEFAULT now(),
  state                 text        NOT NULL DEFAULT '검토 대기'
                                    CHECK (state IN ('검토 대기', '승인됨')),
  decided_by_account_id ulid        REFERENCES d1_account(id),
  decided_at            timestamptz,
  CHECK ((decided_by_account_id IS NULL) = (decided_at IS NULL)),
  CHECK ((state = '검토 대기') = (decided_at IS NULL))
);

CREATE UNIQUE INDEX d2_verification_request_pending_key
  ON d2_verification_request (dataset_id)
  WHERE state = '검토 대기';
CREATE INDEX d2_verification_request_pending_idx
  ON d2_verification_request (lab_id, requested_at)
  WHERE state = '검토 대기';
CREATE INDEX d2_verification_request_lab_idx ON d2_verification_request (lab_id);

ALTER TABLE d2_verification_request ENABLE ROW LEVEL SECURITY;
ALTER TABLE d2_verification_request FORCE  ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d2_verification_request FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());

-- 경계가 실제로 켜졌는지를 DB 에게 되묻는다. 관례가 아니라 기계가 지킨다 (0008·0009 와 같은 방식).
-- **`rls-coverage` 게이트는 선언 스키마를 보고 이 파일은 적용 DB 를 만든다** — 두 쪽 다 막는다.
-- 경계 없는 표는 「연구실 밖의 요청이 목록에 섞이는」 형태로만 드러나고, 그건 조용하다.
DO $$
DECLARE
  t text;
  ok boolean;
BEGIN
  FOREACH t IN ARRAY ARRAY['d2_dataset_access_request', 'd2_verification_request'] LOOP
    SELECT c.relrowsecurity AND c.relforcerowsecurity
       AND EXISTS (SELECT 1 FROM pg_policies p
                    WHERE p.tablename = t AND p.policyname = 'lab_boundary')
      INTO ok
      FROM pg_class c
     WHERE c.oid = t::regclass;
    IF ok IS NOT TRUE THEN
      RAISE EXCEPTION '0010: % 에 경계가 안 걸렸다 — 새는 표를 만들지 않는다', t;
    END IF;
  END LOOP;
END $$;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    """⚠ **전진 전용이다 — 되돌리지 않는다** (`〈168〉-㉲` · 0008·0009 와 같은 자세).

    두 표를 지우면 「누가 무엇을 언제 요청했고 누가 열어 줬는가」가 통째로 사라진다.
    허용 줄(`d2_dataset_access_grant`)은 남지만 그 줄은 **결과**만 적어서 요청·거절의
    이력을 되짚지 못한다. 복구가 필요하면 **앞으로 가는 새 리비전**을 쓴다.
    """
    raise RuntimeError(
        "0010_p6_access_request 는 전진 전용이다 — 되돌리지 않는다. "
        "표를 지우면 요청·거절 이력이 사라지고 되짚을 자리가 없다."
    )
