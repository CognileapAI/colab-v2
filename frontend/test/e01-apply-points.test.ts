// P8 — E-01 화면별 적용 지점 표가 **실물과 갈리지 않는가**.
//
// 이 시험은 표를 만들지 않는다. `contracts/ui/e01-permission-gates.json`이 적은
// 축 A(권한 스위치) 적용 지점이 `frontend/src` 의 `PermissionGate` 실물과
// **집합으로 같은가**만 본다. 문서가 실물보다 낡는 것이 이 레포의 대표 사고이고
// (`CLAUDE.md §0`), 표는 다 그린 화면에서 유도한 것이라 화면이 늘면 표가 조용히 낡는다.
//
// ⚠ 판정 대상은 **축 A 뿐이다.** 데이터 잠김(축 B)은 `LockedContent` 가 맡고
// 값의 정본은 E-06 적용 지점 표다(`Policy_역할과_권한 §4`). 두 축을 한 판정으로
// 합치지 않는다 (P-14).
//
// ⚠ **Node API 를 쓰지 않는다.** 이 시험은 `frontend/tsconfig.json` 의 빌드 대상이고
// 그 tsconfig 는 `types` 에 `node` 를 두지 않는다(브라우저 산출물이므로 둘 이유가 없다).
// `node:fs`/`__dirname` 을 쓰면 `tsc --noEmit` 이 깨지고 **이미지 빌드가 깨진다** —
// 실제로 2026-09-02 에 그렇게 `main` 이 배포 불가가 됐다. 소스 전수는
// `import.meta.glob`으로 받고 기대 집합은 코드 인접 JSON 계약에서 읽는다.
import { describe, expect, it } from 'vitest';
import permissionContract from '../../contracts/ui/e01-permission-gates.json';

/** `frontend/src` 전수 — 빌드 도구가 읽어 준다. 대상 0건이면 red 다 (green-by-skip 금지). */
const sources = import.meta.glob('../src/**/*.{ts,tsx}', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

/** `frontend/src` 전체를 훑어 `<PermissionGate requires="X">` 를 `파일|스위치` 로 모은다. */
function scanSites(): Set<string> {
  const found = new Set<string>();
  for (const [key, text] of Object.entries(sources)) {
    // glob 키는 `../src/...` — 레포 기준 경로(`frontend/src/...`)로 옮긴다.
    const path = key.replace(/^\.\.\//, 'frontend/');
    for (const m of text.matchAll(/<PermissionGate\s+requires="([^"]+)"/g)) {
      found.add(`${path}|${m[1]}`);
    }
  }
  return found;
}

function contractSites(): Set<string> {
  return new Set(permissionContract.sites.map((site) => `${site.path}|${site.requires}`));
}

describe('E-01 적용 지점 표 ↔ 실물', () => {
  it('초안이 적은 축 A 적용 지점과 PermissionGate 실물이 집합으로 같다', () => {
    // 판정 재료가 0건이면 두 집합이 「둘 다 비어서」 같아진다 — 그건 통과가 아니다.
    expect(Object.keys(sources).length).toBeGreaterThan(0);
    const real = [...scanSites()].sort();
    expect(real.length).toBeGreaterThan(0);
    const contract = [...contractSites()].sort();
    expect(contract.length).toBeGreaterThan(0);
    expect(contract).toEqual(real);
  });

  it('권한 스위치는 정확히 네 개다 — 표에 다섯 번째가 들어오지 않는다 (P-3)', () => {
    const switches = new Set([...scanSites()].map((s) => s.split('|')[1]));
    expect(switches.size).toBeGreaterThan(0);
    expect(permissionContract.switches).toEqual([
      '업로드·편집', '프로젝트 생성', '승인 위임', '연구실 설정',
    ]);
    for (const s of switches) expect(permissionContract.switches).toContain(s);
  });
});
