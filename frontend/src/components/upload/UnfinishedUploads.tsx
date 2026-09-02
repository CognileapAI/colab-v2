// **올리다 만 것** — 메인 화면(S-01)의 카드.
//
// 업로드는 두 걸음이다: ㉠ 파일 바이트 올리기 ㉡ 설정 입력 후 「연구실에 등록하기」.
// 그래서 미완결도 두 가지이고, 사람에게는 **둘 다** 「아직 안 끝난 내 업로드」다.
//
//  ㉠ 이 끊긴 것 — 전송 원장(72시간). 서버가 목록으로 준다(`listIncompleteUploadTransfers`).
//  ㉡ 이 안 끝난 것 — 접수 원장(24시간). **목록 창구가 계약에 없다** → 브라우저가 기억해 둔
//     `uploadId`(`pendingStore`)를 **한 건씩** `getUploadStatus` 로 확인한다. 새 op 을 만들지 않는다.
//
// ⚠ **`TodoInboxSlot` 을 침범하지 않는다.** 그 자리는 할 일 함(그룹 셋)으로 열거된 P7 의 것이다.
//    이 카드는 그 옆의 **별도 절**이고, 정본 개정 판정 전까지 그렇게 둔다.
// ⚠ 데이터는 **`/uploads/*` 계열에서만** 온다. 대시보드 op 에 uploadId 를 실으면
//    「원장은 어느 읽기에도 비치지 않는다」 시험이 정당하게 red 를 낸다.
import { useEffect, useState } from 'react';
import { useAccount } from '../../permission/session';
import { useOpenUpload } from './openUpload';
import { forgetPending, listPending } from './pendingStore';
import type { IncompleteTransferItem, UploadSource } from './types';
import './upload.css';

/** 등록만 남은 업로드 한 건 — 표시에 필요한 것만 든다. */
interface PendingRow {
  uploadId: string;
  label: string;
}

export function UnfinishedUploads(props: { upload: UploadSource }) {
  const account = useAccount();
  const openUpload = useOpenUpload();
  const [transfers, setTransfers] = useState<IncompleteTransferItem[]>([]);
  const [pending, setPending] = useState<PendingRow[]>([]);
  const labId = account?.labId ?? '';
  const { upload } = props;

  useEffect(() => {
    if (!labId) return;
    let alive = true;

    // ㉠ 전송 원장 — 서버 목록. 저장 모드 local 이면 빈 배열이 온다(전송 개념이 없다).
    void upload.incomplete?.().then((v) => { if (alive) setTransfers(v); })
      .catch(() => { if (alive) setTransfers([]); });

    // ㉡ 접수했는데 등록 안 한 것 — 기억해 둔 id 를 **한 건씩** 확인한다.
    //    404(만료·소멸)면 조용히 잊는다. **오류를 띄우지 않는다** — 사람이 한 일이 아니다.
    void Promise.all(listPending(labId).map(async (id) => {
      try {
        const s = await upload.status(id);
        // **이미 등록됐으면 잊는다.** 등록 직후 탭이 죽으면 브라우저 기억만 남고, 그때
        // 화면이 **끝낸 일을 「등록만 남았어요」라고** 말했다. 서버가 말하게 해서 닫았다
        // (`UploadStatus.registered` · 2026-09-02 동결 해제).
        // ⚠ `undefined` 는 「모른다」다 — 구판 서버와 섞이면 **판단을 미루고** 그대로 보여준다.
        //    없는 것을 등록됐다고 단정해 사람이 되찾을 길을 지우는 쪽이 더 나쁘다.
        if (s.registered === true) {
          forgetPending(labId, id);
          return null;
        }
        const first = s.files[0];
        return { uploadId: id, label: first ? first.fileName : id } as PendingRow;
      } catch {
        forgetPending(labId, id);
        return null;
      }
    })).then((rows) => {
      if (alive) setPending(rows.filter((r): r is PendingRow => r !== null));
    });

    return () => { alive = false; };
  }, [labId, upload]);

  // **빈 카드를 두지 않는다** — 없으면 자리 자체가 없다.
  if (transfers.length === 0 && pending.length === 0) return null;

  return (
    <section className="up-banner" data-testid="unfinished-uploads" aria-live="polite">
      <p className="ub-hint">올리다 만 것이 있어요</p>

      {transfers.map((t) => (
        <div className="ub-row" key={t.uploadId}>
          <span className="ub-txt">
            {t.sourceLabel} — 파일 올리는 중 {t.uploadedFiles}/{t.plannedFiles}
          </span>
          <button
            type="button"
            className="ub-btn"
            data-testid={`unfinished-resume-${t.uploadId}`}
            onClick={() => openUpload({ resumeUploadId: t.uploadId })}
          >
            이어서 올리기
          </button>
        </div>
      ))}

      {pending.map((p) => (
        <div className="ub-row" key={p.uploadId}>
          {/* 바이트는 다 갔다 — 남은 것은 설정과 [연구실에 등록하기] 한 걸음이다. */}
          <span className="ub-txt">{p.label} — 등록만 남았어요</span>
          <button
            type="button"
            className="ub-btn"
            data-testid={`unfinished-register-${p.uploadId}`}
            onClick={() => openUpload({ resumeUploadId: p.uploadId })}
          >
            이어서 하기
          </button>
        </div>
      ))}
    </section>
  );
}
