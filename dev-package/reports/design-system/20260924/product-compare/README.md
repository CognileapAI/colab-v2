# 제품(origin/product) ↔ 디자인 구조 브랜치 화면 대조

## 결론

- 공통 30장면 180장: **엄격 차이 0px 180/180** · 보조(threshold 0.1) 0px · 크기 차이 0장 · `diff.mjs` exit 0.
- 180장 모두 PNG 파일 바이트(sha256)까지 같다.
- 브랜치에만 있는 4장면 22장(`account-admin` 6 · `password-change` 6 · `gnb-more` 4 · `primitives` 6)은 product 에 대응 장면이 없어 대조하지 않았다(신규 장면).
- 캡처별 `agent-browser errors` 출력이 비어 있지 않은 캡처: product 0 · structure 0 · 신규 0.
- 이미지를 담은 비교 페이지는 저장소 밖 자립형 HTML 1개(10.0 MB)다. 이 문서에는 이미지가 없다.

## 대조 대상

| 쪽 | 커밋 | 빌드 | 캡처 시각(UTC) |
|---|---|---|---|
| product | `origin/product` = `a5ca67d3e3bd8d6497c4b75bb30df948e9003ab3` | `vite build --config audit.vite.config.ts` 만(아래 ⚠) | 2026-09-24T12:03:15 ~ 12:10:43 |
| structure | `claude/design-system-structure` = `565c55b4188b9d4e0a691b16df2fffe8de71377e` | `npm run audit:build`(tsc 포함) | 2026-09-24T12:11:21 ~ 12:18:49 |
| structure 신규 4장면 | 같음 | 위 빌드 재사용 | 2026-09-24T12:18:55 ~ 12:19:49 |

- 장면 명세: `frontend/scripts/visual-baseline/scenes.json`(34장면 · sha256 `20919450d75f2725687259e10057f7d6aa142eeeaea73f2a3dcf22125d35447a`)에서 브랜치 전용 4장면을 뺀 30장면 명세(sha256 `227e8214972ede1bb7e69a461faf180b84d8baac42d5aa797f8691d78575faa3`)를 양쪽에 같게 썼다. 다른 필드(브라우저 래스터 인자 · 높이 900 · 1배율 · 동작 · 대기)는 그대로다. 신규 4장면 명세 sha256 `9ae163e6e73fec28e964f87a130022c9593b8cf3d277371c987561612c9bd4db`.
- 판정: pixelmatch `threshold 0` · `includeAA true`(엄격).
- ⚠ product 의 `npm run audit:build` 는 앞 단계 `tsc --noEmit -p tsconfig.audit.json` 에서 실패한다 — `audit-design.tsx(124,7): error TS2375`(미리보기 픽스처 `RenderJob` 에 필수 필드 `target` 없음 · 오류 1건). 제품 앱 `tsc --noEmit` 는 0건이고, 미리보기 장면이 그리는 `routes/UnregisteredPreviewPage.tsx`·`components/preview/**` 에 `job.target` 참조가 없다. 그래서 product 쪽은 추적 파일을 바꾸지 않고 `vite build` 만으로 빌드해 찍었다. 브랜치는 P0 에서 이 필드를 채웠다. 이 타입 검사는 어느 게이트에도 걸리지 않는다(`architecture.md §7 후속 5`).
- product 의 `audit-design.tsx` 는 계정 플래그 쿼리(`upload`·`labSettings`·`operator`)를 읽지 않는다. 공통 30장면의 명세 값(업로드 켬 · 연구실 설정 켬 · 운영자 아님)은 product 기본값(`design=full` 이면 업로드 켬 · 연구실 설정 켬 · 운영자 아님)과 같다. `audit-upload.html` 4장면은 양쪽 모두 플래그를 읽지 않는다.
- product 의 frontend 트리는 계획 기준 `ea21d8c2` 와 `frontend/package.json`·`package-lock.json` 의 version(1.1.0) 만 다르다. `frontend/src`·vite 설정 2개에 package version 참조가 없다.

## 집계

| 구분 | 장면 | 캡처 | 동일 | 차이 |
|---|---:|---:|---:|---:|
| 공통(product ↔ structure) | 30 | 180 | 180 | 0 |
| 브랜치에만 있음 | 4 | 22 | — | — |

## 장면별 엄격 차이 px

| 장면 | 라이트 375 | 라이트 768 | 라이트 1440 | 다크 375 | 다크 768 | 다크 1440 | 보조 px 합 | 판정 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `catalog` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 동일 |
| `lab` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 동일 |
| `empty` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 동일 |
| `projects` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 동일 |
| `project-table` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 동일 |
| `project-detail` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 동일 |
| `project-dialog` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 동일 |
| `project-close` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 동일 |
| `detail` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 동일 |
| `settings` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 동일 |
| `members` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 동일 |
| `lab-dialog` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 동일 |
| `search` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 동일 |
| `search-empty` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 동일 |
| `search-down` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 동일 |
| `search-degraded` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 동일 |
| `preview` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 동일 |
| `preview-done` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 동일 |
| `preview-expired` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 동일 |
| `access` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 동일 |
| `pending` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 동일 |
| `approval` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 동일 |
| `approval-dialog` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 동일 |
| `lineage-picker` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 동일 |
| `login` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 동일 |
| `not-found` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 동일 |
| `upload` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 동일 |
| `upload-classify` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 동일 |
| `upload-metadata` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 동일 |
| `upload-link` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 동일 |

브랜치에만 있는 장면(product 에 없음): `account-admin`(라이트·다크 × 375·768·1440) · `password-change`(같음) · `gnb-more`(라이트·다크 × 375·768 — `.gnb-more` 는 900px 이하에서만 보인다) · `primitives`(라이트·다크 × 375·768·1440).

## 다시 만드는 법

캡처 도구는 브랜치에만 있으므로 브랜치를 바꾸기 전에 추적되지 않는 사본을 만든다(`frontend/.visual/` 는 브랜치 `.gitignore` 대상).

1. 브랜치에서 `frontend/scripts/visual-baseline/` 의 5개 파일을 `frontend/.visual/tool/` 로 복사한다. 사본 `capture.py` 에만 `--manifest <경로>` 인자를 더한다(기본 `scenes.json` 대신 그 명세를 읽고 `index.json` 에 그 경로·sha256 을 적는다).
2. 사본 `scenes.json` 에서 위 4장면을 뺀 `scenes-common.json`, 4장면만 둔 `scenes-extra.json` 을 만든다(다른 필드 그대로).
3. `git checkout --detach origin/product` → `frontend/` 에서 `npm ci` → `npx vite build --config audit.vite.config.ts` → 저장소 루트에서 `python3 frontend/.visual/tool/capture.py --manifest frontend/.visual/tool/scenes-common.json --label product --skip-build`.
4. 브랜치로 돌아와 `.codex/upload-preview-audit/` 를 지우고(`emptyOutDir: false`) `frontend/` 에서 `npm ci` → `python3 frontend/.visual/tool/capture.py --manifest frontend/.visual/tool/scenes-common.json --label structure` → 같은 명령에 `--manifest frontend/.visual/tool/scenes-extra.json --label structure-extra --skip-build`.
5. `node frontend/scripts/visual-baseline/diff.mjs frontend/.visual/product frontend/.visual/structure frontend/.visual/product-vs-structure` — 명세 sha256 이 같으므로 `--subset` 없이 비교한다.
6. 비교 페이지: pngjs 로 캡처를 정수배 축소(375px 원본 · 768px 1/2 · 1440px 1/3 · 차이가 있는 캡처는 원본 + 차이 이미지)해 CSS 클래스의 data URI 로 싣는 한 파일 HTML. 같은 내용의 그림은 한 번만 싣는다(이미지 202개 · PNG 7.7 MB).

## 비교 페이지 검증

- 외부 참조: `https?://` 0건 · `<script src`·`<link`·`@import`·`@font-face` 0건 · 절대경로 0건.
- agent-browser 로 폭 360·1280 × 라이트·다크 4조합에서 열어 확인: `scrollWidth ≤ innerWidth`(360 → 345 · 1280 → 1265, 1440 캡처를 펼친 뒤에도 같음) · 페이지 오류 0 · 콘솔 출력 0 · 테마 버튼으로 반대 테마를 고르면 `data-theme` 과 `body` 배경이 바뀜.
