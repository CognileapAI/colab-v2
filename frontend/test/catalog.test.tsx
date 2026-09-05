/**
 * S-03 카탈로그 — 정본 대비 시험.
 * 오라클은 `E-02_데이터_찾기/documents/Policy_데이터_찾기.md` (v1.8) 와 그 목업이다.
 * 화면 글자는 정본에서 그대로 온다 — 여기서 새 한국어 라벨을 만들지 않는다.
 */
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { DatasetsPage } from '../src/routes/DatasetsPage';
import { fixtureCatalogSource } from '../src/components/catalog/fixture';
import { DownloadContext } from '../src/components/detail/download';
import type { DownloadTicket, FileSource } from '../src/components/detail/types';

function Where() {
  const l = useLocation();
  return <div data-testid="where">{l.pathname}</div>;
}

/** 다운로드는 티켓이다 (`〈339〉-(다)`) — 표는 `downloadTicket` 만 부르고 바이트는 startDownload 가 받는다. */
function fakeFiles() {
  const tickets: string[] = [];
  const source: FileSource = {
    async list() { throw new Error('카탈로그는 파일 목록을 부르지 않는다'); },
    async downloadTicket(datasetId) {
      tickets.push(datasetId);
      return { url: `/api/v1/downloads/T-${datasetId}`, expiresAt: 'x',
               fileName: 'bundle.zip', byteSize: null, scope: '묶음' };
    },
    async add() { throw new Error('부르지 않는다'); },
    async replace() { throw new Error('부르지 않는다'); },
    async remove() { throw new Error('부르지 않는다'); },
  };
  return { source, tickets };
}

function renderCatalog() {
  const files = fakeFiles();
  const downloads: DownloadTicket[] = [];
  const view = render(
    <MemoryRouter initialEntries={['/datasets']}>
      <DownloadContext.Provider value={(t) => { downloads.push(t); }}>
        <Routes>
          <Route
            path="/datasets"
            element={<DatasetsPage source={fixtureCatalogSource()} fileSource={files.source} />}
          />
          <Route path="*" element={<Where />} />
        </Routes>
      </DownloadContext.Provider>
    </MemoryRouter>,
  );
  return Object.assign(view, { tickets: files.tickets, downloads });
}

/** 새 의존성을 들이지 않는다 — 이미 있는 fireEvent 로 누른다 */
async function click(el: Element) {
  fireEvent.click(el);
  await act(async () => {});
}

/** 표의 데이터 행(헤더 제외) */
function bodyRows() {
  return screen.getAllByRole('row').slice(1);
}

async function settle() {
  await screen.findByText('nakdong_precip_2025_Lv2.nc');
}

describe('§5 열 구성 — 8열 + 오른쪽 끝 빠른 작업 자리', () => {
  it('열 이름은 정본 표기 그대로 여덟이다', async () => {
    renderCatalog();
    await settle();
    const head = within(screen.getAllByRole('row')[0]!);
    expect(head.getAllByRole('columnheader').slice(0, 8).map((th) => th.textContent?.trim())).toEqual(
      ['데이터셋', '주제', 'Level', '프로젝트', '업로더', '수정일', '계보', 'Verified'],
    );
  });

  it('아홉 번째 칸이 빠른 작업 자리다', async () => {
    renderCatalog();
    await settle();
    const head = within(screen.getAllByRole('row')[0]!);
    const cols = head.getAllByRole('columnheader');
    expect(cols).toHaveLength(9);
    expect(cols[8]).toHaveAttribute('aria-label', '빠른 작업');
  });

  it('조건 패널도 좌측 사이드바도 두지 않는다 — 조건은 열 헤더에만 있다', async () => {
    renderCatalog();
    await settle();
    expect(screen.queryByRole('complementary')).toBeNull();
    // 열 이름 자체가 버튼이다 (§8 표 헤더)
    const head = within(screen.getAllByRole('row')[0]!);
    expect(within(head.getAllByRole('columnheader')[1]!).getByRole('button')).toHaveTextContent('주제');
  });
});

describe('§5 기본 정렬 — 수정일 최신순', () => {
  it('처음 그려질 때 수정일 열이 내림차순으로 잡혀 있다', async () => {
    renderCatalog();
    await settle();
    const head = within(screen.getAllByRole('row')[0]!);
    expect(head.getAllByRole('columnheader')[5]).toHaveAttribute('aria-sort', 'descending');
  });

  it('행이 수정일 최신순으로 놓인다', async () => {
    renderCatalog();
    await settle();
    const dates = bodyRows().map((tr) => within(tr).getAllByRole('cell')[5]!.textContent!.trim());
    expect(dates).toEqual([...dates].sort().reverse());
  });
});

describe('§8 열 메뉴', () => {
  it('위쪽은 정렬(오름차순·내림차순), 아래쪽은 값 목록과 건수다', async () => {
    renderCatalog();
    await settle();
    await click(screen.getByRole('button', { name: '주제' }));
    const menu = screen.getByRole('menu');
    expect(within(menu).getByRole('menuitem', { name: '오름차순' })).toBeInTheDocument();
    expect(within(menu).getByRole('menuitem', { name: '내림차순' })).toBeInTheDocument();
    expect(within(menu).getByRole('menuitemcheckbox', { name: /강우·강수/ })).toHaveTextContent('(3)');
  });

  it('값을 고르는 동안 메뉴는 열려 있고, 여러 개를 고를 수 있다', async () => {
    renderCatalog();
    await settle();
    await click(screen.getByRole('button', { name: '주제' }));
    await click(screen.getByRole('menuitemcheckbox', { name: /강우·강수/ }));
    expect(screen.getByRole('menu')).toBeInTheDocument();
    await click(screen.getByRole('menuitemcheckbox', { name: /지형·DEM/ }));
    expect(screen.getByRole('menu')).toBeInTheDocument();
    expect(screen.getByRole('menuitemcheckbox', { name: /강우·강수/ })).toHaveAttribute(
      'aria-checked',
      'true',
    );
    expect(screen.getByRole('menuitemcheckbox', { name: /지형·DEM/ })).toHaveAttribute(
      'aria-checked',
      'true',
    );
  });

  it('주제 값 목록은 잠긴 4값(`〈55〉`) 밖으로 나가지 않는다 — 미분류 행은 값을 만들지 않는다', async () => {
    renderCatalog();
    await settle();
    await click(screen.getByRole('button', { name: '주제' }));
    const menu = screen.getByRole('menu');
    const values = within(menu)
      .getAllByRole('menuitemcheckbox')
      .map((el) => el.textContent!.replace(/\s*\(\d+\)\s*$/, '').trim());
    expect(values.every((v) => ['강우·강수', '식생·NDVI', '지형·DEM', '토지피복·LULC'].includes(v))).toBe(
      true,
    );
  });

  it('같은 열 이름을 다시 누르면 닫힌다', async () => {
    renderCatalog();
    await settle();
    await click(screen.getByRole('button', { name: '주제' }));
    expect(screen.getByRole('menu')).toBeInTheDocument();
    await click(screen.getByRole('button', { name: '주제' }));
    expect(screen.queryByRole('menu')).toBeNull();
  });

  it('조건이 걸린 열에는 `이 열 조건 지우기` 가 생긴다', async () => {
    renderCatalog();
    await settle();
    await click(screen.getByRole('button', { name: '주제' }));
    expect(screen.queryByRole('menuitem', { name: '이 열 조건 지우기' })).toBeNull();
    await click(screen.getByRole('menuitemcheckbox', { name: /강우·강수/ }));
    await click(screen.getByRole('menuitem', { name: '이 열 조건 지우기' }));
    expect(screen.queryByRole('menu')).toBeNull();
    expect(screen.queryByText('적용된 조건')).toBeNull();
  });

  it('조건이 걸린 열은 점 하나로, 정렬이 걸린 열은 화살표로 알린다', async () => {
    renderCatalog();
    await settle();
    await click(screen.getByRole('button', { name: '주제' }));
    await click(screen.getByRole('menuitemcheckbox', { name: /강우·강수/ }));
    const head = within(screen.getAllByRole('row')[0]!);
    expect(head.getAllByRole('columnheader')[1]).toHaveClass('is-filtered');
    expect(head.getAllByRole('columnheader')[5]).toHaveClass('is-sorted');
  });
});

describe('§5 값별 건수 — 다른 열 조건을 먼저 적용하고, 0건은 감추지 않고 흐리게', () => {
  it('0건인 값이 목록에 남아 있고 흐리게 표시된다', async () => {
    renderCatalog();
    await settle();
    await click(screen.getByRole('button', { name: '주제' }));
    await click(screen.getByRole('menuitemcheckbox', { name: /강우·강수/ }));
    await click(screen.getByRole('button', { name: '주제' })); // 닫기
    await click(screen.getByRole('button', { name: '계보' }));
    const zero = screen.getByRole('menuitemcheckbox', { name: /기록 없음/ });
    expect(zero).toHaveTextContent('(0)');
    expect(zero).toHaveClass('is-zero');
  });
});

describe('§8 적용된 조건 칩 줄', () => {
  it('조건이 없으면 줄째로 없다', async () => {
    renderCatalog();
    await settle();
    expect(screen.queryByText('적용된 조건')).toBeNull();
    expect(screen.queryByRole('button', { name: '전체 해제' })).toBeNull();
  });

  it('조건이 걸리면 표 바로 위에 `열 이름 + 값` 칩과 `전체 해제` 가 놓인다', async () => {
    renderCatalog();
    await settle();
    await click(screen.getByRole('button', { name: '주제' }));
    await click(screen.getByRole('menuitemcheckbox', { name: /강우·강수/ }));
    const bar = screen.getByTestId('applied-conditions');
    expect(within(bar).getByText('적용된 조건')).toBeInTheDocument();
    expect(bar).toHaveTextContent('주제');
    expect(bar).toHaveTextContent('강우·강수');
    await click(within(bar).getByRole('button', { name: '전체 해제' }));
    expect(screen.queryByTestId('applied-conditions')).toBeNull();
  });
});

describe('§5 계보 열 — 넷 중 하나, 숫자를 붙이지 않는다', () => {
  it('모든 행의 계보 칸이 네 표기 중 하나이고 숫자가 없다', async () => {
    renderCatalog();
    await settle();
    const 넷 = ['확정', '확인 필요', '기록 없음', '원천'];
    for (const tr of bodyRows()) {
      const t = within(tr).getAllByRole('cell')[6]!.textContent!.trim();
      expect(넷).toContain(t);
      expect(t).not.toMatch(/[0-9]/);
    }
  });
});

describe('§5 프로젝트 열 · 조각 묶음', () => {
  it('프로젝트가 2건 이상이면 대표 이름 + `외 N` 칩이다', async () => {
    renderCatalog();
    await settle();
    const cell = within(bodyRows()[0]!).getAllByRole('cell')[3]!;
    expect(cell).toHaveTextContent('홍수기 강우-유출 분석');
    expect(within(cell).getByText('외 1')).toBeInTheDocument();
  });

  it('파일이 여러 건이면 묶음 이름 + `조각 N` 칩이다', async () => {
    renderCatalog();
    await settle();
    const cell = within(bodyRows()[0]!).getAllByRole('cell')[0]!;
    expect(within(cell).getByText('조각 4')).toBeInTheDocument();
  });

  it('잠긴 행에도 `조각 N` 칩이 뜬다 (PLAN-SoT §9-㊼)', async () => {
    renderCatalog();
    await settle();
    const locked = bodyRows().find((tr) => within(tr).queryByText('잠김'))!;
    expect(within(within(locked).getAllByRole('cell')[0]!).getByText('조각 3')).toBeInTheDocument();
  });
});

describe('§8 잠긴 카탈로그 행 — 표에서 사라지지 않는다', () => {
  it('자물쇠와 `잠김` 칩이 붙고 업로더는 그대로 보인다', async () => {
    renderCatalog();
    await settle();
    const locked = bodyRows().find((tr) => within(tr).queryByText('잠김'))!;
    expect(within(locked).getByTestId('lock-icon')).toBeInTheDocument();
    expect(within(locked).getAllByRole('cell')[4]).toHaveTextContent('토끼');
  });

  it('잠긴 행에는 빠른 작업도 접근 요청 버튼도 두지 않는다', async () => {
    renderCatalog();
    await settle();
    const locked = bodyRows().find((tr) => within(tr).queryByText('잠김'))!;
    expect(within(locked).queryByRole('button', { name: /엿보기/ })).toBeNull();
    expect(within(locked).queryByRole('button', { name: /다운로드/ })).toBeNull();
    expect(within(locked).queryByRole('button', { name: /접근 요청/ })).toBeNull();
  });

  it('열린 행에는 빠른 작업 두 가지가 있다', async () => {
    renderCatalog();
    await settle();
    const open = bodyRows()[0]!;
    expect(within(open).getByRole('button', { name: /엿보기/ })).toBeInTheDocument();
    expect(within(open).getByRole('button', { name: /다운로드/ })).toBeInTheDocument();
  });

  it('다운로드는 링크가 아니라 **버튼 → 티켓 → startDownload** 다 — `<a href>` 에는 Bearer 가 실리지 않는다', async () => {
    const { container, tickets, downloads } = renderCatalog();
    await settle();
    expect(container.querySelector('a[href*="/download"]')).toBeNull();
    const open = bodyRows()[0]!;
    const btn = within(open).getByRole('button', { name: 'nakdong_precip_2025_Lv2.nc 다운로드' });
    await click(btn);
    await waitFor(() => expect(downloads).toHaveLength(1));
    expect(tickets).toHaveLength(1);
    expect(tickets[0]).toMatch(/^[0-9A-Z]{26}$/);
    expect(downloads[0]!.url).toBe(`/api/v1/downloads/T-${tickets[0]}`);
    // 행 클릭(상세로 이동)을 삼킨다 — 다운로드가 상세를 열지 않는다
    expect(screen.queryByTestId('where')).toBeNull();
  });

  it('잠긴 행을 눌러도 상세로 간다 (요청은 거기서 한다)', async () => {
    renderCatalog();
    await settle();
    const locked = bodyRows().find((tr) => within(tr).queryByText('잠김'))!;
    await click(within(locked).getAllByRole('cell')[1]!);
    expect(screen.getByTestId('where').textContent).toMatch(/^\/datasets\/[0-9A-Z]{26}$/);
  });
});

describe('§8 표 — 헤더 고정 · 스크롤 래퍼 한 곳', () => {
  it('가로·세로 스크롤을 맡는 래퍼가 정확히 하나이고 표를 감싼다', async () => {
    const { container } = renderCatalog();
    await settle();
    const wraps = container.querySelectorAll('[data-scroll="both"]');
    expect(wraps).toHaveLength(1);
    expect(wraps[0]!.querySelector('table')).not.toBeNull();
  });

  /**
   * 정본 `Policy_데이터_찾기.md:156` 축자 「헤더는 세로 스크롤에도 위에 고정된다」.
   * 종전 회차들은 이 조항을 **읽기로만** 확인했다 — jsdom 이 stylesheet 를 싣지 않아
   * 계산값이 비었기 때문이다. 원인은 도구가 아니라 설정이었다: `DatasetsPage` 가
   * `catalog.css` 를 import 하는데 vitest 기본값이 css 를 빈 것으로 stub 한다.
   * `vite.config.ts` 의 `test.css.include` 로 이 파일 하나만 실제로 싣고 계산값으로 잰다.
   */
  it('헤더 칸이 계산값으로 sticky · top 0 이다', async () => {
    renderCatalog();
    await settle();
    const head = within(screen.getAllByRole('rowgroup')[0]!);
    const ths = head.getAllByRole('columnheader');
    expect(ths.length).toBeGreaterThan(0);
    for (const th of ths) {
      const cs = getComputedStyle(th);
      expect(cs.position).toBe('sticky');
      expect(cs.top).toBe('0px');
    }
  });
});

describe('§9 조건 결과 0건', () => {
  it('정본 문구를 그대로 안내하고 전체 해제로 복구한다', async () => {
    renderCatalog();
    await settle();
    await click(screen.getByRole('button', { name: '주제' }));
    await click(screen.getByRole('menuitemcheckbox', { name: /강우·강수/ }));
    await click(screen.getByRole('button', { name: '주제' }));
    await click(screen.getByRole('button', { name: '계보' }));
    await click(screen.getByRole('menuitemcheckbox', { name: /기록 없음/ }));
    expect(screen.getByText('조건에 맞는 데이터가 없어요. 조건을 하나 풀어 보세요.')).toBeInTheDocument();
    await click(screen.getByRole('button', { name: '전체 해제' }));
    expect(bodyRows().length).toBeGreaterThan(0);
  });
});

describe('§1.2 카탈로그는 AI 를 쓰지 않는다', () => {
  it('AI 표시(코랄/보라 액센트)·자연어 입력칸이 없다', async () => {
    const { container } = renderCatalog();
    await settle();
    expect(container.querySelector('[data-ai]')).toBeNull();
    expect(screen.queryByRole('searchbox')).toBeNull();
    expect(screen.queryByRole('textbox')).toBeNull();
  });
});

describe('§8 상호 안내 — 반대 길이 그 릴리스에 없을 때 (정본 v1.9)', () => {
  it('점선 박스가 남고, 표 헤더의 조건을 권하는 정본 축자 문구를 그대로 안내한다', async () => {
    const { container } = renderCatalog();
    await settle();
    const box = container.querySelector('.crosslink');
    expect(box).not.toBeNull();
    expect(box).toHaveTextContent(
      '찾을 것이 정해져 있으면 표 헤더의 열 이름을 눌러 조건을 걸어 보세요.',
    );
  });

  it('그 릴리스에 없는 검색 화면으로 보내지 않는다 — 링크 0건 · 「AI 검색」 0건', async () => {
    const { container } = renderCatalog();
    await settle();
    const box = container.querySelector('.crosslink')!;
    expect(box.querySelectorAll('a')).toHaveLength(0);
    expect(box.textContent).not.toMatch(/AI/);
    expect(container.querySelector('a[href="/lab"]')).toBeNull();
  });
});

describe('§5 Verified 열 — 승인 처리 도착 전의 정직한 상태 (Ted 판정 2026-09-02)', () => {
  /**
   * 종전에는 승인이 오지 않은 행의 `Verified` 칸이 **비어 있었다** — 값이 없는 것인지
   * 아직 안 온 것인지 화면이 말하지 않았다. Ted 판정 = **글자를 취소선·회색·비활성 모양**으로
   * 둔다(꺼진 조작처럼). `CT-1` 완료 정의의 `[미확인]` ㈎·㈏ 가 이것으로 닫힌다.
   */
  it('승인이 오지 않은 행은 Verified 를 취소선·비활성 모양으로 그린다', async () => {
    renderCatalog();
    await settle();
    const pending = screen.getAllByTestId('verified-pending');
    expect(pending.length).toBeGreaterThan(0);
    for (const cell of pending) {
      expect(cell.textContent?.trim()).toBe('Verified');
      expect(cell.className).toContain('verified--pending');
      expect(cell).toHaveAttribute('aria-disabled', 'true');
    }
  });

  /**
   * 종전 회차가 `[미확인]` 로 남긴 자리 — 취소선을 **계산값으로** 재지 못했다.
   * 같은 설정(`test.css.include`)으로 닫는다. 규칙은 `catalog.css` `.verified--pending`.
   * ⚠ 읽는 자리는 `textDecoration` 이다 — jsdom 의 cssstyle 은 `text-decoration` 축약을
   * `textDecorationLine` 으로 펼치지 않아 그 자리는 `none` 을 준다(실측 2026-09-03).
   * 값을 만들어 맞추지 않고, **실제로 값이 서는 속성**을 읽는다.
   */
  it('취소선이 계산값으로 확인된다', async () => {
    renderCatalog();
    await settle();
    for (const cell of screen.getAllByTestId('verified-pending')) {
      const cs = getComputedStyle(cell);
      expect(cs.textDecoration).toContain('line-through');
      expect(cs.cursor).toBe('not-allowed');
    }
  });

  it('승인이 도착한 행은 평소대로다 — 취소선 표식이 붙지 않는다', async () => {
    renderCatalog();
    await settle();
    const done = screen.getAllByLabelText('Verified');
    expect(done.length).toBeGreaterThan(0);
    for (const cell of done) {
      expect(cell.className).not.toContain('verified--pending');
      expect(cell).not.toHaveAttribute('aria-disabled');
    }
  });

  it('한 행은 둘 중 하나만 그린다 — 승인 전 칸과 승인 칸이 겹치지 않는다', async () => {
    renderCatalog();
    await settle();
    for (const row of bodyRows()) {
      const w = within(row);
      const pending = w.queryAllByTestId('verified-pending').length;
      const done = w.queryAllByLabelText('Verified').length;
      expect(pending + done).toBe(1);
    }
  });
});
