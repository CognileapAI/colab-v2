/**
 * S-05 데이터셋 상세 **섹션 3(활용 · 가져가기)** — 정본 대비 시험 (레인 Q-D).
 * 오라클 = `E-03_데이터셋_상세/documents/Policy_데이터셋_상세.md` v2.8
 *   · §4 판단 순서 = 기본 정보 → 계보 → 미리보기 → 활용
 *   · §5 활용 프로젝트 행 · §5 122행 `파일` 칸과 `보기` 목록
 *   · §8 활용 프로젝트 목록 · 다운로드 · 잠긴 상세
 *   · §9 오류와 예외
 * 화면 글자는 정본에서 그대로 온다 — 여기서 새 한국어 라벨을 만들지 않는다.
 */
import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { FIXTURE_DETAILS } from '../src/components/detail/fixture';
import type {
  DatasetDetail,
  DatasetProjectUse,
  DetailSource,
} from '../src/components/detail/types';
import { DatasetGone } from '../src/components/detail/types';
import type { DatasetFile, FilesSource } from '../src/components/detail/filesSource';

const OPEN_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA1';
const LOCKED_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA5';

function detailWith(patch: Partial<DatasetDetail>): DatasetDetail {
  return { ...FIXTURE_DETAILS[OPEN_ID]!, ...patch };
}

function sourceOf(detail: DatasetDetail): DetailSource {
  return { get: async () => detail };
}

/** 파일 목록 대역. **부른 횟수를 센다** — `보기` 를 누르기 전에는 0 이어야 한다 (계약 축자). */
function filesSpy(items: DatasetFile[]): FilesSource & { calls: number } {
  const spy = {
    calls: 0,
    async list(_datasetId: string) {
      spy.calls += 1;
      return items;
    },
  };
  return spy;
}

function renderDetail(
  datasetId: string,
  source: DetailSource,
  filesSource?: FilesSource,
) {
  return render(
    <MemoryRouter initialEntries={[`/datasets/${datasetId}`]}>
      <Routes>
        <Route
          path="/datasets/:datasetId"
          element={<DatasetDetailPage source={source} filesSource={filesSource} />}
        />
        <Route path="/datasets" element={<div>카탈로그</div>} />
        <Route path="/lab" element={<div>연구실</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

async function settle(name: string) {
  return screen.findByRole('heading', { level: 1, name });
}

async function click(el: Element) {
  fireEvent.click(el);
  await act(async () => {});
}

const USE_ONE: DatasetProjectUse = {
  projectId: '01JYZ9K7WQ3N8V4M2X6C5B0P01',
  name: '낙동강 홍수 예측',
  type: '국가과제',
  period: { start: '2025-03', end: '2026-02' },
  usageNote: '강우 입력 자료로 썼어요',
};

const USE_TWO: DatasetProjectUse = {
  ...USE_ONE,
  projectId: '01JYZ9K7WQ3N8V4M2X6C5B0P02',
  name: '유역 물수지 논문',
  type: '논문',
  usageNote: '검증 자료로 썼어요',
};

describe('§8 활용 프로젝트 목록 — `#sec-usage`', () => {
  it('활용 섹션이 `#sec-usage` 앵커로 선다 (계보 배지의 목적지)', async () => {
    renderDetail(OPEN_ID, sourceOf(detailWith({ projects: [USE_ONE] })));
    await settle('낙동강 유역 강우 (2025)');
    const sec = await screen.findByTestId('usage-section');
    expect(sec.id).toBe('sec-usage');
    expect(sec.tagName.toLowerCase()).toBe('section');
  });

  it('판단 순서대로 계보·미리보기 **뒤**에 온다 (§4 · §3.1)', async () => {
    renderDetail(OPEN_ID, sourceOf(detailWith({ projects: [USE_ONE] })));
    await settle('낙동강 유역 강우 (2025)');
    const usage = await screen.findByTestId('usage-section');
    const preview = screen.getByTestId('dataset-preview');
    expect(preview.compareDocumentPosition(usage) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('카드를 세로로 쌓아 전부 보여주고 머리줄 N 이 카드 수와 같다', async () => {
    renderDetail(OPEN_ID, sourceOf(detailWith({ projects: [USE_ONE, USE_TWO] })));
    await settle('낙동강 유역 강우 (2025)');
    const sec = await screen.findByTestId('usage-section');
    expect(within(sec).getAllByTestId('usage-card')).toHaveLength(2);
    expect(sec.textContent).toContain('이 데이터를 쓴 과제·논문 2건');
  });

  it('건마다 이름·유형·기간과 **연결마다 따로인** 의미 문장을 표시한다 (§5)', async () => {
    renderDetail(OPEN_ID, sourceOf(detailWith({ projects: [USE_ONE, USE_TWO] })));
    await settle('낙동강 유역 강우 (2025)');
    const cards = within(await screen.findByTestId('usage-section')).getAllByTestId('usage-card');
    expect(cards[0]!.textContent).toContain('낙동강 홍수 예측');
    expect(cards[0]!.textContent).toContain('국가과제');
    // 기간 표기는 프로젝트 목록과 **같은 함수**를 쓴다 — 한 제품이 기간을 두 모양으로 그리지 않는다
    expect(cards[0]!.textContent).toContain('2025.03~2026.02');
    expect(cards[0]!.textContent).toContain('강우 입력 자료로 썼어요');
    expect(cards[1]!.textContent).toContain('검증 자료로 썼어요');
  });

  it('0건이면 빈 상태 문구를 놓는다 (§5)', async () => {
    renderDetail(OPEN_ID, sourceOf(detailWith({ projects: [] })));
    await settle('낙동강 유역 강우 (2025)');
    const sec = await screen.findByTestId('usage-section');
    expect(sec.textContent).toContain('아직 어느 과제·논문에도 담기지 않았어요');
    expect(within(sec).queryAllByTestId('usage-card')).toHaveLength(0);
  });
});

describe('§8 다운로드 — 활용·접근 섹션의 진입점', () => {
  it('`canDownload` 가 참이면 버튼이 서고 **용량을 표시한다** (§8 다운로드 행)', async () => {
    const base = FIXTURE_DETAILS[OPEN_ID]!;
    renderDetail(
      OPEN_ID,
      sourceOf(detailWith({ actions: { ...base.actions, canDownload: true } })),
    );
    await settle('낙동강 유역 강우 (2025)');
    const btn = await screen.findByTestId('detail-download');
    expect(btn.textContent).toContain('다운로드');
    expect(btn.textContent).toContain('148 MB');
  });

  it('조각 묶음이어도 버튼은 **하나**다 — 조각마다 두지 않는다 (§2 흐름 표)', async () => {
    const base = FIXTURE_DETAILS[OPEN_ID]!;
    renderDetail(
      OPEN_ID,
      sourceOf(detailWith({ actions: { ...base.actions, canDownload: true } })),
    );
    await settle('낙동강 유역 강우 (2025)');
    expect(screen.getAllByTestId('detail-download')).toHaveLength(1);
  });

  it('`canDownload` 가 거짓이면 **숨긴다** — 화면이 조건을 정하지 않는다 (P-7·P-12)', async () => {
    const base = FIXTURE_DETAILS[OPEN_ID]!;
    renderDetail(
      OPEN_ID,
      sourceOf(detailWith({ actions: { ...base.actions, canDownload: false } })),
    );
    await settle('낙동강 유역 강우 (2025)');
    expect(screen.queryByTestId('detail-download')).toBeNull();
  });

  it('받은 횟수는 화면에 보여주지 않는다 (§8 다운로드 행)', async () => {
    const base = FIXTURE_DETAILS[OPEN_ID]!;
    renderDetail(
      OPEN_ID,
      sourceOf(detailWith({ actions: { ...base.actions, canDownload: true } })),
    );
    await settle('낙동강 유역 강우 (2025)');
    expect(screen.getByTestId('usage-section').textContent).not.toMatch(/받은 횟수|다운로드 \d+회/);
  });
});

describe('§7·§8 잠긴 상세 — 접근 요청 자리는 하나다', () => {
  it('잠기면 활용 섹션도 다운로드도 서지 않는다 (헤더 요약 + 잠김 안내까지)', async () => {
    renderDetail(LOCKED_ID, sourceOf(FIXTURE_DETAILS[LOCKED_ID]!));
    await settle('낙동강 유역 유출량 (2025)');
    expect(screen.queryByTestId('usage-section')).toBeNull();
    expect(screen.queryByTestId('detail-download')).toBeNull();
  });

  it('접근 요청은 **기존 P6 자리 한 곳**이다 — 두 번째 요청 버튼을 만들지 않는다', async () => {
    renderDetail(LOCKED_ID, sourceOf(FIXTURE_DETAILS[LOCKED_ID]!));
    await settle('낙동강 유역 유출량 (2025)');
    expect(screen.getAllByRole('button', { name: '접근 요청' })).toHaveLength(1);
  });
});

describe('§5 122행 — `파일` 칸의 `보기` 와 조각 목록', () => {
  /** 조각 목록 토글 = 기본 정보 격자의 `.ig-more` 하나다 (아래 주석). */
  const 조각보기 = () => document.querySelector('.ig-more') as HTMLElement;
  const 조각접기 = 조각보기;
  // ⭑ ⟨병합 창 8-a⟩ **`보기` 버튼이 이 화면에 둘이 됐다.** `main` 의 조각 목록 토글(`.ig-more` ·
  //   기본 정보 격자 `파일` 칸 · 이 describe 의 대상)과 PR #1 의 파일 관리 구역 토글
  //   (`[data-testid=dt-files-toggle]` · `〈339〉`)이 둘 다 「보기」라고 적는다.
  //   ⛔ **질의를 느슨하게 하지 않는다** — `getAllBy*` 로 첫 번째를 집으면 순서가 바뀌는 날
  //   이 시험이 **다른 버튼을 재고도 green** 이 된다. 재는 대상을 **자리로 못 박는다.**
  //   ⚠ 「같은 낱말의 버튼 둘」 자체는 이 회차가 판정하지 않았다 — 사람이 볼 화면의 물음이라
  //   레인 보고서에 올렸다(`reports/window-8a/lane-report.md`).
  // ⭑ ⟨병합 창 8-a⟩ `byteSize`·`createdAt` 은 PR #1(`〈339〉`-(가))이 계약에 더한 **필수** 칸이다.
  //   이 픽스처는 그 전 회차라 빠져 있었고 `tsc` 가 그것을 냈다. **값은 지어낸 것이 아니라
  //   이 시험이 안 보는 칸**이다(이 describe 가 재는 것은 `보기` 와 종류 표시뿐).
  const 본체: DatasetFile[] = [
    { fileId: '01JYZ9K7WQ3N8V4M2X6C5B0F01', fileName: 'precip_202506.nc', kind: '본체',
      byteSize: null, createdAt: '2026-06-01T00:00:00Z' },
    { fileId: '01JYZ9K7WQ3N8V4M2X6C5B0F02', fileName: 'precip_202507.nc', kind: '본체',
      byteSize: null, createdAt: '2026-07-01T00:00:00Z' },
  ];

  it('`보기` 를 누르기 전에는 목록 op 을 **부르지 않는다** (계약 축자)', async () => {
    const files = filesSpy(본체);
    renderDetail(OPEN_ID, sourceOf(detailWith({})), files);
    await settle('낙동강 유역 강우 (2025)');
    expect(files.calls).toBe(0);
    expect(screen.queryByTestId('file-list')).toBeNull();
  });

  it('`보기` 를 누르면 그 아래에 목록이 열리고 본체 조각을 나열한다', async () => {
    const files = filesSpy(본체);
    renderDetail(OPEN_ID, sourceOf(detailWith({})), files);
    await settle('낙동강 유역 강우 (2025)');
    await click(조각보기());
    expect(files.calls).toBe(1);
    const list = await screen.findByTestId('file-list');
    expect(list.textContent).toContain('precip_202506.nc');
    expect(list.textContent).toContain('precip_202507.nc');
  });

  it('기준 격자 파일이 없으면 **없다고 적는다** (짝 파일 없음과 필요 없음을 가른다)', async () => {
    const files = filesSpy(본체);
    renderDetail(OPEN_ID, sourceOf(detailWith({})), files);
    await settle('낙동강 유역 강우 (2025)');
    await click(조각보기());
    const list = await screen.findByTestId('file-list');
    expect(list.textContent).toContain('기준 격자 파일이 없어요');
  });

  it('기준 격자 파일이 있으면 그 종류로 함께 보여준다', async () => {
    const files = filesSpy([
      ...본체,
      {
        fileId: '01JYZ9K7WQ3N8V4M2X6C5B0F03',
        fileName: 'lat.nc',
        kind: '기준 격자 파일',
        byteSize: null,
        createdAt: '2026-06-01T00:00:00Z',
        gridAxis: { carriesLat: true, carriesLon: false },
      },
    ]);
    renderDetail(OPEN_ID, sourceOf(detailWith({})), files);
    await settle('낙동강 유역 강우 (2025)');
    await click(조각보기());
    const list = await screen.findByTestId('file-list');
    expect(within(list).getByTestId('file-grid-group').textContent).toContain('lat.nc');
    expect(list.textContent).not.toContain('기준 격자 파일이 없어요');
  });

  it('목록은 **자체 스크롤을 만들지 않는다** — 페이지 흐름을 그대로 쓴다', async () => {
    const files = filesSpy(본체);
    renderDetail(OPEN_ID, sourceOf(detailWith({})), files);
    await settle('낙동강 유역 강우 (2025)');
    await click(조각보기());
    const list = await screen.findByTestId('file-list');
    expect(list.style.overflow).toBe('');
    expect(list.style.overflowY).toBe('');
    expect(list.style.maxHeight).toBe('');
  });

  it('다시 누르면 접히고 op 을 또 부르지 않는다', async () => {
    const files = filesSpy(본체);
    renderDetail(OPEN_ID, sourceOf(detailWith({})), files);
    await settle('낙동강 유역 강우 (2025)');
    await click(조각보기());
    await screen.findByTestId('file-list');
    await click(조각접기());
    expect(screen.queryByTestId('file-list')).toBeNull();
    expect(files.calls).toBe(1);
  });
});

describe('§9 · 없는 주소 — 서버가 접은 404 를 묘비로 번역하지 않는다', () => {
  it('404 는 중립 문구다 — 존재한 적 없는 id 에 삭제를 단정하지 않는다', async () => {
    const gone: DetailSource = {
      get: async () => {
        throw new DatasetGone();
      },
    };
    renderDetail('01JYZ9K7WQ3N8V4M2X6C5B0ZZZ', gone);
    const box = await screen.findByTestId('detail-gone');
    expect(box.textContent).toContain('이 주소에는 화면이 없어요.');
    expect(box.textContent).not.toContain('지워졌어요');
  });

  it('다른 연구실 항목도 같은 404 라 같은 문구다 (경계 밖 · P-9·P-10)', async () => {
    const gone: DetailSource = {
      get: async () => {
        throw new DatasetGone();
      },
    };
    renderDetail('01JYZ9K7WQ3N8V4M2X6C5B0YYY', gone);
    expect((await screen.findByTestId('detail-gone')).textContent).toContain(
      '이 주소에는 화면이 없어요.',
    );
  });
});

describe('픽스처와 실서버의 어긋남', () => {
  it('열린 데이터의 `canDownload` 는 참이다 — 서버 축자 `canDownload = body_accessible`', () => {
    for (const d of Object.values(FIXTURE_DETAILS)) {
      expect(d.actions.canDownload).toBe(d.bodyAccessible);
    }
  });
});
