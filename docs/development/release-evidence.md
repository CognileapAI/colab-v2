# 로컬 릴리스 증거 연결

이 검사는 배포 승인이나 GitHub 증거의 진위 인증을 대신하지 않는다. 운영자는 승인된
대상 Actions run에서 CI 요약과 producer artifacts를 함께 가져와야 한다. 로컬 JSON을
만든 것만으로 GitHub 실행/PR 병합 사실이 인증되지는 않는다. 네트워크 조회·배포·태그
push·ruleset 적용은 이 문서나 검사기가 허가하지 않는다.

dev의 pre JSON은 `colab-release-evidence/1`, full `sha`, `environment: dev`,
`release_id`, `run_id`, timezone 포함 `started_at`, `pr` 객체
(`number`, `merged: true`, 환경별 `base: develop` 또는 `base: product`, `merge_commit_sha`), `ci` 요약,
절대 `artifact_root`를 가진다. CI 요약에는 집계기가 기록한 `inputs`
(event_name/event/needs/filters)가 필요하며 과거 요약만 있으면 준비 실패다.
CI 등록표의 모든 producer/check와 실제 파일·행·종료값·SHA/tree/run/attempt를 재검사한다.
origin/develop과 origin/product는 로컬 refs이며 승인된 별도 조회로 최신화해야 한다.

`ship.sh`는 `COLAB_RELEASE_PRE_EVIDENCE`를 먼저 검사한다. 기존의 반입만 수행하며
up.sh나 doctor를 자동 실행하지 않는다. `COLAB_RELEASE_DRY_RUN=1`은 검증 후
네트워크·반입 없이 종료한다. `COLAB_SHIP_ALLOW_NONMAIN`만으로 새 증거 검사를
우회할 수 없다.

실제 기동 이후 `ops/deploy_doctor_evidence.py`가 doctor 한 번의 15항목과 stdout/stderr를
수집한다. 수기 checks JSON은 완료 증거가 아니다. 전용 빈 `COLAB_RELEASE_ARTIFACT_DIR`에
0600 `post.json`과 redacted `doctor.log`를 생성하며 post 검사는 실제 로그 hash/bytes까지
대조한다. state의 CURRENT_SHA(12자리), 별도 CURRENT_FULL_SHA, MAIN_SHA candidate와
사전 full SHA, 실행 전후 state/source manifest를 대조한다. source bundle은 target commit의
파일을 담으며 실행 중인 doctor/emitter 경로도 manifest 대상과 일치해야 한다.
`/repo`, `/state`, `/secrets`는 읽기 전용이고 artifact 디렉터리만 쓰기 가능하다.
dev 정기 probe는 기본 direct doctor를 유지한다. 릴리스 증거 수집은
`COLAB_RELEASE_COLLECT=1`을 명시해야 하며 매 실행 새 artifact 디렉터리가 필요하다.
prod doctor는 full SHA별 전용 소스를 마운트한다. manifest와 실제 파일 집합이 다르면
거절하며 이전 SHA의 소스 디렉터리를 삭제하지 않는다.
`tag-release.sh dev`는 `COLAB_RELEASE_PRE_EVIDENCE`와 `COLAB_RELEASE_POST_EVIDENCE`
양쪽 검사 후에만 로컬 annotated tag를 생성한다. dry-run은 fetch/tag/push도 하지 않는다.
prod 태그는 반입 선행조건이므로 pre 검사만 요구한다. prod doctor는 반입·기동 이후
완료 확정용이며 태그 선행조건에 post를 요구하지 않는다. prod ship도 pre를 검사한다.

`deploy_release.py` dev/prod target은 `version`이 full SHA이며 `release_evidence`의
`pre`, `post` 경로를 선언한다. post는 실행 전에 존재하면 안 되며 verify 명령이 실제
배포 후 생성해야 한다. 완료·알림 재시도에도 증거를 다시 검사한다.
입력 부재는 78, 불일치·검증 실패는 1이다.

staging의 기존 integration rehearsal과 verify-deploy/verify-chains는 유지한다.
그 검증 성공은 dev/main 릴리스 증명이나 doctor15 완료를 의미하지 않는다.
staging 기존 상태/알림의 “완료”는 해당 rehearsal 절차 완료 의미로 한정한다.
`github-ruleset.json`은 main PR + required-gates 및 관리자 우회 없음의 제안이며 미적용이다.
