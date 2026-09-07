// ㈏ 기간 달력 팝오버 (WU-A6 → WU-B3 이관 · PRD-18 · rev2 `dr-pop` 축자).
//
// 지키는 것
//  - **고른 최소 단위까지만 칸이 열린다** — `일` 이면 시각 칸이 서지 않고, `분` 이면 시·분이 선다.
//    자리표의 정본은 `periodParts.PARTS` 하나다 — 여기서 두 번째 사다리를 만들지 않는다.
//  - **`Date` 로 날짜를 만들지 않는다**(`periodParts.ts` 산문) — 보는 사람의 시간대가 날짜를
//    하루 민다. 달력 격자는 요일 계산에만 `Date.UTC` 를 쓰고, 값은 문자열 자리로만 옮긴다.
//  - **적용을 누를 때만 바깥 값이 바뀐다.** 팝오버 안의 조작은 되돌릴 수 있어야 한다.
//  - ⛔ 종전 인라인 칸(`최소 단위` 셀렉트 ＋ 자리 칸)을 걷지 않는다 — 이 팝오버는 **더해진 길**이다.
//  - **Esc 는 이 층이 스스로 받는다**(⟨advisor ② · F2⟩). 열려 있는 동안
//    `data-esc-layer="기간"` 표식을 달아 업로드 모달이 Esc 를 먹지 않게 하고, 그 Esc 로
//    팝오버 하나만 닫는다 — 표식만 달고 Esc 를 안 받으면 Esc 가 무동작이 된다.
import { useCallback, useState } from 'react';
import { ESC_LAYER_ATTR, useEscLayer } from './escLayer';
import { GRANULARITIES, PARTS, partsFor, type PeriodParts } from './periodParts';

/** 그 달의 날 수 — 윤년 포함. 문자열 자리 계산이라 시간대가 끼지 않는다. */
function daysIn(year: number, month: number): number {
  return new Date(Date.UTC(year, month, 0)).getUTCDate();
}

function pad2(n: number): string {
  return String(n).padStart(2, '0');
}

/** 지금 화면에 세울 달 — 이미 고른 연·월이 있으면 그것, 없으면 오늘의 달. */
function initialMonth(parts: PeriodParts): { year: number; month: number } {
  const y = Number(parts.year);
  const m = Number(parts.month);
  const now = new Date();
  return {
    year: Number.isFinite(y) && y > 0 ? y : now.getUTCFullYear(),
    month: Number.isFinite(m) && m >= 1 && m <= 12 ? m : now.getUTCMonth() + 1,
  };
}

/** 달력 한 판 — 날 버튼만 낸다(빈 앞칸은 격자 자리만 차지한다). */
function MonthGrid(props: {
  year: number;
  month: number;
  side: 'start' | 'end';
  onPick: (day: number) => void;
}) {
  const count = daysIn(props.year, props.month);
  const lead = new Date(Date.UTC(props.year, props.month - 1, 1)).getUTCDay();
  return (
    <div className="dr-cal" data-testid={`reg-period-cal-${props.side}`}>
      <div className="dr-cal-h">{`${props.year}-${pad2(props.month)}`}</div>
      <div className="dr-cal-g">
        {Array.from({ length: lead }, (_, i) => (
          <span className="dr-cal-pad" key={`pad${i}`} aria-hidden="true" />
        ))}
        {Array.from({ length: count }, (_, i) => i + 1).map((d) => (
          <button
            type="button"
            key={d}
            className="dr-cal-d"
            data-testid={`reg-period-day-${props.side}-${d}`}
            onClick={() => props.onPick(d)}
          >
            {d}
          </button>
        ))}
      </div>
    </div>
  );
}

/**
 * 기간 팝오버 본체. 열려 있는 동안만 그려지고, `적용`·`지우기` 로만 바깥 값이 바뀐다.
 *
 * ⚠ **닫기는 바깥이 쥔다** — 업로드 모달의 Esc·배경 규율과 갈릴 자리를 만들지 않는다.
 */
export function PeriodCalendarPopover(props: {
  granularity: string;
  startParts: PeriodParts;
  endParts: PeriodParts;
  onApply: (v: {
    granularity: string;
    startParts: PeriodParts;
    endParts: PeriodParts;
  }) => void;
  onClear: () => void;
  onClose: () => void;
}) {
  const [unit, setUnit] = useState(props.granularity || '일');
  const [start, setStart] = useState<PeriodParts>({ ...props.startParts });
  const [end, setEnd] = useState<PeriodParts>({ ...props.endParts });
  const [shown, setShown] = useState(() => initialMonth(props.startParts));
  const { onClose } = props;
  useEscLayer(useCallback(() => onClose(), [onClose]));

  const open = partsFor(unit);
  const openKeys = new Set(open.map((p) => p.key));
  // 시각 칸은 **시·분·초 중 하나라도 열렸을 때만** 선다 (PRD-18 — 단위까지만 칸이 열린다).
  const withTime = openKeys.has('hour');

  function pickDay(side: 'start' | 'end', day: number) {
    const next: PeriodParts = {
      ...(side === 'start' ? start : end),
      year: String(shown.year),
      month: pad2(shown.month),
      day: pad2(day),
    };
    if (side === 'start') setStart(next);
    else setEnd(next);
  }

  function setTime(side: 'start' | 'end', raw: string) {
    const [h = '', m = '', s = ''] = raw.split(':');
    const patch = { hour: h, minute: m, second: s };
    if (side === 'start') setStart((cur) => ({ ...cur, ...patch }));
    else setEnd((cur) => ({ ...cur, ...patch }));
  }

  function timeValue(parts: PeriodParts): string {
    return `${parts.hour || '00'}:${parts.minute || '00'}`;
  }

  return (
    <div
      className="dr-pop"
      role="dialog"
      aria-label="기간 고르기"
      data-testid="reg-period-pop"
      {...{ [ESC_LAYER_ATTR]: '기간' }}
    >
      {/* 최소 단위 — 이 데이터의 시간 해상도를 먼저 고르고 아래 칸이 그에 맞춰 바뀐다 */}
      <div className="dr-units">
        <span className="du-l">최소 단위</span>
        <div className="dr-useg">
          {GRANULARITIES.map((g) => (
            <button
              type="button"
              key={g}
              className={g === unit ? 'on' : ''}
              data-testid={`reg-period-unit-${g}`}
              aria-pressed={g === unit}
              onClick={() => setUnit(g)}
            >
              {g}
            </button>
          ))}
        </div>
      </div>

      {/* 자리 칸 — 고른 단위까지만. 연·월만 여는 단위에서는 달력 대신 이 칸이 값을 받는다 */}
      <div className="dr-parts">
        {(['start', 'end'] as const).map((side) => (
          <span className="partrow" key={side} data-testid={`reg-period-pop-${side}`}>
            <span className="pr-side">{side === 'start' ? '시작' : '끝'}</span>
            {open.map((spec) => (
              <span className="pr-cell" key={spec.key}>
                <input
                  className="inp pr-in"
                  type="text"
                  inputMode="numeric"
                  maxLength={spec.width}
                  size={spec.width}
                  aria-label={`${side === 'start' ? '시작' : '끝'} ${spec.label}`}
                  data-testid={`reg-period-pop-${side}-${spec.key}`}
                  value={(side === 'start' ? start : end)[spec.key]}
                  onChange={(e) => {
                    const patch = { [spec.key]: e.target.value } as Partial<PeriodParts>;
                    if (side === 'start') setStart((cur) => ({ ...cur, ...patch }));
                    else setEnd((cur) => ({ ...cur, ...patch }));
                  }}
                />
                <span className="pr-unit">{spec.label}</span>
              </span>
            ))}
          </span>
        ))}
      </div>

      {withTime && (
        <div className="dr-times">
          <div className="form-row">
            <label htmlFor="reg-period-time-start">시작 시각</label>
            <input
              id="reg-period-time-start"
              className="inp mono"
              type="time"
              data-testid="reg-period-time-start"
              value={timeValue(start)}
              onChange={(e) => setTime('start', e.target.value)}
            />
          </div>
          <div className="form-row">
            <label htmlFor="reg-period-time-end">종료 시각</label>
            <input
              id="reg-period-time-end"
              className="inp mono"
              type="time"
              data-testid="reg-period-time-end"
              value={timeValue(end)}
              onChange={(e) => setTime('end', e.target.value)}
            />
          </div>
        </div>
      )}

      {openKeys.has('day') && (
        <>
          <div className="dr-nav">
            <button
              type="button"
              aria-label="이전 달"
              data-testid="reg-period-prev-month"
              onClick={() =>
                setShown((c) =>
                  c.month === 1 ? { year: c.year - 1, month: 12 } : { ...c, month: c.month - 1 },
                )
              }
            >
              ‹
            </button>
            <span className="sp" />
            <button
              type="button"
              aria-label="다음 달"
              data-testid="reg-period-next-month"
              onClick={() =>
                setShown((c) =>
                  c.month === 12 ? { year: c.year + 1, month: 1 } : { ...c, month: c.month + 1 },
                )
              }
            >
              ›
            </button>
          </div>
          <div className="dr-cals">
            <MonthGrid
              year={shown.year}
              month={shown.month}
              side="start"
              onPick={(d) => pickDay('start', d)}
            />
            <MonthGrid
              year={shown.year}
              month={shown.month}
              side="end"
              onPick={(d) => pickDay('end', d)}
            />
          </div>
        </>
      )}

      <div className="dr-foot">
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          data-testid="reg-period-clear"
          onClick={() => {
            props.onClear();
            props.onClose();
          }}
        >
          지우기
        </button>
        <button
          type="button"
          className="btn btn-primary btn-sm"
          data-testid="reg-period-apply"
          onClick={() => {
            // 열리지 않은 자리는 값으로 남기지 않는다 — 단위를 좁힌 뒤의 잔값이 저장되면
            // 화면이 안 보인 값을 몰래 싣는다.
            const trim = (p: PeriodParts): PeriodParts =>
              Object.fromEntries(
                PARTS.map((s) => [s.key, openKeys.has(s.key) ? p[s.key] : '']),
              ) as PeriodParts;
            props.onApply({
              granularity: unit,
              startParts: trim(start),
              endParts: trim(end),
            });
            props.onClose();
          }}
        >
          적용
        </button>
      </div>
    </div>
  );
}
