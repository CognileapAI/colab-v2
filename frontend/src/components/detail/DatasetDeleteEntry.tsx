// 상세 헤더의 **삭제 진입점** (`DL-1` · `Policy_데이터셋_상세 §6·§8`).
//
// 관문은 서버가 건별로 판정해 내려준 `actions.canDelete` 하나다 — 화면이 조건을 따로 짓지
// 않는다 (P-7). 그 값의 서버 축자는 `is_owner or is_professor` 이고, 스위치가 아니라
// **소유자·역할 축**이라 `PermissionGate` 가 아니라 `ActionGate` 다.
//
// 꺼져 있으면 **DOM 에서 사라진다** (P-12) — 비활성 버튼도 경고 토스트도 두지 않는다.
//
// 성공하면 목록으로 보낸다. **토스트는 없다** (P-20) — 지워진 데이터의 상세에 남아 있는 것
// 자체가 틀린 화면이고, 목록으로 옮기는 것이 결과를 말하는 방식이다.
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ActionGate } from '../../permission/PermissionGate';
import type { LineageGraphState } from '../lineage/useDatasetLineage';
import { DeleteConfirmModal } from './DeleteConfirmModal';
import type { DatasetDeletionSource, DatasetDetail } from './types';
import './deletion.css';

export function DatasetDeleteEntry(props: {
  detail: DatasetDetail;
  source: DatasetDeletionSource;
  lineage?: LineageGraphState | undefined;
}) {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();

  return (
    <ActionGate allowed={props.detail.actions.canDelete}>
      <button
        type="button"
        className="btn btn-secondary"
        data-testid="detail-delete-open"
        onClick={() => setOpen(true)}
      >
        {/* 글리프는 휴지통이어도 **접근명·글자는 「삭제」** 다 — 정본 낱말이 그것이다 */}
        <span aria-hidden="true">🗑</span> 삭제
      </button>
      {open ? (
        <DeleteConfirmModal
          detail={props.detail}
          source={props.source}
          lineage={props.lineage}
          onClose={() => setOpen(false)}
          // 목록은 재마운트에서 `useCatalog` 가 다시 읽는다 — 화면이 행을 손으로 빼지 않는다.
          onDeleted={() => navigate('/datasets', { replace: true })}
        />
      ) : null}
    </ActionGate>
  );
}
