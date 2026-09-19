"""The single entry point for the deterministic scoring engine: sanity
checks -> derived cash flow -> ratios -> composite score -> anomaly flags.
Nothing in this module calls an LLM — it only runs once a human (or the
extraction step) has produced structured financial data.
"""
from typing import Any, Dict

from app.scoring.anomalies import detect_anomalies
from app.scoring.cashflow import derive_operating_cash_flow
from app.scoring.ratios import compute_ratios
from app.scoring.sanity import has_critical_issues, run_sanity_checks
from app.scoring.score import compute_composite_score


def run_pipeline(record: Dict[str, Any], sector: str) -> Dict[str, Any]:
    issues = run_sanity_checks(record)

    if has_critical_issues(issues):
        return {
            "status": "needs_review",
            "issues": issues,
        }

    cash_flow = derive_operating_cash_flow(record)
    ratios = compute_ratios(record, cash_flow)
    score_result = compute_composite_score(ratios, sector)
    anomaly_flags = detect_anomalies(record, cash_flow)

    return {
        "status": "scored",
        "issues": issues,  # non-critical warnings, if any, shown alongside the score
        "cash_flow": cash_flow,
        "ratios": ratios,
        "anomaly_flags": anomaly_flags,
        **score_result,
    }
