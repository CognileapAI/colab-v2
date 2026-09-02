// P8 — E-01 화면별 적용 지점 표가 **실물과 갈리지 않는가**.
//
// 이 시험은 표를 만들지 않는다. `dev-package/sessions/P8-E01-APPLY-POINTS-DRAFT.md`
// 초안이 적은 축 A(권한 스위치) 적용 지점이 `frontend/src` 의 `PermissionGate` 실물과
// **집합으로 같은가**만 본다. 문서가 실물보다 낡는 것이 이 레포의 대표 사고이고
// (`CLAUDE.md §0`), 표는 다 그린 화면에서 유도한 것이라 화면이 늘면 표가 조용히 낡는다.
//
// ⚠ 판정 대상은 **축 A 뿐이다.** 데이터 잠김(축 B)은 `LockedContent` 가 맡고
// 값의 정본은 E-06 적용 지점 표다(`Policy_역할과_권한 §4`). 두 축을 한 판정으로
// 합치지 않는다 (P-14).
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';
import { describe, expect, it } from 'vitest';

const REPO = join(__dirname, '..', '..');
const SRC = join(REPO, 'frontend', 'src');
const DRAFT = join(REPO, 'dev-package', 'sessions', 'P8-E01-APPLY-POINTS-DRAFT.md');

/** `frontend/src` 전체를 훑어 `<PermissionGate requires="X">` 를 `파일:스위치` 로 모은다. */
function scanSites(): Set<string> {
  const found = new Set<string>();
  const walk = (dir: string) => {
    for (const name of readdirSync(dir)) {
      const p = join(dir, name);
      if (statSync(p).isDirectory()) { walk(p); continue; }
      if (!/\.tsx?$/.test(p)) continue;
      const text = readFileSync(p, 'utf8');
      for (const m of text.matchAll(/<PermissionGate\s+requires="([^"]+)"/g)) {
        found.add(`${relative(REPO, p).replace(/\\/g, '/')}|${m[1]}`);
      }
    }
  };
  walk(SRC);
  return found;
}

/**
 * 초안 **§1.1 절만** 읽는다 — 그 절이 `PermissionGate` 자리를 적는 유일한 표다.
 * §1.2(서버 판정)·§1.3(할 일 함 그룹)은 다른 메커니즘이라 같은 집합에 섞지 않는다.
 */
function tableSites(): Set<string> {
  const md = readFileSync(DRAFT, 'utf8');
  const section = md.split('### 1.1')[1]?.split('### 1.2')[0];
  if (!section) throw new Error('초안에 `### 1.1` 절이 없다 — 표의 자리가 바뀌었다.');
  const rows = section.split('\n').filter((l) => l.startsWith('|') && l.includes('frontend/src/'));
  const found = new Set<string>();
  for (const row of rows) {
    const path = row.match(/(frontend\/src\/[^\s`:|]+)/)?.[1];
    // 스위치 이름은 `보이는 조건` 칸과 `출처` 칸에 두 번 적힌다. **둘이 갈리면 red** —
    // 한쪽만 고친 편집이 표를 조용히 반쪽 낡게 만든다.
    const names = [...row.matchAll(/`(업로드·편집|프로젝트 생성|승인 위임|연구실 설정)`/g)].map((m) => m[1]);
    const uniq = [...new Set(names)];
    if (uniq.length > 1) throw new Error(`한 행이 스위치 둘을 적는다: ${uniq.join(' / ')}`);
    if (path && uniq[0]) found.add(`${path}|${uniq[0]}`);
  }
  return found;
}

describe('E-01 적용 지점 표 ↔ 실물', () => {
  it('초안이 적은 축 A 적용 지점과 PermissionGate 실물이 집합으로 같다', () => {
    const real = [...scanSites()].sort();
    const doc = [...tableSites()].sort();
    expect(doc).toEqual(real);
  });

  it('권한 스위치는 정확히 네 개다 — 표에 다섯 번째가 들어오지 않는다 (P-3)', () => {
    const switches = new Set([...scanSites()].map((s) => s.split('|')[1]));
    for (const s of switches) {
      expect(['업로드·편집', '프로젝트 생성', '승인 위임', '연구실 설정']).toContain(s);
    }
  });
});
