"""#24㉮ 워커 분석 · #25⑴ viz 렌더 소요 측정 — staging · 코드 변경 0.

절차 = 접수(POST /uploads) → 상태 폴링 1000 ms(화면과 같은 주기) → ready 참 →
렌더 요청(POST /previews) → 렌더 폴링 250 ms(화면과 같은 주기) → 완료 → 그림 바이트 수신.
등록(POST /datasets)까지 가지 않는다.
"""
import datetime as dt
import json
import mimetypes
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request
import uuid

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from l4api import call, token, BASE

DATA = pathlib.Path(os.environ["COLAB_REFERENCE_DATA"]) / "02.File-format/file_format_2_nc/00.Data"
STATUS_POLL_S = 1.0
RENDER_POLL_S = 0.25


def now():
    return dt.datetime.now(dt.timezone.utc)


def stamp(t):
    return t.strftime("%Y-%m-%dT%H:%M:%S.") + f"{t.microsecond // 1000:03d}Z"


def multipart(paths):
    boundary = "----l4" + uuid.uuid4().hex
    parts = []
    for p in paths:
        ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
        head = (f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="files"; filename="{p.name}"\r\n'
                f"Content-Type: {ctype}\r\n\r\n").encode()
        parts.append(head + p.read_bytes() + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), boundary


def post_upload(paths):
    body, boundary = multipart(paths)
    t_start = now()
    st, out, url = call("POST", "/uploads", data=body,
                        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    t_end = now()
    return t_start, t_end, st, out, len(body)


def poll_status(upload_id, timeout_s=1800):
    errors = 0
    polls = 0
    started = time.monotonic()
    first_ready = None
    log = []
    while time.monotonic() - started < timeout_s:
        st, out, _ = call("GET", f"/uploads/{upload_id}")
        polls += 1
        t = now()
        if st != 200 or isinstance(out, str):
            errors += 1
            log.append((stamp(t), st, "error"))
        else:
            ready = bool(out.get("ready"))
            log.append((stamp(t), st, out.get("state") or out.get("status"), ready,
                        out.get("progress")))
            if ready:
                first_ready = t
                break
        time.sleep(STATUS_POLL_S)
    return first_ready, polls, errors, log


def render(upload_id, palette):
    t_req = now()
    st, out, _ = call("POST", "/previews",
                      body={"target": {"uploadId": upload_id},
                            "style": {"palette": palette, "classCount": 6},
                            "withoutReferenceGrid": False})
    t_acc = now()
    if st != 202 or isinstance(out, str):
        return t_req, t_acc, st, out, None, 0, 0, []
    render_id = out["renderId"]
    polls = 0
    errors = 0
    log = []
    t_done = None
    result = None
    started = time.monotonic()
    while time.monotonic() - started < 900:
        time.sleep(RENDER_POLL_S)
        s2, o2, _ = call("GET", f"/previews/{render_id}")
        polls += 1
        if s2 != 200 or isinstance(o2, str):
            errors += 1
            continue
        status = o2.get("status")
        if status != "그리는 중":
            t_done = now()
            log.append((stamp(t_done), status))
            result = o2
            break
    return t_req, t_acc, st, out, (t_done, result), polls, errors, log


def fetch_image(result):
    if not result:
        return None, None
    res = result.get("result") or {}
    url = res.get("imageUrl")
    if not url:
        return None, res
    if url.startswith("/"):
        url = "https://www.colab-hydro.com" + url
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token(),
                                               "User-Agent": "curl/8.5.0"})
    try:
        r = urllib.request.urlopen(req)
        n = len(r.read())
        return (now(), n), res
    except urllib.error.HTTPError as e:
        return (now(), f"HTTP {e.code}"), res


def run(label, count, palette, out_path):
    paths = sorted(DATA.glob("gk2a_ami_le2_lst_ko_*.nc"))[:count]
    rec = {"label": label, "pieceCount": len(paths),
           "byteSum": sum(p.stat().st_size for p in paths)}
    t0, t1, st, out, body_len = post_upload(paths)
    rec["intake"] = {"requestSentAt": stamp(t0), "acceptedAt": stamp(t1),
                     "status": st, "bodyBytes": body_len,
                     "transferSeconds": round((t1 - t0).total_seconds(), 3)}
    if st != 201:
        rec["intake"]["error"] = out if isinstance(out, str) else json.dumps(out)[:400]
        out_path.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
        return rec
    upload_id = out["uploadId"]
    rec["uploadId"] = upload_id
    ready_at, polls, errs, log = poll_status(upload_id)
    rec["analysis"] = {
        "startEvent": "접수 수락(201 수신)", "startAt": stamp(t1),
        "endEvent": "분석 완료(ready 참)", "endAt": stamp(ready_at) if ready_at else None,
        "wallSeconds": round((ready_at - t1).total_seconds(), 3) if ready_at else None,
        "statusPolls": polls, "statusPollErrors": errs,
        "pollIntervalSeconds": STATUS_POLL_S,
        "log": log[-6:],
    }
    tr, ta, rst, rout, done, rpolls, rerrs, rlog = render(upload_id, palette)
    t_done, result = done if done else (None, None)
    img, res = fetch_image(result)
    rec["render"] = {
        "startEvent": "렌더 요청 송신", "startAt": stamp(tr),
        "acceptedAt": stamp(ta), "acceptStatus": rst,
        "renderId": rout.get("renderId") if isinstance(rout, dict) else None,
        "doneAt": stamp(t_done) if t_done else None,
        "doneStatus": (result or {}).get("status"),
        "wallSecondsToDone": round((t_done - tr).total_seconds(), 3) if t_done else None,
        "imageFetchedAt": stamp(img[0]) if img else None,
        "imageBytes": img[1] if img else None,
        "wallSecondsToImage": round((img[0] - tr).total_seconds(), 3) if img else None,
        "renderPolls": rpolls, "renderPollErrors": rerrs,
        "pollIntervalSeconds": RENDER_POLL_S,
        "createRenderCalls": 1,
        "resultKeys": sorted(res.keys()) if isinstance(res, dict) else None,
        "failure": (result or {}).get("failure"),
        "partialFailure": (result or {}).get("partialFailure"),
    }
    if isinstance(rout, str):
        rec["render"]["error"] = rout[:400]
    out_path.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    return rec


if __name__ == "__main__":
    label = sys.argv[1]
    count = int(sys.argv[2])
    st, pal, _ = call("GET", "/preview-palettes")
    palette = pal["items"][0]["value"] if isinstance(pal, dict) and pal.get("items") else None
    print("palette", palette)
    here = pathlib.Path(__file__).parent
    r = run(label, count, palette, here / f"run-{label}.json")
    print(json.dumps({k: v for k, v in r.items() if k != "analysis"}, ensure_ascii=False)[:800])
    print("analysis", json.dumps(r.get("analysis", {}), ensure_ascii=False)[:800])
