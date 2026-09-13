/**
 * `/lab-settings` 대표 제목 단계 — 이태헌 1차 검증 `D-6`(카드 ⑦ ⓐ 집행 · ⓑ 규약).
 *
 * 규약(spec §6 ㉮) = 화면당 `h1` 1개(그 화면의 이름) · 탭 본체 제목은 `h2` · 그 아래가 `h3`.
 * 대화상자 안 제목은 대화상자 기준으로 세고 화면 단계에 포함하지 않는다.
 *
 * 집행 범위는 **이 화면 하나**다. 나머지 화면은 후속 항목이라 여기서 재지 않는다.
 * 크기 고정은 jsdom 이 레이아웃을 계산하지 않으므로 **CSS 원문 계측**으로 가른다
 * (`CLAUDE.md §5-b` 주석 오탐 3건 — 주석을 지운 뒤 존재 단언으로 쓴다).
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
// @ts-expect-error — 타입 선언 없이 런타임만 쓴다(`design-fix-20260908` 와 같은 규율).
import { readFileSync } from 'node:fs';
// @ts-expect-error — 같은 이유.
import { resolve } from 'node:path';
import { MemoryRouter } from 'react-router-dom';
import { LabSettingsPage } from '../src/routes/LabSettingsPage';
import type { Lab, LabSource } from '../src/components/lab/labSource';
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

const SOURCE: LabSource = { read: async () => LAB, update: async () => LAB };
const MEMBERS: MembersPort = {
  list: async () => ({ ok: true, items: [] }),
  save: async () => ({ ok: true, items: [] }),
};

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/lab-settings']}>
      <SessionProvider account={account({ '연구실 설정': true })}>
        <LabSettingsPage port={MEMBERS} labSource={SOURCE} />
      </SessionProvider>
    </MemoryRouter>,
  );
}

// vitest 의 실행 뿌리는 `frontend/` 다(`vite.config.ts` 자리).
declare const process: { cwd(): string };

/** 주석을 지운 CSS 원문. 주석 안의 선언을 코드로 세지 않는다. */
const cssOf = (rel: string): string =>
  String(readFileSync(resolve(process.cwd(), rel), 'utf8')).replace(/\/\*[\s\S]*?\*\//g, '');

describe('연구실 설정 — 대표 제목 단계', () => {
  it('화면 제목이 `h1` 한 개이고 그 글자가 화면 이름이다', async () => {
    const { container } = renderPage();
    await waitFor(() => expect(screen.getByText('수자원순환연구실')).toBeTruthy());

    const h1s = Array.from(container.querySelectorAll('h1'));
    expect(h1s.map((h) => h.textContent)).toEqual(['연구실 설정']);
  });

  it('탭 본체 제목이 `h2` 이고 `h1` 다음 단계를 건너뛰지 않는다', async () => {
    const { container } = renderPage();
    await waitFor(() => expect(screen.getByText('수자원순환연구실')).toBeTruthy());

    // `연구실 정보` 탭 — 패널 제목은 h2 다.
    expect(container.querySelector('h2')?.textContent).toBe('연구실 정보');
    // 화면 본문(대화상자 밖)에 h3 가 서려면 그 앞에 h2 가 있어야 한다 — 단계 누락 0.
    const levels = Array.from(container.querySelectorAll('h1,h2,h3'))
      .map((h) => Number(h.tagName.slice(1)));
    const skipped = levels.filter((level, i) => i > 0 && level - (levels[i - 1] ?? level) > 1);
    expect(skipped).toEqual([]);
  });

  it('구성원 탭 제목도 `h2` 다', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByText('수자원순환연구실')).toBeTruthy());
    fireEvent.click(screen.getByRole('tab', { name: '구성원 · 권한' }));

    await waitFor(() =>
      expect(screen.getByRole('heading', { level: 2, name: '구성원 · 권한' })).toBeTruthy(),
    );
  });

  it('CSS 원문에 패널 제목(`h2`) 크기 고정 선언이 있다 — 단계가 크기를 바꾸지 않는다', () => {
    const members = cssOf('src/components/members/members.css');
    const lab = cssOf('src/components/lab/lab.css');
    expect(/\.card-h\s+h2\b[^{]*\{[^}]*font-size\s*:/.test(members)).toBe(true);
    expect(/\.settings-page\s+h1\b[^{]*\{[^}]*font-size\s*:/.test(members)).toBe(true);
    expect(/\.labinfo-card\s+\.card-h\s+h2\b/.test(lab)).toBe(true);
  });
});
