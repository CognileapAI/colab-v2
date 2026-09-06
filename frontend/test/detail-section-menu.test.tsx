/**
 * WU-A8 · PRD-24 (미결-9 ⓑ) — 상세 구역 메뉴 sticky ＋ 활성 표시.
 *
 * 오라클 = `dev-package/prd/rounds/R-A-3-frontend.md` §2 WU-A8 수용 기준 3줄.
 * ⛔ 이 시험은 **탭·패널 전환이 없음**을 함께 못 박는다 — 정본 `Policy_데이터셋_상세 §1.3-1`
 *   「한 페이지 스크롤 · 탭으로 숨기지 않는다」가 개정되지 않았다는 증명이다.
 *
 * sticky 여부는 jsdom 이 계산해 주지 않는다(스타일시트를 얹지 않는다). 그래서
 * ⑴ 화면에서는 **메뉴가 계속 붙어 있는 자리에 그대로 있다**는 것을 DOM 으로 재고,
 * ⑵ `position: sticky` **선언 자체**는 `detail.css` 원문에서 잰다
 *   (`project-css-tokens.test.ts` 머리말의 `?raw` 선례 그대로).
 */
import { act, render, screen, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { fixtureDetailSource } from '../src/components/detail/fixture';
import { fixtureLineageSource } from '../src/components/lineage/graphFixture';
import detailCss from '../src/components/detail/detail.css?raw';

const OPEN_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA1'; // 낙동강 유역 강우 (2025)

/** 스크롤 감시 대역 — 시험이 「어느 구역에 들어왔다」를 손으로 먹인다. */
type IoCallback = (entries: Array<Partial<IntersectionObserverEntry>>) => void;
let callbacks: IoCallback[] = [];

class FakeObserver {
  constructor(cb: IoCallback) {
    callbacks.push(cb);
  }
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
  takeRecords(): [] {
    return [];
  }
  root = null;
  rootMargin = '';
  thresholds = [];
}

beforeEach(() => {
  callbacks = [];
  (globalThis as Record<string, unknown>).IntersectionObserver = FakeObserver;
});

afterEach(() => {
  delete (globalThis as Record<string, unknown>).IntersectionObserver;
});

function renderDetail() {
  return render(
    <MemoryRouter initialEntries={[`/datasets/${OPEN_ID}`]}>
      <Routes>
        <Route
          path="/datasets/:datasetId"
          element={
            <DatasetDetailPage
              source={fixtureDetailSource()}
              lineageSource={fixtureLineageSource()}
            />
          }
        />
        <Route path="/datasets" element={<div>카탈로그</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

async function settle() {
  const h = await screen.findByRole('heading', { level: 1, name: '낙동강 유역 강우 (2025)' });
  // 글자가 섰다고 **효과가 돈 것은 아니다** — 지연 효과(감시 붙이기)는 커밋 뒤에 따로 돈다.
  // 여기서 한 틱을 흘려 주지 않으면 시험이 감시가 붙기 전에 스크롤을 먹인다.
  await act(async () => {
    await Promise.resolve();
  });
  return h;
}

/**
 * 「구역에 들어왔다」를 감시 대역으로 먹인다. 실제 관측기가 그러듯 **떠난 구역도 함께**
 * 보고한다(들어온 구역만 알려 주는 관측기는 없다).
 */
const ANCHORS = ['sec-lineage', 'sec-preview', 'sec-usage'];

function enterSection(anchorId: string) {
  const entries = ANCHORS.map((id) => {
    const target = document.getElementById(id);
    expect(target, `${id} 가 DOM 에 없다`).not.toBeNull();
    return {
      target: target as Element,
      isIntersecting: id === anchorId,
      intersectionRatio: id === anchorId ? 0.9 : 0,
    };
  });
  act(() => {
    for (const cb of callbacks) cb(entries);
  });
}

describe('WU-A8 — 구역 메뉴가 화면 위에 남는다', () => {
  it('계보 · 미리보기 · 활용/접근 세 칸이 앵커로 서 있다', async () => {
    renderDetail();
    await settle();
    const menu = screen.getByTestId('detail-section-menu');
    const links = within(menu).getAllByRole('link');
    expect(links.map((a) => a.textContent)).toEqual(['계보', '미리보기', '활용/접근']);
    expect(links.map((a) => a.getAttribute('href'))).toEqual([
      '#sec-lineage',
      '#sec-preview',
      '#sec-usage',
    ]);
  });

  it('`활용/접근` 을 눌러 이동해도 메뉴가 그대로 보인다', async () => {
    const { container } = renderDetail();
    await settle();
    const menu = screen.getByTestId('detail-section-menu');
    act(() => {
      within(menu).getByText('활용/접근').click();
    });
    enterSection('sec-usage');
    // 눌러도 사라지지 않는다 — 같은 노드가 문서에 그대로 있다
    expect(container.contains(menu)).toBe(true);
    expect(screen.getByTestId('detail-section-menu')).toBe(menu);
    expect(menu).toBeVisible();
  });

  it('메뉴 규칙이 `position: sticky` 다 (detail.css 원문)', () => {
    const rule = detailCss
      .split('}')
      .find((block) => block.includes('.dsec-menu') && block.includes('position'));
    expect(rule, '.dsec-menu 에 position 선언이 없다').toBeDefined();
    expect(rule).toMatch(/position:\s*sticky/);
    expect(rule).toMatch(/top:/);
  });
});

describe('WU-A8 — 현재 구역을 활성 표시한다', () => {
  it('미리보기 구역에 들어가면 `미리보기` 가 활성이다', async () => {
    renderDetail();
    await settle();
    enterSection('sec-preview');
    const menu = screen.getByTestId('detail-section-menu');
    const preview = within(menu).getByText('미리보기');
    expect(preview).toHaveAttribute("aria-current", "true");
    expect(preview).toHaveAttribute('data-active', 'true');
    expect(within(menu).getByText('계보')).toHaveAttribute('data-active', 'false');
    expect(within(menu).getByText('활용/접근')).toHaveAttribute('data-active', 'false');
  });

  it('구역이 바뀌면 활성도 옮겨 간다 — 활성은 언제나 한 칸이다', async () => {
    renderDetail();
    await settle();
    enterSection('sec-preview');
    enterSection('sec-usage');
    const menu = screen.getByTestId('detail-section-menu');
    const active = within(menu)
      .getAllByRole('link')
      .filter((a) => a.getAttribute('data-active') === 'true');
    expect(active).toHaveLength(1);
    expect(active[0]).toHaveTextContent('활용/접근');
  });
});

describe('WU-A8 — 정본 §1.3-1: 어느 구역도 숨기지 않는다', () => {
  it('어느 구역에 있든 세 구역이 전부 DOM 에 남아 보인다', async () => {
    renderDetail();
    await settle();
    for (const anchor of ['sec-lineage', 'sec-preview', 'sec-usage']) {
      enterSection(anchor);
      for (const id of ['sec-lineage', 'sec-preview', 'sec-usage']) {
        const node = document.getElementById(id);
        expect(node, `${id} 가 DOM 에서 사라졌다`).not.toBeNull();
        expect(node as HTMLElement).toBeVisible();
        expect((node as HTMLElement).hidden).toBe(false);
        expect((node as HTMLElement).getAttribute('aria-hidden')).toBeNull();
      }
    }
  });

  it('탭 역할(`tab`·`tabpanel`)을 만들지 않았다', async () => {
    renderDetail();
    await settle();
    expect(screen.queryAllByRole('tab')).toHaveLength(0);
    expect(screen.queryAllByRole('tablist')).toHaveLength(0);
    expect(screen.queryAllByRole('tabpanel')).toHaveLength(0);
  });
});
