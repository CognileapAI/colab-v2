# 시각 대조 보고

- 판정 설정: pixelmatch `threshold 0` · `includeAA true` (엄격). 보조 열: `threshold 0.1`.
- 기준: `frontend/.visual/fixfu0925-base` · HEAD `78a66b823702627636076b551e9839675d2e9a88` · 2026-09-25T07:49:55+00:00
- 후보: `frontend/.visual/fixfu0925-final` · HEAD `9812d41f91c2e6f74570450440b89e1ccbd10c63` · 2026-09-25T08:50:08+00:00
- 명세 sha256: `20919450d75f2725687259e10057f7d6aa142eeeaea73f2a3dcf22125d35447a`
- **부분집합 대조(--subset)** — 공통 장면 34개만 비교 · 명세 sha256 기준 `20919450d75f2725687259e10057f7d6aa142eeeaea73f2a3dcf22125d35447a` / 후보 `fa20427a5eb411ddd4b53ee596dbf1a170f4f3eb239cc8857d730b7653ea6ad8` · 기준에만 있는 장면: 없음 · 후보에만 있는 장면: upload-register-ok
- 캡처 202장 · 장면 34개 · red 30장 · 엄격 차이 픽셀 합 558449 · 보조 차이 픽셀 합 214180 · 크기 차이 0장
- 종료코드: **1**

## red 목록

- `detail-light-375` — 엄격 15043px · 차이 이미지 `detail-light-375.diff.png`
- `detail-light-768` — 엄격 28111px · 차이 이미지 `detail-light-768.diff.png`
- `detail-light-1440` — 엄격 48591px · 차이 이미지 `detail-light-1440.diff.png`
- `detail-dark-375` — 엄격 15050px · 차이 이미지 `detail-dark-375.diff.png`
- `detail-dark-768` — 엄격 28118px · 차이 이미지 `detail-dark-768.diff.png`
- `detail-dark-1440` — 엄격 48598px · 차이 이미지 `detail-dark-1440.diff.png`
- `lineage-picker-light-375` — 엄격 5627px · 차이 이미지 `lineage-picker-light-375.diff.png`
- `lineage-picker-light-768` — 엄격 5107px · 차이 이미지 `lineage-picker-light-768.diff.png`
- `lineage-picker-light-1440` — 엄격 5107px · 차이 이미지 `lineage-picker-light-1440.diff.png`
- `lineage-picker-dark-375` — 엄격 5680px · 차이 이미지 `lineage-picker-dark-375.diff.png`
- `lineage-picker-dark-768` — 엄격 5160px · 차이 이미지 `lineage-picker-dark-768.diff.png`
- `lineage-picker-dark-1440` — 엄격 5160px · 차이 이미지 `lineage-picker-dark-1440.diff.png`
- `login-light-375` — 엄격 11701px · 차이 이미지 `login-light-375.diff.png`
- `login-light-768` — 엄격 11932px · 차이 이미지 `login-light-768.diff.png`
- `login-light-1440` — 엄격 11932px · 차이 이미지 `login-light-1440.diff.png`
- `login-dark-375` — 엄격 11804px · 차이 이미지 `login-dark-375.diff.png`
- `login-dark-768` — 엄격 12048px · 차이 이미지 `login-dark-768.diff.png`
- `login-dark-1440` — 엄격 12048px · 차이 이미지 `login-dark-1440.diff.png`
- `password-change-light-375` — 엄격 11619px · 차이 이미지 `password-change-light-375.diff.png`
- `password-change-light-768` — 엄격 11892px · 차이 이미지 `password-change-light-768.diff.png`
- `password-change-light-1440` — 엄격 11892px · 차이 이미지 `password-change-light-1440.diff.png`
- `password-change-dark-375` — 엄격 11804px · 차이 이미지 `password-change-dark-375.diff.png`
- `password-change-dark-768` — 엄격 12048px · 차이 이미지 `password-change-dark-768.diff.png`
- `password-change-dark-1440` — 엄격 12048px · 차이 이미지 `password-change-dark-1440.diff.png`
- `primitives-light-375` — 엄격 35534px · 차이 이미지 `primitives-light-375.diff.png`
- `primitives-light-768` — 엄격 32288px · 차이 이미지 `primitives-light-768.diff.png`
- `primitives-light-1440` — 엄격 32289px · 차이 이미지 `primitives-light-1440.diff.png`
- `primitives-dark-375` — 엄격 35574px · 차이 이미지 `primitives-dark-375.diff.png`
- `primitives-dark-768` — 엄격 32322px · 차이 이미지 `primitives-dark-768.diff.png`
- `primitives-dark-1440` — 엄격 32322px · 차이 이미지 `primitives-dark-1440.diff.png`

## 불안정 장면

해당 없음 (기준·후보의 HEAD 가 다르거나 미커밋 변경이 있다 — 차이는 코드 변경 후보로 읽는다)

## 캡처별 표

| 캡처 | 엄격 px | 엄격 % | 보조 px | 크기 차이 |
|---|---:|---:|---:|---|
| `catalog-light-375` | 0 | 0 | 0 | 아니오 |
| `catalog-light-768` | 0 | 0 | 0 | 아니오 |
| `catalog-light-1440` | 0 | 0 | 0 | 아니오 |
| `catalog-dark-375` | 0 | 0 | 0 | 아니오 |
| `catalog-dark-768` | 0 | 0 | 0 | 아니오 |
| `catalog-dark-1440` | 0 | 0 | 0 | 아니오 |
| `lab-light-375` | 0 | 0 | 0 | 아니오 |
| `lab-light-768` | 0 | 0 | 0 | 아니오 |
| `lab-light-1440` | 0 | 0 | 0 | 아니오 |
| `lab-dark-375` | 0 | 0 | 0 | 아니오 |
| `lab-dark-768` | 0 | 0 | 0 | 아니오 |
| `lab-dark-1440` | 0 | 0 | 0 | 아니오 |
| `empty-light-375` | 0 | 0 | 0 | 아니오 |
| `empty-light-768` | 0 | 0 | 0 | 아니오 |
| `empty-light-1440` | 0 | 0 | 0 | 아니오 |
| `empty-dark-375` | 0 | 0 | 0 | 아니오 |
| `empty-dark-768` | 0 | 0 | 0 | 아니오 |
| `empty-dark-1440` | 0 | 0 | 0 | 아니오 |
| `projects-light-375` | 0 | 0 | 0 | 아니오 |
| `projects-light-768` | 0 | 0 | 0 | 아니오 |
| `projects-light-1440` | 0 | 0 | 0 | 아니오 |
| `projects-dark-375` | 0 | 0 | 0 | 아니오 |
| `projects-dark-768` | 0 | 0 | 0 | 아니오 |
| `projects-dark-1440` | 0 | 0 | 0 | 아니오 |
| `project-table-light-375` | 0 | 0 | 0 | 아니오 |
| `project-table-light-768` | 0 | 0 | 0 | 아니오 |
| `project-table-light-1440` | 0 | 0 | 0 | 아니오 |
| `project-table-dark-375` | 0 | 0 | 0 | 아니오 |
| `project-table-dark-768` | 0 | 0 | 0 | 아니오 |
| `project-table-dark-1440` | 0 | 0 | 0 | 아니오 |
| `project-detail-light-375` | 0 | 0 | 0 | 아니오 |
| `project-detail-light-768` | 0 | 0 | 0 | 아니오 |
| `project-detail-light-1440` | 0 | 0 | 0 | 아니오 |
| `project-detail-dark-375` | 0 | 0 | 0 | 아니오 |
| `project-detail-dark-768` | 0 | 0 | 0 | 아니오 |
| `project-detail-dark-1440` | 0 | 0 | 0 | 아니오 |
| `project-dialog-light-375` | 0 | 0 | 0 | 아니오 |
| `project-dialog-light-768` | 0 | 0 | 0 | 아니오 |
| `project-dialog-light-1440` | 0 | 0 | 0 | 아니오 |
| `project-dialog-dark-375` | 0 | 0 | 0 | 아니오 |
| `project-dialog-dark-768` | 0 | 0 | 0 | 아니오 |
| `project-dialog-dark-1440` | 0 | 0 | 0 | 아니오 |
| `project-close-light-375` | 0 | 0 | 0 | 아니오 |
| `project-close-light-768` | 0 | 0 | 0 | 아니오 |
| `project-close-light-1440` | 0 | 0 | 0 | 아니오 |
| `project-close-dark-375` | 0 | 0 | 0 | 아니오 |
| `project-close-dark-768` | 0 | 0 | 0 | 아니오 |
| `project-close-dark-1440` | 0 | 0 | 0 | 아니오 |
| `detail-light-375` | 15043 | 1.115 | 44 | 아니오 |
| `detail-light-768` | 28111 | 1.262 | 40 | 아니오 |
| `detail-light-1440` | 48591 | 1.070 | 40 | 아니오 |
| `detail-dark-375` | 15050 | 1.115 | 44 | 아니오 |
| `detail-dark-768` | 28118 | 1.262 | 40 | 아니오 |
| `detail-dark-1440` | 48598 | 1.070 | 40 | 아니오 |
| `settings-light-375` | 0 | 0 | 0 | 아니오 |
| `settings-light-768` | 0 | 0 | 0 | 아니오 |
| `settings-light-1440` | 0 | 0 | 0 | 아니오 |
| `settings-dark-375` | 0 | 0 | 0 | 아니오 |
| `settings-dark-768` | 0 | 0 | 0 | 아니오 |
| `settings-dark-1440` | 0 | 0 | 0 | 아니오 |
| `members-light-375` | 0 | 0 | 0 | 아니오 |
| `members-light-768` | 0 | 0 | 0 | 아니오 |
| `members-light-1440` | 0 | 0 | 0 | 아니오 |
| `members-dark-375` | 0 | 0 | 0 | 아니오 |
| `members-dark-768` | 0 | 0 | 0 | 아니오 |
| `members-dark-1440` | 0 | 0 | 0 | 아니오 |
| `lab-dialog-light-375` | 0 | 0 | 0 | 아니오 |
| `lab-dialog-light-768` | 0 | 0 | 0 | 아니오 |
| `lab-dialog-light-1440` | 0 | 0 | 0 | 아니오 |
| `lab-dialog-dark-375` | 0 | 0 | 0 | 아니오 |
| `lab-dialog-dark-768` | 0 | 0 | 0 | 아니오 |
| `lab-dialog-dark-1440` | 0 | 0 | 0 | 아니오 |
| `search-light-375` | 0 | 0 | 0 | 아니오 |
| `search-light-768` | 0 | 0 | 0 | 아니오 |
| `search-light-1440` | 0 | 0 | 0 | 아니오 |
| `search-dark-375` | 0 | 0 | 0 | 아니오 |
| `search-dark-768` | 0 | 0 | 0 | 아니오 |
| `search-dark-1440` | 0 | 0 | 0 | 아니오 |
| `search-empty-light-375` | 0 | 0 | 0 | 아니오 |
| `search-empty-light-768` | 0 | 0 | 0 | 아니오 |
| `search-empty-light-1440` | 0 | 0 | 0 | 아니오 |
| `search-empty-dark-375` | 0 | 0 | 0 | 아니오 |
| `search-empty-dark-768` | 0 | 0 | 0 | 아니오 |
| `search-empty-dark-1440` | 0 | 0 | 0 | 아니오 |
| `search-down-light-375` | 0 | 0 | 0 | 아니오 |
| `search-down-light-768` | 0 | 0 | 0 | 아니오 |
| `search-down-light-1440` | 0 | 0 | 0 | 아니오 |
| `search-down-dark-375` | 0 | 0 | 0 | 아니오 |
| `search-down-dark-768` | 0 | 0 | 0 | 아니오 |
| `search-down-dark-1440` | 0 | 0 | 0 | 아니오 |
| `search-degraded-light-375` | 0 | 0 | 0 | 아니오 |
| `search-degraded-light-768` | 0 | 0 | 0 | 아니오 |
| `search-degraded-light-1440` | 0 | 0 | 0 | 아니오 |
| `search-degraded-dark-375` | 0 | 0 | 0 | 아니오 |
| `search-degraded-dark-768` | 0 | 0 | 0 | 아니오 |
| `search-degraded-dark-1440` | 0 | 0 | 0 | 아니오 |
| `preview-light-375` | 0 | 0 | 0 | 아니오 |
| `preview-light-768` | 0 | 0 | 0 | 아니오 |
| `preview-light-1440` | 0 | 0 | 0 | 아니오 |
| `preview-dark-375` | 0 | 0 | 0 | 아니오 |
| `preview-dark-768` | 0 | 0 | 0 | 아니오 |
| `preview-dark-1440` | 0 | 0 | 0 | 아니오 |
| `preview-done-light-375` | 0 | 0 | 0 | 아니오 |
| `preview-done-light-768` | 0 | 0 | 0 | 아니오 |
| `preview-done-light-1440` | 0 | 0 | 0 | 아니오 |
| `preview-done-dark-375` | 0 | 0 | 0 | 아니오 |
| `preview-done-dark-768` | 0 | 0 | 0 | 아니오 |
| `preview-done-dark-1440` | 0 | 0 | 0 | 아니오 |
| `preview-expired-light-375` | 0 | 0 | 0 | 아니오 |
| `preview-expired-light-768` | 0 | 0 | 0 | 아니오 |
| `preview-expired-light-1440` | 0 | 0 | 0 | 아니오 |
| `preview-expired-dark-375` | 0 | 0 | 0 | 아니오 |
| `preview-expired-dark-768` | 0 | 0 | 0 | 아니오 |
| `preview-expired-dark-1440` | 0 | 0 | 0 | 아니오 |
| `access-light-375` | 0 | 0 | 0 | 아니오 |
| `access-light-768` | 0 | 0 | 0 | 아니오 |
| `access-light-1440` | 0 | 0 | 0 | 아니오 |
| `access-dark-375` | 0 | 0 | 0 | 아니오 |
| `access-dark-768` | 0 | 0 | 0 | 아니오 |
| `access-dark-1440` | 0 | 0 | 0 | 아니오 |
| `pending-light-375` | 0 | 0 | 0 | 아니오 |
| `pending-light-768` | 0 | 0 | 0 | 아니오 |
| `pending-light-1440` | 0 | 0 | 0 | 아니오 |
| `pending-dark-375` | 0 | 0 | 0 | 아니오 |
| `pending-dark-768` | 0 | 0 | 0 | 아니오 |
| `pending-dark-1440` | 0 | 0 | 0 | 아니오 |
| `approval-light-375` | 0 | 0 | 0 | 아니오 |
| `approval-light-768` | 0 | 0 | 0 | 아니오 |
| `approval-light-1440` | 0 | 0 | 0 | 아니오 |
| `approval-dark-375` | 0 | 0 | 0 | 아니오 |
| `approval-dark-768` | 0 | 0 | 0 | 아니오 |
| `approval-dark-1440` | 0 | 0 | 0 | 아니오 |
| `approval-dialog-light-375` | 0 | 0 | 0 | 아니오 |
| `approval-dialog-light-768` | 0 | 0 | 0 | 아니오 |
| `approval-dialog-light-1440` | 0 | 0 | 0 | 아니오 |
| `approval-dialog-dark-375` | 0 | 0 | 0 | 아니오 |
| `approval-dialog-dark-768` | 0 | 0 | 0 | 아니오 |
| `approval-dialog-dark-1440` | 0 | 0 | 0 | 아니오 |
| `lineage-picker-light-375` | 5627 | 1.667 | 5213 | 아니오 |
| `lineage-picker-light-768` | 5107 | 0.739 | 4693 | 아니오 |
| `lineage-picker-light-1440` | 5107 | 0.394 | 4693 | 아니오 |
| `lineage-picker-dark-375` | 5680 | 1.683 | 5206 | 아니오 |
| `lineage-picker-dark-768` | 5160 | 0.747 | 4686 | 아니오 |
| `lineage-picker-dark-1440` | 5160 | 0.398 | 4686 | 아니오 |
| `login-light-375` | 11701 | 3.467 | 11383 | 아니오 |
| `login-light-768` | 11932 | 1.726 | 11646 | 아니오 |
| `login-light-1440` | 11932 | 0.921 | 11646 | 아니오 |
| `login-dark-375` | 11804 | 3.497 | 11386 | 아니오 |
| `login-dark-768` | 12048 | 1.743 | 11649 | 아니오 |
| `login-dark-1440` | 12048 | 0.930 | 11649 | 아니오 |
| `not-found-light-375` | 0 | 0 | 0 | 아니오 |
| `not-found-light-768` | 0 | 0 | 0 | 아니오 |
| `not-found-light-1440` | 0 | 0 | 0 | 아니오 |
| `not-found-dark-375` | 0 | 0 | 0 | 아니오 |
| `not-found-dark-768` | 0 | 0 | 0 | 아니오 |
| `not-found-dark-1440` | 0 | 0 | 0 | 아니오 |
| `upload-light-375` | 0 | 0 | 0 | 아니오 |
| `upload-light-768` | 0 | 0 | 0 | 아니오 |
| `upload-light-1440` | 0 | 0 | 0 | 아니오 |
| `upload-dark-375` | 0 | 0 | 0 | 아니오 |
| `upload-dark-768` | 0 | 0 | 0 | 아니오 |
| `upload-dark-1440` | 0 | 0 | 0 | 아니오 |
| `upload-classify-light-375` | 0 | 0 | 0 | 아니오 |
| `upload-classify-light-768` | 0 | 0 | 0 | 아니오 |
| `upload-classify-light-1440` | 0 | 0 | 0 | 아니오 |
| `upload-classify-dark-375` | 0 | 0 | 0 | 아니오 |
| `upload-classify-dark-768` | 0 | 0 | 0 | 아니오 |
| `upload-classify-dark-1440` | 0 | 0 | 0 | 아니오 |
| `upload-metadata-light-375` | 0 | 0 | 0 | 아니오 |
| `upload-metadata-light-768` | 0 | 0 | 0 | 아니오 |
| `upload-metadata-light-1440` | 0 | 0 | 0 | 아니오 |
| `upload-metadata-dark-375` | 0 | 0 | 0 | 아니오 |
| `upload-metadata-dark-768` | 0 | 0 | 0 | 아니오 |
| `upload-metadata-dark-1440` | 0 | 0 | 0 | 아니오 |
| `upload-link-light-375` | 0 | 0 | 0 | 아니오 |
| `upload-link-light-768` | 0 | 0 | 0 | 아니오 |
| `upload-link-light-1440` | 0 | 0 | 0 | 아니오 |
| `upload-link-dark-375` | 0 | 0 | 0 | 아니오 |
| `upload-link-dark-768` | 0 | 0 | 0 | 아니오 |
| `upload-link-dark-1440` | 0 | 0 | 0 | 아니오 |
| `account-admin-light-375` | 0 | 0 | 0 | 아니오 |
| `account-admin-light-768` | 0 | 0 | 0 | 아니오 |
| `account-admin-light-1440` | 0 | 0 | 0 | 아니오 |
| `account-admin-dark-375` | 0 | 0 | 0 | 아니오 |
| `account-admin-dark-768` | 0 | 0 | 0 | 아니오 |
| `account-admin-dark-1440` | 0 | 0 | 0 | 아니오 |
| `password-change-light-375` | 11619 | 3.443 | 11193 | 아니오 |
| `password-change-light-768` | 11892 | 1.720 | 11430 | 아니오 |
| `password-change-light-1440` | 11892 | 0.918 | 11430 | 아니오 |
| `password-change-dark-375` | 11804 | 3.497 | 11200 | 아니오 |
| `password-change-dark-768` | 12048 | 1.743 | 11441 | 아니오 |
| `password-change-dark-1440` | 12048 | 0.930 | 11441 | 아니오 |
| `gnb-more-light-375` | 0 | 0 | 0 | 아니오 |
| `gnb-more-light-768` | 0 | 0 | 0 | 아니오 |
| `gnb-more-dark-375` | 0 | 0 | 0 | 아니오 |
| `gnb-more-dark-768` | 0 | 0 | 0 | 아니오 |
| `primitives-light-375` | 35534 | 6.044 | 8224 | 아니오 |
| `primitives-light-768` | 32288 | 3.065 | 7590 | 아니오 |
| `primitives-light-1440` | 32289 | 1.808 | 7585 | 아니오 |
| `primitives-dark-375` | 35574 | 6.051 | 8387 | 아니오 |
| `primitives-dark-768` | 32322 | 3.068 | 7734 | 아니오 |
| `primitives-dark-1440` | 32322 | 1.810 | 7741 | 아니오 |
