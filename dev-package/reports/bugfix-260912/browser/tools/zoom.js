// #27 · #28 실측 — 확대 줄의 뷰포트 안 가시성(스크롤 없이)과 한 줄 배치(세로 접힘) 여부.
(() => {
  const rowOf = (id) => document.querySelector(`[data-testid="${id}"]`);
  const measure = (row) => {
    if (!row) return null;
    const r = row.getBoundingClientRect();
    const btns = Array.from(row.querySelectorAll('button'));
    const tops = btns.map((b) => Math.round(b.getBoundingClientRect().top));
    const lines = Array.from(new Set(tops)).length;
    // 글자 세로 접힘 = 버튼 높이가 한 줄 높이의 1.6배 이상
    const wrapped = btns.map((b) => {
      const br = b.getBoundingClientRect();
      const lh = parseFloat(getComputedStyle(b).lineHeight) || 16;
      return { text: b.textContent, w: Math.round(br.width), h: Math.round(br.height),
        textWrapped: br.height > lh * 1.6 };
    });
    return {
      rect: { top: Math.round(r.top), bottom: Math.round(r.bottom), left: Math.round(r.left), right: Math.round(r.right) },
      inViewport: r.top >= 0 && r.bottom <= innerHeight && r.left >= 0 && r.right <= innerWidth,
      buttonRowCount: lines,
      buttons: wrapped,
    };
  };
  return {
    viewport: { w: innerWidth, h: innerHeight },
    inline: measure(rowOf('up-preview-zoom')),
    expand: measure(rowOf('pv-expand-zoom')),
    detail: measure(rowOf('ds-preview-zoom')),
  };
})();
