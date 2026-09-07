/**
 * WU-B7 — 3축 목록 필터 ＋ 상세 3행 (PRD-05 · PRD-06 · `R-B-2-server.md` WU-B7).
 *
 * 오라클 = 그 절의 수용 기준 중 **화면이 잴 수 있는 넷** —
 *
 *   ㈎ 카탈로그에 3축 필터 바가 있고 각 축 첫 항목이 축자 `분류 전체`·`유형 전체`·
 *      `가공 단계 전체` 다. 축마다 파수꼴 `미지정` 항목이 하나씩 있다.
 *   ㈏ 축을 고르면 질의가 `category`·`dataType`·`processingLevel` 로 나가고 **셋이 함께**
 *      실린다(AND). 파수꼴은 글자 그대로, `Lv2` 는 정수 `2` 로 나간다.
 *   ㈐ 상세 기본 정보의 **첫 세 행**이 `분류`·`유형`·`가공 단계` 이 순서이고 값이
 *      목록 필터에 넣는 문자열과 같다.
 *   ㈑ 값이 NULL 인 행은 「미지정」 ＋ 수정 진입 유도 한 줄이다(재선택을 강제하지 않는다).
 *
 * 모든 단언은 **대상 건수를 먼저 잰다** — 빈 집합 통과(green-by-skip)를 막는다.
 */
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { DatasetsPage } from '../src/routes/DatasetsPage';
import { BasicInfoGrid } from '../src/components/detail/BasicInfoGrid';
import { FIXTURE_ROWS } from '../src/components/catalog/fixture';
import { queryParams } from '../src/components/catalog/catalogSource';
import { AXIS_ALL_LABEL, AXIS_UNSET_NUDGE, UNSPECIFIED } from '../src/components/catalog/axisFilters';
import { AXES, DEFAULT_SORT } from '../src/components/catalog/types';
import type { CatalogQuery, CatalogSource } from '../src/components/catalog/types';
import { FIXTURE_DETAILS } from '../src/components/detail/fixture';
import type { DatasetBasicInfo, DatasetDetail, DatasetFile } from '../src/components/detail/types';

const DETAIL = FIXTURE_DETAILS['01JYZ9K7WQ3N8V4M2X6C5B0AA1'] as DatasetDetail;

/** 질의를 **기록만** 하는 출처. 표가 무엇을 물었는지가 이 시험의 알맹이다. */
function recordingSource() {
  const asked: CatalogQuery[] = [];
  const source: CatalogSource = {
    async list(q) {
      asked.push(q);
      return { items: FIXTURE_ROWS, totalCount: FIXTURE_ROWS.length };
    },
    async facets(q) {
      asked.push(q);
      return {
        columns: [],
        axes: AXES.map((axis) => ({ axis, values: [{ value: UNSPECIFIED, count: 1 }] })),
      };
    },
  };
  return { source, asked };
}

function renderCatalog() {
  const rec = recordingSource();
  render(
    <MemoryRouter initialEntries={['/datasets']}>
      <Routes>
        <Route path="/datasets" element={<DatasetsPage source={rec.source} />} />
      </Routes>
    </MemoryRouter>,
  );
  return rec;
}

const NO_FILES = {
  async list(): Promise<DatasetFile[]> {
    throw new Error('이 시험은 파일 목록을 부르지 않는다');
  },
};

function renderBasicInfo(patch: Partial<DatasetBasicInfo>) {
  const basicInfo = { ...(DETAIL.basicInfo as DatasetBasicInfo), ...patch };
  render(
    <BasicInfoGrid
      basicInfo={basicInfo}
      fileName={DETAIL.fileName}
      datasetId={DETAIL.datasetId}
      filesSource={NO_FILES}
    />,
  );
}

// ═══════════════════ ㈎ 필터 바 3축 ═══════════════════
describe('㈎ 3축 필터 바', () => {
  it('세 축이 이 순서로 있고 첫 항목 글자가 축자다', async () => {
    renderCatalog();
    const bar = await screen.findByTestId('axis-bar');
    const labels = within(bar)
      .getAllByRole('combobox')
      .map((el) => (el as HTMLSelectElement).getAttribute('aria-label'));
    expect(labels).toEqual(['분류', '유형', '가공 단계']);
    for (const axis of AXES) {
      const select = within(bar).getByLabelText(axis) as HTMLSelectElement;
      expect(select.options.length).toBeGreaterThan(2);
      expect(select.options[0]?.textContent).toContain(AXIS_ALL_LABEL[axis]);
    }
  });

  it('축마다 파수꼴 `미지정` 항목이 하나씩 있다', async () => {
    renderCatalog();
    const bar = await screen.findByTestId('axis-bar');
    for (const axis of AXES) {
      const select = within(bar).getByLabelText(axis) as HTMLSelectElement;
      const values = [...select.options].map((o) => o.value);
      expect(values, axis).toContain(UNSPECIFIED);
    }
  });
});

// ═══════════════════ ㈏ 고른 값이 질의로 나간다 ═══════════════════
describe('㈏ 축이 질의 파라미터가 된다', () => {
  it('세 축을 고르면 세 파라미터가 함께 실린다 (AND)', async () => {
    const rec = renderCatalog();
    const bar = await screen.findByTestId('axis-bar');
    fireEvent.change(within(bar).getByLabelText('분류'), { target: { value: '수문 인자' } });
    fireEvent.change(within(bar).getByLabelText('유형'), { target: { value: '위성자료' } });
    fireEvent.change(within(bar).getByLabelText('가공 단계'), { target: { value: 'Lv2' } });
    await waitFor(() => {
      const last = rec.asked[rec.asked.length - 1] as CatalogQuery;
      expect(last.axes).toEqual({ 분류: '수문 인자', 유형: '위성자료', '가공 단계': 'Lv2' });
    });
    const last = rec.asked[rec.asked.length - 1] as CatalogQuery;
    const params = queryParams(last);
    expect(params.category).toEqual(['수문 인자']);
    expect(params.dataType).toEqual(['위성자료']);
    // `Lv2` 는 **정수 2** 로 나간다 — 있던 파라미터를 그대로 쓴다(PRD-05 축자).
    expect(params.processingLevel).toEqual([2]);
  });

  it('파수꼴은 글자 그대로 실린다', () => {
    const q: CatalogQuery = {
      sort: DEFAULT_SORT,
      filters: {},
      axes: { 분류: UNSPECIFIED, '가공 단계': UNSPECIFIED },
    };
    const params = queryParams(q);
    expect(params.category).toEqual([UNSPECIFIED]);
    expect(params.processingLevel).toEqual([UNSPECIFIED]);
  });

  it('아무 축도 안 고르면 그 파라미터가 아예 없다', () => {
    const params = queryParams({ sort: DEFAULT_SORT, filters: {}, axes: {} });
    expect(params).not.toHaveProperty('category');
    expect(params).not.toHaveProperty('dataType');
    expect(params).not.toHaveProperty('processingLevel');
  });
});

// ═══════════════════ ㈐·㈑ 상세 3행 ═══════════════════
describe('㈐ 상세 기본 정보의 3축 3행', () => {
  it('첫 세 행이 분류·유형·가공 단계 이 순서다', () => {
    renderBasicInfo({});
    const keys = screen.getAllByTestId('ig-k').map((el) => el.textContent);
    expect(keys.length).toBeGreaterThanOrEqual(3);
    expect(keys.slice(0, 3)).toEqual(['분류', '유형', '가공 단계']);
  });

  it('값이 목록 필터에 넣는 문자열과 같다', () => {
    renderBasicInfo({ category: '수문 인자', dataType: '위성자료', processingLevelUserSet: 'Lv2' });
    expect(within(screen.getByTestId('ig-분류')).getByText('수문 인자')).toBeTruthy();
    expect(within(screen.getByTestId('ig-유형')).getByText('위성자료')).toBeTruthy();
    expect(within(screen.getByTestId('ig-가공 단계')).getByText('Lv2')).toBeTruthy();
  });

  it('㈑ NULL 이면 「미지정」 ＋ 수정 진입 유도 한 줄이다', () => {
    renderBasicInfo({ category: null, dataType: null, processingLevelUserSet: null });
    for (const axis of AXES) {
      const cell = screen.getByTestId(`ig-${axis}`);
      expect(within(cell).getByText(UNSPECIFIED), axis).toBeTruthy();
      expect(screen.getByTestId(`ig-unset-${axis}`).textContent).toBe(AXIS_UNSET_NUDGE);
    }
  });

  it('값이 있는 축에는 유도 줄이 붙지 않는다', () => {
    renderBasicInfo({ category: '수문 인자', dataType: null, processingLevelUserSet: null });
    expect(screen.queryByTestId('ig-unset-분류')).toBeNull();
    expect(screen.getByTestId('ig-unset-유형')).toBeTruthy();
  });
});
