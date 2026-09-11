# 배포 시험 미리보기 10키의 증거 보존

사용자 「실패해결」 요청에 대한 캐시 판정 처리다. 삭제·원장 복원 승인은 없으며, 기존 exact-key 보존 정책 안에서 현재 오케스트레이터가 아래 시험 증거를 보존하기로 결정한다. 고아가 없어졌다고 보고하지 않는다.

## 원인과 구분

현재 로컬 staging 산출물 158벌의 판정은 살아 있음 120·고아 19·구판 판정 불가 19다. 고아 19 중 기존 보존 9키와 신규 미선언 10키는 중복되지 않는다. 이번에 추가하는 것은 **10키·22파일·551,809바이트**다. 구판 19벌의 기존 정책은 변경하지 않는다.

신규 10키는 2026-09-10 수행한 GRIB2/HDF5 배포 시험 업로드 4건에 대응한다.

| 업로드 | 시험 파일 | 만료 시각(KST) | 캐시 키 수 | 파일 바이트 |
|---|---|---|---:|---:|
| 01M249J3YCD64SPDWYNHZFWRAQ | DEPLOY-E2E-89a28d9c0fd5-GRIB2.grib2 | 2026-09-11 08:55:27 | 3 | 6,634 |
| 01M249JCD1GW4EVEWXTTC0BK0D | DEPLOY-E2E-89a28d9c0fd5-HDF5.h5 | 2026-09-11 08:55:36 | 2 | 963 |
| 01M24HFH6A2DWJWRGQ6CBFE1HN | genuine-multivariable-09e2b9b.h5 | 2026-09-11 11:13:51 | 2 | 241,994 |
| 01M24HJ60QX5FWEDQGMM74PPJ0 | surface-first-32.grib | 2026-09-11 11:15:18 | 3 | 302,218 |

실행 중인 로컬 staging worker는 `09e2b9b2db1a`다. 그 버전의 `services/pipeline-worker/src/colab_pipeline/domains/d5_ingestion.py`에서 `reap_expired_uploads()`가 `SqlLedger.expire()`를 호출해 미등록 업로드 원장만 만료 삭제한다. 미리보기는 남아 연결이 끊긴다. 현재 main의 같은 함수는 이 단독 삭제를 하지 않으며, AWS dev에 배포된 `9e3ff19f6d27`에도 반영돼 있다. **구버전 로컬 staging의 재발 원인을 이번 보존 선언이 고친 것은 아니다.**

## 영속 근거

정확한 10키, 22파일의 상대 경로·크기·SHA256, v2 sidecar의 source와 생성시각, DB 백업 대조를 [cache-retention-evidence.json](../reports/stage12-failure-fix/cache-retention-evidence.json)에 고정했다. 부모가 현재 파일의 해시·총량과 백업 내 시험 업로드 식별자 4개를 직접 대조했다.

- 파일 원본: `/home/ttlhi10/.colab-v2-staging/previews/`의 해당 exact-key 파일. 이동·수정·삭제하지 않는다.
- DB 백업: `/home/ttlhi10/colab-v2-backups/staging/platform-20260911T033002.sql.gz`, 47,873바이트, SHA256 `baa0fee00a62624ce78b49ee7b53023f08a916d0db8bf622bbb35b6f710de915`.
- 백업에는 업로드·파일 행과 24시간 만료 시각이 있고 현재 원장에는 없다. 운영 DB에는 읽기 전용 조회만 수행했다. 백업 전체 SQL이나 접속 비밀은 저장소에 넣지 않는다.
- 최초 실패 근거: `reports/stage12-deployed-supplement/artifact-ownership/run.log`. 신규 키는 이 실패가 출력한 미선언 10키와 정확히 일치한다.

## 책임·범위·해제 조건

현재 배포 오케스트레이터가 증거 보존의 책임을 맡는다. 검사기는 변경하지 않고 `gates/config/artifact-ownership.toml`에 아래 JSON의 exact-key 10개만 추가한다. 기존 9키의 사유와 분리하며 검사 출력에 **고아 19·보존 19·구판 판정 불가 19**를 드러낸다. 소유 연결 복원·고아 0·재발 방지 완료를 뜻하지 않는다.

원본 행을 정당하게 복원하거나 별도 회수 승인을 받아 기존 invalidation 경로로 해당 캐시를 회수하면 재분류하고 보존 선언을 해제한다. 새 고아는 자동 추가하지 않는다. 소유자 확인 없이 행을 조작하거나 캐시를 지워 통과시키지 않는다.

재발 방지는 구버전 로컬 staging의 D5-only reaper 교체와 시험 산출물의 원장·캐시 정리 경계 일치가 필요하다. 이 기록과 보존 선언 자체는 staging 재기동·DB 변경 권한을 부여하지 않는다. AWS dev의 현재 코드와 구버전 로컬 staging의 상태를 구분해 인계한다.

독립 검토는 정확키 보존 결정을 조건부 수용했으며, 영속 증거와 위 재발 한계 표시 조건을 반영했다. 조사자의 최초 read-only lifecycle 검증은 부모의 동시 문서 생성으로 차단됐고, 이후 재등록한 완료 표시는 수용 근거로 사용하지 않았다. 파일·백업 실측과 검사 결과를 근거로 삼는다.
