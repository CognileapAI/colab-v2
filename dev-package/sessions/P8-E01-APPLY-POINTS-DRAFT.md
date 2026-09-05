# P8 — E-01 화면별 적용 지점 표 **초안** (정본 미반영)

> **회차** 2026-09-02 · 워크트리 `.claude/worktrees/lane-p8` · 브랜치 `lane-p8` (off `main` @ `ac3c8fc`)
> **대상 WU** `work-items.yaml` `P8` — 「E-01 화면별 적용 지점 표 → 정책·패키지 재생성」(`WORK-UNITS.md:440`)
> **완료 정의** 「각 P 의 완료 판정」 4항 (`WORK-UNITS.md:245-250`) — 확정본이고 초안이 아니다(`completion_def_draft` 없음).

## 0. 이 문서가 무엇이고 무엇이 아닌가

**정본이 아니다. 정본에 실을 값의 초안이다.**
값이 앉을 자리는 레포 **밖** `40 COLAB-기획/…/E-01_역할과_권한/documents/Policy_역할과_권한.md` 의 `# 나. 화면별 적용 지점 표` 절이고, 그 절은 지금 비어 있다(축자 「⏸ E-07 완료 후 작성한다」).

**이 회차는 그 절을 고치지 않았다 — 파일 수정 0건이다.** 사유 둘 —

1. `PLAN-SoT §9` 선례(`〈232〉`·`〈233〉`·`〈245〉`·`〈254〉`)는 기획 정본 개정을 전부 **「Ted 판정 ＋ 집행 ＋ 결정 번호」**로 처리했다. 이 레인은 **결정 번호 발급이 금지**돼 있다(최신 `〈278〉`).
2. 정본이 예고한 것은 **표가 생긴다는 사실**이지 **표에 무엇이 적히는가**가 아니다. 각 행의 「보이는 조건 / 안 보일 때」는 제품 판정이다.

⟹ **판정 대기 2건**은 `dev-package/notes/P8-LEDGER-PENDING.md`.

**축 A 만 판정한다.** 데이터 잠김(축 B)의 값 정본은 E-06 적용 지점 표다(`Policy_역할과_권한 §4` 축자 「값의 정본은 승인 처리(E-06) 적용 지점 표」 · `Policy_승인_처리 §8` 7곳). 여기서 다시 적지 않는다 — 두 축을 한 메커니즘으로 합치지 않는다(`P-14` · `frontend/src/permission/PermissionGate.tsx:2`).

**「E-07 완료 후」의 대조** — E-07 = `P7`(연구실 대시보드) = `done`(`〈273〉` · `work-items.yaml:1098`). 화면 에픽 대조 = E-02 카탈로그 `P1` ✅ / **E-02 검색 `P4` 는 `after_stage2`**(`〈268〉`) / E-03 `P3` ✅ / E-04 `P2` ✅ / E-05 `P5` ✅ / E-06 `P6` ✅ / E-07 `P7` ✅. 검색 화면에는 축 A 적용 지점이 **0건**이라(조회에 스위치 차이가 없다) 미구현이 표의 결손을 만들지 않는다 — 근거는 §3 ㉮.

---

## 1. 표 초안 — 정본 5열 그대로 (`화면 | 요소 | 보이는 조건 | 안 보일 때 | 관련 정책`)

### 1.1 화면에서 숨기는 자리 — `PermissionGate` 실물 9곳

| 화면 | 요소 | 보이는 조건 | 안 보일 때 | 관련 정책 | 출처(실물) | 원칙 대조 |
|---|---|---|---|---|---|---|
| 공통 셸 · GNB | `업로드` 버튼 | `업로드·편집` 켜짐 | DOM 에서 사라진다. 비활성 버튼·안내 토스트를 두지 않는다 | §4 · §1.3-3 | `frontend/src/shell/Gnb.tsx:87` `업로드·편집` | 일치 |
| 공통 셸 · GNB | `연구실 설정` 링크 | `연구실 설정` 켜짐 | 숨긴다 | §4 · §2 | `frontend/src/shell/Gnb.tsx:92` `연구실 설정` | 일치 |
| 업로드 전체화면 모달 S-04 | 모달 진입 버튼 | `업로드·편집` 켜짐 | 숨긴다 (진입 자리 자체가 없다) | §4 | `frontend/src/components/upload/UploadEntry.tsx:38` `업로드·편집` | 일치 |
| 업로드 모달 S-04 · 등록 영역 | `+ 새 프로젝트`(빠른 생성) | `프로젝트 생성` 켜짐 | 숨긴다. 인라인 유지 — 모달 위에 모달을 얹지 않는다 | §4 · `Policy_프로젝트 §6` | `frontend/src/components/upload/RegisterArea.tsx:259` `프로젝트 생성` | 일치 |
| 데이터셋 상세 S-05 | `기준 격자 추가` | `업로드·편집` 켜짐 | 숨긴다 | §4 · `Policy_데이터셋_상세 §6` | `frontend/src/components/upload/GridAttachEntry.tsx:42` `업로드·편집` | 일치 |
| 데이터셋 상세 S-05 · 미리보기 | `스크린샷` | `업로드·편집` 켜짐 | 숨긴다 | §4 · `Policy_데이터셋_상세 §6` | `frontend/src/components/datasetpreview/ScreenshotButton.tsx:84` `업로드·편집` | 일치 |
| 프로젝트 목록 S-02 | `+ 새 프로젝트` | `프로젝트 생성` 켜짐 | 숨긴다 | §4 · `Policy_프로젝트 §6` | `frontend/src/routes/ProjectsPage.tsx:36` `프로젝트 생성` | 일치 |
| 연구실 홈 S-01 · 연구실 정보 모달 | `연구실 정보 편집` | `연구실 설정` 켜짐 | **모달은 열린다 — 버튼만 숨긴다.** 읽기는 전 구성원 | §6 · `Policy_홈_대시보드` | `frontend/src/components/dashboard/LabInfoModal.tsx:61` `연구실 설정` | 일치 |
| 연구실 설정 S-07 · `연구실 정보` 탭 | `정보 편집` | `연구실 설정` 켜짐 | **탭 본문은 그린다 — 버튼만 숨긴다.** 읽기는 전 구성원 | §6 · 나-2 | `frontend/src/components/lab/LabInfoPanel.tsx:108` `연구실 설정` | 일치 (신설 `〈292〉` · 2026-09-03) |
| 데이터셋 상세 S-05 · 파일 목록 | `파일 추가` | `업로드·편집` 켜짐 | 숨긴다 | §4 · `Policy_데이터셋_상세 §5` | `frontend/src/components/detail/FileList.tsx:186` `업로드·편집` | 일치 (신설 `〈341〉`·`〈339〉` · PR #1 병합 창 8-a) |
| 연구실 홈 S-01 · 올리다 만 업로드 | 구획 전체 | `업로드·편집` 켜짐 | 숨긴다 (구획 자체가 없다) | §4 · `S3.md §3` | `frontend/src/routes/LabPage.tsx:48` `업로드·편집` | 일치 (신설 `〈342〉` · PR #1 병합 창 8-a · **정본 개정 판정 대기**) |

### 1.2 서버가 같은 기준으로 막는 자리 — 화면에서 숨긴 것을 서버가 다시 판정한다 (`P-11`)

| 화면 · op | 판정 스위치 | 막힐 때 | 관련 정책 | 출처(실물) |
|---|---|---|---|---|
| 업로드 접수 | `업로드·편집` | 403 | §4 · `〈59〉-②` | `services/core-api/src/colab_core/app/routes/ingestion.py:172` |
| 미리보기 생성 | `업로드·편집` | 403 | `Policy_업로드와_계보_확정 §8` | `services/core-api/src/colab_core/app/routes/preview.py:165` |
| 계보 수정 | `업로드·편집` | 403 | `Policy_데이터셋_상세 §6` | `services/core-api/src/colab_core/app/routes/lineage.py:43` |
| 데이터셋 상세 `canEditLineage` | `업로드·편집` **＋ 본체 접근 가능** | 값 `false` — 화면이 자리를 안 그린다 | §4 · `P-14`(두 축의 곱) | `services/core-api/src/colab_core/app/routes/catalog.py:615` |
| 프로젝트 **모든 쓰기 동작** | `프로젝트 생성` | 403. 조회에는 권한 차이가 없다 | `Policy_프로젝트 §6` | `services/core-api/src/colab_core/app/routes/project.py:86,121,368,417` |
| 연구실 정보 편집 | `연구실 설정` | 403. 읽기는 전 구성원 | §6 · `〈150〉` | `services/core-api/src/colab_core/app/routes/identity.py:52` |
| `연구실 설정 > 구성원 · 권한` 화면 | `연구실 설정` | 403 — **이 화면 자체가 없다** | §3 · `P-18` | `services/core-api/src/colab_core/app/routes/members.py:46` |
| 구성원 권한 저장 · 위임자 | `연구실 설정` 위임자는 **`업로드·편집`·`프로젝트 생성` 두 열만** | 나머지 두 열은 교수만 — **재위임 금지** | §6 · `P-31` | `services/core-api/src/colab_core/app/routes/members.py:26` |
| 받은 접근 요청 조회·처리 | `승인 위임` (교수는 네 스위치가 항상 켜짐 · `P-5`) | 403 | §6 · `Policy_승인_처리 §1.2` | `services/core-api/src/colab_core/domains/d2_access.py:295` |
| Verified 검토·승인·취소 | **스위치 없음 — 교수 전용. 위임되지 않는다** | 403 | §2 · `P-22` · `Policy_승인_처리 §1.2` | `services/core-api/src/colab_core/domains/d2_access.py:298-302` · `routes/access.py:251` |

### 1.3 할 일 함 — 권한 훅이 카드가 아니라 **그룹**에 걸린다 (§6.1)

| 그룹 | 보이는 조건 | 안 보일 때 | 관련 정책 | 출처(실물) |
|---|---|---|---|---|
| 계보 확인 | **전원.** 조건 없음 | — (항상 보인다) | §6.1 · `Policy_승인_처리 §8` | `frontend/src/components/dashboard/TodoInbox.tsx:66` |
| Verified 검토 대기 | 교수 | 그룹을 통째로 그리지 않는다 | §6.1 · `P-22` | `frontend/src/components/dashboard/TodoInbox.tsx:106,111` |
| 받은 접근 요청 | 교수 · `승인 위임` 연구원 | 그룹을 통째로 그리지 않는다 | §6.1 | `frontend/src/components/dashboard/TodoInbox.tsx:223` |

---

## 2. 정본과 실물의 불일치

**불일치 0건.** 축 A 8곳 · 서버 10자리 · 할 일 함 3그룹 전부가 `가. 원칙`(§2·§4·§6·§6.1)과 `PERMISSION-PRINCIPLES.md` `P-3`·`P-5`·`P-6`·`P-11`·`P-12`·`P-14`·`P-18`·`P-22`·`P-31` 에 그대로 대응한다.

`[미확인]` 1건 — **검색 결과 S-06 의 축 A 적용 지점.** 화면이 `after_stage2`(`P4`)라 실물이 없다. 조회에 스위치 차이가 없다는 것이 `Policy_프로젝트 §6`·`project.py:318` 의 선례이고 검색도 같을 것이라는 것은 **추론이다** — `P4` 착수 회차가 실측해 이 표에 행을 더하거나 「해당 없음」을 확정한다.

---

## 3. 판정 근거로 쓴 것과 쓰지 않은 것

- ㉮ **표는 코드에서 유도하지 않았다.** 열과 형식은 정본 `Policy_역할과_권한.md:155-157`, 값의 근거는 `가. 원칙` §2·§4·§6·§6.1 이다. 코드 출처는 **그 원칙이 실제로 걸린 자리를 증명하는 것**이지 정책의 원천이 아니다. 코드가 원칙과 갈리는 칸은 값이 아니라 §2 의 발견으로 적는다.
- ㉯ **재발 방지 시험** = `frontend/test/e01-apply-points.test.ts`. §1.1 표와 `PermissionGate` 실물을 **집합으로** 대조한다. 적용 지점이 늘거나 줄면 red 다 — 표가 조용히 낡는 것을 막는다.
- ㉰ **재지 않은 것** — 목업 대비 화면 검증(E-01 은 전용 화면·목업이 없다) · staging 배포 green(이 레인은 배포 금지).
