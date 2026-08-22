// GNB 주 내비 — **정본이 값을 준 것만** 담는다.
//
// 탭 구성·순서·라벨의 정본:
//   Policy_공통_기반 v1.4 §1 「상단 내비게이션」
//     `[연구실 전환기 ▾]  연구실 · 프로젝트 · 데이터셋  ←여백→ [⬆️ 업로드] [연구실 설정] [아바타 ▾]`
//     "**첫 탭 이름은 `연구실`이다**" (v1.4, 2026-08-17 개정 — `홈` 아님)
//   IA_사이트맵.md §3 — 같은 줄. "주 영역 3개. 전원 공통"
//
// **URL 경로는 정본에 없다** — 이 레포의 결정이다 (P0-frontend.md 참고).
// 라벨은 정본 문자열 그대로이며 번역·축약하지 않는다.

export type NavTabId = 'lab' | 'projects' | 'datasets';

export interface NavTab {
  readonly id: NavTabId;
  readonly label: string;
  readonly path: string;
}

/** 순서가 곧 화면 순서다. 셋뿐이고 넷째를 만들지 않는다. */
export const MAIN_NAV: readonly NavTab[] = [
  { id: 'lab', label: '연구실', path: '/lab' },
  { id: 'projects', label: '프로젝트', path: '/projects' },
  { id: 'datasets', label: '데이터셋', path: '/datasets' },
] as const;

/** 연구실 설정은 주 내비가 아니라 우측 버튼이다 (권한에 따라 숨는다). */
export const LAB_SETTINGS_PATH = '/lab-settings';

/**
 * GNB 하이라이트는 **화면 주인 탭에 고정**한다 (Policy_공통_기반 §2.3).
 * 들어온 곳에 따라 켜지는 탭이 달라지지 않는다.
 */
export function ownerTabOf(pathname: string): NavTabId | null {
  if (pathname.startsWith('/projects')) return 'projects';
  // 미등록 미리보기(S-08)를 포함해 데이터셋 계열 화면의 주인 탭은 `데이터셋`이다 (§2.4).
  if (pathname.startsWith('/datasets')) return 'datasets';
  if (pathname.startsWith('/lab-settings')) return null; // 설정은 세 탭 어디에도 속하지 않는다
  if (pathname === '/' || pathname.startsWith('/lab')) return 'lab';
  return null;
}
