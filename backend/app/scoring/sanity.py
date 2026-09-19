"""Pre-scoring sanity checks. Pure arithmetic, no LLM involved.

Each issue is tagged "critical" (blocks scoring until the user reviews and
confirms/corrects the numbers) or "warning" (shown to the user, but doesn't
block scoring since it may be a legitimate business situation rather than
a bad extraction).
"""
from typing import Any, Dict, List


def _num(d: Dict[str, Any], key: str) -> float:
    return float(d.get(key) or 0)


def run_sanity_checks(record: Dict[str, Any]) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    bs = record.get("balance_sheet", {})
    inc = record.get("income_statement", {})
    prior = record.get("prior_year")

    total_assets = (
        _num(bs, "cash_and_equivalents")
        + _num(bs, "receivables")
        + _num(bs, "inventory")
        + _num(bs, "other_current_assets")
        + _num(bs, "fixed_assets")
    )
    # current_liabilities is treated as the TOTAL of current liabilities
    # (payables is disclosed separately for working-capital purposes, but
    # is assumed to already be included inside current_liabilities here).
    total_liab_equity = _num(bs, "current_liabilities") + _num(bs, "long_term_debt") + _num(bs, "equity")

    if total_assets > 0 or total_liab_equity > 0:
        denom = max(total_assets, 1.0)
        mismatch_pct = abs(total_assets - total_liab_equity) / denom
        if mismatch_pct > 0.02:
            issues.append(
                {
                    "severity": "critical",
                    "field": "balance_sheet",
                    "message": (
                        f"Balance sheet doesn't tie out: total assets are "
                        f"₹{total_assets:,.0f} but total liabilities + equity are "
                        f"₹{total_liab_equity:,.0f} ({mismatch_pct*100:.1f}% mismatch). "
                        f"Please verify the balance sheet figures."
                    ),
                }
            )

    revenue = _num(inc, "revenue")
    if revenue > 0:
        receivables = _num(bs, "receivables")
        inventory = _num(bs, "inventory")
        cogs = _num(inc, "cogs")

        if receivables > 5 * revenue:
            issues.append(
                {
                    "severity": "warning",
                    "field": "balance_sheet.receivables",
                    "message": (
                        f"Receivables (₹{receivables:,.0f}) look unusually large "
                        f"relative to revenue (₹{revenue:,.0f}) — please verify this figure."
                    ),
                }
            )
        if inventory > 5 * revenue:
            issues.append(
                {
                    "severity": "warning",
                    "field": "balance_sheet.inventory",
                    "message": (
                        f"Inventory (₹{inventory:,.0f}) looks unusually large "
                        f"relative to revenue (₹{revenue:,.0f}) — please verify this figure."
                    ),
                }
            )
        if cogs > 3 * revenue:
            issues.append(
                {
                    "severity": "warning",
                    "field": "income_statement.cogs",
                    "message": (
                        f"Cost of goods sold (₹{cogs:,.0f}) is more than 3x revenue "
                        f"(₹{revenue:,.0f}) — please verify these figures."
                    ),
                }
            )

    if prior:
        net_income = _num(inc, "net_income")
        prior_bs = prior.get("balance_sheet", {})
        equity_change = _num(bs, "equity") - _num(prior_bs, "equity")
        if net_income != 0:
            drift = abs(equity_change - net_income)
            if drift > 0.5 * max(abs(net_income), 1.0):
                issues.append(
                    {
                        "severity": "warning",
                        "field": "balance_sheet.equity",
                        "message": (
                            f"Net income (₹{net_income:,.0f}) doesn't line up closely with "
                            f"the year-over-year change in equity (₹{equity_change:,.0f}). "
                            f"This can be normal (dividends, capital infusion) but may also "
                            f"signal a misread number — please verify."
                        ),
                    }
                )

    return issues


def has_critical_issues(issues: List[Dict[str, str]]) -> bool:
    return any(i["severity"] == "critical" for i in issues)
