// S-01 연구실 (대시보드) — 검색 히어로가 이 화면의 머리다.
// 검색 진입점은 여기 한 곳뿐이다 (`Policy_데이터_찾기 §1.3-2` · `DatasetsPage` 의 상호 링크).
// 데이터 맵·최근 활동은 아직 만들지 않는다 (E-07 → **WU-P7**).
import { SearchHero } from '../components/search/SearchHero';
import { TodoInboxSlot } from '../placeholders/TodoInboxSlot';
import '../components/search/search.css';

export function LabPage() {
  return (
    <div data-screen="S-01" data-fills-in="WU-P7">
      <SearchHero />
      {/* 비워 둘 자리 ③ — 할 일 함. 홈 상단 (Policy_공통_기반 v1.4 §3) */}
      <TodoInboxSlot />
    </div>
  );
}
