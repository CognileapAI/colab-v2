// WU-C3 ⑵ — 틀 **안**의 컨트롤 줄: 파일 · 변수 · 시각 세 고르개.
//
// **한 컴포넌트로 두 화면이 같은 줄을 쓴다**(업로드 `PreviewPanel` · 상세
// `DatasetPreviewSection`). 두 벌로 두면 기본값 표시와 바꿔 그리기 규칙이 갈린다.
//
// 규율 넷 (판정 축자)
//  · 후보는 전부 **서버가 준 값**이다 — 파일은 files 조회, 변수·시각은 `describeTarget`.
//  · 기본값은 **describe 의 서버 선택값을 그대로 보여 준다** — 화면이 다른 값을 고르지 않는다.
//  · 한 번에 값 **하나**만 바뀐다 (`Policy_데이터셋_상세 §1.3-5` 바꿔 그리기).
//  · 고른 값은 **컴포넌트 상태**다 — URL 에 실리지 않는다.
//
// ⚠ 세 고르개는 **후보가 없어도 자리를 지킨다**(disabled). 자리가 사라지면 틀 안쪽 치수가
//   상태마다 달라지고, 그것은 WU-C1 이 막은 바로 그 일이다.
import {
  instantChoicesOf,
  shownInstant,
  shownVariable,
  TOO_LARGE_SECOND_SENTENCE,
  renderablePieces,
  type PickSelection,
  type PreviewPiece,
  type TargetDescription,
} from './pick';

export interface PreviewPickRowProps {
  /** 화면마다 다른 id 앞머리 — 한 문서에 두 줄이 서도 label 이 엉키지 않는다. */
  idPrefix: string;
  pieces: PreviewPiece[];
  description: TargetDescription | undefined;
  selection: PickSelection;
  /** 바꿔 그리기. **한 번에 한 축만 실려 온다.** */
  onPick: (next: PickSelection) => void;
  /** 그리는 중에는 고르지 않는다 — 겹쳐 그리기를 만들지 않는다. */
  disabled?: boolean;
  /**
   * 폴백이 고른 조각. 있으면 틀 안에 안내가 선다.
   * **문면은 `TOO_LARGE_MESSAGE` 둘째 문장이고, 조각 이름은 값으로 붙는다**(새 문장 0).
   */
  fallbackPiece?: PreviewPiece | undefined;
}

export function variableLabel(id: string): string {
  if (id.startsWith('hdf5:')) {
    const encoded = id.slice('hdf5:'.length);
    const slice = encoded.match(/^(.*?)(\[[0-9,]+\])$/);
    try {
      const path = decodeURIComponent(slice?.[1] ?? encoded);
      return slice ? `${path} · 슬라이스 ${slice[2]!.slice(1, -1)}` : path;
    } catch {
      return encoded;
    }
  }
  if (id.startsWith('grib:')) {
    const [prefix, epoch, level, comment, grid] = id.split('|');
    const [, message, ...elementParts] = (prefix ?? '').split(':');
    const seconds = Number(epoch);
    const time = Number.isFinite(seconds)
      ? new Date(seconds * 1000).toISOString().replace('.000Z', 'Z')
      : epoch;
    return [`메시지 ${message}`, elementParts.join(':'), time, level, comment, grid]
      .filter(Boolean)
      .join(' · ');
  }
  return id;
}

export function PreviewPickRow(props: PreviewPickRowProps) {
  const files = renderablePieces(props.pieces);
  const variables = props.description?.variables ?? [];
  const instants = instantChoicesOf(props.description?.instants);
  const disabled = props.disabled ?? false;
  // 조각이 하나뿐이면 **고를 것이 없다** — 자리는 그대로 두고 잠근다(건수를 함께 말한다).
  const singleFile = files.length <= 1;
  const shownFile = props.selection.fileId ?? files[0]?.fileId ?? '';

  return (
    <div className="pv-pick" data-testid={`${props.idPrefix}-pick-row`} aria-label="그릴 것 고르기">
      {props.fallbackPiece ? (
        <p className="pv-muted" data-testid={`${props.idPrefix}-piece-notice`} aria-live="polite">
          {TOO_LARGE_SECOND_SENTENCE}{' '}
          <span data-testid={`${props.idPrefix}-piece-name`}>{props.fallbackPiece.fileName}</span>
        </p>
      ) : null}

      <label className="pv-pick-f">
        <span>파일</span>
        <select
          className="sel"
          id={`${props.idPrefix}-pick-file`}
          data-testid={`${props.idPrefix}-pick-file`}
          value={shownFile}
          disabled={disabled || singleFile}
          onChange={(e) => props.onPick({ fileId: e.currentTarget.value })}
        >
          {files.map((f) => (
            <option key={f.fileId} value={f.fileId}>
              {f.fileName}
            </option>
          ))}
        </select>
        {/* 잠근 이유를 화면이 말한다 — 「고를 수 없다」와 「하나뿐이다」는 다른 사실이다. */}
        {singleFile ? (
          <span className="pv-muted" data-testid={`${props.idPrefix}-pick-file-count`}>
            {files.length}
          </span>
        ) : null}
      </label>

      <label className="pv-pick-f">
        <span>변수</span>
        <select
          className="sel"
          id={`${props.idPrefix}-pick-variable`}
          data-testid={`${props.idPrefix}-pick-variable`}
          value={shownVariable(props.selection, props.description)}
          disabled={disabled || variables.length === 0}
          onChange={(e) => props.onPick({ variable: e.currentTarget.value })}
        >
          {variables.map((v) => (
            <option key={v} value={v}>
              {variableLabel(v)}
            </option>
          ))}
        </select>
      </label>

      <label className="pv-pick-f">
        <span>시각</span>
        <select
          className="sel"
          id={`${props.idPrefix}-pick-instant`}
          data-testid={`${props.idPrefix}-pick-instant`}
          value={shownInstant(props.selection, props.description)}
          disabled={disabled || instants.length === 0}
          onChange={(e) => props.onPick({ instant: e.currentTarget.value })}
        >
          {instants.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}
