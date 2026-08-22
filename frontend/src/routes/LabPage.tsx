// S-01 연구실 (대시보드) — 화면 본체는 E-07 → **WU-P7**.
// 여기는 자리표시자다. 검색 히어로·데이터 맵·최근 활동은 만들지 않는다 (P0 §2 「건드리지 않는 것」).
import { TodoInboxSlot } from '../placeholders/TodoInboxSlot';

export function LabPage() {
  return (
    <div data-screen="S-01" data-fills-in="WU-P7">
      {/* 비워 둘 자리 ③ — 할 일 함. 홈 상단 (Policy_공통_기반 v1.4 §3) */}
      <TodoInboxSlot />
    </div>
  );
}
