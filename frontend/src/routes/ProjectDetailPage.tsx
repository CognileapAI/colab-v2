// S-02b 프로젝트 상세 — 개요(설명·기간) · 연결 주소 · 소속 데이터셋을 **순서대로** 보여준다.
//
// **연결 주소를 설명·기간과 같은 묶음에 두지 않는 것**이 이 화면의 중심 결정이다 (§0·§1.2) —
// 그것이 데이터에서 성과까지 계보를 잇는 값이라서다. 없으면 계보가 논문 앞에서 끊긴다.
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { recordVisit } from '../components/dashboard/visits';
import { ProjectCloseModal } from '../components/project/ProjectCloseModal';
import { ProjectDatasetTable } from '../components/project/ProjectDatasetTable';
import { ProjectFormModal } from '../components/project/ProjectFormModal';
import { projectPeriod } from '../components/project/format';
import { defaultProjectSource } from '../components/project/projectSource';
import { useProject } from '../components/project/useProjects';
import {
  ProjectHasDatasets,
  type ProjectDetail,
  type ProjectSource,
  type ProjectUpdate,
} from '../components/project/types';
import '../components/project/project.css';

export function ProjectDetailPage(props: { source?: ProjectSource } = {}) {
  const { projectId = '' } = useParams();
  const navigate = useNavigate();
  const source = useMemo(() => props.source ?? defaultProjectSource(), [props.source]);
  const state = useProject(source, projectId);

  // 「내가 열어 본 것」 — **브라우저에만 적는다** (`Policy_홈_대시보드 §10` · WU-P7).
  useEffect(() => {
    if (state.status === 'ready') {
      recordVisit({ kind: '프로젝트', id: projectId, name: state.detail.name });
    }
  }, [state, projectId]);

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
        <Ready
          detail={state.detail}
          source={source}
          onOpenDataset={(id) => navigate(`/datasets/${id}`)}
          onDeleted={() => navigate('/projects')}
        />
      ) : null}
    </div>
  );
}

function Ready(props: {
  detail: ProjectDetail;
  source: ProjectSource;
  onOpenDataset(datasetId: string): void;
  onDeleted(): void;
}) {
  const { source } = props;
  // 쓰기 뒤의 상세는 **응답이 들고 온 것**을 쓴다 — 다시 조회하면 두 값이 갈릴 수 있고,
  // `setProjectStatus`·`updateProject` 는 이미 갱신된 상세를 통째로 내린다 (계약).
  const [patched, setPatched] = useState<ProjectDetail | null>(null);
  const detail = patched ?? props.detail;
  const canManage = detail.canManage;

  // 모달 둘 — F-04 정보 수정 · F-05 닫기 확인. **다시 열기·소속 해제는 모달이 없다**:
  // 확인을 받는 것은 잃을까 걱정되는 쪽뿐이고, 정본이 확인 화면을 요구한 것은 닫기다 (§8).
  const [editing, setEditing] = useState(false);
  const [closing, setClosing] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setPatched(await source.get(detail.projectId));
  }, [source, detail.projectId]);

  async function remove() {
    try {
      await source.remove(detail.projectId);
      props.onDeleted();
    } catch (e) {
      // 409 를 조용히 삼키지 않는다 — 화면에서 사라졌어야 할 버튼이 눌린 상황이다.
      setNotice(
        e instanceof ProjectHasDatasets
          ? '소속 데이터셋이 있어 지울 수 없어요. 닫기를 쓰세요.'
          : '프로젝트를 지우지 못했어요.',
      );
    }
  }

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
              사라진다 — 비활성 버튼·경고 토스트로 남기지 않는다 (P-12). */}
          {canManage ? (
            <button type="button" className="quiet" onClick={() => setEditing(true)}>
              정보 수정
            </button>
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
            <button type="button" className="quiet" onClick={() => void remove()}>
              삭제
            </button>
          ) : null}
          {canManage && detail.status === '진행 중' ? (
            <button type="button" className="quiet" onClick={() => setClosing(true)}>
              프로젝트 닫기
            </button>
          ) : null}
          {canManage && detail.status === '닫힘' ? (
            // 되돌리는 쪽에는 확인을 두지 않는다 — 잃는 것이 없다 (§7 두 번째 전이).
            <button
              type="button"
              className="quiet"
              onClick={() => void source.setStatus(detail.projectId, '진행 중').then(setPatched)}
            >
              다시 열기
            </button>
          ) : null}
        </div>
        <ProjectDatasetTable
          rows={detail.datasets}
          canManage={canManage}
          onOpen={props.onOpenDataset}
          onUnlink={async (datasetId) => {
            await source.unlink(detail.projectId, datasetId);
            await reload();
          }}
        />
      </section>

      {notice ? (
        <p className="pd-notice" role="alert" data-testid="project-notice">
          {notice}
        </p>
      ) : null}

      {editing ? (
        <ProjectFormModal
          mode={{ kind: '정보 수정', detail }}
          onClose={() => setEditing(false)}
          onSubmit={async (input) => {
            setPatched(await source.update(detail.projectId, input as ProjectUpdate));
          }}
        />
      ) : null}

      {closing ? (
        <ProjectCloseModal
          detail={detail}
          onClose={() => setClosing(false)}
          onConfirm={async () => {
            setPatched(await source.setStatus(detail.projectId, '닫힘'));
          }}
        />
      ) : null}
    </>
  );
}
