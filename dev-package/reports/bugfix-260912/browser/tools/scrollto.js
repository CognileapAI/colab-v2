// 지정 요소를 모달 본문 스크롤러 안에서 화면 가운데로 올린다. 대상은 window.__T 로 준다.
(() => {
  const sel = window.__T || '[data-testid="reg-period-open"]';
  const t = document.querySelector(sel);
  if (!t) return { err: 'not found', sel };
  let el = t.parentElement, scroller = null;
  while (el) {
    const cs = getComputedStyle(el);
    if (/(auto|scroll)/.test(cs.overflowY) && el.scrollHeight > el.clientHeight) { scroller = el; break; }
    el = el.parentElement;
  }
  if (scroller) {
    const tr = t.getBoundingClientRect(), sr = scroller.getBoundingClientRect();
    scroller.scrollTop += tr.top - sr.top - scroller.clientHeight / 2;
  } else t.scrollIntoView({ block: 'center' });
  const r = t.getBoundingClientRect();
  return { sel, scroller: scroller ? scroller.className : null, top: Math.round(r.top) };
})();
