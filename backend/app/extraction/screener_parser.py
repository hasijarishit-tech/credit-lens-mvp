"""Screener.in-specific fallback parser, used when no API key is configured.

Screener's public company page reports aggregated line items ("Sales",
"Expenses", "Borrowings", "Other Liabilities", "Other Assets") rather than
the granular labels (receivables, payables, COGS vs. opex) our schema
wants — the generic rule_based.py keyword matcher finds nothing on these
pages at all, because Screener simply doesn't use words like "sundry
debtors" anywhere on the page.

This parser reconstructs the schema the same way a human analyst would
when working from Screener's summary: COGS and operating expenses can't be
separated, so the whole "Expenses" line is treated as cogs; receivables /
inventory are backed out from Screener's own reported Debtor Days /
Inventory Days ratios applied to revenue/COGS; payables are estimated as a
share of the "Other Liabilities" aggregate. Every estimate is recorded in
extraction_notes so it's visible on the Extraction Review screen.

Layout note: once stripped to plain text, each label and each number sits
on its own line (not space-separated), and recently-listed SME companies
often have an extra interim/stub column (e.g. "Feb 2026" an 11-month
period) inserted before the latest full fiscal year. Since Indian fiscal
years always end in March, only "Mar YYYY" columns are treated as real
annual figures — any other month is an interim column and is skipped
positionally rather than mistaken for a prior year.
"""
import re
from typing import Any, Dict, List, Optional, Tuple

MONTH_YEAR_RE = re.compile(
    r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{4}$"
)
NUMBER_LINE_RE = re.compile(r"^-?\d[\d,]*\.?\d*$")
DAYS_IN_YEAR = 365
CR_TO_RUPEES = 10_000_000.0


def is_screener_url(source_reference: str) -> bool:
    return "screener.in" in (source_reference or "").lower()


def _section_lines(all_lines: List[str], start_heading: str, end_headings: List[str]) -> List[str]:
    # The section heading text also appears earlier as a nav-menu link
    # (e.g. "Profit & Loss" is both a sidebar link and the real heading) —
    # the real content heading is the one immediately followed by
    # "Figures in Rs. Crores", so match on that pair, not just the text.
    start = None
    for i, l in enumerate(all_lines):
        if l.strip() == start_heading and i + 1 < len(all_lines) and "Figures in Rs" in all_lines[i + 1]:
            start = i + 1
            break
    if start is None:
        return []
    end = len(all_lines)
    for heading in end_headings:
        for i in range(start, len(all_lines)):
            if all_lines[i].strip() == heading:
                end = min(end, i)
                break
    return all_lines[start:end]


def _header_tokens(section_lines: List[str], first_row_labels: List[str]) -> List[str]:
    first_idx = next(
        (i for i, l in enumerate(section_lines) if l.strip() in first_row_labels), None
    )
    if first_idx is None:
        return []
    return [l.strip() for l in section_lines[:first_idx] if MONTH_YEAR_RE.match(l.strip())]


def _row_values(section_lines: List[str], labels: List[str]) -> Optional[List[float]]:
    for i, line in enumerate(section_lines):
        if line.strip() in labels:
            j = i + 1
            if j < len(section_lines) and section_lines[j].strip() == "+":
                j += 1
            values: List[float] = []
            while j < len(section_lines) and NUMBER_LINE_RE.match(section_lines[j].strip()):
                values.append(float(section_lines[j].strip().replace(",", "")))
                j += 1
            return values
    return None


def _mar_only_last_two(
    header_tokens: List[str], values: Optional[List[float]]
) -> Tuple[Optional[float], Optional[float]]:
    """Picks the last two genuine fiscal-year-end (March) columns, skipping
    any interim/stub column positionally rather than treating it as a
    prior year."""
    if not values:
        return None, None
    if len(header_tokens) != len(values):
        # Header/value count mismatch (unexpected layout) — fall back to
        # naive last-two rather than guessing further.
        if len(values) >= 2:
            return values[-2], values[-1]
        return None, values[-1]

    mar_values = [v for tok, v in zip(header_tokens, values) if tok.startswith("Mar ")]
    if len(mar_values) >= 2:
        return mar_values[-2], mar_values[-1]
    if len(mar_values) == 1:
        return None, mar_values[-1]
    return None, None


PL_FIRST_ROW = ["Sales", "Revenue"]
BS_FIRST_ROW = ["Equity Capital"]
RATIOS_FIRST_ROW = ["Debtor Days"]


def extract_financials_screener(text: str, source_reference: str) -> Dict[str, Any]:
    all_lines = text.split("\n")

    pl_lines = _section_lines(all_lines, "Profit & Loss", ["Balance Sheet"])
    bs_lines = _section_lines(all_lines, "Balance Sheet", ["Cash Flows"])
    ratios_lines = _section_lines(all_lines, "Ratios", ["Insights", "Shareholding Pattern", "Documents"])

    pl_headers = _header_tokens(pl_lines, PL_FIRST_ROW)
    bs_headers = _header_tokens(bs_lines, BS_FIRST_ROW)
    ratios_headers = _header_tokens(ratios_lines, RATIOS_FIRST_ROW)

    mar_headers = [h for h in pl_headers if h.startswith("Mar ")]
    financial_year = ""
    if mar_headers:
        end_year = int(mar_headers[-1].split()[1])
        financial_year = f"FY{end_year - 1}-{str(end_year)[2:]}"

    sales_prior, sales_current = _mar_only_last_two(pl_headers, _row_values(pl_lines, PL_FIRST_ROW))
    expenses_prior, expenses_current = _mar_only_last_two(pl_headers, _row_values(pl_lines, ["Expenses"]))
    interest_prior, interest_current = _mar_only_last_two(pl_headers, _row_values(pl_lines, ["Interest"]))
    depreciation_prior, depreciation_current = _mar_only_last_two(pl_headers, _row_values(pl_lines, ["Depreciation"]))
    net_profit_prior, net_profit_current = _mar_only_last_two(pl_headers, _row_values(pl_lines, ["Net Profit"]))

    equity_capital_prior, equity_capital_current = _mar_only_last_two(bs_headers, _row_values(bs_lines, BS_FIRST_ROW))
    reserves_prior, reserves_current = _mar_only_last_two(bs_headers, _row_values(bs_lines, ["Reserves"]))
    borrowings_prior, borrowings_current = _mar_only_last_two(bs_headers, _row_values(bs_lines, ["Borrowings"]))
    other_liabilities_prior, other_liabilities_current = _mar_only_last_two(
        bs_headers, _row_values(bs_lines, ["Other Liabilities"])
    )
    fixed_assets_prior, fixed_assets_current = _mar_only_last_two(bs_headers, _row_values(bs_lines, ["Fixed Assets"]))
    cwip_prior, cwip_current = _mar_only_last_two(bs_headers, _row_values(bs_lines, ["CWIP"]))
    other_assets_prior, other_assets_current = _mar_only_last_two(bs_headers, _row_values(bs_lines, ["Other Assets"]))

    debtor_days_prior, debtor_days_current = _mar_only_last_two(ratios_headers, _row_values(ratios_lines, RATIOS_FIRST_ROW))
    inventory_days_prior, inventory_days_current = _mar_only_last_two(
        ratios_headers, _row_values(ratios_lines, ["Inventory Days"])
    )

    if sales_current is None or expenses_current is None:
        return {
            "balance_sheet": {k: 0.0 for k in [
                "cash_and_equivalents", "receivables", "inventory", "other_current_assets",
                "fixed_assets", "current_liabilities", "payables", "long_term_debt", "equity",
            ]},
            "income_statement": {k: 0.0 for k in [
                "revenue", "cogs", "operating_expenses", "depreciation", "interest_expense", "net_income",
            ]},
            "prior_year": None,
            "extraction_notes": {
                "method": "screener_parser",
                "overall_confidence": "low",
                "field_labels": {},
                "warnings": ["Could not locate a Sales/Expenses row on this Screener page — its layout may differ from what this parser expects."],
            },
        }

    def build_year(sales_v, expenses_v, interest_v, dep_v, net_profit_v, equity_cap_v, reserves_v,
                   borrowings_v, other_liab_v, fixed_v, cwip_v, other_assets_v, debtor_days_v, inventory_days_v):
        revenue = (sales_v or 0) * CR_TO_RUPEES
        cogs = (expenses_v or 0) * CR_TO_RUPEES
        equity = ((equity_cap_v or 0) + (reserves_v or 0)) * CR_TO_RUPEES
        long_term_debt = (borrowings_v or 0) * CR_TO_RUPEES
        current_liabilities = (other_liab_v or 0) * CR_TO_RUPEES
        fixed_assets_total = ((fixed_v or 0) + (cwip_v or 0)) * CR_TO_RUPEES
        other_assets_bucket = (other_assets_v or 0) * CR_TO_RUPEES

        # Allocate the "Other Assets" aggregate PROPORTIONALLY by the
        # relative size of Debtor Days / Inventory Days, rather than
        # computing each as an absolute day-count figure — an absolute
        # calculation can imply receivables + inventory that exceed the
        # actual "Other Assets" total (this happens for real companies:
        # Screener's own day-ratios use a COGS base we don't have access
        # to, which can differ from our full-"Expenses" stand-in). Scaling
        # proportionally guarantees the components always sum exactly to
        # the real reported total, at the cost of the split being relative
        # rather than an independently-verified absolute figure.
        weight_receivables = debtor_days_v or 0.0
        weight_inventory = inventory_days_v or 0.0
        total_weight = weight_receivables + weight_inventory

        if total_weight > 0:
            allocated = other_assets_bucket * 0.9
            receivables = allocated * weight_receivables / total_weight
            inventory = allocated * weight_inventory / total_weight
            remainder = other_assets_bucket * 0.1
        else:
            receivables = 0.0
            inventory = 0.0
            remainder = other_assets_bucket

        cash = remainder * 0.5
        other_current_assets = remainder * 0.5
        payables = current_liabilities * 0.7

        return {
            "balance_sheet": {
                "cash_and_equivalents": round(cash),
                "receivables": round(receivables),
                "inventory": round(inventory),
                "other_current_assets": round(other_current_assets),
                "fixed_assets": round(fixed_assets_total),
                "current_liabilities": round(current_liabilities),
                "payables": round(payables),
                "long_term_debt": round(long_term_debt),
                "equity": round(equity),
            },
            "income_statement": {
                "revenue": round(revenue),
                "cogs": round(cogs),
                "operating_expenses": 0.0,
                "depreciation": round((dep_v or 0) * CR_TO_RUPEES),
                "interest_expense": round((interest_v or 0) * CR_TO_RUPEES),
                "net_income": round((net_profit_v or 0) * CR_TO_RUPEES),
            },
        }

    current_year = build_year(
        sales_current, expenses_current, interest_current, depreciation_current, net_profit_current,
        equity_capital_current, reserves_current, borrowings_current, other_liabilities_current,
        fixed_assets_current, cwip_current, other_assets_current, debtor_days_current, inventory_days_current,
    )

    prior_year = None
    if sales_prior is not None and expenses_prior is not None:
        prior_year = build_year(
            sales_prior, expenses_prior, interest_prior, depreciation_prior, net_profit_prior,
            equity_capital_prior, reserves_prior, borrowings_prior, other_liabilities_prior,
            fixed_assets_prior, cwip_prior, other_assets_prior, debtor_days_prior, inventory_days_prior,
        )

    warnings = [
        "Extracted using the Screener.in-specific parser: Screener reports aggregated "
        "line items, so several fields below are reconstructed rather than read "
        "directly — see the notes below for exactly how.",
        "Full 'Expenses' line assigned entirely to cogs (operating_expenses set to 0) "
        "since Screener doesn't separate COGS from operating expenses. This keeps "
        "EBIT-based ratios accurate, but means gross_margin here effectively equals "
        "operating margin, not a true gross margin.",
        "Receivables and inventory are estimated by splitting the aggregated 'Other "
        "Assets' balance-sheet line proportionally to Screener's own Debtor Days / "
        "Inventory Days ratios (not read as direct line items) — the split reflects "
        "their relative size correctly, but each is not an independently-verified "
        "absolute figure. Cash vs. other-current-assets within the remainder is a "
        "50/50 estimate.",
        "Payables estimated as 70% of the 'Other Liabilities' aggregate.",
    ]
    if prior_year is None:
        warnings.append("Only one fiscal year (Mar-ending) of figures was found — DSCR and YoY growth will be unavailable.")

    return {
        "financial_year": financial_year,
        "balance_sheet": current_year["balance_sheet"],
        "income_statement": current_year["income_statement"],
        "prior_year": prior_year,
        "extraction_notes": {
            "method": "screener_parser",
            "overall_confidence": "medium",
            "field_labels": {
                "revenue": "Sales",
                "cogs": "Expenses (combined, see warnings)",
                "equity": "Equity Capital + Reserves",
                "long_term_debt": "Borrowings",
                "current_liabilities": "Other Liabilities",
            },
            "warnings": warnings,
        },
    }
