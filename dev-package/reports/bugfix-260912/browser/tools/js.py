"""agent-browser eval --stdin 러너 — JS 파일 경로 하나를 받아 실행 결과를 찍는다."""
import os, subprocess, sys, pathlib

src = pathlib.Path(sys.argv[1]).read_text()
env = dict(os.environ, AGENT_BROWSER_SESSION=os.environ.get("AGENT_BROWSER_SESSION", "colabverify"))
r = subprocess.run(["agent-browser", "eval", "--stdin"], input=src,
                   capture_output=True, text=True, env=env)
sys.stdout.write(r.stdout)
sys.stderr.write(r.stderr)
