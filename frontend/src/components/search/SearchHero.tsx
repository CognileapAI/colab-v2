// S-01 검색 히어로 — 검색으로 들어가는 **유일한 입구**다 (`Policy_데이터_찾기 §1.3-2`).
//
// 여기가 약속하는 것은 「뜻을 알아듣는 검색」이 아니다. 매칭·순위는 `tsvector` + 사전이 정하고
// (`PLAN-SoT §9-〈72〉`), 색인은 지금 `ts_config='simple'` 이라 **낱말이 적힌 그대로** 맞는다.
// 그 사실을 결과가 0건이 된 다음에 말하면 늦다 — 입구에서 미리 말한다.
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MAX_QUERY_LENGTH } from './types';

export function SearchHero() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const q = query.trim();
    // 빈 질문을 서버로 보내지 않는다 — 계약이 1자 이상을 요구한다.
    if (!q) return;
    navigate(`/datasets/search?q=${encodeURIComponent(q)}`);
  }

  return (
    <section className="search-hero" data-screen="S-01">
      <h1>찾을 것이 정해져 있으면 물어보세요</h1>
      <form className="hero-box" onSubmit={submit} role="search">
        <input
          type="text"
          aria-label="검색 질문"
          placeholder="예: 한강 유역 강수 자료"
          maxLength={MAX_QUERY_LENGTH}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="submit">찾기</button>
      </form>
      <p className="hero-note" data-testid="search-hero-note">
        이 검색은 데이터에 <b>적혀 있는 낱말 그대로</b> 찾아요. 「강수량」으로는 「강수」가 적힌
        데이터가 나오지 않으니, 적혀 있을 법한 말로 물어보세요.
      </p>
    </section>
  );
}
