/**
 * R-BUGFIX-260912 L3 — 미리보기 조작 자리 `#26`(64×64 축소본의 자리).
 *
 * 오라클 = `dev-package/prd/rounds/R-BUGFIX-260912.md` §L3 1단 ＋
 *          `dev-package/prd/specs/2026-09-12-issue-preview-controls.md` ㉮ · 「시험 결정」 1~3항.
 *
 * ⚠ 범위 = `#26` **한 건뿐이다.** `#25`⑵(고르개 줄 자리) · `#27`·`#28`(확대 줄 접힘·가림)은
 *   2026-09-12 재기획 결정으로 이 회차에서 구현하지 않는다 — 그 시험도 여기 두지 않는다.
 * ⚠ **jsdom 은 레이아웃을 계산하지 않는다** — 배치 판정은 두 갈래로 세운다.
 *   ㈎ DOM 조상 관계(`contains`) ㈏ CSS 원문 계측(주석 제거 뒤 선언 존재 단언).
 *   같은 규율의 선례 = `design-fix-20260908.test.ts` · `preview-slot-4x3.test.tsx`.
 * ⚠ 화면 글자를 새로 만들지 않는다 — 기대 문자열은 전부 정본에 이미 있는 것이다.
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

const UPLOAD_CSS = read('src/components/upload/upload.css');

/** 선택자 하나의 선언 블록(`{ … }`)을 원문에서 잘라낸다. */
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

/** 업로드(S-04) 출처 — 그리기 한 번에 바로 `완료` 로 간다. */
function uploadSource(job: RenderJob): PreviewSource {
  return {
    palettes: vi.fn(async () => [{ palette: 'viridis', label: '비리디스' }]),
    createRender: vi.fn(async () => job),
    getRender: vi.fn(async () => job),
    files: vi.fn(async () => PIECES),
    describe: vi.fn(async () => DESCRIBE),
  } as unknown as PreviewSource;
}

/** 그리기까지 밟아 `완료` 화면을 세운다. */
async function drawUpload(job: RenderJob, representativeFile: File | null = null) {
  render(
    <PreviewPanel
      source={uploadSource(job)}
      uploadId={UPLOAD_ID}
      hasReferenceGrid
      representativeFile={representativeFile}
    />,
  );
  // 버튼은 팔레트 조회 전에도 존재한다. 화면의 선택값이 준비된 뒤 그린다.
  await waitFor(() => expect(screen.getByTestId('up-style-palette')).toHaveValue('viridis'), WAIT);
  fireEvent.click(screen.getByTestId('up-preview-draw'));
  await waitFor(() => expect(screen.getByTestId('up-preview-image')).toBeTruthy(), WAIT);
}

describe('#26 — 64×64 축소본은 지도 자리에서 빠지고 접히는 설정 자리에 선다', () => {
  it('성공 경로의 지도 자리 안 그림 요소는 한 장뿐이다', async () => {
    await drawUpload(doneJob({ thumbnailUrl: 'https://viz.example/p/thumb.png' }));
    const map = screen.getByTestId('up-preview-map');
    expect(map.querySelectorAll('img').length).toBe(1);
    expect(map.querySelector('[data-testid="up-preview-thumb"]')).toBeNull();
  });

  /* ⭑ ⟨개정 2026-09-12 · R-BUGFIX-260912 L3b · spec v2 §6 ㉱ · Ted 승인 「모두 권고대로」⟩
     중복 방지 규칙이 붙었다 — 고른 그림이 없으면 자동 축소본을 따로 두지 않는다.
     표시 목적(`〈88〉` 묶음 3)은 그대로다: 그 경우 대표 그림 고르개(`up-thumb-img`)가
     같은 블록에서 같은 주소를 싣는다. ／ 종전 단언 ~~고른 그림 없이도 `up-preview-thumb`
     가 접히는 블록 안에 있다~~ — 그러면 같은 그림 두 장이 나란히 선다. */
  it('축소본은 접히는 설정 블록 안, 대표 그림 고르개와 같은 자리에 있다', async () => {
    vi.stubGlobal('URL', {
      ...URL,
      createObjectURL: () => 'blob:local/cover.png',
      revokeObjectURL: () => undefined,
    });
    const picked = new File([new Uint8Array([1])], 'cover.png', { type: 'image/png' });
    await drawUpload(doneJob({ thumbnailUrl: 'https://viz.example/p/thumb.png' }), picked);
    const options = screen.getByTestId('up-preview-options');
    const thumb = screen.getByTestId('up-preview-thumb');
    expect(options.contains(thumb)).toBe(true);
    expect(screen.getByTestId('up-thumb-block').contains(thumb)).toBe(true);
    expect(options.contains(screen.getByTestId('up-thumb-block'))).toBe(true);
    vi.unstubAllGlobals();
  });

  it('고른 그림이 없으면 대표 그림 고르개가 같은 블록에서 자동 축소본을 싣는다', async () => {
    await drawUpload(doneJob({ thumbnailUrl: 'https://viz.example/p/thumb.png' }));
    const options = screen.getByTestId('up-preview-options');
    const img = screen.getByTestId('up-thumb-img');
    expect(options.contains(img)).toBe(true);
    expect(img.getAttribute('src')).toBe('https://viz.example/p/thumb.png');
  });

  /* 23 — 옮긴 뒤 죽은 규칙 방지. `.mapcanvas .thumb` 는 **구제(salvage) 경로가 계속 쓴다**
     (그 경로는 이번 회차 범위 밖이다 · spec v2 §6 ㉱ 「범위 밖」). 규칙과 그 규칙을 쓰는
     DOM 이 둘 다 실재해야 죽은 규칙이 아니다. */
  it('지도 자리 축소본 규칙은 구제 경로가 쓰므로 죽은 규칙이 아니다', () => {
    expect(UPLOAD_CSS.indexOf('.mapcanvas .thumb')).toBeGreaterThan(-1);
    const src = String(
      readFileSync(resolve(process.cwd(), 'src/components/upload/PreviewPanel.tsx'), 'utf8'),
    );
    const salvage = src.slice(src.indexOf('data-testid="up-preview-salvage"'));
    expect(salvage.indexOf('className="thumb"')).toBeGreaterThan(-1);
  });

  it('축소본 주소가 없는 응답에서는 자리째 없다 (대조군 · 대상 0건 방지)', async () => {
    await drawUpload(doneJob());
    expect(screen.queryByTestId('up-preview-thumb')).toBeNull();
    expect(screen.getByTestId('up-preview-map').querySelectorAll('img').length).toBe(1);
  });

  it('옮긴 자리의 CSS 가 64×64 · contain · pixelated 를 승계한다', () => {
    const moved = block(UPLOAD_CSS, '.up-preview-options .thumb');
    expect(moved).toContain('width: 64px');
    expect(moved).toContain('height: 64px');
    expect(moved).toContain('object-fit: contain');
    expect(moved).toContain('image-rendering: pixelated');
  });
});
