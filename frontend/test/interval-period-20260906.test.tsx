// WU-A6 · PRD-17 · PRD-18 · PRD-35 — 관측 간격 · 기간 최소 단위 · 기간 표기.
//
// 오라클 세 줄 (라운드 파일 §5 WU-A6 축자)
//   ⑴ 단위 `분` 을 고르면 **연·월·일·시·분 다섯 칸**이 Start/End 각각 열린다 (PRD-18)
//   ⑵ 관측 간격은 숫자 한 칸 ＋ 단위 셀렉트이고 **비운 채 등록해도 막지 않는다** (PRD-17)
//   ⑶ 기간 뒤 괄호는 **한 함수**가 조립하고 상세·목록·등록 미리보기가 그것을 쓴다 (PRD-35)
//      — 간격이 비면 **빈 괄호가 없다**
//
// ⚠ **jsdom 은 폭을 안 잰다.** 여기서 재는 것은 칸의 **개수와 값**이고, 그것은 잴 수 있다.
import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import { SessionProvider } from '../src/permission/session';
import { UploadEntry } from '../src/components/upload/UploadEntry';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { FIXTURE_DETAILS } from '../src/components/detail/fixture';
import {
  EMPTY,
  INTERVAL_MISSING_NOTICE,
  formatInterval,
  formatPeriod,
  formatPeriodWithInterval,
} from '../src/components/detail/format';
import { assemble, partsFor, EMPTY_PARTS } from '../src/components/upload/periodParts';
import type { DatasetDetail, DetailSource } from '../src/components/detail/types';
import type {
  PreviewSource,
  ProjectSource,
  UploadSource,
  UploadSources,
} from '../src/components/upload/types';
import type { LineageSource, LineageSuggestionResponse } from '../src/components/lineage/types';
import type { CurrentAccount, Schemas } from '../src/api/client';

const UPLOAD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0UP1';
const FILE_ID = '01JYZ9K7WQ3N8V4M2X6C5B0FI1';
const FILE_NAME = 'nakdong_precip_2025_Lv2.nc';

/** 마지막 등록 요청 몸통 — 「화면이 무엇을 보냈는가」를 잰다. */
let sent: Record<string, unknown> | null = null;

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
    async register(body) {
      sent = body as unknown as Record<string, unknown>;
      return { datasetId: '01JYZ9K7WQ3N8V4M2X6C5B0DS1' };
    },
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

async function change(el: Element | null, value: string) {
  fireEvent.change(el as HTMLElement, { target: { value } });
  await act(async () => {});
}

async function openRegister() {
  sent = null;
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
  // ⭑ ⟨WU-B3⟩ 등록 카드가 ① 분류에서 열린다 — 이 시험들이 재는 칸은 ② 메타데이터 입력에
  // 있으므로 표시기로 한 단계 옮겨 둔다. **재는 것은 그대로다**(단계 이름만 바뀌었다).
  await click(screen.getByRole('button', { name: /^② / }));
}

/** ③ 까지 넘어가 `데이터셋 만들기` 를 누른다. */
async function submitRegister() {
  await change(screen.getByTestId('reg-summary'), '설명 한 줄');
  // ⭑ ⟨WU-B3⟩ ② 에서 ③ 까지는 한 걸음이다 — 프로젝트 카드가 ③ 안으로 들어왔다.
  await click(screen.getByTestId('reg-next'));
  await click(screen.getByTestId('reg-done'));
}

function detailWith(patch: Partial<DatasetDetail['basicInfo'] & object>): DatasetDetail {
  const base = Object.values(FIXTURE_DETAILS)[0];
  if (!base || !base.basicInfo) throw new Error('픽스처가 비어 있다 — 대조군 없는 통과를 만들지 않는다.');
  return { ...base, basicInfo: { ...base.basicInfo, ...patch } };
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

// ═══════════════ PRD-18 · 고른 단위까지만 칸이 열린다 ════════════════════════
describe('WU-A6 · PRD-18 — 최소 단위가 여는 칸', () => {
  it('단위를 안 고르면 **종전 날짜 칸 두 개** 그대로다 (기존 행이 그 상태다)', async () => {
    await openRegister();
    expect(screen.getByTestId('reg-period-start')).toBeInTheDocument();
    expect(screen.getByTestId('reg-period-end')).toBeInTheDocument();
    expect(screen.queryByTestId('reg-period-start-parts')).toBeNull();
  });

  it('단위 `일` 을 고르면 연·월·일 **세 칸**만 열린다', async () => {
    await openRegister();
    await change(screen.getByTestId('reg-period-granularity'), '일');
    const row = screen.getByTestId('reg-period-start-parts');
    expect(within(row).getAllByRole('textbox')).toHaveLength(3);
    for (const key of ['year', 'month', 'day']) {
      expect(screen.getByTestId(`reg-period-start-${key}`)).toBeInTheDocument();
    }
    expect(screen.queryByTestId('reg-period-start-hour')).toBeNull();
  });

  it('단위 `분` 이면 **다섯 칸**이 Start/End 각각 열린다 (docx `D-2-1` 축자)', async () => {
    await openRegister();
    await change(screen.getByTestId('reg-period-granularity'), '분');
    for (const side of ['start', 'end']) {
      const row = screen.getByTestId(`reg-period-${side}-parts`);
      expect(within(row).getAllByRole('textbox')).toHaveLength(5);
      expect(screen.queryByTestId(`reg-period-${side}-second`)).toBeNull();
    }
  });

  it('단위를 고르면 종전 날짜 칸 두 개는 **사라진다** — 두 입력 방식이 겹치지 않는다', async () => {
    await openRegister();
    await change(screen.getByTestId('reg-period-granularity'), '분');
    expect(screen.queryByTestId('reg-period-start')).toBeNull();
    expect(screen.queryByTestId('reg-period-end')).toBeNull();
  });

  it('`partsFor` 는 6값 전부에 자리 수를 낸다 — 화면 셀렉트와 규칙이 갈리지 않는다', () => {
    const expected: Record<string, number> = { 년: 1, 월: 2, 일: 3, 시: 4, 분: 5, 초: 6 };
    for (const [unit, n] of Object.entries(expected)) {
      expect(partsFor(unit)).toHaveLength(n);
    }
    expect(partsFor('')).toHaveLength(0);
  });
});

// ═══════════════ PRD-18 · 비운 하위 자리는 저장 때 채워진다 ══════════════════
describe('WU-A6 · PRD-18 — 조립', () => {
  it('열지 않은 하위 자리를 채워 `date-time` 하나를 만든다', () => {
    const parts = { ...EMPTY_PARTS, year: '2025', month: '6', day: '1' };
    expect(assemble(parts, '일')).toBe('2025-06-01T00:00:00Z');
  });

  it('시·분·초는 0 으로 채우고 **월·일은 01** 이다 — `2025-00-00` 은 시각이 아니다', () => {
    expect(assemble({ ...EMPTY_PARTS, year: '2025' }, '년')).toBe('2025-01-01T00:00:00Z');
  });

  it('연이 비면 기간이 없다 — 연 없는 월은 시각이 아니다', () => {
    expect(assemble({ ...EMPTY_PARTS, month: '06' }, '월')).toBeNull();
  });

  it('등록 요청이 조립된 시각값 ＋ `granularity` 를 싣는다', async () => {
    await openRegister();
    await change(screen.getByTestId('reg-period-granularity'), '분');
    await change(screen.getByTestId('reg-period-start-year'), '2020');
    await change(screen.getByTestId('reg-period-start-month'), '05');
    await change(screen.getByTestId('reg-period-start-day'), '01');
    await submitRegister();
    // ⭑ **⟨WU-B3 · PRD-40 판정 ⓐ⟩ 종료를 비우면 저장은 `period_end = period_start` 다.**
    //   화면에서만 비고, 「한 시점」이 `null`(무기한·진행 중)과 갈리게 된 자리다.
    expect(sent?.period).toEqual({
      start: '2020-05-01T00:00:00Z',
      end: '2020-05-01T00:00:00Z',
      granularity: '분',
    });
  });
});

// ═══════════════════ PRD-17 · 관측 간격 입력 ════════════════════════════════
describe('WU-A6 · PRD-17 — 관측 간격은 선택 입력이다', () => {
  it('숫자 칸의 placeholder 가 rev1 축자다', async () => {
    await openRegister();
    expect(screen.getByTestId('reg-interval-value')).toHaveAttribute(
      'placeholder',
      '예: 10분 · 1시간 · 1일',
    );
  });

  it('단위 셀렉트가 `초·분·시·일·월·년` 6값을 연다 (＋ 안 고른 상태)', async () => {
    await openRegister();
    const sel = screen.getByTestId('reg-interval-unit') as HTMLSelectElement;
    expect([...sel.options].map((o) => o.value)).toEqual(['', '초', '분', '시', '일', '월', '년']);
  });

  it('`10` ＋ `분` 이 두 칸 구조로 나간다 — **표시 문자열을 보내지 않는다**', async () => {
    await openRegister();
    await change(screen.getByTestId('reg-interval-value'), '10');
    await change(screen.getByTestId('reg-interval-unit'), '분');
    await submitRegister();
    expect(sent?.observationInterval).toEqual({ value: 10, unit: '분' });
  });

  it('비운 채 등록하면 **막지 않고** 열쇠도 싣지 않는다 (⛔ 등록 게이트가 아니다)', async () => {
    await openRegister();
    await submitRegister();
    expect(sent).not.toBeNull();
    expect(sent).not.toHaveProperty('observationInterval');
  });

  it('반쪽이면 경고를 세우되 **막지는 않는다** — 400 의 문구는 서버 봉투가 갖는다', async () => {
    await openRegister();
    await change(screen.getByTestId('reg-interval-value'), '10');
    expect(screen.getByTestId('reg-interval-half')).toBeInTheDocument();
    await submitRegister();
    // 화면이 조용히 버리지 않는다 — 반쪽 그대로 나가 서버가 판정한다.
    expect(sent?.observationInterval).toEqual({ value: 10, unit: null });
  });
});

// ═══════════════════ PRD-35 · 기간 표기 한 함수 ═════════════════════════════
describe('WU-A6 · PRD-35 — 기간 뒤 괄호는 한 곳에서 조립한다', () => {
  const period = {
    start: '2020-05-01T00:00:00Z',
    end: '2020-05-01T03:00:00Z',
    granularity: '분',
  };

  it('목업 축자 — `2020-05-01 00:00 ~ 03:00 (10분)`', () => {
    expect(formatPeriodWithInterval(period, { value: 10, unit: '분' })).toBe(
      '2020-05-01 00:00 ~ 03:00 (10분)',
    );
  });

  it('간격이 비면 **빈 괄호가 없다**', () => {
    expect(formatPeriodWithInterval(period, null)).toBe('2020-05-01 00:00 ~ 03:00');
    expect(formatPeriodWithInterval(period, null)).not.toContain('(');
  });

  it('반쪽 간격도 괄호를 그리지 않는다 — 화면이 `10` 만 적지 않는다', () => {
    expect(formatInterval({ value: 10, unit: null })).toBeNull();
    expect(formatPeriodWithInterval(period, { value: 10, unit: null })).not.toContain('(');
  });

  it('단위 `일` 이면 시·분·초를 노출하지 않는다 (PRD-18 수용 기준)', () => {
    expect(
      formatPeriod({
        start: '2025-06-01T00:00:00Z',
        end: '2025-06-30T00:00:00Z',
        granularity: '일',
      }),
    ).toBe('2025-06-01 ~ 2025-06-30');
  });

  it('granularity 가 `null` 이면 **종전 표기 그대로**다 — 재선택이 없다', () => {
    expect(
      formatPeriod({ start: '2025-06-01T00:00:00Z', end: '2025-09-30T00:00:00Z', granularity: null }),
    ).toBe('2025-06 ~ 09');
  });

  it('기간이 없으면 간격이 있어도 빈 표시 하나다 — `— (10분)` 을 만들지 않는다', () => {
    expect(formatPeriodWithInterval(null, { value: 10, unit: '분' })).toBe(EMPTY);
  });
});

// ═══════════ PRD-17·35 · 상세와 목록이 같은 규칙을 쓴다 ══════════════════════
describe('WU-A6 — 상세 기본 정보', () => {
  it('간격이 있으면 기간 칸이 괄호를 함께 그린다', async () => {
    renderDetail(
      detailWith({
        period: { start: '2020-05-01T00:00:00Z', end: '2020-05-01T03:00:00Z', granularity: '분' },
        observationInterval: { value: 10, unit: '분' },
      }),
    );
    const cell = await screen.findByTestId('ig-기간');
    expect(cell).toHaveTextContent('2020-05-01 00:00 ~ 03:00 (10분)');
    // 값이 있으면 「미기재」가 서지 않는다 — 대조군.
    expect(screen.queryByTestId('ig-interval-missing')).toBeNull();
  });

  it('간격이 `null` 이면 「관측 간격 미기재」가 서고 화면이 안 깨진다', async () => {
    renderDetail(detailWith({ observationInterval: null }));
    expect(await screen.findByTestId('ig-interval-missing')).toHaveTextContent(
      INTERVAL_MISSING_NOTICE,
    );
    expect(INTERVAL_MISSING_NOTICE).toBe('관측 간격 미기재');
    // 기본 정보는 **아홉 칸 그대로**다 — 칸을 늘리지 않았다 (`Policy_데이터셋_상세 §5`).
    expect(screen.getByTestId('basic-info').querySelectorAll('.ig')).toHaveLength(9);
    expect(screen.getByTestId('ig-기간').textContent).not.toContain('()');
  });
});

describe('WU-A6 — 등록 미리보기 (PRD-35 세 번째 자리)', () => {
  it('사람이 적은 값이 상세와 **같은 문면**으로 미리 보인다', async () => {
    await openRegister();
    await change(screen.getByTestId('reg-period-granularity'), '분');
    await change(screen.getByTestId('reg-period-start-year'), '2020');
    await change(screen.getByTestId('reg-period-start-month'), '05');
    await change(screen.getByTestId('reg-period-start-day'), '01');
    await change(screen.getByTestId('reg-period-end-year'), '2020');
    await change(screen.getByTestId('reg-period-end-month'), '05');
    await change(screen.getByTestId('reg-period-end-day'), '01');
    await change(screen.getByTestId('reg-period-end-hour'), '03');
    await change(screen.getByTestId('reg-interval-value'), '10');
    await change(screen.getByTestId('reg-interval-unit'), '분');
    expect(screen.getByTestId('reg-period-preview')).toHaveTextContent(
      '2020-05-01 00:00 ~ 03:00 (10분)',
    );
  });

  it('간격을 비우면 미리보기에도 **빈 괄호가 없다**', async () => {
    await openRegister();
    await change(screen.getByTestId('reg-period-granularity'), '일');
    await change(screen.getByTestId('reg-period-start-year'), '2025');
    await change(screen.getByTestId('reg-period-start-month'), '06');
    await change(screen.getByTestId('reg-period-start-day'), '01');
    expect(screen.getByTestId('reg-period-preview').textContent).not.toContain('(');
  });
});
