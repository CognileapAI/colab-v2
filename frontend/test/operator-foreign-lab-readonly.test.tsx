import { act, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { SessionProvider } from '../src/permission/session';
import { FIXTURE_DETAILS, FIXTURE_LAB_ID } from '../src/components/detail/fixture';
import type { CurrentAccount, PermissionSwitchSet } from '../src/api/client';
import type { DatasetDetail, DetailSource } from '../src/components/detail/types';
import type { LineageGraph, LineageGraphSource } from '../src/components/lineage/graphTypes';
import type { ProjectSource } from '../src/components/project/types';

const OPEN_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA1'; // 목업 기본 장면 — 열린 데이터 · 기본 정보 전부
const BASE = FIXTURE_DETAILS[OPEN_ID] as DatasetDetail;
const OTHER_LAB = '01JYZ9K7WQ3N8V4M2X6C5B0L99';

const CAN_EDIT: PermissionSwitchSet = {
  '업로드·편집': true,
  '프로젝트 생성': true,
  '승인 위임': true,
  '연구실 설정': true,
};

/** 네 스위치가 전부 켜진 계정. `operator` 를 켜도 스위치는 그대로다 — 갈리는 것은 연구실뿐이다. */
function account(operator: boolean): CurrentAccount {
  return {
    accountId: '01JYZ9K7WQ3N8V4M2X6C5B0U01',
    name: '호랑이',
    email: 'tiger@example.org',
    role: '교수',
    permissions: CAN_EDIT,
    labId: FIXTURE_LAB_ID,
    labName: '수문연구실',
    canManageServiceAccounts: operator,
  };
}

/** 계보 편집이 **서버 판정으로는 열려 있는** 그래프. 화면이 닫는지를 재려면 그래야 한다. */
function editableGraph(): LineageGraph {
  return {
    datasetId: OPEN_ID,
    lineageState: '기록 없음',
    lineageConfirmedAt: null,
    unknownParents: true,
    nodes: [
      {
        kind: '이 데이터', datasetId: OPEN_ID, name: BASE.name, processingLevel: 2,
        verified: false, navigable: false, bodyAccessible: true, deletedAt: null,
      },
    ],
    edges: [],
    projectUseCount: 0,
    canEdit: true,
  };
}

function staticSource(detail: DatasetDetail): DetailSource {
  return { async get() { return detail; } };
}

function graphSource(graph: LineageGraph): LineageGraphSource {
  return { async get() { return graph; } };
}

async function mount(opts: { labId: string; operator: boolean }) {
  const view = render(
    <MemoryRouter initialEntries={[`/datasets/${OPEN_ID}`]}>
      <SessionProvider account={account(opts.operator)}>
        <Routes>
          <Route
            path="/datasets/:datasetId"
            element={
              <DatasetDetailPage
                source={staticSource({ ...BASE, labId: opts.labId })}
                lineageSource={graphSource(editableGraph())}
                projectSource={{ list: async () => ({ items: [{ projectId: 'P1', name: '후보', type: '국가과제' }], totalCount: 1 }), link: async () => {} } as unknown as ProjectSource}
              />
            }
          />
          <Route path="/datasets" element={<div>카탈로그</div>} />
        </Routes>
      </SessionProvider>
    </MemoryRouter>,
  );
  await screen.findByRole('heading', { level: 1, name: BASE.name });
  await act(async () => {});
  return view;
}

/** 상세 화면의 **쓰기 진입점 전부**. 이름은 `results.md §1-7` 이 적은 그 낱말이다. */
const WRITE_CONTROLS: readonly [string, string][] = [
  ['수정', 'detail-edit-open'],
  ['기준 격자 추가', 'grid-attach-open'],
  ['파일 추가', 'dt-file-add'],
  ['대표 그림 고르기', 'detail-representative-input'],
  ['계보 수정 · 추가', 'lin-edit'],
  ['계보 채우기', 'lin-fill'],
  ['프로젝트 연결', 'usage-project-add'],
];

describe('관리자 전 연구실 열람 — 타 연구실 전체 관리 (승인 intent 2026-09-16)', () => {
  it('자기 연구실이면 쓰기 진입점 6개가 **전부 있다** — 비교 기준을 먼저 세운다', async () => {
    await mount({ labId: FIXTURE_LAB_ID, operator: true });
    const found = WRITE_CONTROLS.filter(([, id]) => screen.queryAllByTestId(id).length > 0);
    expect(found.map(([label]) => label)).toEqual(WRITE_CONTROLS.map(([label]) => label));
  });

  it('타 연구실에도 쓰기 진입점이 있다', async () => {
    await mount({ labId: OTHER_LAB, operator: true });
    const left = WRITE_CONTROLS.filter(([, id]) => screen.queryAllByTestId(id).length > 0);
    expect(left.map(([label]) => label)).toEqual(WRITE_CONTROLS.map(([label]) => label));
  });

  it('타 연구실 읽기 전용 안내가 없다', async () => {
    await mount({ labId: OTHER_LAB, operator: true });
    expect(screen.queryByTestId('detail-foreign-readonly')).toBeNull();
  });

  it('자기 연구실에는 그 한 줄이 없다 — 늘 붙어 있는 문구가 아니다', async () => {
    await mount({ labId: FIXTURE_LAB_ID, operator: true });
    expect(screen.queryByTestId('detail-foreign-readonly')).toBeNull();
  });

  it('자기 연구실 상세에는 `다운로드` 가 **하나** 있다 — 반출 비교 기준', async () => {
    await mount({ labId: FIXTURE_LAB_ID, operator: true });
    expect(screen.queryAllByTestId('dt-download')).toHaveLength(1);
  });

  it('타 연구실 상세도 다운로드할 수 있다', async () => {
    await mount({ labId: OTHER_LAB, operator: true });
    expect(screen.queryAllByTestId('dt-download')).toHaveLength(1);
  });

  it('**읽기는 그대로다** — 남의 연구실에서도 제목·기본 정보·파일 목록 열기가 남는다', async () => {
    await mount({ labId: OTHER_LAB, operator: true });
    expect(screen.getByRole('heading', { level: 1, name: BASE.name })).toBeTruthy();
    expect(screen.getByTestId('detail-split-right')).toBeTruthy();
    // `파일 관리` 는 목록을 펴는 **읽기** 조작이다 — 읽기 전용에서도 남는다.
    expect(screen.getByTestId('dt-files-toggle')).toBeTruthy();
  });

  it('관리자가 아니면 연구실이 달라도 화면은 한 칸도 바뀌지 않는다 (도달 불가 장면의 회귀 잠금)', async () => {
    await mount({ labId: OTHER_LAB, operator: false });
    const found = WRITE_CONTROLS.filter(([, id]) => screen.queryAllByTestId(id).length > 0);
    expect(found.map(([label]) => label)).toEqual(WRITE_CONTROLS.map(([label]) => label));
    expect(screen.queryByTestId('detail-foreign-readonly')).toBeNull();
  });
});
