// Read-only observation probe for live evidence (design-fix 20260924 · fix/live/index.md).
// Loaded with `agent-browser open --init-script`. It only observes: it records timings into
// data-probe-* attributes on <html> (read back with `agent-browser get attr html ...`) and never
// touches product state, handlers or styles.
(() => {
  const now = () => Math.round(performance.now());
  const put = (k, arr) => {
    try { document.documentElement.setAttribute(k, JSON.stringify(arr.slice(-200))); } catch (e) { /* ignore */ }
  };
  // modal — opacity / transform / data-state per frame for 600ms after mount or data-state change
  const mlog = [];
  const msample = (tag) => {
    const m = document.querySelector('.modal.modal-takeover');
    if (!m) { mlog.push([now(), tag, 'absent']); put('data-probe-modal', mlog); return; }
    const cs = getComputedStyle(m);
    mlog.push([now(), tag, m.getAttribute('data-state') || 'open', Number(cs.opacity).toFixed(2), cs.transform]);
    put('data-probe-modal', mlog);
  };
  const burst = (tag) => {
    const s = performance.now();
    const f = () => { msample(tag); if (performance.now() - s < 600) requestAnimationFrame(f); };
    requestAnimationFrame(f);
  };
  const isModal = (n) => n instanceof Element && (n.matches('.modal-takeover') || n.querySelector('.modal-takeover'));
  const start = () => {
    new MutationObserver((muts) => {
      for (const m of muts) {
        if (m.type === 'attributes' && m.target instanceof Element && m.target.classList.contains('modal-takeover')) {
          mlog.push([now(), 'attr', m.target.getAttribute('data-state') || 'open']);
          burst('state:' + (m.target.getAttribute('data-state') || 'open'));
        }
        if (m.type === 'childList') {
          for (const n of m.addedNodes) if (isModal(n)) { mlog.push([now(), 'mount']); burst('mount'); }
          for (const n of m.removedNodes) if (isModal(n)) { mlog.push([now(), 'unmount']); put('data-probe-modal', mlog); }
        }
      }
    }).observe(document.documentElement, { subtree: true, childList: true, attributes: true, attributeFilter: ['data-state'] });
  };
  if (document.documentElement) start(); else document.addEventListener('DOMContentLoaded', start);
  // pan — pointer events and the preview layer transform per frame for 1500ms after pointerup
  const plog = [];
  const tr = () => {
    const l = document.querySelector('[data-testid=preview-layers]');
    if (!l) return null;
    const m = /translate\(([-\d.e]+)px, ([-\d.e]+)px\) scale\(([-\d.e]+)\)/.exec(l.getAttribute('style') || '');
    return m ? [Number(Number(m[1]).toFixed(1)), Number(Number(m[2]).toFixed(1)), Number(Number(m[3]).toFixed(3))] : null;
  };
  let downAt = 0;
  let upAt = 0;
  const where = (t) => (t instanceof Element ? t.tagName.toLowerCase() + '.' + String(t.className || '').split(' ').join('.') + (t.closest('[data-zoomable]') ? '@zoomable' : '') : String(t));
  window.addEventListener('pointerdown', (e) => {
    downAt = performance.now();
    plog.push(['down', 0, e.clientX, e.clientY, tr(), where(e.target), e.pointerId, e.pointerType]);
    put('data-probe-pan', plog);
  }, true);
  window.addEventListener('gotpointercapture', (e) => { plog.push(['gotcapture', Math.round(performance.now() - downAt), where(e.target)]); put('data-probe-pan', plog); }, true);
  window.addEventListener('lostpointercapture', (e) => { plog.push(['lostcapture', Math.round(performance.now() - downAt), where(e.target)]); put('data-probe-pan', plog); }, true);
  window.addEventListener('pointercancel', (e) => { plog.push(['cancel', Math.round(performance.now() - downAt), where(e.target)]); put('data-probe-pan', plog); }, true);
  // bubbling listener: runs after the element's own non-passive handler, so defaultPrevented tells whether the map took the wheel
  window.addEventListener('wheel', (e) => { plog.push(['wheel', Math.round(e.deltaY), where(e.target), e.defaultPrevented, tr()]); put('data-probe-pan', plog); }, { passive: true });
  window.addEventListener('pointermove', (e) => {
    if (!downAt || upAt > downAt) return;
    plog.push(['move', Math.round(performance.now() - downAt), e.clientX, e.clientY, tr()]);
    put('data-probe-pan', plog);
  }, true);
  window.addEventListener('pointerup', (e) => {
    upAt = performance.now();
    plog.push(['up', Math.round(upAt - downAt), e.clientX, e.clientY, tr()]);
    put('data-probe-pan', plog);
    const f = () => {
      const t = Math.round(performance.now() - upAt);
      plog.push(['f', t, tr()]);
      put('data-probe-pan', plog);
      if (t < 1500) requestAnimationFrame(f);
    };
    requestAnimationFrame(f);
  }, true);
})();
