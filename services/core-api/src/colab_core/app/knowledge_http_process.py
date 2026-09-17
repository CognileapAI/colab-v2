"""Single-request transport child. Authority and request secrets arrive only on stdin."""

import json
import sys
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def main():
    # The parent enforces the wall-clock deadline, including DNS and headers,
    # and kills/reaps this process before returning on any failure.
    request = json.loads(sys.stdin.buffer.read(32769))
    opener = build_opener(ProxyHandler({}), _NoRedirect())
    response = None
    try:
        try:
            response = opener.open(
                Request(
                    request["url"],
                    data=request["body"].encode(),
                    headers=request["headers"],
                ),
                timeout=request["timeout"],
            )
        except HTTPError as error:
            response = error
        status = response.code
        limit = 1048576 if status == 200 else 4096
        data = response.read(limit + 1)
        if len(data) > limit:
            return 1
        sys.stdout.buffer.write(str(status).encode() + b"\n" + data)
        return 0
    except Exception:
        return 1
    finally:
        if response is not None:
            response.close()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # Never print a traceback containing request URLs or credentials.
        sys.exit(1)
