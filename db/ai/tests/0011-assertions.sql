-- 0011 오라클 — **`d10_model_call` 이 실제로 막는가**를 DB 에게 물어본다.
-- 형태는 db/ai/tests/0006-assertions.sql 과 같다 (같은 실패를 두 번 배우지 않는다).
--
-- ⚠ **정의문을 읽지 않는다. 넣어 본다.** CHECK 가 「적혀 있는가」와 「거절하는가」는 다른
--    사실이고, 이 레포가 반복해서 배운 것이 그 차이다. 그래서 아래는 전부 INSERT 를 돌려
--    통과/거절을 실측하고 ROLLBACK 한다 — **한 행도 남기지 않는다.**
--
-- 0010 까지만 적용된 DB 에서는 첫 문장(표 부재)에서 ERROR 가 나고 psql 이 비영으로 끝난다.
-- 그것이 「되돌리면 red」의 실물이다.
\set ON_ERROR_STOP on

DO $$
DECLARE
  ok boolean;
  n  integer;
BEGIN
  -- ── ㈀ 표와 색인이 자리에 있다 ───────────────────────────────────────────
  PERFORM 1 FROM information_schema.tables
    WHERE table_name = 'd10_model_call';
  IF NOT FOUND THEN
    RAISE EXCEPTION '0011 오라클 실패 — d10_model_call 표가 없다';
  END IF;

  SELECT count(*) INTO n FROM pg_indexes
    WHERE tablename = 'd10_model_call'
      AND indexname IN ('d10_model_call_called_at_idx', 'd10_model_call_site_time_idx');
  IF n <> 2 THEN
    RAISE EXCEPTION '0011 오라클 실패 — 색인 둘이 아니라 %건이다', n;
  END IF;

  -- ── ㈁ 리전 칸이 **없다** (㊷ 근거③ 철회 · Ted 2026-09-24) ──────────────
  SELECT count(*) INTO n FROM information_schema.columns
    WHERE table_name = 'd10_model_call' AND column_name LIKE '%region%';
  IF n <> 0 THEN
    RAISE EXCEPTION '0011 오라클 실패 — 리전 칸이 생겼다(%건). 철회된 의무를 되살렸다', n;
  END IF;

  -- ── ㈂ 캐시율은 **저장하지 않는다** — 파생 칸이 없다 ────────────────────
  SELECT count(*) INTO n FROM information_schema.columns
    WHERE table_name = 'd10_model_call'
      AND (column_name LIKE '%ratio%' OR column_name LIKE '%rate%');
  IF n <> 0 THEN
    RAISE EXCEPTION '0011 오라클 실패 — 파생 칸(%건)이 생겼다. 캐시율은 조회 때 계산한다', n;
  END IF;

  -- ── ㈃ 칸 수가 정확히 15 다 ─────────────────────────────────────────────
  -- 늘어난 칸이 무엇인지 여기서는 모른다 — **늘었다는 사실 자체**가 판정 대상이다.
  -- 「넣지 않는 것」 목록은 칸이 조용히 하나 느는 방식으로 무너진다.
  SELECT count(*) INTO n FROM information_schema.columns
    WHERE table_name = 'd10_model_call';
  IF n <> 15 THEN
    RAISE EXCEPTION '0011 오라클 실패 — 칸이 15 가 아니라 %개다', n;
  END IF;

  -- ── ㈄ 닫힌 어휘가 **실제로 거절한다** ──────────────────────────────────
  BEGIN
    INSERT INTO d10_model_call (id, called_at, call_site, provider, model_requested, outcome)
      VALUES ('00000000000000000000000001', now(), 'upload.guess', 'openai', 'm', 'ok');
    ok := true;
  EXCEPTION WHEN check_violation THEN ok := false;
  END;
  IF ok THEN RAISE EXCEPTION '0011 오라클 실패 — 목록 밖 call_site 가 들어갔다'; END IF;

  BEGIN
    INSERT INTO d10_model_call (id, called_at, call_site, provider, model_requested, outcome)
      VALUES ('00000000000000000000000002', now(), 'search.interpret', 'openai', 'm', 'fine');
    ok := true;
  EXCEPTION WHEN check_violation THEN ok := false;
  END;
  IF ok THEN RAISE EXCEPTION '0011 오라클 실패 — 목록 밖 outcome 이 들어갔다'; END IF;

  -- ── ㈅ 「왜 안 불렀나」가 비어 있을 수 없다 ─────────────────────────────
  BEGIN
    INSERT INTO d10_model_call (id, called_at, call_site, provider, model_requested, outcome)
      VALUES ('00000000000000000000000003', now(), 'lineage.suggest', 'openai', 'm', 'not_called');
    ok := true;
  EXCEPTION WHEN check_violation THEN ok := false;
  END;
  IF ok THEN
    RAISE EXCEPTION '0011 오라클 실패 — 사유 없는 not_called 가 들어갔다. 미호출 행의 요지가 사라진다';
  END IF;

  -- 거꾸로도 막는다 — 부르고서 사유를 적는 것은 거짓말이다.
  BEGIN
    INSERT INTO d10_model_call (id, called_at, call_site, provider, model_requested,
                                outcome, not_called_reason)
      VALUES ('00000000000000000000000004', now(), 'lineage.suggest', 'openai', 'm',
              'ok', 'no_candidates');
    ok := true;
  EXCEPTION WHEN check_violation THEN ok := false;
  END;
  IF ok THEN RAISE EXCEPTION '0011 오라클 실패 — not_called 가 아닌 행에 사유가 붙었다'; END IF;

  -- ── ㈆ 부르지 않은 호출에 지연·토큰이 붙지 않는다 ──────────────────────
  BEGIN
    INSERT INTO d10_model_call (id, called_at, call_site, provider, model_requested,
                                outcome, not_called_reason, latency_ms)
      VALUES ('00000000000000000000000005', now(), 'search.interpret', 'openai', 'm',
              'not_called', 'no_credentials', 0);
    ok := true;
  EXCEPTION WHEN check_violation THEN ok := false;
  END;
  IF ok THEN
    RAISE EXCEPTION '0011 오라클 실패 — 미호출 행에 지연 0 이 붙었다. 평균 지연이 조용히 낮아진다';
  END IF;

  -- ── ㈇ 캐시 토큰이 프롬프트 토큰을 넘을 수 없다 ────────────────────────
  BEGIN
    INSERT INTO d10_model_call (id, called_at, call_site, provider, model_requested,
                                outcome, prompt_tokens, cached_prompt_tokens)
      VALUES ('00000000000000000000000006', now(), 'search.interpret', 'openai', 'm',
              'ok', 10, 11);
    ok := true;
  EXCEPTION WHEN check_violation THEN ok := false;
  END;
  IF ok THEN RAISE EXCEPTION '0011 오라클 실패 — 캐시율이 1 을 넘는 행이 들어갔다'; END IF;

  -- ── ㈈ id 는 정규 ID 다 ─────────────────────────────────────────────────
  BEGIN
    INSERT INTO d10_model_call (id, called_at, call_site, provider, model_requested, outcome)
      VALUES ('not-a-ulid', now(), 'search.interpret', 'openai', 'm', 'ok');
    ok := true;
  EXCEPTION WHEN check_violation THEN ok := false;
  END;
  IF ok THEN RAISE EXCEPTION '0011 오라클 실패 — 정규 ID 가 아닌 id 가 들어갔다'; END IF;

  -- ── ㈉ 제대로 된 행 셋은 **실제로 통과한다** ───────────────────────────
  -- 거절만 재면 「전부 막는 표」도 green 이 된다. 통과해야 할 것이 통과하는지 함께 본다.
  BEGIN
    INSERT INTO d10_model_call (id, called_at, call_site, provider, model_requested,
                                model_returned, outcome, latency_ms, prompt_tokens,
                                completion_tokens, cached_prompt_tokens, input_count,
                                result_count, lab_id)
      VALUES ('00000000000000000000000007', now(), 'search.interpret', 'openai',
              'gpt-5.6-luna', 'gpt-5.6-luna-2026-08-01', 'ok', 2740, 1280, 64, 1024,
              NULL, 3, '0000000000000000000000000A'),
             -- 캐시 토큰 미상 = NULL. 0 이 아니다.
             ('00000000000000000000000009', now(), 'lineage.suggest', 'openai',
              'gpt-5.6-luna', 'gpt-5.6-luna-2026-08-01', 'empty_by_model', 900, 700, 12,
              NULL, 5, 0, NULL);
    -- 미호출 행 — 지연·토큰·응답 모델이 전부 비고 사유만 있다.
    INSERT INTO d10_model_call (id, called_at, call_site, provider, model_requested,
                                outcome, not_called_reason, input_count, result_count)
      VALUES ('00000000000000000000000008', now(), 'lineage.suggest', 'openai',
              'gpt-5.6-luna', 'not_called', 'no_candidates', 0, 0);
  EXCEPTION WHEN others THEN
    RAISE EXCEPTION '0011 오라클 실패 — 정상 행이 거절됐다: %', SQLERRM;
  END;

  -- 파생값은 **조회 때** 계산된다 — 저장 칸 없이도 캐시율이 나오는지 실제로 재 본다.
  SELECT round(sum(cached_prompt_tokens)::numeric / nullif(sum(prompt_tokens), 0), 2) = 0.80
    INTO ok
    FROM d10_model_call WHERE outcome = 'ok';
  IF NOT ok THEN
    RAISE EXCEPTION '0011 오라클 실패 — 조회로 캐시율을 계산하지 못했다';
  END IF;

  RAISE NOTICE '[0011-assertions] 닫힌 어휘 실거절 · 미호출 사유 양방향 · 캐시 상한 · 정규 ID · 정상 3행 통과 · 조회 캐시율 0.80 → OK';
  RAISE EXCEPTION 'ROLLBACK_SENTINEL';   -- 한 행도 남기지 않는다
EXCEPTION WHEN others THEN
  IF SQLERRM <> 'ROLLBACK_SENTINEL' THEN
    RAISE;
  END IF;
END $$;
