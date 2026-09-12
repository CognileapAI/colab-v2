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
import type { PreviewPiece, TargetDescription } from '../src/components/preview/pick';

declare const process: { cwd(): string };

const UPLOAD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0UP1';
const RENDER_ID = '01JYZ9K7WQ3N8V4M2X6C5B0RE1';
const PIECE_A = '01JYZ9K7WQ3N8V4M2X6C5B0F01';
const PIECE_B = '01JYZ9K7WQ3N8V4M2X6C5B0F02';
const WAIT = { timeout: 5000 };

/** 주석은 걷어내고 읽는다 — 주석 속 선택자·값이 계측에 섞이지 않도록. */
const read = (rel: string): string =>
  String(readFileSync(resolve(process.cwd(), rel), 'utf8')).replace(/\/\*[\s\S]*?\*\//g, '');

const PREVIEW_CSS = read('src/components/preview/preview.css');

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

describe('㈅ CSS 원문 계측 — 틀 위 줄 컨테이너 (단계 ①)', () => {
  it('22 틀 위 줄 컨테이너 규칙이 있고 간격을 갖는다', () => {
    const slot = block(PREVIEW_CSS, '.pv-frame-wrap {');
    expect(slot).toContain('flex-direction: column');
    expect(slot).toMatch(/gap:\s*\d/);
  });
});
