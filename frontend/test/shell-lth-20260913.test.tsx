/**
 * 상단 셸 3건 — 이태헌 1차 검증 `D-1`·`D-5`·`I-9`
 * 오라클 = `dev-package/prd/rounds/R-LTH-REVIEW-1.md` Task 6 · spec `§8-2` 1~4.
 *
 *   ⑴ 「전체 연구실 (읽기 전용)」이 `button` 이 아니고 키보드 초점을 받지 않는다 (`D-1`)
 *   ⑵ 「내 계정 · 〈이름〉」 자리에 `▾` 가 없고 `button` 이 아니다 (`D-5`)
 *   ⑶ 좁은 폭에서 「더보기」 목록이 업로드·계정 관리·연구실 설정을 **글자로** 말한다 (`I-9`)
 *
 * jsdom 은 레이아웃을 계산하지 않는다 — 폭 조건(어느 단에서 접히는가)은 **CSS 원문 계측**으로
 * 따로 세우고 DOM 단언과 섞지 않는다 (`CLAUDE.md §5-b` 오탐 3건 · spec `§8-1`).
 * fireEvent 를 쓴다 — user-event 를 새로 들이지 않는다(집 관례).
 */
// @ts-expect-error — 타입 선언 없이 런타임만 쓴다(vitest 는 node 위에서 돈다 · `design-fix-20260908` 와 같은 규율).
import { readFileSync } from 'node:fs';
// @ts-expect-error — 같은 이유.
import { resolve } from 'node:path';
import { act, fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { Gnb } from '../src/shell/Gnb';
import { UploadEntry } from '../src/components/upload/UploadEntry';
import { SessionProvider } from '../src/permission/session';
import { account } from './factories';
import type { CurrentAccount } from '../src/api/client';
import type { UploadSources } from '../src/components/upload/types';

declare const process: { cwd(): string };

/** 주석은 걷어내고 읽는다 — 주석 속 선택자가 계측에 섞이지 않게 한다 (spec `§8-6` ⑷). */
const read = (rel: string): string =>
  String(readFileSync(resolve(process.cwd(), rel), 'utf8')).replace(/\/\*[\s\S]*?\*\//g, '');

const SHELL = read('src/shell/shell.css');
const DESIGN = read('src/shell/design-system.css');

/** `@media (…)` 블록들을 원문에서 잘라 이어 붙인다. */
function mediaBlock(css: string, query: string): string {
  const out: string[] = [];
  let from = 0;
  for (;;) {
    const at = css.indexOf(query, from);
    if (at < 0) break;
    const open = css.indexOf('{', at);
    let depth = 0;
    let i = open;
    for (; i < css.length; i += 1) {
      if (css[i] === '{') depth += 1;
      else if (css[i] === '}') {
        depth -= 1;
        if (depth === 0) break;
      }
    }
    out.push(css.slice(open + 1, i));
    from = i + 1;
  }
  expect(out.length, `미디어 질의 부재: ${query}`).toBeGreaterThan(0);
  return out.join('\n');
}

function renderGnb(acc: CurrentAccount) {
  return render(
    <MemoryRouter initialEntries={['/lab']}>
      <SessionProvider account={acc}>
        <Gnb />
      </SessionProvider>
    </MemoryRouter>,
  );
}

/** 상단 기능 3개가 전부 보이는 사람 — 운영자 ＋ 업로드·편집 ＋ 연구실 설정. */
function fullAccount(): CurrentAccount {
  return {
    ...account({ '업로드·편집': true, '연구실 설정': true }),
    canManageServiceAccounts: true,
  };
}

function openMore() {
  const more = screen.getByTestId('gnb-more');
  fireEvent.click(more);
  return more;
}

/* ───────────────────────────────────────── ⑴ 연구실 표기 = 비대화형 칩 (D-1) */
describe('D-1 — 「전체 연구실 (읽기 전용)」은 누를 수 없는 상태 표시다', () => {
  it('`lab-switcher` 가 `button` 이 아니다', () => {
    renderGnb(fullAccount());
    expect(screen.getByTestId('lab-switcher').tagName).not.toBe('BUTTON');
  });

  it('`lab-switcher` 가 키보드 초점을 받지 않는다 — `tabindex` 도 대화형 태그도 없다', () => {
    renderGnb(fullAccount());
    const chip = screen.getByTestId('lab-switcher');
    expect(chip.getAttribute('tabindex')).toBeNull();
    expect(['BUTTON', 'A', 'INPUT', 'SELECT', 'TEXTAREA']).not.toContain(chip.tagName);
    // 안쪽에도 초점 받는 것을 숨겨 두지 않는다.
    expect(chip.querySelector('button, a, input, select, textarea, [tabindex]')).toBeNull();
  });

  it('범위 문면은 그대로다 — 「전체 연구실」 ＋ 보이는 「(읽기 전용)」', () => {
    renderGnb(fullAccount());
    const chip = screen.getByTestId('lab-switcher');
    expect(chip).toHaveTextContent('전체 연구실');
    expect(chip.querySelector('.ln-ro')).toHaveTextContent('읽기 전용');
  });
});

/* ───────────────────────────────────────── ⑵ 사용자 이름 = 표시 (D-5) */
describe('D-5 — 「내 계정 · 〈이름〉」은 메뉴를 약속하지 않는다', () => {
  it('`gnb-avatar` 하위에 `▾` 가 0건이다', () => {
    renderGnb(fullAccount());
    const av = screen.getByTestId('gnb-avatar');
    expect(av.textContent).not.toMatch(/▾/);
    expect(av.querySelector('.cv')).toBeNull();
  });

  it('`gnb-avatar` 가 `button` 이 아니고 초점을 받지 않는다', () => {
    renderGnb(fullAccount());
    const av = screen.getByTestId('gnb-avatar');
    expect(av.tagName).not.toBe('BUTTON');
    expect(av.getAttribute('tabindex')).toBeNull();
  });

  it('이름은 글자로 남는다', () => {
    renderGnb(fullAccount());
    expect(screen.getByTestId('gnb-avatar')).toHaveTextContent('호랑이');
  });

  it('로그아웃은 그대로 버튼이다 — 나가는 길을 같이 걷지 않는다', () => {
    renderGnb(fullAccount());
    expect(screen.getByTestId('gnb-logout').tagName).toBe('BUTTON');
  });
});

/* ───────────────────────────────────────── ⑶ 더보기 목록 (I-9) */
describe('I-9 — 좁은 폭 상단 기능의 이름이 글자로 확인된다', () => {
  it('「더보기」를 열면 업로드·계정 관리·연구실 설정이 글자로 선다', () => {
    renderGnb(fullAccount());
    const more = openMore();
    const list = screen.getByTestId('gnb-more-list');
    expect(more.getAttribute('aria-expanded')).toBe('true');
    for (const name of ['업로드', '계정 관리', '연구실 설정']) {
      expect(list.textContent).toContain(name);
    }
  });

  it('열기 전에는 목록이 없고 `aria-expanded` 가 false 다', () => {
    renderGnb(fullAccount());
    const more = screen.getByTestId('gnb-more');
    expect(more.getAttribute('aria-expanded')).toBe('false');
    expect(screen.queryByTestId('gnb-more-list')).toBeNull();
  });

  it('목록 항목은 그림과 글자를 함께 낸다 — 그림만 남기지 않는다', () => {
    renderGnb(fullAccount());
    openMore();
    const items = [...screen.getByTestId('gnb-more-list').querySelectorAll('.gnb-more-item')];
    expect(items).toHaveLength(3);
    for (const item of items) {
      expect(item.querySelector('svg')).not.toBeNull();
      expect(item.querySelector('.lbl')?.textContent?.trim()).toBeTruthy();
      expect(item.getAttribute('aria-label')).toBeTruthy();
    }
  });

  it('「더보기」는 진짜 `button` 이다 — Enter·Space 가 브라우저 기본으로 선다', () => {
    renderGnb(fullAccount());
    const more = screen.getByTestId('gnb-more');
    expect(more.tagName).toBe('BUTTON');
    expect(more.getAttribute('type')).toBe('button');
    expect(more.getAttribute('aria-label')).toBe('더보기');
  });

  it('Esc 로 닫고 초점이 「더보기」로 돌아온다', () => {
    renderGnb(fullAccount());
    const more = openMore();
    expect(screen.getByTestId('gnb-more-list')).toBeInTheDocument();
    fireEvent.keyDown(screen.getByTestId('gnb-more-list'), { key: 'Escape' });
    expect(screen.queryByTestId('gnb-more-list')).toBeNull();
    expect(document.activeElement).toBe(more);
  });

  it('권한이 있는 항목만 목록에 선다 — 기존 권한 분기를 승계한다', () => {
    renderGnb(account({ '업로드·편집': true })); // 운영자 아님 · 연구실 설정 꺼짐
    openMore();
    const list = screen.getByTestId('gnb-more-list');
    expect(list.textContent).toContain('업로드');
    expect(list.textContent).not.toContain('계정 관리');
    expect(list.textContent).not.toContain('연구실 설정');
  });

  it('담을 항목이 하나도 없으면 「더보기」 자체가 서지 않는다 — 빈 목록을 열게 하지 않는다', () => {
    renderGnb(account()); // 업로드·편집 꺼짐 · 연구실 설정 꺼짐 · 운영자 아님
    expect(screen.queryByTestId('gnb-more')).toBeNull();
  });

  it('계정 관리·연구실 설정 항목은 각 화면으로 가는 링크다', () => {
    renderGnb(fullAccount());
    openMore();
    expect(screen.getByTestId('gnb-more-account-admin').getAttribute('href')).toBe('/account-admin');
    expect(screen.getByTestId('gnb-more-lab-settings').getAttribute('href')).toBe('/lab-settings');
  });
});

/* 목록의 업로드 항목은 **동작이 있다** — 비어 있는 자리를 새로 만들지 않는다. */
describe('I-9 — 목록의 「업로드」가 업로드 모달을 연다', () => {
  const fakeSources = () =>
    ({
      upload: { async status() { return null; } },
      preview: { async palettes() { return []; } },
      projects: { async list() { return []; } },
      lineage: {},
    } as unknown as UploadSources);

  it('`gnb-more-upload` 를 누르면 `upload-modal` 이 선다', async () => {
    render(
      <MemoryRouter initialEntries={['/lab']}>
        <SessionProvider account={fullAccount()}>
          <UploadEntry variant="menu" sources={fakeSources()} />
        </SessionProvider>
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByTestId('gnb-more-upload'));
    await act(async () => {});
    expect(screen.getByTestId('upload-modal')).toBeInTheDocument();
  });
});

/* ───────────────────────────────────────── 폭 조건 = CSS 원문 계측 (DOM 과 분리) */
describe('I-9 폭 조건 — 접는 단이 CSS 에 서 있다', () => {
  it('데스크톱 기본에서 「더보기」는 숨는다', () => {
    expect(SHELL).toMatch(/\.gnb-more\s*\{[^}]*display:\s*none/);
  });

  it('900px 단에서 「더보기」가 서고 기능 버튼이 접힌다', () => {
    const at900 = mediaBlock(DESIGN, '@media (max-width: 900px)');
    expect(at900).toMatch(/\.gnb-more\s*\{[^}]*display:\s*inline-flex/);
    expect(at900).toMatch(/\.gnb-upload[^{]*\{[^}]*display:\s*none|:is\([^)]*gnb-upload[^)]*\)[^{]*\{[^}]*display:\s*none/);
    expect(at900).toMatch(/\.gnb-settings[^{]*\{[^}]*display:\s*none|:is\([^)]*gnb-settings[^)]*\)[^{]*\{[^}]*display:\s*none/);
  });

  it('주 내비 라벨 보존 규칙은 그대로다 — 560px 단에서 감추지 않고 굴린다', () => {
    const at560 = mediaBlock(SHELL, '@media (max-width: 560px)');
    expect(at560).toMatch(/\.mainnav\s*\{[^}]*overflow-x:\s*auto/);
    // 감추면 안 되는 것 = 주 내비 자체·그 링크·그 라벨.
    // (`.mainnav::-webkit-scrollbar { display: none }` 은 스크롤 막대라 여기 걸리지 않는다.)
    expect(at560).not.toMatch(/\.mainnav\s*\{[^}]*display:\s*none/);
    expect(at560).not.toMatch(/\.mainnav\s+a[^{]*\{[^}]*display:\s*none/);
    expect(at560).not.toMatch(/\.gnb\s+\.lbl\s*\{[^}]*display:\s*none/);
  });

  it('휴대전화에서 아바타를 다시 보이게 하지 않는다', () => {
    const at640 = mediaBlock(DESIGN, '@media (max-width: 640px)');
    expect(at640).toMatch(/\.gnb\s+\.avatar\s*\{[^}]*display:\s*none/);
  });
});
