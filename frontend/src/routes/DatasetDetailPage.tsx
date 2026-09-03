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
import { BasicInfoGrid } from '../components/detail/BasicInfoGrid';
import { DetailHeader } from '../components/detail/DetailHeader';
import { LockedNotice } from '../components/detail/LockedNotice';
import { UsageSection } from '../components/detail/UsageSection';
import { defaultFilesSource } from '../components/detail/filesSource';
import type { FilesSource } from '../components/detail/filesSource';
import { defaultDetailSource } from '../components/detail/detailSource';
import { useDatasetDetail } from '../components/detail/useDatasetDetail';
import type { DetailSource } from '../components/detail/types';
import { LineageSection } from '../components/lineage/LineageSection';
import { defaultLineageSource } from '../components/lineage/graphSource';
import { useDatasetLineage } from '../components/lineage/useDatasetLineage';
import type { LineageGraphSource } from '../components/lineage/graphTypes';
import { GridAttachEntry } from '../components/upload/GridAttachEntry';
import type { UploadSources } from '../components/upload/types';
import { LockedContent } from '../permission/LockedContent';
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
    /** 승인 처리 네 동작 (WU-P6). 시험이 대역을 꽂는 자리다. */
    approvalSource?: ApprovalSource;
  } = {},
) {
  const { datasetId = '' } = useParams();
  const state = useLocation().state as BackState;
  // 실서버가 아직 501 을 내면 픽스처로 그린다 — 서버가 붙는 순간 자동으로 갈아탄다
  const source = useMemo(() => props.source ?? defaultDetailSource(), [props.source]);
  // 격자를 반영한 뒤 **서버에게 다시 묻는다** — 화면이 값을 손으로 고치지 않는다.
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

      {/* ⛔ **404 를 묘비로 번역하지 않는다.** 서버는 묘비·연구실 경계 밖·존재한 적 없는 id
          **셋을 같은 404 로** 낸다 — 구분해 주면 그 자체가 존재의 누설이기 때문이다
          (`routes/catalog.py` `dataset_detail` 축자 · P-9·P-10). 화면은 그 셋을 가를 수 없으므로
          `Policy_데이터셋_상세 §9` 의 묘비 문구(「이 데이터는 지워졌어요」)를 쓰면 **있지도 않았던
          데이터를 있었다고 말하게 된다.** 그래서 `Policy_공통_기반 §2.4` 「없는 주소」의 중립 한 줄을
          쓴다 — `NotFoundPage` 와 같은 문구다 (QA 검수 #6 · `PLAN-SoT §9 〈299〉`). */}
      {detail.status === 'gone' ? (
        <div className="gone" data-testid="detail-gone">
          <p>이 주소에는 화면이 없어요.</p>
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
                datasetId={datasetId}
                filesSource={filesSource}
              />
              {/* **진입점 하나.** 격자 0건은 정상 상태이고(`P2.md §2-21`), 나중에 붙이는 길이
                  없으면 그 데이터는 지도 위에 영영 못 선다 (`〈58〉-②`·`〈75〉`).
                  이미 격자가 있으면 남은 축이 없을 수 있으나, **그 판정은 서버가 한다** —
                  화면이 조건을 임의로 정하지 않는다 (`P-7`). 서버는 409 로 답하고
                  모달이 그 문장을 그대로 보여 준다. */}
              <div className="dt-gridact" data-testid="detail-grid-actions">
                <GridAttachEntry
                  datasetId={datasetId}
                  datasetName={detail.detail.name}
                  onAttached={() => setReloadToken((n) => n + 1)}
                  sources={props.uploadSources}
                />
              </div>
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
          {/* 활용 · 가져가기 — 판단 순서의 마지막 칸(`§4`)이고 계보 배지 `#sec-usage` 의 목적지다.
              잠기면 `LockedContent` 가 여기까지 오지 않는다 — 접근 요청 자리는 `LockedNotice`
              한 곳뿐이다 (`§3.3`·`§7`). */}
          <UsageSection detail={detail.detail} />
        </LockedContent>
      ) : null}
    </div>
  );
}
