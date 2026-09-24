"""Compare two cdump outputs (computed styles of every element and pseudo-element, custom properties excluded)."""
import json, sys
before = json.load(open(sys.argv[1]))
after = json.load(open(sys.argv[2]))
pages = sorted(set(before) | set(after))
diff_pages = []
items = 0
for p in pages:
    if p not in before or p not in after:
        diff_pages.append((p, 'missing page')); continue
    hb, ha = before[p]['h'], after[p]['h']
    items += len(ha)
    if hb != ha:
        db = dict(x.split('=', 1) for x in hb); da = dict(x.split('=', 1) for x in ha)
        keys = sorted(set(db) | set(da), key=lambda k: (int(k.split(':')[0]), k))
        bad = [k for k in keys if db.get(k) != da.get(k)]
        diff_pages.append((p, f'{len(bad)} elements: ' + ', '.join(bad[:12])))
print(f'pages before {len(before)} after {len(after)} · items {items} · differing pages {len(diff_pages)}')
for p, why in diff_pages:
    print('  DIFF', p, why)
sys.exit(1 if diff_pages else 0)
