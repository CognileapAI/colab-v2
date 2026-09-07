/**
 * WU-B4 — 공개 범위 **3값** (PRD-11 · `dev-package/prd/rounds/R-B-1-db.md §2` WU-B4).
 *
 * 오라클 = 그 절의 수용 기준 중 **화면이 잴 수 있는 셋** ＋ WU-B3 이 넘긴 ㈓ 「공개 범위 값
 * 재동기 재검증」이다 —
 *
 *   ㈎ 등록 ② 의 자리(`reg-visibility-slot`)가 **3값 셀렉트**다. 라벨은 rev1 축자
 *      (`연구실 구성원 전체`·`나만 보기`·`지정한 사람만`)이고 저장은 `열림`·`잠김`·`지정 공개` 다.
 *   ㈏ 상세 헤더 칩이 **세 갈래**다 — `열림` 은 칩이 없고 나머지 둘은 각자 표기로 선다.
 *   ㈐ `나만 보기` 로 내릴 때 되묻는 문면에 **`2명`** 이 뜨고, 확인해야 저장이 나간다.
 *   ㈓ **재동기 재검증**(WU-B3 이관) — 3값을 각각 저장하면 **다시 읽지 않고** 헤더 칩과
 *      공개 범위 설명이 그 값으로 다시 선다.
 *
 * 모든 단언은 **대상 건수를 먼저 잰다** — 빈 집합 통과(green-by-skip)를 막는다.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { SessionProvider } from '../src/permission/session';
import { FIXTURE_DETAILS } from '../src/components/detail/fixture';
import {
  ACCESS_LABEL,
  ACCESS_STATES,
  DEFAULT_ACCESS_STATE,
  loweringConfirmCopy,
} from '../src/components/common/accessState';
import { toDraft, toPatch } from '../src/components/detail/editFields';
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

function account(): CurrentAccount {
  return {
    accountId: '01JYZ9K7WQ3N8V4M2X6C5B0U01',
    name: '호랑이',
    email: 'tiger@example.org',
    role: '연구원',
    permissions: CAN_EDIT,
    labId: '01JYZ9K7WQ3N8V4M2X6C5B0L01',
    labName: '수문연구실',
  };
}

function staticSource(detail: DatasetDetail): DetailSource {
  return { async get() { return detail; } };
}

/** 서버 왕복 대역 — **보낸 patch 를 그대로 반영한 상세**를 돌려준다(실서버와 같은 규율). */
function echoUpdateSource(detail: DatasetDetail) {
  const calls: Record<string, unknown>[] = [];
  const source: DatasetUpdateSource = {
    async update(_datasetId, patch) {
      const p = patch as Record<string, unknown>;
      calls.push(p);
      return {
        ...detail,
        ...(typeof p.accessState === 'string'
          ? { accessState: p.accessState as DatasetDetail['accessState'] }
          : {}),
        // 서버는 `잠김` 으로 내리면 허용 줄을 전부 만료시킨다 — 응답의 수가 0 이 된다.
        ...(p.accessState === '잠김' ? { activeGrantCount: 0 } : {}),
      };
    },
  };
  return { calls, source };
}

function mount(detail: DatasetDetail, updateSource?: DatasetUpdateSource) {
  return render(
    <MemoryRouter initialEntries={[`/datasets/${OPEN_ID}`]}>
      <SessionProvider account={account()}>
        <Routes>
          <Route
            path="/datasets/:datasetId"
            element={
              <DatasetDetailPage source={staticSource(detail)} updateSource={updateSource} />
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

async function choose(el: Element | null, value: string) {
  fireEvent.change(el as HTMLElement, { target: { value } });
  await act(async () => {});
}

// ═══════ ㈎ 값 대응표 — 저장값과 표기가 갈린다 ══════════════════════════════
describe('§1 값 대응 — 저장은 열림·잠김·지정 공개, 표기는 rev1 축자', () => {
  it('3값이고 표기가 rev1 셀렉트 축자와 같다', () => {
    expect(ACCESS_STATES).toEqual(['열림', '잠김', '지정 공개']);
    expect(ACCESS_STATES.map((v) => ACCESS_LABEL[v])).toEqual([
      '연구실 구성원 전체', '나만 보기', '지정한 사람만',
    ]);
  });

  it('기본 선택은 `연구실 구성원 전체` 다 (PRD-11 축자)', () => {
    expect(DEFAULT_ACCESS_STATE).toBe('열림');
    expect(ACCESS_LABEL[DEFAULT_ACCESS_STATE]).toBe('연구실 구성원 전체');
  });

  it('되묻는 문면이 사람 수를 그대로 싣는다', () => {
    expect(loweringConfirmCopy(2)).toBe('지금 볼 수 있는 사람 2명의 접근이 끊깁니다');
  });
});

// ═══════ ㈏ 헤더 칩 — 두 갈래 → 세 갈래 ════════════════════════════════════
describe('§2 상세 헤더 칩 — 세 갈래', () => {
  it('`열림` 은 칩이 없다 — 기본 상태에 배지를 붙이지 않는다', async () => {
    mount({ ...BASE, accessState: '열림' });
    await settle(BASE.name);
    expect(screen.queryByTestId('dh-access-chip')).toBeNull();
  });

  it('`잠김`·`지정 공개` 가 **각자의 표기**로 선다 — 둘을 한 칩으로 접지 않는다', async () => {
    const seen: string[] = [];
    for (const state of ['잠김', '지정 공개'] as const) {
      const view = mount({ ...BASE, accessState: state });
      await settle(BASE.name);
      seen.push(screen.getByTestId('dh-access-chip').textContent as string);
      view.unmount();
    }
    expect(seen).toEqual(['나만 보기', '지정한 사람만']);
  });
});

// ═══════ 공개 범위 설명 — 상세가 값을 읽는다 ══════════════════════════════
describe('§3 공개 범위 설명 — 값 칸이 섰다 (PRD-39 ⑩ 의 출처 문장 옆)', () => {
  it('세 값이 각자의 표기로 설명에 뜬다', async () => {
    const seen: string[] = [];
    for (const state of ACCESS_STATES) {
      const view = mount({ ...BASE, accessState: state });
      await settle(BASE.name);
      seen.push(screen.getByTestId('usage-access-state').textContent as string);
      view.unmount();
    }
    expect(seen).toHaveLength(3);
    for (const [i, state] of ACCESS_STATES.entries()) {
      expect(seen[i]).toContain(ACCESS_LABEL[state]);
    }
  });
});

// ═══════ ㈐ 내리면 되묻는다 — `2명` ════════════════════════════════════════
describe('§4 `나만 보기` 로 내리기 — 되묻고 나서 저장한다', () => {
  const WITH_TWO: DatasetDetail = { ...BASE, accessState: '지정 공개', activeGrantCount: 2 };

  it('되묻는 문면에 `2명` 이 뜨고 **그 사이에는 저장이 안 나간다**', async () => {
    const server = echoUpdateSource(WITH_TWO);
    mount(WITH_TWO, server.source);
    await settle(WITH_TWO.name);
    await click(screen.getByTestId('detail-edit-open'));
    await choose(screen.getByTestId('edit-access-state-select'), '잠김');
    await click(screen.getByTestId('detail-edit-save'));

    const confirm = screen.getByTestId('detail-edit-confirm');
    expect(confirm.textContent).toContain('지금 볼 수 있는 사람 2명의 접근이 끊깁니다');
    expect(server.calls).toHaveLength(0);

    await click(screen.getByTestId('detail-edit-confirm-ok'));
    expect(server.calls).toHaveLength(1);
    expect(server.calls[0]).toEqual({ accessState: '잠김' });
  });

  it('되묻기에서 물러나면 **편집이 닫히지 않고** 고른 값이 남는다', async () => {
    const server = echoUpdateSource(WITH_TWO);
    mount(WITH_TWO, server.source);
    await settle(WITH_TWO.name);
    await click(screen.getByTestId('detail-edit-open'));
    await choose(screen.getByTestId('edit-access-state-select'), '잠김');
    await click(screen.getByTestId('detail-edit-save'));
    await click(screen.getByTestId('detail-edit-confirm-cancel'));

    expect(server.calls).toHaveLength(0);
    const select = screen.getByTestId('edit-access-state-select') as HTMLSelectElement;
    expect(select.value).toBe('잠김');
  });

  it('끊길 사람이 0명이면 되묻지 않는다 — 잃을 것이 없는 확인은 반사가 된다', async () => {
    const none: DatasetDetail = { ...BASE, accessState: '지정 공개', activeGrantCount: 0 };
    const server = echoUpdateSource(none);
    mount(none, server.source);
    await settle(none.name);
    await click(screen.getByTestId('detail-edit-open'));
    await choose(screen.getByTestId('edit-access-state-select'), '잠김');
    await click(screen.getByTestId('detail-edit-save'));

    expect(screen.queryByTestId('detail-edit-confirm')).toBeNull();
    expect(server.calls).toEqual([{ accessState: '잠김' }]);
  });

  it('`나만 보기` 가 **아닌** 변경은 되묻지 않는다 — 허용 줄이 끊기지 않는다', async () => {
    const server = echoUpdateSource(WITH_TWO);
    mount(WITH_TWO, server.source);
    await settle(WITH_TWO.name);
    await click(screen.getByTestId('detail-edit-open'));
    await choose(screen.getByTestId('edit-access-state-select'), '열림');
    await click(screen.getByTestId('detail-edit-save'));

    expect(screen.queryByTestId('detail-edit-confirm')).toBeNull();
    expect(server.calls).toEqual([{ accessState: '열림' }]);
  });
});

// ═══════ ㈓ 재동기 재검증 (WU-B3 이관) ════════════════════════════════════
describe('§5 ㈓ 공개 범위 **값** 재동기 — 저장하면 다시 읽지 않고 화면이 그 값으로 선다', () => {
  it('3값을 각각 저장하면 헤더 칩과 설명이 **같은 값**으로 다시 그려진다', async () => {
    const results: { state: string; chip: string | null; note: string }[] = [];
    for (const state of ACCESS_STATES) {
      // 출발은 늘 **다른 값**이다 — 안 바뀌면 patch 가 비어 왕복 자체가 없다.
      const start: DatasetDetail = {
        ...BASE,
        accessState: state === '열림' ? '지정 공개' : '열림',
        activeGrantCount: 0,
      };
      const server = echoUpdateSource(start);
      const view = mount(start, server.source);
      await settle(start.name);
      await click(screen.getByTestId('detail-edit-open'));
      await choose(screen.getByTestId('edit-access-state-select'), state);
      await click(screen.getByTestId('detail-edit-save'));

      results.push({
        state,
        // `열림` 은 칩이 없는 것이 정답이다.
        chip: screen.queryByTestId('dh-access-chip')?.textContent ?? null,
        note: screen.getByTestId('usage-access-state').textContent as string,
      });
      // **다시 읽지 않았다** — 상세 조회는 처음 한 번뿐이고 갱신은 저장 응답으로 온다.
      expect(server.calls).toEqual([{ accessState: state }]);
      view.unmount();
    }

    expect(results).toHaveLength(3);
    expect(results.map((r) => r.chip)).toEqual([null, '나만 보기', '지정한 사람만']);
    for (const r of results) {
      expect(r.note).toContain(ACCESS_LABEL[r.state as (typeof ACCESS_STATES)[number]]);
    }
  });

  it('값을 안 바꾸면 `accessState` 를 **보내지 않는다** — 뜻 없는 내림 경로를 안 탄다', () => {
    const detail: DatasetDetail = { ...BASE, accessState: '지정 공개', activeGrantCount: 2 };
    const draft = toDraft(detail);
    expect(draft.accessState).toBe('지정 공개');
    expect(toPatch(detail, draft)).toEqual({});
  });
});
