"""Uses Claude to read raw text (from a PDF, a fetched web page, or a
manual-entry passthrough) and extract it into the structured financial
schema the scoring engine expects — normalizing Indian label variance
("sundry debtors" / "trade receivables" / "book debts" -> receivables)
along the way, with a traceable confidence + original-label record.

This module is intentionally the ONLY place that talks to an LLM for
extraction. The ratio math in app/scoring/ never imports this file.
"""
from typing import Any, Dict

from app.llm.client import get_client
from app.config import settings

FINANCIAL_YEAR_SHAPE = {
    "type": "object",
    "properties": {
        "cash_and_equivalents": {"type": "number"},
        "receivables": {"type": "number"},
        "inventory": {"type": "number"},
        "other_current_assets": {"type": "number"},
        "fixed_assets": {"type": "number"},
        "current_liabilities": {"type": "number"},
        "payables": {"type": "number"},
        "long_term_debt": {"type": "number"},
        "equity": {"type": "number"},
        "revenue": {"type": "number"},
        "cogs": {"type": "number"},
        "operating_expenses": {"type": "number"},
        "depreciation": {"type": "number"},
        "interest_expense": {"type": "number"},
        "net_income": {"type": "number"},
    },
}

EXTRACTION_TOOL = {
    "name": "record_financials",
    "description": (
        "Records one company's extracted balance sheet and income statement "
        "figures, normalized to a fixed internal field naming, plus a second "
        "year if the document contains one, plus extraction confidence notes."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "company_name": {"type": "string"},
            "financial_year": {
                "type": "string",
                "description": "e.g. 'FY2024-25' for the MOST RECENT year found",
            },
            "balance_sheet": {
                "type": "object",
                "properties": {
                    k: v
                    for k, v in FINANCIAL_YEAR_SHAPE["properties"].items()
                    if k
                    in (
                        "cash_and_equivalents",
                        "receivables",
                        "inventory",
                        "other_current_assets",
                        "fixed_assets",
                        "current_liabilities",
                        "payables",
                        "long_term_debt",
                        "equity",
                    )
                },
                "required": [
                    "cash_and_equivalents",
                    "receivables",
                    "inventory",
                    "other_current_assets",
                    "fixed_assets",
                    "current_liabilities",
                    "payables",
                    "long_term_debt",
                    "equity",
                ],
            },
            "income_statement": {
                "type": "object",
                "properties": {
                    k: v
                    for k, v in FINANCIAL_YEAR_SHAPE["properties"].items()
                    if k
                    in (
                        "revenue",
                        "cogs",
                        "operating_expenses",
                        "depreciation",
                        "interest_expense",
                        "net_income",
                    )
                },
                "required": [
                    "revenue",
                    "cogs",
                    "operating_expenses",
                    "depreciation",
                    "interest_expense",
                    "net_income",
                ],
            },
            "prior_year": {
                "type": ["object", "null"],
                "description": "Same shape as the current year, only if a second year is present in the document. Otherwise null.",
                "properties": {
                    "balance_sheet": {"type": "object"},
                    "income_statement": {"type": "object"},
                },
            },
            "extraction_notes": {
                "type": "object",
                "properties": {
                    "overall_confidence": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                    },
                    "field_labels": {
                        "type": "object",
                        "description": (
                            "Map of internal field name -> the exact original label text "
                            "found in the source document/page for that figure, e.g. "
                            "{'receivables': 'Sundry Debtors'}. Only include fields you "
                            "actually found labeled; omit fields you had to default to 0."
                        ),
                    },
                    "warnings": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Anything a human reviewer should double check, e.g. "
                            "'Depreciation not found separately, defaulted to 0' or "
                            "'Figures appear to be in lakhs, converted to rupees'."
                        ),
                    },
                },
                "required": ["overall_confidence", "field_labels", "warnings"],
            },
        },
        "required": [
            "company_name",
            "financial_year",
            "balance_sheet",
            "income_statement",
            "prior_year",
            "extraction_notes",
        ],
    },
}

SYSTEM_PROMPT = """You extract financial data from Indian MSME balance sheets and \
income statements (P&L) for a credit-scoring tool. Sources vary: native-text \
PDF dumps, scraped public web pages (BSE SME/NSE Emerge/Screener.in/MCA), or \
manually typed notes.

Indian filings use inconsistent labels for the same concept. Normalize using \
this mapping (non-exhaustive — use judgement for variants not listed):
- receivables: "sundry debtors", "trade receivables", "book debts", "debtors"
- payables: "sundry creditors", "trade payables", "creditors"
- cash_and_equivalents: "cash and bank balances", "cash & cash equivalents"
- inventory: "stock-in-trade", "stock", "inventories"
- fixed_assets: "property, plant and equipment", "net block", "tangible assets"
- long_term_debt: "term loans", "long-term borrowings", "secured loans"
- equity: "shareholders' funds", "net worth", "capital + reserves and surplus"
- cogs: "cost of materials consumed", "cost of goods sold", "purchases"
- operating_expenses: "other expenses", "administrative expenses", "SG&A" \
  (exclude depreciation and interest, which have their own fields)

Figures are sometimes reported in lakhs or crores rather than plain rupees — \
convert everything to plain rupees (1 lakh = 100,000; 1 crore = 10,000,000) \
and note the conversion in extraction_notes.warnings if you did this.

If a figure genuinely cannot be found, default it to 0 and do NOT list it in \
field_labels, but DO add a note in warnings so a human knows it was defaulted \
rather than actually zero.

Only extract a prior_year if the document actually contains a second year of \
figures — never fabricate one. Call record_financials exactly once with your \
best extraction."""


def extract_financials(
    text: str, source_type: str, source_reference: str, sector_hint: str = ""
) -> Dict[str, Any]:
    """Runs the extraction. Returns the structured record (matching the
    project's schema) with an `extraction_notes` block attached.

    Raises ClaudeNotConfigured if no API key is set (see app.llm.client).
    """
    client = get_client()

    user_content = (
        f"Source type: {source_type}\n"
        f"Source reference: {source_reference}\n"
        + (f"Sector (as told by the user, for context only): {sector_hint}\n" if sector_hint else "")
        + "\n--- DOCUMENT TEXT START ---\n"
        + text
        + "\n--- DOCUMENT TEXT END ---"
    )

    response = client.messages.create(
        model=settings.claude_model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        tools=[EXTRACTION_TOOL],
        tool_choice={"type": "tool", "name": "record_financials"},
        messages=[{"role": "user", "content": user_content}],
    )

    tool_use_block = next(b for b in response.content if b.type == "tool_use")
    extracted = dict(tool_use_block.input)

    extracted["source_type"] = source_type
    extracted["source_reference"] = source_reference
    return extracted
