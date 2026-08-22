# REPO — 저장소 구성

> 시작점: `CognileapAI/colab-dev-package`. 기존 구성을 바꿔도 좋다는 전제(Ted, 2026-08-22) 아래 **v2 기준으로 다시 설계**한다.

---

## 1. 권고 — 단일 모노레포

**`colab-v2` 하나.** `colab-dev-package`를 이 레포로 승격하거나(내용 보존), 신규 생성 후 dev-package 문서를 이관한다.

```
colab-v2/
├─ dev-package/            오케스트레이션 SSoT (이 폴더의 문서들)
│   ├─ 00-START-HERE.md  01-CLAUDE-DRIVER.md  02-DEV-PLAYBOOK.md  03-HANDOFF.md
│   ├─ DOMAINS.md  WORK-UNITS.md  PLAN-SoT.md  REPO.md
│   └─ sessions/
├─ contracts/              계약 권위체 (SSoT)
│   ├─ seams/               FE↔core · core↔viz · core↔ai  (OpenAPI, 손작성)
│   ├─ events/              core↔pipeline 이벤트 봉투 (JSON-Schema)
│   ├─ schemas/             공통 모델 — 정규 ID 타입 등
│   └─ codegen/             → 백엔드 모델 · FE 타입/클라이언트
├─ services/
│   ├─ core-api/            D1 D2 D3 D4 D6 D8    ※ geo 라이브러리 금지
│   ├─ pipeline-worker/     D5
│   ├─ viz-render/          D7
│   └─ ai-service/          D9 D10               ※ 별도 스키마·별도 마이그레이션 head
├─ frontend/                생성 타입만 소비
├─ db/                      선언 스키마 SoT (플랫폼 / AI 분리)
├─ infra/                   IaC — AWS 전량. 콘솔 수작업 0
├─ gates/                   계약·경계·스키마·RLS 게이트 + self-test
├─ eval/                    AI 평가셋 (계보 제안 · 검색)
├─ CODEOWNERS
└─ .github/workflows/
```

## 2. 왜 모노레포인가 — 도메인 분할 기준으로 검증

`DOMAINS.md §1`의 두 기준에 그대로 대면 답이 나온다.

### 기준 A · 협업 — 레포로 가를 필요가 없다

경계는 **손이 바뀌는 지점**에 필요하고, 그 경계는 이미 `contracts/`가 담당한다. 소유는 **디렉터리 + CODEOWNERS**로 충분히 갈린다.

| 소유 집단 | 소유 경로 |
|---|---|
| 수문학 도메인 | `services/ai-service/ontology/` · `eval/` |
| 플랫폼 개발 | `services/core-api/` · `db/platform/` |
| AI 엔지니어링 | `services/ai-service/` · `eval/` |
| 프론트엔드 | `frontend/` |
| 계약 권위 | `contracts/` — **변경 시 필수 리뷰** |

레포를 나눈다고 소유가 더 분명해지지 않는다. CODEOWNERS가 하는 일을 레포 경계가 대신할 뿐이고, 대신 동기화 비용이 붙는다.

### 기준 B · 개발 최적화 — 멀티레포가 이점을 없앤다

AI 개발의 이점은 **조율 비용 ≈ 0**이다. 멀티레포는 그 이점을 정확히 무효화한다.

| | 모노레포 | 멀티레포 |
|---|---|---|
| 계약 변경 → 생산자 → 소비자 | **한 커밋**에서 원자적으로. 게이트가 즉시 판정 | N개 PR + 머지 순서 조율 + 버전 핀 |
| 에이전트 컨텍스트 | 계약·구현·테스트가 한 워크스페이스 | 레포 간 왕복. 컨텍스트가 갈라짐 |
| 리팩터 (도메인 경계 조정) | 한 번에 | 사실상 불가 |
| 드리프트 | 게이트가 같은 CI에서 잡음 | **핀 지연 = 구조적 드리프트원** |

### v1이 남긴 실증

v1은 4 repo로 갔고, 그 대가를 실제로 치렀다.

- 패키지 레지스트리에 pip 피드가 없어 **vendored-pin 우회**를 만들어야 했다
- cross-repo dispatch를 위해 **org 토큰**을 따로 심어야 했다
- `can-i-deploy` 게이트라는 **배포 의식**이 필요했다 — 그런데 실제 서비스 경계는 몇 개뿐이었다
- 계약 스냅샷이 각 레포에 복제돼 "손편집 금지" 규칙을 또 만들어야 했다

**그중 어느 것도 제품 가치를 만들지 않았다.** 전부 레포를 나눠서 생긴 비용이다.

> 계약 SSoT는 레포 분리로 지키는 것이 아니라 **게이트로 지킨다.** `contracts/` 변경 필수 리뷰 + 생성물 최신성 검사 + 파괴적 변경 탐지면 충분하고, 그게 실제로 작동하는 방식이다.

## 3. 모노레포지만 배포는 독립

한 레포에 있다고 한 덩어리로 배포하지 않는다. **변경 경로 필터**로 영향받은 배포 단위만 빌드·배포한다.

| 변경 경로 | 재빌드·재배포 |
|---|---|
| `contracts/**` | 코드젠 → **전체** 검증 (드리프트 탐지 지점) |
| `services/core-api/**` | core-api |
| `services/pipeline-worker/**` | pipeline-worker |
| `services/viz-render/**` | viz-render |
| `services/ai-service/**` | ai-service |
| `frontend/**` | frontend |
| `infra/**` | IaC plan → 승인 후 apply |

## 4. 레포를 쪼갤 조건 (지금은 아님)

아래 중 하나가 실제로 발생하면 그때 쪼갠다. 미리 쪼개지 않는다.

- 배포 단위별 **릴리스 주기가 실제로 갈릴 때**
- **외부 협력사**가 한 서비스만 만져야 할 때 (접근 범위 제한이 필요)
- 한 서비스가 **다른 조직 소유**로 이관될 때

## 5. 기존 레포 처분

| 레포 | 처분 |
|---|---|
| `colab-dev-package` | **v2 모노레포로 승격** (권고) — 또는 문서만 남기고 `colab-v2` 신설 후 이관 |
| `colab-contracts` | v1 자산. **archive** (읽기 전용 참조) |
| `colab-backend-platform` | v1 자산. **archive** |
| `colab-frontend` | v1 자산. **archive** |
| `colab-infra` | v1 자산. **archive** — IaC는 v2에서 다시 저작 |

> 코드를 계승하지 않으므로(`PLAN-SoT §1.1`) 기존 레포는 삭제가 아니라 **동결**한다. `C4`(방법론 추출)가 게이트 구성 방식을 뽑아낼 때까지 살아 있어야 한다.

## 6. 로컬 배치

`<작업공간>` = 이 레포 폴더의 **부모**. 형제로 나란히 둔다.

```
<작업공간>/
├─ 30 CoLAB-v2/      ← colab-v2 클론 위치 (이 레포)
├─ 20 CoLAB-v1/      ← v1 참조 (동결, 읽기 전용)
├─ 01 CoLAB-Plan/    ← 260808 기획 캐시 (인덱스 5종 — WU-G7 입력)
└─ 40 COLAB-기획/    ← **기획 정본** (`planning/README §1` · `PLAN-SoT §9-㉕`)
```

로컬 폴더 이름과 레포 이름이 달라도 된다. **문서에 절대경로를 적지 않는다** — v1의 HANDOFF가 이 규칙이 없어 실제로 틀렸다. 이 절도 2026-08-22 까지 그 규칙을 어기고 있었다.

## 7. 초기 설정 체크리스트 (WU-R1)

- [ ] 레포 결정 — `colab-dev-package` 승격 vs `colab-v2` 신설 *(Ted 확정 필요)*
- [ ] 디렉터리 스캐폴드 + `CODEOWNERS`
- [ ] `main` 보호 — force-push·삭제 차단. 리뷰 필수는 협업자 합류 시
- [ ] CI 실행 환경 확보 (v1에서 결제 문제로 self-hosted 우회했던 지점 — 반복하지 않는다)
- [ ] 변경 경로 필터 워크플로 골격
- [ ] `dev-package/` 문서 이관 + `03-HANDOFF` 갱신
