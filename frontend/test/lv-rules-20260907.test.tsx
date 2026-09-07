/**
 * WU-B5 · Lv 연결 규칙 — 화면 쪽 (PRD-07 · 08 · 09 · 10).
 *
 * 오라클 = `dev-package/prd/rounds/R-B-2-server.md §2` WU-B5 의 **수용 기준 6건** 중 화면이
 * 잴 수 있는 넷 ＋ 대비 계측. 서버 400 과 응답 열쇠는
 * `services/core-api/tests/test_lv_parent_rules.py` 가 잰다.
 *
 *   ㈎ 자기 Lv=Lv0 → 안내가 `Lv0` 하나이고 후보 셀렉트로 Lv0 만 부른다
 *   ㈏ 자기 Lv=Lv1 · 후보에 Lv2 → 그 행이 **보이고** 못 고르며 **사유가 읽힌다**
 *   ㈐ 사유·칩의 **대비 4.5:1 이상** (토큰 값에서 계산한다 — 눈으로 보지 않는다)
 *   ㈑ 사후 충돌 → 연결이 **남고** `확인 필요` ＋ `데이터셋 만들기` 비활성, 되돌리면 산다
 *   ㈒ 불일치 안내 축자 ＋ 등록이 **막히지 않는다**
 *   ㈓ 종전 「자동으로 정해져요」 문면이 코드에 **0건**이다(`〈194〉` 반전)
 */
// @ts-expect-error — 타입 선언 없이 런타임만 쓴다(vitest 는 node 위에서 돈다 · `topics-drift` 와 같은 규율).
import { readFileSync } from 'node:fs';
// @ts-expect-error — 같은 이유.
import { resolve } from 'node:path';
import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { SessionProvider } from '../src/permission/session';
import { UploadEntry } from '../src/components/upload/UploadEntry';
import type { DatasetRow, LineageSource, LineageSuggestionResponse } from '../src/components/lineage/types';
import type { PreviewSource, ProjectSource, UploadSource, UploadSources } from '../src/components/upload/types';
import type { CurrentAccount, Schemas } from '../src/api/client';

const UPLOAD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0UP1';
const FILE_ID = '01JYZ9K7WQ3N8V4M2X6C5B0FI1';
const LV0 = '01JYZ9K7WQ3N8V4M2X6C5B0D00';
const LV1 = '01JYZ9K7WQ3N8V4M2X6C5B0D01';
const LV2 = '01JYZ9K7WQ3N8V4M2X6C5B0D02';

function account(): CurrentAccount {
  return {
    accountId: '01JYZ9K7WQ3N8V4M2X6C5B0AC1',
    name: '호랑이',
    email: 'tiger@example.ac.kr',
    role: '연구원',
    labId: '01JYZ9K7WQ3N8V4M2X6C5B0LB1',
    labName: '수자원순환연구실',
    permissions: {
      '업로드·편집': true,
      '프로젝트 생성': true,
      '승인 위임': false,
      '연구실 설정': false,
    } as Record<Schemas['PermissionSwitch'], boolean>,
  } as unknown as CurrentAccount;
}

function row(datasetId: string, name: string, processingLevel: number): DatasetRow {
  return { datasetId, name, processingLevel } as unknown as DatasetRow;
}

const ALL = [row(LV0, '원자료 강우', 0), row(LV1, '1차 가공 강우', 1), row(LV2, '집계 강우', 2)];

interface Calls {
  registered: Record<string, unknown>[];
  levels: (number | null | undefined)[];
}

function fakes() {
  const calls: Calls = { registered: [], levels: [] };
  const files = [{ fileId: FILE_ID, fileName: 'nakdong_precip_2025_Lv2.nc', kind: '본체',
                   byteSize: 349_000, createdAt: '2026-09-07T00:00:00Z' }];
  const upload = {
    async create() { return { uploadId: UPLOAD_ID, files } as never; },
    async status() {
      return { uploadId: UPLOAD_ID, ready: true, failure: null, metadataComplete: true, files } as never;
    },
    async register(body: Record<string, unknown>) {
      calls.registered.push(body);
      return { datasetId: '01JYZ9K7WQ3N8V4M2X6C5B0DS1' } as never;
    },
    async attachGrid() { return [] as never; },
  } as unknown as UploadSource;
  const preview = {
    async palettes() { return [{ palette: 'viridis', label: '비리디스' }]; },
    async createRender() { return { renderId: 'r', state: '실패', failure: null } as never; },
    async getRender() { return { renderId: 'r', state: '실패', failure: null } as never; },
  } as unknown as PreviewSource;
  const projects = {
    async list() { return []; },
    async create() { return { projectId: '01JYZ9K7WQ3N8V4M2X6C5B0PR9', name: 'x', type: '국가과제' } as never; },
  } as unknown as ProjectSource;
  const lineage: LineageSource = {
    async suggestions() {
      return {
        degraded: false,
        scope: { labId: 'l', labName: '수자원순환연구실', searchedCount: 0 },
        rawDataLikely: false,
        suggestions: [],
      } as unknown as LineageSuggestionResponse;
    },
    async candidates(level?: number | null) {
      // **서버가 거른다** — 화면이 자기 Lv 로 자르지 않는다(PRD-08 축자).
      calls.levels.push(level);
      return level === null || level === undefined ? ALL : ALL.filter((r) => r.processingLevel === level);
    },
  };
  return { sources: { upload, preview, projects, lineage } as unknown as UploadSources, calls };
}

async function click(el: Element | null) {
  fireEvent.click(el as HTMLElement);
  await act(async () => {});
}
async function change(el: Element | null, value: string) {
  fireEvent.change(el as HTMLElement, { target: { value } });
  await act(async () => {});
}

function makeFile() {
  const f = new File(['x'], 'nakdong_precip_2025_Lv2.nc', { type: 'application/octet-stream' });
  Object.defineProperty(f, 'size', { value: 349_000 });
  return f;
}

/** ① 에서 자기 Lv 를 고르고 ③ 연결 단계까지 간다. */
async function openLineage(sources: UploadSources, selfLevel: string) {
  render(
    <MemoryRouter initialEntries={['/datasets']}>
      <SessionProvider account={account()}>
        <UploadEntry sources={sources} />
      </SessionProvider>
    </MemoryRouter>,
  );
  await click(screen.getByTestId('gnb-upload'));
  await screen.findByTestId('upload-modal');
  fireEvent.change(screen.getByTestId('up-drop-input'), { target: { files: [makeFile()] } });
  await act(async () => {});
  await screen.findByTestId('up-files');
  await click(await screen.findByTestId('reg-open'));
  await screen.findByTestId('reg-steps');
  await change(screen.getByTestId('reg-level'), selfLevel);
  await click(screen.getByRole('button', { name: /^③/ }));
  await screen.findByTestId('lin-step');
}

/** WCAG 2.x 상대 명도 대비. **눈으로 보지 않고 계산한다.** */
function contrast(a: string, b: string): number {
  const lum = (hex: string) => {
    const v = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
      .map((c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
    return 0.2126 * (v[0] as number) + 0.7152 * (v[1] as number) + 0.0722 * (v[2] as number);
  };
  const [hi, lo] = [lum(a), lum(b)].sort((x, y) => y - x) as [number, number];
  return (hi + 0.05) / (lo + 0.05);
}

// vitest 의 실행 뿌리는 `frontend/` 다(`vite.config.ts` 자리).
declare const process: { cwd(): string };
const read = (rel: string): string => readFileSync(resolve(process.cwd(), rel), 'utf8');
const CSS: string = read('src/components/lineage/lineage.css');
const token = (name: string) => {
  const m = CSS.match(new RegExp(`${name}:\\s*(#[0-9a-fA-F]{6})`));
  if (!m) throw new Error(`토큰이 없다: ${name}`);
  return m[1] as string;
};

// ═══ ㈎ 자기 Lv=Lv0 — 안내 범위가 `Lv0` 하나다 ═══
describe('PRD-07 연결 단계 안내', () => {
  it('자기 Lv=Lv0 이면 안내가 `Lv0` 하나이고 후보를 Lv0 으로 좁힐 수 있다', async () => {
    const { sources, calls } = fakes();
    await openLineage(sources, 'Lv0');
    expect(screen.getByTestId('lin-lv-scope').textContent).toContain(
      '지금 이 데이터는 Lv0 · Lv0 가공 전 데이터만 연결할 수 있어요.');
    expect(screen.getByTestId('lin-goto-classify').textContent).toBe('분류에서 바꾸기');

    await click(screen.getByTestId('lin-add'));
    await screen.findByTestId('lin-picker');
    await change(screen.getByTestId('lin-lv-filter'), '0');
    expect(calls.levels).toContain(0);
    const items = within(screen.getByTestId('lin-picker')).getAllByRole('listitem');
    expect(items).toHaveLength(1);
    expect(items[0]?.textContent).toContain('원자료 강우');
  });

  it('자기 Lv=Lv2 이면 범위가 `Lv0~Lv2` 다', async () => {
    const { sources } = fakes();
    await openLineage(sources, 'Lv2');
    expect(screen.getByTestId('lin-lv-scope').textContent).toContain(
      '지금 이 데이터는 Lv2 · Lv0~Lv2 가공 전 데이터만 연결할 수 있어요.');
  });

  it('`분류에서 바꾸기` 는 ① 로 데려갈 뿐 자기 Lv 를 고치지 않는다', async () => {
    const { sources } = fakes();
    await openLineage(sources, 'Lv1');
    await click(screen.getByTestId('lin-goto-classify'));
    expect((screen.getByTestId('reg-level') as HTMLSelectElement).value).toBe('Lv1');
  });
});

// ═══ ㈏ 초과 후보 — 보이되 못 고르고 사유가 읽힌다 ═══
describe('PRD-08 초과 후보는 흐리게 ＋ 사유', () => {
  it('자기 Lv=Lv1 이고 후보에 Lv2 가 있으면 그 행이 보이고 선택 불가이며 사유가 읽힌다', async () => {
    const { sources } = fakes();
    await openLineage(sources, 'Lv1');
    await click(screen.getByTestId('lin-add'));
    const picker = await screen.findByTestId('lin-picker');
    // **숨기지 않는다** — 세 행이 다 있다.
    expect(within(picker).getAllByRole('listitem')).toHaveLength(3);
    const over = screen.getByTestId(`lin-pick-${LV2}`) as HTMLButtonElement;
    expect(over).toBeTruthy();
    expect(over.disabled).toBe(true);
    expect(screen.getByTestId(`lin-over-${LV2}`).textContent).toBe(
      '이 데이터(Lv1)보다 높은 단계예요. 연결을 지우거나 분류에서 가공 단계를 올려 주세요.');
    // 자기 Lv 이하는 그대로 고를 수 있다 — 대조군이다.
    expect((screen.getByTestId(`lin-pick-${LV1}`) as HTMLButtonElement).disabled).toBe(false);
    expect((screen.getByTestId(`lin-pick-${LV0}`) as HTMLButtonElement).disabled).toBe(false);
  });

  // ═══ ㈐ 대비 계측 ═══
  it('사유 문구와 `확인 필요` 칩의 대비가 4.5:1 이상이다', () => {
    const ratio = contrast(token('--lin-over-ink'), token('--lin-over-bg'));
    expect(ratio).toBeGreaterThanOrEqual(4.5);
    // 흐려지는 것은 **이름 버튼 하나**다 — 사유가 그것과 같은 색이면 `R-21` 이 고친 자리가 되돌아온다.
    expect(token('--lin-over-name')).not.toBe(token('--lin-over-ink'));
    // 불투명도로 행 전체를 내리지 않는다(같은 이유).
    expect(CSS).not.toMatch(/\.lin-picker li\.is-over\s*\{[^}]*opacity/);
  });
});

// ═══ ㈑ 사후 충돌 ═══
describe('PRD-09 사후 충돌은 지우지 않고 막는다', () => {
  it('Lv2 로 Lv2 를 연결한 뒤 자기 Lv 를 Lv1 로 내리면 연결이 남고 `확인 필요` ＋ 버튼이 막힌다', async () => {
    const { sources } = fakes();
    await openLineage(sources, 'Lv2');
    await click(screen.getByTestId('lin-add'));
    await screen.findByTestId('lin-picker');
    await click(screen.getByTestId(`lin-pick-${LV2}`));
    expect(screen.getAllByTestId('lin-card')).toHaveLength(1);
    expect(screen.queryByTestId('lin-need-check')).toBeNull();
    expect((screen.getByTestId('reg-done') as HTMLButtonElement).disabled).toBe(false);

    // ① 에서 자기 Lv 를 내린다 — **연결을 손대지 않는다.**
    await click(screen.getByRole('button', { name: /^①/ }));
    await change(screen.getByTestId('reg-level'), 'Lv1');
    await click(screen.getByRole('button', { name: /^③/ }));
    expect(screen.getAllByTestId('lin-card')).toHaveLength(1);
    expect(screen.getByTestId('lin-need-check').textContent).toBe('확인 필요');
    expect(screen.getByTestId('lin-conflict-note').textContent).toContain('연결을 지우거나');
    expect((screen.getByTestId('reg-done') as HTMLButtonElement).disabled).toBe(true);

    // 되돌리면 칩이 사라지고 버튼이 산다.
    await click(screen.getByRole('button', { name: /^①/ }));
    await change(screen.getByTestId('reg-level'), 'Lv2');
    await click(screen.getByRole('button', { name: /^③/ }));
    expect(screen.queryByTestId('lin-need-check')).toBeNull();
    expect((screen.getByTestId('reg-done') as HTMLButtonElement).disabled).toBe(false);
  });
});

// ═══ ㈒ 불일치는 경고만 ═══
describe('PRD-10 불일치는 경고만이다', () => {
  it('자기 Lv3 · 부모 Lv0 이면 안내가 뜨고 등록은 그대로 성공한다', async () => {
    const { sources, calls } = fakes();
    await openLineage(sources, 'Lv3');
    await click(screen.getByTestId('lin-add'));
    await screen.findByTestId('lin-picker');
    await click(screen.getByTestId(`lin-pick-${LV0}`));
    await click(screen.getAllByTestId('lin-confirm')[0] as HTMLElement);
    expect(screen.getByTestId('lin-lv-mismatch').textContent).toBe(
      '고른 가공 단계는 Lv3이고, 연결한 데이터로 계산하면 Lv1이에요. 그대로 두어도 등록돼요.');
    // **막지 않는다** — 버튼이 살아 있고 요청이 나간다.
    expect((screen.getByTestId('reg-done') as HTMLButtonElement).disabled).toBe(false);
    await click(screen.getByRole('button', { name: /^②/ }));
    await change(screen.getByTestId('reg-name'), '불일치 시험');
    await change(screen.getByTestId('reg-summary'), '설명 한 줄');
    // `데이터셋 만들기` 는 ③ 의 버튼이다 — 적을 칸에 적고 다시 돌아온다.
    await click(screen.getByRole('button', { name: /^③/ }));
    await click(screen.getByTestId('reg-done'));
    expect(calls.registered).toHaveLength(1);
    expect(calls.registered[0]?.processingLevelUserSet).toBe('Lv3');
  });
});

// ═══ ㈓ 종전 문면 철거 (`〈194〉` 반전) ═══
describe('〈194〉 반전 — 자동 보정 문면이 남아 있지 않다', () => {
  it('`자동으로 정해져요` 문자열이 계보 화면 코드에 0건이다', () => {
    const src: string = read('src/components/lineage/LineageStep.tsx');
    // 주석의 「종전 = …」 인용 한 자리만 남는다 — 화면에 그려지는 자리는 0 이다.
    const rendered = src.split('\n').filter((l) => l.includes('자동으로 정해져요') && !l.trimStart().startsWith('종전'));
    expect(rendered).toHaveLength(0);
  });
});

// ═══ ㈔ ⟨advisor ② · Fix 1⟩ 파일을 빼면 연결 카드·충돌도 함께 내린다 ═══
describe('PRD-09 · 파일 제거는 연결 상태까지 내린다', () => {
  it('연결·충돌이 있는 상태에서 파일을 빼고 다시 올리면 카드 0 · 충돌 칩 0 이다', async () => {
    const { sources } = fakes();
    await openLineage(sources, 'Lv2');
    await click(screen.getByTestId('lin-add'));
    await screen.findByTestId('lin-picker');
    await click(screen.getByTestId(`lin-pick-${LV2}`));
    await click(screen.getAllByTestId('lin-confirm')[0] as HTMLElement);
    // 자기 Lv 를 내려 사후 충돌을 만든다 — 지우는 것이 아니라 칩이 선다.
    await click(screen.getByRole('button', { name: /^①/ }));
    await change(screen.getByTestId('reg-level'), 'Lv1');
    await click(screen.getByRole('button', { name: /^③/ }));
    expect(screen.getAllByTestId('lin-card')).toHaveLength(1);
    expect(screen.getByTestId('lin-need-check')).toBeTruthy();

    // 파일을 빼고 같은 파일을 다시 올린다 — 고지 문면이 「입력하던 내용은 사라져요」다.
    await click(screen.getByLabelText(/빼기$/));
    fireEvent.change(screen.getByTestId('up-drop-input'), { target: { files: [makeFile()] } });
    await act(async () => {});
    await screen.findByTestId('up-files');
    await click(await screen.findByTestId('reg-open'));
    await screen.findByTestId('reg-steps');
    await click(screen.getByRole('button', { name: /^③/ }));
    await screen.findByTestId('lin-step');
    expect(screen.queryAllByTestId('lin-card')).toHaveLength(0);
    expect(screen.queryByTestId('lin-need-check')).toBeNull();
    expect(screen.queryByTestId('lin-conflict-note')).toBeNull();
  });
});

// ═══ ㈕ ⟨advisor ② · Fix 3⟩ 미확인 연결 카드도 「손댐」이다 (PRD-14) ═══
describe('PRD-14 되묻기 — 확인 전 카드도 센다', () => {
  it('연결 카드를 만들고 확인하지 않은 채 Esc 를 누르면 닫기 확인이 뜬다', async () => {
    const { sources } = fakes();
    // 자기 Lv 는 기본값 그대로 둔다 — 세는 것이 카드 하나뿐임을 분명히 한다.
    await openLineage(sources, 'Lv2');
    await click(screen.getByTestId('lin-add'));
    await screen.findByTestId('lin-picker');
    await click(screen.getByTestId(`lin-pick-${LV2}`));
    expect(screen.getAllByTestId('lin-card')).toHaveLength(1);
    // 확인(`lin-confirm`)을 누르지 않는다 — 승격된 카드는 언마운트로 사라지지 않으므로 셀 수 있다.
    fireEvent.keyDown(document, { key: 'Escape' });
    await act(async () => {});
    expect(screen.getByTestId('upload-close-confirm')).toBeTruthy();
  });
});
