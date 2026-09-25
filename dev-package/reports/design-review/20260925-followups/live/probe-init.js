// Read-only observation probe for live evidence (design-fix 후속 20260925 · live/index.md · 부록 D 4 · 7 · 8).
// Loaded with `agent-browser open --init-script`. It only observes: it writes a JSON log into the
// data-probe-log attribute on <html> (read back with `agent-browser get attr html data-probe-log`) and never
// touches product state, handlers or styles. Precedent: 20260924/fix/live/probe-init.js.
(() => {
  const t0 = performance.now();
  const now = () => Math.round(performance.now() - t0);
  const log = [];
  const put = () => {
    try { document.documentElement.setAttribute('data-probe-log', JSON.stringify(log.slice(-300))); } catch (e) { /* ignore */ }
  };
  const desc = (n) => {
    if (!(n instanceof Element)) return String(n);
    const id = n.getAttribute('data-testid');
    const raw = typeof n.className === 'string' ? n.className : (n.className && n.className.baseVal) || '';
    const cls = raw.trim().split(/\s+/).filter(Boolean).slice(0, 3).join('.');
    return n.tagName.toLowerCase() + (cls ? '.' + cls : '') + (id ? '[' + id + ']' : '');
  };
  const sample = (tag) => {
    const back = document.querySelector('.modal-back.mb-takeover');
    const modal = document.querySelector('[data-testid=upload-modal]');
    if (!back) { log.push([now(), 'f', tag, 'absent']); put(); return; }
    const bs = getComputedStyle(back);
    log.push([now(), 'f', tag, back.getAttribute('data-state') || 'open', bs.backgroundColor,
      modal ? Number(getComputedStyle(modal).opacity).toFixed(2) : null, back.hasAttribute('inert')]);
    put();
  };
  const burst = (tag) => {
    const s = performance.now();
    const f = () => { sample(tag); if (performance.now() - s < 600) requestAnimationFrame(f); };
    requestAnimationFrame(f);
  };
  const step = (m) => {
    const h = m.querySelector('.modal-h h3');
    return [m.getAttribute('data-mode'), m.getAttribute('data-scene'), h ? h.textContent : null];
  };
  const start = () => {
    new MutationObserver((muts) => {
      for (const m of muts) {
        if (m.type === 'attributes' && m.target instanceof Element && m.target.matches('.modal-back.mb-takeover')) {
          log.push([now(), 'state', m.target.getAttribute('data-state') || 'open', m.target.hasAttribute('inert')]);
          burst('state:' + (m.target.getAttribute('data-state') || 'open'));
        }
        if (m.type === 'childList') {
          for (const n of m.addedNodes) {
            if (!(n instanceof Element)) continue;
            const um = n.matches('[data-testid=upload-modal]') ? n : n.querySelector('[data-testid=upload-modal]');
            if (um) { log.push([now(), 'mount', ...step(um)]); burst('mount'); }
            if (n.matches('.pvx-back') || n.querySelector('.pvx-back')) log.push([now(), 'mount-pvx']);
            if (n.matches('.confirm-back') || n.querySelector('.confirm-back')) log.push([now(), 'mount-confirm']);
          }
          for (const n of m.removedNodes) {
            if (!(n instanceof Element)) continue;
            if (n.matches('[data-testid=upload-modal]') || n.querySelector('[data-testid=upload-modal]')) log.push([now(), 'unmount']);
            if (n.matches('.pvx-back') || n.querySelector('.pvx-back')) log.push([now(), 'unmount-pvx']);
          }
        }
      }
      put();
    }).observe(document.documentElement, { subtree: true, childList: true, attributes: true, attributeFilter: ['data-state', 'inert'] });
  };
  if (document.documentElement) start(); else document.addEventListener('DOMContentLoaded', start);
  // capture-phase pointerdown / click record: where the hit-test landed and whether it is inside the upload modal
  for (const type of ['pointerdown', 'click']) {
    window.addEventListener(type, (e) => {
      const t = e.target;
      log.push([now(), type, desc(t), Math.round(e.clientX), Math.round(e.clientY),
        t instanceof Element ? Boolean(t.closest('[data-testid=upload-modal]')) : false]);
      put();
    }, true);
  }
})();
