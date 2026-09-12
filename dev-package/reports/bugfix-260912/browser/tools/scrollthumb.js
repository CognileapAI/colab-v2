// 축소본 자리로 스크롤 — details 를 열고 스크롤 조상을 찾아 직접 옮긴다.
(() => {
  const d = document.querySelector('[data-testid="up-preview-options"]');
  if (d) d.open = true;
  const t = document.querySelector('[data-testid="up-thumb-img"]');
  if (!t) return { err: 'no thumb' };
  let el = t.parentElement, scroller = null;
  while (el) {
    const cs = getComputedStyle(el);
    if (/(auto|scroll)/.test(cs.overflowY) && el.scrollHeight > el.clientHeight) { scroller = el; break; }
    el = el.parentElement;
  }
  if (scroller) {
    scroller.scrollTop = t.offsetTop - scroller.offsetTop - 120;
  } else {
    t.scrollIntoView({ block: 'center' });
  }
  const r = t.getBoundingClientRect();
  return { scroller: scroller ? scroller.className : null, rect: { top: Math.round(r.top), left: Math.round(r.left), w: Math.round(r.width), h: Math.round(r.height) } };
})();
