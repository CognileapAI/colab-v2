// WU-A4 · PRD-15 · PRD-28 — **설명은 필수 칸이고, 그 칸은 세 줄이다.**
//
// rev1 축자 두 줄이 오라클이다 —
//   「연구자가 직접 쓴 맥락이 이 데이터의 값어치다.」
//   「필수로 만든 칸이 한 줄이면 **짧게 쓰라는 신호**가 된다.」
// 그래서 `필수` 배지와 **세 줄 높이**가 한 벌이다. 둘 중 하나만 하면 요구가 반만 선다.
// rev1 은 칸 아래 안내 문구를 **없앴다** — 그대로 따른다(설명하는 대신 칸을 키운다).
//
// PRD-28 은 같은 화면의 레이아웃이라 한 WU 로 묶였다 —
//   「좌우를 반씩 쓰던 것을 미리보기 2 : 입력 3 으로. 짧은 값 세 개(기간·좌표계·격자)는
//    한 줄에 넣었다. **2+1 로 갈리면 마지막 줄이 반쯤 빈다.**」
//
// ⚠ jsdom 은 실제 폭을 재지 않는다(레이아웃 엔진이 없다). 그래서 비율은 **선언**으로 잰다 —
//   화면이 붙인 클래스 ＋ 그 클래스의 `grid-template-columns` 값. 「2:3 이라고 적혀 있다」와
//   「2:3 으로 보인다」는 다른 주장이고, 여기서 증명할 수 있는 것은 앞의 것이다.
import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import { SessionProvider } from '../src/permission/session';
import { UploadEntry } from '../src/components/upload/UploadEntry';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { EMPTY_SUMMARY_NOTICE } from '../src/components/detail/DetailHeader';
import { FIXTURE_DETAILS } from '../src/components/detail/fixture';
import type { DatasetDetail, DetailSource } from '../src/components/detail/types';
import type {
  PreviewSource,
  ProjectSource,
  UploadSource,
  UploadSources,
} from '../src/components/upload/types';
import type { LineageSource, LineageSuggestionResponse } from '../src/components/lineage/types';
import type { CurrentAccount, Schemas } from '../src/api/client';
// **CSS 원문을 그대로 읽는다** — jsdom 은 폭을 재지 않으니 재는 것은 선언이다.
// (`?raw` 는 vite 가 제공한다 · `vite/client` 타입에 들어 있다.)
import CSS from '../src/components/upload/upload.css?raw';

const UPLOAD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0UP1';
const FILE_ID = '01JYZ9K7WQ3N8V4M2X6C5B0FI1';
const FILE_NAME = 'nakdong_precip_2025_Lv2.nc';

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

function fakes(): UploadSources {
  const status: Schemas['UploadStatus'] = {
    uploadId: UPLOAD_ID,
    files: [{ fileId: FILE_ID, fileName: FILE_NAME, kind: '본체', byteSize: 148_000_000 }],
    ready: true,
    renderable: true,
    metadataComplete: true,
    expiresAt: '2026-08-24T00:00:00Z',
    failure: null,
  } as Schemas['UploadStatus'];
  const upload: UploadSource = {
    async create(files) {
      return {
        uploadId: UPLOAD_ID,
        files: files.map((f) => ({
          fileId: FILE_ID, fileName: f.file.name, kind: f.kind, byteSize: f.file.size,
        })),
      };
    },
    async status() { return status; },
    async register() { return { datasetId: '01JYZ9K7WQ3N8V4M2X6C5B0DS1' }; },
    async attachGrid() { return []; },
  };
  const preview: PreviewSource = {
    async palettes() { return [{ palette: 'viridis', label: '비리디스' }]; },
    async createRender() { return { renderId: 'R1', status: '그리는 중', stage: '파일 읽는 중' } as never; },
    async getRender() { return { renderId: 'R1', status: '그리는 중', stage: '파일 읽는 중' } as never; },
  };
  const projects: ProjectSource = {
    async list() { return []; },
    async create(body) { return { projectId: '01JYZ9K7WQ3N8V4M2X6C5B0PR9', name: body.name, type: body.type }; },
  };
  const lineage: LineageSource = {
    async suggestions() {
      return {
        degraded: false,
        scope: { labId: '01JYZ9K7WQ3N8V4M2X6C5B0LB1', labName: '수자원순환연구실', searchedCount: 0 },
        rawDataLikely: false,
        suggestions: [],
      } as LineageSuggestionResponse;
    },
    async candidates() { return []; },
  };
  return { upload, preview, projects, lineage };
}

function makeFile(name: string, size = 148_000_000) {
  const f = new File(['x'], name, { type: 'application/octet-stream' });
  Object.defineProperty(f, 'size', { value: size });
  return f;
}

async function click(el: Element | null) {
  fireEvent.click(el as HTMLElement);
  await act(async () => {});
}

/** 파일 1건 → 등록 ① 이 열린 상태. */
async function openRegister() {
  render(
    <MemoryRouter initialEntries={['/datasets']}>
      <SessionProvider account={account()}>
        <UploadEntry sources={fakes()} />
      </SessionProvider>
    </MemoryRouter>,
  );
  await click(screen.getByTestId('gnb-upload'));
  await screen.findByTestId('upload-modal');
  fireEvent.change(screen.getByTestId('up-drop-input'), { target: { files: [makeFile(FILE_NAME)] } });
  await act(async () => {});
  await screen.findByTestId('up-files');
  await click(await screen.findByTestId('reg-open'));
  await screen.findByTestId('reg-steps');
}

/** CSS 선언 한 줄에서 `grid-template-columns` 값을 뽑는다. 없으면 `null` — 지어내지 않는다. */
function gridColumnsOf(selector: string): string | null {
  const block = new RegExp(`\\${selector}\\s*\\{[^}]*\\}`).exec(CSS);
  if (!block) return null;
  const decl = /grid-template-columns:\s*([^;}]+)/.exec(block[0]);
  return decl?.[1] ? decl[1].trim() : null;
}

function detailWith(summary: string | null): DatasetDetail {
  const base = Object.values(FIXTURE_DETAILS)[0];
  if (!base) throw new Error('픽스처가 비어 있다 — 대조군 없는 통과를 만들지 않는다.');
  return { ...base, summary };
}

function renderDetail(detail: DatasetDetail) {
  const source: DetailSource = { get: () => Promise.resolve(detail) };
  return render(
    <MemoryRouter initialEntries={[`/datasets/${detail.datasetId}`]}>
      <Routes>
        <Route path="/datasets/:datasetId" element={<DatasetDetailPage source={source} />} />
      </Routes>
    </MemoryRouter>,
  );
}

// ══════════════════════ PRD-15 · 필수 배지 · 세 줄 ══════════════════════════
describe('WU-A4 · PRD-15 — 설명은 필수 칸이고 세 줄이다', () => {
  it('설명 라벨에 `필수` 배지가 서고 `(선택)` 이 사라진다', async () => {
    await openRegister();
    const label = document.querySelector('label[for="reg-summary"]');
    expect(label).toBeTruthy();
    expect(label?.textContent).toContain('설명');
    expect(within(label as HTMLElement).getByText('필수')).toBeInTheDocument();
    expect(label?.textContent).not.toContain('(선택)');
  });

  it('설명 칸은 한 줄 입력이 아니라 **세 줄 높이 textarea** 다', async () => {
    await openRegister();
    const field = screen.getByTestId('reg-summary');
    // 「필수로 만든 칸이 한 줄이면 짧게 쓰라는 신호가 된다」 — 태그 자체가 요구다.
    expect(field.tagName).toBe('TEXTAREA');
    expect(field.getAttribute('rows')).toBe('3');
  });

  it('칸 아래 안내 문구를 두지 않는다 (rev1 이 없앴다)', async () => {
    await openRegister();
    const row = screen.getByTestId('reg-summary').closest('.form-row');
    expect(row).toBeTruthy();
    // 라벨·배지·입력 칸 말고 설명하는 문단이 없다 — 세 줄이 그 설명을 대신한다.
    expect(row?.querySelectorAll('p').length).toBe(0);
  });

  it('설명을 비운 채 데이터셋을 만들면 등록 ① 로 되돌리고 알린다', async () => {
    await openRegister();
    // 이름은 파일명에서 초안이 잡혀 있다 — 막히는 이유가 설명 하나임을 고정한다.
    expect((screen.getByTestId('reg-name') as HTMLInputElement).value.length).toBeGreaterThan(0);
    await click(screen.getByTestId('reg-next'));
    await click(screen.getByTestId('reg-next'));
    await click(screen.getByTestId('reg-done'));
    expect(screen.getByTestId('reg-summary-error')).toBeInTheDocument();
  });
});

// ══════════════════════ PRD-15 · 기존 빈 행의 상세 ══════════════════════════
describe('WU-A4 · PRD-15 — 설명이 빈 기존 행은 화면이 안내한다', () => {
  it('설명이 `null` 이면 안내 문면이 뜬다', async () => {
    renderDetail(detailWith(null));
    expect(await screen.findByTestId('dh-sum-empty')).toHaveTextContent(
      '설명이 아직 없어요 — 수정에서 채워 주세요',
    );
    expect(EMPTY_SUMMARY_NOTICE).toBe('설명이 아직 없어요 — 수정에서 채워 주세요');
  });

  it('안내가 떠도 화면이 깨지지 않는다 — 헤더의 다른 칸이 그대로 선다', async () => {
    renderDetail(detailWith(null));
    await screen.findByTestId('dh-sum-empty');
    expect(screen.getByTestId('detail-header')).toBeInTheDocument();
    expect(screen.getByTestId('dh-tags')).toBeInTheDocument();
    // 빈 설명 자리에 본문 블록을 같이 그리지 않는다 — 둘 중 하나만 선다.
    expect(screen.queryByTestId('dh-sum')).toBeNull();
  });

  it('설명이 있으면 안내가 없다 (대조군 — 빈 집합 통과 방지)', async () => {
    renderDetail(detailWith('낙동강 유역 강수량'));
    expect(await screen.findByTestId('dh-sum')).toHaveTextContent('낙동강 유역 강수량');
    expect(screen.queryByTestId('dh-sum-empty')).toBeNull();
  });
});

// ══════════════════════ PRD-28 · 2:3 · 짧은 값 3칸 ══════════════════════════
describe('WU-A4 · PRD-28 — 미리보기 2 : 입력 3, 짧은 값 세 개는 한 줄', () => {
  it('등록 화면이 좌우 두 칸으로 갈리고 비율이 2:3 이다', async () => {
    await openRegister();
    const split = screen.getByTestId('up-split');
    expect(split.querySelector('[data-testid="up-split-preview"]')).toBeTruthy();
    expect(split.querySelector('[data-testid="up-split-form"]')).toBeTruthy();
    // 「반씩」이 아니다 — 2fr 3fr 이 선언돼 있어야 한다.
    expect(gridColumnsOf('.up-split')).toBe('2fr 3fr');
  });

  it('기간·좌표계·격자가 한 줄 **세 칸**으로 선다', async () => {
    await openRegister();
    const row = screen.getByTestId('reg-short-row');
    expect(row.className).toContain('form-3');
    // 세 칸이다 — 2+1 로 갈리면 마지막 줄이 반쯤 빈다.
    expect(row.querySelectorAll(':scope > .form-row').length).toBe(3);
    expect(row.textContent).toContain('좌표계');
    expect(row.textContent).toContain('격자');
    expect(within(row).getByTestId('reg-period-start')).toBeInTheDocument();
    expect(within(row).getByTestId('reg-period-end')).toBeInTheDocument();
  });

  it('`.form-3` 은 세 칸 격자로 선언돼 있다', () => {
    expect(gridColumnsOf('.form-3')).toBe('repeat(3, minmax(0, 1fr))');
  });

  it('자동 칸에서 격자가 빠져 그 줄도 반쯤 비지 않는다', async () => {
    await openRegister();
    const auto = screen.getByTestId('reg-auto');
    expect(auto.querySelectorAll(':scope > .form-row').length).toBe(2);
    expect(auto.textContent).toContain('확장자');
    expect(auto.textContent).not.toContain('격자');
  });
});
