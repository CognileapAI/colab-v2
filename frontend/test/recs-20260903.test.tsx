/**
 * 미결 권고 집행(2026-09-03 · `dev-package/notes/PENDING-RECS-20260903.md`)의 회귀 시험.
 * 등재 = `PLAN-SoT §9 〈296〉` (Ted 사전 위임 · advisor 권고대로 집행).
 *
 * 다루는 행 —
 *   ㉰ #27 없는 주소 화면 (`Policy_공통_기반` v1.6 `§2.4` 「없는 주소」 행)
 *   ㉰ #26 연구실 전환기의 `▾` 제거
 *   ㉯ 엿보기 — 미리보기 없는 데이터셋에서도 **버튼을 숨기지 않는다** (`Policy_데이터_찾기` v2.1 `§8`)
 *
 * **빈 집합 위에서 통과하지 않는다** — 단언 전에 대상이 1건 이상임을 먼저 잰다 (`CLAUDE.md §4`).
 */
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { AppRoutes } from '../src/app/routes';
import { SessionProvider } from '../src/permission/session';
import { DatasetsPage } from '../src/routes/DatasetsPage';
import { fixtureCatalogSource, FIXTURE_ROWS } from '../src/components/catalog/fixture';
import { account } from './factories';

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <SessionProvider account={account()}>
        <AppRoutes />
      </SessionProvider>
    </MemoryRouter>,
  );
}

/* ───────────────────────────────────────────────── #27 없는 주소 */
describe('#27 없는 주소 — 중립 문구 한 줄 ＋ 돌아가는 길 하나', () => {
  it('중립 문구를 낸다 — 정본 `Policy_공통_기반 §2.4` 축자', () => {
    renderAt('/이-주소는-없다');
    expect(screen.getByTestId('not-found-message')).toHaveTextContent(
      '이 주소에는 화면이 없어요.',
    );
  });

  it('묘비 문구를 쓰지 않는다 — 지워진 것과 애초에 없는 것은 다른 사실이다', () => {
    renderAt('/이-주소는-없다');
    const screenEl = document.querySelector('[data-screen="not-found"]');
    expect(screenEl).not.toBeNull();
    expect(screenEl!.textContent).not.toMatch(/지워졌/);
    expect(screenEl!.textContent).not.toMatch(/계보 기록은/);
  });

  it('돌아가는 길이 하나 있다 — `연구실로 돌아가기`', () => {
    renderAt('/이-주소는-없다');
    const link = screen.getByRole('link', { name: '연구실로 돌아가기' });
    expect(link).toHaveAttribute('href', '/lab');
  });
});

/* ───────────────────────────────────────────────── #26 전환기 ▾ */
describe('#26 연구실 전환기 — 없는 메뉴를 표기로 약속하지 않는다', () => {
  it('`▾` 를 달지 않는다', () => {
    renderAt('/lab');
    const sw = screen.getByTestId('lab-switcher');
    expect(sw.textContent).not.toMatch(/▾/);
    expect(sw.querySelector('.cv')).toBeNull();
  });

  it('전환기 자리 자체는 남는다 — 걷은 것은 화살표뿐이다', () => {
    renderAt('/lab');
    const sw = screen.getByTestId('lab-switcher');
    expect(sw).toBeInTheDocument();
    expect(sw.getAttribute('aria-label')).toMatch(/^연구실 전환 · /);
  });
});

/* ───────────────────────────────────────────────── 엿보기 · 미리보기 없는 데이터셋 */
describe('엿보기 — 미리보기가 없는 데이터셋에서도 숨기지 않는다', () => {
  it('행에 「미리보기 가능」 값이 없다 — 숨김은 계약 개정이다 (`fe-core.yaml` `DatasetRow` 13칸)', () => {
    // 이 시험이 잠그는 것은 **계약의 모양**이다. 픽스처 행에 미리보기 가부를 말하는 칸이
    // 생기면 여기서 먼저 깨지고, 그때가 「숨길지」를 다시 정하는 자리다.
    expect(FIXTURE_ROWS.length).toBeGreaterThan(0);
    for (const row of FIXTURE_ROWS) {
      expect(Object.keys(row)).not.toContain('previewable');
      expect(Object.keys(row)).not.toContain('hasPreview');
    }
  });

  it('열려 있는 행 전건에 엿보기 버튼이 있다 — 포맷을 보고 감추지 않는다', async () => {
    render(
      <MemoryRouter initialEntries={['/datasets']}>
        <DatasetsPage source={fixtureCatalogSource()} />
      </MemoryRouter>,
    );
    await screen.findByText('nakdong_precip_2025_Lv2.nc');
    const open = FIXTURE_ROWS.filter((r) => r.bodyAccessible);
    expect(open.length).toBeGreaterThan(0);
    for (const row of open) {
      expect(screen.getByLabelText(`${row.name} 엿보기`)).toBeInTheDocument();
    }
  });

  it('잠긴 행에는 두지 않는다 — 이 규칙만 행을 가른다 (`§8` 행 빠른 작업)', () => {
    const locked = FIXTURE_ROWS.filter((r) => !r.bodyAccessible);
    expect(locked.length).toBeGreaterThan(0);
    render(
      <MemoryRouter initialEntries={['/datasets']}>
        <DatasetsPage source={fixtureCatalogSource()} />
      </MemoryRouter>,
    );
    for (const row of locked) {
      expect(screen.queryByLabelText(`${row.name} 엿보기`)).toBeNull();
    }
  });
});
