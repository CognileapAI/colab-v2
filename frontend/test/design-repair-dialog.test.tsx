import { useState } from 'react';
import { useDialogFocus } from '../src/components/common/useDialogFocus';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ProjectFormModal } from '../src/components/project/ProjectFormModal';

afterEach(cleanup);

describe('프로젝트 대화상자의 키보드 경계', () => {
  it('열리면 내부로 이동하고 양쪽 Tab 경계와 Escape를 처리한다', () => {
    const onClose = vi.fn();
    render(<><button>배경</button><ProjectFormModal mode={{kind: '새 프로젝트'}} onSubmit={async () => {}} onClose={onClose} /></>);
    const dialog = screen.getByRole('dialog');
    expect(dialog.contains(document.activeElement)).toBe(true);
    const first = screen.getByRole('button', {name: '창 닫기'});
    const last = screen.getByRole('button', {name: '만들기'});
    last.focus(); fireEvent.keyDown(last, {key: 'Tab'});
    expect(first).toHaveFocus();
    first.focus(); fireEvent.keyDown(first, {key: 'Tab', shiftKey: true});
    expect(last).toHaveFocus();
    fireEvent.keyDown(last, {key: 'Escape'});
    expect(onClose).toHaveBeenCalledTimes(1);
  });
  it('닫힌 뒤 원래 트리거로 포커스를 돌려준다', () => {
    const trigger = document.createElement('button');
    document.body.append(trigger); trigger.focus();
    const view = render(<ProjectFormModal mode={{kind: '새 프로젝트'}} onSubmit={async () => {}} onClose={() => {}} />);
    screen.getByRole('button', {name: '만들기'}).focus();
    view.unmount();
    expect(trigger).toHaveFocus(); trigger.remove();
  });
  it('저장 중 Escape로 닫히지 않는다', async () => {
    const onClose = vi.fn();
    render(<ProjectFormModal mode={{kind: '새 프로젝트'}} onSubmit={() => new Promise(() => {})} onClose={onClose} />);
    fireEvent.change(screen.getByLabelText('이름'), {target: {value: '검증용 프로젝트'}});
    fireEvent.click(screen.getByRole('button', {name: '만들기'}));
    fireEvent.keyDown(screen.getByRole('dialog'), {key: 'Escape'});
    expect(onClose).not.toHaveBeenCalled();
    expect(screen.getByRole('button', {name: '창 닫기'})).toBeDisabled();
  });
});

function Nested() {
  const [child, setChild] = useState(false);
  const ref = useDialogFocus(() => {});
  return <div role="dialog" aria-label="부모" ref={ref} tabIndex={-1}>
    <button onClick={() => setChild(true)}>자식 열기</button>
    {child && <Child close={() => setChild(false)} />}
    <button>부모 끝</button>
  </div>;
}
function Child({close}: {close: () => void}) {
  const ref = useDialogFocus(close);
  return <div role="dialog" aria-label="자식" ref={ref} tabIndex={-1}><button onClick={close}>자식 닫기</button></div>;
}
it('중첩 Escape는 자식만 닫고 부모 트리거로 복귀한다', () => {
  render(<Nested />);
  const trigger = screen.getByRole('button', {name: '자식 열기'});
  trigger.focus(); fireEvent.click(trigger);
  expect(screen.getByRole('button', {name: '자식 닫기'})).toHaveFocus();
  fireEvent.keyDown(document.activeElement!, {key: 'Escape'});
  expect(screen.queryByRole('dialog', {name: '자식'})).toBeNull();
  expect(trigger).toHaveFocus();
});
it('트리거가 제거됐으면 페이지 제목으로 복귀한다', () => {
  const trigger = document.createElement('button');
  document.body.append(trigger); trigger.focus();
  const heading = document.createElement('h1'); heading.textContent = '복귀 위치'; document.body.append(heading);
  const view = render(<ProjectFormModal mode={{kind:'새 프로젝트'}} onSubmit={async () => {}} onClose={() => {}} />);
  trigger.remove(); view.unmount();
  expect(heading).toHaveFocus(); expect(heading).not.toHaveAttribute('tabindex'); heading.remove();
});

it('만료된 보존 모달은 재로그인 입력의 포커스를 가로채지 않는다', () => {
 const onClose=vi.fn();render(<><section data-testid="preserved"><ProjectFormModal mode={{kind:'새 프로젝트'}} onSubmit={async()=>{}} onClose={onClose}/></section><input aria-label="재로그인 계정"/></>);
 const preserved=screen.getByTestId('preserved');preserved.setAttribute('inert','');preserved.setAttribute('aria-hidden','true');const login=screen.getByLabelText('재로그인 계정');login.focus();expect(login).toHaveFocus();fireEvent.keyDown(login,{key:'Escape'});expect(onClose).not.toHaveBeenCalled();preserved.removeAttribute('inert');preserved.removeAttribute('aria-hidden');fireEvent.focusIn(login);expect(screen.getByRole('dialog').contains(document.activeElement)).toBe(true);
});
