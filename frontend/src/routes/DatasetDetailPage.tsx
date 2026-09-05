// S-05 데이터셋 상세 — 상단(헤더 + 기본 정보) + **계보 · 족보** + **미리보기** + **활용 · 가져가기**.
// 섹션 차례는 판단 순서 그대로다 — 기본 정보 → 계보 → 미리보기 → 활용 (`Policy_데이터셋_상세 §4`).
// ⭑ 활용 섹션(`#sec-usage`)·다운로드·파일 목록은 **레인 Q-D** 가 채웠다 (`PLAN-SoT §9 〈299〉`).
//   종전 주석 「활용 프로젝트 섹션은 WU-P5 가 이어서 채운다」는 그 자리가 비어 있던 동안의 기재다.
// 한 페이지 스크롤이고 탭으로 콘텐츠를 숨기지 않는다 (`Policy_데이터셋_상세 §1.3-1`).
import { useEffect, useMemo, useState } from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';
import { DatasetPreviewSection } from '../components/datasetpreview/DatasetPreviewSection';
import type { DatasetPreviewSource } from '../components/datasetpreview/types';
import { apiApprovalSource } from '../components/approval/approvalSource';
import type { ApprovalSource } from '../components/approval/types';
import { LoadFailure } from '../components/common/LoadFailure';
import { BasicInfoGrid } from '../components/detail/BasicInfoGrid';
import { DetailHeader } from '../components/detail/DetailHeader';
import { FileList, describeFileError } from '../components/detail/FileList';
import { LockedNotice } from '../components/detail/LockedNotice';
import { UsageSection } from '../components/detail/UsageSection';
import { defaultFilesSource } from '../components/detail/filesSource';
import type { FilesSource } from '../components/detail/filesSource';
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
    /** 파일(조각) 목록 — `보기` 를 눌렀을 때만 부른다. 시험이 대역을 꽂는 자리다. */
    filesSource?: FilesSource | undefined;

    /** 파일 목록·트리·다운로드 (`〈339〉`-(다)). 시험이 대역을 꽂는 자리다. */
    fileSource?: FileSource;
    /** 승인 처리 네 동작 (WU-P6). 시험이 대역을 꽂는 자리다. */
    approvalSource?: ApprovalSource;
  } = {},
) {
  const { datasetId = '' } = useParams();
  const state = useLocation().state as BackState;
  // 서버가 유일한 출처다 — 못 읽으면 못 읽었다고 말한다 (`detailSource.ts` 2026-09-03 개정)
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
  // 계보는 **다른 op** 이라 다른 출처로 읽는다 — 상세가 죽어도 계보가 살아 있을 수 있고 그 반대도 된다
  const lineageSource = useMemo(
    () => props.lineageSource ?? defaultLineageSource(),
    [props.lineageSource],
  );
  const lineage = useDatasetLineage(lineageSource, datasetId, reloadToken);
  const filesSource = useMemo(
    () => props.filesSource ?? defaultFilesSource(),
    [props.filesSource],
  );

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

      {/* ⛔ **404 를 묘비로 번역하지 않는다.** 서버는 **남의 연구실 묘비 · 남의 연구실 생존 ·
          존재한 적 없는 id 셋을 같은 404 로** 낸다 — 구분해 주면 그 자체가 존재의 누설이기
          때문이다 (`routes/catalog.py` `dataset_detail` 축자 · P-9·P-10). 화면은 그 셋을 가를 수
          없으므로 `Policy_데이터셋_상세 §9` 의 묘비 문구를 여기 쓰면 **있지도 않았던 데이터를
          있었다고 말하게 된다.** 그래서 `Policy_공통_기반 §2.4` 「없는 주소」의 중립 한 줄을
          쓴다 — `NotFoundPage` 와 같은 문구다 (QA 검수 #6 · `PLAN-SoT §9 〈299〉`).
          ⭑ **⟨개정 2026-09-03 · 17차 해제 · Ted 판정 ②⟩ 접힘에서 한 칸이 빠졌다** — 내 연구실
          묘비는 아래 `tombstone` 자리로 간다. **여기 문구는 그대로다.** */}
      {detail.status === 'gone' ? (
        <div className="gone" data-testid="detail-gone">
          <p>이 주소에는 화면이 없어요.</p>
          <Link to="/datasets">데이터셋 목록</Link>
        </div>
      ) : null}

      {/* ⭑ **⟨신설 2026-09-03 · 17차 해제 · Ted 판정 ②⟩ 묘비 — 계약 410 에서만 선다.**
          내 연구실에서 지워진 데이터라 「지워졌다」가 새로 알리는 사실이 없다(그 행은 지워지기
          전에 이미 내 목록에 있었다). 문구는 `Policy_데이터셋_상세 §9` 「지워진 데이터의 주소로
          직접 들어옴」 행 **축자**이고, 복구 방법 열이 적은 「목록으로 보낸다」를 링크로 낸다.
          ⚠ **위 중립 문구와 겹치지 않는다** — 한 응답은 한 자리만 세운다. */}
      {detail.status === 'tombstone' ? (
        <div className="gone" data-testid="detail-tombstone">
          <p>이 데이터는 지워졌어요. 계보 기록은 관련 데이터의 상세에서 볼 수 있어요.</p>
          <Link to="/datasets">데이터셋 목록</Link>
        </div>
      ) : null}

      {/* **못 읽은 것을 「없는 주소」로도 「묘비」로도 말하지 않는다** — 위 두 자리는 각각
          404·410 만의 것이다. 서버가 500 이거나 닿지 않았을 때 그 문구를 쓰면 있는 데이터를
          없다고 말한다. 종전에는 이 자리가 픽스처였고, 픽스처가 모르는 id 는 오히려 묘비로
          그려졌다 (`CODE-REVIEW-20260903` 9). */}
      {detail.status === 'error' ? (
        <LoadFailure
          message="데이터셋을 불러오지 못했어요. 잠시 뒤 다시 시도해 주세요."
          onRetry={() => setReloadToken((n) => n + 1)}
          testId="detail-error"
        />
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
                datasetId={datasetId}
                filesSource={filesSource}
              />
              <div className="dt-gridact" data-testid="detail-grid-actions">
                {/* 묶음 다운로드 — 조각 묶음이면 묶어서 한 번에 (`§2·§8`). 링크가 아니라 **티켓**이다
                    (`〈339〉-(다)` — `<a href>` 에는 Bearer 가 실리지 않는다). 판정은 서버의 `canDownload` (P-7) */}
                <ActionGate allowed={detail.detail.actions.canDownload}>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    data-testid="dt-download"
                    onClick={downloadAll}
                  >
                    다운로드{/* [정본 무근거 · 〈339〉] — 카탈로그 빠른 작업의 같은 낱말 */}
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
          {/* 계보 · 족보 (`§8` — 항상 표시). **못 읽은 것을 빈 계보로도, 남의 계보로도
              그리지 않는다** — 그림을 세우는 대신 못 읽었다는 사실과 다시 불러오기를 둔다
              (종전에는 픽스처 계보가 이 자리를 채웠다 · `CODE-REVIEW-20260903` 9). */}
          {lineage.status === 'ready' ? (
            <LineageSection
              graph={lineage.graph}
              lastModifiedAt={detail.detail.lastModifiedAt}
            />
          ) : null}
          {lineage.status === 'unavailable' ? (
            <LoadFailure
              message="계보를 불러오지 못했어요. 잠시 뒤 다시 시도해 주세요."
              onRetry={() => setReloadToken((n) => n + 1)}
              testId="lineage-error"
            />
          ) : null}
          {/* 미리보기 — **한 페이지 스크롤 안의 한 구역**이다 (`§1.3-1` 탭으로 숨기지 않는다).
              **보기는 전원**이라 권한 관문을 두지 않는다 (`§1.3-5`·`§6` 「전 구성원 — 시각화 보기」).
              잠긴 데이터는 위 `LockedContent` 가 이미 본문째 막는다. */}
          <DatasetPreviewSection
            datasetId={datasetId}
            source={props.previewSource}
            datasetName={detail.detail.name}
            fileName={detail.detail.fileName}
            gridResolution={detail.detail.basicInfo?.grid}
          />
          {/* 활용 · 가져가기 — 판단 순서의 마지막 칸(`§4`)이고 계보 배지 `#sec-usage` 의 목적지다.
              잠기면 `LockedContent` 가 여기까지 오지 않는다 — 접근 요청 자리는 `LockedNotice`
              한 곳뿐이다 (`§3.3`·`§7`). */}
          <UsageSection detail={detail.detail} />
        </LockedContent>
      ) : null}
    </div>
  );
}
