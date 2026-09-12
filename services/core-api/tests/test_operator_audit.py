import json
from unittest.mock import Mock


def test_domain_snapshot_uses_same_source_for_audit_and_export():
    from colab_core.domains.d2_audit import append_snapshot
    session = Mock()
    session.execute.side_effect = [Mock(scalar_one=lambda: "lab-a"), Mock(), Mock()]
    source = append_snapshot(session, actor_id="actor", target_id="target", action="permission.changed",
                             before={"enabled": False}, after={"enabled": True})
    assert len(source) == 26
    audit_params = session.execute.call_args_list[1].args[1]
    export_params = session.execute.call_args_list[2].args[1]
    assert audit_params["source_id"] == export_params["source_id"] == source
    assert json.loads(audit_params["before"]) == {"enabled": False}


def test_different_domains_write_only_their_owner_tables():
    from colab_core.domains import d3_audit, d6_audit
    for module, prefix in ((d3_audit, "d3_"), (d6_audit, "d6_")):
        session = Mock(); session.execute.side_effect = [Mock(scalar_one=lambda: "lab-a"), Mock(), Mock()]
        module.append_snapshot(session, actor_id="actor", target_id="target", action="deleted", before={}, after=None)
        statements = " ".join(str(c.args[0]) for c in session.execute.call_args_list)
        assert prefix + "operator_audit" in statements
        assert prefix + "operator_export" in statements
