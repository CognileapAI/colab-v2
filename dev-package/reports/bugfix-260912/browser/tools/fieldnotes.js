// #31 실측 — 등록 카드 안내 문단 4건이 「라벨 → 컨트롤 → 설명문」 순서인가.
(() => {
  const notes = Array.from(document.querySelectorAll('.up-split-form .fieldnote, [data-testid="up-split-form"] .fieldnote'));
  return notes.map((n) => {
    const box = n.parentElement;
    const kids = Array.from(box.children);
    const noteIdx = kids.indexOf(n);
    const labelIdx = kids.findIndex((k) => k.tagName === 'LABEL');
    const ctrlIdx = kids.findIndex((k) => ['INPUT', 'SELECT', 'TEXTAREA', 'BUTTON'].includes(k.tagName)
      || k.querySelector('input, select, textarea, button'));
    const r = n.getBoundingClientRect();
    const ctrl = ctrlIdx >= 0 ? kids[ctrlIdx] : null;
    const cr = ctrl ? ctrl.getBoundingClientRect() : null;
    return {
      testid: n.getAttribute('data-testid'),
      text: (n.textContent || '').trim().slice(0, 40),
      boxClass: box.className,
      order: kids.map((k) => k.tagName + (k.getAttribute('data-testid') ? '#' + k.getAttribute('data-testid') : '')),
      labelIdx, ctrlIdx, noteIdx,
      orderOk: labelIdx >= 0 && ctrlIdx > labelIdx && noteIdx > ctrlIdx,
      noteTop: Math.round(r.top), ctrlTop: cr ? Math.round(cr.top) : null,
      noteBelowControl: !!(cr && r.top >= cr.bottom - 2),
    };
  });
})();
