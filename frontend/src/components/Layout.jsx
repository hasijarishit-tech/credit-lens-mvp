import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Button } from "./ui";

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const location = useLocation();

  const navItems =
    user?.role === "lender"
      ? [
          { to: "/lender", label: "Portfolio" },
          { to: "/lender/add", label: "Add applicant" },
        ]
      : [
          { to: "/msme", label: "My score" },
          { to: "/msme/upload", label: "Add financials" },
        ];

  return (
    <div className="min-h-screen">
      <header className="border-b border-border bg-surface">
        <div className="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <span className="font-display text-lg font-semibold text-ink">CreditLens</span>
            <nav className="flex items-center gap-1">
              {navItems.map((item) => (
                <Link
                  key={item.to}
                  to={item.to}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium ${
                    location.pathname === item.to ? "bg-accentsoft text-accent" : "text-inkmuted hover:text-ink"
                  }`}
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-inkmuted">{user?.org_name}</span>
            <Button variant="ghost" onClick={logout}>
              Sign out
            </Button>
          </div>
        </div>
      </header>
      <main className="max-w-5xl mx-auto px-6 py-8">{children}</main>
    </div>
  );
}
