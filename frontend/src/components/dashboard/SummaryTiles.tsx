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
 * 계보를 확인해야 하는 목록의 자리. **한 곳에만 적는다** — 지표 타일과 할 일 함의
 * 전체 보기 링크가 같은 목적지라고 §8 이 못 박았고, 두 곳에 적으면 한쪽만 고쳐진다.
 */
export const LINEAGE_TODO_PATH = `/datasets?${new URLSearchParams({ lineageState: '확인 필요' })}`;
