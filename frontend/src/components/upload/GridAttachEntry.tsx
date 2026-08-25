// S-05 데이터셋 상세의 **「기준 격자 추가」 진입점 하나.**
//
// **새 화면 개념을 만들지 않는다** (Ted 2026-08-25 판정 · 사용자 관점 우선). 사람에게
// 「격자를 나중에 붙이는 행위」는 **파일 업로드**이므로, 이 버튼이 여는 것은 S-04 업로드
// 모달 그대로다 — 진행 표시 · 감지 · 판별 사다리 · 11 상태가 같은 코드다.
// 바뀌는 것은 끝의 한 걸음뿐이다: 「연구실에 등록」 대신 「이 데이터셋에 반영」.
//
// **짝(데이터셋 ↔ 업로드)은 이 컴포넌트 트리의 상태로만 존재한다** — 서버에 보관되지 않는다.
// `d5_upload` 는 `datasetId` 를 의도적으로 갖지 않는다(불변규칙 1).
//
// 권한이 꺼지면 **버튼이 숨는다 — 비활성이 아니다** (`P-12`). `UploadEntry` 와 같은 게이트다.
import { useState } from 'react';
import { PermissionGate } from '../../permission/PermissionGate';
import { UploadModal } from './UploadModal';
import { apiLineageSource } from '../lineage/lineageSource';
import { apiPreviewSource } from './previewSource';
import { apiProjectSource } from './projectSource';
import { apiUploadSource } from './uploadSource';
import type { UploadSources } from './types';
import './upload.css';

function defaultSources(): UploadSources {
  return {
    upload: apiUploadSource(),
    preview: apiPreviewSource(),
    projects: apiProjectSource(),
    lineage: apiLineageSource(),
  };
}

export function GridAttachEntry(props: {
  datasetId: string;
  datasetName?: string | undefined;
  /** 반영이 끝난 뒤 상세를 다시 읽는 자리. */
  onAttached?: (() => void) | undefined;
  sources?: UploadSources | undefined;
}) {
  const [open, setOpen] = useState(false);
  const [sources] = useState<UploadSources>(() => props.sources ?? defaultSources());

  return (
    <PermissionGate requires="업로드·편집">
      <button
        type="button"
        className="btn btn-secondary"
        data-testid="grid-attach-open"
        onClick={() => setOpen(true)}
      >
        기준 격자 추가
      </button>
      {open && (
        <UploadModal
          sources={sources}
          attach={{
            datasetId: props.datasetId,
            datasetName: props.datasetName,
            onAttached: props.onAttached,
          }}
          onClose={() => setOpen(false)}
        />
      )}
    </PermissionGate>
  );
}
