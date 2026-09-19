import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import client, { apiErrorMessage } from "../api/client";
import { useAuth } from "../context/AuthContext";
import Layout from "../components/Layout";
import { Button, Card, ErrorBanner } from "../components/ui";
import FinancialsForm from "../components/FinancialsForm";

const SOURCE_LABELS = {
  pdf_upload: "PDF upload",
  manual_entry: "Manual entry",
  source_link: "Source link",
  name_search: "Company name search",
};

const CONFIDENCE_STYLES = {
  high: "bg-goodsoft text-good",
  medium: "bg-warnsoft text-warn",
  low: "bg-criticalsoft text-critical",
};

function toStrings(section) {
  return Object.fromEntries(Object.entries(section || {}).map(([k, v]) => [k, String(v ?? "")]));
}

export default function ReviewPage() {
  const { recordId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [record, setRecord] = useState(null);
  const [financialYear, setFinancialYear] = useState("");
  const [current, setCurrent] = useState(null);
  const [priorYear, setPriorYear] = useState(null);
  const [includePriorYear, setIncludePriorYear] = useState(false);
  const [error, setError] = useState("");
  const [issues, setIssues] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    client.get(`/financial-records/${recordId}`).then((res) => {
      const r = res.data;
      setRecord(r);
      setFinancialYear(r.financial_year || "");
      setCurrent({
        balance_sheet: toStrings(r.extracted_data.balance_sheet),
        income_statement: toStrings(r.extracted_data.income_statement),
      });
      if (r.extracted_data.prior_year) {
        setIncludePriorYear(true);
        setPriorYear({
          balance_sheet: toStrings(r.extracted_data.prior_year.balance_sheet),
          income_statement: toStrings(r.extracted_data.prior_year.income_statement),
        });
      } else {
        setPriorYear({
          balance_sheet: toStrings({}),
          income_statement: toStrings({}),
        });
      }
    });
  }, [recordId]);

  function updateCurrent(section, key, value) {
    setCurrent((prev) => ({ ...prev, [section]: { ...prev[section], [key]: value } }));
  }
  function updatePrior(section, key, value) {
    setPriorYear((prev) => ({ ...prev, [section]: { ...prev[section], [key]: value } }));
  }

  function toNumbers(section) {
    return Object.fromEntries(Object.entries(section).map(([k, v]) => [k, v === "" ? 0 : Number(v)]));
  }

  async function handleConfirmAndScore() {
    setError("");
    setIssues([]);
    setLoading(true);
    try {
      await client.patch(`/financial-records/${recordId}`, {
        financial_year: financialYear,
        balance_sheet: toNumbers(current.balance_sheet),
        income_statement: toNumbers(current.income_statement),
        prior_year: includePriorYear
          ? { balance_sheet: toNumbers(priorYear.balance_sheet), income_statement: toNumbers(priorYear.income_statement) }
          : null,
      });

      const scoreRes = await client.post(`/financial-records/${recordId}/score`);
      if (scoreRes.data.status === "needs_review") {
        setIssues(scoreRes.data.issues);
        return;
      }

      if (user.role === "lender") {
        navigate(`/lender/company/${record.company_id}`);
      } else {
        navigate(`/msme/score/${recordId}`);
      }
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  if (!record || !current) {
    return (
      <Layout>
        <p className="text-inkmuted">Loading...</p>
      </Layout>
    );
  }

  const confidence = record.extraction_confidence;

  return (
    <Layout>
      <h1 className="font-display text-2xl font-semibold text-ink mb-1">Review extracted figures</h1>
      <p className="text-inkmuted mb-6">
        Source: {SOURCE_LABELS[record.source_type]}
        {record.source_reference && ` — ${record.source_reference}`}
      </p>

      {confidence && (
        <Card className="mb-6">
          <div className="flex items-center gap-3 mb-3">
            <span className={`text-xs font-medium px-2 py-1 rounded-full ${CONFIDENCE_STYLES[confidence.overall_confidence] || ""}`}>
              {confidence.overall_confidence} confidence
            </span>
            <span className="text-xs text-inkmuted">extraction method: {confidence.method}</span>
          </div>
          {confidence.warnings?.length > 0 && (
            <ul className="space-y-1.5">
              {confidence.warnings.map((w, i) => (
                <li key={i} className="text-sm text-warn flex gap-2">
                  <span>&bull;</span>
                  <span>{w}</span>
                </li>
              ))}
            </ul>
          )}
        </Card>
      )}

      {issues.length > 0 && (
        <Card className="mb-6 border-critical/40">
          <h3 className="font-medium text-critical mb-2">Please check these before scoring</h3>
          <ul className="space-y-1.5">
            {issues.map((issue, i) => (
              <li key={i} className={`text-sm ${issue.severity === "critical" ? "text-critical" : "text-warn"}`}>
                {issue.message}
              </li>
            ))}
          </ul>
        </Card>
      )}

      <Card>
        <FinancialsForm
          financialYear={financialYear}
          onFinancialYearChange={setFinancialYear}
          current={current}
          onChangeCurrent={updateCurrent}
          priorYear={priorYear}
          onChangePrior={updatePrior}
          includePriorYear={includePriorYear}
          onToggleIncludePriorYear={setIncludePriorYear}
          fieldLabels={confidence?.field_labels}
        />
        <ErrorBanner message={error} />
        <div className="mt-6">
          <Button onClick={handleConfirmAndScore} disabled={loading}>
            {loading ? "Scoring..." : "Confirm & see score"}
          </Button>
        </div>
      </Card>
    </Layout>
  );
}
