// S-05 데이터셋 상세 — 상단(헤더 + 기본 정보) + **계보 · 족보** + **미리보기**(WU-P3).
// 활용 프로젝트 섹션은 WU-P5 가 이어서 채운다 (`sessions/P1.md §1`).
// 한 페이지 스크롤이고 탭으로 콘텐츠를 숨기지 않는다 (`Policy_데이터셋_상세 §1.3-1`).
import { useEffect, useMemo, useState } from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';
import { DatasetPreviewSection } from '../components/datasetpreview/DatasetPreviewSection';
import type { DatasetPreviewSource } from '../components/datasetpreview/types';
import { apiApprovalSource } from '../components/approval/approvalSource';
import type { ApprovalSource } from '../components/approval/types';
import { BasicInfoGrid } from '../components/detail/BasicInfoGrid';
import { DetailHeader } from '../components/detail/DetailHeader';
import { FileList, describeFileError } from '../components/detail/FileList';
import { LockedNotice } from '../components/detail/LockedNotice';
import { defaultDetailSource } from '../components/detail/detailSource';
import { useStartDownload } from '../components/detail/download';
import { apiFileSource } from '../components/detail/fileSource';
import { useDatasetDetail } from '../components/detail/useDatasetDetail';
import type { DetailSource, FileSource } from '../components/detail/types';
import { LineageSection } from '../components/lineage/LineageSection';
import { defaultLineageSource } from '../components/lineage/graphSource';
import { useDatasetLineage } from '../components/lineage/useDatasetLineage';
import type { LineageGraphSource } from '../components/lineage/graphTypes';
import { GridAttachEntry } from '../components/upload/GridAttachEntry';
import type { UploadSources } from '../components/upload/types';
import { LockedContent } from '../permission/LockedContent';
import { ActionGate } from '../permission/PermissionGate';
import { recordVisit } from '../components/dashboard/visits';
import '../components/detail/detail.css';

/** 되돌아가기 기본값. 들어온 곳이 프로젝트면 그 프로젝트 이름을 부른다 (`§8` · WU-P5 가 실어 준다). */
const DEFAULT_BACK = { label: '데이터셋 목록', to: '/datasets' };

type BackState = { backLabel?: string; backTo?: string } | null;

export function DatasetDetailPage(
  props: {
    source?: DetailSource;
    lineageSource?: LineageGraphSource;
    previewSource?: DatasetPreviewSource;
    uploadSources?: UploadSources;
    /** 파일 목록·트리·다운로드 (`〈278〉`-(다)). 시험이 대역을 꽂는 자리다. */
    fileSource?: FileSource;
    /** 승인 처리 네 동작 (WU-P6). 시험이 대역을 꽂는 자리다. */
    approvalSource?: ApprovalSource;
  } = {},
) {
  const { datasetId = '' } = useParams();
  const state = useLocation().state as BackState;
  // 실서버가 아직 501 을 내면 픽스처로 그린다 — 서버가 붙는 순간 자동으로 갈아탄다
  const source = useMemo(() => props.source ?? defaultDetailSource(), [props.source]);
  // 파일 관리는 **픽스처 폴백이 없다** — 쓰기 경로다 (`fileSource.ts` 머리말)
  const fileSource = useMemo(() => props.fileSource ?? apiFileSource(), [props.fileSource]);
  const download = useStartDownload();
  const [downloadError, setDownloadError] = useState<string | null>(null);
  // 격자를 반영하거나 파일이 바뀐 뒤 **서버에게 다시 묻는다** — 화면이 값을 손으로 고치지 않는다.
  const [reloadToken, setReloadToken] = useState(0);
  const detail = useDatasetDetail(source, datasetId, reloadToken);
  // 승인·요청이 끝나면 **서버에게 다시 묻는다** — 화면이 `verified`·`accessRequestPending` 을
  // 손으로 뒤집으면 서버가 거절해도 참으로 보인다 (격자 반영과 같은 규칙).
  const approvalSource = useMemo(
    () => props.approvalSource ?? apiApprovalSource(),
    [props.approvalSource],
  );
  // 계보는 **다른 op** 이라 다른 출처로 읽는다 — 상세가 501 이어도 계보가 살아 있을 수 있고 그 반대도 된다
  const lineageSource = useMemo(
    () => props.lineageSource ?? defaultLineageSource(),
    [props.lineageSource],
  );
  const lineage = useDatasetLineage(lineageSource, datasetId, reloadToken);

  // 「내가 열어 본 것」 — **브라우저에만 적는다** (`Policy_홈_대시보드 §10` · WU-P7).
  // 서버로 보내는 경로가 여기 없는 것이 그 조항의 실물이다. 홈의 최근 활동이 이 값을 읽는다.
  useEffect(() => {
    if (detail.status === 'ready') {
      recordVisit({ kind: '데이터셋', id: datasetId, name: detail.detail.name });
    }
  }, [detail, datasetId]);

  const back = {
    label: state?.backLabel ?? DEFAULT_BACK.label,
    to: state?.backTo ?? DEFAULT_BACK.to,
  };

  function downloadAll() {
    setDownloadError(null);
    fileSource
      .downloadTicket(datasetId)
      .then(download)
      .catch((e: unknown) => setDownloadError(describeFileError(e)));
  }

  return (
    <div className="detail-page" data-screen="S-05">
      {/* 되돌아가기는 헤더 **밖 제 줄**에 하나만 둔다 — 경로(브레드크럼)가 아니고,
          같은 목록의 다른 데이터셋으로 바로 옮기는 길도 두지 않는다 (`§8` · §12 v2.2) */}
      <div className="backrow" data-testid="backrow">
        <Link className="backlink" to={back.to}>
          <span className="bl-a">←</span>
          <span className="bl-n">{back.label}</span>
        </Link>
      </div>

      {detail.status === 'loading' ? <div data-testid="detail-loading" aria-busy="true" /> : null}

      {/* 묘비는 상세 화면이 없다 (`§7`). 문구는 `§9` 그대로다 */}
      {detail.status === 'gone' ? (
        <div className="gone" data-testid="detail-gone">
          <p>이 데이터는 지워졌어요. 계보 기록은 관련 데이터의 상세에서 볼 수 있어요.</p>
          <Link to="/datasets">데이터셋 목록</Link>
        </div>
      ) : null}

      {detail.status === 'ready' ? (
        <LockedContent
          bodyAccessible={detail.detail.bodyAccessible}
          header={
            <DetailHeader
              detail={detail.detail}
              approvalSource={approvalSource}
              onChanged={() => setReloadToken((n) => n + 1)}
            />
          }
          request={
            <LockedNotice
              detail={detail.detail}
              approvalSource={approvalSource}
              onRequested={() => setReloadToken((n) => n + 1)}
            />
          }
        >
          {/* 잠기면 `basicInfo` 가 null 이라 기본 정보가 통째로 사라진다 —
              카탈로그 행이 `조각 N` 을 계속 띄우는 것과 달라 보이는 것은 의도다
              (`§7` · `PLAN-SoT §9-㊼-④`) */}
          {detail.detail.basicInfo ? (
            <>
              <BasicInfoGrid
                basicInfo={detail.detail.basicInfo}
                fileName={detail.detail.fileName}
              />
              <div className="dt-gridact" data-testid="detail-grid-actions">
                {/* 묶음 다운로드 — 조각 묶음이면 묶어서 한 번에 (`§2·§8`). 링크가 아니라 **티켓**이다
                    (`〈278〉-(다)` — `<a href>` 에는 Bearer 가 실리지 않는다). 판정은 서버의 `canDownload` (P-7) */}
                <ActionGate allowed={detail.detail.actions.canDownload}>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    data-testid="dt-download"
                    onClick={downloadAll}
                  >
                    다운로드{/* [정본 무근거 · 〈278〉] — 카탈로그 빠른 작업의 같은 낱말 */}
                  </button>
                </ActionGate>
                {/* **진입점 하나.** 격자 0건은 정상 상태이고(`P2.md §2-21`), 나중에 붙이는 길이
                    없으면 그 데이터는 지도 위에 영영 못 선다 (`〈58〉-②`·`〈75〉`).
                    이미 격자가 있으면 남은 축이 없을 수 있으나, **그 판정은 서버가 한다** —
                    화면이 조건을 임의로 정하지 않는다 (`P-7`). 서버는 409 로 답하고
                    모달이 그 문장을 그대로 보여 준다. */}
                <GridAttachEntry
                  datasetId={datasetId}
                  datasetName={detail.detail.name}
                  onAttached={() => setReloadToken((n) => n + 1)}
                  sources={props.uploadSources}
                />
              </div>
              {downloadError ? (
                <p className="dt-files-error" role="alert" data-testid="dt-download-error">
                  {downloadError}
                </p>
              ) : null}
              {/* 파일 목록은 사람이 눌렀을 때 연다 (`§5`). 추가·교체·삭제 뒤에는 상세를 다시 읽어
                  `파일` 칸의 조각 수·합계가 서버 값으로 돌아온다 */}
              <FileList
                datasetId={datasetId}
                source={fileSource}
                actions={detail.detail.actions}
                onChanged={() => setReloadToken((n) => n + 1)}
              />
            </>
          ) : null}
          {/* 계보 · 족보 (`§8` — 항상 표시). **못 읽은 것을 빈 계보로 그리지 않는다** —
              읽지 못하면 구역 자체를 세우지 않는다. */}
          {lineage.status === 'ready' ? (
            <LineageSection
              graph={lineage.graph}
              lastModifiedAt={detail.detail.lastModifiedAt}
            />
          ) : null}
          {/* 미리보기 — **한 페이지 스크롤 안의 한 구역**이다 (`§1.3-1` 탭으로 숨기지 않는다).
              **보기는 전원**이라 권한 관문을 두지 않는다 (`§1.3-5`·`§6` 「전 구성원 — 시각화 보기」).
              잠긴 데이터는 위 `LockedContent` 가 이미 본문째 막는다. */}
          <DatasetPreviewSection datasetId={datasetId} source={props.previewSource} />
        </LockedContent>
      ) : null}
    </div>
  );
}
