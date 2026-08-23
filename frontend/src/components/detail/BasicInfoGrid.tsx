// 기본 정보 — **아홉 칸**: 구성 · 좌표계 · 기간 · 격자 · 포맷 · 파일 · 원천 표기 · 소유자 · 올린 사람
// (`Policy_데이터셋_상세 §5`). 공간 범위 칸은 두지 않는다 — 이름과 지도가 이미 말한다.
// 잠긴 데이터는 이 블록을 통째로 비운다(`basicInfo` null) — 부르는 쪽이 아예 그리지 않는다.
import { EMPTY, formatFiles, formatPeriod, orEmpty } from './format';
import type { DatasetBasicInfo } from './types';

export function BasicInfoGrid(props: { basicInfo: DatasetBasicInfo; fileName: string | null }) {
  const b = props.basicInfo;
  const cells: [string, string][] = [
    ['구성', b.variables.length > 0 ? b.variables.join(' · ') : EMPTY],
    ['좌표계', orEmpty(b.crs)],
    ['기간', formatPeriod(b.period)],
    ['격자', orEmpty(b.grid)],
    ['포맷', orEmpty(b.format)],
    ['파일', formatFiles(b.files, props.fileName)],
    ['원천 표기', orEmpty(b.sourceLabel)],
    ['소유자', b.owner.name],
    ['올린 사람', b.uploader.name],
  ];
  return (
    <div className="infogrid" data-testid="basic-info">
      {cells.map(([k, v]) => (
        <div className="ig" key={k} data-testid={`ig-${k}`}>
          <div className="k" data-testid="ig-k">
            {k}
          </div>
          <div className="v">{v}</div>
        </div>
      ))}
    </div>
  );
}
