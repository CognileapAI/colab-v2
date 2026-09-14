/**
 * L4 · 프로젝트 카드 접근성 — R-LTH-REVIEW-1 Task 4 (판정 카드 ⑥ ⓐ · `D-2`).
 *
 * 오라클 = 라운드 파일 `Task 4` 목적 ⑴ · spec `§8-2` 13·14 · `§8-6` ⑴.
 * 잰다 = ⑴ 카드가 링크 역할이고 Tab 초점을 받는다 ⑵ Enter 로 `onOpen` 이 1회 불린다
 *        ⑶ 마우스 동작 무변 ⑷ `project.css` 원문에 `.pcard:focus-visible` 규칙 존재.
 * jsdom 은 레이아웃을 계산하지 않으므로 초점 링의 **보임**은 CSS 원문 계측으로 가른다
 * (`CLAUDE.md §5-b` 오탐 3건 · 주석 제거 후 존재 단언).
 */
import { fireEvent, render, screen, within } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ProjectCards } from '../src/components/project/ProjectCards';
import { FIXTURE_PROJECTS, rowOf } from '../src/components/project/fixture';
// 규칙 원문 — `vite.config.ts` 의 `test.css.include` 가 `?raw` id 를 허용해야 비지 않는다.
import projectCss from '../src/components/project/project.css?raw';

const ROW = rowOf(FIXTURE_PROJECTS[0]!);

/** 주석을 걷어낸 규칙 원문 — 주석 속 선택자가 계측에 섞이지 않도록 (`§8-6` ⑷). */
const CSS = projectCss.replace(/\/\*[\s\S]*?\*\//g, '');

describe('§5 프로젝트 카드 — 키보드만으로 열리고 초점이 보인다 (카드 ⑥ ⓐ)', () => {
  it('카드가 링크 역할이고 Tab 초점을 받으며 Enter 로 상세가 열린다', () => {
    const onOpen = vi.fn();
    render(<ProjectCards rows={[ROW]} onOpen={onOpen} />);

    const card = screen.getByTestId(`project-card-${ROW.projectId}`);
    // 역할 — `<a href>` 든 `role="link"` 든 보조기기에 링크로 읽힌다.
    expect(screen.getByRole('link')).toBe(card);

    // 초점 — 마우스 없이 카드에 닿는다.
    card.focus();
    expect(document.activeElement).toBe(card);

    // 활성 — Enter 한 번에 한 번만 연다.
    fireEvent.keyDown(card, { key: 'Enter' });
    expect(onOpen).toHaveBeenCalledTimes(1);
    expect(onOpen).toHaveBeenCalledWith(ROW.projectId);
  });

  it('마우스 동작은 그대로다 — 눌러도 같은 값으로 한 번 연다', () => {
    const onOpen = vi.fn();
    render(<ProjectCards rows={[ROW]} onOpen={onOpen} />);

    fireEvent.click(screen.getByTestId(`project-card-${ROW.projectId}`));
    expect(onOpen).toHaveBeenCalledTimes(1);
    expect(onOpen).toHaveBeenCalledWith(ROW.projectId);
  });

  it('현행 `<article onClick>` 꼴은 이 단언을 통과하지 못한다 (`§8-6` ⑴ green-by-skip 방지)', () => {
    const onOpen = vi.fn();
    render(
      <article className="pcard" data-testid="legacy-card" onClick={() => onOpen('p-legacy')}>
        <h3>옛 카드</h3>
      </article>,
    );

    const legacy = screen.getByTestId('legacy-card');
    expect(screen.queryByRole('link')).toBeNull();
    legacy.focus();
    expect(document.activeElement).not.toBe(legacy);
    fireEvent.keyDown(legacy, { key: 'Enter' });
    expect(onOpen).not.toHaveBeenCalled();
  });

  it('`project.css` 원문에 `.pcard:focus-visible` 규칙이 있다 (주석 제거 후 계측)', () => {
    expect(CSS).toContain('.pcard:focus-visible');
    // 초점 표시는 테두리 굵기가 아니라 `outline` 이다 — 레이아웃을 밀지 않는다.
    const at = CSS.indexOf('.pcard:focus-visible');
    const block = CSS.slice(CSS.indexOf('{', at), CSS.indexOf('}', at));
    expect(block).toContain('outline');
  });

  it('카드 안에 두 번째 클릭 대상을 세우지 않는다 (`§8` 회귀)', () => {
    render(<ProjectCards rows={[ROW]} onOpen={vi.fn()} />);

    const cta = within(screen.getByTestId(`project-card-${ROW.projectId}`)).getByTestId('card-cta');
    expect(within(cta).queryByRole('link')).toBeNull();
    expect(within(cta).queryByRole('button')).toBeNull();
  });
});
