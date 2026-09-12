// 상세 화면 미리보기 절로 스크롤(#25⑵ 촬영).
(() => {
  const row = document.querySelector('[data-testid="dt-pick-row"]');
  if (!row) return { err: 'no row' };
  row.scrollIntoView({ block: 'start' });
  window.scrollBy(0, -80);
  const r = row.getBoundingClientRect();
  const f = document.querySelector('.pv-frame');
  return { rowTop: Math.round(r.top), frameTop: f ? Math.round(f.getBoundingClientRect().top) : null };
})();
