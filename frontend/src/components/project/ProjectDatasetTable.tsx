// §5 소속 데이터셋 표 — **행에서 판단이 끝나도록 싣는다.**
//
// 열 여섯 = 이름 · 가공 단계 · 기간 · 계보 · Verified · 소속 해제.
// **`포맷` 열이 없다** — 파일명 끝의 확장자와 같은 값이라 한 행에서 같은 것을 두 번 읽게 된다
// (v1.6 이력 · E-02 와 같은 규칙).
//
// **자르지 않는다** — 더 보기·페이지 나누기를 두지 않는다 (§5 표 범위).
// **활용 의미 문장(`usageNote`) 열은 여기에 없다** — 목업의 여섯 열에 그 자리가 없고,
// 그 문장을 읽는 자리는 데이터셋 상세의 `활용 프로젝트` 다 (E-03).
import { LockIndicatorSlot } from '../../placeholders/LockIndicatorSlot';
import { dataPeriod } from './format';
import type { ProjectDatasetRow } from './types';

export function ProjectDatasetTable(props: {
  rows: ProjectDatasetRow[];
  canManage: boolean;
  onOpen(datasetId: string): void;
}) {
  return (
    <table className="pj-ds" data-testid="project-datasets">
      <thead>
        <tr>
          <th scope="col">데이터셋</th>
          <th scope="col">가공 단계</th>
          <th scope="col">기간</th>
          <th scope="col">계보</th>
          <th scope="col">Verified</th>
          <th scope="col" />
        </tr>
      </thead>
      <tbody>
        {props.rows.map((row) => (
          <tr
            key={row.datasetId}
            data-testid={`pds-${row.datasetId}`}
            // **잠긴 데이터는 숨기지 않는다** (P-13). 행은 그대로 서고 본체 자리만 닫힌다.
            data-locked={row.bodyAccessible ? undefined : 'true'}
            onClick={() => props.onOpen(row.datasetId)}
          >
            <td className="fname">
              {row.name}
              {/* 파일이 여러 건이면 이름 뒤에 `조각 N` 칩 (E-02 와 같은 규칙) */}
              {row.fileCount > 1 ? <span className="chip">조각 {row.fileCount}</span> : null}
              {row.bodyAccessible ? null : <LockIndicatorSlot />}
            </td>
            <td>
              <span className={`lvl lvl-${row.processingLevel}`}>Lv{row.processingLevel}</span>
            </td>
            <td className="mono">{dataPeriod(row.period)}</td>
            <td>
              <span className={row.lineageState === '기록 없음' ? 'lin-none' : 'lin-ok'}>
                {row.lineageState}
              </span>
            </td>
            {/* 상세 표는 데이터 한 건의 **상태**라 글자를 붙인다. 없으면 `—` — 빈칸은
                「값이 없음」과 「아직 안 봄」이 구분되지 않는다 (§8) */}
            <td data-testid="dataset-verified">{row.verified ? '승인됨' : '—'}</td>
            <td className="right">
              {/* 소속 해제는 `프로젝트 생성` 스위치가 켜진 사람만 (§6). 꺼졌으면 **숨긴다**
                  — 비활성 버튼으로 남기지 않는다 (P-12). 실물 op(`unlinkProjectDataset`)은
                  아직 501 이라 여기는 자리만 둔다. */}
              {props.canManage ? (
                <span className="quiet" data-slot="unlink" data-fills-in="unlinkProjectDataset">
                  소속 해제
                </span>
              ) : null}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
