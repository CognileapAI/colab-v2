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
import { displayLevel } from '../common/processingLevel';
import { dataPeriod } from './format';
import type { ProjectDatasetRow } from './types';

/**
 * 승인 대기 칸의 글자 — **카탈로그 표와 같은 말**이다(`CatalogTable.tsx` 앵커
 * `VERIFIED_PENDING_LABEL`). 두 표가 같은 상태를 다른 글자로 말하지 않게 맞춘다.
 * 열 제목 `Verified` 와 승인된 행의 「승인됨」은 무변이다.
 */
// Ted 문면 확정 대기 · R-LTH-REVIEW-1
const VERIFIED_PENDING_LABEL = '승인 전';

export function ProjectDatasetTable(props: {
  rows: ProjectDatasetRow[];
  canManage: boolean;
  onOpen(datasetId: string): void;
  /** 소속 해제 — **연결 기록만** 지운다. 데이터셋은 카탈로그에 그대로 있다 (`§7`). */
  onUnlink(datasetId: string): Promise<void>;
}) {
  // ⭑ ⟨R-LTH-REVIEW-1 · `I-6`⟩ 0행에서는 밀 것이 없다 — 좌우 이동 안내도, 초점만 받는
  //    빈 스크롤 영역도 세우지 않는다. 표 자체는 남기고 빈 상태를 표 **안**에서 말한다.
  const hasRows = props.rows.length > 0;

  return (
    <>
    {hasRows ? (
      <p className="table-scroll-hint">표를 좌우로 밀면 나머지 항목과 작업을 볼 수 있어요.</p>
    ) : null}
    <div
      className="pj-ds-scroll"
      role={hasRows ? 'region' : undefined}
      aria-label={hasRows ? '소속 데이터셋 표' : undefined}
      tabIndex={hasRows ? 0 : undefined}
    >
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
        {/* 0행 — 「없다」로 끝내지 않고 **담는 자리**를 말한다. 데이터셋을 프로젝트에 담는
            자리는 등록 `③ 연결` 의 `연관 프로젝트·논문` 하나다(`upload/RegisterArea.tsx`).
            선례 = `CatalogTable.tsx` 의 `<td colSpan={9} className="empty">`. */}
        {hasRows ? null : (
          <tr>
            <td colSpan={6} className="empty" data-testid="pds-empty">
              연결된 데이터셋이 없어요. 데이터셋을 올릴 때 ③ 연결 단계의 「연관 프로젝트·논문」에서
              이 프로젝트를 고르면 여기에 보여요.
            </td>
          </tr>
        )}
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
              {/* ⭑ ⟨WU-C9 · 질의 24·27·41⟩ 서버는 파생값과 사람 값을 나란히 내린다 —
                  고르는 것은 화면이고 그 규칙은 `displayLevel` 하나다. */}
              {displayLevel(row) === null ? null : (
                <span className={`lvl lvl-${displayLevel(row)}`}>Lv{displayLevel(row)}</span>
              )}
            </td>
            <td className="mono">{dataPeriod(row.period)}</td>
            <td>
              <span className={row.lineageState === '기록 없음' ? 'lin-none' : 'lin-ok'}>
                {row.lineageState}
              </span>
            </td>
            {/* 상세 표는 데이터 한 건의 **상태**라 글자를 붙인다 (§8 `승인됨`).
                ⭑ 승인이 아직 도착하지 않은 행은 **카탈로그와 같은 표기**를 쓴다 —
                취소선·회색·꺼진 조작(`〈282〉`-㉮ Ted 판정 2026-09-02 의 규칙 확장 ·
                검수 #8 「카탈로그는 취소선 `Verified`, 프로젝트 상세 표는 `—` — 같은
                상태를 두 표기로」). `—` 로 두면 「값이 없음」과 「아직 안 왔음」이
                두 화면에서 서로 다르게 읽힌다. 규칙은 `catalog.css .verified--pending`. */}
            <td data-testid="dataset-verified">
              {row.verified ? (
                '승인됨'
              ) : (
                <span
                  className="verified verified--pending"
                  data-testid="verified-pending"
                  aria-disabled="true"
                  title="승인 처리가 아직 도착하지 않았다"
                >
                  {VERIFIED_PENDING_LABEL}
                </span>
              )}
            </td>
            <td className="right">
              {/* 소속 해제는 `프로젝트 생성` 스위치가 켜진 사람만 (§6). 꺼졌으면 **숨긴다**
                  — 비활성 버튼으로 남기지 않는다 (P-12). */}
              {props.canManage ? (
                <button
                  type="button"
                  className="quiet"
                  onClick={() => void props.onUnlink(row.datasetId)}
                >
                  소속 해제
                </button>
              ) : null}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
    </div>
    </>
  );
}
