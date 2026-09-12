// #30 실측 — 부모 찾기 창의 후보 행 수(`lin-pick-*`)와 빈 상태 문면.
(() => {
  const rows = Array.from(document.querySelectorAll('[data-testid^="lin-pick-"]'));
  const dlg = rows.length ? rows[0].closest('[role="dialog"], .lin-picker') : document.querySelector('.lin-picker');
  const text = dlg ? dlg.innerText : '';
  return {
    rowCount: rows.length,
    firstRows: rows.slice(0, 3).map((r) => (r.innerText || '').split('\n')[0]),
    emptyPhrases: text.split('\n').filter((l) => /없어요/.test(l)),
    filters: Array.from(document.querySelectorAll('.lin-picker select, .lin-picker input')).map((e) => ({
      testid: e.getAttribute('data-testid'), tag: e.tagName, value: e.value,
    })),
  };
})();
