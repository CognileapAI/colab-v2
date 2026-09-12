// 하나의 셸 · GNB (전원 공통, 항상 노출)
// 정본: Policy_공통_기반 v1.4 §1 · IA_사이트맵 §3 · mockups/제품_260817.html (.gnb)
// 목업을 임의로 변형하지 않는다 — 요소·순서·클래스 이름을 목업에서 그대로 가져왔다.
import type { ReactNode } from 'react';
import { NavLink, useLocation, Link } from 'react-router-dom';
import { MAIN_NAV, LAB_SETTINGS_PATH, ownerTabOf } from './nav';
import { useAccount } from '../permission/session';
import { PermissionGate } from '../permission/PermissionGate';
import { UploadEntry } from '../components/upload/UploadEntry';
import { useLogout } from '../auth/AuthGate';
import { ThemeSwitcher } from './ThemeSwitcher';

// 좁은 화면에서는 라벨을 감추고 이 아이콘만 남긴다 (shell.css `@media (max-width: 640px)`).
// 인라인 SVG 만 쓴다 — 아이콘 라이브러리를 들이지 않는다. 모양은 카탈로그 표의 인라인 SVG 와 같은 결이다.
function Icon(props: { children: ReactNode }) {
  return (
    <svg
      className="ico"
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {props.children}
    </svg>
  );
}

/** 주 내비 3탭 아이콘 — 순서·의미는 `nav.ts` 의 탭 id 에 맞춘다. */
const NAV_ICON: Record<string, ReactNode> = {
  lab: <path d="M9 3v6l-5 8a2 2 0 0 0 1.7 3h12.6a2 2 0 0 0 1.7-3l-5-8V3M8 3h8" />,
  projects: <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7Z" />,
  datasets: (
    <>
      <ellipse cx="12" cy="6" rx="8" ry="3" />
      <path d="M4 6v12c0 1.7 3.6 3 8 3s8-1.3 8-3V6M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3" />
    </>
  ),
};

export function Gnb(props: { openRequest?: { seq: number; resumeUploadId?: string } | undefined } = {}) {
  const account = useAccount();
  // 관리자는 전 연구실을 읽는다 — 표기가 그 사실을 따라간다(승인 intent 2026-09-12).
  const operator = account?.canManageServiceAccounts === true;
  const logout = useLogout();
  const activeTab = ownerTabOf(useLocation().pathname);

  return (
    <header className="gnb">
      {/* 브랜드 마크 — 누르면 연구실 화면으로 */}
      <Link className="brand" to="/lab" aria-label="Co-Lab">
        <span className="logo" aria-hidden="true" />
        <span className="bn">Co-Lab</span>
      </Link>

      {/* 연구실 전환기 — "어느 연구실로 보는 중". 이름의 정본은 서버가 내려주는 labName 이다.
          전환 목록·동작은 P0 범위 밖이라 자리만 둔다. */}
      {/* ⛔ **`▾` 를 달지 않는다.** 펼침 화살표는 「누르면 목록이 열린다」를 표기로 약속하는 것이고,
          전환 목록·동작이 P0 범위 밖인 지금 그 약속은 지켜지지 않는다. 계정 1 · 연구실 1 인 현재는
          전환이라는 동작 자체가 없다 — 전환기가 돌아오는 회차에 `▾` 도 같이 돌아온다(백로그).
          ⚠ 정본 `Policy_공통_기반 §1` 의 GNB 도식은 `[연구실 전환기 ▾]` 로 적혀 있다.
             **그 도식은 고치지 않았다** — 델타는 `notes/SPEC-DELTA-PENDING.md` 에 등재돼 있다. */}
      {/* ⭑ 관리자는 **모든 연구실을 읽기 전용으로** 본다(승인 intent 2026-09-12 운영자 지정).
          그래서 이 자리가 「어느 연구실로 보는 중」에 답할 때 소속 이름 하나를 쓰면 거짓말이 된다 —
          목록·상세가 이미 전 연구실을 담고 있기 때문이다. 표기를 실제 범위에 맞춘다.
          ⚠ **특정 연구실 하나로 좁히는 동작은 아직 없다.** 좁히려면 읽기 op 들이 연구실 인자를
             받아야 하고, 그것은 「경계는 요청에서 오지 않는다」(CLAUDE.md §3-5)를 건드리는
             계약 판정이다 — 그래서 여기서 `▾` 를 달지 않는다. 달면 없는 동작을 약속하게 된다. */}
      <button type="button" className="labswitch" data-testid="lab-switcher"
              aria-label={operator
                ? '연구실 전환 · 전체 연구실 (읽기 전용)'
                : `연구실 전환 · ${account?.labName ?? ''}`}>
        <Icon><path d="M3 21V9l6-4 6 4v12M9 21v-5h3v5M15 12h6v9h-6" /></Icon>
        <span className="ln">{operator ? '전체 연구실' : (account?.labName ?? '')}</span>
      </button>

      {/* 주 내비 3개 — 전원 공통. 남는 가로 여백은 여기서 먹는다 (Policy §1) */}
      <nav className="mainnav" aria-label="주 내비">
        {MAIN_NAV.map((tab) => (
          <NavLink
            key={tab.id}
            to={tab.path}
            className={tab.id === activeTab ? 'is-active' : ''}
            {...(tab.id === activeTab ? { 'aria-current': 'page' as const } : {})}
            aria-label={tab.label}
          >
            <Icon>{NAV_ICON[tab.id]}</Icon>
            <span className="lbl">{tab.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* 검색은 GNB 에 없다 — 진입은 `연구실` 화면 히어로 한 곳뿐 (Policy §1) */}

      {/* ⬆️ 업로드 — 1급 버튼. `업로드·편집`이 켜진 사람에게만 **보인다**(P-12).
          화면으로 넘어가지 않고 전체 화면 모달을 연다 (Policy §2.3).
          모달 본체는 E-04 → WU-P2 가 만든다. 여기서는 버튼 자리만 둔다. */}
      <PermissionGate requires="업로드·편집">
        <UploadEntry openRequest={props.openRequest} />
      </PermissionGate>
      {account?.canManageServiceAccounts ? (
        <Link className="gnb-settings" to="/account-admin" data-testid="gnb-account-admin" aria-label="계정 관리"><Icon><circle cx="12" cy="8" r="3" /><path d="M5 21v-3a7 7 0 0 1 14 0v3" /></Icon><span className="lbl">계정 관리</span></Link>
      ) : null}

      {/* 연구실 설정 — `연구실 설정` 스위치가 켜진 사람에게만 보인다 (P-12) */}
      <PermissionGate requires="연구실 설정">
        <Link
          className="gnb-settings"
          to={LAB_SETTINGS_PATH}
          data-testid="gnb-lab-settings"
          aria-label="연구실 설정"
        >
          <Icon>
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-2.9 1.2v.2a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-3-1.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0-1.2-2.9h-.2a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.3-3l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 2.9-1.2V2a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 3 1.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0 1.2 2.9h.2a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.6 1Z" />
          </Icon>
          <span className="lbl">연구실 설정</span>
        </Link>
      </PermissionGate>

      <ThemeSwitcher />
      {/* 아바타 — 현재 사용자·역할·계정. 드롭다운 내용은 P0 범위 밖 */}
      <div className="avatar-wrap">
        <button type="button" className="avatar" data-testid="gnb-avatar" aria-label={`내 계정 · ${account?.name ?? ''}`}>
          <Icon>
            <circle cx="12" cy="8" r="3.5" />
            <path d="M4.5 20a7.5 7.5 0 0 1 15 0" />
          </Icon>
          <span className="nm">{account?.name ?? ''}</span>
          <span className="cv" aria-hidden="true">▾</span>
        </button>
        {/* 로그아웃 — 아바타 드롭다운이 서기 전까지 자리를 여기 둔다 (`PLAN-SoT §9 〈90〉-㉳`).
            들어온 길이 있으면 나가는 길도 있어야 한다. */}
        <button type="button" className="gnb-logout" onClick={logout} data-testid="gnb-logout">
          로그아웃
        </button>
      </div>
    </header>
  );
}
