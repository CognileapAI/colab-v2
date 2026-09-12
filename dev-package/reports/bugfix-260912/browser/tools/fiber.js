// #33㉠ 실측 — 모달이 재개 식별자로 무장했는가. 화면에 그 표식이 안 서는 환경(저장 모드 local ·
// `/uploads/transfers/incomplete` 501)이라 React fiber 의 props 를 직접 읽는다.
(() => {
  const el = document.querySelector('[data-testid="upload-modal"]');
  if (!el) return { err: 'no modal' };
  const key = Object.keys(el).find((k) => k.startsWith('__reactFiber$'));
  if (!key) return { err: 'no fiber key' };
  let f = el[key];
  const found = [];
  let depth = 0;
  while (f && depth < 60) {
    const p = f.memoizedProps;
    if (p && typeof p === 'object') {
      if ('resumeRequest' in p) found.push({ at: depth, kind: 'resumeRequest', value: p.resumeRequest });
      if ('openRequest' in p) found.push({ at: depth, kind: 'openRequest', value: p.openRequest });
    }
    f = f.return;
    depth += 1;
  }
  return { found };
})();
