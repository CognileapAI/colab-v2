// 잠김 (허용 안 됨) — 본문 대신 잠김 안내와 접근 요청 자리가 나온다 (`§3.3` · `§7` · `§8`).
// 문구는 정본 목업 `데이터셋_상세_260817.html` 의 D-03 장면 그대로다.
export function LockedNotice() {
  return (
    <div className="locked-hero">
      <h2>이름과 요약까지만 보여요</h2>
      <p>요청하면 교수 또는 승인을 맡은 연구원이 검토해요.</p>
      {/* `접근 요청` 버튼의 실물·모달은 E-06(WU-P6)이 채운다 */}
      <div data-slot="access-request" data-fills-in="WU-P6" />
    </div>
  );
}
