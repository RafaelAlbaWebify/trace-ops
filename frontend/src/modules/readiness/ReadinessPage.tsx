import { StandardDiagnosticResult } from "../../api/traceApi";

type ReadinessPageProps = {
  title: string;
  group: string;
  onResult: (result: StandardDiagnosticResult) => void;
};

export function ReadinessPage({ title, group, onResult }: ReadinessPageProps) {
  function sample() {
    onResult({
      title,
      status: "warning",
      summary: `${title} is shown as a readiness placeholder in the rebuilt UI shell.`,
      evidenceUsed: ["UI shell loaded successfully.", "Read-only mode is explicit."],
      evidenceMissing: ["Live readiness endpoint has not been confirmed from this page."],
      safeNextSteps: ["Use the validated FactoryOps workflow for release evidence.", "Wire this module to a backend endpoint in a future milestone."],
      doNotChangeYet: ["Do not change local, AD, DNS, or tenant settings from a readiness placeholder."],
      limitations: ["Readiness placeholder."],
      readOnlyKept: true,
      raw: {}
    });
  }

  return (
    <section className="trace-page">
      <div className="trace-page-header">
        <span className="trace-eyebrow">{group}</span>
        <h1>{title}</h1>
        <p>Readiness checks explain whether the current operator context is prepared for a diagnostic.</p>
      </div>
      <section className="trace-placeholder-card">
        <h2>Readiness module</h2>
        <p>This module is part of the modular shell and can be wired to richer backend evidence later.</p>
        <button className="trace-secondary-button" onClick={sample}>Show readiness result</button>
      </section>
    </section>
  );
}
