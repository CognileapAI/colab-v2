/**
 * WU-A14 · 조각 수 표기 (PRD-38) — **회귀 방어선**.
 *
 * 실측 결과 하드코드는 **0건**이다(상세 `format.ts:41` 이 `files.count`, 목록 3곳이 행의
 * `fileCount`). 고칠 것이 없으므로 이 파일은 **고침이 아니라 방어선**이다 — 같은 화면을
 * 고치는 후속 WU 가 조각 수의 출처를 화면 상수·`files.length`·목업 잔재로 갈아끼우면
 * 여기서 red 가 난다.
 *
 * 오라클 = `R-A-4-verify.md §B-2` 수용 기준 3줄. `files.count`(＝`d3_dataset.file_count`)
 * 하나가 상세와 목록의 유일한 출처다.
 */
import { render, screen, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { DatasetsPage } from '../src/routes/DatasetsPage';
import { FIXTURE_DETAILS, fixtureDetailSource } from '../src/components/detail/fixture';
import { FIXTURE_ROWS, fixtureCatalogSource } from '../src/components/catalog/fixture';

/** 조각 4개 — 상세·목록이 같은 데이터셋을 가리킨다 */
const MULTI_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA1';
/** 조각 1개 — `nakdong_DEM_10m.tif` */
const SINGLE_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA3';

function renderDetail(datasetId: string) {
  return render(
    <MemoryRouter initialEntries={[`/datasets/${datasetId}`]}>
      <Routes>
        <Route path="/datasets/:datasetId" element={<DatasetDetailPage source={fixtureDetailSource()} />} />
        <Route path="/datasets" element={<div>카탈로그</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

function renderCatalog() {
  return render(
    <MemoryRouter initialEntries={['/datasets']}>
      <Routes>
        <Route path="/datasets" element={<DatasetsPage source={fixtureCatalogSource()} />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('WU-A14 — 조각 수의 출처는 응답 `files.count` 한 곳이다', () => {
  it('조각 1개면 상세 `파일` 칸에 **다른 수가 보이지 않는다** — 4 도, 조각 N 개도 없다', async () => {
    expect(FIXTURE_DETAILS[SINGLE_ID]!.basicInfo!.files.count).toBe(1);
    renderDetail(SINGLE_ID);
    await screen.findByRole('heading', { level: 1, name: 'nakdong_DEM_10m.tif' });
    const cell = screen.getByTestId('ig-파일');
    // 정본 §5 — 한 건이면 파일명과 용량을 그대로 쓴다. 지어낸 조각 수를 세우지 않는다.
    expect(cell.textContent).not.toMatch(/조각\s*\d/);
    // 목업 잔재(`조각 4개`)가 되살아나면 여기서 잡힌다
    expect(cell.textContent).not.toContain('4');
  });

  it('조각 4개면 상세 표기가 `files.count` 그대로다', async () => {
    const count = FIXTURE_DETAILS[MULTI_ID]!.basicInfo!.files.count;
    expect(count).toBe(4);
    renderDetail(MULTI_ID);
    await screen.findByRole('heading', { level: 1, name: '낙동강 유역 강우 (2025)' });
    expect(screen.getByTestId('ig-파일')).toHaveTextContent(`조각 ${count}개 · 합계 148 MB`);
  });

  it('목록 칩의 수도 같은 값이다 — 상세와 목록이 갈리지 않는다', async () => {
    const detailCount = FIXTURE_DETAILS[MULTI_ID]!.basicInfo!.files.count;
    const rowCount = FIXTURE_ROWS.find((r) => r.datasetId === MULTI_ID)!.fileCount;
    expect(rowCount).toBe(detailCount);
    renderCatalog();
    await screen.findByText('nakdong_precip_2025_Lv2.nc');
    const cell = screen.getByText('nakdong_precip_2025_Lv2.nc').closest('td')!;
    expect(within(cell).getByText(`조각 ${rowCount}`)).toBeInTheDocument();
  });
});
