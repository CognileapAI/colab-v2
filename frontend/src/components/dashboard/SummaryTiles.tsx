// 요약 지표 — **네 개를 넘기지 않는다** (`Policy_홈_대시보드 §5`).
//
// 계보 진척을 **퍼센트로 바꿔 적지 않는다** (§5 축자). 확정 개수를 크게, 아직 확인이
// 필요한 건수를 아래 작게 붙인다 — 필요한 정보는 「얼마나 했나」가 아니라 「무엇이 남았나」다.
//
// **네 타일 가운데 눌리는 것은 계보 확정 하나뿐이다** (§8). 그래서 색을 달리하지 않고
// 커서와 화살표로만 구분한다.
import { useNavigate } from 'react-router-dom';
import type { DashboardSummary } from './types';
import type { Slot } from './useDashboard';

export function SummaryTiles(props: { slot: Slot<DashboardSummary> }) {
  const navigate = useNavigate();
  if (props.slot.kind === '실패') {
    return <p className="dash-error">요약 지표를 불러오지 못했어요.</p>;
  }
  if (props.slot.kind !== '있음') return <p className="dash-loading">불러오는 중이에요.</p>;
  const s = props.slot.value;

  return (
    <ul className="dash-tiles" data-card="summary">
      <li className="dash-tile">
        <span className="dash-tile-name">프로젝트</span>
        <strong>{s.projectCount}</strong>
      </li>
      <li className="dash-tile">
        <span className="dash-tile-name">데이터셋</span>
        <strong>{s.datasetCount}</strong>
      </li>
      <li className="dash-tile dash-tile--linked">
        {/* 눌러서 **계보를 확인해야 하는 데이터만** 카탈로그에 건다 (§8).
            할 일 함의 「계보 확인 필요 전체 보기」와 **같은 곳**으로 간다 — 지표를 보다가도,
            할 일을 보다가도 같은 목록으로 이어져야 두 자리가 갈라지지 않는다. */}
        <button type="button" onClick={() => navigate(LINEAGE_TODO_PATH)}>
          <span className="dash-tile-name">계보 확정 →</span>
          <strong>{s.lineageSettledCount}</strong>
          <span className="dash-tile-sub">미확정 {s.lineageUnsettledCount}건</span>
        </button>
      </li>
      <li className="dash-tile">
        <span className="dash-tile-name">Verified</span>
        <strong>{s.verifiedCount}</strong>
      </li>
    </ul>
  );
}

/**
 * ⭑ **⟨PRD-27 · WU-B8⟩ 「미확정」의 모수 — 이 한 곳이 정본이다.**
 *
 * 서버가 타일 숫자(`lineageUnsettledCount`)를 세는 기준은
 * `routes/insight.py` `SETTLED_STATES = ("확정", "원천")` 의 **여집합**이고, 그것이 정본
 * `Policy_홈_대시보드 §4` 축자(「원천은 가공 전 데이터가 없는 것이 정상이라 미확정으로
 * 세지 않는다」)의 집행이다. 따라서 미확정 = `확인 필요` ＋ `기록 없음` **두 값**이다.
 *
 * ⚠ **이 상수가 없던 자리에 불일치가 있었다** — 타일 링크는 `확인 필요` **한 값**으로
 * 목록을 열고, `dashboardSource.ts` 는 **두 값**으로 셌다. 타일 숫자와 그 링크가 여는
 * 목록의 모수가 갈렸다. PRD-27 은 §4 의 용어 정의를 개정하지 않았으므로 **두 값 쪽으로**
 * 맞춘다 — 한 값 쪽으로 맞추면 서버 타일까지 함께 고쳐야 하고 그것은 §4 개정이다.
 */
export const UNSETTLED_LINEAGE_STATES = ['확인 필요', '기록 없음'] as const;

/**
 * 계보를 확인해야 하는 목록의 자리. **한 곳에만 적는다** — 지표 타일과 할 일 함의
 * 전체 보기 링크가 같은 목적지라고 §8 이 못 박았고, 두 곳에 적으면 한쪽만 고쳐진다.
 *
 * ⚠ 값이 둘이라 `URLSearchParams` 에 객체를 넘기지 않는다 — 객체 리터럴은 같은 열쇠를
 * 한 번만 담아 **뒤엣값이 앞엣값을 지운다.** 쌍의 배열로 넘겨 `lineageState` 를 반복시킨다.
 */
export const LINEAGE_TODO_PATH = `/datasets?${new URLSearchParams(
  UNSETTLED_LINEAGE_STATES.map((s) => ['lineageState', s]),
)}`;
