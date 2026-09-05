// 상세 수정 **진입점** — 헤더 우측 한 자리 (WU-A3 · PRD-22).
//
// 관문은 `업로드·편집` 스위치 하나다 — 서버가 같은 스위치로 판정한다
// (`routes/catalog.py` `update_dataset` → `_require_upload_edit` · `〈59〉-②`
//  「소유자를 별도 관문으로 만들지 않는다」). 화면이 조건을 따로 짓지 않는다 (P-6·P-7).
//
// 꺼져 있으면 **DOM 에서 사라진다** (P-12) — 비활성 버튼도 경고 토스트도 두지 않는다.
import { PermissionGate } from '../../permission/PermissionGate';

export function DatasetEditEntry(props: { onOpen: () => void; disabled?: boolean }) {
  return (
    <PermissionGate requires="업로드·편집">
      <button
        type="button"
        className="btn btn-secondary"
        data-testid="detail-edit-open"
        disabled={props.disabled === true}
        onClick={props.onOpen}
      >
        수정
      </button>
    </PermissionGate>
  );
}
