# colab-v2

수문학 연구 데이터 협업 플랫폼 **CoLAB v2** 모노레포.

> 정본 기획 — 이태헌(lth) 1차 마일스톤 **260818**
> 목표 — **AWS 배포까지, v2 전체 완성**
> 코드 — v2 기준 **신규 구축**. PoC·v1 코드 미계승(도메인 지식·방법론만 참조)

**시작은 `CLAUDE.md §1`** — `dev-package/prd/rounds/` 최신 `R-*.md` 한 개만 읽는다.

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

새 Claude 세션은 `dev-package/prd/rounds/` 최신 `R-*.md` 하나만 읽는다(`CLAUDE.md §1`).

## 하네스 훅

**이 레포를 클론하면 Claude Code 훅 7개가 같이 온다.** `.claude/settings.json` 이 **커밋돼 있기**
때문이고, 그것이 의도다 — 훅이 레포 이력에 있어야 코드와 함께 리뷰·롤백된다(설계 판정 J-9 ·
스펙 `docs/superpowers/specs/2026-09-06-harness-fable51-design.md` C절). 스크립트는
`.claude/hooks/` 에 있고 전부 사람이 읽을 수 있는 bash 다.

| 훅 | 언제 뜨나 | 무엇을 하나 |
|---|---|---|
| `bootstrap-diet.sh` | 세션 시작 | **안내만.** 이번 회차에 읽을 라운드 파일 하나를 찍는다 — 종전 부트스트랩 문서 5개(2.4 MB)를 대체 |
| `worktree-setup.sh` | `lane-worker` 스폰 | **차단 없음.** 새 워크트리의 `node_modules`·서비스 `.venv`·게이트 venv 를 세우고 대장 병합 드라이버를 건다 |
| `git-guard.sh` | Bash 실행 전 | **차단.** ⑴ **레인(서브에이전트)의** main/master push ⑵ main 으로 강제 push ⑶ **HEAD 가 main 일 때 `--ff-only` 없는 `git merge`** ⑷ `gh pr merge` ⑸ `git branch -D main` 다섯 가지만. ⭑ **⑴ 은 `agent_id` 가 실린 호출에만 걸린다** — 오케스트레이터(메인 스레드)의 승인된 `git push origin main` 은 통과한다. 비-main 브랜치의 `merge --ff-only`·**main 에서의 `merge --ff-only`(오케스트레이터의 승인된 병합)**·기능 브랜치 push·`fetch`·`pull` 도 통과 |
| `migration-guard.sh` | Edit·Write 전 | **차단.** `origin/main` 에 **이미 있는** Alembic 마이그레이션 수정. 새 revision 은 통과 |
| `decision-number-guard.sh` | Edit·Write 전 | **차단.** `dev-package/PLAN-SoT.md §9` 에 `origin/main` 최대 + 1 이 아닌 결정 번호 〈N〉 을 새로 쓰는 편집. 기존 번호 인용은 통과 |
| `uncommitted-artifacts.sh` | `researcher` 종료 | **차단.** `dev-package/sessions`·`reports`·`intent` 아래 **미추적 파일**이 남아 있으면 경로를 열거하고 세운다. 자동 커밋은 하지 않는다 — `git add <경로>` 는 사람·에이전트가 직접 한다 |
| `lane-gate-summary.sh` | `lane-worker` 종료 | **차단.** `dev-package/reports/<회차>/<레인>/gate-summary.json` **부재**(＝ 게이트를 안 돌렸다) · **HEAD 와 어긋남**(JSON 의 `commit`·`tree` 가 둘 다 지금 HEAD 와 다르면 옛 회차의 값이므로 부재와 같이 본다) · `counts.red_판정 > 0`. 배출은 `COLAB_GATE_REPORT_DIR` 을 준 `gates/run.sh` 가 한다(`gates/README.md`). ⚠ 이 JSON 은 **추적하지 않는다**(`.gitignore`) — 커밋하면 다음 워크트리가 게이트 없이 통과한다 |

### 전부 끄는 법 — `COLAB_HOOKS=0`

⛔ **세션 안에서 명령 앞에 붙이는 형태(`COLAB_HOOKS=0 git …`)는 듣지 않는다.**
／ 종전 표기 ~~`COLAB_HOOKS=0 <명령>  # 이 한 번만`~~ (⭑ 정정 2026-09-06 · 어드바이저 게이트 ②).
근거 둘 — 공식 hooks 문서 축자 「Leading `VAR=value` assignments are stripped before matching」
· 「A hook process inherits the parent environment」(＝ 훅이 보는 것은 **Claude Code 프로세스의
env** 이지 도구 명령문의 앞머리가 아니다). `git-guard.sh` 자신도 앞머리 `VAR=x` 를 벗기고
판정한다. Edit·Write·SubagentStop 훅에는 「앞에 붙일」 자리 자체가 아예 없다.

**동작하는 형태는 둘이다.**

```bash
# ⑴ 터미널에서 세션을 그렇게 연다 — 그 세션 전체(서브에이전트 포함)
COLAB_HOOKS=0 claude
export COLAB_HOOKS=0 && claude      # 이 셸에서 뜨는 모든 세션
```

```jsonc
// ⑵ .claude/settings.local.json — 이 기계·이 프로젝트만 (커밋되지 않는다)
{ "env": { "COLAB_HOOKS": "0" } }
```

⑵ 의 `env` 는 설정 문서의 정규 키다 — 축자 「Set environment variables for every session and
its subprocesses」 · 적용 범위 「Any file」(`.claude/settings.local.json` 포함). 훅 프로세스가
바로 그 subprocess 다.

모든 훅 스크립트의 **첫 줄**이 이 값을 보고 즉시 통과한다. 차단 훅이 오탐을 내면 우회 경로를
찾지 말고 이것을 쓰고, **그 오탐을 결함으로 보고한다** — 훅을 손으로 고쳐 두면 다음 클론이
같은 자리에서 다시 걸린다.

### 개인별로만 끄는 법

`.claude/settings.local.json` 은 **커밋되지 않는다**(gitignore). 훅 항목은 층 간 **병합**되므로
`.claude/settings.json` 의 공유 훅은 그대로 두고 개인 훅만 여기에 더한다. 공유 훅 자체를 자기
기계에서만 쉬게 하려면 같은 파일의 `"env": {"COLAB_HOOKS": "0"}` 이나 셸 프로파일의
`export COLAB_HOOKS=0` 을 쓴다 — 훅 스크립트를 고치면 diff 가 남아 다음 병합에서 되돌아온다.

> 훅은 **마찰 장치이지 보안 경계가 아니다.** 한 겹 감싼 명령(`bash -c "…"`)은 잡지 않는다.
> 잡으려고 문자열 어디에나 있는 `git` 을 세면 무해한 호출이 걸리고, 오탐이 붙은 차단 훅은
> 곧 상시 비활성으로 끝난다.
