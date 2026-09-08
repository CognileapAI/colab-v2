#!/usr/bin/env python3
"""Static design audit for frontend CSS — deterministic baseline for /design-review.

Measures (no judgement, no edits):
  A. font-size declarations below 13px            (accessibility floor · WU-A11 ⑦⑧)
  B. negative margins                             (spacing ownership · WU-A11 ⑩)
  C. var(--token) references not defined anywhere (dead style · WU-A11 ⑪)
  D. box-shadow declarations                      (shadow policy · WU-A11 ⑥ — cards 0, popovers allowed)
  E. transition/animation per file vs. prefers-reduced-motion presence  (apple-design §Reduced motion)
  F. text/background color pairs on the same rule → WCAG contrast ratio (tokens resolved from tokens.css)
  G. custom-property definitions outside tokens.css (token vocabulary drift · per-file :root redefinitions)

Usage:  python3 css_audit.py [--root frontend/src] [--md out.md] [--json out.json] [FILES...]
Exit code is always 0; this is a measurement, not a gate.
"""
import argparse, json, os, re, sys
from pathlib import Path

PX_RE = re.compile(r'font-size\s*:\s*([0-9.]+)px', re.I)
NEG_MARGIN_RE = re.compile(r'margin(?:-(?:top|right|bottom|left))?\s*:\s*[^;{}]*', re.I)
NEG_NUM_RE = re.compile(r'(?<![\w(-])-\d')  # a real negative number, not the "-5" inside var(--space-5)
VAR_REF_RE = re.compile(r'var\(\s*(--[a-zA-Z0-9_-]+)\s*(?:,[^)]*)?\)')
VAR_DEF_RE = re.compile(r'(--[a-zA-Z0-9_-]+)\s*:\s*([^;{}]+);')
SHADOW_RE = re.compile(r'box-shadow\s*:\s*([^;{}]+)', re.I)
MOTION_RE = re.compile(r'\b(transition|animation|@keyframes)\b', re.I)
RULE_RE = re.compile(r'([^{}]+)\{([^{}]*)\}', re.S)
HEX_RE = re.compile(r'#([0-9a-fA-F]{3,8})\b')


def rel_lum(hexcol):
    h = hexcol.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    if len(h) == 8:
        h = h[:6]
    if len(h) != 6:
        return None
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))

    def lin(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast(fg, bg):
    a, b = rel_lum(fg), rel_lum(bg)
    if a is None or b is None:
        return None
    hi, lo = max(a, b), min(a, b)
    return round((hi + 0.05) / (lo + 0.05), 2)


def line_of(text, idx):
    return text.count('\n', 0, idx) + 1


def collect_defs(files):
    defs = {}
    for f in files:
        for m in VAR_DEF_RE.finditer(strip_comments(f.read_text(encoding='utf-8', errors='replace'))):
            defs.setdefault(m.group(1), m.group(2).strip())
    return defs


def resolve(value, defs, depth=0):
    value = value.strip()
    m = VAR_REF_RE.fullmatch(value)
    if m and depth < 6:
        return resolve(defs.get(m.group(1), value), defs, depth + 1)
    return value


COMMENT_RE = re.compile(r'/\*.*?\*/', re.S)


def strip_comments(text):
    """Blank out /* … */ comments but keep newlines so line numbers stay true."""
    return COMMENT_RE.sub(lambda m: re.sub(r'[^\n]', ' ', m.group(0)), text)


def audit_file(path, defs, root):
    text = strip_comments(path.read_text(encoding='utf-8', errors='replace'))
    rel = os.path.relpath(path, root)
    out = {'file': rel, 'small_font': [], 'neg_margin': [], 'undefined_token': [],
           'shadow': [], 'local_token_def': [], 'motion_lines': 0, 'reduced_motion': '@media (prefers-reduced-motion' in text or 'prefers-reduced-motion' in text,
           'contrast': []}
    for m in PX_RE.finditer(text):
        if float(m.group(1)) < 13:
            out['small_font'].append({'line': line_of(text, m.start()), 'px': float(m.group(1))})
    for m in NEG_MARGIN_RE.finditer(text):
        if NEG_NUM_RE.search(m.group(0)):
            out['neg_margin'].append({'line': line_of(text, m.start()), 'decl': m.group(0).strip()})
    if path.name != 'tokens.css':
        for m in VAR_DEF_RE.finditer(text):
            out['local_token_def'].append({'line': line_of(text, m.start()), 'token': m.group(1)})
    for m in VAR_REF_RE.finditer(text):
        name = m.group(1)
        has_fallback = ',' in m.group(0)
        if name not in defs:
            out['undefined_token'].append({'line': line_of(text, m.start()), 'token': name, 'fallback': has_fallback})
    for m in SHADOW_RE.finditer(text):
        out['shadow'].append({'line': line_of(text, m.start()), 'value': m.group(1).strip()})
    out['motion_lines'] = len(MOTION_RE.findall(text))
    for rm in RULE_RE.finditer(text):
        sel, body = rm.group(1).strip(), rm.group(2)
        color = bg = None
        for d in body.split(';'):
            if ':' not in d:
                continue
            k, v = d.split(':', 1)
            k = k.strip().lower()
            if k == 'color':
                color = resolve(v, defs)
            elif k in ('background', 'background-color'):
                bg = resolve(v, defs)
        if color and bg:
            fg_hex = HEX_RE.search(color)
            bg_hex = HEX_RE.search(bg)
            if fg_hex and bg_hex:
                if len(fg_hex.group(1)) in (4, 8) or len(bg_hex.group(1)) in (4, 8):
                    continue  # alpha channel: contrast depends on what is underneath → not measurable statically
                ratio = contrast(fg_hex.group(0), bg_hex.group(0))
                if ratio is not None:
                    out['contrast'].append({'line': line_of(text, rm.start()), 'selector': ' '.join(sel.split())[:60],
                                            'fg': fg_hex.group(0), 'bg': bg_hex.group(0), 'ratio': ratio,
                                            'aa': ratio >= 4.5})
    return out


def to_md(results, defs_count):
    L = ['# css_audit — static measurement', '',
         f'files {len(results)} · tokens defined {defs_count} · thresholds: font ≥13px · contrast ≥4.5:1 (AA)', '',
         '| file | <13px | neg margin | undefined token | local token def | box-shadow | motion decl | reduced-motion | contrast <4.5 |',
         '|---|---|---|---|---|---|---|---|---|']
    for r in results:
        low = [c for c in r['contrast'] if not c['aa']]
        L.append(f"| `{r['file']}` | {len(r['small_font'])} | {len(r['neg_margin'])} | {len(r['undefined_token'])} | {len(r['local_token_def'])} | "
                 f"{len(r['shadow'])} | {r['motion_lines']} | {'yes' if r['reduced_motion'] else ('—' if r['motion_lines'] == 0 else 'NO')} | {len(low)} |")
    L += ['', '## Detail (path:line · value)', '']
    for r in results:
        items = []
        items += [f"`{r['file']}:{x['line']}` font-size {x['px']}px" for x in r['small_font']]
        items += [f"`{r['file']}:{x['line']}` `{x['decl']}`" for x in r['neg_margin']]
        items += [f"`{r['file']}:{x['line']}` undefined `{x['token']}`" + (' (has fallback)' if x['fallback'] else ' (no fallback → declaration invalid)') for x in r['undefined_token']]
        items += [f"`{r['file']}:{x['line']}` box-shadow `{x['value']}`" for x in r['shadow']]
        items += [f"`{r['file']}:{x['line']}` local token def `{x['token']}` (outside tokens.css)" for x in r['local_token_def']]
        items += [f"`{r['file']}:{x['line']}` `{x['selector']}` {x['fg']} on {x['bg']} → **{x['ratio']}:1** (AA fail)" for x in r['contrast'] if not x['aa']]
        if items:
            L.append(f"### {r['file']}")
            L += [f'- {i}' for i in items]
            L.append('')
    return '\n'.join(L) + '\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='frontend/src')
    ap.add_argument('--md')
    ap.add_argument('--json')
    ap.add_argument('files', nargs='*')
    a = ap.parse_args()
    root = Path(a.root)
    all_css = sorted(root.rglob('*.css'))
    targets = [Path(f) for f in a.files] if a.files else all_css
    defs = collect_defs(all_css)
    results = [audit_file(p, defs, root) for p in targets]
    md = to_md(results, len(defs))
    if a.md:
        Path(a.md).write_text(md, encoding='utf-8')
    if a.json:
        Path(a.json).write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding='utf-8')
    if not a.md:
        sys.stdout.write(md)


if __name__ == '__main__':
    main()
