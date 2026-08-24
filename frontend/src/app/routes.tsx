// 라우팅 표. 화면 본체는 P1 이후가 채우고, 여기는 자리와 주인 탭만 정한다.
// 업로드(S-04)는 **라우트가 아니다** — 전체 화면 모달이다 (Policy_공통_기반 v1.4 §2.3).
import { Navigate, Route, Routes } from 'react-router-dom';
import { AppLayout } from '../shell/AppLayout';
import { LabPage } from '../routes/LabPage';
import { ProjectsPage } from '../routes/ProjectsPage';
import { DatasetsPage } from '../routes/DatasetsPage';
import { DatasetDetailPage } from '../routes/DatasetDetailPage';
import { LabSettingsPage } from '../routes/LabSettingsPage';
import { NotFoundPage } from '../routes/NotFoundPage';
// S-08(미등록 미리보기 화면)은 stage2 대기 — 라우트만 뺀다. 파일은 유지한다
// (`dev-package/sessions/S1-PLAN.md` §5.2, `PLAN-SoT.md §9 〈74〉〈75〉〈79〉`).

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        {/* 로그인 후 시작점은 `연구실` 화면이다 (IA_사이트맵 §4 — 세 여정의 시작점) */}
        <Route path="/" element={<Navigate to="/lab" replace />} />
        <Route path="/lab" element={<LabPage />} />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/datasets" element={<DatasetsPage />} />
        <Route path="/datasets/:datasetId" element={<DatasetDetailPage />} />
        <Route path="/lab-settings" element={<LabSettingsPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
