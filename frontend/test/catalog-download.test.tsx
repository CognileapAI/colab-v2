/**
 * `ST-1` / `CT-1` — 카탈로그 행의 다운로드가 **실제로 열리는가**.
 *
 * 종전 화면은 `<a href>` 하나였고, 그 요청에는 세션 토큰이 붙지 않아 **누르면 401** 이었다.
 * 이 시험이 그 자리를 잠근다 — 누른 뒤 실제로 나가는 요청에 `Authorization` 이 붙는지,
 * 실패하면 사람이 볼 수 있게 말하는지.
 */
import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { DatasetsPage } from '../src/routes/DatasetsPage';
import { fixtureCatalogSource } from '../src/components/catalog/fixture';
import { fileNameFrom } from '../src/api/download';
import { setToken, clearToken } from '../src/auth/store';

const realFetch = globalThis.fetch;

function renderCatalog() {
  return render(
    <MemoryRouter initialEntries={['/datasets']}>
      <Routes>
        <Route path="/datasets" element={<DatasetsPage source={fixtureCatalogSource()} />} />
      </Routes>
    </MemoryRouter>,
  );
}

async function settle() {
  for (let i = 0; i < 6; i += 1) await act(async () => {});
}

beforeEach(() => {
  setToken('a1-prof-token');
  // jsdom 에는 없는 두 자리. 없으면 누르는 순간 예외가 나 시험이 이유 없이 red 가 된다.
  if (!URL.createObjectURL) {
    (URL as unknown as { createObjectURL: unknown }).createObjectURL = () => 'blob:x';
    (URL as unknown as { revokeObjectURL: unknown }).revokeObjectURL = () => undefined;
  }
});

afterEach(() => {
  globalThis.fetch = realFetch;
  clearToken();
  vi.restoreAllMocks();
});

describe('원본 내려받기', () => {
  it('다운로드를 누르면 인증된 요청이 나가고 파일이 저장된다', async () => {
    const calls: Request[] = [];
    globalThis.fetch = vi.fn(async (input: RequestInfo | URL) => {
      calls.push(input as Request);
      return new Response(new Uint8Array([1, 2, 3]), {
        status: 200,
        headers: { 'content-disposition': "attachment; filename*=UTF-8''a1-body.csv" },
      });
    }) as typeof fetch;
    const saved: string[] = [];
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (
      this: HTMLAnchorElement,
    ) {
      saved.push(this.download);
    });

    renderCatalog();
    await settle();
    const open = screen.getAllByRole('row').slice(1)[0]!;
    fireEvent.click(within(open).getByRole('link', { name: /다운로드/ }));
    await settle();

    expect(calls).toHaveLength(1);
    expect(new URL(calls[0]!.url).pathname).toMatch(/\/datasets\/.+\/download$/);
    expect(calls[0]!.headers.get('authorization')).toBe('Bearer a1-prof-token');
    expect(saved).toEqual(['a1-body.csv']);   // **파일이 실제로 저장 경로를 탔다**
  });

  it('열리지 않으면 조용히 넘어가지 않고 말한다', async () => {
    globalThis.fetch = vi.fn(
      async () => new Response('{"code":"FORBIDDEN","message":"x"}', { status: 403 }),
    ) as typeof fetch;

    renderCatalog();
    await settle();
    const open = screen.getAllByRole('row').slice(1)[0]!;
    fireEvent.click(within(open).getByRole('link', { name: /다운로드/ }));
    await settle();

    expect(screen.getByRole('alert')).toHaveTextContent('내려받지 못했어요');
  });

  it('서버가 준 이름을 그대로 쓰고, 없으면 지어내지 않는다', () => {
    expect(fileNameFrom("attachment; filename*=UTF-8''%EA%B0%80.csv", 'ds')).toBe('가.csv');
    expect(fileNameFrom('attachment; filename="b.zip"', 'ds')).toBe('b.zip');
    expect(fileNameFrom(null, 'ds')).toBe('ds');
  });
});
