# 알림 실행 소스 설치 입력

`build-source-bundle.sh`는 지정 커밋의 `infra/notifications`, `infra/__init__.py`, `services/core-api/src`, core의 `pyproject.toml`·`requirements.in`·닫힌 `requirements.txt`를 함께 넣는다. working tree나 개발자의 가상환경은 포함하지 않는다. 미커밋 구현은 해당 SHA 배포 산출물에 존재하지 않으므로 커밋·배포 승인 전에는 운영 반입 완료로 보지 않는다.

승인된 배포 설치 단계에서 검증된 bundle을 푼 뒤 Python 3.12 환경을 해당 버전의 `.operator-venv`에 준비한다. 설치 입력은 아래와 같으며 이 문서 자체는 설치를 실행하지 않는다.

```bash
python3.12 -m venv .operator-venv
.operator-venv/bin/python -m pip install -r services/core-api/requirements.txt -r infra/notifications/requirements.txt
.operator-venv/bin/python -m pip install setuptools==80.9.0
.operator-venv/bin/python -m pip install --no-deps --no-build-isolation services/core-api
```

루트는 검증된 bundle 디렉터리로 고정한다. manifest의 `runtime_python`에 위 가상환경 Python 절대 경로를 지정한다. 미지정 시 명시적으로 구성한 운영 환경 PATH의 `python3`를 사용한다. 앱의 가상환경에는 AWS SDK를 설치하지 않는다. exporter가 직접 파일로 실행되어도 `infra`를 가져올 수 있도록 배치 환경의 `PYTHONPATH`는 이 bundle 루트로 고정한다. 다른 working tree 경로를 넣지 않는다. exporter와 notification 명령 모두 같은 `runtime_python`을 사용한다.

가상환경은 생성 산출물이며 소스 hash manifest에 들어가지 않는다. 소스와 마찬가지로 root 소유, group/world 쓰기 금지로 유지한다. 새 소스 SHA 반입 시 그 SHA의 설치 입력으로 새 환경을 만들고 이전 SHA의 환경을 덮어쓰지 않는다. 의존 설치 실패 또는 Python·package 부재는 준비 실패로 처리하고 작업 스케줄을 활성화하지 않는다. 별도 DB exporter 로그인과 AWS 임시 역할 환경은 운영 비밀 설정에서 주입한다.
