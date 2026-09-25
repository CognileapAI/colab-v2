# Responsive audit — scene x viewport capture (light theme)

- Generated: 2026-09-25T13:28:22+00:00 (UTC) from recorded metrics only. Repo: worktree `mobile-preview-overlay` at develop f0be4268 (clean; nothing tracked edited).
- Browser: Chrome/152.0.7977.82 (agent-browser Chrome for Testing binary), headless, launched with scenes.json `browser.args` + `--blink-settings=primaryPointerType=4,availablePointerTypes=4,primaryHoverType=2,availableHoverTypes=2`, attached as agent-browser session `resp-audit-d406` (connect) and driven over CDP by `audit.mjs`.
- Touch emulation verified: **True** (details in `touch-verify.json`). Touch viewports: CDP `Emulation.setTouchEmulationEnabled` (maxTouchPoints 5) + `setDeviceMetricsOverride` mobile:true -> hover:none, pointer:coarse, maxTouchPoints 5, `--control-height` 44px. Mouse 1440x900: hover:hover, pointer:fine, maxTouchPoints 0, `--control-height` 40px.
- Captures: 357 scene x viewport (357 ok). Scenes: 36 (35 from scenes.json + `dataset-preview-map`). gnb-more (widths max 768) captured only at viewports <= 844 (7).
- Per scene, as capture.py: storage cleared on a same-origin static asset, URL `entry?theme=light&<query>&upload/labSettings/operator`, prefers-color-scheme light, networkidle (500 ms quiet), `document.fonts.ready`, FREEZE_CSS, actions (click = CDP mouse press/release at element centre after scrollIntoView, landing verified by a capture-phase click listener; 0 fallbacks needed), settleMs, theme/width check. PNG is full-page when the scene has `fullPage: true`, viewport-only otherwise (dialog scenes), as in capture.py.
- `dataset-preview-map`: no audit scene opens the dataset detail preview with a fake source (the `detail` scene passes no `previewSource`, so 보기 would call the real API). Used the scratch harness `harness/` = develop `src` (verified identical to the worktree) + `mobile-measure.tsx` (DatasetPreviewSection, fake HLS B02 source, map-b02.png), page set to light theme, built with vite and served by `vite preview`. Actions: wait 보기 enabled -> click 보기 -> wait img.pv-tile loaded -> wait until image rect/zoom stable (3 x 150 ms) -> settle 1000 ms.

## Column definitions

- **overflowX** = `documentElement.scrollWidth - innerWidth` (spec). At 1440 mouse the classic scrollbar makes it -15 when there is no overflow. **widened**: under mobile emulation an overflowing page widens the layout viewport (innerWidth > device width, visual viewport stays at device width, scale 1), which makes the spec value 0; the device-width overflow is then shown as `scrollWidth-device`.
- **offRight** = visible elements with `rect.right > innerWidth+1`; `(Nu)` = offending root elements not clipped by any overflow container of their own (i.e. cut by the viewport or causing page overflow). Clipped offenders (tables in `overflow:auto` wrappers, basemap paths inside the map SVG) are counted in the raw number. `vs device` = same against the emulated device width when widened.
- **smallTargets** = visible `button, a[href], input, select, textarea, summary, [role=button], [tabindex]:not([tabindex="-1"])` with height<44 or width<44 / all visible such targets (touch viewports only; elements <=1px or opacity 0 excluded).
- **overlaps** = pairs (interactive targets + absolutely/fixed positioned boxes that paint a background or own text + outermost background box inside an absolute/fixed layer) whose visible (ancestor-clipped) rects intersect by >1 px each way and are not ancestor/descendant; full-viewport fixed backdrops excluded; when an `[aria-modal=true]`/`dialog[open]` is open only its contents are compared.
- **truncated** = visible elements with `scrollWidth > clientWidth+1` and overflow-x hidden/clip or text-overflow ellipsis; `+clamp` = -webkit-line-clamp elements with hidden lines.
- **smallInputFont** = text-entry input/select/textarea with computed font-size < 16px / all such fields (iOS focus-zoom risk).
- **overlayCoverage** (only when `.pv-viewport` exists) = % of the visible map image (img.pv-tile or tiles, clipped to the viewport) / of the `.pv-viewport` box covered by overlay boxes (children of `.pv-overlay` corner groups and positioned elements over the map), 2 px grid sampling.
- Also in each metrics JSON: tinyText (text parents <12px), fixedHeightOverflow (vh/dvh-sized elements with rect.bottom > innerHeight), media (hover/pointer/width), top-10 lists with paths.

## Mechanical roll-ups

- overflowX > 0 (spec): none
- scrollWidth - device width > 0: primitives@320
- unclipped offRight roots > 0 (scene@width): primitives@320
- smallInputFont > 0 on touch viewports, scenes per viewport: 844x390 34, 744x1133 34, 820x1180 34, 1024x1366 33, 1180x820 33; touch viewports with none: 320x568, 360x780, 390x844, 507x820
- most frequent sub-16px fields on touch viewports (field: scene x viewport hits): select.theme-switcher (select 13px): 138; select (select 14px): 80; input (text 15px): 18; select#up-pick-file.sel[data-testid=up-pick-file] (select 15px): 15; select.sel[data-testid=up-style-palette] (select 13px): 15; input.inp[data-testid=up-style-classcount] (number 13px): 15; select.login-input (select 13px): 15; input.inp (text 15px): 15
- smallInputFont > 0 on 1440 mouse (no iOS zoom there; listed for contrast): 33 scenes (access, account-admin, approval, approval-dialog, catalog, dataset-preview-map, detail, empty, lab, lab-dialog, lineage-picker, login, members, not-found, password-change, pending, preview, preview-done, preview-expired, primitives, project-close, project-detail, project-dialog, project-table, projects, search, search-degraded, search-down, search-empty, settings, upload-classify, upload-link, upload-metadata)
- overlaps > 0 (scene: number of viewports): dataset-preview-map: 4, gnb-more: 7, project-table: 2, upload-link: 7, upload-metadata: 6
- fixedHeightOverflow inside a fixed/absolute layer (vh-sized box whose bottom is below the viewport): lineage-picker@320x568 ul.lin-cand-list {max-height: 42vh} bottom 699.3 > 568; lineage-picker@844x390 ul.lin-cand-list {max-height: 42vh} bottom 451.4 > 390
- fixedHeightOverflow in normal flow (e.g. page `min-height: 100dvh` taller than the viewport; element: viewports): div.modal.modal--dialog {max-height: calc(100dvh - 32px)}: 9; div.login.account-admin {min-height: 100dvh}: 6; main.login {min-height: 100dvh}: 2
- tinyText > 0 in scenes: none
- smallTargets summed over scenes per touch viewport: 320x568 172 (36 scenes), 360x780 172 (36 scenes), 390x844 172 (36 scenes), 844x390 262 (36 scenes), 507x820 172 (36 scenes), 744x1133 262 (36 scenes), 820x1180 262 (36 scenes), 1024x1366 350 (35 scenes), 1180x820 350 (35 scenes)

## Overlay coverage (scenes with a map viewport)

| scene | viewport | image covered % | viewport covered % | per overlay (% of image) |
|---|---|---|---|---|
| dataset-preview-map | 320x568 | 100 | 84.1 | pv-legend 87.3%, pv-zoom 34.4%, pv-shot 10.9%, pv-hud 9.1%, pv-value 32.9% |
| dataset-preview-map | 360x780 | 100 | 85.1 | pv-legend 91.2%, pv-zoom 25.3%, pv-shot 7.1%, pv-hud 6.3%, pv-value 15.4% |
| dataset-preview-map | 390x844 | 100 | 84 | pv-legend 87%, pv-zoom 20.5%, pv-shot 5.3%, pv-hud 5%, pv-value 12.2% |
| dataset-preview-map | 507x820 | 66.3 | 57.9 | pv-legend 48.6%, pv-zoom 10.3%, pv-shot 1.8%, pv-hud 2.2%, pv-value 3.8% |
| dataset-preview-map | 744x1133 | 22 | 25.5 | pv-legend 18.6%, pv-zoom 2.6%, pv-shot 0%, pv-hud 0.5%, pv-value 0.2% |
| dataset-preview-map | 820x1180 | 16.3 | 20.5 | pv-legend 14%, pv-zoom 2%, pv-shot 0%, pv-hud 0.3%, pv-value 0% |
| dataset-preview-map | 844x390 | 14.9 | 19.2 | pv-legend 12.7%, pv-zoom 1.9%, pv-shot 0%, pv-hud 0.2%, pv-value 0% |
| dataset-preview-map | 1024x1366 | 7.5 | 12.5 | pv-legend 6.7%, pv-zoom 0.8%, pv-shot 0%, pv-hud 0%, pv-value 0% |
| dataset-preview-map | 1180x820 | 4.4 | 9.1 | pv-legend 4.1%, pv-zoom 0.3%, pv-shot 0%, pv-hud 0%, pv-value 0% |
| dataset-preview-map | 1440x900 | 3.1 | 7.7 | pv-legend 3%, pv-zoom 0.1%, pv-shot 0%, pv-hud 0%, pv-value 0% |
| preview-done | 320x568 | 16.2 | 16.2 | pv-legend 10.4%, pv-hud 5.8% |
| preview-done | 360x780 | 14.7 | 14.5 | pv-legend 9.5%, pv-hud 5.3% |
| preview-done | 390x844 | 14.7 | 14.5 | pv-legend 9.5%, pv-hud 5.3% |
| preview-done | 507x820 | 14.7 | 14.5 | pv-legend 9.5%, pv-hud 5.3% |
| preview-done | 744x1133 | 14.7 | 14.5 | pv-legend 9.5%, pv-hud 5.3% |
| preview-done | 820x1180 | 14.7 | 14.5 | pv-legend 9.5%, pv-hud 5.3% |
| preview-done | 844x390 | 14.7 | 14.5 | pv-legend 9.5%, pv-hud 5.3% |
| preview-done | 1024x1366 | 14.7 | 14.5 | pv-legend 9.5%, pv-hud 5.3% |
| preview-done | 1180x820 | 14.7 | 14.5 | pv-legend 9.5%, pv-hud 5.3% |
| preview-done | 1440x900 | 14.7 | 14.5 | pv-legend 9.5%, pv-hud 5.3% |

## Failures

- none: all 357 captures status ok (actions landed, theme light, width matched or widened-by-overflow as recorded).

## Scene x viewport table

| scene | viewport | input | overflowX | offRight (unclipped roots) | smallTargets | overlaps | truncated | smallInputFont | overlayCoverage |
|---|---|---|---|---|---|---|---|---|---|
| catalog | 320x568 | touch | 0 | 137 (0u) | 8/36 | 0 | 0 | 0/5 | - |
| catalog | 360x780 | touch | 0 | 129 (0u) | 8/36 | 0 | 0 | 0/5 | - |
| catalog | 390x844 | touch | 0 | 129 (0u) | 8/36 | 0 | 0 | 0/5 | - |
| catalog | 844x390 | touch | 0 | 84 (0u) | 20/36 | 0 | 1 | 5/5 | - |
| catalog | 507x820 | touch | 0 | 115 (0u) | 8/36 | 0 | 0 | 0/5 | - |
| catalog | 744x1133 | touch | 0 | 98 (0u) | 20/36 | 0 | 1 | 5/5 | - |
| catalog | 820x1180 | touch | 0 | 87 (0u) | 20/36 | 0 | 1 | 5/5 | - |
| catalog | 1024x1366 | touch | 0 | 42 (0u) | 24/37 | 0 | 0 | 5/5 | - |
| catalog | 1180x820 | touch | 0 | 0 (0u) | 24/37 | 0 | 0 | 5/5 | - |
| catalog | 1440x900 | mouse | -15 | 0 (0u) | n/a (mouse) | 0 | 0 | 5/5 | - |
| lab | 320x568 | touch | 0 | 0 (0u) | 9/25 | 0 | 0 | 0/2 | - |
| lab | 360x780 | touch | 0 | 0 (0u) | 9/25 | 0 | 0 | 0/2 | - |
| lab | 390x844 | touch | 0 | 0 (0u) | 9/25 | 0 | 0 | 0/2 | - |
| lab | 844x390 | touch | 0 | 0 (0u) | 17/25 | 0 | 1 | 2/2 | - |
| lab | 507x820 | touch | 0 | 0 (0u) | 9/25 | 0 | 0 | 0/2 | - |
| lab | 744x1133 | touch | 0 | 0 (0u) | 17/25 | 0 | 1 | 2/2 | - |
| lab | 820x1180 | touch | 0 | 0 (0u) | 17/25 | 0 | 1 | 2/2 | - |
| lab | 1024x1366 | touch | 0 | 0 (0u) | 21/26 | 0 | 0 | 2/2 | - |
| lab | 1180x820 | touch | 0 | 0 (0u) | 21/26 | 0 | 0 | 2/2 | - |
| lab | 1440x900 | mouse | -15 | 0 (0u) | n/a (mouse) | 0 | 0 | 2/2 | - |
| empty | 320x568 | touch | 0 | 0 (0u) | 5/14 | 0 | 0 | 0/2 | - |
| empty | 360x780 | touch | 0 | 0 (0u) | 5/14 | 0 | 0 | 0/2 | - |
| empty | 390x844 | touch | 0 | 0 (0u) | 5/14 | 0 | 0 | 0/2 | - |
| empty | 844x390 | touch | 0 | 0 (0u) | 7/14 | 0 | 1 | 2/2 | - |
| empty | 507x820 | touch | 0 | 0 (0u) | 5/14 | 0 | 0 | 0/2 | - |
| empty | 744x1133 | touch | 0 | 0 (0u) | 7/14 | 0 | 1 | 2/2 | - |
| empty | 820x1180 | touch | 0 | 0 (0u) | 7/14 | 0 | 1 | 2/2 | - |
| empty | 1024x1366 | touch | 0 | 0 (0u) | 11/15 | 0 | 0 | 2/2 | - |
| empty | 1180x820 | touch | 0 | 0 (0u) | 11/15 | 0 | 0 | 2/2 | - |
| empty | 1440x900 | mouse | -15 | 0 (0u) | n/a (mouse) | 0 | 0 | 2/2 | - |
| projects | 320x568 | touch | 0 | 0 (0u) | 3/17 | 0 | 0 (+1 clamp) | 0/4 | - |
| projects | 360x780 | touch | 0 | 0 (0u) | 3/17 | 0 | 0 (+1 clamp) | 0/4 | - |
| projects | 390x844 | touch | 0 | 0 (0u) | 3/17 | 0 | 0 (+1 clamp) | 0/4 | - |
| projects | 844x390 | touch | 0 | 0 (0u) | 5/17 | 0 | 1 (+1 clamp) | 4/4 | - |
| projects | 507x820 | touch | 0 | 0 (0u) | 3/17 | 0 | 0 | 0/4 | - |
| projects | 744x1133 | touch | 0 | 0 (0u) | 5/17 | 0 | 1 (+1 clamp) | 4/4 | - |
| projects | 820x1180 | touch | 0 | 0 (0u) | 5/17 | 0 | 1 (+1 clamp) | 4/4 | - |
| projects | 1024x1366 | touch | 0 | 0 (0u) | 9/18 | 0 | 0 (+1 clamp) | 4/4 | - |
| projects | 1180x820 | touch | 0 | 0 (0u) | 9/18 | 0 | 0 (+1 clamp) | 4/4 | - |
| projects | 1440x900 | mouse | 0 | 0 (0u) | n/a (mouse) | 0 | 0 (+1 clamp) | 4/4 | - |
| project-table | 320x568 | touch | 0 | 28 (0u) | 3/14 | 2 | 0 | 0/4 | - |
| project-table | 360x780 | touch | 0 | 28 (0u) | 3/14 | 0 | 0 | 0/4 | - |
| project-table | 390x844 | touch | 0 | 23 (0u) | 3/14 | 0 | 0 | 0/4 | - |
| project-table | 844x390 | touch | 0 | 0 (0u) | 5/14 | 1 | 1 | 4/4 | - |
| project-table | 507x820 | touch | 0 | 23 (0u) | 3/14 | 0 | 0 | 0/4 | - |
| project-table | 744x1133 | touch | 0 | 0 (0u) | 5/14 | 0 | 1 | 4/4 | - |
| project-table | 820x1180 | touch | 0 | 0 (0u) | 5/14 | 0 | 1 | 4/4 | - |
| project-table | 1024x1366 | touch | 0 | 0 (0u) | 9/15 | 0 | 0 | 4/4 | - |
| project-table | 1180x820 | touch | 0 | 0 (0u) | 9/15 | 0 | 0 | 4/4 | - |
| project-table | 1440x900 | mouse | 0 | 0 (0u) | n/a (mouse) | 0 | 0 | 4/4 | - |
| project-detail | 320x568 | touch | 0 | 124 (0u) | 18/24 | 0 | 0 | 0/1 | - |
| project-detail | 360x780 | touch | 0 | 112 (0u) | 18/24 | 0 | 0 | 0/1 | - |
| project-detail | 390x844 | touch | 0 | 99 (0u) | 18/24 | 0 | 0 | 0/1 | - |
| project-detail | 844x390 | touch | 0 | 0 (0u) | 20/24 | 0 | 1 | 1/1 | - |
| project-detail | 507x820 | touch | 0 | 86 (0u) | 18/24 | 0 | 0 | 0/1 | - |
| project-detail | 744x1133 | touch | 0 | 0 (0u) | 20/24 | 0 | 1 | 1/1 | - |
| project-detail | 820x1180 | touch | 0 | 0 (0u) | 20/24 | 0 | 1 | 1/1 | - |
| project-detail | 1024x1366 | touch | 0 | 0 (0u) | 24/25 | 0 | 0 | 1/1 | - |
| project-detail | 1180x820 | touch | 0 | 0 (0u) | 24/25 | 0 | 0 | 1/1 | - |
| project-detail | 1440x900 | mouse | -15 | 0 (0u) | n/a (mouse) | 0 | 0 | 1/1 | - |
| project-dialog | 320x568 | touch | 0 | 0 (0u) | 3/27 | 0 | 0 (+1 clamp) | 0/9 | - |
| project-dialog | 360x780 | touch | 0 | 0 (0u) | 3/27 | 0 | 0 (+1 clamp) | 0/9 | - |
| project-dialog | 390x844 | touch | 0 | 0 (0u) | 3/27 | 0 | 0 (+1 clamp) | 0/9 | - |
| project-dialog | 844x390 | touch | 0 | 0 (0u) | 7/27 | 0 | 1 (+1 clamp) | 9/9 | - |
| project-dialog | 507x820 | touch | 0 | 0 (0u) | 3/27 | 0 | 0 | 0/9 | - |
| project-dialog | 744x1133 | touch | 0 | 0 (0u) | 7/27 | 0 | 1 (+1 clamp) | 9/9 | - |
| project-dialog | 820x1180 | touch | 0 | 0 (0u) | 7/27 | 0 | 1 (+1 clamp) | 9/9 | - |
| project-dialog | 1024x1366 | touch | 0 | 0 (0u) | 11/28 | 0 | 0 (+1 clamp) | 9/9 | - |
| project-dialog | 1180x820 | touch | 0 | 0 (0u) | 11/28 | 0 | 0 (+1 clamp) | 9/9 | - |
| project-dialog | 1440x900 | mouse | 0 | 0 (0u) | n/a (mouse) | 0 | 0 (+1 clamp) | 9/9 | - |
| project-close | 320x568 | touch | 0 | 0 (0u) | 3/20 | 0 | 0 (+1 clamp) | 0/4 | - |
| project-close | 360x780 | touch | 0 | 0 (0u) | 3/20 | 0 | 0 (+1 clamp) | 0/4 | - |
| project-close | 390x844 | touch | 0 | 0 (0u) | 3/20 | 0 | 0 (+1 clamp) | 0/4 | - |
| project-close | 844x390 | touch | 0 | 0 (0u) | 5/20 | 0 | 1 (+1 clamp) | 4/4 | - |
| project-close | 507x820 | touch | 0 | 0 (0u) | 3/20 | 0 | 0 | 0/4 | - |
| project-close | 744x1133 | touch | 0 | 0 (0u) | 5/20 | 0 | 1 (+1 clamp) | 4/4 | - |
| project-close | 820x1180 | touch | 0 | 0 (0u) | 5/20 | 0 | 1 (+1 clamp) | 4/4 | - |
| project-close | 1024x1366 | touch | 0 | 0 (0u) | 9/21 | 0 | 0 (+1 clamp) | 4/4 | - |
| project-close | 1180x820 | touch | 0 | 0 (0u) | 9/21 | 0 | 0 (+1 clamp) | 4/4 | - |
| project-close | 1440x900 | mouse | 0 | 0 (0u) | n/a (mouse) | 0 | 0 (+1 clamp) | 4/4 | - |
| detail | 320x568 | touch | 0 | 40 (0u) | 12/30 | 0 | 1 | 0/4 | - |
| detail | 360x780 | touch | 0 | 39 (0u) | 12/30 | 0 | 1 | 0/4 | - |
| detail | 390x844 | touch | 0 | 36 (0u) | 12/30 | 0 | 1 | 0/4 | - |
| detail | 844x390 | touch | 0 | 15 (0u) | 14/30 | 0 | 2 | 4/4 | - |
| detail | 507x820 | touch | 0 | 24 (0u) | 12/30 | 0 | 1 | 0/4 | - |
| detail | 744x1133 | touch | 0 | 19 (0u) | 14/30 | 0 | 2 | 4/4 | - |
| detail | 820x1180 | touch | 0 | 17 (0u) | 14/30 | 0 | 2 | 4/4 | - |
| detail | 1024x1366 | touch | 0 | 9 (0u) | 18/31 | 0 | 1 | 4/4 | - |
| detail | 1180x820 | touch | 0 | 7 (0u) | 18/31 | 0 | 1 | 4/4 | - |
| detail | 1440x900 | mouse | -15 | 0 (0u) | n/a (mouse) | 0 | 1 | 4/4 | - |
| settings | 320x568 | touch | 0 | 0 (0u) | 4/10 | 0 | 0 | 0/1 | - |
| settings | 360x780 | touch | 0 | 0 (0u) | 4/10 | 0 | 0 | 0/1 | - |
| settings | 390x844 | touch | 0 | 0 (0u) | 4/10 | 0 | 0 | 0/1 | - |
| settings | 844x390 | touch | 0 | 0 (0u) | 6/10 | 0 | 1 | 1/1 | - |
| settings | 507x820 | touch | 0 | 0 (0u) | 4/10 | 0 | 0 | 0/1 | - |
| settings | 744x1133 | touch | 0 | 0 (0u) | 6/10 | 0 | 1 | 1/1 | - |
| settings | 820x1180 | touch | 0 | 0 (0u) | 6/10 | 0 | 1 | 1/1 | - |
| settings | 1024x1366 | touch | 0 | 0 (0u) | 10/11 | 0 | 0 | 1/1 | - |
| settings | 1180x820 | touch | 0 | 0 (0u) | 10/11 | 0 | 0 | 1/1 | - |
| settings | 1440x900 | mouse | 0 | 0 (0u) | n/a (mouse) | 0 | 0 | 1/1 | - |
| members | 320x568 | touch | 0 | 0 (0u) | 14/20 | 0 | 0 | 0/1 | - |
| members | 360x780 | touch | 0 | 0 (0u) | 14/20 | 0 | 0 | 0/1 | - |
| members | 390x844 | touch | 0 | 0 (0u) | 14/20 | 0 | 0 | 0/1 | - |
| members | 844x390 | touch | 0 | 0 (0u) | 16/20 | 0 | 1 | 1/1 | - |
| members | 507x820 | touch | 0 | 0 (0u) | 14/20 | 0 | 0 | 0/1 | - |
| members | 744x1133 | touch | 0 | 0 (0u) | 16/20 | 0 | 1 | 1/1 | - |
| members | 820x1180 | touch | 0 | 0 (0u) | 16/20 | 0 | 1 | 1/1 | - |
| members | 1024x1366 | touch | 0 | 0 (0u) | 20/21 | 0 | 0 | 1/1 | - |
| members | 1180x820 | touch | 0 | 0 (0u) | 20/21 | 0 | 0 | 1/1 | - |
| members | 1440x900 | mouse | 0 | 0 (0u) | n/a (mouse) | 0 | 0 | 1/1 | - |
| lab-dialog | 320x568 | touch | 0 | 0 (0u) | 9/27 | 0 | 0 | 0/2 | - |
| lab-dialog | 360x780 | touch | 0 | 0 (0u) | 9/27 | 0 | 0 | 0/2 | - |
| lab-dialog | 390x844 | touch | 0 | 0 (0u) | 9/27 | 0 | 0 | 0/2 | - |
| lab-dialog | 844x390 | touch | 0 | 0 (0u) | 17/27 | 0 | 1 | 2/2 | - |
| lab-dialog | 507x820 | touch | 0 | 0 (0u) | 9/27 | 0 | 0 | 0/2 | - |
| lab-dialog | 744x1133 | touch | 0 | 0 (0u) | 17/27 | 0 | 1 | 2/2 | - |
| lab-dialog | 820x1180 | touch | 0 | 0 (0u) | 17/27 | 0 | 1 | 2/2 | - |
| lab-dialog | 1024x1366 | touch | 0 | 0 (0u) | 21/28 | 0 | 0 | 2/2 | - |
| lab-dialog | 1180x820 | touch | 0 | 0 (0u) | 21/28 | 0 | 0 | 2/2 | - |
| lab-dialog | 1440x900 | mouse | -15 | 0 (0u) | n/a (mouse) | 0 | 0 | 2/2 | - |
| search | 320x568 | touch | 0 | 0 (0u) | 6/12 | 0 | 0 | 0/1 | - |
| search | 360x780 | touch | 0 | 0 (0u) | 6/12 | 0 | 0 | 0/1 | - |
| search | 390x844 | touch | 0 | 0 (0u) | 6/12 | 0 | 0 | 0/1 | - |
| search | 844x390 | touch | 0 | 0 (0u) | 8/12 | 0 | 1 | 1/1 | - |
| search | 507x820 | touch | 0 | 0 (0u) | 6/12 | 0 | 0 | 0/1 | - |
| search | 744x1133 | touch | 0 | 0 (0u) | 8/12 | 0 | 1 | 1/1 | - |
| search | 820x1180 | touch | 0 | 0 (0u) | 8/12 | 0 | 1 | 1/1 | - |
| search | 1024x1366 | touch | 0 | 0 (0u) | 12/13 | 0 | 0 | 1/1 | - |
| search | 1180x820 | touch | 0 | 0 (0u) | 12/13 | 0 | 0 | 1/1 | - |
| search | 1440x900 | mouse | -15 | 0 (0u) | n/a (mouse) | 0 | 0 | 1/1 | - |
| search-empty | 320x568 | touch | 0 | 0 (0u) | 3/10 | 0 | 0 | 0/1 | - |
| search-empty | 360x780 | touch | 0 | 0 (0u) | 3/10 | 0 | 0 | 0/1 | - |
| search-empty | 390x844 | touch | 0 | 0 (0u) | 3/10 | 0 | 0 | 0/1 | - |
| search-empty | 844x390 | touch | 0 | 0 (0u) | 5/10 | 0 | 1 | 1/1 | - |
| search-empty | 507x820 | touch | 0 | 0 (0u) | 3/10 | 0 | 0 | 0/1 | - |
| search-empty | 744x1133 | touch | 0 | 0 (0u) | 5/10 | 0 | 1 | 1/1 | - |
| search-empty | 820x1180 | touch | 0 | 0 (0u) | 5/10 | 0 | 1 | 1/1 | - |
| search-empty | 1024x1366 | touch | 0 | 0 (0u) | 9/11 | 0 | 0 | 1/1 | - |
| search-empty | 1180x820 | touch | 0 | 0 (0u) | 9/11 | 0 | 0 | 1/1 | - |
| search-empty | 1440x900 | mouse | 0 | 0 (0u) | n/a (mouse) | 0 | 0 | 1/1 | - |
| search-down | 320x568 | touch | 0 | 0 (0u) | 4/9 | 0 | 0 | 0/1 | - |
| search-down | 360x780 | touch | 0 | 0 (0u) | 4/9 | 0 | 0 | 0/1 | - |
| search-down | 390x844 | touch | 0 | 0 (0u) | 4/9 | 0 | 0 | 0/1 | - |
| search-down | 844x390 | touch | 0 | 0 (0u) | 6/9 | 0 | 1 | 1/1 | - |
| search-down | 507x820 | touch | 0 | 0 (0u) | 4/9 | 0 | 0 | 0/1 | - |
| search-down | 744x1133 | touch | 0 | 0 (0u) | 6/9 | 0 | 1 | 1/1 | - |
| search-down | 820x1180 | touch | 0 | 0 (0u) | 6/9 | 0 | 1 | 1/1 | - |
| search-down | 1024x1366 | touch | 0 | 0 (0u) | 10/10 | 0 | 0 | 1/1 | - |
| search-down | 1180x820 | touch | 0 | 0 (0u) | 10/10 | 0 | 0 | 1/1 | - |
| search-down | 1440x900 | mouse | 0 | 0 (0u) | n/a (mouse) | 0 | 0 | 1/1 | - |
| search-degraded | 320x568 | touch | 0 | 0 (0u) | 6/12 | 0 | 0 | 0/1 | - |
| search-degraded | 360x780 | touch | 0 | 0 (0u) | 6/12 | 0 | 0 | 0/1 | - |
| search-degraded | 390x844 | touch | 0 | 0 (0u) | 6/12 | 0 | 0 | 0/1 | - |
| search-degraded | 844x390 | touch | 0 | 0 (0u) | 8/12 | 0 | 1 | 1/1 | - |
| search-degraded | 507x820 | touch | 0 | 0 (0u) | 6/12 | 0 | 0 | 0/1 | - |
| search-degraded | 744x1133 | touch | 0 | 0 (0u) | 8/12 | 0 | 1 | 1/1 | - |
| search-degraded | 820x1180 | touch | 0 | 0 (0u) | 8/12 | 0 | 1 | 1/1 | - |
| search-degraded | 1024x1366 | touch | 0 | 0 (0u) | 12/13 | 0 | 0 | 1/1 | - |
| search-degraded | 1180x820 | touch | 0 | 0 (0u) | 12/13 | 0 | 0 | 1/1 | - |
| search-degraded | 1440x900 | mouse | -15 | 0 (0u) | n/a (mouse) | 0 | 0 | 1/1 | - |
| preview | 320x568 | touch | 0 | 0 (0u) | 3/9 | 0 | 0 | 0/1 | - |
| preview | 360x780 | touch | 0 | 0 (0u) | 3/9 | 0 | 0 | 0/1 | - |
| preview | 390x844 | touch | 0 | 0 (0u) | 3/9 | 0 | 0 | 0/1 | - |
| preview | 844x390 | touch | 0 | 0 (0u) | 5/9 | 0 | 1 | 1/1 | - |
| preview | 507x820 | touch | 0 | 0 (0u) | 3/9 | 0 | 0 | 0/1 | - |
| preview | 744x1133 | touch | 0 | 0 (0u) | 5/9 | 0 | 1 | 1/1 | - |
| preview | 820x1180 | touch | 0 | 0 (0u) | 5/9 | 0 | 1 | 1/1 | - |
| preview | 1024x1366 | touch | 0 | 0 (0u) | 9/10 | 0 | 0 | 1/1 | - |
| preview | 1180x820 | touch | 0 | 0 (0u) | 9/10 | 0 | 0 | 1/1 | - |
| preview | 1440x900 | mouse | 0 | 0 (0u) | n/a (mouse) | 0 | 0 | 1/1 | - |
| preview-done | 320x568 | touch | 0 | 2 (0u) | 3/10 | 0 | 0 | 0/2 | img 16.2% / vp 16.2% |
| preview-done | 360x780 | touch | 0 | 2 (0u) | 3/10 | 0 | 0 | 0/2 | img 14.7% / vp 14.5% |
| preview-done | 390x844 | touch | 0 | 2 (0u) | 3/10 | 0 | 0 | 0/2 | img 14.7% / vp 14.5% |
| preview-done | 844x390 | touch | 0 | 2 (0u) | 5/10 | 0 | 1 | 2/2 | img 14.7% / vp 14.5% |
| preview-done | 507x820 | touch | 0 | 2 (0u) | 3/10 | 0 | 0 | 0/2 | img 14.7% / vp 14.5% |
| preview-done | 744x1133 | touch | 0 | 2 (0u) | 5/10 | 0 | 1 | 2/2 | img 14.7% / vp 14.5% |
| preview-done | 820x1180 | touch | 0 | 2 (0u) | 5/10 | 0 | 1 | 2/2 | img 14.7% / vp 14.5% |
| preview-done | 1024x1366 | touch | 0 | 2 (0u) | 9/11 | 0 | 0 | 2/2 | img 14.7% / vp 14.5% |
| preview-done | 1180x820 | touch | 0 | 2 (0u) | 9/11 | 0 | 0 | 2/2 | img 14.7% / vp 14.5% |
| preview-done | 1440x900 | mouse | -15 | 2 (0u) | n/a (mouse) | 0 | 0 | 2/2 | img 14.7% / vp 14.5% |
| preview-expired | 320x568 | touch | 0 | 0 (0u) | 3/9 | 0 | 0 | 0/1 | - |
| preview-expired | 360x780 | touch | 0 | 0 (0u) | 3/9 | 0 | 0 | 0/1 | - |
| preview-expired | 390x844 | touch | 0 | 0 (0u) | 3/9 | 0 | 0 | 0/1 | - |
| preview-expired | 844x390 | touch | 0 | 0 (0u) | 5/9 | 0 | 1 | 1/1 | - |
| preview-expired | 507x820 | touch | 0 | 0 (0u) | 3/9 | 0 | 0 | 0/1 | - |
| preview-expired | 744x1133 | touch | 0 | 0 (0u) | 5/9 | 0 | 1 | 1/1 | - |
| preview-expired | 820x1180 | touch | 0 | 0 (0u) | 5/9 | 0 | 1 | 1/1 | - |
| preview-expired | 1024x1366 | touch | 0 | 0 (0u) | 9/10 | 0 | 0 | 1/1 | - |
| preview-expired | 1180x820 | touch | 0 | 0 (0u) | 9/10 | 0 | 0 | 1/1 | - |
| preview-expired | 1440x900 | mouse | 0 | 0 (0u) | n/a (mouse) | 0 | 0 | 1/1 | - |
| access | 320x568 | touch | 0 | 0 (0u) | 2/8 | 0 | 0 | 0/1 | - |
| access | 360x780 | touch | 0 | 0 (0u) | 2/8 | 0 | 0 | 0/1 | - |
| access | 390x844 | touch | 0 | 0 (0u) | 2/8 | 0 | 0 | 0/1 | - |
| access | 844x390 | touch | 0 | 0 (0u) | 4/8 | 0 | 1 | 1/1 | - |
| access | 507x820 | touch | 0 | 0 (0u) | 2/8 | 0 | 0 | 0/1 | - |
| access | 744x1133 | touch | 0 | 0 (0u) | 4/8 | 0 | 1 | 1/1 | - |
| access | 820x1180 | touch | 0 | 0 (0u) | 4/8 | 0 | 1 | 1/1 | - |
| access | 1024x1366 | touch | 0 | 0 (0u) | 8/9 | 0 | 0 | 1/1 | - |
| access | 1180x820 | touch | 0 | 0 (0u) | 8/9 | 0 | 0 | 1/1 | - |
| access | 1440x900 | mouse | 0 | 0 (0u) | n/a (mouse) | 0 | 0 | 1/1 | - |
| pending | 320x568 | touch | 0 | 0 (0u) | 2/7 | 0 | 0 | 0/1 | - |
| pending | 360x780 | touch | 0 | 0 (0u) | 2/7 | 0 | 0 | 0/1 | - |
| pending | 390x844 | touch | 0 | 0 (0u) | 2/7 | 0 | 0 | 0/1 | - |
| pending | 844x390 | touch | 0 | 0 (0u) | 4/7 | 0 | 1 | 1/1 | - |
| pending | 507x820 | touch | 0 | 0 (0u) | 2/7 | 0 | 0 | 0/1 | - |
| pending | 744x1133 | touch | 0 | 0 (0u) | 4/7 | 0 | 1 | 1/1 | - |
| pending | 820x1180 | touch | 0 | 0 (0u) | 4/7 | 0 | 1 | 1/1 | - |
| pending | 1024x1366 | touch | 0 | 0 (0u) | 8/8 | 0 | 0 | 1/1 | - |
| pending | 1180x820 | touch | 0 | 0 (0u) | 8/8 | 0 | 0 | 1/1 | - |
| pending | 1440x900 | mouse | 0 | 0 (0u) | n/a (mouse) | 0 | 0 | 1/1 | - |
| approval | 320x568 | touch | 0 | 0 (0u) | 2/8 | 0 | 0 | 0/1 | - |
| approval | 360x780 | touch | 0 | 0 (0u) | 2/8 | 0 | 0 | 0/1 | - |
| approval | 390x844 | touch | 0 | 0 (0u) | 2/8 | 0 | 0 | 0/1 | - |
| approval | 844x390 | touch | 0 | 0 (0u) | 4/8 | 0 | 1 | 1/1 | - |
| approval | 507x820 | touch | 0 | 0 (0u) | 2/8 | 0 | 0 | 0/1 | - |
| approval | 744x1133 | touch | 0 | 0 (0u) | 4/8 | 0 | 1 | 1/1 | - |
| approval | 820x1180 | touch | 0 | 0 (0u) | 4/8 | 0 | 1 | 1/1 | - |
| approval | 1024x1366 | touch | 0 | 0 (0u) | 8/9 | 0 | 0 | 1/1 | - |
| approval | 1180x820 | touch | 0 | 0 (0u) | 8/9 | 0 | 0 | 1/1 | - |
| approval | 1440x900 | mouse | 0 | 0 (0u) | n/a (mouse) | 0 | 0 | 1/1 | - |
| approval-dialog | 320x568 | touch | 0 | 0 (0u) | 2/11 | 0 | 0 | 0/2 | - |
| approval-dialog | 360x780 | touch | 0 | 0 (0u) | 2/11 | 0 | 0 | 0/2 | - |
| approval-dialog | 390x844 | touch | 0 | 0 (0u) | 2/11 | 0 | 0 | 0/2 | - |
| approval-dialog | 844x390 | touch | 0 | 0 (0u) | 4/11 | 0 | 1 | 1/2 | - |
| approval-dialog | 507x820 | touch | 0 | 0 (0u) | 2/11 | 0 | 0 | 0/2 | - |
| approval-dialog | 744x1133 | touch | 0 | 0 (0u) | 4/11 | 0 | 1 | 1/2 | - |
| approval-dialog | 820x1180 | touch | 0 | 0 (0u) | 4/11 | 0 | 1 | 1/2 | - |
| approval-dialog | 1024x1366 | touch | 0 | 0 (0u) | 8/12 | 0 | 0 | 1/2 | - |
| approval-dialog | 1180x820 | touch | 0 | 0 (0u) | 8/12 | 0 | 0 | 1/2 | - |
| approval-dialog | 1440x900 | mouse | 0 | 0 (0u) | n/a (mouse) | 0 | 0 | 1/2 | - |
| lineage-picker | 320x568 | touch | 0 | 0 (0u) | 8/20 | 0 | 0 | 0/5 | - |
| lineage-picker | 360x780 | touch | 0 | 0 (0u) | 8/20 | 0 | 0 | 0/5 | - |
| lineage-picker | 390x844 | touch | 0 | 0 (0u) | 8/20 | 0 | 0 | 0/5 | - |
| lineage-picker | 844x390 | touch | 0 | 0 (0u) | 10/20 | 0 | 1 | 5/5 | - |
| lineage-picker | 507x820 | touch | 0 | 0 (0u) | 8/20 | 0 | 0 | 0/5 | - |
| lineage-picker | 744x1133 | touch | 0 | 0 (0u) | 10/20 | 0 | 1 | 5/5 | - |
| lineage-picker | 820x1180 | touch | 0 | 0 (0u) | 10/20 | 0 | 1 | 5/5 | - |
| lineage-picker | 1024x1366 | touch | 0 | 0 (0u) | 14/21 | 0 | 0 | 5/5 | - |
| lineage-picker | 1180x820 | touch | 0 | 0 (0u) | 14/21 | 0 | 0 | 5/5 | - |
| lineage-picker | 1440x900 | mouse | 0 | 0 (0u) | n/a (mouse) | 0 | 0 | 5/5 | - |
| login | 320x568 | touch | 0 | 0 (0u) | 0/4 | 0 | 0 | 0/3 | - |
| login | 360x780 | touch | 0 | 0 (0u) | 0/4 | 0 | 0 | 0/3 | - |
| login | 390x844 | touch | 0 | 0 (0u) | 0/4 | 0 | 0 | 0/3 | - |
| login | 844x390 | touch | 0 | 0 (0u) | 1/4 | 0 | 0 | 3/3 | - |
| login | 507x820 | touch | 0 | 0 (0u) | 0/4 | 0 | 0 | 0/3 | - |
| login | 744x1133 | touch | 0 | 0 (0u) | 1/4 | 0 | 0 | 3/3 | - |
| login | 820x1180 | touch | 0 | 0 (0u) | 1/4 | 0 | 0 | 3/3 | - |
| login | 1024x1366 | touch | 0 | 0 (0u) | 1/4 | 0 | 0 | 3/3 | - |
| login | 1180x820 | touch | 0 | 0 (0u) | 1/4 | 0 | 0 | 3/3 | - |
| login | 1440x900 | mouse | 0 | 0 (0u) | n/a (mouse) | 0 | 0 | 3/3 | - |
| not-found | 320x568 | touch | 0 | 0 (0u) | 3/8 | 0 | 0 | 0/1 | - |
| not-found | 360x780 | touch | 0 | 0 (0u) | 3/8 | 0 | 0 | 0/1 | - |
| not-found | 390x844 | touch | 0 | 0 (0u) | 3/8 | 0 | 0 | 0/1 | - |
| not-found | 844x390 | touch | 0 | 0 (0u) | 5/8 | 0 | 1 | 1/1 | - |
| not-found | 507x820 | touch | 0 | 0 (0u) | 3/8 | 0 | 0 | 0/1 | - |
| not-found | 744x1133 | touch | 0 | 0 (0u) | 5/8 | 0 | 1 | 1/1 | - |
| not-found | 820x1180 | touch | 0 | 0 (0u) | 5/8 | 0 | 1 | 1/1 | - |
| not-found | 1024x1366 | touch | 0 | 0 (0u) | 9/9 | 0 | 0 | 1/1 | - |
| not-found | 1180x820 | touch | 0 | 0 (0u) | 9/9 | 0 | 0 | 1/1 | - |
| not-found | 1440x900 | mouse | 0 | 0 (0u) | n/a (mouse) | 0 | 0 | 1/1 | - |
| upload | 320x568 | touch | 0 | 0 (0u) | 0/1 | 0 | 0 | 0/0 | - |
| upload | 360x780 | touch | 0 | 0 (0u) | 0/1 | 0 | 0 | 0/0 | - |
| upload | 390x844 | touch | 0 | 0 (0u) | 0/1 | 0 | 0 | 0/0 | - |
| upload | 844x390 | touch | 0 | 0 (0u) | 0/1 | 0 | 0 | 0/0 | - |
| upload | 507x820 | touch | 0 | 0 (0u) | 0/1 | 0 | 0 | 0/0 | - |
| upload | 744x1133 | touch | 0 | 0 (0u) | 0/1 | 0 | 0 | 0/0 | - |
| upload | 820x1180 | touch | 0 | 0 (0u) | 0/1 | 0 | 0 | 0/0 | - |
| upload | 1024x1366 | touch | 0 | 0 (0u) | 0/1 | 0 | 0 | 0/0 | - |
| upload | 1180x820 | touch | 0 | 0 (0u) | 0/1 | 0 | 0 | 0/0 | - |
| upload | 1440x900 | mouse | 0 | 0 (0u) | n/a (mouse) | 0 | 0 | 0/0 | - |
| upload-classify | 320x568 | touch | 0 | 0 (0u) | 5/19 | 0 | 0 | 0/6 | - |
| upload-classify | 360x780 | touch | 0 | 0 (0u) | 5/19 | 0 | 0 | 0/6 | - |
| upload-classify | 390x844 | touch | 0 | 0 (0u) | 5/19 | 0 | 0 | 0/6 | - |
| upload-classify | 844x390 | touch | 0 | 0 (0u) | 5/19 | 0 | 0 | 6/6 | - |
| upload-classify | 507x820 | touch | 0 | 0 (0u) | 5/19 | 0 | 0 | 0/6 | - |
| upload-classify | 744x1133 | touch | 0 | 0 (0u) | 5/19 | 0 | 0 | 6/6 | - |
| upload-classify | 820x1180 | touch | 0 | 0 (0u) | 5/19 | 0 | 0 | 6/6 | - |
| upload-classify | 1024x1366 | touch | 0 | 0 (0u) | 5/19 | 0 | 0 | 6/6 | - |
| upload-classify | 1180x820 | touch | 0 | 0 (0u) | 5/19 | 0 | 0 | 6/6 | - |
| upload-classify | 1440x900 | mouse | 0 | 0 (0u) | n/a (mouse) | 0 | 0 | 6/6 | - |
| upload-metadata | 320x568 | touch | 0 | 20 (0u) | 8/34 | 4 | 3 | 0/16 | - |
| upload-metadata | 360x780 | touch | 0 | 20 (0u) | 8/34 | 1 | 2 | 0/16 | - |
| upload-metadata | 390x844 | touch | 0 | 14 (0u) | 8/34 | 0 | 1 | 0/16 | - |
| upload-metadata | 844x390 | touch | 0 | 0 (0u) | 8/34 | 4 | 0 | 16/16 | - |
| upload-metadata | 507x820 | touch | 0 | 0 (0u) | 8/34 | 0 | 0 | 0/16 | - |
| upload-metadata | 744x1133 | touch | 0 | 0 (0u) | 8/34 | 4 | 0 | 16/16 | - |
| upload-metadata | 820x1180 | touch | 0 | 0 (0u) | 8/34 | 4 | 0 | 16/16 | - |
| upload-metadata | 1024x1366 | touch | 0 | 0 (0u) | 8/34 | 0 | 0 | 16/16 | - |
| upload-metadata | 1180x820 | touch | 0 | 0 (0u) | 8/34 | 3 | 0 | 16/16 | - |
| upload-metadata | 1440x900 | mouse | 0 | 0 (0u) | n/a (mouse) | 0 | 0 | 16/16 | - |
| upload-link | 320x568 | touch | 0 | 0 (0u) | 6/24 | 4 | 0 | 0/6 | - |
| upload-link | 360x780 | touch | 0 | 0 (0u) | 6/24 | 1 | 0 | 0/6 | - |
| upload-link | 390x844 | touch | 0 | 0 (0u) | 6/24 | 2 | 0 | 0/6 | - |
| upload-link | 844x390 | touch | 0 | 0 (0u) | 7/24 | 4 | 0 | 6/6 | - |
| upload-link | 507x820 | touch | 0 | 0 (0u) | 6/24 | 2 | 0 | 0/6 | - |
| upload-link | 744x1133 | touch | 0 | 0 (0u) | 7/24 | 0 | 0 | 6/6 | - |
| upload-link | 820x1180 | touch | 0 | 0 (0u) | 7/24 | 0 | 0 | 6/6 | - |
| upload-link | 1024x1366 | touch | 0 | 0 (0u) | 7/24 | 0 | 0 | 6/6 | - |
| upload-link | 1180x820 | touch | 0 | 0 (0u) | 7/24 | 2 | 0 | 6/6 | - |
| upload-link | 1440x900 | mouse | 0 | 0 (0u) | n/a (mouse) | 5 | 0 | 6/6 | - |
| upload-register-ok | 320x568 | touch | 0 | 0 (0u) | 1/3 | 0 | 0 | 0/0 | - |
| upload-register-ok | 360x780 | touch | 0 | 0 (0u) | 1/3 | 0 | 0 | 0/0 | - |
| upload-register-ok | 390x844 | touch | 0 | 0 (0u) | 1/3 | 0 | 0 | 0/0 | - |
| upload-register-ok | 844x390 | touch | 0 | 0 (0u) | 1/3 | 0 | 0 | 0/0 | - |
| upload-register-ok | 507x820 | touch | 0 | 0 (0u) | 1/3 | 0 | 0 | 0/0 | - |
| upload-register-ok | 744x1133 | touch | 0 | 0 (0u) | 1/3 | 0 | 0 | 0/0 | - |
| upload-register-ok | 820x1180 | touch | 0 | 0 (0u) | 1/3 | 0 | 0 | 0/0 | - |
| upload-register-ok | 1024x1366 | touch | 0 | 0 (0u) | 1/3 | 0 | 0 | 0/0 | - |
| upload-register-ok | 1180x820 | touch | 0 | 0 (0u) | 1/3 | 0 | 0 | 0/0 | - |
| upload-register-ok | 1440x900 | mouse | 0 | 0 (0u) | n/a (mouse) | 0 | 0 | 0/0 | - |
| account-admin | 320x568 | touch | 0 | 77 (0u) | 4/29 | 0 | 5 | 0/5 | - |
| account-admin | 360x780 | touch | 0 | 77 (0u) | 4/29 | 0 | 5 | 0/5 | - |
| account-admin | 390x844 | touch | 0 | 77 (0u) | 4/29 | 0 | 5 | 0/5 | - |
| account-admin | 844x390 | touch | 0 | 35 (0u) | 6/29 | 0 | 6 | 5/5 | - |
| account-admin | 507x820 | touch | 0 | 77 (0u) | 4/29 | 0 | 5 | 0/5 | - |
| account-admin | 744x1133 | touch | 0 | 41 (0u) | 6/29 | 0 | 6 | 5/5 | - |
| account-admin | 820x1180 | touch | 0 | 35 (0u) | 6/29 | 0 | 6 | 5/5 | - |
| account-admin | 1024x1366 | touch | 0 | 9 (0u) | 11/31 | 0 | 6 | 5/5 | - |
| account-admin | 1180x820 | touch | 0 | 9 (0u) | 11/31 | 0 | 6 | 5/5 | - |
| account-admin | 1440x900 | mouse | 0 | 0 (0u) | n/a (mouse) | 0 | 6 | 5/5 | - |
| password-change | 320x568 | touch | 0 | 0 (0u) | 0/3 | 0 | 0 | 0/2 | - |
| password-change | 360x780 | touch | 0 | 0 (0u) | 0/3 | 0 | 0 | 0/2 | - |
| password-change | 390x844 | touch | 0 | 0 (0u) | 0/3 | 0 | 0 | 0/2 | - |
| password-change | 844x390 | touch | 0 | 0 (0u) | 0/3 | 0 | 0 | 2/2 | - |
| password-change | 507x820 | touch | 0 | 0 (0u) | 0/3 | 0 | 0 | 0/2 | - |
| password-change | 744x1133 | touch | 0 | 0 (0u) | 0/3 | 0 | 0 | 2/2 | - |
| password-change | 820x1180 | touch | 0 | 0 (0u) | 0/3 | 0 | 0 | 2/2 | - |
| password-change | 1024x1366 | touch | 0 | 0 (0u) | 0/3 | 0 | 0 | 2/2 | - |
| password-change | 1180x820 | touch | 0 | 0 (0u) | 0/3 | 0 | 0 | 2/2 | - |
| password-change | 1440x900 | mouse | 0 | 0 (0u) | n/a (mouse) | 0 | 0 | 2/2 | - |
| gnb-more | 320x568 | touch | 0 | 0 (0u) | 9/27 | 4 | 0 | 0/2 | - |
| gnb-more | 360x780 | touch | 0 | 0 (0u) | 9/27 | 4 | 0 | 0/2 | - |
| gnb-more | 390x844 | touch | 0 | 0 (0u) | 9/27 | 4 | 0 | 0/2 | - |
| gnb-more | 844x390 | touch | 0 | 0 (0u) | 17/27 | 4 | 1 | 2/2 | - |
| gnb-more | 507x820 | touch | 0 | 0 (0u) | 9/27 | 5 | 0 | 0/2 | - |
| gnb-more | 744x1133 | touch | 0 | 0 (0u) | 17/27 | 4 | 1 | 2/2 | - |
| gnb-more | 820x1180 | touch | 0 | 0 (0u) | 17/27 | 4 | 1 | 2/2 | - |
| primitives | 320x568 | touch | 0 (widened: innerWidth 332; scrollWidth-device +12) | 19 (0u); vs device 22 (3u) | 0/19 | 0 | 0 | 0/5 | - |
| primitives | 360x780 | touch | 0 | 19 (0u) | 0/19 | 0 | 0 | 0/5 | - |
| primitives | 390x844 | touch | 0 | 19 (0u) | 0/19 | 0 | 0 | 0/5 | - |
| primitives | 844x390 | touch | 0 | 11 (0u) | 0/19 | 0 | 0 | 5/5 | - |
| primitives | 507x820 | touch | 0 | 15 (0u) | 0/19 | 0 | 0 | 0/5 | - |
| primitives | 744x1133 | touch | 0 | 11 (0u) | 0/19 | 0 | 0 | 5/5 | - |
| primitives | 820x1180 | touch | 0 | 11 (0u) | 0/19 | 0 | 0 | 5/5 | - |
| primitives | 1024x1366 | touch | 0 | 0 (0u) | 0/19 | 0 | 0 | 5/5 | - |
| primitives | 1180x820 | touch | 0 | 0 (0u) | 0/19 | 0 | 0 | 5/5 | - |
| primitives | 1440x900 | mouse | -15 | 0 (0u) | n/a (mouse) | 0 | 0 | 5/5 | - |
| dataset-preview-map | 320x568 | touch | 0 | 2 (0u) | 1/11 | 13 | 0 | 0/5 | img 100% / vp 84.1% |
| dataset-preview-map | 360x780 | touch | 0 | 2 (0u) | 1/11 | 12 | 0 | 0/5 | img 100% / vp 85.1% |
| dataset-preview-map | 390x844 | touch | 0 | 2 (0u) | 1/11 | 9 | 0 | 0/5 | img 100% / vp 84% |
| dataset-preview-map | 844x390 | touch | 0 | 2 (0u) | 5/11 | 0 | 0 | 5/5 | img 14.9% / vp 19.2% |
| dataset-preview-map | 507x820 | touch | 0 | 2 (0u) | 1/11 | 1 | 0 | 0/5 | img 66.3% / vp 57.9% |
| dataset-preview-map | 744x1133 | touch | 0 | 2 (0u) | 5/11 | 0 | 0 | 5/5 | img 22% / vp 25.5% |
| dataset-preview-map | 820x1180 | touch | 0 | 2 (0u) | 5/11 | 0 | 0 | 5/5 | img 16.3% / vp 20.5% |
| dataset-preview-map | 1024x1366 | touch | 0 | 2 (0u) | 5/11 | 0 | 0 | 5/5 | img 7.5% / vp 12.5% |
| dataset-preview-map | 1180x820 | touch | 0 | 2 (0u) | 5/11 | 0 | 0 | 5/5 | img 4.4% / vp 9.1% |
| dataset-preview-map | 1440x900 | mouse | -15 | 2 (0u) | n/a (mouse) | 0 | 0 | 5/5 | img 3.1% / vp 7.7% |

