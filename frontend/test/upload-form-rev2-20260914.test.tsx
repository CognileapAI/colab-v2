/**
 * 업로드 모달 우측 등록 폼 — 기획서 rev2 ＋ 기획자 2026-09-13 구두 피드백.
 *
 * 오라클 = `업로드_계보_260905_rev2.html` 우측 폼 축자 ＋ 그 파일의 `makeDataset()` 검증 순서.
 *
 *   ㈎ `주제` 칸이 없다 — 폼·요청 본문 양쪽에서.
 *   ㈏ 필수/선택 표시는 **배지 하나**로 통일한다 — 라벨 텍스트의 `(선택)` 괄호가 사라진다.
 *   ㈐ 관측 간격 단위 표시 라벨이 `연·월·일·시간·분·초` 다(저장값은 무변).
 *   ㈑ 원천 블록 = 제목 `원천 · 연구실 밖 출처` · 칸 `출처 이름`/`출처 주소`/`내려받은 날` ·
 *      **Lv0 이거나 연결 0건일 때만** 보이고, Lv0 이면 `출처 주소`·`내려받은 날` 이 필수다.
 *   ㈒ `데이터셋 만들기` 검증이 한 곳에 모여 순서대로 돈다 — 첫 실패에 토스트 ＋ 단계 이동.
 *
 * ⚠ **판정 충돌 처리(사용자 결정 2026-09-14)** — 종전 PRD 판정(미결-4 ⓐ 「관측 간격은 선택」 ·
 *    미결-11 ⓐ 「원천 표기는 Lv 무관 상시 노출」 · PRD-19 「Lv0 두 칸은 선택 입력」)은 기획자
 *    9/13 구두 피드백을 새 근거로 갈아탔다. Ted 재판정은 **병합 조건**이고 구현 조건이 아니다.
 *
 * 모든 단언은 **대상 건수를 먼저 잰다** — 빈 집합 통과(green-by-skip)를 막는다.
 */
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { SessionProvider } from '../src/permission/session';
import { UploadEntry } from '../src/components/upload/UploadEntry';
import {
  INTERVAL_UNITS,
  INTERVAL_UNIT_LABEL,
  LV0,
  SOURCE_BLOCK_TITLE,
} from '../src/components/upload/RegisterArea';
import {
  REGISTER_NAME_REQUIRED,
  REGISTER_PERIOD_REQUIRED,
  REGISTER_SUMMARY_REQUIRED,
} from '../src/components/common/toastCopy';
import type {
  LineageSource,
  LineageSuggestionResponse,
  ParentCard,
} from '../src/components/lineage/types';
import type {
  LineageStepContext,
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

function fakes() {
  const calls: { registered: Record<string, unknown>[] } = { registered: [] };
  const files = [
    {
      fileId: FILE_ID,
      fileName: 'nakdong_precip_2025_Lv2.nc',
      kind: '본체',
      byteSize: 349_000,
      createdAt: '2026-09-14T00:00:00Z',
    },
  ];
  const upload: UploadSource = {
    async create() {
      return { uploadId: UPLOAD_ID, files } as never;
    },
    async status() {
      return {
        uploadId: UPLOAD_ID,
        ready: true,
        failure: null,
        metadataComplete: true,
        files,
      } as never;
    },
    async register(body: Record<string, unknown>) {
      calls.registered.push(body);
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

/** ③ 슬롯을 가짜로 바꿔 **연결 건수를 시험이 직접 쥔다** — 실제 계보 화면은 이 레인 밖이다. */
interface Mounted {
  ctx: () => LineageStepContext;
}

function mount(sources: UploadSources): Mounted {
  let seen: LineageStepContext | null = null;
  render(
    <MemoryRouter initialEntries={['/datasets']}>
      <SessionProvider account={account()}>
        <UploadEntry
          sources={sources}
          lineageStep={(c) => {
            seen = c;
            return <div data-testid="fake-lineage">③ 자리</div>;
          }}
        />
      </SessionProvider>
    </MemoryRouter>,
  );
  return { ctx: () => seen as unknown as LineageStepContext };
}

const stepBtn = (n: '①' | '②' | '③') => screen.getByRole('button', { name: new RegExp(`^${n}`) });

async function openRegister(sources: UploadSources): Promise<Mounted> {
  const m = mount(sources);
  await click(screen.getByTestId('gnb-upload'));
  await screen.findByTestId('upload-modal');
  fireEvent.change(screen.getByTestId('up-drop-input'), { target: { files: [makeFile()] } });
  await act(async () => {});
  await screen.findByTestId('up-files');
  await click(await screen.findByTestId('reg-open'));
  await screen.findByTestId('reg-steps');
  return m;
}

/** 달력 팝오버로 기간 시작을 채운다 — 기간을 받는 유일한 길이다. */
async function setPeriod(start = '2025-06-01') {
  await click(stepBtn('②'));
  await click(screen.getByTestId('reg-period-open'));
  await click(screen.getByTestId('reg-period-unit-일'));
  const [year, month, day] = start.split('-');
  await change(screen.getByTestId('reg-period-pop-start-year'), year!);
  await change(screen.getByTestId('reg-period-pop-start-month'), month!);
  await change(screen.getByTestId('reg-period-pop-start-day'), day!);
  await click(screen.getByTestId('reg-period-apply'));
}

/** 필수 다섯(이름은 파일명에서 기본값) 을 다 채운 상태 — 검증 순서 시험의 기준선이다. */
async function fillRequired() {
  await click(stepBtn('②'));
  await change(screen.getByTestId('reg-summary'), '시험용 설명 한 줄');
  await setPeriod();
  await change(screen.getByTestId('reg-interval-value'), '1');
  await change(screen.getByTestId('reg-interval-unit'), '시');
}

async function submit() {
  await click(stepBtn('③'));
  await click(screen.getByTestId('reg-done'));
}

// ═══════════ ㈎ 주제 칸 제거 ═══════════
describe('rev2 등록 폼 — 주제 칸이 없다', () => {
  it('② 메타데이터 입력에 `주제` 셀렉트가 없다', async () => {
    const { sources } = fakes();
    await openRegister(sources);
    await click(stepBtn('②'));
    expect(screen.getByTestId('reg-s2')).toBeTruthy();
    expect(screen.queryByTestId('reg-topic')).toBeNull();
    expect(document.querySelectorAll('label[for="reg-topic"]')).toHaveLength(0);
  });

  it('등록 요청 본문에 `topic` 열쇠 자체가 없다', async () => {
    const { sources, calls } = fakes();
    await openRegister(sources);
    await fillRequired();
    await submit();
    await waitFor(() => expect(calls.registered).toHaveLength(1));
    expect('topic' in (calls.registered[0] as Record<string, unknown>)).toBe(false);
  });
});

// ═══════════ ㈏ 필수/선택 배지 한 벌 ═══════════
describe('rev2 등록 폼 — 필수/선택 표시는 배지 하나로 통일한다', () => {
  it('② 의 라벨 텍스트에 `(선택)` 괄호가 남아 있지 않다', async () => {
    const { sources } = fakes();
    await openRegister(sources);
    await click(stepBtn('②'));
    const labels = Array.from(screen.getByTestId('reg-s2').querySelectorAll('label'));
    expect(labels.length).toBeGreaterThan(5);
    for (const l of labels) expect(l.textContent ?? '').not.toContain('(선택)');
  });

  it('이름·기간·설명에 `필수` 배지가 선다', async () => {
    const { sources } = fakes();
    await openRegister(sources);
    await click(stepBtn('②'));
    const required = ['reg-name', 'reg-period-open', 'reg-summary'];
    expect(required).toHaveLength(3);
    for (const id of required) {
      const label = document.querySelector(`label[for="${id}"]`) as HTMLElement | null;
      expect(label).toBeTruthy();
      expect(within(label!).getByText('필수')).toBeInTheDocument();
      expect(label!.querySelectorAll('.reqtag')).toHaveLength(1);
    }
  });

  it('관측 간격·좌표계·격자 설명·공개 범위에 `선택` 배지가 선다', async () => {
    const { sources } = fakes();
    await openRegister(sources);
    await click(stepBtn('②'));
    const optional = ['reg-interval-value', 'reg-crs', 'reg-grid-description', 'reg-visibility'];
    expect(optional).toHaveLength(4);
    for (const id of optional) {
      const label = document.querySelector(`label[for="${id}"]`) as HTMLElement | null;
      expect(label).toBeTruthy();
      expect(within(label!).getByText('선택')).toBeInTheDocument();
      expect(label!.querySelectorAll('.opttag')).toHaveLength(1);
    }
  });

  it('① 분류 세 축은 종전대로 `필수` 배지다', async () => {
    const { sources } = fakes();
    await openRegister(sources);
    await click(stepBtn('①'));
    const s1 = screen.getByTestId('reg-s1');
    expect(s1.querySelectorAll('.reqtag')).toHaveLength(3);
  });
});

// ═══════════ ㈐ 관측 간격 단위 표시 라벨 ═══════════
describe('rev2 등록 폼 — 관측 간격 단위 라벨', () => {
  it('표시 라벨이 `연·월·일·시간·분·초` 이고 **저장값은 무변**이다', async () => {
    const { sources } = fakes();
    await openRegister(sources);
    await click(stepBtn('②'));
    const sel = screen.getByTestId('reg-interval-unit') as HTMLSelectElement;
    const real = Array.from(sel.options).filter((o) => o.value !== '');
    expect(real).toHaveLength(INTERVAL_UNITS.length);
    // 저장값 = 종전 그대로(계약·DB 무변).
    expect(real.map((o) => o.value)).toEqual(['초', '분', '시', '일', '월', '년']);
    // 표시 라벨 = 기획서 축자.
    expect(real.map((o) => o.textContent)).toEqual(['초', '분', '시간', '일', '월', '연']);
    expect(INTERVAL_UNIT_LABEL['시']).toBe('시간');
    expect(INTERVAL_UNIT_LABEL['년']).toBe('연');
  });
});

// ═══════════ ㈑ 원천 블록 ═══════════
describe('rev2 등록 폼 — 원천 블록', () => {
  it('제목이 `원천 · 연구실 밖 출처` 이고 라벨이 `출처 이름` 이다', async () => {
    const { sources } = fakes();
    await openRegister(sources);
    await click(stepBtn('③'));
    const block = screen.getByTestId('reg-source-block');
    expect(within(block).getByTestId('reg-source-block-title').textContent).toContain(
      SOURCE_BLOCK_TITLE,
    );
    expect(SOURCE_BLOCK_TITLE).toBe('원천 · 연구실 밖 출처');
    const label = document.querySelector('label[for="reg-source"]') as HTMLElement | null;
    expect(label).toBeTruthy();
    expect(label!.textContent).toContain('출처 이름');
    expect(label!.textContent).not.toContain('원천 표기');
  });

  it('Lv2 · 연결 0건이면 블록이 보이고 `출처 주소` 는 있으나 `내려받은 날` 은 없다', async () => {
    const { sources } = fakes();
    await openRegister(sources);
    await change(screen.getByTestId('reg-level'), 'Lv2');
    await click(stepBtn('③'));
    expect(screen.getByTestId('reg-source-block')).toBeTruthy();
    expect(screen.getByTestId('reg-source-url')).toBeTruthy();
    expect(screen.queryByTestId('reg-source-downloaded-on')).toBeNull();
    // 연결 0건이라 필수 배지는 서지 않는다.
    expect(screen.getByTestId('reg-source-block').querySelectorAll('.reqtag')).toHaveLength(0);
  });

  it('Lv0 이면 `출처 주소`·`내려받은 날` 두 칸에 `선택` 배지가 선다', async () => {
    const { sources } = fakes();
    await openRegister(sources);
    await click(stepBtn('①'));
    await change(screen.getByTestId('reg-level'), LV0);
    await click(stepBtn('③'));
    const block = screen.getByTestId('reg-source-block');
    expect(within(block).getByTestId('reg-source-url')).toBeTruthy();
    expect(within(block).getByTestId('reg-source-downloaded-on')).toBeTruthy();
    expect(block.querySelectorAll('.opttag')).toHaveLength(2);
    for (const id of ['reg-source-url', 'reg-source-downloaded-on']) {
      const label = document.querySelector(`label[for="${id}"]`) as HTMLElement | null;
      expect(label).toBeTruthy();
      expect(within(label!).getByText('선택')).toBeInTheDocument();
    }
  });

  it('기본 Lv0을 유지한 채 같은 단계 부모를 연결하면 원천 블록과 적어 둔 값을 유지한다', async () => {
    const { sources, calls } = fakes();
    const m = await openRegister(sources);
    await click(stepBtn('③'));
    await change(screen.getByTestId('reg-source'), 'ERA5 · 유럽중기예보센터');
    await change(screen.getByTestId('reg-source-url'), 'https://example.org/era5');
    // 계보 화면이 부모 1건을 붙인다 — 그 순간 원천은 부모 쪽 계보가 말한다.
    const parent: ParentCard = {
      key: 'k1',
      parentDatasetId: '01JYZ9K7WQ3N8V4M2X6C5B0PA1',
      parentDatasetName: '부모 데이터셋',
      confidence: null,
      rationale: null,
      origin: 'manual',
      confirmed: true,
      method: '절단',
      confirmedMethodText: null,
      picking: false,
      parentLevel: 0,
    };
    await act(async () => {
      m.ctx().onParentsChange([parent]);
    });
    expect(screen.getByTestId('reg-source-block')).toBeTruthy();
    expect(screen.getByTestId('reg-source')).toHaveValue('ERA5 · 유럽중기예보센터');

    await fillRequired();
    await submit();
    await waitFor(() => expect(calls.registered).toHaveLength(1));
    const body = calls.registered[0] as Record<string, unknown>;
    expect(body.sourceLabel).toBe('ERA5 · 유럽중기예보센터');
    expect(body.sourceUrl).toBe('https://example.org/era5');
  });

  it('Lv1을 고른 뒤 유효한 부모를 연결하면 원천 블록이 사라지고 적어 둔 값이 전송되지 않는다', async () => {
    const { sources, calls } = fakes();
    const m = await openRegister(sources);
    await click(stepBtn('①'));
    await change(screen.getByTestId('reg-level'), 'Lv1');
    await click(stepBtn('③'));
    await change(screen.getByTestId('reg-source'), 'ERA5 · 유럽중기예보센터');
    await change(screen.getByTestId('reg-source-url'), 'https://example.org/era5');
    await act(async () => {
      m.ctx().onParentsChange([{
        key: 'k2', parentDatasetId: '01JYZ9K7WQ3N8V4M2X6C5B0PA2',
        parentDatasetName: 'Lv0 부모', confidence: null, rationale: null,
        origin: 'manual', confirmed: true, method: '절단', confirmedMethodText: null,
        picking: false, parentLevel: 0,
      }]);
    });
    expect(screen.queryByTestId('reg-source-block')).toBeNull();
    await fillRequired();
    await submit();
    await waitFor(() => expect(calls.registered).toHaveLength(1));
    const body = calls.registered[0] as Record<string, unknown>;
    expect(body.sourceLabel).toBeNull();
    expect('sourceUrl' in body).toBe(false);
  });
});

// ═══════════ ㈒ 한 곳에 모인 검증 — 순서 · 토스트 · 단계 이동 ═══════════
describe('rev2 등록 폼 — `데이터셋 만들기` 검증 순서', () => {
  it('이름이 비면 첫 실패로 잡히고 토스트 ＋ ② 로 옮긴다', async () => {
    const { sources, calls } = fakes();
    await openRegister(sources);
    await fillRequired();
    await change(screen.getByTestId('reg-name'), '');
    await submit();
    expect(screen.getByTestId('up-register-toast')).toHaveTextContent(REGISTER_NAME_REQUIRED);
    expect(stepBtn('②')).toHaveAttribute('aria-current', 'step');
    expect(calls.registered).toHaveLength(0);
  });

  it('설명이 비면 두 번째로 잡힌다', async () => {
    const { sources, calls } = fakes();
    await openRegister(sources);
    await fillRequired();
    await change(screen.getByTestId('reg-summary'), '');
    await submit();
    expect(screen.getByTestId('up-register-toast')).toHaveTextContent(REGISTER_SUMMARY_REQUIRED);
    expect(stepBtn('②')).toHaveAttribute('aria-current', 'step');
    expect(calls.registered).toHaveLength(0);
  });

  it('기간 시작을 안 고르면 세 번째로 잡힌다', async () => {
    const { sources, calls } = fakes();
    await openRegister(sources);
    await click(stepBtn('②'));
    await change(screen.getByTestId('reg-summary'), '시험용 설명 한 줄');
    await change(screen.getByTestId('reg-interval-value'), '1');
    await change(screen.getByTestId('reg-interval-unit'), '시');
    await submit();
    expect(screen.getByTestId('up-register-toast')).toHaveTextContent(REGISTER_PERIOD_REQUIRED);
    expect(stepBtn('②')).toHaveAttribute('aria-current', 'step');
    expect(calls.registered).toHaveLength(0);
  });

  it('관측 간격을 비워도 등록되고 요청에서 선택 필드가 빠진다', async () => {
    const { sources, calls } = fakes();
    await openRegister(sources);
    await click(stepBtn('②'));
    await change(screen.getByTestId('reg-summary'), '시험용 설명 한 줄');
    await setPeriod();
    await submit();
    await waitFor(() => expect(calls.registered).toHaveLength(1));
    expect('observationInterval' in (calls.registered[0] as Record<string, unknown>)).toBe(false);
  });

  it('Lv0 출처 주소·내려받은 날을 비워도 등록되고 요청에서 두 선택 필드가 빠진다', async () => {
    const { sources, calls } = fakes();
    await openRegister(sources);
    await fillRequired();
    await submit();
    await waitFor(() => expect(calls.registered).toHaveLength(1));
    const body = calls.registered[0] as Record<string, unknown>;
    expect(body.processingLevelUserSet).toBe(LV0);
    expect('sourceUrl' in body).toBe(false);
    expect('sourceDownloadedOn' in body).toBe(false);
  });

  it('필수를 다 채우면 등록이 성립하고 기간·관측 간격이 계약 형상으로 실린다', async () => {
    const { sources, calls } = fakes();
    await openRegister(sources);
    await fillRequired();
    await submit();
    await waitFor(() => expect(calls.registered).toHaveLength(1));
    const body = calls.registered[0] as Record<string, unknown>;
    expect(body.period).toEqual({
      start: '2025-06-01T00:00:00Z',
      end: '2025-06-01T00:00:00Z',
      granularity: '일',
    });
    expect(body.observationInterval).toEqual({ value: 1, unit: '시' });
    expect(screen.queryByTestId('up-register-toast')).toBeNull();
  });
});
