#!/usr/bin/env python3
"""Prepare or explicitly apply a reviewed professor/system-admin split."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from colab_core.kernel.operator_transition import OperatorTransition, TransitionRefused, plan_sha256


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url-file", type=Path, required=True,
                        help="account-admin DB 접속 문자열을 담은 보호된 파일 (비밀을 인자로 넘기지 않음)")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="분류할 현재 시스템 관리자 ID·소속·역할·상태 조회")
    prepare = commands.add_parser("prepare", help="쓰기 없는 dry-run 계획 작성")
    prepare.add_argument("--selection", type=Path, required=True)
    prepare.add_argument("--output", type=Path, required=True)
    apply = commands.add_parser("apply", help="검토한 계획과 SHA256으로 명시 적용")
    apply.add_argument("--plan", type=Path, required=True)
    apply.add_argument("--plan-sha256", required=True)
    args = parser.parse_args(argv)
    engine = None
    try:
        engine = create_engine(args.database_url_file.read_text().strip(), hide_parameters=True)
        service = OperatorTransition(sessionmaker(engine))
        if args.command == "list":
            result = {"operators": service.inventory()}
        elif args.command == "prepare":
            plan = service.prepare(json.loads(args.selection.read_text()))
            args.output.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n")
            result = {"planSha256": plan_sha256(plan), "revokeCount": len(plan["selection"]["revoke"]),
                      "keepCount": len(plan["selection"]["keep"]), "dryRun": True}
        else:
            result = service.apply(json.loads(args.plan.read_text()), args.plan_sha256)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except TransitionRefused as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (OSError, ValueError, TypeError, SQLAlchemyError):
        # Driver/file exceptions may contain credentials; no raw exception or traceback.
        print("전환 준비 또는 적용에 실패했어요. 입력 파일·DB 연결·계정 관리자 권한을 확인하세요.", file=sys.stderr)
        return 1
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
