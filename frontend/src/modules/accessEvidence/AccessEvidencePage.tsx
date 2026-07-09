import { useState } from "react";
import { AccessEvidenceInput, runAccessEvidenceAnalysis, StandardDiagnosticResult } from "../../api/traceApi";

type AccessEvidencePageProps = {
  onResult: (result: StandardDiagnosticResult) => void;
};

type TernaryEvidence = "true" | "false" | "unknown";
type OutcomeEvidence = "success" | "failure" | "unknown";
type ConditionalAccessEvidence = "success" | "failure" | "notApplied" | "unknown";
type MfaEvidence = "satisfied" | "required" | "failure" | "unknown";

type ResourceAssignmentGuide = {
  timestamp: string;
  application: string;
  authenticationOutcome: OutcomeEvidence;
  assignmentPresent: TernaryEvidence;
  expectedAccessConfirmed: TernaryEvidence;
  conditionalAccessStatus: ConditionalAccessEvidence;
  mfaResult: MfaEvidence;
  failureReason: string;
  evidenceChecked: string;
};

const defaultResourceGuide: ResourceAssignmentGuide = {
  timestamp: "2026-07-07T11:00:00Z",
  application: "SharePoint Online",
  authenticationOutcome: "success",
  assignmentPresent: "false",
  expectedAccessConfirmed: "true",
  conditionalAccessStatus: "success",
  mfaResult: "satisfied",
  failureReason: "User receives access denied when opening the specific resource.",
  evidenceChecked: [
    "Entra sign-in result checked",
    "Conditional Access result checked",
    "MFA result checked",
    "Resource owner or ticket confirms expected access",
    "Resource membership or assignment checked"
  ].join("\n")
};

function ternaryToBoolean(value: TernaryEvidence): boolean | undefined {
  if (value === "true") return true;
  if (value === "false") return false;
  return undefined;
}

function evidenceLines(value: string): string[] {
  return value.split("\n").map((line) => line.trim()).filter(Boolean);
}

function buildResourceAssignmentJson(form: AccessEvidenceInput, guide: ResourceAssignmentGuide): string {
  const checked = evidenceLines(guide.evidenceChecked);
  const payload: Record<string, unknown> = {
    timestamp: guide.timestamp || undefined,
    affected_user: form.affectedUser || undefined,
    resource: form.affectedService || undefined,
    application: guide.application || undefined,
    authentication_outcome: guide.authenticationOutcome,
    assignment_present: ternaryToBoolean(guide.assignmentPresent),
    expected_access_confirmed: ternaryToBoolean(guide.expectedAccessConfirmed),
    conditional_access_status: guide.conditionalAccessStatus,
    mfa_result: guide.mfaResult,
    failure_reason: guide.failureReason || undefined,
    evidence_checked: checked.length > 0 ? checked : undefined
  };

  return JSON.stringify(payload, null, 2);
}

const examples: Record<AccessEvidenceInput["sourceType"], string> = {
  generic_access_log_text: '2026-07-07T09:22:11Z user=sample.user@contoso.invalid app="SharePoint Online" result=failure reason="blocked by ca policy"',
  entra_signin_csv: `createdDateTime,userPrincipalName,appDisplayName,resourceDisplayName,clientAppUsed,conditionalAccessStatus,authenticationRequirement,status.errorCode,status.failureReason
2026-07-07T09:22:11Z,sample.user@contoso.invalid,SharePoint Online,SharePoint Online,Browser,failure,multiFactorAuthentication,53003,Policy evaluation did not pass`,
  resource_assignment_json: ""
};

function emptyAccessResult(sourceType: AccessEvidenceInput["sourceType"]): StandardDiagnosticResult {
  const labels: Record<AccessEvidenceInput["sourceType"], string> = {
    generic_access_log_text: "Generic access log text",
    entra_signin_csv: "Entra sign-in CSV",
    resource_assignment_json: "Resource assignment guided form"
  };

  return {
    title: "Access evidence analyzer",
    status: "not_run",
    findingId: null,
    summary: `Ready to analyze ${labels[sourceType]} evidence.`,
    evidenceUsed: [],
    evidenceMissing: [],
    safeNextSteps: [],
    doNotChangeYet: [],
    limitations: [],
    readOnlyKept: true,
    raw: { sourceType }
  };
}

export function AccessEvidencePage({ onResult }: AccessEvidencePageProps) {
  const [resourceGuide, setResourceGuide] = useState<ResourceAssignmentGuide>(defaultResourceGuide);
  const [form, setForm] = useState<AccessEvidenceInput>({
    sourceType: "generic_access_log_text",
    affectedUser: "sample.user@contoso.invalid",
    affectedService: "SharePoint Online",
    content: examples.generic_access_log_text,
    notes: "Redacted operator evidence."
  });
  const [running, setRunning] = useState(false);

  const generatedResourceJson = buildResourceAssignmentJson(form, resourceGuide);
  const isResourceGuidedMode = form.sourceType === "resource_assignment_json";
  const submittedEvidence = isResourceGuidedMode ? generatedResourceJson : form.content;

  function update<K extends keyof AccessEvidenceInput>(key: K, value: AccessEvidenceInput[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function updateResourceGuide<K extends keyof ResourceAssignmentGuide>(key: K, value: ResourceAssignmentGuide[K]) {
    setResourceGuide((current) => ({ ...current, [key]: value }));
  }

  function useExample(sourceType: AccessEvidenceInput["sourceType"]) {
    setForm((current) => ({
      ...current,
      sourceType,
      content: sourceType === "resource_assignment_json" ? buildResourceAssignmentJson(current, resourceGuide) : examples[sourceType],
      affectedService: sourceType === "resource_assignment_json" ? "Engineering SharePoint Site" : current.affectedService
    }));
    onResult(emptyAccessResult(sourceType));
  }

  async function copyStructuredEvidence() {
    try {
      await navigator.clipboard.writeText(submittedEvidence);
    } catch {
      // Clipboard can be unavailable in some local browser contexts. The preview remains visible.
    }
  }

  async function run() {
    setRunning(true);
    try {
      const payload: AccessEvidenceInput = { ...form, content: submittedEvidence };
      const result = await runAccessEvidenceAnalysis(payload);
      onResult(result);
    } finally {
      setRunning(false);
    }
  }

  return (
    <section className="trace-page trace-access-page">
      <div className="trace-page-header trace-page-header-inline">
        <div>
          <span className="trace-eyebrow">IAM / access evidence</span>
          <h1>Access evidence intake</h1>
          <p>Provide redacted evidence so TRACE can structure findings, missing evidence, safe next checks, and non-actions.</p>
        </div>
      </div>

      <section className="trace-info-banner" aria-label="Operator guardrail">
        <div>
          <span className="trace-banner-icon" aria-hidden="true">✓</span>
        </div>
        <div>
          <h2>Read-only • Redacted evidence only</h2>
          <p>Do not paste passwords, tokens, session cookies, personal data, or customer-sensitive content. TRACE structures evidence locally and does not change production systems.</p>
        </div>
      </section>

      <div className="trace-workbench-grid">
        <form className="trace-form trace-evidence-form" onSubmit={(event) => { event.preventDefault(); void run(); }}>
          <fieldset>
            <legend>Evidence source</legend>
            <label>
              <span>Source type</span>
              <select value={form.sourceType} onChange={(event) => useExample(event.target.value as AccessEvidenceInput["sourceType"])}>
                <option value="generic_access_log_text">Generic access log text</option>
                <option value="entra_signin_csv">Entra sign-in CSV</option>
                <option value="resource_assignment_json">Resource assignment guided form</option>
              </select>
            </label>
            <label>
              <span>Affected user</span>
              <input value={form.affectedUser ?? ""} onChange={(event) => update("affectedUser", event.target.value)} />
            </label>
            <label>
              <span>Affected service/resource</span>
              <input value={form.affectedService ?? ""} onChange={(event) => update("affectedService", event.target.value)} />
            </label>
          </fieldset>

          {isResourceGuidedMode ? (
            <fieldset>
              <legend>Resource assignment guided form</legend>
              <div className="trace-guidance-card trace-full-width">
                <strong>Use this when authentication worked but access still fails</strong>
                <p>Collect evidence that separates sign-in, MFA, Conditional Access, expected access, and resource membership before recommending any change.</p>
              </div>
              <div className="trace-guidance-card trace-full-width">
                <strong>Evidence helper</strong>
                <ul>
                  <li><strong>Authentication:</strong> Check Entra sign-in result for the same user, app, and timestamp.</li>
                  <li><strong>MFA / Conditional Access:</strong> Use sign-in details, status, error code, and failure reason.</li>
                  <li><strong>Assignment:</strong> Check the actual resource path: SharePoint/M365 membership, AD group, or app assignment.</li>
                  <li><strong>Expected access:</strong> Confirm with ticket, owner, manager, or access request before recommending membership changes.</li>
                  <li><strong>Observed failure:</strong> Capture exact redacted error text, resource name, and time window. Do not paste secrets.</li>
                </ul>
              </div>
              <label>
                <span>Timestamp / time window</span>
                <input value={resourceGuide.timestamp} onChange={(event) => updateResourceGuide("timestamp", event.target.value)} />
              </label>
              <label>
                <span>Application</span>
                <input value={resourceGuide.application} onChange={(event) => updateResourceGuide("application", event.target.value)} />
              </label>
              <label>
                <span>Sign-in result</span>
                <select value={resourceGuide.authenticationOutcome} onChange={(event) => updateResourceGuide("authenticationOutcome", event.target.value as OutcomeEvidence)}>
                  <option value="success">Succeeded</option>
                  <option value="failure">Failed</option>
                  <option value="unknown">Unknown / not checked</option>
                </select>
              </label>
              <label>
                <span>MFA result</span>
                <select value={resourceGuide.mfaResult} onChange={(event) => updateResourceGuide("mfaResult", event.target.value as MfaEvidence)}>
                  <option value="satisfied">Satisfied</option>
                  <option value="required">Required / pending</option>
                  <option value="failure">Failed</option>
                  <option value="unknown">Unknown / not checked</option>
                </select>
              </label>
              <label>
                <span>Conditional Access result</span>
                <select value={resourceGuide.conditionalAccessStatus} onChange={(event) => updateResourceGuide("conditionalAccessStatus", event.target.value as ConditionalAccessEvidence)}>
                  <option value="success">Success / not blocking</option>
                  <option value="failure">Failure / blocking</option>
                  <option value="notApplied">Not applied</option>
                  <option value="unknown">Unknown / not checked</option>
                </select>
              </label>
              <label>
                <span>Assignment / membership status</span>
                <select value={resourceGuide.assignmentPresent} onChange={(event) => updateResourceGuide("assignmentPresent", event.target.value as TernaryEvidence)}>
                  <option value="false">Missing / not a member</option>
                  <option value="true">Present / member</option>
                  <option value="unknown">Unknown / not checked</option>
                </select>
              </label>
              <label>
                <span>Access expected / approved</span>
                <select value={resourceGuide.expectedAccessConfirmed} onChange={(event) => updateResourceGuide("expectedAccessConfirmed", event.target.value as TernaryEvidence)}>
                  <option value="true">Yes, expected access confirmed</option>
                  <option value="false">No, access not confirmed</option>
                  <option value="unknown">Unknown / not checked</option>
                </select>
              </label>
              <label className="trace-full-width">
                <span>Failure observed by user</span>
                <textarea rows={3} value={resourceGuide.failureReason} onChange={(event) => updateResourceGuide("failureReason", event.target.value)} />
              </label>
              <label className="trace-full-width">
                <span>Evidence checked, one item per line</span>
                <textarea rows={5} value={resourceGuide.evidenceChecked} onChange={(event) => updateResourceGuide("evidenceChecked", event.target.value)} />
              </label>
            </fieldset>
          ) : (
            <fieldset>
              <legend>Evidence content</legend>
              <label className="trace-full-width">
                <span>Paste redacted evidence</span>
                <textarea rows={12} value={form.content} onChange={(event) => update("content", event.target.value)} />
              </label>
            </fieldset>
          )}

          <fieldset>
            <legend>Operator context</legend>
            <label className="trace-full-width">
              <span>Operator notes optional</span>
              <textarea rows={3} value={form.notes ?? ""} onChange={(event) => update("notes", event.target.value)} />
            </label>
          </fieldset>

          <div className="trace-form-footer">
            <p>TRACE helps structure a ticket. It does not modify users, groups, policies, resources, or permissions.</p>
            <button className="trace-primary-button" type="submit" disabled={running || !submittedEvidence.trim()}>{running ? "Analyzing..." : "Analyze evidence"}</button>
          </div>
        </form>

        <aside className="trace-preview-card" aria-label="Structured evidence preview">
          <div className="trace-preview-heading">
            <div>
              <span className="trace-eyebrow">Analyzer input</span>
              <h2>{isResourceGuidedMode ? "Generated structured evidence" : "Submitted evidence"}</h2>
            </div>
            <button className="trace-secondary-button" type="button" onClick={copyStructuredEvidence}>{isResourceGuidedMode ? "Copy JSON" : "Copy evidence"}</button>
          </div>
          <pre className="trace-structured-preview">{submittedEvidence || "No evidence provided yet."}</pre>
          <p className="trace-muted">This is the exact evidence TRACE sends to the analyzer. In guided mode, the JSON is generated from the technician's answers.</p>
        </aside>
      </div>
    </section>
  );
}
