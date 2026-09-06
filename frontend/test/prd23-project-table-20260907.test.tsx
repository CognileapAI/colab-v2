// WU-A7R · PRD-23 개정본(2026-09-06 Ted 판정 미결-r2-3 ⓐ) ＋ PRD-42 · PRD-43 J-12.
//
// 오라클 = `dev-package/prd/rounds/R-A2.md §2-③` 수용 기준 축자.
// 종전 두 패널(WU-A7 · `test/project-panels-20260905.test.tsx`)은 **폐기**다 —
// 「두 패널 분리를 걷고 한 표 ＋ 유형 열로 간다」가 판정 축자다.
//
// 지키는 것
//  · 표 한 장 · 열 = `유형` · `이름` · `해제`.
//  · 유형 배지는 **저장값 `kind`**(`PickedProject.type`)에서 온다 — 이름 문자열로 판정하지 않는다.
//  · 연관 0건이면 **표 자체가 화면에 없다**.
//  · `+ 새 프로젝트 만들기` 는 영역 맨 아래 **한 곳**.
//  · 빠른 생성 안내문은 `toastCopy.ts` 의 `J-12` 행에서 온다(하드코드 0건 · PRD-43).
import { useState } from 'react';
import { describe, expect, it } from 'vitest';
import { fireEvent, render, screen, within } from '@testing-library/react';

import { StepTwo } from '../src/components/upload/RegisterArea';
import { QUICK_PROJECT_NOTE } from '../src/components/common/toastCopy';
import { SessionProvider } from '../src/permission/session';
import type { PickedProject, ProjectRow, ProjectSource } from '../src/components/upload/types';
import type { CurrentAccount } from '../src/api/client';

const P_NATIONAL = '01JYZ9K7WQ3N8V4M2X6C5B0PR1';
const P_PAPER_A = '01JYZ9K7WQ3N8V4M2X6C5B0PR2';
const P_PAPER_B = '01JYZ9K7WQ3N8V4M2X6C5B0PR3';
/** 이름에 `논문` 이 들어간 **국가과제** — 이름 문자열 판정이면 배지가 틀린다. */
const P_TRAP = '01JYZ9K7WQ3N8V4M2X6C5B0PR4';

function row(projectId: string, name: string, type: '국가과제' | '논문'): ProjectRow {
  return {
    projectId,
    name,
    type,
    status: '진행 중',
    period: null,
    description: null,
    datasetCount: 0,
    verifiedCount: 0,
    unknownLineageCount: 0,
  } as ProjectRow;
}

const ROWS: ProjectRow[] = [
  row(P_NATIONAL, '낙동강 유역 홍수기 강우-유출 응답 분석', '국가과제'),
  row(P_PAPER_A, '도시 불투수면 확대와 첨두유량', '논문'),
  row(P_PAPER_B, '위성 강수 보정 기법 비교', '논문'),
  row(P_TRAP, '논문 후속 국가과제 2단계', '국가과제'),
];

function account(): CurrentAccount {
  return {
    accountId: '01JYZ9K7WQ3N8V4M2X6C5B0AC1',
    name: '호랑이',
    email: 'tiger@example.ac.kr',
    role: '연구원',
    labId: '01JYZ9K7WQ3N8V4M2X6C5B0LB1',
    labName: '수자원순환연구실',
    permissions: { '업로드·편집': true, '프로젝트 생성': true },
  } as unknown as CurrentAccount;
}

const source: ProjectSource = {
  async list() {
    return ROWS;
  },
  async create(body) {
    return { projectId: '01JYZ9K7WQ3N8V4M2X6C5B0PR9', name: body.name, type: body.type };
  },
};

function Harness(props: { initial?: PickedProject[]; source?: ProjectSource }) {
  const [picked, setPicked] = useState<PickedProject[]>(props.initial ?? []);
  return (
    <SessionProvider account={account()}>
      <StepTwo source={props.source ?? source} picked={picked} onPicked={setPicked} />
    </SessionProvider>
  );
}

/** 서버가 400 ＋ 축자 문면으로 되돌리는 자리 (PRD-42 · `projectSource.create` 가 옮긴다). */
const DUPLICATE_NAME_MESSAGE = '같은 이름의 프로젝트가 이미 있어요. 목록에서 골라 주세요';
const refusingSource: ProjectSource = {
  async list() {
    return ROWS;
  },
  async create() {
    throw new Error(DUPLICATE_NAME_MESSAGE);
  },
};

function table(): HTMLElement {
  return screen.getByTestId('reg-proj-table');
}

function cells(testid: string): string[] {
  return Array.from(table().querySelectorAll(`[data-testid="${testid}"]`)).map(
    (el) => el.textContent ?? '',
  );
}

async function pick(projectId: string) {
  fireEvent.change(await screen.findByTestId('reg-proj-select'), { target: { value: projectId } });
  fireEvent.click(screen.getByRole('button', { name: '+ 추가' }));
}

describe('WU-A7R — 연관 프로젝트·논문을 한 표에 유형 열로 쌓는다 (PRD-23 개정본)', () => {
  it('국가과제 1건 · 논문 2건이면 표 한 장에 3행이 쌓이고 유형 열이 저장값대로다', async () => {
    render(
      <Harness
        initial={[
          { projectId: P_NATIONAL, name: ROWS[0]!.name, type: '국가과제' },
          { projectId: P_PAPER_A, name: ROWS[1]!.name, type: '논문' },
          { projectId: P_PAPER_B, name: ROWS[2]!.name, type: '논문' },
        ]}
      />,
    );
    await screen.findByTestId('reg-proj-table');

    // 표는 **한 장**이다 — 유형별로 갈라진 패널이 남아 있지 않다
    expect(screen.getAllByTestId('reg-proj-table')).toHaveLength(1);
    expect(screen.queryByTestId('reg-proj-panels')).toBeNull();
    expect(screen.queryByTestId('reg-proj-panel-국가과제')).toBeNull();
    expect(screen.queryByTestId('reg-proj-panel-논문')).toBeNull();

    expect(cells('reg-proj-row-name')).toEqual([ROWS[0]!.name, ROWS[1]!.name, ROWS[2]!.name]);
    expect(cells('reg-proj-row-kind')).toEqual(['국가과제', '논문', '논문']);
  });

  it('열 머리가 `유형` · `이름` · `해제` 세 개다', async () => {
    render(<Harness initial={[{ projectId: P_PAPER_A, name: ROWS[1]!.name, type: '논문' }]} />);
    await screen.findByTestId('reg-proj-table');

    const heads = within(table())
      .getAllByRole('columnheader')
      .map((el) => el.textContent ?? '');
    expect(heads).toEqual(['유형', '이름', '해제']);
  });

  it('`해제` 열의 단추를 누르면 그 행이 표에서 빠진다', async () => {
    render(
      <Harness
        initial={[
          { projectId: P_PAPER_A, name: ROWS[1]!.name, type: '논문' },
          { projectId: P_PAPER_B, name: ROWS[2]!.name, type: '논문' },
        ]}
      />,
    );
    await screen.findByTestId('reg-proj-table');

    fireEvent.click(within(table()).getByRole('button', { name: `${ROWS[1]!.name} 해제` }));
    expect(cells('reg-proj-row-name')).toEqual([ROWS[2]!.name]);
  });

  it('프로젝트를 새로 추가하면 행이 표 아래로 붙는다 — 화면 이동이 없다', async () => {
    render(<Harness initial={[{ projectId: P_PAPER_A, name: ROWS[1]!.name, type: '논문' }]} />);
    await screen.findByTestId('reg-proj-select');

    await pick(P_NATIONAL);
    expect(cells('reg-proj-row-name')).toEqual([ROWS[1]!.name, ROWS[0]!.name]);
    expect(cells('reg-proj-row-kind')).toEqual(['논문', '국가과제']);
    expect(screen.getByTestId('reg-s2')).toContainElement(table());
  });

  it('연관 0건이면 표가 화면에 없다 — 빈 표·빈 패널이 남지 않는다', async () => {
    render(<Harness />);
    await screen.findByTestId('reg-s2');

    expect(screen.queryByTestId('reg-proj-table')).toBeNull();
    expect(screen.queryByTestId('reg-proj-panels')).toBeNull();
    expect(screen.queryByTestId('reg-proj-empty-국가과제')).toBeNull();
    expect(screen.queryByTestId('reg-proj-empty-논문')).toBeNull();
  });

  it('마지막 한 건을 해제하면 표가 다시 사라진다', async () => {
    render(<Harness initial={[{ projectId: P_PAPER_A, name: ROWS[1]!.name, type: '논문' }]} />);
    await screen.findByTestId('reg-proj-table');

    fireEvent.click(within(table()).getByRole('button', { name: `${ROWS[1]!.name} 해제` }));
    expect(screen.queryByTestId('reg-proj-table')).toBeNull();
  });

  it('이름에 `논문` 이 든 국가과제도 유형 열이 저장값 `국가과제` 다 — 이름 문자열로 판정하지 않는다', async () => {
    render(<Harness initial={[{ projectId: P_TRAP, name: ROWS[3]!.name, type: '국가과제' }]} />);
    await screen.findByTestId('reg-proj-table');

    expect(cells('reg-proj-row-name')).toEqual(['논문 후속 국가과제 2단계']);
    expect(cells('reg-proj-row-kind')).toEqual(['국가과제']);
  });

  it('`+ 새 프로젝트 만들기` 는 화면에 한 개이고 표 아래 자리에 있다', async () => {
    render(<Harness initial={[{ projectId: P_PAPER_A, name: ROWS[1]!.name, type: '논문' }]} />);
    const t = await screen.findByTestId('reg-proj-table');

    const links = screen.getAllByRole('button', { name: '+ 새 프로젝트 만들기' });
    expect(links).toHaveLength(1);
    expect(t.contains(links[0]!)).toBe(false);
    expect(t.compareDocumentPosition(links[0]!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('링크를 누르면 유형(국가과제·논문)을 먼저 고르는 칸이 뜬다', async () => {
    render(<Harness />);
    await screen.findByTestId('reg-s2');

    fireEvent.click(screen.getByRole('button', { name: '+ 새 프로젝트 만들기' }));
    const form = await screen.findByTestId('reg-proj-quick');
    const sel = within(form).getByLabelText('유형') as HTMLSelectElement;
    expect(Array.from(sel.options).map((o) => o.value)).toEqual(['국가과제', '논문']);
  });

  it('빠른 생성 안내문은 `toastCopy.ts` 의 J-12 행 축자다', async () => {
    render(<Harness />);
    await screen.findByTestId('reg-s2');

    fireEvent.click(screen.getByRole('button', { name: '+ 새 프로젝트 만들기' }));
    const form = await screen.findByTestId('reg-proj-quick');
    expect(form).toHaveTextContent(QUICK_PROJECT_NOTE);
    // 종전 하드코드 문면은 남아 있지 않다 (PRD-43 「한 곳에서 온다」)
    expect(form).not.toHaveTextContent('여기서는 유형과 이름만 받아요');
  });

  it('빠르게 만든 논문이 표의 행으로 붙고 유형 열이 `논문` 이다', async () => {
    render(<Harness />);
    await screen.findByTestId('reg-s2');

    fireEvent.click(screen.getByRole('button', { name: '+ 새 프로젝트 만들기' }));
    const form = await screen.findByTestId('reg-proj-quick');
    fireEvent.change(within(form).getByLabelText('유형'), { target: { value: '논문' } });
    fireEvent.change(within(form).getByLabelText('과제·논문 이름'), {
      target: { value: '한강 저수지 운영 규칙 재산정' },
    });
    fireEvent.click(within(form).getByRole('button', { name: '만들고 담기' }));

    expect(await screen.findByTestId('reg-proj-table')).toBeInTheDocument();
    expect(cells('reg-proj-row-name')).toEqual(['한강 저수지 운영 규칙 재산정']);
    expect(cells('reg-proj-row-kind')).toEqual(['논문']);
  });

  it('이름이 겹치면 서버가 되돌린 축자 문면이 뜨고 표에 행이 붙지 않는다 (PRD-42)', async () => {
    render(<Harness source={refusingSource} />);
    await screen.findByTestId('reg-s2');

    fireEvent.click(screen.getByRole('button', { name: '+ 새 프로젝트 만들기' }));
    const form = await screen.findByTestId('reg-proj-quick');
    fireEvent.change(within(form).getByLabelText('과제·논문 이름'), {
      target: { value: '이미 있는 이름' },
    });
    fireEvent.click(within(form).getByRole('button', { name: '만들고 담기' }));

    expect(await screen.findByTestId('reg-proj-quick-error')).toHaveTextContent(
      DUPLICATE_NAME_MESSAGE,
    );
    expect(screen.queryByTestId('reg-proj-table')).toBeNull();
    // 거절이라 칸이 닫히지 않는다 — 사람이 이름만 고쳐 다시 누른다
    expect(screen.getByTestId('reg-proj-quick')).toBeInTheDocument();
  });

  it('⚠ 빈 이름 문면은 이 회차가 건드리지 않는다 — 중복 문면이 그 자리에 오지 않는다', async () => {
    render(<Harness source={refusingSource} />);
    await screen.findByTestId('reg-s2');

    fireEvent.click(screen.getByRole('button', { name: '+ 새 프로젝트 만들기' }));
    const form = await screen.findByTestId('reg-proj-quick');
    fireEvent.click(within(form).getByRole('button', { name: '만들고 담기' }));

    expect(screen.queryByTestId('reg-proj-quick-error')).toBeNull();
  });
});
