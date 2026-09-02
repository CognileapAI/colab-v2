// S-01 연구실 (대시보드) — **내 홈이 아니라 연구실 대시보드다** (`Policy_홈_대시보드 §1.1`).
// 그래서 상단 내비의 주 탭 이름도 `홈` 이 아니라 `연구실` 이다.
//
// 검색 히어로가 화면 맨 위를 차지한다. 다른 요소가 그 위에 오지 않는다 (§8) —
// 검색의 유일한 입구이기 때문이다 (`Policy_데이터_찾기 §1.3-2`).
//
// 그 아래는 **두 구획**이다 (§1.3-1) — 왼쪽 `우리 연구실`(연구실이 어떤 상태인가) ·
// 오른쪽 `내 일`(내가 뭘 해야 하는가). 구획 라벨은 카드가 아니라 **층을 나누는 표식**이라
// 배경·보더를 두지 않는다 (§4 용어 · §8). 최근 활동은 주 내용이 연구실 전체 활동이라 왼쪽이다.
import { useMemo, useState } from 'react';
import { SearchHero } from '../components/search/SearchHero';
import { DataMapCard } from '../components/dashboard/DataMapCard';
import { EmptyLabOnboarding } from '../components/dashboard/EmptyLabOnboarding';
import { LabInfoModal } from '../components/dashboard/LabInfoModal';
import { RecentActivity } from '../components/dashboard/RecentActivity';
import { SummaryTiles } from '../components/dashboard/SummaryTiles';
import { TodoInbox } from '../components/dashboard/TodoInbox';
import { apiDashboardSource } from '../components/dashboard/dashboardSource';
import { useDashboard } from '../components/dashboard/useDashboard';
import type { DashboardSource } from '../components/dashboard/types';
import { useAccount } from '../permission/session';
import { PermissionGate } from '../permission/PermissionGate';
import { UnfinishedUploads } from '../components/upload/UnfinishedUploads';
import { apiUploadSource } from '../components/upload/uploadSource';

/** 소스는 한 번만 만든다 — 렌더마다 새로 만들면 카드의 effect 가 매번 다시 돈다. */
const uploadSource = apiUploadSource();
import '../components/search/search.css';
import '../components/dashboard/dashboard.css';

export function LabPage(props: { source?: DashboardSource } = {}) {
  const source = useMemo(() => props.source ?? apiDashboardSource(), [props.source]);
  const state = useDashboard(source);
  const account = useAccount();
  const [labInfoOpen, setLabInfoOpen] = useState(false);

  // **데이터 1건이면 채워진 홈이다** (§7 전이표). 지표를 못 읽는 동안에는 빈 홈으로
  // 단정하지 않는다 — 적재 중을 0건으로 그리면 첫날이 아닌 사람에게 첫날 화면이 뜬다.
  const empty = state.summary.kind === '있음' && state.summary.value.datasetCount === 0;

  return (
    <div data-screen="S-01" data-fills-in="WU-P7">
      <SearchHero />

      {/* ⚠ **올리다 만 업로드는 할 일 함이 아니다.** 아래 두 구획 중 `내 일` 은 정본이 그룹 셋으로
          열거한 P7 의 자리이고, 이 절은 그 **위의 별도 절**이다 — 침범하지 않는다.
          이 배치는 **정본 개정 판정 대기**다(`PLAN-SoT §9 〈281〉` · `S3.md §3`). */}
      <PermissionGate requires="업로드·편집">
        <UnfinishedUploads upload={uploadSource} />
      </PermissionGate>

      <div className="dash-columns">
        <div className="dash-col" data-section="우리 연구실">
          {/* §8 — 라벨 자체가 연구실 정보를 여는 입구를 겸한다. 제목처럼 보이되
              눌린다는 것만 오른쪽 화살표로 알린다. **읽기는 전 구성원**이다 (§6). */}
          <button
            type="button"
            className="dash-section-label dash-section-label--opens"
            onClick={() => setLabInfoOpen(true)}
          >
            우리 연구실 <span aria-hidden="true">›</span>
          </button>

          {empty ? <EmptyLabOnboarding /> : null}
          <DataMapCard slot={state.dataMap} />
          <SummaryTiles slot={state.summary} />
          <RecentActivity slot={state.activities} myAccountId={account?.accountId ?? null} />
        </div>

        <div className="dash-col" data-section="내 일">
          {/* 오른쪽 라벨은 **누르는 자리가 아니다** (§1.3-1 · §6 요구사항). */}
          <p className="dash-section-label">내 일</p>
          <TodoInbox state={state} source={source} />
        </div>
      </div>

      {labInfoOpen ? (
        <LabInfoModal source={source} onClose={() => setLabInfoOpen(false)} />
      ) : null}
    </div>
  );
}
