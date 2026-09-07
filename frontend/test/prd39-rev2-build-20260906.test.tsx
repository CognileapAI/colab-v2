/**
 * WU-A12R · PRD-39 「없음」 잔여 5건 ＋ 커서 위경도 HUD.
 *
 * 이 회차가 세우는 6행 — ① 파일 분석 3단계 표시 ＋ 완료 전 `다음` 비활성 · ② 모달 전역 드롭
 * 수신 · ③ 파일 빼기 즉시 반영 ＋ 초기화 고지 · ⑩ 접근 구역 출처 문장 · ⑫ 행동 줄 바닥 고정
 * ＋ 할 일 안내 3문면 · HUD(커서 위경도 역산).
 *
 * ⛔ **문면을 이 시험이 짓지 않는다** — 축자는 rev1 원문(`10_적용전/업로드_계보_260826_rev1_이태헌.html`
 *    `pbStatus` · `syncFoot()` · `removeFile()` · 접근·다운로드 카드)과 PRD-39 실측표에서 떴다.
 *    다르게 적을 사유를 찾으면 고치지 말고 보고한다 (`rounds/R-A2.md §1`).
 *
 * ⚠ **HUD 는 값 조회를 대체하지 않는다** — 둘이 함께 서고 출처 라벨(`역산값` · `셀값`)이 다르다.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import { SessionProvider } from '../src/permission/session';
import { UploadEntry } from '../src/components/upload/UploadEntry';
import { ANALYZED_CHIP, ANALYZING_CHIP } from '../src/components/common/toastCopy';
import {
  ANALYZE_STAGES,
  FILE_REMOVED_NOTICE,
  RECEIVING_STAGE,
} from '../src/components/upload/UploadModal';
import { FOOT_HINTS, NEXT_BLOCKED_HINT } from '../src/components/upload/RegisterArea';
import { UsageSection } from '../src/components/detail/UsageSection';
import { ACCESS_ORIGIN_NOTE } from '../src/components/detail/UsageSection';
import {
  HUD_IDLE,
  HUD_OUTSIDE,
  HUD_SOURCE_LABEL,
  PreviewMap,
  pvLatOf,
  pvLonOf,
} from '../src/components/preview/PreviewPanels';
import { VALUE_SOURCE_LABEL } from '../src/components/datasetpreview/ValueLookupPanel';
import type { RenderResult } from '../src/components/preview/types';
import type { DatasetDetail } from '../src/components/detail/types';
import type { CurrentAccount, Schemas } from '../src/api/client';
import type {
  LineageStepContext,
  PreviewSource,
  ProjectSource,
  UploadSource,
  UploadSources,
} from '../src/components/upload/types';
import type { LineageSource } from '../src/components/lineage/types';

const UPLOAD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0UP1';
const FILE_ID = '01JYZ9K7WQ3N8V4M2X6C5B0FI1';
const DATASET_ID = '01JYZ9K7WQ3N8V4M2X6C5B0DS1';

function account(): CurrentAccount {
  return {
    accountId: '01JYZ9K7WQ3N8V4M2X6C5B0AC1',
    name: '호랑이',
    email: 'tiger@example.ac.kr',
    role: '연구원',
    labId: '01JYZ9K7WQ3N8V4M2X6C5B0LB1',
    labName: '수자원순환연구실',
    permissions: { '업로드·편집': true } as CurrentAccount['permissions'],
  } as CurrentAccount;
}

function makeFile(name: string, size = 1024): File {
  const f = new File(['x'], name, { type: 'application/octet-stream' });
  Object.defineProperty(f, 'size', { value: size });
  return f;
}

/** 접수는 되지만 **분석이 아직 안 끝난** 업로드를 만들 수 있는 가짜 출처. */
function fakes(
  over: { ready?: boolean; failure?: boolean; projectRows?: { projectId: string; name: string; type: string }[] } = {},
) {
  const ready = over.ready ?? true;
  const status: Schemas['UploadStatus'] = {
    uploadId: UPLOAD_ID,
    files: [
      { fileId: FILE_ID, fileName: 'nakdong_precip_2025_Lv2.nc', kind: '본체', byteSize: 1024 },
    ],
    ready,
    renderable: true,
    metadataComplete: true,
    expiresAt: '2026-08-24T00:00:00Z',
    failure: over.failure
      ? ({ code: '읽기 실패', message: '파일을 읽지 못했어요' } as never)
      : null,
  } as Schemas['UploadStatus'];

  const upload: UploadSource = {
    async create(files: { file: File; kind: string }[]) {
      return {
        uploadId: UPLOAD_ID,
        files: files.map((f: { file: File; kind: string }) => ({
          fileId: FILE_ID,
          fileName: f.file.name,
          kind: f.kind,
          byteSize: f.file.size,
        })),
      };
    },
    async status() {
      return status;
    },
    async register() {
      return { datasetId: DATASET_ID };
    },
    async attachGrid() {
      return [];
    },
  } as unknown as UploadSource;

  const preview: PreviewSource = {
    async palettes() {
      return [{ palette: 'viridis', label: '비리디스' }];
    },
    async createRender() {
      return { renderId: 'R1', status: '그리는 중' } as never;
    },
    async getRender() {
      return { renderId: 'R1', status: '그리는 중' } as never;
    },
  } as unknown as PreviewSource;

  const projectRows = over.projectRows ?? [];
  const projects: ProjectSource = { async list() { return projectRows; }, async create() { return { projectId: 'P', name: 'x', type: '논문' }; } } as unknown as ProjectSource;
  const lineage = {} as LineageSource;
  return { upload, preview, projects, lineage } as UploadSources;
}

async function openModal(sources: UploadSources) {
  render(
    <MemoryRouter initialEntries={['/datasets']}>
      <SessionProvider account={account()}>
        <UploadEntry
          sources={sources}
          lineageStep={(_ctx: LineageStepContext) => <div data-testid="lineage-slot" />}
        />
      </SessionProvider>
    </MemoryRouter>,
  );
  fireEvent.click(screen.getByTestId('gnb-upload'));
  await screen.findByTestId('upload-modal');
}

async function dropFiles(files: File[]) {
  fireEvent.change(screen.getByTestId('up-drop-input'), { target: { files } });
  await act(async () => {});
  await screen.findByTestId('up-files');
}

/* ────────────────────────────────────────────────────────────────────────
 * ① 파일 분석 3단계 표시 ＋ 완료 전 `다음` 비활성
 *   rev1 근거 = `pbStatus` 문면 · `anNext.disabled`
 * ──────────────────────────────────────────────────────────────────────── */

describe('PRD-39 ① — 파일 분석 3단계 표시와 완료 전 `다음` 비활성', () => {
  it('단계 문면이 정확히 3개이고 rev1 `pbStatus` 축자다', () => {
    expect(ANALYZE_STAGES).toHaveLength(3);
    expect(ANALYZE_STAGES[0]).toBe(RECEIVING_STAGE);
    expect(ANALYZE_STAGES[0]).toBe('파일 올리는 중…');
    expect(ANALYZE_STAGES[1]).toBe('확장자·용량 확인 중…');
    expect(ANALYZE_STAGES[2]).toBe('분석 완료 · 확장자와 용량을 읽었어요');
  });

  it('분석이 끝나면 3단계째와 `분석 완료` 칩이 선다', async () => {
    await openModal(fakes({ ready: true }));
    await dropFiles([makeFile('a.nc')]);
    const box = await screen.findByTestId('up-analyze');
    expect(box).toHaveTextContent(ANALYZE_STAGES[2]!);
    expect(box).toHaveTextContent(ANALYZED_CHIP);
    expect(box).toHaveAttribute('data-stage', '3');
  });

  it('분석이 안 끝났으면 `분석 중` 칩이고 단계가 3에 못 간다', async () => {
    await openModal(fakes({ ready: false }));
    await dropFiles([makeFile('a.nc')]);
    const box = await screen.findByTestId('up-analyze');
    expect(box).toHaveTextContent(ANALYZING_CHIP);
    expect(box).not.toHaveAttribute('data-stage', '3');
  });

  it('접수가 실패하면 단계 표시를 걷는다 — 화면이 진행 중과 실패를 함께 말하지 않는다', async () => {
    await openModal(fakes({ ready: false, failure: true }));
    await dropFiles([makeFile('a.nc')]);
    expect(screen.queryByTestId('up-analyze')).toBeNull();
  });

  it('분석이 안 끝났으면 `다음` 이 비활성이고, 끝나면 눌린다', async () => {
    await openModal(fakes({ ready: false }));
    await dropFiles([makeFile('a.nc')]);
    fireEvent.click(screen.getByTestId('reg-open'));
    await screen.findByTestId('reg-steps');
    expect(screen.getByTestId('reg-next')).toBeDisabled();
    expect(screen.getByTestId('reg-foot-hint')).toHaveTextContent(NEXT_BLOCKED_HINT);
  });

  it('분석이 끝나면 `다음` 이 활성이다', async () => {
    await openModal(fakes({ ready: true }));
    await dropFiles([makeFile('a.nc')]);
    fireEvent.click(screen.getByTestId('reg-open'));
    await screen.findByTestId('reg-steps');
    expect(screen.getByTestId('reg-next')).not.toBeDisabled();
  });
});

/* ────────────────────────────────────────────────────────────────────────
 * ② 모달 전역 드롭 수신 — `document` 에 건다
 * ──────────────────────────────────────────────────────────────────────── */

describe('PRD-39 ② — 모달 어디에 놓아도 파일을 받는다', () => {
  it('드롭존 밖(모달 본문)에 놓아도 파일이 목록에 선다', async () => {
    await openModal(fakes());
    const body = screen.getByTestId('upload-modal');
    fireEvent.drop(body, { dataTransfer: { files: [makeFile('b.nc')], items: [] } });
    await act(async () => {});
    expect(await screen.findByTestId('up-files')).toHaveTextContent('b.nc');
  });

  it('드롭존 라벨에 놓으면 **한 번만** 받는다 — 문서 핸들러와 이중 수신하지 않는다', async () => {
    await openModal(fakes());
    fireEvent.drop(screen.getByTestId('up-drop'), {
      dataTransfer: { files: [makeFile('a.nc')], items: [] },
    });
    await act(async () => {});
    const list = await screen.findByTestId('up-files');
    expect(list).toHaveTextContent('a.nc');
    // 두 벌 접수되면 본체가 2건이 되어 조각 묶음이 선다
    expect(screen.queryByTestId('up-bundle')).toBeNull();
    expect(screen.getAllByRole('button', { name: 'a.nc 빼기' })).toHaveLength(1);
  });

  it('모달이 닫히면 전역 드롭을 더 받지 않는다 — 리스너를 걷는다', async () => {
    const add = vi.spyOn(document, 'addEventListener');
    const remove = vi.spyOn(document, 'removeEventListener');
    await openModal(fakes());
    expect(add.mock.calls.some(([t]) => t === 'drop')).toBe(true);
    fireEvent.click(screen.getByTestId('upload-close'));
    await act(async () => {});
    expect(remove.mock.calls.some(([t]) => t === 'drop')).toBe(true);
    add.mockRestore();
    remove.mockRestore();
  });
});

/* ────────────────────────────────────────────────────────────────────────
 * ③ 파일 빼기 즉시 반영 ＋ 초기화 고지
 *   rev1 근거 = `removeFile()` · `파일을 뺐어요. 입력하던 내용은 사라져요`
 * ──────────────────────────────────────────────────────────────────────── */

describe('PRD-39 ③ — 파일을 빼면 즉시 반영되고 초기화를 알린다', () => {
  it('고지 문면이 rev1 `removeFile()` 축자다', () => {
    expect(FILE_REMOVED_NOTICE).toBe('파일을 뺐어요. 입력하던 내용은 사라져요');
  });

  it('`×` 를 누르면 그 파일이 목록에서 사라지고 고지가 뜬다', async () => {
    await openModal(fakes());
    await dropFiles([makeFile('a.nc'), makeFile('c.nc')]);
    // 조각 묶음은 접힘이 기본이다(존치 · rev1 #11) — 펴야 조각별 `×` 가 보인다
    fireEvent.click(screen.getByRole('button', { name: '조각 2개 모두 보기' }));
    fireEvent.click(screen.getByRole('button', { name: 'c.nc 빼기' }));
    await act(async () => {});
    expect(screen.getByTestId('up-files')).not.toHaveTextContent('c.nc');
    expect(screen.getByTestId('up-removed-toast')).toHaveTextContent(FILE_REMOVED_NOTICE);
  });

  it('파일을 빼면 고른 프로젝트도 함께 내린다 — 고지가 말한 그대로다', async () => {
    await openModal(
      fakes({ projectRows: [{ projectId: 'PJ1', name: '낙동강 과제', type: '국가과제' }] }),
    );
    await dropFiles([makeFile('a.nc'), makeFile('c.nc')]);
    fireEvent.click(screen.getByTestId('reg-open'));
    await screen.findByTestId('reg-steps');
    // ⭑ ⟨WU-B3⟩ 연관 프로젝트·논문 표는 ③ 연결 안으로 들어왔다(PRD-12).
    fireEvent.click(screen.getByRole('button', { name: /^③/ }));
    await act(async () => {});
    fireEvent.click(screen.getByRole('button', { name: '+ 추가' }));
    await act(async () => {});
    expect(screen.getAllByTestId('reg-proj-row-name')).toHaveLength(1);

    fireEvent.click(screen.getByRole('button', { name: '조각 2개 모두 보기' }));
    fireEvent.click(screen.getByRole('button', { name: 'c.nc 빼기' }));
    await act(async () => {});

    fireEvent.click(screen.getByTestId('reg-open'));
    await screen.findByTestId('reg-steps');
    fireEvent.click(screen.getByTestId('reg-next'));
    await act(async () => {});
    expect(screen.queryAllByTestId('reg-proj-row-name')).toHaveLength(0);
  });

  it('마지막 파일을 빼면 놓기 전 상태로 돌아간다 — 등록 카드도 걷힌다', async () => {
    await openModal(fakes());
    await dropFiles([makeFile('a.nc')]);
    fireEvent.click(screen.getByTestId('reg-open'));
    await screen.findByTestId('reg-steps');
    fireEvent.click(screen.getByRole('button', { name: 'a.nc 빼기' }));
    await act(async () => {});
    expect(screen.queryByTestId('up-files')).toBeNull();
    expect(screen.queryByTestId('reg-steps')).toBeNull();
  });
});

/* ────────────────────────────────────────────────────────────────────────
 * ⑩ 접근 구역의 출처 문장
 * ──────────────────────────────────────────────────────────────────────── */

const DETAIL = {
  datasetId: DATASET_ID,
  name: '낙동강 강수 2025',
  projects: [],
  basicInfo: { files: { count: 1, totalSizeBytes: 1024 } },
  actions: { canDownload: true },
} as unknown as DatasetDetail;

describe('PRD-39 ⑩ — 접근 구역이 값의 출처를 말한다', () => {
  it('문면이 rev1 접근·다운로드 카드 축자다', () => {
    expect(ACCESS_ORIGIN_NOTE).toBe(
      '업로드할 때 정한 값이에요 · 올린 사람과 연구실 설정 권한자가 바꿀 수 있어요.',
    );
  });

  it('다운로드가 되는 사람에게 출처 문장이 함께 선다', () => {
    render(
      <MemoryRouter>
        <UsageSection detail={DETAIL} />
      </MemoryRouter>,
    );
    expect(screen.getByTestId('access-origin')).toHaveTextContent(ACCESS_ORIGIN_NOTE);
  });

  it('다운로드가 막힌 사람에게는 그 구역째 없다 — 없는 값을 설명하지 않는다', () => {
    const locked = { ...DETAIL, actions: { canDownload: false } } as unknown as DatasetDetail;
    render(
      <MemoryRouter>
        <UsageSection detail={locked} />
      </MemoryRouter>,
    );
    expect(screen.queryByTestId('access-origin')).toBeNull();
  });
});

/* ────────────────────────────────────────────────────────────────────────
 * ⑫ 행동 줄 바닥 고정 ＋ 할 일 안내 3문면
 *   rev1 근거 = `syncFoot()` · `#ufHint`
 * ──────────────────────────────────────────────────────────────────────── */

describe('PRD-39 ⑫ — 행동 줄이 바닥에 고정되고 할 일을 말한다', () => {
  it('안내가 정확히 3문면이고 rev1 `syncFoot()` 축자다', () => {
    expect(Object.keys(FOOT_HINTS)).toHaveLength(3);
    expect(FOOT_HINTS[1]).toBe('분류를 고르고 다음에서 데이터 정보를 입력하세요');
    expect(FOOT_HINTS[2]).toBe('데이터 정보를 입력하고 다음에서 연결하세요');
    expect(FOOT_HINTS[3]).toBe('연결을 마쳤으면 데이터셋을 만드세요');
  });

  it('단계를 옮기면 안내가 그 단계의 문면으로 바뀐다', async () => {
    await openModal(fakes({ ready: true }));
    await dropFiles([makeFile('a.nc')]);
    fireEvent.click(screen.getByTestId('reg-open'));
    await screen.findByTestId('reg-steps');
    expect(screen.getByTestId('reg-foot-hint')).toHaveTextContent(FOOT_HINTS[1]);
    fireEvent.click(screen.getByTestId('reg-next'));
    await act(async () => {});
    expect(screen.getByTestId('reg-foot-hint')).toHaveTextContent(FOOT_HINTS[2]);
    fireEvent.click(screen.getByTestId('reg-next'));
    await act(async () => {});
    expect(screen.getByTestId('reg-foot-hint')).toHaveTextContent(FOOT_HINTS[3]);
  });

  it('행동 줄이 **바닥 고정**이다 — CSS 가 `position: sticky` 를 건다', async () => {
    // jsdom 은 레이아웃을 재지 않는다. 고정은 스타일시트의 사실이라 원문을 실측한다.
    const css = (await import('../src/components/upload/upload.css?raw')).default as string;
    const block = css.slice(css.indexOf('.reg-actions'));
    expect(css).toContain('.reg-actions');
    expect(block.slice(0, block.indexOf('}'))).toMatch(/position:\s*sticky/);
    expect(block.slice(0, block.indexOf('}'))).toMatch(/bottom:\s*0/);
  });
});

/* ────────────────────────────────────────────────────────────────────────
 * HUD — 커서 위경도 역산. `mousemove` 1개 ＋ 역산 2개 ＋ 문면 2종 · 서버 왕복 0
 * ──────────────────────────────────────────────────────────────────────── */

const BOUNDS = { west: 126, south: 34, east: 130, north: 38 };
const RESULT = {
  imageUrl: 'https://viz.example/d/map.png',
  bounds: BOUNDS,
  legend: { palette: 'viridis', unit: 'mm', classes: [{ color: '#440154', min: 0, max: 5 }] },
} as unknown as RenderResult;

const IDENTITY = { scale: 1, x: 0, y: 0 };

describe('PRD-39 ⑥ 각주 — 커서 위경도 HUD', () => {
  it('역산 함수 두 개가 경계 네 숫자에서 좌표를 만든다', () => {
    expect(pvLonOf(0, 100, BOUNDS, IDENTITY)).toBeCloseTo(126, 6);
    expect(pvLonOf(100, 100, BOUNDS, IDENTITY)).toBeCloseTo(130, 6);
    expect(pvLatOf(0, 100, BOUNDS, IDENTITY)).toBeCloseTo(38, 6);
    expect(pvLatOf(100, 100, BOUNDS, IDENTITY)).toBeCloseTo(34, 6);
    // 밖은 지어내지 않는다
    expect(pvLonOf(-1, 100, BOUNDS, IDENTITY)).toBeUndefined();
    expect(pvLatOf(101, 100, BOUNDS, IDENTITY)).toBeUndefined();
  });

  it('배율·이동을 되돌린 뒤 역산한다 — 확대해도 좌표가 틀리지 않는다', () => {
    const zoomed = { scale: 2, x: -100, y: -100 };
    // 화면 100px = 층 좌표 (100 + 100) / 2 = 100 → 폭 100 의 100% = 동쪽 끝
    expect(pvLonOf(100, 100, BOUNDS, zoomed)).toBeCloseTo(130, 6);
  });

  it('처음에는 `커서를 지도 위로` 를 적는다', () => {
    render(<PreviewMap result={RESULT} />);
    expect(screen.getByTestId('preview-cursor-hud')).toHaveTextContent(HUD_IDLE);
    expect(HUD_IDLE).toBe('커서를 지도 위로');
  });

  it('커서가 지도 위에 오면 역산값을 적고 **출처를 라벨로 가른다**', () => {
    render(<PreviewMap result={RESULT} />);
    const viewport = screen.getByTestId('preview-viewport');
    Object.defineProperty(viewport, 'getBoundingClientRect', {
      value: () => ({ left: 0, top: 0, width: 100, height: 100 }),
      configurable: true,
    });
    fireEvent.mouseMove(viewport, { clientX: 50, clientY: 50 });
    const hud = screen.getByTestId('preview-cursor-hud');
    expect(hud).toHaveTextContent(HUD_SOURCE_LABEL);
    expect(HUD_SOURCE_LABEL).toBe('역산값');
    expect(hud).toHaveTextContent('128.0000');
    expect(hud).toHaveTextContent('36.0000');
  });

  it('경계 밖으로 나가면 `지도 밖` 이다 — 좌표를 지어내지 않는다', () => {
    render(<PreviewMap result={RESULT} />);
    const viewport = screen.getByTestId('preview-viewport');
    Object.defineProperty(viewport, 'getBoundingClientRect', {
      value: () => ({ left: 0, top: 0, width: 100, height: 100 }),
      configurable: true,
    });
    fireEvent.mouseMove(viewport, { clientX: 150, clientY: 50 });
    expect(screen.getByTestId('preview-cursor-hud')).toHaveTextContent(HUD_OUTSIDE);
    expect(HUD_OUTSIDE).toBe('지도 밖');
  });

  it('HUD 는 서버를 부르지 않는다 — 값 조회와 출처 라벨이 다르다', () => {
    // 존치 규칙(판정-1 ⓐ) — 값 조회는 그대로 있고 HUD 가 그것을 대체하지 않는다.
    expect(VALUE_SOURCE_LABEL).toBe('셀값');
    expect(HUD_SOURCE_LABEL).not.toBe(VALUE_SOURCE_LABEL);
  });
});
