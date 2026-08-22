// 셸 = GNB + 화면 한 자리. 역할별로 화면을 쪼개지 않는다 (Policy_공통_기반 §1).
import { Outlet } from 'react-router-dom';
import { Gnb } from './Gnb';

export function AppLayout() {
  return (
    <>
      <Gnb />
      <main className="appmain">
        <Outlet />
      </main>
    </>
  );
}
