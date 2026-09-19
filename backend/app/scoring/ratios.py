"""Computes the four ratio buckets: liquidity, leverage, profitability,
efficiency & growth. Ratios that need data we don't have (e.g. DSCR without
two years of financials) are simply omitted rather than guessed.
"""
from typing import Any, Dict, Optional

DAYS_IN_YEAR = 365

# DSCR needs an estimate of annual debt repayment obligations, which Indian
# MSME filings rarely break out explicitly. We assume long-term debt
# amortizes evenly over 5 years as a simple, documented placeholder —
# replace with real repayment schedules if you have them.
ASSUMED_DEBT_AMORTIZATION_YEARS = 5


def _safe_div(numerator: float, denominator: float) -> Optional[float]:
    if denominator == 0:
        return None
    return numerator / denominator


def compute_ratios(
    record: Dict[str, Any], cash_flow: Optional[Dict[str, float]]
) -> Dict[str, Optional[float]]:
    bs = record["balance_sheet"]
    inc = record["income_statement"]
    prior = record.get("prior_year")

    cash = float(bs.get("cash_and_equivalents") or 0)
    receivables = float(bs.get("receivables") or 0)
    inventory = float(bs.get("inventory") or 0)
    other_current_assets = float(bs.get("other_current_assets") or 0)
    current_liabilities = float(bs.get("current_liabilities") or 0)
    payables = float(bs.get("payables") or 0)
    long_term_debt = float(bs.get("long_term_debt") or 0)
    equity = float(bs.get("equity") or 0)

    revenue = float(inc.get("revenue") or 0)
    cogs = float(inc.get("cogs") or 0)
    operating_expenses = float(inc.get("operating_expenses") or 0)
    depreciation = float(inc.get("depreciation") or 0)
    interest_expense = float(inc.get("interest_expense") or 0)
    net_income = float(inc.get("net_income") or 0)

    current_assets = cash + receivables + inventory + other_current_assets
    gross_profit = revenue - cogs
    ebit = gross_profit - operating_expenses - depreciation
    capital_employed = equity + long_term_debt

    ratios: Dict[str, Optional[float]] = {}

    # Liquidity
    ratios["current_ratio"] = _safe_div(current_assets, current_liabilities)
    ratios["quick_ratio"] = _safe_div(cash + receivables, current_liabilities)

    # Leverage
    # Debt-to-equity is undefined (not merely "low") when equity is zero or
    # negative — dividing by a negative equity figure would otherwise flip
    # the sign and make a technically-insolvent company look great. We mark
    # it unavailable here; detect_anomalies() raises a dedicated flag for
    # negative equity so the risk still surfaces clearly.
    ratios["debt_to_equity"] = _safe_div(long_term_debt, equity) if equity > 0 else None
    ratios["interest_coverage"] = _safe_div(ebit, interest_expense)

    if cash_flow is not None:
        estimated_annual_debt_repayment = long_term_debt / ASSUMED_DEBT_AMORTIZATION_YEARS
        debt_service = interest_expense + estimated_annual_debt_repayment
        ratios["dscr"] = _safe_div(cash_flow["operating_cash_flow"], debt_service)
    else:
        ratios["dscr"] = None

    # Profitability
    ratios["gross_margin"] = _safe_div(gross_profit, revenue)
    ratios["net_margin"] = _safe_div(net_income, revenue)
    # Gated on equity (not just capital_employed) being positive: when equity
    # is negative but long-term debt happens to be slightly larger in
    # magnitude, capital_employed can land just above zero and produce a
    # wildly inflated ROCE for a company that is, if anything, in worse
    # shape than a normal low-capital-employed business.
    ratios["roce"] = _safe_div(ebit, capital_employed) if equity > 0 else None

    # Efficiency & growth
    ratios["receivable_days"] = _safe_div(receivables * DAYS_IN_YEAR, revenue)
    ratios["inventory_days"] = _safe_div(inventory * DAYS_IN_YEAR, cogs)
    payable_days = _safe_div(payables * DAYS_IN_YEAR, cogs)

    if ratios["receivable_days"] is not None and ratios["inventory_days"] is not None and payable_days is not None:
        ratios["cash_conversion_cycle"] = ratios["receivable_days"] + ratios["inventory_days"] - payable_days
    else:
        ratios["cash_conversion_cycle"] = None

    if prior:
        prior_revenue = float(prior["income_statement"].get("revenue") or 0)
        ratios["revenue_yoy_growth"] = _safe_div(revenue - prior_revenue, prior_revenue)
    else:
        ratios["revenue_yoy_growth"] = None

    return ratios
