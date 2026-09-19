"""No-API-key fallback for the lender's scenario Q&A: a fixed menu of
what-if buttons instead of a free-text question Claude has to interpret.
The actual math is identical to app/llm/scenario.py — this only replaces
the "understand an arbitrary English question" step, which is the one part
that genuinely needs a model.
"""
import copy
from typing import Any, Dict

from app.scoring.pipeline import run_pipeline

PRESET_SCENARIOS = {
    "receivables_up_50": {
        "label": "Receivables +50%",
        "field": "balance_sheet.receivables",
        "operation": "multiply",
        "value": 1.5,
        "explanation": "Models customers taking meaningfully longer to pay: receivables up 50%, revenue held fixed.",
    },
    "revenue_down_20": {
        "label": "Revenue -20%",
        "field": "income_statement.revenue",
        "operation": "multiply",
        "value": 0.8,
        "explanation": "Models a demand shock: revenue down 20%, costs held fixed.",
    },
    "inventory_up_30": {
        "label": "Inventory +30%",
        "field": "balance_sheet.inventory",
        "operation": "multiply",
        "value": 1.3,
        "explanation": "Models slower-moving stock: inventory up 30%, revenue held fixed.",
    },
    "interest_expense_doubles": {
        "label": "Interest expense doubles",
        "field": "income_statement.interest_expense",
        "operation": "multiply",
        "value": 2.0,
        "explanation": "Models a rate hike or refinancing at worse terms: interest expense doubles.",
    },
}


def _get_by_path(record: Dict[str, Any], path: str) -> float:
    section, field = path.split(".")
    return float(record[section].get(field) or 0)


def _set_by_path(record: Dict[str, Any], path: str, value: float) -> None:
    section, field = path.split(".")
    record[section][field] = value


def apply_preset_scenario(record: Dict[str, Any], sector: str, preset_key: str) -> Dict[str, Any]:
    preset = PRESET_SCENARIOS[preset_key]
    adjusted = copy.deepcopy(record)
    current = _get_by_path(adjusted, preset["field"])
    _set_by_path(adjusted, preset["field"], current * preset["value"])

    before = run_pipeline(record, sector, skip_sanity=True)
    after = run_pipeline(adjusted, sector, skip_sanity=True)

    return {
        "preset": preset_key,
        "label": preset["label"],
        "explanation": preset["explanation"],
        "before": before,
        "after": after,
    }
