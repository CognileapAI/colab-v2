"""Compare two cdump_p3 outputs (computed styles w/o custom properties) and summarise selector coverage."""
import json, sys, collections
before = json.load(open(sys.argv[1]))
after = json.load(open(sys.argv[2]))
pages = sorted(set(before) | set(after))
diff_pages = []
for p in pages:
    if p not in before or p not in after:
        diff_pages.append((p, 'missing page')); continue
    hb, ha = before[p]['h'], after[p]['h']
    if hb != ha:
        db = dict(x.split('=', 1) for x in hb); da = dict(x.split('=', 1) for x in ha)
        keys = sorted(set(db) | set(da), key=lambda k: (int(k.split(':')[0]), k))
        bad = [k for k in keys if db.get(k) != da.get(k)]
        diff_pages.append((p, f'{len(bad)} elements: ' + ', '.join(bad[:8])))
print(f'pages before {len(before)} after {len(after)} · differing pages {len(diff_pages)}')
for p, why in diff_pages:
    print('  DIFF', p, why)
print('elements compared', sum(len(after[p]['h']) for p in after if p in before))

# coverage: selector -> scenes where shown>0 (after build; before for the class-less RegisterArea div is the same testid)
sel_pages = collections.defaultdict(list)
sel_present = collections.defaultdict(list)
for p in sorted(after):
    for sel, c in after[p]['cover'].items():
        if 'err' in c:
            sel_pages[sel].append(p + '(ERR)'); continue
        if c['shown'] > 0: sel_pages[sel].append(p)
        elif c['n'] > 0: sel_present[sel].append(p)
out = {'shown': sel_pages, 'presentNotShown': sel_present}
json.dump(out, open(sys.argv[3], 'w'), ensure_ascii=False, indent=1)
sels = json.load(open('.visual/scratch/selectors.json'))
for sel in sels:
    shown = sel_pages.get(sel, [])
    scenes = sorted({'-'.join(x.split('-')[:-2]) for x in shown})
    print(f'{len(shown):3d} {sel} :: {", ".join(scenes)}' + (f' || present-not-shown {len(sel_present.get(sel, []))}' if not shown and sel_present.get(sel) else ''))
