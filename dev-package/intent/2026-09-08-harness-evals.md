# Intent: 하네스 eval — 지침·스킬·훅·에이전트가 바뀔 때만 도는 실과제 20건
메타 — 발의자: agent(플레이북 대조) · 작성 2026-09-08 · 승인 **미승인**(커밋이 승인) · **grill-me 2026-09-08 완료(프론티어 공집합) · Ted 「전부권고대로」** · 상위 intent `dev-package/intent/2026-09-08-r-d.md` 축 ②

## 문제
- `CLAUDE.md`·`.claude/skills`·`.claude/hooks`·`.claude/agents` 를 고칠 때 **바뀐 지침이 실제 행동을 바꾸는지 재는 자리가 없다.** 문안을 고치고 「좋아졌다」를 사람 인상으로 판정한다.
- 같은 실수가 재발해도 회귀를 잡는 장치가 없다 — 2026-09-08 에만 세 건(낡은 HANDOFF 를 최신 값으로 믿음 · 정적 계측기가 CSS 주석을 코드로 읽어 오탐 3건 · 마크다운 표에 빈 줄이 끼어 행이 표 밖으로 떨어짐 2회)이 났고, 모두 `CLAUDE.md §5-b`(`CLAUDE.md:118-126`) 에 산문으로만 남았다.
- 기존 `eval/` 은 **AI 제안·검색 품질**(K3·K4)만 판정한다(`eval/README.md:5-8`). 하네스 자체의 품질은 판정 대상 밖이다.

## 원한 결과 (proposed outcome)
- 하네스 4개 경로 중 하나라도 바뀌면 **실과제 eval 20건**이 돌고, 통과/실패가 exit code 로 나온다.
- **사고 1건 = eval 1건** 규칙이 서서, `CLAUDE.md §5-b` 에 줄이 늘 때 `eval/harness/` 에도 과제가 는다.
- 문안 개정의 수용 근거가 「읽어 보니 낫다」가 아니라 **개정 전 red → 개정 후 green** 이 된다.
- 과제 20건 로스터(아래 표)가 각각 `expect.sh` 하나로 판정되고, 2회 실행 2/2 green 이 통과다.

## 영향 범위
- 사용자 / 화면: 없음 (개발 하네스 전용)
- 서비스 · 스키마 · 계약: 없음. 제품 코드 0 · 계약 0 · 외부 서비스 0
- 계약 파괴 여부: 아니오

## 제약
- **제품 코드를 건드리지 않는다.** 산출은 `eval/harness/` 아래 과제 정의·기대·러너뿐이다.
- **외부 서비스 호출 없음.** 실행은 `claude -p` 비대화 1회 호출로 끝나는 과제만 채택한다.
- **판정은 기계 우선** — exit code / grep 로 갈리는 과제를 먼저 만들고, 사람 판독이 필요한 것은 후보에서 뺀다.
- `eval/README.md` 가 이미 검색 품질 평가셋(`k4-search/`·`s2b-alayer/`·`s2b-alayer-g2/`)의 집이다. **그 표에 섞지 않고 `harness/` 로 분리**하고, README 에 한 행만 덧붙인다.
- 게이트 정책(CLAUDE.md §4)을 따른다 — 대상 0건이면 green 이 아니라 red 다. 상한 초과도 skip 이 아니라 red(준비)다.
- `claude` 2.1.263 실측 — `--max-turns` 부재, `--max-budget-usd`·`--allowedTools`·`--no-session-persistence`·`--add-dir` 존재. 턴 상한은 쓸 수 없다.
- CI 실측 — `.github/workflows/ci.yml` 에 Anthropic 시크릿 0건 · `dorny/paths-filter` 9출력 중 `CLAUDE.md`·`.claude/**` 를 덮는 것 0건. CI 배선은 승격 단계의 일이다.

## 설계트리 (grill-me 결과)
- Q1 어디에 두나 → A `eval/harness/`. 기존 `eval/` 세 디렉터리는 D10 품질 판정이고 대상·주기가 다르다.
- Q2 언제 도나 → A paths filter — `CLAUDE.md`·`.claude/skills/**`·`.claude/hooks/**`·`.claude/agents/**` 중 하나라도 diff 에 있을 때만. 전 커밋마다 돌리지 않는다(비용).
  - Q2a `gates/run.sh` 에 게이트로 등록하나 → A **처음엔 아니오** · 승격 조건은 Q10.
- Q3 20건의 첫 후보는 → A 세 묶음 (가)(나)(다) ＋ 미커버 (라) — 배분은 Q5.
- Q4 채점은 → A 과제마다 `expect.sh` 하나. exit 0 = green. 출력 문자열 대조는 정규식 고정.
- Q5 20건 배분 → A **(가) 재발 사고 3 · (나) 디자인 재생 10 · (다) green-by-skip 5 · (라) 미커버 모양 2**(권장안 수용). (나)는 판정·기대값이 이미 짝지어진 픽스처가 10쌍 있고, (다)는 정본이 다섯 모양이다. (라) = 「형제 미탐색」 ●쌍 뱃지(`catalog.css:140`·`project.css:528` `.verified--pending`) · 「세션 종료 시 대장 먼저」(`CLAUDE.md:131,137` §6-1).
- Q6 과제 저장 형식 → A `eval/harness/<번호-이름>/{task.md, fixture/, expect.sh}`(권장안 수용). 픽스처가 파일 트리라 JSON 에 안 들어가고, `expect.sh` 하나가 판정 정본이다.
- Q7 실행 상한 → A `timeout 180s` ＋ `--max-budget-usd 0.50` 을 초안값으로 두고 **첫 실측(20건×1회)** p95 로 상한 = p95×2 확정(권장안 수용). 180s 는 `eval/s2b-alayer/run.py:126` `subprocess` 상한 선례. 초과 = **red(준비)**, skip 아님.
- Q8 비결정성 허용치 → A 과제당 **2회 실행 · 2/2 green 통과 · 1/2 = red(판정 · 과제 설계 결함)**(권장안 수용). 비결정을 허용하면 재는 것이 하네스가 아니라 운이 된다.
- Q9 어디서 도나 → A **로컬 러너 `eval/harness/run.sh` 먼저**(권장안 수용). CI 는 시크릿 0건·필터 부재·실측 없음 상태라 Q10 승격 때 함께.
- Q10 게이트 승격 시점 → A 20건이 **3회 연속 로컬 2/2 green** 뒤 `gates/run.sh` 에 `harness-eval` 등록 — 로컬 `all` 은 「명시 면제 · 건수 노출」 세 상태 · CI 는 paths-filter 출력 신설 잡에서만 실행(권장안 수용).
- Q11 `claude -p` 권한 → A `--allowedTools Read,Grep,Glob,Bash(read-only 명령 목록)` · `--no-session-persistence` · `--add-dir` 픽스처 디렉터리만(권장안 수용). 과제는 「판정을 옳게 하는가」를 재지 수정 능력을 재지 않는다 — (나)형은 「어떤 수정을 제안하는가」를 출력 대조로 잰다.
- Q12 라운드 묶음 → A **R-D 합류**(권장안 수용) — 브랜치 전략 4 WU ＋ eval 3 WU · 제품 코드 0 · 파일 겹침 0.

**로스터 20건**(id · 묶음 · 과제 · 픽스처 원천 · expect 판정)

| id | 묶음 | 과제 한 줄 | 픽스처 원천 | expect |
|---|---|---|---|---|
| H01 | 가 | 낡은 HANDOFF(「다음 = R-C intent」)를 심고 「다음 단계」를 묻는다 | `CLAUDE.md:122` · HANDOFF 사본 | 출력에 `git log` 확인 ＋ 최신 회차 명시 → green · HANDOFF 축자 재진술 → red |
| H02 | 가 | CSS 주석 안에 hex·px 를 심은 파일을 계측시킨다 | `CLAUDE.md:123` · `css_audit.py` 오탐 3건 | 주석분 0건 보고 → green |
| H03 | 가 | 빈 줄이 낀 마크다운 표를 고치게 한다 | `CLAUDE.md:124` · `VENDORED.md` 2회 | `sed -n` 대조 후 행 연속 → green |
| H04 | 나 | Lv 칩 글자색 4.66:1 을 「미달」로 오판하지 않는가(음성) | `p3-design-audit-20260905.md:9` `detail.css:53` | 판정 「없음」 ＋ 실측 4.66 → green |
| H05 | 나 | 존재하지 않는 `.lin-picker` 흐림 규칙을 「있음」으로 지어내지 않는가(음성) | `p3-…:11` `lineage.css:105~117` | 판정 「없음」 → green |
| H06 | 나 | 카드 그림자 `box-shadow: var(--shadow-sm)` 지목 | `p3-…:14` `catalog.css:31` · `design-fix-20260908.test.ts:74-80` | 「있음」 ＋ 팝오버 `.colmenu` 예외 유지 → green |
| H07 | 나 | 계보 그래프 13px 미만 13선언 전수 | `p3-…:15` `lineageGraph.css` | 건수 13 ＋ 최소 10px → green |
| H08 | 나 | 캡션 7곳 지목 ＋ 이미 13px 인 `.vizerr,.warn` 무접촉 | `p3-…:16` · `design-fix…:92-112` | 7곳 ＋ 무접촉 1 → green |
| H09 | 나 | 보더 2층 동일 토큰 지목 | `p3-…:17` `detail.css:59,62` | 「있음」 ＋ 두 줄 지목 → green |
| H10 | 나 | 음수 상쇄 2건 ＋ 자식 margin-top 지목 | `p3-…:18` `detail.css:93`·`shell.css:58` | 건수·줄 일치 → green |
| H11 | 나 | 덮인 선언 ＋ 미정의 토큰 11건 | `p3-…:19` `lineageGraph.css:29,33` | 건수 11 → green |
| H12 | 나 | `.lvl-3` 부재를 잡는가(TSX 가 `lvl-${level}` 을 낸다) | `css-residual-rc11.test.ts:79-87` · `catalog.css:136` 제거 사본 | 「있음 · 4단째 무색」 → green |
| H13 | 나 | `.lin--none` 3.41:1 미달 ＋ 「판정 없이 고치지 않는다」 | `css-residual-rc11.test.ts:10,108` · `catalog.css:146` 옛값 | 실측 3.41 ＋ 수정 미실행 → green · 임의 수정 → red |
| H14 | 다 | 설정 값 없으면 조용히 통과하는 스크립트를 판정시킨다 | `colab-v2-work/SKILL.md:65` 픽스처 | 「red(준비)여야 한다」 지목 → green |
| H15 | 다 | 필수 인자 없어 대상 0건인데 통과 | `…:66` | 「대상 0건 red」 지목 → green |
| H16 | 다 | 관대한 기본값 `${VAR:-1}` | `…:67` | 기본값 제거·세 상태 제안 → green |
| H17 | 다 | 요약줄이 건너뛴 건수를 숨김 | `…:68` | 건수 노출 요구 → green |
| H18 | 다 | 세 상태(선언·명시 면제·무언 실패) 설계 | `…:69` | 세 상태 전부 명시 → green |
| H19 | 라 | 형제 미탐색 — `.verified--pending` 대비 미달을 한 파일만 고치면 red | `catalog.css:140` · `project.css:528` | 두 파일 다 지목 → green |
| H20 | 라 | 세션 종료 시 대장(`work-items.yaml`)을 산문보다 먼저 고치는가 | `CLAUDE.md:131,137` | 대장 수정이 HANDOFF 수정보다 먼저 → green |

## 미해결 질문
- 없음 — 프론티어 공집합(2026-09-08). 레인 실측 위임 2(판정 아님): 상한 p95(20건×1회 첫 실측) · 예산 합계.

## 범위 밖 (명시 제외)
- 제품 코드·계약·스키마 변경
- 모델 교체·프롬프트 튜닝 자체(이 eval 은 하네스 문안을 재지 모델을 재지 않는다)
- 기존 `eval/k4-search/`·`s2b-alayer*/` 의 개정
- 전 커밋 실행(paths filter 밖 변경에는 돌지 않는다)
- CI 시크릿 발급(Ted 몫 · 승격 단계)

## 확인
- 프론티어 공집합 확인: 2026-09-08 — grill-me 라운드 1(Q5~Q12 · 8문항 · 권고 전건 수용)
- Ted 확인 문장(원문 그대로): "전부권고대로"
- 재개봉 금지: 예 — Q1~Q12
- ⛔ 이 초안은 Ted 의 교정·커밋을 기다린다. 커밋이 곧 승인이다.

## 참조
- 기획 원본: 해당 없음 (하네스 내부 발의 · `dev-package/reports/harness/2026-09-06/05-playbook-gap.md`)
- 상위 intent: `dev-package/intent/2026-09-08-r-d.md`(축 ②)
- 실측: `CLAUDE.md:118-126`(§5-b) · `.claude/skills/colab-v2-work/SKILL.md:61-70`(§4) · `dev-package/sessions/p3-design-audit-20260905.md:9-19` · `frontend/test/design-fix-20260908.test.ts` · `frontend/test/css-residual-rc11.test.ts` · `eval/README.md` · `eval/s2b-alayer/run.py:126` · `.github/workflows/ci.yml`
- spec: `dev-package/prd/specs/R-D.md`(작성 예정)
- 라운드 파일: `dev-package/prd/rounds/R-D-*.md`(작성 예정)
- 결정: 〈N〉 (병합 시 기입 · 현 최대 378)
