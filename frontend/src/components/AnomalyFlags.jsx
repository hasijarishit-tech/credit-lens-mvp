export default function AnomalyFlags({ flags }) {
  if (!flags || flags.length === 0) {
    return <p className="text-sm text-inkmuted">No anomaly flags on this year's figures.</p>;
  }
  return (
    <div className="space-y-3">
      {flags.map((f, i) => (
        <div key={i} className="bg-criticalsoft border-l-2 border-critical rounded-lg px-4 py-3">
          <div className="text-xs font-semibold uppercase tracking-wide text-critical mb-1">
            {f.flag.replaceAll("_", " ")}
          </div>
          <div className="text-sm text-ink">{f.detail}</div>
        </div>
      ))}
    </div>
  );
}
