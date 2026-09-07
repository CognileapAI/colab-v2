// 분류 3축 필터 바 (PRD-05 · WU-B7). 셀렉트 셋이고 순서는 `분류`·`유형`·`가공 단계` 다.
//
// ⚠ **열 메뉴를 대신하지 않는다** — 주제·Level·업로더·계보·Verified 조건은 표 헤더에 그대로
//   있다(`Policy_데이터_찾기 §1.3-9`). 이 바는 정본이 새로 요구한 **3축 전용** 자리다.
// 건수는 **서버가 준 값을 그대로 쓴다** — 화면이 세지 않는다(열 메뉴와 같은 규율).
import { AXIS_ALL_LABEL, axisOptions } from './axisFilters';
import { AXES } from './types';
import type { AxisFilters, AxisName, FacetSet } from './types';

function countsOf(facets: FacetSet | null, axis: AxisName): Map<string, number> {
  const found = (facets?.axes ?? []).find((a) => a.axis === axis);
  return new Map((found?.values ?? []).map((v) => [v.value, v.count]));
}

export function AxisFilterBar(props: {
  axes: AxisFilters;
  facets: FacetSet | null;
  onPick: (axis: AxisName, value: string | null) => void;
}) {
  return (
    <div className="axis-bar" data-testid="axis-bar">
      {AXES.map((axis) => {
        const counts = countsOf(props.facets, axis);
        return (
          <label className="axis-pick" key={axis} data-testid={`axis-${axis}`}>
            <span className="axis-k">{axis}</span>
            <select
              value={props.axes[axis] ?? ''}
              aria-label={axis}
              onChange={(e) => props.onPick(axis, e.target.value === '' ? null : e.target.value)}
            >
              {/* 첫 항목 = 「조건 없음」. 글자는 rev1 축자다 (PRD-05). */}
              <option value="">{AXIS_ALL_LABEL[axis]}</option>
              {axisOptions(axis).map((o) => (
                <option value={o.value} key={o.value}>
                  {counts.size > 0 ? `${o.label} (${counts.get(o.value) ?? 0})` : o.label}
                </option>
              ))}
            </select>
          </label>
        );
      })}
    </div>
  );
}
