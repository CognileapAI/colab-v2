// §8 「상세 S-05 · 잠긴 상태」 — 본문 대신 잠김 안내 + **접근 요청 버튼**.
//
// **요청은 여기서 한다.** 카탈로그 행에는 이 버튼을 두지 않는다
// (`Policy_데이터_찾기:152` 축자 「행에는 접근 요청 버튼을 두지 않는다 · 행을 누르면
// 잠긴 상세로 가고 요청은 거기서 한다」). 그래서 이 컴포넌트는 상세에만 산다.
//
// 요청을 보낸 뒤에는 버튼이 **검토 대기 칩**으로 바뀐다 (계약 `createAccessRequest` 산문).
// 그 상태는 화면이 기억하지 않고 서버의 `accessRequestPending` 이 말한다 — 새로고침해도
// 같은 것을 보여야 하고, 화면이 기억하면 새로고침에 사라진다.
import { useState } from 'react';
import type { ApprovalSource } from './types';

export function AccessRequestPanel(props: {
  datasetId: string;
  /** 서버가 내린 값. **화면이 계산하지 않는다** (P-7). */
  canRequestAccess: boolean;
  accessRequestPending: boolean;
  source: ApprovalSource;
  onRequested?: (() => void) | undefined;
}) {
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 이미 보낸 요청이 있으면 그 상태만 말한다. 다시 보낼 자리를 두지 않는다 —
  // 서버가 409 를 낼 것을 화면이 먼저 알고 있으면서 버튼을 두면 그건 함정이다.
  if (props.accessRequestPending) {
    return (
      <p className="ar-pending">
        <span className="chip chip--warning">검토 대기</span>
        <span className="ar-pending-note">교수 또는 승인을 맡은 연구원이 보고 있어요.</span>
      </p>
    );
  }
  if (!props.canRequestAccess) return null;

  async function send() {
    setBusy(true);
    setError(null);
    try {
      // **빈 칸은 「안 적었다」다** — 빈 문자열이 아니라 없음으로 보낸다 (§5 「선택」).
      await props.source.requestAccess(props.datasetId, reason.trim() || null);
      setOpen(false);
      setReason('');
      props.onRequested?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : '접근 요청을 보내지 못했어요.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <button type="button" className="btn btn-primary" onClick={() => setOpen(true)}>
        접근 요청
      </button>
      {open ? (
        <div className="modal-back">
          <div className="modal modal--dialog" role="dialog" aria-modal="true" aria-label="접근 요청 보내기">
            <h3>이 데이터에 접근을 요청할까요?</h3>
            <p>교수 또는 승인을 맡은 연구원이 검토해요.</p>
            <label className="ar-reason">
              <span>왜 필요한지 적어 주세요 (선택)</span>
              {/* 300자는 정본이 정한 값이다 (§5). 서버도 같은 값을 강제한다 */}
              <textarea
                maxLength={300}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
              />
            </label>
            {error ? <p className="ar-error">{error}</p> : null}
            <div className="modal-act">
              <button type="button" className="btn btn-ghost" onClick={() => setOpen(false)}>
                그만두기
              </button>
              <button type="button" className="btn btn-primary" disabled={busy} onClick={send}>
                요청 보내기
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
