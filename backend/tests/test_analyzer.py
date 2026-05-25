from app.analyzer import analyze_collector_result
from app.collector_contract import validate_sample_scenario


def _analysis_for(scenario):
    return analyze_collector_result(validate_sample_scenario(scenario))


def _rule_ids(analysis):
    return {finding["rule_id"] for finding in analysis["findings"]}


def test_account_disabled_triggers_user_account_disabled():
    analysis = _analysis_for("account-disabled")

    assert "USER_ACCOUNT_DISABLED" in _rule_ids(analysis)
    assert analysis["primary_finding"]["rule_id"] == "USER_ACCOUNT_DISABLED"


def test_missing_license_triggers_missing_relevant_license():
    analysis = _analysis_for("missing-license")

    assert "MISSING_RELEVANT_LICENSE" in _rule_ids(analysis)
    assert analysis["primary_finding"]["rule_id"] == "MISSING_RELEVANT_LICENSE"


def test_ca_details_missing_triggers_conditional_access_details_missing():
    analysis = _analysis_for("ca-details-missing")

    assert "CONDITIONAL_ACCESS_DETAILS_MISSING" in _rule_ids(analysis)


def test_ca_device_noncompliant_triggers_device_compliance_block():
    analysis = _analysis_for("ca-device-noncompliant")

    assert "CA_DEVICE_COMPLIANCE_BLOCK" in _rule_ids(analysis)
    assert analysis["primary_finding"]["rule_id"] == "CA_DEVICE_COMPLIANCE_BLOCK"


def test_no_recent_signin_evidence_triggers_no_recent_signin_evidence():
    analysis = _analysis_for("no-recent-signin-evidence")

    assert "NO_RECENT_SIGNIN_EVIDENCE" in _rule_ids(analysis)


def test_successful_access_baseline_returns_no_blocking_evidence():
    analysis = _analysis_for("successful-access-baseline")

    assert analysis["status"] == "no_blocking_evidence"
    assert analysis["primary_finding"] is None
    assert analysis["findings"] == []
