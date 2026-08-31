// 잠김 (허용 안 됨) — 본문 대신 잠김 안내와 접근 요청 자리가 나온다 (`§3.3` · `§7` · `§8`).
// 문구는 정본 목업 `데이터셋_상세_260817.html` 의 D-03 장면 그대로다.
//
// ⭑ **WU-P6 이 `접근 요청` 자리를 채웠다.** 요청은 **여기서** 한다 — 카탈로그 행에는 이
// 버튼을 두지 않는다 (`Policy_데이터_찾기:152`).
import { AccessRequestPanel } from '../approval/AccessRequestPanel';
import type { ApprovalSource } from '../approval/types';
import type { DatasetDetail } from './types';

export function LockedNotice(props: {
  detail: DatasetDetail;
  approvalSource: ApprovalSource;
  onRequested?: (() => void) | undefined;
}) {
  return (
    <div className="locked-hero">
      <h2>이름과 요약까지만 보여요</h2>
      <p>요청하면 교수 또는 승인을 맡은 연구원이 검토해요.</p>
      <div data-slot="access-request">
        <AccessRequestPanel
          datasetId={props.detail.datasetId}
          canRequestAccess={props.detail.actions.canRequestAccess}
          accessRequestPending={props.detail.accessRequestPending}
          source={props.approvalSource}
          onRequested={props.onRequested}
        />
      </div>
    </div>
  );
}
