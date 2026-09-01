// 데이터 맵 — 계보 상태별(위) · 주제별 (`Policy_홈_대시보드 §5` · §8).
//
// **막대는 전부 눌린다** (§8 축자) — 그 조건이 걸린 카탈로그로 간다. 조망에서 행동으로
// 이어지는 길이 없으면 맵은 읽고 마는 판이 된다.
//
// **퍼센트를 글자로 적지 않는다** (§5). 비율은 막대의 길이로만 말하고 글자에 남는 것은
// 건수다 — 「59% 채웠다」는 안심만 남기고 「남은 게 몇 건인가」에 답하지 않는다.
import { useNavigate } from 'react-router-dom';
import type { DataMap } from './types';
import type { Slot } from './useDashboard';

/** 원천 줄의 부연 — 계보가 없는 것이 정상이라는 한 줄 (§8). */
const ORIGIN_NOTE = '기록 없음이 정상';

/** `확정 71 + 원천 16 = 지표의 계보 확정 87` (§8 「계산 관계 안내 줄」의 형식). */
export function calcLine(map: DataMap): string {
  const rows = map.byLineageState ?? [];
  const at = (value: string) => rows.find((r) => r.value === value)?.count ?? 0;
  return `확정 ${at('확정')} + 원천 ${at('원천')} = 지표의 계보 확정 ${at('확정') + at('원천')}`;
}

function Bars(props: {
  axis: string;
  rows: { value: string; count: number }[];
  total: number;
  onOpen: (value: string) => void;
}) {
  return (
    <ul className="dash-bars" data-axis={props.axis}>
      {props.rows.map((row) => (
        <li key={row.value}>
          <button type="button" className="dash-bar" onClick={() => props.onOpen(row.value)}>
            <span className="dash-bar-name">{row.value}</span>
            <span className="dash-bar-track" aria-hidden="true">
              <span
                className="dash-bar-fill"
                style={{ width: props.total > 0 ? `${(row.count / props.total) * 100}%` : '0%' }}
              />
            </span>
            <span className="dash-bar-count">{row.count}</span>
          </button>
          {row.value === '원천' ? <span className="dash-note">{ORIGIN_NOTE}</span> : null}
        </li>
      ))}
    </ul>
  );
}

export function DataMapCard(props: { slot: Slot<DataMap> }) {
  const navigate = useNavigate();
  const openCatalog = (params?: Record<string, string>) =>
    navigate(params ? `/datasets?${new URLSearchParams(params).toString()}` : '/datasets');

  return (
    <section className="dash-card" data-card="data-map">
      <div className="dash-card-head">
        <h2>우리 연구실 데이터 맵</h2>
        {/* §8 「전체 목록 보기」 — 조건 없이 카탈로그를 여는 **명시적** 버튼.
            조용한 텍스트 버튼이라 검색 히어로와 무게를 겨루지 않는다. */}
        <button type="button" className="dash-quiet" onClick={() => openCatalog()}>
          전체 목록 보기 →
        </button>
      </div>
      <DataMapBody slot={props.slot} onOpen={openCatalog} />
    </section>
  );
}

function DataMapBody(props: {
  slot: Slot<DataMap>;
  onOpen: (params?: Record<string, string>) => void;
}) {
  if (props.slot.kind === '실패') {
    // §9 문구 그대로. 「카탈로그에서는 볼 수 있어요」가 복구 경로다.
    return (
      <p className="dash-error">
        연구실 데이터 분포를 지금 불러오지 못했어요. 카탈로그에서는 볼 수 있어요.{' '}
        <button type="button" className="dash-quiet" onClick={() => props.onOpen()}>
          데이터셋 카탈로그 열기 →
        </button>
      </p>
    );
  }
  if (props.slot.kind !== '있음') return <p className="dash-loading">불러오는 중이에요.</p>;

  const map = props.slot.value;
  if (map.totalCount === 0) {
    // §8 「카드별 0 상태」 — 지우지 않고 **무엇이 채워질 자리인지** 한 줄로 적는다.
    return (
      <p className="dash-zero">
        아직 그릴 분포가 없어요. 데이터가 올라오면 계보 상태별·주제별로 자동으로 그려져요.
      </p>
    );
  }
  return (
    <>
      <Bars
        axis="계보 상태별"
        rows={map.byLineageState ?? []}
        total={map.totalCount}
        onOpen={(value) => props.onOpen({ lineageState: value })}
      />
      {/* §8 「계산 관계 안내 줄」 — 맵의 확정·원천과 지표의 계보 확정이 어긋난 숫자로
          보이지 않게 하는 **유일한 글자 줄**이다. 유추할 수 없는 것만 남긴다. */}
      <p className="dash-calc">{calcLine(map)}</p>
      <Bars
        axis="주제별"
        rows={map.byTopic ?? []}
        total={map.totalCount}
        onOpen={(value) => props.onOpen({ topic: value })}
      />
      <button type="button" className="dash-open-catalog" onClick={() => props.onOpen()}>
        데이터셋 카탈로그 열기 →
      </button>
    </>
  );
}
