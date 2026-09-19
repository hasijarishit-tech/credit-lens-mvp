import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import client from "../../api/client";
import Layout from "../../components/Layout";
import { Card, GradeBadge, TrustPill } from "../../components/ui";
import BucketBars from "../../components/BucketBars";
import RatioTable from "../../components/RatioTable";
import AnomalyFlags from "../../components/AnomalyFlags";

export default function ScoreResultPage() {
  const { recordId } = useParams();
  const [record, setRecord] = useState(null);
  const [company, setCompany] = useState(null);
  const [score, setScore] = useState(null);

  useEffect(() => {
    client.get(`/financial-records/${recordId}`).then((res) => {
      setRecord(res.data);
      client.get(`/companies/${res.data.company_id}`).then((c) => setCompany(c.data));
    });
    client.post(`/financial-records/${recordId}/score`).then((res) => {
      setScore(res.data.score);
    });
  }, [recordId]);

  if (!record || !score || !company) {
    return (
      <Layout>
        <p className="text-inkmuted">Loading your score...</p>
      </Layout>
    );
  }

  return (
    <Layout>
      <Card className="flex items-center justify-between flex-wrap gap-6 mb-8">
        <div>
          <h1 className="font-display text-2xl font-semibold text-ink">{company.name}</h1>
          <div className="text-sm text-inkmuted mt-1 flex items-center gap-2">
            <span>{company.sector}</span>
            <span>·</span>
            <span>{record.financial_year}</span>
            <span>·</span>
            <TrustPill label={record.trust_label} />
          </div>
        </div>
        <div className="flex items-center gap-4">
          <GradeBadge grade={score.letter_grade} size="lg" />
          <div>
            <div className="text-xs text-inkmuted uppercase tracking-wide">Composite score</div>
            <div className="font-mono-tabular text-xl text-ink">{score.composite_score} / 100</div>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <Card>
          <h2 className="font-medium text-ink mb-4">How you compare to your sector</h2>
          <BucketBars bucketScores={score.bucket_scores} />
        </Card>
        <Card>
          <h2 className="font-medium text-ink mb-4">What to fix first</h2>
          <p className="text-sm text-ink whitespace-pre-line leading-relaxed">{score.narrative_text}</p>
        </Card>
      </div>

      <Card className="mb-8">
        <h2 className="font-medium text-ink mb-4">Anomaly flags</h2>
        <AnomalyFlags flags={score.anomaly_flags} />
      </Card>

      <Card>
        <h2 className="font-medium text-ink mb-4">Every ratio behind your grade</h2>
        <RatioTable ratios={score.ratios} />
      </Card>
    </Layout>
  );
}
