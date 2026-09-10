# 2026-09-10 미리보기 과거 배포 증거

이 폴더는 `89a28d9` 배포 당시 자료를 main 동기화 과정에서 복구한 기록이다. 이번 동기화에서 제품 시험이나 배포를 다시 실행했다는 의미가 아니다. 당시 실패·재시도·면제는 `dev-package/sessions/20260910-preview-dev-stage-deployment.md`를 따른다.

공유 범위는 smoke JSON·산출물 TSV·보존 정책·원본 해시 목록이다. 로그(`*.log`)와 원시 로그 압축(`*.tar.gz`)은 개인 실행 경로를 포함하므로 로컬에 보존하고 Git 배포 대상에서 제외했다. 새 체크아웃에서는 원본 해시 목록의 로그·압축본 참조를 모두 재검증할 수 없다. 원본 보존 위치는 `dev-package/sessions/20260910-main-sync.md`를 따른다.

## 줄바꿈 무결성

복구 시 원본 manifest 26개 참조를 로컬에서 확인했다. 24개는 원시 바이트 SHA256 일치, TSV 2개는 Git의 CRLF→LF 정규화로 달랐다. 아래 LF 파일을 CRLF로 환원하면 원본 `sha256.json`과 일치한다. 원본 manifest는 수정하지 않는다.

| 파일 | 저장소 LF SHA256 |
|---|---|
| `artifact-snapshot.tsv` | `c9a673804d1186e3eac02f531ae0c7a7df1ac35c1fe58dbd1d55acdbc32e9f9d` |
| `artifact-postdeploy-snapshot.tsv` | `1d6127b2301db099454d6d49aa2eddea0fa45e7ec662a9804897a2fe9fe66a57` |

원시 로그와 압축 내부 184파일 및 복구 세션 8건의 자격정보 패턴 검사는 탐지 0건이었다. 이는 모든 민감정보 부재를 보장하는 검사가 아니며, 개인 경로가 발견된 원시 기록은 공개하지 않는다.
