/**
 * `DL-1` — 상세 S-05 의 **데이터셋 삭제** 진입점·확인 모달·서버 왕복.
 *
 * 오라클 = 계약 산문 축자 (`contracts/seams/fe-core.yaml`) —
 *   `deleteDataset`  「소유자 또는 교수만. 파일·미리보기만 지우고 이름·주제·Lv·계보 관계·
 *                    프로젝트 연결·Verified 는 **남긴다**. 되돌리는 전이가 없다.」
 *   `DeletionImpact` 「이 데이터로 만든 데이터 N건의 계보에 **자리가 남아요**」 ·
 *                    「교수 승인이 붙은 데이터예요」 ·
 *                    「대기 중인 접근 요청 N건이 자동으로 닫혀요」
 *
 * ⛔ 사용자가 말한 「관계가 끊어진다」는 **정본과 반대**라 쓰지 않는다 (Ted 판정 ⓔ).
 * ⛔ 「휴지통」은 이 레포에 0건이다 — 글리프만 휴지통이고 글자는 「삭제」다.
 *
 * 모든 단언은 **대상 건수를 먼저 잰다** — 빈 집합 통과(green-by-skip)를 막는다.
 */
import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { SessionProvider } from '../src/permission/session';
import { FIXTURE_DETAILS } from '../src/components/detail/fixture';
import { apiDeletionSource } from '../src/components/detail/deletionSource';
import { DatasetGone, NotImplemented } from '../src/components/detail/types';
import type {
  DatasetDeletionSource,
  DatasetDetail,
  DeletionImpact,
  DetailSource,
} from '../src/components/detail/types';
import type { CurrentAccount, PermissionSwitchSet } from '../src/api/client';
import type { LineageGraph, LineageGraphSource } from '../src/components/lineage/graphTypes';

const ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA1';
const BASE = FIXTURE_DETAILS[ID] as DatasetDetail;

/** 삭제가 켜진 상세 — 판정은 **서버가 내려준 `canDelete` 하나**다 (P-7). */
const CAN_DELETE: DatasetDetail = {
  ...BASE,
  actions: { ...BASE.actions, canDelete: true },
};
const CANNOT_DELETE: DatasetDetail = {
  ...BASE,
  actions: { ...BASE.actions, canDelete: false },
};

const ALL_OFF: PermissionSwitchSet = {
  '업로드·편집': false,
  '프로젝트 생성': false,
  '승인 위임': false,
  '연구실 설정': false,
};

function account(): CurrentAccount {
  return {
    accountId: '01JYZ9K7WQ3N8V4M2X6C5B0U01',
    name: '호랑이',
    email: 'tiger@example.org',
    role: '연구원',
    permissions: ALL_OFF,
    labId: '01JYZ9K7WQ3N8V4M2X6C5B0L01',
    labName: '수문연구실',
  };
}

const NO_IMPACT: DeletionImpact = {
  derivedDatasetCount: 0,
  verified: false,
  pendingAccessRequestCount: 0,
};

/** 파급 세 칸이 전부 켜진 장면 — 모달이 말해야 하는 문장이 넷이 된다(활용 프로젝트 포함). */
const FULL_IMPACT: DeletionImpact = {
  derivedDatasetCount: 2,
  verified: true,
  pendingAccessRequestCount: 3,
};

function staticDetail(detail: DatasetDetail): DetailSource {
  return { async get() { return detail; } };
}

/** 파생 두 건이 선 계보 — 모달이 **이름까지** 말하는지 재는 재료다. */
const LINEAGE: LineageGraph = {
  datasetId: ID,
  lineageState: '확정',
  lineageConfirmedAt: null,
  unknownParents: false,
  nodes: [
    {
      kind: '이 데이터',
      datasetId: ID,
      name: BASE.name,
      processingLevel: 1,
      verified: false,
      navigable: false,
      bodyAccessible: true,
      deletedAt: null,
    },
    {
      kind: '파생',
      datasetId: '01JYZ9K7WQ3N8V4M2X6C5B0AA7',
      name: '홍수지수 2025',
      processingLevel: 3,
      verified: false,
      navigable: true,
      bodyAccessible: true,
      deletedAt: null,
    },
    {
      kind: '파생',
      datasetId: '01JYZ9K7WQ3N8V4M2X6C5B0AA8',
      name: '가뭄지수 2025',
      processingLevel: 3,
      verified: false,
      navigable: true,
      bodyAccessible: true,
      deletedAt: null,
    },
  ],
  edges: [],
  projectUseCount: 0,
  canEdit: false,
};

function lineageSource(graph: LineageGraph | null): LineageGraphSource {
  return {
    async get() {
      if (graph === null) throw new Error('못 읽었다');
      return graph;
    },
  };
}

/** 삭제 대역 — 부른 횟수를 센다. 「눌렀다」가 아니라 **「서버를 한 번 불렀다」**를 잰다. */
function spySource(opts: {
  impact?: DeletionImpact;
  impactError?: Error;
  removeError?: Error;
} = {}) {
  const calls = { impact: 0, remove: 0 };
  const source: DatasetDeletionSource = {
    async impact() {
      calls.impact += 1;
      if (opts.impactError) throw opts.impactError;
      return opts.impact ?? NO_IMPACT;
    },
    async remove() {
      calls.remove += 1;
      if (opts.removeError) throw opts.removeError;
    },
  };
  return { calls, source };
}

function mount(opts: {
  detail?: DatasetDetail;
  source?: DatasetDeletionSource;
  lineage?: LineageGraph | null;
} = {}) {
  return render(
    <MemoryRouter initialEntries={[`/datasets/${ID}`]}>
      <SessionProvider account={account()}>
        <Routes>
          <Route
            path="/datasets/:datasetId"
            element={
              <DatasetDetailPage
                source={staticDetail(opts.detail ?? CAN_DELETE)}
                lineageSource={lineageSource(opts.lineage === undefined ? LINEAGE : opts.lineage)}
                deletionSource={opts.source ?? spySource().source}
              />
            }
          />
          <Route path="/datasets" element={<div data-testid="catalog">카탈로그</div>} />
        </Routes>
      </SessionProvider>
    </MemoryRouter>,
  );
}

async function settle(name: string) {
  const heading = await screen.findByRole('heading', { level: 1, name });
  await act(async () => {});
  return heading;
}

async function click(el: Element | null | undefined) {
  fireEvent.click(el as HTMLElement);
  await act(async () => {});
}

async function openModal(opts: Parameters<typeof mount>[0] = {}) {
  mount(opts);
  await settle((opts.detail ?? CAN_DELETE).name);
  await click(screen.getByTestId('detail-delete-open'));
  return screen.getByTestId('detail-delete-modal');
}

afterEach(() => {
  vi.restoreAllMocks();
});

// ── ① · ② 진입점은 서버의 `canDelete` 로만 켜진다 ────────────────────────────

describe('삭제 진입점 — 판정은 서버가 한다 (P-7 · P-12)', () => {
  it('`canDelete: false` 면 진입점이 **DOM 에 아예 없다**', async () => {
    mount({ detail: CANNOT_DELETE });
    await settle(CANNOT_DELETE.name);
    // 비활성 버튼도 경고 토스트도 두지 않는다 — 꺼진 것은 사라진다
    expect(screen.queryAllByTestId('detail-delete-open')).toHaveLength(0);
    // 대조군: 같은 화면에 헤더는 서 있다(빈 화면을 통과로 세지 않는다)
    expect(screen.getAllByTestId('detail-header')).toHaveLength(1);
  });

  it('`canDelete: true` 면 헤더 안에 진입점이 **하나** 서고 글자는 「삭제」다', async () => {
    mount({});
    await settle(CAN_DELETE.name);
    const entry = screen.getAllByTestId('detail-delete-open');
    expect(entry).toHaveLength(1);
    expect(entry[0]).toHaveTextContent('삭제');
    // 정본 낱말은 「삭제」다 — 「휴지통」이라는 글자를 쓰지 않는다
    expect(entry[0]!.textContent ?? '').not.toContain('휴지통');
    expect(screen.getByTestId('detail-header').contains(entry[0]!)).toBe(true);
  });

  it('`업로드·편집` 스위치가 꺼져 있어도 삭제는 선다 — **다른 축**이다', async () => {
    // 이 계정은 네 스위치가 전부 꺼져 있다. 그래도 서버가 `canDelete` 를 켰으면 선다.
    mount({});
    await settle(CAN_DELETE.name);
    expect(screen.getAllByTestId('detail-delete-open')).toHaveLength(1);
    expect(screen.queryAllByTestId('detail-edit-open')).toHaveLength(0);
  });
});

// ── ③ 모달 문면 — 잔존 안내가 파급보다 앞 ───────────────────────────────────

describe('확인 모달 — 계약 산문 축자 (Ted 판정 ⓔ)', () => {
  it('열면 `role=dialog` 가 서고 파급을 **한 번** 조회한다', async () => {
    const spy = spySource({ impact: FULL_IMPACT });
    const modal = await openModal({ source: spy.source });
    expect(spy.calls.impact).toBe(1);
    expect(within(modal).getByRole('dialog')).toBeTruthy();
    expect(within(modal).getByRole('heading', { name: '이 데이터를 지울까요?' })).toBeTruthy();
  });

  it('**잔존 안내가 파급보다 앞에** 오고 문장이 축자다', async () => {
    const spy = spySource({ impact: FULL_IMPACT });
    const modal = await openModal({ source: spy.source });
    const keep = within(modal).getByTestId('detail-delete-keep');
    const impact = within(modal).getByTestId('detail-delete-impact');
    expect(keep.textContent).toContain(
      '이름·계보 관계·프로젝트 연결·승인 기록은 남아요. 파일과 미리보기만 지워져요. 되돌릴 수 없어요.',
    );
    // 「관계가 끊어진다」는 정본과 반대다 — 어디에도 없어야 한다
    expect(modal.textContent ?? '').not.toContain('끊어');
    // DOM 순서로 「먼저」를 잰다 — 두 노드의 문서 순서가 오라클이다
    expect(keep.compareDocumentPosition(impact) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('파급 네 줄이 계약 낱말 그대로 서고 **파생 이름까지** 말한다', async () => {
    const spy = spySource({ impact: FULL_IMPACT });
    const modal = await openModal({ source: spy.source });
    const items = within(modal).getAllByRole('listitem');
    // 파생 2 · Verified · 대기 3 · 활용 프로젝트(픽스처 상세가 든 건수)
    expect(items.length).toBeGreaterThanOrEqual(3);
    const text = items.map((li) => li.textContent ?? '').join('\n');
    expect(text).toContain('이 데이터로 만든 데이터 2건의 계보에 자리가 남아요');
    expect(text).toContain('교수 승인이 붙은 데이터예요');
    expect(text).toContain('대기 중인 접근 요청 3건이 자동으로 닫혀요');
    // 이름은 계보에서 온다 — 지어내지 않는다
    expect(text).toContain('홍수지수 2025');
    expect(text).toContain('가뭄지수 2025');
  });

  it('계보를 못 읽으면 **건수만** 말하고 이름을 지어내지 않는다', async () => {
    const spy = spySource({ impact: FULL_IMPACT });
    const modal = await openModal({ source: spy.source, lineage: null });
    const text = within(modal).getByTestId('detail-delete-impact').textContent ?? '';
    expect(text).toContain('이 데이터로 만든 데이터 2건의 계보에 자리가 남아요');
    expect(text).not.toContain('홍수지수 2025');
  });

  it('파급이 0 이면 그 줄이 아예 없다 — 「0건」이라고 적지 않는다', async () => {
    const spy = spySource({ impact: NO_IMPACT });
    const modal = await openModal({ source: spy.source });
    const text = within(modal).getByTestId('detail-delete-impact').textContent ?? '';
    expect(text).not.toContain('자리가 남아요');
    expect(text).not.toContain('자동으로 닫혀요');
    expect(text).not.toContain('교수 승인이 붙은');
  });
});

// ── ④ 확인 → 서버 왕복 → 목록 ───────────────────────────────────────────────

describe('삭제 확정', () => {
  it('「삭제」를 누르면 서버를 **한 번** 부르고 목록으로 간다 (토스트 없음)', async () => {
    const spy = spySource({ impact: NO_IMPACT });
    const modal = await openModal({ source: spy.source });
    await click(within(modal).getByTestId('detail-delete-confirm'));
    expect(spy.calls.remove).toBe(1);
    expect(screen.getAllByTestId('catalog')).toHaveLength(1);
    // 성공 토스트를 두지 않는다 (P-20) — 화면이 옮겨간 것이 결과다
    expect(screen.queryAllByRole('status')).toHaveLength(0);
  });

  it('「그대로 두기」는 서버를 부르지 않고 모달만 닫는다', async () => {
    const spy = spySource({ impact: NO_IMPACT });
    const modal = await openModal({ source: spy.source });
    await click(within(modal).getByTestId('detail-delete-cancel'));
    expect(spy.calls.remove).toBe(0);
    expect(screen.queryAllByTestId('detail-delete-modal')).toHaveLength(0);
    expect(screen.queryAllByTestId('catalog')).toHaveLength(0);
  });
});

// ── ⑤ · ⑥ 실패 두 갈래 ─────────────────────────────────────────────────────

describe('실패는 실패로 보인다', () => {
  it('삭제가 거절되면 **서버 문장**을 보이고 화면은 그대로다', async () => {
    const spy = spySource({
      impact: NO_IMPACT,
      removeError: new Error('데이터셋 삭제는 소유자 또는 교수만 할 수 있다 (Policy_데이터셋_상세 §6).'),
    });
    const modal = await openModal({ source: spy.source });
    await click(within(modal).getByTestId('detail-delete-confirm'));
    const err = screen.getByTestId('detail-delete-error');
    expect(err.textContent).toContain('소유자 또는 교수만');
    expect(err.getAttribute('role')).toBe('alert');
    // 모달을 닫지 않는다 — 닫으면 사람이 「지워졌나?」를 다시 눌러 확인한다
    expect(screen.getAllByTestId('detail-delete-modal')).toHaveLength(1);
    expect(screen.queryAllByTestId('catalog')).toHaveLength(0);
  });

  it('파급을 못 읽으면 삭제가 **비활성**이고 「다시 불러오기」가 선다', async () => {
    const spy = spySource({ impactError: new Error('삭제 파급을 불러오지 못했어요.') });
    const modal = await openModal({ source: spy.source });
    const confirm = within(modal).getByTestId('detail-delete-confirm') as HTMLButtonElement;
    expect(confirm.disabled).toBe(true);
    expect(within(modal).getByTestId('detail-delete-impact-failed').textContent)
      .toContain('삭제 파급을 불러오지 못했어요.');

    // 다시 불러오기 → 조회를 한 번 더 부른다
    expect(spy.calls.impact).toBe(1);
    await click(within(modal).getByTestId('detail-delete-impact-retry'));
    expect(spy.calls.impact).toBe(2);
  });
});

// ── ⑦ Esc · 초점 ───────────────────────────────────────────────────────────

describe('나가는 길', () => {
  it('Esc 로 닫히고 서버를 부르지 않는다', async () => {
    const spy = spySource({ impact: NO_IMPACT });
    await openModal({ source: spy.source });
    fireEvent.keyDown(document, { key: 'Escape' });
    await act(async () => {});
    expect(screen.queryAllByTestId('detail-delete-modal')).toHaveLength(0);
    expect(spy.calls.remove).toBe(0);
  });

  it('열리면 초점이 「그대로 두기」에 선다 — 되돌릴 수 없는 쪽이 아니다', async () => {
    const modal = await openModal({ source: spySource({ impact: NO_IMPACT }).source });
    expect(document.activeElement).toBe(within(modal).getByTestId('detail-delete-cancel'));
  });
});

// ── ⑧ `apiDeletionSource` 의 응답 → 예외 매핑 ───────────────────────────────

describe('apiDeletionSource — 응답 코드를 예외로 옮긴다', () => {
  const realFetch = globalThis.fetch;
  afterEach(() => {
    globalThis.fetch = realFetch;
  });

  function stub(status: number, body = '{"code":"X","message":"서버 문장"}') {
    globalThis.fetch = vi.fn(
      async () =>
        new Response(status === 204 ? null : body, {
          status,
          headers: { 'content-type': 'application/json' },
        }),
    ) as typeof fetch;
  }

  it('204 는 성공이다', async () => {
    stub(204);
    await expect(apiDeletionSource().remove(ID)).resolves.toBeUndefined();
  });

  it('404 → `DatasetGone` · 501 → `NotImplemented` · 403 → 서버 문장', async () => {
    const cases: [number, (e: unknown) => void][] = [
      [404, (e) => expect(e).toBeInstanceOf(DatasetGone)],
      [501, (e) => expect(e).toBeInstanceOf(NotImplemented)],
      [403, (e) => expect((e as Error).message).toBe('서버 문장')],
    ];
    expect(cases).toHaveLength(3);
    for (const [status, check] of cases) {
      stub(status);
      await apiDeletionSource()
        .remove(ID)
        .then(
          () => {
            throw new Error(`${status} 인데 성공으로 접혔다`);
          },
          check,
        );
    }
  });

  it('문장이 없는 실패에는 **지어내지 않은 기본 문구**가 선다', async () => {
    stub(500, '{"code":"X"}');
    await apiDeletionSource()
      .remove(ID)
      .then(
        () => {
          throw new Error('500 인데 성공으로 접혔다');
        },
        (e: unknown) => expect((e as Error).message).toBe('데이터를 지우지 못했어요.'),
      );

    stub(500, '{"code":"X"}');
    await apiDeletionSource()
      .impact(ID)
      .then(
        () => {
          throw new Error('500 인데 성공으로 접혔다');
        },
        (e: unknown) => expect((e as Error).message).toBe('삭제 파급을 불러오지 못했어요.'),
      );
  });
});
