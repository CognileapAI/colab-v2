/**
 * 휴대폰·패드 대응 20260926 L4 — 게이트 조건 i · 정본 ⑨ · spec 틀 행을 잠근다.
 *
 * 오라클 = `dev-package/prd/specs/S-DEVICE-WIDTH-INPUT-20260926.md` V1 · V10(게이트) · V13 · 부록 H · 우려 11ⓐ ·
 * 「구현 결정 · 정본 문서」 · 「디자인 검사 판정 스크립트의 조건 i」 · 「시험 결정 · green-by-skip 방지」 · 「승인 요청」 템플릿 ⓐ.
 * ⑴ 공용 상수(`scripts/design-families.mjs`) — 폭 4단계 · 허용 폭 값 · 허용 입력 조건.
 * ⑵ 면제 목록(`gates/fixtures/frontend-design-lint/media-exempt.txt`) — 부록 H 16줄 · 24건과 같다(길이 먼저).
 * ⑶ 저장소 트리 계수 — 판정부를 저장소 CSS 전부에 돌려 `media_rules` · `hover_rules` · `container_rules` · 면제 적중을 고정한다.
 *    `media_rules` 는 L4 시작 트리(`909fe89e` · L3b 뒤)에서 센 값이다(spec 작성 때의 61 이 아니다 — 감싸기 33 · 터치 블록이 더해졌다).
 * ⑷ 정본 `docs/design-system.md` — ⑨ 자리 · 소제목 · 낮은 높이 · 넓은 표 · 폭 표 = 상수 · 지도 경계 = 코드 상수 · ⑤ 네 줄 · ⑥ i 행.
 * ⑸ spec 틀(`.agents/skills/to-spec/SKILL.md`) i 행 · 디자인 검수 절차 토큰 행 a~i · selftest 사례 수 = README 사례 수.
 * 환경 의존: ⑶ 은 `node` 와 `git` 을 부른다. 없으면 종료코드 단언이 red 로 드러난다(건너뛰지 않는다).
 */
// @ts-expect-error — 타입 선언 없이 런타임만 쓴다(vitest 는 node 위에서 돈다 · 선례 device-width-input-20260926-L0a).
import { spawnSync } from 'node:child_process';
// @ts-expect-error — 같은 이유.
import { readFileSync } from 'node:fs';
// @ts-expect-error — 같은 이유.
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { MAP_CELL_BOUNDARY } from '../src/components/preview/useMapCellWidth';

declare const process: { cwd(): string; execPath: string };

const FE = process.cwd();
const REPO = resolve(FE, '..');
const raw = (rel: string): string => String(readFileSync(resolve(REPO, rel), 'utf8'));

type Step = { name: string; min: number | null; max: number | null };
// 공용 상수 모듈은 타입 선언이 없는 .mjs 다 — 경로를 변수로 넘겨 런타임에만 읽는다(타입 = any).
const familiesPath = resolve(FE, 'scripts/design-families.mjs');
const fam = (await import(/* @vite-ignore */ familiesPath)) as {
  WIDTH_STEPS?: Step[]; WIDTH_MAX?: number[]; WIDTH_MIN?: number[]; INPUT_ALLOWED?: string[];
};

// ── ⑴ 공용 상수 ────────────────────────────────────────────────────────────
describe('⑴ 공용 상수 — 폭 4단계 · 허용 폭 값 · 허용 입력 조건', () => {
  it('폭 4단계 = ≤640 휴대폰 · 641–900 패드 세로 · 901–1180 패드 가로 · ≥1181 PC', () => {
    expect(fam.WIDTH_STEPS?.length).toBe(4);
    expect(fam.WIDTH_STEPS).toEqual([
      { name: '휴대폰', min: null, max: 640 },
      { name: '패드 세로', min: 641, max: 900 },
      { name: '패드 가로', min: 901, max: 1180 },
      { name: 'PC', min: 1181, max: null },
    ]);
  });
  it('허용 폭 값 = max-width 640 · 900 · 1180 · min-width 641 · 901 · 1181(단계 경계에서 만든다)', () => {
    expect(fam.WIDTH_MAX).toEqual([640, 900, 1180]);
    expect(fam.WIDTH_MIN).toEqual([641, 901, 1181]);
    const steps = fam.WIDTH_STEPS ?? [];
    expect(fam.WIDTH_MAX).toEqual(steps.map((s) => s.max).filter((v): v is number => v != null));
    expect(fam.WIDTH_MIN).toEqual(steps.map((s) => s.min).filter((v): v is number => v != null));
  });
  it('허용 입력 조건 = 두 표기만(우려 11ⓐ)', () => {
    expect(fam.INPUT_ALLOWED).toEqual(['(pointer: coarse)', '(hover: hover)']);
  });
});

// ── ⑵ 면제 목록 ────────────────────────────────────────────────────────────
// 부록 H 표(파일 · 조건 · 개수) — 줄 번호는 목록에 적지 않는다.
const APPENDIX_H: Array<[string, string, number]> = [
  ['src/auth/login.css', '@media (min-width: 1024px)', 1],
  ['src/auth/login.css', '@media (min-width: 1536px)', 1],
  ['src/components/approval/approval.css', '@media (min-width: 861px)', 1],
  ['src/components/detail/detail.css', '@media (max-width: 860px)', 3],
  ['src/components/detail/detail.css', '@media (max-width: 720px)', 1],
  ['src/components/lineage/lineageGraph.css', '@media (max-width: 520px)', 1],
  ['src/components/upload/upload.css', '@media (max-width: 1023px)', 2],
  ['src/components/upload/upload.css', '@media (max-width: 720px)', 6],
  ['src/components/upload/upload.css', '@media (max-width: 1100px)', 1],
  ['src/components/upload/upload.css', '@media (max-width: 760px)', 1],
  ['src/components/upload/upload.css', '@media (max-width: 600px)', 1],
  ['src/shell/primitives.css', '@media (max-width: 1100px)', 1],
  ['src/shell/shell.css', '@media (max-width: 1000px)', 1],
  ['src/shell/shell.css', '@media (max-width: 880px)', 1],
  ['src/shell/shell.css', '@media (max-width: 740px)', 1],
  ['src/shell/shell.css', '@media (max-width: 560px)', 1],
];
const LIST_PATH = 'gates/fixtures/frontend-design-lint/media-exempt.txt';
const listRows = (): string[][] => raw(LIST_PATH).split('\n').map((l) => l.trim())
  .filter((l) => l && !l.startsWith('#')).map((l) => l.split('·').map((p) => p.trim()));

describe('⑵ 면제 목록 — 부록 H 16줄 · 24건(이동 예정 23 ＋ 영구 예외 1)', () => {
  it('부록 H 표 길이 = 16줄 · 합 24', () => {
    expect(APPENDIX_H.length).toBe(16);
    expect(APPENDIX_H.reduce((n, r) => n + r[2], 0)).toBe(24);
  });
  it('목록 줄 = 부록 H(파일 · 조건 · 개수)와 같다', () => {
    const rows = listRows();
    expect(rows.length).toBe(16);
    expect(rows.map((r) => [r[0], r[1], Number(r[2])])).toEqual(APPENDIX_H);
  });
  it('모든 줄에 사유가 있고 1536 만 영구 예외 · 나머지 23건은 다음 intent 로 옮긴다', () => {
    const rows = listRows();
    const reason = (r: string[]): string => r.slice(3).join(' · ');
    expect(rows.every((r) => reason(r).length > 0)).toBe(true);
    const permanent = rows.filter((r) => reason(r).includes('영구 예외'));
    expect(permanent.map((r) => r[1])).toEqual(['@media (min-width: 1536px)']);
    const moving = rows.filter((r) => !reason(r).includes('영구 예외'));
    expect(moving.reduce((n, r) => n + Number(r[2]), 0)).toBe(23);
    expect(moving.every((r) => reason(r).includes('다음 intent'))).toBe(true);
  });
});

// ── ⑶ 저장소 트리 계수 ─────────────────────────────────────────────────────
function runRepoLint(): { rc: number | null; out: string; counts: Record<string, string> } {
  const ls = spawnSync('git', ['ls-files', '--cached', '--others', '--exclude-standard', '--', ':(glob)src/**/*.css'],
    { cwd: FE, encoding: 'utf8' });
  expect(ls.status).toBe(0);
  const files = String(ls.stdout).split('\n').filter(Boolean).sort();
  expect(files.length).toBeGreaterThan(0);
  const fx = resolve(REPO, 'gates/fixtures/frontend-design-lint');
  const run = spawnSync(process.execPath, [
    'scripts/design-lint.mjs', '--root', '.',
    '--same-in-dark', resolve(fx, 'same-in-dark.txt'),
    '--primitives', resolve(fx, 'primitives.txt'),
    '--primitives-exempt', resolve(fx, 'primitives-exempt.txt'),
    '--media-exempt', resolve(fx, 'media-exempt.txt'),
    '--', ...files,
  ], { cwd: FE, encoding: 'utf8' });
  const out = String(run.stdout) + String(run.stderr);
  const line = out.split('\n').find((l) => l.startsWith('design-lint-counts ')) ?? '';
  const counts = Object.fromEntries(line.split(' ').slice(1).map((kv) => kv.split('=') as [string, string]));
  return { rc: run.status, out, counts };
}

describe('⑶ 저장소 트리 — 조건 i 계수 고정(L4 시작 트리)', () => {
  const r = runRepoLint();
  it('판정부 종료 0 · 계수 줄 존재', () => {
    expect(r.out).toContain('design-lint-counts ');
    expect(r.rc, r.out).toBe(0);
  });
  it('media_rules=105 · hover_rules=33 · container_rules=0(대상 0건이 아니다)', () => {
    expect(r.counts['media_rules']).toBe('105');
    expect(r.counts['hover_rules']).toBe('33');
    expect(r.counts['container_rules']).toBe('0');
    expect(r.out).toContain('media_rules=105 container_rules=0 hover_rules=33');
  });
  it('i=0 · 면제 16줄이 비허용 폭 머리 24개에 걸린다 · hover 조건 밖 0', () => {
    expect(r.counts['i']).toBe('0');
    expect(r.counts['i_media']).toBe('0');
    expect(r.counts['i_form']).toBe('0');
    expect(r.counts['i_container']).toBe('0');
    expect(r.counts['i_hover']).toBe('0');
    expect(r.counts['i_holes']).toBe('0');
    expect(r.counts['i_exempt']).toBe('16');
    expect(r.counts['i_exempted_hits']).toBe('24');
    expect(r.out).toContain('폭·입력 조건 밖 0(면제 16)');
  });
});

// ── ⑷ 정본 문서 ────────────────────────────────────────────────────────────
const DOC = raw('docs/design-system.md');
const section = (head: string): string => {
  const from = DOC.indexOf(`\n## ${head}`);
  expect(from, `절 부재: ${head}`).toBeGreaterThanOrEqual(0);
  const to = DOC.indexOf('\n## ', from + 1);
  return DOC.slice(from, to < 0 ? undefined : to);
};
const sub = (sec: string, head: string): string => {
  const from = sec.indexOf(`\n### ${head}`);
  expect(from, `소제목 부재: ${head}`).toBeGreaterThanOrEqual(0);
  const to = sec.indexOf('\n### ', from + 1);
  return sec.slice(from, to < 0 ? undefined : to);
};
const NINE_SUBS = ['폭 4단계', '판단 기준', '터치 기기 규칙', '낮은 높이 규칙', '넓은 표 원칙', '지도 · 그림 위 도구 원칙', '허용 폭 값 · 면제 목록'];

describe('⑷ 정본 ⑨ 폭 단계 · 입력 방식(V1)', () => {
  it('⑨ 가 ⑧ 뒤에 있다 · ①–⑧ 제목 앵커는 그대로다', () => {
    const at8 = DOC.indexOf('\n## ⑧ 도구');
    const at9 = DOC.indexOf('\n## ⑨ 폭 단계 · 입력 방식');
    expect(at8).toBeGreaterThanOrEqual(0);
    expect(at9).toBeGreaterThan(at8);
    for (const h of ['① 층', '② 토큰', '③ 프리미티브', '④ 패턴', '⑤ 새 화면을 만들 때', '⑥ 게이트', '⑦ 판정 대기 목록']) {
      expect(DOC.indexOf(`\n## ${h}`), h).toBeGreaterThanOrEqual(0);
    }
  });
  it('⑨ 소제목 = intent (a) 여섯 항목 ＋ 허용 폭 값(순서대로 7개)', () => {
    const heads = section('⑨').split('\n').filter((l) => l.startsWith('### ')).map((l) => l.slice(4).trim());
    expect(heads.length).toBe(7);
    expect(heads).toEqual(NINE_SUBS);
  });
  it('폭 표 값 = 공용 상수(폭 4단계)', () => {
    const t = sub(section('⑨'), '폭 4단계');
    const steps = fam.WIDTH_STEPS ?? [];
    expect(steps.length).toBe(4);
    for (const s of steps) {
      const range = s.min == null ? `≤${s.max}` : s.max == null ? `≥${s.min}` : `${s.min}–${s.max}`;
      const rows = t.split('\n').filter((l) => l.startsWith(`| ${s.name} |`));
      expect(rows.length, s.name).toBe(1);
      expect(rows[0], s.name).toContain(`| ${range} |`);
    }
  });
  it('낮은 높이 행 = ≈500 · 잠정 · 다음 intent', () => {
    const rows = sub(section('⑨'), '낮은 높이 규칙').split('\n').filter((l) => l.startsWith('| 낮은 높이'));
    expect(rows.length).toBe(1);
    expect(rows[0]).toContain('≈500');
    expect(rows[0]).toContain('잠정');
    expect(rows[0]).toContain('다음 intent');
  });
  it('넓은 표 행 = 휴대폰 카드 · 패드 이상 열 고정', () => {
    const rows = sub(section('⑨'), '넓은 표 원칙').split('\n').filter((l) => l.startsWith('| 넓은 표'));
    expect(rows.length).toBe(1);
    expect(rows[0]).toContain('카드');
    expect(rows[0]).toContain('열 고정');
  });
  it('지도 경계 행 = 코드 상수 `MAP_CELL_BOUNDARY`', () => {
    expect(typeof MAP_CELL_BOUNDARY).toBe('number');
    const rows = sub(section('⑨'), '지도 · 그림 위 도구 원칙').split('\n').filter((l) => l.startsWith('| 지도 칸 경계'));
    expect(rows.length).toBe(1);
    expect(rows[0]).toContain(`${MAP_CELL_BOUNDARY}px`);
    expect(rows[0]).toContain('MAP_CELL_BOUNDARY');
  });
  it('허용 폭 값 표 = 공용 상수 · 입력 조건 두 표기 · 면제 목록 16줄 · 24건', () => {
    const t = sub(section('⑨'), '허용 폭 값 · 면제 목록');
    const maxRow = t.split('\n').filter((l) => l.startsWith('| `max-width` |'));
    const minRow = t.split('\n').filter((l) => l.startsWith('| `min-width` |'));
    expect(maxRow.length).toBe(1);
    expect(minRow.length).toBe(1);
    for (const v of fam.WIDTH_MAX ?? []) expect(maxRow[0]).toContain(`${v}px`);
    for (const v of fam.WIDTH_MIN ?? []) expect(minRow[0]).toContain(`${v}px`);
    for (const c of fam.INPUT_ALLOWED ?? []) expect(t).toContain(`\`${c}\``);
    expect(t).toContain('media-exempt.txt');
    expect(t).toContain('16줄');
    expect(t).toContain('24건');
  });
  it('⑨ 에는 문서 전체 한 줄 단언의 대상(대비 합격선 · btn 행)이 없다', () => {
    const s = section('⑨');
    expect(s).not.toContain('대비 4.5:1 이상');
    expect(s.split('\n').some((l) => l.startsWith('| btn |'))).toBe(false);
  });
});

describe('⑷ 정본 ⑤ · ⑥ · 머리말 · 캡처 규칙(V1)', () => {
  it('머리말 = 조건 a~i · 문서에 a~h 0', () => {
    expect(DOC.split('\n')[2]).toContain('조건 a~i');
    expect(DOC).not.toContain('a~h');
  });
  it('⑤ 새 줄 4개 — [i] · 터치 기기 · 마우스 전용 동작 · 캡처 도구 수치 모드', () => {
    const lines = section('⑤').split('\n');
    const i = lines.filter((l) => /^\d+\. \[i\] /.test(l));
    expect(i.length).toBe(1);
    expect(i[0]).toContain('(hover: hover)');
    expect(i[0]).toContain('허용 값');
    const touch = lines.filter((l) => l.startsWith('- 터치 기기'));
    expect(touch.length).toBe(1);
    expect(touch[0]).toContain('44');
    expect(touch[0]).toContain('16');
    expect(touch[0]).toContain('`title`');
    const mouse = lines.filter((l) => l.startsWith('- 마우스 전용 동작'));
    expect(mouse.length).toBe(1);
    expect(mouse[0]).toContain('누름 대안');
    const cap = lines.filter((l) => l.startsWith('- 새 화면·새 상태는 캡처 도구를 수치 모드로'));
    expect(cap.length).toBe(1);
  });
  it('⑤ 누름 피드백 줄 바로 다음 줄은 그대로 비활성 규칙이다', () => {
    const lines = section('⑤').split('\n');
    const at = lines.findIndex((l) => l.startsWith('- 누름 피드백'));
    expect(at).toBeGreaterThanOrEqual(0);
    expect(lines[at + 1] ?? '').toContain('비활성 = opacity .5');
  });
  it('캡처 규칙 문장 = 6크기 × 2테마 · 1180 이하 터치 입력(3폭 0)', () => {
    const line = section('⑤').split('\n').filter((l) => l.includes('scenes.json'));
    expect(line.length).toBe(1);
    expect(line[0]).toContain('6크기 × 2테마');
    expect(line[0]).toContain('1180 이하 터치 입력');
    expect(DOC).not.toContain('3폭 × 2테마');
  });
  it('⑥ 제목 a~i · i 행 · 요약 끝 · 준비 실패 · 못 보는 것', () => {
    const s = section('⑥');
    expect(s.split('\n')[1]).toContain('조건 a~i');
    const rows = s.split('\n').filter((l) => l.startsWith('| i |'));
    expect(rows.length).toBe(1);
    expect(rows[0]).toContain('media-exempt.txt');
    expect(rows[0]).toContain('(hover: hover)');
    expect(s).toContain('폭·입력 조건 밖 i(면제 m)');
    const ready = s.split('\n').find((l) => l.startsWith('**red(준비 · 종료 78)**')) ?? '';
    expect(ready).toContain('media-exempt.txt');
    const blind = s.split('\n').find((l) => l.startsWith('**못 보는 것**')) ?? '';
    expect(blind).toContain('JS 폭 측정');
    expect(blind).toContain('TSX');
    expect(blind).toContain('`src` 밖 HTML');
  });
  it('① 토큰 행에 터치 기기 분기', () => {
    const row = section('① 층').split('\n').filter((l) => l.startsWith('| tokens |'));
    expect(row.length).toBe(1);
    expect(row[0]).toContain('터치 기기');
  });
  it('문서 전체 한 줄 단언 보호 — 대비 줄 1 · 프리미티브 btn 행 1(followups L1 과 같은 거르기)', () => {
    expect(DOC.split('\n').filter((l) => l.includes('대비 4.5:1 이상')).length).toBe(1);
    expect(DOC.split('\n').filter((l) => l.startsWith('| btn |') && l.includes('<button class="btn"')).length).toBe(1);
  });
});

// ── ⑸ spec 틀 · 디자인 검수 절차 · selftest 사례 수 ────────────────────────
describe('⑸ spec 틀 i 행 · 검수 절차 토큰 행 · selftest 사례 수(승인 요청 템플릿 ⓐ)', () => {
  it('to-spec 디자인 제약 표 = 머리 a~i · h 행 다음 i 행 · a~h 0', () => {
    const t = raw('.agents/skills/to-spec/SKILL.md');
    expect(t).not.toContain('a~h');
    expect(t).toContain('조건 a~i');
    const lines = t.split('\n');
    const h = lines.findIndex((l) => l.startsWith('|') && l.includes('`design-docs.mjs` 로 다시 씀 | h |'));
    expect(h).toBeGreaterThanOrEqual(0);
    expect(lines[h + 1] ?? '').toMatch(/\| i \| \|$/);
    expect(lines[h + 1] ?? '').toContain('(hover: hover)');
  });
  it('design-review 토큰 행만 a~i · 정적 합격선 행은 1개 그대로', () => {
    const t = raw('.agents/skills/design-review/SKILL.md');
    const token = t.split('\n').filter((l) => l.startsWith('| 토큰 |'));
    expect(token.length).toBe(1);
    expect(token[0]).toContain('`frontend-design-lint` a~i');
    expect(t.split('\n').filter((l) => l.startsWith('| 정적 합격선')).length).toBe(1);
  });
  it('selftest 사례 수 = 끝 문장 수 = README 사례 수', () => {
    const st = raw('gates/tools/frontend-design-lint-selftest.sh');
    const calls = st.split('\n').filter((l) => /^expect (green|red|ready) /.test(l)).length;
    const direct = st.split('\n').filter((l) => l.includes('✓ ⓛ 디스크에 없는 대상 파일 (ready)')).length;
    const n = calls + direct;
    expect(n).toBe(30);
    expect(st).toContain(`검사 ${n}건 전건 기대대로`);
    const readme = raw('gates/README.md').split('\n').filter((l) => l.startsWith('| `frontend-design-lint-selftest`'));
    expect(readme.length).toBe(1);
    expect(readme[0]).toContain(`| **${n}** |`);
  });
});
