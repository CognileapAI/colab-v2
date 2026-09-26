/**
 * 휴대폰·패드 대응 20260926 L0b — 캡처 수치 · 판정 · 새 장면을 잠근다.
 *
 * 오라클 = `dev-package/prd/specs/S-DEVICE-WIDTH-INPUT-20260926.md` 「구현 결정 · 기준 캡처 도구」(수치 모드 ·
 * 수치 전용 실행 · 동작 어휘 2 · 수치 판정 스크립트 · 레인 거르기) · 「새 장면」 · 「시험 결정」(대상 목록 길이 먼저 ·
 * 가림 판정 장면의 지도 칸 폭 없음 78 · 상자 없는 요소 「재지 않음」) · 부록 B(52항목) · 부록 I 「L0b」 행.
 * ⑴ 대상 목록(`scripts/visual-baseline/targets.json`) — 길이 · 번호 · 레인 · 캡처 사각 · 폭 숨김 · 레인 장면.
 * ⑵ 장면 목록(`scenes.json`) — 새 장면 3 · 동작 어휘 · 전제조건 · 색인 450 · 모든 행의 `query`.
 * ⑶ 판정 스크립트(`scripts/visual-baseline/judge.mjs`) — 순수 함수 픽스처 · 레인 거르기 · 면제 목록 · CLI 종료코드.
 * ⑷ 캡처 실행기(`capture.py`) — 새 동작 어휘 · 전제조건 · 수치 전용 뷰포트 · 클릭 전 스크롤 영역 잘림 확인.
 * 실제 브라우저 수치는 캡처 실행(레인 보고의 두 번 찍기 · 장면 연결 · red 시연)이 확인한다 — 이 시험 밖이다.
 * 환경 의존: ⑷ 는 `python3` 를 부른다. 없으면 호출 종료코드 단언이 red 로 드러난다(건너뛰지 않는다).
 */
// @ts-expect-error — 타입 선언 없이 런타임만 쓴다(vitest 는 node 위에서 돈다 · 선례 device-width-input-20260926-L0a).
import { spawnSync } from 'node:child_process';
// @ts-expect-error — 같은 이유.
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
// @ts-expect-error — 같은 이유.
import { tmpdir } from 'node:os';
// @ts-expect-error — 같은 이유.
import { join, resolve } from 'node:path';
// @ts-expect-error — 같은 이유.
import { runInNewContext } from 'node:vm';
import { afterAll, describe, expect, it } from 'vitest';
import {
  judge, links, parseExempt, MAP_BOUNDARY, OCCLUSION_SCENES,
  type Metrics, type TargetHit, type TargetList,
} from '../scripts/visual-baseline/judge.mjs';
import * as detail from '../src/components/datasetpreview/fixture';
import * as upload from '../src/components/upload/fixture';

declare const process: { cwd(): string; execPath: string };

const VB = resolve(process.cwd(), 'scripts/visual-baseline');
const TARGETS = JSON.parse(readFileSync(join(VB, 'targets.json'), 'utf8')) as TargetList;
const EXEMPT_TEXT = readFileSync(join(VB, 'judge-exempt.txt'), 'utf8') as string;

interface Scene {
  name: string; entry: string; query: Record<string, string>; themes: string[]; viewports?: string[];
  fullPage: boolean; actions: Record<string, unknown>[]; require?: Record<string, string>[];
}
const MANIFEST = JSON.parse(readFileSync(join(VB, 'scenes.json'), 'utf8')) as { viewports: { id: string }[]; scenes: Scene[] };
const NEW_SCENES = ['detail-preview-map', 'detail-preview-map-value', 'upload-preview-expand'];
const LANES = ['L1', 'L2a', 'L2b', 'L3a', 'L3b'];

// ---- ⑴ 대상 목록 --------------------------------------------------------------------------------

describe('L0b ⑴ 대상 목록 — 부록 B 52항목(길이 먼저)', () => {
  const byN = new Map(TARGETS.targets.map((t) => [t.n, t]));
  const nums = (pred: (t: TargetList['targets'][number]) => boolean) => TARGETS.targets.filter(pred).map((t) => t.n);

  it('대상 = 52(고정 px 48 ＋ 회귀 감시 4) · 번호 1–53 중 20번(문장 속 링크 · 우려 1 예외) 제외', () => {
    expect(TARGETS.schema).toBe('colab-touch-targets/1');
    expect(TARGETS.targets.length).toBe(52);
    const want = Array.from({ length: 53 }, (_, i) => i + 1).filter((n) => n !== 20);
    expect(TARGETS.targets.map((t) => t.n)).toEqual(want);
    expect(new Set(TARGETS.targets.map((t) => t.selector)).size).toBe(52);
  });

  it('캡처 사각 7(15–17 · 28 · 47–49) · 폭 숨김 2(3 · 4) · 세로만 판정 4(50–53)', () => {
    expect(nums((t) => t.captureBlind === true)).toEqual([15, 16, 17, 28, 47, 48, 49]);
    expect(nums((t) => t.widthHidden === true)).toEqual([3, 4]);
    expect(nums((t) => t.heightOnly === true)).toEqual([50, 51, 52, 53]);
  });

  it('레인 열 = 부록 B(L1 3 · L2a 9 · L2b 34 · L3b 2 · 「—」 4)', () => {
    expect(nums((t) => t.lane === 'L1')).toEqual([23, 29, 30]);
    expect(nums((t) => t.lane === 'L2a')).toEqual([1, 2, 3, 4, 5, 6, 7, 21, 22]);
    expect(nums((t) => t.lane === 'L2b').length).toBe(34);
    expect(nums((t) => t.lane === 'L3b')).toEqual([36, 45]);
    expect(nums((t) => t.lane === '—')).toEqual([50, 51, 52, 53]);
    expect(TARGETS.targets.every((t) => [...LANES, '—'].includes(t.lane))).toBe(true);
  });

  it('선택자는 부록 B 원문(대표 항목) · 13번은 행 높이로 잰다', () => {
    expect(byN.get(1)?.selector).toBe('a.brand');
    expect(byN.get(13)?.selector).toBe('.tbl .catalog-open');
    expect(byN.get(13)?.measure).toBe('row');
    expect(byN.get(30)?.selector).toBe('.pv-zoom button, .pv-shot button');
    expect(byN.get(42)?.selector).toBe('.mapbar .btn-ghost');
    expect(byN.get(50)?.selector).toBe('.btn');
    expect(byN.get(53)?.selector).toBe('.sel');
  });

  it('레인 장면 = 부록 I 자기 게이트의 `frontend-visual` 장면 ＋ 수치 전용 장면 · 모두 장면 목록에 있다', () => {
    expect(Object.keys(TARGETS.laneScenes)).toEqual(LANES);
    expect(TARGETS.laneScenes.L1).toEqual(['detail', 'preview', 'preview-done', ...NEW_SCENES]);
    expect(TARGETS.laneScenes.L2a).toEqual(['primitives', 'catalog', 'detail', 'gnb-more', 'login', 'not-found']);
    expect(TARGETS.laneScenes.L2b).toEqual(['catalog', 'search', 'search-down', 'detail', 'lab', 'projects', 'project-detail',
      'project-dialog', 'settings', 'members', 'account-admin', 'login', 'lineage-picker', 'upload',
      'upload-classify', 'upload-metadata', 'upload-link']);
    expect(TARGETS.laneScenes.L3a).toEqual(['catalog', 'detail', 'project-detail', 'account-admin']);
    expect(TARGETS.laneScenes.L3b).toEqual(['members', 'detail', 'upload']);
    const names = new Set(MANIFEST.scenes.map((s) => s.name));
    for (const t of TARGETS.targets) for (const s of t.scenes) expect(names.has(s), `${t.n}: ${s}`).toBe(true);
  });

  it('장면 연결 — 레인 L1–L3b 이고 캡처 사각 · 폭 숨김이 아닌 대상은 자기 레인 장면이 있고, 50–53 은 어느 레인 장면이든 있다', () => {
    const anyLane = new Set(Object.values(TARGETS.laneScenes).flat());
    const missing = TARGETS.targets.filter((t) => {
      if (t.captureBlind || t.widthHidden) return false;
      const own = t.lane === '—' ? anyLane : new Set(TARGETS.laneScenes[t.lane] ?? []);
      return !t.scenes.some((s) => own.has(s));
    }).map((t) => t.n);
    expect(missing).toEqual([]);
    expect(TARGETS.targets.filter((t) => t.captureBlind).every((t) => t.scenes.length === 0)).toBe(true);
    expect(byN.get(3)?.scenes).toContain('catalog');
    expect(byN.get(4)?.scenes).toContain('catalog');
  });
});

// ---- ⑵ 장면 목록 --------------------------------------------------------------------------------

describe('L0b ⑵ 장면 목록 — 새 장면 3 · 동작 어휘 · 전제조건 · 색인 450', () => {
  const scene = (name: string) => MANIFEST.scenes.find((s) => s.name === name);

  it('장면 38 = 기존 35 ＋ 새 3(순서대로 끝에) · 캡처 수 = 34 × 12 ＋ 6 ＋ 3 × 12 = 450', () => {
    expect(MANIFEST.scenes.length).toBe(38);
    expect(MANIFEST.scenes.slice(-3).map((s) => s.name)).toEqual(NEW_SCENES);
    const all = MANIFEST.viewports.map((v) => v.id);
    const count = MANIFEST.scenes.reduce((n, s) => n + (s.viewports ?? all).length * s.themes.length, 0);
    expect(count).toBe(450);
    for (const name of NEW_SCENES) expect(scene(name)?.viewports, name).toBeUndefined();
  });

  it('모든 장면 행은 `query` 객체를 가진다(업로드 장면 잠금 시험이 모든 행의 `query` 를 읽는다)', () => {
    for (const s of MANIFEST.scenes) expect(typeof s.query, s.name).toBe('object');
  });

  it('상세 지도 두 장면 — audit-design 진입 · 질의 {scene, design: full} · 업로드 권한 · 동작 「보기」 활성 대기 → 누름 → 그림 로드 대기 → 안정 대기', () => {
    for (const name of ['detail-preview-map', 'detail-preview-map-value']) {
      const s = scene(name);
      expect(s?.entry).toBe('audit-design.html');
      expect(s?.query).toEqual({ scene: name, design: 'full' });
      expect((s as unknown as { account: { upload: boolean } }).account.upload).toBe(true);
      expect(s?.actions.slice(0, 4)).toEqual([
        { waitFor: '[data-testid=dt-preview-draw]:not([disabled])' },
        { click: '[data-testid=dt-preview-draw]' },
        { waitImage: '[data-testid=preview-single-image]' },
        { stable: '[data-testid=preview-single-image]' },
      ]);
      expect(s?.require).toEqual([
        { imageLoaded: '[data-testid=preview-single-image]' },
        { box: '[data-testid=preview-viewport]' },
        { exists: '[data-testid=preview-layers][data-zoom-scale]' },
        { exists: '.pv-shot button' },
      ]);
    }
    expect(scene('detail-preview-map')?.actions.length).toBe(4);
    // 값 결과 장면: 지도 중심을 누른 뒤(실제 포인터 위치 누름 · 가리는 도구가 있으면 도구가 받는다) 값 패널이 멈출 때까지.
    expect(scene('detail-preview-map-value')?.actions.slice(4)).toEqual([
      { click: '[data-testid=preview-viewport]' },
      { stable: '[data-testid=value-lookup]' },
    ]);
  });

  it('업로드 미리보기 확장보기 — audit-design 진입(업로드 잠금 거르기 밖) · 창 장면 · 그리기 → 로드 → 확장보기 → 로드 → 안정', () => {
    const s = scene('upload-preview-expand');
    expect(s?.entry).toBe('audit-design.html');
    expect(s?.query).toEqual({ scene: 'upload-preview-expand', design: 'full' });
    expect(s?.fullPage).toBe(false);
    expect(s?.actions).toEqual([
      { waitFor: '[data-testid=up-preview-draw]:not([disabled])' },
      { click: '[data-testid=up-preview-draw]' },
      { waitImage: '[data-testid=up-preview-image]' },
      { click: '[data-testid=pv-expand]' },
      { waitImage: '[data-testid=pv-expand-image]' },
      { stable: '[data-testid=pv-expand-image]' },
    ]);
    expect(s?.require).toEqual([
      { imageLoaded: '[data-testid=pv-expand-image]' },
      { box: '[data-testid=pv-expand-viewport]' },
      { exists: '[data-testid=pv-expand-zoom]' },
    ]);
  });

  it('audit-upload 진입의 등록 전 장면은 여전히 이름 4개 · 빈 질의다(기존 잠금과 같은 거르기)', () => {
    const plain = MANIFEST.scenes.filter((s) => s.entry === 'audit-upload.html' && s.query.register !== 'ok');
    expect(plain.map((s) => s.name)).toEqual(['upload', 'upload-classify', 'upload-metadata', 'upload-link']);
  });

  it('audit-design.tsx 가 새 장면 3개를 그리고, 확장보기 장면은 맨 위 메뉴 없는 단독 목록에 있다', () => {
    const audit = readFileSync(resolve(process.cwd(), 'audit-design.tsx'), 'utf8') as string;
    for (const name of NEW_SCENES) expect(audit).toContain(`'${name}'`);
    expect(audit).toMatch(/const STANDALONE = \[[^\]]*'upload-preview-expand'[^\]]*\]/);
    expect(audit).toContain('fixtureDatasetPreviewSource(');
    expect(audit).toContain('fixtureUploadPreviewSource(');
  });
});

// ---- 픽스처 미리보기 원천 -------------------------------------------------------------------------

describe('L0b 픽스처 미리보기 원천 — 타이머 없음 · 팔레트 3 · 첫 조회 완료 · 긴 이름', () => {
  it('긴 이름 길이 — 데이터셋 이름 80 · 파일 경로 72 · 변수 이름 38(`HLS.S30.T52SCE.2025361T022121.v2.0.B02`)', () => {
    expect([...detail.FIXTURE_PREVIEW_DATASET_NAME].length).toBe(80);
    expect([...detail.FIXTURE_PREVIEW_FILE_PATH].length).toBe(72);
    expect(detail.FIXTURE_PREVIEW_VARIABLE).toBe('HLS.S30.T52SCE.2025361T022121.v2.0.B02');
    expect(detail.FIXTURE_PREVIEW_VARIABLE.length).toBe(38);
  });

  it('상세 원천 — 팔레트 3 · 파일 1 · 변수 1(기본) · 만들기는 그리는 중 · 첫 조회에 완료(그림 1장 · 범례 6구간) · 값 조회 고정값', async () => {
    const src = detail.fixtureDatasetPreviewSource('/map.png');
    expect((await src.palettes()).length).toBe(3);
    expect((await src.files!()).map((f) => f.fileName)).toEqual([detail.FIXTURE_PREVIEW_FILE_PATH]);
    const desc = await src.describe!();
    expect(desc.variables).toEqual([detail.FIXTURE_PREVIEW_VARIABLE]);
    expect(desc.default?.variable).toBe(detail.FIXTURE_PREVIEW_VARIABLE);
    const job = await src.create({ datasetId: 'd', palette: 'viridis', classCount: 6 });
    expect(job.status).toBe('그리는 중');
    const done = await src.get(job.renderId);
    expect(done.status).toBe('완료');
    expect(done.result?.imageUrl).toBe('/map.png');
    expect(done.result?.legend.classes.length).toBe(6);
    const v = await src.lookupValue({ lat: 35.6, lon: 127.4 });
    expect(v.available).toBe(true);
    expect(v.value).toBe(0.0412);
  });

  it('업로드 원천 — 팔레트 3 · 만들기는 그리는 중 · 첫 조회에 완료 · 같은 그림 1장', async () => {
    const src = upload.fixtureUploadPreviewSource('/map.png');
    expect((await src.palettes()).length).toBe(3);
    const job = await src.createRender({ target: { uploadId: 'u' }, style: { palette: 'viridis', classCount: 6 } } as never);
    expect(job.status).toBe('그리는 중');
    const done = await src.getRender(job.renderId);
    expect(done.result?.imageUrl).toBe('/map.png');
  });

  it('원천 원문에 타이머가 없다(setTimeout · setInterval 0)', () => {
    for (const f of ['src/components/datasetpreview/fixture.ts', 'src/components/upload/fixture.ts']) {
      const text = readFileSync(resolve(process.cwd(), f), 'utf8') as string;
      expect(text, f).not.toMatch(/setTimeout|setInterval/);
    }
  });
});

// ---- ⑶ 판정 스크립트 ----------------------------------------------------------------------------

const NO_EXEMPT = parseExempt('');

/** 대상 목록 전체에 대해 기본 hit(44x44 상자 · 요소 id 는 번호)를 만든다. `over` 로 번호별 hit 를 바꾼다. */
function touchMetrics(scene: string, over: Record<number, Partial<TargetHit>[] | null> = {}, extra: Partial<Metrics> = {}): Metrics {
  return {
    schema: 'colab-visual-metrics/1', scene, theme: 'light', viewport: '390', width: 390, height: 844, input: 'touch',
    exemptList: [],
    targets: TARGETS.targets.map((t) => {
      const hits = t.n in over ? (over[t.n] ?? []) : (t.captureBlind ? [] : [{}]);
      return {
        n: t.n,
        hits: hits.map((h, i) => ({ id: t.n * 100 + i, w: 44, h: 44, box: true, via: 'self', path: `x${t.n}`, exempt: [], ...h })),
      };
    }),
    smallOther: { count: 0, top: [] },
    inputFont: { of: 1, small: [] },
    overflow: { scrollWidth: 390, innerWidth: 390, roots: [] },
    // 가림 판정 장면은 지도 칸 폭이 있어야 한다(없으면 78) — 기본은 좁은 지도 칸 · 네 도구 가림 0.
    map: OCCLUSION_SCENES.includes(scene) ? mapBlock(332, 0) : null,
    ...extra,
  };
}

function mapBlock(cellWidth: number | null, fourTools: number | null, zoomGroup = 0) {
  return {
    cellWidth, touchAction: 'none', dragAxis: null, viewportData: {}, valueState: '안내',
    coverage: fourTools === null ? null : { imagePct: fourTools + zoomGroup, fourTools, zoomGroup, tools: { legend: fourTools, value: 0, hud: 0, shot: 0 }, overlays: [] },
  };
}

/** 모든 대상이 상자로 재지는 기본 묶음 — 레인 장면(부록 I)마다 390 터치 한 장. */
function cleanSet(): Metrics[] {
  const scenes = [...new Set(Object.values(TARGETS.laneScenes).flat())];
  return scenes.map((s) => touchMetrics(s));
}

describe('L0b ⑶ 판정 스크립트 — 순수 함수 픽스처', () => {
  it('상수 — 가림 판정 장면 3 · 지도 경계 810', () => {
    expect(OCCLUSION_SCENES).toEqual(['detail-preview-map', 'detail-preview-map-value', 'preview-done']);
    expect(MAP_BOUNDARY).toBe(810);
  });

  it('수치 파일 0개 → 78', () => {
    expect(judge({ metrics: [], targets: TARGETS, exempt: NO_EXEMPT }).code).toBe(78);
  });

  it('깨끗한 묶음 → 종료 0 · red 0', () => {
    const r = judge({ metrics: cleanSet(), targets: TARGETS, exempt: NO_EXEMPT });
    expect(r.readiness).toEqual([]);
    expect(r.red).toEqual([]);
    expect(r.code).toBe(0);
  });

  it('누름 칸 44 미만(1–49 번) → red · 가로만 모자라도 red', () => {
    const r = judge({ metrics: [...cleanSet(), touchMetrics('catalog', { 14: [{ w: 36, h: 44 }] })], targets: TARGETS, exempt: NO_EXEMPT });
    expect(r.code).toBe(1);
    expect(r.red.map((x) => [x.metric, x.n])).toEqual([['44', 14]]);
  });

  it('회귀 감시 50–53 은 세로만 — 가로 30 은 red 아님 · 세로 40 은 red', () => {
    const wide = judge({ metrics: [...cleanSet(), touchMetrics('primitives', { 50: [{ w: 30, h: 44 }] })], targets: TARGETS, exempt: NO_EXEMPT });
    expect(wide.code).toBe(0);
    const low = judge({ metrics: [...cleanSet(), touchMetrics('primitives', { 51: [{ w: 60, h: 40 }] })], targets: TARGETS, exempt: NO_EXEMPT });
    expect(low.red.map((x) => [x.metric, x.n])).toEqual([['44', 51]]);
  });

  it('1–49 번에도 맞는 요소는 1–49 번으로만 판정한다(42 번 확장보기 단추 = `.btn-sm` · L1 거르기에서 51 번으로 잡지 않음)', () => {
    const shared = { id: 4242, w: 37, h: 40 };
    const m = touchMetrics('upload-preview-expand', { 42: [shared], 51: [shared] });
    const all = judge({ metrics: [...cleanSet(), m], targets: TARGETS, exempt: NO_EXEMPT });
    expect(all.red.map((x) => x.n)).toEqual([42]);
    const l1 = judge({ metrics: [...cleanSet(), m], targets: TARGETS, exempt: NO_EXEMPT, lane: 'L1' });
    expect(l1.red).toEqual([]);
    expect(l1.outsideRed['44']).toBe(1);
    expect(l1.code).toBe(0);
  });

  it('상자 없는 요소(display none · 가로나 세로 0)는 「재지 않음」으로 세고 red 로 판정하지 않는다(폭 숨김 3 · 4 @390)', () => {
    const m = touchMetrics('catalog', { 3: [{ w: 0, h: 0, box: false }], 4: [{ w: 86, h: 0, box: false }] });
    const r = judge({ metrics: [...cleanSet(), m], targets: TARGETS, exempt: NO_EXEMPT });
    expect(r.red).toEqual([]);
    expect(r.notMeasured).toBe(2);
    expect(r.code).toBe(0);
  });

  it('입력 글자 16 미만 → red · 가로 넘침(잘림 없는 루트) → red', () => {
    const font = touchMetrics('login', {}, { inputFont: { of: 2, small: [{ path: 'select.theme-switcher', fontSize: 13, exempt: [] }] } });
    const over = touchMetrics('login', {}, { overflow: { scrollWidth: 420, innerWidth: 390, roots: [{ path: 'div.x', right: 420, exempt: [] }] } });
    const r = judge({ metrics: [...cleanSet(), font, over], targets: TARGETS, exempt: NO_EXEMPT });
    expect(r.red.map((x) => x.metric).sort()).toEqual(['16', '넘침']);
    expect(r.code).toBe(1);
  });

  it('마우스 캡처(1440)는 44 · 16 을 재지 않는다 — 넘침만 판정', () => {
    const mouse: Metrics = { ...touchMetrics('catalog'), viewport: '1440', width: 1440, height: 900, input: 'mouse', targets: null, inputFont: null, smallOther: null };
    const r = judge({ metrics: [...cleanSet(), mouse], targets: TARGETS, exempt: NO_EXEMPT });
    expect(r.code).toBe(0);
  });

  it('가림 — 판정 장면 지도 칸 332 에서 네 도구 가림 > 0 → red · 1190 은 기록만 · 확장보기 · 확대 묶음은 기록만', () => {
    const narrow = touchMetrics('detail-preview-map', {}, { map: mapBlock(332, 100, 34) });
    const wide = { ...touchMetrics('detail-preview-map'), viewport: '1440', width: 1440, input: 'mouse' as const, targets: null, inputFont: null, smallOther: null, map: mapBlock(1190, 5, 2) };
    const expand = touchMetrics('upload-preview-expand', {}, { map: mapBlock(null, 40, 20) });
    const zoomOnly = touchMetrics('preview-done', {}, { map: mapBlock(332, 0, 30) });
    const r = judge({ metrics: [...cleanSet(), narrow, wide, expand, zoomOnly], targets: TARGETS, exempt: NO_EXEMPT });
    expect(r.red.map((x) => [x.metric, x.capture])).toEqual([['가림', 'detail-preview-map-light-390']]);
    expect(r.red[0]?.value).toBe(100);
    expect(r.recorded.map((x) => x.capture)).toContain('upload-preview-expand-light-390');
    expect(r.code).toBe(1);
  });

  it('지도 칸 경계 809 → 판정 · 810 → 기록만', () => {
    const at = (w: number) => judge({ metrics: [...cleanSet(), touchMetrics('preview-done', {}, { map: mapBlock(w, 3) })], targets: TARGETS, exempt: NO_EXEMPT });
    expect(at(809).code).toBe(1);
    expect(at(810).code).toBe(0);
  });

  it('가림 판정 장면의 수치 파일에 지도 칸 폭이 없으면 78 — 확장보기(판정 장면 아님)는 폭이 없어도 된다', () => {
    const noMap = touchMetrics('detail-preview-map', {}, { map: null });
    expect(judge({ metrics: [...cleanSet(), noMap], targets: TARGETS, exempt: NO_EXEMPT }).code).toBe(78);
    const noWidth = touchMetrics('detail-preview-map-value', {}, { map: mapBlock(null, 0) });
    const r = judge({ metrics: [...cleanSet(), noWidth], targets: TARGETS, exempt: NO_EXEMPT });
    expect(r.code).toBe(78);
    expect(r.readiness.join('\n')).toContain('detail-preview-map-value-light-390');
    const expand = touchMetrics('upload-preview-expand', {}, { map: mapBlock(null, 10) });
    expect(judge({ metrics: [...cleanSet(), expand], targets: TARGETS, exempt: NO_EXEMPT }).code).toBe(0);
  });

  it('장면에 선언된 대상이 하나도 맞지 않으면 78(캡처 사각 제외)', () => {
    const declared = TARGETS.targets.filter((t) => t.scenes.includes('members')).map((t) => t.n);
    expect(declared.length).toBeGreaterThan(0);
    const none = touchMetrics('members', Object.fromEntries(declared.map((n) => [n, []])));
    const r = judge({ metrics: [...cleanSet(), none], targets: TARGETS, exempt: NO_EXEMPT });
    expect(r.code).toBe(78);
    expect(r.readiness.join('\n')).toContain('members-light-390');
  });

  it('레인 거르기 — 좁힌 밖의 red 는 개수만 · 좁힌 레인 대상이 한 번도 재지지 않으면 78(대상 번호 출력) · 캡처 사각은 제외하고 셈', () => {
    const smallL2b = touchMetrics('catalog', { 14: [{ w: 36, h: 36 }] });
    const l1 = judge({ metrics: [...cleanSet(), smallL2b], targets: TARGETS, exempt: NO_EXEMPT, lane: 'L1' });
    expect(l1.code).toBe(0);
    expect(l1.outsideRed['44']).toBe(1);
    // L3b 대상 36 · 45 가 어느 파일에서도 상자로 재지지 않았다.
    const unmeasured = cleanSet().map((m) => ({ ...m, targets: (m.targets ?? []).map((t) => ([36, 45].includes(t.n) ? { ...t, hits: [] } : t)) }));
    const l3b = judge({ metrics: [...unmeasured, touchMetrics('members', { 36: [], 45: [] })], targets: TARGETS, exempt: NO_EXEMPT, lane: 'L3b' });
    expect(l3b.code).toBe(78);
    expect(l3b.unmeasured).toEqual([36, 45]);
    // 캡처 사각(L2b 7개)은 재지지 않아도 78 이 아니다.
    const l2b = judge({ metrics: cleanSet(), targets: TARGETS, exempt: NO_EXEMPT, lane: 'L2b' });
    expect(l2b.unmeasured).toEqual([]);
    expect(l2b.captureBlind).toBe(7);
    expect(l2b.code).toBe(0);
  });

  it('레인 거르기 — 폭 숨김 3 · 4 가 390 에서 「재지 않음」뿐이면 L2a 는 78, 1024 실행을 더하면 0', () => {
    const at390 = cleanSet().map((m) => ({ ...m, targets: (m.targets ?? []).map((t) => ([3, 4].includes(t.n) ? { ...t, hits: [{ id: t.n, w: 0, h: 0, box: false, via: 'self', path: 'x', exempt: [] }] } : t)) }));
    expect(judge({ metrics: at390, targets: TARGETS, exempt: NO_EXEMPT, lane: 'L2a' }).unmeasured).toEqual([3, 4]);
    const at1024 = { ...touchMetrics('catalog'), viewport: '1024', width: 1024, height: 1366 };
    expect(judge({ metrics: [...at390, at1024], targets: TARGETS, exempt: NO_EXEMPT, lane: 'L2a' }).code).toBe(0);
  });

  it('레인 거르기 — 가림은 L1 만 잰다(L2b 에서는 개수만)', () => {
    const narrow = touchMetrics('detail-preview-map', {}, { map: mapBlock(332, 100) });
    const l2b = judge({ metrics: [...cleanSet(), narrow], targets: TARGETS, exempt: NO_EXEMPT, lane: 'L2b' });
    expect(l2b.code).toBe(0);
    expect(l2b.outsideRed['가림']).toBe(1);
    const l1 = judge({ metrics: [...cleanSet(), narrow], targets: TARGETS, exempt: NO_EXEMPT, lane: 'L1' });
    expect(l1.code).toBe(1);
  });

  it('모르는 레인 이름 → 78', () => {
    expect(judge({ metrics: cleanSet(), targets: TARGETS, exempt: NO_EXEMPT, lane: 'L9' }).code).toBe(78);
  });
});

describe('L0b ⑶ 판정 면제 목록 — `지표 · 선택자 · 사유` · 구멍 red', () => {
  it('저장소의 면제 목록 파일은 형식 오류 0 · 줄 0(지금 면제할 것이 없다)', () => {
    const p = parseExempt(EXEMPT_TEXT);
    expect(p.errors).toEqual([]);
    expect(p.lines).toEqual([]);
  });

  it('형식 — 주석 · 빈 줄은 건너뛰고, 모르는 지표 · 빈 사유 · 칸 수 오류는 오류 줄', () => {
    const p = parseExempt([
      '# 주석', '', '44 · .pj-views button · 표 보기 전환 — 다음 intent', '16 · select.theme-switcher · ',
      '가림 · .pv-legend · 가림은 면제하지 않는다', '44 · .x', '넘침 · .tblwrap table · 표는 가로 스크롤',
    ].join('\n'));
    expect(p.lines.map((l) => [l.metric, l.selector])).toEqual([['44', '.pj-views button'], ['넘침', '.tblwrap table']]);
    expect(p.errors.map((e) => e.line)).toEqual([4, 5, 6]);
  });

  it('형식 오류 줄이 있으면 red(아무것도 면제하지 않는다)', () => {
    const r = judge({ metrics: cleanSet(), targets: TARGETS, exempt: parseExempt('44 · .x') });
    expect(r.code).toBe(1);
    expect(r.red.map((x) => x.metric)).toEqual(['면제']);
  });

  it('맞는 줄은 red 를 면제한다(개수 출력) · 쓰이지 않은 줄은 구멍 red', () => {
    const exempt = parseExempt('44 · .rowact .rab · 행 작업 칸 — 사유\n16 · .never · 맞는 것 없음');
    const list = exempt.lines.map((l) => ({ metric: l.metric, selector: l.selector }));
    const small = touchMetrics('catalog', { 14: [{ w: 36, h: 36, exempt: [0] }] }, { exemptList: list });
    const set = cleanSet().map((m) => ({ ...m, exemptList: list }));
    const r = judge({ metrics: [...set, small], targets: TARGETS, exempt });
    expect(r.exemptHits).toBe(1);
    expect(r.exemptHoles.map((l) => l.selector)).toEqual(['.never']);
    expect(r.red.map((x) => x.metric)).toEqual(['면제']);
    expect(r.code).toBe(1);
  });

  it('수치 파일이 찍을 때 받은 면제 목록과 지금 목록이 다르면 78(목록을 바꾼 뒤 다시 재지 않음)', () => {
    const exempt = parseExempt('44 · .rowact .rab · 사유');
    const r = judge({ metrics: cleanSet(), targets: TARGETS, exempt });
    expect(r.code).toBe(78);
  });
});

describe('L0b ⑶ 장면 연결 검사(`links`) — 390 수치 전용 실행에서 대상이 그려지는 장면', () => {
  it('390 에서 상자가 있는 장면만 센다 · 규칙을 채우면 0', () => {
    const r = links({ metrics: cleanSet(), targets: TARGETS });
    expect(r.missing).toEqual([]);
    expect(r.code).toBe(0);
  });

  it('레인 대상이 자기 레인 장면에서 그려지지 않으면 78 · 대상 번호 출력', () => {
    const set = cleanSet().map((m) => ({ ...m, targets: (m.targets ?? []).map((t) => (t.n === 23 ? { ...t, hits: [] } : t)) }));
    const r = links({ metrics: set, targets: TARGETS });
    expect(r.code).toBe(78);
    expect(r.missing).toEqual([23]);
  });

  it('390 이 아닌 수치 파일은 세지 않는다', () => {
    const at820 = cleanSet().map((m) => ({ ...m, viewport: '820', width: 820 }));
    expect(links({ metrics: at820, targets: TARGETS }).code).toBe(78);
  });
});

// ---- ⑶ CLI 종료코드 ----------------------------------------------------------------------------

const WORK = mkdtempSync(join(tmpdir(), 'dwi-l0b-'));
afterAll(() => rmSync(WORK, { recursive: true, force: true }));

function writeSet(name: string, metrics: Metrics[]): string {
  const dir = join(WORK, name);
  mkdirSync(dir, { recursive: true });
  metrics.forEach((m, i) => writeFileSync(join(dir, `${m.scene}-${m.theme}-${m.viewport}-${i}.metrics.json`), JSON.stringify(m)));
  return dir;
}

function cli(...args: string[]) {
  return spawnSync(process.execPath, [join(VB, 'judge.mjs'), ...args], { encoding: 'utf8' });
}

describe('L0b ⑶ 판정 CLI — 종료 0 / 1 / 78', () => {
  it('깨끗한 폴더 → 0 · red 폴더 → 1 · 빈 폴더 → 78 · 모르는 플래그 → 78', () => {
    expect(cli(writeSet('clean', cleanSet())).status).toBe(0);
    const red = writeSet('red', [...cleanSet(), touchMetrics('detail-preview-map', {}, { map: mapBlock(332, 97) })]);
    const r = cli(red);
    expect(r.status).toBe(1);
    expect(r.stdout).toContain('가림');
    expect(cli(writeSet('empty', [])).status).toBe(78);
    expect(cli('--nope', red).status).toBe(78);
  });

  it('`--lane L1` 거르기 · `--links` 연결 검사 · `--out` 보고 파일', () => {
    const red = writeSet('lane', [...cleanSet(), touchMetrics('catalog', { 14: [{ w: 36, h: 36 }] })]);
    const out = join(WORK, 'lane-report.json');
    const r = cli('--lane', 'L1', '--out', out, red);
    expect(r.status).toBe(0);
    const rep = JSON.parse(readFileSync(out, 'utf8')) as { lane: string; outsideRed: Record<string, number> };
    expect(rep.lane).toBe('L1');
    expect(rep.outsideRed['44']).toBe(1);
    expect(cli('--links', red).status).toBe(0);
  });
});

// ---- ⑷ 캡처 실행기 -----------------------------------------------------------------------------

const CAPTURE = join(VB, 'capture.py');

/** capture.py 를 불러 `body` 를 돌린다 — ab · js 호출을 기록하고 js 는 `answers` 를 차례로 돌려준다. */
function py(body: string[], answers: unknown[] = []): { code: number; calls: { kind: string; args: string[] }[]; out: string; err: string } {
  const harness = [
    'import importlib.util, json, sys',
    'spec = importlib.util.spec_from_file_location("capture", sys.argv[1])',
    'm = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)',
    'calls = []; answers = json.loads(sys.argv[2])',
    'm.ab = lambda session, *args, **kw: calls.append({"kind": "ab", "args": list(args)}) or ""',
    'def fake_js(session, source):',
    '    calls.append({"kind": "js", "args": [source]})',
    '    return answers.pop(0) if answers else None',
    'm.js = fake_js',
    'm.time.sleep = lambda s: None',
    'code = 0',
    'try:',
    ...body.map((l) => `    ${l}`),
    'except m.CaptureError as e:',
    '    code = 78; print(str(e), file=sys.stderr)',
    'print(json.dumps({"code": code, "calls": calls}))',
  ].join('\n');
  const r = spawnSync('python3', ['-c', harness, CAPTURE, JSON.stringify(answers)], { encoding: 'utf8' });
  expect(r.status, r.stderr).toBe(0);
  const lines = (r.stdout as string).trim().split('\n');
  const last = JSON.parse(lines[lines.length - 1] ?? '{}') as { code: number; calls: { kind: string; args: string[] }[] };
  return { ...last, out: r.stdout, err: r.stderr };
}

describe('L0b ⑷ 동작 어휘 2 — 그림 로드 대기 · 안정 대기', () => {
  it('waitImage — 완료 · 원본 폭 > 0 이 될 때까지 페이지 스크립트로 확인한다', () => {
    const r = py(['m.run_action("s", {"waitImage": "img.x"})'], [false, false, true]);
    expect(r.code).toBe(0);
    expect(r.calls.filter((c) => c.kind === 'js').length).toBe(3);
    expect(r.calls[0]?.args[0]).toContain('naturalWidth');
    expect(r.calls[0]?.args[0]).toContain('complete');
  });

  it('waitImage — 끝내 로드되지 않으면 준비 실패(78)', () => {
    const r = py(['m.run_action("s", {"waitImage": "img.x"})'], []);
    expect(r.code).toBe(78);
  });

  it('stable — 상자 · 배율 표시 · 문서 높이 서명이 150ms 간격 3회 같으면 끝난다', () => {
    const r = py(['m.run_action("s", {"stable": "img.x"})'], ['a', 'b', 'b', 'b', 'b']);
    expect(r.code).toBe(0);
    expect(r.calls.filter((c) => c.kind === 'js').length).toBe(5);
    const sig = r.calls[0]?.args[0] ?? '';
    expect(sig).toContain('getBoundingClientRect');
    expect(sig).toContain('data-zoom-scale');
    expect(sig).toContain('scrollHeight');
  });

  it('stable — 끝내 멈추지 않으면 준비 실패(78)', () => {
    const answers = Array.from({ length: 200 }, (_, i) => `s${i}`);
    expect(py(['m.run_action("s", {"stable": "img.x"})'], answers).code).toBe(78);
  });
});

describe('L0b ⑷ 전제조건 · 수치 전용 뷰포트', () => {
  it('require — 모두 참이면 통과, 하나라도 거짓이면 준비 실패(78 · 조건 이름 출력)', () => {
    const req = '[{"imageLoaded": "img.x"}, {"box": ".vp"}, {"exists": ".z"}]';
    expect(py([`m.check_require("s", "scene-x", json.loads('${req}'))`], [[true, true, true]]).code).toBe(0);
    const bad = py([`m.check_require("s", "scene-x", json.loads('${req}'))`], [[true, false, true]]);
    expect(bad.code).toBe(78);
    expect(bad.err).toContain('box');
  });

  it('수치 전용 뷰포트 — 목록 id 는 목록 값 · 목록 밖 `507x820` 은 터치 · `:mouse` 는 마우스 · 형식 오류는 78', () => {
    const r = py([
      'vps = {"390": {"id": "390", "width": 390, "height": 844, "input": "touch"}}',
      'print(json.dumps([m.parse_viewport("390", vps), m.parse_viewport("507x820", vps), m.parse_viewport("600x900:mouse", vps)]))',
    ]);
    expect(r.code).toBe(0);
    const parsed = JSON.parse((r.out as string).trim().split('\n')[0] ?? '[]') as unknown[];
    expect(parsed).toEqual([
      { id: '390', width: 390, height: 844, input: 'touch' },
      { id: '507x820', width: 507, height: 820, input: 'touch' },
      { id: '600x900', width: 600, height: 900, input: 'mouse' },
    ]);
    expect(py(['m.parse_viewport("wide", {})']).code).toBe(78);
  });

  it('측정 스크립트(measure.js)가 있고 네 지표 · 지도 칸 폭 · touch-action · 값 패널 상태를 낸다', () => {
    const src = readFileSync(join(VB, 'measure.js'), 'utf8') as string;
    for (const key of ['targets', 'inputFont', 'overflow', 'coverage', 'cellWidth', 'touchAction', 'valueState', 'section.pv-map']) {
      expect(src, key).toContain(key);
    }
    expect(src).not.toMatch(/\/home\/|\/Users\/|[A-Z]:\\\\/);
  });
});

describe('L0b ⑷ click 전 스크롤 — 창 안이어도 스크롤 영역에 잘리면 먼저 보이게(L0a 남은 위험)', () => {
  function reveal(): string {
    const r = spawnSync('python3', ['-c', [
      'import importlib.util, sys',
      'spec = importlib.util.spec_from_file_location("capture", sys.argv[1])',
      'm = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)',
      'print(m.reveal_script(".t"))',
    ].join('\n'), CAPTURE], { encoding: 'utf8' });
    expect(r.status, r.stderr).toBe(0);
    return r.stdout as string;
  }
  interface Box { top: number; bottom: number; left: number; right: number }
  const rect = (b: Box) => ({ ...b, x: b.left, y: b.top, width: b.right - b.left, height: b.bottom - b.top });

  /** 대상 `box` 가 부모 `clip`(overflow auto · null = 잘림 없음) 안에 있는 가짜 문서에서 페이지 스크립트를 돌린다. */
  function run(box: Box, clip: Box | null) {
    const scrolls: unknown[] = [];
    const body = { nodeType: 1, parentElement: null, tagName: 'BODY' };
    const parent = clip ? { nodeType: 1, tagName: 'DIV', parentElement: body, getBoundingClientRect: () => rect(clip), clientLeft: 0, clientTop: 0, clientWidth: clip.right - clip.left, clientHeight: clip.bottom - clip.top } : body;
    const el = { nodeType: 1, tagName: 'BUTTON', parentElement: parent, getBoundingClientRect: () => rect(box), scrollIntoView: (o: unknown) => { scrolls.push(o); } };
    const result = runInNewContext(reveal(), {
      innerWidth: 390, innerHeight: 844,
      getComputedStyle: (e: unknown) => (e === parent && clip ? { overflowX: 'auto', overflowY: 'auto' } : { overflowX: 'visible', overflowY: 'visible' }),
      document: { querySelector: () => el, body, documentElement: { clientWidth: 390, clientHeight: 844 } },
    }) as unknown;
    return { scrolls, result };
  }

  it('창 안 · 잘림 없음 → 스크롤 0(기존 장면 영향 없음)', () => {
    expect(run({ top: 100, bottom: 144, left: 10, right: 100 }, null).scrolls).toEqual([]);
  });

  it('창 안이지만 스크롤 영역(overflow auto) 밖으로 잘림 → scrollIntoView({block: nearest, inline: nearest}) 한 번', () => {
    const r = run({ top: 500, bottom: 544, left: 10, right: 100 }, { top: 100, bottom: 400, left: 0, right: 390 });
    expect(r.scrolls).toEqual([{ block: 'nearest', inline: 'nearest' }]);
  });

  it('스크롤 영역 안에 다 보임 → 스크롤 0', () => {
    expect(run({ top: 200, bottom: 244, left: 10, right: 100 }, { top: 100, bottom: 400, left: 0, right: 390 }).scrolls).toEqual([]);
  });
});
