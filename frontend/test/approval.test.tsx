/**
 * 승인 처리 (WU-P6) — 화면 대비 시험.
 * 오라클 = `E-06_승인_처리/documents/Policy_승인_처리.md` (v1.7) 축자.
 *
 *   §8 상세 S-05 · 헤더      — 한 자리가 상태 × 보는 사람에 따라 **셋으로 갈린다**
 *   §8 상세 S-05 · 잠긴 상태 — 이름·요약·헤더 태그까지. 본문 대신 **잠김 안내 + 접근 요청 버튼**
 *   §1.3-5                   — 어디까지 보일지는 **화면마다 다르다**
 *   §5                       — 요청 사유 0~300자 **선택** · 취소 사유 0~120자 선택
 *   §1.5 / §8                — **Verified 배지는 표시 전용이고 누르는 곳이 아니다**
 *
 * **화면이 조건을 임의로 정하지 않는다** (P-7) — 세 자리 전부 서버가 내린 `actions` 로만 갈린다.
 */
// **새 의존성을 들이지 않는다 — 이미 있는 `fireEvent` 로 친다**
// (`test/auth.test.tsx:127` · `test/catalog.test.tsx` 선례).
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { FIXTURE_DETAILS } from '../src/components/detail/fixture';
import type { DatasetDetail, DetailSource } from '../src/components/detail/types';
import type { ApprovalSource } from '../src/components/approval/types';

const LOCKED_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA5'; // 목업 D-03 잠긴 상세
const OPEN_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA1';

function sourceOf(detail: DatasetDetail): DetailSource {
  return { get: async () => detail };
}

function detail(id: string, patch: Partial<DatasetDetail> = {}): DatasetDetail {
  const base = FIXTURE_DETAILS[id] as DatasetDetail;
  return { ...base, ...patch };
}

function stubApproval(over: Partial<ApprovalSource> = {}): ApprovalSource {
  return {
    requestAccess: vi.fn(async () => {}),
    requestVerification: vi.fn(async () => {}),
    approveVerification: vi.fn(async () => {}),
    cancelVerification: vi.fn(async () => {}),
    ...over,
  };
}

function renderDetail(d: DatasetDetail, approval: ApprovalSource = stubApproval()) {
  return render(
    <MemoryRouter initialEntries={[`/datasets/${d.datasetId}`]}>
      <Routes>
        <Route
          path="/datasets/:datasetId"
          element={<DatasetDetailPage source={sourceOf(d)} approvalSource={approval} />}
        />
      </Routes>
    </MemoryRouter>,
  );
}

const settle = (name: string) => screen.findByRole('heading', { level: 1, name });

// ── §8 잠긴 상태 — 본문 대신 잠김 안내 + 접근 요청 버튼 ───────────────────────

describe('§8 상세 · 잠긴 상태 — 요청은 여기서 한다', () => {
  it('잠긴 상세에 `접근 요청` 버튼이 선다 (카탈로그 행이 아니라 여기다)', async () => {
    const d = detail(LOCKED_ID, {
      bodyAccessible: false,
      accessRequestPending: false,
      actions: { ...detail(LOCKED_ID).actions, canRequestAccess: true },
    });
    renderDetail(d);
    await settle(d.name);
    expect(await screen.findByRole('button', { name: '접근 요청' })).toBeTruthy();
    // 잠겨도 이름·요약은 그대로 보인다 (P-13 · §1.3-5)
    expect(screen.getByText('이름과 요약까지만 보여요')).toBeTruthy();
  });

  it('사유는 **선택**이라 비운 채로 보낼 수 있다 (§5 「0~300자. 선택」)', async () => {
    const requestAccess = vi.fn(async () => {});
    const d = detail(LOCKED_ID, {
      bodyAccessible: false,
      accessRequestPending: false,
      actions: { ...detail(LOCKED_ID).actions, canRequestAccess: true },
    });
    renderDetail(d, stubApproval({ requestAccess }));
    await settle(d.name);
    fireEvent.click(screen.getByRole('button', { name: '접근 요청' }));
    const modal = await screen.findByRole('dialog');
    fireEvent.click(within(modal).getByRole('button', { name: '요청 보내기' }));
    await waitFor(() => expect(requestAccess).toHaveBeenCalledWith(d.datasetId, null));
  });

  it('사유를 적으면 그대로 실린다', async () => {
    const requestAccess = vi.fn(async () => {});
    const d = detail(LOCKED_ID, {
      bodyAccessible: false,
      accessRequestPending: false,
      actions: { ...detail(LOCKED_ID).actions, canRequestAccess: true },
    });
    renderDetail(d, stubApproval({ requestAccess }));
    await settle(d.name);
    fireEvent.click(screen.getByRole('button', { name: '접근 요청' }));
    const modal = await screen.findByRole('dialog');
    fireEvent.change(within(modal).getByRole('textbox'), { target: { value: '격자화 입력으로 쓰려고 해요' } });
    fireEvent.click(within(modal).getByRole('button', { name: '요청 보내기' }));
    await waitFor(() =>
      expect(requestAccess).toHaveBeenCalledWith(d.datasetId, '격자화 입력으로 쓰려고 해요'),
    );
  });

  it('사유 칸은 300자를 넘겨 받지 않는다 (§5)', async () => {
    const d = detail(LOCKED_ID, {
      bodyAccessible: false,
      accessRequestPending: false,
      actions: { ...detail(LOCKED_ID).actions, canRequestAccess: true },
    });
    renderDetail(d);
    await settle(d.name);
    fireEvent.click(screen.getByRole('button', { name: '접근 요청' }));
    const box = within(await screen.findByRole('dialog')).getByRole('textbox');
    expect(box.getAttribute('maxlength')).toBe('300');
  });

  it('요청을 보낸 뒤에는 **검토 대기 칩**이고 버튼이 사라진다 (계약 `createAccessRequest` 산문)', async () => {
    const d = detail(LOCKED_ID, {
      bodyAccessible: false,
      accessRequestPending: true,
      actions: { ...detail(LOCKED_ID).actions, canRequestAccess: true },
    });
    renderDetail(d);
    await settle(d.name);
    expect(await screen.findByText('검토 대기')).toBeTruthy();
    expect(screen.queryByRole('button', { name: '접근 요청' })).toBeNull();
  });
});

// ── §8 헤더 — 한 자리가 셋으로 갈린다 ────────────────────────────────────────

describe('§8 상세 헤더 — 한 자리가 상태 × 보는 사람으로 셋', () => {
  it('① 미승인 + 올린 사람·소유자 → `✓ 승인 요청`', async () => {
    const requestVerification = vi.fn(async () => {});
    const d = detail(OPEN_ID, {
      verification: { ...detail(OPEN_ID).verification, verified: false },
      actions: { ...detail(OPEN_ID).actions, canRequestVerification: true },
    });
    renderDetail(d, stubApproval({ requestVerification }));
    await settle(d.name);
    const slot = screen.getByTestId('verification-action');
    fireEvent.click(within(slot).getByRole('button', { name: '✓ 승인 요청' }));
    await waitFor(() => expect(requestVerification).toHaveBeenCalledWith(d.datasetId));
  });

  it('② 검토 대기 + 교수 → `승인`', async () => {
    const approveVerification = vi.fn(async () => {});
    const d = detail(OPEN_ID, {
      verification: { ...detail(OPEN_ID).verification, verified: false },
      actions: { ...detail(OPEN_ID).actions, canApproveVerification: true },
    });
    renderDetail(d, stubApproval({ approveVerification }));
    await settle(d.name);
    const slot = screen.getByTestId('verification-action');
    fireEvent.click(within(slot).getByRole('button', { name: '승인' }));
    await waitFor(() => expect(approveVerification).toHaveBeenCalledWith(d.datasetId));
  });

  it('③ 승인됨 + 교수 → `⋯` 더보기 → `승인 취소` (파급 모달 경유)', async () => {
    const cancelVerification = vi.fn(async () => {});
    const d = detail(OPEN_ID, {
      verification: { ...detail(OPEN_ID).verification, verified: true },
      actions: { ...detail(OPEN_ID).actions, canCancelVerification: true },
    });
    renderDetail(d, stubApproval({ cancelVerification }));
    await settle(d.name);
    const slot = screen.getByTestId('verification-action');
    // 취소는 **`⋯` 더보기 하나에서만** 연다 (§1.3-4 · §7.1)
    fireEvent.click(within(slot).getByRole('button', { name: '더보기' }));
    fireEvent.click(await screen.findByRole('menuitem', { name: '승인 취소' }));
    // 파급을 **먼저 보여주고** 확인한 뒤에 취소한다 (§7.1 · P-28)
    const modal = await screen.findByRole('dialog');
    expect(modal.textContent).toContain('활용 프로젝트');
    expect(cancelVerification).not.toHaveBeenCalled();
    fireEvent.click(within(modal).getByRole('button', { name: '승인 취소' }));
    await waitFor(() => expect(cancelVerification).toHaveBeenCalledWith(d.datasetId, null));
  });

  it('그 밖에는 액션이 없다 — 자리는 비어 있고 버튼을 지어내지 않는다', async () => {
    const d = detail(OPEN_ID, {
      actions: {
        ...detail(OPEN_ID).actions,
        canRequestVerification: false,
        canApproveVerification: false,
        canCancelVerification: false,
      },
    });
    renderDetail(d);
    await settle(d.name);
    expect(within(screen.getByTestId('verification-action')).queryAllByRole('button')).toHaveLength(
      0,
    );
  });
});

// ── §1.5 배지는 표시 전용 ────────────────────────────────────────────────────

describe('Verified 배지 — 표시 전용이고 누르는 곳이 아니다 (§1.5 · §8)', () => {
  it('승인된 데이터에는 배지가 붙는다', async () => {
    const d = detail(OPEN_ID, {
      verification: { ...detail(OPEN_ID).verification, verified: true },
    });
    renderDetail(d);
    await settle(d.name);
    expect(within(screen.getByTestId('dh-tags')).getByText('Verified')).toBeTruthy();
  });

  it('미승인 데이터에는 배지가 없다 — 회색 배지를 만들지 않는다', async () => {
    const d = detail(OPEN_ID, {
      verification: { ...detail(OPEN_ID).verification, verified: false },
    });
    renderDetail(d);
    await settle(d.name);
    expect(within(screen.getByTestId('dh-tags')).queryByText('Verified')).toBeNull();
  });

  it('배지는 버튼도 링크도 아니다 — 한 곳에서 눌리면 나머지도 눌릴 것처럼 보인다 (§1.3-4)', async () => {
    const d = detail(OPEN_ID, {
      verification: { ...detail(OPEN_ID).verification, verified: true },
      actions: { ...detail(OPEN_ID).actions, canCancelVerification: true },
    });
    renderDetail(d);
    await settle(d.name);
    const badge = within(screen.getByTestId('dh-tags')).getByText('Verified');
    expect(badge.closest('button')).toBeNull();
    expect(badge.closest('a')).toBeNull();
  });
});
