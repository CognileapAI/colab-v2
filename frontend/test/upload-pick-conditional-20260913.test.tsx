/**
 * 레인 A3 — 업로드 모달 좌측 미리보기의 「변수」·「시각」 고르개는 **후보가 둘 이상일 때만** 선다.
 *
 * 오라클 = 기획서 rev2(업로드 좌측은 「첫 변수·기간 평균 한 장」이고 변수·시각 선택을 그리지
 *          않는다) ＋ 사용자 결정(다변수·다시각일 때만 표시).
 *
 * ⚠ 이 예외는 **업로드 인라인 한 자리뿐**이다 — 데이터셋 상세·확장보기 오버레이는
 *   `PreviewPickRow` 머릿말 규율(세 고르개는 후보가 없어도 자리를 지킨다 · disabled) 그대로다.
 *   그 무변을 이 파일이 함께 잰다 — 한쪽만 재면 예외가 조용히 세 화면으로 번진다.
 */
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { PreviewPanel } from '../src/components/upload/PreviewPanel';
import { clickPreviewDrawWhenReady } from './helpers/previewDraw';
import type { PreviewSource, RenderJob } from '../src/components/upload/types';
import { DatasetPreviewSection } from '../src/components/datasetpreview/DatasetPreviewSection';
import type { DatasetPreviewSource } from '../src/components/datasetpreview/types';
import type { PreviewPiece, TargetDescription } from '../src/components/preview/pick';

const UPLOAD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0UP1';
const DATASET_ID = '01JYZ9K7WQ3N8V4M2X6C5B0DS1';
const RENDER_ID = '01JYZ9K7WQ3N8V4M2X6C5B0RE1';
const PIECE_A = '01JYZ9K7WQ3N8V4M2X6C5B0F01';
const PIECE_B = '01JYZ9K7WQ3N8V4M2X6C5B0F02';
const T0 = '2024-01-01T00:00:00Z';
const T1 = '2024-01-01T01:00:00Z';
const WAIT = { timeout: 5000 };

const PIECES: PreviewPiece[] = [
  { fileId: PIECE_A, fileName: 'hsr_2024_01.nc', renderable: true },
  { fileId: PIECE_B, fileName: 'hsr_2024_02.nc', renderable: true },
];

/** 다변수·다시각 — 고를 것이 실제로 있다. */
const MANY: TargetDescription = {
  variables: ['rainfall', 'temperature'],
  instants: { count: 2, first: T0, last: T1 },
  default: { variable: 'rainfall', instant: T0 },
};

/** 단일 변수·단일 시각 — 고를 것이 없다(변수 1 · `count` 1). */
const SINGLE: TargetDescription = {
  variables: ['rainfall'],
  instants: { count: 1, first: T0, last: T0 },
  default: { variable: 'rainfall', instant: T0 },
};

/** 시각 축 자체가 없는 대상 — 계약 축자 「없으면 `null` 이다」. */
const NO_INSTANT: TargetDescription = {
  variables: ['rainfall', 'temperature'],
  instants: null,
  default: { variable: 'rainfall', instant: null },
};

function doneJob(): RenderJob {
  return {
    renderId: RENDER_ID,
    status: '완료',
    result: {
      imageUrl: 'https://viz.example/p/map.png',
      legend: {
        palette: 'viridis',
        variable: 'rainfall',
        classes: [{ color: '#440154', min: 0, max: 5 }],
      },
    },
  } as unknown as RenderJob;
}

function uploadSource(description: TargetDescription) {
  const job = doneJob();
  return {
    palettes: vi.fn(async () => [{ palette: 'viridis', label: '비리디스' }]),
    createRender: vi.fn(async () => job),
    getRender: vi.fn(async () => job),
    files: vi.fn(async () => PIECES),
    describe: vi.fn(async () => description),
  } as unknown as PreviewSource & { describe: ReturnType<typeof vi.fn> };
}

function detailSource(description: TargetDescription) {
  const job = doneJob();
  return {
    palettes: vi.fn(async () => [{ palette: 'viridis' }]),
    create: vi.fn(async () => job),
    get: vi.fn(async () => job),
    probeTile: vi.fn(async () => 'ok' as const),
    mapGeometry: vi.fn(async () => undefined),
    screenshot: vi.fn(async () => new Blob()),
    lookupValue: vi.fn(async () => ({}) as never),
    files: vi.fn(async () => PIECES),
    describe: vi.fn(async () => description),
  } as unknown as DatasetPreviewSource & { describe: ReturnType<typeof vi.fn> };
}

/**
 * 업로드 화면을 세우고 **describe 회신이 화면에 실릴 때까지** 기다린다.
 * ⚠ 「호출됐다」까지만 기다리면 조회 **전** 상태(변수 0·시각 0)를 「고를 것이 하나뿐이다」로
 *   오인해 통과가 난다 — 회신 약속을 `act` 안에서 끝까지 기다려 그 갈래를 닫는다.
 */
async function mountUpload(description: TargetDescription) {
  const source = uploadSource(description);
  render(<PreviewPanel source={source} uploadId={UPLOAD_ID} hasReferenceGrid />);
  await waitFor(() => expect(source.describe).toHaveBeenCalled(), WAIT);
  await act(async () => {
    await source.describe.mock.results[0]?.value;
  });
  await screen.findByTestId('up-pick-row', undefined, WAIT);
  return source;
}

describe('업로드 인라인 — 고를 것이 하나뿐이면 변수·시각 고르개를 그리지 않는다', () => {
  it('단일 변수·단일 시각 → 변수·시각 고르개 부재 · 파일 고르개는 존재', async () => {
    await mountUpload(SINGLE);
    expect(screen.queryByTestId('up-pick-variable')).toBeNull();
    expect(screen.queryByTestId('up-pick-instant')).toBeNull();
    expect(screen.getByTestId('up-pick-file')).toBeTruthy();
    // **건수가 오라클이다** — 남는 고르개는 파일 하나뿐이다.
    expect(screen.getByTestId('up-pick-row').querySelectorAll('select').length).toBe(1);
  });

  it('시각 축이 없는 대상(`instants: null`) → 시각 고르개 부재 · 변수 고르개는 존재', async () => {
    await mountUpload(NO_INSTANT);
    expect(screen.queryByTestId('up-pick-instant')).toBeNull();
    expect(screen.getByTestId('up-pick-variable')).toBeTruthy();
    expect(screen.getByTestId('up-pick-row').querySelectorAll('select').length).toBe(2);
  });

  it('다변수·다시각 → 세 고르개가 모두 선다', async () => {
    await mountUpload(MANY);
    expect(screen.getByTestId('up-pick-variable')).toBeTruthy();
    expect(screen.getByTestId('up-pick-instant')).toBeTruthy();
    expect(screen.getByTestId('up-pick-row').querySelectorAll('select').length).toBe(3);
  });
});

describe('예외는 업로드 인라인 한 자리뿐이다 — 나머지 두 자리는 무변', () => {
  it('데이터셋 상세는 단일 변수·단일 시각에서도 세 고르개를 유지한다(disabled 존치)', async () => {
    const source = detailSource(SINGLE);
    render(<DatasetPreviewSection datasetId={DATASET_ID} source={source} pollMs={100000} />);
    await waitFor(() => expect(source.describe).toHaveBeenCalled(), WAIT);
    const row = await screen.findByTestId('dt-pick-row', undefined, WAIT);
    await waitFor(() => expect(row.querySelectorAll('select').length).toBe(3), WAIT);
    expect(screen.getByTestId('dt-pick-variable')).toBeTruthy();
    expect(screen.getByTestId('dt-pick-instant')).toBeTruthy();
  });

  it('확장보기 오버레이는 단일 변수·단일 시각에서도 세 고르개를 유지한다', async () => {
    await mountUpload(SINGLE);
    await clickPreviewDrawWhenReady({ wait: WAIT });
    await waitFor(() => expect(screen.getByTestId('up-preview-image')).toBeTruthy(), WAIT);
    fireEvent.click(screen.getByTestId('pv-expand'));
    await screen.findByTestId('pv-expand-body', undefined, WAIT);
    const row = screen.getByTestId('pvx-pick-row');
    expect(row.querySelectorAll('select').length).toBe(3);
    expect(screen.getByTestId('pvx-pick-variable')).toBeTruthy();
    expect(screen.getByTestId('pvx-pick-instant')).toBeTruthy();
  });
});
