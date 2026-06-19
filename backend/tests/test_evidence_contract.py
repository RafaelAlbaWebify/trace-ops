from app.analyzer import analyze_collector_result
from app.collector_contract import validate_sample_scenario


SCENARIOS_WITH_FINDINGS = [
    "account-disabled",
    "missing-license",
    "ca-details-missing",
    "ca-device-noncompliant",
    "mfa-requirement-not-satisfied",
    "no-recent-signin-evidence",
]


REQUIRED_FINDING_FIELDS = {
    "finding_id",
    "rule_id",
    "title",
    "severity",
    "confidence",
    "likely_cause",
    "evidence_used",
    "evidence_missing",
    "safe_next_steps",
    "what_not_to_change_yet",
    "limitations",
    "source_module",
}


def _analysis_for(scenario: str):
    return analyze_collector_result(validate_sample_scenario(scenario))


def test_analysis_declares_evidence_contract_version_for_all_scenarios():
    for scenario in [*SCENARIOS_WITH_FINDINGS, "successful-access-baseline"]:
        analysis = _analysis_for(scenario)

        assert analysis["evidence_contract_version"] == "TRACE_FINDING_EVIDENCE_V1"
        assert "source_modules" in analysis


def test_every_finding_has_phase2_evidence_contract_fields():
    for scenario in SCENARIOS_WITH_FINDINGS:
        analysis = _analysis_for(scenario)

        assert analysis["status"] == "findings"
        assert analysis["findings"], scenario

        for finding in analysis["findings"]:
            assert REQUIRED_FINDING_FIELDS.issubset(finding.keys())
            assert finding["finding_id"] == finding["rule_id"]
            assert finding["source_module"] == "m365-access-path-analyzer"
            assert finding["severity"] in {"low", "medium", "high", "critical"}
            assert finding["confidence"] in {"low", "medium", "high"}
            assert finding["evidence_used"], finding["finding_id"]
            assert finding["safe_next_steps"], finding["finding_id"]
            assert finding["limitations"], finding["finding_id"]
            assert isinstance(finding["evidence_missing"], list)


def test_legacy_finding_aliases_are_preserved_for_current_ui_and_reports():
    analysis = _analysis_for("ca-device-noncompliant")
    finding = analysis["primary_finding"]

    assert finding["finding_id"] == "CA_DEVICE_COMPLIANCE_BLOCK"
    assert finding["rule_id"] == finding["finding_id"]
    assert finding["evidence"] == finding["evidence_used"]
    assert finding["next_steps"] == finding["safe_next_steps"]


def test_no_blocking_evidence_still_uses_contract_but_has_no_findings():
    analysis = _analysis_for("successful-access-baseline")

    assert analysis["status"] == "no_blocking_evidence"
    assert analysis["evidence_contract_version"] == "TRACE_FINDING_EVIDENCE_V1"
    assert analysis["primary_finding"] is None
    assert analysis["findings"] == []
    assert analysis["source_modules"] == []
