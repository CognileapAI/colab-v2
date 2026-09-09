/**
 * WU-B10 · PRD-31 — 상세에서 계보를 고치고 더한다.
 *
 * 오라클 = `dev-package/prd/rounds/R-B-3-frontend.md` WU-B10 수용 기준 6 · PRD-31 축자
 *          (rev1 `H-45`·`H-46`·`H-47`).
 *
 * **재사용을 시험이 증명한다** — 초과 후보의 사유 문구를 이 파일이 다시 적지 않고
 * 등록 ③ 이 쓰는 **같은 모듈의 같은 상수**(`ParentPicker.parentOverReason`)를 불러 대조한다.
 * 문구를 여기 다시 적으면 두 화면이 갈라져도 시험이 green 으로 남는다.
 *
 * **빈 집합 위에서 통과하지 않는다** — 모든 단언이 대상 1건 이상을 먼저 재거나 「없음」을
 * 기대값으로 명시한다.
 */
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { FIXTURE_DETAILS, fixtureDetailSource } from '../src/components/detail/fixture';
import { SessionProvider } from '../src/permission/session';
import type { CurrentAccount, PermissionSwitchSet } from '../src/api/client';
import { parentOverReason } from '../src/components/lineage/ParentPicker';
import { PRE_LINEAGE_ADDED } from '../src/components/common/toastCopy';
import { ESC_LAYER_ATTR } from '../src/components/upload/escLayer';
import type {
  LineageGraph,
  LineageGraphSource,
} from '../src/components/lineage/graphTypes';
import { apiLineageEditSource, type LineageEditSource } from '../src/components/lineage/lineageEditSource';
import type { DatasetDetail, DetailSource } from '../src/components/detail/types';
import type { DatasetRow, LineageSource } from '../src/components/lineage/types';

const SELF = '01JYZ9K7WQ3N8V4M2X6C5B0AA3'; // nakdong_DEM_10m.tif — 기록 없음 장면
const PARENT = '01JYZ9K7WQ3N8V4M2X6C5B0AA6'; // Lv1 — 고를 수 있다
const OVER = '01JYZ9K7WQ3N8V4M2X6C5B0AA7'; // Lv3 — 자기(Lv2)보다 높다
const CHILD = '01JYZ9K7WQ3N8V4M2X6C5B0AA8'; // 파생
const 호랑이 = { accountId: '01JYZ9K7WQ3N8V4M2X6C5B0U01', name: '호랑이' };

/** 자기 Lv2(그래프 파생값) · 부모 0건 · 파생 1건. 기록 없음 선언이 붙어 있다.
 *  `selfProcessingLevel` 로 그래프 노드가 들고 있는 **파생** Lv 를 바꿔 잴 수 있다 —
 *  F1 은 이 값이 아니라 사람이 고른 `processingLevelUserSet` 이 기준이어야 함을 잠근다. */
function emptyGraph(canEdit: boolean, selfProcessingLevel = 2): LineageGraph {
  return {
    datasetId: SELF,
    lineageState: '기록 없음',
    lineageConfirmedAt: null,
    unknownParents: true,
    nodes: [
      { kind: '이 데이터', datasetId: SELF, name: 'nakdong_DEM_10m.tif',
        processingLevel: selfProcessingLevel,
        verified: false, navigable: false, bodyAccessible: true, deletedAt: null },
    ],
    edges: [],
    projectUseCount: 0,
    canEdit,
  };
}

/** 부모 1건이 붙은 뒤의 그래프 — 서버가 `addLineageParent` 응답으로 돌려주는 모습이다. */
function filledGraph(method: string): LineageGraph {
  return {
    datasetId: SELF,
    lineageState: '확인 필요',
    lineageConfirmedAt: null,
    unknownParents: false,
    nodes: [
      { kind: '가공 전', datasetId: PARENT, name: 'ERA5_precip_2025_Lv1.grib', processingLevel: 1,
        verified: false, navigable: true, bodyAccessible: true, deletedAt: null },
      { kind: '이 데이터', datasetId: SELF, name: 'nakdong_DEM_10m.tif', processingLevel: 2,
        verified: false, navigable: false, bodyAccessible: true, deletedAt: null },
    ],
    edges: [
      { childDatasetId: SELF, parentDatasetId: PARENT, parentRole: '주입력', method,
        origin: 'manual', confirmedBy: 호랑이, confirmedAt: '2026-09-07T00:00:00Z' },
    ],
    projectUseCount: 0,
    canEdit: true,
  };
}

/** 파생 행이 있는 그래프 — 파생은 읽기 전용이다 (`H-45`). */
function derivedGraph(): LineageGraph {
  const g = filledGraph('유역 평균');
  return {
    ...g,
    nodes: [
      ...g.nodes,
      { kind: '파생', datasetId: CHILD, name: 'nakdong_flood_index_2025_Lv3.nc',
        processingLevel: 3, verified: false, navigable: true, bodyAccessible: true,
        deletedAt: null },
    ],
    edges: [
      ...g.edges,
      { childDatasetId: CHILD, parentDatasetId: SELF, parentRole: '주입력',
        method: '임계값 초과일 집계', origin: 'manual', confirmedBy: 호랑이,
        confirmedAt: '2026-09-06T00:00:00Z' },
    ],
  };
}

const CANDIDATES: DatasetRow[] = [
  { datasetId: PARENT, name: 'ERA5_precip_2025_Lv1.grib', processingLevel: 1 } as DatasetRow,
  { datasetId: OVER, name: 'nakdong_flood_index_2025_Lv3.nc', processingLevel: 3 } as DatasetRow,
];

function only(graph: LineageGraph): LineageGraphSource {
  return { async get() { return graph; } };
}

/** 등록 ③ 과 **같은 얼굴**(`LineageSource`)로 후보를 준다 — 모달이 새 경로를 만들지 않는다. */
function candidateSource(): Pick<LineageSource, 'candidates'> {
  return { async candidates() { return CANDIDATES; } };
}

/** `업로드·편집` 이 켜진 계정 — 상세 `수정` 진입점의 관문이다(PRD-22). */
const CAN_EDIT: PermissionSwitchSet = {
  '업로드·편집': true,
  '프로젝트 생성': false,
  '승인 위임': false,
  '연구실 설정': false,
};
const ACCOUNT: CurrentAccount = {
  accountId: '01JYZ9K7WQ3N8V4M2X6C5B0U01',
  name: '호랑이',
  email: 'tiger@example.org',
  role: '연구원',
  permissions: CAN_EDIT,
  labId: '01JYZ9K7WQ3N8V4M2X6C5B0L01',
  labName: '수문연구실',
};

function renderDetail(
  graph: LineageGraph,
  editSource?: LineageEditSource,
  detailSource?: DetailSource,
) {
  return render(
    <MemoryRouter initialEntries={[`/datasets/${SELF}`]}>
     <SessionProvider account={ACCOUNT}>
      <Routes>
        <Route
          path="/datasets/:datasetId"
          element={
            <DatasetDetailPage
              source={detailSource ?? fixtureDetailSource()}
              lineageSource={only(graph)}
              lineageCandidateSource={candidateSource()}
              {...(editSource ? { lineageEditSource: editSource } : {})}
            />
          }
        />
        <Route path="/datasets" element={<div>카탈로그</div>} />
      </Routes>
     </SessionProvider>
    </MemoryRouter>,
  );
}

async function openModal(): Promise<HTMLElement> {
  const edit = await screen.findByTestId('lin-edit');
  await act(async () => {
    fireEvent.click(edit);
  });
  return screen.findByTestId('lin-fix-modal');
}

describe('⑴ 기록 없음 상세 — 빈 상태 3문면과 `계보 채우기` (H-47)', () => {
  it('세 문면이 축자로 서고 `계보 채우기` 가 눌려 모달이 열린다', async () => {
    renderDetail(emptyGraph(true));
    const empty = await screen.findByTestId('lin-empty');
    // 3문면 = 제목 · 버튼 · 보조 문구 (PRD-31 ⑵ 축자 그대로)
    expect(within(empty).getByText('아직 채워지지 않은 계보예요')).toBeTruthy();
    const fill = within(empty).getByTestId('lin-fill');
    expect(fill.textContent).toBe('계보 채우기');
    expect(
      within(empty).getByText('원자료(Lv0)라 부모가 없다면 그대로 두어도 괜찮아요.'),
    ).toBeTruthy();
    fireEvent.click(fill);
    expect(await screen.findByTestId('lin-fix-modal')).toBeTruthy();
  });

  it('`계보 수정 · 추가` 는 계보 구역 **헤더**에 선다', async () => {
    renderDetail(emptyGraph(true));
    await screen.findByTestId('lineage-section');
    const head = screen.getByTestId('lin-sec-head');
    const btn = within(head).getByTestId('lin-edit');
    expect(btn.textContent).toBe('계보 수정 · 추가');
  });
});

describe('⑵ 부모 1건 추가 — `직접 연결` ＋ 상태 전이 (H-46)', () => {
  it('저장하면 그 부모가 `직접 연결` 로 서고 상태가 `확인 필요` 로 바뀐다', async () => {
    const add = vi.fn(async () => filledGraph('유역 클리핑'));
    renderDetail(emptyGraph(true), { addParent: add });
    const modal = await openModal();
    await within(modal).findByTestId('lin-fix-picker');
    fireEvent.click(within(modal).getByTestId(`lin-pick-${PARENT}`));
    fireEvent.change(within(modal).getByTestId('lin-fix-method'), { target: { value: '유역 클리핑' } });
    fireEvent.click(within(modal).getByTestId('lin-fix-save'));

    // **이미 있는 경로 하나만 쓴다** — `addLineageParent` 의 열쇠 셋뿐이다.
    await waitFor(() => expect(add).toHaveBeenCalledTimes(1));
    expect(add.mock.calls[0]).toEqual([
      SELF,
      { parentDatasetId: PARENT, parentRole: '주입력', method: '유역 클리핑' },
    ]);

    // 재조회 없이 상세가 새 그래프를 읽는다 (응답 그래프가 그 자리를 받는다)
    const flags = await screen.findAllByTestId('lin-flag');
    expect(flags.length).toBeGreaterThan(0);
    expect(flags.some((f) => f.getAttribute('data-origin') === 'manual'
      && f.textContent === '직접 연결')).toBe(true);
    expect(screen.queryByTestId('lin-empty')).toBeNull();
    expect(screen.queryByTestId('lin-unknown-chip')).toBeNull();
    // 토스트 축자 — 문면의 자리는 `toastCopy.ts` 하나다
    expect((await screen.findByTestId('lin-fix-toast')).textContent).toBe(PRE_LINEAGE_ADDED);
  });
});

describe('⑶ 초과 후보 — 보이되 못 고르고 사유는 등록 ③ 과 **같은 문구**다 (PRD-08 재사용)', () => {
  it('초과 후보가 목록에 남고, 버튼이 비활성이며, 사유가 같은 상수에서 온다', async () => {
    const modal = await (async () => {
      renderDetail(emptyGraph(true));
      return openModal();
    })();
    await within(modal).findByTestId('lin-fix-picker');
    // 없는 것과 못 고르는 것은 다르다 — 초과 행도 목록에 **남는다**
    const over = within(modal).getByTestId(`lin-pick-${OVER}`) as HTMLButtonElement;
    expect(over.disabled).toBe(true);
    expect((within(modal).getByTestId(`lin-pick-${PARENT}`) as HTMLButtonElement).disabled)
      .toBe(false);
    // 자기 Lv 는 그래프의 `이 데이터` 노드가 준다 (Lv2)
    expect(within(modal).getByTestId(`lin-over-${OVER}`).textContent).toBe(parentOverReason(2));
  });
});

describe('⑷ `업로드·편집` 없는 계정 — 진입점이 DOM 에 없다', () => {
  it('`계보 수정 · 추가` 도 `계보 채우기` 도 서지 않는다', async () => {
    renderDetail(emptyGraph(false));
    await screen.findByTestId('lineage-section');
    // 비활성이 아니라 **부재**다 (P-12 관례). 서버 거절은 core 시험이 잠근다 —
    // `services/core-api/tests/test_lineage_confirm.py::test_lineage_edits_need_the_upload_edit_switch`
    expect(screen.queryByTestId('lin-edit')).toBeNull();
    expect(screen.queryByTestId('lin-fill')).toBeNull();
    // 빈 상태 제목은 권한과 무관하게 읽힌다 — 진입점만 사라진다
    expect(
      within(screen.getByTestId('lin-empty')).getByText('아직 채워지지 않은 계보예요'),
    ).toBeTruthy();
  });
});

describe('⑸ 파생 행 — 읽기 전용 ＋ `여기서는 못 고쳐요` (H-45)', () => {
  it('파생 행에 문구가 읽히고 그 행에는 편집 컨트롤이 없다', async () => {
    renderDetail(derivedGraph());
    await screen.findByTestId('lin-rows');
    const rows = screen.getAllByTestId('lrow').filter(
      (r) => r.getAttribute('data-stage') === '파생',
    );
    expect(rows.length).toBe(1);
    expect(rows[0]!.textContent).toContain('여기서는 못 고쳐요');
    expect(within(rows[0]!).queryByRole('button')).toBeNull();
    expect(within(rows[0]!).queryByRole('textbox')).toBeNull();
  });
});

describe('⑹ `가공 방식` — 계보 행과 엣지 라벨이 새 값을 읽는다 (PRD-30 표시층)', () => {
  it('저장 뒤 재조회 없이 두 자리가 같은 값을 보인다', async () => {
    renderDetail(emptyGraph(true), { async addParent() { return filledGraph('유역 평균'); } });
    const modal = await openModal();
    await within(modal).findByTestId('lin-fix-picker');
    fireEvent.click(within(modal).getByTestId(`lin-pick-${PARENT}`));
    fireEvent.change(within(modal).getByTestId('lin-fix-method'), { target: { value: '유역 평균' } });
    fireEvent.click(within(modal).getByTestId('lin-fix-save'));

    // 계보 행 (`LineageSection` 의 `가공 방식: …`)
    const rows = await screen.findAllByTestId('lrow');
    expect(rows.some((r) => r.textContent?.includes('가공 방식: 유역 평균'))).toBe(true);
    // 그래프 엣지 라벨
    const ways = screen.getAllByTestId('lin-method');
    expect(ways.length).toBeGreaterThan(0);
    expect(ways.some((w) => w.textContent === '유역 평균')).toBe(true);
  });
});

describe('모달 층 규율 — 표식 하나 · 닫기 한 곳 (A9R)', () => {
  it('`data-esc-layer="계보 수정"` 표식을 스스로 달고 Esc·배경·× 가 한 곳으로 모인다', async () => {
    renderDetail(emptyGraph(true));
    const modal = await openModal();
    expect(modal.getAttribute(ESC_LAYER_ATTR)).toBe('계보 수정');
    expect(document.querySelectorAll(`[${ESC_LAYER_ATTR}="계보 수정"]`)).toHaveLength(1);

    fireEvent.keyDown(document, { key: 'Escape' });
    await waitFor(() => expect(screen.queryByTestId('lin-fix-modal')).toBeNull());

    // 배경은 mousedown 과 click 이 **둘 다** 배경일 때만 닫는다 (A9R `downOnBackdrop`)
    const back = await openModal();
    const body = screen.getByTestId('lin-fix-body');
    fireEvent.mouseDown(body);
    fireEvent.click(back);
    expect(screen.queryByTestId('lin-fix-modal')).toBeTruthy();
    fireEvent.mouseDown(back);
    fireEvent.click(back);
    await waitFor(() => expect(screen.queryByTestId('lin-fix-modal')).toBeNull());
  });
});

describe('PRD-22 — 편집 화면은 계보 표를 그리지 않고 이 모달로 보낸다', () => {
  it('편집 대상 목록의 `계보 부모 연결` 이 모달을 열고, 폼 안에 계보 표가 없다', async () => {
    renderDetail(emptyGraph(true));
    await screen.findByTestId('lineage-section');
    fireEvent.click(await screen.findByTestId('detail-edit-open'));
    const form = await screen.findByTestId('detail-edit-form');
    expect(within(form).getByText('계보 부모 연결')).toBeTruthy();
    // 폼 안에 계보 표를 두 벌로 그리지 않는다
    expect(within(form).queryByTestId('lin-rows')).toBeNull();
    expect(within(form).queryByTestId('lin-graph')).toBeNull();
    fireEvent.click(within(form).getByTestId('edit-lineage-fix'));
    expect(await screen.findByTestId('lin-fix-modal')).toBeTruthy();
  });
});

describe('⑺ ⟨advisor ② F1⟩ 기준 Lv — 그래프 파생값이 아니라 사람이 고른 값', () => {
  it('그래프 노드는 Lv0(기록 없음 실값)이어도 사람 값 Lv2 가 기준이라 Lv1·Lv2 후보가 열린다', async () => {
    const details: Record<string, DatasetDetail> = {
      ...FIXTURE_DETAILS,
      [SELF]: {
        ...(FIXTURE_DETAILS[SELF] as DatasetDetail),
        basicInfo: {
          ...(FIXTURE_DETAILS[SELF] as DatasetDetail).basicInfo!,
          processingLevelUserSet: 'Lv2',
        },
      },
    };
    // 그래프의 「이 데이터」 노드는 서버 파생값(부모 없음 → Lv0)을 그대로 들고 온다 —
    // 이 값이 기준이면 Lv1 후보(`PARENT`)까지 막혀야 정상이다(버그 재현).
    renderDetail(emptyGraph(true, 0), undefined, fixtureDetailSource(details));
    const modal = await (async () => {
      fireEvent.click(await screen.findByTestId('lin-edit'));
      return screen.findByTestId('lin-fix-modal');
    })();
    await within(modal).findByTestId('lin-fix-picker');
    const parentBtn = within(modal).getByTestId(`lin-pick-${PARENT}`) as HTMLButtonElement;
    const overBtn = within(modal).getByTestId(`lin-pick-${OVER}`) as HTMLButtonElement;
    // 기준 = 사람 값 Lv2 → Lv1(`PARENT`) 은 고를 수 있고 Lv3(`OVER`) 만 막힌다
    expect(parentBtn.disabled).toBe(false);
    expect(overBtn.disabled).toBe(true);
    expect(within(modal).getByTestId(`lin-over-${OVER}`).textContent).toBe(parentOverReason(2));
  });
});

describe('⑻ ⟨advisor ② F2⟩ 서버 400 문구 — 봉투 message 를 그대로 올린다', () => {
  it('addParent 거절 시 서버 문구가 `lin-fix-error` 에 축자로 뜨고 모달은 열린 채 남는다', async () => {
    renderDetail(emptyGraph(true), { async addParent() { throw new Error('넘어간 Lv 예요.'); } });
    const modal = await (async () => {
      fireEvent.click(await screen.findByTestId('lin-edit'));
      return screen.findByTestId('lin-fix-modal');
    })();
    await within(modal).findByTestId('lin-fix-picker');
    fireEvent.click(within(modal).getByTestId(`lin-pick-${PARENT}`));
    fireEvent.click(within(modal).getByTestId('lin-fix-save'));
    expect((await within(modal).findByTestId('lin-fix-error')).textContent).toBe('넘어간 Lv 예요.');
    expect(screen.queryByTestId('lin-fix-modal')).toBeTruthy();
  });

  it('`apiLineageEditSource().addParent` 는 서버 봉투의 `message` 를 그대로 올린다', async () => {
    const original = globalThis.fetch;
    globalThis.fetch = vi.fn(
      async () =>
        new Response(JSON.stringify({ message: '이 부모는 자기보다 높은 단계예요.' }), {
          status: 400,
          headers: { 'content-type': 'application/json' },
        }),
    ) as typeof fetch;
    try {
      await expect(
        apiLineageEditSource().addParent(SELF, { parentDatasetId: PARENT, parentRole: '주입력' }),
      ).rejects.toThrow('이 부모는 자기보다 높은 단계예요.');
    } finally {
      globalThis.fetch = original;
    }
  });
});
