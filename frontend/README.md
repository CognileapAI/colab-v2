# frontend

정적 배포. 타입 안전 라우팅 + 생성 클라이언트.

## 규칙

- **생성된 타입·클라이언트만 쓴다.** 손수정 금지 — v1 PoC의 #1 버그가 FE-BE 타입 수동 동기화였다
- 화면 규격의 정본은 260818 에픽별 목업. 임의 변형 금지

## 화면 (v2 전체)

| 화면 | 에픽 | 단계 |
|---|---|---|
| S-03 카탈로그 | E-02 | 1 |
| S-05 데이터셋 상세 (헤더·기본정보 / 계보·시각화 / 활용 프로젝트) | E-03 | 1 · 3 · 5 |
| S-04 업로드 전체화면 모달 · S-08 미등록 미리보기 | E-04 | 2 |
| S-01 검색 히어로 · S-06 검색 결과 | E-02 | 4 |
| S-02 · S-02b 프로젝트 | E-05 | 5 |
| 접근 요청 모달 · 거절 사유 · 승인 액션 | E-06 | 6 |
| S-01 연구실 대시보드 | E-07 | 7 |
| 연구실 설정 > 구성원·권한 | E-01 | 0~1 (WU-G4에서 확정) |

**GNB 첫 탭은 `연구실`** (`홈` 아님 — 08-17 개정).

---

## 앱 셸 (WU-P0 FE 조각)

스택은 **TypeScript + React + Vite** — `dev-package/PLAN-SoT.md §9-㊳` 확정.
세부(핀한 버전 · GNB 정본 근거 · 권한 게이트 두 축 · 비워 둔 자리 3곳 · 검증 출력)는
`dev-package/sessions/P0-frontend.md`.

### 명령

```bash
npm ci             # 재현 설치 (node 22 · 의존성 전부 exact 핀)
npm run generate   # contracts/seams/fe-core.yaml → src/generated/fe-core.ts
npm run typecheck  # tsc --noEmit
npm run build      # typecheck + vite build → dist/
npm test           # vitest — 완료 판정 #7 + 권한 게이트 두 축 회귀
npm run dev
```

### 구조

```
src/
  generated/    ← 계약 생성물. 손수정 금지 (CLAUDE.md §3-7) — generated/README.md
  api/          ← 생성 타입 위의 seam 클라이언트 (openapi-fetch)
  permission/   ← 권한 게이트 틀. 두 축을 파일부터 나눈다 (P-14)
                  PermissionGate.tsx = 축 A 숨김(P-12) · LockedContent.tsx = 축 B 노출+요청(P-13)
  placeholders/ ← 비워 둘 자리 3곳. 각 파일 머리에 채우는 WU 를 적어 둔다
  shell/        ← GNB · 레이아웃 · 내비 정의 · 목업에서 옮긴 토큰/CSS
  routes/       ← 화면 자리표시자. 본체는 P1 이후
  app/          ← 라우팅 표 · 세션 부트스트랩
```

**화면 본체를 여기서 만들지 않는다.** 목업에 없는 화면·요소를 발명하지 않는다.
