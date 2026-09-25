"""Derive a numeric missing rate from the free-text column instead of copying it.

Revision ID: 0043_variable_missing_rate
Revises: 0042_reconcile_admin_access

⭑ **⟨2026-09-18⟩ 왜 사본이 아니라 파생인가** (`dev-package/intent/2026-09-18-missing-rate-predicate-recon.md`
  증보 3 · Ted 「권고대로」 판정 3=㈐, 구현 형태 ㈐-2).

  조건 검색은 결측률을 수치로 비교해야 하는데 `d3_dataset_variable.missing_rate` 는 자유 입력
  text 다. 세 갈래가 있었다 —
    ㈎ `d3_search_evidence.facts` 에 전재한다 → **사본이 생긴다.** 원본이 고쳐져도 facts 를
       다시 쓰는 주체가 없고, 신규 등록분은 검토자가 근거를 쓰기 전까지 값이 없다.
    ㈏ 질의 시점에 text 를 파싱한다 → 형식이 제각각이면 조용히 매치 없음.
    ㈐ **원본 옆에 파생 칸을 둔다** ← 이 리비전.
  파생이라 동기화 주체가 필요 없다. 원본을 고치면 그 자리에서 따라 바뀐다.

  ⛔ **입력 계약은 한 글자도 바꾸지 않는다.** `contracts/seams/fe-core.yaml` 의 `missingRate`
    는 「자유 입력. `0.2%` 처럼 사람이 적은 그대로」로 못박혀 있고(PRD-16 · WU-B2 · `VAL-006`
    계열), 그 결정을 뒤집는 것이 ㈐-1(입력 검증)이라 접었다. `missing_rate` 는 text · NULL
    허용 · CHECK 없음 그대로다.

  ⚠ **파싱 불가는 오류가 아니라 NULL 이다.** 등록을 막으면 자유 입력이 아니다. 파싱 못한
    문면은 NULL 로 남아 술어에서 빠질 뿐이다(그 값이 검색에서 조용히 빠진다는 것을 등록자에게
    알리는 표시는 이 회차 밖이다 — intent 「㈐ 의 구현 형태」 반대 관점).

  ⚠ **0~100 밖도 NULL 이다.** CHECK 로 막으면 같은 이유로 등록이 막힌다. 백분율이 아닌 수를
    적은 칸은 결측률로 읽을 수 없을 뿐이다.

  ⚠ 조건은 **중첩 CASE** 다. `substring` 이 매치 실패에 NULL 을 돌려주므로 `NULL BETWEEN`
    은 참이 아니고, 캐스트는 매치된 숫자 문면에만 닿는다. `~ … AND …::numeric` 로 적으면
    PostgreSQL 이 AND 의 두 항을 어느 순서로든 계산할 수 있어 `'낮음'::numeric` 가 터진다.

  경계: 생성 컬럼은 표의 RLS 정책을 그대로 물려받는다. 새 정책·새 grant 가 없다
  (`gates/config/rls-allowlist.toml` 무변경, `rls-coverage` 는 표 단위로 본다).
"""
from alembic import op

revision = "0043_variable_missing_rate"
down_revision = "0042_reconcile_admin_access"
branch_labels = None
depends_on = None

#: 정규식은 intent 축자(`^\s*\d+(\.\d+)?\s*%?\s*$`)에서 **좁혔다.** 축자대로 두면 생성식이
#: 자유 입력 칸의 등록을 막는다 — 바로 위 ⚠ 의 정반대다. 두 갈래를 실측했다
#: (로컬 postgres:16 · postgres:16-alpine, 둘 다 16.15):
#:   · `\d+` 는 자릿수가 무제한이라 numeric 한계(정수부 131072 · 소수부 16383)를 넘는 문면에서
#:     `value overflows numeric format` 이 난다. `missing_rate` 에는 길이 상한이 없다 —
#:     `catalog.py` 의 검사는 「문자열이거나 null」까지이고 DB 에도 CHECK 가 없다.
#:     `repeat('9',140000)` 과 `'0.' || repeat('9',20000)` 이 실제로 INSERT 를 죽였다.
#:   · `\d` 는 **locale 의존** 클래스다. ICU collation 판에서 전각 숫자 `'５%'`(U+FF15)를 잡고
#:     `::numeric` 이 `invalid input syntax for type numeric: "５"` 로 거절해 역시 등록이 죽는다.
#:     libc collation(공식 이미지 기본)에서는 안 잡히므로 판마다 결론이 갈린다.
#: 그래서 ASCII 숫자 범위를 명시하고 자릿수를 묶는다. 0~100 의 백분율에는 정수부 3자리·
#: 소수부 6자리면 남는다. 묶은 밖(`'0.1234567'`)은 오류가 아니라 NULL 로 빠질 뿐이다 —
#: 파싱 불가와 같은 자리다. 기존 기대는 그대로 선다(`'0.2%'`→0.2 · `' 20 % '`→20 ·
#: `'100'`→100 · `'101'`→NULL · `'낮음'`→NULL).
#: 숫자만 되받기 위해 바깥 괄호 하나만 잡는 그룹으로 적는 것은 그대로다
#: (PostgreSQL `substring` 은 첫 그룹을 돌려준다).
_NUMBER = r"substring(missing_rate from '^\s*([0-9]{1,3}(?:\.[0-9]{1,6})?)\s*%?\s*$')::numeric"

_ADD = f"""
ALTER TABLE d3_dataset_variable
  ADD COLUMN missing_rate_percent numeric
  GENERATED ALWAYS AS (
    CASE WHEN {_NUMBER} BETWEEN 0 AND 100
         THEN {_NUMBER}
    END
  ) STORED;
"""


def upgrade() -> None:
    op.execute(_ADD)


def downgrade() -> None:
    op.execute("ALTER TABLE d3_dataset_variable DROP COLUMN missing_rate_percent;")
