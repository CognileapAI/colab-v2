/**
 * 휴대폰·패드 대응 20260926 L3a — 누르면 보이는 설명(V9 · `title` 전용 정보 10곳).
 *
 * 오라클 = `dev-package/prd/specs/S-DEVICE-WIDTH-INPUT-20260926.md` V9 · 부록 C(10곳 · `title` 전수 25 · 9파일) ·
 * 구현 결정 「`title` 전용 10곳」 · 「새 문구안」 9–18행(확정 · 원문 그대로) · 우려 10ⓐ(같은 칸 안 라벨 바로 뒤 펼침) ·
 * 「레인 확정」 L3a 제약(advisor ①) · 파일 끝 터치 블록 규칙 · 디자인 제약(설명 글 대비는 CSS 계산 단언).
 * 입력 방식 훅은 모듈 모의로 터치 · 마우스 두 갈래를 모두 그린다. 마우스 갈래는 새 단추 0 · 원래 `title` 을 단언한다
 * (green-by-skip 방지 — 마우스에서도 대상 요소가 실제로 그려졌는지 먼저 센다).
 * jsdom 은 배치를 재지 않는다 — 44 높이 · 1440 픽셀 · 세로 넘침은 캡처 수치(레인 보고)가 근거다.
 */
// @ts-expect-error — 타입 선언 없이 런타임만 쓴다(선례 device-width-input-20260926-L1).
import { readFileSync, readdirSync, statSync } from 'node:fs';
// @ts-expect-error — 같은 이유.
import { join, resolve } from 'node:path';
import ts from 'typescript';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { CatalogTable } from '../src/components/catalog/CatalogTable';
import { useCatalog } from '../src/components/catalog/useCatalog';
import { FIXTURE_ROWS, fixtureCatalogSource } from '../src/components/catalog/fixture';
import type { DatasetRow } from '../src/components/catalog/types';
import { ProjectDatasetTable } from '../src/components/project/ProjectDatasetTable';
import { FIXTURE_PROJECTS } from '../src/components/project/fixture';
import { VerifiedBadge } from '../src/components/approval/VerifiedBadge';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { fixtureDetailSource } from '../src/components/detail/fixture';
import { FIXTURE_LINEAGE } from '../src/components/lineage/graphFixture';
import type { LineageGraph, LineageGraphSource } from '../src/components/lineage/graphTypes';
import { AccountAdminPage } from '../src/routes/AccountAdminPage';
import { SessionProvider } from '../src/permission/session';

declare const process: { cwd(): string };

const mode = vi.hoisted(() => ({ current: 'mouse' as 'touch' | 'mouse' }));
vi.mock('../src/components/common/useInputMode', () => ({ useInputMode: () => mode.current }));

const raw = (rel: string): string => String(readFileSync(resolve(process.cwd(), rel), 'utf8'));

/* ═══ 확정 문구(「새 문구안」 9–18 · 원문 그대로) ═══════════════════════════════ */
const PENDING_TOUCH = '승인 처리가 아직 도착하지 않았어요';
const PENDING_MOUSE = '승인 처리가 아직 도착하지 않았다';
const MISMATCH = '가공 단계가 계보로 계산한 값과 다릅니다';
const VERIFIED_MEANING = '교수가 품질을 보증했어요';
const SRC_NOTE = '연구실 밖 출처라 상세 화면이 없어요';
const TOMB_NOTE = '지워진 데이터라 상세 화면이 없어요 · 2026-08-09';
const STALE_1 = '2026-07-30 에 확정했는데 2026-08-11 에 파일이 바뀌었어요';
const STALE_2 = '2025-09-01 에 확정했는데 2025-10-02 에 파일이 바뀌었어요';
const PROJECT_LIST = '홍수기 강우-유출 분석 · ERA5 강수 편의 보정 비교';

/* ═══ 부록 C 10곳 · 속성 13 ═════════════════════════════════════════════════════ */
type Site = { n: number; file: string; attrs: { tag: string; key: string }[] };
const SITES: Site[] = [
  { n: 1, file: 'src/components/catalog/CatalogTable.tsx', attrs: [{ tag: 'td', key: 'lineageTitle(row)' }] },
  { n: 2, file: 'src/components/catalog/CatalogTable.tsx', attrs: [{ tag: 'td', key: "row.projects.names.join(' · ')" }] },
  { n: 3, file: 'src/components/catalog/CatalogTable.tsx', attrs: [{ tag: 'span', key: 'VERIFIED_PENDING_TITLE' }] },
  { n: 4, file: 'src/components/project/ProjectDatasetTable.tsx', attrs: [{ tag: 'span', key: 'VERIFIED_PENDING_TITLE' }] },
  { n: 5, file: 'src/components/catalog/CatalogTable.tsx', attrs: [{ tag: 'span', key: 'LEVEL_MISMATCH_A11Y' }] },
  { n: 6, file: 'src/components/approval/VerifiedBadge.tsx', attrs: [{ tag: 'span', key: 'VERIFIED_MEANING' }] },
  { n: 7, file: 'src/components/lineage/LineageSection.tsx', attrs: [{ tag: 'div', key: 'nodeTitle(n)' }] },
  { n: 8, file: 'src/components/lineage/LineageSection.tsx', attrs: [{ tag: 'span', key: 'nodeTitle(node)' }] },
  { n: 9, file: 'src/components/lineage/LineageSection.tsx', attrs: [{ tag: 'span', key: 'e.method' }] },
  {
    n: 10,
    file: 'src/routes/AccountAdminPage.tsx',
    attrs: [
      { tag: 'td', key: 'row.email' },
      { tag: 'td', key: 'row.name' },
      { tag: 'td', key: 'roleText' },
      { tag: 'td', key: 'labText' },
    ],
  },
];

/** `title` 전수 기대값(부록 C · 파일별). 고칠 자리 13 ＋ 아이콘 단추 3 ＋ 미리보기 6 ＋ 업로드 1 ＋ 본인 상태 1 ＋ 부품 속성 1. */
const TITLE_PER_FILE: Record<string, number> = {
  'src/components/approval/VerifiedBadge.tsx': 1,
  'src/components/catalog/CatalogTable.tsx': 6,
  'src/components/common/VariableTable.tsx': 1,
  'src/components/lineage/LineageSection.tsx': 3,
  'src/components/preview/PreviewPickRow.tsx': 6,
  'src/components/project/ProjectDatasetTable.tsx': 1,
  'src/components/upload/PreviewPanel.tsx': 1,
  'src/components/upload/UploadModal.tsx': 1,
  'src/routes/AccountAdminPage.tsx': 5,
};

type TitleAttr = { file: string; tag: string; intrinsic: boolean; init: string };

function tsxFiles(dir = 'src'): string[] {
  const out: string[] = [];
  for (const name of readdirSync(resolve(process.cwd(), dir)) as string[]) {
    const rel = join(dir, name);
    if (statSync(resolve(process.cwd(), rel)).isDirectory()) out.push(...tsxFiles(rel));
    else if (rel.endsWith('.tsx')) out.push(rel);
  }
  return out;
}

/** TS 구문 나무로 JSX `title` 속성을 모은다(주석 · 문자열 안 글자는 세지 않는다). */
function titleAttrs(): TitleAttr[] {
  const out: TitleAttr[] = [];
  for (const file of tsxFiles()) {
    const src = ts.createSourceFile(file, raw(file), ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
    const visit = (node: ts.Node): void => {
      if (ts.isJsxAttribute(node) && node.name.getText(src) === 'title') {
        const owner = node.parent.parent as ts.JsxOpeningLikeElement;
        const tag = owner.tagName.getText(src);
        out.push({ file, tag, intrinsic: /^[a-z]/.test(tag), init: node.initializer ? node.initializer.getText(src) : '' });
      }
      ts.forEachChild(node, visit);
    };
    visit(src);
  }
  return out;
}

describe('목록 먼저 — 부록 C 10곳 · 속성 13 · `title` 전수 25(9파일)', () => {
  it('자리 목록 길이 = 10 · 속성 합 = 13 · 번호 1–10', () => {
    expect(SITES).toHaveLength(10);
    expect(SITES.map((s) => s.n)).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
    expect(SITES.reduce((a, s) => a + s.attrs.length, 0)).toBe(13);
  });
  it('파일별 `title` 속성 수 = 부록 C 기대값(9파일) · 그 밖 파일 0 · 원소 속성 24 ＋ 부품 속성 1 = 25', () => {
    const all = titleAttrs();
    const per: Record<string, number> = {};
    for (const a of all) per[a.file] = (per[a.file] ?? 0) + 1;
    expect(Object.keys(TITLE_PER_FILE)).toHaveLength(9);
    expect(per).toEqual(TITLE_PER_FILE);
    expect(all.filter((a) => a.intrinsic)).toHaveLength(24);
    expect(all.filter((a) => !a.intrinsic).map((a) => `${a.file} <${a.tag}>`)).toEqual([
      'src/components/upload/PreviewPanel.tsx <PreviewExpandOverlay>',
    ]);
    expect(all).toHaveLength(25);
  });
  for (const site of SITES) {
    it(`${site.n} 자리 \`title\` 속성 ${site.attrs.length}개가 원래 파일 · 원래 요소에 남는다(마우스에서 그대로)`, () => {
      const inFile = titleAttrs().filter((a) => a.file === site.file);
      for (const want of site.attrs) {
        const hits = inFile.filter((a) => a.tag === want.tag && a.init.includes(want.key));
        expect(hits, `${site.file} <${want.tag} title=…${want.key}…>`).toHaveLength(1);
      }
    });
  }
  it('새 「누르면 보이는 설명」 부품 파일에는 `title` 이 없다', () => {
    expect(raw('src/components/common/TouchNote.tsx')).not.toMatch(/\btitle=/);
  });
});

/* ═══ 그리기 도우미 ═════════════════════════════════════════════════════════════ */

function CatalogHarness(props: { rows: DatasetRow[]; onOpen: (id: string) => void }) {
  const state = useCatalog(fixtureCatalogSource(props.rows));
  return <CatalogTable state={state} uploaderNames={new Map()} onOpen={props.onOpen} onDownload={() => {}} />;
}

const MISMATCH_NAME = 'nakdong_precip_2025_Lv2.nc';
const catalogRows = (): DatasetRow[] =>
  FIXTURE_ROWS.map((r) => (r.name === MISMATCH_NAME ? ({ ...r, processingLevelMismatch: true } as DatasetRow) : r));

async function renderCatalog(onOpen = vi.fn()) {
  render(
    <MemoryRouter>
      <CatalogHarness rows={catalogRows()} onOpen={onOpen} />
    </MemoryRouter>,
  );
  await waitFor(() => expect(screen.getAllByRole('row').length).toBe(FIXTURE_ROWS.length + 1));
  return onOpen;
}

function rowOf(name: string): HTMLElement {
  const row = screen.getAllByRole('row').find((r) => within(r).queryByText(name) !== null);
  expect(row, name).toBeTruthy();
  return row as HTMLElement;
}

/** 설명 단추 계약 — `type=button` · `aria-expanded` · `aria-controls` → 펼침 글 `id`. 누르면 정확한 문장이 보인다. */
function expectDisclosure(trigger: HTMLElement, text: string, onOpen?: ReturnType<typeof vi.fn>) {
  expect(trigger.tagName).toBe('BUTTON');
  expect(trigger.getAttribute('type')).toBe('button');
  expect(trigger.getAttribute('aria-expanded')).toBe('false');
  const id = trigger.getAttribute('aria-controls');
  expect(id, 'aria-controls').toBeTruthy();
  const panel = document.getElementById(id!);
  expect(panel, '펼침 글 id').not.toBeNull();
  expect(panel!.hidden).toBe(true);
  fireEvent.click(trigger);
  expect(trigger.getAttribute('aria-expanded')).toBe('true');
  expect(panel!.hidden).toBe(false);
  expect(panel!.textContent).toBe(text);
  if (onOpen) expect(onOpen).not.toHaveBeenCalled();
  fireEvent.click(trigger);
  expect(trigger.getAttribute('aria-expanded')).toBe('false');
  expect(panel!.hidden).toBe(true);
  if (onOpen) expect(onOpen).not.toHaveBeenCalled();
}

const OPEN_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA1';
const PARENT_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA6';
const BASE = FIXTURE_LINEAGE[OPEN_ID]!;
const TOMB: LineageGraph = {
  ...BASE,
  nodes: BASE.nodes.map((n) =>
    n.datasetId === PARENT_ID ? { ...n, kind: '묘비' as const, navigable: false, deletedAt: '2026-08-09T00:00:00Z' } : n,
  ),
};
const only = (graph: LineageGraph): LineageGraphSource => ({ async get() { return graph; } });

async function renderDetail() {
  render(
    <MemoryRouter initialEntries={[`/datasets/${OPEN_ID}`]}>
      <Routes>
        <Route path="/datasets/:datasetId" element={<DatasetDetailPage source={fixtureDetailSource()} lineageSource={only(TOMB)} />} />
      </Routes>
    </MemoryRouter>,
  );
  await screen.findByTestId('lineage-section');
}

const pendingProjectRows = () => {
  const rows = FIXTURE_PROJECTS.flatMap((p) => p.datasets);
  const pending = rows.filter((r) => !r.verified).slice(0, 1);
  const done = rows.filter((r) => r.verified).slice(0, 1);
  expect(pending).toHaveLength(1);
  expect(done).toHaveLength(1);
  return [...pending, ...done];
};

const LAB = '0000000000000000000000000A';
const OPERATOR = {
  accountId: '00000000000000000000000AP1', name: '운영자', email: 'op@example.com', role: '교수' as const,
  permissions: {}, labId: LAB, labName: 'A 연구실', canManageServiceAccounts: true, mustChangePassword: false,
};
const ACCOUNTS = [
  { accountId: '000000000000000000000000A1', email: 'very.long.address.for.wrapping@example.com', name: '한 사람', labId: LAB, labName: '수자원환경연구실', role: '연구원', status: 'active', operator: false, lastLoginAt: '2026-09-11T02:03:04Z' },
  { accountId: '00000000000000000000000BP1', email: 'two@example.com', name: '두 사람', labId: LAB, labName: null, role: '교수', status: 'inactive', operator: false, lastLoginAt: null },
];
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } });

async function renderAccounts() {
  vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
    const url = new URL((input as Request).url);
    if (url.pathname.endsWith('/admin/account-options')) return json({ labs: [{ labId: LAB, name: 'A 연구실' }], roles: ['교수', '연구원'] });
    if (url.pathname.endsWith('/admin/accounts-v2')) return json({ accounts: ACCOUNTS });
    return json({ message: '모의하지 않은 경로' }, 500);
  });
  render(<SessionProvider account={OPERATOR}><AccountAdminPage /></SessionProvider>);
  await screen.findByText('very.long.address.for.wrapping@example.com');
  const cells = Array.from(document.querySelectorAll<HTMLElement>('.account-table td.account-cell-text'));
  expect(cells).toHaveLength(ACCOUNTS.length * 4);
  return cells;
}

afterEach(() => {
  vi.restoreAllMocks();
  mode.current = 'mouse';
});

/* ═══ 터치 — 1–6 누르면 보이는 설명 단추 ════════════════════════════════════════ */
describe('터치 — 1–6 짧은 라벨이 설명 단추가 된다(누르면 같은 칸 안 라벨 바로 뒤에 펼침 · 행 이동 없음)', () => {
  beforeEach(() => { mode.current = 'touch'; });

  it('목록 설명 단추 = 8(확인 필요 2 · 외 N 1 · 승인 전 4 · 계산값과 다름 1)', async () => {
    await renderCatalog();
    const table = screen.getByRole('table', { name: '데이터셋 목록' });
    expect(table.querySelectorAll('[aria-controls]')).toHaveLength(8);
  });

  it('1 목록 계보 「확인 필요」 → 확정일 · 수정일 문장(칸의 `title` 없음)', async () => {
    const onOpen = await renderCatalog();
    const row = rowOf(MISMATCH_NAME);
    const chip = within(row).getByText('확인 필요');
    const trigger = chip.closest('button')!;
    expect(trigger).not.toBeNull();
    expect(trigger.closest('td')!.hasAttribute('title')).toBe(false);
    expectDisclosure(trigger, STALE_1, onOpen);
    // 펼침 글은 같은 칸 안이다(우려 10ⓐ)
    expect(trigger.closest('td')!.contains(document.getElementById(trigger.getAttribute('aria-controls')!))).toBe(true);
    const other = within(rowOf('ERA5_precip_2025_Lv1.grib')).getByText('확인 필요').closest('button')!;
    expectDisclosure(other, STALE_2, onOpen);
  });

  it('1 대조군 — 「확정」 · 「원천」 · 「기록 없음」 칩은 단추가 아니다', async () => {
    await renderCatalog();
    for (const label of ['확정', '원천', '기록 없음']) {
      for (const el of screen.getAllByText(label, { selector: '.lin' })) expect(el.closest('button'), label).toBeNull();
    }
  });

  it('2 목록 프로젝트 「외 N」 → 전체 프로젝트 목록(칸의 `title` 없음)', async () => {
    const onOpen = await renderCatalog();
    const trigger = within(rowOf(MISMATCH_NAME)).getByText('외 1').closest('button')!;
    expect(trigger).not.toBeNull();
    expect(trigger.closest('td')!.hasAttribute('title')).toBe(false);
    expectDisclosure(trigger, PROJECT_LIST, onOpen);
  });

  it('3 목록 「승인 전」 → 「승인 처리가 아직 도착하지 않았어요」(라벨의 `title` 없음)', async () => {
    const onOpen = await renderCatalog();
    const chips = within(rowOf('GK2A_rain_202506_Lv0.HDF5')).getAllByTestId('verified-pending');
    expect(chips).toHaveLength(1);
    expect(chips[0]!.hasAttribute('title')).toBe(false);
    expect(chips[0]!.textContent).toBe('승인 전');
    expectDisclosure(chips[0]!.closest('button')!, PENDING_TOUCH, onOpen);
  });

  it('5 목록 「계산값과 다름」 → 같은 문장(라벨의 `title` 없음 · 낭독기 이름 유지)', async () => {
    const onOpen = await renderCatalog();
    const mark = within(rowOf(MISMATCH_NAME)).getByTestId('lvl-mismatch');
    expect(mark.hasAttribute('title')).toBe(false);
    expect(mark.getAttribute('aria-label')).toBe(MISMATCH);
    expectDisclosure(mark.closest('button')!, MISMATCH, onOpen);
  });

  it('4 프로젝트 상세 「승인 전」 → 「승인 처리가 아직 도착하지 않았어요」 · 행 이동 없음', () => {
    const onOpen = vi.fn();
    render(<ProjectDatasetTable rows={pendingProjectRows()} canManage={false} onOpen={onOpen} onUnlink={async () => {}} />);
    const chip = screen.getByTestId('verified-pending');
    expect(chip.hasAttribute('title')).toBe(false);
    expect(screen.getByTestId('project-datasets').querySelectorAll('[aria-controls]')).toHaveLength(1);
    expectDisclosure(chip.closest('button')!, PENDING_TOUCH, onOpen);
  });

  it('6 상세 머리 「Verified」 → 「교수가 품질을 보증했어요」 · 미승인은 배지 없음 그대로', () => {
    const { unmount } = render(<VerifiedBadge verified />);
    const badge = screen.getByText('Verified');
    expect(badge.hasAttribute('title')).toBe(false);
    expectDisclosure(badge.closest('button')!, VERIFIED_MEANING);
    unmount();
    const empty = render(<VerifiedBadge verified={false} />);
    expect(empty.container.innerHTML).toBe('');
  });
});

/* ═══ 터치 — 7–9 계보 ═════════════════════════════════════════════════════════ */
describe('터치 — 7 계보 그래프 노드 · 8 계보 목록 줄 아래 글 · 9 방법 라벨 줄바꿈', () => {
  beforeEach(() => { mode.current = 'touch'; });

  it('7 원천 · 묘비 노드 = 누르는 노드(`role=button` · `tabIndex=0` · `aria-expanded` · `aria-controls`) · 이동 노드는 링크 그대로', async () => {
    await renderDetail();
    const nodes = screen.getAllByTestId('lin-node');
    const noted = nodes.filter((n) => n.dataset.kind === '원천' || n.dataset.kind === '묘비');
    expect(noted).toHaveLength(3);
    for (const n of noted) {
      expect(n.getAttribute('role')).toBe('button');
      expect(n.tabIndex).toBe(0);
      expect(n.hasAttribute('title')).toBe(false);
      expect(n.getAttribute('aria-expanded')).toBe('false');
      expect(document.getElementById(n.getAttribute('aria-controls') ?? '')).not.toBeNull();
    }
    for (const n of nodes.filter((x) => x.dataset.kind === '파생')) expect(n.tagName).toBe('A');
  });

  it('7 원천 노드를 누르면 · Enter · Space 로 「연구실 밖 출처라 상세 화면이 없어요」가 펼쳐지고 접힌다', async () => {
    await renderDetail();
    const src = screen.getAllByTestId('lin-node').filter((n) => n.dataset.kind === '원천')[0]!;
    const panel = document.getElementById(src.getAttribute('aria-controls')!)!;
    expect(panel.hidden).toBe(true);
    fireEvent.click(src);
    expect(src.getAttribute('aria-expanded')).toBe('true');
    expect(panel.hidden).toBe(false);
    expect(panel.textContent).toBe(SRC_NOTE);
    fireEvent.keyDown(src, { key: 'Enter' });
    expect(src.getAttribute('aria-expanded')).toBe('false');
    expect(panel.hidden).toBe(true);
    fireEvent.keyDown(src, { key: ' ' });
    expect(src.getAttribute('aria-expanded')).toBe('true');
    expect(panel.textContent).toBe(SRC_NOTE);
    fireEvent.keyDown(src, { key: 'a' });
    expect(src.getAttribute('aria-expanded')).toBe('true');
  });

  it('7 묘비 노드를 누르면 「지워진 데이터라 상세 화면이 없어요 · {삭제일}」', async () => {
    await renderDetail();
    const tomb = screen.getAllByTestId('lin-node').filter((n) => n.dataset.kind === '묘비');
    expect(tomb).toHaveLength(1);
    fireEvent.click(tomb[0]!);
    expect(document.getElementById(tomb[0]!.getAttribute('aria-controls')!)!.textContent).toBe(TOMB_NOTE);
  });

  it('8 계보 목록 묘비 줄: 이름의 `title` 없음 · 줄 아래에 같은 문장이 보인다(누르지 않아도)', async () => {
    await renderDetail();
    const row = screen.getAllByTestId('lrow').filter((r) => r.dataset.stage === '지워진 데이터');
    expect(row).toHaveLength(1);
    const name = row[0]!.querySelector('.ln-name')!;
    expect(name.hasAttribute('title')).toBe(false);
    const visible = Array.from(row[0]!.querySelectorAll('div')).filter((d) => d.textContent === TOMB_NOTE);
    expect(visible).toHaveLength(1);
    expect(visible[0]!.hidden).toBe(false);
  });

  it('9 방법 라벨: `title` 없음 · 줄바꿈 표지(말줄임 대신) · 새 문구 0', async () => {
    await renderDetail();
    const labels = screen.getAllByTestId('lin-method');
    expect(labels.length).toBeGreaterThan(0);
    for (const l of labels) {
      expect(l.hasAttribute('title')).toBe(false);
      expect(l.classList.contains('lin-way--wrap')).toBe(true);
    }
    expect(labels.map((l) => l.textContent)).toContain('✦ 유역 클리핑 · 유역 평균');
  });

  it('6 상세 머리 배지도 상세 화면 안에서 단추다(이 픽스처는 승인됨)', async () => {
    await renderDetail();
    const badge = within(screen.getByTestId('detail-header')).getByText('Verified');
    expect(badge.closest('button')).not.toBeNull();
  });
});

/* ═══ 터치 — 10 계정 관리 ════════════════════════════════════════════════════ */
describe('터치 — 10 계정 관리 잘린 칸은 말줄임 대신 줄바꿈', () => {
  beforeEach(() => { mode.current = 'touch'; });
  it('이메일 · 이름 · 역할 · 연구실 칸: `title` 없음 · 줄바꿈 표지 · 본인 상태 줄의 `title` 은 그대로', async () => {
    const cells = await renderAccounts();
    for (const c of cells) {
      expect(c.hasAttribute('title'), c.textContent ?? '').toBe(false);
      expect(c.classList.contains('account-cell-wrap')).toBe(true);
    }
    expect(cells.map((c) => c.textContent)).toContain('수자원환경연구실');
  });
});

/* ═══ 마우스 — 원래 요소 · 원래 `title` · 새 단추 0 ═══════════════════════════ */
describe('마우스(판별 불가 포함) — 원래 요소와 `title` 그대로 · 새 단추 0', () => {
  beforeEach(() => { mode.current = 'mouse'; });

  it('목록: 설명 단추 0 · 1 · 2 · 3 · 5 의 `title` 원문', async () => {
    await renderCatalog();
    const table = screen.getByRole('table', { name: '데이터셋 목록' });
    expect(table.querySelectorAll('[aria-controls]')).toHaveLength(0);
    const row = rowOf(MISMATCH_NAME);
    const lin = within(row).getByText('확인 필요');
    expect(lin.closest('button')).toBeNull();
    expect(lin.closest('td')!.getAttribute('title')).toBe(STALE_1);
    const more = within(row).getByText('외 1');
    expect(more.closest('button')).toBeNull();
    expect(more.closest('td')!.getAttribute('title')).toBe(PROJECT_LIST);
    const pending = screen.getAllByTestId('verified-pending');
    expect(pending).toHaveLength(4);
    for (const p of pending) {
      expect(p.closest('button')).toBeNull();
      expect(p.getAttribute('title')).toBe(PENDING_MOUSE);
    }
    const mark = within(row).getByTestId('lvl-mismatch');
    expect(mark.closest('button')).toBeNull();
    expect(mark.getAttribute('title')).toBe(MISMATCH);
    expect(document.querySelectorAll('.touch-note-text')).toHaveLength(0);
  });

  it('프로젝트 상세: 설명 단추 0 · 4 의 `title` 원문', () => {
    render(<ProjectDatasetTable rows={pendingProjectRows()} canManage={false} onOpen={() => {}} onUnlink={async () => {}} />);
    const chip = screen.getByTestId('verified-pending');
    expect(chip.closest('button')).toBeNull();
    expect(chip.getAttribute('title')).toBe(PENDING_MOUSE);
    expect(screen.getByTestId('project-datasets').querySelectorAll('[aria-controls]')).toHaveLength(0);
  });

  it('상세 머리 배지: 단추 아님 · 6 의 `title` 원문', () => {
    render(<VerifiedBadge verified />);
    const badge = screen.getByText('Verified');
    expect(badge.closest('button')).toBeNull();
    expect(badge.getAttribute('title')).toBe(VERIFIED_MEANING);
  });

  it('계보: 노드 7 은 `title` 있는 원래 상자(누르는 역할 0) · 8 은 이름 `title` · 줄 아래 글 0 · 9 는 `title` · 줄바꿈 표지 0', async () => {
    await renderDetail();
    const nodes = screen.getAllByTestId('lin-node');
    const src = nodes.filter((n) => n.dataset.kind === '원천');
    expect(src).toHaveLength(2);
    for (const n of src) {
      expect(n.getAttribute('title')).toBe(SRC_NOTE);
      expect(n.hasAttribute('role')).toBe(false);
      expect(n.hasAttribute('tabindex')).toBe(false);
      expect(n.hasAttribute('aria-controls')).toBe(false);
    }
    const tomb = nodes.filter((n) => n.dataset.kind === '묘비');
    expect(tomb).toHaveLength(1);
    expect(tomb[0]!.getAttribute('title')).toBe(TOMB_NOTE);
    const row = screen.getAllByTestId('lrow').filter((r) => r.dataset.stage === '지워진 데이터')[0]!;
    expect(row.querySelector('.ln-name')!.getAttribute('title')).toBe(TOMB_NOTE);
    expect(Array.from(row.querySelectorAll('div')).filter((d) => d.textContent === TOMB_NOTE)).toHaveLength(0);
    const labels = screen.getAllByTestId('lin-method');
    expect(labels.length).toBeGreaterThan(0);
    for (const l of labels) {
      expect(l.getAttribute('title')).toBe(l.textContent!.replace(/^✦ /, ''));
      expect(l.classList.contains('lin-way--wrap')).toBe(false);
    }
    expect(document.querySelectorAll('[aria-controls]')).toHaveLength(0);
    expect(within(screen.getByTestId('detail-header')).getByText('Verified').closest('button')).toBeNull();
  });

  it('계정 관리: 4 칸 `title` = 화면 값 전체 · 줄바꿈 표지 0', async () => {
    const cells = await renderAccounts();
    for (const c of cells) {
      expect(c.getAttribute('title')).toBe(c.textContent);
      expect(c.classList.contains('account-cell-wrap')).toBe(false);
    }
  });
});

/* ═══ CSS — 부품 CSS · 줄바꿈 규칙 · 파일 끝 터치 블록 · 대비 ═══════════════════════ */

const strip = (css: string): string => css.replace(/\/\*[\s\S]*?\*\//g, '');
type Rule = { selectors: string[]; body: string; media: string; top: number };
function rules(css: string, media = '', topBase = -1): Rule[] {
  const out: Rule[] = [];
  let i = 0;
  let n = 0;
  while (i < css.length) {
    const open = css.indexOf('{', i);
    if (open < 0) break;
    const head = css.slice(i, open).trim();
    let depth = 1;
    let j = open + 1;
    while (j < css.length && depth > 0) {
      if (css[j] === '{') depth += 1;
      else if (css[j] === '}') depth -= 1;
      j += 1;
    }
    const inner = css.slice(open + 1, j - 1);
    const top = topBase < 0 ? n : topBase;
    if (head.startsWith('@layer')) out.push(...rules(inner, media, -1));
    else if (head.startsWith('@media')) out.push(...rules(inner, head, top));
    else if (!head.startsWith('@')) out.push({ selectors: head.split(',').map((s) => s.trim().replace(/\s+/g, ' ')), body: inner.trim(), media, top });
    n += 1;
    i = j;
  }
  return out;
}
const decls = (b: string): string[] => b.split(';').map((d) => d.trim().replace(/\s+/g, ' ')).filter(Boolean);
const COARSE = '@media (pointer: coarse)';
const CONTROL = 'var(--control-height)';
const cssRules = (rel: string): Rule[] => rules(strip(raw(rel)));
const ruleOf = (rs: Rule[], sel: string, media = ''): Rule[] => rs.filter((r) => r.media === media && r.selectors.includes(sel));

describe('CSS — 새 부품 CSS(누르면 보이는 설명)', () => {
  const FILE = 'src/components/common/touchNote.css';
  it('한 층 블록(`@layer screens`) · 새 색 0 · 강제 우선 0', () => {
    const t = strip(raw(FILE)).trim();
    expect(t.startsWith('@layer screens {')).toBe(true);
    expect(t.endsWith('}')).toBe(true);
    expect(t).not.toMatch(/#[0-9a-f]{3,8}\b|rgba?\(|hsla?\(/i);
    expect(t).not.toContain('!important');
  });
  it('터치 블록: 설명 단추 · 누르는 노드의 최소 높이 · 최소 가로 = 44 토큰 · 글자 크기 선언 0 · 블록 1', () => {
    const rs = cssRules(FILE);
    const coarse = rs.filter((r) => r.media === COARSE);
    expect(new Set(coarse.map((r) => r.top)).size).toBe(1);
    const d = coarse.filter((r) => r.selectors.includes('.touch-note-trigger')).flatMap((r) => decls(r.body));
    expect(d).toContain(`min-height: ${CONTROL}`);
    expect(d).toContain(`min-width: ${CONTROL}`);
    expect(coarse.flatMap((r) => decls(r.body)).filter((x) => x.startsWith('font'))).toEqual([]);
  });
  it('설명 단추는 글자를 바꾸지 않는다(`font: inherit`) · 누르는 순간 피드백(`:active` = 누름 면 토큰)', () => {
    const rs = cssRules(FILE);
    const btn = ruleOf(rs, '.touch-note-btn').flatMap((r) => decls(r.body));
    expect(btn).toContain('font: inherit');
    expect(btn).toContain('color: inherit');
    const active = ruleOf(rs, '.touch-note-btn:active').flatMap((r) => decls(r.body));
    expect(active).toContain('background: var(--color-surface-pressed)');
  });
  it('펼침 글 = 캡션 토큰 · 보조 글자 토큰 · 줄바꿈 · 접힘은 `hidden` 이 이긴다', () => {
    const rs = cssRules(FILE);
    const text = ruleOf(rs, '.touch-note-text').flatMap((r) => decls(r.body));
    expect(text).toContain('font-size: var(--text-caption)');
    expect(text).toContain('color: var(--color-text-muted)');
    expect(text).toContain('white-space: normal');
    expect(ruleOf(rs, '.touch-note-text[hidden]').flatMap((r) => decls(r.body))).toContain('display: none');
  });
});

describe('CSS — 줄바꿈 규칙(9 · 10)은 파일 끝 터치 블록 앞 · 조건 없는 표지 규칙(마우스 규칙 불변)', () => {
  it('계보 그래프: `.lin-way--wrap` 규칙이 말줄임을 풀고 터치 블록 앞에 있다 · 기존 `.lin-way` 규칙(150px 말줄임) 그대로', () => {
    const rs = cssRules('src/components/lineage/lineageGraph.css');
    const wrap = ruleOf(rs, '.detail-page .lin-way.lin-way--wrap');
    expect(wrap).toHaveLength(1);
    const d = decls(wrap[0]!.body);
    expect(d).toContain('white-space: normal');
    expect(d).toContain('height: auto');
    expect(d).toContain('text-overflow: clip');
    const base = decls(ruleOf(rs, '.detail-page .lin-way')[0]!.body);
    expect(base).toEqual(expect.arrayContaining(['white-space: nowrap', 'max-width: 150px', 'overflow: hidden', 'text-overflow: ellipsis', 'height: 23px']));
    const coarseTop = rs.find((r) => r.media === COARSE)!.top;
    expect(wrap[0]!.top).toBeLessThan(coarseTop);
    expect(coarseTop).toBe(Math.max(...rs.map((r) => r.top)));
  });
  it('계보 그래프: 노드 옆 펼침 글은 칸 폭(178px) 안 · 누르는 노드의 누름 피드백 규칙', () => {
    const rs = cssRules('src/components/lineage/lineageGraph.css');
    expect(decls(ruleOf(rs, '.detail-page .lin-col > .touch-note-text')[0]!.body)).toContain('max-width: 178px');
    expect(decls(ruleOf(rs, '.detail-page .ln[role="button"]:active')[0]!.body)).toContain('border-color: var(--color-primary-600)');
  });
  it('계정 관리: `.account-cell-wrap` 규칙이 줄바꿈을 켜고 터치 블록 앞에 있다 · 기존 말줄임 규칙 그대로', () => {
    const rs = cssRules('src/auth/login.css');
    const wrap = ruleOf(rs, '.account-table td.account-cell-wrap');
    expect(wrap).toHaveLength(1);
    const d = decls(wrap[0]!.body);
    expect(d).toContain('white-space: normal');
    expect(d).toContain('overflow-wrap: anywhere');
    expect(decls(ruleOf(rs, '.account-table td:not(.account-row-actions-cell)')[0]!.body)).toEqual(['overflow: hidden', 'text-overflow: ellipsis']);
    const coarseTop = rs.find((r) => r.media === COARSE)!.top;
    expect(wrap[0]!.top).toBeLessThan(coarseTop);
    expect(coarseTop).toBe(Math.max(...rs.map((r) => r.top)));
  });
});

/* ═══ 대비 — 터치 전용 설명 글(보조 글자 토큰)은 두 테마의 면 위에서 4.5 이상(디자인 제약 · CSS 계산 단언) ═══ */
describe('대비 — 펼침 글 `--color-text-muted` 대 면 토큰(라이트 · 다크) ≥ 4.5', () => {
  const tokens = strip(raw('src/shell/tokens.css'));
  const block = (head: string): Map<string, string> => {
    const at = tokens.indexOf(head);
    expect(at, head).toBeGreaterThanOrEqual(0);
    const open = tokens.indexOf('{', at);
    const close = tokens.indexOf('}', open);
    const m = new Map<string, string>();
    for (const d of decls(tokens.slice(open + 1, close))) {
      const k = d.indexOf(':');
      if (d.startsWith('--')) m.set(d.slice(0, k).trim(), d.slice(k + 1).trim());
    }
    return m;
  };
  const light = block(':root {');
  const dark = block(':root[data-theme="dark"] {');
  const resolveHex = (name: string, theme: 'light' | 'dark'): string => {
    let v = (theme === 'dark' ? dark.get(name) : undefined) ?? light.get(name);
    for (let k = 0; k < 8 && v?.startsWith('var('); k += 1) {
      const inner = v.slice(4, -1).trim();
      v = (theme === 'dark' ? dark.get(inner) : undefined) ?? light.get(inner);
    }
    expect(v, `${name} ${theme}`).toMatch(/^#[0-9a-f]{6}$/i);
    return v!;
  };
  const lum = (hex: string): number => {
    const c = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255).map((x) => (x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4));
    return 0.2126 * c[0]! + 0.7152 * c[1]! + 0.0722 * c[2]!;
  };
  const ratio = (a: string, b: string): number => {
    const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p) as [number, number];
    return (x + 0.05) / (y + 0.05);
  };
  const SURFACES = ['--color-surface', '--color-surface-alt', '--color-bg'];
  for (const theme of ['light', 'dark'] as const) {
    for (const s of SURFACES) {
      it(`${theme} · ${s}`, () => {
        expect(ratio(resolveHex('--color-text-muted', theme), resolveHex(s, theme))).toBeGreaterThanOrEqual(4.5);
      });
    }
  }
});
