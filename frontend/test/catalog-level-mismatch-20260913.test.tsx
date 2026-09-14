/**
 * R-LTH-REVIEW-1 Task 5 — 목록 가공 단계 칸의 **불일치 표식** (spec §6 ㉳ · red 선행 18).
 *
 * 오라클 = 판정 카드 ⑩ 목록 표식 축자 「목록 가공 단계 칸이 `row.processingLevelMismatch`
 * 를 읽어 표식 ＋ 보조기기용 이름을 그린다」. **서버 무변** — 열쇠는 이미 목록 응답에
 * 실려 온다(`routes/catalog.py` 앵커 `**d3_catalog.level_view(core, summary),`).
 *
 * ⛔ 표식은 **알림이지 차단이 아니다** — 정렬·조건은 한 글자도 바뀌지 않는다
 *   (`d3_catalog.level_view` 독스트링 축자 「불일치는 경고 신호이지 차단이 아니다」).
 * ⛔ **대조군 없이 통과시키지 않는다** — `false` 행에 0건을 같은 시험에서 센다(§8-6 ⑶).
 */
import { render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import { CatalogTable } from '../src/components/catalog/CatalogTable';
import { useCatalog } from '../src/components/catalog/useCatalog';
import { FIXTURE_ROWS, fixtureCatalogSource } from '../src/components/catalog/fixture';
import type { DatasetRow } from '../src/components/catalog/types';

const MISMATCH_NAME = 'nakdong_precip_2025_Lv2.nc';
const MATCH_NAME = 'GK2A_rain_202506_Lv0.HDF5';

/** 있는 픽스처 행에 열쇠 하나만 얹는다 — 행을 지어내지 않는다. */
function withFlag(name: string, mismatch: boolean): DatasetRow {
  const base = FIXTURE_ROWS.find((r) => r.name === name) as DatasetRow;
  expect(base).toBeTruthy();
  return { ...base, processingLevelMismatch: mismatch } as DatasetRow;
}

function Harness(props: { rows: DatasetRow[] }) {
  const state = useCatalog(fixtureCatalogSource(props.rows));
  return (
    <CatalogTable state={state} uploaderNames={new Map()} onOpen={() => {}} onDownload={() => {}} />
  );
}

/** 이름이 적힌 칸을 품은 데이터 행 — 정렬 순서에 기대지 않는다. */
function rowOf(name: string): HTMLElement {
  const row = screen
    .getAllByRole('row')
    .find((r) => within(r).queryByText(name) !== null);
  expect(row).toBeTruthy();
  return row as HTMLElement;
}

async function renderBoth() {
  render(
    <MemoryRouter>
      <Harness rows={[withFlag(MISMATCH_NAME, true), withFlag(MATCH_NAME, false)]} />
    </MemoryRouter>,
  );
  await waitFor(() => expect(screen.getAllByRole('row').length).toBe(3)); // 머리줄 1 ＋ 데이터 2
}

describe('spec §6 ㉳ — 목록 가공 단계 칸의 불일치 표식', () => {
  it('불일치 행에 표식이 서고 보조기기용 이름이 붙는다', async () => {
    await renderBoth();
    const mark = within(rowOf(MISMATCH_NAME)).getByTestId('lvl-mismatch');
    expect(mark.textContent?.trim()).toBe('계산값과 다름');
    // 보조기기용 이름 — 글자 넉 자만으로는 「무엇이 다른지」가 표 밖에서 읽히지 않는다.
    expect(mark.getAttribute('aria-label') ?? '').toContain('가공 단계');
  });

  it('일치 행에는 표식이 0건이다 (대조군)', async () => {
    await renderBoth();
    expect(within(rowOf(MATCH_NAME)).queryAllByTestId('lvl-mismatch').length).toBe(0);
    expect(screen.getAllByTestId('lvl-mismatch').length).toBe(1);
  });

  it('표식은 알림이다 — Lv 칩은 두 행 모두 그대로 선다', async () => {
    await renderBoth();
    // 표식이 뜬 행도 자기 Lv 를 잃지 않는다 — 값과 알림은 별개다.
    expect(rowOf(MISMATCH_NAME).querySelector('.lvl')?.textContent).toMatch(/^Lv\d$/);
    expect(rowOf(MATCH_NAME).querySelector('.lvl')?.textContent).toMatch(/^Lv\d$/);
  });

  it('열쇠가 없는 행(종전 응답)에도 표식이 없다', async () => {
    const base = FIXTURE_ROWS.find((r) => r.name === MISMATCH_NAME) as DatasetRow;
    render(
      <MemoryRouter>
        <Harness rows={[base]} />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getAllByRole('row').length).toBe(2));
    expect(screen.queryAllByTestId('lvl-mismatch').length).toBe(0);
  });
});
