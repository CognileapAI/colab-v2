"""⑧ 확장 오버레이 단계 문면 촬영 — 고르개를 바꾸는 것과 폴링을 한 프로세스에서 붙인다."""
import json, os, pathlib, subprocess, sys, threading, time

ENV = dict(os.environ, AGENT_BROWSER_SESSION="colabverify")
STAGE_JS = """
(() => {
  const e = document.querySelector('[data-testid="pv-expand-stage"]');
  const i = document.querySelector('[data-testid="up-preview-stage"]');
  const box = (x) => { if (!x) return null; const r = x.getBoundingClientRect();
    return { text: x.textContent, top: Math.round(r.top), bottom: Math.round(r.bottom),
      inViewport: r.top >= 0 && r.bottom <= innerHeight && r.width > 0 }; };
  return { expand: box(e), inline: box(i) };
})();
"""


def ab(*args, stdin=None):
    return subprocess.run(["agent-browser", *args], input=stdin, capture_output=True,
                          text=True, env=ENV).stdout.strip()


def main():
    target, shot = sys.argv[1], sys.argv[2]
    hits = []
    stop = threading.Event()

    def poll():
        while not stop.is_set():
            try:
                s = json.loads(ab("eval", "--stdin", stdin=STAGE_JS))
            except Exception:
                continue
            if s.get("expand"):
                ab("screenshot", shot)
                hits.append(s)
                stop.set()
                return

    t = threading.Thread(target=poll)
    t.start()
    time.sleep(0.2)
    ab("select", "[data-testid=pvx-pick-file]", target)
    t.join(timeout=60)
    stop.set()
    print(json.dumps(hits, ensure_ascii=False, indent=1) if hits else "no stage captured")


main()
