// S-03 카탈로그 — 뭐가 있는지 훑는 길. **AI 를 쓰지 않는다** (`Policy_데이터_찾기 §1.2`).
// 조건과 정렬은 전부 표 헤더에 있다. 자연어 입력칸도 조건 툴바도 여기 없다.
import { useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { AppliedConditions } from '../components/catalog/AppliedConditions';
import { CatalogTable } from '../components/catalog/CatalogTable';
import { defaultCatalogSource } from '../components/catalog/catalogSource';
import { useCatalog } from '../components/catalog/useCatalog';
import { LoadFailure } from '../components/common/LoadFailure';
import type { CatalogFilters, CatalogSource } from '../components/catalog/types';
import { describeFileError } from '../components/detail/FileList';
import { useStartDownload } from '../components/detail/download';
import { apiFileSource } from '../components/detail/fileSource';
import type { FileSource } from '../components/detail/types';
import { VerifiedBadgeSlot } from '../placeholders/VerifiedBadgeSlot';
import { LockIndicatorSlot } from '../placeholders/LockIndicatorSlot';
import '../components/catalog/catalog.css';

export function DatasetsPage(props: { source?: CatalogSource; fileSource?: FileSource } = {}) {
  const navigate = useNavigate();
  // 서버가 유일한 출처다 — 못 읽으면 못 읽었다고 말한다 (`catalogSource.ts` 2026-09-03 개정)
  const source = useMemo(() => props.source ?? defaultCatalogSource(), [props.source]);
  // 홈의 데이터 맵이 「그 조건이 걸린 카탈로그」로 보낸다 (`Policy_홈_대시보드 §8` · WU-P7).
  // **여기서 새 조건을 발명하지 않는다** — 주소가 나르는 것은 카탈로그가 이미 거는
  // 두 열(`계보`·`주제`)뿐이고, 그래서 맵의 묶음과 표의 조건이 같은 값이 된다.
  const [params] = useSearchParams();
  const initialFilters = useMemo<CatalogFilters>(() => {
    const filters: CatalogFilters = {};
    const lineageState = params.get('lineageState');
    const topic = params.get('topic');
    if (lineageState) filters['계보'] = [lineageState];
    if (topic) filters['주제'] = [topic];
    return filters;
  }, [params]);
  const state = useCatalog(source, initialFilters);
  // 빠른 작업의 다운로드는 **티켓**이다 (`〈339〉-(다)`). 읽기 폴백을 두는 표와 달리 여기는 폴백이 없다
  const fileSource = useMemo(() => props.fileSource ?? apiFileSource(), [props.fileSource]);
  const download = useStartDownload();
  const [downloadError, setDownloadError] = useState<string | null>(null);

  // 업로더 조건은 계정 ID 로 걸지만 사람에게는 이름을 보인다 (계약 `FilterUploader`)
  const uploaderNames = useMemo(
    () => new Map((state.list?.items ?? []).map((r) => [r.uploader.accountId, r.uploader.name])),
    [state.list],
  );

  // **못 읽었으면 건수가 없다.** `?? 0` 은 실패 자리에 「0건」을 세우고, `baseTotal` 은
  // 앞선 성공이 남긴 수라 「0건 / 전체 N건」까지 만든다 — 둘 다 못 읽은 것을 없는 것으로
  // 바꿔 말한다 (`CODE-REVIEW-20260903-E` 수용 검토 · 정직한 빈 상태).
  // 조회 중(`list === null` · `error === null`)에도 아직 모르는 수를 지어내지 않는다.
  const shown = state.list?.totalCount ?? null;
  const base = state.baseTotal;

  function onDownload(datasetId: string) {
    setDownloadError(null);
    // **어느 행이 실패했는지 말한다.** 표에는 행이 여럿이라 서버 문장만 내리면 사람이
    // 어느 데이터셋 이야기인지 모른다(`main` 줄기 `ST-1`/`CT-1` 의 문안 규약 · 시험이 잠근다).
    // 서버가 제 문장을 준 경우 그것도 버리지 않는다 — 이름 뒤에 붙인다(PR #1 줄기의 태도).
    const name = (state.list?.items ?? []).find((r) => r.datasetId === datasetId)?.name ?? null;
    fileSource
      .downloadTicket(datasetId)
      .then(download)
      .catch((e: unknown) => {
        const said = describeFileError(e);
        setDownloadError(
          name ? `${name} 을(를) 내려받지 못했어요. ${said}` : `내려받지 못했어요. ${said}`,
        );
      });
  }

  return (
    <div className="catalog-page" data-screen="S-03">
      <div className="page-head">
        <h1>데이터셋</h1>
        {shown !== null ? (
          <span className="hcnt">
            {shown}건{base !== null && shown < base ? ` / 전체 ${base}건` : ''}
          </span>
        ) : null}
        <span className="desc">뭐가 있는지부터 훑을 때의 길이에요.</span>
      </div>

      <div className="card">
        {/* E-06 이 얹힐 자리 — Verified 배지의 모양·조건과 접근 요청은 WU-P6 이 채운다 */}
        <VerifiedBadgeSlot />
        <LockIndicatorSlot />

        {/* 못 불러왔으면 **표를 세우지 않는다** — 빈 표의 「조건에 맞는 데이터가 없어요」가
            읽지 못한 것을 없는 것으로 바꿔 말하기 때문이다. 종전에는 이 자리에서 픽스처
            여섯 행을 실데이터처럼 그렸다 (`CODE-REVIEW-20260903` 9). */}
        {state.error ? (
          <LoadFailure message={state.error} onRetry={state.reload} testId="catalog-error" />
        ) : (
          <>
            <AppliedConditions
              filters={state.query.filters}
              uploaderNames={uploaderNames}
              onToggle={state.toggleValue}
              onClearAll={state.clearAll}
            />
            {downloadError ? (
              <p className="dl-error" role="alert" data-testid="dl-error">
                {downloadError}
              </p>
            ) : null}
            <CatalogTable
              state={state}
              uploaderNames={uploaderNames}
              onOpen={(datasetId) => navigate(`/datasets/${datasetId}`)}
              onDownload={onDownload}
            />
          </>
        )}
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
