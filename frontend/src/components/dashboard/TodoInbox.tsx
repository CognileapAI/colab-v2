// 할 일 함 — **카드는 전 구성원에게 보이고 권한 훅은 그룹 각각에 건다**
// (`Policy_홈_대시보드 §6` 축자). 카드 자체를 권한자 전용으로 두면 매일 쓰는 연구원의
// 할 일이 0건이 되고, 계보가 P0 인데 부르는 자리가 화면에 없으면 아무도 채우지 않는다.
//
// **그룹 순서** = 계보 확인(전원) → Verified 검토(교수) → 받은 접근 요청(교수·승인 위임) (§6).
// **처리할 수 없는 그룹은 통째로 없다** — 빈 그룹으로 남기면 권한이 있는 줄 알고 기다리게 된다.
//
// **홈에서 처리하지 않는다** (§1.2 · §7). 계보는 상세의 계보 구역으로, Verified 는 상세로
// 보낸다 — 홈에 승인 버튼을 두면 근거를 보지 않고 누르는 승인이 생긴다 (E-06).
// 마크업은 E-06 목업의 `.todo-grp` / `.titem` 구조를 그대로 쓴다 (§8 축자) — 같은 카드가
// 화면마다 다르게 생기지 않게 한다.
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { LINEAGE_TODO_PATH } from './SummaryTiles';
import { relativeTime } from './visits';
import type { AccessRequest, DashboardSource, LineageTodo, VerificationRequest } from './types';
import type { DashboardState, Slot } from './useDashboard';

/** 계보 확인 그룹은 **3건까지** 펼친다 (§8). */
const LINEAGE_SHOWN = 3;
/** 승인 계열 두 그룹은 **오래된 순으로 5건까지** — 값의 주인은 E-06 이다 (§8). */
const APPROVAL_SHOWN = 5;

/** 왜 확인해야 하는지 (§8 「데이터 이름과 왜 확인해야 하는지를 한 줄로」). */
function reasonOf(todo: LineageTodo): string {
  return todo.lineageState === '기록 없음' ? '계보 기록 없음' : '올린 뒤 파일이 바뀌었어요';
}

function Group(props: {
  name: string;
  count: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
}) {
  return (
    <section className="todo-grp">
      <h3>
        {props.name}
        <span className="todo-count">{props.count}</span>
      </h3>
      {props.children}
      {props.footer}
    </section>
  );
}

function More(props: { hidden: number; onOpen: () => void }) {
  // §8 「+N건 더 보기」 — **남은 수를 글자에 그대로 적는다.** 승인 계열은 전용 목록
  // 화면으로 내보내지 않는다(E-06) — 같은 카드 안에서 그 자리에 펼친다.
  if (props.hidden <= 0) return null;
  return (
    <button type="button" className="todo-more" onClick={props.onOpen}>
      +{props.hidden}건 더 보기
    </button>
  );
}

function LineageGroup(props: { slot: Slot<LineageTodo[]>; unsettledTotal: number | null }) {
  const navigate = useNavigate();
  const [all, setAll] = useState(false);
  if (props.slot.kind !== '있음') return null;
  const rows = props.slot.value;
  const shown = all ? rows : rows.slice(0, LINEAGE_SHOWN);
  return (
    <Group
      name="계보 확인"
      count={`대기 ${props.unsettledTotal ?? rows.length}건`}
      footer={
        <>
          <More hidden={rows.length - shown.length} onOpen={() => setAll(true)} />
          {/* §8 「계보 확인 필요 전체 보기」 — 접힌 나머지가 아니라 **연구실 전체**의
              확인 필요 목록으로 간다. 계보 확정 지표와 같은 곳이다. */}
          <button type="button" className="todo-all" onClick={() => navigate(LINEAGE_TODO_PATH)}>
            계보 확인이 필요한 데이터 {props.unsettledTotal ?? rows.length}건 전부 보기 →
          </button>
        </>
      }
    >
      {rows.length === 0 ? (
        <p className="dash-zero">확인할 계보가 없어요.</p>
      ) : (
        <ul>
          {shown.map((todo) => (
            <li className="titem" key={todo.datasetId}>
              <span className="titem-name">{todo.name}</span>
              <span className="titem-why">{reasonOf(todo)}</span>
              {/* 홈에서 계보를 확정하지 않는다 — 상세의 계보 구역까지 데려간다 (§2 · E-04). */}
              <button
                type="button"
                onClick={() => navigate(`/datasets/${todo.datasetId}#lineage`)}
              >
                계보 확인 →
              </button>
            </li>
          ))}
        </ul>
      )}
    </Group>
  );
}

function VerificationGroup(props: { slot: Slot<VerificationRequest[]> }) {
  const navigate = useNavigate();
  const [all, setAll] = useState(false);
  // **없음 = 교수가 아니다.** 그룹을 통째로 그리지 않는다 (§6).
  if (props.slot.kind !== '있음') return null;
  const rows = props.slot.value;
  const shown = all ? rows : rows.slice(0, APPROVAL_SHOWN);
  return (
    <Group
      name="Verified 검토 대기"
      count={`${rows.length}건`}
      footer={<More hidden={rows.length - shown.length} onOpen={() => setAll(true)} />}
    >
      {rows.length === 0 ? (
        <p className="dash-zero">검토할 요청이 없어요.</p>
      ) : (
        <ul>
          {shown.map((row) => (
            <li className="titem" key={row.dataset.datasetId}>
              <span className="titem-name">{row.dataset.name}</span>
              <span className="titem-why">
                {row.requester.name}가 승인을 요청했어요 · {relativeTime(row.requestedAt)}
              </span>
              {/* **홈에 승인 버튼을 두지 않는다** (§8 축자 · E-06). 링크만이다. */}
              <button
                type="button"
                onClick={() => navigate(`/datasets/${row.dataset.datasetId}`)}
              >
                상세에서 검토 →
              </button>
            </li>
          ))}
        </ul>
      )}
    </Group>
  );
}

function AccessItem(props: { row: AccessRequest; source: DashboardSource; onDone: () => void }) {
  const [rejecting, setRejecting] = useState(false);
  const [reason, setReason] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const row = props.row;

  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError(null);
    try {
      await action();
      props.onDone();
    } catch (e) {
      // **문구를 화면이 지어내지 않는다** — 서버 봉투의 message 를 그대로 올린다.
      setError(e instanceof Error ? e.message : '처리하지 못했어요.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <li className="titem" key={row.requestId}>
      <span className="titem-name">
        {row.requester.name} 연구원이 {row.dataset.name} 접근을 요청했어요
      </span>
      <span className="titem-why">
        {relativeTime(row.requestedAt)}
        {row.reason ? ` · 사유: ${row.reason}` : ''}
      </span>
      {rejecting ? (
        // **거절 사유는 1~300자 필수**이고 요청자에게 그대로 전달된다 (`Policy_승인_처리 §5`·§9).
        // 문구는 E-06 정본의 것이다 — 홈이 새로 짓지 않는다.
        <span className="titem-reject">
          <label>
            사유를 적어 주세요. 요청한 사람에게 그대로 전달돼요.
            <input
              type="text"
              maxLength={300}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
          </label>
          <button
            type="button"
            disabled={busy || reason.trim().length === 0}
            onClick={() => run(() => props.source.rejectAccessRequest(row.requestId, reason.trim()))}
          >
            거절 보내기
          </button>
        </span>
      ) : (
        <span className="titem-actions">
          {/* §8 「처리 버튼을 그 자리에 둔다」. 처리 **절차**는 E-06 이 정하고
              홈은 그 op 을 그대로 부른다 — 규칙을 두 곳에 적지 않는다 (§5.2). */}
          <button type="button" disabled={busy} onClick={() => setRejecting(true)}>
            거절
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={() => run(() => props.source.approveAccessRequest(row.requestId))}
          >
            승인
          </button>
        </span>
      )}
      {error ? <span className="dash-error">{error}</span> : null}
    </li>
  );
}

function AccessGroup(props: {
  slot: Slot<AccessRequest[]>;
  source: DashboardSource;
  onDone: () => void;
}) {
  const [all, setAll] = useState(false);
  if (props.slot.kind !== '있음') return null;
  const rows = props.slot.value;
  const shown = all ? rows : rows.slice(0, APPROVAL_SHOWN);
  return (
    <Group
      name="받은 접근 요청"
      count={`${rows.length}건`}
      footer={<More hidden={rows.length - shown.length} onOpen={() => setAll(true)} />}
    >
      {rows.length === 0 ? (
        <p className="dash-zero">받은 요청이 없어요.</p>
      ) : (
        <ul>
          {shown.map((row) => (
            <AccessItem key={row.requestId} row={row} source={props.source} onDone={props.onDone} />
          ))}
        </ul>
      )}
    </Group>
  );
}

/** 카드 머리의 `모두 N건` — 보이는 그룹의 합이다 (목업 축자 「할 일 함 · 14건」 · §3.1). */
function totalOf(state: DashboardState): number {
  const at = <T,>(slot: Slot<T[]>): number => (slot.kind === '있음' ? slot.value.length : 0);
  const lineage =
    state.summary.kind === '있음' ? state.summary.value.lineageUnsettledCount : at(state.lineageTodo);
  return lineage + at(state.verifications) + at(state.accessRequests);
}

export function TodoInbox(props: { state: DashboardState; source: DashboardSource }) {
  const s = props.state;
  const failed = [s.lineageTodo, s.verifications, s.accessRequests].some((x) => x.kind === '실패');
  const unsettled = s.summary.kind === '있음' ? s.summary.value.lineageUnsettledCount : null;

  return (
    <section className="dash-card" data-card="todo-inbox" data-slot="todo-inbox">
      <div className="dash-card-head">
        <h2>할 일 함</h2>
        <span className="todo-total">{totalOf(s)}건</span>
      </div>
      {failed ? (
        // §9 문구 그대로 + 다시 불러오기 버튼.
        <p className="dash-error">
          처리할 일을 불러오지 못했어요. 잠시 뒤 다시 시도해 주세요.{' '}
          <button type="button" className="dash-quiet" onClick={s.reload}>
            다시 불러오기
          </button>
        </p>
      ) : null}
      <LineageGroup slot={s.lineageTodo} unsettledTotal={unsettled} />
      <VerificationGroup slot={s.verifications} />
      <AccessGroup slot={s.accessRequests} source={props.source} onDone={s.reload} />
    </section>
  );
}
