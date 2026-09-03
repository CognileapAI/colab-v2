/**
 * 버그 15 — 데이터셋 설명문의 전각 슬래시 `／` 를 **표시 단계에서만** 줄로 나눈다 (A안).
 *
 * 출처 = `infra/staging/manifest-s2.json` 의 시드 `summary` 12건 42개(recon C §5).
 * 그 `／` 는 원천 동봉 문서의 문단 이음매라 사람이 손으로 적은 것이고, **저장·검색은 그대로 둔다.**
 * 여기서 못 박는 것은 셋뿐이다.
 *
 *   ① 상세 헤더(`.dh-sum`) 는 첫 조각을 이끔 문장으로, 나머지를 목록 항목으로 그린다
 *   ② `／` 가 없는 설명은 **종전과 완전히 같다** — 목록을 만들지 않는다
 *   ③ 목록·검색 카드(`.hit-summary`) 는 한 줄 그대로다 — 이 회차가 건드리지 않는다
 *
 * ⚠ 정본 `Policy_데이터셋_상세 §8` 은 이 자리를 「③ 한 줄 요약」이라 부른다.
 *    여러 줄로 펼치는 것은 Ted 최종 확인 대상이고, 되돌리기는 이 커밋 하나를 되돌리면 된다.
 */
import { render, screen, within } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { DetailHeader } from '../src/components/detail/DetailHeader';
import { SearchHitCard } from '../src/components/search/SearchHitCard';
import { FIXTURE_DETAILS } from '../src/components/detail/fixture';
import type { DatasetDetail } from '../src/components/detail/types';
import type { ApprovalSource } from '../src/components/approval/types';
import type { SearchResultRow } from '../src/components/search/types';

const OPEN_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA1';

/** 시드 D-03 의 모양 그대로 — 조각 4개(`／` 3개)다. */
const SEG = [
  '저해상도(2 km) 자료를 고해상도(1 km)로 변환하는 다운스케일링.',
  'Nearest-Neighbour — 타깃 셀에 가장 가까운 원본 셀 값을 그대로 복사.',
  'GeoTIFF, EPSG:4326, 정확히 1 km (0.01°) 격자, float32.',
  '해상도 한계 — 원본 2 km 가 가진 정보 한도 안에 갇혀 있다.',
];
const MULTI = SEG.join(' ／ ');
const SINGLE = '유역 평균 강수량';

function stubApproval(): ApprovalSource {
  return {
    requestAccess: vi.fn(async () => {}),
    requestVerification: vi.fn(async () => {}),
    approveVerification: vi.fn(async () => {}),
    cancelVerification: vi.fn(async () => {}),
  };
}

function renderHeader(summary: string | null) {
  const base = FIXTURE_DETAILS[OPEN_ID] as DatasetDetail;
  const detail: DatasetDetail = { ...base, summary };
  return render(<DetailHeader detail={detail} approvalSource={stubApproval()} />);
}

describe('버그 15 · 상세 헤더 — `／` 는 표시 단계에서 줄로 나뉜다', () => {
  it('`／` 3개면 이끔 문장 1 + 목록 항목 3 이다', () => {
    renderHeader(MULTI);
    const sum = screen.getByTestId('dh-sum');
    expect(within(sum).getByTestId('dh-sum-lead')).toHaveTextContent(SEG[0] as string);
    const items = within(screen.getByTestId('dh-sum-list')).getAllByRole('listitem');
    expect(items).toHaveLength(3);
    expect(items.map((li) => li.textContent)).toEqual([SEG[1], SEG[2], SEG[3]]);
  });

  it('구분자와 그 둘레 공백은 화면에 남지 않는다', () => {
    renderHeader(MULTI);
    const sum = screen.getByTestId('dh-sum');
    expect(sum.textContent).not.toContain('／');
    for (const li of within(screen.getByTestId('dh-sum-list')).getAllByRole('listitem')) {
      expect(li.textContent).toBe((li.textContent as string).trim());
    }
  });

  it('`／` 가 없는 설명은 종전 그대로 — 목록을 만들지 않는다', () => {
    renderHeader(SINGLE);
    const sum = screen.getByTestId('dh-sum');
    expect(sum.textContent).toBe(SINGLE);
    expect(screen.queryByTestId('dh-sum-list')).toBeNull();
    expect(sum.querySelector('ul')).toBeNull();
  });

  it('설명이 비면 자리 자체가 없다 (종전 성질)', () => {
    renderHeader(null);
    expect(screen.queryByTestId('dh-sum')).toBeNull();
  });
});

describe('버그 15 · 목록·검색 카드는 한 줄 그대로다', () => {
  const row: SearchResultRow = {
    datasetId: '01JYZ9K7WQ3N8V4M2X6C5B0A01',
    name: '충청권 NDVI 다운스케일 (Nearest)',
    fileCount: 1,
    topic: '식생',
    processingLevel: 1,
    projects: { representative: null, moreCount: 0, names: [] },
    uploader: { accountId: '01JYZ9K7WQ3N8V4M2X6C5B0AHT', name: '호랑이' },
    lastModifiedAt: '2026-08-01T00:00:00Z',
    lineageState: '원천',
    lineageConfirmedAt: null,
    verified: false,
    accessState: '열림',
    bodyAccessible: true,
    relevanceBar: 1,
    rationale: '‘NDVI’가 이름에 맞았어요.',
    summary: MULTI,
    period: null,
  };

  it('검색 카드는 `／` 를 그대로 한 줄로 적는다', () => {
    render(<SearchHitCard row={row} onOpen={() => {}} />);
    const card = screen.getByTestId('hit-summary');
    expect(card.textContent).toBe(MULTI);
    expect(card.querySelector('ul')).toBeNull();
    expect(screen.queryByTestId('dh-sum-list')).toBeNull();
  });
});
