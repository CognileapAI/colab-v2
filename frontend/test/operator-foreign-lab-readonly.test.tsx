/**
 * 관리자(운영자)가 **다른 연구실** 데이터셋 상세를 열면 쓰기 진입점이 하나도 없다.
 *
 * 오라클 = 승인 intent `dev-package/intent/2026-09-12-operator-designation.md`
 *          「관리자는 모든 연구실의 데이터를 **읽기 전용**으로 열람한다 …
 *           쓰기(수정·삭제·업로드·권한 변경)는 소속 연구실 범위 그대로다」.
 *
 * 왜 이 파일이 생겼나 — dev 실사용 검증(`dev-package/reports/r-login-backoffice/
 * task8-realuse/results.md §1-7`)에서 연구실 B 데이터셋 상세에 `수정` · `기준 격자 추가` ·
 * `파일 추가` · `계보 수정 · 추가` · `계보 채우기` 가 **전부 보이고 활성**이었다. 서버는 그
 * 전부를 403·404 로 거절한다(`services/core-api/tests/test_operator_designation.py` ㈒) —
 * 어긋난 것은 화면뿐이고, **그 어긋남을 잡는 검사가 어디에도 없었다**(게이트에도
 * `deploy_doctor` 에도). 이 파일이 그 자리다.
 *
 * **빈 집합 위에서 통과하지 않는다** — 「없다」를 재기 전에 **같은 장면의 자기 연구실 판이
 * 그것을 실제로 그린다**는 것을 먼저 잰다. 그게 없으면 선택자 오타도 green 이 된다.
 */
import { act, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { SessionProvider } from '../src/permission/session';
import { FIXTURE_DETAILS, FIXTURE_LAB_ID } from '../src/components/detail/fixture';
import type { CurrentAccount, PermissionSwitchSet } from '../src/api/client';
import type { DatasetDetail, DetailSource } from '../src/components/detail/types';
import type { LineageGraph, LineageGraphSource } from '../src/components/lineage/graphTypes';

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
];

describe('관리자 전 연구실 열람 — 남의 연구실 상세는 읽기 전용 (승인 intent 2026-09-12)', () => {
  it('자기 연구실이면 쓰기 진입점 6개가 **전부 있다** — 비교 기준을 먼저 세운다', async () => {
    await mount({ labId: FIXTURE_LAB_ID, operator: true });
    const found = WRITE_CONTROLS.filter(([, id]) => screen.queryAllByTestId(id).length > 0);
    expect(found.map(([label]) => label)).toEqual(WRITE_CONTROLS.map(([label]) => label));
  });

  it('남의 연구실이면 그 6개가 **DOM 에서 사라진다** — 비활성이 아니라 부재다 (P-12)', async () => {
    await mount({ labId: OTHER_LAB, operator: true });
    const left = WRITE_CONTROLS.filter(([, id]) => screen.queryAllByTestId(id).length > 0);
    expect(left.map(([label]) => label)).toEqual([]);
  });

  it('남의 연구실이면 제목 위에 「다른 연구실 데이터 — 읽기 전용」 한 줄이 선다', async () => {
    await mount({ labId: OTHER_LAB, operator: true });
    const note = screen.getByTestId('detail-foreign-readonly');
    expect(note).toHaveTextContent('다른 연구실 데이터 — 읽기 전용');
  });

  it('자기 연구실에는 그 한 줄이 없다 — 늘 붙어 있는 문구가 아니다', async () => {
    await mount({ labId: FIXTURE_LAB_ID, operator: true });
    expect(screen.queryByTestId('detail-foreign-readonly')).toBeNull();
  });

  it('자기 연구실 상세에는 `다운로드` 가 **하나** 있다 — 반출 비교 기준', async () => {
    await mount({ labId: FIXTURE_LAB_ID, operator: true });
    expect(screen.queryAllByTestId('dt-download')).toHaveLength(1);
  });

  it('남의 연구실 상세의 `다운로드` 는 DOM 에 없다 — 서버가 404 로 거절하는 길이다', async () => {
    await mount({ labId: OTHER_LAB, operator: true });
    expect(screen.queryAllByTestId('dt-download')).toHaveLength(0);
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
