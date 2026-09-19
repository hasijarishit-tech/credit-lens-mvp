"""No-API-key fallback for the lender's scenario Q&A: a fixed menu of
what-if buttons instead of a free-text question Claude has to interpret.
The actual math is identical to app/llm/scenario.py — this only replaces
the "understand an arbitrary English question" step, which is the one part
that genuinely needs a model.

Each preset is a small function rather than a generic declarative rule,
because a couple of them need to keep two fields consistent with each
other (e.g. a revenue drop has to reduce net income too, or the composite
score index moves the wrong way — see the note on _revenue_down_20 below).
"""
import copy
from typing import Any, Callable, Dict

from app.scoring.pipeline import run_pipeline


def _get(record: Dict[str, Any], path: str) -> float:
    section, field = path.split(".")
    return float(record[section].get(field) or 0)


def _set(record: Dict[str, Any], path: str, value: float) -> None:
    section, field = path.split(".")
    record[section][field] = value


def _receivables_up_50(record: Dict[str, Any]) -> Dict[str, Any]:
    # Customers taking longer to pay doesn't itself change reported
    # accrual-basis profit — that's the whole point of this scenario:
    # profit looks the same, cash flow doesn't. net_income intentionally
    # untouched.
    adjusted = copy.deepcopy(record)
    _set(adjusted, "balance_sheet.receivables", _get(record, "balance_sheet.receivables") * 1.5)
    return adjusted


def _revenue_down_20(record: Dict[str, Any]) -> Dict[str, Any]:
    # If revenue falls with costs genuinely held fixed, profit must fall by
    # the same absolute amount as the revenue drop — net_income is an
    # independent input field in this schema, so it needs to be moved
    # explicitly here or the scenario would (incorrectly) leave profit
    # unchanged while revenue drops, which even makes net margin look
    # better, not worse.
    adjusted = copy.deepcopy(record)
    original_revenue = _get(record, "income_statement.revenue")
    revenue_drop = original_revenue * 0.2
    _set(adjusted, "income_statement.revenue", original_revenue - revenue_drop)
    _set(adjusted, "income_statement.net_income", _get(record, "income_statement.net_income") - revenue_drop)
    return adjusted


def _inventory_up_30(record: Dict[str, Any]) -> Dict[str, Any]:
    # Same reasoning as receivables: slower-moving stock doesn't itself
    # change reported profit, only cash flow — net_income untouched.
    adjusted = copy.deepcopy(record)
    _set(adjusted, "balance_sheet.inventory", _get(record, "balance_sheet.inventory") * 1.3)
    return adjusted


def _interest_expense_doubles(record: Dict[str, Any]) -> Dict[str, Any]:
    # Extra interest cost reduces profit dollar-for-dollar (ignoring tax
    # effects, a fine simplification here).
    adjusted = copy.deepcopy(record)
    original_interest = _get(record, "income_statement.interest_expense")
    extra_interest = original_interest  # doubling = +100% = +original amount
    _set(adjusted, "income_statement.interest_expense", original_interest + extra_interest)
    _set(adjusted, "income_statement.net_income", _get(record, "income_statement.net_income") - extra_interest)
    return adjusted


PRESET_SCENARIOS: Dict[str, Dict[str, Any]] = {
    "receivables_up_50": {
        "label": "Receivables +50%",
        "explanation": "Models customers taking meaningfully longer to pay: receivables up 50%, reported profit unchanged (this is deliberately a profit-vs-cash scenario).",
        "apply": _receivables_up_50,
    },
    "revenue_down_20": {
        "label": "Revenue -20%",
        "explanation": "Models a demand shock: revenue down 20% with costs held fixed, so net income falls by the same absolute amount as the revenue drop.",
        "apply": _revenue_down_20,
    },
    "inventory_up_30": {
        "label": "Inventory +30%",
        "explanation": "Models slower-moving stock: inventory up 30%, reported profit unchanged (this is deliberately a profit-vs-cash scenario).",
        "apply": _inventory_up_30,
    },
    "interest_expense_doubles": {
        "label": "Interest expense doubles",
        "explanation": "Models a rate hike or refinancing at worse terms: interest expense doubles, and net income falls by the added interest cost.",
        "apply": _interest_expense_doubles,
    },
}


def apply_preset_scenario(record: Dict[str, Any], sector: str, preset_key: str) -> Dict[str, Any]:
    preset = PRESET_SCENARIOS[preset_key]
    apply_fn: Callable[[Dict[str, Any]], Dict[str, Any]] = preset["apply"]
    adjusted = apply_fn(record)

    before = run_pipeline(record, sector, skip_sanity=True)
    after = run_pipeline(adjusted, sector, skip_sanity=True)

    return {
        "preset": preset_key,
        "label": preset["label"],
        "explanation": preset["explanation"],
        "before": before,
        "after": after,
    }
