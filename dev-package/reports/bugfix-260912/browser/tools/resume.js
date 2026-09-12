// #33㉠ 실측 — 배너 「이어서 하기」로 연 모달이 재개로 무장했는가.
(() => {
  const modal = document.querySelector('[data-testid="upload-modal"]');
  if (!modal) return { modal: false };
  const hint = document.querySelector('[data-testid="up-resume-hint"]');
  const banner = document.querySelector('[data-testid="up-incomplete"]');
  return {
    modal: true,
    resumeHint: hint ? hint.textContent : null,
    incompleteBanner: banner ? banner.innerText.replace(/\n+/g, ' | ') : null,
    modalText: modal.innerText.replace(/\n+/g, ' | ').slice(0, 400),
  };
})();
