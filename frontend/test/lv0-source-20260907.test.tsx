/**
 * WU-B6 · PRD-19 — Lv0 전용 출처 두 칸(출처 주소 · 내려받은 날).
 *
 * 오라클 = `dev-package/prd/rounds/R-B-1-db.md §2 WU-B6` **수용 기준 5건 축자**.
 *
 *   ㈎ ① 에서 Lv0 → ③ 진입 → 두 칸이 보이고 `선택` 표기가 붙는다
 *   ㈏ ① 에서 Lv1 → ③ 진입 → 두 칸이 안 보이고 **원천 표기는 그대로 보인다**(미결-11 ⓐ)
 *   ㈐ Lv0 이고 출처 주소가 빔 → `createDataset` **성공**
 *   ㈑ Lv1 인데 `sourceUrl` 을 실어 보냄 → 성공하고 값이 저장된다 → **서버 몫**
 *      (`services/core-api/tests/test_lv0_source.py`). 여기서는 **화면이 Lv1 에서 안 싣는다**를 잰다.
 *   ㈒ ③ 에서 두 칸을 채운 뒤 ① 로 돌아가 Lv2 → ③ 재진입 → 숨고 **두 값이 전송되지 않는다**
 *
 * ＋ 상세 두 건 — 파생 Lv 가 Lv0 이고 두 칸이 비면 **안내로만** 뜬다 · 수정 폼이 그 안내를
 *    실행 가능하게 만드는 두 칸을 갖는다(「수정에서 채워 주세요」).
 *
 * ⛔ ~~**폐기된 판정을 재지 않는다** — 「Lv0 이면 필수」·「Lv1 이상이면 400」은 폐기됐다(PRD-19).
 *    `필수` 배지의 **부재**를 단언하는 것이 그 폐기의 화면 쪽 회귀 시험이다.~~
 * ⭑ **⟨개정 2026-09-14 · 기획자 9/13 구두 피드백 · Ted 재판정 대기⟩ 「Lv0 이면 필수」가
 *    되살아났다.** 화면이 Lv0 에서 두 칸을 막고 `필수` 배지를 세운다. ⚠ **「Lv1 이상이면
 *    400」은 여전히 폐기된 채다** — 서버는 값이 오면 저장한다(PRD-19). 여기 판정은 화면 쪽이다.
 * ⭑ **⟨개정 2026-09-14⟩ 원천 세 칸은 한 블록이고 `Lv0` **또는** 연결 0건일 때만 선다.**
 *    ／ 종전 ~~`원천 표기` 한 칸은 Lv 무관 상시(미결-11 ⓐ)~~.
 *
 * 모든 단언은 **대상 건수를 먼저 잰다** — 빈 집합 통과(green-by-skip)를 막는다.
 */
import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { SessionProvider } from '../src/permission/session';
import { UploadEntry } from '../src/components/upload/UploadEntry';
import {
  LV0,
  LV0_SOURCE_DATE_PLACEHOLDER,
  LV0_SOURCE_NOTICE,
  LV0_SOURCE_URL_PLACEHOLDER,
} from '../src/components/upload/RegisterArea';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { FIXTURE_DETAILS } from '../src/components/detail/fixture';
import { LV0_SOURCE_MISSING_NOTICE } from '../src/components/detail/format';
import { TEXT_FIELDS, toDraft, toPatch } from '../src/components/detail/editFields';
import type { DatasetDetail, DetailSource } from '../src/components/detail/types';
import type {
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
const DATASET_ID = '01JYZ9K7WQ3N8V4M2X6C5B0DS1';

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

interface Calls {
  registered: Record<string, unknown>[];
}

function fakes() {
  const calls: Calls = { registered: [] };
  const upload: UploadSource = {
    async create() {
      return {
        uploadId: UPLOAD_ID,
        files: [
          {
            fileId: FILE_ID,
            fileName: 'nakdong_precip_2025_Lv2.nc',
            kind: '본체',
            byteSize: 349_000,
            createdAt: '2026-09-07T00:00:00Z',
          },
        ],
      } as never;
    },
    async status() {
      return {
        uploadId: UPLOAD_ID,
        ready: true,
        failure: null,
        metadataComplete: true,
        files: [
          {
            fileId: FILE_ID,
            fileName: 'nakdong_precip_2025_Lv2.nc',
            kind: '본체',
            byteSize: 349_000,
            createdAt: '2026-09-07T00:00:00Z',
          },
        ],
      } as never;
    },
    async register(body: Record<string, unknown>) {
      calls.registered.push(body as unknown as Record<string, unknown>);
      return { datasetId: DATASET_ID } as never;
    },
    async attachGrid() {
      return [] as never;
    },
  } as unknown as UploadSource;
  const preview: PreviewSource = {
    async palettes() {
      return [{ palette: 'viridis', label: '비리디스' }];
    },
    async createRender() {
      return { renderId: 'r', state: '실패', failure: null } as never;
    },
    async getRender() {
      return { renderId: 'r', state: '실패', failure: null } as never;
    },
  } as unknown as PreviewSource;
  const projects: ProjectSource = {
    async list() {
      return [];
    },
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
    async candidates() {
      return [];
    },
  } as unknown as LineageSource;
  return { sources: { upload, preview, projects, lineage } as UploadSources, calls };
}

async function click(el: Element | null) {
  fireEvent.click(el as HTMLElement);
  await act(async () => {});
}

async function change(el: Element | null, value: string) {
  fireEvent.change(el as HTMLElement, { target: { value } });
  await act(async () => {});
}

function makeFile(name = 'nakdong_precip_2025_Lv2.nc') {
  const f = new File(['x'], name, { type: 'application/octet-stream' });
  Object.defineProperty(f, 'size', { value: 349_000 });
  return f;
}

async function openModal(sources: UploadSources) {
  render(
    <MemoryRouter initialEntries={['/datasets']}>
      <SessionProvider account={account()}>
        <UploadEntry sources={sources} />
      </SessionProvider>
    </MemoryRouter>,
  );
  await click(screen.getByTestId('gnb-upload'));
  await screen.findByTestId('upload-modal');
}

async function dropOne() {
  fireEvent.change(screen.getByTestId('up-drop-input'), { target: { files: [makeFile()] } });
  await act(async () => {});
  await screen.findByTestId('up-files');
}

/** 파일 1건 ＋ 등록 카드 열기까지. 등록 카드는 늘 ① 분류에서 시작한다. */
async function openRegister(sources: UploadSources) {
  await openModal(sources);
  await dropOne();
  await click(await screen.findByTestId('reg-open'));
  await screen.findByTestId('reg-steps');
}


async function goStep(n: '①' | '②' | '③') {
  await click(screen.getByRole('button', { name: new RegExp(`^${n}`) }));
}

/** ① 의 가공 단계 셀렉트를 고른다. ③ 의 블록은 이 값 하나로 열리고 닫힌다. */
async function pickLevel(value: string) {
  await goStep('①');
  await change(screen.getByTestId('reg-level'), value);
}

async function submitRegister() {
  await goStep('②');
  await change(screen.getByTestId('reg-summary'), '시험용 설명 한 줄');
  // ⭑ ⟨개정 2026-09-14⟩ 기간·관측 간격도 등록 게이트다 — 이 파일이 재는 것은 출처 두 칸이다.
  await click(screen.getByTestId('reg-period-open'));
  await click(screen.getByTestId('reg-period-unit-일'));
  await change(screen.getByTestId('reg-period-pop-start-year'), '2025');
  await change(screen.getByTestId('reg-period-pop-start-month'), '06');
  await change(screen.getByTestId('reg-period-pop-start-day'), '01');
  await click(screen.getByTestId('reg-period-apply'));
  await change(screen.getByTestId('reg-interval-value'), '1');
  await change(screen.getByTestId('reg-interval-unit'), '시');
  await goStep('③');
  await click(screen.getByTestId('reg-done'));
}

// ═══════════ 수용 기준 ㈎㈏ — 표시·숨김과 `선택` 표기 ═══════════
describe('WU-B6 · PRD-19 등록 ③ Lv0 출처 블록', () => {
  it('㈎ ① 에서 Lv0 을 고르면 ③ 에 두 칸이 보이고 **`선택` 배지**가 붙는다', async () => {
    const { sources } = fakes();
    await openRegister(sources);
    await pickLevel(LV0);
    await goStep('③');

    const source = screen.getByTestId('reg-source-block');
    // **두 칸이다.** 건수를 먼저 재 빈 집합 통과를 막는다(`출처 이름` 은 세 번째 칸이다).
    const url = within(source).getByTestId('reg-source-url') as HTMLInputElement;
    const day = within(source).getByTestId('reg-source-downloaded-on') as HTMLInputElement;
    expect(within(source).getAllByRole('textbox')).toHaveLength(3);
    expect(url.placeholder).toBe(LV0_SOURCE_URL_PLACEHOLDER);
    expect(day.placeholder).toBe(LV0_SOURCE_DATE_PLACEHOLDER);
    expect(LV0_SOURCE_URL_PLACEHOLDER).toBe('예: https://cds.climate.copernicus.eu/...');
    expect(LV0_SOURCE_DATE_PLACEHOLDER).toBe('예: 2026-08-20');

    expect(source.querySelectorAll('.opttag')).toHaveLength(2);
    for (const id of ['reg-source-url', 'reg-source-downloaded-on']) {
      const label = document.querySelector(`label[for="${id}"]`) as HTMLElement | null;
      expect(label).toBeTruthy();
      expect(within(label!).getByText('선택')).toBeInTheDocument();
    }
    // ⛔ 괄호 문구는 남지 않는다 — 표시는 배지 하나다.
    expect(source.textContent).not.toContain('(선택)');

    // 안내 문면은 rev1 축자다.
    const block = within(source).getByTestId('reg-source-lv0');
    expect(within(block).getByTestId('reg-source-lv0-notice').textContent).toBe(LV0_SOURCE_NOTICE);
    expect(LV0_SOURCE_NOTICE).toBe('원시 데이터라 부모가 없어요. 대신 어디서 언제 받았는지를 남겨요.');
  });

  // ⭑ **⟨개정 2026-09-14⟩** ／ 종전 ~~「㈏ Lv1 이면 두 칸이 안 보이고 **원천 표기는 그대로
  //    보인다**(미결-11 ⓐ)」~~ — `출처 주소` 는 연결 0건이면 Lv1 에서도 선다. Lv 로 갈리는
  //    것은 `내려받은 날` 과 `필수` 배지뿐이다(기획서 `srcLv0`·`srcUrlReq` 축자).
  it('㈏ Lv1 · 연결 0건이면 `내려받은 날` 만 사라지고 `필수` 배지도 서지 않는다', async () => {
    const { sources } = fakes();
    await openRegister(sources);
    await pickLevel('Lv1');
    await goStep('③');

    const source = screen.getByTestId('reg-source-block');
    expect(screen.queryByTestId('reg-source-lv0')).toBeNull();
    expect(screen.queryByTestId('reg-source-downloaded-on')).toBeNull();
    // 슬롯은 남아 있고 **안이 비었다** — 「블록이 없다」와 「Lv0 이 아니다」를 가른다.
    expect(screen.getByTestId('reg-source-lv0-slot').children).toHaveLength(0);
    // 출처 이름·출처 주소는 연구실 밖 출처를 묻는 칸이라 연결 0건 동안 그대로 선다.
    expect(within(source).getByTestId('reg-source')).toBeTruthy();
    expect(within(source).getByTestId('reg-source-url')).toBeTruthy();
    expect(source.querySelectorAll('.reqtag')).toHaveLength(0);
  });

  it('㈎-b ① 에서 Lv 를 바꾸면 ③ 의 블록이 **즉시** 열리고 닫힌다', async () => {
    const { sources } = fakes();
    await openRegister(sources);
    // ⭑ ⟨카드 ⑩ ⓐ⟩ 부모 0건 기본값이 `Lv0` 이라 흐름이 한 단 늘었다 —
    //   Lv0(기본값) → 열림 → Lv2 → 닫힘 → Lv0 → 열림 → Lv3 → 닫힘.
    //   ／ 종전 ~~Lv2(기본값) → 닫힘 → Lv0 → 열림 → Lv3 → 닫힘~~
    await goStep('③');
    expect(screen.getByTestId('reg-source-lv0')).toBeTruthy();
    await pickLevel('Lv2');
    await goStep('③');
    expect(screen.queryByTestId('reg-source-lv0')).toBeNull();
    await pickLevel(LV0);
    await goStep('③');
    expect(screen.getByTestId('reg-source-lv0')).toBeTruthy();
    await pickLevel('Lv3');
    await goStep('③');
    expect(screen.queryByTestId('reg-source-lv0')).toBeNull();
    // 블록 자체는 연결 0건이라 남는다 — 갈리는 것은 `내려받은 날` 칸이다.
    expect(screen.getByTestId('reg-source-block')).toBeTruthy();
  });
});

// ═══════════ 수용 기준 ㈐㈑㈒ — 무엇이 전송되는가 ═══════════
describe('WU-B6 · PRD-19 전송 규율', () => {
  it('㈐ Lv0 이고 두 칸이 비어도 등록되고 선택 필드는 요청에서 빠진다', async () => {
    const { sources, calls } = fakes();
    await openRegister(sources);
    await pickLevel(LV0);
    await submitRegister();

    expect(calls.registered).toHaveLength(1);
    const body = calls.registered[0] as Record<string, unknown>;
    expect('sourceUrl' in body).toBe(false);
    expect('sourceDownloadedOn' in body).toBe(false);
  });

  it('㈐-b Lv0 에서 두 칸을 채우면 그 값이 그대로 실린다', async () => {
    const { sources, calls } = fakes();
    await openRegister(sources);
    await pickLevel(LV0);
    await goStep('③');
    await change(screen.getByTestId('reg-source-url'), 'https://example.org/era5');
    await change(screen.getByTestId('reg-source-downloaded-on'), '2026-08-20');
    await submitRegister();

    expect(calls.registered).toHaveLength(1);
    const body = calls.registered[0] as Record<string, unknown>;
    expect(body.sourceUrl).toBe('https://example.org/era5');
    expect(body.sourceDownloadedOn).toBe('2026-08-20');
  });

  // ⭑ **⟨개정 2026-09-14⟩ 숨는 것은 `내려받은 날` 하나다** ／ 종전 ~~「두 값이 전송되지
  //    않는다」~~ — `출처 주소` 는 연결 0건 동안 Lv2 에서도 화면에 서 있으므로 전송된다.
  //    **규율은 무변**이다 — 「보이는 동안 적은 것만 싣는다」이고, 무엇이 보이는가가 바뀌었다.
  it('㈒ 채운 뒤 ① 에서 Lv2 로 바꾸면 `내려받은 날` 만 숨고 그 값이 전송되지 않는다', async () => {
    const { sources, calls } = fakes();
    await openRegister(sources);
    await pickLevel(LV0);
    await goStep('③');
    await change(screen.getByTestId('reg-source-url'), 'https://example.org/era5');
    await change(screen.getByTestId('reg-source-downloaded-on'), '2026-08-20');
    // ① 로 돌아가 Lv2 로 바꾼다.
    await pickLevel('Lv2');
    await goStep('③');
    expect(screen.queryByTestId('reg-source-lv0')).toBeNull();
    await submitRegister();

    expect(calls.registered).toHaveLength(1);
    const body = calls.registered[0] as Record<string, unknown>;
    expect(body.processingLevelUserSet).toBe('Lv2');
    // **숨은 값은 전송되지 않는다** — 사용자가 지운 적 없는 값이 저장되면 상세에
    // 「내가 적은 적 없는 출처」가 뜬다.
    expect('sourceDownloadedOn' in body).toBe(false);
    // 보이는 칸의 값은 그대로 나간다 — 숨김과 전송이 같은 식이라는 사실의 뒷면이다.
    expect(body.sourceUrl).toBe('https://example.org/era5');
  });

  // ⭑ **⟨개정 2026-09-14⟩** ／ 종전 ~~「㈑ 화면은 Lv1 에서 두 값을 싣지 않는다」~~ —
  //    Lv1 에서 갈리는 것은 `내려받은 날` 뿐이다. 연결이 붙으면 그때 블록 전체가 사라진다
  //    (그쪽 판정은 `test/upload-form-rev2-20260914.test.tsx`).
  it('㈑ 화면은 Lv1 에서 `내려받은 날` 을 싣지 않는다 (서버는 오면 저장한다 — 서버 시험 몫)', async () => {
    const { sources, calls } = fakes();
    await openRegister(sources);
    await pickLevel(LV0);
    await goStep('③');
    await change(screen.getByTestId('reg-source-url'), 'https://example.org/era5');
    await change(screen.getByTestId('reg-source-downloaded-on'), '2026-08-20');
    await pickLevel('Lv1');
    await submitRegister();

    const body = calls.registered[0] as Record<string, unknown>;
    expect(body.processingLevelUserSet).toBe('Lv1');
    expect('sourceDownloadedOn' in body).toBe(false);
    expect(body.sourceUrl).toBe('https://example.org/era5');
  });
});

// ═══════════ 상세 — 기존 행 안내와 그 안내의 실행 경로 ═══════════
const DETAIL_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA1';
const DETAIL_BASE = FIXTURE_DETAILS[DETAIL_ID] as DatasetDetail;

function detailWith(patch: Record<string, unknown>): DatasetDetail {
  return {
    ...DETAIL_BASE,
    basicInfo: { ...DETAIL_BASE.basicInfo!, ...patch },
  } as DatasetDetail;
}

function mountDetail(detail: DatasetDetail) {
  const source: DetailSource = { async get() { return detail; } };
  return render(
    <MemoryRouter initialEntries={[`/datasets/${DETAIL_ID}`]}>
      <SessionProvider account={account()}>
        <Routes>
          <Route path="/datasets/:datasetId" element={<DatasetDetailPage source={source} />} />
          <Route path="/datasets" element={<div>카탈로그</div>} />
        </Routes>
      </SessionProvider>
    </MemoryRouter>,
  );
}

describe('WU-B6 · PRD-19 상세 — 기존 행 안내', () => {
  // ⭑ **⟨R-C · WU-C8 · R-B §5-28 판정⟩ 기준이 파생 Lv → **사람 Lv** 로 바뀌었다.**
  //   이 시험이 겨냥한 것은 backfill 되지 않은 **기존 행**이고 그 행은 사람 값이 `null`
  //   이라 파생 Lv 로 물러난다 — 재는 사실은 그대로이고, 그 「사람 값 없음」을 픽스처가
  //   이제 **명시**한다. 새 기준 자체(사람 0·파생≠0 / 사람≠0·파생 0)는 `fe-small-rc8` 이 잰다.
  it('사람 Lv 가 없고 파생 Lv 가 Lv0 이며 두 칸이 비면 **안내로만** 뜬다 (저장을 막지 않는다)', async () => {
    mountDetail(detailWith({
      processingLevelDerived: 0,
      processingLevelUserSet: null,
      sourceUrl: null,
      sourceDownloadedOn: null,
    }));
    await screen.findByTestId('basic-info');
    await act(async () => {});
    const note = screen.getByTestId('ig-lv0-source-missing');
    expect(note.textContent).toBe(LV0_SOURCE_MISSING_NOTICE);
    expect(LV0_SOURCE_MISSING_NOTICE)
      .toBe('Lv0 인데 출처 주소·내려받은 날이 비어 있어요 — 수정에서 채워 주세요');
    // ⛔ 안내는 **원천 표기 칸 안쪽**이다 — 칸 수는 아홉 그대로다.
    expect(within(screen.getByTestId('ig-원천 표기')).getByTestId('ig-lv0-source-missing')).toBeTruthy();
  });

  it('두 칸 중 하나라도 차 있으면 안내가 서지 않고 값이 그대로 보인다', async () => {
    mountDetail(detailWith({
      processingLevelDerived: 0,
      processingLevelUserSet: null,
      sourceUrl: 'https://example.org/era5',
      sourceDownloadedOn: null,
    }));
    await screen.findByTestId('basic-info');
    await act(async () => {});
    expect(screen.queryByTestId('ig-lv0-source-missing')).toBeNull();
    expect(screen.getByTestId('ig-source-url').textContent).toBe('https://example.org/era5');
  });

  it('보이는 Lv 가 Lv0 이 아니면 두 칸이 비어도 안내가 서지 않는다', async () => {
    mountDetail(detailWith({
      processingLevelDerived: 2,
      processingLevelUserSet: null,
      sourceUrl: null,
      sourceDownloadedOn: null,
    }));
    await screen.findByTestId('basic-info');
    await act(async () => {});
    expect(screen.queryByTestId('ig-lv0-source-missing')).toBeNull();
  });
});

describe('WU-B6 · PRD-19 수정 폼 — 안내가 실행 가능한가', () => {
  it('수정 폼의 텍스트 칸 표에 두 칸이 있고 `필수` 가 아니다', () => {
    const keys = TEXT_FIELDS.map((f) => f.key);
    expect(keys).toContain('sourceUrl');
    expect(keys).toContain('sourceDownloadedOn');
    const url = TEXT_FIELDS.find((f) => f.key === 'sourceUrl');
    const day = TEXT_FIELDS.find((f) => f.key === 'sourceDownloadedOn');
    expect(url?.label).toBe('출처 주소');
    expect(day?.label).toBe('내려받은 날');
    // ⛔ 두 칸은 선택 입력이다 — 목업 필수 배지를 채택하지 않는다.
    expect(url?.required).toBeFalsy();
    expect(day?.required).toBeFalsy();
  });

  it('상세의 값이 초안으로 들어오고, 고친 값만 패치에 실린다', () => {
    const detail = detailWith({
      processingLevelDerived: 0,
      sourceUrl: null,
      sourceDownloadedOn: null,
    });
    const draft = toDraft(detail);
    expect(draft.sourceUrl).toBe('');
    expect(draft.sourceDownloadedOn).toBe('');

    const patch = toPatch(detail, {
      ...draft,
      sourceUrl: 'https://example.org/era5',
      sourceDownloadedOn: '2026-08-20',
    });
    expect(patch.sourceUrl).toBe('https://example.org/era5');
    expect(patch.sourceDownloadedOn).toBe('2026-08-20');
    // 안 고친 칸은 실리지 않는다 — 부분 수정의 뜻이 안 바뀐다.
    expect('crs' in patch).toBe(false);
  });

  it('채워진 칸을 비우면 `null` 로 실린다 (「비우라」)', () => {
    const detail = detailWith({
      processingLevelDerived: 0,
      sourceUrl: 'https://example.org/era5',
      sourceDownloadedOn: '2026-08-20',
    });
    const draft = toDraft(detail);
    expect(draft.sourceUrl).toBe('https://example.org/era5');
    const patch = toPatch(detail, { ...draft, sourceUrl: '', sourceDownloadedOn: '' });
    expect(patch.sourceUrl).toBeNull();
    expect(patch.sourceDownloadedOn).toBeNull();
  });
});
