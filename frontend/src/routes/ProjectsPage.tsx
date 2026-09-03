// S-02 프로젝트 목록 — 계보가 「데이터가 어디서 왔는가」라면 이 화면은 「어디로 갔는가」다.
//
// **카드가 기본이다** — 표는 설명을 담지 못해 "이게 내가 찾던 과제인가"에 목록에서 답할 수 없다.
// 표를 없애지 않은 이유는 `기록 없음`·`승인` 을 훑어 견주려면 값이 세로로 정렬돼야 해서다.
// 필터·정렬은 **한 벌**이라 두 보기가 같은 목록을 본다 (`Policy_프로젝트 §5`).
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { LoadFailure } from '../components/common/LoadFailure';
import { ProjectCards } from '../components/project/ProjectCards';
import { ProjectFormModal } from '../components/project/ProjectFormModal';
import { ProjectTable } from '../components/project/ProjectTable';
import { ProjectToolbar } from '../components/project/ProjectToolbar';
import { defaultProjectSource } from '../components/project/projectSource';
import { useProjects } from '../components/project/useProjects';
import type { ProjectCreate, ProjectSource } from '../components/project/types';
import { PermissionGate } from '../permission/PermissionGate';
import '../components/project/project.css';

export function ProjectsPage(props: { source?: ProjectSource } = {}) {
  const navigate = useNavigate();
  const source = useMemo(() => props.source ?? defaultProjectSource(), [props.source]);
  const state = useProjects(source);
  const open = (projectId: string) => navigate(`/projects/${projectId}`);
  // F-03 새 프로젝트 모달. **라우트를 만들지 않는다** — 모달이다 (`Policy_공통_기반 §2.3`).
  const [creating, setCreating] = useState(false);

  return (
    <div className="project-page" data-screen="S-02">
      <div className="page-head">
        <h1>프로젝트</h1>
        {/* **화면 소개**다. 정의문을 여기 두면 탭이 무엇을 보관하는지가 안 읽힌다 (v1.3 이력).
            프로젝트의 정의·공동연구 범위 안내는 **새 프로젝트 모달**의 몫이다 (§8). */}
        <span className="desc">
          우리 연구실의 과제와 논문을 등록해 두고, 각각에 어떤 데이터를 썼는지 모아 보는 곳이에요.
        </span>
        {/* 만들기는 `프로젝트 생성` 이 켜진 사람만 — 꺼졌으면 숨긴다 (§6 · P-12) */}
        <PermissionGate requires="프로젝트 생성">
          <button type="button" className="pj-new" onClick={() => setCreating(true)}>
            + 새 프로젝트
          </button>
        </PermissionGate>
      </div>

      <ProjectToolbar state={state} />

      {/* **못 읽은 것과 없는 것을 가른다** — 실패 자리에서는 목록도 「조건에 맞는 프로젝트가
          없어요」도 세우지 않는다. 종전에는 목록 실패가 픽스처로 덮여 남의 프로젝트가 우리
          목록으로 그려졌다 (`CODE-REVIEW-20260903` 9). */}
      {state.failed ? (
        <LoadFailure
          message="프로젝트 목록을 불러오지 못했어요. 잠시 뒤 다시 시도해 주세요."
          onRetry={state.reload}
          testId="project-list-error"
        />
      ) : (
        <>
          {state.view === '카드' ? (
            <ProjectCards rows={state.rows} onOpen={open} />
          ) : (
            <ProjectTable rows={state.rows} onOpen={open} />
          )}

          {!state.loading && state.rows.length === 0 ? (
            <p className="pj-empty" data-testid="project-empty">
              조건에 맞는 프로젝트가 없어요.
            </p>
          ) : null}
        </>
      )}

      {creating ? (
        <ProjectFormModal
          mode={{ kind: '새 프로젝트' }}
          onClose={() => setCreating(false)}
          onSubmit={async (input) => {
            // 만든 것을 **바로 그 상세로** 데려간다 — 목록으로 돌려보내면 방금 만든 것을
            // 다시 찾아야 한다. 목업의 `createProj()` 도 같은 자리로 간다.
            const made = await source.create(input as ProjectCreate);
            navigate(`/projects/${made.projectId}`);
          }}
        />
      ) : null}
    </div>
  );
}
