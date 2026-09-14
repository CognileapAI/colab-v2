/**
 * L4 · 소속 데이터셋 0건 — R-LTH-REVIEW-1 Task 4 (SUMMARY §3 `I-6`).
 *
 * 오라클 = 라운드 파일 `Task 4` 목적 ⑵ · spec `§8-2` 15 · `§8-6` ⑶(대조군).
 * 잰다 = ⑴ 0행에서 「연결된 데이터셋이 없어요」 ＋ 연결 방법 한 줄이 표 안에 선다
 *        ⑵ 0행에서 좌우 이동 안내(`table-scroll-hint`)와 스크롤 영역이 없다
 *        ⑶ 1건 대조군에서는 안내와 스크롤 영역이 그대로 선다.
 * 연결 방법 문장의 경로는 화면 실측으로 정했다 — 데이터셋을 프로젝트에 담는 자리는
 * 등록 `③ 연결` 의 `연관 프로젝트·논문` 하나다(`upload/RegisterArea.tsx` 앵커 `STEP_LABELS`
 * ＋ 앵커 `<h3>연관 프로젝트·논문</h3>`). 데이터셋 상세 편집 칸에는 그 자리가 없다.
 */
import { render, screen, within } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ProjectDatasetTable } from '../src/components/project/ProjectDatasetTable';
import { FIXTURE_PROJECTS } from '../src/components/project/fixture';
import type { ProjectDatasetRow } from '../src/components/project/types';

const ONE: ProjectDatasetRow = FIXTURE_PROJECTS[0]!.datasets[0]!;

function renderTable(rows: ProjectDatasetRow[]) {
  return render(
    <ProjectDatasetTable
      rows={rows}
      canManage
      onOpen={vi.fn()}
      onUnlink={vi.fn(async () => undefined)}
    />,
  );
}

describe('§5 소속 데이터셋 표 — 0건이면 다음 행동을 말한다 (`I-6`)', () => {
  it('0건이면 표 안에 빈 상태 한 칸이 서고 연결 방법을 말한다', () => {
    renderTable([]);

    const table = screen.getByTestId('project-datasets');
    const empty = within(table).getByTestId('pds-empty');
    expect(empty.textContent).toContain('연결된 데이터셋이 없어요');
    // 다음 행동 — 실제로 담을 수 있는 자리 하나를 그대로 말한다.
    expect(empty.textContent).toContain('연관 프로젝트·논문');
    // 열 여섯을 한 칸으로 잇는다 (선례 `CatalogTable.tsx` 앵커 `<td colSpan={9} className="empty">`).
    expect(empty.getAttribute('colspan')).toBe('6');
  });

  it('0건에는 좌우 이동 안내도 스크롤 영역도 세우지 않는다', () => {
    const { container } = renderTable([]);

    expect(container.querySelectorAll('.table-scroll-hint')).toHaveLength(0);
    expect(screen.queryByRole('region', { name: '소속 데이터셋 표' })).toBeNull();
  });

  it('1건 대조군에서는 안내와 스크롤 영역이 그대로 선다 (`§8-6` ⑶)', () => {
    const { container } = renderTable([ONE]);

    expect(container.querySelectorAll('.table-scroll-hint')).toHaveLength(1);
    expect(screen.getByRole('region', { name: '소속 데이터셋 표' })).toBeInTheDocument();
    expect(screen.queryByTestId('pds-empty')).toBeNull();
    expect(screen.getByTestId(`pds-${ONE.datasetId}`)).toBeInTheDocument();
  });
});
