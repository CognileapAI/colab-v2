// S-03 데이터셋 목록(카탈로그) — 화면 본체는 E-02 → **WU-P1**. 여기는 자리표시자다.
import { VerifiedBadgeSlot } from '../placeholders/VerifiedBadgeSlot';
import { LockIndicatorSlot } from '../placeholders/LockIndicatorSlot';

export function DatasetsPage() {
  return (
    <div data-screen="S-03" data-fills-in="WU-P1">
      {/* 비워 둘 자리 ① — Verified 배지. 카탈로그 행 · 검색 카드 · 상세 헤더 */}
      <VerifiedBadgeSlot />
      {/* 비워 둘 자리 ② — 잠긴 데이터 표시. 행은 사라지지 않는다 (P-13) */}
      <LockIndicatorSlot />
    </div>
  );
}
