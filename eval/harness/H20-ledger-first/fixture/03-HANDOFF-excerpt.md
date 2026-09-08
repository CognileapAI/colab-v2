## 1. 진행도

> ⭑ **⟨2026-09-05 정리⟩ 각 행의 「비고」 원문은 `dev-package/archive/HANDOFF-DETAIL-2026-09.md` 에 있다** — 표에는 상태 표기와 포인터만 남겼다. **상태의 원본은 `work-items.yaml`** 이고 게이트가 읽는 것은 `WU`·`상태` 두 열이다.

표기 — ✅ 닫힘 · 🟦 진행 · ⬜ 대기 · 🟧 부분(사유 필수) · ⛔ 차단(무엇이 막는지)

### T-R 저장소
| WU | 상태 | 비고 |
|---|---|---|
| R0 레포 결정 | ✅ | **`colab-v2` 신규 모노레포** (Ted, 2026-08-22). `colab-dev-package`는 v1 자산으로 archive |
| R1 스캐폴드 + CI 골격 | ✅ | 원격 `CognileapAI/colab-v2`(public) push 완료 · `main` 보호(force-push·삭제 차단, 리뷰 필수 없음) · CI 1회 완주 — 게이트 잡(`contract-gates` 등) 전부 "미구현 — red"로 **설계대로** 실패. 가시성 결정 = `PLAN-SoT §9-⑯` |
