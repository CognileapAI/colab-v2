"""Issue 36 browser journey for the disposable e2e-login environment."""
import re
from pathlib import Path


def run(command, args, session):
    if not args.operator_login:
        raise RuntimeError("issue36 journey requires --operator-login")
    email = f"issue36-{session.rsplit('-', 1)[-1]}@example.com"
    initial = args.e2e_password
    changed = initial + "-changed"

    command("click", '[data-testid="gnb-account-admin"]')
    command("wait", "--text", "사용자 목록")
    command("find", "role", "tab", "click", "--name", "관리자 등록")
    command("fill", 'input[name="name"]', "무소속 관리자")
    command("fill", 'input[name="email"]', email)
    command("fill", 'input[name="initialPassword"]', initial, private=True)
    command("click", 'button[type="submit"]')
    command("wait", "--text", f"{email} 계정을 추가했어요.")

    command("find", "role", "button", "click", "--name", "로그아웃")
    command("wait", '[data-testid="login-account-name"]')
    command("fill", '[data-testid="login-account-name"]', email)
    command("fill", '[data-testid="login-password"]', initial, private=True)
    command("click", '[data-testid="login-submit"]')
    command("wait", '[data-testid="new-password"]')
    command("fill", '[data-testid="new-password"]', changed, private=True)
    command("fill", '[data-testid="confirm-password"]', changed, private=True)
    command("click", '[data-testid="change-password"]')
    command("wait", "--text", "로그아웃")

    command("find", "role", "button", "click", "--name", "로그아웃")
    command("wait", '[data-testid="login-account-name"]')
    command("fill", '[data-testid="login-account-name"]', email)
    command("fill", '[data-testid="login-password"]', changed, private=True)
    command("click", '[data-testid="login-submit"]')
    command("wait", "--text", "로그아웃")
    command("click", '[data-testid="gnb-account-admin"]')
    command("wait", "--text", email)
    command("reload")
    command("wait", "--text", email)
    snapshot = command("snapshot", "-i")
    if not re.search(r"사용자 목록", snapshot) or email not in snapshot:
        raise RuntimeError("labless operator did not persist through relogin and refresh")
    if args.artifacts:
        artifacts = Path(args.artifacts).resolve()
        artifacts.mkdir(parents=True, exist_ok=True)
        (artifacts / "issue36-final.snapshot.txt").write_text(snapshot, encoding="utf-8")
        command("screenshot", str(artifacts / "issue36-final.png"))
