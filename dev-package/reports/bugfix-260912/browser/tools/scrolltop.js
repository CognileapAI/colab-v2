// 업로드 모달 본문 스크롤을 맨 위로.
(() => {
  const b = document.querySelector('.modal-b.up-body');
  if (b) b.scrollTop = 0;
  const btn = document.querySelector('[data-testid="pv-expand"]');
  return { scrollTop: b ? b.scrollTop : null, btnTop: btn ? Math.round(btn.getBoundingClientRect().top) : null };
})();
