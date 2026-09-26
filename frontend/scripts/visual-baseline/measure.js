// Page script: capture metrics for one settled scene (capture.py --metrics / --metrics-only). Read-only: it reads
// boxes, computed styles and media state; it does not scroll or change the DOM.
// Spec: dev-package/prd/specs/S-DEVICE-WIDTH-INPUT-20260926.md 「구현 결정 · 수치 모드」 (L0b). Four metrics ported from
// the responsive audit's in-page collector (dev-package/reports/responsive-audit/20260925/summary.md column definitions):
//   targets    tap box of every target-list selector match (touch only). An input inside a label is measured by the label
//              box; `measure: 'row'` targets by their row (tr). A match without a box (display none · width or height 0 ·
//              visibility hidden) is recorded with box false = 「재지 않음」.
//   inputFont  text-entry input/select/textarea (not checkbox · radio · range · …) with computed font-size < 16 (touch only).
//   overflow   visible elements whose box, or whose own content (text wider than its box · overflow-x visible), passes
//              innerWidth, reduced to roots not clipped by an overflow container of their own (잘림 없는 루트). If the page
//              scrolls sideways (scrollWidth > clientWidth) and no such root is found, the document itself is the root.
//   coverage   map occlusion: % of the visible map image inside the map viewport covered by tool boxes, grid-sampled every
//              2 px. fourTools = legend · value lookup · coordinates · screenshot (union, overlaps counted once);
//              zoomGroup = every other tool box over the map (zoom row, fit button) — recorded only.
// Map scenes also record the map cell width (section.pv-map box width), the viewport's computed touch-action, its data-*
// attributes (drag axis), and the value panel state (안내 · 값 · 읽는 중 · 못 읽음).
// Called as `(<this file>)(opt)`: opt = {touch, targets: [{n, selector, measure?}], exempt: [{metric, selector}]}.
(function colabMeasure(opt) {
  const W = innerWidth;
  const r1 = (n) => Math.round(n * 10) / 10;
  const ids = new Map();
  const idOf = (el) => { if (!ids.has(el)) ids.set(el, ids.size + 1); return ids.get(el); };
  const clsOf = (el) => (typeof el.className === 'string' ? el.className : (el.getAttribute && el.getAttribute('class')) || '').trim();
  function hasBox(el) {
    const r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) return false;
    if (el.checkVisibility && !el.checkVisibility({ checkOpacity: false, checkVisibilityCSS: true })) return false;
    return true;
  }
  function pathOf(el) {
    const parts = [];
    for (let e = el, d = 0; e && e.nodeType === 1 && d < 4 && e !== document.body; e = e.parentElement, d++) {
      let s = e.tagName.toLowerCase();
      if (e.id) s += '#' + e.id;
      const c = clsOf(e).split(/\s+/).filter(Boolean).slice(0, 2);
      if (c.length) s += '.' + c.join('.');
      const tid = e.getAttribute('data-testid');
      if (tid) s += '[data-testid=' + tid + ']';
      parts.unshift(s);
      if (e.id) break;
    }
    return parts.join(' > ');
  }
  const exemptOf = (el, metric) => opt.exempt.map((x, i) => [x, i])
    .filter(([x]) => x.metric === metric && (() => { try { return el.matches(x.selector); } catch (e) { return false; } })())
    .map(([, i]) => i);
  // nearest clipping ancestor (overflow != visible), stopping at a fixed-position boundary
  function clipOf(el) {
    for (let cur = el, e = el.parentElement; e; cur = e, e = e.parentElement) {
      if (getComputedStyle(cur).position === 'fixed') return null;
      const cs = getComputedStyle(e);
      if (cs.overflowX !== 'visible' || cs.overflowY !== 'visible') return e;
    }
    return null;
  }

  const out = { media: { coarse: matchMedia('(pointer: coarse)').matches, hover: matchMedia('(hover: hover)').matches, width: W, height: innerHeight } };
  const visible = Array.from(document.body.querySelectorAll('*')).filter((el) => !['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE', 'LINK', 'META'].includes(el.tagName) && hasBox(el));
  const visSet = new Set(visible);

  // ---- targets (touch only)
  const claimed = new Set();
  if (opt.touch) {
    out.targets = opt.targets.map((t) => {
      let els;
      try { els = Array.from(document.querySelectorAll(t.selector)); } catch (e) { return { n: t.n, error: 'bad selector ' + t.selector }; }
      const hits = els.map((el) => {
        let m = el;
        let via = 'self';
        if (t.measure === 'row' && el.closest('tr')) { m = el.closest('tr'); via = 'row'; }
        else if (el.matches('input, select, textarea') && el.closest('label')) { m = el.closest('label'); via = 'label'; }
        const r = m.getBoundingClientRect();
        claimed.add(el);
        return { id: idOf(el), w: r1(r.width), h: r1(r.height), box: hasBox(m), via, path: pathOf(el), exempt: exemptOf(el, '44') };
      });
      return { n: t.n, hits };
    });
    const TSEL = 'button, a[href], input, select, textarea, summary, [role=button], [tabindex]:not([tabindex="-1"])';
    const small = Array.from(document.querySelectorAll(TSEL)).filter((el) => {
      if (claimed.has(el) || !visSet.has(el) || (el.tagName === 'INPUT' && el.type === 'hidden')) return false;
      const r = el.getBoundingClientRect();
      return r.width > 1 && r.height > 1 && (r.width < 44 || r.height < 44);
    });
    out.smallOther = { count: small.length, top: small.slice(0, 10).map((el) => { const r = el.getBoundingClientRect(); return { path: pathOf(el), wh: r1(r.width) + 'x' + r1(r.height) }; }) };
    const NOZOOM = ['checkbox', 'radio', 'range', 'color', 'file', 'submit', 'button', 'reset', 'image', 'hidden'];
    const fields = Array.from(document.querySelectorAll('input, select, textarea')).filter((el) => visSet.has(el) && !(el.tagName === 'INPUT' && NOZOOM.includes(el.type)));
    out.inputFont = {
      of: fields.length,
      small: fields.filter((el) => parseFloat(getComputedStyle(el).fontSize) < 16)
        .map((el) => ({ path: pathOf(el), fontSize: parseFloat(getComputedStyle(el).fontSize), exempt: exemptOf(el, '16') })),
    };
  } else {
    out.targets = null;
    out.smallOther = null;
    out.inputFont = null;
  }

  // ---- horizontal overflow: unclipped roots past innerWidth
  const de = document.documentElement;
  const off = new Set(visible.filter((el) => el.getBoundingClientRect().right > W + 1));
  const unclipped = (el) => { const c = clipOf(el); return !c || c === document.body; };
  const allRoots = Array.from(off).filter((el) => !off.has(el.parentElement));
  // Text that runs past its own box (a long unbreakable name) moves no element box past the edge: an element whose
  // content (scrollWidth) runs past innerWidth with overflow-x visible is a root too.
  const textOff = new Set(visible.filter((el) => el.clientWidth > 0 && el.scrollWidth > el.clientWidth + 1
    && getComputedStyle(el).overflowX === 'visible' && el.getBoundingClientRect().left + el.scrollWidth > W + 1));
  // Box roots are the outermost boxes past the edge; text roots are the innermost elements whose content runs past it
  // (every ancestor's scrollWidth carries the same overflow up to #root).
  const textRoots = Array.from(textOff).filter((el) => !Array.from(textOff).some((o) => o !== el && el.contains(o)));
  const roots = [...new Set([...allRoots, ...textRoots])].filter(unclipped);
  const rightOf = (el) => (textOff.has(el) ? el.getBoundingClientRect().left + el.scrollWidth : el.getBoundingClientRect().right);
  roots.sort((a, b) => rightOf(b) - rightOf(a));
  const rootList = roots.map((el) => ({ path: pathOf(el), right: r1(rightOf(el)), text: textOff.has(el), exempt: exemptOf(el, '넘침') }));
  // The page itself scrolls sideways but no root was found: the document is the root.
  if (!rootList.length && de.scrollWidth > de.clientWidth + 1) rootList.push({ path: 'html', right: de.scrollWidth, text: false, exempt: exemptOf(de, '넘침') });
  out.overflow = {
    scrollWidth: de.scrollWidth, clientWidth: de.clientWidth, innerWidth: W, offRight: off.size,
    clipped: allRoots.filter((el) => !unclipped(el)).slice(0, 5).map((el) => ({ path: pathOf(el), right: r1(el.getBoundingClientRect().right), clip: pathOf(clipOf(el)) })),
    roots: rootList,
  };

  // ---- map (any scene with a visible map viewport)
  const vpEl = document.querySelector('[data-testid=pv-expand-viewport]') && visSet.has(document.querySelector('[data-testid=pv-expand-viewport]'))
    ? document.querySelector('[data-testid=pv-expand-viewport]')
    : Array.from(document.querySelectorAll('.pv-viewport')).find((e) => visSet.has(e));
  if (!vpEl) { out.map = null; return out; }
  const cellEl = Array.from(document.querySelectorAll('section.pv-map')).find((e) => visSet.has(e) && e.contains(vpEl));
  const vr = vpEl.getBoundingClientRect();
  const V = { x: vr.left, y: vr.top, r: vr.right, b: vr.bottom };
  let imgs = Array.from(vpEl.querySelectorAll('img.pv-tile')).filter((e) => visSet.has(e));
  if (!imgs.length) imgs = Array.from(vpEl.querySelectorAll('img, canvas')).filter((e) => visSet.has(e));
  let I = null;
  for (const im of imgs) {
    const r = im.getBoundingClientRect();
    I = I ? { x: Math.min(I.x, r.left), y: Math.min(I.y, r.top), r: Math.max(I.r, r.right), b: Math.max(I.b, r.bottom) } : { x: r.left, y: r.top, r: r.right, b: r.bottom };
  }
  if (I) I = { x: Math.max(I.x, V.x), y: Math.max(I.y, V.y), r: Math.min(I.r, V.r), b: Math.min(I.b, V.b) };
  if (I && (I.r <= I.x || I.b <= I.y)) I = null;
  const container = vpEl.closest('.pv-frame') || vpEl.closest('.pv-map') || vpEl.parentElement;
  const layers = Array.from(vpEl.querySelectorAll('.pv-layers'));
  const ovEls = [];
  for (const el of Array.from(container.querySelectorAll('*'))) {
    // map content (image, tiles, basemap) is what is covered, not a tool
    if (!visSet.has(el) || el === vpEl || el.contains(vpEl) || layers.some((l) => l.contains(el))) continue;
    const r = el.getBoundingClientRect();
    if (r.right <= V.x || r.left >= V.r || r.bottom <= V.y || r.top >= V.b) continue;
    // the tool layer and its corner groups are pointer-events:none containers: count their children instead
    if (/(^|\s)pv-overlay(-tr|-br|-bl)?(\s|$)/.test(clsOf(el))) continue;
    // outside the viewport subtree only boxes drawn over it (positioned) count
    if (!vpEl.contains(el) && !['absolute', 'fixed', 'sticky'].includes(getComputedStyle(el).position)) continue;
    if (ovEls.some((o) => o.contains(el))) continue;
    ovEls.push(el);
  }
  const TOOLS = { legend: '.pv-legend', value: '.pv-value', hud: '.pv-hud', shot: '.pv-shot' };
  const toolOf = (el) => {
    for (const [k, sel] of Object.entries(TOOLS)) if (el.matches(sel) || el.closest(sel) || el.querySelector(sel)) return k;
    return 'zoomGroup';
  };
  const ov = ovEls.map((el) => { const r = el.getBoundingClientRect(); return { el, tool: toolOf(el), x: r.left, y: r.top, r: r.right, b: r.bottom }; });
  let coverage = null;
  if (I) {
    const step = 2;
    let total = 0;
    const count = { all: 0, fourTools: 0, zoomGroup: 0, legend: 0, value: 0, hud: 0, shot: 0 };
    const per = ov.map(() => 0);
    for (let y = I.y + step / 2; y < I.b; y += step) {
      for (let x = I.x + step / 2; x < I.r; x += step) {
        total++;
        const hit = new Set();
        ov.forEach((o, k) => { if (x >= o.x && x < o.r && y >= o.y && y < o.b) { per[k]++; hit.add(o.tool); } });
        if (hit.size) count.all++;
        if (['legend', 'value', 'hud', 'shot'].some((k) => hit.has(k))) count.fourTools++;
        for (const k of hit) count[k]++;
      }
    }
    const pct = (c) => (total ? r1((100 * c) / total) : null);
    coverage = {
      imagePct: pct(count.all), fourTools: pct(count.fourTools), zoomGroup: pct(count.zoomGroup),
      tools: { legend: pct(count.legend), value: pct(count.value), hud: pct(count.hud), shot: pct(count.shot) },
      imageRect: { x: r1(I.x), y: r1(I.y), w: r1(I.r - I.x), h: r1(I.b - I.y) },
      overlays: ov.map((o, k) => ({ path: pathOf(o.el), tool: o.tool, rect: { x: r1(o.x), y: r1(o.y), w: r1(o.r - o.x), h: r1(o.b - o.y) }, imagePct: pct(per[k]) })),
    };
  }
  const panel = document.querySelector('[data-testid=value-lookup]');
  const valueState = !panel ? null
    : panel.querySelector('[data-testid=value-lookup-value]') ? '값'
    : panel.querySelector('[data-testid=value-lookup-unavailable]') ? '못 읽음'
    : /읽는 중/.test(panel.textContent || '') ? '읽는 중' : '안내';
  const viewportData = Object.assign({}, vpEl.dataset);
  out.map = {
    cellWidth: cellEl ? r1(cellEl.getBoundingClientRect().width) : null,
    viewport: { testid: vpEl.getAttribute('data-testid'), x: r1(V.x), y: r1(V.y), w: r1(V.r - V.x), h: r1(V.b - V.y) },
    touchAction: getComputedStyle(vpEl).touchAction,
    zoom: (() => { const z = vpEl.querySelector('[data-zoom-scale]'); return z ? { scale: Number(z.dataset.zoomScale), base: Number(z.dataset.zoomBaseScale) } : null; })(),
    dragAxis: viewportData.dragAxis ?? viewportData.panAxis ?? null,
    viewportData,
    valueState,
    coverage,
  };
  return out;
})
