// 하나의 셸 · GNB (전원 공통, 항상 노출)
// 정본: Policy_공통_기반 v1.4 §1 · IA_사이트맵 §3 · mockups/제품_260817.html (.gnb)
// 목업을 임의로 변형하지 않는다 — 요소·순서·클래스 이름을 목업에서 그대로 가져왔다.
import { NavLink, useLocation, Link } from 'react-router-dom';
import { MAIN_NAV, LAB_SETTINGS_PATH, ownerTabOf } from './nav';
import { useAccount } from '../permission/session';
import { PermissionGate } from '../permission/PermissionGate';

export function Gnb() {
  const account = useAccount();
  const activeTab = ownerTabOf(useLocation().pathname);

  return (
    <header className="gnb">
      {/* 브랜드 마크 — 누르면 연구실 화면으로 */}
      <Link className="brand" to="/lab">
        <span className="logo" aria-hidden="true" />
        <span className="bn">Co-Lab</span>
      </Link>

      {/* 연구실 전환기 — "어느 연구실로 보는 중". 이름의 정본은 서버가 내려주는 labName 이다.
          전환 목록·동작은 P0 범위 밖이라 자리만 둔다. */}
      <button type="button" className="labswitch" data-testid="lab-switcher">
        <span className="ln">{account?.labName ?? ''}</span>
        <span className="cv" aria-hidden="true">▾</span>
      </button>

      {/* 주 내비 3개 — 전원 공통. 남는 가로 여백은 여기서 먹는다 (Policy §1) */}
      <nav className="mainnav" aria-label="주 내비">
        {MAIN_NAV.map((tab) => (
          <NavLink
            key={tab.id}
            to={tab.path}
            className={tab.id === activeTab ? 'is-active' : ''}
            {...(tab.id === activeTab ? { 'aria-current': 'page' as const } : {})}
          >
            {tab.label}
          </NavLink>
        ))}
      </nav>

      {/* 검색은 GNB 에 없다 — 진입은 `연구실` 화면 히어로 한 곳뿐 (Policy §1) */}

      {/* ⬆️ 업로드 — 1급 버튼. `업로드·편집`이 켜진 사람에게만 **보인다**(P-12).
          화면으로 넘어가지 않고 전체 화면 모달을 연다 (Policy §2.3).
          모달 본체는 E-04 → WU-P2 가 만든다. 여기서는 버튼 자리만 둔다. */}
      <PermissionGate requires="업로드·편집">
        <button type="button" className="gnb-upload" data-testid="gnb-upload" data-fills-in="WU-P2">
          <span className="lbl">업로드</span>
        </button>
      </PermissionGate>

      {/* 연구실 설정 — `연구실 설정` 스위치가 켜진 사람에게만 보인다 (P-12) */}
      <PermissionGate requires="연구실 설정">
        <Link className="gnb-settings" to={LAB_SETTINGS_PATH} data-testid="gnb-lab-settings">
          연구실 설정
        </Link>
      </PermissionGate>

      {/* 아바타 — 현재 사용자·역할·계정. 드롭다운 내용은 P0 범위 밖 */}
      <div className="avatar-wrap">
        <button type="button" className="avatar" data-testid="gnb-avatar">
          <span className="nm">{account?.name ?? ''}</span>
          <span className="cv" aria-hidden="true">▾</span>
        </button>
      </div>
    </header>
  );
}
