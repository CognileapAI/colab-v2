// 브라우저 기억(`colab.upload.pending.*`) 실측 — #34 세 번째 선택지·#32 폐기의 대상.
(() => {
  const out = {};
  for (let i = 0; i < localStorage.length; i += 1) {
    const k = localStorage.key(i);
    if (k && k.startsWith('colab.upload.pending')) out[k] = JSON.parse(localStorage.getItem(k) || '[]');
  }
  const banner = document.querySelector('[data-testid="unfinished-uploads"]');
  return {
    pending: out,
    bannerRows: banner ? banner.querySelectorAll('.ub-row').length : null,
    bannerText: banner ? banner.innerText.replace(/\n+/g, ' | ') : null,
  };
})();
