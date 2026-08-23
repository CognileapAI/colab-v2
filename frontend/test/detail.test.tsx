/**
 * S-05 데이터셋 상세 — **상단(헤더 + 기본 정보)** 정본 대비 시험.
 * 오라클 = `E-03_데이터셋_상세/documents/Policy_데이터셋_상세.md` (v2.1) 와 그 목업.
 * 계보 그래프·미리보기·활용 프로젝트는 P2·P3·P5 라 여기서 시험하지 않는다.
 * 화면 글자는 정본에서 그대로 온다 — 여기서 새 한국어 라벨을 만들지 않는다.
 */
import { render, screen, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { FIXTURE_DETAILS, fixtureDetailSource } from '../src/components/detail/fixture';
import type { DatasetDetail, DetailSource } from '../src/components/detail/types';
import { DatasetGone } from '../src/components/detail/types';

const OPEN_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA1'; // 낙동강 유역 강우 (2025) — 목업 기본 장면
const LOCKED_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA5'; // 낙동강 유역 유출량 (2025) — 목업 D-03 잠긴 상세
const SINGLE_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA3'; // nakdong_DEM_10m.tif — 조각 1건

function renderDetail(datasetId: string, source: DetailSource = fixtureDetailSource()) {
  return render(
    <MemoryRouter initialEntries={[`/datasets/${datasetId}`]}>
      <Routes>
        <Route path="/datasets/:datasetId" element={<DatasetDetailPage source={source} />} />
        <Route path="/datasets" element={<div>카탈로그</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

async function settle(name: string) {
  return screen.findByRole('heading', { level: 1, name });
}

describe('§8 되돌아가기 — 헤더 밖 제 줄에 하나', () => {
  it('`← {들어온 곳}` 한 줄이고 기본 라벨은 목록이다', async () => {
    renderDetail(OPEN_ID);
    await settle('낙동강 유역 강우 (2025)');
    const back = screen.getByTestId('backrow');
    expect(within(back).getAllByRole('link')).toHaveLength(1);
    expect(back.textContent).toContain('←');
    expect(back.textContent).toContain('데이터셋 목록');
  });

  it('경로(브레드크럼)도 형제 전환도 두지 않는다 (§12 v2.2)', async () => {
    renderDetail(OPEN_ID);
    await settle('낙동강 유역 강우 (2025)');
    expect(screen.queryByRole('navigation', { name: '경로' })).toBeNull();
    expect(screen.queryByText(/다른 데이터셋/)).toBeNull();
  });

  it('되돌아가기는 헤더 **밖**에 있다', async () => {
    renderDetail(OPEN_ID);
    await settle('낙동강 유역 강우 (2025)');
    expect(screen.getByTestId('detail-header').contains(screen.getByTestId('backrow'))).toBe(false);
  });
});

describe('§8 상세 헤더 — 줄마다 한 가지만 말한다', () => {
  it('제목은 사람이 붙인 이름이고 파일명은 그 아래 제 줄이다', async () => {
    renderDetail(OPEN_ID);
    await settle('낙동강 유역 강우 (2025)');
    expect(screen.getByTestId('dh-file')).toHaveTextContent('nakdong_precip_2025_Lv2.nc');
    expect(screen.getByTestId('dh-sum')).toHaveTextContent('유역 평균 강수량');
  });

  it('칩은 판단에 쓰는 것만 — 주제 · 가공 단계 · Verified 자리', async () => {
    renderDetail(OPEN_ID);
    await settle('낙동강 유역 강우 (2025)');
    const tags = screen.getByTestId('dh-tags');
    expect(within(tags).getByText('강우·강수')).toBeInTheDocument();
    expect(within(tags).getByText('Lv2')).toBeInTheDocument();
    // Verified 배지의 모양·조건은 E-06(WU-P6)이 채운다 — 여기는 자리만 잡는다
    expect(tags.querySelector('[data-slot="verified-badge"]')).not.toBeNull();
  });

  it('소유자·올린 사람·포맷을 헤더에 두지 않는다 (중복 금지 · §12 v1.6)', async () => {
    renderDetail(OPEN_ID);
    await settle('낙동강 유역 강우 (2025)');
    const header = screen.getByTestId('detail-header');
    expect(header.textContent).not.toContain('호랑이');
    expect(header.textContent).not.toContain('소유자');
    expect(header.textContent).not.toContain('올린 사람');
  });

  it('헤더 우측 승인 액션 한 자리는 E-06(P6)이 채우도록 비워 둔다', async () => {
    renderDetail(OPEN_ID);
    await settle('낙동강 유역 강우 (2025)');
    const slot = screen.getByTestId('detail-header').querySelector('[data-slot="verification-action"]');
    expect(slot).not.toBeNull();
    expect(slot).toHaveAttribute('data-fills-in', 'WU-P6');
    expect(slot!.textContent).toBe('');
  });
});

describe('§5 기본 정보 — 아홉 칸', () => {
  it('라벨과 순서가 정본 그대로다', async () => {
    renderDetail(OPEN_ID);
    await settle('낙동강 유역 강우 (2025)');
    const keys = within(screen.getByTestId('basic-info'))
      .getAllByTestId('ig-k')
      .map((e) => e.textContent);
    expect(keys).toEqual([
      '구성', '좌표계', '기간', '격자', '포맷', '파일', '원천 표기', '소유자', '올린 사람',
    ]);
  });

  it('공간 범위 칸을 두지 않는다 (이름과 지도가 이미 말한다)', async () => {
    renderDetail(OPEN_ID);
    await settle('낙동강 유역 강우 (2025)');
    expect(within(screen.getByTestId('basic-info')).queryByText('공간 범위')).toBeNull();
  });

  it('목업이 준 값을 그대로 말한다', async () => {
    renderDetail(OPEN_ID);
    await settle('낙동강 유역 강우 (2025)');
    const info = screen.getByTestId('basic-info');
    expect(within(info).getByTestId('ig-구성')).toHaveTextContent('시간별 격자 강수량 (tp, mm)');
    expect(within(info).getByTestId('ig-좌표계')).toHaveTextContent('EPSG:5179');
    expect(within(info).getByTestId('ig-기간')).toHaveTextContent('2025-06 ~ 09');
    expect(within(info).getByTestId('ig-격자')).toHaveTextContent('0.05° (~5km)');
    expect(within(info).getByTestId('ig-소유자')).toHaveTextContent('호랑이');
    expect(within(info).getByTestId('ig-올린 사람')).toHaveTextContent('호랑이');
  });

  it('`파일` 칸은 조각 수와 용량 합계만 말한다', async () => {
    renderDetail(OPEN_ID);
    await settle('낙동강 유역 강우 (2025)');
    expect(screen.getByTestId('ig-파일')).toHaveTextContent('조각 4개 · 합계 148 MB');
  });

  it('조각을 이 자리에 나열하지 않는다', async () => {
    renderDetail(OPEN_ID);
    await settle('낙동강 유역 강우 (2025)');
    expect(screen.queryByText('nakdong_precip_2025_Lv2_06.nc')).toBeNull();
  });

  it('파일이 한 건이면 파일명과 용량을 그대로 쓴다', async () => {
    renderDetail(SINGLE_ID);
    await settle('nakdong_DEM_10m.tif');
    expect(screen.getByTestId('ig-파일')).toHaveTextContent('nakdong_DEM_10m.tif');
    expect(screen.getByTestId('ig-파일').textContent).not.toContain('조각');
  });

  it('정본이 값을 주지 않은 칸은 지어내지 않고 비운 표시를 쓴다', async () => {
    renderDetail(SINGLE_ID);
    await settle('nakdong_DEM_10m.tif');
    expect(screen.getByTestId('ig-원천 표기')).toHaveTextContent('—');
  });
});

describe('§7 잠김 (허용 안 됨) — 헤더 요약 + 잠김 안내만', () => {
  it('이름·요약·헤더 태그까지는 보인다 (P-13)', async () => {
    renderDetail(LOCKED_ID);
    await settle('낙동강 유역 유출량 (2025)');
    expect(screen.getByTestId('dh-file')).toHaveTextContent('nakdong_runoff_2025_Lv2.nc');
    expect(screen.getByTestId('dh-sum')).toHaveTextContent('강우와 짝이 되는 유출 결과');
    const tags = screen.getByTestId('dh-tags');
    expect(within(tags).getByText('유출·수문')).toBeInTheDocument();
    expect(within(tags).getByText('Lv2')).toBeInTheDocument();
    expect(within(tags).getByText('잠김')).toBeInTheDocument();
  });

  it('`기본 정보` 블록을 통째로 비운다 (basicInfo null · PLAN-SoT §9-㊼-④)', async () => {
    renderDetail(LOCKED_ID);
    await settle('낙동강 유역 유출량 (2025)');
    expect(screen.queryByTestId('basic-info')).toBeNull();
  });

  it('`basicInfo` 가 null 이면 그리지 않는다 — 잠김 게이트와 별개의 두 번째 방어', async () => {
    const odd: DatasetDetail = { ...FIXTURE_DETAILS[LOCKED_ID]!, bodyAccessible: true };
    renderDetail(LOCKED_ID, { async get() { return odd; } });
    await settle('낙동강 유역 유출량 (2025)');
    expect(screen.queryByTestId('basic-info')).toBeNull();
  });

  it('카탈로그 행과 달리 상세에는 `조각 N` 이 뜨지 않는다 — 의도된 차이다', async () => {
    renderDetail(LOCKED_ID);
    await settle('낙동강 유역 유출량 (2025)');
    expect(screen.queryByText(/조각 3개/)).toBeNull();
  });

  it('본문 대신 잠김 안내와 접근 요청 자리가 나온다', async () => {
    renderDetail(LOCKED_ID);
    await settle('낙동강 유역 유출량 (2025)');
    const body = screen.getByTestId('locked-body-slot');
    expect(within(body).getByText('이름과 요약까지만 보여요')).toBeInTheDocument();
    expect(
      within(body).getByText('요청하면 교수 또는 승인을 맡은 연구원이 검토해요.'),
    ).toBeInTheDocument();
    // 접근 요청 버튼의 실물은 E-06(WU-P6)이 채운다
    const slot = body.querySelector('[data-slot="access-request"]');
    expect(slot).not.toBeNull();
    expect(slot).toHaveAttribute('data-fills-in', 'WU-P6');
  });
});

describe('§9 지워진 데이터의 주소로 직접 들어옴 — 묘비는 상세가 없다', () => {
  it('정본 문구를 그대로 말하고 목록으로 보낸다', async () => {
    const gone: DetailSource = {
      async get() {
        throw new DatasetGone();
      },
    };
    renderDetail('01JYZ9K7WQ3N8V4M2X6C5B0ZZZ', gone);
    expect(
      await screen.findByText(
        '이 데이터는 지워졌어요. 계보 기록은 관련 데이터의 상세에서 볼 수 있어요.',
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole('link', { name: '데이터셋 목록' })).toHaveAttribute(
      'href',
      '/datasets',
    );
  });
});

describe('501 → 실서버 전환에 화면 코드가 바뀌지 않는다', () => {
  it('출처가 서버든 픽스처든 같은 컴포넌트가 같은 자리를 그린다', async () => {
    const fromServer: DatasetDetail = {
      ...FIXTURE_DETAILS[OPEN_ID]!,
      name: '서버가 내려준 이름',
      basicInfo: { ...FIXTURE_DETAILS[OPEN_ID]!.basicInfo!, crs: 'EPSG:4326' },
    };
    renderDetail(OPEN_ID, { async get() { return fromServer; } });
    await settle('서버가 내려준 이름');
    expect(screen.getByTestId('ig-좌표계')).toHaveTextContent('EPSG:4326');
  });
});

describe('계보·미리보기·활용 프로젝트는 이 WU 가 만들지 않는다 (P2·P3·P5)', () => {
  it('상단만 세운다', async () => {
    renderDetail(OPEN_ID);
    await settle('낙동강 유역 강우 (2025)');
    expect(screen.queryByText('계보')).toBeNull();
    expect(screen.queryByText('미리보기')).toBeNull();
    expect(screen.queryByText('활용·접근')).toBeNull();
  });
});
