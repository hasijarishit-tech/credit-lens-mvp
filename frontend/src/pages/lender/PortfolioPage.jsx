import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import client from "../../api/client";
import Layout from "../../components/Layout";
import { Button, Card, GradeBadge, TrustPill } from "../../components/ui";

const SOURCE_LABELS = {
  pdf_upload: "PDF upload",
  manual_entry: "Manual entry",
  source_link: "Source link",
  name_search: "Name search",
};

export default function PortfolioPage() {
  const navigate = useNavigate();
  const [rows, setRows] = useState(null);
  const [sortDesc, setSortDesc] = useState(true);

  useEffect(() => {
    async function load() {
      const companiesRes = await client.get("/companies");
      const built = [];
      for (const company of companiesRes.data) {
        const recordsRes = await client.get(`/companies/${company.id}/financial-records`);
        const latest = recordsRes.data[0]; // already ordered newest-first by the API
        let score = null;
        if (latest) {
          const scoreRes = await client.get(`/financial-records/${latest.id}/score`);
          score = scoreRes.data;
        }
        built.push({ company, latest, score });
      }
      setRows(built);
    }
    load();
  }, []);

  if (rows === null) {
    return (
      <Layout>
        <p className="text-inkmuted">Loading portfolio...</p>
      </Layout>
    );
  }

  const sorted = [...rows].sort((a, b) => {
    const sa = a.score?.composite_score ?? -1;
    const sb = b.score?.composite_score ?? -1;
    return sortDesc ? sb - sa : sa - sb;
  });

  return (
    <Layout>
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-display text-2xl font-semibold text-ink">Applicant portfolio</h1>
        <Link to="/lender/add">
          <Button>Add applicant</Button>
        </Link>
      </div>

      {rows.length === 0 ? (
        <Card className="text-center py-12">
          <p className="text-inkmuted mb-6">No applicants yet.</p>
          <Link to="/lender/add">
            <Button>Add your first applicant</Button>
          </Link>
        </Card>
      ) : (
        <div className="overflow-x-auto border border-border rounded-xl bg-surface">
          <table className="w-full text-sm">
            <thead className="bg-surfacealt">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-inkmuted text-xs uppercase tracking-wide">Company</th>
                <th className="text-left px-4 py-3 font-medium text-inkmuted text-xs uppercase tracking-wide">Sector</th>
                <th className="text-left px-4 py-3 font-medium text-inkmuted text-xs uppercase tracking-wide">Grade</th>
                <th
                  className="text-right px-4 py-3 font-medium text-inkmuted text-xs uppercase tracking-wide cursor-pointer select-none"
                  onClick={() => setSortDesc((s) => !s)}
                >
                  Score {sortDesc ? "↓" : "↑"}
                </th>
                <th className="text-left px-4 py-3 font-medium text-inkmuted text-xs uppercase tracking-wide">Trust</th>
                <th className="text-left px-4 py-3 font-medium text-inkmuted text-xs uppercase tracking-wide">Source</th>
                <th className="text-right px-4 py-3 font-medium text-inkmuted text-xs uppercase tracking-wide">Flags</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map(({ company, latest, score }) => (
                <tr
                  key={company.id}
                  className="border-t border-border hover:bg-surfacealt cursor-pointer"
                  onClick={() => navigate(`/lender/company/${company.id}`)}
                >
                  <td className="px-4 py-3 text-ink font-medium">{company.name}</td>
                  <td className="px-4 py-3 text-inkmuted">{company.sector}</td>
                  <td className="px-4 py-3">
                    {score ? <GradeBadge grade={score.letter_grade} /> : <span className="text-inkmuted text-xs">Not scored</span>}
                  </td>
                  <td className="px-4 py-3 text-right font-mono-tabular text-ink">
                    {score ? score.composite_score : "—"}
                  </td>
                  <td className="px-4 py-3">{latest ? <TrustPill label={latest.trust_label} /> : "—"}</td>
                  <td className="px-4 py-3 text-inkmuted">{latest ? SOURCE_LABELS[latest.source_type] : "—"}</td>
                  <td className="px-4 py-3 text-right">
                    {score && score.anomaly_flags.length > 0 ? (
                      <span className="text-warn font-medium">{score.anomaly_flags.length}</span>
                    ) : (
                      <span className="text-inkmuted">0</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Layout>
  );
}
