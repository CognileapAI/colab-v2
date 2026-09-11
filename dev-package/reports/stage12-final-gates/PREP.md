# Stage 1·2 최종 게이트 실행 패킷

- 준비 기준 SHA: `620f4066b32d0596274f3851457d371abe3a3d38`
- 실행기 SHA-256: `cec36eb562917a2f055f54ca951fa772ac121aa5539f9875677e77687f8c9c5d`
- 전수 대상: 61개, 중복 0개
- 일회용 DB: platform·AI 각 1개, `postgres:16-alpine`, PGDATA tmpfs, 공개 host port 0개
- staging 사용: 현재 컨테이너 IP 조회와 읽기 전용 URL의 host 교체만 수행. staging DB 쓰기·재시작 0회
- URL 보존: 자격·path·query 보존 여부만 `input-facts.json`에 기록. 실제 URL·비밀번호 미기록
- 화면 검사: dev URL 선언, 화면 면제 미선언
- 모델 평가: 명시 면제 20건. Astra 실행 결과로 세지 않음

최종 통합 SHA가 확정되면 그 SHA를 `COLAB_FINAL_EXPECTED_SHA`에 넣는다. 준비 때와 SHA가 달라졌으면
새 최종 checkout에서 실행기를 다시 준비하며, 이 패킷의 620f406 결과를 최종 판정에 쓰지 않는다.

```bash
export COLAB_FINAL_EXPECTED_SHA=<최종 통합 SHA>
.codex/artifacts/stage12-final-gates/run-final-gates.sh prepare
.codex/artifacts/stage12-final-gates/run-final-gates.sh before
.codex/artifacts/stage12-final-gates/run-final-gates.sh after
.codex/artifacts/stage12-final-gates/run-final-gates.sh compare
.codex/artifacts/stage12-final-gates/run-final-gates.sh cleanup
```

`before`는 공통·서비스·렌더 worker를 모두 1로 고정하고 `all -j 4`를 실행한다. `after`는 세 값을
모두 4로 고정해 같은 명령을 실행한다. 각 실행은 SHA·CPU 4개·가용 메모리 6 GiB·다른 전수 실행 부재를
먼저 검사한다. 로그·벽시계·게이트 3계수·서비스 수집/실행/skip/deselect/fail 계수는
`before/`, `after/`, `comparison.json`에 기록한다.
