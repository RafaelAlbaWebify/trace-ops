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
  }

  async function run() {
    setRunning(true);
    try {
      const payload: AccessEvidenceInput = isResourceGuidedMode
        ? { ...form, content: generatedResourceJson }
        : form;
      const result = await runAccessEvidenceAnalysis(payload);
      onResult(result);
    } finally {
      setRunning(false);
    }
  }

  return (
    <section className="trace-page">
      <div className="trace-page-header">
        <span className="trace-eyebrow">IAM / access evidence</span>
        <h1>Access evidence intake</h1>
        <p>Paste redacted access evidence, choose the source type, or use the guided resource-assignment check to structure what the technician verified.</p>
      </div>

      <section className="trace-help-card compact">
        <div>
          <span className="trace-eyebrow">Operator guardrail</span>
          <h2>Use redacted evidence only</h2>
          <p>TRACE helps the technician collect and structure access evidence locally. It does not change users, groups, policies, resources, or permissions.</p>
        </div>
        <ul>
          <li>Generic access log text</li>
          <li>Exported Entra sign-in CSV</li>
          <li>Guided resource assignment check</li>
          <li>Ticket-ready Markdown in the result panel</li>
        </ul>
      </section>

      <form className="trace-form" onSubmit={(event) => { event.preventDefault(); void run(); }}>
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

        {isResourceGuidedMode && (
          <fieldset>
            <legend>Guided resource assignment check</legend>
            <section className="trace-help-card compact">
              <div>
                <span className="trace-eyebrow">Where to get the evidence</span>
                <h2>Check these before changing access</h2>
                <p>Use the normal admin portals, ticket/request context, or approved evidence sources. TRACE only structures what you verified.</p>
              </div>
              <ul>
                <li>Entra sign-in log: authentication, MFA, Conditional Access</li>
                <li>Ticket/resource owner: whether access is expected</li>
                <li>SharePoint/M365 group/AD group/app role: whether assignment exists</li>
                <li>Retest notes: what the user sees after sign-in</li>
              </ul>
            </section>

            <label>
              <span>Timestamp / time window</span>
              <input value={resourceGuide.timestamp} onChange={(event) => updateResourceGuide("timestamp", event.target.value)} />
            </label>
            <label>
              <span>Application</span>
              <input value={resourceGuide.application} onChange={(event) => updateResourceGuide("application", event.target.value)} />
            </label>
            <label>
              <span>Did sign-in/authentication succeed?</span>
              <select value={resourceGuide.authenticationOutcome} onChange={(event) => updateResourceGuide("authenticationOutcome", event.target.value as OutcomeEvidence)}>
                <option value="success">Yes, sign-in succeeded</option>
                <option value="failure">No, sign-in failed</option>
                <option value="unknown">Unknown / not checked</option>
              </select>
            </label>
            <label>
              <span>Did MFA pass?</span>
              <select value={resourceGuide.mfaResult} onChange={(event) => updateResourceGuide("mfaResult", event.target.value as MfaEvidence)}>
                <option value="satisfied">Yes, MFA satisfied</option>
                <option value="required">MFA required / pending</option>
                <option value="failure">MFA failed</option>
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
              <span>Is the user assigned/member of the resource access path?</span>
              <select value={resourceGuide.assignmentPresent} onChange={(event) => updateResourceGuide("assignmentPresent", event.target.value as TernaryEvidence)}>
                <option value="false">No, assignment/membership missing</option>
                <option value="true">Yes, assignment/membership present</option>
                <option value="unknown">Unknown / not checked</option>
              </select>
            </label>
            <label>
              <span>Is access expected/approved?</span>
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
        )}

        <fieldset>
          <legend>{isResourceGuidedMode ? "Generated structured evidence" : "Evidence content"}</legend>
          <label className="trace-full-width">
            <span>{isResourceGuidedMode ? "Generated JSON preview" : "Paste redacted evidence"}</span>
            <textarea
              rows={isResourceGuidedMode ? 10 : 12}
              value={isResourceGuidedMode ? generatedResourceJson : form.content}
              readOnly={isResourceGuidedMode}
              onChange={(event) => update("content", event.target.value)}
            />
          </label>
          <label className="trace-full-width">
            <span>Operator notes optional</span>
            <textarea rows={3} value={form.notes ?? ""} onChange={(event) => update("notes", event.target.value)} />
          </label>
        </fieldset>

        <div className="trace-check-row" aria-label="What TRACE checks">
          <span>Collect evidence</span>
          <span>Generate structure</span>
          <span>Normalize events</span>
          <span>Detect access pattern</span>
          <span>Show safe next steps</span>
        </div>

        <div className="trace-form-footer">
          <p>TRACE keeps this workflow read-only. It helps structure a ticket; it does not modify users, groups, policies, resources, or permissions.</p>
          <button className="trace-primary-button" type="submit" disabled={running || (!isResourceGuidedMode && !form.content.trim())}>{running ? "Analyzing..." : "Analyze evidence"}</button>
        </div>
      </form>
    </section>
  );
}
