"""`clear_login_throttle` — 잠긴 계정의 로그인 시도 셈을 푼다.

**이 스크립트는 API 를 부른다. DB 도 프로세스도 직접 만지지 않는다.** 시도 제한은 웹 서버
프로세스의 메모리에 있어(`kernel/throttle.py`) 밖에서는 닿을 길이 없다 — 그래서 유일한
해제 경로가 `POST /api/v1/admin/login-throttle/clear`(운영자 전용)이고, 여기 있는 것은
그 호출을 감싼 얇은 겉면뿐이다.

    (services/core-api 에서)
    .venv/bin/python ops/clear_login_throttle.py \
        --base-url https://<호스트>/api/v1 --email <계정 이메일> --token-file <토큰 파일>

토큰은 **파일 또는 stdin** 으로만 받는다. `argv` 로 받으면 그 값이 셸 히스토리·`ps` 출력·
작업 기록에 남는다 — DB 비밀번호가 그 경로로 샜던 것이 `_FILE` 간접참조를 도입한 이유다
(`tests/test_secret_file_refs.py`).

⛔ **여러 워커로 떠 있으면 해제도 그 워커 하나에만 닿는다.** 시도 제한 자체의 한계이고
(`PLAN-SoT §9 〈108〉-㉲`), 이 스크립트가 새로 만드는 한계가 아니다. 그 배치에서는 같은
명령을 워커 수만큼 부르거나(로드밸런서 뒤라면 반복 호출) 잠금이 창(기본 900초) 안에
스스로 풀리기를 기다린다.

종료코드 — 0 해제 호출 성공 · 1 거절·입력 오류 · 2 호출 실패(네트워크·서버).
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import urllib.error
import urllib.request


def _read_token(token_file: str | None) -> str:
    """토큰은 파일 또는 stdin. **`argv` 를 받지 않는다.**"""
    if token_file:
        token = pathlib.Path(token_file).read_text(encoding="utf-8").strip()
    else:
        token = sys.stdin.read().strip()
    if not token:
        raise ValueError("운영자 토큰이 비어 있다 (--token-file 또는 stdin).")
    return token


def clear(base_url: str, email: str, token: str, *, timeout: int = 30) -> int:
    url = base_url.rstrip("/") + "/admin/login-throttle/clear"
    payload = json.dumps({"email": email}, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url, method="POST", data=payload,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="잠긴 계정의 로그인 시도 셈을 푼다 (운영자 전용 API 호출)")
    parser.add_argument("--base-url", required=True,
                        help="API 기준 주소. 예: https://<호스트>/api/v1")
    parser.add_argument("--email", required=True, help="잠금을 풀 계정 이메일")
    parser.add_argument("--token-file",
                        help="운영자 세션 토큰 파일. 생략하면 stdin 에서 읽는다.")
    args = parser.parse_args(argv)
    try:
        token = _read_token(args.token_file)
    except (OSError, ValueError) as exc:
        print(f"토큰을 읽지 못했다: {exc}")
        return 1
    try:
        status = clear(args.base_url, args.email, token)
    except urllib.error.HTTPError as exc:
        # **응답 본문을 그대로 찍지 않는다** — 오류 봉투의 message 한 줄만 낸다.
        try:
            message = json.loads(exc.read().decode("utf-8")).get("message", "")
        except (ValueError, OSError):
            message = ""
        print(f"거절됐다 (HTTP {exc.code}) {message}".rstrip())
        return 1
    except (urllib.error.URLError, OSError) as exc:
        print(f"호출하지 못했다: {exc}")
        return 2
    # **「잠겨 있었는가」는 서버도 말하지 않는다** (계정 열거를 막는 같은 이유) —
    # 여기서도 「지웠다」가 아니라 「해제를 걸었다」까지만 적는다.
    print(f"해제를 걸었다 (HTTP {status}). 잠겨 있었다면 다음 로그인부터 통과한다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
