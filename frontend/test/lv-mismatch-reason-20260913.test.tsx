/**
 * R-LTH-REVIEW-1 Task 3 — 불일치 한 줄이 **각 값의 근거**를 말한다 (spec §6 ㉲ · §8-2 21).
 *
 * 오라클 = intent `2026-09-13-lth-processing-level-mismatch.md` 검증 가능 문장 ⑴ —
 * 「두 값 ＋ 각 값의 근거(사람이 고른 값 / 부모 최대 Lv＋1)를 함께 말한다.
 *   상세와 등록 두 자리가 **같은 문장**을 쓴다.」
 *
 * 판정 수단 = ⑴ 두 자리의 `textContent` 가 **글자까지 같다** ⑵ 근거 구절이 둘 다에 있다
 *            ⑶ 문장 생성이 공용 함수 하나다(`components/common/processingLevel.ts`).
 * green-by-skip 방지 = 두 자리를 **같은 Lv 쌍**으로 세우고, 불일치가 없는 대조군에서
 *            두 자리 모두 줄이 0건임을 함께 잰다(§8-6 ⑶).
 */
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { SessionProvider } from '../src/permission/session';
import { UploadEntry } from '../src/components/upload/UploadEntry';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { FIXTURE_DETAILS } from '../src/components/detail/fixture';
import { levelMismatchNotice } from '../src/components/common/processingLevel';
import type { DatasetDetail, DetailSource } from '../src/components/detail/types';
import type { DatasetRow, LineageSource, LineageSuggestionResponse } from '../src/components/lineage/types';
import type { PreviewSource, ProjectSource, UploadSource, UploadSources } from '../src/components/upload/types';
import type { CurrentAccount, Schemas } from '../src/api/client';

const UPLOAD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0UP1';
const FILE_ID = '01JYZ9K7WQ3N8V4M2X6C5B0FI1';
const LV0 = '01JYZ9K7WQ3N8V4M2X6C5B0D00';
const OPEN_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA1';
const BASE = FIXTURE_DETAILS[OPEN_ID] as DatasetDetail;

function account(): CurrentAccount {
  return {
    accountId: '01JYZ9K7WQ3N8V4M2X6C5B0AC1',
    name: '호랑이',
    email: 'tiger@example.ac.kr',
    role: '연구원',
    labId: BASE.labId,
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

const ALL = [row(LV0, '원자료 강우', 0)];

function fakes() {
  const files = [{ fileId: FILE_ID, fileName: 'nakdong_precip_2025_Lv2.nc', kind: '본체',
                   byteSize: 349_000, createdAt: '2026-09-13T00:00:00Z' }];
  const upload = {
    async create() { return { uploadId: UPLOAD_ID, files } as never; },
    async status() {
      return { uploadId: UPLOAD_ID, ready: true, failure: null, metadataComplete: true, files } as never;
    },
    async register() { return { datasetId: '01JYZ9K7WQ3N8V4M2X6C5B0DS1' } as never; },
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
    async candidates() { return ALL; },
  };
  return { upload, preview, projects, lineage } as unknown as UploadSources;
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

/**
 * 등록 ③ 에서 **사람 Lv3 · 부모 Lv0(파생 Lv1)** 불일치를 세운다.
 * 상세 쪽 장면과 **같은 Lv 쌍**이라 두 문장을 글자로 견줄 수 있다.
 */
async function registerNotice(): Promise<string> {
  render(
    <MemoryRouter initialEntries={['/datasets']}>
      <SessionProvider account={account()}>
        <UploadEntry sources={fakes()} />
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
  await change(screen.getByTestId('reg-level'), 'Lv3');
  await click(stepBtn('③'));
  await screen.findByTestId('lin-step');
  await click(screen.getByTestId('lin-add'));
  await screen.findByTestId('lin-picker');
  await click(screen.getByTestId(`lin-pick-${LV0}`));
  await click(screen.getByRole('button', { name: '이 데이터로 연결' }));
  return screen.getByTestId('lin-lv-mismatch').textContent ?? '';
}

function detailWith(mismatch: boolean): DatasetDetail {
  return {
    ...BASE,
    basicInfo: {
      ...BASE.basicInfo!,
      processingLevelUserSet: 'Lv3',
      processingLevelDerived: 1,
      processingLevelMismatch: mismatch,
    },
  } as DatasetDetail;
}

async function mountDetail(detail: DatasetDetail) {
  const source: DetailSource = { async get() { return detail; } };
  render(
    <MemoryRouter initialEntries={[`/datasets/${OPEN_ID}`]}>
      <SessionProvider account={account()}>
        <Routes>
          <Route path="/datasets/:datasetId" element={<DatasetDetailPage source={source} />} />
          <Route path="/datasets" element={<div>카탈로그</div>} />
        </Routes>
      </SessionProvider>
    </MemoryRouter>,
  );
  await screen.findByRole('heading', { level: 1, name: detail.name });
  await act(async () => {});
}

// ═══ ㈎ 두 자리가 같은 문장을 쓴다 ═══
describe('㉲ 사유 한 줄 — 상세와 등록이 한 문장이다', () => {
  it('등록 ③ 과 상세 헤더의 불일치 줄이 **글자까지 같다**', async () => {
    const inRegister = await registerNotice();
    cleanup();
    await mountDetail(detailWith(true));
    const inDetail = screen.getByTestId('dh-lv-mismatch').textContent ?? '';
    expect(inRegister.length).toBeGreaterThan(0);
    expect(inDetail).toBe(inRegister);
  });

  it('두 값 ＋ **각 값의 근거**를 함께 말한다', async () => {
    const inRegister = await registerNotice();
    // 두 값
    expect(inRegister).toContain('Lv3');
    expect(inRegister).toContain('Lv1');
    // 각 값의 근거
    expect(inRegister).toContain('사람이 고른 값');
    expect(inRegister).toContain('주입력 부모 중 최대 Lv＋1');
    // 「경고만」 문면은 유지된다
    expect(inRegister).toContain('그대로 두어도 등록돼요.');
  });

  it('문장 생성은 공용 함수 하나다 — 두 화면이 그 함수 출력과 같다', async () => {
    const shared = levelMismatchNotice(3, 1);
    const inRegister = await registerNotice();
    expect(inRegister).toBe(shared);
    cleanup();
    await mountDetail(detailWith(true));
    expect(screen.getByTestId('dh-lv-mismatch').textContent).toBe(shared);
  });
});

// ═══ 부모 0건 = 계산값 `Lv0` (카드 ⑩ ⓐ) — 상세도 같은 규칙이다 ═══
describe('㉲ 부모 0건 상세 — 계산값 `Lv0` 과 다르면 사유 줄이 선다', () => {
  it('사람 `Lv2` · 파생 `Lv0`(부모 0건) 상세에 공용 함수 문장이 그대로 선다', async () => {
    await mountDetail({
      ...BASE,
      basicInfo: {
        ...BASE.basicInfo!,
        processingLevelUserSet: 'Lv2',
        processingLevelDerived: 0,
        processingLevelMismatch: true,
      },
    } as DatasetDetail);
    const inDetail = screen.getByTestId('dh-lv-mismatch').textContent ?? '';
    expect(inDetail).toBe(levelMismatchNotice(2, 0));
    expect(inDetail).toContain('부모가 없으면 Lv0');
  });
});

// ═══ ㈏ 대조군 — 불일치가 아니면 두 자리 모두 0건 ═══
describe('㉲ 대조군 — 불일치가 아니면 줄이 서지 않는다', () => {
  it('`processingLevelMismatch=false` 상세에는 사유 줄이 0건이다', async () => {
    await mountDetail(detailWith(false));
    expect(screen.queryByTestId('dh-lv-mismatch')).toBeNull();
  });
});
