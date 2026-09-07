"""R-B-1 `M-8` — Lv0 출처 두 칸(출처 주소 · 내려받은 날) (PRD-19 · WU-B6)

선언 정본은 db/platform/schema.sql 이다. 이 파일은 0017 까지의 스키마에 그 정본의
**차분만** 더한다 — 두 쪽이 갈라지면 schema-diff 게이트가 red 를 낸다.

━━ 무엇을 세우는가 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

`d3_dataset` 에 `source_url text` · `source_downloaded_on date` 를 신설한다.
PRD-19 축자 — 「원시 데이터라 부모가 없어요. 대신 어디서 언제 받았는지를 남겨요.」

⛔ **`source_label` 을 건드리지 않는다.** 그 열에는 정규화 열(`source_label_normalized`)과
   자동완성 색인(`d3_dataset_source_label_normalized_idx`)이 붙어 있고, 원천 표기는
   **Lv 무관 상시 노출**이다(미결-11 ⓐ). 이 회차가 더하는 것은 그 옆의 두 칸뿐이다.

━━ CHECK 를 걸지 않는다 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

두 칸은 **선택 입력**이다(PRD-19 축자 「비어도 등록된다」·「`Lv1` 이상에서 값이 와도
거절하지 않고 저장한다」). 그래서 NOT NULL 도, 값 집합 CHECK 도, Lv 와의 조건 제약도
걸지 않는다. ⛔ **종전 완료 판정(「Lv0 이면 두 칸 필수·400」·「Lv1 이상 값 전송 시
400」)은 폐기됐다** — 목업 배지를 근거로 400 을 세우지 않는다(PRD-19 「2026-09-06 감사
교차 확인」).

`source_downloaded_on` 이 `date` 인 것은 「내려받은 날」이 날짜이기 때문이다 — 시각이
아니다. 잘못된 날짜 문자열은 DB 캐스트가 아니라 **서버가 400 으로** 되돌린다(캐스트에
맡기면 사용자의 오타가 500 이 된다 · `CODE-REVIEW-20260903` #12 와 같은 자리).

━━ 기존 데이터 — **backfill 이 0 이다** ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

두 열 전부 **전 행 NULL** 이고 채울 근거가 없다 — `source_label` 은 출처의 **이름**이지
주소가 아니고, 내려받은 날은 어디에도 기록돼 있지 않다. 지어내면 그 순간 거짓 출처가
기존 행에 박힌다.

⟹ 이 마이그레이션에는 `UPDATE` 가 한 줄도 없고, `0017` 이 필요로 했던
**`NO FORCE ROW LEVEL SECURITY` 구간도 없다** — 고칠 행이 없으므로 정책을 내릴 이유가
없다(`0015` 와 같은 자리). 필수 검사가 없으므로 기존 행의 수정도 막히지 않는다.

파생 Lv 가 Lv0 인 기존 행의 상세에는 「Lv0 인데 출처 주소·내려받은 날이 비어 있어요 —
수정에서 채워 주세요」를 **안내로만** 표시한다(저장을 막지 않는다) — 그 자리는 화면이다.

━━ 되돌림 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

`downgrade` 는 두 열을 지운다. 배포 직후라면 전 행 NULL 이라 **잃는 값이 0** 이다.

⚠ **값이 쌓인 뒤에는 다르다.** 두 칸은 **사람이 적은 값**이라 열을 지우면 다시 올려도
   안 돌아온다(`0015` 의 세 칸과 같은 부류 · `0007` 류의 실패). 그래서 배포 뒤 표기만
   물리고 싶을 때의 정규 경로는 **소비를 멈추는 쪽**이다: 계약·서버·화면에서 `sourceUrl`·
   `sourceDownloadedOn` 을 되돌리면 열은 남은 채 아무도 안 읽는다.
   **열까지 지우는 것은 값이 0 행일 때만** 한다.

⚠ ⭑ **32자를 넘기지 않는다** — `alembic_version_platform.version_num` 이 `varchar(32)` 다.
   `0018_rb6_lv0_source` = 19자.

Revision ID: 0018_rb6_lv0_source
Revises: 0017_rb4_access_state_3
"""
from __future__ import annotations

from alembic import op

revision = "0018_rb6_lv0_source"
down_revision = "0017_rb4_access_state_3"
branch_labels = None
depends_on = None


UPGRADE = r"""
-- `M-8` — Lv0 출처 두 칸. **선택 입력이라 CHECK 도 NOT NULL 도 없다** (PRD-19 축자).
-- ⛔ 백필이 없다. 전 행 NULL 이 정상이고 재입력을 강제하지 않는다.
-- ⛔ `source_label` 과 그 정규화 열·색인은 한 글자도 건드리지 않는다 (미결-11 ⓐ).
ALTER TABLE d3_dataset
  ADD COLUMN source_url          text,
  ADD COLUMN source_downloaded_on date;
"""

DOWNGRADE = r"""
-- ⚠ **사람이 적은 값이 여기 있으면 사라진다** — 다시 올려도 안 돌아온다.
--    값이 있는 배포에서 표기만 물리려면 이 경로가 아니라 **소비를 멈추는 쪽**이다(윗글).
ALTER TABLE d3_dataset DROP COLUMN IF EXISTS source_downloaded_on;
ALTER TABLE d3_dataset DROP COLUMN IF EXISTS source_url;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    """열 둘을 지운다.

    배포 직후라면 **잃는 값이 0** 이다(두 열 전부 전 행 NULL · backfill 없음).
    ⚠ 값이 쌓인 뒤에는 **사람이 적은 값**이 사라지고 다시 올려도 안 돌아온다 —
    그때의 정규 경로는 **소비를 멈추는 쪽**이다(모듈 산문 「되돌림」).
    """
    op.execute(DOWNGRADE)
