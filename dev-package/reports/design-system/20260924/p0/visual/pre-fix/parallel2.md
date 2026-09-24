# 시각 대조 보고

- 판정 설정: pixelmatch `threshold 0` · `includeAA true` (엄격). 보조 열: `threshold 0.1`.
- 기준: `frontend/.visual/pre-a` · HEAD `f417c769d3f1a26db2a9b27142abc6c4f5574843` · 2026-09-24T01:28:17+00:00
- 후보: `frontend/.visual/pre-b` · HEAD `f417c769d3f1a26db2a9b27142abc6c4f5574843` · 2026-09-24T01:36:14+00:00
- 명세 sha256: `a5ba330601b8f83b15a164191ded15c6bce5dc9dd17b86f0babe17882df35641`
- 캡처 196장 · 장면 33개 · red 4장 · 엄격 차이 픽셀 합 14 · 보조 차이 픽셀 합 0 · 크기 차이 0장
- 종료코드: **1**

## red 목록

- `project-dialog-dark-768` — 엄격 1px · 차이 이미지 `project-dialog-dark-768.diff.png`
- `project-dialog-dark-1440` — 엄격 1px · 차이 이미지 `project-dialog-dark-1440.diff.png`
- `project-close-light-768` — 엄격 1px · 차이 이미지 `project-close-light-768.diff.png`
- `lab-dialog-dark-768` — 엄격 11px · 차이 이미지 `lab-dialog-dark-768.diff.png`

## 불안정 장면

- `project-dialog-dark-768` (같은 HEAD 두 번 찍기에서 차이)
- `project-dialog-dark-1440` (같은 HEAD 두 번 찍기에서 차이)
- `project-close-light-768` (같은 HEAD 두 번 찍기에서 차이)
- `lab-dialog-dark-768` (같은 HEAD 두 번 찍기에서 차이)

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
| `project-dialog-dark-768` | 1 | <0.001 | 0 | 아니오 |
| `project-dialog-dark-1440` | 1 | <0.001 | 0 | 아니오 |
| `project-close-light-375` | 0 | 0 | 0 | 아니오 |
| `project-close-light-768` | 1 | <0.001 | 0 | 아니오 |
| `project-close-light-1440` | 0 | 0 | 0 | 아니오 |
| `project-close-dark-375` | 0 | 0 | 0 | 아니오 |
| `project-close-dark-768` | 0 | 0 | 0 | 아니오 |
| `project-close-dark-1440` | 0 | 0 | 0 | 아니오 |
| `detail-light-375` | 0 | 0 | 0 | 아니오 |
| `detail-light-768` | 0 | 0 | 0 | 아니오 |
| `detail-light-1440` | 0 | 0 | 0 | 아니오 |
| `detail-dark-375` | 0 | 0 | 0 | 아니오 |
| `detail-dark-768` | 0 | 0 | 0 | 아니오 |
| `detail-dark-1440` | 0 | 0 | 0 | 아니오 |
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
| `lab-dialog-dark-768` | 11 | 0.002 | 0 | 아니오 |
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
| `lineage-picker-light-375` | 0 | 0 | 0 | 아니오 |
| `lineage-picker-light-768` | 0 | 0 | 0 | 아니오 |
| `lineage-picker-light-1440` | 0 | 0 | 0 | 아니오 |
| `lineage-picker-dark-375` | 0 | 0 | 0 | 아니오 |
| `lineage-picker-dark-768` | 0 | 0 | 0 | 아니오 |
| `lineage-picker-dark-1440` | 0 | 0 | 0 | 아니오 |
| `login-light-375` | 0 | 0 | 0 | 아니오 |
| `login-light-768` | 0 | 0 | 0 | 아니오 |
| `login-light-1440` | 0 | 0 | 0 | 아니오 |
| `login-dark-375` | 0 | 0 | 0 | 아니오 |
| `login-dark-768` | 0 | 0 | 0 | 아니오 |
| `login-dark-1440` | 0 | 0 | 0 | 아니오 |
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
| `password-change-light-375` | 0 | 0 | 0 | 아니오 |
| `password-change-light-768` | 0 | 0 | 0 | 아니오 |
| `password-change-light-1440` | 0 | 0 | 0 | 아니오 |
| `password-change-dark-375` | 0 | 0 | 0 | 아니오 |
| `password-change-dark-768` | 0 | 0 | 0 | 아니오 |
| `password-change-dark-1440` | 0 | 0 | 0 | 아니오 |
| `gnb-more-light-375` | 0 | 0 | 0 | 아니오 |
| `gnb-more-light-768` | 0 | 0 | 0 | 아니오 |
| `gnb-more-dark-375` | 0 | 0 | 0 | 아니오 |
| `gnb-more-dark-768` | 0 | 0 | 0 | 아니오 |
