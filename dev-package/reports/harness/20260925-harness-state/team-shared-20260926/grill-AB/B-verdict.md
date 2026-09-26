(Opus) spec B의 우려 항목 6건 판정. 판정자는 blind이고 초안 권고 열은 인용하지 않았음.

### B-#1
- 판정: 「새 선택지: ⓐ의 골격(형식 OR (legacy ∧ 동결 스냅샷), 영구 동결)을 유지하고 두 곳을 보정. ⑴ 불변 검사는 `LEGACY_SNAPSHOT ∈ changed(fork..head)` ∧ base에 존재할 때만 base 블롭과 바이트 대조 ⑵ 스냅샷이 base·head 모두에 없으면 현행 legacy 규칙을 전체에 적용(형식만으로 떨어지지 않게)」
- 확신: 높음
- 사실 확인:
  - HEAD `4f84c433`에서 다시 셈: `dev-package/intent/*.md` 86파일 = approved 63 · unapproved 17(TEMPLATE 포함) · no-meta 6(README 포함). approved 63은 `5bb3d6fe`(84파일)와 같음. 10라운드에서 늘어난 2건(`ci-harness-eval-run` · `portable-gate-locks`)은 둘 다 미승인.
  - spec 4.1 `:56`은 불변 검사를 base 블롭 ≠ head 블롭, head 부재도 포함한 조건으로 적었음. 그러면 B 병합 전에 분기한 다른 구성원의 열린 PR이 push할 때마다 red가 됨. CI는 `COLAB_INTENT_REF_HEAD = pull_request.head.sha`(`ci.yml:675-676`)라 머지 커밋이 아님. 이 PR들은 스냅샷을 건드리지 않았으므로 오탐.
  - 기존 ⑵ 검사는 `changed`(fork..head, `intent_ref.py:115-116,161`)로 대상을 거름. 같은 방식을 쓰면 삭제·추가·주석 변경·다른 사본 반입은 모두 여전히 red로 잡힘.
  - spec이 fail-closed라고 적은 「스냅샷 부재 = 형식만」은 보호 기준으로 보면 fail-open임. 로컬에서 base를 선언하지 않으면 base = merge-base(`:103-107`). 갱신하지 않은 브랜치는 base·head 둘 다 스냅샷이 없어 63건이 비보호가 되고, 로컬 green이 CI red와 갈림.
  - base∪fork 보호(`:154-160`)에 base 스냅샷 하나를 쓰는 설계 자체는 성립함.
- 이유:
  - ⓑ는 승인 intent 63건의 append-only 보호(ADR-0007 `:14`)를 한 번에 풀어 버림. 재발행하면 원 승인 원문과 날짜를 새로 지어내야 함.
  - ⓐ의 동결 목록은 규칙을 기계로 돌린 출력이고 재생성이 가능함. 네트워크 0·토큰 0이라 어느 기계에서나 같은 판정이 나옴.
  - 보정 ⑴은 다른 구성원의 열린 PR에 생기는 거짓 red를 없앰(팀 원칙 「같은 비용」). 보정 ⑵는 전환기에 로컬과 CI가 다르게 판정하는 것을 없앰.
- 위험·전제:
  - lane begin부터 병합 전까지 develop에 legacy 표기로 승인된 intent가 새로 들어오면 스냅샷 밖에 남음. §6·§9의 병합 직전 `--freeze-legacy origin/develop` 재대조는 필수 절차로 유지해야 함.
- 뒤집힐 조건:
  - CI가 머지 ref를 head로 쓰도록 바뀌거나, ruleset strict 때문에 갱신 전 push 자체가 발생하지 않는다는 실측이 있으면 보정 ⑴은 불요.
  - 스냅샷 없는 base를 쓰는 실행 경로가 CI와 로컬 어디에도 없다는 것이 확인되면 보정 ⑵는 불요.

### B-#2
- 판정: ⓐ
- 확신: 높음
- 사실 확인:
  - ADR-0003 `:19` 「검사 green은 형식 판정이며 승인이 아니다」 · `:18` 결정 승인·병합은 사람이 한다.
  - 10라운드 Q4(intent `:627`)는 「승인 권한 = develop 리뷰 권한자」를 정했지만, 권한을 기계로 대조하라는 문구는 없음.
  - `intent-ref` CI 잡에는 `GH_TOKEN` 설정이 없음(`ci.yml:663-677`).
- 이유:
  - ⓑ는 네트워크와 토큰에 의존함. 오프라인 기계나 토큰 없는 실행에서는 78이 나와 기계마다 판정이 갈림(팀 원칙 위반).
  - ⓑ가 보장하는 것은 계정이 있다는 사실뿐이고 승인 권한은 여전히 판정하지 못함. 비용은 늘고 보증은 늘지 않음.
  - 실제 승인 행위는 사람이 병합하는 것(Q1)이고, 형식 검사는 기록 품질만 담당함.
- 위험·전제:
  - 오타이거나 실존하지 않는 handle도 approved가 됨. 리뷰어가 메타 줄을 읽는다는 전제에 기댐.
- 뒤집힐 조건:
  - Ted가 「승인자 권한을 기계로 대조한다」를 새로 결정하는 경우. 그때는 존재 조회가 아니라 CI 전용 collaborator permission 조회와 준비 실패 규약을 함께 설계해야 함.

### B-#3
- 판정: ⓐ
- 확신: 높음
- 사실 확인:
  - ADR-0003 `:35` 「2026-09-17 추가 —」 선례가 실제로 있음.
  - ADR-0007 `:30` 재검토 조건 「메타 형식이 바뀌어 승인 판별식이 틀리기 시작할 때」에 이번 변경이 해당함.
  - `adr_gate.py:170-174`는 accepted 이력의 삭제·이름 변경·상태 되돌림만 막음. 줄 추가는 통과함.
  - `docs/decisions/README.md:61` 「하네스의 승인·검증·완료 조건을 바꿀 때」 → 기록 자체는 필요함.
  - 최신 ADR은 0010.
- 이유:
  - 결정 본문(`:14` 「승인 표기가 있는 intent는 줄 추가만」)은 그대로이고 판별 방식만 바뀜. 같은 결정의 개정이므로 대체 ADR이 필요 없음.
  - ⓑ는 0011·0012 예약과 병합 순서를 뒤집음.
  - 추가 줄에서 `:26` 「알려진 비보호」의 현재 목록(B-#4의 2건)도 함께 갱신할 수 있음.
- 위험·전제:
  - §7 begin에 `--gate adr-records --scope docs/decisions/0007-…` 추가가 필요함.
  - 추가 줄은 「형식 OR legacy∧스냅샷 · 스냅샷 불변」만 적고 기존 줄은 한 글자도 바꾸지 않아야 함.
- 뒤집힐 조건:
  - append-only 원칙 자체(예: 스냅샷 만료, 승인 intent 개정 허용)를 바꾸게 되면 새 ADR로 대체해야 함.

### B-#4
- 판정: ⓐ
- 확신: 높음
- 사실 확인:
  - `2026-09-08-harness-evals.md`의 첫 메타 줄에 「**미승인**(커밋이 승인)」이 있어 unapproved로 분류됨. v1 `:13-15` intended_unprotected와 일치.
  - **spec 누락 1건**: `2026-09-18-missing-rate-predicate-recon.md`. 메타가 두 줄로 줄바꿈되어 첫 `메타` 줄(`:2`)에 「승인」이 없어 unapproved로 분류됨. 실제 승인 표기(「승인 **사용자 2026-09-25**」)는 `:3`에 있고 `da3fee02`(2026-09-25)에서 승인됨.
  - v1 표에 이 파일 행이 없음. spec §1의 unapproved 15에 조용히 포함돼 있음.
- 이유:
  - 스냅샷이 `--freeze-legacy` 바이트 출력과 같아야 V-B3 재현이 성립함. 예외 1건을 손으로 넣으면 재현이 깨지고 「손 편집도 red」 규칙과 모순됨.
  - 두 파일 모두 기계 기준으로는 미승인이라 편집할 수 있음. 사람이 메타 첫 줄을 새 꼴로 바꾸면 곧바로 보호됨.
- 위험·전제:
  - 사람이 조치하기 전까지 두 파일은 비보호로 남음.
  - v2 정답표 `intended_unprotected`에 2건을 모두 적고, B-#3 추가 줄에도 2건을 적는 것이 전제.
- 뒤집힐 조건:
  - 판별 규칙 자체를 「메타 단락 전체」로 넓히기로 결정하는 경우. 그때는 예외가 아니라 규칙이 바뀌므로 스냅샷을 다시 생성함.

### B-#5
- 판정: 「새 선택지: ⓐ의 소유 분리(B는 1회 검사, A가 `home_path_roots`를 소유)를 유지하되 A에 추가할 토큰은 `dev-package/reports/harness/20260925-harness-state`(정확한 하위 디렉터리). B의 검사는 ad hoc grep 대신 `scripts/harness/config.py` `HOME_PATH` + `home_path_allow`와 같은 식으로」
- 확신: 중간
- 사실 확인:
  - ⓐ의 전제 「기존 `dev-package/reports/**` 잔존 0」은 현재 거짓임. `dev-package/reports/harness/` 아래 5개 파일(`20260924-agent-model-tiering/M2-codex.md` · `2026-09-06/pe-sweep-3.12.log` · `20260924-lane-hygiene-review/A2-turn-cuts.md` · `20260925-external-harness-gap/G1-flow.md` · `G2-guards.md`)에 실행자 홈 절대경로 6건이 있음. `dev-package/reports/**` 전체로는 80여 파일.
  - 상위 토큰 `dev-package/reports/harness`를 넣으면 A가 red가 됨.
  - `check_home_paths`(`config.py:271-290`)는 `git ls-files` pathspec을 씀. 아직 없는 경로는 0파일로 통과하므로 A를 먼저 병합해도 무해함.
  - spec의 grep 식은 `HOME_PATH`의 Windows 형식(`C:\Users\…`)을 빠뜨렸고, `home_path_allow`의 `/home/user/`를 걸러내지 못함.
  - 원본 3개 파일(`R4-judges-evidence.md:11` · `round10-drafts/spec-B.md:9` · `gate-B.md:21`)에 `/home/user/`가 있음. 그래서 V-B9 「grep = 0」은 spec이 스스로 정한 「`/home/user/` 유지」와 동시에 성립할 수 없음.
  - ⓑ는 `.agents/**`가 해시 집합(`config-paths.txt:12`)이라 회차가 필요해지고, B의 「회차 불요」 조건이 깨짐.
- 이유:
  - 소유 분리 자체는 옳음(ⓑ 배제).
  - 다만 토큰 범위와 검사식이 A의 정식 장치와 같아야 두 번 검사해도 같은 판정이 나옴.
  - 과거 증거 5개 파일을 정리하는 일은 A·B 어느 쪽의 범위에도 없음.
- 위험·전제:
  - A의 `home_path_roots` 목록은 10라운드 Ted 확정 3토큰임. 1토큰 추가는 spec A 우려 판정에서 확인받아야 함.
- 뒤집힐 조건:
  - 기존 5개 파일의 홈 경로를 치환하는 별도 작업이 먼저 병합되면 상위 토큰 `dev-package/reports/harness`가 더 나음.

### B-#6
- 판정: ⓐ
- 확신: 높음
- 사실 확인:
  - `~/.claude/` 표기는 원본 20여 파일에 약 40곳(줄 단위 grep 35줄).
  - `HOME_PATH`(`config.py:29-33`)는 `~` 형식을 잡지 않음. 절대경로가 아니므로 위생 검사 대상도 아님.
  - 일부는 반입 대상 밖(`~/.claude/pr-bodies/` · `jobs/` · 메모리)을 가리킴.
- 이유:
  - 반입물은 증거라서, 내용을 바꾸지 않는 것이 README 「내용 무수정」 선언과 맞음.
  - README에 `~/.claude/reports/harness-state-20260925/` → 반입 디렉터리 대응 1줄을 두고, 대응이 없는 `~/.claude/*`는 「저장소에 없음」으로 1줄 적는 것으로 충분함.
- 위험·전제:
  - 다른 기계의 리뷰어는 README를 거쳐야 경로를 따라갈 수 있음.
- 뒤집힐 조건:
  - 반입 디렉터리 안에서 링크를 기계로 검사하는 게이트를 도입하는 경우.

### 묶음 메모
- 반입 범위: 원본은 현재 97파일임. spec의 「88」에 `team-shared-20260926/round10-drafts/` 7개와 `grill-AB/` 2개가 더해졌고, 이 판정문도 곧 추가됨. V-B9 「89」와 README 표 행은 복사 시점에 다시 재야 하며, 두 디렉터리 행을 README 표에 추가해야 함.
- B-#1 보정 ⑵, B-#4, B-#3은 서로 묶임: 스냅샷을 순수 기계 출력으로 두고, 비보호 2건(harness-evals · missing-rate)을 v2 정답표와 ADR-0007 추가 줄에 같이 적음.
- B-#5는 spec A의 우려 판정(`home_path_roots` 토큰)과 연결됨. A가 먼저 병합돼도 하위 디렉터리 토큰은 0파일로 green.
- TEMPLATE 주석(4.3)에 「새 꼴 승인은 첫 `메타` 줄 한 줄 안에 적는다」를 넣을 것. missing-rate처럼 줄바꿈되면 새 꼴도 unapproved가 됨.
- §9 병합 직전 `--freeze-legacy` 재대조는 B 자체의 base에 스냅샷이 없을 때만 가능한 창이므로(B-#1 보정 ⑴과 무관), 게시 뒤 메인 절차에 고정해야 함.
