"""L4 측정 보조 — staging API 호출기(읽기 전용 조사용). 산출물 아님.

세션 토큰은 `/tmp/l4sess.json` 에서만 읽고 이 파일에 값을 적지 않는다.
"""
import json, sys, urllib.request, urllib.parse, urllib.error

BASE = "https://www.colab-hydro.com/api/v1"


def token():
    return json.load(open("/tmp/l4sess.json"))["token"]


def call(method, path, query=None, body=None, headers=None, data=None):
    url = BASE + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    payload = data if data is not None else (json.dumps(body).encode() if body is not None else None)
    h = {"Authorization": "Bearer " + token(),
         "User-Agent": "curl/8.5.0"}
    if data is None and body is not None:
        h["Content-Type"] = "application/json"
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=payload, method=method, headers=h)
    try:
        r = urllib.request.urlopen(req)
        raw = r.read()
        try:
            return r.status, json.loads(raw or b"null"), url
        except Exception:
            return r.status, raw[:400], url
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace"), url


if __name__ == "__main__":
    method, path = sys.argv[1], sys.argv[2]
    q = json.loads(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3] else None
    b = json.loads(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4] else None
    st, out, url = call(method, path, q, b)
    print("URL", url)
    print("STATUS", st)
    print(json.dumps(out, ensure_ascii=False)[:4000] if not isinstance(out, str) else out[:4000])
