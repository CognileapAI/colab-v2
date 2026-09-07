/**
 * WU-B8 · PRD-27 — 「기록 없음」 선언 체크박스 ＋ 홈 대시보드 모수 통일.
 *
 * 오라클 = `dev-package/prd/rounds/R-B-2-server.md §2` WU-B8 의 **수용 기준 7건** 중 화면이
 * 잴 수 있는 넷. 판정식 6항과 400 은 `services/core-api/tests/test_lineage_unknown.py` 가 잰다.
 *
 *   ㈎ ③ 에 체크박스가 있고 라벨이 **축자**다 ＋ 체크하면 `lineageUnknown: true` 가 실린다
 *   ㈏ 확정 부모 ≥1 → **비활성 ＋ 사유가 읽히고 칸이 사라지지 않는다**(연결도 남는다)
 *   ㈐ 자기 Lv=`Lv0` → 체크박스가 **보이지 않는다**(판정 ⑷ 가 이미 `원천` 으로 가른다)
 *   ㈑ 종전 문면(rev1 `#unknownChk`)이 코드에 **0건**이다 — 그 문자열은 이 파일에도 적지
 *      않는다(자기 자신이 검색에 걸린다). 아래 `LEGACY_LABEL` 이 조각에서 조립한다.
 *   ㈒ 홈 타일 숫자의 모수 == 그 링크가 여는 목록의 모수 (`확인 필요` ＋ `기록 없음`)
 *
 * 모든 단언은 **대상 건수를 먼저 잰다** — 빈 집합 통과(green-by-skip)를 막는다.
 */
// @ts-expect-error — 타입 선언 없이 런타임만 쓴다(vitest 는 node 위에서 돈다).
import { readFileSync, readdirSync, statSync } from 'node:fs';
// @ts-expect-error — 같은 이유.
import { join, resolve } from 'node:path';
import { act, fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { SessionProvider } from '../src/permission/session';
import { UploadEntry } from '../src/components/upload/UploadEntry';
import {
  LINEAGE_UNKNOWN_DISABLED_REASON,
  LINEAGE_UNKNOWN_LABEL,
} from '../src/components/lineage/LineageStep';
import {
  LINEAGE_TODO_PATH,
  UNSETTLED_LINEAGE_STATES,
} from '../src/components/dashboard/SummaryTiles';
import type {
  DatasetRow,
  LineageSource,
  LineageSuggestionResponse,
} from '../src/components/lineage/types';
import type {
  PreviewSource,
  ProjectSource,
  UploadSource,
  UploadSources,
} from '../src/components/upload/types';
import type { CurrentAccount, Schemas } from '../src/api/client';

const UPLOAD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0UP1';
const FILE_ID = '01JYZ9K7WQ3N8V4M2X6C5B0FI1';
const LV0 = '01JYZ9K7WQ3N8V4M2X6C5B0D00';
const LV1 = '01JYZ9K7WQ3N8V4M2X6C5B0D01';

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

const ALL = [row(LV0, '원자료 강우', 0), row(LV1, '1차 가공 강우', 1)];

function fakes() {
  const calls: { registered: Record<string, unknown>[] } = { registered: [] };
  const files = [{ fileId: FILE_ID, fileName: 'nakdong_precip_2025_Lv2.nc', kind: '본체',
                   byteSize: 349_000, createdAt: '2026-09-07T00:00:00Z' }];
  const upload = {
    async create() { return { uploadId: UPLOAD_ID, files } as never; },
    async status() {
      return { uploadId: UPLOAD_ID, ready: true, failure: null,
               metadataComplete: true, files } as never;
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
    async create() {
      return { projectId: '01JYZ9K7WQ3N8V4M2X6C5B0PR9', name: 'x', type: '국가과제' } as never;
    },
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
      return level === null || level === undefined
        ? ALL : ALL.filter((r) => r.processingLevel === level);
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

async function submit() {
  await click(screen.getByRole('button', { name: /^②/ }));
  await change(screen.getByTestId('reg-summary'), '시험용 설명 한 줄');
  await click(screen.getByRole('button', { name: /^③/ }));
  await click(screen.getByTestId('reg-done'));
}

// ═══ ㈎ 체크박스가 있고 라벨이 축자다 ═══
describe('PRD-27 ③ 에 「기록 없음」 선언 체크박스가 있다', () => {
  it('라벨이 축자이고, 체크하면 등록 요청에 `lineageUnknown: true` 가 실린다', async () => {
    const { sources, calls } = fakes();
    await openLineage(sources, 'Lv1');

    const box = screen.getByTestId('lin-unknown-check') as HTMLInputElement;
    expect(box.disabled).toBe(false);
    expect(box.checked).toBe(false);
    // **라벨은 축자다** — 상수도 화면도 같은 문장이어야 한다.
    expect(LINEAGE_UNKNOWN_LABEL).toBe('가공 전 데이터를 못 찾았어요 — 기록 없이 등록할게요');
    expect(screen.getByTestId('lin-unknown').textContent).toContain(LINEAGE_UNKNOWN_LABEL);
    // 확정 부모가 0건이라 사유 줄은 없다.
    expect(screen.queryByTestId('lin-unknown-why')).toBeNull();

    await click(box);
    expect((screen.getByTestId('lin-unknown-check') as HTMLInputElement).checked).toBe(true);
    await submit();
    expect(calls.registered).toHaveLength(1);
    expect(calls.registered[0]!.lineageUnknown).toBe(true);
  });

  it('체크하지 않으면 열쇠 자체를 싣지 않는다 — 그 상태는 `기록 없음` 이 아니라 `확인 필요` 다', async () => {
    const { sources, calls } = fakes();
    await openLineage(sources, 'Lv1');
    expect(screen.getByTestId('lin-unknown-check')).toBeTruthy();
    await submit();
    expect(calls.registered).toHaveLength(1);
    expect('lineageUnknown' in calls.registered[0]!).toBe(false);
  });
});

// ═══ ㈏ 확정 부모 ≥1 → 비활성 ＋ 사유 ＋ 칸이 남는다 ═══
describe('PRD-27 확정 부모가 있으면 비활성이고 칸은 사라지지 않는다', () => {
  it('부모 1건을 확정하면 체크박스가 비활성이고 사유가 읽히며 연결도 그대로 남는다', async () => {
    const { sources, calls } = fakes();
    await openLineage(sources, 'Lv1');
    // **먼저 체크한 뒤** 부모를 붙인다 — 옛 `true` 가 그대로 실려 서버 400 이 되는 경로를 막는다.
    await click(screen.getByTestId('lin-unknown-check'));

    await click(screen.getByTestId('lin-add'));
    await screen.findByTestId('lin-picker');
    await click(screen.getByTestId(`lin-pick-${LV0}`));
    await click(screen.getAllByTestId('lin-confirm')[0] as HTMLElement);
    expect(screen.getAllByTestId('lin-card')).toHaveLength(1);

    // **칸이 사라지지 않는다** — 숨기면 왜 못 고르는지가 함께 사라진다.
    const box = screen.getByTestId('lin-unknown-check') as HTMLInputElement;
    expect(box.disabled).toBe(true);
    expect(box.checked).toBe(false);
    expect(screen.getByTestId('lin-unknown-why').textContent).toBe(
      LINEAGE_UNKNOWN_DISABLED_REASON);

    // **연결을 지우지 않는다** ＋ 요청에 `lineageUnknown` 이 실리지 않는다(서버 400 방지).
    await submit();
    expect(calls.registered).toHaveLength(1);
    expect((calls.registered[0]!.lineageParents as unknown[])).toHaveLength(1);
    expect('lineageUnknown' in calls.registered[0]!).toBe(false);
  });
});

// ═══ ㈐ Lv0 이면 보이지 않는다 ═══
describe('PRD-27 Lv0 이면 체크박스가 보이지 않는다', () => {
  it('자기 Lv=Lv0 에서는 칸 자체가 없고, Lv1 로 바꾸면 다시 선다', async () => {
    const { sources } = fakes();
    await openLineage(sources, 'Lv0');
    expect(screen.queryByTestId('lin-unknown')).toBeNull();

    // 대조 — 같은 화면에서 Lv 만 바꾸면 칸이 선다(부재가 화면 고장이 아님을 증명한다).
    await click(screen.getByRole('button', { name: /^①/ }));
    await change(screen.getByTestId('reg-level'), 'Lv1');
    await click(screen.getByRole('button', { name: /^③/ }));
    expect(screen.getByTestId('lin-unknown')).toBeTruthy();
  });

  it('Lv1 에서 체크한 뒤 Lv0 으로 바꾸면 그 선언이 요청에 실리지 않는다', async () => {
    const { sources, calls } = fakes();
    await openLineage(sources, 'Lv1');
    await click(screen.getByTestId('lin-unknown-check'));
    await click(screen.getByRole('button', { name: /^①/ }));
    await change(screen.getByTestId('reg-level'), 'Lv0');
    await click(screen.getByRole('button', { name: /^③/ }));
    expect(screen.queryByTestId('lin-unknown')).toBeNull();
    await submit();
    expect(calls.registered).toHaveLength(1);
    expect('lineageUnknown' in calls.registered[0]!).toBe(false);
  });
});

// ═══ ㈑ 종전 문면이 코드에 0건 ═══
describe('PRD-27 종전 문면은 코드에 남지 않는다', () => {
  it('폐기된 종전 라벨이 `src`·`test` 전체에서 0건이다', () => {
    // **조각에서 조립한다** — 통째로 적으면 이 시험 파일 자신이 걸려 언제나 red 다.
    const LEGACY_LABEL = ['못 ', '찾은 것이 있어요 (기록 없음)'].join('');
    const roots = ['src', 'test'].map((d) => resolve(__dirname, '..', d));
    const files: string[] = [];
    const walk = (dir: string) => {
      for (const name of readdirSync(dir)) {
        if (name === 'node_modules') continue;
        const full = join(dir, name);
        if (statSync(full).isDirectory()) walk(full);
        else if (/\.(ts|tsx|css)$/.test(name)) files.push(full);
      }
    };
    roots.forEach(walk);
    // **대상 건수를 먼저 잰다** — 0건을 훑고 「0건이다」라고 말하지 않는다.
    expect(files.length).toBeGreaterThan(100);
    const hits = files.filter((f) =>
      readFileSync(f, 'utf8').includes(LEGACY_LABEL));
    expect(hits).toEqual([]);
  });
});

// ═══ ㈒ 홈 타일 숫자 == 링크 목록 건수 ═══
describe('PRD-27 홈 타일의 모수와 링크 목록의 모수가 같다', () => {
  it('타일 링크가 `확인 필요`·`기록 없음` 두 값을 그대로 싣는다', () => {
    // 서버 타일(`insight.py` `SETTLED_STATES = ("확정","원천")` 의 여집합)과 같은 두 값이다.
    expect([...UNSETTLED_LINEAGE_STATES]).toEqual(['확인 필요', '기록 없음']);
    const query = new URLSearchParams(LINEAGE_TODO_PATH.split('?')[1]);
    expect(query.getAll('lineageState')).toEqual(['확인 필요', '기록 없음']);
  });

  it('할 일 함의 조회가 타일과 **같은 상수**를 쓴다 — 값을 두 곳에 적지 않는다', () => {
    const src = readFileSync(
      resolve(__dirname, '..', 'src/components/dashboard/dashboardSource.ts'), 'utf8');
    expect(src).toContain('UNSETTLED_LINEAGE_STATES');
    // 값 리터럴이 이 파일에 **다시** 적혀 있으면 한쪽만 고쳐지는 자리가 되살아난다.
    expect(src).not.toMatch(/\[\s*'확인 필요'\s*,\s*'기록 없음'\s*\]/);
  });
});
