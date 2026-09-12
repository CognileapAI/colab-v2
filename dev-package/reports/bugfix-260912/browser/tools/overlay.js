// 확장 오버레이 실측 — 고르개 줄 위치(#25⑥) · 확대 줄 한 줄(#28) · 기간 입력 겹침(#29).
(() => {
  const r = (s) => { const e = document.querySelector(s); return e ? e.getBoundingClientRect() : null; };
  const row = r('[data-testid="pvx-pick-row"]');
  const vp = r('[data-testid="pv-expand-viewport"]');
  const img = r('[data-testid="pv-expand-image"]');
  const zoom = r('[data-testid="pv-expand-zoom"]');
  const dlg = document.querySelector('[role="dialog"][aria-label="미리보기"]');
  // #29 — 오버레이 안에 기간 입력·기간 문면이 있는가, 그림과 겹치는가
  const periodHits = [];
  if (dlg) {
    for (const e of dlg.querySelectorAll('input, .fieldnote, label, p, span, button')) {
      const t = (e.textContent || '').trim();
      if (/기간|한 시점|달력|시작|종료/.test(t) && t.length < 60) {
        const b = e.getBoundingClientRect();
        periodHits.push({ tag: e.tagName, text: t.slice(0, 40),
          rect: { top: Math.round(b.top), left: Math.round(b.left), w: Math.round(b.width), h: Math.round(b.height) },
          overlapsImage: !!(img && b.width > 0 && b.left < img.right && b.right > img.left && b.top < img.bottom && b.bottom > img.top) });
      }
    }
  }
  const box = (b) => (b ? { top: Math.round(b.top), bottom: Math.round(b.bottom), left: Math.round(b.left), right: Math.round(b.right) } : null);
  return {
    viewport: { w: innerWidth, h: innerHeight },
    dialogText: dlg ? dlg.innerText.replace(/\n+/g, ' | ').slice(0, 300) : null,
    pickRow: box(row),
    expandViewport: box(vp),
    image: box(img),
    zoomRow: box(zoom),
    pickAboveViewport: !!(row && vp && row.bottom <= vp.top),
    zoomInViewport: !!(zoom && zoom.top >= 0 && zoom.bottom <= innerHeight),
    periodHits,
  };
})();
