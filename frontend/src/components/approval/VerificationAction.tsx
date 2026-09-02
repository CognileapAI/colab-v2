// §8 「상세 S-05 · 헤더」 — **한 자리가 상태 × 보는 사람에 따라 셋으로 갈린다.**
//
//   ① 미승인 + 올린 사람·소유자 → `✓ 승인 요청`
//   ② 검토 대기 + 교수         → `승인`
//   ③ 승인됨 + 교수           → `⋯` 더보기 → `승인 취소` (파급 모달 경유)
//   그 외에는 **액션이 없다.**
//
// **셋을 화면이 판정하지 않는다** (P-7). 서버가 `actions` 세 칸으로 내려주고 여기서는 그
// 값만 읽는다 — 역할·상태로 다시 유도하면 서버와 화면이 갈라진다.
//
// **취소를 배지에 붙이지 않는다** (§1.3-4). 배지는 카탈로그·검색·프로젝트·홈에도 똑같이
// 반복되는 상태 표시라, 한 곳에서 눌리기 시작하면 나머지도 눌릴 것처럼 보이고 오조작이 생긴다.
// 그래서 진입점은 **`⋯` 더보기 하나뿐**이다 (§1.3-4 · §7.1).
import { useState } from 'react';
import type { DatasetDetail } from '../detail/types';
import type { ApprovalSource } from './types';

export function VerificationAction(props: {
  detail: DatasetDetail;
  source: ApprovalSource;
  onChanged?: (() => void) | undefined;
}) {
  const { datasetId, actions, projects } = props.detail;
  const [menuOpen, setMenuOpen] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [reason, setReason] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run(fn: () => Promise<void>, fallback: string) {
    setBusy(true);
    setError(null);
    try {
      await fn();
      setConfirming(false);
      setMenuOpen(false);
      setReason('');
      props.onChanged?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : fallback);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="dh-act" data-slot="verification-action" data-testid="verification-action">
      {/* ① */}
      {actions.canRequestVerification ? (
        <button
          type="button"
          className="btn btn-secondary"
          disabled={busy}
          onClick={() =>
            run(() => props.source.requestVerification(datasetId), '승인 요청을 보내지 못했어요.')
          }
        >
          ✓ 승인 요청
        </button>
      ) : null}

      {/* ② 할 일 함이 아니라 **상세에서** 누른다 — 근거를 보고 판단하는 자리다 (§1.3-2) */}
      {actions.canApproveVerification ? (
        <button
          type="button"
          className="btn btn-primary"
          disabled={busy}
          onClick={() =>
            run(() => props.source.approveVerification(datasetId), '승인하지 못했어요.')
          }
        >
          승인
        </button>
      ) : null}

      {/* ③ */}
      {actions.canCancelVerification ? (
        <div className="dh-more">
          <button
            type="button"
            className="btn btn-ghost"
            aria-haspopup="menu"
            aria-expanded={menuOpen}
            aria-label="더보기"
            onClick={() => setMenuOpen((v) => !v)}
          >
            ⋯
          </button>
          {menuOpen ? (
            <div role="menu" className="dh-menu">
              <button
                type="button"
                role="menuitem"
                onClick={() => {
                  setMenuOpen(false);
                  setConfirming(true);
                }}
              >
                승인 취소
              </button>
            </div>
          ) : null}
        </div>
      ) : null}

      {/* 파급을 **먼저 보여주고** 확인하면 그대로 취소한다 — 막지는 않는다 (§1.3-9 · P-28).
          파급 셋 = 정렬 하락 · 활용 프로젝트 · 파생 데이터 건수 (§7.1).
          **파생 데이터에는 표시하지 않는다**(§7.1) — 건수만 말하고 끝이다. */}
      {confirming ? (
        <div className="modal-back">
          <div className="modal modal--dialog" role="dialog" aria-modal="true" aria-label="승인을 취소할까요?">
            <h3>이 데이터의 승인을 취소할까요?</h3>
            <ul className="vc-impact">
              <li>검색·카탈로그에서 우선 정렬이 사라져요.</li>
              <li>활용 프로젝트 {projects?.length ?? 0}건에 취소가 표시돼요.</li>
              <li>데이터와 계보는 그대로 남고 배지만 사라져요.</li>
            </ul>
            <label className="vc-reason">
              <span>취소 사유 (선택)</span>
              {/* 120자는 정본이 정한 값이다 (§5 취소 사유 행) */}
              <textarea
                maxLength={120}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
              />
            </label>
            {error ? <p className="ar-error">{error}</p> : null}
            <div className="modal-act">
              <button type="button" className="btn btn-ghost" onClick={() => setConfirming(false)}>
                그만두기
              </button>
              <button
                type="button"
                className="btn btn-danger"
                disabled={busy}
                onClick={() =>
                  run(
                    () => props.source.cancelVerification(datasetId, reason.trim() || null),
                    '승인을 취소하지 못했어요.',
                  )
                }
              >
                승인 취소
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {error && !confirming ? <p className="ar-error">{error}</p> : null}
    </div>
  );
}
