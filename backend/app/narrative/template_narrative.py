"""No-API-key fallback for narrative generation: canned sentence templates
filled in with the real computed numbers, instead of Claude writing prose.
Used automatically when ANTHROPIC_API_KEY isn't configured.
"""
from typing import Any, Dict, List, Tuple

# label, unit ("x" | "%" | "days"), higher_is_better
RATIO_DISPLAY: Dict[str, Tuple[str, str, bool]] = {
    "current_ratio": ("current ratio", "x", True),
    "quick_ratio": ("quick ratio", "x", True),
    "debt_to_equity": ("debt-to-equity", "x", False),
    "interest_coverage": ("interest coverage", "x", True),
    "dscr": ("debt service coverage (DSCR)", "x", True),
    "gross_margin": ("gross margin", "%", True),
    "net_margin": ("net margin", "%", True),
    "roce": ("return on capital employed (ROCE)", "%", True),
    "receivable_days": ("receivable days", "days", False),
    "inventory_days": ("inventory days", "days", False),
    "cash_conversion_cycle": ("cash conversion cycle", "days", False),
    "revenue_yoy_growth": ("revenue growth", "%", True),
}

RATIO_SUGGESTIONS: Dict[str, str] = {
    "receivable_days": "Tightening payment terms or following up sooner with customers who pay late would help.",
    "inventory_days": "Reducing stock levels or clearing slow-moving inventory would free up cash.",
    "cash_conversion_cycle": "Shortening how long cash is tied up in receivables and inventory, or negotiating longer payment terms with suppliers, would help.",
    "debt_to_equity": "Paying down some borrowings, or raising additional equity before taking on more debt, would help.",
    "interest_coverage": "Current profit leaves little cushion for interest payments — improving margins or reducing debt would help.",
    "dscr": "Cash flow doesn't comfortably cover debt obligations yet — converting profit into actual cash (see working capital ratios) is the priority.",
    "current_ratio": "Building up more short-term liquid assets relative to what's owed in the next year would help.",
    "quick_ratio": "Holding more cash and receivables relative to near-term obligations, without relying on inventory, would help.",
    "gross_margin": "Re-pricing or reducing direct costs relative to sales would help.",
    "net_margin": "Overall costs relative to revenue are high — reviewing operating expenses and interest costs would help.",
    "roce": "Returns on capital employed are below the sector norm — worth reviewing whether assets are being used efficiently.",
    "revenue_yoy_growth": "Revenue growth is below the sector norm — worth reviewing what's limiting demand or sales capacity.",
}


def _format(ratio_name: str, value: float) -> str:
    _, unit, _ = RATIO_DISPLAY[ratio_name]
    if unit == "%":
        return f"{value * 100:.1f}%"
    if unit == "x":
        return f"{value:.2f}x"
    return f"{value:.0f} days"


def _weak_and_strong(pipeline_result: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    ratio_scores = {k: v for k, v in pipeline_result["ratio_scores"].items() if v is not None}
    ranked = sorted(ratio_scores.items(), key=lambda kv: kv[1])
    weak = [name for name, score in ranked if score < 45][:2]
    strong = [name for name, score in ranked if score >= 65][-1:]
    return weak, strong


def generate_msme_narrative_template(
    company_name: str, sector: str, pipeline_result: Dict[str, Any]
) -> str:
    grade = pipeline_result["letter_grade"]
    score = pipeline_result["composite_score"]
    ratios = pipeline_result["ratios"]
    benchmark = pipeline_result["sector_benchmark_used"]
    weak, strong = _weak_and_strong(pipeline_result)

    parts = [f"{company_name} is rated {grade} ({score}/100) for the {sector} sector."]

    if strong:
        name = strong[0]
        label, _, _ = RATIO_DISPLAY[name]
        parts.append(
            f"Your strongest area is {label}, at {_format(name, ratios[name])} against a "
            f"sector norm of {_format(name, benchmark[name])}."
        )

    for name in weak:
        label, _, _ = RATIO_DISPLAY[name]
        suggestion = RATIO_SUGGESTIONS.get(name, "")
        parts.append(
            f"{label[0].upper()}{label[1:]} is {_format(name, ratios[name])}, against a sector norm of "
            f"{_format(name, benchmark[name])}. {suggestion}"
        )

    for flag in pipeline_result["anomaly_flags"]:
        parts.append(flag["detail"])

    if not weak and not pipeline_result["anomaly_flags"]:
        parts.append("No major red flags were found in this year's numbers relative to your sector.")

    return " ".join(parts)


def generate_lender_summary_template(
    company_name: str, sector: str, pipeline_result: Dict[str, Any]
) -> str:
    grade = pipeline_result["letter_grade"]
    score = pipeline_result["composite_score"]
    ratios = pipeline_result["ratios"]
    benchmark = pipeline_result["sector_benchmark_used"]
    weak, strong = _weak_and_strong(pipeline_result)
    flags = pipeline_result["anomaly_flags"]

    parts = [f"{company_name} ({sector}) scores {grade} ({score}/100)."]

    if strong:
        name = strong[0]
        label, _, _ = RATIO_DISPLAY[name]
        parts.append(f"Strongest factor: {label} at {_format(name, ratios[name])} vs. sector norm {_format(name, benchmark[name])}.")

    if weak:
        driver_bits = []
        for name in weak:
            label, _, _ = RATIO_DISPLAY[name]
            driver_bits.append(f"{label} at {_format(name, ratios[name])} (norm {_format(name, benchmark[name])})")
        parts.append("Primary risk drivers: " + "; ".join(driver_bits) + ".")

    if flags:
        parts.append("Flags for underwriting attention: " + " ".join(f["detail"] for f in flags))
    else:
        parts.append("No anomaly flags triggered on this year's figures.")

    return " ".join(parts)
