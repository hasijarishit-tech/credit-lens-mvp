import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import client, { apiErrorMessage } from "../api/client";
import { useAuth } from "../context/AuthContext";
import Layout from "../components/Layout";
import { Button, Card, ErrorBanner, Field, Input, Select } from "../components/ui";
import FinancialsForm, { emptyYear } from "../components/FinancialsForm";

const SECTORS = ["Manufacturing", "Trading", "Services", "Construction", "Agriculture-adjacent"];
const METHODS = [
  { key: "manual", label: "Manual entry", desc: "Type the figures in yourself" },
  { key: "pdf", label: "PDF upload", desc: "A balance sheet + P&L PDF" },
  { key: "link", label: "Source link", desc: "Paste a public filing URL" },
  { key: "name_search", label: "Search by name", desc: "Find a public company" },
];

export default function IntakePage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const isLender = user?.role === "lender";

  const [companies, setCompanies] = useState([]);
  const [companyId, setCompanyId] = useState("");
  const [newCompanyName, setNewCompanyName] = useState("");
  const [newSector, setNewSector] = useState(SECTORS[0]);

  const [method, setMethod] = useState("manual");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const [financialYear, setFinancialYear] = useState("");
  const [current, setCurrent] = useState(emptyYear());
  const [priorYear, setPriorYear] = useState(emptyYear());
  const [includePriorYear, setIncludePriorYear] = useState(false);

  const [file, setFile] = useState(null);
  const [url, setUrl] = useState("");

  const [searchQuery, setSearchQuery] = useState("");
  const [candidates, setCandidates] = useState(null);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    client.get("/companies").then((res) => {
      setCompanies(res.data);
      if (res.data.length > 0 && !isLender) setCompanyId(res.data[0].id);
    });
  }, [isLender]);

  const isNewCompany = companyId === "";

  async function resolveCompanyId() {
    if (!isNewCompany) return companyId;
    if (!newCompanyName.trim()) throw new Error("Please enter a business name.");
    const res = await client.post("/companies", { name: newCompanyName, sector: newSector });
    return res.data.id;
  }

  function updateCurrent(section, key, value) {
    setCurrent((prev) => ({ ...prev, [section]: { ...prev[section], [key]: value } }));
  }
  function updatePrior(section, key, value) {
    setPriorYear((prev) => ({ ...prev, [section]: { ...prev[section], [key]: value } }));
  }

  function toNumbers(section) {
    return Object.fromEntries(Object.entries(section).map(([k, v]) => [k, v === "" ? 0 : Number(v)]));
  }

  async function handleManualSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const cid = await resolveCompanyId();
      const payload = {
        financial_year: financialYear || "Unknown",
        balance_sheet: toNumbers(current.balance_sheet),
        income_statement: toNumbers(current.income_statement),
        prior_year: includePriorYear
          ? { balance_sheet: toNumbers(priorYear.balance_sheet), income_statement: toNumbers(priorYear.income_statement) }
          : null,
      };
      const res = await client.post(`/companies/${cid}/financial-records/manual`, payload);
      navigate(`/review/${res.data.id}`);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function handlePdfSubmit(e) {
    e.preventDefault();
    setError("");
    if (!file) return setError("Please choose a PDF file.");
    setLoading(true);
    try {
      const cid = await resolveCompanyId();
      const form = new FormData();
      form.append("file", file);
      const res = await client.post(`/companies/${cid}/financial-records/pdf`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      navigate(`/review/${res.data.id}`);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleLinkSubmit(e) {
    e.preventDefault();
    setError("");
    if (!url.trim()) return setError("Please paste a URL.");
    setLoading(true);
    try {
      const cid = await resolveCompanyId();
      const res = await client.post(`/companies/${cid}/financial-records/link`, { url });
      navigate(`/review/${res.data.id}`);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleSearch(e) {
    e.preventDefault();
    setError("");
    setSearching(true);
    setCandidates(null);
    try {
      const res = await client.post("/name-search", { query: searchQuery });
      setCandidates(res.data.candidates);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setSearching(false);
    }
  }

  async function handleConfirmCandidate(candidate) {
    setError("");
    setLoading(true);
    try {
      const cid = await resolveCompanyId();
      const res = await client.post("/name-search/confirm", {
        company_id: cid,
        source_reference: candidate.source_reference,
      });
      navigate(`/review/${res.data.id}`);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <Layout>
      <h1 className="font-display text-2xl font-semibold text-ink mb-1">
        {isLender ? "Add an applicant" : "Add your financials"}
      </h1>
      <p className="text-inkmuted mb-8">Choose how you'd like to bring in this year's numbers.</p>

      <Card className="mb-6">
        <h2 className="font-medium text-ink mb-4">Which business is this for?</h2>
        {companies.length > 0 && (
          <Select value={companyId} onChange={(e) => setCompanyId(e.target.value)} className="mb-3">
            {companies.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.sector})
              </option>
            ))}
            <option value="">+ Add a new business</option>
          </Select>
        )}
        {isNewCompany && (
          <div className="grid grid-cols-2 gap-4">
            <Field label="Business name">
              <Input value={newCompanyName} onChange={(e) => setNewCompanyName(e.target.value)} />
            </Field>
            <Field label="Sector">
              <Select value={newSector} onChange={(e) => setNewSector(e.target.value)}>
                {SECTORS.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </Select>
            </Field>
          </div>
        )}
      </Card>

      <Card>
        <div className="grid grid-cols-4 gap-2 mb-6">
          {METHODS.map((m) => (
            <button
              key={m.key}
              onClick={() => {
                setMethod(m.key);
                setError("");
              }}
              className={`text-left rounded-xl border p-3 ${
                method === m.key ? "border-accent bg-accentsoft" : "border-border hover:border-accent/50"
              }`}
            >
              <div className="text-sm font-medium text-ink">{m.label}</div>
              <div className="text-xs text-inkmuted mt-0.5">{m.desc}</div>
            </button>
          ))}
        </div>

        {method === "manual" && (
          <form onSubmit={handleManualSubmit} className="space-y-6">
            <FinancialsForm
              financialYear={financialYear}
              onFinancialYearChange={setFinancialYear}
              current={current}
              onChangeCurrent={updateCurrent}
              priorYear={priorYear}
              onChangePrior={updatePrior}
              includePriorYear={includePriorYear}
              onToggleIncludePriorYear={setIncludePriorYear}
            />
            <ErrorBanner message={error} />
            <Button type="submit" disabled={loading}>
              {loading ? "Saving..." : "Continue to review"}
            </Button>
          </form>
        )}

        {method === "pdf" && (
          <form onSubmit={handlePdfSubmit} className="space-y-4">
            <Field label="Balance sheet + P&L PDF" hint="Native-text PDF only — scanned images aren't supported yet">
              <input
                type="file"
                accept="application/pdf"
                onChange={(e) => setFile(e.target.files[0])}
                className="block w-full text-sm text-inkmuted"
              />
            </Field>
            <ErrorBanner message={error} />
            <Button type="submit" disabled={loading}>
              {loading ? "Extracting..." : "Upload & extract"}
            </Button>
          </form>
        )}

        {method === "link" && (
          <form onSubmit={handleLinkSubmit} className="space-y-4">
            <Field label="Public filing URL" hint="BSE SME, NSE Emerge, Screener.in, or a public MCA filing link">
              <Input
                type="url"
                placeholder="https://www.screener.in/company/..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
            </Field>
            <ErrorBanner message={error} />
            <Button type="submit" disabled={loading}>
              {loading ? "Fetching..." : "Fetch & extract"}
            </Button>
          </form>
        )}

        {method === "name_search" && (
          <div className="space-y-4">
            <form onSubmit={handleSearch} className="flex gap-2">
              <Input
                placeholder="Company name"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <Button type="submit" disabled={searching}>
                {searching ? "Searching..." : "Search"}
              </Button>
            </form>
            <ErrorBanner message={error} />

            {candidates && candidates.length === 0 && (
              <div className="text-sm text-inkmuted bg-surfacealt rounded-lg p-4">
                No public match found for "{searchQuery}". Most private MSMEs don't have a public
                financial footprint — try PDF upload or manual entry instead.
              </div>
            )}

            {candidates && candidates.length > 0 && (
              <div className="space-y-2">
                <p className="text-sm text-inkmuted">Confirm which company this is before we fetch anything:</p>
                {candidates.map((c) => (
                  <div key={c.source_reference} className="flex items-center justify-between border border-border rounded-lg p-3">
                    <div>
                      <div className="text-sm font-medium text-ink">{c.name}</div>
                      <div className="text-xs text-inkmuted">
                        {c.sector} · {c.location} · {c.listing}
                      </div>
                    </div>
                    <Button variant="secondary" onClick={() => handleConfirmCandidate(c)} disabled={loading}>
                      This is the one
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </Card>
    </Layout>
  );
}
