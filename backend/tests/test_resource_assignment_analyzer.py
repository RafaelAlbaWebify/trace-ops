import json

from app.log_models import LogAnalyzeRequest
from app.resource_assignment_analyzer import analyze_resource_assignment_evidence, parse_resource_assignment_json


def _content(value=False):
    return json.dumps({
        "timestamp": "2026-07-07T11:00:00Z",
        "affected_user": "sample.user@contoso.invalid",
        "resource": "Engineering Site",
        "authentication_outcome": "success",
        "assignment_present": value,
        "expected_access_confirmed": True,
        "conditional_access_status": "success",
    })


def test_parser_creates_authorization_event():
    events = parse_resource_assignment_json(_content())

    assert len(events) == 1
    assert events[0].source_type == "resource_assignment_json"
    assert events[0].event_type == "authorization"
    assert events[0].event_outcome == "failure"


def test_analyzer_returns_resource_assignment_finding():
    analysis = analyze_resource_assignment_evidence(
        LogAnalyzeRequest(source_type="resource_assignment_json", content=_content())
    )

    assert analysis.status == "findings"
    assert analysis.primary_finding is not None
    assert analysis.primary_finding["rule_id"] == "RESOURCE_ASSIGNMENT_OR_GROUP_MEMBERSHIP_MISSING_OR_UNCONFIRMED"


def test_empty_payload_returns_insufficient_evidence():
    analysis = analyze_resource_assignment_evidence(
        LogAnalyzeRequest(source_type="resource_assignment_json", content="not-json")
    )

    assert analysis.status == "insufficient_evidence"
    assert analysis.primary_finding is not None
    assert analysis.primary_finding["rule_id"] == "RESOURCE_ASSIGNMENT_EVIDENCE_MISSING"
