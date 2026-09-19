import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import client from "../../api/client";
import Layout from "../../components/Layout";
import { Button, Card, TrustPill } from "../../components/ui";

export default function MyScorePage() {
  const [companies, setCompanies] = useState(null);
  const [recordsByCompany, setRecordsByCompany] = useState({});

  useEffect(() => {
    client.get("/companies").then(async (res) => {
      setCompanies(res.data);
      for (const company of res.data) {
        const r = await client.get(`/companies/${company.id}/financial-records`);
        setRecordsByCompany((prev) => ({ ...prev, [company.id]: r.data }));
      }
    });
  }, []);

  if (companies === null) {
    return (
      <Layout>
        <p className="text-inkmuted">Loading...</p>
      </Layout>
    );
  }

  if (companies.length === 0) {
    return (
      <Layout>
        <Card className="text-center py-12">
          <h1 className="font-display text-2xl font-semibold text-ink mb-2">No financials yet</h1>
          <p className="text-inkmuted mb-6">Add your balance sheet and P&amp;L to get your first credit score.</p>
          <Link to="/msme/upload">
            <Button>Add your financials</Button>
          </Link>
        </Card>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-display text-2xl font-semibold text-ink">My score history</h1>
        <Link to="/msme/upload">
          <Button variant="secondary">Add another year</Button>
        </Link>
      </div>

      {companies.map((company) => (
        <Card key={company.id} className="mb-4">
          <h2 className="font-medium text-ink mb-3">
            {company.name} <span className="text-sm text-inkmuted font-normal">· {company.sector}</span>
          </h2>
          <div className="space-y-2">
            {(recordsByCompany[company.id] || []).map((record) => (
              <Link
                key={record.id}
                to={`/msme/score/${record.id}`}
                className="flex items-center justify-between px-4 py-3 rounded-lg border border-border hover:border-accent/50"
              >
                <div className="flex items-center gap-3">
                  <span className="text-sm font-medium text-ink">{record.financial_year}</span>
                  <TrustPill label={record.trust_label} />
                </div>
                <span className="text-sm text-accent">View score →</span>
              </Link>
            ))}
            {(recordsByCompany[company.id] || []).length === 0 && (
              <p className="text-sm text-inkmuted">No years added yet.</p>
            )}
          </div>
        </Card>
      ))}
    </Layout>
  );
}
