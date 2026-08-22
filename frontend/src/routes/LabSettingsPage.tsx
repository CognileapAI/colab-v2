// S-07 연구실 설정 (`연구실 정보` / `구성원 · 권한` 두 탭) — 본체는 E-01 → WU-G4 가 단계를 배정한다.
// 이 화면 자체가 `연구실 설정` 스위치로 가려진다. 주소를 직접 쳐도 같은 결과여야 하므로(P-11)
// 서버가 403 을 내는 것이 정본이고, 여기 숨김은 UX 다.
export function LabSettingsPage() {
  return <div data-screen="S-07" data-fills-in="WU-G4" />;
}
