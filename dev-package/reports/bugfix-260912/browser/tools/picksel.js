// 인라인·오버레이 고르개의 현재 값 대조(#25⑥ 선택 공유).
(() => {
  const v = (id) => {
    const s = document.querySelector(`[data-testid="${id}"]`);
    if (!s) return null;
    const o = s.options[s.selectedIndex];
    return { value: s.value, label: o ? o.textContent : null,
      values: Array.from(s.options).map((x) => x.value) };
  };
  return { inlineFile: v('up-pick-file'), expandFile: v('pvx-pick-file') };
})();
