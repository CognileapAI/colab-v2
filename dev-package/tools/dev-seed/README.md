# dev 화면 자동 투입 — 러너 정본

- 자리 = `dev-package/tools/dev-seed/`. 2026-09-13 회차에 실제로 dev 를 채운 도구를 레포로 들인 것이다.
- 성격 = 사람이 밟던 체크리스트를 **같은 화면 경로로** 밟는다. 서버 API 직접 호출 없음.
- 구성 3 + 1 —

| 파일 | 하는 일 |
|---|---|
| `plan-manifest.yaml` | 등재표 **생성물**(데이터셋 28 · 간선 18 · 상대 glob · 기준 격자 짝 · 부모 · 제품 레벨). **손으로 고치지 않는다** |
| `build_plan.py` | `DATASETS.md` 4건 + 참조자료 뿌리 → `plan-manifest.yaml` ＋ `upload-plan.json`(러너 입력) |
| `runner.py` | 로그인 · 프로젝트 · 데이터셋 · 확인 · 보고 다섯 단계를 화면에서 실행 |
| `watch.py` | 러너 진행을 20초 간격으로 읽어 새 줄만 출력 |

- **정본 사슬 = `DATASETS.md` 4건 → `build_plan.py` → `plan-manifest.yaml` ＋ `upload-plan.json`.**
  값을 고칠 자리는 md 하나뿐이고, 뒤의 둘은 생성물이다.
- md 4건의 자리(참조자료 뿌리 기준) = `01.level-data/01.precipitation/DATASETS.md` ·
  `01.level-data/02.vegetation/DATASETS.md` · `01.level-data/03.drought/DATASETS.md` ·
  `02.File-format/DATASETS.md`. 레포 안 거울 사본은 `dev-package/reports/reference-data/datasets-md/`.
- 각 md 는 사람이 읽는 표와 기계가 읽는 ```yaml 블록(첫 줄 `colab-datasets v1`)을 함께 담는다.
  블록의 `seq` 1~28 은 러너 상태 파일의 키라서 **바꾸지 않는다**.
- 등재표 계수의 출처 = `dev-package/reports/reference-data/2026-09-13-inventory-v2.md` §5(등재표 28행) · §5-6(기준 격자 짝).
- 시나리오 = `dev-package/scenarios/dev-minimal-data-setup.md` 2·4·5·6·7 절.
- 능력문(지목점) = `dev-package/reports/r-dev-reset/agent-browser-capability.md` 6 절.

## 0. 자리와 값 — 코드에 절대경로를 두지 않는다

| 값 | 주는 법 | 기본값 |
|---|---|---|
| 참조자료 뿌리 | `--ref-root` · 환경변수 `COLAB_REF_ROOT` | 본 체크아웃과 나란한 `03 Reference-Data`(워크트리에서도 본 체크아웃 기준) |
| `DATASETS.md` 뿌리 | `--md-root` | 참조자료 뿌리와 같은 자리 |
| 작업 자리 | `--work-dir` · 환경변수 `COLAB_SEED_WORK_DIR` | 이 폴더의 `.work/`(레포 `.gitignore` 제외) |
| 대상 주소 | `--base-url` > `COLAB_DEV_WEB_URL` > 호환 `COLAB_DEV_URL` | **없음** — 빈 환경변수는 다음 값으로 넘어간다. seed/reseed가 같은 우선순위를 쓴다. dev 주소의 원본은 `docs/DEPLOY.md` |

- 작업 자리 아래에 생기는 것 = `upload-plan.json` · `state.json` · `verify.json` · `logs/` · `shots/` ·
  `fail/` · `initial-password.txt` · `new-password.txt`. **전부 추적하지 않는다**(자격·세션·절대경로 포함).
- 자격 파일은 0600 으로 강제된다. 실투입이 끝나면 `initial-password.txt` 는 `shred -u` 로 지운다.

## 1. 준비

1. `agent-browser` 설치 확인 — `agent-browser doctor` 가 10 pass.
2. dev 선행 4건(연구실 · 계정 · 자격 · 서비스 운영자)이 끝나 있어야 한다(시나리오 1 절).
3. 계획 만들기 —

```
# ⓐ 레포 쪽 대조 — 레포에 실린 정본 md 사본으로 표↔블록↔실물을 먼저 본다
python3 build_plan.py --md-root dev-package/reports/reference-data/datasets-md --dry-run

# ⓑ 실투입 기록 — md 뿌리를 주지 않는다(기본값 = 참조자료 뿌리의 md 가 정본)
python3 build_plan.py                    # plan-manifest.yaml ＋ <work-dir>/upload-plan.json 기록
```

- **ⓐ 와 ⓑ 는 읽는 md 가 다르다** — ⓐ 는 레포 사본(`dev-package/reports/reference-data/datasets-md`),
  ⓑ 는 참조자료 뿌리(`--ref-root` · `COLAB_REF_ROOT`). 실투입에 쓰는 계획은 **ⓑ 다.**
  ⓐ 는 참조자료가 없는 자리에서도 도는 대조용이고, 여기서 종료코드가 0 이 아니면 md 부터 고친다.

- `--dry-run` 은 계수(28 · 18) · glob 이 맞힌 파일 수 · 총 바이트를 찍고 **아무것도 쓰지 않는다.**
- 참조자료 뿌리가 없으면 `--dry-run` 은 파일 해석을 건너뛰고 블록 계수만 센다. 기록 실행은 거절한다.
- **판정 3단 · 종료코드** —

| 코드 | 뜻 | 무엇이 어긋났는가 |
|---|---|---|
| 0 | 정상 | 표 = 블록 = 실물 나무 · 총계 28/18 |
| 3 | 표 ↔ 블록 불일치 | 같은 md 안에서 표의 이름·건수·바이트가 블록과 다르다. 어긋난 행 이름을 찍는다 |
| 2 | 블록 ↔ 실물 불일치 · 총계 불일치 · md 부재 · 뿌리 부재 | glob 이 맞힌 파일 수·바이트가 블록과 다르거나 총계가 28/18 이 아니다 |

- 계획 행은 **`processing_level`(`Lv0`~`Lv3`)을 싣는다** — 러너가 「가공 단계」에 그대로 넣는다(§2-1).
- 총계 기대값은 `--expect-datasets`·`--expect-edges` 로 바꾼다(기본 28 · 18 · 시험용).
- **실물 폴더가 정본이다** — 2 가 나오면 md 의 값을 실측값으로 고친다(폴더를 고치지 않는다).
- 시험 = `python3 -m pytest dev-package/tools/dev-seed/tests -q`(표준 라이브러리 ＋ `yaml` ＋ `pytest`).

4. 자격 파일 2개를 작업 자리에 둔다 — `initial-password.txt`(초기 비밀번호 1줄),
   `new-password.txt`(첫 로그인 변경용. 없으면 러너가 20자로 만들고 0600 으로 적는다).

## 2. 단계별 실행

```
python3 runner.py --phase login    --account <이메일> --base-url <주소>
python3 runner.py --phase accounts --accounts-file <0600 JSON> --base-url <주소>   # 선택
python3 runner.py --phase projects --base-url <주소>
python3 runner.py --phase datasets --base-url <주소>
python3 runner.py --phase verify   --base-url <주소>
python3 runner.py --phase report   --base-url <주소>
```

- `--phase all` = 위 여섯을 순서대로. `accounts` 는 `--accounts-file` 을 주지 않으면 건너뛴다.
- `--dry-run` = 브라우저를 건드리지 않고 실행될 `agent-browser` 명령만 출력. 상태도 쓰지 않는다.
- `--only-seq 3,5` = 그 순번만. `--from-seq 12` = 그 순번부터.
- `--force` = 이미 `done`·`blocked` 인 순번도 다시 실행(중복 등록이 생기므로 기본은 금지).
- `--project-type` = 프로젝트 유형(기본 `국가과제`). 정본에 지정이 없어 4건을 하나로 통일하고 `state.json` 에 적는다.
- `--plan` = 계획 파일 자리(기본 `<work-dir>/upload-plan.json`).
- `--accounts-file` = 계정 목록 JSON(0600). 주면 `accounts` 단계가 동작한다(§2-2).
- `--accounts-password-file` = 계정 초기 비밀번호 파일(0600). 없으면 **표준입력**으로 받는다.
- `--allow-argv-secret` = 비밀번호를 `fill` argv 로 넘기는 폴백 허용. 프로세스 목록에 노출되므로 기본 금지.

### 2-1. 「가공 단계」는 계획값을 매 행 명시 지정한다

- 러너는 등록 카드 ① 단계에서 `reg-level`(「가공 단계」)에 계획의 `processing_level` 을 **직접 넣는다.**
- **화면 기본값에 기대지 않는다** — 2026-09-13 회차는 이 칸을 한 번도 건드리지 않아 26건이 전부 `Lv2` 로 저장됐다.
  선택지가 빈 값으로 시작하도록 바뀌어도, 계보에서 자동으로 채우도록 바뀌어도 같은 동작이 선다.
- 계획값이 화면 선택지에 없으면 **그 순번만 이름을 실어 실패**시킨다(다른 행으로 옮겨 붙이지 않는다).
- 넣은 값은 `state.json` 의 그 행 `processing_level` 에 적히고 `--phase report` 표의 `Lv` 열에 나온다.
- 계보 부모가 자기 Lv 규칙 때문에 비활성이면 **우회하지 않는다** — 기존 실패 문면(부모 이름 포함)으로 멈춘다.

### 2-2. `accounts` — dev 초기화로 지워진 계정을 화면으로 되만든다

- 계정은 **계정 관리 화면**(`/account-admin` · `account-create`)으로만 만든다. API·DB 직접 쓰기 없음.
- 목록 파일 = JSON 배열. **권한이 0600 이 아니면 거절한다**(고쳐 주지 않는다).

```json
[
 {"email": "someone@example.com", "name": "홍길동", "role": "교수", "admin": true},
 {"email": "other@example.com",   "name": "김연구", "role": "연구원", "admin": false, "lab": "A 연구실"}
]
```

| 칸 | 필수 | 뜻 |
|---|---|---|
| `email` · `name` | 필수 | 화면의 「이메일」·「이름」 |
| `role` | 필수 | `교수` 또는 `연구원` 2값. 그 밖의 값은 거절 |
| `admin` | 필수 · 불 값 | 참이면 「관리자로 등록」 체크. 문자열 `"yes"` 는 거절 |
| `lab` | 선택 | 「연구실」 선택지의 **보이는 이름**. 없으면 화면이 고른 것을 그대로 둔다 |

- **비밀번호는 이 파일에 두지 않는다** — 파일에 `password`·`initialPassword` 칸이 있으면 거절한다.
  값은 `--accounts-password-file`(0600) 또는 표준입력으로 받고, argv·로그·`state.json`·JSON 어디에도 남지 않는다.
- 「첫 로그인 비밀번호 변경 강제」는 **화면에 칸이 없다** — 서버가 늘 강제한다. 러너는 건드리지 않는다.
- 결과는 `state.json` 의 `accounts.<이메일>` 에 `{email·name·role·admin·status·message·at}` 로 적힌다.
  `status` = `created` · `failed`. `created` 인 항목은 재실행에서 건너뛴다(`--force` 로만 다시 만든다).
- 진행 관찰 = `python3 watch.py`(같은 `--work-dir` 을 준다).

## 3. 상태 · 로그 · 갈무리

| 자리(작업 자리 아래) | 내용 |
|---|---|
| `state.json` | 단계별 status · 프로젝트 id · 데이터셋 id · 시각 · 소요 · 통한 선택자 · 계정 결과 |
| `logs/run-<시각>.log` | 실행된 명령과 판정 줄. 비밀번호는 `stdin = 비밀 스크립트` 로만 남는다 |
| `shots/<순번>.png` | 순번별 등록 직후 화면 |
| `shots/verify-preview-<순번>-<포맷>.png` | 미리보기 렌더 확인 5장 |
| `fail/<순번>-failed.png` · `.txt` | 실패 자리 화면 ＋ `snapshot -i` ＋ 본문 문자열 |
| `verify.json` | 데이터셋 계수 · 간선 계수 · 미리보기 판정 · 미달 목록 |

`state.json` 의 데이터셋 한 행 —

| 칸 | 값 |
|---|---|
| `processing_level` | 화면에 넣은 「가공 단계」(`Lv0`~`Lv3`). 넣기 전 행에는 없다 |
| `status` | `running` · `done` · `registered_no_preview` · `blocked` · `failed` |
| `analysis_failed` · `analysis_failure_reason` | 분석 실패에서 등록으로 이은 행에만 붙는다(화면 축자) |
| `blocked_reason` | `blocked` 인 행의 사유. `reg-open` 이 비활성으로 남은 자리만 여기 온다 |

- **`done` 과 `registered_no_preview` 는 둘 다 「등록됨」으로 센다**(계수·건너뛰기·`verify`).
  `done` 은 옛 상태 파일의 값이라 그대로 읽는다 — 옛 `state.json` 을 그대로 이어 써도 된다.
  `accounts` 칸이 없는 옛 파일도 그대로 읽는다(빠진 칸만 채운다).

## 4. 재개

- 데이터셋 단계는 실패한 순번에서 **비영 종료(2)** 한다. 자동 재시도 없음 — 등록 확정은 되돌릴 수 없다.
- 원인을 `fail/` 에서 확인한 뒤 같은 명령을 다시 낸다. `done` 인 순번은 건너뛰고 실패 순번부터 잇는다.

```
python3 runner.py --phase datasets --from-seq <실패 순번> --base-url <주소>
```

- 로그인 상태가 끊겼으면 `--phase login` 을 먼저 낸다. `state.json` 의 `password_rotated` 가 참이면
  `new-password.txt` 로 로그인한다.
- 화면에서 데이터셋을 지우는 길은 없다(서버 501). 오입력은 초기화 전까지 남는다 — 시나리오 9 절.

## 5. 시간 상한

- 업로드·분석 대기 = `60초 + 10초/MB + 5초/파일`(데이터＋격자 기준 · 상한 6시간).
- ⚠ **파일 수도 센다** — 바이트만으로 재면 순번 16(72건)·18(143건) 처럼 작은 파일이 많은 묶음이 짧게 끊겼다.

## 6. 지목점(testid)이 없을 때 — 6자리

러너는 자리마다 후보를 차례로 시도하고, **통한 후보를 `state.json` 의 `selectors` 에 적어**
다음 실행에서 먼저 쓴다. 어느 후보가 통했는지는 로그에 `지목점 <key> <- <종류>:<값>` 으로 남는다.

### 6-1. 라벨·문구로 지목하는 3자리 (능력문 6 절 「혼합」)

| 자리 | 1순위 | 폴백 순서 |
|---|---|---|
| 프로젝트 모달의 칸 | 라벨 `이름` · `설명` | `id` 접미 선택자 `[data-testid="project-form-modal"] input[id$="-name"]` · `... [id$="-desc"]`. 접두는 실행 시 생성값이라 고정으로 쓰지 않는다 |
| 연관 프로젝트 「추가」 버튼 | 역할 `button` ＋ 이름 `추가` | 문구 `추가` · 형제 선택자 `[data-testid="reg-proj-select"] ~ button` |
| 모달 안 프로젝트 빠른 생성 | `reg-proj-quick-open` | 문구 `+ 새 프로젝트 만들기` → 안쪽 칸은 `aria-label` 지목. **기본 흐름에서는 쓰지 않는다**(프로젝트 4건을 먼저 만들어 두므로) |

- 새 프로젝트 여는 버튼도 testid 가 없다 — `.pj-new` → `project-new` → 역할 `button` 이름 `새 프로젝트` → 문구 `+ 새 프로젝트` 순.
- ⚠ 「+ 추가」는 `click` 이 성공을 돌려주고도 React 의 onClick 이 동작하지 않았다(모달 스크롤 밖 좌표).
  러너는 그 자리에서 **보이는 자리로 옮기고 초점 ＋ Enter** 로 누른다.

### 6-2. 실행 시 화면에서 확인할 3자리 (능력문 6 절 「실행 시 확인」)

| 자리 | 대체 수단 | 미달일 때 |
|---|---|---|
| `/datasets` 목록 계수 | 화면 머리의 「N건」(`.catalog-page .hcnt`) | ⚠ **표 행을 세지 않는다** — 목록 계약의 `limit` 기본값이 20 이고 화면은 `limit` 을 보내지 않아 표는 한 쪽(20행)에서 잘린다. 머리의 수는 서버가 준 `totalCount` 라 잘리지 않는다. 머리를 못 읽으면 본문의 같은 꼴 → 표 행 수 순으로 내려가고, 그때는 방법 문자열에 「쪽 잘림 가능」이 남는다 |
| `/projects` 목록 계수 | `[data-testid^="project-card-"]` 카드 수 | 카드가 없으면 이름 문자열 포함 여부로 존재만 판정하고 id 는 `null` 로 남는다(계보에 쓰지 않으므로 진행에 지장 없음) |
| `/account-admin` 칸 | 이 러너는 계정을 추가하지 않는다(시나리오 3 절 기본값) | 계정 추가가 필요해지면 그 화면의 `snapshot -i` 를 먼저 떠서 칸 이름을 확인한 뒤 라벨 지목으로 붙인다 |

### 6-3. 기준 격자 — 순서가 판정을 가른다

- ⚠ **격자 칸은 등록 결정 게이트(「다음 →」)를 먼저 연 뒤에 붙는다.** 격자 블록은 미리보기 렌더 결과
  (「좌표 없음」)에서만 생기기 때문이다(`PreviewPanel.tsx` · `gridFlow.ts`). 러너의 순서는
  분석 완료 → `reg-open` → 격자 지정 → 2단계 확인이고, 이 순서를 바꾸면 격자가 붙지 않는다.
- 전체 파일 기준 미리보기가 도착하면 판정이 「위치 확인」으로 되돌아온다. 그때 「맞습니다」를
  **다시** 누르지 않으면 기준 격자가 붙지 않는다(러너가 등록 직전에 한 번 더 확인한다).
- 경계 위생 실패(한반도 밖)는 등록을 막지 않는다 — 지도형만 안 생긴다. 기록하고 이어간다.
  형상·축·짝 불일치와 `up-grid-mismatch` 는 판정이 필요하므로 멈춘다.
- **격자 대기는 두 단이다**(⭑ 2026-09-24 · dev 4회차 seq 18 846초 정체). 1단은 판정 표시 또는
  서버 격자 수용 = 「예상 영역」(`up-grid-expected-bounds`, grid-options `currentGrid` · 렌더와 무관)을
  기다린다. 수용 뒤 2단은 전체 파일 렌더의 판정(「맞습니다」 등)을 상한 안에서 본다.
  렌더가 실패(`up-preview-error` · 진행 표시 없음)하거나 상한(`COLAB_SEED_GRID_RENDER_WAIT_S`,
  기본 300초)을 넘기면 — 계획 `preview_expected` 가 「렌더 성립…」인 행은 **멈추고**, 그 밖의 행은
  등록을 잇는다. 상태 `registered_no_preview` · 사유 `no_preview_reason` · 목록 `grid_render_unverified`.
  「맞습니다」는 미리보기 칸의 표시 상태만 바꾸고(`UploadModal` 이 `onAccept` 을 넘기지 않는다)
  격자 파일은 업로드에 이미 「기준 격자 파일」로 실려 등록된다.

### 6-4. 계보 행 지목

- 부모 행은 `lin-pick-<데이터셋 id>` 로 데이터셋 id 에서 파생된다. id 는 부모 순번을 끝낼 때
  `state.json` 에 적히므로 **부모 먼저** 원칙(계획의 `seq` 순서)을 깨면 안 된다.
- 행이 목록에 없으면 층 거르개(`lin-lv-filter`)를 한 번 눌러 좁힌 뒤 다시 찾고, 그래도 없으면 실패로 멈춘다.
- ⛔ `lin-ask`(AI 제안 받기)는 **누르지 않는다.** 계보는 사람이 고른 값으로만 세운다.

## 7. 멈추는 자리 · 건너뛰는 자리

멈춘다(자동 진행하지 않는다) —

- 기준 격자 불일치(`up-grid-mismatch`) · 형상·축·짝 불일치 — 판정이 필요하다.
- 「데이터셋 만들기」가 비활성 — 자기 Lv 를 넘는 연결이 남았다는 뜻이다.
- 로그인 거절(`login-error`) — 자격 행부터 다시 본다. 401 이 5건 쌓이면 429(창 900초 · 한도 5).
- 「가공 단계」 계획값이 화면 선택지에 없다 — 그 순번만 이름을 실어 멈춘다.

분석이 실패해도 **등록은 잇는다**(⭑ 2026-09-14 개정) —

- 분석 실패 표시(`up-analysis-failure` 등)를 받으면 실패 자리를 `fail/` 에 갈무리한 뒤
  **`reg-open` 이 활성이 될 때까지 기다렸다가 정상 경로와 똑같이 등록한다.**
  상태는 `registered_no_preview` 이고 실패 문면은 `analysis_failure_reason` 에 남는다.
- ⛔ 「보기만 할게요」(`reg-viewonly`)는 **쓰지 않는다** — 등록하지 않고 닫는 길이라 데이터셋이 생기지 않는다.
  2026-09-13 회차는 그 길로 가서 `.gpkg` 2건이 아예 만들어지지 않았다(§9).
  화면은 그 뒤 분석 실패에서도 등록을 허용하도록 바뀌었다(배너 축자 「등록은 됩니다」).
- 미리보기 렌더를 판정하는 5순번도 같다 — 등록해 두어야 `verify` 가 그 데이터셋을 볼 수 있다.

건너뛴다(`blocked` 로 적고 다음 순번으로) —

- 기다린 뒤에도 `reg-open` 이 비활성으로 남은 자리 **하나뿐이다.** 사유를 `blocked_reason` 에 적는다.

## 8. 비밀 취급

- 비밀번호는 `agent-browser` 의 표준입력 경로로만 들어간다(페이지 안에서 입력칸 값을 직접 설정).
  argv·로그·화면 갈무리 어디에도 값이 남지 않는다.
- 표준입력 경로가 실패하면 러너는 멈춘다. `--allow-argv-secret` 를 준 경우에만 `fill` 로 넘어간다.
- `accounts` 단계의 초기 비밀번호도 같다 — `--accounts-password-file`(0600) 또는 표준입력이고,
  동작 목록·로그 줄·`state.json` 에는 자리표 `***` 만 남는다(시험 = `tests/test_runner_plan_mapping.py`).
- 자격 파일 권한 판정이 두 갈래다 — 옛 `initial-password.txt`·`new-password.txt` 는 0600 으로 **조여 주고** 잇고,
  `--accounts-file`·`--accounts-password-file` 은 **거절한다**(사람이 만들어 넣는 파일이라 조용히 고치지 않는다).

## 9. 오늘 실측 (2026-09-13 dev 초기화 회차)

| 항목 | 값 |
|---|---|
| 등록 | 26 / 28 |
| 차단 | 2 — `SPI-4weeks` · `SPEI-4weeks`(`.gpkg`). 화면 축자 「파일 분석을 마치지 못했어요 · 형식 인식 실패」 · 「다음 →」 비활성 |
| 계보 간선 | 18 / 18 |
| 프로젝트 | 4 / 4 |
| 투입량 | 파일 543건 · 자료 3,641,736,593 B ＋ 기준 격자 1,534,685,472 B |
| 미리보기 | 5포맷 중 `nc` 만 그려짐. `grib`·`bin`·`tif`·`hdf4` 는 안 그려짐 — **원인 미진단** |

실행 중에 고친 것 3 — **코드 대조 결과**(2026-09-14 · `runner.py` 실물과 맞춰 봤다) —

1. **기준 격자 순서** — 격자 칸을 먼저 찾다가 못 찾았다. 등록 결정 게이트를 먼저 열어야 격자 블록이 붙는다(§6-3).
   → **이미 반영** · `do_dataset` 이 `open_register` → `do_grid` 순서로 부른다.
2. **`.gpkg` 차단** — 분석 실패에서 전체를 멈추던 것을 「보기만 할게요」로 닫고 건너뛰도록 바꿨다.
   → **2026-09-14 에 되돌렸다** · 그 길은 등록하지 않고 닫는 길이라 데이터셋이 생기지 않았다.
   지금은 `reg-open` 을 기다렸다가 등록으로 잇는다(`registered_no_preview` · §7).
3. **대기 상한** — 바이트만으로 재던 상한에 파일 수(5초/건)를 더했다. 작은 파일 수십~백여 건 묶음이 끊겼다(§5).
   → **이미 반영** · `analyze_timeout(nbytes, nfiles)` = `60 + 10/MB + 5/파일` · 상한 6시간.

⚠ `R-DEV-RESET.md §12` 는 「실행 중 정정 **7건** 반영 완료」로 적는다. 위 3건은 이 README 가
적어 둔 세 가지이고, 7 과 3 은 **기준이 다른 계수**다(§12 는 회차 전체의 정정 수).

이 회차(2026-09-14 · WU-C1b)에서 바뀐 것 3 —

1. **「가공 단계」 명시 지정** — 26건이 전부 `Lv2` 로 저장된 원인은 러너가 그 칸을 한 번도 건드리지 않은 것이었다(§2-1).
2. **분석 실패 → 등록** — 「보기만 할게요」를 걷어내고 `reg-open` 을 기다려 등록으로 잇는다(§7).
3. **`accounts` 단계** — dev 초기화로 지워지는 계정을 화면으로 되만든다(§2-2).

⚠ **브라우저 실행 증명은 이 회차에 없다.** 위 3건은 단위 시험(`tests/test_runner_plan_mapping.py` 17건)과
`--dry-run` 까지만 확인했다. 실화면 확인은 다음 dev 실투입 회차가 진다.

확인 단계에서 드러난 것 1 — 목록 표 행을 세면 26건을 넣고도 20 이 나온다(쪽 잘림). 계수는 머리의 「N건」으로 읽는다(§6-2).

미결 1 — 미리보기 4포맷 미렌더의 원인 진단. 이 도구의 결함인지 미리보기 뒷단의 결함인지 아직 가르지 않았다.

### reseed 배포 계획

`dev-package/tools/dev-reseed/reseed.sh --release-plan <계획.json>`의 deploy 단계는
현재 HEAD/후보 full SHA와 계획의 단일 `dv` 대상이 같은지 확인한 뒤, 보호된 임시 폴더(0700)의
계획 사본(0600)을 기존 executor `--check`와 `run`에 함께 전달한다. 원본 파일이 바뀌어도
검증한 사본의 내용으로 실행한다. 직접 build/ship/tree/up/web/doctor 호출은 중복하지 않는다.
reset/bootstrap 뒤의 `stage_up` 재기동·검증은 유지한다.

계획은 기존 `colab-deploy/1` 계약을 따른다: 단일 dev 대상과 full SHA, 비어 있지 않은 deploy/verify
argv, 입력 파일 해시, 유효한 pre-evidence와 이번 verify에서 새로 만드는 post-evidence가 필요하다.
deploy 명령은 build/ship/tree/up/web 등 필요한 배포 작업을 포함해야 하며 `reseed.sh`를 다시
호출하는 재귀 계획은 거절한다. executor의 managed/pre/post 검사와 알림 정책은 유지한다.
executor 알림은 배포 결과이며 전체 reseed 완료를 뜻하지 않는다.

계획 부재/검사·실행 실패는 reset 전에 중단한다. 상대 계획 경로는 명령을 시작한 폴더 기준이다.
`--rehearse`는 같은 계약의 `--check`만 수행하고 기존 원격 읽기 리허설로 이어진다.
`--dry-run`은 계획 읽기·executor 실행도 하지 않는다.
로컬 `tests/deploy-rehearsal.sh`는 격리 연결 시험이며 실제 EC2 배포 준비성을 증명하지 않는다.
