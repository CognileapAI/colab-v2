/**
 * `WU-S4`(회차 `R-K3-STRUCTURE.md`) — 계보 제안 중계가 **사람이 고른 가공 단계**를
 * 질의에 싣는가.
 *
 * ⛔ **브라우저 검증 대상이 0건인 변경이다.** `.suggestions(` 호출 자리는 이 회차에도
 * 0건이고(`LineageStep.tsx:5-14` 축자 「부르는 자리가 사라졌을 뿐이다」), 제안 영역 복원은
 * 범위 밖(㉮)이다. 그러므로 화면에서 가로챌 요청이 없다 — 검증은 **여기 한 층**이다:
 * `apiLineageSource().suggestions` 가 실제로 만들어 내보내는 요청 URL 을 `fetch` 대역으로
 * 붙잡아 질의 열쇠를 읽는다. 「화면에서 확인했다」고 적지 않는다.
 *
 * 잠그는 것 둘:
 *   ⑴ 값이 있으면 `processingLevelUserSet` 이 **그대로** 실린다(문자열 `Lv0`~`Lv3`).
 *   ⑵ 안 골랐으면 **열쇠 자체가 없다** — core-api 가 그때 「가공 단계를 고르면 제안이
 *      가능합니다」의 빈 상태로 답한다(`WU-S1`). 빈 문자열을 보내면 그 구분이 무너진다
 *      (`lineageSource.ts:42` 축자 「「아직 안 골랐다」와 「빈 문자열」이 갈려야 한다」).
 *   ⑶ 계약 enum 밖 값은 **타입이 막는다** — 아래 `typeOracle` 이 `frontend-typecheck` 의
 *      판정 대상이다(`@ts-expect-error` 가 오류가 아니게 되면 그 게이트가 red 다).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { apiLineageSource } from '../src/components/lineage/lineageSource';
import type { LineageSource } from '../src/components/lineage/types';

const realFetch = globalThis.fetch;
const UPLOAD = '01JYZ9K7WQ3N8V4M2X6C5B0PR9';

const BODY = {
  degraded: false,
  scope: { labId: '01JYZ9K7WQ3N8V4M2X6C5B0PRA', labName: '수자원순환연구실', searchedCount: 0 },
  rawDataLikely: false,
  suggestions: [],
};

function captureUrls(): URL[] {
  const urls: URL[] = [];
  globalThis.fetch = vi.fn(async (input: RequestInfo | URL) => {
    urls.push(new URL((input as Request).url));
    return new Response(JSON.stringify(BODY), {
      status: 200,
      headers: { 'content-type': 'application/json' },
    });
  }) as unknown as typeof globalThis.fetch;
  return urls;
}

/**
 * 타입 오라클 — **실행하지 않는다.** 판정하는 것은 `frontend-typecheck`(`tsc --noEmit`)이고,
 * `frontend/tsconfig.json` 의 `include` 가 `test` 를 덮으므로 이 파일이 그 대상이다.
 */
export async function typeOracle(source: LineageSource): Promise<void> {
  await source.suggestions(UPLOAD, { processingLevelUserSet: 'Lv1' });
  // @ts-expect-error 계약 enum(`Lv0`~`Lv3`) 밖 값이다 — 손으로 적은 문자열이 새는 자리를 막는다.
  await source.suggestions(UPLOAD, { processingLevelUserSet: 'Lv9' });
}

beforeEach(() => {
  globalThis.fetch = realFetch;
});

afterEach(() => {
  globalThis.fetch = realFetch;
  vi.restoreAllMocks();
});

describe('계보 제안 질의 — 사람이 고른 가공 단계', () => {
  it('고른 값이 있으면 processingLevelUserSet 이 그대로 실린다', async () => {
    const urls = captureUrls();
    await apiLineageSource().suggestions(UPLOAD, {
      datasetNameDraft: '한강 유량 2023',
      processingLevelUserSet: 'Lv1',
    });
    expect(urls).toHaveLength(1);
    expect(urls[0]?.searchParams.get('processingLevelUserSet')).toBe('Lv1');
    expect(urls[0]?.searchParams.get('datasetNameDraft')).toBe('한강 유량 2023');
  });

  it('안 골랐으면 열쇠 자체를 보내지 않는다', async () => {
    const urls = captureUrls();
    await apiLineageSource().suggestions(UPLOAD, { subject: '수자원' });
    expect(urls).toHaveLength(1);
    expect(urls[0]?.searchParams.has('processingLevelUserSet')).toBe(false);
    expect(urls[0]?.searchParams.get('subject')).toBe('수자원');
  });

  it('Lv0 도 고른 값이다 — 거짓값이라고 빠지지 않는다', async () => {
    const urls = captureUrls();
    await apiLineageSource().suggestions(UPLOAD, { processingLevelUserSet: 'Lv0' });
    expect(urls[0]?.searchParams.get('processingLevelUserSet')).toBe('Lv0');
  });

  it('타입 오라클은 typecheck 가 판정한다', () => {
    expect(typeof typeOracle).toBe('function');
  });
});
