import { useState } from "react";
import { AccessEvidenceInput, runAccessEvidenceAnalysis, StandardDiagnosticResult } from "../../api/traceApi";

type AccessEvidencePageProps = {
  onResult: (result: StandardDiagnosticResult) => void;
};

type EvidenceMode = AccessEvidenceInput["sourceType"] | "entra_signin_guided_form" | "license_service_plan_guided_form";
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

type EntraGuidedForm = {
  timestamp: string;
  application: string;
  resource: string;
  clientApp: string;
  ipAddress: string;
  conditionalAccessStatus: ConditionalAccessEvidence;
  authenticationRequirement: string;
  status: string;
  statusErrorCode: string;
  failureReason: string;
  deviceCompliance: string;
};

type LicenseServicePlanGuide = {
  timestamp: string;
  application: string;
  resource: string;
  sku: string;
  servicePlan: string;
  licenseAssigned: TernaryEvidence;
  servicePlanEnabled: TernaryEvidence;
  licensingSource: string;
  recentChange: TernaryEvidence;
  failureReason: string;
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

const defaultEntraGuide: EntraGuidedForm = {
  timestamp: "2026-07-07T09:22:11Z",
  application: "SharePoint Online",
  resource: "SharePoint Online",
  clientApp: "Browser",
  ipAddress: "203.0.113.10",
  conditionalAccessStatus: "failure",
  authenticationRequirement: "multiFactorAuthentication",
  status: "failure",
  statusErrorCode: "53003",
  failureReason: "Access has been blocked by Conditional Access policies.",
  deviceCompliance: "false"
};

const defaultLicenseGuide: LicenseServicePlanGuide = {
  timestamp: "2026-07-07T10:10:00Z",
  application: "Exchange Online",
  resource: "User mailbox",
  sku: "Microsoft 365 E3",
  servicePlan: "EXCHANGE_S_ENTERPRISE",
  licenseAssigned: "false",
  servicePlanEnabled: "false",
  licensingSource: "group-based licensing",
  recentChange: "unknown",
  failureReason: "User is not licensed for Exchange Online or the required service plan is disabled."
};

function ternaryToBoolean(value: TernaryEvidence): boolean | undefined {
  if (value === "true") return true;
  if (value === "false") return false;
  return undefined;
}

function evidenceLines(value: string): string[] {
  return value.split("\n").map((line) => line.trim()).filter(Boolean);
}

function csvEscape(value: string | undefined): string {
  const text = value ?? "";
  if (/[",\n\r]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

function buildCsv(headers: string[], values: string[]): string {
  return `${headers.join(",")}\n${values.map(csvEscape).join(",")}`;
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

function buildEntraGuidedCsv(form: AccessEvidenceInput, guide: EntraGuidedForm): string {
  const headers = [
    "createdDateTime",
    "userPrincipalName",
    "appDisplayName",
    "resourceDisplayName",
    "clientAppUsed",
    "ipAddress",
    "conditionalAccessStatus",
    "authenticationRequirement",
    "status",
    "status.errorCode",
    "status.failureReason",
    "deviceDetail.isCompliant"
  ];
  const values = [
    guide.timestamp,
    form.affectedUser || "sample.user@contoso.invalid",
    guide.application,
    guide.resource || form.affectedService || guide.application,
    guide.clientApp,
    guide.ipAddress,
    guide.conditionalAccessStatus,
    guide.authenticationRequirement,
    guide.status,
    guide.statusErrorCode,
    guide.failureReason,
    guide.deviceCompliance
  ];
  return buildCsv(headers, values);
}

function buildLicenseServicePlanEvidence(form: AccessEvidenceInput, guide: LicenseServicePlanGuide): string {
  const user = form.affectedUser || "sample.user@contoso.invalid";
  const resource = guide.resource || form.affectedService || guide.application;
  const licenseState = guide.licenseAssigned === "true" ? "license assigned" : guide.licenseAssigned === "false" ? "not licensed" : "license unknown";
  const servicePlanState = guide.servicePlanEnabled === "true" ? "service plan enabled" : guide.servicePlanEnabled === "false" ? "service plan disabled" : "service plan unknown";
  return [
    `${guide.timestamp} user=${user} app="Microsoft 365" result=success reason="authentication succeeded before license check"`,
    `${guide.timestamp} user=${user} app="${guide.application}" resource="${resource}" result=failure reason="${guide.failureReason} ${licenseState}; ${servicePlanState}" sku="${guide.sku}" service_plan="${guide.servicePlan}" licensing_source="${guide.licensingSource}" recent_license_change="${guide.recentChange}"`
  ].join("\n");
}

const examples: Record<AccessEvidenceInput["sourceType"], string> = {
  generic_access_log_text: '2026-07-07T09:22:11Z user=sample.user@contoso.invalid app="SharePoint Online" result=failure reason="blocked by ca policy"',
  entra_signin_csv: `createdDateTime,userPrincipalName,appDisplayName,resourceDisplayName,clientAppUsed,conditionalAccessStatus,authenticationRequirement,status.errorCode,status.failureReason
2026-07-07T09:22:11Z,sample.user@contoso.invalid,SharePoint Online,SharePoint Online,Browser,failure,multiFactorAuthentication,53003,Policy evaluation did not pass`,
  resource_assignment_json: ""
};

function sourceTypeForMode(mode: EvidenceMode): AccessEvidenceInput["sourceType"] {
  if (mode === "entra_signin_guided_form") return "entra_signin_csv";
  if (mode === "license_service_plan_guided_form") return "generic_access_log_text";
  return mode;
}

function modeLabel(mode: EvidenceMode): string {
  const labels: Record<EvidenceMode, string> = {
    generic_access_log_text: "Generic access log text",
    entra_signin_csv: "Entra sign-in CSV",
    entra_signin_guided_form: "Conditional Access / MFA guided form",
    license_service_plan_guided_form: "License / Service Plan guided form",
    resource_assignment_json: "Resource assignment guided form"
  };
  return labels[mode];
}

function emptyAccessResult(mode: EvidenceMode): StandardDiagnosticResult {
  return {
    title: "Access evidence analyzer",
    status: "not_run",
    findingId: null,
    summary: `Ready to analyze ${modeLabel(mode)} evidence.`,
    evidenceUsed: [],
    evidenceMissing: [],
    safeNextSteps: [],
    doNotChangeYet: [],
    limitations: [],
    readOnlyKept: true,
    raw: { mode, sourceType: sourceTypeForMode(mode) }
  };
}

export function AccessEvidencePage({ onResult }: AccessEvidencePageProps) {
  const [mode, setMode] = useState<EvidenceMode>("generic_access_log_text");
  const [resourceGuide, setResourceGuide] = useState<ResourceAssignmentGuide>(defaultResourceGuide);
  const [entraGuide, setEntraGuide] = useState<EntraGuidedForm>(defaultEntraGuide);
  const [licenseGuide, setLicenseGuide] = useState<LicenseServicePlanGuide>(defaultLicenseGuide);
  const [form, setForm] = useState<AccessEvidenceInput>({
    sourceType: "generic_access_log_text",
    affectedUser: "sample.user@contoso.invalid",
    affectedService: "SharePoint Online",
    content: examples.generic_access_log_text,
    notes: "Redacted operator evidence."
  });
  const [running, setRunning] = useState(false);

  const generatedResourceJson = buildResourceAssignmentJson(form, resourceGuide);
  const generatedEntraCsv = buildEntraGuidedCsv(form, entraGuide);
  const generatedLicenseEvidence = buildLicenseServicePlanEvidence(form, licenseGuide);
  const isResourceGuidedMode = mode === "resource_assignment_json";
  const isEntraGuidedMode = mode === "entra_signin_guided_form";
  const isLicenseGuidedMode = mode === "license_service_plan_guided_form";
  const submittedEvidence = isResourceGuidedMode ? generatedResourceJson : isEntraGuidedMode ? generatedEntraCsv : isLicenseGuidedMode ? generatedLicenseEvidence : form.content;

  function update<K extends keyof AccessEvidenceInput>(key: K, value: AccessEvidenceInput[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function updateResourceGuide<K extends keyof ResourceAssignmentGuide>(key: K, value: ResourceAssignmentGuide[K]) {
    setResourceGuide((current) => ({ ...current, [key]: value }));
  }

  function updateEntraGuide<K extends keyof EntraGuidedForm>(key: K, value: EntraGuidedForm[K]) {
    setEntraGuide((current) => ({ ...current, [key]: value }));
  }

  function updateLicenseGuide<K extends keyof LicenseServicePlanGuide>(key: K, value: LicenseServicePlanGuide[K]) {
    setLicenseGuide((current) => ({ ...current, [key]: value }));
  }

  function useExample(nextMode: EvidenceMode) {
    setMode(nextMode);
    setForm((current) => {
      const nextSourceType = sourceTypeForMode(nextMode);
      return {
        ...current,
        sourceType: nextSourceType,
        content: nextMode === "resource_assignment_json"
          ? buildResourceAssignmentJson(current, resourceGuide)
          : nextMode === "entra_signin_guided_form"
            ? buildEntraGuidedCsv(current, entraGuide)
            : nextMode === "license_service_plan_guided_form"
              ? buildLicenseServicePlanEvidence(current, licenseGuide)
              : examples[nextSourceType],
        affectedService: nextMode === "resource_assignment_json" ? "Engineering SharePoint Site" : nextMode === "license_service_plan_guided_form" ? licenseGuide.application : current.affectedService
      };
    });
    onResult(emptyAccessResult(nextMode));
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
      const payload: AccessEvidenceInput = { ...form, sourceType: sourceTypeForMode(mode), content: submittedEvidence };
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
              <select value={mode} onChange={(event) => useExample(event.target.value as EvidenceMode)}>
                <option value="generic_access_log_text">Generic access log text</option>
                <option value="entra_signin_csv">Entra sign-in CSV</option>
                <option value="entra_signin_guided_form">Conditional Access / MFA guided form</option>
                <option value="license_service_plan_guided_form">License / Service Plan guided form</option>
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

          {isEntraGuidedMode ? (
            <fieldset>
              <legend>Conditional Access / MFA guided form</legend>
              <div className="trace-guidance-card trace-full-width">
                <strong>Use this when sign-in evidence points to MFA, Conditional Access, client app, or device compliance</strong>
                <p>TRACE will generate a redacted Entra sign-in CSV row from these fields and analyze it with the existing Entra export analyzer.</p>
              </div>
              <div className="trace-guidance-card trace-full-width">
                <strong>Evidence helper</strong>
                <ul>
                  <li><strong>Same event:</strong> Use one sign-in event for the affected user, app, resource, and time window.</li>
                  <li><strong>Conditional Access:</strong> Record the policy result and failure reason, but do not exclude users or disable policy from this evidence alone.</li>
                  <li><strong>MFA:</strong> Use the sign-in detail value, not the user description of the prompt.</li>
                  <li><strong>Client/device:</strong> Keep client app and device compliance because they often explain policy decisions.</li>
                </ul>
              </div>
              <label><span>Timestamp / time window</span><input value={entraGuide.timestamp} onChange={(event) => updateEntraGuide("timestamp", event.target.value)} /></label>
              <label><span>Application</span><input value={entraGuide.application} onChange={(event) => updateEntraGuide("application", event.target.value)} /></label>
              <label><span>Resource</span><input value={entraGuide.resource} onChange={(event) => updateEntraGuide("resource", event.target.value)} /></label>
              <label>
                <span>Client app</span>
                <select value={entraGuide.clientApp} onChange={(event) => updateEntraGuide("clientApp", event.target.value)}>
                  <option value="Browser">Browser</option>
                  <option value="Mobile Apps and Desktop clients">Mobile Apps and Desktop clients</option>
                  <option value="Other clients">Other clients</option>
                  <option value="IMAP">IMAP</option>
                  <option value="POP">POP</option>
                  <option value="SMTP">SMTP</option>
                </select>
              </label>
              <label>
                <span>Sign-in status</span>
                <select value={entraGuide.status} onChange={(event) => updateEntraGuide("status", event.target.value)}>
                  <option value="failure">Failure</option>
                  <option value="success">Success</option>
                  <option value="interrupted">Interrupted</option>
                </select>
              </label>
              <label>
                <span>Conditional Access result</span>
                <select value={entraGuide.conditionalAccessStatus} onChange={(event) => updateEntraGuide("conditionalAccessStatus", event.target.value as ConditionalAccessEvidence)}>
                  <option value="failure">Failure / blocking</option>
                  <option value="success">Success / not blocking</option>
                  <option value="notApplied">Not applied</option>
                  <option value="unknown">Unknown / not checked</option>
                </select>
              </label>
              <label>
                <span>Authentication requirement</span>
                <select value={entraGuide.authenticationRequirement} onChange={(event) => updateEntraGuide("authenticationRequirement", event.target.value)}>
                  <option value="multiFactorAuthentication">multiFactorAuthentication</option>
                  <option value="singleFactorAuthentication">singleFactorAuthentication</option>
                  <option value="unknown">Unknown / not checked</option>
                </select>
              </label>
              <label><span>Error code</span><input value={entraGuide.statusErrorCode} onChange={(event) => updateEntraGuide("statusErrorCode", event.target.value)} /></label>
              <label>
                <span>Device compliant</span>
                <select value={entraGuide.deviceCompliance} onChange={(event) => updateEntraGuide("deviceCompliance", event.target.value)}>
                  <option value="false">False</option>
                  <option value="true">True</option>
                  <option value="unknown">Unknown / not checked</option>
                </select>
              </label>
              <label><span>IP address redacted/sample</span><input value={entraGuide.ipAddress} onChange={(event) => updateEntraGuide("ipAddress", event.target.value)} /></label>
              <label className="trace-full-width"><span>Failure reason</span><textarea rows={3} value={entraGuide.failureReason} onChange={(event) => updateEntraGuide("failureReason", event.target.value)} /></label>
            </fieldset>
          ) : isLicenseGuidedMode ? (
            <fieldset>
              <legend>License / Service Plan guided form</legend>
              <div className="trace-guidance-card trace-full-width">
                <strong>Use this when authentication works but the service says the user is not licensed</strong>
                <p>TRACE generates redacted access evidence and checks for license or service-plan symptoms without changing assignments.</p>
              </div>
              <div className="trace-guidance-card trace-full-width">
                <strong>Evidence helper</strong>
                <ul>
                  <li><strong>License SKU:</strong> Confirm the expected product SKU and whether assignment is direct or group-based.</li>
                  <li><strong>Service plan:</strong> Check whether the specific service plan is enabled, not only whether a product license exists.</li>
                  <li><strong>Propagation:</strong> Check recent license changes before removing/reassigning licenses.</li>
                  <li><strong>Comparison:</strong> Compare with a known-good user who can access the same service.</li>
                </ul>
              </div>
              <label><span>Timestamp / time window</span><input value={licenseGuide.timestamp} onChange={(event) => updateLicenseGuide("timestamp", event.target.value)} /></label>
              <label><span>Application</span><input value={licenseGuide.application} onChange={(event) => updateLicenseGuide("application", event.target.value)} /></label>
              <label><span>Resource</span><input value={licenseGuide.resource} onChange={(event) => updateLicenseGuide("resource", event.target.value)} /></label>
              <label><span>License SKU</span><input value={licenseGuide.sku} onChange={(event) => updateLicenseGuide("sku", event.target.value)} /></label>
              <label><span>Service plan</span><input value={licenseGuide.servicePlan} onChange={(event) => updateLicenseGuide("servicePlan", event.target.value)} /></label>
              <label>
                <span>License assigned</span>
                <select value={licenseGuide.licenseAssigned} onChange={(event) => updateLicenseGuide("licenseAssigned", event.target.value as TernaryEvidence)}>
                  <option value="false">No / missing</option>
                  <option value="true">Yes</option>
                  <option value="unknown">Unknown / not checked</option>
                </select>
              </label>
              <label>
                <span>Service plan enabled</span>
                <select value={licenseGuide.servicePlanEnabled} onChange={(event) => updateLicenseGuide("servicePlanEnabled", event.target.value as TernaryEvidence)}>
                  <option value="false">No / disabled</option>
                  <option value="true">Yes</option>
                  <option value="unknown">Unknown / not checked</option>
                </select>
              </label>
              <label>
                <span>Licensing source</span>
                <select value={licenseGuide.licensingSource} onChange={(event) => updateLicenseGuide("licensingSource", event.target.value)}>
                  <option value="group-based licensing">Group-based licensing</option>
                  <option value="direct assignment">Direct assignment</option>
                  <option value="unknown">Unknown / not checked</option>
                </select>
              </label>
              <label>
                <span>Recent license change</span>
                <select value={licenseGuide.recentChange} onChange={(event) => updateLicenseGuide("recentChange", event.target.value as TernaryEvidence)}>
                  <option value="unknown">Unknown / not checked</option>
                  <option value="true">Yes</option>
                  <option value="false">No</option>
                </select>
              </label>
              <label className="trace-full-width"><span>Observed failure / portal message</span><textarea rows={3} value={licenseGuide.failureReason} onChange={(event) => updateLicenseGuide("failureReason", event.target.value)} /></label>
            </fieldset>
          ) : isResourceGuidedMode ? (
            <fieldset>
              <legend>Resource assignment guided form</legend>
              <div className="trace-guidance-card trace-full-width">
                <strong>Use this when authentication worked but access still fails</strong>
                <p>Collect enough evidence to separate sign-in, MFA, Conditional Access, expected access, and resource membership before recommending any change.</p>
              </div>
              <div className="trace-guidance-card trace-full-width">
                <strong>Evidence helper</strong>
                <ul>
                  <li><strong>Authentication:</strong> Check the Entra sign-in result for the same user, application, and timestamp.</li>
                  <li><strong>MFA / Conditional Access:</strong> Use sign-in details, status, error code, and failure reason before changing policies.</li>
                  <li><strong>Assignment:</strong> Check the actual access path: SharePoint/M365 membership, AD group, or app assignment.</li>
                  <li><strong>Expected access:</strong> Confirm with ticket, owner, manager, or access request before recommending membership changes.</li>
                  <li><strong>Observed failure:</strong> Capture exact redacted error text, resource name, and time window. Do not paste secrets.</li>
                </ul>
              </div>
              <label><span>Timestamp / time window</span><input value={resourceGuide.timestamp} onChange={(event) => updateResourceGuide("timestamp", event.target.value)} /></label>
              <label><span>Application</span><input value={resourceGuide.application} onChange={(event) => updateResourceGuide("application", event.target.value)} /></label>
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
              <label className="trace-full-width"><span>Failure observed by user</span><textarea rows={3} value={resourceGuide.failureReason} onChange={(event) => updateResourceGuide("failureReason", event.target.value)} /></label>
              <label className="trace-full-width"><span>Evidence checked, one item per line</span><textarea rows={5} value={resourceGuide.evidenceChecked} onChange={(event) => updateResourceGuide("evidenceChecked", event.target.value)} /></label>
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
            <label className="trace-full-width"><span>Operator notes optional</span><textarea rows={3} value={form.notes ?? ""} onChange={(event) => update("notes", event.target.value)} /></label>
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
              <h2>{isResourceGuidedMode ? "Generated structured evidence" : isEntraGuidedMode ? "Generated Entra sign-in CSV" : isLicenseGuidedMode ? "Generated license evidence" : "Submitted evidence"}</h2>
            </div>
            <button className="trace-secondary-button" type="button" onClick={copyStructuredEvidence}>{isResourceGuidedMode ? "Copy JSON" : isEntraGuidedMode ? "Copy CSV" : "Copy evidence"}</button>
          </div>
          <pre className="trace-structured-preview">{submittedEvidence || "No evidence provided yet."}</pre>
          <p className="trace-muted">This is the exact evidence TRACE sends to the analyzer. Guided modes generate structured evidence from the technician's answers.</p>
        </aside>
      </div>
    </section>
  );
}
