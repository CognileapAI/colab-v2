// 지도 칸 폭 시험 도우미 (spec S-DEVICE-WIDTH-INPUT-20260926 「시험 결정」 신설 seam).
//
// jsdom 에는 `ResizeObserver` 도 레이아웃도 없다. 이 도우미는 가짜 `ResizeObserver` 를 전역에
// 심고, **관찰 대상이 지도 구역(`section.pv-map`)일 때만** 항목의 `contentRect.width` 로 폭을
// 알린다. 맨 위 메뉴처럼 다른 관찰 대상에는 알리지 않는다.
// 콜백이 실제로 불렸는지(`calls()`)를 시험이 단언한다 — 도우미가 심겼는데 아무도 관찰하지 않아
// 「모름」 배치로 통과하는 green-by-skip 을 막는다. 전역 되돌리기는 `restore()`
// (`vi.unstubAllGlobals`)가 한다. 도우미를 심지 않은 시험은 폭 「모름」이라 지금 배치 그대로다.
import { act } from '@testing-library/react';
import { vi } from 'vitest';

type Entry = { target: Element; contentRect: { width: number; height: number } };
type Callback = (entries: Entry[], observer: unknown) => void;
type Watch = { cb: Callback; target: Element; observer: unknown };

export interface MapCellWidth {
  /** 관찰 중인 지도 구역 전부에 새 폭을 알린다(`act` 안). */
  setWidth(width: number): void;
  /** 지도 구역으로 콜백을 부른 횟수. */
  calls(): number;
  restore(): void;
}

export function installMapCellWidth(initial: number): MapCellWidth {
  let width = initial;
  let calls = 0;
  const watched = new Set<Watch>();
  const notify = (w: Watch) => {
    calls += 1;
    w.cb([{ target: w.target, contentRect: { width, height: 0 } }], w.observer);
  };

  class FakeResizeObserver {
    private readonly cb: Callback;
    private readonly mine = new Set<Watch>();
    constructor(cb: Callback) {
      this.cb = cb;
    }
    observe(target: Element) {
      if (!target.matches('section.pv-map')) return;
      const w = { cb: this.cb, target, observer: this };
      this.mine.add(w);
      watched.add(w);
      notify(w);
    }
    unobserve(target: Element) {
      for (const w of Array.from(this.mine)) {
        if (w.target === target) {
          this.mine.delete(w);
          watched.delete(w);
        }
      }
    }
    disconnect() {
      for (const w of Array.from(this.mine)) watched.delete(w);
      this.mine.clear();
    }
  }

  vi.stubGlobal('ResizeObserver', FakeResizeObserver);
  return {
    setWidth(next: number) {
      width = next;
      act(() => {
        for (const w of Array.from(watched)) notify(w);
      });
    },
    calls: () => calls,
    restore: () => vi.unstubAllGlobals(),
  };
}

/** 입력 방식 스텁 — 매체 질의 스텁 선례(design-fix 20260924 L3b). 받은 질의를 기록한다. */
export function stubPointer(coarse: boolean): { queries: string[] } {
  const queries: string[] = [];
  vi.stubGlobal('matchMedia', (q: string) => {
    queries.push(q);
    return {
      matches: coarse && q === '(pointer: coarse)',
      media: q,
      onchange: null,
      addEventListener: () => {},
      removeEventListener: () => {},
      addListener: () => {},
      removeListener: () => {},
      dispatchEvent: () => false,
    };
  });
  return { queries };
}
