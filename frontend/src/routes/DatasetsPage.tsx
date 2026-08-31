// S-03 카탈로그 — 뭐가 있는지 훑는 길. **AI 를 쓰지 않는다** (`Policy_데이터_찾기 §1.2`).
// 조건과 정렬은 전부 표 헤더에 있다. 자연어 입력칸도 조건 툴바도 여기 없다.
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppliedConditions } from '../components/catalog/AppliedConditions';
import { CatalogTable } from '../components/catalog/CatalogTable';
import { defaultCatalogSource } from '../components/catalog/catalogSource';
import { useCatalog } from '../components/catalog/useCatalog';
import type { CatalogSource } from '../components/catalog/types';
import { VerifiedBadgeSlot } from '../placeholders/VerifiedBadgeSlot';
import { LockIndicatorSlot } from '../placeholders/LockIndicatorSlot';
import '../components/catalog/catalog.css';

export function DatasetsPage(props: { source?: CatalogSource } = {}) {
  const navigate = useNavigate();
  // 실서버가 아직 501 을 내면 픽스처로 그린다 — 서버가 붙는 순간 자동으로 갈아탄다
  const source = useMemo(() => props.source ?? defaultCatalogSource(), [props.source]);
  const state = useCatalog(source);

  // 업로더 조건은 계정 ID 로 걸지만 사람에게는 이름을 보인다 (계약 `FilterUploader`)
  const uploaderNames = useMemo(
    () => new Map((state.list?.items ?? []).map((r) => [r.uploader.accountId, r.uploader.name])),
    [state.list],
  );

  const shown = state.list?.totalCount ?? 0;
  const base = state.baseTotal;

  return (
    <div className="catalog-page" data-screen="S-03">
      <div className="page-head">
        <h1>데이터셋</h1>
        <span className="hcnt">
          {shown}건{base !== null && shown < base ? ` / 전체 ${base}건` : ''}
        </span>
        <span className="desc">뭐가 있는지부터 훑을 때의 길이에요.</span>
      </div>

      <div className="card">
        {/* E-06 이 얹힐 자리 — Verified 배지의 모양·조건과 접근 요청은 WU-P6 이 채운다 */}
        <VerifiedBadgeSlot />
        <LockIndicatorSlot />

        <AppliedConditions
          filters={state.query.filters}
          uploaderNames={uploaderNames}
          onToggle={state.toggleValue}
          onClearAll={state.clearAll}
        />
        <CatalogTable
          state={state}
          uploaderNames={uploaderNames}
          onOpen={(datasetId) => navigate(`/datasets/${datasetId}`)}
        />
      </div>

      {/* 상호 안내 — 반대 길(검색 화면 S-01·S-06)이 이번 릴리스에 없다.
          정본 `Policy_데이터_찾기 v1.9 §8` 「상호 안내 — 반대 길이 그 릴리스에 없을 때」:
          점선 박스는 자리와 형태 그대로 두되, 없는 화면으로 가는 링크를 빼고
          이 표 자신의 조건 거는 법을 권한다. 문구는 정본이 고정한 한 줄이다. */}
      <div className="crosslink">
        <span>
          찾을 것이 정해져 있으면 <b>표 헤더의 열 이름</b>을 눌러 조건을 걸어 보세요.
        </span>
      </div>
    </div>
  );
}
