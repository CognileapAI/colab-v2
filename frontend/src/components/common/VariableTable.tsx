// 변수 표 — ⭑ **⟨WU-B2 · PRD-16⟩ 5열(`변수 · 단위 · 값 범위 · 결측률 · 대표`).**
//
// **한 컴포넌트가 두 자리를 그린다** — 등록 ①(편집)과 상세(읽기 전용). 두 벌로 적으면
// 열 순서·라벨이 갈리는 날이 오고, PRD-16 이 못 박은 것이 바로 그 열 구성이다.
// 값의 정본은 `d3_dataset_variable` 이고 이 표는 그 행 집합을 그대로 그린다.
import { AT_LEAST_ONE_VARIABLE } from './toastCopy';
import './variableTable.css';

/** 계약 `DatasetVariable` 과 같은 모양. 화면이 쥐는 동안 `name` 은 비어 있을 수 있다. */
export type VariableRow = {
  name: string;
  unit: string | null;
  valueRange: string | null;
  missingRate: string | null;
  representative: boolean;
};

/** 열 순서·라벨은 **rev1 `vt-head` 축자**다. 여기 말고 다른 곳에 적지 않는다. */
export const VARIABLE_COLUMNS = ['변수', '단위', '값 범위', '결측률', '대표'] as const;

export function emptyVariableRow(): VariableRow {
  return { name: '', unit: null, valueRange: null, missingRate: null, representative: false };
}

/**
 * 화면의 행 → 계약 `DatasetCreate.variables`. **빈 이름 행은 싣지 않는다** —
 * `+ 변수 추가` 로 만든 빈 줄을 그대로 보내면 서버가 400 을 내고, 사용자는 자기가 안 적은
 * 줄 때문에 막힌다. 한 행도 안 적었으면 **열쇠 자체를 안 싣는다**(「안 적었다」의 표현).
 */
export function variablesPayload(rows: VariableRow[]): VariableRow[] | null {
  const filled = rows.filter((r) => r.name.trim() !== '');
  if (filled.length === 0) return null;
  return filled.map((r) => ({
    name: r.name.trim(),
    unit: r.unit?.trim() ? r.unit.trim() : null,
    valueRange: r.valueRange?.trim() ? r.valueRange.trim() : null,
    missingRate: r.missingRate?.trim() ? r.missingRate.trim() : null,
    representative: r.representative,
  }));
}

/** 상세가 받는 계약 배열 → 화면의 행. `unit` 등이 `null` 인 것이 정상이다. */
export function toVariableRows(
  got: readonly {
    name: string;
    unit?: string | null;
    valueRange?: string | null;
    missingRate?: string | null;
    representative?: boolean;
  }[],
): VariableRow[] {
  return got.map((v) => ({
    name: v.name,
    unit: v.unit ?? null,
    valueRange: v.valueRange ?? null,
    missingRate: v.missingRate ?? null,
    representative: v.representative ?? false,
  }));
}

const CELL_KEYS = ['unit', 'valueRange', 'missingRate'] as const;

export function VariableTable(props: {
  rows: VariableRow[];
  /** 없으면 **읽기 전용**이다 — 상세가 그렇게 쓴다. */
  onRows?: (rows: VariableRow[]) => void;
  /** 마지막 행 삭제를 막을 때 부르는 자리. 문면은 `AT_LEAST_ONE_VARIABLE` 하나뿐이다. */
  onBlocked?: (message: string) => void;
}) {
  const readOnly = props.onRows === undefined;
  const rows = props.rows;

  function change(index: number, patch: Partial<VariableRow>) {
    props.onRows?.(rows.map((r, i) => (i === index ? { ...r, ...patch } : r)));
  }

  /**
   * ⭑ **⟨PRD-16 수용 기준⟩ 마지막 한 행은 지워지지 않는다** — 「변수는 하나 이상 있어야
   * 해요」. 서버도 같은 문면으로 400 을 내지만(뒷문), 화면에서 막는 것이 앞문이다.
   */
  function remove(index: number) {
    if (rows.length <= 1) {
      props.onBlocked?.(AT_LEAST_ONE_VARIABLE);
      return;
    }
    const left = rows.filter((_, i) => i !== index);
    // 대표를 지웠으면 **첫 행이 대표**가 된다 — 서버의 자동 보정과 같은 규칙이고,
    // 두 곳이 다른 규칙을 쓰면 저장 전후로 대표가 움직인다.
    if (!left.some((r) => r.representative) && left[0]) left[0].representative = true;
    props.onRows?.(left);
  }

  function pick(index: number) {
    props.onRows?.(rows.map((r, i) => ({ ...r, representative: i === index })));
  }

  return (
    <div className="vartable" data-testid="variable-table">
      <table>
        <thead>
          <tr data-testid="vt-head">
            {VARIABLE_COLUMNS.map((c) => (
              <th key={c}>{c}</th>
            ))}
            {readOnly ? null : <th aria-label="행 삭제" />}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            // 행 열쇠로 이름을 쓰지 않는다 — 이름이 비거나 겹치는 동안 입력 포커스가 튄다.
            // eslint-disable-next-line react/no-array-index-key
            <tr key={i} data-testid="vt-row">
              <td>
                {readOnly ? (
                  row.name
                ) : (
                  <input
                    className="inp"
                    aria-label={`변수 ${i + 1}`}
                    data-testid={`vt-name-${i}`}
                    value={row.name}
                    onChange={(e) => change(i, { name: e.target.value })}
                  />
                )}
              </td>
              {CELL_KEYS.map((key) => (
                <td key={key}>
                  {readOnly ? (
                    (row[key] ?? '—')
                  ) : (
                    <input
                      className="inp"
                      aria-label={`${VARIABLE_COLUMNS[CELL_KEYS.indexOf(key) + 1]} ${i + 1}`}
                      data-testid={`vt-${key}-${i}`}
                      value={row[key] ?? ''}
                      onChange={(e) => change(i, { [key]: e.target.value } as Partial<VariableRow>)}
                    />
                  )}
                </td>
              ))}
              <td>
                <input
                  type="radio"
                  name="vt-representative"
                  aria-label={`대표 ${i + 1}`}
                  data-testid={`vt-rep-${i}`}
                  checked={row.representative}
                  disabled={readOnly}
                  onChange={() => pick(i)}
                />
              </td>
              {readOnly ? null : (
                <td>
                  <button
                    type="button"
                    className="vt-del"
                    data-testid={`vt-del-${i}`}
                    onClick={() => remove(i)}
                  >
                    삭제
                  </button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
      {readOnly ? null : (
        <button
          type="button"
          className="vt-add"
          data-testid="vt-add"
          onClick={() => props.onRows?.([...rows, emptyVariableRow()])}
        >
          + 변수 추가
        </button>
      )}
    </div>
  );
}
