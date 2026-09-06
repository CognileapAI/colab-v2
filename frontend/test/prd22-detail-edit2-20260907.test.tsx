/**
 * WU-A3R ＋ WU-A4R — 편집 중 다운로드 숨김·칩 재동기 ＋ `좌표계 (선택)`
 * (PRD-22 · PRD-28 · `dev-package/prd/rounds/R-A2.md §2-⑤`).
 *
 * 오라클 = 라운드 파일 §2-⑤ 축자 셋.
 *   ⑴ 편집 중에는 다운로드가 숨고 `취소`/`저장` 이 그 자리에 온다.
 *   ⑵ 저장 뒤 헤더 칩과 공개 범위 설명이 같은 값으로 다시 그려진다(새로고침 불요).
 *   ⑶ 등록 화면 좌표계 칸 보조 라벨이 `좌표계 (선택)` 이다 — 그 판정은
 *      `test/upload.test.tsx` §8 ① 에 함께 세운다(같은 화면의 다른 시험과 한자리).
 *
 * ⛔ R-B 가 더하는 칸(분류·유형·가공 단계·변수 표·공개 범위 값·관측 간격·기간 최소 단위·
 *    Lv0 2칸)은 여기서 재지 않는다. `topic` 은 읽기 전용이라 **편집 진입이 없음**만 잰다.
 *
 * 모든 단언은 **대상 건수를 먼저 잰다** — 빈 집합 통과(green-by-skip)를 막는다.
 */
import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { SessionProvider } from '../src/permission/session';
import { FIXTURE_DETAILS } from '../src/components/detail/fixture';
import { ACCESS_ORIGIN_NOTE } from '../src/components/detail/UsageSection';
import type { CurrentAccount, PermissionSwitchSet } from '../src/api/client';
import type { DatasetDetail, DetailSource } from '../src/components/detail/types';
import type { DatasetUpdateSource } from '../src/components/detail/updateSource';

const OPEN_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA1';
const BASE = FIXTURE_DETAILS[OPEN_ID] as DatasetDetail;

const ALL_OFF: PermissionSwitchSet = {
  '업로드·편집': false,
  '프로젝트 생성': false,
  '승인 위임': false,
  '연구실 설정': false,
};
const CAN_EDIT: PermissionSwitchSet = { ...ALL_OFF, '업로드·편집': true };

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

/** 상세를 몇 번 읽었는지 센다 — 「새로고침 불요」는 **다시 읽지 않았다**로만 성립한다. */
function countingSource(detail: DatasetDetail) {
  const calls: string[] = [];
  const source: DetailSource = {
    async get(datasetId) {
      calls.push(datasetId);
      return detail;
    },
  };
  return { calls, source };
}

function deferredUpdateSource(result: DatasetDetail) {
  const calls: { datasetId: string }[] = [];
  let release: (() => void) | null = null;
  const source: DatasetUpdateSource = {
    update(datasetId) {
      calls.push({ datasetId });
      return new Promise<DatasetDetail>((resolve) => {
        release = () => resolve(result);
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
  };
}

function mount(opts: {
  detail?: DatasetDetail;
  detailSource?: DetailSource;
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
                source={opts.detailSource ?? { async get() { return opts.detail ?? BASE; } }}
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
  const heading = await screen.findByRole('heading', { level: 1, name });
  await act(async () => {});
  return heading;
}

async function click(el: Element | null) {
  fireEvent.click(el as HTMLElement);
  await act(async () => {});
}

async function type(el: HTMLElement, value: string) {
  fireEvent.change(el, { target: { value } });
  await act(async () => {});
}

async function openForm(opts: Parameters<typeof mount>[0] = {}) {
  mount(opts);
  await settle((opts.detail ?? BASE).name);
  await click(await screen.findByTestId('detail-edit-open'));
  return screen.findByTestId('detail-edit-form');
}

// ── ⑴ 편집 중에는 다운로드가 숨고 `취소`/`저장` 이 그 자리에 온다 ──────────────

describe('WU-A3R ⑴ — 편집 중 다운로드 숨김 · 그 자리에 `취소`/`저장`', () => {
  it('편집 전에는 다운로드 진입점 2곳이 서 있다 (기준선 실측)', async () => {
    mount({});
    await settle(BASE.name);
    expect(screen.getAllByTestId('dt-download')).toHaveLength(1);
    expect(screen.getAllByTestId('detail-download')).toHaveLength(1);
  });

  it('`수정` 을 누르면 다운로드가 **DOM 에서 사라진다** (두 자리 모두)', async () => {
    await openForm({});
    expect(screen.queryByTestId('dt-download')).toBeNull();
    expect(screen.queryByTestId('detail-download')).toBeNull();
  });

  it('다운로드가 있던 행에 `취소`/`저장` 이 선다', async () => {
    await openForm({});
    const row = screen.getByTestId('detail-grid-actions');
    const save = within(row).getByTestId('detail-edit-save');
    const cancel = within(row).getByTestId('detail-edit-cancel');
    expect(save).toHaveTextContent('저장');
    expect(cancel).toHaveTextContent('취소');
    // 진입점은 하나뿐이다 — 폼 안에 같은 버튼을 겹쳐 두지 않는다
    expect(screen.getAllByTestId('detail-edit-save')).toHaveLength(1);
    expect(screen.getAllByTestId('detail-edit-cancel')).toHaveLength(1);
  });

  it('`취소` 뒤에는 다운로드가 그 자리로 돌아온다', async () => {
    await openForm({});
    await click(screen.getByTestId('detail-edit-cancel'));
    expect(screen.getAllByTestId('dt-download')).toHaveLength(1);
    expect(screen.getAllByTestId('detail-download')).toHaveLength(1);
    expect(screen.queryByTestId('detail-edit-save')).toBeNull();
  });
});

// ── ⑵ 저장 뒤 헤더 칩 · 공개 범위 설명 재동기 ────────────────────────────────

describe('WU-A3R ⑵ — 저장 뒤 헤더 칩과 공개 범위 설명이 서버 값으로 다시 그려진다', () => {
  it('서버가 돌려준 칩 값과 접근 판정이 **다시 읽지 않고** 화면에 선다', async () => {
    // 서버가 저장 응답으로 돌려주는 상세 — 칩 세 값과 다운로드 판정이 함께 바뀐다
    const served: DatasetDetail = {
      ...BASE,
      name: '서버가 확정한 이름',
      topic: '수질',
      processingLevel: 3,
      actions: { ...BASE.actions, canDownload: false },
    };
    const ds = countingSource(BASE);
    const up = deferredUpdateSource(served);
    const form = await openForm({ detailSource: ds.source, updateSource: up.source });
    // 기준선 — 편집 전 칩과 공개 범위 설명이 옛 값이다
    await type(within(form).getByTestId('edit-name'), '서버가 확정한 이름');
    await click(screen.getByTestId('detail-edit-save'));
    await up.settle();

    expect(up.calls).toHaveLength(1);
    // 헤더 칩 — 서버가 돌려준 값으로 다시 그려진다
    const tags = screen.getByTestId('dh-tags');
    expect(tags.textContent).toContain('수질');
    expect(tags.textContent).toContain('Lv3');
    expect(tags.textContent).not.toContain('강우·강수');
    // 공개 범위 설명 — 같은 상세의 `canDownload` 로 판정되므로 함께 사라진다
    expect(screen.queryByTestId('access-origin')).toBeNull();
    expect(screen.queryByTestId('detail-download')).toBeNull();
    expect(screen.queryByTestId('dt-download')).toBeNull();
    // 새로고침 불요 — 상세를 **한 번만** 읽었다
    expect(ds.calls).toHaveLength(1);
  });

  it('다운로드가 열린 채로 저장하면 공개 범위 설명이 그 자리에 다시 선다', async () => {
    const served: DatasetDetail = { ...BASE, name: '이름만 바뀐 상세' };
    const ds = countingSource(BASE);
    const up = deferredUpdateSource(served);
    const form = await openForm({ detailSource: ds.source, updateSource: up.source });
    await type(within(form).getByTestId('edit-name'), '이름만 바뀐 상세');
    await click(screen.getByTestId('detail-edit-save'));
    await up.settle();
    expect(screen.getByTestId('access-origin').textContent).toBe(ACCESS_ORIGIN_NOTE);
    expect(screen.getAllByTestId('dt-download')).toHaveLength(1);
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('이름만 바뀐 상세');
    expect(ds.calls).toHaveLength(1);
  });

  it('`topic` 은 읽기 전용이다 — 편집 폼에 칸이 없다 (R-B 몫)', async () => {
    const form = await openForm({});
    expect(within(form).queryByTestId('edit-topic')).toBeNull();
    expect(form.textContent).not.toContain('주제');
  });
});
