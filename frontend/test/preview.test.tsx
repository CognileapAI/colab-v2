/**
 * S-08 미등록 파일 미리보기 — **정본 §8.1 전 행** 대비 시험.
 * 오라클 = `E-04_업로드와_계보_확정/documents/Policy_업로드와_계보_확정.md` (v2.3) §8.1 · §9 · §7.1 · §7.2.
 * 화면 글자는 정본에서 그대로 온다 — 여기서 새 한국어 문구를 만들지 않는다.
 * 렌더 경로 소비 규약은 `sessions/P2-viz-report.md §13` · 부록 `A-4` 를 따른다.
 */
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { UnregisteredPreviewPage } from '../src/routes/UnregisteredPreviewPage';
import {
  PREVIEW_ROUTE_PATH,
  previewPath,
  REGISTER_FROM_PREVIEW_STATE_KEY,
} from '../src/components/preview/handoff';
import { tileUrl } from '../src/components/preview/tiles';
import { PreviewGone, NotRenderableError } from '../src/components/preview/types';
import type { PreviewHandoff, PreviewSource, RenderJob } from '../src/components/preview/types';
import { ownerTabOf } from '../src/shell/nav';
import { AppRoutes } from '../src/app/routes';
import { SessionProvider } from '../src/permission/session';
import { account } from './factories';

const UPLOAD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0UP1';
const RENDER_ID = '01JYZ9K7WQ3N8V4M2X6C5B0RN1';

const TILE_TEMPLATE =
  'https://viz.example/renders/01JYZ9K7WQ3N8V4M2X6C5B0RN1/tiles/{z}/{x}/{y}.png?exp=1766000000&sig=abc.def';

const DONE: RenderJob = {
  renderId: RENDER_ID,
  status: '완료',
  result: {
    tileUrlTemplate: TILE_TEMPLATE,
    bounds: { west: 126.5, south: 34.8, east: 129.6, north: 37.2 },
    legend: {
      palette: 'viridis-like',
      variable: 'rain',
      unit: 'mm/h',
      classes: [{ color: '#440154', min: 0, max: 5 }],
    },
  },
};

/** 헤더에서 읽은 값만 이어받는다 — 사람이 붙이는 이름·주제·프로젝트 자리는 애초에 없다 (§8.1 기본정보). */
const HANDOFF: PreviewHandoff = {
  uploadId: UPLOAD_ID,
  renderId: RENDER_ID,
  // 짝 파일 없이 그려 봤는지는 **S-04 가 아는 사실**이다. S-08 이 지어내지 않고 이어받는다 (§8)
  withoutReferenceGrid: true,
  basicInfo: { byteSize: 1288490188, variable: 'rain' },
  files: [
    {
      fileId: '01JYZ9K7WQ3N8V4M2X6C5B0FI1',
      fileName: 'rdr_2025.nc',
      kind: '본체',
      byteSize: 1288490188,
    },
  ],
};

function makeSource(over: Partial<PreviewSource> = {}) {
  const calls: string[] = [];
  const source: PreviewSource = {
    get: vi.fn(async () => {
      calls.push('get');
      return DONE;
    }),
    create: vi.fn(async () => {
      calls.push('create');
      return DONE;
    }),
    probeTile: vi.fn(async () => {
      calls.push('probeTile');
      return 'ok' as const;
    }),
    ...over,
  };
  return { source, calls };
}

function renderPage(source: PreviewSource, handoff: PreviewHandoff | null = HANDOFF) {
  return render(
    <MemoryRouter
      initialEntries={[
        {
          pathname: previewPath(UPLOAD_ID, handoff?.renderId).split('?')[0]!,
          search: previewPath(UPLOAD_ID, handoff?.renderId).split('?')[1] ?? '',
          state: handoff ? { preview: handoff } : null,
        },
      ]}
    >
      <Routes>
        <Route
          path={PREVIEW_ROUTE_PATH}
          element={<UnregisteredPreviewPage source={source} pollMs={1} />}
        />
        <Route path="/datasets" element={<div>카탈로그</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('§8.1 화면 귀속 — 탭 귀속은 `데이터셋`이다', () => {
  it('S-08 주소의 주인 탭이 데이터셋이다', () => {
    expect(ownerTabOf(previewPath(UPLOAD_ID, RENDER_ID).split('?')[0]!)).toBe('datasets');
  });
});

describe('§8.1 휘발 고지 — 상단 상시 · 남은 시간을 숫자로 적지 않는다', () => {
  it('정본 두 문장과 `연구실에 등록 →` 이 한 줄에 있다', async () => {
    const { source } = makeSource();
    renderPage(source);
    const notice = await screen.findByTestId('volatile-notice');
    expect(notice.textContent).toContain('연구실에 등록하지 않은 파일이에요');
    expect(notice.textContent).toContain(
      '여기서 얼마든지 열어 볼 수 있어요. 다만 이 화면을 벗어나면 사라지고, 다른 사람은 볼 수 없어요.',
    );
    expect(within(notice).getByRole('button', { name: '연구실에 등록 →' })).toBeInTheDocument();
  });

  it('남은 시간을 숫자로 세지 않는다', async () => {
    const { source } = makeSource();
    renderPage(source);
    const notice = await screen.findByTestId('volatile-notice');
    expect(notice.textContent).not.toMatch(/남았|남은 시간|\d+\s*(시간|분|초)/);
  });
});

describe('§8.1 기본정보 — 파일 헤더에서 읽은 값만 · 없는 항목은 자리째 뺀다', () => {
  it('읽은 값의 자리만 서고, 못 받은 항목은 행이 아예 없다 (빈 칸·대시를 두지 않는다)', async () => {
    const { source } = makeSource();
    renderPage(source);
    const grid = await screen.findByTestId('preview-basicinfo');
    expect(within(grid).getByText('크기')).toBeInTheDocument();
    expect(within(grid).queryByText('좌표계')).toBeNull();
    expect(within(grid).queryByText('기간')).toBeNull();
    expect(within(grid).queryByText('격자')).toBeNull();
    expect(grid.textContent).not.toContain('—');
  });

  it('이름·주제·소속 프로젝트는 등록 전이라 자리 자체가 없다', async () => {
    const { source } = makeSource();
    renderPage(source);
    await screen.findByTestId('preview-basicinfo');
    expect(screen.queryByText('주제')).toBeNull();
    expect(screen.queryByText('소속 프로젝트')).toBeNull();
    expect(screen.queryByText('데이터셋 이름')).toBeNull();
  });
});

describe('§8.1 미리보기 — 업로드 모달에서 그린 것을 그대로 이어서 보여준다', () => {
  it('넘겨받은 renderId 를 조회할 뿐 다시 그리지 않는다', async () => {
    const { source, calls } = makeSource();
    renderPage(source);
    await screen.findByTestId('preview-map');
    expect(source.get).toHaveBeenCalledWith(RENDER_ID);
    expect(calls).not.toContain('create');
  });

  it('이어받은 것이 없으면 없는 대로 말한다 — 가짜 미리보기를 만들지 않는다', async () => {
    const { source, calls } = makeSource();
    renderPage(source, { uploadId: UPLOAD_ID, basicInfo: {}, files: [] });
    await screen.findByTestId('preview-none');
    expect(calls).toHaveLength(0);
  });
});

describe('진행 단계 — 정본 3값 그대로 · 한 덩어리 「로딩 중」으로 두지 않는다', () => {
  it('`그리는 중` 일 때만 단계가 있고 문구가 정본 그대로다', async () => {
    const seq: RenderJob[] = [
      { renderId: RENDER_ID, status: '그리는 중', stage: '파일 읽는 중' },
      { renderId: RENDER_ID, status: '그리는 중', stage: '지도 그리는 중' },
      { renderId: RENDER_ID, status: '그리는 중', stage: '범례 만드는 중' },
      DONE,
    ];
    // 조회 응답을 시험이 한 걸음씩 푼다 — 단계가 실제로 셋 다 화면을 지나간다
    const gates = seq.map(() => {
      let release!: (j: RenderJob) => void;
      const p = new Promise<RenderJob>((res) => {
        release = res;
      });
      return { p, release };
    });
    let i = 0;
    const { source } = makeSource({
      get: vi.fn(async () => gates[Math.min(i++, gates.length - 1)]!.p),
    });
    renderPage(source);
    gates[0]!.release(seq[0]!);
    expect(await screen.findByText('파일 읽는 중…')).toBeInTheDocument();
    gates[1]!.release(seq[1]!);
    expect(await screen.findByText('지도 그리는 중…')).toBeInTheDocument();
    gates[2]!.release(seq[2]!);
    expect(await screen.findByText('범례 만드는 중…')).toBeInTheDocument();
    gates[3]!.release(seq[3]!);
    await screen.findByTestId('preview-map');
    expect(screen.queryByText('로딩 중')).toBeNull();
    expect(screen.queryByTestId('render-stage')).toBeNull();
  });

  it('안내는 aria-live=polite 다 (§8 미리보기 그리기)', async () => {
    const { source } = makeSource({
      get: vi.fn(
        async () =>
          ({ renderId: RENDER_ID, status: '그리는 중', stage: '파일 읽는 중' }) as RenderJob,
      ),
    });
    renderPage(source);
    const stage = await screen.findByTestId('render-stage');
    expect(stage).toHaveAttribute('aria-live', 'polite');
  });
});

describe('실패는 200 + `failure` 다 — HTTP 오류가 아니다', () => {
  it('status=실패 면 서버가 준 정본 문구를 그대로 말한다', async () => {
    const failed: RenderJob = {
      renderId: RENDER_ID,
      status: '실패',
      failure: {
        code: 'RENDER_TIMEOUT',
        message: '그리는 데 너무 오래 걸려요. 조각 하나나 좁은 기간으로 다시 해 보세요.',
      },
    };
    const { source } = makeSource({ get: vi.fn(async () => failed) });
    renderPage(source);
    const box = await screen.findByTestId('render-failure');
    expect(box).toHaveAttribute('aria-live', 'assertive');
    expect(box.textContent).toContain(
      '그리는 데 너무 오래 걸려요. 조각 하나나 좁은 기간으로 다시 해 보세요.',
    );
    // 그릴 수 없어도 등록은 그대로 된다 (§9)
    expect(screen.getByRole('button', { name: '연구실에 등록 →' })).toBeEnabled();
  });
});

describe('부분 실패는 실패가 아니다 — 읽힌 조각으로 그리고 `완료` 로 남는다', () => {
  it('오류 자리가 아니라 안내 자리에 서고, 못 읽은 조각을 이름으로 밝힌다', async () => {
    const partial: RenderJob = {
      ...DONE,
      partialFailure: {
        totalParts: 72,
        renderedParts: 69,
        missingParts: [
          { fileName: 'rdr_20250101_0300.nc' },
          { fileName: 'rdr_20250101_0400.nc' },
          { fileName: 'rdr_20250101_0500.nc' },
        ],
      },
    };
    const { source } = makeSource({ get: vi.fn(async () => partial) });
    renderPage(source);
    const note = await screen.findByTestId('partial-failure');
    expect(note.textContent).toContain(
      '조각 72개 중 3개를 읽지 못했어요. 읽은 69개로 그릴 수 있어요.',
    );
    expect(note.textContent).toContain('rdr_20250101_0300.nc');
    expect(screen.queryByTestId('render-failure')).toBeNull();
    expect(await screen.findByTestId('preview-map')).toBeInTheDocument();
  });
});

describe('415 그릴 수 없음 — 등록이 막힌 것이 아니다', () => {
  it('그릴 수 있는 형식을 함께 말하고 등록 길은 살아 있다', async () => {
    const { source } = makeSource({
      get: vi.fn(async () => {
        throw new NotRenderableError('이 형식은 아직 지도로 못 그려요.', [
          'NetCDF',
          'Binary',
          'HDF4',
          'GeoTIFF',
        ]);
      }),
    });
    renderPage(source);
    const box = await screen.findByTestId('not-renderable');
    expect(box.textContent).toContain('이 형식은 아직 지도로 못 그려요.');
    expect(box.textContent).toContain('NetCDF · Binary · HDF4 · GeoTIFF');
    expect(screen.getByRole('button', { name: '연구실에 등록 →' })).toBeEnabled();
    expect(screen.queryByTestId('render-failure')).toBeNull();
  });
});

describe('§8.1 수명 · §9 수명이 지난 파일 — 만료는 만료라고 말한다', () => {
  it('조회가 없는 것으로 답하면 정본 문구를 그대로 낸다', async () => {
    const { source } = makeSource({
      get: vi.fn(async () => {
        throw new PreviewGone();
      }),
    });
    renderPage(source);
    const box = await screen.findByTestId('preview-expired');
    expect(box.textContent).toContain('이 파일은 더 이상 없어요. 다시 올려 주세요.');
  });

  it('타일이 401 이어도 「권한이 없다」가 아니라 만료로 말한다 (`P2-viz-report A-1`)', async () => {
    const { source } = makeSource({ probeTile: vi.fn(async () => 'expired' as const) });
    renderPage(source);
    const box = await screen.findByTestId('preview-expired');
    expect(box.textContent).toContain('이 파일은 더 이상 없어요. 다시 올려 주세요.');
    expect(box.textContent).not.toMatch(/권한|인증|로그인/);
  });
});

describe('`tileUrlTemplate` 은 불투명 문자열이다 (`〈68〉` 서명이 실려 있다)', () => {
  it('치환은 {z}·{x}·{y} 셋뿐이고 질의부는 한 글자도 건드리지 않는다', () => {
    expect(tileUrl(TILE_TEMPLATE, 3, 6, 2)).toBe(
      'https://viz.example/renders/01JYZ9K7WQ3N8V4M2X6C5B0RN1/tiles/3/6/2.png?exp=1766000000&sig=abc.def',
    );
  });

  it('화면은 템플릿을 그대로 들고 있다 — 다시 조립하지 않는다', async () => {
    const { source } = makeSource();
    renderPage(source);
    const map = await screen.findByTestId('preview-map');
    expect(map).toHaveAttribute('data-tile-template', TILE_TEMPLATE);
  });
});

describe('컨트롤은 팔레트와 구간 수 둘뿐이다', () => {
  it('구간 수는 3~9 이고 기본이 6 이다', async () => {
    const { source } = makeSource();
    renderPage(source);
    const sel = (await screen.findByLabelText('구간 수')) as HTMLSelectElement;
    expect(sel.value).toBe('6');
    expect([...sel.options].map((o) => o.value)).toEqual(['3', '4', '5', '6', '7', '8', '9']);
  });

  it('팔레트 이름을 화면이 지어내지 않는다 — 목록의 출처는 `listPalettes` 다', async () => {
    const { source } = makeSource();
    const { container } = renderPage(source);
    await screen.findByTestId('preview-map');
    const control = screen.getByTestId('palette-control');
    // 완료된 렌더가 실제로 쓴 팔레트 키만 되쓴다. 후보 목록을 화면이 만들지 않는다
    expect(control.querySelectorAll('option')).toHaveLength(0);
    expect(container.textContent).not.toContain('viridis');
  });

  it('구간 수를 바꾸면 완료된 렌더의 팔레트 키를 그대로 실어 다시 그린다', async () => {
    const { source } = makeSource();
    renderPage(source);
    await screen.findByTestId('preview-map');
    fireEvent.change(screen.getByLabelText('구간 수'), { target: { value: '9' } });
    await waitFor(() =>
      expect(source.create).toHaveBeenCalledWith({
        uploadId: UPLOAD_ID,
        palette: 'viridis-like',
        classCount: 9,
        withoutReferenceGrid: true,
      }),
    );
  });
});

describe('§8.1 계보·족보 / 검색·공유·승인 — 빈 자리 + 안내 문구', () => {
  it('두 자리가 눈에 보이게 비어 있고 정본 문구가 그대로 있다', async () => {
    const { source } = makeSource();
    renderPage(source);
    const lineage = await screen.findByTestId('slot-lineage');
    expect(lineage.textContent).toContain('등록하면 AI가 가공 전 데이터를 찾아 줘요');
    const share = screen.getByTestId('slot-share');
    expect(share.textContent).toContain('등록하면 연구실이 이 데이터를 찾을 수 있어요');
  });
});

describe('§8.1 나가기 · §7.2 — 파일을 버리고 목록으로', () => {
  it('`← 데이터셋 목록` 한 줄이 목록으로 간다', async () => {
    const { source } = makeSource();
    renderPage(source);
    const back = await screen.findByTestId('backrow');
    const link = within(back).getByRole('link');
    expect(link).toHaveAttribute('href', '/datasets');
    expect(back.textContent).toContain('데이터셋 목록');
  });
});

describe('§7.1 저장 안 됨 — 이 화면은 사실을 하나도 만들지 않는다', () => {
  it('읽기(조회·타일)와 다시 그리기 말고는 아무것도 부르지 않는다', async () => {
    const { source, calls } = makeSource();
    renderPage(source);
    await screen.findByTestId('preview-map');
    expect(new Set(calls)).toEqual(new Set(['get', 'probeTile']));
  });

  it('등록으로 가는 길은 이 화면이 저장하는 것이 아니라 모달을 다시 여는 것이다', async () => {
    const { source } = makeSource();
    renderPage(source);
    await screen.findByTestId('preview-map');
    fireEvent.click(screen.getByRole('button', { name: '연구실에 등록 →' }));
    expect(await screen.findByText('카탈로그')).toBeInTheDocument();
    expect(REGISTER_FROM_PREVIEW_STATE_KEY).toBe('openUploadForRegister');
  });
});

/**
 * Ted 2026-08-28 완료 정의 ① 도달 경로 — **라우팅 표 쪽 절반.**
 * 앞의 시험들은 화면 컴포넌트를 직접 마운트하므로 `app/routes.tsx` 를 한 줄도 검사하지 않는다.
 * 라우트가 빠져 있으면 사람은 이 화면에 **도달할 수 없고**, 그때 여기가 red 가 된다.
 */
describe('완료 정의 ① — 앱 라우팅 표가 S-08 을 세운다', () => {
  it('S-08 주소로 들어가면 없는 화면이 아니라 미등록 미리보기가 선다', async () => {
    const { container } = render(
      <MemoryRouter initialEntries={[previewPath(UPLOAD_ID)]}>
        <SessionProvider account={account({ '업로드·편집': true })}>
          <AppRoutes />
        </SessionProvider>
      </MemoryRouter>,
    );
    expect(container.querySelector('[data-screen="S-08"]')).not.toBeNull();
    // 라우트가 없으면 `*` 가 먹어 「없는 화면」이 뜬다 — 그 자리를 못 박는다
    expect(screen.queryByTestId('preview-none')).toBeInTheDocument();
    // 이어받은 것이 없으므로 화면은 없는 대로 말한다. 여기서 값을 지어내지 않는다
    expect(await screen.findByTestId('volatile-notice')).toBeInTheDocument();
  });
});

/**
 * 완료 정의 **명시적 범위 밖** — 확대 · 타일 (`work-items.yaml` `F-1` ⑶ · `PLAN-SoT §9 〈183〉`).
 * 미등록 미리보기는 **언제나 한 장**이다. 렌더 결과에 `tileUrlTemplate` 과 `bounds` 가 실려
 * 있어도(위 `DONE` 이 그렇다) 이 화면은 타일 갈래를 타지 않는다 — 타일 모자이크의 주 화면은
 * **등록된 데이터셋의 지도**이고 S-08 이 아니다(`〈238〉` · `tiles.ts` 주석).
 * `usePreviewRender` 의 확대용 선택 인자를 이 화면이 받는 순간 여기가 red 가 된다.
 */
describe('완료 정의 범위 밖 — S-08 은 언제나 한 장이다 (타일·확대 갈래가 아니다)', () => {
  it('타일 조각을 세우지 않고 그림 한 장을 그린다', async () => {
    const { source } = makeSource();
    renderPage(source);
    const map = await screen.findByTestId('preview-map');
    // 조각도 모자이크도 없다
    expect(within(map).queryByTestId('preview-mosaic')).toBeNull();
    expect(within(map).queryAllByTestId('preview-tile')).toHaveLength(0);
    // 한 장이고, 그 한 장은 0/0/0 이다 (`tiles.ts` `resultImageSrc`)
    const one = within(map).getByTestId('preview-single-image');
    expect(one).toHaveAttribute('src', tileUrl(TILE_TEMPLATE, 0, 0, 0));
  });

  it('확대 컨트롤도 확대 조작 자리도 없다', async () => {
    const { source } = makeSource();
    renderPage(source);
    const map = await screen.findByTestId('preview-map');
    expect(within(map).queryByTestId('preview-viewport')).not.toHaveAttribute('data-zoomable');
    expect(within(map).queryByTestId('preview-layers')).not.toHaveAttribute('data-zoom-scale');
    expect(within(map).queryByTestId('preview-zoom')).toBeNull();
  });
});
