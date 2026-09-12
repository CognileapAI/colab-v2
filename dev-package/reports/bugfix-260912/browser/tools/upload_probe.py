"""업로드 1건 접수 → 분석 중 구간 DOM 실측·촬영 → ready 이후 재실측.

⑧ / #24㉯ 판정 입력을 만든다. 파일 고르기는 실브라우저 `input[type=file]` 로 한다.
"""
import json, os, pathlib, subprocess, sys, time

HERE = pathlib.Path(__file__).parent
SHOTS = HERE.parent
ENV = dict(os.environ, AGENT_BROWSER_SESSION="colabverify")
PROBE = (HERE / "probe.js").read_text()


def ab(*args, stdin=None):
    r = subprocess.run(["agent-browser", *args], input=stdin, capture_output=True,
                       text=True, env=ENV)
    return r.stdout.strip() or r.stderr.strip()


def probe():
    out = ab("eval", "--stdin", stdin=PROBE)
    try:
        return json.loads(out)
    except Exception:
        return {"raw": out[:300]}


def main():
    sample = sys.argv[1]
    ab("upload", "input[type=file]", sample)
    t0 = time.monotonic()
    log = []
    shot_done = False
    while time.monotonic() - t0 < 90:
        s = probe()
        log.append({"dt": round(time.monotonic() - t0, 2), **s})
        if s.get("stage") in ("1", "2") and not shot_done and s.get("elapsedText"):
            ab("screenshot", str(SHOTS / "08-24-analyzing.png"))
            shot_done = True
        if s.get("stage") == "3":
            break
        time.sleep(0.7)
    time.sleep(0.5)
    log.append({"dt": round(time.monotonic() - t0, 2), "after_ready": True, **probe()})
    (HERE / "analyze-log.json").write_text(json.dumps(log, ensure_ascii=False, indent=1))
    for row in log:
        print(json.dumps(row, ensure_ascii=False))


main()
