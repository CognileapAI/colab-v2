# WSL stage 시험 인계 — 실행 전 준비

이 문서는 실행 절차다. 이번 개발 작업에서 dev 배포, stage 배포·재시작, stage 데이터 적재는 실행하지 않았다. 모델 평가도 사용자 지시에 따라 보류했다.

## 대상과 선행 조건

- 저장소 `codex/stage3-next`의 검증한 변경 전체가 대상이다. 현재 HEAD만 배포하면 미커밋 변경이 빠진다. 배포 직전 커밋/작업트리 승인 및 최신 검증 receipt와 실제 내용 일치를 확인한다.
- WSL의 기존 stage 설정 파일과 로그인 가능한 해당 연구실의 편집 계정이 필요하다. 토큰은 저장소 밖 0600 파일로 전달한다.
- main 통합 후 platform migration은 `0030_merge_audit_and_backoffice` 다음 `0031_search_evidence`다. 이전 미배포 초안 `0028_search_evidence`는 최신 체인 뒤로 이동했다. stage의 실제 체인이 이 분기와 호환되는지 배포 전 확인한다. 다른 분기의 후속 revision이 있으면 적용하지 말고 체인을 먼저 통합한다.
- 기존 stage 14개 자료와 레퍼런스 9개 자료는 같은 구성이 아니다. 이름만 비슷한 자료를 임의 연결하거나 dev ID를 복사하지 않는다.

## 실행 순서

1. stage 배포 시 기존 `infra/staging/deploy.sh --target staging` 진입점을 사용한다. 백업·체인 검사·이미지 빌드·마이그레이션·상태 확인은 기존 절차를 따른다. 지금 이 문서 작성에서는 실행하지 않았다. 기본 절차는 깨끗한 커밋을 요구하므로 미커밋 상태를 자동 우회하지 않는다.
2. stage에 레퍼런스가 없으면 `infra/staging/load-seed.py`, `manifest-refdata.json`과 실제 `03 Reference-Data`를 사용해 공개 API로 등록한다. 이미 있는 동일 이름은 충돌 여부를 먼저 확인한다. 실제 파일 업로드 완료를 근거 텍스트 저장으로 대체하지 않는다.
3. `stage-evidence-packet-02.json`의 97개 파일 입력을 검토한다. 이전 `stage-evidence-packet.json`은 설명서에 자료 조건을 상속한 초안이라 사용하지 않는다. 원문 변경이 있으면 아래 build로 새 묶음을 만들고 차이를 검토한다.
4. 읽기 전용 preflight로 stage의 실제 파일 ID·내용 버전·근거 수정 버전을 확인한다. 누락·동명 충돌은 전부 해소한 후 저장한다.
5. 초안 저장 후 화면에서 근거를 확인한다. 명시적 전체 검토가 끝난 입력만 `--reviewed`로 확인 저장하거나 화면에서 개별 확인한다. 확인 전 근거는 검색 조건에 사용하지 않는다.
6. 골든 12문항을 stage 실제 검색으로 실행한다. 자료 누락과 검색 실패를 구분한다. 100m 직접 관측/결측률은 근거 없이 충족으로 표시되면 실패다. 자료 역할·SPI/SPEI·기간·상세 이동·잠긴 파일 비노출을 확인한다.
7. 별도로 파일 교체 후 stale, 오래된 수정 화면 충돌, 권한 없는 계정의 읽기와 저장 거부를 시험한다. 현재 저장된 원문은 수집 당시 사본이다. 외부 DOCX 변경을 제품이 자동 감지한다고 기대하지 않는다.

## 입력 도구 예시

저장소 루트에서 실행한다. `<...>`는 실제 stage 값으로 치환한다. 결과 파일은 새 이름이어야 한다.

```bash
python3 eval/k4-search/stage_evidence.py --build \
  --reference-root '<실제 Reference-Data 경로>' --output /tmp/stage-evidence-new.json

python3 eval/k4-search/stage_evidence.py \
  --packet dev-package/reports/stage3-ai-search-plan/stage-evidence-packet-02.json \
  --base-url http://127.0.0.1:3000 --token-file '<stage 토큰 파일>' \
  --output /tmp/stage-evidence-preflight.json
```

동일 명령에 `--apply`를 추가하면 초안을 저장한다. `--apply --reviewed`는 전체 입력을 사람이 확인했다는 명시적 저장이다. 기본값은 읽기 전용이며 외부 주소·리다이렉트는 거부한다. 일부 저장 후 오류가 나면 앞선 저장은 유지된다. 보고서의 written 건수를 확인하고 현재 상태를 다시 조회한다.

## 복구와 판정

기존 `infra/staging/rollback.sh`는 이전 이미지로 되돌리며 DB를 downgrade하지 않는다. 근거 삭제를 수반하는 migration downgrade를 복구 방법으로 사용하지 않는다. 입력 오류는 현재 버전을 조회해 초안으로 수정한다. DB 복원은 별도 복구 승인·백업 절차를 따른다.

로컬 HTTP 해석 대역을 사용한 시험은 실제 Sonnet 의미 품질 평가가 아니다. 이번 개발의 로컬 준비 완료와 K4 제품 출시 판정을 구분한다. stage 실행 결과와 실제 모델 평가는 후속 보고서로 남긴다.
