/**
 * R-LTH-REVIEW-1 Task 3 — 등록 가공 단계 **기본값이 계산값을 따른다** (spec §6 ㉱ · §8-2 19·20).
 *
 * 오라클 = 라운드 파일 `dev-package/prd/rounds/R-LTH-REVIEW-1.md ### Task 3` 목적 ⑴ ＋
 * spec `2026-09-13-lth-review-1.md` §6 ㉱ 축자 넷 —
 *   ㈎ 확인된 부모 ≥1 이고 부모 Lv 를 모두 알면 기본 선택값 = **계산값**(최대 부모 Lv ＋ 1 · 상한 Lv3)
 *   ㈏ 부모 **0건**이면 계산값 `Lv0` → 기본 선택값 `Lv0`. 다른 단계를 고르면 등록 화면에도
 *      불일치 줄이 선다(카드 ⑩ ⓐ 축자 「부모 0건이면 Lv0 · 그 경우 등록 화면에도 경고가 선다」)
 *   ㈐ 사람이 한 번 고르면 **추종을 멈춘다**(고른 값을 덮지 않는다)
 *   ㈑ 불일치 상태에서도 등록이 **성공한다**(미결-2 ⓐ 「경고만」 회귀)
 *
 * green-by-skip 방지 = ㈏ 와 ㈐ 가 대조군이고, ㈑ 이 회귀 단언이다(§8-6 ⑶).
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { SessionProvider } from '../src/permission/session';
import { UploadEntry } from '../src/components/upload/UploadEntry';
import type { DatasetRow, LineageSource, LineageSuggestionResponse } from '../src/components/lineage/types';
import type { PreviewSource, ProjectSource, UploadSource, UploadSources } from '../src/components/upload/types';
import type { CurrentAccount, Schemas } from '../src/api/client';
import { levelMismatchNotice } from '../src/components/common/processingLevel';

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

function fakes() {
  const calls: { registered: Record<string, unknown>[] } = { registered: [] };
  const files = [{ fileId: FILE_ID, fileName: 'nakdong_precip_2025_Lv2.nc', kind: '본체',
                   byteSize: 349_000, createdAt: '2026-09-13T00:00:00Z' }];
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
    async candidates(input) {
      const level = typeof input === 'number' ? input : input?.processingLevel;
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

const stepBtn = (n: '①' | '②' | '③') =>
  screen.getByRole('button', { name: new RegExp(`^${n}`) });

const levelValue = () => (screen.getByTestId('reg-level') as HTMLSelectElement).value;

/** 등록을 열고 **가공 단계를 건드리지 않은 채** ③ 연결 단계까지 간다. */
async function openLineageUntouched(sources: UploadSources) {
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
  await click(stepBtn('③'));
  await screen.findByTestId('lin-step');
}

/** 후보 하나를 골라 **확인**까지 — 그 순간 확정 부모 1건이 된다. */
async function confirmParent(datasetId: string) {
  await click(screen.getByTestId('lin-add'));
  await screen.findByTestId('lin-picker');
  await click(screen.getByTestId(`lin-pick-${datasetId}`));
  await click(screen.getByRole('button', { name: '이 데이터로 연결' }));
  // 방금 붙인 카드는 목록 끝이다 — 앞서 확인한 카드는 확인 단추가 없다.
  const confirms = screen.getAllByTestId('lin-confirm');
  await click(confirms[confirms.length - 1] as HTMLElement);
}

// ═══ ㈎ 확정 부모가 있으면 기본값이 계산값으로 선다 ═══
describe('㉱ 기본 선택값 = 계산값 추종', () => {
  // ⚠ 부모 0건 기본값이 `Lv0` 이라(카드 ⑩ ⓐ) 첫 연결은 `Lv0` 부모만 허용된다 — 자기 Lv 를
  //   넘는 부모는 고를 수 없다(PRD-09 · `ParentPicker.valid`). 그래서 확정 부모를 한 단씩 쌓아
  //   계산값이 **최대 부모 Lv ＋ 1** 로 따라가는지 잰다.
  it('부모 Lv0·Lv1 을 차례로 확인하면 기본값이 계산값 `Lv2` 로 선다 (spec §8-2 19)', async () => {
    const { sources } = fakes();
    await openLineageUntouched(sources);
    await confirmParent(LV0);
    await confirmParent(LV1);
    await click(stepBtn('①'));
    expect(levelValue()).toBe('Lv2');
  });

  it('부모 Lv0·Lv1·Lv2 를 차례로 확인하면 기본값이 계산값 `Lv3` 로 선다', async () => {
    const { sources } = fakes();
    await openLineageUntouched(sources);
    await confirmParent(LV0);
    await confirmParent(LV1);
    await confirmParent(LV2);
    await click(stepBtn('①'));
    expect(levelValue()).toBe('Lv3');
  });

  it('부모 1건(Lv0)을 확인하면 기본값이 계산값 `Lv1` 로 선다', async () => {
    const { sources } = fakes();
    await openLineageUntouched(sources);
    await confirmParent(LV0);
    await click(stepBtn('①'));
    expect(levelValue()).toBe('Lv1');
  });

  it('확인 전(대기 카드)에는 추종하지 않는다 — 확정만 센다', async () => {
    const { sources } = fakes();
    await openLineageUntouched(sources);
    await click(screen.getByTestId('lin-add'));
    await screen.findByTestId('lin-picker');
    await click(screen.getByTestId(`lin-pick-${LV0}`));
    await click(screen.getByRole('button', { name: '이 데이터로 연결' }));
    // 카드 1건이 서 있으나 `확인` 을 누르지 않았다 — 셌다면 계산값 `Lv1` 이 선다.
    expect(screen.getAllByTestId('lin-card')).toHaveLength(1);
    await click(stepBtn('①'));
    expect(levelValue()).toBe('Lv0');
  });
});

// ═══ ㈏ 부모 0건 = 계산값 `Lv0` (카드 ⑩ ⓐ) ═══
describe('㉱ 부모 0건이면 계산값 `Lv0` 이 기본값이다', () => {
  it('부모를 한 건도 연결하지 않으면 기본값이 `Lv0` 이고 불일치 줄이 0건이다', async () => {
    const { sources } = fakes();
    await openLineageUntouched(sources);
    expect(screen.queryAllByTestId('lin-card')).toHaveLength(0);
    expect(screen.queryByTestId('lin-lv-mismatch')).toBeNull();
    await click(stepBtn('①'));
    expect(levelValue()).toBe('Lv0');
  });

  it('부모 0건에서 `Lv2` 를 고르면 등록 ③ 에 불일치 줄과 사유가 선다', async () => {
    const { sources } = fakes();
    await openLineageUntouched(sources);
    await click(stepBtn('①'));
    await change(screen.getByTestId('reg-level'), 'Lv2');
    await click(stepBtn('③'));
    const notice = screen.getByTestId('lin-lv-mismatch').textContent ?? '';
    expect(notice).toBe(levelMismatchNotice(2, 0));
    expect(notice).toContain('부모가 없으면 Lv0');
  });

  it('부모 0건에서 `Lv0` 을 그대로 두면 불일치 줄이 0건이다 (대조군)', async () => {
    const { sources } = fakes();
    await openLineageUntouched(sources);
    await click(stepBtn('①'));
    await change(screen.getByTestId('reg-level'), 'Lv0');
    await click(stepBtn('③'));
    expect(screen.queryByTestId('lin-lv-mismatch')).toBeNull();
  });

  it('부모 0건 · `Lv2` 불일치 상태에서도 등록이 성공하고 고른 값이 실린다', async () => {
    const { sources, calls } = fakes();
    await openLineageUntouched(sources);
    await click(stepBtn('①'));
    await change(screen.getByTestId('reg-level'), 'Lv2');
    await click(stepBtn('②'));
    await change(screen.getByTestId('reg-name'), '부모 없음 시험');
    await change(screen.getByTestId('reg-summary'), '설명 한 줄');
    await click(stepBtn('③'));
    expect(screen.getByTestId('lin-lv-mismatch')).toBeTruthy();
    await click(screen.getByTestId('reg-done'));
    expect(calls.registered).toHaveLength(1);
    expect(calls.registered[0]?.processingLevelUserSet).toBe('Lv2');
  });
});

// ═══ ㈐ 사람이 고른 값은 덮지 않는다 (대조군) ═══
describe('㉱ 사람이 고른 뒤에는 추종을 멈춘다', () => {
  it('`Lv3` 를 직접 고른 뒤 부모(Lv0)를 확인해도 값이 `Lv3` 로 남고 불일치 줄이 선다', async () => {
    const { sources } = fakes();
    await openLineageUntouched(sources);
    await click(stepBtn('①'));
    await change(screen.getByTestId('reg-level'), 'Lv3');
    await click(stepBtn('③'));
    await confirmParent(LV0);
    expect(screen.getByTestId('lin-lv-mismatch')).toBeTruthy();
    await click(stepBtn('①'));
    expect(levelValue()).toBe('Lv3');
  });
});

// ═══ ㈑ 불일치 상태 제출 성공 회귀 (spec §8-2 20) ═══
describe('미결-2 ⓐ — 불일치는 경고만이고 등록은 성공한다', () => {
  it('불일치 줄이 뜬 상태에서 `데이터셋 만들기` 가 살아 있고 고른 값이 그대로 실려 나간다', async () => {
    const { sources, calls } = fakes();
    await openLineageUntouched(sources);
    await click(stepBtn('①'));
    await change(screen.getByTestId('reg-level'), 'Lv3');
    await click(stepBtn('③'));
    await confirmParent(LV0);
    expect(screen.getByTestId('lin-lv-mismatch')).toBeTruthy();
    expect((screen.getByTestId('reg-done') as HTMLButtonElement).disabled).toBe(false);
    await click(stepBtn('②'));
    await change(screen.getByTestId('reg-name'), '불일치 시험');
    await change(screen.getByTestId('reg-summary'), '설명 한 줄');
    await click(stepBtn('③'));
    await click(screen.getByTestId('reg-done'));
    expect(calls.registered).toHaveLength(1);
    expect(calls.registered[0]?.processingLevelUserSet).toBe('Lv3');
  });
});
