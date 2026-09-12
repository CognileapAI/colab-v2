"""브라우저에 staging 세션을 심는다 — agent-browser eval 로 localStorage 주입 후 새로고침."""
import json, os, pathlib, subprocess

here = pathlib.Path(__file__).parent
sess = json.load(open("/tmp/vsess/sess.json"))
tpl = (here / "inject-session.js").read_text()
script = tpl.replace("__SESSION__", json.dumps(sess))
env = dict(os.environ, AGENT_BROWSER_SESSION="colabverify")
r = subprocess.run(["agent-browser", "eval", "--stdin"], input=script,
                   capture_output=True, text=True, env=env)
print(r.stdout.strip(), r.stderr.strip())
