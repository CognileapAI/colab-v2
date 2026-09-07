/**
 * WU-B2 · PRD-16 — 변수 표 5열 (`변수 · 단위 · 값 범위 · 결측률 · 대표`).
 *
 * 오라클 = `dev-package/prd/rounds/R-B-1-db.md §2` WU-B2 수용 기준 중 **화면 몫 셋**.
 *   ⑴ 변수 3행에 각각 다른 단위 → 상세가 세 행을 각자의 단위와 함께 그린다(읽기 전용).
 *   ⑵ 변수 행이 1개일 때 삭제 시도 → 막히고 「변수는 하나 이상 있어야 해요」가 뜬다.
 *   ⑶ 대표는 라디오 한 자리 — 고르면 앞의 대표가 풀린다(둘이 되지 않는다).
 * 그리고 열 순서·라벨이 **rev1 `vt-head` 축자**임을 잰다 — 그 5열이 PRD-16 의 확정값이다.
 *
 * ⛔ 등록 화면의 배선(`+ 변수 추가` 로 만든 행이 요청에 실린다)은 `test/upload.test.tsx`
 *    §8 ① 에 있다 — 같은 화면의 다른 시험과 한자리에 둔다.
 *
 * 모든 단언은 **대상 건수를 먼저 잰다** — 빈 집합 통과(green-by-skip)를 막는다.
 */
import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { useState } from 'react';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { SessionProvider } from '../src/permission/session';
import { FIXTURE_DETAILS } from '../src/components/detail/fixture';
import {
  VARIABLE_COLUMNS,
  VariableTable,
  emptyVariableRow,
  variablesPayload,
  type VariableRow,
} from '../src/components/common/VariableTable';
import { AT_LEAST_ONE_VARIABLE } from '../src/components/common/toastCopy';
import type { CurrentAccount, PermissionSwitchSet } from '../src/api/client';
import type { DatasetDetail } from '../src/components/detail/types';

const OPEN_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA1';
const BASE = FIXTURE_DETAILS[OPEN_ID] as DatasetDetail;

const THREE: VariableRow[] = [
  { name: '강우량', unit: 'mm', valueRange: '0~350', missingRate: '0.2%', representative: true },
  { name: '기온', unit: '℃', valueRange: '-30~40', missingRate: null, representative: false },
  { name: '유출량', unit: 'm3/s', valueRange: null, missingRate: null, representative: false },
];

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

async function click(el: Element | null) {
  fireEvent.click(el as HTMLElement);
  await act(async () => {});
}

/** 편집 가능한 표를 상태와 함께 띄운다 — 삭제·대표 선택은 상태 갱신까지 봐야 뜻이 있다. */
function Harness(props: { initial: VariableRow[] }) {
  const [rows, setRows] = useState<VariableRow[]>(props.initial);
  const [notice, setNotice] = useState<string | null>(null);
  return (
    <>
      <VariableTable rows={rows} onRows={setRows} onBlocked={setNotice} />
      {notice ? <p data-testid="vt-notice">{notice}</p> : null}
    </>
  );
}

// ═══ 열 구성 — PRD-16 이 확정한 5열 ═══════════════════════════════════════
describe('PRD-16 열 구성', () => {
  it('머리가 `변수 · 단위 · 값 범위 · 결측률 · 대표` 다 (rev1 `vt-head` 축자)', () => {
    render(<Harness initial={THREE} />);
    const head = screen.getByTestId('vt-head');
    const labels = within(head)
      .getAllByRole('columnheader')
      .map((th) => th.textContent ?? '');
    // 편집 표는 삭제 칸 하나가 더 있다 — 앞 다섯이 요구된 열이다.
    expect(labels.length).toBeGreaterThanOrEqual(5);
    expect(labels.slice(0, 5)).toEqual([...VARIABLE_COLUMNS]);
  });
});

// ═══ ⑵ 마지막 한 행은 지워지지 않는다 ════════════════════════════════════
describe('PRD-16 수용 기준 ⑵ — 마지막 행 삭제 차단', () => {
  it('행이 1개일 때 삭제를 누르면 막히고 「변수는 하나 이상 있어야 해요」가 뜬다', async () => {
    render(<Harness initial={[{ ...emptyVariableRow(), name: '강우량', representative: true }]} />);
    expect(screen.getAllByTestId('vt-row')).toHaveLength(1);
    await click(screen.getByTestId('vt-del-0'));
    expect(screen.getAllByTestId('vt-row')).toHaveLength(1);
    expect(screen.getByTestId('vt-notice')).toHaveTextContent(AT_LEAST_ONE_VARIABLE);
  });

  it('행이 2개면 삭제된다 — 차단이 「언제나 못 지운다」가 아니다', async () => {
    render(<Harness initial={THREE.slice(0, 2)} />);
    expect(screen.getAllByTestId('vt-row')).toHaveLength(2);
    await click(screen.getByTestId('vt-del-1'));
    expect(screen.getAllByTestId('vt-row')).toHaveLength(1);
    expect(screen.queryByTestId('vt-notice')).toBeNull();
  });

  it('대표 행을 지우면 남은 첫 행이 대표가 된다 — 서버의 자동 보정과 같은 규칙', async () => {
    render(<Harness initial={THREE} />);
    await click(screen.getByTestId('vt-del-0'));
    const radios = screen.getAllByRole('radio') as HTMLInputElement[];
    expect(radios).toHaveLength(2);
    expect(radios.map((r) => r.checked)).toEqual([true, false]);
  });
});

// ═══ ⑶ 대표는 한 행뿐 ════════════════════════════════════════════════════
describe('PRD-16 — 대표 라디오', () => {
  it('다른 행을 고르면 앞의 대표가 풀린다 (둘이 되지 않는다)', async () => {
    render(<Harness initial={THREE} />);
    await click(screen.getByTestId('vt-rep-2'));
    const radios = screen.getAllByRole('radio') as HTMLInputElement[];
    expect(radios).toHaveLength(3);
    expect(radios.map((r) => r.checked)).toEqual([false, false, true]);
  });
});

// ═══ `+ 변수 추가` ═══════════════════════════════════════════════════════
describe('PRD-16 — 행 추가', () => {
  it('`+ 변수 추가` 가 빈 행 하나를 끝에 붙인다', async () => {
    render(<Harness initial={THREE} />);
    await click(screen.getByTestId('vt-add'));
    expect(screen.getAllByTestId('vt-row')).toHaveLength(4);
    expect((screen.getByTestId('vt-name-3') as HTMLInputElement).value).toBe('');
  });
});

// ═══ 계약 형상으로 옮기는 자리 ═══════════════════════════════════════════
describe('PRD-16 — 요청 형상', () => {
  it('빈 이름 행은 싣지 않고, 한 행도 안 적었으면 열쇠 자체가 없다', () => {
    expect(variablesPayload([emptyVariableRow()])).toBeNull();
    const got = variablesPayload([
      { ...emptyVariableRow(), name: ' tp ', unit: ' mm ' },
      emptyVariableRow(),
    ]);
    expect(got).toEqual([
      { name: 'tp', unit: 'mm', valueRange: null, missingRate: null, representative: false },
    ]);
  });
});

// ═══ ⑴ 상세는 같은 표를 읽기 전용으로 그린다 ═════════════════════════════
describe('PRD-16 수용 기준 ⑴ — 상세의 읽기 전용 표', () => {
  it('세 행이 각자의 단위와 함께 보이고 입력 칸이 없다', async () => {
    const detail: DatasetDetail = {
      ...BASE,
      basicInfo: { ...BASE.basicInfo!, variables: THREE },
    };
    render(
      <MemoryRouter initialEntries={[`/datasets/${OPEN_ID}`]}>
        <SessionProvider account={account()}>
          <Routes>
            <Route
              path="/datasets/:datasetId"
              element={<DatasetDetailPage source={{ async get() { return detail; } }} />}
            />
          </Routes>
        </SessionProvider>
      </MemoryRouter>,
    );
    await screen.findByTestId('variable-table');
    const rows = screen.getAllByTestId('vt-row');
    expect(rows).toHaveLength(3);
    expect(rows.map((r) => within(r).getAllByRole('cell')[0]?.textContent)).toEqual([
      '강우량', '기온', '유출량',
    ]);
    expect(rows.map((r) => within(r).getAllByRole('cell')[1]?.textContent)).toEqual([
      'mm', '℃', 'm3/s',
    ]);
    // **읽기 전용이다** — 상세에서 값을 고치는 자리는 편집 모드이고(WU-A3R) 이 표가 아니다.
    expect(screen.queryByTestId('vt-add')).toBeNull();
    expect(screen.queryByTestId('vt-name-0')).toBeNull();
    for (const radio of screen.getAllByRole('radio') as HTMLInputElement[]) {
      expect(radio.disabled).toBe(true);
    }
  });
});
