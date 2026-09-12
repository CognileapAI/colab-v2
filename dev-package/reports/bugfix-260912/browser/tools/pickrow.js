// 고르개 줄(#25⑵ · ⑥) 실측 — 세 컨트롤의 옵션, 4:3 틀(`.pv-frame`) 대비 DOM·좌표 위치.
(() => {
  const out = { viewport: { w: innerWidth, h: innerHeight } };
  for (const prefix of ["up", "pvx", "dt"]) {
    const row = document.querySelector(`[data-testid="${prefix}-pick-row"]`);
    if (!row) { out[prefix] = null; continue; }
    const wrap = row.closest('.pv-frame-wrap');
    const frame = wrap ? wrap.querySelector('.pv-frame') : null;
    out[prefix] = {
      selects: Array.from(row.querySelectorAll('select')).map((s) => ({
        testid: s.getAttribute('data-testid'), disabled: s.disabled, value: s.value,
        options: Array.from(s.options).map((o) => o.textContent),
      })),
      insideFrame: !!row.closest('.pv-frame'),
      siblingOfFrame: !!(frame && row.parentElement === frame.parentElement),
      rowBefore: !!(frame && (row.compareDocumentPosition(frame) & Node.DOCUMENT_POSITION_FOLLOWING)),
      rowTop: Math.round(row.getBoundingClientRect().top),
      frameTop: frame ? Math.round(frame.getBoundingClientRect().top) : null,
    };
  }
  return out;
})();
