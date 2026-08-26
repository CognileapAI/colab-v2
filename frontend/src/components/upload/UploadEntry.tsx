// GNB 의 업로드 버튼 + 그것이 여는 S-04 전체 화면 모달.
//
// **버튼과 모달을 한 컴포넌트로 묶은 이유** — `frontend/src/shell/` 은 이 레인의 소유가 아니고
// (`P2-EXEC §3` 공유 파일 규칙: `Gnb.tsx` 는 **업로드 버튼 한 줄**만), 모달을 다른 데 얹으려면
// 셸을 더 만져야 한다. 묶어 두면 셸에 남는 변경이 버튼 한 줄뿐이다.
//
// 권한이 꺼지면 **버튼이 숨는다 — 비활성이 아니다** (`P-12` · 정본 §6). 그 판정은 `Gnb.tsx` 의
// `PermissionGate` 가 이미 하고 있고, 여기서도 같은 게이트를 걸어 **이 컴포넌트만 따로 써도
// 규칙이 유지되게** 한다(두 겹이어도 결과는 같다).
import { useState } from 'react';
import { PermissionGate } from '../../permission/PermissionGate';
import { UploadModal } from './UploadModal';
import { apiLineageSource } from '../lineage/lineageSource';
import { apiPreviewSource } from './previewSource';
import { apiProjectSource } from './projectSource';
import { apiUploadSource } from './uploadSource';
import type { LineageStepRender, UploadSources } from './types';
import './upload.css';

function defaultSources(): UploadSources {
  return {
    upload: apiUploadSource(),
    preview: apiPreviewSource(),
    projects: apiProjectSource(),
    lineage: apiLineageSource(),
  };
}

export function UploadEntry(props: {
  sources?: UploadSources | undefined;
  /** ③ 계보 확정 자리를 바깥에서 갈아 끼우고 싶을 때만 넘긴다. 없으면 모달이 집 안의 것을 세운다. */
  lineageStep?: LineageStepRender | undefined;
}) {
  const [open, setOpen] = useState(false);
  const [sources] = useState<UploadSources>(() => props.sources ?? defaultSources());

  return (
    <PermissionGate requires="업로드·편집">
      <button
        type="button"
        className="gnb-upload"
        data-testid="gnb-upload"
        aria-label="업로드"
        onClick={() => setOpen(true)}
      >
        {/* 좁은 화면에서는 `.lbl` 이 숨고 이 아이콘만 남는다 (`shell.css` 640px).
            아이콘이 없으면 버튼이 빈 칸이 된다 — main 의 모바일 반응형 병합에서 실제로 그럴 뻔했다. */}
        <svg
          className="ico"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M12 16V4M7 9l5-5 5 5M4 20h16" />
        </svg>
        <span className="lbl">업로드</span>
      </button>
      {open && (
        <UploadModal
          sources={sources}
          lineageStep={props.lineageStep}
          onClose={() => setOpen(false)}
        />
      )}
    </PermissionGate>
  );
}
