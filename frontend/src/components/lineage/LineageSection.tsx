// ④ S-05 상세 — **계보 · 족보** 구역 (WU-P3).
//
// 이 구역이 지키는 것 (`Policy_데이터셋_상세 §1-2·§2·§3.2·§5·§8·§9`)
//  - **가로축에는 데이터만 세운다.** 프로젝트는 노드가 아니라 배지다 (§1-2·§4 용어).
//  - 축은 원천(점선) → 가공 전 → 이 데이터(굵은 테두리) → 파생. **화면을 넘으면 가로 스크롤**하고
//    접거나 요약하지 않는다 (§8). 노드 몇 개부터 다른 표현인지는 정본이 정하지 않았다 (§11).
//  - **원천·묘비는 이동하지 않는다** — 열 화면이 없다. 잠긴 노드는 사라지지 않고 잠긴 상세로 간다.
//  - **가공 방식은 관계에 붙는다** — 노드가 아니라 화살표 위 라벨이고, AI 경로에만 ✦ 를 붙인다.
//  - **파생은 읽기 전용**이다. 자식을 올릴 때 확정된 이력이라 여기서 고치지 않는다 (§3.2).
//  - **편집 컨트롤은 `canEdit` 이 켜졌을 때만 화면에 존재한다** (§3.2·§6 · P-12).
//  - 화면 글자는 정본·목업에서 그대로 온다. 없는 값을 지어내지 않는다.
import { useEffect, useMemo, useRef, useState } from 'react';
import { useWorkProtection } from '../../auth/useWorkProtection';
import { Link } from 'react-router-dom';
import { Toast } from '../common/Toast';
import { PRE_LINEAGE_ADDED } from '../common/toastCopy';
import { displayLevel } from '../common/processingLevel';
import type { LineageEdge, LineageGraph, LineageNode } from './graphTypes';
import { LineageFixModal, type ParentCandidateSource } from './LineageFixModal';
import { apiLineageEditSource, type LineageEditSource } from './lineageEditSource';
import { apiLineageSource } from './lineageSource';
import { useReadOnlyScope } from '../../permission/PermissionGate';
import './lineageGraph.css';

/** 목업 `linHint` 두 문장. 기록 없음은 별도 화면이 아니라 이 구역의 상태 변형이다. */
const HINT = '가공 방식은 화살표 라벨 · 데이터 상자를 누르면 그 상세로 가요';
const HINT_EMPTY = '아직 채워지지 않은 계보예요';

/** 노드 종류별 역할 라벨 — 목업 `n-role` 그대로다. */
const ROLE_LABEL: Record<LineageNode['kind'], string> = {
  원천: '원천',
  '가공 전': '가공 전',
  '이 데이터': '이 데이터',
  파생: '이걸로 만든 데이터',
  묘비: '지워진 데이터',
};

/** 계보 상세 행의 단계 라벨. 목업 `stg` 그대로다. */
const STAGE_LABEL: Record<LineageNode['kind'], string> = {
  원천: '원천',
  '가공 전': '가공 전',
  '이 데이터': '이 데이터',
  파생: '파생',
  묘비: '지워진 데이터',
};

function day(ts: string): string {
  return ts.slice(0, 10);
}

/**
 * 노드가 서는 칸. 묘비는 `kind` 만으로는 부모 쪽인지 자식 쪽인지 모른다 —
 * **관계로 가른다.** 어느 쪽도 아니면 부모 자리에 세운다 (자식은 이 데이터에서 뻗어야 생긴다).
 */
function columnOf(node: LineageNode, graph: LineageGraph): 0 | 1 | 2 | 3 {
  switch (node.kind) {
    case '원천':
      return 0;
    case '가공 전':
      return 1;
    case '이 데이터':
      return 2;
    case '파생':
      return 3;
    case '묘비': {
      const id = node.datasetId;
      const isChild = graph.edges.some(
        (e) => e.parentDatasetId === graph.datasetId && e.childDatasetId === id,
      );
      return isChild ? 3 : 1;
    }
  }
}

/** 관계가 건너는 칸 경계. 자식 노드가 선 칸의 왼쪽 경계다. */
function railOf(edge: LineageEdge, graph: LineageGraph): 0 | 1 | 2 {
  const child = graph.nodes.find((n) => n.datasetId === edge.childDatasetId);
  const col = child ? columnOf(child, graph) : 2;
  return (col === 3 ? 2 : col === 2 ? 1 : 0) as 0 | 1 | 2;
}

function nodeTitle(node: LineageNode): string | undefined {
  if (node.kind === '원천') return '연구실 밖 출처라 상세 화면이 없어요';
  // 묘비의 hover 문구는 지운 날짜를 함께 말한다 (§8). 날짜가 없으면 그 자리를 지어내지 않는다
  if (node.kind === '묘비') {
    return node.deletedAt
      ? `지워진 데이터라 상세 화면이 없어요 · ${day(node.deletedAt)}`
      : '지워진 데이터라 상세 화면이 없어요';
  }
  return undefined;
}

function NodeBody(props: { node: LineageNode }) {
  const n = props.node;
  // ⭑ **⟨WU-C9 · 질의 27·41⟩ 노드가 그리는 Lv 도 사람 값 우선이다.** 응답의
  //    `processingLevel` 은 파생값 그대로이고(서버가 덮어 쓰지 않는다), 옆에 실린
  //    `processingLevelUserSet` 을 화면이 골라 쓴다 — 규칙은 `displayLevel` 한 자리다.
  const lv = displayLevel(n);
  return (
    <>
      <span className="n-head">
        {lv === null ? null : (
          <span className={`lvl lvl-${lv}`} data-testid="lin-lv">
            Lv{lv}
          </span>
        )}
        <span className="n-role">{ROLE_LABEL[n.kind]}</span>
      </span>
      <span className="n-name">{n.name}</span>
    </>
  );
}

function GraphNode(props: { node: LineageNode }) {
  const n = props.node;
  const cls = [
    'ln',
    n.kind === '이 데이터' ? 'is-self' : '',
    n.kind === '원천' ? 'is-src' : '',
    n.kind === '묘비' ? 'is-tomb' : '',
  ]
    .filter(Boolean)
    .join(' ');

  // 이동하는 노드만 링크다. 원천·묘비는 열 화면이 없고, 잠긴 노드는 **사라지지 않고** 링크로 남는다
  if (n.navigable && n.datasetId) {
    return (
      <Link
        className={cls}
        to={`/datasets/${n.datasetId}`}
        data-testid="lin-node"
        data-kind={n.kind}
        data-dataset-id={n.datasetId}
      >
        <NodeBody node={n} />
        <span className="arw">›</span>
      </Link>
    );
  }
  return (
    <div
      className={cls}
      data-testid="lin-node"
      data-kind={n.kind}
      data-dataset-id={n.datasetId ?? undefined}
      title={nodeTitle(n)}
    >
      <NodeBody node={n} />
    </div>
  );
}

/** 경로 플래그. `processed` 는 정본이 문구를 주지 않아 **지어내지 않는다**. */
function OriginFlag(props: { origin: LineageEdge['origin'] }) {
  if (props.origin === 'ai') {
    return (
      <span className="aiflag" data-testid="lin-flag" data-origin="ai">
        <span className="sp">✦</span>
        AI 제안 · 확인됨
      </span>
    );
  }
  if (props.origin === 'manual') {
    return (
      <span className="manflag" data-testid="lin-flag" data-origin="manual">
        직접 연결
      </span>
    );
  }
  return null;
}

function DetailRow(props: { edge: LineageEdge; node: LineageNode | undefined; derived: boolean; datasetId?: string; editSource?: LineageEditSource | undefined; onSaved?: (graph: LineageGraph) => void }) {
  const { edge, node, derived } = props;
  const [editing, setEditing] = useState(false);
  const [removing, setRemoving] = useState(false);
  const [method, setMethod] = useState(edge.method ?? '');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  useWorkProtection(`lineage-edge:${props.datasetId ?? 'none'}:${edge.parentDatasetId ?? 'none'}`, {
    dirty: (editing && method !== (edge.method ?? '')) || removing,
    inFlight: busy,
    discard: () => {
      setMethod(edge.method ?? ''); setEditing(false); setRemoving(false); setError(null);
    },
  });
  const active = useRef(true);
  useEffect(() => { active.current = true; return () => { active.current = false; }; }, []);
  const editable = !derived && !!props.editSource && !!edge.parentDatasetId;
  async function save(remove = false) {
    if (busy || !props.datasetId || !edge.parentDatasetId || !props.editSource) return;
    const action = remove ? props.editSource.removeParent : props.editSource.updateMethod;
    if (!action) return;
    setBusy(true); setError(null);
    try {
      const next = remove ? await props.editSource.removeParent!(props.datasetId, edge.parentDatasetId) : await props.editSource.updateMethod!(props.datasetId, edge.parentDatasetId, method);
      if (!active.current) return;
      props.onSaved?.(next); setEditing(false); setRemoving(false);
    } catch (reason) {
      if (active.current) setError(reason instanceof Error ? reason.message : '계보를 저장하지 못했어요.');
    } finally { if (active.current) setBusy(false); }
  }
  const kind = node?.kind ?? (derived ? '파생' : '가공 전');
  const name = node?.name ?? '—';
  const hist = `확인 ${edge.confirmedBy.name} · ${day(edge.confirmedAt)}${
    derived ? ' · 여기서는 못 고쳐요' : ''
  }`;
  return (
    <div className="lrow" data-testid="lrow" data-stage={STAGE_LABEL[kind]}>
      <span className="stg">{STAGE_LABEL[kind]}</span>
      <div>
        <div className="ln-line">
          {node && node.navigable && node.datasetId ? (
            <Link className="ln-go" to={`/datasets/${node.datasetId}`}>
              <span className="ln-name">{name}</span>
              <span className="arw">›</span>
            </Link>
          ) : (
            <span className="ln-name" title={node ? nodeTitle(node) : undefined}>
              {name}
            </span>
          )}
          <OriginFlag origin={edge.origin} />
        </div>
        {/* 값이 없으면 **구분자도 없다** (검수 #23 — 빈 가공 방식 앞의 `·` 로 줄이 시작했다).
            빈 조각을 걷어낸 뒤 남은 것만 `·` 로 잇는다. */}
        <div className="ln-sub">
          {edge.method ? <span className="way">{`가공 방식: ${edge.method} · `}</span> : null}
          <span className="hist">{hist}</span>
        </div>
        {editable && <div className="lin-relation-actions">
          {editing ? <label>가공 방식<input className="inp" value={method} disabled={busy} onChange={event => setMethod(event.target.value)} /><button type="button" className="btn btn-primary btn-sm" disabled={busy} onClick={() => void save()}>가공 방식 저장</button><button type="button" className="btn btn-secondary btn-sm" disabled={busy} onClick={() => { setEditing(false); setError(null); }}>취소</button></label>
            : props.editSource?.updateMethod && <button type="button" className="btn btn-secondary btn-sm" disabled={busy || removing} onClick={() => { setMethod(edge.method ?? ''); setEditing(true); }}>가공 방식 수정</button>}
          {removing ? <div><p>이 데이터와의 연결만 제거해요. 원본 데이터는 남아요.</p><button type="button" className="btn btn-secondary btn-sm" disabled={busy} onClick={() => void save(true)}>이 연결 제거</button><button type="button" className="btn btn-ghost btn-sm" disabled={busy} onClick={() => { setRemoving(false); setError(null); }}>취소</button></div>
            : props.editSource?.removeParent && <button type="button" className="btn btn-ghost btn-sm" disabled={busy || editing} onClick={() => setRemoving(true)}>연결 제거</button>}
          {busy && <p role="status">계보를 저장하는 중이에요…</p>}
          {error && <p role="alert">{error}</p>}
        </div>}
      </div>
      {node && displayLevel(node) !== null ? (
        <span className={`lvl lvl-${displayLevel(node)}`}>Lv{displayLevel(node)}</span>
      ) : (
        <span />
      )}
    </div>
  );
}

export function LineageSection(props: {
  graph: LineageGraph;
  /**
   * ⭑ **⟨advisor ② F1⟩ 모달 기준 Lv — 사람이 고른 값**(`levelOf(processingLevelUserSet)`,
   * `DatasetDetailPage.tsx` 가 넘긴다). 서버 400 도 이 값을 기준으로 판정한다(`lineage.py
   * user_set_level()`) — 그래프 노드의 파생 Lv 와는 다른 값일 수 있다. `null`/미전달이면
   * **그때만** 그래프의 「이 데이터」 노드 파생 Lv 로 물러난다(잠긴 상세처럼 `basicInfo` 가
   * 없을 때의 대비다 — 화면을 완전히 막지 않는다).
   */
  selfLv?: number | null;
  /** 상세가 이미 읽어 온 값. 계보 응답에는 없다 — 「이후 수정됨」은 이 둘을 나란히 놓는 표시다 (§2). */
  lastModifiedAt?: string | null;
  /**
   * ⭑ **⟨WU-B10 · PRD-31⟩ 계보 수정·추가 모달의 두 출처.** 시험이 대역을 꽂는 자리이고,
   * 기본값은 실서버다 — 후보는 **등록 ③ 이 쓰는 그 출처**(`apiLineageSource`)를 그대로 쓴다.
   */
  candidateSource?: ParentCandidateSource;
  editSource?: LineageEditSource;
  /**
   * PRD-22 — 편집 화면의 `계보 부모 연결` 이 이 모달을 연다. 값이 오를 때마다 한 번 열린다.
   * ⛔ 편집 폼 안에 계보 표를 그리지 않는다 — 같은 규칙을 두 곳이 각자 구현하지 않게 한다.
   */
  openToken?: number;
}) {
  // 저장 응답으로 온 그래프가 **재조회 없이** 이 자리를 받는다. 화면이 값을 손으로 조립하지
  // 않고 **서버가 돌려준 그래프**를 그대로 세운다 — 낙관적 갱신이 아니다.
  const [saved, setSaved] = useState<LineageGraph | null>(null);
  const [fixing, setFixing] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const g = saved?.datasetId === props.graph.datasetId ? saved : props.graph;
  const previousDatasetId = useRef(props.graph.datasetId);
  useEffect(() => { setSaved(null); }, [props.graph]);
  useEffect(() => {
    if (previousDatasetId.current === props.graph.datasetId) return;
    previousDatasetId.current = props.graph.datasetId;
    setFixing(false);
  }, [props.graph.datasetId]);
  // ⭑ **⟨증보 2026-09-13 · 승인 intent 2026-09-12 운영자 지정⟩ 읽기 전용 구역이면 끈다.**
  // 서버 `canEdit` 은 아직 `업로드·편집` 스위치만 본다(`routes/lineage.py`) — 관리자가 남의
  // 연구실 계보를 열면 참으로 내려온다. 그 화면의 `계보 수정 · 추가`·`계보 채우기` 는 서버가
  // 403·404 로 거절하는 길이라(`test_operator_designation.py` ㈒) **그리지 않는다**.
  // ⚠ 훅은 **조건 없이** 부른다 — `&&` 뒤에 두면 렌더마다 호출 수가 갈린다.
  const readOnlyScope = useReadOnlyScope();
  const canEdit = g.canEdit && !readOnlyScope;
  const openToken = props.openToken ?? 0;
  useEffect(() => {
    // 최초 렌더(0)로는 열지 않는다 — 편집 화면이 눌렀을 때만 오른다.
    if (openToken > 0 && canEdit) setFixing(true);
  }, [openToken, canEdit]);
  // 기준 = 사람이 고른 Lv(props.selfLv). 안 왔을 때만 그래프 파생값으로 물러난다.
  // ⭑ ⟨WU-C9⟩ 물러나는 값도 **같은 표시 규칙**을 지난다 — 노드에 사람 값이 실려 있으면
  //    그것이 기준이다(서버 400 이 보는 값과 같은 축).
  const selfLv =
    props.selfLv ?? displayLevel(g.nodes.find((n) => n.kind === '이 데이터'));
  // 출처는 **한 번만 만든다** — 매 렌더마다 새 객체를 넘기면 모달의 후보 조회가 끝없이 돈다.
  const candidateSource = useMemo(
    () => props.candidateSource ?? apiLineageSource(),
    [props.candidateSource],
  );
  const editSource = useMemo(
    () => props.editSource ?? apiLineageEditSource(),
    [props.editSource],
  );
  const fixEntry = canEdit ? (
    <button
      type="button"
      className="btn btn-secondary btn-sm"
      data-testid="lin-edit"
      onClick={() => setFixing(true)}
    >
      계보 수정 · 추가
    </button>
  ) : null;

  // 관계가 없고 기록 없음 표시가 있을 때만 빈 상태다. 관계가 붙어 있으면 그래프를 그린다 (§8)
  //
  // **원천 관계는 여기서 세지 않는다** (`BF-9`). 「기록 없음」은 **가공 전 데이터를 모른다**는
  // 뜻이고(`DataModel §4.2` · 빈 상태 문구 축자 「업로드할 때 가공 전 데이터를 찾지 못해」),
  // 연구실 밖 출처 표기는 그 물음에 답하지 않는다. 서버가 원천 관계를 싣기 시작해도
  // 이 판정이 뒤집히지 않아야 **edge 유무와 무관하게 같은 그림**이 나온다 (완료 정의 ⑵).
  const empty = g.edges.every((e) => e.parentDatasetId === null) && g.unknownParents;

  const confirmed = g.lineageConfirmedAt;
  const modified = props.lastModifiedAt ?? null;
  const stale = confirmed !== null && modified !== null && modified > confirmed;

  const cols: LineageNode[][] = [[], [], [], []];
  for (const n of g.nodes) cols[columnOf(n, g)]!.push(n);

  const rails: LineageEdge[][] = [[], [], []];
  for (const e of g.edges) if (e.method) rails[railOf(e, g)]!.push(e);

  // **빈 칸은 세우지 않는다.** 종류가 없는 칸이 폭(`lineageGraph.css`)과 화살표를 그대로 들고 있어
  // 루트 왼쪽·잎 오른쪽에 갈 곳 없는 화살표가 남았다 (버그 3·5·7).
  // §8 이 정한 것은 축의 **순서**지 「빈 칸도 자리를 지킨다」가 아니다 — 걸러도 칸 번호는 오름차순이다.
  const shown = cols.map((nodes, col) => ({ nodes, col })).filter((c) => c.nodes.length > 0);

  const byId = new Map(g.nodes.filter((n) => n.datasetId).map((n) => [n.datasetId!, n]));
  const srcNodes = g.nodes.filter((n) => n.kind === '원천');
  const parentEdges = g.edges.filter(
    (e) => e.childDatasetId === g.datasetId && e.parentDatasetId !== null,
  );
  const childEdges = g.edges.filter((e) => e.parentDatasetId === g.datasetId);
  const selfNode = g.nodes.find((n) => n.kind === '이 데이터');

  return (
    <section className="dsec lin-sec" id="sec-lineage" data-testid="lineage-section">
      {/* ⭑ **⟨WU-B10 · PRD-31 ⑴⟩ 진입점은 구역 **헤더**에 선다** — 빈 상태든 그래프든 같은
          자리다. 권한이 없으면 **DOM 에 없다**(비활성이 아니다 · P-12 관례). */}
      <div className="dsec-h" data-testid="lin-sec-head">
        <h2>계보 · 족보</h2>
        <span className="hint">{empty ? HINT_EMPTY : HINT}</span>
        {fixEntry}
      </div>

      {/* 확정을 지우지 않는다. 확정일과 수정일을 나란히 놓고 판단은 사람에게 남긴다 (§2·§3.2) */}
      {stale ? (
        <div className="lin-stale" data-testid="lin-stale">
          <span className="chip chip--warning">이후 수정됨</span>
          <span className="d">
            확정 {day(confirmed!)} · 수정 {day(modified!)}
          </span>
        </div>
      ) : null}

      {empty ? (
        <div className="lin-empty" data-testid="lin-empty">
          <span className="chip chip--warning">기록 없음</span>
          <div className="t">아직 채워지지 않은 계보예요</div>
          <div className="d">
            업로드할 때 가공 전 데이터를 찾지 못해 <b>모름</b>으로 남겨 뒀어요.
          </div>
          {/* ⭑ **⟨R-C · WU-C8 · R-B §5-43 판정⟩ 빈 상태 3문면은 **권한과 무관**하다.**
              종전에는 이 셋째 문장이 `canEdit` 안에 있어, 고칠 권한이 없는 계정은 2문면만
              보고 「내가 뭔가 안 한 탓」으로 읽었다. 문장은 **사실 설명**이고 사실은 권한에
              따라 달라지지 않는다(PRD-31 ⑵ 「빈 상태 3문면」).
              ⛔ **가려지는 것은 행동뿐이다** — `계보 채우기` 버튼은 그대로 `canEdit` 안에
                 남고, 권한이 없으면 DOM 에 없다(P-12 관례 · 비활성이 아니다). */}
          {canEdit ? (
            <button
              type="button"
              className="btn btn-strong btn-sm"
              data-testid="lin-fill"
              onClick={() => setFixing(true)}
            >
              계보 채우기
            </button>
          ) : null}
          <p className="muted">원자료(Lv0)라 부모가 없다면 그대로 두어도 괜찮아요.</p>
        </div>
      ) : (
        <>
          {/* 기록 없음 표시가 남아 있으면 경고 칩 (§5) */}
          {g.unknownParents ? (
            <span className="chip chip--warning" data-testid="lin-unknown-chip">
              기록 없음
            </span>
          ) : null}

          {/* 커지면 가로로 흐른다. 접거나 요약하는 컨트롤을 두지 않는다 (§8) */}
          <div className="lin-graph" data-testid="lin-graph" data-overflow="가로 스크롤">
            <div className="lin-axis">
              {shown.map(({ nodes, col }, k) => {
                // 화살표는 **선 칸과 선 칸 사이**에만 있다. 건너뛴 칸의 라벨은 잃지 않는다 —
                // 사이에 접힌 레일의 가공 방식을 그 한 칸에 모아 싣는다.
                const next = shown[k + 1];
                const ways = next ? rails.slice(col, next.col).flat() : [];
                return (
                  <div key={`c${col}`} className="lin-colwrap">
                    <div className="lin-col" data-testid="lin-col" data-col={col}>
                      {nodes.map((n, j) => (
                        <GraphNode key={n.datasetId ?? `${n.kind}-${j}`} node={n} />
                      ))}
                      {/* 활용 배지는 **노드가 아니다** — 프로젝트 개수만 알리고 활용 섹션으로 보낸다 */}
                      {col === 2 && g.projectUseCount > 0 ? (
                        <a className="lin-use" href="#sec-usage" data-testid="lin-usebadge">
                          활용 프로젝트 {g.projectUseCount}건 ›
                        </a>
                      ) : null}
                    </div>
                    {next ? (
                      <div className="lin-rail" data-rail={col}>
                        {ways.map((e, m) => (
                          <span
                            key={`${e.parentDatasetId ?? '원천'}>${e.childDatasetId}#${m}`}
                            className="lin-way"
                            data-testid="lin-method"
                            data-origin={e.origin}
                            /* 상자 폭을 넘으면 …로 접힌다(`lineageGraph.css`). **전문은
                               여기 남는다** — 접혔다고 값이 사라지면 안 된다 (검수 #22) */
                            title={e.method ?? undefined}
                          >
                            {e.origin === 'ai' ? `✦ ${e.method}` : e.method}
                          </span>
                        ))}
                        {/* 원천 관계는 `method` 가 null 이라 라벨을 만들지 않는다 — 라벨 없는
                            화살표로 남기지, 빈 칸을 만들지 않는다 (버그 7).
                            ⭑ `BF-9` 로 서버(`routes/lineage.py`)가 **원천 → 루트 관계를 싣는다.**
                            그전에는 대응 edge 자체가 없었고, 화면은 그때도 같은 그림을 냈다 —
                            둘 다 시험이 잠근다(`test/lineage-graph.test.tsx`). */}
                        <span className="lin-arw" aria-hidden="true">
                          →
                        </span>
                      </div>
                    ) : null}
                  </div>
                );
              })}
            </div>
          </div>

          {/* 계보 상세 행 — 그래프를 안 봐도 같은 목적지로 갈 수 있다 (§8) */}
          <div className="lin-strip" data-testid="lin-rows">
            {srcNodes.length > 0 ? (
              <div className="lrow" data-testid="lrow" data-stage="원천">
                <span className="stg">원천</span>
                <div>
                  <div className="ln-name plain">{srcNodes.map((n) => n.name).join(' · ')}</div>
                  <div className="ln-sub">연구실 밖 출처 표기라 열어 볼 상세 화면이 없어요</div>
                </div>
                <span />
              </div>
            ) : null}

            {parentEdges.map((e, i) => (
              <DetailRow
                key={`p${e.parentDatasetId}#${i}`}
                edge={e}
                node={byId.get(e.parentDatasetId!)}
                derived={false}
                datasetId={g.datasetId}
                editSource={canEdit ? editSource : undefined}
                onSaved={next => { setSaved(next); setNotice('계보를 수정했어요.'); }}
              />
            ))}

            {selfNode ? (
              <div className="lrow is-self" data-testid="lrow" data-stage="이 데이터">
                <span className="stg">이 데이터</span>
                <div>
                  <div className="ln-name">{selfNode.name}</div>
                </div>
                {displayLevel(selfNode) === null ? (
                  <span />
                ) : (
                  <span className={`lvl lvl-${displayLevel(selfNode)}`}>
                    Lv{displayLevel(selfNode)}
                  </span>
                )}
              </div>
            ) : null}

            {childEdges.map((e, i) => (
              <DetailRow
                key={`c${e.childDatasetId}#${i}`}
                edge={e}
                node={byId.get(e.childDatasetId)}
                derived
              />
            ))}
          </div>

        </>
      )}

      {/* ⭑ **⟨WU-B10⟩ 모달은 자기 닫기 함수 한 곳으로 닫힌다**(A9R) — Esc·배경·×·취소·저장. */}
      {fixing ? (
        <LineageFixModal
          datasetId={g.datasetId}
          selfLv={selfLv}
          candidateSource={candidateSource}
          editSource={editSource}
          onSaved={(next) => {
            setSaved(next);
            setNotice(PRE_LINEAGE_ADDED);
          }}
          requestClose={() => setFixing(false)}
        />
      ) : null}

      {notice ? (
        <Toast
          message={notice}
          testId="lin-fix-toast"
          onDismiss={() => setNotice(null)}
        />
      ) : null}
    </section>
  );
}
