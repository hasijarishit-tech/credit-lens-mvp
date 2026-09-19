import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import client, { apiErrorMessage } from "../../api/client";
import Layout from "../../components/Layout";
import { Button, Card, ErrorBanner, GradeBadge, TrustPill } from "../../components/ui";
import BucketBars from "../../components/BucketBars";
import RatioTable from "../../components/RatioTable";
import AnomalyFlags from "../../components/AnomalyFlags";

const PRESETS = [
  { key: "receivables_up_50", label: "Receivables +50%" },
  { key: "revenue_down_20", label: "Revenue -20%" },
  { key: "inventory_up_30", label: "Inventory +30%" },
  { key: "interest_expense_doubles", label: "Interest expense doubles" },
];

function formatDelta(before, after, unit) {
  if (before == null || after == null) return "—";
  if (unit === "%") return `${(before * 100).toFixed(1)}% → ${(after * 100).toFixed(1)}%`;
  if (unit === "x") return `${before.toFixed(2)}x → ${after.toFixed(2)}x`;
  return `${before} → ${after}`;
}

export default function DrilldownPage() {
  const { companyId } = useParams();
  const [company, setCompany] = useState(null);
  const [records, setRecords] = useState(null);
  const [selectedRecordId, setSelectedRecordId] = useState(null);
  const [score, setScore] = useState(null);

  const [scenarioLoading, setScenarioLoading] = useState(null);
  const [scenarioResult, setScenarioResult] = useState(null);
  const [scenarioError, setScenarioError] = useState("");

  useEffect(() => {
    client.get(`/companies/${companyId}`).then((res) => setCompany(res.data));
    client.get(`/companies/${companyId}/financial-records`).then((res) => {
      setRecords(res.data);
      if (res.data.length > 0) setSelectedRecordId(res.data[0].id);
    });
  }, [companyId]);

  useEffect(() => {
    if (!selectedRecordId) return;
    setScore(null);
    client.get(`/financial-records/${selectedRecordId}/score`).then((res) => setScore(res.data));
  }, [selectedRecordId]);

  async function runScenario(presetKey) {
    setScenarioError("");
    setScenarioLoading(presetKey);
    setScenarioResult(null);
    try {
      const res = await client.post(`/companies/${companyId}/scenario`, { preset: presetKey });
      setScenarioResult(res.data);
    } catch (err) {
      setScenarioError(apiErrorMessage(err));
    } finally {
      setScenarioLoading(null);
    }
  }

  if (!company || !records) {
    return (
      <Layout>
        <p className="text-inkmuted">Loading...</p>
      </Layout>
    );
  }

  const selectedRecord = records.find((r) => r.id === selectedRecordId);

  return (
    <Layout>
      <Link to="/lender" className="text-sm text-accent mb-4 inline-block">
        ← Back to portfolio
      </Link>

      <Card className="flex items-center justify-between flex-wrap gap-6 mb-6">
        <div>
          <h1 className="font-display text-2xl font-semibold text-ink">{company.name}</h1>
          <div className="text-sm text-inkmuted mt-1 flex items-center gap-2">
            <span>{company.sector}</span>
            {selectedRecord && (
              <>
                <span>·</span>
                <span>{selectedRecord.financial_year}</span>
                <span>·</span>
                <TrustPill label={selectedRecord.trust_label} />
              </>
            )}
          </div>
        </div>
        {score && (
          <div className="flex items-center gap-4">
            <GradeBadge grade={score.letter_grade} size="lg" />
            <div>
              <div className="text-xs text-inkmuted uppercase tracking-wide">Composite score</div>
              <div className="font-mono-tabular text-xl text-ink">{score.composite_score} / 100</div>
            </div>
          </div>
        )}
      </Card>

      {!score ? (
        <Card>
          <p className="text-inkmuted">This year hasn't been scored yet.</p>
        </Card>
      ) : (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <Card>
              <h2 className="font-medium text-ink mb-4">Ratio buckets vs. sector</h2>
              <BucketBars bucketScores={score.bucket_scores} />
            </Card>
            <Card>
              <h2 className="font-medium text-ink mb-4">Analyst note</h2>
              <p className="text-sm text-ink whitespace-pre-line leading-relaxed">{score.lender_summary_text}</p>
            </Card>
          </div>

          <Card className="mb-6">
            <h2 className="font-medium text-ink mb-4">Anomaly flags</h2>
            <AnomalyFlags flags={score.anomaly_flags} />
          </Card>

          <Card className="mb-6">
            <h2 className="font-medium text-ink mb-4">Full ratio breakdown</h2>
            <RatioTable ratios={score.ratios} />
          </Card>

          <Card>
            <h2 className="font-medium text-ink mb-1">Scenario Q&amp;A</h2>
            <p className="text-sm text-inkmuted mb-4">
              Recomputed by the real scoring engine — pick a scenario to see the actual before/after.
            </p>
            <div className="flex flex-wrap gap-2 mb-4">
              {PRESETS.map((p) => (
                <Button
                  key={p.key}
                  variant="secondary"
                  onClick={() => runScenario(p.key)}
                  disabled={scenarioLoading !== null}
                >
                  {scenarioLoading === p.key ? "Computing..." : p.label}
                </Button>
              ))}
            </div>
            <ErrorBanner message={scenarioError} />

            {scenarioResult && (
              <div className="border border-border rounded-xl p-4 mt-2">
                <p className="text-sm text-inkmuted mb-4">{scenarioResult.explanation}</p>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="border border-border rounded-lg p-3">
                    <div className="text-xs text-inkmuted uppercase mb-1">Before</div>
                    <div className="font-display text-lg font-semibold text-ink">
                      {scenarioResult.before.letter_grade} · {scenarioResult.before.composite_score}
                    </div>
                  </div>
                  <div className="border border-warn/40 rounded-lg p-3">
                    <div className="text-xs text-inkmuted uppercase mb-1">After</div>
                    <div className="font-display text-lg font-semibold text-ink">
                      {scenarioResult.after.letter_grade} · {scenarioResult.after.composite_score}
                    </div>
                  </div>
                </div>
                <div className="text-sm space-y-1">
                  <div>
                    <span className="text-inkmuted">DSCR: </span>
                    {formatDelta(scenarioResult.before.ratios?.dscr, scenarioResult.after.ratios?.dscr, "x")}
                  </div>
                  <div>
                    <span className="text-inkmuted">Current ratio: </span>
                    {formatDelta(scenarioResult.before.ratios?.current_ratio, scenarioResult.after.ratios?.current_ratio, "x")}
                  </div>
                  <div>
                    <span className="text-inkmuted">Net margin: </span>
                    {formatDelta(scenarioResult.before.ratios?.net_margin, scenarioResult.after.ratios?.net_margin, "%")}
                  </div>
                </div>
              </div>
            )}
          </Card>
        </>
      )}
    </Layout>
  );
}
