#!/usr/bin/env bash
# Read-only; no deletion probes against a live instance.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PG="${COLAB_STAGING_PG_CONTAINER:-colab_v2_staging_pg}"
if ! result="$(docker exec -i "$PG" psql -X -v ON_ERROR_STOP=1 -U postgres -d colab_ai -At < "$HERE/../ontology-protection-check.sql")"; then
  echo "ontology protection: preparation failure (catalog query failed)" >&2
  exit 78
fi
if [ "$result" != ONTOLOGY_PROTECTED ]; then
  echo "ontology protection: RED (ownership or destructive privileges unsafe)" >&2
  exit 1
fi
echo "ontology protection: GREEN (DB/schema/D9 ownership, isolated role, runtime privileges)"
