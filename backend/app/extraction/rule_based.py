"""No-API-key fallback for extraction: keyword/regex matching instead of an
LLM reading the document. Used automatically when ANTHROPIC_API_KEY isn't
configured (see app/extraction/router.py).

This is deliberately more brittle than app/llm/extraction.py — it can only
recognize label variants we've explicitly listed below, and it can't
reconcile ambiguous layouts the way a model reading for meaning can. That
tradeoff is why extraction_notes always reports a method and confidence, so
the Extraction Review screen can make it visible to the user.
"""
import re
from typing import Any, Dict, List, Optional, Tuple

NUMBER_RE = re.compile(r"-?\d[\d,]*\.?\d*")

BALANCE_SHEET_FIELDS = [
    "cash_and_equivalents",
    "receivables",
    "inventory",
    "other_current_assets",
    "fixed_assets",
    "current_liabilities",
    "payables",
    "long_term_debt",
    "equity",
]
INCOME_STATEMENT_FIELDS = [
    "revenue",
    "cogs",
    "operating_expenses",
    "depreciation",
    "interest_expense",
    "net_income",
]

# Same label variants documented in app/llm/extraction.py's system prompt,
# kept in sync manually since one is read by a model and one by regex.
LABEL_MAP: Dict[str, List[str]] = {
    "receivables": ["sundry debtors", "trade receivables", "book debts", "debtors"],
    "payables": ["sundry creditors", "trade payables", "creditors"],
    "cash_and_equivalents": [
        "cash and cash equivalents",
        "cash & cash equivalents",
        "cash and bank balances",
    ],
    "inventory": ["inventories", "stock-in-trade", "stock in trade", "closing stock"],
    "fixed_assets": [
        "property, plant and equipment",
        "property plant and equipment",
        "net block",
        "tangible assets",
        "fixed assets",
    ],
    "long_term_debt": [
        "long-term borrowings",
        "long term borrowings",
        "term loans",
        "secured loans",
    ],
    "other_current_assets": ["other current assets", "short-term loans and advances", "loans and advances"],
    "current_liabilities": ["total current liabilities", "current liabilities"],
    "revenue": ["revenue from operations", "total revenue", "net sales", "turnover"],
    "cogs": ["cost of materials consumed", "cost of goods sold", "purchases of stock-in-trade"],
    "operating_expenses": ["other expenses", "administrative expenses", "employee benefit expense"],
    "depreciation": ["depreciation and amortisation", "depreciation and amortization", "depreciation"],
    "interest_expense": ["finance costs", "interest expense", "interest and finance charges"],
    "net_income": ["profit for the year", "profit after tax", "net profit"],
}

EQUITY_LABELS = ["shareholders' funds", "shareholders funds", "net worth", "total equity"]
EQUITY_COMPONENT_LABELS = {
    "share_capital": ["share capital", "equity share capital"],
    "reserves": ["reserves and surplus", "reserves & surplus"],
}

COMPANY_NAME_RE = re.compile(r"^.{0,80}\b(private )?limited\b.{0,10}$", re.IGNORECASE | re.MULTILINE)
FINANCIAL_YEAR_RE = re.compile(r"(FY\s?20\d{2}-\d{2}|year ended,? 31st? march,? 20\d{2})", re.IGNORECASE)


def _numbers_in_line(line: str) -> List[float]:
    return [float(m.replace(",", "")) for m in NUMBER_RE.findall(line)]


def _find_label_line(lower_lines: List[str], labels: List[str]) -> Optional[int]:
    for label in labels:
        for i, line in enumerate(lower_lines):
            if label in line:
                return i
    return None


def _detect_scale(text_lower: str) -> Tuple[float, Optional[str]]:
    if "in lakhs" in text_lower:
        return 100_000.0, "Figures appear to be reported in lakhs; converted to plain rupees."
    if "in crore" in text_lower or "in crores" in text_lower:
        return 10_000_000.0, "Figures appear to be reported in crores; converted to plain rupees."
    return 1.0, None


def extract_financials_rule_based(
    text: str, source_type: str, source_reference: str
) -> Dict[str, Any]:
    lines = text.split("\n")
    lower_lines = [l.lower() for l in lines]
    text_lower = text.lower()

    current: Dict[str, float] = {}
    prior: Dict[str, float] = {}
    field_labels: Dict[str, str] = {}
    warnings: List[str] = []

    for field, labels in LABEL_MAP.items():
        idx = _find_label_line(lower_lines, labels)
        if idx is not None:
            numbers = _numbers_in_line(lines[idx])
            if numbers:
                current[field] = numbers[0]
                if len(numbers) > 1:
                    prior[field] = numbers[1]
                field_labels[field] = lines[idx].strip()[:80]

    equity_idx = _find_label_line(lower_lines, EQUITY_LABELS)
    if equity_idx is not None:
        numbers = _numbers_in_line(lines[equity_idx])
        if numbers:
            current["equity"] = numbers[0]
            if len(numbers) > 1:
                prior["equity"] = numbers[1]
            field_labels["equity"] = lines[equity_idx].strip()[:80]
    else:
        comp_current: Dict[str, float] = {}
        comp_prior: Dict[str, float] = {}
        for comp, labels in EQUITY_COMPONENT_LABELS.items():
            idx = _find_label_line(lower_lines, labels)
            if idx is not None:
                numbers = _numbers_in_line(lines[idx])
                if numbers:
                    comp_current[comp] = numbers[0]
                    if len(numbers) > 1:
                        comp_prior[comp] = numbers[1]
        if comp_current:
            current["equity"] = sum(comp_current.values())
            field_labels["equity"] = "sum of: " + " + ".join(comp_current.keys())
        if comp_prior:
            prior["equity"] = sum(comp_prior.values())

    scale, scale_warning = _detect_scale(text_lower)
    if scale_warning:
        warnings.append(scale_warning)

    all_fields = set(LABEL_MAP.keys()) | {"equity"}
    for field in all_fields:
        if field not in current:
            current[field] = 0.0
            warnings.append(f"Could not find a line matching known labels for '{field}'; defaulted to 0.")

    for d in (current, prior):
        for k in list(d.keys()):
            d[k] = d[k] * scale

    balance_sheet = {k: current[k] for k in BALANCE_SHEET_FIELDS}
    income_statement = {k: current[k] for k in INCOME_STATEMENT_FIELDS}

    prior_year = None
    prior_fields_found = sum(1 for k in all_fields if k in prior)
    if prior_fields_found >= 8:
        prior_year = {
            "balance_sheet": {k: prior.get(k, 0.0) for k in BALANCE_SHEET_FIELDS},
            "income_statement": {k: prior.get(k, 0.0) for k in INCOME_STATEMENT_FIELDS},
        }
    elif prior_fields_found > 0:
        warnings.append(
            f"Found a second column of numbers for only {prior_fields_found} of "
            f"{len(all_fields)} fields — not enough to trust as a full prior year, "
            f"so it was left out. DSCR and YoY growth will be unavailable."
        )

    company_name_match = COMPANY_NAME_RE.search(text)
    company_name = company_name_match.group(0).strip()[:120] if company_name_match else ""
    if not company_name:
        warnings.append("Could not detect a company name automatically; please fill it in.")

    year_match = FINANCIAL_YEAR_RE.search(text)
    financial_year = year_match.group(0) if year_match else ""
    if not financial_year:
        warnings.append("Could not detect the financial year automatically; please fill it in.")

    overall_confidence = "medium" if len(warnings) <= 3 else "low"

    return {
        "company_name": company_name,
        "financial_year": financial_year,
        "source_type": source_type,
        "source_reference": source_reference,
        "balance_sheet": balance_sheet,
        "income_statement": income_statement,
        "prior_year": prior_year,
        "extraction_notes": {
            "method": "rule_based_keyword_match",
            "overall_confidence": overall_confidence,
            "field_labels": field_labels,
            "warnings": warnings,
        },
    }
