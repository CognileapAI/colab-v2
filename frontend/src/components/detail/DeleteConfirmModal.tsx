// 삭제 확인 모달 (`DL-1` · Ted 판정 ⓔ).
//
// **문면은 계약 산문 축자다.** 사용자가 말한 「관계가 끊어진다」는 **정본과 반대**라 쓰지
// 않는다 — 계약 `deleteDataset` 산문은 「파일·미리보기만 지우고 이름·주제·Lv·**계보 관계·
// 프로젝트 연결·Verified 는 남긴다**」이고, `DeletionImpact` 세 칸의 설명도 「**자리가
// 남아요**」다. 화면이 남아 있는 것을 없다고 말하면 사람은 지우지 않을 것을 지운다.
//
// **잔존 안내가 파급보다 먼저다** — `ProjectCloseModal` 이 세운 순서 그대로다
// (「가장 큰 걱정을 누르기 전에 없앤다」). 골격은 `VerificationAction` 의
// `modal-back > modal modal--dialog[role=dialog]` 를 쓴다(전역 이름 · `members.css`).
//
// **파급을 못 읽으면 삭제가 서지 않는다.** 무엇이 닫히고 무엇이 남는지 모른 채 되돌릴 수
// 없는 것을 누르게 하지 않는다 — 그 자리에는 「다시 불러오기」만 둔다.
//
// ⛔ 낱말은 **「삭제」**다. 「휴지통」은 이 레포에 0건이고 정본 낱말이 아니다 — 글리프만
// 휴지통이고 접근명·버튼 글자는 「삭제」다.
import { useEffect, useId, useState } from 'react';
import type { LineageGraphState } from '../lineage/useDatasetLineage';
import type { DatasetDeletionSource, DatasetDetail, DeletionImpact } from './types';

type ImpactState =
  | { status: 'loading' }
  | { status: 'ready'; impact: DeletionImpact }
  | { status: 'failed'; message: string };

/** 계약 산문 축자. **한 글자도 바꾸지 않는다** — 시험이 이 문장들을 잠근다. */
export const KEEP_NOTICE =
  '이름·계보 관계·프로젝트 연결·승인 기록은 남아요. 파일과 미리보기만 지워져요. 되돌릴 수 없어요.';
export const TITLE = '이 데이터를 지울까요?';

/** 파생 데이터의 이름 — **계보를 읽었을 때만** 말한다. 못 읽었으면 건수만 말한다. */
function derivedNames(lineage: LineageGraphState | undefined): string[] {
  if (!lineage || lineage.status !== 'ready') return [];
  return lineage.graph.nodes.filter((n) => n.kind === '파생').map((n) => n.name);
}

export function DeleteConfirmModal(props: {
  detail: DatasetDetail;
  source: DatasetDeletionSource;
  lineage?: LineageGraphState | undefined;
  onDeleted(): void;
  onClose(): void;
}) {
  const { detail } = props;
  const titleId = useId();
  const [impact, setImpact] = useState<ImpactState>({ status: 'loading' });
  const [reloadToken, setReloadToken] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // 파급은 **열릴 때 한 번** 읽는다. 상세에 이미 있는 값(파생·Verified·프로젝트)과 달리
  // 대기 접근 요청 건수는 이 화면에 없는 값이라 서버가 따로 내준다 (계약 산문).
  useEffect(() => {
    let alive = true;
    setImpact({ status: 'loading' });
    props.source
      .impact(detail.datasetId)
      .then((v) => alive && setImpact({ status: 'ready', impact: v }))
      .catch((e: unknown) =>
        alive &&
        setImpact({
          status: 'failed',
          message: e instanceof Error && e.message ? e.message : '삭제 파급을 불러오지 못했어요.',
        }),
      );
    return () => {
      alive = false;
    };
  }, [props.source, detail.datasetId, reloadToken]);

  // Esc 로 닫는다 — 되돌릴 수 없는 것을 여는 창에는 **나가는 길이 항상 있어야 한다.**
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') props.onClose();
    }
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [props.onClose]);

  async function confirm() {
    setBusy(true);
    setError(null);
    try {
      await props.source.remove(detail.datasetId);
      props.onDeleted();
    } catch (e) {
      // 실패해도 **모달은 닫지 않는다** — 닫으면 사람이 「지워졌나?」를 다시 눌러 확인한다.
      setError(e instanceof Error && e.message ? e.message : '데이터를 지우지 못했어요.');
    } finally {
      setBusy(false);
    }
  }

  const names = derivedNames(props.lineage);
  const ready = impact.status === 'ready' ? impact.impact : null;
  const projects = detail.projects?.length ?? 0;

  return (
    <div className="modal-back" data-testid="detail-delete-modal">
      <div className="modal modal--dialog" role="dialog" aria-modal="true" aria-labelledby={titleId}>
        <div className="modal-h">
          <h3 id={titleId}>{TITLE}</h3>
        </div>

        <div className="modal-b">
          {/* **잔존 안내가 먼저다** (`ProjectCloseModal` 순서 · Ted 판정 ⓔ) */}
          <div className="dl-keep" data-testid="detail-delete-keep">
            <b>{detail.name}</b>
            <p>{KEEP_NOTICE}</p>
          </div>

          {impact.status === 'loading' ? (
            <p data-testid="detail-delete-impact-loading" aria-busy="true">
              파급을 불러오는 중이에요.
            </p>
          ) : null}

          {impact.status === 'failed' ? (
            <div data-testid="detail-delete-impact-failed">
              <p className="ar-error" role="alert">
                {impact.message}
              </p>
              <button
                type="button"
                className="btn btn-ghost"
                data-testid="detail-delete-impact-retry"
                onClick={() => setReloadToken((n) => n + 1)}
              >
                다시 불러오기
              </button>
            </div>
          ) : null}

          {ready ? (
            <ul className="dl-impact" data-testid="detail-delete-impact">
              {ready.derivedDatasetCount > 0 ? (
                <li>
                  이 데이터로 만든 데이터 {ready.derivedDatasetCount}건의 계보에 자리가 남아요
                  {/* 계보를 읽었을 때만 이름을 말한다 — 못 읽었으면 건수까지가 아는 전부다 */}
                  {names.length > 0 ? ` — ${names.join(' · ')}` : null}
                </li>
              ) : null}
              {ready.verified ? <li>교수 승인이 붙은 데이터예요</li> : null}
              {ready.pendingAccessRequestCount > 0 ? (
                <li>대기 중인 접근 요청 {ready.pendingAccessRequestCount}건이 자동으로 닫혀요</li>
              ) : null}
              {projects > 0 ? <li>활용 프로젝트 {projects}건에 연결이 남아요</li> : null}
            </ul>
          ) : null}

          {error ? (
            <p className="ar-error" role="alert" data-testid="detail-delete-error">
              {error}
            </p>
          ) : null}
        </div>

        <div className="modal-f">
          {/* 「그대로 두기」가 무엇을 고르는지 더 잘 말한다 (`ProjectCloseModal` 과 같은 낱말) */}
          <button
            type="button"
            className="btn btn-secondary"
            data-testid="detail-delete-cancel"
            autoFocus
            onClick={props.onClose}
          >
            그대로 두기
          </button>
          <button
            type="button"
            className="btn btn-danger"
            data-testid="detail-delete-confirm"
            disabled={busy || ready === null}
            onClick={() => void confirm()}
          >
            삭제
          </button>
        </div>
      </div>
    </div>
  );
}
