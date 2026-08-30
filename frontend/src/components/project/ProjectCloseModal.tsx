// F-05 프로젝트 닫기 모달 — 목업 `프로젝트_260817.html` 의 `closeModal`.
//
// **가장 큰 걱정을 누르기 전에 없앤다** (`Policy_프로젝트 §8` 닫기 확인 행) — 그래서
// 「데이터는 사라지지 않아요」가 확인 문구보다 **먼저** 온다. 이 순서가 이 모달의 존재 이유다.
// 닫기는 정리이지 삭제가 아니고(`§1.3-5`·`§7`), 소속 데이터셋은 카탈로그에 그대로 남는다.
//
// **다시 열기에는 이 모달을 세우지 않는다** — 확인이 필요한 것은 잃을까 걱정되는 쪽뿐이다.
import { useId, useState } from 'react';
import { projectPeriod } from './format';
import type { ProjectDetail } from './types';

export function ProjectCloseModal(props: {
  detail: ProjectDetail;
  onConfirm(): Promise<void>;
  onClose(): void;
}) {
  const { detail } = props;
  const titleId = useId();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function confirm() {
    setBusy(true);
    try {
      await props.onConfirm();
      props.onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : '닫지 못했어요.');
    } finally {
      setBusy(false);
    }
  }

  const sub = [detail.type, projectPeriod(detail.period), `데이터셋 ${detail.datasets.length}개`]
    .filter(Boolean)
    .join(' · ');

  return (
    <div className="pj-modal-back" data-testid="project-close-modal">
      <div className="pj-modal" role="dialog" aria-modal="true" aria-labelledby={titleId}>
        <div className="pj-modal-h">
          <h3 id={titleId}>이 프로젝트를 닫을까요?</h3>
          <button type="button" className="pj-x" onClick={props.onClose} aria-label="창 닫기">
            ×
          </button>
        </div>

        <div className="pj-modal-b">
          <div className="pj-target" data-testid="project-close-target">
            <div className="pj-tn">{detail.name}</div>
            <div className="pj-tm">{sub}</div>
          </div>

          {/* **잔존 안내가 먼저다** (§8) — 그 뒤에 무엇이 달라지는지를 적는다 */}
          <div className="pj-keepbox" data-testid="project-close-keep">
            <b>데이터는 사라지지 않아요.</b> 소속 데이터셋 {detail.datasets.length}개는 카탈로그에
            그대로 남아요.
          </div>
          <p className="pj-closebody">
            닫으면 목록에서 <b>닫힘</b>으로 표시되고, 새 데이터를 이 프로젝트에 담을 수 없어요.
            언제든 다시 열 수 있어요.
          </p>

          {error ? (
            <p className="pj-err" role="alert" data-testid="project-close-error">
              {error}
            </p>
          ) : null}
        </div>

        <div className="pj-modal-f">
          {/* 취소 쪽 글자도 목업 그대로다 — 「그대로 두기」가 무엇을 고르는지 더 잘 말한다 */}
          <button type="button" className="btn btn-secondary" onClick={props.onClose}>
            그대로 두기
          </button>
          <button type="button" className="btn btn-strong" disabled={busy} onClick={() => void confirm()}>
            닫기
          </button>
        </div>
      </div>
    </div>
  );
}
