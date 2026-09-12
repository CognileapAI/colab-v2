// 공개 범위 안내 문단 자리로 스크롤(#31 나머지 2건 촬영).
(() => {
  const t = document.querySelector('[data-testid="reg-summary-hint"]');
  if (!t) return { err: 'not found' };
  let el = t.parentElement, scroller = null;
  while (el) {
    const cs = getComputedStyle(el);
    if (/(auto|scroll)/.test(cs.overflowY) && el.scrollHeight > el.clientHeight) { scroller = el; break; }
    el = el.parentElement;
  }
  if (scroller) {
    const tr = t.getBoundingClientRect(), sr = scroller.getBoundingClientRect();
    scroller.scrollTop += tr.top - sr.top - 300;
  }
  const r = t.getBoundingClientRect();
  return { top: Math.round(r.top) };
})();
