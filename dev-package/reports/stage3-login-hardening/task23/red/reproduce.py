import sys,json
sys.path.insert(0,sys.argv[1])
from fastapi import FastAPI,Depends
from fastapi.testclient import TestClient
from colab_core.app.routes.session import router
from colab_core.app.deps import current_subject
from colab_core.kernel.auth import Subject,SubjectRegistry
from colab_core.kernel.ids import Ulid
from colab_core.kernel.session_token import SessionSigner
from colab_core.kernel import authn
from colab_core.kernel.throttle import AttemptLimiter
app=FastAPI()
subject=Subject(Ulid("01ARZ3NDEKTSV4RRFFQ69G5FAV"),Ulid("01ARZ3NDEKTSV4RRFFQ69G5FAW"))
app.state.authenticators,app.state.session_issuer=authn.build(registry=SubjectRegistry({"test-only-code":subject}),signer=SessionSigner("test-only-secret",ttl_minutes=720))
app.state.login_limiter=AttemptLimiter(max_failures=5,window_seconds=900)
app.include_router(router,prefix="/api/v1")
@app.get("/protected")
def protected(subject=Depends(current_subject)): return {"ok":True}
with TestClient(app) as c:
 issued=c.post("/api/v1/sessions",json={"accessCode":"test-only-code"})
 headers={"Authorization":"Bearer "+issued.json()["token"]}
 before=c.get("/protected",headers=headers).status_code
 logout=c.delete("/api/v1/sessions/current",headers=headers).status_code
 after=c.get("/protected",headers=headers).status_code
 print(json.dumps({"baseline":"b63c9e8a0d40","login":issued.status_code,"before":before,"logout":logout,"after":after,"expected_after":401}))
 assert after==401,"logged-out token still accepted"
