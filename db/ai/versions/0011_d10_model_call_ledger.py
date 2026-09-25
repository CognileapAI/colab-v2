"""D10 — 모델 호출 실행 원장 한 표 (d10_model_call)

정본 = dev-package/intent/2026-09-24-d10-model-call-ledger.md 「판정 기록 (2026-09-24 Ted)」
판정  = Ted 2026-09-24 — 「작은 데이터베이스 표 하나 만드는 건 좋으나, 어느 나라인지는 적을
        필요 없다. 어떤 모델이고 캐시율부터 이런 걸 적재해야 하지 않을까?」
근거  = dev-package/PLAN-SoT.md §9-㊷ 추기 ② (같은 판정으로 「처리 리전 필수 기록」을 철회했다)

**왜 로그 줄이 아니라 표인가.** 「필수 필드로 기록」은 조회 가능한 기록을 요구하는 것으로
읽는 것이 자연스럽고, 이 저장소에는 앱 stdout 을 모으는 수집기 배선이 없다 — 구조화 로그로만
두면 dev/staging 에서 원장을 **볼 방법이 없고**, 그것은 기록이 없는 것과 같은 상태다.

**왜 이 체인인가.** D9·D10 저장소는 기록 도메인과 마이그레이션 체인이 분리된다
(CLAUDE.md §3-3 · DOMAINS.md). 원장은 D10 안에서 나고 D10 안에서 산다 — 중계 쪽이 이 값을
기록하면 호출 세부사항이 그쪽으로 새어 도메인 경계가 깨진다.

**이 리비전은 표 하나와 색인 둘만 만든다. 시드가 없다.** 행은 런타임이 쌓고, 게이트가 도는
동안에는 두 호출 지점의 기본 설정이 모델을 부르지 않으므로 **비어 있는 것이 정상이다** —
「행 0건」을 실패로 재는 시험을 만들지 않는다.

선언 정본은 db/ai/schema.sql 이고 이 리비전은 그 정본을 재현하는 절차다
(env.py — autogenerate 를 쓰지 않는다). 그래서 DDL 을 schema.sql 과 **한 글자도 다르지 않게**
적는다. 갈라지면 schema-diff 와 db/ai/tests/0011-drift.sh 가 red 를 낸다.

⚠ 이 파일의 산문에 기록 체인의 **경로 문자열**을 적지 않는다. ai-no-lineage-write ⑨ 는 그
경로가 db/ai 안에서 글자로 나타나면 주석이라도 red 를 낸다. 게이트가 맞다 — 정규식이 산문과
코드를 가르려 들면 진짜 참조를 놓칠 문이 생긴다. **고칠 것은 게이트가 아니라 문장이다.**

Revision ID: 0011_d10_model_call_ledger
Revises: 0010_practitioner_concept

⭑ ⟨재번호 2026-09-25 · ai-search-integration⟩ 처음 id 는 `0008_d10_model_call_ledger`(부모 0007)였다.
AI 검색 갈래의 `0008_dataset_knowledge`~`0010_practitioner_concept` 와 합치며 id·부모를 함께
옮겼다. dev·prod 어느 쪽에도 옛 id 가 적용된 적이 없다(두 쪽 ai head = 0007). 부모만 바꾸고
id 를 두면 옛 id 가 찍힌 DB 에서 0008~0010 을 적용된 것으로 보고 조용히 건너뛰므로, 그런 DB 가
「Can't locate revision」으로 즉시 실패하도록 id 까지 바꾼다.
"""
from __future__ import annotations

from alembic import op

#: ⚠ **32자를 넘기지 않는다** — alembic_version_ai.version_num 이 varchar(32) 다.
#: `0011_d10_model_call_ledger` = 26자.
revision = "0011_d10_model_call_ledger"
down_revision = "0010_practitioner_concept"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE d10_model_call (
          id                   text        PRIMARY KEY
                               CHECK (id ~ '^[0-9A-HJKMNP-TV-Z]{26}$'),
          called_at            timestamptz NOT NULL,
          -- 닫힌 두 값. 코드 쪽 사본은 colab_ai.ports.CALL_SITES 이고 드리프트 시험이 대조한다.
          call_site            text        NOT NULL
                               CHECK (call_site IN ('search.interpret', 'lineage.suggest')),
          provider             text        NOT NULL
                               CHECK (btrim(provider) = provider AND length(provider) BETWEEN 1 AND 40),
          model_requested      text        NOT NULL
                               CHECK (btrim(model_requested) = model_requested
                                      AND length(model_requested) BETWEEN 1 AND 120),
          -- 응답이 실어 보낸 model. 못 닿았거나 안 불렀으면 NULL — 요청한 이름으로 채우지 않는다.
          model_returned       text        NULL
                               CHECK (model_returned IS NULL OR length(btrim(model_returned)) > 0),
          -- not_called 를 따로 두는 것이 이 목록의 요지다 — 「불렀는데 빈 답」과 「안 불렀다」는
          -- 다른 사실이고, 접으면 「왜 안 불렀나」가 원장에서 사라진다.
          outcome              text        NOT NULL
                               CHECK (outcome IN ('ok', 'timeout', 'unreachable', 'unreadable',
                                                  'empty_by_model', 'not_called')),
          -- **안정된 코드다. 자유 문장을 넣지 않는다** — 문구가 바뀌면 같은 사유가 두 값이 되고
          -- 집계가 조용히 갈린다.
          not_called_reason    text        NULL
                               CHECK (not_called_reason IS NULL
                                      OR not_called_reason IN ('no_credentials', 'no_candidates',
                                                               'mode_off')),
          latency_ms           integer     NULL CHECK (latency_ms IS NULL OR latency_ms >= 0),
          prompt_tokens        integer     NULL CHECK (prompt_tokens IS NULL OR prompt_tokens >= 0),
          completion_tokens    integer     NULL CHECK (completion_tokens IS NULL OR completion_tokens >= 0),
          -- OpenAI usage.prompt_tokens_details.cached_tokens. 안 실려 오면 NULL —
          -- 0 으로 채우면 「캐시가 안 걸렸다」와 「공급자가 안 알려줬다」가 같은 값이 된다.
          cached_prompt_tokens integer     NULL
                               CHECK (cached_prompt_tokens IS NULL OR cached_prompt_tokens >= 0),
          -- 입력 규모 = 제안이 받은 후보 수. 해석은 NULL 이다 — 그 자리의 입력은 질의 그 자체이고,
          -- 그것을 세는 것은 질의를 재는 것이라 담지 않는다.
          input_count          integer     NULL CHECK (input_count IS NULL OR input_count >= 0),
          -- 결과 수 = 해석은 검색어 수, 제안은 남긴 제안 수. **값이 아니라 개수다.**
          result_count         integer     NULL CHECK (result_count IS NULL OR result_count >= 0),
          lab_id               text        NULL
                               CHECK (lab_id IS NULL OR lab_id ~ '^[0-9A-HJKMNP-TV-Z]{26}$'),
          -- 사유는 not_called 의 것이다. 양쪽으로 건다: 사유 없는 not_called 는 「왜 안 불렀나」가
          -- 비어 미호출 행을 세는 의미가 사라지고, not_called 아닌 행의 사유는 거짓말이다.
          CONSTRAINT d10_model_call_reason_iff_not_called
                       CHECK ((outcome = 'not_called') = (not_called_reason IS NOT NULL)),
          -- 캐시 토큰은 프롬프트 토큰의 부분집합이다 — 넘으면 캐시율이 1 을 넘고, 그 수를 본 사람은
          -- 계산식을 의심하지 표를 의심하지 않는다.
          CONSTRAINT d10_model_call_cached_within_prompt
                       CHECK (cached_prompt_tokens IS NULL OR prompt_tokens IS NULL
                              OR cached_prompt_tokens <= prompt_tokens),
          -- 부르지 않은 호출에는 잴 지연도 쓸 토큰도 없다. 0 으로 적히면 평균 지연이 조용히 낮아진다.
          CONSTRAINT d10_model_call_not_called_has_no_measures
                       CHECK (outcome <> 'not_called'
                              OR (latency_ms IS NULL AND prompt_tokens IS NULL
                                  AND completion_tokens IS NULL AND cached_prompt_tokens IS NULL
                                  AND model_returned IS NULL))
        )
        """
    )
    op.execute("CREATE INDEX d10_model_call_called_at_idx ON d10_model_call (called_at)")
    op.execute(
        "CREATE INDEX d10_model_call_site_time_idx ON d10_model_call (call_site, called_at)")


def downgrade() -> None:
    """표를 지운다 — **색인은 표와 함께 간다.**

    되돌리면 그때까지 쌓인 호출 기록이 사라진다. 그 행들은 다시 만들 수 없다(호출은 이미
    일어났다). 되돌릴 이유가 생기면 되돌리기 전에 표를 떠 두는 것은 운영의 몫이고,
    이 파일이 대신 결정하지 않는다 — 보존 기간 자체가 아직 정해지지 않았다(intent 미해결 질문).
    """
    op.execute("DROP TABLE d10_model_call")
