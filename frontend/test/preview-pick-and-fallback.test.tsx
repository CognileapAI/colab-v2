/**
 * WU-C3 — **500MB 조각 폴백 ＋ 파일·변수·시각 고르개** (축 ①-③④).
 *
 * **red 를 먼저 봤다** (2026-09-08 · 이 파일을 세우기 전):
 *  ⑴ `createRender` 는 413 을 일반 실패로 접었다 — 조각 폴백이 **없었다**(호출 1회에서 끝).
 *  ⑵ 두 화면 어디에도 파일·변수·시각 고르개가 **0개**였고 `fileIds`·`variable`·`instant`
 *     가 요청에 실린 적이 없다(`PreviewPanel.tsx:140-144` 실측 · 계약은 이미 받고 있었다).
 *  ⑶ describe(`POST /preview-target-descriptions`)를 부르는 화면이 **0곳**이었다.
 *
 * 오라클은 **건수**다(green-by-skip 방지) — 화면 2벌 · 고르개 3개 · `createRender` 2회 ·
 * `fileIds` 길이 1 · describe 배열 길이 ≥ 1.
 *
 * ⚠ 폴백 문면은 **새 문장이 아니다** — viz-render `TOO_LARGE_MESSAGE` 의 **둘째 문장**이고
 *   조각 이름은 그 옆에 **값으로** 선다(`preview/pick.ts` 주석).
 */
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { PreviewPanel } from '../src/components/upload/PreviewPanel';
import type { PreviewSource as UploadPreviewSource } from '../src/components/upload/types';
import { DatasetPreviewSection } from '../src/components/datasetpreview/DatasetPreviewSection';
import type { DatasetPreviewSource } from '../src/components/datasetpreview/types';
import {
  RenderTooLarge,
  TOO_LARGE_SECOND_SENTENCE,
  type PreviewPiece,
  type TargetDescription,
} from '../src/components/preview/pick';

const UPLOAD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0UP1';
const DATASET_ID = '01JYZ9K7WQ3N8V4M2X6C5B0DS1';
const RENDER_ID = '01JYZ9K7WQ3N8V4M2X6C5B0RE1';

const PIECE_A = '01JYZ9K7WQ3N8V4M2X6C5B0F01';
const PIECE_B = '01JYZ9K7WQ3N8V4M2X6C5B0F02';
const GRID_FILE = '01JYZ9K7WQ3N8V4M2X6C5B0F03';

const WAIT = { timeout: 5000 };

/** 조각 픽스처 — 본체 둘 ＋ 기준 격자 파일 하나(그리는 대상이 아니다). */
const PIECES: PreviewPiece[] = [
  { fileId: PIECE_A, fileName: 'hsr_2024_01.nc', renderable: true },
  { fileId: PIECE_B, fileName: 'hsr_2024_02.nc', renderable: true },
  { fileId: GRID_FILE, fileName: 'latlon.bin', renderable: false },
];

/** describe 픽스처 — `TargetDescription` 그대로. **배열 길이 ≥ 1 이 오라클이다.** */
const DESCRIBE: TargetDescription = {
  variables: ['rainfall', 'temperature'],
  instants: { count: 24, first: '2024-01-01T00:00:00Z', last: '2024-01-01T23:00:00Z' },
  default: { variable: 'rainfall', instant: '2024-01-01T00:00:00Z' },
};

function drawingJob(renderId = RENDER_ID) {
  return { renderId, status: '그리는 중', stage: '지도 그리는 중' } as never;
}

/** 요청 인자에서 조각 목록을 꺼낸다 — 업로드는 `target.fileIds`, 상세는 입력 평면이다. */
function fileIdsOf(arg: unknown): string[] | undefined {
  const a = arg as { target?: { fileIds?: string[] }; fileIds?: string[] };
  return a.target?.fileIds ?? a.fileIds;
}

function variableOf(arg: unknown): string | undefined {
  return (arg as { variable?: string }).variable;
}

function instantOf(arg: unknown): string | undefined {
  return (arg as { instant?: string }).instant;
}

/** 업로드(S-04) 화면의 출처 — 첫 `createRender` 만 413 이다. */
function uploadSource(opts: { tooLargeFirst: boolean }) {
  let created = 0;
  return {
    palettes: vi.fn(async () => [{ palette: 'viridis', label: '비리디스' }]),
    createRender: vi.fn(async () => {
      created += 1;
      if (opts.tooLargeFirst && created === 1) throw new RenderTooLarge();
      return drawingJob();
    }),
    getRender: vi.fn(async () => drawingJob()),
    files: vi.fn(async () => PIECES),
    describe: vi.fn(async () => DESCRIBE),
  } as unknown as UploadPreviewSource & {
    createRender: ReturnType<typeof vi.fn>;
    files: ReturnType<typeof vi.fn>;
    describe: ReturnType<typeof vi.fn>;
  };
}

/** 상세(S-05) 화면의 출처 — 같은 사실을 상세의 포트 모양으로 준다. */
function detailSource(opts: { tooLargeFirst: boolean }) {
  let created = 0;
  return {
    palettes: vi.fn(async () => [{ palette: 'viridis' }]),
    create: vi.fn(async () => {
      created += 1;
      if (opts.tooLargeFirst && created === 1) throw new RenderTooLarge();
      return drawingJob();
    }),
    get: vi.fn(async () => drawingJob()),
    probeTile: vi.fn(async () => 'ok' as const),
    mapGeometry: vi.fn(async () => undefined),
    screenshot: vi.fn(async () => new Blob()),
    lookupValue: vi.fn(async () => ({}) as never),
    files: vi.fn(async () => PIECES),
    describe: vi.fn(async () => DESCRIBE),
  } as unknown as DatasetPreviewSource & {
    create: ReturnType<typeof vi.fn>;
    files: ReturnType<typeof vi.fn>;
    describe: ReturnType<typeof vi.fn>;
  };
}

/**
 * 화면 둘을 **같은 표로 돈다** — 판정이 「업로드·상세 양쪽」이라 한쪽만 green 이면 미달이다.
 * `SCREENS.length` 자체가 오라클이다(2).
 */
const SCREENS = [
  {
    name: '업로드(S-04)',
    prefix: 'up',
    make: uploadSource,
    /** 업로드는 사람이 「미리보기 그리기」를 눌러야 그린다. */
    async start(source: ReturnType<typeof uploadSource>) {
      render(<PreviewPanel source={source} uploadId={UPLOAD_ID} hasReferenceGrid />);
      const draw = await screen.findByTestId('up-preview-draw');
      await waitFor(() => expect(source.describe).toHaveBeenCalled(), WAIT);
      fireEvent.click(draw);
    },
    renderSpy: (s: ReturnType<typeof uploadSource>) => s.createRender,
  },
  {
    name: '상세(S-05)',
    prefix: 'dt',
    make: detailSource,
    /** 상세는 **열자마자** 그린다. */
    async start(source: ReturnType<typeof detailSource>) {
      render(<DatasetPreviewSection datasetId={DATASET_ID} source={source} pollMs={100000} />);
    },
    renderSpy: (s: ReturnType<typeof detailSource>) => s.create,
  },
] as const;

describe('WU-C3 — 화면 2벌이 같은 규약을 쓴다', () => {
  it('시험이 도는 화면은 업로드·상세 둘이다', () => {
    expect(SCREENS.length).toBe(2);
  });

  it('describe 픽스처의 변수 배열은 비어 있지 않다', () => {
    // 계약 산문 축자 — 「비어 있지 않다 — 하나도 없으면 그건 415 이지 빈 목록이 아니다」
    expect(DESCRIBE.variables.length).toBeGreaterThanOrEqual(1);
  });
});

describe.each(SCREENS)('WU-C3 · $name', (sc) => {
  it('413 이면 조각 목록을 한 번 묻고 첫 renderable 조각으로 다시 그린다', async () => {
    const source = sc.make({ tooLargeFirst: true }) as never;
    await sc.start(source);
    const spy = sc.renderSpy(source as never);

    // 상한을 유지한 채 **첫 renderable 조각으로 자동 재요청**한다 — 호출은 정확히 2회다.
    await waitFor(() => expect(spy.mock.calls.length).toBe(2), WAIT);
    expect((source as { files: { mock: { calls: unknown[] } } }).files.mock.calls.length).toBe(1);

    const second = spy.mock.calls[1]?.[0];
    expect(fileIdsOf(second)?.length).toBe(1);
    // 기준 격자 파일이 아니라 **첫 본체 조각**이다.
    expect(fileIdsOf(second)?.[0]).toBe(PIECE_A);

    // 문면은 `TOO_LARGE_MESSAGE` 둘째 문장 ＋ 조각 이름이다. **새 문장이 없다.**
    const notice = await screen.findByTestId(`${sc.prefix}-piece-notice`, undefined, WAIT);
    expect(notice.textContent).toContain(TOO_LARGE_SECOND_SENTENCE);
    expect(within(notice).getByTestId(`${sc.prefix}-piece-name`).textContent).toBe(
      'hsr_2024_01.nc',
    );
  });

  it('고르개는 파일·변수·시각 셋이고 기본값은 describe 가 준 값이다', async () => {
    const source = sc.make({ tooLargeFirst: false }) as never;
    await sc.start(source);

    const row = await screen.findByTestId(`${sc.prefix}-pick-row`, undefined, WAIT);
    // **건수가 오라클이다** — 하나라도 빠지면 red.
    expect(row.querySelectorAll('select').length).toBe(3);

    const variable = screen.getByTestId(`${sc.prefix}-pick-variable`) as HTMLSelectElement;
    const instant = screen.getByTestId(`${sc.prefix}-pick-instant`) as HTMLSelectElement;
    await waitFor(() => expect(variable.value).toBe(DESCRIBE.default.variable), WAIT);
    expect(instant.value).toBe(DESCRIBE.default.instant);
    // 시각 후보는 **처음과 마지막 둘**이다(계약이 목록을 주지 않는다 · ⓐ).
    expect(instant.querySelectorAll('option').length).toBe(2);
  });

  it('변수를 바꾸면 `variable` 을 실어 다시 그린다', async () => {
    const source = sc.make({ tooLargeFirst: false }) as never;
    await sc.start(source);
    const spy = sc.renderSpy(source as never);
    await waitFor(() => expect(spy.mock.calls.length).toBe(1), WAIT);

    fireEvent.change(await screen.findByTestId(`${sc.prefix}-pick-variable`), {
      target: { value: 'temperature' },
    });

    await waitFor(() => expect(spy.mock.calls.length).toBe(2), WAIT);
    const arg = spy.mock.calls[1]?.[0];
    expect(variableOf(arg)).toBe('temperature');
    // 한 번에 값 하나 — 시각은 실리지 않는다(겹쳐 그리기 0).
    expect(instantOf(arg)).toBeUndefined();
  });

  it('시각을 바꾸면 `instant` 를 실어 다시 그린다', async () => {
    const source = sc.make({ tooLargeFirst: false }) as never;
    await sc.start(source);
    const spy = sc.renderSpy(source as never);
    await waitFor(() => expect(spy.mock.calls.length).toBe(1), WAIT);

    fireEvent.change(await screen.findByTestId(`${sc.prefix}-pick-instant`), {
      target: { value: DESCRIBE.instants!.last },
    });

    await waitFor(() => expect(spy.mock.calls.length).toBe(2), WAIT);
    expect(instantOf(spy.mock.calls[1]?.[0])).toBe(DESCRIBE.instants!.last);
  });

  it('파일을 바꾸면 `fileIds` 하나를 실어 다시 그린다', async () => {
    const source = sc.make({ tooLargeFirst: false }) as never;
    await sc.start(source);
    const spy = sc.renderSpy(source as never);
    await waitFor(() => expect(spy.mock.calls.length).toBe(1), WAIT);

    fireEvent.change(await screen.findByTestId(`${sc.prefix}-pick-file`), {
      target: { value: PIECE_B },
    });

    await waitFor(() => expect(spy.mock.calls.length).toBe(2), WAIT);
    expect(fileIdsOf(spy.mock.calls[1]?.[0])).toEqual([PIECE_B]);
  });
});
