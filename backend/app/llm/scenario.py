"""Lender-side scenario Q&A ("what if receivable days doubled next year?").

Claude's job is split into two narrow steps so the actual math is never left
to the model:
  1. Interpret the free-text question into structured adjustments to the RAW
     input fields (revenue, receivables, etc.) — the same fields the
     deterministic engine already knows how to score.
  2. After we've re-run the real scoring pipeline on the adjusted numbers,
     Claude explains the before/after difference in words, citing the
     actual recomputed figures.

Claude never invents a score or ratio value in this flow — every number in
the final answer traces back to app/scoring/pipeline.py.
"""
import copy
import json
from typing import Any, Dict

from app.config import settings
from app.llm.client import get_client

ADJUSTABLE_FIELDS = [
    "balance_sheet.cash_and_equivalents",
    "balance_sheet.receivables",
    "balance_sheet.inventory",
    "balance_sheet.other_current_assets",
    "balance_sheet.fixed_assets",
    "balance_sheet.current_liabilities",
    "balance_sheet.payables",
    "balance_sheet.long_term_debt",
    "balance_sheet.equity",
    "income_statement.revenue",
    "income_statement.cogs",
    "income_statement.operating_expenses",
    "income_statement.depreciation",
    "income_statement.interest_expense",
    "income_statement.net_income",
]

INTERPRET_TOOL = {
    "name": "apply_scenario",
    "description": (
        "Translates a lender's what-if question into concrete adjustments to "
        "the company's raw financial input fields, so the real ratio engine "
        "can recompute the score under that scenario."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "adjustments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "field": {"type": "string", "enum": ADJUSTABLE_FIELDS},
                        "operation": {
                            "type": "string",
                            "enum": ["multiply", "set", "add"],
                        },
                        "value": {
                            "type": "number",
                            "description": (
                                "For 'multiply': factor (e.g. 2.0 = double). "
                                "For 'set': the new absolute value. "
                                "For 'add': amount to add (can be negative)."
                            ),
                        },
                    },
                    "required": ["field", "operation", "value"],
                },
            },
            "interpretation_note": {
                "type": "string",
                "description": (
                    "One sentence on how you translated the question into these "
                    "field adjustments, e.g. 'Doubling receivable days is modeled "
                    "by doubling the receivables balance, holding revenue fixed.'"
                ),
            },
        },
        "required": ["adjustments", "interpretation_note"],
    },
}

INTERPRET_SYSTEM_PROMPT = """You translate a lender's what-if question about an \
MSME loan applicant into adjustments to specific raw balance-sheet / income- \
statement fields, so a separate deterministic engine can recompute the real \
score. You do not compute ratios or scores yourself.

Only use fields from the allowed list. If a question refers to a ratio (e.g. \
"receivable days", "debt-to-equity") rather than a raw field, translate it to \
the raw field(s) that ratio is built from (e.g. doubling receivable days, with \
revenue held fixed, means doubling balance_sheet.receivables). State your \
translation logic in interpretation_note. If the question is ambiguous, make \
the most reasonable assumption and say so in interpretation_note."""

ANSWER_SYSTEM_PROMPT = """You are a credit analyst answering a lender's what-if \
question about an MSME loan applicant, using BEFORE and AFTER results that a \
deterministic ratio engine already computed for the original and adjusted \
scenario. Do not recompute or second-guess these numbers — only explain them.

Rules:
- Cite the actual before/after numbers (composite score, letter grade, and the \
  ratios most relevant to the question).
- State plainly whether the scenario would improve, worsen, or not meaningfully \
  change the credit view.
- Mention the interpretation_note so the lender understands what assumption was \
  modeled.
- Keep it to about 100-150 words."""


def _get_by_path(record: Dict[str, Any], path: str) -> float:
    section, field = path.split(".")
    return float(record[section].get(field) or 0)


def _set_by_path(record: Dict[str, Any], path: str, value: float) -> None:
    section, field = path.split(".")
    record[section][field] = value


def _apply_adjustments(record: Dict[str, Any], adjustments: list) -> Dict[str, Any]:
    adjusted = copy.deepcopy(record)
    for adj in adjustments:
        current = _get_by_path(adjusted, adj["field"])
        if adj["operation"] == "multiply":
            new_value = current * adj["value"]
        elif adj["operation"] == "add":
            new_value = current + adj["value"]
        else:  # set
            new_value = adj["value"]
        _set_by_path(adjusted, adj["field"], new_value)
    return adjusted


def answer_scenario_question(
    question: str,
    record: Dict[str, Any],
    sector: str,
    company_name: str,
    run_pipeline_fn,
) -> Dict[str, Any]:
    """`run_pipeline_fn` is app.scoring.pipeline.run_pipeline, passed in rather
    than imported here to make the dependency direction explicit: this module
    depends on the scoring engine, never the other way around."""
    client = get_client()

    interpret_response = client.messages.create(
        model=settings.claude_model,
        max_tokens=1024,
        system=INTERPRET_SYSTEM_PROMPT,
        tools=[INTERPRET_TOOL],
        tool_choice={"type": "tool", "name": "apply_scenario"},
        messages=[{"role": "user", "content": question}],
    )
    tool_use_block = next(b for b in interpret_response.content if b.type == "tool_use")
    interpretation = dict(tool_use_block.input)

    adjusted_record = _apply_adjustments(record, interpretation["adjustments"])

    before = run_pipeline_fn(record, sector)
    after = run_pipeline_fn(adjusted_record, sector)

    comparison_payload = {
        "question": question,
        "interpretation_note": interpretation["interpretation_note"],
        "adjustments_applied": interpretation["adjustments"],
        "before": {
            "composite_score": before.get("composite_score"),
            "letter_grade": before.get("letter_grade"),
            "ratios": before.get("ratios"),
        },
        "after": {
            "composite_score": after.get("composite_score"),
            "letter_grade": after.get("letter_grade"),
            "ratios": after.get("ratios"),
        },
    }

    answer_response = client.messages.create(
        model=settings.claude_model,
        max_tokens=768,
        system=ANSWER_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": json.dumps(comparison_payload, indent=2, default=str)}],
    )
    answer_text = "".join(b.text for b in answer_response.content if b.type == "text").strip()

    return {
        "question": question,
        "interpretation_note": interpretation["interpretation_note"],
        "adjustments_applied": interpretation["adjustments"],
        "before": before,
        "after": after,
        "answer": answer_text,
    }
