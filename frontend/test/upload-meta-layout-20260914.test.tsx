/**
 * ② 메타데이터 입력 — **레이아웃·순서·표 모양·필수 표기**를 기획서 rev2 목업에 맞춘다.
 *
 * 오라클 = `업로드_계보_260905_rev2.html` 의 `#reg-s1`(`data-regstep="2"`) 카드 본문 축자.
 * 사용자 지적(2026-09-14 · 스크린샷 대조) = 「입력 순서가 다르다 · 변수 표 형태가 기획서와
 * 다르다 · UI 형태 자체를 기획서와 동일하게」.
 *
 *   ㈎ 사람이 적는 칸의 **순서** — 이름 → 기간 → 관측 간격 → 좌표계 → 격자 → 설명 →
 *      변수 표 → 공개 범위. 목업 본문의 위→아래 순서 그대로다.
 *   ㈏ **기간은 한 행에 시작·종료 두 반쪽**이다(`.dr-field` ＋ `.dr-half` 둘).
 *      「한 시점이면 비워 둬요」는 별도 문단이 아니라 **종료 반쪽의 빈 값 표기**다.
 *   ㈐ **관측 간격·좌표계·격자가 같은 행**(`.form-3`)이다. 기간은 그 행에서 빠진다.
 *   ㈑ **격자는 한 줄 입력**이고 칸 아래 안내 문단이 없다(목업에 그 문단이 없다).
 *   ㈒ **변수는 선 있는 표**다 — 제목 한 줄 ＋ 머리행 6칸 ＋ 삭제는 `×` 글자 ＋
 *      표 **아래** `+ 변수 추가`.
 *   ㈓ **필수 표기는 라벨 옆 `필수` 글자**이고 배지 컴포넌트의 **사용처는 무변**이다.
 *
 * ⛔ **데이터 흐름은 무변이다** — 폼 상태 열쇠·요청 본문·검증 순서를 이 시험이 건드리지
 *    않는다. 그 판정은 `upload-form-rev2-20260914.test.tsx` 가 계속 진다.
 *
 * 모든 단언은 **대상 건수를 먼저 잰다** — 빈 집합 통과(green-by-skip)를 막는다.
 */
import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { SessionProvider } from '../src/permission/session';
import { UploadEntry } from '../src/components/upload/UploadEntry';
import {
  PERIOD_SINGLE_POINT_HINT,
  VARIABLES_FIELD_LABEL,
} from '../src/components/upload/RegisterArea';
import { VARIABLE_COLUMNS } from '../src/components/common/VariableTable';
import type { LineageSource, LineageSuggestionResponse } from '../src/components/lineage/types';
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

function fakes() {
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
    async register() {
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
  return { sources: { upload, preview, projects, lineage } as UploadSources };
}

async function click(el: Element | null) {
  fireEvent.click(el as HTMLElement);
  await act(async () => {});
}

function makeFile(name = 'nakdong_precip_2025_Lv2.nc') {
  const f = new File(['x'], name, { type: 'application/octet-stream' });
  Object.defineProperty(f, 'size', { value: 349_000 });
  return f;
}

const stepBtn = (n: '①' | '②' | '③') => screen.getByRole('button', { name: new RegExp(`^${n}`) });

/** ② 메타데이터 카드가 떠 있는 상태까지 연다. ③ 슬롯은 이 레인 밖이라 가짜로 바꾼다. */
async function openMeta(sources: UploadSources) {
  render(
    <MemoryRouter initialEntries={['/datasets']}>
      <SessionProvider account={account()}>
        <UploadEntry sources={sources} lineageStep={() => <div>③ 자리</div>} />
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
  await click(stepBtn('②'));
  return screen.getByTestId('reg-s2');
}

/** `a` 가 `b` 보다 문서 순서상 앞이면 참. */
const before = (a: Element, b: Element) =>
  (a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING) !== 0;

// ═══════════ ㈎ 입력 순서 ═══════════
describe('② 메타데이터 — 사람이 적는 칸의 순서가 목업 순서다', () => {
  it('이름 → 기간 → 관측 간격 → 좌표계 → 격자 → 설명 → 변수 표 → 공개 범위', async () => {
    const { sources } = fakes();
    await openMeta(sources);
    const order = [
      'reg-name',
      'reg-period-open',
      'reg-interval-value',
      'reg-crs',
      'reg-grid-description',
      'reg-summary',
      'variable-table',
      'reg-visibility',
    ];
    const nodes = order.map((id) => screen.getByTestId(id));
    expect(nodes).toHaveLength(8);
    for (let i = 0; i + 1 < nodes.length; i += 1) {
      expect([order[i], order[i + 1], before(nodes[i]!, nodes[i + 1]!)]).toEqual([
        order[i],
        order[i + 1],
        true,
      ]);
    }
  });
});

// ═══════════ ㈏ 기간 = 한 행에 두 반쪽 ═══════════
describe('② 기간 — 한 행에 시작·종료 두 칸', () => {
  it('기간 칸이 `.dr-field` 이고 그 안에 `.dr-half` 두 개가 선다', async () => {
    const { sources } = fakes();
    await openMeta(sources);
    const field = screen.getByTestId('reg-period-open');
    expect(field).toHaveClass('dr-field');
    const halves = field.querySelectorAll('.dr-half');
    expect(halves).toHaveLength(2);
    expect(within(halves[0] as HTMLElement).getByText('시작')).toBeInTheDocument();
    expect(within(halves[1] as HTMLElement).getByText('종료')).toBeInTheDocument();
  });

  it('「한 시점이면 비워 둬요」가 종료 반쪽의 빈 값 표기다 — 별도 안내 문단이 아니다', async () => {
    const { sources } = fakes();
    await openMeta(sources);
    const hint = screen.getByTestId('reg-period-single-hint');
    expect(hint.textContent).toBe(PERIOD_SINGLE_POINT_HINT);
    expect(hint.closest('.dr-half')).not.toBeNull();
    expect(hint.tagName).not.toBe('P');
  });
});

// ═══════════ ㈐ 짧은 값 한 줄 = 관측 간격·좌표계·격자 ═══════════
describe('② 짧은 값 한 줄 — 관측 간격·좌표계·격자', () => {
  it('세 칸이 같은 행이고 기간은 그 행에 없다', async () => {
    const { sources } = fakes();
    await openMeta(sources);
    const row = screen.getByTestId('reg-short-row');
    expect(row).toHaveClass('form-3');
    const inside = ['reg-interval-value', 'reg-crs', 'reg-grid-description'];
    expect(inside).toHaveLength(3);
    for (const id of inside) expect(row.contains(screen.getByTestId(id))).toBe(true);
    expect(row.contains(screen.getByTestId('reg-period-open'))).toBe(false);
  });

  it('관측 간격은 숫자 칸 ＋ 단위 셀렉트가 `.itv` 한 묶음이다', async () => {
    const { sources } = fakes();
    await openMeta(sources);
    const itv = screen.getByTestId('reg-interval-value').closest('.itv');
    expect(itv).not.toBeNull();
    expect((itv as HTMLElement).contains(screen.getByTestId('reg-interval-unit'))).toBe(true);
  });
});

// ═══════════ ㈑ 격자 = 한 줄 입력 ═══════════
describe('② 격자 — 한 줄 입력', () => {
  it('`textarea` 가 아니라 `input` 이고 라벨이 `격자` 다', async () => {
    const { sources } = fakes();
    await openMeta(sources);
    const grid = screen.getByTestId('reg-grid-description');
    expect(grid.tagName).toBe('INPUT');
    const label = document.querySelector('label[for="reg-grid-description"]');
    expect(label).not.toBeNull();
    expect((label as HTMLElement).textContent).toBe('격자선택');
  });

  it('칸 아래 안내 문단이 없다 (목업에 그 문단이 없다)', async () => {
    const { sources } = fakes();
    await openMeta(sources);
    expect(screen.getByTestId('reg-s2')).toBeTruthy();
    expect(screen.queryByText('자동 판독과 별도로 연구자가 설명을 남겨요.')).toBeNull();
  });
});

// ═══════════ ㈒ 변수 = 선 있는 표 ═══════════
describe('② 변수 — 목업 표 모양', () => {
  it('표 위에 제목 한 줄이 서고 머리행이 6칸이다', async () => {
    const { sources } = fakes();
    await openMeta(sources);
    const title = screen.getByTestId('reg-variables-label');
    expect(title).toHaveClass('fieldlbl');
    expect(title.textContent).toBe(VARIABLES_FIELD_LABEL);
    expect(before(title, screen.getByTestId('variable-table'))).toBe(true);
    const head = within(screen.getByTestId('variable-table')).getByTestId('vt-head');
    const cells = head.querySelectorAll('th');
    expect(cells).toHaveLength(VARIABLE_COLUMNS.length + 1);
    expect([...cells].slice(0, VARIABLE_COLUMNS.length).map((c) => c.textContent)).toEqual([
      ...VARIABLE_COLUMNS,
    ]);
  });

  it('삭제는 `×` 글자 버튼이고 이름은 접근성 이름으로 남는다', async () => {
    const { sources } = fakes();
    await openMeta(sources);
    const del = screen.getByTestId('vt-del-0');
    expect(del.textContent).toBe('×');
    expect(del).toHaveAccessibleName('변수 1 빼기');
  });

  it('`+ 변수 추가` 가 표 **아래**에 있다', async () => {
    const { sources } = fakes();
    await openMeta(sources);
    const table = screen.getByTestId('variable-table');
    const add = screen.getByTestId('vt-add');
    expect(before(table.querySelector('table') as Element, add)).toBe(true);
  });

  it('변수 표에 `선택` 배지를 단 라벨이 없다 — 제목 한 줄이 그 자리를 진다', async () => {
    const { sources } = fakes();
    await openMeta(sources);
    const varLabels = Array.from(document.querySelectorAll('label')).filter(
      (l) => (l.textContent ?? '').startsWith('변수') && !l.hasAttribute('for'),
    );
    expect(varLabels).toHaveLength(0);
  });
});

// ═══════════ ㈓ 필수 표기 ═══════════
describe('② 필수 표기 — 라벨 옆 `필수` 글자', () => {
  it('② 안의 `필수` 배지는 이름·기간·설명·관측 간격 네 곳이다', async () => {
    const { sources } = fakes();
    await openMeta(sources);
    const card = screen.getByTestId('reg-s2');
    expect(card.querySelectorAll('.reqtag')).toHaveLength(4);
    const owners = ['reg-name', 'reg-period-open', 'reg-summary', 'reg-interval-value'];
    expect(owners).toHaveLength(4);
    for (const id of owners) {
      const label = document.querySelector(`label[for="${id}"]`);
      expect(label).not.toBeNull();
      expect((label as HTMLElement).querySelectorAll('.reqtag')).toHaveLength(1);
      expect(within(label as HTMLElement).getByText('필수')).toBeInTheDocument();
    }
  });
});
