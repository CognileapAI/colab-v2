/**
 * R-BUGFIX-260912 L3b — 미리보기 조작 줄과 진행 표시 (spec v2 · 6단계).
 *
 * 오라클 = `dev-package/prd/specs/2026-09-12-issue-preview-controls-v2.md` §8-2 단언 목록
 *          ㈀ 1~4 · ㈁ 5~8 · ㈃ 10~13 · ㈅ 18~23. Ted 승인 2026-09-12 「모두 권고대로」.
 *
 * ⚠ **jsdom 은 레이아웃을 계산하지 않는다** — 배치 판정은 두 갈래로 세운다.
 *   ㈎ DOM 관계(`contains` · `compareDocumentPosition`) ㈏ CSS 원문 계측(주석 제거 뒤 존재 단언).
 *   선례 = `preview-slot-4x3.test.tsx` · `design-fix-20260908.test.ts` · `css-residual-rc11.test.ts`.
 * ⚠ 화면 글자를 새로 만들지 않는다 — 기대 문자열은 전부 이미 있는 정본 문면이다.
 */
// @ts-expect-error — 타입 선언 없이 런타임만 쓴다(`design-fix-20260908` 과 같은 규율).
import { readFileSync } from 'node:fs';
// @ts-expect-error — 같은 이유.
import { resolve } from 'node:path';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { PreviewPanel } from '../src/components/upload/PreviewPanel';
import type { PreviewSource, RenderJob } from '../src/components/upload/types';
import { DatasetPreviewSection } from '../src/components/datasetpreview/DatasetPreviewSection';
import { drawDatasetPreviewWhenReady } from './datasetPreviewTest';
import type { DatasetPreviewSource } from '../src/components/datasetpreview/types';
import type { PreviewPiece, TargetDescription } from '../src/components/preview/pick';

declare const process: { cwd(): string };

const UPLOAD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0UP1';
const DATASET_ID = '01JYZ9K7WQ3N8V4M2X6C5B0DS1';
const RENDER_ID = '01JYZ9K7WQ3N8V4M2X6C5B0RE1';
const PIECE_A = '01JYZ9K7WQ3N8V4M2X6C5B0F01';
const PIECE_B = '01JYZ9K7WQ3N8V4M2X6C5B0F02';
const WAIT = { timeout: 5000 };

/** 주석은 걷어내고 읽는다 — 주석 속 선택자·값이 계측에 섞이지 않도록. */
const read = (rel: string): string =>
  String(readFileSync(resolve(process.cwd(), rel), 'utf8')).replace(/\/\*[\s\S]*?\*\//g, '');

const PREVIEW_CSS = read('src/components/preview/preview.css');
const UPLOAD_CSS = read('src/components/upload/upload.css');

/** 선택자 하나의 선언 블록(`{ … }`)을 원문에서 잘라낸다. 부재면 그 자리에서 실패한다. */
function block(css: string, selector: string): string {
  const at = css.indexOf(selector);
  expect(at, `선택자 부재: ${selector}`).toBeGreaterThan(-1);
  const open = css.indexOf('{', at);
  return css.slice(open + 1, css.indexOf('}', open));
}

const PIECES: PreviewPiece[] = [
  { fileId: PIECE_A, fileName: 'hsr_2024_01.nc', renderable: true },
  { fileId: PIECE_B, fileName: 'hsr_2024_02.nc', renderable: true },
];

const DESCRIBE: TargetDescription = {
  variables: ['rainfall', 'temperature'],
  instants: { count: 2, first: '2024-01-01T00:00:00Z', last: '2024-01-01T01:00:00Z' },
  default: { variable: 'rainfall', instant: '2024-01-01T00:00:00Z' },
};

function doneJob(extra: Record<string, unknown> = {}): RenderJob {
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
      ...extra,
    },
  } as unknown as RenderJob;
}

/** 업로드(S-04) 출처 — 건네받은 작업 하나만 돌려준다. */
function uploadSource(job: RenderJob) {
  return {
    palettes: vi.fn(async () => [{ palette: 'viridis', label: '비리디스' }]),
    createRender: vi.fn(async () => job),
    getRender: vi.fn(async () => job),
    files: vi.fn(async () => PIECES),
    describe: vi.fn(async () => DESCRIBE),
  } as unknown as PreviewSource & {
    createRender: ReturnType<typeof vi.fn>;
    describe: ReturnType<typeof vi.fn>;
  };
}

const DRAWING_JOB = {
  renderId: RENDER_ID,
  status: '그리는 중',
  stage: '지도 그리는 중',
} as unknown as RenderJob;

/** 상세(S-05) 출처 — 같은 사실을 상세 포트 모양으로 준다. */
function detailSource(job: RenderJob) {
  return {
    palettes: vi.fn(async () => [{ palette: 'viridis' }]),
    create: vi.fn(async () => job),
    get: vi.fn(async () => job),
    probeTile: vi.fn(async () => 'ok' as const),
    mapGeometry: vi.fn(async () => undefined),
    screenshot: vi.fn(async () => new Blob()),
    lookupValue: vi.fn(async () => ({}) as never),
    files: vi.fn(async () => PIECES),
    describe: vi.fn(async () => DESCRIBE),
  } as unknown as DatasetPreviewSource;
}

/** 업로드 화면을 세우고 「미리보기 그리기」까지 밟는다. */
async function drawUpload(job: RenderJob) {
  const source = uploadSource(job);
  render(<PreviewPanel source={source} uploadId={UPLOAD_ID} hasReferenceGrid />);
  const draw = await screen.findByTestId('up-preview-draw');
  await waitFor(() => expect(source.describe).toHaveBeenCalled(), WAIT);
  fireEvent.click(draw);
  return source;
}

/** 「앞선 형제」 판정 — 같은 부모 ＋ 문서 순서에서 뒤에 온다. */
function precedes(first: Element, second: Element): boolean {
  return (
    first.parentElement === second.parentElement &&
    Boolean(first.compareDocumentPosition(second) & Node.DOCUMENT_POSITION_FOLLOWING)
  );
}

describe('㈀ 고르개 줄은 4:3 틀 밖 · 틀보다 앞선 형제다 — 업로드 인라인 (단계 ①)', () => {
  it('① 고르개 줄이 4:3 틀의 자손이 아니다', async () => {
    render(<PreviewPanel source={uploadSource(doneJob())} uploadId={UPLOAD_ID} hasReferenceGrid />);
    const pick = await screen.findByTestId('up-pick-row');
    expect(screen.getByTestId('up-preview-slot').contains(pick)).toBe(false);
  });

  it('② 고르개 줄이 4:3 틀보다 앞선 형제다', async () => {
    render(<PreviewPanel source={uploadSource(doneJob())} uploadId={UPLOAD_ID} hasReferenceGrid />);
    const pick = await screen.findByTestId('up-pick-row');
    expect(precedes(pick, screen.getByTestId('up-preview-slot'))).toBe(true);
  });

  it('④ 렌더 전·후로 고르개 줄의 부모가 같다 — 상태에 따라 자리가 갈리지 않는다', async () => {
    await drawUpload(doneJob());
    const before = (await screen.findByTestId('up-pick-row')).parentElement;
    await waitFor(() => expect(screen.getByTestId('up-preview-image')).toBeTruthy(), WAIT);
    expect(screen.getByTestId('up-pick-row').parentElement).toBe(before);
  });
});

/**
 * ⭑ **⟨2026-09-17 · #93⟩ 팔레트·구간 수·미리보기 그리기는 접힌 메뉴 밖에 선다.**
 * 기본 닫힘 `<details>` 안에 있으면 접기를 펼치기 전에는 **지도 표현을 바꾸는 수단의
 * 존재가 화면에 없다.** 옮기는 자리는 파일·변수 고르개 줄 **바로 아래** — 「무엇을
 * 그릴지 → 어떻게 그릴지」 순서다. ⚠ jsdom 은 `<details>` 안쪽도 DOM 에 두므로
 * **조회 성공만으로는 통과를 판정할 수 없다** — 실제 부모 노드와 접기 자손 여부를 잰다.
 */
describe('㈆ 팔레트·구간 수는 접힌 메뉴 밖 고르개 줄 컨테이너에 선다 — 업로드 (#93)', () => {
  const MOVED = ['up-style-palette', 'up-style-classcount', 'up-preview-draw'] as const;

  it('접기를 펼치지 않은 상태에서 세 조작이 모두 화면에 있다', async () => {
    render(<PreviewPanel source={uploadSource(doneJob())} uploadId={UPLOAD_ID} hasReferenceGrid />);
    await screen.findByTestId('up-preview-draw');
    // 접기는 손대지 않는다 — 기본 닫힘 그대로에서 잰다.
    expect((screen.getByTestId('up-preview-options') as HTMLDetailsElement).open).toBe(false);
    expect(MOVED).toHaveLength(3);
    for (const id of MOVED) expect(screen.getAllByTestId(id)).toHaveLength(1);
  });

  it('세 조작의 실제 부모가 틀 위 줄 컨테이너이고 접기의 자손이 아니다', async () => {
    render(<PreviewPanel source={uploadSource(doneJob())} uploadId={UPLOAD_ID} hasReferenceGrid />);
    await screen.findByTestId('up-preview-draw');
    const options = screen.getByTestId('up-preview-options');
    const wrap = (await screen.findByTestId('up-pick-row')).parentElement;
    expect(wrap?.className).toBe('pv-frame-wrap');
    for (const id of MOVED) {
      const el = screen.getByTestId(id);
      // 접기 자손 집합에 없다 — 「옮겼다」의 음성 단언.
      expect(options.contains(el)).toBe(false);
      // 묶음 하나로 옮기므로 조상이 컨테이너다.
      expect(wrap?.contains(el)).toBe(true);
    }
    // 묶음 자체의 **직계 부모**가 컨테이너다 — 중간에 새 껍데기를 두지 않는다.
    expect(screen.getByTestId('up-style-palette').closest('.vizsetup')?.parentElement).toBe(wrap);
  });

  it('파일·변수 고르개 줄보다 뒤에 놓인다 — 「무엇을 → 어떻게」 순서', async () => {
    render(<PreviewPanel source={uploadSource(doneJob())} uploadId={UPLOAD_ID} hasReferenceGrid />);
    await screen.findByTestId('up-preview-draw');
    const pick = screen.getByTestId('up-pick-row');
    const viz = screen.getByTestId('up-style-palette').closest('.vizsetup') as Element;
    expect(precedes(pick, viz)).toBe(true);
    // 틀보다는 앞이다 — 조작부가 4:3 틀 안 스크롤에 실리지 않는다.
    expect(precedes(viz, screen.getByTestId('up-preview-slot'))).toBe(true);
  });

  it('대표 그림 고르개와 접기는 그대로 접힌 채 남는다', async () => {
    render(<PreviewPanel source={uploadSource(doneJob())} uploadId={UPLOAD_ID} hasReferenceGrid />);
    await screen.findByTestId('up-preview-draw');
    const options = screen.getByTestId('up-preview-options');
    expect((options as HTMLDetailsElement).open).toBe(false);
    expect(options.contains(screen.getByTestId('up-thumb-block'))).toBe(true);
  });

  it('옮긴 뒤에도 팔레트·구간 수를 바꿔 그리면 같은 요청이 한 번 더 돈다', async () => {
    const source = uploadSource(doneJob());
    render(<PreviewPanel source={source} uploadId={UPLOAD_ID} hasReferenceGrid />);
    const draw = await screen.findByTestId('up-preview-draw');
    await waitFor(() => expect(source.describe).toHaveBeenCalled(), WAIT);
    fireEvent.click(draw);
    await waitFor(() => expect(source.createRender).toHaveBeenCalledTimes(1), WAIT);

    fireEvent.change(screen.getByTestId('up-style-classcount'), { target: { value: '7' } });
    fireEvent.click(screen.getByTestId('up-preview-draw'));
    await waitFor(() => expect(source.createRender).toHaveBeenCalledTimes(2), WAIT);
    expect(source.createRender).toHaveBeenLastCalledWith(
      expect.objectContaining({ style: { palette: 'viridis', classCount: 7 } }),
    );
  });

  it('옮긴 뒤 죽는 접기 자손 전제 여백 규칙이 남아 있지 않다', () => {
    expect(UPLOAD_CSS.indexOf('.up-preview-options .vizsetup')).toBe(-1);
    // 글자 크기는 상속에 기대지 않는다 — 묶음 자신이 13px 을 명시한다(우려 #4).
    expect(block(UPLOAD_CSS, '.vizsetup .vs-f {')).toContain('font-size:13px');
  });

  it('idle 안내가 없는 조작을 안내하지 않는다 — 「설정을 열어」 절이 빠진다', async () => {
    const source = uploadSource(doneJob());
    render(<PreviewPanel source={source} uploadId={UPLOAD_ID} hasReferenceGrid />);
    await screen.findByTestId('up-preview-draw');
    const ph = document.querySelector('.vizph') as HTMLElement;
    expect(ph).toBeTruthy();
    expect(ph.textContent).toContain('아직 그리지 않았어요');
    expect(ph.textContent).toContain('팔레트와 구간 수를 고르고 미리보기 그리기를 눌러 주세요');
    expect(ph.textContent).not.toContain('미리보기 설정을 열어');
  });
});

describe('㈀ 고르개 줄은 4:3 틀 밖 · 틀보다 앞선 형제다 — 데이터셋 상세 (단계 ②)', () => {
  it('③ 상세 고르개 줄이 4:3 틀의 자손이 아니고 앞선 형제다', async () => {
    render(<DatasetPreviewSection datasetId={DATASET_ID} source={detailSource(DRAWING_JOB)} pollMs={100000} />);
    const pick = await screen.findByTestId('dt-pick-row');
    const slot = screen.getByTestId('dt-preview-slot');
    expect(slot.contains(pick)).toBe(false);
    expect(precedes(pick, slot)).toBe(true);
  });

  it('④ 상세도 렌더 전·후로 고르개 줄의 부모가 같다', async () => {
    render(<DatasetPreviewSection datasetId={DATASET_ID} source={detailSource(doneJob())} pollMs={100000} />);
    drawDatasetPreviewWhenReady();
    const before = (await screen.findByTestId('dt-pick-row')).parentElement;
    await waitFor(() => expect(screen.getByTestId('preview-viewport')).toBeTruthy(), WAIT);
    expect(screen.getByTestId('dt-pick-row').parentElement).toBe(before);
  });

  it('두 화면의 고르개 줄이 같은 이음매(틀 위 줄 컨테이너)에 선다', async () => {
    render(<PreviewPanel source={uploadSource(doneJob())} uploadId={UPLOAD_ID} hasReferenceGrid />);
    const upParent = (await screen.findByTestId('up-pick-row')).parentElement;
    render(<DatasetPreviewSection datasetId={DATASET_ID} source={detailSource(DRAWING_JOB)} pollMs={100000} />);
    const dtParent = (await screen.findByTestId('dt-pick-row')).parentElement;
    expect(upParent?.className).toBe('pv-frame-wrap');
    expect(dtParent?.className).toBe('pv-frame-wrap');
  });
});

/** 확장보기를 실제로 연다 — 닫힌 상태의 `queryBy…` 가 null 인 것을 통과로 세지 않는다(§8-6 ⑷). */
async function openExpand(): Promise<HTMLElement> {
  fireEvent.click(screen.getByTestId('pv-expand'));
  return screen.findByTestId('pv-expand-body');
}

describe('㈁ 확장보기 — 고르개 신설과 선택 상태 공유 (단계 ③)', () => {
  it('5 확장보기 본문이 고르개 줄 하나를 포함한다', async () => {
    await drawUpload(doneJob());
    await waitFor(() => expect(screen.getByTestId('up-preview-image')).toBeTruthy(), WAIT);
    const body = await openExpand();
    expect(body.contains(screen.getByTestId('pvx-pick-row'))).toBe(true);
    expect(screen.getAllByTestId('pvx-pick-row').length).toBe(1);
  });

  it('6 오버레이 고르개의 DOM id 가 인라인의 것과 겹치지 않는다', async () => {
    await drawUpload(doneJob());
    await waitFor(() => expect(screen.getByTestId('up-preview-image')).toBeTruthy(), WAIT);
    await openExpand();
    for (const axis of ['file', 'variable', 'instant']) {
      const inline = screen.getByTestId(`up-pick-${axis}`);
      const overlay = screen.getByTestId(`pvx-pick-${axis}`);
      expect(inline.id).toBe(`up-pick-${axis}`);
      expect(overlay.id).toBe(`pvx-pick-${axis}`);
      expect(overlay.id).not.toBe(inline.id);
    }
  });

  it('7 오버레이에서 변수를 바꾸면 인라인 고르개의 표시값도 같이 바뀐다', async () => {
    await drawUpload(doneJob());
    await waitFor(() => expect(screen.getByTestId('up-preview-image')).toBeTruthy(), WAIT);
    await openExpand();
    const inline = screen.getByTestId('up-pick-variable') as HTMLSelectElement;
    expect(inline.value).toBe('rainfall');
    fireEvent.change(screen.getByTestId('pvx-pick-variable'), { target: { value: 'temperature' } });
    await waitFor(() => expect(inline.value).toBe('temperature'), WAIT);
  });

  it('8 오버레이 고르개를 바꾸면 바꿔 그리기가 한 번 더 돈다', async () => {
    const source = await drawUpload(doneJob());
    await waitFor(() => expect(screen.getByTestId('up-preview-image')).toBeTruthy(), WAIT);
    await openExpand();
    expect(source.createRender).toHaveBeenCalledTimes(1);
    fireEvent.change(screen.getByTestId('pvx-pick-variable'), { target: { value: 'temperature' } });
    await waitFor(() => expect(source.createRender).toHaveBeenCalledTimes(2), WAIT);
    expect(source.createRender.mock.calls[1]?.[0]).toMatchObject({ variable: 'temperature' });
  });
});

describe('㈃ 진행 표시 — 세 화면이 「동작 중」을 말한다 (단계 ③)', () => {
  it('10 인라인 진행 표시가 서는 동안 지도 자리·구제 자리·오류 자리가 없다 (회귀)', async () => {
    await drawUpload(DRAWING_JOB);
    await screen.findByTestId('up-preview-stage');
    expect(screen.queryByTestId('up-preview-map')).toBeNull();
    expect(screen.queryByTestId('up-preview-salvage')).toBeNull();
    expect(screen.queryByTestId('up-preview-error')).toBeNull();
  });

  it('11 그리는 중에 확장보기를 열면 진행 표시가 있다', async () => {
    await drawUpload(DRAWING_JOB);
    await screen.findByTestId('up-preview-stage');
    const body = await openExpand();
    const stage = screen.getByTestId('pv-expand-stage');
    expect(body.contains(stage)).toBe(true);
    // 문면은 인라인과 **같은 값**이다 — 새 문장을 만들지 않는다.
    expect(stage.textContent).toContain('지도 그리는 중');
    expect(screen.queryByTestId('pv-expand-empty')).toBeNull();
  });

  it('12 오버레이 고르개를 바꾼 직후에도 「아직 그리지 않았어요」가 아니라 진행 표시를 낸다', async () => {
    await drawUpload(doneJob());
    await waitFor(() => expect(screen.getByTestId('up-preview-image')).toBeTruthy(), WAIT);
    await openExpand();
    fireEvent.change(screen.getByTestId('pvx-pick-variable'), { target: { value: 'temperature' } });
    // `draw()` 첫 줄의 `setJob(null)` 로 `result` 가 사라지는 그 순간을 겨눈다.
    expect(screen.getByTestId('pv-expand-stage')).toBeTruthy();
    expect(screen.queryByTestId('pv-expand-empty')).toBeNull();
  });

  it('13 상세 그리는 중 상태에서 진행 문면이 있다 (회귀)', async () => {
    render(<DatasetPreviewSection datasetId={DATASET_ID} source={detailSource(DRAWING_JOB)} pollMs={100000} />);
    drawDatasetPreviewWhenReady();
    expect((await screen.findAllByTestId('render-stage')).length).toBeGreaterThan(0);
  });
});

describe('㈅ CSS 원문 계측 — 틀 위 줄 컨테이너 (단계 ①)', () => {
  it('22 틀 위 줄 컨테이너 규칙이 있고 간격을 갖는다', () => {
    const slot = block(PREVIEW_CSS, '.pv-frame-wrap {');
    expect(slot).toContain('flex-direction: column');
    expect(slot).toMatch(/gap:\s*\d/);
  });
});

describe('㈅ CSS 원문 계측 — 확대 줄의 접힘·가림 (단계 ④)', () => {
  it('18 틀 안 지도 자리에 세로 배분 선언이 있다 — 그림은 줄고 확대 줄은 줄지 않는다', () => {
    const canvas = block(PREVIEW_CSS, '.pv-frame .mapcanvas {');
    expect(canvas).toContain('flex-direction: column');
    expect(canvas).toContain('min-height: 0');
    // 그림 자리만 줄어든다.
    expect(block(PREVIEW_CSS, '.pv-frame .pv-viewport {')).toContain('flex: 1 1 auto');
  });

  it('18a 절대 배치 타일만 있어도 지도와 열이 4:3 틀의 실제 높이를 받는다', () => {
    const map = block(PREVIEW_CSS, '.pv-frame .pv-map {');
    const column = block(PREVIEW_CSS, '.pv-frame .pv-mapcol {');
    expect(map).toContain('flex: 1 1 auto');
    expect(map).toContain('min-height: 0');
    expect(column).toContain('align-self: stretch');
    expect(column).toContain('min-height: 0');
  });

  it('19 확대 줄에 줄바꿈 금지와 「줄지 않음」 선언이 있다', () => {
    const zoom = block(PREVIEW_CSS, '.pv-zoom {');
    expect(zoom).toContain('white-space: nowrap');
    expect(zoom).toContain('flex: none');
  });

  it('20 확장보기 본문에 세로 방향 선언이 있다', () => {
    expect(block(UPLOAD_CSS, '.modal-b.pvx-b{')).toContain('flex-direction:column');
  });

  it('21 확장보기 그림에 폭 상한 선언이 있다', () => {
    expect(block(PREVIEW_CSS, '.pv-layers .pv-tile {')).toContain('max-width: 100%');
  });
});
