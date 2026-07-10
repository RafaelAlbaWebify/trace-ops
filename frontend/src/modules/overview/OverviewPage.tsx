import { BackendHealth, modules } from "../registry";

type OverviewPageProps = {
  health: BackendHealth;
  historyCount: number;
  onSelect: (id: string) => void;
};

export function OverviewPage({ health, historyCount, onSelect }: OverviewPageProps) {
  const evidenceModules = modules.filter((module) => module.maturity === "Evidence");

  return (
    <section className="trace-page">
      <div className="trace-page-header">
        <span className="trace-eyebrow">IAM / Access Evidence</span>
        <h1>TRACE operator dashboard</h1>
        <p>TRACE is a local-first IAM evidence workbench. Use it to structure redacted access evidence, identify missing context, and prepare safe ticket-ready next steps.</p>
      </div>

      <section className="trace-help-card" aria-label="How to use TRACE">
        <div>
          <span className="trace-eyebrow">Workflow</span>
          <h2>How to use TRACE</h2>
          <p>Use TRACE as an evidence and decision-support tool for IAM/access cases. It should clarify what to check next, not silently change systems.</p>
        </div>
        <ol>
          <li>Open the Access evidence workspace.</li>
          <li>Select the relevant evidence source or guided form.</li>
          <li>Run the analyzer using redacted/sample evidence.</li>
          <li>Review the finding, missing evidence, safe next checks, and non-actions.</li>
        </ol>
      </section>

      <section className="trace-overview-grid">
        <article className="trace-card">
          <span className="trace-eyebrow">Backend</span>
          <strong className={`trace-pill ${health.ok ? "success" : "warning"}`}>{health.ok ? "ok" : "unknown"}</strong>
          <p>{health.endpoint ? `Health endpoint: ${health.endpoint}` : "Backend health endpoint not confirmed."}</p>
        </article>
        <article className="trace-card">
          <span className="trace-eyebrow">Mode</span>
          <strong className="trace-pill success">Read-only</strong>
          <p>TRACE reports IAM evidence and safe next steps. It does not change users, groups, policies, licenses, resources, or tenant settings.</p>
        </article>
        <article className="trace-card">
          <span className="trace-eyebrow">Visible scope</span>
          <strong>{evidenceModules.length}</strong>
          <p>Only release-ready IAM evidence modules are shown in the sidebar.</p>
        </article>
        <article className="trace-card">
          <span className="trace-eyebrow">History</span>
          <strong>{historyCount}</strong>
          <p>Local IAM evidence runs and report links.</p>
        </article>
      </section>

      <section className="trace-action-card">
        <div>
          <span className="trace-eyebrow">Recommended next action</span>
          <h2>Run the Access Evidence analyzer</h2>
          <p>This is the validated release workflow for TRACE as an IAM Engineer portfolio project.</p>
        </div>
        <button className="trace-primary-button" onClick={() => onSelect("access-evidence")}>Open Access evidence</button>
      </section>

      <section className="trace-module-summary">
        <h2>Release modules</h2>
        <div className="trace-module-grid">
          {modules.map((module) => (
            <article key={module.id} className="trace-module-card">
              <span className="trace-eyebrow">{module.group}</span>
              <h3>{module.label}</h3>
              <strong className="trace-pill neutral">{module.maturity}</strong>
              <p>{module.description}</p>
            </article>
          ))}
        </div>
      </section>
    </section>
  );
}
