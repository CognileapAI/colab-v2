// live-ci first-paint observer: records every insertion / disabled-attribute change of the two draw buttons,
// and samples their disabled state inside requestAnimationFrame (i.e. the state that goes into that frame's paint).
(() => {
  const IDS = ['up-preview-draw', 'up-preview-without-grid'];
  const log = { events: [], frames: [], t0: performance.now() };
  window.__liveciObs = log;
  const sel = IDS.map((id) => `[data-testid="${id}"]`).join(',');
  const sty = (el) => { const c = getComputedStyle(el); return { cursor: c.cursor, opacity: c.opacity, backgroundColor: c.backgroundColor, color: c.color, borderColor: c.borderColor, filter: c.filter, pointerEvents: c.pointerEvents }; };
  // mirror to a DOM attribute so the log can be read with `get attr` (no page-script evaluation needed)
  const flush = () => { try { document.documentElement.setAttribute('data-liveci', JSON.stringify(log)); } catch (e) {} };
  const rec = (kind, el) => { log.events.push({ kind, id: el.getAttribute('data-testid'), disabled: el.disabled, t: +performance.now().toFixed(1), style: sty(el) }); flush(); };
  const scan = (node, kind) => {
    if (!(node instanceof Element)) return;
    if (node.matches(sel)) rec(kind, node);
    node.querySelectorAll(sel).forEach((el) => rec(kind, el));
  };
  new MutationObserver((muts) => {
    for (const m of muts) {
      if (m.type === 'childList') m.addedNodes.forEach((n) => scan(n, 'insert'));
      else if (m.type === 'attributes' && m.target.matches && m.target.matches(sel)) rec('attr', m.target);
    }
  }).observe(document, { subtree: true, childList: true, attributes: true, attributeFilter: ['disabled'] });
  let frames = 0;
  const tick = () => {
    const els = document.querySelectorAll(sel);
    if (els.length) {
      const snap = { t: +performance.now().toFixed(1), buttons: Array.from(els).map((e) => ({ id: e.getAttribute('data-testid'), disabled: e.disabled })) };
      const last = log.frames[log.frames.length - 1];
      if (!last || JSON.stringify(last.buttons) !== JSON.stringify(snap.buttons)) { log.frames.push(snap); flush(); }
    }
    if (++frames < 3000) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
})();
