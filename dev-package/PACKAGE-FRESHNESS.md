# PACKAGE-FRESHNESS — 전달 패키지 최신성 스냅샷

> **마지막 실측: 2026-08-22** (WU-G1)
> 이 파일은 **스냅샷**이지 오라클이 아니다. 상시 오라클은 `./gates/run.sh planning-freshness` 다.
> 판정은 **내용 해시로만** 한다 — 파일명·mtime 은 판정 입력에서 배제한다.
> 정본 8개 패키지의 mtime 은 전부 같고(Drive 동기화 시각), 파일명 `260817` 은 내용(08-18 개정 반영)과 다르다.

## 1. 판정 — 15개 임베드 블록 **전부 일치 (15/15 MATCH)**

| 에픽 | 임베드 블록 | 원본 문서 | 원본 version | 판정 | sha256(앞 8) |
|---|---|---|---|---|---|
| E-00 공통 기반 | `md-prd` | `DataModel_공통_기반.md` | 1.8 | ✅ MATCH | `5e307ca4` |
| E-00 공통 기반 | `md-policy` | `Policy_공통_기반.md` | 1.4 | ✅ MATCH | `68df5dfe` |
| E-01 역할과 권한 | `md-policy` | `Policy_역할과_권한.md` | 1.3 | ✅ MATCH | `533c6d6a` |
| E-02 데이터 찾기 | `md-prd` | `PRD_데이터_찾기.md` | 1.1 | ✅ MATCH | `4fe6f458` |
| E-02 데이터 찾기 | `md-policy` | `Policy_데이터_찾기.md` | 1.8 | ✅ MATCH | `4ef1327a` |
| E-03 데이터셋 상세 | `md-prd` | `PRD_데이터셋_상세.md` | 1.2 | ✅ MATCH | `09bc2e6c` |
| E-03 데이터셋 상세 | `md-policy` | `Policy_데이터셋_상세.md` | 2.1 | ✅ MATCH | `f9700f18` |
| E-04 업로드와 계보 확정 | `md-prd` | `PRD_업로드와_계보_확정.md` | 1.2 | ✅ MATCH | `a7bd83c6` |
| E-04 업로드와 계보 확정 | `md-policy` | `Policy_업로드와_계보_확정.md` | 2.2 | ✅ MATCH | `cf009cce` |
| E-05 프로젝트 | `md-prd` | `PRD_프로젝트.md` | 1.3 | ✅ MATCH | `15ecab24` |
| E-05 프로젝트 | `md-policy` | `Policy_프로젝트.md` | 1.6 | ✅ MATCH | `dc30b87c` |
| E-06 승인 처리 | `md-prd` | `PRD_승인_처리.md` | 1.2 | ✅ MATCH | `746d799d` |
| E-06 승인 처리 | `md-policy` | `Policy_승인_처리.md` | 1.7 | ✅ MATCH | `0ac2a5a7` |
| E-07 홈 대시보드 | `md-prd` | `PRD_홈_대시보드.md` | 1.3 | ✅ MATCH | `8a05946a` |
| E-07 홈 대시보드 | `md-policy` | `Policy_홈_대시보드.md` | 1.5 | ✅ MATCH | `223d844f` |

짝 없는 임베드 블록 **0건**, 임베드되지 않은 원본 문서 **0건**.
E-01 은 원본이 Policy 1종뿐이라 임베드 블록도 `md-policy` 하나다 — 누락이 아니다.
P1 은 1차 범위 밖이라 검사 대상에서 빠진다 (`E-*` 폴더만 훑는다).

## 2. 오라클 2 — v1.8/v1.4 신설 항목이 E-00 임베드 본문에 실재하는가

| 신설 항목 | 임베드 본문 |
|---|---|
| front matter `version: 1.8` (DataModel) · `version: 1.4` (Policy) | ✅ 각 1건 |
| 레코드 시점 3종 | ✅ 5회 |
| 계보 상태 4값 | ✅ 4회 |
| `연구실 설정` (권한 스위치 4종 · GNB) | ✅ 7회 |
| 업로드 전체 화면 모달 | ✅ 3회 |
| 데이터셋 : 파일 1:N | ✅ 서술형 — "데이터셋 하나에 파일이 여러 건 붙는다" |
| 프로젝트 N:N | ✅ 서술형 — "다중 연결로 확정한다 … 여러 건을 지정하고 여러 건을 보여준다" |

> 마지막 두 항목은 정본이 `1:N`·`N:N` 표기를 쓰지 않고 문장으로 적는다. 표기 부재는 미반영이 아니다.

## 3. 이 게이트가 보지 **않는** 것

**문서 임베드만 본다.** 화면·목업 최신성(E-02 카탈로그 표 헤더 리뉴얼, E-04 08-17 리뉴얼 등)은 판정하지 않는다.
그쪽은 **WU-G1b** 다. 여기가 green 이라고 목업이 최신이라는 뜻이 아니다.

## 4. 재현

```bash
./gates/run.sh planning-freshness                              # 정본 마운트 후
python3 dev-package/tools/check-package-freshness.py --selftest # fail-closed 증명
```

정본이 마운트돼 있지 않으면 게이트는 **red** 를 낸다. skip 하지 않는다 (`CLAUDE.md §4`).
정본 위치는 `planning/README.md §1`. 검사기는 `COLAB_PLANNING_ROOT` 환경변수 또는 첫 인자로 루트를 덮어쓸 수 있다.
