/**
 * `연구실 설정 > 연구실 정보` 탭 — 백지였던 자리(QA #1).
 *
 * 오라클은 정본이다:
 *  · `DataModel_공통_기반 §2` 「고치는 화면은 `연구실 설정 > 연구실 정보`」 · 항목 여덟 칸
 *  · `Policy_역할과_권한 나-1·나-2` 「연구실 정보 편집 · `연구실 설정` · **읽기는 전 구성원**」
 *  · 문안·폼 순서는 `mockups/제품_260817.html` S-07 `연구실 정보` 카드와 편집 모달 축자
 *  · 보내는 형태는 계약 `LabUpdate` (`contracts/seams/fe-core.yaml`)
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { LabSettingsPage } from '../src/routes/LabSettingsPage';
import type { LabSource, Lab } from '../src/components/lab/labSource';
import type { MembersPort } from '../src/components/members/port';
import { SessionProvider } from '../src/permission/session';
import { account } from './factories';

const LAB: Lab = {
  labId: '01JYZ9K7WQ3N8V4M2X6C5B0AHU',
  name: '수자원순환연구실',
  university: '한국대학교',
  department: '건설환경공학부',
  principalInvestigator: '사자 교수',
  researchField: '수자원 · 수문 · 기후',
  introduction: '기후·수문 자료를 모아 유역 단위 물 순환을 분석하는 연구실이에요.',
  defaultVisibility: '열림',
  memberCount: 5,
  openedAt: '2020-03-01T00:00:00Z',
};

/** 구성원 탭은 이 시험의 대상이 아니다 — 빈 대역을 준다. */
const MEMBERS: MembersPort = { list: async () => ({ ok: true, items: [] }), save: async () => ({ ok: true, items: [] }) };

function sourceOf(over: Partial<LabSource> = {}) {
  const update = vi.fn(async (changes) => ({ ...LAB, ...changes }) as Lab);
  const source: LabSource = { read: async () => LAB, update, ...over };
  return { source, update };
}

function renderTab(source: LabSource, perms: Record<string, boolean> = {}) {
  return render(
    <MemoryRouter initialEntries={['/lab-settings']}>
      <SessionProvider account={account(perms)}>
        <LabSettingsPage port={MEMBERS} labSource={source} />
      </SessionProvider>
    </MemoryRouter>,
  );
}

describe('연구실 정보 탭 — 읽기는 전 구성원', () => {
  it('탭 본문에 연구실 정보 여덟 칸이 선다 (백지가 아니다)', async () => {
    renderTab(sourceOf().source);
    await waitFor(() => expect(screen.getByText('수자원순환연구실')).toBeTruthy());
    for (const label of ['연구실 이름', '소속 대학', '학부/학과', '책임교수', '연구 분야',
                         '구성원 수', '데이터 공개 범위', '한 줄 소개']) {
      expect(screen.getByText(label)).toBeTruthy();
    }
    expect(screen.getByText('5명')).toBeTruthy();
  });

  it('`연구실 설정` 이 꺼진 연구원은 읽되 `정보 편집` 이 없다', async () => {
    renderTab(sourceOf().source);
    await waitFor(() => expect(screen.getByText('수자원순환연구실')).toBeTruthy());
    expect(screen.queryByText('정보 편집')).toBeNull();
  });

  it('읽지 못하면 서버 문안을 그대로 보인다', async () => {
    const source: LabSource = {
      read: async () => { throw new Error('연구실을 찾지 못했다.'); },
      update: async () => LAB,
    };
    renderTab(source);
    await waitFor(() => expect(screen.getByRole('alert').textContent).toBe('연구실을 찾지 못했다.'));
  });
});

describe('연구실 정보 탭 — 편집은 `연구실 설정` 스위치', () => {
  async function openForm(over: Partial<LabSource> = {}) {
    const { source, update } = sourceOf(over);
    renderTab(source, { '연구실 설정': true });
    await waitFor(() => expect(screen.getByText('정보 편집')).toBeTruthy());
    fireEvent.click(screen.getByText('정보 편집'));
    await waitFor(() => expect(screen.getByRole('dialog', { name: '연구실 정보 편집' })).toBeTruthy());
    return update;
  }

  it('권한자에게 `정보 편집` 이 보이고 일곱 칸 폼이 열린다', async () => {
    await openForm();
    for (const label of ['연구실 이름', '소속 대학', '학부 · 학과', '책임교수', '연구 분야',
                         '한 줄 소개', '데이터 공개 범위']) {
      expect(screen.getByLabelText(label)).toBeTruthy();
    }
    // 공개 범위는 계약이 고정한 두 값이다.
    const scope = screen.getByLabelText('데이터 공개 범위') as HTMLSelectElement;
    expect([...scope.options].map((o) => o.value)).toEqual(['열림', '잠김']);
  });

  it('저장하면 계약 `LabUpdate` 형태로 updateLab 을 부른다', async () => {
    const update = await openForm();
    fireEvent.change(screen.getByLabelText('연구실 이름'), { target: { value: '한강수문연구실' } });
    fireEvent.change(screen.getByLabelText('연구 분야'), { target: { value: '' } });
    fireEvent.change(screen.getByLabelText('데이터 공개 범위'), { target: { value: '잠김' } });
    fireEvent.click(screen.getByText('저장'));

    await waitFor(() => expect(update).toHaveBeenCalledTimes(1));
    expect(update).toHaveBeenCalledWith({
      name: '한강수문연구실',
      university: '한국대학교',
      department: '건설환경공학부',
      principalInvestigator: '사자 교수',
      researchField: null, // 빈 칸은 null 로 간다 — 계약이 여섯 칸에 null 을 허용한다
      introduction: '기후·수문 자료를 모아 유역 단위 물 순환을 분석하는 연구실이에요.',
      defaultVisibility: '잠김',
    });
    // 저장 뒤 읽기 표시가 새 값으로 갈린다.
    await waitFor(() => expect(screen.getByText('한강수문연구실')).toBeTruthy());
    expect(screen.getByTestId('labinfo-notice').textContent).toBe('연구실 정보를 저장했어요');
  });

  it('이름을 비우면 서버와 같은 문안으로 막고 부르지 않는다', async () => {
    const update = await openForm();
    fireEvent.change(screen.getByLabelText('연구실 이름'), { target: { value: '   ' } });
    fireEvent.click(screen.getByText('저장'));
    await waitFor(() => expect(screen.getByRole('alert').textContent).toBe('연구실 이름을 적어 주세요.'));
    expect(update).not.toHaveBeenCalled();
  });

  it('서버가 거절하면 그 문안을 폼 안에서 보이고 폼을 닫지 않는다', async () => {
    await openForm({
      update: async () => { throw new Error('연구실 설정 권한이 없어요.'); },
    });
    fireEvent.click(screen.getByText('저장'));
    await waitFor(() => expect(screen.getByRole('alert').textContent).toBe('연구실 설정 권한이 없어요.'));
    expect(screen.getByRole('dialog', { name: '연구실 정보 편집' })).toBeTruthy();
  });
});
