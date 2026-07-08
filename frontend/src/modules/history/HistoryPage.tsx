type HistoryPageProps = {
  history: unknown[];
};

function renderItem(item: unknown, index: number) {
  if (!item || typeof item !== "object") {
    return { id: index + 1, user: "unknown", service: String(item), status: "ok", rule: "none" };
  }
  const obj = item as Record<string, unknown>;
  return {
    id: obj.id ?? obj.run_id ?? index + 1,
    user: obj.affected_user ?? obj.user ?? obj.user_principal_name ?? obj.userSam ?? "unknown",
    service: obj.affected_service ?? obj.service ?? obj.module ?? obj.diagnostic ?? "diagnostic",
    status: obj.status ?? "ok",
    rule: obj.primary_rule_id ?? obj.finding_id ?? obj.rule_id ?? "none"
  };
}

export function HistoryPage({ history }: HistoryPageProps) {
  const rows = history.map(renderItem);

  return (
    <section className="trace-page">
      <div className="trace-page-header">
        <span className="trace-eyebrow">Evidence</span>
        <h1>Diagnostic run history</h1>
        <p>Review previous access-evidence diagnostic runs and report links when available.</p>
      </div>

      <section className="trace-history-card">
        {rows.length === 0 ? (
          <p className="trace-muted">No history rows were returned by the backend yet.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>User</th>
                <th>Service</th>
                <th>Status</th>
                <th>Rule</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={String(row.id)}>
                  <td>{String(row.id)}</td>
                  <td>{String(row.user)}</td>
                  <td>{String(row.service)}</td>
                  <td><span className="trace-pill success">{String(row.status)}</span></td>
                  <td>{String(row.rule)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </section>
  );
}
