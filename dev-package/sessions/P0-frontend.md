# WU-P0 · FE 조각 — 앱 셸

> 대상: `sessions/P0.md` §2 「FE 셸」 · §4 산출물 5 · §5 완료 판정 #7.
> 쓴 곳은 `frontend/` 아래뿐이다. `contracts/`·`gates/`·`services/`·`db/` 는 건드리지 않았다.

---

## 1. 스택 · 핀한 버전

`PLAN-SoT.md §9-㊳` 확정 — **TypeScript + React + Vite**. 이 문서가 값을 다시 정하지 않는다.

의존성은 **전부 exact 핀**(범위 기호 없음)이고 `package-lock.json` 을 커밋한다 → `npm ci` 재현.

| | 버전 | 왜 |
|---|---|---|
| node | 22 (`engines: >=22`) | 실행 환경 |
| react · react-dom | 19.2.8 | — |
| react-router-dom | 7.18.2 | 라우팅 |
| openapi-fetch | 0.17.0 | 생성 타입(`paths`)을 그대로 먹는 클라이언트. 별도 클라이언트 코드를 손으로 쓰지 않는다 |
| vite | 8.2.2 | 정적 번들 (`frontend/README` — 정적 배포) |
| @vitejs/plugin-react | 6.1.0 | — |
| typescript | **5.9.3** | `openapi-typescript@7` 의 peer 가 `^5.x` 다. 처음 설치가 끌어온 7.0.2 는 peer 밖이라 내렸다 |
| openapi-typescript | 7.13.0 | 계약 → 타입 생성 |
| vitest · jsdom · @testing-library/react · @testing-library/jest-dom | 4.1.11 · 29.1.1 · 16.3.2 · 7.0.1 | 완료 판정 #7 회귀 |

tsconfig 는 `strict` 에 더해 `noUncheckedIndexedAccess` · `exactOptionalPropertyTypes` ·
`verbatimModuleSyntax` · `noUnusedLocals/Parameters` 를 켰다.

## 2. 생성 클라이언트

```
contracts/seams/fe-core.yaml (+ contracts/schemas/common.json)  →  frontend/src/generated/fe-core.ts
npm run generate
```

- 생성물은 **한 곳(`src/generated/`)에만** 모은다. 파일 머리에 openapi-typescript 의
  `Do not make direct changes to the file.` 가 박히고, `src/generated/README.md` 가
  `CLAUDE.md §3-7` 근거와 함께 손수정 금지를 다시 못 박는다.
- `common.json` 의 `$ref` 가 정상 해석된다 — `PermissionSwitch` 가
  `"업로드·편집" | "프로젝트 생성" | "승인 위임" | "연구실 설정"` 유니온으로 나온다.
- 재실행 idempotent 확인 완료(아래 §7). 생성물은 `.gitignore` 대상이 아니다
  (루트 `.gitignore` 말미 주석 — `generated-up-to-date` 게이트가 diff 로 본다).
- `src/api/client.ts` 는 `createClient<paths>({ baseUrl: '/api/v1' })` 한 줄과
  생성 타입 재수출뿐이다. 요청/응답 형태를 손으로 다시 선언한 곳이 없다.

## 3. GNB — 탭 구성과 정본 근거

정의는 `src/shell/nav.ts` 한 곳이다(`MAIN_NAV`). 라벨은 정본 문자열 그대로다.

| # | 라벨 | 근거 |
|---|---|---|
| 1 | **연구실** | `Policy_공통_기반 v1.4 §1` — "**첫 탭 이름은 `연구실`이다** … `홈`이라는 이름은 나중에 개인 층이 생길 때를 위해 비워 둔다" (v1.4 개정 이력 ①, 2026-08-17) · `IA_사이트맵 §3` 동일 |
| 2 | 프로젝트 | `Policy_공통_기반 v1.4 §1` 다이어그램 `연구실 · 프로젝트 · 데이터셋` · `IA_사이트맵 §3` "주 영역 3개. 전원 공통" |
| 3 | 데이터셋 | 〃 |

셸의 나머지도 정본 그대로다.

- **연구실 전환기**(좌) · **아바타**(우) — `IA_사이트맵 §3`. 이름은 서버가 준 `labName`·`name` 을 그린다.
- **업로드** — 1급 버튼. `업로드·편집` 이 켜진 사람에게만 **보인다**. 화면이 아니라 전체 화면 모달이라
  라우트를 만들지 않았다 (`Policy_공통_기반 §2.3`). 모달 본체는 E-04 → **WU-P2**.
- **연구실 설정** — `연구실 설정` 스위치가 켜진 사람에게만 보인다 (`Policy §1`).
- **검색은 GNB 에 없다** (`Policy §1`) — 넣지 않았다.
- 남는 가로 여백은 주 내비가 먹는다(`margin-right:auto` on `.mainnav`) — 우측 버튼은 권한에 따라
  숨는 요소라 거기에 여백을 걸면 화면이 무너진다는 `Policy §1` 의 이유를 그대로 옮겼다.
- **GNB 하이라이트는 화면 주인 탭 고정** (`Policy §2.3`) — `ownerTabOf(pathname)`.
  라우터의 `isActive` 를 쓰지 않은 이유가 이것이다.
- 색·간격·구조는 목업 `mockups/제품_260817.html` 의 `.gnb` 블록에서 옮겼다
  (높이 64 · `--color-border-shell` 밑줄 · 활성 탭 흰 면 + 잉크 밑줄 3px). 임의 변형 없음.

## 4. 권한 게이트 틀 — 두 축을 파일부터 나눴다

`P-14`("두 축은 서로 다른 처리다 … 한 메커니즘으로 합치지 않는다")를 **디렉터리 구조로** 강제했다.
합치려면 두 파일을 합쳐야 하므로 리뷰에서 눈에 띈다.

| | 축 A — 권한 없음 → **숨김** | 축 B — 데이터 잠김 → **노출 + 요청 자리** |
|---|---|---|
| 원칙 | `P-12` | `P-13` · `P-34` |
| 파일 | `src/permission/PermissionGate.tsx` | `src/permission/LockedContent.tsx` |
| 입력 | `/me` 의 `permissions`(스위치 4종) · 서버가 건별로 내린 `actions.*`·`canEdit`·`canManage` | 응답의 `bodyAccessible` |
| 없을 때 | `null` 을 그린다 — DOM 에서 사라진다. 비활성 버튼·토스트를 만들지 않는다 | 이름·요약(`header`)은 그대로 두고 **본체 자리만** 잠금 표시 + `접근 요청` 으로 바꾼다 |
| API | `PermissionGate requires=` · `ActionGate allowed=` · `useHasPermission()` | `LockedContent bodyAccessible= header= request=` |

- **화면이 역할로 권한을 재계산하지 않는다** (`P-6`·`P-7`). `Role` 값을 읽는 분기가 코드에 하나도 없다 —
  판정은 전부 서버가 실어 준 boolean 을 그대로 읽는다.
- `/me` 응답 도착 전에는 `account === null` 이고 모든 스위치를 꺼진 것으로 본다 — **fail-closed**.
- **규칙 본체는 P6 이다.** 어느 행동이 어느 스위치인지, 접근 요청 버튼의 실물은 여기서 만들지 않았다.
- 서버 쪽 동일 기준(`P-11`)은 core-api 몫이다 — 화면 숨김은 UX 라고 각 파일에 적어 뒀다.

## 5. 비워 둘 자리 3곳

정본 `Policy_공통_기반 v1.4 §3` 표를 그대로 옮겼다. 각 파일 머리 주석에 **채우는 WU** 를 적었다.

| 자리 | 컴포넌트 | 마커 | 어디에 | 채우는 WU |
|---|---|---|---|---|
| Verified 배지 | `placeholders/VerifiedBadgeSlot.tsx` | `data-slot="verified-badge"` | 상세 헤더 · 검색 카드 · 카탈로그 행 | **P6** (E-06) |
| 잠긴 데이터 표시 | `placeholders/LockIndicatorSlot.tsx` | `data-slot="lock-indicator"` | 검색 카드 · 카탈로그 행 · 상세 | **P6** (E-06) |
| 할 일 함 | `placeholders/TodoInboxSlot.tsx` | `data-slot="todo-inbox"` | 홈(=`연구실` 화면) 상단 | **P6 · P7** (E-06 · E-07) |

셸 단계에서 실제로 렌더되는 자리 — 할 일 함은 `/lab`, 나머지 둘은 `/datasets`.
잠금 표시는 `LockedContent` 의 잠긴 분기에서도 쓰인다.

## 6. 라우팅

| 경로 | 화면 | 본체를 만드는 WU |
|---|---|---|
| `/` | → `/lab` 로 보낸다 (`IA_사이트맵 §4` — 세 여정의 시작점) | — |
| `/lab` | S-01 연구실(대시보드) | P7 (E-07) |
| `/projects` | S-02 프로젝트 | P5 (E-05) |
| `/datasets` | S-03 카탈로그 | P1 (E-02) |
| `/lab-settings` | S-07 연구실 설정 | G4 가 단계 배정 |

각 라우트는 **자리표시자**다 — `data-screen` · `data-fills-in` 만 붙은 빈 컨테이너.
업로드(S-04)는 라우트가 아니다(모달). 검색 결과(S-06)·데이터셋 상세(S-05)·미등록 미리보기(S-08)는
화면 본체가 P1 이후 몫이라 **경로를 미리 발명하지 않았다**.

## 7. 검증 — 실제로 돌린 명령과 출력

```
$ cd frontend && rm -rf node_modules && npm ci
added 146 packages in 16s

$ npm run build          # = tsc --noEmit && vite build
> tsc --noEmit && vite build
vite v8.2.2 building client environment for production...
✓ 40 modules transformed.
dist/index.html                   0.38 kB │ gzip:  0.26 kB
dist/assets/index-DChEh9Pk.css    4.12 kB │ gzip:  1.21 kB
dist/assets/index-Bz6dVmBp.js   239.67 kB │ gzip: 76.82 kB │ map: 1,313.31 kB
✓ built in 945ms

$ npm run typecheck
> tsc --noEmit
(출력 없음 — 0 에러)

$ npm test
 Test Files  2 passed (2)
      Tests  14 passed (14)
```

### 완료 판정 #7 증명

**① 빌드 산출물 직접 확인** — 번들에 박힌 내비 정의를 읽었다.

```
$ node -e "const s=require('fs').readFileSync('dist/assets/index-Bz6dVmBp.js','utf8');
           const i=s.indexOf('연구실'); console.log(s.slice(i-80,i+120));
           for(const k of ['todo-inbox','verified-badge','lock-indicator']) console.log(k, s.includes(k));
           console.log('label:\"홈\" 존재:', /label:\"홈\"/.test(s));"

… or=[{id:`lab`,label:`연구실`,path:`/lab`},{id:`projects`,label:`프로젝트`,path:`/projects`},
      {id:`datasets`,label:`데이터셋`,path:`/datasets`}] …
todo-inbox true
verified-badge true
lock-indicator true
label:"홈" 존재: false
```

**② 회귀 테스트** (`test/shell.test.tsx` — 사람이 지우면 red 가 된다)

- `MAIN_NAV` 라벨 배열이 `['연구실','프로젝트','데이터셋']` 인가
- 렌더된 GNB 의 **첫 번째 `<a>` 글자가 `연구실`** 이고 `홈` 은 화면에 없는가
- 하이라이트가 화면 주인 탭에 고정되는가 (`/datasets` 에서 3번 탭 활성)
- `/lab` 에 `data-slot="todo-inbox"`, `/datasets` 에 `verified-badge`·`lock-indicator` 가 있는가

`test/permission.test.tsx` 는 두 축을 각각, 그리고 **교차로** 묶었다 —
스위치가 전부 꺼져도 잠기지 않은 본체는 보이고, 전부 켜져도 잠긴 본체는 열리지 않는다(P-14).

**③ 생성 idempotent**

```
$ cp src/generated/fe-core.ts /tmp/g.ts && npm run generate && diff -q /tmp/g.ts src/generated/fe-core.ts
GENERATE IDEMPOTENT
```

**④ .gitignore**

```
$ git check-ignore -v frontend/node_modules/.package-lock.json frontend/dist/index.html
.gitignore:12:node_modules/	frontend/node_modules/.package-lock.json
.gitignore:13:dist/	frontend/dist/index.html
$ git check-ignore -v frontend/src/generated/fe-core.ts
(무시되지 않음 — 생성물은 추적 대상)
```

**⑤ 기존 게이트 회귀 없음**

```
$ ./gates/run.sh planning-freshness
planning-freshness green — 15개 임베드 블록 전부 원본과 일치.

$ ./gates/run.sh contract-lint
contract-lint green — seam 3건, 룰 위반 0.
```

## 8. 정본 근거가 없어 **빼거나 최소화한** 것

| 뺀 것 | 이유 |
|---|---|
| 연구실 전환기 드롭다운 목록 · 아바타 드롭다운 내용 | 목업의 드롭다운은 **역할 미리보기(데모)** 컨트롤이 절반이라 제품 규격이 아니다. 정본이 목록 형태를 주지 않아 버튼 자리만 뒀다 |
| 업로드 모달 | 정본이 전체 화면 모달이라고만 정했고 내용은 E-04 다. 버튼은 두되 동작은 WU-P2 |
| 로그인·인증 화면 | 정본 화면 인벤토리(`IA_사이트맵 §5`)에 없다 |
| `홈` 탭 · GNB 검색 | 정본이 **명시적으로 뺐다** (`Policy v1.4 §1`) |
| 404 화면 문구·디자인 | 정본에 값이 없다. 빈 컨테이너만 |
| S-05/S-06/S-08 라우트 경로 | 화면 본체가 P1 이후라 경로를 미리 발명하지 않았다 |
| 목업 토큰 전량 복사 | 셸이 실제로 쓰는 토큰만 `src/shell/tokens.css` 로 옮겼다. 값은 한 자도 바꾸지 않았다. 상태색·AI 액센트는 그 화면을 만드는 WU 가 옮긴다 (크림슨/바이올렛은 **AI 액션 전용** — `Policy §4`) |
| 반응형 브레이크포인트 | 목업에 있으나 셸 검증 범위 밖이고 화면이 붙어야 실측이 된다. 화면 WU 에서 목업 그대로 옮긴다 |

## 9. URL 경로는 정본이 아니라 **레포 결정**이다

`Policy_공통_기반` 도 `IA_사이트맵` 도 URL 문자열을 주지 않는다.
`/lab` `/projects` `/datasets` `/lab-settings` 는 탭 id 를 그대로 쓴 이 레포의 결정이며,
`src/shell/nav.ts` 주석에도 그렇게 적었다. 정본이 나중에 값을 주면 그 표가 이긴다.
