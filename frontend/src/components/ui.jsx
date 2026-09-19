export function Button({ children, variant = "primary", className = "", ...props }) {
  const base = "inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition disabled:opacity-50 disabled:cursor-not-allowed";
  const variants = {
    primary: "bg-accent text-white hover:opacity-90",
    secondary: "bg-surfacealt text-ink border border-border hover:bg-border",
    ghost: "text-inkmuted hover:text-ink",
  };
  return (
    <button className={`${base} ${variants[variant]} ${className}`} {...props}>
      {children}
    </button>
  );
}

export function Card({ children, className = "" }) {
  return (
    <div className={`bg-surface border border-border rounded-2xl p-6 ${className}`}>
      {children}
    </div>
  );
}

export function Field({ label, children, hint }) {
  return (
    <label className="block">
      <span className="block text-sm font-medium text-ink mb-1">{label}</span>
      {children}
      {hint && <span className="block text-xs text-inkmuted mt-1">{hint}</span>}
    </label>
  );
}

export function Input(props) {
  return (
    <input
      className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-accent"
      {...props}
    />
  );
}

export function Select(props) {
  return (
    <select
      className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-accent"
      {...props}
    />
  );
}

export function ErrorBanner({ message }) {
  if (!message) return null;
  return (
    <div className="rounded-lg bg-criticalsoft border border-critical/30 text-critical text-sm px-4 py-3">
      {message}
    </div>
  );
}

const GRADE_STYLES = {
  AA: "bg-goodsoft text-good",
  A: "bg-goodsoft text-good",
  BBB: "bg-warnsoft text-warn",
  BB: "bg-criticalsoft text-critical",
  B: "bg-criticalsoft text-critical",
};

export function GradeBadge({ grade, size = "md" }) {
  const sizeClasses = size === "lg" ? "text-3xl w-20 h-20" : "text-sm w-9 h-9";
  return (
    <div
      className={`font-display font-semibold rounded-2xl flex items-center justify-center ${sizeClasses} ${GRADE_STYLES[grade] || "bg-surfacealt text-inkmuted"}`}
    >
      {grade}
    </div>
  );
}

export function TrustPill({ label }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-inkmuted">
      <span className="w-1.5 h-1.5 rounded-full bg-accent" />
      {label === "verified" ? "Verified" : "Self-reported"}
    </span>
  );
}
