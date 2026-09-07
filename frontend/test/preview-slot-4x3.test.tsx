/**
 * WU-C1 · 미리보기 **자리 선점 4:3 틀** (축 ① · `intent/2026-09-08-preview-slot.md ①`).
 *
 * 오라클 = `dev-package/prd/rounds/R-C-2-frontend.md §2 WU-C1` 수용 기준 축자
 *  ⑴ 파일 선택 직후(그리기 전) 틀이 있고 `aspect-ratio` 4:3
 *  ⑵ idle→drawing→done→failed **네 상태**에서 바깥 상자 치수 불변(상태 건수 4 를 단언한다)
 *  ⑶ 진행 3단계 문면이 순서대로 · `data-testid="up-preview-stage"` 유지
 *  ⑷ 상세는 **열자마자**(`시작하는 중` 포함) 같은 틀
 *
 * ⚠ **jsdom 은 스타일을 계산하지 않는다** — `getComputedStyle` 이 `aspect-ratio` 를 돌려주지
 *   않으므로 비율은 ㈎ 요소의 클래스·`data-preview-slot` 표식과 ㈏ **CSS 원문**(`preview.css`)
 *   두 가지로 잰다(집 관례 — `design-fix-20260908.test.ts` 와 같은 규율).
 * ⚠ 치수 불변도 같은 이유로 **같은 CSS 상자(클래스)** 임을 단언하고, 아울러
 *   `getBoundingClientRect` 폭·높이가 네 상태에서 서로 같음을 단언한다.
 * ⚠ 화면 글자를 **새로 만들지 않는다** — 기대 문자열은 전부 정본에 이미 있는 것이다.
 */
// @ts-expect-error — 타입 선언 없이 런타임만 쓴다(`design-fix-20260908` 과 같은 규율).
import { readFileSync } from 'node:fs';
// @ts-expect-error — 같은 이유.
import { resolve } from 'node:path';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { PreviewPanel } from '../src/components/upload/PreviewPanel';
import type { PreviewSource, RenderJob } from '../src/components/upload/types';
import { PREVIEW_SLOT_STATES } from '../src/components/preview/PreviewSlot';
import { DatasetPreviewSection } from '../src/components/datasetpreview/DatasetPreviewSection';
import type { DatasetPreviewSource } from '../src/components/datasetpreview/types';

declare const process: { cwd(): string };

const UPLOAD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0UP1';
const RENDER_ID = '01JYZ9K7WQ3N8V4M2X6C5B0RE1';
const WAIT = { timeout: 5000 };

/** 진행 3단계 — 계약 `RenderStage` 값 그대로(정본 §8). 여기서 다시 쓰지 않는다. */
const STAGES = ['파일 읽는 중', '지도 그리는 중', '범례 만드는 중'] as const;

const CSS = String(
  readFileSync(resolve(process.cwd(), 'src/components/preview/preview.css'), 'utf8'),
).replace(/\/\*[\s\S]*?\*\//g, '');

function block(css: string, selector: string): string {
  const at = css.indexOf(selector);
  expect(at, `선택자 부재: ${selector}`).toBeGreaterThan(-1);
  const open = css.indexOf('{', at);
  return css.slice(open, css.indexOf('}', open));
}

function drawingJob(stage: string): RenderJob {
  return { renderId: RENDER_ID, status: '그리는 중', stage } as unknown as RenderJob;
}

const DONE_JOB = {
  renderId: RENDER_ID,
  status: '완료',
  result: {
    imageUrl: 'https://viz.example/p/map.png',
    legend: { palette: 'viridis', classes: [{ color: '#440154', min: 0, max: 5 }] },
  },
} as unknown as RenderJob;

const FAILED_JOB = {
  renderId: RENDER_ID,
  status: '실패',
  failure: { code: 'RENDER_FAILED', message: '지금 미리보기를 만들 수 없어요. 잠시 뒤 다시 시도해 주세요.' },
} as unknown as RenderJob;

/** 네 상태를 한 화면에서 차례로 밟게 하는 원천 — 조회 응답을 순서대로 돌려준다. */
function sequenceSource(jobs: RenderJob[]): PreviewSource {
  let i = 0;
  return {
    palettes: vi.fn(async () => [{ palette: 'viridis', label: '비리디스' }]),
    createRender: vi.fn(async () => jobs[0] as RenderJob),
    getRender: vi.fn(async () => {
      const job = jobs[Math.min(i, jobs.length - 1)] as RenderJob;
      i += 1;
      return job;
    }),
  } as unknown as PreviewSource;
}

function slotBox() {
  const el = screen.getByTestId('up-preview-slot');
  const rect = el.getBoundingClientRect();
  return { cls: el.className, ratio: el.getAttribute('data-preview-slot'), w: rect.width, h: rect.height };
}

describe('WU-C1 ⑴ — 파일을 고른 직후 4:3 틀이 이미 서 있다', () => {
  it('그리기를 누르기 전에 틀이 있다', async () => {
    render(<PreviewPanel source={sequenceSource([DONE_JOB])} uploadId={UPLOAD_ID} hasReferenceGrid />);
    const slot = await screen.findByTestId('up-preview-slot');
    expect(slot.className).toContain('pv-frame');
    expect(slot.getAttribute('data-preview-slot')).toBe('4x3');
    // 아직 그리지 않은 상태다 — 안쪽은 정본 문구 그대로다(문면 신설 0).
    expect(slot.textContent).toContain('아직 그리지 않았어요');
  });

  it('비율은 CSS 한 자리(토큰)에서 온다 — 4 / 3', () => {
    expect(block(CSS, ':root')).toContain('--pv-frame-ratio: 4 / 3');
    expect(block(CSS, '.pv-frame {')).toContain('aspect-ratio: var(--pv-frame-ratio)');
  });

  it('그림은 틀 안에 맞춘다 — 찌그러뜨리지 않는다', () => {
    expect(CSS).toContain('object-fit: contain');
  });
});

describe('WU-C1 ⑵ — idle→drawing→done→failed 네 상태에서 바깥 치수 불변', () => {
  it('상태 목록은 정확히 네 값이다 (대상 0건이 아님)', () => {
    expect(PREVIEW_SLOT_STATES.length).toBe(4);
    expect([...PREVIEW_SLOT_STATES]).toEqual(['idle', 'drawing', 'done', 'failed']);
  });

  it('네 상태를 밟는 동안 틀의 상자가 바뀌지 않는다', async () => {
    const boxes: Array<ReturnType<typeof slotBox>> = [];
    const view = render(
      <PreviewPanel
        source={sequenceSource([drawingJob('파일 읽는 중'), DONE_JOB])}
        uploadId={UPLOAD_ID}
        hasReferenceGrid
      />,
    );
    await screen.findByTestId('up-preview-draw');
    boxes.push(slotBox()); // ① idle
    expect(screen.getByTestId('up-preview-slot').getAttribute('data-preview-slot-state')).toBe('idle');

    fireEvent.click(screen.getByTestId('up-preview-draw'));
    await screen.findByTestId('up-preview-stage');
    boxes.push(slotBox()); // ② drawing

    await waitFor(() => expect(screen.getByTestId('up-preview-image')).toBeTruthy(), WAIT);
    boxes.push(slotBox()); // ③ done
    expect(screen.getByTestId('up-preview-slot').getAttribute('data-preview-slot-state')).toBe('done');

    view.unmount();
    render(
      <PreviewPanel source={sequenceSource([FAILED_JOB])} uploadId={UPLOAD_ID} hasReferenceGrid />,
    );
    fireEvent.click(await screen.findByTestId('up-preview-draw'));
    await waitFor(() => expect(screen.getByTestId('up-preview-error')).toBeTruthy(), WAIT);
    boxes.push(slotBox()); // ④ failed
    expect(screen.getByTestId('up-preview-slot').getAttribute('data-preview-slot-state')).toBe('failed');

    // **네 상태를 실제로 밟았다** — 건수를 단언한다(green-by-skip 방지).
    expect(boxes.length).toBe(PREVIEW_SLOT_STATES.length);
    for (const b of boxes) {
      expect(b.cls).toBe(boxes[0]?.cls);
      expect(b.ratio).toBe('4x3');
      expect(b.w).toBe(boxes[0]?.w);
      expect(b.h).toBe(boxes[0]?.h);
    }
  });

  it('실패해도 틀이 접히지 않고 `UNAVAILABLE` 문면이 그 안에 뜬다', async () => {
    render(<PreviewPanel source={sequenceSource([FAILED_JOB])} uploadId={UPLOAD_ID} hasReferenceGrid />);
    fireEvent.click(await screen.findByTestId('up-preview-draw'));
    const err = await screen.findByTestId('up-preview-error');
    expect(err.textContent).toContain('지금 미리보기를 만들 수 없어요.');
    expect(screen.getByTestId('up-preview-slot').contains(err)).toBe(true);
  });
});

describe('WU-C1 ⑶ — 진행 3단계 문면과 표식이 그대로다', () => {
  it('세 문구가 순서대로 `up-preview-stage` 안에 뜬다', async () => {
    render(
      <PreviewPanel
        source={sequenceSource(STAGES.map((s) => drawingJob(s)))}
        uploadId={UPLOAD_ID}
        hasReferenceGrid
      />,
    );
    fireEvent.click(await screen.findByTestId('up-preview-draw'));
    const seen: string[] = [];
    for (const stage of STAGES) {
      await waitFor(
        () => expect(screen.getByTestId('up-preview-stage').textContent).toContain(stage),
        WAIT,
      );
      seen.push(stage);
      // 단계 표시는 **틀 안**에 있다 — 틀 밖으로 나가면 자리 선점이 깨진다.
      expect(
        screen.getByTestId('up-preview-slot').contains(screen.getByTestId('up-preview-stage')),
      ).toBe(true);
    }
    expect(seen).toEqual([...STAGES]);
  });
});

describe('WU-C1 ⑷ — 상세는 열자마자 같은 틀이 선다', () => {
  it('`시작하는 중` 에도 틀이 있다', async () => {
    // 렌더 시작이 끝나지 않게 잡아 둔다 — `시작함` 이전 시점을 그대로 본다.
    const source = {
      palettes: vi.fn(async () => [{ palette: 'viridis' }]),
      create: vi.fn(() => new Promise<RenderJob>(() => {})),
      get: vi.fn(async () => DONE_JOB),
      probeTile: vi.fn(async () => 'ok' as const),
      mapGeometry: vi.fn(async () => undefined),
      lookupValue: vi.fn(async () => {
        throw new Error('이 시험은 값 조회를 부르지 않는다');
      }),
      screenshot: vi.fn(async () => new Blob([new Uint8Array([1])], { type: 'image/png' })),
    } as unknown as DatasetPreviewSource;

    render(<DatasetPreviewSection datasetId="01JYZ9K7WQ3N8V4M2X6C5B0AA1" source={source} />);
    const slot = await screen.findByTestId('dt-preview-slot');
    expect(slot.className).toContain('pv-frame');
    expect(slot.getAttribute('data-preview-slot')).toBe('4x3');
    expect(slot.getAttribute('data-preview-slot-state')).toBe('drawing');
  });
});
