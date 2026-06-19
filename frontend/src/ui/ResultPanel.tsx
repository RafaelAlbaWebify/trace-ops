import { buildTicketSummary, StandardDiagnosticResult } from "../api/traceApi";

type ResultPanelProps = {
  result: StandardDiagnosticResult;
};

function ListBlock({ title, items }: { title: string; items?: string[] }) {
  return (
    <details>
      <summary>{title}</summary>
      {items && items.length > 0 ? (
        <ul>
          {items.map((item, index) => <li key={`${title}-${index}`}>{item}</li>)}
        </ul>
      ) : (
        <p className="trace-muted">None recorded.</p>
      )}
    </details>
  );
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
      </div>

      {!hasRun ? (
        <section className="trace-empty-result">
          <h3>No diagnostic run yet</h3>
          <p>Run the selected diagnostic to see the outcome, evidence used, evidence missing, safe next steps, and read-only boundary.</p>
          <ol>
            <li>Confirm the target values.</li>
            <li>Run the diagnostic.</li>
            <li>Review evidence and limitations.</li>
            <li>Copy the ticket summary if needed.</li>
          </ol>
        </section>
      ) : (
        <>
          <div className="trace-result-metrics">
            <div>
              <span>Status</span>
              <strong className={`trace-pill ${String(result.status).includes("error") ? "danger" : String(result.status).includes("finding") || String(result.status).includes("warning") ? "warning" : "success"}`}>
                {result.status}
              </strong>
            </div>
            <div>
              <span>Finding</span>
              <strong className="trace-pill neutral">{result.findingId ?? "none"}</strong>
            </div>
            <div>
              <span>Read-only</span>
              <strong className={`trace-pill ${result.readOnlyKept === false ? "danger" : "success"}`}>
                {result.readOnlyKept === false ? "review" : "boundary kept"}
              </strong>
            </div>
          </div>

          {result.summary && (
            <section className="trace-conclusion">
              <h3>Conclusion</h3>
              <p>{result.summary}</p>
            </section>
          )}

          <section className="trace-ticket-summary">
            <div>
              <h3>Ticket summary</h3>
              <p>{buildTicketSummary(result)}</p>
            </div>
            <button className="trace-secondary-button" onClick={copyTicketSummary}>Copy</button>
          </section>

          <ListBlock title="Evidence used" items={result.evidenceUsed} />
          <ListBlock title="Evidence missing" items={result.evidenceMissing} />
          <ListBlock title="Safe next steps" items={result.safeNextSteps} />
          <ListBlock title="Do not change yet" items={result.doNotChangeYet} />
          <ListBlock title="Limitations" items={result.limitations} />

          <details>
            <summary>Raw JSON</summary>
            <pre className="trace-raw-json">{JSON.stringify(result.raw ?? {}, null, 2)}</pre>
          </details>
        </>
      )}
    </aside>
  );
}
