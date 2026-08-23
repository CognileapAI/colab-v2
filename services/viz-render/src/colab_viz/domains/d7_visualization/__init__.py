"""D7 Visualization — 미리보기가 요구하는 **최소 렌더 경로** (`〈63〉-㉮`).

여기 있는 것 — 렌더 작업(`createRender`·`getRender`) · 타일 서빙(`getRenderTile`) ·
팔레트(`listPalettes`).

**여기 없는 것과 그 이유** — 데이터셋 상세의 2D 렌더 3종(격자·경계·점)과
`createScreenshot` 은 **P3** 다. 이 레인의 경계는 「미리보기가 요구하는 범위까지」이고,
그 밖으로 넓히는 것은 범위 확대다 (`P2-EXEC §3 레인 표`).
"""
