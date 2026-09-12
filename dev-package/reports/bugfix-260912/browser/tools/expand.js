// 확장 오버레이 상태 확인 — 버튼 존재·위치, 오버레이 dialog 존재.
(() => {
  const b = document.querySelector('[data-testid="pv-expand"]');
  const dlg = document.querySelector('[role="dialog"][aria-label*="미리보기"], .pvx-b, [data-testid="pv-expand-viewport"]');
  const dialogs = Array.from(document.querySelectorAll('[role="dialog"]')).map((d) => d.getAttribute('aria-label'));
  return {
    btn: b ? { rect: b.getBoundingClientRect().toJSON(), disabled: b.disabled } : null,
    overlay: !!dlg,
    dialogs,
  };
})();
