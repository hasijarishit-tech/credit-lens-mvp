"""Illustrative sector benchmark medians for the MVP.

These are reasonable placeholder values for Indian MSMEs, NOT sourced from
a real dataset. The product is designed so these can be swapped for real
sector medians later without touching any other code — this file is the
only place they live.
"""

# Ratios where a HIGHER value is healthier.
HIGHER_IS_BETTER = {
    "current_ratio",
    "quick_ratio",
    "interest_coverage",
    "dscr",
    "gross_margin",
    "net_margin",
    "roce",
    "revenue_yoy_growth",
}

# Ratios where a LOWER value is healthier.
LOWER_IS_BETTER = {
    "debt_to_equity",
    "receivable_days",
    "inventory_days",
    "cash_conversion_cycle",
}

BUCKETS = {
    "liquidity": ["current_ratio", "quick_ratio"],
    "leverage": ["debt_to_equity", "interest_coverage", "dscr"],
    "profitability": ["gross_margin", "net_margin", "roce"],
    "efficiency_growth": [
        "receivable_days",
        "inventory_days",
        "cash_conversion_cycle",
        "revenue_yoy_growth",
    ],
}

# How much each bucket counts toward the composite score. Leverage and
# profitability are weighted highest since they matter most for credit risk;
# tweak these freely as you refine the model.
BUCKET_WEIGHTS = {
    "liquidity": 0.20,
    "leverage": 0.30,
    "profitability": 0.30,
    "efficiency_growth": 0.20,
}

SECTOR_BENCHMARKS = {
    "Manufacturing": {
        "current_ratio": 1.30,
        "quick_ratio": 0.90,
        "debt_to_equity": 1.20,
        "interest_coverage": 3.0,
        "dscr": 1.50,
        "gross_margin": 0.25,
        "net_margin": 0.06,
        "roce": 0.15,
        "receivable_days": 60,
        "inventory_days": 75,
        "cash_conversion_cycle": 90,
        "revenue_yoy_growth": 0.10,
    },
    "Trading": {
        "current_ratio": 1.20,
        "quick_ratio": 0.80,
        "debt_to_equity": 1.00,
        "interest_coverage": 2.5,
        "dscr": 1.40,
        "gross_margin": 0.15,
        "net_margin": 0.04,
        "roce": 0.14,
        "receivable_days": 45,
        "inventory_days": 50,
        "cash_conversion_cycle": 60,
        "revenue_yoy_growth": 0.12,
    },
    "Services": {
        "current_ratio": 1.40,
        "quick_ratio": 1.20,
        "debt_to_equity": 0.70,
        "interest_coverage": 4.0,
        "dscr": 1.70,
        "gross_margin": 0.40,
        "net_margin": 0.10,
        "roce": 0.20,
        "receivable_days": 50,
        "inventory_days": 5,
        "cash_conversion_cycle": 45,
        "revenue_yoy_growth": 0.15,
    },
    "Construction": {
        "current_ratio": 1.15,
        "quick_ratio": 0.75,
        "debt_to_equity": 1.50,
        "interest_coverage": 2.2,
        "dscr": 1.30,
        "gross_margin": 0.18,
        "net_margin": 0.05,
        "roce": 0.12,
        "receivable_days": 90,
        "inventory_days": 40,
        "cash_conversion_cycle": 110,
        "revenue_yoy_growth": 0.08,
    },
    "Agriculture-adjacent": {
        "current_ratio": 1.25,
        "quick_ratio": 0.85,
        "debt_to_equity": 1.10,
        "interest_coverage": 2.8,
        "dscr": 1.45,
        "gross_margin": 0.20,
        "net_margin": 0.06,
        "roce": 0.13,
        "receivable_days": 40,
        "inventory_days": 60,
        "cash_conversion_cycle": 70,
        "revenue_yoy_growth": 0.09,
    },
}

GRADE_BANDS = [
    ("AA", 85),
    ("A", 70),
    ("BBB", 55),
    ("BB", 40),
    ("B", 0),
]


def score_to_grade(composite_score: float) -> str:
    for grade, floor in GRADE_BANDS:
        if composite_score >= floor:
            return grade
    return "B"
