// S-04 「파일 놓기」 — 정본 §8 파일 놓기 · 올린 파일 표시 · 기준 격자 파일 세 묶음.
//
// **번호를 붙이지 않는다** (§8 단계 번호) — 파일 놓기·바로 미리보기는 절차가 아니라
// 파일을 열어 보는 일이다.
// **축(위도·경도)을 사람에게 묻지 않는다** — 서버가 파일에서 판별한다 (`〈63〉-㉰`).
import { useState } from 'react';
import { collectDrop } from './dropTree';
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
        {/* 폴더에서 왔으면 어느 폴더의 무엇인지가 곧 이름이다 */}
        <div className="fn">{picked.relativePath ?? picked.file.name}</div>
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
  /** `paths` 는 폴더째 드롭에서만 온다 — 파일 → `폴더/이름` 상대 경로. */
  onPick: (files: File[], paths?: ReadonlyMap<File, string>) => void;
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
        {/* 여러 개를 한 번에 받는다 — 드롭 영역이 그렇게 말한다 (§8).
            실제 드롭은 여기 핸들러가 받는다 — 숨긴 1px 인풋에는 드롭이 닿지 않는다.
            폴더가 떨어지면 dropTree 가 재귀로 펼친다 (`〈337〉`). */}
        <label
          className="dropzone"
          data-testid="up-drop"
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            void collectDrop(e.dataTransfer).then((dropped) => {
              if (dropped.length === 0) return;
              const paths = new Map(
                dropped.flatMap((d) => (d.relativePath ? [[d.file, d.relativePath] as const] : [])),
              );
              props.onPick(dropped.map((d) => d.file), paths.size > 0 ? paths : undefined);
            });
          }}
        >
          <span className="big">파일을 끌어다 놓으세요</span>
          {/* **폴더는 끌어다 놓아야 한다** — 눌러서 여는 파일 선택창으로는 폴더를 고를 수 없다
              (인풋에 `webkitdirectory` 를 붙이면 낱개 파일 선택이 죽는다). 화면이 그 말을
              안 하면, 폴더를 올리려는 사람은 유일하게 눌러 보이는 것을 누르고 막힌다. */}
          <span className="muted">여러 개를 한 번에, 폴더째 끌어다 놓아도 돼요</span>
          <input
            type="file"
            multiple
            className="hidden-input"
            data-testid="up-drop-input"
            onChange={(e) => handlePick(Array.from(e.target.files ?? []))}
          />
        </label>

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
