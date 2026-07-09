from app.log_analyzer import analyze_log_evidence
from app.log_models import LogAnalyzeRequest
from app.log_parser import parse_generic_access_log_text


def test_parser_normalizes_ca_failure():
    events = parse_generic_access_log_text(
        '2026-07-07T09:22:11Z user=sample.user@contoso.invalid app="SharePoint Online" result=failure reason="blocked by ca policy"'
    )

    assert len(events) == 1
    assert events[0].user_principal_name == "sample.user@contoso.invalid"
    assert events[0].application == "SharePoint Online"
    assert events[0].event_outcome == "failure"


def test_ca_pattern_returns_primary_finding():
    request = LogAnalyzeRequest(
        affected_user="sample.user@contoso.invalid",
        affected_service="SharePoint Online",
        content='2026-07-07T09:22:11Z user=sample.user@contoso.invalid app="SharePoint Online" result=failure reason="blocked by ca policy"',
    )

    analysis = analyze_log_evidence(request)

    assert analysis.status == "findings"
    assert analysis.primary_finding is not None
    assert analysis.primary_finding["rule_id"] == "LOG_PATTERN_CONDITIONAL_ACCESS_BLOCK"
    assert analysis.normalized_events


def test_auth_success_then_resource_denied_returns_authorization_pattern():
    request = LogAnalyzeRequest(
        affected_user="sample.user@contoso.invalid",
        affected_service="Engineering Site",
        content="""
2026-07-07T09:20:00Z user=sample.user@contoso.invalid app="Microsoft 365" result=success
2026-07-07T09:21:00Z user=sample.user@contoso.invalid app="Engineering Site" result=failure reason="forbidden not assigned"
""",
    )

    analysis = analyze_log_evidence(request)
    rule_ids = {finding["rule_id"] for finding in analysis.findings}

    assert "LOG_PATTERN_AUTH_SUCCESS_ACCESS_DENIED" in rule_ids


def test_license_or_service_plan_missing_returns_license_pattern():
    request = LogAnalyzeRequest(
        affected_user="sample.user@contoso.invalid",
        affected_service="Exchange Online",
        content="""
2026-07-07T09:20:00Z user=sample.user@contoso.invalid app="Microsoft 365" result=success
2026-07-07T09:21:00Z user=sample.user@contoso.invalid app="Exchange Online" result=failure reason="not licensed service plan disabled"
""",
    )

    analysis = analyze_log_evidence(request)
    rule_ids = {finding["rule_id"] for finding in analysis.findings}

    assert "LOG_PATTERN_LICENSE_OR_SERVICE_PLAN_MISSING" in rule_ids
    assert analysis.primary_finding is not None
    assert analysis.primary_finding["rule_id"] == "LOG_PATTERN_LICENSE_OR_SERVICE_PLAN_MISSING"


def test_guest_b2b_access_blocked_returns_guest_pattern():
    request = LogAnalyzeRequest(
        affected_user="guest.user@partner.invalid",
        affected_service="Partner SharePoint Site",
        content="""
2026-07-07T09:20:00Z user=guest.user@partner.invalid app="Microsoft 365" result=success reason="guest user sign-in succeeded"
2026-07-07T09:21:00Z user=guest.user@partner.invalid app="Partner SharePoint Site" result=failure reason="guest user invitation not redeemed cross-tenant access tenant restrictions guest not assigned"
""",
    )

    analysis = analyze_log_evidence(request)
    rule_ids = {finding["rule_id"] for finding in analysis.findings}

    assert "LOG_PATTERN_GUEST_B2B_ACCESS_BLOCKED" in rule_ids
    assert analysis.primary_finding is not None
    assert analysis.primary_finding["rule_id"] == "LOG_PATTERN_GUEST_B2B_ACCESS_BLOCKED"


def test_no_usable_events_returns_insufficient_evidence():
    analysis = analyze_log_evidence(LogAnalyzeRequest(content="hello this is not a log"))

    assert analysis.status == "insufficient_evidence"
    assert analysis.primary_finding is not None
    assert analysis.primary_finding["rule_id"] == "LOG_PATTERN_NO_USABLE_EVENTS"
    assert analysis.normalized_events == []


def test_unsupported_source_type_returns_insufficient_evidence():
    analysis = analyze_log_evidence(LogAnalyzeRequest(source_type="unknown_export", content="result=failure user=sample.user@contoso.invalid"))

    assert analysis.status == "insufficient_evidence"
    assert analysis.primary_finding is not None
    assert analysis.primary_finding["rule_id"] == "LOG_PATTERN_UNSUPPORTED_SOURCE_TYPE"
