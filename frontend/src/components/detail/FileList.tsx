// S-05 파일 목록 + 파일 관리 (`PLAN-SoT §9 〈339〉` — 회의 결정 · 정본 산문 밖).
//
// 정본이 못 박은 두 가지는 그대로다 — 「파일」 칸은 조각 수와 합계만 말하고(`BasicInfoGrid`),
// **목록은 사람이 눌렀을 때 연다** (`Policy_데이터셋_상세 §5` · `listDatasetFiles` 산문).
// 그래서 기본은 접힘이고, `보기` 를 누르기 전에는 목록 op 을 부르지 않는다.
//
// 게이트 둘을 섞지 않는다 (P-14):
// · 다운로드 = 서버가 건별로 판정해 내려준 `actions.canDownload` (`ActionGate` · P-7)
// · 추가·교체·삭제 = `업로드·편집` 스위치 (`PermissionGate` · `〈59〉-②` · P-12 — 숨긴다, 비활성이 아니다)
//
// 성공하면 **서버에게 다시 묻는다** — 화면이 목록을 손으로 고치지 않는다 (`useDatasetDetail` 의 reloadToken 과 같은 태도).
// 409(마지막 본체)는 서버 문장을 그대로 보여 준다.
//
// 이 파일의 새 문구는 정본에 없다 — 신설마다 `[정본 무근거 · 〈339〉]` 를 남긴다.
import { useState } from 'react';
import { ActionGate, PermissionGate } from '../../permission/PermissionGate';
import { useStartDownload } from './download';
import { buildTree, type FileTreeNode } from './fileTree';
import { formatFileSize } from './format';
import {
  FileGone,
  LastBodyFile,
  NotImplemented,
  type DatasetDetail,
  type DatasetFile,
  type FileSource,
} from './types';

/** 목록의 시각은 날짜만 적는다 — 카탈로그의 수정일 칸과 같은 표기(`2026-08-11`). */
function day(ts: string): string {
  return ts.slice(0, 10);
}

/** 실패를 사람 문장으로. 409 는 **서버 문장 그대로**, 나머지는 최소한의 평범한 라벨이다. */
export function describeFileError(e: unknown): string {
  if (e instanceof LastBodyFile) return e.message;
  if (e instanceof FileGone) return '이 파일은 더 이상 없어요.'; // [정본 무근거 · 〈339〉] — 업로드 §9 문장의 앞 절을 빌렸다
  if (e instanceof NotImplemented) return '아직 지원하지 않아요.'; // [정본 무근거 · 〈339〉]
  if (e instanceof Error && e.message) return e.message;
  return '파일 작업에 실패했어요.'; // [정본 무근거 · 〈339〉]
}

/** 파일 입력 한 번 — 고른 파일을 넘기고 입력을 비운다(같은 파일을 다시 고를 수 있게). */
function pickOne(e: React.ChangeEvent<HTMLInputElement>): File | null {
  const f = e.target.files?.[0] ?? null;
  e.target.value = '';
  return f;
}

export function FileList(props: {
  datasetId: string;
  source: FileSource;
  /** 서버가 건별로 판정한 값 (P-7). 화면이 조건을 임의로 정하지 않는다. */
  actions: DatasetDetail['actions'];
  /** 추가·교체·삭제가 끝난 뒤 — 상세(`파일` 칸의 조각 수·합계)를 다시 읽는 자리. */
  onChanged?: (() => void) | undefined;
}) {
  const { datasetId, source } = props;
  const download = useStartDownload();
  const [open, setOpen] = useState(false);
  const [files, setFiles] = useState<DatasetFile[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run(work: () => Promise<void>) {
    setBusy(true);
    setError(null);
    try {
      await work();
    } catch (e) {
      setError(describeFileError(e));
    } finally {
      setBusy(false);
    }
  }

  async function reload() {
    setFiles(await source.list(datasetId));
    setOpen(true);
  }

  /** 쓰기 하나 — 성공하면 목록을 다시 묻고 상세에도 알린다. 실패면 아무것도 다시 묻지 않는다. */
  function mutate(work: () => Promise<unknown>) {
    void run(async () => {
      await work();
      await reload();
      props.onChanged?.();
    });
  }

  function toggle() {
    if (open) {
      setOpen(false);
      return;
    }
    void run(reload);
  }

  function row(f: DatasetFile) {
    return (
      <>
        <span className="fl-name">{f.fileName}</span>
        <span className="fl-kind chip chip--neutral">{f.kind}</span>
        <span className="fl-size">{formatFileSize(f.byteSize)}</span>
        <span className="fl-date mono">{day(f.createdAt)}</span>
        <span className="fl-act">
          <ActionGate allowed={props.actions.canDownload}>
            <button
              type="button"
              className="btn btn-sm"
              data-testid={`dt-file-download-${f.fileId}`}
              aria-label={`${f.fileName} 다운로드`}
              disabled={busy}
              onClick={() =>
                void run(async () => download(await source.downloadTicket(datasetId, f.fileId)))
              }
            >
              다운로드
            </button>
          </ActionGate>
          <PermissionGate requires="업로드·편집">
            {/* 교체 = 파일을 하나 고르는 일이다 — 라벨이 곧 버튼이고 입력은 숨긴다 (`FileDropCard` 와 같은 모양) */}
            <label className="btn btn-sm">
              교체{/* [정본 무근거 · 〈339〉] */}
              <input
                type="file"
                className="hidden-input"
                data-testid={`dt-file-replace-${f.fileId}`}
                disabled={busy}
                onChange={(e) => {
                  const picked = pickOne(e);
                  if (picked) mutate(() => source.replace(datasetId, f.fileId, picked));
                }}
              />
            </label>
            <button
              type="button"
              className="btn btn-sm"
              data-testid={`dt-file-delete-${f.fileId}`}
              disabled={busy}
              onClick={() => mutate(() => source.remove(datasetId, f.fileId))}
            >
              삭제{/* [정본 무근거 · 〈339〉] */}
            </button>
          </PermissionGate>
        </span>
      </>
    );
  }

  function nodes(list: FileTreeNode[]) {
    return (
      <ul className="fl-list">
        {list.map((n) =>
          n.kind === 'folder' ? (
            <li key={`d:${n.path}`} className="fl-folder" data-testid={`dt-folder-${n.path}`}>
              <span className="fl-dir">{n.name}/</span>
              {nodes(n.children)}
            </li>
          ) : (
            <li key={n.file.fileId} className="fl-file" data-testid={`dt-file-${n.file.fileId}`}>
              {row(n.file)}
            </li>
          ),
        )}
      </ul>
    );
  }

  const tree = open && files ? buildTree(files) : null;

  return (
    <div className="dt-files" data-testid="dt-files-section">
      <div className="dt-files-head">
        <span className="dt-files-k">파일</span>
        <button
          type="button"
          className="btn btn-sm"
          data-testid="dt-files-toggle"
          aria-expanded={open}
          disabled={busy}
          onClick={toggle}
        >
          {open ? '접기' : '보기'}{/* [정본 무근거 · 〈339〉] — 「목록은 사람이 눌렀을 때 연다」의 그 버튼 */}
        </button>
        <PermissionGate requires="업로드·편집">
          {/* 종류는 본체로 고정 — 격자는 `기준 격자 추가`(업로드 모달 재사용)가 맡고 서버도 여기서는 400 을 낸다 */}
          <label className="btn btn-sm">
            파일 추가{/* [정본 무근거 · 〈339〉] */}
            <input
              type="file"
              className="hidden-input"
              data-testid="dt-file-add"
              disabled={busy}
              onChange={(e) => {
                const picked = pickOne(e);
                if (picked) mutate(() => source.add(datasetId, picked, '본체'));
              }}
            />
          </label>
        </PermissionGate>
      </div>

      {error ? (
        <p className="dt-files-error" role="alert" data-testid="dt-files-error">
          {error}
        </p>
      ) : null}

      {tree ? (
        <div className="dt-files-body-wrap" data-testid="dt-files">
          <div data-testid="dt-files-body">{nodes(tree.body)}</div>
          {/* 기준 격자 파일은 본체와 **따로** 세우고, 없으면 없다고 적는다 — 목업 문구 `기준 격자 파일 없음` */}
          <div className="fl-grid" data-testid="dt-files-grid">
            {tree.grid.length === 0 ? (
              <span className="fl-gh muted">기준 격자 파일 없음</span>
            ) : (
              <>
                <span className="fl-gh">기준 격자 파일</span>
                <ul className="fl-list">
                  {tree.grid.map((f) => (
                    <li key={f.fileId} className="fl-file" data-testid={`dt-file-${f.fileId}`}>
                      {row(f)}
                    </li>
                  ))}
                </ul>
              </>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
