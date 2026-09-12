// 메인 화면 「올리다 만 것」 카드로 스크롤.
(() => {
  const b = document.querySelector('[data-testid="unfinished-uploads"]');
  if (!b) return { err: 'no banner' };
  b.scrollIntoView({ block: 'center' });
  const r = b.getBoundingClientRect();
  return { top: Math.round(r.top), rows: b.querySelectorAll('.ub-row').length,
    buttons: Array.from(b.querySelectorAll('button')).map((x) => x.getAttribute('data-testid')) };
})();
