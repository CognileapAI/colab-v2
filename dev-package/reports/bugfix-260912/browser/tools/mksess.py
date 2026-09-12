"""staging 세션 발급 — 심어 둔 접속 코드로 POST /sessions. 값은 /tmp 에만 둔다."""
import json, os, subprocess, urllib.request, urllib.error

OUT = "/tmp/vsess/sess.json"
os.makedirs("/tmp/vsess", exist_ok=True)

code = subprocess.run(
    ["docker", "exec", "colab_v2_staging_core_api", "python3", "-c",
     "import json;d=json.load(open('/etc/colab/subjects.json'));print(list(d.keys())[0])"],
    capture_output=True, text=True, check=True).stdout.strip()

req = urllib.request.Request(
    "http://127.0.0.1:3000/api/v1/sessions",
    data=json.dumps({"accessCode": code}).encode(),
    method="POST",
    headers={"Content-Type": "application/json", "User-Agent": "curl/8.5.0"})
try:
    r = urllib.request.urlopen(req)
    out = json.loads(r.read())
    print("STATUS", r.status)
    json.dump(out, open(OUT, "w"))
    print("keys", sorted(out.keys()), "expiresAt", out.get("expiresAt"))
except urllib.error.HTTPError as e:
    print("ERR", e.code, e.read().decode()[:400])
