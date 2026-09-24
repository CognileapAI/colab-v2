#!/usr/bin/env bash
# Repro: a daemon spawned while the gate holds the flock keeps the lock after the gate releases it.
# FIX=1 closes the lock fd in the child before exec.
L="$(mktemp -d)/repro.lock"
exec {FD}>"$L"; flock -n "$FD" && echo "gate: acquired"
if [ "${FIX:-0}" = 1 ]; then
  ( eval "exec ${FD}>&-"; exec -a fake-agent-browser-daemon sleep 30 ) &
else
  ( exec -a fake-agent-browser-daemon sleep 30 ) &
fi
DPID=$!
eval "exec ${FD}>&-"; echo "gate: released (parent fd closed)"
exec {G}>"$L"
if flock -n "$G"; then echo "next gate: acquired"; else echo "next gate: BLOCKED while daemon lives"; fi
eval "exec ${G}>&-"
kill "$DPID"; wait "$DPID" 2>/dev/null
exec {H}>"$L"; flock -n "$H" && echo "next gate after daemon killed: acquired"
