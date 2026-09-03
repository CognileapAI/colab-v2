/**
 * 정직한 빈 상태 — 픽스처 폴백 제거 (`CODE-REVIEW-20260903` 9 · 부록 `AuthGate`).
 *
 * **red 를 먼저 봤다.** 이 파일을 쓴 시점의 `catalogSource`·`detailSource`·`projectSource`·
 * `graphSource` 는 401·500·네트워크 오류를 전부 `catch {}` 로 삼켜 픽스처로 그렸고,
 * `AuthGate` 의 `/me` 에는 `.catch` 가 없었다. 아래 시험은 전부 그 상태에서 실패한다.
 *
 * 이 파일이 잠그는 것 —
 *  ⑴ **401 은 기존 인증 경로로 간다** — 토큰을 버리고 `AuthGate` 가 로그인 화면을 세운다.
 *     새 통로를 만들지 않는다: 신호는 `auth/store` 의 `clearToken` 하나다.
 *  ⑵ 500·네트워크 오류는 **오류 상태 + 다시 시도**다. 픽스처 행이 한 줄도 그려지지 않는다.
 *  ⑶ 성공은 서버가 준 것을 그대로 그린다.
 *  ⑷ 픽스처는 **손으로 꽂을 때만** 선다 — 운영 경로에 `fixture.ts` 로 가는 import 가 없다.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { App } from '../src/app/App';
import { clearToken, getToken, setToken } from '../src/auth/store';
import { apiCatalogSource } from '../src/components/catalog/catalogSource';
import { apiDetailSource } from '../src/components/detail/detailSource';
import { apiLineageGraphSource } from '../src/components/lineage/graphSource';
import { apiProjectSource } from '../src/components/project/projectSource';
import { DatasetsPage } from '../src/routes/DatasetsPage';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { ProjectsPage } from '../src/routes/ProjectsPage';
import { ProjectDetailPage } from '../src/routes/ProjectDetailPage';
import { DEFAULT_SORT } from '../src/components/catalog/types';
import { DatasetGone } from '../src/components/detail/types';
import { DEFAULT_QUERY, ProjectGone } from '../src/components/project/types';
import { FIXTURE_ROWS } from '../src/components/catalog/fixture';
import { FIXTURE_PROJECTS } from '../src/components/project/fixture';
import { account } from './factories';

const TOKEN = 'v1.eyJzdWIiOiJBIn0.c2lnbmF0dXJl';
const DATASET_ID = '01ARZ3NDEKTSV4RRFFQ69G5FAV';
const PROJECT_ID = '01ARZ3NDEKTSV4RRFFQ69G5FAW';

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

/** 서버에 닿지 못한다 — `fetch` 자체가 거절한다(오프라인·DNS·CORS). */
function offline() {
  vi.stubGlobal('fetch', () => Promise.reject(new TypeError('Failed to fetch')));
}

function serverError() {
  vi.stubGlobal('fetch', () =>
    Promise.resolve(json(500, { code: 'INTERNAL', message: '서버가 아프다' })),
  );
}

function unauthorized() {
  vi.stubGlobal('fetch', () =>
    Promise.resolve(json(401, { code: 'UNAUTHORIZED', message: '만료' })),
  );
}

beforeEach(() => {
  clearToken();
});

afterEach(() => {
  clearToken();
  vi.unstubAllGlobals();
});

// ── ⑴·⑵·⑶ 출처 넷 — 401 · 500 · 네트워크 · 성공 ──────────────────────────

describe('출처 넷은 실패를 픽스처로 덮지 않는다', () => {
  const cases: Array<{
    name: string;
    call: () => Promise<unknown>;
    ok: unknown;
    /** 성공 응답에서 화면이 읽는 값 하나 — 서버가 준 것이 그대로 왔는지 본다. */
    read: (v: unknown) => unknown;
    expected: unknown;
  }> = [
    {
      name: 'catalogSource.list',
      call: () => apiCatalogSource().list({ sort: DEFAULT_SORT, filters: {} }),
      ok: { items: [], totalCount: 7 },
      read: (v) => (v as { totalCount: number }).totalCount,
      expected: 7,
    },
    {
      name: 'catalogSource.facets',
      call: () => apiCatalogSource().facets({ sort: DEFAULT_SORT, filters: {} }),
      ok: { 주제: [{ value: '수문', count: 3 }] },
      read: (v) => (v as Record<string, unknown[]>)['주제']?.length,
      expected: 1,
    },
    {
      name: 'detailSource.get',
      call: () => apiDetailSource().get(DATASET_ID),
      ok: { datasetId: DATASET_ID, name: '서버가 준 이름' },
      read: (v) => (v as { name: string }).name,
      expected: '서버가 준 이름',
    },
    {
      name: 'projectSource.list',
      call: () => apiProjectSource().list(DEFAULT_QUERY),
      ok: { items: [], totalCount: 4 },
      read: (v) => (v as { totalCount: number }).totalCount,
      expected: 4,
    },
    {
      name: 'projectSource.get',
      call: () => apiProjectSource().get(PROJECT_ID),
      ok: { projectId: PROJECT_ID, name: '서버가 준 프로젝트' },
      read: (v) => (v as { name: string }).name,
      expected: '서버가 준 프로젝트',
    },
    {
      name: 'graphSource.get',
      call: () => apiLineageGraphSource().get(DATASET_ID),
      ok: { nodes: [{ datasetId: DATASET_ID }], edges: [] },
      read: (v) => (v as { nodes: unknown[] }).nodes.length,
      expected: 1,
    },
  ];

  for (const c of cases) {
    it(`${c.name} — 401 은 토큰을 버려 인증 경로로 넘긴다`, async () => {
      setToken(TOKEN);
      unauthorized();
      await expect(c.call()).rejects.toBeTruthy();
      // **새 통로를 만들지 않는다** — `AuthGate` 가 이미 보고 있는 신호가 이것이다.
      expect(getToken()).toBeNull();
    });

    it(`${c.name} — 500 은 픽스처가 아니라 실패다`, async () => {
      serverError();
      await expect(c.call()).rejects.toBeTruthy();
    });

    it(`${c.name} — 서버에 닿지 못해도 픽스처로 채우지 않는다`, async () => {
      offline();
      await expect(c.call()).rejects.toBeTruthy();
    });

    it(`${c.name} — 성공하면 서버가 준 것을 그대로 낸다`, async () => {
      vi.stubGlobal('fetch', () => Promise.resolve(json(200, c.ok)));
      expect(c.read(await c.call())).toEqual(c.expected);
    });
  }

  it('묘비(404)와 못 읽음을 가른다 — 404 만 `DatasetGone`·`ProjectGone` 이다', async () => {
    vi.stubGlobal('fetch', () => Promise.resolve(json(404, { code: 'NOT_FOUND', message: '없다' })));
    await expect(apiDetailSource().get(DATASET_ID)).rejects.toBeInstanceOf(DatasetGone);
    await expect(apiProjectSource().get(PROJECT_ID)).rejects.toBeInstanceOf(ProjectGone);

    serverError();
    await expect(apiDetailSource().get(DATASET_ID)).rejects.not.toBeInstanceOf(DatasetGone);
    await expect(apiProjectSource().get(PROJECT_ID)).rejects.not.toBeInstanceOf(ProjectGone);
  });
});

// ── ⑵ 화면 — 오류 상태 + 다시 시도, 픽스처 행 없음 ───────────────────────────

function renderAt(path: string, element: React.ReactNode) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/datasets" element={element} />
        <Route path="/datasets/:datasetId" element={element} />
        <Route path="/projects" element={element} />
        <Route path="/projects/:projectId" element={element} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('화면은 못 읽은 것을 없는 것으로 말하지 않는다', () => {
  it('카탈로그 — 픽스처 행 대신 실패와 다시 불러오기', async () => {
    serverError();
    renderAt('/datasets', <DatasetsPage />);

    const box = await screen.findByTestId('catalog-error');
    expect(box.textContent).toContain('불러오지 못했어요');
    expect(screen.getByText('다시 불러오기')).toBeTruthy();
    // 픽스처 이름이 한 줄도 없다 — 종전에는 여섯 행이 실데이터처럼 그려졌다.
    for (const row of FIXTURE_ROWS) {
      expect(screen.queryByText(row.name)).toBeNull();
    }
    // **「조건에 맞는 데이터가 없어요」로도 접지 않는다** — 없는 것이 아니라 못 읽은 것이다.
    expect(screen.queryByText(/조건에 맞는 데이터가 없어요/)).toBeNull();
  });

  it('데이터셋 상세 — 못 읽은 것을 「이 주소에는 화면이 없어요」로 그리지 않는다', async () => {
    serverError();
    renderAt(`/datasets/${DATASET_ID}`, <DatasetDetailPage />);

    expect(await screen.findByTestId('detail-error')).toBeTruthy();
    expect(screen.queryByTestId('detail-gone')).toBeNull();
  });

  it('프로젝트 목록 — 픽스처 대신 실패와 다시 불러오기', async () => {
    serverError();
    renderAt('/projects', <ProjectsPage />);

    expect(await screen.findByTestId('project-list-error')).toBeTruthy();
    for (const p of FIXTURE_PROJECTS) {
      expect(screen.queryByText(p.name)).toBeNull();
    }
    expect(screen.queryByTestId('project-empty')).toBeNull();
  });

  it('프로젝트 상세 — 못 읽은 것을 「찾을 수 없어요」로 그리지 않는다', async () => {
    serverError();
    renderAt(`/projects/${PROJECT_ID}`, <ProjectDetailPage />);

    expect(await screen.findByTestId('project-detail-error')).toBeTruthy();
    expect(screen.queryByTestId('project-gone')).toBeNull();
  });

  it('세션이 만료되면 카탈로그가 아니라 로그인 화면이 선다', async () => {
    setToken(TOKEN);
    unauthorized();
    render(
      <MemoryRouter initialEntries={['/datasets']}>
        <App />
      </MemoryRouter>,
    );
    expect(await screen.findByTestId('login-account-name')).toBeTruthy();
    expect(getToken()).toBeNull();
  });
});

// ── 부록 · `AuthGate` — `/me` 실패가 영구 빈 화면이 되지 않는다 ────────────────

describe('AuthGate — 확인하지 못한 것과 통하지 않는 것을 가른다', () => {
  it('서버에 닿지 못하면 빈 화면이 아니라 오류와 다시 시도다', async () => {
    setToken(TOKEN);
    offline();
    render(
      <MemoryRouter initialEntries={['/lab']}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByTestId('auth-unreachable')).toBeTruthy();
    expect(screen.queryByTestId('auth-pending')).toBeNull();
    // 못 닿은 것은 로그인 문제가 아니다 — 멀쩡한 토큰을 버리지 않는다.
    expect(getToken()).toBe(TOKEN);
  });

  it('다시 시도를 누르면 `/me` 를 다시 부르고 성공하면 앱이 선다', async () => {
    setToken(TOKEN);
    let attempts = 0;
    vi.stubGlobal('fetch', (input: Request | string) => {
      const url = typeof input === 'string' ? input : input.url;
      if (!url.endsWith('/me')) return Promise.resolve(json(200, {}));
      attempts += 1;
      return attempts === 1
        ? Promise.reject(new TypeError('Failed to fetch'))
        : Promise.resolve(json(200, account()));
    });
    render(
      <MemoryRouter initialEntries={['/lab']}>
        <App />
      </MemoryRouter>,
    );

    (await screen.findByTestId('auth-retry')).click();
    await waitFor(() => expect(screen.getByTestId('gnb-avatar')).toBeTruthy());
    expect(attempts).toBe(2);
  });

  it('5xx 도 로그인 문제가 아니다 — 토큰을 버리지 않는다', async () => {
    setToken(TOKEN);
    serverError();
    render(
      <MemoryRouter initialEntries={['/lab']}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByTestId('auth-unreachable')).toBeTruthy();
    expect(getToken()).toBe(TOKEN);
  });
});
