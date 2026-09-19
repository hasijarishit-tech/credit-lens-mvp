"""Anomaly detection computed directly from the numbers (not LLM sentiment).
Every flag names the specific figures that triggered it.
"""
from typing import Any, Dict, List, Optional


def detect_anomalies(
    record: Dict[str, Any], cash_flow: Optional[Dict[str, float]]
) -> List[Dict[str, str]]:
    flags: List[Dict[str, str]] = []
    inc = record["income_statement"]
    bs = record["balance_sheet"]
    prior = record.get("prior_year")

    net_income = float(inc.get("net_income") or 0)

    if cash_flow is not None and net_income > 0 and cash_flow["operating_cash_flow"] < 0:
        flags.append(
            {
                "flag": "profit_without_cash",
                "detail": (
                    f"Net income is positive (₹{net_income:,.0f}) but estimated operating "
                    f"cash flow is negative (₹{cash_flow['operating_cash_flow']:,.0f}). "
                    f"Profit is being reported but cash isn't actually coming in — often "
                    f"a sign of working-capital strain."
                ),
            }
        )

    if not prior:
        return flags

    prior_inc = prior["income_statement"]
    prior_bs = prior["balance_sheet"]

    revenue = float(inc.get("revenue") or 0)
    prior_revenue = float(prior_inc.get("revenue") or 0)
    revenue_growth = (revenue - prior_revenue) / prior_revenue if prior_revenue else None

    receivables = float(bs.get("receivables") or 0)
    prior_receivables = float(prior_bs.get("receivables") or 0)
    receivables_growth = (
        (receivables - prior_receivables) / prior_receivables if prior_receivables else None
    )

    if revenue_growth is not None and receivables_growth is not None:
        if receivables_growth > 0 and receivables_growth > revenue_growth + 0.10:
            flags.append(
                {
                    "flag": "receivables_outpacing_revenue",
                    "detail": (
                        f"Receivables grew {receivables_growth*100:.0f}% year-over-year while "
                        f"revenue grew {revenue_growth*100:.0f}%. Customers may be taking "
                        f"longer to pay, which strains cash flow even as sales look healthy."
                    ),
                }
            )

    inventory = float(bs.get("inventory") or 0)
    prior_inventory = float(prior_bs.get("inventory") or 0)
    inventory_growth = (inventory - prior_inventory) / prior_inventory if prior_inventory else None

    if inventory_growth is not None and revenue_growth is not None:
        if inventory_growth > 0.05 and revenue_growth <= 0.02:
            flags.append(
                {
                    "flag": "inventory_building_without_sales",
                    "detail": (
                        f"Inventory grew {inventory_growth*100:.0f}% year-over-year while "
                        f"revenue changed only {revenue_growth*100:.0f}%. Stock may be piling "
                        f"up faster than it's being sold."
                    ),
                }
            )

    long_term_debt = float(bs.get("long_term_debt") or 0)
    prior_long_term_debt = float(prior_bs.get("long_term_debt") or 0)
    debt_growth = (
        (long_term_debt - prior_long_term_debt) / prior_long_term_debt if prior_long_term_debt else None
    )

    prior_net_income = float(prior_inc.get("net_income") or 0)
    profit_growth = (net_income - prior_net_income) / abs(prior_net_income) if prior_net_income else None

    if debt_growth is not None and debt_growth > 0:
        if profit_growth is None or debt_growth > profit_growth + 0.10:
            profit_growth_str = f"{profit_growth*100:.0f}%" if profit_growth is not None else "flat/unavailable"
            flags.append(
                {
                    "flag": "debt_outpacing_profit",
                    "detail": (
                        f"Long-term debt grew {debt_growth*100:.0f}% year-over-year while net "
                        f"income growth was {profit_growth_str}. Borrowing is expanding faster "
                        f"than the profit available to service it."
                    ),
                }
            )

    return flags
