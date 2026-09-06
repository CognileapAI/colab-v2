// WU-A13R · PRD-43 — 공통 토스트 한 개와 문면 21행.
//
// 수용 기준 축자(PRD-43) 넷을 그대로 잰다.
//   ⑴ 토스트가 한 줄로 뜨고 **스스로 사라지며 포커스를 뺏지 않는다**
//   ⑵ 21행이 전부 코드에 있고 **하드코드 중복이 0건**이다(한 곳에서 온다)
//   ⑶ `F-11`·`D-13` 의 건수가 **보간값**이고 고정 숫자가 아니다
//   ⑷ `D-07` 축약 표기가 `2025-06 ~ 09` 다
//
// ⛔ 문면은 PRD-43 표(그리고 그 표가 가리키는 rev2 원문)에서 **축자로** 떴다.
//    한 글자도 고쳐 적지 않는다 — 고칠 사유를 찾으면 구현하지 말고 보고한다.
import { useEffect, useState } from 'react';
import { act, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { TOAST_DISMISS_MS, Toast } from '../src/components/common/Toast';
import * as copy from '../src/components/common/toastCopy';
import { COPY_ROWS, COPY_ROW_IDS } from '../src/components/common/toastCopy';
import { formatPeriod } from '../src/components/detail/format';

afterEach(() => {
  vi.useRealTimers();
});

describe('PRD-43 ⑵ — 21행이 한 곳에 있다', () => {
  it('표의 행 id 가 정확히 21개다 — 21 미만이면 red 다', () => {
    // 대상 0건이 통과로 새지 않게 **길이를 단언한다**(spec `R-A2.md` green-by-skip 방지).
    expect(COPY_ROW_IDS).toHaveLength(21);
    expect(new Set(COPY_ROW_IDS).size).toBe(21);
    expect([...COPY_ROW_IDS]).toEqual([
      'U-14', 'U-17', 'P-06', 'P-07', 'V-01', 'B-10', 'B-32',
      'L-08', 'L-11', 'L-14', 'J-08', 'J-12', 'F-11',
      'S-04', 'S-05', 'X-05', 'D-01', 'D-07', 'D-13', 'N-11', 'E-07',
    ]);
  });

  it('행마다 자리와 문면이 비어 있지 않다 — 「자리만 있고 말이 없는」 행을 세지 않는다', () => {
    for (const id of COPY_ROW_IDS) {
      const row = COPY_ROWS[id];
      expect(row.place.length, id).toBeGreaterThan(0);
      expect(row.texts.length, id).toBeGreaterThan(0);
      for (const t of row.texts) expect(t.trim().length, `${id} · ${t}`).toBeGreaterThan(0);
    }
  });

  it('21행의 문면이 PRD-43 축자 그대로다', () => {
    // U-14 분석 상태 칩
    expect(copy.ANALYZING_CHIP).toBe('분석 중');
    expect(copy.ANALYZED_CHIP).toBe('분석 완료');
    // U-17
    expect(copy.UPLOAD_DONE).toBe('파일을 올렸어요. 등록을 시작할 수 있어요');
    // P-06
    expect(copy.PREVIEW_DREW_ONE).toBe('파일에서 바로 한 장을 그렸어요');
    // P-07 업로드 미리보기 푸터
    expect(copy.UPLOAD_PREVIEW_FOOT).toBe(
      '첫 변수를 미리 그렸어요 · 확장보기(⤢)에서 확대하고 좌표를 읽을 수 있어요',
    );
    // V-01 뷰어 머리 ＋ 힌트
    expect(copy.viewerHead('EPSG:5179')).toBe('EPSG:5179 · PNG + 경계 좌표');
    expect(copy.VIEWER_HINT).toBe('휠로 확대하고 끌어서 움직여요');
    // B-10
    expect(copy.PERIOD_CLEARED).toBe('기간을 지웠어요');
    expect(copy.PERIOD_START_NEEDED).toBe('시작할 날을 골라 주세요');
    // B-32
    expect(copy.THUMB_REPLACED).toBe('직접 올린 그림으로 바꿨어요');
    expect(copy.THUMB_RESTORED).toBe('자동 생성본으로 되돌렸어요');
    // L-08 · L-11 · L-14
    expect(copy.LINK_REMOVED).toBe('연결을 지웠어요');
    expect(copy.LINK_ADDED).toBe('직접 연결했어요. 계보에 들어가요');
    expect(copy.UNRECORDED_ON).toBe('기록 없음으로 표시했어요');
    expect(copy.UNRECORDED_OFF).toBe('기록 없음 표시를 지웠어요');
    // J-08 · J-12
    expect(copy.PROJECT_UNPICKED).toBe('프로젝트 지정을 뺐어요');
    expect(copy.QUICK_PROJECT_NOTE).toBe('유형과 이름만 받아요. 나머지는 프로젝트 화면에서 채워요.');
    // S-04 — PRD 표는 `…` 로 줄였고, 축자는 rev2 원문에서 떴다
    expect(copy.STAGE_TOO_HIGH).toBe(
      '이 데이터보다 높은 단계라 연결할 수 없어요. 분류에서 가공 단계를 확인해 주세요',
    );
    // S-05 · X-05
    expect(copy.PICK_TARGET_FIRST).toBe('연결할 데이터를 먼저 골라 주세요');
    // D-01 · N-11
    expect(copy.BACK_TO_ORIGIN).toBe('들어온 곳으로 돌아가요. 필터와 스크롤 위치는 그대로예요');
    expect(copy.LINEAGE_GRAPH_HINT).toBe('각 데이터를 누르면 그 상세로 가요');
    // E-07 편집 토스트 **3종**
    expect(copy.EDIT_MODE_ON).toBe('편집 모드예요. 값을 고치고 저장을 누르세요');
    expect(copy.EDIT_SAVED).toBe('편집 내용을 저장했어요');
    expect(copy.EDIT_CANCELED).toBe('편집을 취소했어요');
    expect(COPY_ROWS['E-07'].texts).toHaveLength(3);
  });

  it('`S-05` 와 `X-05` 는 같은 문면이라 **한 곳에서 온다** — 두 번 적지 않는다', () => {
    expect(copy.PICK_TARGET_FIRST_IN_EDIT).toBe(copy.PICK_TARGET_FIRST);
  });

  it('하드코드 중복 0건 — 21행의 문면이 상수 모듈 밖 `src/` 에 문자열로 다시 있지 않다', () => {
    // 「한 곳에서 온다」를 **선언이 아니라 실측**으로 잰다. `node:fs` 는 쓰지 않는다
    // (`e01-apply-points.test.ts:14` 의 배포 불가 사고) — vite 의 `?raw` 글롭으로 읽는다.
    const sources = import.meta.glob('../src/**/*.{ts,tsx}', {
      query: '?raw',
      import: 'default',
      eager: true,
    }) as Record<string, string>;
    expect(Object.keys(sources).length).toBeGreaterThan(50);

    const HOME = 'toastCopy.ts';
    // 보간행(`F-11`·`D-13`·`V-01` 머리·`D-07` 예시)은 인자에 따라 값이 달라 문자열 검색의
    // 대상이 아니다 — 대상 목록은 상수 모듈이 스스로 내보낸다(시험이 따로 적으면 두 벌이 된다).
    expect(copy.FIXED_COPY.length).toBeGreaterThanOrEqual(20);

    // **따옴표 안쪽 전체가 같을 때만** 중복이다. 부분 문자열로 세면 같은 말로 시작하는
    // 남의 문장(`편집을 취소했어요. 권한은 그대로예요` · `MemberPermissionGrid.tsx:67`)이
    // 걸리고, 그것을 이 상수로 바꾸면 **다른 자리 둘이 한 문면에 묶인다** — PRD-43 이
    // 한 자리의 문면을 고칠 때 무관한 화면이 함께 바뀐다.
    const literal = (text: string) =>
      new RegExp(`(['"\`])${text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\1`);

    const duplicates: string[] = [];
    for (const [path, src] of Object.entries(sources)) {
      if (path.endsWith(HOME)) continue;
      for (const text of copy.FIXED_COPY) {
        if (literal(text).test(src)) duplicates.push(`${path} ← «${text}»`);
      }
    }
    expect(duplicates).toEqual([]);
  });
});

describe('PRD-43 ⑶ — `F-11`·`D-13` 은 보간값이다', () => {
  it('`F-11` 계보 건수가 인자로 들어간다 — 고정 숫자가 아니다', () => {
    expect(copy.datasetCreated(3)).toBe('데이터셋을 만들었어요 (계보 연결 3건). 상세 화면으로 넘어가요');
    expect(copy.datasetCreated(0)).toBe('데이터셋을 만들었어요 (계보 연결 0건). 상세 화면으로 넘어가요');
    expect(copy.datasetCreated(3)).not.toBe(copy.datasetCreated(12));
  });

  it('`D-13` 본체 건수가 인자로 들어간다', () => {
    expect(copy.bodyPieceHead(4)).toBe('본체 4개 · 같은 데이터를 월로 자른 조각이에요');
    expect(copy.bodyPieceHead(1)).toBe('본체 1개 · 같은 데이터를 월로 자른 조각이에요');
    expect(copy.bodyPieceHead(4)).not.toBe(copy.bodyPieceHead(9));
  });
});

describe('PRD-43 ⑷ — `D-07` 축약 표기', () => {
  it('기간 `2025-06-01 ~ 2025-09-30` · 단위 `월` 이면 `2025-06 ~ 09` 다', () => {
    expect(
      formatPeriod({
        start: '2025-06-01T00:00:00Z',
        end: '2025-09-30T00:00:00Z',
        granularity: '월',
      }),
    ).toBe('2025-06 ~ 09');
  });

  it('해가 다르면 줄이지 않는다 — 「겹치면」이 조건이다', () => {
    expect(
      formatPeriod({
        start: '2024-11-01T00:00:00Z',
        end: '2025-03-31T00:00:00Z',
        granularity: '월',
      }),
    ).toBe('2024-11 ~ 2025-03');
  });

  it('상수 표의 `D-07` 예시가 그 축약값과 같다 — 표와 화면이 갈리지 않는다', () => {
    expect(COPY_ROWS['D-07'].texts).toContain('2025-06 ~ 09');
  });
});

describe('PRD-43 ⑴ — 토스트는 스스로 사라지고 포커스를 뺏지 않는다', () => {
  it('한 줄이 뜨고 `role="status"` 인 공손한 알림 구역이다', () => {
    render(<Toast message={copy.UPLOAD_DONE} testId="t-one" />);
    const el = screen.getByTestId('t-one');
    expect(el).toHaveTextContent(copy.UPLOAD_DONE);
    expect(el).toHaveAttribute('role', 'status');
    expect(el).toHaveAttribute('aria-live', 'polite');
  });

  it('스스로 사라진다 — 아무도 누르지 않아도 없어진다', () => {
    vi.useFakeTimers();
    render(<Toast message={copy.LINK_REMOVED} testId="t-gone" />);
    expect(screen.getByTestId('t-gone')).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(TOAST_DISMISS_MS + 10);
    });
    expect(screen.queryByTestId('t-gone')).toBeNull();
  });

  it('포커스를 뺏지 않는다 — 떠 있던 자리에 그대로 있다', () => {
    function Harness() {
      const [shown, setShown] = useState(false);
      useEffect(() => {
        document.getElementById('anchor')?.focus();
      }, []);
      return (
        <div>
          <button id="anchor" type="button" onClick={() => setShown(true)}>
            닻
          </button>
          {shown && <Toast message={copy.PERIOD_CLEARED} testId="t-focus" />}
        </div>
      );
    }
    render(<Harness />);
    const anchor = document.getElementById('anchor') as HTMLButtonElement;
    expect(document.activeElement).toBe(anchor);

    act(() => {
      anchor.click();
    });
    const toast = screen.getByTestId('t-focus');
    // ⑴ 포커스가 그대로다 ⑵ 탭 순서에도 끼어들지 않는다(`tabindex` 를 달지 않는다)
    expect(document.activeElement).toBe(anchor);
    expect(toast).not.toHaveAttribute('tabindex');
    expect(toast).not.toHaveAttribute('autofocus');
  });

  it('문면이 바뀌면 사라짐 시계가 다시 선다 — 뒤 토스트가 앞 시계에 잘리지 않는다', () => {
    vi.useFakeTimers();
    const { rerender } = render(<Toast message={copy.LINK_REMOVED} testId="t-reset" />);
    act(() => {
      vi.advanceTimersByTime(TOAST_DISMISS_MS - 100);
    });
    rerender(<Toast message={copy.LINK_ADDED} testId="t-reset" />);
    act(() => {
      vi.advanceTimersByTime(TOAST_DISMISS_MS - 100);
    });
    expect(screen.getByTestId('t-reset')).toHaveTextContent(copy.LINK_ADDED);

    act(() => {
      vi.advanceTimersByTime(200);
    });
    expect(screen.queryByTestId('t-reset')).toBeNull();
  });
});
