/**
 * WU-A3 — 상세 수정 UI (**현행 필드만** · PRD-22 · `dev-package/prd/rounds/R-A-3-frontend.md §2`).
 *
 * 오라클 = 그 파일의 수용 기준 넷 ＋ `DatasetUpdate` 계약이 **지금 받는 열쇠**
 * (`contracts/seams/fe-core.yaml:2794` · 생성물 `frontend/src/generated/fe-core.ts`).
 *
 * ⛔ 이 라운드가 여는 칸은 **다섯**이다 — 이름 · 설명 · 원천 표기 · 좌표계 · 기간.
 *    `주제`(`topic`)는 표시만 하고 편집 진입이 없다(R-B PRD-01 이 `분류` 로 갈아친다).
 *    R-B 가 더하는 칸(분류·유형·가공 단계·공개 범위·관측 간격…)은 여기서 그리지 않는다.
 *
 * 모든 단언은 **대상 건수를 먼저 잰다** — 빈 집합 통과(green-by-skip)를 막는다.
 */
import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { SessionProvider } from '../src/permission/session';
import { FIXTURE_DETAILS } from '../src/components/detail/fixture';
import type { CurrentAccount, PermissionSwitchSet } from '../src/api/client';
import type { DatasetDetail, DetailSource } from '../src/components/detail/types';
import type { DatasetUpdateSource } from '../src/components/detail/updateSource';
import { apiDatasetUpdateSource } from '../src/components/detail/updateSource';
import { applyDraft, toDraft, toPatch } from '../src/components/detail/editFields';

const OPEN_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA1'; // 목업 기본 장면 — 다섯 칸이 전부 차 있다
const BASE = FIXTURE_DETAILS[OPEN_ID] as DatasetDetail;

/** 값이 전부 NULL 인 상세 — 「빈 칸으로 열린다」를 재는 장면 */
const NULLED: DatasetDetail = {
  ...BASE,
  summary: null,
  basicInfo: { ...BASE.basicInfo!, crs: null, period: null, sourceLabel: null },
};

const ALL_OFF: PermissionSwitchSet = {
  '업로드·편집': false,
  '프로젝트 생성': false,
  '승인 위임': false,
  '연구실 설정': false,
};

function account(permissions: PermissionSwitchSet): CurrentAccount {
  return {
    accountId: '01JYZ9K7WQ3N8V4M2X6C5B0U01',
    name: '호랑이',
    email: 'tiger@example.org',
    role: '연구원',
    permissions,
    labId: '01JYZ9K7WQ3N8V4M2X6C5B0L01',
    labName: '수문연구실',
  };
}

const CAN_EDIT: PermissionSwitchSet = { ...ALL_OFF, '업로드·편집': true };

function staticSource(detail: DatasetDetail): DetailSource {
  return { async get() { return detail; } };
}

/** 저장 왕복을 손으로 붙잡는 대역 — 낙관적 갱신이 응답 **전에** 보이는지 재려면 필요하다. */
function deferredUpdateSource(result?: DatasetDetail) {
  const calls: { datasetId: string; patch: Record<string, unknown> }[] = [];
  let release: (() => void) | null = null;
  let reject: ((e: Error) => void) | null = null;
  const source: DatasetUpdateSource = {
    update(datasetId, patch) {
      calls.push({ datasetId, patch: patch as Record<string, unknown> });
      return new Promise<DatasetDetail>((resolve, rej) => {
        release = () => resolve(result ?? { ...BASE });
        reject = rej;
      });
    },
  };
  return {
    calls,
    source,
    async settle() {
      release?.();
      await act(async () => {});
    },
    async fail(message: string) {
      reject?.(new Error(message));
      await act(async () => {});
    },
  };
}

function mount(opts: {
  detail?: DatasetDetail;
  permissions?: PermissionSwitchSet;
  updateSource?: DatasetUpdateSource;
}) {
  return render(
    <MemoryRouter initialEntries={[`/datasets/${OPEN_ID}`]}>
      <SessionProvider account={account(opts.permissions ?? CAN_EDIT)}>
        <Routes>
          <Route
            path="/datasets/:datasetId"
            element={
              <DatasetDetailPage
                source={staticSource(opts.detail ?? BASE)}
                updateSource={opts.updateSource}
              />
            }
          />
          <Route path="/datasets" element={<div>카탈로그</div>} />
        </Routes>
      </SessionProvider>
    </MemoryRouter>,
  );
}

async function settle(name: string) {
  return screen.findByRole('heading', { level: 1, name });
}

async function click(el: Element | null) {
  fireEvent.click(el as HTMLElement);
  await act(async () => {});
}

async function openForm(opts: Parameters<typeof mount>[0] = {}) {
  mount(opts);
  await settle((opts.detail ?? BASE).name);
  await click(screen.getByTestId('detail-edit-open'));
  return screen.getByTestId('detail-edit-form');
}

function field(form: HTMLElement, testId: string): HTMLInputElement {
  return within(form).getByTestId(testId) as HTMLInputElement;
}

async function type(el: HTMLElement, value: string) {
  fireEvent.change(el, { target: { value } });
  await act(async () => {});
}

// ── 수용 기준 ① 권한 없으면 진입점이 없다 ─────────────────────────────────────

describe('§2 WU-A3 — `수정` 진입점은 `업로드·편집` 이 켜진 사람에게만 (P-12)', () => {
  it('스위치가 켜졌으면 상세 헤더에 `수정` 진입점이 **하나** 있다', async () => {
    mount({});
    await settle(BASE.name);
    const entry = screen.getAllByTestId('detail-edit-open');
    expect(entry).toHaveLength(1);
    expect(entry[0]).toHaveTextContent('수정');
    // 헤더 안에 선다 — 본문 어딘가가 아니다 (`§8` 헤더 우측 자리)
    expect(screen.getByTestId('detail-header').contains(entry[0]!)).toBe(true);
  });

  it('스위치가 꺼졌으면 DOM 에서 **사라진다** — 비활성 버튼을 두지 않는다', async () => {
    mount({ permissions: ALL_OFF });
    await settle(BASE.name);
    expect(screen.queryAllByTestId('detail-edit-open')).toHaveLength(0);
    expect(screen.queryByText('수정')).toBeNull();
  });
});

// ── 수용 기준 ② 이름만 바꾸면 이름만 간다 ─────────────────────────────────────

describe('§2 WU-A3 — 부분 수정: 보내지 않은 열쇠는 안 건드린다', () => {
  it('이름만 고쳐 저장하면 요청 몸통의 열쇠가 `name` **하나**다', async () => {
    const up = deferredUpdateSource();
    const form = await openForm({ updateSource: up.source });
    await type(field(form, 'edit-name'), '낙동강 유역 강우 (2025) 개정');
    await click(screen.getByTestId('detail-edit-save'));
    expect(up.calls).toHaveLength(1);
    expect(Object.keys(up.calls[0]!.patch)).toEqual(['name']);
    expect(up.calls[0]!.patch['name']).toBe('낙동강 유역 강우 (2025) 개정');
    expect(up.calls[0]!.datasetId).toBe(OPEN_ID);
    await up.settle();
  });

  it('아무것도 안 고치고 저장하면 **빈 몸통**이라 나머지 값이 그대로다', async () => {
    const up = deferredUpdateSource();
    const form = await openForm({ updateSource: up.source });
    expect(field(form, 'edit-name').value).toBe(BASE.name);
    await click(screen.getByTestId('detail-edit-save'));
    expect(up.calls).toHaveLength(1);
    expect(Object.keys(up.calls[0]!.patch)).toHaveLength(0);
    await up.settle();
  });

  it('`toPatch` 는 바뀐 칸만 담고 비운 칸은 `null` 로 담는다 (생략 ≠ null)', () => {
    const draft = toDraft(BASE);
    expect(Object.keys(toPatch(BASE, draft))).toHaveLength(0);
    expect(toPatch(BASE, { ...draft, crs: '' })).toEqual({ crs: null });
    expect(toPatch(BASE, { ...draft, summary: '고친 설명' })).toEqual({ summary: '고친 설명' });
    // 기간은 두 칸이 한 값이다 — 한쪽만 바뀌어도 `period` 하나로 나간다
    expect(Object.keys(toPatch(BASE, { ...draft, periodEnd: '' }))).toEqual(['period']);
    expect(toPatch(BASE, { ...draft, periodStart: '' })).toEqual({ period: null });
  });
});

// ── 수용 기준 ④ 주제는 읽기 전용 · R-B 필드는 그리지 않는다 ───────────────────

describe('§2 WU-A3 — 여는 칸은 다섯뿐이다 (topic 읽기 전용 · R-B 필드 없음)', () => {
  it('폼의 입력 칸은 이름·설명·원천 표기·좌표계·기간(시작·끝) **여섯 개**다', async () => {
    const form = await openForm();
    const inputs = within(form).getAllByRole('textbox');
    const dates = form.querySelectorAll('input[type="date"]');
    expect(inputs.length + dates.length).toBe(6);
    for (const id of ['edit-name', 'edit-summary', 'edit-sourceLabel', 'edit-crs',
                      'edit-period-start', 'edit-period-end']) {
      expect(within(form).getAllByTestId(id)).toHaveLength(1);
    }
  });

  it('`주제` 는 상세에 **표시되지만** 편집 칸이 없다', async () => {
    const form = await openForm();
    // 표시는 남는다 — 헤더 칩
    expect(screen.getByTestId('dh-tags').textContent).toContain(BASE.topic as string);
    // 편집 진입은 없다
    expect(within(form).queryByTestId('edit-topic')).toBeNull();
    expect(within(form).queryByText('주제')).toBeNull();
  });

  it('R-B 가 더할 칸을 미리 그리지 않는다', async () => {
    const form = await openForm();
    for (const label of ['분류', '유형', '가공 단계', '공개 범위', '관측 간격', '변수']) {
      expect(within(form).queryByText(label)).toBeNull();
    }
  });
});

// ── 기존 데이터 — NULL 은 빈 칸으로 열린다 ────────────────────────────────────

describe('§2 WU-A3 — NULL 인 칸은 빈 칸으로 열린다', () => {
  it('설명·원천 표기·좌표계·기간이 NULL 이면 전부 빈 문자열이다', async () => {
    const form = await openForm({ detail: NULLED });
    const empties = ['edit-summary', 'edit-sourceLabel', 'edit-crs',
                     'edit-period-start', 'edit-period-end'];
    expect(empties).toHaveLength(5);
    for (const id of empties) expect(field(form, id).value).toBe('');
    // 이름은 NULL 이 될 수 없다 — 그대로 찬다
    expect(field(form, 'edit-name').value).toBe(NULLED.name);
  });

  it('값이 있으면 그 값이 그대로 열린다', async () => {
    const form = await openForm();
    expect(field(form, 'edit-summary').value).toBe(BASE.summary);
    expect(field(form, 'edit-sourceLabel').value).toBe(BASE.basicInfo!.sourceLabel);
    expect(field(form, 'edit-crs').value).toBe(BASE.basicInfo!.crs);
    expect(field(form, 'edit-period-start').value).toBe('2025-06-01');
    expect(field(form, 'edit-period-end').value).toBe('2025-09-30');
  });
});

// ── 낙관적 갱신 ＋ 저장 왕복 ──────────────────────────────────────────────────

describe('§2 WU-A3 — 낙관적 갱신과 저장 왕복', () => {
  it('응답 **전에** 바뀐 이름이 서고, 응답이 오면 서버 값으로 갈아탄다', async () => {
    const served: DatasetDetail = { ...BASE, name: '서버가 확정한 이름' };
    const up = deferredUpdateSource(served);
    const form = await openForm({ updateSource: up.source });
    await type(field(form, 'edit-name'), '내가 적은 이름');
    await click(screen.getByTestId('detail-edit-save'));
    // 낙관 — 아직 응답이 오지 않았는데 화면이 먼저 바뀐다
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('내가 적은 이름');
    await up.settle();
    // 왕복 — 서버가 돌려준 상세가 이긴다
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('서버가 확정한 이름');
    expect(screen.queryByTestId('detail-edit-form')).toBeNull();
  });

  it('설명·원천 표기·좌표계도 서버 응답으로 갈아탄다', async () => {
    const served: DatasetDetail = {
      ...BASE,
      summary: '고친 설명',
      basicInfo: { ...BASE.basicInfo!, sourceLabel: 'ERA5 재분석', crs: 'EPSG:4326' },
    };
    const up = deferredUpdateSource(served);
    const form = await openForm({ updateSource: up.source });
    await type(field(form, 'edit-summary'), '고친 설명');
    await type(field(form, 'edit-crs'), 'EPSG:4326');
    await click(screen.getByTestId('detail-edit-save'));
    expect(Object.keys(up.calls[0]!.patch).sort()).toEqual(['crs', 'summary']);
    await up.settle();
    const info = screen.getByTestId('basic-info');
    expect(info.textContent).toContain('EPSG:4326');
    expect(info.textContent).toContain('ERA5 재분석');
    expect(screen.getByTestId('dh-sum').textContent).toContain('고친 설명');
  });

  it('저장이 실패하면 **낙관값을 되돌리고** 서버 문구를 그대로 보인다', async () => {
    const up = deferredUpdateSource();
    const form = await openForm({ updateSource: up.source });
    await type(field(form, 'edit-name'), '실패할 이름');
    await click(screen.getByTestId('detail-edit-save'));
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('실패할 이름');
    await up.fail('데이터셋 이름을 적어 주세요.');
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe(BASE.name);
    expect(screen.getByTestId('detail-edit-error').textContent).toContain(
      '데이터셋 이름을 적어 주세요.',
    );
  });

  it('빈 이름으로는 저장하지 못한다 — 요청을 보내지 않는다 (ERR-001 문구)', async () => {
    const up = deferredUpdateSource();
    const form = await openForm({ updateSource: up.source });
    await type(field(form, 'edit-name'), '   ');
    await click(screen.getByTestId('detail-edit-save'));
    expect(up.calls).toHaveLength(0);
    expect(screen.getByTestId('detail-edit-error').textContent).toContain(
      '데이터셋 이름을 적어 주세요.',
    );
  });

  it('`취소` 는 아무것도 보내지 않고 값을 되돌린다', async () => {
    const up = deferredUpdateSource();
    const form = await openForm({ updateSource: up.source });
    await type(field(form, 'edit-name'), '버릴 이름');
    await click(screen.getByTestId('detail-edit-cancel'));
    expect(up.calls).toHaveLength(0);
    expect(screen.queryByTestId('detail-edit-form')).toBeNull();
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe(BASE.name);
    await click(screen.getByTestId('detail-edit-open'));
    expect(field(screen.getByTestId('detail-edit-form'), 'edit-name').value).toBe(BASE.name);
  });
});

// ── 생성된 클라이언트로 나가는가 (계약 op `updateDataset`) ────────────────────

describe('§2 WU-A3 — 저장은 생성물 클라이언트의 `updateDataset` 으로 나간다', () => {
  it('PATCH /datasets/{datasetId} 로 몸통을 그대로 보낸다', async () => {
    const seen: { url: string; method: string; body: string }[] = [];
    const original = globalThis.fetch;
    globalThis.fetch = vi.fn(async (input: RequestInfo | URL) => {
      const req = input as Request;
      seen.push({ url: req.url, method: req.method, body: await req.clone().text() });
      return new Response(JSON.stringify(BASE), {
        status: 200,
        headers: { 'content-type': 'application/json' },
      });
    }) as typeof fetch;
    try {
      const detail = await apiDatasetUpdateSource().update(OPEN_ID, { name: '고친 이름' });
      expect(seen).toHaveLength(1);
      expect(seen[0]!.method).toBe('PATCH');
      expect(seen[0]!.url).toContain(`/api/v1/datasets/${OPEN_ID}`);
      expect(JSON.parse(seen[0]!.body)).toEqual({ name: '고친 이름' });
      expect(detail.datasetId).toBe(OPEN_ID);
    } finally {
      globalThis.fetch = original;
    }
  });

  it('서버가 거절하면 봉투의 `message` 를 그대로 올린다 — 화면이 문구를 짓지 않는다', async () => {
    const original = globalThis.fetch;
    globalThis.fetch = vi.fn(
      async () =>
        new Response(JSON.stringify({ message: '데이터셋 이름을 적어 주세요.' }), {
          status: 400,
          headers: { 'content-type': 'application/json' },
        }),
    ) as typeof fetch;
    try {
      await expect(apiDatasetUpdateSource().update(OPEN_ID, { name: '' })).rejects.toThrow(
        '데이터셋 이름을 적어 주세요.',
      );
    } finally {
      globalThis.fetch = original;
    }
  });
});

// ── 골격 재사용 — A4·A6·R-B 가 칸만 늘린다 ────────────────────────────────────

describe('§2 WU-A3 — 골격은 필드 표 하나로 늘어난다', () => {
  it('`applyDraft` 는 헤더 값과 기본 정보 값을 한 번에 반영한다', () => {
    const next = applyDraft(BASE, {
      ...toDraft(BASE),
      name: 'N',
      summary: 'S',
      sourceLabel: 'L',
      crs: 'C',
      periodStart: '2024-01-01',
      periodEnd: '',
    });
    expect(next.name).toBe('N');
    expect(next.summary).toBe('S');
    expect(next.basicInfo!.sourceLabel).toBe('L');
    expect(next.basicInfo!.crs).toBe('C');
    expect(next.basicInfo!.period).toEqual({ start: '2024-01-01T00:00:00Z', end: null });
    // 건드리지 않은 값은 그대로다
    expect(next.topic).toBe(BASE.topic);
    expect(next.processingLevel).toBe(BASE.processingLevel);
    expect(next.basicInfo!.variables).toEqual(BASE.basicInfo!.variables);
  });
});
