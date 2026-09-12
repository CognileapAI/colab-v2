import { useEffect, useRef } from 'react';

// Only the most recently mounted dialog owns keyboard focus (nested dialogs included).
const stack: HTMLElement[] = [];
const selector = 'button, a[href], input, select, textarea, [tabindex]';
function controls(root: HTMLElement) {
  return Array.from(root.querySelectorAll<HTMLElement>(selector)).filter((el) =>
    el.tabIndex >= 0 && !el.matches(':disabled') && !el.closest('[hidden], [inert], [aria-hidden="true"]') &&
    getComputedStyle(el).display !== 'none' && getComputedStyle(el).visibility !== 'hidden');
}
export function useDialogFocus(onClose: () => void, busy = false, open = true) {
  const ref = useRef<HTMLDivElement>(null);
  const current = useRef({ onClose, busy });
  current.current = { onClose, busy };
  useEffect(() => {
    const root = ref.current;
    if (!open || !root) return;
    const trigger = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    stack.push(root);
    const activeStack = () => stack.filter((el) => !el.closest('[hidden], [inert], [aria-hidden="true"]'));
    const top = () => activeStack().at(-1) === root;
    const first = () => controls(root)[0] ?? root;
    first().focus();
    const keydown = (event: KeyboardEvent) => {
      if (!top() || event.defaultPrevented) return;
      if (event.key === 'Escape') {
        event.preventDefault();
        event.stopPropagation();
        if (!current.current.busy) current.current.onClose();
      } else if (event.key === 'Tab') {
        const list = controls(root);
        const head = list[0] ?? root;
        const tail = list.at(-1) ?? root;
        if (!root.contains(document.activeElement) || (event.shiftKey ? document.activeElement === head : document.activeElement === tail) || document.activeElement === root) {
          event.preventDefault(); (event.shiftKey ? tail : head).focus();
        }
      }
    };
    const focusin = (event: FocusEvent) => {
      if (top() && event.target instanceof Node && !root.contains(event.target)) first().focus();
    };
    document.addEventListener('keydown', keydown);
    document.addEventListener('focusin', focusin);
    return () => {
      document.removeEventListener('keydown', keydown);
      document.removeEventListener('focusin', focusin);
      const owned = top();
      const index = stack.indexOf(root);
      if (index >= 0) stack.splice(index, 1);
      if (owned) {
        const parent = activeStack().at(-1);
        if (trigger?.isConnected && (!parent || parent.contains(trigger))) trigger.focus();
        else if (parent) (controls(parent)[0] ?? parent).focus();
        else {
          const fallback = document.querySelector<HTMLElement>('main, h1, [data-screen]');
          if (fallback) {
            const previous = fallback.getAttribute('tabindex');
            fallback.tabIndex = -1; fallback.focus();
            if (previous === null) fallback.removeAttribute('tabindex');
            else fallback.setAttribute('tabindex', previous);
          }
        }
      }
    };
  }, [open]);
  return ref;
}
