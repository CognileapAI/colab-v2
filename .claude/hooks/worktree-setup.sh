#!/usr/bin/env bash
# Claude compatibility entrypoint; shared implementation resolves from this file.
exec bash "$(dirname "${BASH_SOURCE[0]}")/../../scripts/harness/hooks/worktree-setup.sh" "$@"
