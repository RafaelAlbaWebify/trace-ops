import { buildTicketSummary, StandardDiagnosticResult } from "../api/traceApi";

type ResultPanelProps = {
  result: StandardDiagnosticResult;
};

function ListBlock({ title, items }: { title: string; items?: string[] }) {
  return (
    <section className="trace-result-section">
      <h3>{title}</h3>
      {items && items.length > 0 ? (
        <ul>
          {items.map((item, index) => <li key={`${title}-${index}`}>{item}</li>)}
        </ul>
      ) : (
        <p className="trace-muted">None recorded.</p>
      )}
    </section>
  );
}

function statusClass(value?: string | null): string {
  const text = String(value ?? "").toLowerCase();
  if (text.includes("error") || text.includes("fail")) return "danger";
  if (text.includes("finding") || text.includes("warning") || text.includes("insufficient")) return "warning";
  return "success";
}

export function ResultPanel({ result }: ResultPanelProps) {
  const hasRun = Boolean(result.status && result.status !== "not_run");

  async function copyTicketSummary() {
    const text = buildTicketSummary(result);
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      // Clipboard can be unavailable in some local contexts. The text remains visible.
    }
  }

  return (
    <aside className="trace-result-panel" aria-label="Diagnostic result panel">
      <div className="trace-result-heading">
        <span className="trace-eyebrow">Result</span>
        <h2>{result.title}</h2>
        <p>Review the finding, evidence, safe next checks, and non-actions before updating a ticket or escalating.</p>
      </div>

      {!hasRun ? (
        <section className="trace-empty-result">
          <h3>No diagnostic run yet</h3>
          <p>Run the selected workflow to see the outcome, evidence used, evidence missing, safe next steps, and read-only boundary.</p>
          <ol>
            <li>Confirm the affected user and resource.</li>
            <li>Provide redacted evidence or guided answers.</li>
            <li>Run the analyzer.</li>
            <li>Copy the ticket summary if useful.</li>
          </ol>
        </section>
      ) : (
        <>
          <section className="trace-finding-card">
            <div className="trace-finding-header">
              <span className={`trace-pill ${statusClass(result.status)}`}>{result.status}</span>
              <span className="trace-pill neutral">{result.findingId ?? "no finding id"}</span>
            </div>
            <h3>{result.summary ?? "No conclusion returned."}</h3>
            <div className="trace-result-metrics">
              <div>
                <span>Confidence</span>
                <strong>{result.confidence ?? "unknown"}</strong>
              </div>
              <div>
                <span>Read-only</span>
                <strong>{result.readOnlyKept === false ? "review" : "boundary kept"}</strong>
              </div>
              <div>
                <span>Evidence used</span>
                <strong>{result.evidenceUsed?.length ?? 0}</strong>
              </div>
              <div>
                <span>Missing evidence</span>
                <strong>{result.evidenceMissing?.length ?? 0}</strong>
              </div>
            </div>
          </section>

          <section className="trace-ticket-summary">
            <div>
              <h3>Ticket summary</h3>
              <p>{buildTicketSummary(result)}</p>
            </div>
            <button className="trace-secondary-button" onClick={copyTicketSummary}>Copy summary</button>
          </section>

          <div className="trace-result-grid">
            <ListBlock title="Evidence used" items={result.evidenceUsed} />
            <ListBlock title="Evidence missing" items={result.evidenceMissing} />
            <ListBlock title="Safe next steps" items={result.safeNextSteps} />
            <ListBlock title="Do not change yet" items={result.doNotChangeYet} />
            <ListBlock title="Limitations" items={result.limitations} />
          </div>

          <details className="trace-raw-section">
            <summary>Raw JSON</summary>
            <pre className="trace-raw-json">{JSON.stringify(result.raw ?? {}, null, 2)}</pre>
          </details>
        </>
      )}
    </aside>
  );
}
