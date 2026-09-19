const RATIO_META = {
  current_ratio: ["Current ratio", "liquidity", "x"],
  quick_ratio: ["Quick ratio", "liquidity", "x"],
  debt_to_equity: ["Debt-to-equity", "leverage", "x"],
  interest_coverage: ["Interest coverage", "leverage", "x"],
  dscr: ["DSCR (est.)", "leverage", "x"],
  gross_margin: ["Gross margin", "profitability", "%"],
  net_margin: ["Net margin", "profitability", "%"],
  roce: ["ROCE", "profitability", "%"],
  receivable_days: ["Receivable days", "efficiency", "days"],
  inventory_days: ["Inventory days", "efficiency", "days"],
  cash_conversion_cycle: ["Cash conversion cycle", "efficiency", "days"],
  revenue_yoy_growth: ["Revenue growth YoY", "efficiency", "%"],
};

function format(value, unit) {
  if (value == null) return "—";
  if (unit === "%") return `${(value * 100).toFixed(1)}%`;
  if (unit === "x") return `${value.toFixed(2)}x`;
  return `${Math.round(value)}`;
}

export default function RatioTable({ ratios }) {
  return (
    <div className="overflow-x-auto border border-border rounded-xl">
      <table className="w-full text-sm">
        <thead className="bg-surfacealt">
          <tr>
            <th className="text-left px-4 py-2.5 font-medium text-inkmuted text-xs uppercase tracking-wide">Ratio</th>
            <th className="text-right px-4 py-2.5 font-medium text-inkmuted text-xs uppercase tracking-wide">Value</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(RATIO_META).map(([key, [label, bucket, unit]]) => (
            <tr key={key} className="border-t border-border">
              <td className="px-4 py-2.5 text-ink">
                {label} <span className="text-xs text-inkmuted">· {bucket}</span>
              </td>
              <td className="px-4 py-2.5 text-right font-mono-tabular text-ink">{format(ratios[key], unit)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
