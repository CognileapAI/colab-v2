/**
 * S-05 상세 — **묘비를 자기 연구실에서만 구분한다** (계약 동결 해제 17차 · Ted 판정 ② 2026-09-03).
 *
 * 오라클 —
 *   · `Policy_데이터셋_상세.md` §9 「지워진 데이터의 주소로 직접 들어옴」 행 축자 문구
 *   · `Policy_공통_기반.md` §2.4 「없는 주소」 중립 문구 (`〈296〉`-㉰)
 *   · `fe-core.yaml` `getDataset` — 410 `Gone` / 404 `NotFound`
 *
 * **넷을 한 벌로 잰다.** 410 하나만 시험하면 「누설이 늘지 않았다」가 증명되지 않는다.
 * 화면 글자는 정본에서 그대로 온다 — 여기서 새 한국어 라벨을 만들지 않는다.
 */
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { apiDetailSource } from '../src/components/detail/detailSource';
import { DatasetGone, DatasetTombstone } from '../src/components/detail/types';
import type { DetailSource } from '../src/components/detail/types';

/** `Policy_데이터셋_상세 §9` 축자. 한 글자도 바꾸지 않는다. */
const 묘비 = '이 데이터는 지워졌어요. 계보 기록은 관련 데이터의 상세에서 볼 수 있어요.';
/** `Policy_공통_기반 §2.4` 축자. */
const 중립 = '이 주소에는 화면이 없어요.';

const ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA1';
const realFetch = globalThis.fetch;

afterEach(() => {
  globalThis.fetch = realFetch;
  vi.restoreAllMocks();
});

function renderDetail(source: DetailSource) {
  return render(
    <MemoryRouter initialEntries={[`/datasets/${ID}`]}>
      <Routes>
        <Route path="/datasets/:datasetId" element={<DatasetDetailPage source={source} />} />
      </Routes>
    </MemoryRouter>,
  );
}

function throwing(e: Error): DetailSource {
  return {
    get: async () => {
      throw e;
    },
  };
}

// ── 계약 응답 → 화면 상태의 번역 ─────────────────────────────────────────────
describe('detailSource — 응답 코드를 상태로 옮긴다', () => {
  function stub(status: number) {
    globalThis.fetch = vi.fn(
      async () =>
        new Response(status === 200 ? '{}' : '{"code":"X","message":"m"}', {
          status,
          headers: { 'content-type': 'application/json' },
        }),
    ) as typeof fetch;
    return apiDetailSource();
  }

  it('410 은 묘비다 — 자기 연구실에서 지워진 것이다', async () => {
    await expect(stub(410).get(ID)).rejects.toBeInstanceOf(DatasetTombstone);
  });

  it('404 는 묘비가 아니다 — 셋(남의 묘비·남의 생존·없는 id)이 접힌 자리다', async () => {
    await expect(stub(404).get(ID)).rejects.toBeInstanceOf(DatasetGone);
  });

  it('묘비는 404 의 하위 종류가 아니다 — 둘을 섞으면 화면이 갈리지 못한다', async () => {
    await expect(stub(404).get(ID)).rejects.not.toBeInstanceOf(DatasetTombstone);
  });
});

// ── 화면 문구 ────────────────────────────────────────────────────────────────
describe('§9 · 묘비 문구는 410 에서만 나온다', () => {
  it('⑴ 자기 연구실 묘비(410) — 정본 §9 문구를 축자로 낸다', async () => {
    renderDetail(throwing(new DatasetTombstone()));
    const box = await screen.findByTestId('detail-tombstone');
    expect(box.textContent).toContain(묘비);
    expect(box.textContent).not.toContain(중립);
  });

  it('⑵⑶⑷ 404 — 중립 문구 그대로다 (남의 연구실 묘비·생존·없는 id)', async () => {
    renderDetail(throwing(new DatasetGone()));
    const box = await screen.findByTestId('detail-gone');
    expect(box.textContent).toContain(중립);
    expect(box.textContent).not.toContain('지워졌어요');
    expect(screen.queryByTestId('detail-tombstone')).toBeNull();
  });

  it('묘비 자리에는 중립 문구가 없고 그 반대도 같다 — 두 자리는 겹치지 않는다', async () => {
    renderDetail(throwing(new DatasetTombstone()));
    await screen.findByTestId('detail-tombstone');
    expect(screen.queryByTestId('detail-gone')).toBeNull();
  });

  it('묘비도 목록으로 되돌아가는 길을 준다 (§9 복구 방법 「목록으로 보낸다」)', async () => {
    renderDetail(throwing(new DatasetTombstone()));
    const box = await screen.findByTestId('detail-tombstone');
    expect(box.querySelector('a[href="/datasets"]')).not.toBeNull();
  });
});
