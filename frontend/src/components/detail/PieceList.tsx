/**
 * ⭑ ⟨병합 창 8-a⟩ 이 컴포넌트는 종전 `FileList.tsx` 에 있었고 이름도 `FileList` 였다.
 * PR #1 이 **같은 이름의 다른 컴포넌트**(파일 목록 ＋ 추가·교체·삭제 관리 · `〈175〉`·`〈339〉`)를
 * 같은 파일에 세워 add/add 충돌이 났다. **둘 다 산다 — 서로 다른 자리의 다른 화면이다.**
 *   · 이것(`PieceList`) = 기본 정보 격자 안에서 `보기` 로 펼치는 **조각 목록**(`Policy_데이터셋_상세 §5`).
 *   · `FileList.tsx` 의 `FileList` = 격자 아래 **파일 관리 구역**.
 * 이름만 갈랐고 마크업·CSS(`.filelist .fl-g/.fl-k/.fl-u/.fl-i/.fl-n/.fl-x`)는 한 글자도 안 바꿨다.
 */
// `파일` 칸의 `보기` 로 열리는 조각 목록 (`Policy_데이터셋_상세 §5` 122행 · §12 v1.9).
//
// 축자 셋을 그대로 지킨다 —
//  ⑴ **`보기` 를 눌렀을 때만** 부른다 (계약 `listDatasetFiles` 요약).
//  ⑵ **목록은 자체 스크롤을 만들지 않고 페이지 흐름을 그대로 쓴다** — 한 페이지 스크롤 화면
//     안에 스크롤 상자를 또 두면 휠이 어느 쪽에서 도는지가 커서 위치로 갈린다.
//     그래서 이 컴포넌트에도 `detail.css` 에도 `overflow`·`max-height` 를 두지 않는다.
//  ⑶ **기준 격자 파일은 없으면 없다고 적는다** — 짝 파일이 없어서 못 그리는 것인지
//     원래 필요 없는 포맷인지가 갈리기 때문이다.
import type { DatasetFile } from './filesSource';

/**
 * 기준 격자 파일이 어느 축을 싣고 있는지. **서버가 판별한 값을 읽기만 한다** —
 * 사용자에게 「위도냐 경도냐」를 묻지 않는다 (`DatasetFile.gridAxis` 산문).
 * 한 파일이 둘을 다 실을 수 있어 두 열이 따로 있다 (`0004` CHECK).
 */
function axisLabel(axis: DatasetFile['gridAxis']): string | null {
  if (!axis) return null;
  const 축 = [axis.carriesLat ? '위도' : null, axis.carriesLon ? '경도' : null].filter(Boolean);
  return 축.length === 0 ? null : 축.join('·');
}

export function PieceList(props: { files: DatasetFile[] }) {
  const 본체 = props.files.filter((f) => f.kind === '본체');
  const 격자 = props.files.filter((f) => f.kind === '기준 격자 파일');

  return (
    <div className="filelist" data-testid="file-list">
      <div className="fl-g" data-testid="file-body-group">
        <div className="fl-k">본체</div>
        {본체.length === 0 ? (
          <p className="fl-none">본체 조각이 없어요</p>
        ) : (
          <ul className="fl-u">
            {본체.map((f) => (
              <li key={f.fileId} className="fl-i">
                <span className="fl-n">{f.fileName}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
      <div className="fl-g" data-testid="file-grid-group">
        <div className="fl-k">기준 격자 파일</div>
        {격자.length === 0 ? (
          <p className="fl-none">기준 격자 파일이 없어요</p>
        ) : (
          <ul className="fl-u">
            {격자.map((f) => (
              <li key={f.fileId} className="fl-i">
                <span className="fl-n">{f.fileName}</span>
                {/* 어느 축에 배정됐는지는 서버가 판별해 내려준다 — 사람에게 묻지 않는다 */}
                {axisLabel(f.gridAxis) ? (
                  <span className="fl-x">{axisLabel(f.gridAxis)}</span>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
