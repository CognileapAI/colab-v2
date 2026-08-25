// S-05 데이터셋 상세 — **상단(헤더 + 기본 정보)만.**
// 계보 그래프·미리보기·활용 프로젝트 섹션은 WU-P2·P3·P5 가 이어서 채운다 (`sessions/P1.md §1`).
// 한 페이지 스크롤이고 탭으로 콘텐츠를 숨기지 않는다 (`Policy_데이터셋_상세 §1.3-1`).
import { useMemo, useState } from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';
import { BasicInfoGrid } from '../components/detail/BasicInfoGrid';
import { DetailHeader } from '../components/detail/DetailHeader';
import { LockedNotice } from '../components/detail/LockedNotice';
import { defaultDetailSource } from '../components/detail/detailSource';
import { useDatasetDetail } from '../components/detail/useDatasetDetail';
import type { DetailSource } from '../components/detail/types';
import { GridAttachEntry } from '../components/upload/GridAttachEntry';
import type { UploadSources } from '../components/upload/types';
import { LockedContent } from '../permission/LockedContent';
import '../components/detail/detail.css';

/** 되돌아가기 기본값. 들어온 곳이 프로젝트면 그 프로젝트 이름을 부른다 (`§8` · WU-P5 가 실어 준다). */
const DEFAULT_BACK = { label: '데이터셋 목록', to: '/datasets' };

type BackState = { backLabel?: string; backTo?: string } | null;

export function DatasetDetailPage(
  props: { source?: DetailSource; uploadSources?: UploadSources } = {},
) {
  const { datasetId = '' } = useParams();
  const state = useLocation().state as BackState;
  // 실서버가 아직 501 을 내면 픽스처로 그린다 — 서버가 붙는 순간 자동으로 갈아탄다
  const source = useMemo(() => props.source ?? defaultDetailSource(), [props.source]);
  // 격자를 반영한 뒤 **서버에게 다시 묻는다** — 화면이 값을 손으로 고치지 않는다.
  const [reloadToken, setReloadToken] = useState(0);
  const detail = useDatasetDetail(source, datasetId, reloadToken);

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
          header={<DetailHeader detail={detail.detail} />}
          request={<LockedNotice />}
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
        </LockedContent>
      ) : null}
    </div>
  );
}
