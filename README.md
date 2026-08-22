# colab-v2

수문학 연구 데이터 협업 플랫폼 **CoLAB v2** 모노레포.

> 정본 기획 — 이태헌(lth) 1차 마일스톤 **260818**
> 목표 — **AWS 배포까지, v2 전체 완성**
> 코드 — v2 기준 **신규 구축**. PoC·v1 코드 미계승(도메인 지식·방법론만 참조)

**시작은 [`dev-package/00-START-HERE.md`](dev-package/00-START-HERE.md).**

---

## 구조

```
colab-v2/
├─ dev-package/          오케스트레이션 SSoT — 여기부터 읽는다
├─ contracts/            계약 권위체 (SSoT). seam · 이벤트 봉투 · 공통 스키마 · 코드젠
├─ services/
│   ├─ core-api/          D1 D2 D3 D4 D6 D8   ※ geo 라이브러리 금지
│   ├─ pipeline-worker/   D5
│   ├─ viz-render/        D7
│   └─ ai-service/        D9 D10              ※ 별도 스키마 · 별도 마이그레이션 head
├─ frontend/             생성 타입만 소비
├─ db/                   선언 스키마 SoT — platform / ai 분리
├─ gates/                계약 · 경계 · 스키마 · RLS 게이트 + self-test
├─ eval/                 AI 평가셋 (계보 제안 · 검색)
├─ infra/                IaC — AWS 전량. 콘솔 수작업 0
└─ planning/             기획 정본 위치 안내 (문서 사본은 두지 않는다)
```

## 도메인 10개

| 레이어 | 도메인 | 소유 |
|---|---|---|
| 지식 | **D9** Ontology & Knowledge Graph | 수문학 도메인 |
| 추론 | **D10** AI Services — 제안만 하고 기록하지 않는다 | AI 엔지니어링 |
| 기록 | **D1** Identity & Lab · **D2** Access & Policy · **D3** Catalog · **D4** Lineage · **D5** Ingestion & Pipeline · **D6** Project · **D7** Visualization · **D8** Insight | 플랫폼 개발 |

경계와 분할 기준 → [`dev-package/DOMAINS.md`](dev-package/DOMAINS.md)

## 불변 규칙

1. **도메인은 자기 테이블 + D1(shared kernel)만 참조한다.** 타 도메인 테이블 직접 FK·접근 금지 — import 경계 검사로 강제
2. **D10 → D4(Lineage) 쓰기 경로가 존재하지 않는다.** AI는 제안만 하고, 사람이 확인한 것만 커밋된다 — 음성 테스트로 강제
3. **D9·D10 저장소는 D1~D8과 마이그레이션 체인이 분리된다**
4. **core-api에 geo 라이브러리를 import하지 않는다** — banned-import 게이트
5. **모든 조회에 연구실 경계가 자동 주입된다** — 스코프 커널 + RLS + cross-tenant 음성 테스트
6. **정규 ID 타입은 `contracts/schemas/`에서만 정의된다**
7. **생성된 타입·클라이언트를 손으로 고치지 않는다**
8. **문서에 절대경로를 적지 않는다**

## 진행

주차 일정이 아니라 **작업 단위(WU)** 로 센다 → [`dev-package/WORK-UNITS.md`](dev-package/WORK-UNITS.md)
현재 상태 → [`dev-package/03-HANDOFF.md`](dev-package/03-HANDOFF.md)

## 개발 세션 시작

새 Claude 세션에 [`dev-package/01-CLAUDE-DRIVER.md`](dev-package/01-CLAUDE-DRIVER.md) 의 킥오프 프롬프트를 붙여넣는다.
