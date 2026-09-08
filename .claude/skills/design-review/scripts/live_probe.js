// live_probe.js — agent-browser `eval --stdin` payload. Returns JSON only; mutates nothing.
// Measures on the LIVE page what css_audit.py cannot: inherited contrast, computed font size,
// :active / reduced-motion rules actually loaded, transition durations on interactive elements.
// Usage: cat live_probe.js | agent-browser --session <s> eval --stdin --json
(() => {
  const AA = 4.5, MIN_PX = 13;
  const lum = (r, g, b) => {
    const f = c => { c /= 255; return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; };
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
  };
  const parse = s => { const m = s && s.match(/rgba?\(([^)]+)\)/); if (!m) return null;
    const p = m[1].split(',').map(Number); return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 }; };
  const bgOf = el => { // walk up until an opaque background
    for (let n = el; n; n = n.parentElement) { const c = parse(getComputedStyle(n).backgroundColor); if (c && c.a >= 0.99) return c; }
    return { r: 255, g: 255, b: 255, a: 1 };
  };
  const ratio = (a, b) => { const x = lum(a.r, a.g, a.b), y = lum(b.r, b.g, b.b); return +((Math.max(x, y) + .05) / (Math.min(x, y) + .05)).toFixed(2); };
  const sel = el => { let s = el.tagName.toLowerCase(); if (el.id) s += '#' + el.id; if (el.className && typeof el.className === 'string') s += '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.'); return s; };
  const visible = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== 'hidden'; };

  // 1. text nodes: font size + inherited contrast
  const small = [], lowContrast = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const seen = new Set();
  for (let t; (t = walker.nextNode());) {
    if (!t.textContent.trim()) continue;
    const el = t.parentElement; if (!el || seen.has(el) || !visible(el)) continue; seen.add(el);
    const cs = getComputedStyle(el); const px = parseFloat(cs.fontSize);
    const fg = parse(cs.color); if (!fg) continue;
    const r = ratio(fg, bgOf(el));
    const rec = { sel: sel(el), text: t.textContent.trim().slice(0, 24), px, ratio: r };
    if (px < MIN_PX) small.push(rec);
    if (r < AA) lowContrast.push(rec);
  }

  // 2. stylesheet facts: :active rules, reduced-motion blocks, keyframes
  let activeRules = 0, reducedMotionBlocks = 0, keyframes = 0, sheets = 0, blocked = 0;
  for (const ss of document.styleSheets) {
    let rules; try { rules = ss.cssRules; } catch { blocked++; continue; } sheets++;
    for (const r of rules) {
      if (r.selectorText && /:active/.test(r.selectorText)) activeRules++;
      if (r.media && /prefers-reduced-motion/.test(r.media.mediaText)) reducedMotionBlocks++;
      if (r.type === CSSRule.KEYFRAMES_RULE) keyframes++;
    }
  }

  // 3. interactive elements: transition durations / properties
  const interactive = [...document.querySelectorAll('button, a[href], [role=button], input, select, [tabindex]')].filter(visible).slice(0, 200);
  const transitions = {};
  for (const el of interactive) { const cs = getComputedStyle(el); const k = cs.transitionProperty + ' ' + cs.transitionDuration; transitions[k] = (transitions[k] || 0) + 1; }

  return {
    url: location.href, viewport: { w: innerWidth, h: innerHeight },
    media: { dark: matchMedia('(prefers-color-scheme: dark)').matches, reducedMotion: matchMedia('(prefers-reduced-motion: reduce)').matches },
    counts: { textElements: seen.size, small: small.length, lowContrast: lowContrast.length, interactive: interactive.length, sheets, blockedSheets: blocked, activeRules, reducedMotionBlocks, keyframes },
    small: small.slice(0, 80), lowContrast: lowContrast.slice(0, 80), transitions,
  };
})()
