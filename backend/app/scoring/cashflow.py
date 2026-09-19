"""Derives an indirect-method operating cash flow when no formal cash flow
statement is available, using two years of balance sheet + income statement
data. Most MSMEs won't have a formal cash flow statement, so this is the
backbone of the DSCR calculation.
"""
from typing import Any, Dict, Optional


def derive_operating_cash_flow(record: Dict[str, Any]) -> Optional[Dict[str, float]]:
    prior = record.get("prior_year")
    if not prior:
        return None

    bs = record["balance_sheet"]
    inc = record["income_statement"]
    prior_bs = prior["balance_sheet"]

    net_income = float(inc.get("net_income") or 0)
    depreciation = float(inc.get("depreciation") or 0)

    delta_receivables = float(bs.get("receivables") or 0) - float(prior_bs.get("receivables") or 0)
    delta_inventory = float(bs.get("inventory") or 0) - float(prior_bs.get("inventory") or 0)
    delta_payables = float(bs.get("payables") or 0) - float(prior_bs.get("payables") or 0)

    operating_cash_flow = (
        net_income
        + depreciation
        - delta_receivables
        - delta_inventory
        + delta_payables
    )

    return {
        "operating_cash_flow": operating_cash_flow,
        "net_income": net_income,
        "depreciation": depreciation,
        "delta_receivables": delta_receivables,
        "delta_inventory": delta_inventory,
        "delta_payables": delta_payables,
    }
