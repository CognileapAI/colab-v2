// 업로드 미리보기 「미리보기 그리기」(`up-preview-draw`)를 **누를 수 있게 된 뒤에** 누른다.
//
// ⭑ ⟨design-fix 20260924 · F-ci⟩ 버튼은 `uploadId` 만 있으면 첫 렌더부터 서지만, 팔레트는
//   `source.palettes()` 가 끝나야 채워진다. 버튼이 보이자마자 누르면 그 클릭은 버려지고
//   (`draw()` 첫 줄 `if (!uploadId || !palette) return;`) 뒤에 무한히 기다려도 그려지지 않는다
//   — PR #141 CI `frontend-gates` 의 `data-preview-slot-state="idle"` 두 건이 이 경합이다.
//   제품은 팔레트 준비 전 버튼을 `disabled` 로 두고, 시험은 **활성화를 기다린 뒤** 누른다.
//   「보이면 누른다」로 되돌리지 않는다 — 대기 한도를 늘려도 버려진 클릭은 복구되지 않는다.
//   같은 `draw()` 를 부르는 「짝 파일 없이 그려 보기」(`up-preview-without-grid`)도 같은 경합이라
//   `testId` 로 그 버튼을 지정해 같은 방식으로 누른다.
import { fireEvent, screen, waitFor, type waitForOptions } from '@testing-library/react';

const DEFAULT_TEST_ID = 'up-preview-draw';

export async function clickPreviewDrawWhenReady(
  options: {
    /** 기다림 옵션 — 종전 자리가 `findByTestId` 에 넘기던 값을 그대로 넘긴다(없으면 기본값). */
    wait?: waitForOptions;
    /** 누르는 방식 — 파일 고유의 `click`(누른 뒤 `act` 한 바퀴 등)이 있으면 그것을 쓴다. */
    click?: (button: HTMLElement) => unknown;
    /** 누를 버튼 — 기본 `up-preview-draw`. 같은 `draw()` 경로의 `up-preview-without-grid` 도 받는다. */
    testId?: string;
  } = {},
): Promise<HTMLButtonElement> {
  const testId = options.testId ?? DEFAULT_TEST_ID;
  const button = await waitFor(() => {
    const el = screen.getByTestId(testId) as HTMLButtonElement;
    if (el.disabled) throw new Error(`${testId} is still disabled (palettes not ready)`);
    return el;
  }, options.wait);
  await (options.click ?? fireEvent.click)(button);
  return button;
}
