import { useState } from "react";
import { AccessEvidenceInput, runAccessEvidenceAnalysis, StandardDiagnosticResult } from "../../api/traceApi";

type AccessEvidencePageProps = {
  onResult: (result: StandardDiagnosticResult) => void;
};

const examples: Record<AccessEvidenceInput["sourceType"], string> = {
  generic_access_log_text: '2026-07-07T09:22:11Z user=sample.user@contoso.invalid app="SharePoint Online" result=failure reason="blocked by ca policy"',
  entra_signin_csv: `createdDateTime,userPrincipalName,appDisplayName,resourceDisplayName,clientAppUsed,conditionalAccessStatus,authenticationRequirement,status.errorCode,status.failureReason
2026-07-07T09:22:11Z,sample.user@contoso.invalid,SharePoint Online,SharePoint Online,Browser,failure,multiFactorAuthentication,53003,Policy evaluation did not pass`,
  resource_assignment_json: JSON.stringify({
    timestamp: "2026-07-07T11:00:00Z",
    affected_user: "sample.user@contoso.invalid",
    resource: "Engineering Site",
    authentication_outcome: "success",
    assignment_present: false,
    expected_access_confirmed: true,
    conditional_access_status: "success"
  }, null, 2)
};

export function AccessEvidencePage({ onResult }: AccessEvidencePageProps) {
  const [form, setForm] = useState<AccessEvidenceInput>({
    sourceType: "generic_access_log_text",
    affectedUser: "sample.user@contoso.invalid",
    affectedService: "SharePoint Online",
    content: examples.generic_access_log_text,
    notes: "Redacted operator evidence."
  });
  const [running, setRunning] = useState(false);

  function update<K extends keyof AccessEvidenceInput>(key: K, value: AccessEvidenceInput[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function useExample(sourceType: AccessEvidenceInput["sourceType"]) {
    setForm((current) => ({ ...current, sourceType, content: examples[sourceType] }));
  }

  async function run() {
    setRunning(true);
    try {
      const result = await runAccessEvidenceAnalysis(form);
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
        <p>Paste redacted access evidence, choose the source type, and let TRACE structure the finding, missing evidence, safe next checks, and non-actions.</p>
      </div>

      <section className="trace-help-card compact">
        <div>
          <span className="trace-eyebrow">Operator guardrail</span>
          <h2>Use redacted evidence only</h2>
          <p>Do not paste passwords, tokens, session cookies, personal data, or customer-sensitive content. TRACE analyzes evidence locally and does not change production systems.</p>
        </div>
        <ul>
          <li>Generic access log text</li>
          <li>Exported Entra sign-in CSV</li>
          <li>Structured resource assignment JSON</li>
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
              <option value="resource_assignment_json">Resource assignment JSON</option>
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

        <fieldset>
          <legend>Evidence content</legend>
          <label className="trace-full-width">
            <span>Paste redacted evidence</span>
            <textarea rows={12} value={form.content} onChange={(event) => update("content", event.target.value)} />
          </label>
          <label className="trace-full-width">
            <span>Operator notes optional</span>
            <textarea rows={3} value={form.notes ?? ""} onChange={(event) => update("notes", event.target.value)} />
          </label>
        </fieldset>

        <div className="trace-check-row" aria-label="What TRACE checks">
          <span>Parse evidence</span>
          <span>Normalize events</span>
          <span>Detect access pattern</span>
          <span>Show missing evidence</span>
          <span>Generate report</span>
        </div>

        <div className="trace-form-footer">
          <p>TRACE keeps this workflow read-only. It helps structure a ticket; it does not modify users, groups, policies, resources, or permissions.</p>
          <button className="trace-primary-button" type="submit" disabled={running || !form.content.trim()}>{running ? "Analyzing..." : "Analyze evidence"}</button>
        </div>
      </form>
    </section>
  );
}
