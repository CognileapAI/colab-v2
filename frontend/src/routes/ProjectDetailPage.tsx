// S-02b 프로젝트 상세 — 개요(설명·기간) · 연결 주소 · 소속 데이터셋을 **순서대로** 보여준다.
//
// **연결 주소를 설명·기간과 같은 묶음에 두지 않는 것**이 이 화면의 중심 결정이다 (§0·§1.2) —
// 그것이 데이터에서 성과까지 계보를 잇는 값이라서다. 없으면 계보가 논문 앞에서 끊긴다.
import { useMemo } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ProjectDatasetTable } from '../components/project/ProjectDatasetTable';
import { projectPeriod } from '../components/project/format';
import { defaultProjectSource } from '../components/project/projectSource';
import { useProject } from '../components/project/useProjects';
import type { ProjectSource } from '../components/project/types';
import '../components/project/project.css';

export function ProjectDetailPage(props: { source?: ProjectSource } = {}) {
  const { projectId = '' } = useParams();
  const navigate = useNavigate();
  const source = useMemo(() => props.source ?? defaultProjectSource(), [props.source]);
  const state = useProject(source, projectId);

  return (
    <div className="project-detail" data-screen="S-02b">
      {/* 돌아가기는 제목 **위** 한 줄이고 이것 하나뿐이다. 경로(브레드크럼)도, 다른
          프로젝트로 옮겨 가는 형제 전환도 두지 않는다 — 옆으로 옮기는 일은 목록이 맡는다
          (§8 · v2.0 이력) */}
      <div className="backrow" data-testid="project-backrow">
        <Link className="backlink" to="/projects">
          <span className="bl-a">←</span>
          <span className="bl-n">프로젝트 목록</span>
        </Link>
      </div>

      {state.status === 'loading' ? <div data-testid="project-loading" aria-busy="true" /> : null}

      {state.status === 'gone' ? (
        <div className="gone" data-testid="project-gone">
          <p>이 프로젝트를 찾을 수 없어요.</p>
          <Link to="/projects">프로젝트 목록</Link>
        </div>
      ) : null}

      {state.status === 'ready' ? (
        <Ready detail={state.detail} onOpenDataset={(id) => navigate(`/datasets/${id}`)} />
      ) : null}
    </div>
  );
}

function Ready(props: {
  detail: import('../components/project/types').ProjectDetail;
  onOpenDataset(datasetId: string): void;
}) {
  const { detail } = props;
  const canManage = detail.canManage;
  return (
    <>
      <header className="pd-head">
        <h1>{detail.name}</h1>
        <div className="pd-m">
          <span className="chip">{detail.type}</span>
          {detail.status === '닫힘' ? <span className="chip chip--closed">닫힘</span> : null}
          <span className="pd-sub">데이터셋 {detail.datasets.length}개</span>
        </div>
        {/* 닫힌 뒤에도 활용 기록이 보인다 — 남은 데이터셋 수를 다시 알린다 (§8) */}
        {detail.status === '닫힘' ? (
          <p className="pd-closedbar">
            소속 데이터셋 {detail.datasets.length}개는 카탈로그에 그대로 있어요.
          </p>
        ) : null}
      </header>

      <section className="card" data-testid="project-overview">
        <div className="pd-sect">
          <h2>개요</h2>
          {/* 수정·닫기·삭제는 `프로젝트 생성` 이 켜진 사람만 (§6). 꺼졌으면 DOM 에서
              사라진다 — 비활성 버튼·경고 토스트로 남기지 않는다 (P-12).
              실물 op(`updateProject`·`setProjectStatus`·`deleteProject`)은 아직 501 이다. */}
          {canManage ? (
            <span className="quiet" data-slot="edit" data-fills-in="updateProject">
              정보 수정
            </span>
          ) : null}
        </div>
        <p className={detail.description ? 'pd-desc' : 'pd-desc is-empty'}>
          {detail.description ??
            '아직 설명이 없어요 — 무엇을 하는 과제·논문인지 몇 줄만 적어 두세요.'}
        </p>
        <dl className="pd-grid">
          <dt>유형</dt>
          <dd>{detail.type}</dd>
          <dt>기간</dt>
          <dd>{projectPeriod(detail.period) || '—'}</dd>
          <dt>데이터셋</dt>
          <dd>{detail.datasets.length}개</dd>
        </dl>
      </section>

      {/* 설명·기간과 **다른 카드·다른 묶음**으로 세우고 `계보` 표시를 붙인다 (§8) */}
      <section className="card pd-link" data-testid="project-link-card">
        <div className="pd-sect">
          <h2>연결 주소</h2>
          <span className="chip chip--lineage">계보</span>
        </div>
        {detail.link ? (
          // 받아 적은 값을 **그대로** 링크로 보여준다. 형식·생존 여부를 확인하지 않는다 (§1.3-3)
          <a
            data-testid="project-link-url"
            className="pd-linkurl"
            href={detail.link}
            rel="noreferrer"
          >
            {detail.link}
          </a>
        ) : (
          <p className="pd-linkempty">아직 적지 않았어요.</p>
        )}
      </section>

      <section className="card">
        <div className="pd-sect">
          <h2>소속 데이터셋</h2>
          {/* 삭제는 **데이터셋 0건일 때만** 열린다 — 업로드 중 빠른 생성으로 잘못 만든
              프로젝트를 지우기 위한 예외다. 한 건이라도 붙으면 사라진다 (§1.3-6 · §8) */}
          {canManage && detail.datasets.length === 0 ? (
            <span className="quiet" data-slot="delete" data-fills-in="deleteProject">
              삭제
            </span>
          ) : null}
          {canManage && detail.status === '진행 중' ? (
            <span className="quiet" data-slot="close" data-fills-in="setProjectStatus">
              프로젝트 닫기
            </span>
          ) : null}
          {canManage && detail.status === '닫힘' ? (
            <span className="quiet" data-slot="reopen" data-fills-in="setProjectStatus">
              다시 열기
            </span>
          ) : null}
        </div>
        <ProjectDatasetTable
          rows={detail.datasets}
          canManage={canManage}
          onOpen={props.onOpenDataset}
        />
      </section>
    </>
  );
}
