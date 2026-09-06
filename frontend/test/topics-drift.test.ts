/**
 * 주제 어휘 드리프트 시험 — 프론트 사본 ↔ **선언 정본**(`db/platform/schema.sql`).
 *
 * ⭑ **왜 필요한가** — 어휘가 사는 자리가 넷이다(DB CHECK · `routes/catalog._TOPICS` ·
 *   프론트 `TOPICS` · ai-service `ports.TOPICS`). 한 곳만 넓히면 **DB 는 받는데 화면이
 *   못 고르거나** 그 반대가 되고, **둘 다 조용하다**. `〈352〉` 가 정확히 그 무늬였다.
 *
 * 종전 시험(`catalog.test.tsx`·`qd-catalog-topic-fixed4.test.tsx`)은 **`TOPICS` 를 자기 자신과
 * 대조**해서 사본이 정본과 갈려도 green 이었다. 이 시험이 그 구멍을 막는다.
 * 같은 무늬의 서버 쪽 대조 = `services/core-api/tests/test_input_error_paths.py`.
 *
 * 근거 = `PLAN-SoT §9 〈55〉`(값 집합은 DB 가 강제한다) · `〈354〉`(4값 → 6값 · 회차 19차).
 */
import { describe, expect, it } from 'vitest';
import { TOPICS } from '../src/components/upload/types';

// ⚠ **node API 를 여기서만 쓴다.** `frontend/tsconfig.json` 에 `@types/node` 가 없어 타입이 없고
//   (그래서 `@ts-expect-error`), vite 의 `?raw` 는 **뿌리 밖 파일을 막는다**(`Denied ID`) —
//   그 둘 때문에 이 모양이 됐다. ⛔ 대조를 포기하지 않는다: 사본이 정본과 갈리는 것을 잡는 것이
//   이 파일의 전부다(`〈352〉` 가 그 무늬였다).
// @ts-expect-error — 타입 선언 없이 런타임만 쓴다(vitest 는 node 위에서 돈다).
import { readFileSync } from 'node:fs';
// @ts-expect-error — 같은 이유.
import { resolve } from 'node:path';

declare const process: { cwd(): string };

/** `db/platform/schema.sql` 의 `d3_dataset_description.topic` CHECK 에 적힌 값 목록. */
function declaredTopics(): string[] {
  // vitest 의 실행 뿌리는 `frontend/` 다(`vite.config.ts` 자리).
  const schema: string = resolve(process.cwd(), '../db/platform/schema.sql');
  const line: string | undefined = readFileSync(schema, 'utf8')
    .split('\n')
    .find((l: string) => l.trim().startsWith('topic') && l.includes('CHECK'));
  if (!line) throw new Error('schema.sql 에서 topic CHECK 줄을 못 찾았다');
  return [...line.matchAll(/'([^']+)'/g)].map((m) => m[1] as string);
}

describe('주제 어휘 — 프론트 사본이 선언 정본과 갈리지 않는다 (〈55〉·〈354〉)', () => {
  it('`TOPICS` 가 `schema.sql` 의 CHECK 값과 **순서까지** 같다', () => {
    // ⛔ 기대값을 여기 다시 적지 않는다 — 세 곳에 적으면 갈라진다.
    expect([...TOPICS]).toEqual(declaredTopics());
  });

  it('`〈354〉` 가 넓힌 두 값이 실제로 들어 있다 — 회귀 표식', () => {
    expect(TOPICS).toContain('가뭄');
    expect(TOPICS).toContain('파일 포맷 예제');
  });

  it('빈 값은 목록에 없다 — **미정은 목록의 값이 아니라 선택 안 함**이다', () => {
    expect(TOPICS).not.toContain('');
  });
});
