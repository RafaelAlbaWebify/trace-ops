import { BackendHealth, modules } from "../registry";

type OverviewPageProps = {
  health: BackendHealth;
  historyCount: number;
  onSelect: (id: string) => void;
};

export function OverviewPage({ health, historyCount, onSelect }: OverviewPageProps) {
  const validated = modules.filter((module) => module.maturity === "Validated lab diagnostic");

  return (
    <section className="trace-page">
      <div className="trace-page-header">
        <span className="trace-eyebrow">Overview</span>
        <h1>Operator dashboard</h1>
        <p>TRACE is a read-only diagnostic console. Select a scenario, run a diagnostic, and use the result panel for evidence and ticket-ready next steps.</p>
      </div>

      <section className="trace-help-card" aria-label="How to use TRACE">
        <div>
          <span className="trace-eyebrow">Help</span>
          <h2>How to use TRACE</h2>
          <p>Use TRACE as an evidence collector and decision-support tool. It should help you understand what to check next, not silently change systems.</p>
        </div>
        <ol>
          <li>Select a module from the sidebar.</li>
          <li>Confirm the target values in the workspace.</li>
          <li>Run the diagnostic in read-only mode.</li>
          <li>Review the result panel for evidence, limitations, and safe next steps.</li>
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
          <p>TRACE reports evidence and safe next steps. It does not change AD, DNS, SMB, endpoint, or tenant settings.</p>
        </article>
        <article className="trace-card">
          <span className="trace-eyebrow">Validated diagnostic</span>
          <strong>{validated.length}</strong>
          <p>FactoryOps share access is the current validated lab workflow.</p>
        </article>
        <article className="trace-card">
          <span className="trace-eyebrow">History</span>
          <strong>{historyCount}</strong>
          <p>Local diagnostic runs and report links.</p>
        </article>
      </section>

      <section className="trace-action-card">
        <div>
          <span className="trace-eyebrow">Recommended next action</span>
          <h2>Run the FactoryOps share-access diagnostic</h2>
          <p>This is the strongest validated scenario for the current v1 portfolio release.</p>
        </div>
        <button className="trace-primary-button" onClick={() => onSelect("share-access")}>Open Share access</button>
      </section>

      <section className="trace-module-summary">
        <h2>Module maturity</h2>
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
