"""⑧ 렌더 단계 문면 촬영 — 다시 그리기 유발 후 단계 줄(inline · 확장 오버레이)을 잡는다.

인자 = <모드 inline|expand> <스크린샷 경로>
"""
import json, os, pathlib, subprocess, sys, time

HERE = pathlib.Path(__file__).parent
ENV = dict(os.environ, AGENT_BROWSER_SESSION="colabverify")

STAGE_JS = """
(() => {
  const inline = document.querySelector('[data-testid="up-preview-stage"]');
  const exp = document.querySelector('[data-testid="pv-expand-stage"]');
  const vis = (e) => {
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return { text: e.textContent, top: Math.round(r.top), bottom: Math.round(r.bottom),
      inViewport: r.top >= 0 && r.bottom <= innerHeight && r.width > 0 };
  };
  return { t: new Date().toISOString(), inline: vis(inline), expand: vis(exp) };
})();
"""


def ab(*args, stdin=None):
    r = subprocess.run(["agent-browser", *args], input=stdin, capture_output=True, text=True, env=ENV)
    return r.stdout.strip() or r.stderr.strip()


def stage():
    try:
        return json.loads(ab("eval", "--stdin", stdin=STAGE_JS))
    except Exception as exc:
        return {"err": str(exc)}


def main():
    mode, shot = sys.argv[1], sys.argv[2]
    key = "expand" if mode == "expand" else "inline"
    log = []
    t0 = time.monotonic()
    shot_done = False
    while time.monotonic() - t0 < 60:
        s = stage()
        log.append(s)
        if s.get(key) and not shot_done:
            ab("screenshot", shot)
            shot_done = True
            log.append({"shot": shot, "at": s[key]})
            break
        time.sleep(0.25)
    print(json.dumps(log[-4:], ensure_ascii=False, indent=1))
    print("captured", shot_done)


main()
