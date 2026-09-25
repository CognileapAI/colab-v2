"""Collect the explicitly cross-service integration scenario in the core gate."""
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'tests/integration'))
from knowledge_http_roundtrip import (  # noqa: E402,F401
    roundtrip, connected, prepared, sources,
    test_authenticated_roundtrip_replay_forgery_and_logout,
    test_current_other_viewer_reads_expired_grant_and_denials,
    test_deletion_roundtrip_survives_logout_and_denies_other_capabilities,
    test_projection_roundtrip_recovers_committed_receipt_and_reauthenticates,
    test_measured_file_pipeline_registration_d9_projection,
)
