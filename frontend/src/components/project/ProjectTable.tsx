// §5 표 보기 — 견줄 때의 자리. `기록 없음`·`승인 / 전체` 는 프로젝트가 3건이든 50건이든
// 똑같이 읽히고, **열은 모든 프로젝트가 동시에 비교된다**(펼침은 한 번에 하나뿐이었다).
//
// **행을 펴지 않는다** (1.5 이력). 누르면 상세로 간다.
import { projectPeriod } from './format';
import type { ProjectRow } from './types';

export function ProjectTable(props: { rows: ProjectRow[]; onOpen(projectId: string): void }) {
  return (
    <table className="pj-table">
      <thead>
        <tr>
          <th scope="col">프로젝트</th>
          <th scope="col">유형</th>
          <th scope="col">데이터셋</th>
          <th scope="col">기간</th>
          <th scope="col">기록 없음</th>
          {/* 같은 아이콘의 두 뜻을 가른다 — 목록은 개수, 상세는 상태다 (§8) */}
          <th scope="col">Verified</th>
        </tr>
      </thead>
      <tbody>
        {props.rows.map((row) => (
          <tr
            key={row.projectId}
            data-testid={`project-trow-${row.projectId}`}
            data-closed={row.status === '닫힘' ? 'true' : undefined}
            onClick={() => props.onOpen(row.projectId)}
          >
            <td className="pname">
              {row.name}
              {row.status === '닫힘' ? <span className="chip chip--closed">닫힘</span> : null}
            </td>
            <td>{row.type}</td>
            <td>{row.datasetCount}개</td>
            <td className="mono">{projectPeriod(row.period)}</td>
            {/* 1건부터 강조색. 0이면 `—` 가 아니라 0 을 적는다 — 열은 세로로 견주는 자리다 */}
            <td data-warn={row.unknownLineageCount > 0 ? 'true' : undefined}>
              {row.unknownLineageCount}
            </td>
            <td data-testid="verified-cell">
              {row.verifiedCount} / {row.datasetCount}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
