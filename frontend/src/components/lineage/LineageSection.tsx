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
import { Link } from 'react-router-dom';
import type { LineageEdge, LineageGraph, LineageNode } from './graphTypes';
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
  return (
    <>
      <span className="n-head">
        {n.processingLevel === null ? null : (
          <span className={`lvl lvl-${n.processingLevel}`} data-testid="lin-lv">
            Lv{n.processingLevel}
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

function DetailRow(props: { edge: LineageEdge; node: LineageNode | undefined; derived: boolean }) {
  const { edge, node, derived } = props;
  const kind = node?.kind ?? (derived ? '파생' : '가공 전');
  const name = node?.name ?? '—';
  const hist = `· 확인 ${edge.confirmedBy.name} · ${day(edge.confirmedAt)}${
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
        <div className="ln-sub">
          {edge.method ? `가공 방식: ${edge.method} ` : ''}
          <span className="hist">{hist}</span>
        </div>
      </div>
      {node && node.processingLevel !== null ? (
        <span className={`lvl lvl-${node.processingLevel}`}>Lv{node.processingLevel}</span>
      ) : (
        <span />
      )}
    </div>
  );
}

export function LineageSection(props: {
  graph: LineageGraph;
  /** 상세가 이미 읽어 온 값. 계보 응답에는 없다 — 「이후 수정됨」은 이 둘을 나란히 놓는 표시다 (§2). */
  lastModifiedAt?: string | null;
}) {
  const g = props.graph;

  // 관계가 없고 기록 없음 표시가 있을 때만 빈 상태다. 관계가 붙어 있으면 그래프를 그린다 (§8)
  const empty = g.edges.length === 0 && g.unknownParents;

  const confirmed = g.lineageConfirmedAt;
  const modified = props.lastModifiedAt ?? null;
  const stale = confirmed !== null && modified !== null && modified > confirmed;

  const cols: LineageNode[][] = [[], [], [], []];
  for (const n of g.nodes) cols[columnOf(n, g)]!.push(n);

  const rails: LineageEdge[][] = [[], [], []];
  for (const e of g.edges) if (e.method) rails[railOf(e, g)]!.push(e);

  const byId = new Map(g.nodes.filter((n) => n.datasetId).map((n) => [n.datasetId!, n]));
  const srcNodes = g.nodes.filter((n) => n.kind === '원천');
  const parentEdges = g.edges.filter(
    (e) => e.childDatasetId === g.datasetId && e.parentDatasetId !== null,
  );
  const childEdges = g.edges.filter((e) => e.parentDatasetId === g.datasetId);
  const selfNode = g.nodes.find((n) => n.kind === '이 데이터');

  return (
    <section className="dsec lin-sec" id="sec-lineage" data-testid="lineage-section">
      <div className="dsec-h">
        <h2>계보 · 족보</h2>
        <span className="hint">{empty ? HINT_EMPTY : HINT}</span>
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
          {g.canEdit ? (
            <>
              <button type="button" className="btn btn-strong btn-sm" data-testid="lin-fill">
                계보 채우기
              </button>
              <p className="muted">원자료(Lv0)라 부모가 없다면 그대로 두어도 괜찮아요.</p>
            </>
          ) : null}
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
              {cols.map((nodes, i) => (
                <div key={`c${i}`} className="lin-colwrap">
                  <div className="lin-col" data-testid="lin-col" data-col={i}>
                    {nodes.map((n, j) => (
                      <GraphNode key={n.datasetId ?? `${n.kind}-${j}`} node={n} />
                    ))}
                    {/* 활용 배지는 **노드가 아니다** — 프로젝트 개수만 알리고 활용 섹션으로 보낸다 */}
                    {i === 2 && g.projectUseCount > 0 ? (
                      <a className="lin-use" href="#sec-usage" data-testid="lin-usebadge">
                        활용 프로젝트 {g.projectUseCount}건 ›
                      </a>
                    ) : null}
                  </div>
                  {i < 3 ? (
                    <div className="lin-rail" data-rail={i}>
                      {rails[i]!.map((e, k) => (
                        <span
                          key={`${e.parentDatasetId ?? '원천'}>${e.childDatasetId}#${k}`}
                          className="lin-way"
                          data-testid="lin-method"
                          data-origin={e.origin}
                        >
                          {e.origin === 'ai' ? `✦ ${e.method}` : e.method}
                        </span>
                      ))}
                      <span className="lin-arw" aria-hidden="true">
                        →
                      </span>
                    </div>
                  ) : null}
                </div>
              ))}
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
              />
            ))}

            {selfNode ? (
              <div className="lrow is-self" data-testid="lrow" data-stage="이 데이터">
                <span className="stg">이 데이터</span>
                <div>
                  <div className="ln-name">{selfNode.name}</div>
                </div>
                {selfNode.processingLevel === null ? (
                  <span />
                ) : (
                  <span className={`lvl lvl-${selfNode.processingLevel}`}>
                    Lv{selfNode.processingLevel}
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

          {/* 편집 권한자에게만 존재한다. 검색 창(E-04 패턴)은 아직 이 화면에 없다 — 자리만 잡는다 */}
          {g.canEdit ? (
            <div className="lin-act">
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                data-testid="lin-edit"
                data-fills-in="E-04 검색 창 미연결"
              >
                계보 수정 · 추가
              </button>
            </div>
          ) : null}
        </>
      )}
    </section>
  );
}
