/**
 * WU-B3 · 등록 3단계 재구성 ＋ 값 안내 (PRD-12 · 04 · 13 · 33 · 40 ＋ R-A′ 이관 6건).
 *
 * 오라클 = `dev-package/prd/rounds/R-B-3-frontend.md §2` WU-B3 의 **수용 기준 요구 본체 11건**
 * ＋ **R-A′ 이관 ㈎㈏㈐㈑㈒**. ㈓(공개 범위 값 재동기)는 값 칸이 WU-B4 몫이라 이 파일이 재지 않는다.
 *
 * 모든 단언은 **대상 건수를 먼저 잰다** — 빈 집합 통과(green-by-skip)를 막는다.
 */
import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { SessionProvider } from '../src/permission/session';
import { UploadEntry } from '../src/components/upload/UploadEntry';
import { ESC_LAYER_ATTR } from '../src/components/upload/UploadModal';
import { PERIOD_SINGLE_POINT_HINT, STEP_LABELS } from '../src/components/upload/RegisterArea';
import { MISSING_CATEGORY_MESSAGE } from '../src/components/upload/axisDict';
import {
  CATEGORIES,
  DATA_TYPES,
  DEFAULT_CATEGORY,
  DEFAULT_DATA_TYPE,
  DEFAULT_PROCESSING_LEVEL,
  PROCESSING_LEVELS,
  bilingual,
} from '../src/components/upload/axisDict';
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

const stepBtn = (n: '①' | '②' | '③') =>
  screen.getByRole('button', { name: new RegExp(`^${n}`) });

// ═══ 요구 본체 ①~⑥ — 단계 구성과 이동 규칙 (PRD-12 · rev1 UI-003 · PRD-13) ═══
describe('PRD-12 등록 3단계 재구성', () => {
  it('① 표시기 세 라벨이 `① 분류 · ② 메타데이터 입력 · ③ 연결` 이고 ① 이 열려 있다', async () => {
    const { sources } = fakes();
    await openRegister(sources);
    const steps = within(screen.getByTestId('reg-steps')).getAllByRole('button');
    expect(steps).toHaveLength(3);
    expect(steps.map((b) => b.textContent)).toEqual([
      '① 분류',
      '② 메타데이터 입력',
      '③ 연결',
    ]);
    expect(STEP_LABELS[1]).toBe('① 분류');
    expect(screen.getByTestId('reg-s1')).toBeTruthy();
    expect(screen.queryByTestId('reg-s2')).toBeNull();
  });

  it('② 분류·유형 중 하나가 비면 `다음` 이 막힌다 (가공 단계는 기본값 Lv2 라 빈 상태가 없다)', async () => {
    const { sources } = fakes();
    await openRegister(sources);
    const next = screen.getByTestId('reg-next') as HTMLButtonElement;
    expect(next.disabled).toBe(false);
    await change(screen.getByTestId('reg-category'), '');
    expect((screen.getByTestId('reg-next') as HTMLButtonElement).disabled).toBe(true);
    await change(screen.getByTestId('reg-category'), DEFAULT_CATEGORY);
    await change(screen.getByTestId('reg-datatype'), '');
    expect((screen.getByTestId('reg-next') as HTMLButtonElement).disabled).toBe(true);
    // 가공 단계에는 빈 선택지가 없다 — 기본값 `Lv2` 가 늘 서 있다.
    const lvOptions = within(screen.getByTestId('reg-level')).getAllByRole('option');
    expect(lvOptions).toHaveLength(PROCESSING_LEVELS.length);
    expect(lvOptions.some((o) => (o as HTMLOptionElement).value === '')).toBe(false);
  });

  it('③ ③ 진입 시 계보 카드와 연관 프로젝트·논문 카드가 같은 단계 안에 있다', async () => {
    const { sources } = fakes();
    await openRegister(sources);
    await click(stepBtn('③'));
    const s3 = await screen.findByTestId('reg-s3');
    expect(within(s3).getByTestId('reg-lineage-slot')).toBeTruthy();
    expect(within(s3).getByTestId('reg-projects')).toBeTruthy();
    expect(within(s3).getByTestId('reg-source')).toBeTruthy();
  });

  it('④ ③ 에서 표시기 ① 을 누르면 조건 없이 ① 로 간다', async () => {
    const { sources } = fakes();
    await openRegister(sources);
    await click(stepBtn('③'));
    await screen.findByTestId('reg-s3');
    await click(stepBtn('①'));
    expect(screen.getByTestId('reg-s1')).toBeTruthy();
  });

  it('⑤ 이름·설명이 빈 채여도 표시기 ③ 은 조건 없이 간다 (rev1 UI-003)', async () => {
    const { sources } = fakes();
    await openRegister(sources);
    await click(stepBtn('②'));
    expect((screen.getByTestId('reg-name') as HTMLInputElement).value).not.toBe('');
    await change(screen.getByTestId('reg-name'), '');
    await change(screen.getByTestId('reg-summary'), '');
    await click(stepBtn('③'));
    expect(screen.getByTestId('reg-s3')).toBeTruthy();
  });

  it('⑥ ③ 까지 갔다가 닫고 다시 열면 ① 분류다 (PRD-13)', async () => {
    const { sources } = fakes();
    await openRegister(sources);
    await click(stepBtn('③'));
    await screen.findByTestId('reg-s3');
    await click(screen.getByTestId('upload-close'));
    await click(screen.getByTestId('gnb-upload'));
    await screen.findByTestId('upload-modal');
    await dropOne();
    await click(await screen.findByTestId('reg-open'));
    expect(await screen.findByTestId('reg-s1')).toBeTruthy();
  });
});

// ═══ 요구 본체 ⑦~⑪ — 값 사전 15값과 PRD-33 힌트 ═══════════════════════════
describe('PRD-04 · PRD-33 값 안내', () => {
  it('⑦ 15값(5+6+4) 전부 정의·예시 한 줄이고 빈 정의가 0 이다', async () => {
    const { sources } = fakes();
    await openRegister(sources);
    expect(CATEGORIES.length + DATA_TYPES.length + PROCESSING_LEVELS.length).toBe(15);
    let seen = 0;
    for (const v of CATEGORIES) {
      await change(screen.getByTestId('reg-category'), v.value);
      const line = screen.getByTestId('reg-category-def');
      expect(line.textContent).toContain(v.def);
      expect(line.textContent).toContain(`예: ${v.example}`);
      expect(v.def.trim()).not.toBe('');
      seen += 1;
    }
    for (const v of DATA_TYPES) {
      await change(screen.getByTestId('reg-datatype'), v.value);
      const line = screen.getByTestId('reg-datatype-def');
      expect(line.textContent).toContain(v.def);
      expect(line.textContent).toContain(`예: ${v.example}`);
      seen += 1;
    }
    for (const v of PROCESSING_LEVELS) {
      await change(screen.getByTestId('reg-level'), v.value);
      const line = screen.getByTestId('reg-level-def');
      expect(line.textContent).toContain(v.def);
      expect(line.textContent).toContain(`예: ${v.example}`);
      seen += 1;
    }
    expect(seen).toBe(15);
  });

  it('⑪ 15값 전부 부가 문구가 빈 값이 0 이다', () => {
    const all = [...CATEGORIES, ...DATA_TYPES, ...PROCESSING_LEVELS];
    expect(all).toHaveLength(15);
    const empty = all.filter((v) => v.extra.trim() === '');
    expect(empty).toHaveLength(0);
  });

  it('⑧ 유형 `위성자료` 를 고르면 정의 줄 아래에 `참고 · 해상도, 궤도 정보 명시 필요` 가 읽힌다', async () => {
    const { sources } = fakes();
    await openRegister(sources);
    await change(screen.getByTestId('reg-datatype'), '위성자료');
    expect(screen.getByTestId('reg-datatype-note').textContent).toBe(
      '참고 · 해상도, 궤도 정보 명시 필요',
    );
  });

  it('⑧b `필요` 어조 3종(위성·수치모형·합성)이 그대로 보인다 (PRD-33 ⑶)', async () => {
    const { sources } = fakes();
    await openRegister(sources);
    const cases: [string, string][] = [
      ['위성자료', '해상도, 궤도 정보 명시 필요'],
      ['수치모형자료', '초기조건 및 설정 파라미터 기재 필요'],
      ['합성자료', '생성 방식, 융합 기법의 상세 설명 필요'],
    ];
    expect(cases).toHaveLength(3);
    for (const [type, text] of cases) {
      await change(screen.getByTestId('reg-datatype'), type);
      expect(screen.getByTestId('reg-datatype-note').textContent).toBe(`참고 · ${text}`);
    }
  });

  it('⑨ 분류 `수문 인자` ＋ `Lv1` 이면 ② 설명 칸 힌트에 두 항목이 함께 보인다', async () => {
    const { sources } = fakes();
    await openRegister(sources);
    await change(screen.getByTestId('reg-category'), '수문 인자');
    await change(screen.getByTestId('reg-level'), 'Lv1');
    await click(stepBtn('②'));
    const hint = await screen.findByTestId('reg-summary-hint');
    expect(hint.textContent).toContain('유역코드, 관측 해상도');
    expect(hint.textContent).toContain('보간방법, 좌표계 유형');
  });

  it('⑩ 가공 단계 `Lv0` 이면 힌트에 `출처(Source URL), 다운로드 일자` 가 없다', async () => {
    const { sources } = fakes();
    await openRegister(sources);
    await change(screen.getByTestId('reg-level'), 'Lv0');
    await click(stepBtn('②'));
    const hint = await screen.findByTestId('reg-summary-hint');
    expect(hint.textContent).not.toContain('출처(Source URL), 다운로드 일자');
  });

  it('기본 선택값 3개와 국문＋영문 병기 표기 (미결-13 ⓐ)', async () => {
    const { sources } = fakes();
    await openRegister(sources);
    expect((screen.getByTestId('reg-category') as HTMLSelectElement).value).toBe(DEFAULT_CATEGORY);
    expect((screen.getByTestId('reg-datatype') as HTMLSelectElement).value).toBe(DEFAULT_DATA_TYPE);
    expect((screen.getByTestId('reg-level') as HTMLSelectElement).value).toBe(
      DEFAULT_PROCESSING_LEVEL,
    );
    // 표시는 병기, 저장은 국문 단일.
    const opt = within(screen.getByTestId('reg-datatype')).getByRole('option', {
      name: '재분석자료 (Reanalysis Data)',
    }) as HTMLOptionElement;
    expect(opt.value).toBe('재분석자료');
    expect(bilingual(DATA_TYPES[2]!)).toBe('재분석자료 (Reanalysis Data)');
  });

  it('카드 부제 두 줄이 rev1 축자다', async () => {
    const { sources } = fakes();
    await openRegister(sources);
    expect(screen.getByTestId('reg-s1-sub').textContent).toBe(
      '목록 필터가 이 세 축을 그대로 받아요',
    );
    await click(stepBtn('②'));
    expect(screen.getByTestId('reg-s2-sub').textContent).toBe(
      '파일에서 읽는 값은 확장자·용량뿐이에요',
    );
  });

  it('세 축의 기본값이 등록 요청에 실린다 (계약 required 승격의 짝)', async () => {
    const { sources, calls } = fakes();
    await openRegister(sources);
    await click(stepBtn('②'));
    await change(screen.getByTestId('reg-summary'), '시험용 설명 한 줄');
    await click(stepBtn('③'));
    await click(screen.getByTestId('reg-done'));
    expect(calls.registered).toHaveLength(1);
    const body = calls.registered[0]!;
    expect(body.category).toBe(DEFAULT_CATEGORY);
    expect(body.dataType).toBe(DEFAULT_DATA_TYPE);
    expect(body.processingLevelUserSet).toBe(DEFAULT_PROCESSING_LEVEL);
  });
});

// ═══ R-A′ 이관 ㈎ 확장보기 오버레이 ══════════════════════════════════════
describe('㈎ 확장보기 오버레이', () => {
  it('열려 있는 동안 `data-esc-layer="확장보기"` 표식이 붙는다', async () => {
    const { sources } = fakes();
    await openModal(sources);
    await dropOne();
    await click(await screen.findByTestId('pv-expand'));
    const layer = await screen.findByTestId('pv-expand-overlay');
    expect(layer.getAttribute(ESC_LAYER_ATTR)).toBe('확장보기');
    expect(document.querySelectorAll(`[${ESC_LAYER_ATTR}="확장보기"]`)).toHaveLength(1);
  });

  it('배경 클릭으로 닫히고 내부 클릭은 무동작이다 (mousedown/click 분리)', async () => {
    const { sources } = fakes();
    await openModal(sources);
    await dropOne();
    await click(await screen.findByTestId('pv-expand'));
    const back = await screen.findByTestId('pv-expand-overlay');
    const inner = within(back).getByTestId('pv-expand-body');
    // 내부에서 눌러 배경에서 뗀 드래그는 닫지 않는다.
    fireEvent.mouseDown(inner);
    fireEvent.click(back);
    await act(async () => {});
    expect(screen.queryByTestId('pv-expand-overlay')).not.toBeNull();
    // 배경에서 누르고 배경에서 떼면 닫힌다.
    fireEvent.mouseDown(back);
    fireEvent.click(back);
    await act(async () => {});
    expect(screen.queryByTestId('pv-expand-overlay')).toBeNull();
  });

  // ⭑ ⟨advisor ② · F2⟩ A9R 규율의 세 갈래(배경 · × · Esc)에서 Esc 가 빠져 있었다.
  it('Esc 로 확장보기만 닫히고 업로드 모달은 남는다', async () => {
    const { sources } = fakes();
    await openModal(sources);
    await dropOne();
    await click(await screen.findByTestId('pv-expand'));
    await screen.findByTestId('pv-expand-overlay');
    fireEvent.keyDown(document, { key: 'Escape' });
    await act(async () => {});
    expect(screen.queryByTestId('pv-expand-overlay')).toBeNull();
    expect(screen.queryByTestId('upload-modal')).not.toBeNull();
    expect(screen.queryByTestId('upload-close-confirm')).toBeNull();
  });

  it('확장보기가 떠 있는 동안 Esc 가 업로드 모달을 닫지 않는다', async () => {
    const { sources } = fakes();
    await openModal(sources);
    await dropOne();
    await click(await screen.findByTestId('pv-expand'));
    await screen.findByTestId('pv-expand-overlay');
    fireEvent.keyDown(document, { key: 'Escape' });
    await act(async () => {});
    expect(screen.queryByTestId('upload-modal')).not.toBeNull();
  });
});

// ═══ R-A′ 이관 ㈏ 기간 달력 팝오버 ═══════════════════════════════════════
describe('㈏ 기간 달력 팝오버 (PRD-18)', () => {
  it('팝오버가 열리고 고른 최소 단위까지만 칸이 열린다', async () => {
    const { sources } = fakes();
    await openRegister(sources);
    await click(stepBtn('②'));
    expect(screen.queryByTestId('reg-period-pop')).toBeNull();
    await click(screen.getByTestId('reg-period-open'));
    const pop = await screen.findByTestId('reg-period-pop');
    // 단위 6값이 다 서 있다.
    const units = within(pop).getAllByTestId(/^reg-period-unit-/);
    expect(units).toHaveLength(6);
    // `일` 이면 시각 칸이 없다.
    await click(within(pop).getByTestId('reg-period-unit-일'));
    expect(within(screen.getByTestId('reg-period-pop')).queryByTestId('reg-period-time-start'))
      .toBeNull();
    // `분` 이면 시각 칸이 선다.
    await click(within(screen.getByTestId('reg-period-pop')).getByTestId('reg-period-unit-분'));
    expect(
      within(screen.getByTestId('reg-period-pop')).getByTestId('reg-period-time-start'),
    ).toBeTruthy();
  });

  // ⭑ ⟨advisor ② · F2⟩ 팝오버도 Esc 층이다 — 표식이 없으면 Esc 가 업로드 모달까지 내려간다.
  it('Esc 로 팝오버만 닫히고 업로드 모달은 남는다', async () => {
    const { sources } = fakes();
    await openRegister(sources);
    await click(stepBtn('②'));
    await click(screen.getByTestId('reg-period-open'));
    const pop = await screen.findByTestId('reg-period-pop');
    expect(pop.getAttribute(ESC_LAYER_ATTR)).toBe('기간');
    fireEvent.keyDown(document, { key: 'Escape' });
    await act(async () => {});
    expect(screen.queryByTestId('reg-period-pop')).toBeNull();
    expect(screen.queryByTestId('upload-modal')).not.toBeNull();
    expect(screen.queryByTestId('upload-close-confirm')).toBeNull();
  });

  it('달력에서 날을 골라 적용하면 기간 값이 선다', async () => {
    const { sources } = fakes();
    await openRegister(sources);
    await click(stepBtn('②'));
    await click(screen.getByTestId('reg-period-open'));
    const pop = await screen.findByTestId('reg-period-pop');
    await click(within(pop).getByTestId('reg-period-unit-일'));
    const days = within(screen.getByTestId('reg-period-pop')).getAllByTestId(/^reg-period-day-/);
    expect(days.length).toBeGreaterThan(27);
    await click(days[0]!);
    await click(within(screen.getByTestId('reg-period-pop')).getByTestId('reg-period-apply'));
    expect((screen.getByTestId('reg-period-start-year') as HTMLInputElement).value).not.toBe('');
  });
});

// ═══ R-A′ 이관 ㈑ 모달 2장면 ═════════════════════════════════════════════
describe('㈑ 모달 2장면', () => {
  it('파일 0건이면 등록 폼·미리보기가 DOM 에 없다', async () => {
    const { sources } = fakes();
    await openModal(sources);
    expect(screen.queryByTestId('up-split')).toBeNull();
    expect(screen.queryByTestId('reg-area')).toBeNull();
    expect(screen.queryByTestId('up-split-preview')).toBeNull();
    expect(screen.getByTestId('up-drop-input')).toBeTruthy();
  });

  it('파일 1건이면 장면2 — 좌 미리보기 ＋ 우 ① 분류이고 존치 3종이 도달 가능하다', async () => {
    const { sources } = fakes();
    await openRegister(sources);
    expect(screen.getByTestId('up-split-preview')).toBeTruthy();
    expect(screen.getByTestId('reg-s1')).toBeTruthy();
    // 존치 — 2단 등록 게이트 · 기준 격자 첨부 자리(파일 종류를 `기준 격자 파일` 로 바꾸는 칸).
    expect(screen.getByTestId('reg-gate')).toBeTruthy();
    const kinds = within(screen.getByTestId('up-file-kind')).getAllByRole('option');
    expect(kinds.map((o) => (o as HTMLOptionElement).value)).toContain('기준 격자 파일');
  });

  // ⭑ ⟨advisor ② · F6⟩ 라운드 ㈑ 문면 3종 중 미검증분 — 이어올리기 배너에서 장면2 도달.
  it('이어올리기 배너에서 파일을 다시 놓으면 장면2 로 간다', async () => {
    const { sources } = fakes();
    (sources.upload as unknown as { incomplete: () => Promise<unknown[]> }).incomplete =
      async () => [
        {
          uploadId: UPLOAD_ID,
          sourceLabel: 'nakdong_precip_2025_Lv2.nc',
          uploadedFiles: 1,
          plannedFiles: 2,
          uploadedBytes: 100,
          plannedBytes: 349_000,
          createdAt: '2026-09-07T00:00:00Z',
          expiresAt: '2026-09-14T00:00:00Z',
        },
      ];
    await openModal(sources);
    // 장면1 — 배너만 서 있고 등록 폼·미리보기는 아직 DOM 에 없다.
    const banner = await screen.findByTestId('up-incomplete');
    expect(within(banner).getByTestId(`up-resume-${UPLOAD_ID}`)).toBeTruthy();
    expect(screen.queryByTestId('up-split')).toBeNull();
    await click(screen.getByTestId(`up-resume-${UPLOAD_ID}`));
    expect(screen.getByTestId('up-resume-hint')).toBeTruthy();
    // 안내대로 같은 파일을 다시 놓으면 장면2 다.
    await dropOne();
    expect(screen.getByTestId('up-split')).toBeTruthy();
    expect(screen.getByTestId('up-split-preview')).toBeTruthy();
    await click(await screen.findByTestId('reg-open'));
    expect(await screen.findByTestId('reg-s1')).toBeTruthy();
  });

  it('파일 배지 `×` 를 누르면 장면1 로 돌아가고 초기화 고지가 뜬다', async () => {
    const { sources } = fakes();
    await openRegister(sources);
    await click(screen.getByRole('button', { name: /빼기$/ }));
    expect(screen.queryByTestId('up-split')).toBeNull();
    expect(screen.getByTestId('up-removed-toast')).toBeTruthy();
  });
});

// ═══ R-A′ 이관 ㈒ PRD-40 종료 비움 ═══════════════════════════════════════
describe('㈒ PRD-40 종료 비움', () => {
  it('종료 칸에 `한 시점이면 비워 둬요` 안내가 서고 필수 표시가 없다', async () => {
    const { sources } = fakes();
    await openRegister(sources);
    await click(stepBtn('②'));
    const hint = await screen.findByTestId('reg-period-single-hint');
    expect(hint.textContent).toBe(PERIOD_SINGLE_POINT_HINT);
    expect(PERIOD_SINGLE_POINT_HINT).toBe('한 시점이면 비워 둬요');
  });

  it('시작만 적고 종료를 비우면 `period_end = period_start` 로 실린다', async () => {
    const { sources, calls } = fakes();
    await openRegister(sources);
    await click(stepBtn('②'));
    await change(screen.getByTestId('reg-summary'), '시험용 설명 한 줄');
    await change(screen.getByTestId('reg-period-start'), '2020-06-01');
    await click(stepBtn('③'));
    await click(screen.getByTestId('reg-done'));
    expect(calls.registered).toHaveLength(1);
    const period = calls.registered[0]!.period as { start: string; end: string | null };
    expect(period.start).toBe('2020-06-01T00:00:00Z');
    expect(period.end).toBe('2020-06-01T00:00:00Z');
  });
});

// ═══ ⭑ ⟨advisor ② · F3⟩ 최종 게이트 — 분류·유형이 비면 ① 로 되돌린다 ══════════
describe('advisor ② F3 — 등록 최종 게이트', () => {
  it('분류를 비운 채 `데이터셋 만들기` 를 누르면 ① 로 가고 서버와 같은 문면이 선다', async () => {
    const { sources, calls } = fakes();
    await openRegister(sources);
    await change(screen.getByTestId('reg-category'), '');
    await click(stepBtn('②'));
    await change(screen.getByTestId('reg-summary'), '시험용 설명 한 줄');
    await click(stepBtn('③'));
    await click(screen.getByTestId('reg-done'));
    // 서버까지 가지 않는다 — 화면이 먼저 판정한다.
    expect(calls.registered).toHaveLength(0);
    // 적을 칸이 있는 단계로 데려간다 (이름·설명 경로와 같은 규율).
    expect(screen.getByTestId('reg-s1')).toBeTruthy();
    expect(document.activeElement).toBe(screen.getByTestId('reg-category'));
    expect(screen.getByTestId('reg-area').textContent).toContain(MISSING_CATEGORY_MESSAGE);
    expect(MISSING_CATEGORY_MESSAGE).toBe('분류를 골라 주세요');
  });
});

// ═══ WU-B4 · PRD-11 — ② 부가 정보의 공개 범위 셀렉트 (B3 이 세운 자리를 채운다) ═══
//
// 이 자리는 `reg-visibility-slot` 이고 WU-B3 이 **라벨만** 세워 뒀다. WU-B4 가 값을 채우면서
// 그 슬롯이 실물 셀렉트가 됐다 — 그래서 오라클도 이 파일에 붙는다(같은 화면·같은 harness).
describe('WU-B4 · PRD-11 공개 범위 3값', () => {
  it('② 부가 정보의 자리가 **3값 셀렉트**이고 표기가 rev1 축자다', async () => {
    const { sources } = fakes();
    await openRegister(sources);
    await click(stepBtn('②'));
    const slot = screen.getByTestId('reg-visibility-slot');
    const options = within(slot).getAllByRole('option');
    expect(options).toHaveLength(3);
    expect(options.map((o) => o.textContent)).toEqual([
      '연구실 구성원 전체',
      '나만 보기',
      '지정한 사람만',
    ]);
    // **저장값은 표기와 다르다** — 「열림/잠김」 어휘를 지우지 않는다(PRD-11 축자).
    expect(options.map((o) => (o as HTMLOptionElement).value)).toEqual([
      '열림',
      '잠김',
      '지정 공개',
    ]);
  });

  it('기본 선택이 `연구실 구성원 전체` 이고 고른 값의 **범위**가 한 줄로 뜬다', async () => {
    const { sources } = fakes();
    await openRegister(sources);
    await click(stepBtn('②'));
    const select = screen.getByTestId('reg-visibility') as HTMLSelectElement;
    expect(select.value).toBe('열림');
    expect(screen.getByTestId('reg-visibility-note').textContent)
      .toBe('연구실 안 누구나 뷰·다운로드');
    await change(select, '지정 공개');
    expect((screen.getByTestId('reg-visibility') as HTMLSelectElement).value).toBe('지정 공개');
    // `지정한 사람만` 은 허용 목록 0건으로 시작해 사실상 `나만 보기` 와 같다 — 그 사실이 뜬다.
    expect(screen.getByTestId('reg-visibility-note').textContent)
      .toBe('허용 목록에 오른 사람만. 만료 = 승인일 + 6개월');
  });
});
