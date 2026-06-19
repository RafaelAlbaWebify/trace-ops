import { StandardDiagnosticResult } from "../../api/traceApi";

type AdUserAccessPageProps = {
  type: "access" | "readiness";
  onResult: (result: StandardDiagnosticResult) => void;
};

export function AdUserAccessPage({ type, onResult }: AdUserAccessPageProps) {
  const title = type === "access" ? "AD user access" : "AD readiness";

  function sample() {
    onResult({
      title,
      status: "not_run",
      summary: `${title} is available as a sample/readiness module in the current UI shell.`,
      evidenceUsed: [],
      evidenceMissing: ["Live AD endpoint execution is not part of this UI shell rebuild."],
      safeNextSteps: ["Use a domain-joined lab machine and validated read-only collector before treating AD evidence as real."],
      doNotChangeYet: ["Do not change AD account state or group membership from a sample result."],
      limitations: ["Sample/readiness page."],
      readOnlyKept: true,
      raw: {}
    });
  }

  return (
    <section className="trace-page">
      <div className="trace-page-header">
        <span className="trace-eyebrow">Identity</span>
        <h1>{title}</h1>
        <p>Validate account-state, lockout, password, and group-context evidence when the backend diagnostic is connected.</p>
      </div>
      <section className="trace-placeholder-card">
        <h2>{type === "access" ? "Sample diagnostic" : "Readiness check"}</h2>
        <p>This module is intentionally separated from the shell so it can evolve without making App.tsx monolithic.</p>
        <button className="trace-secondary-button" onClick={sample}>Show sample result</button>
      </section>
    </section>
  );
}
