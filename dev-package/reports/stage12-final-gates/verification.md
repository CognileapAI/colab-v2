# G10 전수 전후 실측 및 원본 검증

구현 SHA `30f5adf6774771c9ca34e2c3a0b92a0648b9cc76`, tree `32738137cdbd88fa45b851da96fd73c114763ae2`. BEFORE/AFTER 모두 실제 `all -j4` 단일 실행이며 내부 jobs만1→4로 변경했다.

| 실행 | UTC 시작→종료 | 결과 | wall |
|---|---|---|---|
| BEFORE | 08:38:08→09:00:40 | 61/0/0 | 1352.57초 |
| AFTER | 09:00:59→09:21:10 | 61/0/0 | 1211.22초 |

네 서비스 수집=실행1071/138/431/275, skip0, deselect6/26/42/50, failed0로 동일하다. 선택한 게이트61개도 일치한다. 기존 나머지 내부 병렬화·실패 안전 fixture 근거는 각 `gates/*.out`, `all.log` 및 기존 G10 세션과 함께 읽는다. 입력은 `input-facts.json`, 각 실행 `run-facts.json`. harness eval20은 명시적 면제이고 실제 모델 평가 통과가 아니다.

141.35초(약10.45%) 감소를 관측했다. 다른 TL-2 서비스 시험 부하가 실행 구간과 겹쳤으므로 순수 병렬화 효과 또는 반복 실행의 보장값으로 확대하지 않는다. 검사 범위를 줄이지 않았다.

## 직접 검증

실행 사본 `/tmp/colab-stage12-final-gates`의 HEAD/tree와 tracked 파일은 바뀌지 않았다. 작업 소유 runner/report 두 디렉터리만 `/tmp/colab-stage12-final-gates-evidence-30f5`로 이동한 뒤 clean checkout에서 검증했다. 제품·시험 파일 이동이나 ignore 규칙 변경은 없었다.

부모가 `gates/run.sh`의 `ALL_GATES` 정본에서61개를 읽어 중복0을 확인하고, **각 게이트를 `--gate`로 명시**해 외부 원본 BEFORE/AFTER `gate-summary.json`을 각각 검증했다. 두 명령 exit0, 출력은 각각 다음과 같다.

```
green: explicit required gates, counts, clean checkout and HEAD tree verified
```

이는 **현재 깨끗한 checkout·HEAD/tree·명시된61개 결과 검증**이다. 실행 시 COLAB_TASK_ID가 빠졌으므로 실행 시점 task fingerprint 검증으로 바꾸지 않는다. 이동 전 dirty checkout 검증 exit1은 보존하며 61개 게이트 판정 실패와 구분한다. worker 종료용 별도 contract-lint1/0/0도 전체61개의 대체 근거가 아니다.

## 보관 한계와 이동 후 봉인

이동 전 runner1파일/9375B, reports390파일/734048B. runner SHA256 `cec36eb562917a2f055f54ca951fa772ac121aa5539f9875677e77687f8c9c5d`.

이동 전 tar aggregate 기록은 runner `003f43eb329802e0affd35dc0aa16486f3330b331bd965fcb038db53dc2144a0`, reports `502c0a0da5f6dac4ed1a76ed722ad8ebc87b956706c68f1c0fcd599d3139f611`이다. 이동 후 생성한 aggregate는 일치하지 않았다. 원 명령/옵션이 남아 있지 않아 **불일치 원인을 재현할 수 없다**. 경로 직렬화 때문이라고 확정하지 않는다.

사전 파일별 manifest와 개별 summary hash가 없으므로390개 파일의 이동 전후 바이트 동일성을 암호학적으로 증명했다고 주장하지 않는다. 현재 원본의 manifest는 `post-move-manifest.json`이며 **이동 후** 측정이다. 부모 저장소로 복사할 때 현재 외부 원본과 각 파일 SHA가 같음을 확인했다. 과거 시점 봉인으로 소급하지 않는다. 독립 advisor는 이 보관 한계를 명시하는 조건에서 현재 원본·실제 두 실행·동일 입력/계수·clean 검증을 G10 수용 근거로 승인했다.
