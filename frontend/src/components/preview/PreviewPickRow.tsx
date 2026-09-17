// WU-C3 ⑵ — 틀 **밖·틀보다 앞**의 컨트롤 줄: 파일 · 변수 · 시각 세 고르개.
//   ⭑ ⟨개정 2026-09-12 · R-BUGFIX-260912 `#25`⑵ · spec v2 §5 ㉮⟩ ／ 종전 표기 ~~틀 **안**의
//     컨트롤 줄~~ — 틀 안 스크롤 영역(`.pv-frame-in` · `overflow:auto`)의 첫 자식이라
//     그림이 렌더되면 스크롤 위로 밀려 화면에서 빠졌다. 자리는 `PreviewSlot` 의 `controls`
//     프로퍼티가 만드는 컨테이너(`.pv-frame-wrap`)이고, 틀보다 앞선 형제로 선다.
//
// **한 컴포넌트로 세 화면이 같은 줄을 쓴다**(업로드 `PreviewPanel` · 상세
// `DatasetPreviewSection` · 확장보기 — 같은 파일의 오버레이 JSX).
//   ⭑ ⟨개정 2026-09-12 · R-BUGFIX-260912 · Ted 판정 ⑥⟩ ／ 종전 표기 ~~두 화면~~.
// 두 벌로 두면 기본값 표시와 바꿔 그리기 규칙이 갈린다.
//
// 규율 넷 (판정 축자)
//  · 후보는 전부 **서버가 준 값**이다 — 파일은 files 조회, 변수·시각은 `describeTarget`.
//  · 기본값은 **describe 의 서버 선택값을 그대로 보여 준다** — 화면이 다른 값을 고르지 않는다.
//  · 한 번에 값 **하나**만 바뀐다 (`Policy_데이터셋_상세 §1.3-5` 바꿔 그리기).
//  · 고른 값은 **컴포넌트 상태**다 — URL 에 실리지 않는다.
//
// ⚠ 세 고르개는 **후보가 없어도 자리를 지킨다**(disabled).
//   ⭑ ⟨개정 2026-09-12 · R-BUGFIX-260912 `#25`⑵⟩ 존치 근거를 **세 화면 자리 일관성**으로
//     고쳐 적는다. ／ 종전 근거 ~~자리가 사라지면 틀 안쪽 치수가 상태마다 달라지고, 그것은
//     WU-C1 이 막은 바로 그 일이다~~ — 줄이 틀 **밖**으로 나갔으므로 「틀 안쪽 치수」 근거는
//     더 이상 성립하지 않는다(치수 불변은 `PreviewSlot` 이 계속 진다). 줄이 상태에 따라
//     사라지면 세 화면에서 조작의 자리가 상태마다 달라지고, 사용자가 매번 찾아야 한다.
//     disabled 존치 자체는 무변이다.
//   ⭑ ⟨예외 신설 2026-09-13 · 업로드 화면 한 자리⟩ **업로드 모달 좌측 인라인**은 후보가 둘 이상일
//     때만 변수·시각 고르개를 그린다(`hideSingleChoice`). 근거 = 기획서 rev2 — 업로드 좌측은
//     「첫 변수·기간 평균 한 장」이고 변수·시각 선택을 그리지 않는다. 고를 것이 하나뿐인데 잠긴
//     고르개를 세우면 등록 흐름에 조작할 수 없는 칸이 둘 늘어난다. ⛔ 데이터셋 상세·확장보기
//     오버레이는 이 예외를 쓰지 않는다 — 그 두 자리는 위 disabled 존치 규율 그대로다.
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
  /**
   * **업로드 화면 전용 예외** — 켜면 변수 고르개는 변수가 2개 이상일 때, 시각 고르개는
   * `instants.count` 가 2 이상일 때만 선다. 파일 고르개는 무변(하나뿐이면 잠그고 건수를 말한다).
   * 기본값 `false` = 세 고르개가 자리를 지키는 현행 규율(상세·확장보기).
   */
  hideSingleChoice?: boolean;
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
  const shownFileName = files.find((file) => file.fileId === shownFile)?.fileName ?? '';
  const shownVariableId = shownVariable(props.selection, props.description);
  const shownInstantId = shownInstant(props.selection, props.description);
  // 업로드 예외의 판정 — **후보 수**로 가른다. 시각은 목록이 아니라 범위라 `count` 가 원본이다
  // (`instantChoicesOf` 는 처음·마지막 둘만 세우므로 건수 판정에 쓰지 않는다).
  const hideSingle = props.hideSingleChoice ?? false;
  const showVariable = !hideSingle || variables.length >= 2;
  const showInstant = !hideSingle || (props.description?.instants?.count ?? 0) > 1;

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
          title={shownFileName}
          disabled={disabled || singleFile}
          onChange={(e) => props.onPick({ fileId: e.currentTarget.value })}
        >
          {files.map((f) => (
            <option key={f.fileId} value={f.fileId} title={f.fileName}>
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

      {showVariable ? (
      <label className="pv-pick-f">
        <span>변수</span>
        <select
          className="sel"
          id={`${props.idPrefix}-pick-variable`}
          data-testid={`${props.idPrefix}-pick-variable`}
          value={shownVariableId}
          title={variableLabel(shownVariableId)}
          disabled={disabled || variables.length === 0}
          onChange={(e) => props.onPick({ variable: e.currentTarget.value })}
        >
          {variables.map((v) => (
            <option key={v} value={v} title={variableLabel(v)}>
              {variableLabel(v)}
            </option>
          ))}
        </select>
      </label>
      ) : null}

      {showInstant ? (
      <label className="pv-pick-f">
        <span>시각</span>
        <select
          className="sel"
          id={`${props.idPrefix}-pick-instant`}
          data-testid={`${props.idPrefix}-pick-instant`}
          value={shownInstantId}
          title={shownInstantId}
          disabled={disabled || instants.length === 0}
          onChange={(e) => props.onPick({ instant: e.currentTarget.value })}
        >
          {instants.map((t) => (
            <option key={t} value={t} title={t}>
              {t}
            </option>
          ))}
        </select>
      </label>
      ) : null}

      <details className="pv-pick-values" data-testid={`${props.idPrefix}-pick-values`}>
        <summary>선택값 전체 보기</summary>
        <dl>
          <div><dt>파일</dt><dd>{shownFileName}</dd></div>
          <div><dt>변수</dt><dd>{variableLabel(shownVariableId)}</dd></div>
          <div><dt>시각</dt><dd>{shownInstantId}</dd></div>
        </dl>
      </details>
    </div>
  );
}
