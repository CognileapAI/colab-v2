// 섹션 4 「어떻게 쓰였나 · 가져가기」 — 활용 프로젝트 목록 + 다운로드 진입점.
//
// **판단 순서의 마지막 칸이다** — 기본 정보 → 계보 → 미리보기 → **활용**
// (`Policy_데이터셋_상세 §4` 판단 순서 · §3.1 정상 예시).
//
// ⑴ 목록 (`§8` 활용 프로젝트 목록 · `§5` 표) — 카드를 세로로 쌓아 **전부** 보여주고, 위에
//    「이 데이터를 쓴 과제·논문 N건」 한 줄을 둔다. **N 은 계보 그래프의 활용 배지 숫자와 같은
//    값이다** — 배지를 눌러 내려온 사람이 같은 숫자를 확인한다. 건마다 이름·유형·기간과
//    **연결마다 따로인** 의미 문장을 적는다. 0건이면 빈 상태 한 줄이다.
// ⑵ 다운로드 (`§8` 다운로드 행) — 원본 파일 그대로, 부분 다운로드 없음. **조각 묶음이면 묶어서
//    한 번에** 받는다(`§2` 흐름 표 — 조각마다 버튼을 두면 72번 눌러야 한다). **용량은 이 자리의
//    버튼에 표시하고 받은 횟수는 보여주지 않는다.**
// ⑶ 판정은 서버가 한다 — `actions.canDownload` 가 꺼져 있으면 **숨긴다**(P-7·P-12).
//    잠긴 데이터는 이 구역에 닿지 않는다: `LockedContent` 가 본문째 막고 접근 요청 자리는
//    `LockedNotice` 한 곳뿐이다(`§3.3`·`§7`). 여기에 두 번째 요청 버튼을 만들지 않는다.
//
// ⚠ **`§5` 표는 「이름·유형·기간·담당」을 적지만 계약 `DatasetProjectUse` 에 담당이 없다.**
//    없는 값을 지어내지 않는다 — 이 자리는 비운 채 두고 그 사실을 대장에 적었다.
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { downloadDataset } from '../../api/download';
import { projectPeriod } from '../project/format';
import { formatBytes } from './format';
import type { DatasetDetail } from './types';

/**
 * 접근 값의 **출처 문장** (PRD-39 ⑩ · rev1 접근·다운로드 카드 축자).
 *
 * 왜 필요한가: 접근 관련 값은 상세에서 처음 보이지만 **정해진 자리는 업로드**다. 어디서 온
 * 값인지 말하지 않으면 사용자는 이 화면에서 정해진 값으로 읽고, 바꾸려고 여기서 길을 찾는다.
 * 문장이 그 자리와 바꿀 수 있는 사람을 함께 말한다.
 *
 * ⚠ **공개 범위 값 자체는 이 회차의 몫이 아니다** — 그 칸은 R-B 가 세운다(라운드 파일 §2-⑤).
 *    없는 값을 지어내지 않고, 출처 문장만 이 자리에 둔다.
 */
export const ACCESS_ORIGIN_NOTE =
  '업로드할 때 정한 값이에요 · 올린 사람과 연구실 설정 권한자가 바꿀 수 있어요.';

export function UsageSection(props: { detail: DatasetDetail }) {
  const [error, setError] = useState<string | null>(null);
  const uses = props.detail.projects ?? [];
  const files = props.detail.basicInfo?.files ?? null;

  return (
    <section className="dsec use-sec" id="sec-usage" data-testid="usage-section">
      <div className="dsec-h">
        <h2>어떻게 쓰였나 · 가져가기</h2>
      </div>

      <p className="use-n" data-testid="usage-count">
        이 데이터를 쓴 과제·논문 {uses.length}건
      </p>

      {uses.length === 0 ? (
        <p className="use-empty">아직 어느 과제·논문에도 담기지 않았어요</p>
      ) : (
        <ul className="use-u">
          {uses.map((u) => (
            <li key={u.projectId} className="use-c" data-testid="usage-card">
              <div className="use-t">
                <Link to={`/projects/${u.projectId}`}>{u.name}</Link>
                <span className="chip chip--neutral">{u.type}</span>
                {u.period ? <span className="use-p">{projectPeriod(u.period)}</span> : null}
              </div>
              {/* 의미 문장은 **연결마다 따로**다 — 같은 데이터라도 과제마다 쓰임이 다르다 (§5) */}
              {u.usageNote ? <p className="use-note">{u.usageNote}</p> : null}
            </li>
          ))}
        </ul>
      )}

      {props.detail.actions.canDownload ? (
        <div className="use-dl">
          <button
            type="button"
            className="btn btn-primary"
            data-testid="detail-download"
            onClick={() => {
              setError(null);
              void downloadDataset(props.detail.datasetId).catch(() => {
                setError(`${props.detail.name} 을(를) 내려받지 못했어요.`);
              });
            }}
          >
            다운로드
            {files && files.totalSizeBytes > 0 ? (
              <span className="use-dl-s"> · {formatBytes(files.totalSizeBytes)}</span>
            ) : null}
          </button>
          {/* 값의 출처 — 버튼 아래 한 줄 (PRD-39 ⑩). 다운로드가 막힌 사람에게는 이 구역째 없다 */}
          <p className="use-dl-note muted" data-testid="access-origin">
            {ACCESS_ORIGIN_NOTE}
          </p>
        </div>
      ) : null}

      {error ? (
        <p className="dlerr" role="alert">
          {error}
        </p>
      ) : null}
    </section>
  );
}
