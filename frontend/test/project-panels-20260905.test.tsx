// WU-A7 · PRD-23 프로젝트·논문 패널 분리 — ③ 연결 단계의 표시 방식이다.
//
// 오라클 = `dev-package/prd/rounds/R-A-3-frontend.md` §2 WU-A7 수용 기준.
// 칩 나열을 두 패널(국가과제 / 논문)로 가르고, 패널 안은 **행**이 위에서 아래로 쌓인다.
// `+ 새 프로젝트 만들기` 는 두 패널 아래 **한 곳에만** 있고 유형을 먼저 묻는다.
// 계약·서버·DB 변경 0 — 유형값(`ProjectRow.type`)은 이미 있다.
import { useState } from 'react';
import { describe, expect, it } from 'vitest';
import { fireEvent, render, screen, within } from '@testing-library/react';

import { StepTwo } from '../src/components/upload/RegisterArea';
import { SessionProvider } from '../src/permission/session';
import type { PickedProject, ProjectRow, ProjectSource } from '../src/components/upload/types';
import type { CurrentAccount } from '../src/api/client';

const P_NATIONAL = '01JYZ9K7WQ3N8V4M2X6C5B0PR1';
const P_PAPER_A = '01JYZ9K7WQ3N8V4M2X6C5B0PR2';
const P_PAPER_B = '01JYZ9K7WQ3N8V4M2X6C5B0PR3';

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

/** 실제 모달과 같은 결선 — 고른 목록이 부모 상태에 쌓인다 (`UploadModal.projects`). */
function Harness(props: { initial?: PickedProject[] }) {
  const [picked, setPicked] = useState<PickedProject[]>(props.initial ?? []);
  return (
    <SessionProvider account={account()}>
      <StepTwo source={source} picked={picked} onPicked={setPicked} />
    </SessionProvider>
  );
}

function panel(type: '국가과제' | '논문'): HTMLElement {
  return screen.getByTestId(`reg-proj-panel-${type}`);
}

function rowNames(type: '국가과제' | '논문'): string[] {
  const list = within(panel(type)).queryByTestId(`reg-proj-rows-${type}`);
  if (!list) return [];
  return Array.from(list.querySelectorAll('[data-testid="reg-proj-row-name"]')).map(
    (el) => el.textContent ?? '',
  );
}

async function pick(projectId: string) {
  fireEvent.change(await screen.findByTestId('reg-proj-select'), { target: { value: projectId } });
  fireEvent.click(screen.getByRole('button', { name: '+ 추가' }));
}

describe('WU-A7 — 연관 프로젝트는 국가과제·논문 두 패널로 갈라 행으로 쌓인다', () => {
  it('국가과제 1건 · 논문 2건을 고르면 두 패널이 각각 1행 · 2행을 쌓는다', async () => {
    render(
      <Harness
        initial={[
          { projectId: P_NATIONAL, name: ROWS[0]!.name, type: '국가과제' },
          { projectId: P_PAPER_A, name: ROWS[1]!.name, type: '논문' },
          { projectId: P_PAPER_B, name: ROWS[2]!.name, type: '논문' },
        ]}
      />,
    );
    await screen.findByTestId('reg-proj-panels');

    expect(rowNames('국가과제')).toEqual([ROWS[0]!.name]);
    expect(rowNames('논문')).toEqual([ROWS[1]!.name, ROWS[2]!.name]);
    // 칩이 아니라 행이다 — 종전 칩 묶음은 남아 있지 않다
    expect(screen.queryByTestId('reg-proj-chips')).toBeNull();
  });

  it('행마다 이름과 `해제` 버튼이 있고, 해제하면 그 패널에서 빠진다', async () => {
    render(
      <Harness
        initial={[
          { projectId: P_PAPER_A, name: ROWS[1]!.name, type: '논문' },
          { projectId: P_PAPER_B, name: ROWS[2]!.name, type: '논문' },
        ]}
      />,
    );
    await screen.findByTestId('reg-proj-panels');

    fireEvent.click(within(panel('논문')).getByRole('button', { name: `${ROWS[1]!.name} 해제` }));
    expect(rowNames('논문')).toEqual([ROWS[2]!.name]);
  });

  it('프로젝트를 새로 추가하면 해당 유형 패널에 행이 아래로 붙는다 — 화면 이동이 없다', async () => {
    render(<Harness initial={[{ projectId: P_PAPER_A, name: ROWS[1]!.name, type: '논문' }]} />);
    await screen.findByTestId('reg-proj-select');

    await pick(P_PAPER_B);
    expect(rowNames('논문')).toEqual([ROWS[1]!.name, ROWS[2]!.name]);

    await pick(P_NATIONAL);
    expect(rowNames('국가과제')).toEqual([ROWS[0]!.name]);
    // 같은 카드 안에서 그대로 보인다 — 다른 화면으로 옮겨 가지 않는다
    expect(screen.getByTestId('reg-s2')).toContainElement(screen.getByTestId('reg-proj-panels'));
  });

  it('논문 0건이어도 논문 패널이 빈 상태 문구와 함께 남는다', async () => {
    render(<Harness initial={[{ projectId: P_NATIONAL, name: ROWS[0]!.name, type: '국가과제' }]} />);
    await screen.findByTestId('reg-proj-panels');

    expect(panel('논문')).toBeInTheDocument();
    expect(screen.getByTestId('reg-proj-empty-논문')).toHaveTextContent('아직 담은 논문이 없어요.');
    expect(rowNames('논문')).toEqual([]);
  });

  it('둘 다 0건이어도 두 패널이 각각 빈 상태로 선다', async () => {
    render(<Harness />);
    await screen.findByTestId('reg-proj-panels');

    expect(screen.getByTestId('reg-proj-empty-국가과제')).toHaveTextContent(
      '아직 담은 국가과제가 없어요.',
    );
    expect(screen.getByTestId('reg-proj-empty-논문')).toHaveTextContent('아직 담은 논문이 없어요.');
  });

  it('`+ 새 프로젝트 만들기` 는 화면에 한 개이고 두 패널 아래 공통 자리에 있다', async () => {
    render(<Harness />);
    const panels = await screen.findByTestId('reg-proj-panels');

    const links = screen.getAllByRole('button', { name: '+ 새 프로젝트 만들기' });
    expect(links).toHaveLength(1);
    // 패널마다 두지 않는다 — 패널 안에는 없고, DOM 상 두 패널 뒤에 온다
    expect(panels.contains(links[0]!)).toBe(false);
    expect(panels.compareDocumentPosition(links[0]!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('링크를 누르면 유형(국가과제·논문)을 먼저 고르는 칸이 뜬다', async () => {
    render(<Harness />);
    await screen.findByTestId('reg-proj-panels');

    fireEvent.click(screen.getByRole('button', { name: '+ 새 프로젝트 만들기' }));
    const form = await screen.findByTestId('reg-proj-quick');
    const sel = within(form).getByLabelText('유형') as HTMLSelectElement;
    expect(Array.from(sel.options).map((o) => o.value)).toEqual(['국가과제', '논문']);
  });

  it('빠르게 만든 논문이 논문 패널 행으로 붙는다', async () => {
    render(<Harness />);
    await screen.findByTestId('reg-proj-panels');

    fireEvent.click(screen.getByRole('button', { name: '+ 새 프로젝트 만들기' }));
    const form = await screen.findByTestId('reg-proj-quick');
    fireEvent.change(within(form).getByLabelText('유형'), { target: { value: '논문' } });
    fireEvent.change(within(form).getByLabelText('과제·논문 이름'), {
      target: { value: '한강 저수지 운영 규칙 재산정' },
    });
    fireEvent.click(within(form).getByRole('button', { name: '만들고 담기' }));

    expect(await within(panel('논문')).findByText('한강 저수지 운영 규칙 재산정')).toBeInTheDocument();
    expect(rowNames('국가과제')).toEqual([]);
  });
});
