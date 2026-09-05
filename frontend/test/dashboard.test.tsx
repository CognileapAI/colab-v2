/**
 * S-01 연구실 대시보드 — 정본 대비 시험 (WU-P7).
 * 오라클 = `E-07_홈_대시보드/documents/Policy_홈_대시보드.md` (v1.5) 와 그 PRD.
 * 화면 글자는 정본에서 그대로 온다 — 여기서 새 한국어 라벨을 만들지 않는다.
 *
 * **음성이 이 파일의 절반이다.** 대시보드의 실패는 「안 보인다」로 오지 않고
 * 「보이면 안 되는 사람에게 보였다」로 오는데(§6 숨김 원칙) 그건 화면에서 조용하다.
 */
import { render, screen, waitFor, within, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { describe, expect, it, beforeEach } from 'vitest';
import { LabPage } from '../src/routes/LabPage';
import { GroupHidden, type DashboardSource } from '../src/components/dashboard/types';
import { SessionProvider } from '../src/permission/session';
import { recordVisit } from '../src/components/dashboard/visits';
import { account } from './factories';
import type { CurrentAccount } from '../src/api/client';

const DS1 = '01JYZ9K7WQ3N8V4M2X6C5B0DS1';
const DS2 = '01JYZ9K7WQ3N8V4M2X6C5B0DS2';
const PRJ = '01JYZ9K7WQ3N8V4M2X6C5B0PR1';

/** 정본 §3.1 의 예시 값 — 확정 71 · 원천 16 · 확인 필요 25 · 기록 없음 16, 지표 87 · 미확정 41. */
function fullSource(over: Partial<DashboardSource> = {}): DashboardSource {
  return {
    summary: async () => ({
      projectCount: 4,
      datasetCount: 128,
      lineageSettledCount: 87,
      lineageUnsettledCount: 41,
      verifiedCount: 33,
    }),
    dataMap: async () => ({
      totalCount: 128,
      byLineageState: [
        { value: '확정', count: 71 },
        { value: '원천', count: 16 },
        { value: '확인 필요', count: 25 },
        { value: '기록 없음', count: 16 },
      ],
      byTopic: [{ value: '강우·강수', count: 80 }, { value: '토지피복·LULC', count: 48 }],
    }),
    activities: async () => [
      {
        activityId: '01JYZ9K7WQ3N8V4M2X6C5B0AC1',
        actor: { accountId: '01JYZ9K7WQ3N8V4M2X6C5B0LI1', name: '사자' },
        action: '데이터셋 등록',
        target: { kind: '데이터셋', id: DS1, name: '낙동강 강우 원자료' },
        occurredAt: '2026-08-30T09:00:00Z',
      },
    ],
    lab: async () => ({
      labId: '01JYZ9K7WQ3N8V4M2X6C5B0AHU',
      name: '수자원순환연구실',
      university: 'A 대학교',
      department: '토목공학과',
      principalInvestigator: '사자 교수',
      researchField: '수문학',
      introduction: '수문 자료를 다룬다',
      defaultVisibility: '열림',
      memberCount: 7,
      openedAt: '2020-03-01T00:00:00Z',
    }),
    lineageTodo: async () => [
      { datasetId: DS1, name: '낙동강 강우 원자료', lineageState: '기록 없음' },
      { datasetId: DS2, name: '낙동강 강우 격자화', lineageState: '확인 필요' },
      { datasetId: PRJ, name: '한강 유출량', lineageState: '확인 필요' },
      { datasetId: 'x4', name: '금강 수질', lineageState: '확인 필요' },
    ],
    // 기본은 **권한 없음** — 승인 계열 두 그룹은 서버가 403 을 내는 것이 기본값이다.
    pendingVerifications: async () => {
      throw new GroupHidden();
    },
    pendingAccessRequests: async () => {
      throw new GroupHidden();
    },
    approveAccessRequest: async () => undefined,
    rejectAccessRequest: async () => undefined,
    ...over,
  };
}

function renderLab(source: DashboardSource, acc: CurrentAccount | null = account()) {
  return render(
    <MemoryRouter initialEntries={['/lab']}>
      <SessionProvider account={acc}>
        <Routes>
          <Route path="/lab" element={<LabPage source={source} />} />
          <Route path="/datasets" element={<Landed name="카탈로그" />} />
          <Route path="/datasets/:datasetId" element={<Landed name="데이터셋 상세" />} />
          <Route path="/lab-settings" element={<Landed name="연구실 설정" />} />
        </Routes>
      </SessionProvider>
    </MemoryRouter>,
  );
}

function Landed(props: { name: string }) {
  const location = useLocation();
  return (
    <p>
      {props.name} 도착:{location.search}
    </p>
  );
}

/** `우리 연구실` 구획 라벨 — 같은 글자로 시작하는 카드 제목과 헷갈리지 않게 자리로 집는다. */
function sectionLabel(container: HTMLElement): HTMLElement {
  return container.querySelector('.dash-section-label--opens') as HTMLElement;
}

async function click(el: HTMLElement | null) {
  fireEvent.click(el as HTMLElement);
  await Promise.resolve();
}

beforeEach(() => {
  globalThis.localStorage?.clear();
});

// ── 구획과 지표 ──────────────────────────────────────────────────────────────

describe('§1.3-1 — 화면은 두 구획으로 갈린다', () => {
  it('왼쪽 `우리 연구실` · 오른쪽 `내 일` 이 있고, 왼쪽만 눌린다', async () => {
    const { container } = renderLab(fullSource());
    expect(container.querySelector('[data-section="우리 연구실"]')).not.toBeNull();
    expect(container.querySelector('[data-section="내 일"]')).not.toBeNull();
    // 오른쪽 라벨은 **누르는 자리가 아니다** (§1.3-1).
    expect(screen.getByText('내 일').tagName).toBe('P');
    await waitFor(() => expect(screen.getByText('계보 확정 →')).toBeTruthy());
  });
});

describe('§5 — 요약 지표', () => {
  it('타일은 넷이고 계보 확정 아래에 확인 필요 건수가 붙는다', async () => {
    renderLab(fullSource());
    await waitFor(() => expect(screen.getByText('87')).toBeTruthy());
    expect(screen.getByText('미확정 41건')).toBeTruthy();
    expect(screen.getByText('4')).toBeTruthy();
    expect(screen.getByText('128')).toBeTruthy();
    expect(screen.getByText('33')).toBeTruthy();
  });

  it('**퍼센트를 글자로 적지 않는다** (§5 축자)', async () => {
    const { container } = renderLab(fullSource());
    await waitFor(() => expect(screen.getByText('87')).toBeTruthy());
    expect(container.textContent).not.toMatch(/%/);
  });
});

describe('§8 — 데이터 맵', () => {
  it('계보 네 값이 전부 있고 계산 한 줄이 지표와 맞는다', async () => {
    renderLab(fullSource());
    await waitFor(() => expect(screen.getByText('확정')).toBeTruthy());
    for (const value of ['확정', '원천', '확인 필요', '기록 없음']) {
      expect(screen.getAllByText(value).length).toBeGreaterThan(0);
    }
    // §8 계산 관계 안내 줄 — 맵의 71 과 지표의 87 이 어긋난 숫자로 보이지 않게 한다.
    expect(screen.getByText('확정 71 + 원천 16 = 지표의 계보 확정 87')).toBeTruthy();
    // 원천 줄의 부연 (§8).
    expect(screen.getByText('기록 없음이 정상')).toBeTruthy();
  });

  it('막대를 누르면 **그 조건이 걸린** 카탈로그로 간다 (§8 축자)', async () => {
    renderLab(fullSource());
    await waitFor(() => expect(screen.getAllByText('확인 필요').length).toBeGreaterThan(0));
    await click(screen.getAllByText('확인 필요')[0]!.closest('button'));
    await waitFor(() => expect(screen.getByText(/카탈로그 도착/)).toBeTruthy());
    expect(screen.getByText(/카탈로그 도착/).textContent).toContain('lineageState');
  });

  it('카드 헤더에 `전체 목록 보기` 가 있다 (§1.3-4 — 두 길의 무게가 다르다)', async () => {
    renderLab(fullSource());
    await waitFor(() => expect(screen.getByText('전체 목록 보기 →')).toBeTruthy());
  });
});

// ── 할 일 함 (§6) ────────────────────────────────────────────────────────────

describe('§6 — 할 일 함의 권한 훅은 그룹 각각에 걸린다', () => {
  it('기본 권한 연구원도 카드를 보고, 계보 확인 그룹만 남는다', async () => {
    renderLab(fullSource());
    await waitFor(() => expect(screen.getByText('계보 확인')).toBeTruthy());
    // **카드 자체는 전 구성원에게 보인다** — 0건 카드가 되지 않게 하는 조항이다.
    expect(screen.getByText('할 일 함')).toBeTruthy();
    // 승인 계열 두 그룹은 **통째로 없다**.
    expect(screen.queryByText('Verified 검토 대기')).toBeNull();
    expect(screen.queryByText('받은 접근 요청')).toBeNull();
  });

  it('교수는 세 그룹을 다 본다', async () => {
    renderLab(
      fullSource({
        pendingVerifications: async () => [
          {
            dataset: { datasetId: DS2, name: '낙동강 강우 격자화' },
            requester: { accountId: 'a', name: '호랑이' },
            requestedAt: '2026-08-29T00:00:00Z',
          },
        ],
        pendingAccessRequests: async () => [
          {
            requestId: 'r1',
            dataset: { datasetId: DS1, name: '낙동강 강우 원자료' },
            requester: { accountId: 'b', name: '강아지' },
            requestedAt: '2026-08-28T00:00:00Z',
            reason: '격자화에 쓰려고 해요',
          },
        ],
      }),
    );
    await waitFor(() => expect(screen.getByText('Verified 검토 대기')).toBeTruthy());
    expect(screen.getByText('받은 접근 요청')).toBeTruthy();
    // **Verified 는 홈에서 승인하지 않는다** (§8 축자 — 근거를 보지 않고 누르는 승인을 막는다).
    expect(screen.getByText('상세에서 검토 →')).toBeTruthy();
    // 접근 요청은 반대다 — **처리 버튼을 그 자리에 둔다** (§8). 두 갈래가 서로 다른 조항이다.
    expect(screen.getByText('승인')).toBeTruthy();
    expect(screen.getByText('거절')).toBeTruthy();
  });

  it('받은 접근 요청은 **그 자리에서** 처리한다 — 승인은 P6 op 을 그대로 부른다 (§8)', async () => {
    const called: string[] = [];
    renderLab(
      fullSource({
        pendingAccessRequests: async () => [
          {
            requestId: 'r1',
            dataset: { datasetId: DS1, name: '낙동강 강우 원자료' },
            requester: { accountId: 'b', name: '강아지' },
            requestedAt: '2026-08-28T00:00:00Z',
            reason: '모델 검증에 쓰려고 해요',
          },
        ],
        approveAccessRequest: async (requestId) => {
          called.push(`승인:${requestId}`);
        },
      }),
    );
    await waitFor(() => expect(screen.getByText('받은 접근 요청')).toBeTruthy());
    expect(screen.getByText(/사유: 모델 검증에 쓰려고 해요/)).toBeTruthy();
    await click(screen.getByText('승인'));
    await waitFor(() => expect(called).toEqual(['승인:r1']));
  });

  it('거절은 **사유가 있어야** 보내진다 — 1~300자 필수 (`Policy_승인_처리 §5` · P-26)', async () => {
    const called: string[] = [];
    renderLab(
      fullSource({
        pendingAccessRequests: async () => [
          {
            requestId: 'r1',
            dataset: { datasetId: DS1, name: '낙동강 강우 원자료' },
            requester: { accountId: 'b', name: '강아지' },
            requestedAt: '2026-08-28T00:00:00Z',
            reason: null,
          },
        ],
        rejectAccessRequest: async (requestId, reason) => {
          called.push(`거절:${requestId}:${reason}`);
        },
      }),
    );
    await waitFor(() => expect(screen.getByText('받은 접근 요청')).toBeTruthy());
    await click(screen.getByText('거절'));
    const send = screen.getByText('거절 보내기') as HTMLButtonElement;
    // 사유가 비면 보낼 수 없다 — 서버가 400 을 낼 것을 알면서 버튼을 열어 두면 함정이다.
    expect(send.disabled).toBe(true);
    fireEvent.change(
      screen.getByLabelText(/사유를 적어 주세요/),
      { target: { value: '공개 범위 밖이에요' } },
    );
    await click(screen.getByText('거절 보내기'));
    await waitFor(() => expect(called).toEqual(['거절:r1:공개 범위 밖이에요']));
  });

  it('계보 확인 그룹은 3건까지 펼치고 나머지는 `+N건 더 보기` 로 접는다 (§8)', async () => {
    const { container } = renderLab(fullSource());
    await waitFor(() => expect(screen.getByText('계보 확인')).toBeTruthy());
    const group = container.querySelector('.todo-grp') as HTMLElement;
    expect(within(group).getAllByRole('listitem')).toHaveLength(3);
    expect(within(group).getByText('+1건 더 보기')).toBeTruthy();
    await click(within(group).getByText('+1건 더 보기'));
    expect(within(group).getAllByRole('listitem')).toHaveLength(4);
  });

  it('그룹 건수는 **연구실 전체의 미확정**이고 전체 보기가 같은 곳으로 간다 (§8)', async () => {
    const { container } = renderLab(fullSource());
    await waitFor(() => expect(screen.getByText('계보 확인')).toBeTruthy());
    const group = container.querySelector('.todo-grp') as HTMLElement;
    // 펼친 3건이 아니라 지표의 41 이 소제목 오른쪽에 온다.
    expect(within(group).getByText('대기 41건')).toBeTruthy();
    await click(within(group).getByText(/계보 확인이 필요한 데이터 41건 전부 보기/));
    await waitFor(() => expect(screen.getByText(/카탈로그 도착/)).toBeTruthy());
  });

  it('계보 확인 항목은 **왜 확인해야 하는지**를 함께 든다 (§8)', async () => {
    renderLab(fullSource());
    await waitFor(() => expect(screen.getByText('계보 기록 없음')).toBeTruthy());
    expect(screen.getAllByText('계보 확인 →').length).toBeGreaterThan(0);
  });
});

// ── 연구실 정보 (§6 · §8) ────────────────────────────────────────────────────

describe('§6 — 연구실 정보는 읽기만 전 구성원에게 연다', () => {
  it('`우리 연구실` 라벨을 누르면 읽기 모달이 열린다', async () => {
    const { container } = renderLab(fullSource());
    await click(sectionLabel(container));
    await waitFor(() => expect(screen.getByRole('dialog', { name: '연구실 정보' })).toBeTruthy());
    expect(screen.getByText('수자원순환연구실')).toBeTruthy();
    expect(screen.getByText('7명')).toBeTruthy();
  });

  it('**편집 버튼만 권한자에게** 보인다 — 스위치가 꺼진 사람에게는 없다 (§6 · P-12)', async () => {
    const { container } = renderLab(fullSource());
    await click(sectionLabel(container));
    await waitFor(() => expect(screen.getByRole('dialog', { name: '연구실 정보' })).toBeTruthy());
    expect(screen.queryByText('연구실 정보 편집')).toBeNull();
  });

  it('`연구실 설정` 스위치가 켜지면 편집 버튼이 늘어난다', async () => {
    const { container } = renderLab(fullSource(), account({ '연구실 설정': true }));
    await click(sectionLabel(container));
    await waitFor(() => expect(screen.getByText('연구실 정보 편집')).toBeTruthy());
  });
});

// ── 최근 활동 (§5 · §10) ─────────────────────────────────────────────────────

describe('§10 — 내 열람은 브라우저에만 있다', () => {
  it('연구실 활동과 내 열람을 한 목록에 섞고 행마다 누가 한 일인지 적는다 (§5)', async () => {
    recordVisit({ kind: '데이터셋', id: DS2, name: '내가 본 격자화' }, '2026-08-31T09:00:00Z');
    renderLab(fullSource());
    await waitFor(() => expect(screen.getByText('내가 본 격자화')).toBeTruthy());
    expect(screen.getByText('내가 열어 봄')).toBeTruthy();
    expect(screen.getByText('사자가 데이터셋 등록')).toBeTruthy();
  });

  it('열람 기록 안내 줄은 내 열람이 하나도 없어도 같은 자리에 남는다 (§8)', async () => {
    renderLab(fullSource());
    await waitFor(() =>
      expect(
        screen.getByText(
          '내가 열어 본 기록은 이 기기에만 남아요. 다른 기기에서는 연구실 활동만 보여요.',
        ),
      ).toBeTruthy(),
    );
  });
});

// ── 빈 연구실 (§3.3 · §7) ────────────────────────────────────────────────────

describe('§3.3 — 데이터 0건인 첫날', () => {
  const emptySource = () =>
    fullSource({
      summary: async () => ({
        projectCount: 0,
        datasetCount: 0,
        lineageSettledCount: 0,
        lineageUnsettledCount: 0,
        verifiedCount: 0,
      }),
      dataMap: async () => ({
        totalCount: 0,
        byLineageState: [
          { value: '확정', count: 0 },
          { value: '원천', count: 0 },
          { value: '확인 필요', count: 0 },
          { value: '기록 없음', count: 0 },
        ],
        byTopic: [],
      }),
      activities: async () => [],
      lineageTodo: async () => [],
    });

  it('온보딩 3단계와 안내 문구가 뜬다', async () => {
    renderLab(emptySource());
    await waitFor(() =>
      expect(
        screen.getByText(
          '아직 올라온 데이터가 없어요. 과거 데이터를 한꺼번에 옮기지 않아도 돼요. 지금 쓰는 데이터 한 건부터 시작하세요.',
        ),
      ).toBeTruthy(),
    );
    for (const step of ['첫 데이터 업로드', '계보 확인', '구성원 초대']) {
      expect(screen.getAllByText(step).length).toBeGreaterThan(0);
    }
  });

  it('카드를 지우지 않고 **무엇이 채워질 자리인지** 한 줄로 남긴다 (§8)', async () => {
    renderLab(emptySource());
    await waitFor(() =>
      expect(
        screen.getByText(
          '아직 그릴 분포가 없어요. 데이터가 올라오면 계보 상태별·주제별로 자동으로 그려져요.',
        ),
      ).toBeTruthy(),
    );
    expect(screen.getByText('할 일 함')).toBeTruthy();
    expect(screen.getByText('최근 활동')).toBeTruthy();
  });

  it('데이터가 1건이라도 있으면 온보딩이 내려간다 (§7 전이표)', async () => {
    renderLab(fullSource());
    await waitFor(() => expect(screen.getByText('87')).toBeTruthy());
    expect(screen.queryByText('이렇게 시작해요')).toBeNull();
  });
});

// ── 실패 (§9) ────────────────────────────────────────────────────────────────

describe('§9 — 못 불러왔을 때', () => {
  it('데이터 맵 실패는 카탈로그 링크와 함께 정본 문구를 낸다', async () => {
    renderLab(
      fullSource({
        dataMap: async () => {
          throw new Error('boom');
        },
      }),
    );
    await waitFor(() =>
      expect(
        screen.getByText(/연구실 데이터 분포를 지금 불러오지 못했어요. 카탈로그에서는 볼 수 있어요./),
      ).toBeTruthy(),
    );
    // 한 구획이 죽어도 **다른 구획은 뜬다**.
    expect(screen.getByText('할 일 함')).toBeTruthy();
  });

  it('할 일 함 실패는 정본 문구와 다시 불러오기 버튼을 낸다', async () => {
    renderLab(
      fullSource({
        lineageTodo: async () => {
          throw new Error('boom');
        },
      }),
    );
    await waitFor(() =>
      expect(
        screen.getByText(/처리할 일을 불러오지 못했어요. 잠시 뒤 다시 시도해 주세요./),
      ).toBeTruthy(),
    );
    expect(screen.getByText('다시 불러오기')).toBeTruthy();
  });
});

/**
 * BF-8 — 화면 뿌리가 자기 여백을 갖는 관례(BF-5 가 `project.css` 에 세운 것)를 S-01 에 적용.
 * 계산값으로 재려면 `dashboard.css`·`search.css` 가 실려야 한다 (`vite.config.ts` `test.css.include`).
 */
describe('S-01 화면 뿌리 여백 (BF-8)', () => {
  it('뿌리는 좌우 여백과 프로젝트·데이터셋 상세와 같은 최대폭을 갖는다', async () => {
    const { container } = renderLab(fullSource());
    await screen.findByText('할 일 함');
    const root = container.querySelector('[data-screen="S-01"]');
    expect(root).not.toBeNull();
    const cs = getComputedStyle(root as Element);
    expect(parseFloat(cs.paddingLeft)).toBeGreaterThan(0);
    expect(parseFloat(cs.paddingRight)).toBeGreaterThan(0);
    expect(cs.maxWidth).toBe('1200px');
  });

  it('검색 히어로의 좌우 여백은 뿌리 여백과 겹치지 않는다', async () => {
    const { container } = renderLab(fullSource());
    await screen.findByText('할 일 함');
    const hero = container.querySelector('.search-hero');
    expect(hero).not.toBeNull();
    const cs = getComputedStyle(hero as Element);
    expect(parseFloat(cs.paddingLeft)).toBe(0);
    expect(parseFloat(cs.paddingRight)).toBe(0);
    // `shell.css` 가 `* { box-sizing: border-box }` 라 720px 은 여백을 포함한 폭이다.
    // 여백만 0 으로 두면 내용 폭이 680 → 720 으로 넓어진다 — 40px 을 최대폭에서 뺀다.
    expect(cs.maxWidth).toBe('680px');
  });
});
