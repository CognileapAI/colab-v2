# H08 픽스처 원천 — 재현 명령

원천 = intent 로스터 (나) H08 · `p3-design-audit-20260905.md:16`(판정표 8행) · 시험 `frontend/test/design-fix-20260908.test.ts:92-112`

```bash
git show 947bf1f:frontend/src/components/detail/detail.css > detail.css
git show 947bf1f:frontend/src/components/upload/upload.css > upload.css
git show 947bf1f:frontend/src/components/lineage/lineageGraph.css > lineageGraph.css
```

- 결함이 **심긴 상태**다. 세 파일 합계 13px 미만 선언은 47건이고, 지적된 **네 유형은 7곳**이다 —
  파일명 `detail.css:101`·`upload.css:106`·`upload.css:168` / 빈 화면 안내 `lineageGraph.css:95`
  / 목록 링크 `lineageGraph.css:81`·`:76` / 오류 본문 `upload.css:92`.
- 무접촉 = `upload.css:138` `.vizerr, .warn` — 이미 13px 이라 고칠 자리가 아니다.
