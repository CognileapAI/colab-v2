// 분석 중 고지(⑧ · #24㉯) DOM 실측 — 칩·경과 시간·`다음 →` 비활성·사유 줄·title/aria-describedby.
(() => {
  const q = (s) => document.querySelector(s);
  const chip = q('[data-testid="up-analyze-chip"]');
  const elapsed = q('[data-testid="up-analyze-elapsed"]');
  const why = q('[data-testid="reg-open-why"]');
  const next = q('[data-testid="reg-open"]');
  const analyze = q('[data-testid="up-analyze"]');
  const cs = chip ? getComputedStyle(chip) : null;
  return {
    t: new Date().toISOString(),
    stage: analyze ? analyze.getAttribute('data-stage') : null,
    chipText: chip ? chip.textContent : null,
    chipClass: chip ? chip.className : null,
    chipAnimation: cs ? cs.animationName + ' ' + cs.animationDuration : null,
    elapsedText: elapsed ? elapsed.textContent : null,
    whyId: why ? why.id : null,
    whyText: why ? why.textContent : null,
    nextDisabled: next ? next.disabled : null,
    nextTitle: next ? next.getAttribute('title') : null,
    nextDescribedBy: next ? next.getAttribute('aria-describedby') : null,
    // 사유 줄이 버튼 「옆에」 있는지 — 같은 `.reggate` 안 형제 여부
    whySameGate: !!(why && next && why.closest('.reggate') === next.closest('.reggate')),
  };
})();
