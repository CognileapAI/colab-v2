// S-04 「파일 놓기」 — 정본 §8 파일 놓기 · 올린 파일 표시 · 기준 격자 파일 세 묶음.
//
// **번호를 붙이지 않는다** (§8 단계 번호) — 파일 놓기·바로 미리보기는 절차가 아니라
// 파일을 열어 보는 일이다.
// **축(위도·경도)을 사람에게 묻지 않는다** — 서버가 파일에서 판별한다 (`〈63〉-㉰`).
import { useState } from 'react';
import type { FileKind, PickedFile } from './types';

const KINDS: FileKind[] = ['본체', '기준 격자 파일'];

function humanSize(bytes: number): string {
  if (bytes >= 1024 ** 3) return `${(bytes / 1024 ** 3).toFixed(1)} GB`;
  if (bytes >= 1024 ** 2) return `${Math.round(bytes / 1024 ** 2)} MB`;
  if (bytes >= 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${bytes} B`;
}

export function totalBytes(files: PickedFile[]): number {
  return files.reduce((s, f) => s + f.file.size, 0);
}

/** 확장자 혼합 안내 — rev1 `H-37` **축자**. 한 글자도 바꾸지 않는다. */
export const MIXED_EXTENSION_NOTICE = '확장자가 다른 파일은 뺐어요. 한 번에 한 종류만 묶어요';

/**
 * 업로드 안내는 **업로드 가능 / 미리보기 가능** 둘로 갈린다 (PRD-21 · rev1 축자).
 *
 * 가르지 않으면 「미리보기가 되는 확장자」가 「올릴 수 있는 확장자」로 읽힌다 — 실제로는
 * 무엇이든 올라가고, 지도로 못 그리는 것만 못 그린다. 한 문장으로 두면 사용자가 올릴 수
 * 있는 파일을 못 올린다고 믿는다.
 */
export const UPLOAD_ANY_FORMAT_NOTICE =
  '어떤 포맷이든 올려요 · 같은 확장자면 여러 개를 한 데이터셋으로 묶어요';
export const PREVIEWABLE_EXTENSIONS_NOTICE = '지도 미리보기까지 되는 확장자: *.nc *.tif *.hdf *.bin';
export const NOT_PREVIEWABLE_NOTICE = '이 확장자는 지도로 못 그려요';

/** 지도 미리보기가 되는 확장자 — 위 안내 문면과 **같은 목록**이다. 두 곳에 적지 않는다. */
export const PREVIEWABLE_EXTENSIONS = ['nc', 'tif', 'hdf', 'bin'] as const;

/**
 * 미리보기 가능 안내의 판정. **업로드를 막지 않는다** — 말만 다르다.
 * 확장자가 없는 파일(`''`)도 못 그린다 — 「모른다」와 「된다」를 섞지 않는다.
 */
export function previewabilityNotice(extension: string): string {
  return (PREVIEWABLE_EXTENSIONS as readonly string[]).includes(extension)
    ? PREVIEWABLE_EXTENSIONS_NOTICE
    : NOT_PREVIEWABLE_NOTICE;
}

/**
 * 확장자 — **소문자 기준**이다 (`.NC` 와 `.nc` 는 같은 종류다 · PRD-32).
 * 점이 없는 이름은 빈 문자열로 접는다 — 「확장자 없음」끼리도 한 종류다.
 */
export function extensionOf(fileName: string): string {
  const dot = fileName.lastIndexOf('.');
  return dot <= 0 ? '' : fileName.slice(dot + 1).toLowerCase();
}

/**
 * WU-A13 · PRD-32 — **성립 전의 선별 규칙**이다.
 *
 * 부록 A `P-5`(같은 확장자 여러 개 = 데이터셋 하나)는 성립한 **뒤의 저장 규칙**이고,
 * 이것은 놓는 순간의 선별이다. **가장 먼저 놓인 파일의 확장자**만 남긴다 — 이미 놓인
 * 조각이 있으면 그쪽이 기준이고, 없으면 이번 묶음의 첫 파일이 기준이다.
 */
export function keepOneExtension(
  existing: PickedFile[],
  incoming: File[],
): { kept: File[]; dropped: number } {
  const first = existing.find((p) => p.kind === '본체') ?? existing[0];
  const baseline = first ? extensionOf(first.file.name) : extensionOf(incoming[0]?.name ?? '');
  const kept = incoming.filter((f) => extensionOf(f.name) === baseline);
  return { kept, dropped: incoming.length - kept.length };
}

function FileRow(props: {
  picked: PickedFile;
  onKind: (kind: FileKind) => void;
}) {
  const { picked } = props;
  return (
    <div className="filecard">
      <div className="fmeta">
        <div className="fn">{picked.file.name}</div>
        <div className="fs">{humanSize(picked.file.size)}</div>
      </div>
      <label className="fkind">
        <span className="lbl">파일 종류</span>
        <select
          className="sel"
          data-testid="up-file-kind"
          value={picked.kind}
          onChange={(e) => props.onKind(e.target.value as FileKind)}
        >
          {KINDS.map((k) => (
            <option key={k} value={k}>
              {k}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}

export function FileDropCard(props: {
  picked: PickedFile[];
  onPick: (files: File[]) => void;
  onKind: (index: number, kind: FileKind) => void;
}) {
  const [slicesOpen, setSlicesOpen] = useState(false);
  const [mixedNotice, setMixedNotice] = useState(false);

  /** 놓는 순간 확장자를 세어 **한 종류만** 위로 올린다 (PRD-32 · `VAL-002`). */
  function handlePick(files: File[]) {
    if (files.length === 0) return;
    const { kept, dropped } = keepOneExtension(props.picked, files);
    setMixedNotice(dropped > 0);
    if (kept.length > 0) props.onPick(kept);
  }

  const bodies = props.picked
    .map((p, i) => ({ p, i }))
    .filter(({ p }) => p.kind === '본체');
  const grids = props.picked
    .map((p, i) => ({ p, i }))
    .filter(({ p }) => p.kind === '기준 격자 파일');
  const bundle = bodies.length > 1;

  return (
    <div className="card up-card">
      <div className="card-b">
        {/* 여러 개를 한 번에 받는다 — 드롭 영역이 그렇게 말한다 (§8) */}
        <label className="dropzone" data-testid="up-drop">
          <span className="big">파일을 끌어다 놓으세요</span>
          <span className="muted">여러 개를 한 번에 놓아도 돼요</span>
          <input
            type="file"
            multiple
            className="hidden-input"
            data-testid="up-drop-input"
            onChange={(e) => handlePick(Array.from(e.target.files ?? []))}
          />
        </label>

        {/* ⑴ 업로드 가능 — **놓기 전에** 말한다. 무엇이든 올라간다는 사실이 먼저다 (PRD-21) */}
        <p className="up-note" data-testid="up-any-format">
          {UPLOAD_ANY_FORMAT_NOTICE}
        </p>

        {/* ⑵ 미리보기 가능 — 놓은 것의 확장자를 보고 말한다. **막지 않는다**, 말만 다르다 */}
        {props.picked.length > 0 && (
          <p className="up-note" data-testid="up-previewable">
            {previewabilityNotice(extensionOf((bodies[0] ?? grids[0])?.p.file.name ?? ''))}
          </p>
        )}

        {/* 뺀 것이 1건 이상일 때만 말한다 — 문면은 rev1 `H-37` 축자다 */}
        {mixedNotice && (
          <p className="up-toast" data-testid="up-ext-toast" role="status" aria-live="polite">
            {MIXED_EXTENSION_NOTICE}
          </p>
        )}

        {props.picked.length > 0 && (
          <div className="filelist" data-testid="up-files">
            {/* 조각 묶음이면 **요약 한 줄**이고 목록은 눌렀을 때만 편다 (§8 · `DataModel §4.3`) */}
            {bundle && (
              <>
                <div className="filecard is-bundle" data-testid="up-bundle">
                  <div className="fmeta">
                    <div className="fn">
                      {bodies[0]?.p.file.name}
                      <span className="chip chip--neutral">조각 {bodies.length}</span>
                    </div>
                    <div className="fs">합계 {humanSize(totalBytes(bodies.map(({ p }) => p)))}</div>
                  </div>
                </div>
                <button
                  type="button"
                  className="slicebtn"
                  onClick={() => setSlicesOpen((v) => !v)}
                >
                  조각 {bodies.length}개 {slicesOpen ? '접기' : '모두 보기'}
                </button>
              </>
            )}

            {(!bundle || slicesOpen) && (
              <div className={bundle ? 'slicelist' : ''} data-testid={bundle ? 'up-slices' : undefined}>
                {bodies.map(({ p, i }) => (
                  <FileRow key={`${p.file.name}-${i}`} picked={p} onKind={(k) => props.onKind(i, k)} />
                ))}
              </div>
            )}
          </div>
        )}

        {/* 기준 격자 파일은 본체 목록과 **따로** 세운다 (§8) */}
        {grids.length > 0 && (
          <div className="companion" data-testid="up-companion">
            <span className="cl">기준 격자 파일</span>
            {grids.map(({ p, i }) => (
              <div className="cline" key={`${p.file.name}-${i}`}>
                <span className="cn">{p.file.name}</span>
                <span className="cw">이 파일이 있어야 지도에 그려요</span>
                <FileRow picked={p} onKind={(k) => props.onKind(i, k)} />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
