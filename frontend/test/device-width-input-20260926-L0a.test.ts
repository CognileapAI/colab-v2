/**
 * 휴대폰·패드 대응 20260926 L0a — 기준 캡처 도구 틀을 잠근다.
 *
 * 오라클 = `dev-package/prd/specs/S-DEVICE-WIDTH-INPUT-20260926.md` 「구현 결정 · 기준 캡처 도구」 ·
 * 「시험 결정」(뷰포트 = 6 · 비교 뷰포트 거르기 0장 78 · 색인 기존 장면 414) · 부록 I 「L0a」 행.
 * ⑴ 장면 목록 스키마(`scripts/visual-baseline/scenes.json`) — 뷰포트 목록 · 입력 방식 · 장면의 뷰포트 참조.
 * ⑵ 비교 스크립트(`scripts/visual-baseline/diff.mjs`) 뷰포트 id 거르기 — PNG 픽스처를 시험 안에서 만들어
 *    실제 CLI 를 돌린다(선례 `visual-diff.test.ts` · 바이너리 커밋 없음 · 실제 브라우저 없음).
 * ⑶ 캡처 동작 `click` — 대상 상자가 창 밖이면 먼저 창 안으로 스크롤한 뒤 누르고, 창 안이면 스크롤하지 않는다
 *    (오케스트레이터 결정 · spec 빈칸 「클릭 대상이 창 밖이면 먼저 창 안으로」). `capture.py` 의 `run_action` 을
 *    python 으로 불러 브라우저 호출을 기록하고, 기록된 페이지 스크립트를 가짜 문서 위에서 돌린다(실제 브라우저 없음).
 * 입력 래퍼의 실제 포인터 · hover 상태는 캡처 실행의 상태 확인(어긋나면 78)이 확인한다 — 이 시험 밖이다.
 * 환경 의존: ⑶ 은 `python3` 를 부른다. 없으면 호출 종료코드 단언이 red 로 드러난다(건너뛰지 않는다).
 */
// @ts-expect-error — 타입 선언 없이 런타임만 쓴다(vitest 는 node 위에서 돈다 · 선례 design-fix-followups-20260925-L2).
import { spawnSync } from 'node:child_process';
// @ts-expect-error — 같은 이유.
import { createHash } from 'node:crypto';
// @ts-expect-error — 같은 이유.
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
// @ts-expect-error — 같은 이유.
import { tmpdir } from 'node:os';
// @ts-expect-error — 같은 이유.
import { join, resolve } from 'node:path';
// @ts-expect-error — 같은 이유.
import { runInNewContext } from 'node:vm';
import { afterAll, describe, expect, it } from 'vitest';
import { encodePng } from '../scripts/visual-baseline/compare.mjs';

declare const process: { cwd(): string; execPath: string };

interface Viewport { id: string; width: number; height: number; input: string }
interface Scene { name: string; themes: string[]; viewports?: string[]; widths?: unknown }
interface Manifest {
  schema: string;
  viewport?: { height?: unknown };
  deviceScaleFactor: number;
  viewports: Viewport[];
  browser: { args: string[]; inputArgs: Record<string, string[]> };
  scenes: Scene[];
}

const MANIFEST = JSON.parse(readFileSync(resolve(process.cwd(), 'scripts/visual-baseline/scenes.json'), 'utf8')) as Manifest;
const DIFF = resolve(process.cwd(), 'scripts/visual-baseline/diff.mjs');

const SIX: Viewport[] = [
  { id: '390', width: 390, height: 844, input: 'touch' },
  { id: '844x390', width: 844, height: 390, input: 'touch' },
  { id: '820', width: 820, height: 1180, input: 'touch' },
  { id: '1024', width: 1024, height: 1366, input: 'touch' },
  { id: '1180', width: 1180, height: 820, input: 'touch' },
  { id: '1440', width: 1440, height: 900, input: 'mouse' },
];

describe('L0a ⑴ 장면 목록 스키마 — 6크기 × 입력 방식', () => {
  it('뷰포트 목록은 6개이고 spec 조각과 같다(id · 가로 · 세로 · 입력)', () => {
    expect(MANIFEST.viewports.length).toBe(6);
    expect(MANIFEST.viewports).toEqual(SIX);
  });

  it('스키마 판을 올렸다 — `colab-visual-scenes/2` · 옛 높이 한 값(`viewport.height`) 없음 · 배율 1', () => {
    expect(MANIFEST.schema).toBe('colab-visual-scenes/2');
    expect(MANIFEST.viewport?.height).toBeUndefined();
    expect(MANIFEST.deviceScaleFactor).toBe(1);
  });

  it('입력 방식은 touch · mouse 둘이고, 뷰포트가 쓰는 입력마다 실행 래퍼 인자가 있다', () => {
    const inputs = [...new Set(MANIFEST.viewports.map((v) => v.input))].sort();
    expect(inputs).toEqual(['mouse', 'touch']);
    expect(Object.keys(MANIFEST.browser.inputArgs).sort()).toEqual(['mouse', 'touch']);
    const touch = MANIFEST.browser.inputArgs.touch ?? [];
    expect(touch).toContain('--touch-events=enabled');
    expect(touch).toContain('--hide-scrollbars');
    for (const input of inputs) {
      expect((MANIFEST.browser.inputArgs[input] ?? []).some((a) => a.startsWith('--blink-settings='))).toBe(true);
    }
  });

  it('장면은 폭 목록(`widths`)을 쓰지 않고, 뷰포트 참조는 목록 안의 id 만 쓴다', () => {
    const ids = new Set(MANIFEST.viewports.map((v) => v.id));
    expect(MANIFEST.scenes.length).toBe(35);
    for (const s of MANIFEST.scenes) {
      expect(s.widths, s.name).toBeUndefined();
      if (s.viewports === undefined) continue;
      expect(s.viewports.length, s.name).toBeGreaterThan(0);
      expect(new Set(s.viewports).size, s.name).toBe(s.viewports.length);
      for (const id of s.viewports) expect(ids.has(id), `${s.name}: ${id}`).toBe(true);
    }
  });

  it('맨 위 메뉴 더보기(`gnb-more`)만 390 · 844x390 · 820 이고, 나머지 34 장면은 기본값(전체 6)이다', () => {
    const narrowed = MANIFEST.scenes.filter((s) => s.viewports !== undefined);
    expect(narrowed.map((s) => s.name)).toEqual(['gnb-more']);
    expect(narrowed[0]?.viewports).toEqual(['390', '844x390', '820']);
  });

  it('기존 장면 캡처 수 = 34 × 12 ＋ 더보기 6 = 414', () => {
    const count = MANIFEST.scenes.reduce((n, s) => n + (s.viewports ?? SIX.map((v) => v.id)).length * s.themes.length, 0);
    expect(count).toBe(414);
  });
});

// ---- ⑵ 비교 뷰포트 거르기 ----------------------------------------------------------------------

type Rgba = readonly [number, number, number, number];
const GREY: Rgba = [100, 100, 100, 255];

function png(fill: Rgba, paint: { x: number; y: number; c: Rgba }[] = []): Uint8Array {
  const w = 6;
  const h = 4;
  const data = new Uint8Array(w * h * 4);
  for (let i = 0; i < w * h; i++) data.set(fill, i * 4);
  for (const p of paint) data.set(p.c, (p.y * w + p.x) * 4);
  return encodePng({ width: w, height: h, data });
}

const WORK = mkdtempSync(join(tmpdir(), 'dwi-l0a-'));
afterAll(() => rmSync(WORK, { recursive: true, force: true }));

/** 장면 `s` 의 라이트 390 · 1440 두 장. 후보의 1440 한 장만 1픽셀 다르다. */
function captureDir(side: 'base' | 'cand'): string {
  const dir = join(WORK, side);
  mkdirSync(dir, { recursive: true });
  const shots = [
    { viewport: '390', width: 390, height: 844, input: 'touch', bytes: png(GREY) },
    { viewport: '1440', width: 1440, height: 900, input: 'mouse',
      bytes: side === 'cand' ? png(GREY, [{ x: 2, y: 1, c: [255, 255, 255, 255] }]) : png(GREY) },
  ];
  const captures = shots.map(({ bytes, ...vp }) => {
    const name = `s-light-${vp.viewport}`;
    writeFileSync(join(dir, `${name}.png`), bytes);
    return { name, scene: 's', theme: 'light', ...vp, file: `${name}.png`, bytes: bytes.length,
      sha256: createHash('sha256').update(bytes).digest('hex'), fullPage: true, pageErrors: '' };
  });
  writeFileSync(join(dir, 'index.json'), JSON.stringify({
    schema: 'colab-visual-index/2', manifestSha256: 'fixture', gitHead: 'fixture', gitDirty: false,
    capturedAt: '2026-09-26T00:00:00+00:00', parallel: 1, scenes: ['s'], captureCount: captures.length, captures,
  }));
  return dir;
}

const BASE = captureDir('base');
const CAND = captureDir('cand');
let runs = 0;

function diff(...flags: string[]) {
  const report = join(WORK, `report-${runs++}`);
  const r = spawnSync(process.execPath, [DIFF, ...flags, BASE, CAND, report], { encoding: 'utf8' });
  const read = () => JSON.parse(readFileSync(join(report, 'report.json'), 'utf8')) as {
    viewportFilter: string[] | null; totals: { captures: number }; red: string[]; rows: { name: string; viewport: string }[];
  };
  return { code: r.status, stderr: r.stderr, read };
}

describe('L0a ⑵ 비교 스크립트 뷰포트 id 거르기(`--viewport`) — 픽스처 CLI 실행', () => {
  it('① 거르기 없음 → 1440 의 1픽셀 차이로 종료 1(픽스처가 차이를 잡는다)', () => {
    const r = diff();
    expect(r.code).toBe(1);
    expect(r.read().red).toEqual(['s-light-1440']);
  });

  it('② `--viewport 390` → 390 한 장만 비교 · 종료 0 · 보고에 거르기 값과 행의 뷰포트 id', () => {
    const r = diff('--viewport', '390');
    expect(r.code).toBe(0);
    const rep = r.read();
    expect(rep.viewportFilter).toEqual(['390']);
    expect(rep.totals.captures).toBe(1);
    expect(rep.rows.map((row) => [row.name, row.viewport])).toEqual([['s-light-390', '390']]);
  });

  it('③ `--viewport 1440` → 1440 한 장 · 종료 1', () => {
    const r = diff('--viewport', '1440');
    expect(r.code).toBe(1);
    expect(r.read().totals.captures).toBe(1);
    expect(r.read().red).toEqual(['s-light-1440']);
  });

  it('④ 쉼표 목록 `--viewport 390,1440` → 두 장 · 종료 1', () => {
    const r = diff('--viewport', '390,1440');
    expect(r.code).toBe(1);
    expect(r.read().totals.captures).toBe(2);
  });

  it('⑤ 고른 캡처가 0장(`--viewport 820`) → 준비 실패 78', () => {
    const r = diff('--viewport', '820');
    expect(r.code).toBe(78);
    expect(r.stderr).toContain('::visual-diff-readiness::');
  });

  it('⑥ 값 없는 `--viewport` → 준비 실패 78', () => {
    const r = spawnSync(process.execPath, [DIFF, '--viewport'], { encoding: 'utf8' });
    expect(r.status).toBe(78);
  });
});

// ---- ⑶ click 동작 — 창 밖 대상은 먼저 창 안으로 ------------------------------------------------

const CAPTURE = resolve(process.cwd(), 'scripts/visual-baseline/capture.py');

/** `run_action(session, {click: selector})` 를 실제 capture.py 로 부르고 브라우저 호출(ab · js)을 순서대로 기록한다. */
function recordClick(selector: string): { kind: 'ab' | 'js'; args: string[] }[] {
  const harness = [
    'import importlib.util, json, sys',
    'spec = importlib.util.spec_from_file_location("capture", sys.argv[1])',
    'm = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)',
    'calls = []',
    'm.ab = lambda session, *args, **kw: calls.append({"kind": "ab", "args": list(args)}) or ""',
    'm.js = lambda session, source: calls.append({"kind": "js", "args": [source]}) or "inside"',
    'm.run_action("s", {"click": sys.argv[2]})',
    'print(json.dumps(calls))',
  ].join('\n');
  const r = spawnSync('python3', ['-c', harness, CAPTURE, selector], { encoding: 'utf8' });
  expect(r.status, r.stderr).toBe(0);
  return JSON.parse(r.stdout) as { kind: 'ab' | 'js'; args: string[] }[];
}

interface Box { top: number; bottom: number; left: number; right: number }

/** 기록된 페이지 스크립트를 창 `win` · 대상 상자 `box`(null = 대상 없음) 인 가짜 문서에서 돌린다. */
function runPageScript(source: string, win: { width: number; height: number }, box: Box | null) {
  const scrolls: unknown[] = [];
  const el = box && {
    getBoundingClientRect: () => ({ ...box, x: box.left, y: box.top, width: box.right - box.left, height: box.bottom - box.top }),
    scrollIntoView: (opts: unknown) => { scrolls.push(opts); },
  };
  const result = runInNewContext(source, {
    innerWidth: win.width, innerHeight: win.height,
    document: { querySelector: () => el, documentElement: { clientWidth: win.width, clientHeight: win.height } },
  }) as unknown;
  return { scrolls, result };
}

describe('L0a ⑶ 캡처 동작 `click` — 대상이 창 밖일 때만 먼저 창 안으로(오케스트레이터 결정)', () => {
  const SEL = '[data-testid=reg-open]';
  const WIN = { width: 844, height: 390 };

  it('click 은 페이지 스크립트(대상 확인 · 필요 시 스크롤)를 먼저 돌리고 그다음 같은 선택자를 누른다', () => {
    const calls = recordClick(SEL);
    expect(calls.map((c) => c.kind)).toEqual(['js', 'ab']);
    expect(calls[1]?.args).toEqual(['click', SEL]);
    expect(calls[0]?.args[0]).toContain(JSON.stringify(SEL));
  });

  it('창 밖 대상(844x390 · 업로드 단추 y=411.7 높이 44 실측) → scrollIntoView({block: nearest, inline: nearest}) 한 번', () => {
    const [probe] = recordClick(SEL);
    const r = runPageScript(probe?.args[0] ?? '', WIN, { top: 411.7, bottom: 455.7, left: 600, right: 800 });
    expect(r.scrolls).toEqual([{ block: 'nearest', inline: 'nearest' }]);
  });

  it('가로로 창 밖인 대상도 스크롤한다', () => {
    const [probe] = recordClick(SEL);
    const r = runPageScript(probe?.args[0] ?? '', WIN, { top: 100, bottom: 144, left: 900, right: 1000 });
    expect(r.scrolls).toEqual([{ block: 'nearest', inline: 'nearest' }]);
  });

  it('창 안 대상 → 스크롤하지 않는다(기존 장면 영향 없음)', () => {
    const [probe] = recordClick(SEL);
    const r = runPageScript(probe?.args[0] ?? '', WIN, { top: 300, bottom: 344, left: 600, right: 800 });
    expect(r.scrolls).toEqual([]);
  });

  it('대상이 없으면 스크롤하지 않고 스크립트도 실패하지 않는다(없음 판정은 누르기 단계가 그대로 낸다)', () => {
    const [probe] = recordClick(SEL);
    const r = runPageScript(probe?.args[0] ?? '', WIN, null);
    expect(r.scrolls).toEqual([]);
  });
});
