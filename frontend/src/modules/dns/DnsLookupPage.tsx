import { StandardDiagnosticResult } from "../../api/traceApi";

type DnsLookupPageProps = {
  onResult: (result: StandardDiagnosticResult) => void;
};

export function DnsLookupPage({ onResult }: DnsLookupPageProps) {
  function sample() {
    onResult({
      title: "DNS lookup",
      status: "not_run",
      summary: "DNS lookup UI shell is available. Endpoint wiring can be connected in a later diagnostic milestone.",
      evidenceUsed: [],
      evidenceMissing: ["Live DNS endpoint integration is not part of the UI shell rebuild."],
      safeNextSteps: ["Use the validated FactoryOps share-access workflow for v1 evidence."],
      doNotChangeYet: ["Do not change DNS records based on a sample screen."],
      limitations: ["Sample/readiness page."],
      readOnlyKept: true,
      raw: {}
    });
  }

  return (
    <section className="trace-page">
      <div className="trace-page-header">
        <span className="trace-eyebrow">Network</span>
        <h1>DNS lookup</h1>
        <p>Collect read-only DNS name-resolution evidence for support cases.</p>
      </div>
      <section className="trace-placeholder-card">
        <h2>Readiness page</h2>
        <p>This screen is preserved as a module placeholder. The validated v1 workflow remains FactoryOps share access.</p>
        <button className="trace-secondary-button" onClick={sample}>Show sample result</button>
      </section>
    </section>
  );
}
