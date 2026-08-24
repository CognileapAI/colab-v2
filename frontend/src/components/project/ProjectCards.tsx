// §5 카드 보기 — 기본 보기다. **표는 설명을 담지 못한다.**
//
// 카드 구성 셋 — 위(이름·유형 칩·기간·설명 두 줄) / 가운데(지표 타일 세 칸) /
// 아래(이동 안내 한 줄). **진행 바를 두지 않는다** — 계보 진척은 퍼센트가 아니라 남은 건수다.
import { projectPeriod } from './format';
import type { ProjectRow } from './types';

function Tile(props: { n: number; label: string; warn?: boolean }) {
  return (
    <div
      className="pc-s"
      data-testid="metric-tile"
      // **값이 0이어도 칸을 비우지 않는다** — 카드마다 항목 수가 달라지면 세로로 못 견준다.
      // 0은 흐리게, 기록 없음은 1건부터 강조색 (§5 지표 타일).
      data-zero={props.n === 0 ? 'true' : undefined}
      data-warn={props.warn && props.n > 0 ? 'true' : undefined}
    >
      <span className="n">{props.n}</span>
      <span className="k">{props.label}</span>
    </div>
  );
}

export function ProjectCards(props: { rows: ProjectRow[]; onOpen(projectId: string): void }) {
  return (
    <div className="pj-cards">
      {props.rows.map((row) => (
        <article
          key={row.projectId}
          className="pcard"
          data-testid={`project-card-${row.projectId}`}
          data-closed={row.status === '닫힘' ? 'true' : undefined}
          onClick={() => props.onOpen(row.projectId)}
        >
          <div className="pc-body">
            <h3 className="pc-t">{row.name}</h3>
            <div className="pc-m">
              <span className="chip">{row.type}</span>
              {/* 닫힘은 **칩으로 밝힌다** — 투명도로 흐리게 만들지 않는다 (§5) */}
              {row.status === '닫힘' ? <span className="chip chip--closed">닫힘</span> : null}
              <span className="pc-term">{projectPeriod(row.period)}</span>
            </div>
            {row.description ? (
              <p className="pc-d">{row.description}</p>
            ) : (
              // 빈칸을 그냥 두면 비었다는 사실 자체가 안 보여 영영 안 채워진다 (§5 설명)
              <p className="pc-d is-empty">설명을 적어 두면 나중에 찾기 쉬워요</p>
            )}
          </div>

          <div className="pc-stats">
            <Tile n={row.datasetCount} label="데이터셋" />
            <Tile n={row.verifiedCount} label="승인" />
            <Tile n={row.unknownLineageCount} label="기록 없음" warn />
          </div>

          {/* 카드 전체가 이미 클릭 대상이라 **그 안에 또 하나의 클릭 대상을 세우지 않는다** (§8) */}
          <div className="pc-cta" data-testid="card-cta">
            <span className="cta-t">데이터셋 {row.datasetCount}개 보기</span>
            <span className="cta-a" aria-hidden="true">
              →
            </span>
          </div>
        </article>
      ))}
    </div>
  );
}
