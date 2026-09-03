/**
 * S-03 카탈로그 `주제` 열 메뉴 — **고정 4목록** (레인 Q-D · QA 검수 #9).
 * 오라클 =
 *   · `Policy_업로드와_계보_확정.md §5` 주제 고정 4값 (`〈55〉` DB CHECK · `upload/types.ts` TOPICS)
 *   · `Policy_데이터_찾기.md 116행` 「0건 값은 미리 흐리게 표시(비활성), 빈 결과로 보내지 않음」
 * 실물 결함 = 값 목록이 **표에 실린 행에서만** 만들어져 `토지피복·LULC` 가 아예 없었다.
 */
import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { DatasetsPage } from '../src/routes/DatasetsPage';
import { fixtureCatalogSource } from '../src/components/catalog/fixture';
import { TOPICS } from '../src/components/upload/types';

async function click(el: Element) {
  fireEvent.click(el);
  await act(async () => {});
}

function renderCatalog() {
  return render(
    <MemoryRouter initialEntries={['/datasets']}>
      <Routes>
        <Route path="/datasets" element={<DatasetsPage source={fixtureCatalogSource()} />} />
        <Route path="*" element={<div />} />
      </Routes>
    </MemoryRouter>,
  );
}

async function openTopicMenu() {
  renderCatalog();
  await screen.findByRole('button', { name: '주제' });
  await click(screen.getByRole('button', { name: '주제' }));
  return screen.getByRole('menu');
}

function labels(menu: HTMLElement) {
  return within(menu)
    .getAllByRole('menuitemcheckbox')
    .map((el) => el.textContent!.replace(/\s*\(\d+\)\s*$/, '').trim());
}

describe('§5 주제 열 메뉴 — 고정 4목록', () => {
  it('네 값이 **전부** 서고 정본 차례를 지킨다 (표에 없는 값도 사라지지 않는다)', async () => {
    const menu = await openTopicMenu();
    expect(labels(menu)).toEqual([...TOPICS]);
  });

  it('표에 0건인 값은 감추지 않고 `(0)` 으로 흐리게 둔다 (116행)', async () => {
    const menu = await openTopicMenu();
    const lulc = within(menu).getByRole('menuitemcheckbox', { name: /토지피복·LULC/ });
    expect(lulc.textContent).toContain('(0)');
    expect(lulc.className).toContain('is-zero');
  });

  it('서버가 준 건수는 그대로 쓴다 — 화면이 세지 않는다', async () => {
    const menu = await openTopicMenu();
    expect(
      within(menu).getByRole('menuitemcheckbox', { name: /강우·강수/ }).textContent,
    ).toContain('(3)');
  });
});
