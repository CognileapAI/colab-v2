# Width sweep summary (320 -> 1440 step 20, height 900, no screenshots)

- Touch emulation ON for width <= 1180 (mobile:true, hover:none, pointer:coarse), OFF above (mouse: hover:hover, pointer:fine). gnb-more swept only <= 840 (its scene widths max 768; `.gnb-more` exists <= 900). Each width is a fresh load with the same capture.py sequence and actions as the captures.
- **break** between consecutive widths a->b = any of: visible element count changes (`vis`), visible interactive count changes (`inter`), distinct left edges of blocks >=120x24 px (8 px buckets) change by >=2 (`cols`), document height changes by >10%% (`height`), smallTargets count changes within touch (`small`). The 1180->1200 step also switches touch->mouse and is listed separately (`input-switch`). `css:` = @media conditions whose match flipped at that step (from the page stylesheets).
- Ranges: widths where the condition holds. offRight is raw (includes clipped offenders); `unclipped` = offending roots not inside their own overflow container. `widened` = layout viewport widened by overflow under mobile emulation (spec overflowX reads 0; `scrollWidth-device` > 0).

## catalog

- widths measured: 57 (320-1440); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: none
- offRight > 0 (raw): 320-1080
- offRight unclipped roots > 0: none
- first offender (by widths): table.tbl.catalog [clipped by div.tblwrap] x39
- smallTargets (touch widths): min 8 @320, max 24 @920
- candidate breaks (7):
  - 380->400 (weak: cols only): cols 8->10
  - 640->660: vis +4, small +12; css: (width <= 640px)
  - 740->760: vis +1; css: (width <= 740px)
  - 880->900: vis +2, cols 11->13; css: (width <= 880px)
  - 900->920: vis +3, inter +1, height 1100->962, small +4; css: (width <= 900px)
  - 960->980 (weak: cols only): cols 11->13
  - 1100->1120: vis -1; css: (width <= 1100px)

## lab

- widths measured: 57 (320-1440); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: none
- offRight > 0 (raw): none
- offRight unclipped roots > 0: none
- smallTargets (touch widths): min 9 @320, max 21 @920
- candidate breaks (12):
  - 340->360 (weak: cols only): cols 4->6
  - 380->400 (weak: cols only): cols 6->8
  - 640->660: vis +4, small +8; css: (width <= 640px)
  - 700->720 (weak: cols only): cols 9->13
  - 740->760: vis +1; css: (width <= 740px)
  - 880->900: vis +2, cols 14->17; css: (width <= 880px)
  - 900->920: vis +3, inter +1, cols 17->8, height 1835->1264, small +4; css: (width <= 900px)
  - 940->960 (weak: cols only): cols 8->10
  - 960->980 (weak: cols only): cols 10->13
  - 1060->1080 (weak: cols only): cols 13->11
  - 1160->1180 (weak: cols only): cols 12->16
  - 1420->1440 (weak: cols only): cols 17->15

## empty

- widths measured: 57 (320-1440); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: none
- offRight > 0 (raw): none
- offRight unclipped roots > 0: none
- smallTargets (touch widths): min 5 @320, max 11 @920
- candidate breaks (12):
  - 340->360 (weak: cols only): cols 4->6
  - 380->400 (weak: cols only): cols 6->8
  - 640->660: vis +4, small +2; css: (width <= 640px)
  - 700->720 (weak: cols only): cols 9->13
  - 740->760: vis +1; css: (width <= 740px)
  - 880->900: vis +2, cols 14->17; css: (width <= 880px)
  - 900->920: vis +3, inter +1, cols 17->8, height 1461->1161, small +4; css: (width <= 900px)
  - 940->960 (weak: cols only): cols 8->10
  - 960->980 (weak: cols only): cols 10->13
  - 1060->1080 (weak: cols only): cols 13->11
  - 1160->1180 (weak: cols only): cols 12->16
  - 1420->1440 (weak: cols only): cols 17->15

## projects

- widths measured: 57 (320-1440); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: none
- offRight > 0 (raw): none
- offRight unclipped roots > 0: none
- smallTargets (touch widths): min 3 @320, max 9 @920
- candidate breaks (12):
  - 320->340 (weak: cols only): cols 3->5
  - 380->400 (weak: cols only): cols 5->7
  - 440->460 (weak: cols only): cols 7->10
  - 640->660: vis +4, height 1540->1006, small +2; css: (width <= 640px)
  - 740->760: vis +1; css: (width <= 740px)
  - 800->820 (weak: cols only): cols 8->11
  - 880->900: vis +2, cols 11->13; css: (width <= 880px)
  - 900->920: vis +3, inter +1, cols 13->17, small +4; css: (width <= 900px)
  - 920->940 (weak: cols only): cols 17->9
  - 1000->1020: cols 10->12; css: (width <= 1000px)
  - 1180->1200 (input-switch): cols 11->16; css: (pointer: coarse) | (width <= 1180px) | (width <= 640px), (pointer: coarse)
  - 1220->1240 (weak: cols only): cols 17->14

## project-table

- widths measured: 57 (320-1440); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: none
- offRight > 0 (raw): 320-700
- offRight unclipped roots > 0: none
- first offender (by widths): table.pj-table [clipped by div.pj-ds-scroll] x20
- smallTargets (touch widths): min 3 @320, max 9 @920
- candidate breaks (8):
  - 320->340 (weak: cols only): cols 3->5
  - 380->400 (weak: cols only): cols 5->7
  - 640->660: vis +4, small +2; css: (width <= 640px)
  - 740->760: vis +1; css: (width <= 740px)
  - 880->900: vis +2; css: (width <= 880px)
  - 900->920: vis +3, inter +1, cols 9->5, small +4; css: (width <= 900px)
  - 1100->1120: vis -1; css: (width <= 1100px)
  - 1140->1160 (weak: cols only): cols 8->10

## project-detail

- widths measured: 57 (320-1440); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: none
- offRight > 0 (raw): 320-720
- offRight unclipped roots > 0: none
- first offender (by widths): table.pj-ds[data-testid=project-datasets] [clipped by div.pj-ds-scroll] x21
- smallTargets (touch widths): min 18 @320, max 24 @920
- candidate breaks (7):
  - 380->400 (weak: cols only): cols 3->5
  - 640->660: vis +4, small +2; css: (width <= 640px)
  - 740->760: vis +1; css: (width <= 740px)
  - 880->900: vis +2, cols 7->10; css: (width <= 880px)
  - 900->920: vis +3, inter +1, cols 10->7, small +4; css: (width <= 900px)
  - 1100->1120: vis -1; css: (width <= 1100px)
  - 1240->1260 (weak: cols only): cols 10->12

## project-dialog

- widths measured: 57 (320-1440); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: none
- offRight > 0 (raw): none
- offRight unclipped roots > 0: none
- smallTargets (touch widths): min 3 @320, max 11 @920
- candidate breaks (14):
  - 320->340 (weak: cols only): cols 4->7
  - 380->400 (weak: cols only): cols 6->9
  - 440->460 (weak: cols only): cols 9->11
  - 640->660: vis +4, height 1540->1006, small +4; css: (width <= 640px)
  - 680->700 (weak: cols only): cols 13->11
  - 700->720 (weak: cols only): cols 11->13
  - 740->760: vis +1; css: (width <= 740px)
  - 800->820 (weak: cols only): cols 12->14
  - 880->900: vis +2, cols 14->17; css: (width <= 880px)
  - 900->920: vis +3, inter +1, cols 17->19, small +4; css: (width <= 900px)
  - 920->940 (weak: cols only): cols 19->13
  - 1000->1020: cols 14->16; css: (width <= 1000px)
  - 1180->1200 (input-switch): cols 15->21; css: (pointer: coarse) | (width <= 1180px) | (width <= 640px), (pointer: coarse)
  - 1220->1240 (weak: cols only): cols 21->16

## project-close

- widths measured: 57 (320-1440); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: none
- offRight > 0 (raw): none
- offRight unclipped roots > 0: none
- smallTargets (touch widths): min 3 @320, max 9 @920
- candidate breaks (14):
  - 320->340 (weak: cols only): cols 3->5
  - 380->400 (weak: cols only): cols 5->7
  - 440->460 (weak: cols only): cols 7->10
  - 640->660: vis +4, height 1540->1006, small +2; css: (width <= 640px)
  - 660->680 (weak: cols only): cols 10->12
  - 680->700 (weak: cols only): cols 12->10
  - 740->760: vis +1; css: (width <= 740px)
  - 800->820 (weak: cols only): cols 10->13
  - 880->900: vis +2, cols 12->15; css: (width <= 880px)
  - 900->920: vis +3, inter +1, cols 15->18, small +4; css: (width <= 900px)
  - 920->940 (weak: cols only): cols 18->11
  - 1000->1020: cols 12->14; css: (width <= 1000px)
  - 1180->1200 (input-switch): cols 13->19; css: (pointer: coarse) | (width <= 1180px) | (width <= 640px), (pointer: coarse)
  - 1220->1240 (weak: cols only): cols 19->15

## detail

- widths measured: 57 (320-1440); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: none
- offRight > 0 (raw): 320-1240
- offRight unclipped roots > 0: none
- first offender (by widths): div.lin-axis [clipped by div.lin-graph[data-testid=lin-graph]] x47
- smallTargets (touch widths): min 12 @320, max 18 @920
- candidate breaks (8):
  - 380->400 (weak: cols only): cols 9->13
  - 640->660: vis +4, height 3486->3122, small +2; css: (width <= 640px)
  - 660->680 (weak: cols only): cols 17->19
  - 720->740: cols 18->23; css: (width <= 720px)
  - 740->760: vis +1; css: (width <= 740px)
  - 880->900: vis +2, cols 22->26; css: (width <= 880px)
  - 900->920: vis +3, inter +1, cols 26->21, small +4; css: (width <= 900px)
  - 1420->1440 (weak: cols only): cols 26->24

## settings

- widths measured: 57 (320-1440); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: none
- offRight > 0 (raw): none
- offRight unclipped roots > 0: none
- smallTargets (touch widths): min 4 @320, max 10 @920
- candidate breaks (5):
  - 380->400 (weak: cols only): cols 3->5
  - 640->660: vis +4, cols 5->7, small +2; css: (width <= 640px)
  - 740->760: vis +1; css: (width <= 740px)
  - 880->900: vis +2; css: (width <= 880px)
  - 900->920: vis +3, inter +1, cols 9->6, small +4; css: (width <= 900px)

## members

- widths measured: 57 (320-1440); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: none
- offRight > 0 (raw): 660-680
- offRight unclipped roots > 0: none
- first offender (by widths): table.tbl.memtbl [clipped by div.card-b] x2
- smallTargets (touch widths): min 14 @320, max 20 @920
- candidate breaks (5):
  - 380->400 (weak: cols only): cols 4->6
  - 640->660: vis +12, height 1233->900, small +2; css: (width <= 640px)
  - 740->760: vis +1; css: (width <= 740px)
  - 880->900: vis +2; css: (width <= 880px)
  - 900->920: vis +3, inter +1, cols 10->7, small +4; css: (width <= 900px)

## lab-dialog

- widths measured: 57 (320-1440); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: none
- offRight > 0 (raw): none
- offRight unclipped roots > 0: none
- smallTargets (touch widths): min 9 @320, max 21 @920
- candidate breaks (15):
  - 340->360 (weak: cols only): cols 5->7
  - 380->400 (weak: cols only): cols 7->9
  - 640->660: vis +4, small +8; css: (width <= 640px)
  - 700->720 (weak: cols only): cols 12->16
  - 740->760: vis +1; css: (width <= 740px)
  - 820->840 (weak: cols only): cols 16->18
  - 880->900: vis +2, cols 17->20; css: (width <= 880px)
  - 900->920: vis +3, inter +1, cols 20->12, height 1835->1264, small +4; css: (width <= 900px)
  - 940->960 (weak: cols only): cols 12->14
  - 960->980 (weak: cols only): cols 14->17
  - 1060->1080 (weak: cols only): cols 17->14
  - 1080->1100 (weak: cols only): cols 14->16
  - 1160->1180 (weak: cols only): cols 16->20
  - 1220->1240 (weak: cols only): cols 21->19
  - 1420->1440 (weak: cols only): cols 21->19

## search

- widths measured: 57 (320-1440); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: none
- offRight > 0 (raw): none
- offRight unclipped roots > 0: none
- smallTargets (touch widths): min 6 @320, max 12 @920
- candidate breaks (10):
  - 380->400 (weak: cols only): cols 4->6
  - 640->660: vis +4, small +2; css: (width <= 640px)
  - 740->760: vis +1; css: (width <= 740px)
  - 880->900: vis +2; css: (width <= 880px)
  - 900->920: vis +3, inter +1, cols 9->6, small +4; css: (width <= 900px)
  - 920->940 (weak: cols only): cols 6->8
  - 1020->1040: cols 9->7; css: (width <= 1023px) | (width >= 1024px)
  - 1160->1180 (weak: cols only): cols 7->9
  - 1400->1420 (weak: cols only): cols 7->9
  - 1420->1440 (weak: cols only): cols 9->7

## search-empty

- widths measured: 57 (320-1440); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: none
- offRight > 0 (raw): none
- offRight unclipped roots > 0: none
- smallTargets (touch widths): min 3 @320, max 9 @920
- candidate breaks (5):
  - 380->400 (weak: cols only): cols 5->7
  - 640->660: vis +4, small +2; css: (width <= 640px)
  - 740->760: vis +1; css: (width <= 740px)
  - 880->900: vis +2, cols 7->9; css: (width <= 880px)
  - 900->920: vis +3, inter +1, cols 9->7, small +4; css: (width <= 900px)

## search-down

- widths measured: 57 (320-1440); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: none
- offRight > 0 (raw): none
- offRight unclipped roots > 0: none
- smallTargets (touch widths): min 4 @320, max 10 @920
- candidate breaks (5):
  - 380->400 (weak: cols only): cols 3->5
  - 640->660: vis +4, small +2; css: (width <= 640px)
  - 740->760: vis +1; css: (width <= 740px)
  - 880->900: vis +2; css: (width <= 880px)
  - 900->920: vis +3, inter +1, cols 7->4, small +4; css: (width <= 900px)

## search-degraded

- widths measured: 57 (320-1440); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: none
- offRight > 0 (raw): none
- offRight unclipped roots > 0: none
- smallTargets (touch widths): min 6 @320, max 12 @920
- candidate breaks (10):
  - 380->400 (weak: cols only): cols 5->7
  - 640->660: vis +4, small +2; css: (width <= 640px)
  - 740->760: vis +1; css: (width <= 740px)
  - 880->900: vis +2; css: (width <= 880px)
  - 900->920: vis +3, inter +1, cols 9->6, small +4; css: (width <= 900px)
  - 920->940 (weak: cols only): cols 6->8
  - 1020->1040: cols 9->7; css: (width <= 1023px) | (width >= 1024px)
  - 1160->1180 (weak: cols only): cols 7->9
  - 1400->1420 (weak: cols only): cols 7->9
  - 1420->1440 (weak: cols only): cols 9->7

## preview

- widths measured: 57 (320-1440); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: none
- offRight > 0 (raw): none
- offRight unclipped roots > 0: none
- smallTargets (touch widths): min 3 @320, max 9 @920
- candidate breaks (5):
  - 380->400 (weak: cols only): cols 3->5
  - 640->660: vis +4, cols 5->7, small +2; css: (width <= 640px)
  - 740->760: vis +1; css: (width <= 740px)
  - 880->900: vis +2, cols 8->10; css: (width <= 880px)
  - 900->920: vis +3, inter +1, cols 10->7, small +4; css: (width <= 900px)

## preview-done

- widths measured: 57 (320-1440); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: none
- offRight > 0 (raw): 320-1440
- offRight unclipped roots > 0: none
- first offender (by widths): path.pv-basemap-coast[data-testid=pv-basemap-coastline] [clipped by svg.pv-basemap[data-testid=pv-basemap]] x57
- smallTargets (touch widths): min 3 @320, max 9 @920
- overlayCoverage (map image % covered by overlays; extra measurement for map scenes): >=90%: none; >=50%: none; >=25%: none; overlay/interactive overlaps > 0: none
  - series (width: image% / overlaps): 320: 16.2 / 0, 360: 14.7 / 0, 400: 14.7 / 0, 440: 14.7 / 0, 480: 14.7 / 0, 520: 14.7 / 0, 560: 14.7 / 0, 600: 14.7 / 0, 640: 14.7 / 0, 680: 14.7 / 0, 720: 14.7 / 0, 760: 14.7 / 0, 800: 14.7 / 0, 840: 14.7 / 0, 880: 14.7 / 0, 920: 14.7 / 0, 960: 14.7 / 0, 1000: 14.7 / 0, 1040: 14.7 / 0, 1080: 14.7 / 0, 1120: 14.7 / 0, 1160: 14.7 / 0, 1200: 14.7 / 0, 1240: 14.7 / 0, 1280: 14.7 / 0, 1320: 14.7 / 0, 1360: 14.7 / 0, 1400: 14.7 / 0, 1440: 14.7 / 0
- candidate breaks (5):
  - 380->400 (weak: cols only): cols 5->7
  - 640->660: vis +4, cols 7->9, small +2; css: (width <= 640px)
  - 740->760: vis +1; css: (width <= 740px)
  - 880->900: vis +2, cols 10->12; css: (width <= 880px)
  - 900->920: vis +3, inter +1, cols 12->9, small +4; css: (width <= 900px)

## preview-expired

- widths measured: 57 (320-1440); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: none
- offRight > 0 (raw): none
- offRight unclipped roots > 0: none
- smallTargets (touch widths): min 3 @320, max 9 @920
- candidate breaks (5):
  - 380->400 (weak: cols only): cols 3->5
  - 640->660: vis +4, cols 5->7, small +2; css: (width <= 640px)
  - 740->760: vis +1; css: (width <= 740px)
  - 880->900: vis +2, cols 8->10; css: (width <= 880px)
  - 900->920: vis +3, inter +1, cols 10->7, small +4; css: (width <= 900px)

## access

- widths measured: 57 (320-1440); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: none
- offRight > 0 (raw): none
- offRight unclipped roots > 0: none
- smallTargets (touch widths): min 2 @320, max 8 @920
- candidate breaks (5):
  - 380->400 (weak: cols only): cols 2->4
  - 640->660: vis +4, small +2; css: (width <= 640px)
  - 740->760: vis +1; css: (width <= 740px)
  - 880->900: vis +2; css: (width <= 880px)
  - 900->920: vis +3, inter +1, cols 7->4, small +4; css: (width <= 900px)

## pending

- widths measured: 57 (320-1440); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: none
- offRight > 0 (raw): none
- offRight unclipped roots > 0: none
- smallTargets (touch widths): min 2 @320, max 8 @920
- candidate breaks (5):
  - 380->400 (weak: cols only): cols 2->4
  - 640->660: vis +4, small +2; css: (width <= 640px)
  - 740->760: vis +1; css: (width <= 740px)
  - 880->900: vis +2; css: (width <= 880px)
  - 900->920: vis +3, inter +1, cols 7->4, small +4; css: (width <= 900px)

## approval

- widths measured: 57 (320-1440); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: none
- offRight > 0 (raw): none
- offRight unclipped roots > 0: none
- smallTargets (touch widths): min 2 @320, max 8 @920
- candidate breaks (5):
  - 380->400 (weak: cols only): cols 2->4
  - 640->660: vis +4, small +2; css: (width <= 640px)
  - 740->760: vis +1; css: (width <= 740px)
  - 880->900: vis +2; css: (width <= 880px)
  - 900->920: vis +3, inter +1, cols 7->4, small +4; css: (width <= 900px)

## approval-dialog

- widths measured: 57 (320-1440); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: none
- offRight > 0 (raw): none
- offRight unclipped roots > 0: none
- smallTargets (touch widths): min 2 @320, max 8 @920
- candidate breaks (5):
  - 380->400 (weak: cols only): cols 3->5
  - 640->660: vis +4, small +2; css: (width <= 640px)
  - 740->760: vis +1; css: (width <= 740px)
  - 880->900: vis +2; css: (width <= 880px)
  - 900->920: vis +3, inter +1, cols 9->6, small +4; css: (width <= 900px)

## lineage-picker

- widths measured: 57 (320-1440); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: none
- offRight > 0 (raw): none
- offRight unclipped roots > 0: none
- smallTargets (touch widths): min 8 @320, max 14 @920
- candidate breaks (7):
  - 380->400 (weak: cols only): cols 8->11
  - 640->660: vis +4, small +2; css: (width <= 640px)
  - 740->760: vis +1; css: (width <= 740px)
  - 800->820 (weak: cols only): cols 13->11
  - 880->900: vis +2; css: (width <= 880px)
  - 900->920: vis +3, inter +1, cols 13->10, small +4; css: (width <= 900px)
  - 1040->1060 (weak: cols only): cols 12->10

## login

- widths measured: 57 (320-1440); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: none
- offRight > 0 (raw): none
- offRight unclipped roots > 0: none
- smallTargets (touch widths): min 0 @320, max 1 @660
- candidate breaks (1):
  - 640->660: small +1; css: (width <= 640px)

## not-found

- widths measured: 57 (320-1440); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: none
- offRight > 0 (raw): none
- offRight unclipped roots > 0: none
- smallTargets (touch widths): min 3 @320, max 9 @920
- candidate breaks (5):
  - 380->400 (weak: cols only): cols 2->4
  - 640->660: vis +4, small +2; css: (width <= 640px)
  - 740->760: vis +1; css: (width <= 740px)
  - 880->900: vis +2; css: (width <= 880px)
  - 900->920: vis +3, inter +1, cols 7->4, small +4; css: (width <= 900px)

## upload

- widths measured: 57 (320-1440); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: none
- offRight > 0 (raw): none
- offRight unclipped roots > 0: none
- smallTargets (touch widths): min 0 @320, max 0 @320
- candidate breaks (0):

## upload-classify

- widths measured: 57 (320-1440); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: none
- offRight > 0 (raw): none
- offRight unclipped roots > 0: none
- smallTargets (touch widths): min 5 @320, max 5 @320
- candidate breaks (2):
  - 720->740: vis +1; css: (width <= 720px)
  - 1420->1440 (weak: cols only): cols 10->12

## upload-metadata

- widths measured: 57 (320-1440); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: none
- offRight > 0 (raw): 320-440
- offRight unclipped roots > 0: none
- first offender (by widths): table [clipped by div.vt-box] x7
- smallTargets (touch widths): min 8 @320, max 8 @320
- candidate breaks (11):
  - 540->560 (weak: cols only): cols 8->10
  - 600->620: cols 9->12; css: (width <= 600px)
  - 720->740: vis +1; css: (width <= 720px)
  - 840->860 (weak: cols only): cols 13->15
  - 1020->1040: cols 15->11; css: (width <= 1023px) | (width >= 1024px)
  - 1060->1080 (weak: cols only): cols 11->14
  - 1100->1120: cols 14->16; css: (width <= 1100px)
  - 1200->1220 (weak: cols only): cols 15->17
  - 1280->1300 (weak: cols only): cols 15->19
  - 1300->1320 (weak: cols only): cols 19->17
  - 1360->1380 (weak: cols only): cols 16->18

## upload-link

- widths measured: 57 (320-1440); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: none
- offRight > 0 (raw): none
- offRight unclipped roots > 0: none
- smallTargets (touch widths): min 6 @320, max 7 @660
- candidate breaks (3):
  - 640->660: small +1; css: (width <= 640px)
  - 720->740: vis +1; css: (width <= 720px)
  - 1420->1440 (weak: cols only): cols 11->13

## upload-register-ok

- widths measured: 57 (320-1440); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: none
- offRight > 0 (raw): none
- offRight unclipped roots > 0: none
- smallTargets (touch widths): min 1 @320, max 1 @320
- candidate breaks (1):
  - 740->760: vis +1; css: (width <= 740px)

## account-admin

- widths measured: 57 (320-1440); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: 920  (widened at: 920)
- offRight > 0 (raw): 320-1340
- offRight unclipped roots > 0: 920
- first offender (by widths): table.account-table [clipped by div.account-table-scroll] x52
- smallTargets (touch widths): min 4 @320, max 11 @920
- candidate breaks (6):
  - 380->400 (weak: cols only): cols 8->10
  - 640->660: vis +4, height 1608->1092, small +2; css: (width <= 640px)
  - 740->760: vis +1; css: (width <= 740px)
  - 880->900: vis +2; css: (width <= 880px)
  - 900->920: vis +8, inter +2, cols 15->12, small +5; css: (width <= 900px)
  - 1100->1120: vis -1; css: (width <= 1100px)

## password-change

- widths measured: 57 (320-1440); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: none
- offRight > 0 (raw): none
- offRight unclipped roots > 0: none
- smallTargets (touch widths): min 0 @320, max 0 @320
- candidate breaks (0):

## gnb-more

- widths measured: 27 (320-840); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: none
- offRight > 0 (raw): none
- offRight unclipped roots > 0: none
- smallTargets (touch widths): min 9 @320, max 17 @660
- candidate breaks (5):
  - 340->360 (weak: cols only): cols 5->7
  - 380->400 (weak: cols only): cols 6->10
  - 640->660: vis +4, small +8; css: (width <= 640px)
  - 700->720 (weak: cols only): cols 11->15
  - 740->760: vis +1; css: (width <= 740px)

## primitives

- widths measured: 57 (320-1440); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: 320  (widened at: 320)
- offRight > 0 (raw): 320-920
- offRight unclipped roots > 0: 320
- first offender (by widths): table.tbl [clipped by div.tblwrap] x31
- smallTargets (touch widths): min 0 @320, max 0 @320
- candidate breaks (2):
  - 320->340 (weak: cols only): cols 6->8
  - 1100->1120: vis -1; css: (width <= 1100px)

## dataset-preview-map

- widths measured: 57 (320-1440); non-ok: none
- overflowX > 0 (spec): none
- scrollWidth - device > 0: none
- offRight > 0 (raw): 320-1440
- offRight unclipped roots > 0: none
- first offender (by widths): path.pv-basemap-coast[data-testid=pv-basemap-coastline] [clipped by svg.pv-basemap[data-testid=pv-basemap]] x57
- smallTargets (touch widths): min 1 @320, max 5 @660
- overlayCoverage (map image % covered by overlays; extra measurement for map scenes): >=90%: 320-420; >=50%: 320-540; >=25%: 320-700; overlay/interactive overlaps > 0: 320-500
  - series (width: image% / overlaps): 320: 100 / 13, 360: 100 / 12, 400: 96.9 / 9, 440: 87.2 / 5, 480: 73.7 / 4, 520: 62.3 / 0, 560: 49.6 / 0, 600: 40.7 / 0, 640: 33.1 / 0, 680: 30 / 0, 720: 24.9 / 0, 760: 20.7 / 0, 800: 17.4 / 0, 840: 15 / 0, 880: 12.9 / 0, 920: 11.1 / 0, 960: 9.6 / 0, 1000: 8.3 / 0, 1040: 7.1 / 0, 1080: 6.2 / 0, 1120: 5.4 / 0, 1160: 4.7 / 0, 1200: 4.2 / 0, 1240: 3.8 / 0, 1280: 3.2 / 0, 1320: 3.1 / 0, 1360: 3.1 / 0, 1400: 3.1 / 0, 1440: 3.1 / 0
- candidate breaks (4):
  - 320->340 (weak: cols only): cols 11->9
  - 380->400 (weak: cols only): cols 8->11
  - 580->600 (weak: cols only): cols 10->13
  - 640->660: small +4; css: (width <= 640px)

## Aggregate histogram of break widths (excluding the 1180->1200 input switch)

Boundary `a->b` means the break lies in (a, b]. `scenes` = scenes with a break at that step other than cols-only; `weak` = scenes whose only signal was `cols` (block left edges; e.g. an element growing past the 120 px filter) with no @media flip.

| step | scenes | bar | weak (cols only) | css conditions flipped at this step | scenes |
|---|---|---|---|---|---|
| 320->340 | 0 |  | 6 | - | - |
| 340->360 | 0 |  | 4 | - | - |
| 380->400 | 0 |  | 28 | - | - |
| 440->460 | 0 |  | 3 | - | - |
| 540->560 | 0 |  | 1 | - | - |
| 580->600 | 0 |  | 1 | - | - |
| 600->620 | 1 | # | 0 | (width <= 600px) | upload-metadata |
| 640->660 | 30 | ############################## | 0 | (width <= 640px) | catalog, lab, empty, projects, project-table, project-detail, project-dialog, project-close, detail, settings, members, lab-dialog, search, search-empty, search-down, search-degraded, preview, preview-done, preview-expired, access, pending, approval, approval-dialog, lineage-picker, login, not-found, upload-link, account-admin, gnb-more, dataset-preview-map |
| 660->680 | 0 |  | 2 | - | - |
| 680->700 | 0 |  | 2 | - | - |
| 700->720 | 0 |  | 5 | - | - |
| 720->740 | 4 | #### | 0 | (width <= 720px) | detail, upload-classify, upload-metadata, upload-link |
| 740->760 | 28 | ############################ | 0 | (width <= 740px) | catalog, lab, empty, projects, project-table, project-detail, project-dialog, project-close, detail, settings, members, lab-dialog, search, search-empty, search-down, search-degraded, preview, preview-done, preview-expired, access, pending, approval, approval-dialog, lineage-picker, not-found, upload-register-ok, account-admin, gnb-more |
| 800->820 | 0 |  | 4 | - | - |
| 820->840 | 0 |  | 1 | - | - |
| 840->860 | 0 |  | 1 | - | - |
| 880->900 | 26 | ########################## | 0 | (width <= 880px) | catalog, lab, empty, projects, project-table, project-detail, project-dialog, project-close, detail, settings, members, lab-dialog, search, search-empty, search-down, search-degraded, preview, preview-done, preview-expired, access, pending, approval, approval-dialog, lineage-picker, not-found, account-admin |
| 900->920 | 26 | ########################## | 0 | (width <= 900px) | catalog, lab, empty, projects, project-table, project-detail, project-dialog, project-close, detail, settings, members, lab-dialog, search, search-empty, search-down, search-degraded, preview, preview-done, preview-expired, access, pending, approval, approval-dialog, lineage-picker, not-found, account-admin |
| 920->940 | 0 |  | 5 | - | - |
| 940->960 | 0 |  | 3 | - | - |
| 960->980 | 0 |  | 4 | - | - |
| 1000->1020 | 3 | ### | 0 | (width <= 1000px) | projects, project-dialog, project-close |
| 1020->1040 | 3 | ### | 0 | (width <= 1023px) \| (width >= 1024px) | search, search-degraded, upload-metadata |
| 1040->1060 | 0 |  | 1 | - | - |
| 1060->1080 | 0 |  | 4 | - | - |
| 1080->1100 | 0 |  | 1 | - | - |
| 1100->1120 | 6 | ###### | 0 | (width <= 1100px) | catalog, project-table, project-detail, upload-metadata, account-admin, primitives |
| 1140->1160 | 0 |  | 1 | - | - |
| 1160->1180 | 0 |  | 5 | - | - |
| 1200->1220 | 0 |  | 1 | - | - |
| 1220->1240 | 0 |  | 4 | - | - |
| 1240->1260 | 0 |  | 1 | - | - |
| 1280->1300 | 0 |  | 1 | - | - |
| 1300->1320 | 0 |  | 1 | - | - |
| 1360->1380 | 0 |  | 1 | - | - |
| 1400->1420 | 0 |  | 2 | - | - |
| 1420->1440 | 0 |  | 8 | - | - |

## @media conditions that flipped in the sweep

Conditions whose match changed between consecutive widths in any scene (steps where they flipped). `layout break` = at least one scene had a non-weak break at that step with this flip.

| condition | flipped at | layout break |
|---|---|---|
| `(width <= 1000px)` | 1000->1020 | yes |
| `(width <= 1023px)` | 1020->1040 | yes |
| `(width >= 1024px)` | 1020->1040 | yes |
| `(width <= 1100px)` | 1100->1120 | yes |
| `(pointer: coarse)` | 1180->1200 | no |
| `(width <= 1180px)` | 1180->1200 | no |
| `(width <= 640px), (pointer: coarse)` | 1180->1200 | no |
| `(width <= 520px)` | 520->540 | no |
| `(width <= 560px)` | 560->580 | no |
| `(width <= 600px)` | 600->620 | yes |
| `(width <= 640px)` | 640->660 | yes |
| `(width <= 720px)` | 720->740 | yes |
| `(width <= 740px)` | 740->760 | yes |
| `(width <= 760px)` | 760->780 | no |
| `(width <= 860px)` | 860->880 | no |
| `(width >= 861px)` | 860->880 | no |
| `(width <= 880px)` | 880->900 | yes |
| `(width <= 900px)` | 900->920 | yes |

## Sweep failures

- none

