---
name: design-review
description: 현재 프론트 디자인을 정본(토큰·패턴·apple-design 원칙)에 대조해 판정표로 정리하고, 승인된 것만 고친다. 「시스템 디자인 정리」·「디자인 검토」·「디자인 검수」·「/design-review」 처럼 명시적으로 요구할 때만 쓴다 — 레포·화면에 대한 일반 질문에는 발동하지 않는다.
---

# design-review — 현재 시스템 디자인 정리

프론트(`frontend/src/`)의 디자인 상태를 **재고 → 판정하고 → 승인된 것만 고친다.** 세 단계는 분리돼 있고 순서를 건너뛰지 않는다. 판정 없이 고친 선례가 0건이어야 이 스킬이 산 것이다(WU-A11 → WU-B11 이 세운 규율: 「없는 결함을 고치지 않는다」·「판정 없이 고치지 않는다」).

이 스킬은 `colab-v2-work` 의 규율(위임·레인·게이트·보고 문체) 위에서 돈다. 먼저 그것을 부른다.

## 0. 정본 — 무엇에 맞추나

| 축 | 정본 | 비고 |
|---|---|---|
| 토큰 | `frontend/src/shell/tokens.css` | v2 의 유일한 토큰 정본. `01 CoLAB-Plan/planning-base/design-tokens/tokens.md` 는 Figma 미동기화 빈 템플릿이라 정본이 아니다 |
| 정적 합격선 | `dev-package/sessions/p3-design-audit-20260905.md` 판정 11항목 ＋ 접근성 = 대비 **4.5:1**(AA) · 글자 **13px 이상** · 미정의 토큰 0 · 음수 여백 0 · 카드 그림자 0(팝오버 허용) · 보더 2층 토큰 분리 · 여백은 컨테이너 소유 | 측정 방식은 그 문서와 동일(WCAG 상대휘도 · `path:line` · 실측값) |
| 인터랙션·모션 | `.claude/skills/apple-design/SKILL.md` | 응답(pointer-down 피드백) · 1:1 추적 · 중단 가능 전환 · 스프링/속도 계승 · 재질·깊이 · 타이포(tracking·leading) · **reduced-motion** · 절제 |
| 목업 참고 | `01 CoLAB-Plan/design/`(`component-library.html` · `patterns/*.md` · `styles/design-system.css`) | v1 목업의 `ds-` 어휘. **v2 정본이 아니다** — 의도를 읽는 참고자료로만 쓴다. 코랄 액센트 `--color-accent-*` 정본은 여기에 없다(0건 실측 2026-09-08) → `40 COLAB-기획/00_기획원본` 이 후보지 |
| 이월·판정 대기 | 직전 audit/fix 산출물의 §「하지 않은 것」·§「후속」 ＋ 그것을 집행한 WU 의 커밋 메시지 | 실행 전에 **집행 WU 가 있었는지 `git log` 로 먼저 확인**한다. 선례 = `p3-design-fix-20260908.md` 의 이월 7건은 WU-C11(`2c4d335`)이 집행했으므로 재판정 기준은 「집행 후 잔존 여부」다. 「전에 열려 있었다」는 최근 값이 아니다 |

정본끼리 어긋나면 **멈추고 Ted 판정 항목으로 올린다.** 임의로 한쪽을 고르지 않는다.

## 1. 모드 — 무엇을 요구받았나

| 모드 | 트리거 | 산출 | 코드 변경 |
|---|---|---|---|
| `audit`(기본) | 「정리해」·「검토해」·「검수해」 | 판정표 1건 `dev-package/sessions/design-review-<YYYYMMDD>.md` ＋ Ted 판정 묶음 ＋ R-C 후보 WU 목록 | **0건** |
| `fix` | 「고쳐」＋ 판정표 지목 · 또는 Ted 가 판정표의 항목을 승인한 뒤 | 레인별 CSS/TSX 수정 ＋ 시험 ＋ 게이트 green | 승인된 「있음」 항목만 |

`fix` 는 **`audit` 산출물이 커밋돼 있어야** 시작한다. 판정표 없는 `fix` 요청은 `audit` 부터 돈다고 알리고 그렇게 한다.

## 2. audit — 에이전트 구조

메인 세션은 범위 확정·취합·판정 대기 묶음만 한다. 파일을 읽어 재는 일은 전부 `researcher` 로 격리한다.

### 2-1. 범위 확정 (메인 · 직접)

```bash
git ls-files 'frontend/src/**/*.css'                       # CSS 전수(현재 16종)
grep -rlE 'transition|animation|@keyframes|onPointer|onDrag|onTouch' frontend/src --include='*.tsx' --include='*.css'
python3 .claude/skills/design-review/scripts/css_audit.py --root frontend/src --md dev-package/reports/design-review/<YYYYMMDD>/css_audit.md
```

`css_audit.py` 가 정적 계측 6축(13px 미만 · 음수 여백 · 미정의 토큰 · box-shadow · 모션 선언 vs reduced-motion · 같은 규칙 안 색 대비)을 **먼저 기계로 잰다.** 서브에이전트는 이 표를 받아 「사람 판정이 필요한 것」만 본다 — 기계가 센 숫자를 손으로 다시 세지 않는다.

레인은 **파일 면이 겹치지 않게** 나눈다. 기본 분할 3레인 —
- **L1 셸·공통** = `shell/`·`components/common/`·`auth/`·`components/dashboard/`
- **L2 카탈로그·검색·상세·미리보기** = `components/catalog/`·`search/`·`detail/`·`preview/`
- **L3 업로드·계보·프로젝트·랩·멤버** = `components/upload/`·`lineage/`·`project/`·`lab/`·`members/`
- **L4 인터랙션(선택)** = 모션·제스처가 있는 `.tsx`·`.css` 만 — apple-design 축 전담. 대상 파일이 5개 미만이면 L1 에 합친다.

레인이 3개 이상이면 **advisor ①** 에 분할·지시문을 먼저 보인다.

### 2-2. researcher 지시문 (레인마다 · 새 세션)

지시문에 반드시 넣는 것 —
1. 대상 파일 목록(앵커 = 경로. 행 번호로 위치를 지정하지 않는다).
2. 읽을 정본 = §0 표의 경로 그대로 ＋ `css_audit.md` 경로.
3. 판정표 형식(§2-3) 과 세 값 = **있음 / 없음 / [미상]**. 근거는 `path:line` ＋ 실측값. 대비는 WCAG 상대휘도로 계산해 `n.nn:1` 로 적는다.
4. apple-design 축은 **코드에서 확인 가능한 것만** 판정한다 — `:active` 피드백 유무 · `transition` 의 중단 가능성(`transition` vs `animation` 고정 길이) · `prefers-reduced-motion` 분기 · 고정 `letter-spacing` · `backdrop-filter` 사용처(열거만 · 「재질·깊이」의 정적 합격선은 없으므로 판정하지 않는다). 실화면이 필요한 항목(스프링 느낌·속도 계승)은 `[미상 · 실화면 계측 필요]` 로 적고 판단하지 않는다.
5. **CSS·TSX 를 한 자도 고치지 않는다.** 쓰기는 `dev-package/sessions/design-review-<YYYYMMDD>-L<n>.md` 한 파일.
6. 「지시가 실물과 어긋나면 멈추고 보고하라」. 정본끼리 충돌하면 「판정 대기」로 적는다.
7. 커밋은 **메인이 순차로** 한다(같은 워크트리에서 레인 n개가 동시에 커밋하면 `index.lock` 경합). 레인은 파일만 쓰고 경로를 돌려준다.
8. 스크립트 값을 그대로 믿지 않는다 — 채택하는 행마다 실물 규칙을 열어 확인하고, 오탐은 산출 파일의 소절 「css_audit 오탐」에 적는다. 스크립트는 같은 규칙 안의 색쌍만 재므로 **상속 색쌍(부모 배경 위 자식 글자)은 사람이 계산**한다.
9. 「파일 내 토큰 정의」 축은 둘로 가른다 — ⓐ 컴포넌트 전용 변수(접두사가 그 화면 고유 · `--pv-*`·`--toast-*` 류) = 없음 / ⓑ 전역 어휘(`--color-*`·`--radius-*`·`--space-*`)를 파일마다 복제 = Ted 판정(`tokens.css` 승격 여부). 이 구분 없이 판정하지 않는다.

모델 = `researcher`(sonnet). L4 인터랙션 레인만 판단이 무거우면 `model: opus` 로 올린다.

### 2-3. 판정표 형식 (레인 산출 · 메인 취합 공통)

```
| # | 축 | 항목 | 판정 | 근거 path:line · 실측값 | 처리 |
|---|---|---|---|---|---|
| 1 | 정적 | catalog.css .lin--none 대비 | 있음 | catalog.css:135 #848c94 on #fff → 3.41:1 | Ted 판정 |
| 2 | 모션 | 확장보기 오버레이 reduced-motion 분기 | 없음 | detail.css:… @media (prefers-reduced-motion) 존재 | — |
| 3 | 모션 | 드래그 속도 계승 | [미상] | 코드에서 판정 불가 | 실화면 계측 |
```

「처리」 값은 넷 = **즉시 수정 후보**(정본이 명확 · 값 하나로 닫힘) / **Ted 판정**(정본 부재·충돌·색 선택) / **실화면 계측**(정적으로 못 잰다) / **—**(없음).

### 2-4. 취합 (메인)

- 레인 산출 n건을 `dev-package/sessions/design-review-<YYYYMMDD>.md` 로 합친다 — 표 하나 · 축별 소계 · **Ted 판정 묶음**(각 건에 ⓐ/ⓑ 선택지와 권고 1개 · 내부 약어 풀어서) · **R-C 후보 WU 목록**(즉시 수정 후보를 레인 단위로 묶은 것).
- 이월 항목(§0 마지막 행)은 이번 표에 **다시 실어** 현재 값으로 재판정한다. 「전에 열려 있었다」는 최근 값이 아니다.
- **advisor ②** 에 판정표를 보인다(approve / approve-with-changes / reject). 반영 내용은 표 아래 「advisor ② 반영」 절에 적는다.
- 산출은 회수 즉시 커밋. `PLAN-SoT §9` 등재문 초안은 문서 끝에 두고 〈N〉 은 병합 직전 재실측한다.

## 3. fix — 에이전트 구조

- 입력 = 커밋된 판정표 ＋ 승인 범위(Ted 판정 결과 또는 「즉시 수정 후보」 명시 지목). **범위 밖은 건드리지 않는다.**
- 레인 = `lane-worker`(`isolation: worktree`) · 파일 면이 겹치지 않게 audit 과 같은 분할. 각 레인은 RED → GREEN 순서(`frontend/test/design-fix-<YYYYMMDD>.test.ts` 유형 · 선례 `frontend/test/design-fix-20260908.test.ts`) 로 시험을 먼저 세운다.
- 레인 완료 조건 = `gate-runner` 로 `frontend-typecheck`·`frontend-test`·`frontend-fixture-reach` green. 판정은 `-j 1` 로 재현한 값만 쓴다.
- 레인 산출 = `dev-package/sessions/design-fix-<YYYYMMDD>-L<n>.md`(before → after 표 · 수용 기준 · 「하지 않은 것」 · 부수 간격 변화).
- 병합 전 **advisor ③**(사용자 노출 변경 go/no-go). 병합·〈N〉 발급은 오케스트레이터만.
- TSX 구조 변경이 필요한 항목(예: `LockedContent.tsx` 클래스 부여)은 CSS 레인에 섞지 않고 별도 레인 또는 R-C WU 로 뺀다.

## 4. 하지 않는 것

- 정본 없는 값을 짓지 않는다 — 액센트 hex · Lv3 칩 색 · 새 토큰 이름은 Ted 판정 뒤에만 세운다.
- 13px 미만 전수 일괄 승격처럼 **판정표에 지목되지 않은 자리**를 고치지 않는다.
- 실화면이 필요한 판정을 정적 근거로 대신하지 않는다. `[미상]` 은 결함이 아니라 값이다.
- staging·dev 환경에 접촉하지 않는다(실화면 계측은 별도 배포 창 뒤의 일이다).

## 5. 완료 보고

개조식 · 실측 지도(`rules §5-5`). 판정 소계(있음/없음/미상) · Ted 판정 건수 · R-C 후보 WU 수 · 산출 경로 · 커밋 SHA. `fix` 면 게이트 3계수와 시험 수(전/후)를 더한다.

Before reporting, check each claim against this session's tool results.
