// WU-A8 · PRD-24 (미결-9 ⓑ 확정) — 상세 구역 메뉴. `position: sticky` 로 화면 위에 남고
// 스크롤 위치에 따라 현재 구역을 활성 표시한다.
// ⛔ **탭·패널 전환이 아니다.** 이 메뉴가 하는 일은 앵커 이동과 「지금 어디」 표시뿐이고,
//    누른다고 다른 구역이 숨겨지지 않는다 — 정본 `Policy_데이터셋_상세 §1.3-1`
//    「한 페이지 스크롤 · 탭으로 콘텐츠를 숨기지 않는다」를 그대로 둔다(개정 없음).
import { useEffect, useState } from 'react';

/** 구역 차례는 판단 순서 그대로다 (`Policy_데이터셋_상세 §4`). 앵커는 이미 있던 id 를 쓴다. */
export const DETAIL_SECTIONS = [
  { id: 'sec-lineage', label: '계보' },
  { id: 'sec-preview', label: '미리보기' },
  { id: 'sec-usage', label: '활용/접근' },
] as const;

export function SectionMenu() {
  const [active, setActive] = useState<string>(DETAIL_SECTIONS[0].id as string);

  useEffect(() => {
    // ⑴ 관측기가 있으면 그것으로 — 화면에 가장 크게 걸친 구역이 현재 구역이다.
    if (typeof IntersectionObserver !== 'undefined') {
      const seen = new Map<string, number>();
      const observer = new IntersectionObserver(
        (entries) => {
          for (const e of entries) {
            const id = (e.target as HTMLElement).id;
            seen.set(id, e.isIntersecting ? e.intersectionRatio || 1 : 0);
          }
          let best: string | null = null;
          let bestRatio = 0;
          for (const s of DETAIL_SECTIONS) {
            const r = seen.get(s.id) ?? 0;
            if (r > bestRatio) {
              best = s.id;
              bestRatio = r;
            }
          }
          if (best) setActive(best);
        },
        { rootMargin: '-72px 0px -55% 0px', threshold: [0, 0.25, 0.5, 0.75, 1] },
      );
      // **구역은 늦게 올 수 있다** — 계보는 제 op 로 따로 읽고, 다 읽은 뒤에야 자리를 세운다.
      // 처음 한 번만 훑고 말면 늦게 온 구역이 영영 감시 밖에 남는다.
      const watched = new Set<HTMLElement>();
      const attach = () => {
        for (const s of DETAIL_SECTIONS) {
          const el = document.getElementById(s.id);
          if (el && !watched.has(el)) {
            watched.add(el);
            observer.observe(el);
          }
        }
      };
      attach();
      const mutations = new MutationObserver(attach);
      mutations.observe(document.body, { childList: true, subtree: true });
      return () => {
        mutations.disconnect();
        observer.disconnect();
      };
    }

    // ⑵ 없으면 스크롤 위치로 — 머리(72px) 를 지난 구역 중 마지막 것이 현재 구역이다.
    const onScroll = () => {
      let current: string = DETAIL_SECTIONS[0].id;
      for (const s of DETAIL_SECTIONS) {
        const el = document.getElementById(s.id);
        if (el && el.getBoundingClientRect().top <= 72) current = s.id;
      }
      setActive(current);
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <nav className="dsec-menu" data-testid="detail-section-menu" aria-label="구역">
      <ul className="dsec-menu-l">
        {DETAIL_SECTIONS.map((s) => (
          <li key={s.id}>
            <a
              className={s.id === active ? 'dsec-menu-i is-active' : 'dsec-menu-i'}
              href={`#${s.id}`}
              data-testid={`secmenu-${s.id}`}
              data-active={s.id === active ? 'true' : 'false'}
              aria-current={s.id === active ? 'true' : undefined}
              onClick={() => setActive(s.id)}
            >
              {s.label}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  );
}
