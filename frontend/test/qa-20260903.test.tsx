/**
 * 화면 검수(2026-09-03 · `dev-package/notes/QA-SCREENS-20260903.md`)가 잡은 소수리의 회귀 시험.
 * 오라클은 각 시험 머리말에 **정본 파일·행**으로 적는다 — 여기서 새 한국어 라벨을 만들지 않는다.
 *
 * 다루는 행 — #20(범례 자릿수) · #22(화살표 라벨) · #23(빈 값 앞 구분자) · #24(휠 preventDefault)
 *            · #13·#14(0건 문구) · #8(프로젝트 표 Verified 표기).
 * **빈 집합 위에서 통과하지 않는다** — 단언 전에 대상이 1건 이상임을 먼저 잰다 (`CLAUDE.md §4`).
 */
import { act, render, renderHook, screen, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { legendValue } from '../src/components/preview/format';
import { useZoomPan } from '../src/components/preview/useZoomPan';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { SearchResultsPage } from '../src/routes/SearchResultsPage';
import { ProjectDetailPage } from '../src/routes/ProjectDetailPage';
import { fixtureDetailSource } from '../src/components/detail/fixture';
import { FIXTURE_LINEAGE, fixtureLineageSource } from '../src/components/lineage/graphFixture';
import type { LineageGraph, LineageGraphSource } from '../src/components/lineage/graphTypes';
import type { SearchSource } from '../src/components/search/types';
import { fixtureProjectSource, FIXTURE_PROJECTS } from '../src/components/project/fixture';

/* ─────────────────────────────────────────────────────────────── #20 범례 자릿수 */
describe('#20 범례 값 — 사람이 읽는 자릿수 (검수 #20 · 관찰: 17자리 출력)', () => {
  it('부동소수의 꼬리를 유효숫자 4자리에서 끊는다', () => {
    expect(legendValue(0.18798384070396423)).toBe('0.188');
    expect(legendValue(0.27763089040915173)).toBe('0.2776');
  });
  it('정수·0 은 그대로 둔다 — 없는 소수점을 지어내지 않는다', () => {
    expect(legendValue(0)).toBe('0');
    expect(legendValue(5)).toBe('5');
    expect(legendValue(-12)).toBe('-12');
  });
  it('사람이 못 읽는 크기는 지수로 적는다 — 0 으로 뭉개지 않는다', () => {
    expect(legendValue(0.0000001234)).toContain('e');
    expect(legendValue(12345678)).toContain('e');
  });
});

/* ───────────────────────────────────────── #22·#23 계보 상자 — 라벨과 빈 값 표기 */
const OPEN_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA1';

function only(graph: LineageGraph): LineageGraphSource {
  return { async get() { return graph; } };
}
function renderDetail(datasetId: string, lineage: LineageGraphSource = fixtureLineageSource()) {
  return render(
    <MemoryRouter initialEntries={[`/datasets/${datasetId}`]}>
      <Routes>
        <Route
          path="/datasets/:datasetId"
          element={<DatasetDetailPage source={fixtureDetailSource()} lineageSource={lineage} />}
        />
        <Route path="/datasets" element={<div>카탈로그</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('#23 부모 카드 — 가공 방식이 없으면 구분자도 없다 (검수 #23)', () => {
  it('빈 가공 방식 앞의 `·` 로 줄이 시작하지 않는다', async () => {
    const g = structuredClone(FIXTURE_LINEAGE[OPEN_ID]!) as LineageGraph;
    const e = g.edges.find((x) => x.parentDatasetId !== null && x.childDatasetId !== null);
    expect(e).toBeDefined();
    e!.method = null;
    renderDetail(OPEN_ID, only(g));
    await screen.findByTestId('lineage-section');
    const subs = Array.from(document.querySelectorAll('.lrow .ln-sub'));
    expect(subs.length).toBeGreaterThan(0);
    for (const s of subs) expect((s.textContent ?? '').trim().startsWith('·')).toBe(false);
  });
});

describe('#22 화살표 라벨 — 잘려도 전문에 닿는다 (검수 #22)', () => {
  it('가공 방식 라벨에 전문이 title 로 붙는다', async () => {
    renderDetail(OPEN_ID);
    await screen.findByTestId('lineage-section');
    const ways = screen.getAllByTestId('lin-method');
    expect(ways.length).toBeGreaterThan(0);
    for (const w of ways) {
      const t = w.getAttribute('title');
      expect(t && t.length > 0).toBe(true);
      expect((w.textContent ?? '')).toContain(t!.slice(0, 4));
    }
  });
});

/* ────────────────────────────────────────────────── #24 휠 — passive 가 아니어야 한다 */
describe('#24 지도 확대·축소 — 휠 리스너는 passive 가 아니다 (검수 #24 · 콘솔 오류 14건)', () => {
  /**
   * React 17+ 는 `wheel` 을 루트에 **passive 로** 위임한다. 그래서 `onWheel` 안의
   * `preventDefault()` 는 아무 일도 하지 않았고 브라우저가
   * `Unable to preventDefault inside passive event listener` 를 14건 찍었다.
   * ⚠ jsdom 은 passive 의미를 흉내 내지 않아 **`defaultPrevented` 로는 이 결함이 잡히지
   * 않는다** — 그래서 재는 것은 「리스너가 `{ passive: false }` 로 걸렸는가」다.
   */
  it('viewport 에 wheel 리스너를 { passive: false } 로 건다', () => {
    const seen: { type: string; opts: unknown }[] = [];
    const el = document.createElement('div');
    const orig = el.addEventListener.bind(el);
    el.addEventListener = ((type: string, fn: never, opts: never) => {
      seen.push({ type, opts });
      return orig(type, fn as never, opts as never);
    }) as typeof el.addEventListener;

    const { result } = renderHook(() => useZoomPan());
    act(() => result.current.viewportRef(el));

    const wheels = seen.filter((s) => s.type === 'wheel');
    expect(wheels.length).toBeGreaterThan(0);
    for (const w of wheels) {
      expect(w.opts).toBeTypeOf('object');
      expect((w.opts as AddEventListenerOptions).passive).toBe(false);
    }
  });
});

/* ───────────────────────────────────────────────── #13·#14 검색 0건 상태 (E-02 F-02) */
const SCOPE = { labName: '수자원순환연구실', searchedCount: 13 };
function emptySearch(): SearchSource {
  return {
    async search() {
      return { scope: SCOPE, items: [], isDataQuery: true, degraded: false, totalCount: 0 };
    },
  } as unknown as SearchSource;
}
function renderSearch(source: SearchSource) {
  return render(
    <MemoryRouter initialEntries={['/search?q=금강+염분']}>
      <Routes>
        <Route path="/search" element={<SearchResultsPage source={source} />} />
        <Route path="/datasets" element={<div>카탈로그</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('#13·#14 검색 0건 — 목업 F-02 의 네 조각 (E-02 `데이터_찾기_260817.html` 448~453행)', () => {
  it('`맞는 것이 없었어요` 가 화면에 한 번만 나온다', async () => {
    renderSearch(emptySearch());
    const box = await screen.findByTestId('search-empty');
    expect(box).toBeInTheDocument();
    const n = (document.body.textContent ?? '').split('맞는 것이 없었어요').length - 1;
    expect(n).toBe(1);
  });

  it('제목 `맞는 데이터를 못 찾았어요` · 뒤진 범위·개수 · 두 버튼 · 업로드 권유가 선다', async () => {
    renderSearch(emptySearch());
    const box = await screen.findByTestId('search-empty');
    const w = within(box);
    expect(w.getByText('맞는 데이터를 못 찾았어요')).toBeInTheDocument();
    expect(box.textContent).toContain('수자원순환연구실');
    expect(box.textContent).toContain('13');
    expect(w.getByText('단어를 바꿔 다시 찾기')).toBeInTheDocument();
    expect(w.getByText('카탈로그에서 훑어보기')).toBeInTheDocument();
    expect(w.getByText('이 데이터를 갖고 계시면 업로드해 주세요.')).toBeInTheDocument();
  });
});

/* ─────────────────────────────── #8 프로젝트 상세 표 — 카탈로그와 같은 Verified 표기 */
describe('#8 프로젝트 상세 표 Verified — 카탈로그와 같은 표기 (〈282〉 규칙 확장)', () => {
  it('승인이 오지 않은 행은 취소선·비활성 모양이고, `—` 를 쓰지 않는다', async () => {
    const id = FIXTURE_PROJECTS[0]!.projectId;
    render(
      <MemoryRouter initialEntries={[`/projects/${id}`]}>
        <Routes>
          <Route
            path="/projects/:projectId"
            element={<ProjectDetailPage source={fixtureProjectSource()} />}
          />
        </Routes>
      </MemoryRouter>,
    );
    const cells = await screen.findAllByTestId('dataset-verified');
    expect(cells.length).toBeGreaterThan(0);
    const pending = cells.filter((c) => c.textContent?.trim() === 'Verified');
    expect(pending.length).toBeGreaterThan(0);
    for (const c of pending) {
      expect(c.querySelector('.verified--pending')).not.toBeNull();
      expect(c.querySelector('[aria-disabled="true"]')).not.toBeNull();
    }
    for (const c of cells) expect(c.textContent?.trim()).not.toBe('—');
  });
});
