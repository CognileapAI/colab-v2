-- db/ai/schema.sql — 지식·추론 선언 스키마 정본 (SoT)
--
-- 소유 도메인: D9 Ontology & Knowledge Graph · D10 AI Services
--
-- **지금은 빈 골격이다.** 테이블은 하나도 없고 체인 상태 테이블만 있다.
-- 온톨로지 1차 범위(무엇을 아는가)는 G8 에서, 그래프 저장소 선택은 K1 에서 정한다
-- (PLAN-SoT §9 열린 것 ⑨ ⑩). 정해지지 않은 형태를 미리 적어 두지 않는다.
--
-- 이 체인이 지키는 것
--   · CLAUDE.md §3-3 — 이 체인은 기록 도메인(D1~D8)과 마이그레이션 체인이 분리된다.
--     체인 상태 테이블 이름이 다른 것이 그 분리의 실물이다.
--   · CLAUDE.md §3-2 — 여기에 계보 테이블을 두지 않는다. AI 는 제안만 하고,
--     사람이 확인한 것만 기록 쪽 체인으로 넘어간다. 제안 임시 저장소가 생기면 `ai_` 접두사를 쓴다.
--   · 여기에 D1~D8 테이블을 넣지 않는다. 넣으면 온톨로지 한 줄 추가가 기록 쪽 마이그레이션을 기다린다.
--
-- RLS: D9 온톨로지는 연구실 공통 지식이라 테넌트별로 갈리지 않는다 (DOMAINS.md D9).
-- 다만 면제는 **접두사가 아니라 이름 하나씩** gates/config/rls-allowlist.toml 에 적는다 —
-- 테이블이 생길 때마다 사람이 판단을 한 번 내리게 하려는 것이다.

CREATE TABLE alembic_version_ai (
  version_num character varying(32) NOT NULL,
  CONSTRAINT alembic_version_ai_pkc PRIMARY KEY (version_num)
);
