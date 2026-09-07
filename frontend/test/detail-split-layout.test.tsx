/**
 * WU-C2 · 데이터셋 상세 **좌우 배치** (축 ①-② · Ted 판정
 * 「좌 미리보기 sticky · 우 기본 정보＋파일 · 계보·활용 아래 전폭 · 960px 미만 한 열, 미리보기 먼저」).
 *
 * 오라클 = `dev-package/prd/rounds/R-C-2-frontend.md §2 WU-C2` 수용 기준 축자
 *  ⑴ 1200px 에서 grid 2열(좌 preview · 우 infogrid＋files) — **2분기 단언**
 *  ⑵ 960px 미만 1열이고 preview 가 먼저
 *  ⑶ `sec-lineage`·`sec-preview`·`sec-usage` 앵커 3개 존재
 *
 * ⚠ **jsdom 은 레이아웃을 계산하지 않는다** — 열 수·sticky 는 `getComputedStyle` 로 잴 수
 *   없다. 그래서 ㈎ DOM 구조(컨테이너·좌/우 자식)와 ㈏ **CSS 원문**(`detail.css`) 두 가지로
 *   잰다(집 관례 — WU-C1 `preview-slot-4x3.test.tsx` · `detail-section-menu.test.tsx` 와 같은 규율).
 * ⚠ 분기가 하나 빠져도 초록이 되는 것을 막으려고 **분기 건수 2 를 명시적으로 단언**한다.
 */
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { fixtureDetailSource } from '../src/components/detail/fixture';
import { fixtureLineageSource } from '../src/components/lineage/graphFixture';
import { DETAIL_SECTIONS } from '../src/components/detail/SectionMenu';
import detailCss from '../src/components/detail/detail.css?raw';

const OPEN_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA1'; // 낙동강 유역 강우 (2025)

/** 주석을 걷어낸 CSS 원문 — 선언이 아니라 설명문에 걸리는 것을 막는다. */
const CSS = detailCss.replace(/\/\*[\s\S]*?\*\//g, '');

/** `@media (…)` 한 덩이를 통째로 떠낸다(중괄호 짝을 센다). */
function mediaBlock(query: string): string {
  const at = CSS.indexOf(`@media ${query}`);
  expect(at, `미디어 질의 부재: @media ${query}`).toBeGreaterThan(-1);
  let i = CSS.indexOf('{', at);
  let depth = 0;
  const start = i;
  for (; i < CSS.length; i += 1) {
    if (CSS[i] === '{') depth += 1;
    else if (CSS[i] === '}') {
      depth -= 1;
      if (depth === 0) return CSS.slice(start, i);
    }
  }
  throw new Error(`닫히지 않은 미디어 덩이: ${query}`);
}

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
  return screen.findByRole('heading', { level: 1, name: '낙동강 유역 강우 (2025)' });
}

describe('WU-C2 · 상세 좌우 배치 — DOM 구조', () => {
  it('컨테이너 한 겹 안에서 좌 = 미리보기 · 우 = 기본 정보＋파일이다', async () => {
    const { container } = renderDetail();
    await settle();

    const split = container.querySelector('.dt-split');
    expect(split, '.dt-split 컨테이너가 없다').not.toBeNull();
    const cols = Array.from((split as Element).children);
    expect(cols).toHaveLength(2);
    const [left, right] = cols as [Element, Element];
    expect(left.className).toContain('dt-split-l');
    expect(right.className).toContain('dt-split-r');

    // 좌 = 미리보기 앵커가 **첫 자식**이다 (960px 미만 한 열에서 먼저 오는 근거이기도 하다)
    expect(left.firstElementChild?.id).toBe('sec-preview');
    expect(left.querySelector('#sec-preview')).not.toBeNull();

    // 우 = 기본 정보 격자 ＋ 파일 목록
    expect(right.querySelector('.infogrid'), '오른쪽 열에 기본 정보 격자가 없다').not.toBeNull();
    expect(
      right.querySelector('[data-testid="detail-grid-actions"]'),
      '오른쪽 열에 격자 붙이기 줄이 없다',
    ).not.toBeNull();
    expect(right.textContent).toContain('파일');
  });

  it('계보·활용은 컨테이너 **밖** 아래에서 전폭이다', async () => {
    const { container } = renderDetail();
    await settle();

    const split = container.querySelector('.dt-split') as Element;
    const lineage = document.getElementById('sec-lineage');
    const usage = document.getElementById('sec-usage');
    expect(lineage, 'sec-lineage 가 없다').not.toBeNull();
    expect(usage, 'sec-usage 가 없다').not.toBeNull();
    expect(split.contains(lineage as Node)).toBe(false);
    expect(split.contains(usage as Node)).toBe(false);

    // DOM 차례 — 미리보기 컨테이너 → 계보 → 활용
    const order = Node.DOCUMENT_POSITION_FOLLOWING;
    expect(split.compareDocumentPosition(lineage as Node) & order).toBe(order);
    expect((lineage as Node).compareDocumentPosition(usage as Node) & order).toBe(order);
  });

  it('앵커 3개가 남고 구역 메뉴 차례·이름표는 그대로다', async () => {
    renderDetail();
    await settle();

    expect(DETAIL_SECTIONS.map((s) => s.id)).toEqual(['sec-lineage', 'sec-preview', 'sec-usage']);
    expect(DETAIL_SECTIONS.map((s) => s.label)).toEqual(['계보', '미리보기', '활용/접근']);
    for (const s of DETAIL_SECTIONS) {
      expect(document.getElementById(s.id), `${s.id} 가 DOM 에 없다`).not.toBeNull();
      // 메뉴가 가리키는 자리가 실제로 있다 — 앵커 이동이 계속 닿는다
      expect(document.querySelector(`a[href="#${s.id}"]`), `${s.id} 링크 부재`).not.toBeNull();
    }
  });
});

describe('WU-C2 · 상세 좌우 배치 — CSS 원문 계측', () => {
  it('분기는 정확히 **2개**다 (≥960 두 열 · ≤959 한 열)', () => {
    const branches = CSS.match(/@media\s*\([^)]*\)\s*\{[^]*?\.dt-split\b/g) ?? [];
    expect(branches).toHaveLength(2);
  });

  it('≥960px 은 2열 grid 이고 왼쪽이 sticky 다', () => {
    const wide = mediaBlock('(min-width: 960px)');
    expect(wide).toContain('.dt-split');
    expect(wide).toMatch(/\.dt-split\s*\{[^}]*display:\s*grid/);
    expect(wide).toMatch(/grid-template-columns:\s*[^;]*minmax\([^)]*\)[^;]*minmax\(/);
    expect(wide).toMatch(/\.dt-split-l\s*\{[^}]*position:\s*sticky/);
    expect(wide).toMatch(/\.dt-split-l\s*\{[^}]*top:\s*var\(--dt-split-sticky-top\)/);
  });

  it('959px 이하는 한 열이다 (DOM 차례 그대로 미리보기 먼저 · `order` 뒤집기 없음)', () => {
    const narrow = mediaBlock('(max-width: 959px)');
    expect(narrow).toMatch(/\.dt-split\s*\{[^}]*display:\s*block/);
    expect(narrow).not.toMatch(/order:/);
    expect(narrow).toMatch(/\.dt-split-l\s*\{[^}]*position:\s*static/);
  });

  it('`.detail-page` 최대 폭 1200px 과 토큰 사용은 그대로다 (새 색 상수 0)', () => {
    expect(CSS).toMatch(/\.detail-page\s*\{[^}]*max-width:\s*1200px/);
    const added = CSS.slice(CSS.indexOf('--dt-split-sticky-top'));
    expect(added).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    expect(added).toContain('var(--space-6)');
  });
});
