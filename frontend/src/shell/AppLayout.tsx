// 셸 = GNB + 화면 한 자리. 역할별로 화면을 쪼개지 않는다 (Policy_공통_기반 §1).
//
// 업로드 모달의 주인은 GNB 의 `UploadEntry` 다. 메인 화면의 「올리다 만 것」 카드가 그 모달을
// 열어야 하므로, **여는 함수를 여기서 컨텍스트로 내려보낸다** — 모달을 하나 더 세우지 않는다
// (`components/detail/download.ts` 의 `DownloadContext` 와 같은 모양).
import { useCallback, useMemo, useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Gnb } from './Gnb';
import { OpenUploadContext, type OpenUploadRequest } from '../components/upload/openUpload';

export function AppLayout() {
  const [request, setRequest] = useState<{ seq: number; resumeUploadId?: string }>({ seq: 0 });
  const open = useCallback((req?: OpenUploadRequest) => {
    setRequest((cur) => ({ seq: cur.seq + 1, ...(req?.resumeUploadId ? { resumeUploadId: req.resumeUploadId } : {}) }));
  }, []);
  const value = useMemo(() => open, [open]);

  return (
    <OpenUploadContext.Provider value={value}>
      <Gnb openRequest={request} />
      <main className="appmain">
        <Outlet />
      </main>
    </OpenUploadContext.Provider>
  );
}
