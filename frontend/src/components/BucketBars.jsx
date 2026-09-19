const BUCKET_LABELS = {
  liquidity: "Liquidity",
  leverage: "Leverage",
  profitability: "Profitability",
  efficiency_growth: "Efficiency & growth",
};

function barColor(score) {
  if (score >= 65) return "bg-good";
  if (score >= 40) return "bg-warn";
  return "bg-critical";
}

export default function BucketBars({ bucketScores }) {
  return (
    <div className="space-y-4">
      {Object.entries(BUCKET_LABELS).map(([key, label]) => {
        const score = bucketScores[key];
        return (
          <div key={key} className="grid grid-cols-[140px_1fr_48px] items-center gap-4">
            <div className="text-sm font-medium text-ink">{label}</div>
            <div className="relative h-2.5 bg-surfacealt rounded-full">
              <div className="absolute top-1/2 -translate-y-1/2 w-px h-4 bg-inkmuted/40" style={{ left: "50%" }} />
              {score != null && (
                <div
                  className={`absolute top-0 left-0 h-full rounded-full ${barColor(score)}`}
                  style={{ width: `${Math.max(score, 2)}%` }}
                />
              )}
            </div>
            <div className="text-right text-sm font-mono-tabular text-ink">
              {score != null ? score.toFixed(1) : "—"}
            </div>
          </div>
        );
      })}
      <p className="text-xs text-inkmuted">0–100, where 50 = right at your sector's benchmark median.</p>
    </div>
  );
}
