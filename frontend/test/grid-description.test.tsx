import { render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { BasicInfoGrid } from '../src/components/detail/BasicInfoGrid';
import { applyDraft, toDraft, toPatch } from '../src/components/detail/editFields';
import { FIXTURE_DETAILS } from '../src/components/detail/fixture';
import type { DatasetDetail } from '../src/components/detail/types';

const ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA1';
const BASE = FIXTURE_DETAILS[ID] as DatasetDetail;

function detail(human: string | null, automatic: string | null): DatasetDetail {
  return {
    ...BASE,
    basicInfo: {
      ...BASE.basicInfo!,
      grid: automatic,
      gridDescription: human,
      gridDescriptionAutomatic: automatic,
    },
  };
}

describe('사람 격자 설명 저장과 표시', () => {
  it('수정 초안에 사람 값을 열고 바뀐 값만 patch하며 빈 값은 null로 보낸다', () => {
    const base = detail('250m 정방 격자', '2881 × 2305 자동 판독');
    const draft = toDraft(base);
    expect(draft.gridDescription).toBe('250m 정방 격자');
    expect(toPatch(base, draft)).toEqual({});
    expect(toPatch(base, { ...draft, gridDescription: '  ' })).toEqual({ gridDescription: null });
    expect(toPatch(base, { ...draft, gridDescription: '유역 맞춤 격자' })).toEqual({
      gridDescription: '유역 맞춤 격자',
    });
  });

  it('낙관 갱신은 사람 값만 바꾸고 자동 판독 값을 보존한다', () => {
    const base = detail('250m 정방 격자', '2881 × 2305 자동 판독');
    const next = applyDraft(base, { ...toDraft(base), gridDescription: '유역 맞춤 격자' });
    expect(next.basicInfo?.gridDescription).toBe('유역 맞춤 격자');
    expect(next.basicInfo?.gridDescriptionAutomatic).toBe('2881 × 2305 자동 판독');
  });

  it('사람 설명을 주값으로, 자동 판독을 보조로 보이고 사람 값을 지우면 자동값이 본문으로 복귀한다', () => {
    const source = { list: async () => [] };
    const view = render(
      <BasicInfoGrid basicInfo={detail('250m 정방 격자', '2881 × 2305 자동 판독').basicInfo!}
        fileName={null} datasetId={ID} filesSource={source} />,
    );
    const cell = screen.getByTestId('ig-격자');
    expect(within(cell).getByTestId('ig-grid-human')).toHaveTextContent('250m 정방 격자');
    expect(within(cell).getByTestId('ig-grid-automatic')).toHaveTextContent(
      '자동 판독: 2881 × 2305 자동 판독',
    );

    view.rerender(
      <BasicInfoGrid basicInfo={detail(null, '2881 × 2305 자동 판독').basicInfo!}
        fileName={null} datasetId={ID} filesSource={source} />,
    );
    expect(screen.getByTestId('ig-grid-human')).toHaveTextContent('2881 × 2305 자동 판독');
    expect(screen.queryByTestId('ig-grid-automatic')).toBeNull();
  });
});
