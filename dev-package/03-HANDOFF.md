# 03 · HANDOFF — 진행 상태 추적기 (단일 진실원)

> **이 문서가 "지금 어디까지 왔는가"의 진실원.** 매 세션 끝에 갱신한다(규약 `01-CLAUDE-DRIVER.md §C`).
> 새 세션은 여기부터 읽는다. 코드·인프라와 모순되면 실제 상태를 점검해 **이 문서를 먼저 바로잡는다.**

**최종 갱신** 2026-08-23 (**밤샘 세션 WU 8개 닫힘** + **결정 `㊻` — AWS 보류, 완주 판정을 staging 까지로 내림**)
**현재 단계** **T-G 전부 닫힘 · T-D 전부 닫힘(D1 D2 D2b D3 D3b) · P0 ✅ · I2 ✅** · 게이트 **13종 중 12종 구현**(`generated-up-to-date` 만 미구현 — 설계대로 red), 자기 증명 **139 케이스** green · **staging 에 5개 배포 단위 + postgres 2체인이 실제로 서 있다**(`www.colab-hydro.com`)
**다음 WU** → **P1**(카탈로그 S-03 + 상세 헤더 + `연구실 설정 > 구성원·권한`). 진입조건 P0 충족. **I2 를 지났으므로 이제부터 각 WU 의 완료 판정에 `staging 배포 green` 이 붙는다.** 병렬 착수 가능 = **I3**(배포 자동화) · `generated-up-to-date` 게이트 · **IS4 잔여**. **K3·K4 는 키 투입으로 차단 해제됐다.**
／ **Ted 비토 대기 (기본은 그대로 간다)**: `㉝` 스토리 6개 상한 폐기(정본 내용 변경) · `㉟` 표기 규약 · `㊱` 잠김 200·경계 404·권한 403 · `㊲` 멱등 키 둘 · `㊳` 기술 스택 · **`㊸-④-3` D9 시드 배치(④-4 함의로 확정 — 명시 답변 아님)**. **PLAN 이탈 1건**(`§5`)
／ **Ted 가 줄 것**: **IS2 apply 용 Cloudflare API 토큰**(`Account → Cloudflare Tunnel : Edit`) · 터널 ID 히스토리 처리(`§4-8`). **OpenAI API 키는 투입 완료 — K3·K4 차단 해제**
／ **⏸ 보류 — 열지 않기로 한 것**: **AWS 계정 (I0·I1·I5, prod 전용)**. `㊻`(2026-08-23 Ted) — **v2 완주 판정은 `staging 배포 green` 까지로 내렸다.** prod 는 ① staging 에서 v2 전체가 충분히 동작하고 ② Ted 가 **출시를 결정**했을 때 연다. **더 이상 블로커가 아니다 — 대기가 아니라 결정이다.**
／ Claude 착수 가능: **P1** · **I3** 배포 자동화 · `generated-up-to-date` 게이트 · **IS4 잔여**(마지막 apply · 맨몸 호스트 조건)
／ **T-C(C1~C4)는 v1 정리 트랙이므로 지금 열지 않는다** — C3는 P2·D5, C4는 D3에 가서야 입력이 된다

---

## 1. 진행도

표기 — ✅ 닫힘 · 🟦 진행 · ⬜ 대기 · 🟧 부분(사유 필수) · ⛔ 차단(무엇이 막는지)

### T-R 저장소
| WU | 상태 | 비고 |
|---|---|---|
| R0 레포 결정 | ✅ | **`colab-v2` 신규 모노레포** (Ted, 2026-08-22). `colab-dev-package`는 v1 자산으로 archive |
| R1 스캐폴드 + CI 골격 | ✅ | 원격 `CognileapAI/colab-v2`(public) push 완료 · `main` 보호(force-push·삭제 차단, 리뷰 필수 없음) · CI 1회 완주 — 게이트 잡(`contract-gates` 등) 전부 "미구현 — red"로 **설계대로** 실패. 가시성 결정 = `PLAN-SoT §9-⑯` |
| R2 v1 레포 5종 archive | ⬜ | C4 후 (`colab-dev-package` 포함) |

### T-C 정리
| WU | 상태 | 비고 |
|---|---|---|
| C1 5 repo 푸시 확인 | ⬜ | 이관의 차단 조건 |
| C2 v1 이관 (`20 CoLAB-v1`) | ⬜ | C1 후 |
| C3 PoC 지식 추출 `HARVEST.md` | ⬜ | 4포맷·좌표계·COG·실패 목록 |
| C4 v1 방법론 추출 `METHOD.md` | ⬜ | 계약 게이트 6종 구성 방식 |

### T-I 인프라 (**staging 배포가 완료 조건** — prod 는 `§9-㊻` 로 보류)

> **staging = WSL+Cloudflare Tunnel 호스트 재사용 · prod = AWS** *(2026-08-22 Ted, `PLAN-SoT §9-㉓`)*.
> **PoC 스택은 2026-08-22 철거됐다** — 컨테이너·볼륨·데이터 전부. `colab-hydro.com` 은 현재 **530**(오리진 없음).
> **Cloudflare 터널·DNS 는 살아 있다.** 즉 staging 은 새로 만드는 게 아니라 **빈 터널에 오리진을 붙이는 일**이다.
> 기록과 컷오버 준비물은 `DEPLOY-CURRENT.md`. **AWS에는 아무것도 없다**(`~/.aws` 미설정).

| WU | 상태 | 비고 |
|---|---|---|
| I0 계정·결제·리전·예산 알람 | ⏸ | **보류 — 출시 결정 대기** (`㊻`). staging 은 IS1 이 대신한다. ⬜ 가 아닌 이유 = ⬜ 는 "곧 할 것"으로 읽혀 매 세션 착수 후보에 오른다 |
| **IS1 staging 호스트 구성** | ✅ | 기존 터널에 v2 오리진 재부착. 산출 `infra/staging/` — nginx + cloudflared **둘뿐**(데이터 저장소 없음), 호스트 노출은 `127.0.0.1:3000` 만(PoC 의 `0.0.0.0` 반복 회피). **롤백 왕복 증명 200→530→200.** 현재 `colab-hydro.com` = v2 staging 자리표시(중립 안내 + `/healthz`). 토큰은 레포 밖 홈 `0600` 파일. **커넥터 로그가 원격 ingress 정본을 노출했다 — `www.colab-hydro.com → http://nginx:80`** (그래서 서비스명을 `nginx` 로 고정) |
| **IS2 터널 라우팅 IaC화** | ✅ | **완료 판정 증명됨 — `terraform plan` = `No changes.`** 레포 선언이 실제 상태와 일치한다. 즉 **대시보드가 정본이 아니라 레포가 정본이고 대시보드가 그 산출**이다. 산출 `infra/staging/tunnel/`(versions·variables·tunnel.tf·tfvars.example·.gitignore·README). ingress 선언 = `www→nginx:80` + catch-all 404 **둘뿐이고 ssh 규칙 없음**(`§9-㉜`) — 없는 이유를 파일 주석에 남겼다. 비밀은 전부 변수(default 없음)이고 `.gitignore` 가 `*.tfvars`·상태파일 차단(`git check-ignore` 확인). 실행 기록 — `init → import → plan → apply`(`0 add, 1 change, 0 destroy`, destroy/replace 0건) → `www/healthz` **200 무중단** → 커넥터가 `version=7` 로 새 ingress 수신. **블로커 #7 은 세 겹이었다**(ingress · Access 앱 · DNS CNAME) — 셋 다 제거, `ssh.colab-hydro.com` 은 이제 **DNS 미해석**. terraform 은 `~/.local/bin` 에 사용자 수준 설치(sudo·apt 저장소 불필요, 파일 삭제로 원복). **한계 = state 가 이 호스트 로컬에만 있다**(레포에 커밋하지 않는다 — 비밀 포함). 호스트가 사라지면 재import 로 복구해야 한다 → **IS4 로 세웠다**. 터널은 **원격 관리형**(토큰만 · ingress 를 Cloudflare 가 push, 커넥터 로그 `version=6` 으로 확증). 3안 비교 후 **Terraform `cloudflare_zero_trust_tunnel_cloudflared_config`** 채택 — 무중단이고 `terraform plan` 이 "레포에서 재적용해 동일 상태 재현"을 그대로 만족시킨다. `.tf` 초안·apply/verify/rollback 시퀀스 = `sessions/IS2.md`(아직 `infra/` 에 배치하지 않았다). 블로커 #7 은 `§9-㉜` 로 **삭제 확정** — IS2 선언에서 빼면 apply 시 사라진다 |
| IS3 staging 백업 체계 | ✅ | **2026-08-23 닫힘 — 실 staging 대상.** 백업 1회(두 체인) · **복원 1회**(일회용 인스턴스, 테이블·행 수·내용 md5 대조 일치, K2 시드 22행 별도 확인) · **fail-closed fixture 11건 전부 red**. F2 가 핵심 — **빈 gzip 20B 는 `gzip -t` 를 통과한다**(PoC 가드가 통과시킨 그 파일). I2 가 넘긴 설정으로는 platform 만 덮여 부분 성공이 났고, 프로파일별 합격선으로 고친 뒤 **F9 로 박았다**. 스케줄 설치. **정직한 한계 = 실패가 「가서 봐야 보이는」 자리에만 남는다** — push 알림 채널이 없어 침묵 창이 0 이 된 것이 아니라 8주 → 최대 1주로 잘렸다. 산출 `sessions/IS3.md` |
| **IS4 terraform state 보관** | 🟧 | **2026-08-23 — 절차는 섰고 리허설도 돌렸다.** scratch 에 `.tf` 만 복사해 빈 state 로 `init → import → plan`(실자격증명). 원본 state md5 동일 · 실디렉터리 `plan` = `No changes.` · staging 내내 200. 산출 `sessions/IS4.md` · `infra/staging/tunnel/README §5-1`. **미달 2건 = ① 마지막 `apply` 미실행**(실 터널을 건드린다) **② 맨몸 호스트 조건**(terraform 미설치·자격증명 파일 없음) 미실험. 원격 백엔드(S3+DynamoDB)는 **I0 대기** |
| I1 토폴로지 + IaC (`plan`까지) | ⏸ | I0 후 — **보류** (`㊻`) |
| **I2 walking skeleton 배포** | ✅ | **2026-08-23 — 분수령 통과.** 5개 단위 전부 헬스 green(`/healthz/{core-api,frontend,pipeline-worker,viz-render,ai-service}`), 컨테이너 7/7 healthy, 호스트 노출 `127.0.0.1` 하나뿐 **`0.0.0.0` 0건**. **롤백 증명에서 방법을 고쳤다 — 상태 코드만으로는 판정할 수 없다**(자리표시가 모든 경로에 200 을 준다). 본문까지 대조했다: `<!doctype html>` ↔ `{"unit":"core-api"}` · `/api/v1/me` 200↔401. 배포→롤백→재배포 4구간 **530 없이 무중단**. postgres 2체인 분리 유지(`colab_platform` 20표 · `colab_ai` 시드 22행). 앱 롤 staging 실측 `rolsuper=f·rolbypassrls=f·소유 0` — P0 숫자와 동일. 터널 선언 무수정(`plan` = No changes). 산출 `sessions/I2.md` |
| I3 배포 자동화 | ⬜ | |
| I4 운영 준비 (추적·알람·복구 리허설) | ⬜ | |
| I5 prod 전환 | ⏸ | I4 + P7 — **보류** (`㊻`). v2 개발의 종점은 여기가 아니라 **staging 전체 green** 이다 |

### T-G 게이트
| WU | 상태 | 비고 |
|---|---|---|
| G1 패키지 신선도 게이트 | ✅ | **재빌드는 필요 없었다** — 15개 임베드 블록이 8개 에픽 전부에서 원본과 일치(sha256). 낡은 것은 *내용*이 아니라 "미반영"이라 적어둔 **서술**이었다. 산출 = `tools/check-package-freshness.py` · `planning-freshness` 게이트 · `PACKAGE-FRESHNESS.md` · `planning/README §3` 정정. **오라클은 content-hash 전용** — 파일명(`260817`)과 mtime이 둘 다 거짓말을 한다. selftest가 변조 fixture + 미마운트 둘 다 red 로 fail-closed 증명. 남은 것 = 정본 `E-00 README §4` 의 낡은 서술(Ted 판단, `sessions/G1.md` R3) |
| G1b E-04·E-02 패키지 재빌드 | ⬜ | **문서 임베드는 이미 일치**(G1 게이트가 매일 지킨다). 남은 것은 **목업·화면** 최신성뿐 — `planning-freshness` 는 이걸 판정하지 않는다 |
| G2 자연어 검색 엔진 | ✅ | **해소 (2026-08-23, `§9-㊶`)** — Postgres 단독(tsvector+pgvector). P4·K4 차단 해제 |
| G3 E-01 권한 원칙/적용표 분리 | ✅ | **원칙 문서 초안 완료** — 산출 `PERMISSION-PRINCIPLES.md`(P-1~P-34). 정본이 열어둔 9건 중 **4건을 이번 세션에 닫았다**(`§9-㉖㉗㉘㉙` — 잠금 시행 위치 · 접근 상태 기본값 · 감사 기록 · 재위임 금지). **G7 통합 후 `IA_사이트맵.md 7장`(권한표 원본) 대조 완료 — E-01 §2 와 동일, 새로 얹을 것 없음.** 잔여 미결 4건(①②⑤⑥)은 P8·P1 전까지 유예이며 원칙 문서에 목록으로 남아 있다 |
| G4 미배치 화면 3건 단계 배정 | ✅ | **순서표 갱신 완료.** ① `연구실 설정 > 구성원·권한` → **P1**(P1 단계 취지 문구도 함께 개정 — 권한 값의 원천 하나만 예외로 쓰기 화면을 연다) ② S-08 → **이미 P2 에 배정돼 있었다**(미배치는 실제로 3건이 아니라 2건) ③ 연구실 정보 읽기 모달 → **P7 편입**(E-07 안의 컴포넌트라 별도 단계로 뺄 이유가 없다). 조사 = `sessions/G4.md` |
| G5 DataModel v1.8 ↔ 스키마 대조 | ✅ | 산출 `DATAMODEL-BASELINE.md` — 기준표(누락 0) · v1 diff · 소급 위험 11건. **v1 저장 형태 계승 0**(계보·프로젝트 테이블 자체가 없음). 결정 `PLAN-SoT §9-⑰⑱⑲⑳` · 신규 열림 `㉑`(D4→D3 Port) |
| G7 기획 SSOT 통합 | ✅ | **정본 폴더 하나로 완결.** 인덱스 6파일을 정본 루트로 통합하고 260818 기준으로 갱신. **깨진 상대링크 38건 → 1건**(남은 1건은 P1 README → 없는 package html, P1 은 1차 범위 밖이라 미수정). 재검증 = 내가 직접 링크 스윕(222개 중 1개) · 스토리 실측(E-01 7 · E-07 8 · 합 45) · 게이트 green. **정본 내용 변경 1건 = "에픽당 스토리 6개 상한" 폐기(`§9-㉝`, Ted 비토 가능 · 백업 `99 temp/정본-백업-20260822`)**. 남은 `[미확인]` = `연구실 설정` 화면(S-07)의 소유 에픽이 어느 문서에도 없다 |
| G8 온톨로지 범위 합의 | ✅ | **승인 완료 (2026-08-23, `§9-㊸`)** — ④-1 (다) 하이브리드 · ④-2 (가) 문서 정본(목업은 예시) · ④-3 (가) D9 시드(④-4 함의, 비토 가능) · ④-4 **시드 테이블 3개**. 산출 `ONTOLOGY-SCOPE.md`(값 기재 완료). **K1 진입조건 충족** |

### T-D 도메인·계약
| WU | 상태 | 비고 |
|---|---|---|
| D1 도메인 경계 확정 | ✅ | **배정표 확정 — `DOMAINS.md §7` 신설**(10개 전부 Ted · 협의 필수 5곳은 **정본 대조** · 딸린 규칙 4개). 근거 `§9-㉚`·**`§9-㊴`**. **2026-08-23 닫힘** — 별도의 수문학 소유자를 두지 않고 **10개 전부 Ted**, 대신 **D9 의 판단 근거를 사람의 암묵지에서 `기획 정본` 으로 옮겼다.** 정본에 없으면 `[정본 무근거]` 로 남기지 만들지 않는다. `DOMAINS §3-③` 이 경고한 "아무도 검증하지 않는" 상태를 막는 방어가 이것이다 — **출처가 문서면 검증이 가능하다** |
| D2 계약 동결 | ✅ | **완료 판정(spectral + oasdiff green) 충족.** 산출 = `contracts/schemas/common.json`(정의 21종 · 값 집합 enum 9종을 DataModel v1.8 에서 전수 대조) · seam 3종 `fe-core`(op 34) `core-ai`(op 2) `core-viz`(op 5) · async 봉투 `contracts/events/`(이벤트 7종) · 게이트 `contract-lint`(spectral 6.16.3 핀) `contract-breaking`(oasdiff 도커 다이제스트 고정) · `contract-selftest` **15 케이스 green**. **진입조건 이탈 1건 — 2026-08-23 해소.** 착수 당시 `D1` 이 열려 있었으나 계약이 그 값을 소비하지 않아 전제를 밝히고 진행했고, `§9-㊴` 로 D1 이 닫히며 전제가 사실로 확인됐다(`§5`). 결정 ㉟㊱㊲ |
| **D3b RLS 실효 증명** | ✅ | **2026-08-23 닫힘** — 게이트 `rls-effect` 로 승격. ①본체 음성(허용자 아님·만료 → 0행) ②메타 양성(잠긴 것의 메타는 조회됨, `P-13`) ③cross-tenant(18표 전수 0행). **red fixture 18/18**, 그중 4방향이 **잘못된 롤이면 red**(superuser·BYPASSRLS·소유자 이전·없는 롤) — 소유자 롤로 도는 게이트는 green 을 보고하면서 아무것도 증명하지 않는다. 부수로 `db-selftest` 결합 결함을 고쳤다(기준 케이스가 레포 정본 allow-list 를 읽어, K1 의 정당한 `d9_*` 추가가 「낡은 면제」로 걸렸다 — **게이트가 옳고 selftest 배선이 틀렸다.** 검사와 3줄을 둘 다 남기고 픽스처를 격리). ~~신설~~ `rls-coverage` 는 정책이 *걸렸는지* 만 본다. 정책이 *실제로 막는지* 는 음성·양성 테스트만 증명한다 — ① 허용자 아님·만료됨 → 본체 조회 **DB 층 0행** ② 잠긴 데이터셋의 **메타는 조회됨**(`P-13` 회귀 방지) ③ cross-tenant 0행. **진입조건 = P0 스키마** |
| **D2b 이벤트 계약 게이트** | ✅ | **2026-08-23 닫힘** — `event-lint`(ajv 8.17.1 핀 · 스키마 컴파일 + 유효 5 통과/무효 8 거부) · `event-breaking`($defs 단위 diff, **ERR 14규칙 / WARN 3규칙을 표로 명문화** — 파괴 규칙이 암묵인 게이트는 게이트가 아니다) · `event-selftest` **33 케이스**(그중 5건은 green 을 주장한다 — enum 추가·선택 필드 추가·제약 완화. 「파괴가 아닌 것」의 절반도 증명해야 한다). **실제 파괴가 red 를 냄을 fixture 가 아니라 진짜 파일로 증명**했다(`envelope.json` 의 enum 값 제거 + required 추가 → E06·E04, 되돌린 뒤 `contracts/` 바이트 동일). 산출 `sessions/D2b.md`. ~~신설~~ `contracts/events/**` 를 보는 게이트가 없다 — `contract-lint` 는 `seams/**` 만, `contract-breaking`(oasdiff)은 OpenAPI 전용. **이벤트 계약의 파괴적 변경을 아무도 못 잡는다.** 필요 = `event-lint`(ajv) + `$defs` 단위 diff + red fixture selftest |
| D3 경계 강제 장치 | ✅ | **2026-08-23 닫힘** — 잔여였던 RLS 실효 증명이 D3b 로 완결됐다. 이하 원 기록: | **게이트 6종 배선·증명 완료. 남은 것은 RLS 실효 증명 하나**(→ **D3b**, P0 스키마가 있어야 쓸 수 있다). `import-boundary`(import-linter 2.13 · 계약 7개) · `banned-import`(ast · 배포 단위별 deny) · **`ai-no-lineage-write`**(음성 · red 조건 12개를 계약/코드/체인 3단으로) 배선 완료, **`boundary-selftest` 30 케이스 전부 의도대로 green**. 세 게이트 자체는 **red 이고 그게 정상** — `services/`·`db/` 에 코드가 없다("AI 가 계보에 쓰지 않는다"와 "AI 가 아직 없다"는 다른 사실이라 0건을 green 으로 세지 않았다). **부수 산출 = 모듈 경로 관례 확정**(`sessions/D3-boundary.md`) — P0 가 이걸 따른다. **DB 게이트 3종도 완료** — `migration-single-head`(alembic 미사용, `ast` 로 `down_revision` 그래프 직접 파싱 → DB 접속 없이 판정) · `schema-diff`(선언 `schema.sql` 을 일회용 postgres 에 적용해 `pg_dump` 대조. **DB 없음·도커 없음도 red** — 여기서 skip 하면 그게 정확히 v1 의 실패다) · `rls-coverage`(`pg_class`/`pg_policy` 조회 ↔ `gates/config/rls-allowlist.toml`). **`db-selftest` 38 케이스 green**(도커 없이 도는 24 + e2e 14). **한계 = RLS 정책의 *내용* 은 안 본다** — `USING(true)` 가짜 정책이 통과한다. ㉖ 이 요구한 실효 증명은 D3b 다. **C4 입력은 없어도 진행됐다** |

### T-P 플랫폼 (에픽 0~7)
| WU | 단계 | 상태 | 진입조건 |
|---|:--:|---|---|
| P0 공통 기반 | 0 | ✅ | **2026-08-23 닫힘.** 완료 판정 8행 중 1~7 충족(8 은 조문 자체가 「I2 이후」). 스키마 20표 · core-api **34 라우트**(실질의 5 · 501 29, code 두 종으로 「저장처 없음」과 「로직 미착수」를 구분) · **경계 증명 6종**(cross-tenant 음성 4 + `body_access` 실효 2, red 9/9) · FE 셸. 산출 `sessions/P0-schema.md`·`P0-core-api.md`·`P0-rls-proof.md`·`P0-frontend.md` |
| P1 카탈로그 + 상세 헤더 | 1 | ⬜ | **P0 ✅ — 진입조건 충족, 착수 가능** |
| P2 업로드·계보 확정·S-08 | 2 | ⬜ | P1 · G4 · K3 |
| P3 계보 그래프 · 2D 시각화 | 3 | ⬜ | P2 |
| P4 검색 히어로 · 결과 | 4 | ⬜ | P1 · **G2** · K4 |
| P5 프로젝트 | 5 | ⬜ | P1 |
| P6 승인 처리 | 6 | ⬜ | P1~P5 |
| P7 연구실 대시보드 | 7 | ⬜ | P6 |
| P8 E-01 적용 지점 표 | 후 | ⬜ | P7 |

### T-K 지식·AI
| WU | 상태 | 비고 |
|---|---|---|
| K1 온톨로지 스키마 | ✅ | **2026-08-23 닫힘.** 시드 테이블 3개 — `d9_method_term`·`d9_topic_synonym`·`d9_place_alias`, 전부 `db/ai` 체인(`0002_k1_ontology`). 그래프 구조 없음(`㊸-④-4`). **RLS 를 걸지 않았다** — 세 표에 `lab_id` 가 없고, 공유 어휘를 경계로 감싸면 `current_lab_id()` NULL 비교로 전 연구실에서 안 보이게 되어 사전이 죽는다. 면제가 소극적 선택이 아니라 옳은 값이며, 뒤집히는 조건을 allowlist 주석에 남겼다. 게이트 4종 green · **왕복 증명이 음성을 포함한다** — 목업의 `유출·수문` 이 CHECK 위반으로 튕긴다(`㊸-④-2` 「목업은 예시」가 DB 층에서 강제된 실물). 산출 `sessions/K1.md` |
| K2 온톨로지 시드 적재 | ✅ | **2026-08-23 닫힘.** **적재 22행**(어휘 13 · 주제 5 · 지명 4) / **커버리지 기준 21항목 미커버 0**. 둘이 다른 수인 이유 — 기준의 주제는 4값이고 적재는 5행이다(항등행 4 + 정본이 준 유일한 동의어 `강우데이터` 1) — 21건 전부 정본에서 직접 grep 해 인용 위치를 기재했다. **중요한 것은 넣은 것이 아니라 넣지 않은 것이다** — 정본이 준 주제 동의어는 `강우데이터` **하나뿐**이었고 나머지를 만들지 않았다. `크롭` 은 §2.6 표의 의역이라(정본 grep 0건) 원문 `유역 경계로 잘라냄` 만 적재. `[정본 무근거]` 5건은 `K2.md §5`. 커버리지 체크 red 실증 5방향 — 그중 **기준 파일을 13→12 로 줄이면 red**(검사 대상을 줄여 green 을 얻는 경로를 스스로 막는다). 시드는 마이그레이션 체인 안(`0003`), `ON CONFLICT DO UPDATE` 멱등 실측. 산출 `sessions/K2.md` |
| K3 계보 제안 서비스 | ⬜ | **D4 쓰기 경로 부재 음성 테스트 필수** · 모델 = `㊷` GPT(luna/terra) — **luna 품질 실측 후 승격 판단** |
| K4 자연어 검색 서비스 | ⬜ | ~~G2 차단~~ **해제**(`㊶`) · 모델 = `㊷` |
| K5 제안 원장 | ⬜ | |

## 2. 현재 상태 스냅샷

- **개발환경**: WSL. 레포는 기존 작업트리를 그대로 승계(`core.fileMode false` 유지) · `gh` 인증 완료. **레포 밖 자산(기획 정본)은 승계되지 않는다** — 2026-08-22 정본을 작업공간 형제 폴더로 들여와 이 위험을 줄였다(`PLAN-SoT §9-㉕`).
- **레포**: `CognileapAI/colab-v2` (신규 모노레포, **public** — PLAN-SoT §9-⑯). **원격 push 완료**, `origin/main` = 스캐폴드 커밋(`620238c`). `main` 보호 ON: force-push·삭제 차단, 리뷰 필수 없음(1인 CODEOWNERS 셀프-락아웃 회피), enforce_admins off. CI 1회 완주 — 게이트 잡 전부 "미구현 — red". 스캐폴드 = `contracts/` `services/{core-api,pipeline-worker,viz-render,ai-service}` `frontend/` `db/{platform,ai}/` `gates/` `eval/` `infra/` `dev-package/` `planning/` + CODEOWNERS + CI 골격.
- **게이트**: **13종 중 12종 구현.** `planning-freshness` `contract-lint` `contract-breaking` `event-lint` `event-breaking` `import-boundary` `banned-import` `ai-no-lineage-write` `migration-single-head` `rls-coverage` `rls-effect` `schema-diff`. 미구현은 `generated-up-to-date` 하나이고 **설계대로 red** 다. 자기 증명 **139 케이스**(contract 15 · event 33 · boundary 30 · db 43 · rls-effect 18).
- **코드**: **있다.** `services/core-api`(FastAPI, 34 라우트 · pytest 106) · `frontend`(React 앱 셸) · `pipeline-worker`·`viz-render`·`ai-service`(빈 도메인 자리 + 헬스). `db/platform` 20표 · `db/ai` 3표+시드 22행. **저장 형태 기준은 `DATAMODEL-BASELINE.md`가 정본** — 코드가 이 표와 어긋나면 코드가 틀린 것이다.
- **staging**: **살아 있다.** `www.colab-hydro.com` 에 5개 배포 단위 + postgres(2체인). 컨테이너 `colab_v2_staging_*` 8개. 앱 롤은 비소유자·NOBYPASSRLS. 백업은 일 03:30 · 주간 재검사.
- **AWS 리소스**: 없음. I1에서 IaC로 생성.
- **기획 정본**: `Co-Lab_ver2_1차마일스톤_목업패키지_260818_이태헌` — **작업공간 형제 폴더 `40 COLAB-기획/`**(2026-08-22 이전, `PLAN-SoT §9-㉕`). E-00 DataModel **v1.8**·Policy **v1.4**, E-01 Policy **v1.3** 확인 · DataModel `§8 미결 = 없다`(1차 저장 형태 전부 확정). 인덱스 5종은 260808판에만 있음 → G7.
- **전달 패키지**: 8종 중 **6종이 낡음**. E-00이 가장 크게 밀림(v1.7·v1.8 두 판).
- **참조 자산**: `20 CoLAB-v1` (이관 전 — 현재 `00 CoLAB-PoC`·`10 CoLAB-Launch`). 읽기 전용.
- **도메인**: `DOMAINS.md` 10개 정의 완료. **소유자 배정 완료**(`§7` — 10개 전부 Ted, D9 판단 근거는 기획 정본. `§9-㊴`).

## 3. 결정 로그

확정·열림 전체는 `PLAN-SoT.md §9`. 새 결정이 나면 **거기 적고 여기서 링크**한다(두 곳에 적으면 갈라진다).

최근 확정 — ① 신규 구축 ~~② AWS 배포까지~~(**㊻ 로 개정 — staging 까지**) ③ 정본 260818 ④ AI 도메인 분리 ⑤ WU 단위 ⑥ Assistant BC 미계승 ⑦ `colab-v2` 모노레포 ⑯ 레포 public *(전부 2026-08-22 Ted)* · **⑰ G5 대조 상대 = v1 스키마 ⑱ v1 저장 형태 계승 0 ⑲ 값 집합은 DB가 강제 ⑳ 파생값 2종 미저장** *(2026-08-22 G5)*. **㉑ D4→D3 읽기 Port 시그니처 확정 ㉒ "도메인 소유자" = 변경 승인권자 ㉓ staging=터널 호스트·prod=AWS ㉔ PoC 철거·데이터 폐기** *(2026-08-22 Ted)*. **㊵ 승격 게이트(staging 확인 → Ted 승인 → AWS) ㊶ 검색 = Postgres 단독 ㊷ 모델 = GPT 전면 통일(luna/terra, API 키 · Claude 어댑터 휴면) ㊸ 온톨로지 §④ 4항목 확정 — G8 승인, K1 진입조건 충족** *(2026-08-23 Ted)*. **㊹ 미구현 엔드포인트 = 501 + code 두 종(404 아님, 계약 무수정) ㊺ staging postgres 2 DB · 앱 롤 비소유자·NOBYPASSRLS** *(2026-08-23 Claude 판단 · 비토 가능)*. **㊻ AWS 보류 — v2 완주 판정을 `staging 배포 green` 까지로 내리고 prod 는 출시 결정 뒤에 연다** *(2026-08-23 Ted)*. 열린 결정 **⑧⑨⑩ 해소**(⑪~⑮는 그대로 열려 있다). **㉖(RLS 실효 증명) 은 D3b 로 닫혔다.** 새로 열린 것 — 없음

## 4. 블로커 (사람이 풀어야 할 것)

> **2026-08-23 갱신 — 진행을 막는 사람 결정이 남아 있지 않다.** AWS 계정(#1)은 `§9-㊻` 으로 **보류가 결정됐고**, OpenAI API 키(#9)는 **투입됐다.** **전 트랙이 Claude 착수 가능이다.**

| # | 블로커 | 막는 것 |
|---|---|---|
| 1 | ~~**AWS 계정·결제**~~ | **성격 변경 · 블로커 아님** (2026-08-23, `§9-㊻`) — Ted 가 **보류**를 결정했다. 완주 판정이 `staging 배포 green` 까지로 내려갔으므로 I0·I1·I5 는 임계경로에서 빠진다. prod 는 **출시를 결정할 때** 연다. 실제로 이 항목이 막고 있던 P·K·D 트랙은 **하나도 없었다** |
| 2 | ~~**자연어 검색 엔진 결정**~~ | **해소** (2026-08-23, `§9-㊶`) — **Postgres 단독**(tsvector + pgvector). 별도 엔진을 두지 않는다. 경계가 RLS 로 공짜로 따라오고, 정렬 최종 결정권이 어차피 core 에 있다. **P4·K4 차단 해제** |
| 3 | ~~**온톨로지 범위 (수문학 소유자 시간)**~~ | **성격 변경** (2026-08-23, `§9-㊴`) — 더 이상 **사람의 시간을 기다리는 블로커가 아니다.** 범위·어휘를 **기획 정본에서 길어 올리는 작업**이고 승인은 Ted 가 한다. **G8·K 트랙이 Claude 착수 가능**이 됐다. 남은 위험은 하나 — 정본이 값을 주지 않는 곳에서 **만들어 채우는 것**. 그런 자리는 `[정본 무근거]` 로 남긴다 |
| 7 | ~~**`ssh.colab-hydro.com` ingress 가 오리진 없이 살아 있다**~~ | **해소 · 실행 완료** (2026-08-23, `§9-㉜`). 진단이 얕았다 — 잔재는 **세 겹**(ingress · Access 앱 · DNS CNAME)이었고 셋 다 제거했다. **엣지에 만든 것은 라우팅·인증·이름 세 층에 흩어진다** |
| 8 | **Cloudflare 터널 ID 가 public 레포 히스토리에 남아 있다** — 커밋 `2c06cc3` 의 `sessions/IS2.md`. 다음 커밋에서 값은 빠졌으나 히스토리는 그대로다. **자격증명은 아니다**(터널 조작에는 API 토큰이나 터널 토큰이 필요하고 둘 다 유출되지 않았다). 심각도 낮음이나 이 프로젝트 규약은 ID 도 레포 밖에 둔다. 선택지 = ① 그대로 둔다(권장 — `main` 은 force-push 차단) ② 히스토리 재작성 + 보호 일시 해제 ③ 터널 재생성(`TUNNEL_TOKEN` 무효화 = staging 재구성, 과하다) | 없음 (판단만) |
| 4 | ~~CI 실행 환경 결제~~ | **해소** (2026-08-22) — public 전환으로 GitHub Actions 무료 러너 사용. R1에서 CI 1회 완주 확인 |
| 5 | ~~전달 패키지 재빌드 (기획 소유자)~~ | **해소** (2026-08-22) — 패키지 내용은 이미 `DataModel v1.8`·`Policy v1.4` 와 일치했다(sha256 대조). 재빌드 대상이 없다. 남은 것은 그 사실을 기계가 지키게 하는 것(G1) |
| 6 | ~~기획 정본 마운트~~ | **소멸** (2026-08-22) — 정본을 작업공간 안 `40 COLAB-기획/` 로 옮겨 **마운트 의존 자체가 없어졌다**(`PLAN-SoT §9-㉕`). 외부 드라이브 스트리밍 사본은 읽기가 간헐 실패해 게이트에 오탐 red 를 냈다. 참조 고리를 전부 끊었다 |

| 9 | ~~**OpenAI API 키**~~ (`㊷`) | **해소** (2026-08-23) — Ted 가 `~/.colab-v2-staging.env` 에 투입. `ai-service` 컨테이너까지 통로 연결 완료(`compose.i2.yml`, 커밋 `6737b73`). **K3·K4 차단 해제.** 소비 시작은 K3. |

## 4.5 다음 세션 진입조건 (WSL — 작업 시작 전 확인)

| # | 확인 | 명령 | 실패하면 |
|---|---|---|---|
| 1 | **기획 정본이 읽히는가** | `./gates/run.sh planning-freshness` 가 **green** | 폴더 목록만 보는 확인은 이 조건을 못 잡는다 — **목록은 되고 읽기가 실패**하는 상태가 실제로 있었다. 게이트는 15개 문서를 실제로 **읽어서** 해시를 낸다. red 면 정본 폴더(`planning/README §1`)가 제자리에 있는지 먼저 본다 |
| 2 | 레포가 원격과 같은가 | `git status -sb` 가 clean + ahead/behind 0 | `git pull` |
| 3 | gh 인증 | `gh auth status` | `gh auth login` (환경별 키링 — Windows 인증은 WSL로 안 넘어온다) |
| 4 | **staging 이 살아 있는가** | `docker ps` 에 `colab_v2_staging_*` **8개**(nginx·cloudflared·pg·core_api·frontend·pipeline_worker·viz_render·ai_service) · `curl -I https://www.colab-hydro.com/healthz` 200 · 5개 단위 `/healthz/<unit>` 각각 200 | WSL 재시작 시 컨테이너가 안 뜬다(데몬이 자동 기동하지 않는다). 되살리는 명령은 **`-f compose.i2.yml` 을 반드시 붙인다** — `docker compose -f infra/staging/compose.i2.yml --env-file ~/.colab-v2-staging.env up -d`. **`-f` 를 빼면 `compose.yml`(자리표시 오리진 2개)이 떠서 I2 가 조용히 롤백된다.** 컨테이너는 `restart=unless-stopped` 이고 `pgdata` 는 홈의 바인드 마운트라 **데이터는 재부팅을 넘긴다**. **토큰은 홈의 `.colab-v2-staging.env`(0600) — 레포에 없다** |

> **1번은 이 프로젝트의 반복 함정이었다.** 레포는 환경을 옮겨도 따라오지만 **레포 밖 자산(기획 정본)은 따라오지 않는다.**
> 2026-08-22 정본을 **작업공간 형제 폴더 `40 COLAB-기획/`** 로 들여와 외부 드라이브 의존을 끊었다(`PLAN-SoT §9-㉕`).
> 확인 방법도 바꿨다 — **폴더가 보이는가**가 아니라 **문서가 실제로 읽히는가**를 본다. 앞의 것은 통과하고 뒤의 것만 실패하는 상태가 실재했다.

## 5. PLAN 이탈 기록

| # | 이탈 | 왜 | 되돌리는 법 |
|---|---|---|---|
| **1** | **D1 이 열린 채로 D2·D3 을 진행했다** (2026-08-22 밤) | `WORK-UNITS §6` 이 D2 의 진입조건을 `D1, A3` 로 적었는데 둘 다 문제가 있었다. **(a) `A3` 는 존재하지 않는 WU 다** — 트랙 목록에 A 트랙 자체가 없다(v1 잔재로 보이는 유령 참조). **(b) D1 의 잔여는 `HYD` 실명 한 칸뿐**이고, 그 값은 *누가 승인하는가*의 문제이지 계약의 내용이 아니다 — OpenAPI·JSON-Schema 어디도 그것을 소비하지 않는다. Ted 가 "밤새 개발할 수 있는 것은 개발하자"고 한 상황에서, 이름 하나를 기다리며 밤을 비우는 것이 더 큰 손실이라고 판단했다 **해소 (2026-08-23)** — `§9-㊴` 로 D1 이 닫혔고, 전제("경계·배정 구조는 확정, 이름 한 칸만 미기재")가 **사실로 확인됐다.** 배정은 바뀌었지만(2인 → Ted 1인 + 정본 대조) 계약은 한 줄도 손대지 않았다 — **계약이 배정과 독립이라는 판단 자체가 검증된 것이다.** 되돌릴 것 없음 |

> **`A3` 유령 참조는 별도로 정리해야 한다.** 진입조건에 없는 WU 가 적혀 있으면 다음 세션이 그것을 기다린다.

---

## 갱신 방법 (세션 종료 시)

1. §1에서 해당 WU 상태 갱신 (✅/🟧+사유/⛔+원인)
2. §2 스냅샷 갱신
3. 상단 **최종 갱신 / 현재 단계 / 다음 WU** 갱신
4. 새 결정은 `PLAN-SoT §9`에 기록하고 §3에서 링크
5. 새 블로커·이탈은 §4·§5에
6. **미완 항목과 다음 WU의 진입조건을 명시** — 다음 세션이 §1을 선행조건으로 확인한다
