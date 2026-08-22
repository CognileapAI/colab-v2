# src/generated — 손으로 고치지 않는다

이 폴더의 파일은 전부 **계약에서 생성된 산출물**이다.

- 원본: `contracts/seams/fe-core.yaml` (+ `contracts/schemas/common.json`)
- 생성: `npm run generate`
- 근거: `CLAUDE.md §3-7` (생성된 타입·클라이언트를 손으로 고치지 않는다) · `frontend/README.md`

고칠 것이 있으면 **계약을 고치고 다시 생성한다.** 생성물은 커밋 대상이며
(`generated-up-to-date` 게이트가 diff 로 검증한다) `.gitignore` 에 넣지 않는다.
