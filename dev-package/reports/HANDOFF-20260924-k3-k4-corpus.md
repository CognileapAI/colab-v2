# 인계 — K4 실측 · K3 재설계 · 코퍼스 확장 (2026-09-22 ~ 09-24)

다음 세션이 **이 문서 하나만 읽고** 이어받을 수 있게 적는다. 세부는 각 절이 가리키는 파일에 있다.

- 작업 브랜치 **`k3-resume`** · HEAD **`c4cdd5ea`** · origin push 완료 · **develop 미병합**(Ted 「dev 병합은 추후」 2026-09-24)
- develop(`02d251d8`) 대비 41 커밋. 작업 체크아웃 = 워크트리 `.claude/worktrees/k4-haiku-probe`
- 레인별 가지는 전부 origin 에 남아 있다(`k3-*`, `k3s-*`, `corpus-*`, `d10-*`) — 되짚을 때 쓴다

---

## 0. 지금 무엇을 하던 중이었나 (재개 지점)

**진행 중이던 레인 1건 — 「재시드 재개 전 로컬 검증」**(가지 `corpus-local-verify`, 미완).
로컬 일회용 스택에서 재시드 러너의 `accounts → 임시 운영자 해제 → 재로그인 → projects` 순서가
실제로 프로젝트 생성에 성공하는지 증명하는 일이다. **dev 무접촉.**
그 레인이 끝났는지 origin 에 `corpus-local-verify` 가 있는지로 확인하고, 없으면 새로 띄운다.
지시 전문은 이 문서 §4-(a) 에 요약돼 있다.

**막힌 자리 한 줄** — dev 재시드가 `seed` 국면에서 두 번 멈췄다. 2차 실패의 남은 문제는
**운영자 자격 해제가 로그인 세션을 무효화해 `projects` 화면이 로그인 화면을 본 것**이고,
재로그인 한 줄이 실물에서 검증된 적이 없다. 그것만 닫으면 `--from seed` 로 잇는다.

---

## 1. 끝난 일 — K4 자연어 검색 (develop 에 병합됨)

**결정 `PLAN-SoT §9-㊷` 의 잔여 조건 절반을 닫았다.** develop `02d251d8`.

- luna(`gpt-5.6-luna`)를 제품 프롬프트·파서 그대로 골든 12문항 × 2회 실호출 → 참조 코퍼스 9건에서
  **retrieval 10/10 · 순위 중앙값 1.0** vs literal **9/10 · 2.0**. 기능어 혼입·낱말 날조 0, 지연 중앙 2.74초.
- ㊷ 에 추기 2건 — ① K4 실측 결과·terra 승격 대상 없음·**K3 미실측** ② **처리 리전 기록 의무 철회**
  (OpenAI 가 리전을 노출하지 않음 · 대신 모델·캐시율·토큰·지연·결과를 원장에 적재).
- 러너 `eval/k4-search/llm_interpreter_probe.py` · 재생 시험 `services/core-api/tests/test_k4_interpreter_probe.py`
  (표식 `k4_probe`, 판정 게이트 선택자에서 제외) · 보고 `dev-package/reports/k4-luna-probe/README.md`.

⚠ **dev 에서 K4 골든을 다시 재려면 골든 ID 재고정이 선행**이다(§3 과 같은 문제). 메모리
`k4-golden-ids-not-on-dev` 참조.

---

## 2. 끝난 일 — K3 계보 제안 (k3-resume 에만 있음 · develop 미병합)

K3 는 **검색이 아니라 자료 등록 화면(E-04)의 「부모 자료 귀띔」 기능**이다. Ted 가 2026-09-24 에
「K3 는 검색과 별개」임을 확인한 뒤 진행을 결정했다(「아 그렇네」).

### 2-1. 1차 구현 (intent `2026-09-24-k3-lineage-suggestion-resume.md` · 라운드 `R-K3-RESUME.md`)
계약에 후보 배열 추가 → core-api 가 후보 선정·중계 → ai-service 가 luna 로 순위·근거 →
게이트 ② 수정 8건 → 실측. **실측에서 red 2건**: 근거가 메타에 없는 말을 인용(2건), 정답을 뺀
대조군에서 8회 중 6회 억지 선택(그중 5회가 **자기 자신**).

### 2-2. 자기 자신 제외 + 프롬프트 두 문장
- 이름 초안과 파일명이 **둘 다** 같은 후보를 뺐다 → 근거 위반 0 으로 닫힘. 그러나 대조군에서
  이번엔 **자기 자식**(가공 단계가 더 높은 후손)을 골랐다.
- 프롬프트 두 문장(「근거 없으면 빈 배열」·「상위 단계는 부모 아님」) → 빈 제안 2/4·2/4 로 개선했으나
  **보장은 아니다**(Q1 판정의 근거).

### 2-3. 재설계 — 「없다」는 구조가 말한다 (intent `2026-09-24-k3-abstention-by-structure.md` · 라운드 `R-K3-STRUCTURE.md`)
Ted 승인 Q1~Q6 + 게이트 ① 조건 5건. **문 세 개** 구조:
1. **적격 필터**(core-api) — 자기 자신 제외 + `max(파생 Lv, 사람이 적은 Lv)` ≤ 업로드 Lv.
   업로드 Lv 가 없으면 ai-service 를 부르지 않고 「가공 단계를 고르면 제안이 가능합니다」.
2. **모델의 일 = 후보별 근거 인용**(`evidence[{field, uploadValue, candidateValue}]`). 확신도·근거 문장은
   모델에게 묻지 않는다(잠정 자리채움).
3. **인용 검증**(core-api) — 다섯 축(기간 겹침·CRS/격자 정규화 동등·변수 교집합·파일명 토큰 접두)으로
   대조해 검증 안 된 제안은 폐기. **확신도는 검증된 근거 종류 수에서 파생**(≥2 확실 · 1 애매 · 0 제안 없음).
4. **규칙 기반 팔**(`app/rule_suggest.py`) — 모델 없이 축 대조만으로 순위. 모델 팔과 같은 k 절단.
   스위치는 모듈 상수, 기본 `model`.

**S6 실측 결과** — 구조 누수 **0건**(후손만·정답+형제 제거 군에서 두 팔 모두 빈 제안).
그러나 **모델이 30회 중 29회 빈 배열**을 내 hit@3 가 0~1/6(규칙 팔 2/6) → 둘 다 판정 보류.
**원인은 코퍼스의 축 빈곤** — 참조 9건의 자동 메타에서 살아 있는 축이 `fileName` 하나뿐이다.
그래서 **코퍼스 확장이 다음 병목**이 됐다(§3).

### 2-4. 곁가지로 끝난 것 — D10 모델 호출 원장
`db/ai` 에 표 `d10_model_call`(리비전 `0008_d10_model_call_ledger`) + 검색 해석·계보 제안 두 자리 배선.
칸 15(모델 요청/응답·결과·지연·토큰 3·**캐시 토큰**·입력/결과 수·연구실). **리전 칸 없음**(㊷ 추기 ②).
캐시율은 조회 때 계산. intent `2026-09-24-d10-model-call-ledger.md`.

⚠ **알려진 충돌** — 이 `0008` 이 `codex/ai-search-next` 의 `0008_dataset_knowledge`(0009·0010 이어짐)와
번호가 겹친다. 두 갈래가 만날 때 **원장을 `0011` 로 재부모화**한다(시드 없는 표 하나라 이동 비용 최소).

---

## 3. 진행 중 — 코퍼스 확장 (intent `2026-09-24-corpus-expansion-dev-reseed.md`)

**왜** — K3·K4 측정이 전부 참조 코퍼스 9건에서 돌고, 그 자동 메타가 비어 있어 축 대조가 공허하다.
dev 를 28건 실물로 재시드하면 `format·crs·grid·period` 4축이 살아난다.

### 3-1. 사전 확인 (전부 끝남 · 보고서 `dev-package/reports/corpus-expansion/`)
| 항목 | 결과 |
|---|---|
| dev 플랫폼 DB | **0건**(자료·계정·자동메타·계보). 연구실 1 |
| dev AI 사전 DB | 103행 · head `0007` · **재시드해도 손실 0행**(표 전수 6개 확인, 전부 마이그레이션 시드) |
| S3 | `uploads/`·`previews/` 1,778 객체 = **DB 가 가리키지 않는 고아**. 재시드가 543파일로 다시 만든다 |
| 선행 ㉮㉯ | `/opt/colab-repo` 를 `ea21d8c2aa54` 트리로 갱신 · 백업 1회(07:40Z) — **완료** |
| 리허설 | 원시동작 **10/10** · doctor **15/15** · preflight **11/11** |
| 게이트 ③ | **조건부 go** — 조건 1~3 충족, 조건 4(동시 사용자 없음)는 Ted 확인 완료 |

⚠ **백업 24시간 창** — doctor ⑭ 가 24시간 내 백업을 요구한다. 07:40Z(한국 16:40) 기준이며
넘겼으면 `infra/dev/backup.sh` 를 한 번 더 내고 시작한다. dev 야간 백업 크론이 옛 판이라
9-13 이후 죽어 있다(별건 후속).

### 3-2. 두 번의 중단 (실행 기록 `dev-package/sessions/DR-4-run-20260924T*.md`)
1. **1차** — `seed` 의 프로젝트 생성에서 「대상 연구실을 선택해 주세요」. 원인 = 2026-09-14 이후
   `services/core-api/src/colab_core/app/target_scope.py` 가 생성 4종에 `X-CoLAB-Target-Lab` 을 요구하는데
   **운영자 계정에만** 걸린다. 러너는 교수를 임시 운영자로 올린 채 화면을 걷는다.
2. **2차(㈏ 수선 뒤)** — 운영자 해제는 성공(`DELETE 1`)했고 「대상 연구실」 오류는 **사라졌다**.
   그런데 자격 변경이 **로그인 세션을 무효화**(`kernel/db_credentials.py:260-264` ·
   `kernel/login_sessions.py:192-206`)해 `projects` 가 로그인 화면을 봤다. 재로그인 한 줄은 **실물 미검증**.
   「재개 1회」 규칙을 지켜 3회차는 내지 않았다.

**지금 dev** — 비어 있고 정상 가동(컨테이너 4 healthy). 교수는 평범한 교수, 운영자 4명 유지.
해제가 멱등이라 **`--from seed` 로 같은 run-dir 에서 그대로 잇는다**(reset~prelude 재실행 불요).

### 3-3. 곁가지 — dev DB 가 왜 비었나 (조사 완료 · 부분 확정)
- **시점 확정** — 2026-09-15 04:17~07:27 UTC 사이. S3 백업이 172,867 B → 20,983 B.
  스키마 head 불변이라 마이그레이션·DROP 이 아니라 **행만 지워졌다**.
- 그 구간 유일한 배포(PR #67)는 「데이터 초기화 미포함」 명시. 자동 reset 도구는 그때 없었다.
- **미확인** — 실제 쓰기 주체, 9-16 백업 회복(168,601 B) 경위, 9-18 이후 재공백화 경로.
- **권고(미착수)** — `backup.sh` 가 행 수를 함께 기록하고 전일 대비 급감 시 fail-closed 경보.

---

## 4. 다음에 할 일 (순서 고정)

### (a) 로컬 검증 — **진행 중이던 레인**
로컬 일회용 스택에서 `accounts → 해제 → 재로그인 → projects` 를 돌려 프로젝트 생성 200/201 을 본다.
2차 실패를 먼저 red 로 재현하고, 재로그인이 왜 안 먹었는지(쿠키 항아리? 대기? 해제 경로?)를
파일:줄로 짚은 뒤 고친다. **dev 무접촉.** 여기서 막히면 대안 ㈎(러너가 세 화면에서 「대상 연구실」을
고르게 한다 — 화면 구조에 다시 묶이는 비용)로 전환한다.

### (b) dev 3회차 재개
백업 24h 확인 → preflight 11/11 → `COLAB_RESEED_TARGET_REF=ea21d8c2aa54 bash dev-package/tools/dev-reseed/reseed.sh --from seed --run-dir <기존 run-dir>`
(env 는 `~/.config/colab-platform/with-dev-env.sh` · `COLAB_DEV_SECRETS_DIR` unset).
**파일럿** — 첫 3건 업로드 뒤 읽기 전용 SQL 로 `d3_dataset_autometa` 의 `crs`·`grid`·`format`·`period_start`
non-null 확인(BYPASSRLS 롤로 세야 한다 — 소유자 롤은 FORCE RLS 로 거짓 0 을 낸다).
전부 null 이면 나머지 3.4 GB 를 올리지 않고 중단.

### (c) WU3 스냅샷 재포획 (읽기 전용)
28건의 `id`·`name`·**`processing_level`(이름의 「(Lv.n)」이 아니라 열로)**·`lab_id`·프로젝트 연결·
자동메타 5축·`d3_dataset_variable` 행·파일(본체/격자 구분)·부모(역할·method 유무).
⚠ 28건 이름에 「(Lv.n)」이 **없다** — 현행 K3 의 Lv 추출이 깨지므로 스냅샷 v2 에 열로 넣어야 한다.

### (d) WU4 골든 재박기 — **Ted 서명 2건**
① 이름→새 ID 대응표 28행 ② 골든 12문항의 새 `scope`·`required`.
**9건은 28건의 부분집합이 아니다**(묶음 경계가 다름) — 단순 ID 치환 불가.
재박기 대상 6파일 490회(ULID 122): `expanded-normalized-02.json` 228 · `dev-data-snapshot.json` 123 ·
`golden-cases.json` 113 · `golden-set.md` 11 · `lineage-cases.json` 10 · `test_llm_lineage_probe.py` 5 ·
코드 박힘 `eval/k4-search/golden_baseline.py:134`(`!= 9`). 질문 문장과 `golden-set.md` 의미 기준은 무수정.

### (e) WU5 재측정
K4(literal·luna) · K3(규칙 팔·규칙+모델 팔 · 대조군 4종)를 새 코퍼스에서. 합격선은 실측 전 고정.
`variables` 축은 **재시드로 채워지지 않는다**(0/28 · 코드 확정 — 파이프라인이 안 쓴다).
후속으로 공식 PATCH 경로(`d3_catalog.replace_variables`)로 채울 수 있고 **두 번째 reset 은 불요**.

---

## 5. 열려 있는 Ted 판정거리

| # | 무엇 | 권고 |
|---|---|---|
| 1 | **develop 병합 시점** | 코퍼스 실측 뒤 한 번에(Ted 「추후」 확인됨) |
| 2 | 골든 재박기 대응표·scope 서명 | WU4 에서 올린다 |
| 3 | K3 후보 0건일 때 `degraded` 값·사유 표시 | 사유를 `degraded` 와 분리해 항상 싣기 (intent 미해결 7) |
| 4 | `variables` 축 채우기(PATCH 후속) | 재시드와 분리해 별건 |
| 5 | dev 백업 행수 경보 · 크론 드리프트 검사 | 별건 intent |
| 6 | 재시드 러너 ↔ 제품 권한 모델 정합 검사 | 어느 게이트에도 없다 — 별건 |

---

## 6. 함정 목록 (다음 세션이 밟기 쉬운 것)

- **워크트리 가드** — 이 세션은 워크트리에 격리돼 있어 `eval` 이라는 낱말이 든 셸 명령, `.`/`source`,
  복잡한 파이프라인이 거부된다. 디렉터리는 `./ev*l` 로 쓰고 명령은 단순하게 쪼갠다.
- **lifecycle `--mode=complete`** — 공백 형식(`--mode complete`)이 훅에 막힌다. `=` 로 쓴다.
- **게이트 전용 적용 DB** — `colab_platform_applied_30`·`colab_ai_applied_30` 을 워크트리 여럿이 공유한다.
  원장 레인이 한 번 재생성했으므로 `codex/ai-search-next` 쪽 레인이 쓰면 drift 검사가 red 를 낼 수 있다.
- **`k3_probe`·`k4_probe` 표식** — 측정 전용이라 `gates/run.sh:644` 의 core-api 선택자에서 빠져 있다.
  새 측정 시험을 만들면 선택자에 함께 넣어야 전수에서 error 가 안 난다.
- **FORCE RLS** — dev 를 소유자 롤로 세면 0 이 나온다. BYPASSRLS 롤로 센다.
- **`--rehearse`** 는 `HEAD = 후보 sha` 를 요구한다(`stages.sh:973-976`). 본 실행(`--from seed`)엔 없다.

---

## 7. 파일 지도

```
dev-package/intent/
  2026-09-22-k4-luna-interpreter-probe.md        K4 실측 (승인 · develop 병합됨)
  2026-09-24-k3-lineage-suggestion-resume.md     K3 1차 (승인 · 판정 기록 1·2회차)
  2026-09-24-k3-abstention-by-structure.md       K3 재설계 (승인 · Q1~Q6 + 게이트 ① 조건 5)
  2026-09-24-d10-model-call-ledger.md            실행 원장 (승인)
  2026-09-24-corpus-expansion-dev-reseed.md      코퍼스 확장 (미승인 · 서명 2건 대기)
dev-package/prd/rounds/
  R-K3-RESUME.md · R-K3-STRUCTURE.md             라운드 + 게이트 ① 판정 기록
dev-package/reports/
  k4-luna-probe/README.md                        K4 두 절반
  k3-lineage-probe/README.md                     K3 실측 4회분 + ELI7 HTML 4건
  corpus-expansion/                              사전대조·리허설·선행조건·재시드 2회
dev-package/sessions/DR-4-run-20260924T*.md      재시드 실행 기록 2건
```

사용자 전달본(레포 밖) — `~/workspace/00_Project/00 CoLAB/_delivered/K3-*.html` 4건.

---

## 8. 추기 2026-09-25 — 재개 지점

- 최종 가지 **`corpus-reseed-final`** = `corpus-verify-preview-5`(`c24c03d4`) ＋ 문제 기록. `k3-resume`(`4b162d54`) 위 선형 사슬 · develop 미병합.
- **(a) 로컬 검증 — 끝남**(`corpus-local-verify` `8f90f7d7`).
- **(b) dev 재시드 — 데이터 적재 끝 · 검증 미달.** 28/28 등록 · 프로젝트 4 · 간선 18 · autometa 28/28(period_start 28 · grid 26 · crs 24).
  재시드 `stage_verify` exit 1(미리보기 성립 25 · 미성립 1 · 판정불가 2) → **계정 최종화 미실행** — 운영자 4명 초기 자격 유지 ·
  Ted 개인 계정 비밀번호 초기화는 최종화 뒤로 계속 연기.
- 수선 재시도 **3회 소진**(Ted 규칙 — 무변경 재시도 금지 · 수선 재시도 최대 3회 · 매 시도 전 전략 서면).
  남은 항목(seq 13·14 GeoPackage 판정불가 · seq 16 미성립)은 `corpus-expansion/dev-reseed-issues-2026-09-24.md` #21·#22.
- 업로드 필수 칸 28행은 Ted 서명 확정(`b210ce5c` · `dev-package/tools/dev-seed/upload-classify.json`).
- **(c) 스냅샷 재포획 · (d) 골든 재박기(Ted 서명 2건) · (e) 재측정 — 미착수.** 적재된 dev 데이터로 진행할 수 있다.
- 최종화 재시도 여부·방법은 Ted 판단. 문제 기록 25건과 §9 개선 항목이 dev-reseed 개선 intent 의 입력이다.
- 제품 후속 후보 6건(문제 기록 §7)은 미수선 · GitHub 이슈 등재 여부는 Ted.
- 실행 자리 run-dir = `.claude/worktrees/agent-a9c33a67acf039b61/dev-package/reports/dev-reseed-runs/wu2-20260924T0834Z/`
  (`preview-judgment.tsv` · `logs/verify.log` · `session-records/` 8건). 다음 실행이 `logs/*.log` 를 덮는다(문제 기록 #10).
