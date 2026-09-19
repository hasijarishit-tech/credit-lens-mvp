import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { apiErrorMessage } from "../api/client";
import { Button, Card, ErrorBanner, Field, Input } from "../components/ui";

export default function Signup() {
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [role, setRole] = useState("msme");
  const [name, setName] = useState("");
  const [orgName, setOrgName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const user = await signup({ name, org_name: orgName, email, password, role });
      navigate(user.role === "lender" ? "/lender" : "/msme");
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-10">
      <Card className="w-full max-w-sm">
        <h1 className="font-display text-2xl font-semibold text-ink mb-1">Create an account</h1>
        <p className="text-sm text-inkmuted mb-6">CreditLens — MSME credit risk scoring</p>

        <div className="grid grid-cols-2 gap-2 mb-6">
          <button
            type="button"
            onClick={() => setRole("msme")}
            className={`rounded-lg border px-3 py-2 text-sm font-medium ${role === "msme" ? "border-accent bg-accentsoft text-accent" : "border-border text-inkmuted"}`}
          >
            I'm an MSME
          </button>
          <button
            type="button"
            onClick={() => setRole("lender")}
            className={`rounded-lg border px-3 py-2 text-sm font-medium ${role === "lender" ? "border-accent bg-accentsoft text-accent" : "border-border text-inkmuted"}`}
          >
            I'm a lender
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Field label="Your name">
            <Input required value={name} onChange={(e) => setName(e.target.value)} />
          </Field>
          <Field label={role === "msme" ? "Business name" : "Institution name"}>
            <Input required value={orgName} onChange={(e) => setOrgName(e.target.value)} />
          </Field>
          <Field label="Email">
            <Input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          </Field>
          <Field label="Password" hint="At least 8 characters">
            <Input type="password" required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} />
          </Field>
          <ErrorBanner message={error} />
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Creating account..." : "Create account"}
          </Button>
        </form>
        <p className="text-sm text-inkmuted mt-6 text-center">
          Already have an account? <Link to="/login" className="text-accent font-medium">Sign in</Link>
        </p>
      </Card>
    </div>
  );
}
